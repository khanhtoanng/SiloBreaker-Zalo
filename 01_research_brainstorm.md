# LifeMate 2026 — Research, Brainstorm, and Scoring Risk Register

**As of:** 2026-11-09 (Asia/Ho_Chi_Minh)  
**Role:** Pro Researcher + Technical Architect  
**Scope:** LifeMate track only; this is research evidence and a decision log, not an authoritative rules replacement.  
**Inputs:** `LifeMate_AI_Research_Handoff(1).md` (user's proposal) and `data.md` (organizer data/API description provided by user). **Neither file supplies the actual raw train/public-test assets or runnable SDK.** All dataset-specific claims below originating from participants must be verified locally when the kit becomes available.

## 1. Executive technical recommendation

Use a **hybrid, observation-conditioned, offline agent**:

1. Local Vietnamese ASR transcribes the latest spoken user turn *and relevant earlier spoken turns*.
2. Runtime catalog/context/history are assembled without examining simulator-state files.
3. A sub-5B LLM chooses **one next action at a time** from `CALL`, `ASK`, or `DONE`; goals and tool observations remain in context.
4. Deterministic code resolves arithmetic/time safely, validates JSON-schema extensions, checks reference provenance, enforces an execution budget, and calls the **one official `ToolEnv`**.
5. Append actual ToolEnv observations; repeat decision making until complete or budget exhausted; serialize *actual* `env.get_tool_calls()` and `env.get_state_hash()`.
6. Train the action model on **gold tool trajectories, not only text-to-final-list pairs**; benchmark against a text-only baseline before investing in ASR or LoRA.

The largest likely sources of avoidable zeros are incorrect state-mutating writes, wrong/missing ID provenance, missing dependent steps, premature DONE, ambiguity handling, and unsupported-tool guesses. Do **not** promise a target leaderboard score without evidence.

## 2. Rules and evidence status

| Claim | Evidence | Status / action |
|---|---|---|
| Input = audio + context + history + installed runtime JSON-schema tools | Official portal; user's `data.md` | **Supported** |
| Output = ordered tool calls + hash; `sys.ask_missing_info`, `[]` supported | Official portal; user's `data.md` | **Supported** |
| One official ToolEnv per inference sample; no direct read/parse of `<split>_environment/`; rejected calls logged | User's `data.md` | **Provided data contract; verify installed SDK** |
| `x-ref`, `x-match: fuzzy`, `x-one-of`, read/write/meta `kind` | User's `data.md` | **Provided data contract; verify SDK semantics** |
| Score: gold `[]` iff predicted `[]`; otherwise wrong hash or zero matches => zero; else matched-call F1; unordered call matching with multiplicity | Nguyen-Le-Tuan participant rule transcription | **Participant-reported; obtain official Evaluation implementation** |
| <5B LLM, <6B total model parameters, <=16,384 context tokens; A30 24GB, 30s per sample; local-only inference; release cutoff 2026-10-26 | Participant transcription / handoff | **Unverified numeric rules: official Rule tab or kit is authoritative** |
| Official deadline Docker 2026-11-16 23:59 +07 and private-test period November 20–23 | Competition home page | **Official public schedule** |
| Local dataset counts train 1,545 / public 634 and app overlaps | Independent participant reports, not supplied raw dataset | **Verify by parsing authorized manifests** |
| Participant claims official clarification permits synthetic data from public catalog | One participant journal | **Do not assume permission without direct organizer/kit verification** |

**Rule conflict precaution:** `data.md` explains that ToolEnv returns `ok: false` for invalid inputs. A participant further reports `ok: true, done: false` can indicate business failure (e.g., missing balance), and that `validate()` does not log. Treat these as testable SDK behavior; never infer success from `ok` alone.

## 3. Peer evidence: what is reproducible and what is not

**Leaderboard caveat:** The LifeMate leaderboard is dynamically rendered and was not reliably extractable into a verifiable current team-to-method mapping. Public GitHub/Hugging Face projects below are **participating implementations**, not proven top-placed teams. No link found proving how current top teams achieve their score.

| Public project | Specific publicly stated observation | Decision for us | Caution |
|---|---|---|---|
| [Nguyen-Le-Tuan / ZAIC_2026, JOURNAL](https://github.com/Nguyen-Le-Tuan/ZAIC_2026/blob/main/JOURNAL.md) | Self-reported public progression 25.93 → 35.24 → 45.39 → 46.29 → 51.16; on a later ASR trial, lower WER coincided with lower public score (49.65) | Track end-to-end score rather than WER or training loss; use paired tests | Many changes across runs; public scores self-reported, not controlled comparison |
| Same journal, dataset audit | Reports 11 public-only apps; ~294/1020 calls use history-only IDs; read calls counted by call-F1; 217 ask calls occurred at the end; legitimate duplicate writes exist | Runtime schema grounding, preserve history tool results, train ask/read/STOP behavior and repeat-write handling | Counts from one participant's inspected kit/version |
| [MrPickle200 / INSIGHTS](https://github.com/MrPickle200/zalo-ai-2026-lifemate/blob/main/INSIGHTS.md) | On a deliberately hard 30-sample set, providing correct first gold call still led to wrong second tool in 24/30 | Train/evaluate next action conditioned on actual tool observation, not just top-level intent | Selected difficult subset, not population prevalence |
| Same INSIGHTS | Hard tool shortlist excluded at least one gold tool for 20/38 regression samples; local retrieval proxy improved while public result worsened | Keep full eligible tool set in v0; optional *soft* few-shot only after held-out verification | Self-reported results, not verified leaderboard leader |
| Same INSIGHTS | One experiment with extended cap generated extra calls without state improvement | Stop/goal completion matters more than simply raising max tool calls | Tool cap should match train distribution AND runtime |
| [Neeze / lifemate-zac2026](https://huggingface.co/Neeze/lifemate-zac2026) | Self-described PhoWhisper-large FT + Qwen3-4B LoRA r16 + text normalization + guards; dev 61.52 and public 49.03 | Evaluate LoRA on gold observation trajectories; allow ASR-noise + schema-name augmentation as later ablations | Dev/public gap; model's `License: other` is not permission to reuse another team's weights |
| [AIVIETNAM-AIO-Dewey baseline](https://github.com/AIVIETNAM-AIO-Dewey/Zalo-AIC-2026-Lifemate) | Reports train gold replay 1,545/1,545 matched; prioritized transcript-first baseline | Gold replay/evaluator integrity before tuning | Not an authoritative scoring implementation |

**Research inference:** End-to-end state/hash accuracy, argument grounding, deciding the next action after observations, and robust ASK/STOP behavior are higher-priority experiments than swapping orchestration frameworks. This is a hypothesis until our own ablations demonstrate the gains.

## 4. Architecture options

| Option | Description | Strengths | Risks | Recommendation |
|---|---|---|---|---|
| A. Minimal LLM + Python loop | LLM chooses next call; runtime validator + ToolEnv | Small, auditable, low overhead; baseline fast | Little explicit progress tracking; easy premature STOP | **Build first** |
| B. LangGraph/LangChain agent | Graph nodes for ASR, decisions, tools, recovery | Useful for tracing and complex orchestration | Extra abstractions do not intrinsically improve call correctness; version/runtime overhead | **Defer unless A becomes unmanageable** |
| C. Hybrid policy + deterministic guard (chosen) | A plus goal ledger, reference store, time/number helper, observability, schema-grounded validation | Controls costly mistakes while letting LLM generalize to new tools | Overzealous rules can delete legitimate gold calls or change gold conventions | **Build incrementally with per-guard ablations** |

## 5. Main functions to implement (developer contract)

| ID | Main function | Purpose | Primary module | Priority |
|---|---|---|---|---|
| F01 | `load_sample_and_catalog(split, id)` | Read manifest/catalog, installed-tool intersection, metadata (not raw app state) | `data_loader.py` | P0 |
| F02 | `transcribe_request_and_history(sample)` | Local ASR for latest and user-history WAV | `asr.py` | P0 for full e2e; transcript bypass in baseline |
| F03 | `normalize_utterance(text, context)` | Safe numbers/times/negation correction without inventing values | `normalizer.py` | P1 |
| F04 | `build_decision_context(...)` | Schema-grounded prompt, history results, provenance, constraints | `context_builder.py` | P0 |
| F05 | `propose_next_action(context)` | Model produces one of CALL/ASK/DONE | `policy.py` | P0 |
| F06 | `validate_proposal(decision, catalog, env)` | Parse/shape/enum/one-of/ref checks; dry-run `env.validate` | `validator.py` | P0 |
| F07 | `execute_and_observe(decision, env)` | Official tool call, real observation, no trace forgery | `toolenv_adapter.py` | P0 |
| F08 | `update_goal_ledger(...)` | Track pending/achieved/blocked goals from evidence | `agent_loop.py` | P1 |
| F09 | `run_agent_loop(sample)` | Bounded iterative stateful execution/stop/ask/time guards | `agent_loop.py` | P0 |
| F10 | `serialize_submission(env, id)` | Actual logged calls + actual hash; exact JSONL | `submission.py` | P0 |
| F11 | `replay_gold_train(sample)` | Reconstruct teacher-forcing observations using permitted train ToolEnv | `trajectory_builder.py` | P0 for SFT |
| F12 | `score_and_diagnose(pred, gold)` | Independently tested gold-hash/F1 proxy, failure taxonomy, paired reports | `evaluation.py` | P0 |
| F13 | `train_policy_lora(trajectories)` | Per-decision SFT (including ASK and DONE) | `train_lora.py` | P1 |
| F14 | `benchmark_offline_container()` | End-to-end 30s/A30/parameter/license/offline checks | `benchmark.py` | P0 |

## 6. Score-sensitive edge-case catalogue

All examples below are **constructed regression tests**, unless explicitly identified as official sample. Do not assume their exact gold tool sequence; infer test oracle from **the authorized training labels** and real runtime schema. Use the table as scenario coverage and expected semantic behavior.

| ID | Edge case / Vietnamese example | Failure mode | Expected behavior / test assertion | Score risk |
|---|---|---|---|---|
| E01 | `Bật điều hòa phòng khách 26 độ` with no device ID | Hallucinated x-ref | Read available tool status before write unless valid ID is already in trusted history; use returned ID | Hash-zero |
| E02 | `Gửi tin cho Minh` and two contacts named Minh | Wrong recipient | Search; do not pick arbitrarily; ask required `contact_id` if unresolved | Hash-zero / ASK |
| E03 | `Chuyển mẹ 500 nghìn` | Amount transcribed `50 nghìn` or wrong saved contact | Preserve amount 500000 and identify legitimate recipient, ask when ambiguous | Hash-zero |
| E04 | `Đặt xe về nhà` with missing home address | Guessed address | Use profile if available; otherwise `ask_missing_info` matching runtime schema | ASK/hash |
| E05 | `Đặt taxi` while only bike_rental exists | Semantic nearest-tool substitution | No equivalent app: `[]` if no eligible action | Empty-gold |
| E06 | `À thôi, đừng đặt xe nữa` | Negation/cancellation ignored | Detect correction/negation; do not place ride order | Empty-gold / hash |
| E07 | `5 giờ, à không, 5 rưỡi` | First spoken number chosen | Interpret correction as final 17:30 or 05:30 only if temporal context resolves; otherwise ask | Hash-zero |
| E08 | `thứ tư trừ ba tiếng`, `45 phút nữa` | Bad arithmetic, midnight/date rollover | Timezone-aware deterministic calculation relative to `context.current_time` | Hash-zero |
| E09 | `tắt hết đèn tầng một` | One light mutated, others ignored | Read all relevant devices then write each applicable device; no phantom devices | Hash-zero |
| E10 | `bật đèn rồi đặt xe` | Premature DONE after first write | Maintain two pending goals and finish both | Hash-zero |
| E11 | `nếu trời mưa thì hủy lịch` | Unconditional cancellation | Read weather, branch on actual result; if no rain do not cancel | Hash-zero |
| E12 | Tool returns `ok:true, done:false` | Treat business failure as success | Inspect `done`/details; do not assume write succeeded | Hash-zero |
| E13 | `env.validate` rejects a required field | Invalid call still executed | Repair proposal before `env.call`; invalid proposals must not enter log | Call-F1 |
| E14 | `x-one-of: contact_id OR phone_number` | Validator only checks JSON required keys | Enforce vendor extension or rely on actual `env.validate` | Call-F1 |
| E15 | Optional `brightness` invented when user asks `bật đèn` | Excess optional parameters | Prefer minimal supported args; benchmark vs labels; do not erase required state mutations | Call-F1 / hash |
| E16 | Read tool called with needlessly restrictive filter | Wrong observed list or mismatched gold read | Prefer train-evidenced conventions only where they preserve necessary result coverage | Call-F1 |
| E17 | Same write twice to buy two tickets | Unsafe dedup | Preserve distinct intentional writes; only suppress duplicate *accidental* writes with proof | Hash-zero |
| E18 | Repeated read with identical unchanged context | Unnecessary extra tool call | Avoid redundant read when observation remains authoritative; do not forbid legitimate refreshes | Call-F1 |
| E19 | User refers to contact ID from assistant tool result in history | History result dropped | Preserve tool-result IDs; don't hallucinate again | Hash-zero |
| E20 | History contains assistant instructions conflicting with latest correction | Wrong priority | Latest request and valid temporal ordering govern | Hash-zero |
| E21 | Missing info only after some successful steps | ASK too early/late | Complete determinable work first if labels/schema indicate; then `sys.ask_missing_info` | Call-F1 / hash |
| E22 | `[]` classification for a request already completed/changed in history | Unnecessary writes | Use available prior actions and request interpretation; learn abstention convention from gold | Empty-gold |
| E23 | Unknown app with schema similar to known tool | Tool-name memorization | Read runtime description/args, call eligible unseen app by schema | Hash-zero |
| E24 | Similar names but different tool `kind` | Read tool mistaken for write | Reason from kind, descriptions, return fields and requirements | Call-F1 |
| E25 | Free text with fuzzy match, accents or punctuation | Unnecessary exact-match repair | Preserve meaning and required fields; use NFC normalization where scorer does | Call-F1 |
| E26 | Audio speaker uses Central/South dialect or English insertion | Wrong verb/slot | Evaluate dialect and critical-slot accuracy separately | Hash-zero |
| E27 | History has many WAV turns (up to reported 24) | Too slow, missing crucial last context | Budget ASR; preserve last intent and history tool-result references; measure runtime | Timeout/hash |
| E28 | Six real gold calls + terminal DONE | Loop cap of five incl STOP | Configured cap allows 6 official calls + terminal decision; benchmark over-call risk | Hash-zero |
| E29 | Tool call fails with uncertain side effect | Duplicate transfer/order retry | Do not retry non-idempotent writes without explicit reliable failure evidence | Hash-zero |
| E30 | Tool is installed globally but not in sample's installed apps | Forbidden tool call | Strict per-sample intersection of runtime catalog and installed permissions | Call-F1 |
| E31 | Wrong split `zaic_tools` module loaded | SDK difference and hash mismatch | Split-aware isolate/load; verify import path and kit version | Hash-zero |
| E32 | `state_hash` recomputed from label/state files | Integrity violation | Always obtain hash from the *same* `env` that actually executed calls | Invalid submission |
| E33 | Public audio/transcript reused as training labels | Data contamination | Train only on authorized labeled train; never pseudo-label public/private audio | Eligibility |
| E34 | Mid-sample time budget exhaustion | Missing/partial actions, invented trace | Stop safely; preserve actual logged calls/hash and valid line; measure cutoff | Timeout/hash |
| E35 | Model JSON contains extra free-text wrapper/trailing invalid JSON | Parse failure | Typed output or single bounded repair before ToolEnv execution | Call-F1 |
| E36 | Some requested app available, another unavailable | Blanket `[]` vs partial execute mismatch | Derive behavior from train gold and exact organizer docs; do not assume either policy | UNKNOWN |
| E37 | 2 different contacts share identical text names + history resolution | Ambiguity incorrectly asked | Prefer unambiguous ID already grounded in history rather than ASK | Call-F1 |
| E38 | Timezone omitted vs different than machine locale | Wrong timestamps | Use sample's timezone; do not use host wall-clock time | Hash-zero |

### Prioritization: score-risk × evidence × build cost

**P0 before training:** E01, E02, E05, E06, E09–E16, E19, E21–E24, E28–E34.  
**P1 after reliable baseline:** E03–E04, E07–E08, E17–E18, E20, E25–E27, E35–E38.  
Do not assume an edge case has high train/private frequency; slice validation reports must quantify prevalence and fix impact.

## 7. Experiment hypotheses (all falsifiable)

- **H1:** LoRA trained on `(history + actual previous observations) -> next action` improves next-tool, argument, and final-state correctness relative to list-at-once SFT under the same base model/split.
- **H2:** Schema/name perturbation on **train-derived** trajectories improves leave-app-out score without harming in-distribution tool selection.
- **H3:** A goal ledger reduces premature DONE and missing multi-goal writes, with no extra-call F1 regression.
- **H4:** Source-grounded ID validator reduces wrong-hash outcomes without suppressing valid history-ID references.
- **H5:** Fine-tuning ASR or injecting mild ASR-like noise improves end-to-end downstream score, even if WER changes only slightly.
- **H6:** Native function-call templates vs typed JSON produce materially different parser validity, latency, and end score; choose by controlled runs, not framework preference.
- **H7:** Hard shortlist of runtime tools causes unseen-app recall loss; keep all eligible tool schemas unless controlled held-out improvement is demonstrated.
- **H8:** Targeted `ASK` and `[]` training improves their exact classifications without inducing overly frequent early refusal.

## 8. Questions requiring evidence / user decisions (kept OUT of intent.md and spec.md)

1. **Official kit accessibility (blocking for code-level verification):** Can the coding agent access `train/`, `public_test/`, `zaic_tools/`, official README, official scoring validator and the Rule tab? `data.md` alone is not enough to confirm scorer parity or package API edge behavior.
2. **Compute (affects model path, not spec):** What local GPU and VRAM are available for training and inference? Is paid cloud GPU permissible? Default: small ASR + quantized 4B for baseline; move to 1.55B ASR only after measured win.
3. **Submission/release rule:** Confirm image entrypoint, exact `/data` mount, result path, artifact deadline, model release/license policy, GPU warmup and time accounting from official kit (participant reports can conflict).
4. **Gold score implementation:** Do matching and final hash follow the participant transcription exactly? Obtain official evaluator or organizer clarification; keep evaluator marked PROXY until confirmed.
5. **Synthetic training data permissions:** Explicit organizer confirmation before using public test schema to generate synthetic *training* data; until then, only use authorized train.
6. **Split-specific partial execution conventions:** When some tasks are unsupported or missing info, infer from training labels and verify against official rules rather than inventing a universal policy.

**Default approach:** Proceed with code scaffold + train-only local evaluator and transcript-only baseline while the above checks are resolved. Do not block the first three implementation stages on GPU choice.

## 9. Direct sources, checked November 9, 2026

**Primary:**
- https://challenge.zalo.ai/portal/lifemate — official task + example (dynamic Rule/Evaluation details not fully readable by crawler).
- https://challenge.zalo.ai/ — official calendar.
- User supplied `data.md` — data format and ToolEnv contract (not the actual runnable kit).

**Public participants / secondary:**
- https://github.com/Nguyen-Le-Tuan/ZAIC_2026/blob/main/JOURNAL.md — detailed participant-reported scoring rules, train catalog audits, failure modes, test and Docker experiments.
- https://github.com/MrPickle200/zalo-ai-2026-lifemate/blob/main/INSIGHTS.md — selected hard cases, next-action and retrieval/latency ablations.
- https://huggingface.co/Neeze/lifemate-zac2026 — self-reported pipeline and dev/public results.
- https://github.com/AIVIETNAM-AIO-Dewey/Zalo-AIC-2026-Lifemate — baseline and gold replay report.

**Libraries/models:**
- https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507 — Apache-2.0, 4.0B, non-thinking model. Native context exceeds competition cap; **enforce competition cap**.
- https://huggingface.co/vinai/PhoWhisper-medium and https://huggingface.co/vinai/PhoWhisper-large — BSD-3-Clause Vietnamese ASR choices.
- https://huggingface.co/docs/trl/sft_trainer — tool-call dialogue format, tools column, assistant-only loss and masking compatibility.
- https://huggingface.co/docs/peft/main/en/conceptual_guides/lora — LoRA.
- https://github.com/QwenLM/Qwen3/blob/main/docs/source/framework/function_call.md — function-call/chat format.
- https://docs.vllm.ai/en/latest/features/structured_outputs/ — structured decoding, version-sensitive.


## 10. Post-research source audit: actual train SDK v3.2.0 (2026-11-09)

The user subsequently uploaded a 71 KiB SDK/docs extraction from the official package. This is **stronger evidence than public peer implementations** for train-split semantics. Exact findings and code paths are in `KIT_VERIFIED_FINDINGS.md`; 54 actionable regression tests are in `SCORING_EDGE_CASES.md`.

- `VERSION`: v3.2.0, 1,545 train, 634 public-test items.
- `train_tools_catalog.json`: 46 apps/147 tools; 68 typed reference annotations and 40 fuzzy text annotations.
- `ToolEnv`: logs failed executions; `validate` is side-effect-free; canonical hashing omits a defined set of free text keys and read-only information apps; business no-op is often `ok:true,done:false`.
- **Novel high-risk finding:** SDK schema validation is shallower than declared nested JSON Schema, and `x-ref` is advisory metadata. The agent must implement its own nested/semantic preflight without assuming the SDK will catch failures.
- **Research caution:** This extraction does **not** contain the official scorer or public-test catalog/SDK. All call-F1/fuzzy-threshold rules remain externally reported and must not be promoted to official verification.

**Recommendation update:** Keep the Python loop + Qwen next-action model + deterministic preflight, but move `BUSINESS_NOOP` detection and reference provenance ahead of generic LLM fine-tuning in the backlog. Use the local train gold replay as the first executable correctness gate.
