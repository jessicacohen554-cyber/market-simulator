"""Generate the pjm-90 keeper calibration_attestation.json (DOF ledger).

Transforms the pjm-80 keeper attestation into pjm-90's. pjm-90 carries the
pjm-83 recipe plus four structural corrections: (1) ST_GAS extreme-day overnight
drag (reliability_floor engine, measured-physical, LOO-stable), (2) CHP
steam-credit power-only HR correction extended to PJM (universal turbine
physics), (3) PRB dead-stop + orphaned ST_CHP outage capture (measured CAMPD),
and (4) CC_CHP SRMC re-grounding to the Manual-15 composite-cost floor (which,
like the pjm-80 ST_GAS/CT_INTERMEDIATE re-grounding, removes CC_CHP from the
sub-SRMC below-floor residual DOF). Run after the bundle is scored so the
residuals_note reflects the committed legitimacy numbers.
"""

from __future__ import annotations

import json
from pathlib import Path

SRC = Path(
    "results/calibration/pjm80_srmc_reground_keeper/calibration_attestation.json"
)
DST = Path("results/calibration/pjm90_cchp_srmc/calibration_attestation.json")

# Leave-one-year-out (rule 22) coefficient-stability result for the ST_GAS
# overnight drag, from re-deriving on each 2-year fold (scripts/
# derive_pjm_st_gas_overnight_drag.py --years <fold> --dry-run).
ST_GAS_DRAG = {
    "mechanism": "ST_GAS extreme-day overnight pre-positioning drag",
    "engine": "reliability_floor (reliability_floor_coeffs_PJM.csv ST_GAS limbs)",
    "window": "overnight [0,6]; drivers tmax/tmin/netload; floor_pct = "
    "commit_frac_overnight x MIN_STABLE_PCT_PHYSICAL['ST_GAS']=0.12",
    "derivation": "scripts/derive_pjm_st_gas_overnight_drag.py (measured CAMPD "
    "overnight committed-share vs driver, 2023-2025; nothing fit to a "
    "price/volume residual)",
    "enabled_limbs": "7 (Central_PA/EMAAC/West_APS tmax + Central_PA/Dominion/"
    "EMAAC/West_APS netload); all tmin limbs disabled (cold days n<30, "
    "unidentified); forced-energy 3.4-6.1% of ST_GAS class energy (rule 20)",
    "identification": "measured-physical",
    "loo_stability": "PASS — re-derived on all three 2-year folds; the four "
    "net-load limbs are rock-stable (floor_pct within ~0.01 across folds) and 6 "
    "of 7 limbs are stable. Only movement: the near-threshold Central_PA tmax "
    "limb (rho~0.33) swaps with Dominion tmax in the 2024-holdout fold — "
    "gate-boundary noise on a trivial-energy, non-gated (<2% load) class, not "
    "mechanism overfitting. The mechanism as a whole shows no held-out "
    "degradation (rule 22).",
}

CC_CHP_REGROUND = (
    "CC_CHP economic tranches re-grounded 0.6624/0.684/0.8208 -> 1.0/1.0/1.05 "
    "(Manual-15 composite-cost floor): the pjm-79/80 SRMC re-grounding for the "
    "one class it skipped. Measured diagnosis (agent 2026-07-08): CC_CHP "
    "over-DISPATCHED (grid CF ~48% vs measured net-to-grid ~29%) by bidding "
    "sub-SRMC, NOT a BTM capacity issue (merchant 35% BTM = correct host share, "
    "net-to-grid/gross 0.63-0.68). The steam credit is the host's (BTM-removed) "
    "so the grid MWh bids at power-only cost; must-run steam floor untouched. "
    "Removes CC_CHP from the residual below-floor DOF (like ST_GAS/CT_INTERMEDIATE)."
)

RESIDUALS_NOTE = (
    "CC_CHP over-run materially reduced by the SRMC re-grounding: vs EIA-923 "
    "net-to-grid, 2024 +47%->+19% (10.7->8.7 TWh), 2025 +52%->+16% (9.6->7.3). "
    "OPEN: 2023 CC_CHP still +50% (10.0->9.1 vs 6.1) — CC_CHP is genuinely "
    "efficient (corrected power-only HR ~6.3) so the netted grid capacity clears "
    "hard even at the composite-cost floor; the structural closer is a measured "
    "grid-export availability cap (net-export envelope, same family as "
    "retiree_cems_cap/cc_derate_from_top), flagged for owner sign-off rather than "
    "added autonomously (rule 11). CC_CHP is <2% of ISO load (non-gated, C8) and "
    "its D-1 diurnal shape PASSES. CT_CHP fixed by the CHP HR correction "
    "(2.0->1.4 TWh, near 923). ST_GAS overnight drag LOO-stable (see "
    "st_gas_drag_coefficients). Coal near-perfect (146.0 vs 145.9 EIA-930) with "
    "the PRB dead-stop + ST_CHP steam-boiler outage capture. The only residual "
    "D-4 flag is reliability_floor x CT_PEAKER 0.0002-0.0013 TWh (100% "
    "off-window), the same mixed-fuel class-aggregation artifact as pjm-80 on a "
    "dropped (drag-owned) floor, not a real floor."
)


def main() -> None:
    """Write the pjm-90 attestation by transforming the pjm-80 keeper's."""
    att = json.loads(SRC.read_text())
    g = att["governance"]
    g["attested_by"] = (
        "pjm-90 cchp-srmc 2026-07-08: steam-gas overnight drag + CHP power-only "
        "HR + PRB/ST_CHP outage capture + CC_CHP SRMC re-grounding"
    )
    g["note"] = (
        "pjm-83 keeper recipe + four grounded structural corrections: (1) ST_GAS "
        "extreme-day overnight drag in the reliability_floor engine (RUC-style "
        "reliability commitment, measured-physical, LOO-stable); (2) CHP "
        "steam-credit power-only HR correction extended to PJM (universal turbine "
        "physics, CHP_STEAM_CREDIT_HR_CORRECTION_ISOS={CAISO,PJM} — CT_CHP "
        "2.0->1.4 TWh); (3) PRB 5-13d dead-stop + orphaned ST_CHP steam-boiler "
        "outage capture (FULL_STOP_OVERRIDE_DAYS 14->5, measured CAMPD); (4) "
        + CC_CHP_REGROUND
    )
    g["residuals_note"] = RESIDUALS_NOTE
    g["st_gas_drag_coefficients"] = ST_GAS_DRAG

    fp = att["free_parameters"]
    fp["seeded"] = (
        fp.get("seeded", "")
        + " | pjm-90 (2026-07-08): CC_CHP committed band re-grounded to the "
        "Manual-15 SRMC floor (removes it from the residual below-floor DOF, like "
        "ST_GAS/CT_INTERMEDIATE at pjm-80); ST_GAS overnight drag added as a "
        "measured-physical, LOO-stable identified parameter."
    )
    fp["entries"].append(
        {
            "name": "st_gas_overnight_drag[PJM]",
            "where": "reliability_floor_coeffs_PJM.csv (ST_GAS limbs) via "
            "ScenarioConfig.reliability_floor",
            "identification": "measured-physical",
            "lineage_solves": "pjm-89/pjm-90",
            "value": ST_GAS_DRAG,
        }
    )
    fp["n_entries"] = len(fp["entries"])

    DST.write_text(json.dumps(att, indent=2) + "\n")
    print(
        f"wrote {DST} (n_entries={fp['n_entries']}, n_residual={fp.get('n_residual')})"
    )


if __name__ == "__main__":
    main()
