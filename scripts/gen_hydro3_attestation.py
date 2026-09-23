"""Write the hydro-3 ARM bundle's governance attestation (rule 21 [R-DOF], C6).

``replay_keeper.py`` does not write an attestation, so a composed arm bundle has
none and C6 scores UNATTESTED. This mints one the way ``gen_nyiso247_attestation``
does: start from the INCUMBENT KEEPER's attestation (every governance flag,
exception and note inherited unchanged, because the arm changes exactly one
thing about that recipe), restate ``attested_by`` for this lane, then refresh
the DOF ledger from the ARM's own ``run_config.json`` with
``scripts/build_dof_ledger.py``.

``authorized_price_tuning`` stays ``null``: no ``offer_curve_by_group`` band
multiplier moved, so rule 1 [R-STRUCT]'s carve-out is NOT invoked.

Usage::

    python3 scripts/gen_hydro3_attestation.py results/calibration/hydro3_nyiso_ror_span
    python3 scripts/build_dof_ledger.py results/calibration/hydro3_nyiso_ror_span
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KEEPER = REPO / "results" / "calibration" / "nyiso247_fuelinv_span"

ATTESTED_BY = (
    "session hydro-3 (2026-09-22), THE ARM. Pre-registration: "
    "docs/PRECOMMIT-hydro-3-nyiso-ror-split-span-2026-09-22.md, pushed at "
    "57e3c77fcc00164da5c869e732783fbd695bcdc9 before any solve; owner ruling "
    "'1' (promote hydro_ror_split, 2022 G2 miss reported and attributed to the "
    "Central-East seam) on docs/FINDING-hydro-3-nyiso-2022-g2-is-seam-spill-"
    "2026-09-22.md. THE SINGLE DELTA: hydro_ror_split=true on the incumbent "
    "keeper nyiso247_fuelinv_span recipe (replay_keeper.py --set A/B); "
    "hydro_budget_nameplate_aware stays False. G-DRIFT 42d75053 -> aaaaeb61: "
    "every solve-path hunk INERT for this recipe. ZERO DOF: the ORNL-EHA/HILARRI "
    "classifier is categorical-external (94 run-of-river-class / 70 "
    "reservoir-class after hydro-1's HYBRID-label repair) and the flat level is "
    "each plant's own EIA-923 monthly budget. RULE 19 [R-ONE-MECH]: the RoR flat "
    "base subsumes its share of hydro_min_flow_floor, which is re-allocated over "
    "the reservoir class only (data.hydro.build_hydro_fleet). REPORTED AGAINST "
    "ITSELF: the pre-registered hydro-energy invariant G2 (< 0.1 %) is breached "
    "in 2022 (hydro-1: -0.1229 %, 31.4 GWh). This is NOT the nameplate clip (the "
    "clip is 1 plant-month, ~0 GWh). The cause is additional reservoir-class "
    "SPILL in the months the keeper already spills 629 GWh, i.e. nyiso-237's "
    "fabricated <= $0 Upstate_West hours behind a Central-East link pinned at its "
    "cap. The successor is that seam (owner-gated, nyiso-224), not this mechanism."
)


def main() -> None:
    """Mint the arm's attestation from the incumbent keeper's."""
    bundle = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else REPO / "results/calibration/hydro3_nyiso_ror_span"
    )
    att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    att["governance"]["attested_by"] = ATTESTED_BY
    att["authorized_price_tuning"] = None
    dest = bundle / "calibration_attestation.json"
    dest.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {dest}")
    print(
        "  NEXT: scripts/build_dof_ledger.py on this bundle (refresh from the ARM config)"
    )


if __name__ == "__main__":
    main()
