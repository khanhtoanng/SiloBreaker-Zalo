"""Pre-execution checks supplement, and never replace, official env.validate."""

from __future__ import annotations

import json
import math


class Rejected(ValueError):
    pass


def present(value):
    return value is not None and value != "" and value != [] and value != {}


def check_value(value, schema, path="arguments"):
    types = {
        "object": lambda v: isinstance(v, dict),
        "array": lambda v: isinstance(v, list),
        "string": lambda v: isinstance(v, str),
        "boolean": lambda v: isinstance(v, bool),
        "integer": lambda v: type(v) is int,
        "number": lambda v: type(v) in (int, float) and math.isfinite(v),
    }
    if schema.get("type") in types and not types[schema["type"]](value):
        raise Rejected(f"{path}: expected {schema['type']}")
    if "enum" in schema and not any(type(value) is type(x) and value == x for x in schema["enum"]):
        raise Rejected(f"{path}: invalid enum value")
    if type(value) in (int, float):
        if not math.isfinite(value):
            raise Rejected(f"{path}: nonfinite number")
        for key, valid in (
            ("minimum", lambda a, b: a >= b),
            ("maximum", lambda a, b: a <= b),
            ("exclusiveMinimum", lambda a, b: a > b),
            ("exclusiveMaximum", lambda a, b: a < b),
        ):
            if key in schema and not valid(value, schema[key]):
                raise Rejected(f"{path}: violates {key}")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        extras = set(value) - set(props)
        if extras and ("properties" in schema or schema.get("additionalProperties") is False):
            raise Rejected(f"{path}: unknown fields {sorted(extras)}")
        missing = [key for key in schema.get("required", []) if not present(value.get(key))]
        if missing:
            raise Rejected(f"{path}: missing {missing}")
        groups = schema.get("x-one-of", [])
        if groups and not any(all(present(value.get(k)) for k in group) for group in groups):
            raise Rejected(f"{path}: missing x-one-of alternative")
        for key, item in value.items():
            if key in props:
                check_value(item, props[key], f"{path}.{key}")
    if isinstance(value, str):
        import re
        from datetime import datetime

        if "minLength" in schema and len(value) < schema["minLength"]:
            raise Rejected(f"{path}: violates minLength")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise Rejected(f"{path}: violates maxLength")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise Rejected(f"{path}: violates pattern")
        fmt = schema.get("format")
        if fmt in ("date", "time", "date-time"):
            from datetime import date, time

            patterns = {
                "date": r"\d{4}-\d{2}-\d{2}",
                "time": r"\d{1,2}:\d{2}(?::\d{2})?",
                "date-time": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?",
            }
            try:
                if re.fullmatch(patterns[fmt], value) is None:
                    raise ValueError("Invalid ISO shape")
                if fmt == "date":
                    date.fromisoformat(value)
                elif fmt == "time":
                    time.fromisoformat(value if len(value.split(":")[0]) == 2 else "0" + value)
                else:
                    datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise Rejected(f"{path}: expected {fmt}") from exc
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise Rejected(f"{path}: violates minItems")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise Rejected(f"{path}: violates maxItems")
    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            check_value(item, schema["items"], f"{path}[{index}]")


def parse_decision(raw):
    from ..contracts import DECISION, json_loads

    try:
        if not isinstance(raw, str):
            json.dumps(raw, allow_nan=False)
        return DECISION.model_validate(
            json_loads(raw) if isinstance(raw, str) else raw
        ).root.model_dump()
    except (ValueError, TypeError) as exc:
        raise Rejected(f"Expected one strict decision: {exc}") from exc


def checked_call(decision, registry, env):
    name, args = decision["tool_name"], decision["arguments"]
    if decision["kind"] == "ASK":
        if name not in registry or name == "sys.ask_missing_info":
            raise Rejected("ASK target must be an installed action tool")
        if set(args) != {"params"} or not isinstance(args["params"], list) or not args["params"]:
            raise Rejected("ASK requires a nonempty params array")
        props = registry[name]["parameters"].get("properties", {})
        if any(not isinstance(p, str) or p not in props for p in args["params"]):
            raise Rejected("ASK refers to nonexistent target parameters")
        name, args = "sys.ask_missing_info", {"tool_name": name, "params": args["params"]}
    elif name == "sys.ask_missing_info":
        raise Rejected("Use the ASK decision for the system missing-info tool")
    if name not in registry:
        raise Rejected(f"Tool is not installed: {name}")
    check_value(args, registry[name]["parameters"])
    result = env.validate(name, args)
    if result.get("ok") is not True:
        raise Rejected(f"SDK validation: {result.get('error')}")
    return name, args


# Result markers verified in the organizer handlers. This is not a tool allowlist:
# all installed tools remain eligible, including unseen split tools.
WRITE_MARKERS: dict[str, dict[str, type | tuple[type, ...]]] = {
    "banking.open_savings": {"savings": dict},
    "bill_payment.pay": {"bill": dict},
    "bill_payment.schedule_autopay": {"autopay": dict},
    "sms.send": {"message": dict},
    "chat_ott.send_message": {"message": dict},
    "chat_ott.send_location": {"message": dict},
    "chat_ott.call": {"call": dict},
    "phone.call": {"call": dict},
    "bike_rental.reserve": {"reservation": dict},
    "library.reserve": {"reservation": dict},
    "email.send": {"email": dict},
    "email.reply": {"email": dict},
    "email.create_draft": {"draft": dict},
    "loyalty.redeem": {"voucher": dict},
    "home_automation.create_rule": {"rule": dict},
    "robot_vacuum.start": {"current_job": dict},
    "robot_vacuum.stop": {"status": str},
    "music.play": {"now_playing": dict},
    "music.control": {"now_playing": dict, "volume": int},
    "music.add_to_playlist": {"playlist": dict},
    "podcast_radio.play": {"now_playing": dict},
    "podcast_radio.queue": {"queue": list},
    "podcast_radio.subscribe": {"subscriptions": list},
    "learning.log_progress": {"progress": dict},
    "learning.schedule_lesson": {"lesson": dict},
    "fitness.log_workout": {"workout": dict},
    "fitness.set_goal": {"goal_steps": int},
    "package_tracking.schedule_pickup": {"pickup": dict},
    "package_tracking.reschedule_delivery": {"shipment": dict},
    "home_energy.set_alert": {"alert_threshold_kwh": (int, float)},
    "medication.log_taken": {"log": dict},
    "door_lock.grant_guest_code": {"guest_code": dict},
    "tv.record": {"recording": dict},
    "tv.control": {"power": str, "volume": int},
    "tv.tune": {"channel": str},
    "home_security.arm": {"mode": str},
    "smart_home.scene_run": {"scene_id": str},
}
BARE_OK_DELETIONS = {
    "home_automation.delete_rule",
    "medication.remove",
    "shopping_list.remove",
    "email.archive",
    "alarm.delete",
    "reminders.delete",
}


def classify(kind, result, tool_name=None):
    if not isinstance(result, dict):
        return "UNKNOWN"
    if result.get("ok") is False:
        return "REJECTED"
    if result.get("done") is False:
        return "BUSINESS_NOOP"
    if result.get("waiting_for_user") is True:
        return "META_WAIT"
    if result.get("ok") is not True:
        return "UNKNOWN"
    if kind == "read":
        return "READ_OBSERVATION"
    if kind == "write" and (
        result.get("done") is True
        or any(k in result for k in ("item", "transaction", "booking", "order"))
    ):
        return "WRITE_EFFECT"
    if kind == "write":
        if tool_name in BARE_OK_DELETIONS and set(result) == {"ok"}:
            return "WRITE_EFFECT"
        markers = WRITE_MARKERS.get(tool_name, {})
        if any(
            isinstance(result.get(key), expected) and not isinstance(result.get(key), bool)
            for key, expected in markers.items()
        ):
            return "WRITE_EFFECT"
    # Tool-specific success semantics remain unverified for other shapes.
    return "UNKNOWN"
