"""Driver: D-3 zero-forcing ablation twin of the pjm-80 keeper candidate (rule 25).

The pjm-80 G-21 re-grounding recipe (``run_pjm80_srmc_reground_keeper._solve``)
VERBATIM, solved with ``zero_forcing_ablation=True``: every merchant
floor/bridge/drag neutralized via ``ScenarioConfig.as_zero_forcing_ablation``
(off-list from the D-2 mechanism registry), keeping only the structural
protected set (nuclear must-run, CHP steam, coal take-or-pay). The keeper-vs-twin
per-class delta quantifies what the CT net-load drag buys once the sub-SRMC
ST_GAS flood is removed. No parameter differs from the keeper config — the
transform is applied inside ``run_year``/``solve_and_persist``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

from scripts.run_calibration_full import report_run  # noqa: E402
from scripts.archive.run_pjm80_srmc_reground_keeper import _solve  # noqa: E402


def main() -> int:
    out_dir = Path("results/calibration/pjm80_srmc_reground_keeper-ablation")
    run_dir = _solve(
        out_dir,
        zero_forcing_ablation=True,
        ablation_of="pjm80_srmc_reground_keeper",
        note=(
            "D-3 zero-forcing ablation twin of pjm-80 (CLAUDE.md rule 25): the "
            "pjm80_srmc_reground_keeper recipe verbatim with every merchant "
            "floor/bridge/drag neutralized (ScenarioConfig."
            "as_zero_forcing_ablation; off-list from the D-2 mechanism "
            "registry), structural protected set kept. Registered alongside "
            "the keeper for the E9 keeper-vs-twin delta."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
