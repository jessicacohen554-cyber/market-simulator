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
import zipfile
from collections import defaultdict
from pathlib import Path

ZIP_PATH = Path("data/raw/NYISO/ATC_TTC.zip")
INTERFACE = "CENT EAST"
YEARS = (2023, 2024, 2025)
ROUND_TO = 25  # MW — postings are 5 MW granular; 25 MW avoids false precision.


def _round(x: float) -> int:
    return int(round(x / ROUND_TO) * ROUND_TO)


def collect() -> dict[tuple[int, int], list[float]]:
    """Return ``{(year, month): [TTC(DAM) MW, ...]}`` for the Central-East interface."""
    monthly: dict[tuple[int, int], list[float]] = defaultdict(list)
    with zipfile.ZipFile(ZIP_PATH) as outer:
        for member in outer.namelist():
            if not member.endswith(".zip"):
                continue
            year, month = int(member[:4]), int(member[4:6])
            if year not in YEARS:
                continue
            inner = zipfile.ZipFile(io.BytesIO(outer.read(member)))
            for day in inner.namelist():
                if not day.endswith(".csv"):
                    continue
                reader = csv.reader(
                    inner.read(day).decode("utf-8", "replace").splitlines()
                )
                next(reader, None)  # header
                for row in reader:
                    if row and row[0] == INTERFACE:
                        try:
                            monthly[(year, month)].append(float(row[2]))  # TTC (DAM)
                        except (ValueError, IndexError):
                            pass
    return monthly


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
