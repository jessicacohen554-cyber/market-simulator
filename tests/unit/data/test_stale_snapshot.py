"""Tests for the EIA-930 stale-snapshot repair (owner rulings R22 / R23).

A synthetic ISO ``TST`` is registered with a hand-built 8760 frame and tiny
clean partitions; nothing reads real data.
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
AREAS = {"A1": "Z-North", "A2": "Z-North", "B1": "Z-South"}


def _frame() -> pd.DataFrame:
    t = np.arange(HOURS_PER_YEAR, dtype=float)
    demand = 30_000.0 + 1_000.0 * np.sin(t / 7.0)
    wind = 10_000.0 + 2_000.0 * np.cos(t / 5.0)
    solar = np.where(t % 24 < 12, 0.0, 500.0 + t % 24)  # zero half of each day
    for col in (demand, wind, solar):
        col[FROZEN] = col[FROZEN.start]
    return pd.DataFrame(
        {"UTC time": CLOCK, "Demand": demand, "NG: WND": wind, "NG: SUN": solar}
    )


def _subba() -> np.ndarray:
    t = np.arange(HOURS_PER_YEAR, dtype=float)
    vec = np.column_stack([1000 + t % 7, 2000 + t % 5, 3000 + t % 3]).astype(float)
    vec[FROZEN] = vec[FROZEN.start]
    return vec


@pytest.fixture()
def tst(monkeypatch, tmp_clean_dir):
    """Register ``TST`` and redirect its frame; clean partitions go to a tempdir."""
    frame = _frame()
    monkeypatch.setattr(ss, "_eia_hourly_frame_filled", lambda ba, year: frame.copy())
    monkeypatch.setitem(
        ss.STALE_SNAPSHOT_SPECS,
        ISO,
        ss.StaleSnapshotSpec(
            iso=ISO,
            ba="TBA",
            min_run=4,
            subba_vector=lambda year: _subba(),
            area_groups=lambda zones: AREAS,
            genmix_area="TST",
        ),
    )
    ss.reset_caches()
    yield frame
    ss.reset_caches()


def _utc(hours) -> pd.Series:
    return pd.Series(CLOCK[hours]).dt.tz_localize("UTC")


def _write_area_load(
    hours=None, value=lambda a: {"A1": 900.0, "A2": 1100.0, "B1": 2000.0}[a]
):
    hours = np.arange(HOURS_PER_YEAR) if hours is None else hours
    rows = [
        pd.DataFrame(
            {
                "iso": ISO,
                "area": a,
                "interval_end_utc": _utc(hours),
                "load_mw": value(a),
            }
        )
        for a in AREAS
    ]
    clean_io.write_clean(
        pd.concat(rows, ignore_index=True), "iso-area-load", iso=ISO, year=YEAR
    )


def _write_legs(rows: list[tuple[str, str, int, float]]):
    df = pd.DataFrame(rows, columns=["counterparty", "reporter", "hour", "export_mw"])
    df["interval_end_utc"] = _utc(df.pop("hour").to_numpy()).to_numpy()
    df["iso"], df["ba"] = ISO, "TBA"
    clean_io.write_clean(df, "counterparty-interchange", iso=ISO, year=YEAR)


def _write_genmix(fuels=("wind", "solar"), hours=None):
    hours = np.arange(HOURS_PER_YEAR) if hours is None else hours
    rows = [
        pd.DataFrame(
            {
                "iso": ISO,
                "area": "TST",
                "fuel": f,
                "interval_end_utc": _utc(hours),
                "generation_mw": 123.0,
                "n_intervals": 12,
            }
        )
        for f in fuels
    ]
    clean_io.write_clean(
        pd.concat(rows, ignore_index=True), "iso-genmix", iso=ISO, year=YEAR
    )


# ---------------------------------------------------------------- masks


def test_demand_mask_is_exactly_the_frozen_block(tst):
    mask = ss.demand_stale_mask(ISO, YEAR)
    assert np.flatnonzero(mask).tolist() == list(range(FROZEN.start, FROZEN.stop))


def test_subba_vector_alone_triggers_the_mask(tst, monkeypatch):
    moving = tst.copy()
    moving["Demand"] = np.arange(HOURS_PER_YEAR, dtype=float)  # Demand not frozen
    monkeypatch.setattr(ss, "_eia_hourly_frame_filled", lambda ba, year: moving)
    ss.reset_caches()
    assert ss.demand_stale_mask(ISO, YEAR).sum() == FROZEN.stop - FROZEN.start


def test_night_zero_solar_is_not_stale_outside_the_record_freeze(tst):
    mask = ss.fuel_stale_mask(ISO, YEAR, "NG: SUN")
    # Every day carries a 12-h zero run; only the frozen block is masked.
    assert np.flatnonzero(mask).tolist() == list(range(FROZEN.start, FROZEN.stop))


def test_unregistered_iso_has_no_mask():
    assert ss.demand_stale_mask("MISO", YEAR) is None
    assert ss.fuel_stale_mask("MISO", YEAR, "NG: WND") is None


# ---------------------------------------------------------------- repairs


def test_system_demand_repaired_only_in_masked_hours(tst):
    _write_area_load()
    raw = tst["Demand"].to_numpy(dtype=float)
    out = ss.repair_system_demand(ISO, YEAR, raw)
    assert np.all(out[FROZEN] == 4000.0)
    keep = np.ones(HOURS_PER_YEAR, bool)
    keep[FROZEN] = False
    assert np.array_equal(out[keep], raw[keep])


def test_zone_shares_repaired_from_area_loads(tst):
    _write_area_load()
    shares = np.full((2, HOURS_PER_YEAR), 0.5)
    out = ss.repair_zone_shares(ISO, YEAR, shares, ["Z-North", "Z-South"])
    assert np.allclose(out[:, FROZEN], [[0.5], [0.5]])  # (900+1100) / 4000
    np.testing.assert_allclose(out.sum(axis=0), 1.0)


def _respec(**kw) -> None:
    """Replace the registered TST spec's ruled-gap fields for one test."""
    ss.STALE_SNAPSHOT_SPECS[ISO] = dataclasses.replace(
        ss.STALE_SNAPSHOT_SPECS[ISO], **kw
    )
    ss.reset_caches()


def _stamp(hour: int) -> str:
    return CLOCK[hour].strftime("%Y-%m-%dT%H:%MZ")


def _every_masked_hour(party: str, reporter: str, mw: float, skip=()):
    return [
        (party, reporter, k, mw)
        for k in range(FROZEN.start, FROZEN.stop)
        if k not in skip
    ]


def test_interchange_counterparty_first_then_own(tst):
    h = FROZEN.start
    _write_legs(
        _every_masked_hour("C1", "counterparty", 100.0)
        + [("C1", "own", h, 999.0)]  # ignored: the counterparty reports
        + _every_masked_hour("C2", "own", -40.0)  # no counterparty report: own used
    )
    out = ss.repair_net_interchange(ISO, YEAR, np.zeros(HOURS_PER_YEAR))
    assert np.allclose(out[FROZEN], 60.0)
    assert out[FROZEN.stop] == 0.0


def test_unruled_unreported_leg_raises(tst):
    # C3 reports from hour 0, then nothing in the frozen block, and no ruling.
    _write_legs(_every_masked_hour("C1", "counterparty", 1.0) + [("C3", "own", 0, 5.0)])
    with pytest.raises(ss.StaleSnapshotDataError, match="C3"):
        ss.repair_net_interchange(ISO, YEAR, np.zeros(HOURS_PER_YEAR))


def test_ruled_omittable_leg_is_left_out_and_flagged(tst, caplog):
    _respec(omitted_legs=("C3",))
    _write_legs(_every_masked_hour("C1", "counterparty", 1.0) + [("C3", "own", 0, 5.0)])
    out = ss.repair_net_interchange(ISO, YEAR, np.zeros(HOURS_PER_YEAR))
    assert np.allclose(out[FROZEN], 1.0)
    _write_genmix()
    prov = ss.stale_snapshot_provenance(ISO, YEAR)
    in_block = prov[prov["hour"].between(FROZEN.start, FROZEN.stop - 1)]
    assert (in_block["interchange_legs_omitted"] == "C3").all()
    assert "omitted legs" in caplog.text


def test_ruled_hour_keeps_the_stale_interchange(tst):
    gap = FROZEN.start + 2  # C4 unreported on both sides in this one hour
    _respec(kept_stale_interchange_hours=(_stamp(gap),))
    _write_legs(
        [("C4", "counterparty", 0, 7.0)]
        + _every_masked_hour("C4", "counterparty", 7.0, skip=(gap,))
    )
    ti = np.full(HOURS_PER_YEAR, 273.0)
    out = ss.repair_net_interchange(ISO, YEAR, ti)
    assert out[gap] == 273.0
    assert out[gap - 1] == 7.0
    _write_genmix()
    prov = ss.stale_snapshot_provenance(ISO, YEAR).set_index("hour")
    assert prov.loc[gap, "interchange_source"] == "eia_stale_kept"
    assert prov.loc[gap - 1, "interchange_source"] == "iso_measured"


def test_leg_before_its_first_report_is_not_a_residual(tst):
    # C9 starts reporting after the frozen block (a BA that did not yet exist).
    _write_legs(
        _every_masked_hour("C1", "counterparty", 1.0)
        + [("C9", "counterparty", FROZEN.stop + 10, 1.0)]
    )
    out = ss.repair_net_interchange(ISO, YEAR, np.zeros(HOURS_PER_YEAR))
    assert np.allclose(out[FROZEN], 1.0)


def test_renewables_repaired_on_their_own_masks(tst):
    _write_genmix()
    gen = {
        "wind": tst["NG: WND"].to_numpy(float),
        "solar": tst["NG: SUN"].to_numpy(float),
    }
    out = ss.repair_renewable_gen(ISO, YEAR, gen)
    for fuel in ("wind", "solar"):
        assert np.all(out[fuel][FROZEN] == 123.0)
        assert out[fuel][FROZEN.stop] == gen[fuel][FROZEN.stop]


# ---------------------------------------------------------------- loud failures


def test_missing_partition_raises_with_regenerate_hint(tst):
    with pytest.raises(FileNotFoundError, match="regenerate_clean.py"):
        ss.repair_system_demand(ISO, YEAR, tst["Demand"].to_numpy(float))


def test_provenance_flags_every_masked_hour(tst):
    _write_area_load()
    _write_legs(_every_masked_hour("C1", "counterparty", 1.0))
    _write_genmix()
    prov = ss.stale_snapshot_provenance(ISO, YEAR)
    assert prov["hour"].tolist() == list(range(FROZEN.start, FROZEN.stop))
    assert (prov["demand_source"] == "iso_measured").all()
    assert (prov["wind_source"] == "iso_measured").all()


def test_masked_hour_without_area_load_raises(tst):
    hours = np.setdiff1d(np.arange(HOURS_PER_YEAR), [FROZEN.start + 2])
    _write_area_load(hours=hours)
    with pytest.raises(ss.StaleSnapshotDataError, match="area load"):
        ss.repair_system_demand(ISO, YEAR, tst["Demand"].to_numpy(float))


def test_ruled_genmix_gap_keeps_the_stale_value_and_flags_it(tst):
    gap = (FROZEN.start + 1, FROZEN.start + 2)
    _respec(kept_stale_renewable_windows=((_stamp(gap[0]), _stamp(gap[1])),))
    _write_genmix(hours=np.setdiff1d(np.arange(HOURS_PER_YEAR), gap))
    wind = tst["NG: WND"].to_numpy(float)
    out = ss.repair_renewable_gen(ISO, YEAR, {"wind": wind})["wind"]
    assert np.array_equal(out[list(gap)], wind[list(gap)])
    assert out[FROZEN.start] == 123.0
    _write_legs(_every_masked_hour("C1", "counterparty", 1.0))
    prov = ss.stale_snapshot_provenance(ISO, YEAR).set_index("hour")
    assert prov.loc[gap[0], "wind_source"] == "eia_stale_kept"
    assert prov.loc[FROZEN.start, "wind_source"] == "iso_measured"


def test_masked_hour_without_genmix_raises(tst):
    hours = np.setdiff1d(np.arange(HOURS_PER_YEAR), [FROZEN.start])
    _write_genmix(hours=hours)
    with pytest.raises(ss.StaleSnapshotDataError, match="wind generation mix"):
        ss.repair_renewable_gen(ISO, YEAR, {"wind": tst["NG: WND"].to_numpy(float)})


# ---------------------------------------------------------------- other ISOs


@pytest.mark.parametrize(
    "iso", ["ERCOT", "CAISO", "MISO", "PJM", "NYISO", "NEISO", "NWPP", "SOCO"]
)
def test_other_isos_pass_through_bit_identical(iso):
    arr = np.arange(HOURS_PER_YEAR, dtype=float)
    shares = np.full((2, HOURS_PER_YEAR), 0.5)
    gen = {"wind": arr.copy()}
    assert ss.repair_system_demand(iso, YEAR, arr) is arr
    assert ss.repair_zone_shares(iso, YEAR, shares, ["a", "b"]) is shares
    assert ss.repair_net_interchange(iso, YEAR, arr) is arr
    assert ss.repair_renewable_gen(iso, YEAR, gen) is gen


def test_only_spp_is_registered():
    assert set(ss.STALE_SNAPSHOT_SPECS) == {"SPP"}
