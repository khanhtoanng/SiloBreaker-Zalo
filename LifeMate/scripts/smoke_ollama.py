"""Synthetic local-model smoke; no dataset or ToolEnv is opened."""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lifemate.cli import external_output, save_json
from lifemate.ollama_policy import OllamaPolicy
from lifemate.validator import parse_decision

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="qwen3:4b-instruct-2507-q4_K_M")
    parser.add_argument("--tokenizer-path", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = external_output(args.out, inputs=(args.tokenizer_path,))
    policy = OllamaPolicy(model=args.model, tokenizer_path=args.tokenizer_path)
    started = time.monotonic()
    result = policy.next_action(
        [
            {
                "role": "system",
                "content": "Return exactly this JSON object: " + json.dumps({"kind": "DONE"}),
            },
            {"role": "user", "content": "Synthetic setup check. No tools are available."},
        ],
        deadline=time.monotonic() + 180,
    )
    decision = parse_decision(result)
    if decision != {"kind": "DONE"}:
        raise RuntimeError("Synthetic JSON protocol check failed")
    report = {
        "status": "PASS",
        "kind": "SYNTHETIC_LOCAL_MODEL_SMOKE_NOT_ACCURACY",
        "model": policy.metadata,
        "elapsed_seconds": time.monotonic() - started,
        "usage": policy.last_usage,
    }
    save_json(out, report)
    print(json.dumps({key: value for key, value in report.items() if key != "model"}), flush=True)
