"""Synthetic behavioral assertions, not organizer gold/policy accuracy claims."""

import copy
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lifemate.agent_loop import RunConfig, infer
from lifemate.data_loader import (
    allowed_tools,
    frozen_split,
    inference_input,
    load_catalog,
    read_jsonl,
    resolve_data_root,
)
from lifemate.evaluation import call_matches, evaluate, matched_calls, token_f1
from lifemate.references import ReferenceIndex
from lifemate.submission import validate_submission, write_submission
from lifemate.validator import Rejected, check_value, checked_call, classify, parse_decision


def tool(name, kind, properties, required=()):
    return {
        "name": name,
        "kind": kind,
        "app": name.split(".")[0],
        "parameters": {"type": "object", "properties": properties, "required": list(required)},
    }


CATALOG = {
    "contacts.search": tool("contacts.search", "read", {"name": {"type": "string"}}),
    "sms.send": tool(
        "sms.send",
        "write",
        {
            "contact_id": {"type": "string", "x-ref": "contacts.contacts"},
            "content": {"type": "string", "x-match": "fuzzy"},
        },
        ["contact_id", "content"],
    ),
    "sys.ask_missing_info": tool(
        "sys.ask_missing_info",
        "meta",
        {"tool_name": {"type": "string"}, "params": {"type": "array", "items": {"type": "string"}}},
        ["tool_name", "params"],
    ),
}
SAMPLE = {
    "id": "synthetic_1",
    "text": "Nhắn Minh tôi đến muộn",
    "context": {
        "current_time": "2026-11-10T14:00:00+07:00",
        "installed_apps": {
            "contacts": {"tools": ["contacts.search"]},
            "sms": {"tools": ["sms.send"]},
        },
    },
    "history": [],
}

SAMPLE["context"]["profile"] = {"contact_id": "c1"}


def call(tool_name="sms.send", **arguments):
    return {"name": tool_name, "arguments": arguments}


def decision(tool_name="sms.send", **arguments):
    return {"kind": "CALL", "tool_name": tool_name, "arguments": arguments}


class FakeEnv:
    """Test fixture only. Production always opens the organizer SDK."""

    def __init__(self, results=()):
        self.calls = []
        self.events = []
        self.results = iter(results)

    def validate(self, name, arguments):
        self.events.append("validate")
        return {"ok": True}

    def call(self, name, arguments):
        self.events.append("call")
        self.calls.append({"name": name, "arguments": copy.deepcopy(arguments)})
        return next(self.results, {"ok": True, "done": True})

    def get_tool_calls(self):
        return copy.deepcopy(self.calls)

    def get_state_hash(self):
        return "a" * 64

    def get_state(self):
        raise AssertionError("Inference must never inspect state")


class ScriptedPolicy:
    def __init__(self, actions):
        actions = list(actions)
        self.actions = iter(actions)
        self.planned_actions = actions
        self.messages = []

    def plan(self, request_context, *, deadline):
        writes = [
            a
            for a in self.planned_actions
            if a.get("kind") == "CALL" and a.get("tool_name") == "sms.send"
        ]
        return {
            "goals": [
                {
                    "id": "send",
                    "intent": "send requested message",
                    "tool_name": "sms.send",
                    "arguments": {},
                    "occurrences": [{"id": "send-1", "span": [0, len(SAMPLE["text"])]}],
                }
            ]
            if writes
            else []
        }

    def next_action(self, messages, *, deadline):
        self.messages.append(copy.deepcopy(messages))
        return next(self.actions, {"kind": "DONE"})


class RuntimeTests(unittest.TestCase):
    def run_agent(self, actions, results=(), sample=None, config=None):
        env, policy, opened = FakeEnv(results), ScriptedPolicy(actions), []

        def factory(*args):
            opened.append(args)
            return env

        prediction, diagnostic = infer(
            sample or SAMPLE,
            ".",
            "train",
            CATALOG,
            policy,
            config or RunConfig(),
            env_factory=factory,
        )
        self.assertEqual(len(opened), 1)
        self.assertEqual(prediction["tool_calls"], env.calls)
        self.assertEqual(prediction["state_hash"], "a" * 64)
        return prediction, diagnostic, env, policy

    def test_K01_uninstalled_tool_blocked(self):
        result, _, env, _ = self.run_agent([decision("banking.transfer", amount=10)])
        self.assertEqual(result["tool_calls"], [])
        self.assertNotIn("call", env.events)

    def test_K02_required_blocked_before_sdk_call(self):
        _, _, env, _ = self.run_agent([decision(content="hello")])
        self.assertEqual(env.events, [])

    def test_K10_K11_exact_getters_and_one_session(self):
        prediction, _, env, _ = self.run_agent([decision(contact_id="c1", content="hello")])
        self.assertEqual(prediction["tool_calls"], [call(contact_id="c1", content="hello")])
        self.assertEqual(env.events, ["validate", "call"])

    def test_K12_history_kept_without_replay(self):
        sample = copy.deepcopy(SAMPLE)
        sample["history"] = [
            {
                "role": "assistant",
                "tool_calls": [call(contact_id="c_old", content="history")],
                "tool_results": [{"ok": True}],
            }
        ]
        prediction, _, _, policy = self.run_agent([{"kind": "DONE"}], sample=sample)
        self.assertEqual(prediction["tool_calls"], [])
        self.assertIn("c_old", policy.messages[0][1]["content"])

    def test_K18_noop_is_terminal_without_retry(self):
        _, diagnostic, env, _ = self.run_agent(
            [decision(contact_id="c1", content="hi")] * 2, [{"ok": True, "done": False}]
        )
        self.assertEqual(diagnostic["stop_reason"], "BUSINESS_NOOP")
        self.assertEqual(len(env.calls), 1)

    def test_K26_wrong_ask_param_blocked(self):
        prediction, _, _, _ = self.run_agent(
            [{"kind": "ASK", "tool_name": "sms.send", "arguments": {"params": ["invented"]}}]
        )
        self.assertEqual(prediction["tool_calls"], [])

    def test_K27_done_has_empty_real_trace(self):
        prediction, diagnostic, _, _ = self.run_agent([{"kind": "DONE"}])
        self.assertEqual(prediction["tool_calls"], [])
        self.assertEqual(diagnostic["stop_reason"], "DONE")

    def test_K28_K29_two_goals_then_terminal_ask(self):
        actions = [
            decision(contact_id="c1", content="first"),
            {"kind": "ASK", "tool_name": "sms.send", "arguments": {"params": ["contact_id"]}},
            decision(contact_id="c2", content="must not run"),
        ]
        prediction, diagnostic, _, _ = self.run_agent(
            actions, [{"ok": True, "done": True}, {"ok": True, "waiting_for_user": True}]
        )
        self.assertEqual(
            [c["name"] for c in prediction["tool_calls"]], ["sms.send", "sys.ask_missing_info"]
        )
        self.assertEqual(diagnostic["stop_reason"], "ASK")

    def test_read_then_observation_grounded_write(self):
        class GroundedPolicy(ScriptedPolicy):
            def plan(self, request_context, *, deadline):
                return {
                    "goals": [
                        {
                            "id": "send",
                            "intent": "requested send",
                            "tool_name": "sms.send",
                            "occurrences": [{"id": "send-1", "span": [0, 5]}],
                        }
                    ]
                }

            def next_action(self, messages, *, deadline):
                payload = json.loads(messages[1]["content"])
                if not payload["observations"]:
                    return decision("contacts.search", name="Minh")
                if len(payload["observations"]) == 1:
                    identifier = payload["observations"][0]["result"]["contacts"][0]["id"]
                    return decision(contact_id=identifier, content="hello")
                return {"kind": "DONE"}

        env = FakeEnv(
            [{"ok": True, "contacts": [{"id": "c_observed"}]}, {"ok": True, "done": True}]
        )
        prediction, _ = infer(
            SAMPLE, ".", "train", CATALOG, GroundedPolicy([]), env_factory=lambda *_: env
        )
        self.assertEqual(prediction["tool_calls"][1]["arguments"]["contact_id"], "c_observed")

    def test_six_calls_plus_done(self):
        class ReadPolicy(ScriptedPolicy):
            def plan(self, request_context, *, deadline):
                return {
                    "goals": [
                        {
                            "id": f"read-{i}",
                            "intent": f"search for contact {i}",
                            "tool_name": "contacts.search",
                            "arguments": {"name": str(i)},
                            "occurrences": [{"id": f"occurrence-{i}", "span": [i * 2, i * 2 + 1]}],
                        }
                        for i in range(6)
                    ]
                }

        actions = [decision("contacts.search", name=str(i)) for i in range(6)] + [{"kind": "DONE"}]
        prediction, diagnostic = infer(
            {**SAMPLE, "text": "0 1 2 3 4 5"},
            ".",
            "train",
            CATALOG,
            ReadPolicy(actions),
            env_factory=lambda *_: FakeEnv(),
        )
        self.assertEqual(len(prediction["tool_calls"]), 6)
        self.assertEqual(diagnostic["stop_reason"], "DONE")

    def test_unknown_write_outcome_not_retried(self):
        _, diagnostic, env, _ = self.run_agent(
            [decision(contact_id="c1", content="hi")] * 2, [{"ok": True, "message": "uncertain"}]
        )
        self.assertEqual(len(env.calls), 1)
        self.assertEqual(diagnostic["stop_reason"], "UNKNOWN")

    def test_late_policy_proposal_not_executed(self):
        class LatePolicy:
            def next_action(self, messages, *, deadline):
                time.sleep(0.02)
                return decision(contact_id="c1", content="late")

        env = FakeEnv()
        prediction, diagnostic = infer(
            SAMPLE,
            ".",
            "train",
            CATALOG,
            LatePolicy(),
            RunConfig(sample_seconds=0.01),
            env_factory=lambda *_: env,
        )
        self.assertEqual(prediction["tool_calls"], [])
        self.assertEqual(diagnostic["stop_reason"], "TIMEOUT")

    def test_backend_timeout_preserves_trace_and_reports_timeout(self):
        class TimedOutPolicy:
            def next_action(self, messages, *, deadline):
                raise TimeoutError("local generation timeout")

        env = FakeEnv()
        prediction, diagnostic = infer(
            SAMPLE, ".", "train", CATALOG, TimedOutPolicy(), env_factory=lambda *_: env
        )
        self.assertEqual(prediction["tool_calls"], [])
        self.assertEqual(diagnostic["stop_reason"], "TIMEOUT")

    def test_label_leakage_rejected(self):
        with self.assertRaises(ValueError):
            infer({**SAMPLE, "label": {}}, ".", "train", CATALOG, ScriptedPolicy([]))

    def test_inference_input_allowlist(self):
        row = {
            **SAMPLE,
            "audio_text": "oracle",
            "label": {"tool_calls": ["secret"]},
            "unknown": "secret",
        }
        cleaned = inference_input(row, oracle_text=True)
        self.assertNotIn("secret", json.dumps(cleaned))
        self.assertEqual(cleaned["text"], "oracle")


class SchemaTests(unittest.TestCase):
    def test_reference_provenance_read_history_literal_and_unknown(self):
        index = ReferenceIndex(SAMPLE)
        schema = CATALOG["sms.send"]["parameters"]
        with self.assertRaises(Rejected):
            index.check({"contact_id": "made_up"}, schema)
        index.observe("contacts.search", {"ok": True, "contacts": [{"id": "c1"}]}, "live:0")
        proof = index.check({"contact_id": "c1"}, schema)
        self.assertTrue(proof[0]["type_confirmed"])
        sample = copy.deepcopy(SAMPLE)
        sample["history"] = [
            {
                "role": "assistant",
                "tool_calls": [call("contacts.search", name="Minh")],
                "tool_results": [{"ok": True, "contacts": [{"id": "history_id"}]}],
            }
        ]
        self.assertTrue(ReferenceIndex(sample).check({"contact_id": "history_id"}, schema))
        sample["text"] = "Gửi cho contact_id=literal_id"
        self.assertTrue(ReferenceIndex(sample).check({"contact_id": "literal_id"}, schema))

    def test_K03_enum(self):
        with self.assertRaises(Rejected):
            check_value("taxi", {"type": "string", "enum": ["bike", "car4"]})

    def test_K04_K38_integer_types_and_range(self):
        for value in (True, "500000", 500000.0, 0, -1):
            with self.subTest(value=value), self.assertRaises(Rejected):
                check_value(value, {"type": "integer", "minimum": 1})
        check_value(500000, {"type": "integer", "minimum": 1})

    def test_K05_x_one_of(self):
        schema = {
            "type": "object",
            "properties": {"id": {"type": "string"}, "phone": {"type": "string"}},
            "x-one-of": [["id"], ["phone"]],
        }
        check_value({"phone": "0900000000"}, schema)
        with self.assertRaises(Rejected):
            check_value({}, schema)

    def test_K07_nested_required(self):
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"item_id": {"type": "string"}, "quantity": {"type": "integer"}},
                "required": ["item_id", "quantity"],
            },
        }
        with self.assertRaises(Rejected):
            check_value([{}], schema)

    def test_K08_extra_fields_rejected(self):
        with self.assertRaises(Rejected):
            check_value({"invented": 1}, {"type": "object", "properties": {}})

    def test_K25_missing_ask_shape(self):
        with self.assertRaises(Rejected):
            parse_decision({"kind": "ASK", "arguments": {"params": ["contact_id"]}})

    def test_K37_missing_vehicle(self):
        with self.assertRaises(Rejected):
            check_value(
                {"pickup": "home", "dropoff": "work"},
                {
                    "type": "object",
                    "properties": {k: {"type": "string"} for k in ("pickup", "dropoff", "vehicle")},
                    "required": ["pickup", "dropoff", "vehicle"],
                },
            )

    def test_sdk_final_permission_guard(self):
        env = FakeEnv()
        env.validate = lambda *args: {"ok": False, "error": "not permitted"}
        with self.assertRaises(Rejected):
            checked_call(decision(contact_id="c1", content="hi"), CATALOG, env)
        self.assertEqual(env.calls, [])

    def test_parse_single_strict_object(self):
        for raw in (
            "[]",
            "{}",
            '{"kind":"DONE","extra":1}',
            '{"kind":"DONE","kind":"CALL"}',
            '{"kind":"DONE"}\n{"kind":"DONE"}',
            '{"kind":"CALL","tool_name":"x","arguments":{"n":NaN}}',
        ):
            with self.subTest(raw=raw), self.assertRaises(Rejected):
                parse_decision(raw)

    def test_noop_and_unknown_are_not_write_success(self):
        self.assertEqual(classify("write", {"ok": True, "done": False}), "BUSINESS_NOOP")
        self.assertEqual(classify("write", {"ok": True}), "UNKNOWN")
        self.assertEqual(classify("write", {"ok": True, "item": {"id": "1"}}), "WRITE_EFFECT")

    def test_tool_specific_success_without_done(self):
        self.assertEqual(
            classify("write", {"ok": True, "message": {"id": "m1"}}, "sms.send"), "WRITE_EFFECT"
        )
        self.assertEqual(
            classify("write", {"ok": True, "message": "uncertain"}, "sms.send"), "UNKNOWN"
        )
        self.assertEqual(classify("write", {"ok": True}, "alarm.delete"), "WRITE_EFFECT")
        self.assertEqual(classify("write", {"ok": True}, "unknown.delete"), "UNKNOWN")
        self.assertEqual(
            classify("write", {"ok": True, "done": False, "message": {"id": "m1"}}, "sms.send"),
            "BUSINESS_NOOP",
        )


class EvaluatorTests(unittest.TestCase):
    def evaluate_one(self, p, g, same_hash=True):
        row = {"id": "x", "label": {"tool_calls": g}}
        prediction = {"id": "x", "tool_calls": p, "state_hash": "a" * 64}
        refs = [{"id": "x", "pass": True, "state_hash": ("a" if same_hash else "b") * 64}]
        return evaluate([prediction], [row], refs, CATALOG)["records"][0]

    def test_empty_rule_and_hash_gate(self):
        c = call(contact_id="c1", content="hello")
        self.assertEqual(self.evaluate_one([], [c])["score"], 0)
        self.assertEqual(self.evaluate_one([], [], False)["score"], 1)
        self.assertEqual(self.evaluate_one([c], [c], False)["score"], 0)

    def test_duplicate_multiplicity(self):
        c = call(contact_id="c1", content="hello")
        self.assertEqual(matched_calls([c, c], [c], CATALOG), 1)
        self.assertAlmostEqual(self.evaluate_one([c, c], [c])["score"], 2 / 3)

    def test_K48_extra_read_penalty(self):
        c, read = call(contact_id="c1", content="hello"), call("contacts.search", name="Minh")
        self.assertAlmostEqual(self.evaluate_one([read, c], [c])["score"], 2 / 3)

    def test_K45_K46_hash_not_text_equality(self):
        a, b = call(contact_id="c1", content="hello"), call(contact_id="c1", content="unrelated")
        result = self.evaluate_one([a], [b])
        self.assertTrue(result["hash_match"])
        self.assertEqual(result["score"], 0)

    def test_fuzzy_strict_boundary(self):
        self.assertEqual(token_f1("a b c", "a b d"), 2 / 3)
        self.assertFalse(
            call_matches(
                call(contact_id="c1", content="a b c"),
                call(contact_id="c1", content="a b d"),
                CATALOG,
                2 / 3,
            )
        )

    def test_maximum_matching_recovers_from_greedy_collision(self):
        predicted = [call(contact_id="c1", content="a b"), call(contact_id="c1", content="a")]
        gold = [call(contact_id="c1", content="a"), call(contact_id="c1", content="b")]
        self.assertEqual(matched_calls(predicted, gold, CATALOG), 2)

    def test_unordered_calls(self):
        a, b = call(contact_id="c1", content="hi"), call(contact_id="c2", content="bye")
        self.assertEqual(matched_calls([b, a], [a, b], CATALOG), 2)

    def test_unknown_optional_argument_mismatch(self):
        self.assertFalse(
            call_matches(
                call(contact_id="c1", content="hi", extra=1),
                call(contact_id="c1", content="hi"),
                CATALOG,
            )
        )


class DataTests(unittest.TestCase):
    def test_unzip_wrapper_root_resolves_unambiguously(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            catalog = base / "wrapper" / "train" / "train_tools_catalog.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_text('{"apps":[]}', encoding="utf-8")
            self.assertEqual(resolve_data_root(base), base / "wrapper")
            self.assertEqual(resolve_data_root(base / "wrapper"), base / "wrapper")
            other = base / "second" / "train" / "train_tools_catalog.json"
            other.parent.mkdir(parents=True)
            other.write_text('{"apps":[]}', encoding="utf-8")
            with self.assertRaises(ValueError):
                resolve_data_root(base)

    def test_K53_missing_duplicate_rows(self):
        row = {"id": "x", "tool_calls": [], "state_hash": "a" * 64}
        for predictions, expected in (
            ([], ["x"]),
            ([row, row], ["x"]),
            ([row], ["y"]),
            ([{**row, "state_hash": "fake"}], ["x"]),
        ):
            with self.subTest(predictions=predictions), self.assertRaises(ValueError):
                validate_submission(predictions, expected)

    def test_jsonl_duplicate_and_malformed_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "rows.jsonl"
            for content in ('{"id":"x"}\n{"id":"x"}', "{broken}", '{"id":2}'):
                p.write_text(content, encoding="utf-8")
                with self.assertRaises(ValueError):
                    read_jsonl(p)

    def test_roundtrip_submission(self):
        with tempfile.TemporaryDirectory() as directory:
            row = {
                "id": "x",
                "tool_calls": [call(contact_id="c1", content="tôi đến muộn")],
                "state_hash": "a" * 64,
            }
            p = Path(directory) / "submission.jsonl"
            write_submission([row], ["x"], p)
            self.assertEqual(read_jsonl(p), [row])

    def test_K13_missing_catalog_does_not_fall_back(self):
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(FileNotFoundError):
            load_catalog(directory, "public_test")

    def test_registry_intersection(self):
        sample = copy.deepcopy(SAMPLE)
        sample["context"]["installed_apps"] = {
            "sms": {"tools": ["sms.send", "contacts.search", "fake.tool"]}
        }
        with self.assertRaises(ValueError):
            allowed_tools(sample, CATALOG)
        sample["context"]["installed_apps"] = {"sms": {"tools": ["sms.send"]}}
        self.assertEqual(set(allowed_tools(sample, CATALOG)), {"sms.send", "sys.ask_missing_info"})

    def test_frozen_partition_and_leave_app_out(self):
        rows = [
            {"id": str(i), "context": {"installed_apps": {"banking": {}} if i < 3 else {}}}
            for i in range(10)
        ]
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "train.jsonl"
            p.write_text("synthetic fingerprint input", encoding="utf-8")
            a = frozen_split(rows, p, heldout_app="banking")
            b = frozen_split(list(reversed(rows)), p, heldout_app="banking")
        self.assertEqual(a, b)
        self.assertFalse(set(a["fit_ids"]) & set(a["validation_ids"]))
        self.assertEqual(len(a["fit_ids"]) + len(a["validation_ids"]), 10)
        self.assertEqual(a["leave_app_out"]["validation_ids"], ["0", "1", "2"])


if __name__ == "__main__":
    unittest.main()
