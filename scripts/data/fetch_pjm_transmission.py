#!/usr/bin/env python3
"""Fetch PJM DataMiner2 transmission/interchange/hub-LMP feeds for holdout years.

Rule-22 holdout intake (docs/handoffs/holdout-policy-memo-2026-07.md): extends
the existing 2023-2025 raw drops in ``data/raw/iso-specific-transmission/`` and
``data/raw/lmp-data/`` to 2018-2022 and H1-2026, using PJM's public DataMiner2
REST API (subscription key is public — embedded in the DataMiner2 Angular
app's settings.json, same key ``fetch_pjm_energy_offers.py`` uses).

Three feeds, one CLI:

* ``interchange`` — ``act_sch_interchange`` (firstAvailable 2014-01-01,
  retention indefinite) -> ``PJM_<year>_import_export_act_sch_interchange.csv``
  (data-register row 36).
* ``transfer`` — ``transfer_limits_and_flows`` (firstAvailable 2011-01-01,
  retention indefinite) -> ``PJM_<year>_transfer_limits_and_flows.csv``
  (data-register row 36).
* ``hublmp`` — ``da_hrl_lmps`` + ``rt_hrl_lmps``, both filtered
  ``type=HUB`` (covers the transmission hubs AND the MISO-facing generator
  hubs CHICAGO GEN HUB / AEP GEN HUB / ATSI GEN HUB used by
  ``build_pjm_border_lmp_miso.py``), merged on
  (datetime_beginning_utc, pnode_id) into the same wide schema as the
  existing ``PJM_<year>_rt_da_monthly_lmps.csv`` (data-register row 40 PJM
  validation LMP + row 38 MISO-PJM border LMP input) ->
  ``PJM_<year>_rt_da_monthly_lmps.csv``.

Verified 2026-07-10: all three feeds return unfiltered/type-filtered archived
data back to at least 2019 with no ``API_1044`` restriction (only
``pnode_name`` filtering is blocked on >2yr-old archived rows; ``type`` is
not).

H1-2026 scope cap
-----------------
The rule-22 intake authorization for 2026 covers **Jan 1 - Jun 30 only**.
``--h1-2026`` requests exactly that window and writes the result under a
``_partial`` filename suffix (``PJM_2026_<feed>_partial.csv``), the same
convention ``fetch_pjm_as.py`` uses and for the same reason: every consumer
(``derive_interface_limits.py``, ``derive_pjm_seam_ladders.py``,
``data/eia930/envelopes.py``, the probes) resolves the plain
``PJM_<year>_<feed>.csv`` name and would silently treat a half-year file as a
full year. The suffix makes a partial year invisible to those consumers rather
than quietly wrong. ``--years 2026`` is refused — use ``--h1-2026``.

Usage:
    python scripts/data/fetch_pjm_transmission.py --feed interchange --years 2018 2019 2020 2021 2022
    python scripts/data/fetch_pjm_transmission.py --feed transfer --h1-2026
    python scripts/data/fetch_pjm_transmission.py --feed hublmp --years 2018 2019
"""

from __future__ import annotations

import argparse
import calendar
import sys
from datetime import date
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import ISO_TRANSMISSION_DIR, LMP_DATA_DIR  # noqa: E402
from scripts.lib import pjm_dataminer  # noqa: E402

TRANS_DIR = ISO_TRANSMISSION_DIR
LMP_DIR = LMP_DATA_DIR

# The API base / public subscription key / page size live in
# scripts.lib.pjm_dataminer (shared across the fetch_pjm_* scripts).

# The rule-22 intake authorization covers Jan 1 - Jun 30 2026 for the "H1-2026"
# leg — a hard cap, not a default (same constant pair as fetch_pjm_as.py).
H1_2026_YEAR = 2026
H1_2026_LAST_MONTH = 6


def _date_filter(year: int, month: int) -> str:
    last_day = calendar.monthrange(year, month)[1]
    end_date = min(date(year, month, last_day), date.today())
    start = f"{year:04d}-{month:02d}-01T00:00:00.0000000"
    end = f"{end_date:%Y-%m-%d}T23:59:59.0000000"
    return f"{start} to {end}"


def _out_name(stem: str, year: int, h1_only: bool) -> str:
    """Filename for one feed-year — ``_partial`` suffixed when the year is capped.

    A partial year never takes the plain ``PJM_<year>_<stem>.csv`` name that
    every consumer resolves directly (module docstring, "H1-2026 scope cap").
    """
    suffix = "_partial" if h1_only else ""
    return f"PJM_{year}_{stem}{suffix}.csv"


def _fetch_all_pages(
    feed: str, date_filter: str, extra_params: dict, sleep_s: float, retries: int
) -> pd.DataFrame:
    """Page through one DataMiner2 feed for one calendar month; return concatenated rows."""
    params = {
        "datetime_beginning_ept": date_filter,
        "format": "csv",
        **extra_params,
    }
    rows = pjm_dataminer.fetch_feed(
        feed,
        params,
        user_agent="market-sim/fetch_pjm_transmission",
        sleep_s=sleep_s,
        retries=retries,
        verbose=False,
    )
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _fetch_year(
    feed: str,
    year: int,
    extra_params: dict,
    sleep_s: float,
    retries: int,
    h1_only: bool = False,
) -> pd.DataFrame:
    months_end = 13 if date.today().year > year else date.today().month + 1
    if h1_only:
        months_end = min(months_end, H1_2026_LAST_MONTH + 1)
    frames = []
    for month in range(1, months_end):
        if date(year, month, 1) > date.today():
            break
        print(f"  {feed} {year}-{month:02d} …", flush=True)
        df = _fetch_all_pages(
            feed, _date_filter(year, month), extra_params, sleep_s, retries
        )
        print(f"    {len(df)} rows")
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def fetch_interchange(
    years: list[int], sleep_s: float, retries: int, h1_only: bool = False
) -> None:
    TRANS_DIR.mkdir(parents=True, exist_ok=True)
    for year in years:
        out = TRANS_DIR / _out_name("import_export_act_sch_interchange", year, h1_only)
        df = _fetch_year("act_sch_interchange", year, {}, sleep_s, retries, h1_only)
        if df.empty:
            print(f"  {year}: no data returned — skipping")
            continue
        df.to_csv(out, index=False)
        print(f"wrote {out.relative_to(REPO)} ({len(df):,} rows)")


def fetch_transfer(
    years: list[int], sleep_s: float, retries: int, h1_only: bool = False
) -> None:
    TRANS_DIR.mkdir(parents=True, exist_ok=True)
    for year in years:
        out = TRANS_DIR / _out_name("transfer_limits_and_flows", year, h1_only)
        df = _fetch_year(
            "transfer_limits_and_flows", year, {}, sleep_s, retries, h1_only
        )
        if df.empty:
            print(f"  {year}: no data returned — skipping")
            continue
        df.to_csv(out, index=False)
        print(f"wrote {out.relative_to(REPO)} ({len(df):,} rows)")


# Renamed *_da/*_rt columns -> the wide schema of the existing
# PJM_<year>_rt_da_monthly_lmps.csv (module docstring).
_DA_RENAME = {
    "system_energy_price_da": "system_energy_price_da",
    "total_lmp_da": "total_lmp_da",
    "congestion_price_da": "congestion_price_da",
    "marginal_loss_price_da": "marginal_loss_price_da",
}
_MERGE_KEYS = ["datetime_beginning_utc", "pnode_id"]
_SHARED_COLS = [
    "datetime_beginning_utc",
    "datetime_beginning_ept",
    "pnode_id",
    "pnode_name",
    "voltage",
    "equipment",
    "type",
    "zone",
]
_OUT_COLS = _SHARED_COLS + [
    "system_energy_price_rt",
    "total_lmp_rt",
    "congestion_price_rt",
    "marginal_loss_price_rt",
    "system_energy_price_da",
    "total_lmp_da",
    "congestion_price_da",
    "marginal_loss_price_da",
]


def fetch_hublmp(
    years: list[int], sleep_s: float, retries: int, h1_only: bool = False
) -> None:
    LMP_DIR.mkdir(parents=True, exist_ok=True)
    for year in years:
        out = LMP_DIR / _out_name("rt_da_monthly_lmps", year, h1_only)
        da = _fetch_year(
            "da_hrl_lmps", year, {"type": "HUB"}, sleep_s, retries, h1_only
        )
        rt = _fetch_year(
            "rt_hrl_lmps", year, {"type": "HUB"}, sleep_s, retries, h1_only
        )
        if da.empty or rt.empty:
            print(f"  {year}: da={len(da)} rt={len(rt)} rows — skipping (need both)")
            continue
        for df in (da, rt):
            df["pnode_id"] = pd.to_numeric(df["pnode_id"], errors="coerce")
        merged = rt.merge(
            da[_MERGE_KEYS + list(_DA_RENAME)],
            on=_MERGE_KEYS,
            how="outer",
            suffixes=("", "_da_dup"),
        )
        missing = [c for c in _OUT_COLS if c not in merged.columns]
        if missing:
            print(f"  {year}: missing expected columns after merge: {missing}")
        merged = merged.reindex(columns=_OUT_COLS)
        merged = merged.sort_values(["datetime_beginning_utc", "pnode_name"])
        merged.to_csv(out, index=False)
        print(f"wrote {out.relative_to(REPO)} ({len(merged):,} rows)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--feed", required=True, choices=["interchange", "transfer", "hublmp"]
    )
    ap.add_argument("--years", nargs="+", type=int)
    ap.add_argument(
        "--h1-2026",
        action="store_true",
        help="fetch Jan 1 - Jun 30 2026 only, written under a _partial suffix "
        "(the rule-22 intake authorization's hard cap for 2026)",
    )
    ap.add_argument("--sleep", type=float, default=1.5)
    ap.add_argument("--retries", type=int, default=4)
    args = ap.parse_args()

    if args.h1_2026:
        if args.years:
            ap.error("--h1-2026 is exclusive with --years")
        years, h1_only = [H1_2026_YEAR], True
    else:
        if not args.years:
            ap.error("one of --years / --h1-2026 is required")
        if H1_2026_YEAR in args.years:
            ap.error(
                f"--years must not include {H1_2026_YEAR}: the intake "
                "authorization caps 2026 at Jun 30 — use --h1-2026"
            )
        years, h1_only = sorted(args.years), False

    if args.feed == "interchange":
        fetch_interchange(years, args.sleep, args.retries, h1_only)
    elif args.feed == "transfer":
        fetch_transfer(years, args.sleep, args.retries, h1_only)
    else:
        fetch_hublmp(years, args.sleep, args.retries, h1_only)


if __name__ == "__main__":
    main()
