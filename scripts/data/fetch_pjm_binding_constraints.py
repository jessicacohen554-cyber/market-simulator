#!/usr/bin/env python3
"""Fetch PJM's published day-ahead BINDING TRANSMISSION CONSTRAINTS from DataMiner2.

The pjm-137 intake behind the question `FINDING-pjm136` §5 left open: the model
reproduces PJM's *loss* separation but produces no **congestion** at all on the
Dominion boundary, and the lever family that tightens a flow limit is closed by
measurement (every internal PJM link is bound-but-priceless). Before proposing
any successor mechanism, PJM's own record is asked which facility was actually
binding, and for how much rent — the PJM analogue of MISO's `bc_HIST` binding
constraint feed (`data/raw/lmp-data/MISO/`).

Two feeds, both public DataMiner2 REST (same subscription key, paging and
back-off as every other `fetch_pjm_*` script via `scripts.lib.pjm_dataminer`):

* ``da_marginal_value`` — **the analysis basis.** One row per binding
  constraint per DAY-AHEAD hour: ``monitored_facility``,
  ``contingency_facility`` and the constraint's ``shadow_price`` ($/MWh of
  relief). The day-ahead market is the hourly, commitment-aware full-network
  optimization the model's LP mirrors, and its shadow price is the exact
  analogue of the model's own transmission-constraint dual — so the two are
  directly comparable quantities, not proxies.
* ``da_transconstraints`` — the companion congestion-EVENT record (same
  facility keys plus ``duration`` and ``day_ahead_congestion_event``), fetched
  for cross-checking event counts against the hourly rent record. Carries no
  shadow price and is never derived from.

Both feeds are small (~55–80 k rows/year, roughly 6–9 binding constraint-hours
per hour of the year), so a whole year fetches in a couple of minutes.

One compressed Parquet per feed per calendar month is written to
``data/raw/pjm-binding-constraints/`` (**gitignored** — same PJM DataMiner2
non-member redistribution restriction as `pjm-energy-offers/`,
`pjm-da-virtuals/` and `pjm-zonal-lmp/`; see `docs/data-licensing.md` §4 and the
directory README for the sha256 provenance manifest).

Usage
-----
    python scripts/data/fetch_pjm_binding_constraints.py            # 2023-2025, both feeds
    python scripts/data/fetch_pjm_binding_constraints.py --years 2025
    python scripts/data/fetch_pjm_binding_constraints.py --feeds da_marginal_value
    python scripts/data/fetch_pjm_binding_constraints.py --manifest # rewrite sha256 manifest
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import sys
import urllib.error
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config import paths  # noqa: E402
from scripts.lib import pjm_dataminer  # noqa: E402

OUT_DIR = paths.RAW_DATA_DIR / "pjm-binding-constraints"

#: feed name -> (datetime filter/sort field, numeric columns to coerce)
FEEDS: dict[str, tuple[str, tuple[str, ...]]] = {
    "da_marginal_value": ("datetime_beginning_ept", ("shadow_price",)),
    "da_transconstraints": ("datetime_beginning_ept", ("duration",)),
}

#: Columns kept verbatim from either feed (whatever the feed actually returns).
KEEP = (
    "datetime_beginning_utc",
    "datetime_beginning_ept",
    "datetime_ending_utc",
    "datetime_ending_ept",
    "monitored_facility",
    "contingency_facility",
    "day_ahead_congestion_event",
    "duration",
    "shadow_price",
)


def _date_filter(year: int, month: int, day_from: int, day_to: int) -> str:
    """EPT day-range filter string (ISO-8601, DataMiner2 convention)."""
    start = f"{year:04d}-{month:02d}-{day_from:02d}T00:00:00.0000000"
    end = f"{year:04d}-{month:02d}-{day_to:02d}T23:59:59.0000000"
    return f"{start} to {end}"


def _fetch_window(
    feed: str,
    ts_field: str,
    year: int,
    month: int,
    day_from: int,
    day_to: int,
    *,
    sleep_s: float = 1.0,
) -> pd.DataFrame:
    """Download every binding-constraint row for one day range; return one frame."""
    # NB: no ``sort``/``order`` — these feeds reject them with HTTP 400 (same as
    # the hrl_lmps feeds), so rows are ordered here instead.
    params = {
        "isActiveMetadata": "true",
        "format": "csv",
        ts_field: _date_filter(year, month, day_from, day_to),
    }
    rows = pjm_dataminer.fetch_feed(
        feed,
        params,
        user_agent="market-sim/fetch_pjm_binding_constraints",
        sleep_s=sleep_s,
        verbose=False,
    )
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame = frame.sort_values([ts_field, "monitored_facility"]).reset_index(
            drop=True
        )
    return frame


def _fetch_month(
    feed: str, ts_field: str, year: int, month: int, *, sleep_s: float
) -> pd.DataFrame:
    """Fetch one feed-month, bisecting the window on DataMiner2's HTTP 400.

    Same gateway behaviour the zonal-LMP intake documents: some multi-day
    windows are rejected with 400 while each half of the same window serves
    fine. The window is halved down to single days rather than changing retry
    policy for every other `fetch_pjm_*` consumer; a day that still 400s is
    reported and skipped, and `main`'s completeness print flags a short month.
    """
    last_day = calendar.monthrange(year, month)[1]
    frames: list[pd.DataFrame] = []
    windows: list[tuple[int, int]] = [(1, last_day)]
    while windows:
        lo, hi = windows.pop(0)
        try:
            frames.append(
                _fetch_window(feed, ts_field, year, month, lo, hi, sleep_s=sleep_s)
            )
        except urllib.error.HTTPError as exc:
            if exc.code != 400:
                raise
            if lo == hi:
                print(f"  !! HTTP 400 on {year}-{month:02d}-{lo:02d} — SKIPPED")
                continue
            mid = (lo + hi) // 2
            print(f"  HTTP 400 on days {lo}-{hi}; bisecting")
            windows[:0] = [(lo, mid), (mid + 1, hi)]
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    return out.sort_values([ts_field, "monitored_facility"]).reset_index(drop=True)


def _write_manifest() -> None:
    """Rewrite the sha256 provenance manifest for the gitignored bulk pull."""
    lines = ["# sha256  size_bytes  file", ""]
    for path in sorted(OUT_DIR.glob("*.parquet")):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.stat().st_size}  {path.name}")
    (OUT_DIR / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")
    print(f"  wrote {OUT_DIR / 'SHA256SUMS.txt'} ({len(lines) - 2} files)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--months", nargs="*", type=int, default=list(range(1, 13)))
    ap.add_argument("--feeds", nargs="*", choices=sorted(FEEDS), default=sorted(FEEDS))
    ap.add_argument("--force", action="store_true", help="re-download existing files")
    ap.add_argument("--manifest", action="store_true", help="only rewrite SHA256SUMS")
    ap.add_argument("--sleep", type=float, default=0.6)
    args = ap.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.manifest:
        _write_manifest()
        return 0

    for feed in args.feeds:
        ts_field, num_cols = FEEDS[feed]
        for year in args.years:
            for month in args.months:
                out = OUT_DIR / f"{feed}_{year:04d}_{month:02d}.parquet"
                if out.exists() and not args.force:
                    print(f"[skip] {out.name} exists")
                    continue
                print(f"[{feed} {year}-{month:02d}]", end=" ", flush=True)
                df = _fetch_month(feed, ts_field, year, month, sleep_s=args.sleep)
                if df.empty:
                    print(f"\n  !! no rows for {year}-{month:02d}; not writing")
                    continue
                for col in num_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                keep = [c for c in KEEP if c in df.columns]
                df[keep].to_parquet(out, compression="zstd", index=False)
                hours = pd.to_datetime(df[ts_field], format="mixed").nunique()
                expected = calendar.monthrange(year, month)[1] * 24
                flag = "" if hours >= expected * 0.9 else f"  << THIN (of {expected} h)"
                print(
                    f"{len(df)} rows, {df['monitored_facility'].nunique()} facilities, "
                    f"{hours} h{flag}",
                    flush=True,
                )
    _write_manifest()
    return 0


if __name__ == "__main__":
    sys.exit(main())
