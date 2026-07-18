"""G-21 diagnostic: single-year 2024 replay of the pjm-97 keeper config.

Throwaway probe (rule 16 — never registered) to regenerate the dispatch
parquets (dispatch/2024_P1.parquet, flows.parquet, floors/) that the slim
committed bundle lacks, so the CC_REGULAR over-run / price-level-gap audit
(G-20 technique: zone x class vs CAMPD/EIA-923) can run against the KEEPER
dispatch. Config is the keeper's meta.json byte-faithful, years=[2024] only.
Idempotent: skips if the parquet already exists; /dev/shm mkdir lock guards
against concurrent duplicate solves (12 GB LP, OOM risk).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "scripts"))
sys.path.insert(0, str(_REPO))

LOCK = Path("/dev/shm/g21_keeper2024.lock")
OUT = _REPO / "results" / "calibration" / "pjm_g21_keeper2024_diag"


def main() -> int:
    if (OUT / "dispatch" / "2024_P1.parquet").exists():
        print("already solved; skipping")
        return 0
    try:
        LOCK.mkdir()
    except FileExistsError:
        print("lock held; another solve is running — exiting")
        return 0
    try:
        from scripts.replay_keeper import build_kwargs
        from scripts.run_calibration_full import _load_reference, solve_and_persist

        keeper = _REPO / "results" / "calibration" / "pjm97_measured_interfaces"
        meta = json.loads((keeper / "meta.json").read_text())
        kwargs = build_kwargs(meta)
        kwargs["years"] = [2024]
        kwargs["iso"] = "PJM"
        kwargs["hours"] = 8760
        kwargs["reference"] = _load_reference()
        kwargs["run_dir"] = OUT
        kwargs["note"] = (
            "G-21 THROWAWAY DIAGNOSTIC (rule 16, never registered): 2024-only "
            "byte-faithful replay of the pjm-97 keeper to regenerate dispatch "
            "parquets for the CC over-run / price-gap audit."
        )
        run_dir = solve_and_persist(**kwargs)
        print(f"solved into {run_dir}")
        return 0
    finally:
        LOCK.rmdir()


if __name__ == "__main__":
    os.environ.setdefault("MALLOC_ARENA_MAX", "2")
    sys.exit(main())
