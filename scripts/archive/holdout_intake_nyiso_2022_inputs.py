"""NYISO 2022 holdout intake: measured-input 2022 extensions (rule 22).

Owner-authorized 2026-07-12 NYISO 2022 validation-holdout DATA intake
(session-logged in ``frontend/data/backcast/calibration-complete.json``
``intake_log``). Extends the NYISO keeper-recipe measured-input series with
2022 rows so the (future, separately-authorized) one-shot validation has an
input set EQUIVALENT to 2023-2025. Companion of
``holdout_intake_nyiso_2022_lmp.py`` (the bench side).

Every step: (a) uses the SAME producer/derivation as the committed in-sample
rows, (b) merges ONLY out-of-training rows, and (c) asserts the committed
in-sample (2023-2025) rows byte-frozen before writing — a step that would
touch an in-sample byte aborts. Steps are idempotent.

Steps (run in this order; each is a subcommand)::

    transco-table --csv <scratch.csv>   # merge 2022 EIA spot-table daily prints
                                        # (fetch_transco_daily_spot.py --start-year
                                        # 2022 --end-year 2022 --out <scratch.csv>)
    monthly-hubs                        # create the 12 2022 rows of
                                        # transco_z6_iroquois_monthly.csv from the
                                        # completed 2022 daily series + the SOM-2022
                                        # annual Iroquois-Transco spread
    basis                               # recompute the 12 NYISO 2022 rows of
                                        # gas_basis_by_iso_month.csv onto the
                                        # in-sample construction (Iroquois Z2 - HH)
    downstate --csv <scratch.csv>       # merge 2022 rows of
                                        # nyiso_downstate_ct_gas_basis_monthly.csv
                                        # (fetch_nyiso_downstate_gas_basis.py
                                        # --start 2022-01 --end 2022-12 --out ...)
    ldc-transport --csv <scratch.csv>   # merge the 24 2022 rows of
                                        # nyiso_downstate_ldc_transport_monthly.csv
                                        # (fetch_nyiso_downstate_ldc_transport.py
                                        # 2022 statements)
    zonal-hub                           # append the 5 2022 rows of
                                        # nyiso_zonal_gas_hub.csv (SOM-2022 Fig A-6)
    weather                             # merge the 2022h1/h2 split zone-temp rows
                                        # into nyiso_zone_temp_daily.csv
    downstate-tmax                      # fetch + merge 2022 NYC-metro TMAX into
                                        # nyiso_downstate_tmax_daily.csv (same
                                        # fetch_nyc_tmax producer as committed rows)

Between ``transco-table`` and ``monthly-hubs``, run the narrative harvest for
the winter spike prints (same producer as the committed years)::

    python scripts/data/fetch_nyiso_gas_narrative.py --start-year 2022 --end-year 2022

(it merges narrative-only 2022 dates into the daily CSV — a table print wins
on a duplicate date — and its own monthly/basis recompute no-ops for 2022
until ``monthly-hubs`` has created the rows).

SOM-2022 anchors: the NYISO 2022 State of the Market report (Potomac
Economics, 2023-05-16) Figure A-6 annual per-hub fuel prices, already
transcribed in ``data/raw/gas-prices/nyiso_som_hub_fuel_annual.csv`` (2022
rows) — Transco Z6 NY $7.04, Iroquois Z2 $8.82, Tenn Z4 200L $5.75. The
Iroquois-Transco spread ($1.78) is the same SOM-annual-spread construction
the committed 2023-2025 monthly rows document in their ``source`` column.
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
SOM_ANNUAL = GAS_DIR / "nyiso_som_hub_fuel_annual.csv"
HH_MONTHLY = GAS_DIR / "henry_hub_monthly.csv"
BASIS = REPO / "data" / "raw" / "gas_basis_by_iso_month.csv"
ZONAL_HUB = REPO / "data" / "raw" / "nyiso_zonal_gas_hub.csv"
WEATHER_DIR = REPO / "data" / "raw" / "nyiso-weather"
ZONE_TEMP = WEATHER_DIR / "nyiso_zone_temp_daily.csv"
DOWNSTATE_TMAX = WEATHER_DIR / "nyiso_downstate_tmax_daily.csv"

YEAR = 2022
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


def _som_2022(hub: str) -> float:
    """SOM-2022 Figure A-6 annual price for ``hub`` from the committed CSV."""
    with SOM_ANNUAL.open() as fh:
        for r in csv.DictReader(fh):
            if int(r["year"]) == YEAR and r["hub"] == hub:
                return float(r["price_usd_per_mmbtu"])
    sys.exit(f"{SOM_ANNUAL}: no {YEAR} row for {hub}")


def step_transco_table(scratch: Path) -> None:
    """Merge the 2022 spot-table daily prints into the committed daily CSV."""
    lines = _lines(TRANSCO_DAILY)
    header, rows = lines[0], lines[1:]
    add = [ln for ln in _lines(scratch)[1:] if ln.startswith(str(YEAR))]
    if not add:
        sys.exit(f"{scratch}: no {YEAR} rows")
    have = {ln.split(",")[0] for ln in rows}
    new = [ln for ln in add if ln.split(",")[0] not in have]
    merged = sorted(rows + new, key=lambda ln: ln.split(",")[0])
    _write_guarded(TRANSCO_DAILY, [header] + merged, _is_in_sample_date)
    print(f"  +{len(new)} table prints for {YEAR}")


def step_monthly_hubs() -> None:
    """Create the 12 2022 monthly hub rows (daily means + SOM annual spread)."""
    lines = _lines(MONTHLY_HUBS)
    header, rows = lines[0], lines[1:]
    if any(ln.startswith(f"{YEAR}-") for ln in rows):
        print(f"{MONTHLY_HUBS}: {YEAR} rows already present — nothing to do")
        return
    by_month: dict[str, list[float]] = {}
    for ln in _lines(TRANSCO_DAILY)[1:]:
        parts = ln.split(",")
        if parts[0].startswith(str(YEAR)):
            by_month.setdefault(parts[0][:7], []).append(float(parts[1]))
    missing = [m for m in range(1, 13) if f"{YEAR}-{m:02d}" not in by_month]
    if missing:
        sys.exit(
            f"{YEAR} daily series missing months {missing} — run the "
            f"table/narrative fetches first"
        )
    spread = round(_som_2022("IROQUOIS_Z2") - _som_2022("TRANSCO_Z6_NY"), 4)
    src = (
        "EIA Natural Gas Weekly Update spot, 'New York' = Transco Zone 6 NY "
        "(NGI Daily GPI), monthly mean of daily quotes; Iroquois Z2 = Transco "
        "monthly shape + NYISO SOM annual Iroquois-Transco spread"
    )
    new_rows = []
    for m in range(1, 13):
        ym = f"{YEAR}-{m:02d}"
        tz = round(sum(by_month[ym]) / len(by_month[ym]), 4)
        iq = round(tz + spread, 4)
        new_rows.append(f'{ym},{tz},{iq},"{src}"')
    merged = sorted(rows + new_rows, key=lambda ln: ln.split(",")[0])
    _write_guarded(MONTHLY_HUBS, [header] + merged, _is_in_sample_date)
    print(
        f"  SOM-{YEAR} Iroquois-Transco spread: {spread} $/MMBtu; "
        f"prints/month: "
        f"{ {m: len(v) for m, v in sorted(by_month.items())} }"
    )


def step_basis() -> None:
    """Recompute the NYISO 2022 basis rows onto the in-sample construction.

    The pre-existing NYISO 2022 rows carry the generic EIA-citygate-proxy
    construction (``N3050NY3 - HH``); the in-sample (2023-2025) NYISO rows are
    ``Iroquois Z2 (Transco spot + SOM spread) - HH``. With the 2022 monthly
    hub rows in place, the 2022 rows are re-based onto the SAME construction
    (hub + source labels updated to match) — an equivalency fix on
    out-of-training rows only; every other row byte-frozen.
    """
    iq = {}
    for ln in _lines(MONTHLY_HUBS)[1:]:
        p = ln.split(",")
        if p[0].startswith(str(YEAR)):
            iq[p[0]] = float(p[2])
    if len(iq) != 12:
        sys.exit("run monthly-hubs first")
    hh = {}
    with HH_MONTHLY.open() as fh:
        for r in csv.DictReader(fh):
            if int(r["year"]) == YEAR:
                hh[int(r["month"])] = float(r["price_usd_mmbtu"])
    lines = _lines(BASIS)
    header, rows = lines[0], lines[1:]

    # In-sample guard: every row EXCEPT the NYISO 2022 rows must be byte-frozen.
    def is_frozen(ln: str) -> bool:
        return not ln.startswith(f"NYISO,{YEAR},")

    hub_label = "Transco Z6 NY / Iroquois Z2 (EIA NG Weekly spot)"
    src = (
        "EIA NG Weekly spot Transco Z6 NY + NYISO SOM Iroquois-Transco "
        "spread; basis = Iroquois Z2 - Henry Hub (RNGWHHDm)"
    )
    out, n = [], 0
    for ln in rows:
        if ln.startswith(f"NYISO,{YEAR},"):
            m = int(ln.split(",")[2])
            b = round(iq[f"{YEAR}-{m:02d}"] - hh[m], 4)
            out.append(f'NYISO,{YEAR},{m},{hub_label},{b},"{src}"')
            n += 1
        else:
            out.append(ln)
    if n != 12:
        sys.exit(f"expected 12 NYISO {YEAR} basis rows, found {n}")
    _write_guarded(BASIS, [header] + out, is_frozen)
    print(f"  re-based {n} NYISO {YEAR} rows onto the in-sample construction")


def step_downstate(scratch: Path) -> None:
    """Merge the 2022 downstate citygate-premium rows (same fetch producer)."""
    lines = _lines(DOWNSTATE)
    header, rows = lines[0], lines[1:]
    add = [ln for ln in _lines(scratch)[1:] if ln.startswith(f"{YEAR},")]
    if len(add) != 12:
        sys.exit(f"{scratch}: expected 12 {YEAR} rows, got {len(add)}")
    if any(ln.startswith(f"{YEAR},") for ln in rows):
        print(f"{DOWNSTATE}: {YEAR} rows already present — nothing to do")
        return
    merged = sorted(
        rows + add, key=lambda ln: (int(ln.split(",")[0]), int(ln.split(",")[1]))
    )

    def is_frozen(ln: str) -> bool:
        return ln.split(",")[0] in IN_SAMPLE

    _write_guarded(DOWNSTATE, [header] + merged, is_frozen)


def step_ldc_transport(scratch: Path) -> None:
    """Merge the 2022 LDC non-firm transport rows (same statnfdr producer)."""
    path = GAS_DIR / "nyiso_downstate_ldc_transport_monthly.csv"
    lines = _lines(path)
    header, rows = lines[0], lines[1:]
    if any(f",{YEAR}," in ln for ln in rows):
        print(f"{path}: {YEAR} rows already present — nothing to do")
        return
    add = [ln for ln in _lines(scratch)[1:] if f",{YEAR}," in ln]
    if len(add) != 24:
        sys.exit(f"{scratch}: expected 24 {YEAR} rows (2 LDCs x 12), got {len(add)}")
    # Committed layout is LDC-major, years ascending within an LDC.
    merged = sorted(
        rows + add,
        key=lambda ln: (
            ln.split(",")[0],
            int(ln.split(",")[2]),
            int(ln.split(",")[3]),
        ),
    )

    def is_frozen(ln: str) -> bool:
        return f",{YEAR}," not in ln

    _write_guarded(path, [header] + merged, is_frozen)


def step_zonal_hub() -> None:
    """Append the 5 2022 zone rows (SOM-2022 Figure A-6 annual averages)."""
    lines = _lines(ZONAL_HUB)
    header, rows = lines[0], lines[1:]
    if any(f",{YEAR}," in ln for ln in rows):
        print(f"{ZONAL_HUB}: {YEAR} rows already present — nothing to do")
        return
    src = "NYISO 2022 SOM (Potomac Economics) Figure A-6 annual avg"
    zone_hub = {
        "Upstate_West": ("Tenn Z4 200L", _som_2022("TENN_Z4_200L")),
        "Capital_Hudson": ("Iroquois Z2", _som_2022("IROQUOIS_Z2")),
        "Lower_Hudson": ("Iroquois Z2", _som_2022("IROQUOIS_Z2")),
        "NYC": ("Transco Z6 NY", _som_2022("TRANSCO_Z6_NY")),
        "Long_Island": ("Iroquois Z2", _som_2022("IROQUOIS_Z2")),
    }
    # Keep the committed layout: rows grouped by zone (file order), each
    # zone's years ascending — insert each 2022 row before the zone's 2023 row.
    out: list[str] = []
    for ln in rows:
        zone = ln.split(",")[0]
        if f",{YEAR + 1}," in ln and zone in zone_hub:
            hub, price = zone_hub[zone]
            out.append(f"{zone},{YEAR},{hub},{price:.2f},{src}")
        out.append(ln)

    def is_frozen(ln: str) -> bool:
        return f",{YEAR}," not in ln

    _write_guarded(ZONAL_HUB, [header] + out, is_frozen)


def step_weather() -> None:
    """Merge the split 2022h1/h2 zone-temp rows into the consolidated CSV."""
    lines = _lines(ZONE_TEMP)
    header, rows = lines[0], lines[1:]
    if any(ln.startswith(f"{YEAR}-") for ln in rows):
        print(f"{ZONE_TEMP}: {YEAR} rows already present — nothing to do")
        return
    add: list[str] = []
    for half in ("h1", "h2"):
        split = WEATHER_DIR / f"nyiso_zone_temp_daily_{YEAR}{half}.csv"
        s_lines = _lines(split)
        if s_lines[0] != header:
            sys.exit(f"{split}: header differs from {ZONE_TEMP}")
        add += [ln for ln in s_lines[1:] if ln.startswith(f"{YEAR}-")]
    # The committed file is ZONE-major (all of a zone's days 2023-2025, zones
    # alphabetical), so a plain date sort would reorder in-sample lines.
    # Insert each zone's 2022 block ahead of its first in-sample row instead.
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
            f"{ZONE_TEMP}: split-file zones absent from committed file: "
            f"{sorted(by_zone)}"
        )
    _write_guarded(ZONE_TEMP, [header] + out, _is_in_sample_date)
    print(f"  +{len(add)} zone-day rows from the {YEAR}h1/h2 split files")


def step_downstate_tmax() -> None:
    """Fetch + merge 2022 NYC-metro TMAX (same producer as committed rows)."""
    lines = _lines(DOWNSTATE_TMAX)
    header, rows = lines[0], lines[1:]
    if any(ln.startswith(f"{YEAR}-") for ln in rows):
        print(f"{DOWNSTATE_TMAX}: {YEAR} rows already present — nothing to do")
        return
    from derive_nyiso_ct_reliability_floor import fetch_nyc_tmax

    s = fetch_nyc_tmax(f"{YEAR}-01-01", f"{YEAR}-12-31")
    add = [f"{d},{v}" for d, v in s.items()]
    merged = sorted(rows + add, key=lambda ln: ln.split(",")[0])
    _write_guarded(DOWNSTATE_TMAX, [header] + merged, _is_in_sample_date)
    print(f"  +{len(add)} NYC-metro TMAX days (Central Park/LaGuardia/JFK mean)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="step", required=True)
    p = sub.add_parser("transco-table")
    p.add_argument("--csv", type=Path, required=True)
    sub.add_parser("monthly-hubs")
    sub.add_parser("basis")
    p = sub.add_parser("downstate")
    p.add_argument("--csv", type=Path, required=True)
    p = sub.add_parser("ldc-transport")
    p.add_argument("--csv", type=Path, required=True)
    sub.add_parser("zonal-hub")
    sub.add_parser("weather")
    sub.add_parser("downstate-tmax")
    args = ap.parse_args()
    {
        "transco-table": lambda: step_transco_table(args.csv),
        "monthly-hubs": step_monthly_hubs,
        "basis": step_basis,
        "downstate": lambda: step_downstate(args.csv),
        "ldc-transport": lambda: step_ldc_transport(args.csv),
        "zonal-hub": step_zonal_hub,
        "weather": step_weather,
        "downstate-tmax": step_downstate_tmax,
    }[args.step]()


if __name__ == "__main__":
    main()
