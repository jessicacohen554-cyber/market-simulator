"""Write the nyiso-247 ARM bundle's governance attestation (rule 21 [R-DOF], C6).

``replay_keeper.py`` does not write an attestation, so a composed arm bundle has
none and C6 scores UNATTESTED. This mints one the way the ``gen_caiso*`` lane
scripts do: start from the INCUMBENT KEEPER's attestation — every governance
flag, exception and note it carries is inherited unchanged, because this arm
changes exactly one thing about that recipe — then restate ``attested_by`` for
this lane and refresh the DOF ledger from the ARM's own ``run_config.json``
(``scripts/build_dof_ledger.py``), which is what makes the ledger honest: the
disarm removes a mechanism, so any entry keyed on its flag must drop out.

``authorized_price_tuning`` stays ``null``, as on the keeper: this lane touched
no ``offer_curve_by_group`` band multiplier. Rule 1 [R-STRUCT]'s carve-out is
NOT invoked and must not read as if it were.

Usage::

    python3 scripts/gen_nyiso247_attestation.py results/calibration/nyiso247_fuelinv_span
    python3 scripts/build_dof_ledger.py results/calibration/nyiso247_fuelinv_span
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KEEPER = REPO / "results" / "calibration" / "nyiso241_ctcommitted_span"

ATTESTED_BY = (
    "session nyiso-247 (2026-09-20), THE ARM. Pre-registration: "
    "docs/PRECOMMIT-nyiso247-fuel-invariance-limb-2026-09-20.md, pushed at "
    "40316764d1977e48e44566ec71a09ed562be73f1 BEFORE any gated number existed, "
    "carrying the FORM, every bar and every kill; phase 0 at "
    "42d750537532c95d335286b63bca881e8a01c76b "
    "(docs/ADDENDUM-nyiso247-phase0-gates-and-two-falsified-claims-2026-09-20.md). "
    "Matrix cell: gas_offer_net_revenue_margin. "
    "THE SINGLE DELTA: gas_offer_net_revenue_margin is DISARMED for NYISO, with "
    "its two sub-gates (gas_offer_margin_zonal_anchor{,_vintage}), which resolve "
    "the SAME mechanism's identification point and cannot stand without it "
    "(data/fleet/assembly.py:210). Nothing else moves: the arm is a "
    "replay_keeper.py --set A/B off the keeper's own committed bundle. "
    "THE BASIS IS MEASURED CONDUCT AND NEVER THE RESIDUAL (rules 1 [R-STRUCT] / "
    "13 [R-MEASURED]). The armed term is offer_markup_hr x (anchor - fuel), so "
    "the offer's IMPLIED HEAT RATE FALLS as delivered gas rises; NYISO MIS P-27 "
    "genbids (DAM, 2022-2025 pooled, within-unit, capacity-weighted; "
    "data/raw/_validation-source/nyiso_offer_level_dispersion.json, sha256 "
    "1ad26b2f21e3654c5cb1f25f66c0715ebeff601299624b4dd85de05d95e2f1db) measures "
    "the market's RISING +2.035 / +11.928 / +27.880 MMBtu/MWh at p50/p75/p90. "
    "The market prices scarcity INTO its implied offer heat rate and the armed "
    "model prices it OUT. The registered family has exactly two members: the "
    "armed one is the ONLY member whose conditional response is strictly "
    "negative and the disarmed one the UNIQUE member whose response is zero, so "
    "the disarm is the family's closest admissible point to the measurement and "
    "adds NO free parameter. No price error enters the identification path. "
    "ZERO DOF, ZERO NEW CODE, ZERO NEW ScenarioConfig FIELD; rule 1's authorized "
    "band-multiplier channel is NOT invoked (authorized_price_tuning stays null) "
    "and no multiplier moved. RULE 19 [R-ONE-MECH]: this REMOVES one of the five "
    "armed non-base writers and adds nothing — the strongest form of "
    "replace-never-stack; nyiso_st_gas_econ_bands_deleaked and "
    "nyiso_ct_peaker_committed_measured both stay armed and untouched, and the "
    "ST_GAS markup that routes to OPEN ROOT CAUSE #1344 reverts to the "
    "multiplier form rather than being removed, so that issue is neither closed "
    "nor stacked upon. RULE 28 [R-MECH-MATRIX] (a) DISCHARGED BEFORE ANYTHING "
    "WAS PROPOSED: nyiso-167's DO-NOT-REDO on this cell is satisfied ON ITS OWN "
    "TERMS — it refused a PER-YEAR RE-ANCHOR 'absent new measured NYISO offer "
    "data', the P-27 corpus IS that data, and a per-year re-anchor is NOT "
    "proposed here; nyiso-195's kill of REMOVING the CC_REGULAR econ markup is "
    "not re-tested either, because the markup SURVIVES AT FULL STRENGTH under "
    "the disarm (mult is untouched; only its fuel basis moves). "
    "REPORTED AGAINST ITSELF, so a favourable price move cannot later be read as "
    "the object closing: (a) the disarm moves the model's conditional response "
    "from NEGATIVE to ZERO and the book's is POSITIVE, so it closes the SIGN and "
    "NO MORE — the remaining rise belongs to the conditional level-dispersion "
    "object (refused on FORM by nyiso-246, r_anchor 0.145) and to the "
    "daily-citygate successor; (b) below p50 the fit WORSENS (rank-mean "
    "|Q_mod - Q_book| 6.9868 -> 9.0060) and the full-grid closure is narrow "
    "(12.1646 -> 11.9268, 2.0 %); (c) the PRECOMMIT's own level-neutrality claim "
    "was FALSIFIED by its own gate G-E before the solve and is declared at full "
    "magnitude — the removed term's capacity-weighted annual mean is -1.49 / "
    "-2.01 / -2.77 / -1.59 $/MWh at ISO level and -4.36 to -5.73 in NYC, so this "
    "is a LEVEL intervention in a load pocket, not the pure redistribution the "
    "PRECOMMIT asserted."
)


def main() -> None:
    bundle = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else REPO / "results/calibration/nyiso247_fuelinv_span"
    )
    att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    att["governance"]["attested_by"] = ATTESTED_BY
    att["authorized_price_tuning"] = None
    dest = bundle / "calibration_attestation.json"
    dest.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {dest}")
    print(
        f"  governance flags : {[k for k, v in att['governance'].items() if v is True]}"
    )
    print(f"  price tuning     : {att['authorized_price_tuning']}")
    print(
        "  NEXT: scripts/build_dof_ledger.py on this bundle (refresh from the ARM config)"
    )


if __name__ == "__main__":
    main()
