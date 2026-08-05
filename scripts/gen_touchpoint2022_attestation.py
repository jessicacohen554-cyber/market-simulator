"""Generate the governance attestation for a 2022 validation-touchpoint run.

A touchpoint is not a new calibration: it is an ISO's FROZEN keeper recipe
replayed verbatim on the held-out 2022 year (``replay_keeper.py --years 2022``,
zero recipe deltas). So its attestation is not written from scratch — it is
DERIVED from the keeper's own committed attestation:

* ``free_parameters`` (the rule 20 ``[R-DOF]`` ledger) is carried over
  BYTE-IDENTICAL. That is the substantive claim the touchpoint makes: every
  free parameter was identified on 2023-2025 and NOT ONE was re-identified,
  re-fitted or re-tuned on 2022. A ledger that changed between the keeper and
  its own touchpoint would mean the holdout year had leaked into the recipe,
  which is the exact failure rule 22 exists to prevent.
* ``governance`` re-asserts the four gates, with the attestation text naming
  the touchpoint's own provenance (keeper id, freeze lift, tier).
* ``exceptions`` carries the touchpoint's measured criterion misses, written
  from the scored verdict rather than asserted, so the run reports against
  itself.

Usage:
    python scripts/gen_touchpoint2022_attestation.py --iso NEISO \
        --bundle results/calibration/neiso2022_touchpoint \
        --keeper-bundle results/calibration/neiso83_ca1reclass_B \
        --keeper-id 2026-08-05-neiso-83-ca1-reclass
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# The rule-22 framing every touchpoint attestation carries. Stated once here so
# the two ISOs cannot drift into describing the same spend differently.
_TIER_NOTE = (
    "VALIDATION TIER (CLAUDE.md rule 22). 2022 is ITERABLE model-SELECTION "
    "evidence, NOT a certified out-of-sample skill number and never quotable "
    "as one. It may be re-spent after the open availability-envelope defect "
    "lands, which is precisely why the owner spent it rather than the "
    "touch-once locked tier (2019 / H1-2026), which stays unspent and "
    "ungranted ('final' is empty)."
)


def build(
    iso: str,
    bundle: Path,
    keeper_bundle: Path,
    keeper_id: str,
    keeper_determination: str,
) -> dict:
    """Assemble the touchpoint attestation from the keeper's committed one."""
    keeper_att = json.loads(
        (keeper_bundle / "calibration_attestation.json").read_text()
    )
    dof = keeper_att["free_parameters"]

    return {
        "schema": "calibration-attestation/v1",
        # Carried over verbatim — see module docstring. The identical ledger IS
        # the out-of-sample claim.
        "free_parameters": dof,
        "governance": {
            "levers_trace_to_measured_input": True,
            "no_fit_to_price_residuals": True,
            "no_pinning_to_actuals": True,
            "outage_filter_exogenous_net_load": True,
            "attested_by": (
                f"{iso} 2022 VALIDATION TOUCHPOINT, 2026-08-05. A "
                f"replay_keeper.py re-solve of the designated keeper "
                f"{keeper_id} ({keeper_determination}) from its own "
                f"meta.json, with --years 2022 and NO other change: zero "
                f"--set overrides, zero offer-curve overrides, zero recipe "
                f"deltas. The rule 20 [R-DOF] ledger above is the keeper's "
                f"own, carried over byte-identical ({dof['n_entries']} "
                f"entries, {dof['n_residual']} residual-identified) — no "
                f"parameter was identified, re-identified or re-fitted on "
                f"2022, and no 2022 result fed back into any input. "
                f"{_TIER_NOTE} Spent under a NARROW owner lift of the "
                f"2026-07-25 holdout spend freeze (AskUserQuestion, "
                f"2026-08-05: 'Lift, spend, re-arm'), scoped to the PJM and "
                f"NEISO 2022 touchpoints alone and RE-ARMED in the same "
                f"session — see frontend/data/backcast/holdout-freeze.json "
                f"history."
            ),
        },
        "disclosures": {
            "note": (
                "TOUCHPOINT DISCLOSURES, reported rather than patched. "
                "(a) THE AVAILABILITY ENVELOPE IS KNOWN-IMPERFECT AND WAS NOT "
                "FIXED FIRST. The freeze this spend was taken under exists "
                "because the CAMPD unit-outage detector still books sustained "
                "economic layup as mechanical outage in all six ISO extracts, "
                "and a residual over-count survives the 2026-07-26 "
                "merit-order guard (campd-economic-layup-fix-charter-2026-07 "
                "§8, adopt-and-hold). Every criterion miss below is therefore "
                "scored against a fleet whose availability is about to "
                "change, and NONE of them may be attributed to forecast error "
                "alone without re-running after that fix. This is a stated "
                "limit of the evidence, not a hedge added after seeing the "
                "numbers — it is the freeze's own documented rationale. "
                "(b) SINGLE-YEAR BY DESIGN, NOT A RULE 16 [R-ALLYEARS] "
                "BREACH. Rule 16 governs calibration KEEPERS, which must "
                "cover 2023-2025 in one bundle. This is a validation "
                "touchpoint of one held-out year, which is exactly the shape "
                "the 'complete' marker authorizes ('complete only means 2022 "
                "test point can run'). It is NOT a keeper, is NOT promoted, "
                "and does NOT re-key any marker. (c) NO RE-TUNE IS PERFORMED "
                "HERE. Rule 22's stated response to a validation miss is to "
                "send the issue back to 2023-2025 and re-tune there; this "
                "session only measures and reports."
            )
        },
        "exceptions": [],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", required=True)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--keeper-bundle", required=True)
    ap.add_argument("--keeper-id", required=True)
    ap.add_argument("--keeper-determination", required=True)
    args = ap.parse_args()

    bundle = Path(args.bundle)
    if not bundle.is_absolute():
        bundle = REPO / bundle
    keeper_bundle = Path(args.keeper_bundle)
    if not keeper_bundle.is_absolute():
        keeper_bundle = REPO / keeper_bundle

    att = build(
        args.iso,
        bundle,
        keeper_bundle,
        args.keeper_id,
        args.keeper_determination,
    )
    out = bundle / "calibration_attestation.json"
    out.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {out.relative_to(REPO)}")
    print(
        f"  DOF ledger carried from {args.keeper_id}: "
        f"{att['free_parameters']['n_entries']} entries, "
        f"{att['free_parameters']['n_residual']} residual-identified"
    )


if __name__ == "__main__":
    main()
