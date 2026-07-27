"""Tests for ERCOT's endogenous THERMAL AS credit (rule 19, thermal seam).

The thermal analogue of ``ercot_storage_as_endogenous``: under the reserve
co-optimization, thermal AS is priced by the co-opt's own reserve duals, so the
retirement/new-entry capacity screens must credit the AS value DERIVED from those
duals (``ancillary.realized_thermal_as_revenue_per_mw_yr_by_fuel``) instead of the
exogenous flat ``as_revenue_per_mw_yr`` — exactly one mechanism prices thermal AS.
Forecast-only (capacity evolution never runs in backcast) and default off, so
keepers are byte-identical. Built from the trivial case up (CLAUDE.md testing
pattern); nothing is pinned to a measured award.
"""

import unittest
from types import SimpleNamespace

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.ancillary import (
    as_revenue_per_mw_yr,
    realized_thermal_as_revenue_per_mw_yr_by_fuel,
)
from market_sim.model.capacity import apply_economic_retirements


def _fleet_arrays(specs, hours):
    """Build fleet arrays from ``(uid, fuel, pmax)`` specs, all in zone 0."""
    gens = [
        Generator(
            unit_id=uid,
            name=uid,
            zone="Z0",
            fuel_type=fuel,
            pmax_mw=pmax,
            pmin_mw=0.0,
            eford=0.0,  # no derate -> headroom is exactly pmax - dispatch
        )
        for uid, fuel, pmax in specs
    ]
    return gens, generators_to_fleet_arrays(gens, ["Z0"], hours=hours)


class TestDerivedThermalASRate(unittest.TestCase):
    """The per-fuel $/MW-yr credit recovered from a solved co-opt's duals."""

    T = 24

    def test_none_when_coopt_did_not_price_reserve(self):
        # No reserve price -> no derived credit (empty map, caller keeps exogenous
        # only if the flag is off; when on, thermal simply earns no AS this year).
        _gens, fa = _fleet_arrays([("G0", "gas_cc", 100.0)], self.T)
        out = realized_thermal_as_revenue_per_mw_yr_by_fuel(
            fa, np.zeros((1, self.T)), None, self.T
        )
        self.assertEqual(out, {})

    def test_positive_rate_from_reserve_dual_and_headroom(self):
        # gas_cc is reserve-eligible (spinning); a single reserve-price spike over
        # its unused headroom yields a positive $/MW-yr, and the price is a dual,
        # never a measured MCPC.
        _gens, fa = _fleet_arrays([("G0", "gas_cc", 100.0)], self.T)
        dispatch = np.full((1, self.T), 40.0)  # 60 MW headroom
        rp = np.zeros((self.T, 1))
        rp[12, 0] = 500.0  # one binding AS hour
        out = realized_thermal_as_revenue_per_mw_yr_by_fuel(fa, dispatch, rp, self.T)
        # value = headroom(60) * price(500) = 30_000 $, over pmax 100 = 300 $/MW-yr.
        self.assertAlmostEqual(out["gas_cc"], 300.0, places=6)

    def test_non_responsive_fuel_absent_from_map(self):
        # Wind holds no responsive reserve -> zero AS value -> not in the map, so
        # a wind new-entry candidate is credited 0 via dict.get(..., 0.0).
        _gens, fa = _fleet_arrays(
            [("G0", "gas_cc", 100.0), ("W0", "wind", 100.0)], self.T
        )
        dispatch = np.zeros((2, self.T))
        rp = np.full((self.T, 1), 100.0)
        out = realized_thermal_as_revenue_per_mw_yr_by_fuel(fa, dispatch, rp, self.T)
        self.assertIn("gas_cc", out)
        self.assertNotIn("wind", out)


class TestScreenMutualExclusion(unittest.TestCase):
    """Supplying the derived map suppresses the exogenous rate (rule 19)."""

    T = 10

    def _screen(self, thermal_map):
        # gas_cc on the retirement margin: energy revenue alone < going-forward
        # cost, but energy + the exogenous AS credit clears it. Fed the empty
        # derived map, the exogenous credit is suppressed and the year is a loss.
        config = ScenarioConfig(
            iso="ERCOT", weather_year=2025, hours=self.T, as_revenue_enabled=True
        )
        gens, fa = _fleet_arrays([("G0", "gas_cc", 100.0)], self.T)
        # going_forward_cost = fixed_om_gas_cc * pmax * 1000.
        cost = config.fixed_om_gas_cc * 100.0 * 1000.0
        exo = as_revenue_per_mw_yr("gas_cc", 0.0, config) * 100.0
        self.assertGreater(exo, 0.0)  # exogenous ERCOT credit is live
        # Energy net revenue straddles: below cost, above (cost - exo).
        energy = cost - 0.5 * exo
        dispatch_mwh = 100.0 * self.T  # full output every hour
        price = np.full((1, self.T), energy / dispatch_mwh)
        mc = np.zeros((1, self.T))
        dispatch = SimpleNamespace(dispatch=np.full((1, self.T), 100.0))
        _fleet, losses, _ = apply_economic_retirements(
            gens,
            fa,
            dispatch,
            price,
            config,
            {},
            peak_demand=0.0,
            mc=mc,
            thermal_as_revenue_per_mw_yr=thermal_map,
        )
        return losses.get("G0", 0)

    def test_exogenous_credit_keeps_unit_profitable(self):
        # Flag off (map None): exogenous AS lifts revenue over cost -> loss 0.
        self.assertEqual(self._screen(None), 0)

    def test_derived_map_suppresses_exogenous_credit(self):
        # Flag on with an empty derived map (co-opt priced no AS this year): the
        # exogenous rate is NOT stacked on top -> the year is an unprofitable one.
        self.assertEqual(self._screen({}), 1)


class TestConfigValidation(unittest.TestCase):
    """The flag requires the co-opt that supplies the duals it derives from."""

    def test_requires_energy_reserve_coopt(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(
                iso="ERCOT",
                weather_year=2025,
                ercot_thermal_as_endogenous=True,
                energy_reserve_coopt=False,
            )

    def test_forecast_multiproduct_requires_forward_requirement(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(
                iso="ERCOT",
                weather_year=2025,
                mode="forecast",
                ercot_thermal_as_endogenous=True,
                energy_reserve_coopt=True,
                ercot_multiproduct_as_coopt=True,
                ercot_as_forward_requirement=False,
            )

    def test_valid_forecast_config_accepted(self):
        cfg = ScenarioConfig(
            iso="ERCOT",
            weather_year=2025,
            mode="forecast",
            ercot_thermal_as_endogenous=True,
            energy_reserve_coopt=True,
            ercot_multiproduct_as_coopt=True,
            ercot_as_forward_requirement=True,
        )
        self.assertTrue(cfg.ercot_thermal_as_endogenous)


if __name__ == "__main__":
    unittest.main()
