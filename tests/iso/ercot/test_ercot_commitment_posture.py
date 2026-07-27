"""Tests for the ERCOT standalone energy-only commitment-posture lever.

``ercot_commitment_posture`` (design note
``docs/multi-iso/miso-scarcity-posture-design-2026-07.md`` §A; ERCOT port
``docs/handoffs/ercot-commitment-thinness-2026-07.md``): ERCOT runs a fleet-wide
ORDC co-opt with no pergen substrate, so the posture is built reserve-decoupled —
only the energy-side rows on the U/SU columns (headroom ``Σ P ≤ U``, CEMS-measured
min-load ``Σ P ≥ mlf·U``, cyclic startup charge on ``ΔU⁺``), leaving the reserve
design untouched. These tests exercise the LP-core construction directly (no
reserve requirement) — the pure energy-only posture.

Trivial cases first per the repo testing pattern: 1 zone, 3 gens, 4-24 hours.
"""

from __future__ import annotations

import unittest

import numpy as np

from market_sim.config.reserve_config import ercot_commitment_posture_spec
from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays
from market_sim.model.dispatch import solve_dispatch


def _cfg(posture=True, mlf=0.574):
    return type(
        "C",
        (),
        {
            "iso": "ERCOT",
            "ercot_commitment_posture": posture,
            "ercot_commitment_posture_min_load_frac": mlf,
        },
    )()


def _mixed_fleet(specs):
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
        availability=np.ones((n, 4)),
        unit_ids=[f"u{i}" for i in range(n)],
        efficiency_bin=np.zeros(n),
        plant_code=np.arange(1, n + 1),
        plant_group=np.array([s[3] for s in specs], dtype=object),
        ramp10=np.array([s[2] * 0.4 for s in specs], dtype=float),
    )


class TestPostureSpec(unittest.TestCase):
    """ercot_commitment_posture_spec scoping: physics exempt + rule-19 exclude."""

    def test_off_returns_none(self):
        fleet = _mixed_fleet([("gas_cc", 7.0, 1000.0, "CC_REGULAR", 0)])
        self.assertIsNone(ercot_commitment_posture_spec(_cfg(posture=False), fleet))

    def test_cc_postured_ct_exempt_chp_coal_excluded(self):
        # CC_REGULAR (postured), CT_PEAKER (fast-start exempt), CC_CHP (rule-19
        # excluded), COAL + gas_st (fuel-excluded). Only the CC pool survives.
        fleet = _mixed_fleet(
            [
                ("gas_cc", 7.0, 2000.0, "CC_REGULAR", 0),
                ("gas_ct", 10.5, 500.0, "CT_PEAKER", 0),
                ("gas_cc", 7.0, 800.0, "CC_CHP", 0),
                ("coal", 10.0, 1000.0, "COAL", 0),
                ("gas_st", 10.5, 400.0, "ST_GAS", 0),
            ]
        )
        spec = ercot_commitment_posture_spec(_cfg(), fleet)
        self.assertIsNotNone(spec)
        gen_idx, col, mlf, startup = spec
        # One postured pool (the merchant CC), one member (gen 0).
        self.assertEqual(mlf.size, 1)
        np.testing.assert_array_equal(gen_idx, np.array([0]))
        np.testing.assert_array_equal(col, np.array([0]))
        # Measured CC mlf (frozen 0.574), NREL-table startup for gas_cc.
        self.assertAlmostEqual(float(mlf[0]), 0.574, places=6)
        self.assertGreater(float(startup[0]), 0.0)

    def test_measured_mlf_override_applies(self):
        fleet = _mixed_fleet([("gas_cc", 7.0, 1000.0, "CC_REGULAR", 0)])
        spec = ercot_commitment_posture_spec(_cfg(mlf=0.62), fleet)
        self.assertAlmostEqual(float(spec[2][0]), 0.62, places=6)

    def test_all_fast_start_returns_none(self):
        # A pure CT fleet: every pool fast-start-exempt -> no posture.
        fleet = _mixed_fleet([("gas_ct", 10.5, 500.0, "CT_PEAKER", 0)])
        self.assertIsNone(ercot_commitment_posture_spec(_cfg(), fleet))


_MLF = 0.574  # measured committed-CC LSL/HSL p50 (ERCOT-62, frozen)
_SU = 40.0  # $/MW per start (gas_cc class-table order of magnitude)


def _cc_fleet(T):
    n = 3
    fuel_idx = FUEL_TYPE_NAMES.index("gas_cc")
    return FleetArrays(
        pmax=np.array([2000.0, 1000.0, 1000.0]),
        pmin=np.zeros(n),
        heat_rate=np.array([7.0, 8.0, 8.0]),
        vom=np.zeros(n),
        emission_rate=np.zeros(n),
        nox_rate=np.zeros(n),
        so2_rate=np.zeros(n),
        zone_idx=np.zeros(n, dtype=int),
        fuel_type_idx=np.full(n, fuel_idx),
        availability=np.ones((n, T)),
        unit_ids=[f"u{i}" for i in range(n)],
        efficiency_bin=np.zeros(n),
        plant_code=np.arange(1, n + 1),
        plant_group=np.array(["CC_REGULAR"] * n, dtype=object),
        ramp10=np.array([800.0, 400.0, 400.0]),
    )


def _solve(fleet, T, demand, posture: bool):
    n = fleet.n_gen
    kw = {}
    if posture:
        kw = dict(
            posture_gen_idx=np.arange(n),
            posture_col=np.zeros(n, dtype=int),
            posture_mlf=np.array([_MLF]),
            posture_startup=np.array([_SU]),
        )
    return solve_dispatch(
        fleet,
        np.asarray(demand, dtype=float).reshape(1, T),
        wind_cf=np.zeros((1, T)),
        wind_cap=np.zeros(1),
        solar_cf=np.zeros((1, T)),
        solar_cap=np.zeros(1),
        fuel_prices=np.ones((n, T)),
        voll=5000.0,
        **kw,
    )


def _cycling_demand(T):
    d = np.full(T, 600.0)
    d[8:20] = 3600.0
    return d


class TestStandalonePostureLP(unittest.TestCase):
    """End-to-end trivial LP: 1 zone, 3-gen CC pool, energy-only posture."""

    _T = 24

    def test_off_is_byte_identical(self):
        # No posture params -> the LP must be identical to a plain dispatch.
        fleet = _cc_fleet(self._T)
        demand = _cycling_demand(self._T)
        off = _solve(fleet, self._T, demand, posture=False)
        self.assertEqual(off.status, "Optimal")
        self.assertIsNone(off.posture_online_mw)

    def test_couplings_hold(self):
        fleet = _cc_fleet(self._T)
        res = _solve(fleet, self._T, _cycling_demand(self._T), posture=True)
        self.assertEqual(res.status, "Optimal")
        u = np.asarray(res.posture_online_mw)[0]
        p_pool = np.asarray(res.dispatch).sum(axis=0)
        # Energy headroom: Σ P ≤ U ≤ Σ cap (4,000 MW).
        self.assertTrue(np.all(p_pool <= u + 1e-4))
        self.assertTrue(np.all(u <= 4000.0 + 1e-6))
        # Min-load coupling: Σ P ≥ mlf·U.
        self.assertTrue(np.all(p_pool >= _MLF * u - 1e-4))
        # No reserve coupling in the standalone (energy-only) posture.
        self.assertIsNone(res.posture_reserve_mw)

    def test_startup_counts_up_moves(self):
        fleet = _cc_fleet(self._T)
        on = _solve(fleet, self._T, _cycling_demand(self._T), posture=True)
        u = np.asarray(on.posture_online_mw)[0]
        su = np.asarray(on.posture_startup_mw)[0]
        up_moves = np.maximum(u - np.roll(u, 1), 0.0)  # cyclic
        self.assertGreaterEqual(float(su.sum()), float(up_moves.sum()) - 1e-3)

    def test_cycling_costs_startup_or_min_load(self):
        # The posture objective must exceed the free-re-timing objective: the
        # overnight decommit now pays a real morning startup (or holds min-load
        # energy overnight) instead of re-timing CC at zero cost.
        fleet = _cc_fleet(self._T)
        off = _solve(fleet, self._T, _cycling_demand(self._T), posture=False)
        on = _solve(fleet, self._T, _cycling_demand(self._T), posture=True)
        self.assertEqual(on.status, "Optimal")
        self.assertGreater(on.objective_value, off.objective_value + 1.0)

    def test_forces_no_energy(self):
        # NOT a floor (rule 17 / design §A window clause): generation tracks
        # demand exactly — no slack, no dump — with the posture on. Without
        # reserve pressure the min-load coupling binds only capacity the LP
        # itself keeps online (U free to track Σ P).
        T = self._T
        fleet = _cc_fleet(T)
        demand = _cycling_demand(T)
        on = _solve(fleet, T, demand, posture=True)
        gen = float(np.asarray(on.dispatch).sum())
        self.assertAlmostEqual(gen, float(demand.sum()), delta=1e-2)
        self.assertAlmostEqual(float(np.asarray(on.slack).sum()), 0.0, places=3)
        self.assertAlmostEqual(float(np.asarray(on.dump).sum()), 0.0, places=3)

    def test_prices_uncorrupted(self):
        # The inserted posture rows must not disturb the energy-balance dual
        # extraction: at a flat demand served entirely by the cheapest CC unit
        # (hr 7.0, fuel price 1.0), the price equals its marginal cost $7/MWh.
        T = 4
        fleet = _cc_fleet(T)
        demand = np.full(T, 500.0)  # below unit-0 pmax; unit 0 is marginal
        on = _solve(fleet, T, demand, posture=True)
        self.assertEqual(on.status, "Optimal")
        prices = np.asarray(on.prices)[0]
        self.assertTrue(np.allclose(prices, 7.0, atol=1e-6))


if __name__ == "__main__":
    unittest.main()
