# Five role contracts — authoritative stage ownership

Each role operates on **accepted or clearly proposed** current evidence. A role is a responsibility, **not an automatic native subagent**; choose direct/delegated execution under `delegation.md`. Worker status: `READY | NEEDS_DECISION | BLOCKED`, except Developer (`READY_FOR_REVIEW`) and Reviewer (`AI_PASS | CHANGES_REQUESTED | BLOCKED`). Workers return results to Coordinator; **none** may ask owner directly, grant scope, dispatch downstream, or mark owner approval. Re-derive from current source if input revision is stale.

<discovery-and-brainstorming>
Shared **mandatory discovery check**, **conditional brainstorming** for Intent, Spec and Architect. Run within the current responsibility, not as a sixth role, new document, obligatory meeting or automatic subagent. It is a reasoning/decision discipline, not permission to change scope.

1. **Look before asking:** read the request, existing source/contracts, effective project rules and current accepted decisions. Do not re-ask answered questions, rerun accepted stages or assume undocumented behavior.
2. **Own your uncertainty:** Intent explores **WHY/WHO/scope/outcomes**; Spec explores **WHAT/observable business rules**; Architect explores **HOW/implementation trade-offs**. Do not have all three independently debate the same question.
3. **Triage:** if a single grounded approach exists and no consequential choice is open, proceed with a one-line rationale; no options menu or owner question. Otherwise explore only materially different alternatives (usually 2–3 *when they actually exist*), source evidence, consequences and the simplest viable proposal. Comparing invented options is not a requirement.
4. **Classify the result:** `OBSERVED` (verified current fact), `OWNER_ACCEPTED` (binding choice), `PROPOSED` (recommendation, not approval), `UNKNOWN` (evidence missing) and `DECISION` (consequential owner-owned choice). In Spec, classify candidate rules/examples with `coverage.md` (`REQUIRED | VERIFY | DECISION | DEFER | REJECT`); do not turn brainstormed cases into ACs without authority.
5. **Clarify via Coordinator:** ask at most the single highest-impact unresolved question at a time, with concise grounded options and a recommended default where appropriate; ask only when the answer would change outcome, accepted behavior, rights/data/security/compatibility, or consequential design. The worker never asks the owner directly. Stop and wait at a real decision gate; never silently make the owner's choice.
6. **Close and hand off:** state selected conclusion, source/rationale, material exclusions and any blocking decision. No brainstorm transcript, speculative AC inventory or duplicate design document. When already resolved, record `NO_MATERIAL_UNCERTAINTY` briefly and continue. Keep full normative AC text and exact approvals inspectable under existing record policy.

**Proportionality:** Quick = check only, no brainstorm unless a blocker surfaces. Standard = focused discovery where new WHAT/outcome is unclear. Extended = deliberate high-impact alternatives and reversibility, but grounded and concise. Spike = compare evidence-based approaches to answer the explicit research question, then STOP. No extra loops after a decision is accepted without new evidence.
</discovery-and-brainstorming>

## Intent — WHY, WHO, boundary

**Run when:** actor, outcome, scope, benefit or consequential product boundary is genuinely unsettled (Standard conditional; Extended explicit check; Quick one-line only).

**Input:** request/ticket revision, effective policy, observed behavior and selected roots. **Steps:** inspect existing evidence → identify actor, outcome, measurable success, in/out scope and current compatibility/permission constraints → run the shared discovery check and **brainstorm materially different product outcomes/scope boundaries only if unsettled** → route any consequential WHY/WHO/scope decision through Coordinator. Do not design architecture, reopen settled requirements or brainstorm unrelated future stories.

**Output:** concise intent (normally a few bullets), evidence/source, explicit non-goals, one consequential owner decision if blocked, `READY/NEEDS_DECISION/BLOCKED`. Human gate only for material outcome/scope choice. **Never:** invent features, design architecture or grant edits.

## Spec — WHAT, observable rules and traceability

**Run when:** accepted intent lacks current, testable observable requirements or behavior changed. **Input:** accepted Intent/current product contracts, risk/evidence, coverage rules. **Steps:** trace accepted source/current behavior → run the shared discovery check to **brainstorm distinct observable WHAT alternatives only where a real ambiguity changes behavior** → use lightweight Example Mapping (story → rules/ACs → representative VERIFY examples → consequential questions) → write source-linked observable Given/When/Then or equivalent contract → classify new ideas via `coverage.md`, separating `UNKNOWN` and owner WHAT choices. Keep accepted unchanged ACs; do not turn each negative/boundary example into another AC.

**Output:** full text of every AC (ID, source, revision, expected outcome), lightweight VERIFY examples/checks, explicit exclusions, short owner card with grouping mapped to *every AC ID*, one blocker. Owner acceptance binds exact complete AC revision, **not** a summary by itself. **Never:** turn every invalid input into a new product requirement, choose implementation, put unresolved questions into approved ACs.

## Architect — HOW, bounded solution

**Run when:** material implementation/test seams/rollout strategy is unsettled; Quick needs only minimal seam reasoning. **Input:** accepted WHAT, actual code/test/contract inventory, current snapshot. **Steps:** trace accepted ACs → inspect actual modules/consumers/trust boundaries → run shared discovery check for **HOW**; consider REMOVE/REUSE/MODIFY before ADD → compare grounded technical options **only when** cost, risk, compatibility or reversibility changes the decision, otherwise state the one sensible path → select the smallest safe design after any required approval → plan vertical slices and meaningful test seams per `tdd.md` → for Extended add evidence-based migration/order/rollback/observability/human approval. Treat unverified reachability as UNKNOWN.

**Output:** short numbered slices, AC→paths/test seams, risk/rollout and one meaningful design blocker. Human gate for consequential architecture/security/data/rollout choices. **Never:** write code in plan-only state, make product rules or build speculative abstractions.

## Developer — BUILD, evidence

**Run when:** behavior/design gates and separate bounded code-edit grant are verified. **Input:** approved work and current baseline/owner changes, exact allowed paths and operations. **Steps:** follow the **required built-in `tdd.md` contract** for applicable behavior changes: one grounded RED that actually fails for the intended reason → smallest GREEN that passes → conditional REFACTOR with pass rerun; run complete vertical slices. Equivalent negative/boundary inputs are VERIFY not new ACs. Pure refactor/docs/config or missing test runner: use credible alternate check and mark TDD `NOT_APPLICABLE/NOT_RUN` rather than fabricate; explain evidence gaps. `UPSTREAM` may be claimed only for a selected/installed external skill actually followed. Optional Ponytail can simplify HOW only if explicitly selected and never replace required tests. Run authorized meaningful regression/static/integration/security checks, inspect whole actual diff, preserve unrelated edits.

**Output:** `READY_FOR_REVIEW/NEEDS_DECISION/BLOCKED`, change identity and AC→code/tests, exact observed commands/results, TDD status, incomplete checks. **Never:** change dependencies/external actions without applicable grant, self-declare AI_PASS, silently modify out-of-scope files.

## Reviewer — independent VERIFY on the current snapshot

**Run when:** Developer has a stable identifiable current diff. For any code-change `AI_PASS`, Coordinator must explicitly invoke a fresh independent host-native reviewer; DIRECT self-review cannot pass. **Input:** accepted AC/plan revision, actual current diff (including relevant untracked files), test/CI results, scope/security and previous findings. **Steps:** confirm independent context + changed snapshot; inspect behavior/AC mapping, TDD RED/GREEN/REFACTOR evidence or truthful exception (`tdd.md`), meaningful tests, unauthorized changes, actual implicated correctness/security/privacy/data/concurrency/compatibility/rollback defects; classify risk evidence per coverage, avoid nit-driven loops; return reproducible severity/path/line/expected-vs-actual findings. `AI_PASS` only if mandatory checks and affected ACs are credibly satisfied on **this snapshot**.

**Output:** `AI_PASS/CHANGES_REQUESTED/BLOCKED`, `INDEPENDENCE: VERIFIED/NOT VERIFIED`, reviewed snapshot, AC evidence summary, TDD status/evidence, optional capability use (if selected), ordered blocking findings, residual risks and human gates. Review stays read-only; fresh review after actual repairs (max three agent rounds). Qualified human acceptance required for high-risk and any organization/security gate; AI_PASS never grants merge/deploy.
