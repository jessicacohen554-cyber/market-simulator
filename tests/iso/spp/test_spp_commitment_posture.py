"""Tests for the SPP standalone commitment posture with min-up / min-down (SPP-102).

``spp_commitment_posture`` (``docs/handoffs/DESIGN-spp-102-cc-commitment-state-2026-09-29.md``)
reuses the ERCOT standalone energy-only posture (headroom, measured min-load,
startup charge on the pooled online capacity U) and adds the min-up / min-down
coupling. Trivial cases first per the repo testing pattern: 1 zone, a 1-3 gen CC
pool, 24 hours.
"""

from __future__ import annotations

import unittest

import numpy as np

from market_sim.config.constants import (
    SPP_GAS_BRIDGE_MIN_LOAD_FRAC,
    SPP_GAS_BRIDGE_MIN_RUN_HOURS,
    SPP_POSTURE_MIN_DOWN_HOURS,
)
from market_sim.config.reserve_config import (
    ercot_commitment_posture_spec,
    spp_commitment_posture_spec,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays
from market_sim.model.dispatch import solve_dispatch


def _cfg(iso="SPP", on=True):
    return type("C", (), {"iso": iso, "spp_commitment_posture": on})()


def _fleet(specs, T=4):
    """specs: list of (fuel, heat_rate, pmax, plant_group, zone)."""
    n = len(specs)
    return FleetArrays(
        pmax=np.array([s[2] for s in specs], dtype=float),
        pmin=np.zeros(n),
        heat_rate=np.array([s[1] for s in specs], dtype=float),
        vom=np.zeros(n),
        emission_rate=np.zeros(n),
        nox_rate=np.zeros(n),
        so2_rate=np.zeros(n),
        zone_idx=np.array([s[4] for s in specs], dtype=int),
        fuel_type_idx=np.array([FUEL_TYPE_NAMES.index(s[0]) for s in specs]),
        availability=np.ones((n, T)),
        unit_ids=[f"u{i}" for i in range(n)],
        efficiency_bin=np.zeros(n),
        plant_code=np.arange(1, n + 1),
        plant_group=np.array([s[3] for s in specs], dtype=object),
        ramp10=np.array([s[2] * 0.4 for s in specs], dtype=float),
    )


class TestConfig(unittest.TestCase):
    """Field gating and cache-key neutrality."""

    def test_default_off_keeps_key(self):
        a = ScenarioConfig(iso="SPP")
        self.assertFalse(a.spp_commitment_posture)
        b = ScenarioConfig(iso="SPP", spp_commitment_posture=True)
        self.assertNotEqual(a.cache_key(), b.cache_key())

    def test_spp_only(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(iso="ERCOT", spp_commitment_posture=True)

    def test_exclusive_with_bridge(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(
                iso="SPP", spp_commitment_posture=True, spp_gas_commitment_bridge=True
            )


class TestSpec(unittest.TestCase):
    """Scoping and parameters of spp_commitment_posture_spec."""

    def test_off_or_wrong_iso_returns_none(self):
        f = _fleet([("gas_cc", 7.0, 1000.0, "CC_REGULAR", 0)])
        self.assertIsNone(spp_commitment_posture_spec(_cfg(on=False), f))
        self.assertIsNone(spp_commitment_posture_spec(_cfg(iso="ERCOT"), f))

    def test_cc_postured_with_measured_params(self):
        f = _fleet(
            [
                ("gas_cc", 7.0, 2000.0, "CC_REGULAR", 0),
                ("gas_cc", 7.0, 1000.0, "CC_REGULAR", 0),
                ("gas_ct", 10.5, 500.0, "CT_PEAKER", 0),
                ("gas_cc", 7.0, 800.0, "CC_CHP", 0),
                ("gas_st", 10.5, 400.0, "ST_GAS", 0),
            ]
        )
        gen_idx, col, mlf, startup, up, down = spp_commitment_posture_spec(_cfg(), f)
        # Two CC pools (one per PLANT, same zone); CT fast-start exempt; CHP / ST
        # excluded.
        self.assertEqual(mlf.size, 2)
        np.testing.assert_array_equal(np.sort(gen_idx), np.array([0, 1]))
        np.testing.assert_allclose(mlf, SPP_GAS_BRIDGE_MIN_LOAD_FRAC["gas_cc"])
        np.testing.assert_array_equal(up, int(SPP_GAS_BRIDGE_MIN_RUN_HOURS["gas_cc"]))
        np.testing.assert_array_equal(down, int(SPP_POSTURE_MIN_DOWN_HOURS))
        self.assertTrue(np.all(startup > 0))

    def test_ercot_spec_unchanged_by_refactor(self):
        f = _fleet([("gas_cc", 7.0, 1000.0, "CC_REGULAR", 0)])
        cfg = type(
            "C",
            (),
            {
                "iso": "ERCOT",
                "ercot_commitment_posture": True,
                "ercot_commitment_posture_min_load_frac": 0.574,
            },
        )()
        spec = ercot_commitment_posture_spec(cfg, f)
        self.assertEqual(len(spec), 4)
        self.assertAlmostEqual(float(spec[2][0]), 0.574)


_T = 24
_MLF = 0.209
_SU = 40.0


def _cc(T=_T, avail=None):
    f = _fleet([("gas_cc", 7.0, 1000.0, "CC_REGULAR", 0)], T=T)
    if avail is not None:
        f.availability[:] = avail
    return f


def _solve(fleet, demand, *, up=None, down=None, gas=1.0, coal_cap=0.0, su=_SU):
    """One CC pool vs. a cheap wind resource that can serve everything overnight."""
    T = demand.size
    kw = dict(
        posture_gen_idx=np.array([0]),
        posture_col=np.array([0]),
        posture_mlf=np.array([_MLF]),
        posture_startup=np.array([su]),
    )
    if up is not None:
        kw["posture_min_up_h"] = np.array([up])
    if down is not None:
        kw["posture_min_down_h"] = np.array([down])
    return solve_dispatch(
        fleet,
        demand.reshape(1, T),
        wind_cf=np.full((1, T), 1.0),
        wind_cap=np.array([coal_cap]),
        solar_cf=np.zeros((1, T)),
        solar_cap=np.zeros(1),
        fuel_prices=np.full((fleet.n_gen, T), gas),
        voll=5000.0,
        **kw,
    )


def _two_peak_demand():
    # Peak 06-09 and 16-19; a 6 h valley between the peaks where wind covers it.
    d = np.full(_T, 300.0)
    d[6:10] = 900.0
    d[16:20] = 900.0
    return d


class TestMinUpDownLP(unittest.TestCase):
    """End-to-end trivial LP: the time rows hold, and they bind as designed."""

    def test_no_time_rows_is_the_ercot_block(self):
        # Without min-up/down the posture is the pre-existing construction.
        r = _solve(_cc(), _two_peak_demand(), coal_cap=400.0)
        self.assertEqual(r.status, "Optimal")

    def test_min_up_holds_started_capacity(self):
        up = 12
        r = _solve(_cc(), _two_peak_demand(), up=up, coal_cap=400.0)
        self.assertEqual(r.status, "Optimal")
        u = np.asarray(r.posture_online_mw)[0]
        su = np.asarray(r.posture_startup_mw)[0]
        for t in range(_T):
            window = su[[(t - k) % _T for k in range(up)]].sum()
            self.assertGreaterEqual(u[t] + 1e-4, window)

    def test_min_down_blocks_quick_restart(self):
        down = 8
        r = _solve(_cc(), _two_peak_demand(), down=down, coal_cap=400.0)
        self.assertEqual(r.status, "Optimal")
        u = np.asarray(r.posture_online_mw)[0]
        su = np.asarray(r.posture_startup_mw)[0]
        for t in range(_T):
            lhs = su[[(t - k) % _T for k in range(down)]].sum() + u[(t - down) % _T]
            self.assertLessEqual(lhs, 1000.0 + 1e-4)

    def test_min_down_keeps_pool_on_through_short_valley(self):
        # Peaks need the WHOLE pool (1,400 MW = 400 wind + 1,000 CC). A near-free
        # start makes the pool stop through the 6 h valley (wind serves it); an
        # 8 h min-down forbids stopping capacity that must restart inside 8 h, so
        # the pool idles at min-load through the valley instead. (Clustered
        # semantics: capacity that never started may still start freely.)
        d = _two_peak_demand()
        d[d > 300.0] = 1400.0
        base = _solve(_cc(), d, coal_cap=400.0, su=0.01)
        held = _solve(_cc(), d, down=8, coal_cap=400.0, su=0.01)
        valley = slice(10, 16)
        p_base = np.asarray(base.dispatch)[0, valley].sum()
        p_held = np.asarray(held.dispatch)[0, valley].sum()
        self.assertLess(p_base, 1e-3)
        self.assertGreater(p_held, 6 * _MLF * 1000.0 - 1.0)
        self.assertGreater(held.objective_value, base.objective_value)

    def test_outage_never_infeasible(self):
        # Availability collapses mid-run; the allowance keeps both rows feasible.
        avail = np.ones(_T)
        avail[12:15] = 0.0
        r = _solve(_cc(avail=avail), _two_peak_demand(), up=15, down=8, coal_cap=400.0)
        self.assertEqual(r.status, "Optimal")
        u = np.asarray(r.posture_online_mw)[0]
        self.assertTrue(np.all(u[12:15] <= 1e-6))


class TestMarkupReconciliation(unittest.TestCase):
    """Rule 19: the P1 startup markup is zeroed on postured members (SPP only)."""

    def test_markup_zeroed_on_members(self):
        from market_sim.pipeline.solve import zero_posture_markup

        markup = np.full((3, 4), 5.0)
        cfg = ScenarioConfig(iso="SPP", spp_commitment_posture=True)
        out = zero_posture_markup(markup, cfg, {"posture_gen_idx": np.array([1])})
        np.testing.assert_array_equal(out[[0, 2]], 5.0)
        np.testing.assert_array_equal(out[1], 0.0)
        np.testing.assert_array_equal(markup, 5.0)  # input untouched

    def test_off_path_returns_same_object(self):
        from market_sim.pipeline.solve import zero_posture_markup

        markup = np.full((3, 4), 5.0)
        kw = {"posture_gen_idx": np.array([1])}
        self.assertIs(
            zero_posture_markup(markup, ScenarioConfig(iso="SPP"), kw), markup
        )
        ercot = type("C", (), {"ercot_commitment_posture": True})()
        self.assertIs(zero_posture_markup(markup, ercot, kw), markup)


if __name__ == "__main__":
    unittest.main()
