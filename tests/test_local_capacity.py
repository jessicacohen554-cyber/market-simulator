"""Tests for the local-capacity (LCR-area) minimum-generation rows.

Design: docs/ramp-locational-design-2026-07.md §3 / §7 (T4-T5). Trivial cases
first (2 gens, 1 zone, 24 hours); the RHS builder is exercised against the
committed CAISO published-study inputs.
"""

import unittest

import numpy as np

from market_sim.data.local_capacity import (
    build_local_capacity_specs,
    load_lcr_parameters,
)
from market_sim.model.dispatch import (
    VariableLayout,
    _build_local_capacity_rows,
    build_constraints,
    solve_dispatch,
)
from tests.test_dispatch import _make_fleet

T24 = 24


def _no_renewables(n_zones, T):
    """Zero wind/solar kwargs for ``solve_dispatch``."""
    return dict(
        wind_cf=np.zeros((n_zones, T)),
        wind_cap=np.zeros(n_zones),
        solar_cf=np.zeros((n_zones, T)),
        solar_cap=np.zeros(n_zones),
    )


class TestLocalCapacityT4UpliftNotPrice(unittest.TestCase):
    """T4: the row commits the in-area unit without lifting the zonal LMP."""

    def _solve(self, with_lcr):
        # Gen 0: in-area, dear (MC 80, pmax 100). Gen 1: out-of-area, cheap
        # (MC 20, pmax 300). Flat demand 120; local need 50 MW in hours 18-21.
        fleet = _make_fleet(
            ["Z0", "Z0"], ["Z0"], hours=T24, pmax=100.0, pmin=0.0, eford=0.0
        )
        fleet.pmax[1] = 300.0
        mc = np.vstack([np.full(T24, 80.0), np.full(T24, 20.0)])
        demand = np.full((1, T24), 120.0)
        kwargs = dict(_no_renewables(1, T24))
        if with_lcr:
            rhs = np.zeros(T24)
            rhs[18:22] = 50.0
            kwargs.update(
                local_capacity_specs=[(np.array([0]), np.zeros(0, dtype=int), 0.0, rhs)]
            )
        return solve_dispatch(fleet, demand, mc=mc, T=T24, **kwargs)

    def test_in_area_unit_meets_local_need_in_binding_hours_only(self):
        result = self._solve(with_lcr=True)
        np.testing.assert_allclose(
            result.dispatch[0, 18:22], 50.0, atol=1e-6
        )  # exactly the local need — the unit is out of merit
        mask = np.ones(T24, dtype=bool)
        mask[18:22] = False
        np.testing.assert_allclose(result.dispatch[0, mask], 0.0, atol=1e-6)

    def test_zonal_lmp_stays_at_the_cheap_unit(self):
        # Uplift-not-price semantics: the cheap out-of-area unit still has
        # headroom in the binding hours, so it stays marginal and the zonal
        # energy dual never sees the dear in-area unit's offer.
        result = self._solve(with_lcr=True)
        np.testing.assert_allclose(result.prices, 20.0, atol=1e-4)

    def test_flag_off_in_area_unit_never_runs(self):
        result = self._solve(with_lcr=False)
        np.testing.assert_allclose(result.dispatch[0], 0.0, atol=1e-6)


class TestLocalCapacityFlagOffByteIdentity(unittest.TestCase):
    """No specs -> zero rows -> byte-identical constraint matrix."""

    def test_empty_specs_add_no_rows(self):
        fleet = _make_fleet(
            ["Z0", "Z0"], ["Z0"], hours=T24, pmax=100.0, pmin=0.0, eford=0.0
        )
        demand = np.full((1, T24), 120.0)
        layout = VariableLayout(n_gen=2, n_zones=1, n_storage=0, n_links=0, T=T24)
        a0, lo0, up0, *_ = build_constraints(layout, fleet, demand)
        a1, lo1, up1, *_ = build_constraints(
            layout, fleet, demand, local_capacity_specs=[]
        )
        a2, lo2, up2, *_ = build_constraints(
            layout, fleet, demand, local_capacity_specs=None
        )
        for a, lo, up in ((a1, lo1, up1), (a2, lo2, up2)):
            self.assertEqual(a0.shape, a.shape)
            self.assertEqual((a0 != a).nnz, 0)
            np.testing.assert_array_equal(lo0, lo)
            np.testing.assert_array_equal(up0, up)


class TestLocalCapacityStorageCoefficients(unittest.TestCase):
    """In-area storage share enters the row LHS with the right signs."""

    def test_storage_coefficients_and_signs(self):
        layout = VariableLayout(n_gen=1, n_zones=1, n_storage=1, n_links=0, T=T24)
        rhs = np.full(T24, 10.0)
        block, lower, upper = _build_local_capacity_rows(
            layout, [(np.array([0]), np.array([0]), 0.5, rhs)]
        )
        self.assertEqual(block.shape[0], T24)
        for t in (0, 12):
            row = block.getrow(t).toarray().ravel()
            self.assertEqual(row[layout.p_col(0, t)], 1.0)
            self.assertEqual(row[layout.dis_col(0, t)], 0.5)
            self.assertEqual(row[layout.chg_col(0, t)], -0.5)
        np.testing.assert_allclose(lower, 10.0)
        self.assertTrue(np.all(np.isinf(upper)))


class TestLocalCapacityT5RhsBuilder(unittest.TestCase):
    """T5: clip, share scaling, per-year selection, thermal-only cap.

    Exercises the published CAISO study inputs committed in the repo
    (capacity-deliverability intake + LCR membership crosswalk).
    """

    def _specs(self, demand_mw, member_pmax, with_storage):
        # Two committed LA Basin members (NQC-list override plants).
        plant_code = np.array([57482, 55541])
        pmax = np.asarray(member_pmax, dtype=float)
        availability = np.ones((2, T24))
        demand = np.full((1, T24), 20_000.0)
        demand[0, 20:] = demand_mw
        storage_zone_idx = np.array([0]) if with_storage else None
        storage_power_cap = np.array([100.0]) if with_storage else None
        return build_local_capacity_specs(
            "CAISO",
            2024,
            plant_code,
            pmax,
            availability,
            ["SP15"],
            demand,
            storage_zone_idx,
            storage_power_cap,
        )

    def test_rhs_clips_to_zero_below_the_import_cap(self):
        params = load_lcr_parameters("CAISO", 2024)
        self.assertIn("LA Basin", params)
        la = params["LA Basin"]
        # Published 2024 numbers: requirement 4,413, peak 19,637 -> import
        # cap 15,224 MW; share = 19,637 / 28,310 SP26 zonal peak.
        self.assertAlmostEqual(la["import_cap_mw"], 19637.0 - 4413.0)
        self.assertAlmostEqual(la["share"], 19637.0 / 28310.0, places=6)

        specs, meta = self._specs(
            demand_mw=25_000.0, member_pmax=[5000.0, 5000.0], with_storage=False
        )
        self.assertEqual(len(specs), 1)  # SD-IV has no members here
        gen_idx, s_idx, s_frac, rhs = specs[0]
        self.assertEqual(gen_idx.size, 2)
        self.assertEqual(s_idx.size, 0)
        self.assertEqual(s_frac, 0.0)
        # share*20,000 = ~13,875 < import cap -> clipped to exactly 0.
        np.testing.assert_allclose(rhs[:20], 0.0)
        # share*25,000 - import_cap binds in the evening block.
        expected = la["share"] * 25_000.0 - la["import_cap_mw"]
        np.testing.assert_allclose(rhs[20:], expected, rtol=1e-9)

    def test_per_year_requirement_selection(self):
        p23 = load_lcr_parameters("CAISO", 2023)["LA Basin"]
        p24 = load_lcr_parameters("CAISO", 2024)["LA Basin"]
        self.assertAlmostEqual(p23["requirement_mw"], 7529.0)
        self.assertAlmostEqual(p24["requirement_mw"], 4413.0)
        self.assertNotEqual(p23["import_cap_mw"], p24["import_cap_mw"])

    def test_rhs_cap_is_thermal_only(self):
        # Tiny in-area thermal fleet: the cap must bind at 99.9% of THERMAL
        # capacity even when in-area storage exists — crediting storage
        # toward the guarantee went infeasible on 2023 (SOC-limited).
        specs, meta = self._specs(
            demand_mw=25_000.0, member_pmax=[400.0, 200.0], with_storage=True
        )
        gen_idx, s_idx, s_frac, rhs = specs[0]
        self.assertGreater(s_frac, 0.0)  # storage IS on the row LHS...
        self.assertEqual(s_idx.size, 1)
        # ...but the feasibility cap ignores it entirely.
        np.testing.assert_allclose(rhs[20:], 0.999 * 600.0, rtol=1e-9)


if __name__ == "__main__":
    unittest.main()
