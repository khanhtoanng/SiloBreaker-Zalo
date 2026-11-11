"""Compatible frozen-selection reports and paired regressions, explicitly PROXY."""

from statistics import median

from .proxy import evaluate


def enrich(report, gold_rows, *, identity=None, timings=None):
    records = report["records"]
    for record, row in zip(records, gold_rows, strict=True):
        record["apps"] = sorted(row.get("context", {}).get("installed_apps", {}))
        record["later_action_count"] = max(0, len(row["label"]["tool_calls"]) - 1)

    def rate(selected, key):
        return sum(bool(r[key]) for r in selected) / len(selected) if selected else None

    report["identity"] = identity or {}
    report["selected_ids"] = [r["id"] for r in records]
    report["whole_trajectory_rate"] = rate(records, "exact_trajectory")
    report["first_action_rate"] = rate(records, "first_action_match")
    denominator = sum(r["later_action_denominator"] for r in records)
    report["later_action_rate"] = (
        sum(r["later_action_matches"] for r in records) / denominator if denominator else None
    )
    report["ask_confusion"] = {
        key: sum(r["ask_gold"] == a and r["ask_predicted"] == b for r in records)
        for key, a, b in (
            ("tp", True, True),
            ("fn", True, False),
            ("fp", False, True),
            ("tn", False, False),
        )
    }
    report["empty_confusion"] = {
        key: sum(
            r["empty_gold"] == a and (r["matched_calls"] + r["extra_calls"] == 0) == b
            for r in records
        )
        for key, a, b in (
            ("tp", True, True),
            ("fn", True, False),
            ("fp", False, True),
            ("tn", False, False),
        )
    }
    report["slices"] = {
        app: {"samples": len(selected), "score": sum(r["score"] for r in selected) / len(selected)}
        for app in sorted({a for r in records for a in r["apps"]})
        if (selected := [r for r in records if app in r["apps"]])
    }
    values = list((timings or {}).values())
    report["timing"] = {
        "measured_samples": len(values),
        "median_seconds": median(values) if values else None,
        "max_seconds": max(values) if values else None,
    }
    return report


def compare(baseline, candidate):
    if baseline.get("identity") != candidate.get("identity") or not baseline.get("identity"):
        raise ValueError("Evaluation identity differs or is missing")
    if baseline.get("selected_ids") != candidate.get("selected_ids"):
        raise ValueError("Frozen selection/order differs")
    before = {r["id"]: r for r in baseline["records"]}
    after = {r["id"]: r for r in candidate["records"]}
    if (
        len(before) != len(baseline["records"])
        or len(after) != len(candidate["records"])
        or set(before) != set(after)
    ):
        raise ValueError("Duplicate/missing paired IDs")
    pairs = [
        {
            "id": sid,
            "delta": after[sid]["score"] - before[sid]["score"],
            "before": before[sid]["score"],
            "after": after[sid]["score"],
        }
        for sid in baseline["selected_ids"]
    ]
    return {
        "score_kind": "PROXY",
        "identity": baseline["identity"],
        "n_better": sum(p["delta"] > 0 for p in pairs),
        "n_worse": sum(p["delta"] < 0 for p in pairs),
        "n_tied": sum(p["delta"] == 0 for p in pairs),
        "records": pairs,
        "confidence_interval": None,
    }


def evaluate_report(*args, identity=None, timings=None, **kwargs):
    return enrich(evaluate(*args, **kwargs), args[1], identity=identity, timings=timings)
