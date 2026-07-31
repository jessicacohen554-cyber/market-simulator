"""NYISO 2018-2021 (+2026 where the source allows) holdout intake: measured-input
extensions. The 2018-2021 generalization of ``holdout_intake_nyiso_2022_inputs.py``.

Owner-authorized 2026-07-31 NYISO out-of-training DATA READINESS (rule 22
Option-2 channel-1 intake; session-logged verbatim in
``frontend/data/backcast/calibration-complete.json`` ``intake_log``). **No LP is
constructed, solved, or scored.** Closes the 2026-07-13 session's explicit
"not attempted this session (time-boxed, confirmed fetchable in a follow-up)"
carryover list.

Every step: (a) uses the SAME producer/derivation as the committed in-sample
rows, (b) merges ONLY out-of-training rows, and (c) asserts the committed
in-sample (2023-2025) rows byte-frozen before writing — a step that would touch
an in-sample byte aborts. Steps are idempotent.

Steps (subcommands, in this order)::

    transco-table --csv <scratch.csv>  # merge the 2018-2021 EIA spot-table daily
                                       # prints (fetch_transco_daily_spot.py
                                       # --start-year 2018 --end-year 2021 --out ...)
    monthly-hubs                       # 12 rows/yr of transco_z6_iroquois_monthly.csv
                                       # from the completed daily series + each
                                       # year's SOM annual Iroquois-Transco spread
    basis                              # re-base the NYISO 2018-2021 rows of
                                       # gas_basis_by_iso_month.csv off the old
                                       # citygate-proxy construction onto the
                                       # in-sample Iroquois-Z2-minus-HH one
    downstate --csv <scratch.csv>      # merge 2018-2021 rows of
                                       # nyiso_downstate_ct_gas_basis_monthly.csv
    ldc-transport --csv <scratch.csv>  # merge the 96 2018-2021 rows of
                                       # nyiso_downstate_ldc_transport_monthly.csv
    weather                            # merge the on-disk <year>h1/h2 (and 2026)
                                       # zone-temp split files into the consolidated CSV
    downstate-tmax --csv <scratch.csv> # merge 2018-2021 + 2026 NYC-metro TMAX

Between ``transco-table`` and ``monthly-hubs``, run the narrative harvest for
the winter spike prints the compact table misses (same producer as the
committed years)::

    python scripts/data/fetch_nyiso_gas_narrative.py --start-year 2018 --end-year 2021

SOM anchors: ``data/raw/gas-prices/nyiso_som_hub_fuel_annual.csv`` already
carries the NYISO State-of-the-Market Figure A-6 annual per-hub prices for
2018-2021 (transcribed by the 2026-07-13 session), so each year's
Iroquois-minus-Transco spread — the same construction the committed 2022-2025
monthly rows document in their ``source`` column — is read straight from it.
No new transcription is introduced here.

Usage::

    python scripts/archive/holdout_intake_nyiso_2018_2021_inputs.py <step> [args]
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))
sys.path.insert(0, str(REPO / "src"))

GAS_DIR = REPO / "data" / "raw" / "gas-prices"
TRANSCO_DAILY = GAS_DIR / "transco_z6_ny_daily.csv"
MONTHLY_HUBS = GAS_DIR / "transco_z6_iroquois_monthly.csv"
DOWNSTATE = GAS_DIR / "nyiso_downstate_ct_gas_basis_monthly.csv"
LDC_TRANSPORT = GAS_DIR / "nyiso_downstate_ldc_transport_monthly.csv"
SOM_ANNUAL = GAS_DIR / "nyiso_som_hub_fuel_annual.csv"
HH_MONTHLY = GAS_DIR / "henry_hub_monthly.csv"
BASIS = REPO / "data" / "raw" / "gas_basis_by_iso_month.csv"
WEATHER_DIR = REPO / "data" / "raw" / "nyiso-weather"
ZONE_TEMP = WEATHER_DIR / "nyiso_zone_temp_daily.csv"
DOWNSTATE_TMAX = WEATHER_DIR / "nyiso_downstate_tmax_daily.csv"

YEARS = (2018, 2019, 2020, 2021)
# Years whose zone-temp / TMAX raws also exist on disk beyond the gas window.
WEATHER_YEARS = (2018, 2019, 2020, 2021, 2026)
IN_SAMPLE = ("2023", "2024", "2025")


def _lines(path: Path) -> list[str]:
    return path.read_text().splitlines()


def _in_sample_lines(lines: list[str], match) -> list[str]:
    """Subset of ``lines`` whose row is in-sample per ``match(line)``."""
    return [ln for ln in lines if match(ln)]


def _write_guarded(path: Path, new_lines: list[str], match) -> None:
    """Write ``new_lines``, asserting the in-sample subset is byte-frozen."""
    before = _in_sample_lines(_lines(path), match)
    after = _in_sample_lines(new_lines, match)
    if before != after:
        sys.exit(f"{path}: in-sample rows would change — refusing to write")
    path.write_text("\n".join(new_lines) + "\n")
    print(f"wrote {path} ({len(new_lines) - 1} data rows)")


def _is_in_sample_date(line: str) -> bool:
    return line[:4] in IN_SAMPLE


def _som(year: int, hub: str) -> float:
    """SOM Figure A-6 annual price for ``hub`` in ``year`` from the committed CSV."""
    with SOM_ANNUAL.open() as fh:
        for r in csv.DictReader(fh):
            if int(r["year"]) == year and r["hub"] == hub:
                return float(r["price_usd_per_mmbtu"])
    sys.exit(f"{SOM_ANNUAL}: no {year} row for {hub}")


def step_transco_table(scratch: Path) -> None:
    """Merge the 2018-2021 spot-table daily prints into the committed daily CSV."""
    lines = _lines(TRANSCO_DAILY)
    header, rows = lines[0], lines[1:]
    want = tuple(str(y) for y in YEARS)
    add = [ln for ln in _lines(scratch)[1:] if ln[:4] in want]
    if not add:
        sys.exit(f"{scratch}: no {YEARS} rows")
    have = {ln.split(",")[0] for ln in rows}
    new = [ln for ln in add if ln.split(",")[0] not in have]
    merged = sorted(rows + new, key=lambda ln: ln.split(",")[0])
    _write_guarded(TRANSCO_DAILY, [header] + merged, _is_in_sample_date)
    by_year: dict[str, int] = {}
    for ln in new:
        by_year[ln[:4]] = by_year.get(ln[:4], 0) + 1
    print(f"  +{len(new)} table prints: {dict(sorted(by_year.items()))}")


def step_monthly_hubs() -> None:
    """Create the 2018-2021 monthly hub rows (daily means + SOM annual spread)."""
    lines = _lines(MONTHLY_HUBS)
    header, rows = lines[0], lines[1:]
    by_month: dict[str, list[float]] = {}
    for ln in _lines(TRANSCO_DAILY)[1:]:
        parts = ln.split(",")
        if int(parts[0][:4]) in YEARS:
            by_month.setdefault(parts[0][:7], []).append(float(parts[1]))
    new_rows: list[str] = []
    for year in YEARS:
        if any(ln.startswith(f"{year}-") for ln in rows):
            print(f"{MONTHLY_HUBS}: {year} rows already present — skipped")
            continue
        missing = [m for m in range(1, 13) if f"{year}-{m:02d}" not in by_month]
        if missing:
            sys.exit(
                f"{year} daily series missing months {missing} — run the "
                f"table/narrative fetches first"
            )
        spread = round(_som(year, "IROQUOIS_Z2") - _som(year, "TRANSCO_Z6_NY"), 4)
        src = (
            "EIA Natural Gas Weekly Update spot, 'New York' = Transco Zone 6 NY "
            "(NGI Daily GPI), monthly mean of daily quotes; Iroquois Z2 = Transco "
            "monthly shape + NYISO SOM annual Iroquois-Transco spread"
        )
        for m in range(1, 13):
            ym = f"{year}-{m:02d}"
            tz = round(sum(by_month[ym]) / len(by_month[ym]), 4)
            new_rows.append(f'{ym},{tz},{round(tz + spread, 4)},"{src}"')
        print(
            f"  {year}: SOM Iroquois-Transco spread {spread} $/MMBtu; prints/month "
            f"{ {m[-2:]: len(v) for m, v in sorted(by_month.items()) if m[:4] == str(year)} }"
        )
    if not new_rows:
        return
    merged = sorted(rows + new_rows, key=lambda ln: ln.split(",")[0])
    _write_guarded(MONTHLY_HUBS, [header] + merged, _is_in_sample_date)


def step_basis() -> None:
    """Re-base the NYISO 2018-2021 basis rows onto the in-sample construction.

    The pre-existing NYISO 2018-2021 rows carry the generic EIA-citygate-proxy
    construction (``N3050NY3 - HH``); the in-sample (2023-2025) NYISO rows are
    ``Iroquois Z2 (Transco spot + SOM spread) - HH``. With the monthly hub rows
    in place, the out-of-training rows are re-based onto the SAME construction
    (hub + source labels updated to match) — an equivalency fix on
    out-of-training rows only; every other row byte-frozen. Same step the 2022
    lander applied, one year at a time.
    """
    iq: dict[str, float] = {}
    for ln in _lines(MONTHLY_HUBS)[1:]:
        p = ln.split(",")
        if int(p[0][:4]) in YEARS:
            iq[p[0]] = float(p[2])
    if len(iq) != 12 * len(YEARS):
        sys.exit(f"run monthly-hubs first (have {len(iq)} monthly hub rows)")
    hh: dict[tuple[int, int], float] = {}
    with HH_MONTHLY.open() as fh:
        for r in csv.DictReader(fh):
            if int(r["year"]) in YEARS:
                hh[(int(r["year"]), int(r["month"]))] = float(r["price_usd_mmbtu"])
    lines = _lines(BASIS)
    header, rows = lines[0], lines[1:]
    targets = tuple(f"NYISO,{y}," for y in YEARS)

    def is_frozen(ln: str) -> bool:
        return not ln.startswith(targets)

    hub_label = "Transco Z6 NY / Iroquois Z2 (EIA NG Weekly spot)"
    src = (
        "EIA NG Weekly spot Transco Z6 NY + NYISO SOM Iroquois-Transco "
        "spread; basis = Iroquois Z2 - Henry Hub (RNGWHHDm)"
    )
    out, n = [], 0
    for ln in rows:
        if ln.startswith(targets):
            _, y_s, m_s = ln.split(",")[:3]
            y, m = int(y_s), int(m_s)
            b = round(iq[f"{y}-{m:02d}"] - hh[(y, m)], 4)
            out.append(f'NYISO,{y},{m},{hub_label},{b},"{src}"')
            n += 1
        else:
            out.append(ln)
    if n != 12 * len(YEARS):
        sys.exit(f"expected {12 * len(YEARS)} NYISO basis rows to re-base, found {n}")
    _write_guarded(BASIS, [header] + out, is_frozen)
    print(f"  re-based {n} NYISO {YEARS} rows onto the in-sample construction")


def step_downstate(scratch: Path) -> None:
    """Merge the 2018-2021 downstate citygate-premium rows (same fetch producer)."""
    lines = _lines(DOWNSTATE)
    header, rows = lines[0], lines[1:]
    want = tuple(f"{y}," for y in YEARS)
    add = [ln for ln in _lines(scratch)[1:] if ln.startswith(want)]
    if len(add) != 12 * len(YEARS):
        sys.exit(f"{scratch}: expected {12 * len(YEARS)} rows, got {len(add)}")
    if any(ln.startswith(want) for ln in rows):
        print(f"{DOWNSTATE}: rows already present — nothing to do")
        return
    merged = sorted(
        rows + add, key=lambda ln: (int(ln.split(",")[0]), int(ln.split(",")[1]))
    )

    def is_frozen(ln: str) -> bool:
        return ln.split(",")[0] in IN_SAMPLE

    _write_guarded(DOWNSTATE, [header] + merged, is_frozen)


def step_ldc_transport(scratch: Path) -> None:
    """Merge the 2018-2021 LDC non-firm transport rows (same statnfdr producer)."""
    lines = _lines(LDC_TRANSPORT)
    header, rows = lines[0], lines[1:]
    want = tuple(f",{y}," for y in YEARS)
    if any(ln.count(",") and any(w in ln for w in want) for ln in rows):
        print(f"{LDC_TRANSPORT}: rows already present — nothing to do")
        return
    add = [ln for ln in _lines(scratch)[1:] if any(w in ln for w in want)]
    expect = 24 * len(YEARS)
    if len(add) != expect:
        sys.exit(
            f"{scratch}: expected {expect} rows (2 LDCs x 12 x years), got {len(add)}"
        )
    # Committed layout is LDC-major, years ascending within an LDC.
    merged = sorted(
        rows + add,
        key=lambda ln: (ln.split(",")[0], int(ln.split(",")[2]), int(ln.split(",")[3])),
    )

    def is_frozen(ln: str) -> bool:
        return not any(w in ln for w in want)

    _write_guarded(LDC_TRANSPORT, [header] + merged, is_frozen)


def step_weather() -> None:
    """Merge the on-disk split zone-temp files into the consolidated CSV."""
    lines = _lines(ZONE_TEMP)
    header, rows = lines[0], lines[1:]
    add: list[str] = []
    for year in WEATHER_YEARS:
        if any(ln.startswith(f"{year}-") for ln in rows):
            print(f"{ZONE_TEMP}: {year} rows already present — skipped")
            continue
        # 2018-2022 land as h1/h2 halves; 2026 as a single partial-year file.
        splits = [
            WEATHER_DIR / f"nyiso_zone_temp_daily_{year}{h}.csv" for h in ("h1", "h2")
        ]
        if not all(p.exists() for p in splits):
            single = WEATHER_DIR / f"nyiso_zone_temp_daily_{year}.csv"
            if not single.exists():
                print(f"  {year}: no split file on disk — skipped")
                continue
            splits = [single]
        got = 0
        for split in splits:
            s_lines = _lines(split)
            if s_lines[0] != header:
                sys.exit(f"{split}: header differs from {ZONE_TEMP}")
            rows_y = [ln for ln in s_lines[1:] if ln.startswith(f"{year}-")]
            add += rows_y
            got += len(rows_y)
        print(f"  {year}: +{got} zone-day rows from {len(splits)} split file(s)")
    if not add:
        return
    # The committed file is ZONE-major (all of a zone's days, zones
    # alphabetical), so a plain date sort would reorder in-sample lines.
    # Insert each zone's new block ahead of its first existing row instead.
    by_zone: dict[str, list[str]] = {}
    for ln in add:
        by_zone.setdefault(ln.split(",")[1], []).append(ln)
    out: list[str] = []
    seen: set[str] = set()
    for ln in rows:
        zone = ln.split(",")[1]
        if zone not in seen:
            seen.add(zone)
            out += sorted(by_zone.pop(zone, []), key=lambda x: x.split(",")[0])
        out.append(ln)
    if by_zone:
        sys.exit(
            f"{ZONE_TEMP}: split-file zones absent from committed file: {sorted(by_zone)}"
        )
    _write_guarded(ZONE_TEMP, [header] + out, _is_in_sample_date)


def step_downstate_tmax(scratch: Path) -> None:
    """Merge the fetched 2018-2021 + 2026 NYC-metro TMAX rows."""
    lines = _lines(DOWNSTATE_TMAX)
    header, rows = lines[0], lines[1:]
    want = tuple(str(y) for y in WEATHER_YEARS)
    have = {ln.split(",")[0] for ln in rows}
    add = [
        ln
        for ln in _lines(scratch)[1:]
        if ln[:4] in want and ln.split(",")[0] not in have
    ]
    if not add:
        print(f"{DOWNSTATE_TMAX}: nothing new to merge")
        return
    merged = sorted(rows + add, key=lambda ln: ln.split(",")[0])
    _write_guarded(DOWNSTATE_TMAX, [header] + merged, _is_in_sample_date)
    by_year: dict[str, int] = {}
    for ln in add:
        by_year[ln[:4]] = by_year.get(ln[:4], 0) + 1
    print(f"  +{len(add)} TMAX days: {dict(sorted(by_year.items()))}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="step", required=True)
    for name in ("transco-table", "downstate", "ldc-transport", "downstate-tmax"):
        p = sub.add_parser(name)
        p.add_argument("--csv", type=Path, required=True)
    sub.add_parser("monthly-hubs")
    sub.add_parser("basis")
    sub.add_parser("weather")
    args = ap.parse_args()

    if args.step == "transco-table":
        step_transco_table(args.csv)
    elif args.step == "monthly-hubs":
        step_monthly_hubs()
    elif args.step == "basis":
        step_basis()
    elif args.step == "downstate":
        step_downstate(args.csv)
    elif args.step == "ldc-transport":
        step_ldc_transport(args.csv)
    elif args.step == "weather":
        step_weather()
    elif args.step == "downstate-tmax":
        step_downstate_tmax(args.csv)


if __name__ == "__main__":
    main()
