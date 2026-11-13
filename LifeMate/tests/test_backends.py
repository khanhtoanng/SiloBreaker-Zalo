import sys
import tempfile
import unittest
from pathlib import Path

from test_ollama import FixtureClient

from lifemate.adapters.llama_cpp import LlamaCppPolicy
from lifemate.adapters.transformers import LocalPolicy
from lifemate.adapters.whisper import WhisperAsr
from lifemate.ollama_policy import OllamaPolicy
from lifemate.runtime.validation import Rejected


class BackendTests(unittest.TestCase):
    def test_truncated_binding_is_a_rejected_proposal(self):
        from unittest.mock import Mock

        policy = LlamaCppPolicy.__new__(LlamaCppPolicy)
        policy.next_action = Mock(return_value='{"occurrence_id":')
        with self.assertRaises(Rejected):
            policy.bind({}, deadline=1)

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
            def to(self, **kw):
                seen["input_placement"] = kw
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
            dtype = "float32"
            config = SimpleNamespace(max_target_positions=448)

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
            "torch": SimpleNamespace(
                inference_mode=nullcontext,
                cuda=SimpleNamespace(is_available=lambda: False),
                float32="float32",
            ),
            "transformers": SimpleNamespace(
                AutoProcessor=Processor,
                AutoModelForSpeechSeq2Seq=Model,
                StoppingCriteria=object,
                StoppingCriteriaList=list,
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
        self.assertTrue(seen["processor_call"]["return_attention_mask"])
        self.assertEqual(seen["input_placement"], {"device": "cpu", "dtype": "float32"})
        self.assertEqual(seen["generate"]["max_length"], 448)
        self.assertNotIn("max_new_tokens", seen["generate"])
        for key in ("processor_load", "model_load"):
            self.assertTrue(seen[key]["local_files_only"])
            self.assertFalse(seen[key]["trust_remote_code"])
