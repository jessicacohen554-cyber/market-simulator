"""Tests for the NEISO winter fuel-inventory seasonal oil-burn budget (A).

Trivial-first (CLAUDE.md testing pattern): the generalized budget-row builder
is exercised on tiny hand-checkable cases, then an end-to-end 1-zone/2-gen LP
confirms a binding budget lifts the *persisted* clearing price via the
constraint dual (the whole point of Component A), then the reader is checked
against the real ISO-NE clean data when present.
"""

from __future__ import annotations

import unittest

import numpy as np

from market_sim.model.dispatch import (
    VariableLayout,
    _build_oil_budget_rows,
    solve_dispatch,
)
from market_sim.data.winter_fuel_inventory import (
    WINTER_MONTH_INDICES,
    apply_winter_fuelsec_mustrun,
    build_winter_fuel_budget,
    read_winter_fuel_study,
)

# Reuse the shared trivial-fleet helper from the dispatch tests.
from tests.test_dispatch import _make_fleet


class TestBuildOilBudgetRows(unittest.TestCase):
    """Structural unit tests for the generalized builder."""

    def _layout(self, n_gen, T):
        return VariableLayout(n_gen=n_gen, n_zones=1, n_storage=0, n_links=0, T=T)

    def test_backward_compatible_per_gen_mwh(self):
        # Default coeff/group: one row per (gen, month), coefficient 1.0 on P.
        T = 24
        layout = self._layout(2, T)
        month_index = np.zeros(T, dtype=int)  # all hour -> month 0
        budget = np.array([[100.0], [200.0]])  # (n_gen, 1 month)
        block, lower, upper = _build_oil_budget_rows(
            layout, np.array([0, 1]), budget, month_index
        )
        self.assertEqual(block.shape, (2, layout.total_columns))
        np.testing.assert_allclose(upper, [100.0, 200.0])
        np.testing.assert_allclose(lower, [0.0, 0.0])
        # Each row sums its generator's P across all T hours with coefficient 1.
        dense = block.toarray()
        self.assertEqual(int(dense[0].sum()), T)  # gen 0 appears in T columns
        self.assertEqual(int(dense[1].sum()), T)

    def test_pooled_group_single_row(self):
        # group_index all-zero -> one pooled row summing both gens per month.
        T = 24
        layout = self._layout(2, T)
        month_index = np.zeros(T, dtype=int)
        budget = np.array([[500.0]])  # (1 group, 1 month)
        block, lower, upper = _build_oil_budget_rows(
            layout,
            np.array([0, 1]),
            budget,
            month_index,
            group_index=np.array([0, 0]),
        )
        self.assertEqual(block.shape, (1, layout.total_columns))
        np.testing.assert_allclose(upper, [500.0])
        self.assertEqual(int(block.toarray()[0].sum()), 2 * T)

    def test_heat_rate_coeff_and_zero_drop(self):
        # coeff = HR on some hours, 0 on others -> zeros dropped, HR kept.
        T = 4
        layout = self._layout(1, T)
        month_index = np.zeros(T, dtype=int)
        budget = np.array([[1000.0]])
        coeff = np.array([[10.0, 0.0, 10.0, 0.0]])  # oil only in hours 0 and 2
        block, _, _ = _build_oil_budget_rows(
            layout,
            np.array([0]),
            budget,
            month_index,
            gen_hour_coeff=coeff,
            group_index=np.array([0]),
        )
        row = block.toarray()[0]
        # Two nonzero entries, each 10.0 (hours 0 and 2); no explicit zeros.
        self.assertEqual(block.nnz, 2)
        np.testing.assert_allclose(row[row != 0.0], [10.0, 10.0])


class TestBindingBudgetLiftsPrice(unittest.TestCase):
    """A binding oil budget's dual raises the persisted clearing price."""

    T = 24

    def _no_renewables(self):
        return dict(
            wind_cf=np.zeros((1, self.T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, self.T)),
            solar_cap=np.zeros(1),
        )

    def _fleet_mc_demand(self):
        # gen0 cheap "oil" (MC 30), gen1 expensive backup (MC 500); demand 50
        # (< each pmax=100 so exactly one gen is marginal per hour).
        fleet = _make_fleet(
            ["Z0", "Z0"], ["Z0"], hours=self.T, pmax=100.0, pmin=0.0, eford=0.0
        )
        mc = np.vstack([np.full(self.T, 30.0), np.full(self.T, 500.0)])
        demand = np.full((1, self.T), 50.0)
        return fleet, mc, demand

    def test_no_budget_prices_at_oil_mc(self):
        fleet, mc, demand = self._fleet_mc_demand()
        result = solve_dispatch(fleet, demand, mc=mc, T=self.T, **self._no_renewables())
        np.testing.assert_allclose(result.prices, 30.0)

    def test_binding_budget_lifts_price_to_backup_parity(self):
        # Cap oil (gen0) at 600 MWh over the month; 50*24 = 1200 MWh needed, so
        # 600 MWh must come from the 500 backup. The budget dual (500-30=470)
        # is added to oil's marginal cost, so every hour clears at 500.
        fleet, mc, demand = self._fleet_mc_demand()
        budget = np.full((1, 12), np.inf)
        budget[0, 0] = 600.0  # month 0 (all T=24 hours map here)
        result = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=self.T,
            oil_gen_idx=np.array([0]),
            oil_monthly_budget=budget,
            oil_month_index=np.zeros(self.T, dtype=int),
            oil_group_index=np.array([0]),
            **self._no_renewables(),
        )
        # Oil budget respected and price lifted to backup parity everywhere.
        self.assertLessEqual(result.dispatch[0].sum(), 600.0 + 1e-6)
        np.testing.assert_allclose(result.prices, 500.0, atol=1e-6)

    def test_hr_weighted_budget_matches_mwh_equivalent(self):
        # coeff = HR (10) with an MMBtu budget of 6000 == a 600 MWh cap.
        fleet, mc, demand = self._fleet_mc_demand()
        budget = np.full((1, 12), np.inf)
        budget[0, 0] = 6000.0  # MMBtu
        coeff = np.full((1, self.T), 10.0)  # HR 10 MMBtu/MWh
        result = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=self.T,
            oil_gen_idx=np.array([0]),
            oil_monthly_budget=budget,
            oil_month_index=np.zeros(self.T, dtype=int),
            oil_gen_hour_coeff=coeff,
            oil_group_index=np.array([0]),
            **self._no_renewables(),
        )
        self.assertLessEqual(result.dispatch[0].sum(), 600.0 + 1e-6)
        np.testing.assert_allclose(result.prices, 500.0, atol=1e-6)


class TestReader(unittest.TestCase):
    """Reader over the real ISO-NE clean data (skipped when absent)."""

    @classmethod
    def setUpClass(cls):
        cls.study = read_winter_fuel_study("NEISO")

    def test_study_scalars(self):
        if self.study is None:
            self.skipTest("no winter-fuel-inventory clean data for ISONE")
        self.assertAlmostEqual(self.study.start_fill_low_bbl, 2_800_000.0)
        self.assertAlmostEqual(self.study.start_fill_high_bbl, 3_800_000.0)
        self.assertAlmostEqual(self.study.delivery_fills_per_season, 2.0)

    def test_build_budget_shapes_and_winter_months(self):
        if self.study is None:
            self.skipTest("no winter-fuel-inventory clean data for ISONE")
        # Synthetic 3-gen fleet: one oil-primary, two gas (no dual-fuel roster
        # match -> excluded), so scope should be exactly the oil-primary gen.
        fleet = _make_fleet(["Z0"], ["Z0"], hours=48, pmax=100.0, pmin=0.0, eford=0.0)
        # Force gen 0 to the oil fuel code.
        from market_sim.data.fleet import FUEL_TYPE_MAP

        fleet.fuel_type_idx[0] = FUEL_TYPE_MAP["oil"]
        out = build_winter_fuel_budget("NEISO", fleet, None, hours=48)
        self.assertIsNotNone(out)
        gen_idx, budget, month_index, coeff, group_index = out
        np.testing.assert_array_equal(gen_idx, [0])
        self.assertEqual(budget.shape, (1, 12))
        self.assertEqual(coeff.shape, (1, 48))
        np.testing.assert_array_equal(group_index, [0])
        # Winter months finite, all others infinite.
        finite = np.isfinite(budget[0])
        np.testing.assert_array_equal(
            np.nonzero(finite)[0], sorted(WINTER_MONTH_INDICES)
        )
        # Budget value = 0.6 * start_fill * 5.825 (low fill default).
        expected = 2_800_000.0 * (1 + 2) / 5 * 5.825
        np.testing.assert_allclose(budget[0, 0], expected)

    def test_start_fill_override_scales_budget(self):
        if self.study is None:
            self.skipTest("no winter-fuel-inventory clean data for ISONE")
        from market_sim.data.fleet import FUEL_TYPE_MAP

        fleet = _make_fleet(["Z0"], ["Z0"], hours=48, pmax=100.0, pmin=0.0, eford=0.0)
        fleet.fuel_type_idx[0] = FUEL_TYPE_MAP["oil"]
        out = build_winter_fuel_budget(
            "NEISO", fleet, None, start_fill_bbl=3_800_000.0, hours=48
        )
        expected = 3_800_000.0 * (1 + 2) / 5 * 5.825
        np.testing.assert_allclose(out[1][0, 0], expected)


class TestWinterFuelsecMustrun(unittest.TestCase):
    """Component B — winter fuel-security must-run floor (trivial-first).

    A 3-gen 1-zone fleet (2 COAL_BIT + 1 CT_PEAKER) over a full 8760, with the
    zone TMIN monkeypatched to a controlled cold-January / warm-rest series, so
    the season+cold gate, class scope, depth, and D-2 mechanism tag are all
    hand-checkable without loading real weather.
    """

    def _fleet(self, hours=8760):
        # 3 gens in a real NEISO zone ("Central" -> the engine's zone lookup
        # resolves); classes set post-build (generators_to_fleet_arrays leaves
        # plant_group None for these bare Generators).
        fa = _make_fleet(
            ["Central", "Central", "Central"],
            ["Central"],
            hours=hours,
            pmax=100.0,
            pmin=0.0,
            eford=0.0,
        )
        fa.plant_group = np.array(["COAL_BIT", "COAL_BIT", "CT_PEAKER"], dtype=object)
        return fa

    def _patch_tmin(self, cold_month_indices, cold_c=-15.0, warm_c=10.0, hours=8760):
        """Return an iso_zone_tmax stub: cold in the given calendar months."""
        from market_sim.data.fleet import _hour_to_month_index

        month = _hour_to_month_index(hours)
        tmin = np.where(np.isin(month, cold_month_indices), cold_c, warm_c).astype(
            float
        )
        tmax = tmin + 5.0
        return lambda iso, year, T, zone=None: (tmax[:T], tmin[:T])

    def test_floors_coal_in_winter_cold_only(self):
        import market_sim.data.eia_loader as eia_loader
        from market_sim.data.floor_mechanisms import MECH_WINTER_FUELSEC

        hours = 8760
        fa = self._fleet(hours)
        orig = eia_loader.iso_zone_tmax
        # Cold January (month 0, in WINTER_MONTH_INDICES) only.
        eia_loader.iso_zone_tmax = self._patch_tmin([0], hours=hours)
        try:
            applied = apply_winter_fuelsec_mustrun(
                fa, "NEISO", 2024, ["Central"], hours=hours
            )
        finally:
            eia_loader.iso_zone_tmax = orig
        self.assertTrue(applied)
        self.assertIsNotNone(fa.min_gen)
        from market_sim.data.fleet import _hour_to_month_index

        jan = _hour_to_month_index(hours) == 0
        jul = _hour_to_month_index(hours) == 6
        # COAL_BIT group (gens 0,1) floored cheapest-first at frac x GROUP avail:
        # 0.4 * (2*100) = 80 MW/hr total across the class in January...
        coal_total_jan = fa.min_gen[0, jan] + fa.min_gen[1, jan]
        np.testing.assert_allclose(coal_total_jan, 80.0)
        # ...and untouched (pmin=0) outside winter for both units.
        np.testing.assert_allclose(fa.min_gen[0, jul], 0.0)
        np.testing.assert_allclose(fa.min_gen[1, jul], 0.0)
        # Every floored COAL unit-hour carries the winter-fuelsec D-2 tag.
        coal_floored = fa.min_gen[:2, :] > 0.0
        self.assertTrue(np.any(coal_floored))
        self.assertTrue(
            np.all(fa.min_gen_mechanism[:2, :][coal_floored] == MECH_WINTER_FUELSEC)
        )
        # Floored COAL unit-hours are exactly the January (winter-cold) hours.
        self.assertTrue(np.all(coal_floored[:, ~jan] == False))  # noqa: E712
        # CT_PEAKER (gen 2) is NOT a fuel-secure class -> never floored.
        np.testing.assert_allclose(fa.min_gen[2, :], 0.0)

    def test_no_op_when_winter_is_warm(self):
        import market_sim.data.eia_loader as eia_loader

        hours = 8760
        fa = self._fleet(hours)
        orig = eia_loader.iso_zone_tmax
        # No cold month at all (warm everywhere) -> nothing flags.
        eia_loader.iso_zone_tmax = self._patch_tmin([], hours=hours)
        try:
            applied = apply_winter_fuelsec_mustrun(
                fa, "NEISO", 2024, ["Central"], hours=hours
            )
        finally:
            eia_loader.iso_zone_tmax = orig
        self.assertFalse(applied)
        self.assertIsNone(fa.min_gen)

    def test_summer_cold_does_not_bind_season_gate(self):
        import market_sim.data.eia_loader as eia_loader

        hours = 8760
        fa = self._fleet(hours)
        orig = eia_loader.iso_zone_tmax
        # Cold in July (month 6, NOT in WINTER_MONTH_INDICES) -> season gate
        # blocks it; the floor must not bind.
        eia_loader.iso_zone_tmax = self._patch_tmin([6], hours=hours)
        try:
            applied = apply_winter_fuelsec_mustrun(
                fa, "NEISO", 2024, ["Central"], hours=hours
            )
        finally:
            eia_loader.iso_zone_tmax = orig
        self.assertFalse(applied)

    def test_commit_frac_and_min_stable_scale_depth(self):
        import market_sim.data.eia_loader as eia_loader

        hours = 8760
        fa = self._fleet(hours)
        orig = eia_loader.iso_zone_tmax
        eia_loader.iso_zone_tmax = self._patch_tmin([0], hours=hours)
        try:
            apply_winter_fuelsec_mustrun(
                fa,
                "NEISO",
                2024,
                ["Central"],
                min_stable_pct=0.5,
                commit_frac=0.5,
                hours=hours,
            )
        finally:
            eia_loader.iso_zone_tmax = orig
        from market_sim.data.fleet import _hour_to_month_index

        jan = _hour_to_month_index(hours) == 0
        # cheapest-first distributes 0.25 * (group avail cap) across the 2 COAL
        # units; total floored group energy per hour = 0.25 * 200 = 50 MW.
        total = fa.min_gen[0, jan] + fa.min_gen[1, jan]
        np.testing.assert_allclose(total, 50.0)


if __name__ == "__main__":
    unittest.main()
