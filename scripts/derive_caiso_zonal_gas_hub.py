#!/usr/bin/env python
"""Derive CAISO per-zone gas-hub basis rows from the scraped EIA weekly prints.

Builds ``data/raw/caiso_zonal_gas_hub.csv`` — the CAISO analogue of the
committed ``pjm_zonal_gas_hub.csv`` / ``miso_zonal_gas_hub.csv`` /
``ercot_zonal_gas_hub.csv`` tables — from the measured PG&E Citygate and SoCal
Citygate Wednesday spot prints scraped by
``scripts/fetch_pge_socal_citygate_daily.py`` (EIA Natural Gas Weekly Update
archive narrative, NGI Daily GPI prints).

Zone → hub mapping (the two LDC systems CAISO's gas fleet actually buys from):

  * **NP15, ZP26** → PG&E Citygate (the PG&E backbone serves both the Bay Area
    and the San Joaquin Valley between Paths 15 and 26)
  * **SP15**       → SoCal Citygate (SoCalGas/SDG&E system)

Each ``basis_vs_hh_usd_mmbtu`` is the hub's annual mean minus the Henry Hub
annual mean **computed month-balanced over the same covered weeks** (mean of
monthly means, both series restricted to weeks where the hub was quoted), so
the uneven weekly narrative coverage (winter holes: Dec-2024 PG&E, Dec-2025
both hubs) cannot seasonally bias the annual level. Henry Hub daily prints come
from the sibling ``caiso_citygate_daily.csv`` (same EIA pages). Coverage (n
weeks, covered months) is recorded in each row's ``source`` string.

Like every zonal hub table, the LEVEL of these rows never reaches the solve:
``apply_caiso_zonal_gas_basis`` re-centres to a gas-capacity-weighted mean of
zero (the ERCOT/PJM/MISO convention), so the calibrated CAISO aggregate gas
level is preserved and ONLY the measured cross-zonal spread moves dispatch.
Nothing here is fitted to any residual (CLAUDE.md rules 13/14/21/24).

Usage:
    python scripts/derive_caiso_zonal_gas_hub.py            # derive + write CSV
    python scripts/derive_caiso_zonal_gas_hub.py --dry-run  # print only
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent

WEEKLY_PATH = REPO / "data" / "raw" / "gas-prices" / "pge_socal_citygate_weekly.csv"
COMPOSITE_PATH = REPO / "data" / "raw" / "gas-prices" / "caiso_citygate_daily.csv"
OUT_PATH = REPO / "data" / "raw" / "caiso_zonal_gas_hub.csv"

# Model zone -> (weekly-CSV column, hub label) mapping.
ZONE_HUBS: dict[str, tuple[str, str]] = {
    "NP15": ("pge_citygate_usd_mmbtu", "PG&E Citygate"),
    "ZP26": ("pge_citygate_usd_mmbtu", "PG&E Citygate"),
    "SP15": ("socal_citygate_usd_mmbtu", "SoCal Citygate"),
}

SOURCE_TMPL = (
    "{hub} weekly Wednesday prints (EIA NG Weekly Update archive narrative, "
    "NGI Daily GPI; scripts/fetch_pge_socal_citygate_daily.py) minus Henry Hub "
    "same-week prints; month-balanced mean over {n} weeks / {months} months"
)


def _month_balanced_basis(
    weekly: pd.DataFrame, hub_col: str, year: int
) -> tuple[float, int, int] | None:
    """Return ``(basis_vs_hh, n_weeks, n_months)`` for one hub-year, or None.

    Restricts to weeks where BOTH the hub and Henry Hub were quoted, averages
    the per-week (hub − HH) spread within each month, then averages the monthly
    means — so unevenly covered months carry equal weight.
    """
    sub = weekly[
        (weekly["date"].dt.year == year)
        & weekly[hub_col].notna()
        & weekly["henry_hub_usd_mmbtu"].notna()
    ].copy()
    if sub.empty:
        return None
    sub["spread"] = sub[hub_col] - sub["henry_hub_usd_mmbtu"]
    monthly = sub.groupby(sub["date"].dt.month)["spread"].mean()
    return float(monthly.mean()), int(len(sub)), int(len(monthly))


def derive_rows(years: tuple[int, ...]) -> list[dict]:
    """Derive one CSV row per (zone, year) from the scraped weekly prints."""
    weekly = pd.read_csv(WEEKLY_PATH, parse_dates=["date"])
    hh = pd.read_csv(COMPOSITE_PATH, parse_dates=["date"])[
        ["date", "henry_hub_usd_mmbtu"]
    ]
    weekly = weekly.merge(hh, on="date", how="left")

    rows: list[dict] = []
    for year in years:
        for zone, (hub_col, hub_label) in ZONE_HUBS.items():
            res = _month_balanced_basis(weekly, hub_col, year)
            if res is None:
                print(f"  {zone} {year}: NO COVERAGE — row omitted", file=sys.stderr)
                continue
            basis, n_weeks, n_months = res
            rows.append(
                {
                    "zone": zone,
                    "year": year,
                    "basis_vs_hh_usd_mmbtu": round(basis, 3),
                    "hub": hub_label,
                    "source": SOURCE_TMPL.format(
                        hub=hub_label, n=n_weeks, months=n_months
                    ),
                }
            )
    return rows


def main() -> None:
    """CLI: derive the CAISO zonal gas-hub basis rows and write the CSV."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--dry-run", action="store_true", help="print only; don't write")
    args = ap.parse_args()

    rows = derive_rows(tuple(args.years))
    print(f"{'zone':6s} {'year':4s} {'basis':>7s}  hub / coverage")
    for r in rows:
        print(
            f"{r['zone']:6s} {r['year']:4d} {r['basis_vs_hh_usd_mmbtu']:+7.3f}  "
            f"{r['hub']} ({r['source'].split('mean over ')[1]})"
        )
    # The spread the mean-zero applier will realize (NP15/ZP26 minus SP15).
    by = {(r["zone"], r["year"]): r["basis_vs_hh_usd_mmbtu"] for r in rows}
    for year in args.years:
        if ("NP15", year) in by and ("SP15", year) in by:
            print(
                f"  {year}: realized N-S gas spread (PG&E - SoCal) = "
                f"{by[('NP15', year)] - by[('SP15', year)]:+.3f} $/MMBtu"
            )

    if args.dry_run:
        print("\n[dry-run] CSV not written")
        return
    with OUT_PATH.open("w", newline="") as fh:
        w = csv.DictWriter(
            fh, fieldnames=["zone", "year", "basis_vs_hh_usd_mmbtu", "hub", "source"]
        )
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"\nwrote {len(rows)} rows -> {OUT_PATH}")


if __name__ == "__main__":
    main()
