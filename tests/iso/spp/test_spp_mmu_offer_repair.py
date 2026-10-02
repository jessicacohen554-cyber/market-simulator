"""Tests for the SPP-107 repair sub-gate of the MMU offer-side carrier.

``spp_mmu_offer_repair`` (``docs/records/spp/DESIGN-spp-107-mmu-carrier-repair-2026-10-02.md``):
(1) the MMU bands are shares of the row's post-outage AVAILABLE MW (multiplicative); (2) the
economic-to-emergency slice is a per-zone pool offered at the shed price minus epsilon, so it clears
only where load would otherwise be shed. Trivial cases first: a few rows, one zone, 24 h for the LP.
"""

from __future__ import annotations

import unittest

import numpy as np

from market_sim.config.constants import STORAGE_TIEBREAKER_EPSILON
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import arrays, generators_to_fleet_arrays
from market_sim.data.spp_mmu_unavailability import (
    build_spp_mmu_pool_generators,
    mmu_shares,
)
from tests.helpers.builders import make_gen
from tests.helpers.solve import solve_tiny

T = 8760


def _fossil():
    return [
        make_gen(
            "ct_s",
            "SPP-South",
            fuel_type="gas_ct",
            pmax_mw=100.0,
            plant_group="CT_PEAKER",
        ),
        make_gen(
            "coal_s",
            "SPP-South",
            fuel_type="coal",
            pmax_mw=300.0,
            plant_group="COAL_PRB",
        ),
        make_gen(
            "cc_n",
            "SPP-North",
            fuel_type="gas_cc",
            pmax_mw=200.0,
            plant_group="CC_REGULAR",
        ),
        make_gen(
            "nuc_n", "SPP-North", fuel_type="nuclear", pmax_mw=1000.0, plant_group=""
        ),
    ]


def _cfg(**kw):
    return ScenarioConfig(
        iso="SPP",
        mode="backcast",
        weather_year=2024,
        spp_mmu_offer_unavailability=True,
        **kw,
    )


class TestConfig(unittest.TestCase):
    """A sub-gate of the parent; off keeps every key."""

    def test_requires_parent(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(iso="SPP", spp_mmu_offer_repair=True)

    def test_spp_only_through_parent(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(
                iso="MISO", spp_mmu_offer_unavailability=True, spp_mmu_offer_repair=True
            )

    def test_default_off_keeps_key(self):
        a = _cfg()
        self.assertFalse(a.spp_mmu_offer_repair)
        self.assertNotEqual(a.cache_key(), _cfg(spp_mmu_offer_repair=True).cache_key())
        self.assertEqual(
            ScenarioConfig(iso="SPP").cache_key(), ScenarioConfig(iso="SPP").cache_key()
        )


class TestMultiplicativeBands(unittest.TestCase):
    """Repair (1): a partly outaged row loses the share of what it still has."""

    def test_multiplicative_vs_additive(self):
        gens = _fossil()
        pmax = np.array([g.pmax_mw for g in gens])
        add, mul = np.full((4, T), 0.5), np.full((4, T), 0.5)
        add[1, :10] = mul[1, :10] = 0.0
        arrays._apply_spp_mmu_bands(gens, add, pmax, T, 2024)
        arrays._apply_spp_mmu_bands(gens, mul, pmax, T, 2024, multiplicative=True)
        sh = mmu_shares(2024)
        jan = arrays._hour_to_month_index(T) == 0
        flat = sh.above_emer + sh.eco_to_emer
        np.testing.assert_allclose(add[0, jan], 0.5 - flat)
        np.testing.assert_allclose(mul[0, jan], 0.5 * (1.0 - flat))
        self.assertTrue((mul[:3] >= add[:3]).all())  # never removes more than EX
        np.testing.assert_array_equal(mul[1, :10], 0.0)  # full outage stays 0
        np.testing.assert_array_equal(mul[3], 0.5)  # nuclear untouched

    def test_full_availability_identical(self):
        gens = _fossil()
        pmax = np.array([g.pmax_mw for g in gens])
        add, mul = np.ones((4, T)), np.ones((4, T))
        arrays._apply_spp_mmu_bands(gens, add, pmax, T, 2024)
        arrays._apply_spp_mmu_bands(gens, mul, pmax, T, 2024, multiplicative=True)
        np.testing.assert_allclose(add, mul)


class TestPool(unittest.TestCase):
    """Repair (2): one pool row per zone, priced at shed - eps, sized to the removed slice."""

    def test_builder_gated(self):
        self.assertEqual(
            build_spp_mmu_pool_generators(_cfg(), "SPP", _fossil(), 2000.0), []
        )

    def test_builder_rows(self):
        pool = build_spp_mmu_pool_generators(
            _cfg(spp_mmu_offer_repair=True), "SPP", _fossil(), 2000.0
        )
        sh = mmu_shares(2024)
        self.assertEqual([p.zone for p in pool], ["SPP-North", "SPP-South"])
        for p in pool:
            self.assertEqual(p.fuel_type, "emergency_band")
            self.assertAlmostEqual(p.vom, 2000.0 - STORAGE_TIEBREAKER_EPSILON)
            self.assertEqual((p.heat_rate, p.pmin_mw, p.eford), (0.0, 0.0, 0.0))
        self.assertAlmostEqual(pool[1].pmax_mw, sh.eco_to_emer * 400.0)

    def test_pool_restores_emergency_max(self):
        cfg = _cfg(spp_mmu_offer_repair=True)
        gens = _fossil()
        gens = gens + build_spp_mmu_pool_generators(cfg, "SPP", gens, 2000.0)
        pmax = np.array([g.pmax_mw for g in gens])
        pre = np.full((len(gens), T), 0.6)
        a = pre.copy()
        arrays._apply_spp_mmu_bands(gens, a, pmax, T, 2024, multiplicative=True)
        arrays._apply_spp_mmu_pool(gens, a, pmax, T, 2024)
        sh = mmu_shares(2024)
        south = [0, 1]
        econ = (a[south] * pmax[south, None]).sum(0)
        pool_mw = a[5] * pmax[5]
        np.testing.assert_allclose(
            pool_mw, sh.eco_to_emer * (pre[south] * pmax[south, None]).sum(0)
        )
        jan = arrays._hour_to_month_index(T) == 0
        # economic max + pool = emergency max = pre x (1 - above) outside Jun-Sep
        np.testing.assert_allclose(
            (econ + pool_mw)[jan],
            ((pre[south] * pmax[south, None]).sum(0) * (1 - sh.above_emer))[jan],
        )


class TestPoolClearsOnlyInScarcity(unittest.TestCase):
    """1 zone, 24 h: the pool is dark while fossil covers load and serves instead of shedding."""

    def test_lp(self):
        voll = 2000.0
        gens = [
            make_gen(
                "ct",
                "SPP-South",
                fuel_type="gas_ct",
                pmax_mw=100.0,
                pmin_mw=0.0,
                eford=0.0,
            ),
            make_gen(
                "pool",
                "SPP-South",
                fuel_type="emergency_band",
                pmax_mw=10.0,
                pmin_mw=0.0,
                eford=0.0,
                vom=voll - STORAGE_TIEBREAKER_EPSILON,
            ),
        ]
        fa = generators_to_fleet_arrays(gens, ["SPP-South"], hours=24)
        fa.availability[0, :] = 0.9
        fa.availability[1, :] = 0.5
        demand = np.r_[np.full(12, 50.0), np.full(12, 93.0)]
        r = solve_tiny(
            fa,
            {"SPP-South": demand},
            mc=np.array([30.0, voll - STORAGE_TIEBREAKER_EPSILON]),
            voll=voll,
        )
        np.testing.assert_allclose(r.dispatch[1, :12], 0.0, atol=1e-6)
        np.testing.assert_allclose(r.dispatch[1, 12:], 3.0, atol=1e-6)
        np.testing.assert_allclose(r.slack, 0.0, atol=1e-6)
        np.testing.assert_allclose(
            r.prices[0, 12:], voll - STORAGE_TIEBREAKER_EPSILON, atol=1e-6
        )
        self.assertLess(float(r.prices[0, :12].max()), 31.0)


if __name__ == "__main__":
    unittest.main()
