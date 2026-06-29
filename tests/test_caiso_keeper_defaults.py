"""CAISO calibration keeper defaults (Step-1 RA must-offer design).

The structurally-correct CAISO market design defaults a forward-derivable RA
must-offer commitment (``caiso_ra_mustoffer``) and negative curtailable-renewable
offers ON for CAISO, leaving every other ISO untouched. The Step-1 overhaul
RETIRED the measured-NG:NG midday gas slab (``caiso_gas_commitment_floor``) and
the per-ISO CT temperature floor (``caiso_ct_reliability_floor``) in favour of
the must-offer bridge plus the generic ``reliability_floor`` registry
(iso_configs.RELIABILITY_FLOOR_REGISTRY), so both legacy levers now default OFF.
The CLI flags are tri-state (``None`` = keep the base default; explicit
``True``/``False`` overrides), so a no-floor baseline probe stays possible.
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
    def test_caiso_defaults_ra_mustoffer_and_negative_offers_on(self):
        c = rc._calibration_config(2024, "CAISO", 8760, 3.0)
        # Step-1 design: must-offer bridge ON, the retired slab + per-ISO CT
        # floor OFF, the generic registry-driven reliability floor ON.
        self.assertTrue(c.caiso_ra_mustoffer)
        self.assertAlmostEqual(c.caiso_ra_min_load_frac, 0.26)
        self.assertTrue(c.negative_renewable_offers)
        self.assertTrue(c.reliability_floor)
        # Legacy lever superseded by the must-offer bridge / generic registry.
        self.assertFalse(c.caiso_gas_commitment_floor)

    def test_other_isos_are_unaffected(self):
        for iso in ("ERCOT", "PJM", "NYISO", "NEISO"):
            c = rc._calibration_config(2024, iso, 8760, 3.0)
            self.assertFalse(c.caiso_ra_mustoffer, iso)
            self.assertFalse(c.caiso_gas_commitment_floor, iso)
            self.assertEqual(c.caiso_gas_floor_frac, 1.0, iso)
            self.assertFalse(c.negative_renewable_offers, iso)

    def test_explicit_override_can_disable_for_a_baseline_probe(self):
        c = rc._calibration_config(2024, "CAISO", 8760, 3.0).with_overrides(
            caiso_ra_mustoffer=False,
            negative_renewable_offers=False,
        )
        self.assertFalse(c.caiso_ra_mustoffer)
        self.assertFalse(c.negative_renewable_offers)


if __name__ == "__main__":
    unittest.main()
