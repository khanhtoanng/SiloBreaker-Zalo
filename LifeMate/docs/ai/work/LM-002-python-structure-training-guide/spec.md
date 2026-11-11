# Specification — LifeMate application software and run guides

WORK_ID: LM-002-python-structure-training-guide  
FLOW: FULL  
STAGE: SPEC  
REVISION: r1  
INPUT: approved intent.md r2; source.md r3  
DATE: 2026-11-10 (Asia/Saigon)  
STATUS: READY_FOR_REVIEW  
CLARIFICATION_CHECK: NO_MATERIAL_GAPS — DEC-01, DEC-02 and DEC-03 applied

## Approved basis and scope

The user directly approved **`APPROVE intent r2`**, recorded by the coordinator as
AP-01 in [progress.md](progress.md). This worker independently verified the current
[Intent r2](intent.md) SHA-256:
`d7c8e8ada44f76feaaa074b8f19c575e71610d618038b7ac0327362ba6e6e5a6`.
Its [source r3](source.md) hash is
`ab1e5a069dc9c2379226c0e475f35b9d1992da9416175ec2d2a15e042c5f0205`.

DEC-01 authorizes generic role-guided delegates and the existing human gates.
DEC-02 includes training code and the complete guide. DEC-03 establishes the full
original LifeMate application as the software deliverable, including ASR and
offline packaging, while deferring model/training runtime work. Pydantic and a
clear Python structure are explicit user requirements.

The original [parent intent](../../../../../intent.md),
[parent specification](../../../../../spec.md),
[kit findings](../../../../../KIT_VERIFIED_FINDINGS.md) and
[edge cases](../../../../../SCORING_EDGE_CASES.md) supply product and SDK contracts.
The parent's illustrative dataclasses/layout and optional model/experiment choices
do not override the approved Intent. Later Architecture chooses the concrete
layout, libraries, interfaces and task plan within these behavioral requirements.

The delivered software supports this operator path:

1. Inspect the external authorized kit and prepare frozen train-derived data.
2. Configure locally supplied ASR, policy and optional trained adapter assets.
3. Run latest/history audio or authorized train oracle-text processing through
   the same observation-driven action pipeline and official split SDK.
4. Write the actual submission trace/hash and separate diagnostic artifacts.
5. Prepare trajectories, invoke supervised adapter training, evaluate candidates
   and package the offline application when the operator runs those workflows later.

No stage approval, software test, dry-run or example configuration is evidence of
trained-model quality, official scoring parity or competition release compliance.

## Evidence and execution boundary

- **OBSERVED:** AP-01 approves the full Intent r2, with INT-01–INT-13 and original
  C01–C15 coverage. Existing source has text execution, SDK loading, train replay,
  trajectory preparation, proxy evaluation and local policy adapters. ASR,
  normalization, goal/repetition completion and the trainer require implementation.
- **OBSERVED AS PRIOR DOCUMENTED EVIDENCE:** current local audit documents report
  train and public-test catalogs/SDKs, exact train replay and differing split hash
  behavior. This supersedes the old small-review-ZIP absence of public assets;
  this Spec stage has not rerun those checks.
- **UNKNOWN:** official scoring equivalence, final Docker mounts/output contract,
  numerical resource/release rules, future model quality and target-hardware fit.
  Configurable example settings are not certified organizer rules.
- **DEFERRED:** training-environment setup, package/model setup for training,
  model downloads, real policy/ASR inference, training/loss-forward jobs,
  model benchmarks and model-bearing container/runtime certification.
- **PERMITTED IN LATER BOUNDED IMPLEMENTATION:** static checks and deterministic
  unit/contract/component checks with synthetic inputs, injected model/trainer
  boundaries and, where authorized, the external SDK's synthetic fixture API.
  Heavy dependencies or real models are not prerequisites for core software checks.
  Exact commands and side effects remain subject to the later edit grant.

All acceptance checks below are **specified**, not executed or passed by this
stage. Fixture results establish software behavior for the supplied decisions and
observations; they do not establish that an unrun model understands an utterance.

## Contract rules carried into the acceptance criteria

- The scored row contains only `id`, `tool_calls` and `state_hash`. Each call is
  `{name, arguments}`. Actual values come from the same official sample session.
- The current custom next-action JSON semantics remain CALL, ASK and DONE.
  CALL names one tool and its arguments; ASK names the intended installed target
  and missing parameter names; DONE is internal. ASK is converted to the real
  `sys.ask_missing_info` call with `tool_name` and `params`. One representation is
  used consistently by policy parsing, trajectory targets and training/inference
  conversion; no incompatible native/custom formats are silently mixed.
- Pydantic validates application envelopes/configuration without changing SDK
  authority or stripping catalog extensions. Dynamic tool arguments still require
  the selected tool schema, project semantic preflight and `env.validate`.
- Gold labels are available only to authorized preparation/replay/evaluation
  workflows. A label-free inference representation is passed to policy execution;
  train oracle text is an explicitly selected train-only input mode.
- Outputs, diagnostics, datasets and model/adapter assets are kept outside the
  implementation source root. Organizer inputs and existing model assets are not
  overwritten by output selection. Relative paths resolve against documented roots.
- External inference services and inference-time downloads are prohibited.
  The user-selected Ollama option is a local loopback policy service with cloud
  and remote-backed models rejected; it is not the training engine.

## Acceptance criteria and verification matrix

Each criterion states observable positive, negative or boundary behavior and its
verification. `U` means deterministic unit/contract checks; `I` means controlled
component/integration checks using injected model outputs or synthetic SDK state;
`S` means static/package/document consistency checks. These checks may later run
under the implementation grant. `D` denotes an additional deferred real-runtime
check, which must remain unverified until the operator actually performs it.

### Validated inputs, audio and context

| ID | Intent trace | Required observable behavior | Verification and expected observation |
|---|---|---|---|
| AC-01 | INT-02, INT-05 | Given configuration, sample envelopes, decisions, submissions and training records at their affected boundaries, Pydantic models validate the declared contract before the workflow uses it. Invalid required fields/types/ranges and command-owned unknown configuration fields produce actionable validation errors. Integer tool amounts do not accept bool/string/float through coercion. Valid dynamic catalog annotations and declared extension payloads survive unchanged. | U: valid and malformed records, unknown configuration typo, nested argument payload, boolean/integer boundary and catalog `x-ref`/`x-match`/`x-one-of` roundtrips. Assert rejection or preserved values at the relevant boundary, rather than relying on type annotations alone. |
| AC-02 | INT-01, INT-02, INT-04, INT-06 | Operator help and configuration/preflight validation can be used without loading a model, starting a service, creating a ToolEnv, downloading assets or beginning training. Runtime selection, input/output roots, split and finite positive budgets are explicit. Missing optional runtime dependencies/assets fail clearly when their workflow is requested; they are not silently installed or replaced with a different backend. | U/I/S: inject dependency/model/session factories and assert no calls for help/validation; invalid budgets and unavailable workflow dependencies produce an error and no action trace or training success artifact. |
| AC-03 | INT-05, INT-09, INT-12 | Given the inner organizer kit root or the user's single outer unzip wrapper, select the intended split's manifest, catalog and SDK. Missing selected-split assets and ambiguous wrappers fail explicitly. Never substitute the train catalog/SDK for public/private data, and never enumerate or parse hidden environment state to resolve the root. | U/I: direct/wrapper roots, multiple candidate wrappers, missing public/private catalog/SDK and differing synthetic split packages; selected imports/catalogs agree and unrelated state-file access is rejected by the fixture. K13/K54. |
| AC-04 | INT-05, INT-09, INT-12 | Manifest loading detects malformed JSON, missing/non-string or duplicate IDs and incompatible sample envelopes before those records guide actions. Policy input contains permitted current-sample context/history/transcripts and observations, not label/final-state/future-gold fields. Oracle-text mode accepts authorized train transcripts only and cannot be used as a public/private label or pseudo-label fallback. | U/I: corrupted/duplicate manifests, train oracle input and an input carrying sentinel gold fields. Capture policy requests and assert only the approved inference representation reaches them. No missing sample is silently treated as a valid empty prediction. |
| AC-05 | INT-08, INT-09 | In audio mode, latest user audio and provided earlier user-turn audio are processed locally and attached to the correct chronological turns. Assistant text, prior tool calls/results and latest-request identity are preserved. Train oracle mode bypasses ASR explicitly and enters the same downstream action contract. Original transcripts and their associations remain available separately from normalized text. | U/I: recording ASR fixture with distinguishable history/latest paths and outputs; assert order, turn placement and no history action replay. Compare downstream contracts for equivalent fixture audio/oracle transcripts. D: actual Vietnamese ASR/accents and code-switching quality. |
| AC-06 | INT-05, INT-06, INT-08 | Missing, unreadable or unsupported audio and missing local ASR assets are reported as input/runtime failures, not as successful unsupported requests or invented transcripts. Audio resolution cannot escape the documented authorized audio root or read environment-state files. A failed ASR step cannot trigger an action based on guessed text or silently switch to hidden oracle data. | U/I: absent/corrupt audio, path traversal/out-of-root targets and ASR exceptions. Assert no proposed text is invented, no resulting SDK call is made from the failed transcription, and the diagnostic identifies the failure. |
| AC-07 | INT-05, INT-09, INT-11 | Context compilation preserves sample current time/timezone, location/profile, relevant conversational order and ID-bearing prior tool results. History operations are already applied: they are never executed again. Context budgeting never silently drops required tool schemas or reference-bearing observations to fit; an unresolved overflow is surfaced and prevents a late/unsafe action. | U/I: history-only ID, mixed user/assistant turns, prior write, contextual correction and over-budget prompt. Assert retained evidence, no replayed write and explicit overflow/stop behavior. K12/K22. |
| AC-08 | INT-05, INT-09 | Eligible tools are the current sample's installed-tool/catalog intersection plus the authorized system tool. Schema names, descriptions, kinds, required fields, enums, nested structure, return summaries and reference/matching/alternative annotations remain available to the policy. No global train app list or retrieval shortlist excludes necessary eligible tools, and no similar uninstalled tool is substituted. | U/I: installed/uninstalled tools, unknown app names, public-only tool and malformed installed app/tool association. Capture the registry/policy schemas; only eligible tools survive and all eligible schemas remain represented. K01/K13/K54. |

### Semantics, decisions and stateful execution

| ID | Intent trace | Required observable behavior | Verification and expected observation |
|---|---|---|---|
| AC-09 | INT-09, INT-11 | Temporal/numeric helpers preserve original text, identify supported unambiguous Vietnamese quantities/time expressions and resolve relative time from the sample clock/timezone, not the host clock. Negation and latest explicit self-correction govern the effective request. Ambiguous expressions carry uncertainty rather than an invented amount/date/default. Explicit optional user text is not removed merely because hashing ignores it. | U/I: `500 nghìn` versus `500`, `một triệu rưỡi`, midnight/year rollover, `mai`, timezone boundary, `năm giờ… à không, năm rưỡi` and `đừng đặt xe`. Assert exact supported values, retained original/correction evidence and uncertainty/no guessed write for unresolved cases. Include explicit past/equal/future ride schedules. K32/K35–K40. |
| AC-10 | INT-05, INT-11 | Reference evidence carries value, source and semantic type where available, from explicit user/context/schema literals, history results or current authorized observations. An invented entity ID is not accepted as grounded. Valid literal/history IDs do not force unnecessary reads; zero/multiple lookup results do not authorize guessing the first entity. Known type/collection or restaurant/menu mismatches are handled before a write or surfaced as unresolved. Evidence of provenance is not described as proof of current database existence. | U/I: read-returned ID, history-only ID, explicit literal/schema value, fabricated ID, ambiguous contacts, wrong device type and wrong restaurant/menu. Assert typed evidence and correct permitted read/ASK/block behavior without hidden state. K06/K14–K24/K41/K43. |
| AC-11 | INT-02, INT-05, INT-10 | Parse exactly one CALL/ASK/DONE decision in the selected application protocol. Reject non-JSON, multiple decisions, duplicate JSON keys, nonfinite numbers, unknown kinds/fields, unknown tools and malformed arguments before official execution. Any repair is bounded, remains within the same sample session and preserves the proposed/rejected distinction in diagnostics. Training targets and inference parsing share these semantics. | U/I: valid three decision classes plus adversarial JSON/shape cases and a repaired proposal. Assert no invalid proposal reaches `env.call`, no fake DONE call is logged and repair exhaustion terminates with the real trace intact. K02–K05/K08/K25. |
| AC-12 | INT-05, INT-10, INT-12 | One inference sample creates exactly one official ToolEnv from the selected split. All actual decisions execute through it. A rejection, no-op, ambiguity, timeout or repair never causes a hidden reset/replacement session. Project inference never calls `get_state()` or directly reads simulator files. SDK construction failure cannot be replaced with a fabricated hash. | U/I/S: counted SDK factory, failure/repair paths, forbidden-state-access fixture and selected-split import checks. Assert one session, zero direct state reads and no dummy submission hash. K09–K13. |
| AC-13 | INT-02, INT-05, INT-11, INT-12 | Before each real CALL/ASK, enforce installed scope, the selected schema and semantic preflight, including nested required objects, field names, supported types/enums/ranges, alternatives and reference evidence. Then call official `env.validate` as the final schema/scope guard. A rejected validation does not execute or become an attempted call. Do not claim SDK validation checks x-ref existence or nested required fields it does not enforce. | U/I: nested food items `[{}]`, unknown argument, invalid vehicle/mode, integer/bool amount, valid one-of recipient and SDK-denied call. Assert project/SDK checks are distinguishable, validation precedes execution and rejected proposals leave the log unchanged. K01–K08/K25/K37/K43. |
| AC-14 | INT-05, INT-10, INT-12 | Consume the actual returned observation after every call. Distinguish schema rejection, business no-op, read data, meta wait, supported tool-specific successful writes and unknown outcomes. `ok:true,done:false` never fulfills the requested write; absence of `done` alone does not make a known successful write fail. Unknown/exceptional outcomes do not prove rollback or permit a blind repeated mutation. | U/I: insufficient funds, nonexistent x-ref, empty read, supported write result without `done`, malformed/uncertain result and accidental failed executed call. Assert truthful classifications, goal evidence and preserved attempted calls. K06/K09/K18/K19/K23. |
| AC-15 | INT-09, INT-10, INT-12 | The runtime represents pending goals, dependencies, blocked/completed status and supporting observations. A first read or one successful independent goal cannot by itself complete every represented goal. Conditional branches use actual observations; unmet conditions do not execute their writes. A bounded completion check can request reconsideration of premature DONE without inventing an action or marking the goal successful. Independent completed work is retained when another goal becomes blocked or requires ASK. | U/I: read→write, two independent goals, dependent second goal, premature DONE with pending evidence, and rain/no-rain observations. Assert supported goals are completed or explicitly blocked/clarified, correct branch selection and no fabricated supporting observations. K14/K28/K29/K34; US01/US02/US06. D: learned decomposition and conditional accuracy. |
| AC-16 | INT-02, INT-05, INT-10 | Missing information leads to an appropriate available read or real ASK when unresolved. ASK names an installed intended target and real missing parameter names, then executes `sys.ask_missing_info` with both `tool_name` and nonempty string-array `params`; it ends the sample turn. It may follow completed independent actions, whose calls remain in the trace. An invented target/parameter is rejected before execution. | U/I: ambiguous lookup, missing vehicle/amount, invalid target/parameter and success followed by ASK. Assert final meta call/shape, no subsequent calls and unchanged prior trace. Do not enforce a blanket read when permitted history already resolves the target. K20/K25/K26/K28/K33/K37. |
| AC-17 | INT-05, INT-10, INT-12 | DONE is internal and produces no official call. A controlled fully unsupported or withdrawn latest request produces no unintended action and retains the SDK's actual unchanged hash. When another independent action was legitimately executed, later cancellation/unsupported handling does not erase it. Input/runtime failures are diagnosed separately from successful no-action completion. | U/I: unsupported installed set, latest explicit cancellation/correction, already-applied history and partial supported request. Assert correct controlled trace and distinct failure/completion reasons. Gold-specific no-action conventions require later authorized validation rather than a universal heuristic. K27/K32/K34. |
| AC-18 | INT-05, INT-10 | A write already fulfilled for a represented goal/occurrence is not repeated merely to check success. An uncertain or possibly partial outcome cannot trigger a blind retry. A proven non-effect may support bounded recovery only from available evidence. Two explicitly distinct repeated requested occurrences remain representable and executable; the runtime does not globally deduplicate equal argument dictionaries. | U/I: successful-send retry, uncertain transfer/order, no-op followed by a safe lookup/correction, and two intended identical reminders/payments with distinct goal occurrences. Assert no accidental duplicate, no hidden reset and preservation of intentional repeats. K18/K30/K31. |
| AC-19 | INT-06, INT-10, INT-12 | Configured sample/decision/repair/generation budgets bound processing. Sample elapsed timing includes sample SDK creation, ASR, context/decision/tool work and serialization accounting. Check available budget before a new decision and before execution; an over-deadline model response cannot authorize a new call. Existing calls/hash are retained on timeout/cap. A budget permitting six calls plus terminal DONE can process that controlled trajectory. Configured limits and non-preemptible runtime limits are reported honestly. | U/I: injected clock/late policy, ASR deadline, cap/repair exhaustion and six-call sequence. Assert explicit stop reason, unchanged real trace after cutoff and no hard-latency certification from fixtures. D: end-to-end p50/p95/p99/max and actual hardware timing. |

### Submissions, diagnostics, preparation and learning

| ID | Intent trace | Required observable behavior | Verification and expected observation |
|---|---|---|---|
| AC-20 | INT-05, INT-12 | Submission values are copied from the actual session's `get_tool_calls()` and `get_state_hash()`, including all failed executed attempts and their order. Final selected-manifest output is UTF-8 JSONL with exactly one unique `id` per selected sample in manifest order, an array of `{name,arguments}` calls and the SDK hash, without diagnostic fields. Unknown/missing/duplicate/extra IDs, malformed rows or invalid field/hash shape fail integrity checks. | U/I: getter/log fidelity, failed attempt plus correct call, Unicode content and complete/missing/extra/duplicate/reordered rows. Assert byte/JSON roundtrip and no reconstruction from model plans. Separate hash equality from correctness of hash-excluded text/read calls. K09–K11/K45–K48/K53. |
| AC-21 | INT-06, INT-12 | Fatal manifest/SDK/asset errors do not produce a fabricated complete submission. Incremental completed-sample checkpoints, if present, identify their selected IDs and incomplete/interrupted status; they cannot silently satisfy final completeness or resume/reset a partly executed environment. A complete run is marked complete only after final integrity checks for its declared selection. | U/I: failure after one completed sample, interrupted/partial output, missing SDK state through the sanctioned API and final count mismatch. Assert usable diagnostics, truthful completion status and no absent row treated as `[]`. K11/K53. |
| AC-22 | INT-06, INT-10, INT-12 | Separate diagnostics identify input mode/split, selected sample/fold, model/config/code/data revisions where available, seeds/decoding/budgets, proposed versus executed actions, validation/recovery reasons, actual observations and stop/outcome status. Timing records distinguish ASR, model, tools and total accounting where measured. Reports support the original error taxonomy and do not persist raw simulator snapshots, gold targets in inference prompts, credentials or secret-bearing transport configuration. | U/I/S: injected successful/failing run, model timeout and sentinel protected fields. Assert traceable per-sample records, no scored-row pollution, available-versus-unmeasured metrics distinguished and protected data not emitted. |
| AC-23 | INT-05, INT-06, INT-12 | Standalone authorized train gold replay creates one fresh train session per scenario, executes ordered gold calls, compares actual observations and changed-app final state to labels through permitted SDK APIs, and obtains reference hashes through the SDK. Mismatches/errors are explicit per scenario; labels/reference hashes never enter inference decisions. Raw state files and copied hash algorithms are not used. | U/I/S: synthetic train replay fixtures with exact and mismatching observations/state/trace, zero-call and ASK trajectories. Assert diagnostics and reference fingerprints. Existing historical replay is not a new run. D: rerun all authorized real train scenarios under a later execution scope. |
| AC-24 | INT-03, INT-05, INT-12 | Freeze partitions by original train scenario before trajectory expansion; retain source fingerprint, seed and IDs. Fit/validation are disjoint and cover their declared source selection without duplicate scenario membership. A separate configured leave-app-out fold excludes its held-out scenarios from fit. Changed manifests, foreign IDs, overlap, mismatched selection or test-derived training data fail rather than silently changing the fold. | U/I: reordered same-source records, fingerprint drift, overlap/foreign ID, multi-step scenario and app-out fixtures. Assert reproducibility and no scenario leakage across either selected fold. |
| AC-25 | INT-03, INT-05 | Training preparation uses authorized train records and real preceding gold-replay observations when the operator runs it later. Every row has scenario/partition/step provenance, eligible schemas and only the observation prefix available before its single next action. It produces CALL/ASK targets and a terminal DONE, including immediate DONE for zero calls. Replay drift or malformed call/result alignment fails the preparation run. | U/I: READ→WRITE, ASK, empty-gold, later-action and drifting replay fixtures. Assert consecutive prefixes, one target per step, terminal output, correct partition and no future-gold observation leakage. |
| AC-26 | INT-02, INT-03, INT-05 | Training conversion produces a coherent serialization compatible with the selected local tokenizer/template and inference action protocol. The supervised loss target contains only the desired assistant action/completion; system/user text, tool observations and previous actions are excluded. Oversized/empty-target/malformed examples are rejected or explicitly reported without silently truncating away required tools/history/targets. | U/I/S: deterministic tokenizer/collator fixtures for READ→WRITE, ASK and DONE; inspect labels/masks and roundtrip decisions. Assert at least one intended target token and no context token in loss. D: actual selected-tokenizer roundtrip and model forward/loss smoke when the operator sets up training later. |
| AC-27 | INT-02, INT-03, INT-04 | An implemented training entrypoint accepts validated local training configuration, selected prepared fit/validation artifacts and local base-model/tokenizer assets; checks data identity/partitions, paths, required dependencies and supported options before training. It invokes real supervised LoRA/adapter-training behavior when explicitly run later, rather than returning a placeholder success. Validation/help/dry-run behavior cannot start training or download/load weights. Invalid or unavailable prerequisites fail with useful instructions. | U/I/S: inject the training runtime and assert validated fit/eval inputs/options, configuration-only no-op behavior, missing dependency/model paths and exception propagation; inspect the production training integration for actual adapter-training invocation. D: real local training run. No trained adapter is claimed by the injected test. |
| AC-28 | INT-03, INT-04, INT-06 | Training configuration and outputs carry base-model/tokenizer/template/adapter identity, relevant optimization/seed/context settings, data/fold fingerprints and output locations. Saved adapters/checkpoints are discoverable through the run guide and can be selected for the supported downstream inference path without a different action protocol. Fit failure/interruption is not reported as successful completed training. Ollama is described as a local inference option, not the LoRA trainer; any later conversion/import path is explicitly documented if supplied. | U/I/S: injected trainer save/fail behavior and inference adapter selection/configuration fixtures. Assert recorded provenance, truthful status, existing output paths and consistent action contract. D: actual save/load/quality verification with trained assets. |
| AC-29 | INT-06, INT-12 | Evaluation validates prediction completeness against the exact frozen selection and compares calls and replay-derived state hashes independently. The existing local approximate scorer remains visibly PROXY with its matching/fuzzy/argument/empty/hash-gate choices recorded; maximum one-to-one matching retains duplicate multiplicity and excess reads. Official parity is not inferred from SDK/schema validation, matching hashes or a gold identity fixture. Reports support first/later/whole-trajectory, ASK/empty, missing/extra calls and paired per-sample regression comparison where inputs exist. | U/I: empty/nonempty, wrong hash, differing text with equal hash, duplicate/unordered calls, greedy-matching collision, extra read, fuzzy boundary, missing prediction and mismatched replay fingerprint. Assert explicit score kind/assumptions and honest unavailable metrics. D: official scorer parity and model/fold scoring. |
| AC-30 | INT-06, INT-08, INT-11, INT-12 | ASR evaluation software pairs authorized reference transcripts and actual-ASR outputs by the same frozen scenario IDs and policy configuration, and can report WER/CER, critical-slot differences and downstream call/state/runtime deltas. Missing/misaligned pairs and differing comparison configurations are surfaced. Metric computation from supplied fixtures does not launch ASR or claim actual dialect/model accuracy. | U/I: paired transcript/prediction fixtures containing negation, phone digits, amounts, times, names and corrections; missing pair/config mismatch. Assert correct pairing, metric denominators and explicitly supplied-versus-measured provenance. D: real paired ASR/oracle experiment. K44. |

### Local adapters, packaging, guides and engineering delivery

| ID | Intent trace | Required observable behavior | Verification and expected observation |
|---|---|---|---|
| AC-31 | INT-04, INT-05, INT-06, INT-13 | Offline packaging and operator entrypoint code can run the complete selected-split audio/text pipeline with locally supplied policy/adapter/ASR and external organizer assets when invoked later. Startup does not fetch weights or call external inference services. Input/output/model paths, supported backend prerequisites and reproducibility/verification instructions are explicit. Missing assets fail clearly; unknown official mounts/resources are labeled unverified configurable operator settings, not certified defaults. | S/I: inspect packaging/entrypoint/dependency/config consistency and use injected local runtime boundary to check split/path/argument forwarding and missing-asset failures. Ensure no organizer/model assets are committed or copied into source. D: actual image build, network-disabled model-bearing container, manifest/latency/memory/parameter and official release validation. |
| AC-32 | INT-01, INT-03, INT-04, INT-06, INT-13 | Complete guides provide the operator's later steps for prerequisites and reviewed local assets, safe external kit layout, core/optional environment setup, configuration validation, audit/replay/frozen folds, trajectories, training and adapter outputs, oracle/audio inference, evaluation, submissions and offline packaging. Commands/config names/outputs match delivered code and distinguish PowerShell host steps from any different supported training/container platform. Troubleshooting covers unavailable dependencies/assets/hardware, data drift, invalid configuration, context/budget failures, interruptions and unverified official rules. Instructions and examples are not presented as executed training evidence. | S/U: command/help/config/guide consistency checks with no models or installers; review a complete operator path against implemented entrypoints and outputs. D: operator performs the documented model/training/container workflows on suitable hardware. |
| AC-33 | INT-01, INT-02, INT-04 | The implementation has clear responsibilities, documented conventions and typed public workflow/contracts, with Pydantic used in executed validation paths. Application imports/help do not start jobs. Dependency boundaries keep heavy optional model/training packages out of unrelated core checks. Refactoring preserves the documented workflow meanings; any changed invocation has an explicit migration mapping in the approved design and guides, not a silent semantic change. Focused tests verify behavior and affected consumers rather than only mirroring implementation. | S/U/I: independent representative workflow trace, import/help side-effect fixtures, lint/type/format checks chosen by Architecture, validated-model integration and documented-command/migration checks. Exact layout and tooling are later design choices. |
| AC-34 | INT-06, INT-07 | Implementation and review evidence covers the complete changed snapshot, approved criteria and actual commands/exit codes. Synthetic/injected, external SDK, actual-model and official evidence are distinguished. Deferred checks and unresolved official facts remain NOT RUN/NOT VERIFIED/UNKNOWN. No stage approval, edit grant, independent AI review or human final acceptance is invented; no model/setup job is launched merely to complete this work item. | S: review evidence and recorded receipts against the actual artifacts/change identity and allowed operations. An immutable before/after application baseline and plan-bound edit grant are established in later approved stages; this Spec creates neither. |
| AC-35 | INT-04, INT-05, INT-06, INT-09, INT-13 | The selected local policy path uses locally available model assets and deterministic configured decoding. The existing Ollama option remains local-only: endpoint origins are loopback, redirects/proxies cannot forward sample data externally, cloud/remote-backed models are rejected, and inference never pulls a missing model. Backend timeout/malformed/incomplete responses cannot become executed tool calls or fake successful decisions. Equivalent supported backends expose the same application decision semantics. | U/I/S: transport/backend fixtures for loopback versus remote origin, redirect, cloud tag, missing model, JSON response, deadline and optional backend absence. Assert no external/downloading route and no SDK action from invalid/late output. D: actual local backend/model compatibility and speed. |
| AC-36 | INT-04, INT-05, INT-06, INT-13 | Dataset-derived artifacts, diagnostic files and training/model outputs resolve outside source and cannot overwrite organizer inputs or supplied model assets. Output provenance and completeness are explicit; unsuccessful workflows cannot leave a partial file labeled a complete result. Setup/download instructions are separate operator actions rather than implicit import, validation, inference or training-preparation side effects. | U/I/S: source-root/output/input collision and normalized-path fixtures, partial writer/trainer failures and inspection of package/guide paths. Assert refusal/protected inputs unchanged and truthful output status. |

## Intent and capability traceability

All approved outcomes have acceptance coverage; each listed criterion has its
verification and expected observation in the matrix above.

| Approved outcome | Acceptance coverage |
|---|---|
| INT-01 — Maintainable full application | AC-02, AC-32, AC-33 |
| INT-02 — Pydantic contracts | AC-01, AC-02, AC-11, AC-13, AC-26, AC-27, AC-33 |
| INT-03 — Adaptation software | AC-24, AC-25, AC-26, AC-27, AC-28, AC-32 |
| INT-04 — Complete run guides | AC-02, AC-27, AC-28, AC-31, AC-32, AC-33, AC-35, AC-36 |
| INT-05 — SDK/data boundaries | AC-01, AC-03, AC-04, AC-06, AC-07, AC-08, AC-10–AC-14, AC-16–AC-18, AC-20, AC-23–AC-25, AC-26, AC-31, AC-35, AC-36 |
| INT-06 — Truthful deferred verification | AC-02, AC-06, AC-19, AC-21–AC-23, AC-28–AC-32, AC-34–AC-36 |
| INT-07 — SDLC and review | AC-34 |
| INT-08 — Offline latest/history ASR | AC-05, AC-06, AC-30 |
| INT-09 — Context and eligible capabilities | AC-03, AC-04, AC-05, AC-07, AC-08, AC-09, AC-15, AC-35 |
| INT-10 — Goal/conditional next actions | AC-11, AC-12, AC-14–AC-19, AC-22 |
| INT-11 — Grounded faithful arguments | AC-07, AC-09, AC-10, AC-13, AC-30 |
| INT-12 — Submission/replay/evaluation | AC-03, AC-04, AC-12–AC-15, AC-17, AC-19–AC-24, AC-29, AC-30 |
| INT-13 — Offline packaging/entrypoints | AC-31, AC-32, AC-35, AC-36 |

| Original parent capability | Acceptance coverage | Parent specification basis |
|---|---|---|
| C01 — Speech recognition | AC-05, AC-06, AC-30 | §3; §5.1 |
| C02 — Context/history | AC-04, AC-05, AC-07, AC-09 | §2; §3; §5.1/§5.2 |
| C03 — Runtime capability discovery | AC-03, AC-08 | §2.1; §3; §5.3; §12.5 |
| C04 — Multi-intent goals | AC-15, AC-18 | §4; §5.4 |
| C05 — Iterative next action | AC-11, AC-12, AC-14, AC-15, AC-19 | §2.3; §4 |
| C06 — Argument/reference grounding | AC-10, AC-13 | §2.2; §5.2/§5.3; §12.1 |
| C07 — Temporal/numeric interpretation | AC-09, AC-30 | §3; §5.2 |
| C08 — Validation/execution | AC-11–AC-14 | §3; §4; §12.1/§12.2 |
| C09 — Missing information | AC-10, AC-16 | §2.3; §4; §12.4 |
| C10 — No action | AC-17, AC-20, AC-29 | §4; §7.1; §8 |
| C11 — Stopping/recovery | AC-14–AC-19, AC-21 | §4; §5.4/§5.5; §12.2 |
| C12 — Exact submissions | AC-20, AC-21 | §2.1; §3; §4; §8 |
| C13 — Reproducible validation | AC-22–AC-24, AC-29, AC-30 | §6.1; §7; §8 |
| C14 — Model adaptation | AC-24–AC-28 | §6.1–§6.4; §8 |
| C15 — Offline packaging | AC-02, AC-31, AC-32, AC-35, AC-36 | §3; §9–§11 |

## Original edge-case coverage and evidence levels

Architecture and implementation retain traceability to all K01–K54. A controlled
fixture for a POLICY case establishes the specified application response given
the fixture evidence, not an official hidden-gold convention. SDK contract checks
must use self-generated state through the SDK fixture API or separately authorized
train replay; project code never reads raw environment files. The original P0
matrix rows and its pre-training priority gate receive explicit checks before any
later training run; remaining cases remain visible rather than silently passed.

| Edge cases | Relevant acceptance coverage |
|---|---|
| K01–K13 | AC-03, AC-04, AC-07, AC-08, AC-11–AC-14, AC-20 |
| K14–K19 | AC-09, AC-10, AC-13–AC-16, AC-18 |
| K20–K24 | AC-07, AC-10, AC-14–AC-16 |
| K25–K34 | AC-09, AC-11, AC-15–AC-18 |
| K35–K43 | AC-09, AC-10, AC-13, AC-14, AC-16 |
| K44 | AC-05, AC-09, AC-30 |
| K45–K52 | AC-20, AC-23, AC-29 |
| K53 | AC-04, AC-20, AC-21 |
| K54 | AC-03, AC-08, AC-35 |

SDK hash behavior is split-specific. Tests use each selected SDK's getter/function
on synthetic fixture states where needed, never a project-owned state hash port.
Differing text or read-only app queries can share a state hash; that does not
remove the need to test call arguments and the actual call trace.

## Compatibility, quality and verification delivery

- Preserve the existing documented preparation, replay, prediction, evaluation,
  validation and local Ollama workflow meanings. Add missing full-app workflows;
  concrete command/module reorganization and explicit migration mappings belong
  to the approved Architecture, with guide and consumer checks under AC-33.
- Maintain selected-split behavior and exact scored submission semantics through
  Pydantic/refactoring. Rejecting an invalid application record must not be
  misreported as an SDK-executed rejection or silently mutate user values.
- Keep original and normalized transcription evidence, output diagnostics and
  training provenance understandable without embedding implementation-only
  records into the scored submission.
- Require deterministic software checks for data/contract and control-flow risks;
  no learned semantic accuracy threshold, speed guarantee, score increase or
  official model/resource rule is invented for this code-and-guides delivery.
- Provide later-run procedures for real tokenizer/model/ASR/adapter behavior,
  full frozen-fold evaluation, regression slices, repeated-run stability,
  network-disabled packaging, resource totals and official validator/scorer checks.
  Those results remain deferred until actually run on reviewed local assets.

Tentative risk is **MEDIUM**, pending Architecture confirmation and independent
Reviewer reassessment of the concrete changes. Existing owner files and rules
remain protected. No immutable application before/after snapshot or application
edit grant is established here. This stage changes only this `spec.md` artifact.

The coordinator requests human approval of this exact Spec revision before
Architecture. A later approved plan and separate bounded edit grant are required
before application implementation. No automatic SDLC evaluation, install, model
run, training, publish, merge or deployment is implied by this document.
