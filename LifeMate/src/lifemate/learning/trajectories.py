"""Authorized train replay -> single-decision targets. Output stays outside source."""

from ..adapters.sdk import open_env
from ..data.kit import allowed_tools, inference_input
from ..runtime.context import compile_messages
from ..runtime.validation import classify


def action_target(call):
    if call["name"] == "sys.ask_missing_info":
        return {
            "kind": "ASK",
            "tool_name": call["arguments"]["tool_name"],
            "arguments": {"params": call["arguments"]["params"]},
        }
    return {"kind": "CALL", "tool_name": call["name"], "arguments": call["arguments"]}


def expand_train(
    rows, root, catalog, split_config, *, env_factory=open_env, fold="grouped", identities=None
):
    from ..data.splits import validate_partition
    from ..provenance import digest
    from .serialization import serialize_action

    split_config = validate_partition(split_config, rows, fold=fold)
    identities = identities or {
        "dataset_sha256": split_config["dataset_sha256"],
        "fold_sha256": digest(split_config),
        "schema_sha256": digest(catalog),
        "protocol": "lifemate-json-v1",
        "context": "lifemate-context-v1",
    }
    fit, val = set(split_config["fit_ids"]), set(split_config["validation_ids"])
    if fit & val or fit | val != {r["id"] for r in rows}:
        raise ValueError("Frozen partitions must be disjoint and cover train exactly")
    for row in rows:
        partition = "fit" if row["id"] in fit else "validation"
        sample = inference_input(row, oracle_text=True)
        registry = allowed_tools(sample, catalog)
        env = env_factory(root, "train", row["id"])
        observations: list[dict] = []
        calls = row["label"]["tool_calls"]
        if len(calls) != len(row["label"]["tool_results"]):
            raise ValueError("Gold call/result lengths differ")
        for index, call in enumerate(calls):
            messages = compile_messages(sample, registry, observations)
            target = action_target(call)
            result = env.call(call["name"], call["arguments"])
            if result != row["label"]["tool_results"][index]:
                raise ValueError(f"Replay result drift: {row['id']} step {index}")
            yield {
                "scenario_id": row["id"],
                "partition": partition,
                "source_split": "train",
                "step_index": index,
                "messages": messages + [{"role": "assistant", "content": serialize_action(target)}],
                "target": target,
                "fold": fold,
                "identities": identities,
            }
            observations.append(
                {
                    **call,
                    "result": result,
                    "outcome": classify(catalog[call["name"]]["kind"], result, call["name"]),
                }
            )
        yield {
            "scenario_id": row["id"],
            "partition": partition,
            "source_split": "train",
            "step_index": len(calls),
            "messages": compile_messages(sample, registry, observations)
            + [{"role": "assistant", "content": serialize_action({"kind": "DONE"})}],
            "target": {"kind": "DONE"},
            "fold": fold,
            "identities": identities,
        }
