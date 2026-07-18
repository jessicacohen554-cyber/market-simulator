"""Generate the pjm-93 keeper calibration_attestation.json (DOF ledger).

Transforms the pjm-90 keeper attestation into pjm-93's. pjm-93 carries the
pjm-90 recipe verbatim plus one addition: temp_dependent_derate=True, the
physically-derived per-class dry-bulb temperature capacity curve that
replaces the flat EIA-860 net-summer derate for CC/CT (capacity-neutral
reshape) and adds a pure additive hot-hour derate for COAL/ST_GAS (see
src/market_sim/config/scenarios.py temp_dependent_derate block,
docs/handoffs/temp-derate-keeper-rerun-playbook-2026-07.md). Run after the
bundle is scored so the residuals_note reflects the committed legitimacy
numbers.
"""

from __future__ import annotations

import json
from pathlib import Path

SRC = Path("results/calibration/pjm90_cchp_srmc/calibration_attestation.json")
DST = Path("results/calibration/pjm93_tempderate/calibration_attestation.json")

TEMP_DERATE = {
    "mechanism": "temperature-dependent capacity derate (temp_dependent_derate)",
    "engine": "fleet.generators_to_fleet_arrays temp_dependent_derate block "
    "(config/scenarios.py ScenarioConfig.temp_dependent_derate)",
    "physics": "raw(t) = 1 - slope_class * max(0, tmax_zone(t) - ref_class); "
    "CC/CT (air-density/mass-flow limited) rescaled so its Jun-Sep mean "
    "reproduces the existing net-summer capability -- a capacity-neutral "
    "reshape, not a level change; COAL/ST_GAS (condenser-limited, no prior "
    "summer derate) gain a pure additive hot-hour derate. Nuclear excluded; "
    "zones without weather coverage fall back to the flat derate. "
    "Availability always clipped to [0, 1].",
    "slopes": {
        "CT": "0.0126/C = 0.70 %/F (arXiv:2311.07001 0.0083/C; CPUC "
        "R.21-10-002 ~1 %/C)",
        "CC": "0.0076/C = 0.42 %/F net (arXiv:2311.07001 net-CC ~0.75 %/C)",
        "ST_GAS": "0.0054/C = 0.30 %/F (CPUC R.21-10-002: steam slope > GT "
        "slope, plant-level condenser derate modest)",
        "COAL": "0.0040/C = 0.22 %/F, onset 25 C/77 F (arXiv:2311.07001 "
        "modest steam-coal summer deration)",
    },
    "identification": "measured-physical",
    "forward_reproducibility": "physics slope x measured/forecast hourly "
    "dry-bulb temperature -- forward-reproducible in both backcast and "
    "forecast (rule 11); never fitted to a price/volume residual.",
    "effect": "PJM full-keeper rerun (pjm-93, 2023-2025): 2025 C3c scarcity "
    "tail (DA-expressible hours >$200) improved 0h->19h vs 51h actual "
    "(0.00x->0.37x, 37% of the undershoot closed); 2023 0h->2h (actual 8h), "
    "2024 4h->12h (actual 2h), both still small-count PASS. C1 fuel-mix "
    "(CC_REGULAR under/over-run, ST_GAS) essentially unchanged -- this "
    "mechanism reshapes capacity by temperature, it does not address the "
    "fuel-mix volume miss. No regression on any other C1-C8 criterion; "
    "forced-energy shares and D-4 off-window windows unchanged from pjm-90.",
}


def main() -> None:
    """Write the pjm-93 attestation by transforming the pjm-90 keeper's."""
    att = json.loads(SRC.read_text())
    g = att["governance"]
    g["attested_by"] = (
        "pjm-93 temp-derate 2026-07-09: pjm-90 recipe + temp_dependent_derate"
    )
    g["note"] = (
        "pjm-90 keeper recipe verbatim plus temp_dependent_derate=True: the "
        "per-class dry-bulb temperature capacity curve (arXiv:2311.07001, "
        "CPUC R.21-10-002) replacing the flat EIA-860 net-summer derate for "
        "CC/CT (capacity-neutral reshape) and adding a pure additive "
        "hot-hour derate for COAL/ST_GAS. Registered and reviewed as a "
        "probe (2026-07-08-pjm-93-temp-derate) before promotion; see "
        "temp_derate_coefficients below and "
        "docs/handoffs/temp-derate-keeper-rerun-playbook-2026-07.md."
    )
    g["residuals_note"] = (
        TEMP_DERATE["effect"]
        + " All other pjm-90 residuals (CC_CHP grid over-run, ST_GAS "
        "overnight drag, reliability_floor x CT_PEAKER D-4 off-window flag) "
        "carry over unchanged -- see pjm-90's residuals_note for their "
        "detail, none of which this mechanism addresses."
    )
    g["temp_derate_coefficients"] = TEMP_DERATE

    fp = att["free_parameters"]
    fp["seeded"] = (
        fp.get("seeded", "")
        + " | pjm-93 (2026-07-09): temp_dependent_derate added as a "
        "measured-physical, forward-reproducible parameter (arXiv:2311.07001, "
        "CPUC R.21-10-002 slopes) -- not a residual fit; ablation twin "
        "registered per rule 20 (2026-07-08-pjm-93-temp-derate-ablation)."
    )
    fp["entries"].append(
        {
            "name": "temp_dependent_derate[PJM]",
            "where": "config/scenarios.py ScenarioConfig.temp_dependent_derate "
            "(+ temp_derate_ref_c*/temp_derate_slope_* fields) via "
            "fleet.generators_to_fleet_arrays",
            "identification": "measured-physical",
            "lineage_solves": "pjm-93",
            "value": TEMP_DERATE,
        }
    )
    fp["n_entries"] = len(fp["entries"])

    DST.write_text(json.dumps(att, indent=2) + "\n")
    print(
        f"wrote {DST} (n_entries={fp['n_entries']}, n_residual={fp.get('n_residual')})"
    )


if __name__ == "__main__":
    main()
