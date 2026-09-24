"""Write the R-NYISO composite bundle's governance attestation (rule 21 [R-DOF], C6).

``replay_keeper.py`` does not write an attestation, so a composed bundle has
none and C6 scores UNATTESTED. This mints one the way ``gen_hydro3_attestation``
does: start from the INCUMBENT KEEPER's attestation (every governance flag,
exception and note inherited unchanged, because this lane changes no mechanism
of that recipe -- it re-solves it on corrected INPUTS), restate
``attested_by`` for this lane, then refresh the DOF ledger from the composite's
own ``run_config.json`` with ``scripts/build_dof_ledger.py``.

``authorized_price_tuning`` stays ``null``: no ``offer_curve_by_group`` band
multiplier moved (verified leg by leg in ``scripts/probes/rnyiso_compose_span.py``),
so rule 1 [R-STRUCT]'s carve-out is NOT invoked.

Usage::

    python3 scripts/gen_rnyiso_attestation.py results/calibration/rnyiso_span
    python3 scripts/build_dof_ledger.py results/calibration/rnyiso_span
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KEEPER = REPO / "results" / "calibration" / "hydro3_nyiso_ror_span"

ATTESTED_BY = (
    "session R-NYISO (2026-09-24), INPUT CORRECTION of the incumbent keeper "
    "2026-09-22-nyiso-hydro3-ror-split. Pre-registration: "
    "docs/PRECOMMIT-r-nyiso-backcast-inputs-2026-09-24.md, pushed at "
    "e95436d5024fc14096eed558d6dd15a65128e524 before any solve, on the owner "
    "instruction of 2026-09-24 (docs/handoffs/AUDIT-backcast-inputs-860-heatrate-"
    "outage-2026-09-24.md sec. 5.3.6). THE ONLY CHANGE IS THE F1 INPUT FOUNDATION: "
    "the year-matched EIA-860 vintage (eia860_vintage_tracks_solve_year) and the "
    "measured CAMPD coal / ST / CC heat rates, default-on in backcast since F1 "
    "(#6572); CT and CHP were already measured and now read per-year rows. F2 "
    "(#6569) moves nothing NYISO reads (the armed std extract is byte-identical, "
    "sha256 ee778a87...). Offer curves byte-identical to the keeper (rule 1(c): an "
    "input correction is never re-tuned). G-DRIFT 57e3c77f -> 92100753: no LIVE-OTHER "
    "hunk. ZERO new DOF: every changed input is a measured or published source "
    "(EIA-860 annual release, eGRID, CAMPD). Rule 19 [R-ONE-MECH]: one heat rate per "
    "plant; at Bethlehem 2539 the eGRID steam-collapse identity rate (6.877) rightly "
    "supersedes a measured CC row that its own per-year boundary guard refuses in 6 "
    "of 7 years (PRECOMMIT sec. 4). Four year-isolated shards (rule 36), composed at "
    "zero LP. 2019-2021 not solved: DATA-BLOCKED (PRECOMMIT sec. 5)."
)


def main() -> None:
    """Mint the composite's attestation from the incumbent keeper's."""
    bundle = Path(
        sys.argv[1] if len(sys.argv) > 1 else REPO / "results/calibration/rnyiso_span"
    )
    att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    att["governance"]["attested_by"] = ATTESTED_BY
    att["authorized_price_tuning"] = None
    dest = bundle / "calibration_attestation.json"
    dest.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {dest}")
    print(
        "  NEXT: scripts/build_dof_ledger.py on this bundle (refresh from its config)"
    )


if __name__ == "__main__":
    main()
