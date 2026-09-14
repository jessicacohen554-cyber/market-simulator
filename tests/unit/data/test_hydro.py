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
from market_sim.data.eia_loader import measured_monthly_hydro
from market_sim.data.hydro import hours_per_month, load_hydro_budget
from market_sim.model.dispatch import (
    VariableLayout,
    build_constraints,
    solve_dispatch,
)
from tests.helpers import REPO_ROOT
from tests.helpers.base import CleanDirTestCase


def _hydro_fleet(hours, hydro_pmax=50.0, hydro_pmin=0.0):
    """Return a fleet with one hydro gen plus cheap and peaking thermal.

    Generator order: ``[hydro, cheap thermal, peaking thermal]`` in a single
    zone ``Z``. EFORD is zeroed so availability is exactly 1.0 and the budget
    arithmetic is exact.
    """
    gens = [
        Generator(
            unit_id="H0",
            name="H0",
            zone="Z",
            fuel_type="hydro",
            pmax_mw=hydro_pmax,
            pmin_mw=hydro_pmin,
            eford=0.0,
        ),
        Generator(
            unit_id="C0",
            name="C0",
            zone="Z",
            fuel_type="gas_cc",
            pmax_mw=50.0,
            pmin_mw=0.0,
            eford=0.0,
        ),
        Generator(
            unit_id="E0",
            name="E0",
            zone="Z",
            fuel_type="gas_ct",
            pmax_mw=200.0,
            pmin_mw=0.0,
            eford=0.0,
        ),
    ]
    return generators_to_fleet_arrays(gens, ["Z"], hours=hours)


# Marginal cost: hydro free, cheap thermal $10, peaking thermal $100.
def _mc(hours):
    """Return the ``(3, hours)`` marginal-cost array for ``_hydro_fleet``."""
    return np.array([[0.0] * hours, [10.0] * hours, [100.0] * hours], dtype=float)


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
        a0, lo0, hi0, *_ = build_constraints(self.layout, self.fleet, self.demand)
        a1, lo1, hi1, *_ = build_constraints(
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
        a0, _, _, *_ = build_constraints(self.layout, self.fleet, self.demand)
        a1, _, _, *_ = build_constraints(
            self.layout,
            self.fleet,
            self.demand,
            hydro_monthly_energy=self.budget,
            hydro_month_index=self.month_idx,
        )
        # 1 hydro gen x 2 months = 2 new rows.
        self.assertEqual(a1.shape[0], a0.shape[0] + 2)

    def test_row_columns_match_hydro_p_slots_by_month(self):
        a0, _, _, *_ = build_constraints(self.layout, self.fleet, self.demand)
        a1, lo, hi, *_ = build_constraints(
            self.layout,
            self.fleet,
            self.demand,
            hydro_monthly_energy=self.budget,
            hydro_month_index=self.month_idx,
        )
        rows = a1[a0.shape[0] :].toarray()
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
        auto_a, _, auto_hi, *_ = build_constraints(
            self.layout,
            self.fleet,
            self.demand,
            hydro_monthly_energy=self.budget,
            hydro_month_index=self.month_idx,
        )
        hydro_idx = np.flatnonzero(
            np.asarray(self.fleet.fuel_type_idx) == FUEL_TYPE_MAP["hydro"]
        )
        self.assertEqual(list(hydro_idx), [0])
        expl_a, _, expl_hi, *_ = build_constraints(
            self.layout,
            self.fleet,
            self.demand,
            hydro_monthly_energy=self.budget,
            hydro_month_index=self.month_idx,
            hydro_gen_idx=hydro_idx,
        )
        self.assertEqual((auto_a != expl_a).nnz, 0)

    def test_min_flow_lower_bounds_applied(self):
        # The min-flow floor lands on the row lower bounds.
        monthly_min = np.array([[20.0, 30.0]])
        _, lo, hi, *_ = build_constraints(
            self.layout,
            self.fleet,
            self.demand,
            hydro_monthly_energy=self.budget,
            hydro_month_index=self.month_idx,
            hydro_monthly_min=monthly_min,
        )
        np.testing.assert_array_equal(lo[-2:], [20.0, 30.0])
        np.testing.assert_array_equal(hi[-2:], [80.0, 90.0])

    def test_empty_hydro_subset_adds_no_rows(self):
        # A fleet with no hydro generators adds nothing even when a budget
        # array is passed (the auto-derived subset is empty).
        gens = [
            Generator(
                unit_id="C0",
                name="C0",
                zone="Z",
                fuel_type="gas_cc",
                pmax_mw=50.0,
                pmin_mw=0.0,
                eford=0.0,
            )
        ]
        fleet = generators_to_fleet_arrays(gens, ["Z"], hours=self.T)
        layout = VariableLayout(n_gen=1, n_zones=1, n_storage=0, n_links=0, T=self.T)
        a0, _, _, *_ = build_constraints(layout, fleet, self.demand)
        a1, _, _, *_ = build_constraints(
            layout,
            fleet,
            self.demand,
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
            self.fleet,
            self.demand,
            self.wind_cf,
            self.cap,
            self.solar_cf,
            self.cap,
            mc=self.mc,
            voll=5000.0,
            **kwargs,
        )

    def test_budget_respected_and_shifts_to_high_price_hours(self):
        # Single month covering all four hours; prices are $10 in hours 0-1
        # (cheap thermal marginal) and $100 in hours 2-3 (peaker marginal).
        month_idx = np.zeros(self.T, dtype=int)
        budget = np.array([[60.0]])
        res = self._solve(hydro_monthly_energy=budget, hydro_month_index=month_idx)
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

    def test_trivial_one_unit_one_zone_31_days_respects_monthly_budget(self):
        # Acceptance criterion #4: 1 hydro unit, 1 zone, 24 hours x 31 days.
        # The single hydro plant's total generation over the month must not
        # exceed its monthly energy budget, while it is free to shift WHEN it
        # generates within the 744 hours.
        hours = 24 * 31  # 744-hour single calendar month
        fleet = _hydro_fleet(hours)
        # Demand the cheap thermal can always meet, so hydro is purely
        # economic; a price spike in the last day pulls hydro into those hours.
        demand = np.full((1, hours), 40.0)
        demand[0, -24:] = 130.0  # day-31 peak draws hydro to its budget
        mc = _mc(hours)
        month_idx = np.zeros(hours, dtype=int)  # all hours -> month 0
        budget = np.array([[600.0]])  # one unit, one month (MWh)
        res = solve_dispatch(
            fleet,
            demand,
            np.zeros((1, hours)),
            np.zeros(1),
            np.zeros((1, hours)),
            np.zeros(1),
            mc=mc,
            voll=5000.0,
            hydro_monthly_energy=budget,
            hydro_gen_idx=np.array([0]),
            hydro_month_index=month_idx,
        )
        hydro = res.dispatch[0]
        self.assertLessEqual(hydro.sum(), 600.0 + 1e-6)
        # The budget binds (peak hours alone exceed it), so it is fully used.
        self.assertAlmostEqual(hydro.sum(), 600.0, places=3)
        # Energy is concentrated in the high-price final day, not spread flat.
        self.assertGreater(hydro[-24:].sum(), hydro[:-24].sum())

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
            hydro_monthly_energy=budget,
            hydro_month_index=month_idx,
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

    def test_backfill_carries_nonreporting_prior_year_plants(self):
        # NEISO 2025 EIA-923 is a monthly-survey-only early release: only a
        # handful of large hydro plants have filed, so a current-year budget
        # under-counts conventional hydro by ~6 TWh. backfill_year=2024 carries
        # the plants that reported in 2024 but not 2025 at their 2024 inflow.
        bare = load_hydro_budget("NEISO", 2025)
        filled = load_hydro_budget("NEISO", 2025, backfill_year=2024)
        self.assertGreater(filled.n_hydro, bare.n_hydro)
        self.assertGreater(filled.monthly_energy.sum(), 5.0 * bare.monthly_energy.sum())
        # The plants that DID report 2025 keep their as-reported budget — the
        # backfill only adds the missing ones, never overwrites a filer.
        for pid in bare.plant_ids:
            i_bare = list(bare.plant_ids).index(int(pid))
            i_full = list(filled.plant_ids).index(int(pid))
            np.testing.assert_allclose(
                filled.monthly_energy[i_full], bare.monthly_energy[i_bare]
            )

    def test_backfill_none_is_identical_to_current_build(self):
        # The default (no backfill) must be byte-for-byte the prior behaviour,
        # so every existing ISO/year run is unchanged.
        a = load_hydro_budget("NEISO", 2025)
        b = load_hydro_budget("NEISO", 2025, backfill_year=None)
        np.testing.assert_array_equal(a.plant_ids, b.plant_ids)
        np.testing.assert_allclose(a.monthly_energy, b.monthly_energy)

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
        # Post-SP15-split load zones (c28d57b1, 2026-07-09: SP15 ->
        # LA_BASIN / SDGE / SP15_rest; 0f14b757 re-pointed the literals).
        hb = load_hydro_budget("CAISO", 2023)
        self.assertTrue(
            set(hb.zones) <= {"NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest"}
        )
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
        self.assertGreater(filled.monthly_energy.sum(), bare.monthly_energy.sum())

    def test_measured_monthly_hydro_repins_incomplete_2025(self):
        # measured_monthly_hydro exists to repin the incomplete 2025 EIA-923
        # vintage to the EIA-930 metered total. The CISO 2025 hourly extract is
        # 8751 local-year rows (9 short of a clean 8760), so the strict frame
        # loader rejected it and the repin silently no-oped on the one year it
        # is meant to fix. The gap-filling loader bridges the hole.
        target = measured_monthly_hydro("CAISO", 2025)
        self.assertIsNotNone(target)
        self.assertEqual(target.shape, (12,))
        self.assertLess(abs(target.sum() / 1e6 - 21.32) / 21.32, 0.02)
        # 2023/2024 have clean frames and are unchanged by the gap-filler.
        self.assertAlmostEqual(
            measured_monthly_hydro("CAISO", 2023).sum() / 1e6, 24.40, delta=0.1
        )

    def test_2025_eia930_repin_recovers_full_budget(self):
        # With monthly_target_mwh from EIA-930, the 26 survey-only reporters'
        # energy is scaled up so the 2025 budget total matches the measured
        # ~21.3 TWh (vs the bare 12.3 TWh early-release undercount), without
        # adding plants (the MW envelope stays physical).
        bare = load_hydro_budget("CAISO", 2025)
        target = measured_monthly_hydro("CAISO", 2025)
        repinned = load_hydro_budget("CAISO", 2025, monthly_target_mwh=target)
        self.assertEqual(repinned.n_hydro, bare.n_hydro)
        total = repinned.monthly_energy.sum() / 1e6
        self.assertLess(abs(total - 21.32) / 21.32, 0.02)
        self.assertGreater(total, bare.monthly_energy.sum() / 1e6 + 8.0)

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
                unit_id=f"H{i}",
                name=f"H{i}",
                zone="Z",
                fuel_type="hydro",
                pmax_mw=float(pmax[i]),
                pmin_mw=0.0,
                eford=0.0,
            )
            for i in range(3)
        ]
        peak_demand = float(pmax.sum()) + 500.0
        gens.append(
            Generator(
                unit_id="G0",
                name="G0",
                zone="Z",
                fuel_type="gas_cc",
                pmax_mw=peak_demand + 100.0,
                pmin_mw=0.0,
                eford=0.0,
            )
        )
        fleet = generators_to_fleet_arrays(gens, ["Z"], hours=T)
        demand = np.full((1, T), peak_demand)
        mc = np.vstack([np.zeros((3, T)), np.full((1, T), 50.0)])
        res = solve_dispatch(
            fleet,
            demand,
            np.zeros((1, T)),
            np.zeros(1),
            np.zeros((1, T)),
            np.zeros(1),
            mc=mc,
            voll=5000.0,
            hydro_monthly_energy=budget,
            hydro_month_index=month_idx,
        )
        for g in range(3):
            for m in range(2):
                dispatched = res.dispatch[g][month_idx == m].sum()
                self.assertLessEqual(dispatched, budget[g, m] * (1 + 1e-6))
                expected = min(budget[g, m], pmax[g] * hpm[m])
                self.assertAlmostEqual(
                    dispatched, expected, delta=1e-3 * max(expected, 1.0)
                )


class TestNEISOHydroBudget(unittest.TestCase):
    """NEISO hydro energy budgets from EIA-923 (P4 hydro+PS stage).

    ISO-NE conventional hydro is modest — 8.55 TWh (2023), 6.71 TWh (2024)
    — and concentrated in the North zone (ME/NH/VT, ~81% of annual energy).
    EIA-923 ``HY`` and EIA-930 ``WAT`` agree within 15% for both years
    (2023: 8.55 vs 8.77 TWh; 2024: 6.71 vs 7.42 TWh — small QF/non-
    dispatchable plants create minor timing differences between the two
    surveys but both land in the same ballpark).

    2025 is survey-only in the early-release EIA-923 (5 reporters vs
    ~166 full-year plants); backfilling non-reporters from 2024 recovers
    the fleet to near the 2024 level.
    """

    # EIA-923 anchors (TWh) via load_hydro_budget — regression guards on
    # the ISNE BA filter, monthly-column aggregation, and negative-gen clip.
    EIA923_TWH = {2023: 8.548, 2024: 6.714}
    # EIA-930 ISNE WAT (conventional hydro, excluding PS fuel-type ``PS``).
    # Source: data/raw/ISNE_fueltype.parquet, column fueltype=="WAT".
    EIA930_WAT_TWH = {2023: 8.774, 2024: 7.424}

    def test_shapes_for_both_backcast_years(self):
        for year in self.EIA923_TWH:
            hb = load_hydro_budget("NEISO", year)
            self.assertGreater(hb.n_hydro, 0)
            self.assertEqual(hb.monthly_energy.shape, (hb.n_hydro, 12))
            self.assertEqual(hb.min_mw.shape, (hb.n_hydro,))
            self.assertEqual(hb.max_mw.shape, (hb.n_hydro,))
            self.assertEqual(len(hb.plant_names), hb.n_hydro)
            self.assertTrue(np.all(np.diff(hb.plant_ids) > 0))
            self.assertTrue(np.all(hb.monthly_energy >= 0.0))
            self.assertTrue(np.all(hb.max_mw > 0.0))

    def test_totals_match_eia923_anchors(self):
        for year, expected in self.EIA923_TWH.items():
            hb = load_hydro_budget("NEISO", year)
            total = hb.monthly_energy.sum() / 1e6
            self.assertAlmostEqual(
                total, expected, delta=0.01 * expected, msg=f"NEISO {year} TWh"
            )

    def test_totals_within_15pct_of_eia930_wat(self):
        # EIA-923 HY vs EIA-930 WAT sanity cross-check. 2023 is within 3%;
        # 2024 is ~10% (EIA-930 captures some December generation in early
        # January, so annual boundaries differ slightly). A 15% tolerance
        # guards against gross BA-filter bugs without demanding survey parity.
        for year, ref in self.EIA930_WAT_TWH.items():
            hb = load_hydro_budget("NEISO", year)
            total = hb.monthly_energy.sum() / 1e6
            self.assertLess(
                abs(total - ref) / ref,
                0.15,
                msg=f"NEISO {year} EIA-923 {total:.3f} TWh vs EIA-930 {ref:.3f} TWh",
            )

    def test_north_zone_carries_majority_of_energy(self):
        # ME/NH/VT run-of-river plants dominate NEISO hydro; North zone
        # should carry >70% of annual energy in both years (actual: ~81%).
        for year in self.EIA923_TWH:
            hb = load_hydro_budget("NEISO", year)
            zones = np.array(hb.zones)
            north_e = hb.monthly_energy[zones == "North"].sum()
            total_e = hb.monthly_energy.sum()
            self.assertGreater(
                north_e / total_e,
                0.70,
                msg=f"NEISO {year} North zone fraction",
            )

    def test_zones_are_valid_neiso_topology(self):
        hb = load_hydro_budget("NEISO", 2023)
        valid = {"North", "Central", "Boston", "Connecticut", ""}
        self.assertTrue(
            set(hb.zones) <= valid,
            msg=f"Unexpected zones: {set(hb.zones) - valid}",
        )

    def test_nameplate_from_eia860(self):
        # EIA-860 ISNE HY nameplate is ~1,900 MW; the loader falls back to
        # peak-average power for any plant absent from EIA-860, so the sum
        # will land somewhat above the strict nameplate total.
        hb = load_hydro_budget("NEISO", 2023)
        self.assertGreater(hb.max_mw.sum(), 1500.0)
        self.assertLess(hb.max_mw.sum(), 2500.0)

    def test_2025_backfill_recovers_survey_only_coverage(self):
        # 2025 early-release EIA-923: only monthly-survey reporters (~5).
        # Backfilling non-reporters from 2024 recovers the fleet to the
        # 2024 level (~166 plants) and the TWh to within 5% of 2024.
        bare = load_hydro_budget("NEISO", 2025)
        self.assertLess(bare.n_hydro, 20, msg="2025 bare should be survey-only subset")
        filled = load_hydro_budget("NEISO", 2025, backfill_year=2024)
        self.assertGreater(
            filled.n_hydro, 100, msg="backfill should recover near-full fleet"
        )
        total_twh = filled.monthly_energy.sum() / 1e6
        ref_twh = self.EIA923_TWH[2024]
        self.assertLess(
            abs(total_twh - ref_twh) / ref_twh,
            0.05,
            msg=f"2025 backfilled {total_twh:.3f} TWh vs 2024 {ref_twh:.3f} TWh",
        )
        self.assertGreater(filled.monthly_energy.sum(), bare.monthly_energy.sum())

    def test_2025_eia930_monthly_pin(self):
        # Pinning the backfilled 2025 budget to the measured EIA-930 NG: WAT
        # monthly total corrects the flat-2024 over-statement (6.70 -> 5.12
        # TWh) while leaving the MW envelope and per-plant within-month shares
        # intact.
        target = measured_monthly_hydro("NEISO", 2025)
        self.assertIsNotNone(target)
        self.assertEqual(target.shape, (12,))
        backfilled = load_hydro_budget("NEISO", 2025, backfill_year=2024)
        pinned = load_hydro_budget(
            "NEISO", 2025, backfill_year=2024, monthly_target_mwh=target
        )
        # Monthly totals now equal the measured series, and annual ~5.12 TWh.
        np.testing.assert_allclose(pinned.monthly_energy.sum(axis=0), target)
        self.assertAlmostEqual(pinned.monthly_energy.sum() / 1e6, 5.12, delta=0.1)
        self.assertLess(pinned.monthly_energy.sum(), backfilled.monthly_energy.sum())
        # Power caps untouched; same plant set.
        np.testing.assert_allclose(pinned.max_mw, backfilled.max_mw)
        self.assertEqual(pinned.n_hydro, backfilled.n_hydro)
        # Within-month per-plant shares preserved (January).
        jan_b = backfilled.monthly_energy[:, 0]
        jan_p = pinned.monthly_energy[:, 0]
        np.testing.assert_allclose(jan_p / jan_p.sum(), jan_b / jan_b.sum())

    def test_eia930_monthly_pin_wrong_length_raises(self):
        with self.assertRaises(ValueError):
            load_hydro_budget(
                "NEISO", 2025, backfill_year=2024, monthly_target_mwh=np.ones(11)
            )

    def test_measured_monthly_hydro_unknown_iso_is_none(self):
        self.assertIsNone(measured_monthly_hydro("NOT_AN_ISO", 2024))


class TestForecastHydroBudget(unittest.TestCase):
    """Forecast hydro budget: normal-water-year climatology + wet/dry lever.

    The forward analogue of the measured EIA-930 backcast level (G9). The
    climatology is the per-month mean of measured EIA-930 NG:WAT across the
    constants window; the wet/dry lever scales the level only.
    """

    def test_climatology_is_mean_of_measured_years(self):
        from market_sim.data.eia_loader import climatological_monthly_hydro

        years = (2023, 2024, 2025)
        clim = climatological_monthly_hydro("CAISO", years)
        self.assertEqual(clim.shape, (12,))
        manual = np.vstack([measured_monthly_hydro("CAISO", y) for y in years]).mean(
            axis=0
        )
        np.testing.assert_allclose(clim, manual)
        # CAISO 2023/24/25 ~24.40/22.68/21.32 TWh -> mean ~22.8 TWh.
        self.assertAlmostEqual(clim.sum() / 1e6, 22.8, delta=0.1)

    def test_climatology_skips_uncovered_years(self):
        # PJM has no 2022 hourly extract, so a window spanning it still
        # returns a climatology from the years present (no crash, no NaN).
        # 2021 was backfilled into the PJM extract by commit a2cb5c2 (EIA-930
        # BALANCE backfill), which shifted the covered-year set and this total.
        from market_sim.data.eia_loader import climatological_monthly_hydro

        clim = climatological_monthly_hydro("PJM", (2021, 2022, 2023, 2024, 2025))
        self.assertIsNotNone(clim)
        self.assertTrue(np.all(np.isfinite(clim)))
        self.assertAlmostEqual(clim.sum() / 1e6, 15.87, delta=0.2)

    def test_climatology_unknown_iso_is_none(self):
        from market_sim.data.eia_loader import climatological_monthly_hydro

        self.assertIsNone(climatological_monthly_hydro("NOT_AN_ISO"))

    def test_hydro_year_multiplier_scales_level_only(self):
        from market_sim.data.eia_loader import climatological_monthly_hydro
        from market_sim.data.hydro import forecast_monthly_hydro

        clim = climatological_monthly_hydro("CAISO")
        normal = forecast_monthly_hydro("CAISO", "normal")
        wet = forecast_monthly_hydro("CAISO", "wet")
        dry = forecast_monthly_hydro("CAISO", "dry")
        np.testing.assert_allclose(normal, clim)
        np.testing.assert_allclose(wet, clim * 1.15)
        np.testing.assert_allclose(dry, clim * 0.85)
        # The lever is a pure level scale — the monthly shape is unchanged.
        np.testing.assert_allclose(wet / wet.sum(), normal / normal.sum())

    def test_resolve_hydro_year_multiplier(self):
        from market_sim.data.hydro import resolve_hydro_year_multiplier

        self.assertEqual(resolve_hydro_year_multiplier("normal"), 1.0)
        self.assertEqual(resolve_hydro_year_multiplier("wet"), 1.15)
        self.assertEqual(resolve_hydro_year_multiplier("dry"), 0.85)
        with self.assertRaises(ValueError):
            resolve_hydro_year_multiplier("soggy")

    def test_forecast_monthly_hydro_unknown_iso_is_none(self):
        from market_sim.data.hydro import forecast_monthly_hydro

        self.assertIsNone(forecast_monthly_hydro("NOT_AN_ISO"))

    def test_forecast_budget_repins_load_hydro_budget(self):
        # End-to-end: forecast climatology pins the assembled budget level while
        # leaving the MW envelope and per-plant within-month shares intact —
        # the same seam the measured backcast pin uses.
        from market_sim.data.hydro import forecast_monthly_hydro

        target = forecast_monthly_hydro("CAISO", "wet")
        bare = load_hydro_budget("CAISO", 2024)
        pinned = load_hydro_budget("CAISO", 2024, monthly_target_mwh=target)
        np.testing.assert_allclose(pinned.monthly_energy.sum(axis=0), target)
        np.testing.assert_allclose(pinned.max_mw, bare.max_mw)
        self.assertEqual(pinned.n_hydro, bare.n_hydro)
        jan_b = bare.monthly_energy[:, 0]
        jan_p = pinned.monthly_energy[:, 0]
        np.testing.assert_allclose(jan_p / jan_p.sum(), jan_b / jan_b.sum())

    def test_scenario_config_hydro_year_validation(self):
        from market_sim.config.scenarios import ScenarioConfig

        self.assertEqual(ScenarioConfig().hydro_year, "normal")
        self.assertEqual(ScenarioConfig(hydro_year="dry").hydro_year, "dry")
        with self.assertRaises(ValueError):
            ScenarioConfig(hydro_year="soggy")

    def test_build_hydro_fleet_forecast_wiring(self):
        # The shared build_hydro_fleet forecast path scales the assembled
        # budget by the wet/dry lever and is mutually exclusive with the
        # measured backcast pin. (Used by both the calibration harness and the
        # forecast runner.)
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.data.hydro import build_hydro_fleet

        zones = get_iso_config("CAISO").zone_names
        _, normal = build_hydro_fleet(
            "CAISO", 2024, zones, forecast_budget=True, hydro_year="normal"
        )
        _, wet = build_hydro_fleet(
            "CAISO", 2024, zones, forecast_budget=True, hydro_year="wet"
        )
        self.assertAlmostEqual(wet.sum() / normal.sum(), 1.15, places=3)
        with self.assertRaises(ValueError):
            build_hydro_fleet(
                "CAISO", 2024, zones, eia930_monthly=True, forecast_budget=True
            )

    def test_build_hydro_fleet_forecast_shape_year_clamped(self):
        # Forecast years past (or inside the early-release tail of) the
        # EIA-923 data horizon clamp the budget SHAPE year to the newest
        # final-census vintage instead of silently emptying the fleet
        # (nyiso-forecast-2035 finding 1). The clamped fleet is unit-for-unit
        # identical to the final-vintage fleet: same plants, same budgets
        # (the level is the climatology either way).
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.data.eia923 import EIA923_LATEST_FINAL_VINTAGE
        from market_sim.data.hydro import build_hydro_fleet

        zones = get_iso_config("PJM").zone_names
        base_units, base_energy = build_hydro_fleet(
            "PJM", EIA923_LATEST_FINAL_VINTAGE, zones, forecast_budget=True
        )
        self.assertGreater(len(base_units), 50)  # complete census, not partial
        for fyear in (EIA923_LATEST_FINAL_VINTAGE + 1, 2030):
            units, energy = build_hydro_fleet("PJM", fyear, zones, forecast_budget=True)
            self.assertEqual(
                [u.unit_id for u in units], [u.unit_id for u in base_units]
            )
            np.testing.assert_allclose(energy, base_energy)

    def test_build_hydro_fleet_backcast_paths_not_clamped(self):
        # The clamp is forecast-branch-only: a bare (no-flag) load of a year
        # with no EIA-923 rows still yields an empty fleet, exactly as before.
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.data.hydro import build_hydro_fleet

        zones = get_iso_config("PJM").zone_names
        units, energy = build_hydro_fleet("PJM", 2030, zones)
        self.assertEqual(units, [])
        self.assertIsNone(energy)


class TestPumpedStorageFoldedLevelGuard(unittest.TestCase):
    """A BA that folds pumped storage into ``NG: WAT`` never pins its level to it.

    miso-108/109: MISO files no ``NG: PS`` column, so its ``NG: WAT`` carries
    pumped-storage gross discharge on top of conventional hydro — while the LP
    units are EIA-923 prime mover ``HY`` alone. Pinning the units' monthly
    energy to that series applies one population's energy to another's units
    (rule 14 ``[R-ACCURATE]``), so the pin is refused for the listed ISOs and
    the level stays on EIA-923 ``HY``.
    """

    def _zones(self, iso):
        from market_sim.config.iso_configs import get_iso_config

        return [z.name for z in get_iso_config(iso).zones]

    def test_miso_and_pjm_are_listed_and_neiso_is_not(self):
        from market_sim.config.constants import EIA930_PS_FOLDED_INTO_WAT

        self.assertIn("MISO", EIA930_PS_FOLDED_INTO_WAT)
        # PJM listed at pjm-143: the largest fold of the six ISOs (+72.1 % /
        # +78.5 % vs 923 HY in 2023/2024, a 5,046 MW PS fleet beside a
        # 3,334 MW conventional nameplate the pinned series breaches
        # 1,437-1,572 h/yr).
        self.assertIn("PJM", EIA930_PS_FOLDED_INTO_WAT)
        # NEISO files NG: PS from Nov 2024 (a time split, not a standing fold)
        # and NYISO shows no fold signature at all — neither is switched here.
        self.assertNotIn("NEISO", EIA930_PS_FOLDED_INTO_WAT)
        self.assertNotIn("NYISO", EIA930_PS_FOLDED_INTO_WAT)

    def test_split_registry_is_neiso_only_and_disjoint_from_the_flat_one(self):
        # neiso-72: the TIME-SPLIT companion registry. NEISO's first wholly-
        # split calendar year is 2025 (first filed NG: PS hour 2024-11-07;
        # the seam year counts as folded — one source basis per year).
        from market_sim.config.constants import (
            EIA930_PS_FOLDED_INTO_WAT,
            EIA930_PS_SPLIT_COMPLETE_FROM,
        )

        self.assertEqual(EIA930_PS_SPLIT_COMPLETE_FROM, {"NEISO": 2025})
        for iso in EIA930_PS_SPLIT_COMPLETE_FROM:
            self.assertNotIn(iso, EIA930_PS_FOLDED_INTO_WAT)

    def test_folded_predicate_is_per_year_for_neiso_and_flat_elsewhere(self):
        from market_sim.data.hydro import eia930_wat_level_folded

        for year in (2019, 2023, 2024):  # pre-split + the seam year
            self.assertTrue(eia930_wat_level_folded("NEISO", year))
        for year in (2025, 2026):  # wholly-split years keep the pin
            self.assertFalse(eia930_wat_level_folded("NEISO", year))
        # Flat-registry BAs are folded in EVERY year; clean ISOs in none.
        self.assertTrue(eia930_wat_level_folded("MISO", 2025))
        self.assertTrue(eia930_wat_level_folded("PJM", 2030))
        self.assertFalse(eia930_wat_level_folded("NYISO", 2019))
        self.assertFalse(eia930_wat_level_folded("ERCOT", 2023))

    def test_neiso_presplit_years_refuse_the_pin(self):
        # Design D (neiso-72): 2023/2024 predate the first wholly-split year,
        # so asking for the pin yields the un-pinned EIA-923 HY budget — the
        # units' own complete-census filings (173/169 plants) — which sits
        # BELOW the PS-folded measured series.
        from market_sim.data.hydro import build_hydro_fleet

        zones = self._zones("NEISO")
        # Expected totals are the BUILDER's (923 HY census + the backfill_year
        # population construction every run already uses: 8.5762 = the raw
        # 8.5469 census + 0.029 TWh of plants carried at their 2024 filing),
        # NOT the raw-census probe numbers — the pin is the only thing removed.
        for year, expected_twh in ((2023, 8.576), (2024, 6.714)):
            pinned_request, monthly = build_hydro_fleet(
                "NEISO", year, zones, backfill_year=2024, eia930_monthly=True
            )
            bare_units, bare = build_hydro_fleet(
                "NEISO", year, zones, backfill_year=2024, eia930_monthly=False
            )
            np.testing.assert_array_equal(monthly, bare)
            self.assertEqual(len(pinned_request), len(bare_units))
            self.assertAlmostEqual(monthly.sum() / 1e6, expected_twh, delta=0.01)
            wat = measured_monthly_hydro("NEISO", year)
            self.assertIsNotNone(wat)
            self.assertLess(monthly.sum(), wat.sum())
        # 2025 — the first wholly-split year — KEEPS the pin: covered by
        # test_unlisted_iso_still_pins_to_the_measured_series below.

    def test_miso_level_is_the_923_hy_budget_not_the_930_pin(self):
        from market_sim.data.hydro import build_hydro_fleet

        zones = self._zones("MISO")
        for year, expected_twh in ((2023, 8.789), (2024, 9.042)):
            pinned_request, monthly = build_hydro_fleet(
                "MISO", year, zones, backfill_year=2024, eia930_monthly=True
            )
            bare_units, bare = build_hydro_fleet(
                "MISO", year, zones, backfill_year=2024, eia930_monthly=False
            )
            # Asking for the pin yields the un-pinned (EIA-923 HY) budget...
            np.testing.assert_array_equal(monthly, bare)
            self.assertEqual(len(pinned_request), len(bare_units))
            self.assertAlmostEqual(monthly.sum() / 1e6, expected_twh, delta=0.01)
            # ...which is materially BELOW the PS-inclusive measured series.
            wat = measured_monthly_hydro("MISO", year)
            self.assertIsNotNone(wat)
            self.assertLess(monthly.sum(), 0.90 * wat.sum())

    def test_nameplate_aware_is_inert_for_a_listed_iso(self):
        # With no level target there is nothing to re-allocate, so
        # hydro_budget_nameplate_aware cannot move a listed ISO's budget.
        # PJM matters here: its keeper ARMS the mechanism (pjm-133), and under
        # the pinned level it moved 1,703/1,147/2,085 GWh of plant-months a
        # year — all of it the PS contamination being shuffled off plant-months
        # pushed above their own nameplate ceilings (pjm-143, mirroring
        # miso-109 §6).
        from market_sim.data.hydro import build_hydro_fleet

        for iso in ("MISO", "PJM"):
            zones = self._zones(iso)
            for year in (2023, 2024, 2025):
                _ua, off = build_hydro_fleet(
                    iso,
                    year,
                    zones,
                    backfill_year=2024,
                    eia930_monthly=True,
                    nameplate_aware_target=False,
                )
                _ub, on = build_hydro_fleet(
                    iso,
                    year,
                    zones,
                    backfill_year=2024,
                    eia930_monthly=True,
                    nameplate_aware_target=True,
                )
                np.testing.assert_array_equal(off, on)

    def test_pjm_level_is_the_923_hy_budget_not_the_930_pin(self):
        # pjm-143: the largest PS fold of the six ISOs. Asking for the pin
        # yields the un-pinned (EIA-923 HY) budget, which sits at 58 % of the
        # PS-inclusive measured series (+72.1 % / +78.5 % gaps).
        from market_sim.data.hydro import build_hydro_fleet

        zones = self._zones("PJM")
        for year, expected_twh in ((2023, 8.977), (2024, 8.864)):
            pinned_request, monthly = build_hydro_fleet(
                "PJM", year, zones, backfill_year=2024, eia930_monthly=True
            )
            bare_units, bare = build_hydro_fleet(
                "PJM", year, zones, backfill_year=2024, eia930_monthly=False
            )
            np.testing.assert_array_equal(monthly, bare)
            self.assertEqual(len(pinned_request), len(bare_units))
            self.assertAlmostEqual(monthly.sum() / 1e6, expected_twh, delta=0.01)
            wat = measured_monthly_hydro("PJM", year)
            self.assertIsNotNone(wat)
            # The fold is ~+72-79 %, so the corrected level is far BELOW the
            # PS-inclusive series — a much wider margin than MISO's 0.90.
            self.assertLess(monthly.sum(), 0.65 * wat.sum())

    def test_unlisted_iso_still_pins_to_the_measured_series(self):
        from market_sim.data.hydro import build_hydro_fleet

        target = measured_monthly_hydro("NEISO", 2025)
        self.assertIsNotNone(target)
        _units, monthly = build_hydro_fleet(
            "NEISO", 2025, self._zones("NEISO"), backfill_year=2024, eia930_monthly=True
        )
        self.assertAlmostEqual(monthly.sum() / 1e6, target.sum() / 1e6, delta=0.02)


class TestPumpedStorageFoldedForecastLevel(unittest.TestCase):
    """The FORWARD half of the fold fix: a listed BA's forecast level is EIA-923.

    miso-109 corrected the backcast level for the BAs in
    ``EIA930_PS_FOLDED_INTO_WAT`` but deliberately left the forward analogue —
    ``forecast_monthly_hydro`` -> ``climatological_monthly_hydro``, the
    multi-year mean of the SAME PS-inclusive ``NG: WAT`` series — merely
    warned about. miso-110 replaces it with the coverage-gated EIA-923 ``HY``
    climatology, the same population as the LP units. Verification is entirely
    no-LP: the level is a 12-vector.
    """

    ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "NWPP", "SOCO")

    def _zones(self, iso):
        from market_sim.config.iso_configs import get_iso_config

        return [z.name for z in get_iso_config(iso).zones]

    def test_realised_window_gates_out_the_early_release(self):
        # The 2025 EIA-923 filing carries 14 MISO `HY` plants against ~163 in
        # 2021-2024; averaging it in would measure source COVERAGE, not
        # hydrology (miso-109's "2025 trap"). The gate can only ever remove a
        # year, so the realised window is a subset of the requested one.
        from market_sim.config.constants import HYDRO_CLIMATOLOGY_YEARS
        from market_sim.data.hydro import complete_923_hydro_years

        window = complete_923_hydro_years("MISO")
        self.assertEqual(window, (2021, 2022, 2023, 2024))
        self.assertNotIn(2025, window)
        self.assertTrue(set(window).issubset(set(HYDRO_CLIMATOLOGY_YEARS)))

    def test_miso_forecast_level_is_exactly_the_gated_923_mean(self):
        # Equality, not a tolerance: the forecast level IS the mean of the
        # gated years' EIA-923 `HY` totals, with no reconciliation factor
        # anywhere between the two series (miso-109 §2 — none is identifiable).
        from market_sim.data.eia923 import (
            load_monthly_generation,
            monthly_netgen_columns,
        )
        from market_sim.data.hydro import (
            _load_hydro_generation,
            climatological_monthly_hydro_923,
            complete_923_hydro_years,
            forecast_monthly_hydro,
        )

        gen = load_monthly_generation()
        mcols = monthly_netgen_columns()
        expected = np.vstack(
            [
                _load_hydro_generation("MISO", y, gen=gen)[mcols]
                .to_numpy(dtype=float)
                .sum(axis=0)
                for y in complete_923_hydro_years("MISO")
            ]
        ).mean(axis=0)

        np.testing.assert_array_equal(
            climatological_monthly_hydro_923("MISO"), expected
        )
        np.testing.assert_array_equal(
            forecast_monthly_hydro("MISO", "normal"), expected
        )
        self.assertEqual(expected.shape, (12,))
        self.assertAlmostEqual(expected.sum() / 1e6, 9.3116, delta=0.001)

    def test_miso_forecast_level_is_below_the_ps_inclusive_climatology(self):
        # The defect being removed. NOTE the WINDOW: the two sources realise
        # DIFFERENT year sets (923 -> 2021-2024, 930 -> 2021+2023-2025, because
        # the wide MISO hourly extract carries 7 rows for 2022), so this delta
        # mixes the PS fold with a window mismatch and is NOT quotable as the
        # fold. The defensible fold numbers are the coverage-gated per-year
        # backcast ones, +13.5 % (2023) and +18.5 % (2024) — asserted below.
        from market_sim.data.eia_loader import climatological_monthly_hydro
        from market_sim.data.hydro import _load_hydro_generation, forecast_monthly_hydro
        from market_sim.data.eia923 import monthly_netgen_columns

        level = forecast_monthly_hydro("MISO", "normal")
        self.assertLess(level.sum(), climatological_monthly_hydro("MISO").sum())

        mcols = monthly_netgen_columns()
        for year, expected_pct in ((2023, 13.5), (2024, 18.5)):
            hy = _load_hydro_generation("MISO", year)[mcols].to_numpy(dtype=float).sum()
            wat = measured_monthly_hydro("MISO", year).sum()
            self.assertAlmostEqual((wat / hy - 1) * 100, expected_pct, delta=0.5)

    def test_neiso_forecast_level_is_the_923_climatology_while_window_folded(self):
        # neiso-72, the time-split forecast half: 2021-2024 of the climatology
        # window predate NEISO's first wholly-split year, so averaging the 930
        # series would fold pumped storage into the forward level; the whole
        # climatology stays on the 923 basis instead. The guard un-arms
        # itself once the window holds only wholly-split years — asserted on
        # the predicate, since no such 930 window exists on disk yet.
        from market_sim.config.constants import HYDRO_CLIMATOLOGY_YEARS
        from market_sim.data.hydro import (
            climatological_monthly_hydro_923,
            eia930_wat_level_folded,
            forecast_monthly_hydro,
        )

        self.assertTrue(
            any(eia930_wat_level_folded("NEISO", y) for y in HYDRO_CLIMATOLOGY_YEARS)
        )
        np.testing.assert_array_equal(
            forecast_monthly_hydro("NEISO", "normal"),
            climatological_monthly_hydro_923("NEISO"),
        )
        self.assertFalse(
            any(eia930_wat_level_folded("NEISO", y) for y in (2025, 2026, 2027))
        )

    def test_every_non_registry_iso_is_byte_unchanged(self):
        # Asserted, not assumed: the registry is the ONLY thing that switches
        # source, so a non-listed ISO's forecast level must still be exactly
        # its EIA-930 climatology times the wet/dry lever (rule 25 — a verdict
        # never crosses an ISO boundary).
        from market_sim.config.constants import EIA930_PS_FOLDED_INTO_WAT
        from market_sim.data.eia_loader import climatological_monthly_hydro
        from market_sim.data.hydro import (
            forecast_monthly_hydro,
            resolve_hydro_year_multiplier,
        )

        from market_sim.config.constants import EIA930_PS_SPLIT_COMPLETE_FROM

        unlisted = [
            i
            for i in self.ISOS
            if i not in EIA930_PS_FOLDED_INTO_WAT
            and i not in EIA930_PS_SPLIT_COMPLETE_FROM
        ]
        # MISO + PJM are flat-listed; NEISO is split-listed (neiso-72). SPP
        # (registered 2026-09-06, SPP-20) is unlisted: its EIA-930 extract's
        # NG: BAT column is 100 % null through 2025 (spp-data-audit §3.3), so
        # no PS fold has been measured for it and it takes the default path.
        # NWPP (registered 2026-09-14, NWPP-20) is unlisted too: pumped
        # storage is UNOBSERVABLE in EIA-930 for the footprint in every year
        # (nwpp-data-audit §4.5; EIA-860 carries 314.0 MW, one BPAT plant), so
        # no fold has been measured and it takes the default path.
        # SOCO (registered 2026-09-14, SOCO-20) is unlisted for the OPPOSITE
        # measured reason: its NG: WAT never goes negative before the 2024-07-15
        # taxonomy cut-over (min +32 MW over 13,470 h), so pumped-storage
        # charging was never folded into hydro — it was not reported at all
        # (soco-data-audit §3.3). No fold exists to correct.
        self.assertEqual(len(unlisted), 6)
        for iso in unlisted:
            base = climatological_monthly_hydro(iso)
            self.assertIsNotNone(base, f"{iso} has no EIA-930 climatology")
            for hydro_year in ("dry", "normal", "wet"):
                np.testing.assert_array_equal(
                    forecast_monthly_hydro(iso, hydro_year),
                    base * resolve_hydro_year_multiplier(hydro_year),
                    err_msg=f"{iso}/{hydro_year} forecast level moved",
                )

    def test_pjm_forecast_level_is_exactly_the_gated_923_mean(self):
        # pjm-143, the forward half armed by the same registry line: PJM's
        # forecast level moves 15.875 -> 9.254 TWh (the coverage-gated EIA-923
        # HY climatology over the realised window 2021-2024; the 930 side's
        # +71.5 % naive / +72.5 % window-matched delta was the fold).
        from market_sim.data.eia923 import (
            load_monthly_generation,
            monthly_netgen_columns,
        )
        from market_sim.data.hydro import (
            _load_hydro_generation,
            climatological_monthly_hydro_923,
            complete_923_hydro_years,
            forecast_monthly_hydro,
        )

        window = complete_923_hydro_years("PJM")
        self.assertEqual(window, (2021, 2022, 2023, 2024))
        gen = load_monthly_generation()
        mcols = monthly_netgen_columns()
        expected = np.vstack(
            [
                _load_hydro_generation("PJM", y, gen=gen)[mcols]
                .to_numpy(dtype=float)
                .sum(axis=0)
                for y in window
            ]
        ).mean(axis=0)

        np.testing.assert_array_equal(climatological_monthly_hydro_923("PJM"), expected)
        np.testing.assert_array_equal(forecast_monthly_hydro("PJM", "normal"), expected)
        self.assertAlmostEqual(expected.sum() / 1e6, 9.2541, delta=0.001)

    def test_wet_dry_lever_still_multiplies_cleanly(self):
        from market_sim.data.hydro import (
            forecast_monthly_hydro,
            resolve_hydro_year_multiplier,
        )

        base = forecast_monthly_hydro("MISO", "normal")
        for hydro_year in ("dry", "normal", "wet"):
            np.testing.assert_array_equal(
                forecast_monthly_hydro("MISO", hydro_year),
                base * resolve_hydro_year_multiplier(hydro_year),
            )
        self.assertLess(forecast_monthly_hydro("MISO", "dry").sum(), base.sum())
        self.assertGreater(forecast_monthly_hydro("MISO", "wet").sum(), base.sum())

    def test_no_complete_filing_falls_back_and_warns(self):
        # Design decision 2: the documented fallback. With every candidate year
        # gated out there is no climatology, so `forecast_monthly_hydro`
        # returns None and `build_hydro_fleet` leaves the budget at the
        # (clamped) shape year's own EIA-923 level — still the right
        # population, but a single water year, with the wet/dry lever inert.
        from market_sim.data.hydro import (
            climatological_monthly_hydro_923,
            complete_923_hydro_years,
            forecast_monthly_hydro,
        )

        self.assertEqual(complete_923_hydro_years("MISO", (2025,)), ())
        with self.assertLogs("market_sim.data.hydro", level="WARNING"):
            self.assertIsNone(climatological_monthly_hydro_923("MISO", (2025,)))
        with self.assertLogs("market_sim.data.hydro", level="WARNING"):
            self.assertIsNone(forecast_monthly_hydro("MISO", "normal", (2025,)))

    def test_forecast_fleet_past_the_vintage_horizon_keeps_a_full_census(self):
        # REGRESSION GUARD. The `shape_year = min(year, EIA923_LATEST_FINAL_
        # VINTAGE)` clamp exists because an unclamped forecast year silently
        # EMPTIED the hydro fleet (nyiso-forecast-2035-2026-07-13.md finding 1).
        # Re-asserted on the new source path at both a near and a far year.
        from market_sim.data.hydro import build_hydro_fleet, forecast_monthly_hydro

        expected = forecast_monthly_hydro("MISO", "normal")
        for year in (2026, 2035):
            units, monthly = build_hydro_fleet(
                "MISO",
                year,
                self._zones("MISO"),
                backfill_year=2024,
                forecast_budget=True,
            )
            self.assertEqual(len(units), 160, f"MISO {year} hydro census collapsed")
            self.assertIsNotNone(monthly)
            self.assertAlmostEqual(
                monthly.sum() / 1e6, expected.sum() / 1e6, delta=0.001
            )

    def test_forecast_and_backcast_levels_are_the_same_population(self):
        # The point of the whole fix: the forward level and the corrected
        # backcast level are now both EIA-923 `HY`, so a forecast year's level
        # sits in the same range as the backcast years' rather than ~10 % above
        # them the way the PS-inclusive climatology did.
        from market_sim.data.hydro import build_hydro_fleet, forecast_monthly_hydro

        zones = self._zones("MISO")
        backcast = [
            build_hydro_fleet(
                "MISO", y, zones, backfill_year=2024, eia930_monthly=True
            )[1].sum()
            for y in (2023, 2024)
        ]
        level = forecast_monthly_hydro("MISO", "normal").sum()
        self.assertGreater(level, min(backcast))
        self.assertLess(level, max(backcast) * 1.05)


class TestOtherISOBudgetsUnchanged(unittest.TestCase):
    """PJM / ERCOT / CAISO hydro budgets are untouched by the NYISO/NEISO P4 stage."""

    def test_pjm_2023_budget_regression(self):
        hb = load_hydro_budget("PJM", 2023)
        self.assertEqual(hb.n_hydro, 72)
        self.assertAlmostEqual(hb.monthly_energy.sum() / 1e6, 8.976, delta=0.05)
        self.assertAlmostEqual(hb.max_mw.sum(), 3288.0, delta=20.0)

    def test_ercot_2023_budget_regression(self):
        hb = load_hydro_budget("ERCOT", 2023)
        self.assertEqual(hb.n_hydro, 14)
        self.assertAlmostEqual(hb.monthly_energy.sum() / 1e6, 0.350, delta=0.005)

    def test_caiso_2023_budget_regression(self):
        hb = load_hydro_budget("CAISO", 2023)
        self.assertAlmostEqual(hb.monthly_energy.sum() / 1e6, 23.90, delta=0.01 * 23.90)

    def test_per_plant_min_flow_none_is_identical_to_existing(self):
        # Passing per_plant_min_flow=None must reproduce the exact same
        # budget as not passing the argument at all — no regression to PJM.
        base = load_hydro_budget("PJM", 2023)
        explicit_none = load_hydro_budget("PJM", 2023, per_plant_min_flow=None)
        import numpy as np

        np.testing.assert_array_equal(base.plant_ids, explicit_none.plant_ids)
        np.testing.assert_array_equal(base.min_mw, explicit_none.min_mw)
        np.testing.assert_array_equal(base.max_mw, explicit_none.max_mw)


class TestNYISOHydroBudget(unittest.TestCase):
    """NYISO hydro energy budgets from EIA-923 (P4 hydro stage).

    Anchors: EIA-923 NYIS conventional hydro (prime mover ``HY``) monthly
    net generation sums to 28.40 TWh (2023) and 27.88 TWh (2024). Both
    years are anchored on the full annual EIA-923 release.

    EIA-930 NYIS NG:WAT crosscheck: 26.84 TWh 2023, 26.86 TWh 2024.
    EIA-930 WAT includes PS net generation (generation minus pumping);
    because the NYISO PS fleet is a net energy consumer, EIA-923 HY >
    EIA-930 WAT by approximately 1–2 TWh (the PS net pumping load).

    The NYISO hydro fleet (~4.6 GW, ~28 TWh/yr) is the largest in the
    model — larger than CAISO's ~4 GW Sierra/Cascade fleet — and is
    dominated by NYPA's Robert Moses Niagara (~2.4 GW, ~15 TWh) and
    Robert Moses Power Dam on the St-Lawrence (~0.9 GW, ~7 TWh), with
    ~1 TWh from smaller run-of-river plants in the Capital/Hudson region.
    """

    EIA923_TWH = {2023: 28.40, 2024: 27.88}
    # EIA-930 NYIS NG:WAT (hydro + PS net) annual totals.
    EIA930_WAT_TWH = {2023: 26.84, 2024: 26.86}

    def test_totals_match_eia923_anchors(self):
        for year, expected in self.EIA923_TWH.items():
            hb = load_hydro_budget("NYISO", year)
            total = hb.monthly_energy.sum() / 1e6
            self.assertAlmostEqual(total, expected, delta=0.01 * expected)

    def test_eia923_exceeds_eia930_by_ps_net_pumping(self):
        # EIA-923 HY (gross conventional hydro) > EIA-930 WAT (hydro + PS
        # net) because the NYISO PS fleet (Blenheim-Gilboa + Lewiston) is
        # a net energy consumer — it pumps more than it generates. The gap
        # is bounded by the total PS installed capacity and reasonable
        # cycling assumptions (< 3 TWh/yr net pumping for 1.22 GW of PS).
        for year, wat in self.EIA930_WAT_TWH.items():
            hb = load_hydro_budget("NYISO", year)
            hy_twh = hb.monthly_energy.sum() / 1e6
            self.assertGreater(hy_twh, wat)
            self.assertLess(hy_twh - wat, 3.0)

    def test_totals_within_10pct_of_eia930(self):
        # EIA-923 HY is within 10% of EIA-930 WAT; the EIA-930 WAT is the
        # sanity cross-check, accounting for PS net pumping.
        for year, wat in self.EIA930_WAT_TWH.items():
            hb = load_hydro_budget("NYISO", year)
            total = hb.monthly_energy.sum() / 1e6
            self.assertLess(abs(total - wat) / wat, 0.10)

    def test_spring_freshet_exceeds_fall(self):
        # NYISO hydro shows more generation in spring (March-May) than fall
        # (September-November) driven by Adirondack/Catskill snowmelt and
        # spring precipitation, primarily in the smaller run-of-river
        # plants. Niagara and St-Lawrence moderate the contrast.
        for year in (2023, 2024):
            hb = load_hydro_budget("NYISO", year)
            monthly = hb.monthly_energy.sum(axis=0)
            spring = monthly[2:5].sum()  # March, April, May
            fall = monthly[8:11].sum()  # September, October, November
            self.assertGreater(
                spring,
                fall,
                msg=f"NYISO {year}: spring {spring / 1e6:.2f} TWh should "
                f"exceed fall {fall / 1e6:.2f} TWh",
            )

    def test_nameplate_dominated_by_niagara(self):
        # Niagara (plant 2693, Robert Moses Niagara, ~2,429 MW) accounts
        # for more than 50% of total NYISO hydro nameplate capacity.
        hb = load_hydro_budget("NYISO", 2023)
        niagara_idx = np.flatnonzero(hb.plant_ids == 2693)
        self.assertEqual(len(niagara_idx), 1)
        niagara_mw = hb.max_mw[niagara_idx[0]]
        self.assertGreater(niagara_mw / hb.max_mw.sum(), 0.50)
        # Nameplate total consistent with ~4.5-4.8 GW EIA-860 fleet.
        self.assertGreater(hb.max_mw.sum(), 4_000.0)
        self.assertLess(hb.max_mw.sum(), 5_500.0)

    def test_zones_limited_to_upstate(self):
        # NYISO conventional hydro is wholly upstate: Niagara and the
        # St-Lawrence fleet are in Upstate_West; smaller run-of-river
        # plants on the Hudson and Mohawk are in Capital_Hudson. No hydro
        # appears in the downstate zones (Lower_Hudson, NYC, Long_Island).
        hb = load_hydro_budget("NYISO", 2023)
        zone_set = set(hb.zones) - {""}
        self.assertTrue(
            zone_set <= {"Upstate_West", "Capital_Hudson"},
            msg=f"Unexpected zones: {zone_set - {'Upstate_West', 'Capital_Hudson'}}",
        )
        self.assertIn("Upstate_West", zone_set)

    def test_upstate_west_dominates_by_nameplate(self):
        # Niagara + St-Lawrence + western run-of-river put Upstate_West
        # above 85% of total NYISO hydro nameplate.
        hb = load_hydro_budget("NYISO", 2023)
        zones = np.array(hb.zones)
        uw_mw = hb.max_mw[zones == "Upstate_West"].sum()
        self.assertGreater(uw_mw / hb.max_mw.sum(), 0.80)

    def test_2025_survey_only_has_few_reporters(self):
        # The 2025 EIA-923 early release carries only the monthly-survey
        # (large) reporters — NYISO 2025 has just 3 plants (Niagara, Power
        # Dam, and one more) covering ~21 TWh (the big plants run flat).
        bare = load_hydro_budget("NYISO", 2025)
        self.assertLess(bare.n_hydro, 10)
        # The survey-only plants are the largest ones so their TWh is high.
        self.assertGreater(bare.monthly_energy.sum() / 1e6, 15.0)

    def test_2025_backfill_recovers_fleet(self):
        # Backfilling 2024 non-reporters into 2025 recovers the fleet to
        # near the full 2024 annual level (within 10%) while preserving the
        # survey reporters' 2025 budgets.
        bare = load_hydro_budget("NYISO", 2025)
        filled = load_hydro_budget("NYISO", 2025, backfill_year=2024)
        self.assertGreater(filled.n_hydro, 100)
        # Total lands within 10% of 2024.
        total_2024 = load_hydro_budget("NYISO", 2024).monthly_energy.sum() / 1e6
        filled_twh = filled.monthly_energy.sum() / 1e6
        self.assertLess(abs(filled_twh - total_2024) / total_2024, 0.10)
        # Survey reporters keep their own 2025 budget (not overwritten).
        self.assertGreater(filled.monthly_energy.sum(), bare.monthly_energy.sum())

    def test_dispatch_respects_real_monthly_budgets(self):
        # End-to-end: the two large NYISO hydro plants (Niagara, Power Dam)
        # dispatched over January + February 2023 at their EIA-923 budgets.
        # Hydro is cheapest, so budget binds from above.
        hb = load_hydro_budget("NYISO", 2023)
        niagara = np.flatnonzero(hb.plant_ids == 2693)
        powerdam = np.flatnonzero(hb.plant_ids == 2694)
        top = np.concatenate([niagara, powerdam])
        pmax = hb.max_mw[top]
        budget = hb.monthly_energy[top][:, :2]
        hpm = hours_per_month()[:2]
        T = int(hpm.sum())
        month_idx = np.repeat([0, 1], hpm)

        gens = [
            Generator(
                unit_id=f"H{i}",
                name=f"H{i}",
                zone="Z",
                fuel_type="hydro",
                pmax_mw=float(pmax[i]),
                pmin_mw=0.0,
                eford=0.0,
            )
            for i in range(len(top))
        ]
        peak_demand = float(pmax.sum()) + 500.0
        gens.append(
            Generator(
                unit_id="G0",
                name="G0",
                zone="Z",
                fuel_type="gas_cc",
                pmax_mw=peak_demand + 100.0,
                pmin_mw=0.0,
                eford=0.0,
            )
        )
        fleet = generators_to_fleet_arrays(gens, ["Z"], hours=T)
        demand = np.full((1, T), peak_demand)
        mc = np.vstack([np.zeros((len(top), T)), np.full((1, T), 50.0)])
        res = solve_dispatch(
            fleet,
            demand,
            np.zeros((1, T)),
            np.zeros(1),
            np.zeros((1, T)),
            np.zeros(1),
            mc=mc,
            voll=5000.0,
            hydro_monthly_energy=budget,
            hydro_month_index=month_idx,
        )
        for g in range(len(top)):
            for m in range(2):
                dispatched = res.dispatch[g][month_idx == m].sum()
                self.assertLessEqual(dispatched, budget[g, m] * (1 + 1e-6))
                expected = min(budget[g, m], pmax[g] * hpm[m])
                self.assertAlmostEqual(
                    dispatched, expected, delta=1e-3 * max(expected, 1.0)
                )


class TestNYISOTreatyMinFlows(unittest.TestCase):
    """Treaty-mandated minimum flows for Niagara and St-Lawrence.

    The 1950 Niagara Treaty and the IJC/Plan 2014 St-Lawrence order require
    sustained minimum hydraulic flows from the NYPA plants. These floors are
    stored in :data:`market_sim.config.constants.NYISO_HYDRO_TREATY_MIN_FLOW`
    and applied via the ``per_plant_min_flow`` argument.

    Niagara plant 2693 (Robert Moses Niagara, ~2,429 MW): 25% of nameplate
    St-Lawrence plant 2694 (Robert Moses Power Dam, ~912 MW): 50% of nameplate
    """

    # EIA plant IDs: EIA-860/923 ORIS codes.
    NIAGARA_PLANT_ID = 2693
    ST_LAWRENCE_PLANT_ID = 2694

    def setUp(self):
        from market_sim.config.constants import NYISO_HYDRO_TREATY_MIN_FLOW

        self.treaty = NYISO_HYDRO_TREATY_MIN_FLOW
        self.hb_no_floor = load_hydro_budget("NYISO", 2023)
        self.hb_treaty = load_hydro_budget(
            "NYISO", 2023, per_plant_min_flow=self.treaty
        )

    def test_treaty_constant_covers_both_plants(self):
        self.assertIn(self.NIAGARA_PLANT_ID, self.treaty)
        self.assertIn(self.ST_LAWRENCE_PLANT_ID, self.treaty)

    def test_niagara_min_flow_fraction(self):
        # 25% of Niagara nameplate = ~607 MW minimum sustained output.
        self.assertAlmostEqual(self.treaty[self.NIAGARA_PLANT_ID], 0.25)

    def test_st_lawrence_min_flow_fraction(self):
        # 50% of St-Lawrence nameplate = ~456 MW minimum sustained output.
        self.assertAlmostEqual(self.treaty[self.ST_LAWRENCE_PLANT_ID], 0.50)

    def test_niagara_min_mw_applied(self):
        # With treaty floors, Niagara's min_mw is 25% of its max_mw.
        n_idx = np.flatnonzero(self.hb_treaty.plant_ids == self.NIAGARA_PLANT_ID)
        self.assertEqual(len(n_idx), 1)
        i = n_idx[0]
        expected_min = 0.25 * self.hb_treaty.max_mw[i]
        self.assertAlmostEqual(self.hb_treaty.min_mw[i], expected_min, places=3)

    def test_st_lawrence_min_mw_applied(self):
        # With treaty floors, Power Dam's min_mw is 50% of its max_mw.
        sl_idx = np.flatnonzero(self.hb_treaty.plant_ids == self.ST_LAWRENCE_PLANT_ID)
        self.assertEqual(len(sl_idx), 1)
        i = sl_idx[0]
        expected_min = 0.50 * self.hb_treaty.max_mw[i]
        self.assertAlmostEqual(self.hb_treaty.min_mw[i], expected_min, places=3)

    def test_without_treaty_floors_min_mw_is_zero(self):
        # Default (no per-plant floor, min_flow_fraction=0) has no minimum.
        n_idx = np.flatnonzero(self.hb_no_floor.plant_ids == self.NIAGARA_PLANT_ID)
        sl_idx = np.flatnonzero(self.hb_no_floor.plant_ids == self.ST_LAWRENCE_PLANT_ID)
        self.assertEqual(self.hb_no_floor.min_mw[n_idx[0]], 0.0)
        self.assertEqual(self.hb_no_floor.min_mw[sl_idx[0]], 0.0)

    def test_non_treaty_plants_use_global_floor(self):
        # Other plants (not in the treaty dict) use the global min_flow_fraction.
        hb_global = load_hydro_budget(
            "NYISO",
            2023,
            min_flow_fraction=0.10,
            per_plant_min_flow=self.treaty,
        )
        for i, pid in enumerate(hb_global.plant_ids):
            if int(pid) in self.treaty:
                continue
            self.assertAlmostEqual(
                hb_global.min_mw[i], 0.10 * hb_global.max_mw[i], places=3
            )

    def test_treaty_floor_takes_max_over_global(self):
        # A global min_flow_fraction lower than the treaty value must not
        # override the treaty floor (the max() rule applies).
        hb_low_global = load_hydro_budget(
            "NYISO",
            2023,
            min_flow_fraction=0.10,
            per_plant_min_flow=self.treaty,
        )
        n_idx = np.flatnonzero(hb_low_global.plant_ids == self.NIAGARA_PLANT_ID)
        i = n_idx[0]
        # Treaty says 0.25 > global 0.10, so treaty wins.
        self.assertAlmostEqual(
            hb_low_global.min_mw[i], 0.25 * hb_low_global.max_mw[i], places=3
        )

    def test_min_energy_floors_feasible_vs_budget(self):
        # Monthly min energy floors must never exceed the monthly budget
        # (infeasible two-sided constraint) — the clip in monthly_min_energy
        # must handle any month where the floor exceeds the inflow budget.
        hpm = hours_per_month()
        mm = self.hb_treaty.monthly_min_energy(hpm)
        self.assertTrue(
            np.all(mm <= self.hb_treaty.monthly_energy + 1e-9),
            msg="Treaty min-energy floor exceeds budget for some plant-month",
        )


class TestHydroMinFlowFloor(unittest.TestCase):
    """The measured monthly minimum-flow floor (caiso-124).

    The lower half of the two-sided measured hydro capability envelope:
    :func:`~market_sim.data.eia_loader.measured_hydro_min_flow_level` derives
    the fleet's monthly Q95 sustained level and
    :func:`~market_sim.data.hydro.allocate_min_flow_floor` splits it across
    plants pro-rata by each plant's share of that month's energy budget.
    """

    def test_percentile_is_the_ceiling_mirror(self):
        # The floor introduces NO new free parameter: its percentile is the
        # exact complement of the ceiling's (DOF ledger — 0 new DOF).
        from market_sim.config.constants import (
            HYDRO_ENVELOPE_PERCENTILE,
            HYDRO_MIN_FLOW_PERCENTILE,
        )

        self.assertAlmostEqual(
            HYDRO_MIN_FLOW_PERCENTILE, 100.0 - HYDRO_ENVELOPE_PERCENTILE
        )

    def test_measured_level_is_monthly_and_nonnegative(self):
        from market_sim.data.eia_loader import measured_hydro_min_flow_level

        lev = measured_hydro_min_flow_level("CAISO", 2023)
        self.assertIsNotNone(lev)
        self.assertEqual(lev.shape, (12,))
        self.assertTrue(np.all(lev >= 0.0))
        # A large reservoir system never runs its whole fleet dry: every month
        # carries a real sustained level, and it sits far below the fleet's
        # measured mean output (~2.8 GW) — a floor, not a shape pin.
        self.assertTrue(np.all(lev > 100.0))
        self.assertLess(lev.max(), 2800.0)

    def test_measured_level_is_shape_free(self):
        # The level is one number per month, so expanding it over the hour
        # horizon cannot carry a diurnal profile (rule 13: a floor following
        # the measured hour-of-day shape would pin the measured outcome).
        from market_sim.data.eia_loader import measured_hydro_min_flow_level
        from market_sim.data.fleet import _hour_to_month_index

        lev = measured_hydro_min_flow_level("CAISO", 2024)
        hourly = lev[_hour_to_month_index(8760)]
        by_hod = np.array([hourly[np.arange(8760) % 24 == h].mean() for h in range(24)])
        self.assertLess(by_hod.max() - by_hod.min(), 1e-9)

    def test_allocation_sums_to_the_fleet_level(self):
        from market_sim.data.hydro import allocate_min_flow_floor

        level = np.full(12, 300.0)
        energy = np.array([[200_000.0] * 12, [100_000.0] * 12, [0.0] * 12])
        hpm = hours_per_month().astype(float)
        floors = allocate_min_flow_floor(level, energy, hpm)
        np.testing.assert_allclose(floors.sum(axis=0), level)
        # Pro-rata by budget share: 2:1:0.
        np.testing.assert_allclose(floors[0], 200.0)
        np.testing.assert_allclose(floors[1], 100.0)
        np.testing.assert_allclose(floors[2], 0.0)

    def test_allocation_clips_to_monthly_feasibility(self):
        # A level above the month's average power would make the two-sided
        # budget row infeasible; the allocator clips it to that exact bound.
        from market_sim.data.hydro import allocate_min_flow_floor

        hpm = hours_per_month().astype(float)
        energy = np.array([[100.0 * h for h in hpm]])  # 100 MW average power
        floors = allocate_min_flow_floor(np.full(12, 500.0), energy, hpm)
        np.testing.assert_allclose(floors[0], 100.0)
        self.assertTrue(np.all(floors * hpm[np.newaxis, :] <= energy + 1e-6))

    def test_build_hydro_fleet_off_is_inert(self):
        from market_sim.data.hydro import build_hydro_fleet

        zones = ["NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest"]
        off_units, off_energy = build_hydro_fleet("CAISO", 2023, zones)
        on_units, on_energy = build_hydro_fleet(
            "CAISO", 2023, zones, min_flow_floor=True
        )
        # The floor never touches the energy budget or the unit set.
        np.testing.assert_array_equal(off_energy, on_energy)
        self.assertEqual(len(off_units), len(on_units))
        self.assertTrue(
            all(u.hydro_min_flow_monthly_mw is None for u in off_units),
            msg="default-off path must leave every unit unfloored",
        )
        self.assertTrue(all(u.hydro_min_flow_monthly_mw is not None for u in on_units))

    def test_build_hydro_fleet_floor_fits_every_plant_budget(self):
        from market_sim.data.hydro import build_hydro_fleet

        zones = ["NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest"]
        units, energy = build_hydro_fleet("CAISO", 2023, zones, min_flow_floor=True)
        hpm = hours_per_month().astype(float)
        floors = np.array([u.hydro_min_flow_monthly_mw for u in units], dtype=float)
        self.assertTrue(
            np.all(floors * hpm[np.newaxis, :] <= energy + 1e-6),
            msg="a plant-month floor exceeds its own budget row (infeasible LP)",
        )
        # The floor leaves the LP real room to shape the rest of the month —
        # it is commitment scaffolding, not the dispatch model.
        forced = float((floors.sum(axis=0) * hpm).sum())
        self.assertLess(forced / energy.sum(), 0.6)
        self.assertGreater(forced / energy.sum(), 0.2)
        # And it never asks a plant for more than its nameplate.
        self.assertTrue(
            all(floors[i].max() <= units[i].pmax_mw + 1e-6 for i in range(len(units)))
        )

    @staticmethod
    def _gens(monthly=None):
        """One hydro unit (50 MW, no EFORD) plus a thermal unit."""
        hydro = Generator(
            unit_id="H0",
            name="H0",
            zone="Z",
            fuel_type="hydro",
            pmax_mw=50.0,
            eford=0.0,
        )
        if monthly is not None:
            hydro.hydro_min_flow_monthly_mw = monthly
        return [
            hydro,
            Generator(
                unit_id="C0",
                name="C0",
                zone="Z",
                fuel_type="gas_cc",
                pmax_mw=50.0,
                eford=0.0,
            ),
        ]

    def test_min_gen_carries_the_floor_with_its_mechanism_id(self):
        from market_sim.data.fleet import _hour_to_month_index
        from market_sim.data.floor_mechanisms import MECH_HYDRO_MIN_FLOW

        hours = 8760
        # 40 MW in January only: month-constant within the month, zero outside,
        # and below the 50 MW pmax so the availability clip cannot mask it.
        gens = self._gens(tuple([40.0] + [0.0] * 11))
        fa = generators_to_fleet_arrays(gens, ["Z"], hours=hours)
        self.assertIsNotNone(fa.min_gen)
        jan = _hour_to_month_index(hours) == 0
        np.testing.assert_allclose(fa.min_gen[0, jan], 40.0)
        np.testing.assert_allclose(fa.min_gen[0, ~jan], 0.0)
        self.assertTrue(np.all(fa.min_gen_mechanism[0, jan] == MECH_HYDRO_MIN_FLOW))
        # Thermal units are untouched.
        np.testing.assert_allclose(fa.min_gen[1:], 0.0)

    def test_min_gen_absent_when_no_unit_is_floored(self):
        # The gate is read off the units themselves, so an unfloored fleet
        # allocates no min_gen at all (byte-identical to before the mechanism).
        fa = generators_to_fleet_arrays(self._gens(), ["Z"], hours=744)
        self.assertIsNone(fa.min_gen)

    def test_d4_window_declared_all_hours(self):
        # Rule 12/17: the mechanism must carry a declared window. Inflow and
        # licence releases are around-the-clock, so the window is all 24 hours.
        import sys

        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import legitimacy_diagnostics as ld
        from market_sim.data.floor_mechanisms import MECH_HYDRO_MIN_FLOW

        self.assertEqual(ld.D4_WINDOWS[(MECH_HYDRO_MIN_FLOW, None)], (0, 24))

    def test_ablation_registry_classifies_the_mechanism(self):
        from market_sim.data.floor_mechanisms import (
            MECH_HYDRO_MIN_FLOW,
            MECH_NAMES,
            NON_THERMAL_MECHS,
            assert_ablation_coverage,
        )

        assert_ablation_coverage()
        self.assertIn(MECH_HYDRO_MIN_FLOW, MECH_NAMES)
        # Non-thermal forcing: reported by D-2, never counted against a
        # merchant thermal class's forced-share budget.
        self.assertIn(MECH_HYDRO_MIN_FLOW, NON_THERMAL_MECHS)


class TestHydroRoRSplit(CleanDirTestCase):
    """The per-plant run-of-river split (caiso-126, config.hydro_ror_split).

    Plants the external hydro-plant-modes classifier marks non-shapeable
    dispatch flat at their own monthly water (budget[g,m]/hours[m], min ==
    availability cap == the flat level, MECH_HYDRO_ROR_FLAT); the min-flow
    floor reconciles onto the reservoir class only (rule 19 — one family,
    never stacked).
    """

    ZONES = ["NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest"]

    def setUp(self):
        # Curate the classifier from the committed raw EHA/HILARRI files into
        # the redirected (per-test) CLEAN_DIR, so build_hydro_fleet resolves
        # it without touching the real data/clean tree.
        super().setUp()
        from scripts.data.curate_hydro_plant_modes import curate

        curate(isos=["CAISO"])

    def test_split_off_is_inert(self):
        from market_sim.data.hydro import build_hydro_fleet

        off_units, off_energy = build_hydro_fleet("CAISO", 2023, self.ZONES)
        on_units, on_energy = build_hydro_fleet(
            "CAISO", 2023, self.ZONES, ror_split=True
        )
        np.testing.assert_array_equal(off_energy, on_energy)
        self.assertEqual(len(off_units), len(on_units))
        self.assertTrue(
            all(u.hydro_ror_flat_monthly_mw is None for u in off_units),
            msg="default-off path must stamp no unit",
        )
        self.assertTrue(any(u.hydro_ror_flat_monthly_mw is not None for u in on_units))

    def test_split_stamps_ror_at_its_own_flat_budget(self):
        from market_sim.data.hydro import build_hydro_fleet
        from market_sim.data.hydro_modes import load_hydro_shapeable

        units, energy = build_hydro_fleet("CAISO", 2023, self.ZONES, ror_split=True)
        modes = load_hydro_shapeable("CAISO")
        hpm = hours_per_month().astype(float)
        n_ror = 0
        for i, u in enumerate(units):
            flat = u.hydro_ror_flat_monthly_mw
            if modes.get(int(u.plant_code)) is False:
                n_ror += 1
                self.assertIsNotNone(flat)
                # The level is the plant's OWN budget spread flat, clipped
                # only by nameplate (a few small wet-year plant-months trip
                # the clip when the EIA-930-pinned budget exceeds
                # nameplate-hours — a source-data inconsistency, logged).
                np.testing.assert_allclose(
                    np.asarray(flat),
                    np.minimum(energy[i] / hpm, u.pmax_mw),
                    rtol=1e-12,
                )
                self.assertLessEqual(max(flat), u.pmax_mw + 1e-6)
            else:
                self.assertIsNone(flat)
        self.assertGreater(n_ror, 0)
        # Energy-weighted, the CAISO RoR class is a minority of the budget
        # (the caiso-126 finding: ~9-13 %, count-weighted ~40 %).
        ror_share = (
            sum(
                energy[i].sum()
                for i, u in enumerate(units)
                if u.hydro_ror_flat_monthly_mw is not None
            )
            / energy.sum()
        )
        self.assertGreater(ror_share, 0.02)
        self.assertLess(ror_share, 0.5)

    def test_reconciled_floor_never_stacks_and_preserves_the_q95_total(self):
        from market_sim.data.eia_loader import measured_hydro_min_flow_level
        from market_sim.data.hydro import build_hydro_fleet

        units, energy = build_hydro_fleet(
            "CAISO", 2023, self.ZONES, min_flow_floor=True, ror_split=True
        )
        hpm = hours_per_month().astype(float)
        level = measured_hydro_min_flow_level("CAISO", 2023)
        ror = np.array([u.hydro_ror_flat_monthly_mw is not None for u in units])
        # Rule 19: no unit carries both stamps.
        for u in units:
            self.assertFalse(
                u.hydro_ror_flat_monthly_mw is not None
                and u.hydro_min_flow_monthly_mw is not None,
                msg=f"{u.unit_id} carries both the RoR flat and the floor",
            )
        # The reservoir-class floor plus the RoR flat base reproduces the
        # frozen fleet Q95 level exactly wherever the level exceeds the base
        # (the allocator feasibility clip can only lower it further).
        ror_base = np.array(
            [u.hydro_ror_flat_monthly_mw for u in np.array(units)[ror]], dtype=float
        ).sum(axis=0)
        floors = np.array(
            [
                u.hydro_min_flow_monthly_mw
                for u in np.array(units)[~ror]
                if u.hydro_min_flow_monthly_mw is not None
            ],
            dtype=float,
        ).sum(axis=0)
        fleet_cap = energy[~ror].sum(axis=0) / hpm  # allocator clip bound
        expect = np.minimum(np.clip(level - ror_base, 0.0, None), fleet_cap)
        np.testing.assert_allclose(floors, expect, rtol=1e-9, atol=1e-6)
        # And each reservoir plant-month floor stays inside its own budget.
        for i, u in enumerate(units):
            if u.hydro_min_flow_monthly_mw is not None:
                self.assertTrue(
                    np.all(
                        np.asarray(u.hydro_min_flow_monthly_mw) * hpm
                        <= energy[i] + 1e-6
                    )
                )

    def test_min_gen_and_availability_fix_dispatch_at_the_flat_level(self):
        from market_sim.data.fleet import _hour_to_month_index
        from market_sim.data.floor_mechanisms import MECH_HYDRO_ROR_FLAT

        hours = 8760
        hydro = Generator(
            unit_id="H0",
            name="H0",
            zone="Z",
            fuel_type="hydro",
            pmax_mw=50.0,
            eford=0.0,
        )
        # 30 MW flat in January, off the rest of the year (zero budget).
        hydro.hydro_ror_flat_monthly_mw = tuple([30.0] + [0.0] * 11)
        thermal = Generator(
            unit_id="C0",
            name="C0",
            zone="Z",
            fuel_type="gas_cc",
            pmax_mw=50.0,
            eford=0.0,
        )
        fa = generators_to_fleet_arrays([hydro, thermal], ["Z"], hours=hours)
        jan = _hour_to_month_index(hours) == 0
        # min == pmax x availability == the flat level: dispatch is FIXED.
        np.testing.assert_allclose(fa.min_gen[0, jan], 30.0)
        np.testing.assert_allclose(fa.availability[0, jan] * 50.0, 30.0)
        np.testing.assert_allclose(fa.availability[0, ~jan], 0.0)
        self.assertTrue(np.all(fa.min_gen_mechanism[0, jan] == MECH_HYDRO_ROR_FLAT))
        # Thermal untouched.
        np.testing.assert_allclose(fa.min_gen[1:], 0.0)
        np.testing.assert_allclose(fa.availability[1], 1.0)

    def test_missing_classifier_leaves_fleet_shapeable(self):
        # Point CLEAN_DIR at an empty tree: the gate arms but no partition
        # exists — the loader returns None and the fleet stays shapeable.
        import shutil

        from market_sim.data.hydro import build_hydro_fleet

        shutil.rmtree(self.clean_dir / "hydro-plant-modes")
        units, _ = build_hydro_fleet("CAISO", 2023, self.ZONES, ror_split=True)
        self.assertTrue(all(u.hydro_ror_flat_monthly_mw is None for u in units))

    def test_d4_window_declared_all_hours(self):
        import sys

        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import legitimacy_diagnostics as ld
        from market_sim.data.floor_mechanisms import MECH_HYDRO_ROR_FLAT

        self.assertEqual(ld.D4_WINDOWS[(MECH_HYDRO_ROR_FLAT, None)], (0, 24))

    def test_ablation_registry_classifies_the_mechanism(self):
        from market_sim.data.floor_mechanisms import (
            MECH_ABLATION_FIELDS,
            MECH_HYDRO_ROR_FLAT,
            MECH_NAMES,
            NON_THERMAL_MECHS,
            assert_ablation_coverage,
        )

        assert_ablation_coverage()
        self.assertIn(MECH_HYDRO_ROR_FLAT, MECH_NAMES)
        self.assertIn(MECH_HYDRO_ROR_FLAT, NON_THERMAL_MECHS)
        self.assertEqual(
            MECH_ABLATION_FIELDS[MECH_HYDRO_ROR_FLAT], {"hydro_ror_split": False}
        )


class NameplateAwareScaleTest(unittest.TestCase):
    """The rule-14 water-filling monthly-target rescale (caiso-127 SECONDARY)."""

    def setUp(self):
        from market_sim.data.hydro import _nameplate_aware_scale

        self.scale = _nameplate_aware_scale
        self.hpm = hours_per_month().astype(float)

    def test_byte_identical_to_the_uniform_scale_below_the_bound(self):
        """No plant-month over its ceiling => exactly the uniform expression."""
        energy = np.array([[100.0] * 12, [300.0] * 12])
        bound = np.array([[1e9] * 12, [1e9] * 12])
        target = np.full(12, 800.0)
        out, stats = self.scale(energy, bound, target)
        col_sums = energy.sum(axis=0)
        uniform = energy * (target / col_sums)[np.newaxis, :]
        np.testing.assert_array_equal(out, uniform)
        self.assertEqual(stats["clipped"], 0.0)
        self.assertEqual(stats["moved_mwh"], 0.0)

    def test_clipped_plant_month_reallocates_and_hits_the_target(self):
        """A capped small plant hands its excess to the plants with headroom."""
        energy = np.array([[100.0] * 12, [100.0] * 12])
        bound = np.array([[120.0] * 12, [1e9] * 12])
        target = np.full(12, 400.0)  # uniform would put 200 on each
        out, stats = self.scale(energy, bound, target)
        np.testing.assert_allclose(out[0], 120.0)
        np.testing.assert_allclose(out[1], 280.0)
        np.testing.assert_allclose(out.sum(axis=0), target)
        self.assertEqual(stats["clipped"], 12.0)
        self.assertAlmostEqual(stats["moved_mwh"], 12 * 80.0)
        self.assertEqual(stats["short_mwh"], 0.0)

    def test_physically_unattainable_month_reports_the_shortfall(self):
        """Target above the fleet ceiling: every plant at bound, shortfall logged."""
        energy = np.array([[100.0] * 12, [100.0] * 12])
        bound = np.array([[50.0] * 12, [50.0] * 12])
        target = np.full(12, 400.0)
        out, stats = self.scale(energy, bound, target)
        np.testing.assert_allclose(out, 50.0)
        self.assertAlmostEqual(stats["short_mwh"], 12 * 300.0)

    def test_cascading_overflow_converges(self):
        """Re-allocation that overflows a second plant keeps water-filling."""
        energy = np.array([[10.0], [10.0], [10.0]])
        bound = np.array([[12.0], [15.0], [1e9]])
        target = np.array([90.0])
        out, stats = self.scale(energy, bound, target)
        np.testing.assert_allclose(out[:, 0], [12.0, 15.0, 63.0])
        self.assertAlmostEqual(float(out.sum()), 90.0)
        self.assertEqual(stats["clipped"], 2.0)

    def test_loader_gate_is_off_by_default_and_registered(self):
        """The gate exists on ScenarioConfig and defaults off (rule 24)."""
        from market_sim.config.scenarios import ScenarioConfig

        self.assertFalse(ScenarioConfig(iso="CAISO").hydro_budget_nameplate_aware)


if __name__ == "__main__":
    unittest.main()
