"""Generate the pjm-94 keeper calibration_attestation.json (DOF ledger).

Transforms the pjm-90 keeper attestation into pjm-94's. pjm-94 carries the
pjm-90 recipe with ONE structural change: the ST_GAS extreme-day OVERNIGHT
pre-positioning drag (h0-6, reliability_floor engine) is replaced by the
all-hours ST_GAS NET-LOAD reliability-commitment drag
(fleet.apply_gas_st_netload_drag_floor), resolving root-cause issue #1483 /
gap-register G-21. Rule 19 drops the overnight ST_GAS reliability limbs when the
drag is on, so this is a replacement, not a stack.

Run after the bundle is scored so the residuals_note reflects the committed
legitimacy numbers.
"""

from __future__ import annotations

import json
from pathlib import Path

SRC = Path("results/calibration/pjm90_cchp_srmc/calibration_attestation.json")
DST = Path("results/calibration/pjm94_stgas_netload_drag/calibration_attestation.json")

# The all-hours ST_GAS net-load drag DOF entry (replaces st_gas_overnight_drag).
# Leave-one-year-out (rule 22): the hinge re-derived on each 2-year fold —
# holdout-2023 slope 0.00762 / int -0.4498 / cap 0.44 / zc 59.1 GW;
# holdout-2024 slope 0.01009 / int -0.7197 / cap 0.36 / zc 71.3 GW;
# holdout-2025 slope 0.01079 / int -0.7967 / cap 0.36 / zc 73.8 GW;
# pooled (applied) slope 0.01029 / int -0.7263 / cap 0.39 / zc 70.6 GW.
ST_GAS_NETLOAD_DRAG_ENTRY = {
    "name": "st_gas_netload_drag[PJM]",
    "where": "ScenarioConfig.gas_st_drag_slope_per_gw/_intercept/_cap "
    "(run_config; armed via gas_st_netload_drag) → fleet.apply_gas_st_netload_drag_floor",
    "identification": "measured-physical",
    "lineage_solves": "pjm-94 (#1483/G-21)",
    "value": {
        "mechanism": "all-hours ST_GAS net-load reliability-commitment drag "
        "(RUC-style; boilers committed in multi-day blocks when system net-load "
        "is high and held at part load through the low-price trough)",
        "engine": "fleet.apply_gas_st_netload_drag_floor (min-gen FLOOR; offers "
        "and prices untouched, LP dispatches economically above it)",
        "form": "min_gen = clip(0.01029*netGW - 0.7263, 0, 0.39) x available "
        "capacity; keyed to EIA-930 PJM net-load (load - wind - solar); "
        "zero-crossing 70.6 GW",
        "derivation": "scripts/data/derive_pjm_st_gas_netload_drag.py — measured "
        "OVERNIGHT (23-05h, low-price non-economic hours where any output is "
        "commitment not merit) CAMPD CF regressed on EIA-930 PJM net-load, "
        "2023-2025. PJM's OWN hinge (rule 25); nothing fit to a price/volume "
        "residual (rule 11); re-derives only on CAMPD/EIA-930 source update "
        "(rule 23).",
        "replaces": "st_gas_overnight_drag[PJM] (the pjm-89/90 overnight [0,6] "
        "reliability_floor limbs) — dropped at solve time by "
        "drop_drag_owned_reliability_specs (rule 19, one mechanism per class). "
        "The overnight limbs forced ~0.3 TWh and captured <20% of the class's "
        "energy (81-91% of measured ST_GAS energy falls OFF temperature-flagged "
        "days); the net-load drag is the year-round continuous commitment the "
        "measured operating rule shows.",
        "forced_energy": "ST_GAS st_netload_drag forces 4.18 TWh of 10.74 TWh "
        "class energy (38.9%, 2025). ST_GAS is <2% of PJM load (non-gated, C8); "
        "rubric-v2.2 grounded pass — D-4 all-24h window clean (the class's own "
        "driver evidence shows no hour it is offline: overnight CF rises with "
        "net-load, Spearman rho 0.32-0.52) and D-1 diurnal PASS (profile_r 0.971).",
        "identification": "measured-physical",
        "loo_stability": "PASS — hinge re-derived on all three 2-year folds: "
        "slope 0.0076-0.0108, intercept -0.45 to -0.80, cap 0.36-0.44, "
        "zero-crossing in a tight 59-74 GW band with NO sign flips or shape "
        "change. The pooled applied hinge (0.01029/-0.7263/0.39, zc 70.6) sits "
        "inside the fold spread; the flattest fold (holdout-2023) reflects the "
        "hotter 2024-25 CF, not overfitting. ST_GAS volume improves in every "
        "held-out year (2023 5.1->8.5, 2024 4.4->8.1, 2025 7.4->11.7 TWh vs "
        "actual 8.6/12.4/14.3) — in-sample gain WITH held-out gain, not "
        "overfitting (rule 22).",
    },
}

GOV_ATTESTED_BY = (
    "pjm-94 stgas-netload-drag 2026-07-09: pjm-90 recipe + all-hours ST_GAS "
    "net-load reliability-commitment drag (replaces the pjm-89/90 overnight "
    "pre-positioning drag; #1483/G-21)"
)
GOV_NOTE = (
    "pjm-90 keeper recipe with ONE structural change: the ST_GAS commitment "
    "mechanism moves from the extreme-day OVERNIGHT [0,6] pre-positioning drag "
    "(reliability_floor engine, ~0.3 TWh forced, captured <20% of the class) to "
    "the all-hours NET-LOAD reliability-commitment drag "
    "(fleet.apply_gas_st_netload_drag_floor), resolving #1483/G-21. Measured "
    "diagnosis (CAMPD, 9 pure-play plants 7.71 GW; diag_pjm_stgas_operation.py): "
    "real ST_GAS runs 8.6/12.4/14.3 TWh (2023/24/25) online 293-337/365 days in "
    "weeks-to-months blocks with only 9-19% of energy on temperature-flagged "
    "days — a net-load-driven continuous commitment, not a temperature event. "
    "The drag is a min-gen FLOOR (offers/prices untouched) with PJM's OWN hinge "
    "clip(0.01029*netGW-0.7263,0,0.39) fit from the measured overnight CF vs "
    "EIA-930 net-load (rule 25 PJM-own coeffs, rule 11 zero residual-fit); the "
    "SAME mechanism the ERCOT/NEISO keepers use, forward-native (#10/#13), NOT "
    "the fake sub-SRMC band #1483 warned against. Rule 19 drops the redundant "
    "overnight ST_GAS reliability limbs (no stacking)."
)
RESIDUALS_NOTE = (
    "ST_GAS underrun resolved as the tracked #1483/G-21 root cause: model "
    "5.1/4.4/7.4 -> 8.5/8.1/11.7 TWh (vs actual 8.6/12.4/14.3), 2023 near-exact. "
    "C2 system-volume FLIPS TO PASS (the criterion the ST_GAS de-flooding had "
    "regressed): CC_REGULAR overrun relaxes correspondingly (2024 +13.5->+12.0, "
    "2025 +3.6->+2.0 TWh). ST_GAS drag LOO-stable (see st_gas_netload_drag "
    "coefficients). D-1/D-2/D-4/D-9/D-10 all PASS; ST_GAS D-1 diurnal improves "
    "(profile_r 0.948->0.971). OPEN (unchanged from pjm-90, NOT touched by this "
    "change): (1) 2024/2025 ST_GAS still -4.3/-2.6 TWh short — the min-gen floor "
    "respects real CAMPD outage derates (available-capacity-capped), an honest "
    "residual NOT closed by tuning the cap (that would be the fake band #1483 "
    "warned against); (2) C3c price tail 2025 0h vs 51h >$200 — the per-gen "
    "ORDC/reserve scarcity item (G-20 Phase 2), pjm-94 fails it identically to "
    "pjm-90; the temp_dependent_derate lever (pjm-95) targets it. CC_CHP 2023 "
    "+50% and the coal near-match carry over from pjm-90 unchanged."
)


def main() -> None:
    """Write the pjm-94 attestation from the pjm-90 source with the drag DOF swap."""
    att = json.loads(SRC.read_text())

    att["governance"]["attested_by"] = GOV_ATTESTED_BY
    att["governance"]["note"] = GOV_NOTE
    att["governance"]["residuals_note"] = RESIDUALS_NOTE

    # Swap the overnight-drag DOF entry for the net-load drag entry (same count).
    entries = att["free_parameters"]["entries"]
    entries = [e for e in entries if e.get("name") != "st_gas_overnight_drag[PJM]"]
    entries.append(ST_GAS_NETLOAD_DRAG_ENTRY)
    att["free_parameters"]["entries"] = entries
    att["free_parameters"]["seeded"] = (
        att["free_parameters"]["seeded"]
        + " | pjm-94 (2026-07-09): st_gas_overnight_drag -> all-hours "
        "st_gas_netload_drag (measured-physical, LOO-stable; #1483/G-21 root "
        "cause resolved, C2 sysvol -> PASS)."
    )

    DST.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {DST}")


if __name__ == "__main__":
    main()
