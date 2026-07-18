#!/usr/bin/env python
"""One-off (P-3A wrap-up): synthesize full_horizon_summary.json for the ISO runs
that were stopped mid-horizon, by scoring the I1-I14 invariants and extracting
the trajectory over whatever years are already cached on disk. Reuses the exact
functions run_full_horizon.py calls post-solve, so the partial summaries are
byte-compatible with collate_full_horizon.py. Timing (per_year_perf) is left
empty for partials — it was never recorded (the run didn't finish); feasibility
data comes from the ISOs that completed (CAISO/NEISO).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts import check_forecast_invariants as C  # noqa: E402
from scripts.run_full_horizon import extract_trajectory  # noqa: E402

PARTIALS = {
    "PJM": "results/full-horizon/pjm",
    "ERCOT": "results/full-horizon/ercot",
    "NYISO": "results/full-horizon/nyiso",
}


def main() -> int:
    for iso, out in PARTIALS.items():
        out_dir = Path(out)
        run_dirs = [p for p in (out_dir / iso).glob("*") if p.is_dir()]
        if not run_dirs:
            print(f"{iso}: no run dir under {out_dir}/{iso}; skip")
            continue
        run_dir = max(run_dirs, key=lambda p: len(list(p.glob("year_*.parquet"))))
        run = C.load_run(run_dir)
        solved = run.solved_years
        if not solved:
            print(f"{iso}: no solved years cached; skip")
            continue
        invariants = [
            {"id": r.ident, "name": r.name, "status": r.status, "detail": r.detail}
            for r in C.run_single(run_dir)
        ]
        trajectory = extract_trajectory(run)
        summary = {
            "iso": iso,
            "start_year": min(solved),
            "end_year": 2050,
            "capacity_market_clearing": False,
            "cache_key": run_dir.name,
            "run_dir": str(run_dir),
            "error": None,
            "partial": True,
            "partial_note": (
                f"Run STOPPED mid-horizon at user request; scored over the "
                f"{len(solved)} cached years {min(solved)}-{max(solved)} of 25. "
                f"Timing not captured (per_year_perf empty)."
            ),
            "total_wall_s": 0.0,
            "global_peak_rss_mb": 0.0,
            "n_solved_years": len(solved),
            "solved_years": solved,
            "per_year_perf": [],
            "invariants": invariants,
            "trajectory": trajectory,
        }
        (out_dir / "full_horizon_summary.json").write_text(
            json.dumps(summary, indent=2) + "\n"
        )
        nf = sum(1 for i in invariants if i["status"] == "FAIL")
        nw = sum(1 for i in invariants if i["status"] == "WARN")
        print(
            f"{iso}: wrote partial summary — {len(solved)} yrs "
            f"({min(solved)}-{max(solved)}), {nf} FAIL, {nw} WARN"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
