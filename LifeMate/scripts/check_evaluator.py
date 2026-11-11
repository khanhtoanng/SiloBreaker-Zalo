"""Gold-derived evaluator fixture. Never an inference or model accuracy claim."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lifemate.cli import external_output, save_json
from lifemate.data_loader import load_catalog, load_manifest, resolve_data_root
from lifemate.evaluation import evaluate

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    selected_root = args.data_root
    args.data_root = resolve_data_root(args.data_root)
    out = external_output(args.out, inputs=(selected_root, args.data_root, args.replay))
    replay = json.loads(args.replay.read_text(encoding="utf-8"))
    fingerprint = hashlib.sha256(
        (args.data_root / "train" / "train.jsonl").read_bytes()
    ).hexdigest()
    if fingerprint != replay["dataset_sha256"]:
        raise ValueError("Manifest/replay fingerprint mismatch")
    rows = load_manifest(args.data_root, "train")
    references = {r["id"]: r for r in replay["records"]}
    # Deliberately label-derived fixture, never written as an inference submission.
    fixtures = [
        {
            "id": r["id"],
            "tool_calls": r["label"]["tool_calls"],
            "state_hash": references[r["id"]]["state_hash"],
        }
        for r in rows
    ]
    report = evaluate(fixtures, rows, replay["records"], load_catalog(args.data_root, "train"))
    if report["score"] != 100 or report["hash_match_rate"] != 1:
        raise RuntimeError("Gold identity fixture failed")
    summary = {k: v for k, v in report.items() if k != "records"}
    summary.update({"kind": "LABEL_DERIVED_IDENTITY_FIXTURE_NOT_MODEL_ACCURACY", "status": "PASS"})
    save_json(out, summary)
    print(json.dumps(summary))
