"""R-CAISO-13 ``caiso_eia930_clock_repair``: the CISO late-stamp frame repair.

Synthetic extracts only (1 BA, a few hours), per the repo's trivial-case-first
testing pattern. Checks: the unarmed and non-CISO paths return the SAME object;
inside a registered window the value stamped ``s`` lands on ``s - 1 h``; the
seam hour takes its neighbours' mean; the column families are respected; the
switch clears the frame caches; and the supply-consistent demand transform
moves only the EIA-930 term.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config import constants
from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.paths import CAISO_HSL_DIR as _CAISO_HSL
from market_sim.data import renewables as R
from market_sim.data.eia930 import actuals as A
from market_sim.data.eia930 import demand as D
from market_sim.data.eia930 import frames as F
from tests.helpers import requires_raw

from market_sim.config.paths import RAW_DIR as _RAW

_ENVELOPE = _RAW / "reference" / "caiso-storage-shape-envelope.csv"
_CISO_EXTRACT = F._eia_hourly_path("CISO")


@pytest.fixture(autouse=True)
def _disarm():
    """Leave the process switch off after every test."""
    F.set_caiso_eia930_clock_repair(False)
    yield
    F.set_caiso_eia930_clock_repair(False)


def _extract(n: int = 8) -> pd.DataFrame:
    """An 8-row hourly CISO-like extract with distinct values per column."""
    utc = pd.date_range("2024-01-01 00:00", periods=n, freq="h")
    k = np.arange(n, dtype=float)
    return pd.DataFrame(
        {
            "UTC time": utc,
            "Demand": 100.0 + k,
            "Demand forecast": 500.0 + k,
            "Net generation": 200.0 + k,
            "Total interchange": 300.0 + k,
            "NG: SUN": 400.0 + k,
        }
    )


def _windows(monkeypatch, gen, dem):
    monkeypatch.setattr(
        constants,
        "EIA930_CISO_CLOCK_LATE_WINDOWS_UTC",
        {"generation": gen, "demand": dem},
    )


def test_unarmed_returns_same_object():
    """Off by default: the input object comes back untouched."""
    df = _extract()
    assert F._repair_clock_late_windows(df, "CISO") is df


def test_other_ba_returns_same_object():
    """Armed, but a non-CISO BA is never touched."""
    F.set_caiso_eia930_clock_repair(True)
    df = _extract()
    assert F._repair_clock_late_windows(df, "ERCO") is df


def test_window_pulls_back_one_hour_with_mean_seam(monkeypatch):
    """Stamps 02..05 are late: row s-1 takes s; the last row takes the mean."""
    _windows(
        monkeypatch,
        ("2024-01-01 02:00", "2024-01-01 05:00"),
        ("2024-01-01 02:00", "2024-01-01 05:00"),
    )
    F.set_caiso_eia930_clock_repair(True)
    df = _extract()
    out = F._repair_clock_late_windows(df, "CISO")
    assert out is not df
    # Rows 1..4 take the values published at 2..5; row 5 (the seam) takes
    # mean(published 5, published 6); rows 0, 6, 7 are untouched.
    exp = np.array([0, 2, 3, 4, 5, 5.5, 6, 7], dtype=float)
    for col, base in (
        ("Demand", 100.0),
        ("Net generation", 200.0),
        ("NG: SUN", 400.0),
    ):
        np.testing.assert_allclose(out[col].to_numpy(), base + exp)
    # Not in any family: never moved. Total interchange is on the true clock
    # (R-CAISO-16), so it is outside the generation family.
    np.testing.assert_allclose(out["Demand forecast"], df["Demand forecast"])
    np.testing.assert_allclose(out["Total interchange"], df["Total interchange"])
    # The raw input is never edited in place.
    np.testing.assert_allclose(df["Demand"], 100.0 + np.arange(8))


def test_families_have_independent_windows(monkeypatch):
    """Generation window empty of rows: only Demand moves."""
    _windows(
        monkeypatch,
        ("2030-01-01 00:00", "2030-01-02 00:00"),
        ("2024-01-01 03:00", "2024-01-01 04:00"),
    )
    F.set_caiso_eia930_clock_repair(True)
    out = F._repair_clock_late_windows(_extract(), "CISO")
    np.testing.assert_allclose(out["NG: SUN"], 400.0 + np.arange(8))
    np.testing.assert_allclose(
        out["Demand"], 100.0 + np.array([0, 1, 3, 4, 4.5, 5, 6, 7])
    )


def test_switch_clears_frame_caches(monkeypatch):
    """Changing the switch empties every cached frame."""
    calls = []
    for name in (
        "_eia_hourly_frame",
        "_eia_hourly_frame_filled",
        "_pool_hourly_frame",
        "_ercot_hourly_frame",
    ):
        fn = getattr(F, name)
        monkeypatch.setattr(fn, "cache_clear", lambda n=name: calls.append(n))
    F.set_caiso_eia930_clock_repair(True)
    assert len(calls) == 4
    F.set_caiso_eia930_clock_repair(True)  # idempotent: no second clear
    assert len(calls) == 4


def test_supply_consistent_moves_only_eia930_term(monkeypatch):
    """The CEMS/flat remainder is invariant; the 930 term shifts one row."""
    g = np.arange(D.HOURS_PER_YEAR, dtype=float)
    rest = np.full(D.HOURS_PER_YEAR, 1000.0)
    monkeypatch.setattr(
        D, "_supply_consistent_eia930_term", lambda y: g if y == 2024 else None
    )
    stamps = D._model_row_starts_utc(2024) + pd.Timedelta(hours=1)
    first, last = stamps[10], stamps[20]
    monkeypatch.setattr(
        constants,
        "EIA930_CISO_CLOCK_LATE_WINDOWS_UTC",
        {"generation": (str(first), str(last)), "demand": (str(first), str(last))},
    )
    out = D._repair_supply_consistent_clock(2024, g + rest)
    moved = out - rest
    np.testing.assert_allclose(moved[:9], g[:9])
    np.testing.assert_allclose(moved[9:20], g[10:21])
    assert moved[20] == pytest.approx(0.5 * (g[20] + g[21]))
    np.testing.assert_allclose(moved[21:], g[21:])


def test_model_row_starts_skip_leap_day():
    """The 8760 model clock drops Feb 29 and starts at PST midnight."""
    idx = D._model_row_starts_utc(2024)
    assert len(idx) == D.HOURS_PER_YEAR
    assert idx[0] == pd.Timestamp("2024-01-01 08:00")
    pst = idx - pd.Timedelta(hours=8)
    assert not ((pst.month == 2) & (pst.day == 29)).any()


# --- R-CAISO-15: the HSL generation term (renewables._repair_caiso_hsl_clock) --


def _hsl_frame(n: int = HOURS_PER_YEAR) -> pd.DataFrame:
    """A synthetic HSL frame: gen = k, curtailment = 10 (wind) / 20 (solar)."""
    k = np.arange(n, dtype=float)
    return pd.DataFrame(
        {
            "hour": np.arange(n),
            "wind_gen_mw": k,
            "wind_hsl_mw": k + 10.0,
            "solar_gen_mw": 2 * k,
            "solar_hsl_mw": 2 * k + 20.0,
        }
    )


def test_hsl_unarmed_and_other_iso_return_same_object():
    """Off by default, and armed-but-not-CAISO: the input object comes back."""
    df = _hsl_frame()
    assert R._repair_caiso_hsl_clock("CAISO", 2024, df) is df
    F.set_caiso_eia930_clock_repair(True)
    assert R._repair_caiso_hsl_clock("ERCOT", 2024, df) is df


def test_hsl_year_outside_window_returns_same_object(monkeypatch):
    """Armed, but the year's stamps never reach the generation window."""
    _windows(
        monkeypatch,
        ("2023-11-01 08:00", "2025-12-02 22:00"),
        ("2022-06-16 08:00", "2025-12-02 22:00"),
    )
    F.set_caiso_eia930_clock_repair(True)
    df = _hsl_frame()
    for year in (2019, 2022, 2026):
        assert R._repair_caiso_hsl_clock("CAISO", year, df) is df


def test_hsl_gen_replaced_and_curtailment_kept(monkeypatch):
    """Gen is re-read from the repaired frame; hsl = new gen + old curtailment."""
    F.set_caiso_eia930_clock_repair(True)
    new = {
        "wind": np.full(HOURS_PER_YEAR, 7.0),
        "solar": np.full(HOURS_PER_YEAR, 9.0),
    }
    monkeypatch.setattr(A, "load_eia_hourly_renewable_gen", lambda iso, y: new)
    df = _hsl_frame()
    out = R._repair_caiso_hsl_clock("CAISO", 2024, df)
    assert out is not df
    np.testing.assert_allclose(out["wind_gen_mw"], 7.0)
    np.testing.assert_allclose(out["wind_hsl_mw"], 17.0)
    np.testing.assert_allclose(out["solar_gen_mw"], 9.0)
    np.testing.assert_allclose(out["solar_hsl_mw"], 29.0)
    np.testing.assert_allclose(df["wind_gen_mw"], np.arange(HOURS_PER_YEAR))


def test_hsl_missing_repaired_frame_raises(monkeypatch):
    """Armed in-window with no repaired EIA-930 series: fail, never fall back."""
    F.set_caiso_eia930_clock_repair(True)
    monkeypatch.setattr(A, "load_eia_hourly_renewable_gen", lambda iso, y: None)
    with pytest.raises(RuntimeError, match="HSL generation term"):
        R._repair_caiso_hsl_clock("CAISO", 2024, _hsl_frame())


def _solar_centroid_by_month(gen: np.ndarray, year: int) -> np.ndarray:
    """Monthly solar centroid (h PST, hour-beginning + 0.5) on the frame clock."""
    utc = pd.DatetimeIndex(F._eia_hourly_frame_filled("CISO", year)["UTC time"])
    pst = utc - pd.Timedelta(hours=9)  # hour-ending UTC -> hour-beginning PST
    h, m = np.asarray(pst.hour) + 0.5, np.asarray(pst.month)
    return np.array(
        [(gen[m == k] * h[m == k]).sum() / gen[m == k].sum() for k in range(1, 13)]
    )


@requires_raw(_CAISO_HSL / "caiso_2024_hsl_hourly.parquet")
def test_live_hsl_precondition_file_gen_is_unarmed_loader():
    """The offline file's gen term IS the unarmed EIA-930 loader, 2019-2025."""
    for year in range(2019, 2026):
        df = R.load_hsl_hourly("CAISO", year)
        eia = A.load_eia_hourly_renewable_gen("CAISO", year)
        for fuel in ("wind", "solar"):
            np.testing.assert_array_equal(df[f"{fuel}_gen_mw"].to_numpy(), eia[fuel])


@requires_raw(_CAISO_HSL / "caiso_2024_hsl_hourly.parquet")
def test_live_hsl_armed_moves_solar_centroid_and_conserves_curtailment():
    """2024-25 solar centroid lands at 11.5-12.0 h PST every month; 2019-22 inert."""
    for year in range(2019, 2026):
        F.set_caiso_eia930_clock_repair(False)
        off = R.load_hsl_hourly("CAISO", year)
        F.set_caiso_eia930_clock_repair(True)
        on = R.load_hsl_hourly("CAISO", year)
        if year <= 2022:
            pd.testing.assert_frame_equal(on, off)
            continue
        for fuel in ("wind", "solar"):
            curt_on = (on[f"{fuel}_hsl_mw"] - on[f"{fuel}_gen_mw"]).sum()
            curt_off = (off[f"{fuel}_hsl_mw"] - off[f"{fuel}_gen_mw"]).sum()
            assert curt_on == pytest.approx(curt_off, rel=1e-12, abs=1e-6)
        if year >= 2024:
            c = _solar_centroid_by_month(on["solar_gen_mw"].to_numpy(), year)
            assert ((c >= 11.5) & (c <= 12.0 + 5e-3)).all(), c


# --- R-CAISO-15: the battery shape envelope (storage._caiso_storage_envelope_clock_repaired)


def test_envelope_unarmed_returns_none():
    """Off by default: the committed CSV row is used unchanged."""
    from market_sim.model import storage as S

    assert S._caiso_storage_envelope_clock_repaired(2024) is None


@requires_raw(_ENVELOPE, _CISO_EXTRACT)
def test_live_envelope_precondition_reproduces_committed_csv(monkeypatch):
    """On the UNREPAIRED extract the reader's derivation equals the CSV p95."""
    from market_sim.model import storage as S

    F.set_caiso_eia930_clock_repair(True)
    # Precondition probe: the same construction with the repair made a no-op.
    monkeypatch.setattr(F, "_repair_clock_late_windows", lambda df, ba: df)
    csv = pd.read_csv(_ENVELOPE)
    for year in (2023, 2024, 2025):
        chg, dis = S._caiso_storage_envelope_clock_repaired(year)
        row = csv[csv["year"] == year].sort_values("hod")
        np.testing.assert_array_equal(chg, row["chg_frac_p95"].to_numpy())
        np.testing.assert_array_equal(dis, row["dis_frac_p95"].to_numpy())


@requires_raw(_ENVELOPE, _CISO_EXTRACT)
def test_live_envelope_armed_moves_2024_2025_one_hour_earlier():
    """Armed 2024-25 caps are the committed caps rolled one hour earlier."""
    from market_sim.model import storage as S

    F.set_caiso_eia930_clock_repair(True)
    csv = pd.read_csv(_ENVELOPE)
    for year in (2024, 2025):
        chg, dis = S._caiso_storage_envelope_clock_repaired(year)
        row = csv[csv["year"] == year].sort_values("hod")
        # Correlation with the committed row shifted one hour earlier beats
        # correlation with the committed row itself.
        for new, col in ((chg, "chg_frac_p95"), (dis, "dis_frac_p95")):
            old = row[col].to_numpy()
            assert np.corrcoef(new, np.roll(old, -1))[0, 1] > 0.97
            assert (
                np.corrcoef(new, np.roll(old, -1))[0, 1] > np.corrcoef(new, old)[0, 1]
            )
    assert S._caiso_storage_envelope_clock_repaired(2022) is None


@requires_raw(_ENVELOPE, _CISO_EXTRACT)
def test_live_envelope_under_solve_year_vintage_matches_canonical_and_restores():
    """The keeper tracks the solve-year EIA-860 vintage: the envelope still uses
    the canonical fleet (the committed derivation's) and hands the solve's
    directory back unchanged (the R-CAISO-15 shard crash)."""
    from market_sim.config import paths as P
    from market_sim.model import storage as S

    F.set_caiso_eia930_clock_repair(True)
    P.set_eia860_vintage(None)
    canonical = S._caiso_storage_envelope_clock_repaired(2024)
    solve_dir = P.set_eia860_vintage(2024)
    try:
        assert solve_dir != P.EIA_860_DIR  # a year-matched vintage is active
        under_vintage = S._caiso_storage_envelope_clock_repaired(2024)
        assert P.active_eia860_dir() == solve_dir
    finally:
        P.set_eia860_vintage(None)
    np.testing.assert_array_equal(under_vintage[0], canonical[0])
    np.testing.assert_array_equal(under_vintage[1], canonical[1])


def test_benchmark_rebuild_arms_from_bundle_and_restores(tmp_path, monkeypatch):
    """A zero-LP benchmark rebuild uses the bundle's own clock-repair setting
    and leaves the process switch as it found it (R-CAISO-15 census)."""
    import json

    import scripts.run_calibration_full as rcf

    (tmp_path / "meta.json").write_text(json.dumps({"iso": "CAISO", "years": [2024]}))
    (tmp_path / "run_config.json").write_text(
        json.dumps({"scenario_config": {"caiso_eia930_clock_repair": True}})
    )
    seen = []
    monkeypatch.setattr(
        rcf,
        "_build_benchmark_frames",
        lambda b: seen.append(F.caiso_eia930_clock_repair_active()) or ("CAISO", {}),
    )
    assert rcf._bundle_caiso_clock_repair(tmp_path) is True
    rcf.build_benchmark_frames(tmp_path)
    assert seen == [True]
    assert F.caiso_eia930_clock_repair_active() is False
    (tmp_path / "meta.json").write_text(json.dumps({"iso": "ERCOT", "years": [2024]}))
    assert rcf._bundle_caiso_clock_repair(tmp_path) is False


def test_supply_consistent_term_excludes_ti(tmp_path, monkeypatch):
    """R-CAISO-16: the re-stamped caiso-80 term is NetGen - NG_cell; TI stays put."""
    from market_sim.config import paths as P

    pd.DataFrame(
        {"netgen_mw": [10.0, 20.0], "ng_cell_mw": [1.0, 2.0], "ti_mw": [100.0, 300.0]}
    ).to_csv(tmp_path / "caiso_supply_consistent_demand_2024.csv", index=False)
    monkeypatch.setattr(P, "CAISO_SUPPLY_CONSISTENT_DEMAND_DIR", tmp_path)
    np.testing.assert_allclose(D._supply_consistent_eia930_term(2024), [9.0, 18.0])


def test_live_armed_frame_ti_is_raw_and_matches_diba_feed():
    """Armed: CISO TI is byte-identical to unarmed, and still equals the per-DIBA
    feed summed on the pinned read-seam clock inside the late window."""
    from market_sim.data.eia930 import envelopes

    raw = F._eia_hourly_frame("CISO", 2024)
    if raw is None:
        pytest.skip("CISO extract not hydrated")
    F.set_caiso_eia930_clock_repair(True)
    armed = F._eia_hourly_frame("CISO", 2024)
    np.testing.assert_array_equal(
        armed["Total interchange"].to_numpy(), raw["Total interchange"].to_numpy()
    )
    assert not np.array_equal(
        armed["Net generation"].to_numpy(), raw["Net generation"].to_numpy()
    )
    from market_sim.config import paths as P

    path = P.RAW_DATA_DIR / "eia-930-interchange" / "CISO interchange hourly.parquet"
    ic = pd.read_parquet(path)
    s = ic.groupby("local_time", observed=True)["mw"].sum(min_count=1).sort_index()
    feed = pd.Series(
        s.to_numpy(),
        index=envelopes._caiso_interchange_model_clock(pd.DatetimeIndex(s.index)),
    )
    utc = pd.DatetimeIndex(armed["UTC time"])
    utc = utc.tz_convert("UTC").tz_localize(None) if utc.tz is not None else utc
    ti = pd.Series(
        armed["Total interchange"].to_numpy(float), index=utc - pd.Timedelta(hours=9)
    )
    j = pd.concat({"f": feed, "t": ti}, axis=1, join="inner").dropna()
    assert len(j) > 8000
    assert ((j["f"] - j["t"]).abs() < 1.0).mean() > 0.99
