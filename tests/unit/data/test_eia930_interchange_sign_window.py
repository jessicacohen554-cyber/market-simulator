"""EIA-930 published sign-inverted ``Total interchange`` windows (lane R-SOCO-B).

``constants.EIA930_INTERCHANGE_SIGN_INVERTED_WINDOWS_UTC`` registers, per BA,
the inclusive UTC windows inside which EIA's published ``Total interchange``
carries the wrong sign. ``frames._repair_inverted_interchange`` negates the
column inside them at every raw-extract read seam; outside them, and for every
BA with no window, the frame is returned unchanged (the same object).

Pinned here: the registry is SOCO-only; the repair is exact on a synthetic
frame (inside negated, outside untouched, window edges inclusive, input never
edited); and on the committed SOCO extract the served 2019 schedule satisfies
EIA's own identity ``TI = NG - D`` in every hour where the three are present.
"""

import numpy as np
import pandas as pd
import pytest

from market_sim.config.constants import EIA930_INTERCHANGE_SIGN_INVERTED_WINDOWS_UTC
from market_sim.data.eia930 import frames
from tests.helpers import REPO_ROOT

_SOCO_HOURLY = REPO_ROOT / "data" / "raw" / "eia-930-hourly" / "SOCO hourly.parquet"


def _frame(ti: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "UTC time": pd.date_range("2019-09-11 03:00", periods=len(ti), freq="h"),
            "Total interchange": ti,
            "Demand": 100.0,
        }
    )


def test_registry_is_soco_only_and_measured_window():
    assert EIA930_INTERCHANGE_SIGN_INVERTED_WINDOWS_UTC == {
        "SOCO": (("2019-01-01 07:00", "2019-09-11 05:00"),)
    }


def test_synthetic_window_negated_inclusive_and_input_untouched():
    df = _frame([10.0, 20.0, 30.0, 40.0, np.nan])
    out = frames._repair_inverted_interchange(df, "SOCO")
    # 03:00, 04:00, 05:00 are inside (05:00 is the inclusive last stamp).
    assert out["Total interchange"].tolist()[:4] == [-10.0, -20.0, -30.0, 40.0]
    assert np.isnan(out["Total interchange"].iloc[4])
    assert df["Total interchange"].tolist()[:4] == [10.0, 20.0, 30.0, 40.0]
    assert (out["Demand"] == df["Demand"]).all()


def test_other_ba_and_outside_window_return_same_object():
    df = _frame([10.0, 20.0])
    assert frames._repair_inverted_interchange(df, "ERCO") is df
    late = df.assign(**{"UTC time": df["UTC time"] + pd.Timedelta(days=30)})
    assert frames._repair_inverted_interchange(late, "SOCO") is late
    no_col = df.drop(columns=["Total interchange"])
    assert frames._repair_inverted_interchange(no_col, "SOCO") is no_col


@pytest.mark.skipif(not _SOCO_HOURLY.exists(), reason="SOCO hourly extract absent")
def test_real_2019_soco_repaired_to_eia_identity():
    frames._eia_hourly_frame.cache_clear()
    frames._eia_hourly_frame_filled.cache_clear()
    f = frames._eia_hourly_frame_filled("SOCO", 2019)
    assert f is not None
    ng, d, ti = f["Net generation"], f["Demand"], f["Total interchange"]
    ok = ng.notna() & d.notna() & ti.notna()
    assert int(ok.sum()) >= 8700
    assert float((ti[ok] - (ng[ok] - d[ok])).abs().max()) <= 1.0
    # The raw column is still inverted on disk (data/raw is immutable).
    raw = pd.read_parquet(_SOCO_HOURLY)
    raw = raw[raw["UTC time"] <= pd.Timestamp("2019-09-11 05:00")]
    x = raw["Net generation"] - raw["Demand"]
    assert np.allclose(raw["Total interchange"], -x, atol=1.0)


@pytest.mark.skipif(not _SOCO_HOURLY.exists(), reason="SOCO hourly extract absent")
def test_real_2020_soco_untouched():
    raw = pd.read_parquet(_SOCO_HOURLY)
    assert (
        frames._repair_inverted_interchange(
            raw[raw["UTC time"] >= pd.Timestamp("2020-01-01")], "SOCO"
        )
        is not None
    )
    frames._eia_hourly_frame.cache_clear()
    frames._eia_hourly_frame_filled.cache_clear()
    f = frames._eia_hourly_frame_filled("SOCO", 2020)
    ok = f[["Net generation", "Demand", "Total interchange"]].notna().all(axis=1)
    g = f[ok]
    assert np.allclose(
        g["Total interchange"], g["Net generation"] - g["Demand"], atol=1.0
    )
