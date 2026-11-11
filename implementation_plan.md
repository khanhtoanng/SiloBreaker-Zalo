# Implementation Plan — LifeMate Score-First Delivery

**Prepared:** 2026-11-09 (Asia/Ho_Chi_Minh)  
**Roles:** Technical Architect (acceptance and tradeoffs), Coding Agent (implementation), Research/Evaluation Agent (evidence and experiments).  
**Read before coding:** `KIT_VERIFIED_FINDINGS.md` → `intent.md` → `spec.md` → `SCORING_EDGE_CASES.md` → `implementation_plan.md`. The train SDK/catalog is now source-inspected (v3.2.0); official scorer and public-test SDK are still unavailable in the review ZIP.  
**Hard milestone from official competition site:** Docker submission by **2026-11-16 23:59 GMT+7**; private test afterward (November 20–23). The detailed runtime limits are still pending kit-level verification.

## A. Delivery strategy and dependency graph

```text
P0 Rule/API audit ──> P1 Gold replay + frozen train holdout ──> P2 Scorer
       |                           |                              |
       +────────> P3 Text-only next-action baseline <─────────────+
                              |
                       P4 Score-risk guards
                              |
               +--------------+---------------+
               |                              |
         P5 Real-audio ASR              P6 SFT/LoRA trajectories
               |                              |
               +---------------+--------------+
                               |
                    P7 Paired ablations + freeze
                               |
                     P8 Offline Docker + audit
```

**Parallel from day 1:** create a minimal Docker shell/entrypoint and verify offline dependency installation; do not postpone packaging until after model training. Build a working baseline first, then decide which ML experiments can still finish before the deadline.

## B. Work backlog with exact completion gates

### P0 — Kit and scoring audit (must-build; partially source-verified)

**Completed by code inspection + eight synthetic contract checks:** `VERSION` v3.2.0; 1,545 train / 634 public_test counts; train catalog v2.7.0 (46 apps/147 tools); Session/ToolEnv API; schema rejection rules; canonical hash behavior; `sys.ask_missing_info`; no-op semantics. See `KIT_VERIFIED_FINDINGS.md`.

**Still required before full P0 pass:** run tool catalog comparison against complete local public-test SDK/catalog, replay gold labels, source/read official scorer or explicitly mark PROXY, and verify final Docker/hardware/rules. This small ZIP is SDK-only; do not call P0 complete.


**Goal:** Convert assumed rules into executable local truth. No model training until this audit is readable.

**Tasks**
- [ ] Locate actual authorized `train/`, `public_test/`, split catalogs, split `zaic_tools`, official README, sample submission, official checker/evaluator and Docker instructions.
- [ ] Read official Rule/Evaluation and record hard model/parameter/release/latency/network constraints; reconcile differences from participant journal.
- [ ] Inspect schemas of **all** tools in authorized catalogs, including `kind`, nested JSON-schema properties, `x-ref`, `x-match`, `x-one-of` and `returns`.
- [ ] Confirm `env.validate()` is log-free; exercise valid, schema-invalid, missing ID, insufficient funds, one-of alternatives, read/write/meta with test fixture train IDs only.
- [ ] Confirm whether a successful `ok` can coexist with business `done:false`; identify tool result success semantics.
- [ ] Confirm ASR history record shape, exact installed-app intersection, per-split importer, hash getters and call log shape.
- [ ] Record counts/number of calls/seen vs unseen apps directly from local authorized manifests; don't substitute participant counts.
- [ ] Confirm whether the organizer provides scorer, command-line validator, Docker mount and output path.

**Deliverable:** `docs/rules_audit.md` containing official source citation/kit version + observed API behavior, a list of proven vs unproven claims and adapter decisions; `scripts/audit_kit.py` read-only on permitted inputs.

**Pass:** One smoke sample can instantiate exactly one ToolEnv, perform an allowed read, get a real logged trace and hash; no code reads `<split>_environment/`. **Stop and request user/organizer evidence** if no kit is accessible; otherwise continue to implement scaffold with explicit unverified statuses.

### P1 — Deterministic gold replay and frozen evaluation split (must-build)

**Tasks**
- [ ] Parse authorized train JSONL; set frozen seed and group split by original sample ID **before** trajectory expansion.
- [ ] Add a second leave-app-out holdout where enough training data exists; report eligible sample counts and coverage.
- [ ] Implement gold replay through fresh **train** ToolEnv per sample/run, capturing the actual observations and hash through permitted APIs.
- [ ] Compare returned observations to label `tool_results`, replay outcomes to `label.final_state` where safely supported without directly reading environment files. Do not implement an independent hash algorithm.
- [ ] Persist fit/val IDs and SHA256 fingerprint of source training manifest/config; no public/private labels.
- [ ] Write invalid/missing/duplicate ID checks; never silently interpret an absent prediction row as a valid `[]`.

**Deliverables:** `scripts/replay_gold.py`, `configs/splits.json` (locally derived), `docs/replay_report.md`, strict data-loader unit tests.

**Pass:** 100% gold replay matches expected recorded results or clearly document/resolve official kit discrepancies; no held-out IDs in fit; zero unreadable train records.

### P2 — Scorer and failure taxonomy (must-build)

**Tasks**
- [ ] Prefer official scoring implementation; otherwise implement participant-described maximum one-to-one call matching, duplicate multiplicity, fuzzy thresholds, and hash gate as a **proxy**.
- [ ] Write fixtures: gold `[]`, matching `[]`, wrong hash, `M=0`, duplicate calls, missing/extra reads, extra optional fields, fuzzy threshold boundary, `sys.ask_missing_info`, invalid logged call, call order vs matching order.
- [ ] Collect first-tool/next-tool/complete-trajectory/state-hash/ASK/[]/runtime metrics and error tags as specified in `spec.md`.
- [ ] Generate a per-sample CSV/JSON report with a failure-reason summary and regression diff tool.
- [ ] Audit parity by comparing to official scorer when accessible; label local scores PROXY until established equivalent.

**Deliverables:** `evaluation.py`, `tests/test_scorer.py`, `docs/scorer_parity.md`, `scripts/evaluate.py`.

**Pass:** All adversarial scoring fixtures pass; no missing predictions incorrectly treated as correct empty predictions; exact official parity demonstrated OR evaluator visibly labeled approximate.

### P3 — Text-only next-action baseline (must-build, core control)

**Tasks**
- [ ] Create split-aware loader and installed-tool registry; no hardcoded app allowlist.
- [ ] Plug in Qwen3-4B-Instruct-2507 (local weights, no thinking), bounded context and deterministic decode; verify release/license before submission.
- [ ] For **train holdout only**, use provided gold `audio_text` as the user text to isolate decision quality from ASR.
- [ ] Assemble prompt from current time/zone/profile, latest text, earlier text, assistant history tool results, all allowed tool schemas with parameter descriptions and return summaries.
- [ ] Generate one CALL/ASK/DONE action; validate; execute real ToolEnv; append actual observations; repeat until DONE/ASK/cap/deadline.
- [ ] Record per-step prompt tokens, proposed vs actual calls, observations, validation errors and latency; diagnostics separate from submission.
- [ ] Keep a minimal local command and a sample end-to-end JSONL output.

**Deliverables:** minimal `src/lifemate` runtime, `configs/baseline.yaml`, `tests/test_agent_loop.py`, a frozen baseline score/report `E0`.

**Pass:** Complete held-out evaluation with **zero crashes and 100% valid output lines**, consistent ToolEnv integrity and actionable error breakdown. Low baseline score is acceptable at this stage; no training until it is measured.

### P4 — Deterministic, scoring-sensitive improvements (must-build; ablate individually)

Run changes separately against `E0` using same held-out IDs, transcripts, model, prompts and decoding settings:

| Experiment | Intervention | Target failure | Critical regression check |
|---|---|---|---|
| E1a | Strict parser + JSON-schema/`x-one-of` + `env.validate` before execution | Invalid or rejected calls | Valid relevant calls must not be suppressed |
| E1b | Typed ID provenance from history/live observations | Wrong recipient/device/account IDs | Valid references already in history must still work |
| E1c | Conditional goal ledger and DONE reconsideration | Missed second/third goals, premature DONE | Do not produce speculative extra writes |
| E1d | Minimal necessary optional arguments | Parameter mismatch | Don't strip parameters required for state or user intent |
| E1e | ASK vs DONE vs unsupported `[]` policy | Wrong ambiguity/abstention decisions | ASK and empty recall/precision both monitored |
| E1f | Safe retry & repeated-write policy | Duplicated purchases/transfers, suppressing legitimate repeat writes | Test both idempotent and deliberate repeat cases |
| E1g | Time and amount calculator | Wrong values and relative dates | Never override explicit user correction/negation |
| E1h | Full eligible tool list vs soft retrieval (optional) | Unknown app miss | No hard-pruning of necessary tools |

**Pass each:** Gain on local official-equivalent score **or** demonstrably prevent high-severity integrity errors without unacceptable aggregate/slice regression; if no win, revert or leave behind an opt-in experiment flag. Document positive and negative cases, not just mean.

### P5 — Real-audio path and ASR evaluation (core submission, tune only if indicated)

**Tasks**
- [ ] Use the same frozen holdout with gold transcript and local ASR transcription, paired by sample ID.
- [ ] Support user-turn WAVs inside conversation history; include per-sample total ASR time and chronological assembly.
- [ ] Baseline at least one legal local ASR candidate. Compare PhoWhisper-medium/large or Whisper-turbo only where compute allows; count combined params including adapters/auxiliary models.
- [ ] Analyze critical-slot errors: negation, money, amount, time/date, addresses, contact names, region/dialect, English insertion, self-correction.
- [ ] Keep sample time context independent of host clock; test midnight/weekday and half-hour expressions.
- [ ] Optionally fine-tune ASR **only on authorized train audio** after paired score evidence; choose best downstream score per second, not lowest WER alone.

**Deliverables:** `asr.py`, `normalizer.py`, report `E2_asr_oracle_vs_actual.md` with same model policy and paired inputs.

**Pass:** Real-audio inference produces valid call traces. End-to-end score and runtime delta versus oracle are quantified, with a minimum of one ASR model that fits time/parameter budgets.

### P6 — Trajectory-based LLM SFT/LoRA (central ML experiment)

**Tasks**
- [ ] Convert all authorized fit training samples into per-decision teacher-forced examples with real prior ToolEnv observations.
- [ ] Include per-step target: read/write tool call, `ASK`, or terminal DONE. Include no-tool samples and full installed runtime schemas.
- [ ] Verify one selected action format (custom JSON or Qwen native tool call) is identical in SFT and inference; test tokenizer roundtrip, masking, tools serialization.
- [ ] Log distribution of first/later/terminal actions, classes (including STOP), required IDs and tool apps to prevent overtraining on DONE or known tools.
- [ ] Train small Qwen3-4B LoRA pilot (e.g. r16, 1 epoch; learning rate/batch/length set from VRAM pilot), then evaluate **gold transcript** holdout before integrating ASR.
- [ ] Compare against (a) unmodified Qwen baseline, (b) optional full-list SFT, (c) per-decision SFT with same prompt and kit.
- [ ] Probe leave-app-out separately; check if improvement is only memorization of known app names.
- [ ] Save adapter/model/prompt/data split revisions and decision-specific error report.

**Deliverables:** `trajectory_builder.py`, `scripts/build_trajectories.py`, `scripts/train_lora.py`, `configs/lora.yaml`, `E3` evaluation and adapter.

**Pass:** Clear held-out **end-to-end** gain over E0/E1 on same evaluation protocol, or choose baseline instead. Training loss alone is never a passing result.

### P7 — Generalization and robustness trials (time-boxed, not a prerequisite for valid submission)

| Trial | Test question | Start condition | Keep only if |
|---|---|---|---|
| E4 schema/app renaming on train only | Can model use unseen tools? | Per-decision SFT viable | Leave-app-out improves without large known-app regression |
| E5 ASR-like text noise augmentation | Can model ignore innocuous transcription variation? | Real ASR loss is measurable | Actual ASR e2e improves without gold-text degradation |
| E6 synthetic error/ambiguous observations | Does recovery/ASK improve? | Official data generation permissions checked | ASK/branch/hash outcomes improve on frozen held-out |
| E7 native tools vs typed JSON | Which serialization produces better tool choice/runtime? | Both parsers run with same model & IDs | Official-equivalent score and runtime win, not just valid JSON |
| E8 soft few-shot retrieval | Do examples help without pruning needed tools? | E1/E3 baseline established | Score gain on holdout and zero tool-coverage regression |

**No-go:** unlicensed/after-cutoff model, public/private-label adaptation, hard-pruned unknown tools, extra external APIs during inference, creating replacement ToolEnv, or introducing LangGraph without a measured functionality need.

### P8 — Offline Docker and final submission (must-build)

**Tasks**
- [ ] Build image with local model weights, tokenizer, adapter, ASR, inference dependencies, single split-aware entrypoint; train scripts included if required by official rule.
- [ ] Verify `predict.sh` executable and **exact** organizer mount/output path/working directory; no startup-time hidden downloads.
- [ ] Run with network **disabled**, `HF_HUB_OFFLINE`/similar settings as appropriate; verify no HTTP inference dependency.
- [ ] Parameter totals, local model checkpoint publication cutoff, licenses, context cap, GPU memory, offline startup, seed/decoding all verified.
- [ ] Test on A30 24GB or authorized equivalent; measure **overall** p50/p95/p99/max and timeouts across representative long-history/6-call cases.
- [ ] Run exact manifest (all rows) twice and compare call traces/hash; investigate any nondeterminism (the official rules may average repeated runs).
- [ ] Validate missing/extra IDs, call-log fidelity, hash fidelity, encoding, JSONL fields/order and official validator.
- [ ] Freeze best candidate and record hashes of code/model/image/config; keep a known-good baseline container as fallback.

**Deliverables:** Dockerfile, `predict.sh`, `scripts/predict.py`, `docs/final_validation.md`, final `result/submission.jsonl` from test inference, reproducible image/checksums.

**Pass:** Official validator accepts entire sample set; image operates offline, within official latency/model limits, with no raw environment reads or invented output calls; repeated runs sufficiently reproducible.

## C. Prioritized edge-case test worklist

The IDs correspond to `01_research_brainstorm.md` and have **semantic** expected behaviors, not invented official gold labels.

| Priority | Cases | Why prioritize | Required automated assertion |
|---|---|---|---|
| Critical | E01, E02, E09, E10, E11, E19, E21, E23 | Wrong/missing dependent writes cause hash-zero | Correct observation-grounded IDs, complete goals, conditional branch, ASK after reads |
| Critical | E05, E06, E22, E30 | Wrong/extra calls can turn empty-gold correct result into 0 | No unauthorized substitute tools, cancellation respects latest speech |
| Critical | E12–E16, E18, E28, E31–E35 | Rejected calls, scorer mismatch, timeouts or SDK mismatch | Validate before call, no false-success, correct 6-call handling, actual trace/hash |
| High | E03, E04, E07, E08, E20, E26–E27, E38 | ASR/history/temporal wrong slot affects final state | Critical-slot assertions, time zone, self-corrections, long history |
| High | E17, E29, E37 | Accidental replay or wrong disambiguation | Legitimate repeat supported, unknown outcome not repeated, known ID reused |
| Medium | E24–E25, E36 | New-schema and fuzzy/partial unsupported conventions | A/B by gold labels, no hardcoded assumptions |

**Ordering rule:** Start with failures observed on local validation, then test generalization. Large hand-authored test suites without measured baseline error coverage are not substitutes for actual score improvements.

## D. Evaluation and experiment ledger

Create `docs/experiment_log.md` table as follows, one entry per run:

| Field | Requirement |
|---|---|
| `experiment_id` | E0, E1a, E2, E3, E4… |
| `hypothesis` | What exactly will improve and why |
| `dataset_sha`, `split_id`, `seed` | Freeze holdout and reproducibility |
| `model_revision`, `asr_revision`, `adapter_revision` | Exact weights/license/release date |
| `prompt_revision`, `code_commit`, `backend`, `decode` | Traceable runtime behavior |
| `hardware`, `max_context`, `sample_budget`, `params_total` | Compliance and latency |
| `score_kind` | `OFFICIAL`, `VERIFIED_EQUIVALENT`, or `PROXY` |
| `score`, `hash_match`, `call_f1`, `ASK`, `[]`, `late_tool_acc`, `runtime` | Results and subslices |
| `n_better`, `n_worse`, `n_tied`, `CI` | Paired comparison, confidence |
| `decision` | `KEEP`, `REVERT`, `RETEST`, `NO-GO` + rationale |

**Release gate:** Never pick a variant solely by a leaderboard number or a lower ASR WER. Pick on frozen train-derived end-to-end official-equivalent scoring, acceptable slice tradeoffs, and offline compliance. The public leaderboard is a final sanity check, not a source of labels or ongoing hyperparameter search.

## E. Proposed calendar (tight deadline; rescope when kit/compute becomes known)

| Day (Vietnam time) | Target checkpoint | Fallback if behind |
|---|---|---|
| **Nov 9** | P0 audit, source/data contract, Docker skeleton; freeze train split | Identify missing official files and proceed with pure unit tests only |
| **Nov 10** | P1 gold replay + P2 evaluator parity; artifact score fixture suite | Keep evaluator PROXY; no new ML claims |
| **Nov 11** | P3 transcript-only 4B baseline complete, per-sample error report | Reduce model/context, run smaller fixed diagnostic pilot then full holdout |
| **Nov 12** | P4 high-severity guards with controlled ablations; start real ASR integration | Keep only guards that prevent logged invalid attempts or show score gain |
| **Nov 13** | P5 real ASR oracle gap; P6 LoRA pilot begins if GPU available | Keep baseline; focus on correctness and ASR runtime |
| **Nov 14** | P6 per-decision LoRA score vs baseline; selective E4/E5 | No expensive unproven experiments; select known-best candidate |
| **Nov 15** | P8 complete offline Docker, A30/resource/latency and reproducibility smoke/full run | Freeze fallback model and optimize time budget/entrypoint |
| **Nov 16** | Submission validator, checksums, rule audit, final Docker delivery before official 23:59 cutoff | No late architectural rewrite; submit verified known-good version |

**Nov 20–23:** Run the frozen solution against private-test data under official rules. Do not adapt training to private test labels or inspect protected simulator state.

### Compute/time estimation (planning data, not a promise)

- The [Nguyen-Le-Tuan public journal](https://github.com/Nguyen-Le-Tuan/ZAIC_2026/blob/main/JOURNAL.md) reports **318–349 minutes** for ~4,050–4,874 per-step SFT rows on its specific RTX 4070 laptop 8 GB setup. This is a **peer observation**, not our forecast. Benchmark a 100–200-row pilot first to estimate our actual throughput.
- Size training from **number of decision steps**, not only source scenario count; teacher forcing expands each scenario into one example per gold call plus terminal DONE.
- Budget **at least one complete inference pass on the frozen holdout** after each promising checkpoint. End-to-end validation, not the SFT training run, selects the candidate.
- A30/30-second inference feasibility requires measuring **ASR latest + all history audio + iterative LLM turns + tool calls + serialization**. Model parameter count and 24GB VRAM are independent constraints; quantization reduces memory, not number of parameters.
- If a long training run threatens the November 15 Docker milestone, stop speculative experiments and release the best previously measured candidate.

## F. Go/no-go decision gates

| Gate | GO if | NO-GO if |
|---|---|---|
| G0 legal/runtime | Official kit contract, license/release cutoff and allowed data established | Need unauthorized data/network or rule remains contradictory for submission |
| G1 evaluator | Gold replay exact and scorer verified/equivalent or honestly labeled PROXY | Training/eval labels leak across splits; missing rows scored as `[]` |
| G2 baseline | All holdout samples processed, valid trace/hash, errors measurable | Agent produces fictional calls/hash or crashes |
| G3 guard | Fewer serious errors or paired score improvement without unacceptable regressions | Fix suppresses valid reads/writes or worsens end-state |
| G4 LoRA | Higher **paired end-to-end** score; unseen-app performance not sacrificed | Lower loss but unchanged/lower state score |
| G5 ASR | Better total e2e score under sample time and parameter limits | Better WER but lower downstream score or worse timeout |
| G6 release | Docker offline, correct paths/results, fits all limits and reproducible | Any hidden download, schema failure, forbidden access, unbounded latency |

## G. Local coding-agent task instructions (copy/paste)

> You are the implementation agent for Zalo AI Challenge 2026 LifeMate. Read `intent.md`, `spec.md`, `01_research_brainstorm.md`, `implementation_plan.md` in that order, then inspect the actual organizer kit. Implement phases P0→P8 with a score-first approach. Use only current-sample allowed runtime schemas, one official ToolEnv per inference sample and actual observed calls/hash. Do not read any environment state files. Implement gold replay/evaluator before ML fine-tuning. Each phase must ship tests, a small runnable command, metrics/evidence and a go/no-go report. Use authorized labeled train only; no public/private pseudo-labeling. The native model weights and every auxiliary model must meet official license, release and parameter limits. For conflicts with official rules, stop the conflicting implementation, update `docs/rules_audit.md`, and ask the human **a specific question with recommended default and impact**. Do not leave unresolved design questions inside `intent.md` or `spec.md`. Keep only tested score improvements; never fabricate metrics or claim leaderboard results without evidence. Finish with an offline Docker and manifest validator.

## H. What coding agent must return at each checkpoint

- **P0:** extracted rule diff, SDK findings, exact allowed-tool schema inventory and unresolved blockers.
- **P1/P2:** gold replay summary and scorer fixtures/parity report.
- **P3:** one command to run baseline; table of end-to-end and per-step errors.
- **P4:** before/after paired score and regressions per guard.
- **P5/P6:** paired ASR oracle gap, model SFT config/adapter provenance, next-step and final-state comparison.
- **P7:** evidence-driven KEEP/REVERT matrix.
- **P8:** offline test command, Docker digest, output validator evidence, timing/memory/model totals, final artifact checklist.

## I. Risks and the minimal viable fallback

1. **No official runnable kit:** Write parser/tests from supplied `data.md`, but **cannot** verify actual scoring, SDK semantics or output container. Escalate as one explicit blocker.
2. **No GPU or expensive training:** Use quantized legal 4B policy + small ASR and focus on strict execution, ASK/[] correctness, runtime-schema coverage and deterministic date/ID helpers. This may be low-scoring but is implementable.
3. **Training consumes deadline:** Freeze a text-only baseline by Nov 11 and real ASR + offline Docker by Nov 15; keep a known-good model as fallback.
4. **Generalization collapse:** If unseen apps lose score, undo tool-name memorization or retrieval shortlisting; keep full runtime schemas.
5. **High confidence in wrong calls:** Do not execute more tools just to appear useful; state/hash zero gate makes wrong writes expensive.
6. **Misinterpreted official rules:** Maintain verified vs reported separation; complete the official kit audit before choosing model or scoring claim.

**Additional references:** All URLs and provenance reside in `01_research_brainstorm.md`, not duplicated in the role documents.


## J. Post-review implementation priorities (2026-11-09)

**Source evidence:** user-uploaded v3.2.0 **train** SDK/catalog. Full results in `KIT_VERIFIED_FINDINGS.md`; canonical concrete regression tests in `SCORING_EDGE_CASES.md`.

| Stage | Immediate coding-agent task | Concrete pass condition | Evidence level |
|---|---|---|---|
| P0a | Build safe catalog inventory using `tools/audit_catalogs.py` on authorized local train/public dirs | Print true app/tool overlap and schema counts; no environment directory read | Not run here; train-only count statically verified |
| P0b | Gold replay on authorized train using one fresh `ToolEnv` per scenario | All 1,545 labels replay or every mismatch explained; compare tool results and changed app state | NOT RUN: labels absent from small ZIP |
| P0c | Check scorer implementation/Rule tab and record exact F1/arg matching | Actual parity fixtures pass or all metrics carry `PROXY` label | UNKNOWN |
| P1 | Implement `env.validate` + nested/reference preflight + separate success classifier | P0 K01–K13, K18, K25–K30, K35–K38, K45–K48, K53 pass | Design grounded in train SDK |
| P2 | Run text-only baseline with real authorized train ToolEnv | Output actual calls/hash, 100% rows, no crashes; retain per-case diagnostics | Requires local models/train |
| P3 | Paired ASR/oracle, then trajectory SFT | Improvements on **frozen** train holdout; log per-action and no-op regressions | Experiment, not verified |
| P4 | Freeze Docker/latency/licensing | Official resource/mount/output compliance verified | Requires organizer guidance |

### Critical implementation changes

1. **Never use `ok:true` as a blanket success signal.** Many business failures are `ok:true, done:false`; a normal successful write may have no `done` key.
2. **Do not confuse schema check with semantic check.** `x-ref` is not enforced by `env.validate`; nested object `required` is not recursively checked; unknown props may not reject. Add isolated semantic preflight before `env.call`.
3. **Hash match is not score parity.** Free-text fields and read-only information apps are dropped from canonical hash, but tool-call content may still be scored. Confirm official F1 rather than silently adopting participant threshold.
4. **System ASK is a real tool** requiring `tool_name` + `params`, and may follow completed independent goals.
5. **Catalog is per split, runtime tools per sample.** Public-test SDK/catalog was not included; use complete local kit via sanctioned paths and no hardcoded `train` tool registry.
6. **Use the SDK's own `get_state_hash` and log.** No second environment, hidden retries, call deletion, or submission forgery.
7. **Preserve user history without replaying history operations.** The initial simulator data already includes their effects.
8. **Prioritize the actual issue taxonomy** from `SCORING_EDGE_CASES.md` and regress every heuristic; suppressing an intended write can be as harmful as adding an extra read.

**Exit criterion:** Do not claim the revised pack is an evaluated solution. It is an implementable, kit-grounded specification awaiting authorized train scenario replay and target-GPU model evaluation.

**Executed synthetic evidence:** `tools/verify_sdk_contract.py` passed 8 SDK contract checks (no real state files opened, no model run); source details in `KIT_VERIFIED_FINDINGS.md`.
