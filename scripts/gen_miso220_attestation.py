"""Generate the miso-220 arm's calibration attestation from the keeper's.

miso-220 is a **KEEPER CANDIDATE**, which is what separates it from miso-218. The
distinction rests on an explicit OWNER RULING of 2026-09-05, recorded in
``PREREG-miso220-nonsteam-offer-lift-2026-09-05.md`` §1: the offer-curve band
multipliers ARE the intended channel for tuning on price and adjusting merit order,
and ONE CONFIG HELD ACROSS 2023-2025 is the discipline that separates tuning from
per-year fitting. miso-218 was rejected on two independent grounds — (a) rule 1
[R-STRUCT], a level scalar identified against a price residual is not a keeper
mechanism, and (b) it broke a load-bearing C1 cell. **The ruling disposes of (a);
(b) is untouched and is exactly what this arm's pre-registered kills test.**

The attestation exists so the arm can be SCORED: a replay writes none, and without
one the C6 governance gate reads UNATTESTED, guard (b) of the C3c standing rule
blocks reclassification, and C3c scores FAIL on values identical to the control's
(the miso-200 vacuous-pass trap, hit and documented at miso-217 §5, closed in
advance here as PREREG §6 K-4).

**No new ledger entry and no new parameter.** The lift rides the EXISTING
``offer_curve_by_group`` operator channel and is recorded verbatim in the bundle's
``run_config.json``; no ``ScenarioConfig`` field is minted and no matrix row is
added. ``n_entries`` stays 41 and ``n_residual`` 2.

Usage:
    python3 scripts/gen_miso220_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "results/calibration/miso217_intermphys_B/calibration_attestation.json"
ARM = REPO / "results/calibration/miso220_nonsteamlift_B"

DISCLOSURE = (
    "THE ARM: the four offer-curve band multipliers (committed, econ_low, econ_high, "
    "peak) of ELEVEN fossil classes scaled x1.10 - CC_REGULAR, CC_INTERMEDIATE, "
    "CC_CHP, CT_CHP, CT_PEAKER, CT_INTERMEDIATE, COAL, COAL_PRB, COAL_BIT, "
    "COAL_LIGNITE, COAL_WC - with ST_GAS and ST_GAS_INTERMEDIATE HELD BYTE-IDENTICAL "
    "per the owner's 2026-09-05 scoping answer, and with phys_* keys (measured "
    "physics) and the structural shares econ_low_share / pct_peaking NEVER scaled in "
    "any class. Within-class band ratios are preserved exactly for every lifted "
    "class, so merit order is preserved WITHIN each lifted class; what moves is the "
    "lifted classes against the held steam-gas pair, which is the merit-order "
    "adjustment the owner's ruling names as an intended effect. "
    "WHY STEAM GAS IS HELD, measured before the solve and not fitted: "
    "_miso220_marginal_class.json establishes that CT_PEAKER holds the margin in 24 "
    "of the 45 object hours (CT_PEAKER|econ alone in 22) while ST_GAS holds it in 4, "
    "with a merit-order reconstruction residual of at most $0.07/$0.48/$1.18 against "
    "the committed P1 duals - so steam gas is not the price setter in the hours the "
    "determination turns on, and it is the class the model most under-produces "
    "(2024 -7.155 TWh). "
    "THE SINGLE-DELTA PROOF: the keeper records only ONE explicit "
    "offer_curve_by_group row (ST_GAS_INTERMEDIATE) and resolves the rest implicitly, "
    "so a full explicit table is a single delta only if its unlifted half reproduces "
    "that implicit resolution exactly. _miso220_liveness.json S-1 measures "
    "max |delta mc| = 0.0 across all 2,923 tranches in EACH of 2023, 2024 and 2025; "
    "S-2 measures 1,604 tranches moved, ZERO in a held class and ZERO outside the "
    "covered classes, 74,251.8 MW lifted, with ST_GAS's cap-weighted offer moving "
    "+0.00 %. "
    "DECLARED LIMITS, not discovered afterwards (PREREG §3): oil (3,278.8 MW), "
    "biomass (1,865.7 MW) and ST_CHP (698.3 MW) carry no offer_curve_by_group entry "
    "and are UNLIFTED BY OMISSION, since adding entries would be a second delta and a "
    "new tuning surface; oil is fossil and already holds the marginal unit in 1 of "
    "2025's 15 object hours. "
    "AND THE NON-CLAIM, pre-committed (PREREG §5 P-6): this arm targets the MEAN. The "
    "phase-0 ladder shows the price pinned inside a ~15 GW near-flat CT_PEAKER|econ "
    "block with the whole stack topping out near $490 against actuals to $1,782 and "
    "an implied marginal-to-actual multiplier of 4.07/7.12/8.28, so NO TAIL CLAIM is "
    "made from this run whatever C3c returns."
)


def build(dst: Path) -> None:
    """Copy the keeper's attestation onto the arm, restamped and disclosed."""
    d = json.loads(SRC.read_text())
    d["governance"]["attested_by"] = (
        "miso-220 KEEPER CANDIDATE (2026-09-05) under the OWNER RULING of 2026-09-05 "
        "(PREREG-miso220 §1: the offer-curve band multipliers are the intended "
        "channel for tuning on price and adjusting merit order; one config held "
        "across 2023-2025; steam gas held as is): control = the miso-217 keeper "
        "bundle miso217_intermphys_B itself (already attested, never re-solved, "
        "rule 29(b) form 4) vs arm miso220_nonsteamlift_B, MISO 2023+2024+2025 in "
        "ONE invocation, years sequential, solved in-session and never on CI "
        "(rules 12/16), from the SAME committed keeper recipe via replay_keeper "
        "--set on the existing offer_curve_by_group operator channel. No "
        "ScenarioConfig field minted, no matrix row, ledger 41/2 unchanged. This "
        "attestation exists so the arm can be SCORED (without it C6 reads "
        "UNATTESTED and guard (b) of the C3c standing rule blocks reclassification "
        "- PREREG §6 K-4); it certifies the run's provenance, NOT that its gates "
        "pass, which _miso220_ab_gates.json adjudicates against kills frozen before "
        "the solve."
    )
    # THE TWO ASSERTIONS THAT CANNOT BE CARRIED FORWARD, and why they are flipped
    # rather than copied. The keeper asserts governance.no_fit_to_price_residuals =
    # true and levers_trace_to_measured_input = true. Neither is factually true of
    # THIS arm, and the owner's 2026-09-05 ruling does not make them true: the ruling
    # authorizes the CHANNEL (band multipliers may be tuned on price and may adjust
    # merit order), it does not license an attestation that asserts the opposite of
    # what the run did. The 1.10 was chosen to move a price residual and traces to no
    # measured input, so copying `true` would launder exactly the thing C6 exists to
    # catch. Both are set FALSE and the ruling is cited as the authorization for the
    # channel, not as a warrant for the claim. The scoring consequence (C6 is a
    # PROTECTIVE criterion, so a failure carries a protective caveat and can move the
    # determination) is accepted and reported, never engineered around.
    d["governance"]["no_fit_to_price_residuals"] = False
    d["governance"]["levers_trace_to_measured_input"] = False
    # UNCHANGED and still true: the arm sets no value to make an output match an
    # actual (the multiplier is owner-set and uniform across all three years, not
    # solved for a target), and it touches nothing in the outage/net-load path.
    d["governance"]["no_pinning_to_actuals"] = True
    # THE DECLARATION THE AMENDED RULE REQUIRES (rule 1 [R-STRUCT] carve-out,
    # owner ruling 2026-09-05, conditions (a)-(e)). Without a well-formed block
    # here, the two false assertions above are NOT scoped and C6 FAILs — the
    # amendment authorizes a declared channel, never silence. Machine-checked by
    # calibration_verdict._authorized_tuning_finding and audit_keepers.
    d["governance"]["authorized_price_tuning"] = {
        # (a) the ONLY authorized channel — not phys_*, not the structural shares
        "channel": "offer_curve_by_group",
        "ruling": (
            "owner ruling 2026-09-05: 'the offer curve multipliers are meant to allow "
            "us to tune on price & adjust merit order… as long as it's the same config "
            "across the 3 years'; steam gas scoped to ST_GAS + ST_GAS_INTERMEDIATE by "
            "the owner's follow-up answer the same day"
        ),
        "value": (
            "x1.10 on committed/econ_low/econ_high/peak for 11 non-steam fossil "
            "classes; ST_GAS and ST_GAS_INTERMEDIATE held byte-identical; phys_* and "
            "econ_low_share/pct_peaking untouched in every class"
        ),
        # (b) ONE config across EVERY scored year — never a per-year value
        "years_held": [2023, 2024, 2025],
        # (c) set ex ante in the PREREG, and never swept against the gates
        "set_ex_ante": True,
        "not_swept": True,
        "prereg": "results/calibration/PREREG-miso220-nonsteam-offer-lift-2026-09-05.md @ e1a2eb01",
        # (d) merit-order adjustment is an INTENDED effect, measured not hidden
        "merit_order_effect": (
            "intended and measured: _miso220_liveness.json S-3 records 121 non-steam "
            "tranches crossing above the steam-gas median at the mid-year probe hour"
        ),
        # (e) carried as a free parameter in the DOF ledger, identified by the
        # ruling rather than by a measured source
        "dof_entry": "offer_curve_by_group non-steam fossil lift (1.10), identified by owner ruling",
    }
    d.setdefault("disclosures", {})["miso220_nonsteam_lift"] = DISCLOSURE
    d["disclosures"]["miso220_governance_flip"] = (
        "governance.no_fit_to_price_residuals and levers_trace_to_measured_input are "
        "set FALSE on this arm, against the keeper's true. The owner ruling of "
        "2026-09-05 authorizes the offer-curve multiplier CHANNEL for tuning on price "
        "and adjusting merit order; it does not make the two factual assertions true, "
        "and this run does not claim them. The x1.10 was chosen to move a price "
        "residual and traces to no measured input. no_pinning_to_actuals REMAINS TRUE: "
        "the factor is owner-set and uniform across 2023-2025, not solved to land an "
        "output on an actual, and one config held across all three years is the "
        "discipline the ruling names. Whatever C6 scores on this basis is reported as "
        "scored."
    )
    dst.write_text(json.dumps(d, indent=1))
    print(
        f"wrote {dst.relative_to(REPO)} "
        f"(n_entries={d['free_parameters']['n_entries']}, "
        f"n_residual={d['free_parameters']['n_residual']})"
    )


if __name__ == "__main__":
    build(ARM / "calibration_attestation.json")
