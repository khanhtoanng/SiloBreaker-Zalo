"""PROXY only: hash-gated maximum one-to-one call matching.

Unverified choices are explicit: unordered calls, equal argument key sets, fuzzy
NFC/lowercase whitespace-token F1 strictly greater than 0.6. No official parity.
"""

import unicodedata
from collections import Counter

from ..submission import validate_submission


def token_f1(a, b):
    a = Counter(unicodedata.normalize("NFC", a).lower().split())
    b = Counter(unicodedata.normalize("NFC", b).lower().split())
    if not a and not b:
        return 1.0
    return 2 * sum((a & b).values()) / (sum(a.values()) + sum(b.values())) if a and b else 0.0


def value_matches(a, b, schema, fuzzy_threshold):
    if schema.get("x-match") == "fuzzy" and isinstance(a, str) and isinstance(b, str):
        return token_f1(a, b) > fuzzy_threshold
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(
            value_matches(a[k], b[k], schema.get("properties", {}).get(k, {}), fuzzy_threshold)
            for k in a
        )
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(
            value_matches(x, y, schema.get("items", {}), fuzzy_threshold)
            for x, y in zip(a, b, strict=True)
        )
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    return a == b


def call_matches(a, b, catalog, fuzzy_threshold=0.6):
    return a["name"] == b["name"] and value_matches(
        a["arguments"],
        b["arguments"],
        catalog.get(a["name"], {}).get("parameters", {}),
        fuzzy_threshold,
    )


def matched_calls(predicted, gold, catalog, fuzzy_threshold=0.6):
    edges = [
        [
            j
            for j, expected in enumerate(gold)
            if call_matches(actual, expected, catalog, fuzzy_threshold)
        ]
        for actual in predicted
    ]
    owners: dict[int, int] = {}

    def augment(i, visited):
        for j in edges[i]:
            if j in visited:
                continue
            visited.add(j)
            if j not in owners or augment(owners[j], visited):
                owners[j] = i
                return True
        return False

    return sum(augment(i, set()) for i in range(len(predicted)))


def evaluate(predictions, gold_rows, replay_records, catalog, fuzzy_threshold=0.6):
    validate_submission(predictions, [row["id"] for row in gold_rows])
    refs = {record["id"]: record for record in replay_records}
    if len(refs) != len(replay_records):
        raise ValueError("Duplicate replay reference IDs")
    details = []
    for predicted, row in zip(predictions, gold_rows, strict=True):
        ref = refs.get(row["id"])
        if ref is None or not ref.get("pass"):
            raise ValueError(f"Missing/passing gold replay reference required for {row['id']}")
        p, g = predicted["tool_calls"], row["label"]["tool_calls"]
        matched = matched_calls(p, g, catalog, fuzzy_threshold)
        hash_match = predicted["state_hash"] == ref["state_hash"]
        f1 = 2 * matched / (len(p) + len(g)) if p or g else 1.0
        score = float(not p) if not g else f1 if hash_match else 0.0
        tags = []
        if not hash_match:
            tags.append("STATE_MISMATCH")
        if len(p) > matched:
            tags.append("EXTRA_OR_WRONG_CALL")
        if len(g) > matched:
            tags.append("MISSING_OR_WRONG_CALL")
        if not p and g:
            tags.append("EMPTY_WRONG")
        details.append(
            {
                "id": row["id"],
                "score_kind": "PROXY",
                "score": score,
                "call_f1": f1,
                "hash_match": hash_match,
                "matched_calls": matched,
                "extra_calls": len(p) - matched,
                "missing_calls": len(g) - matched,
                "exact_trajectory": p == g,
                "later_action_matches": sum(
                    call_matches(a, b, catalog, fuzzy_threshold)
                    for a, b in zip(p[1:], g[1:], strict=False)
                ),
                "later_action_denominator": max(0, max(len(p), len(g)) - 1),
                "first_action_match": bool(
                    not p
                    and not g
                    or p
                    and g
                    and call_matches(p[0], g[0], catalog, fuzzy_threshold)
                ),
                "ask_gold": any(c["name"] == "sys.ask_missing_info" for c in g),
                "ask_predicted": any(c["name"] == "sys.ask_missing_info" for c in p),
                "empty_gold": not g,
                "error_tags": tags,
            }
        )
    n = len(details)
    return {
        "score_kind": "PROXY",
        "official_parity": "UNKNOWN",
        "samples": n,
        "score": 100 * sum(d["score"] for d in details) / n if n else None,
        "hash_match_rate": sum(d["hash_match"] for d in details) / n if n else None,
        "matching": {
            "order": "unordered",
            "arguments": "equal keys",
            "fuzzy_threshold_strict_gt": fuzzy_threshold,
        },
        "records": details,
    }
