# Source record

WORK_ID: LM-002-python-structure-training-guide  
FLOW: FULL  
SOURCE_REVISION: r2
DATE: 2026-11-10 (Asia/Saigon)

## Original user request and provenance

U-01 — Direct user instruction in this conversation:

> you dont need to setup model training at my local now. Create a guide docs that show me step to run trainning at local. Current, your job is use sdlc workflow then implement the code base on that.
> RULES coding convention: Python project have to clean and clear. Use pytantic for control model. and design a good structure for project

"pytantic" is understood in context as the Python Pydantic validation library.
The user requests code and documentation work through SDLC, deferring actual local
training setup/execution. The original LifeMate handoff remains supporting product
and SDK-contract evidence, not an approved stage artifact for this new work item.

U-02 — Direct user decision via the asynchronous question reply:

Question: "May I run FULL SDLC using the available generic agents, each given the
project’s role instructions, with an independent reviewer and the existing human
approval gates? Proposed work ID: LM-002-python-structure-training-guide, with
stage artifacts under LifeMate/docs/ai/work/LM-002-python-structure-training-guide/.
Named native-agent selection is unavailable in this session."

Answer: **"Use available agents with SDLC gates (Recommended)"**

This authorizes the generic-agent fallback, FULL flow and the named process-artifact
directory. It does not approve a not-yet-written Intent, Spec or Architecture,
grant application edits for a future plan, or grant final human acceptance.

U-03 — Direct user decision via the asynchronous question reply:

Question: "The Intent review found that LifeMate prepares training data but has no
training command yet. Should this work item implement the training entrypoint and
configuration so the local training guide is runnable later? Both options keep
local environment setup, model downloads, and training execution out of the
current work."

Answer: **"Implement training code and the complete guide (Recommended)"**

DEC-02 records this as confirmed product scope: the future approved implementation
includes the missing training entrypoint/configuration as well as the Pydantic
refactor and complete guide. No local training setup, model downloads or training
execution is requested now. This scope decision is not approval of an unwritten
Intent/Spec/Plan or a plan-bound application edit grant. The previous source
revision is preserved as `source.r1.md` with its original recorded hash.

## Selected roots and evidence boundaries

- Implementation root:
  `C:/Users/nktoan/Downloads/LifeMate_2026_Kit_Verified_Coding_Handoff/LifeMate`.
- Work/process artifacts: `docs/ai/work/LM-002-python-structure-training-guide/`
  inside that implementation root.
- Parent handoff README, KIT_VERIFIED_FINDINGS, intent, spec, edge cases and
  implementation plan: read-only supporting inputs.
- Organizer kit: sibling `../train+public_test`, with one nested kit root.
  No direct environment-state reads or redistribution; no test labels for training.
- Dataset-derived local artifacts: sibling `../local_lifemate_artifacts/`;
  inspect only necessary aggregate metadata or authorized train workflow evidence.
- Project rules/worker definitions and existing owner files remain unchanged.

## Observed implementation context

OBSERVED on 2026-11-10:

- The root now contains `pyproject.toml`, `src/lifemate`, `scripts`, `tests`, README
  and evidence documents. The greenfield bootstrap statement in AGENTS.md is
  historical, not the current implementation inventory.
- The package has no required dependencies; optional Transformers and Ollama
  tokenizer dependencies exist. Pydantic is not yet declared.
- Runtime contracts largely use dictionaries. `RunConfig` is a frozen dataclass;
  `validator.py` performs manual decision/argument checks.
- `cli.py` combines argument parsing, data loading, workflow dispatch, inference
  orchestration and artifact persistence.
- Separate modules implement SDK loading, replay, trajectory expansion, proxy
  evaluation, JSONL submissions and local model adapters.
- An authorized train trajectory builder exists. The observed scripts do not
  include a project LoRA training entrypoint.
- The README records previous replay/contract checks and 68 passing tests.
  Those are historical evidence; no test execution has occurred for this work item.
- Existing local verification command: `python -m unittest discover -s tests -q`.
  Compilation check: `python -m compileall -q src scripts tests`.
- No `.git` directory appears in the implementation root inventory. An immutable
  change baseline for later implementation/review has not yet been agreed or taken.
- Named native-agent selection is unavailable through this session's delegation
  schema. The available generic delegation mechanism is real and is used under U-02.
- No active LifeMate pilot process was found when switching focus. This work item
  does not launch benchmarks, training, installers or model downloads.

## User outcomes to carry into Intent

- Clean, understandable, maintainable Python code and a good project structure.
- Pydantic-controlled data/configuration contracts.
- Training code and configuration, with a complete guide explaining how the user
  can run local training later; environment setup and execution remain deferred.
- Implementation follows approved SDLC artifacts and independent review.
- Existing LifeMate SDK integrity, data separation and truthful evidence reporting
  remain mandatory supporting constraints.

## Current authorization and exclusions

Coordinator may write `source.md` and `progress.md` in this work directory.
The delegated Intent worker may write only this work directory's `intent.md`
when its clarification check is complete. Source/code/tests/dependencies, other
stage artifacts and project rules are not writable during the Intent stage.

No authorization in this stage for model/training environment setup, downloads,
training or inference execution, package installation, Git writes, external service
mutations, publishing, merge/deploy, credential access or raw simulator-state reads.

Material scope questions, if discovered, must return to the coordinator before
the final Intent artifact. Routine engineering choices belong to later approved
stages; do not turn unverified SDK/scorer/GPU facts into invented requirements.
