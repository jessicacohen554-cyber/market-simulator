"""Write ``calibration_attestation.json`` for the neiso-71 nuclear-availability keeper.

Seeds from the outgoing ``neiso70_ctheatrate_B`` keeper's attestation and
applies exactly the changes neiso-71 earns (precedent:
``scripts/gen_neiso70_attestation.py``):

1. **Governance block** re-attested to this session, naming the single delta
   (``nuclear_unit_availability=true``) and the same-HEAD control it was
   scored against.
2. **Exceptions carried VERBATIM.** C3c is BIT-IDENTICAL between control and
   arm — model 0 tail hours in both, all three years, against the same
   RT actuals (15 / 8 / 20 h) — so the ``price_tail`` ledger entries and the
   other carried exceptions transfer unchanged. No new disposition is created
   and no ledger slot is spent (the neiso-70 / caiso-147 precedent).
3. **DOF ledger** gains one entry for the measured per-reactor daily NRC
   availability, identification ``measured`` — so ``n_entries`` rises by one
   while ``n_residual`` is UNCHANGED at 5. The arm introduces **zero** fitted
   parameters (rule 21 ``[R-DOF]`` / rule 24 ``[R-REGISTRY]``).

Usage::

    PYTHONPATH=.:src python3 scripts/gen_neiso71_attestation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

SRC = REPO / "results/calibration/neiso70_ctheatrate_B/calibration_attestation.json"
DST = REPO / "results/calibration/neiso71_nucavail_B/calibration_attestation.json"

ATTESTED_BY = (
    "neiso-71 nuclear-availability session 2026-07-31 (branch "
    "claude/neiso-71-chp-floor-nuclear-twsx5m): the neiso-70 keeper recipe + ONE "
    "structural delta (nuclear_unit_availability=true) — the "
    "NUCLEAR_MONTHLY_CF_BY_YEAR fleet-month SMEAR replaced on NEISO's three "
    "reactors by the MEASURED per-reactor DAILY availability from the NRC daily "
    "Power Reactor Status reports, with the monthly EIA-923 anchor preserved "
    "exactly (the anchor owns the LEVEL, NRC owns the TIMING). Zero fitted "
    "scalars: the artifact is derived (scripts/data/derive_nuclear_availability.py "
    "--iso NEISO, rule 23 [R-FROZEN-DERIVE]) and its three reconciliation "
    "constants (EVENT_RAW_MAX 0.90, SCALE_CLIP 1.25, WEDGE_TOL 0.01) are "
    "inherited VERBATIM and frozen from the ERCOT deriver — never swept here. "
    "The only code change is an IDENTIFIER CROSSWALK (three NRC_TO_EIA['NEISO'] "
    "rows: Millstone 2/3 -> EIA plant 566 units 2/3, Seabrook 1 -> EIA 6115 "
    "unit 1; 3,355.4 MW), not a tunable. Scored against a SAME-HEAD zero-delta "
    "control (2026-07-31-neiso-71-control) solved at the identical frozen HEAD "
    "464817e, never against the committed keeper. Pre-registered before any "
    "solve: results/calibration/PREREG-neiso71-nuclear-availability-2026-07-31.md "
    "(commit 464817e)."
)

NOTE = (
    "neiso-71 = the neiso-70 keeper recipe with measured per-reactor daily "
    "nuclear availability armed. EVERY pre-registered gate PASSES (G-1 flag "
    "fidelity, G-2 control integrity, G-3 liveness, G-4 single delta, G-5 year "
    "span, plus the P-1 energy-neutrality KILL check) and there are ZERO "
    "criterion status changes vs the same-HEAD control across all nine criteria "
    "— C1 stays all 12/12 / free 8/8 and C3c is BIT-IDENTICAL (model 0h vs RT "
    "15/8/20h), so the price_tail ledger entries below carry over verbatim and "
    "no new ledger slot is spent. THE STRUCTURAL DELIVERABLE: NEISO's 3,355.4 MW "
    "nuclear fleet (~22 % of ISO energy) stops being derated by a UNIFORM "
    "fleet-month factor and instead follows each reactor's measured daily state. "
    "The mis-allocation this removes is large — in 2025 Millstone 2 never fell "
    "below 94 % and Seabrook below 47 % while Millstone 3 took a full refuel, "
    "yet the Apr/May anchor (0.75/0.77) derated all three alike. Liveness: max "
    "|delta class MW| 1,129 / 1,842 / 1,265 (2023/24/25), i.e. 20-37x the 50 MW "
    "floor, while fleet nuclear ENERGY is anchor-preserved to -0.0079 / -0.0006 "
    "/ -0.0313 TWh (tolerance 0.05) — the whole effect is TIMING, exactly as "
    "pre-registered. Because nuclear is nuclear_mustrun-pinned at 0.999+ share, "
    "the overlay moves the must-run FLOOR itself hour-by-hour (min_gen is "
    "clipped to pmax x availability), which is the documented application order. "
    "FIT: the scored C1 total absolute error IMPROVES 2.602 -> 2.521 TWh over "
    "the 12 scored rows (2023+2024; the six 2025 rows are SKIPPED on a "
    "preliminary EIA-923 vintage, 57 % plant reporting). Mean lambda -0.025 / "
    "-0.024 / -0.019 $/MWh; C3c tail hours unchanged. D-2 and D-4 gates PASS in "
    "both arms with every forced share moving <=0.005. REPORTED AGAINST "
    "INTEREST: (a) pre-registered prediction P2's ZONAL half did NOT "
    "materialize — all four NEISO zones clear at an identical mean lambda in "
    "control and arm alike (no binding internal congestion in the annual mean), "
    "so the Connecticut-vs-North separation predicted from Millstone/Seabrook "
    "sitting in different zones is not visible at annual-mean grain; only the "
    "TIMING half of P2 is confirmed. (b) D-1 fails in BOTH arms on the SAME "
    "class/year set (COAL_BIT 2023-2025, ST_GAS 2023) — a pre-existing "
    "condition, not a regression, and C7 shape is SKIPPED for NEISO; within it "
    "2024 COAL_BIT profile_r improves 0.617 -> 0.753 while 2023 COAL_BIT slips "
    "0.600 -> 0.588. (c) At the class level the C1 improvement is mixed and "
    "small (7 rows improve, 6 worsen, 5 unchanged); the headline -0.081 TWh is "
    "a net, not a uniform gain."
)

DOF_ENTRY = {
    "name": "nuclear_unit_availability[NEISO]",
    "where": "run_config.scenario_config.nuclear_unit_availability + "
    "data/raw/nuclear-availability-NEISO.csv",
    "identification": "measured",
    "lineage_solves": "0 residual solves — derived from the NRC daily Power "
    "Reactor Status reports reconciled to the committed EIA-923 monthly anchor, "
    "never swept against a residual",
    "value": {
        "reactors": {
            "Millstone 2": [566, 2],
            "Millstone 3": [566, 3],
            "Seabrook 1": [6115, 1],
        },
        "fleet_mw": 3355.4,
        "rows": 3288,
        "reactor_days_per_year": [365, 366, 365],
        "months_reconciled_within_tolerance": 36,
        "months_dropped_for_wedge": 0,
        "worst_month_off_anchor_pct": -0.70,
        "frozen_constants_inherited_from_ercot_deriver": {
            "EVENT_RAW_MAX": 0.90,
            "SCALE_CLIP": 1.25,
            "WEDGE_TOL": 0.01,
        },
        "check": "--check reports 'nuclear-availability-NEISO.csv reproduces "
        "byte-for-byte'",
    },
    "note": "A reactor power state / refuel window is a physical availability "
    "event — rule 13 [R-MEASURED] admissible as an INPUT, the same class as the "
    "CAMPD fossil outage windows and the already-keeper ERCOT/PJM/NYISO/CAISO "
    "nuclear overlays. It regenerates for a forward year from the static "
    "NUCLEAR_MONTHLY_CF / refuel-block schedule and responds to changed "
    "conditions. It is NOT a measured outcome fed back to close a residual: the "
    "EIA-923 anchor owns the LEVEL (fleet-month energy is preserved to "
    "<=0.031 TWh/yr) and NRC supplies only the TIMING. Per rule 23 "
    "[R-FROZEN-DERIVE] it re-derives ONLY when a new NRC annual file lands, and "
    "that commit must cite the data change. Rule 25 [R-ISO-SCOPE]: the "
    "crosswalk is NEISO's own fleet; no parameter was imported from the "
    "precedent ISOs.",
}


def main() -> int:
    """Write the neiso-71 attestation from the neiso-70 keeper's."""
    att = json.loads(SRC.read_text())

    att["governance"]["attested_by"] = ATTESTED_BY
    att["governance"]["note"] = NOTE

    dof = att["free_parameters"]
    names = {e["name"] for e in dof["entries"]}
    if DOF_ENTRY["name"] not in names:
        dof["entries"].append(DOF_ENTRY)
    dof["n_entries"] = len(dof["entries"])
    # n_residual is UNCHANGED: this arm adds a MEASURED entry, not a fitted one.
    dof["n_residual"] = sum(
        1 for e in dof["entries"] if e["identification"] == "residual"
    )

    DST.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {DST.relative_to(REPO)}")
    print(f"  DOF entries {dof['n_entries']} (residual {dof['n_residual']})")
    print(f"  exceptions carried: {len(att['exceptions'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
