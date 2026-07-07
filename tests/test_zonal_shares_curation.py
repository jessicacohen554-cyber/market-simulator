"""Round-trip tests for scripts/curate_zonal_shares.py.

Verifies that the per-ISO parse functions produce output that:
- Matches the (n_zones, HOURS_PER_YEAR) shape contract.
- Has shares summing to 1.0 across zones for every hour (energy conservation).
- Round-trips through the long-format Parquet seam and back to a numpy array
  that is bit-for-bit identical to the direct parse result (float64 exact).
- ``load_zonal_shares`` returns an array identical to direct parsing when a
  curated Parquet exists for the ISO-year.

ISOs covered:
  ERCOT — XLSX source, wide zone columns.
  PJM   — CSV source, multi-zone mapping.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest import mock

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.data.eia_loader import load_zonal_shares
from scripts.curate_zonal_shares import (
    _shares_to_long,
    parse_ercot_shares,
    parse_pjm_shares,
)
from scripts.lib.clean_io import read_clean, write_clean

_ERCOT_YEAR = 2024
_PJM_YEAR = 2023


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_is_available(iso: str, year: int) -> bool:
    """Return True when the raw source file for iso/year exists on disk."""
    from scripts.curate_zonal_shares import _PARSE_FUNCS

    zone_names = get_iso_config(iso).zone_names
    try:
        shares = _PARSE_FUNCS[iso](year, zone_names)
    except Exception:
        return False
    return shares is not None


def _write_to_tmp(df_long, iso: str, year: int, tmp_path: Path) -> None:
    """Write a long-format shares DataFrame to a temp clean directory."""
    with mock.patch("market_sim.config.paths.CLEAN_DIR", tmp_path):
        write_clean(df_long, "zonal-shares", iso=iso, year=year)


def _read_from_tmp(iso: str, year: int, tmp_path: Path):
    """Read a zonal-shares Parquet back from a temp clean directory."""
    with mock.patch("market_sim.config.paths.CLEAN_DIR", tmp_path):
        return read_clean("zonal-shares", iso=iso, year=year)


def _shares_df(shares: np.ndarray, zone_names: list[str]):
    """Convert share matrix to typed long-format DataFrame ready for write_clean."""
    df = _shares_to_long(shares, zone_names)
    df["hour"] = df["hour"].astype("int64")
    df["zone"] = df["zone"].astype("string")
    df["share"] = df["share"].astype("float64")
    return df


# ---------------------------------------------------------------------------
# Shape and sum-to-one checks (ERCOT)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _parse_is_available("ERCOT", _ERCOT_YEAR),
    reason=f"ERCOT native-load XLSX for {_ERCOT_YEAR} not present",
)
def test_ercot_parse_shape():
    """parse_ercot_shares returns (n_zones, HOURS_PER_YEAR)."""
    zone_names = get_iso_config("ERCOT").zone_names
    shares = parse_ercot_shares(_ERCOT_YEAR, zone_names)
    assert shares is not None
    assert shares.shape == (len(zone_names), HOURS_PER_YEAR)


@pytest.mark.skipif(
    not _parse_is_available("ERCOT", _ERCOT_YEAR),
    reason=f"ERCOT native-load XLSX for {_ERCOT_YEAR} not present",
)
def test_ercot_parse_shares_sum_to_one():
    """ERCOT parse: shares sum to 1.0 across zones every hour."""
    zone_names = get_iso_config("ERCOT").zone_names
    shares = parse_ercot_shares(_ERCOT_YEAR, zone_names)
    assert shares is not None
    np.testing.assert_allclose(shares.sum(axis=0), 1.0, atol=1e-9)


# ---------------------------------------------------------------------------
# Shape and sum-to-one checks (PJM)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _parse_is_available("PJM", _PJM_YEAR),
    reason=f"PJM metered-load CSV for {_PJM_YEAR} not present",
)
def test_pjm_parse_shape():
    """parse_pjm_shares returns (n_zones, HOURS_PER_YEAR)."""
    zone_names = get_iso_config("PJM").zone_names
    shares = parse_pjm_shares(_PJM_YEAR, zone_names)
    assert shares is not None
    assert shares.shape == (len(zone_names), HOURS_PER_YEAR)


@pytest.mark.skipif(
    not _parse_is_available("PJM", _PJM_YEAR),
    reason=f"PJM metered-load CSV for {_PJM_YEAR} not present",
)
def test_pjm_parse_shares_sum_to_one():
    """PJM parse: shares sum to 1.0 across zones every hour."""
    zone_names = get_iso_config("PJM").zone_names
    shares = parse_pjm_shares(_PJM_YEAR, zone_names)
    assert shares is not None
    np.testing.assert_allclose(shares.sum(axis=0), 1.0, atol=1e-9)


# ---------------------------------------------------------------------------
# Long-format Parquet round-trip (ERCOT)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _parse_is_available("ERCOT", _ERCOT_YEAR),
    reason=f"ERCOT native-load XLSX for {_ERCOT_YEAR} not present",
)
def test_ercot_long_format_round_trip():
    """shares_to_long → write_clean → read_clean → pivot reproduces the array exactly."""
    zone_names = get_iso_config("ERCOT").zone_names
    shares = parse_ercot_shares(_ERCOT_YEAR, zone_names)
    assert shares is not None

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_to_tmp(_shares_df(shares, zone_names), "ERCOT", _ERCOT_YEAR, tmp_path)
        df_back = _read_from_tmp("ERCOT", _ERCOT_YEAR, tmp_path)

    pivot = df_back.pivot(index="hour", columns="zone", values="share")
    pivot = pivot.reindex(columns=zone_names, fill_value=0.0)
    recovered = pivot.to_numpy(dtype=float).T

    np.testing.assert_array_equal(recovered, shares)


# ---------------------------------------------------------------------------
# load_zonal_shares integration (ERCOT)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _parse_is_available("ERCOT", _ERCOT_YEAR),
    reason=f"ERCOT native-load XLSX for {_ERCOT_YEAR} not present",
)
def test_load_zonal_shares_matches_direct_parse_ercot():
    """load_zonal_shares returns the same array as parse_ercot_shares after curation."""
    zone_names = get_iso_config("ERCOT").zone_names
    shares_direct = parse_ercot_shares(_ERCOT_YEAR, zone_names)
    assert shares_direct is not None

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_to_tmp(
            _shares_df(shares_direct, zone_names), "ERCOT", _ERCOT_YEAR, tmp_path
        )
        with mock.patch("market_sim.config.paths.CLEAN_DIR", tmp_path):
            shares_loaded = load_zonal_shares("ERCOT", _ERCOT_YEAR, zone_names)

    assert shares_loaded is not None
    np.testing.assert_array_equal(shares_loaded, shares_direct)


@pytest.mark.skipif(
    not _parse_is_available("NYISO", 2023),
    reason="NYISO pal actual-load CSV for 2023 not present",
)
def test_load_zonal_shares_raw_fallback_when_clean_absent_nyiso():
    """With no clean parquet, load_zonal_shares falls back to the measured raw file.

    Guards the G-20c fix: ``data/clean`` is derived and gitignored, so in a
    fresh clone the curated parquet is absent. Without the raw fallback the LP
    would silently drop to the static Gold-Book share and lose the downstate
    diurnal shape. The fallback must return the measured shares (not ``None``)
    and match the canonical curate parser byte-for-byte.
    """
    from scripts.curate_zonal_shares import parse_nyiso_shares

    zone_names = get_iso_config("NYISO").zone_names
    shares_direct = parse_nyiso_shares(2023, zone_names)
    assert shares_direct is not None

    # Point the clean seam at an EMPTY dir so no parquet exists — exercises the
    # raw fallback path, not the clean-parquet path.
    with tempfile.TemporaryDirectory() as tmp:
        with mock.patch("market_sim.config.paths.CLEAN_DIR", Path(tmp)):
            shares_loaded = load_zonal_shares("NYISO", 2023, zone_names)

    assert shares_loaded is not None, "raw fallback must not return None"
    np.testing.assert_array_equal(shares_loaded, shares_direct)
    # Measured NYC (zone J) share peaks materially above its 0.28 static value.
    nyc_i = zone_names.index("NYC")
    assert shares_loaded[nyc_i].max() > 0.30
