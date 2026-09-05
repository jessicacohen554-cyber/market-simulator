"""Generate miso186_dir_B's calibration attestation from the keeper's.

The arm is the miso-177 keeper recipe plus exactly one zero-residual-DOF
mechanism (the gen_miso169/gen_miso180 attestation pattern), so its
attestation is the keeper's with: one MEASURED-identified ledger entry for
the unit-outage fleet-status scope (EIA-860 operable generator status — a
published data sheet, zero fitted scalars, zero lineage solves), a rewritten
``governance.attested_by`` for the miso-186 A/B, and this session's
disclosures appended AT FULL MAGNITUDE (the S-5 regressions included).
``n_residual`` is UNCHANGED at 2. Exceptions carry unchanged.
"""

import json

SRC = "results/calibration/miso177_rho_B/calibration_attestation.json"
DST = "results/calibration/miso186_dir_B/calibration_attestation.json"

d = json.load(open(SRC))

d["free_parameters"]["entries"].append(
    {
        "name": "unit_outage_fleet_status_scope (boolean arm)",
        "where": (
            "ScenarioConfig.unit_outage_fleet_status_scope -> "
            "data/fleet/arrays.py -> outages._unit_outage_factors_from_events "
            "(fleet_status_scope=) over the std/short/partial CAMPD event "
            "layers; status source = the active EIA-860 operable snapshot's "
            "Generator Status column (outages._fleet_status_index), the SAME "
            "sheet data/fleet/eia860.py builds the OP-only dispatch fleet from"
        ),
        "identification": "measured",
        "lineage_solves": (
            "0 (a consistency scope on a published data sheet: event rows "
            "whose unit id matches a non-OP generator are dropped because "
            "their capacity is already absent from the derate denominator — "
            "the double-count was adjudicated against the plant's own CAMPD "
            "record BEFORE any LP was spent, PREREG-miso186 §4 clauses "
            "(i)-(v); no LMP, no residual, no tuned scalar anywhere in the "
            "path. Static reach computed offline from inputs only: "
            "+0.480 GW 2025 scarce-hour South economic capacity)"
        ),
        "value": (
            "True (the filter itself carries no numeric parameter; the "
            "adjudicated case is Cottonwood 55358 — two OA trains' terminal "
            "CEMS darkness summing to 1.23 of the modeled 580.4 MW OP half, "
            "clipping it to availability 0.0 Jul-Nov 2025 against the "
            "plant's own CAMPD record of ~526 MW in ALL 47 scarce hours; "
            "audit table of every dropped event row: FINDING-miso186)"
        ),
    }
)
d["free_parameters"]["n_entries"] = len(d["free_parameters"]["entries"])

d["governance"]["attested_by"] = (
    "ARM - EXACTLY ONE MECHANISM CHANGES: unit_outage_fleet_status_scope="
    "true. miso-186, 2026-08-25. PREREG "
    "results/calibration/PREREG-miso186-midwest-stack-direction-2026-08-25.md "
    "was committed and pushed (3f0d9f0) BEFORE any adjudicating quantity was "
    "computed; the candidate was named by the pre-registered formation-input "
    "decomposition (measured South scarce surplus +2.441 GW vs keeper "
    "economic surplus -1.354 GW), cleared all five admissibility clauses, "
    "and won the frozen selection rule (static reach +0.480 GW vs the "
    "also-clearing nuclear candidate's +0.299). Both legs are replay_keeper "
    "re-solves of the 2026-08-22-miso-177-rho-measured keeper's own recipe "
    "at this session's HEAD, --year 2023 2024 2025 in ONE invocation each, "
    "years sequential (rules 12/16); the arm's single delta rode the "
    "sanctioned replay_keeper --set channel. CONTROL VALUE-IDENTITY (S-0): "
    "2026-08-25-miso-186-control reproduces the committed keeper with "
    "numeric max|diff|=0 on every scored sidecar of every year. STRUCTURAL "
    "GATES: S-2 PASS (2025 scarce N->S RDT binding falls 9/47 -> 7/47; the "
    "first MISO mechanism ever to move the scarce-hour direction toward the "
    "measured 32/47 S->N record) and S-3 PASS (South boundary-complex net "
    "inflow +0.969 -> +0.682 GW, +0.286 GW toward the measured -2.441, "
    "balance-verified < 0.002 MW); S-1 exactness PASS (Cottonwood scarce "
    "dispatch 0 -> 448.7 MW vs the CAMPD-measured 525.8); S-4 PASS (zero "
    "D-4 conduct failures, zero new; C8 PASS). SCORED FACE AT FULL "
    "MAGNITUDE (S-5, the owner-escalation path): C3a-2025 -11.75% -> "
    "-12.32% (-0.57 pp), C3a-2024 -4.06% -> -4.67%, C3a-2023 +1.28% -> "
    "+1.22%; ONE criterion-year flip, C1 fuelmix CC_REGULAR 2024 "
    "PASS->FAIL at +8.09 TWh vs the +-8.00 TWh band (control +6.65 — the "
    "restored real capacity tips a class the model already over-dispatches "
    "past the band edge by 0.09 TWh). PROMOTED UNDER THE OWNER POSTURE "
    "DIRECTIVE (2026-08-24 PREREG-miso184 preamble, re-affirmed in writing "
    "2026-08-25 this session: 'If structural integrity improves but gates "
    "regress that may still be a keeper') and rules 1/14: the control is "
    "KNOWN to carry a CAMPD-falsified availability input, so the "
    "structurally faithful run is the arm; the worse fit under the accurate "
    "input is rule-14's own signal that the residual's root cause lies "
    "elsewhere (the adjudicated flat-stack/tail family). LOYO within "
    "2023-2025: the mechanism carries ZERO fitted parameters and its "
    "identification (a status sheet) is year-independent, so no year's "
    "parameters were identified against any year's outcome; per-year "
    "effects reported at full magnitude above. The mechanism adds ZERO "
    "residual-identified parameters (n_residual unchanged at 2). Rule 22: "
    "no year outside 2023-2025 was solved, scored or registered; MISO holds "
    "neither complete nor final and the holdout spend freeze is untouched."
)

d["disclosures"]["miso186_ab"] = (
    "A/B verdict record: results/calibration/_miso186_ab_gates.json "
    "(S-0..S-5 + the charter kill, which does NOT fire: C3a-2025 worsens "
    "while BOTH structural gates pass — the exact opposite of the "
    "level-adder signature). Formation-input decomposition record: "
    "_miso186_direction_decomposition.json (legs L/A/M/R/S + the "
    "candidate static reach). Instrument-fidelity corrections disclosed in "
    "FINDING-miso186: the F-2 footing gate was made faithful to the "
    "imported machinery's own committed usage (V1+V4 gate, V2 reported — "
    "lineage drift, the miso-178 precedent); the fuel-family crosswalk was "
    "re-keyed to the fleet's actual fuel_type vocabulary; the S-3 balance "
    "identity gained the LP's own zonal storage term. The ALSO-CLEARING "
    "second candidate (the missing MISO measured-nuclear availability "
    "layer: no NUCLEAR_MONTHLY_CF_BY_YEAR['MISO'] entry, no "
    "nuclear-availability-MISO.csv, MISO absent from NRC_TO_EIA while all "
    "four sister ISOs carry the overlay; static reach +0.299 GW South) is "
    "handed to the queue, not armed here (single-delta discipline)."
)

json.dump(d, open(DST, "w"), indent=1)
print(
    f"wrote {DST} (n_entries={d['free_parameters']['n_entries']}, "
    f"n_residual={d['free_parameters']['n_residual']})"
)
