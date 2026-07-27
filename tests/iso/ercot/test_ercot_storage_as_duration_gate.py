"""Tests for the ERCOT endogenous-storage AS DURATION GATE (G5 follow-up).

The endogenous split (``ercot_storage_as_endogenous``) lets a battery choose
energy vs upward-AS, but nothing stopped a short-duration battery from selling a
long-duration product on its full power — so it held 2.1–2.4× the measured
60-Day DAM award (ercot32 root cause 1). ``ercot_storage_as_duration_gate`` adds
the published per-product State-of-Charge durations (RegUp/RRS 1 h, ECRS 2 h,
Non-Spin 4 h, ``ERCOT_AS_PRODUCT_DURATION_H``) as an LP-linear, vectorized gate
linking cleared storage AS to SOC — ``Σ_c dur_c·RS[c,z] ≤ Σ_{s∈z} SOC[s]``.

Built from the trivial case up (CLAUDE.md testing pattern): a 1-storage,
1-zone, 24-hour LP where a 1-hour battery offered a 4-hour product can only hold
a quarter of its power as that product, and everything above the requirement is
met by an ORDC shortfall. Every quantity is an LP variable; nothing is pinned.
"""

import unittest

import numpy as np

from market_sim.config.reserve_config import (
    ERCOT_AS_PRODUCT_DURATION_H,
    build_reserve_dispatch_kwargs,
    get_reserve_design,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import solve_dispatch
from market_sim.results.scarcity import nyiso_rcpf_product_shortfall_steps


def _fleet(specs, zone_names, hours):
    """Build a fleet from ``(fuel, pmax, mc)`` specs, all in zone 0."""
    gens = [
        Generator(
            unit_id=f"G{i}",
            name=f"G{i}",
            zone=zone_names[0],
            fuel_type=fuel,
            pmax_mw=pmax,
            pmin_mw=0.0,
            eford=0.0,
        )
        for i, (fuel, pmax, _mc) in enumerate(specs)
    ]
    fa = generators_to_fleet_arrays(gens, zone_names, hours=hours)
    mc = np.array([[s[2]] * hours for s in specs], dtype=float)
    return fa, mc


class TestDurationGateBinds(unittest.TestCase):
    """1 storage, 1 zone, 24 h: the SOC duration gate caps a 1-h battery's AS.

    A 20 MW / 20 MWh (1-hour) battery is the sole AS supplier for a 20 MW
    requirement priced dear (offer cap 5000 ≫ arbitrage). Ungated the battery
    holds the full 20 MW. With the duration gate the held AS is bounded by
    ``SOC / duration``: at duration 1 h the battery still reaches 20 MW, but at
    duration 4 h (Non-Spin) it can hold at most 20 MWh / 4 h = 5 MW — the rest
    goes short at the ORDC penalty.
    """

    PEAK = 12

    def _solve(self, duration_h, gate):
        hours = 24
        zone_names = ["Z0"]
        # Base unit (cheap) + peaker (dear); NEITHER reserve-eligible, so the
        # battery is the only AS supply.
        fleet, mc = _fleet(
            [("gas_cc", 100.0, 20.0), ("gas_ct", 50.0, 200.0)], zone_names, hours
        )
        demand = np.full((1, hours), 60.0)
        req = np.zeros((1, hours))
        req[0, self.PEAK] = 20.0
        pen, wid = nyiso_rcpf_product_shortfall_steps(20.0, 0.0, 5000.0, 10)
        not_eligible = np.zeros((1, fleet.n_gen), dtype=bool)
        dur = np.array([float(duration_h)]) if gate else None
        return solve_dispatch(
            fleet,
            demand,
            wind_cf=np.zeros((1, hours)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, hours)),
            solar_cap=np.zeros(1),
            mc=mc,
            voll=5000.0,
            storage_power_cap=np.array([20.0]),
            storage_energy_cap=np.array([20.0]),  # 1-HOUR battery
            storage_zone_idx=np.array([0]),
            eta_chg=1.0,
            eta_dis=1.0,
            reserve_storage=True,
            reserve_requirement=req,
            reserve_eligible=not_eligible,
            ordc_penalties=pen,
            ordc_step_widths=wid,
            reserve_balance_zone_mask=np.ones((1, 1), dtype=bool),
            reserve_balance_ordc_counts=np.array([pen.size]),
            reserve_balance_class=np.array([0]),
            reserve_headroom_eligible=not_eligible,
            reserve_headroom_products=np.ones((1, 1), dtype=bool),
            reserve_storage_duration_h=dur,
            T=hours,
        )

    def test_one_hour_battery_gated_at_four_hour_product(self):
        # A 1-h battery offered a 4-h product (Non-Spin) can hold at most a
        # quarter of its power (20 MWh / 4 h = 5 MW) as that AS.
        r = self._solve(duration_h=4.0, gate=True)
        srd = r.storage_reserve_dispatch
        self.assertIsNotNone(srd)  # exact split exposed
        held = float(srd[0, self.PEAK])
        self.assertLess(held, 5.0 + 1e-3)  # gate binds at SOC/duration
        self.assertGreater(held, 4.5)  # and does clear up to the gate

    def test_one_hour_battery_ungated_by_one_hour_product(self):
        # The same battery at a 1-h product duration holds its full 20 MW: the
        # gate SOC/1h = 20 MW does not bind.
        r = self._solve(duration_h=1.0, gate=True)
        held = float(r.storage_reserve_dispatch[0, self.PEAK])
        self.assertGreater(held, 19.0)

    def test_gate_monotonic_in_duration(self):
        # Held AS falls as the product duration lengthens: 1 h ≈ 20, 2 h ≈ 10,
        # 4 h ≈ 5 — the SOC/duration schedule, an LP outcome, not a tuned level.
        h1 = float(self._solve(1.0, gate=True).storage_reserve_dispatch[0, self.PEAK])
        h2 = float(self._solve(2.0, gate=True).storage_reserve_dispatch[0, self.PEAK])
        h4 = float(self._solve(4.0, gate=True).storage_reserve_dispatch[0, self.PEAK])
        self.assertGreater(h1, h2 + 4.0)
        self.assertGreater(h2, h4 + 4.0)
        self.assertAlmostEqual(h2, 10.0, delta=0.5)


class TestFlagOffByteIdentical(unittest.TestCase):
    """The gate off leaves the endogenous-split LP and kwargs untouched."""

    def _design_kwargs(self, gate):
        fleet, _mc = _fleet([("gas_cc", 100.0, 20.0)], ["Z0"], 24)
        cfg = ScenarioConfig(
            iso="ERCOT",
            weather_year=2024,
            hours=24,
            energy_reserve_coopt=True,
            ercot_multiproduct_as_coopt=True,
            ercot_as_forward_requirement=True,
            ercot_storage_as_endogenous=True,
            ercot_storage_as_duration_gate=gate,
        )
        load = np.full(24, 4e4)
        design = get_reserve_design(
            cfg,
            fleet,
            24,
            ["ERCOT"],
            system_load=load,
            wind_gen=load * 0,
            solar_gen=load * 0,
            sim_year=2024,
        )
        return design, build_reserve_dispatch_kwargs(design)

    def test_gate_off_emits_no_duration_kwarg(self):
        design, kw = self._design_kwargs(gate=False)
        self.assertIsNone(design.storage_duration_h)
        self.assertNotIn("reserve_storage_duration_h", kw)

    def test_gate_on_emits_published_durations(self):
        design, kw = self._design_kwargs(gate=True)
        self.assertIn("reserve_storage_duration_h", kw)
        np.testing.assert_allclose(
            kw["reserve_storage_duration_h"], np.asarray(ERCOT_AS_PRODUCT_DURATION_H)
        )

    def test_lp_byte_identical_when_durations_none(self):
        # Passing reserve_storage_duration_h=None must reproduce the pre-gate
        # endogenous LP exactly (storage pooled in the shared headroom).
        fleet, mc = _fleet([("gas_cc", 100.0, 20.0)], ["Z0"], 24)
        common = dict(
            wind_cf=np.zeros((1, 24)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, 24)),
            solar_cap=np.zeros(1),
            mc=mc,
            voll=5000.0,
            storage_power_cap=np.array([20.0]),
            storage_energy_cap=np.array([40.0]),
            storage_zone_idx=np.array([0]),
            eta_chg=1.0,
            eta_dis=1.0,
            reserve_storage=True,
            reserve_requirement=np.full((1, 24), 10.0),
            reserve_eligible=np.zeros((1, fleet.n_gen), dtype=bool),
            ordc_penalties=np.array([500.0]),
            ordc_step_widths=np.array([10.0]),
            reserve_balance_zone_mask=np.ones((1, 1), dtype=bool),
            reserve_balance_ordc_counts=np.array([1]),
            reserve_balance_class=np.array([0]),
            reserve_headroom_eligible=np.zeros((1, fleet.n_gen), dtype=bool),
            reserve_headroom_products=np.ones((1, 1), dtype=bool),
            T=24,
        )
        demand = np.full((1, 24), 60.0)
        r_none = solve_dispatch(
            fleet, demand, reserve_storage_duration_h=None, **common
        )
        r_default = solve_dispatch(fleet, demand, **common)
        np.testing.assert_allclose(r_none.prices, r_default.prices)
        self.assertIsNone(r_none.storage_reserve_dispatch)  # no RS columns


class TestSupplyCapCountsStorageAS(unittest.TestCase):
    """Cleared storage AS still counts under the RTOLCAP supply cap."""

    PEAK = 12

    def test_storage_as_bounded_by_supply_cap(self):
        # A dear 20 MW requirement met solely by the battery, but a supply cap of
        # 8 MW: the cleared storage AS (RS) is capped at 8, not the 5–20 the
        # duration/power would otherwise allow. RTOLCAP includes online batteries.
        hours = 24
        fleet, mc = _fleet([("gas_cc", 100.0, 20.0)], ["Z0"], hours)
        demand = np.full((1, hours), 60.0)
        req = np.zeros((1, hours))
        req[0, self.PEAK] = 20.0
        pen, wid = nyiso_rcpf_product_shortfall_steps(20.0, 0.0, 5000.0, 10)
        not_elig = np.zeros((1, fleet.n_gen), dtype=bool)
        cap = np.full((1, hours), 1e6)
        cap[0, self.PEAK] = 8.0  # supply cap binds below power/duration
        r = solve_dispatch(
            fleet,
            demand,
            wind_cf=np.zeros((1, hours)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, hours)),
            solar_cap=np.zeros(1),
            mc=mc,
            voll=5000.0,
            storage_power_cap=np.array([20.0]),
            storage_energy_cap=np.array([80.0]),  # 4-h: duration would allow 20
            storage_zone_idx=np.array([0]),
            eta_chg=1.0,
            eta_dis=1.0,
            reserve_storage=True,
            reserve_requirement=req,
            reserve_eligible=not_elig,
            ordc_penalties=pen,
            ordc_step_widths=wid,
            reserve_balance_zone_mask=np.ones((1, 1), dtype=bool),
            reserve_balance_ordc_counts=np.array([pen.size]),
            reserve_balance_class=np.array([0]),
            reserve_headroom_eligible=not_elig,
            reserve_headroom_products=np.ones((1, 1), dtype=bool),
            reserve_supply_cap=cap,
            reserve_storage_duration_h=np.array([1.0]),
            T=hours,
        )
        held = float(r.storage_reserve_dispatch[0, self.PEAK])
        self.assertLess(held, 8.0 + 1e-3)
        self.assertGreater(held, 7.5)


if __name__ == "__main__":
    unittest.main()
