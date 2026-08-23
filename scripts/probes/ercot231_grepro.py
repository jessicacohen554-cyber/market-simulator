#!/usr/bin/env python3
"""ercot-231 G-REPRO: numeric identity of a replayed bundle vs the keeper.

Compares every numeric column of every 2023 hourly sidecar in the replay
bundle against the keeper's committed sidecars, reporting max|Δ| per column
(the ercot-230 form: sha is unusable cross-environment; numeric identity is
the gate). Usage:

    python scripts/probes/ercot231_grepro.py <replay_bundle> [<keeper_bundle>]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/ercot223_release_arm"
YEAR = 2023


def compare(replay: Path, keeper: Path = KEEPER) -> bool:
    """Print per-column max|Δ| for every 2023 sidecar; return overall pass."""
    ok = True
    names = sorted(
        p.name for p in (keeper / "hourly").glob(f"*_{YEAR}.parquet")
    )
    for name in names:
        kp, rp = keeper / "hourly" / name, replay / "hourly" / name
        if not rp.exists():
            print(f"{name}: MISSING in replay")
            ok = False
            continue
        k, r = pd.read_parquet(kp), pd.read_parquet(rp)
        if len(k) != len(r):
            print(f"{name}: row count {len(k)} vs {len(r)}")
            ok = False
            continue
        worst = 0.0
        worst_col = ""
        for col in k.columns:
            if not np.issubdtype(k[col].dtype, np.number):
                if not (k[col].astype(str).to_numpy() == r[col].astype(str).to_numpy()).all():
                    print(f"{name}.{col}: non-numeric mismatch")
                    ok = False
                continue
            d = float(
                np.nanmax(
                    np.abs(k[col].to_numpy(float) - r[col].to_numpy(float))
                )
                if len(k)
                else 0.0
            )
            if d > worst:
                worst, worst_col = d, col
        print(f"{name}: max|Δ| = {worst:.6g}" + (f" ({worst_col})" if worst else ""))
        if worst != 0.0:
            ok = False
    print("G-REPRO", "PASS (numeric identity)" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    replay = Path(sys.argv[1])
    keeper = Path(sys.argv[2]) if len(sys.argv) > 2 else KEEPER
    sys.exit(0 if compare(replay, keeper) else 1)
