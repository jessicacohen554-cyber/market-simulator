"""Derive actual historical average LMP per ISO/year for the dashboard.

The backcast dashboard's summary page compares the model's average LMP against
the actual historical market price. Parsing the raw ERCOT settlement-point
workbooks (20+ MB xlsx, 15-minute real-time intervals) on every dashboard
render would be slow and would pull ``openpyxl`` into the render path, so this
script reduces the raw price files to a tiny committed reference,
``data/raw/_validation-source/actual_lmp.json``:

    {"ERCOT": {"2024": {"da": 28.09, "rt": 26.83,
                        "da_mon": [...12...], "rt_mon": [...12...],
                        "src": "..."}, ...},
     "PJM":   {"2024": {"da": 29.78, "rt": 29.53,
                        "da_pct": {"min": ..., "p1": ..., ..., "max": ...},
                        "rt_pct": {...}, ...}, ...}}

``da`` / ``rt`` are the annual mean day-ahead / real-time price in $/MWh, and
``da_mon`` / ``rt_mon`` the 12 monthly means (Jan-Dec; ``null`` for a month with
no data) feeding the summary page's monthly LMP table. All are taken from the
system-wide hub-average series of each market:

  * ERCOT — ``HB_HUBAVG`` settlement point in the DAM (hourly) and RTM
    (15-minute) Load-Zone/Hub settlement-point-price reports.
  * PJM — the mean across the 12 trading hubs in the hourly RT/DA LMP export.
  * CAISO — the three trading hubs (TH_NP15/TH_ZP26/TH_SP15) in the OASIS
    hourly aggregates (``scripts/postprocess_oasis_downloads.py``),
    load-weighted by zone share into a system price. DA is 2024-2025 only
    and RT 2024-2025 only: OASIS's ~39-month retention had already aged out
    most of 2023 DAM by the mid-2026 pull (only a few Feb-2023 trade dates
    survive), and 2023 RTM was never fetched.
  * NYISO — the eleven zonal LBMPs (DAM hourly / RTD 5-minute averaged to the
    hour) from ``NYISO/``. The system price is the simple mean of the eleven
    *internal* zones (the H Q / NPX / O H / PJM external-proxy buses are
    excluded); the five model zones are the simple mean of their constituent
    NYISO zones.
  * NEISO — the ISO-NE SMD ``*_smd_hourly.xlsx`` per-zone sheets (hourly
    ``DA_LMP`` / ``RT_LMP``) from ``NEISO/``. The system price is the
    ``.H.INTERNAL_HUB`` ("ISO NE CA" sheet); the four model zones are the
    simple mean of their constituent SMD load zones.

The two zonal ISOs (NYISO, NEISO) additionally carry a ``zones`` sub-dict —
``{model_zone: {da, rt, da_mon, rt_mon}}`` — alongside the hub-level
``da``/``rt``/``*_mon``/``*_pct``; the dashboard reads only the top-level hub
fields, so the sub-dict is additive and leaves the ERCOT/PJM/CAISO blocks
byte-identical.

For ISOs with a true hourly source (PJM, CAISO, and ERCOT — the ERCOT
HB_HUBAVG hub-average is itself the comparable system price, from the DAM
hourly and the RTM 15-minute intervals averaged to the hour), two extras are
produced for the price-duration-curve overlay (J3a):

  * ``da_pct`` / ``rt_pct`` in the JSON — duration-curve percentiles of the
    hub-mean hourly price (``p99`` is a high price, ``p1`` a low one).
  * ``data/raw/_validation-source/actual_lmp_hourly_{ISO}.parquet`` — the hub-mean
    hourly series itself (columns ``year``, ``hour``, ``rt``, ``da``), dense
    on the model's fixed 8760-hour local calendar: Feb 29 is dropped, the
    DST fall-back hour is averaged, and the spring-forward hour is NaN.

Run after refreshing ``data/raw/lmp-data/``; commit the JSON and the
hourly parquet. Missing source files for an ISO/year are skipped, so a
partial data drop still produces a valid reference.

Usage:
    python scripts/derive_actual_lmp.py [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
from market_sim.config import paths  # noqa: E402  (resolves the data root)

# Paths resolve through config/paths.py (CLAUDE.md: never hardcode the legacy
# inputs/ tree — the W1 relocation collapsed inputs/raw-data -> data/raw and
# inputs/calibration -> data/raw/_validation-source).
LMP_DIR = paths.RAW_DATA_DIR / "lmp-data"
OUT = paths.CALIBRATION_DIR / "actual_lmp.json"
HOURLY_OUT = paths.CALIBRATION_DIR  # actual_lmp_hourly_{ISO}.parquet

DEFAULT_YEARS = (2023, 2024, 2025)

PJM_SRC = "PJM RT/DA LMP, mean of the 12 trading hubs (hourly)"
ERCOT_SRC = "ERCOT HB_HUBAVG settlement point price (DAM hourly / RTM 15-min)"
CAISO_SRC = (
    "CAISO OASIS hub LMPs (PRC_LMP DAM / PRC_INTVL_LMP RTM hourly), "
    "load-weighted across TH_NP15/TH_ZP26/TH_SP15"
)
NYISO_SRC = (
    "NYISO zonal LBMP (DAM hourly / RTD 5-min averaged to the hour); "
    "hub is the simple mean of the 11 internal zones, model zones the "
    "simple mean of their constituent NYISO zones"
)
NEISO_SRC = (
    "ISO-NE SMD hourly DA_LMP / RT_LMP; hub is the .H.INTERNAL_HUB "
    "(ISO NE CA sheet), model zones the simple mean of their "
    "constituent SMD load zones"
)

# CAISO has no single system hub; the comparable-to-the-model "system price"
# is the three trading hubs load-weighted by their zone shares (the same
# static ``load_share`` values in ``config.iso_configs``; WECC_import is 0).
CAISO_HUB_WEIGHTS = {
    "TH_NP15_GEN-APND": 0.3969,
    "TH_ZP26_GEN-APND": 0.0646,
    "TH_SP15_GEN-APND": 0.5385,
}
# CISO localizes to Pacific prevailing time, like the model's dispatch clock
# (``scripts/convert_eia930.py`` BA_TIMEZONES["CISO"], ``eia_loader``).
CAISO_TZ = "America/Los_Angeles"
# Minimum valid system-hours to emit a CAISO year. OASIS's ~39-month retention
# aged out CAISO DAM/RTM before ~2023-03-10 (probed 2026-06-22: ERR 1000 before
# Mar 10, data from Mar 10 on), so the deepest 2023 reference we can fetch is
# Mar-Dec (~7.1k DAM / ~7.3k RTM hours). The guard sits below that span so the
# partial-but-substantial 2023 year scores (Jan-Feb stay NaN in the dense
# series and simply don't contribute), while still rejecting a true stub.
CAISO_MIN_HOURS = 6500

# Duration-curve percentile levels for the ``da_pct`` / ``rt_pct`` records.
_PCT_LEVELS = (1, 5, 10, 25, 50, 75, 90, 95, 99)

# The model's fixed non-leap dispatch calendar (matches
# market_sim.data.campd: Feb 29 is dropped, hours are local clock).
_HOURS_PER_YEAR = 8760
_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR = tuple(int(sum(_DAYS_IN_MONTH[:m]) * 24) for m in range(12))


def _by_month(values, months) -> list:
    """12 monthly means ($/MWh, rounded) from a value series labelled by month.

    ``months`` is a 1-12 month label per row; empty months come back ``None``.
    """
    out: list = [None] * 12
    g = pd.Series(list(values)).groupby(list(months)).mean()
    for m, v in g.items():
        if pd.notna(m) and 1 <= int(m) <= 12 and pd.notna(v):
            out[int(m) - 1] = round(float(v), 2)
    return out


def _hour_index(ts: pd.Series) -> np.ndarray:
    """Map local timestamps to the fixed non-leap hour-of-year, Feb 29 -> -1."""
    idx = (
        np.asarray([_MONTH_START_HOUR[m - 1] for m in ts.dt.month])
        + (ts.dt.day.to_numpy() - 1) * 24
        + ts.dt.hour.to_numpy()
    )
    return np.where((ts.dt.month == 2) & (ts.dt.day == 29), -1, idx)


def _pct(values: np.ndarray) -> dict:
    """Duration-curve summary of an hourly price series (NaNs ignored)."""
    out = {"min": round(float(np.nanmin(values)), 2)}
    for p in _PCT_LEVELS:
        out[f"p{p}"] = round(float(np.nanpercentile(values, p)), 2)
    out["max"] = round(float(np.nanmax(values)), 2)
    return out


def _hub_mean_hourly(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Hub-mean hourly RT/DA series on the dense fixed 8760-hour calendar.

    The raw export is one row per hub per local (EPT) hour. The hub mean is
    taken first, then wall-clock hours are placed on the model's non-leap
    local calendar: Feb 29 is dropped, the duplicated DST fall-back hour
    averages its two instances, and the missing spring-forward hour is NaN.
    """
    ts = pd.to_datetime(
        df["datetime_beginning_ept"], format="%m/%d/%Y %I:%M:%S %p", errors="coerce"
    )
    g = (
        df.assign(hour=_hour_index(ts))
        .query("hour >= 0")
        .groupby("hour")[["total_lmp_rt", "total_lmp_da"]]
        .mean()
    )
    dense = g.reindex(range(_HOURS_PER_YEAR))
    return pd.DataFrame(
        {
            "year": np.int16(year),
            "hour": np.arange(_HOURS_PER_YEAR, dtype=np.int16),
            "rt": dense["total_lmp_rt"].to_numpy(np.float32),
            "da": dense["total_lmp_da"].to_numpy(np.float32),
        }
    )


def _pjm(year: int) -> tuple[dict, pd.DataFrame] | None:
    """Return ``(record, hourly)`` for PJM, or ``None`` if the file is absent.

    ``record`` is the ``{da, rt, da_mon, rt_mon, da_pct, rt_pct, src}`` JSON
    entry; ``hourly`` the dense hub-mean hourly frame for the parquet sidecar.
    """
    f = LMP_DIR / f"PJM_{year}_rt_da_monthly_lmps.csv"
    if not f.exists():
        return None
    df = pd.read_csv(
        f, usecols=["datetime_beginning_ept", "total_lmp_rt", "total_lmp_da"]
    )
    mon = pd.to_datetime(
        df["datetime_beginning_ept"], format="%m/%d/%Y %I:%M:%S %p", errors="coerce"
    ).dt.month
    hourly = _hub_mean_hourly(df, year)
    rec = {
        "da": round(float(df["total_lmp_da"].mean()), 2),
        "rt": round(float(df["total_lmp_rt"].mean()), 2),
        "da_mon": _by_month(df["total_lmp_da"], mon),
        "rt_mon": _by_month(df["total_lmp_rt"], mon),
        "da_pct": _pct(hourly["da"].to_numpy(float)),
        "rt_pct": _pct(hourly["rt"].to_numpy(float)),
        "src": PJM_SRC,
    }
    return rec, hourly


def _caiso_system_series(name: str, year: int) -> pd.Series | None:
    """Load-weighted CAISO hub system price, indexed by local Pacific time.

    ``name`` is the aggregate stem (``dam`` or ``rtm``). The per-year hourly
    aggregate (``scripts/postprocess_oasis_downloads.py``) is pivoted to one
    column per hub, weighted by ``CAISO_HUB_WEIGHTS`` into a single system
    price, and reindexed onto the Pacific wall clock. Returns ``None`` when
    the aggregate is missing, lacks a hub, or carries fewer than
    ``CAISO_MIN_HOURS`` complete hours — i.e. cannot stand for a year (the
    retention-aged 2023 DAM stub and the unfetched 2023 RTM).
    """
    path = LMP_DIR / "CAISO" / f"CAISO_{name}_hourly_{year}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, usecols=["interval_start_gmt", "node", "LMP"])
    wide = df.pivot_table(
        index="interval_start_gmt", columns="node", values="LMP", aggfunc="mean"
    )
    if not set(CAISO_HUB_WEIGHTS) <= set(wide.columns):
        return None
    wide = wide[list(CAISO_HUB_WEIGHTS)].dropna()
    if len(wide) < CAISO_MIN_HOURS:
        return None
    w = np.array(list(CAISO_HUB_WEIGHTS.values()))
    price = wide.to_numpy() @ (w / w.sum())
    ts = pd.to_datetime(wide.index, utc=True).tz_convert(CAISO_TZ)
    return pd.Series(price, index=ts, name="price")


def _caiso_densify(ser: pd.Series) -> np.ndarray:
    """Dense fixed-8760 array from a Pacific-time-indexed price series.

    Feb 29 is dropped, the DST fall-back hour averages its two instances and
    the missing spring-forward hour is NaN — the same calendar as
    :func:`_hub_mean_hourly`.
    """
    hour = _hour_index(pd.Series(ser.index))
    g = pd.Series(ser.to_numpy()).groupby(hour).mean()
    g = g[g.index >= 0]
    return g.reindex(range(_HOURS_PER_YEAR)).to_numpy(float)


def _caiso(year: int) -> tuple[dict, pd.DataFrame] | None:
    """Return ``(record, hourly)`` for CAISO, or ``None`` if no usable year.

    Mirrors :func:`_pjm`: the ``{da, rt, da_mon, rt_mon, da_pct, rt_pct,
    src}`` record uses the load-weighted hub system price, and ``hourly`` is
    the dense system series for the parquet sidecar. DA and RT are emitted
    independently, so a year present in DAM but not RTM still produces a
    record (as ERCOT 2025 does with RT only).
    """
    series = {
        "da": _caiso_system_series("dam", year),
        "rt": _caiso_system_series("rtm", year),
    }
    if series["da"] is None and series["rt"] is None:
        return None
    parts: dict = {}
    dense: dict[str, np.ndarray] = {}
    for key, ser in series.items():
        if ser is None:
            dense[key] = np.full(_HOURS_PER_YEAR, np.nan)
            continue
        d = _caiso_densify(ser)
        dense[key] = d
        parts[key] = round(float(ser.mean()), 2)
        parts[f"{key}_mon"] = _by_month(ser.to_numpy(), pd.Series(ser.index).dt.month)
        parts[f"{key}_pct"] = _pct(d)
    rec = {
        k: parts[k]
        for k in ("da", "rt", "da_mon", "rt_mon", "da_pct", "rt_pct")
        if k in parts
    }
    rec["src"] = CAISO_SRC
    hourly = pd.DataFrame(
        {
            "year": np.int16(year),
            "hour": np.arange(_HOURS_PER_YEAR, dtype=np.int16),
            "rt": dense["rt"].astype(np.float32),
            "da": dense["da"].astype(np.float32),
        }
    )
    return rec, hourly


def _month_of(v) -> int | None:
    """Month (1-12) from an ERCOT date cell (``MM/DD/YYYY`` or a datetime)."""
    if v is None:
        return None
    if hasattr(v, "month"):
        return int(v.month)
    try:
        return int(str(v).strip().split("/")[0])
    except (ValueError, IndexError):
        return None


def _month_day(v) -> tuple[int, int] | None:
    """``(month, day)`` from an ERCOT date cell (``MM/DD/YYYY`` or a datetime)."""
    if v is None:
        return None
    if hasattr(v, "month"):
        return int(v.month), int(v.day)
    try:
        p = str(v).strip().split("/")
        return int(p[0]), int(p[1])
    except (ValueError, IndexError):
        return None


def _ercot_hubavg(
    zip_glob: str, name_col: int, price_col: int, hod_col: int, hod_kind: str
) -> dict | None:
    """``HB_HUBAVG`` annual/monthly means + dense hourly series for a workbook.

    Args:
        zip_glob: Glob (under ``LMP_DIR``) selecting the report zip.
        name_col: Zero-based column index of the settlement-point name.
        price_col: Zero-based column index of the settlement-point price.
        hod_col: Zero-based column index of the hour-of-day field — the DAM
            "Hour Ending" (``HH:00``) string or the RTM "Delivery Hour" (1-24)
            integer; hour-of-day is the field minus one (hour-beginning, the
            PJM convention).
        hod_kind: ``"he"`` for the DAM ``HH:00`` string, ``"int"`` for the RTM
            1-24 integer.

    Returns:
        ``{"ann": annual_mean, "mon": [12 monthly means or None],
        "hourly": np.ndarray[8760]}`` over every HB_HUBAVG row (the report's
        date column, index 0, gives the month/day), or ``None`` when no
        matching zip is present. The annual/monthly means weight every raw row
        equally (15-minute intervals for RTM, including Feb 29 and the
        duplicated DST fall-back hour) — unchanged from the pre-hourly code.
        The ``hourly`` series instead lands on the model's fixed non-leap local
        calendar: Feb 29 is dropped, the RTM 15-minute intervals and the
        duplicated DST fall-back hour average into their hour, and the missing
        spring-forward hour stays NaN.
    """
    paths = sorted(LMP_DIR.glob(zip_glob))
    if not paths:
        return None
    with zipfile.ZipFile(paths[0]) as z:
        inner = next(n for n in z.namelist() if n.endswith(".xlsx"))
        data = z.read(inner)
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    msum, mcnt = [0.0] * 12, [0] * 12
    hsum = np.zeros(_HOURS_PER_YEAR)
    hcnt = np.zeros(_HOURS_PER_YEAR, dtype=np.int64)
    for sheet in wb.sheetnames:
        rows = wb[sheet].iter_rows(values_only=True)
        next(rows, None)  # header
        for r in rows:
            if r is None or len(r) <= price_col:
                continue
            if r[name_col] == "HB_HUBAVG" and r[price_col] is not None:
                price = float(r[price_col])
                mo = _month_of(r[0])
                if mo is None:
                    continue
                msum[mo - 1] += price
                mcnt[mo - 1] += 1
                md = _month_day(r[0])
                if md is None:
                    continue
                m, d = md
                if m == 2 and d == 29:  # model calendar drops Feb 29
                    continue
                hod = (
                    int(str(r[hod_col]).split(":")[0]) - 1
                    if hod_kind == "he"
                    else int(r[hod_col]) - 1
                )
                hoy = _MONTH_START_HOUR[m - 1] + (d - 1) * 24 + hod
                if 0 <= hoy < _HOURS_PER_YEAR:
                    hsum[hoy] += price
                    hcnt[hoy] += 1
    wb.close()
    n = sum(mcnt)
    if not n:
        return None
    mon = [round(msum[i] / mcnt[i], 2) if mcnt[i] else None for i in range(12)]
    hourly = np.where(hcnt > 0, hsum / np.where(hcnt > 0, hcnt, 1), np.nan)
    return {"ann": sum(msum) / n, "mon": mon, "hourly": hourly}


def _ercot(year: int) -> tuple[dict, pd.DataFrame] | None:
    """Return ``(record, hourly)`` for ERCOT, or ``None`` if no usable year.

    Mirrors :func:`_pjm`: the ``{da, rt, da_mon, rt_mon, da_pct, rt_pct, src}``
    record uses the ``HB_HUBAVG`` hub-average price (itself the comparable ERCOT
    system price), and ``hourly`` is the dense series for the parquet sidecar.
    DA and RT are emitted independently, so 2025 — RT only, no DAM workbook —
    still produces a record (its ``da`` column is all-NaN).
    """
    # DAM columns: Date, Hour Ending, Repeated, Settlement Point(3), Price(4).
    da = _ercot_hubavg(f"*DAMLZHBSPP_{year}*.zip", 3, 4, 1, "he")
    # RTM columns: Date, Hour, Interval, Repeated, Name(4), Type, Price(6).
    rt = _ercot_hubavg(f"*RTMLZHBSPP_{year}*.zip", 4, 6, 1, "int")
    if da is None and rt is None:
        return None
    out: dict = {"src": ERCOT_SRC}
    da_h = da["hourly"] if da is not None else np.full(_HOURS_PER_YEAR, np.nan)
    rt_h = rt["hourly"] if rt is not None else np.full(_HOURS_PER_YEAR, np.nan)
    if da is not None:
        out["da"], out["da_mon"] = round(da["ann"], 2), da["mon"]
        out["da_pct"] = _pct(da_h)
    if rt is not None:
        out["rt"], out["rt_mon"] = round(rt["ann"], 2), rt["mon"]
        out["rt_pct"] = _pct(rt_h)
    hourly = pd.DataFrame(
        {
            "year": np.int16(year),
            "hour": np.arange(_HOURS_PER_YEAR, dtype=np.int16),
            "rt": rt_h.astype(np.float32),
            "da": da_h.astype(np.float32),
        }
    )
    return out, hourly


# ── NYISO / NEISO (zonal) ───────────────────────────────────────────────────
# NYISO publishes eleven load zones; the model folds them into five. The four
# external-proxy buses (H Q Hydro-Québec, NPX New England, O H Ontario, PJM)
# are excluded from the internal-zone system price — they are import nodes, not
# NY load zones (they can sanity-check the P9 import tie, out of scope here).
NYISO_INTERNAL = (
    "WEST",
    "GENESE",
    "CENTRL",
    "NORTH",
    "MHK VL",
    "CAPITL",
    "HUD VL",
    "MILLWD",
    "DUNWOD",
    "N.Y.C.",
    "LONGIL",
)
NYISO_ZONE_MAP: dict[str, list[str]] = {
    "Upstate_West": ["WEST", "GENESE", "CENTRL", "NORTH", "MHK VL"],
    "Capital_Hudson": ["CAPITL"],
    "Lower_Hudson": ["HUD VL", "MILLWD", "DUNWOD"],
    "NYC": ["N.Y.C."],
    "Long_Island": ["LONGIL"],
}

# ISO-NE SMD per-zone sheets folded into the four model zones; the hub is the
# system "ISO NE CA" sheet (.H.INTERNAL_HUB). In every SMD sheet DA_LMP is
# column 4 and RT_LMP column 8 (0-based), and Hr_End ("01".."24") is
# hour-ending, so hour-beginning is the field minus one. The workbook uses a
# fixed 24-hour-per-day clock (no DST 23/25-hour days; leap years carry Feb 29).
NEISO_HUB_SHEET = "ISO NE CA"
NEISO_DA_COL, NEISO_RT_COL = 4, 8
NEISO_ZONE_MAP: dict[str, list[str]] = {
    "North": ["ME", "NH", "VT"],
    "Central": ["WCMA", "SEMA", "RI"],
    "Boston": ["NEMA"],
    "Connecticut": ["CT"],
}


def _read_nyiso_csv(data: bytes) -> pd.DataFrame:
    """Parse one NYISO daily zone CSV's timestamp / name / price columns."""
    return pd.read_csv(
        io.BytesIO(data), usecols=["Time Stamp", "Name", "LBMP ($/MWHr)"]
    ).rename(columns={"LBMP ($/MWHr)": "lmp"})


def _nyiso_wide(year: int, kind: str) -> pd.DataFrame | None:
    """Hourly per-internal-zone NYISO LBMP wide frame for ``year`` / ``kind``.

    ``kind`` is ``"da"`` — the day-ahead monthly ``damlbmp_zone`` zips inside
    ``NYISO_zonal_hourly.zip``, already hourly — or ``"rt"`` — the flat monthly
    ``realtime_zone`` zips, 5-minute, averaged to the hour. Columns are the
    eleven internal zones (external-proxy buses dropped); the index is the
    local (EPT) wall-clock hour, with the duplicated DST fall-back hour
    averaged and the missing spring-forward hour absent. ``None`` if no source.
    """
    frames: list[pd.DataFrame] = []
    if kind == "da":
        outer_path = LMP_DIR / "NYISO" / "NYISO_zonal_hourly.zip"
        if not outer_path.exists():
            return None
        fmt = "%m/%d/%Y %H:%M"
        with zipfile.ZipFile(outer_path) as outer:
            for name in outer.namelist():
                base = name.rsplit("/", 1)[-1]
                if not (base.startswith(str(year)) and "damlbmp_zone" in base):
                    continue
                with zipfile.ZipFile(io.BytesIO(outer.read(name))) as inner:
                    frames += [
                        _read_nyiso_csv(inner.read(dn))
                        for dn in inner.namelist()
                        if dn.endswith(".csv")
                    ]
    else:
        fmt = "%m/%d/%Y %H:%M:%S"
        for path in sorted((LMP_DIR / "NYISO").glob(f"{year}*realtime_zone_csv.zip")):
            with zipfile.ZipFile(path) as z:
                frames += [
                    _read_nyiso_csv(z.read(dn))
                    for dn in z.namelist()
                    if dn.endswith(".csv")
                ]
    if not frames:
        return None
    df = pd.concat(frames, ignore_index=True)
    df = df[df["Name"].isin(NYISO_INTERNAL)]
    ts = pd.to_datetime(df["Time Stamp"], format=fmt, errors="coerce")
    df = df.assign(ts=ts.dt.floor("h")).dropna(subset=["ts"])
    # pivot_table mean folds the RT 5-minute intervals and the DST fall-back
    # hour's two instances into one value per zone per wall-clock hour.
    return df.pivot_table(index="ts", columns="Name", values="lmp", aggfunc="mean")


def nyiso_zone_hourly(year: int, kind: str = "da") -> pd.DataFrame | None:
    """Model-zone (+ ``hub``) hourly NYISO LBMP frame for ``year`` / ``kind``.

    Columns are the five model zones (each the simple mean of its constituent
    NYISO internal zones) plus ``hub`` (the simple mean of all eleven internal
    zones), indexed by the local hour. Shared by the JSON builder and the
    zonal-sufficiency test. ``None`` when the source files are absent.
    """
    wide = _nyiso_wide(year, kind)
    if wide is None:
        return None
    cols = {
        z: wide[[c for c in members if c in wide.columns]].mean(axis=1)
        for z, members in NYISO_ZONE_MAP.items()
    }
    present = [z for z in NYISO_INTERNAL if z in wide.columns]
    cols["hub"] = wide[present].mean(axis=1)
    return pd.DataFrame(cols)


def _neiso_sheet_series(wb, sheet: str) -> dict[str, pd.Series]:
    """``{"da": series, "rt": series}`` of hourly LMP for one SMD sheet.

    The timestamp is the row's Date plus (Hr_End − 1) hours. Leap-day Feb 29
    rows stay in (dropped only when densified onto the 8760 calendar).
    """
    rows = wb[sheet].iter_rows(values_only=True)
    next(rows, None)  # header
    idx: list = []
    da: list = []
    rt: list = []
    for r in rows:
        if r is None or r[0] is None or r[1] is None:
            continue
        try:
            he = int(str(r[1]))
        except ValueError:
            continue
        idx.append(pd.Timestamp(r[0]) + pd.Timedelta(hours=he - 1))
        da.append(r[NEISO_DA_COL])
        rt.append(r[NEISO_RT_COL])
    index = pd.DatetimeIndex(idx)
    return {
        "da": pd.Series(pd.to_numeric(da, errors="coerce"), index=index),
        "rt": pd.Series(pd.to_numeric(rt, errors="coerce"), index=index),
    }


def neiso_zone_hourly(year: int, kind: str = "da") -> pd.DataFrame | None:
    """Model-zone (+ ``hub``) hourly NEISO LMP frame for ``year`` / ``kind``.

    Columns are the four model zones (each the simple mean of its constituent
    SMD load-zone sheets) plus ``hub`` (the .H.INTERNAL_HUB "ISO NE CA"
    sheet), indexed by the local hour. Shared by the JSON builder and the
    zonal-sufficiency test. ``None`` when the workbook is absent.
    """
    path = LMP_DIR / "NEISO" / f"{year}_smd_hourly.xlsx"
    if not path.exists():
        return None
    needed = {NEISO_HUB_SHEET, *(s for ss in NEISO_ZONE_MAP.values() for s in ss)}
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    raw = {
        sh: _neiso_sheet_series(wb, sh)[kind] for sh in wb.sheetnames if sh in needed
    }
    wb.close()
    cols: dict[str, pd.Series] = {}
    for z, sheets in NEISO_ZONE_MAP.items():
        avail = [raw[s] for s in sheets if s in raw]
        if avail:
            cols[z] = pd.concat(avail, axis=1).mean(axis=1)
    if NEISO_HUB_SHEET in raw:
        cols["hub"] = raw[NEISO_HUB_SHEET]
    return pd.DataFrame(cols) if cols else None


def _assemble_zonal(
    frames: dict[str, pd.DataFrame | None], year: int, src: str
) -> tuple[dict, pd.DataFrame]:
    """Build the JSON record + dense hourly frame from model-zone/hub frames.

    ``frames`` maps ``"da"`` / ``"rt"`` to a model-zone-plus-``hub`` frame (or
    ``None``). The top-level ``da``/``rt``/``*_mon``/``*_pct`` mirror the
    ERCOT/PJM/CAISO schema and carry the hub; a ``zones`` sub-dict adds each
    model zone's ``da``/``rt``/``da_mon``/``rt_mon``. The dense 8760 hub series
    feeds the parquet sidecar (same calendar as the other ISOs).
    """
    parts: dict = {}
    zones_out: dict[str, dict] = {}
    dense: dict[str, np.ndarray] = {}
    for kind in ("da", "rt"):
        fr = frames.get(kind)
        if fr is None or "hub" not in fr.columns or not fr["hub"].notna().any():
            dense[kind] = np.full(_HOURS_PER_YEAR, np.nan)
            continue
        months = pd.Series(fr.index).dt.month
        hub = fr["hub"]
        parts[kind] = round(float(hub.mean()), 2)
        parts[f"{kind}_mon"] = _by_month(hub.to_numpy(), months)
        d = _caiso_densify(hub)
        dense[kind] = d
        parts[f"{kind}_pct"] = _pct(d)
        for z in fr.columns:
            if z == "hub":
                continue
            ser = fr[z]
            entry = zones_out.setdefault(z, {})
            entry[kind] = round(float(ser.mean()), 2)
            entry[f"{kind}_mon"] = _by_month(ser.to_numpy(), months)
    rec = {
        k: parts[k]
        for k in ("da", "rt", "da_mon", "rt_mon", "da_pct", "rt_pct")
        if k in parts
    }
    order = ("da", "rt", "da_mon", "rt_mon")
    rec["zones"] = {z: {k: e[k] for k in order if k in e} for z, e in zones_out.items()}
    rec["src"] = src
    hourly = pd.DataFrame(
        {
            "year": np.int16(year),
            "hour": np.arange(_HOURS_PER_YEAR, dtype=np.int16),
            "rt": dense["rt"].astype(np.float32),
            "da": dense["da"].astype(np.float32),
        }
    )
    return rec, hourly


def _nyiso(year: int) -> tuple[dict, pd.DataFrame] | None:
    """Return ``(record, hourly)`` for NYISO, or ``None`` if no source files."""
    frames = {k: nyiso_zone_hourly(year, k) for k in ("da", "rt")}
    if frames["da"] is None and frames["rt"] is None:
        return None
    return _assemble_zonal(frames, year, NYISO_SRC)


def _neiso(year: int) -> tuple[dict, pd.DataFrame] | None:
    """Return ``(record, hourly)`` for NEISO, or ``None`` if no workbook."""
    frames = {k: neiso_zone_hourly(year, k) for k in ("da", "rt")}
    if frames["da"] is None and frames["rt"] is None:
        return None
    return _assemble_zonal(frames, year, NEISO_SRC)


BUILDERS = {
    "ERCOT": _ercot,
    "PJM": _pjm,
    "CAISO": _caiso,
    "NYISO": _nyiso,
    "NEISO": _neiso,
}


def build(years, isos=None) -> tuple[dict, dict]:
    """Build the JSON reference and per-ISO hourly frames for ``years``.

    Args:
        years: Calendar years to (re)derive.
        isos: Optional subset of ISO keys to build; ``None`` builds all. Use a
            subset to refresh one ISO without depending on the others' raws
            (ERCOT/NYISO DA source zips are staged out of the repo, so building
            them on a fresh checkout would otherwise drop or degrade them — the
            committed reference is the durable record, and ``main`` merges).

    Returns:
        ``(table, hourly)`` — the ``{iso: {year: record}}`` JSON table, and
        ``{iso: DataFrame}`` of concatenated hourly hub-mean series for the
        ISOs whose builder produces one.
    """
    table: dict[str, dict] = {}
    hourly: dict[str, list] = {}
    for iso, fn in BUILDERS.items():
        if isos is not None and iso not in isos:
            continue
        for year in years:
            got = fn(int(year))
            if got is None:
                continue
            rec, hr = got
            table.setdefault(iso, {})[str(year)] = rec
            if hr is not None:
                hourly.setdefault(iso, []).append(hr)
            means = ", ".join(f"{k} ${rec[k]}" for k in ("da", "rt") if k in rec)
            print(f"  {iso} {year}: {means}")
    return table, {
        iso: pd.concat(frames, ignore_index=True) for iso, frames in hourly.items()
    }


# ---------------------------------------------------------------------------
# Load-weighted (like-for-like) price basis — rubric v2.4
# ---------------------------------------------------------------------------
# The C3a/C3b scorer's model side is the system LOAD-WEIGHTED mean LMP
# (per-zone demand-weighted zonal means, zone-demand-weighted across zones),
# but the legacy ``rt``/``da`` fields above are EQUAL-HOUR means of a hub
# series — a mixed basis whose wedge grows with tail realism (a byte-perfect
# ERCOT 2023 model scores +33.5% against its own actual; see
# docs/handoffs/ercot-ordc-capdual-adder-2026-07.md §4). The ``*_lw`` fields
# below put the ACTUAL on the same basis as the model: each ISO's committed
# hourly actual series weighted by the MEASURED hourly load the model itself
# dispatches in a backcast (``eia_loader.load_demand`` — same series, so the
# two sides of C3a finally share weights). Where a committed ZONAL hourly
# archive exists (ERCOT), the construction mirrors the scorer zone-by-zone;
# elsewhere it weights the system hub series by system load. The legacy
# equal-hour fields stay untouched (display continuity + fallback basis).

# Model zone -> ERCOT settlement load zone(s). A model zone spanning several
# LZs takes their simple mean (South_Central = Austin Energy + CPS Energy +
# LCRA, the three municipal LZs it aggregates; Northeast = the Rayburn
# country LZ; Panhandle has no LZ of its own and carries ~0 model load — it
# rides with LZ_WEST). Documented in docs/rubric-v24-price-basis-memo-2026-07.md.
ERCOT_MODEL_ZONE_TO_LZ: dict[str, tuple[str, ...]] = {
    "Houston": ("LZ_HOUSTON",),
    "North": ("LZ_NORTH",),
    "Northeast": ("LZ_RAYBN",),
    "South": ("LZ_SOUTH",),
    "South_Central": ("LZ_AEN", "LZ_CPS", "LZ_LCRA"),
    "West": ("LZ_WEST",),
    "Panhandle": ("LZ_WEST",),
}
ERCOT_ZONAL_PARQUET = "actual_lmp_zonal_ERCOT.parquet"


def _lw_stats(prices: np.ndarray, weights: np.ndarray) -> tuple[float, list]:
    """NaN-aware ``(annual, [12 monthly])`` load-weighted means of a series."""
    p = np.asarray(prices, dtype=float)[:_HOURS_PER_YEAR]
    w = np.asarray(weights, dtype=float)[: p.size]
    v = ~np.isnan(p) & (w > 0)
    annual = float((p[v] * w[v]).sum() / w[v].sum()) if v.any() else float("nan")
    mon: list = []
    for m in range(12):
        lo = _MONTH_START_HOUR[m]
        hi = lo + _DAYS_IN_MONTH[m] * 24
        pm, wm, vm = p[lo:hi], w[lo:hi], v[lo:hi]
        mon.append(
            round(float((pm[vm] * wm[vm]).sum() / wm[vm].sum()), 2)
            if vm.any()
            else None
        )
    return round(annual, 2), mon


def _measured_zone_demand(iso: str, year: int) -> np.ndarray | None:
    """Measured hourly zonal demand ``(n_zones, T)`` — the model's own series."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia_loader import load_demand

    try:
        return load_demand(iso, int(year), get_iso_config(iso))
    except Exception as exc:  # measured series absent for this iso-year
        print(f"  {iso} {year}: no measured demand ({exc}); lw fields skipped")
        return None


def _lw_fields(iso: str, year: int) -> dict | None:
    """Return the ``*_lw`` record fields for one ISO-year, or ``None``.

    ERCOT: zone-resolved — the scorer's exact formula mirrored on the actual
    (per-model-zone LZ hourly series weighted by that zone's measured demand,
    then zone-demand-weighted across zones). Other ISOs: the committed system
    hub series weighted by measured system load.
    """
    from market_sim.config.iso_configs import get_iso_config

    demand = _measured_zone_demand(iso, year)
    if demand is None:
        return None
    out: dict = {}
    if iso == "ERCOT":
        zp = HOURLY_OUT / ERCOT_ZONAL_PARQUET
        if not zp.exists():
            return None
        z = pd.read_parquet(zp)
        z = z[z["year"] == int(year)]
        series: dict[str, dict[str, np.ndarray]] = {}
        for sp, g in z.groupby("settlement_point"):
            g = g.sort_values("hour")
            for kind in ("rt", "da"):
                dense = np.full(_HOURS_PER_YEAR, np.nan)
                hr = g["hour"].to_numpy(int)
                ok = hr < _HOURS_PER_YEAR
                dense[hr[ok]] = g[kind].to_numpy(float)[ok]
                series.setdefault(str(sp), {})[kind] = dense
        zone_names = [zn.name for zn in get_iso_config(iso).zones]
        for kind in ("rt", "da"):
            pairs: list[tuple[float, list, float]] = []  # (annual, mon, weight)
            for zi, zone in enumerate(zone_names):
                lzs = ERCOT_MODEL_ZONE_TO_LZ.get(zone)
                w = demand[zi]
                if not lzs or float(w.sum()) <= 0.0:
                    continue
                have = [
                    series[lz][kind]
                    for lz in lzs
                    if lz in series and not np.isnan(series[lz][kind]).all()
                ]
                if not have:
                    continue
                p = np.nanmean(np.vstack(have), axis=0)
                annual, mon = _lw_stats(p, w)
                if np.isnan(annual):
                    continue
                pairs.append((annual, mon, float(w.sum())))
            if not pairs:
                continue
            wsum = sum(w for _, _, w in pairs)
            out[f"{kind}_lw"] = round(sum(a * w for a, _, w in pairs) / wsum, 2)
            out[f"{kind}_lw_mon"] = [
                (
                    round(
                        sum(m[i] * w for _, m, w in pairs if m[i] is not None)
                        / sum(w for _, m, w in pairs if m[i] is not None),
                        2,
                    )
                    if any(m[i] is not None for _, m, w in pairs)
                    else None
                )
                for i in range(12)
            ]
        if out:
            out["src_lw"] = (
                "zonal LZ settlement prices (RTM 15-min / DAM hourly) "
                "load-weighted by measured zonal demand (eia_loader.load_demand), "
                "model-zone crosswalk ERCOT_MODEL_ZONE_TO_LZ"
            )
    else:
        hp = HOURLY_OUT / f"actual_lmp_hourly_{iso}.parquet"
        if not hp.exists():
            return None
        h = pd.read_parquet(hp)
        h = h[h["year"] == int(year)].sort_values("hour")
        if h.empty:
            return None
        w = demand.sum(axis=0)
        for kind in ("rt", "da"):
            dense = np.full(_HOURS_PER_YEAR, np.nan)
            hr = h["hour"].to_numpy(int)
            ok = hr < _HOURS_PER_YEAR
            dense[hr[ok]] = h[kind].to_numpy(float)[ok]
            if np.isnan(dense).all():
                continue
            annual, mon = _lw_stats(dense, w)
            if not np.isnan(annual):
                out[f"{kind}_lw"] = annual
                out[f"{kind}_lw_mon"] = mon
        if out:
            out["src_lw"] = (
                "system hub hourly series load-weighted by measured system "
                "demand (eia_loader.load_demand)"
            )
    return out or None


def lw_retrofit(years: list[int], isos: list[str] | None = None) -> None:
    """Amend the committed reference with the ``*_lw`` fields in place.

    Reads ``actual_lmp.json``, adds ``rt_lw``/``rt_lw_mon``/``da_lw``/
    ``da_lw_mon``/``src_lw`` to each covered ISO-year from the committed
    hourly parquets × measured load, and rewrites the JSON. Legacy fields are
    never touched; ISO-years without a committed hourly series or measured
    demand keep their record unchanged (the scorer falls back to the legacy
    equal-hour basis with an explicit label). Rubric v2.4; re-derivation
    citation: methodology change (mixed-basis C3), not a residual.
    """
    table = json.loads(OUT.read_text())
    n = 0
    for iso, yrec in sorted(table.items()):
        if isos is not None and iso not in isos:
            continue
        for y in sorted(yrec):
            if int(y) not in years:
                continue
            fields = _lw_fields(iso, int(y))
            if fields:
                yrec[y].update(fields)
                n += 1
                print(
                    f"  {iso} {y}: rt_lw {fields.get('rt_lw')} "
                    f"da_lw {fields.get('da_lw')} "
                    f"(legacy rt {yrec[y].get('rt')} da {yrec[y].get('da')})"
                )
    OUT.write_text(json.dumps(table, indent=2) + "\n")
    print(f"wrote {OUT} (+lw fields on {n} iso-years)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=list(DEFAULT_YEARS))
    ap.add_argument(
        "--isos",
        nargs="+",
        default=None,
        help="Subset of ISOs to (re)derive; default all. Only the built ISOs "
        "are updated — others keep their committed entry/parquet (their raws "
        "may be staged out of the repo).",
    )
    ap.add_argument(
        "--lw-retrofit",
        action="store_true",
        help="Do not re-parse raw archives; amend the committed "
        "actual_lmp.json with the load-weighted (*_lw) price fields from the "
        "committed hourly parquets × measured demand (rubric v2.4 C3 basis).",
    )
    args = ap.parse_args()
    if args.lw_retrofit:
        lw_retrofit(args.years, isos=args.isos)
        return
    table, hourly = build(args.years, isos=args.isos)
    # Merge into the committed reference rather than overwriting: ISOs not built
    # this run (or whose source raws are staged out) keep their durable entry.
    merged: dict[str, dict] = {}
    if OUT.exists():
        merged = json.loads(OUT.read_text())
    for iso, years in table.items():
        merged.setdefault(iso, {}).update(years)
    OUT.write_text(json.dumps(merged, indent=2) + "\n")
    print(f"wrote {OUT} ({sum(len(v) for v in merged.values())} iso-years)")
    # Only rewrite parquets for ISOs actually built this run.
    for iso, frame in hourly.items():
        p = HOURLY_OUT / f"actual_lmp_hourly_{iso}.parquet"
        frame.to_parquet(p, index=False)
        print(f"wrote {p} ({len(frame)} hours, {frame['year'].nunique()} years)")


if __name__ == "__main__":
    main()
