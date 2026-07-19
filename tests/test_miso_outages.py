"""Tests for the MISO-native published-outage overlay (market_sim.data.miso_outages).

Trivial cases first (repo rule): the pure fetch-script helpers on synthetic
rows, then the loader on synthetic committed wide CSVs, then the derate
interface. No network, no real MISO files.

(The `ScenarioConfig.miso_native_outage_source` gate + the `fleet.py` seam that
select this overlay in a solve are a paste-ready follow-up in
``docs/handoffs/miso-native-outage-wiring-2026-07.md`` — not applied to the
solve path in the intake commit — so the gate/cache-key assertions live there,
not here.)
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts" / "data"))

import fetch_miso_outages as fetch  # noqa: E402

from market_sim.config.constants import HOURS_PER_YEAR  # noqa: E402
from market_sim.data import miso_outages as mo  # noqa: E402
from market_sim.data.outages import _hour_of_year  # noqa: E402


# --------------------------------------------------------------------------- #
# Fetch-script pure helpers
# --------------------------------------------------------------------------- #
def test_parse_date_header_variants():
    assert fetch._parse_date_header("6/16/24 **") == date(2024, 6, 16)
    assert fetch._parse_date_header("6/16/24 ") == date(2024, 6, 16)
    assert fetch._parse_date_header("1/2/2025") == date(2025, 1, 2)
    assert fetch._parse_date_header(None) is None
    assert fetch._parse_date_header("") is None
    assert fetch._parse_date_header("not a date") is None


def test_settle_estimated_keeps_latest_publish():
    # Same (region, type, interval) published twice — the later publish (the
    # more-settled estimate) must win.
    rows = [
        {
            "publish_date": date(2024, 6, 1),
            "region": "MISO",
            "cause_type": "Forced",
            "interval_date": date(2024, 5, 20),
            "outage_mw": 100.0,
        },
        {
            "publish_date": date(2024, 6, 15),
            "region": "MISO",
            "cause_type": "Forced",
            "interval_date": date(2024, 5, 20),
            "outage_mw": 250.0,
        },
    ]
    out = fetch._settle_estimated(rows)
    assert len(out) == 1
    assert float(out.iloc[0]["outage_mw"]) == 250.0
    assert out.iloc[0]["publish_date"] == date(2024, 6, 15)


def test_settle_estimated_empty():
    out = fetch._settle_estimated([])
    assert out.empty
    assert set(["interval_date", "region", "cause_type", "outage_mw"]).issubset(
        out.columns
    )


# --------------------------------------------------------------------------- #
# Loader: synthetic committed CSVs (the in-repo form)
# --------------------------------------------------------------------------- #
def _write_synthetic(tmp_dir: Path, rows: list[dict]) -> None:
    """Write ``rows`` (long dicts) as per-year wide CSVs in ``tmp_dir``.

    Mirrors the committed form: ``interval_date`` + ``<Region>_<CauseType>``
    columns, one file per year. Empty ``rows`` writes nothing (loader -> None).
    """
    if not rows:
        return
    df = pd.DataFrame(rows)
    df["interval_date"] = pd.to_datetime(df["interval_date"])
    df["col"] = df["region"].astype(str) + "_" + df["cause_type"].astype(str)
    wide = df.pivot_table(index="interval_date", columns="col", values="outage_mw")
    wide = wide.round().astype("Int64")
    for year, sub in wide.groupby(wide.index.year):
        sub = sub.copy()
        sub.index = sub.index.date
        sub.to_csv(
            tmp_dir / f"miso_outages_estimated_{int(year)}.csv",
            index_label="interval_date",
        )


@pytest.fixture
def _patch_data(tmp_path, monkeypatch):
    """Point the loader at synthetic committed CSVs and clear caches.

    Monkeypatches ``MISO_OUTAGES_DIR`` to an isolated tmp dir (so the real
    committed CSVs never leak in) and ``ESTIMATED_PARQUET`` to a nonexistent path
    (so the CSV read path — the committed form — is what gets exercised).
    """

    def _install(rows):
        _write_synthetic(tmp_path, rows)
        monkeypatch.setattr(mo, "MISO_OUTAGES_DIR", tmp_path)
        monkeypatch.setattr(mo, "ESTIMATED_PARQUET", tmp_path / "none.parquet")
        mo._load_estimated.cache_clear()
        mo.miso_outage_mw_series.cache_clear()
        mo.miso_native_outage_derate_factors.cache_clear()
        mo._miso_thermal_capacity_mw.cache_clear()

    yield _install
    mo._load_estimated.cache_clear()
    mo.miso_outage_mw_series.cache_clear()
    mo.miso_native_outage_derate_factors.cache_clear()
    mo._miso_thermal_capacity_mw.cache_clear()


def test_mw_series_sums_types_and_broadcasts(_patch_data):
    # One interval day (2024-03-04), two cause types for MISO. The series must
    # sum the requested types over that day's 24-hour block, zero elsewhere.
    rows = [
        {
            "publish_date": date(2024, 3, 10),
            "region": "MISO",
            "cause_type": "Forced",
            "interval_date": date(2024, 3, 4),
            "outage_mw": 1000.0,
        },
        {
            "publish_date": date(2024, 3, 10),
            "region": "MISO",
            "cause_type": "Planned",
            "interval_date": date(2024, 3, 4),
            "outage_mw": 500.0,
        },
        # A different region on the same day must not leak into the MISO series.
        {
            "publish_date": date(2024, 3, 10),
            "region": "North",
            "cause_type": "Forced",
            "interval_date": date(2024, 3, 4),
            "outage_mw": 777.0,
        },
    ]
    _patch_data(rows)
    s = mo.miso_outage_mw_series(2024, "MISO")  # default = all four types
    lo = _hour_of_year(3, 4, 0)
    assert s.shape == (HOURS_PER_YEAR,)
    assert s[lo : lo + 24].tolist() == [1500.0] * 24  # 1000 Forced + 500 Planned
    assert s[:lo].sum() == 0.0 and s[lo + 24 :].sum() == 0.0
    # Restrict to a single type.
    s_forced = mo.miso_outage_mw_series(2024, "MISO", ("Forced",))
    assert s_forced[lo] == 1000.0


def test_mw_series_absent_file_is_zeros(tmp_path, monkeypatch):
    # No parquet and an empty data dir (no CSVs) -> loader None -> all-zero.
    monkeypatch.setattr(mo, "MISO_OUTAGES_DIR", tmp_path)
    monkeypatch.setattr(mo, "ESTIMATED_PARQUET", tmp_path / "missing.parquet")
    mo._load_estimated.cache_clear()
    mo.miso_outage_mw_series.cache_clear()
    s = mo.miso_outage_mw_series(2024, "MISO")
    assert s.shape == (HOURS_PER_YEAR,)
    assert not s.any()
    mo._load_estimated.cache_clear()
    mo.miso_outage_mw_series.cache_clear()


def test_available_years(_patch_data):
    rows = [
        {
            "publish_date": date(2024, 1, 5),
            "region": "MISO",
            "cause_type": "Forced",
            "interval_date": date(2024, 1, 1),
            "outage_mw": 10.0,
        },
        {
            "publish_date": date(2025, 1, 5),
            "region": "MISO",
            "cause_type": "Forced",
            "interval_date": date(2025, 1, 1),
            "outage_mw": 20.0,
        },
    ]
    _patch_data(rows)
    assert mo.miso_outage_available_years() == [2024, 2025]


# --------------------------------------------------------------------------- #
# Derate interface (aggregate envelope)
# --------------------------------------------------------------------------- #
def test_native_derate_factors_interface(_patch_data, monkeypatch):
    rows = [
        {
            "publish_date": date(2024, 3, 10),
            "region": "MISO",
            "cause_type": "Forced",
            "interval_date": date(2024, 3, 4),
            "outage_mw": 2000.0,
        },
    ]
    _patch_data(rows)
    # Small synthetic MISO thermal fleet: two bins totaling 10 000 MW.
    fake_cap = {
        (100, "COAL"): 6000.0,
        (200, "CC_REGULAR"): 4000.0,
        (300, "WIND"): 5000.0,
    }
    from market_sim.data import outages as outages_mod

    monkeypatch.setattr(outages_mod, "_iso_plant_capacity", lambda iso: fake_cap)
    mo._miso_thermal_capacity_mw.cache_clear()
    mo.miso_native_outage_derate_factors.cache_clear()

    fac = mo.miso_native_outage_derate_factors(2024, cause_types=("Forced",))
    # WIND is not a thermal group -> excluded; two thermal bins get the envelope.
    assert set(fac.keys()) == {(100, "COAL"), (200, "CC_REGULAR")}
    lo = _hour_of_year(3, 4, 0)
    # Denominator = thermal capacity only (10 000 MW): 1 - 2000/10000 = 0.8.
    assert fac[(100, "COAL")][lo] == pytest.approx(0.8)
    assert fac[(200, "CC_REGULAR")][lo] == pytest.approx(0.8)
    # Uniform envelope: every thermal bin shares the same series.
    assert np.array_equal(fac[(100, "COAL")], fac[(200, "CC_REGULAR")])
    # Outside the outage day the envelope is fully available.
    assert fac[(100, "COAL")][0] == pytest.approx(1.0)


def test_native_derate_non_miso_is_empty(_patch_data):
    _patch_data(
        [
            {
                "publish_date": date(2024, 3, 10),
                "region": "MISO",
                "cause_type": "Forced",
                "interval_date": date(2024, 3, 4),
                "outage_mw": 2000.0,
            },
        ]
    )
    assert mo.miso_native_outage_derate_factors(2024, iso="ERCOT") == {}


def test_native_derate_no_outage_is_empty(_patch_data):
    # Data exists but carries no MISO-region rows for the year -> the system
    # offline series is all-zero -> the derate is a clean no-op.
    _patch_data(
        [
            {
                "publish_date": date(2024, 3, 10),
                "region": "North",
                "cause_type": "Forced",
                "interval_date": date(2024, 3, 4),
                "outage_mw": 500.0,
            },
        ]
    )
    assert mo.miso_native_outage_derate_factors(2024) == {}
