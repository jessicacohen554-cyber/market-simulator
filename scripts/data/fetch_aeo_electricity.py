#!/usr/bin/env python3
"""Fetch the AEO2025 electricity-corridor tables into immutable raw.

Companion to ``scripts/data/fetch_eia_aeo.py`` (which pulls the AEO *fuel-price*
trajectories): this pulls the AEO2025 regional **electricity** projections —
capacity mix, generation (energy) mix, and power-sector CO2 by Electricity
Market Module region — for the ``benchmark-corridor`` datatype's FC-5 external
corridor. It uses the same EIA Open Data API v2 ``aeo`` route; all the logic
lives in :mod:`scripts.lib.benchmark_corridor.aeo` (region crosswalk, series
map, unit assertions). Output:
``data/raw/benchmark-corridor/aeo2025/aeo2025_electricity_corridor.csv``.

Nothing in the model or ``config`` changes; re-deriving the clean datatype from
this raw is ``scripts/data/curate_benchmark_corridor.py`` (rule 23 — raw fetch and
curation are separate, cited steps).

Usage:
    EIA_API_KEY=your_key python scripts/data/fetch_aeo_electricity.py
    python scripts/data/fetch_aeo_electricity.py --years 2030 2035 2040
"""

from __future__ import annotations

import argparse
import sys

from scripts.lib.benchmark_corridor import aeo


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--aeo-year", type=int, default=2025, help="AEO release year")
    ap.add_argument(
        "--scenarios",
        nargs="+",
        default=["ref2025"],
        help="AEO scenario ids to pull (default: ref2025 = Reference case)",
    )
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=list(aeo.CORRIDOR_YEARS),
        help="corridor target years to keep (default: 2030 2035 2040)",
    )
    ap.add_argument(
        "--sleep", type=float, default=0.3, help="inter-request sleep seconds"
    )
    args = ap.parse_args(argv)

    key = aeo.load_api_key()
    if key == aeo._DEMO_KEY:
        print(
            "WARNING: no EIA_API_KEY found (env or .env) — using the public "
            "rate-limited DEMO_KEY. Register a free key at "
            "https://www.eia.gov/opendata/register.php for repeated use.",
            file=sys.stderr,
        )
    print(
        f"=== AEO{args.aeo_year} electricity corridor (capacity / generation / CO2 by EMM region) ==="
    )
    aeo.fetch_raw(
        aeo_year=args.aeo_year,
        scenarios=tuple(args.scenarios),
        years=tuple(args.years),
        sleep_s=args.sleep,
        key=key,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
