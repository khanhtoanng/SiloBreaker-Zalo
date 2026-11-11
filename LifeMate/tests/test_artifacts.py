import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lifemate.artifacts import audio_path, external_output, save_json, write_jsonl
from lifemate.provenance import source_identity


class ArtifactTests(unittest.TestCase):
    def test_output_protection_normalization_and_collisions(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root / "source"
            source.mkdir()
            model = root / "model"
            model.mkdir()
            for target in (source / "x", root / "z/../source/x", model / "new", model):
                with self.subTest(target=target), self.assertRaises(ValueError):
                    external_output(target, inputs=[model], source_root=source)
            with self.assertRaises(ValueError):
                external_output(root / "run/a", outputs=[root / "run"], source_root=source)

    def test_atomic_no_clobber_and_failure_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "report.json"
            save_json(p, {"v": 1})
            with self.assertRaises(FileExistsError):
                save_json(p, {"v": 2})
            self.assertIn("1", p.read_text())
            with (
                patch("lifemate.artifacts.os.replace", side_effect=OSError("fixture")),
                self.assertRaises(OSError),
            ):
                save_json(p, {"v": 3}, replace=True)
            self.assertEqual(sorted(x.name for x in Path(d).iterdir()), ["report.json"])

    def test_nonfinite_never_published(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x"
            with self.assertRaises(ValueError):
                write_jsonl(p, [{"n": float("nan")}])
            self.assertFalse(p.exists())

    def test_nested_source_changes_identity(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "src/lifemate/runtime/nested.py"
            p.parent.mkdir(parents=True)
            p.write_text("x=1")
            before = source_identity(d)
            p.write_text("x=2")
            self.assertNotEqual(before, source_identity(d))

    def test_audio_escape_and_environment(self):
        with tempfile.TemporaryDirectory() as d:
            for value in ("../outside.wav", "environment/s.wav", "states/s.wav"):
                with self.assertRaises(ValueError):
                    audio_path(d, value)

    def test_symlink_target_protected(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            source = base / "source"
            source.mkdir()
            link = base / "alias"
            try:
                link.symlink_to(source, target_is_directory=True)
            except OSError as exc:
                self.skipTest("OS symlink permission unavailable: " + type(exc).__name__)
            with self.assertRaises(ValueError):
                external_output(link / "out", source_root=source)

    def test_windows_junction_escape_actual(self):
        import os
        import subprocess

        if os.name != "nt":
            self.skipTest("Windows junction contract")
        with tempfile.TemporaryDirectory() as d:
            base = Path(d).resolve()
            source = base / "source"
            source.mkdir()
            alias = base / "alias"
            self.assertTrue(source.is_relative_to(base))
            self.assertTrue(alias.is_relative_to(base))
            result = subprocess.run(
                ["cmd.exe", "/c", "mklink", "/J", str(alias), str(source)],
                capture_output=True,
                text=True,
            )
            if result.returncode:
                self.skipTest("Junction creation unavailable: " + str(result.returncode))
            try:
                self.assertEqual(alias.resolve(), source)
                with self.assertRaises(ValueError):
                    external_output(alias / "escaped.json", source_root=source)
            finally:
                os.rmdir(alias)  # Remove only the junction itself, never its resolved target.
            self.assertTrue(source.is_dir())

    def test_split_environment_audio_root_forbidden_before_read(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "environment state"):
                audio_path(Path(d) / "train_environment", "x.wav")

    def test_installed_wheel_source_identity_and_output_protection(self):
        with tempfile.TemporaryDirectory() as d:
            package = Path(d) / "site-packages/lifemate"
            nested = package / "runtime/loop.py"
            nested.parent.mkdir(parents=True)
            nested.write_text("value=1")
            before = source_identity(package_root=package)
            nested.write_text("value=2")
            self.assertNotEqual(before, source_identity(package_root=package))
            with (
                patch("lifemate.artifacts.PACKAGE_ROOT", package),
                patch("lifemate.artifacts.SOURCE_ROOT", package),
            ):
                with self.assertRaises(ValueError):
                    external_output(package / "generated/result.json")
