"""Derive actual historical average LMP per ISO/year for the dashboard.

The backcast dashboard's summary page compares the model's average LMP against
the actual historical market price. Parsing the raw ERCOT settlement-point
workbooks (20+ MB xlsx, 15-minute real-time intervals) on every dashboard
render would be slow and would pull ``openpyxl`` into the render path, so this
script reduces the raw price files to a tiny committed reference,
``inputs/calibration/actual_lmp.json``:

    {"ERCOT": {"2024": {"da": 28.09, "rt": 26.83, "src": "..."}, ...},
     "PJM":   {"2024": {"da": 29.78, "rt": 29.53, "src": "..."}, ...}}

``da`` / ``rt`` are the annual mean day-ahead / real-time price in $/MWh, taken
from the system-wide hub-average series of each market:

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


def _pjm(year: int) -> dict | None:
    """Return ``{da, rt, src}`` for PJM, or ``None`` if the file is absent."""
    f = LMP_DIR / f"PJM_{year}_rt_da_monthly_lmps.csv"
    if not f.exists():
        return None
    df = pd.read_csv(f, usecols=["total_lmp_rt", "total_lmp_da"])
    return {
        "da": round(float(df["total_lmp_da"].mean()), 2),
        "rt": round(float(df["total_lmp_rt"].mean()), 2),
        "src": PJM_SRC,
    }


def _ercot_hubavg(zip_glob: str, name_col: int, price_col: int) -> float | None:
    """Mean ``HB_HUBAVG`` price across an ERCOT settlement-point workbook.

    Args:
        zip_glob: Glob (under ``LMP_DIR``) selecting the report zip.
        name_col: Zero-based column index of the settlement-point name.
        price_col: Zero-based column index of the settlement-point price.

    Returns:
        The mean price over every HB_HUBAVG row in every month sheet, or
        ``None`` when no matching zip is present.
    """
    paths = sorted(LMP_DIR.glob(zip_glob))
    if not paths:
        return None
    with zipfile.ZipFile(paths[0]) as z:
        inner = next(n for n in z.namelist() if n.endswith(".xlsx"))
        data = z.read(inner)
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    total, n = 0.0, 0
    for sheet in wb.sheetnames:
        rows = wb[sheet].iter_rows(values_only=True)
        next(rows, None)  # header
        for r in rows:
            if r is None or len(r) <= price_col:
                continue
            if r[name_col] == "HB_HUBAVG" and r[price_col] is not None:
                total += float(r[price_col])
                n += 1
    wb.close()
    return total / n if n else None


def _ercot(year: int) -> dict | None:
    """Return ``{da, rt, src}`` for ERCOT, or ``None`` if no file is present."""
    # DAM columns: Date, Hour Ending, Repeated, Settlement Point(3), Price(4).
    da = _ercot_hubavg(f"*DAMLZHBSPP_{year}*.zip", 3, 4)
    # RTM columns: Date, Hour, Interval, Repeated, Name(4), Type, Price(6).
    rt = _ercot_hubavg(f"*RTMLZHBSPP_{year}*.zip", 4, 6)
    if da is None and rt is None:
        return None
    out: dict = {"src": ERCOT_SRC}
    if da is not None:
        out["da"] = round(da, 2)
    if rt is not None:
        out["rt"] = round(rt, 2)
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
