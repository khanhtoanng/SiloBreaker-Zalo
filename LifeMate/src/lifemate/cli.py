"""Offline LifeMate preparation, inference, evaluation and later-run training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .artifacts import external_output as external_output
from .artifacts import save_json as save_json
from .data.splits import load_partition as load_partition


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in (
        "freeze",
        "predict",
        "evaluate",
        "trajectories",
        "validate",
        "replay",
        "audit",
        "train",
        "config-check",
        "compare",
        "asr-evaluate",
        "package-check",
    ):
        sub.add_parser(name, argument_default=argparse.SUPPRESS)
    for name in ("freeze", "predict", "evaluate", "trajectories", "validate", "replay", "audit"):
        p = sub.choices[name]
        p.add_argument("--data-root", type=Path)
        p.add_argument("--out", type=Path)
    for name in ("predict", "evaluate", "trajectories"):
        sub.choices[name].add_argument("--split-config", type=Path)
        sub.choices[name].add_argument("--fold", choices=("grouped", "leave-app-out"))
    for name in ("predict", "evaluate", "train", "package-check", "config-check"):
        sub.choices[name].add_argument("--config", type=Path)
    for name in ("evaluate", "validate"):
        sub.choices[name].add_argument("--predictions", type=Path)
    sub.choices["freeze"].add_argument("--seed", type=int)
    sub.choices["freeze"].add_argument("--heldout-app")
    p = sub.choices["predict"]
    p.add_argument("--backend", choices=("ollama", "transformers"))
    p.add_argument("--model-path", type=Path)
    p.add_argument("--tokenizer-path", type=Path)
    p.add_argument("--adapter-path", type=Path)
    p.add_argument("--asr-path", type=Path)
    p.add_argument("--ollama-model")
    p.add_argument("--ollama-url")
    p.add_argument("--input-mode", choices=("oracle", "audio"))
    p.add_argument("--selection", choices=("validation", "fit", "all"))
    for name in ("predict", "validate"):
        sub.choices[name].add_argument("--split", choices=("train", "public_test", "private_test"))
    for name in ("predict", "evaluate"):
        sub.choices[name].add_argument("--limit", type=int)
    for flag in (
        "max-context-tokens",
        "max-new-tokens",
        "max-decisions",
        "max-repairs",
        "max-generations",
        "done-reconsiderations",
    ):
        p.add_argument("--" + flag, type=int)
    p.add_argument("--sample-seconds", type=float)
    p.add_argument(
        "--require-reference-provenance",
        action="store_true",
        help="Deprecated spelling; reference enforcement is always active",
    )
    sub.choices["evaluate"].add_argument("--replay", type=Path)
    sub.choices["train"].add_argument("--dry-run", action="store_true")
    sub.choices["config-check"].add_argument(
        "--kind", choices=("inference", "training", "evaluation"), required=True
    )
    for name in ("compare", "asr-evaluate"):
        q = sub.choices[name]
        q.add_argument(
            "--baseline" if name == "compare" else "--reference", type=Path, required=True
        )
        q.add_argument("--candidate", type=Path, required=True)
        q.add_argument("--out", type=Path, required=True)
    return parser


def main(argv=None, *, dispatcher=None) -> None:
    """Print the command result and let the launcher exit successfully."""
    parser = build_parser()
    values = vars(parser.parse_args(argv))
    command = values.pop("command")
    if dispatcher is None:
        from .workflows import dispatch

        dispatcher = dispatch
    try:
        result = dispatcher(command, values)
    except (ValueError, FileNotFoundError, FileExistsError) as exc:
        parser.error(str(exc))
    if result is not None:
        print(json.dumps(result, ensure_ascii=False, allow_nan=False, default=str))
    if command == "replay" and result is not None and result.get("counts", {}).get("failed", 0):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
