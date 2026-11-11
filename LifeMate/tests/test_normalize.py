import unittest

from lifemate.runtime.normalize import normalize, sample_clock

CONTEXT = {"current_time": "2026-12-31T23:50:00+07:00", "timezone": "Asia/Ho_Chi_Minh"}


class NormalizeTests(unittest.TestCase):
    def test_temporal_corrections_preserve_complete_bases_and_explicit_overrides(self):
        context = {"current_time": "2026-11-10T10:00:00+07:00", "timezone": "Asia/Ho_Chi_Minh"}
        cases = (
            ("mai năm giờ à không, năm rưỡi", "2026-11-11T05:30:00+07:00"),
            ("nhắc mai 8 giờ à không, 9 giờ", "2026-11-11T09:00:00+07:00"),
            ("thứ hai tuần sau 5 giờ à không, 6 giờ", "2026-11-16T06:00:00+07:00"),
            ("thứ hai tới 5 giờ à không, 6 giờ", "2026-11-16T06:00:00+07:00"),
            ("mai 8 giờ à không 9 giờ à không, 10 giờ", "2026-11-11T10:00:00+07:00"),
            ("mai 8 giờ, à không, 9 giờ", "2026-11-11T09:00:00+07:00"),
            ("2026-12-31T23:00:00+02:00 à không, 22 giờ", "2026-12-31T22:00:00+02:00"),
            ("2026-12-31 à không, 22 giờ", "2026-12-31T22:00:00+07:00"),
            ("2026-12-31T23:00:00Z à không, 22 giờ", "2026-12-31T22:00:00+00:00"),
            ("nhắc sau 2 giờ à không, 3 giờ", "2026-11-10T13:00:00+07:00"),
            ("nhắc trước 2 giờ à không, 3 giờ", "2026-11-10T07:00:00+07:00"),
            ("sau 20 phút à không, 30 phút", "2026-11-10T10:30:00+07:00"),
            ("trước 2 ngày à không, 3 ngày", "2026-11-07T10:00:00+07:00"),
            ("sau 2 giờ à không, 30 phút à không 40 phút", "2026-11-10T10:40:00+07:00"),
            ("mai 8 giờ tối à không, 9 giờ", "2026-11-11T21:00:00+07:00"),
            ("mai tối 8 giờ à không, 9 giờ", "2026-11-11T21:00:00+07:00"),
            ("mai 12 giờ sáng à không, 1 giờ", "2026-11-11T01:00:00+07:00"),
            ("mai 8 giờ tối à không, 9 giờ sáng à không 10 giờ", "2026-11-11T10:00:00+07:00"),
            ("mai 8 giờ à không, hôm nay 9 giờ", "2026-11-10T09:00:00+07:00"),
            ("mai 8 giờ à không hôm nay 9 giờ", "2026-11-10T09:00:00+07:00"),
            ("mai 8 giờ à không, sau 2 giờ", "2026-11-10T12:00:00+07:00"),
            ("sau 2 giờ à không, trước 3 giờ", "2026-11-10T07:00:00+07:00"),
            ("mai 8 giờ à không, 2026-12-31T22:00:00+02:00", "2026-12-31T22:00:00+02:00"),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                result = normalize(text, context)
                certain = [
                    v["value"]
                    for v in result["values"]
                    if v["kind"] == "time" and not v["superseded"] and not v["uncertain"]
                ]
                self.assertEqual(certain, [expected])
                self.assertFalse(result["uncertainties"])
                self.assertIn(expected, result["effective_text"])
                self.assertEqual(result["raw_text"], text)
                for value in result["values"]:
                    self.assertEqual(text[slice(*value["span"])], value["text"])

    def test_ambiguous_temporal_correction_marks_all_affected_entries_uncertain(self):
        for text in (
            "mai 8 giờ trưa à không, 9 giờ",
            "mai khoảng 8 giờ à không, 9 giờ",
            "mai 8 giờ à không, 9 giờ trưa",
            "mai 8 giờ à không, 9 giờ sáng tối",
            "mai 8 giờ à không, 9 giờ kém hai mươi",
            "mai 8 giờ à không, vài giờ",
            "sau 2 giờ à không, 3 rưỡi",
            "sau 2 giờ à không, 3 giờ tối",
            "mai 8 giờ à không, -3 giờ",
            "thứ hai 8 giờ à không, 9 giờ",
        ):
            with self.subTest(text=text):
                result = normalize(text, CONTEXT)
                self.assertTrue(result["uncertainties"])
                self.assertTrue(
                    all(v["uncertain"] for v in result["values"] if v["kind"] == "time")
                )
                self.assertEqual(result["effective_text"], text)

    def test_temporal_basis_rollover_and_uncertainty_do_not_taint_independent_goals(self):
        text = "Đừng chuyển 500 nghìn và nhắc mai 8 giờ à không, 9 giờ; hôm nay 17 giờ"
        result = normalize(text, CONTEXT)
        active = [v for v in result["values"] if not v["superseded"] and not v["uncertain"]]
        self.assertEqual([v["value"] for v in active if v["kind"] == "amount"], [500000])
        self.assertEqual(
            [v["value"] for v in active if v["kind"] == "time"],
            ["2027-01-01T09:00:00+07:00", "2026-12-31T17:00:00+07:00"],
        )
        self.assertIn("Đừng chuyển 500 nghìn và nhắc", result["effective_text"])
        self.assertEqual(text[slice(*result["negation_spans"][0])], "Đừng")
        ambiguous = normalize("hôm nay 17 giờ và mai 8 giờ trưa à không, 9 giờ", CONTEXT)
        self.assertEqual(
            [v["value"] for v in ambiguous["values"] if v["kind"] == "time" and not v["uncertain"]],
            ["2026-12-31T17:00:00+07:00"],
        )

    def values(self, text, kind):
        return [
            x["value"]
            for x in normalize(text, CONTEXT)["values"]
            if x["kind"] == kind and not x["superseded"]
        ]

    def test_K38_K39_money_no_phone_rewrite(self):
        self.assertEqual(self.values("500 nghìn", "amount"), [500000])
        self.assertEqual(self.values("500", "amount"), [])
        self.assertEqual(self.values("một triệu rưỡi", "amount"), [1500000])
        self.assertEqual(normalize("gửi 0901234567", CONTEXT)["effective_text"], "gửi 0901234567")

    def test_K35_K36_rollover_sample_not_host(self):
        self.assertEqual(self.values("mai 5 giờ rưỡi", "time"), ["2027-01-01T05:30:00+07:00"])
        self.assertEqual(self.values("sau 20 phút", "time"), ["2027-01-01T00:10:00+07:00"])

    def test_K40_correction_and_negation(self):
        result = normalize("năm giờ à không, năm giờ rưỡi", CONTEXT)
        self.assertEqual(
            [x["value"] for x in result["values"] if not x["superseded"]],
            ["2026-12-31T05:30:00+07:00"],
        )
        self.assertTrue(normalize("đừng đặt xe", CONTEXT)["negation_spans"])

    def test_half_before_weekday_and_uncertainty(self):
        self.assertEqual(self.values("6 giờ kém mười lăm", "time"), ["2026-12-31T05:45:00+07:00"])
        self.assertTrue(normalize("lát nữa", CONTEXT)["uncertainties"])
        self.assertTrue(normalize("mai 5 giờ", {})["uncertainties"])

    def test_inconsistent_clock(self):
        with self.assertRaises(ValueError):
            sample_clock(
                {"current_time": "2026-11-10T10:00:00+00:00", "timezone": "Asia/Ho_Chi_Minh"}
            )

    def test_words_without_half_next_calendar_week_and_source_spans(self):
        self.assertEqual(self.values("một triệu", "amount"), [1000000])
        context = {"current_time": "2026-11-13T10:00:00+07:00", "timezone": "Asia/Ho_Chi_Minh"}
        value = normalize("thứ hai tuần sau 5 giờ", context)["values"][0]["value"]
        self.assertEqual(value, "2026-11-16T05:00:00+07:00")
        text = "đặt xe à không, đừng đặt xe"
        result = normalize(text, CONTEXT)
        self.assertEqual(
            text[result["negation_spans"][0][0] : result["negation_spans"][0][1]], "đừng"
        )
        self.assertEqual(
            self.values("năm giờ à không, năm rưỡi", "time"), ["2026-12-31T05:30:00+07:00"]
        )

    def test_evening_and_relative_hours_do_not_emit_spurious_absolute_time(self):
        self.assertEqual(self.values("mai 7 giờ tối", "time"), ["2027-01-01T19:00:00+07:00"])
        self.assertEqual(self.values("sau 2 giờ", "time"), ["2027-01-01T01:50:00+07:00"])

    def test_complete_number_words_numeric_boundaries_and_unsupported_signs(self):
        for text, expected in (
            ("mười ba triệu", [13000000]),
            ("hai mươi lăm nghìn", [25000]),
            ("500nghìn", [500000]),
        ):
            with self.subTest(text=text):
                self.assertEqual(self.values(text, "amount"), expected)
        for text in ("abcba triệu", "x500 nghìn", "ba triệuđồng", "1e3 triệu", "090500nghìnx"):
            with self.subTest(text=text):
                self.assertEqual(self.values(text, "amount"), [])
        for text in (
            "-500 nghìn",
            "+500 nghìn",
            "−500 nghìn",
            "- 500 nghìn",
            "- ba triệu",
            "1 000 nghìn",
            "mười 3 triệu",
            "1.000.000 triệu",
            "một trăm ba triệu",
            "1 triệu 500 nghìn",
            "9" * 400 + " tỷ",
        ):
            with self.subTest(text=text):
                self.assertEqual(self.values(text, "amount"), [])
                self.assertTrue(normalize(text, CONTEXT)["uncertainties"])
        self.assertEqual(self.values("mười ba giờ", "time"), ["2026-12-31T13:00:00+07:00"])
        self.assertEqual(self.values("hai mươi lăm giờ", "time"), [])
        self.assertEqual(self.values("x5 giờ", "time"), [])

    def test_day_qualifiers_are_local_and_conflicts_are_uncertain(self):
        text = "nhắc hôm nay 17 giờ và mai 8 giờ; thứ hai tuần sau 9 giờ"
        self.assertEqual(
            self.values(text, "time"),
            ["2026-12-31T17:00:00+07:00", "2027-01-01T08:00:00+07:00", "2027-01-04T09:00:00+07:00"],
        )
        self.assertEqual(self.values("gọi Mai Anh 8 giờ", "time"), [])
        self.assertTrue(normalize("gọi Mai Anh 8 giờ", CONTEXT)["uncertainties"])
        self.assertEqual(self.values("email 8 giờ", "time"), ["2026-12-31T08:00:00+07:00"])
        conflict = normalize("hôm nay mai 8 giờ", CONTEXT)
        self.assertFalse(conflict["values"])
        self.assertTrue(conflict["uncertainties"])

    def test_local_correction_preserves_independent_amount_goal_and_raw_spans(self):
        text = "Đừng chuyển 500 nghìn và đặt xe năm giờ à không, năm rưỡi"
        result = normalize(text, CONTEXT)
        self.assertEqual(
            [v["value"] for v in result["values"] if v["kind"] == "amount" and not v["superseded"]],
            [500000],
        )
        self.assertEqual(
            [v["value"] for v in result["values"] if v["kind"] == "time" and not v["superseded"]],
            ["2026-12-31T05:30:00+07:00"],
        )
        self.assertIn("Đừng chuyển 500 nghìn và đặt xe", result["effective_text"])
        self.assertEqual(result["raw_text"], text)
        self.assertEqual(text[slice(*result["negation_spans"][0])], "Đừng")
        for value in result["values"]:
            self.assertEqual(text[slice(*value["span"])], value["text"])
        ambiguous = normalize("500 nghìn và đặt xe à không, gửi 600 nghìn", CONTEXT)
        self.assertTrue(ambiguous["uncertainties"])
        self.assertTrue(all(not v["superseded"] for v in ambiguous["values"]))
        unresolved = normalize("500 nghìn à không -600 nghìn", CONTEXT)
        self.assertTrue(unresolved["values"][0]["uncertain"])
        self.assertTrue(unresolved["uncertainties"])
        self.assertEqual(
            self.values("năm giờ à không năm rưỡi", "time"), ["2026-12-31T05:30:00+07:00"]
        )
