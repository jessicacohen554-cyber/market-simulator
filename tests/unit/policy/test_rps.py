"""Tests for policy.rps — trajectories, ACP, and the eligible-fuel sets.

FFR-7B Arm 1 (FFR-6B §8): the renewable row carries each statute's RENEWABLE
tier and its statute-defined eligible set. These tests pin the corrected
levels to their statutory sources and the eligible-set table to the fuel
taxonomy, so drift in either is a deliberate, cited edit — never silent.
"""

import unittest

from market_sim.config.constants import RPS_ELIGIBLE_FUELS_BY_ISO
from market_sim.data.fleet import FUEL_TYPE_MAP
from market_sim.policy.rps import (
    get_rps_acp,
    get_rps_eligible_fuels,
    get_rps_target,
)


class TestRenewableTierTrajectories(unittest.TestCase):
    """The corrected renewable-tier knots (FFR-7B Arm 1, rule 14)."""

    def test_nyiso_renewable_tier_plateaus_at_70(self):
        # PSL §66-p(2)(a): 70% renewable by 2030; NO post-2030 renewable
        # percentage exists in the statute — the 100x40 zero-emission
        # standard (§66-p(2)(b), nuclear-counting) is NOT this row.
        self.assertAlmostEqual(get_rps_target("NYISO", 2030), 0.70)
        self.assertAlmostEqual(get_rps_target("NYISO", 2040), 0.70)
        self.assertAlmostEqual(get_rps_target("NYISO", 2045), 0.70)

    def test_caiso_rps_plateaus_at_statutory_60(self):
        # Pub. Util. Code §399.15(b)(2)(B)/(C): 60% by 2030 and "not less
        # than 60 percent" for all subsequent years. SB 100's zero-carbon
        # path (§454.53) is a separate tier and never re-enters this row.
        self.assertAlmostEqual(get_rps_target("CAISO", 2030), 0.60)
        self.assertAlmostEqual(get_rps_target("CAISO", 2040), 0.60)
        self.assertAlmostEqual(get_rps_target("CAISO", 2045), 0.60)

    def test_neiso_class_i_blend_knots(self):
        # Load-weighted New England NEW-renewable (Class I / RES) blend —
        # MA 225 CMR 14.05 tier per G.L. c.25A §11F, CT CGS §16-245a,
        # RI §39-26-4, ME 35-A M.R.S. §3210, NH RSA 362-F:3, VT Act 179 —
        # NOT the nuclear-counting MA CES blend the old knots encoded.
        self.assertAlmostEqual(get_rps_target("NEISO", 2026), 0.29)
        self.assertAlmostEqual(get_rps_target("NEISO", 2030), 0.40)
        self.assertAlmostEqual(get_rps_target("NEISO", 2040), 0.48)
        self.assertAlmostEqual(get_rps_target("NEISO", 2045), 0.50)


class TestEligibleFuelSets(unittest.TestCase):
    """RPS_ELIGIBLE_FUELS_BY_ISO — statute-defined, taxonomy-resolvable."""

    def test_every_name_resolves_against_fuel_taxonomy(self):
        for iso, fuels in RPS_ELIGIBLE_FUELS_BY_ISO.items():
            for fuel in fuels:
                self.assertIn(fuel, FUEL_TYPE_MAP, msg=f"{iso}: {fuel}")

    def test_nuclear_never_eligible(self):
        # CX-6a: a clean tier that counts nuclear is a separate row family
        # (FFR-6B §6.3), never a widening of the renewable row.
        for iso, fuels in RPS_ELIGIBLE_FUELS_BY_ISO.items():
            self.assertNotIn("nuclear", fuels, msg=iso)

    def test_statutory_sets(self):
        # NYISO: PSL §66-p(1)(b) counts hydroelectric (existing included);
        # biomass/biogas are NOT in the statutory definition.
        self.assertEqual(
            get_rps_eligible_fuels("NYISO"),
            ("wind", "solar", "offshore_wind", "hydro"),
        )
        # CAISO: Pub. Res. Code §25741(a) counts geothermal and biomass
        # (small hydro ≤30 MW is excluded as misaligned to the aggregated
        # hydro class — rule 14 exception, documented at the table).
        self.assertEqual(
            get_rps_eligible_fuels("CAISO"),
            ("wind", "solar", "offshore_wind", "geothermal", "biomass"),
        )
        # NEISO: MA Class I (225 CMR 14.05) — offshore wind counts; the
        # small biomass/hydro share stays folded in (PJM/MISO convention).
        self.assertEqual(
            get_rps_eligible_fuels("NEISO"),
            ("wind", "solar", "offshore_wind"),
        )

    def test_unlisted_isos_keep_wind_solar_only_row(self):
        # PJM/MISO folded-in convention adjudicated sound (FFR-6B §8.2);
        # ERCOT builds no row. None keeps the row byte-identical.
        for iso in ("PJM", "MISO", "ERCOT"):
            self.assertIsNone(get_rps_eligible_fuels(iso), msg=iso)

    def test_acp_unchanged(self):
        # Arm 1 corrects levels and eligible sets — never the ACP ceilings.
        self.assertEqual(get_rps_acp("NYISO"), 40.0)
        self.assertEqual(get_rps_acp("CAISO"), 50.0)
        self.assertEqual(get_rps_acp("NEISO"), 50.0)


if __name__ == "__main__":
    unittest.main()
