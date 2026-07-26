"""Tests for ERCOT's endogenous storage energy-vs-AS co-optimization (G5).

The forward analogue of the measured 60-Day DAM battery AS-award reservation
(``storage_as_commitment`` + ``ercot_storage_as_reserve``): the battery CHOOSES
energy vs upward-AS inside the multi-product co-opt, competing with arbitrage on
the same power cap and priced by the per-product AS demand curves. Built from the
trivial case up (CLAUDE.md testing pattern): a 1-storage, 1-zone, 24-hour LP in
which the battery holds AS when the reserve dual exceeds its energy-arbitrage
opportunity cost and releases it (discharges for energy) when it does not — the
real bid. Every price is recovered as an LP dual; nothing is pinned to a measured
award.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import solve_dispatch, storage_reserve_mw
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
            eford=0.0,  # no derate -> headroom is exactly pmax - dispatch
        )
        for i, (fuel, pmax, _mc) in enumerate(specs)
    ]
    fa = generators_to_fleet_arrays(gens, zone_names, hours=hours)
    mc = np.array([[s[2]] * hours for s in specs], dtype=float)
    return fa, mc


class TestEndogenousStorageChoice(unittest.TestCase):
    """1 storage, 1 zone, 24 h: the battery chooses energy vs AS endogenously.

    Setup: a cheap base unit (mc 20) and an expensive peaker (mc 200), NEITHER
    reserve-eligible, so the only AS supply is the battery. A single peak hour
    (h=12) lifts the LMP to 200, giving the battery a ~180/MWh arbitrage
    incentive to discharge. A reserve requirement competes for that same battery
    power. The reserve demand-curve offer cap is the only thing that changes
    between the two regimes — so the split is the LP's choice, not a tuned level.
    """

    PEAK = 12

    def _solve(self, max_penalty):
        hours = 24
        zone_names = ["Z0"]
        # Base unit (mc 20, 100 MW) + peaker (mc 200, 50 MW); not reserve-eligible.
        fleet, mc = _fleet(
            [("gas_cc", 100.0, 20.0), ("gas_ct", 50.0, 200.0)], zone_names, hours
        )
        demand = np.full((1, hours), 60.0)
        demand[0, self.PEAK] = 130.0  # peak: base 100 + (peaker | battery) = 130
        # Reserve requirement only in the peak hour, met solely by the battery.
        req = np.zeros((1, hours))
        req[0, self.PEAK] = 20.0
        pen, wid = nyiso_rcpf_product_shortfall_steps(20.0, 0.0, max_penalty, 10)
        # No generator is reserve-eligible -> AS comes only from the battery.
        not_eligible = np.zeros((1, fleet.n_gen), dtype=bool)
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
            storage_energy_cap=np.array([80.0]),  # 4-hour battery
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
            T=hours,
        )

    def test_battery_releases_as_when_arbitrage_wins(self):
        # Cheap reserve (offer cap 50 < ~180 arbitrage): the battery discharges
        # for energy in the peak hour and lets the AS requirement go short.
        r = self._solve(max_penalty=50.0)
        dis = float(r.storage_discharge[0, self.PEAK])
        self.assertGreater(dis, 19.0)  # ~full discharge for arbitrage
        as_mw = storage_reserve_mw(
            r.reserve_dispatch,
            r.storage_charge,
            r.storage_discharge,
            np.array([20.0]),
            np.array([0]),
            n_reserve_classes=1,
        )
        self.assertLess(float(as_mw[0, self.PEAK]), 1.0)  # held ~no reserve

    def test_battery_holds_as_when_reserve_dual_wins(self):
        # Dear reserve (offer cap 5000 >> ~180 arbitrage): the battery holds its
        # power as AS in the peak hour instead of discharging for energy.
        r = self._solve(max_penalty=5000.0)
        dis = float(r.storage_discharge[0, self.PEAK])
        self.assertLess(dis, 1.0)  # holds power back, does not arbitrage
        as_mw = storage_reserve_mw(
            r.reserve_dispatch,
            r.storage_charge,
            r.storage_discharge,
            np.array([20.0]),
            np.array([0]),
            n_reserve_classes=1,
        )
        self.assertGreater(float(as_mw[0, self.PEAK]), 19.0)  # held ~full reserve

    def test_split_flips_on_the_reserve_price(self):
        # The energy-vs-AS split is set by which is worth more — the LP's choice,
        # not a fixed level: raising only the AS offer cap flips the battery from
        # all-energy to all-AS in the peak hour.
        arb = float(self._solve(max_penalty=50.0).storage_discharge[0, self.PEAK])
        held = float(self._solve(max_penalty=5000.0).storage_discharge[0, self.PEAK])
        self.assertGreater(arb - held, 18.0)


class TestStorageReserveAttribution(unittest.TestCase):
    """The storage-first attribution helper (validation metering)."""

    def test_storage_first_min_rule(self):
        # 2 zones, 2 products (classes), 3 hours; one storage unit per zone.
        # reserve_dispatch is class-major: (n_classes*n_zones, T).
        n_classes = 2
        # Per (class, zone) cleared reserve.
        rd = np.array(
            [
                [10.0, 0.0, 5.0],  # class0 zone0
                [4.0, 4.0, 4.0],  # class0 zone1
                [6.0, 0.0, 0.0],  # class1 zone0
                [1.0, 1.0, 1.0],  # class1 zone1
            ]
        )
        # zone0 total reserve = 16, 0, 5 ; zone1 = 5, 5, 5
        charge = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
        discharge = np.array([[5.0, 0.0, 0.0], [0.0, 0.0, 3.0]])
        cap = np.array([20.0, 4.0])  # unit0 in zone0, unit1 in zone1
        zone_idx = np.array([0, 1])
        out = storage_reserve_mw(rd, charge, discharge, cap, zone_idx, n_classes)
        # zone0 room = 20-5 = 15 ; min(15, [16,0,5]) = [15,0,5]
        np.testing.assert_allclose(out[0], [15.0, 0.0, 5.0])
        # zone1 room = 4-[0,0,3] = [4,4,1] ; min([4,4,1],[5,5,5]) = [4,4,1]
        np.testing.assert_allclose(out[1], [4.0, 4.0, 1.0])


class TestWiringByteIdentical(unittest.TestCase):
    """The flag leaves the measured/legacy reserve-inputs path untouched."""

    def test_measured_credit_guarded_off_under_endogenous(self):
        # get_reserve_design applies the measured storage-AS credit only
        # when storage_as_commitment is on AND endogenous is off. Turning the
        # endogenous flag on must suppress the measured credit (no double path).
        fleet, _mc = _fleet([("gas_cc", 100.0, 20.0)], ["Z0"], 24)
        base = ScenarioConfig(
            iso="ERCOT",
            weather_year=2025,
            hours=24,
            # energy_reserve_coopt is required by the endogenous flag (the split
            # is priced by the co-opt); the single-product ORDC path is used here
            # (no multiproduct flag), so no forward-requirement gate applies.
            energy_reserve_coopt=True,
            ercot_storage_as_reserve=True,
            ercot_storage_as_reserve_from_year=2025,
            storage_as_commitment=True,
        )
        endo = base.with_overrides(ercot_storage_as_endogenous=True)
        from market_sim.config.reserve_config import (
            build_reserve_dispatch_kwargs,
            get_reserve_design,
        )

        design_base = get_reserve_design(base, fleet, 24, ["ERCOT"])
        req_measured = build_reserve_dispatch_kwargs(design_base)["reserve_requirement"]
        design_endo = get_reserve_design(endo, fleet, 24, ["ERCOT"])
        req_endo = build_reserve_dispatch_kwargs(design_endo)["reserve_requirement"]
        # With the measured credit active the requirement is pulled DOWN by the
        # measured storage AS; under endogenous it is not (>= the credited one).
        self.assertTrue(np.all(req_endo >= req_measured - 1e-9))
        self.assertGreater(float(req_endo.sum()), float(req_measured.sum()))


if __name__ == "__main__":
    unittest.main()
