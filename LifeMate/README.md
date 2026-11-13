# LifeMate

LifeMate is an offline Python CLI for the Zalo AI Challenge. The runtime follows
one request from Vietnamese audio through transcription, tool selection, and
validated execution in Zalo's simulator. It writes the resulting tool trace and
state hash to JSONL.

Read [the learning guide](../learn.md) for a walkthrough from WAV to submission
and a roadmap for improving the model. Use the [competition run guide](docs/competition_run.md)
to run the current local model and produce a submission file.

| I want to | Guide |
| --- | --- |
| Read the code in order | [Request walkthrough](../learn.md#2-follow-one-request-through-the-code) and [architecture](docs/architecture.md) |
| Build and install the app | [Build the Python package](docs/build.md) for the wheel, source archive, and clean-install check |
| Run and test the app locally | [Local quickstart](docs/local_quickstart.md) for the test suite, an SDK smoke test, and text/audio prediction |
| Run a full workflow | [Operator guide](docs/operator_guide.md) for kit setup, inference, validation, and evaluation |
| Fine-tune the action policy | [Local LoRA guide](docs/local_training.md) for replayed trajectories, preflight, training, and adapter inference |
| Build a container or prepare a submission | [Offline packaging](docs/offline_packaging.md) and [Zalo submission milestone](docs/milestones/06-zalo-submission.md) |

## Start locally

From the `LifeMate/` folder that contains `pyproject.toml`, use Python 3.10 or
newer. These PowerShell commands install the core package and run the tests.
An existing working LifeMate environment can use its own Python executable.

```powershell
$Venv = Join-Path $env:USERPROFILE 'LifeMateWork\venvs\app'
python -m venv $Venv
$Python = Join-Path $Venv 'Scripts\python.exe'
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
& $Python -m pip install -e .
& $Python -m lifemate --help
& $Python -m unittest discover -s tests -v
```

Run [one real simulator read](docs/local_quickstart.md#1-run-one-sdk-read) with
the organizer kit to verify SDK access. Then run the [public audio pilot](docs/competition_run.md#public-test-on-windows)
with the competition's local Qwen and PhoWhisper configuration.

## Source map

| Code | Responsibility |
| --- | --- |
| [cli.py](src/lifemate/cli.py), [workflows.py](src/lifemate/workflows.py) | Parse commands, select scenarios, set up backends, and run use cases |
| [contracts.py](src/lifemate/contracts.py), [config.py](src/lifemate/config.py) | Validate data, settings, and action decisions |
| [data/](src/lifemate/data/), [adapters/](src/lifemate/adapters/) | Load the selected kit split and connect to the simulator, policy, and ASR |
| [runtime/](src/lifemate/runtime/) | Build context, ground references, track goals, and validate and execute CALL, ASK, and DONE decisions |
| [prediction_artifacts.py](src/lifemate/prediction_artifacts.py), [submission.py](src/lifemate/submission.py) | Manage prediction outputs and validate final JSONL rows |
| [learning/](src/lifemate/learning/), [metrics/](src/lifemate/metrics/) | Prepare training trajectories, fine-tune the policy, and compute local proxy and ASR metrics |
| [configs/](configs/), [scripts/](scripts/), [tests/](tests/) | Example settings, command wrappers, and regression tests |

Keep the organizer kit, model weights, and run outputs outside this source
directory. Inference uses the selected split's SDK and catalog. Train
transcripts are available in oracle mode, and gold labels are used for
train replay, preparation, and evaluation. See the [verification history](docs/verification.md)
and [scorer parity notes](docs/scorer_parity.md) when interpreting results.
