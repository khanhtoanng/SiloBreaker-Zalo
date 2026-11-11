import unittest

from test_runtime import CATALOG, call

from lifemate.evaluation import evaluate
from lifemate.metrics.reports import compare, enrich


class ReportTests(unittest.TestCase):
    def test_reports_pairing_and_later_actions(self):
        calls = [call(contact_id="c1", content="hello"), call("contacts.search", name="Minh")]
        rows = [{"id": "x", "label": {"tool_calls": calls}}]
        pred = [{"id": "x", "tool_calls": calls, "state_hash": "a" * 64}]
        refs = [{"id": "x", "pass": True, "state_hash": "a" * 64}]
        report = enrich(evaluate(pred, rows, refs, CATALOG), rows, identity={"frozen": "one"})
        self.assertEqual(report["later_action_rate"], 1.0)
        self.assertEqual(compare(report, report)["n_tied"], 1)
        other = {**report, "identity": {"frozen": "two"}}
        with self.assertRaises(ValueError):
            compare(report, other)

    def test_missing_duplicate_reference_never_empty_substitute(self):
        row = {"id": "x", "label": {"tool_calls": []}}
        p = {"id": "x", "tool_calls": [], "state_hash": "a" * 64}
        for refs in ([], [{"id": "x", "pass": False}], [{"id": "x"}, {"id": "x"}]):
            with self.assertRaises(ValueError):
                evaluate([p], [row], refs, CATALOG)
