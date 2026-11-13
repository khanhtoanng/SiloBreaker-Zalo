# Learn LifeMate by following one request

Start with the user’s goal: “Nhắn Minh là tôi đến muộn.” The program needs to hear the message, identify Minh, send the SMS in the simulator, and record what it actually did. You can learn each piece by tracing that example through the code and then running a small experiment.

## 1. Define success before changing the model

| Goal | How to reach it | How to check it |
| --- | --- | --- |
| Execute the right actions | Transcribe the WAV, select eligible tools, look up IDs, and use live tool results to decide the next action | Replay the trace and compare the final state hash. On labeled examples, compare the tool names and arguments with the expected calls |
| Handle missing information | Ask for the fields the chosen tool still needs, after using available context and useful lookups | Check for `sys.ask_missing_info` with the intended tool and the missing parameter names |
| Handle unsupported requests | Use the available tool schemas to determine whether the simulator can fulfill the request | Check that the trace is empty and comes from the sample's actual SDK session |
| Produce a usable submission | Run every manifest row in order and write the session's trace and state hash | Run the project and organizer validators. Compare the timed notebook and CLI output on the same cases |
| Improve accuracy with evidence | Evaluate a fixed holdout, inspect failures, and change the component responsible | Compare accuracy, extra or missing calls, and latency on the same samples before and after the change |

## 2. Follow one request through the code

| Step | What happens in the SMS example | Read this code |
| --- | --- | --- |
| Load the case | The CLI chooses a split. The loader reads the matching manifest and catalog and projects the sample into the fields inference can use. The organizer SDK opens one session for this sample | [`predict()`](LifeMate/src/lifemate/workflows.py#L158), [kit loader](LifeMate/src/lifemate/data/kit.py), [SDK adapter](LifeMate/src/lifemate/adapters/sdk.py) |
| Transcribe Vietnamese | PhoWhisper processes the current WAV and historical user audio. A wrong name or number here can change what the agent does downstream | [`prepare_audio()` and `WhisperAsr`](LifeMate/src/lifemate/adapters/whisper.py) |
| Plan and propose | The prompt contains the transcript, context, allowed tool schemas, and observations. Qwen proposes `contacts.search` for Minh. After reading the result, it can propose `sms.send` with the returned ID and the message text | [Prompt builder](LifeMate/src/lifemate/runtime/context.py), [goal planner](LifeMate/src/lifemate/runtime/goals.py), [local Qwen adapter](LifeMate/src/lifemate/adapters/llama_cpp.py) |
| Validate and execute | The agent checks the tool and argument schema, verifies the ID's source, and binds a write to a requested goal. The official SDK validates the call before running it. The loop records the result and either continues, asks for information, or finishes | [`infer()`](LifeMate/src/lifemate/runtime/loop.py#L32), [argument validation](LifeMate/src/lifemate/runtime/validation.py), [reference checks](LifeMate/src/lifemate/runtime/references.py) |
| Write the submission | The output includes the calls actually executed by the SDK and its final state hash. A separate diagnostics file records model proposals and stop reasons for debugging | [Artifact writer](LifeMate/src/lifemate/prediction_artifacts.py), [submission validator](LifeMate/src/lifemate/submission.py) |

The policy speaks in three decisions. `CALL` proposes a tool and arguments. `ASK` names a target tool and the information still needed. `DONE` ends the turn. A model proposal reaches the submission only if the runtime executes the corresponding call. Historical tool calls were applied before the current turn and are available as context.

**What to read alongside the code.** Start with automatic speech recognition (ASR) and how Whisper handles multilingual audio. Then read about the local language model and the runtime that serves its quantized GGUF weights. Quantization represents weights with fewer bits for inference. [Whisper paper](https://arxiv.org/abs/2212.04356) · [PhoWhisper model card](https://huggingface.co/vinai/PhoWhisper-small) · [Qwen model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507) · [llama.cpp](https://github.com/ggml-org/llama.cpp)

## 3. Run it in three steps

1. **Run one SDK read.** Follow the quickstart to see an actual tool response and state hash before bringing in model weights. This checks the selected catalog, kit paths, and simulator wiring. [SDK smoke test](LifeMate/docs/local_quickstart.md#1-run-one-sdk-read)
2. **Run a small audio pilot.** Use the public command with `--limit 8`. Open the diagnostics first. Find a transcript, the proposed actions, any rejections, and the final stop reason. Compare those steps with the calls in `submission.jsonl`. [Competition run guide](LifeMate/docs/competition_run.md#public-test-on-windows)
3. **Run and validate the full public split.** Remove `--limit`, use a fresh output directory, and check every manifest ID and call schema before uploading. Use the notebook when measuring the private-test format. [Validation commands](LifeMate/docs/milestones/06-zalo-submission.md#1-validate-and-upload-the-public-result) · [Timing notebook](LifeMate/predict_notebook.ipynb)

## 4. Diagnose failures before training

Freeze a validation subset from the labeled **train** split. Run the same IDs in oracle mode, which supplies the organizer's train transcripts, and in audio mode, which supplies PhoWhisper transcripts. Keep the policy and settings fixed between the two runs. The difference helps locate speech errors. Compare specific cases as well as the aggregate score.

| What you see | What to check next |
| --- | --- |
| The text run succeeds and the audio run fails | Inspect the transcript for changed names, times, and amounts. Use [`asr.py`](LifeMate/src/lifemate/metrics/asr.py) to measure word and character errors and compare important values |
| Both runs choose the wrong tool or argument | Read the prompt and check the available schemas. If the failure recurs across held-out requests, test a policy prompt change or LoRA |
| A proposed call was rejected | Read the diagnostic reason and inspect its schema, reference evidence, or goal. Reproduce the case in the runtime tests before changing a guard |
| The state hash matches but the proxy score is low | Inspect extra reads, duplicate calls, or mismatched arguments. A matching hash can coexist with a different call trace |
| Timing is too high | Compare time in ASR, planning, policy generation, and the SDK. Include long-history and multi-action examples in the pilot |

The local scorer uses expected train calls and hashes from gold replay. For nonempty expected traces, it gates on final-state hash and compares calls by one-to-one matching. It is a proxy for diagnosis. The organizer leaderboard is the competition score. [Evaluator code](LifeMate/src/lifemate/metrics/proxy.py) · [Paired evaluation procedure](LifeMate/docs/milestones/04-audio-and-evaluation.md) · [Scoring assumptions](LifeMate/docs/scorer_parity.md)

## 5. Fine-tune the action policy with LoRA

**Supervised fine-tuning** teaches the policy what action should come next from a labeled example. For the SMS request, one training row targets `contacts.search`. The next row includes the observed search result and targets `sms.send`. The last row targets `DONE`. Each step sees only observations available at that point. [Trajectory generation](LifeMate/src/lifemate/learning/trajectories.py)

**LoRA** keeps the base model weights frozen and learns small, low-rank updates to selected layers. LifeMate's sample config targets Qwen's attention `q_proj` and `v_proj` layers. The tokenizer and training collator mask the prompt and padding, so loss is computed on the target action and its end-of-sequence token. This experiment trains the action policy. PhoWhisper remains the ASR model. [LoRA paper](https://arxiv.org/abs/2106.09685) · [PEFT LoRA guide](https://huggingface.co/docs/peft/conceptual_guides/lora) · [Token and label preparation](LifeMate/src/lifemate/learning/serialization.py)

1. **Prepare the labeled data.** Run `lifemate freeze`, `lifemate replay`, and `lifemate trajectories` with the registered team's train kit. Freeze whole scenario IDs before expanding them into steps so one conversation stays entirely in fit or validation. [Split implementation](LifeMate/src/lifemate/data/splits.py) · [Commands](LifeMate/docs/local_training.md#1-what-training-data-is-available)
2. **Train a candidate.** Use the original Transformers-format Qwen checkpoint and the matching tokenizer. Fill in the data and template fingerprints in a copy of the LoRA config. Run `lifemate train --config ... --dry-run`, then run the same command without `--dry-run` to train and save the adapter. The GGUF used for competition inference is a separate artifact. [LoRA config](LifeMate/configs/training.lora.json) · [Trainer](LifeMate/src/lifemate/learning/trainer.py) · [Configuration and training commands](LifeMate/docs/local_training.md#3-generate-the-complete-training-configuration)
3. **Compare base and adapter.** Use the Transformers backend for both runs and add `--adapter-path` for the candidate. Keep holdout IDs, tokenizer, input mode, and budgets fixed. Run `lifemate evaluate` and `lifemate compare`. Look for better state match and tool calls, then repeat with real audio and check latency. [Adapter inference](LifeMate/docs/local_training.md#6-run-the-saved-adapter) · [Comparison code](LifeMate/src/lifemate/metrics/reports.py)

The current competition launcher loads the published Qwen GGUF and PhoWhisper checkpoints. The trainer prepares a separate adapter experiment. If the experiment wins on held-out requests, the selected weights still need to be prepared for the intended inference backend and verified there before changing the competition config. [Competition config](LifeMate/configs/inference.competition.json) · [Pinned model revisions](LifeMate/training_code/README.md)
