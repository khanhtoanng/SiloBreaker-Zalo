# LifeMate model and training reproduction

The baseline uses PhoWhisper-small for Vietnamese transcription and Qwen3-4B-Instruct-2507 for planning and tool selection. The application loads both checkpoints from local directories and uses greedy decoding with seed `20261109`. The Qwen checkpoint has 4B parameters and a native 262,144-token context. LifeMate caps its full prompt and generation at 16,384 tokens. PhoWhisper-small has approximately 244M parameters.

| Local directory | Upstream checkpoint | Revision | License |
| --- | --- | --- | --- |
| `saved_models/policy.gguf` | [Qwen3-4B-Instruct-2507 Q4_K_M GGUF](https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/blob/a06e946bb6b655725eafa393f4a9745d460374c9/Qwen3-4B-Instruct-2507-Q4_K_M.gguf) | `a06e946bb6b655725eafa393f4a9745d460374c9` | Apache 2.0 |
| `saved_models/asr` | [vinai/PhoWhisper-small](https://huggingface.co/vinai/PhoWhisper-small/tree/a86b604c346caf7148c37512eafe783a16420adb) | `a86b604c346caf7148c37512eafe783a16420adb` | BSD 3-Clause |

The ASR adapter transcribes the latest Vietnamese audio and historical user audio. The policy sees the transcript, context, past dialogue and tool schemas for installed apps. It proposes each next action, uses read results to ground entity IDs, and either calls a validated tool, asks for missing parameters or stops. One organizer SDK session supplies each result row's tool calls and state hash.

The baseline uses the published checkpoints with no team fine-tuning or synthetic training data. PhoWhisper's original training is documented in the upstream model card. The optional action-policy training implementation is in `src/lifemate/learning/` and `scripts/train_lora.py`. To reproduce that experiment, use the [original Transformers checkpoint](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/tree/cdbee75f17c01a7cc42f958dc650907174af0554) and the registered team's copy of the organizer LifeMate v3.2.0 **train** split. Follow the [local LoRA guide](../docs/local_training.md) to freeze the split, replay the labels, generate next-action examples and run the training command.
