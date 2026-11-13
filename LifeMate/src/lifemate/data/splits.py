"""Create and verify deterministic train-only scenario partitions."""

import random
from pathlib import Path

from ..contracts import FoldRecord, json_object
from ..provenance import file_sha256


def _app_ids(rows, app):
    return {row["id"] for row in rows if app in row.get("context", {}).get("installed_apps", {})}


def frozen_split(rows, manifest_path, seed=20261109, *, heldout_app=None):
    ids = sorted(row["id"] for row in rows)
    if len(ids) < 2 or len(set(ids)) != len(ids):
        raise ValueError("A frozen split needs at least two unique train IDs")
    random.Random(seed).shuffle(ids)
    count = max(1, len(ids) // 5)
    result = {
        "source_split": "train",
        "seed": seed,
        "dataset_sha256": file_sha256(manifest_path),
        "fit_ids": sorted(ids[count:]),
        "validation_ids": sorted(ids[:count]),
    }
    if heldout_app:
        heldout = _app_ids(rows, heldout_app)
        result["leave_app_out"] = {
            "app": heldout_app,
            "fit_ids": sorted(set(ids) - heldout),
            "validation_ids": sorted(heldout),
        }
    validate_partition(result, rows)
    return result


def validate_partition(config, rows, *, manifest_path=None, fold="grouped"):
    if fold not in {"grouped", "leave-app-out"}:
        raise ValueError(f"Unknown train fold: {fold}")
    grouped = FoldRecord.model_validate(config)
    all_ids = {row["id"] for row in rows}
    if manifest_path is not None and grouped.dataset_sha256 != file_sha256(manifest_path):
        raise ValueError("Frozen split dataset fingerprint differs")

    def checked(record):
        if set(record.fit_ids) | set(record.validation_ids) != all_ids:
            raise ValueError("Frozen partitions must cover the train manifest exactly")
        return record.model_dump(exclude_none=True)

    selected = checked(grouped)
    part = grouped.leave_app_out
    if part is not None:
        if set(part) != {"app", "fit_ids", "validation_ids"} or not isinstance(part["app"], str):
            raise ValueError("Leave-app-out fold requires an app and both ID lists")
        alternate = checked(
            FoldRecord.model_validate(
                {
                    "source_split": grouped.source_split,
                    "seed": grouped.seed,
                    "dataset_sha256": grouped.dataset_sha256,
                    "fit_ids": part["fit_ids"],
                    "validation_ids": part["validation_ids"],
                }
            )
        )
        if set(alternate["validation_ids"]) != _app_ids(rows, part["app"]):
            raise ValueError("Leave-app-out exposure does not match the train manifest")
        if fold == "leave-app-out":
            return {**alternate, "leave_app_out": part}
    elif fold == "leave-app-out":
        raise ValueError("Frozen configuration has no leave-app-out fold")
    return selected


def load_partition(path, rows, *, manifest_path, fold="grouped"):
    config = json_object(Path(path).read_text(encoding="utf-8"))
    return validate_partition(config, rows, manifest_path=manifest_path, fold=fold)
