# Intent — Maintainable LifeMate Python and local training capability

WORK_ID: LM-002-python-structure-training-guide  
FLOW: FULL  
STAGE: INTENT  
REVISION: r1  
INPUT: source.md r2  
DATE: 2026-11-10 (Asia/Saigon)  
STATUS: READY_FOR_REVIEW  
CLARIFICATION_CHECK: RESOLVED — DEC-02; no remaining material Intent gaps

## Source and confirmed decisions

The direct user request, recorded as U-01 in [source.md](source.md), asks for clean,
clear Python code, Pydantic-controlled models, a good project structure, and a
guide explaining how to run local training later. The user requests implementation
through the project's SDLC workflow and defers local training setup and execution.

- DEC-01 / U-02: use the available generic agents with the project's role
  instructions, an independent reviewer, and the existing human SDLC gates.
  These delegates are not represented as named native agents.
- DEC-02 / U-03: **"Implement training code and the complete guide (Recommended)"**.
  The work includes the missing training entrypoint and configuration. It is not
  limited to documentation of the existing data-preparation capability.

The parent LifeMate handoff and existing implementation provide domain and contract
evidence. They do not approve this work item's Intent, Specification, Architecture
or application edits. This revision is a reviewable scope artifact, not an approval.

## Problem and actors

The project owner needs an understandable codebase that can be maintained and
extended, plus a complete path to run model training on their own suitable local
environment when they choose. Existing runtime/data workflows are implemented
primarily with dictionary contracts, and training-data preparation currently stops
before a project training command. A training guide alone would not supply that
missing software capability.

The primary actors are:

- **Project owner and maintainer:** reviews the design, understands responsibilities
  and validation boundaries, and changes the Python project confidently.
- **Local training operator:** later prepares an authorized environment, configures
  and runs training, finds the resulting artifacts, and follows the project's
  evaluation/use instructions.
- **Implementation and independent review agents:** trace the approved outcomes
  through code, documentation and permitted verification without claiming unrun
  training or benchmark results.

## Evidence of the need

- **OBSERVED:** `pyproject.toml` declares no required dependencies and does not yet
  declare Pydantic. `RunConfig` is a frozen dataclass; runtime decisions and several
  input/output contracts are handled as dictionaries with manual validation.
- **OBSERVED:** `cli.py` combines command parsing, workflow dispatch, data loading,
  inference coordination and artifact persistence. The project already contains
  separate SDK, replay, evaluation, trajectory and model-adapter capabilities.
- **OBSERVED:** `trajectory_builder.py` creates teacher-forced next-action examples.
  The current CLI exposes preparation, prediction, evaluation and validation
  commands, but the inspected project scripts contain no training entrypoint.
- **INFERRED:** clearer responsibilities and validated models can make these
  workflows easier to understand and maintain. The implementation and later review
  must substantiate that outcome rather than treat a folder rearrangement as proof.
- **UNKNOWN:** successful local training, target-hardware feasibility, official
  scorer parity and competition release compliance for the future implementation.
  This work does not convert those unknowns into performance promises.

## Intended outcomes and success signals

| ID | Intended outcome | Source and decisions | Observable success signal |
|---|---|---|---|
| INT-01 | The Python project is clean, understandable and organized around clear responsibilities. Maintainers can locate and change a workflow without unrelated orchestration obscuring its purpose. | U-01 | The implemented structure and documented conventions explain responsibilities and dependencies; the independent reviewer can trace a representative preparation, prediction, evaluation and training path through the code. |
| INT-02 | Pydantic is used to define and validate the project's relevant data and configuration contracts. Accepted values, validation boundaries and failures are explicit. | U-01 | Relevant workflows consume the declared validated models, and focused checks demonstrate valid and invalid inputs at the affected boundaries while preserving the official SDK's authority. |
| INT-03 | The project supplies the missing training entrypoint and configuration for its next-action model using authorized train-derived examples. The code can be invoked by the operator later rather than leaving training as a nonexistent command. | U-01; DEC-02 / U-03 | The delivered training interface, configuration and artifact handling are implemented and covered by permitted software-level checks; their documented invocation corresponds to actual project code. Heavy training execution remains explicitly unverified until performed later. |
| INT-04 | A complete, actionable guide takes the operator from prerequisites through data preparation, configuration, training invocation, artifact discovery and subsequent evaluation/use. | U-01; DEC-02 / U-03 | The guide's commands, configuration references and expected outputs agree with the implemented interfaces, explain prerequisites and troubleshooting, and distinguish instructions from steps actually executed or verified in this work. |
| INT-05 | The refactor and training capability preserve LifeMate's execution and data-integrity boundaries. | U-01 project context; AGENTS.md; supporting handoff contracts | Verification addresses one official split-specific environment per inference sample, actual logged calls/hash, history without replay, authorized train-only learning, and scenario-disjoint fit/validation data. No copied SDK or protected data is added to source. |
| INT-06 | The work produces trustworthy implementation and review evidence without performing the deferred local training setup or model runs. | U-01; DEC-02 / U-03 | Reports identify actual commands/results and unrun checks separately. No training environment setup, model download, training job or model benchmark is launched to claim completion of this work item. |
| INT-07 | Delivery follows the approved SDLC sequence with traceable decisions and independent review before final human acceptance. | U-01; DEC-01 / U-02 | The coordinator records actual stage approvals, a plan-bound edit grant, the implementation evidence, a fresh independent review, and final human acceptance of the reviewed snapshot. |

## In scope

- Refactor the existing Python codebase to improve clarity, responsibility
  boundaries and consistent coding conventions, using Pydantic as requested.
- Implement training code, its configuration and the supporting interfaces needed
  to make the local next-action training workflow usable later.
- Deliver complete local training instructions aligned with that implementation,
  including preparation, invocation, outputs, evaluation/use and troubleshooting.
- Preserve the existing LifeMate SDK boundary and relevant workflow behavior;
  document intentional interface changes through the approved later stages.
- Add or adapt focused software-level verification for the changed contracts,
  workflows and documented interfaces within the later approved edit scope.

## Non-goals and execution boundaries

- Setting up the user's local training environment now, downloading model weights,
  running training, running model benchmarks or claiming new model quality results.
- Completing every future feature from the parent handoff, such as ASR training,
  new speech capabilities or competition Docker release work, solely because that
  broader roadmap exists.
- Changing the organizer SDK, reconstructing its simulator or hash authority,
  inspecting hidden environment-state files directly, or using public/private
  test examples as training labels.
- Redistributing organizer assets, raw states, labels, audio or trained artifacts
  through the implementation source directory.
- Guaranteeing training speed, GPU fit, score improvement, scorer equivalence or
  competition compliance before the relevant actual evidence exists.
- Automatically changing project rules, installing unrelated tools, publishing,
  pushing, merging, deploying or bypassing the human SDLC gates.

## Constraints carried forward

Pydantic is an explicit user-selected requirement. The exact package layout,
training implementation choices, model/configuration details and verification
design belong to the subsequent approved Specification and Architecture stages.

Only authorized labeled train data may feed training. Scenario partitions must
remain disjoint across preparation and training. Inference must not consume gold
labels or direct simulator-state data; its submitted calls and hash remain sourced
from the same official environment actually used for that sample.

Organizer assets and dataset-derived outputs stay outside source. Existing owner
changes and project/SDLC rules remain protected. Later implementation needs an
agreed immutable baseline and a bounded edit grant; neither is created by this
Intent. Reported historical checks are not new verification for this revision.

## Completion boundary for this stage

This Intent is complete for human scope review because DEC-02 settles the missing
training-capability boundary. Human approval of this exact revision is required
before Specification. No application code, dependency or test changes are part of
the Intent stage, and no training or inference execution has been performed here.
