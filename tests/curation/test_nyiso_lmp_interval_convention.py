"""Guard the NYISO LMP interval convention in ``derive_actual_lmp._nyiso_wide``.

NYISO labels its two zonal LBMP products on DIFFERENT clocks, and the builder
has to bin them differently:

* the 5-minute real-time export (P-24A ``realtime_zone``) stamps an interval by
  its **END**, so a stamp must be mapped back one instant before flooring;
* the hourly day-ahead export (``damlbmp_zone``) stamps its interval by its
  **BEGINNING**, so the same shift applied there would move every DA hour by
  one.

Getting this wrong is close to invisible — it moves ~95 % of hours while
shifting the annual mean by ~0.01 %, so no level statistic catches it — but it
mis-assigns every price by an hour, which is exactly what a per-hour scarcity
count (C3c) and any correlation-sensitive metric read. It was wrong on the RT
side until session nyiso-139 (2026-08-16). The convention is not a judgement
call: it is adjudicated against NYISO's own published time-weighted hourly
product P-4A, which Manual 12 p. 136 / Manual 14 §4 state is built from these
same 5-minute prices — ENDING agrees within P-4A's $0.005 rounding bound on all
14,905 strict zone-hours tested, BEGINNING is wrong on 14,174 of 14,828 by up
to $50.01 (``scripts/probes/nyiso_rtd_clock_adjudication.py --strict``).

Synthetic fixtures only — no staged archive is read, so this runs anywhere.
"""

from __future__ import annotations

import importlib.util
import io
import sys
import zipfile
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]


def _load_module():
    """Import ``scripts/data/derive_actual_lmp.py`` as a standalone module.

    It lives outside the installed package, so it is loaded by path rather
    than imported by name.
    """
    sys.path.insert(0, str(REPO / "src"))
    spec = importlib.util.spec_from_file_location(
        "_derive_actual_lmp_undertest",
        REPO / "scripts" / "data" / "derive_actual_lmp.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def dal():
    """The module under test."""
    return _load_module()


def _rt_csv(stamps: list[str], zone: str = "WEST", price: float = 10.0) -> bytes:
    """One daily RT CSV holding ``stamps`` for a single zone."""
    return (
        pd.DataFrame(
            {
                "Time Stamp": stamps,
                "Name": zone,
                "LBMP ($/MWHr)": [price] * len(stamps),
            }
        )
        .to_csv(index=False)
        .encode()
    )


def _stage_rt(tmp: Path, year: int, csv: bytes) -> None:
    """Write one monthly RT zip where ``_nyiso_wide``'s glob will find it."""
    d = tmp / "NYISO"
    d.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(d / f"{year}0601realtime_zone_csv.zip", "w") as z:
        z.writestr(f"{year}0601realtime_zone.csv", csv)


def test_rt_five_minute_stamps_are_interval_ending(dal, tmp_path, monkeypatch):
    """The 12 stamps 00:05..01:00 price hour 00, NOT hour 01.

    Under the old interval-BEGINNING reading, 00:05..00:55 would land in hour
    00 and the 01:00 stamp would open hour 01 — leaving a spurious one-sample
    hour 01 and a hour 00 built from 11 samples instead of 12.
    """
    stamps = [f"06/01/2024 00:{m:02d}:00" for m in range(5, 60, 5)] + [
        "06/01/2024 01:00:00"
    ]
    assert len(stamps) == 12
    _stage_rt(tmp_path, 2024, _rt_csv(stamps))
    monkeypatch.setattr(dal, "LMP_DIR", tmp_path)

    wide = dal._nyiso_wide(2024, "rt")

    assert wide is not None
    # Exactly one hour is formed, from all twelve intervals.
    assert len(wide) == 1, f"expected a single whole hour, got {wide.index.tolist()}"
    # 2024-06-01 00:00 EDT (UTC-4) == 04:00Z.
    assert wide.index[0] == pd.Timestamp("2024-06-01 04:00", tz="UTC")


def test_rt_top_of_hour_stamp_closes_the_previous_hour(dal, tmp_path, monkeypatch):
    """A stamp at exactly HH:00:00 belongs to hour HH-1, not hour HH."""
    _stage_rt(tmp_path, 2024, _rt_csv(["06/01/2024 05:00:00"]))
    monkeypatch.setattr(dal, "LMP_DIR", tmp_path)

    wide = dal._nyiso_wide(2024, "rt")

    assert wide is not None
    # 04:00 EDT == 08:00Z; the stamp closes 04:00-05:00 local, so it must NOT
    # land on 05:00 local (09:00Z).
    assert wide.index[0] == pd.Timestamp("2024-06-01 08:00", tz="UTC")


def test_da_hourly_stamps_are_not_shifted(dal, tmp_path, monkeypatch):
    """The DA branch must be exempt: its stamps already label the hour start.

    Applying the RT shift here would move every day-ahead hour back by one and
    silently corrupt the ``da`` column (and the import ladder derived from it).
    """
    d = tmp_path / "NYISO"
    d.mkdir(parents=True, exist_ok=True)
    inner = io.BytesIO()
    with zipfile.ZipFile(inner, "w") as z:
        z.writestr(
            "20240601damlbmp_zone.csv",
            pd.DataFrame(
                {
                    "Time Stamp": ["06/01/2024 05:00"],
                    "Name": ["WEST"],
                    "LBMP ($/MWHr)": [42.0],
                }
            )
            .to_csv(index=False)
            .encode(),
        )
    with zipfile.ZipFile(d / "NYISO_zonal_hourly.zip", "w") as outer:
        outer.writestr("20240601damlbmp_zone_csv.zip", inner.getvalue())
    monkeypatch.setattr(dal, "LMP_DIR", tmp_path)

    wide = dal._nyiso_wide(2024, "da")

    assert wide is not None
    # 05:00 EDT == 09:00Z, unshifted.
    assert wide.index[0] == pd.Timestamp("2024-06-01 09:00", tz="UTC")
    assert float(wide.iloc[0]["WEST"]) == pytest.approx(42.0)
