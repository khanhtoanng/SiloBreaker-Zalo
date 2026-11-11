# Local organizer-kit audit — 2026-11-10 (Asia/Saigon)

**Ollama follow-up:** Local model setup is now available via Ollama 0.40.16 and
Qwen3 4B Instruct. The base Python still has no torch/transformers/ASR stack, but
the project `.venv` has tokenizers for the Ollama backend. The user-confirmed outer
unzip folder was rechecked; it adds no scorer or Docker guidance beyond the kit
already audited. See [local Ollama evidence](ollama_local.md).

**OBSERVED:** The supplied ZIP and extracted local kit identify release v3.2.0,
built 2026-10-24. Its README authorizes labeled train checks through ToolEnv and
prohibits direct environment-file inspection and dataset redistribution.
No organizer source/catalog, raw audio, states or labels were copied into this
implementation directory. Missing train SDK/environment assets were extracted
from the supplied ZIP into its sibling authorized data directory. Application
state was inspected only through SDK `get_state()` during standalone train gold
replay, as explicitly described by the organizer executor documentation.
Inference never calls `get_state()`.

## Catalog and SDK facts

| Property | Train | Public test |
|---|---:|---:|
| Manifest rows | 1,545 | 634 |
| Catalog schema | 2.7.0 | 2.7.0 |
| Apps including sys | 46 | 36 |
| Tools | 147 | 122 |
| Shared apps | 25 | 25 |
| SDK Python files | 53 | 45 |
| Catalog tools absent from SDK registry | 0 | 0 |

**OBSERVED:** 34 tools are public-only and 59 are train-only; all shared tool
specifications are equal. Eleven public-only apps are ecommerce, event_tickets,
grocery, habit_tracker, pantry, parking, public_transit, recipes, stocks,
train_bus_tickets and translator. Inventory: [catalog_audit.json](catalog_audit.json).

**OBSERVED:** Of 32 shared SDK Python paths, only `utils.py` differs in source bytes.
The train information-app exclusion set contains exchange_rate, fuel_price,
gold_price, lottery and weather; public contains fuel_price, gold_price and
weather. Train drops `expression` from canonical state; public drops `text`
instead. The remaining free-text exclusion keys are shared. Synthetic tests
verify the differing hash behavior using each SDK's own hash function.

**INFERRED implementation consequence:** A copied train hash implementation would
be incorrect for some public states. The adapter imports each split package under
a unique module name and submits only `env.get_state_hash()` from that package.
There is no project hash implementation.

**OBSERVED:** SDK validation does not log, failed executed calls remain in traces,
x-ref existence is not schema-validated, nested required properties are not
recursively checked, and business failures can return ok:true/done:false. Both
past and equal-current-time ride schedules become immediate rides. Own preflight
rejects unknown argument fields and nested malformed objects before execution.

## Scorer, rules and release status

**OBSERVED:** The archive includes SDK schema checking, not a scoring algorithm.
The official CLI checks calls against each sample's allowed tools and prints an
error count. It does not establish scoring parity or full manifest completeness.
Project submission checks additionally enforce IDs, order, field types and hash
format. The CLI itself does not use a failing exit code for schema errors, so its
printed count must be inspected.

**UNKNOWN:** official call matching, fuzzy threshold, hash gate, model limits,
weight release cutoff, GPU/latency limits, context limit, external-data rules,
Docker entrypoint/mount/output paths and final submission requirements. Numeric
values in the handoff remain proposals or reported constraints, not certification.
The [official portal](https://challenge.zalo.ai/portal/lifemate) was checked on
2026-11-10; the browser extraction returned zero readable lines. No schedule or
current rule claim was inferred from that response.

**OBSERVED hardware/software:** Python 3.12.0; uv available; active Python has no
torch, transformers, pytest or faster_whisper modules. Win32_VideoController
reports Intel Iris Xe Graphics. Docker and nvidia-smi were not found on PATH.
This does not establish the availability of remote compute.

**Next evidence needed:** local reviewed model path plus compute; official scorer
and Rule/Evaluation/Submission Guidance. Never request protected raw state or test
labels. No training or competition Docker compliance claim is made.

The optional model adapter follows the official Transformers interfaces for
[generation](https://huggingface.co/docs/transformers/v4.57.1/en/main_classes/text_generation)
and [local/offline setup](https://huggingface.co/docs/transformers/v4.57.1/en/installation).
Dependency declarations are optional development requirements, not a tested release
lock. The backend still requires a real local-model smoke and full holdout run.
