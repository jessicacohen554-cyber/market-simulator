"""Generate the miso-71 (KEEPER CANDIDATE) calibration_attestation.json pair.

Carries forward the miso-70 keeper attestation (governance clauses + the
hand-curated measured-physical rows build_dof_ledger does not enumerate) and
writes the run-specific text for the Midwest sub-regional reserve-holding
family (the engagement-depth lane) and its same-box base replica.

Sequence (matches the miso-68/69/70 chain):

1. seed both bundles' ``calibration_attestation.json`` from the miso-70
   keeper attestation (``--seed``),
2. ``python scripts/build_dof_ledger.py <bundle> --iso MISO`` on BOTH bundles
   (rebuilds ``free_parameters`` from each bundle's own run_config — the main
   arm picks up the miso_midwest_subregional_reserves measured-physical entry
   -> 25 measured / 2 residual after the carried-row merge; the base arm stays
   24/2),
3. this script (merges back the carried rows + writes the texts).

Adjudication recorded here (2026-07-17 probe reads, main − same-box base; the
base reproduces the registered miso-70 keeper EXACTLY on every gated criterion
— zero box drift). Every pre-registered band of the frozen design
(docs/handoffs/miso-engagement-depth-design-2026-07.md §5) HELD:
C3b 0.079/0.124/0.184 IDENTICAL to base (Δ 0.000; 2025 0.184 ≤ 0.20 veto —
R1 held); C3c 1/7/1 vs base 1/6/1 (RT 30/37/88) — the +1 in 2024 is the
Aug-26 Warning window's HE20 lifted to $294 (in-window; R2-clean), 2023/2025
unchanged; C3a-2025 −13.7% (identical, price-neutral in 2025 as pre-declared);
C1 CC_REGULAR-2023 −8.29 (identical, watch); C2/C4/C5a PASS both arms
(C5a Δ ≈ 0.003 Mt); C7/C8 PASS with the same ST_GAS grounded-above-budget
notes (no new floors — a reserve requirement carries no floor-mechanism id).
Reserve fidelity (R2 HELD): the Midwest family dual ≤ $25 in 100/99.93/100 %
of hours, ≥ $200 in 0/5/0 h/yr, ALL inside the declared Aug-26-2024 Warning
window (0 outside declared/measured-scarce). R3 HELD: Jan-14-17-2024 Midwest
dual max $0, 0 h > $50. KEEPER CANDIDATE — same fail set as the keeper
{C1 CC_REGULAR-2023, C3a-2025, C3c×3} with no gated regression and one
additional measured structure at zero fitted scalars (rule 1 / R6). Keeper
swap is owner-only.

Usage: python scripts/archive/gen_miso71_attestation.py [--seed]  (after build_dof_ledger)
"""

import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC70 = REPO / "results/calibration/miso70_tier_pricing/calibration_attestation.json"
MAIN = REPO / "results/calibration/miso71_midwest"
BASE = REPO / "results/calibration/miso71_midwest-base"

# Hand-curated measured-physical rows carried across the lineage (not
# enumerated by build_dof_ledger from config).
CARRIED = {
    "MISO COAL SOM near-cost offer floor",
    "COAL_SIGMOID_DEFAULTS[MISO]",
    "gas_daily_shape[MISO]",
    "hydro 2025 completeness (backfill 2024 + EIA-930 monthly repin)",
}

ATTESTED_MAIN = (
    "miso-71 Midwest sub-regional reserve-holding family 2026-07-17 (KEEPER "
    "CANDIDATE, swap owner-only): the PROMOTED miso-70 keeper recipe "
    "(scripts/probes/_miso71_midwest_reserves.py — the miso70_tier_pricing "
    "meta.json strict replay via replay_keeper.build_kwargs) plus ONE new "
    "mechanism through the generic prb_overrides channel: "
    "miso_midwest_subregional_reserves = True. The MEASURED Midwest "
    "(North+Central) cleared operating-reserve reservation "
    "(data.miso_reserve_requirements 'MISO-Midwest' leg — reg+spin+supp summed "
    "over the two Midwest ASM regions, the same measured-cleared construction, "
    "clock and admissibility as the market-wide and South legs) is held IN the "
    "5 PHYSICAL Midwest model zones (reserve_config.MISO_MIDWEST_ZONES = "
    "MISO-West/Plains/Illinois/Indiana/East — external seam buses excluded by "
    "construction, the F5 precedent), priced at a SINGLE shortfall step = the "
    "published $200/MWh Reserve Procurement Enhancement demand value "
    "(constants.MISO_RPE_DEMAND_VALUE, 2024 SOM §III.B — the demand value of "
    "exactly the sub-regional reserve-deliverability construct), reserve_class "
    "0 NESTED inside the market-wide RBDC (a Midwest reserve MW counts toward "
    "both — the NYISO East ⊂ NYCA template). The per-Reserve-Zone §5.2.1.2 "
    "Zonal ORDC ladder is DELIBERATELY NOT used: the per-zone Zonal ORDC never "
    "separated in 26,280 measured 2023-2025 hours, so pricing a region at its "
    "deep steps would be structure the measured record refutes (rule 1). The "
    "mechanism closes the ledgered 'RPE Only' STR-scarcity gap the "
    "congestion-blind market-wide family leaves open (a cost-min LP otherwise "
    "parks the market-wide requirement in the RDT-trapped South surplus and "
    "converts Midwest headroom to energy in a Midwest event): the base parks "
    "reserve in the South (Jun-23/24-2025 South held 951 MW vs measured ~477, "
    "Midwest held 1,635 vs measured 1,862) and the main forces the measured "
    "Midwest holding (1,862/1,941/2,253 MW across the deep windows), "
    "de-parking the South. ZERO fitted scalars: the series is measured, the "
    "$200 is a cited constant, the zone list is topology. Design: "
    "docs/handoffs/miso-engagement-depth-design-2026-07.md (frozen BEFORE the "
    "build; every expected-delta band + the R1-R6 refutation criteria "
    "pre-registered in §5/§6)."
)

NOTE_MAIN = (
    "Midwest sub-regional reserve-holding family — KEEPER CANDIDATE "
    "(mechanism-only read = main minus a same-box unchanged-keeper-recipe base "
    "replica; the base reproduces the registered miso-70 keeper EXACTLY on "
    "every gated criterion — zero box drift). EVERY pre-registered band of the "
    "frozen design HELD. R1 (C3b veto) HELD: C3b 0.079/0.124/0.184 IDENTICAL "
    "to base (mechanism-only Δ 0.000 all years; 2025 0.184 ≤ 0.20 veto, in the "
    "[0.160,0.195] band). R2 (fabricated scarcity) HELD: the Midwest family "
    "dual is ≤ $25 in 100.00/99.93/100.00 % of hours and reaches the $200 RPE "
    "step in 0/5/0 h/yr, ALL 5 inside the declared Aug-26-2024 Warning window "
    "(0 outside declared-window ∪ measured-RT-scarce). R3 (Jan-2024 "
    "wrong-driver) HELD: Jan-14-17-2024 Midwest dual max $0, 0 h > $50 (the "
    "winter tail is measured NOT-a-reserve-event, reserve MCPs ~$3). In-window "
    "LMP ceiling clean (Aug-26-2024 Midwest LMP max $500.0 = the tier floor, "
    "both arms). C3c 1/7/1 vs base 1/6/1 (RT actual 30/37/88): the +1 in 2024 "
    "is Aug-26 HE20 lifted to $294 — the last declared-Warning-window hour, "
    "R2-clean; 2023 and 2025 unchanged. C3c-2025 stays 1 exactly as "
    "PRE-DECLARED (honesty band [1,26], the PASS [44,176] band NEVER claimed): "
    "the family HOLDS the measured Midwest requirement through the 2025 deep "
    "windows (1,862/1,941 MW held = the measured requirement) but its dual is "
    "$0 there — because the measured cleared series DIPS to 957/851 MW in the "
    "tightest hours (leg (b)), so holding it creates no shortfall. The "
    "remaining C3c-2025 gap is LEDGERED as out-of-representation (the "
    "leg-(b) lower-bound understatement + the sub-hourly Jul-28 40-min "
    "transient + the rejected §A commitment posture), NOT force-closed here "
    "and NOT residual-fitted by undoing the dip (rules 1/13; the NYISO B1 "
    "ledgered-lower-bound precedent). C3a-2025 −13.7% (IDENTICAL to base — "
    "price-neutral in 2025 as pre-declared; the family reallocates reserve at "
    "$0 dual there); C3a-2024 −6.9% PASS both; C1 CC_REGULAR-2023 −8.29 "
    "(IDENTICAL, watch — not this lane's lever); C2/C4/C5a PASS both arms "
    "(C5a mechanism-only Δ ≈ 0.003 Mt, within ±7); C6/C7/C8 PASS with the "
    "same ST_GAS grounded-above-budget notes (NO new floors — a reserve "
    "requirement carries no floor-mechanism id, and the D-2/D-4 regen adds no "
    "row). DOF main 25/2, base 24/2 (+1 measured-physical: the Midwest family "
    "— measured N+C series + published $200, zero new scalars). KEEPER CASE "
    "(rule 1 / R6): the fail set is EXACTLY the keeper's {C1 CC_REGULAR-2023, "
    "C3a-2025, C3c×3} with no gated regression, and ONE additional real "
    "structure at zero fitted scalars — the measured Midwest sub-regional "
    "reserve holding that removes the phantom South-parked peak supply the "
    "congestion-blind market-wide family allowed. A more structurally "
    "faithful run with no criterion regression is the keeper definition — "
    "recommendation to the owner; swap is owner-only. No zero-forcing ablation "
    "twin (rule 20 as amended 2026-07-14)."
)

ATTESTED_BASE = (
    "miso-71 base 2026-07-17 (PROBE drift control): unchanged miso-70 keeper "
    "recipe (miso70_tier_pricing meta.json strict replay via "
    "replay_keeper.build_kwargs, NO override), solved same-box so the "
    "mechanism-only footprint of the paired main run is main - base, never "
    "main - the registered bundle. Reproduces the registered miso-70 keeper "
    "EXACTLY on every gated criterion (C1 CC_REGULAR-2023 −8.29, C3a-2025 "
    "−13.7%, C3b 0.079/0.124/0.184 PASS, C3c 1/6/1 vs RT 30/37/88) — zero box "
    "drift, which certifies the paired mechanism-only read."
)

NOTE_BASE = (
    "Same-box unchanged-recipe drift control for the miso-71 Midwest "
    "sub-regional reserve-holding family probe (the miso-66 drift lesson: "
    "mechanism-only = probe - base, never probe - registered). Not a keeper "
    "candidate; registered per rule 15 so the paired read is reproducible from "
    "the dashboard."
)


def _finish(dst_dir: Path, attested_by: str, note: str) -> None:
    """Merge carried rows into the ledger-rebuilt attestation + write texts."""
    dst = dst_dir / "calibration_attestation.json"
    att = json.loads(dst.read_text())
    src = json.loads(SRC70.read_text())
    fp = att.get("free_parameters")
    if fp:
        have = {e["name"] for e in fp["entries"]}
        for e in src["free_parameters"]["entries"]:
            if e["name"] in CARRIED and e["name"] not in have:
                fp["entries"].append(e)
        fp["n_entries"] = len(fp["entries"])
        fp["n_residual"] = sum(
            1 for e in fp["entries"] if e["identification"] == "residual"
        )
        att["free_parameters"] = fp
    att["governance"]["attested_by"] = attested_by
    att["governance"]["note"] = note
    att["disclosures"]["note"] = (
        "PENDING SCORE (filled by the registration step; see metrics.json "
        "determination + reasons)."
    )
    dst.write_text(json.dumps(att, indent=1) + "\n")
    fpn = att.get("free_parameters", {})
    print(
        f"wrote {dst}  (ledger {fpn.get('n_entries', '?')} entries / "
        f"{fpn.get('n_residual', '?')} residual)"
    )


def seed() -> None:
    """Copy the miso-70 keeper attestation into both bundles (step 1)."""
    for d in (MAIN, BASE):
        shutil.copy(SRC70, d / "calibration_attestation.json")
        print(f"seeded {d / 'calibration_attestation.json'}")


def main() -> None:
    import sys

    if "--seed" in sys.argv:
        seed()
        return
    _finish(MAIN, ATTESTED_MAIN, NOTE_MAIN)
    _finish(BASE, ATTESTED_BASE, NOTE_BASE)


if __name__ == "__main__":
    main()
