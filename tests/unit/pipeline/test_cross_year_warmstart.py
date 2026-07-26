"""Cross-year warm-start basis transfer: neutrality across a changed fleet.

The cross-year warm-start carries one ISO-year's optimal basis into the next
year's first solve, remapping it onto a fleet that has gained and lost units.
Because an LP's optimum is independent of the starting basis, the warm path must
reproduce the cold path's cleared prices and generation exactly (up to the same
degenerate tie-breaking the intra-year warm-start already tolerates). These
tests pin that invariant; the runtime payoff is measured separately on the real
ERCOT LP by ``scripts/bench_warmstart_xyear.py``.
"""

import unittest

import numpy as np

from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import DispatchModel

T = 168
ZONES = ["Z"]


def _fleet(specs):
    gens = [
        Generator(
            unit_id=u,
            name=u,
            zone="Z",
            fuel_type="gas_cc",
            pmax_mw=p,
            pmin_mw=0.0,
            heat_rate=h,
            eford=0.0,
        )
        for (u, p, h) in specs
    ]
    return generators_to_fleet_arrays(gens, ZONES, hours=T)


def _demand(scale=1.0):
    return np.array([[scale * (500 + 200 * np.sin(t / 12)) for t in range(T)]])


_ZERO_CF = np.zeros((1, T))
_ZERO_CAP = np.array([0.0])


def _build(fleet, demand):
    return DispatchModel(
        fleet, demand, _ZERO_CF, _ZERO_CAP, _ZERO_CF, _ZERO_CAP, voll=5000.0, T=T
    )


class TestCrossYearWarmStart(unittest.TestCase):
    def test_changed_fleet_basis_is_generation_and_price_neutral(self):
        # Year A: units U0..U9.
        fleet_a = _fleet([(f"U{i}", 100 + 5 * i, 7.0 + 0.1 * i) for i in range(10)])
        mc_a = np.broadcast_to((fleet_a.heat_rate * 3.0)[:, None], (fleet_a.n_gen, T))
        model_a = _build(fleet_a, _demand())
        model_a.solve(mc=mc_a.copy())
        basis = model_a.export_cross_year_basis()
        self.assertIsNotNone(basis)

        # Year B: retire U0/U1, add U10/U11, lift demand and costs.
        fleet_b = _fleet([(f"U{i}", 100 + 5 * i, 7.0 + 0.1 * i) for i in range(2, 12)])
        mc_b = np.broadcast_to(
            (fleet_b.heat_rate * 3.2)[:, None], (fleet_b.n_gen, T)
        ).copy()
        demand_b = _demand(1.05)

        cold = _build(fleet_b, demand_b).solve(mc=mc_b.copy())

        warm_model = _build(fleet_b, demand_b)
        self.assertTrue(warm_model.apply_cross_year_basis(basis))
        warm = warm_model.solve(mc=mc_b.copy())

        # Same global optimum, cleared prices and per-unit annual energy.
        self.assertAlmostEqual(cold.objective_value, warm.objective_value, delta=1e-3)
        self.assertLess(float(np.abs(cold.prices - warm.prices).max()), 1e-6)
        cold_gen = cold.dispatch.sum(axis=1)
        warm_gen = warm.dispatch.sum(axis=1)
        self.assertLess(float(np.abs(cold_gen - warm_gen).max()), 1e-3)

    def test_apply_is_skipped_when_horizon_differs(self):
        fleet_a = _fleet([("U0", 100.0, 7.0)])
        model_a = _build(fleet_a, _demand())
        model_a.solve(mc=np.full((1, T), 21.0))
        basis = model_a.export_cross_year_basis()
        # A model on a different horizon cannot take the hour-blocked basis.
        gens = [
            Generator(
                unit_id="U0",
                name="U0",
                zone="Z",
                fuel_type="gas_cc",
                pmax_mw=100.0,
                pmin_mw=0.0,
                heat_rate=7.0,
                eford=0.0,
            )
        ]
        fleet_24 = generators_to_fleet_arrays(gens, ZONES, hours=24)
        other = DispatchModel(
            fleet_24,
            _demand()[:, :24],
            np.zeros((1, 24)),
            _ZERO_CAP,
            np.zeros((1, 24)),
            _ZERO_CAP,
            voll=5000.0,
            T=24,
        )
        self.assertFalse(other.apply_cross_year_basis(basis))

    def test_export_before_solve_returns_none(self):
        model = _build(_fleet([("U0", 100.0, 7.0)]), _demand())
        self.assertIsNone(model.export_cross_year_basis())


if __name__ == "__main__":
    unittest.main()
