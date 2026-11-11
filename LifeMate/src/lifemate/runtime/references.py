"""Typed provenance and conservative ambiguity/collection/parent checks."""

import re

from .validation import Rejected, present


def string_leaves(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from string_leaves(item)
    elif isinstance(value, list):
        for item in value:
            yield from string_leaves(item)


class ReferenceIndex:
    def __init__(self, sample: dict):
        self.values: dict[str, list[dict]] = {}
        self.groups: dict[str, list[dict]] = {}
        self.explicit = list(string_leaves(sample.get("context", {}))) + [sample.get("text", "")]
        for turn_index, turn in enumerate(sample.get("history", [])):
            if turn.get("role") == "user":
                self.explicit.extend(string_leaves(turn.get("text", "")))
            for call_index, (call, result) in enumerate(
                zip(turn.get("tool_calls", []), turn.get("tool_results", []), strict=False)
            ):
                self.observe(
                    call["name"],
                    result,
                    f"history:{turn_index}:{call_index}",
                    call.get("arguments", {}),
                )

    def observe(self, tool_name: str, result, source: str, arguments: dict | None = None) -> None:
        if not isinstance(result, dict) or result.get("ok") is False or result.get("done") is False:
            return
        app = tool_name.split(".")[0]
        requested_parent = (
            (arguments or {}).get("restaurant_id")
            if tool_name == "food_delivery.get_menu"
            else None
        )

        def visit(value, collection=None, parent=None, group=None):
            if isinstance(value, dict):
                if isinstance(value.get("id"), str):
                    self.values.setdefault(value["id"], []).append(
                        {
                            "source": source,
                            "ref_type": f"{app}.{collection}" if collection else None,
                            "attributes": {
                                k: v
                                for k, v in value.items()
                                if k
                                in (
                                    "type",
                                    "device_type",
                                    "restaurant_id",
                                    "name",
                                    "room",
                                    "floor",
                                    "phone",
                                )
                            },
                            "parent_id": value.get("restaurant_id", parent),
                            "group": group,
                        }
                    )
                for key, child in value.items():
                    visit(
                        child,
                        key if isinstance(child, list) else collection,
                        value.get("id", parent),
                        group,
                    )
            elif isinstance(value, list):
                identifier = f"{source}:{collection}:{parent}"
                self.groups[identifier] = [
                    v for v in value if isinstance(v, dict) and isinstance(v.get("id"), str)
                ]
                for child in value:
                    visit(child, collection, parent, identifier)

        visit(result, parent=requested_parent)

    def disambiguated(self, value, sources, desired_type):
        for source in sources:
            members = self.groups.get(source.get("group"), [])
            if len(members) <= 1:
                return True
            if desired_type:
                members = [m for m in members if m.get("type") in (None, desired_type)]
            if len(members) == 1 and members[0]["id"] == value:
                return True
            matches = []
            for member in members:
                attrs = [
                    v.casefold()
                    for k, v in member.items()
                    if k in ("name", "room", "phone") and isinstance(v, str) and v
                ]
                if any(attr in text.casefold() for attr in attrs for text in self.explicit):
                    matches.append(member)
            if len(matches) == 1 and matches[0]["id"] == value:
                return True
        return False

    def check(self, arguments: dict, schema: dict, tool_name: str | None = None) -> list[dict]:
        evidence = []

        def visit(value, spec, path):
            # The inspected food schema omits x-ref for nested item_id. This is
            # an explicit project semantic supplement, never a catalog rewrite.
            if tool_name == "food_delivery.place_order" and path.endswith(".item_id"):
                spec = {**spec, "x-ref": "food_delivery.menu"}
            if spec.get("x-ref") and present(value):
                sources = self.values.get(value, []) if isinstance(value, str) else []
                literal = isinstance(value, str) and any(
                    re.search(r"(?<!\w)" + re.escape(value) + r"(?!\w)", text)
                    for text in self.explicit
                )
                literal = (
                    literal
                    or value in spec.get("enum", [])
                    or ("const" in spec and value == spec["const"])
                )
                known_types = {s["ref_type"] for s in sources if s["ref_type"]}
                if known_types and spec["x-ref"] not in known_types:
                    raise Rejected(f"{path}: known collection mismatch")
                desired = None
                if tool_name and path.endswith("device_id"):
                    desired = next(
                        (
                            kind
                            for kind in ("light", "fan", "climate")
                            if "." + kind + "_" in tool_name
                        ),
                        None,
                    )
                    types = {s["attributes"].get("type") for s in sources} - {None}
                    if desired and types and desired not in types:
                        raise Rejected(f"{path}: known device type mismatch")
                restaurant = arguments.get("restaurant_id")
                parents = {s.get("parent_id") for s in sources} - {None}
                if "menu" in spec["x-ref"] and restaurant and parents and restaurant not in parents:
                    raise Rejected(f"{path}: restaurant/menu mismatch")
                if not sources and not literal:
                    raise Rejected(
                        f"{path}: ungrounded reference {spec['x-ref']}; use a read or ASK"
                    )
                if sources and not literal and not self.disambiguated(value, sources, desired):
                    raise Rejected(f"{path}: ambiguous lookup evidence; refine read or ASK")
                evidence.append(
                    {
                        "path": path,
                        "value": value,
                        "required_ref_type": spec["x-ref"],
                        "sources": sources or [{"source": "explicit_input", "ref_type": None}],
                        "type_confirmed": any(s["ref_type"] == spec["x-ref"] for s in sources),
                    }
                )
            if isinstance(value, dict):
                for key, child in value.items():
                    visit(child, spec.get("properties", {}).get(key, {}), f"{path}.{key}")
            elif isinstance(value, list):
                for i, child in enumerate(value):
                    visit(child, spec.get("items", {}), f"{path}[{i}]")

        visit(arguments, schema, "arguments")
        return evidence
