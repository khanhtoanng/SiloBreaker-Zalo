"""Strict submission checks. Missing rows are errors, never implicit empty actions."""

import json

from .contracts import SubmissionRow, TimedSubmissionRow


def validate_submission(rows, expected_ids, *, include_timing=False):
    schema = TimedSubmissionRow if include_timing else SubmissionRow
    ids = []
    for row in rows:
        ids.append(schema.model_validate(row).id)
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate prediction IDs")
    if len(set(expected_ids)) != len(expected_ids):
        raise ValueError("Duplicate expected IDs")
    if ids != list(expected_ids):
        raise ValueError("Submission IDs/order differ from selected manifest")
    json.dumps(rows, allow_nan=False)


def write_submission(rows, expected_ids, path, *, include_timing=False):
    from .artifacts import write_jsonl

    validate_submission(rows, expected_ids, include_timing=include_timing)
    write_jsonl(path, rows)
