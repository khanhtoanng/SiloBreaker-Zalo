# 02. Build the data and simulator foundation

[Roadmap](README.md) · [Previous milestone](01-idea-and-contract.md) · [Next milestone](03-text-agent.md)

First establish that LifeMate can load the right split, use its tool catalog and replay the organizer's labeled training examples. These checks give later model runs a stable reference.

## 1. Locate the kit and the active loader

In this workspace the inner `../train+public_test/train+public_test/` folder contains `train/` and `public_test/`. [data/kit.py](../../src/lifemate/data/kit.py) also accepts the outer folder when it finds a single valid kit wrapper. `__MACOSX/` is archive metadata. `private_test/` is a separately released split.

| Asset | How to use it |
| --- | --- |
| `<split>.jsonl` | Scenario IDs, audio paths, context and history. Train additionally provides transcripts and labels for preparation and evaluation |
| `<split>_tools_catalog.json` | Tool names, argument schemas, read/write/meta kinds and extensions such as `x-ref` |
| `<split>/zaic_tools/` | External simulator package loaded by [adapters/sdk.py](../../src/lifemate/adapters/sdk.py) for the selected split |
| `audio/` | Latest WAV plus WAVs for earlier user turns when present |
| `<split>_environment/` | Organizer-owned inputs accessed through the SDK. Keep them in place and avoid opening, copying or parsing their contents in application code |

The v3.2.0 kit has 1,545 train scenarios and 147 train tools, and 634 public scenarios and 122 public tools. The current loader returned those counts. The historical [kit audit](../rules_audit.md) shows differences in tools and hash canonicalization across splits. The SDK therefore supplies the final hash and tool log for its own split.

## 2. Run the model-free setup

From `LifeMate/`, set `$Python`, `$Kit` and `$Work` using sections 1–2 of the [operator guide](../operator_guide.md). These commands use the core dependencies. Pick fresh filenames under `$Work\data` because generated files refuse overwrite.

```powershell
& $Python -m lifemate --help
& $Python -m lifemate audit --data-root $Kit --out "$Work\data\catalog-m02.json"
& $Python -m lifemate freeze --data-root $Kit --out "$Work\data\folds-run001.json" --seed 20261109 --heldout-app banking
& $Python -m lifemate replay --data-root $Kit --out "$Work\data\replay-run001.json"
```

1. **Audit.** Check tool counts and availability in each split. Review [data/kit.py](../../src/lifemate/data/kit.py) for the input projection and catalog validation.
2. **Freeze.** Save fit and validation IDs before generating training examples. The grouped fold separates whole scenarios. The separate `leave-app-out` fold probes generalization to the held-out app. [data/splits.py](../../src/lifemate/data/splits.py)
3. **Replay.** Execute the train gold call sequence and check its observations and state effects through the SDK. Save reference hashes and the manifest fingerprint for later comparisons. This workflow intentionally uses train labels. Inference receives a projection that excludes them. [data/replay.py](../../src/lifemate/data/replay.py)

The commands above ran successfully on 11 November 2026. Replay passed all 1,545 scenarios with 3,541 executed calls, including 217 scenarios with ASK. The [experiment ledger](../experiment_log.md) records the earlier grouped split of 1,236 fit and 309 validation scenarios. Match the manifest fingerprint and fold before reusing the older `../local_lifemate_artifacts/splits.json` and `replay.json`.

**Ready to move on** when your replay report has zero failed scenarios, and the same frozen scenario IDs can be used by prediction, evaluation and any future training. If replay disagrees with a label, inspect the failed replay and SDK version before interpreting a policy score.
