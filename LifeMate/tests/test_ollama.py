"""Ollama protocol tests use local fixtures, never download or load a real model."""

import copy
import json
import sys
import time
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lifemate.ollama_policy import NoRedirect, OllamaClient, OllamaPolicy, local_url


class FixtureClient:
    base_url = "http://127.0.0.1:11434"

    def __init__(self):
        self.requests = []
        self.models = [
            {
                "name": "fixture:4b",
                "digest": "synthetic-digest",
                "details": {"parameter_size": "4B"},
            }
        ]
        self.info = {
            "capabilities": ["completion"],
            "model_info": {"general.architecture": "fixture"},
        }
        self.response = {
            "message": {"content": '{"kind":"DONE"}'},
            "done": True,
            "prompt_eval_count": 10,
            "eval_count": 5,
        }

    def request(self, path, payload=None, timeout=10):
        self.requests.append((path, copy.deepcopy(payload), timeout))
        return copy.deepcopy(
            {
                "/api/tags": {"models": self.models},
                "/api/show": self.info,
                "/api/version": {"version": "fixture"},
                "/api/chat": self.response,
            }[path]
        )


class OllamaTests(unittest.TestCase):
    def test_loopback_origins_only(self):
        for origin in (
            "https://ollama.com",
            "http://example.com:11434",
            "http://0.0.0.0:11434",
            "http://127.0.0.1@evil.test",
            "http://127.0.0.1:11434/api",
            "http://127.0.0.1:11434/?key=x",
        ):
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                local_url(origin)
        self.assertEqual(local_url("http://localhost:11434"), "http://127.0.0.1:11434")
        self.assertEqual(local_url("http://[::1]:11434"), "http://[::1]:11434")

    def test_redirects_are_blocked(self):
        with self.assertRaises(RuntimeError):
            NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://example.com")

    def test_cloud_models_blocked_before_request(self):
        client = FixtureClient()
        with self.assertRaises(ValueError):
            OllamaPolicy("model:cloud", client=client)
        self.assertEqual(client.requests, [])

    def test_remote_backed_local_tag_blocked(self):
        client = FixtureClient()
        client.info["remote_model"] = "remote"
        with self.assertRaises(ValueError):
            OllamaPolicy("fixture:4b", client=client)

    def test_absent_model_never_pulled(self):
        client = FixtureClient()
        with self.assertRaises(ValueError):
            OllamaPolicy("missing:4b", client=client)
        self.assertEqual([r[0] for r in client.requests], ["/api/tags"])

    def test_local_json_request_and_metadata(self):
        client = FixtureClient()
        policy = OllamaPolicy("fixture:4b", client=client)
        result = policy.next_action(
            [{"role": "user", "content": "Xin chào"}], deadline=time.monotonic() + 3
        )
        self.assertEqual(json.loads(result), {"kind": "DONE"})
        path, payload, timeout = client.requests[-1]
        self.assertEqual(path, "/api/chat")
        self.assertFalse(payload["think"])
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["format"], "json")
        self.assertEqual(payload["options"]["temperature"], 0)
        self.assertEqual(payload["options"]["num_ctx"], 16384)
        self.assertLessEqual(timeout, 3)
        self.assertEqual(policy.metadata["digest"], "synthetic-digest")
        self.assertEqual(policy.last_usage["eval_count"], 5)

    def test_expired_deadline_never_generates(self):
        client = FixtureClient()
        policy = OllamaPolicy("fixture:4b", client=client)
        with self.assertRaises(TimeoutError):
            policy.next_action([], deadline=time.monotonic() - 1)
        self.assertNotIn("/api/chat", [r[0] for r in client.requests])

    def test_context_overflow_does_not_drop_tools_or_history(self):
        client = FixtureClient()
        policy = OllamaPolicy("fixture:4b", max_context_tokens=1024, client=client)
        with self.assertRaises(ValueError):
            policy.next_action([{"content": "x" * 1024}], deadline=time.monotonic() + 3)
        self.assertNotIn("/api/chat", [r[0] for r in client.requests])

    def test_incomplete_response_rejected(self):
        client = FixtureClient()
        client.response["done"] = False
        policy = OllamaPolicy("fixture:4b", client=client)
        with self.assertRaises(RuntimeError):
            policy.next_action([], deadline=time.monotonic() + 3)

    def test_token_usage_guard(self):
        client = FixtureClient()
        client.response["prompt_eval_count"] = 16380
        policy = OllamaPolicy("fixture:4b", client=client)
        with self.assertRaises(ValueError):
            policy.next_action([], deadline=time.monotonic() + 3)

    def test_nontext_response_rejected(self):
        client = FixtureClient()
        client.response["message"]["content"] = {"kind": "DONE"}
        policy = OllamaPolicy("fixture:4b", client=client)
        with self.assertRaises(RuntimeError):
            policy.next_action([], deadline=time.monotonic() + 3)

    def test_transport_has_no_pull_or_external_api_route(self):
        client = OllamaClient()
        with self.assertRaises(ValueError):
            client.request("/api/pull", {"model": "anything"})

    def test_transport_timeout_classification(self):
        client = OllamaClient()
        with patch.object(
            client.opener, "open", side_effect=urllib.error.URLError(TimeoutError("synthetic"))
        ):
            with self.assertRaises(TimeoutError):
                client.request("/api/chat", {"messages": []})


if __name__ == "__main__":
    unittest.main()
