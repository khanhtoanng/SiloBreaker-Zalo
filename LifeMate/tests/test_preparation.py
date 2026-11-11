import json
import unittest

from test_runtime import CATALOG, SAMPLE, FakeEnv, call

from lifemate.data.replay import replay_gold
from lifemate.learning.trajectories import expand_train


class PreparationTests(unittest.TestCase):
    def fixture(self):
        a = {
            **SAMPLE,
            "id": "a",
            "audio_text": "send",
            "label": {
                "tool_calls": [
                    call("contacts.search", name="Minh"),
                    call(contact_id="c1", content="hello"),
                ],
                "tool_results": [
                    {"ok": True, "contacts": [{"id": "c1"}]},
                    {"ok": True, "done": True},
                ],
                "final_state": {},
            },
        }
        b = {
            **SAMPLE,
            "id": "b",
            "audio_text": "nothing",
            "label": {"tool_calls": [], "tool_results": [], "final_state": {}},
        }
        config = {
            "source_split": "train",
            "seed": 1,
            "dataset_sha256": "a" * 64,
            "fit_ids": ["a"],
            "validation_ids": ["b"],
        }
        return [a, b], config

    def test_teacher_forcing_prefix_no_future_and_terminal_empty(self):
        rows, fold = self.fixture()
        envs = []

        def factory(root, split, sid):
            env = FakeEnv(rows[0]["label"]["tool_results"] if sid == "a" else [])
            envs.append(env)
            return env

        expanded = list(expand_train(rows, ".", CATALOG, fold, env_factory=factory))
        self.assertEqual(len(expanded), 4)
        self.assertEqual(len(envs), 2)
        self.assertEqual([r["target"]["kind"] for r in expanded], ["CALL", "CALL", "DONE", "DONE"])
        self.assertEqual(
            [len(json.loads(r["messages"][1]["content"])["observations"]) for r in expanded],
            [0, 1, 2, 0],
        )
        self.assertNotIn('"label"', expanded[0]["messages"][1]["content"])

    def test_drift_and_length_alignment_rejected(self):
        rows, fold = self.fixture()
        with self.assertRaisesRegex(ValueError, "Replay result drift"):
            list(expand_train(rows, ".", CATALOG, fold, env_factory=lambda *_: FakeEnv()))
        rows[0]["label"]["tool_results"] = []
        with self.assertRaises(ValueError):
            list(expand_train(rows, ".", CATALOG, fold, env_factory=lambda *_: FakeEnv()))

    def test_ask_gets_terminal_training_done(self):
        rows, fold = self.fixture()
        rows[0]["label"] = {
            "tool_calls": [
                {
                    "name": "sys.ask_missing_info",
                    "arguments": {"tool_name": "sms.send", "params": ["content"]},
                }
            ],
            "tool_results": [{"ok": True, "waiting_for_user": True}],
        }
        expanded = list(
            expand_train(
                rows,
                ".",
                CATALOG,
                fold,
                env_factory=lambda *_: FakeEnv(rows[0]["label"]["tool_results"]),
            )
        )
        self.assertEqual([r["target"]["kind"] for r in expanded], ["ASK", "DONE", "DONE"])

    def test_train_replay_raw_states_transient_no_report_leak(self):
        rows, fold = self.fixture()

        class Replay(FakeEnv):
            def get_state(self):
                return {"private": {"secret": "raw-state"}}

        report = replay_gold(
            rows,
            ".",
            env_factory=lambda r, s, sid: Replay(
                rows[0]["label"]["tool_results"] if sid == "a" else []
            ),
        )
        self.assertTrue(all(r["pass"] for r in report["records"]))
        self.assertNotIn("raw-state", json.dumps(report))
