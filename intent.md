# Intent — LifeMate Offline Voice-to-Action Agent

> **Kit audit status (2026-11-09):** Train SDK v3.2.0 verified by code inspection; 46 apps / 147 tools. See `KIT_VERIFIED_FINDINGS.md`. Public-test SDK/catalog and actual scorer are not present in the small review bundle, so score-equivalence remains UNKNOWN.

**Status:** Implementation-ready product intent (2026-11-09)  
**Audience:** Local coding agent, technical architect, evaluator/training engineers  
**Scope:** Zalo AI Challenge 2026 **LifeMate**, not DataMate  
**Source priority:** 1) Actual organizer kit + official rules; 2) user-provided `data.md`; 3) user-provided handoff; 4) public participant research and our own hypotheses. If a conflict arises, official materials prevail. Research questions reside only in `01_research_brainstorm.md`.

## 1. Problem and desired outcome

Build a fully offline solution that converts spoken Vietnamese user requests into a sequence of **authorized, accurately parameterized, stateful app tool calls** through the official `zaic_tools.ToolEnv`. It must perform multiple steps, consume intermediate tool observations, handle incomplete and unsupported requests, and return the **actual** final state hash from the same environment. Optimize official **end-to-end LifeMate score**, not merely word-error rate, code coverage, or training loss.

### Success statement

For every sample in a competition split, the solution generates a valid JSONL output whose tool trace reflects exactly the calls it actually executed through the official environment, reaches the target state whenever possible, chooses necessary intermediate reads and asks for missing information when appropriate, and stays within all official competition limits.

## 2. Users and stakeholders

- **Primary operator:** Developer invoking an offline inference command and constructing Docker submission.
- **End user (simulated):** Vietnamese speaker requesting actions across installed apps, potentially with conversation history.
- **Technical evaluator:** Organizer's runtime and scoring pipeline, plus a locally reproducible train-derived evaluator.
- **Coding/training agents:** Implement, test, measure and iteratively improve the system with a traceable experiment record.

## 3. Explicit in-scope capabilities / main functions

| ID | Capability | User intent / observable outcome |
|---|---|---|
| C01 | Speech recognition | Understand the latest user audio and relevant earlier spoken history, including Vietnamese accents and English code-switching. |
| C02 | Context and history understanding | Apply sample-local time, timezone, location, profile, previous turns, and prior tool results without inventing information. |
| C03 | Runtime capability discovery | Identify which applications/tools are **installed for this sample**, based on supplied catalog and `installed_apps`, including unseen app/tool names. |
| C04 | Multi-intent goal decomposition | Account for all independent and dependent requested outcomes; don't stop after one partial success. |
| C05 | Iterative next-action decision | Choose one permitted next tool call, clarification, or done after every real tool observation. |
| C06 | Argument and reference grounding | Resolve account/contact/device/event IDs from permitted context, history results, or live ToolEnv reads. |
| C07 | Safe temporal/numeric interpretation | Preserve money, time, dates, offsets, counts, negation and user self-corrections. |
| C08 | Runtime validation and execution | Validate schemas and semantic constraints before calling real tools; execute only through official ToolEnv. |
| C09 | Missing-information handling | Call `sys.ask_missing_info` with correct `tool_name` and missing `params` when required information cannot be obtained. |
| C10 | No-action behavior | Submit `[]` for truly unsupported, withdrawn, or already-handled requests as indicated by official/gold conventions. |
| C11 | Correct stopping/recovery | Avoid premature DONE, redundant reads, duplicate accidental writes, unsupported retries and runaway loops. |
| C12 | Exact submission integrity | Produce one line/sample with unique id, actual calls and state hash, in the organizer's required format. |
| C13 | Reproducible local validation | Replay authorized train gold traces; compare predicted trajectories, state outcomes and runtime. |
| C14 | Targeted model adaptation | Improve tool decision quality with gold-trajectory LoRA/SFT and optionally ASR tuning after controlled benchmarks. |
| C15 | Competition-grade packaging | Run fully offline with legal weights, bounded memory/time, reproducible outputs and correct entrypoint. |

## 4. Behavioral user stories with acceptance criteria

**US01 — Multi-step dependency.** As a user asking “Bật điều hòa phòng khách 26 độ và đặt xe về nhà,” I expect the agent to discover the correct AC ID (unless already grounded), set the requested state, then book the ride with my current pickup and home destination when known. **Accept** when all required steps appear in the actual trace and final state agrees with train gold for equivalent labeled scenarios.

**US02 — Multi-goal completion.** As a user requesting several tasks in a single utterance, I expect none to be silently dropped. **Accept** when validation reports explicit missed-goal/premature-DONE rates and every covered synthetic integration scenario is completed or correctly clarified.

**US03 — Referencing tool outcomes.** As a user asking to contact someone discovered by search, I expect the agent to reuse the returned exact ID rather than fabricate one. **Accept** when reference-provenance tests reject invented IDs before any state-mutating call and preserve valid IDs from history.

**US04 — Clarification.** As a user who names an ambiguous contact or omits a required amount, I expect an authorized request for the exact missing fields rather than a random choice. **Accept** when `sys.ask_missing_info` is invoked through ToolEnv with runtime-valid arguments and the proper final trace.

**US05 — Unsupported / canceled action.** As a user who has no suitable installed app or changes my mind, I expect no unintended action. **Accept** when `[]` samples are correctly classified against the authorized train labels and no write occurs in cancellation cases.

**US06 — Conditional workflow.** As a user saying “Nếu trời mưa thì hủy lịch,” I expect the environment to be queried and actions to branch on actual returned facts. **Accept** when tested rain/no-rain scenarios produce different appropriate trajectories and neither uses fabricated observations.

**US07 — Conversation and temporal resolution.** As a user referencing earlier messages, addresses, or relative dates, I expect the agent to keep relevant prior context, correctly interpret corrections, and compute timestamps from sample time. **Accept** when numeric/temporal/history tests pass, including boundary rollover and ambiguous references.

**US08 — Accurate and legal submission.** As the competition operator, I expect an offline Docker solution, actual call log/hash and a line for every sample. **Accept** when organizer's validator passes, no forbidden data-state access/network dependency exists, and the final hardware/timeout constraints pass.

## 5. Non-functional requirements

1. **Correctness:** Optimize official per-sample score and state-hash match; preserve failures and actual tool attempts in the trace.
2. **Determinism:** Fix seeds/decoding and replay conditions where supported; quantify any output instability.
3. **Latency:** Honor the **reported** 30-second/sample overall budget; tune model-step budget with adequate startup/ASR/multi-turn margin and revalidate the official timing rule.
4. **Resources:** Honor reported total model parameter limit (<6B), action LLM limit (<5B), token limit (<=16,384), and A30 24GB; reverify these limits from official kit before release.
5. **Security/integrity:** Never inspect files under `<split>_environment/` directly, reconstruct target app state, compute a synthetic hash, or use hidden gold data in test-time predictions.
6. **Privacy/data eligibility:** Do not redistribute official datasets; train only on explicitly authorized labels/audio. No test-set pseudo-labeling or external inference APIs.
7. **Observability:** Record per-sample local diagnostic traces without duplicating logs into the scored submission, and without leaking restricted app-state files.
8. **Maintainability:** Keep a minimal set of modules and configuration switches; do not implement replacement simulations for `zaic_tools`.

## 6. Non-goals

- Building integrations with live banking, email, ride, device or payment services.
- Building or training an LLM from scratch.
- Reimplementing the organizer's ToolEnv, state files, scoring authority, or submission checker.
- Building a UI/voice product outside the competition.
- Switching to LangGraph or a larger model unless a controlled experiment justifies it.
- Optimizing public leaderboard by labeling public/private test requests, mining unseen test states, or manually injecting correct test calls.
- Assuming any participant's public score/leaderboard position is a private-test guarantee.

## 7. Scope boundaries and trust rules

- **Allowed user input:** sample metadata, audio and history provided for inference, installed tools and schema catalog.
- **Allowed application data:** tool observations returned via the sample's one official `ToolEnv`, plus permitted prior assistant tool results contained in `history`.
- **Disallowed application data:** direct reads of `<split>_environment/<id>/state.json` or other environment files.
- **Training:** authorized labeled `train` records only for the default learning path. Separate dev gold replay and inference runs in independently created environments; each inference run still uses only one environment/sample.
- **Tools:** only those exposed by this sample's installed applications plus the authorized meta-tool `sys.ask_missing_info`.
- **Submission:** never add a tool call not actually executed or edit the real trace/hash for a better hypothetical score.

## 8. Outcomes and quality measures

### Primary

- Organizer score or verified exact-equivalent local scorer on held-out **train-derived** scenarios.
- Final state-hash match rate and valid submission rate.

### Secondary (diagnostic)

- First full-action exact match; second-and-later next-action accuracy; complete trajectory; matched/unmatched tool-call F1; precision and recall of `ASK` and `[]`.
- Correct ID provenance; illegal-call prevention; unnecessary/omitted reads; duplicate-write errors; premature-DONE and missed-goal rates.
- ASR WER/CER **and** critical-slot accuracy (numbers, dates, negation, names), paired gold-transcript vs ASR end-to-end score.
- Runtime p50/p95/p99/max and number of over-budget samples; GPU memory and model parameter totals.
- Breakdown by seen vs unseen app, 1–2 vs 3+ calls, history present, conditional branches and clarification cases.

**Acceptance philosophy:** Use a frozen held-out set and predeclared comparisons. No absolute leaderboard target is promised. Each new model/guard is accepted only if the official-equivalent score or a clearly justified risk metric improves without unacceptable regression in critical slices.

## 9. High-level project completion criteria

- [ ] Official kit/API/rules/validator audited and differences from assumptions documented.
- [ ] 100% authorized train gold replay success (or documented kit discrepancy resolved).
- [ ] Transcript-based baseline completes entire train-derived holdout with zero crashes.
- [ ] Real-audio pipeline implemented; score delta from oracle transcript measured.
- [ ] Stateful next-action loop uses real observations, supports CALL/ASK/DONE and verified tool provenance.
- [ ] All P0 scoring-risk edge cases have automated unit/integration tests.
- [ ] Candidate SFT/LoRA changes evaluated against a frozen baseline, without leakage.
- [ ] Container passes offline test, deadline/hardware/resource checks and submission schema validation.
- [ ] Reproducible final model/adapter, code, prompt, experiment config and results are recorded.

**Next read:** `spec.md` for executable contracts and detailed behavior; `implementation_plan.md` for ordered backlog, experiments, gates and timelines; `01_research_brainstorm.md` for citations, hypothetical edge cases and unresolved rule verification.


## 10. Official-kit-grounded intent addendum — mandatory acceptance criteria

These requirements supersede weaker assumptions elsewhere in the handoff. They are backed by v3.2.0 **train SDK source inspection**, not yet by execution of real scenarios.

- **I-01 — Exact tool execution:** For each inference scenario, construct exactly one official `ToolEnv` and return **its** logged calls and state hash. Invalid executed attempts remain logged.
- **I-02 — Preflight with honest limits:** Validate tool existence, install scope, required fields, enum/type/range/format and `x-one-of` through `env.validate` before execution. Add separate checks for reference provenance (`x-ref`), nested argument objects, and business preconditions; do not describe these as SDK-validated.
- **I-03 — Semantic success:** A response `ok:true, done:false` does not satisfy the requested action. A successful write may lack `done`; implement tool-aware interpretation and safe bounded recovery.
- **I-04 — Text accuracy independent of state hash:** The SDK hashes canonical state after dropping certain free-text fields. Correct hash alone is insufficient; the agent must still generate faithful message content, names, labels, and user-specified details.
- **I-05 — Missing information:** `sys.ask_missing_info` uses actual `tool_name` and string-array `params`, is a logged tool call, and does not change state. It can follow other executed actions when another goal cannot yet be completed.
- **I-06 — History preservation:** Only the **latest** user turn is to be acted on; history operations have already been applied in initial state. History text and tool results remain available for coreference.
- **I-07 — Split generalization:** The implementation must read the selected split's authorized catalog and runtime registry, not assume train's 46 apps/147 tools cover public/private test.
- **I-08 — Score honesty:** No local numeric score is called `official` before scorer parity. Scorer details, public-only app count, runtime hardware and Docker rules are flagged `UNKNOWN` until independently verified.

**Mandatory evidence gates:** (a) local train gold replay, (b) frozen train-derived end-to-end baseline, (c) no direct raw environment-state inspection, (d) P0 cases from `SCORING_EDGE_CASES.md` passing, (e) exact source-bound submitted trace and hash, (f) offline runtime/Docker checks when official constraints are known.
