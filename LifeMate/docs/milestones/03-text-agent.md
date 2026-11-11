# 03. Build a text-first agent

[Roadmap](README.md) · [Previous milestone](02-kit-and-replay.md) · [Next milestone](04-audio-and-evaluation.md)

Start with organizer-provided train transcripts to see what the policy can do with a known request. This is called **oracle text** in the configuration. It lets you diagnose tool selection and argument grounding before adding automatic speech recognition.

## 1. Follow one prediction through the code

1. [`cli.py`](../../src/lifemate/cli.py) parses `predict`. [`workflows.py`](../../src/lifemate/workflows.py) loads settings, selects rows, prepares the policy and calls `infer` once per sample. JSON paths resolve relative to the config. Explicit CLI paths resolve from the shell's working directory.
2. [`runtime/context.py`](../../src/lifemate/runtime/context.py) assembles the transcript, sample clock, profile, history and eligible tool schemas. [`runtime/normalize.py`](../../src/lifemate/runtime/normalize.py) records supported values such as relative times or money spans and keeps the original text available.
3. [`runtime/goals.py`](../../src/lifemate/runtime/goals.py) manages requested outcomes and their dependencies. [`runtime/loop.py`](../../src/lifemate/runtime/loop.py) asks the local policy for one CALL, ASK or DONE decision and checks the remaining time and decision budget.
4. [`runtime/validation.py`](../../src/lifemate/runtime/validation.py) checks the proposed action. [`runtime/references.py`](../../src/lifemate/runtime/references.py) tracks whether IDs have supporting evidence. Official `env.validate` is the final schema check before `env.call`. A rejected proposal remains in diagnostics. Every actual SDK attempt remains in the submission trace.
5. [`runtime/outcomes.py`](../../src/lifemate/runtime/outcomes.py) interprets tool responses. For example, `ok:true` can accompany `done:false`, which signals no completed write. The loop uses the actual observation when deciding what to do next.
6. The loop retrieves `get_tool_calls()` and `get_state_hash()`. [prediction_artifacts.py](../../src/lifemate/prediction_artifacts.py) publishes the final file after all selected scenarios complete. The run, diagnostics and partial checkpoint files are for local analysis.

## 2. Trace a small fixture

Open [`test_two_goals_independent_success_then_ask` in tests/test_loop.py](../../tests/test_loop.py). Follow the two goals, the first write, and the clarification for the second goal. The final trace retains the write and the ASK call. Open `test_unsupported_withdrawn_plan_real_empty_hash` in the same file to see how the loop emits an empty trace and passes through the hash returned by the test environment. Run the file from `LifeMate/` with your core interpreter.

```powershell
& $Python -m unittest discover -s tests -p test_loop.py -v
```

The fixtures isolate execution and control flow by supplying decisions. They are a practical way to learn the code before testing a model's ability to choose those decisions.

## 3. Run a local text baseline

1. Set up the Ollama loopback service with a local model and tokenizer using sections 2–3 of the [operator guide](../operator_guide.md). The alternative [Transformers adapter](../../src/lifemate/adapters/transformers.py) accepts a complete local model directory and can later load a LoRA adapter.
2. Generate an oracle config as in section 5 of the guide, pointing it at the grouped fold from milestone 02. Use the pilot command below. Read its `.run.json` and `.diagnostics.json` for the selected ID, actual actions, timing and stop reason.
3. Use a fresh output path for the full validation fold, omit `--limit`, and preserve model identity and settings. Evaluate the result in milestone 04. Use a fixed local Transformers baseline for the later comparison if your candidate will use Transformers too.

```powershell
& $Python -m lifemate predict --config "$Work\configs\oracle.json" --out "$Work\runs\oracle-pilot-m03.jsonl" --limit 1
```

The [Ollama notes](../ollama_local.md) record an older CPU protocol smoke and a three-scenario train pilot with a 180-second allowance per sample. They help explain the setup. The competition limit is 30 seconds per sample. [LifeMate portal, Rule](https://challenge.zalo.ai/portal/lifemate)

**Ready to move on** when the current policy produces one real trace and hash per frozen validation ID, and you have diagnostics for dropped goals, extra reads, bad arguments and timeouts. Preserve this baseline for the paired audio run.
