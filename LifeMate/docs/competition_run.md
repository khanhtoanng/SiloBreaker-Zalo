# Run the LifeMate competition solution

Run from `LifeMate/` using Python 3.10 or later. Install a CUDA-enabled PyTorch build at version 2.6 or newer, then install the ASR extra and JupyterLab. PhoWhisper's pinned model uses PyTorch's `.bin` weight format. Prepare the Python dependencies and model files while online. Prediction uses the local files and the mounted split's organizer SDK.

```bash
python -m pip install '.[asr]' jupyterlab
```

| Default path relative to `LifeMate/` | Asset |
| --- | --- |
| `bin/llama-server` | CUDA-enabled llama.cpp server, tested with [b12340](https://github.com/ggml-org/llama.cpp/releases/tag/b12340) |
| `saved_models/policy.gguf` | Pinned Qwen3-4B-Instruct-2507 Q4_K_M file |
| `saved_models/asr/` | Pinned PhoWhisper-small model and processor files |

The checkpoint URLs, revisions and training instructions are in [training_code/README.md](../training_code/README.md). Place the Python package, launcher scripts, `configs/` and notebook in the same application layout for the final image. Pass the organizer data root that contains `public_test/` or `private_test/`. The organizer SDK is loaded from that split.

## Public test on Windows

The command below uses the local dependencies and checkpoints prepared beside this checkout. Give each run a fresh output directory. Remove `--limit 8` for a full 634-sample run. This command writes the public kit's three-field upload format.

```powershell
$Work = (Resolve-Path '../local_lifemate_artifacts').Path
$Kit = (Resolve-Path '../train+public_test/train+public_test').Path
$Python = Join-Path $Work '.venv/Scripts/python.exe'
$env:PYTHONPATH = (Resolve-Path 'src').Path
$env:PYTHONHASHSEED = '20261109'
$RunName = Get-Date -Format 'yyyyMMdd-HHmmss'
$Output = Join-Path $Work "runs/$RunName/submission.jsonl"

& $Python -m lifemate predict --data-root $Kit --split public_test --input-mode audio --selection all `
  --backend llama_cpp --llama-server-path "$Work/llama/bin/llama-server.exe" `
  --model-path "$Work/models/gguf/policy.gguf" --asr-path "$Work/models/asr" `
  --max-new-tokens 384 --out $Output --limit 8
```

For a complete public result, run the `lifemate validate` and organizer `zaic_tools --validate` commands in [milestone 06](milestones/06-zalo-submission.md). Check the `.diagnostics.json` sidecar for timeouts and blocked calls before uploading.

## Private test and timing notebook

`bash /code/predict.sh` uses `configs/inference.competition.json`. Its defaults read `/data/private_test/`, write `/result/submission.jsonl`, and print model load and total prediction time. The `time` field is the elapsed integer milliseconds for each sample, including WAV processing, model inference and simulator calls. Add `--include-timing` when validating timed output with `lifemate validate`.

`bash /code/start_jupyter.sh` launches JupyterLab at port `9777` with token `zac2026`. Run all four cells of `predict_notebook.ipynb` to write `/result/jupyter_submission.jsonl` independently. Compare `id`, `tool_calls`, and `state_hash` with the script output. Each run measures its own timings.
