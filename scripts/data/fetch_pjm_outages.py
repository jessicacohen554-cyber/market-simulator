"""Fetch PJM generation-outage history from the Data Miner 2 API.

Downloads the ``gen_outages_by_type`` feed ("Generation Outage for Seven Days
by Type") from PJM's public Data Miner 2 REST API and writes the full row set
to ``data/raw/pjm-outages/gen_outages_by_type.csv`` (the immutable raw source).
This is PJM's published, DAM-horizon generation-outage forecast: for each
posting day it carries the actual + scheduled MW on outage for today and the
next six days, broken out by outage type (forced / maintenance / planned) and
by region (Mid Atlantic - Dominion, Western, PJM RTO).

Source / provenance
-------------------
* Endpoint  : https://api.pjm.com/api/v1/gen_outages_by_type
* Tool      : PJM Data Miner 2 (https://dataminer2.pjm.com/feed/gen_outages_by_type)
* Feed docs : "Generation Outage for Seven Days by Type", posted daily 06:00 EPT,
              first available 2015-05-26, retained indefinitely.
* Auth      : the anonymous ``Ocp-Apim-Subscription-Key`` the Data Miner 2 web
              client publishes at https://dataminer2.pjm.com/config/settings.json
              (no personal registration required). Override with ``--api-key`` or
              the ``PJM_API_KEY`` env var if PJM rotates the anonymous key.

This is the PJM analogue of ERCOT's 60-Day DAM disclosure thermal-availability
source (``scripts/data/derive_ercot_thermal_dam_availability.py``): a
market-operator-published, forward-looking capacity-availability quantity that
regenerates for future days and responds to changed conditions (CLAUDE.md
rule 13 admissible). It is a *measured/forecast input*, never a fitted answer.

Usage::

    python scripts/data/fetch_pjm_outages.py \
        [--start 2018-01-01] [--end 2026-12-31] \
        [--out data/raw/pjm-outages/gen_outages_by_type.csv]
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import pandas as pd
import requests

REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO / "data" / "raw" / "pjm-outages" / "gen_outages_by_type.csv"

API_URL = "https://api.pjm.com/api/v1/gen_outages_by_type"
SETTINGS_URL = "https://dataminer2.pjm.com/config/settings.json"
# The Data Miner 2 web client ships this anonymous subscription key publicly; it
# is not a secret and grants read-only access to the public feeds. Resolved at
# runtime from SETTINGS_URL so a rotation is picked up automatically; this
# literal is only the last-resort fallback.
_FALLBACK_KEY = "6a75d9f6d933401dbb4f36f8e70b95b3"
PAGE_ROWS = 50000  # Data Miner 2 caps a single response at 50,000 rows.

# Native feed columns (see the feed metadata endpoint). forced == unplanned.
COLUMNS = [
    "forecast_execution_date_ept",
    "forecast_date",
    "region",
    "total_outages_mw",
    "planned_outages_mw",
    "maintenance_outages_mw",
    "forced_outages_mw",
]


def resolve_api_key(cli_key: str | None) -> str:
    """Return the subscription key: CLI > env > live settings.json > fallback."""
    if cli_key:
        return cli_key
    env = os.environ.get("PJM_API_KEY")
    if env:
        return env
    try:
        r = requests.get(SETTINGS_URL, timeout=30)
        r.raise_for_status()
        key = r.json().get("subscriptionKey")
        if key:
            return str(key)
    except requests.RequestException:
        pass
    return _FALLBACK_KEY


def _get(url: str, headers: dict, params: dict, retries: int = 4) -> dict:
    """GET with exponential backoff on transient network / 5xx errors."""
    delay = 2.0
    last: Exception | None = None
    for _ in range(retries):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=120)
            if resp.status_code >= 500:
                raise requests.HTTPError(f"{resp.status_code} server error")
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:  # pragma: no cover - network
            last = exc
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"PJM API request failed after {retries} attempts: {last}")


def fetch(start: str, end: str, api_key: str) -> pd.DataFrame:
    """Fetch every ``gen_outages_by_type`` row for execution dates in [start, end].

    Pages through the feed ``PAGE_ROWS`` at a time (ascending by execution date)
    and returns the concatenated frame with the native feed columns. ``start`` /
    ``end`` are inclusive ``YYYY-MM-DD`` execution-date bounds passed to the API's
    range filter so we only pull the requested window.
    """
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    # The API rejects a fields+sort+date-range combination (400); the whole feed
    # is small (~85k rows), so we page the full feed ascending and clip to the
    # requested execution-date window in pandas below.
    base = {
        "startRow": 1,
        "rowCount": PAGE_ROWS,
        "order": "Asc",
        "sort": "forecast_execution_date_ept",
    }
    frames: list[pd.DataFrame] = []
    start_row = 1
    total = None
    while True:
        params = dict(base, startRow=start_row)
        payload = _get(API_URL, headers, params)
        items = payload.get("items", [])
        if total is None:
            total = payload.get("totalRows", 0)
            print(f"totalRows (full feed): {total}")
        if not items:
            break
        frames.append(pd.DataFrame(items))
        got = len(frames[-1])
        print(f"  fetched rows {start_row}..{start_row + got - 1}")
        start_row += got
        if start_row > (total or 0) or got < PAGE_ROWS:
            break
    if not frames:
        return pd.DataFrame(columns=COLUMNS)
    df = pd.concat(frames, ignore_index=True)[COLUMNS]
    # Clip to the requested inclusive execution-date window.
    exec_day = pd.to_datetime(df["forecast_execution_date_ept"]).dt.normalize()
    mask = (exec_day >= pd.Timestamp(start)) & (exec_day <= pd.Timestamp(end))
    return df.loc[mask].reset_index(drop=True)


def main() -> None:
    """CLI entry point: fetch the feed window and write the raw CSV."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", default="2018-01-01", help="inclusive YYYY-MM-DD")
    ap.add_argument("--end", default="2026-12-31", help="inclusive YYYY-MM-DD")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--api-key", default=None, help="override subscription key")
    args = ap.parse_args()

    key = resolve_api_key(args.api_key)
    df = fetch(args.start, args.end, key)
    if df.empty:
        raise SystemExit("no rows returned from PJM API")
    df = df.sort_values(["forecast_execution_date_ept", "forecast_date", "region"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    n_exec = df["forecast_execution_date_ept"].nunique()
    print(
        f"wrote {len(df):,} rows ({n_exec:,} execution dates, "
        f"{df['region'].nunique()} regions) -> {args.out}"
    )


if __name__ == "__main__":
    main()
