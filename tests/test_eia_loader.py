"""Tests for the EIA-930 demand and generation loaders."""

import numpy as np
import pytest

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.data.eia_loader import (
    load_demand,
    load_demand_meta,
    load_generation_profiles,
)

_TEST_YEAR = 2024

# Reference peak demand bands (MW), from EIA-930: ERCOT ~85,544 MW,
# CAISO ~47,571 MW for 2024.
_ERCOT_PEAK_RANGE = (80_000.0, 90_000.0)
_CAISO_PEAK_RANGE = (45_000.0, 50_000.0)


def test_load_demand_ercot_shape():
    """ERCOT demand spans its four zones over a full year."""
    demand = load_demand("ERCOT", _TEST_YEAR)
    assert demand.shape == (4, HOURS_PER_YEAR)


def test_load_demand_caiso_shape_and_import_zone():
    """CAISO has two zones; the WECC_import node carries no load."""
    demand = load_demand("CAISO", _TEST_YEAR)
    assert demand.shape == (2, HOURS_PER_YEAR)
    assert np.all(demand[1] == 0.0)


def test_load_demand_no_nan():
    """Allocated zonal demand contains no NaN values."""
    for iso in ("ERCOT", "CAISO"):
        assert not np.isnan(load_demand(iso, _TEST_YEAR)).any()


def test_ercot_peak_in_reference_band():
    """ERCOT peak (summed across zones) matches the EIA reference."""
    demand = load_demand("ERCOT", _TEST_YEAR)
    peak = demand.sum(axis=0).max()
    assert _ERCOT_PEAK_RANGE[0] <= peak <= _ERCOT_PEAK_RANGE[1]


def test_caiso_peak_in_reference_band():
    """CAISO peak (summed across zones) matches the EIA reference."""
    demand = load_demand("CAISO", _TEST_YEAR)
    peak = demand.sum(axis=0).max()
    assert _CAISO_PEAK_RANGE[0] <= peak <= _CAISO_PEAK_RANGE[1]


def test_zone_rows_sum_to_total_iso_demand():
    """Zonal rows sum back to total ISO demand each hour."""
    iso_config = get_iso_config("ERCOT")
    demand = load_demand("ERCOT", _TEST_YEAR, iso_config)
    total_share = sum(zone.load_share for zone in iso_config.zones)
    meta = load_demand_meta("ERCOT", _TEST_YEAR)
    assert demand.sum(axis=0).max() == pytest.approx(
        meta["peak_mw"] * total_share
    )


def test_load_demand_meta_keys():
    """Demand metadata exposes the expected summary statistics."""
    meta = load_demand_meta("ERCOT", _TEST_YEAR)
    assert set(meta) == {"peak_mw", "min_mw", "avg_mw", "total_annual_mwh"}
    assert meta["peak_mw"] > meta["avg_mw"] > meta["min_mw"]


def test_load_generation_profiles_filtered():
    """Generation profiles are filtered to the requested ISO and year."""
    profiles = load_generation_profiles("ERCOT", _TEST_YEAR)
    assert not profiles.empty
    assert (profiles["iso"] == "ERCOT").all()
    assert (profiles["year"] == _TEST_YEAR).all()
