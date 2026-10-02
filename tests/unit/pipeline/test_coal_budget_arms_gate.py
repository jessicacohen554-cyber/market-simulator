"""Tests for ``run_calibration.resolve_coal_budget_arms`` (neiso-117 gate lift).

The per-coal-yard ANNUAL rows (``coal_fuel_inventory_plant_grain``) arm alone
for NEISO without the pooled MONTHLY limb (``coal_fuel_inventory``), which
stays MISO-only; both stay backcast-only; MISO's two-limb recipe is unchanged.
"""

from __future__ import annotations

import pytest

from market_sim.config.scenarios import ScenarioConfig
from scripts.run_calibration import (
    COAL_PLANT_GRAIN_ISOS,
    resolve_coal_budget_arms,
    resolve_coal_measured_receipts,
    resolve_coal_monthly_pile,
)


def _cfg(**kw) -> ScenarioConfig:
    return ScenarioConfig(mode="backcast").with_overrides(**kw)


def test_default_arms_nothing():
    assert resolve_coal_budget_arms(_cfg(), "NEISO") == (False, False)


def test_neiso_arms_annual_yard_rows_alone():
    cfg = _cfg(coal_fuel_inventory_plant_grain=True)
    assert resolve_coal_budget_arms(cfg, "NEISO") == (False, True)


def test_miso_two_limb_recipe_unchanged():
    cfg = _cfg(coal_fuel_inventory=True, coal_fuel_inventory_plant_grain=True)
    assert resolve_coal_budget_arms(cfg, "MISO") == (True, True)


def test_pooled_monthly_limb_stays_miso_only():
    cfg = _cfg(coal_fuel_inventory=True)
    with pytest.raises(ValueError, match="MISO-gated"):
        resolve_coal_budget_arms(cfg, "NEISO")


@pytest.mark.parametrize("iso", ["PJM", "SPP"])
def test_yard_rows_refused_outside_their_isos(iso):
    assert iso not in COAL_PLANT_GRAIN_ISOS
    cfg = _cfg(coal_fuel_inventory_plant_grain=True)
    with pytest.raises(ValueError, match="R-ISO-SCOPE"):
        resolve_coal_budget_arms(cfg, iso)


def test_yard_rows_backcast_only():
    cfg = ScenarioConfig(mode="forecast").with_overrides(
        coal_fuel_inventory_plant_grain=True
    )
    with pytest.raises(ValueError, match="backcast-only"):
        resolve_coal_budget_arms(cfg, "NEISO")


def test_ercot_arms_ceiling_only_pile_with_measured_receipts():
    """closeout-L1: ERCOT arms the yard rows + monthly pile WITHOUT a take floor."""
    cfg = _cfg(
        coal_fuel_inventory_plant_grain=True,
        coal_fuel_inventory_monthly_pile=True,
        coal_monthly_pile_measured_receipts=True,
    )
    assert resolve_coal_budget_arms(cfg, "ERCOT") == (False, True)
    assert resolve_coal_monthly_pile(cfg, "ERCOT", floor_armed=False) is True
    assert resolve_coal_measured_receipts(cfg, "ERCOT", pile_armed=True) is True


@pytest.mark.parametrize("iso", ["NWPP", "MISO", "NEISO"])
def test_pile_without_take_floor_refused_outside_ceiling_isos(iso):
    cfg = _cfg(coal_fuel_inventory_monthly_pile=True)
    with pytest.raises(ValueError, match="requires coal_fuel_inventory_take_floor"):
        resolve_coal_monthly_pile(cfg, iso, floor_armed=False)


def test_ercot_pile_with_take_floor_still_refused():
    """The take floor stays NWPP's own evidence; ERCOT arms the ceiling only."""
    cfg = _cfg(coal_fuel_inventory_monthly_pile=True)
    with pytest.raises(ValueError, match="R-ISO-SCOPE"):
        resolve_coal_monthly_pile(cfg, "ERCOT", floor_armed=True)


def test_nwpp_floor_pile_unchanged():
    cfg = _cfg(coal_fuel_inventory_monthly_pile=True)
    assert resolve_coal_monthly_pile(cfg, "NWPP", floor_armed=True) is True
