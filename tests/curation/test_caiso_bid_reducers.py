"""caiso-282/283: the bid-ladder aggregator's rung convention and the exact year reducer.

Fixture: the 12 complete RTM energy ladders the caiso-281 2023q1 shard kept
verbatim (``results/rtm-intake/caiso281/2023q1/sample_PUB_BID_RTM_v3__20230215_
energy_ladders.csv``) — real OASIS rows, not synthetic ones.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
SAMPLE = (
    REPO
    / "results/rtm-intake/caiso281/2023q1/sample_PUB_BID_RTM_v3__20230215_energy_ladders.csv"
)

pytestmark = pytest.mark.skipif(
    not SAMPLE.exists(), reason="verbatim ladder fixture absent"
)


def _ladder_514544():
    """The FINDING-caiso281-rtm-2023q1 §3 ladder, verbatim."""
    mw = np.array([46, 50, 59, 80, 105, 110, 118, 127, 130, 140], float)
    px = np.array([18.59, 18.64, 24.37, 25.61, 27.11, 27.18, 300, 350, 450, 450], float)
    return mw, px


def test_aggregator_reads_the_step_covering_the_target():
    from scripts.data.aggregate_caiso_bid_ladders import _curve_price_at

    mw, px = _ladder_514544()
    # 80 % of 140 MW = 112 MW sits on the [110, 118) rung priced 27.18 — the
    # caiso-282 defect read the NEXT rung ($300) here.
    assert _curve_price_at(mw, px, np.array([112.0]))[0] == 27.18
    # exactly on a breakpoint: that breakpoint's price
    assert _curve_price_at(mw, px, np.array([118.0]))[0] == 300.0
    # below the curve start: first rung; past the end: held flat
    assert _curve_price_at(mw, px, np.array([7.0]))[0] == 18.59
    assert _curve_price_at(mw, px, np.array([150.0]))[0] == 450.0


def test_exact_quantile_from_counts_matches_pandas():
    from scripts.data.reduce_caiso_bid_year import exact_quantile_from_counts

    rng = np.random.default_rng(0)
    for _ in range(20):
        vals = rng.choice(
            np.round(rng.uniform(0, 300, 15), 2), size=rng.integers(3, 400)
        )
        s = pd.Series(vals)
        v, c = np.unique(vals, return_counts=True)
        assert exact_quantile_from_counts(v, c.astype(float), 0.98) == pytest.approx(
            float(s.quantile(0.98)), abs=1e-9
        )


def _sample_zip(tmp_path: Path) -> Path:
    z = tmp_path / "20230215_PUB_BID_RTM_v3_csv.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("20230215_20230215_PUB_BID_RTM_v3.csv", SAMPLE.read_bytes())
    return z


def test_reducer_reproduces_the_derive_on_real_ladders(tmp_path: Path):
    from scripts.data import derive_caiso_offer_surface as D
    from scripts.data import reduce_caiso_bid_year as R

    z = _sample_zip(tmp_path)
    seg = R._curve_rows(z)
    assert seg.resource_seq.nunique() == 12
    cap, min_mw, _ = R.pass1_capacity([z], tmp_path / "cache")
    # capacity is the derive's own statistic: p98 over segment rows
    ref = seg.groupby("resource_seq").segment_mw.quantile(0.98)
    pd.testing.assert_series_equal(
        cap.sort_index(), ref.sort_index(), check_names=False
    )

    geom = D._fleet_geometry()
    gas = D._gas_staircase()
    hourly = R.pass2_hourly(
        sorted((tmp_path / "cache").glob("*.parquet")), cap, geom, gas, 33.03
    )
    # body probe and one band, recomputed directly with the derive's functions
    s = seg.join(cap.rename("cap"), on="resource_seq")
    s = s[s.cap >= D.MIN_CAP_MW].sort_values(
        ["resource_seq", "interval_start_utc", "segment_mw"]
    )
    body = D._price_at_frac(s, D.BODY_FRAC)
    got = hourly.set_index(["resource_seq", "interval_start_utc"]).p_body
    pd.testing.assert_series_equal(
        got.sort_index(), body.sort_index(), check_names=False
    )
    lo, hi = D.class_band_windows(geom, "CC_REGULAR")["econ_high"]
    bp = D._band_price(s, lo, hi)
    day = hourly.day.iloc[0]
    m_ref = (bp - D.VOM_BY_CLASS["CC_REGULAR"]) / (
        geom["CC_REGULAR"]["base_hr"] * (gas[day] + D.CO2_FACTOR * 33.03)
    )
    got_m = hourly.set_index(
        ["resource_seq", "interval_start_utc"]
    ).m_CC_REGULAR_econ_high
    pd.testing.assert_series_equal(
        got_m.sort_index(), m_ref.sort_index(), check_names=False
    )
    # the 514544 ladder at hour 15 PT: body (35 % of 140 = 49 MW) prices 18.59
    r = hourly[hourly.resource_seq == 514544]
    assert r.p_body.iloc[0] == 18.59
