#!/usr/bin/env python3
"""Fetch EIA Annual Energy Outlook fuel-price trajectories (gas/coal/oil).

This is the machine-readable counterpart to the hand-typed
``HENRY_HUB_TRAJECTORIES`` table in ``config/constants.py`` (which carries a
standing ``TODO: verify against AEO Table 13`` at ``constants.py:914``) and to
the flat 1%/yr coal escalation and flat oil scalars used elsewhere. It pulls
the AEO's own Reference / High Oil and Gas Supply / Low Oil and Gas Supply
cases straight from the EIA Open Data API v2 ``aeo`` route (not a scrape of
the table-browser HTML), landing them as an immutable raw CSV. Nothing in
``config/constants.py`` is changed by this script -- see
``docs/handoffs/aeo-verification-<date>.md`` for the hardcoded-vs-fetched
diff; re-deriving the trajectories from this data is a separate, deliberate
step (CLAUDE.md rule 23: derive scripts cite the data change that triggered
them).

Series pulled (AEO2025; re-run with ``--aeo-year`` for a later edition once
released):

  * Table 13 (Natural Gas Supply, Disposition, and Prices):
    Henry Hub spot price, 2024 $/MMBtu.
  * Table 12 (Petroleum and Other Liquids Prices):
    WTI crude spot (2024 $/b); electric-power-sector delivered distillate
    and residual fuel oil (2024 $/gal) -- the two oil products this model's
    oil-fired fleet actually burns, not just the upstream crude marker.
  * Table 15 (Coal Supply, Disposition, and Prices):
    delivered-to-electric-power price (2024 $/MMBtu, national) and the
    average minemouth price (2024 $/MMBtu, national).
  * Table 65 (Coal Production and Minemouth Prices by Region):
    minemouth price by the five EIA coal supply regions (2024 $/short ton;
    the source table has no by-region $/MMBtu breakout, so this is the
    finest by-region granularity AEO publishes) -- "by supply region if
    easy, national if not" per the P-0C brief; both are landed.

Each series is pulled for all three AEO2025 scenario cases:
``ref2025`` (Reference -> the model's "mid" path), ``highogs`` (High Oil and
Gas Supply -> "low" price path, more supply), ``lowogs`` (Low Oil and Gas
Supply -> "high" price path, less supply) -- the same scenario/path mapping
already documented next to ``HENRY_HUB_TRAJECTORIES``.

Output (raw, immutable, never hand-edited):
  data/raw/eia-aeo/eia_aeo2025_fuel_prices.csv
    columns: fuel, metric, region, scenario, scenario_name, year, value,
             unit, series_id, table_id, table_name

EIA API v2 docs: https://www.eia.gov/opendata/documentation.php
Free key: https://www.eia.gov/opendata/register.php (falls back to the
public rate-limited ``DEMO_KEY`` if none is configured, matching NASA/other
federal open-data APIs -- verified working for this route, but a registered
personal key is recommended for repeated/heavy use).

Usage:
    EIA_API_KEY=your_key python scripts/fetch_eia_aeo.py
    python scripts/fetch_eia_aeo.py --aeo-year 2025 --start-year 2024
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "data" / "raw" / "eia-aeo"
OUT_CSV = OUT_DIR / "eia_aeo2025_fuel_prices.csv"

BASE = "https://api.eia.gov/v2"

# scenario id -> (scenario description, model gas_price_path-style label).
# Mapping matches the comment block above HENRY_HUB_TRAJECTORIES in
# constants.py ("low" = more supply = lower price, etc.) -- reproduced here,
# not redefined, so a re-derivation session has one source of truth to check.
SCENARIOS: dict[str, tuple[str, str]] = {
    "ref2025": ("Reference case", "mid"),
    "highogs": ("High Oil and Gas Supply", "low"),
    "lowogs": ("Low Oil and Gas Supply", "high"),
}

# (table_id, series_id, fuel, metric, region, unit) -- unit is the AEO API's
# own `unit` field, recorded here only for the human-readable docstring/log;
# the fetched value always carries the API's own unit string in the output.
SERIES: list[tuple[str, str, str, str, str]] = [
    ("13", "prce_hhp_NA_NA_ng_NA_usa_y13dlrpmmbtu", "gas", "henry_hub_spot", "usa"),
    ("12", "prce_NA_NA_NA_cr_wti_usa_y13dlrpbbl", "oil", "wti_spot_crude", "usa"),
    (
        "12",
        "prce_NA_elep_NA_dfo_NA_usa_y13dlrpgln",
        "oil",
        "electric_power_distillate",
        "usa",
    ),
    (
        "12",
        "prce_NA_elep_NA_rfo_NA_usa_y13dlrpgln",
        "oil",
        "electric_power_residual",
        "usa",
    ),
    (
        "15",
        "prce_NA_elep_NA_cl_NA_NA_y13dlrpmmbtu",
        "coal",
        "delivered_electric_power",
        "usa",
    ),
    (
        "15",
        "prce_NA_NA_NA_cl_mnmth_NA_y13dlrpmmbtu",
        "coal",
        "minemouth_average",
        "usa",
    ),
    (
        "94",
        "prce_NA_NA_NA_cl_mnmth_aplch_y13dlrptn",
        "coal",
        "minemouth_by_region",
        "appalachia",
    ),
    (
        "94",
        "prce_NA_NA_NA_cl_mnmth_eom_y13dlrptn",
        "coal",
        "minemouth_by_region",
        "east_of_mississippi",
    ),
    (
        "94",
        "prce_NA_NA_NA_cl_mnmth_intr_y13dlrptn",
        "coal",
        "minemouth_by_region",
        "interior",
    ),
    (
        "94",
        "prce_NA_NA_NA_cl_mnmth_west_y13dlrptn",
        "coal",
        "minemouth_by_region",
        "west",
    ),
    (
        "94",
        "prce_NA_NA_NA_cl_mnmth_wom_y13dlrptn",
        "coal",
        "minemouth_by_region",
        "west_of_mississippi",
    ),
]

_DEMO_KEY = "DEMO_KEY"


def _load_key() -> str:
    """Resolve the EIA API key: ``EIA_API_KEY`` env var, then repo ``.env``,
    then the public ``DEMO_KEY`` fallback (rate-limited but functional for
    this route -- verified during this intake)."""
    key = os.environ.get("EIA_API_KEY")
    if not key and (REPO / ".env").exists():
        for line in (REPO / ".env").read_text().splitlines():
            if line.startswith("EIA_API_KEY="):
                candidate = line.split("=", 1)[1].strip()
                if candidate:
                    key = candidate
                break
    return key or _DEMO_KEY


def _fetch_series(
    aeo_year: int,
    table_id: str,
    series_id: str,
    scenario: str,
    key: str,
    start_year: int,
    sleep_s: float,
) -> list[dict]:
    """Return every ``{period, value, unit}`` row for one series/scenario."""
    q = {
        "api_key": key,
        "frequency": "annual",
        "facets[tableId][]": table_id,
        "facets[seriesId][]": series_id,
        "facets[scenario][]": scenario,
        "data[0]": "value",
        "start": str(start_year),
        "length": 5000,
    }
    url = f"{BASE}/aeo/{aeo_year}/data/?{urlencode(q, doseq=True)}"
    backoffs = (5, 10, 20, 40, 60)
    payload = None
    for attempt, wait in enumerate((0, *backoffs)):
        if wait:
            print(
                f"    retrying after transient error -- backing off {wait}s "
                f"(attempt {attempt + 1})"
            )
            time.sleep(wait)
        try:
            with urlopen(url, timeout=60) as fh:
                payload = json.loads(fh.read().decode())
            break
        except HTTPError as exc:
            if exc.code == 429 and attempt < len(backoffs):
                continue
            raise RuntimeError(
                f"EIA AEO request failed ({series_id}/{scenario}): {exc}"
            ) from exc
        except URLError as exc:
            # Transient proxy/connection resets (e.g. ConnectionResetError)
            # surface as URLError -- retry them same as a 429 up to the cap.
            if attempt < len(backoffs):
                continue
            raise RuntimeError(
                f"EIA AEO request failed ({series_id}/{scenario}): {exc}"
            ) from exc
    time.sleep(sleep_s)
    rows = payload.get("response", {}).get("data", [])
    out = []
    for r in rows:
        if r.get("value") in (None, "", "NA"):
            continue
        out.append(
            {
                "period": int(r["period"]),
                "value": round(float(r["value"]), 6),
                "unit": r.get("unit", ""),
                "table_name": r.get("tableName", ""),
                "scenario_name": r.get("scenarioDescription", ""),
            }
        )
    return out


def fetch_all(aeo_year: int, key: str, start_year: int, sleep_s: float) -> list[dict]:
    """Fetch every (series, scenario) combination in :data:`SERIES`."""
    rows: list[dict] = []
    for table_id, series_id, fuel, metric, region in SERIES:
        for scenario in SCENARIOS:
            print(f"  fetching {fuel}/{metric}/{region} scenario={scenario} ...")
            for rec in _fetch_series(
                aeo_year, table_id, series_id, scenario, key, start_year, sleep_s
            ):
                rows.append(
                    {
                        "fuel": fuel,
                        "metric": metric,
                        "region": region,
                        "scenario": scenario,
                        "scenario_name": rec["scenario_name"],
                        "year": rec["period"],
                        "value": rec["value"],
                        "unit": rec["unit"],
                        "series_id": series_id,
                        "table_id": table_id,
                        "table_name": rec["table_name"],
                    }
                )
    rows.sort(
        key=lambda r: (r["fuel"], r["metric"], r["region"], r["scenario"], r["year"])
    )
    return rows


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "fuel",
        "metric",
        "region",
        "scenario",
        "scenario_name",
        "year",
        "value",
        "unit",
        "series_id",
        "table_id",
        "table_name",
    ]
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        w.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--aeo-year", type=int, default=2025, help="AEO release year")
    ap.add_argument(
        "--start-year",
        type=int,
        default=2024,
        help="earliest AEO projection year to pull (AEO2025 starts 2024)",
    )
    ap.add_argument("--sleep", type=float, default=0.3)
    args = ap.parse_args(argv)

    key = _load_key()
    if key == _DEMO_KEY:
        print(
            "WARNING: no EIA_API_KEY found (env or .env) -- using the public "
            "rate-limited DEMO_KEY. Register a free key at "
            "https://www.eia.gov/opendata/register.php for repeated use.",
            file=sys.stderr,
        )

    print(f"=== AEO{args.aeo_year} fuel-price trajectories (gas/coal/oil) ===")
    rows = fetch_all(args.aeo_year, key, args.start_year, args.sleep)
    _write_csv(OUT_CSV, rows)
    print(f"wrote {len(rows)} rows -> {OUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
