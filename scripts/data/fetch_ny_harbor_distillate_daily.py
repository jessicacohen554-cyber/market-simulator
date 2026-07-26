#!/usr/bin/env python3
"""Fetch the **daily** New York Harbor ULSD spot price, for the dual-fuel oil-parity cap.

A dual-fuel gas unit burns whichever fuel is cheaper each hour, so
:func:`market_sim.data.fuel.apply_dual_fuel_pricing` caps its delivered gas
price at delivered oil parity. That parity price is measured EIA-923
Petroleum receipts, which are **monthly** — a flat plateau across every day of
the month. The gas side of the same comparison is already daily (the
Transco Z6 NY / Iroquois hub overlay, ``gas_daily_shape_factors``), so on the
coldest days of a NYISO winter the delivered gas price spikes into a
*monthly-flat* oil cap and ~16.5 GW of downstate dual-fuel capacity pins there:
120 of the 744 Jan-2025 hours clear on that flat cap, and the polar-vortex
price peak cannot form (docs/handoffs/nyiso-overrun-underrun-2026-07.md §2, §6).

The defect is granularity, not level. This script supplies the missing daily
SHAPE: EIA's New York Harbor Ultra-Low Sulfur No. 2 Diesel spot price, the
free daily benchmark for the exact product NY dual-fuel units burn (NYSDEC
6 NYCRR Part 225-1 / ECL §19-0325 cap distillate at 15 ppm sulfur statewide,
so a NY backup-fuel tank is ULSD, not high-sulfur No. 2). The consumer
(:func:`market_sim.data.fuel.oil_daily_shape_factors`) uses it **mean-
preservingly** within each month — the EIA-923 monthly receipt keeps setting
the delivered LEVEL (it alone carries transport, storage and the
distributor's margin, none of which a FOB cargo quote contains); the spot
series only says which days of that month were dear and which were cheap.
Rule 14 [R-ACCURATE]: a measured daily shape replaces a flat estimate.

Source: ``https://www.eia.gov/dnav/pet/hist_xls/EER_EPD2DXL0_PF4_Y35NY_DPGd.xls``
(EIA "Petroleum & Other Liquids" series ``EER_EPD2DXL0_PF4_Y35NY_DPG``, daily,
dollars per gallon, FOB New York Harbor). EIA serves this dnav series only as a
legacy ``.xls`` workbook — the ``.csv`` sibling 404s and the HTML LeafHandler
redirects — so reading it needs ``xlrd`` (a dev-group dependency, not a model
runtime one).

Output: ``data/raw/oil-prices/ny_harbor_ulsd_daily.csv``
  columns ``date, ny_harbor_ulsd_usd_gal``, one row per EIA trading day.

Holdout discipline (CLAUDE.md rule 22 [R-HOLDOUT]): the default window is the
TRAINING span 2023-2025 only. Widening it to a validation/locked-test year is a
data intake into an out-of-training period and needs its own explicit,
session-logged owner authorization — which ``--start-year``/``--end-year``
make deliberate rather than accidental.

Usage:
    uv run python scripts/data/fetch_ny_harbor_distillate_daily.py
    uv run python scripts/data/fetch_ny_harbor_distillate_daily.py --start-year 2023 --end-year 2025
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import pandas as pd
import requests

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

#: EIA dnav series id — NY Harbor Ultra-Low Sulfur No. 2 Diesel Spot Price FOB.
SERIES_ID = "EER_EPD2DXL0_PF4_Y35NY_DPG"
SOURCE_URL = f"https://www.eia.gov/dnav/pet/hist_xls/{SERIES_ID}d.xls"

#: Default intake window — the rule-22 training span. See the module docstring.
DEFAULT_START_YEAR = 2023
DEFAULT_END_YEAR = 2025

OUT_PATH: Path = RAW_DATA_DIR / "oil-prices" / "ny_harbor_ulsd_daily.csv"


def fetch_workbook(url: str = SOURCE_URL, timeout: int = 120) -> bytes:
    """Download the EIA daily-series workbook and return its raw bytes."""
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.content


def parse_workbook(data: bytes) -> pd.DataFrame:
    """Parse the EIA daily workbook into ``date, ny_harbor_ulsd_usd_gal``.

    The dnav workbook carries a ``Contents`` sheet and a ``Data 1`` sheet whose
    first two rows are the series header block; the data itself is two columns
    (date, price) with blank rows for days EIA publishes no quote.
    """
    frame = pd.read_excel(io.BytesIO(data), sheet_name="Data 1", skiprows=2)
    if frame.shape[1] != 2:
        raise ValueError(
            f"unexpected EIA workbook shape {frame.shape} — expected 2 columns "
            "(date, price); the dnav layout may have changed"
        )
    frame.columns = ["date", "ny_harbor_ulsd_usd_gal"]
    frame = frame.dropna()
    frame["date"] = pd.to_datetime(frame["date"])
    frame["ny_harbor_ulsd_usd_gal"] = frame["ny_harbor_ulsd_usd_gal"].astype(float)
    return frame.sort_values("date").reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start-year", type=int, default=DEFAULT_START_YEAR)
    ap.add_argument("--end-year", type=int, default=DEFAULT_END_YEAR)
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args()

    print(f"fetching {SOURCE_URL} ...")
    frame = parse_workbook(fetch_workbook())
    years = frame["date"].dt.year
    frame = frame[(years >= args.start_year) & (years <= args.end_year)]
    if frame.empty:
        raise SystemExit(
            f"no quotes in {args.start_year}-{args.end_year} — nothing written"
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out, index=False, float_format="%.4f")
    span = f"{frame['date'].min():%Y-%m-%d}..{frame['date'].max():%Y-%m-%d}"
    print(
        f"wrote {args.out} ({len(frame)} trading days, {span}, "
        f"${frame['ny_harbor_ulsd_usd_gal'].min():.3f}-"
        f"${frame['ny_harbor_ulsd_usd_gal'].max():.3f}/gal)"
    )


if __name__ == "__main__":
    main()
