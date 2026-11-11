# LifeMate local quickstart

Start with the regression tests and one simulator read. Then choose a local
model, a package build, or policy training.

| I want to | Start with | What you get |
| --- | --- | --- |
| Run the regression tests | [Test the code](#test-the-code) | Deterministic coverage of CLI, runtime, packaging, and training interfaces |
| Verify the supplied kit works with the app | [Run one SDK read](#1-run-one-sdk-read) | One genuine tool trace and state hash |
| Run an AI model locally | [Run one model prediction](#2-run-one-model-prediction) | An Ollama text pilot or a Transformers and Whisper audio pilot |
| Build installable Python packages | [Build and verify the Python package](build.md) | A wheel, a source archive, and a clean-install check |
| Fine-tune the action policy | [Prepare and train LoRA](#4-prepare-and-train-lora) | Prepared scenarios, a preflight report, then an adapter after successful training |
| Build the Zalo release image | [Offline packaging draft](offline_packaging.md) and [Zalo submission milestone](milestones/06-zalo-submission.md) | The container build workflow and the organizer-specific work still required |

## Set up Python

Open PowerShell in the `LifeMate/` folder that contains `pyproject.toml`. Use
Python 3.10 or newer. Dependencies can come from a package index or a prepared
local wheelhouse.

```powershell
$Project = (Get-Location).Path
$Work = Join-Path $env:USERPROFILE 'LifeMateWork'
$Venv = Join-Path $Work 'venvs\app'
python -m venv $Venv
$Python = Join-Path $Venv 'Scripts\python.exe'
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
& $Python -m pip install -e .
& $Python -m lifemate --help
New-Item -ItemType Directory -Force -Path "$Work\runs", "$Work\data", "$Work\configs", "$Work\reports" | Out-Null
```

If the handoff's `.venv-core\Scripts\python.exe` works on this machine, you can
use it as `$Python` and skip creating and installing a new environment.

## Test the code

```powershell
& $Python -m unittest discover -s tests -v
```

The tests use fixtures for the model and training interfaces. The SDK contract
tests use the supplied train SDK when available. For a kit in another location,
set `$env:LIFEMATE_DATA_ROOT` to the directory containing `train/` before running
the suite. Some path tests may skip when Windows cannot create symbolic links
or junctions.

## 1. Run one SDK read

This uses a scripted policy and the real train simulator. Point `$Kit` at the
directory containing `train/` and `public_test/` if you extracted it elsewhere.
Each run needs a fresh output filename.

```powershell
$Kit = (Resolve-Path -LiteralPath '..\train+public_test\train+public_test').Path
$RunTag = Get-Date -Format 'yyyyMMdd-HHmmss'
$Smoke = Join-Path $Work "runs\sdk-smoke-$RunTag.jsonl"
& $Python scripts/smoke_runtime.py --data-root $Kit --out $Smoke
Get-Content -LiteralPath $Smoke
Get-Content -LiteralPath ([IO.Path]::ChangeExtension($Smoke, '.diagnostics.json'))
```

Expect `PASS`, one call, and a JSONL row with `id`, `tool_calls` and `state_hash`. The `.diagnostics.json` sidecar should report `stop_reason` as `DONE`. In the current kit the test selected `alarm.list`. This verifies loading, validation, execution and serialization. Model behavior is covered by the next step.

## 2. Run one model prediction

**Text first.** Follow the [Ollama setup](operator_guide.md#3-make-your-local-models-available) to start the local server and confirm the model tag with `ollama list`. Use a Python environment with the `ollama` extra. For the example Qwen tag, the handoff includes a matching tokenizer file under `../local_lifemate_artifacts/qwen3_tokenizer/`.

```powershell
& $Python -m pip install -e '.[ollama]'
$RunTag = Get-Date -Format 'yyyyMMdd-HHmmss'
$FoldPath = Join-Path $Work "data\folds-$RunTag.json"
& $Python -m lifemate freeze --data-root $Kit --out $FoldPath --seed 20261109 --heldout-app banking
$Tokenizer = (Resolve-Path -LiteralPath '..\local_lifemate_artifacts\qwen3_tokenizer\tokenizer.json').Path
$Pilot = Join-Path $Work "runs\oracle-pilot-$RunTag.jsonl"
$PilotArgs = @(
    '--data-root', $Kit, '--split', 'train', '--input-mode', 'oracle',
    '--selection', 'validation', '--split-config', $FoldPath, '--limit', '1',
    '--backend', 'ollama', '--ollama-model', 'qwen3:4b-instruct-2507-q4_K_M',
    '--tokenizer-path', $Tokenizer, '--sample-seconds', '180', '--out', $Pilot
)
& $Python -m lifemate predict @PilotArgs
```

If you already froze the same kit, point `$FoldPath` at that file and skip `freeze`. If you change the model tag, supply its matching tokenizer. `oracle` uses the train transcript, which isolates model decisions from speech recognition. The 180-second setting gives a CPU pilot more time. Use the [competition milestone](milestones/06-zalo-submission.md) for the official limit.

Open the pilot's `.run.json` and `.diagnostics.json` beside its JSONL file. Check the stop reason, actual calls, and timing. A complete file can contain a timed-out scenario with the real partial trace. A one-row pilot is useful for setup and debugging. Run the full selected fold for a baseline.

**Add audio next.** Use the [operator guide](operator_guide.md#5-generate-usable-inferenceevaluation-configs) to generate `$Work\configs\audio.json`. The shipped audio configuration uses a local Transformers-format language model and a separate Whisper-compatible checkpoint. Install `.[model,asr]` and set `model_path`, `tokenizer_path`, and `asr_path` to the corresponding local directories. The [model setup](operator_guide.md#3-make-your-local-models-available) explains what each directory needs. Use a fresh output and limit the first run to one sample.

```powershell
& $Python -m lifemate predict --config "$Work\configs\audio.json" --limit 1 --out "$Work\runs\audio-pilot-$RunTag.jsonl"
```

For a public result, use `split=public_test`, `input_mode=audio`, `selection=all`, a fresh output path and no row limit. Follow the [two validation checks](milestones/06-zalo-submission.md#1-validate-and-upload-the-public-result) before submission. For a same-scenario comparison with oracle text, follow [milestone 04](milestones/04-audio-and-evaluation.md).

## 3. Build the package

Use the [Python build guide](build.md) for the wheel, source archive, and
clean-install check. Use [offline packaging](offline_packaging.md) for the Linux
container and [milestone 06](milestones/06-zalo-submission.md) for the organizer's
launch, timing, and submission requirements.

## 4. Prepare and train LoRA

1. Prepare the frozen folds, replay report and trajectories from authorized train scenarios. Reuse the fold from step 2 if it matches the kit. Follow the commands in [local fine-tuning, section 1](local_training.md#1-what-training-data-is-available).
2. Set up `$TrainPython` with `.[training]` and supply a complete local Transformers-format base model and its matching tokenizer. Use the training config generator to record dataset, trajectory, split and chat-template fingerprints. Follow [local fine-tuning, sections 2–3](local_training.md#2-create-a-training-environment-and-supply-the-base-model).
3. Validate and then start training from a fresh output path. The dry-run reports the checked row count and `status: NOT RUN` because it stops before model loading and optimization. Use the Linux/CUDA instructions in the training guide when that is your training platform.

```powershell
$TrainingConfig = Join-Path $Work 'configs\training.json'
& $TrainPython -m lifemate train --config $TrainingConfig --dry-run
# Run this line when the inputs and training machine are ready.
& $TrainPython -m lifemate train --config $TrainingConfig
```

Look for `COMPLETE` in the training run's `run.json`, plus `adapter/` and `tokenizer/`. Load them with the original base model via the Transformers backend, then compare against the baseline on the same held-out scenarios. [Local fine-tuning, sections 5–7](local_training.md#5-find-the-trained-files)
