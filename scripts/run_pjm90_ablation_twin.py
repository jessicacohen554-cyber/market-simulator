"""Driver: D-3 zero-forcing ablation twin of the pjm-90 keeper candidate (rule 21).

The pjm-90 recipe (``run_pjm90_cchp_srmc._solve`` — pjm-89 steam-gas drag + CHP
HR + outage capture, plus the CC_CHP SRMC re-grounding) VERBATIM, solved with
``zero_forcing_ablation=True``: every merchant floor/bridge/drag neutralized via
``ScenarioConfig.as_zero_forcing_ablation`` (off-list from the D-2 mechanism
registry), keeping only the structural protected set (nuclear must-run, CHP
steam-following, coal take-or-pay). The keeper-vs-twin per-class delta quantifies
what the ST_GAS overnight drag + CT net-load drag buy. No parameter differs from
the keeper config — the transform is applied inside solve_and_persist.

Run with MALLOC_ARENA_MAX=2 (one process, ~13 GB peak; without it the 2nd year
OOMs on a 15 GB host).
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

from scripts.run_calibration_full import report_run  # noqa: E402
from scripts.run_pjm90_cchp_srmc import _solve  # noqa: E402


def main() -> int:
    """Solve the pjm-90 zero-forcing ablation twin over 2023-2025."""
    out_dir = Path("results/calibration/pjm90_cchp_srmc-ablation")
    run_dir = _solve(
        [2023, 2024, 2025],
        out_dir,
        zero_forcing_ablation=True,
        ablation_of="pjm90_cchp_srmc",
        note=(
            "D-3 zero-forcing ablation twin of pjm-90 (CLAUDE.md rule 21): the "
            "pjm90_cchp_srmc recipe verbatim with every merchant floor/bridge/"
            "drag neutralized (ScenarioConfig.as_zero_forcing_ablation; off-list "
            "from the D-2 mechanism registry), structural protected set kept. "
            "Registered alongside the keeper candidate for the E9 keeper-vs-twin "
            "delta — quantifies what the ST_GAS overnight drag + CT net-load drag "
            "buy per class."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
