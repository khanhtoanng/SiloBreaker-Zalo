"""Check labeled train traces against the organizer's SDK."""

from ..adapters.sdk import open_env


def replay_gold(rows, root, *, env_factory=open_env):
    records = []
    for row in rows:
        label = row["label"]
        calls = label["tool_calls"]
        env = env_factory(root, "train", row["id"])
        initial = env.get_state()
        results = [env.call(call["name"], call["arguments"]) for call in calls]
        final = env.get_state()
        delta = {app: state for app, state in final.items() if initial.get(app) != state}
        results_match = results == label["tool_results"]
        trace_match = env.get_tool_calls() == calls
        state_match = delta == label["final_state"]
        records.append(
            {
                "id": row["id"],
                "state_hash": env.get_state_hash(),
                "trace_match": trace_match,
                "results_match": results_match,
                "state_match": state_match,
                "pass": trace_match and results_match and state_match,
            }
        )
    passed = sum(record["pass"] for record in records)
    return {
        "counts": {"total": len(records), "passed": passed, "failed": len(records) - passed},
        "records": records,
    }
