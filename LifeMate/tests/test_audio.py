import tempfile
import unittest
import wave
from pathlib import Path

from lifemate.adapters.whisper import inspect_wav, prepare_audio


def wav(path, rate=16000):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\0\0" * 160)


class AudioTests(unittest.TestCase):
    def test_history_latest_order_and_no_oracle_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name in ("old.wav", "latest.wav"):
                wav(root / name)

            class ASR:
                def __init__(self):
                    self.paths = []

                def transcribe(self, path, *, deadline):
                    self.paths.append(path.name)
                    return path.stem

            asr = ASR()
            sample = {
                "id": "x",
                "audio": "audio/latest.wav",
                "history": [
                    {"role": "user", "audio": "old.wav"},
                    {
                        "role": "assistant",
                        "text": "reply",
                        "tool_calls": [{"name": "old", "arguments": {}}],
                    },
                ],
            }
            result = prepare_audio(sample, root, asr, deadline=float("inf"))
            self.assertEqual(asr.paths, ["old.wav", "latest.wav"])
            self.assertEqual(result["history"][0]["text"], "old")
            self.assertEqual(result["text"], "latest")
            self.assertEqual(result["history"][1], sample["history"][1])
            self.assertNotIn("text", sample)

    def test_corrupt_missing_and_truncated(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.wav"
            p.write_bytes(b"bad")
            with self.assertRaises(ValueError):
                inspect_wav(p)
            wav(p)
            p.write_bytes(p.read_bytes()[:-3])
            with self.assertRaises(ValueError):
                inspect_wav(p)

    def test_asr_failure_and_late_response(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            wav(root / "a.wav")

            class Bad:
                def transcribe(self, *a, **k):
                    raise RuntimeError("ASR failed")

            with self.assertRaises(RuntimeError):
                prepare_audio({"audio": "a.wav"}, root, Bad(), deadline=float("inf"))
            with self.assertRaises(TimeoutError):
                prepare_audio({"audio": "a.wav"}, root, Bad(), deadline=0)

    def test_rate_duration_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.wav"
            wav(p, 8000)
            self.assertEqual(inspect_wav(p)["sample_rate"], 8000)
            self.assertAlmostEqual(inspect_wav(p)["duration_seconds"], 0.02)

    def test_short_form_duration_boundary(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)

            def create(name, frames):
                with wave.open(str(root / name), "wb") as stream:
                    stream.setnchannels(1)
                    stream.setsampwidth(2)
                    stream.setframerate(8000)
                    stream.writeframes(b"\0\0" * frames)

            create("limit.wav", 240000)
            create("long.wav", 240001)

            class ASR:
                def __init__(self):
                    self.calls = 0

                def transcribe(self, *a, **kw):
                    self.calls += 1
                    return "text"

            asr = ASR()
            self.assertEqual(
                prepare_audio({"audio": "limit.wav"}, root, asr, deadline=float("inf"))["text"],
                "text",
            )
            with self.assertRaisesRegex(ValueError, "at most 30"):
                prepare_audio({"audio": "long.wav"}, root, asr, deadline=float("inf"))
            self.assertEqual(asr.calls, 1)
