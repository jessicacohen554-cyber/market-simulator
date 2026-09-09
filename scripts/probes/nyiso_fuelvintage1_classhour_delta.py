"""Class-hour dispatch differencing between a replay bundle and a committed run.

Reports, per year: the max |class-hour delta| in MW, which classes moved, the
class-level ANNUAL energy delta (the quantity that separates a real dispatch
change from a within-budget hourly reshuffle), and any class present in one
bundle but not the other.

Charter task 3 asks for ``max |class-hour delta| = 0.000000 MW`` against the
committed keeper. G-DRIFT found that gate INVALID for this session's arm — two
LIVE hunks (the SPP-49 simple-cycle heat-rate floor and the F923 plausibility
screen) moved on ``main`` since the keeper solved, so a nonzero delta here is
not evidence about the retiree window. Task 3 is discharged instead by the
artifact-swap instrument (``nyiso_fuelvintage1_gate_t3.py``), which cancels both
by construction. This script MEASURES and ATTRIBUTES the residual difference.

Usage:
    uv run python scripts/probes/nyiso_fuelvintage1_classhour_delta.py \
        results/calibration/nyiso213_summer_seam results/nyiso_fuelvintage_A 2023 2024 2025
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

KEYS = ["year", "pass", "klass", "hour"]


def compare(ref: Path, arm: Path, year: int) -> None:
    """Print the class-hour and class-annual differences for one year.

    Args:
        ref: Committed reference bundle dir.
        arm: Replay bundle dir to difference against it.
        year: Solve year.
    """
    a = pd.read_parquet(ref / "hourly" / f"class_hourly_{year}.parquet")
    b = pd.read_parquet(arm / "hourly" / f"class_hourly_{year}.parquet")
    for df in (a, b):
        for k in ("pass", "klass"):
            df[k] = df[k].astype(str)
    m = a.merge(b, on=KEYS, suffixes=("_ref", "_arm"), how="outer", indicator=True)
    d = (m["mw_arm"].fillna(0) - m["mw_ref"].fillna(0)).abs()
    moved = m.loc[d > 1e-6]
    print(f"\n=== {year} :: {ref.name}  ->  {arm.name}")
    print(f"  max |class-hour delta| = {d.max():.6f} MW")
    print(
        f"  cells: ref {len(a)}  arm {len(b)}  "
        f"moved {len(moved)} ({100 * len(moved) / max(len(m), 1):.4f}% of {len(m)})"
    )
    only = set(b["klass"]) - set(a["klass"])
    for k in sorted(only):
        s = b.loc[b["klass"] == k, "mw"]
        print(f"  CLASS ONLY IN ARM: {k} — mean {s.mean():.4f} MW, max {s.max():.4f} MW")
    ea = a.groupby("klass")["mw"].sum() / 1e6
    eb = b.groupby("klass")["mw"].sum() / 1e6
    j = pd.concat([ea.rename("ref_TWh"), eb.rename("arm_TWh")], axis=1).fillna(0.0)
    j["delta_TWh"] = j["arm_TWh"] - j["ref_TWh"]
    j = j.reindex(j["delta_TWh"].abs().sort_values(ascending=False).index)
    print("  class ANNUAL energy (TWh):")
    print("   " + j.round(4).to_string().replace("\n", "\n   "))
    print(
        f"  SYSTEM total: ref {ea.sum():.4f} -> arm {eb.sum():.4f} TWh "
        f"(delta {eb.sum() - ea.sum():+.6f})"
    )


def main() -> None:
    """CLI entry point."""
    ref, arm = Path(sys.argv[1]), Path(sys.argv[2])
    for y in (int(x) for x in sys.argv[3:]):
        compare(ref, arm, y)


if __name__ == "__main__":
    main()
