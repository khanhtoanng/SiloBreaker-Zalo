"""Validated command configuration; JSON file paths resolve beside their config."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from .contracts import StrictModel, json_loads


class RunConfig(StrictModel):
    max_decisions: int = Field(default=9, ge=1)
    sample_seconds: float = Field(default=25.0, gt=0, allow_inf_nan=False)
    max_repairs: int = Field(default=1, ge=0)
    require_reference_provenance: bool = False
    done_reconsiderations: int = Field(default=1, ge=0, le=1)
    max_generations: int = Field(default=32, ge=1)
    max_context_tokens: int = Field(default=16384, gt=256)
    max_new_tokens: int = Field(default=512, ge=1)

    @model_validator(mode="after")
    def context_budget(self):
        if self.max_context_tokens <= self.max_new_tokens + 256:
            raise ValueError("Context must exceed generation budget plus framing")
        return self


class InferenceConfig(RunConfig):
    data_root: Path
    out: Path
    split: Literal["train", "public_test", "private_test"] = "train"
    input_mode: Literal["oracle", "audio"] = "oracle"
    selection: Literal["validation", "fit", "all"] = "validation"
    fold: Literal["grouped", "leave-app-out"] = "grouped"
    split_config: Path | None = None
    backend: Literal["ollama", "transformers", "llama_cpp"] = "ollama"
    model_path: Path | None = None
    tokenizer_path: Path | None = None
    adapter_path: Path | None = None
    asr_path: Path | None = None
    ollama_model: str = "qwen3:4b-instruct-2507-q4_K_M"
    ollama_url: str = "http://127.0.0.1:11434"
    limit: int | None = Field(default=None, ge=1)
    include_timing: bool = False
    llama_server_path: Path | None = None

    @model_validator(mode="after")
    def modes(self):
        if self.backend == "ollama":
            from .adapters.ollama import local_url

            local_url(self.ollama_url)
            if "cloud" in self.ollama_model.lower():
                raise ValueError("Cloud models are forbidden")
        if self.input_mode == "oracle" and self.split != "train":
            raise ValueError("Oracle text is train-only")
        if self.selection != "all" and self.split_config is None:
            raise ValueError("Frozen selection requires split_config")
        if self.split != "train" and self.selection != "all":
            raise ValueError("Test splits require explicit all selection")
        if self.backend == "transformers" and self.model_path is None:
            raise ValueError("Transformers requires model_path")
        if self.backend == "llama_cpp" and (
            self.model_path is None or self.llama_server_path is None
        ):
            raise ValueError("llama_cpp requires a local GGUF model_path and llama_server_path")
        if self.input_mode == "audio" and self.asr_path is None:
            raise ValueError("Audio requires local asr_path")
        return self


class PreparationConfig(StrictModel):
    data_root: Path
    out: Path
    split_config: Path | None = None
    seed: int = 20261109
    heldout_app: str | None = "banking"
    fold: Literal["grouped", "leave-app-out"] = "grouped"


class EvaluationConfig(StrictModel):
    data_root: Path
    out: Path
    split_config: Path
    predictions: Path
    replay: Path
    fold: Literal["grouped", "leave-app-out"] = "grouped"
    limit: int | None = Field(default=None, ge=1)


class TrainingConfig(StrictModel):
    source_split: Literal["train"] = "train"
    base_model: Path
    tokenizer_path: Path
    trajectories: Path
    split_config: Path
    out: Path
    dataset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    trajectories_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    split_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    template_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    fold: Literal["grouped", "leave-app-out"] = "grouped"
    rank: int = Field(default=16, ge=1)
    alpha: int = Field(default=32, ge=1)
    dropout: float = Field(default=0.05, ge=0, lt=1)
    target_modules: list[str] = Field(default_factory=lambda: ["q_proj", "v_proj"], min_length=1)
    epochs: float = Field(default=1.0, gt=0)
    learning_rate: float = Field(default=0.0002, gt=0)
    batch_size: int = Field(default=1, ge=1)
    accumulation_steps: int = Field(default=8, ge=1)
    seed: int = 20261109
    precision: Literal["fp32", "fp16", "bf16"] = "fp32"
    max_sequence_length: int = Field(default=8192, ge=32)


PATH_FIELDS = {
    "data_root",
    "out",
    "split_config",
    "model_path",
    "tokenizer_path",
    "adapter_path",
    "asr_path",
    "llama_server_path",
    "base_model",
    "trajectories",
    "predictions",
    "replay",
}


def resolve_config_values(values, base):
    values = dict(values)
    for key in PATH_FIELDS & values.keys():
        if values[key] is not None:
            values[key] = (Path(base) / values[key]).resolve()
    return values


def load_config(path, kind, overrides=None):
    path = Path(path).resolve()
    values = json_loads(path.read_text(encoding="utf-8"))
    if not isinstance(values, dict):
        raise ValueError(f"{path}: expected configuration object")
    values = resolve_config_values(values, path.parent)
    values.update(resolve_config_values(overrides or {}, Path.cwd()))
    models: dict[str, type[StrictModel]] = {
        "inference": InferenceConfig,
        "training": TrainingConfig,
        "evaluation": EvaluationConfig,
    }
    return models[kind].model_validate(values)
