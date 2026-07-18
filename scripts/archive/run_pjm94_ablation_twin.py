"""Driver: D-3 zero-forcing ablation twin of the pjm-94 keeper candidate (rule 20).

The pjm-94 recipe (``run_pjm94_stgas_netload_drag._solve`` — pjm-90 verbatim plus
the all-hours ST_GAS net-load reliability drag) solved with
``zero_forcing_ablation=True``: every merchant floor/bridge/drag neutralized via
``ScenarioConfig.as_zero_forcing_ablation`` (off-list from the D-2 mechanism
registry, which now includes the ST_GAS net-load drag → gas_st_netload_drag=False),
keeping only the structural protected set (nuclear must-run, CHP steam-following,
coal take-or-pay). The keeper-vs-twin per-class delta quantifies what the ST_GAS
net-load drag + CT net-load drag buy. No parameter differs from the keeper config
— the transform is applied inside solve_and_persist.

Run with MALLOC_ARENA_MAX=2 (one process, ~13 GB peak; without it the 2nd year
OOMs on a 15 GB host).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

from scripts.run_calibration_full import report_run  # noqa: E402
from scripts.archive.run_pjm94_stgas_netload_drag import _solve  # noqa: E402

NOTE = (
    "D-3 zero-forcing ablation twin of pjm-94 (CLAUDE.md rule 20): the "
    "pjm94_stgas_netload_drag recipe verbatim with every merchant floor/"
    "bridge/drag neutralized (ScenarioConfig.as_zero_forcing_ablation; "
    "off-list from the D-2 mechanism registry incl. gas_st_netload_drag), "
    "structural protected set kept. Registered alongside the keeper "
    "candidate for the E9 keeper-vs-twin delta — quantifies what the "
    "all-hours ST_GAS net-load drag + CT net-load drag buy per class."
)


def main() -> int:
    """Solve the pjm-94 zero-forcing ablation twin (year-by-year, rule 16)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("results/calibration/pjm94_stgas_netload_drag-ablation"),
    )
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    if not args.report_only:
        _solve(
            args.years,
            args.out_dir,
            zero_forcing_ablation=True,
            ablation_of="pjm94_stgas_netload_drag",
            note=NOTE,
        )
    report_run(args.out_dir, band_width=0.10)
    print(f"DONE: {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
