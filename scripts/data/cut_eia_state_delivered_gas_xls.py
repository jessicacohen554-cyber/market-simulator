#!/usr/bin/env python3
"""Cut a year window of EIA's ``N3045<ST>3`` delivered-gas series out of a committed dnav workbook.

``data/raw/gas-prices/eia_delivered_gas_<ST>_monthly_<first>-<last>.csv`` — EIA
monthly *Natural Gas Price Sold to Electric Power Consumers* ($/Mcf) for one
state — was transcribed by lane SOCO-12 by hand from the key-free dnav history
workbook committed beside it (``eia_N3045<ST>3m_<pull-date>.xls``; provenance
``data/raw/gas-prices/SOURCES_soco_gas.md``). This script is that transcription
as a committed instrument, so a further window (the SOCO 2019-2022 backcast
years, I-SOCO 2026-09-24) is the same construction:

* the workbook's ``Data 1`` sheet — row 1 carries the ``Sourcekey``
  (``series``), row 2 the series title (``description``), rows 3+ the
  mid-month date serial and the value;
* one row per month of the window, ``period`` = ``YYYY-MM``; ``value`` is the
  published figure at two decimals, ``NA`` where EIA publishes none;
* the SPP-11 per-state schema ``period, series, description, area-name,
  process-name, value, units``, written by :mod:`csv` (CRLF line endings, as
  every committed sibling).

No network, no key: the workbook is already committed. ``--check`` proves the
committed window regenerates byte-for-byte before a new window is written.

Usage::

    python scripts/data/cut_eia_state_delivered_gas_xls.py --state AL GA MS \
        --pull-date 2026-09-13 --first-year 2023 --last-year 2025 --check
    python scripts/data/cut_eia_state_delivered_gas_xls.py --state AL GA MS \
        --pull-date 2026-09-13 --first-year 2019 --last-year 2022
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import GAS_PRICES_DIR  # noqa: E402

FIELDS: tuple[str, ...] = (
    "period",
    "series",
    "description",
    "area-name",
    "process-name",
    "value",
    "units",
)
PROCESS_NAME = "Price Sold to Electric Power Consumers"
UNITS = "$/MCF"


def workbook_path(state: str, pull_date: str) -> Path:
    """Committed dnav workbook for ``state`` pulled on ``pull_date``."""
    return GAS_PRICES_DIR / f"eia_N3045{state}3m_{pull_date}.xls"


def csv_path(state: str, first_year: int, last_year: int) -> Path:
    """Committed per-state CSV for the ``[first_year, last_year]`` window."""
    return (
        GAS_PRICES_DIR
        / f"eia_delivered_gas_{state}_monthly_{first_year}-{last_year}.csv"
    )


def render(state: str, pull_date: str, first_year: int, last_year: int) -> str:
    """Return the CSV text for one state's window, cut from its committed workbook."""
    sheet = pd.read_excel(
        workbook_path(state, pull_date), sheet_name="Data 1", header=None
    )
    series = str(sheet.iloc[1, 1])
    description = str(sheet.iloc[2, 1])
    body = sheet.iloc[3:, :2].copy()
    body.columns = ["date", "value"]
    body["date"] = pd.to_datetime(body["date"])
    body = body[body["date"].dt.year.between(first_year, last_year)]
    by_period = {d.strftime("%Y-%m"): v for d, v in zip(body["date"], body["value"])}
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(FIELDS)
    for period in pd.period_range(f"{first_year}-01", f"{last_year}-12", freq="M"):
        key = period.strftime("%Y-%m")
        value = by_period.get(key)
        cell = "NA" if value is None or pd.isna(value) else f"{float(value):.2f}"
        writer.writerow(
            [key, series, description, f"USA-{state}", PROCESS_NAME, cell, UNITS]
        )
    return buf.getvalue()


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--state", nargs="+", required=True)
    ap.add_argument(
        "--pull-date", required=True, help="the committed workbook's date stamp"
    )
    ap.add_argument("--first-year", type=int, required=True)
    ap.add_argument("--last-year", type=int, required=True)
    ap.add_argument(
        "--check",
        action="store_true",
        help="byte-compare against the committed CSV instead of writing",
    )
    a = ap.parse_args()
    failed = False
    for state in a.state:
        text = render(state, a.pull_date, a.first_year, a.last_year)
        path = csv_path(state, a.first_year, a.last_year)
        if a.check:
            same = path.read_bytes() == text.encode()
            failed |= not same
            print(f"{path.name}: {'BYTE-IDENTICAL' if same else 'DIFFERS'}")
            continue
        path.write_bytes(text.encode())
        n = text.count("\n") - 1
        published = n - text.count(",NA,")
        print(f"wrote {path.name}: {n} months, {published} published")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
