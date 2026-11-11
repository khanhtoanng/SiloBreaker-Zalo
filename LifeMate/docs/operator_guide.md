# Run LifeMate locally

Use this runbook for model inference, training data preparation, and evaluation.
For the first SDK smoke test and regression checks, use the [local quickstart](local_quickstart.md).

## 1. Set your paths

Open PowerShell in `LifeMate/`, where `pyproject.toml` lives. Set the kit path
to match your extraction. The example uses a separate user-owned work directory.

```powershell
$Project = (Get-Location).Path
$Kit = (Resolve-Path -LiteralPath '..\train+public_test\train+public_test').Path
$Work = Join-Path $env:USERPROFILE 'LifeMateWork'
$Venv = Join-Path $Work 'venvs\app'
$Python = Join-Path $Venv 'Scripts\python.exe'
New-Item -ItemType Directory -Force -Path $Work, "$Work\configs", "$Work\data", "$Work\runs", "$Work\reports", "$Work\models", "$Work\adapters" | Out-Null
```

The expected external kit layout is:

```text
kit/
  train/
    train.jsonl
    train_tools_catalog.json
    zaic_tools/
    audio/
    ... organizer-owned assets
  public_test/
    public_test.jsonl
    public_test_tools_catalog.json
    zaic_tools/
    audio/
```

The loader also accepts one outer unzip wrapper. Every selected split needs its
own manifest/catalog/SDK. Missing private-test assets fail explicitly. Keep the
organizer folder intact; do not manually inspect environment-state files or put
generated files inside the kit/source/model directories.

## 2. Create an app environment

Use Python 3.10 or newer. Create a new environment; keep existing environments
intact. Every later command uses the explicit `$Python`, so activation is optional.

```powershell
python -m venv $Venv
$env:PIP_CACHE_DIR = Join-Path $Work 'cache\pip'
$env:PYTHONDONTWRITEBYTECODE = '1'
```

Choose the installation matching what you will run:

```powershell
# Local Ollama policy + train oracle-text mode and data preparation:
& $Python -m pip install -e '.[ollama]'

# Add local speech recognition and Transformers inference when needed:
& $Python -m pip install -e '.[ollama,model,asr]'

# Add policy fine-tuning when you are ready for it:
& $Python -m pip install -e '.[ollama,asr,training]'
```

The lines are incremental choices, not three required setup steps. Training and
ASR install large optional dependencies. Pick a PyTorch/platform combination that
fits your machine. The shipped training recipe is ordinary LoRA; fp16/bf16 require
the supported CUDA capabilities. CPU fp32 exists but can be very slow or exceed
available memory. A Linux/CUDA training setup is described in the training guide.

## 3. Make your local models available

### Ollama policy

Install/open [Ollama](https://ollama.com/) if needed. Use a local model, not a cloud
tag. The shipped example tag is `qwen3:4b-instruct-2507-q4_K_M`; use a compatible
local tag actually available on your installation.

```powershell
ollama list
# Only if you choose to download this example model during setup:
ollama pull qwen3:4b-instruct-2507-q4_K_M
```

If the desktop app is not already serving, start a local server in a second terminal:

```powershell
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_NO_CLOUD = '1'
ollama serve
```

Keep one server running. LifeMate connects to loopback, rejects remote/cloud-backed
models and does not pull a missing model during prediction. See the official
[Ollama quickstart](https://docs.ollama.com/quickstart) and
[server configuration](https://docs.ollama.com/faq).

### Transformers policy, training base and speech model

For fine-tuning, supply a complete Transformers-format CausalLM folder and matching
tokenizer/chat template. An Ollama GGUF model alone is not that training base. For
audio, supply a local Whisper-compatible processor/model folder. ASR uses an existing
model; this project fine-tunes the action policy.

Use these locations, or edit the generated configs to point to existing folders:

```text
LifeMateWork/models/base/   # config, tokenizer/template, complete model weights
LifeMateWork/models/asr/    # processor/preprocessor, tokenizer, speech weights
```

You can copy complete local model folders. Alternatively, after selecting eligible
repositories, download them explicitly during setup. Replace the repository strings:

```powershell
@'
import sys
from pathlib import Path
from huggingface_hub import snapshot_download
work = Path(sys.argv[1])
snapshot_download(repo_id="REPLACE_WITH_CAUSAL_LM_REPOSITORY", local_dir=work / "models/base")
snapshot_download(repo_id="REPLACE_WITH_WHISPER_REPOSITORY", local_dir=work / "models/asr")
'@ | & $Python - $Work
```

`huggingface_hub` is supplied with the model/training dependencies. Gated models
require access through the provider's normal setup. Choose model licenses and
sizes appropriate to your use and hardware. Record the chosen model revision.
This follows the provider's [local-folder download API](https://huggingface.co/docs/huggingface_hub/guides/download).
LifeMate's runtime loaders use local files and do not download missing weights.

## 4. Prepare the supplied training data

The raw training data is already in your kit's `train/train.jsonl` with authorized
transcripts and labels. Do not fine-tune on public/private-test labels. Freeze the
scenario split before expanding multi-step decisions:

```powershell
& $Python -m lifemate audit --data-root $Kit --out "$Work\data\catalog-run001.json"
& $Python -m lifemate freeze --data-root $Kit --out "$Work\data\folds-run001.json" --seed 20261109 --heldout-app banking
& $Python -m lifemate replay --data-root $Kit --out "$Work\data\replay-run001.json"
& $Python -m lifemate trajectories --data-root $Kit --split-config "$Work\data\folds-run001.json" --out "$Work\data\trajectories-run001.jsonl"
```

These are real data-preparation commands when you run them. Replay uses the train
SDK and compares actual results with train labels; inspect its report before using
it as an evaluation reference. Trajectory preparation replays each preceding action
and fails on drift. It produces fit/validation rows, CALL/ASK targets and a terminal
DONE for each scenario. No future observation is placed before its action target.

For a separate app-generalization dataset, use the same frozen file and a new output:

```powershell
& $Python -m lifemate trajectories --data-root $Kit --split-config "$Work\data\folds-run001.json" --fold leave-app-out --out "$Work\data\trajectories-appout-run001.jsonl"
```

Set training/inference `fold` to the same selection. Never mix grouped rows with an
app-out training config. If raw manifest bytes change, create new folds, replay,
trajectories and run names instead of silently reusing old identities.

## 5. Generate usable inference/evaluation configs

Run this with the variables from section 1. It writes UTF-8 JSON without a Windows
PowerShell BOM and replaces the shipped placeholder paths. It does not load a model:

```powershell
@'
import json, sys
from pathlib import Path
project, kit, work = map(Path, sys.argv[1:])
def example(name):
    return json.loads((project / "configs" / name).read_text(encoding="utf-8"))
def save(name, value):
    (work / "configs" / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
oracle = example("inference.ollama.json")
oracle.update(data_root=str(kit), out=str(work / "runs/oracle-run001.jsonl"),
              split_config=str(work / "data/folds-run001.json"), sample_seconds=300.0)
save("oracle.json", oracle)
audio = example("inference.audio.json")
audio.update(data_root=str(kit), out=str(work / "runs/audio-run001.jsonl"),
             model_path=str(work / "models/base"), tokenizer_path=str(work / "models/base"),
             asr_path=str(work / "models/asr"), sample_seconds=300.0)
save("audio.json", audio)
evaluation = example("evaluation.json")
evaluation.update(data_root=str(kit), out=str(work / "reports/oracle-run001.json"),
                  split_config=str(work / "data/folds-run001.json"),
                  predictions=str(work / "runs/oracle-run001.jsonl"),
                  replay=str(work / "data/replay-run001.json"))
save("evaluation.json", evaluation)
'@ | & $Python - $Project $Kit $Work
```

Edit `ollama_model` if you selected a different installed tag. The audio example
uses Transformers. To use Ollama with speech recognition, set `backend` to `ollama`,
set `ollama_model`/`ollama_url`, and retain the local `asr_path`. The example budget
of 300 seconds is for local development, not an official competition limit or a
performance guarantee. Adjust context length, sample budget and generation caps
to your assets/hardware. Relative JSON paths resolve beside the JSON file; explicit
CLI paths resolve from the shell's current directory.

## 6. Run text and audio inference

For the train oracle-text validation fold:

```powershell
# A separate pilot output avoids occupying the full-run destination:
& $Python -m lifemate predict --config "$Work\configs\oracle.json" --out "$Work\runs\oracle-pilot001.jsonl" --limit 1
# Full selected validation fold:
& $Python -m lifemate predict --config "$Work\configs\oracle.json"
```

For public-test audio with local Transformers and Whisper:

```powershell
& $Python -m lifemate predict --config "$Work\configs\audio.json"
```

Oracle text is train-only. Public/private audio uses `selection=all`; each selected
split must have its own assets. For train audio validation, set `split=train`,
`selection=validation` and the frozen `split_config` in an audio config.

Current speech input is readable mono/stereo PCM WAV, at least 8 kHz, at most
30 seconds per latest/history turn. Longer input fails explicitly. History speech
is associated chronologically; already applied history tool calls are not replayed.

The policy receives current context, full eligible schemas, normalized evidence and
actual observations. It proposes CALL/ASK/DONE; the same SDK session supplies final
calls/hash. Ambiguity and unsupported normalization remain explicit, and the actual
model's interpretation still determines practical language quality.

## 7. Fine-tune and load the adapter

After section 4 has produced the grouped data, follow
[Local fine-tuning](local_training.md). That guide generates the complete training
JSON, including the required data/fold/template identities, and shows the training
command and output layout. Do not train an Ollama GGUF directly.

After a run saves `adapters/lora-run001`, use the Transformers backend with the
original base, saved tokenizer and adapter:

```powershell
& $Python -m lifemate predict --data-root $Kit --split-config "$Work\data\folds-run001.json" --backend transformers --model-path "$Work\models\base" --tokenizer-path "$Work\adapters\lora-run001\tokenizer" --adapter-path "$Work\adapters\lora-run001\adapter" --out "$Work\runs\adapter-run001.jsonl" --sample-seconds 300
```

For adapter audio, put the same three model paths in a copy of `audio.json` and use
a new output name. Automatic merge/conversion/import of a trained adapter into
Ollama is not implemented; direct local Transformers adapter loading is supported.

## 8. Outputs and optional evaluation

For `oracle-run001.jsonl`, the workflow writes:

| File | Meaning |
|---|---|
| `oracle-run001.jsonl` | Final complete rows: only `id`, actual `tool_calls`, `state_hash` |
| `oracle-run001.run.json` | Selected/completed IDs, settings, identities and status |
| `oracle-run001.partial.jsonl` | Explicit checkpoint of completed rows |
| `oracle-run001.diagnostics.json` | Proposals, actual observations, goals, transcripts, timing and stop reasons |

Existing destinations refuse overwrite. Choose a new run name after failure or
interruption; no automatic resume or SDK-session reconstruction exists. A failed
run has FAILED/INTERRUPTED metadata and does not publish an incomplete final result.

When you want to evaluate a complete oracle run:

```powershell
& $Python -m lifemate evaluate --config "$Work\configs\evaluation.json"
& $Python -m lifemate compare --baseline "$Work\reports\baseline.json" --candidate "$Work\reports\candidate.json" --out "$Work\reports\paired-run001.json"
```

For an adapter report, copy/edit `evaluation.json` so `predictions` and `out` use
the adapter run. Paired reports require the same frozen selection/replay/matching
identity. Scores are local **PROXY** results, not an official scorer certification.

Use `python -m lifemate asr-evaluate` with `--reference`, `--candidate` and `--out`
to compare existing transcript artifacts without launching models. Supply equal
`identity` objects and `records` containing matching `id`/`text`, plus optional
context and downstream measurements. See `metrics/asr.py` for the input contract.
Use `python -m lifemate config-check --kind inference --config PATH` to resolve
settings before starting a run. Use `python -m lifemate validate` to check the
completed full-split result against its manifest. See the [Zalo submission
milestone](milestones/06-zalo-submission.md) for both validation commands and the
competition-specific container contract.

## Common problems

| Symptom | Action |
|---|---|
| Missing `pydantic` or `lifemate` | Use `$Python` from the environment installed in section 2 |
| Model not found | Finish the explicit local setup; check the model tag/folder and config |
| Ollama server unavailable | Open the desktop app or keep one loopback server running |
| Output overlap/existing destination | Choose a new path outside source, supplied/resolved kit and model inputs |
| Fold/source fingerprint mismatch | Regenerate the data chain with new filenames from the intended train manifest |
| CONTEXT_OVERFLOW | Increase supported context/memory or choose suitable assets; required schemas/targets are not truncated |
| TIMEOUT | Increase the development budget or use faster local hardware/model settings |
| Training OOM | Reduce batch size, increase accumulation, or use suitable smaller assets/context/hardware |
| Unsupported config option | Use the declared JSON fields; QLoRA and implicit checkpoint resume are not implemented |
| Uncertain time/reference or BLOCKED | Inspect raw request/normalization/observations; do not treat uncertainty as successful completion |

