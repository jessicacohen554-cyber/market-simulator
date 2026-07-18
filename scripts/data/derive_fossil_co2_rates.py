"""Derive the fleet-wide fossil CO2 emission-rate artifact (kg CO2 / net MWh).

Assembles one per-MWh CO2 rate for every fossil plant from eGRID (the fleet-wide
base, the only source spanning the small non-CEMS units) overridden by the
CAMPD-measured pooled intensities where they exist. The result is the input to
the calibration page's emissions metric: a class's generation (MWh) times its
net-generation-weighted intensity gives metric tonnes of CO2, model vs actual.

Writes ``data/raw/_processed-legacy/fossil_co2_rates.{parquet,csv}`` (one row per
plant-year), the fast-path artifact :func:`market_sim.data.egrid.fossil_co2_rate_map`
reads in preference to parsing the 21 MB eGRID workbook at render time.

Usage:
    python scripts/data/derive_fossil_co2_rates.py --years 2023 2024
    python scripts/data/derive_fossil_co2_rates.py --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.data import egrid  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("derive_fossil_co2_rates")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2023, 2024],
        help="Calendar years to assemble (default: 2023 2024).",
    )
    args = parser.parse_args()

    rates = egrid.build_fossil_co2_rates(args.years)
    if rates.empty:
        logger.error("no fossil CO2 rates assembled for years %s", args.years)
        return

    out_pq = egrid.FOSSIL_CO2_RATES_PATH
    out_csv = out_pq.with_suffix(".csv")
    out_pq.parent.mkdir(parents=True, exist_ok=True)
    rates.to_parquet(out_pq, index=False)
    rates.to_csv(out_csv, index=False)
    logger.info("wrote %s and %s", out_pq, out_csv)

    for year, g in rates.groupby("year"):
        n_campd = int((g["source"] == "campd").sum())
        n_egrid = int((g["source"] == "egrid").sum())
        logger.info(
            "%d: %d fossil plants (%d CAMPD-measured, %d eGRID); "
            "CO2 rate mean=%.1f median=%.1f kg/MWh-net",
            year,
            len(g),
            n_campd,
            n_egrid,
            g["co2_kg_per_mwh_net"].mean(),
            g["co2_kg_per_mwh_net"].median(),
        )


if __name__ == "__main__":
    main()
