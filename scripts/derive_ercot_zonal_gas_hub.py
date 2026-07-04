#!/usr/bin/env python3
"""Derive ERCOT per-zone delivered-gas basis rows from EIA-923 Schedule 5.

Extends ``data/raw/ercot_zonal_gas_hub.csv`` to a new year with the SAME
methodology as the committed 2023-2025 rows
(docs/ercot-zonal-gas-basis-ct-relocation-2026-06.md):

* **North / South_Central / South** — quantity-weighted delivered gas price of
  the zone's Schedule-5-reporting plants (F923 "Page 5 Fuel Receipts and
  Costs": ``FUEL_COST`` cents/MMBtu x ``QUANTITY x heat content`` MMBtu),
  minus the annual-mean on-disk Henry Hub, plants zoned via the model fleet's
  own plant->zone assignment. ``--validate`` reproduces the committed 2023
  coverage exactly (North 5 plants/61M MMBtu, South_Central 12/175M,
  South 3/9M) and the basis to within ~$0.03 (residual = F923
  final-vs-revision vintage noise).
* **Northeast** — proxy -> North (no Sch5 gas receipts in zone; committed
  convention).
* **Houston** — flat -0.15 HSC~HH convention (no Sch5 sample; committed
  convention).
* **West / Panhandle** — Waha annual average minus HH; the Waha average is NOT
  derivable from an in-repo/API source, so these rows are written only when
  ``--waha-annual-avg`` (and ``--waha-source``) are passed explicitly. Absent
  zones degrade to a zero spread in ``apply_ercot_zonal_gas_basis``.

A partial year (e.g. 2026 with receipts published Jan-Apr) is labelled
``PARTIAL YEAR`` in ``source`` and uses the HH mean over the same months.
Existing rows are never modified.

Usage:
    python scripts/derive_ercot_zonal_gas_hub.py --validate \
        --f923 /path/EIA923_Schedules_2_3_4_5_M_12_2023_Final_Revision.xlsx
    python scripts/derive_ercot_zonal_gas_hub.py --year 2022 \
        --f923 /path/EIA923_Schedules_2_3_4_5_M_12_2022_Final_Revision.xlsx
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import warnings
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

HUB_PATH = REPO / "data" / "raw" / "ercot_zonal_gas_hub.csv"
HH_MONTHLY_PATH = REPO / "data" / "raw" / "gas-prices" / "henry_hub_monthly.csv"

_MONTH_ABBR = (
    "",
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)

# Committed per-zone conventions (data/raw/ercot_zonal_gas_hub.csv 2023-2025).
_SCH5_ZONES = ("North", "South_Central", "South")
_HUB_LABEL = {
    "North": "North/East TX",
    "Northeast": "North/East TX",
    "South_Central": "South TX",
    "South": "South TX/Agua Dulce",
    "Houston": "Houston Ship Channel",
    "West": "Waha",
    "Panhandle": "Waha",
}
# Houston: HSC ~ Henry Hub, slight discount; no Sch5 sample (committed rows).
_HOUSTON_BASIS = -0.15


def _fleet_zone_map() -> dict[int, str]:
    """Plant code -> model zone from the ERCOT fleet's own assignment."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_fleet_from_csv

    zmap: dict[int, str] = {}
    for g in load_fleet_from_csv("ERCOT", get_iso_config("ERCOT")):
        m = re.match(r"(\d+)", str(g.unit_id))
        if m:
            zmap.setdefault(int(m.group(1)), g.zone)
    return zmap


def _henry_hub() -> dict[tuple[int, int], float]:
    """(year, month) -> Henry Hub $/MMBtu from the committed monthly CSV."""
    out: dict[tuple[int, int], float] = {}
    with HH_MONTHLY_PATH.open() as fh:
        for row in csv.DictReader(fh):
            out[(int(row["year"]), int(row["month"]))] = float(row["price_usd_mmbtu"])
    return out


def _read_sch5_tx_gas(f923: Path) -> pd.DataFrame:
    """TX natural-gas Schedule-5 receipt rows with cost, as $/MMBtu + MMBtu.

    Handles both workbook layouts (final revisions header at row 4, monthly
    early releases at row 3) by locating the ``YEAR``/``Plant Id`` header row.
    """
    warnings.filterwarnings("ignore", message="Cannot parse header or footer")
    probe = pd.read_excel(
        f923, sheet_name="Page 5 Fuel Receipts and Costs", header=None, nrows=8
    )
    header_row = next(
        i for i, r in probe.iterrows() if str(r.iloc[0]).strip() == "YEAR"
    )
    df = pd.read_excel(
        f923, sheet_name="Page 5 Fuel Receipts and Costs", skiprows=header_row
    )
    df.columns = [str(c).replace("\n", " ").strip() for c in df.columns]
    tx = df[(df["Plant State"] == "TX") & (df["FUEL_GROUP"] == "Natural Gas")].copy()
    tx["usd_mmbtu"] = pd.to_numeric(tx["FUEL_COST"], errors="coerce") / 100.0
    tx["mmbtu"] = pd.to_numeric(tx["QUANTITY"], errors="coerce") * pd.to_numeric(
        tx["Average Heat Content"], errors="coerce"
    )
    tx = tx.dropna(subset=["usd_mmbtu", "mmbtu"])
    tx["plant_id"] = tx["Plant Id"].astype(int)
    tx["month"] = tx["MONTH"].astype(int)
    tx["year"] = tx["YEAR"].astype(int)
    return tx


def _zone_stats(
    tx: pd.DataFrame, year: int, hh: dict[tuple[int, int], float]
) -> tuple[dict[str, tuple[float, int, float]], list[int]]:
    """Per-zone (basis, n_plants, mmbtu) for ``year`` + the months covered."""
    zmap = _fleet_zone_map()
    sub = tx[tx["year"] == year].copy()
    months = sorted(sub["month"].unique())
    if not months:
        return {}, []
    hh_mean = sum(hh[(year, m)] for m in months) / len(months)
    sub["zone"] = sub["plant_id"].map(zmap)
    out: dict[str, tuple[float, int, float]] = {}
    for zone, g in sub.dropna(subset=["zone"]).groupby("zone"):
        if zone not in _SCH5_ZONES:
            continue
        price = (g["usd_mmbtu"] * g["mmbtu"]).sum() / g["mmbtu"].sum()
        out[zone] = (price - hh_mean, g["plant_id"].nunique(), g["mmbtu"].sum())
    return out, months


def validate(f923: Path) -> int:
    """Recompute the committed Sch5 zones for the workbook's year."""
    tx = _read_sch5_tx_gas(f923)
    year = int(tx["year"].mode().iloc[0])
    stats, months = _zone_stats(tx, year, _henry_hub())
    with HUB_PATH.open() as fh:
        committed = {
            (r["zone"], int(r["year"])): float(r["basis_vs_hh_usd_mmbtu"])
            for r in csv.DictReader(fh)
        }
    bad = 0
    for zone, (basis, n, mmbtu) in sorted(stats.items()):
        c = committed.get((zone, year))
        line = (
            f"  {zone:14s} {year}: recomputed {basis:+.2f} "
            f"({n} plants, {mmbtu / 1e6:.0f}M MMBtu)"
        )
        if c is None:
            print(f"{line} — no committed row")
        else:
            ok = abs(basis - c) <= 0.05
            bad += 0 if ok else 1
            print(f"{line} committed {c:+.2f} {'OK' if ok else 'MISMATCH'}")
    print(f"months covered: {months}")
    return bad


def extend(
    year: int,
    f923: Path,
    waha: float | None,
    waha_source: str,
    waha_neg: tuple[str, str] = ("", ""),
) -> None:
    """Append the new year's zone rows (existing rows never modified)."""
    with HUB_PATH.open() as fh:
        reader = csv.DictReader(fh)
        header = list(reader.fieldnames or [])
        rows = [dict(r) for r in reader]
    have = {(r["zone"], int(r["year"])) for r in rows}
    tx = _read_sch5_tx_gas(f923)
    stats, months = _zone_stats(tx, year, _henry_hub())
    partial = (
        ""
        if len(months) >= 12
        else (
            f"; PARTIAL YEAR: {_MONTH_ABBR[months[0]]}-{_MONTH_ABBR[months[-1]]} "
            f"{year} published receipts only (winter-weighted); re-derive when "
            f"EIA publishes the rest"
        )
    )

    def add(zone: str, basis: float, source: str, neg=("", "")) -> None:
        if (zone, year) in have:
            print(f"  {zone} {year}: exists, skipped")
            return
        row = {
            "zone": zone,
            "year": year,
            "basis_vs_hh_usd_mmbtu": round(basis, 2),
            "hub": _HUB_LABEL[zone],
            "source": source,
            "neg_day_freq": neg[0],
            "neg_day_freq_source": neg[1],
        }
        rows.append({k: row.get(k, "") for k in header})
        print(f"  + {zone} {year}: {basis:+.2f}")

    for zone in ("North", "South_Central", "South"):
        if zone not in stats:
            print(f"  {zone} {year}: no Sch5 cost reporters; NOT written")
            continue
        basis, n, mmbtu = stats[zone]
        add(
            zone,
            basis,
            f"EIA-923 Sch5 qty-weighted delivered gas minus HH "
            f"({n} plants {mmbtu / 1e6:.0f}M MMBtu){partial}",
        )
    if "North" in stats:
        add(
            "Northeast",
            stats["North"][0],
            f"proxy->North (East TX; no Sch5 gas receipts reported in zone){partial}",
        )
    add(
        "Houston",
        _HOUSTON_BASIS,
        "HSC ~ Henry Hub (Gulf-Coast demand/LNG hub; slight discount; "
        "NGI/EIA) - no Sch5 sample",
    )
    if waha is not None:
        hh = _henry_hub()
        hh_mean = sum(hh[(year, m)] for m in months) / len(months)
        for zone in ("West", "Panhandle"):
            src = (
                f"Waha annual avg ${waha:.2f} ({waha_source}) minus HH "
                f"${hh_mean:.2f} (on-disk henry_hub_monthly){partial}"
                if zone == "West"
                else f"proxy->Waha (Permian; carries 0.0 modeled load){partial}"
            )
            neg_src = waha_neg[1] if zone == "West" else f"proxy->Waha West {year}"
            add(zone, waha - hh_mean, src, neg=(waha_neg[0], neg_src))
    else:
        print(
            f"  West/Panhandle {year}: SKIPPED — pass --waha-annual-avg "
            f"(+ --waha-source); no reproducible in-repo Waha source. "
            f"Absent zones degrade to a 0 spread in apply_ercot_zonal_gas_basis."
        )

    zone_order = list(dict.fromkeys([r["zone"] for r in rows]))
    rows.sort(key=lambda r: (zone_order.index(r["zone"]), int(r["year"])))
    with HUB_PATH.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {HUB_PATH} ({len(rows)} rows)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--f923",
        type=Path,
        required=True,
        help="EIA-923 Schedules_2_3_4_5 workbook (final or monthly)",
    )
    ap.add_argument("--year", type=int, default=None)
    ap.add_argument(
        "--validate",
        action="store_true",
        help="recompute the workbook year's committed rows; write nothing",
    )
    ap.add_argument(
        "--waha-annual-avg",
        type=float,
        default=None,
        help="Waha annual average spot $/MMBtu (explicit, sourced)",
    )
    ap.add_argument(
        "--waha-source",
        default="NGI/EIA NG Weekly",
        help="citation for --waha-annual-avg",
    )
    ap.add_argument(
        "--waha-neg-day-freq",
        default="",
        help="measured Waha negative-day frequency for the year (optional)",
    )
    ap.add_argument(
        "--waha-neg-day-freq-source",
        default="",
        help="citation for --waha-neg-day-freq",
    )
    args = ap.parse_args()
    if args.validate:
        sys.exit(1 if validate(args.f923) else 0)
    if args.year is None:
        sys.exit("--year is required unless --validate")
    extend(
        args.year,
        args.f923,
        args.waha_annual_avg,
        args.waha_source,
        waha_neg=(args.waha_neg_day_freq, args.waha_neg_day_freq_source),
    )


if __name__ == "__main__":
    main()
