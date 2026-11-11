# 05. Optimize with evidence

[Roadmap](README.md) · [Previous milestone](04-audio-and-evaluation.md) · [Next milestone](06-zalo-submission.md)

Use the paired results to choose one improvement at a time. Freeze the audio baseline and preserve a runnable release candidate while testing changes.

## 1. Decide what to improve

| Symptom in the baseline | First change to test | Evidence to compare |
| --- | --- | --- |
| Both oracle and audio use wrong tools or stop with goals pending | Improve the planner or action policy. Check [goals.py](../../src/lifemate/runtime/goals.py) and [loop.py](../../src/lifemate/runtime/loop.py) for premature DONE and mishandled dependencies | Whole-trajectory match, goal completion and unnecessary calls |
| Both modes choose the right tool but use unsupported IDs or arguments | Check [references.py](../../src/lifemate/runtime/references.py), [validation.py](../../src/lifemate/runtime/validation.py), and actual tool observations | Invented references, rejected arguments, no-op writes and valid actions mistakenly blocked |
| Oracle handles a case that audio misses | Inspect the transcript for names, amounts, times and negation. Test one change to speech recognition or normalization | Critical-field changes, downstream state/call scores and ASR latency |
| Correct decisions arrive late | Measure latest and history ASR, planning and generation, SDK time and output overhead. Try a smaller or faster eligible runtime and recheck hard cases | p95/max latency, timeout count and paired score |

Use [edge-case coverage](../edge_case_coverage.md) as a test index. Prioritize repeat writes, false success on no-ops, empty traces, ASK after partial success, and scenarios from the held-out app. Record before and after runs on the same frozen IDs. Change one variable so you can explain the result.

## 2. Add LoRA if the policy is the measured bottleneck

1. Generate `trajectories` from the train kit and frozen fold in milestone 02. [learning/trajectories.py](../../src/lifemate/learning/trajectories.py) replays previous calls to build each next-decision example. A read then a write becomes a read target, a write target with the actual read result in context, and a final DONE target. All rows from that scenario inherit the same partition.
2. Supply a local Transformers-format causal model and its matching tokenizer. Use [local fine-tuning](../local_training.md) to create the training config and asset fingerprints. Run `train --dry-run` to validate preparation, then run the training command on suitable compute. The ordinary PEFT/TRL LoRA path adapts the action policy. Whisper ASR has its own checkpoint and evaluation.
3. Read [learning/serialization.py](../../src/lifemate/learning/serialization.py) to see how the current action and EOS receive supervision. Prompt, history, tool observations, earlier actions and padding receive the ignore label `-100`. Check that the chat template preserves the expected prefix and that examples fit the configured sequence length.
4. Confirm the training run reports `COMPLETE` with an adapter and tokenizer. Load them with the original base in [the Transformers backend](../../src/lifemate/adapters/transformers.py). Compare the base and adapter first on the same oracle holdout, then through audio under the same inference budget. Keep the held-out app check separate from the grouped experiment.

```powershell
& $Python -m lifemate trajectories --data-root $Kit --split-config "$Work\data\folds-run001.json" --out "$Work\data\trajectories-run001.jsonl"
& $TrainPython -m lifemate train --config "$Work\configs\training.json" --dry-run
& $TrainPython -m lifemate train --config "$Work\configs\training.json"
```

The `trajectories` command ran successfully on 11 November 2026 and reproduced the [experiment ledger's](../experiment_log.md) 5,086 prepared rows. Training and adapter quality need fresh evidence. Keep the trainer's output path distinct for each run. If the submission deadline arrives before a candidate clears the comparison, freeze the working eligible baseline and record the exact preparation or training history in the submission README.

**Ready to promote a change** when a paired report shows better action results on held-out scenarios, important safety cases still pass, and the complete audio run stays within the competition timing and model limits. A lower training loss alone cannot establish this.
