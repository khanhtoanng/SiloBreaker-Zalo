# Intent — Implement the LifeMate offline voice-to-action application

WORK_ID: LM-002-python-structure-training-guide  
FLOW: FULL  
STAGE: INTENT  
REVISION: r2  
INPUT: source.md r3  
DATE: 2026-11-10 (Asia/Saigon)  
STATUS: READY_FOR_REVIEW  
CLARIFICATION_CHECK: RESOLVED — DEC-03 confirms full application scope; no remaining material Intent gaps

## Source, revision and confirmed decisions

The product to implement is the LifeMate offline Vietnamese voice-to-action agent
defined in the original [parent intent](../../../../../intent.md) and
[parent specification](../../../../../spec.md). Those documents supply the product
goal, C01–C15 capabilities, behavioral stories and technical workflow contracts.
This work delivers that application's code, configuration, tests and guides for
the operator to run later, with the user's additional Python conventions.

This revision replaces the rejected refactor/trainer-only framing in
`intent.r1.md`. The work ID remains stable; its title does not limit the clarified
product scope. The direct request and decision receipts are in
[source.md r3](source.md):

- **DEC-01 / U-02:** use generic role-guided agents, an independent reviewer and
  the project's existing human SDLC gates. These are not named native agents.
- **DEC-02 / U-03:** implement training code and the complete guide; actual local
  training setup, model downloads and training execution are deferred.
- **DEC-03 / U-04:** **"REVISE intent r1"** and **"My goals is implementing it.
  But just code and guide to run. Not start training runtime yet"**, explicitly
  referring to the original parent intent/spec. The full application's software
  scope is retained; runtime execution is the deferred part.
- **U-01:** keep Python clean and clear, use Pydantic for relevant data and
  configuration models, and design a good project structure. This explicit choice
  takes precedence over illustrative dataclasses or a flat layout in the parent spec.

The parent documents remain read-only. Their model candidates, proposed layouts,
reported numeric rules and optional experiments are not automatically verified
official facts or selected designs. Actual organizer evidence and direct user
instructions take priority. This Intent remains subject to human approval.

## Product problem and actors

A simulated Vietnamese-speaking user needs a spoken request, including multiple
goals and conversational references, translated into the correct authorized app
actions. The agent must understand supplied audio and context, use actual tool
observations to choose each next action, handle missing or unsupported requests,
and return the official environment's real call trace and state hash.

The project owner needs the full software path implementing that behavior, plus
maintainable code and dependable instructions to prepare data, train or adapt the
action model, run text/audio inference, evaluate results and package the offline
application later. Cleaning up existing modules and adding a trainer alone would
leave the original product incomplete.

The actors are:

- **Simulated end user:** expresses Vietnamese spoken requests, corrections,
  conditions and multiple goals across the installed applications.
- **Application operator:** later configures local models and data, invokes the
  offline text/audio pipeline, inspects diagnostics and creates submissions.
- **Training/evaluation operator:** later prepares authorized train-derived
  trajectories, invokes model adaptation and compares results on frozen folds.
- **Maintainer and reviewers:** understand the project structure and validated
  contracts, extend behavior and verify the approved implementation with honest
  evidence and protected data boundaries.

## Evidence and existing implementation

- **OBSERVED:** the original intent defines C01–C15, US01–US08 and SDK/data-integrity
  constraints. The original specification describes the audio-to-action pipeline,
  next-action loop, grounding, goal tracking, training, evaluation and offline
  packaging workflows. Both documents were read completely for this revision.
- **OBSERVED:** current source includes manifest/catalog loading, context building,
  a text decision loop, SDK adapters, manual validation, provenance diagnostics,
  submission writing, train replay, trajectory preparation, proxy evaluation and
  local model adapters. Pydantic is not yet declared in `pyproject.toml`.
- **OBSERVED:** the inspected source/script inventory has no ASR implementation,
  temporal/numeric normalization module or project LoRA training entrypoint.
  `docs/p0_coverage.md` also records unfinished semantic goal and repetition work.
  These gaps explain why the full original product must guide implementation.
- **OBSERVED AS DOCUMENTED HISTORY:** current audit documents report inspected
  train/public SDKs, replay and synthetic contracts. They also record differing
  split-specific hash behavior. Those reports do not constitute new checks by
  this Intent stage or complete implementation of the product.
- **UNKNOWN:** future model accuracy, ASR quality, training success, latency and
  memory on target hardware, official scorer parity and competition release
  compliance. The complete local kit supersedes the small-bundle availability
  statements where supported by actual evidence; unavailable rules remain unknown.

## Intended outcomes and success signals

Stable INT-01–INT-07 identities are retained and expanded to the clarified full
product. INT-08–INT-13 make the previously omitted application outcomes explicit.
The success signals below concern software delivery and permitted verification;
they do not assert that deferred model or training runs have occurred.

| ID | Intended outcome | Source | Observable software-delivery success signal |
|---|---|---|---|
| INT-01 | The complete Python application is clean, understandable and organized around clear responsibilities. | U-01; DEC-03; parent intent §5 item 8 and spec §3/§9 | Maintainers can trace preparation, audio/text inference, evaluation, training and packaging paths through implemented code and documented conventions; responsibilities and dependencies are clear to independent review. |
| INT-02 | Pydantic controls the application's relevant data and configuration contracts, with explicit validation boundaries and failures. | U-01; DEC-03 | Affected workflows use declared validated models, with focused positive/negative checks; project validation supplements rather than replaces official SDK validation and semantics. |
| INT-03 | The next-action model adaptation workflow is implemented using authorized train-derived trajectories and a training entrypoint/configuration the operator can invoke later. | DEC-02/03; parent C14; spec §6 | Software covers frozen scenario partitions, per-decision examples, consistent inference/training action representation, assistant-action loss boundaries, adapter/artifact provenance and subsequent evaluation/use. Permitted checks validate these contracts without launching training. |
| INT-04 | Complete guides explain how to prepare and run the whole application, including local training later. | U-01; DEC-02/03 | Instructions for prerequisites, external data/models, configuration, preparation, training, audio/text inference, evaluation, submissions and offline packaging correspond to implemented interfaces and outputs, with troubleshooting and explicit execution-status limits. |
| INT-05 | The entire application preserves official SDK authority and dataset-integrity boundaries. | DEC-03; parent intent §7/§10; spec §2/§12; AGENTS.md | Checks address one split-specific official environment per inference sample, actual calls/hash, no history replay or direct hidden-state inspection, eligible tools only, authorized train-only learning, disjoint scenario folds and protected assets outside source. |
| INT-06 | Verification evidence truthfully separates implemented software and permitted checks from deferred model/runtime certification. | U-01; DEC-02/03; parent I-08 | Reports identify actual commands and results, fixture evidence, proxy scoring and unrun checks separately. Software is not described as trained, benchmarked or competition-certified without actual evidence. |
| INT-07 | Delivery follows FULL SDLC with traceable decisions, approved stages, bounded edits and independent review before final human acceptance. | U-01; DEC-01 | Actual approval receipts, the plan-bound edit grant, complete change identity, implementation evidence and a fresh independent review are recorded before final human acceptance. |
| INT-08 | The application supplies offline Vietnamese speech-recognition software for the latest request and relevant earlier user audio. | DEC-03; parent C01; spec §3/§5.1 | Implemented audio/history paths preserve turn ordering, expose transcription/diagnostic results and connect to the same action workflow as authorized train oracle text. Software-level tests can use controlled transcriptions; actual ASR model quality remains deferred. |
| INT-09 | Supplied context, history and current-sample capabilities are understood and retained throughout processing. | DEC-03; parent C02/C03; spec §2/§3/§5.3 | The pipeline carries sample time/timezone, location/profile, chronological history and prior results, and exposes the selected split's complete eligible tool schemas without substituting train-only assumptions or replaying history operations. |
| INT-10 | Multi-goal and conditional requests are handled through observation-driven next actions, appropriate clarification/no-action behavior and safe completion/recovery. | DEC-03; parent C04/C05/C09/C10/C11 and US01/02/04/05/06; spec §4/§5.4/§5.5 | Implemented control flow tracks goal evidence and dependencies, processes one CALL/ASK/DONE decision at a time, branches on actual observations, distinguishes no-op/uncertain outcomes, preserves completed independent work, bounds recovery and supports deliberate repeated intent without blindly repeating writes. Controlled component/integration cases exercise these paths. |
| INT-11 | Arguments and references preserve the user's intended entities, amounts, times, negation and corrections. | DEC-03; parent C06/C07 and US03/07; spec §2.2/§5.2 | Software handles typed provenance from permitted sources, sample-local temporal interpretation and unambiguous numeric normalization; unresolved ambiguity leads to a permitted read or ASK rather than guessed IDs or changed semantic values. |
| INT-12 | Submission, replay and evaluation software provides exact output integrity and reproducible diagnostics for later runs. | DEC-03; parent C08/C12/C13; spec §3/§7/§8/§12 | Implemented workflows enforce preflight plus SDK validation, actual trace/hash output and manifest integrity, authorized train replay, call/state comparisons, relevant error/latency/ASR diagnostics and frozen-fold evaluation. Unverified scoring remains visibly PROXY. |
| INT-13 | Offline packaging and operator entrypoints are implemented so the complete application can be packaged and run later with locally supplied assets. | DEC-03; parent C15 and US08; spec §3/§9/§10/§11 | Packaging code/configuration and entrypoint/run guides cover local model/adapter/ASR assets, split-aware input/output, offline startup, reproducibility metadata and verification procedures. Official path/resource settings are grounded in available evidence; actual image/runtime and target-hardware certification are not claimed now. |

## Original capability coverage

Every original core capability remains in the software deliverable. The original
specification sections below identify the relevant source behavior, not an
approval of detailed implementation design at this stage.

| Parent capability | Revised Intent coverage | Original spec source |
|---|---|---|
| C01 — Speech recognition | INT-08, INT-04 | §1; §3 ASR; §5.1 |
| C02 — Context/history understanding | INT-09, INT-11 | §2; §3 context compilation; §5.1/§5.2 |
| C03 — Runtime capability discovery | INT-09, INT-05 | §2.1; §3 registry; §5.3; §12.5 |
| C04 — Multi-intent goals | INT-10 | §4; §5.4 |
| C05 — Iterative next action | INT-10, INT-05 | §2.3; §4 |
| C06 — Argument/reference grounding | INT-11, INT-05 | §2.2; §5.2/§5.3; §12.1 |
| C07 — Temporal/numeric interpretation | INT-11 | §3 normalizer; §5.2 |
| C08 — Validation/execution | INT-05, INT-12 | §3 validator/adapter; §4; §12.1/§12.2 |
| C09 — Missing information | INT-10, INT-05 | §2.3; §4; §12.4 |
| C10 — No-action behavior | INT-10, INT-12 | §4; §7.1; §8 |
| C11 — Stopping/recovery | INT-10 | §4; §5.4/§5.5; §12.2 |
| C12 — Exact submissions | INT-12, INT-05 | §2.1; §3 submission; §4; §8 |
| C13 — Reproducible validation | INT-12, INT-06 | §6.1; §7; §8 |
| C14 — Model adaptation | INT-03, INT-04, INT-06 | §6.1–§6.4; §8 |
| C15 — Offline packaging | INT-13, INT-04, INT-06 | §3 package verification; §9–§11 |

## In scope

- Complete the original offline audio-to-action product workflow, including
  latest/history ASR software, context and capability handling, semantic helpers,
  grounded multi-goal next-action processing, official tool execution and exact
  submissions. These features are not removed because their model runs are deferred.
- Implement the required preparation, replay, evaluation/diagnostic and trajectory
  SFT/LoRA adaptation software, configuration and operator entrypoints.
- Implement offline packaging/entrypoint software and supporting run/verification
  instructions without representing an untested image as a compliant release.
- Apply Pydantic and a clear Python structure across the application rather than
  limiting the work to rearranging existing modules.
- Deliver complete, consistent guides for later setup, data/model preparation,
  training, text/audio inference, evaluation and packaging, with commands that
  correspond to real delivered software.
- Add or adapt appropriate software-level checks for the affected workflows and
  original edge-case contracts under the later approved implementation grant.

## Execution deferral and non-goals

The current deliverable is implemented software and guides with permitted static,
unit, contract and controlled component checks. Actual local training-environment
setup, model downloads, model inference/ASR runtime jobs, model training, model
benchmarks and target-hardware/runtime certification are deferred. Later-stage
verification must state which checks can be performed without those activities;
deferred checks remain NOT RUN or NOT VERIFIED rather than fabricated passes.

The following remain outside the original product or are conditional research:

- Live banking, messaging, ride, device or payment-service integrations; a separate
  consumer UI/voice product; training an LLM from scratch; a replacement simulator
  or independent submission-state hash authority.
- Public/private test-label learning, pseudo-label adaptation, mining protected
  state, fabricating executed calls/hash or redistributing organizer SDK/data.
- Treating every proposed model, orchestration framework, augmentation, optional
  ASR-tuning experiment, RL method or full-model fine-tuning experiment as a
  mandatory implementation solely because it appears in the research roadmap.
  The core speech inference path and next-action adaptation software stay in scope.
- Claims of score improvements, trained adapter quality, hardware fit, official
  scorer equivalence or competition compliance without the required actual evidence.
- Automatic rule changes, unrelated tooling, publishing, push/merge/deploy or
  bypassing the agreed SDLC gates.

## Constraints and delivery boundary

Only supplied inference inputs, permitted history/context and observations from
the sample's one official environment may guide actions. Nested semantic and
reference checks supplement SDK validation; an `ok:true` response alone cannot
prove a completed write. `sys.ask_missing_info` remains a real logged tool, history
actions remain already applied, and the SDK log/hash are submission authority.

Training uses authorized labeled train examples and scenario-disjoint partitions
before trajectory expansion. Its chosen action representation and assistant-target
loss boundaries must agree with inference. Local Ollama remains a relevant policy
adapter option from prior user direction; it is not a LoRA training engine.

Organizer SDK/data, model assets and derived outputs remain outside implementation
source as required by project rules. Existing owner changes and read-only parent
documents are preserved. Reported resource limits and unverified official mounting,
entrypoint or scoring details are explicitly distinguished from verified facts;
software/configuration and future verification instructions still cover these
boundaries without inventing official certification.

The exact layout, frameworks, interfaces, configuration choices and detailed tests
belong to subsequent approved Specification and Architecture stages. No application
edit grant or immutable implementation baseline is created by this Intent. Human
approval of this exact r2 is required before Specification. Delivering the code and
guides later will not, by itself, satisfy the parent's separate trained-model,
benchmark or competition-runtime release gates; those remain deferred execution
checkpoints under DEC-03.
