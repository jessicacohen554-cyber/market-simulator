"""Tests for the ercot-231 N1a tie-zone interchange attribution.

``ercot_tie_zone_interchange`` places ERCOT's netted DC-tie interchange at
the tie-connected zones (constants.ERCOT_DC_TIE_ZONE_MAP) from the measured
EIA-930 BA-to-BA per-neighbor series, conserving the netted system total
exactly. Hermetic tests run on a synthetic by-neighbor extract in a tempdir;
the ``fulldata`` tests verify the same invariants on the real 2023 data.
"""

from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.data import eia_loader
from market_sim.data.eia930.demand import ercot_tie_zone_interchange, load_demand
from tests.helpers.base import requires_raw

_YEAR = 2023
_ZONES = get_iso_config("ERCOT").zone_names
_NB_PATH = Path("data/raw/eia-930-interchange/ERCO interchange hourly.parquet")


def _write_synthetic_nb(tmp: Path, swpp_mw: float, cen_mw: float) -> Path:
    """Write a flat synthetic ERCO by-neighbor extract under a raw-dir clone."""
    hourly_dir = tmp / "eia-930-hourly"
    hourly_dir.mkdir(parents=True, exist_ok=True)
    nb_dir = tmp / "eia-930-interchange"
    nb_dir.mkdir(parents=True, exist_ok=True)
    stamps = pd.date_range(f"{_YEAR}-01-01 01:00:00", periods=HOURS_PER_YEAR, freq="h")
    frame = pd.concat(
        [
            pd.DataFrame({"diba": diba, "mw": np.float32(mw), "local_time": stamps})
            for diba, mw in (("SWPP", swpp_mw), ("CEN", cen_mw))
        ],
        ignore_index=True,
    )
    frame.to_parquet(nb_dir / "ERCO interchange hourly.parquet")
    return hourly_dir


def test_tie_zone_matrix_conserves_total_and_places_flows(tmp_path):
    """Column sums equal the netted total; flows land on the tie zones."""
    hourly_dir = _write_synthetic_nb(tmp_path, swpp_mw=-820.0, cen_mw=100.0)
    interchange = np.full(HOURS_PER_YEAR, -720.0)  # matches SWPP+CEN
    weights = np.full((len(_ZONES), HOURS_PER_YEAR), 1.0 / len(_ZONES))
    with mock.patch.object(eia_loader, "EIA_HOURLY_DIR", hourly_dir):
        m = ercot_tie_zone_interchange(_YEAR, _ZONES, interchange, weights)
    assert m is not None
    np.testing.assert_allclose(m.sum(axis=0), interchange, atol=1e-9)
    z = {name: i for i, name in enumerate(_ZONES)}
    # SWPP -820 splits 600/820 Northeast, 220/820 North; CEN +100 on South.
    np.testing.assert_allclose(m[z["Northeast"]], -600.0, atol=1e-9)
    np.testing.assert_allclose(m[z["North"]], -220.0, atol=1e-9)
    np.testing.assert_allclose(m[z["South"]], 100.0, atol=1e-9)
    for name in ("West", "Panhandle", "Houston", "South_Central"):
        np.testing.assert_allclose(m[z[name]], 0.0, atol=1e-9)


def test_tie_zone_residual_rides_the_demand_weights(tmp_path):
    """A by-neighbor/total residual is spread by the caller's weights."""
    hourly_dir = _write_synthetic_nb(tmp_path, swpp_mw=-800.0, cen_mw=0.0)
    interchange = np.full(HOURS_PER_YEAR, -810.0)  # 10 MW residual
    weights = np.zeros((len(_ZONES), HOURS_PER_YEAR))
    weights[_ZONES.index("Houston")] = 1.0  # all residual to Houston
    with mock.patch.object(eia_loader, "EIA_HOURLY_DIR", hourly_dir):
        m = ercot_tie_zone_interchange(_YEAR, _ZONES, interchange, weights)
    assert m is not None
    np.testing.assert_allclose(m.sum(axis=0), interchange, atol=1e-9)
    np.testing.assert_allclose(m[_ZONES.index("Houston")], -10.0, atol=1e-9)


def test_tie_zone_matrix_absent_file_returns_none(tmp_path):
    """No by-neighbor extract (e.g. a forecast year) -> None -> spread."""
    hourly_dir = tmp_path / "eia-930-hourly"
    hourly_dir.mkdir(parents=True)
    (tmp_path / "eia-930-interchange").mkdir()
    interchange = np.zeros(HOURS_PER_YEAR)
    weights = np.full((len(_ZONES), HOURS_PER_YEAR), 1.0 / len(_ZONES))
    with mock.patch.object(eia_loader, "EIA_HOURLY_DIR", hourly_dir):
        assert ercot_tie_zone_interchange(_YEAR, _ZONES, interchange, weights) is None


def test_tie_zone_matrix_short_year_returns_none(tmp_path):
    """A partial-year by-neighbor slice refuses attribution (no silent pad)."""
    hourly_dir = tmp_path / "eia-930-hourly"
    hourly_dir.mkdir(parents=True)
    nb_dir = tmp_path / "eia-930-interchange"
    nb_dir.mkdir()
    stamps = pd.date_range(f"{_YEAR}-01-01 01:00:00", periods=1000, freq="h")
    pd.DataFrame(
        {"diba": "SWPP", "mw": np.float32(-100.0), "local_time": stamps}
    ).to_parquet(nb_dir / "ERCO interchange hourly.parquet")
    interchange = np.zeros(HOURS_PER_YEAR)
    weights = np.full((len(_ZONES), HOURS_PER_YEAR), 1.0 / len(_ZONES))
    with mock.patch.object(eia_loader, "EIA_HOURLY_DIR", hourly_dir):
        assert ercot_tie_zone_interchange(_YEAR, _ZONES, interchange, weights) is None


@requires_raw(_NB_PATH, "data/raw/eia-930-hourly/ERCO hourly.parquet")
def test_flag_moves_placement_never_the_system_total():
    """On real 2023 data the armed flag re-places, never re-sizes, demand."""
    ercot = get_iso_config("ERCOT")
    base = load_demand("ERCOT", _YEAR, ercot)
    armed = load_demand("ERCOT", _YEAR, ercot, ercot_tie_zonal_interchange=True)
    # System total identical to numerical noise: placement only.
    np.testing.assert_allclose(armed.sum(axis=0), base.sum(axis=0), rtol=0, atol=1e-6)
    # And the placement genuinely moved MW onto the tie zones.
    z = {name: i for i, name in enumerate(_ZONES)}
    delta = armed - base
    assert np.abs(delta[z["Northeast"]]).max() > 50.0
    assert np.abs(delta).max() < 2000.0  # bounded by the tie capability


def test_tie_zone_matrix_leap_year_drops_feb29(tmp_path):
    """A leap-year extract (8,784 hour-ending rows) attributes after Feb-29 excision."""
    year = 2024
    hourly_dir = tmp_path / "eia-930-hourly"
    hourly_dir.mkdir(parents=True)
    nb_dir = tmp_path / "eia-930-interchange"
    nb_dir.mkdir()
    stamps = pd.date_range(f"{year}-01-01 01:00:00", periods=8784, freq="h")
    frame = pd.concat(
        [
            pd.DataFrame({"diba": d, "mw": np.float32(mw), "local_time": stamps})
            for d, mw in (("SWPP", -820.0), ("CEN", 0.0))
        ],
        ignore_index=True,
    )
    frame.to_parquet(nb_dir / "ERCO interchange hourly.parquet")
    interchange = np.full(HOURS_PER_YEAR, -820.0)
    weights = np.full((len(_ZONES), HOURS_PER_YEAR), 1.0 / len(_ZONES))
    with mock.patch.object(eia_loader, "EIA_HOURLY_DIR", hourly_dir):
        m = ercot_tie_zone_interchange(year, _ZONES, interchange, weights)
    assert m is not None
    np.testing.assert_allclose(m.sum(axis=0), interchange, atol=1e-9)
    np.testing.assert_allclose(m[_ZONES.index("Northeast")], -600.0, atol=1e-9)
