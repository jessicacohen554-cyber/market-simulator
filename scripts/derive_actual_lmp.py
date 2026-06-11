"""Derive actual historical average LMP per ISO/year for the dashboard.

The backcast dashboard's summary page compares the model's average LMP against
the actual historical market price. Parsing the raw ERCOT settlement-point
workbooks (20+ MB xlsx, 15-minute real-time intervals) on every dashboard
render would be slow and would pull ``openpyxl`` into the render path, so this
script reduces the raw price files to a tiny committed reference,
``inputs/calibration/actual_lmp.json``:

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

For ISOs with a true hourly source (PJM today), two extras are produced for
the price-duration-curve overlay (J3a):

  * ``da_pct`` / ``rt_pct`` in the JSON — duration-curve percentiles of the
    hub-mean hourly price (``p99`` is a high price, ``p1`` a low one).
  * ``inputs/calibration/actual_lmp_hourly_{ISO}.parquet`` — the hub-mean
    hourly series itself (columns ``year``, ``hour``, ``rt``, ``da``), dense
    on the model's fixed 8760-hour local calendar: Feb 29 is dropped, the
    DST fall-back hour is averaged, and the spring-forward hour is NaN.

Run after refreshing ``inputs/raw-data/lmp-data/``; commit the JSON and the
hourly parquet. Missing source files for an ISO/year are skipped, so a
partial data drop still produces a valid reference.

Usage:
    python scripts/derive_actual_lmp.py [--years 2023 2024 2025]
"""
from __future__ import annotations

import argparse
import io
import json
import zipfile
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
LMP_DIR = REPO / "inputs" / "raw-data" / "lmp-data"
OUT = REPO / "inputs" / "calibration" / "actual_lmp.json"
HOURLY_OUT = REPO / "inputs" / "calibration"  # actual_lmp_hourly_{ISO}.parquet

DEFAULT_YEARS = (2023, 2024, 2025)

PJM_SRC = "PJM RT/DA LMP, mean of the 12 trading hubs (hourly)"
ERCOT_SRC = "ERCOT HB_HUBAVG settlement point price (DAM hourly / RTM 15-min)"

# Duration-curve percentile levels for the ``da_pct`` / ``rt_pct`` records.
_PCT_LEVELS = (1, 5, 10, 25, 50, 75, 90, 95, 99)

# The model's fixed non-leap dispatch calendar (matches
# market_sim.data.campd: Feb 29 is dropped, hours are local clock).
_HOURS_PER_YEAR = 8760
_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR = tuple(
    int(sum(_DAYS_IN_MONTH[:m]) * 24) for m in range(12))


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
    idx = (np.asarray([_MONTH_START_HOUR[m - 1] for m in ts.dt.month])
           + (ts.dt.day.to_numpy() - 1) * 24 + ts.dt.hour.to_numpy())
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
    ts = pd.to_datetime(df["datetime_beginning_ept"],
                        format="%m/%d/%Y %I:%M:%S %p", errors="coerce")
    g = (df.assign(hour=_hour_index(ts))
           .query("hour >= 0")
           .groupby("hour")[["total_lmp_rt", "total_lmp_da"]].mean())
    dense = g.reindex(range(_HOURS_PER_YEAR))
    return pd.DataFrame({
        "year": np.int16(year),
        "hour": np.arange(_HOURS_PER_YEAR, dtype=np.int16),
        "rt": dense["total_lmp_rt"].to_numpy(np.float32),
        "da": dense["total_lmp_da"].to_numpy(np.float32),
    })


def _pjm(year: int) -> tuple[dict, pd.DataFrame] | None:
    """Return ``(record, hourly)`` for PJM, or ``None`` if the file is absent.

    ``record`` is the ``{da, rt, da_mon, rt_mon, da_pct, rt_pct, src}`` JSON
    entry; ``hourly`` the dense hub-mean hourly frame for the parquet sidecar.
    """
    f = LMP_DIR / f"PJM_{year}_rt_da_monthly_lmps.csv"
    if not f.exists():
        return None
    df = pd.read_csv(
        f, usecols=["datetime_beginning_ept", "total_lmp_rt", "total_lmp_da"])
    mon = pd.to_datetime(df["datetime_beginning_ept"],
                         format="%m/%d/%Y %I:%M:%S %p",
                         errors="coerce").dt.month
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


def _ercot_hubavg(zip_glob: str, name_col: int, price_col: int) -> dict | None:
    """``{ann, mon}`` ``HB_HUBAVG`` price for an ERCOT settlement-point workbook.

    Args:
        zip_glob: Glob (under ``LMP_DIR``) selecting the report zip.
        name_col: Zero-based column index of the settlement-point name.
        price_col: Zero-based column index of the settlement-point price.

    Returns:
        ``{"ann": annual_mean, "mon": [12 monthly means or None]}`` over every
        HB_HUBAVG row (the report's date column, index 0, gives the month), or
        ``None`` when no matching zip is present.
    """
    paths = sorted(LMP_DIR.glob(zip_glob))
    if not paths:
        return None
    with zipfile.ZipFile(paths[0]) as z:
        inner = next(n for n in z.namelist() if n.endswith(".xlsx"))
        data = z.read(inner)
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    msum, mcnt = [0.0] * 12, [0] * 12
    for sheet in wb.sheetnames:
        rows = wb[sheet].iter_rows(values_only=True)
        next(rows, None)  # header
        for r in rows:
            if r is None or len(r) <= price_col:
                continue
            if r[name_col] == "HB_HUBAVG" and r[price_col] is not None:
                mo = _month_of(r[0])
                if mo is None:
                    continue
                msum[mo - 1] += float(r[price_col])
                mcnt[mo - 1] += 1
    wb.close()
    n = sum(mcnt)
    if not n:
        return None
    mon = [round(msum[i] / mcnt[i], 2) if mcnt[i] else None for i in range(12)]
    return {"ann": sum(msum) / n, "mon": mon}


def _ercot(year: int) -> tuple[dict, None] | None:
    """Return ``(record, None)`` for ERCOT, or ``None`` (no hourly sidecar)."""
    # DAM columns: Date, Hour Ending, Repeated, Settlement Point(3), Price(4).
    da = _ercot_hubavg(f"*DAMLZHBSPP_{year}*.zip", 3, 4)
    # RTM columns: Date, Hour, Interval, Repeated, Name(4), Type, Price(6).
    rt = _ercot_hubavg(f"*RTMLZHBSPP_{year}*.zip", 4, 6)
    if da is None and rt is None:
        return None
    out: dict = {"src": ERCOT_SRC}
    if da is not None:
        out["da"], out["da_mon"] = round(da["ann"], 2), da["mon"]
    if rt is not None:
        out["rt"], out["rt_mon"] = round(rt["ann"], 2), rt["mon"]
    return out, None


BUILDERS = {"ERCOT": _ercot, "PJM": _pjm}


def build(years) -> tuple[dict, dict]:
    """Build the JSON reference and per-ISO hourly frames for ``years``.

    Returns:
        ``(table, hourly)`` — the ``{iso: {year: record}}`` JSON table, and
        ``{iso: DataFrame}`` of concatenated hourly hub-mean series for the
        ISOs whose builder produces one.
    """
    table: dict[str, dict] = {}
    hourly: dict[str, list] = {}
    for iso, fn in BUILDERS.items():
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
    return table, {iso: pd.concat(frames, ignore_index=True)
                   for iso, frames in hourly.items()}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=list(DEFAULT_YEARS))
    args = ap.parse_args()
    table, hourly = build(args.years)
    OUT.write_text(json.dumps(table, indent=2) + "\n")
    print(f"wrote {OUT} ({sum(len(v) for v in table.values())} iso-years)")
    for iso, frame in hourly.items():
        p = HOURLY_OUT / f"actual_lmp_hourly_{iso}.parquet"
        frame.to_parquet(p, index=False)
        print(f"wrote {p} ({len(frame)} hours, "
              f"{frame['year'].nunique()} years)")


if __name__ == "__main__":
    main()
