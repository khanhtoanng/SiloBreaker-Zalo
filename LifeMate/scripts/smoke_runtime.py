"""One real train read through the agent loop. This is an SDK smoke, not a model benchmark."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lifemate.agent_loop import infer
from lifemate.cli import external_output, save_json
from lifemate.data_loader import (
    allowed_tools,
    inference_input,
    load_catalog,
    load_manifest,
    resolve_data_root,
)
from lifemate.submission import write_submission


class ReadOnce:
    def __init__(self, name):
        self.name = name
        self.called = False

    def next_action(self, messages, *, deadline):
        if self.called:
            return {"kind": "DONE"}
        self.called = True
        return {"kind": "CALL", "tool_name": self.name, "arguments": {}}

    def plan(self, request_context, *, deadline):
        # Preserve this public fixture's use by callers that rely on infer's
        # policy-planner discovery; planning never advances next_action state.
        return ReadPlan(self.name).plan(request_context, deadline=deadline)


class ReadPlan:
    """Explicit smoke-only plan, independent of the action policy's read state."""

    def __init__(self, name):
        self.name = name

    def plan(self, request_context, *, deadline):
        return {
            "goals": [
                {
                    "id": "smoke-read",
                    "intent": "One eligible SDK read",
                    "tool_name": self.name,
                    "arguments": {},
                    "occurrences": [
                        {
                            "id": "smoke-read-1",
                            "span": [0, len(request_context["latest_user_text"])],
                        }
                    ],
                }
            ]
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    selected_root = args.data_root
    args.data_root = resolve_data_root(args.data_root)
    inputs = (selected_root, args.data_root)
    out = external_output(args.out, inputs=inputs)
    sidecar = external_output(out.with_suffix(".diagnostics.json"), inputs=inputs, outputs=(out,))
    catalog = load_catalog(args.data_root, "train")
    for row in load_manifest(args.data_root, "train"):
        sample = inference_input(row, oracle_text=True)
        eligible = [
            name
            for name, spec in allowed_tools(sample, catalog).items()
            if spec["kind"] == "read"
            and not spec["parameters"].get("required")
            and not spec["parameters"].get("x-one-of")
        ]
        if eligible:
            name = sorted(eligible)[0]
            prediction, diagnostic = infer(
                sample, args.data_root, "train", catalog, ReadOnce(name), planner=ReadPlan(name)
            )
            if diagnostic["stop_reason"] != "DONE" or len(prediction["tool_calls"]) != 1:
                raise RuntimeError("Real SDK smoke failed")
            write_submission([prediction], [row["id"]], out)
            save_json(sidecar, diagnostic)
            print(
                json.dumps(
                    {
                        "status": "PASS",
                        "kind": "REAL_TRAIN_READ_SMOKE_NOT_MODEL",
                        "calls": 1,
                        "tool": name,
                    }
                )
            )
            break
    else:
        raise RuntimeError("No eligible read-only train smoke sample")
