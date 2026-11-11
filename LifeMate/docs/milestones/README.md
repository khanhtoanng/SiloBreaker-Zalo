# LifeMate project roadmap

LifeMate takes a Vietnamese voice request, chooses and executes actions in the organizer's app simulator, and records the actual calls and final state hash. Read the milestones in order to see why each layer exists and how to verify it. The order is an architecture learning path reconstructed from the handoff and active source. For commands you can run today, open the [local quickstart](../local_quickstart.md). For background on the AI components, open [AI for software engineers](../ai_for_software_engineers.md).

| Milestone | What you will understand | Evidence in this checkout |
| --- | --- | --- |
| [01. Define the voice-to-action problem](01-idea-and-contract.md) | The three design decisions behind LifeMate and what one successful request looks like | Organizer contract and source boundaries are documented |
| [02. Build the data and simulator foundation](02-kit-and-replay.md) | Which data belongs to each split and how replay creates a trusted reference | Current loader read both manifests and catalogs. A fresh train replay passed all 1,545 scenarios |
| [03. Build a text-first agent](03-text-agent.md) | How a policy decision turns into a validated call, clarification, or stop | Runtime and local backends exist. An older three-scenario Ollama pilot is recorded. Full current holdout quality is pending |
| [04. Add speech and measure the baseline](04-audio-and-evaluation.md) | How to tell speech errors from planning errors and validate a full public result | Audio and evaluation code exists. Current real-audio quality and target-hardware timing are pending |
| [05. Optimize with evidence](05-optimization-and-training.md) | When to change a guard, tune ASR, or train a LoRA adapter | Fresh preparation generated 5,086 decision rows. A trained adapter and its measured gain are pending |
| [06. Package and submit to Zalo](06-zalo-submission.md) | The public JSONL, the final Docker image, and the private-test result | Organizer contract mapped. Competition image, timing notebook, offline run and uploads are pending |

## Find your way around

Paths in this table are relative to `LifeMate/`.

| When you see | What it is for | Where to start |
| --- | --- | --- |
| `pyproject.toml`, `src/lifemate/cli.py`, `src/lifemate/workflows.py` | Package entry point, command flags and orchestration | Follow `python -m lifemate` into `cli.main`, then `workflows.dispatch` |
| `src/lifemate/contracts.py`, `config.py` | Input, action and configuration validation | Read `InferenceConfig` and the CALL/ASK/DONE definitions |
| `src/lifemate/data/`, `runtime/`, `adapters/` | Kit and scenario selection, the agent loop, and external interfaces | Open `data/kit.py`, `runtime/loop.py`, and `adapters/sdk.py` first |
| `src/lifemate/learning/`, `metrics/` | Generate training decisions, train the policy and measure results | Open `learning/trajectories.py` or `metrics/reports.py` when you reach their milestone |
| `src/lifemate/agent_loop.py`, `data_loader.py`, `validator.py` and similar names | Compatibility modules for earlier imports | Use the [migration map](../migration.md) to find the active implementation |
| `src/lifemate/artifacts.py`, `prediction_artifacts.py`, `submission.py`, `provenance.py` | Output path checks, final results and sidecars, row validation, and run identity | Open `prediction_artifacts.py` when tracking where a run wrote its results |
| `configs/`, `scripts/`, `tests/` | Example JSON settings, entry points and utilities, and regression fixtures | Copy configs to your work folder. Use tests to see inputs and expected outcomes |
| `Dockerfile`, `predict.sh`, `.dockerignore`, `MANIFEST.in` | Container draft, container launch wrapper, build-context exclusions, and Python archive rules | Use [milestone 06](06-zalo-submission.md) for the competition-specific differences |
| `docs/ai/`, `.agents/`, `.ai-sdlc/`, `.codex/`, `AGENTS.md` | Prior work records, snapshots and development workflow | Read `AGENTS.md` when editing the project. Use snapshots when investigating a past change |
| `.venv/`, `.venv-core/`, `dist/`, `src/lifemate.egg-info/`, `__pycache__/`, `.mypy_cache/`, `.ruff_cache/` | Local Python installs, built packages, install metadata and caches | Start with `src/` for application code. Use an environment's Python to run it |
| `../train+public_test.zip`, `../train+public_test/`, `../local_lifemate_artifacts/` | Organizer ZIP and extraction, plus earlier local reports and run outputs | Keep these separate from the source and any public archive |
| `../intent.md`, `../spec.md`, `../implementation_plan.md`, `../tools/`, `../inputs/` | Original design, research and kit-audit utilities | Refer to these for project rationale. Use the active source and organizer material for current behavior |

## First 15 minutes

1. Read [milestone 01](01-idea-and-contract.md) to understand the input and the output.
2. Open [CLI dispatch](../../src/lifemate/cli.py) and run `python -m lifemate --help` from `LifeMate/` using the interpreter set up in the [operator guide](../operator_guide.md). If the copied `.venv-core` works on your machine, its `Scripts\python.exe` can run the core commands.
3. Follow the worked fixture in [milestone 03](03-text-agent.md). It shows how a successful action and a clarification can appear in the same turn, with no model setup required.
4. Use the [submission milestone](06-zalo-submission.md) to plan the remaining release work. Start with a measurable audio baseline and get the Docker launch contract working in parallel. Treat LoRA as an experiment with an explicit promotion gate.

## Checks for this guide

On 11 November 2026, `python -m unittest discover -s tests -v` completed with 187 passes and three skips for symlink or junction creation unavailable in the Windows environment. CLI help and the Markdown links resolved. The `audit`, `freeze`, `replay`, and `trajectories` examples ran with exit code 0 in a temporary work directory. The kit and WAV checks exercised the supplied data without loading models. Model quality, full-run timing and competition packaging need the release checks in milestones 04–06.
