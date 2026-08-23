"""caiso-217 — the REALIZED post-crosswalk south-belly surplus table.

Re-runs the committed caiso-216 belly-surplus instrument
(``_caiso216_belly_surplus.py``) with the measured hub-membership crosswalk
ACTIVE in ``zone_assignment`` (caiso-217 Phase A), writing to a caiso-217
output so the committed caiso-216 record (the PRE-crosswalk state its FINDING
quotes) is never overwritten. The B2 deciding table then carries the realized
re-allocation exactly as the LP will receive it — the S1'/S2' answer the
caiso-216 packet's Ask 1 requested, replacing that FINDING's §E upper-bound
arithmetic — and the B0 demand-row-match control doubles as proof the
crosswalk moved GENERATION only (zonal load is untouched: the load split is
the separate caiso-172 ATL_LDF derivation).

The B2b "sensitivity" rows in the caiso-217 output are residual movable-mass
bounds measured on the POST-crosswalk assignment (the straddle cohorts the
join did not reach); they are reported for completeness, not decision-bearing.

Usage:
    PYTHONPATH=.:src python3 scripts/probes/_caiso217_realized_membership.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _caiso216_belly_surplus as c216  # noqa: E402  (committed instrument)

# A caiso-217 cache namespace: the caiso-216 recon cache must never be reused
# (its arrays embed the PRE-crosswalk zone assignment).
c216.CACHE = Path(
    os.environ.get(
        "CAISO217_CACHE",
        str(c216.CACHE.parent / "caiso217_recon"),
    )
)
c216.OUT_JSON = REPO / "results/calibration/_caiso217_realized_membership.json"


def main() -> None:
    from market_sim.data.zone_assignment import load_caiso_hub_membership

    membership = load_caiso_hub_membership()
    if not membership:
        raise SystemExit(
            "caiso-plant-hub-membership.csv is absent — this probe measures "
            "the POST-crosswalk state and must not run without it"
        )
    print(f"hub-membership crosswalk ACTIVE: {len(membership)} plants")
    c216.main()


if __name__ == "__main__":
    main()
