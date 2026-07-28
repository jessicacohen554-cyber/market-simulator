"""caiso-133 — byte-identity gate for the two new write-only sidecars.

The caiso-133 sidecars (``hourly/unit_hourly_<y>.parquet`` and
``hourly/network_<y>.parquet``) are added to the solve writer, and the network
one needs the LP module to hand back two things it did not previously expose:
the aggregate-interface row block's offset and the flow columns' reduced costs.
Both are *reporting* outputs — no row, bound or coefficient moves — but that is
a claim about code, and CLAUDE.md rule 1 ``[R-STRUCT]`` wants it measured.

This compares a replay of the committed keeper AT THIS SESSION'S HEAD against
the keeper's own committed sidecars, on the two series every scored metric is
built from: the per-class hourly dispatch (``class_hourly_<y>.parquet``) and
the per-zone hourly price/demand/slack/dump (``system_<y>.parquet``). Any
difference at all — not a tolerance, an exact ``max |delta|`` — means the new
code touched the LP.

Usage::

    PYTHONPATH=.:src .venv/bin/python \\
        scripts/probes/_caiso133_sidecar_invariance.py \\
        --keeper results/calibration/caiso130_nameplate_B \\
        --arm results/calibration/caiso133_sidecar_A
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# Every column the two committed sidecars carry that a scored metric reads.
CLASS_COLS = ("mw",)
SYSTEM_COLS = ("price", "slack", "dump", "demand", "reserve_price")


def _aligned(a: Path, b: Path, keys: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read two sidecars and align them on ``keys`` so a delta is well-defined."""
    da = pd.read_parquet(a).sort_values(keys).reset_index(drop=True)
    db = pd.read_parquet(b).sort_values(keys).reset_index(drop=True)
    return da, db


def compare(keeper: Path, arm: Path, years: tuple[int, ...]) -> int:
    worst = 0.0
    failures = 0
    for year in years:
        for name, keys, cols in (
            ("class_hourly", ["pass", "klass", "hour"], CLASS_COLS),
            ("system", ["pass", "zone", "hour"], SYSTEM_COLS),
        ):
            pa = keeper / "hourly" / f"{name}_{year}.parquet"
            pb = arm / "hourly" / f"{name}_{year}.parquet"
            if not pa.exists() or not pb.exists():
                print(f"  {year} {name:<12} MISSING ({pa.exists()}/{pb.exists()})")
                failures += 1
                continue
            da, db = _aligned(pa, pb, keys)
            if len(da) != len(db):
                print(f"  {year} {name:<12} ROW COUNT {len(da)} != {len(db)}")
                failures += 1
                continue
            if not da[keys].equals(db[keys]):
                print(f"  {year} {name:<12} KEY MISMATCH")
                failures += 1
                continue
            for col in cols:
                if col not in da.columns:
                    continue
                d = float(
                    np.nanmax(
                        np.abs(
                            da[col].to_numpy(dtype=float)
                            - db[col].to_numpy(dtype=float)
                        )
                    )
                )
                worst = max(worst, d)
                flag = "OK" if d == 0.0 else "DIFFERS"
                print(f"  {year} {name:<12} {col:<14} max|delta| = {d:.10g}   {flag}")
                if d != 0.0:
                    failures += 1
    print(
        f"\n  >>> worst max|delta| across every series and year: {worst:.10g}\n"
        f"  >>> {'BYTE-IDENTICAL — the sidecar wiring is solve-invariant' if not failures else f'{failures} MISMATCH(ES) — the wiring TOUCHED the LP'}"
    )
    return 0 if failures == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keeper", type=Path, required=True)
    ap.add_argument("--arm", type=Path, required=True)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()
    print("caiso-133 — sidecar solve-invariance: replay vs the committed keeper")
    print(f"  keeper: {args.keeper}\n  arm:    {args.arm}\n")
    return compare(args.keeper, args.arm, tuple(int(y) for y in args.years))


if __name__ == "__main__":
    raise SystemExit(main())
