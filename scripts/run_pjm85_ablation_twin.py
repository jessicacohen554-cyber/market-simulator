"""Driver: D-3 zero-forcing ablation twin of the pjm-85 path-B candidate (rule 21).

The pjm-85 commitment-scoped-reserve recipe
(``run_pjm85_commitment_scoped_reserve._solve``) VERBATIM, solved with
``zero_forcing_ablation=True``: every merchant floor/bridge/drag neutralized via
``ScenarioConfig.as_zero_forcing_ablation`` (off-list from the D-2 mechanism
registry), keeping only the structural protected set (nuclear must-run, CHP
steam, coal take-or-pay). The commitment-scoped reserve mask itself is NOT a
floor (it removes idle capacity from the reserve RHS; it never forces energy)
and rides both runs identically, so the keeper-vs-twin per-class delta isolates
what the merchant floors/drag buy under the path-B reserve structure. No
parameter differs from the candidate config.

Run ONLY after the owner GO on the pjm-85 keeper decision (a twin is a
promotion requirement, not a probe requirement).
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

from scripts.run_calibration_full import report_run  # noqa: E402
from scripts.run_pjm85_commitment_scoped_reserve import _solve  # noqa: E402


def main() -> int:
    out_dir = Path("results/calibration/pjm85_commitment_scoped_reserve-ablation")
    run_dir = _solve(
        out_dir,
        zero_forcing_ablation=True,
        ablation_of="pjm85_commitment_scoped_reserve",
        note=(
            "D-3 zero-forcing ablation twin of pjm-85 (CLAUDE.md rule 21): the "
            "pjm85_commitment_scoped_reserve recipe verbatim with every "
            "merchant floor/bridge/drag neutralized (ScenarioConfig."
            "as_zero_forcing_ablation; off-list from the D-2 mechanism "
            "registry), structural protected set kept. The path-B reserve "
            "mask rides both runs (it is supply scoping, not forcing). "
            "Registered alongside the candidate for the keeper-vs-twin delta."
        ),
    )
    report_run(run_dir, band_width=0.10)
    print(f"DONE: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
