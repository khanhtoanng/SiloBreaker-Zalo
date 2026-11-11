"""Supplied transcript pairing; never launches ASR or policy models."""

import re

from ..runtime.normalize import normalize
from .proxy import token_f1


def distance(a, b):
    previous = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        current = [i]
        for j, y in enumerate(b, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (x != y)))
        previous = current
    return previous[-1]


def critical(text, context):
    normalized = normalize(text, context)
    return {
        "phone": re.findall(r"(?<!\d)0\d{8,10}(?!\d)", text),
        "amount": [
            v["value"]
            for v in normalized["values"]
            if v["kind"] == "amount" and not v["superseded"] and not v["uncertain"]
        ],
        "time": [
            v["value"]
            for v in normalized["values"]
            if v["kind"] == "time" and not v["superseded"] and not v["uncertain"]
        ],
        "uncertainty": [
            {"text": text[u["span"][0] : u["span"][1]], "reason": u["reason"]}
            for u in normalized["uncertainties"]
        ],
        "negation": bool(normalized["negation_spans"]),
        "correction": bool(normalized["correction_spans"]),
    }


def evaluate_asr(reference, candidate):
    if not reference.get("identity") or reference.get("identity") != candidate.get("identity"):
        raise ValueError("ASR/oracle policy/fold/config identity differs")

    def index(rows):
        result = {r["id"]: r for r in rows}
        if len(result) != len(rows):
            raise ValueError("Duplicate transcript IDs")
        return result

    refs = index(reference["records"])
    cands = index(candidate["records"])
    if set(refs) != set(cands):
        raise ValueError("Missing same-ID transcript pairs")
    rows = []
    word_errors = char_errors = words = chars = 0
    for sid, ref in refs.items():
        cand = cands[sid]
        a = ref["text"]
        b = cand["text"]
        we = distance(a.split(), b.split())
        ce = distance(list(a), list(b))
        nw = len(a.split())
        nc = len(a)
        word_errors += we
        char_errors += ce
        words += nw
        chars += nc
        before = critical(a, ref.get("context", {}))
        after = critical(b, ref.get("context", {}))
        rows.append(
            {
                "id": sid,
                "word_errors": we,
                "reference_words": nw,
                "wer": we / nw if nw else None,
                "char_errors": ce,
                "reference_chars": nc,
                "cer": ce / nc if nc else None,
                "critical_slot_differences": {
                    k: {"reference": v, "candidate": after[k]}
                    for k, v in before.items()
                    if after[k] != v
                },
                "name_match": token_f1(ref["name"], cand["name"])
                if "name" in ref and "name" in cand
                else None,
                "call_f1_delta": cand["call_f1"] - ref["call_f1"]
                if "call_f1" in ref and "call_f1" in cand
                else None,
                "hash_match_delta": int(cand["hash_match"]) - int(ref["hash_match"])
                if type(ref.get("hash_match")) is bool and type(cand.get("hash_match")) is bool
                else None,
                "calls_changed": cand["tool_calls"] != ref["tool_calls"]
                if "tool_calls" in ref and "tool_calls" in cand
                else None,
                "state_hash_changed": cand["state_hash"] != ref["state_hash"]
                if "state_hash" in ref and "state_hash" in cand
                else None,
                "downstream_delta": cand["score"] - ref["score"]
                if "score" in ref and "score" in cand
                else None,
                "timing_delta": cand["elapsed_seconds"] - ref["elapsed_seconds"]
                if "elapsed_seconds" in ref and "elapsed_seconds" in cand
                else None,
            }
        )
    return {
        "kind": "SUPPLIED_ASR_COMPARISON",
        "identity": reference["identity"],
        "word_errors": word_errors,
        "reference_words": words,
        "wer": word_errors / words if words else None,
        "char_errors": char_errors,
        "reference_chars": chars,
        "cer": char_errors / chars if chars else None,
        "records": rows,
    }
