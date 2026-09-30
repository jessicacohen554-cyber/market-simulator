"""Tests for the SPP gas-family CROW-residual outage carrier (SPP-105, carrier B).

``spp_gas_crow_residual_outage`` (``docs/handoffs/DESIGN-spp-105-gas-family-outage-2026-09-30.md``)
replaces every gas row's statistical WEFOR / POF with SPP's published gas outage minus the CAMPD
events. Trivial cases first per the repo testing pattern: two or three rows, a handful of hours for the
allocator, a full-year index where seasons matter.
"""

from __future__ import annotations

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import arrays
from market_sim.data.spp_gas_outage import (
    allocate_crow_residual,
    edge_live,
    spp_published_gas_outage_mw,
)
from tests.helpers.builders import make_gen

T = 8760


def _gens():
    return [
        make_gen(
            "CT_PEAKER_SPP-North_p7_peak",
            "SPP-North",
            fuel_type="gas_ct",
            pmax_mw=60.0,
            plant_group="CT_PEAKER",
            plant_code=7,
            online_year=2015,
        ),
        make_gen(
            "ST_GAS_SPP-North_p8",
            "SPP-North",
            fuel_type="gas_st",
            pmax_mw=300.0,
            plant_group="ST_GAS",
            plant_code=8,
            online_year=1975,
        ),
        make_gen(
            "COAL_PRB_SPP-North_p9",
            "SPP-North",
            fuel_type="coal",
            pmax_mw=500.0,
            plant_group="COAL_PRB",
            plant_code=9,
            online_year=1980,
        ),
    ]


def _avail(cfg, rate_out=None):
    gens = _gens()
    a = np.ones((len(gens), T))
    arrays._availability_matrix(
        gens, a, T, cfg, "SPP", 2024, set(), crow_rate_out=rate_out
    )
    return a


class TestAllocator(unittest.TestCase):
    """The residual is SPP's total minus events, split on the key, capped, never forced."""

    def test_residual_split_on_key(self):
        pm = np.array([100.0, 300.0])
        pre = np.ones((2, 4))
        post = pre.copy()
        post[1, :] = 0.5  # 150 MW of events on row 1 every hour
        rate = np.array([0.1, 0.1 / 3])  # equal keys: 10 MW each
        pub = np.array([150.0, 250.0, 100.0, np.nan])
        new, d = allocate_crow_residual(pm, pre, post, rate, pub)
        # hour 0: residual 0; hour 1: 100 MW split 50/50; hour 2: SPP below events -> none; hour 3 NaN
        np.testing.assert_allclose(new[:, 0], post[:, 0])
        np.testing.assert_allclose(new[0, 1], 1.0 - 50.0 / 100.0)
        np.testing.assert_allclose(new[1, 1], 0.5 - 50.0 / 300.0)
        np.testing.assert_allclose(new[:, 2], post[:, 2])
        np.testing.assert_allclose(new[:, 3], post[:, 3])
        self.assertAlmostEqual(d["binding_hour_share"], 0.25)

    def test_caps_then_refills_other_rows(self):
        pm = np.array([100.0, 100.0])
        pre = np.ones((2, 1))
        post = np.array([[0.2], [1.0]])  # row 0 has only 20 MW available (80 MW events)
        rate = np.array([0.5, 0.5])
        new, d = allocate_crow_residual(pm, pre, post, rate, np.array([180.0]))
        # residual 100: row 0 capped at 20, row 1 takes the other 80
        np.testing.assert_allclose(new[:, 0], [0.0, 0.2])
        self.assertAlmostEqual(d["unplaced_gw_mean"], 0.0)

    def test_unplaceable_is_reported_not_forced(self):
        pm = np.array([100.0])
        new, d = allocate_crow_residual(
            pm, np.ones((1, 1)), np.ones((1, 1)), np.array([0.1]), np.array([250.0])
        )
        self.assertEqual(new[0, 0], 0.0)
        self.assertAlmostEqual(d["unplaced_gw_mean"], 0.15)

    def test_edge_runs_are_not_events(self):
        post = np.ones((1, 2000))
        post[0, :800] = 0.0  # dark from 1 January for > 30 days: pre-COD
        live = edge_live(post)
        self.assertFalse(live[0, :800].any())
        self.assertTrue(live[0, 800:].all())
        pm = np.array([100.0])
        _, d = allocate_crow_residual(
            pm, np.ones((1, 2000)), post, np.array([0.1]), np.full(2000, 50.0)
        )
        # no event counted on the pre-COD run, and nothing placed there
        self.assertAlmostEqual(d["event_gw_mean"], 0.0)
        self.assertAlmostEqual(d["placed_gw_mean"], 0.05 * 1200 / 2000)


class TestAvailabilitySeam(unittest.TestCase):
    """Armed, gas rows leave the statistical terms and record their key; coal never moves."""

    def setUp(self):
        self.cfg = ScenarioConfig(
            iso="SPP", mode="backcast", wefor_multiplier=0.7, coal_drop_pof=True
        )

    def test_off_is_byte_identical(self):
        np.testing.assert_array_equal(_avail(self.cfg), _avail(self.cfg, None))

    def test_armed_zeroes_gas_statistical_terms_and_keys_them(self):
        base = _avail(self.cfg)
        rate: dict[int, float] = {}
        armed = _avail(self.cfg, rate)
        self.assertEqual(sorted(rate), [0, 1])
        np.testing.assert_array_equal(base[2], armed[2])  # coal untouched
        month = arrays._hour_to_month_index(T) + 1
        for g, grp, age in ((0, "CT_PEAKER", 2024 - 2015), (1, "ST_GAS", 2024 - 1975)):
            pof, wefor, derate = arrays._thermal_outage(grp, age)
            jan = armed[g, month == 1]
            np.testing.assert_allclose(jan, 1.0 - derate)
            self.assertGreater(float(armed[g].mean()), float(base[g].mean()))
        # key = annual statistical rate: CT keeps its shoulder POF, ST's POF is dropped
        shoulder = np.isin(month, list(arrays._CC_SHOULDER_MONTHS)).mean()
        pof, wefor, _ = arrays._thermal_outage("CT_PEAKER", 2024 - 2015)
        self.assertAlmostEqual(rate[0], wefor * 0.7 + pof * shoulder)
        _, wefor_st, _ = arrays._thermal_outage("ST_GAS", 2024 - 1975)
        self.assertAlmostEqual(rate[1], wefor_st * 0.7)


class TestConfigAndData(unittest.TestCase):
    """SPP-only, exclusive with the CT LOLE swap, off keeps the key; the committed series loads."""

    def test_spp_only_and_exclusive(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(iso="MISO", spp_gas_crow_residual_outage=True)
        with self.assertRaises(ValueError):
            ScenarioConfig(
                iso="SPP", spp_gas_crow_residual_outage=True, spp_ct_lole_efor=True
            )

    def test_default_off_keeps_key(self):
        a = ScenarioConfig(iso="SPP")
        self.assertFalse(a.spp_gas_crow_residual_outage)
        b = ScenarioConfig(iso="SPP", spp_gas_crow_residual_outage=True)
        self.assertNotEqual(a.cache_key(), b.cache_key())

    def test_published_series_on_model_clock(self):
        s = spp_published_gas_outage_mw(2024, T)
        self.assertEqual(s.shape, (T,))
        self.assertGreater(np.isfinite(s).mean(), 0.999)
        # DESIGN s2: 9.66 GW annual mean (2024)
        self.assertAlmostEqual(float(np.nanmean(s)) / 1e3, 9.66, delta=0.02)


if __name__ == "__main__":
    unittest.main()
