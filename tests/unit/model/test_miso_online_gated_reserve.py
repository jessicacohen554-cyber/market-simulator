"""Online-gated pergen reserve supply (miso_reserve_online_gated) LP semantics.

PREREG-miso167 §2 at trivial scale (1 zone, 2 gens in one pool, 4 hours):
the pool's R column splits into a GATED product column (coupling row
``R ≤ online_rho · Σ P`` — idle capacity backs none of it) and an UNGATED
product column (offline-eligible, exactly today's semantics), a nested
gated-only balance family draws the gated column, and a pool-shared ramp row
holds the two product columns inside one 10-minute deliverable ramp.
"""

import unittest

import numpy as np

from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays
from market_sim.model.dispatch import solve_dispatch


class TestMisoOnlineGatedReserveLP(unittest.TestCase):
    _T = 4

    def _fleet(self):
        cc_idx = FUEL_TYPE_NAMES.index("gas_cc")
        n = 2
        return FleetArrays(
            pmax=np.array([400.0, 400.0]),
            pmin=np.zeros(n),
            heat_rate=np.array([7.0, 7.5]),
            vom=np.zeros(n),
            emission_rate=np.zeros(n),
            nox_rate=np.zeros(n),
            so2_rate=np.zeros(n),
            zone_idx=np.zeros(n, dtype=int),
            fuel_type_idx=np.full(n, cc_idx),
            availability=np.ones((n, self._T)),
            unit_ids=["cc0", "cc1"],
            efficiency_bin=np.zeros(n),
            plant_code=np.array([1, 2]),
            ramp10=np.array([400.0, 400.0]),
        )

    def _solve(
        self,
        demand_mw: float,
        gated_req: float,
        total_req: float,
        online_rho: float = 0.3,
        pool_ramp: float = 800.0,
    ):
        T = self._T
        # Columns: [0] = GATED product, [1] = UNGATED product, one pool.
        col_pool = np.array([0, 0])
        requirement = np.vstack(
            [np.full(T, total_req), np.full(T, gated_req)]
        )  # (2 families, T)
        balance_zone_mask = np.ones((2, 1), dtype=bool)
        balance_col_mask = np.array([[True, True], [True, False]])
        # One high shortfall step per family, wide enough to span it.
        ordc_penalties = np.array([1000.0, 1000.0])
        ordc_step_widths = np.array([max(total_req, 1.0), max(gated_req, 1.0)])
        return solve_dispatch(
            self._fleet(),
            np.full((1, T), demand_mw),
            wind_cf=np.zeros((1, T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, T)),
            solar_cap=np.zeros(1),
            fuel_prices=np.full((2, T), 1.0),
            voll=5000.0,
            reserve_requirement=requirement,
            reserve_eligible=np.ones((1, 2), dtype=bool),
            ordc_penalties=ordc_penalties,
            ordc_step_widths=ordc_step_widths,
            reserve_balance_zone_mask=balance_zone_mask,
            reserve_balance_ordc_counts=np.array([1, 1]),
            reserve_pergen_gen_idx=np.array([0, 1]),
            reserve_pergen_col=np.array([0, 0]),  # members -> POOL 0
            reserve_pergen_ramp10=np.full((2, T), pool_ramp),
            reserve_pergen_col_pool=col_pool,
            reserve_balance_col_mask=balance_col_mask,
            reserve_pergen_online_gated_cols=np.array([True, False]),
            reserve_online_rho=online_rho,
            reserve_pergen_pool_ramp10=np.full((1, T), pool_ramp),
        )

    def test_gated_product_needs_online_output(self):
        # Demand ~0 but a 50 MW gated requirement at rho=0.3: backing it
        # takes >= 50/0.3 = 166.7 MW of ON-LINE output. Dispatching that
        # (mc x heat_rate ~ $7/MWh, overgeneration dumped) is far cheaper
        # than the $1,000 shortfall step, so the LP runs the fleet up
        # purely to synchronise reserve backing — the commitment-driver
        # semantics the mechanism exists for.
        r = self._solve(demand_mw=1.0, gated_req=50.0, total_req=50.0)
        self.assertEqual(r.status, "Optimal")
        disp = np.asarray(r.dispatch).sum(axis=0)
        self.assertTrue(
            np.all(disp >= 50.0 / 0.3 - 1e-4),
            f"online output {disp} must back the gated requirement",
        )
        # The gated family's dual carries the SYNCHRONISATION opportunity
        # cost: one more MW of gated reserve takes 1/rho more MW of online
        # output at the marginal cost (heat_rate 7.0 x fuel 1.0), so the
        # reserve price clears at mc/rho — never $0 (the phantom-headroom
        # defect) and never the shortfall step (the requirement is met).
        self.assertAlmostEqual(
            float(np.asarray(r.reserve_price).mean()), 7.0 / 0.3, delta=1.0
        )

    def test_ungated_product_clears_offline(self):
        # No gated requirement; the 100 MW total requirement can clear on
        # the UNGATED column with the fleet idle (offline supplemental
        # semantics — exactly the pre-split behavior).
        r = self._solve(demand_mw=1.0, gated_req=0.0, total_req=100.0)
        self.assertEqual(r.status, "Optimal")
        disp = np.asarray(r.dispatch).sum(axis=0)
        self.assertTrue(np.all(disp <= 5.0), f"no online backing needed: {disp}")
        self.assertAlmostEqual(float(np.asarray(r.reserve_price).mean()), 0.0)

    def test_pool_shared_ramp_binds_across_products(self):
        # Pool ramp 60 < total requirement 100: whatever the product split,
        # the pool can deliver only 60 MW in 10 minutes — the total family
        # runs 40 MW short and prices its $1,000 step. Without the shared
        # row the two product columns could stack to 2x the pool ramp and
        # clear a phantom 100.
        r = self._solve(demand_mw=1.0, gated_req=0.0, total_req=100.0, pool_ramp=60.0)
        self.assertEqual(r.status, "Optimal")
        self.assertGreater(float(np.asarray(r.reserve_price).mean()), 900.0)


if __name__ == "__main__":
    unittest.main()
