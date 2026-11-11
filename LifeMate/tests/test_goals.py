import unittest

from test_runtime import CATALOG

from lifemate.runtime.goals import Ledger
from lifemate.validator import Rejected


def goal(identifier="g", tool="sms.send", span=(0, 4), **kw):
    return {
        "id": identifier,
        "intent": "requested effect",
        "tool_name": tool,
        "occurrences": [{"id": identifier + "-1", "span": list(span)}],
        **kw,
    }


def observation(name, result, outcome="READ_OBSERVATION", arguments=None):
    return {"name": name, "arguments": arguments or {}, "result": result, "outcome": outcome}


class GoalTests(unittest.TestCase):
    def ledger(self, goals):
        return Ledger({"goals": goals}, "send and send again", CATALOG)

    def test_invalid_spans_dependencies_cycles_and_claimed_effect(self):
        variants = [
            [goal(span=(0, 100))],
            [goal(dependencies=["absent"])],
            [goal(dependencies=["h"]), goal("h", span=(5, 9), dependencies=["g"])],
            [goal(occurrences=[{"id": "o", "span": [0, 2], "status": "COMPLETE"}])],
            [goal(), goal("g")],
        ]
        for goals in variants:
            with self.subTest(goals=goals), self.assertRaises(ValueError):
                self.ledger(goals)

    def test_K30_completed_write_not_repeated(self):
        ledger = self.ledger([goal()])
        g, o = ledger.bind("sms.send", {}, [])
        ledger.record(g, o, "WRITE_EFFECT", {}, 0)
        with self.assertRaises(Rejected):
            ledger.bind("sms.send", {}, [])
        self.assertEqual(o.observation_ids, [0])

    def test_K31_deliberate_identical_occurrences_and_ambiguous_binding(self):
        g = goal()
        g["occurrences"].append({"id": "g-2", "span": [9, 13]})
        ledger = self.ledger([g])
        with self.assertRaises(Rejected):
            ledger.bind("sms.send", {}, [])
        first = ledger.bind("sms.send", {}, [], "g-1")
        ledger.record(*first, "WRITE_EFFECT", {}, 0)
        second = ledger.bind("sms.send", {}, [], "g-2")
        ledger.record(*second, "WRITE_EFFECT", {}, 1)
        self.assertEqual(ledger.pending([]), [])

    def test_K29_dependency_not_completed_by_unrelated_read(self):
        ledger = self.ledger([goal(), goal("h", span=(9, 13), dependencies=["g"])])
        self.assertEqual([g.id for g, o in ledger.candidates("sms.send", {}, [])], ["g"])

    def test_K34_condition_requires_actual_typed_observation(self):
        catalog = {**CATALOG, "weather.read": {"name": "weather.read", "kind": "read"}}
        ledger = Ledger(
            {
                "goals": [
                    goal(
                        condition={
                            "tool_name": "weather.read",
                            "field": "rain",
                            "operator": "eq",
                            "value": True,
                        }
                    )
                ]
            },
            "send",
            catalog,
        )
        g = ledger.goals[0]
        self.assertIsNone(ledger.condition(g, []))
        self.assertIsNone(ledger.condition(g, [observation("weather.read", {"rain": 1})]))
        self.assertFalse(ledger.condition(g, [observation("weather.read", {"rain": False})]))
        self.assertTrue(ledger.condition(g, [observation("weather.read", {"rain": True})]))
        self.assertEqual(ledger.pending([observation("weather.read", {"rain": False})]), [])

    def test_unknown_outcome_quarantines(self):
        ledger = self.ledger([goal()])
        bound = ledger.bind("sms.send", {}, [])
        ledger.record(*bound, "UNKNOWN", {}, 0)
        with self.assertRaises(Rejected):
            ledger.bind("sms.send", {}, [])
        self.assertEqual(bound[1].status, "QUARANTINED")

    def test_cause_linked_bank_recovery_and_unrelated_read_negative(self):
        catalog = {"banking.transfer": {"kind": "write"}, "banking.get_balance": {"kind": "read"}}
        ledger = Ledger({"goals": [goal(tool="banking.transfer")]}, "send", catalog)
        args = {"from_account_id": "old", "beneficiary_id": "ben", "amount": 100}
        new = {**args, "from_account_id": "new"}
        noop = observation(
            "banking.transfer",
            {"ok": True, "done": False, "message": "số dư không đủ"},
            "BUSINESS_NOOP",
            args,
        )
        bound = ledger.bind("banking.transfer", args, [])
        ledger.record(*bound, "BUSINESS_NOOP", args, 0)
        for read in (
            observation("contacts.search", {"contacts": [{"id": "new"}]}),
            observation("banking.get_balance", {"accounts": [{"id": "new", "balance": 1}]}),
        ):
            with self.assertRaises(Rejected):
                ledger.bind("banking.transfer", new, [noop, read])
        read = observation("banking.get_balance", {"accounts": [{"id": "new", "balance": 1000}]})
        recovered = ledger.bind("banking.transfer", new, [noop, read])
        self.assertIs(recovered[1], bound[1])
        with self.assertRaises(Rejected):
            ledger.bind("banking.transfer", {**new, "amount": 1}, [noop, read])
