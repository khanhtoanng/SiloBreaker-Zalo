"""Injectable boundaries; inference sessions deliberately expose no raw state getter."""

from __future__ import annotations

from typing import Protocol

from ..contracts import GoalPlan, JsonValue


class ContextOverflow(RuntimeError):
    """The complete prompt cannot fit the configured model context."""


class Clock(Protocol):
    def monotonic(self) -> float: ...


class Policy(Protocol):
    def next_action(self, messages: list[dict[str, str]], *, deadline: float) -> str: ...


class GoalPlanner(Protocol):
    def plan(self, request_context: dict, *, deadline: float) -> GoalPlan: ...


class Session(Protocol):
    def validate(self, name: str, arguments: dict) -> dict: ...
    def call(self, name: str, arguments: dict) -> JsonValue: ...
    def get_tool_calls(self) -> list[dict]: ...
    def get_state_hash(self) -> str: ...


class Asr(Protocol):
    def transcribe(self, path, *, deadline: float) -> str: ...


class TrainingRuntime(Protocol):
    def train(self, validated_inputs, config): ...
