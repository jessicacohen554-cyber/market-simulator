"""Tests for the MISO pooled linear commitment-posture lever.

``miso_commitment_posture`` (design note
``docs/multi-iso/miso-scarcity-posture-design-2026-07.md`` §A): per postured
(zone × fuel-class) pergen pool, an online-capacity variable U[p,t] with joint
``Σ P + R ≤ U``, CEMS-measured min-load coupling ``Σ P ≥ mlf·U``, a cyclic
startup charge on ``ΔU⁺``, and the reserve cap online-gated ``R ≤ ρ(t)·U``.

Trivial cases first per the repo testing pattern: 1 zone, 3 gens, 4-24 hours.
"""

from __future__ import annotations

import unittest

import numpy as np

from market_sim.config.reserve_config import (
    build_reserve_dispatch_kwargs,
    get_reserve_design,
)
from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays
from market_sim.model.dispatch import VariableLayout, solve_dispatch


def _fleet(T, fuel, heat_rates, pmax, plant_group, ramp10):
    n = len(pmax)
    fuel_idx = FUEL_TYPE_NAMES.index(fuel)
    return FleetArrays(
        pmax=np.asarray(pmax, dtype=float),
        pmin=np.zeros(n),
        heat_rate=np.asarray(heat_rates, dtype=float),
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
        plant_group=np.array([plant_group] * n, dtype=object),
        ramp10=np.asarray(ramp10, dtype=float),
    )


def _cfg(posture: bool):
    return type(
        "C",
        (),
        {
            "iso": "MISO",
            "weather_year": 2024,
            "miso_reserve_pergen": True,
            "miso_commitment_posture": posture,
        },
    )()


def _design_kwargs(fleet, T, posture: bool):
    design = get_reserve_design(_cfg(posture), fleet, T, ["z0"])
    kw = build_reserve_dispatch_kwargs(design)
    keys = (
        "reserve_pergen_gen_idx",
        "reserve_pergen_col",
        "reserve_pergen_ramp10",
        "reserve_posture_pools",
        "reserve_posture_mlf",
        "reserve_posture_startup",
    )
    extra = {k: kw[k] for k in keys if k in kw}
    return design, kw, extra


def _solve(fleet, T, demand, posture: bool):
    n = fleet.n_gen
    _design, kw, extra = _design_kwargs(fleet, T, posture)
    return solve_dispatch(
        fleet,
        np.asarray(demand, dtype=float).reshape(1, T),
        wind_cf=np.zeros((1, T)),
        wind_cap=np.zeros(1),
        solar_cf=np.zeros((1, T)),
        solar_cap=np.zeros(1),
        fuel_prices=np.ones((n, T)),
        voll=5000.0,
        reserve_requirement=kw["reserve_requirement"],
        reserve_eligible=kw["reserve_eligible"],
        ordc_penalties=kw["ordc_penalties"],
        ordc_step_widths=kw["ordc_step_widths"],
        **extra,
    )


class TestLayout(unittest.TestCase):
    """The posture block leaves the layout byte-identical when off."""

    def test_off_is_identical(self):
        base = VariableLayout(n_gen=3, n_zones=1, n_storage=0, n_links=0, T=4)
        off = VariableLayout(
            n_gen=3, n_zones=1, n_storage=0, n_links=0, T=4, n_posture=0
        )
        self.assertEqual(base.vars_per_hour, off.vars_per_hour)
        self.assertEqual(base.total_columns, off.total_columns)

    def test_on_appends_two_blocks(self):
        on = VariableLayout(
            n_gen=3, n_zones=1, n_storage=0, n_links=0, T=4, n_posture=2
        )
        off = VariableLayout(n_gen=3, n_zones=1, n_storage=0, n_links=0, T=4)
        self.assertEqual(on.vars_per_hour, off.vars_per_hour + 4)
        self.assertEqual(on._posture_u_off, off.vars_per_hour)
        self.assertEqual(on._posture_su_off, off.vars_per_hour + 2)


class TestPostureParams(unittest.TestCase):
    """Pool posture parameters gate on physics, never class names (rule 18)."""

    def test_fast_start_ct_pool_exempt(self):
        # gas CT, hr 10.5 -> frame class ($24.5/MW, min-down 1 h): both
        # fast-start thresholds met, so the pool carries NO posture entry.
        T = 4
        fleet = _fleet(
            T,
            "gas_ct",
            [10.5, 10.5, 10.5],
            [100.0, 100.0, 100.0],
            "CT_PEAKER",
            [100.0, 100.0, 100.0],
        )
        design, kw, extra = _design_kwargs(fleet, T, posture=True)
        self.assertTrue(design.posture_pools is None or design.posture_pools.size == 0)
        self.assertNotIn("reserve_posture_pools", kw)

    def test_slow_cc_pool_postured_with_class_params(self):
        # gas CC (f-class + older): capacity-weighted startup ≈ $36/MW ≥ 30,
        # min-down ≈ 5 h > 2 — postured. mlf falls back to the WWSIS-2 CC
        # class value (0.52) because test plant codes are not in the MISO
        # thermal-tranches artifact.
        T = 4
        fleet = _fleet(
            T,
            "gas_cc",
            [7.0, 8.0, 8.0],
            [2000.0, 1000.0, 1000.0],
            "CC_REGULAR",
            [800.0, 400.0, 400.0],
        )
        design, kw, extra = _design_kwargs(fleet, T, posture=True)
        self.assertEqual(design.posture_pools.size, 1)
        self.assertAlmostEqual(float(design.posture_mlf[0]), 0.52, places=6)
        su = float(design.posture_startup[0])
        self.assertGreater(su, 30.0)
        self.assertLess(su, 50.0)

    def test_off_emits_nothing(self):
        T = 4
        fleet = _fleet(
            T,
            "gas_cc",
            [7.0, 8.0, 8.0],
            [2000.0, 1000.0, 1000.0],
            "CC_REGULAR",
            [800.0, 400.0, 400.0],
        )
        design, kw, extra = _design_kwargs(fleet, T, posture=False)
        self.assertIsNone(design.posture_pools)
        self.assertNotIn("reserve_posture_pools", kw)


class TestPostureLP(unittest.TestCase):
    """End-to-end trivial LP: 1 zone, 3-gen CC pool, 24 hours."""

    _T = 24

    def _cc_fleet(self):
        return _fleet(
            self._T,
            "gas_cc",
            [7.0, 8.0, 8.0],
            [2000.0, 1000.0, 1000.0],
            "CC_REGULAR",
            [800.0, 400.0, 400.0],
        )

    def _cycling_demand(self):
        # Day 3,600 MW (h8-19), night 600 MW: night sits far below
        # mlf × day-online capacity, so the free-re-timing LP would idle the
        # fleet overnight and restart free; the posture must either hold
        # min-load or pay the startup charge.
        d = np.full(self._T, 600.0)
        d[8:20] = 3600.0
        return d

    def test_feasible_and_couplings_hold(self):
        fleet = self._cc_fleet()
        res = _solve(fleet, self._T, self._cycling_demand(), posture=True)
        self.assertEqual(res.status, "Optimal")
        u = np.asarray(res.posture_online_mw)[0]
        p_pool = np.asarray(res.dispatch).sum(axis=0)
        r_pool = np.asarray(res.posture_reserve_mw)[0]
        # Joint online headroom: P + R ≤ U; capacity bound: U ≤ 4,000.
        self.assertTrue(np.all(p_pool + r_pool <= u + 1e-4))
        self.assertTrue(np.all(u <= 4000.0 + 1e-6))
        # Min-load coupling: P ≥ mlf·U.
        self.assertTrue(np.all(p_pool >= 0.52 * u - 1e-4))

    def test_cycling_costs_startup_or_min_load(self):
        # The posture objective must exceed the free-re-timing objective:
        # the overnight decommit now pays a real morning startup (or holds
        # min-load energy overnight) instead of re-timing at zero cost.
        fleet = self._cc_fleet()
        off = _solve(fleet, self._T, self._cycling_demand(), posture=False)
        on = _solve(fleet, self._T, self._cycling_demand(), posture=True)
        self.assertEqual(on.status, "Optimal")
        self.assertGreater(on.objective_value, off.objective_value + 1.0)
        su = np.asarray(on.posture_startup_mw)[0]
        u = np.asarray(on.posture_online_mw)[0]
        p_pool = np.asarray(on.dispatch).sum(axis=0)
        held_min_load = float(p_pool.min()) > 600.0 + 1e-3  # night > demand?
        paid_startup = float(su.sum()) > 1.0
        # SU counts every up-move of U (cyclic).
        up_moves = np.maximum(u - np.roll(u, 1), 0.0)
        self.assertGreaterEqual(float(su.sum()), float(up_moves.sum()) - 1e-3)
        self.assertTrue(held_min_load or paid_startup)

    def test_offline_capacity_backs_no_reserve(self):
        # Low flat demand (600 MW) vs a ~2,400 MW requirement: without the
        # posture, idle offline headroom backs reserve for FREE (the gate-4
        # relief channel). With it, reserve must come from ONLINE capacity —
        # R ≤ ρ(t)·U — so serving the requirement means holding capacity
        # online and paying its min-load energy: a real provision cost in
        # the objective, exactly the economics the free-headroom LP lacked.
        fleet = self._cc_fleet()
        demand = np.full(self._T, 600.0)
        off = _solve(fleet, self._T, demand, posture=False)
        on = _solve(fleet, self._T, demand, posture=True)
        self.assertEqual(on.status, "Optimal")
        u = np.asarray(on.posture_online_mw)[0]
        r = np.asarray(on.posture_reserve_mw)[0]
        # Online ramp gate: R ≤ ρ·U with ρ = Σ ramp10 / Σ cap = 1600/4000.
        self.assertTrue(np.all(r <= 0.4 * u + 1e-4))
        # The LP held capacity online ABOVE demand to back reserve (U > P
        # requires min-load burn) and paid a real provision cost for it.
        p_pool = np.asarray(on.dispatch).sum(axis=0)
        self.assertGreater(float(u.mean()), float(p_pool.mean()) + 100.0)
        # Both arms pay the same 800 MW deliverability shortfall (Σ ramp10 =
        # 1,600 < 2,400); the posture arm additionally pays the real
        # min-load burn of the capacity it holds online (~1,480 MW dumped at
        # ~$7/MWh ≈ $250k/yr-of-24h) — free idle headroom no longer exists.
        self.assertGreater(
            on.objective_value,
            off.objective_value + 100_000.0,
            "reserve provision must carry a real min-load/startup cost",
        )

    def test_forces_no_energy_absent_reserve_pressure(self):
        # NOT a floor (rule 17 / design §A window clause): with the reserve
        # requirement neutralized (1 MW), the posture must not force one MWh —
        # generation tracks demand exactly (U is free to track P: the
        # min-load coupling binds only capacity the LP itself holds online).
        # Under a REAL requirement the LP may hold min-load energy online for
        # reserves — that is its economic choice against the published curve,
        # not a floor (covered by test_offline_capacity_backs_no_reserve).
        T = self._T
        fleet = self._cc_fleet()
        demand = self._cycling_demand()
        _design, kw, extra = _design_kwargs(fleet, T, posture=True)
        on = solve_dispatch(
            fleet,
            demand.reshape(1, T),
            wind_cf=np.zeros((1, T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, T)),
            solar_cap=np.zeros(1),
            fuel_prices=np.ones((3, T)),
            voll=5000.0,
            reserve_requirement=np.ones(T),  # neutralized
            reserve_eligible=kw["reserve_eligible"],
            ordc_penalties=kw["ordc_penalties"],
            ordc_step_widths=kw["ordc_step_widths"],
            **extra,
        )
        gen = float(np.asarray(on.dispatch).sum())
        self.assertAlmostEqual(gen, float(demand.sum()), delta=1e-3)
        self.assertAlmostEqual(float(np.asarray(on.slack).sum()), 0.0, places=4)
        self.assertAlmostEqual(float(np.asarray(on.dump).sum()), 0.0, places=4)


def _cfg_pjm(posture: bool):
    return type(
        "C",
        (),
        {
            "iso": "PJM",
            "weather_year": 2024,
            "energy_reserve_coopt": True,
            "pjm_reserve_pergen": True,
            "pjm_commitment_posture": posture,
        },
    )()


class TestPjmPortSharesMechanism(unittest.TestCase):
    """The PJM port reuses MISO's _posture_pool_params verbatim — not a fork.

    Same fleet through both ISO designs must produce identical posture pools /
    parameters, and PJM's default-off path must be a byte-identical no-op
    (the pjm-81 ablation-twin guarantee).
    """

    def _pjm_design(self, fleet, T, posture: bool):
        return get_reserve_design(_cfg_pjm(posture), fleet, T, ["z0"])

    def test_pjm_off_emits_no_posture(self):
        T = 4
        fleet = _fleet(
            T,
            "gas_cc",
            [7.0, 8.0, 8.0],
            [2000.0, 1000.0, 1000.0],
            "CC_REGULAR",
            [800.0, 400.0, 400.0],
        )
        design = self._pjm_design(fleet, T, posture=False)
        self.assertIsNone(design.posture_pools)
        kw = build_reserve_dispatch_kwargs(design)
        self.assertNotIn("reserve_posture_pools", kw)

    def test_pjm_slow_cc_pool_postured_with_class_params(self):
        # Same fleet as the MISO TestPostureParams CC case: shared code must
        # produce the same postured pool, mlf (WWSIS-2 CC gap-fill 0.52) and
        # class startup ($30-$50/MW).
        T = 4
        fleet = _fleet(
            T,
            "gas_cc",
            [7.0, 8.0, 8.0],
            [2000.0, 1000.0, 1000.0],
            "CC_REGULAR",
            [800.0, 400.0, 400.0],
        )
        design = self._pjm_design(fleet, T, posture=True)
        self.assertEqual(design.posture_pools.size, 1)
        self.assertAlmostEqual(float(design.posture_mlf[0]), 0.52, places=6)
        su = float(design.posture_startup[0])
        self.assertGreater(su, 30.0)
        self.assertLess(su, 50.0)

    def test_pjm_fast_start_ct_pool_exempt(self):
        # gas CT frame class: both fast-start thresholds met -> no posture
        # column (rule 18 parameter gate, shared with MISO).
        T = 4
        fleet = _fleet(
            T,
            "gas_ct",
            [10.5, 10.5, 10.5],
            [100.0, 100.0, 100.0],
            "CT_PEAKER",
            [100.0, 100.0, 100.0],
        )
        design = self._pjm_design(fleet, T, posture=True)
        self.assertTrue(design.posture_pools is None or design.posture_pools.size == 0)

    def test_pjm_matches_miso_pool_params(self):
        # The two ISO designs, same fleet: posture pools/params identical
        # (the port is not a fork).
        T = 4
        fleet = _fleet(
            T,
            "gas_cc",
            [7.0, 8.0, 8.0],
            [2000.0, 1000.0, 1000.0],
            "CC_REGULAR",
            [800.0, 400.0, 400.0],
        )
        pjm = self._pjm_design(fleet, T, posture=True)
        miso = get_reserve_design(_cfg(True), fleet, T, ["z0"])
        np.testing.assert_array_equal(pjm.posture_pools, miso.posture_pools)
        np.testing.assert_allclose(pjm.posture_mlf, miso.posture_mlf)
        np.testing.assert_allclose(pjm.posture_startup, miso.posture_startup)


if __name__ == "__main__":
    unittest.main()
