"""Generate a synthetic plant-level generator fleet for all seven ISOs.

This is the Approach 5 fallback used when no real EIA-860 / eGRID data can
be fetched (the build environment cannot reach api.eia.gov or epa.gov). It
writes one CSV per ISO with an approximate real-world fleet composition.

Usage:
    python scripts/generate_synthetic_fleet.py

Outputs (CSV, one file per ISO):
    inputs/raw-data/eia-860/generators_{iso}.csv
"""

import csv
import logging

from market_sim.data.fleet import (
    BA_CODE_TO_ISO,
    EIA_860_DIR,
    SYNTHETIC_CSV_COLUMNS,
    build_synthetic_fleet_rows,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("generate_synthetic_fleet")


def main() -> None:
    """Write a synthetic fleet CSV for each of the seven ISOs."""
    EIA_860_DIR.mkdir(parents=True, exist_ok=True)

    for iso in BA_CODE_TO_ISO.values():
        rows = build_synthetic_fleet_rows(iso)
        path = EIA_860_DIR / f"generators_{iso.lower()}.csv"
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=SYNTHETIC_CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)

        total_gw = sum(r["net_summer_capacity_mw"] for r in rows) / 1000.0
        logger.warning(
            "Approach 5 (SYNTHETIC) used for %s — wrote %d generators "
            "(%.1f GW net summer) to %s",
            iso,
            len(rows),
            total_gw,
            path.name,
        )

    logger.warning(
        "Data provenance: SYNTHETIC. Approaches 1-4 (EIA API, PUDL, eGRID, "
        "other GitHub repos) did not yield real plant-level data."
    )


if __name__ == "__main__":
    main()
