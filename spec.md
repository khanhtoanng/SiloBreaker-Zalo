# Technical Specification — LifeMate Offline Agent

> **Source-of-truth update (2026-11-09):** `KIT_VERIFIED_FINDINGS.md` establishes the v3.2.0 **train** simulator behavior from code inspection. Where this document disagrees, that audit takes precedence. No official scorer code was in the review ZIP; all participant F1 details below remain `PROXY` until verified.

**Status:** Proposed engineering specification for local coding agent, 2026-11-09.  
**Depends on:** `intent.md`, `01_research_brainstorm.md`, user-supplied `data.md`, and actual organizer kit.  
**Engineering rule:** Where `data.md` and live kit disagree, **inspect the official kit and modify the adapter**, not the ToolEnv implementation. External research is not the official scoring authority.

## 1. System architecture

```text
sample JSONL + latest WAV + history WAVs + sample context
              |                    |
              |                official split tools catalog
              v                    v
[Split-aware Loader]  ------> [Installed-Tool Registry]
              |
              v
[Offline ASR latest/history]  <-- bypass on gold-transcript train evaluation
              |
              v
[Safe ITN + History/Context Compiler]
              |
              v
[Policy LLM + pending-goal ledger] -- proposes ONE next action --> CALL | ASK | DONE
              |                                  |
              |                      [JSON/Schema/Provenance Validator]
              |                                  |
              |                       rejected --> bounded local repair
              |                                  |
              |                        validated CALL/ASK
              |                                  v
              +<-- [Actual Observation] <-- [Official split ToolEnv: one per sample]
                                                     |
                                                     v
                                          env.get_tool_calls()
                                          env.get_state_hash()
                                                     |
                                                     v
                                          UTF-8 submission.jsonl
```

**No separate agent role is needed at runtime.** The policy model performs conditional next-step selection; plain Python orchestrates validation, tool execution and observation. A planner/goal ledger may be an internal prompt structure, never a fake ToolEnv tool call.

## 2. Data and process contracts

### 2.1 Files expected from organizer (per `data.md`)

```text
<root>/<split>/
  audio/<id>/<id>.wav
  <split>.jsonl
  <split>_tools_catalog.json
  <split>_environment/<id>/state.json  # FORBIDDEN DIRECT READ
  zaic_tools/
  sample_submission.jsonl               # when supplied
```

- `split`: `train`, `public_test`, `private_test`, loaded from configuration.
- `sample`: `id`, `audio`, `context`, `history`; train may add `audio_text` and `label.tool_calls`, `label.tool_results`, `label.final_state`.
- `context`: `current_time`, `timezone`, `location`, `user_profile`, `installed_apps`.
- `tools_catalog`: a split-wide list of apps/tools, including `kind`, `description`, `parameters`, `returns`, extensions `x-ref`, `x-one-of`, `x-match: fuzzy`.
- `ToolEnv(split, sample_id, root=root)` must be instantiated **exactly once per inference sample**. Train-only standalone replay uses a different run; it is not a second environment created inside inference.
- The only state and execution authority is `env.call(...)`, its observation and `env.get_tool_calls()`, `env.get_state_hash()`.
- `env.validate(name, args)` is **reported** non-executing/non-logging; test that property against actual SDK before relying on it.
- A true execution attempt may be logged even when invalid; never discard it from the actual output.

### 2.2 Typed internal representations (not submission schema)

```python
from dataclasses import dataclass, field
from typing import Any, Literal

@dataclass(frozen=True)
class ToolSpec:
    name: str
    app: str
    kind: Literal['read', 'write', 'meta']
    description: str
    parameters: dict[str, Any]
    returns: Any

@dataclass(frozen=True)
class Decision:
    kind: Literal['CALL', 'ASK', 'DONE']
    tool_name: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)
    # ASK becomes real sys.ask_missing_info(tool_name, params)

@dataclass
class RuntimeState:
    observations: list[dict[str, Any]] = field(default_factory=list)
    grounded_references: dict[str, dict[str, Any]] = field(default_factory=dict)
    goals: list[dict[str, Any]] = field(default_factory=list)
    last_rejection: str | None = None
    steps: int = 0
    # Never store or read raw state.json
```

`grounded_references` must carry value + source (`context`, `history_tool_result`, `live_tool_result`) + semantic type, not only an untyped string. It is an advisory grounding index; actual call validity comes from the catalog/ToolEnv, and missing grounding is not automatic refusal when a legitimate literal ID is supplied by user or schema.

### 2.3 Decision output protocol

Pick one output format for BOTH SFT and inference; benchmark the following two instead of mixing:

**Default simple typed JSON** (internal only):

```json
{"kind":"CALL","tool_name":"contacts.search","arguments":{"name":"Minh"}}
```

```json
{"kind":"ASK","tool_name":"phone.call","arguments":{"params":["contact_id"]}}
```

```json
{"kind":"DONE"}
```

The adapter maps ASK to the real call:

```python
env.call('sys.ask_missing_info', {'tool_name': decision.tool_name,
                                  'params': decision.arguments['params']})
```

**Alternative:** Qwen's native tool-calling chat protocol if paired evaluation proves better. Do not mix custom JSON SFT targets with native-function-call inference without a deliberate compatibility adapter and a matched experiment.

If model emits an unknown `kind`, multiple actions, non-JSON, unknown tool, bad types, or extra fields: reject in process; attempt at most a bounded model repair **before** real execution, subject to latency reserve. Don't silently rewrite semantic values to guesses. Internal `DONE` is not logged; `ASK` must be an actual permitted call and is normally terminal per sample unless the kit explicitly contradicts this.

## 3. Module responsibilities, function signatures, and acceptance

| Module / callable | Input | Output | Testable obligations |
|---|---|---|---|
| `data_loader.load_split(split, root)` | split/root | manifest iterator + catalog | No environment-file access; correct split-specific package resolution; output ordering/unique ID checks |
| `data_loader.allowed_tools(sample, catalog)` | sample installed apps + catalog | `dict[str, ToolSpec]` | **Intersection** of sample-installed tools and current split catalog, plus authorized meta-tool |
| `asr.transcribe(audio_paths, config)` | provided WAV paths | ordered transcripts + timing | Local-only; Vietnamese; retain history turn ordering, no public/private pseudo-labeling for train |
| `normalizer.normalize(text, context)` | transcript and sample time | normalized text + uncertainty flags | Don't change negation or money values without evidence; preserve original alongside normalized |
| `context_builder.compile(sample, transcripts, registry, observations, goals)` | approved input/observations | model messages + tool schemas | History tool_results kept; token budget <= reported 16K; no guessed IDs; tool descriptions retained |
| `policy.next_action(messages, registry, budget)` | model state | typed `Decision` | One next action; deterministic decoding; no network |
| `validator.check(decision, registry, refs, env)` | proposed action | `Valid` or diagnostics | JSON types, enum, required, x-one-of, runtime existence, installed scope, x-ref where provable, `env.validate` |
| `toolenv_adapter.execute(env, decision)` | authorized action | exact observation | One real call per approved CALL/ASK, no falsified success, no hidden replay |
| `agent_loop.update_goals(...)` | observations + request goals | updated goal ledger | Don't mark goal done on `ok:true, done:false`; no unchecked re-execution of writes |
| `agent_loop.run(sample, config)` | one sample | actual calls + hash + optional local diagnostics | exactly one ToolEnv; latency/cap; ASK/DONE; return actual log and hash |
| `submission.write(items, path)` | output tuples | JSONL | exactly one row/split sample, unique IDs, JSON UTF-8; official schema |
| `evaluation.run(...)` | train validation IDs and config | score + per-error reports | frozen splits; official scorer if available; proxy explicitly labeled otherwise |
| `trajectory_builder.expand_train(...)` | authorized train records + SDK | teacher-forced decision examples | ordered gold call replay, tool observations, final DONE, group-split before expansion |
| `train_lora.train(...)` | decision SFT rows | adapter + metrics | assistant-target loss only, no leakage, exact tokenizer/template smoke test |
| `benchmark.verify_package(...)` | image/config/samples | pass/fail report | offline, A30 24GB, param total, <=30s, no missing results |

## 4. Orchestration algorithm (normative)

```python
def infer(sample, cfg):
    registry = load_allowed_tools(sample, split_catalog=cfg.catalog)
    # These steps are inference-only; no train gold labels loaded here.
    t0 = monotonic()  # Start before SDK creation and ASR; sample timing is end-to-end.
    env = ToolEnv(cfg.split, sample['id'], root=cfg.data_root)  # ONE per sample
    transcripts = transcribe_sample_audio_and_history(sample, cfg)
    runtime = RuntimeState()

    for step in range(cfg.max_decisions):
        if not enough_budget_for_safe_next_decision(t0, cfg):
            break
        messages = compile_context(sample, transcripts, registry, runtime)
        proposal = policy.next_action(messages, registry, cfg)
        if proposal.kind == 'DONE':
            break
        validated = validate_or_bounded_repair(proposal, registry, env, runtime, cfg)
        if validated is None:
            # No invalid attempt is executed; leave trace unchanged.
            break
        if validated.kind == 'ASK':
            obs = env.call('sys.ask_missing_info', {
                'tool_name': validated.tool_name,
                'params': validated.arguments['params']
            })
            runtime.observations.append(observation_record('sys.ask_missing_info', obs))
            break
        obs = env.call(validated.tool_name, validated.arguments)
        runtime.observations.append(observation_record(validated.tool_name, obs))
        update_reference_index_and_goals(runtime, validated, obs)
        if terminal_or_nonrecoverable_error(obs, validated, cfg):
            break

    # Actual env trace is source of truth, including rejected attempts.
    return {
        'id': sample['id'],
        'tool_calls': env.get_tool_calls(),
        'state_hash': env.get_state_hash()
    }
```

**Clarifications:**
- `max_decisions` must include sufficient headroom for **at least six real calls plus terminal DONE**, because a participant audit reports six-call gold examples. Tune experimentally; larger cap can cause over-calling. Set initial cap to 8–9 decisions **as a hypothesis**, with a hard wall-clock stop.
- When an already-executed real tool yields `ok:false`, the call remains in the log even if repair follows. Prevalidate to prevent it; differentiate syntax failure from business `done:false` or ambiguous network-like outcomes.
- Do not hardcode “always read before write”; if trusted history already contains a valid ID, extra reads can hurt precision. Do not hardcode “always no-op if already satisfied”; learned gold trace conventions may still call reads.
- `sys.ask_missing_info` must be present/authorized and its `params` value exactly shaped per the **actual** schema; don't assume request can omit required keys.
- Never use `env.get_state()` or read raw state files for decisions or diagnosis during inference. Source app information through tools.

## 5. Detailed semantic specifications

### 5.1 ASR

1. Accept only provided WAVs and respect their sample order. The brief reports 16kHz mono 16-bit; do not make fixed-shape assumptions beyond what actual samples establish.
2. Use a small/fast offline Vietnamese candidate first; experiment with PhoWhisper-medium vs PhoWhisper-large vs Whisper-turbo **within the total parameter budget**.
3. Include earlier user-turn audio when history provides it. Preserve assistant `text`, executed `tool_calls`, `tool_results` and chronology. If too long, compact non-essential dialogue first while **keeping ID-bearing tool results**.
4. Keep original ASR output and normalized text side by side for diagnostics; do not use organizer test transcript labels (unavailable) or posthoc public pseudo-labels for training.
5. Evaluate WER/CER plus critical-slot metrics; break out negation, amounts, addresses, phone digits, timestamps and self-corrections.

### 5.2 Numeric, time, and coreference helpers

- Parse relative time against `context.current_time` and `context.timezone` using timezone-aware datetime calculations; never machine's `datetime.now()` for sample semantics.
- Normalize Vietnamese `nghìn`, `triệu`, `rưỡi`, `kém`, `sau`, `trước`, `thứ ...`, and colloquial dialect only where unambiguous. Preserve uncertainty rather than assert risky conversions.
- Detect latest self-correction and negation before performing writes. Examples: “năm giờ ... à không, năm rưỡi” and “đừng đặt xe”.
- `x-ref` denotes a typed reference constraint per catalog; grounding candidate sources: **permitted input/context/history tool results/live tool observations**. Never reconstruct hidden IDs from sample filenames or raw state.
- Do not guess absent recipient, amount, account, vehicle or location; trigger an allowed read or `ASK`.

### 5.3 Runtime tool/schema matching

- Tool registry is specific to the current sample, even if split-level catalog contains more tools.
- Retain name, description, `kind`, required fields, enums, parameter descriptions, `x-one-of`, `x-ref`, `x-match`, return summaries; compact descriptions only if semantics survive.
- For x-one-of, enforce permitted alternate groups; check real `env.validate` to avoid implementing the extension incorrectly.
- For `x-match: fuzzy`, do not discard optional user-specified text merely because its final-state hash may omit free text; tool-call F1 still depends on fuzzy matching.
- Omit optional args only when not warranted by user intent, read results or target schema. No blanket optional-arg stripping.
- Never substitute a “similar” tool when no current installed tool can perform the request.
- Do not force a rigid tool-call order beyond data dependencies. Training gold may count unordered matches, but *execution order still impacts state*.

### 5.4 Multi-goal ledger

Internal goals have `semantic_intent`, `target_app`, `needed_effect`, `status ∈ {pending, in_progress, done, blocked}`, `supporting_observation_ids` and dependencies. The ledger:
- tracks independent tasks so one completed write does not cause premature DONE;
- is evidence-based, not an oracle of gold state;
- marks a write fulfilled only when the tool observation confirms effect, not solely `ok:true`;
- does not create extra official tool calls or bypass the model's decision policy;
- can flag suspicion of missing goal and request one extra model reconsideration **without automatically calling a write**;
- never blocks a legitimate repeated write when quantity/purpose requires two executions.

### 5.5 Retry/idempotence and recovery

- Before execution: at most one fast local repair attempt for parse/schema errors, as time allows; record repair diagnostics separately.
- After execution: distinguish `rejected/invalid`, `executed-but-not-done`, `success`, and `outcome-unknown`. Success interpretation depends on the actual tool's result schema.
- Never blindly retry a stateful operation such as transfer, ticket purchase, ride booking, sending a message; only retry if the SDK clearly establishes no effect or the operation is proven idempotent.
- Identical `read` calls may be pruned when no relevant intervening mutation and no freshness need exists; benchmark because excessive pruning might remove gold-matched reads.
- A corrected CALL must never erase an invalid real call that already occurred.

## 6. Training specification: supervised next-action trajectories

### 6.1 Source and split

- Only licensed base models released before the reported 2026-10-26 cutoff; record model revisions/licenses locally.
- Only **authorized labeled train** for fine-tuning and model selection. Verify dataset counts from actual kit; do not import public_test/private_test audio or requests into training.
- Partition **original sample IDs into fit/validation** before expanding to multiple time-step examples. Provide two frozen folds:
  - **grouped random holdout:** group by original scenario/sample, all trajectory steps together;
  - **leave-app-out holdout:** exclude one or more application groups/tools from fit (where enough train coverage exists) to test runtime schema generalization.
- Never place the same gold scenario's later observations in train and its earlier steps in validation. Keep split manifests and hashes.

### 6.2 Gold replay and per-decision target

For each authorized labeled train sample:

1. Prepare input using **gold `audio_text`** for baseline, with available sample `context`, history and per-sample eligible schemas.
2. Create a fresh train ToolEnv in a standalone **teacher-forcing replay run**; execute ordered gold calls via `env.call`, save their actual observations (the provided `label.tool_results` may be compared as an integrity check).
3. Before each gold call, create a training example with messages containing the user request, schemas, history and all preceding gold calls/results; the target is the **single next gold action**.
4. After the last gold call, create terminal `DONE` target; for a zero-call label, the immediate target is `DONE` (submission will be `[]`); `sys.ask_missing_info` gold call is encoded as an `ASK` action followed by terminal state.
5. Store a compact provenance record: sample ID, trajectory index, gold action, actual observation hash/summary, allowed tools, source split, train/validation partition. Never save protected simulator state.

**Illustrative conversation only (not an actual train label):**

```json
{
  "scenario_id": "example_contact_1",
  "step_index": 1,
  "messages": [
    {"role": "system", "content": "Select exactly the next authorized action using runtime schemas and observations."},
    {"role": "user", "content": "Nhắn Minh là tôi đến muộn"},
    {"role": "assistant", "content": "{\"kind\":\"CALL\",\"tool_name\":\"contacts.search\",\"arguments\":{\"name\":\"Minh\"}}"},
    {"role": "tool", "name": "contacts.search", "content": "{\"ok\":true,\"contacts\":[{\"id\":\"c42\",\"name\":\"Minh\"}]}"}
  ],
  "tools": ["<runtime schemas of eligible tools for this scenario>"],
  "target_next_action": {"kind": "CALL", "tool_name": "messages.send", "arguments": {"contact_id": "c42", "text": "Tôi đến muộn"}}
}
```

**Serialization requirement:** The snippet above is a conceptual source format, **not** a ready-to-pass TRL conversational dataset: `tools` should hold the actual JSON schema objects, and the serialized assistant targets must match the exact chosen Qwen chat template. Write an explicit converter that emits *either* a valid `messages` + `tools` tool-call dataset (native mode) *or* prompt/completion records for the custom JSON protocol. Verify with real tokenizer roundtrip on 3 representative examples: READ→WRITE, ASK, DONE.

### 6.3 Loss and LoRA objective

- Use Hugging Face TRL `SFTTrainer` + PEFT LoRA/QLoRA; start with a small pilot (e.g. r16, 1 epoch) and tune only after baseline.
- Target loss **only on the assistant's desired action output**. With tool-call conversational mode, `assistant_only_loss=True` requires a compatible chat template exposing generation spans; verify token mask and a forward/loss smoke test. For prompt-completion mode, use completion-only masking. Do **not** train loss on tool observations, system or user text.
- Label `ASK`, `DONE`, normal CALLs and late CALLs; report per-class and per-time-step accuracy. Since DONE examples may dominate expanded trajectories, audit STOP prevalence and false-positive STOP separately (a public model-classifier experiment collapsed to STOP for all timesteps).
- Early tests: **T0** zero-shot Qwen3-4B; **T1** list-at-once SFT; **T2** per-step trajectory SFT. Keep ASR/prompt/model/backends identical for fair comparison.
- Optional later ablations: train-only runtime tool name permutations while retaining consistent schema descriptions; train-only mild ASR noise derived from training ASR error patterns; synthetic ambiguous/error observations only where permitted and validated.
- No RL or full-model fine-tuning unless a reproducible SFT improvement and spare budget justify it.

### 6.4 Model selection and budgets

| Candidate | Public model information | Intended use | Decision gate |
|---|---|---|---|
| [Qwen3-4B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507) | 4.0B, Apache-2.0, native >16K context, **non-thinking** | Initial policy model | Keep runtime max context <= official 16,384; benchmark memory/30s |
| [PhoWhisper-medium](https://huggingface.co/vinai/PhoWhisper-medium) | Vietnamese ASR, BSD-3-Clause; reported ~0.77B | Lower-cost ASR candidate | Downstream score per second and parameter cap |
| [PhoWhisper-large](https://huggingface.co/vinai/PhoWhisper-large) | Vietnamese ASR, BSD-3-Clause; reported ~1.55B | Higher-quality ASR candidate | Total reported ~5.55B with Qwen 4B before extra components; verify total count |
| Whisper-large-v3-turbo | Candidate in handoff; model/license/revision to verify | ASR alternative | Compare against same local validation |

Models are optional candidates, not mandated by this spec. Measure actual params (`sum(p.numel() ...)` + adapters + other models), exact released revisions, A30 VRAM and licenses. Quantization affects memory, **not parameter count**. Any auxiliary trainable model must be counted under reported rules.

## 7. Local evaluation: exactness first, then diagnostics

### 7.1 Evaluation precedence

1. **Authoritative official evaluator/validator**, if supplied.
2. Independently port official scorer exactly, with parity fixtures and proof.
3. If official implementation is not available, use a clearly labeled **participant-reported proxy**. Never publish proxy numbers as official.

**Participant-reported proxy algorithm:**

```text
If G is empty:
    sample_score = 1 iff P is empty, else 0
Else:
    if prediction_final_hash != gold_final_hash: sample_score = 0
    else:
        M = maximum one-to-one matching between predicted and gold calls,
            same tool name and matching args (including x-match fuzzy semantics)
        if M == 0: sample_score = 0
        else:
            U = |P| - M
            precision = M / (M + U)
            recall = M / |G|
            sample_score = 2 * precision * recall / (precision + recall)
Overall = 100 * mean(sample_score)
```

For matching:
- Match duplicates with **multiplicity**, not set semantics.
- Do not compare predicted call positions directly if organizer's matching is unordered; execution remains ordered.
- Participant reports fuzzy args use token-F1 > 0.6 after Unicode NFC + lowercase; exact handling of punctuation, optional args and field omission requires official scoring-code inspection.
- Read calls and `sys.ask_missing_info` count as calls in reported F1.
- A wrong state hash on a nonempty-gold sample zeroes the sample, even if some calls matched.
- Gold empty samples are a special case; do not treat `[]` as universal safe fallback.

**Gold state hash:** Never create an environment in inference to compute a hypothetical gold hash. In offline train evaluation, obtain expected reference hash via gold replay in a separate controlled evaluation run and compare to the predicted run's `env.get_state_hash()`. The train `label.final_state` is an **authorized label**, but must not be read by inference or used to manipulate the simulator.

### 7.2 Evaluation instrumentation

Return per-sample **diagnostics separate from submission**:

```json
{
  "id": "train_example",
  "split": "train_validation",
  "oracle_text_score": null,
  "asr_e2e_score": null,
  "hash_match": false,
  "matched_calls": 0,
  "extra_calls": 0,
  "missing_calls": 0,
  "first_full_action_correct": false,
  "next_action_accuracy_by_step": {},
  "ask_correct": null,
  "empty_correct": null,
  "error_tags": ["WRONG_TOOL", "WRONG_ARGUMENT"],
  "latency_ms": {"asr": 0, "generation": 0, "tool": 0, "total": 0},
  "model_id": "...",
  "config_id": "..."
}
```

Error taxonomy: `ASR_CRITICAL_SLOT`, `FIRST_TOOL_WRONG`, `LATE_TOOL_WRONG`, `REF_UNGROUNDED`, `WRONG_ARGUMENT`, `MISSING_READ`, `EXTRA_READ`, `MISSING_WRITE`, `WRONG_WRITE`, `ASK_EARLY`, `ASK_MISSING`, `ASK_WRONG_PARAM`, `EMPTY_WRONG`, `PREMATURE_DONE`, `EXTRA_CALL`, `CONDITION_WRONG`, `HISTORY_LOSS`, `VALIDATION_REJECTION`, `BUSINESS_FAILURE`, `DUPLICATE_WRITE`, `TIMEOUT`, `OUTPUT_INVALID`, `KIT_INCOMPATIBILITY`.

Report breakdowns: all / seen-app / leave-app-out / 1–2 vs 3+ calls / ASK / `[]` / conditionals / history / numeric / dialect / execution errors. Use paired bootstrap confidence intervals on sample scores where practical; do not infer strong improvements from a single noisy leaderboard change.

## 8. Mandatory tests / edge-case IDs

Implement all **P0** cases from `01_research_brainstorm.md`. At minimum, write:

| Test | Assertion |
|---|---|
| `test_allowed_registry_filters_apps` | Globally catalogued but uninstalled tool never emitted or executed |
| `test_one_env_per_infer` | Single instance for one sample, no hidden `state.json` reads |
| `test_validate_before_call` | Invalid schema proposal is rejected before any official call or log entry |
| `test_x_one_of` | At least one allowed argument group and correct required schema fields |
| `test_ref_after_read` | Second write receives exact ID from first read observation |
| `test_ref_from_history` | Valid ID from history used without hallucination or unnecessary read |
| `test_ambiguous_contact` | Search with duplicates produces correct `ASK` behavior (per fixture) |
| `test_no_app_no_call` | Eligible set empty / unrelated apps yields `[]` when correct |
| `test_cancellation_and_correction` | Earlier intent overwritten by latest explicit negation/correction |
| `test_conditional_no_write` | False condition produces no forbidden write |
| `test_multigoal_ledger` | Finishes both supported goals, no premature DONE |
| `test_ask_after_reads` | Lookup before `sys.ask_missing_info` when needed |
| `test_ask_terminal` | Actual ASK call executed/logged, no extra actions afterward |
| `test_duplicate_legitimate_writes` | Two intended purchases/transfers not deduplicated |
| `test_write_retry_guard` | Unknown outcome does not produce second non-idempotent write |
| `test_unmatched_read_penalty` | Scorer correctly penalizes extra and missing reads |
| `test_gold_empty_case` | Exact empty rule applied; missing sample row not silently equivalent to `[]` |
| `test_call_matching_multiplicity` | One-to-one unordered matching if organizer confirms rule |
| `test_hash_zero_gate` | Wrong hash on nonempty gold yields zero |
| `test_six_calls_plus_stop` | Loop supports long trajectories when enough budget |
| `test_split_specific_sdk` | Correct `zaic_tools` version imported for each split |
| `test_jsonl_order_unique_hash` | One valid UTF-8 line per manifest item, exact logged trace/hash |
| `test_network_disabled` | No remote API/download during inference |
| `test_budget_abort` | Safe deadline stops generation, preserves actual tool trace |
| `test_train_val_group_disjoint` | No scenario or trajectory-step leakage |
| `test_assistant_target_mask` | Only intended action spans contribute to SFT loss |

Add synthetic cases for E07–E08, E17–E18, E25–E27, E35–E38. **Synthetic fixture oracle is a software behavior assertion; only labeled real train data can establish organizer gold-call conventions.**

## 9. Directory layout (no duplicated simulator or unused templates)

```text
lifemate/
  README.md
  pyproject.toml
  configs/
    baseline.yaml
    lora.yaml
  src/lifemate/
    data_loader.py
    asr.py
    normalizer.py
    context_builder.py
    policy.py
    validator.py
    toolenv_adapter.py
    agent_loop.py
    submission.py
    evaluation.py
    trajectory_builder.py
  scripts/
    audit_kit.py
    replay_gold.py
    evaluate.py
    build_trajectories.py
    train_lora.py
    predict.py
    verify_docker.py
  tests/
    test_agent_loop.py
    test_toolenv_integrity.py
    test_schema_extensions.py
    test_references.py
    test_ask_and_empty.py
    test_multistep.py
    test_scorer.py
    test_training_data.py
    test_submission.py
  docs/
    rules_audit.md
    experiment_log.md
    evaluation_report.md
  Dockerfile
  predict.sh
```

**Do not create** a generic `mock_toolenv` product implementation, copied organizer SDK, runtime DB service, LangGraph scaffolding, or independent `final_state` hash generator. **Tests** may use minimal fake deterministic tool observations in isolated fixtures, never in actual inference.

## 10. Config contract and default settings

```yaml
# baseline.yaml (hypotheses; tune only from local measured evidence)
data_root: /data
split: public_test
llm_model_path: /models/qwen3_4b_instruct_2507
asr_model_path: /models/phowhisper_medium
max_context_tokens: 16384
max_decisions: 9
max_total_sample_seconds: 30
agent_soft_deadline_seconds: 25
max_schema_repair: 1
temperature: 0
seed: 20261109
output_path: result/submission.jsonl
```

- `soft_deadline_seconds=25` must be **measured end-to-end**, not a promise that every sample completes. Stop before hard deadline, leaving enough serialization time.
- `split` can be configured; do not hardcode `public_test` in reusable modules.
- Confirm exact `/data`, `result/submission.jsonl`, script flags and Docker entrypoint from kit; these defaults are currently **tentative**.

## 11. Definition of done

The spec is implemented only if: organizer kit audit passed, all train-gold replayed through proper SDK, no blocked/illegal file access, no test data leakage, error taxonomy and scorer parity verified, frozen split benchmark run, chosen model demonstrated measured benefit (or baseline selected), all P0 tests passed, 100% manifest rows valid, fully offline Docker smoke test succeeded, 30s/A30 and memory/param/context constraints passed on target or authorized equivalent, and final artifacts fully reproducible.

**Related source links and remaining rule verifications:** `01_research_brainstorm.md`.


## 12. Normative v3.2.0 source contracts (post-kit-audit)

This section is **normative** for coding agents. See `KIT_VERIFIED_FINDINGS.md` for source file and evidence details and `SCORING_EDGE_CASES.md` for test IDs.

### 12.1 Official runtime boundary

```python
# PSEUDOCODE — import only the SDK corresponding to selected split.
env = ToolEnv(split=selected_split, question_id=item["id"], root=data_root)  # once
# Before each proposed call:
check = env.validate(tool_name, args)          # no call/log/state mutation
# Our own preflight ALSO checks nested arguments, reference provenance, and known business prerequisites.
if check["ok"] and own_preflight_valid:
    observed = env.call(tool_name, args)        # the attempt is permanently logged, even on rejection
    update_observations_and_goal_ledger(observed)
# When terminal:
return {"id": item["id"], "tool_calls": env.get_tool_calls(), "state_hash": env.get_state_hash()}
```

- `env.validate` does not reject an unknown `x-ref` identifier; it checks schema, not database existence.
- `env.validate` checks immediate `items.type` for arrays but does not recurse into nested object required properties. Our preflight must validate `food_delivery.place_order.items[]` `item_id`/`quantity` and other nested structures.
- Unknown argument keys may not be schema-rejected. The agent must not invent `**kwargs`; strip only undocumented **model-generated** extras **before** call, not user-mandated legitimate fields.
- `None`, empty strings, empty arrays and empty objects are treated as absent by organizer validation.
- `Session.allowed` is derived from simulator metadata, so `env.validate` is the final scope guard even if `context.installed_apps` was malformed.
- `get_state()` is **not** an inference observation API. Its availability for offline authorized train replay diagnostics is not permission to inspect simulator internals during inference.

### 12.2 Outcome semantics and tool observations

Define `ToolOutcome = SCHEMA_REJECTED | BUSINESS_NOOP | WRITE_EFFECT | READ_OBSERVATION | META_WAIT | UNKNOWN`. Do **not** define success as `result.get("ok") is True`. For `result.get("done") is False`, always classify a business no-op, regardless of `ok` (then check actual operation class). For writes returning `ok: true` with `id/item/transaction` or equivalent, treat as likely effect only after a tool-specific check, not a universal assumption.

When a no-op occurs, recompute remaining goals with the actual observation; never retry transfers, orders, messages, bookings, or other mutations after an uncertain outcome. The previous speculative `DONE` decision does not override a failed app operation. Preserve tool result snapshots (SDK deep-copies them).

### 12.3 Canonicalized-state subtlety

In the organizer code, `get_state_hash` hashes a canonical state in which certain free-text keys are removed recursively and read-only information apps do not contribute. Therefore `same hash` is **not** equivalent to `same call arguments` or `successful entire task`. The executor must emit the hash it receives; the evaluator tracks both state-match and call-match independently.

Never modify tokenizer/normalization to erase user content simply because those fields are hash-excluded. Enforce the requested action text and all `x-match: fuzzy` arguments. Exact fuzzy matching threshold/order/multiplicity belong to the **unavailable official scorer**, not this train SDK; the experiment dashboard must label them `PROXY`.

### 12.4 Mandatory tested shape examples

```json
{"decision":"CALL","tool_name":"sms.send","arguments":{"phone_number":"0912345678","content":"Tôi đến muộn 10 phút"}}
```

`sms.send` requires `content` plus one of `contact_id` or `phone_number`. It does NOT require both.

```json
{"decision":"ASK","tool_name":"sys.ask_missing_info","arguments":{"tool_name":"ride_hailing.book","params":["vehicle"]}}
```

`ride_hailing.book` requires `pickup`, `dropoff`, `vehicle`; an ASK for `vehicle` is justified **only** when current request, context and available reads do not supply it. **Do not hardcode ASK for all ride requests**; learn from train gold labels.

```json
{"decision":"CALL","tool_name":"food_delivery.place_order","arguments":{"restaurant_id":"r_01","items":[{"item_id":"i_01","quantity":2}]}}
```

The payload should pass the independent nested preflight **and** `env.validate`; `restaurant_id` and each `item_id` must be grounded using actual restaurant/menu reads for the active sample. IDs here are schematic examples only.

### 12.5 Catalog-and-scoring dependencies

The provided small ZIP exposes only `train/train_tools_catalog.json`, **46 apps, 147 tools, 62 read/84 write/1 meta**, not the public-test SDK. Never use these numbers as hardcoded inference limits. Use `tools/audit_catalogs.py` on the complete authorized local kit to produce a safe catalog comparison.

**Not resolved:** the real scorer algorithm and fuzzy threshold; per-split catalog deltas; actual labeled-gold replay; final Docker entrypoint/resource rules. Add a **blocked/UNKNOWN** status to the corresponding acceptance tests rather than silently passing them.

### 12.6 Added test cases

`K01..K54` from `SCORING_EDGE_CASES.md` constitute the implementation test matrix. At minimum, CI must execute unit/contract tests for `K01..K13`, `K18`, `K25..K30`, `K35..K38`, `K45..K48`, `K53` and show the remaining as an explicit P1 backlog. Synthetic tests are permitted, but the final evaluator must also use a frozen authorized train holdout with real ToolEnv execution.
