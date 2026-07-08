"""CPT->CST clock regression tests for the ERCOT measured-series builders.

The 2026-07-07 clock-unification round (PR #1725 + this round's parquet
rebuilds) fixed the shared placement defect where Central-*Prevailing*-Time
report labels were placed on the model's fixed CST clock unconverted, leaving
the whole mid-Mar-early-Nov series one hour late (Jan best lag 0 / Jul best
lag +1 vs EIA-930; ``docs/handoffs/ercot-g22-demand-side-design-2026-07.md``
§6-§7). These tests mirror ``tests/test_ercot_hsl.py`` for the remaining
prevailing-stamped builders: winter identity (CST labels unshifted), summer
-1 h (CDT labels), and gapless duplicate-free coverage through both DST
transitions.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from scripts import fetch_ercot_ordc_reserves as ordc  # noqa: E402
from scripts.build_ercot_as_withholding import (  # noqa: E402
    prevailing_he_to_cst,
)
from scripts.curate_ercot_wtx_congestion import _sced_ts_to_cst  # noqa: E402


# ---------------------------------------------------------------------------
# build_ercot_as_withholding.prevailing_he_to_cst — the sequential-HE DAM
# convention (NP3-911 cleared AS, 60-Day Gen Resource Data, DAMASAGG).
# ---------------------------------------------------------------------------


def _he_frame(day: str, hes: list[int]) -> tuple[pd.Series, pd.Series]:
    dd = pd.Series(pd.to_datetime([day] * len(hes)))
    return dd, pd.Series(hes)


def test_prevailing_he_winter_identity():
    """January labels are already CST: HE k -> hour-beginning k-1, same day."""
    dd, he = _he_frame("2024-01-05", list(range(1, 25)))
    ts = prevailing_he_to_cst(dd, he)
    assert ts.iloc[0] == pd.Timestamp("2024-01-05 00:00")
    assert ts.iloc[-1] == pd.Timestamp("2024-01-05 23:00")
    assert ts.is_monotonic_increasing and ts.nunique() == 24


def test_prevailing_he_summer_minus_one_hour():
    """June labels are CDT: the CST stamp is one hour earlier than naive."""
    dd, he = _he_frame("2024-06-10", list(range(1, 25)))
    ts = prevailing_he_to_cst(dd, he)
    # naive HE 1 -> 2024-06-10 00:00; converted -> 2024-06-09 23:00 CST.
    assert ts.iloc[0] == pd.Timestamp("2024-06-09 23:00")
    assert ts.iloc[-1] == pd.Timestamp("2024-06-10 22:00")


def test_prevailing_he_spring_forward_23_rows_gapless():
    """Spring-forward day carries HE 1,2,4..24 (23 rows) and covers CST
    2024-03-10 00:00..22:00 gapless once converted."""
    dd, he = _he_frame("2024-03-10", [1, 2] + list(range(4, 25)))
    ts = prevailing_he_to_cst(dd, he)
    got = sorted(ts)
    want = list(pd.date_range("2024-03-10 00:00", periods=23, freq="h"))
    assert got == want


def test_prevailing_he_fall_back_25_rows_gapless():
    """Fall-back day carries sequential HE 1-25 (HE 3 = the repeated
    01:00-02:00 prevailing hour, already CST); conversion covers
    2024-11-02 23:00 .. 2024-11-03 23:00 gapless and duplicate-free."""
    dd, he = _he_frame("2024-11-03", list(range(1, 26)))
    ts = prevailing_he_to_cst(dd, he)
    got = sorted(ts)
    want = list(pd.date_range("2024-11-02 23:00", periods=25, freq="h"))
    assert got == want


def test_prevailing_he_year_coverage_gapless():
    """A full DST-spanning year of sequential-HE labels covers every CST hour
    it should exactly once (the spring day's missing CST 23:00 arrives from
    the next day's HE 1)."""
    days, hes = [], []
    for day in pd.date_range("2024-03-09", "2024-03-12"):
        n = 23 if day == pd.Timestamp("2024-03-10") else 24
        seq = [1, 2] + list(range(4, 25)) if n == 23 else list(range(1, 25))
        days += [day] * n
        hes += seq
    ts = prevailing_he_to_cst(pd.Series(days), pd.Series(hes))
    got = sorted(ts)
    # 2024-03-09 00:00 CST .. 2024-03-12 22:00 CST, gapless (95 hours: the
    # window's last CDT HE 24 lands at 22:00 CST; 23:00 arrives with the
    # NEXT day's HE 1, outside this window).
    want = list(pd.date_range("2024-03-09 00:00", periods=95, freq="h"))
    assert got == want


# ---------------------------------------------------------------------------
# fetch_ercot_ordc_reserves — NP6-905 SCED-interval stamps + plausibility
# nulling + hourly placement.
# ---------------------------------------------------------------------------


def _sced_frame(ts: pd.DatetimeIndex, flag: str = "N") -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ts": list(ts),
            "prc": 6000.0 + np.arange(len(ts)),
            "rtolcap": 9000.0,
        }
    )


def test_ordc_to_model_clock_hourly_mean_on_cst():
    """5-min CST-converted stamps average into their covering CST hour."""
    ts = pd.date_range("2024-01-05 00:00", periods=24, freq="5min")
    df, interpolated, left_nan = ordc._to_model_clock(_sced_frame(ts), 2024)
    assert len(df) == 8760
    jan5_h0 = df.loc[(df["hour"] == 96), "prc"]  # Jan 5 = day 4 -> hour 96
    assert np.isclose(jan5_h0.iloc[0], 6000.0 + np.mean(range(12)))
    assert left_nan > 0  # everything outside the one covered day


def test_ordc_null_implausible_mw():
    """MW capability values outside [0, 200 GW] are nulled (the corrupt 2024
    PRC interval class); price columns are never bounded."""
    ts = pd.date_range("2024-01-05 00:00", periods=4, freq="5min")
    df = _sced_frame(ts)
    df.loc[1, "prc"] = -56_246_691.0  # the cited corrupt-interval magnitude
    df.loc[2, "rtolcap"] = 250_000.0
    df["rtorpa"] = -5.0  # negative price is legitimate -> untouched
    cleaned, nulled = ordc._null_implausible_mw(df)
    assert nulled == 2
    assert cleaned["prc"].isna().sum() == 1
    assert cleaned["rtolcap"].isna().sum() == 1
    assert (cleaned["rtorpa"] == -5.0).all()


def test_ordc_interp_short_gaps_keeps_long_tail_nan():
    """Interior holes <= 24 h interpolate; a long regime tail stays NaN."""
    s = pd.Series(np.arange(200, dtype=float))
    s.iloc[10:12] = np.nan  # short interior hole
    s.iloc[150:] = np.nan  # 50-hour tail > _MAX_GAP_HOURS
    filled, interpolated, left_nan = ordc._interp_short_gaps(s)
    assert interpolated == 2 and left_nan == 50
    assert np.isclose(filled.iloc[10], 10.0)
    assert filled.iloc[150:].isna().all()


def test_ordc_sced_stamps_summer_conversion():
    """NP6-905 SCED stamps are prevailing: a June stamp lands one CST hour
    earlier (via the same _prevailing_to_standard the HSL builder uses)."""
    from scripts.build_ercot_hsl import _prevailing_to_standard

    raw = pd.Series(pd.to_datetime(["2024-06-10 15:00:00", "2024-01-10 15:00:00"]))
    conv = _prevailing_to_standard(raw, None)
    assert conv.iloc[0] == pd.Timestamp("2024-06-10 14:00")  # CDT -> CST
    assert conv.iloc[1] == pd.Timestamp("2024-01-10 15:00")  # winter identity


# ---------------------------------------------------------------------------
# curate_ercot_wtx_congestion — NP6-86 SCED stamps via RepeatedHourFlag.
# ---------------------------------------------------------------------------


def test_wtx_sced_ts_winter_identity_summer_shift():
    df = pd.DataFrame(
        {
            "SCEDTimeStamp": ["01/15/2024 12:00:00", "07/15/2024 12:00:00"],
            "RepeatedHourFlag": ["N", "N"],
        }
    )
    ts = _sced_ts_to_cst(df)
    assert ts.iloc[0] == pd.Timestamp("2024-01-15 12:00")
    assert ts.iloc[1] == pd.Timestamp("2024-07-15 11:00")


def test_wtx_sced_ts_fall_back_repeat_disambiguated():
    """The twice-occurring 01:xx prevailing stamps on the fall-back day map to
    distinct CST hours: first pass (CDT) -> 00:xx, flagged repeat (CST) -> 01:xx."""
    df = pd.DataFrame(
        {
            "SCEDTimeStamp": ["11/03/2024 01:30:00", "11/03/2024 01:30:00"],
            "RepeatedHourFlag": ["N", "Y"],
        }
    )
    ts = _sced_ts_to_cst(df)
    assert ts.iloc[0] == pd.Timestamp("2024-11-03 00:30")
    assert ts.iloc[1] == pd.Timestamp("2024-11-03 01:30")


# ---------------------------------------------------------------------------
# build_ercot_as_by_restype_from_60day — the sequential-HE conversion is
# imported and applied (guards the missing-import regression found when the
# rebuilt parquets were first regenerated in this round).
# ---------------------------------------------------------------------------


def test_by_restype_build_year_uses_converted_clock():
    import build_ercot_as_by_restype_from_60day as restype

    days, hes = [], []
    for day in pd.date_range("2024-06-10", "2024-06-11"):
        days += [day] * 24
        hes += list(range(1, 25))
    big = pd.DataFrame(
        {
            "dd": pd.Series(days),
            "he": pd.Series(hes),
            "cls": "storage",
            "mw": 100.0,
        }
    )
    frame = restype.build_year(big, 2024)
    assert frame is not None and len(frame) == 8760
    # June 10 HE 1 (CDT) -> CST 2024-06-09 23:00 = hour index 3839 on the
    # non-leap clock (Jan..May = 151 days; Jun 9 is day index 159;
    # 159*24 + 23 = 3839). Naive placement would start at 3840 instead.
    assert frame.loc[3839, "storage"] == 100.0
    # The two delivery days cover CST 3839..3886 contiguously (Jun 11 HE 1
    # backfills Jun 10 23:00); the hour after the window is zero-filled.
    assert (frame.loc[3839:3886, "storage"] == 100.0).all()
    assert frame.loc[3887, "storage"] == 0.0
