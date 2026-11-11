import unittest
from pathlib import Path

from pydantic import ValidationError

from lifemate.config import InferenceConfig, RunConfig
from lifemate.contracts import FoldRecord, InferenceSample, SubmissionRow, ToolSpec, json_loads
from lifemate.validator import Rejected, parse_decision


class ContractsTests(unittest.TestCase):
    def test_strict_budgets_and_unknown_config(self):
        for kwargs in (
            {"max_decisions": True},
            {"sample_seconds": 0.0},
            {"max_repairs": -1},
            {"max_decision": 2},
            {"sample_seconds": float("nan")},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValidationError):
                RunConfig(**kwargs)

    def test_catalog_extensions_roundtrip(self):
        value = {
            "name": "new.call",
            "app": "new",
            "kind": "write",
            "parameters": {
                "x-ref": "new.items",
                "x-one-of": [["a"], ["b"]],
                "nested": {"x-match": "fuzzy"},
            },
            "returns": {"type": "object"},
            "x-extension": {"nested": [1, True]},
        }
        self.assertEqual(ToolSpec.model_validate(value).model_dump(exclude_unset=True), value)

    def test_decision_strict_envelopes_and_json(self):
        for raw in (
            '{"kind":"DONE","kind":"DONE"}',
            '{"kind":"CALL","tool_name":"x.y","arguments":{"v":Infinity}}',
            '{"kind":"ASK","tool_name":"x.y","arguments":{"params":[1]}}',
            '{"kind":"DONE","goal_id":"g"}',
        ):
            with self.subTest(raw=raw), self.assertRaises(Rejected):
                parse_decision(raw)
        self.assertEqual(parse_decision('{"kind":"DONE"}'), {"kind": "DONE"})

    def test_inference_no_label_contract(self):
        with self.assertRaises(ValidationError):
            InferenceSample(id="x", label={})

    def test_oracle_test_split_rejected(self):
        with self.assertRaises(ValidationError):
            InferenceConfig(
                data_root=Path("kit"), out=Path("out"), split="public_test", selection="all"
            )

    def test_submission_no_extra_fields(self):
        with self.assertRaises(ValidationError):
            SubmissionRow(id="x", tool_calls=[], state_hash="a" * 64, diagnostics={})

    def test_fold_duplicates(self):
        with self.assertRaises(ValidationError):
            FoldRecord(
                source_split="train",
                seed=1,
                dataset_sha256="a" * 64,
                fit_ids=["a", "a"],
                validation_ids=["b"],
            )

    def test_duplicate_nested_json(self):
        with self.assertRaises(ValueError):
            json_loads('{"x":{"a":1,"a":2}}')

    def test_overflow_json_and_nested_nonfinite_dictionary(self):
        for raw in (
            '{"kind":"CALL","tool_name":"x.y","arguments":{"n":1e400}}',
            '{"kind":"CALL","tool_name":"x.y","arguments":{"n":-1e400}}',
            {"kind": "CALL", "tool_name": "x.y", "arguments": {"nested": [float("nan")]}},
        ):
            with self.subTest(raw=raw), self.assertRaises(Rejected):
                parse_decision(raw)

    def test_legacy_reference_flag_default_preserved_with_runtime_enforcement(self):
        self.assertFalse(RunConfig().require_reference_provenance)
