import json
import unittest

from test_goals import goal
from test_runtime import CATALOG, SAMPLE, FakeEnv, ScriptedPolicy, decision

from lifemate.agent_loop import infer


class Policy(ScriptedPolicy):
    def __init__(self, actions, goals):
        super().__init__(actions)
        self.goals = goals

    def plan(self, request_context, *, deadline):
        return {"goals": self.goals}

    def bind(self, request_context, *, deadline):
        return request_context["candidates"][0]["occurrence"]


class LoopTests(unittest.TestCase):
    def run_loop(self, actions, goals, results=(), **kwargs):
        env = FakeEnv(results)
        opened = []

        def factory(*a):
            opened.append(a)
            return env

        p, d = infer(
            SAMPLE, ".", "train", CATALOG, Policy(actions, goals), env_factory=factory, **kwargs
        )
        self.assertEqual(len(opened), 1)
        self.assertEqual(p["tool_calls"], env.calls)
        return p, d, env

    def test_premature_done_reconsideration_keeps_goal(self):
        p, d, e = self.run_loop(
            [{"kind": "DONE"}, decision(contact_id="c1", content="hello"), {"kind": "DONE"}],
            [goal()],
        )
        self.assertEqual(len(e.calls), 1)
        self.assertEqual(d["stop_reason"], "DONE")
        self.assertEqual(d["goals"][0]["occurrences"][0]["status"], "COMPLETE")

    def test_repeated_done_stops_truthfully_pending(self):
        p, d, e = self.run_loop([{"kind": "DONE"}] * 3, [goal()])
        self.assertEqual(e.calls, [])
        self.assertEqual(d["stop_reason"], "PREMATURE_DONE")
        self.assertEqual(len(d["steps"]), 2)

    def test_no_goals_cannot_write_and_no_fabricated_reference(self):
        for goals, args in (
            ([], {"contact_id": "c1", "content": "hello"}),
            ([goal()], {"contact_id": "made_up", "content": "hello"}),
        ):
            p, d, e = self.run_loop([decision(**args)] * 2, goals)
            self.assertEqual(e.calls, [])

    def test_two_goals_independent_success_then_ask(self):
        p, d, e = self.run_loop(
            [
                decision(contact_id="c1", content="one"),
                {"kind": "ASK", "tool_name": "sms.send", "arguments": {"params": ["content"]}},
            ],
            [goal(), goal("h", span=(8, 12), arguments={"content": "two"})],
        )
        self.assertEqual([c["name"] for c in e.calls], ["sms.send", "sys.ask_missing_info"])
        self.assertEqual(d["stop_reason"], "ASK")

    def test_explicit_repeats_can_execute_twice_success_not_three(self):
        g = goal()
        g["occurrences"].append({"id": "g-2", "span": [9, 13]})
        p, d, e = self.run_loop([decision(contact_id="c1", content="same")] * 3, [g])
        self.assertEqual(len(e.calls), 2)

    def test_injected_clock_late_proposal_has_no_call(self):
        class Clock:
            value = 0.0

            def monotonic(self):
                return self.value

        clock = Clock()

        class Late(Policy):
            def next_action(self, *a, **kw):
                clock.value = 100.0
                return decision(contact_id="c1", content="late")

        e = FakeEnv()
        p, d = infer(
            SAMPLE, ".", "train", CATALOG, Late([], [goal()]), env_factory=lambda *_: e, clock=clock
        )
        self.assertEqual(e.calls, [])
        self.assertEqual(d["stop_reason"], "TIMEOUT")

    def test_factory_and_getter_failure_fatal(self):
        def fail(*a):
            raise RuntimeError("SDK init")

        with self.assertRaises(RuntimeError):
            infer(SAMPLE, ".", "train", CATALOG, Policy([], []), env_factory=fail)
        e = FakeEnv()
        e.get_state_hash = lambda: (_ for _ in ()).throw(RuntimeError("getter"))
        with self.assertRaises(RuntimeError):
            infer(SAMPLE, ".", "train", CATALOG, Policy([], []), env_factory=lambda *_: e)

    def test_fatal_error_keeps_actual_trace_diagnostic(self):
        class Broken(Policy):
            def next_action(self, *a, **kw):
                if not e.calls:
                    return decision(contact_id="c1", content="hello")
                raise RuntimeError("token=secret")

        e = FakeEnv()
        with self.assertRaises(RuntimeError) as raised:
            infer(SAMPLE, ".", "train", CATALOG, Broken([], [goal()]), env_factory=lambda *_: e)
        self.assertEqual(raised.exception.diagnostic["tool_calls"], e.calls)
        self.assertNotIn("secret", json.dumps(raised.exception.diagnostic))

    def test_conditional_write_only_after_observed_true(self):
        for rain in (False, True):
            g = goal(
                condition={
                    "tool_name": "contacts.search",
                    "field": "rain",
                    "operator": "eq",
                    "value": True,
                }
            )
            actions = [
                decision("contacts.search", name="weather"),
                decision(contact_id="c1", content="rain"),
                {"kind": "DONE"},
            ]
            p, d, e = self.run_loop(
                actions, [g], [{"ok": True, "rain": rain}, {"ok": True, "done": True}]
            )
            self.assertEqual(sum(c["name"] == "sms.send" for c in e.calls), int(rain))
            if not rain:
                self.assertEqual(d["goals"][0]["occurrences"][0]["status"], "CANCELED")

    def test_unsupported_withdrawn_plan_real_empty_hash(self):
        p, d, e = self.run_loop([{"kind": "DONE"}], [])
        self.assertEqual(p["tool_calls"], [])
        self.assertEqual(p["state_hash"], e.get_state_hash())
        self.assertEqual(d["stop_reason"], "DONE")

    def test_K33_ambiguous_read_then_terminal_ask(self):
        p, d, e = self.run_loop(
            [
                decision("contacts.search", name="mother"),
                {"kind": "ASK", "tool_name": "sms.send", "arguments": {"params": ["contact_id"]}},
            ],
            [goal()],
            [
                {
                    "ok": True,
                    "contacts": [{"id": "a", "name": "mother"}, {"id": "b", "name": "mother"}],
                },
                {"ok": True, "waiting_for_user": True},
            ],
        )
        self.assertEqual([c["name"] for c in e.calls], ["contacts.search", "sys.ask_missing_info"])
        self.assertEqual(d["stop_reason"], "ASK")
