"""Write ``calibration_attestation.json`` for the ercot-265 receipts-fallback keeper.

The run is the ercot-261 keeper recipe plus ONE registered field,
``ercot_ep_gas_basis_receipts_fallback`` (False -> True): when the corroboration
filter finds the two independent measurements of a month's delivered gas
disagree, the held-out month takes the EIA-923 Schedule-5 receipt basis instead
of the year's corroborated mean.

The DOF ledger is carried VERBATIM from the incumbent: the field introduces no
tunable, no multiplier, no offset and no threshold, so ``n_entries`` and
``n_residual`` do not move (rule 21 ``[R-DOF]``). The exceptions ledger is
likewise carried — C3c remains ERCOT's single ledgered model-class caveat — and
this run adds ONE exceptions row for the 2021 C3c band, which the standing rule
already governs on a holdout year (rubric v3.6).

Usage: python scripts/gen_ercot265_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

INCUMBENT = Path("results/calibration/ercot261_five_year_keeper")
ARM = Path("results/calibration/ercot265_receipts_five_year")

ATTESTED_BY = (
    'ercot-265 (2026-09-10, owner ruling: "It looks like it should be promoted"). '
    "ONE change over the 2026-09-09-ercot261-corroborated-gas-level keeper: the "
    "registered field ercot_ep_gas_basis_receipts_fallback, False -> True, armed in "
    "all five years. THE DEFECT IT REPAIRS is inside the incumbent's own filter. "
    "ercot_ep_gas_basis_corroborated admits a month's measured basis only where a "
    "SECOND independent measurement of the same delivered-gas quantity agrees within "
    "ERCOT_GAS_CORROBORATION_TOL_USD_MMBTU = 1.00; when they DISAGREE the incumbent "
    "substitutes the year's corroborated mean, i.e. it DISCARDS BOTH MEASUREMENTS and "
    "prices an extraordinary month at an ordinary level. It fires in exactly one year "
    "of 2019-2025: 2021, months 2 and 12. February 2021 is Winter Storm Uri and "
    "carried 94.8% of that year's C3b SSE, the ISO's only remaining rubric failure. "
    "THE REPAIR IS RULE 14 [R-ACCURATE]: between the two disagreeing measurements, "
    "prefer the better-grounded. EIA-923 Schedule-5 receipts are what the plants "
    "ACTUALLY PAID, quantity-weighted over the same population -- Feb-2021 $45.96/MMBtu "
    "across 36 plants on 28.4 million MMBtu, the year's LARGEST burn month -- against "
    "an EIA N3045TX3 survey print that is a monthly cost/volume RATIO which "
    "data.fuel.basis.ercot's own docstring already records as unreliable when a month's "
    "within-month price distribution is extreme. So a held-out month takes the "
    "corroborator's own basis (receipts minus the same monthly hub): 2021-02 basis "
    "+0.390 -> +40.611 and 2021-12 +0.390 -> +1.589 $/MMBtu. "
    "ZERO FREE PARAMETERS (rule 21 [R-DOF]) and the DOF ledger is carried verbatim: the "
    "tolerance constant, the admissibility test and the fail-closed incompleteness "
    "discipline are all UNTOUCHED, and the substitute value comes from a series already "
    "committed and already read by this filter. A SUB-GATE inside the corroboration flag, "
    "never a mechanism beside it (rule 19 [R-ONE-MECH]): same filter, same rows, same "
    "held-out months, same mechanism id -- only the fallback VALUE changes. "
    "MOTIVATION STATED HONESTLY, because it is not the identification: the lane came to "
    "this filter from the C3b-2021 residual, but nothing here is fitted to that residual "
    "and there is no value to fit -- +40.611 is read entirely off the measured receipt "
    "series, and the choice between the two series rests on measurement quality (a "
    "quantity-weighted receipt vs a cost/volume ratio in an extreme month), an argument "
    "that stands independently of any price. No sweep was run and no criterion selected "
    "the value. "
    "CONFINEMENT VERIFIED BY SHA256, not asserted: of the 30 committed hourly sidecars "
    "(6 x 5 years), the six 2021 files differ from the incumbent and all 24 files for "
    "2022/2023/2024/2025 are BYTE-IDENTICAL. The 2023-2025 TRAIN TIER therefore cannot "
    "move, and ERCOT's CALIBRATED determination on that tier is untouched (rule 30(c)). "
    "MEASURED, arm vs the incumbent's committed 2021: C3b price_shape 0.559 FAIL -> 0.168 "
    "PASS against a 0.20 gate, closing the incumbent's ONLY failing criterion; C3a "
    "price_mean -6.7% -> +5.6%, both PASS and the arm smaller in absolute error against "
    "the $165.53/MWh actual; February 2021 $1,422.13 -> $1,690.92 against $1,767.07 "
    "actual, i.e. -19.5% -> -4.3%. "
    "COSTS AT FULL MAGNITUDE, none minimised: C3c price_tail 223 h -> 687 h against 258 h "
    "actual RT (0.86x -> 2.66x), and the entire blow-up is February -- 464 new >$200 "
    "hours, 464 of them in February and ZERO outside it, with the >=$1,000 deep tail "
    "essentially unmoved at 131 -> 133 h. That is the monthly-resolution BREADTH defect: "
    "a monthly value lands on all 672 February hours while the real Uri spike lasted ~5 "
    "days. It is reported, not repaired, and the NAMED SUCCESSOR is unchanged -- a DAILY "
    "delivered series (Waha / Houston Ship Channel), which ercot-265's own survey found "
    "unobtainable from any free public source (EIA's NGWU daily table carries no Texas "
    "hub; CME/NYMEX delisted both hubs on zero open interest; ICE/NGI/Platts/Argus are "
    "paid and refused by the owner ruling of 2026-08-04). Slack also rises 960.6 -> "
    "2,274.9 MWh in 2021 (dump stays 0.0). D-4 per-unit conduct carries 310 rows / 91 "
    "failures against the incumbent's 309 / 89 -- one extra row and two extra convictions, "
    "all 2021, inherited from the same pre-existing mechanism family and not introduced "
    "by this field. "
    "Records: docs/handoffs/PRECOMMIT-ercot265-receipts-fallback-2026-09-09.md (with "
    "AMENDMENT 1, which withdrew a mis-specified C3c kill gate on the owner's correction "
    "that C3c is an accepted caveat and cannot kill a run), and "
    "results/calibration/METRICS-ercot265-2021.json / METRICS-ercot265-2022.json."
)

C3C_2021_EXCEPTION = {
    "criterion": "price_tail",
    "year": 2021,
    "kind": "model-class",
    "magnitude": (
        "model 687 h vs actual RT 258 h > $200/MWh (2.66x); incumbent keeper 223 h "
        "(0.86x). The entire delta is February: 464 new >$200 hours, all of them in "
        "February and zero outside it; the >=$1,000 deep tail is essentially unmoved "
        "(131 -> 133 h)."
    ),
    "reason": (
        "ACCEPTED MODEL-CLASS LIMITATION on a HOLDOUT year. 2021 is validation tier, and "
        'under rubric v3.6 (owner, 2026-09-05, verbatim: "c3c should be an accepted '
        "caveat on all holdout years\") the C3c standing rule's lone-failure condition is "
        "DROPPED on an out-of-training year, so C3c reads CAVEAT there whatever else that "
        "year does. It spends no second ledger slot: C3c already carries ERCOT's "
        "model-class entry. THE CAUSE IS STATED AND NOT REPAIRED HERE -- it is the "
        "monthly-resolution BREADTH of the measured level, which lands a single monthly "
        "value on all 672 February hours when the real Uri spike lasted about five days. "
        "The named successor is a DAILY delivered series (Waha / Houston Ship Channel), "
        "measured unobtainable from any free public source by the ercot-265 survey and "
        "therefore an owner procurement decision, not a modelling choice. This caveat "
        "does NOT close root-causing."
    ),
}


def main() -> None:
    """Compose the arm's attestation from the incumbent's, changing only what moved."""
    incumbent = json.loads((INCUMBENT / "calibration_attestation.json").read_text())

    out = {
        "schema": incumbent["schema"],
        # Zero new tunables, so the ledger is carried VERBATIM (rule 21 [R-DOF]).
        "free_parameters": incumbent["free_parameters"],
        "exceptions": [*incumbent["exceptions"], C3C_2021_EXCEPTION],
        "governance": {
            "levers_trace_to_measured_input": True,
            "no_fit_to_price_residuals": True,
            "no_pinning_to_actuals": True,
            "outage_filter_exogenous_net_load": True,
            "attested_by": ATTESTED_BY,
        },
    }
    (ARM / "calibration_attestation.json").write_text(json.dumps(out, indent=1) + "\n")
    fp = out["free_parameters"]
    print(f"wrote {ARM / 'calibration_attestation.json'}")
    print(
        f"  free_parameters: n_entries={fp['n_entries']} n_residual={fp['n_residual']} (carried verbatim)"
    )
    print(
        f"  exceptions: {len(incumbent['exceptions'])} carried + 1 new (price_tail 2021)"
    )


if __name__ == "__main__":
    main()
