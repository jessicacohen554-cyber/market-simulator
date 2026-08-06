"""Tests for policy.clean_tiers — the MISO clean/carbon-free tier family.

FFR-7B Arm 3 (FFR-6B E-2): two per-state clean rows (MN carbon-free, MI
clean) on the Arm-2 K-row machinery, with per-statute qualifying sets as
data, a zero-before-first-knot trajectory convention, an explicit Illinois
null, and the per-(fuel, zone) consumer credit mapping. These tests pin the
cited table to its statutory sources so drift is a deliberate edit — never
silent.
"""

import unittest

import numpy as np

from market_sim.config.constants import MISO_CLEAN_TIER_REGIONS
from market_sim.config.iso_configs import get_iso_config
from market_sim.data.fleet import FUEL_TYPE_MAP
from market_sim.policy.clean_tiers import (
    build_clean_region_arrays,
    clean_credit_by_fuel,
    clean_credit_for_zone,
)


def _miso_zone_names():
    return [z.name for z in get_iso_config("MISO").zones]


class TestCleanTierTable(unittest.TestCase):
    """The cited MISO_CLEAN_TIER_REGIONS table and its trajectory convention."""

    def test_illinois_is_a_recorded_null(self):
        # FFR-6B §6.1: CEJA is a source-side phase-out, not an LSE share
        # obligation — Illinois must NOT have a clean row.
        self.assertEqual(tuple(MISO_CLEAN_TIER_REGIONS), ("MN", "MI"))

    def test_qualifying_sets_are_per_statute(self):
        # MN carbon-free admits hydrogen and biomass (§216B.1691 subd. 2g);
        # MI clean admits qualified CCS gas (2023 PA 235) — and neither set
        # is the other's. Every name resolves against the fuel taxonomy.
        mn = MISO_CLEAN_TIER_REGIONS["MN"]["qualifying_fuels"]
        mi = MISO_CLEAN_TIER_REGIONS["MI"]["qualifying_fuels"]
        self.assertIn("hydrogen_ct", mn)
        self.assertIn("hydrogen_ccgt", mn)
        self.assertIn("biomass", mn)
        self.assertNotIn("gas_cc_ccs", mn)
        self.assertIn("gas_cc_ccs", mi)
        self.assertNotIn("hydrogen_ct", mi)
        for fuels in (mn, mi):
            self.assertIn("nuclear", fuels)
            for f in fuels:
                self.assertIn(f, FUEL_TYPE_MAP, msg=f)

    def test_zero_before_first_statutory_knot(self):
        # A clean tier imposes NOTHING before its first compliance date —
        # deliberately NOT the RPS edge-hold, which would compel MN's 80%
        # in 2026 four years before the law requires it.
        zone_names = _miso_zone_names()
        arrays = build_clean_region_arrays("MISO", 2026, zone_names)
        np.testing.assert_array_equal(arrays.obligation_frac, 0.0)

    def test_obligations_reproduce_ffr6b_adjudication_table(self):
        # FFR-6B §6.2's measured obligations: West .616/.693/.770 and
        # East 0/.456/.570 at 2030/35/40 (state tier x within-zone share).
        zone_names = _miso_zone_names()
        west = zone_names.index("MISO-West")
        east = zone_names.index("MISO-East")
        expected = {
            2030: {"MN": 0.616, "MI": 0.0},
            2035: {"MN": 0.693, "MI": 0.456},
            2040: {"MN": 0.770, "MI": 0.570},
        }
        for year, exp in expected.items():
            arrays = build_clean_region_arrays("MISO", year, zone_names)
            mn = arrays.labels.index("MN")
            mi = arrays.labels.index("MI")
            self.assertAlmostEqual(
                arrays.obligation_frac[mn, west], exp["MN"], places=3, msg=str(year)
            )
            self.assertAlmostEqual(
                arrays.obligation_frac[mi, east], exp["MI"], places=3, msg=str(year)
            )

    def test_mi_row_is_east_only(self):
        # The same MCL 460.1029 in-state restriction as MI's renewable row.
        zone_names = _miso_zone_names()
        arrays = build_clean_region_arrays("MISO", 2040, zone_names)
        mi = arrays.labels.index("MI")
        east = zone_names.index("MISO-East")
        self.assertTrue(arrays.eligible_zone_mask[mi, east])
        self.assertEqual(int(arrays.eligible_zone_mask[mi].sum()), 1)

    def test_feasibility_escape_is_the_documented_miso_proxy(self):
        # FFR-6B §6.3: a 100%-by-2040 row MUST carry a feasibility escape —
        # the $30 MISO proxy, reused and documented.
        zone_names = _miso_zone_names()
        arrays = build_clean_region_arrays("MISO", 2040, zone_names)
        for price in arrays.acp_price:
            self.assertEqual(float(price), 30.0)

    def test_row_count_is_year_invariant(self):
        # Layout / cache identity is a function of the table alone.
        zone_names = _miso_zone_names()
        for year in (2026, 2035, 2045):
            arrays = build_clean_region_arrays("MISO", year, zone_names)
            self.assertEqual(len(arrays.labels), 2, msg=str(year))

    def test_non_miso_has_no_clean_table(self):
        for iso in ("ERCOT", "CAISO", "PJM", "NYISO", "NEISO"):
            self.assertIsNone(build_clean_region_arrays(iso, 2040, ["Z0"]), msg=iso)


class TestCleanCreditMapping(unittest.TestCase):
    """The per-(fuel, zone) consumer credit — fuel AND zone resolved."""

    def _arrays(self, year=2040):
        return build_clean_region_arrays("MISO", year, _miso_zone_names())

    def test_credit_is_fuel_and_zone_resolved(self):
        # With MN's row binding at $20 and MI's at $30: a nuclear unit in
        # MISO-East sees max(MN via footprint, MI) = 30; in MISO-South
        # (outside both geographies) 0; a gas_cc_ccs unit earns MI's dual in
        # East ONLY (MN's carbon-free definition excludes CCS gas), so in
        # MISO-West it earns 0 even though MN's row is binding there.
        zone_names = _miso_zone_names()
        arrays = self._arrays()
        by_fuel = clean_credit_by_fuel(arrays, np.array([20.0, 30.0]))
        east = zone_names.index("MISO-East")
        west = zone_names.index("MISO-West")
        south = zone_names.index("MISO-South")
        self.assertEqual(clean_credit_for_zone(by_fuel, "nuclear", east), 30.0)
        self.assertEqual(clean_credit_for_zone(by_fuel, "nuclear", west), 20.0)
        self.assertEqual(clean_credit_for_zone(by_fuel, "nuclear", south), 0.0)
        self.assertEqual(clean_credit_for_zone(by_fuel, "gas_cc_ccs", east), 30.0)
        self.assertEqual(clean_credit_for_zone(by_fuel, "gas_cc_ccs", west), 0.0)
        self.assertEqual(clean_credit_for_zone(by_fuel, "hydrogen_ct", west), 20.0)
        self.assertEqual(clean_credit_for_zone(by_fuel, "hydrogen_ct", east), 20.0)

    def test_family_off_and_unlisted_fuel_degrade_to_zero(self):
        arrays = self._arrays()
        by_fuel = clean_credit_by_fuel(arrays, np.array([20.0, 30.0]))
        self.assertEqual(clean_credit_for_zone(None, "nuclear", 0), 0.0)
        self.assertEqual(clean_credit_for_zone({}, "nuclear", 0), 0.0)
        self.assertEqual(clean_credit_for_zone(by_fuel, "coal", 0), 0.0)
        self.assertEqual(clean_credit_for_zone(by_fuel, "nuclear", None), 0.0)
        self.assertEqual(clean_credit_for_zone(by_fuel, "nuclear", 99), 0.0)


if __name__ == "__main__":
    unittest.main()
