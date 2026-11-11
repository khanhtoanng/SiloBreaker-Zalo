"""Local-only Ollama transport and next-action policy; downloads are setup only."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Ollama endpoint redirects are forbidden")


def local_url(value):
    parsed = urllib.parse.urlsplit(value)
    if (
        parsed.scheme != "http"
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
    ):
        raise ValueError("Ollama URL must be a loopback HTTP origin")
    host = parsed.hostname
    if host != "localhost":
        try:
            if not ipaddress.ip_address(host).is_loopback:
                raise ValueError("Ollama endpoint must be loopback")
        except (ValueError, TypeError) as exc:
            raise ValueError("Ollama endpoint must be localhost or a loopback IP") from exc
    # Validate the port before sending any data.
    port = parsed.port or 11434
    host = "127.0.0.1" if host == "localhost" else host
    return f"http://{'[' + host + ']' if ':' in host else host}:{port}"


class OllamaClient:
    def __init__(self, base_url="http://127.0.0.1:11434"):
        self.base_url = local_url(base_url)
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def request(self, path, payload=None, timeout=10):
        if path not in ("/api/tags", "/api/show", "/api/chat", "/api/version", "/api/ps"):
            raise ValueError("Unsupported local API endpoint")
        request = urllib.request.Request(
            self.base_url + path,
            data=None
            if payload is None
            else json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with self.opener.open(request, timeout=timeout) as response:
                body = response.read(8 * 1024 * 1024 + 1)
                if len(body) > 8 * 1024 * 1024:
                    raise RuntimeError("Oversized Ollama response")
                result = json.loads(body)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Local Ollama HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise TimeoutError("Local Ollama request timed out") from exc
            raise RuntimeError(f"Local Ollama unavailable: {exc.reason}") from exc
        if not isinstance(result, dict) or result.get("error"):
            raise RuntimeError("Ollama returned an invalid/error response")
        return result


class OllamaPolicy:
    def __init__(
        self,
        model="qwen3:4b-instruct-2507-q4_K_M",
        base_url="http://127.0.0.1:11434",
        max_context_tokens=16384,
        max_new_tokens=512,
        tokenizer_path=None,
        *,
        client=None,
    ):
        if not isinstance(model, str) or not model or "cloud" in model.lower():
            raise ValueError("Choose an installed local model, not a cloud model")
        if max_new_tokens < 1 or max_context_tokens <= max_new_tokens + 256:
            raise ValueError("Invalid context/generation budget")
        self.client = client or OllamaClient(base_url)
        models = self.client.request("/api/tags").get("models", [])
        found = next(
            (item for item in models if item.get("name") == model or item.get("model") == model),
            None,
        )
        if found is None:
            raise ValueError(f"Local model not installed: {model}; pull it during setup")
        info = self.client.request("/api/show", {"model": model})
        if info.get("remote_model") or info.get("remote_host"):
            raise ValueError("Remote Ollama models are forbidden for this local backend")
        self.model = model
        self.max_context_tokens = max_context_tokens
        self.max_new_tokens = max_new_tokens
        self.tokenizer = None
        self.metadata = {
            "backend": "ollama",
            "base_url": self.client.base_url,
            "model": model,
            "digest": found.get("digest"),
            "details": found.get("details"),
            "model_info": info.get("model_info"),
            "capabilities": info.get("capabilities"),
            "license_sha256": hashlib.sha256(info.get("license", "").encode()).hexdigest(),
            "template_sha256": hashlib.sha256(info.get("template", "").encode()).hexdigest(),
            "server_version": self.client.request("/api/version").get("version"),
            "max_context_tokens": max_context_tokens,
            "max_new_tokens": max_new_tokens,
            "temperature": 0,
            "seed": 20261109,
            "think": False,
            "format": "json",
        }
        if tokenizer_path:
            from tokenizers import Tokenizer  # type: ignore[import-not-found,import-untyped]

            path = Path(tokenizer_path).resolve()
            self.tokenizer = Tokenizer.from_file(str(path))
            self.tokenizer.no_truncation()
            self.tokenizer.no_padding()
            self.metadata["tokenizer_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            self.metadata["token_budget_method"] = (
                "local content tokenizer plus 256 framing-token reserve"
            )
        else:
            self.metadata["token_budget_method"] = (
                "conservative UTF-8 byte bound plus 256 framing-token reserve"
            )
        self.last_usage = {}

    def next_action(self, messages: list[dict[str, str]], *, deadline: float) -> str:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Sample deadline reached before Ollama request")
        content = [message["content"] for message in messages]
        count = (
            sum(len(self.tokenizer.encode(text, add_special_tokens=False).ids) for text in content)
            if self.tokenizer
            else sum(len(text.encode("utf-8")) for text in content)
        )
        if count + 256 + self.max_new_tokens > self.max_context_tokens:
            raise ValueError("Full schema/history exceeds the conservative Ollama context budget")
        started = time.monotonic()
        response = self.client.request(
            "/api/chat",
            {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "think": False,
                "format": "json",
                "keep_alive": "10m",
                "options": {
                    "temperature": 0,
                    "seed": 20261109,
                    "num_ctx": self.max_context_tokens,
                    "num_predict": self.max_new_tokens,
                },
            },
            timeout=remaining,
        )
        self.last_usage = {
            key: response[key]
            for key in (
                "prompt_eval_count",
                "eval_count",
                "total_duration",
                "load_duration",
                "prompt_eval_duration",
                "eval_duration",
                "done_reason",
            )
            if key in response
        }
        self.last_usage.update(
            content_token_budget=count, elapsed_seconds=time.monotonic() - started
        )
        if time.monotonic() >= deadline:
            raise TimeoutError("Ollama response exceeded the sample deadline")
        if response.get("done") is not True:
            raise RuntimeError("Incomplete Ollama response")
        actual_prompt = response.get("prompt_eval_count")
        if (
            isinstance(actual_prompt, int)
            and actual_prompt + self.max_new_tokens > self.max_context_tokens
        ):
            raise ValueError("Ollama prompt leaves insufficient configured generation budget")
        message = response.get("message", {})
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise RuntimeError("Ollama response has no text decision")
        return message["content"]

    def plan(self, request_context, *, deadline):
        from ..runtime.goals import PolicyPlanner

        return PolicyPlanner(self).plan(request_context, deadline=deadline)

    def bind(self, request_context, *, deadline):
        import json

        from ..contracts import json_loads

        raw = self.next_action(
            [
                {
                    "role": "system",
                    "content": 'Bind this proposed action to exactly one explicitly requested pending occurrence. Return only {"occurrence_id":"id"}. Choose only when intent and span support it; otherwise return {"occurrence_id":null}. No tool call is executed by this binding.',
                },
                {"role": "user", "content": json.dumps(request_context, ensure_ascii=False)},
            ],
            deadline=deadline,
        )
        value = json_loads(raw)
        if (
            not isinstance(value, dict)
            or set(value) != {"occurrence_id"}
            or not isinstance(value["occurrence_id"], str)
        ):
            from ..runtime.validation import Rejected

            raise Rejected("Ambiguous goal occurrence binding")
        return value["occurrence_id"]
