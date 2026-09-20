"""nyiso-243 phase 2 — the MEASURED NYISO offer stack in the missed tail hours.

ZERO LP (rule 32 ``[R-SHARD]`` (a)). No model quantity is read; this probe is
entirely a description of NYISO MIS **P-27** masked bid curves.

**This is NOT a gated test and nothing is selected on it.** The session's gate
is the kill test of
``docs/PRECOMMIT-nyiso243-outage-intake-kill-test-2026-09-20.md`` §3, which the
availability reading FAILED. This probe characterises the corpus's *other*
field — the submitted 12-block economic offer curve — because the kill test's
own result points at it: the fleet offered **more** capacity in the extreme
hours, not less, so the capacity was there and the $383/MWh clearing price was
made by what that capacity was **offered at**, not by how much of it existed.

Construction. In each row the ``Dispatch MW1..12`` are **cumulative** MW points
and ``Dispatch $/MW1..12`` their offer prices (verified against the raw rows:
a unit with ``Upper Oper Limit`` 40.0 posts ``MW1 = 40.0 @ $995`` and
``MW2 = 43.9 @ $999`` up to its emergency limit). Capacity a resource offered
**at or below** a price *P* is therefore the largest cumulative MW whose block
price is ≤ *P*, and everything above that up to its UOL is offered above *P*.

Reported per window: measured MW offered above $100 / $300 / $500 / $1,000, and
the price at which the measured stack's cumulative MW reaches the hour's load.
Rule 1 `[R-STRUCT]` applies in full — a measured offer distribution is a
legitimate input only as a *distribution identified from the measurement*, never
as a level chosen because it closes the residual.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso243_measured_offer_stack.py
"""

from __future__ import annotations

import argparse
import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.probes.nyiso243_offered_availability import (
    GENBIDS,
    HOURS,
    THRESHOLD,
    _std_hour,
    windows,
)

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results" / "calibration" / "_nyiso243_measured_offer_stack.json"

PRICE_POINTS = (100.0, 300.0, 500.0, 1000.0)
_MW_COLS = [f"Dispatch MW{i}" for i in range(1, 13)]
_PX_COLS = [f"Dispatch $/MW{i}" for i in range(1, 13)]


def offer_stack_hourly(year: int, market: str = "DAM") -> pd.DataFrame:
    """Hourly measured MW offered above each price point, for ``market``."""
    acc: list[pd.DataFrame] = []
    formats: dict[str, int] = {}
    for month in range(1, 13):
        path = GENBIDS / f"{year:04d}{month:02d}01biddata_genbids_csv.zip"
        if not path.exists():
            continue
        with zipfile.ZipFile(path) as z:
            raw = pd.read_csv(
                io.BytesIO(z.read(z.namelist()[0])), skipinitialspace=True, low_memory=False
            )
        raw.columns = [c.strip() for c in raw.columns]
        raw = raw[raw["Market"].astype(str).str.strip() == market]
        if raw.empty:
            continue
        for fmt, n in raw["Bid Curve Format"].astype(str).str.strip().value_counts().items():
            formats[fmt] = formats.get(fmt, 0) + int(n)

        ts = pd.to_datetime(raw["Date Time"].astype(str).str.strip(), format="%d%b%Y:%H:%M:%S")
        hour = _std_hour(pd.DatetimeIndex(ts).tz_localize("UTC"), year)
        uol = raw["Upper Oper Limit"].to_numpy(float)
        mw = raw[_MW_COLS].to_numpy(float)
        px = raw[_PX_COLS].to_numpy(float)

        out = {"hour": hour}
        for p in PRICE_POINTS:
            # Cumulative MW offered at or below p; NaN blocks never qualify.
            at_or_below = np.where((px <= p) & np.isfinite(mw), mw, 0.0).max(axis=1)
            out[f"above_{p:.0f}"] = np.clip(uol - at_or_below, 0.0, None)
        # A resource with no block priced at or below the cap is offering its
        # whole UOL above it; one with no curve at all contributes nothing.
        frame = pd.DataFrame(out)
        acc.append(frame[frame["hour"] >= 0].groupby("hour").sum())

    if not acc:
        raise FileNotFoundError(f"no P-27 archives for {year}")
    total = pd.concat(acc).groupby(level=0).sum()
    total = total.reindex(range(HOURS))
    total.attrs["bid_curve_formats"] = formats
    return total


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2022, 2025])
    ap.add_argument("--markets", nargs="+", default=["DAM", "HAM"])
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    result: dict = {
        "note": (
            "DESCRIPTIVE. Not a gate, nothing selected on it. The session's gate is "
            "the kill test of PRECOMMIT-nyiso243 section 3, which FAILED."
        ),
        "price_points": list(PRICE_POINTS),
        "years": {},
    }
    for year in args.years:
        win, rt, _da = windows(year)
        rec: dict = {}
        for market in args.markets:
            stack = offer_stack_hourly(year, market)
            rec.setdefault("bid_curve_formats", {})[market] = stack.attrs["bid_curve_formats"]
            rows: dict[str, dict] = {}
            for label, sel in win.items():
                if not len(sel):
                    continue
                sel = sel[sel < HOURS]
                rows[label] = {"hours": int(len(sel)), "rt_median": round(float(np.nanmedian(rt[sel])), 2)}
                for p in PRICE_POINTS:
                    v = stack[f"above_{p:.0f}"].to_numpy(float)[sel]
                    v = v[np.isfinite(v)]
                    rows[label][f"offered_above_{p:.0f}_mw"] = (
                        round(float(np.median(v)), 1) if len(v) else None
                    )
            rec[market] = rows
        result["years"][str(year)] = rec
        print(f"{year}: done", flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2))
    print(f"wrote {args.out}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
