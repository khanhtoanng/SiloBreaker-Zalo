# Score-Risk Edge Case Matrix — v3.2.0 Kit-Grounded

**Use:** implement a test for each case, with fixture source `synthetic` or `authorized_train`; never reuse private/public-test labels. P0 = correctness/integrity risk, P1 = likely score-risk, P2 = experimental. `KIT` = verified from train SDK/catalog; `POLICY` = proposed behavior requiring train holdout validation; `SCORER?` = exact score impact unverified until official scorer is available.

## A. Tools, schemas, and log integrity

| ID | Priority | Scenario / input | Expected agent or validator behavior | Evidence |
|---|---|---|---|---|
| K01 | P0 | Proposed app/tool absent from `installed_apps` | Do not execute; only per-sample allowed tools | KIT |
| K02 | P0 | Correct tool name but missing a `required` string | Block before execution; repair/ASK where appropriate; `env.validate` alone is log-free | KIT |
| K03 | P0 | Wrong enum e.g. `vehicle: taxi` instead of `car4` | Validate and reject pre-call | KIT |
| K04 | P0 | Amount sent as float/string or bool where schema says integer | Preserve integer type; validate/recover without trying an invalid call | KIT |
| K05 | P0 | Alternative `x-one-of` (`sms.send` `contact_id` or `phone_number`) | One valid nonempty group satisfies requirement; choose the grounded option | KIT |
| K06 | P0 | `x-ref` provided as a string but nonexistent in app state | `validate` may pass; read/ground before write; handle `done:false` | KIT + POLICY |
| K07 | P0 | `food_delivery.place_order.items = [{}]` | Extra nested semantic validator rejects before execution; SDK is not recursively strict | KIT |
| K08 | P0 | Unknown extra argument or explicitly empty optional argument | No hallucinated fields; optional omission differs from user-explicit value | KIT + SCORER? |
| K09 | P0 | Invalid call accidentally executed | Cannot remove from `get_tool_calls`; report and prevent repeats | KIT |
| K10 | P0 | Agent emits its own predicted call list/hash rather than actual log/hash | Must serialize only `env.get_tool_calls()` and `env.get_state_hash()` | KIT |
| K11 | P0 | Creating a new ToolEnv after a bad call | Forbidden reset; keep exactly one session per sample in inference | KIT |
| K12 | P0 | User history contains prior write tool calls | Do not execute them again; history changes already in initial state | KIT |
| K13 | P1 | Dynamic catalog differs between splits | Use selected split's catalog and SDK; do not assume identical tool names/semantics | KIT source layout, public catalog still missing |

## B. Reads, grounded IDs, and no-op results

| ID | Priority | Scenario / input | Expected behavior | Evidence |
|---|---|---|---|---|
| K14 | P0 | "Bật đèn phòng khách" with no `device_id` | Read smart_home devices, choose correct type and room, write once | KIT + POLICY |
| K15 | P0 | Two devices have same name across rooms | Ground room/floor/type from request and read results; clarify if unresolved | KIT + POLICY |
| K16 | P0 | `smart_home.get_status(room=...)` hides scenes | Use unfiltered read when scene resolution required | KIT |
| K17 | P0 | Bank beneficiary is missing/ambiguous | Read beneficiary IDs; no ungrounded transfer | KIT + POLICY |
| K18 | P0 | Bank balance insufficient | `ok:true, done:false` is not a successful transfer; no blind retry | KIT |
| K19 | P0 | `smart_home.light_set` given fan ID | May no-op despite schema pass; match device type | KIT |
| K20 | P1 | `contacts.search` yields 0, 1, multiple results | 0/multiple are not permission to guess; ASK when target unresolved | KIT + POLICY |
| K21 | P1 | Phone numbers `+84...` vs `0...` | Respect SDK contact equivalence when unique; no arbitrary reformat of target arg | KIT |
| K22 | P1 | Assistant needs ID returned only in earlier history tool result | Retain context reference index; never invent ID from filename | KIT + POLICY |
| K23 | P1 | Empty successful `list/get` result | `ok:true` with an empty collection is not a resolved target | KIT |
| K24 | P1 | Failed search followed by write with an assumed ID | Guard blocks ungrounded write; model chooses alternate search/ASK | POLICY |

## C. ASK, DONE, out-of-scope and multi-goal control

| ID | Priority | Scenario / input | Expected behavior | Evidence |
|---|---|---|---|---|
| K25 | P0 | ASK only has `params`, no `tool_name` | Block: both fields required in catalog | KIT |
| K26 | P0 | ASK refers to wrong target tool or nonexistent parameter | Do not invent `tool_name` or `params`; choose intended installed tool/parameter schema | KIT + POLICY |
| K27 | P0 | Out-of-scope utterance; no supported installed app | Return no calls (`[]`), use genuine unchanged state hash | Official overview |
| K28 | P0 | Two goals, first succeeds, second missing information | Preserve first executed call and then ASK for second goal's missing parameter | Official overview + POLICY |
| K29 | P0 | Two goals, first read completes but model stops | Enforce multi-goal ledger; require completion/ASK for every explicit subgoal | POLICY |
| K30 | P0 | Same write already succeeded; model tries retry | Do not execute duplicate mutation just to check result | POLICY |
| K31 | P1 | User explicitly asks for two identical reminders/payments | Do **not** universally deduplicate valid repeated actions; preserve intent | POLICY |
| K32 | P1 | Request negates or corrects previous command ("không bật... tắt") | Last explicit correction governs, no stale first write | POLICY |
| K33 | P1 | "chuyển cho mẹ" but beneficiary ambiguous | Prefer ASK after available safe reads, not a random recipient | POLICY |
| K34 | P1 | ASK vs DONE after partial multi-step success | Emit terminal decision only after each executable goal is resolved or explicitly blocked | POLICY |

## D. Time, money, normalization and domain specifics

| ID | Priority | Scenario / input | Expected behavior | Evidence |
|---|---|---|---|---|
| K35 | P0 | `ride_hailing.book.schedule_time == current_time` | Simulator stores immediate ride (omits schedule); avoid unintended schedule | KIT |
| K36 | P0 | `ride_hailing.book.schedule_time` is in the past | Simulator treats as immediate; handle against **sample** clock | KIT |
| K37 | P0 | Missing mandatory `ride_hailing.book.vehicle` | ASK or derive from explicit context; don't invent `bike/car4/car7` arbitrarily | KIT + POLICY |
| K38 | P0 | `banking.transfer.amount` parsed as `500` vs `500000` | Normalize Vietnamese units exactly; integer positive with no punctuation | KIT + POLICY |
| K39 | P1 | `calendar.create_event` without `end` | SDK's defaults apply; never fill an arbitrary end time | KIT |
| K40 | P1 | "mai", "thứ hai tới", "7 giờ tối" near midnight/DST or year boundary | Resolve using `context.current_time`/timezone, not machine time | POLICY |
| K41 | P1 | `food_delivery` menu ID valid for wrong restaurant | Get correct menu for grounded restaurant; item ID must exist there | KIT |
| K42 | P1 | `food_delivery.place_order` payment omitted | SDK defaults to `cash`; omit unless explicitly supported/wanted | KIT |
| K43 | P1 | `smart_home.climate_set` mode missing | `mode` required even with temperature; choose semantically supported mode or ASK | KIT |
| K44 | P2 | ASR misrecognizes negation, names, amounts or phone digits | Measure critical-slot accuracy and decision consequences with paired audio vs oracle | Research hypothesis |

## E. State hash vs tool-call equality and scoring proxy

| ID | Priority | Scenario / input | Expected behavior | Evidence |
|---|---|---|---|---|
| K45 | P0 | Same state, differing SMS `content` | Canonical state hash can match; arguments must still be evaluated independently | KIT + SCORER? |
| K46 | P0 | Two states differ only in `title/name/note/location` | Canonical hash can match; do not claim perfect score | KIT + SCORER? |
| K47 | P0 | Information-app query (e.g. weather) with no state mutations | Hash insensitive to live app data; read call still relevant | KIT + SCORER? |
| K48 | P0 | Added optional tool read that did not change state | Track excess logged call; predicted call sequence differs despite identical hash | KIT + SCORER? |
| K49 | P1 | Scalar collection order differs vs object list order | SDK canonicalizes scalar list ordering, but keeps object list ordering | KIT |
| K50 | P1 | Tool name correct but fuzzy-text phrase differs | Exact matching policy UNKNOWN; test via official scorer or labeled proxy, not hash alone | SCORER? |
| K51 | P1 | Read calls unordered in F1 but dependency read→write | Whether official F1 ignores order UNKNOWN; execution order changes outcome | KIT + SCORER? |
| K52 | P1 | Invalid call plus correct retry yields correct hash | Rejected call remains in log; F1 may penalize extra call | KIT + SCORER? |
| K53 | P0 | Missing prediction row, duplicate `id`, malformed JSONL | Fail submission integrity; not equivalent to a valid `[]` prediction | README + POLICY |
| K54 | P1 | Public-test tool absent from train catalog | Don't hard-prune; use public split registry when available | Split layout + POLICY |

## F. Test case structure (coding-agent contract)

For each ID create a regression test or audited train scenario with:

```yaml
case_id: K18
source: synthetic  # or authorized_train
fixture: banking.transfer with insufficient balance
inputs: {utterance: "Chuyển một triệu cho mẹ", observations: "balance=500000"}
expected_decision: "do not claim transfer complete; no duplicate transfer"
assertions:
  - "The wrong success classification is impossible"
  - "Every executed call appears in actual env.get_tool_calls()"
  - "The resulting state_hash is taken from env.get_state_hash()"
metrics: [business_noop_detected, wrong_write_rate, logged_extra_calls]
scorer_status: UNKNOWN  # until official scorer parity test
```

**Important:** Tests tagged `POLICY` describe proposals, not facts about the hidden gold labels. Measure both improvements and regressions on frozen train validation before merging heuristics. Keep test actions independent of raw environment state files; local ToolEnv is the only legal access to application state.

## G. Priority gate

- **P0 before first model training:** K01–K13, K18, K25–K30, K35–K38, K45–K48, K53.
- **P1 before final Docker:** remaining K14–K24, K31–K44, K49–K52 and K54, with explicit measured regressions; no overfitting to individual held-out cases.
- **Never claim exact scoring parity** from this small archive; the source does not contain the scorer implementation.
