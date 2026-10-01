"""Download PJM DA / RT hourly LMP at the NY-facing interface pricing nodes.

WHY THIS EXISTS (NYISO-NEXT-10, 2026-09-28).  NEXT-7
(``docs/records/nyiso/FINDING-nyiso-next7-star-node-2026-09-27.md`` §3(c)) found the repo held
no PJM price at the seams with New York: ``pjm-zonal-lmp`` carries zones only.
PJM prices each external interface at an ``INTERFACE`` aggregate pnode; four face
New York (ids from the DataMiner2 ``pnode`` feed, ``pnode_subtype=INTERFACE``,
2026-09-28):

    5413134     NYIS       -- the PJM-NYISO AC proxy (Keystone/Branchburg/Ramapo)
    56958967    NEPTUNE    -- the Neptune HVDC (Sayreville -> Long Island)
    81436855    LINDENVFT  -- the Linden VFT (-> NYC, Goethals)
    1124361945  HUDSONTP   -- the Hudson Transmission Project (Bergen -> NYC, W 49th)

Feeds ``da_hrl_lmps`` / ``rt_hrl_lmps`` (RT = settlement-verified hourly).
**Archived rows (older than ~2 years) reject a ``pnode_id`` filter with HTTP
400**, but accept ``type=INTERFACE`` (verified 2026-09-28 on 2021-01-05: 8 rows
per hour, the four NY pnodes plus IMO, MISO, SOUTHIMP, SOUTHEXP), so the fetcher
pulls the whole INTERFACE type and keeps the four locally.  Pulled one month per
request (~6 k rows, under the 50 k page).

**Not committed** — PJM DataMiner2 non-member redistribution restriction
(``docs/data-licensing.md`` §4), the same treatment as ``pjm-zonal-lmp/`` and
``pjm-ehv-lmp/``.  The CSVs are gitignored; ``SHA256SUMS.txt`` is the committed
provenance record and this script is the recovery route.

Output: ``data/raw/seam-neighbour-price/pjm/PJM_ny_interface_lmp_<year>.csv``,
columns ``datetime_beginning_utc, datetime_beginning_ept, pnode_id, pnode_name,
market, total_lmp, congestion_price, marginal_loss_price`` (USD/MWh).

Usage:
    uv run python scripts/data/fetch_seam_neighbour_price_pjm.py --years 2021 2022 2023 2024 2025
"""

from __future__ import annotations

import argparse
import calendar
import csv
import datetime as dt
import urllib.error
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

from scripts.lib.pjm_dataminer import fetch_feed  # noqa: E402

RAW_DIR = RAW_DATA_DIR / "seam-neighbour-price" / "pjm"
STEM = "PJM_ny_interface_lmp"
USER_AGENT = "market-sim-seam-neighbour-price/1.0"

#: pnode_id -> name, from the DataMiner2 ``pnode`` feed (see module docstring).
NY_INTERFACE_PNODES: dict[str, str] = {
    "5413134": "NYIS",
    "56958967": "NEPTUNE",
    "81436855": "LINDENVFT",
    "1124361945": "HUDSONTP",
}

#: market -> (feed, the per-market column prefix DataMiner2 uses).
FEEDS: dict[str, tuple[str, str]] = {
    "DA": ("da_hrl_lmps", "da"),
    "RT": ("rt_hrl_lmps", "rt"),
}

COLUMNS = (
    "datetime_beginning_utc",
    "datetime_beginning_ept",
    "pnode_id",
    "pnode_name",
    "market",
    "total_lmp",
    "congestion_price",
    "marginal_loss_price",
)


def _iso(ts: str) -> str:
    """DataMiner2 ``M/D/YYYY h:mm:ss AM`` -> ISO-8601 ``YYYY-MM-DDTHH:MM:SS``."""
    return dt.datetime.strptime(ts, "%m/%d/%Y %I:%M:%S %p").isoformat()


def _pull(feed: str, first: str, last: str) -> list[dict]:
    """One INTERFACE pull over ``[first, last]`` (EPT dates, inclusive)."""
    window = f"{first}T00:00:00.0 to {last}T23:59:59.0"
    return fetch_feed(
        feed,
        {"type": "INTERFACE", "datetime_beginning_ept": window, "format": "csv"},
        user_agent=USER_AGENT,
        verbose=False,
    )


def fetch_month(market: str, year: int, month: int) -> list[dict]:
    """Fetch one market-month of INTERFACE rows and keep the four NY pnodes.

    A window that straddles DataMiner2's archive boundary (~2 years back) is
    rejected with HTTP 400 even though each side alone is served (measured
    2026-09-28: 2024-09-16..30 400s, 2024-09-25 and 2024-09-29 each 200), so
    a 400 on the month falls back to one request per day.
    """
    feed, pfx = FEEDS[market]
    last = calendar.monthrange(year, month)[1]
    try:
        rows = _pull(feed, f"{year}-{month:02d}-01", f"{year}-{month:02d}-{last:02d}")
    except urllib.error.HTTPError as exc:
        if exc.code != 400:
            raise
        rows = []
        for day in range(1, last + 1):
            d = f"{year}-{month:02d}-{day:02d}"
            rows += _pull(feed, d, d)
    out = []
    for r in rows:
        if r["pnode_id"] not in NY_INTERFACE_PNODES:
            continue
        # RT rows carry superseded versions (row_is_current=False) beside the
        # current one -- measured 2022-02: 1,344 doubled NY-pnode hours, 286
        # with different prices. Keep only the current version.
        if r.get("row_is_current", "True") != "True":
            continue
        out.append(
            {
                "datetime_beginning_utc": _iso(r["datetime_beginning_utc"]),
                "datetime_beginning_ept": _iso(r["datetime_beginning_ept"]),
                "pnode_id": r["pnode_id"],
                "pnode_name": r["pnode_name"],
                "market": market,
                "total_lmp": r[f"total_lmp_{pfx}"],
                "congestion_price": r[f"congestion_price_{pfx}"],
                "marginal_loss_price": r[f"marginal_loss_price_{pfx}"],
            }
        )
    return out


def fetch_year(year: int, dest_dir: Path = RAW_DIR) -> Path:
    """Fetch both markets for every month of ``year`` and write one sorted CSV."""
    rows: list[dict] = []
    for market in FEEDS:
        for month in range(1, 13):
            got = fetch_month(market, year, month)
            print(f"  {year}-{month:02d} {market}: {len(got)} rows", flush=True)
            rows.extend(got)
    rows.sort(key=lambda r: (r["market"], r["pnode_id"], r["datetime_beginning_utc"]))
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"{STEM}_{year}.csv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(COLUMNS))
        w.writeheader()
        w.writerows(rows)
    return path


def main(argv: list[str] | None = None) -> int:
    """Fetch the requested years."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--years", nargs="+", type=int, required=True)
    p.add_argument("--out-dir", type=Path, default=RAW_DIR)
    args = p.parse_args(argv)
    for y in args.years:
        print(f"wrote {fetch_year(y, args.out_dir)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
