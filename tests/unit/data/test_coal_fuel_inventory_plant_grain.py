"""Tests for the per-coal-yard annual budget (miso-268, coal_fuel_inventory_plant_grain).

Trivial-first: two plants and one shared yard on hand-written clean data, then
the yard arithmetic, the rule-13 read, the no-substitute rule, and an
end-to-end LP in which the pooled budget has slack but one yard does not — the
case the partition exists for.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from market_sim.data.coal_fuel_inventory import (  # noqa: E402
    build_coal_fuel_budget,
    build_coal_plant_budget,
    coal_yard_groups,
)
from market_sim.model.dispatch import solve_dispatch  # noqa: E402
from scripts.lib.clean_io import write_clean  # noqa: E402
from tests.helpers.base import CleanDirTestCase  # noqa: E402
from tests.unit.data.test_coal_fuel_inventory import (  # noqa: E402
    _HOURS,
    _coal_fleet,
    _receipt_row,
    _stock_row,
)


class CoalYardBudgetTest(CleanDirTestCase):
    """Plant 1001 holds 1,000 t + 800 t/yr; plant 1002 files ZERO; 1003 never files."""

    def setUp(self):
        super().setUp()
        self.ref = self.tmp_path / "reference"
        self.ref.mkdir(parents=True, exist_ok=True)
        (self.ref / "coal-shared-storage-crosswalk.csv").write_text(
            "storage_plant_id,storage_plant_name,served_plant_ids,iso,source\n"
            "8841,Yard,2001 2002,MISO,test\n",
            encoding="utf-8",
        )
        stocks = [_stock_row(1001, 2021, 12, 1000), _stock_row(1002, 2021, 12, 0)]
        stocks += [_stock_row(8841, 2021, 12, 500)]
        write_clean(pd.DataFrame(stocks), "coal-stocks", year=2021, source="test")
        write_clean(
            pd.DataFrame([_stock_row(1001, 2022, 12, 999_999)]),
            "coal-stocks", year=2022, source="test",
        )
        write_clean(
            pd.DataFrame([_receipt_row(1001, 2020, 1, 600), _receipt_row(8841, 2020, 1, 100)]),
            "coal-receipts", year=2020, source="test",
        )
        write_clean(
            pd.DataFrame([_receipt_row(1001, 2021, 1, 1000), _receipt_row(8841, 2021, 1, 300)]),
            "coal-receipts", year=2021, source="test",
        )
        write_clean(
            pd.DataFrame([_receipt_row(1001, 2022, 1, 999_999)]),
            "coal-receipts", year=2022, source="test",
        )

    def test_shared_yard_pools_its_served_plants_and_the_entity(self):
        fleet = _coal_fleet([1001, 2001, 2002])
        yards = coal_yard_groups(fleet, reference_dir=self.ref)
        self.assertEqual(yards, {1001: {1001}, 2001: {2001, 2002, 8841}})

    def test_budget_per_yard_and_no_row_without_a_record(self):
        fleet = _coal_fleet([1001, 1002, 1003, 2001, 2002])
        gidx, budget, month, coeff, grp, prov = build_coal_plant_budget(
            fleet, 2022, hours=_HOURS, reference_dir=self.ref
        )
        # 1001: (1000 + 800) x 20; 1002 filed zero -> 0; yard 2001: (500 + 200) x 20.
        np.testing.assert_allclose(sorted(budget[:, 0]), [0.0, 14_000.0, 36_000.0])
        # 1003 never filed: its generator carries no row (never substituted).
        self.assertEqual(prov.n_unrowed_generators, 1)
        self.assertNotIn(2, gidx.tolist())
        self.assertEqual(budget.shape[1], 1)
        np.testing.assert_array_equal(month, np.zeros(_HOURS, dtype=int))
        # Units 3 and 4 share the yard's row.
        self.assertEqual(grp[list(gidx).index(3)], grp[list(gidx).index(4)])
        self.assertNotIn(2022, prov.rate_source_years)

    def test_yard_budgets_sum_to_the_pooled_annual_identity(self):
        fleet = _coal_fleet([1001, 2001, 2002])
        _, budget, *_ = build_coal_plant_budget(fleet, 2022, hours=_HOURS, reference_dir=self.ref)
        pooled = build_coal_fuel_budget(fleet, 2022, hours=_HOURS, reference_dir=self.ref)
        self.assertAlmostEqual(float(budget.sum()), float(pooled[1].sum()))


class YardBindsWherePoolDoesNotTest(unittest.TestCase):
    """Pooled budget is loose; yard A's own budget binds and gas backfills."""

    T = 24

    def test_yard_row_binds_under_a_slack_pool(self):
        fleet = _coal_fleet([1, 2], heat_rate=10.0, pmax=100.0, hours=self.T)
        # A is cheap (MC 20), B dear coal (MC 40), gas MC 50; demand 100 MW.
        demand = np.full((1, self.T), 100.0)
        mc = np.vstack([np.full(self.T, 20.0), np.full(self.T, 40.0), np.full(self.T, 50.0)])
        base = dict(
            wind_cf=np.zeros((1, self.T)), wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, self.T)), solar_cap=np.zeros(1),
        )
        pooled = np.full((1, 12), np.inf)
        pooled[0, 0] = 50_000.0  # loose: 5,000 MWh of coal against 2,400 wanted
        base.update(
            coal_monthly_budget=pooled, coal_gen_idx=np.array([0, 1]),
            coal_month_index=np.zeros(self.T, dtype=int),
            coal_gen_hour_coeff=np.array([10.0, 10.0]), coal_group_index=np.array([0, 0]),
        )
        r0 = solve_dispatch(fleet, demand, mc=mc, T=self.T, **base)
        self.assertAlmostEqual(float(r0.dispatch[0].sum()), 2400.0, places=3)
        yard = dict(base)
        yard.update(
            coal_plant_budget=np.array([[6_000.0], [np.inf]]),  # A: 600 MWh
            coal_plant_gen_idx=np.array([0, 1]),
            coal_plant_month_index=np.zeros(self.T, dtype=int),
            coal_plant_gen_hour_coeff=np.array([10.0, 10.0]),
            coal_plant_group_index=np.array([0, 1]),
        )
        r1 = solve_dispatch(fleet, demand, mc=mc, T=self.T, **yard)
        self.assertLessEqual(float(r1.dispatch[0].sum()), 600.0 + 1e-6)
        # B's own coal, not gas, takes the displaced energy: it has its own pile.
        self.assertAlmostEqual(float(r1.dispatch[1].sum()), 1800.0, places=3)
        self.assertAlmostEqual(float(r1.dispatch[2].sum()), 0.0, places=3)
        np.testing.assert_allclose(r1.prices, 40.0, atol=1e-6)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
