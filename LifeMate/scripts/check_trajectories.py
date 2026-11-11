"""Verify partition, per-step observation and action protocol integrity; no model required."""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lifemate.cli import external_output, save_json
from lifemate.data.splits import load_partition
from lifemate.data_loader import load_catalog, load_manifest, resolve_data_root
from lifemate.validator import check_value, parse_decision

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--split-config", type=Path, required=True)
    parser.add_argument("--trajectories", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--fold", choices=("grouped", "leave-app-out"), default="grouped")
    args = parser.parse_args()
    selected_root = args.data_root
    args.data_root = resolve_data_root(args.data_root)
    out = external_output(
        args.out, inputs=(selected_root, args.data_root, args.split_config, args.trajectories)
    )
    config = load_partition(
        args.split_config,
        load_manifest(args.data_root, "train"),
        manifest_path=args.data_root / "train/train.jsonl",
        fold=args.fold,
    )
    fit, val = set(config["fit_ids"]), set(config["validation_ids"])
    if fit & val:
        raise ValueError("Overlapping frozen partitions")
    catalog = load_catalog(args.data_root, "train")
    counts, steps, ended = Counter(), {}, set()
    with args.trajectories.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            sample_id = row["scenario_id"]
            if row.get("fold", "grouped") != args.fold:
                raise ValueError("Trajectory fold differs")
            partition = "fit" if sample_id in fit else "validation" if sample_id in val else None
            if partition is None or row["partition"] != partition or row["source_split"] != "train":
                raise ValueError("Trajectory source/partition mismatch")
            if sample_id in ended or row["step_index"] != steps.get(sample_id, 0):
                raise ValueError("Noncontiguous steps or action after DONE")
            steps[sample_id] = row["step_index"] + 1
            payload = json.loads(row["messages"][-2]["content"])
            observations = payload["observations"]
            if len(observations) != row["step_index"] or any(
                "outcome" not in o for o in observations
            ):
                raise ValueError("SFT/inference observation format mismatch")
            action = parse_decision(row["messages"][-1]["content"])
            if action["kind"] == "CALL":
                check_value(action["arguments"], catalog[action["tool_name"]]["parameters"])
            elif action["kind"] == "ASK":
                target = catalog[action["tool_name"]]
                if not action["arguments"].get("params") or any(
                    p not in target["parameters"]["properties"]
                    for p in action["arguments"]["params"]
                ):
                    raise ValueError("Invalid ASK target/params")
            else:
                ended.add(sample_id)
            counts[partition] += 1
            counts[action["kind"]] += 1
    if set(steps) != fit | val or ended != fit | val:
        raise ValueError("Incomplete trajectory scenarios or missing terminal decisions")
    report = {
        "status": "PASS",
        "kind": "TRAIN_TRAJECTORY_STRUCTURE_NOT_MODEL",
        "scenarios": len(steps),
        "rows": counts["fit"] + counts["validation"],
        "counts": dict(counts),
        "bytes": args.trajectories.stat().st_size,
    }
    save_json(out, report)
    print(json.dumps(report))
