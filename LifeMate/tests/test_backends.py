import sys
import tempfile
import unittest
from pathlib import Path

from test_ollama import FixtureClient

from lifemate.adapters.transformers import LocalPolicy
from lifemate.adapters.whisper import WhisperAsr
from lifemate.ollama_policy import OllamaPolicy


class BackendTests(unittest.TestCase):
    def test_missing_local_assets_no_download_or_fallback(self):
        for adapter in (LocalPolicy, WhisperAsr):
            with self.assertRaises(FileNotFoundError):
                adapter(Path(tempfile.gettempdir()) / "nonexistent-lifemate-model-812987")

    def test_planner_uses_same_local_json_generation(self):
        client = FixtureClient()
        client.response["message"]["content"] = '{"goals":[]}'
        policy = OllamaPolicy("fixture:4b", client=client)
        import time

        self.assertEqual(
            policy.plan({"latest_user_text": "hello"}, deadline=time.monotonic() + 5).goals, []
        )
        self.assertEqual(client.requests[-1][0], "/api/chat")

    def test_imports_do_not_load_heavy_libraries(self):
        import subprocess

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import lifemate.cli,lifemate.learning.trainer,lifemate.adapters.whisper,lifemate.adapters.transformers;import sys;assert not {'torch','transformers','trl','peft','soundfile','scipy'} & sys.modules.keys()",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_actual_whisper_boundary_local_load_mono_resample(self):
        from contextlib import nullcontext
        from types import SimpleNamespace
        from unittest.mock import patch

        from test_audio import wav

        seen = {}

        class Inputs(dict):
            def to(self, device):
                seen["device"] = device
                return self

        class Processor:
            feature_extractor = SimpleNamespace(sampling_rate=16000)

            @staticmethod
            def from_pretrained(path, **kw):
                seen["processor_load"] = kw
                return Processor()

            def __call__(self, audio, **kw):
                seen["processor_call"] = kw
                return Inputs(values=audio)

            def batch_decode(self, output, **kw):
                return ["xin chao"]

        class Model:
            device = "cpu"

            @staticmethod
            def from_pretrained(path, **kw):
                seen["model_load"] = kw
                return Model()

            def eval(self):
                return self

            def generate(self, **kw):
                seen["generate"] = kw
                return [[1]]

        class Signal:
            def mean(self, axis):
                seen["mono_axis"] = axis
                return [0.1, 0.2]

        def resample(audio, up, down):
            seen["resample"] = (up, down)
            return audio

        modules = {
            "torch": SimpleNamespace(inference_mode=lambda: nullcontext()),
            "transformers": SimpleNamespace(
                AutoProcessor=Processor, AutoModelForSpeechSeq2Seq=Model
            ),
            "soundfile": SimpleNamespace(read=lambda *a, **kw: (Signal(), 8000)),
            "scipy": SimpleNamespace(),
            "scipy.signal": SimpleNamespace(resample_poly=resample),
        }
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            wav(path / "a.wav", 8000)
            with patch.dict("sys.modules", modules):
                asr = WhisperAsr(path)
                text = asr.transcribe(path / "a.wav", deadline=float("inf"))
        self.assertEqual(text, "xin chao")
        self.assertEqual(seen["resample"], (2, 1))
        self.assertEqual(seen["mono_axis"], 1)
        self.assertEqual(seen["processor_call"]["sampling_rate"], 16000)
        for key in ("processor_load", "model_load"):
            self.assertTrue(seen[key]["local_files_only"])
            self.assertFalse(seen[key]["trust_remote_code"])
