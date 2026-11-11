import unittest
from pathlib import Path


class PackagingTests(unittest.TestCase):
    def test_offline_entrypoint_and_context(self):
        root = Path(__file__).resolve().parents[1]
        docker = (root / "Dockerfile").read_text()
        entry = (root / "predict.sh").read_bytes()
        ignore = (root / ".dockerignore").read_text()
        manifest = (root / "MANIFEST.in").read_text()
        self.assertIn("--no-index", docker)
        self.assertIn('"setuptools>=68" "wheel>=0.45,<1"', docker)
        self.assertIn("--no-build-isolation", docker)
        self.assertIn(".[model,asr]", docker)
        self.assertIn("exec python -m lifemate predict", entry.decode())
        self.assertNotIn(b"\r", entry)
        self.assertTrue(ignore.startswith("*\n"))
        self.assertIn("prune docs/ai", manifest)
        self.assertNotIn("COPY models", docker)
