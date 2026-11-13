"""Application orchestration. CLI parsing and optional runtime creation stay separate."""

from __future__ import annotations

import importlib.util
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .adapters.protocols import Asr, Clock, Policy, Session
from .artifacts import external_output as external_output
from .artifacts import save_json as save_json
from .artifacts import write_jsonl
from .config import (
    EvaluationConfig,
    InferenceConfig,
    PreparationConfig,
    RunConfig,
    TrainingConfig,
    load_config,
    resolve_config_values,
)
from .contracts import INFERENCE_SEED, RunMetadata, StrictModel, json_loads, json_object
from .data.kit import (
    frozen_split,
    inference_input,
    load_catalog,
    load_manifest,
    read_jsonl,
    resolve_data_root,
)
from .data.splits import load_partition as load_partition
from .prediction_artifacts import PredictionArtifacts
from .provenance import digest, file_sha256, source_identity
from .runtime.loop import infer
from .submission import validate_submission


def command_config(values, kind):
    values = dict(values)
    path = values.pop("config", None)
    if path:
        return load_config(path, kind, values)
    models: dict[str, type[StrictModel]] = {
        "inference": InferenceConfig,
        "evaluation": EvaluationConfig,
        "training": TrainingConfig,
    }
    return models[kind].model_validate(resolve_config_values(values, Path.cwd()))


def bundle(root, split):
    root = resolve_data_root(root)
    for name in (f"{split}.jsonl", f"{split}_tools_catalog.json", "zaic_tools/__init__.py"):
        if not (root / split / name).is_file():
            raise FileNotFoundError(f"Missing selected {split} asset: {name}")
    return root


def selected_rows(config, root, rows):
    if config.selection == "all":
        selected = rows
    else:
        folds = load_partition(
            config.split_config, rows, manifest_path=root / "train/train.jsonl", fold=config.fold
        )
        wanted = set(folds[config.selection + "_ids"])
        selected = [row for row in rows if row["id"] in wanted]
    if config.limit is not None:
        selected = selected[: config.limit]
    if not selected:
        raise ValueError("Selected manifest is empty")
    return selected


def create_policy(config: InferenceConfig) -> Policy:
    if config.backend == "llama_cpp":
        from .adapters.llama_cpp import LlamaCppPolicy

        return LlamaCppPolicy(
            config.llama_server_path,
            config.model_path,
            max_context_tokens=config.max_context_tokens,
            max_new_tokens=config.max_new_tokens,
        )
    if config.backend == "ollama":
        from .adapters.ollama import OllamaPolicy

        return OllamaPolicy(
            config.ollama_model,
            config.ollama_url,
            max_context_tokens=config.max_context_tokens,
            max_new_tokens=config.max_new_tokens,
            tokenizer_path=config.tokenizer_path,
        )
    from .adapters.transformers import LocalPolicy

    return LocalPolicy(
        config.model_path,
        max_context_tokens=config.max_context_tokens,
        max_new_tokens=config.max_new_tokens,
        tokenizer_path=config.tokenizer_path,
        adapter_path=config.adapter_path,
    )


def seed_inference():
    import random

    import numpy as np
    import torch

    random.seed(INFERENCE_SEED)
    np.random.seed(INFERENCE_SEED)
    torch.manual_seed(INFERENCE_SEED)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


@dataclass(frozen=True)
class PredictionModels:
    policy: Policy
    asr: Asr | None
    load_seconds: float

    def close(self):
        close = getattr(self.policy, "close", None)
        if close is not None:
            close()


def load_prediction_models(config, *, policy_factory=create_policy, asr_factory=None, clock=time):
    started = clock.monotonic()
    if policy_factory is create_policy and config.backend in {"transformers", "llama_cpp"}:
        seed_inference()
    policy = policy_factory(config)
    asr = None
    try:
        if config.input_mode == "audio":
            if asr_factory is None:
                from .adapters.whisper import WhisperAsr

                asr_factory = WhisperAsr
            asr = asr_factory(config.asr_path)
    except BaseException:
        PredictionModels(policy, None, 0).close()
        raise
    return PredictionModels(policy, asr, clock.monotonic() - started)


def prediction_inputs(config):
    root = bundle(config.data_root, config.split)
    rows = selected_rows(config, root, load_manifest(root, config.split))
    return root, rows, load_catalog(root, config.split)


def predict(
    config: InferenceConfig,
    *,
    policy_factory: Callable[[InferenceConfig], Policy] = create_policy,
    asr_factory: Callable[..., Asr] | None = None,
    env_factory: Callable[..., Session] | None = None,
    clock: Clock = time,
    models: PredictionModels | None = None,
    prepared_inputs=None,
) -> dict:
    root = bundle(config.data_root, config.split)
    inputs = [
        config.data_root,
        root,
        config.model_path,
        config.tokenizer_path,
        config.adapter_path,
        config.asr_path,
        config.llama_server_path,
        config.split_config,
    ]
    artifacts = PredictionArtifacts(config.out, inputs=inputs, include_timing=config.include_timing)
    _, rows, catalog = prepared_inputs or prediction_inputs(config)
    # Validate every selected inference projection before optional backend/session setup.
    samples = [
        inference_input(row, oracle_text=config.input_mode == "oracle", split=config.split)
        for row in rows
    ]
    run_settings = {key: getattr(config, key) for key in RunConfig.model_fields}
    runtime_config = RunConfig.model_validate(run_settings)
    metadata = RunMetadata(
        split=config.split,
        input_mode=config.input_mode,
        fold=config.fold,
        selection=config.selection,
        backend=config.backend,
        settings={
            **run_settings,
            "seed": INFERENCE_SEED,
            "decoding": "greedy",
            "include_timing": config.include_timing,
        },
        status="RUNNING",
        selected_ids=[r["id"] for r in rows],
        identities={
            "source_sha256": source_identity(),
            "dataset_sha256": file_sha256(root / config.split / f"{config.split}.jsonl"),
            "catalog_sha256": digest(catalog),
            "config_sha256": digest(config.model_dump(mode="json")),
        },
    )
    if config.split_config is not None:
        metadata.identities["split_sha256"] = file_sha256(config.split_config)
    metadata.identities["sdk_entrypoint_sha256"] = file_sha256(
        root / config.split / "zaic_tools/__init__.py"
    )
    artifacts.start(metadata)
    owns_models = models is None
    try:
        models = models or load_prediction_models(
            config, policy_factory=policy_factory, asr_factory=asr_factory, clock=clock
        )
        policy = models.policy
        available = getattr(policy, "metadata", {})
        model_metadata = {
            key: available[key]
            for key in (
                "backend",
                "model",
                "model_path",
                "tokenizer_path",
                "adapter_path",
                "digest",
                "license_sha256",
                "template_sha256",
                "max_context_tokens",
                "max_new_tokens",
                "temperature",
                "seed",
                "think",
                "format",
                "token_budget_method",
            )
            if key in available
        }
        artifacts.record_model(model_metadata)
        kwargs: dict = {"clock": clock}
        if env_factory is not None:
            kwargs["env_factory"] = env_factory
        if config.input_mode == "audio":
            from .adapters.whisper import prepare_audio

            asr = models.asr
            if asr is None:
                raise ValueError("Audio prediction requires a loaded ASR model")
            kwargs["prepare"] = lambda value, deadline: prepare_audio(
                value, root / config.split / "audio", asr, deadline=deadline, clock=clock
            )
        prediction_seconds = 0.0
        for sample in samples:
            result, diagnostic = infer(
                sample,
                root,
                config.split,
                catalog,
                policy,
                runtime_config,
                **kwargs,
            )
            prediction_seconds += diagnostic["elapsed_seconds"]
            artifacts.record_sample(
                sample["id"], result, diagnostic, setup_seconds=models.load_seconds
            )
        summary = artifacts.complete()
        if config.include_timing:
            summary.update(
                model_load_seconds=models.load_seconds, prediction_seconds=prediction_seconds
            )
        return summary
    except BaseException as exc:
        try:
            artifacts.fail(exc)
        except Exception as artifact_error:
            raise exc from artifact_error
        raise
    finally:
        if owns_models and models is not None:
            models.close()


def package_check(config: InferenceConfig) -> dict:
    root = bundle(config.data_root, config.split)
    external_output(
        config.out,
        inputs=[
            config.data_root,
            root,
            config.model_path,
            config.asr_path,
            config.adapter_path,
            config.tokenizer_path,
            config.llama_server_path,
        ],
    )
    for field in ("model_path", "tokenizer_path", "adapter_path", "asr_path", "llama_server_path"):
        value = getattr(config, field)
        if value is not None and not value.exists():
            raise FileNotFoundError(f"Missing local {field}: {value}")
    deps = ["torch", "transformers"] if config.backend == "transformers" else []
    if config.input_mode == "audio":
        deps += ["torch", "transformers", "soundfile", "scipy"]
    return {
        "status": "STATIC_ONLY",
        "missing_dependencies": [
            d for d in sorted(set(deps)) if importlib.util.find_spec(d) is None
        ],
        "backend": config.backend,
        "entrypoint": "predict.sh -> python -m lifemate predict",
        "offline_runtime": "NOT RUN",
        "official_contract": "UNKNOWN",
    }


def dispatch(command: str, values: dict) -> dict:
    values = dict(values)
    if command == "config-check":
        config = load_config(values["config"], values["kind"])
        external_output(
            config.out,
            inputs=[
                getattr(config, key, None)
                for key in (
                    "data_root",
                    "model_path",
                    "asr_path",
                    "llama_server_path",
                    "adapter_path",
                    "tokenizer_path",
                    "base_model",
                    "trajectories",
                    "split_config",
                    "predictions",
                    "replay",
                )
            ],
        )
        return {
            "status": "CONFIG_VALID",
            "kind": values["kind"],
            "runtime": "NOT RUN",
            "config": config.model_dump(mode="json"),
        }
    if command == "train":
        from .learning.trainer import train

        dry = values.pop("dry_run", False)
        return train(command_config(values, "training"), dry_run=dry)
    if command == "predict":
        # Legacy no-mode invocation remains frozen train oracle; supplied flags override config.
        if "config" not in values and values.get("model_path") and "backend" not in values:
            values["backend"] = "transformers"
        return predict(command_config(values, "inference"))
    if command == "package-check":
        return package_check(command_config(values, "inference"))
    if command in ("compare", "asr-evaluate"):
        from .metrics.asr import evaluate_asr
        from .metrics.reports import compare

        before = Path(values["baseline"] if "baseline" in values else values["reference"])
        after = Path(values["candidate"])
        out = external_output(values["out"], inputs=[before, after])
        report = (compare if command == "compare" else evaluate_asr)(
            json_loads(before.read_text(encoding="utf-8")),
            json_loads(after.read_text(encoding="utf-8")),
        )
        save_json(out, report)
        return report
    if command == "evaluate":
        from .metrics.reports import evaluate_report

        config = command_config(values, "evaluation")
        root = bundle(config.data_root, "train")
        out = external_output(
            config.out,
            inputs=[config.data_root, root, config.replay, config.predictions, config.split_config],
        )
        rows = load_manifest(root, "train")
        fold = load_partition(
            config.split_config, rows, manifest_path=root / "train/train.jsonl", fold=config.fold
        )
        selected = [r for r in rows if r["id"] in fold["validation_ids"]]
        if config.limit is not None:
            selected = selected[: config.limit]
        replay = json_object(config.replay.read_text(encoding="utf-8"))
        if replay.get("dataset_sha256") != file_sha256(root / "train/train.jsonl"):
            raise ValueError("Replay dataset fingerprint differs")
        report = evaluate_report(
            read_jsonl(config.predictions),
            selected,
            replay["records"],
            load_catalog(root, "train"),
            identity={
                "dataset_sha256": fold["dataset_sha256"],
                "fold_sha256": file_sha256(config.split_config),
                "replay_sha256": file_sha256(config.replay),
                "matching": "PROXY-v1",
            },
        )
        save_json(out, report)
        return report
    if command == "validate":
        root = bundle(values["data_root"], values.get("split", "train"))
        out = external_output(
            values["out"], inputs=[values["data_root"], root, values["predictions"]]
        )
        rows = load_manifest(root, values.get("split", "train"))
        validate_submission(
            read_jsonl(values["predictions"]),
            [r["id"] for r in rows],
            include_timing=values.get("include_timing", False),
        )
        result = {
            "status": "PASS",
            "samples": len(rows),
            "scope": "manifest/shape/hash-format; SDK validation separate",
        }
        save_json(out, result)
        return result
    cfg = PreparationConfig.model_validate(resolve_config_values(values, Path.cwd()))
    root = resolve_data_root(cfg.data_root)
    out = external_output(cfg.out, inputs=[cfg.data_root, root, cfg.split_config])
    catalog = load_catalog(root, "train")
    if command == "audit":
        result = {
            "kind": "SAFE_CATALOG_AUDIT",
            "tools": len(catalog),
            "apps": sorted({t["app"] for t in catalog.values()}),
            "catalog_sha256": digest(catalog),
            "sdk_present": (root / "train/zaic_tools/__init__.py").is_file(),
        }
    else:
        rows = load_manifest(root, "train")
        if command == "freeze":
            result = frozen_split(
                rows, root / "train/train.jsonl", cfg.seed, heldout_app=cfg.heldout_app
            )
        elif command == "replay":
            from .data.replay import replay_gold

            result = replay_gold(rows, root)
            result["dataset_sha256"] = file_sha256(root / "train/train.jsonl")
        elif command == "trajectories":
            from .learning.trajectories import expand_train

            if cfg.split_config is None:
                raise ValueError("trajectories requires split_config")
            folds = load_partition(
                cfg.split_config, rows, manifest_path=root / "train/train.jsonl", fold=cfg.fold
            )
            records = list(
                expand_train(
                    rows,
                    root,
                    catalog,
                    folds,
                    fold=cfg.fold,
                    identities={
                        "dataset_sha256": folds["dataset_sha256"],
                        "split_sha256": file_sha256(cfg.split_config),
                        "fold_sha256": digest(folds),
                        "schema_sha256": digest(catalog),
                        "protocol": "lifemate-json-v1",
                        "context": "lifemate-context-v1",
                        "source_sha256": source_identity(),
                    },
                )
            )
            write_jsonl(out, records)
            return {"trajectory_rows": len(records), "output": str(out)}
        else:
            raise ValueError("Unknown command")
    save_json(out, result)
    return result
