"""Nuclear winter-capability basis (closeout-PJM-w3): pmax -> EIA-860 winter, unclipped CF.

Trivial two-reactor fleet against a synthetic operable sheet, so every number is
hand-checkable: re-rating, the W0 nameplate cap, energy conservation in months
below the summer rating, the unclipped winter months, dormancy, and byte-identity
off / other ISO / other years.
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from market_sim.config import paths
from market_sim.config.constants import NUCLEAR_MONTHLY_CF_UNCLIPPED_BY_YEAR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet.arrays import _apply_nuclear_winter_basis

HOURS = 8760
JAN = slice(0, 744)
APR = slice(2160, 2880)


@pytest.fixture
def operable(tmp_path, monkeypatch):
    """Two reactors: A winter 1030 (plate 1050), B winter 1100 capped at plate 1020."""
    pd.DataFrame(
        {
            "Plant Code": [1, 2],
            "Generator ID": ["1", "1"],
            "Nameplate Capacity (MW)": [1050.0, 1020.0],
            "Winter Capacity (MW)": [1030.0, 1100.0],
        }
    ).to_parquet(tmp_path / "eia860_generator_operable.parquet")
    monkeypatch.setattr(paths, "active_eia860_dir", lambda: tmp_path)
    return tmp_path


def _fleet():
    gens = [
        SimpleNamespace(fuel_type="nuclear", plant_code=1, unit_id="1_1"),
        SimpleNamespace(fuel_type="nuclear", plant_code=2, unit_id="2_1"),
        SimpleNamespace(fuel_type="gas_cc", plant_code=3, unit_id="3_1"),
    ]
    pmax = np.array([1000.0, 1000.0, 500.0])
    cf = np.asarray(NUCLEAR_MONTHLY_CF_UNCLIPPED_BY_YEAR["PJM"][2022])
    from market_sim.data.fleet.models import _hour_to_month_index

    avail = np.ones((3, HOURS))
    avail[:2] = np.minimum(cf, 1.0)[_hour_to_month_index(HOURS)]
    return gens, pmax, avail


def test_rerates_to_winter_with_the_nameplate_cap(operable):
    gens, pmax, avail = _fleet()
    _apply_nuclear_winter_basis(gens, pmax, avail, HOURS, "PJM", 2022)
    assert pmax.tolist() == [1030.0, 1020.0, 500.0]


def test_energy_conserved_below_summer_and_unclipped_in_january(operable):
    gens, pmax, avail = _fleet()
    before = (pmax[:2, None] * avail[:2]).copy()
    _apply_nuclear_winter_basis(gens, pmax, avail, HOURS, "PJM", 2022)
    after = pmax[:2, None] * avail[:2]
    np.testing.assert_allclose(after[:, APR], before[:, APR])  # Apr CF 0.822 < 1
    cf_jan = NUCLEAR_MONTHLY_CF_UNCLIPPED_BY_YEAR["PJM"][2022][0]
    np.testing.assert_allclose(
        after[0, JAN], 1000.0 * cf_jan
    )  # A: 1027 MW fits under 1030
    np.testing.assert_allclose(
        after[1, JAN], 1020.0
    )  # B: stops at its 1020 MW winter cap
    assert (after[:, JAN] > before[:, JAN]).all()


def test_zero_stays_zero_and_non_nuclear_untouched(operable):
    gens, pmax, avail = _fleet()
    avail[1, :] = 0.0  # dormant reactor
    _apply_nuclear_winter_basis(gens, pmax, avail, HOURS, "PJM", 2022)
    assert (avail[1] == 0.0).all()
    assert (avail[2] == 1.0).all() and pmax[2] == 500.0


def test_year_without_rows_is_a_noop(operable):
    gens, pmax, avail = _fleet()
    p0, a0 = pmax.copy(), avail.copy()
    _apply_nuclear_winter_basis(gens, pmax, avail, HOURS, "PJM", 2018)
    assert (pmax == p0).all() and (avail == a0).all()


def test_field_default_off_and_forecast_refused():
    assert ScenarioConfig().nuclear_winter_capability_basis is False
    with pytest.raises(ValueError, match="backcast-only measured overlays"):
        ScenarioConfig(mode="forecast", nuclear_winter_capability_basis=True)
    base = ScenarioConfig(mode="backcast")
    on = ScenarioConfig(mode="backcast", nuclear_winter_capability_basis=True)
    assert on.cache_key() != base.cache_key()
