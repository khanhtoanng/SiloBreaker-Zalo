# Independent review — LifeMate application, repair revision r2

WORK_ID: LM-002-python-structure-training-guide  
STAGE: REVIEWER  
REVIEW_ROUND: 2 of maximum 3  
REVISION: r2  
INPUT_REVISION: implementation.md r2 / READY_FOR_AI_REVIEW  
CLARIFICATION_CHECK: NO_MATERIAL_GAPS — DEC-01, DEC-02 and DEC-03 applied  
RISK_TIER: MEDIUM  
RECOMMENDATION: CHANGES_REQUESTED  
DATE: 2026-11-10 (Asia/Saigon)

F-02 and F-03 are independently CLOSED. The original four normalization reproductions
are repaired, but additional supported temporal-correction combinations reproduce
confidently incorrect evidence, so stable F-01 remains OPEN / MEDIUM / VERIFIED.
The full unchanged core suite passes: 180 tests, 179 passed and one existing Windows
symlink-privilege skip. That does not resolve the independently reproduced defect.
No new product choice is needed. No model, real-data ToolEnv, training, ASR, replay,
container or external service job ran in this review.

## Authority, independence and risk

This fresh generic role-guided Reviewer read the effective AGENTS.md,
.ai-sdlc/COMMON_RULES.md, embedded .codex/agents/reviewer.toml, actual coordinator
handoff, source/Intent/Spec/Plan/progress/implementation and preserved review r1.
The approved criteria, actual repaired files/tests, sealed original and r1/r2 bytes,
full change inventory, surrounding consumers and relevant original parent
product/SDK/edge-case evidence were assessed. Prior full independent r1 evidence
is preserved and used only after independently proving the other application bytes
unchanged; it does not substitute for inspecting the repairs and their consumers.
DEC-01 explicitly permits this real generic delegation. No named native selection,
Developer identity reuse or subdelegation is claimed.

The actual coordinator handoff supplies these user approval receipts. Their bound
artifact hashes were independently recalculated by review.r2.audit.py:

| Receipt/input | Exact SHA-256 |
|---|---|
| AP-01 `APPROVE intent r2` | `d7c8e8ada44f76feaaa074b8f19c575e71610d618038b7ac0327362ba6e6e5a6` |
| AP-02 `APPROVE spec r1` | `84f6a227878423ec886f3575b523f6b3e7aa5b7d0e8e1ba7d1da1aa4c9ad12a0` |
| AP-03 `APPROVE architect r1` | `722c2d624027dc17e4697f4648be5f6f3abe7a20e4087239807582c1059905ba` |
| source.md r3 / DEC-01–03 | `ab1e5a069dc9c2379226c0e475f35b9d1992da9416175ec2d2a15e042c5f0205` |
| implementation.md r2 | `2d5559db285ce8604a92d416fcb47f5c7a1e5de37a18a66868b425c1f8d31ee9` |
| Preserved complete independent review.r1.md | `5a6c95a879406667aa89b7e37d509cb8c8ac0e186ae0d8cdf3f74f2852042e90` |

Separate EG-01 receipt, verbatim: **GRANT implementation under plan r1 §13,
including snapshot capture under §12 and core/dev setup and checks under §11,
retaining all listed exclusions.** This remains the full C01–C15 application
code/configuration/guide delivery, including real future training code. DEC-02/03
defer actual model/training setup and execution, without deleting their software
components from scope. Historical stage READY_FOR_REVIEW/NONE headings do not
override the actual revision-bound approval/grant receipts. The coordinator
confirmed the repair classes and affected consumers are within unchanged EG-01.

All shell commands explicitly selected
`C:/Users/nktoan/Downloads/LifeMate_2026_Kit_Verified_Coding_Handoff/LifeMate`
and `C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe`. Writes were limited
to review.md and review.r2.* evidence. No application, tests, approved stages,
progress.md, rules, previous review/implementation evidence or sealed store changed.
OS-temp fixtures were authored synthetic inputs only. No install, model download,
network service, Git operation, publication, credential access or raw-state read.

MEDIUM remains appropriate independently: this is ordinary offline application
behavior against a simulated SDK, without live financial/service integration or
irreversible deployment/migration. Goal binding, references/labels, repeated writes,
normalization, output ownership and training-mask integrity are material risks.
No discovered change expands the integration or sensitivity to HIGH. Synthetic
enforcement tests do not prove learned semantic accuracy or hardware fitness.

## Exact complete reviewed snapshot

No Git baseline is claimed. The independent [audit](review.r2.audit.json), produced
by [review.r2.audit.py](review.r2.audit.py), recalculated canonical manifest identities,
every stored file length/hash, live application metadata/bytes, protected baseline
bytes, original and r1 test assertion retention, K references, and archive bytes.
Its exit was 0. It uses the inspected agreed inventory helper for the application
boundary and independently calculates/compares content digests and identities.

| Bound identity | Independently verified value |
|---|---|
| Original BEFORE | `snapshots/before-20261110-ap03-eg01-02/application/` |
| BEFORE application | `c38a7def852406a3411f9c9dc5ee1e1b6e95cadf8b9e73d3452cf75b95608a24` |
| BEFORE manifest SHA | `b5525c293e51ddd65d20b0b720bc49465d1d35d9b004d8bade69fe0294822249` |
| Preserved AFTER r1 application | `e2db119b38994814c0689d339b1e9a334060db65678c35a949cd5af1038e6ea0` |
| AFTER r1 manifest SHA | `f618dd62ec7ff529fb9a6d2a62f4a6ac0670674aef2ac9daf2c27766ab5808ac` |
| Current AFTER | `snapshots/after-20261110-r2/application/` |
| AFTER r2 and exact live application | **`79ba6a2e59ffba48035c2c03c549eb3ad820a5f04ef5a6f91a8b0b0b6a4a4b07`** |
| AFTER r2 manifest SHA | `50e5282f03607e271b06169dba5fa5ea8cc6f25dce15c3ba5599b3b805de80f2` |
| Full original→r2 diff SHA | `037d468dc621c64f375fd533a28ced062123083c742cc302c1e9af754c991ca6` |
| Repair r1→r2 diff SHA | `104215fe280230d065727d0b39fa70d6d5a6d30fac1bd40438683d2b6804ea8b` |

BEFORE contains 34 files/39 records; each AFTER contains 102 files/113 records.
Original→r2 changes 97 files (68 added, 29 modified), with zero deletions; six added
directories make 103 changed records. The complete 97-file inventory is
`changed_files` in the independent audit. Exact before/current path/type/byte records
are in implementation-diff-r2.json, and the full 9558-line patch is retained in
implementation-full-diff-r2.patch. The 850-line repair patch and live repaired files
were inspected with surrounding consumers, rather than accepting the report alone.

Exactly nine application files differ from independently reviewed r1:

- docs/operator_guide.md
- scripts/check_evaluator.py
- scripts/check_trajectories.py
- scripts/smoke_runtime.py
- src/lifemate/metrics/asr.py
- src/lifemate/runtime/normalize.py
- tests/test_asr_metrics.py
- tests/test_cli.py
- tests/test_normalize.py

The complete resulting scope assessed includes contracts/configs; data/SDK selection;
runtime context/normalization/references/validation/goals/outcomes/loop; local policy
and ASR boundaries; train replay/trajectories/serialization/collator/trainer; proxy
and paired metrics; artifacts/provenance/submission; CLI/workflows and compatibility
facades; scripts, all test modules, example configs, operator/training/migration/
offline/architecture/edge guides, packaging/build/dependency configuration. Relevant
critical consumers were reread directly, including the real smoke main, normalized
planner/action payload and ASR metrics, guarded utility writers, same-session loop,
label-free projection, goal/reference enforcement and actual trainer invocation.
Unchanged r1 paths and full original baseline remain part of this review identity.

All three stored protected inventories and their file bytes independently verify.
Original protected identity is
`f6515d78f11b848a276bf5651e89daa3ac84f443c624c158fc21c5694d4a88cf`;
r1 is `924a213753e66a24eb988d97611bf450686718ccad88fd26f04e6d13f6914284`;
r2 is `660bf6cd9c459c01daac7c895d366c2ddcea4694e7a92935d74b5095046bc4b5`,
with r2 manifest SHA
`58174304155be1074ff3c7c897d42f7ec901e7f8259d2ac7d68bc8669a7d2ad1`.
The only changed pre-existing protected file is coordinator-owned progress.md;
all other original protected/approved bytes match live. New authorized process
receipts and review evidence are separate from application identity. Snapshot output
is excluded from its own inputs. Coordinator's complete AFTER r2 audit records
out_of_grant=[] and protected_violations=[]; independent full path/baseline checks
agree with the approved file/operation scope. No application drift was found.

## Actual independent commands and evidence

All child Python processes used existing `.venv-core/Scripts/python.exe` (Python
3.12.0), `PYTHONDONTWRITEBYTECODE=1` and
`PIP_CACHE_DIR=<root>/.venv-core/pip-cache`. Commands below show arguments following
that interpreter; cwd/shell are the explicit values above.

| Actual independent command/check | Exit | Observed result |
|---|---:|---|
| `-m unittest discover -s tests -v`, sandbox | 1 | 180 tests, 12 OS-temp atomic-rename errors, three skips. Host restriction, not PASS; [raw log](review.r2.unittest.log). |
| Identical suite, actual authorized permission escalation | 0 | **180 tests, 179 PASS, one existing symlink-privilege SKIP**, no failures/errors. Actual utility/artifact Windows junctions and all 18 external SDK synthetic Session checks PASS; [raw log](review.r2.unittest-escalated.log). |
| `-m ruff check src scripts tests` | 0 | PASS; [log](review.r2.ruff.log). |
| `-m ruff format --check src scripts tests` | 0 | PASS, 76 files already formatted; [log](review.r2.format.log). |
| `-m mypy src/lifemate` | 0 | PASS, 46 source files; [log](review.r2.mypy.log). |
| `docs/ai/work/LM-002-python-structure-training-guide/review.r2.audit.py` | 0 | PASS exact complete original/r1/r2 stores, live identity, protected originals, all prior assertions, K references and owned archive bytes; [JSON](review.r2.audit.json). |
| Unchanged `review.r1.probes.py`, output redirected to new r2 evidence | 0 | Original four normalization cases now repaired; actual ReadOnce→infer reaches DONE with one read; protected utility child exits 1 and creates no forbidden output; [results](review.r2.original-probes.json). |
| `docs/ai/work/LM-002-python-structure-training-guide/review.r2.probes.py` | 0 | Successful **defect reproduction**, not product PASS. Nine adjacent temporal cases, actual infer planner payload, downstream supplied-ASR comparison and evening case; [source](review.r2.probes.py), [results](review.r2.probes.json). |

The sandbox failures were preserved. The identical already-authorized suite passed
using the actual permission API; no atomic writer was substituted and no assertion
was weakened. One remaining skip is Windows inability to create an unprivileged
symlink. Separate real generated junction checks passed, including utility kit and
sidecar aliases. No actual SDK skip remains in the successful run.

Developer complete-release/summary.json records 16 actual commands, all exit 0:
pip check, unittest, compileall, Ruff check/format, mypy, build --no-isolation and
nine help surfaces. Summary and relevant raw pip/build/static/help evidence were
inspected. Those are inspected Developer results, not additional independent
executions. Build/compile/help were not unnecessarily repeated after independent
archive identity and source-byte verification. A convenience evidence-summary read
initially assumed UTF-16 and failed to decode; reading the actual UTF-8 JSON then
succeeded. That read failure is unrelated to application verification.

Wheel `dist/lifemate-0.1.0-py3-none-any.whl` hashes to
`9cb513cc7059f58284d15fa269ac392c4bd1246738681fac50432e21a685ff7b`;
sdist `dist/lifemate-0.1.0.tar.gz` hashes to
`6d4e9b7684fae7633619771467b7d18e367bb8bfbd5ba077140315f3819ed2bd`.
Independent zipfile/tarfile inspection confirms all 47 wheel-owned package files
and all 100 sdist-owned files byte-match live source. Full member lists remain in
review.r2.audit.json. No unexpected wheel package or source-local organizer/model/
dataset/environment/process-evidence payload is present. These packages also carry
the normalization defect; a successful build is not behavioral acceptance.

## Test integrity and K-case coverage

Independent AST comparison confirms all original 68 test methods/137 assertion-call
expressions survive, and every r1 test method and assertion expression survives in
r2. Original per-file counts remain test_runtime 42 methods/76 assertions,
test_ollama 13/28, test_sdk_contract 13/33. All original tests remain in the passing
suite. New tests extend the actual utility consumers; there is no removed assertion,
new blanket skip, mock of the production atomic writer, dependency relaxation or
runtime fallback. Prior/planner-capable controlled fixtures remain controlled proof.

All K01–K54 rows appear exactly once in docs/edge_case_coverage.md; all 63 unique
executable references resolve to actual test methods and pass at their declared
CORE/SDK/POLICY/PROXY evidence levels. No universal semantic or official scorer
claim follows. Relevant original P0 gate is unchanged: K01–K13, K18, K25–K30,
K35–K38, K45–K48, K53. K32/K40 temporal-correction combinations are still incomplete
under F-01, affecting supplied critical-slot K44 metrics. The new proof includes
tomorrow/next-week, midnight/year rollover, relative duration, explicit date and
chained correction combinations, rather than only the original four strings.

## Full acceptance trace

PASS means adequate software evidence within the accepted current scope. It never
means a deferred model/official check passed. Named tests reside under tests/;
implementation paths are relative to src/lifemate/ except scripts/packaging/docs.
The complete suite was independently rerun; detailed unchanged r1 proof remains
preserved and byte-bound. AC-34 final owner acceptance is pending.

| AC | Implementation → concrete test/evidence | Current software result |
|---|---|---|
| AC-01 | contracts/config and runtime/validation → ContractsTests strict budgets/extensions/single JSON, SchemaTests strict integer/range, ValidationTests nested fields | PASS |
| AC-02 | CLI/config, lazy adapters/trainer → BackendTests.test_imports_do_not_load_heavy_libraries; TrainingTests.test_dry_run_no_heavy_runtime_or_output; CliTests help/forwarding | PASS |
| AC-03 | data/kit, adapters/sdk and workflows.bundle → DataTests wrapper resolution; DataBoundaryTests selected-bundle completeness; actual SDK distinct split imports | PASS |
| AC-04 | data/kit inference projection/read_jsonl, InferenceSample → DataBoundaryTests train-oracle/test isolation; RuntimeTests label guard; duplicate/malformed IDs | PASS |
| AC-05 | adapters/whisper.prepare_audio, workflows.predict → AudioTests history/latest association and no fallback; CliTests complete public audio pipeline | PASS injected; actual ASR deferred |
| AC-06 | artifacts.audio_path, inspect_wav/prepare_audio → ArtifactTests traversal/environment and actual junction; AudioTests corrupt/absent/duration/deadline | PASS |
| AC-07 | runtime/context/references, adapter context budgets → ContextTests full retained payload/overflow; RuntimeTests history not replayed; OllamaTests context overflow | PASS |
| AC-08 | data/kit catalog/allowed_tools, ToolSpec → dynamic extension roundtrip, malformed installed association, actual SDK public-only full coverage | PASS |
| AC-09 | runtime/normalize → original and added complete-number/local-days tests PASS; independent corrected temporal-basis probes produce certain wrong date/time | **FAIL F-01** |
| AC-10 | runtime/references → ReferenceTests literal/history/live/fabricated/ambiguous/type/menu-parent cases and runtime provenance | PASS |
| AC-11 | contracts decisions/json_loads, runtime/validation/loop → duplicate/nonfinite/overflow/exact shape/repair and invalid-proposal checks | PASS |
| AC-12 | adapters/sdk, runtime/loop and Session protocol → counted factory/getters, fatal init/getter fixture, actual SDK contracts; inference has no get_state | PASS |
| AC-13 | runtime/validation/references and final env.validate → nested arrays/required/extra/type/one-of/ASK guards; actual SDK nested-gap and preflight check | PASS |
| AC-14 | outcomes/validation/loop/ledger → success without done, no-op/unknown/tool-specific outcomes and actual failed/insufficient-balance SDK results | PASS |
| AC-15 | runtime/goals/loop → GoalTests dependency and typed condition; LoopTests premature DONE, independent goals and actual rain/no-rain branches | PASS controlled plans; learned decomposition deferred |
| AC-16 | validation.checked_call, loop ASK → actual target/params shape, invalid names, ambiguous read then terminal ASK and independent success retained | PASS |
| AC-17 | internal DONE and controlled GoalPlan → unsupported/withdrawn request actual empty hash, applied history and independent partial work | PASS controlled decisions |
| AC-18 | Ledger.bind/record/recovery_proven and loop → success/unknown retry blocks, cause-linked bank recovery/unrelated-read negative, distinct equal occurrences twice not three | PASS |
| AC-19 | RunConfig, loop clock/generation guards, adapter/ASR deadlines → injected late proposal no call; cap/timeout/six calls plus DONE, audio deadline | PASS; hard hardware timing deferred |
| AC-20 | loop same-session getters, submission and atomic writer → exact getters, failed-then-correct log, Unicode, strict order/IDs/fields/hash and complete CLI fixture | PASS |
| AC-21 | workflows.predict, run metadata/checkpoint writers → fatal after one sample/after write, no final on failure, selected/completed IDs and truthful status | PASS |
| AC-22 | diagnostics/run contracts, loop/workflows and allowlisted metadata → mode/settings/timing, rejected/executed distinctions, fatal true trace, secret config/exception sentinel absence | PASS; unavailable measures explicit |
| AC-23 | data/replay, sanctioned train replay boundary → PreparationTests transient state/exact result/state/trace comparison, SDK synthetic contracts; no inference state getter | PASS injected/static; full real replay NOT RUN |
| AC-24 | data/kit.frozen_split, data/splits, trainer preflight → deterministic assignments, exact source digest, overlap/foreign/mismatched/app-out exposure failures | PASS |
| AC-25 | learning/trajectories and trainer preflight → READ→WRITE observation prefixes, ASK/empty terminal DONE, sequence/provenance/drift/alignment checks | PASS fixture/static; real expansion NOT RUN |
| AC-26 | learning/serialization and ActionCollator → exact target roundtrip/prefix/masks, pad==EOS, overflow/empty target, injected actual trainer preserves collator labels | PASS fixture/static; real tokenizer/forward/loss NOT RUN |
| AC-27 | learning/trainer, train CLI/wrapper → dry-run no heavy/output; injected real LoraRuntime options and SFTTrainer.train/save_model invocation, prerequisite/error checks | PASS software; actual training NOT RUN |
| AC-28 | trainer artifacts/provenance/status, TrainingConfig and local PEFT adapter selection → injected save/missing artifact/failure/interruption, hashes/config/settings and local adapter integration | PASS software; real adapter save/reload/quality NOT RUN |
| AC-29 | metrics/proxy/reports, workflows.evaluate → maximum matching, duplicates/extra reads/fuzzy boundary/empty/hash-versus-text, frozen identity and paired first/later report checks | PASS PROXY; official parity UNKNOWN |
| AC-30 | metrics/asr using shared normalize → same-ID/config/denominator/downstream tests PASS; independent corrected-vs-final supplied transcript comparison emits wrong critical time difference | **FAIL F-01**; actual ASR deferred |
| AC-31 | Dockerfile/.dockerignore/predict.sh, package_check and entrypoints → PackagingTests bootstrap/offline/static paths, complete injected audio workflow, independent archive byte/member audit | PASS static/injected; image/model runtime NOT RUN |
| AC-32 | operator/local_training/offline/migration/architecture guides/configs → GuideTests interfaces/examples/K references and operator-path inspection, recorded nine help exits 0 | PASS scoped structure/commands; helper behavior gap remains F-01 |
| AC-33 | layered contracts/protocols/facades/CLI and real smoke consumer → independent Ruff/format/mypy; no-heavy imports; UtilityConsumerTests actual policy/planner/main and saved reviewer probe one read then DONE | PASS; **F-02 CLOSED** |
| AC-34 | approvals/grant, immutable baseline/AFTER/diff, implementation/review and exact actual command evidence → independent full byte/protected/assertion/package checks | PASS evidence discipline; final owner acceptance NOT RUN |
| AC-35 | local Ollama/Transformers/Whisper boundaries → all original 13 Ollama origin/proxy/redirect/cloud/missing/late guards; local-only mocked model/assets and invalid response tests | PASS software; actual optional-runtime/model fitness NOT RUN |
| AC-36 | artifacts/workflows/trainer and actual kit utilities → source/input/model/output/no-clobber/partial failure checks; direct/wrapper/lexical and real junction aliases, all explicit inputs and smoke sidecar preflight; independent forbidden-child refusal | PASS; **F-03 CLOSED** |

## Stable finding dispositions

| ID | Severity/confidence | Disposition and evidence |
|---|---|---|
| F-01 | MEDIUM / VERIFIED | **OPEN, partially repaired.** Exact original four cases now correct. New supported adjacent temporal-basis cases still emit wrong certain values and reach actual inference/ASR consumers. Details below. |
| F-02 | MEDIUM / VERIFIED in r1 | **CLOSED.** ReadOnce.plan delegates without consuming action state; explicit ReadPlan is injected by actual smoke main. Independent suite tests actual script import and main using the real infer loop with only session creation injected. Saved unchanged reviewer probe reaches DONE with exactly one read and real fake-session getter trace. |
| F-03 | MEDIUM / VERIFIED in r1 | **CLOSED.** All three utilities protect both selected/resolved direct/wrapper kit plus explicit file inputs before processing. Smoke preflights sidecar against inputs/output before catalog/runtime. Independent actual-script direct/wrapper/lexical alias/input collision/existing-sidecar/external-success and Windows kit/sidecar junction tests pass; old reproduction now child exit 1/no file. Original baseline limitation was correctly repaired under newly approved AC-36, without claiming an introduced regression. |

No additional independent F-ID or unresolved SUSPECTED material finding is recorded.
F-01 is retained under its existing grouped normalization/correction identity because
the new evidence demonstrates incomplete repair of that same defect class. Fixed
numeric and independent-intent cases are not reported again as failing.

### F-01 — Corrected time loses its temporal basis and remains falsely certain

**Status:** OPEN. **Severity:** MEDIUM. **Confidence:** VERIFIED.
**Criteria:** AC-09/AC-30, related K32/K40/K44.
**Locations:** src/lifemate/runtime/normalize.py:171–218 (local clock/date
interpretation, especially separators at 175–180) and :247–275 (same-kind scalar
supersession without temporal-basis preservation/uncertainty). Consumers:
runtime/loop.py normalization/planner/action payload, runtime/context.py, and
metrics/asr.py:19–35 filtering only per-value superseded/uncertain flags.

Expected: a supported local scalar clock correction retains the associated
unmodified temporal basis where justified, or reports the affected interpretation
as uncertain. It must not invent a certain today/absolute timestamp that contradicts
the retained request. Unknown correction scope must not leave stale/conflicting
time values advertised as certain critical slots. Preserve independent goals,
original spans/negation and the repaired expression-local multi-goal behavior.

Actual independent reproduction uses only authored text and sample clock
`2026-11-10T10:00:00+07:00`, timezone Asia/Ho_Chi_Minh:

| Authored input | Actual surviving certain time | Required basis or uncertainty |
|---|---|---|
| `mai năm giờ à không, năm rưỡi` | `2026-11-10T05:30:00+07:00` | Tomorrow `2026-11-11T05:30:00+07:00`, or explicit affected-value uncertainty |
| `nhắc mai 8 giờ à không, 9 giờ` | `2026-11-10T09:00:00+07:00` | Tomorrow 09:00, or uncertainty |
| `thứ hai tuần sau 5 giờ à không, 6 giờ` / `thứ hai tới ...` | `2026-11-10T06:00:00+07:00` | Monday `2026-11-16` 06:00, or uncertainty |
| `nhắc mai 8 giờ à không, 9 giờ à không 10 giờ` | `2026-11-10T10:00:00+07:00` | Tomorrow 10:00, or uncertainty through the chain |
| `2026-12-31T23:00:00+07:00 à không, 22 giờ` | `2026-11-10T22:00:00+07:00` | Preserve explicit December 31 basis if justified, otherwise uncertainty |
| `nhắc sau 2 giờ à không, 3 giờ` | `2026-11-10T03:00:00+07:00` | Preserve a justified relative-duration correction or mark ambiguity; no silent absolute 03:00 default |

The first case returns effective_text=`mai năm rưỡi`, supersedes tomorrow 05:00,
leaves today 05:30 with uncertain=false, and returns uncertainties=[]. The actual
infer→planner request contains that contradiction; a captured empty-plan/DONE
fixture proves propagation without any SDK action or model. `critical()` also
returns today 05:30 as its sole certain time. Supplied `evaluate_asr` between the
corrected transcript and its final equivalent `mai năm rưỡi` reports a false
critical time difference (today versus tomorrow). WER/CER and the correction-marker
difference are naturally textual; the time mismatch is the demonstrated defect.

The independent probe also reproduces the same error with an independent transfer
goal retained, and at sample `2026-12-31T23:50:00+07:00` where tomorrow's corrected
09:00 wrongly becomes December 31 rather than January 1. Directly loading the
sealed r1 normalizer for comparison confirms the tomorrow/day-combination regression
was introduced by this repair's clause-local rewrite. This does not recommend
restoring r1's utterance-global date leakage; retain the independent-intent fix.

For `mai 8 giờ tối à không, 9 giờ`, r2 adds a marker-level unresolved-scope
uncertainty but leaves both tomorrow 20:00 and today 09:00 with uncertain=false;
critical() exposes both as certain. This adjacent form shows why merely adding a
global uncertainty message does not resolve affected-value certainty downstream.

Reproduction: execute review.r2.probes.py from the explicit root with the core
interpreter/environment above; exit 0 confirms the defect assertions reproduced.
Full raw normalized values, spans, expected-or-uncertain bases, sealed r1 comparisons,
actual planner payload and supplied-ASR result are retained in review.r2.probes.json.
Coordinator's supplementary snapshots/after-20261110-r2.adjacent-time-probes.json was
also read; relative/explicit/chained/evening cases were then independently reproduced
in this Reviewer's own probe. No real data/models or hidden state were used.

**Minimal corrective action:** make correction handling aware of the temporal
basis it is replacing, or conservatively mark/omit affected normalized values where
inheritance cannot be established. Keep original/raw/effective/span evidence
consistent and ensure critical metrics exclude affected uncertain interpretations.
Cover all currently supported bases and adjacent combinations: day/weekday,
AM/PM/evening qualifiers, relative duration, explicit date/time, chained correction,
explicit changed qualifier, independent intents and rollover. Add actual
planner/action-context and critical-slot consumer checks. Do not fix only the
first comma/tomorrow string, restore global day leakage, or run real models merely
to demonstrate this deterministic software repair.

## Explicit limits and coordinator action

Actual ASR/model semantic accuracy, learned planner/binder behavior, optional-runtime
dependency resolution on intended hardware, real tokenizer/template/token-boundary
and mask roundtrip, forward/loss, LoRA training/save/reload/quality, full authorized
train replay/freeze/trajectory jobs, holdout paired scores and repeated model-run
stability remain **NOT RUN**. Official scorer parity and competition release/mount/
resource constraints remain **UNKNOWN**. Docker build/network-disabled model-bearing
runtime, Linux executable mode, real latency/memory/parameter totals and official
validation remain **NOT VERIFIED**. These are explicit approved DEC-02/03 deferrals;
synthetic Session/injected third-party checks are not substituted for them.

There is no material unanswered product decision and no permission/scope/risk change.
Return F-01 to an authorized Developer under unchanged EG-01, preserving F-02/F-03
closures, all sealed stores, prior artifacts and regression assertions. Coordinator
may dispatch that bounded repair without redundant human approval, then seal a new
AFTER and obtain a **fresh independent review round 3, the final permitted round**.
This Reviewer neither repairs application code nor dispatches Developer.

AI_PASS is not supported for r2. After any later AI_PASS, coordinator must recompute
live/protected identities and request one consolidated accountable-owner acceptance
of implementation plus review tied to that exact unchanged snapshot and MEDIUM risk.
No human acceptance, merge, publish, deployment or competition submission is granted
by this artifact.
