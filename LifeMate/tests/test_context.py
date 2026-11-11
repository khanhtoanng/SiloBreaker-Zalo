import copy
import json
import unittest

from test_runtime import CATALOG, SAMPLE, FakeEnv

from lifemate.runtime.context import compile_messages
from lifemate.runtime.loop import infer


class ContextTests(unittest.TestCase):
    def test_actual_infer_planner_and_action_share_corrected_temporal_basis(self):
        class Capture:
            def plan(self, request_context, *, deadline):
                self.request = request_context
                return {"goals": []}

            def next_action(self, messages, *, deadline):
                self.action = json.loads(messages[1]["content"])
                return {"kind": "DONE"}

        for text, expected in (
            ("mai năm giờ à không, năm rưỡi", ["2026-11-11T05:30:00+07:00"]),
            ("sau 2 giờ à không, 3 giờ", ["2026-11-10T13:00:00+07:00"]),
            ("mai 8 giờ tối à không, 9 giờ", ["2026-11-11T21:00:00+07:00"]),
            ("mai 8 giờ trưa à không, 9 giờ", []),
        ):
            with self.subTest(text=text):
                sample = copy.deepcopy(SAMPLE)
                sample["text"] = "chuyển 500 nghìn và " + text
                sample["context"].update(
                    current_time="2026-11-10T10:00:00+07:00", timezone="Asia/Ho_Chi_Minh"
                )
                policy, env = Capture(), FakeEnv()
                prediction, diagnostic = infer(
                    sample, ".", "train", CATALOG, policy, env_factory=lambda *_, fixture=env: fixture
                )
                self.assertEqual(prediction["tool_calls"], [])
                self.assertEqual(env.calls, [])
                self.assertEqual(diagnostic["stop_reason"], "DONE")
                normalized = policy.request["normalization"]
                self.assertEqual(normalized, policy.action["normalization"])
                self.assertEqual(normalized["raw_text"], sample["text"])
                self.assertEqual(
                    [
                        v["value"]
                        for v in normalized["values"]
                        if v["kind"] == "time" and not v["superseded"] and not v["uncertain"]
                    ],
                    expected,
                )
                self.assertEqual(
                    [
                        v["value"]
                        for v in normalized["values"]
                        if v["kind"] == "amount" and not v["uncertain"]
                    ],
                    [500000],
                )
                self.assertEqual(bool(normalized["uncertainties"]), not bool(expected))

    def test_full_context_and_schema_extensions(self):
        messages = compile_messages(SAMPLE, CATALOG, [{"result": {"id": "history"}}])
        payload = json.loads(messages[1]["content"])
        self.assertEqual(payload["context"], SAMPLE["context"])
        self.assertEqual(len(payload["installed_tools"]), len(CATALOG))
        self.assertIn("x-ref", messages[1]["content"])
        self.assertIn("history", messages[1]["content"])

    def test_explicit_overflow(self):
        with self.assertRaisesRegex(ValueError, "CONTEXT_OVERFLOW"):
            compile_messages(SAMPLE, CATALOG, [], max_characters=1)
