"""Unit tests for the ERCOT storage RT discharge-offer tranche LP arm.

The LP-layer tests of ``ercot_storage_rt_offer_surface`` (ercot-162): the
discharge-tranche decomposition (``Dis[s,t] = Σ_k DisT[a,k,t]``) that prices an
ERCOT battery's energy-side discharge at its measured multi-tranche SCED ladder
instead of the flat ``battery_dispatch_adder``. Trivial-case-first per
CLAUDE.md: 1 zone, 1 battery, 24 hours.

Covers:

* byte-identical when the arm is off (the layout/bounds/costs/rows guards);
* the layout accounting (n_dis_tranche, offsets, column uniqueness);
* the tranche ladder sets the marginal price at a battery-marginal hour
  (offer + charge-replacement, the natural arbitrage dual);
* the tranche prices keep the battery OUT of the mid-band (no spurious lift):
  a tranche priced above the mid-band thermal cost never discharges there;
* the base ``storage_discharge`` output stays the TOTAL discharge (the volume
  guard reads it), i.e. the decomposition is invisible to every consumer of
  the base column.
"""

import unittest

import numpy as np

from market_sim.model.lp import solve_dispatch
from market_sim.model.lp.layout import VariableLayout
from tests.unit.model.test_dispatch import _make_fleet

T = 24


def _base_kwargs(power=50.0, energy=200.0, eta=1.0):
    """Common storage-solve kwargs: 1 zone, no VRE, 1 battery, flat $10 adder."""
    return dict(
        wind_cf=np.zeros((1, T)),
        wind_cap=np.array([0.0]),
        solar_cf=np.zeros((1, T)),
        solar_cap=np.array([0.0]),
        storage_power_cap=np.array([power]),
        storage_energy_cap=np.array([energy]),
        storage_zone_idx=np.array([0]),
        eta_chg=eta,
        eta_dis=eta,
        storage_discharge_cost=10.0,
        voll=5000.0,
        T=T,
    )


class TestDisTrancheLayout(unittest.TestCase):
    """Layout accounting for the appended discharge-tranche block."""

    def test_off_is_byte_identical(self):
        # n_dis_tranche defaults to 0 -> vars_per_hour and offsets unchanged.
        base = VariableLayout(n_gen=2, n_zones=1, n_storage=1, n_links=0, T=T)
        armed = VariableLayout(n_gen=2, n_zones=1, n_storage=1, n_links=0, T=T)
        self.assertEqual(base.vars_per_hour, armed.vars_per_hour)
        self.assertEqual(base._dis_tranche_off, base.vars_per_hour)

    def test_tranche_block_appended_after_every_existing_block(self):
        layout = VariableLayout(
            n_gen=2,
            n_zones=1,
            n_storage=1,
            n_links=0,
            T=T,
            n_dis_tranche=6,  # 2 armed batteries * K=3
            dis_tranche_k=3,
        )
        # The tranche block is the LAST block, so every prior offset is intact.
        self.assertEqual(
            layout._dis_tranche_off, layout._rec_acp_off + layout.n_rec_acp
        )
        self.assertEqual(
            layout.vars_per_hour,
            layout.n_gen + 4 * 1 + 3 * 1 + layout.n_dis_tranche,
        )

    def test_tranche_columns_unique(self):
        layout = VariableLayout(
            n_gen=1,
            n_zones=1,
            n_storage=2,
            n_links=0,
            T=5,
            n_dis_tranche=6,
            dis_tranche_k=3,
        )
        cols = [layout.dis_tranche_col(a, k, 2) for a in range(2) for k in range(3)]
        self.assertEqual(len(cols), len(set(cols)))
        # armed-major / tranche-minor stride.
        self.assertEqual(
            layout.dis_tranche_col(1, 0, 2) - layout.dis_tranche_col(0, 0, 2), 3
        )
        self.assertEqual(
            layout.dis_tranche_col(0, 1, 2) - layout.dis_tranche_col(0, 0, 2), 1
        )


class TestDisTrancheSolve(unittest.TestCase):
    """End-to-end solves of the tranche arm on the trivial system."""

    def _spike_demand(self, batt_need):
        d = np.full((1, T), 30.0)
        d[0, 18] = 100.0 + batt_need  # thermal pmax 100; batt covers the rest
        return d

    def test_off_matches_no_arm(self):
        fleet = _make_fleet(["Z"], ["Z"], hours=T, pmax=100.0, pmin=0.0, eford=0.0)
        mc = np.full((1, T), 25.0)
        demand = self._spike_demand(12.0)
        no_arm = solve_dispatch(fleet, demand, mc=mc, **_base_kwargs())
        arm_none = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            dis_tranche_arm_idx=None,
            dis_tranche_width=None,
            dis_tranche_price=None,
            **_base_kwargs(),
        )
        np.testing.assert_allclose(no_arm.prices, arm_none.prices)
        np.testing.assert_allclose(no_arm.storage_discharge, arm_none.storage_discharge)

    def test_marginal_tranche_sets_price(self):
        # RTE=1, gas mc $25. Spike needs 12 MW from the battery; tranche widths
        # 0.1/0.2/0.7 of 50 MW = 5/10/35 MW at $40/$500/$5000. 12 MW fills
        # tranche 0 (5) + 7 of tranche 1, so tranche 1 ($500) is marginal. The
        # battery charges at a $25 gas hour, so the energy-balance dual is the
        # offer + charge replacement = $500 + $25 = $525 (natural arbitrage dual).
        fleet = _make_fleet(["Z"], ["Z"], hours=T, pmax=100.0, pmin=0.0, eford=0.0)
        mc = np.full((1, T), 25.0)
        demand = self._spike_demand(12.0)
        price_KT = np.tile(np.array([[40.0], [500.0], [5000.0]]), (1, T))
        r = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            dis_tranche_arm_idx=np.array([0]),
            dis_tranche_width=np.array([0.1, 0.2, 0.7]),
            dis_tranche_price=price_KT,
            **_base_kwargs(eta=1.0),
        )
        self.assertAlmostEqual(float(r.storage_discharge[0, 18]), 12.0, places=3)
        self.assertAlmostEqual(float(r.prices[0, 18]), 525.0, delta=0.5)

    def test_base_discharge_is_total(self):
        # The base storage_discharge output equals Σ_k tranches (the volume guard
        # reads it), i.e. the decomposition is invisible to base-column consumers.
        fleet = _make_fleet(["Z"], ["Z"], hours=T, pmax=100.0, pmin=0.0, eford=0.0)
        mc = np.full((1, T), 25.0)
        demand = self._spike_demand(12.0)
        price_KT = np.tile(np.array([[40.0], [500.0], [5000.0]]), (1, T))
        r = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            dis_tranche_arm_idx=np.array([0]),
            dis_tranche_width=np.array([0.1, 0.2, 0.7]),
            dis_tranche_price=price_KT,
            **_base_kwargs(eta=1.0),
        )
        # Total discharge is exactly the 12 MW spike coverage (no phantom cycling
        # — the tranche prices exceed the $25 gas cost, so no mid-band arbitrage).
        self.assertAlmostEqual(float(r.storage_discharge.sum()), 12.0, places=2)

    def test_no_midband_spurious_lift(self):
        # A tranche priced above the mid-band thermal cost never discharges
        # there: with gas $25 everywhere and the cheapest tranche $40, the
        # round-trip (charge $25 + discharge $40) exceeds any mid-band price, so
        # the battery holds for the spike and mid-band prices are the gas cost.
        fleet = _make_fleet(["Z"], ["Z"], hours=T, pmax=100.0, pmin=0.0, eford=0.0)
        mc = np.full((1, T), 25.0)
        demand = self._spike_demand(12.0)
        price_KT = np.tile(np.array([[40.0], [500.0], [5000.0]]), (1, T))
        r = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            dis_tranche_arm_idx=np.array([0]),
            dis_tranche_width=np.array([0.1, 0.2, 0.7]),
            dis_tranche_price=price_KT,
            **_base_kwargs(eta=1.0),
        )
        offpeak_dis = float(r.storage_discharge[0, :18].sum()) + float(
            r.storage_discharge[0, 19:].sum()
        )
        self.assertLess(offpeak_dis, 1e-3)
        # Mid-band price is the gas marginal cost, untouched by the arm.
        self.assertAlmostEqual(float(r.prices[0, 0]), 25.0, delta=0.5)


class TestTrancheHelper(unittest.TestCase):
    """The artifact-reading helper ``ercot_storage_rt_offer_tranches``."""

    def _units_and_helper(self):
        from market_sim.config.paths import RAW_DATA_DIR
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.model.storage import (
            ercot_storage_rt_offer_tranches,
            load_eia860_storage,
        )

        path = (
            RAW_DATA_DIR
            / "_validation-source"
            / "ercot_storage_rt_offer_condbinned.json"
        )
        if not path.exists():
            self.skipTest("storage RT offer surface artifact not present")
        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            weather_year=2023,
            storage_deployment="mid",
            storage_vintage_ramp=True,
            battery_dispatch_adder=10.0,
            ercot_storage_capability_measured=True,
        )
        units = load_eia860_storage("ERCOT", 2023, cfg)
        return units, ercot_storage_rt_offer_tranches

    def test_helper_reads_ladder_and_bins(self):
        units, helper = self._units_and_helper()
        hours = 8760
        net = np.arange(hours, dtype=float)  # ascending -> bin0..bin6 by hour
        res = helper(units, 2023, net, hours)
        self.assertIsNotNone(res)
        arm_idx, width, price_KT = res
        self.assertEqual(arm_idx.size, 5)  # 5 ERCOT battery zones
        np.testing.assert_allclose(width, [0.1, 0.2, 0.7])
        self.assertEqual(price_KT.shape, (3, hours))
        # The top-net-load hour lands in bin6 (2023 [60, 501, 5000]); the lowest
        # in bin0 ([40, 230, 5000]) — the measured per-bin toe, cap at $5000.
        np.testing.assert_allclose(price_KT[:, -1], [60.0, 501.0, 5000.0])
        np.testing.assert_allclose(price_KT[:, 0], [40.0, 230.0, 5000.0])

    def test_helper_year_absent_returns_none(self):
        units, helper = self._units_and_helper()
        # 2019 is a locked-test year absent from the training-only artifact.
        self.assertIsNone(helper(units, 2019, np.arange(8760, dtype=float), 8760))


if __name__ == "__main__":
    unittest.main()
