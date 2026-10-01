"""Tests for the SPP MMU offer-side unavailability carrier (SPP-106, carrier EX).

``spp_mmu_offer_unavailability`` (``docs/handoffs/DESIGN-spp-106-offer-side-unavailability-2026-10-01.md``)
replaces the flat fossil performance / summer class derates with the SPP MMU's measured bands.
Trivial cases first per the repo testing pattern: three rows, a full-year index where seasons matter.
"""

from __future__ import annotations

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import arrays
from market_sim.data.spp_mmu_unavailability import JUN_SEP_DAYS, mmu_shares
from tests.helpers.builders import make_gen

T = 8760


def _gens():
    return [
        make_gen(
            "CT_PEAKER_SPP-North_p7_peak",
            "SPP-North",
            fuel_type="gas_ct",
            pmax_mw=100.0,
            plant_group="CT_PEAKER",
            plant_code=7,
            online_year=2015,
        ),
        make_gen(
            "COAL_PRB_SPP-North_p9",
            "SPP-North",
            fuel_type="coal",
            pmax_mw=300.0,
            plant_group="COAL_PRB",
            plant_code=9,
            online_year=1980,
        ),
        make_gen(
            "nuclear_SPP-North_p10",
            "SPP-North",
            fuel_type="nuclear",
            pmax_mw=1000.0,
            plant_group="",
            plant_code=10,
            online_year=1985,
        ),
    ]


def _avail(cfg):
    gens = _gens()
    a = np.ones((len(gens), T))
    arrays._availability_matrix(gens, a, T, cfg, "SPP", 2024, set())
    return a


class TestShares(unittest.TestCase):
    """The table loads; the nearest-published-year hold rule; shares on the rated basis."""

    def test_hold_rule(self):
        self.assertEqual(mmu_shares(2019).year_used, 2020)
        self.assertEqual(mmu_shares(2023).year_used, 2023)
        self.assertEqual(mmu_shares(2025).year_used, 2024)
        self.assertEqual(mmu_shares(2040).year_used, 2024)

    def test_2024_values(self):
        sh = mmu_shares(2024)
        self.assertAlmostEqual(sh.above_emer, 1700 / 64800)
        self.assertAlmostEqual(sh.eco_to_emer, 1750 / 64800)
        # Fig 12 (exact): 340 MW on 112 days, spread over Jun-Sep
        self.assertAlmostEqual(sh.ambient_mw, 340 * 112 / JUN_SEP_DAYS)


class TestAvailabilitySeam(unittest.TestCase):
    """Armed, fossil rows drop the flat perf and summer class derates; off is untouched."""

    def setUp(self):
        self.off = ScenarioConfig(iso="SPP", mode="backcast", wefor_multiplier=0.7)
        self.on = ScenarioConfig(
            iso="SPP",
            mode="backcast",
            wefor_multiplier=0.7,
            spp_mmu_offer_unavailability=True,
        )

    def test_off_is_the_incumbent(self):
        base = _avail(self.off)
        month = arrays._hour_to_month_index(T) + 1
        _, _, derate = arrays._thermal_outage("CT_PEAKER", 2024 - 2015)
        # incumbent CT summer = (1 - summer_wefor - derate) x (1 - 0.125) < 1 - derate
        self.assertLess(float(base[0, month == 7].max()), 1.0 - derate)

    def test_armed_drops_flat_derates_on_fossil_only(self):
        base, armed = _avail(self.off), _avail(self.on)
        month = arrays._hour_to_month_index(T) + 1
        for g, grp, age in (
            (0, "CT_PEAKER", 2024 - 2015),
            (1, "COAL_PRB", 2024 - 1980),
        ):
            _, _, derate = arrays._thermal_outage(grp, age)
            diff = armed[g] - base[g]
            self.assertTrue((diff >= -1e-12).all())
            self.assertGreater(float(diff.mean()), 0.0)
            if grp == "CT_PEAKER":
                # summer: the 12.5 % class derate and the perf derate both gone
                jul_base, jul_on = base[g, month == 7][0], armed[g, month == 7][0]
                self.assertAlmostEqual(
                    jul_on, jul_base / (1.0 - 0.125) + derate, places=9
                )
        np.testing.assert_array_equal(base[2], armed[2])  # nuclear untouched

    def test_bands_after_overlays(self):
        gens = _gens()
        a = np.full((3, T), 0.9)
        a[1, :100] = 0.0  # coal on full outage for 100 h
        pmax = np.array([g.pmax_mw for g in gens])
        arrays._apply_spp_mmu_bands(gens, a, pmax, T, 2024)
        sh = mmu_shares(2024)
        month = arrays._hour_to_month_index(T) + 1
        flat = sh.above_emer + sh.eco_to_emer
        amb = sh.ambient_mw / 400.0
        np.testing.assert_allclose(a[0, month == 1], 0.9 - flat)
        np.testing.assert_allclose(a[0, month == 7], 0.9 - flat - amb)
        np.testing.assert_array_equal(a[1, :100], 0.0)  # clipped, never negative
        np.testing.assert_array_equal(a[2], 0.9)  # nuclear untouched


class TestConfig(unittest.TestCase):
    """SPP-only; off keeps the key."""

    def test_spp_only(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(iso="MISO", spp_mmu_offer_unavailability=True)

    def test_default_off_keeps_key(self):
        a = ScenarioConfig(iso="SPP")
        self.assertFalse(a.spp_mmu_offer_unavailability)
        b = ScenarioConfig(iso="SPP", spp_mmu_offer_unavailability=True)
        self.assertNotEqual(a.cache_key(), b.cache_key())


if __name__ == "__main__":
    unittest.main()
