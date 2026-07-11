"""Per-PR forecast-driver directionality smoke tests (plan §2 Tier 1 harness note).

These are the *fast* per-PR gate the testing audit found missing (its G2/G3/G4):
tiny analytic LPs — 1 zone, 24 hours, a two- or three-unit fleet — solved on the
**real** HiGHS solver in seconds, asserting that the model's driver responses
have the right *sign* and hit the *analytically-computed* crossover. They are the
seconds-scale companion to ``scripts/run_driver_battery.py`` (the minutes-scale
Tier-1 elasticity ladders) and to the weekly ``check_forecast_invariants.py``
paired invariants P1-P3, which only ran on a cron before this file existed.

Deliberately NOT ``@pytest.mark.slow`` — every test here solves a 24-hour LP that
finishes in well under a second, so the whole module runs inside the per-PR
``pytest -m "not slow and not integration"`` tier. A directional regression here
should block the PR, not wait a week (rule 1: the model's mechanisms are the
product; a silently wrong sign is a broken mechanism).

Coverage, mapped to the Tier-1 tests these smoke the direction of:

* **T1.1 carbon** — coal generation and system CO2 are monotone non-increasing
  across a carbon-price ladder, and the coal→gas switch lands on the analytic
  SRMC crossover computed from the fleet's own heat-rate/emission-rate params
  (no magic number — the crossover is derived, then asserted).
* **T1.3 gas / P2 merit sign** — a +gas move flips the marginal unit from gas to
  coal: coal generation ↑, gas-CC generation ↓, price ↑, objective ↑.
* **T1.6 RPS/ACP** — the REC dual is ≤ the ACP ceiling always, pins *at* the ACP
  when renewables are physically short, and falls to ~0 once VRE covers the
  target.
* **T1.7 capacity revenue** — the economic-retirement screen retires monotone
  *fewer* thermal units as the capacity-market net-CONE rises (a capacity
  payment covers the fixed-cost gap), and ERCOT is the zero-capacity-revenue
  negative control: identical retirements across the whole net-CONE ladder.

Every numeric input lives in the :class:`Analytic` dataclass at the top so the
expected crossovers are computed, not hand-copied.
"""

from __future__ import annotations

import unittest
from dataclasses import dataclass
from unittest import mock

import numpy as np

from market_sim.config.constants import MARKET_DESIGN, MarketDesign
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.capacity import (
    apply_economic_retirements,
    capacity_revenue_per_mw_yr,
)
from market_sim.model.dispatch import solve_dispatch


# --------------------------------------------------------------------------- #
# Analytic parameters — every literal the smoke LPs use, in one place, so the
# expected crossovers are *derived* from these rather than hand-copied (plan
# §2.1: "assert the crossover, not a magic number").
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Analytic:
    """Fleet + ladder parameters and the crossovers derived from them."""

    hours: int = 24

    # Two-unit merit fleet: a coal unit (cheaper energy, dirtier) and a gas-CC
    # unit (pricier energy, cleaner). pmin 0 and eford 0 so availability is 1
    # and only the cheaper unit carries the (sub-capacity) load.
    coal_mc0: float = 20.0  # $/MWh at zero carbon (heat_rate x fuel + VOM)
    gas_mc0: float = 30.0
    coal_co2: float = 1.00  # t/MWh — coal is the higher-emitting unit
    gas_co2: float = 0.40
    unit_pmax: float = 100.0
    demand_mw: float = 80.0  # < one unit's pmax: exactly one unit is marginal

    # Carbon ladder (T1.1). $/t CO2.
    carbon_ladder: tuple[float, ...] = (0.0, 25.0, 50.0, 100.0)

    # Gas merit move (T1.3): a base where gas is *cheaper* than coal, and a
    # bumped gas cost that pushes gas above coal so coal takes over.
    merit_gas_mc_base: float = 22.0  # gas below coal (25) -> gas serves load
    merit_coal_mc: float = 25.0
    merit_gas_mc_bumped: float = 30.0  # gas above coal -> coal serves load

    # RPS/ACP (T1.6).
    rps_target: float = 1.0
    rps_acp: float = 65.0
    gas_only_mc: float = 50.0
    wind_premium_mc: float = 100.0  # dirtier than the ACP, idle absent the RPS

    # Capacity-revenue retirement ladder (T1.7). Coal retires after ONE loss
    # year, so a single screen call suffices. net-CONE $/kW-yr rungs.
    net_cone_ladder: tuple[float, ...] = (0.0, 50.0, 100.0)
    ret_unit_pmax: float = 100.0
    ret_unit_eford: float = 0.05
    ret_n_units: int = 3

    @property
    def carbon_crossover(self) -> float:
        """Carbon price ($/t) where coal SRMC overtakes gas SRMC.

        ``coal_mc0 + coal_co2 * c = gas_mc0 + gas_co2 * c`` solved for ``c``.
        Below it coal is cheaper (coal runs); above it gas is cheaper.
        """
        return (self.gas_mc0 - self.coal_mc0) / (self.coal_co2 - self.gas_co2)

    def coal_srmc(self, carbon: float) -> float:
        return self.coal_mc0 + self.coal_co2 * carbon

    def gas_srmc(self, carbon: float) -> float:
        return self.gas_mc0 + self.gas_co2 * carbon


A = Analytic()


def _two_unit_fleet(zone: str = "Z0"):
    """Coal + gas-CC, one zone, no must-run — a controllable merit order."""
    gens = [
        Generator(
            unit_id="COAL",
            name="COAL",
            zone=zone,
            fuel_type="coal",
            pmax_mw=A.unit_pmax,
            pmin_mw=0.0,
            emission_rate_co2=A.coal_co2,
            eford=0.0,
        ),
        Generator(
            unit_id="GASCC",
            name="GASCC",
            zone=zone,
            fuel_type="gas_cc",
            pmax_mw=A.unit_pmax,
            pmin_mw=0.0,
            emission_rate_co2=A.gas_co2,
            eford=0.0,
        ),
    ]
    return gens, generators_to_fleet_arrays(gens, [zone], hours=A.hours)


def _no_renewables(n_zones: int = 1) -> dict:
    return dict(
        wind_cf=np.zeros((n_zones, A.hours)),
        wind_cap=np.zeros(n_zones),
        solar_cf=np.zeros((n_zones, A.hours)),
        solar_cap=np.zeros(n_zones),
    )


class TestCarbonDirectionality(unittest.TestCase):
    """T1.1 — carbon monotonicity + the analytic coal/gas SRMC crossover."""

    def _solve_ladder(self):
        """Solve the two-unit LP at each carbon rung; return per-rung metrics.

        Carbon is baked directly into the ``mc`` array (mc = mc0 + co2 x carbon),
        so the LP receives the SRMC it should merit-order on and the emission
        rates are used only to score CO2 from the realized dispatch.
        """
        _gens, fleet = _two_unit_fleet()
        out = []
        for carbon in A.carbon_ladder:
            mc = np.vstack(
                [
                    np.full(A.hours, A.coal_srmc(carbon)),
                    np.full(A.hours, A.gas_srmc(carbon)),
                ]
            )
            demand = np.full((1, A.hours), A.demand_mw)
            res = solve_dispatch(fleet, demand, mc=mc, T=A.hours, **_no_renewables())
            self.assertEqual(res.status, "Optimal")
            coal_gen = float(res.dispatch[0].sum())
            gas_gen = float(res.dispatch[1].sum())
            co2 = coal_gen * A.coal_co2 + gas_gen * A.gas_co2
            out.append({"carbon": carbon, "coal": coal_gen, "gas": gas_gen, "co2": co2})
        return out

    def test_coal_generation_monotone_down(self):
        rungs = self._solve_ladder()
        coal = [r["coal"] for r in rungs]
        for lo, hi in zip(coal, coal[1:]):
            self.assertLessEqual(
                hi, lo + 1e-6, f"coal generation rose across the carbon ladder: {coal}"
            )
        # And it actually moves — coal runs at the bottom, is displaced by the top.
        self.assertGreater(coal[0], coal[-1] + 1.0)

    def test_system_co2_monotone_down(self):
        rungs = self._solve_ladder()
        co2 = [r["co2"] for r in rungs]
        for lo, hi in zip(co2, co2[1:]):
            self.assertLessEqual(
                hi, lo + 1e-6, f"system CO2 rose across the carbon ladder: {co2}"
            )

    def test_switch_lands_on_analytic_srmc_crossover(self):
        # The crossover is DERIVED from the fleet's own params, not hard-coded.
        c_star = A.carbon_crossover
        # Sanity: the ladder must actually straddle the crossover for the test
        # to be meaningful.
        self.assertLess(min(A.carbon_ladder), c_star)
        self.assertGreater(max(A.carbon_ladder), c_star)
        for r in self._solve_ladder():
            coal_cheaper = A.coal_srmc(r["carbon"]) < A.gas_srmc(r["carbon"])
            if r["carbon"] < c_star:
                # Below the crossover coal is cheaper and carries all the load.
                self.assertTrue(coal_cheaper)
                self.assertAlmostEqual(r["coal"], A.demand_mw * A.hours, delta=1e-3)
                self.assertAlmostEqual(r["gas"], 0.0, delta=1e-3)
            elif r["carbon"] > c_star:
                # Above it gas is cheaper and takes over entirely.
                self.assertFalse(coal_cheaper)
                self.assertAlmostEqual(r["gas"], A.demand_mw * A.hours, delta=1e-3)
                self.assertAlmostEqual(r["coal"], 0.0, delta=1e-3)


class TestMeritSignUnderGasMove(unittest.TestCase):
    """T1.3 / P2 — +gas flips the margin from gas to coal (signs, not levels)."""

    def _solve(self, gas_mc: float):
        _gens, fleet = _two_unit_fleet()
        # Row 0 coal (fixed), row 1 gas (the moved unit).
        mc = np.vstack([np.full(A.hours, A.merit_coal_mc), np.full(A.hours, gas_mc)])
        demand = np.full((1, A.hours), A.demand_mw)
        res = solve_dispatch(fleet, demand, mc=mc, T=A.hours, **_no_renewables())
        self.assertEqual(res.status, "Optimal")
        return res

    def test_gas_up_raises_coal_lowers_gas_lifts_price(self):
        base = self._solve(A.merit_gas_mc_base)
        up = self._solve(A.merit_gas_mc_bumped)

        coal_base, coal_up = base.dispatch[0].sum(), up.dispatch[0].sum()
        gas_base, gas_up = base.dispatch[1].sum(), up.dispatch[1].sum()

        # Base: gas is cheaper (22 < 25) so it serves the load; bumped: gas (30)
        # is above coal (25) so coal takes over.
        self.assertGreater(coal_up, coal_base + 1.0, "coal gen did not rise with +gas")
        self.assertLess(gas_up, gas_base - 1.0, "gas-CC gen did not fall with +gas")
        self.assertGreaterEqual(
            up.prices.mean(), base.prices.mean() - 1e-6, "price did not rise with +gas"
        )
        self.assertGreaterEqual(
            up.objective_value,
            base.objective_value - 1e-6,
            "objective did not rise with +gas",
        )


class TestRpsAcpDual(unittest.TestCase):
    """T1.6 — REC dual ≤ ACP; pins at ACP when short, → 0 when VRE covers."""

    def _gas_only_fleet(self):
        gens = [
            Generator(
                unit_id="G0",
                name="G0",
                zone="Z0",
                fuel_type="gas_cc",
                pmax_mw=200.0,
                pmin_mw=0.0,
                eford=0.0,
            )
        ]
        return generators_to_fleet_arrays(gens, ["Z0"], hours=A.hours)

    def test_dual_pins_at_acp_when_renewables_short(self):
        # No renewable capacity at all: a 100% RPS can only be met by paying the
        # ACP, so the REC dual clears exactly at the buy-out ceiling.
        fleet = self._gas_only_fleet()
        mc = np.full((1, A.hours), A.gas_only_mc)
        demand = np.full((1, A.hours), A.demand_mw)
        res = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=A.hours,
            rps_target=A.rps_target,
            rps_acp_price=A.rps_acp,
            **_no_renewables(),
        )
        self.assertEqual(res.status, "Optimal")
        self.assertIsNotNone(res.rps_shadow_price)
        self.assertLessEqual(res.rps_shadow_price, A.rps_acp + 1e-6)  # never above ACP
        self.assertAlmostEqual(res.rps_shadow_price, A.rps_acp, delta=1e-2)

    def test_dual_falls_to_zero_when_vre_covers_target(self):
        # Cheap wind supplies more than the target: the RPS is slack, the ACP
        # escape goes unused, and the dual sits at ~0 (still ≤ ACP).
        fleet = self._gas_only_fleet()
        mc = np.full((1, A.hours), A.gas_only_mc)
        demand = np.full((1, A.hours), A.demand_mw)
        res = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=A.hours,
            rps_target=A.rps_target,
            rps_acp_price=A.rps_acp,
            # 100 MW nameplate x CF 1.0 = 100 MW cheap wind vs 80 MW demand:
            # renewables cover the whole 100% target with room to spare.
            wind_cf=np.full((1, A.hours), 1.0),
            wind_cap=np.array([100.0]),
            solar_cf=np.zeros((1, A.hours)),
            solar_cap=np.zeros(1),
        )
        self.assertEqual(res.status, "Optimal")
        self.assertIsNotNone(res.rps_shadow_price)
        self.assertLessEqual(res.rps_shadow_price, A.rps_acp + 1e-6)
        self.assertAlmostEqual(res.rps_shadow_price, 0.0, delta=1e-2)


class TestCapacityRevenueRetirementScreen(unittest.TestCase):
    """T1.7 — retirement-screen capacity-revenue monotonicity + ERCOT control."""

    def _coal_fleet(self, zone: str = "Z0"):
        """N coal units, deeply unprofitable on energy (so the capacity payment
        is the only thing that can keep them online)."""
        gens = [
            Generator(
                unit_id=f"C{i}",
                name=f"C{i}",
                zone=zone,
                fuel_type="coal",
                pmax_mw=A.ret_unit_pmax,
                pmin_mw=0.0,
                heat_rate=10.0,
                eford=A.ret_unit_eford,
            )
            for i in range(A.ret_n_units)
        ]
        return gens, generators_to_fleet_arrays(gens, [zone], hours=A.hours)

    def _retire_count(self, iso: str, net_cone: float) -> int:
        """Retirements from one screen call with ``MARKET_DESIGN[iso]`` net-CONE
        patched to ``net_cone``. Energy revenue is near zero (price 1 $/MWh, mc
        set to the coal fuel cost) so the capacity payment is decisive."""
        gens, fleet = self._coal_fleet()
        # Full variable cost well above the depressed price: no energy margin.
        mc = np.full((A.ret_n_units, A.hours), 25.0)
        prices = np.full((1, A.hours), 1.0)
        dispatch = mock.Mock(dispatch=np.zeros((A.ret_n_units, A.hours)))
        config = ScenarioConfig(iso=iso)
        # Preserve the real capacity_market flag for the ISO, vary only net-CONE.
        base = MARKET_DESIGN.get(iso)
        patched = MarketDesign(
            capacity_market=base.capacity_market if base else False,
            net_cone_per_kw_yr=net_cone,
        )
        with mock.patch.dict("market_sim.model.capacity.MARKET_DESIGN", {iso: patched}):
            survivors, _losses, _log = apply_economic_retirements(
                gens,
                fleet,
                dispatch,
                prices,
                config,
                {},
                peak_demand=0.0,  # no reliability floor to confound the count
                mc=mc,
            )
        return A.ret_n_units - len(survivors)

    def test_ercot_capacity_revenue_is_zero(self):
        # Negative control precondition: an energy-only ISO pays nothing, at any
        # net-CONE the patch might carry.
        self.assertEqual(capacity_revenue_per_mw_yr("ERCOT", 0.05), 0.0)

    def test_pjm_retirements_monotone_down_in_net_cone(self):
        counts = [self._retire_count("PJM", nc) for nc in A.net_cone_ladder]
        for lo, hi in zip(counts, counts[1:]):
            self.assertLessEqual(
                hi, lo, f"retirements rose as net-CONE rose (should fall): {counts}"
            )
        # A real response: everything retires with no capacity payment, the
        # payment saves units at the top of the ladder.
        self.assertGreater(counts[0], counts[-1])
        self.assertEqual(counts[0], A.ret_n_units)
        self.assertEqual(counts[-1], 0)

    def test_ercot_retirements_identical_across_net_cone_ladder(self):
        # The zero-capacity-revenue negative control: ERCOT's retirement count
        # does not move as the (irrelevant) net-CONE rung changes, because an
        # energy-only ISO collects no capacity payment.
        counts = [self._retire_count("ERCOT", nc) for nc in A.net_cone_ladder]
        self.assertEqual(
            len(set(counts)), 1, f"ERCOT count moved with net-CONE: {counts}"
        )
        # And with no capacity payment every unprofitable coal unit exits.
        self.assertEqual(counts[0], A.ret_n_units)


if __name__ == "__main__":
    unittest.main()
