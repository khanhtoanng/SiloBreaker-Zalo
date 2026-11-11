import json
import tempfile
import unittest
from pathlib import Path

from test_runtime import CATALOG, SAMPLE

from lifemate.data.kit import allowed_tools, inference_input, read_jsonl
from lifemate.data.splits import validate_partition
from lifemate.workflows import bundle


class DataBoundaryTests(unittest.TestCase):
    def test_train_oracle_and_test_label_isolation(self):
        row = {
            **SAMPLE,
            "audio": "audio/a.wav",
            "audio_text": "current",
            "label": {"secret": "gold"},
            "future": "gold",
            "history": [{"role": "user", "audio_text": "old", "label": "gold"}],
        }
        clean = inference_input(row, oracle_text=True)
        self.assertNotIn("gold", json.dumps(clean))
        self.assertEqual(clean["history"][0]["text"], "old")
        with self.assertRaises(ValueError):
            inference_input(row, oracle_text=True, split="public_test")
        self.assertNotIn("text", inference_input(row))

    def test_malformed_installed_association(self):
        with self.assertRaises(ValueError):
            allowed_tools(
                {"context": {"installed_apps": {"sms": {"tools": ["contacts.search"]}}}}, CATALOG
            )

    def test_selected_bundle_completeness(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "train/train_tools_catalog.json"
            p.parent.mkdir()
            p.write_text('{"apps":[]}')
            for split in ("train", "public_test", "private_test"):
                with self.subTest(split=split), self.assertRaises(FileNotFoundError):
                    bundle(d, split)

    def test_nested_duplicate_manifest_keys(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "m.jsonl"
            p.write_text('{"id":"x","context":{"a":1,"a":2}}')
            with self.assertRaises(ValueError):
                read_jsonl(p)

    def test_leave_app_out_duplicate_foreign_overlap(self):
        rows = [{"id": "a"}, {"id": "b"}]
        config = {
            "source_split": "train",
            "seed": 1,
            "dataset_sha256": "a" * 64,
            "fit_ids": ["a"],
            "validation_ids": ["b"],
        }
        for part in (
            {"fit_ids": ["a", "a"], "validation_ids": ["b"]},
            {"fit_ids": ["a"], "validation_ids": ["foreign"]},
            {"fit_ids": ["a"], "validation_ids": ["a", "b"]},
        ):
            with self.assertRaises(ValueError):
                validate_partition({**config, "leave_app_out": part}, rows)

    def test_heldout_app_exposure_must_match_fold(self):
        rows = [
            {"id": "a", "context": {"installed_apps": {"banking": {}}}},
            {"id": "b", "context": {"installed_apps": {}}},
        ]
        config = {
            "source_split": "train",
            "seed": 1,
            "dataset_sha256": "a" * 64,
            "fit_ids": ["a"],
            "validation_ids": ["b"],
            "leave_app_out": {"app": "banking", "fit_ids": ["a"], "validation_ids": ["b"]},
        }
        with self.assertRaisesRegex(ValueError, "exposure"):
            validate_partition(config, rows)
        config["leave_app_out"] = {"app": "banking", "fit_ids": ["b"], "validation_ids": ["a"]}
        self.assertEqual(validate_partition(config, rows, fold="leave-app-out")["fit_ids"], ["b"])
