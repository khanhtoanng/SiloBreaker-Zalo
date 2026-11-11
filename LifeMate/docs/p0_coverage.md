# P0 coverage and remaining policy work

All fixtures are synthetic unless the row explicitly states authorized train.
Passing a scripted decision sequence proves orchestration only; it does not prove
the language model chooses that sequence for a spoken request.

| Cases | Implemented evidence | Remaining limit |
|---|---|---|
| K01–K05 | Installed-tool intersection; required/enum/integer/range/x-one-of rejection; log-free SDK validation | Model repair quality NOT RUN |
| K06 | SDK unknown-reference no-op verified; provenance index tests cover live/history/literal IDs | Blocking is opt-in; existence/entity/type correctness not guaranteed |
| K07–K08 | Nested required preflight and unknown-field rejection | Optional defaults remain model/schema driven |
| K09–K11 | Failed calls logged in real SDK; exact getter serialization; one env per inference test | Target-platform concurrency/duration NOT RUN |
| K12–K13 | History preserved without replay; separate SDK namespaces; missing catalog fails | Audio history ASR NOT IMPLEMENTED |
| K18 | Synthetic insufficient balance returns no-op; loop stops without repeating | Learned recovery and independent pending goals need validation |
| K25–K26 | ASK requires correct structure, installed target and real parameter names | Semantic choice of missing parameter needs a model run |
| K27–K28 | Scripted DONE preserves empty real trace; completed write followed by terminal ASK retained | Unsupported/partial-goal recognition needs a model run |
| K29 | Scripted multi-step continuation and six calls plus DONE pass | Semantic goal ledger and premature-DONE checks PENDING |
| K30 | Uncertain and no-op writes terminate; prompt prohibits retries after success | Detecting repeated successful writes versus deliberate repeat intent PENDING |
| K35–K37 | SDK ride scheduling at past/equal/future sample time; required vehicle rejection | Natural-language date/vehicle inference needs a model run |
| K38 | Positive integer amount schema enforced | Vietnamese money normalization and paired critical-slot tests PENDING |
| K45–K48 | SDK hash collisions/free-text and information-app behavior; evaluator checks arguments and excess calls independently | Official score impact UNKNOWN |
| K53 | Duplicate/missing/malformed rows, hash format and JSONL roundtrip | Full model manifest and official final validator NOT RUN |

Additional P1 checks: K19 wrong device type SDK no-op, K49 scalar/object ordering,
K54 public-only tool registry, observation-grounded ID use and history provenance.
Remaining P1 semantic cases, learned retry/repetition decisions, ASR cases and
paired ablations are a backlog. **The full P0 model-behavior gate has not passed.**


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
