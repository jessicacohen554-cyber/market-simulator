"""caiso-204 Phase-0: fetch the pre-registered PUB_BID_DAM subset.

Day-selection rule pinned in
``results/calibration/PRECHECK-caiso204-adaptive-phase0-2026-08-19.md`` §2:
per year 2023-2025, the union of (a) every 6th day of year (1-based doy = 1
mod 6) and (b) each measured $200 event day and the 21 days after it, minus
the known OASIS archive hole 2023-06-01. The event days come from the
committed ``actual_lmp_hourly_CAISO.parquet`` (rt, nan-aware daily maxima) --
identification-driver evidence, never a model quantity. 585 trade dates.

Reuses the committed fetcher's machinery (`_fetch_day`, 6 s spacing,
rate-limit detection) unchanged; skips already-present valid zips.
"""

from __future__ import annotations

import datetime as dt
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from scripts.data.fetch_caiso_public_bids import (  # noqa: E402
    DEFAULT_SLEEP_S,
    RAW_DIR,
    _fetch_day,
    _out_path,
)

LMP_PARQUET = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_CAISO.parquet"
EVENT_USD = 200.0  # PRECHECK §1: CAISO's own scarcity-tail threshold
POST_EVENT_DAYS = 21  # PRECHECK §2: dense decay sampling
HOLE = dt.date(2023, 6, 1)  # known OASIS archive hole (caiso-178 §1)


def selected_days() -> list[dt.date]:
    """The pre-registered 585-date selection, deterministically."""
    df = pd.read_parquet(LMP_PARQUET)
    out: list[dt.date] = []
    for yr in (2023, 2024, 2025):
        rt = df.loc[df["year"] == yr, "rt"].to_numpy(dtype=float)
        n = rt.size // 24
        body = np.where(np.isnan(rt[: n * 24]), -np.inf, rt[: n * 24])
        day_max = body.reshape(n, 24).max(axis=1)
        events = np.flatnonzero(day_max >= EVENT_USD)
        keep: set[int] = set(range(0, n, 6))  # doy = 1 mod 6, 1-based
        for e in events:
            keep |= set(range(int(e), min(int(e) + POST_EVENT_DAYS + 1, n)))
        base = dt.date(yr, 1, 1)
        out.extend(base + dt.timedelta(days=int(d)) for d in sorted(keep))
    return [d for d in out if d != HOLE]


def main() -> int:
    days = selected_days()
    print(f"caiso-204 subset: {len(days)} trade dates", flush=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    fetched = skipped = holes = 0
    for day in days:
        out = _out_path(day)
        if out.exists() and out.stat().st_size > 10_000:
            skipped += 1
            continue
        body = _fetch_day(day)
        if body is None:
            holes += 1
        else:
            out.write_bytes(body)
            fetched += 1
            if fetched % 25 == 0:
                print(f"  progress: {fetched} fetched / {skipped} present / {holes} holes", flush=True)
        time.sleep(DEFAULT_SLEEP_S)
    print(f"DONE: {fetched} fetched, {skipped} already present, {holes} archive holes", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
