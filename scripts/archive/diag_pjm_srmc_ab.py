"""G-21 A/B decomposition: pjm-78 (baseline) vs pjm-79 (SRMC re-grounded).

Reads the two bundles' `dispatch/<year>_P1.parquet` plus the committed EIA-923
class benchmarks (`frontend/data/backcast/bench/PJM/<year>.json.gz` classFull)
and prints, per year:

* per-class annual energy — baseline / re-grounded / actual, with deltas, so
  the classes that absorb the de-flooded ST_GAS / CT_INTERMEDIATE energy are
  attributable (the "what were the sub-SRMC offers compensating for"
  decomposition of the G-21 cycle);
* ST_GAS hour-of-day profile correlation vs the bench plant actuals (does the
  re-grounded steam fleet keep the right diurnal shape at the lower volume);
* generation-weighted mean LMP and the >$200/MWh tail-hour count from the
  dispatch frame's dual column (price-level cost of removing the sub-SRMC
  floor supply);
* CT_PEAKER totals + the drag share denominator effect for the C8 memo
  (docs/handoffs/pjm-c8-drag-memo-2026-07.md §6 sequencing).

Pure reader — no solve, no writes. Rule-15 evidence artifact for the cycle's
calibration-log entry.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
BASE = REPO / "results/calibration/pjm78_srmc_baseline"
REGROUND = REPO / "results/calibration/pjm79_srmc_reground"
BENCH = REPO / "frontend/data/backcast/bench/PJM"
YEARS = (2023, 2024, 2025)
GAS_CLASSES = (
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_INTERMEDIATE",
    "CT_CHP",
    "ST_GAS",
    "ST_CHP",
)


def class_twh(bundle: Path, year: int) -> pd.Series:
    """Model annual TWh by class from the P1 dispatch frame."""
    df = pd.read_parquet(
        bundle / "dispatch" / f"{year}_P1.parquet", columns=["klass", "mw"]
    )
    return df.groupby("klass", observed=True)["mw"].sum() / 1e6


def bench_class(year: int) -> tuple[dict, dict]:
    """(classFull annual TWh, per-plant hourly records) from the bench file."""
    with gzip.open(BENCH / f"{year}.json.gz") as fh:
        b = json.load(fh)["bench"]
    return b.get("classFull", {}), b.get("plants", {})


def hod_profile(bundle: Path, year: int, klass: str) -> np.ndarray:
    """Mean hour-of-day MW profile (24,) for one class."""
    df = pd.read_parquet(
        bundle / "dispatch" / f"{year}_P1.parquet", columns=["klass", "hour", "mw"]
    )
    df = df[df["klass"] == klass]
    mw = df.groupby(df["hour"] % 24, observed=True)["mw"].sum()
    return mw.reindex(range(24), fill_value=0.0).to_numpy()


def actual_hod(plants: dict, klass: str) -> np.ndarray:
    """Measured hour-of-day MW profile (24,) for one class from bench plants."""
    tot = np.zeros(8760)
    for rec in plants.values():
        if isinstance(rec, dict) and rec.get("group") == klass:
            mw = np.asarray(rec.get("mw", []), dtype=float)
            tot[: mw.size] += mw[:8760]
    return tot.reshape(-1, 24).mean(axis=0)


def price_stats(bundle: Path, year: int) -> tuple[float, int]:
    """(gen-weighted mean LMP, count of unit-zone-hours' zone-hours > $200)."""
    df = pd.read_parquet(
        bundle / "dispatch" / f"{year}_P1.parquet",
        columns=["zone", "hour", "mw", "lmp"],
    )
    wmean = float((df["mw"] * df["lmp"]).sum() / max(df["mw"].sum(), 1e-9))
    zh = df.groupby(["zone", "hour"], observed=True)["lmp"].first()
    tail = int((zh > 200.0).sum())
    return wmean, tail


def main() -> int:
    for bundle in (BASE, REGROUND):
        if not (bundle / "dispatch").exists():
            print(f"missing bundle: {bundle}", file=sys.stderr)
            return 1
    for year in YEARS:
        cf, plants = bench_class(year)
        a = class_twh(BASE, year)
        b = class_twh(REGROUND, year)
        print(f"\n=== PJM {year}: class TWh — baseline(78) / reground(79) / actual ===")
        print(
            f"{'class':<16} {'pjm78':>8} {'pjm79':>8} {'delta':>8} {'actual':>8} "
            f"{'78-act':>8} {'79-act':>8}"
        )
        keys = sorted(set(a.index) | set(b.index), key=str)
        for k in keys:
            va, vb = float(a.get(k, 0.0)), float(b.get(k, 0.0))
            act = cf.get(str(k))
            if abs(va) < 0.005 and abs(vb) < 0.005:
                continue
            act_s = f"{act:8.2f}" if isinstance(act, (int, float)) else "       —"
            d78 = f"{va - act:8.2f}" if isinstance(act, (int, float)) else "       —"
            d79 = f"{vb - act:8.2f}" if isinstance(act, (int, float)) else "       —"
            print(
                f"{str(k):<16} {va:8.2f} {vb:8.2f} {vb - va:+8.2f} {act_s} {d78} {d79}"
            )

        st_act = actual_hod(plants, "ST_GAS")
        for label, bundle in (("pjm78", BASE), ("pjm79", REGROUND)):
            prof = hod_profile(bundle, year, "ST_GAS")
            if st_act.std() > 0 and prof.std() > 0:
                r = float(np.corrcoef(prof, st_act)[0, 1])
                print(f"ST_GAS HOD profile r vs actual ({label}): {r:.3f}")

        for label, bundle in (("pjm78", BASE), ("pjm79", REGROUND)):
            wmean, tail = price_stats(bundle, year)
            print(
                f"{label}: gen-wtd mean LMP ${wmean:.2f}/MWh; zone-hours >$200: {tail}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
