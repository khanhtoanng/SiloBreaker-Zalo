"""Local Whisper-compatible ASR with explicit PCM validation and resampling."""

from __future__ import annotations

import copy
import time
import wave
from pathlib import Path

from ..artifacts import audio_path


def inspect_wav(path):
    try:
        with wave.open(str(path), "rb") as stream:
            info = {
                "sample_rate": stream.getframerate(),
                "channels": stream.getnchannels(),
                "frames": stream.getnframes(),
                "sample_width": stream.getsampwidth(),
            }
            if (
                stream.getcomptype() != "NONE"
                or info["channels"] not in (1, 2)
                or info["sample_width"] not in (1, 2, 3, 4)
                or info["sample_rate"] < 8000
                or info["frames"] <= 0
            ):
                raise ValueError("Unsupported/empty PCM WAV")
            expected = info["frames"] * info["channels"] * info["sample_width"]
            if len(stream.readframes(info["frames"])) != expected:
                raise ValueError("Truncated WAV")
            return {**info, "duration_seconds": info["frames"] / info["sample_rate"]}
    except (wave.Error, EOFError, OSError) as exc:
        raise ValueError("Unreadable PCM WAV") from exc


def prepare_audio(sample, audio_root, asr, *, deadline, clock=time):
    sample = copy.deepcopy(sample)
    timings = []

    def transcribe(value):
        if clock.monotonic() >= deadline:
            raise TimeoutError("ASR deadline reached")
        parts = Path(value).parts
        relative = Path(*parts[1:]) if parts and parts[0] == "audio" else Path(value)
        path = audio_path(audio_root, relative)
        info = inspect_wav(path)
        if info["duration_seconds"] > 30.0:
            raise ValueError(
                "ASR supports at most 30 seconds per WAV; long-form processing is not configured"
            )
        started = clock.monotonic()
        text = asr.transcribe(path, deadline=deadline)
        if clock.monotonic() >= deadline:
            raise TimeoutError("Late ASR response")
        if not isinstance(text, str):
            raise ValueError("ASR returned a non-text transcript")
        timings.append(
            {
                "audio": str(relative),
                "elapsed_seconds": float(clock.monotonic() - started),
                "raw_text": text,
                "sample_rate": info["sample_rate"],
                "duration_seconds": info["duration_seconds"],
            }
        )
        return text

    for turn in sample.get("history", []):
        if turn["role"] == "user" and turn.get("audio"):
            turn["text"] = transcribe(turn["audio"])
    if not sample.get("audio"):
        raise ValueError("Latest user WAV required")
    sample["text"] = transcribe(sample["audio"])
    sample["_asr_diagnostics"] = timings
    return sample


class WhisperAsr:
    def __init__(self, model_path):
        path = Path(model_path).resolve()
        if not path.is_dir():
            raise FileNotFoundError("Local ASR assets missing")
        import os

        os.environ.update(
            HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1"
        )
        try:
            import torch  # type: ignore[import-not-found,import-untyped]
            from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor  # type: ignore[import-not-found,import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "Install optional asr dependencies on the reviewed runtime platform"
            ) from exc
        self.torch = torch
        self.processor = AutoProcessor.from_pretrained(
            path, local_files_only=True, trust_remote_code=False
        )
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            path,
            local_files_only=True,
            trust_remote_code=False,
            device_map="auto",
            dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        ).eval()

    def transcribe(self, path: Path | str, *, deadline: float) -> str:
        from math import gcd

        import soundfile as sf  # type: ignore[import-not-found,import-untyped]
        from scipy.signal import resample_poly  # type: ignore[import-not-found,import-untyped]
        from transformers import StoppingCriteria, StoppingCriteriaList  # type: ignore[import-not-found,import-untyped]

        class Deadline(StoppingCriteria):
            def __call__(self, input_ids, scores, **kwargs):
                return time.monotonic() >= deadline

        info = inspect_wav(path)
        if info["duration_seconds"] > 30.0:
            raise ValueError("ASR supports at most 30 seconds per WAV")
        audio, rate = sf.read(path, dtype="float32", always_2d=True)
        audio = audio.mean(axis=1)
        target = int(self.processor.feature_extractor.sampling_rate)
        divisor = gcd(rate, target)
        if rate != target:
            audio = resample_poly(audio, target // divisor, rate // divisor)
        if time.monotonic() >= deadline:
            raise TimeoutError("ASR deadline before generation")
        inputs = self.processor(
            audio, sampling_rate=target, return_attention_mask=True, return_tensors="pt"
        ).to(device=self.model.device, dtype=self.model.dtype)
        with self.torch.inference_mode():
            output = self.model.generate(
                **inputs,
                language="vi",
                task="transcribe",
                do_sample=False,
                num_beams=1,
                max_length=self.model.config.max_target_positions,
                stopping_criteria=StoppingCriteriaList([Deadline()]),
            )
        if time.monotonic() >= deadline:
            raise TimeoutError("ASR response exceeded deadline")
        return self.processor.batch_decode(output, skip_special_tokens=True)[0].strip()
