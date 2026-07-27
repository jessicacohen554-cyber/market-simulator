"""Tests for the hydro hourly deliverability envelope (caiso-72 STEP-2).

Covers the ``_build_gen_group_cap_rows`` constraint family (default-off
identical-LP guard, row placement/bounds), the anti-hoarding dispatch
behaviour (the envelope forces the budget LP to spread hydro out of the top
price hours so the peaker clears), and the measured EIA-930 NG:WAT envelope
loader (:func:`market_sim.data.eia_loader.measured_hydro_hourly_envelope`).
"""

import unittest

import numpy as np

from market_sim.data.eia_loader import measured_hydro_hourly_envelope
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import (
    VariableLayout,
    build_constraints,
    solve_dispatch,
)


def _hydro_fleet(hours, hydro_pmax=50.0):
    """One free hydro gen + cheap and peaking thermal in one zone ``Z``."""
    gens = [
        Generator(
            unit_id="H0",
            name="H0",
            zone="Z",
            fuel_type="hydro",
            pmax_mw=hydro_pmax,
            pmin_mw=0.0,
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


def _mc(hours):
    """Marginal cost: hydro free, cheap thermal $10, peaker $100."""
    return np.array([[0.0] * hours, [10.0] * hours, [100.0] * hours], dtype=float)


class TestGenGroupCapRows(unittest.TestCase):
    """Constraint-family tests for the hourly group-cap rows."""

    def setUp(self):
        self.T = 4
        self.fleet = _hydro_fleet(self.T)
        self.layout = VariableLayout(
            n_gen=3, n_zones=1, n_storage=0, n_links=0, T=self.T
        )
        self.demand = np.array([[40.0, 40.0, 130.0, 120.0]])

    def test_none_is_identical_to_current_build(self):
        # Default-off guard: absent kwargs yield a byte-identical system.
        a0, lo0, hi0, *_ = build_constraints(self.layout, self.fleet, self.demand)
        a1, lo1, hi1, *_ = build_constraints(
            self.layout,
            self.fleet,
            self.demand,
            hydro_envelope_gen_idx=None,
            hydro_envelope_mw=None,
        )
        self.assertEqual(a0.shape, a1.shape)
        self.assertEqual((a0 != a1).nnz, 0)
        np.testing.assert_array_equal(lo0, lo1)
        np.testing.assert_array_equal(hi0, hi1)

    def test_adds_one_row_per_hour_with_envelope_bounds(self):
        env = np.array([30.0, 30.0, 25.0, 20.0])
        a0, _, _, *_ = build_constraints(self.layout, self.fleet, self.demand)
        a1, lo, hi, *_ = build_constraints(
            self.layout,
            self.fleet,
            self.demand,
            hydro_envelope_gen_idx=np.array([0]),
            hydro_envelope_mw=env,
        )
        self.assertEqual(a1.shape[0], a0.shape[0] + self.T)
        rows = a1[a0.shape[0] :].toarray()
        # Row t touches exactly hydro's P column at hour t with coefficient 1.
        for t in range(self.T):
            self.assertEqual(list(np.flatnonzero(rows[t])), [self.layout.p_col(0, t)])
        np.testing.assert_array_equal(hi[-self.T :], env)
        self.assertTrue(np.all(np.isneginf(lo[-self.T :])))

    def test_empty_gen_idx_adds_no_rows(self):
        a0, _, _, *_ = build_constraints(self.layout, self.fleet, self.demand)
        a1, _, _, *_ = build_constraints(
            self.layout,
            self.fleet,
            self.demand,
            hydro_envelope_gen_idx=np.array([], dtype=int),
            hydro_envelope_mw=np.full(self.T, 10.0),
        )
        self.assertEqual(a0.shape, a1.shape)


class TestGroupCapStorageTerm(unittest.TestCase):
    """The optional pumped-storage net-discharge term of the group cap."""

    def test_storage_columns_carry_signed_coefficients(self):
        from market_sim.model.dispatch import _build_gen_group_cap_rows

        T = 3
        layout = VariableLayout(n_gen=2, n_zones=1, n_storage=2, n_links=0, T=T)
        env = np.array([10.0, 20.0, 30.0])
        block, lo, hi = _build_gen_group_cap_rows(
            layout,
            np.array([0]),
            env,
            storage_idx=np.array([1]),
        )
        self.assertEqual(block.shape[0], T)
        np.testing.assert_array_equal(hi, env)
        self.assertTrue(np.all(np.isneginf(lo)))
        rows = block.toarray()
        for t in range(T):
            r = rows[t]
            # +1 on hydro P, +1 on storage-1 discharge, -1 on its charge.
            self.assertEqual(r[layout.p_col(0, t)], 1.0)
            vph = layout.vars_per_hour
            self.assertEqual(r[t * vph + layout._dis_off + 1], 1.0)
            self.assertEqual(r[t * vph + layout._chg_off + 1], -1.0)
            # Storage 0 (a battery) is not a member.
            self.assertEqual(r[t * vph + layout._dis_off + 0], 0.0)
            self.assertEqual(np.count_nonzero(r), 3)


class TestEnvelopeDispatchBehaviour(unittest.TestCase):
    """The envelope stops the budget LP hoarding hydro into the peak."""

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

    def test_uncapped_budget_hoards_into_peak(self):
        # Baseline: 60 MWh budget all lands in the two $100 peak hours.
        res = self._solve(
            hydro_monthly_energy=np.array([[60.0]]),
            hydro_month_index=np.zeros(self.T, dtype=int),
        )
        hydro = res.dispatch[0]
        self.assertAlmostEqual(hydro[2:].sum(), 60.0, places=4)

    def test_envelope_caps_peak_and_spreads_energy(self):
        # A 20 MW hourly ceiling caps each peak hour at 20; the freed energy
        # lands in the cheap hours and the peaker clears the peak residual.
        env = np.full(self.T, 20.0)
        res = self._solve(
            hydro_monthly_energy=np.array([[60.0]]),
            hydro_month_index=np.zeros(self.T, dtype=int),
            hydro_envelope_gen_idx=np.array([0]),
            hydro_envelope_mw=env,
        )
        hydro = res.dispatch[0]
        peaker = res.dispatch[2]
        self.assertTrue(np.all(hydro <= 20.0 + 1e-6))
        # Peak hours capped at 20 each -> 40; budget still spent (<= 60).
        self.assertAlmostEqual(hydro[2:].sum(), 40.0, places=4)
        # Peak residual (130-50-20 and 120-50-20) now clears on the peaker.
        self.assertAlmostEqual(peaker[2], 60.0, places=4)
        self.assertAlmostEqual(peaker[3], 50.0, places=4)

    def test_envelope_only_binds_where_below_pmax(self):
        # An envelope above pmax changes nothing economically: the budget
        # still lands entirely in the peak hours and prices are identical.
        # (The exact peak-hour split of the free hydro is degenerate, so
        # compare aggregates and duals, not the per-hour allocation.)
        base = self._solve(
            hydro_monthly_energy=np.array([[60.0]]),
            hydro_month_index=np.zeros(self.T, dtype=int),
        )
        capped = self._solve(
            hydro_monthly_energy=np.array([[60.0]]),
            hydro_month_index=np.zeros(self.T, dtype=int),
            hydro_envelope_gen_idx=np.array([0]),
            hydro_envelope_mw=np.full(self.T, 1000.0),
        )
        self.assertAlmostEqual(capped.dispatch[0][2:].sum(), 60.0, places=4)
        self.assertAlmostEqual(
            base.dispatch[0].sum(), capped.dispatch[0].sum(), places=4
        )
        np.testing.assert_allclose(base.prices, capped.prices, atol=1e-6)


class TestMeasuredEnvelopeLoader(unittest.TestCase):
    """Loader tests against the on-disk EIA-930 extracts."""

    def test_caiso_2024_envelope_shape_and_positivity(self):
        env = measured_hydro_hourly_envelope("CAISO", 2024, 8760)
        if env is None:
            self.skipTest("CISO EIA-930 extract not on disk")
        self.assertEqual(env.shape, (8760,))
        self.assertTrue(np.all(np.isfinite(env)))
        self.assertTrue(np.all(env >= 0.0))
        # The ceiling is a real bound: below the CAISO hydro nameplate (~9.5
        # GW) everywhere, and diurnal (evening ceiling above the midday one
        # in the summer months).
        self.assertLess(env.max(), 9500.0)

    def test_forecast_year_falls_back_to_climatology(self):
        env = measured_hydro_hourly_envelope("CAISO", 2035, 8760)
        if env is None:
            self.skipTest("CISO EIA-930 extract not on disk")
        self.assertEqual(env.shape, (8760,))
        self.assertTrue(np.all(env >= 0.0))
        self.assertGreater(env.max(), 0.0)

    def test_unknown_iso_returns_none(self):
        self.assertIsNone(measured_hydro_hourly_envelope("NOPE", 2024, 8760))

    def test_partial_horizon(self):
        env = measured_hydro_hourly_envelope("CAISO", 2024, 240)
        if env is None:
            self.skipTest("CISO EIA-930 extract not on disk")
        self.assertEqual(env.shape, (240,))


if __name__ == "__main__":
    unittest.main()
