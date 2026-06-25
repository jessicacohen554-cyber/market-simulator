"""CAISO calibration keeper defaults (P2).

The RA must-offer midday gas-commitment floor (frac 0.80) and negative
curtailable-renewable offers are the structurally-correct CAISO market design
(validated keeper caiso-6-floor-negrenew), so ``_calibration_config`` defaults
them ON for CAISO and leaves every other ISO untouched. The CLI flags are
tri-state (``None`` = keep the base default; explicit ``True``/``False``
overrides), so a no-floor baseline probe stays possible.
"""

import importlib.util
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "run_calibration", str(REPO / "scripts" / "run_calibration.py")
)
rc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rc)


class TestCaisoKeeperDefaults(unittest.TestCase):
    def test_caiso_defaults_floor_and_negative_offers_on(self):
        c = rc._calibration_config(2024, "CAISO", 8760, 3.0)
        self.assertTrue(c.caiso_gas_commitment_floor)
        self.assertAlmostEqual(c.caiso_gas_floor_frac, 0.80)
        self.assertTrue(c.negative_renewable_offers)
        # Local-RA CT_PEAKER reliability floor (temperature-driven) defaults ON.
        self.assertTrue(c.caiso_ct_reliability_floor)

    def test_other_isos_are_unaffected(self):
        for iso in ("ERCOT", "PJM", "NYISO", "NEISO"):
            c = rc._calibration_config(2024, iso, 8760, 3.0)
            self.assertFalse(c.caiso_gas_commitment_floor, iso)
            self.assertEqual(c.caiso_gas_floor_frac, 1.0, iso)
            self.assertFalse(c.negative_renewable_offers, iso)
            self.assertFalse(c.caiso_ct_reliability_floor, iso)

    def test_explicit_override_can_disable_for_a_baseline_probe(self):
        c = rc._calibration_config(2024, "CAISO", 8760, 3.0).with_overrides(
            caiso_gas_commitment_floor=False,
            negative_renewable_offers=False,
            caiso_ct_reliability_floor=False,
        )
        self.assertFalse(c.caiso_gas_commitment_floor)
        self.assertFalse(c.negative_renewable_offers)
        self.assertFalse(c.caiso_ct_reliability_floor)


if __name__ == "__main__":
    unittest.main()
