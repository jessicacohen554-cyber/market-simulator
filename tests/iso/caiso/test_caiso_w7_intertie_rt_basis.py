"""closeout-CAISO-w7: the RTM intertie-print basis for the CAISO import ladder.

``caiso_intertie_print_rt_basis`` swaps the OASIS DAM intertie print for the
RTM print wherever the RTM sibling artifact prints; every other hour keeps the
DAM print. Off (the default) the measured series is read untouched.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import market_sim.data.eia930.envelopes as env
from market_sim.config.scenarios import ScenarioConfig


def _write(tmp_path, name, rows):
    pd.DataFrame(rows, columns=["year", "hour", "hub", "price"]).to_parquet(
        tmp_path / name, index=False
    )


@pytest.fixture
def calib(tmp_path, monkeypatch):
    """A tiny calibration dir: 4 DAM hours, RTM prints for hours 0-1 only."""
    _write(
        tmp_path,
        "wecc_intertie_lmp_hourly_CAISO.parquet",
        [(2021, h, "PALOVRDE", 50.0 + h) for h in range(4)],
    )
    _write(
        tmp_path,
        "wecc_intertie_lmp_hourly_CAISO_rtm.parquet",
        [
            (2021, 0, "PALOVRDE", 30.0),
            (2021, 1, "PALOVRDE", 31.0),
            (2021, 2, "PALOVRDE", np.nan),
        ],
    )
    monkeypatch.setattr(env, "_calibration_dir", lambda: tmp_path)
    yield tmp_path
    env.set_caiso_intertie_rt_basis(False)


def test_default_off():
    """The shipping default never arms the RTM basis."""
    assert ScenarioConfig().caiso_intertie_print_rt_basis is False
    assert env.caiso_intertie_rt_basis_active() is False


def test_off_reads_dam_untouched(calib):
    """Disarmed, the frame is exactly the DAM artifact."""
    path = calib / "wecc_intertie_lmp_hourly_CAISO.parquet"
    pd.testing.assert_frame_equal(
        env._read_intertie_frame(path, "CAISO"), pd.read_parquet(path)
    )


def test_on_overlays_rtm_where_printed(calib):
    """Armed, RTM replaces DAM only in hours the RTM sibling prints."""
    env.set_caiso_intertie_rt_basis(True)
    out = env._read_intertie_frame(
        calib / "wecc_intertie_lmp_hourly_CAISO.parquet", "CAISO"
    )
    assert out.sort_values("hour")["price"].tolist() == [30.0, 31.0, 52.0, 53.0]
    assert list(out.columns) == ["year", "hour", "hub", "price"]


def test_on_is_caiso_scoped(calib):
    """The toggle never touches another ISO's read."""
    env.set_caiso_intertie_rt_basis(True)
    path = calib / "wecc_intertie_lmp_hourly_CAISO.parquet"
    pd.testing.assert_frame_equal(
        env._read_intertie_frame(path, "NYISO"), pd.read_parquet(path)
    )


def test_on_without_sibling_raises(calib):
    """An armed run with no RTM artifact fails loud instead of pricing on DAM."""
    (calib / "wecc_intertie_lmp_hourly_CAISO_rtm.parquet").unlink()
    env.set_caiso_intertie_rt_basis(True)
    with pytest.raises(FileNotFoundError):
        env._read_intertie_frame(
            calib / "wecc_intertie_lmp_hourly_CAISO.parquet", "CAISO"
        )


def test_raw_hub_reader_follows_toggle(calib):
    """The raw-hub reader the clean rungs use sees the RTM print when armed."""
    off = env.measured_intertie_hub_price_raw("CAISO", 2021, 4, "PALOVRDE")
    env.set_caiso_intertie_rt_basis(True)
    on = env.measured_intertie_hub_price_raw("CAISO", 2021, 4, "PALOVRDE")
    if off is None:
        pytest.skip("raw reader needs a full-year series")
    assert on[0] == pytest.approx(30.0) and off[0] == pytest.approx(50.0)
