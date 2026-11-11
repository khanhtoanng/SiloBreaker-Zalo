# Fine-tune the LifeMate action policy locally

This guide covers the supplied training data, generated model-ready examples,
LoRA configuration, execution, saved adapter and inference. These are instructions
for your local run. Real model training in this checkout is **NOT RUN**.

Start with sections 1–4 of [Run LifeMate locally](operator_guide.md). They define
`$Project`, `$Kit`, `$Work`, install the app and produce the required data files.
Ollama does not train LoRA in this project. The trainer adapts the action policy
using a local Transformers-format base model with PEFT/TRL. Speech recognition
uses its own local checkpoint.

## 1. What training data is available?

Your supplied kit contains `train/train.jsonl`, train audio, the train tool catalog
and the train SDK. Training records include authorized transcript/history/context
and gold calls/results. Public/private-test data is for inference/evaluation, not
for fitting this policy.

The data-preparation sequence is:

```powershell
& $Python -m lifemate freeze --data-root $Kit --out "$Work\data\folds-run001.json" --seed 20261109 --heldout-app banking
& $Python -m lifemate replay --data-root $Kit --out "$Work\data\replay-run001.json"
& $Python -m lifemate trajectories --data-root $Kit --split-config "$Work\data\folds-run001.json" --out "$Work\data\trajectories-run001.jsonl"
```

Run these once with new filenames. If you already ran the operator guide's commands,
use those same outputs rather than rerunning into existing destinations.

| Generated file | Purpose |
|---|---|
| `folds-run001.json` | Scenario-level fit/validation IDs, seed, source identity and app-out fold |
| `replay-run001.json` | SDK replay results and reference hashes for later evaluation |
| `trajectories-run001.jsonl` | Model-ready action examples with replayed observation prefixes |

Every trajectory line is a `TrajectoryRecord` with:

| Field | Meaning |
|---|---|
| `scenario_id` | Original scenario, shared by all its action rows |
| `source_split` | Always `train` |
| `partition` | `fit` or `validation`, inherited before expansion |
| `fold` | `grouped` or `leave-app-out` |
| `step_index` | Number of preceding observations |
| `messages` | System/context prompt plus one assistant action target |
| `target` | One CALL, ASK or DONE object |
| `identities` | Source/fold/schema and action/context protocol identities |

For a read followed by a write, the first row targets the read, the next row sees
the actual read observation and targets the write, and the final row targets DONE.
ASK scenarios also receive terminal DONE; zero-call scenarios produce immediate
DONE. The assistant target uses the same action JSON as inference:

```json
{"kind":"CALL","tool_name":"sms.send","arguments":{"contact_id":"example_id","content":"Example message"}}
```

This JSON is illustrative, not a standalone training dataset. Use the trajectory
command's complete output, which supplies eligible schemas, real prefixes and
required identities. It keeps all rows from one scenario in the same partition.
Do not manually mix public-test rows or future observations into the fit data.

For app-out training, generate a separate file using `--fold leave-app-out`, then
set the training config's `fold` and trajectory path consistently. Keep its outputs
separate from the grouped experiment.

## 2. Create a training environment and supply the base model

From the source root, create a dedicated environment if you have not already chosen
one with the training extra:

```powershell
Set-Location -LiteralPath $Project
$TrainVenv = Join-Path $Work 'venvs\training'
python -m venv $TrainVenv
$TrainPython = Join-Path $TrainVenv 'Scripts\python.exe'
$env:PIP_CACHE_DIR = Join-Path $Work 'cache\pip'
$env:PYTHONDONTWRITEBYTECODE = '1'
& $TrainPython -m pip install -e '.[training]'
```

If your existing chosen environment already has `.[training]`, set `$TrainPython`
to its Python executable instead. This code selects ordinary LoRA, not QLoRA or
bitsandbytes. Dependency declarations include Transformers 4.56.2, PEFT 0.17.1,
TRL 0.23.1, torch >=2.2,<3, Accelerate >=1.4,<2 and Datasets >=3,<4.

Place a complete compatible local CausalLM and matching tokenizer in
`$Work/models/base`, including `config.json`, complete weights and
`tokenizer_config.json` with a string `chat_template`. Model modules must be supported
by the installed Transformers version with `trust_remote_code=False`.
The trainer loads the tokenizer and base with `local_files_only=True`. If the
tokenizer has no padding token, it uses `pad==EOS` as a fallback. Padding positions
are masked independently of their token ID, so the target's EOS is still supervised.
See the operator guide for explicit model download/copy instructions. Check the
model's license and hardware requirements yourself before choosing it.

The default example uses fp32. fp16/bf16 require the supported CUDA capabilities;
bf16 support is checked by the runtime. GPU memory depends on base size, context,
batch and activations. CPU fp32 can be slow or too large for the machine. The
project does not promise that the example base/context fits your hardware.

## 3. Generate the complete training configuration

The shipped `configs/training.lora.json` contains placeholders. The following
generator fills paths and required identities from your actual prepared files.
Save it as `$Work/create_training_config.py` using a UTF-8 editor:

```python
import json
import sys
from pathlib import Path

from lifemate.contracts import json_object
from lifemate.provenance import digest, file_sha256

project, kit, work = map(Path, sys.argv[1:])
base = work / "models/base"
fold_path = work / "data/folds-run001.json"
trajectory_path = work / "data/trajectories-run001.jsonl"
folds = json_object(fold_path.read_text(encoding="utf-8"))
manifest_hash = file_sha256(kit / "train/train.jsonl")
if manifest_hash != folds["dataset_sha256"]:
    raise ValueError("Train manifest changed; regenerate the data chain")
template = json_object((base / "tokenizer_config.json").read_text(encoding="utf-8"))["chat_template"]
if not isinstance(template, str):
    raise ValueError("This trainer expects a string chat_template")
config = json_object((project / "configs/training.lora.json").read_text(encoding="utf-8"))
config.update(
    source_split="train",
    base_model=str(base),
    tokenizer_path=str(base),
    trajectories=str(trajectory_path),
    split_config=str(fold_path),
    out=str(work / "adapters/lora-run001"),
    fold="grouped",
    dataset_sha256=manifest_hash,
    trajectories_sha256=file_sha256(trajectory_path),
    split_sha256=file_sha256(fold_path),
    template_sha256=digest(template),
)
destination = work / "configs/training.json"
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(destination)
```

Run the generator and select the resulting config:

```powershell
& $TrainPython "$Work\create_training_config.py" $Project $Kit $Work
$TrainingConfig = Join-Path $Work 'configs\training.json'
```

Edit the optimization fields to match the selected model and machine:

| Setting | Shipped example | Meaning |
|---|---:|---|
| `rank`, `alpha` | 16, 32 | LoRA rank/scaling |
| `dropout` | 0.05 | Adapter dropout |
| `target_modules` | `q_proj`, `v_proj` | Must match actual modules in your base model |
| `epochs`, `learning_rate` | 1.0, 0.0002 | Optimization duration/rate |
| `batch_size` | 1 | Per-device batch |
| `accumulation_steps` | 8 | Steps accumulated before an update |
| `precision` | `fp32` | `fp32`, supported `fp16` or supported `bf16` |
| `max_sequence_length` | 8192 | Maximum complete prompt + current action + EOS |
| `seed` | 20261109 | Run seed |

These are examples, not tuned settings. Required tools/history/actions are never
silently truncated. If examples exceed the sequence limit, use a supported larger
context and enough memory or adjust your eligible workload/model choice. Do not
delete required schemas or labels to force an example to fit.

## 4. Start fine-tuning when ready

An optional config/data preflight loads no real tokenizer/model and starts no training:

```powershell
& $TrainPython -m lifemate train --config $TrainingConfig --dry-run
```

The actual training command is:

```powershell
& $TrainPython -m lifemate train --config $TrainingConfig
```

Equivalent script entrypoint, for the same single run:

```powershell
& $TrainPython scripts/train_lora.py --config $TrainingConfig
```

Choose one entrypoint. The trainer loads local assets, converts fit/validation
examples, applies LoRA and invokes real `SFTTrainer.train()`. Its labels supervise
only the current action plus EOS: system/user/history/tool observations/previous
actions and padding have label `-100`. Exact tokenizer-prefix and action-roundtrip
checks happen during conversion; oversize or inconsistent examples fail explicitly.
No goal-planning objective or ASR fine-tuning is silently added.

## 5. Find the trained files

```text
LifeMateWork/adapters/lora-run001/
  run.json                # RUNNING / COMPLETE / FAILED / INTERRUPTED
  config.json             # Chosen training settings
  inputs.json             # Declared local input metadata/identity coverage
  checkpoints/            # Trainer checkpoints
  adapter/                # PEFT adapter config and weights
  tokenizer/              # Saved tokenizer and template
  metrics.json            # Returned training metrics
  provenance.json         # Data/code/config and saved-artifact identities
```

The run is COMPLETE only after the required adapter/tokenizer files exist. Failure
or interruption leaves its status and available partial checkpoints. Existing output
directories refuse overwrite; use `lora-run002` for another run. Automatic checkpoint
resume is not implemented. A recorded metadata hash does not claim complete base
weight identity when that coverage is explicitly marked UNMEASURED.

## 6. Run the saved adapter

For train oracle-text holdout inference, use the training environment, which includes
the Transformers/PEFT dependencies:

```powershell
& $TrainPython -m lifemate predict --data-root $Kit --split-config "$Work\data\folds-run001.json" --backend transformers --model-path "$Work\models\base" --tokenizer-path "$Work\adapters\lora-run001\tokenizer" --adapter-path "$Work\adapters\lora-run001\adapter" --out "$Work\runs\lora-run001.jsonl" --sample-seconds 300
```

Use the original base model that produced the adapter. For audio, add the ASR extra
to the chosen environment and set the same base/tokenizer/adapter plus local speech
path in an audio config. Evaluation uses a copy of the operator guide's evaluation
config pointing to this prediction file and a new report filename.

Keep frozen IDs, input mode, budgets and replay reference consistent when comparing
with the baseline. Training loss alone is not an end-to-end quality result.
Loading the saved adapter directly through Transformers is implemented. Automatic
conversion/merge/import into Ollama is not part of this code.

## 7. Linux/CUDA local training alternative

Use Linux paths throughout the config. For WSL, point `PROJECT` to the mounted source
or a Linux checkout, `KIT` to the complete supplied kit, and `WORK` to your work area:

```bash
PROJECT=/path/to/LifeMate
KIT=/path/to/kit
WORK="$HOME/LifeMateWork"
python3 -m venv "$WORK/venvs/training"
. "$WORK/venvs/training/bin/activate"
export PIP_CACHE_DIR="$WORK/cache/pip"
export PYTHONDONTWRITEBYTECODE=1
cd "$PROJECT"
python -m pip install -e '.[training]'
```

Install the PyTorch build appropriate to your CUDA/driver setup if the default
package resolution does not match it. Prepare/download assets locally, run the
same freeze/replay/trajectories commands with Linux paths, and save the section 3
generator at `$WORK/create_training_config.py`. Then:

```bash
python "$WORK/create_training_config.py" "$PROJECT" "$KIT" "$WORK"
python -m lifemate train --config "$WORK/configs/training.json"
```

Change `precision` to a supported CUDA mode only after choosing the actual platform.
Do not reuse a Windows config's drive-letter paths unchanged under Linux.

## Troubleshooting

- **Missing asset/template:** provide the complete matching base/tokenizer folder;
  a model tag or GGUF file cannot replace it.
- **Wrong target modules:** edit `target_modules` for the base architecture.
- **Out of memory:** lower per-device batch, increase accumulation, or choose suitable
  context/model/hardware. Ordinary LoRA here does not provide QLoRA quantization.
- **Fingerprint/fold mismatch:** regenerate the complete data chain with new names
  from the intended train source and update the config through the generator.
- **Template-prefix/roundtrip error:** use a compatible tokenizer/chat template;
  conversion rejects inconsistent targets instead of silently changing the masks.
- **Existing output/interruption:** keep the old run and choose a new output directory.
- **Poor actions after training:** inspect actual held-out predictions and relevant
  slices. The training job saving an adapter does not establish language quality,
  official scoring parity or target-hardware performance.
