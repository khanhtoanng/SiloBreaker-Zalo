"""Train-only LoRA orchestration; config/dry-run never imports heavy runtimes."""

from __future__ import annotations

from pathlib import Path

from ..adapters.protocols import TrainingRuntime
from ..artifacts import external_output, save_json
from ..config import TrainingConfig
from ..contracts import FoldRecord, TrainingRunRecord, TrajectoryRecord, json_loads, json_object
from ..provenance import digest, file_sha256, source_identity
from .serialization import ActionCollator, serialize_action, tokenized_example


def preflight(config: TrainingConfig) -> tuple[list[dict], Path]:
    inputs = [config.base_model, config.tokenizer_path, config.trajectories, config.split_config]
    out = external_output(config.out, inputs=inputs)
    for path in (config.base_model, config.tokenizer_path):
        if not path.is_dir():
            raise FileNotFoundError(f"Local model/tokenizer missing: {path}")
    for path, expected in (
        (config.trajectories, config.trajectories_sha256),
        (config.split_config, config.split_sha256),
    ):
        if not path.is_file() or file_sha256(path) != expected:
            raise ValueError(f"Missing/drifted input fingerprint: {path}")
    folds = FoldRecord.model_validate(json_loads(config.split_config.read_text(encoding="utf-8")))
    if folds.dataset_sha256 != config.dataset_sha256:
        raise ValueError("Frozen dataset fingerprint differs")
    selected = folds.model_dump()
    if config.fold == "leave-app-out":
        if not folds.leave_app_out:
            raise ValueError("Missing leave-app-out fold")
        selected.update(folds.leave_app_out)
    fit, val = selected["fit_ids"], selected["validation_ids"]
    if (
        len(fit) != len(set(fit))
        or len(val) != len(set(val))
        or not fit
        or not val
        or set(fit) & set(val)
        or set(fit) | set(val) != set(folds.fit_ids) | set(folds.validation_ids)
    ):
        raise ValueError("Invalid selected frozen fold")
    tok_config = config.tokenizer_path / "tokenizer_config.json"
    if not tok_config.is_file():
        raise FileNotFoundError("Local tokenizer_config.json required")
    template = json_object(tok_config.read_text(encoding="utf-8")).get("chat_template")
    if not isinstance(template, str) or digest(template) != config.template_sha256:
        raise ValueError("Tokenizer template identity differs")
    rows: list[dict] = []
    steps: dict[str, int] = {}
    ended = set()
    with config.trajectories.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = TrajectoryRecord.model_validate(json_loads(line)).model_dump()
            sid = row["scenario_id"]
            partition = "fit" if sid in fit else "validation" if sid in val else None
            if partition is None or row["partition"] != partition or row["fold"] != config.fold:
                raise ValueError(f"Trajectory line {line_number}: source/fold/partition mismatch")
            if row["identities"].get("dataset_sha256") != config.dataset_sha256:
                raise ValueError("Trajectory dataset identity differs")
            if row["identities"].get("split_sha256") != config.split_sha256:
                raise ValueError("Trajectory frozen split identity differs")
            if (
                row["identities"].get("protocol") != "lifemate-json-v1"
                or row["identities"].get("context") != "lifemate-context-v1"
            ):
                raise ValueError("Trajectory protocol/context identity differs")
            if not row["identities"].get("schema_sha256") or not row["identities"].get(
                "fold_sha256"
            ):
                raise ValueError("Missing schema/fold provenance")
            if rows and row["identities"] != rows[0]["identities"]:
                raise ValueError("Mixed trajectory provenance")
            if sid in ended or row["step_index"] != steps.get(sid, 0):
                raise ValueError("Trajectory sequence is not contiguous")
            if [m["role"] for m in row["messages"]] != ["system", "user", "assistant"]:
                raise ValueError("Unexpected trajectory role shape")
            if serialize_action(row["target"]) != serialize_action(row["messages"][-1]["content"]):
                raise ValueError("Target identity differs")
            payload = json_object(row["messages"][-2]["content"])
            if config.fold == "leave-app-out":
                app = selected.get("app")
                if not isinstance(app, str) or not app:
                    raise ValueError("Missing held-out app provenance")
                exposed = app in payload.get("context", {}).get("installed_apps", {})
                if exposed != (partition == "validation"):
                    raise ValueError("Held-out app trajectory exposure conflicts with partition")
            if len(payload["observations"]) != row["step_index"]:
                raise ValueError("Future/missing observation prefix")
            steps[sid] = row["step_index"] + 1
            if row["target"]["kind"] == "DONE":
                ended.add(sid)
            rows.append(row)
    if set(steps) != set(fit) | set(val) or ended != set(steps):
        raise ValueError("Incomplete scenario coverage/terminal DONE")
    return rows, out


class LoraRuntime:
    def train(self, rows: list[dict], config: TrainingConfig) -> dict:
        import os

        os.environ.update(
            HF_HUB_OFFLINE="1",
            TRANSFORMERS_OFFLINE="1",
            HF_HUB_DISABLE_TELEMETRY="1",
            WANDB_DISABLED="true",
        )
        try:
            import torch  # type: ignore[import-not-found,import-untyped]
            from datasets import Dataset  # type: ignore[import-not-found,import-untyped]
            from peft import LoraConfig  # type: ignore[import-not-found,import-untyped]
            from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed  # type: ignore[import-not-found,import-untyped]
            from trl import SFTConfig, SFTTrainer  # type: ignore[import-not-found,import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "Install reviewed training extra in a separate training environment"
            ) from exc
        if config.precision != "fp32" and not torch.cuda.is_available():
            raise ValueError("Selected training precision requires a reviewed CUDA platform")
        if config.precision == "bf16" and not torch.cuda.is_bf16_supported():
            raise ValueError("CUDA device lacks bf16 support")
        set_seed(config.seed)
        tokenizer = AutoTokenizer.from_pretrained(
            config.tokenizer_path, local_files_only=True, trust_remote_code=False
        )
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
        data = {
            part: [
                tokenized_example(row, tokenizer, config.max_sequence_length)
                for row in rows
                if row["partition"] == part
            ]
            for part in ("fit", "validation")
        }
        dtype = {"fp32": torch.float32, "fp16": torch.float16, "bf16": torch.bfloat16}[
            config.precision
        ]
        model = AutoModelForCausalLM.from_pretrained(
            config.base_model, local_files_only=True, trust_remote_code=False, torch_dtype=dtype
        )
        peft = LoraConfig(
            r=config.rank,
            lora_alpha=config.alpha,
            lora_dropout=config.dropout,
            target_modules=config.target_modules,
            task_type="CAUSAL_LM",
            bias="none",
        )
        options = SFTConfig(
            output_dir=str(config.out / "checkpoints"),
            num_train_epochs=config.epochs,
            learning_rate=config.learning_rate,
            per_device_train_batch_size=config.batch_size,
            per_device_eval_batch_size=config.batch_size,
            gradient_accumulation_steps=config.accumulation_steps,
            seed=config.seed,
            fp16=config.precision == "fp16",
            bf16=config.precision == "bf16",
            report_to="none",
            packing=False,
            padding_free=False,
            max_length=None,
            remove_unused_columns=False,
            dataset_kwargs={"skip_prepare_dataset": True},
            eval_strategy="epoch",
            save_strategy="epoch",
        )
        trainer = SFTTrainer(
            model=model,
            args=options,
            train_dataset=Dataset.from_list(data["fit"]),
            eval_dataset=Dataset.from_list(data["validation"]),
            processing_class=tokenizer,
            data_collator=ActionCollator(tokenizer.pad_token_id, tensor=True),
            peft_config=peft,
        )
        result = trainer.train()
        trainer.save_model(str(config.out / "adapter"))
        tokenizer.save_pretrained(str(config.out / "tokenizer"))
        return {k: float(v) for k, v in result.metrics.items() if isinstance(v, (int, float))}


def train(
    config: TrainingConfig, *, dry_run: bool = False, runtime: TrainingRuntime | None = None
) -> dict:
    rows, out = preflight(config)
    identities = {
        "dataset_sha256": config.dataset_sha256,
        "trajectories_sha256": config.trajectories_sha256,
        "split_sha256": config.split_sha256,
        "template_sha256": config.template_sha256,
        "source_sha256": source_identity(),
        "config_sha256": digest(config.model_dump(mode="json")),
    }
    if dry_run:
        return {"status": "NOT RUN", "rows": len(rows), "identities": identities}
    out.mkdir(parents=True, exist_ok=False)
    meta = TrainingRunRecord(status="RUNNING", identities=identities)
    save_json(out / "run.json", meta.model_dump())
    try:
        save_json(out / "config.json", config.model_dump(mode="json"))
        declared = {}
        for label, directory in (
            ("base_model", config.base_model),
            ("tokenizer", config.tokenizer_path),
        ):
            declared[label] = {
                "path": str(directory),
                "metadata_sha256": {
                    name: file_sha256(directory / name)
                    for name in (
                        "config.json",
                        "generation_config.json",
                        "tokenizer_config.json",
                        "tokenizer.json",
                        "special_tokens_map.json",
                    )
                    if (directory / name).is_file()
                },
                "weights_identity": "UNMEASURED; metadata fingerprints do not identify model weights",
            }
        save_json(out / "inputs.json", declared)
        metrics = (runtime or LoraRuntime()).train(rows, config)
        if (
            not (out / "adapter/adapter_config.json").is_file()
            or not any(
                (out / "adapter" / name).is_file()
                for name in ("adapter_model.safetensors", "adapter_model.bin")
            )
            or not (out / "tokenizer/tokenizer_config.json").is_file()
        ):
            raise ValueError("Trainer returned without required saved adapter/tokenizer")
        saved = {
            p.relative_to(out).as_posix(): file_sha256(p)
            for directory in (out / "adapter", out / "tokenizer")
            for p in directory.iterdir()
            if p.is_file()
        }
        save_json(
            out / "provenance.json",
            {
                "identities": identities,
                "inputs": declared,
                "saved_artifact_sha256": saved,
                "configuration": config.model_dump(mode="json"),
            },
        )
        save_json(out / "metrics.json", metrics)
        meta.status = "COMPLETE"
        meta.metrics = metrics
    except BaseException as exc:
        meta.status = "INTERRUPTED" if isinstance(exc, KeyboardInterrupt) else "FAILED"
        meta.error_type = type(exc).__name__
        save_json(out / "run.json", meta.model_dump(), replace=True)
        raise
    save_json(out / "run.json", meta.model_dump(), replace=True)
    return meta.model_dump()
