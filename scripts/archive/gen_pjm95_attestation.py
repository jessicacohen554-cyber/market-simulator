"""Generate the pjm-95 keeper calibration_attestation.json (DOF ledger).

Transforms the pjm-94 keeper attestation into pjm-95's. pjm-95 carries the
pjm-94 recipe with ONE structural change: ``temp_dependent_derate=True`` — the
physically-derived per-class dry-bulb capacity curve (arXiv:2311.07001, CPUC
R.21-10-002; capacity-neutral CC/CT reshape + additive hot-hour COAL/ST_GAS
derate). The mechanism carries ZERO fitted parameters (published curve
coefficients, no residual in the loop), so the DOF ledger gains a
documentation entry, not a free parameter: the ledger count is unchanged and
the rule-22 LOO requirement is satisfied structurally (nothing to refit; the
C3c gain repeats in every train year independently).

Run after the bundle is scored so the residuals_note reflects the committed
rubric-v2.4 numbers.
"""

from __future__ import annotations

import json
from pathlib import Path

SRC = Path("results/calibration/pjm94_stgas_netload_drag/calibration_attestation.json")
DST = Path(
    "results/calibration/pjm95_stgas_drag_tempderate/calibration_attestation.json"
)

# Zero-DOF mechanism entry: documented in the ledger for completeness, but it
# contributes no free parameter (identification is published-physical, the
# coefficients are not tunable through ScenarioConfig and never touched a
# residual).
TEMP_DERATE_ENTRY = {
    "name": "temp_dependent_derate[all-ISO mechanism, PJM keeper use]",
    "where": "ScenarioConfig.temp_dependent_derate (boolean gate) → "
    "fleet.generators_to_fleet_arrays temp-derate block",
    "identification": "physical-literature (zero fitted parameters)",
    "lineage_solves": "pjm-93 (single-delta probe on pjm-90), pjm-95 (keeper)",
    "value": {
        "mechanism": "hourly zone dry-bulb temperature reshapes thermal "
        "available capacity: CC/CT air-density curve rescaled so the Jun-Sep "
        "mean reproduces the existing net-summer capability (capacity-NEUTRAL "
        "reshape, heatwave hours fall below net-summer, cool hours rise toward "
        "full rating); COAL/ST_GAS gain a pure additive hot-hour condenser "
        "derate; nuclear excluded; availability clipped to [0,1]",
        "derivation": "published per-class slopes (arXiv:2311.07001, CPUC "
        "R.21-10-002) — coefficients are literature constants cited in "
        "scenarios.py, NOT exposed as tunables and NEVER fit to any residual "
        "(rule 11/23). Boolean gate only.",
        "loo_status": "no fitted parameter to refit — rule-22 LOO satisfied "
        "structurally; the C3c tail gain repeats independently in every train "
        "year (RT >$200h: 2023 0->2 of 6, 2024 4->12 of 18, 2025 DA 0->19 of "
        "51), not a single-year artifact",
        "open_validation": "PJM-fleet measured capability check outstanding: "
        "the ERCOT temp-derate line was REJECTED 2026-07-09 because ERCOT's "
        "own scarcity-hour capability slopes measured ~0/negative "
        "(calibration-log closure); that finding is ERCOT-only (rule 24) and "
        "the analogous PJM CAMPD scarcity-hour slope derivation "
        "(_scarcity_hour_slope pattern) should be run for PJM — if PJM's fleet "
        "refutes the slopes the same way, this mechanism exits the keeper the "
        "same way ERCOT's did.",
    },
}

GOV_ATTESTED_BY = (
    "pjm-95 stgas-drag+temp-derate 2026-07-09: pjm-94 recipe + "
    "temp_dependent_derate=True (zero-DOF physical capacity curve; targets the "
    "C3c scarcity-tail FAIL, G-20)"
)
GOV_NOTE_SUFFIX = (
    " | pjm-95 adds temp_dependent_derate=True on the pjm-94 recipe verbatim: "
    "a physically-derived per-class dry-bulb capacity curve (arXiv:2311.07001, "
    "CPUC R.21-10-002) — capacity-neutral CC/CT reshape + additive hot-hour "
    "COAL/ST_GAS derate, zero fitted parameters (boolean gate; coefficients "
    "are cited literature constants, rule 11/23). Structural scarcity physics "
    "(rule 1): heatwave hours lose thermal capability exactly when the tail "
    "prices form."
)
RESIDUALS_NOTE = (
    "Rubric v2.4 (load-weighted C3a/C3b basis), 2023-2025 one bundle: C3b "
    "duration/shape PASSES all years (pjm-94 FAILs 2025 at NRMSE 0.217); C3a "
    "2025 -13.2% FAIL (pjm-94 -14.9%; 2023/2024 within band); C3c DA tail 2025 "
    "19h vs 51h >$200 (0.37x; pjm-94 0h/0.00x) with RT companions 2/6 (2023), "
    "12/18 (2024), 19/59 (2025) — the tail gain repeats in every year. "
    "Temp-derate cost to ST_GAS volume is -0.05/-0.01/-0.19 TWh/yr on "
    "8.4/8.1/11.7 (class <2% of ISO load, non-gated) — trivial next to the "
    "class's honest -4.3/-2.6 TWh CAMPD-outage-capped residual, which carries "
    "over from pjm-94 untouched. D-1/D-2/D-4/D-5/D-9/D-10 all PASS; E9 "
    "keeper-vs-twin registered (2026-07-09-pjm-95-ablation-twin). OPEN: (1) C1 "
    "CC_REGULAR 2023 -14.1 / 2024 +10.25 TWh (shared pjm-90-lineage miss, the "
    "load-bearing blocker); (2) C3a/C3c 2025 level+tail residual — the per-gen "
    "ORDC/reserve scarcity item (G-20 Phase 2); (3) PJM-fleet measured "
    "validation of the temp-derate slopes (see temp_dependent_derate ledger "
    "entry; ERCOT's own-fleet refutation is ERCOT-only per rule 24)."
)


def main() -> None:
    """Write the pjm-95 attestation from the pjm-94 source with the temp-derate entry."""
    att = json.loads(SRC.read_text())

    att["governance"]["attested_by"] = GOV_ATTESTED_BY
    att["governance"]["note"] = att["governance"]["note"] + GOV_NOTE_SUFFIX
    att["governance"]["residuals_note"] = RESIDUALS_NOTE

    entries = att["free_parameters"]["entries"]
    entries = [
        e
        for e in entries
        if e.get("name") != "temp_dependent_derate[all-ISO mechanism, PJM keeper use]"
    ]
    entries.append(TEMP_DERATE_ENTRY)
    att["free_parameters"]["entries"] = entries
    att["free_parameters"]["seeded"] = (
        att["free_parameters"]["seeded"]
        + " | pjm-95 (2026-07-09): + temp_dependent_derate (zero-DOF "
        "physical-literature curve; C3c 0h->19h, C3b 2025 -> PASS; no new free "
        "parameter)."
    )

    DST.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {DST}")


if __name__ == "__main__":
    main()
