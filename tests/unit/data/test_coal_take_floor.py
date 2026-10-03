"""Tests for the per-coal-yard TAKE floor (NWPP-NEXT-7, coal_fuel_inventory_take_floor).

Trivial-first: the estimator-B-net arithmetic on hand-written clean data, the
two feasibility clips, the no-substitute rule, an end-to-end 1-zone LP where the
floor forces dear coal ahead of cheap gas, and the orchestrator gate.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.coal_fuel_inventory import (  # noqa: E402
    build_coal_plant_budget,
    build_coal_take_floor,
)
from market_sim.model.dispatch import solve_dispatch  # noqa: E402
from scripts.lib.clean_io import write_clean  # noqa: E402
from scripts.run_calibration import resolve_coal_take_floor  # noqa: E402
from tests.helpers.base import CleanDirTestCase  # noqa: E402
from tests.unit.data.test_coal_fuel_inventory import (  # noqa: E402
    _HOURS,
    _coal_fleet,
    _receipt_row,
    _stock_row,
)


def _spot(plant_id, year, month, tons):
    row = _receipt_row(plant_id, year, month, tons)
    row["purchase_type"] = "S"
    return row


class TakeFloorArithmeticTest(CleanDirTestCase):
    """Plant 1: 1,000 t contract + 500 t spot in 2021, Dec stock 300, max stock 400.

    B net = max(0, 1000 + 300 - 400) * 20 MMBtu/t = 18,000 MMBtu (spot excluded).
    Plant 2 files receipts but no stock record: no floor (never substituted).
    """

    def setUp(self):
        super().setUp()
        self.ref = self.tmp_path / "reference"
        self.ref.mkdir(parents=True, exist_ok=True)
        (self.ref / "coal-shared-storage-crosswalk.csv").write_text(
            "storage_plant_id,storage_plant_name,served_plant_ids,iso,source\n",
            encoding="utf-8",
        )
        write_clean(
            pd.DataFrame([_stock_row(1, 2020, 6, 400), _stock_row(1, 2020, 12, 350)]),
            "coal-stocks",
            year=2020,
            source="test",
        )
        write_clean(
            pd.DataFrame([_stock_row(1, 2021, 12, 300)]),
            "coal-stocks",
            year=2021,
            source="test",
        )
        write_clean(
            pd.DataFrame([_stock_row(1, 2022, 12, 999_999)]),
            "coal-stocks",
            year=2022,
            source="test",
        )
        write_clean(
            pd.DataFrame([_receipt_row(1, 2020, 1, 900), _receipt_row(2, 2020, 1, 50)]),
            "coal-receipts",
            year=2020,
            source="test",
        )
        write_clean(
            pd.DataFrame(
                [
                    _receipt_row(1, 2021, 1, 1000),
                    _spot(1, 2021, 2, 500),
                    _receipt_row(2, 2021, 1, 50),
                ]
            ),
            "coal-receipts",
            year=2021,
            source="test",
        )
        write_clean(
            pd.DataFrame([_receipt_row(1, 2022, 1, 999_999)]),
            "coal-receipts",
            year=2022,
            source="test",
        )

    def _build(self, pmax=100.0):
        fleet = _coal_fleet([1, 2], pmax=pmax)
        g, budget, _mi, coeff, grp, prov = build_coal_plant_budget(
            fleet, 2022, hours=_HOURS, reference_dir=self.ref
        )
        floor, tf = build_coal_take_floor(
            fleet, 2022, g, grp, coeff, budget, prov.yard_keys, reference_dir=self.ref
        )
        return budget, floor, tf, prov

    def test_estimator_b_net_uses_contract_tons_only_and_prior_years(self):
        budget, floor, tf, prov = self._build(pmax=1e6)
        i1 = prov.yard_keys.index(1)
        i2 = prov.yard_keys.index(2)
        self.assertAlmostEqual(float(floor[i1, 0]), 18_000.0)
        self.assertEqual(float(floor[i2, 0]), 0.0)  # no stock record: no floor
        self.assertEqual(tf.n_binding_rows, 1)
        self.assertLessEqual(float(floor[i1, 0]), float(budget[i1, 0]))

    def test_floor_clipped_to_what_the_units_can_burn(self):
        # 1 MW x 24 h x HR 10 = 240 MMBtu of physical capability.
        _budget, floor, tf, prov = self._build(pmax=1.0)
        self.assertAlmostEqual(float(floor[prov.yard_keys.index(1), 0]), 240.0)
        self.assertEqual(tf.clipped_to_capacity, 1)


def test_floor_forces_dear_coal_ahead_of_cheap_gas():
    """A 1,200 MWh take on coal (MC 40) displaces gas (MC 30) from the LP."""
    T = 24
    fleet = _coal_fleet([1], heat_rate=10.0, pmax=100.0, hours=T)
    demand = np.full((1, T), 100.0)
    mc = np.vstack([np.full(T, 40.0), np.full(T, 30.0)])
    base = dict(
        wind_cf=np.zeros((1, T)),
        wind_cap=np.zeros(1),
        solar_cf=np.zeros((1, T)),
        solar_cap=np.zeros(1),
        coal_plant_budget=np.array([[1e9]]),
        coal_plant_gen_idx=np.array([0]),
        coal_plant_month_index=np.zeros(T, dtype=int),
        coal_plant_gen_hour_coeff=np.array([10.0]),
        coal_plant_group_index=np.array([0]),
    )
    r0 = solve_dispatch(fleet, demand, mc=mc, T=T, **base)
    assert float(r0.dispatch[0].sum()) == pytest.approx(0.0, abs=1e-6)
    r1 = solve_dispatch(
        fleet, demand, mc=mc, T=T, coal_plant_floor=np.array([[12_000.0]]), **base
    )
    assert float(r1.dispatch[0].sum()) == pytest.approx(1200.0, abs=1e-4)
    assert float(r1.dispatch[1].sum()) == pytest.approx(1200.0, abs=1e-4)


def _cfg(**kw) -> ScenarioConfig:
    return ScenarioConfig(mode="backcast").with_overrides(**kw)


def test_gate_default_off():
    assert resolve_coal_take_floor(_cfg(), "NWPP", True) is False


def test_gate_arms_for_nwpp_without_the_per_hour_discounts():
    assert resolve_coal_take_floor(
        _cfg(coal_fuel_inventory_take_floor=True), "NWPP", True
    )


def test_gate_requires_the_yard_rows():
    with pytest.raises(ValueError, match="requires coal_fuel_inventory_plant_grain"):
        resolve_coal_take_floor(
            _cfg(coal_fuel_inventory_take_floor=True), "NWPP", False
        )


def test_gate_refuses_other_isos():
    with pytest.raises(ValueError, match="R-ISO-SCOPE"):
        resolve_coal_take_floor(_cfg(coal_fuel_inventory_take_floor=True), "MISO", True)


def test_gate_arms_soco_only_in_the_measured_monthly_pile_form():
    """R-49: SOCO's take floor rides only with the same-year measured pile."""
    armed = _cfg(
        coal_fuel_inventory_take_floor=True,
        coal_fuel_inventory_monthly_pile=True,
        coal_monthly_pile_measured_receipts=True,
    )
    assert resolve_coal_take_floor(armed, "SOCO", True)
    for partial in (
        _cfg(coal_fuel_inventory_take_floor=True),
        _cfg(
            coal_fuel_inventory_take_floor=True, coal_fuel_inventory_monthly_pile=True
        ),
    ):
        with pytest.raises(ValueError, match="R-49"):
            resolve_coal_take_floor(partial, "SOCO", True)


def test_gate_refuses_stacking_on_the_take_or_pay_discounts():
    cfg = _cfg(coal_fuel_inventory_take_floor=True, coal_takeorpay_from_data=True)
    with pytest.raises(ValueError, match="REPLACES"):
        resolve_coal_take_floor(cfg, "NWPP", True)


def test_cache_key_unchanged_off_and_distinct_armed():
    base = ScenarioConfig()
    assert (
        base.cache_key()
        == ScenarioConfig(coal_fuel_inventory_take_floor=False).cache_key()
    )
    assert (
        base.cache_key()
        != ScenarioConfig(coal_fuel_inventory_take_floor=True).cache_key()
    )


def test_soft_floor_unreachable_take_is_paid_not_infeasible():
    """A take above what the unit can burn stays feasible; the shortfall is paid.

    Coal (MC 40, HR 10) can burn at most 100 MW x 24 h = 24,000 MMBtu; the take
    is 30,000. With a $2/MMBtu shortfall price the LP runs the coal flat out
    (burning is cheaper than paying for coal plus buying gas) and pays 6,000.
    """
    T = 24
    fleet = _coal_fleet([1], heat_rate=10.0, pmax=100.0, hours=T)
    demand = np.full((1, T), 100.0)
    mc = np.vstack([np.full(T, 40.0), np.full(T, 30.0)])
    base = dict(
        wind_cf=np.zeros((1, T)),
        wind_cap=np.zeros(1),
        solar_cf=np.zeros((1, T)),
        solar_cap=np.zeros(1),
        coal_plant_budget=np.array([[1e9]]),
        coal_plant_gen_idx=np.array([0]),
        coal_plant_month_index=np.zeros(T, dtype=int),
        coal_plant_gen_hour_coeff=np.array([10.0]),
        coal_plant_group_index=np.array([0]),
    )
    r = solve_dispatch(
        fleet,
        demand,
        mc=mc,
        T=T,
        coal_plant_floor=np.array([[30_000.0]]),
        coal_plant_floor_price=np.array([2.0]),
        **base,
    )
    assert float(r.dispatch[0].sum()) == pytest.approx(2400.0, abs=1e-4)


def test_soft_floor_price_caps_the_take_or_pay_value():
    """Shortfall price $0.5/MMBtu (=$5/MWh at HR 10): dear coal (MC 40) is NOT run
    against gas (MC 30), because paying the take costs less than the $10/MWh gap."""
    T = 24
    fleet = _coal_fleet([1], heat_rate=10.0, pmax=100.0, hours=T)
    demand = np.full((1, T), 100.0)
    mc = np.vstack([np.full(T, 40.0), np.full(T, 30.0)])
    r = solve_dispatch(
        fleet,
        demand,
        mc=mc,
        T=T,
        wind_cf=np.zeros((1, T)),
        wind_cap=np.zeros(1),
        solar_cf=np.zeros((1, T)),
        solar_cap=np.zeros(1),
        coal_plant_budget=np.array([[1e9]]),
        coal_plant_gen_idx=np.array([0]),
        coal_plant_month_index=np.zeros(T, dtype=int),
        coal_plant_gen_hour_coeff=np.array([10.0]),
        coal_plant_group_index=np.array([0]),
        coal_plant_floor=np.array([[12_000.0]]),
        coal_plant_floor_price=np.array([0.5]),
    )
    assert float(r.dispatch[0].sum()) == pytest.approx(0.0, abs=1e-4)


def test_shortfall_price_is_capability_weighted_model_fuel_price():
    from market_sim.data.coal_fuel_inventory import coal_take_shortfall_price

    fleet = _coal_fleet([1, 2], heat_rate=10.0, pmax=100.0)
    fp = np.vstack([np.full(_HOURS, 2.0), np.full(_HOURS, 4.0), np.full(_HOURS, 3.0)])
    p = coal_take_shortfall_price(
        fp, fleet, np.array([0, 1]), np.array([0, 0]), np.array([10.0, 10.0]), 1
    )
    assert p.tolist() == [3.0]
