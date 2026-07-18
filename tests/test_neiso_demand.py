"""Tests for NEISO demand loading and zonal load-share derivation.

Covers:
- Static zone shares sum to 1.0 (validates the Tier-3 RSP seed)
- load_demand("NEISO", year) shape, no-NaN, positive peak
- Zonal demand reconciles to the system series (shares sum to 1 every hour)
- neiso_zonal_load_shares returns None when U3 file is absent (fallback path)
- neiso_zonal_load_shares produces valid shares from a synthetic U3 CSV
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.data.eia_loader import (
    _load_neiso_hourly_demand,
    load_demand,
)
from scripts.data.curate_zonal_shares import (
    parse_neiso_shares as neiso_zonal_load_shares,
)

_TEST_YEAR = 2024

# ISO-NE ISNE system peak is roughly 22–27 GW (EIA-930 2023–2025).
_NEISO_PEAK_RANGE = (18_000.0, 30_000.0)


# ---------------------------------------------------------------------------
# Static configuration checks
# ---------------------------------------------------------------------------


def test_neiso_static_load_shares_sum_to_one():
    """The four NEISO load zones plus HQ_import share must sum to 1.0."""
    neiso = get_iso_config("NEISO")
    total = sum(zone.load_share for zone in neiso.zones)
    assert abs(total - 1.0) < 1e-9


def test_neiso_static_shares_cover_four_load_zones():
    """North/Central/Boston/Connecticut each carry positive load; HQ_import zero."""
    neiso = get_iso_config("NEISO")
    load_zones = {z.name: z.load_share for z in neiso.zones}
    for name in ("North", "Central", "Boston", "Connecticut"):
        assert load_zones[name] > 0.0, f"{name} should have positive load_share"
    assert load_zones["HQ_import"] == 0.0


# ---------------------------------------------------------------------------
# System demand loading
# ---------------------------------------------------------------------------


def test_neiso_demand_shape():
    """load_demand returns (n_zones, HOURS_PER_YEAR) for NEISO."""
    neiso = get_iso_config("NEISO")
    demand = load_demand("NEISO", _TEST_YEAR, neiso)
    assert demand.shape == (neiso.n_zones, HOURS_PER_YEAR)


def test_neiso_demand_no_nan():
    """NEISO demand contains no NaN values."""
    demand = load_demand("NEISO", _TEST_YEAR)
    assert not np.isnan(demand).any()


def test_neiso_demand_positive_peak():
    """NEISO system peak (summed across zones) is in the expected MW band."""
    demand = load_demand("NEISO", _TEST_YEAR)
    peak = demand.sum(axis=0).max()
    assert _NEISO_PEAK_RANGE[0] <= peak <= _NEISO_PEAK_RANGE[1], (
        f"NEISO peak {peak:.0f} MW outside [{_NEISO_PEAK_RANGE[0]:.0f}, "
        f"{_NEISO_PEAK_RANGE[1]:.0f}]"
    )


def test_neiso_demand_hq_import_carries_no_load():
    """The HQ_import zone has zero demand in every hour (it is supply, not load)."""
    neiso = get_iso_config("NEISO")
    demand = load_demand("NEISO", _TEST_YEAR, neiso)
    hq_idx = neiso.zone_names.index("HQ_import")
    assert np.all(demand[hq_idx] == 0.0)


# ---------------------------------------------------------------------------
# Zonal reconciliation (shares sum to 1 → zone sum = system series)
# ---------------------------------------------------------------------------


def test_neiso_zonal_demand_reconciles_to_system_series():
    """Zonal demand sums back to the ISNE system demand every hour.

    With the static share fallback (U3 absent), each zone row is a constant
    fraction of the system series so the sum is exact to floating-point.
    Interchange is disabled so the reconciliation isolates the zonal split;
    NEISO now serves the measured net-interchange schedule by default (a
    net-import wedge that otherwise shifts the system total).
    """
    neiso = get_iso_config("NEISO")
    demand = load_demand("NEISO", _TEST_YEAR, neiso, include_interchange=False)
    system = _load_neiso_hourly_demand(_TEST_YEAR)
    if system is None:
        pytest.skip("ISNE hourly parquet not available for year")
    np.testing.assert_allclose(demand.sum(axis=0), system, rtol=1e-9)


def test_neiso_demand_uses_static_share_split_without_zonal_file():
    """Without a zonal U3 file the zones are constant multiples of each other.

    Every non-zero zone row is proportional to the system series, so the
    ratio zone[i] / zone[j] is the same constant every hour.
    """
    neiso = get_iso_config("NEISO")
    demand = load_demand("NEISO", _TEST_YEAR, neiso)
    # Collect non-zero zones (HQ_import is excluded).
    nonzero = [
        (i, z.load_share) for i, z in enumerate(neiso.zones) if z.load_share > 0.0
    ]
    # All non-zero zones should be constant multiples of the first.
    ref_row = demand[nonzero[0][0]] / nonzero[0][1]
    for idx, share in nonzero:
        np.testing.assert_allclose(demand[idx], share * ref_row, rtol=1e-9)


# ---------------------------------------------------------------------------
# neiso_zonal_load_shares — fallback and synthetic-file paths
# ---------------------------------------------------------------------------


def test_neiso_zonal_load_shares_absent_returns_none():
    """neiso_zonal_load_shares returns None when the U3 file is missing."""
    zone_names = get_iso_config("NEISO").zone_names
    result = neiso_zonal_load_shares(_TEST_YEAR, zone_names)
    assert result is None


def _build_synthetic_neiso_csv(path: Path, year: int) -> None:
    """Write a full-year ISO-NE SMD wide-format CSV for testing.

    Uses constant zone loads so the expected shares are deterministic:
    North (ME+NH+VT) = 1300 MW, Central (WCMASS+SEMASS+RI) = 2200 MW,
    Boston (NEMA) = 1500 MW, Connecticut (CT) = 3000 MW.
    System total = 8000 MW → shares 0.1625 / 0.275 / 0.1875 / 0.375.
    """
    import calendar

    rows = []
    for month in range(1, 13):
        _, days_in_month = calendar.monthrange(year, month)
        for day in range(1, days_in_month + 1):
            if month == 2 and day == 29:
                continue
            for he in range(1, 25):
                rows.append(
                    {
                        "Date": f"{month:02d}/{day:02d}/{year}",
                        "Hour Ending": he,
                        "CT": 3000.0,
                        "ME": 500.0,
                        "NH": 600.0,
                        "RI": 400.0,
                        "VT": 200.0,
                        "NEMA": 1500.0,
                        "SEMASS": 800.0,
                        "WCMASS": 1000.0,
                    }
                )
    pd.DataFrame(rows).to_csv(path, index=False)


def test_neiso_zonal_load_shares_sum_to_one_each_hour():
    """Measured NEISO shares partition system load to 1.0 in every hour."""
    zone_names = get_iso_config("NEISO").zone_names
    with tempfile.TemporaryDirectory() as tmp:
        neiso_dir = Path(tmp) / "NEISO"
        neiso_dir.mkdir()
        _build_synthetic_neiso_csv(
            neiso_dir / f"NEISO_load_hourly_{_TEST_YEAR}.csv", _TEST_YEAR
        )
        with mock.patch("scripts.data.curate_zonal_shares.ZONE_DEMAND_DIR", Path(tmp)):
            shares = neiso_zonal_load_shares(_TEST_YEAR, zone_names)

    assert shares is not None
    assert shares.shape == (len(zone_names), HOURS_PER_YEAR)
    np.testing.assert_allclose(shares.sum(axis=0), 1.0, atol=1e-9)


def test_neiso_zonal_load_shares_hq_import_is_zero():
    """HQ_import row in the shares matrix is all-zero (import node, not load)."""
    zone_names = get_iso_config("NEISO").zone_names
    with tempfile.TemporaryDirectory() as tmp:
        neiso_dir = Path(tmp) / "NEISO"
        neiso_dir.mkdir()
        _build_synthetic_neiso_csv(
            neiso_dir / f"NEISO_load_hourly_{_TEST_YEAR}.csv", _TEST_YEAR
        )
        with mock.patch("scripts.data.curate_zonal_shares.ZONE_DEMAND_DIR", Path(tmp)):
            shares = neiso_zonal_load_shares(_TEST_YEAR, zone_names)

    assert shares is not None
    hq_idx = zone_names.index("HQ_import")
    assert np.all(shares[hq_idx] == 0.0)


def test_neiso_zonal_load_shares_expected_values():
    """Shares derived from the synthetic CSV match the known constant values."""
    # With CT=3000, ME=500, NH=600, RI=400, VT=200, NEMA=1500, SEMASS=800,
    # WCMASS=1000; system=8000 MW:
    # North=1300 → 0.1625, Central=2200 → 0.275, Boston=1500 → 0.1875, CT=3000 → 0.375
    expected = {
        "North": 1300.0 / 8000.0,
        "Central": 2200.0 / 8000.0,
        "Boston": 1500.0 / 8000.0,
        "Connecticut": 3000.0 / 8000.0,
        "HQ_import": 0.0,
    }
    zone_names = get_iso_config("NEISO").zone_names
    with tempfile.TemporaryDirectory() as tmp:
        neiso_dir = Path(tmp) / "NEISO"
        neiso_dir.mkdir()
        _build_synthetic_neiso_csv(
            neiso_dir / f"NEISO_load_hourly_{_TEST_YEAR}.csv", _TEST_YEAR
        )
        with mock.patch("scripts.data.curate_zonal_shares.ZONE_DEMAND_DIR", Path(tmp)):
            shares = neiso_zonal_load_shares(_TEST_YEAR, zone_names)

    assert shares is not None
    for zone, exp_share in expected.items():
        idx = zone_names.index(zone)
        np.testing.assert_allclose(
            shares[idx],
            exp_share,
            atol=1e-9,
            err_msg=f"{zone} share mismatch",
        )


def test_neiso_zonal_demand_reconciles_with_synthetic_file():
    """With a synthetic U3 file, zonal demand still sums to the system series.

    Interchange is disabled so the reconciliation isolates the zonal split
    (NEISO serves the measured net-interchange schedule by default).
    """
    neiso = get_iso_config("NEISO")
    system = _load_neiso_hourly_demand(_TEST_YEAR)
    if system is None:
        pytest.skip("ISNE hourly parquet not available for year")

    with tempfile.TemporaryDirectory() as tmp:
        neiso_dir = Path(tmp) / "NEISO"
        neiso_dir.mkdir()
        _build_synthetic_neiso_csv(
            neiso_dir / f"NEISO_load_hourly_{_TEST_YEAR}.csv", _TEST_YEAR
        )
        with mock.patch("scripts.data.curate_zonal_shares.ZONE_DEMAND_DIR", Path(tmp)):
            shares = neiso_zonal_load_shares(_TEST_YEAR, neiso.zone_names)

    assert shares is not None
    with mock.patch(
        "market_sim.data.eia_loader.load_zonal_shares", return_value=shares
    ):
        demand = load_demand("NEISO", _TEST_YEAR, neiso, include_interchange=False)

    np.testing.assert_allclose(demand.sum(axis=0), system, rtol=1e-9)
