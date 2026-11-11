import unittest

from lifemate.references import ReferenceIndex
from lifemate.validator import Rejected


class ReferenceTests(unittest.TestCase):
    def test_K19_device_type_and_collection_mismatch(self):
        idx = ReferenceIndex({"text": "", "history": []})
        idx.observe(
            "smart_home.get_status",
            {"ok": True, "devices": [{"id": "fan1", "type": "fan"}]},
            "live:0",
        )
        schema = {"type": "object", "properties": {"device_id": {"x-ref": "smart_home.devices"}}}
        with self.assertRaises(Rejected):
            idx.check({"device_id": "fan1"}, schema, "smart_home.light_set")
        with self.assertRaises(Rejected):
            idx.check({"id": "fan1"}, {"properties": {"id": {"x-ref": "contacts.contacts"}}})

    def test_K41_restaurant_parent(self):
        idx = ReferenceIndex({"text": ""})
        idx.observe(
            "food_delivery.search",
            {"ok": True, "restaurants": [{"id": "r1", "menu": [{"id": "m1"}]}]},
            "live:0",
        )
        schema = {
            "properties": {
                "items": {"items": {"properties": {"item_id": {"x-ref": "food_delivery.menu"}}}}
            }
        }
        with self.assertRaises(Rejected):
            idx.check({"restaurant_id": "r2", "items": [{"item_id": "m1"}]}, schema)

    def test_schema_literal_grounding_and_filename_not_evidence(self):
        idx = ReferenceIndex({"audio": "made_up.wav", "text": ""})
        with self.assertRaises(Rejected):
            idx.check({"id": "made_up"}, {"properties": {"id": {"x-ref": "x.items"}}})
        self.assertTrue(
            idx.check(
                {"id": "builtin"}, {"properties": {"id": {"x-ref": "x.items", "enum": ["builtin"]}}}
            )
        )

    def test_K15_K20_K23_K24_ambiguity_and_empty_reads(self):
        schema = {"properties": {"contact_id": {"x-ref": "contacts.contacts"}}}
        idx = ReferenceIndex({"text": "send Minh"})
        idx.observe("contacts.search", {"ok": True, "contacts": []}, "live:0")
        with self.assertRaises(Rejected):
            idx.check({"contact_id": "first"}, schema)
        idx.observe(
            "contacts.search",
            {
                "ok": True,
                "contacts": [{"id": "first", "name": "Minh"}, {"id": "second", "name": "Minh"}],
            },
            "live:1",
        )
        with self.assertRaisesRegex(Rejected, "ambiguous"):
            idx.check({"contact_id": "first"}, schema)
        idx.observe(
            "contacts.search",
            {"ok": True, "contacts": [{"id": "second", "name": "Minh"}]},
            "live:2",
        )
        self.assertTrue(idx.check({"contact_id": "second"}, schema))

    def test_K14_device_room_and_type_disambiguates(self):
        idx = ReferenceIndex({"text": "light living room"})
        idx.observe(
            "smart_home.get_status",
            {
                "ok": True,
                "devices": [
                    {"id": "a", "type": "light", "room": "living room"},
                    {"id": "b", "type": "light", "room": "bedroom"},
                    {"id": "c", "type": "fan", "room": "living room"},
                ],
            },
            "live:0",
        )
        self.assertTrue(
            idx.check(
                {"device_id": "a"},
                {"properties": {"device_id": {"x-ref": "smart_home.devices"}}},
                "smart_home.light_set",
            )
        )

    def test_K41_actual_schema_missing_nested_ref_still_checks_parent(self):
        idx = ReferenceIndex({"text": "r2"})
        idx.observe(
            "food_delivery.get_menu",
            {"ok": True, "menu": [{"id": "m1", "name": "rice"}]},
            "live:0",
            {"restaurant_id": "r1"},
        )
        schema = {
            "properties": {"items": {"items": {"properties": {"item_id": {"type": "string"}}}}}
        }
        with self.assertRaisesRegex(Rejected, "restaurant/menu"):
            idx.check(
                {"restaurant_id": "r2", "items": [{"item_id": "m1"}]},
                schema,
                "food_delivery.place_order",
            )

    def test_K17_beneficiary_missing_or_ambiguous(self):
        idx = ReferenceIndex({"text": "transfer to mother"})
        schema = {"properties": {"beneficiary_id": {"x-ref": "banking.beneficiaries"}}}
        with self.assertRaises(Rejected):
            idx.check({"beneficiary_id": "b1"}, schema)
        idx.observe(
            "banking.list_beneficiaries",
            {
                "ok": True,
                "beneficiaries": [{"id": "b1", "name": "mother"}, {"id": "b2", "name": "mother"}],
            },
            "live:0",
        )
        with self.assertRaisesRegex(Rejected, "ambiguous"):
            idx.check({"beneficiary_id": "b1"}, schema)
