# Compatibility and migration

Legacy modules remain explicit facades: agent_loop, context_builder, data_loader,
evaluation, ollama_policy, policy, references, replay, submission, toolenv_adapter,
trajectory_builder and validator. Dictionary helpers still return dictionaries.
RunConfig is Pydantic with observed keyword names/default meanings and extra finite
planning/generation/context budgets. Positional compatibility beyond observed
consumers is not promised. CLI keeps freeze/predict/evaluate/trajectories/validate,
lifemate and scripts/lifemate.py, adding python -m lifemate and new commands/wrappers.
Legacy no-mode predict remains frozen train oracle with local Ollama default or
Transformers when model-path selects it; --limit stays a manifest-order prefix.

Required changes: provenance is enforced even without deprecated
--require-reference-provenance. Known collection/type/parent mismatch blocks writes.
Strict decisions reject extra/duplicate/nonfinite fields; SDK validation remains
final authority. Internal planning/occurrence binding precedes mutations without
adding fields to CALL/ASK/DONE or official submissions. Completed/uncertain writes
cannot repeat, explicit separate occurrences can, and no-op recovery requires
cause-linked actual evidence. Outputs refuse source/input/model collisions and
existing destinations. Final submissions require full completion; partial sidecars
carry truthful status and there is no implicit resume. Public/private inference is
audio with explicit all selection; oracle stays train-only. WAVs above 30 seconds
fail explicitly. Nested source changes affect recursive provenance, unlike old
historical top-level-only hashes. Only supplied CLI flags override JSON config.

No automatic data/model migration/regeneration occurs. Prior audit/experiment
claims remain historical. Re-run software and later model/data gates before
adoption. Manual rollback uses immutable before bytes only after current path identity
matches reviewed after; preserve later owner changes. This guide does not authorize
destructive rollback or replace final owner acceptance.
