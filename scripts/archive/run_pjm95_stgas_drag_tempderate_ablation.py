"""Driver: D-3 zero-forcing ablation twin of the pjm-95 keeper candidate (rule 20).

The pjm-95 recipe (pjm-94's ``_solve`` — pjm-90 verbatim + the all-hours ST_GAS
net-load reliability drag + ``temp_dependent_derate=True``) solved with
``zero_forcing_ablation=True``: every merchant floor/bridge/drag neutralized via
``ScenarioConfig.as_zero_forcing_ablation`` (off-list from the D-2 mechanism
registry, which includes the ST_GAS net-load drag -> gas_st_netload_drag=False),
keeping only the structural protected set (nuclear must-run, CHP steam-
following, coal take-or-pay). ``temp_dependent_derate`` stays on (it is a
capacity/availability reshape, not a forcing floor, so it is not in the D-2
mechanism registry and is unaffected by the ablation transform). The
keeper-vs-twin per-class delta quantifies what the ST_GAS net-load drag + CT
net-load drag buy on top of the temp-derated capacity envelope. No parameter
differs from pjm-95 itself — the transform is applied inside
``solve_and_persist``. Mirrors ``scripts/archive/run_pjm94_ablation_twin.py``.

Run with MALLOC_ARENA_MAX=2 (one process, ~13 GB peak; without it the 2nd year
OOMs on a 15 GB host) -- solve ONE year per process into the SAME --out-dir,
then --report-only.
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
    "D-3 zero-forcing ablation twin of pjm-95 (CLAUDE.md rule 20): the "
    "pjm95_stgas_drag_tempderate recipe verbatim (pjm-94 + "
    "temp_dependent_derate=True) with every merchant floor/bridge/drag "
    "neutralized (ScenarioConfig.as_zero_forcing_ablation; off-list from the "
    "D-2 mechanism registry incl. gas_st_netload_drag), structural protected "
    "set kept. temp_dependent_derate itself is not a forcing floor (a "
    "capacity/availability reshape) so it stays on unchanged. Registered "
    "alongside the pjm-95 keeper candidate for the E9 keeper-vs-twin delta -- "
    "quantifies what the all-hours ST_GAS net-load drag + CT net-load drag "
    "buy on top of the temp-derated capacity envelope."
)


def main() -> int:
    """Solve the pjm-95 zero-forcing ablation twin (year-by-year, rule 16)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("results/calibration/pjm95_stgas_drag_tempderate-ablation"),
    )
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    if not args.report_only:
        _solve(
            args.years,
            args.out_dir,
            zero_forcing_ablation=True,
            ablation_of="pjm95_stgas_drag_tempderate",
            temp_dependent_derate=True,
            note=NOTE,
        )
    report_run(args.out_dir, band_width=0.10)
    print(f"DONE: {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
