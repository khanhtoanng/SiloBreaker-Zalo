import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lifemate.artifacts import save_json, write_jsonl
from lifemate.config import TrainingConfig
from lifemate.learning.serialization import ActionCollator, serialize_action, tokenized_example
from lifemate.learning.trainer import train
from lifemate.provenance import digest, file_sha256


class Tokenizer:
    eos_token_id = 0
    pad_token_id = 0

    def apply_chat_template(self, messages, **kwargs):
        return "PROMPT:" + json.dumps(messages, ensure_ascii=False) + "ASSISTANT:"

    def __call__(self, text, **kwargs):
        return {"input_ids": [ord(c) + 1 for c in text]}

    def decode(self, ids, **kwargs):
        return "".join(chr(i - 1) for i in ids)


def training_fixture(root):
    base = root / "base"
    base.mkdir()
    save_json(base / "config.json", {"model_type": "fixture"})
    save_json(base / "tokenizer_config.json", {"chat_template": "template"})
    fold = {
        "source_split": "train",
        "seed": 1,
        "dataset_sha256": "a" * 64,
        "fit_ids": ["fit"],
        "validation_ids": ["val"],
    }
    save_json(root / "split.json", fold)
    rows = []
    for sid, partition in (("fit", "fit"), ("val", "validation")):
        target = {"kind": "DONE"}
        rows.append(
            {
                "scenario_id": sid,
                "source_split": "train",
                "partition": partition,
                "fold": "grouped",
                "step_index": 0,
                "messages": [
                    {"role": "system", "content": "schema"},
                    {"role": "user", "content": '{"observations":[]}'},
                    {"role": "assistant", "content": serialize_action(target)},
                ],
                "target": target,
                "identities": {
                    "dataset_sha256": "a" * 64,
                    "split_sha256": file_sha256(root / "split.json"),
                    "protocol": "lifemate-json-v1",
                    "context": "lifemate-context-v1",
                    "schema_sha256": "b" * 64,
                    "fold_sha256": "c" * 64,
                },
            }
        )
    write_jsonl(root / "data.jsonl", rows)
    cfg = TrainingConfig(
        base_model=base,
        tokenizer_path=base,
        trajectories=root / "data.jsonl",
        split_config=root / "split.json",
        out=root / "new-run",
        dataset_sha256="a" * 64,
        trajectories_sha256=file_sha256(root / "data.jsonl"),
        split_sha256=file_sha256(root / "split.json"),
        template_sha256=digest("template"),
    )
    return cfg, rows


class TrainingTests(unittest.TestCase):
    def test_single_action_masks_call_ask_done_previous_action_not_supervised(self):
        tokenizer = Tokenizer()
        for target in (
            {"kind": "CALL", "tool_name": "x.read", "arguments": {}},
            {"kind": "ASK", "tool_name": "x.write", "arguments": {"params": ["id"]}},
            {"kind": "DONE"},
        ):
            row = {
                "messages": [
                    {"role": "system", "content": "schema"},
                    {"role": "user", "content": "previous assistant CALL and actual observation"},
                    {"role": "assistant", "content": serialize_action(target)},
                ],
                "target": target,
            }
            item = tokenized_example(row, tokenizer, 4096)
            n = next(i for i, x in enumerate(item["labels"]) if x != -100)
            self.assertTrue(all(x == -100 for x in item["labels"][:n]))
            self.assertEqual(item["labels"][n:], item["input_ids"][n:])
            self.assertEqual(item["labels"][-1], 0)

    def test_padding_equals_eos_still_masked(self):
        batch = ActionCollator(0)(
            [
                {"input_ids": [1, 2, 0], "attention_mask": [1, 1, 1], "labels": [-100, 2, 0]},
                {"input_ids": [3, 0], "attention_mask": [1, 1], "labels": [3, 0]},
            ]
        )
        self.assertEqual(batch["labels"][1], [3, 0, -100])
        self.assertEqual(batch["attention_mask"][1], [1, 1, 0])

    def test_overflow_and_tokenizer_boundary_rejected(self):
        row = {
            "messages": [
                {"role": "system", "content": "schema"},
                {"role": "user", "content": "context"},
                {"role": "assistant", "content": '{"kind":"DONE"}'},
            ]
        }
        with self.assertRaisesRegex(ValueError, "CONTEXT_OVERFLOW"):
            tokenized_example(row, Tokenizer(), 1)

        class Bad(Tokenizer):
            def __call__(self, text, **kw):
                return {"input_ids": [len(text)]}

        with self.assertRaisesRegex(ValueError, "prefix"):
            tokenized_example(row, Bad(), 4096)

    def test_dry_run_no_heavy_runtime_or_output(self):
        with tempfile.TemporaryDirectory() as d:
            cfg, rows = training_fixture(Path(d))
            with patch(
                "lifemate.learning.trainer.LoraRuntime",
                side_effect=AssertionError("runtime must stay lazy"),
            ):
                result = train(cfg, dry_run=True)
            self.assertEqual(result["status"], "NOT RUN")
            self.assertFalse(cfg.out.exists())

    def test_injected_train_save_options_and_identity(self):
        with tempfile.TemporaryDirectory() as d:
            cfg, rows = training_fixture(Path(d))
            seen = []

            class Runtime:
                def train(self, inputs, config):
                    seen.append((inputs, config))
                    save_json(config.out / "adapter/adapter_config.json", {"r": config.rank})
                    (config.out / "adapter/adapter_model.safetensors").write_bytes(b"synthetic")
                    save_json(
                        config.out / "tokenizer/tokenizer_config.json",
                        {"chat_template": "template"},
                    )
                    return {"loss": 0.25}

            result = train(cfg, runtime=Runtime())
            self.assertEqual(result["status"], "COMPLETE")
            self.assertEqual(seen[0][1].seed, 20261109)
            provenance = json.loads((cfg.out / "provenance.json").read_text())
            self.assertIn("adapter/adapter_model.safetensors", provenance["saved_artifact_sha256"])
            self.assertIn("UNMEASURED", provenance["inputs"]["base_model"]["weights_identity"])
            self.assertEqual(provenance["configuration"]["rank"], 16)
            with self.assertRaises(FileExistsError):
                train(cfg, runtime=Runtime())

    def test_failure_interruption_and_missing_artifacts_not_complete(self):
        for error in (RuntimeError("token=private"), KeyboardInterrupt(), None):
            with tempfile.TemporaryDirectory() as d:
                cfg, rows = training_fixture(Path(d))

                class Runtime:
                    def train(self, *args, failure=error):
                        if failure is not None:
                            raise failure
                        return {}

                with self.assertRaises((RuntimeError, KeyboardInterrupt, ValueError)):
                    train(cfg, runtime=Runtime())
                meta = json.loads((cfg.out / "run.json").read_text())
                self.assertEqual(
                    meta["status"],
                    "INTERRUPTED" if isinstance(error, KeyboardInterrupt) else "FAILED",
                )
                self.assertNotIn("private", json.dumps(meta))
                self.assertFalse((cfg.out / "provenance.json").exists())

    def test_drift_label_split_template_and_path_fail(self):
        with tempfile.TemporaryDirectory() as d:
            cfg, rows = training_fixture(Path(d))
            cfg.template_sha256 = "b" * 64
            with self.assertRaises(ValueError):
                train(cfg, dry_run=True)
            cfg.template_sha256 = digest("template")
            cfg.out = cfg.base_model / "overwrite"
            with self.assertRaises(ValueError):
                train(cfg, dry_run=True)

    def test_real_lora_runtime_passes_verified_labels_and_invokes_train_save(self):
        from types import SimpleNamespace
        from unittest.mock import patch

        from lifemate.learning.trainer import LoraRuntime

        with tempfile.TemporaryDirectory() as d:
            cfg, rows = training_fixture(Path(d))
            cfg.out.mkdir()
            seen = {}

            class LocalTokenizer(Tokenizer):
                pad_token_id = 0

                def save_pretrained(self, path):
                    save_json(Path(path) / "tokenizer_config.json", {"chat_template": "template"})

            tokenizer = LocalTokenizer()

            class LoadTokenizer:
                @staticmethod
                def from_pretrained(path, **kw):
                    seen["tokenizer_load"] = (path, kw)
                    return tokenizer

            class LoadModel:
                @staticmethod
                def from_pretrained(path, **kw):
                    seen["model_load"] = (path, kw)
                    return object()

            class Dataset:
                @staticmethod
                def from_list(rows):
                    return rows

            class Trainer:
                def __init__(self, **kw):
                    seen["trainer"] = kw

                def train(self):
                    seen["trained"] = True
                    return SimpleNamespace(metrics={"train_loss": 0.3})

                def save_model(self, path):
                    save_json(Path(path) / "adapter_config.json", {})
                    (Path(path) / "adapter_model.safetensors").write_bytes(b"synthetic")

            def options(**kw):
                seen["sft_options"] = kw
                return kw

            def lora(**kw):
                seen["lora"] = kw
                return kw

            modules = {
                "torch": SimpleNamespace(
                    float32="fp32",
                    float16="fp16",
                    bfloat16="bf16",
                    cuda=SimpleNamespace(is_available=lambda: False),
                ),
                "transformers": SimpleNamespace(
                    AutoTokenizer=LoadTokenizer,
                    AutoModelForCausalLM=LoadModel,
                    set_seed=lambda seed: seen.update(seed=seed),
                ),
                "peft": SimpleNamespace(LoraConfig=lora),
                "datasets": SimpleNamespace(Dataset=Dataset),
                "trl": SimpleNamespace(SFTConfig=options, SFTTrainer=Trainer),
            }
            with patch.dict("sys.modules", modules):
                metrics = LoraRuntime().train(rows, cfg)
            self.assertTrue(seen["trained"])
            self.assertEqual(metrics["train_loss"], 0.3)
            for loader in ("model_load", "tokenizer_load"):
                self.assertTrue(seen[loader][1]["local_files_only"])
                self.assertFalse(seen[loader][1]["trust_remote_code"])
            options = seen["sft_options"]
            self.assertEqual(options["dataset_kwargs"], {"skip_prepare_dataset": True})
            self.assertFalse(options["packing"])
            self.assertFalse(options["padding_free"])
            self.assertIsNone(options["max_length"])
            self.assertFalse(options["remove_unused_columns"])
            self.assertEqual(options["report_to"], "none")
            self.assertEqual(seen["lora"]["r"], cfg.rank)
            data = seen["trainer"]["train_dataset"][0]
            self.assertIn(-100, data["labels"])
            self.assertEqual(data["labels"][-1], 0)
            self.assertIs(seen["trainer"]["processing_class"], tokenizer)
