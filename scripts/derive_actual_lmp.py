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
     "PJM":   {"2024": {"da": 29.78, "rt": 29.53, ...}, ...}}

``da`` / ``rt`` are the annual mean day-ahead / real-time price in $/MWh, and
``da_mon`` / ``rt_mon`` the 12 monthly means (Jan-Dec; ``null`` for a month with
no data) feeding the summary page's monthly LMP table. All are taken from the
system-wide hub-average series of each market:

  * ERCOT — ``HB_HUBAVG`` settlement point in the DAM (hourly) and RTM
    (15-minute) Load-Zone/Hub settlement-point-price reports.
  * PJM — the mean across the 12 trading hubs in the hourly RT/DA LMP export.

Run after refreshing ``inputs/raw-data/lmp-data/``; commit the JSON. Missing
source files for an ISO/year are skipped, so a partial data drop still
produces a valid reference.

Usage:
    python scripts/derive_actual_lmp.py [--years 2023 2024 2025]
"""
from __future__ import annotations

import argparse
import io
import json
import zipfile
from pathlib import Path

import openpyxl
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
LMP_DIR = REPO / "inputs" / "raw-data" / "lmp-data"
OUT = REPO / "inputs" / "calibration" / "actual_lmp.json"

DEFAULT_YEARS = (2023, 2024, 2025)

PJM_SRC = "PJM RT/DA LMP, mean of the 12 trading hubs (hourly)"
ERCOT_SRC = "ERCOT HB_HUBAVG settlement point price (DAM hourly / RTM 15-min)"


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


def _pjm(year: int) -> dict | None:
    """Return ``{da, rt, da_mon, rt_mon, src}`` for PJM, or ``None`` if absent."""
    f = LMP_DIR / f"PJM_{year}_rt_da_monthly_lmps.csv"
    if not f.exists():
        return None
    df = pd.read_csv(
        f, usecols=["datetime_beginning_ept", "total_lmp_rt", "total_lmp_da"])
    mon = pd.to_datetime(df["datetime_beginning_ept"],
                         format="%m/%d/%Y %I:%M:%S %p",
                         errors="coerce").dt.month
    return {
        "da": round(float(df["total_lmp_da"].mean()), 2),
        "rt": round(float(df["total_lmp_rt"].mean()), 2),
        "da_mon": _by_month(df["total_lmp_da"], mon),
        "rt_mon": _by_month(df["total_lmp_rt"], mon),
        "src": PJM_SRC,
    }


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


def _ercot(year: int) -> dict | None:
    """Return ``{da, rt, da_mon, rt_mon, src}`` for ERCOT, or ``None``."""
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
    return out


BUILDERS = {"ERCOT": _ercot, "PJM": _pjm}


def build(years) -> dict:
    """Build the ``{iso: {year: {da, rt, src}}}`` reference for ``years``."""
    table: dict[str, dict] = {}
    for iso, fn in BUILDERS.items():
        for year in years:
            rec = fn(int(year))
            if rec is None:
                continue
            table.setdefault(iso, {})[str(year)] = rec
            got = ", ".join(f"{k} ${rec[k]}" for k in ("da", "rt") if k in rec)
            print(f"  {iso} {year}: {got}")
    return table


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=list(DEFAULT_YEARS))
    args = ap.parse_args()
    table = build(args.years)
    OUT.write_text(json.dumps(table, indent=2) + "\n")
    print(f"wrote {OUT} ({sum(len(v) for v in table.values())} iso-years)")


if __name__ == "__main__":
    main()
