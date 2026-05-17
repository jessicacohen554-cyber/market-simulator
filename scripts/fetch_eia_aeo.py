"""Fetch Henry Hub natural gas price trajectories from EIA AEO API.

This script requires network access to api.eia.gov and a free EIA API key.
It is NOT run during model builds — only when updating gas price
trajectories for a new AEO release.

Usage:
    EIA_API_KEY=your_key python scripts/fetch_eia_aeo.py [--aeo-year 2025]

Output: prints Python dict literals ready to paste into constants.py
(see HENRY_HUB_TRAJECTORIES).

EIA API v2 documentation: https://www.eia.gov/opendata/documentation.php
AEO data route: https://api.eia.gov/v2/aeo/
Register for free API key: https://www.eia.gov/opendata/register.php
"""

import os
import sys
import json
from urllib.request import urlopen
from urllib.error import HTTPError


def fetch_aeo_gas_prices(api_key: str, aeo_year: int = 2025) -> dict:
    """Fetch Henry Hub spot price projections from EIA AEO API v2.

    Queries the AEO route for natural gas prices across Reference,
    High Oil and Gas Supply, and Low Oil and Gas Supply cases.

    Returns dict mapping case_name -> {year: price_real_dollars}.
    """
    base_url = "https://api.eia.gov/v2/aeo"

    # First, discover available data structure.
    meta_url = f"{base_url}/{aeo_year}/?api_key={api_key}"
    print(f"Fetching AEO metadata: {meta_url}")
    try:
        with urlopen(meta_url) as resp:
            meta = json.loads(resp.read())
            routes = meta.get("response", {}).get("routes", [])
            print(f"Available routes: {[r['id'] for r in routes]}")
    except HTTPError as e:
        print(f"Error fetching metadata: {e}")
        print("Trying alternative route structure...")

    # AEO natural gas prices are typically under:
    # /aeo/{year}/data/?facets[seriesId][]=prng_nom_hhub
    # Case IDs vary by AEO year. Common ones:
    #   ref2025 = Reference case
    #   highogs = High Oil and Gas Supply
    #   lowogs  = Low Oil and Gas Supply
    #
    # The exact facet values depend on the AEO release. Query the facets
    # endpoint first to discover available cases and series.
    facets_url = (
        f"{base_url}/{aeo_year}/data/?api_key={api_key}"
        "&frequency=annual&length=5000"
    )
    print(f"\nFetching data: {facets_url}")

    try:
        with urlopen(facets_url) as resp:
            data = json.loads(resp.read())
    except HTTPError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Filter for Henry Hub series.
    records = data.get("response", {}).get("data", [])
    print(f"Total records returned: {len(records)}")

    # Print a sample to help identify the right series.
    if records:
        print(f"\nSample record keys: {list(records[0].keys())}")
        print(f"Sample record: {json.dumps(records[0], indent=2)}")

    # Filter and organize by case.
    hh_data: dict = {}
    for r in records:
        series_id = r.get("seriesId", "")
        if "hhub" in series_id.lower() or "henry" in str(r).lower():
            case = r.get("caseId", r.get("scenarioId", "unknown"))
            year = int(r.get("period", 0))
            value = float(r.get("value", 0))
            hh_data.setdefault(case, {})[year] = value

    return hh_data


def print_constants(data: dict, aeo_year: int) -> None:
    """Print data as Python dict literals for constants.py."""
    # Map AEO case names to our model path names.
    case_mapping = {
        "ref": "mid",
        "reference": "mid",
        "highogs": "low",   # High supply = low price
        "lowogs": "high",   # Low supply = high price
    }

    print("\n\n# === PASTE INTO constants.py ===")
    print(f"# Source: EIA Annual Energy Outlook {aeo_year}")
    print("# Fetched via scripts/fetch_eia_aeo.py")
    print("HENRY_HUB_TRAJECTORIES: dict[str, dict[int, float]] = {")

    for case_id, years in sorted(data.items()):
        model_path = None
        for prefix, path in case_mapping.items():
            if prefix in case_id.lower():
                model_path = path
                break
        if model_path is None:
            model_path = case_id

        print(f'    "{model_path}": {{')
        for year in sorted(years):
            if 2025 <= year <= 2050:
                print(f"        {year}: {years[year]:.2f},")
        print("    },")

    print("}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch EIA AEO gas price trajectories"
    )
    parser.add_argument(
        "--aeo-year", type=int, default=2025, help="AEO release year"
    )
    args = parser.parse_args()

    api_key = os.environ.get("EIA_API_KEY")
    if not api_key:
        print("ERROR: Set EIA_API_KEY environment variable.")
        print("Register for free at: https://www.eia.gov/opendata/register.php")
        sys.exit(1)

    fetched = fetch_aeo_gas_prices(api_key, args.aeo_year)
    if fetched:
        print_constants(fetched, args.aeo_year)
    else:
        print("No Henry Hub data found. Check the API route structure")
        print("and facet IDs, which may change between AEO releases.")
        print("\nManual fallback: download the AEO tables Excel file from")
        print("https://www.eia.gov/outlooks/aeo/tables_ref.php")
        print("and look at Table 13 (Natural Gas Supply, Disposition, and Prices).")
