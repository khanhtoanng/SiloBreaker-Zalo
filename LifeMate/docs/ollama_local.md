# Local Ollama follow-up — 2026-11-10, Asia/Saigon

The user selected Ollama for local inference and confirmed the outer unzip folder
`../train+public_test`. The loader now accepts that folder or the inner kit root.
It rejects ambiguous wrappers and inspects only known split catalog paths.

## Observed setup

- Ollama was absent initially, and the local API connection was refused.
- Downloaded the Windows installer from the official Ollama site, verified its
  valid Authenticode signature from Ollama Inc., and installed it silently with
  hidden windows. Installer exit code: 0. Runtime version: **0.40.16**.
- Started a loopback-only service at `127.0.0.1:11434` with
  `OLLAMA_NO_CLOUD=1`. Server log explicitly confirms cloud disabled and CPU compute.
- Pulled **qwen3:4b-instruct-2507-q4_K_M** during setup. Ollama verified its SHA-256
  blobs before writing the manifest. No model download occurs in inference code.
- Downloaded the corresponding official Qwen tokenizer JSON outside source.
  `.venv` uses Python 3.11.15 and tokenizers 0.23.3. Tokenizer truncation and
  padding are explicitly disabled before counting.
- Synthetic JSON smoke: **PASS**. Total 20.42 seconds, including 15.08 seconds of
  model loading; server reported 35 prompt tokens and 7 generated tokens. No
  dataset or ToolEnv was opened for that setup test.
- Loaded model memory reported by Ollama: 5,113,412,320 bytes, zero VRAM,
  configured context 16,384 tokens. This is CPU inference, not GPU benchmarking.

The [official Ollama model page](https://ollama.com/library/qwen3:4b-instruct-2507-q4_K_M)
lists a 4.02B model with Q4_K_M quantization and an Apache 2.0 license. The
[official Qwen model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)
also identifies Apache 2.0. Competition eligibility and resource limits still
require the unavailable official rule guidance.

## Runtime behavior and verification

The backend calls the documented [local chat API](https://docs.ollama.com/api/chat)
with JSON mode, thinking disabled, temperature zero, fixed seed, context/generation
limits and a deadline-derived socket timeout. Model responses still go through the
same strict CALL/ASK/DONE parser, semantic preflight and official SDK validation.
It never accepts model-produced state hashes or lists of hypothetical executed calls.

The transport permits only loopback HTTP origins, disables proxies and redirects,
rejects cloud model names and remote-backed tags, and checks the model is already
installed. Its inference endpoint allowlist excludes pull/download operations.
The [local-only setting](https://docs.ollama.com/faq#how-do-i-disable-ollamas-cloud-features)
is applied to the started server process without overwriting user account settings.

Context counting uses the corresponding local Qwen tokenizer plus a conservative
256-token framing reserve and the generation budget. Without a supplied tokenizer,
the backend falls back to a stricter UTF-8-byte bound. No schemas or history are
silently removed by the project. Initial validation prompts range from 2,110 to
9,644 content tokens (median 5,182); all 309 fit the initial configured budget.
The reserve is a project guard, not an exact native Ollama template tokenizer.

**68 tests PASS**, including loopback restrictions, redirect/cloud blocking,
missing-model behavior, JSON request shape, metadata, context guards, deadline
handling, invalid responses and the unzip wrapper resolver. Model quality is
established separately by the pilot/evaluation artifacts, not these fixtures.

## Pilot

The fixed pilot selects the first three IDs in manifest order from the existing
309-scenario validation fold. It runs train oracle text through one official
ToolEnv per scenario. The per-scenario allowance is **180 seconds** to diagnose
CPU performance. The full fold, ASR, LoRA, target-GPU timing and competition Docker
checks remain pending.

Results and model provenance are saved outside source:

- `../local_lifemate_artifacts/ollama_smoke.json`
- `../local_lifemate_artifacts/ollama_pilot_3.jsonl`
- `../local_lifemate_artifacts/ollama_pilot_3.diagnostics.json`
- `../local_lifemate_artifacts/ollama_pilot_3.run.json`
- `../local_lifemate_artifacts/ollama_pilot_3_evaluation.json`

The model digest, tokenizer SHA-256, source fingerprint, server version, selected
IDs and decoding/budget settings are recorded in the run metadata. Per-scenario
completed outputs are persisted during the run. There is no automatic replay or
resume of a partially executed environment.

## Rechecked organizer evidence

The confirmed outer unzip directory contains the same kit README, two split SDK
READMEs, catalogs, manifests, audio/environment directories and sample submission.
Its metadata/source filename inventory contains no additional scorer, Rule,
Evaluation or Docker guidance. Hidden state contents were not inspected. The
official scorer and submission/resource contracts remain UNKNOWN.


## LM-002 current software delivery (2026-11-10)

Historical evidence above retains its original meaning. Current layered software adds
strict Pydantic contracts, enforced references/goal occurrences, local audio code,
real lazy LoRA integration and atomic complete-run publication. See
[operator_guide.md](operator_guide.md), [local_training.md](local_training.md),
[edge_case_coverage.md](edge_case_coverage.md) and revision-bound
[implementation evidence](ai/work/LM-002-python-structure-training-guide/implementation.md)
for exact checks/exit codes and limits. Fixtures do not prove learned quality,
official scoring parity, successful training, target GPU or offline image compliance.
Ollama is inference only. Dry-run loads no model/tokenizer/session/training runtime.
Reference enforcement is active without the deprecated diagnostic flag.
