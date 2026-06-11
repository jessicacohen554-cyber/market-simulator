"""Tests for the hydro monthly energy-budget module.

Covers the dispatch constraint family (vectorized month-budget rows, the
default-off identical-LP guard, min-flow lower bounds and price-following
behaviour) and the EIA-923/EIA-860 budget loader in
:mod:`market_sim.data.hydro`.
"""

import unittest

import numpy as np

from market_sim.data.fleet import (
    FUEL_TYPE_MAP,
    Generator,
    generators_to_fleet_arrays,
)
from market_sim.data.hydro import hours_per_month, load_hydro_budget
from market_sim.model.dispatch import (
    VariableLayout,
    build_constraints,
    solve_dispatch,
)


def _hydro_fleet(hours, hydro_pmax=50.0, hydro_pmin=0.0):
    """Return a fleet with one hydro gen plus cheap and peaking thermal.

    Generator order: ``[hydro, cheap thermal, peaking thermal]`` in a single
    zone ``Z``. EFORD is zeroed so availability is exactly 1.0 and the budget
    arithmetic is exact.
    """
    gens = [
        Generator(
            unit_id="H0", name="H0", zone="Z", fuel_type="hydro",
            pmax_mw=hydro_pmax, pmin_mw=hydro_pmin, eford=0.0,
        ),
        Generator(
            unit_id="C0", name="C0", zone="Z", fuel_type="gas_cc",
            pmax_mw=50.0, pmin_mw=0.0, eford=0.0,
        ),
        Generator(
            unit_id="E0", name="E0", zone="Z", fuel_type="gas_ct",
            pmax_mw=200.0, pmin_mw=0.0, eford=0.0,
        ),
    ]
    return generators_to_fleet_arrays(gens, ["Z"], hours=hours)


# Marginal cost: hydro free, cheap thermal $10, peaking thermal $100.
def _mc(hours):
    """Return the ``(3, hours)`` marginal-cost array for ``_hydro_fleet``."""
    return np.array(
        [[0.0] * hours, [10.0] * hours, [100.0] * hours], dtype=float
    )


class TestHydroConstraintFamily(unittest.TestCase):
    """Tests for the hydro budget rows in ``build_constraints``."""

    def setUp(self):
        self.T = 4
        self.fleet = _hydro_fleet(self.T)
        self.layout = VariableLayout(
            n_gen=3, n_zones=1, n_storage=0, n_links=0, T=self.T
        )
        self.demand = np.array([[40.0, 40.0, 130.0, 120.0]])
        # Two months: hours {0,1} -> month 0, hours {2,3} -> month 1.
        self.month_idx = np.array([0, 0, 1, 1])
        self.budget = np.array([[80.0, 90.0]])  # one hydro gen, two months

    def test_none_is_identical_to_current_build(self):
        # The default-off guard: passing hydro_monthly_energy=None must yield
        # a byte-identical constraint system to the current (kwarg-free) build,
        # even though the fleet contains a hydro generator (a flat thermal
        # block today).
        a0, lo0, hi0 = build_constraints(self.layout, self.fleet, self.demand)
        a1, lo1, hi1 = build_constraints(
            self.layout, self.fleet, self.demand, hydro_monthly_energy=None
        )
        self.assertEqual(a0.shape, a1.shape)
        self.assertEqual((a0 != a1).nnz, 0)
        np.testing.assert_array_equal(a0.indptr, a1.indptr)
        np.testing.assert_array_equal(a0.indices, a1.indices)
        np.testing.assert_array_equal(a0.data, a1.data)
        np.testing.assert_array_equal(lo0, lo1)
        np.testing.assert_array_equal(hi0, hi1)

    def test_family_adds_one_row_per_gen_month(self):
        a0, _, _ = build_constraints(self.layout, self.fleet, self.demand)
        a1, _, _ = build_constraints(
            self.layout, self.fleet, self.demand,
            hydro_monthly_energy=self.budget, hydro_month_index=self.month_idx,
        )
        # 1 hydro gen x 2 months = 2 new rows.
        self.assertEqual(a1.shape[0], a0.shape[0] + 2)

    def test_row_columns_match_hydro_p_slots_by_month(self):
        a0, _, _ = build_constraints(self.layout, self.fleet, self.demand)
        a1, lo, hi = build_constraints(
            self.layout, self.fleet, self.demand,
            hydro_monthly_energy=self.budget, hydro_month_index=self.month_idx,
        )
        rows = a1[a0.shape[0]:].toarray()
        # Hydro is generator 0; its P columns are p_col(0, t).
        month0_cols = sorted(self.layout.p_col(0, t) for t in (0, 1))
        month1_cols = sorted(self.layout.p_col(0, t) for t in (2, 3))
        np.testing.assert_array_equal(np.flatnonzero(rows[0]), month0_cols)
        np.testing.assert_array_equal(np.flatnonzero(rows[1]), month1_cols)
        np.testing.assert_array_equal(rows[rows != 0], np.ones(4))
        # Upper bounds are the monthly budget; default lower bound is zero.
        np.testing.assert_array_equal(hi[-2:], [80.0, 90.0])
        np.testing.assert_array_equal(lo[-2:], [0.0, 0.0])

    def test_gen_idx_auto_derived_from_fuel_type(self):
        # Explicit hydro_gen_idx and the auto-derived subset agree.
        auto_a, _, auto_hi = build_constraints(
            self.layout, self.fleet, self.demand,
            hydro_monthly_energy=self.budget, hydro_month_index=self.month_idx,
        )
        hydro_idx = np.flatnonzero(
            np.asarray(self.fleet.fuel_type_idx) == FUEL_TYPE_MAP["hydro"]
        )
        self.assertEqual(list(hydro_idx), [0])
        expl_a, _, expl_hi = build_constraints(
            self.layout, self.fleet, self.demand,
            hydro_monthly_energy=self.budget, hydro_month_index=self.month_idx,
            hydro_gen_idx=hydro_idx,
        )
        self.assertEqual((auto_a != expl_a).nnz, 0)

    def test_min_flow_lower_bounds_applied(self):
        # The min-flow floor lands on the row lower bounds.
        monthly_min = np.array([[20.0, 30.0]])
        _, lo, hi = build_constraints(
            self.layout, self.fleet, self.demand,
            hydro_monthly_energy=self.budget, hydro_month_index=self.month_idx,
            hydro_monthly_min=monthly_min,
        )
        np.testing.assert_array_equal(lo[-2:], [20.0, 30.0])
        np.testing.assert_array_equal(hi[-2:], [80.0, 90.0])

    def test_empty_hydro_subset_adds_no_rows(self):
        # A fleet with no hydro generators adds nothing even when a budget
        # array is passed (the auto-derived subset is empty).
        gens = [
            Generator(
                unit_id="C0", name="C0", zone="Z", fuel_type="gas_cc",
                pmax_mw=50.0, pmin_mw=0.0, eford=0.0,
            )
        ]
        fleet = generators_to_fleet_arrays(gens, ["Z"], hours=self.T)
        layout = VariableLayout(
            n_gen=1, n_zones=1, n_storage=0, n_links=0, T=self.T
        )
        a0, _, _ = build_constraints(layout, fleet, self.demand)
        a1, _, _ = build_constraints(
            layout, fleet, self.demand,
            hydro_monthly_energy=np.empty((0, 2)),
            hydro_month_index=self.month_idx,
        )
        self.assertEqual(a0.shape, a1.shape)


class TestHydroDispatch(unittest.TestCase):
    """End-to-end solves exercising the hydro budget behaviour."""

    def setUp(self):
        self.T = 4
        self.fleet = _hydro_fleet(self.T)
        self.demand = np.array([[40.0, 40.0, 130.0, 120.0]])
        self.mc = _mc(self.T)
        self.wind_cf = np.zeros((1, self.T))
        self.solar_cf = np.zeros((1, self.T))
        self.cap = np.zeros(1)

    def _solve(self, **kwargs):
        return solve_dispatch(
            self.fleet, self.demand, self.wind_cf, self.cap,
            self.solar_cf, self.cap, mc=self.mc, voll=5000.0, **kwargs,
        )

    def test_budget_respected_and_shifts_to_high_price_hours(self):
        # Single month covering all four hours; prices are $10 in hours 0-1
        # (cheap thermal marginal) and $100 in hours 2-3 (peaker marginal).
        month_idx = np.zeros(self.T, dtype=int)
        budget = np.array([[60.0]])
        res = self._solve(
            hydro_monthly_energy=budget, hydro_month_index=month_idx
        )
        hydro = res.dispatch[0]
        # Budget is binding and respected.
        self.assertAlmostEqual(hydro.sum(), 60.0, places=4)
        self.assertLessEqual(hydro.sum(), 60.0 + 1e-6)
        # All the limited energy goes to the high-price hours.
        self.assertAlmostEqual(hydro[:2].sum(), 0.0, places=4)
        self.assertAlmostEqual(hydro[2:].sum(), 60.0, places=4)
        np.testing.assert_allclose(res.prices[0], [10.0, 10.0, 100.0, 100.0])

    def test_budget_binds_below_unconstrained_output(self):
        # Without a budget the free hydro runs in every hour; the budget
        # strictly reduces its total energy.
        free = self._solve()
        month_idx = np.zeros(self.T, dtype=int)
        capped = self._solve(
            hydro_monthly_energy=np.array([[60.0]]), hydro_month_index=month_idx
        )
        self.assertGreater(free.dispatch[0].sum(), capped.dispatch[0].sum())
        self.assertAlmostEqual(capped.dispatch[0].sum(), 60.0, places=4)

    def test_none_solution_unchanged_vs_current_build(self):
        # Default-off reproduces today's flat-thermal-block solution exactly:
        # solving with hydro_monthly_energy=None equals the kwarg-free solve.
        base = self._solve()
        off = self._solve(hydro_monthly_energy=None)
        np.testing.assert_array_equal(base.dispatch, off.dispatch)
        np.testing.assert_array_equal(base.prices, off.prices)
        self.assertEqual(base.objective_value, off.objective_value)

    def test_min_flow_floor_forces_minimum_monthly_energy(self):
        # A monthly minimum forces hydro to deliver at least that energy even
        # in the cheap month, where it would otherwise stay idle.
        month_idx = np.array([0, 0, 1, 1])
        # Generous caps; floor of 30 MWh in the cheap month (hours 0-1).
        budget = np.array([[100.0, 100.0]])
        monthly_min = np.array([[30.0, 0.0]])
        res = self._solve(
            hydro_monthly_energy=budget, hydro_month_index=month_idx,
            hydro_monthly_min=monthly_min,
        )
        cheap_month = res.dispatch[0][:2].sum()
        self.assertGreaterEqual(cheap_month, 30.0 - 1e-6)


class TestHydroBudgetLoader(unittest.TestCase):
    """Tests for ``load_hydro_budget`` and ``HydroBudget``."""

    def test_loads_ercot_budget_shapes(self):
        hb = load_hydro_budget("ERCOT", 2023)
        self.assertGreater(hb.n_hydro, 0)
        self.assertEqual(hb.monthly_energy.shape, (hb.n_hydro, 12))
        self.assertEqual(hb.min_mw.shape, (hb.n_hydro,))
        self.assertEqual(hb.max_mw.shape, (hb.n_hydro,))
        self.assertEqual(len(hb.plant_names), hb.n_hydro)
        # Plant ids are unique, sorted ascending; budgets and capacity are
        # non-negative; some plant carries real nameplate.
        self.assertTrue(np.all(np.diff(hb.plant_ids) > 0))
        self.assertTrue(np.all(hb.monthly_energy >= 0.0))
        self.assertTrue(np.all(hb.max_mw > 0.0))
        self.assertGreater(hb.monthly_energy.sum(), 0.0)

    def test_min_flow_fraction_scales_min_mw(self):
        zero = load_hydro_budget("ERCOT", 2023)
        self.assertEqual(zero.min_mw.sum(), 0.0)
        frac = load_hydro_budget("ERCOT", 2023, min_flow_fraction=0.1)
        np.testing.assert_allclose(frac.min_mw, 0.1 * frac.max_mw)

    def test_monthly_min_energy_matches_min_flow(self):
        hb = load_hydro_budget("ERCOT", 2023, min_flow_fraction=0.2)
        hpm = hours_per_month()
        mm = hb.monthly_min_energy(hpm)
        self.assertEqual(mm.shape, (hb.n_hydro, 12))
        # The floor is the sustained min-flow energy, clipped to the monthly
        # budget so the two-sided dispatch row stays feasible (lower <= upper)
        # in low-inflow months.
        raw = hb.min_mw[:, None] * hpm[None, :]
        np.testing.assert_allclose(mm, np.minimum(raw, hb.monthly_energy))
        self.assertTrue(np.all(mm <= hb.monthly_energy + 1e-9))
        # The clip binds somewhere (ERCOT hydro has months well below 20% CF)
        # but not everywhere.
        self.assertTrue(np.any(mm < raw))
        self.assertTrue(np.any(mm == raw))

    def test_align_to_reorders_to_fleet_subset(self):
        hb = load_hydro_budget("ERCOT", 2023)
        # Request a reordered subset of two plants; align must follow it and
        # drop a plant code that the budget does not cover.
        codes = [int(hb.plant_ids[3]), int(hb.plant_ids[1]), -1]
        local_idx, energy, min_mw, max_mw = hb.align_to(codes)
        np.testing.assert_array_equal(local_idx, [0, 1])
        np.testing.assert_allclose(energy[0], hb.monthly_energy[3])
        np.testing.assert_allclose(energy[1], hb.monthly_energy[1])
        np.testing.assert_allclose(max_mw, hb.max_mw[[3, 1]])

    def test_unknown_iso_year_raises(self):
        with self.assertRaises(ValueError):
            load_hydro_budget("ERCOT", 1901)

    def test_hours_per_month_sums_to_year(self):
        hpm = hours_per_month()
        self.assertEqual(hpm.shape, (12,))
        self.assertEqual(int(hpm.sum()), 8760)


class TestCAISOHydroBudget(unittest.TestCase):
    """CAISO hydro energy budgets from EIA-923 (multi-iso P4).

    Anchors: EIA-923 CISO conventional-hydro (prime mover ``HY``) monthly
    net generation sums to 23.90 TWh (2023, extreme wet year) and 21.48 TWh
    (2024). EIA-930 CISO cross-check: 24.40 TWh 2023 (hydro incl. PS net —
    the pre-2024 schema does not split them) and ~22.8 TWh 2024
    (12.51 Jan-Jun incl-PS + 10.25 Jul-Dec excl-PS across the schema split).
    The famous ~2x wet/dry swing is 2022-vs-2023; within the 2023-2025 data
    window the swing is 2023 -> 2024 at about +11%.
    """

    # EIA-923 anchors (TWh) — regression guards on the BA filter, the
    # plant aggregation and the negative-month clip.
    EIA923_TWH = {2023: 23.90, 2024: 21.48}
    # EIA-930 CISO hydro (TWh) — the sanity cross-check source.
    EIA930_TWH = {2023: 24.40, 2024: 22.76}

    def test_totals_match_eia923_anchors(self):
        for year, expected in self.EIA923_TWH.items():
            hb = load_hydro_budget("CAISO", year)
            total = hb.monthly_energy.sum() / 1e6
            self.assertAlmostEqual(total, expected, delta=0.01 * expected)

    def test_totals_within_10pct_of_eia930(self):
        for year, expected in self.EIA930_TWH.items():
            hb = load_hydro_budget("CAISO", year)
            total = hb.monthly_energy.sum() / 1e6
            self.assertLess(abs(total - expected) / expected, 0.10)

    def test_wet_2023_exceeds_2024(self):
        wet = load_hydro_budget("CAISO", 2023).monthly_energy.sum()
        nxt = load_hydro_budget("CAISO", 2024).monthly_energy.sum()
        ratio = wet / nxt
        self.assertGreater(ratio, 1.05)
        self.assertLess(ratio, 1.25)

    def test_zones_resolve_to_caiso_topology(self):
        hb = load_hydro_budget("CAISO", 2023)
        self.assertTrue(set(hb.zones) <= {"NP15", "ZP26", "SP15"})
        # Sierra/Cascade hydro concentrates north of Path 26: NP15 carries
        # the bulk of the nameplate.
        np15_mw = hb.max_mw[np.array(hb.zones) == "NP15"].sum()
        self.assertGreater(np15_mw, 0.7 * hb.max_mw.sum())

    def test_2025_backfill_recovers_survey_only_coverage(self):
        # The 2025 EIA-923 early release carries only the monthly-survey
        # reporters: 26 CAISO plants, ~12.3 TWh vs ~21.4 TWh actual
        # (EIA-930 excl-PS). Backfilling non-reporters from 2024 recovers
        # the fleet to within 10% of the EIA-930 total.
        bare = load_hydro_budget("CAISO", 2025)
        self.assertLess(bare.n_hydro, 50)
        filled = load_hydro_budget("CAISO", 2025, backfill_year=2024)
        self.assertGreater(filled.n_hydro, 150)
        total = filled.monthly_energy.sum() / 1e6
        self.assertLess(abs(total - 21.35) / 21.35, 0.10)
        # Reporters keep their 2025 budgets — only non-reporters are filled.
        self.assertGreater(
            filled.monthly_energy.sum(), bare.monthly_energy.sum()
        )

    def test_dispatch_respects_real_monthly_budgets(self):
        # End-to-end: the three largest CAISO hydro plants dispatched over
        # January + February 2023 at their real EIA-923 budgets. Hydro is
        # the cheapest unit, so each plant-month budget binds from above:
        # dispatch <= budget always, == min(budget, nameplate-hours) here.
        hb = load_hydro_budget("CAISO", 2023)
        top = np.argsort(hb.max_mw)[-3:]
        pmax = hb.max_mw[top]
        budget = hb.monthly_energy[top][:, :2]  # (3 plants, Jan + Feb)
        hpm = hours_per_month()[:2]
        T = int(hpm.sum())
        month_idx = np.repeat([0, 1], hpm)

        gens = [
            Generator(
                unit_id=f"H{i}", name=f"H{i}", zone="Z", fuel_type="hydro",
                pmax_mw=float(pmax[i]), pmin_mw=0.0, eford=0.0,
            )
            for i in range(3)
        ]
        peak_demand = float(pmax.sum()) + 500.0
        gens.append(
            Generator(
                unit_id="G0", name="G0", zone="Z", fuel_type="gas_cc",
                pmax_mw=peak_demand + 100.0, pmin_mw=0.0, eford=0.0,
            )
        )
        fleet = generators_to_fleet_arrays(gens, ["Z"], hours=T)
        demand = np.full((1, T), peak_demand)
        mc = np.vstack([np.zeros((3, T)), np.full((1, T), 50.0)])
        res = solve_dispatch(
            fleet, demand, np.zeros((1, T)), np.zeros(1),
            np.zeros((1, T)), np.zeros(1), mc=mc, voll=5000.0,
            hydro_monthly_energy=budget, hydro_month_index=month_idx,
        )
        for g in range(3):
            for m in range(2):
                dispatched = res.dispatch[g][month_idx == m].sum()
                self.assertLessEqual(dispatched, budget[g, m] * (1 + 1e-6))
                expected = min(budget[g, m], pmax[g] * hpm[m])
                self.assertAlmostEqual(
                    dispatched, expected, delta=1e-3 * max(expected, 1.0)
                )


class TestOtherISOBudgetsUnchanged(unittest.TestCase):
    """PJM / ERCOT hydro budgets are untouched by the CAISO P4 stage."""

    def test_pjm_2023_budget_regression(self):
        hb = load_hydro_budget("PJM", 2023)
        self.assertEqual(hb.n_hydro, 72)
        self.assertAlmostEqual(
            hb.monthly_energy.sum() / 1e6, 8.976, delta=0.05
        )
        self.assertAlmostEqual(hb.max_mw.sum(), 3288.0, delta=20.0)

    def test_ercot_2023_budget_regression(self):
        hb = load_hydro_budget("ERCOT", 2023)
        self.assertEqual(hb.n_hydro, 14)
        self.assertAlmostEqual(
            hb.monthly_energy.sum() / 1e6, 0.350, delta=0.005
        )


if __name__ == "__main__":
    unittest.main()
