"""Derive NYISO Central-East monthly TTC from the NYISO ATC/TTC postings.

NYISO posts the day-ahead Total Transfer Capability (TTC) for every internal
interface hour by hour (MIS ``ATC_TTC`` files, mirrored here in
``data/raw/NYISO/ATC_TTC.zip`` — one nested monthly zip per month, each
holding daily CSVs). The ``CENT EAST`` interface is the west->east Central-East
limit the model represents as the ``Upstate_West -> Capital_Hudson`` link.

This script aggregates the posted ``TTC (DAM)`` column for ``CENT EAST`` to a
calendar-month mean (MW), rounded to the nearest 25 MW, and prints the
``NYISO_INTERFACE_TTC_BY_MONTH`` / ``NYISO_INTERFACE_TTC_BY_YEAR`` literals used
in :mod:`market_sim.config.constants`. Re-run it after refreshing the postings
to regenerate those tables.

    uv run python scripts/data/derive_nyiso_central_east_ttc.py
"""

from __future__ import annotations

import csv
import io
import statistics
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import NYISO_DIR  # noqa: E402

# Resolved through the registry (config/paths.py) — the old Path("data/raw/…")
# literal here was CWD-relative and only worked from the repo root.
ZIP_PATH = NYISO_DIR / "ATC_TTC.zip"
# Native MIS layout: one monthly zip per month, as fetched straight from the
# public posting. Preferred over ZIP_PATH because it is what a re-fetch
# produces; ZIP_PATH (an outer zip of those same monthly zips) still works.
MIS_DIR = NYISO_DIR / "atc-ttc"
MIS_URL = "http://mis.nyiso.com/public/csv/atc_ttc/{ym}01atc_ttc_csv.zip"
INTERFACE = "CENT EAST"
# 2018-2022 ADDED 2026-08-14 (nyiso-134). The tables previously stopped at 2023,
# and BOTH appliers in market_sim.pipeline.ttc silently return unchanged for a
# year with no entry, so an out-of-training solve fell back to the STATIC
# topology value — which carries the POST-upgrade limit. For 2022 that is
# 2850 MW flat against a measured annual mean of 1825 MW (+56 %), and in
# November 2022 against a measured 725 MW — 3.9x the real limit. Diagnosis:
# defect D-2 of ASSESSMENT-nyiso134-2022-readiness-2026-08-14.md; the appliers
# now fail loud instead of silently no-opping.
YEARS = (2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025)
ROUND_TO = 25  # MW — postings are 5 MW granular; 25 MW avoids false precision.


def _round(x: float) -> int:
    return int(round(x / ROUND_TO) * ROUND_TO)


def _scan_month(blob: bytes, year: int, month: int, out: dict) -> None:
    """Accumulate one monthly zip's Central-East ``TTC (DAM)`` values into ``out``.

    The column is located BY NAME rather than by position: the daily CSV header
    is ``Interface Name, Time Stamp, TTC (DAM), ATC (DAM), TTC (HAM) ...``, and
    a positional read silently grabs the wrong column if NYISO ever inserts one.

    Args:
        blob: Raw bytes of one monthly ``*atc_ttc_csv.zip``.
        year: Calendar year the zip covers.
        month: Calendar month the zip covers.
        out: ``{(year, month): [MW, ...]}`` accumulator, mutated in place.
    """
    with zipfile.ZipFile(io.BytesIO(blob)) as inner:
        for day in inner.namelist():
            if not day.endswith(".csv"):
                continue
            rows = csv.reader(inner.read(day).decode("utf-8", "replace").splitlines())
            header = next(rows, None)
            if not header:
                continue
            try:
                ttc_col = header.index("TTC (DAM)")
            except ValueError:
                continue
            for row in rows:
                if row and row[0].strip().upper() == INTERFACE:
                    try:
                        out[(year, month)].append(float(row[ttc_col]))
                    except (ValueError, IndexError):
                        pass


def collect() -> dict[tuple[int, int], list[float]]:
    """Return ``{(year, month): [TTC(DAM) MW, ...]}`` for the Central-East interface.

    Reads the native per-month MIS layout under :data:`MIS_DIR` when present,
    else the legacy outer :data:`ZIP_PATH`. Neither is committed (NYISO's
    redistribution terms are unverified — ``docs/data-licensing.md`` §7), so a
    fresh checkout re-fetches with the URL printed by :func:`_missing_input`.
    """
    monthly: dict[tuple[int, int], list[float]] = defaultdict(list)
    if MIS_DIR.is_dir():
        for path in sorted(MIS_DIR.glob("*atc_ttc_csv.zip")):
            year, month = int(path.name[:4]), int(path.name[4:6])
            if year in YEARS:
                _scan_month(path.read_bytes(), year, month, monthly)
    elif ZIP_PATH.exists():
        with zipfile.ZipFile(ZIP_PATH) as outer:
            for member in outer.namelist():
                if not member.endswith(".zip"):
                    continue
                year, month = int(member[:4]), int(member[4:6])
                if year in YEARS:
                    _scan_month(outer.read(member), year, month, monthly)
    else:
        _missing_input()
    missing = [(y, m) for y in YEARS for m in range(1, 13) if not monthly.get((y, m))]
    if missing:
        raise SystemExit(
            f"no Central-East TTC rows for {len(missing)} month(s): {missing[:6]}"
            f"{' ...' if len(missing) > 6 else ''} — re-fetch those months."
        )
    return monthly


def _missing_input() -> None:
    """Exit with the exact re-fetch command; the raw postings are not committed."""
    raise SystemExit(
        f"NYISO ATC/TTC postings not found ({MIS_DIR} or {ZIP_PATH}).\n"
        f"Re-fetch (one zip per month, ~200 KB each):\n"
        f"  mkdir -p {MIS_DIR}\n"
        f"  for y in {' '.join(str(y) for y in YEARS)}; do\n"
        f"    for m in 01 02 03 04 05 06 07 08 09 10 11 12; do\n"
        f"      curl -sS -o {MIS_DIR}/${{y}}${{m}}01atc_ttc_csv.zip \\\n"
        f"        {MIS_URL.format(ym='${y}${m}')}\n"
        f"    done\n"
        f"  done"
    )


def main() -> None:
    monthly = collect()
    by_month: dict[int, list[int]] = {}
    by_year: dict[int, int] = {}
    for year in YEARS:
        per_month = [_round(statistics.mean(monthly[(year, m)])) for m in range(1, 13)]
        by_month[year] = per_month
        all_vals = [v for m in range(1, 13) for v in monthly[(year, m)]]
        by_year[year] = _round(statistics.mean(all_vals))

    key = '("Upstate_West", "Capital_Hudson")'
    print("NYISO_INTERFACE_TTC_BY_MONTH = {")
    for year in YEARS:
        vals = ", ".join(f"{v}.0" for v in by_month[year])
        print(f"    {year}: {{{key}: [{vals}]}},")
    print("}")
    print()
    print("NYISO_INTERFACE_TTC_BY_YEAR = {")
    for year in YEARS:
        print(f"    {year}: {{{key}: {by_year[year]}.0}},")
    print("}")


if __name__ == "__main__":
    main()
