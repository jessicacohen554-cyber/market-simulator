"""
Fetch EIA Form 860 plant/generator data via EIA API v2 and save to
data/raw/eia-860/.

Usage:
    python scripts/data/fetch_eia860.py [--scope full|markets]

Scopes:
    full    Pull all U.S. generators (default)
    markets Pull only generators in ERCOT, PJM, CAISO, NEISO, NYISO, MISO

Outputs (CSV, one file per scope/BA):
    data/raw/eia-860/generators_us.csv          (full scope)
    data/raw/eia-860/generators_<BA>.csv        (markets scope, per BA)
    data/raw/eia-860/metadata.json              (column/facet reference)
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from market_sim.config.paths import EIA_860_DIR  # noqa: E402
from scripts.lib.env_keys import get_api_key  # noqa: E402

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL = "https://api.eia.gov/v2/electricity/operating-generator-capacity"
# Resolved but not required at import time; ``main`` raises if still missing so
# ``--help`` works without a key.
API_KEY = get_api_key("EIA_API_KEY", required=False) or ""

# Single W1 data root (paths.EIA_860_DIR = data/raw/eia-860); the pre-W1
# ``inputs/raw-data`` path was removed by the relocation.
OUTPUT_DIR = EIA_860_DIR
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PAGE_SIZE = 5000  # max rows per request

# Balancing authority codes for the seven major wholesale markets
MARKETS = {
    "ERCO": "ERCOT",
    "PJM": "PJM",
    "CISO": "CAISO",
    "ISNE": "NEISO",
    "NYIS": "NYISO",
    "MISO": "MISO",
}

# Data columns to request from the API
DATA_COLS = [
    "nameplate_capacity_mw",
    "net_summer_capacity_mw",
    "net_winter_capacity_mw",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get(params: dict, retries: int = 4) -> dict:
    params["api_key"] = API_KEY
    for attempt in range(retries):
        try:
            r = requests.get(f"{BASE_URL}/data/", params=params, timeout=60)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as exc:
            if attempt == retries - 1:
                raise
            wait = 2**attempt
            print(f"  Retry {attempt + 1}/{retries} after {wait}s: {exc}")
            time.sleep(wait)


def fetch_metadata() -> dict:
    r = requests.get(BASE_URL, params={"api_key": API_KEY}, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch_all(facet_filters: dict | None = None) -> list[dict]:
    """Page through the API and return all matching rows."""
    rows = []
    offset = 0
    total = None

    base_params = {
        "frequency": "annual",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": PAGE_SIZE,
    }
    for col in DATA_COLS:
        base_params["data[]"] = col  # last one wins in requests; use list form below

    # Build data[] as list
    data_list = DATA_COLS

    if facet_filters:
        for facet_key, values in facet_filters.items():
            if isinstance(values, list):
                for v in values:
                    base_params.setdefault(f"facets[{facet_key}][]", [])
                    if isinstance(base_params[f"facets[{facet_key}][]"], list):
                        base_params[f"facets[{facet_key}][]"].append(v)
                    else:
                        base_params[f"facets[{facet_key}][]"] = [
                            base_params[f"facets[{facet_key}][]"],
                            v,
                        ]
            else:
                base_params[f"facets[{facet_key}][]"] = values

    while total is None or offset < total:
        params = {**base_params, "offset": offset}
        # requests doesn't serialize list params correctly for EIA — build manually
        param_parts = []
        for k, v in params.items():
            if k == "data[]":
                continue
            if isinstance(v, list):
                for item in v:
                    param_parts.append((k, item))
            else:
                param_parts.append((k, v))
        for col in data_list:
            param_parts.append(("data[]", col))

        r = requests.get(
            f"{BASE_URL}/data/",
            params=param_parts,
            timeout=60,
        )
        r.raise_for_status()
        payload = r.json()

        response = payload.get("response", {})
        if total is None:
            total = response.get("total", 0)
            print(f"  Total rows: {total:,}")

        batch = response.get("data", [])
        rows.extend(batch)
        offset += len(batch)
        print(f"  Fetched {offset:,} / {total:,}")

        if not batch:
            break

    return rows


def rows_to_csv(rows: list[dict], path: Path) -> None:
    import csv

    if not rows:
        print(f"  No data — skipping {path.name}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(rows[0].keys())
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Saved {len(rows):,} rows → {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scope",
        choices=["full", "markets"],
        default="full",
        help="'full' = all U.S.; 'markets' = ERCOT/PJM/CAISO/NEISO/NYISO/MISO only",
    )
    args = parser.parse_args()

    if not API_KEY:
        raise SystemExit("EIA_API_KEY not found. Set the env var or add it to .env")

    # Save metadata for reference
    print("Fetching API metadata…")
    try:
        meta = fetch_metadata()
        meta_path = OUTPUT_DIR / "metadata.json"
        meta_path.write_text(json.dumps(meta, indent=2))
        print(f"  Metadata → {meta_path}")
    except Exception as exc:
        print(f"  Could not fetch metadata: {exc}")

    if args.scope == "full":
        print("\nFetching all U.S. generators…")
        rows = fetch_all()
        rows_to_csv(rows, OUTPUT_DIR / "generators_us.csv")

    elif args.scope == "markets":
        ba_codes = list(MARKETS.keys())
        print(f"\nFetching generators for: {', '.join(MARKETS.values())}…")
        rows = fetch_all(facet_filters={"balancing_authority_code": ba_codes})
        rows_to_csv(rows, OUTPUT_DIR / "generators_markets.csv")

        # Also write per-BA files for easy slicing
        ba_field = "balancingAuthorityCode"  # field name in response rows
        by_ba: dict[str, list] = {}
        for row in rows:
            code = row.get(ba_field) or row.get("balancing_authority_code", "UNKNOWN")
            by_ba.setdefault(code, []).append(row)

        for code, ba_rows in by_ba.items():
            name = MARKETS.get(code, code).lower()
            rows_to_csv(ba_rows, OUTPUT_DIR / f"generators_{name}.csv")

    print("\nDone.")


if __name__ == "__main__":
    main()
