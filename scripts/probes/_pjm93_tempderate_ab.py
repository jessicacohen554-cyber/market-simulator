"""Full-keeper A/B probe: PJM temperature-dependent derate (pjm-93).

Reproduces the pjm90_cchp_srmc keeper's exact configuration -- by calling its
own driver's ``_solve`` helper (``scripts/run_pjm90_cchp_srmc.py``) directly,
not by re-typing its kwargs from the curated ``calibration_flags`` subset --
across all three train years (2023-2025, rule 16) and adds only
``temp_dependent_derate=True``. Reusing the keeper's own ``_solve`` guarantees
byte-identical reproduction of every flag (including ones not surfaced in
calibration_flags, e.g. ``curve_smoothing``, ``ct_drag_overrides``,
``pjm_reserve_supply_cap``).

Single-year validation (_pjm_tempderate_ab.py, 2025 only) showed hoursGt200
0->4 (actual 51) -- directionally real but small. This is the full-keeper
rerun across all three years plus its rule-20 zero-forcing ablation twin.
Registered as PROBES only (never touches keepers.json) per
docs/handoffs/temp-derate-keeper-rerun-playbook-2026-07.md.

Usage: python scripts/probes/_pjm93_tempderate_ab.py {main|ablation}
"""

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "scripts"))

from scripts.run_pjm90_cchp_srmc import _solve  # noqa: E402

ROOT = _REPO / "results" / "calibration"


def main(mode: str) -> None:
    ablate = mode == "ablation"
    out = ROOT / ("pjm93_tempderate" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    _solve(
        [2023, 2024, 2025],
        out,
        temp_dependent_derate=True,
        zero_forcing_ablation=ablate,
        ablation_of=(ROOT / "pjm93_tempderate").name if ablate else None,
        note=(
            f"temp-derate full-keeper {mode} -- pjm90_cchp_srmc config + "
            "temp_dependent_derate, 2023-2025"
        ),
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
