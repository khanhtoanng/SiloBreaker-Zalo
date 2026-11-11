# Verification checkpoint — 2026-11-10 (Asia/Saigon)

**Follow-up:** The user subsequently selected Ollama. It has now been installed,
the local 4B model has passed a synthetic JSON smoke, and the expanded suite has
**68 passing tests**. See [Ollama local evidence](ollama_local.md) for the model
pilot and setup. The original checkpoint below records what was available before
that follow-up; its "no model supplied" limitation has been resolved through Ollama.

**OBSERVED:** The implementation, tests and commands below were executed locally.
There is no Git repository metadata in the implementation root; no commit, push,
merge or deployment was performed. Existing AGENTS/SDLC files were preserved.
The user's request was treated as ordinary implementation work, not activation
of the staged SDLC harness.

## Executed checks

Commands use paths relative to `LifeMate/` unless a working directory is specified.

| Command/check | Exit / result |
|---|---|
| `python ../tools/audit_catalogs.py --data-root ../train+public_test/train+public_test --out docs/catalog_audit.json` | 0; train/public comparison written |
| `python ../tools/verify_sdk_contract.py --data-root ../train+public_test/train+public_test` | 0; original 8 synthetic SDK checks PASS |
| `python scripts/replay_gold.py --data-root ../train+public_test/train+public_test --out ../local_lifemate_artifacts/replay.json` | 0; 1,545/1,545 exact train replay |
| `python scripts/lifemate.py freeze --data-root ../train+public_test/train+public_test --out ../local_lifemate_artifacts/splits.json` | 0; 1,236/309 random fold; 1,056/489 banking-out fold |
| `python scripts/smoke_runtime.py --data-root ../train+public_test/train+public_test --out ../local_lifemate_artifacts/runtime_smoke.jsonl` | 0; one actual read through loop and real trace/hash |
| `python -m zaic_tools --split train --root .. --validate ../../../local_lifemate_artifacts/runtime_smoke.jsonl`, cwd external kit `train/` | 0; printed `1 lines checked, 0 schema errors` |
| `python scripts/check_evaluator.py --data-root ../train+public_test/train+public_test --replay ../local_lifemate_artifacts/replay.json --out ../local_lifemate_artifacts/evaluator_selfcheck.json` | 0; label-derived identity fixture PASS, explicitly not accuracy |
| `python scripts/lifemate.py trajectories --data-root ../train+public_test/train+public_test --split-config ../local_lifemate_artifacts/splits.json --out ../local_lifemate_artifacts/trajectories.jsonl` | 0; 5,086 rows generated through actual train replay |
| `python scripts/check_trajectories.py --data-root ../train+public_test/train+public_test --split-config ../local_lifemate_artifacts/splits.json --trajectories ../local_lifemate_artifacts/trajectories.jsonl --out ../local_lifemate_artifacts/trajectory_validation.json` | 0; all scenarios partitioned, consecutive observation prefixes, terminal DONE and target schemas PASS |
| `python -m unittest discover -s tests -q` | 0; **53 tests PASS**, no skips with this kit |
| `python -m compileall -q src scripts tests` | 0; syntax compilation PASS |
| `python scripts/lifemate.py --help` | 0; command surface loads without model packages |

After the initial gold replay, its existing report was annotated with the train
manifest fingerprint. The replay was not presented as a second independent run.
Trajectories were regenerated when the inference observation format and
source-verified response classifier changed, then revalidated.

Source scan confirms `get_state()` occurs only in authorized train replay and
synthetic tests. Production inference uses `get_tool_calls()` and
`get_state_hash()`. The adapter delegates environment loading exclusively to
the selected official `ToolEnv`. No implementation code parses state files.

## Local artifacts outside source

- `../local_lifemate_artifacts/replay.json`: per-scenario results/state/trace checks,
  replay hashes and manifest fingerprint; no raw state snapshots persisted.
- `../local_lifemate_artifacts/splits.json`: frozen fit/validation and app-out IDs.
- `../local_lifemate_artifacts/trajectories.jsonl`: authorized train-derived
  teacher-forced examples; no public/private training data.
- `../local_lifemate_artifacts/trajectory_validation.json`: aggregate structure check.
- `../local_lifemate_artifacts/runtime_smoke.jsonl` and diagnostics: one real read;
  a partial diagnostic sample, not a competition submission.
- `../local_lifemate_artifacts/evaluator_selfcheck.json`: proxy identity check only.

The source tree contains no copied SDK/catalog payload, raw data, model weights,
audio, labels or simulator state. `docs/catalog_audit.json` is the safe inventory
report requested by the handoff; it contains counts/names, not full schemas.

## NOT RUN / UNKNOWN

The 309-scenario model baseline, learned multi-goal and repetition behavior,
ASR, tokenizer/masking compatibility, SFT/LoRA, score ablations, target-GPU latency,
full inference submissions, Docker build/offline test and official scorer parity
remain unverified. No model path or remote compute details were supplied.
The optional backend cannot be called a tested model implementation until a
local-model smoke and holdout run pass. See [rules audit](rules_audit.md) and
[P0 coverage](p0_coverage.md) for the exact limits.


## LM-002 current software delivery (2026-11-10)

Historical evidence above retains its original meaning. Current layered software adds
strict Pydantic contracts, enforced references/goal occurrences, local audio code,
real lazy LoRA integration and atomic complete-run publication. See
[operator_guide.md](operator_guide.md), [local_training.md](local_training.md),
[edge_case_coverage.md](edge_case_coverage.md) and revision-bound
[implementation evidence](ai/work/LM-002-python-structure-training-guide/implementation.md)
for exact checks/exit codes and limits. Fixtures do not prove learned quality,
official scoring parity, successful training, target GPU or offline image compliance.
Ollama is inference only. Dry-run loads no model/tokenizer/session/training runtime.
Reference enforcement is active without the deprecated diagnostic flag.
