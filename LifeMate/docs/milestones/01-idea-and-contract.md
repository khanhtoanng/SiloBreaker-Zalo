# 01. Define the voice-to-action problem

[Roadmap](README.md) · [Next milestone](02-kit-and-replay.md)

## Start with three design decisions

1. **Translate speech into actions.** A request such as “Bật điều hòa phòng khách 26 độ rồi đặt xe về nhà” can require two independent outcomes. One call can discover a device ID, the next can change its setting, and a ride call can use pickup and home information from the sample. Tool names and argument shapes come from the selected split and sample.
2. **Use a model to propose one next decision at a time.** The policy receives the transcript, conversation history, context, eligible schemas and observations so far. It can propose a call, ask for missing information, or stop. Keeping execution in Python makes the sequence and failures inspectable.
3. **Let the organizer's simulator own app state.** Use one split-specific `ToolEnv` per sample. Capture every executed call in order and take the final hash from that same environment. Earlier turns' writes are already reflected in the starting state. [LifeMate portal, Description and Rule](https://challenge.zalo.ai/portal/lifemate)

## Walk through the contract

| You receive | What the agent does with it |
| --- | --- |
| Latest Vietnamese audio and earlier user-turn audio | Transcribe supplied user turns. Focus execution on the latest request, using prior turns for context |
| Sample time, timezone, location, profile and installed apps | Resolve relative time and known addresses. Limit choices to the tools the sample can use |
| Catalog and SDK supplied for the split | Use schemas to form arguments and the SDK to validate and execute them |
| Actual tool observations | Ground IDs, check business outcomes, and decide whether a remaining goal needs another action or clarification |

The project handles three representative outcomes. For a supported request with enough information, it executes the necessary calls. If a required value cannot be resolved, it can execute `sys.ask_missing_info` with the intended `tool_name` and missing `params`, including after a completed independent action. If the request is outside the installed capabilities, it can finish with `tool_calls: []` and the SDK's unchanged hash. [LifeMate portal, Description and Evaluation](https://challenge.zalo.ai/portal/lifemate)

## Find those decisions in the code

| Responsibility | Start here |
| --- | --- |
| What enters the app and how decisions are shaped | [contracts.py](../../src/lifemate/contracts.py) |
| Which tools are eligible for the current sample | [`allowed_tools` in data/kit.py](../../src/lifemate/data/kit.py) |
| Which actions are proposed and actually run | [`infer` in runtime/loop.py](../../src/lifemate/runtime/loop.py) |
| Where the final trace and hash are written | [prediction_artifacts.py](../../src/lifemate/prediction_artifacts.py) and [submission.py](../../src/lifemate/submission.py) |

**Ready to move on** when you can explain why a read can matter even if the hash stays the same, and why a correct-looking list of proposed actions is insufficient until the simulator executes it. The next milestone shows how to establish that baseline with the supplied kit.
