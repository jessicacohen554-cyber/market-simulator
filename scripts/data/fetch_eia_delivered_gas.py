#!/usr/bin/env python3
"""Extend the ERCOT/PJM delivered-to-electric-power gas series to new years.

Extends two committed reference CSVs from the EIA API (route
``natural-gas/pri/sum``, series ``N3045<ST>3`` — monthly gas delivered to
electric-power consumers, $/Mcf), appending rows for years/months not yet
present and never touching existing rows:

* ``data/raw/ercot_electric_power_gas_price.csv`` — monthly N3045TX3 rows
  (year, month, price_usd_mcf, source).
* ``data/raw/pjm_zonal_gas_hub.csv`` — one annual basis row per PJM zone:
  ``mean over published months of (N3045<ST>3 / 1.036 − HenryHub_monthly)``.
  ``--validate`` reproduces every committed 2023-2025 value to ±0.001 from
  this exact formula, so extensions are methodology-identical. When a state's
  year is mostly EIA-withheld (the file's WV-2025 precedent), the row is
  proxied to the OH+PA Appalachian mean and says so in ``source``.

Partial years (e.g. 2026 with only Jan-Apr published) are labelled in
``source`` with the covered months; they are winter-weighted until EIA
publishes the remaining months and should be re-extended then (delete the
partial row and re-run, citing the data update — CLAUDE.md rule 23).

Usage:
    EIA_API_KEY=... python scripts/data/fetch_eia_delivered_gas.py --validate
    EIA_API_KEY=... python scripts/data/fetch_eia_delivered_gas.py --years 2022 2026
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import GAS_PRICES_DIR, RAW_DATA_DIR  # noqa: E402

sys.path.insert(0, str(REPO))
from scripts.lib.env_keys import get_api_key  # noqa: E402

ERCOT_EP_PATH = RAW_DATA_DIR / "ercot_electric_power_gas_price.csv"
PJM_ZONAL_PATH = RAW_DATA_DIR / "pjm_zonal_gas_hub.csv"
MISO_ZONAL_PATH = RAW_DATA_DIR / "miso_zonal_gas_hub.csv"
HH_MONTHLY_PATH = GAS_PRICES_DIR / "henry_hub_monthly.csv"

BASE = "https://api.eia.gov/v2/natural-gas/pri/sum/data/"
# 1 Mcf of pipeline-quality gas ~ 1.036 MMBtu (EIA average heat content).
MMBTU_PER_MCF = 1.036

# PJM zone -> (EIA state series suffix, hub label, source template) — the
# committed file's own crosswalk (data/raw/pjm_zonal_gas_hub.csv 2023-2025).
PJM_ZONE_STATE: dict[str, tuple[str, str, str]] = {
    "PJM_ComEd": ("IL", "Chicago Citygate (IL)", "Chicago Citygate / IL"),
    "PJM_AEP_Ohio": ("OH", "Appalachian (OH)", "Appalachian/Dominion South / OH"),
    "PJM_ATSI": ("OH", "Appalachian (OH)", "Appalachian/TETCO M2 / OH"),
    "PJM_West_APS": ("WV", "Appalachian (WV)", "Appalachian/Dominion South / WV"),
    "PJM_Central_PA": ("PA", "TETCO M3 (PA)", "TETCO M3/Transco Z6 / PA"),
    "PJM_Dominion": ("VA", "Transco Z6 (VA)", "Transco Z6/TETCO M3 / VA"),
    "PJM_EMAAC": ("NJ", "Transco Z6 non-NY (NJ)", "Transco Z6 non-NY/TETCO M3 / NJ"),
    "PJM_SWMAAC": ("MD", "Transco Z6 (MD)", "Transco Z6/TETCO M3 / MD"),
}
# States whose withheld years proxy to the Appalachian delivered-to-EP mean
# (the committed WV-2025 convention).
_APPALACHIAN_PROXY_STATES = ("OH", "PA")

# MISO zone -> (EIA state series suffix, hub label, source template) — the
# committed file's own crosswalk, read straight off
# data/raw/miso_zonal_gas_hub.csv's 2023-2025 ``hub``/``source`` columns.
# MISO-Plains rides IA (no MidCon hub of its own), and Indiana/East ride the
# IL Chicago Citygate print as the committed documented proxies (no N3045IN3 /
# N3045MI3 pull exists) — the crosswalk IS the proxy record, so nothing here
# invents a substitute the committed file did not already declare.
MISO_ZONE_STATE: dict[str, tuple[str, str, str]] = {
    "MISO-West": ("IA", "MidCon / Northern Natural (IA)", "IA"),
    "MISO-Plains": ("IA", "MidCon / Northern Natural (IA)", "IA"),
    "MISO-Illinois": ("IL", "Chicago Citygate (IL)", "IL"),
    "MISO-Indiana": (
        "IL",
        "Chicago Citygate (IL)",
        "IL; IN proxy pending N3045IN3 pull",
    ),
    "MISO-East": (
        "IL",
        "Chicago Citygate (IL)",
        "IL; WI/MI (MichCon) proxy pending N3045MI3 pull",
    ),
    "MISO-South": ("LA", "Gulf Coast (LA)", "LA"),
}

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


def _api_key(required: bool = True) -> str | None:
    """Resolve the EIA API key from the environment or the repo ``.env``."""
    return get_api_key(
        "EIA_API_KEY",
        required=required,
        hint="free at https://www.eia.gov/opendata/register.php",
    )


def _monthly_series_dnav(sid: str) -> dict[tuple[int, int], float]:
    """Same series as :func:`_monthly_series`, from EIA's key-free dnav page.

    ``https://www.eia.gov/dnav/ng/hist/<sid>m.htm`` renders the full monthly
    history of an ``N3045<ST>3`` series as a year-per-row, month-per-column
    table — the same numbers the v2 API returns, published without
    registration. This is the transport when no ``EIA_API_KEY`` is available
    (the v2 API rejects unauthenticated calls outright), so a data-intake lane
    is not blocked on a credential. ``W`` (withheld), ``-``, ``NA`` and empty
    cells are skipped exactly as the API's null values are.
    """
    url = f"https://www.eia.gov/dnav/ng/hist/{sid.lower()}m.htm"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (market-sim data fetch)"})
    with urlopen(req, timeout=120) as fh:
        html = fh.read().decode("utf-8", errors="replace")
    out: dict[tuple[int, int], float] = {}
    row_re = re.compile(
        r"<td class='B4'>&nbsp;&nbsp;(\d{4})</td>"
        r"((?:\s*<td class='B3'>[^<]*</td>){12})"
    )
    for m in row_re.finditer(html):
        year = int(m.group(1))
        for i, cell in enumerate(
            re.findall(r"<td class='B3'>([^<]*)</td>", m.group(2)), start=1
        ):
            cell = cell.strip()
            if re.fullmatch(r"\d+(\.\d+)?", cell):
                out[(year, i)] = float(cell)
    if not out:
        raise RuntimeError(f"{url}: no monthly rows parsed (page layout changed?)")
    return out


def _monthly_series(sid: str, key: str | None) -> dict[tuple[int, int], float]:
    """All published (year, month) -> value rows of one EIA monthly series."""
    if not key:
        return _monthly_series_dnav(sid)
    url = (
        f"{BASE}?api_key={key}&data[0]=value&frequency=monthly"
        f"&facets[series][]={sid}&length=5000"
    )
    with urlopen(url, timeout=120) as fh:
        rows = json.load(fh)["response"]["data"]
    out = {}
    for r in rows:
        if r.get("value") in (None, ""):
            continue
        y, m = (int(x) for x in r["period"].split("-")[:2])
        out[(y, m)] = float(r["value"])
    return out


def _henry_hub_monthly() -> dict[tuple[int, int], float]:
    """(year, month) -> Henry Hub $/MMBtu from the committed monthly CSV."""
    out = {}
    with HH_MONTHLY_PATH.open() as fh:
        for row in csv.DictReader(fh):
            out[(int(row["year"]), int(row["month"]))] = float(row["price_usd_mmbtu"])
    return out


def _annual_basis(
    series: dict[tuple[int, int], float],
    hh: dict[tuple[int, int], float],
    year: int,
) -> tuple[float | None, list[int]]:
    """Mean monthly (delivered $/MMBtu − HH) over the year's published months."""
    months = [m for m in range(1, 13) if (year, m) in series and (year, m) in hh]
    if not months:
        return None, []
    basis = sum(
        series[(year, m)] / MMBTU_PER_MCF - hh[(year, m)] for m in months
    ) / len(months)
    return basis, months


def _months_label(months: list[int]) -> str:
    """Human label for a partial-year month span, e.g. ``Jan-Apr``."""
    return f"{_MONTH_ABBR[months[0]]}-{_MONTH_ABBR[months[-1]]}"


def extend_ercot_ep(years: list[int], key: str) -> int:
    """Append missing monthly N3045TX3 rows for the requested years."""
    with ERCOT_EP_PATH.open() as fh:
        reader = csv.DictReader(fh)
        header = list(reader.fieldnames or [])
        rows = [dict(r) for r in reader]
    have = {(int(r["year"]), int(r["month"])) for r in rows}
    tx = _monthly_series("N3045TX3", key)
    added = 0
    for year in years:
        for m in range(1, 13):
            if (year, m) in have or (year, m) not in tx:
                continue
            rows.append(
                {
                    "year": year,
                    "month": m,
                    "price_usd_mcf": round(tx[(year, m)], 2),
                    "source": "EIA series N3045TX3",
                }
            )
            added += 1
    rows.sort(key=lambda r: (int(r["year"]), int(r["month"])))
    with ERCOT_EP_PATH.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
    print(f"  ercot_electric_power_gas_price.csv: +{added} rows ({len(rows)} total)")
    return added


def extend_pjm_zonal(years: list[int], key: str) -> int:
    """Append missing per-zone annual basis rows for the requested years."""
    with PJM_ZONAL_PATH.open() as fh:
        reader = csv.DictReader(fh)
        header = list(reader.fieldnames or [])
        rows = [dict(r) for r in reader]
    have = {(r["zone"], int(r["year"])) for r in rows}
    hh = _henry_hub_monthly()
    states = sorted({st for st, _, _ in PJM_ZONE_STATE.values()})
    series = {st: _monthly_series(f"N3045{st}3", key) for st in states}
    added = 0
    for year in years:
        # Published window this year (for flagging withheld states): the modal
        # month coverage across the non-withheld states.
        coverage = {st: _annual_basis(series[st], hh, year)[1] for st in states}
        full_months = max((len(m) for m in coverage.values()), default=0)
        proxy_basis, proxy_months = _annual_basis(
            {
                k: sum(series[st].get(k, 0.0) for st in _APPALACHIAN_PROXY_STATES)
                / len(_APPALACHIAN_PROXY_STATES)
                for k in set.intersection(
                    *(set(series[st]) for st in _APPALACHIAN_PROXY_STATES)
                )
            },
            hh,
            year,
        )
        for zone, (st, hub, src) in PJM_ZONE_STATE.items():
            if (zone, year) in have:
                continue
            basis, months = _annual_basis(series[st], hh, year)
            if basis is None or len(months) < max(1, full_months // 2):
                # Mostly-withheld state (the committed WV-2025 precedent):
                # proxy to the OH+PA Appalachian delivered-to-EP mean.
                if proxy_basis is None:
                    print(f"  {zone} {year}: no data and no proxy; skipped")
                    continue
                n = len(months)
                basis = proxy_basis
                source = (
                    f"{st} {year} {12 - n}/12 months EIA-withheld; proxied to "
                    f"OH+PA Appalachian delivered-to-EP mean = {basis:.3f}"
                )
                months = proxy_months
            else:
                source = f"{src} (EIA N3045{st}3 delivered-to-electric-power)"
            if len(months) < 12:
                source += (
                    f"; PARTIAL YEAR: {_months_label(months)} {year} published "
                    f"months only (winter-weighted); re-extend when EIA "
                    f"publishes the rest"
                )
            rows.append(
                {
                    "zone": zone,
                    "year": year,
                    "basis_vs_hh_usd_mmbtu": round(basis, 3),
                    "hub": hub,
                    "source": source,
                }
            )
            added += 1
    rows.sort(key=lambda r: (list(PJM_ZONE_STATE).index(r["zone"]), int(r["year"])))
    with PJM_ZONAL_PATH.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
    print(f"  pjm_zonal_gas_hub.csv: +{added} rows ({len(rows)} total)")
    return added


def _month_list(months: list[int]) -> str:
    """Published-month label: a ``Jan-Apr`` span, or the explicit list if gappy."""
    if months == list(range(months[0], months[-1] + 1)):
        return _months_label(months)
    return " ".join(_MONTH_ABBR[m] for m in months)


def extend_miso_zonal(years: list[int], key: str | None) -> int:
    """Append missing per-zone annual basis rows to ``miso_zonal_gas_hub.csv``.

    Same formula and file shape as :func:`extend_pjm_zonal` — one annual row
    per model zone, ``mean over published months of (N3045<ST>3 / 1.036 −
    HenryHub_monthly)`` — over the MISO crosswalk in :data:`MISO_ZONE_STATE`.

    MISO takes NO cross-state proxy for a withheld year (PJM's Appalachian
    fallback has no MISO analogue in the committed file): a state-year with no
    published month is SKIPPED, not filled, so a year the source never
    published stays visibly absent instead of becoming a fabricated basis
    (rule 14). A partly-published year lands with its exact published months
    named in ``source``, and under half a year is additionally marked SPARSE.
    """
    with MISO_ZONAL_PATH.open() as fh:
        reader = csv.DictReader(fh)
        header = list(reader.fieldnames or [])
        rows = [dict(r) for r in reader]
    have = {(r["zone"], int(r["year"])) for r in rows}
    hh = _henry_hub_monthly()
    states = sorted({st for st, _, _ in MISO_ZONE_STATE.values()})
    series = {st: _monthly_series(f"N3045{st}3", key) for st in states}
    added = 0
    for year in years:
        for zone, (st, hub, src) in MISO_ZONE_STATE.items():
            if (zone, year) in have:
                continue
            basis, months = _annual_basis(series[st], hh, year)
            if basis is None:
                print(
                    f"  {zone} {year}: N3045{st}3 published no month "
                    "(EIA-withheld); skipped, no proxy"
                )
                continue
            source = (
                f"{src} delivered-to-electric-power (EIA N3045{st}3) minus "
                "Henry Hub monthly mean"
            )
            if len(months) < 12:
                source += (
                    f"; PARTIAL YEAR: {_month_list(months)} {year} published "
                    f"months only ({len(months)}/12, remainder EIA-withheld)"
                )
                if len(months) < 6:
                    source += "; SPARSE — treat as indicative, not an annual basis"
            rows.append(
                {
                    "zone": zone,
                    "year": year,
                    "basis_vs_hh_usd_mmbtu": round(basis, 3),
                    "hub": hub,
                    "source": source,
                }
            )
            added += 1
    rows.sort(key=lambda r: (list(MISO_ZONE_STATE).index(r["zone"]), int(r["year"])))
    with MISO_ZONAL_PATH.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
    print(f"  miso_zonal_gas_hub.csv: +{added} rows ({len(rows)} total)")
    return added


def validate(key: str | None, iso: str = "PJM") -> int:
    """Reproduce every committed zonal-hub basis of ``iso`` from the formula."""
    path, crosswalk = (
        (PJM_ZONAL_PATH, PJM_ZONE_STATE)
        if iso == "PJM"
        else (MISO_ZONAL_PATH, MISO_ZONE_STATE)
    )
    with path.open() as fh:
        rows = [dict(r) for r in csv.DictReader(fh)]
    hh = _henry_hub_monthly()
    states = sorted({st for st, _, _ in crosswalk.values()})
    series = {st: _monthly_series(f"N3045{st}3", key) for st in states}
    bad = 0
    for r in rows:
        if "proxied" in r["source"]:
            print(f"  {r['zone']} {r['year']}: proxied row, skipped")
            continue
        st = crosswalk[r["zone"]][0]
        basis, months = _annual_basis(series[st], hh, int(r["year"]))
        committed = float(r["basis_vs_hh_usd_mmbtu"])
        ok = basis is not None and abs(basis - committed) < 1e-3
        bad += 0 if ok else 1
        print(
            f"  {r['zone']} {r['year']}: committed {committed:+.3f} "
            f"recomputed {basis:+.3f} (n={len(months)}) {'OK' if ok else 'MISMATCH'}"
        )
    print("validate:", "all reproduced" if bad == 0 else f"{bad} MISMATCHES")
    return bad


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2022, 2026])
    ap.add_argument(
        "--validate",
        action="store_true",
        help="recompute every committed non-proxied zonal-hub row of the "
        "selected --iso from the formula and report mismatches; write nothing",
    )
    ap.add_argument(
        "--iso",
        nargs="+",
        default=["ERCOT", "PJM"],
        choices=["ERCOT", "PJM", "MISO"],
        help="which committed series to extend (ERCOT monthly EP price, PJM "
        "zonal hub, MISO zonal hub). --validate takes one of PJM/MISO",
    )
    args = ap.parse_args()
    # The v2 API needs a key; without one every series falls back to EIA's
    # key-free dnav monthly pages (_monthly_series_dnav), so an intake lane in
    # an environment with no credential still runs.
    key = _api_key(required=False)
    if not key:
        print("no EIA_API_KEY — using EIA's key-free dnav monthly pages")
    if args.validate:
        iso = "MISO" if args.iso == ["MISO"] else "PJM"
        sys.exit(1 if validate(key, iso) else 0)
    if "ERCOT" in args.iso:
        extend_ercot_ep(args.years, key)
    if "PJM" in args.iso:
        extend_pjm_zonal(args.years, key)
    if "MISO" in args.iso:
        extend_miso_zonal(args.years, key)
    print("done.")


if __name__ == "__main__":
    main()
