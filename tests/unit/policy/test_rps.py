"""Tests for policy.rps — trajectories, ACP, and the eligible-fuel sets.

FFR-7B Arm 1 (FFR-6B §8): the renewable row carries each statute's RENEWABLE
tier and its statute-defined eligible set. These tests pin the corrected
levels to their statutory sources and the eligible-set table to the fuel
taxonomy, so drift in either is a deliberate, cited edit — never silent.
"""

import unittest

import numpy as np

from market_sim.config.constants import RPS_ELIGIBLE_FUELS_BY_ISO
from market_sim.config.iso_configs import get_iso_config
from market_sim.data.fleet import FUEL_TYPE_MAP
from market_sim.policy.rps import (
    build_rps_region_arrays,
    get_rps_acp,
    get_rps_eligible_fuels,
    get_rps_target,
    rps_credit_for_zone,
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


class TestMisoComplianceRegions(unittest.TestCase):
    """The per-state MISO compliance-region table (FFR-7B Arm 2 / FFR-6B E-1)."""

    def _miso_zones(self):
        cfg = get_iso_config("MISO")
        return [z.name for z in cfg.zones], {z.name: z.load_share for z in cfg.zones}

    def test_blend_reproduces_iso_wide_knots(self):
        # FFR-6B §1.5 verification, re-run against the SHIPPED table: the
        # per-region obligations re-blended onto the model's own zone load
        # shares reproduce the ISO-wide STATE_RPS_FLOORS["MISO"] knots —
        # Σ_r rhs_r / total demand ≈ .1139 / .1606 / .1981 at 2026/30/40. The
        # zonal grain moves WHERE compliance is met, never HOW MUCH is owed.
        zone_names, shares = self._miso_zones()
        share_vec = [shares[z] for z in zone_names]
        for year, expected in ((2026, 0.1139), (2030, 0.1606), (2040, 0.1981)):
            arrays = build_rps_region_arrays("MISO", year, zone_names)
            blended = float(
                sum(
                    arrays.obligation_frac[r, z] * share_vec[z]
                    for r in range(arrays.obligation_frac.shape[0])
                    for z in range(len(zone_names))
                )
            )
            self.assertAlmostEqual(blended, expected, delta=1e-4, msg=str(year))

    def test_mi_row_is_east_only_and_footprint_excludes_south(self):
        # MCL 460.1029 ("located within this state", MIRECS): Michigan's row
        # admits MISO-East certificates ONLY — the restriction that IS E-1.
        # Every delivery-based row's footprint excludes MISO-South.
        zone_names, _ = self._miso_zones()
        arrays = build_rps_region_arrays("MISO", 2030, zone_names)
        mi = arrays.labels.index("MI")
        east = zone_names.index("MISO-East")
        south = zone_names.index("MISO-South")
        self.assertTrue(arrays.eligible_zone_mask[mi, east])
        self.assertEqual(int(arrays.eligible_zone_mask[mi].sum()), 1)
        for r in range(len(arrays.labels)):
            self.assertFalse(arrays.eligible_zone_mask[r, south])

    def test_row_count_is_year_invariant(self):
        # Layout (and with it cache identity) is a function of the table
        # alone: a region whose target is flat/zero at some year still emits
        # its row, so K never varies with the solve year.
        zone_names, _ = self._miso_zones()
        for year in (2026, 2035, 2045):
            arrays = build_rps_region_arrays("MISO", year, zone_names)
            self.assertEqual(len(arrays.labels), 5, msg=str(year))
            self.assertEqual(arrays.acp_price.shape, (5,))

    def test_acp_is_miso_proxy_for_every_region(self):
        # STATE_RPS_ACP["MISO"]'s $30 forward REC-price-ceiling proxy prices
        # every region's escape (per-region ACPs are a refinement, not a
        # requirement — FFR-6B §3.4).
        zone_names, _ = self._miso_zones()
        arrays = build_rps_region_arrays("MISO", 2030, zone_names)
        for price in arrays.acp_price:
            self.assertEqual(float(price), 30.0)

    def test_non_miso_has_no_region_table(self):
        # Rule 25 [R-ISO-SCOPE] + FFR-6B §2.1: the other RPS ISOs' single
        # ISO-wide row is exact — no region table exists for them.
        for iso in ("ERCOT", "CAISO", "PJM", "NYISO", "NEISO"):
            self.assertIsNone(build_rps_region_arrays(iso, 2030, ["Z0"]), msg=iso)

    def test_topology_drift_fails_loud(self):
        # A zone name in the table absent from the model ordering is a
        # KeyError, never a silently dropped state standard.
        with self.assertRaises(KeyError):
            build_rps_region_arrays("MISO", 2030, ["MISO-West", "MISO-East"])


class TestRpsCreditForZone(unittest.TestCase):
    """The shared per-zone credit helper every capacity screen routes through."""

    def test_scalar_passes_through(self):
        # Legacy single-row dual: unchanged for every consumer, zone or not.
        self.assertEqual(rps_credit_for_zone(12.5, 3), 12.5)
        self.assertEqual(rps_credit_for_zone(12.5, None), 12.5)

    def test_vector_indexes_by_zone(self):
        # K-row grain: an East candidate sees East's dual; a South candidate
        # (outside every region's eligibility geography) sees 0 — never a
        # broadcast of another region's dual (FFR-6B §3.2).
        per_zone = np.array([0.0, 0.0, 0.0, 0.0, 30.0, 0.0])
        self.assertEqual(rps_credit_for_zone(per_zone, 4), 30.0)
        self.assertEqual(rps_credit_for_zone(per_zone, 5), 0.0)

    def test_vector_without_zone_context_degrades_to_zero(self):
        # No zone context → 0.0, the conservative side: the broadcast max
        # would rebuild the defect the grain fixed.
        per_zone = np.array([30.0, 0.0])
        self.assertEqual(rps_credit_for_zone(per_zone, None), 0.0)
        self.assertEqual(rps_credit_for_zone(per_zone, 7), 0.0)

    def test_none_is_zero(self):
        self.assertEqual(rps_credit_for_zone(None, 2), 0.0)


if __name__ == "__main__":
    unittest.main()
