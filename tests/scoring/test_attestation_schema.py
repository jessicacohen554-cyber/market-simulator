"""Tests for the fixed calibration_attestation.json schema (owner ruling 2026-10-03).

Exercises ``scripts/lib/attestation_schema.py``: a conforming attestation is
valid, the migration is additive and idempotent, and the lane-block manifest
tells a deliberate extra block from drift.
"""

import copy
import unittest

from scripts.lib import attestation_schema as asch


def _att():
    return {
        "schema": "calibration-attestation/v1",
        "governance": {
            "levers_trace_to_measured_input": True,
            "no_fit_to_price_residuals": True,
            "no_pinning_to_actuals": True,
            "outage_filter_exogenous_net_load": True,
            "attested_by": "test",
        },
        "free_parameters": {
            "schema": "dof-ledger/v1",
            "entries": [
                {
                    "name": "a",
                    "where": "x",
                    "identification": "measured",
                    "source": "s",
                    "value": 1,
                }
            ],
        },
        "exceptions": [],
        "authorized_price_tuning": {"declared": False},
        "disclosures": {},
        "lane_blocks": [],
    }


class AttestationSchemaTests(unittest.TestCase):
    def test_conforming_is_valid(self):
        self.assertEqual(asch.validate(_att()), [])

    def test_migrate_is_additive_and_idempotent(self):
        att = _att()
        for k in ("authorized_price_tuning", "disclosures", "lane_blocks", "schema"):
            del att[k]
        att["miso267"] = {"note": "lane block"}
        before = copy.deepcopy(att)
        changes = asch.migrate_dict(att)
        self.assertTrue(changes)
        self.assertEqual(asch.validate(att), [])
        self.assertEqual(att["lane_blocks"], ["miso267"])
        self.assertEqual(att["authorized_price_tuning"], {"declared": False})
        for k, v in before.items():  # nothing existing was touched
            self.assertEqual(att[k], v)
        self.assertEqual(asch.migrate_dict(att), [])

    def test_unlisted_lane_block_is_drift(self):
        att = _att()
        att["spp85"] = {}
        self.assertTrue(any("unlisted" in p for p in asch.validate(att)))
        att["lane_blocks"] = ["spp85"]
        self.assertEqual(asch.validate(att), [])

    def test_declared_must_agree_with_governance(self):
        att = _att()
        att["authorized_price_tuning"] = {"declared": True}
        self.assertTrue(any("disagrees" in p for p in asch.validate(att)))
        att["governance"]["authorized_price_tuning"] = dict.fromkeys(
            asch.TUNING_FIELDS, "x"
        )
        self.assertEqual(asch.validate(att), [])

    def test_rubric_stamp_tolerated(self):
        att = _att()
        att["rubric_version"] = "v3.19"
        self.assertEqual(asch.validate(att), [])


if __name__ == "__main__":
    unittest.main()
