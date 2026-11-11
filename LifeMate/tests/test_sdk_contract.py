"""Synthetic contracts against the external organizer SDK, with zero raw-state reads.

Set LIFEMATE_DATA_ROOT to use another authorized kit. No SDK is copied into source.
"""

import copy
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lifemate.data_loader import load_catalog
from lifemate.toolenv_adapter import load_sdk
from lifemate.validator import Rejected, check_value, classify

DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "train+public_test" / "train+public_test"
ROOT = Path(os.environ.get("LIFEMATE_DATA_ROOT", DEFAULT_ROOT)).resolve()


@unittest.skipUnless(
    (ROOT / "train" / "zaic_tools" / "__init__.py").is_file(), "External authorized kit unavailable"
)
class SDKContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sdk = load_sdk(ROOT, "train")
        cls.catalog = load_catalog(ROOT, "train")

    def setUp(self):
        self.entry = {
            "_meta": {
                "question_id": "synthetic",
                "current_time": "2026-11-10T16:00:00+07:00",
                "tools": list(self.catalog),
            },
            "smart_home": {
                "devices": [
                    {"id": "light_01", "type": "light", "state": {"power": "off"}},
                    {"id": "fan_01", "type": "fan", "state": {"power": "off"}},
                ]
            },
            "food_delivery": {
                "restaurants": [
                    {"id": "rest_01", "menu": [{"id": "food_01", "name": "cơm", "price": 35000}]}
                ],
                "orders": [],
            },
            "ride_hailing": {"rides": []},
            "sms": {"messages": []},
            "banking": {
                "accounts": [{"id": "acc_01", "balance": 10}],
                "beneficiaries": [{"id": "ben_01"}],
                "transactions": [],
            },
        }
        self.env = self.sdk.Session("synthetic", self.entry, self.catalog)

    def test_K02_validate_does_not_log_or_mutate(self):
        before = self.env.get_state_hash()
        self.assertFalse(self.env.validate("smart_home.light_set", {"power": "on"})["ok"])
        self.assertEqual(self.env.get_tool_calls(), [])
        self.assertEqual(self.env.get_state_hash(), before)

    def test_K06_xref_passes_schema_but_noops(self):
        args = {"device_id": "missing", "power": "on"}
        self.assertTrue(self.env.validate("smart_home.light_set", args)["ok"])
        self.assertEqual(
            classify("write", self.env.call("smart_home.light_set", args)), "BUSINESS_NOOP"
        )

    def test_K07_nested_gap_and_own_preflight(self):
        args = {"restaurant_id": "rest_01", "items": [{}]}
        self.assertTrue(self.env.validate("food_delivery.place_order", args)["ok"])
        with self.assertRaises(Rejected):
            check_value(args, self.catalog["food_delivery.place_order"]["parameters"])

    def test_K09_failed_attempt_is_logged(self):
        before = self.env.get_state_hash()
        result = self.env.call("smart_home.light_set", {"power": "on"})
        self.assertFalse(result["ok"])
        self.assertEqual(len(self.env.get_tool_calls()), 1)
        self.assertEqual(self.env.get_state_hash(), before)

    def test_K18_insufficient_balance(self):
        result = self.env.call(
            "banking.transfer",
            {"from_account_id": "acc_01", "beneficiary_id": "ben_01", "amount": 100},
        )
        self.assertTrue(result["ok"])
        self.assertFalse(result["done"])
        self.assertEqual(classify("write", result), "BUSINESS_NOOP")

    def test_K19_wrong_device_type_noops(self):
        self.assertFalse(
            self.env.call("smart_home.light_set", {"device_id": "fan_01", "power": "on"})["done"]
        )

    def test_K25_ask_required_and_hash(self):
        self.assertFalse(self.env.validate("sys.ask_missing_info", {"tool_name": "sms.send"})["ok"])
        before = self.env.get_state_hash()
        self.assertTrue(
            self.env.call("sys.ask_missing_info", {"tool_name": "sms.send", "params": ["content"]})[
                "waiting_for_user"
            ]
        )
        self.assertEqual(self.env.get_state_hash(), before)
        self.assertEqual(self.env.get_tool_calls()[0]["name"], "sys.ask_missing_info")

    def test_K35_K36_schedule_boundaries(self):
        for timestamp, retained in (
            ("2026-11-10T15:59:00+07:00", False),
            ("2026-11-10T16:00:00+07:00", False),
            ("2026-11-10T16:01:00+07:00", True),
        ):
            with self.subTest(timestamp=timestamp):
                result = self.env.call(
                    "ride_hailing.book",
                    {
                        "pickup": "home",
                        "dropoff": "work",
                        "vehicle": "bike",
                        "schedule_time": timestamp,
                    },
                )
                self.assertEqual("schedule_time" in result["item"], retained)

    def test_K45_K46_freetext_hash_collision(self):
        a = {"sms": {"messages": [{"id": "m1", "content": "alpha", "title": "first"}]}}
        b = {"sms": {"messages": [{"id": "m1", "content": "beta", "title": "other"}]}}
        self.assertEqual(self.sdk.state_hash(a), self.sdk.state_hash(b))

    def test_K47_information_state_ignored_by_hash(self):
        a, b = {"weather": {"value": 1}}, {"weather": {"value": 99}}
        self.assertEqual(self.sdk.state_hash(a), self.sdk.state_hash(b))

    def test_K49_array_order_contract(self):
        self.assertEqual(
            self.sdk.state_hash({"custom": [1, 2]}), self.sdk.state_hash({"custom": [2, 1]})
        )
        self.assertNotEqual(
            self.sdk.state_hash({"custom": [{"id": "1"}, {"id": "2"}]}),
            self.sdk.state_hash({"custom": [{"id": "2"}, {"id": "1"}]}),
        )

    def test_K13_K54_distinct_split_imports_and_full_coverage(self):
        public = load_sdk(ROOT, "public_test")
        public_catalog = load_catalog(ROOT, "public_test")
        self.assertIsNot(public, self.sdk)
        self.assertNotEqual(public.ToolEnv.__module__, self.sdk.ToolEnv.__module__)
        self.assertTrue(set(self.catalog) <= set(self.sdk.TOOLS))
        self.assertTrue(set(public_catalog) <= set(public.TOOLS))
        self.assertIn("translator.translate", public_catalog)
        self.assertNotIn("translator.translate", self.catalog)

    def test_split_specific_canonical_text_keys(self):
        public = load_sdk(ROOT, "public_test")
        a, b = {"custom": {"text": "alpha"}}, {"custom": {"text": "beta"}}
        self.assertNotEqual(self.sdk.state_hash(a), self.sdk.state_hash(b))
        self.assertEqual(public.state_hash(a), public.state_hash(b))
        a, b = {"custom": {"expression": "1+1"}}, {"custom": {"expression": "2+2"}}
        self.assertEqual(self.sdk.state_hash(a), self.sdk.state_hash(b))
        self.assertNotEqual(public.state_hash(a), public.state_hash(b))

    def test_K16_scenes_require_unfiltered_status(self):
        entry = copy.deepcopy(self.entry)
        entry["smart_home"]["scenes"] = [{"id": "scene1", "name": "evening", "actions": []}]
        env = self.sdk.Session("synthetic", entry, self.catalog)
        self.assertIn("scenes", env.call("smart_home.get_status", {}))
        self.assertNotIn("scenes", env.call("smart_home.get_status", {"room": "living"}))

    def test_K21_unique_phone_equivalence_and_ambiguous_preservation(self):
        for duplicated in (False, True):
            entry = copy.deepcopy(self.entry)
            entry["contacts"] = {
                "contacts": [{"id": "c1", "phone": "0901234567"}]
                + ([{"id": "c2", "phone": "0901234567"}] if duplicated else [])
            }
            entry["ewallet"] = {"balance": 1000, "transactions": []}
            env = self.sdk.Session("synthetic", entry, self.catalog)
            result = env.call("ewallet.transfer", {"phone": "+84901234567", "amount": 100})
            self.assertEqual(result["transaction"]["to"], "+84901234567" if duplicated else "c1")
            self.assertEqual(env.get_tool_calls()[0]["arguments"]["phone"], "+84901234567")

    def test_K39_K42_sdk_defaults_without_invented_arguments(self):
        entry = copy.deepcopy(self.entry)
        entry["calendar"] = {"events": []}
        env = self.sdk.Session("synthetic", entry, self.catalog)
        event = env.call(
            "calendar.create_event", {"title": "meeting", "start": "2026-11-10T17:00:00+07:00"}
        )
        self.assertEqual(event["item"]["end"], "2026-11-10T18:00:00+07:00")
        self.assertNotIn("end", env.get_tool_calls()[0]["arguments"])
        order = env.call(
            "food_delivery.place_order",
            {"restaurant_id": "rest_01", "items": [{"item_id": "food_01", "quantity": 1}]},
        )
        self.assertEqual(order["order"]["payment"], "cash")
        self.assertNotIn("payment", env.get_tool_calls()[-1]["arguments"])

    def test_K43_climate_requires_mode(self):
        with self.assertRaises(Rejected):
            check_value(
                {"device_id": "climate1", "temperature": 26},
                self.catalog["smart_home.climate_set"]["parameters"],
            )

    def test_K52_failed_then_correct_attempt_keeps_both(self):
        self.env.call("smart_home.light_set", {"power": "on"})
        self.env.call("smart_home.light_set", {"device_id": "light_01", "power": "on"})
        self.assertEqual(len(self.env.get_tool_calls()), 2)
        self.assertNotIn("device_id", self.env.get_tool_calls()[0]["arguments"])


if __name__ == "__main__":
    unittest.main()
