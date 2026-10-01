"""Tests for the soco-96 measured oil-burn overlay (``dual_fuel_measured_oil_burn``).

Trivial cases first (one generator, 24 hours): the flag off is byte-identical,
a plant-day at f=1 prices at oil, f=0.5 at the midpoint, a plant with no rows
and a non-gas generator are untouched, forecast mode is refused / inert, the
dual-fuel switch leaves measured cells alone (rule 19), and the CAMPD mixing
identity maps the two Part 75 signatures to 0 and 1.
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from market_sim.config.constants import (
    CAMPD_CO2_SHORT_TONS_PER_MMBTU_GAS,
    CAMPD_CO2_SHORT_TONS_PER_MMBTU_OIL,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays
from market_sim.data.fuel import (
    apply_dual_fuel_pricing,
    apply_measured_oil_burn_pricing,
    load_measured_oil_burn_days,
    oil_heat_share_from_co2,
)

HOURS = 24
YEAR = 2023
GAS = 4.0
OIL = 20.0
PLANT = 6124


def _fleet(fuel: str = "gas_cc", plant: int = PLANT, group: str = "CC_REGULAR"):
    """One-generator fleet at *plant* burning *fuel*."""
    return FleetArrays(
        pmax=np.array([100.0]),
        pmin=np.array([0.0]),
        heat_rate=np.array([7.0]),
        vom=np.array([2.0]),
        emission_rate=np.array([0.05]),
        nox_rate=np.array([0.0]),
        so2_rate=np.array([0.0]),
        zone_idx=np.array([0]),
        fuel_type_idx=np.array([FUEL_TYPE_MAP[fuel]]),
        availability=np.ones((1, HOURS)),
        unit_ids=["U1"],
        efficiency_bin=np.array([0]),
        plant_code=np.array([plant]),
        plant_group=np.array([group]),
    )


def _cfg(on: bool = True, **kw) -> ScenarioConfig:
    return ScenarioConfig(
        iso="SOCO", mode="backcast", hours=HOURS, dual_fuel_measured_oil_burn=on, **kw
    )


def _artifact(tmp_path, share: float, date: str = "2023-01-01", plant: int = PLANT):
    path = tmp_path / "campd_measured_oil_burn_days_SOCO.csv"
    pd.DataFrame(
        {
            "iso": ["SOCO"],
            "year": [int(date[:4])],
            "plant_code": [plant],
            "date": [date],
            "oil_heat_share": [share],
        }
    ).to_csv(path, index=False)
    return path


@pytest.fixture(autouse=True)
def _flat_oil(monkeypatch):
    """Pin the delivered oil series to a flat OIL $/MMBtu."""
    monkeypatch.setattr(
        "market_sim.data.fuel.dual_fuel.dual_fuel_oil_price_series",
        lambda config, year, monthly_costs_path=None: np.full(config.hours, OIL),
    )


def test_off_is_byte_identical(tmp_path):
    path = _artifact(tmp_path, 1.0)
    prices = np.full((1, HOURS), GAS)
    before = prices.copy()
    out = apply_measured_oil_burn_pricing(
        prices, _fleet(), _cfg(False), YEAR, path=path
    )
    assert out is None
    np.testing.assert_array_equal(prices, before)


def test_full_oil_day_prices_at_oil(tmp_path):
    path = _artifact(tmp_path, 1.0)
    prices = np.full((1, HOURS), GAS)
    mask = apply_measured_oil_burn_pricing(prices, _fleet(), _cfg(), YEAR, path=path)
    np.testing.assert_allclose(prices[0], OIL)
    assert mask is not None and mask.all()


def test_half_share_is_midpoint(tmp_path):
    path = _artifact(tmp_path, 0.5)
    prices = np.full((1, HOURS), GAS)
    apply_measured_oil_burn_pricing(prices, _fleet(), _cfg(), YEAR, path=path)
    np.testing.assert_allclose(prices[0], 0.5 * (GAS + OIL))


def test_uncovered_day_untouched(tmp_path):
    path = _artifact(tmp_path, 1.0, date="2023-01-02")
    prices = np.full((1, 48), GAS)
    cfg = ScenarioConfig(
        iso="SOCO", mode="backcast", hours=48, dual_fuel_measured_oil_burn=True
    )
    apply_measured_oil_burn_pricing(prices, _fleet(), cfg, YEAR, path=path)
    np.testing.assert_allclose(prices[0, :24], GAS)
    np.testing.assert_allclose(prices[0, 24:], OIL)


def test_plant_without_rows_untouched(tmp_path):
    path = _artifact(tmp_path, 1.0, plant=999)
    prices = np.full((1, HOURS), GAS)
    out = apply_measured_oil_burn_pricing(prices, _fleet(), _cfg(), YEAR, path=path)
    assert out is None
    np.testing.assert_array_equal(prices, np.full((1, HOURS), GAS))


def test_non_gas_generator_untouched(tmp_path):
    path = _artifact(tmp_path, 1.0)
    prices = np.full((1, HOURS), 2.5)
    out = apply_measured_oil_burn_pricing(
        prices, _fleet(fuel="coal", group="COAL_BIT"), _cfg(), YEAR, path=path
    )
    assert out is None
    np.testing.assert_array_equal(prices, np.full((1, HOURS), 2.5))


def test_other_year_untouched(tmp_path):
    path = _artifact(tmp_path, 1.0)
    prices = np.full((1, HOURS), GAS)
    assert (
        apply_measured_oil_burn_pricing(prices, _fleet(), _cfg(), 2024, path=path)
        is None
    )
    np.testing.assert_array_equal(prices, np.full((1, HOURS), GAS))


def test_forecast_mode_refused_and_inert(tmp_path):
    # The config refuses it outright (backcast-only overlay family, rule 13) ...
    with pytest.raises(ValueError, match="dual_fuel_measured_oil_burn"):
        ScenarioConfig(iso="SOCO", mode="forecast", dual_fuel_measured_oil_burn=True)
    # ... and the applier is inert outside mode == "backcast" regardless.
    path = _artifact(tmp_path, 1.0)
    cfg = SimpleNamespace(
        dual_fuel_measured_oil_burn=True, mode="forecast", iso="SOCO", hours=HOURS
    )
    prices = np.full((1, HOURS), GAS)
    assert (
        apply_measured_oil_burn_pricing(prices, _fleet(), cfg, YEAR, path=path) is None
    )
    np.testing.assert_array_equal(prices, np.full((1, HOURS), GAS))


def test_measured_mix_replaces_dual_fuel_min(tmp_path, monkeypatch):
    """Rule 19: on a covered cell the switch must not re-cap the measured mix."""
    monkeypatch.setattr(
        "market_sim.data.fuel.dual_fuel_plant_groups",
        lambda: {(PLANT, "CC_REGULAR")},
    )
    path = _artifact(tmp_path, 0.5)
    gas_spike = 30.0  # above oil parity, so min(gas, oil) would read OIL
    cfg = _cfg(dual_fuel_switching=True)
    prices = np.full((1, HOURS), gas_spike)
    mask = apply_measured_oil_burn_pricing(prices, _fleet(), cfg, YEAR, path=path)
    apply_dual_fuel_pricing(prices, _fleet(), cfg, YEAR, skip_cells=mask)
    np.testing.assert_allclose(prices[0], 0.5 * (gas_spike + OIL))
    # Without skip_cells the pre-existing switch still caps (unchanged path).
    capped = np.full((1, HOURS), gas_spike)
    apply_dual_fuel_pricing(capped, _fleet(), cfg, YEAR)
    np.testing.assert_allclose(capped[0], OIL)


def test_leap_year_drops_feb29(tmp_path):
    path = tmp_path / "leap.csv"
    pd.DataFrame(
        {
            "iso": ["SOCO", "SOCO"],
            "year": [2024, 2024],
            "plant_code": [PLANT, PLANT],
            "date": ["2024-02-29", "2024-03-01"],
            "oil_heat_share": [0.9, 0.25],
        }
    ).to_csv(path, index=False)
    daily = load_measured_oil_burn_days("SOCO", 2024, path)[PLANT]
    assert daily.shape == (365,)
    assert daily[59] == pytest.approx(0.25)  # Mar 1 on the non-leap clock
    assert daily.max() == pytest.approx(0.25)  # Feb 29 dropped


def test_mixing_identity():
    hi = np.array([100.0, 100.0, 100.0, 100.0, 100.0, 0.0])
    mid = 0.5 * (
        CAMPD_CO2_SHORT_TONS_PER_MMBTU_GAS + CAMPD_CO2_SHORT_TONS_PER_MMBTU_OIL
    )
    r = np.array(
        [
            CAMPD_CO2_SHORT_TONS_PER_MMBTU_GAS,
            CAMPD_CO2_SHORT_TONS_PER_MMBTU_OIL,
            mid,
            0.03,  # below gas -> clipped to 0
            0.12,  # above oil -> clipped to 1
            0.06,  # zero heat input -> undefined
        ]
    )
    f = oil_heat_share_from_co2(r * hi, hi)
    np.testing.assert_allclose(f[:5], [0.0, 1.0, 0.5, 0.0, 1.0], atol=1e-12)
    assert np.isnan(f[5])


def test_part75_signatures_match_campd_booking():
    # 1,040 / 1,420 scf CO2 per MMBtu x 44.0 / 385 / 2000 (App. G Eq. G-4).
    assert CAMPD_CO2_SHORT_TONS_PER_MMBTU_GAS == pytest.approx(0.0594286, abs=1e-7)
    assert CAMPD_CO2_SHORT_TONS_PER_MMBTU_OIL == pytest.approx(0.0811429, abs=1e-7)


def _derive_module():
    import importlib.util
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[3]
        / "scripts"
        / "data"
        / "derive_measured_oil_burn_days.py"
    )
    spec = importlib.util.spec_from_file_location("_derive_oil_burn", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_coal_capable_unit_is_excluded():
    """A unit mapped to a generator with a coal Energy Source is excluded."""
    d = _derive_module()
    units = pd.DataFrame({"facilityId": [26, 26, 55], "unitId": ["1", "GT4", "CT1"]})
    crosswalk = pd.DataFrame(
        {
            "plant": [26, 26, 55],
            "unit": ["1", "GT4", "CT1"],
            "eia_plant": [26, 26, 55],
            "gen": ["1", "GT4", "CT1"],
            "boiler": ["1", "", ""],
        }
    )
    gens = {(26, "1")}  # e.g. NG primary with BIT as Energy Source 2
    boilers = {(26, "1")}
    excluded, how = d.coal_capable_units(units, gens, boilers, crosswalk)
    assert excluded == {(26, "1")}
    assert how["generator"] == 1
    # No crosswalk row: excluded only via a same-id coal-associated boiler.
    orphan = pd.DataFrame({"facilityId": [26, 26], "unitId": ["1", "9"]})
    excluded, how = d.coal_capable_units(orphan, gens, boilers, crosswalk.iloc[:0])
    assert excluded == {(26, "1")} and how["fallback_boiler"] == 1


def test_plant_day_symmetric_noise_around_gas_is_zero():
    """The identity on plant-day sums does not turn symmetric noise into oil."""
    d = _derive_module()
    hi = np.full(24, 1000.0)
    noise = np.tile([0.0005, -0.0005], 12)
    hours = pd.DataFrame(
        {
            "facilityId": 55,
            "unitId": "CT1",
            "date": pd.Timestamp("2022-01-01"),
            "hour": np.arange(24),
            "grossLoad": 100.0,
            "co2Mass": (CAMPD_CO2_SHORT_TONS_PER_MMBTU_GAS + noise) * hi,
            "heatInput": hi,
        }
    )
    out = d.plant_day_shares(hours)
    assert len(out) == 1
    assert out["oil_heat_share"].iloc[0] == pytest.approx(0.0, abs=1e-12)
    # The per-hour clip-then-average construction would have read ~0.0115.
    per_hour = np.nanmean(oil_heat_share_from_co2(hours.co2Mass, hours.heatInput))
    assert per_hour > 0.01
