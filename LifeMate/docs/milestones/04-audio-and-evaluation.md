# 04. Add speech and measure the baseline

[Roadmap](README.md) · [Previous milestone](03-text-agent.md) · [Next milestone](05-optimization-and-training.md)

The text baseline isolates the policy. Add local speech recognition and run the same scenarios again to see what changes when the input comes from Vietnamese audio.

## 1. Put the speech adapter before the policy

[`adapters/whisper.py`](../../src/lifemate/adapters/whisper.py) transcribes the supplied historical user turns and latest WAV, then sends their text through the same agent loop. It uses a local Whisper-compatible processor and model, with mono conversion and resampling. The current reader accepts mono or stereo PCM WAVs at 8 kHz or higher and at most 30 seconds of audio per file. The competition's separate 30-second processing limit applies to the whole sample, including its history. [LifeMate portal, Rule](https://challenge.zalo.ai/portal/lifemate)

The current WAV inspector accepted all 1,933 audio references in the 634 public scenarios, counting latest and historical user audio. The longest file was 20.24 seconds. This check establishes input compatibility for the supplied public WAVs. Speech quality and processing time require a model run.

Follow sections 2–6 of the [operator guide](../operator_guide.md) for model and config setup. Use [inference.audio.json](../../configs/inference.audio.json) as the template. For the paired train experiment set `split=train`, `input_mode=audio`, `selection=validation`, and use the same `fold` and `split_config` as the oracle run. Change `out` and supply `asr_path`. Keep the policy, tokenizer and decision limits fixed across the pair. Use a short pilot for setup and a full frozen validation run for comparison.

## 2. Compare the runs

1. Copy the [evaluation template](../../configs/evaluation.json) for each run. Use the same frozen IDs and replay reference, and give each report its own `predictions` and `out` paths. If evaluating pilot outputs, match the prediction and evaluation `limit` values.
2. Run the commands below after creating both evaluation configs. Inspect state match, tool-call F1, first versus later actions, and cases where the audio run added or missed a call. The reports pair scenarios by ID and check the dataset, fold and replay identities. [metrics/reports.py](../../src/lifemate/metrics/reports.py)
3. Compare transcript pairs with `asr-evaluate` when you have assembled the input artifacts. It measures word and character error rates and changes in fields such as amounts or times. Use the corresponding action results to decide which transcription errors matter. [metrics/asr.py](../../src/lifemate/metrics/asr.py)

```powershell
& $Python -m lifemate evaluate --config "$Work\configs\evaluation-oracle.json"
& $Python -m lifemate evaluate --config "$Work\configs\evaluation-audio.json"
& $Python -m lifemate compare --baseline "$Work\reports\oracle.json" --candidate "$Work\reports\audio.json" --out "$Work\reports\oracle-vs-audio.json"
```

Zalo's Evaluation tab describes an empty-gold special case, a final-state gate for nonempty gold, and one-to-one tool-call matching. Argument matching uses exact values for non-fuzzy fields and token F1 above 0.6 for fuzzy text after lowercasing and NFC normalization. Submitted calls execute in order, even though matching ignores order. The local report is still labeled **PROXY**. The published scoring description is available, while exact implementation parity remains unverified. [Local scoring assumptions](../scorer_parity.md) · [LifeMate portal, Evaluation](https://challenge.zalo.ai/portal/lifemate)

## 3. Produce a full public result

Run a separate audio config with `split=public_test`, `selection=all`, `input_mode=audio`, and a fresh `out` ending in `submission.jsonl` in a dedicated run directory. Leave `limit` unset. The v3.2.0 public manifest has 634 IDs. A short pilot can produce a valid local file for its selected rows, so validate the full candidate against the full public manifest before upload. Follow the two checks in [milestone 06](06-zalo-submission.md).

Treat `.run.json` as the place to verify completion and selected IDs. Read `.diagnostics.json` for `TIMEOUT`, `CONTEXT_OVERFLOW`, unfinished goals and timing. A timeout can still leave a real trace and hash. A fatal sample error prevents this version from publishing the final file. Both cases need attention before release.

**Ready to move on** when you have paired train reports and a full public audio run with real traces and hashes. Record model startup time, per-sample p50, p95 and maximum latency, and the failures on multi-turn and multi-call inputs. Use a target-class GPU to establish competition timing.
