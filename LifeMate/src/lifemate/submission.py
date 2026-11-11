"""Strict submission checks. Missing rows are errors, never implicit empty actions."""

import json
import re


def validate_submission(rows, expected_ids):
    from .contracts import SubmissionRow

    ids = []
    for row in rows:
        SubmissionRow.model_validate(row)
        if set(row) != {"id", "tool_calls", "state_hash"}:
            raise ValueError("Submission fields must be id, tool_calls, state_hash")
        if not isinstance(row["id"], str) or not row["id"]:
            raise ValueError("Invalid prediction id")
        if not isinstance(row["state_hash"], str) or not re.fullmatch(
            r"[0-9a-f]{64}", row["state_hash"]
        ):
            raise ValueError("Expected SDK SHA-256 state hash")
        if not isinstance(row["tool_calls"], list):
            raise ValueError("tool_calls must be an array")
        for call in row["tool_calls"]:
            if (
                not isinstance(call, dict)
                or set(call) != {"name", "arguments"}
                or not isinstance(call["name"], str)
                or not isinstance(call["arguments"], dict)
            ):
                raise ValueError("Invalid call shape")
        ids.append(row["id"])
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate prediction IDs")
    if len(set(expected_ids)) != len(expected_ids):
        raise ValueError("Duplicate expected IDs")
    if ids != list(expected_ids):
        raise ValueError("Submission IDs/order differ from selected manifest")
    json.dumps(rows, allow_nan=False)


def write_submission(rows, expected_ids, path):
    from .artifacts import write_jsonl

    validate_submission(rows, expected_ids)
    write_jsonl(path, rows)
