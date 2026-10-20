"""Tests for the whole-frame EIA-930 stale-snapshot repair (owner ruling R27).

The scoring benchmark (``load_eia_hourly_benchmark``) and the outage net-load
mask (``outage_detect.high_load_mask``) read the raw BA frame; both are served
through :func:`market_sim.data.stale_snapshot.repair_eia930_frame`. A synthetic
ISO ``TST`` is registered with a hand-built 8760 frame and tiny clean
partitions in a tmp CLEAN_DIR; nothing reads real data.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd
import pytest

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.data import stale_snapshot as ss
from scripts.lib import clean_io

YEAR = 2023
ISO = "TST"
CLOCK = pd.date_range("2023-01-01 07:00", periods=HOURS_PER_YEAR, freq="h")
FROZEN = slice(100, 106)  # a 6-h whole-record freeze
AREAS = {"A1": "Z-North", "B1": "Z-South"}
NG_COLUMNS = ("NG: COL", "NG: NG", "NG: NUC", "NG: WND", "NG: OIL")


def _frame() -> pd.DataFrame:
    t = np.arange(HOURS_PER_YEAR, dtype=float)
    cols = {
        "Demand": 30_000.0 + 1_000.0 * np.sin(t / 7.0),
        "Total interchange": 500.0 + 100.0 * np.cos(t / 3.0),
        "NG: COL": 9_000.0 + 500.0 * np.sin(t / 4.0),
        "NG: NG": 8_000.0 + 700.0 * np.cos(t / 6.0),
        "NG: NUC": np.full(HOURS_PER_YEAR, 1_800.0),  # a genuinely flat fleet
        "NG: WND": 10_000.0 + 2_000.0 * np.cos(t / 5.0),
        "NG: OIL": 5.0 + t % 7,
    }
    cols["Net generation"] = cols["Demand"] + cols["Total interchange"]
    for name, col in cols.items():
        if name != "NG: NUC":
            col[FROZEN] = col[FROZEN.start]
    return pd.DataFrame({"UTC time": CLOCK, **cols})


@pytest.fixture()
def tst(monkeypatch, tmp_clean_dir):
    """Register ``TST`` (coal / gas / nuclear / wind on the mix; oil kept)."""
    frame = _frame()
    monkeypatch.setattr(ss, "_eia_hourly_frame_filled", lambda ba, year: frame.copy())
    monkeypatch.setitem(
        ss.STALE_SNAPSHOT_SPECS,
        ISO,
        ss.StaleSnapshotSpec(
            iso=ISO,
            ba="TBA",
            min_run=4,
            subba_vector=lambda year: None,
            area_groups=lambda zones: AREAS,
            genmix_area="TST",
            genmix_columns=(
                ("NG: COL", "coal"),
                ("NG: NG", "gas"),
                ("NG: NUC", "nuclear"),
                ("NG: WND", "wind"),
            ),
            kept_stale_columns=("NG: OIL",),
        ),
    )
    ss.reset_caches()
    _write_sources()
    yield frame
    ss.reset_caches()


def _utc(hours) -> pd.Series:
    return pd.Series(CLOCK[hours]).dt.tz_localize("UTC")


GENMIX_MW = {"coal": 9_100.0, "gas": 8_200.0, "nuclear": 1_790.0, "wind": 7_000.0}


def _write_sources(genmix_hours=None):
    every = np.arange(HOURS_PER_YEAR)
    clean_io.write_clean(
        pd.concat(
            [
                pd.DataFrame(
                    {
                        "iso": ISO,
                        "area": a,
                        "interval_end_utc": _utc(every),
                        "load_mw": {"A1": 15_000.0, "B1": 16_000.0}[a],
                    }
                )
                for a in AREAS
            ],
            ignore_index=True,
        ),
        "iso-area-load",
        iso=ISO,
        year=YEAR,
    )
    legs = pd.DataFrame(
        {
            "counterparty": "C1",
            "reporter": "counterparty",
            "interval_end_utc": _utc(every).to_numpy(),
            "export_mw": 250.0,
            "iso": ISO,
            "ba": "TBA",
        }
    )
    clean_io.write_clean(legs, "counterparty-interchange", iso=ISO, year=YEAR)
    hours = every if genmix_hours is None else genmix_hours
    clean_io.write_clean(
        pd.concat(
            [
                pd.DataFrame(
                    {
                        "iso": ISO,
                        "area": "TST",
                        "fuel": f,
                        "interval_end_utc": _utc(hours),
                        "generation_mw": mw,
                        "n_intervals": 12,
                    }
                )
                for f, mw in GENMIX_MW.items()
            ],
            ignore_index=True,
        ),
        "iso-genmix",
        iso=ISO,
        year=YEAR,
    )


def _outside(frozen: slice = FROZEN) -> np.ndarray:
    keep = np.ones(HOURS_PER_YEAR, bool)
    keep[frozen] = False
    return keep


# ------------------------------------------------------------ trivial cases


def test_unregistered_iso_returns_the_same_object():
    frame = _frame()
    assert ss.repair_eia930_frame("MISO", YEAR, frame) is frame


def test_frame_without_utc_clock_is_untouched(tst):
    frame = tst.drop(columns=["UTC time"])
    assert ss.repair_eia930_frame(ISO, YEAR, frame) is frame


def test_input_frame_is_never_mutated(tst):
    raw = tst.copy()
    ss.repair_eia930_frame(ISO, YEAR, tst)
    pd.testing.assert_frame_equal(tst, raw)


# ------------------------------------------------------------ repairs


def test_fuel_columns_take_the_generation_mix_in_masked_hours(tst):
    out = ss.repair_eia930_frame(ISO, YEAR, tst)
    for column, fuel in (("NG: COL", "coal"), ("NG: NG", "gas"), ("NG: WND", "wind")):
        assert np.all(out[column].to_numpy()[FROZEN] == GENMIX_MW[fuel])
        assert np.array_equal(
            out[column].to_numpy()[_outside()], tst[column].to_numpy()[_outside()]
        )


def test_wind_equals_the_lp_input_repair(tst):
    out = ss.repair_eia930_frame(ISO, YEAR, tst)
    lp = ss.repair_renewable_gen(ISO, YEAR, {"wind": tst["NG: WND"].to_numpy()})
    assert np.array_equal(out["NG: WND"].to_numpy(), lp["wind"])


def test_demand_interchange_and_net_generation_share_the_input_repair(tst):
    out = ss.repair_eia930_frame(ISO, YEAR, tst)
    assert np.all(out["Demand"].to_numpy()[FROZEN] == 31_000.0)
    assert np.all(out["Total interchange"].to_numpy()[FROZEN] == 250.0)
    assert np.all(out["Net generation"].to_numpy()[FROZEN] == 31_250.0)
    for column in ("Demand", "Total interchange", "Net generation"):
        assert np.array_equal(
            out[column].to_numpy()[_outside()], tst[column].to_numpy()[_outside()]
        )


def test_genuinely_flat_column_is_screened_and_served_measured(tst):
    # NG: NUC holds 1,800 MW all year: the one screen flags it (nonzero repeat)
    # and the mix serves it — a measured value for a measured value.
    out = ss.repair_eia930_frame(ISO, YEAR, tst)
    assert np.all(out["NG: NUC"].to_numpy() == GENMIX_MW["nuclear"])


def test_kept_stale_column_keeps_eia_and_is_flagged(tst):
    out = ss.repair_eia930_frame(ISO, YEAR, tst)
    assert np.array_equal(out["NG: OIL"].to_numpy(), tst["NG: OIL"].to_numpy())
    prov = ss.benchmark_stale_provenance(ISO, YEAR)
    oil = prov[prov["column"] == "NG: OIL"]
    assert oil["hour"].tolist() == list(range(FROZEN.start, FROZEN.stop))
    assert set(oil["source"]) == {"eia_stale_kept"}
    assert set(prov[prov["column"] == "NG: COL"]["source"]) == {"iso_measured"}


def test_undeclared_stale_column_raises(tst, monkeypatch):
    frame = tst.assign(**{"NG: OTH": np.where(np.arange(HOURS_PER_YEAR) < 10, 7.0, 0)})
    monkeypatch.setattr(ss, "_eia_hourly_frame_filled", lambda ba, year: frame.copy())
    ss.reset_caches()
    with pytest.raises(ss.StaleSnapshotDataError, match="NG: OTH"):
        ss.repair_eia930_frame(ISO, YEAR, frame)


def test_blank_mix_raises_unless_the_hour_is_ruled(tst):
    blank = FROZEN.start + 2
    _write_sources(genmix_hours=np.delete(np.arange(HOURS_PER_YEAR), blank))
    ss.reset_caches()
    with pytest.raises(ss.StaleSnapshotDataError, match="coal generation mix"):
        ss.repair_eia930_frame(ISO, YEAR, tst)
    stamp = CLOCK[blank].strftime("%Y-%m-%dT%H:%MZ")
    ss.STALE_SNAPSHOT_SPECS[ISO] = dataclasses.replace(
        ss.STALE_SNAPSHOT_SPECS[ISO],
        kept_stale_genmix_hours=tuple(
            (c, stamp) for c in ("NG: COL", "NG: NG", "NG: NUC", "NG: WND")
        ),
    )
    ss.reset_caches()
    out = ss.repair_eia930_frame(ISO, YEAR, tst)
    assert out["NG: COL"].to_numpy()[blank] == tst["NG: COL"].to_numpy()[blank]
    prov = ss.benchmark_stale_provenance(ISO, YEAR)
    row = prov[(prov["hour"] == blank) & (prov["column"] == "NG: COL")]
    assert row["source"].tolist() == ["eia_stale_kept"]


def test_rows_are_matched_by_utc_stamp_not_position(tst):
    # A reversed slice (and a row the clock does not carry) still lands right.
    extra = pd.DataFrame({"UTC time": [CLOCK[0] - pd.Timedelta(hours=1)]})
    sliced = pd.concat([tst.iloc[::-1], extra], ignore_index=True)
    out = ss.repair_eia930_frame(ISO, YEAR, sliced)
    by_time = out.set_index("UTC time")["NG: COL"]
    assert np.all(by_time.loc[CLOCK[FROZEN]].to_numpy() == GENMIX_MW["coal"])
    assert np.isnan(by_time.loc[extra["UTC time"][0]])


def test_tz_aware_stamps_are_matched(tst):
    aware = tst.assign(**{"UTC time": tst["UTC time"].dt.tz_localize("UTC")})
    out = ss.repair_eia930_frame(ISO, YEAR, aware)
    assert np.all(out["NG: COL"].to_numpy()[FROZEN] == GENMIX_MW["coal"])
