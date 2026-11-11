# Experiment ledger

Date: 2026-11-10, Asia/Saigon. The initial CPU checkpoint below used no model.
The subsequent user-authorized Ollama follow-up loaded a local model; no model
has been trained.

| Experiment | Evidence | Status / decision |
|---|---|---|
| Kit audit | v3.2.0; split catalogs and SDK imports; 8 original synthetic checks PASS | KEEP split-specific loading |
| Gold replay | 1,545/1,545 exact; 3,541 calls, 217 ASK, 111 empty | PASS train contract gate |
| Split freeze | Seed 20261109; 1,236 fit / 309 val; separate banking-out 1,056/489 | Frozen before trajectory expansion |
| Runtime smoke | One actual read, serialized real trace/hash; organizer checker 0 schema errors | PASS integration smoke only |
| Evaluator identity | Label-derived fixture, 1,545 rows; expected PROXY 100.0 | Consistency PASS; no accuracy inference |
| Trajectory preparation | 5,086 rows; 4,096 fit / 990 val; all partitions disjoint by scenario | PASS structure/preflight; tokenizer/masking NOT RUN |
| Write response contracts | Source-verified markers recognize 1,724 successful train write responses and one no-op | PASS response-shape coverage; not a model score |
| E0 local model | No model path or model libraries; detected Intel integrated GPU | NOT RUN |
| E1 reference blocking | Implemented behind explicit CLI flag | RETEST after E0; default advisory |
| E2 ASR | No local ASR model/compute supplied | NOT RUN |
| E3 LoRA | Teacher-forced data prepared; no training launched | NOT RUN |
| P8 Docker/target benchmark | Docker absent from PATH; official release contracts UNKNOWN | NOT RUN |
| Ollama setup | Signed installer exit 0; local Qwen3 4B checksum verified; loopback service and cloud disabled | PASS setup |
| Ollama synthetic JSON smoke | 20.42 s including 15.08 s load; JSON DONE parsed | PASS protocol; not accuracy |
| Ollama validation pilot | First three frozen validation IDs; relaxed 180 s CPU budget | See [pilot evidence](ollama_local.md); separate from full E0 |

Dataset SHA-256:
`24c42c79fbe8db932fe9817d041c0d0ca422ac8177b413cc1be0cda1fd8941a8`.
The frozen IDs, replay hashes, generated decision examples and smoke outputs are
in the sibling local artifact folder. Do not distribute them with this repository.
