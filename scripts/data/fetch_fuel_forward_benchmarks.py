#!/usr/bin/env python3
"""Fetch near-term natural-gas forward benchmarks for the FF-G2 triangulation.

These are **context/benchmarks only — never fit targets** (CLAUDE.md rule 1;
docs/fuel-forward-methodology-2026-07.md). They let the FF-G2 doc triangulate
the near-term (2026-2028) AEO2026 annual Henry Hub path against two independent
references:

  * **EIA Short-Term Energy Outlook (STEO)** Henry Hub spot-price forecast —
    the short-horizon, market/futures-informed sibling of the AEO (which is
    long-horizon fundamentals). API-fetchable, so this is a rule-13-admissible
    reproducible input (it regenerates for any forward vintage). Series:
      - ``NGHHUUS`` — Henry Hub spot, annual, real... actually **nominal**
        $/MMBtu (STEO is a nominal forecast; documented in the README).
      - ``NGHHMCF`` — Henry Hub spot, monthly, $/mcf.
  * **NYMEX Henry Hub futures strip (CME)** — the exchange-traded forward
    curve. The full multi-year strip is published by CME behind a bot-wall /
    licence, and EIA's free ``RNGC1..RNGC4`` futures series (contracts 1-4)
    stopped updating in 2024 on the open API — so the *current* strip is a
    **MANUAL DOWNLOAD** row in the datatype README, never guessed (rule 5).
    This script still pulls whatever ``RNGC1..RNGC4`` the free API returns and
    records the as-of date, so the staleness is auditable rather than asserted.

Output (raw, immutable):
  data/raw/fuel-forward-benchmarks/steo_henry_hub.csv
  data/raw/fuel-forward-benchmarks/nymex_hh_futures_eia_free.csv   (may be stale)

EIA API v2 docs: https://www.eia.gov/opendata/documentation.php

Usage:
    EIA_API_KEY=your_key python scripts/data/fetch_fuel_forward_benchmarks.py
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

REPO = Path(__file__).resolve().parent.parent.parent
OUT_DIR = REPO / "data" / "raw" / "fuel-forward-benchmarks"
BASE = "https://api.eia.gov/v2"
_DEMO_KEY = "DEMO_KEY"


def _load_key() -> str:
    key = os.environ.get("EIA_API_KEY")
    if not key and (REPO / ".env").exists():
        for line in (REPO / ".env").read_text().splitlines():
            if line.startswith("EIA_API_KEY="):
                candidate = line.split("=", 1)[1].strip()
                if candidate:
                    key = candidate
                break
    return key or _DEMO_KEY


def _get(url: str) -> dict:
    with urlopen(url, timeout=60) as fh:
        return json.loads(fh.read().decode())


def fetch_steo(key: str) -> list[dict]:
    """Henry Hub STEO forecast: annual $/MMBtu + monthly $/mcf."""
    rows: list[dict] = []
    specs = [
        ("annual", "NGHHUUS", "henry_hub_spot_annual"),
        ("monthly", "NGHHMCF", "henry_hub_spot_monthly"),
    ]
    for freq, series, metric in specs:
        q = {
            "api_key": key,
            "frequency": freq,
            "facets[seriesId][]": series,
            "data[0]": "value",
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "length": 500,
        }
        url = f"{BASE}/steo/data/?{urlencode(q)}"
        for r in _get(url).get("response", {}).get("data", []):
            if r.get("value") in (None, "", "NA"):
                continue
            rows.append(
                {
                    "source": "EIA STEO",
                    "metric": metric,
                    "series_id": series,
                    "period": r["period"],
                    "value": round(float(r["value"]), 4),
                    "unit": r.get("unit", ""),
                    "series_description": r.get("seriesDescription", ""),
                }
            )
    return rows


def fetch_nymex_free(key: str) -> list[dict]:
    """EIA free NYMEX HH futures contracts 1-4 (may be stale — documented)."""
    rows: list[dict] = []
    for c in ("RNGC1", "RNGC2", "RNGC3", "RNGC4"):
        q = {
            "api_key": key,
            "frequency": "daily",
            "facets[series][]": c,
            "data[0]": "value",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": 1,
        }
        url = f"{BASE}/natural-gas/pri/fut/data/?{urlencode(q)}"
        data = _get(url).get("response", {}).get("data", [])
        if data:
            r = data[0]
            rows.append(
                {
                    "source": "EIA NYMEX futures (free feed)",
                    "contract": c,
                    "as_of": r["period"],
                    "value": round(float(r["value"]), 4),
                    "unit": r.get("units", ""),
                }
            )
    return rows


def _write_csv(path: Path, rows: list[dict], header: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        w.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    key = _load_key()
    if key == _DEMO_KEY:
        print(
            "WARNING: no EIA_API_KEY (env or .env) -- using rate-limited DEMO_KEY.",
            file=sys.stderr,
        )

    steo = fetch_steo(key)
    _write_csv(
        OUT_DIR / "steo_henry_hub.csv",
        steo,
        [
            "source",
            "metric",
            "series_id",
            "period",
            "value",
            "unit",
            "series_description",
        ],
    )
    print(f"wrote {len(steo)} STEO rows -> {OUT_DIR / 'steo_henry_hub.csv'}")

    nymex = fetch_nymex_free(key)
    _write_csv(
        OUT_DIR / "nymex_hh_futures_eia_free.csv",
        nymex,
        ["source", "contract", "as_of", "value", "unit"],
    )
    if nymex:
        latest = max(r["as_of"] for r in nymex)
        print(
            f"wrote {len(nymex)} NYMEX (free-feed) rows -> "
            f"{OUT_DIR / 'nymex_hh_futures_eia_free.csv'}  (latest as_of {latest})"
        )
        print(
            "  NOTE: the EIA free NYMEX feed is stale; the CURRENT full CME "
            "strip is a MANUAL DOWNLOAD row in the datatype README (rule 5)."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
