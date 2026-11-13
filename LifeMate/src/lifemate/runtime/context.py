"""Single next-action protocol; all eligible schemas and observed history retained."""

import json

SYSTEM = """You execute Vietnamese user requests using only the installed tools below.
Choose exactly ONE next decision as JSON, with no markdown or extra fields:
For example, if installed:
{"kind":"CALL","tool_name":"contacts.search","arguments":{"name":"Lan"}}
{"kind":"ASK","tool_name":"sms.send","arguments":{"params":["content"]}}
{"kind":"DONE"}
Use actual tool observations to choose the next action. IDs must come from explicit
user/context/history data or live observations; never guess an entity ID. Resolve
ambiguous entities with available reads, then ASK if still unresolved. Use the sample
current_time and timezone for dates and money units accurately. Preserve requested
text, corrections and negation. History operations are already applied; do not replay
them. Complete each explicit goal. A result done:false is not success. Do not retry
a write after success or uncertain execution. Deliberate repeated actions require
separate user intent. Return DONE for unsupported requests or completed goals.
ASK must name an installed target tool and its actual missing parameters and ends
this turn. Put tool_name at the top level only. Do not make extra verification calls
after success. Only use an optional argument when the user or tool contract supplies
its value. Use profile home/work addresses when the user refers to them. Never request
or inspect hidden state.
"""


def compile_messages(
    sample, registry, observations, rejection=None, *, ledger=None, max_characters=None
):
    if not isinstance(sample.get("text"), str):
        raise ValueError(
            "This text baseline requires text; train CLI supplies authorized oracle transcripts"
        )
    payload = {
        "installed_tools": list(registry.values()),
        "context": sample.get("context", {}),
        "history": sample.get("history", []),
        "latest_user_text": sample["text"],
        "observations": observations,
        "normalization": sample.get("normalization"),
    }
    if ledger is not None:
        payload["goal_ledger"] = ledger
    if rejection:
        payload["previous_decision_rejected_before_execution"] = rejection
    encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False)
    if (
        max_characters is not None
        and len(encoded.encode("utf-8")) + len(SYSTEM.encode("utf-8")) > max_characters
    ):
        raise ValueError("CONTEXT_OVERFLOW: required schemas/history/evidence cannot fit")
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": encoded}]
