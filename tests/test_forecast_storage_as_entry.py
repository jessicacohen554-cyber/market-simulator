"""Forecast-mode storage AS: endogenous entry credit + requirement scaling.

Companion to ``tests/test_ercot_storage_as_endogenous.py`` (which covers the
dispatch-level energy-vs-AS *withholding*). This file covers the two forecast
pieces this workstream added:

* the AS credit the storage new-entry screen sees is DERIVED from the solved
  co-opt's reserve duals under ``ercot_storage_as_endogenous`` and the exogenous
  ``as_revenue_per_mw_yr`` is suppressed — exactly one mechanism prices storage
  AS (CLAUDE.md rule 19);
* the AS *requirement* that drives the withholding regenerates from forward
  load/VRE drivers (it scales with load), so it is forward-valid (rule 13);
* the config guards that keep the endogenous flag meaningful.

Built from the trivial case up (CLAUDE.md testing pattern).
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.ancillary import realized_storage_as_revenue_per_mw_yr
from market_sim.model.dispatch import solve_dispatch
from market_sim.model.storage import apply_storage_new_entry
from market_sim.results.scarcity import (
    ercot_as_forward_drivers,
    ercot_as_forward_requirement_mw,
    nyiso_rcpf_product_shortfall_steps,
)


def _coopt_solve(max_penalty, peak=12, hours=24):
    """1 storage, 1 zone, 24 h co-opt solve — the endogenous-choice fixture.

    Cheap base (mc 20) + dear peaker (mc 200), neither reserve-eligible, so the
    battery is the only AS supply. A 20 MW reserve requirement in the peak hour
    competes with the ~180/MWh arbitrage the peak offers.
    """
    gens = [
        Generator(
            unit_id="G0",
            name="G0",
            zone="Z0",
            fuel_type="gas_cc",
            pmax_mw=100.0,
            pmin_mw=0.0,
            eford=0.0,
        ),
        Generator(
            unit_id="G1",
            name="G1",
            zone="Z0",
            fuel_type="gas_ct",
            pmax_mw=50.0,
            pmin_mw=0.0,
            eford=0.0,
        ),
    ]
    fa = generators_to_fleet_arrays(gens, ["Z0"], hours=hours)
    mc = np.array([[20.0] * hours, [200.0] * hours])
    demand = np.full((1, hours), 60.0)
    demand[0, peak] = 130.0
    req = np.zeros((1, hours))
    req[0, peak] = 20.0
    pen, wid = nyiso_rcpf_product_shortfall_steps(20.0, 0.0, max_penalty, 10)
    notelig = np.zeros((1, fa.n_gen), dtype=bool)
    return solve_dispatch(
        fa,
        demand,
        wind_cf=np.zeros((1, hours)),
        wind_cap=np.zeros(1),
        solar_cf=np.zeros((1, hours)),
        solar_cap=np.zeros(1),
        mc=mc,
        voll=5000.0,
        storage_power_cap=np.array([20.0]),
        storage_energy_cap=np.array([80.0]),
        storage_zone_idx=np.array([0]),
        eta_chg=1.0,
        eta_dis=1.0,
        reserve_storage=True,
        reserve_requirement=req,
        reserve_eligible=notelig,
        ordc_penalties=pen,
        ordc_step_widths=wid,
        reserve_balance_zone_mask=np.ones((1, 1), dtype=bool),
        reserve_balance_ordc_counts=np.array([pen.size]),
        reserve_balance_class=np.array([0]),
        reserve_headroom_eligible=notelig,
        reserve_headroom_products=np.ones((1, 1), dtype=bool),
        T=hours,
    )


class TestRealizedStorageAsRevenue(unittest.TestCase):
    """The AS credit recovered from the co-opt's own reserve duals."""

    def test_credit_equals_held_reserve_times_binding_price(self):
        # Dear reserve: the battery holds its 20 MW as AS in the peak hour; the
        # reserve dual is the forgone arbitrage (~180). The derived $/MW-yr is
        # exactly held-MW x price / fleet-MW.
        r = _coopt_solve(max_penalty=5000.0)
        self.assertLess(float(r.storage_discharge[0, 12]), 1.0)  # holds AS
        val = realized_storage_as_revenue_per_mw_yr(
            r.reserve_price_by_family,
            r.reserve_dispatch,
            r.storage_charge,
            r.storage_discharge,
            np.array([20.0]),
            np.array([0]),
            1,
        )
        # 20 MW held x ~180 $/MWh dual / 20 MW fleet = ~180 $/MW-yr.
        self.assertGreater(val, 150.0)
        price_peak = float(np.asarray(r.reserve_price_by_family).max(axis=1)[12])
        self.assertAlmostEqual(val, price_peak, delta=1.0)

    def test_zero_when_battery_arbitrages_instead(self):
        # Cheap reserve: the battery discharges for energy and holds ~no AS, so
        # the derived credit is ~0 — the forward analogue of AS saturation.
        r = _coopt_solve(max_penalty=50.0)
        val = realized_storage_as_revenue_per_mw_yr(
            r.reserve_price_by_family,
            r.reserve_dispatch,
            r.storage_charge,
            r.storage_discharge,
            np.array([20.0]),
            np.array([0]),
            1,
        )
        self.assertLess(val, 5.0)

    def test_no_coopt_and_empty_fleet_return_zero(self):
        # co-opt off (None duals) -> 0; empty fleet -> 0.
        self.assertEqual(
            realized_storage_as_revenue_per_mw_yr(
                None, None, None, None, np.array([20.0]), np.array([0]), 1
            ),
            0.0,
        )
        r = _coopt_solve(max_penalty=5000.0)
        self.assertEqual(
            realized_storage_as_revenue_per_mw_yr(
                r.reserve_price_by_family,
                r.reserve_dispatch,
                r.storage_charge,
                r.storage_discharge,
                np.array([]),
                np.array([], dtype=int),
                1,
            ),
            0.0,
        )


class TestEntryCreditGate(unittest.TestCase):
    """apply_storage_new_entry uses exactly one AS-credit mechanism."""

    # Flat prices -> zero arbitrage revenue; ERCOT pays no capacity value, so
    # the storage build decision turns purely on the AS credit vs cost. A huge
    # exogenous AS multiplier guarantees the sign, magnitude-safely.
    PRICES = np.full((7, 48), 30.0)

    def _build_count(self, config, derived=None):
        fleet = apply_storage_new_entry(
            [],
            self.PRICES,
            2030,
            config,
            "ERCOT",
            endogenous_as_revenue_per_mw_yr=derived,
        )
        return len(fleet)

    def test_exogenous_applies_only_when_endogenous_off(self):
        # endo OFF + huge exogenous AS -> storage is profitable -> builds.
        off = ScenarioConfig(
            iso="ERCOT",
            weather_year=2030,
            mode="forecast",
            hours=48,
            as_revenue_enabled=True,
            as_revenue_multiplier=100.0,
        )
        self.assertGreater(self._build_count(off), 0)

    def test_endogenous_suppresses_exogenous_and_uses_derived(self):
        base = dict(
            iso="ERCOT",
            weather_year=2030,
            mode="forecast",
            hours=48,
            energy_reserve_coopt=True,
            as_revenue_enabled=True,
            as_revenue_multiplier=100.0,
        )
        endo = ScenarioConfig(ercot_storage_as_endogenous=True, **base)
        # endo ON with a zero derived credit -> the huge exogenous rate is
        # SUPPRESSED (not double-counted), so no AS value -> no build.
        self.assertEqual(self._build_count(endo, derived=0.0), 0)
        # endo ON with a large derived credit from the co-opt -> builds. Same
        # config, only the co-opt-derived credit changed -> the derived stream
        # is the one that drives entry.
        self.assertGreater(self._build_count(endo, derived=500_000.0), 0)


class TestForwardRequirementScalesWithLoad(unittest.TestCase):
    """The AS requirement regenerates from forward drivers and scales up."""

    def _req(self, load_mw, product="NSPIN", hours=24):
        cfg = ScenarioConfig(
            iso="ERCOT",
            weather_year=2030,
            mode="forecast",
            hours=hours,
            ercot_multiproduct_as_coopt=True,
            ercot_as_forward_requirement=True,
        )
        load = np.full(hours, float(load_mw))
        wind = np.full(hours, 5_000.0)
        solar = np.full(hours, 3_000.0)
        drivers = ercot_as_forward_drivers(load, wind, solar)
        return ercot_as_forward_requirement_mw(cfg, product, hours, drivers)

    def test_requirement_increases_with_load(self):
        low = self._req(30_000.0)
        high = self._req(70_000.0)
        self.assertIsNotNone(low)
        self.assertIsNotNone(high)
        # Non-Spin has an explicit load coefficient; higher load -> higher req.
        self.assertGreater(float(high.mean()), float(low.mean()))

    def test_requirement_is_positive_forward(self):
        # A forward year (2030, no measured plan file) still yields a real,
        # positive requirement purely from drivers — never the silent-zero
        # measured fallback.
        req = self._req(50_000.0, product="RRS")
        self.assertIsNotNone(req)
        self.assertGreater(float(req.min()), 0.0)


class TestConfigGuards(unittest.TestCase):
    """The endogenous flag stays meaningful (no silent no-op)."""

    def test_requires_energy_reserve_coopt(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(
                iso="ERCOT", weather_year=2030, ercot_storage_as_endogenous=True
            )

    def test_forecast_multiproduct_requires_forward_requirement(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(
                iso="ERCOT",
                weather_year=2030,
                mode="forecast",
                ercot_storage_as_endogenous=True,
                energy_reserve_coopt=True,
                ercot_multiproduct_as_coopt=True,
            )

    def test_valid_forecast_and_backcast_configs_construct(self):
        ScenarioConfig(
            iso="ERCOT",
            weather_year=2030,
            mode="forecast",
            ercot_storage_as_endogenous=True,
            energy_reserve_coopt=True,
            ercot_multiproduct_as_coopt=True,
            ercot_as_forward_requirement=True,
        )
        ScenarioConfig(
            iso="ERCOT",
            weather_year=2024,
            mode="backcast",
            ercot_storage_as_endogenous=True,
            energy_reserve_coopt=True,
            ercot_multiproduct_as_coopt=True,
        )


if __name__ == "__main__":
    unittest.main()
