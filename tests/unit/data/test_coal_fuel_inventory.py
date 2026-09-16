"""Tests for the coal fuel-inventory monthly energy budget (miso-259).

Trivial-first (CLAUDE.md testing pattern): a tiny hand-checkable fleet and a
tiny hand-written pair of clean datatypes, then the budget arithmetic, then the
two things about this mechanism that can go wrong silently — the rule-13 read
(it must never touch the solved year) and the shared-storage footprint
crosswalk — and last an end-to-end 1-zone LP confirming the row actually binds
coal and prices the shortage through its dual.
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
    coal_footprint_plant_ids,
    coal_gen_idx,
)
from market_sim.data.fleet import Generator, generators_to_fleet_arrays  # noqa: E402
from market_sim.model.dispatch import solve_dispatch  # noqa: E402
from scripts.lib.clean_io import write_clean  # noqa: E402
from tests.helpers.base import CleanDirTestCase  # noqa: E402

_HOURS = 24


def _coal_fleet(plant_codes, *, heat_rate=10.0, pmax=100.0, hours=_HOURS):
    """One coal generator per plant code, plus one gas unit that must not be capped."""
    gens = [
        Generator(
            unit_id=f"C{code}",
            name=f"Coal {code}",
            zone="Z1",
            fuel_type="coal",
            pmax_mw=pmax,
            pmin_mw=0.0,
            eford=0.0,
            heat_rate=heat_rate,
            plant_code=code,
        )
        for code in plant_codes
    ]
    gens.append(
        Generator(
            unit_id="GAS",
            name="Gas",
            zone="Z1",
            fuel_type="gas_cc",
            pmax_mw=pmax,
            pmin_mw=0.0,
            eford=0.0,
            heat_rate=7.0,
            plant_code=9001,
        )
    )
    return generators_to_fleet_arrays(gens, ["Z1"], hours=hours)


def _stock_row(plant_id, year, month, tons):
    return {
        "plant_id": plant_id,
        "energy_source": "SUB",
        "year": year,
        "month": month,
        "ending_stock_tons": float(tons),
        "plant_name": f"P{plant_id}",
        "plant_state": "IL",
        "balancing_authority_code": "MISO",
        "nerc_region": "MRO",
        "eia_sector_number": 1,
        "physical_unit_label": "short tons",
    }


def _receipt_row(plant_id, year, month, tons, heat=20.0):
    return {
        "plant_id": plant_id,
        "energy_source": "SUB",
        "year": year,
        "month": month,
        "purchase_type": "C",
        "primary_transportation_mode": "RR",
        "quantity_tons": float(tons),
        "heat_content_mmbtu_per_ton": float(heat),
        "fuel_cost_cents_per_mmbtu": 200.0,
        "plant_name": f"P{plant_id}",
        "plant_state": "IL",
        "balancing_authority_code": "MISO",
    }


class CoalFuelBudgetTest(CleanDirTestCase):
    """The budget arithmetic and the rule-13 read, on hand-written clean data."""

    def setUp(self):
        super().setUp()
        self.ref = self.tmp_path / "reference"
        self.ref.mkdir(parents=True, exist_ok=True)
        # Prior years: 2020 stock ends December at 1,000 t; 2020 + 2021 receipts
        # are 600 and 1,000 t, so the 2022 rate is 800 t/yr at 20 MMBtu/t.
        # The SOLVED year 2022 carries deliberately absurd values, so any read
        # that touches it is unmistakable in the assertions below.
        write_clean(
            pd.DataFrame(
                [_stock_row(1001, 2021, m, 1000) for m in range(1, 13)]
                + [_stock_row(1001, 2022, m, 999_999) for m in range(1, 13)]
            ).query("year == 2021"),
            "coal-stocks",
            year=2021,
            source="test",
        )
        write_clean(
            pd.DataFrame([_stock_row(1001, 2022, m, 999_999) for m in range(1, 13)]),
            "coal-stocks",
            year=2022,
            source="test",
        )
        write_clean(
            pd.DataFrame([_receipt_row(1001, 2020, 1, 600)]),
            "coal-receipts",
            year=2020,
            source="test",
        )
        write_clean(
            pd.DataFrame([_receipt_row(1001, 2021, 1, 1000)]),
            "coal-receipts",
            year=2021,
            source="test",
        )
        write_clean(
            pd.DataFrame([_receipt_row(1001, 2022, 1, 999_999)]),
            "coal-receipts",
            year=2022,
            source="test",
        )

    def test_coal_gen_idx_selects_on_fuel_physics_not_class_name(self):
        fleet = _coal_fleet([1001, 1002])
        np.testing.assert_array_equal(coal_gen_idx(fleet), [0, 1])

    def test_budget_is_opening_stock_plus_prior_rate_over_twelve(self):
        """Trivial case, hand-checkable: (1000 + 800) t x 20 MMBtu/t / 12."""
        fleet = _coal_fleet([1001])
        result = build_coal_fuel_budget(
            fleet, 2022, hours=_HOURS, reference_dir=self.ref
        )
        self.assertIsNotNone(result)
        gen_idx, budget, month_index, coeff, group_index, prov = result
        self.assertEqual(prov.opening_stock_tons, 1000.0)
        self.assertEqual(prov.delivery_rate_tons_per_year, 800.0)
        self.assertEqual(prov.rate_source_years, (2020, 2021))
        self.assertAlmostEqual(prov.mmbtu_per_ton, 20.0)
        self.assertAlmostEqual(prov.annual_budget_mmbtu, 36_000.0)
        self.assertAlmostEqual(prov.monthly_budget_mmbtu, 3_000.0)
        # One pooled fleet row, the same cap in every one of the 12 months.
        self.assertEqual(budget.shape, (1, 12))
        np.testing.assert_allclose(budget, 3_000.0)
        np.testing.assert_array_equal(group_index, [0])
        # Only the coal generator is constrained; the gas unit is untouched.
        np.testing.assert_array_equal(gen_idx, [0])
        np.testing.assert_allclose(coeff, [10.0])
        self.assertEqual(month_index.shape, (_HOURS,))

    def test_solved_year_stock_and_receipts_are_never_read(self):
        """G-PIN in a unit test: the 2022 rows are absurd and must not appear."""
        fleet = _coal_fleet([1001])
        _, _, _, _, _, prov = build_coal_fuel_budget(
            fleet, 2022, hours=_HOURS, reference_dir=self.ref
        )
        self.assertLess(prov.opening_stock_tons, 999_999)
        self.assertLess(prov.delivery_rate_tons_per_year, 999_999)
        self.assertNotIn(2022, prov.rate_source_years)

    def test_missing_measured_input_returns_none_rather_than_a_substitute(self):
        """A year with no curated prior stock is unarmed, never sized on a guess."""
        fleet = _coal_fleet([1001])
        self.assertIsNone(
            build_coal_fuel_budget(fleet, 2019, hours=_HOURS, reference_dir=self.ref)
        )

    def test_fleet_with_no_coal_returns_none(self):
        gens = [
            Generator(
                unit_id="GAS",
                name="Gas",
                zone="Z1",
                fuel_type="gas_cc",
                pmax_mw=100.0,
                pmin_mw=0.0,
                eford=0.0,
                heat_rate=7.0,
                plant_code=9001,
            )
        ]
        fleet = generators_to_fleet_arrays(gens, ["Z1"], hours=_HOURS)
        self.assertIsNone(
            build_coal_fuel_budget(fleet, 2022, hours=_HOURS, reference_dir=self.ref)
        )


class SharedStorageCrosswalkTest(CleanDirTestCase):
    """The crosswalk adds fuel only to a fleet that holds a plant it serves."""

    def setUp(self):
        super().setUp()
        self.ref = self.tmp_path / "reference"
        self.ref.mkdir(parents=True, exist_ok=True)
        (self.ref / "coal-shared-storage-crosswalk.csv").write_text(
            "# comment line that must be skipped\n"
            "storage_plant_id,storage_plant_name,served_plant_ids,iso,source\n"
            "8841,Yard,6034 1743,MISO,test\n",
            encoding="utf-8",
        )

    def test_storage_entity_joins_only_when_a_served_plant_is_in_the_fleet(self):
        served = _coal_fleet([6034])
        ids, n_storage = coal_footprint_plant_ids(served, reference_dir=self.ref)
        self.assertEqual(ids, {6034, 8841})
        self.assertEqual(n_storage, 1)

        unrelated = _coal_fleet([1001])
        ids, n_storage = coal_footprint_plant_ids(unrelated, reference_dir=self.ref)
        self.assertEqual(ids, {1001})
        self.assertEqual(n_storage, 0)

    def test_absent_crosswalk_degrades_to_the_generator_only_footprint(self):
        fleet = _coal_fleet([6034])
        ids, n_storage = coal_footprint_plant_ids(
            fleet, reference_dir=self.tmp_path / "nonexistent"
        )
        self.assertEqual(ids, {6034})
        self.assertEqual(n_storage, 0)


class CoalBudgetBindsInAnLPTest(unittest.TestCase):
    """End to end: the row caps coal energy input and its dual prices the shortage."""

    T = 24

    def _solve(self, budget_mmbtu):
        # gen0 cheap coal (MC 20, HR 10), gen1 dearer gas (MC 50); demand 50 MW
        # against pmax 100 so exactly one unit is marginal in each hour.
        fleet = _coal_fleet([1001], heat_rate=10.0, pmax=100.0, hours=self.T)
        demand = np.full((1, self.T), 50.0)
        mc = np.vstack([np.full(self.T, 20.0), np.full(self.T, 50.0)])
        kwargs = dict(
            wind_cf=np.zeros((1, self.T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, self.T)),
            solar_cap=np.zeros(1),
        )
        if budget_mmbtu is not None:
            budget = np.full((1, 12), np.inf)
            budget[0, 0] = budget_mmbtu  # month 0 — every T=24 hour maps here
            kwargs.update(
                coal_monthly_budget=budget,
                coal_gen_idx=np.array([0]),
                coal_month_index=np.zeros(self.T, dtype=int),
                coal_gen_hour_coeff=np.array([10.0]),
                coal_group_index=np.array([0]),
            )
        return solve_dispatch(fleet, demand, mc=mc, T=self.T, **kwargs)

    def test_unconstrained_coal_serves_everything_at_its_own_mc(self):
        result = self._solve(None)
        self.assertAlmostEqual(float(result.dispatch[0].sum()), 1200.0, places=3)
        np.testing.assert_allclose(result.prices, 20.0)

    def test_binding_budget_caps_coal_ENERGY_INPUT_and_gas_backfills(self):
        # Cap coal at 6,000 MMBtu over the month. The coefficient is the HEAT
        # RATE, so that is 600 MWh of coal against the 1,200 MWh it wants —
        # which is the whole point of budgeting MMBtu rather than MWh.
        result = self._solve(6_000.0)
        self.assertLessEqual(float(result.dispatch[0].sum()), 600.0 + 1e-6)
        # Load is still served: gas covers the displaced 600 MWh.
        self.assertAlmostEqual(float(result.dispatch.sum()), 1200.0, places=3)
        # The binding dual re-prices the market at the backfill unit's cost.
        np.testing.assert_allclose(result.prices, 50.0, atol=1e-6)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
