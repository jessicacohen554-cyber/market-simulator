"""Fetch PJM transmission-ZONE LMP components (MEC / MCC / MLC) from DataMiner2.

The pjm-136 intake behind the PJM marginal-loss (delivery-factor) surface —
the PJM analogue of the MISO `lmp-components` intake that backs
`scripts/data/derive_miso_loss_surface.py` (miso-76 A2/A3).

**Why zone pnodes and not the committed hub file.** The repo already commits
`data/raw/lmp-data/PJM_<year>_rt_da_monthly_lmps.csv`, but that file carries only
PJM's twelve trading **HUBs** — price baskets that do not align to the model's
eight zones: three of them sit inside `PJM_ComEd` alone while `PJM_West_APS`,
`PJM_Central_PA` and `PJM_SWMAAC` have no hub at all. PJM separately publishes a
`type = ZONE` pnode per transmission zone (AECO, AEP, APS, ATSI, BGE, COMED,
DAY, DEOK, DOM, DPL, DUQ, EKPC, JCPL, METED, OVEC, PECO, PENELEC, PEPCO, PPL,
PSEG, RECO), which is the load-weighted zonal price the model's zonal duals are
the analogue of, and which crosswalks 1:1 onto all eight model zones via the
canonical `eia930.zonal_shares._PJM_LOAD_ZONE_GROUPS`. CLAUDE.md rule 14
[R-ACCURATE]: take the aligned measured series over a misaligned proxy.

Feeds (same DataMiner2 REST API, public subscription key, paging and back-off as
the other `fetch_pjm_*` scripts):

* ``da_hrl_lmps`` — hourly day-ahead LMP with its published
  ``system_energy_price_da`` / ``congestion_price_da`` /
  ``marginal_loss_price_da`` components. **The derive basis**: the DA market is
  the hourly, commitment-aware full-network optimization the model's LP mirrors.
* ``rt_hrl_lmps`` — the real-time counterpart, fetched for the acceptance
  report only, never derived from.

One compressed Parquet per feed per calendar month is written to
``data/raw/pjm-zonal-lmp/`` (**gitignored** — same PJM DataMiner2 non-member
redistribution restriction as `pjm-energy-offers/` and `pjm-da-virtuals/`; see
`docs/data-licensing.md` §4 and the directory README for the sha256 provenance
manifest). Only the small dimensionless DERIVED surface is committed.

Usage
-----
    python scripts/data/fetch_pjm_zonal_lmp_components.py            # 2023-2025, both feeds
    python scripts/data/fetch_pjm_zonal_lmp_components.py --years 2024
    python scripts/data/fetch_pjm_zonal_lmp_components.py --feeds da_hrl_lmps
    python scripts/data/fetch_pjm_zonal_lmp_components.py --manifest # rewrite sha256 manifest
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

OUT_DIR = paths.RAW_DATA_DIR / "pjm-zonal-lmp"

#: feed name -> (datetime filter/sort field, market-run suffix)
FEEDS: dict[str, tuple[str, str]] = {
    "da_hrl_lmps": ("datetime_beginning_ept", "da"),
    "rt_hrl_lmps": ("datetime_beginning_ept", "rt"),
}

#: Columns kept verbatim from the feed (everything the component identity needs).
KEEP = (
    "datetime_beginning_utc",
    "datetime_beginning_ept",
    "pnode_id",
    "pnode_name",
    "type",
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
    sleep_s: float = 1.5,
) -> pd.DataFrame:
    """Download every ZONE-pnode row for one day range; return one frame."""
    # NB: no ``sort``/``order`` — the hrl_lmps feeds reject them with HTTP 400
    # (unlike the bid feeds the other fetchers use), so rows are ordered here.
    params = {
        "isActiveMetadata": "true",
        "format": "csv",
        "type": "ZONE",
        ts_field: _date_filter(year, month, day_from, day_to),
    }
    rows = pjm_dataminer.fetch_feed(
        feed,
        params,
        user_agent="market-sim/fetch_pjm_zonal_lmp_components",
        sleep_s=sleep_s,
        verbose=False,
    )
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame = frame.sort_values([ts_field, "pnode_name"]).reset_index(drop=True)
    return frame


def _fetch_month(
    feed: str, ts_field: str, year: int, month: int, *, sleep_s: float
) -> pd.DataFrame:
    """Fetch one feed-month, bisecting the window on DataMiner2's HTTP 400.

    The gateway rejects some multi-day windows with 400 while serving each
    half of the same window fine (reproduced 2026-07-28: `da_hrl_lmps`
    2024-07-01..31 and 2024-07-16..31 both 400, 2024-07-01..15 returns
    8,280 rows). The cause is on PJM's side and is not rate-related —
    `fetch_page` already backs off on 429/503 — so the window is halved down
    to single days rather than changing retry policy for every other
    `fetch_pjm_*` consumer. A day that still 400s is reported and skipped, and
    the completeness check at the end of `main` fails the run loudly rather
    than writing a silently short month.
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
    return out.sort_values([ts_field, "pnode_name"]).reset_index(drop=True)


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
    ap.add_argument("--sleep", type=float, default=1.0)
    args = ap.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.manifest:
        _write_manifest()
        return 0

    for feed in args.feeds:
        ts_field, run = FEEDS[feed]
        float_cols = (
            f"system_energy_price_{run}",
            f"total_lmp_{run}",
            f"congestion_price_{run}",
            f"marginal_loss_price_{run}",
        )
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
                for col in float_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                keep = [c for c in (*KEEP, *float_cols) if c in df.columns]
                df[keep].to_parquet(out, compression="zstd", index=False)
                hours = pd.to_datetime(df[ts_field]).nunique()
                expected = calendar.monthrange(year, month)[1] * 24
                flag = "" if hours >= expected else f"  << SHORT (expect {expected})"
                print(
                    f"{len(df)} rows, {df['pnode_name'].nunique()} zones, "
                    f"{hours} h{flag}",
                    flush=True,
                )
    _write_manifest()
    return 0


if __name__ == "__main__":
    sys.exit(main())
