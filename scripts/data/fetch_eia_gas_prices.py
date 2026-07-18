#!/usr/bin/env python3
"""Fetch Henry Hub spot + state citygate gas prices from the EIA API, for every
ISO, and refresh the model's gas-price inputs.

The model prices marginal gas two ways: a Henry-Hub-spot path (the default for
most ISOs, ``resolve_annual_gas_price`` / the monthly + daily HH series) and a
measured hub-basis overlay (``apply_hub_basis_overlay``: gas repriced at HH-month
+ the ISO's named-hub basis). The hub basis was filled only for NEISO (a licensed
ISO-NE MA gas index); every other ISO was header-only. This script fills it for
ALL ISOs from a free, regenerable EIA source — the state **citygate** price (what
gas costs delivered to the LDC city gate, the closest free public proxy for the
ISO's marginal gas trading region) minus Henry Hub — and refreshes the Henry Hub
monthly + daily series the rest of the gas path rides on.

Why citygate (not EIA-923 delivered): a dispatched CC's marginal offer is the gas
*commodity at the trading hub*; the firm pipeline reservation that gets gas to the
plant is a sunk fixed cost (see DIAGNOSIS-caiso-import-ladder-2026-06-19, lever B).
The state citygate is the public, regenerable, forward-applicable measure of that
hub level. It is a documented PROXY for the ISO's marginal trading point (SoCal /
PG&E for CAISO, Transco Z6 for NYISO, Chicago for MISO, ...), the "EIA-citygate-
proxy fill" anticipated in fuel.py's gas-basis comment.

Outputs (committed by .github/workflows/fetch-eia-gas-prices.yml on an open-egress
runner; the Claude remote env blocks api.eia.gov):
  * data/raw/gas-prices/henry_hub_monthly.csv  (year, month, price_usd_mmbtu)
  * data/raw/gas-prices/henry_hub_daily.csv    (date, price_usd_mmbtu)
  * data/raw/gas_basis_by_iso_month.csv        (iso, year, month, hub,
       basis_usd_mmbtu, source) — EIA-proxy rows ADDED without clobbering
       existing measured rows (e.g. NEISO's licensed AGT index is preserved).

EIA API v2 docs: https://www.eia.gov/opendata/documentation.php
Free key: https://www.eia.gov/opendata/register.php

Usage:
    EIA_API_KEY=... python scripts/data/fetch_eia_gas_prices.py
    EIA_API_KEY=... python scripts/data/fetch_eia_gas_prices.py --datasets citygate \
        --isos CAISO NYISO --start-year 2022
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

REPO = Path(__file__).resolve().parent.parent.parent
GAS_DIR = REPO / "data" / "raw" / "gas-prices"
BASIS_PATH = REPO / "data" / "raw" / "gas_basis_by_iso_month.csv"

BASE = "https://api.eia.gov/v2"

# Henry Hub Natural Gas Spot Price (Dollars per Million Btu), EIA "Natural Gas
# Spot and Futures Prices (NYMEX)" dataset. RNGWHHD = daily, RNGWHHM = monthly.
HH_ROUTE = "natural-gas/pri/fut"
HH_DAILY_SERIES = "RNGWHHD"
# NOTE: the monthly Henry Hub series (RNGWHHM) returns EMPTY on this route
# (confirmed by --dry-run), so the monthly average is derived from RNGWHHD.

# State citygate price series (Dollars per Thousand Cubic Feet), EIA "Natural Gas
# Prices" summary dataset. Series id N3050<state>3 = citygate price, monthly.
CITYGATE_ROUTE = "natural-gas/pri/sum"

# 1 Mcf of pipeline-quality gas ~ 1.036 MMBtu (EIA average heat content); citygate
# is published $/Mcf, every other model gas price is $/MMBtu.
MMBTU_PER_MCF = 1.036

# ISO -> (state, named trading hub the state citygate proxies). The state citygate
# is a documented PROXY for the ISO's marginal gas trading region, chosen as the
# region the ISO's price-setting gas units buy from. NEISO keeps its licensed AGT
# index (existing rows are preserved); the EIA MA citygate only fills gaps.
ISO_CITYGATE: dict[str, tuple[str, str]] = {
    "CAISO": ("CA", "SoCal / PG&E Citygate (EIA CA citygate proxy)"),
    "ERCOT": ("TX", "Houston Ship Channel region (EIA TX citygate proxy)"),
    "PJM": ("PA", "Transco Z6 / Appalachia (EIA PA citygate proxy)"),
    "MISO": ("IL", "Chicago Citygate (EIA IL citygate proxy)"),
    "NYISO": ("NY", "Transco Z6 NY / Iroquois (EIA NY citygate proxy)"),
    "NEISO": ("MA", "Algonquin Citygate (EIA MA citygate proxy)"),
}


def _get(route: str, params: dict, key: str, sleep_s: float) -> list[dict]:
    """Page through an EIA v2 data route, returning all rows. Raises on failure."""
    rows: list[dict] = []
    offset = 0
    page = 5000
    while True:
        q = {
            "api_key": key,
            "data[0]": "value",
            "length": page,
            "offset": offset,
            **params,
        }
        url = f"{BASE}/{route}/data/?{urlencode(q, doseq=True)}"
        try:
            with urlopen(url, timeout=60) as fh:
                import json

                payload = json.loads(fh.read().decode())
        except (HTTPError, URLError) as exc:
            raise RuntimeError(f"EIA request failed ({route}): {exc}") from exc
        chunk = payload.get("response", {}).get("data", [])
        rows.extend(chunk)
        if len(chunk) < page:
            break
        offset += page
        time.sleep(sleep_s)
    return rows


def _probe(route: str, params: dict, key: str, label: str) -> bool:
    """One cheap EIA call (length=5) to validate a series id. Returns True if it
    returned rows. Prints a one-line summary; never writes files."""
    q = {"api_key": key, "data[0]": "value", "length": 5, "offset": 0, **params}
    url = f"{BASE}/{route}/data/?{urlencode(q, doseq=True)}"
    try:
        with urlopen(url, timeout=60) as fh:
            import json

            payload = json.loads(fh.read().decode())
    except (HTTPError, URLError) as exc:
        print(f"  {label}: FAIL — {exc}")
        return False
    resp = payload.get("response", {})
    rows = resp.get("data", [])
    total = resp.get("total", "?")
    if not rows:
        print(
            f"  {label}: EMPTY — series id likely wrong "
            f"(warning: {payload.get('response', {}).get('warnings')})"
        )
        return False
    units = rows[0].get("units", "?")
    periods = [r.get("period") for r in rows]
    print(
        f"  {label}: OK — {total} rows total, units={units}, "
        f"sample periods {periods[0]}..{periods[-1]}"
    )
    return True


def _facet_values(route: str, facet: str, key: str) -> list[tuple[str, str]]:
    """Return (id, name) for every value of a route's facet (EIA metadata).

    ``GET /v2/<route>/facet/<facet>/`` lists the valid ids — the authoritative
    way to discover, e.g., the real citygate ``series`` ids without guessing.
    """
    url = f"{BASE}/{route}/facet/{facet}/?api_key={key}"
    try:
        with urlopen(url, timeout=60) as fh:
            import json

            payload = json.loads(fh.read().decode())
    except (HTTPError, URLError) as exc:
        print(f"  facet metadata FAIL ({route}/{facet}): {exc}")
        return []
    facets = payload.get("response", {}).get("facets", [])
    out = []
    for f in facets:
        out.append((f.get("id", ""), f.get("name") or f.get("alias") or ""))
    return out


def dry_run(key: str, isos: list[str]) -> int:
    """Validate Henry Hub series and DISCOVER the citygate series ids.

    HH is probed (it already works). For citygate the current ``N3050<ST>3``
    guess returned +0 rows in the first workflow run, so this prints EIA's own
    list of citygate series ids (from the series-facet metadata) — copy the right
    ids into ``ISO_CITYGATE`` / the citygate query. Returns an exit code.
    """
    ok = True
    print("=== Henry Hub (monthly is derived from daily) ===")
    ok &= _probe(
        HH_ROUTE,
        {"frequency": "daily", "facets[series][]": HH_DAILY_SERIES},
        key,
        f"{HH_DAILY_SERIES} (HH daily)",
    )

    print("=== Citygate: current guesses ===")
    states = {ISO_CITYGATE[i][0] for i in isos}
    for iso in isos:
        state, _ = ISO_CITYGATE[iso]
        _probe(
            CITYGATE_ROUTE,
            {"frequency": "monthly", "facets[series][]": f"N3050{state}3"},
            key,
            f"N3050{state}3 ({iso})",
        )

    print(
        f"=== Citygate: EIA's actual series ids matching 'Citygate' "
        f"(route {CITYGATE_ROUTE}) ==="
    )
    found = [
        (sid, name)
        for sid, name in _facet_values(CITYGATE_ROUTE, "series", key)
        if "citygate" in name.lower()
    ]
    if not found:
        print(
            "  none found on this route — citygate may live on a different "
            "route (try natural-gas/pri/sum vs a state route); inspect "
            f"{BASE}/{CITYGATE_ROUTE}/facet/series/"
        )
        ok = False
    for sid, name in sorted(found):
        flag = (
            " <-- one of our states"
            if any(f" {s} " in f" {name} " or name.startswith(s) for s in states)
            else ""
        )
        print(f"  {sid}: {name}{flag}")
    print("dry-run complete — set ISO_CITYGATE/query from the list above.")
    return 0 if ok else 1


def fetch_henry_hub(key: str, sleep_s: float) -> None:
    """Refresh henry_hub_daily.csv, and henry_hub_monthly.csv derived from it.

    The daily spot series (RNGWHHD) returns full history; the monthly series
    (RNGWHHM) comes back EMPTY on this route (confirmed by --dry-run), so the
    monthly average is derived from the daily series — a defensible monthly value
    and exactly what the citygate basis join needs.
    """
    GAS_DIR.mkdir(parents=True, exist_ok=True)

    daily = _get(
        HH_ROUTE,
        {"frequency": "daily", "facets[series][]": HH_DAILY_SERIES},
        key,
        sleep_s,
    )
    drows = sorted(
        (r["period"], round(float(r["value"]), 4))
        for r in daily
        if r.get("value") not in (None, "")
    )
    _write_csv(GAS_DIR / "henry_hub_daily.csv", ["date", "price_usd_mmbtu"], drows)
    print(f"  henry_hub_daily.csv: {len(drows)} rows")

    # Monthly = mean of the daily spot in each calendar month.
    buckets: dict[tuple[int, int], list[float]] = {}
    for date, val in drows:
        y, m = (int(x) for x in date.split("-")[:2])
        buckets.setdefault((y, m), []).append(val)
    mrows = sorted((y, m, round(sum(v) / len(v), 4)) for (y, m), v in buckets.items())
    _write_csv(
        GAS_DIR / "henry_hub_monthly.csv", ["year", "month", "price_usd_mmbtu"], mrows
    )
    print(f"  henry_hub_monthly.csv: {len(mrows)} rows (derived from daily)")


def fetch_citygate(key: str, isos: list[str], start_year: int, sleep_s: float) -> None:
    """Add per-ISO citygate-minus-Henry-Hub basis rows (preserving existing)."""
    hh = _henry_hub_monthly_map()
    existing, header = _read_basis()
    have = {(r["iso"], int(r["year"]), int(r["month"])) for r in existing}
    added = 0
    for iso in isos:
        state, hub = ISO_CITYGATE[iso]
        series = f"N3050{state}3"
        try:
            data = _get(
                CITYGATE_ROUTE,
                {"frequency": "monthly", "facets[series][]": series},
                key,
                sleep_s,
            )
        except RuntimeError as exc:
            print(f"  {iso} ({series}): SKIP — {exc}", file=sys.stderr)
            continue
        n = 0
        for r in data:
            if r.get("value") in (None, ""):
                continue
            y, m = (int(x) for x in r["period"].split("-")[:2])
            if y < start_year or (iso, y, m) in have:
                continue
            hh_price = hh.get((y, m))
            if hh_price is None:
                continue
            citygate_mmbtu = float(r["value"]) / MMBTU_PER_MCF
            basis = round(citygate_mmbtu - hh_price, 4)
            existing.append(
                {
                    "iso": iso,
                    "year": y,
                    "month": m,
                    "hub": hub,
                    "basis_usd_mmbtu": basis,
                    "source": f"EIA {series} citygate - Henry Hub ({HH_DAILY_SERIES} "
                    f"monthly mean)",
                }
            )
            have.add((iso, y, m))
            n += 1
        added += n
        print(f"  {iso} ({series}): +{n} basis rows")
        time.sleep(sleep_s)
    existing.sort(key=lambda r: (r["iso"], int(r["year"]), int(r["month"])))
    _write_dictcsv(BASIS_PATH, header, existing)
    print(f"  gas_basis_by_iso_month.csv: +{added} rows ({len(existing)} total)")


def _henry_hub_monthly_map() -> dict[tuple[int, int], float]:
    path = GAS_DIR / "henry_hub_monthly.csv"
    out: dict[tuple[int, int], float] = {}
    if path.exists():
        with path.open() as fh:
            for row in csv.DictReader(fh):
                out[(int(row["year"]), int(row["month"]))] = float(
                    row["price_usd_mmbtu"]
                )
    return out


def _read_basis() -> tuple[list[dict], list[str]]:
    header = ["iso", "year", "month", "hub", "basis_usd_mmbtu", "source"]
    if not BASIS_PATH.exists():
        return [], header
    with BASIS_PATH.open() as fh:
        reader = csv.DictReader(fh)
        return [dict(r) for r in reader], reader.fieldnames or header


def _write_csv(path: Path, header: list[str], rows: list[tuple]) -> None:
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def _write_dictcsv(path: Path, header: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--datasets",
        nargs="+",
        default=["henry-hub", "citygate"],
        choices=["henry-hub", "citygate"],
    )
    ap.add_argument(
        "--isos", nargs="+", default=list(ISO_CITYGATE), choices=list(ISO_CITYGATE)
    )
    ap.add_argument(
        "--start-year",
        type=int,
        default=2015,
        help="earliest citygate-basis year to add (default 2015)",
    )
    ap.add_argument(
        "--sleep", type=float, default=1.0, help="seconds between EIA requests"
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="validate every series id with one cheap call each and "
        "print row counts; write nothing",
    )
    args = ap.parse_args()

    key = os.environ.get("EIA_API_KEY")
    if not key:
        print(
            "ERROR: set EIA_API_KEY (free: https://www.eia.gov/opendata/register.php)",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.dry_run:
        sys.exit(dry_run(key, args.isos))

    if "henry-hub" in args.datasets:
        print("=== Henry Hub spot (RNGWHHM / RNGWHHD) ===")
        fetch_henry_hub(key, args.sleep)
    if "citygate" in args.datasets:
        print("=== State citygate basis over Henry Hub ===")
        fetch_citygate(key, args.isos, args.start_year, args.sleep)
    print("done.")


if __name__ == "__main__":
    main()
