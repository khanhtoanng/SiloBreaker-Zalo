"""Conservative observation classification grounded in inspected SDK markers."""

from .validation import classify as legacy_classify


def classify(kind, result, tool_name=None):
    outcome = legacy_classify(kind, result, tool_name)
    return "SCHEMA_REJECTED" if outcome == "REJECTED" else outcome
