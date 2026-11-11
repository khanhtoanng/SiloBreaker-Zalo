import unittest

from lifemate.metrics.asr import critical, distance, evaluate_asr


class AsrMetricTests(unittest.TestCase):
    def test_temporal_basis_corrections_match_final_equivalents_and_uncertain_slots_are_empty(self):
        context = {"current_time": "2026-11-10T10:00:00+07:00", "timezone": "Asia/Ho_Chi_Minh"}
        pairs = (
            ("mai năm giờ à không, năm rưỡi", "mai năm rưỡi"),
            ("thứ hai tuần sau 5 giờ à không 6 giờ", "thứ hai tuần sau 6 giờ"),
            ("sau 2 giờ à không, 3 giờ", "sau 3 giờ"),
            ("mai 8 giờ tối à không, 9 giờ", "mai 9 giờ tối"),
            ("2026-12-31T23:00:00+02:00 à không 22 giờ", "2026-12-31T22:00:00+02:00"),
            ("mai 8 giờ à không, hôm nay 9 giờ", "hôm nay 9 giờ"),
        )
        for corrected, final in pairs:
            with self.subTest(text=corrected):
                reference = {
                    "identity": {"policy": "same"},
                    "records": [{"id": "x", "context": context, "text": corrected}],
                }
                candidate = {
                    "identity": reference["identity"],
                    "records": [{"id": "x", "context": context, "text": final}],
                }
                report = evaluate_asr(reference, candidate)
                self.assertNotIn("time", report["records"][0]["critical_slot_differences"])
                self.assertTrue(critical(corrected, context)["time"])
        ambiguous = "mai 8 giờ trưa à không, 9 giờ"
        self.assertEqual(critical(ambiguous, context)["time"], [])
        self.assertTrue(critical(ambiguous, context)["uncertainty"])

    def test_complete_quantities_and_local_scope_reach_critical_slot_metrics(self):
        context = {"current_time": "2026-11-10T10:00:00+07:00"}
        before = critical("chuyển mười ba triệu và đặt xe năm giờ à không, năm rưỡi", context)
        self.assertEqual(before["amount"], [13000000])
        self.assertEqual(before["time"], ["2026-11-10T05:30:00+07:00"])
        self.assertEqual(critical("-500 nghìn", context)["amount"], [])
        self.assertTrue(critical("-500 nghìn", context)["uncertainty"])
        reference = {
            "identity": {"policy": "same"},
            "records": [{"id": "x", "context": context, "text": "chuyển mười ba triệu"}],
        }
        candidate = {
            **reference,
            "records": [{"id": "x", "context": context, "text": "chuyển ba triệu"}],
        }
        difference = evaluate_asr(reference, candidate)["records"][0]["critical_slot_differences"]
        self.assertEqual(difference["amount"], {"reference": [13000000], "candidate": [3000000]})
        self.assertEqual(
            critical("hôm nay 17 giờ và mai 8 giờ", context)["time"],
            ["2026-11-10T17:00:00+07:00", "2026-11-11T08:00:00+07:00"],
        )

    def test_empty_denominators_and_insertions(self):
        a = {"identity": {"policy": "same"}, "records": [{"id": "x", "text": ""}]}
        b = {**a, "records": [{"id": "x", "text": "extra"}]}
        r = evaluate_asr(a, b)
        self.assertIsNone(r["wer"])
        self.assertEqual(r["word_errors"], 1)
        self.assertEqual(distance("abc", "adc"), 1)

    def test_same_ids_config_critical_slots_and_downstream_delta(self):
        a = {
            "identity": {"policy": "same"},
            "records": [{"id": "x", "text": "gửi 500 nghìn 0901234567", "score": 1.0}],
        }
        b = {**a, "records": [{"id": "x", "text": "đừng gửi 50 nghìn 0901234568", "score": 0.0}]}
        a["records"][0].update(
            call_f1=1.0, hash_match=True, tool_calls=[], state_hash="a" * 64, elapsed_seconds=1.0
        )
        b["records"][0].update(
            call_f1=0.5,
            hash_match=False,
            tool_calls=[{"name": "x"}],
            state_hash="b" * 64,
            elapsed_seconds=2.0,
        )
        r = evaluate_asr(a, b)
        self.assertEqual(r["records"][0]["call_f1_delta"], -0.5)
        self.assertEqual(r["records"][0]["hash_match_delta"], -1)
        self.assertTrue(r["records"][0]["calls_changed"])
        self.assertTrue(r["records"][0]["state_hash_changed"])
        self.assertEqual(r["records"][0]["timing_delta"], 1.0)
        self.assertIn("amount", r["records"][0]["critical_slot_differences"])
        self.assertIn("negation", r["records"][0]["critical_slot_differences"])
        self.assertEqual(r["records"][0]["downstream_delta"], -1.0)
        with self.assertRaises(ValueError):
            evaluate_asr(a, {**b, "identity": {"policy": "different"}})
        with self.assertRaises(ValueError):
            evaluate_asr(a, {**b, "records": []})
