#!/usr/bin/env python3
"""Fetch PJM 500 kV EHV aggregate-node LMPs from DataMiner2 (intra-zonal spread).

The pjm-137 intake behind the topology question `FINDING-pjm136` §3 left open
for `PJM_Dominion`. pjm-136 tested whether the 8-zone reduction can carry the
DOM-vs-AEP separation by comparing PJM's published trading HUBs *inside* one
model zone against the inter-zone spread — but PJM publishes no hub inside
`PJM_Dominion`, so the same test could not be run there, and Dominion's own
internal spread was never measured.

PJM does publish, separately from the hubs, an ``AGGREGATE``/``EHV`` pnode per
500 kV station — 38 of them inside the DOM zone alone, including every
substation PJM's own day-ahead binding-constraint record names in the hours
Dominion separates (PLEASANT VIEW, GOOSECRE, LOUDOUN, BRAMBLET, OX,
MORRISVILLE) as well as the southern and western Dominion stations (SURRY,
CARSON, CLOVER, CHICKAHOMINY, BATH COUNTY, YADKIN). Their day-ahead LMPs are
the direct measurement of how much price separation lives *inside* a model
zone, which is exactly what decides whether a zonal mechanism can reach it
(CLAUDE.md rule 14 `[R-ACCURATE]`: measure it, don't assume it).

Feed: ``da_hrl_lmps`` filtered ``type=EHV`` — **all zones in one pull, filtered
to the wanted zones locally**. DataMiner2 rejects the server-side ``zone``
filter on archived rows older than ~2 years with HTTP 400 (verified
2026-07-29: ``type=EHV&zone=DOM`` 400s for 2023-01-05 while ``type=EHV`` alone
serves the same day's 3,240 rows across 15 zones), the same restriction
`fetch_pjm_transmission.py` documents for ``pnode_name``. Pulling every zone is
also strictly more useful: it measures the intra-zonal spread of **all eight
model zones**, not just the chartered one. The published
``system_energy_price_da`` / ``congestion_price_da`` /
``marginal_loss_price_da`` components come through unchanged, so the same
MEC/MCC/MLC decomposition the zonal intake uses applies here.

One compressed Parquet per zone per calendar month is written to
``data/raw/pjm-ehv-lmp/`` (**gitignored** — same PJM DataMiner2 non-member
redistribution restriction as `pjm-zonal-lmp/`; see `docs/data-licensing.md` §4
and the directory README for the sha256 provenance manifest).

Usage
-----
    python scripts/data/fetch_pjm_ehv_lmp.py                    # all zones, 2023-2025
    python scripts/data/fetch_pjm_ehv_lmp.py --zones DOM AEP
    python scripts/data/fetch_pjm_ehv_lmp.py --manifest         # rewrite sha256 manifest
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

OUT_DIR = paths.RAW_DATA_DIR / "pjm-ehv-lmp"

TS_FIELD = "datetime_beginning_ept"

#: ``None`` keeps every zone the feed returns (~15). Narrow with ``--zones`` to
#: e.g. DOM (the chartered defect) and AEP (the other end of the boundary, so
#: the intra-zone spread compares like-for-like the way pjm-136 §3 did with
#: hubs); the filter is applied locally, after the pull.
DEFAULT_ZONES: tuple[str, ...] = ()

KEEP = (
    "datetime_beginning_utc",
    "datetime_beginning_ept",
    "pnode_id",
    "pnode_name",
    "voltage",
    "type",
    "zone",
)
FLOAT_COLS = (
    "system_energy_price_da",
    "total_lmp_da",
    "congestion_price_da",
    "marginal_loss_price_da",
)


def _date_filter(year: int, month: int, day_from: int, day_to: int) -> str:
    """EPT day-range filter string (ISO-8601, DataMiner2 convention)."""
    start = f"{year:04d}-{month:02d}-{day_from:02d}T00:00:00.0000000"
    end = f"{year:04d}-{month:02d}-{day_to:02d}T23:59:59.0000000"
    return f"{start} to {end}"


def _fetch_window(
    year: int, month: int, day_from: int, day_to: int, *, sleep_s: float
) -> pd.DataFrame:
    """Download every EHV-pnode row (all zones) for one day range."""
    # NB: no ``sort``/``order`` — the hrl_lmps feeds reject them with HTTP 400,
    # and no ``zone`` either: it 400s on archived rows (see the module
    # docstring), so zone selection happens locally in ``main``.
    params = {
        "isActiveMetadata": "true",
        "format": "csv",
        "type": "EHV",
        TS_FIELD: _date_filter(year, month, day_from, day_to),
    }
    rows = pjm_dataminer.fetch_feed(
        "da_hrl_lmps",
        params,
        user_agent="market-sim/fetch_pjm_ehv_lmp",
        sleep_s=sleep_s,
        verbose=False,
    )
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame = frame.sort_values([TS_FIELD, "pnode_name"]).reset_index(drop=True)
    return frame


def _fetch_month(year: int, month: int, *, sleep_s: float) -> pd.DataFrame:
    """Fetch one month (all zones), bisecting the window on DataMiner2's HTTP 400.

    Same gateway behaviour the zonal-LMP intake documents: some multi-day
    windows are rejected with 400 while each half of the same window serves
    fine, so the window is halved down to single days rather than changing
    retry policy for every other `fetch_pjm_*` consumer.
    """
    last_day = calendar.monthrange(year, month)[1]
    frames: list[pd.DataFrame] = []
    windows: list[tuple[int, int]] = [(1, last_day)]
    while windows:
        lo, hi = windows.pop(0)
        try:
            frames.append(_fetch_window(year, month, lo, hi, sleep_s=sleep_s))
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
    return out.sort_values([TS_FIELD, "pnode_name"]).reset_index(drop=True)


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
    ap.add_argument(
        "--zones",
        nargs="*",
        default=list(DEFAULT_ZONES),
        help="PJM zone codes to keep (filtered locally); empty keeps all",
    )
    ap.add_argument("--force", action="store_true", help="re-download existing files")
    ap.add_argument("--manifest", action="store_true", help="only rewrite SHA256SUMS")
    ap.add_argument("--sleep", type=float, default=0.6)
    args = ap.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.manifest:
        _write_manifest()
        return 0

    for year in args.years:
        for month in args.months:
            out = OUT_DIR / f"da_ehv_lmps_{year:04d}_{month:02d}.parquet"
            if out.exists() and not args.force:
                print(f"[skip] {out.name} exists")
                continue
            print(f"[EHV {year}-{month:02d}]", end=" ", flush=True)
            df = _fetch_month(year, month, sleep_s=args.sleep)
            if df.empty:
                print(f"\n  !! no rows for {year}-{month:02d}; not writing")
                continue
            if args.zones:
                df = df[df["zone"].isin(args.zones)]
            for col in FLOAT_COLS:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            keep = [c for c in (*KEEP, *FLOAT_COLS) if c in df.columns]
            df[keep].to_parquet(out, compression="zstd", index=False)
            hours = pd.to_datetime(df[TS_FIELD], format="mixed").nunique()
            expected = calendar.monthrange(year, month)[1] * 24
            flag = "" if hours >= expected else f"  << SHORT (expect {expected})"
            print(
                f"{len(df)} rows, {df['pnode_name'].nunique()} nodes, "
                f"{df['zone'].nunique()} zones, {hours} h{flag}",
                flush=True,
            )
    _write_manifest()
    return 0


if __name__ == "__main__":
    sys.exit(main())
