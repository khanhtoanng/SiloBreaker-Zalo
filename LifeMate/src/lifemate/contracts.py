"""Strict, label-separated application records. Organizer schemas remain dynamic JSON."""

from __future__ import annotations

import json
import math
from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, JsonValue, RootModel, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        validate_assignment=True,
        allow_inf_nan=False,
        hide_input_in_errors=True,
    )


Payload = dict[str, JsonValue]
INFERENCE_SEED = 20261109


def json_loads(raw: str) -> JsonValue:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON field: {key}")
            result[key] = value
        return result

    def invalid(value):
        raise ValueError(f"Nonfinite JSON value: {value}")

    def finite_float(raw):
        value = float(raw)
        if not math.isfinite(value):
            raise ValueError("Overflow to nonfinite JSON number")
        return value

    return json.loads(
        raw, object_pairs_hook=unique, parse_constant=invalid, parse_float=finite_float
    )


def json_object(raw: str) -> dict:
    value = json_loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Expected JSON object")
    return value


class ToolCall(StrictModel):
    name: str = Field(min_length=1)
    arguments: Payload


class HistoryTurn(StrictModel):
    role: Literal["user", "assistant", "tool", "system"]
    audio: str | None = None
    text: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_results: list[JsonValue] = Field(default_factory=list)


class SampleContext(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True, hide_input_in_errors=True)
    current_time: str | None = None
    timezone: str | None = None
    installed_apps: dict[str, Payload] = Field(default_factory=dict)


class InferenceSample(StrictModel):
    id: str = Field(min_length=1)
    audio: str | None = None
    text: str | None = None
    context: SampleContext = Field(default_factory=SampleContext)
    history: list[HistoryTurn] = Field(default_factory=list)
    normalization: Payload | None = None


class TrainSample(InferenceSample):
    audio_text: str
    label: Payload


class ToolSpec(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True, hide_input_in_errors=True)
    name: str = Field(min_length=1)
    app: str
    kind: Literal["read", "write", "meta"]
    parameters: Payload
    description: str = ""


class CallDecision(StrictModel):
    kind: Literal["CALL"]
    tool_name: str = Field(min_length=1)
    arguments: Payload


class AskArguments(StrictModel):
    params: list[str] = Field(min_length=1)


class AskDecision(StrictModel):
    kind: Literal["ASK"]
    tool_name: str = Field(min_length=1)
    arguments: AskArguments


class DoneDecision(StrictModel):
    kind: Literal["DONE"]


Decision: TypeAlias = Annotated[
    CallDecision | AskDecision | DoneDecision, Field(discriminator="kind")
]


class DecisionRecord(RootModel[Decision]):
    pass


DECISION = DecisionRecord


class SubmissionRow(StrictModel):
    id: str = Field(min_length=1)
    tool_calls: list[ToolCall]
    state_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class TimedSubmissionRow(SubmissionRow):
    time: int = Field(ge=0)


class ObservationRecord(ToolCall):
    result: JsonValue
    outcome: Literal[
        "SCHEMA_REJECTED",
        "BUSINESS_NOOP",
        "WRITE_EFFECT",
        "READ_OBSERVATION",
        "META_WAIT",
        "UNKNOWN",
    ]


class ReferenceEvidence(StrictModel):
    value: str
    source: str
    ref_type: str | None = None
    attributes: Payload = Field(default_factory=dict)


class Condition(StrictModel):
    tool_name: str
    field: str
    operator: Literal["eq", "ne", "gt", "ge", "lt", "le", "contains"]
    value: JsonValue


class GoalOccurrence(StrictModel):
    id: str
    span: list[int] = Field(min_length=2, max_length=2)
    status: Literal["PENDING", "COMPLETE", "BLOCKED", "CANCELED", "QUARANTINED"] = "PENDING"
    observation_ids: list[int] = Field(default_factory=list)
    attempts: int = 0


class Goal(StrictModel):
    id: str
    intent: str
    tool_name: str
    arguments: Payload = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
    condition: Condition | None = None
    occurrences: list[GoalOccurrence] = Field(min_length=1)


class GoalPlan(StrictModel):
    goals: list[Goal]


class FoldRecord(StrictModel):
    source_split: Literal["train"]
    seed: int
    dataset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    fit_ids: list[str] = Field(min_length=1)
    validation_ids: list[str] = Field(min_length=1)
    leave_app_out: Payload | None = None

    @model_validator(mode="after")
    def disjoint(self):
        if len(set(self.fit_ids)) != len(self.fit_ids) or len(set(self.validation_ids)) != len(
            self.validation_ids
        ):
            raise ValueError("Duplicate frozen IDs")
        if set(self.fit_ids) & set(self.validation_ids):
            raise ValueError("Overlapping frozen IDs")
        return self


class Message(StrictModel):
    role: Literal["system", "user", "assistant"]
    content: str


class TrajectoryRecord(StrictModel):
    scenario_id: str
    source_split: Literal["train"]
    partition: Literal["fit", "validation"]
    step_index: int = Field(ge=0)
    messages: list[Message]
    target: Payload
    fold: Literal["grouped", "leave-app-out"] = "grouped"
    identities: dict[str, str]


class RunMetadata(StrictModel):
    split: Literal["train", "public_test", "private_test"] | None = None
    input_mode: Literal["oracle", "audio"] | None = None
    fold: str | None = None
    selection: str | None = None
    backend: str | None = None
    settings: Payload = Field(default_factory=dict)
    model: Payload = Field(default_factory=dict)
    status: Literal["RUNNING", "FAILED", "INTERRUPTED", "COMPLETE"]
    selected_ids: list[str]
    completed_ids: list[str] = Field(default_factory=list)
    identities: dict[str, str] = Field(default_factory=dict)
    error_type: str | None = None


class DiagnosticRecord(StrictModel):
    generations: int = Field(default=0, ge=0)
    timing: dict[str, float | None] = Field(default_factory=dict)
    transcriptions: list[Payload] = Field(default_factory=list)
    id: str
    stop_reason: str
    elapsed_seconds: float = Field(ge=0)
    steps: list[Payload]
    goals: list[Goal] = Field(default_factory=list)


class TrainingRunRecord(StrictModel):
    status: Literal["RUNNING", "FAILED", "INTERRUPTED", "COMPLETE"]
    identities: dict[str, str]
    metrics: Payload = Field(default_factory=dict)
    error_type: str | None = None
