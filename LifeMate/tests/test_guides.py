import unittest
from pathlib import Path

from lifemate.config import load_config


class GuideTests(unittest.TestCase):
    def test_configs_parse_without_runtime_and_guides_match_interfaces(self):
        root = Path(__file__).resolve().parents[1]
        for name, kind in (
            ("inference.ollama.json", "inference"),
            ("inference.audio.json", "inference"),
            ("training.lora.json", "training"),
            ("evaluation.json", "evaluation"),
        ):
            model = load_config(root / "configs" / name, kind)
            self.assertTrue(model.out.is_absolute())
        for name in (
            "architecture",
            "operator_guide",
            "local_training",
            "migration",
            "offline_packaging",
            "edge_case_coverage",
        ):
            self.assertTrue((root / "docs" / (name + ".md")).is_file())
        train = (root / "docs/local_training.md").read_text(encoding="utf-8")
        for token in (
            "--dry-run",
            "train --config",
            "-100",
            "pad==EOS",
            "NOT RUN",
            "Ollama does not train LoRA",
            "local_files_only=True",
            "template_sha256",
        ):
            self.assertIn(token, train)
        operator = (root / "docs/operator_guide.md").read_text(encoding="utf-8")
        for command in (
            "predict",
            "freeze",
            "replay",
            "trajectories",
            "evaluate",
            "compare",
            "asr-evaluate",
            "validate",
            "config-check",
        ):
            self.assertIn("lifemate " + command, operator)

    def test_all_edge_cases_and_p0_gate_visible(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "docs/edge_case_coverage.md").read_text()
        for i in range(1, 55):
            self.assertEqual(text.count("| K" + str(i).zfill(2) + " |"), 1)
        self.assertIn("P0 pre-training gate", text)
        self.assertIn("SCORER", text)
        self.assertIn("NOT RUN", text)
