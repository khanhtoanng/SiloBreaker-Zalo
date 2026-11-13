"""A managed, offline llama-server for local GGUF inference."""

from __future__ import annotations

import atexit
import json
import os
import secrets
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from ..contracts import DECISION, INFERENCE_SEED, GoalPlan, json_loads
from ..runtime.goals import PLANNER_SYSTEM, PolicyPlanner
from ..runtime.validation import Rejected
from .ollama import NoRedirect
from .protocols import ContextOverflow

DECISION_SCHEMA = DECISION.model_json_schema()
GOAL_SCHEMA = GoalPlan.model_json_schema()


def _action_schema(payload):
    """Constrain ASK to real parameter names of the planned target tool."""
    goals = {goal["tool_name"] for goal in payload.get("goal_ledger", [])}
    definitions = DECISION_SCHEMA["$defs"]
    options = [{"$ref": "#/$defs/CallDecision"}, {"$ref": "#/$defs/DoneDecision"}]
    for tool in payload.get("installed_tools", []):
        name = tool["name"]
        properties = tool["parameters"].get("properties", {})
        if name not in goals or not properties:
            continue
        options.append(
            {
                "type": "object",
                "properties": {
                    "kind": {"const": "ASK"},
                    "tool_name": {"const": name},
                    "arguments": {
                        "type": "object",
                        "properties": {
                            "params": {
                                "type": "array",
                                "items": {"enum": list(properties)},
                                "minItems": 1,
                                "maxItems": len(properties),
                            }
                        },
                        "required": ["params"],
                        "additionalProperties": False,
                    },
                },
                "required": ["kind", "tool_name", "arguments"],
                "additionalProperties": False,
            }
        )
    return {"$defs": definitions, "oneOf": options}


class LlamaCppPolicy:
    def __init__(self, executable, model_path, *, max_context_tokens, max_new_tokens):
        executable = Path(executable).resolve(strict=True)
        model = Path(model_path).resolve(strict=True)
        if not executable.is_file() or not model.is_file() or model.suffix.lower() != ".gguf":
            raise ValueError("llama_cpp requires a local executable and GGUF file")
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        self._base_url = f"http://127.0.0.1:{port}"
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        self._context = max_context_tokens
        self._max_new_tokens = max_new_tokens
        self._cache_prompt = False
        self.last_usage: dict = {}
        self.metadata = {
            "backend": "llama_cpp",
            "model_path": str(model),
            "max_context_tokens": max_context_tokens,
            "max_new_tokens": max_new_tokens,
            "temperature": 0,
            "seed": INFERENCE_SEED,
            "format": "json",
            "token_budget_method": "exact server chat token count",
        }
        # Require the server to authenticate the client, including the first inference request.
        self._api_key = secrets.token_urlsafe(24)
        with tempfile.TemporaryFile(mode="w+b") as log:
            self._process = subprocess.Popen(
                [
                    str(executable),
                    "--model",
                    str(model),
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--ctx-size",
                    str(max_context_tokens),
                    "--parallel",
                    "1",
                    "--n-gpu-layers",
                    "999",
                    "--flash-attn",
                    "on",
                    "--offline",
                    "--no-webui",
                    "--no-context-shift",
                    "--api-key",
                    self._api_key,
                    "--log-verbosity",
                    "1",
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            try:
                self._wait_ready()
            except (KeyboardInterrupt, SystemExit):
                self.close()
                raise
            except Exception:
                self.close()
                log.seek(0)
                details = (
                    log.read(2000)
                    .decode("utf-8", errors="replace")
                    .replace(self._api_key, "[redacted]")
                )
                if details:
                    raise RuntimeError(f"llama-server startup failed: {details.strip()}") from None
                raise
        atexit.register(self.close)

    def _wait_ready(self):
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline and self._process.poll() is None:
            try:
                if self._request("/health", None, time.monotonic() + 1).get("status") == "ok":
                    return
            except (urllib.error.URLError, TimeoutError):
                time.sleep(0.1)
        raise RuntimeError("llama-server did not become ready")

    def _request(self, route, payload, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Sample deadline reached before llama-server request")
        body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
        request = urllib.request.Request(
            self._base_url + route,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
        )
        with self._opener.open(request, timeout=remaining) as response:
            result = json.load(response)
        if time.monotonic() >= deadline:
            raise TimeoutError("llama-server exceeded the sample deadline")
        return result

    def next_action(self, messages: list[dict[str, str]], *, deadline: float) -> str:
        system = messages[0]["content"]
        if system == PLANNER_SYSTEM:
            schema = GOAL_SCHEMA
        elif system.startswith("Bind the proposed action"):
            schema = {
                "type": "object",
                "properties": {"occurrence_id": {"type": ["string", "null"]}},
                "required": ["occurrence_id"],
                "additionalProperties": False,
            }
        else:
            schema = _action_schema(json.loads(messages[1]["content"]))
        payload = {"messages": messages}
        count = self._request("/v1/chat/completions/input_tokens", payload, deadline)[
            "input_tokens"
        ]
        if count + self._max_new_tokens > self._context:
            raise ContextOverflow("Full prompt and generation exceed the context cap")
        response = self._request(
            "/v1/chat/completions",
            {
                **payload,
                "stream": False,
                "temperature": 0,
                "seed": INFERENCE_SEED,
                "max_tokens": self._max_new_tokens,
                "response_format": {"type": "json_object", "schema": schema},
                "cache_prompt": self._cache_prompt,
            },
            deadline,
        )
        self._cache_prompt = True
        self.last_usage = response["usage"]
        return response["choices"][0]["message"]["content"]

    def plan(self, request_context, *, deadline) -> GoalPlan:
        if request_context.get("planning_rejection") is None:
            self._cache_prompt = False
        return PolicyPlanner(self).plan(request_context, deadline=deadline)

    def bind(self, request_context, *, deadline):
        raw = self.next_action(
            [
                {
                    "role": "system",
                    "content": 'Bind the proposed action to one explicitly requested pending occurrence. Return {"occurrence_id":"id"} or {"occurrence_id":null} if ambiguous.',
                },
                {"role": "user", "content": json.dumps(request_context, ensure_ascii=False)},
            ],
            deadline=deadline,
        )
        try:
            result = json_loads(raw)
        except ValueError as exc:
            raise Rejected("Malformed goal occurrence binding") from exc
        if (
            not isinstance(result, dict)
            or set(result) != {"occurrence_id"}
            or not isinstance(result["occurrence_id"], str)
        ):
            raise Rejected("Ambiguous goal occurrence binding")
        return result["occurrence_id"]

    def close(self):
        atexit.unregister(self.close)
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()
