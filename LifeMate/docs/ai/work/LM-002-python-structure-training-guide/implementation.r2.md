# Implementation — full LifeMate application, bounded review repairs

WORK_ID: LM-002-python-structure-training-guide  
STAGE: DEVELOPER  
REVISION: r2  
STATUS: READY_FOR_AI_REVIEW  
CLARIFICATION_CHECK: NO_MATERIAL_GAPS — DEC-01/02/03 and coordinator-confirmed EG-01 repair scope  
RISK_TIER: MEDIUM  
DATE: 2026-11-10 (Asia/Saigon)

This revision retains the complete accepted C01–C15 application and fixes the three
verified groups from independent review r1. It is a Developer handoff for fresh
independent review round 2, not AI_PASS or human final acceptance. The prior
implementation, review, logs and both sealed stores remain preserved read-only.

## Approved scope, receipts and authority

This is the full C01-C15 application software delivery, not a trainer-only sketch.
The Developer was a real generic role-guided delegate under DEC-01, inheriting the
coordinator model/effort/permissions; no native-worker selection or subdelegation is
claimed. Effective AGENTS.md, COMMON_RULES, embedded Developer instructions, actual
handoff, source/Intent/Spec/Plan/ledger and original parent evidence were independently
read. Source documents are evidence, not authority to expand operations.

Observed user receipts supplied by coordinator and independently bound to unchanged
artifact hashes:

| Receipt/input | Bound identity |
|---|---|
| AP-01 `APPROVE intent r2` | d7c8e8ada44f76feaaa074b8f19c575e71610d618038b7ac0327362ba6e6e5a6 |
| AP-02 `APPROVE spec r1` | 84f6a227878423ec886f3575b523f6b3e7aa5b7d0e8e1ba7d1da1aa4c9ad12a0 |
| AP-03 `APPROVE architect r1` | 722c2d624027dc17e4697f4648be5f6f3abe7a20e4087239807582c1059905ba |
| source.md r3 / DEC-01/02/03 | ab1e5a069dc9c2379226c0e475f35b9d1992da9416175ec2d2a15e042c5f0205 |

EG-01, separately observed verbatim: **GRANT implementation under plan r1 §13,
including snapshot capture under §12 and core/dev setup and checks under §11,
retaining all listed exclusions.** Root is
`C:/Users/nktoan/Downloads/LifeMate_2026_Kit_Verified_Coding_Handoff/LifeMate`.
All commands used that explicit working directory. Only exact §13 application paths,
authorized generated .venv-core/build/dist/caches and bounded implementation revision
evidence were written. Approved source/Intent/Spec/Plan, rules, progress.md, original
parent evidence, owner .venv and organizer/model/data boundaries were not edited.
No Git, external messages/mutations, downloads of models, actual training/ASR/policy
jobs, real ToolEnv/replay/dataset generation, Docker execution or destructive rollback.

## Review findings and observable repairs

Coordinator explicitly confirmed that F-01–F-03, affected consumers/tests and accurate
guides remain under original EG-01/Plan r1 without scope, dependency, design or risk
expansion. The latest actual user instruction to resume maintains that authorization.
No additional material product decision or human Developer gate is required.

| Finding | Developer disposition and defect-class repair | Current concrete proof |
|---|---|---|
| F-01 / MEDIUM / VERIFIED in r1 | Implemented: consume complete numeric phrases with word/numeric boundaries, support complete Vietnamese tens, reject unsupported signs/compounds/nonfinite ranges with uncertainty, preserve exact source spans. Clock qualifiers associate locally; conflicting/unsupported associations stay uncertain. Only adjacent same-kind scalar replacements supersede their previous value. Independent intents, raw text and negation evidence survive. Unresolved adjacent corrections mark the affected prior value uncertain. ASR critical slots omit uncertain values and expose uncertainty evidence. | NormalizeTests three new defect-class methods cover compound words, signed/adjacent malformed numbers, large values, separate day clauses, names/qualifier conflicts and local/unsupported/no-comma corrections. New AsrMetricTests method proves 13M versus 3M is detected, amount retention across an independent corrected clock, signed uncertainty and local dates in downstream metrics. All pass. |
| F-02 / MEDIUM / VERIFIED in r1 | Implemented: actual smoke script injects separate deterministic ReadPlan. ReadOnce also delegates planning without advancing its action state, preserving callers that use planner discovery. One eligible read remains followed by internal DONE. | UtilityConsumerTests imports the actual script and exercises its policy/planner with real infer and FakeEnv, then executes the actual script main with only its environment factory injected. Exactly one validate/call, real getter trace and DONE/sidecar are asserted. The unchanged saved Reviewer probe also reaches DONE with one read. No real ToolEnv is used. |
| F-03 / MEDIUM / VERIFIED in r1 | Implemented: all three utilities resolve direct/wrapper roots and preflight outputs against both selected/resolved kit roots plus every explicit fold/trajectory/replay input before data processing. Smoke preflights the diagnostics sidecar against inputs and output before catalog/runtime work. Existing-destination no-clobber remains. This repairs a retained baseline limitation required by the newly approved full scope; it is not mislabeled a new regression. | Actual-script tests cover direct/wrapper/lexical aliases, all explicit file collisions, existing outputs/sidecars, sidecar/input collision, successful external destinations for all utilities and actual Windows kit/sidecar junction aliases. Early-work sentinels prove rejection precedes processing/session creation. Unchanged Reviewer utility probe exits 1, creates no forbidden kit report. |

The saved read-only `review.r1.probes.py` was rerun unchanged; new results are
[review-probes.json](verification-r2/focused-boundaries-final/review-probes.json). Its runner
exit is 0, meaning the reproduction runner completed; the protected-write child exit
1 is the expected refusal. Concrete normalization outputs are 13,000,000, no positive
value for -500 nghìn (uncertainty), today 17:00 plus tomorrow 08:00, and preserved
500,000 with the ride's 05:00 superseded by 05:30. These are authored fixtures, not
actual speech/model understanding.

Only these nine application paths changed from r1:

- `docs/operator_guide.md`
- `scripts/check_evaluator.py`
- `scripts/check_trajectories.py`
- `scripts/smoke_runtime.py`
- `src/lifemate/metrics/asr.py`
- `src/lifemate/runtime/normalize.py`
- `tests/test_asr_metrics.py`
- `tests/test_cli.py`
- `tests/test_normalize.py`

The operator guide now explains conservative quantity/correction boundaries,
critical uncertainty diagnostics and the utility/sidecar preflight. No package,
dependency, runtime, path allowance or approved stage/rule was changed.

## Complete change identity and self-review

No Git history is claimed. The agreed original BEFORE application identity is
`c38a7def852406a3411f9c9dc5ee1e1b6e95cadf8b9e73d3452cf75b95608a24` in
`snapshots/before-20261110-ap03-eg01-02/application/`; manifest SHA is
`b5525c293e51ddd65d20b0b720bc49465d1d35d9b004d8bade69fe0294822249`.
The immutable r1 AFTER identity remains
`e2db119b38994814c0689d339b1e9a334060db65678c35a949cd5af1038e6ea0`, manifest SHA
`f618dd62ec7ff529fb9a6d2a62f4a6ac0670674aef2ac9daf2c27766ab5808ac`.

Final live application identity: **`79ba6a2e59ffba48035c2c03c549eb3ad820a5f04ef5a6f91a8b0b0b6a4a4b07`**.
The agreed inventory includes all source/tests/scripts/configs/guides/packaging and
original file/directory metadata/bytes, with only Plan §12 exclusions. There are
102 application files, 97 baseline-to-final changed files (68 added, 29 modified),
zero deletions and zero out-of-grant paths. Repair r1→r2 changes nine existing files.

| Inspectable evidence | SHA-256 / size |
|---|---|
| [Full original→final diff](implementation-full-diff-r2.patch) | `037d468dc621c64f375fd533a28ced062123083c742cc302c1e9af754c991ca6` / 9558 lines |
| [Full original→final path/type/byte records](implementation-diff-r2.json) | Canonical baseline/live identities, all changed paths, original assertion audit |
| [Repair r1→r2 diff](implementation-repair-diff-r2.patch) | `104215fe280230d065727d0b39fa70d6d5a6d30fac1bd40438683d2b6804ea8b` / 850 lines |
| [Repair path/type/byte records](implementation-repair-diff-r2.json) | All nine paths and r1/r2 digests, all r1 test assertions retained |
| [Final evidence audit](implementation-evidence-audit-r2.json) | PASS; approved/preserved artifacts, original/r1 tests, K coverage, final archives |

One-off [self-review script](implementation_self_review_r2.py) uses the agreed
capture inventory, verifies sealed stores without creating/reusing a new store,
rejects ungranted/deleted paths, compares both complete unions and inspects final
archive bytes/membership. Self-review examined all nine repaired paths and affected
runtime/context/metric/SDK consumers; the remaining r1 application bytes are proven
unchanged against the independently reviewed r1 store. The complete original-to-final
diff remains inspectable for Reviewer rather than substituting the repair-only patch.
All original 68 methods/137 assertion-call expressions and every r1 test method and
assertion expression remain; no assertion weakening or production atomic-writer
substitution was used. Coordinator alone captures/seals new AFTER r2 after handoff.

## TASK coverage

| Task | Implemented done condition / evidence | AC coverage |
|---|---|---|
| TASK-01 | Coordinator baseline before any app edit; sealed BEFORE reread/verified by Developer | AC-34 |
| TASK-02 | Pydantic strict contracts/configs, lazy dependency groups, example configs | AC-01/02/33 |
| TASK-03 | Protected normalized paths, atomic no-clobber writers, recursive editable/installed provenance | AC-20/21/22/28/36 |
| TASK-04 | Direct/wrapper selected kits, SDK namespaces, dynamic registry, exact frozen/app-out checks | AC-03/04/08/12/24 |
| TASK-05 | Local WAV/history ASR software, raw/normalized span evidence, sample-clock context | AC-05/06/07/09/30 |
| TASK-06 | Recursive schema/ASK/format checks, typed/ambiguous/parent references, tool-aware outcomes | AC-10/11/13/14/16/18 |
| TASK-07 | Validated goals/dependencies/conditions/occurrences, one-session bounded loop/recovery | AC-11/12/14/15/16/17/18/19 |
| TASK-08 | Local Ollama/Transformers planner/action/binding and optional adapter integration | AC-02/11/19/28/35 |
| TASK-09 | Train-only injectable replay and exact teacher-forced observation-prefix expansion | AC-23/24/25 |
| TASK-10 | Single-action serializer/masks/collator, real lazy LoRA trainer, dry-run/save/failure provenance | AC-26/27/28 |
| TASK-11 | PROXY maximum matching/reports/paired regressions and supplied ASR slot/call/state/timing deltas | AC-22/29/30 |
| TASK-12 | Thin CLI/workflows/wrappers, complete injected audio pipeline, offline packaging/config/archive boundaries | AC-02/20/21/22/27/31/33/35/36 |
| TASK-13 | Complete operator/training/migration/packaging/architecture guides and exact K01-K54 matrix | AC-32/33/34 |
| TASK-14 | Actual core/dev/static/build/help checks, full path/byte diff, grant and original-test self-audit | AC-01-36 software evidence; review/owner gates pending |

## Acceptance criteria → code → observed checks

All rows below are software evidence at this stage. Where real-model/official checks
are required, they remain explicit deferred limits below; AC-34 independent review/
owner acceptance is the coordinator's next gate rather than a fabricated pass.
Names below refer to current tests, rerun in the final 180-test suite. The K matrix
contains all 54 rows and 63 unique executable method references, with none missing.

| AC | Changed implementation | Actual passing software evidence |
|---|---|---|
| AC-01 | `src/lifemate/contracts.py, config.py; runtime/validation.py` | test_contracts, test_validation, test_runtime.SchemaTests |
| AC-02 | `src/lifemate/cli.py, config.py; lazy adapters and learning/trainer.py` | test_cli, test_backends, test_training.test_dry_run_no_heavy_runtime_or_output |
| AC-03 | `src/lifemate/data/kit.py, adapters/sdk.py; workflows.bundle` | test_data, test_runtime.DataTests, test_sdk_contract distinct split namespaces |
| AC-04 | `src/lifemate/contracts.InferenceSample; data/kit.inference_input/read_jsonl` | test_data train-oracle/test isolation and duplicate manifests; test_runtime label guard |
| AC-05 | `src/lifemate/adapters/whisper.prepare_audio; workflows.predict` | test_audio history/latest order; test_cli complete public audio fixture |
| AC-06 | `src/lifemate/artifacts.audio_path; adapters/whisper.inspect_wav/prepare_audio` | test_artifacts traversal/environment/junction; test_audio corruption/duration/ASR failure |
| AC-07 | `src/lifemate/runtime/context.py; runtime/references.py; adapters budgets` | test_context full payload/overflow; test_runtime history not replayed; test_ollama overflow |
| AC-08 | `src/lifemate/data/kit.allowed_tools/load_catalog; contracts.ToolSpec` | test_contracts extension roundtrip; test_data installed association; test_sdk_contract public-only tool |
| AC-09 | `src/lifemate/runtime/normalize.py` | all prior test_normalize checks plus complete numeric boundaries/spaced signs/mixed phrases, local day/correction scope and raw spans (F-01) |
| AC-10 | `src/lifemate/runtime/references.py` | test_references fabricated/ambiguous/device/menu-parent; test_runtime explicit/history/lookup provenance |
| AC-11 | `src/lifemate/runtime/validation.parse_decision; contracts decision RootModel` | test_contracts duplicate/nonfinite/overflow; test_runtime strict parsing/repair path |
| AC-12 | `src/lifemate/runtime/loop.py; adapters/protocols.Session/sdk.py` | test_runtime exact getters/one factory; test_loop SDK init/getter/fatal errors; SDK contracts |
| AC-13 | `src/lifemate/runtime/validation.py and references.py; final SDK validate` | test_validation nested/ASK/date/time/date-time; test_runtime schema negatives; actual SDK nested gap |
| AC-14 | `src/lifemate/runtime/outcomes.py; validation tool markers; runtime/loop.py` | test_runtime no-op/unknown/tool-specific success; SDK insufficient balance and failed logs |
| AC-15 | `src/lifemate/runtime/goals.py, runtime/loop.py` | test_goals dependencies/actual typed conditions; test_loop premature DONE/conditional/independent goals |
| AC-16 | `src/lifemate/runtime/validation.checked_call; runtime/loop ASK branch` | test_validation real ASK shape; test_loop independent success/ambiguous read then terminal ASK |
| AC-17 | `src/lifemate/runtime/loop DONE branch; validated controlled goal plan` | test_loop unsupported/withdrawn fixture real empty hash; test_runtime history/unsupported DONE |
| AC-18 | `src/lifemate/runtime/goals Ledger.bind/record/recovery_proven` | test_goals successful/unknown/no-op retry guards; test_loop explicit repeat twice not three |
| AC-19 | `src/lifemate/config.RunConfig; loop clock/generation guards; local backend deadlines` | test_loop injected late clock; test_runtime six calls plus DONE and timeout; test_audio deadline |
| AC-20 | `src/lifemate/runtime/loop actual getters; submission.py; artifacts writers` | test_runtime exact getter/shape/Unicode; SDK failed+correct trace; test_cli complete final |
| AC-21 | `src/lifemate/workflows.predict; artifacts.py; RunMetadata` | test_cli failure after completed x before SDK y; fatal-after-write diagnostics; no final on failure |
| AC-22 | `src/lifemate/RunMetadata/DiagnosticRecord; workflows.predict; loop timing; hidden error inputs` | test_cli explicit mode/split/settings, secret sentinel absent, fatal real trace; test_loop diagnostics |
| AC-23 | `src/lifemate/data/replay.py compatibility replay.py` | test_preparation transient sanctioned state getter/exact replay; SDK Session contracts; real replay deferred |
| AC-24 | `src/lifemate/data/kit.frozen_split; data/splits.py; training preflight` | test_runtime deterministic freeze; test_data app-out overlap/foreign/exposure; exact digest checks |
| AC-25 | `src/lifemate/learning/trajectories.py; check_trajectories wrapper` | test_preparation READ-WRITE prefixes/ASK/empty/DONE/alignment/drift; training provenance checks |
| AC-26 | `src/lifemate/learning/serialization.py` | test_training masks/roundtrip/boundary/overflow/EOS/pad and actual collator; real tokenizer/loss deferred |
| AC-27 | `src/lifemate/learning/trainer.py; train CLI/wrapper` | test_training dry-run and injected actual LoraRuntime options/train/save; no real model/training |
| AC-28 | `src/lifemate/config.py; contracts.py; learning/trainer.py; adapters/transformers.py` | test_training save/fail/interruption/identity; backend local adapter code and guides; real reload deferred |
| AC-29 | `src/lifemate/metrics/proxy.py, reports.py; workflows.evaluate` | test_runtime EvaluatorTests maximum matching/hash/text/empty/duplicates; test_evaluation paired identity/later actions |
| AC-30 | `src/lifemate/metrics/asr.py` | all prior ASR metric checks plus complete quantities/local scope/uncertainty downstream (F-01); actual ASR deferred |
| AC-31 | `Dockerfile; .dockerignore; predict.sh; src/lifemate/workflows.py; entrypoints` | test_packaging offline backend bootstrap/entrypoint; test_cli complete public audio injection; archive member audit |
| AC-32 | `docs/*.md; configs/*.json; script help surfaces` | test_guides example configs/interface tokens/K matrix; all requested help exits 0; real smoke snippet AST parsed only |
| AC-33 | Layered source/contracts/protocols/facades and `scripts/smoke_runtime.py` | Ruff/format/mypy46 PASS; import no-heavy fixture; actual smoke policy/planner/main one-read consumer PASS (F-02); original tests retained |
| AC-34 | This artifact and complete baseline/diff/check evidence; coordinator AFTER/review ownership | self-review exact grant/path/byte identity PASS; approved hashes unchanged; fresh AI review and final human acceptance NOT RUN |
| AC-35 | `src/lifemate/adapters/ollama.py, transformers.py, whisper.py` | all 13 original Ollama guards PASS; test_backends actual lazy mocked APIs/local-only loads; late response no call |
| AC-36 | `src/lifemate/artifacts.py; training/workflows; package manifests/guides` | all prior artifact checks; all three actual utilities/direct-wrapper-alias/input-sidecar collisions/no-clobber/external-success; kit/sidecar Windows junction PASS (F-03); archive exclusions |

All original K01-K54 are mapped exactly once in
[edge_case_coverage.md](../../../edge_case_coverage.md), with CORE/SDK/POLICY/PROXY/
SCORER/deferred distinctions. Original P0 pre-training gate is retained verbatim in
meaning: K01-K13, K18, K25-K30, K35-K38, K45-K48, K53. Core passes do not grant or prove
real replay/baseline/tokenizer/loss/training/model/Docker/official release gates.

## Actual r2 checks, commands and outcomes

Every child used `PYTHONDONTWRITEBYTECODE=1` and
`PIP_CACHE_DIR=<root>/.venv-core/pip-cache`, Python 3.12.0 from the existing
`.venv-core/Scripts/python.exe`, and explicit implementation-root cwd. The explicit
built-in WindowsPowerShell shell was used. No installs occurred in r2. Core/dev
versions and absent optional runtimes remain documented by the preserved r1
core-environment evidence; pip check was rerun. Actual compileall only targets
`src scripts tests`. Package builds use existing build/dev dependencies and
`--no-isolation`, without package-index/network use.

[Final complete command records](verification-r2/complete-release/summary.json)
contain exact absolute commands, cwd, environment, exits and separate raw logs.
All final commands below exited **0**:

| Interpreter arguments | Final observed result |
|---|---|
| `-m pip check` | PASS; no broken requirements |
| `-m unittest discover -s tests -v` | **180 tests: 179 PASS, 1 Windows symlink-privilege SKIP, zero failures/errors** |
| `-m compileall -q src scripts tests` | PASS |
| `-m ruff check src scripts tests` | PASS |
| `-m ruff format --check src scripts tests` | PASS, 76 files |
| `-m mypy src/lifemate` | PASS, 46 source files |
| `-m build --no-isolation` | PASS; wheel and sdist refreshed after final application edit |
| `-m lifemate --help`; `-m lifemate train --help` | Both PASS |
| `scripts/lifemate.py predict --help`; `scripts/train_lora.py --help`; `scripts/predict.py --help`; `scripts/verify_package.py --help` | All four PASS |
| `scripts/check_trajectories.py --help`; `scripts/check_evaluator.py --help`; `scripts/smoke_runtime.py --help` | All three affected utilities PASS |
| `implementation_verify_r2.py focused-boundaries-final` | Exit 0; normalizer (10), ASR metrics (3), actual CLI consumers (12) and immutable Reviewer probes all exit 0 |
| `implementation_verify_r2.py audit-release` | Exit 0; self-review command exit 0; full diff/grant/original+r1 assertions/K references/archive-byte checks PASS |

The final suite adds nine tests to the preserved r1 171: three normalization,
one ASR metric, five actual utility consumer tests. All 18 actual external SDK
synthetic Session contracts pass. The existing artifact junction and new actual
utility-kit/sidecar junction checks pass. Synthetic fixtures and injected trainer/
ASR/SDK boundaries remain software proof, not real model execution.

Prior attempts are retained truthfully:

- `verification-r2/focused-sandbox/summary.json` runner exit 1: normalizer/ASR/probes
  exit 0; consumer tests exit 1 on host OS-temp atomic-rename denial and the new
  evaluator fixture's missing required `pass` flag. No writer/test was weakened.
- `focused-escalated` runner exit 1: permission escalation removes atomic-rename
  errors; one new evaluator-success fixture still failed because its authored
  replay reference omitted `pass:true`. Fixture corrected to the real contract.
- `focused-final` runner exit 0. A subsequent marker-masking improvement for
  no-comma corrections exposed four existing/new assertions in `complete-final`
  (runner exit 1; 179 tests, four failures/one skip). Whitespace masking had
  incorrectly extended clock spans across the marker; non-whitespace sentinel
  masking restores exact spans and local supersession. No assertion changed.
- `focused-confirmed`, `complete-confirmed` and final `complete-frozen` are PASS.
  The latter includes the final added utility junction test. After expanding the same numeric-boundary test with spaced signs and mixed/spaced numeric phrases, `focused-boundaries-final` and final `complete-release` also exit 0 against the exact final source. Failed logs remain.
- The first one-off self-review checker rejected the retained historical
  `docs/catalog_audit.json` missing from the established sdist manifest. Its raw
  traceback is retained in `verification-r2/self-review-first.log`; checker
  expectation corrected to the unchanged r1 packaging policy. Final checker
  verifies all intended current source/tests/scripts/guides/configs and Docker
  metadata, excludes only `.gitignore` and that historical audit from expected
  sdist coverage, and checks every actual owned member byte. No app packaging
  exclusion was added. Final `audit-release` command has a recorded actual exit 0.

Managed escalation was used only for already-granted core/build and authored
OS-temp atomic-rename checks. There was no rejected approval or unresolved host
permission blocker. Immutable r1 logs/reports and snapshot outputs were not reused.

## Final archive byte proof

| Archive | SHA-256 | Current owned bytes checked |
|---|---|---:|
| `dist/lifemate-0.1.0-py3-none-any.whl` | `9cb513cc7059f58284d15fa269ac392c4bd1246738681fac50432e21a685ff7b` | 47 |
| `dist/lifemate-0.1.0.tar.gz` | `6d4e9b7684fae7633619771467b7d18e367bb8bfbd5ba077140315f3819ed2bd` | 100 |

Full member names are in the final evidence audit. All 47 wheel-owned package
files exactly match the final source set and bytes; all 100 sdist-owned files
match current application bytes. No unexpected wheel package, process evidence,
SDK/data/model/audio/environment/cache payload is packaged. All intended source,
test, script, guide/configuration and declared Docker entrypoint files are covered.

## Preserved full-app coverage, decisions and residual limits

The full implementation behavior and architectural explanation in
[implementation.r1.md](implementation.r1.md) remain applicable except the explicit
F-01–F-03 corrections above. The complete TASK/AC matrix here is rerun against the
current final suite. K01–K54 rows and original P0 gate remain unchanged; 63 unique
named method references resolve and pass at their declared CORE/SDK/POLICY/PROXY
level. Fixture coverage does not establish semantic model accuracy, hidden gold
conventions or official scorer parity. Current application bytes are frozen.

DEC-01 generic role-guided staged work, DEC-02 real training code plus complete
later-run guide and DEC-03 full application/code-and-guides remain confirmed.
There is no new dependency, product/architecture choice, expanded risk or
unapproved deviation. MEDIUM remains appropriate for offline simulated tool
correctness, local input boundaries, training masks and compatibility. Independent
review and accountable-owner final acceptance remain required.

NOT RUN / NOT VERIFIED / UNKNOWN limits persist from the approved plan and r1:

- Real ASR/policy/planner/binder understanding, dialect/code-switching accuracy,
  real model/backend/adapter compatibility, latency/memory/target hardware. The
  existing maximum 30-second WAV support is unchanged. The normalizer deliberately
  leaves unsupported compounds/signs/qualifier/correction scope uncertain.
- Real-data ToolEnv, full train replay/freeze/trajectory production, frozen end-to-end
  baselines, holdout/app-out/model/ASR experiments. Only authored/injected fixtures
  and actual external SDK Session on authored dictionaries ran.
- Optional training/ASR/model setup, downloads, real tokenizer/template roundtrip,
  forward/loss, LoRA training, actual adapter/checkpoint save/reload/quality. The
  genuine delivered integrations and later-run guides remain intact.
- Complete weight fingerprint where metadata-only coverage is UNMEASURED; Python
  3.10 and Linux executable mode; CUDA/precision/optional-wheel resolution.
- Docker build/run/network-disabled model runtime, official resources/mounts,
  parameter/license/cutoff compliance, validator/scorer parity and submission.
  PROXY stays PROXY; supplied critical-slot calculations are not actual ASR runs.
- Symlink creation privilege (one skip); independent actual junction cases pass.
- New AFTER r2 capture, fresh independent Reviewer round 2 and final human exact-
  snapshot acceptance belong to coordinator; none is fabricated by this artifact.

Process writes comprise active implementation.md, the new r2 diff/audit/helper
files and `verification-r2/**` only. Approved artifacts, rules, coordinator ledger,
old evidence and original parent files remain read-only. No permanent runtime
tracker, snapshot reuse, Git mutation, external message/action or rollback occurred.

No known unresolved mandatory software failure or material decision remains after
final verification. Developer's disposition is ready for independent confirmation;
this is not self-issued AI_PASS.

RECOMMENDED_ACTION: coordinator independently validates final live identity and
protected evidence, captures/seals new AFTER r2 by the agreed method, and dispatches
a fresh independent Reviewer round 2 against the full baseline→final change and
F-01–F-03. Do not request a human Developer approval. Final accountable-owner
acceptance follows a passing independent review of this same exact snapshot.
