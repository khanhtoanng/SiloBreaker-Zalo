# LifeMate v3.2.0 — Verified Kit Contract and Unresolved Scoring Rules

**Review date:** 2026-11-09 (Asia/Ho_Chi_Minh)  
**Basis:** user-provided `LifeMate_Kit_Review_Small.zip` extracted from organizer archive `train+public_test.zip`; all findings here are from static examination of the enclosed code and catalog unless explicitly tagged external.  
**Status:** **TRAIN SDK VERIFIED BY SOURCE INSPECTION AND EIGHT SYNTHETIC CONTRACT CHECKS; NOT YET GOLD-REPLAY TESTED.** The small ZIP contains no training JSONL/audio, sample states, public-test catalog/runtime, official scorer, or Docker rules.

## 0. Evidence status legend

- `VERIFIED-IN-KIT`: the README, catalog or implementation provided in the uploaded archive expressly establishes the behavior. This is source inspection; not a claim of empirical success on real samples.
- `EXTERNALLY REPORTED`: public repositories/participant notes; do not treat as official scorer code.
- `UNKNOWN`: missing from the current upload; audit on the complete **local** organizer kit or official Rule/Evaluation page before claiming compliance.
- `RECOMMENDATION`: proposed engineering policy to test against held-out labeled train scenarios; not a guaranteed gold behavior.

## 1. Archive inventory and capability coverage

| Item | Verified observation | Evidence |
|---|---|---|
| Package version | `v3.2.0`, built `2026-10-24T23:35:25+0700` | `VERSION` |
| Sample counts | `train 1545`, `public_test 634` | `VERSION` |
| Extracted files | 57 selected source files + extraction manifest (58 archive entries) | `review_manifest.json` |
| Catalog | `schema_version: 2.7.0`, **46 applications / 147 tools**, specifically **62 read / 84 write / 1 meta** | `train/train_tools_catalog.json` |
| Tool schema annotations | **68 `x-ref` properties**, **40 `x-match` properties**, **6 `x-one-of` tools** | counted from catalog properties |
| Runtime | `ToolEnv(split, question_id, root)` returns `Session` and loads a **single sample** from the official split | `train/zaic_tools/__init__.py` |
| Scorer | **NOT included**: scorer parity, fuzzy-match threshold, matching order/multiplicity and full gating remain UNKNOWN | ZIP inventory |
| Public test SDK/catalog | **NOT included** in small ZIP: cannot compare app overlap or confirm unseen-app counts yet | ZIP inventory |
| Official Docker resource limits/model rules | **NOT included** here; verify Rule/Submission Guidance and Docker instructions | ZIP inventory |

No raw audio, labeled train JSONL or `<split>_environment` sample state was copied into the small review bundle. **Do not redistribute the organizer SDK/catalog in the project deliverables**; keep them inside the authorized local competition data directory, as the organizer README prohibits distributing the dataset.

## 2. ToolEnv: exact runtime contract (`VERIFIED-IN-KIT`)

1. Import **the SDK for the selected split**, not a locally copied implementation. `ToolEnv('train', id, root=<root containing train/> )` creates the one session used by the agent for that sample. Do not create a second `ToolEnv` during an inference run, even to simulate or undo an action.
2. `env.validate(name, arguments) -> {'ok': bool, 'error': str | None}` calls the schema checker without executing a tool, mutating state or adding a logged call.
3. `env.call(name, arguments) -> dict` appends the call to `Session.calls` **before** attempting it. Schema-invalid calls are still logged. The result may be `{'ok': False, 'error': ...}` or successful-looking no-op results such as `{'ok': True, 'done': False, 'message': ...}`.
4. `env.get_tool_calls()` copies the **actual attempted calls**, in order. Never reconstruct/alter it from model plans, remove rejected calls or append hypothetical ones.
5. `env.get_state_hash()` provides the submitted hash. Source implements SHA-256 over canonicalized state; **do not calculate the submission hash independently**. `env.get_state()` exists but must not be used to inspect application data during inference; training-only replay diagnostic usage requires authorization.
6. `Session.allowed` is derived by the SDK from the initial sample's `_meta.tools` plus `sys.ask_missing_info`. The agent should build its runtime tool registry from user-visible `context.installed_apps` intersected with the **split catalog**, and use `env.validate` as the final permit check. Log any mismatch between registry and `env.allowed` on authorized local train fixtures.
7. `sys.ask_missing_info` is a **real logged meta tool call**, requiring both `tool_name` (string) and `params` (string array). It returns `{'ok': True, 'waiting_for_user': True}`, does not modify state, and should normally terminate that inference turn. **Semantic correctness of the target tool and named params is not enforced by schema validation alone.**
8. History actions are already applied to the official initial state (per root README). Inference **must not replay history**; do preserve history user turns and tool observations for intent/coreference resolution.
9. SDK is Python 3.10+ and stdlib-only. Code uses `getattr` to dispatch supported app methods; an additional implementation check may be needed if a future catalog lists tools absent from SDK (`env.validate` only checks schema/allowed set).

## 3. `validate.py`: rejection contract (`VERIFIED-IN-KIT`)

Validation rejects tool names not in the catalog, tools not installed for a sample, missing `required` values, missing all `x-one-of` alternatives, incorrect primitive types and supported array item types/enums, invalid enum/range/format values. **Missing** means `None`, `''`, `[]` or `{}`. A bool is not accepted for integer/number; values must satisfy range bounds. Known formats: date, date-time and time (regex plus some field range checks).

**Crucial limits:**

- `x-ref` is **not** a runtime schema rejection criterion. Unknown ID can reach the app handler and return a business no-op. Treat `x-ref` as an instruction to ground/verify IDs through authorized tool observations, not proof that `env.validate()` checked existence.
- `x-match: fuzzy` is **not** implemented as a predicate in `validate.py`; it is matching metadata for scoring. Never make up free text or drop an explicitly requested free-text argument just because it is removed from canonical state.
- The validator checks an array's immediate `items.type` / `items.enum` but does **not recursively enforce nested object `properties.required`**. Example: `food_delivery.place_order.items[]` declares required `item_id` and `quantity`, yet `validate.py` only checks that each array member is an object. Add a separate *preflight semantic validator* for structured payloads without pretending the organizer rejects them at schema level.
- Unknown parameter names are not rejected by `schema_error`; the executor passes Python-identifier argument keys to the app handler, where many methods use `**_` and ignore extras. Avoid unknown fields: they may still reduce call matching precision or trigger handler exceptions.
- Empty optional values are treated as omitted by schema validation. Normalize optional fields consistently with the selected tool's expected semantics; **never invent defaults** that change final state.
- `env.validate` is not an oracle for business success; balance, item existence, status, phone lookup, duplicate contacts and other constraints require read observations and response checks.

## 4. Business result classification (`VERIFIED-IN-KIT`)

Recommended four-outcome classifier, implemented by the orchestrator and tested per tool:

| Outcome | Typical result | Mandatory agent handling |
|---|---|---|
| `REJECTED_SCHEMA` | `ok: false`, `error` | Call remains in log; prevent further invalid writes; learn from validation before call instead |
| `BUSINESS_NOOP` | `ok: true`, `done: false`, `message` | Do **not** mark goal complete; recover only if a missing read/parameter can be established without duplicate side effects |
| `BUSINESS_EFFECT` | `ok: true`, with created/updated entity and no failure marker | Update goal ledger with actual response; stop duplicate writes |
| `READ_OR_META` | `ok: true`, collections/data or `waiting_for_user` | Consume results; distinguish empty results and intentional ASK from success of a write |

Do **not** assume all writes have a `done` field: many successful writes omit it. Some app functions can return `ok: true, done:false` following exceptions, so use both result and tool-specific semantics. Do not replay rejected or partially applied writes simply because output was not what the model expected.

### SDK examples proving non-obvious behavior

- `banking.transfer`: valid-looking positive amount with nonexistent account/beneficiary or insufficient balance yields no-op; ensure `get_balance` and `list_beneficiaries` data is grounded.
- `ewallet.transfer`: when uniquely matched, contact phone can resolve to contact ID using `+84` ↔ `0` normalization. Two fields with inconsistent values are not guaranteed to be reconciled. Avoid adding redundant recipient args.
- `smart_home.light_set`: ID must belong to a light; generic `switch_set` has different behavior. A valid string ID with wrong type may no-op.
- `smart_home.get_status`: returns scenes only for an unfiltered request; need appropriate read to resolve `scene_id`.
- `ride_hailing.book`: `schedule_time` omitted or at/before context current time becomes an immediate booking (no scheduled timestamp stored). Catalog also mandates `vehicle` even if natural request omits it; use ASK if neither instruction nor context safely resolves it.
- `food_delivery.place_order`: menu item existence is checked in app code; unknown item makes a business no-op. Default `payment` is `cash`. Adding an unsupported or unasked optional value can change a submitted call or final state.
- `App.read`: text filters use Vietnamese diacritic folding and substring matching; multiple hits and empty results must be handled, not first-match guessed.
- `App.contact_ref`: phone lookup only fills contact ID when **exactly one** contact matches; ambiguous duplicates remain unresolved.

## 5. Canonical state hash: what it proves and what it does not (`VERIFIED-IN-KIT`)

`zaic_tools.utils.canon(state)` **removes recursively** free-text keys named `address`, `body`, `content`, `dropoff`, `expression`, `label`, `location`, `name`, `note`, `pickup`, `subject`, `title`, and removes information apps `exchange_rate`, `fuel_price`, `gold_price`, `lottery`, `weather` from the compared state. It lowercases/collapses whitespace in other strings and collapses number-plus-unit whitespace. Scalar lists are sorted; lists of objects retain their order. Hash is SHA-256 over sorted compact JSON of that canonical state.

**Consequences:** Two semantically different calls may lead to the **same** hash if differences are only in excluded free-text fields or read-only information apps. Conversely a wrong write can fail the state condition even when tool names matched. Therefore evaluate **both** predicted call arguments/sequence and final state; never use hash equality alone as a correct score. The official F1 implementation and exact hash/F1 gate are NOT in this upload, so their relative weight and fuzzy threshold remain UNKNOWN.

## 6. Concrete acceptance tests to implement first

1. `test_validate_does_not_log`: snapshot `env.get_tool_calls`, call `env.validate`, assert no new call (authorized train fixture).
2. `test_failed_call_stays_logged`: attempt an intentionally schema-invalid call on a **synthetic** `Session` fixture, assert identical state/hash and a logged call.
3. `test_xref_not_enforced_by_validate`: valid-format nonexistent ID validates but action becomes `BUSINESS_NOOP`.
4. `test_nested_payload_preflight`: malformed `food_delivery.place_order.items[]` is blocked by **our** semantic preflight even if organizer schema validation accepts it.
5. `test_ask_required_fields`: omit `params` -> validation reject; valid ASK appends a meta call, hash unchanged.
6. `test_read_no_duplicate_write`: read → same write once → DONE; no retries after successful write.
7. `test_hash_ignores_freetext`: synthetic two states differing only in `content` hash equally; matching still requires argument checks (scorer unavailable).
8. `test_hash_order`: scalar arrays sorted, list-of-dicts order preserved, per SDK canon.
9. `test_ride_schedule_boundary`: past/current scheduled time omitted in stored ride versus future time retained.
10. `test_absent_public_catalog_guard`: do **not** silently reuse train catalog as public/private truth when split catalog exists or is required.
11. `test_history_not_replayed`: history tool calls not executed a second time.
12. `test_submission_exact_trace`: serializer emits exact env log/hash; no fabricated fields or edits.

All state-fixture tests should use a self-generated synthetic environment/session or authorized train Toolkit calls. They must **not** parse the provided `<split>_environment/` files directly.

## 7. Issues still unresolved / research tasks

| Priority | Unresolved question | Resolution mechanism |
|---|---|---|
| P0 | Official scoring formula and fuzzy threshold, argument equivalence, matching order and multi-set handling | Organizer evaluator/rule text; scoring source or organizer clarification; participant formula only a labeled proxy |
| P0 | Public/private split tool catalogs and SDK differences | Inspect authorized local `public_test_tools_catalog.json`, public-test SDK; compare, without reading environment files |
| P0 | Docker entrypoint/mount/output path, GPU time, parameter budget and allowed model revisions | Official Submission Guidance and updated Rule tab |
| P0 | Gold train-label replay parity (all 1545, including semantic no-op and ASK) | Local train.jsonl + **ONE fresh train ToolEnv per scenario in replay**; compare label.tool_results and final_state |
| P1 | Actual per-tool read/write/multi-step/error frequency and gold ASK/[] prevalence | Authorized labeled **train** records only |
| P1 | ASR noise and critical-slot loss | Authorized train audio vs train `audio_text`, paired dev run |
| P1 | Generalization to public-only apps | Compare split catalogs; never use public/private examples as training labels |

## 8. External context, separate from kit verification

- Official track overview: https://challenge.zalo.ai/portal/lifemate (voice → stateful tool execution, ASK and `[]` behavior).
- Public participant research (NOT official scoring rules): https://github.com/Nguyen-Le-Tuan/ZAIC_2026 and https://github.com/MrPickle200/zalo-ai-2026-lifemate.
- Training framework reference: https://huggingface.co/docs/trl/sft_trainer (`assistant_only_loss` with compatible chat template).

**Do not copy the SDK, `state_hash` implementation, catalog or raw dataset into the submission repository.** The coding agent should inspect/execute the organizer-provided local package through its sanctioned APIs.


## 9. Executed synthetic contract verification (2026-11-09)

We extracted **only SDK Python files and train catalog** to an isolated temporary directory (no real sample states, labels or audio), then ran `tools/verify_sdk_contract.py` against the actual train SDK. **Result: PASS — 8 checks.**

1. All **147 catalog tools** are implemented in the train SDK tool registry (0 missing).
2. `env.validate` does not add to the call log.
3. An unknown `x-ref` device ID passes schema validation but yields `ok:true,done:false` when executed.
4. `food_delivery.place_order` with an `items` object missing nested required fields passes SDK `validate`, then business-noops.
5. ASK with missing `params` fails schema validation; valid ASK returns `waiting_for_user`, with the same hash before/after.
6. A past `ride_hailing.book.schedule_time` results in an immediate ride without a saved schedule timestamp.
7. A schema-invalid executed call is still logged.
8. Two synthetic states differing only in message `content` produce the same canonical hash.

**Scope limitation:** These are *synthetic contract checks*, not accuracy results, scorer parity, real-data replay, or an end-to-end model benchmark. Run against complete authorized train/public kits locally for integration coverage.
