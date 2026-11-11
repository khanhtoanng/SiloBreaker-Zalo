import unittest

from test_runtime import CATALOG, FakeEnv

from lifemate.validator import Rejected, check_value, checked_call, parse_decision


class ValidationTests(unittest.TestCase):
    def test_nested_optional_present_wrong_types(self):
        for value in (None, False, 1.0, ""):
            if value == "":
                continue
            with self.subTest(value=value), self.assertRaises(Rejected):
                check_value(
                    {"n": value}, {"type": "object", "properties": {"n": {"type": "integer"}}}
                )

    def test_formats_arrays_constraints(self):
        for value, schema in (
            ("bad", {"type": "string", "format": "date-time"}),
            ([], {"type": "array", "minItems": 1}),
            ("a", {"type": "string", "minLength": 2}),
            ("abc", {"type": "string", "pattern": "^[0-9]+$"}),
        ):
            with self.subTest(value=value), self.assertRaises(Rejected):
                check_value(value, schema)

    def test_ask_target_and_real_shape(self):
        env = FakeEnv()
        name, args = checked_call(
            parse_decision(
                {"kind": "ASK", "tool_name": "sms.send", "arguments": {"params": ["content"]}}
            ),
            CATALOG,
            env,
        )
        self.assertEqual(name, "sys.ask_missing_info")
        self.assertEqual(args, {"tool_name": "sms.send", "params": ["content"]})
        self.assertEqual(env.calls, [])

    def test_known_date_time_formats_and_boundaries(self):
        for value, fmt in (
            ("2024-02-29", "date"),
            ("7:30", "time"),
            ("23:59:59", "time"),
            ("2026-11-10T10:00", "date-time"),
            ("2026-11-10T10:00:00Z", "date-time"),
        ):
            check_value(value, {"type": "string", "format": fmt})
        for value, fmt in (
            ("2025-02-29", "date"),
            ("20261110", "date"),
            ("24:00", "time"),
            ("12:60", "time"),
            ("12:00:99", "time"),
            ("2026-02-30T10:00", "date-time"),
            ("20261110T100000", "date-time"),
        ):
            with self.subTest(value=value), self.assertRaises(Rejected):
                check_value(value, {"type": "string", "format": fmt})
