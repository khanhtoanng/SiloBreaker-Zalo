# Architecture and implementation plan — LifeMate application

WORK_ID: LM-002-python-structure-training-guide  
FLOW: FULL  
STAGE: ARCHITECT  
REVISION: r1  
DATE: 2026-11-10 (Asia/Saigon)  
STATUS: READY_FOR_REVIEW  
CLARIFICATION_CHECK: NO_MATERIAL_GAPS — DEC-01/02/03 and approved full-app scope applied  
RISK_TIER: MEDIUM  
APPLICATION_BASELINE: NOT ESTABLISHED  
APPLICATION_EDIT_GRANT: NONE

## 1. Approved basis and evidence

This is one selected implementation plan for the full offline Vietnamese
voice-to-action application, covering C01–C15 and AC-01–AC-36. It does not narrow
delivery to a refactor or trainer. Actual setup and model/runtime evidence remain
deferred. Approval of this document does not authorize application edits.

The Architect independently read [source r3](source.md), [Intent r2](intent.md),
[Spec r1](spec.md), [the ledger](progress.md), the effective project rules and role
procedure. SHA-256 identities recomputed with `Get-FileHash -Algorithm SHA256`:

| Input | SHA-256 | Actual human receipt supplied by coordinator |
|---|---|---|
| source.md r3 | ab1e5a069dc9c2379226c0e475f35b9d1992da9416175ec2d2a15e042c5f0205 | DEC-01/02/03 source evidence |
| intent.md r2 | d7c8e8ada44f76feaaa074b8f19c575e71610d618038b7ac0327362ba6e6e5a6 | AP-01: `APPROVE intent r2` |
| spec.md r1 | 84f6a227878423ec886f3575b523f6b3e7aa5b7d0e8e1ba7d1da1aa4c9ad12a0 | AP-02: `APPROVE spec r1` |

DEC-01 permits generic role-guided agents with the existing gates and a fresh
independent Reviewer; this worker is not a named native agent. DEC-02 includes
real training code and a complete later-run guide. DEC-03 includes the original
full app while deferring model downloads, training environment setup, model/ASR
execution, training, forward/loss jobs, benchmarks and runtime certification.
Pydantic and clear Python structure are direct user requirements. Local Ollama
policy inference is already selected; it does not perform LoRA training.

OBSERVED source context, read without executing application workflows:

- [pyproject.toml](../../../../pyproject.toml) uses setuptools, Python >=3.10,
  no core dependencies, optional model/ollama extras and `lifemate.cli:main`.
- Existing [CLI](../../../../src/lifemate/cli.py) handles preparation, train-only
  prediction/evaluation and persistence together. `source_sha256` only covers
  top-level `*.py`; moving code requires recursive provenance coverage.
- Existing loader/registry and SDK adapter select external split assets and import
  SDKs under distinct namespaces. Existing loop obtains actual SDK trace/hash,
  uses one environment, prevalidates and bounds repairs. Preserve these strengths.
- Existing context/references/validator, replay, trajectories, submission and proxy
  evaluator provide reusable behavior. The reference flag currently warns by
  default; the approved spec requires blocking fabricated references and known
  semantic mismatches in the completed product.
- Existing `policy.py` and `ollama_policy.py` are optional local policy adapters.
  ASR, numeric/time helpers, evidence-backed goal/occurrence tracking and LoRA
  trainer are absent. There is no Dockerfile/entrypoint in the inventory.
- Existing `tests/test_runtime.py`, `test_ollama.py`, `test_sdk_contract.py` use
  unittest and synthetic fixtures. The SDK tests instantiate `sdk.Session` from
  self-generated dictionaries. They do not require reading real initial states.
- [README](../../../../README.md), [rules audit](../../../../docs/rules_audit.md),
  [P0 coverage](../../../../docs/p0_coverage.md) and other audit documents describe
  historical checks, not new evidence for this work. Train/public hashes differ;
  the actual selected SDK remains authority. No new tests were run here.
- No Git metadata is available, as independently checked by the coordinator;
  `.gitignore` excludes `.venv`, build/cache, data/model paths and most JSONL.
  Ignore rules do not define the review boundary.

The complete original [parent intent](../../../../../intent.md) and
[parent spec](../../../../../spec.md), [kit findings](../../../../../KIT_VERIFIED_FINDINGS.md),
[edge matrix](../../../../../SCORING_EDGE_CASES.md), parent README and implementation
backlog were read. Old small-bundle availability statements are superseded where
the current local audits supply stronger evidence. Scorer/resource/mount/release
contracts remain UNKNOWN. No protected raw state files were read, no SDK/data were
copied, and no application/model/setup job ran during Architecture.

## 2. Selected structure and dependency direction

Use a small synchronous Python application with explicit injectable boundaries.
Keep argparse, unittest, pathlib, JSON and existing algorithms. Add Pydantic v2 for
application contracts. Do not add an orchestration framework, service database,
replacement simulator, remote vendor or UI. JSON configuration avoids a new YAML
runtime dependency. The supported Python floor stays 3.10; timezone support uses
stdlib `zoneinfo` with `tzdata` for Windows.

All paths below are relative to the implementation root
`C:/Users/nktoan/Downloads/LifeMate_2026_Kit_Verified_Coding_Handoff/LifeMate`.
The following is the complete planned source layout in addition to retained
compatibility facades:

```text
src/lifemate/
  __init__.py  __main__.py  cli.py  workflows.py
  contracts.py  config.py  artifacts.py  provenance.py  py.typed
  data/        __init__.py  kit.py  splits.py  replay.py
  runtime/     __init__.py  context.py  normalize.py  references.py
               validation.py  outcomes.py  goals.py  loop.py
  adapters/    __init__.py  protocols.py  sdk.py  ollama.py
               transformers.py  whisper.py
  learning/    __init__.py  trajectories.py  serialization.py  trainer.py
  metrics/     __init__.py  proxy.py  reports.py  asr.py
```

Contracts/config contain no SDK/model imports. Data and runtime depend on
contracts and protocols; adapters implement protocols. Metrics and learning reuse
the same context/action serialization. `workflows.py` wires explicit factories,
selections and atomic writers; `cli.py` only parses/validates arguments and calls
workflows. Optional heavy libraries are imported inside the requested adapter's
runtime factory, never at package import/help/config-validation time. Avoid
general plugin discovery and mutable process-global application state.

Retain these existing modules as thin typed compatibility facades, with explicit
exports and argument conversion, rather than deleting files:
`agent_loop.py`, `context_builder.py`, `data_loader.py`, `evaluation.py`,
`ollama_policy.py`, `policy.py`, `references.py`, `replay.py`, `submission.py`,
`toolenv_adapter.py`, `trajectory_builder.py`, `validator.py`. `RunConfig`, `infer`,
`LocalPolicy`, `OllamaPolicy`, existing loader/validation/evaluation helpers and
`external_output`/`save_json` retain documented invocation meanings. Existing
dictionary-facing helpers return dictionaries where callers expect them; typed
models validate at the internal boundary. `RunConfig` becomes a validated model
with existing keyword names/defaults. No positional compatibility promise beyond
observed/documented consumers is added. New behavior required by the spec is
documented in the migration guide.

## 3. Validated contracts and file ownership

Use strict fields and `extra='forbid'` for command configurations, decisions,
submissions, folds and project-owned records. Use discriminated CALL/ASK/DONE
models with literal kinds and exact allowed fields. Parse JSON first using a
duplicate-key detector and rejection of NaN/Infinity, then Pydantic validation;
Pydantic alone does not detect duplicate keys. Primitive tool arguments stay
strict JSON values: bool/string/float never become integer amounts by coercion.
Normalize CLI/path strings explicitly at config loading, not via blanket lax
coercion of user arguments. Errors name command, file/line and field path.

Models in `contracts.py` cover `InferenceSample`, `TrainSample`, `HistoryTurn`,
`SampleContext`, `ToolSpec`, the three decisions, `ToolCall`, `SubmissionRow`,
`ObservationRecord`, `ReferenceEvidence`, `Goal`, `GoalOccurrence`, `FoldRecord`,
`TrajectoryRecord`, `RunMetadata`, `DiagnosticRecord` and `TrainingRunRecord`.
Config models in `config.py` cover common paths/budgets, inference, backend/ASR,
preparation/evaluation and training options. Use narrow typed structures and JSON
payload aliases instead of pervasive `Any`.

`InferenceSample` is an allowlisted projection with no label, final-state, oracle
target or future observation field. Only explicitly authorized train oracle mode
maps `audio_text` to current/history text; public/private modes reject oracle mode.
Unknown manifest fields never reach policy prompts by accidental model dumping.
Permitted nested context/profile and dynamic schema annotations are preserved as
JSON payloads. `ToolSpec` preserves extensions, nested schemas, descriptions and
returns; do not turn it into a closed global train-tool enum.

`artifacts.py` owns normalized paths and atomic JSON/JSONL writers. Config-relative
paths resolve against the config file's parent; CLI path flags resolve against
the invoking working directory. Resolve existing ancestors and reparse/symlink
targets before access. Reject output anywhere inside source, kit roots, model or
tokenizer/adapter inputs, or overlapping other inputs/outputs. Audio paths must
stay within the selected split's authorized audio root and must never resolve to
an environment directory. Do not recursively walk organizer/model roots to find
inputs or destinations. Output roots are explicit, not inferred from current data.

Publish completed artifacts by write-to-unique-sibling-temporary-file, flush/close,
validate and atomic replace, with failure cleanup limited to that owned temporary
file. Refuse existing destinations by default. A new run uses a new output name;
no implicit overwrite/resume. Checkpoints have `.partial.jsonl` plus run metadata
with exact selected/completed IDs and RUNNING/FAILED/INTERRUPTED status. The final
requested submission path appears only after full selection integrity passes.
Diagnostics and training directories remain explicitly incomplete on failure.
No aborted environment is reconstructed from a checkpoint.

`provenance.py` computes ordered path/byte SHA-256 manifests recursively for
`src/lifemate/**/*.py`, `py.typed`, configuration, scripts, package manifest and
packaging entrypoints used in a run. Include relative POSIX path, length and digest
in a stable aggregate; nested source edits must change `source_sha256`. Record
available SDK/catalog/manifest/template/model/adapter identities separately.
Hash declared local metadata/assets as configured without discovering hidden
state. Never substitute a provenance digest for the SDK state hash. Diagnostics
use allowlisted metadata and sanitized exceptions, not arbitrary config/env dumps
or transport credentials.

## 4. Interfaces, data flow and errors

Typed protocols in `adapters/protocols.py` define:

- `Clock.monotonic() -> float` for deterministic budget fixtures.
- `Asr.transcribe(path, *, deadline) -> Transcription`, preserving raw text,
  normalized association, measured timing and turn identity.
- `Policy.next_action(messages, *, deadline) -> str`; parsing is shared downstream.
  A separate `GoalPlanner.plan(request_context, *, deadline) -> GoalPlan` produces
  internal intent evidence only. Local policy adapters expose a shared bounded
  JSON-generation helper for that planner; it is not an official tool or a change
  to the CALL/ASK/DONE protocol.
- `Session.validate/call/get_tool_calls/get_state_hash` for inference. It deliberately
  has no `get_state`. A separate train-replay protocol exposes sanctioned
  `get_state` for transient authorized replay comparisons only.
- `TrainingRuntime.train(validated_inputs, config) -> TrainingResult`, with an
  injected fake runtime for core checks and a real lazy TRL/PEFT implementation.

The inference workflow validates selection and paths, constructs local backend
objects once per run, and starts sample timing before its SDK factory. It creates
exactly one selected-split session, transcribes latest/history user audio in
chronological association (or explicitly maps train oracle text), normalizes
supported expressions, builds references/eligible schemas/goals, and iterates
proposal → parse → semantic/schema preflight → SDK validate → budget check → SDK
call → actual observation → ledger update. ASK maps to the real authorized
`sys.ask_missing_info` shape and ends the turn. DONE remains internal. At exit,
only the same session getters provide submission calls/hash, including failed
executed attempts. No reset/second environment and no inference state getter.

Kit resolution checks direct known catalog paths or one outer wrapper, with
selected-split manifest/catalog/SDK completeness and ambiguity errors. Preserve
the split/path-based private SDK namespace and failure cleanup; no train fallback.
Only permitted inputs and sanctioned SDK loading are used. The registry is the
installed app/tool association intersected with selected catalog plus authorized
system ASK; schema/content assertions guard malformed associations. Every eligible
schema reaches context compilation. Tool/result data are input evidence, not new
instructions or permissions.

`runtime/normalize.py` returns raw text plus explicit span-based normalized values,
uncertainty, negation and latest-correction evidence. Support tested Vietnamese
money units including `nghìn`, `triệu`, `rưỡi`, half-hour/`kém`, relative `mai`,
`sau`/`trước`, explicit time/date and supported next-weekday expressions. Resolve
from sample aware current_time/timezone, including rollover; reject inconsistent
or missing time context when needed. Unsupported/ambiguous phrases stay uncertain.
Never rewrite phone strings, content or optional values with a blanket normalizer.
Resolve equal/past/future ride times against the sample clock and preserve SDK
semantics rather than inventing a scheduled effect.

`runtime/context.py` keeps latest request identity, chronological user/assistant
turns, prior calls/results, profile/location/time, original/normalized transcripts,
eligible schemas and current observations. No history call is executed. Budget
all content before generation; fail with CONTEXT_OVERFLOW if required material
cannot fit. No silent schema/reference pruning. The same context builder is used
for inference and teacher-forced actions, with separate labelled preparation code.

`runtime/references.py` indexes value, source turn/observation/span, schema or
collection type, and known parent/type attributes. Explicit user/schema literals
and valid history references can ground without another read; membership in a
filename does not. Known collection/device/restaurant-menu mismatch blocks the
write. Multiple/zero candidates remain unresolved; do not pick the first. Absence
of type evidence is not fabricated negative evidence, and provenance does not
prove current existence. An ungrounded reference must be repaired via permitted
read/ASK; the completed runtime enforces this even if the legacy diagnostic flag
is omitted. Retain the flag as a deprecated accepted spelling for enforcement.

`runtime/validation.py` supplements strict envelopes with recursive dynamic schema
checks for nested required fields, known keys, exact primitive types/enums,
numeric/format constraints and actual x-one-of alternatives. Preserve legitimate
explicit optional values. Check semantic/reference/goal constraints before final
`env.validate`. A rejected proposal produces no real call/log entry. A repair is
at most the configured finite count within the same sample deadline/session.
An invalid executed attempt remains in the actual trace forever.

Failures distinguish configuration/input/asset/SDK initialization, ASR, context,
parse/validation, backend timeout, unknown tool outcome and output-integrity errors.
Backend/output errors never authorize a call. SDK initialization or getter failure
is fatal for that sample/run: no dummy hash or fabricated complete output. An ASR
failure cannot fall back to oracle text or become successful unsupported DONE.
If a session exists, preserve its real trace/hash for diagnostics where getters
work; incomplete run metadata prevents publishing an incomplete final submission.
Timeout/cap with usable getters retains actual calls/hash and explicit stop reason.
Check clock before each planning/decision/repair generation and immediately before
each real call. Include SDK creation, ASR, goal planning, tools and serialization
accounting in total elapsed diagnostics; backend setup time is separately recorded.
No claimed preemption of SDK initialization, kernels/prefill or filesystem work.

## 5. Goal evidence, conditions and safe repeated actions

Use a request-scoped ledger, not a global equality cache. Goal IDs are internal,
stable within one sample and backed by latest-request spans; occurrences distinguish
two explicitly requested identical actions. Each goal carries semantic intent,
target/effect, dependencies, optional condition predicate/evidence, status,
supporting observation IDs and occurrence states. Planner output is validated:
IDs unique, dependencies acyclic/existing, spans refer to supplied latest request,
tool references eligible, repetitions supported by distinct explicit intent.
History may resolve references but cannot create newly executable past goals.
Malformed or unresolved planning receives bounded repair, then a truthful blocked
outcome; never silently assume no goals and execute unrestricted writes.

The planner is the local policy runtime operating on permitted request/context and
schemas. Its decomposition/semantic bindings remain model hypotheses. It cannot
declare effects complete, supply fictitious observations, fabricate reference IDs
or bypass argument validation. Controlled tests inject planner outputs, including
unsupported, canceled, independent, dependent and conditional goals. They prove
software enforcement, not learned decomposition accuracy. No extra auxiliary
model or vendor is selected. Goal planning shares configured generation/deadline
budgets; `max_decisions` still counts next-action proposals so six calls plus DONE
remain possible when sample time and other generation budgets permit.

Before a mutation, a bounded internal binding step associates the proposed action
with a pending goal occurrence and its evidence; never add a `goal_id` field to
the official/custom action JSON. Read actions may supply evidence for multiple
goals but do not alone fulfill dependent write goals. Conditions are predicates
over identified actual observation fields and supported comparisons, with true,
false and unresolved results. Only observed true permits the conditional write;
false blocks that branch, unresolved requires a permitted read/ASK or explicit
blocked stop. A model's statement that it rained is not observation evidence.

Outcome classification uses the existing source-grounded per-tool markers,
extended only from inspected authorized SDK/schema contracts. Kinds are
SCHEMA_REJECTED, BUSINESS_NOOP, WRITE_EFFECT, READ_OBSERVATION, META_WAIT, UNKNOWN.
`done:false` cannot fulfill a write; absence of `done` is not failure for a known
supported successful shape. Unknown split tools remain eligible, with conservative
UNKNOWN outcome if effect semantics cannot be established. Completion requires
actual compatible effect evidence for the bound occurrence. Ledger transitions
record why an occurrence completed, was canceled, blocked or waits on a condition.

An occurrence with confirmed write effect cannot execute again to verify success.
An attempted mutation with unknown/possibly partial outcome is quarantined and
never blindly retried. A proven no-effect can allow bounded recovery: new actual
lookup/correction evidence must address the observed cause, all preflight applies,
and the occurrence remains pending. Do not loop on the same no-op. Two distinct
requested occurrences may execute equal dictionaries once each. If binding is
ambiguous, block/clarify rather than consuming the next occurrence arbitrarily.
No universal read pruning or always-read-before-write rule is introduced.

DONE with pending executable goals triggers at most one configured reconsideration
using ledger diagnostics; it does not auto-execute a call. Continued premature
DONE stops as PREMATURE_DONE/BLOCKED with the true trace. Unsupported/withdrawn
goals produce no unintended actions; completed independent work remains. ASK for
a remaining installed target/real missing fields may follow that work and is
terminal. The planner/binder's real semantic quality remains a deferred experiment.

## 6. Learning, evaluation and offline adapters

Frozen train partitions precede expansion. Preserve source manifest bytes digest,
seed, exact declared IDs and named grouped/leave-app-out folds. Selection validates
disjointness, full declared coverage and foreign/duplicate IDs, including the
leave-app-out fold. Reordering the same supplied record list does not alter ID
assignment; a changed source-file digest is drift requiring explicit refreeze.
Never silently regenerate a fold. Training workflows require source_split=train.

Standalone replay uses one fresh train session per scenario, ordered gold calls,
actual results and SDK hash. Compare results/trace and changed-app state with
authorized labels through SDK getters; raw states are transient in this isolated
workflow, never written into reports or passed to inference. Report mismatch
indices/apps and fingerprints, not simulator snapshots. Replay/trajectory code
accepts injected session factories so core checks need no real-data replay.

Trajectory rows retain scenario/fold/partition/step/source/protocol/schema/context
identity, messages, one explicit target and prior-observation provenance. Only
the prefix before that target is included. Compare each executed gold observation
before accepting the preparation output; drift fails the entire atomic result.
CALL/ASK and terminal DONE use one shared serializer; ASK trajectories still get
their required terminal training DONE even though inference ASK ends its turn.
Zero-call scenarios yield immediate DONE. Do not add gold-derived goals/future
effects to inference prompts or make a new goal-plan training objective here.
Action training uses the shared action-context contract; optional internal goal
planning is a separate local orchestration prompt with separately recorded identity.

Select custom JSON prompt/completion SFT. Render the prompt with the local policy
tokenizer/template and generation prompt (non-thinking), append the serialized
single assistant action and appropriate EOS. Verify the prompt token sequence is
an exact prefix of the full sequence; reject boundary/template inconsistency.
Labels are `-100` for every prompt/history/observation/previous-action token and
padding, with target IDs only for this one action and its EOS. At least one action
token must remain. Reject oversized examples, empty targets and unexpected role
shapes; never truncate required tools/history/target to force training. A custom
collator pads IDs/attention/labels without losing masks. Tokenizer-only fixtures
check READ→WRITE, ASK, DONE and pad==EOS. Real tokenizer/forward-loss checks are
deferred and documented as necessary before actual training.

The real lazy trainer loads local tokenizer/base CausalLM with local_files_only
and trust_remote_code=False; disables telemetry/hub reporting, applies validated
PEFT LoraConfig, builds SFTTrainer with pretokenized fit/eval data, explicit
processing_class/custom collator, and invokes `train()` then adapter/tokenizer
save and metrics persistence. Use SFTConfig dataset_kwargs skip_prepare_dataset,
packing=False, padding_free=False, max_length=None, remove_unused_columns=False
so preprocessing cannot replace the verified labels or truncate inputs. The
application enforces configured max sequence length itself. No chat-wide
assistant_only_loss shortcut that also supervises previous actions. Train-only
and config/preflight paths are separate; `train --dry-run` never imports a heavy
runtime, loads weights/tokenizer, starts SDK replay or calls trainer.train.

Training config specifies base/tokenizer/template and input/fold digests, LoRA
rank/alpha/dropout/target modules, epochs/learning rate/batch/accumulation/seed,
precision, context length and new output directory. Begin with ordinary LoRA,
not QLoRA/bitsandbytes. Validate unsupported options and hardware requirements
on the actual later-run platform. Runtime exceptions/interruption leave FAILED/
INTERRUPTED metadata and discoverable partial checkpoints; COMPLETE only after
expected adapter/tokenizer/provenance artifacts exist. Loading that adapter is
supported by the Transformers policy via local PeftModel; Ollama receives an
already installed compatible model, with no automatic merge/conversion/import.
Guide the direct Transformers adapter route; defer Ollama conversion research.

Retain maximum one-to-one PROXY matching, multiplicity, exact-key/fuzzy choices,
empty/hash gate and independent call/hash diagnostics. Add first/later actions,
whole trajectory, ASK/empty confusion, error taxonomy, slices, per-sample paired
regression and supplied timing summaries. Require exact frozen selection and
replay/config identity; unsupported metrics are null/unmeasured. ASR comparison
pairs same IDs/config with WER/CER edit-distance denominators and critical-slot
diffs (including negation, correction, phone, amount, time and name); zero-length
references have explicit denominator/error counts rather than divide-by-zero.
It consumes supplied artifacts and cannot launch models as a side effect.

Whisper-compatible local ASR is the selected minimal speech backend, using local
Transformers processor/seq2seq model and soundfile/scipy audio loading/resampling.
Validate WAV/readability, rate/channels/duration; deterministic conversion to
backend-required PCM rate is explicit and tested with tiny generated audio.
Latest and earlier user audio use the same adapter/deadline. No model identity or
quality claim is selected from unrun candidates. Missing/unsupported assets fail.
Ollama retains its loopback-only origin/proxy/redirect/cloud/missing-model guards
and deterministic decoding. Transformers policy and ASR use only local assets,
no remote code/downloads, explicit token/context caps and late-response rejection.

## 7. Dependencies and API compatibility

Declare the following selected bounds in `pyproject.toml`; exact platform wheel
and full transitive installation compatibility are NOT VERIFIED until later setup.
No optional dependency is installed now or needed by deterministic core tests.

| Group | Selected declarations | Purpose |
|---|---|---|
| core | `pydantic>=2.10,<3`, `tzdata>=2024.1` | Strict contracts; sample IANA zones on Windows |
| dev | `ruff>=0.9,<1`, `mypy>=1.14,<2`, `build>=1.2,<2`, `setuptools>=68`, `wheel>=0.45,<1` | Lint/format, typed source, wheel/sdist without build isolation |
| ollama | `tokenizers>=0.22,<0.23` | Optional locally supplied tokenizer; existing conservative fallback retained |
| model | `torch>=2.2,<3`, `transformers==4.56.2`, `accelerate>=1.4,<2`, `peft==0.17.1` | Local policy and adapter loading |
| asr | same torch/Transformers/accelerate bounds, `soundfile>=0.12,<0.14`, `scipy>=1.11,<2` | Local Whisper-compatible speech path |
| training | model bounds plus `trl==0.23.1`, `datasets>=3,<4` | Actual supervised LoRA integration |

These retain Transformers <5 and intentionally avoid a floating latest TRL major.
Versioned [TRL 0.23.1 dependency metadata](https://github.com/huggingface/trl/blob/v0.23.1/setup.cfg)
requires Transformers >=4.56.1, Accelerate >=1.4 and Datasets >=3; 4.56.2 satisfies
that declared intersection. [PEFT 0.17.1 metadata](https://github.com/huggingface/peft/blob/v0.17.1/setup.py)
supplies the adapter dependency basis. This is declaration/API inspection, not
proof of a resolved installation or trained model.

The selected integration follows the versioned [SFT API](https://huggingface.co/docs/trl/v0.23.1/sft_trainer)
and [trainer source](https://github.com/huggingface/trl/blob/v0.23.1/trl/trainer/sft_trainer.py)
for supplied labels/collator and skipped dataset preparation. Custom completion
masks enforce this project's single-action objective. [Whisper documentation](https://huggingface.co/docs/transformers/v4.56.2/en/model_doc/whisper)
supports the selected processor/generation boundary. [Pydantic strict-mode guidance](https://docs.pydantic.dev/latest/concepts/strict_mode/)
supports strict boundary validation; project JSON parsing still handles duplicate
keys separately. These primary references were inspected during Architecture.

Use Ruff E/F/I/UP/B with line length 100 and Python 3.10 target; format changed
application/test/script files consistently. Mypy checks all `src/lifemate` with
typed public boundaries, check_untyped_defs and no_implicit_optional; local SDK
and optional third-party imports use targeted stubs/ignores only at adapter
boundaries, never a blanket ignore of project errors. No pytest conversion,
type-framework plugin or new CI/release automation is needed. Build includes only
owned package/typed metadata and source/docs/configuration, no data/models/venv.

## 8. CLI, configuration, migration and packaging

Retain `lifemate`, `python scripts/lifemate.py` and add `python -m lifemate` with
the same parser. Keep existing `freeze`, `predict`, `evaluate`, `trajectories`,
`validate` flags and meanings. In particular legacy `predict` without input-mode
remains frozen train oracle validation, default Ollama unless model-path selects
Transformers; `--limit` remains manifest-order pilot prefix. Accept existing script
wrappers and imports rather than replacing them with duplicated workflow logic.

Add `--config PATH` for validated JSON command configs; explicit CLI flags override
config values (only supplied flags, not parser defaults). Add `config-check
--kind {inference,training,evaluation} --config PATH`: syntax/paths/configuration
only, no model/session/service. Add:

- `predict --split {train,public_test,private_test} --input-mode {oracle,audio}
  --selection {validation,fit,all} --fold {grouped,leave-app-out}`. Audio uses an
  explicit ASR config/path; oracle requires train. Frozen train selections require
  split-config; all public/private manifest selection does not require a train
  fold and cannot accept test labels. All-rows selection is explicit.
- `replay --data-root PATH --out PATH`; `audit --data-root PATH --out PATH` reads
  safe catalog/SDK metadata only. Preserve `scripts/replay_gold.py` syntax.
- `train --config PATH [--dry-run]`; default actual train is only an explicit
  operator command, never dispatched by preparation. `scripts/train_lora.py`
  delegates to it. Dry-run validates config/identities/local file prerequisites
  and reports execution NOT RUN without loading a tokenizer/model.
- `compare --baseline PATH --candidate PATH --out PATH` for compatible evaluation
  reports, `asr-evaluate --reference PATH --candidate PATH --out PATH` for paired
  authorized supplied transcripts/results, and `package-check --config PATH`
  for static asset/path/dependency/entrypoint checks without model execution.

Examples: `configs/inference.ollama.json`, `inference.audio.json`, `training.lora.json`,
`evaluation.json` use explicit external placeholder paths and example budgets
(25 sample seconds, 9 next-action decisions, 1 parse repair, 1 DONE reconsideration,
configured finite planning/generation cap). The values are operator hypotheses,
not official limits. Bad/missing example asset paths fail preflight clearly.
Guide commands tell users to copy/edit configs outside source before runtime.

Existing wrappers retained: `scripts/lifemate.py`, `replay_gold.py`,
`check_trajectories.py`, `check_evaluator.py`, `smoke_runtime.py`, `smoke_ollama.py`,
`start_ollama.ps1`. Update forwarding/guarded entrypoints and import compatibility.
The smoke commands that actually run models or real scenarios remain later-run
only. Tests exercise their help/argument forwarding through injected workflows.

Add `Dockerfile`, `.dockerignore`, `predict.sh`, `scripts/predict.py`,
`scripts/verify_package.py`. Docker build consumes an operator-prepared local
wheelhouse at build time with `--no-index`; source/SDK/weights are not downloaded
at startup. Models/tokenizers/adapter, kit and output are explicit external mounts;
exclude all such assets from build context. Default container policy is local
Transformers+optional adapter plus Whisper ASR, which can operate with network
disabled. Existing local Ollama remains supported on the host; a separate Ollama
service is not silently bundled into a single offline container.
`predict.sh` uses `exec python -m lifemate predict` and passes supplied arguments;
LF/shebang/mode requirements are verified on the later Linux platform. Base image,
wheelhouse and GPU runtime are operator prerequisites, with no certified official
mounts or resource defaults. No image is built in this work item.

Add `docs/architecture.md`, `docs/local_training.md`, `docs/operator_guide.md`,
`docs/migration.md`, `docs/offline_packaging.md`, `docs/edge_case_coverage.md`.
Update README entrypoints/status and `docs/p0_coverage.md`/`docs/verification.md`
without rewriting historical results as current passes. Preserve existing rules,
catalog/scorer audit and experiment history; link their limits. Training guide
covers reviewed base/model/tokenizer identity/license, platform-specific later
environment creation, fit/fold freeze, legal replay, trajectories, mask/tokenizer
checks, LoRA invocation/save/resume constraints, adapter inference and paired
evaluation. Explain CPU/Windows software checks versus separately provisioned
Linux/CUDA training, optional installs, hardware/precision/OOM troubleshooting,
data drift, output collisions, incomplete runs, context/budget failures and unknown
official rules. Never tell the reader Ollama trains LoRA.

## 9. Ordered implementation tasks and done conditions

Every operation here is proposed, NOT executed. Task ordering is sequential at
shared files; no subworker dispatch or parallel edit authority is implied. `new`
means create; `edit` includes bounded movement of implementation into the selected
new module while retaining its old facade. No source-file deletion is planned.

| Task | Dependencies; paths/operations | Observable done condition |
|---|---|---|
| TASK-01 | After exact plan approval + separate grant: establish immutable before snapshot by §12; inspect latest owner bytes; no product edit yet | Complete scope manifest/bytes and protected/process inventories verified; collisions/owner differences resolved before edits. AC-34 |
| TASK-02 | 01; edit pyproject.toml; new contracts.py/config.py, package initializers/py.typed; add configs; tests/test_contracts.py | Strict validated config/sample/decision/fold/diagnostic/training boundaries; explicit paths/budgets; core import with no heavy libraries; valid/negative/extension roundtrips. AC-01/02/33 |
| TASK-03 | 02; new artifacts.py/provenance.py; edit submission.py facade; tests/test_artifacts.py | External/protected-input path checks, symlink/normalized collisions, atomic completeness/refusal behavior and recursive nested-source identity covered. AC-20/21/22/28/36 |
| TASK-04 | 02; new data/kit.py/splits.py, adapters/protocols.py/sdk.py; edit data_loader.py/toolenv_adapter.py facades; tests/test_data.py, test_sdk_contract.py | Direct/wrapper split resolution, valid manifests/projections, eligible schemas, frozen grouped/app-out folds and selected actual SDK synthetic contracts; no inference raw state or train fallback. AC-03/04/08/12/24 |
| TASK-05 | 02/04; new adapters/whisper.py, runtime/normalize.py/context.py; edit context_builder.py facade; tests/test_audio.py/test_normalize.py/test_context.py | Latest/history audio associations, oracle separation, sample-clock quantities/corrections/uncertainty, required context/schema retention and explicit overflow/error behavior. AC-05/06/07/09/30 |
| TASK-06 | 02/04/05; new runtime/references.py/validation.py/outcomes.py; edit references.py/validator.py facades; tests/test_validation.py/test_references.py plus SDK fixtures | Fabricated/type-parent mismatched IDs blocked; strict nested/x-one-of/ASK preflight and SDK final guard; successful/no-op/unknown tool classification with exact attempts. AC-10/11/13/14/16/18 |
| TASK-07 | 02/04/05/06; new runtime/goals.py/loop.py; edit agent_loop.py facade; tests/test_goals.py/test_loop.py and existing runtime regressions | Validated injected planner/condition/occurrence behavior; one env; actual observations; bounded DONE reconsideration/repair/recovery; deliberate repeats, cancellation, independent goals, ASK, six calls+DONE and injected late clocks pass. AC-11/12/14/15/16/17/18/19 |
| TASK-08 | 02/04/05/07; new adapters/ollama.py/transformers.py; edit policy.py/ollama_policy.py facades and test_ollama.py; tests/test_backends.py | Shared bounded generation for planner/action; local-only guards preserved; adapter selection, absent optional dependencies, malformed/late responses and no-download/help behavior tested with fakes. AC-02/11/19/28/35 |
| TASK-09 | 02/03/04/05/06; new data/replay.py/learning/trajectories.py; edit replay.py/trajectory_builder.py facades and replay/check-trajectory wrappers; tests/test_preparation.py | Injected exact/drifting replay with sanctioned state getter only in train replay; frozen-prefix target rows incl ASK/zero/DONE; provenance and no future observations; atomic failure. AC-23/24/25 |
| TASK-10 | 02/03/08/09; new learning/serialization.py/trainer.py, scripts/train_lora.py; tests/test_training.py | Deterministic mask/collator/tokenizer fixtures, data/config/runtime injection tests, real TRL/PEFT train/save path statically reviewed, dry-run side-effect guard, truthful save/failure and adapter contract; no actual training. AC-26/27/28 |
| TASK-11 | 02/03/04; new metrics/proxy.py/reports.py/asr.py; edit evaluation.py facade and evaluator wrapper; tests/test_evaluation.py/test_asr_metrics.py | Maximum matching regressions retained; exact frozen selection/reference checks, paired reports/slices/metrics/protected diagnostics; supplied ASR/oracle pairing and slot metrics with unavailable fields explicit. AC-22/29/30 |
| TASK-12 | 03–11; edit cli.py and existing scripts; new workflows.py/__main__.py, scripts/predict.py/verify_package.py, Dockerfile/.dockerignore/predict.sh; tests/test_cli.py/test_packaging.py | All existing command meanings/consumers and new audio/public/private/train/config/package routes exercised via injection; complete pipeline forwarding, offline static packaging/missing-path checks and import/help no jobs. AC-02/20/21/22/27/31/33/35/36 |
| TASK-13 | 02–12; new/edit guides from §8; tests/test_guides.py; edge coverage document | Complete PowerShell and later Linux/CUDA/operator paths match help/configs/artifacts, compatibility changes explicit; every K01–K54 has named synthetic/SDK check or deferred evidence row and P0 pre-training gate. AC-32/33/34 |
| TASK-14 | 01–13; execute permitted core/static checks in §11; prepare implementation evidence and immutable after snapshot by §12 | All required software checks pass with exact commands/exit codes and skips distinguished; AC matrix actual results/deferred limits; full before/after change inventory and independent review handoff, no self-approval. AC-01–36/34 |

## 10. Complete acceptance-to-task-to-check matrix

All checks below are proposed NOT RUN. Test paths are under `tests/`. Existing
tests remain behavioral regressions; new files have the exact planned names above.
U/I denotes deterministic synthetic or injected software evidence. SDK means
external actual SDK with self-generated Session state only. D is deferred real
runtime proof and never a condition silently reported PASS by a fixture.

| AC | Tasks | Named verification and required assertion |
|---|---|---|
| AC-01 | 02/06 | test_contracts strict boundary/unknown config/extension roundtrip; test_validation integer bool/string/float/nested payload rejection; executed workflow model validation |
| AC-02 | 02/08/12 | test_cli help/config-check/dry-run factories untouched; test_backends missing deps/assets; finite positive budget tests |
| AC-03 | 04 | test_data direct/wrapper/ambiguous/missing selected assets; SDK split namespace fixture; forbidden-state-access spy |
| AC-04 | 02/04 | test_data duplicate/bad manifest, sentinel gold stripping and train-only oracle; capture actual policy requests in test_cli |
| AC-05 | 05/12 | test_audio recording-ASR latest/history chronology; equivalent oracle/audio downstream requests; D actual ASR |
| AC-06 | 03/05 | test_audio missing/corrupt/path escape/ASR exception; zero resulting call and explicit failure |
| AC-07 | 05/07 | test_context time/profile/history IDs/schema preservation/overflow; prior writes never replayed |
| AC-08 | 04/05 | test_data installed association/public-only schema/unknown app and all extensions; capture full eligible schemas |
| AC-09 | 05/07 | test_normalize amounts/half-hours/correction/negation/midnight/year/timezone/ride boundaries/ambiguous phrase; test_loop no stale write |
| AC-10 | 06/07 | test_references literal/schema/history/live IDs, ambiguous/empty lookup, invented ID, wrong device/restaurant-menu type; no needless history read |
| AC-11 | 02/06/07/08 | test_validation strict single JSON/duplicate keys/nonfinite/unknown shape; repair/session preservation in test_loop; shared training serializer roundtrip |
| AC-12 | 04/07 | test_loop counted factory across rejection/timeout, forbidden get_state and factory error; SDK split checks |
| AC-13 | 06/07 | test_validation nested objects/one-of/range/enums/unknown key/ASK and SDK-denial; call-order spy preflight→validate→call |
| AC-14 | 06/07 | test_loop read/empty/meta/no-op/known no-done success/unknown/exception; test_sdk_contract failed logged attempt |
| AC-15 | 07 | test_goals dependencies/multigoal/premature DONE/rain-no-rain with real fixture evidence; test_loop completion/blocked independent work; D learned semantics |
| AC-16 | 06/07 | test_loop ambiguous/missing target, valid terminal ASK after success; test_validation invalid target/params rejected |
| AC-17 | 05/07 | test_loop unsupported/withdrawn/history-only/partial request; true unchanged getter hash, distinct input failure reason |
| AC-18 | 06/07 | test_goals occurrence-level successful-write guard, unknown mutation quarantine, proven no-effect correction and two explicit identical actions |
| AC-19 | 05/07/08 | test_loop injected clock before creation/ASR/planner/decision/call/serialization, late policy and cap/repair stop; six calls+DONE; D p50/p95/p99/hard limits |
| AC-20 | 03/07/12 | test_artifacts Unicode/order/unknown-extra-missing-duplicate rows/exact fields; getter fidelity incl failed call; SDK text/read hash distinctions |
| AC-21 | 03/12 | test_cli fail after completed sample, factory/getter failure/interruption; final absent, partial marked, no reset/resume/completeness bypass |
| AC-22 | 03/07/11/12 | test_artifacts recursive source identity; test_cli diagnostic successful/fail/timeout metadata and protected-field sentinels; test_evaluation error/timing unmeasured fields |
| AC-23 | 04/09 | test_preparation one fresh train replay env, mismatching result/state/trace, ASK/zero hash from getter; no state persistence; D all real train replay |
| AC-24 | 04/09/10 | test_data reproducibility/source drift/foreign-overlap/app-out; test_training reject test-derived or mismatched source/fold selection |
| AC-25 | 09 | test_preparation READ→WRITE/ASK/empty/later prefix/terminal DONE and replay drift/alignment; no future target observation in request |
| AC-26 | 10 | test_training deterministic tokenizer prefix/labels/padding/target roundtrip/context rejection; D real tokenizer and forward/loss smoke |
| AC-27 | 10/12 | test_training injected trainer real options and errors, invalid paths/deps/data; test_cli dry-run loads nothing; source review actual train() integration; D real LoRA |
| AC-28 | 03/08/10 | test_training save/provenance/FAILED/INTERRUPTED outputs; test_backends local adapter selection and protocol; D real save/reload/quality |
| AC-29 | 11 | test_evaluation empty/hash gate, unequal text same hash, duplicates/extra-read/fuzzy/greedy collision, frozen mismatch, first/later/paired reports; D official parity/model score |
| AC-30 | 05/11 | test_asr_metrics same-ID/config pairing, missing pairs, WER/CER/empty denominator and critical slots/deltas supplied provenance; D paired actual ASR |
| AC-31 | 08/12 | test_packaging static context/mount/backend/entrypoint consistency; injected complete audio split pipeline and missing assets; D actual build/offline image/resources/official release |
| AC-32 | 13 | test_guides commands/config names/outputs and manual full operator-path review; D operator setup/training/runtime path execution |
| AC-33 | 02/08/12/13/14 | test_cli/test_guides old/new help/wrappers/side-effect-free imports, architecture import boundaries; Ruff/mypy/build plus representative workflow trace |
| AC-34 | 01/13/14 | before/after manifest/review/grant/receipts audit, actual command evidence and deferred table; independent Reviewer then exact-snapshot human acceptance |
| AC-35 | 08/12 | test_ollama origins/proxies/redirects/cloud/remote/missing model; test_backends local-only Transformers/assets, malformed/late output no calls; D real backend speed/compatibility |
| AC-36 | 03/10/12 | test_artifacts normalized source/input/output/reparse collision and atomic failure; trainer partial statuses; build/guide asset exclusion inspection |

All INT-01–INT-13 and C01–C15 remain traced through the approved Spec matrix and
the complete AC rows above. `docs/edge_case_coverage.md` maps every K01–K54 to a
named test, evidence kind and actual status. Distribution: K01–K13 → data,
validation, loop, SDK; K14–K24 → references/goals/SDK; K25–K34 → goals/loop;
K35–K43 → normalization/validation/SDK; K44 → ASR metrics; K45–K52 → SDK/proxy;
K53 → artifacts/CLI; K54 → data/SDK. Retain the explicit original pre-training P0
gate: K01–K13, K18, K25–K30, K35–K38, K45–K48, K53. All remaining cases stay
visible, including POLICY/SCORER uncertainty; synthetic behavior never establishes
hidden gold conventions. Training guide requires current software gate, real
authorized replay, frozen baseline and tokenizer/loss proof before later training.

## 11. Proposed commands and evidence boundary — all NOT RUN

Run later from the explicit implementation root using a new core-only `.venv-core`
(do not alter existing owner `.venv`). These commands are a proposal for the
separate edit grant; Architecture runs none of them:

```powershell
python -m venv .venv-core
.venv-core/Scripts/python.exe -m pip install -e ".[dev]"
.venv-core/Scripts/python.exe -m pip check
.venv-core/Scripts/python.exe -m unittest discover -s tests -v
.venv-core/Scripts/python.exe -m compileall -q src scripts tests
.venv-core/Scripts/python.exe -m ruff check src scripts tests
.venv-core/Scripts/python.exe -m ruff format --check src scripts tests
.venv-core/Scripts/python.exe -m mypy src/lifemate
.venv-core/Scripts/python.exe -m build --no-isolation
.venv-core/Scripts/python.exe -m lifemate --help
.venv-core/Scripts/python.exe -m lifemate train --help
.venv-core/Scripts/python.exe scripts/lifemate.py predict --help
.venv-core/Scripts/python.exe scripts/train_lora.py --help
.venv-core/Scripts/python.exe scripts/predict.py --help
.venv-core/Scripts/python.exe scripts/verify_package.py --help
```

Core/dev installation may access the configured package index and write only the
new environment and project build metadata (plus explicitly directed local pip
cache); no training/model/asr/ollama extras, services or asset downloads. Set
`PIP_CACHE_DIR` to `.venv-core/pip-cache`, avoid user/global installs. The declared
dev setuptools/wheel requirements support `build --no-isolation` in that same
core environment. No package upgrade of the
owner environment. If the managed host disallows the proposed install, report
actual blocked check rather than asserting success or escalating scope silently.

The unittest suite separates core/injected tests from actual external SDK
synthetic Session contracts; print skip reasons if the authorized SDK is absent.
Tests never instantiate real-data ToolEnv or contact Ollama/models. Use actual
train/public SDK Session on generated state only if available, never enumerate
real environment state. Required SDK checks skipped for absence mean NOT VERIFIED
and must be visible to Reviewer; do not treat a skip as a pass. Build inspection
checks wheel/sdist membership for accidental organizer/model/data inclusion.
Focused fixes may use Ruff format/check-fix only on granted files, followed by the
read-only checks above. Guide/config tests use generated temporary configs/assets
and injected factories, not the example's nonexistent model paths.

Future operator-only commands documented, NOT authorized to execute in this work:
install `.[model,asr,training]` on a separately provisioned reviewed platform;
audit real kit; real replay/freeze/trajectory generation; actual tokenizer/model
smoke, forward/loss, LoRA train/adapter load; oracle/audio holdout inference;
paired comparisons; Docker build/run --network none and official validator.
These require reviewed local assets and separate runtime/setup scope. Official
validator printed error counts must be inspected; exit zero alone is insufficient
as described by the current audit. Resource totals, actual latency/memory/quality,
official scorer parity and mount/entrypoint certification remain UNKNOWN/NOT RUN.

Architecture's actual checks: read-only PowerShell Get-Content/Select-Object,
rg inventories/searches, directory metadata and Get-FileHash returned exit 0;
primary versioned library pages were read. The recurring PowerShell host startup
drive warning did not prevent file reads. This artifact's read-back/coverage/link
check and final hash are returned in the handoff. Application tests/build/lint,
snapshot capture and installations: NOT RUN.

## 12. Immutable no-Git snapshot, review and rollback

Approval of r1 explicitly agrees to the following snapshot method, but capture
requires the separate grant. Do not initialize Git or pretend historical code is
this work's output. Before any app edit, capture every existing owner byte in
the application review scope, not merely the anticipated changed file list.

Use a new unique directory under
`docs/ai/work/LM-002-python-structure-training-guide/snapshots/` with `before/` and
later `after/` content stores. Each store contains an immutable ordered UTF-8 JSON
manifest and copied full bytes under their relative paths. Manifest records root,
snapshot schema, capture time, relative POSIX path, file/directory/link type,
length, SHA-256 and available Windows attributes/mode/link target. Reject escaping
reparse points; do not traverse links. Record empty directories and relevant mode/
type changes. Stable aggregate hashes use canonical ordered manifest records,
excluding capture-time metadata from the identity. Re-read each copied file and
compare to live source before sealing; a changing file aborts capture. Mark sealed
stores read-only and never overwrite/reuse their paths. Read-only flags plus
hash verification are procedural immutability, not tamper-proof storage.

Application scope is **every regular file under the implementation root**, whether
ignored/untracked/hidden or unexpected, except the following explicit exclusions:

- Protected process/rule trees: `AGENTS.md`, `.agents/**`, `.ai-sdlc/**`, `.codex/**`,
  all `docs/ai/**` (including snapshots); hash separately in a protected/process
  manifest, with exact stage-artifact identities/receipts tracked by coordinator.
- Runtime/generated dependency/cache: `.venv/**`, `.venv-core/**`, `**/__pycache__/**`,
  `*.pyc`, `.mypy_cache/**`, `.ruff_cache/**`, `*.egg-info/**`, `build/**`, `dist/**`.
  Record exclusion names/types and generated build membership evidence separately.
- Prohibited source-local assets: `data/**`, `models/**`, `local_artifacts/**`.
  Do not read their bytes; record that the excluded directory exists, if present.
  Any other discovered model, organizer SDK/catalog, credential or dataset output
  is quarantined from capture and reported as a scope conflict before edits;
  do not copy it into snapshots or silently extend exclusions.

Thus `.gitignore`, configs, Docker files, all application/source/test/script/docs
bytes (including relevant ignored synthetic JSONL fixtures) are included. No
parent/sibling data, models, owner environment or raw-state assets are captured.
No Git exists; unexpected Git/protected structures are inventoried without writes.
Process exclusions cannot conceal product changes under `docs/ai`.

An after snapshot uses the same agreed boundary and a new store. Compare the union
of before/after paths for added/deleted/content/type/mode changes; represent a move
as old deletion plus new addition with byte identities (optionally a derived move
hint), never lose the deleted bytes. Record pre-existing owner files and actual
grant allowlist; any application change outside the grant blocks handoff. Include
all owner changes present at capture. Snapshot infrastructure may be implemented
by a one-off reviewed PowerShell/Python command recorded in implementation evidence,
with exact inclusion/exclusion behavior; do not add a permanent runtime workflow
or extra tracker merely for snapshots.

After Developer self-checks, a fresh independent Reviewer inspects the full
before/after diff, changed tests, contracts and actual evidence. Maximum three
review rounds apply. Reviewer independently rechecks MEDIUM risk and snapshot
coverage, including masks, actual trainer invocation, loop/occurrence safety,
local-only transports, selected SDK and output protection. AI_PASS requires no
blocking findings and adequate actual mandatory software evidence; real-runtime
deferrals are explicit limitations, not claimed verified capabilities.

Before requesting and accepting human signoff, recompute live application identity
and protected/process identities. Any product drift invalidates affected review
and acceptance, requiring review/retest. Process receipt additions are separately
recorded, not silently hashed into a moving app baseline. Accountable project
owner validates behavioral/contract impact, complete diff, actual checks and
residual deferred runtime risk. No new qualified human slot is required for
MEDIUM; escalation to HIGH requires owner plus separate qualified/domain reviewer.

Rollout is local software handoff only; no publication, push, merge, deploy or
competition submission. Preserve the old behavior through facades and explicit
CLI mappings; no data/model migration or automatic regeneration. Rollback uses
sealed before bytes only for paths changed by this work and recorded additions.
Before restoring/removing anything, require current path hash/type to match the
recorded reviewed after state and ensure absolute targets remain under root.
If owner bytes changed since review, stop restoration for that path and report
the conflict; never overwrite it. Restore moved/deleted originals from before,
remove only newly created work files that still match after, verify final hashes
and retain failed evidence/snapshots. This is a documented recovery procedure,
not authorization for automatic destructive rollback in this stage or grant.

MEDIUM is justified by new ordinary offline application behavior across audio,
SDK adapters, local data contracts, training and loop control. Tools simulate
actions and no live financial/service system is connected. No raw-state access,
credential migration, source-local private-data persistence, production release
or irreversible data/schema change is selected. Highest risks are incorrect goal
binding/retries, input/label leakage, loss-mask drift and compatibility. Synthetic
negative/contract checks plus independent review are necessary; learned accuracy,
training success and competition runtime compliance remain later evidence gates.
Discovery of sensitive-data handling beyond these boundaries, external service
routing or hard-to-revert changes triggers reassessment before affected edits.

## 13. DISTINCT future bounded edit-grant proposal — inactive

This is a reviewable grant proposal tied only to **plan.md r1 and its exact final
SHA-256**. It is not granted by this file, plan approval alone, or the resume
message. The coordinator must obtain an explicit human grant after or alongside
`APPROVE architect r1`, recording both decisions separately.

Root: `C:/Users/nktoan/Downloads/LifeMate_2026_Kit_Verified_Coding_Handoff/LifeMate`.
Allow create/edit only the following application paths, preserving owner bytes
with §12 baseline first:

- `pyproject.toml`, `.gitignore`, `README.md`; `Dockerfile`, `.dockerignore`, `predict.sh`.
- Existing `src/lifemate/*.py` files listed in §§1–2; new root files
  `__main__.py`, `workflows.py`, `contracts.py`, `config.py`, `artifacts.py`,
  `provenance.py`, `py.typed`; exact subpackage files shown in §2. No other source
  package or arbitrary recursive refactoring is granted.
- `configs/inference.ollama.json`, `configs/inference.audio.json`,
  `configs/training.lora.json`, `configs/evaluation.json`.
- Existing scripts named in §8 and new `scripts/train_lora.py`, `scripts/predict.py`,
  `scripts/verify_package.py`.
- Existing three test files; new `tests/test_contracts.py`, `test_artifacts.py`,
  `test_data.py`, `test_audio.py`, `test_normalize.py`, `test_context.py`,
  `test_validation.py`, `test_references.py`, `test_goals.py`, `test_loop.py`,
  `test_backends.py`, `test_preparation.py`, `test_training.py`, `test_evaluation.py`,
  `test_asr_metrics.py`, `test_cli.py`, `test_packaging.py`, `test_guides.py` and
  `tests/fixtures/**` containing only authored synthetic fixtures. Add
  `tests/__init__.py` only if test discovery/import behavior needs it.
- New docs listed in §8, plus edit `docs/p0_coverage.md`, `docs/verification.md`
  and `docs/ollama_local.md` for accurate compatibility/current limits; preserve
  historical audit/experiment evidence. No catalog regeneration in source.

Allowed operations: create needed directories/files, edit/refactor bounded files,
retain facade exports; no application deletion, repository/rule mutation or
unrelated owner overwrite. Source movement occurs by create/edit and facade
retention. Build-generated `build/**`, `dist/**`, `src/*.egg-info/**`, caches and
new `.venv-core/**` are permitted generated side effects, not product source.
Permit §11 core/dev environment/install, deterministic unittest and actual SDK
synthetic Session tests, compilation, Ruff/mypy/build, help/static checks and
grant-file-only format fixes. Test temporary synthetic artifacts use OS temp,
never organizer/model input directories. No install/service/model setup beyond
core/dev; package-index network is limited to core/dev package installation.

Separately permit bounded process evidence: create/seal snapshots by §12, Developer
`implementation.md` and Reviewer `review.md` plus revision copies in this work
directory, coordinator-only `progress.md` receipts/identities. These process writes
do not grant changes to approved source/Intent/Spec/Plan or project rules. Record
actual check commands, exit codes, snapshot digests, changed paths, AC/K coverage,
skips/deferrals and findings. Current Architect still may write only this plan.

Exclude organizer SDK/catalog/data/audio/raw states/labels, parent handoff files,
`../local_lifemate_artifacts/**`, existing models/tokenizers/adapters/owner `.venv`,
credentials, `.git`, `.agents`, `.ai-sdlc`, `.codex`, AGENTS.md, other chats/projects
and all external writes. Reading authorized SDK source/catalog and using its
synthetic Session API for software checks is allowed; real-data ToolEnv replay,
freeze/trajectory dataset runs, model-bearing tokenization/loss, ASR/policy jobs,
training, benchmarks, downloads, Docker build/run and actual inference/submission
remain deferred. No auto-evaluation, Git commit, push/merge/deploy/publish or
destructive rollback. Additional paths/operations or material changes require
targeted amended approval/grant before acting.

## 14. Review handoff

The selected design is decision-complete within approved behavior: routine package,
strict-model, JSON config, local adapter and compatibility choices are specified;
no new public vendor, live integration, data migration or rollout is introduced.
Unknown official/model facts remain explicitly deferred evidence, not open product
choices resolved by invention. No application code, tests, dependencies, rules,
ledger, data or snapshots changed in Architecture.

Recommended coordinator action: independently inspect this exact r1/hash and its
36-row AC matrix; present `APPROVE architect r1` / `REVISE architect r1`, and the
distinct bounded grant proposal above. Stop before Developer until both actual
receipts and host permissions are available. Independent Reviewer and final
accountable human acceptance remain required for the implemented exact snapshot.
