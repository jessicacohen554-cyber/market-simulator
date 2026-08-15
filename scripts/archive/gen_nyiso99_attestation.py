"""Write ``calibration_attestation.json`` for the nyiso-99 PROMOTED arm.

``2026-07-29-nyiso-99-demandfix`` (``results/calibration/nyiso99_demandfix``)
was registered as a gate-passing, KEEPER-RECOMMENDED arm and the promotion was
surfaced to the owner rather than taken by the building session (the NYISO lane
convention since nyiso-96). The OWNER PROMOTED IT on 2026-07-29. This script
builds the C6 attestation the promotion requires (rule 21 [R-DOF]: every keeper
carries a DOF ledger), inheriting the nyiso-98 keeper's UNION'd 22-entry ledger
and adding ONE entry for the arm's single delta.

The delta adds **zero free parameters of any kind**. It is not a mechanism and
not a tunable: it is a source-data repair under rule 14 [R-ACCURATE]. EIA-930
posts some reporting gaps as a literal ``0.0`` MW **value** rather than an
absent row, so they survive the NaN reindex and every loader's
``interpolate().bfill().ffill()`` and are handed to the LP as real load. A
whole balancing authority's metered demand is never 0 MW, so the flag needs no
threshold, no percentile and no margin. ``n_entries`` therefore goes 22 -> 23
while ``n_residual`` stays 6.

Usage:
    python scripts/gen_nyiso99_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
PRIOR_KEEPER = (
    REPO / "results/calibration/nyiso98_nucavail/calibration_attestation.json"
)
DEST = REPO / "results/calibration/nyiso99_demandfix/calibration_attestation.json"

NEW_ENTRY = {
    "name": "EIA-930 demand zero-dropout repair (_screen_demand_dropouts)",
    "where": (
        "market_sim.data.eia930.demand._screen_demand_dropouts — wired into "
        "all six per-BA demand loaders; NOT a ScenarioConfig field (a "
        "source-data repair is not a tunable, so there is nothing to arm)"
    ),
    "identification": "measured-physical",
    "lineage_solves": (
        "0 solves added to the tuning lineage — the repair was built to a "
        "pre-registration (docs/PREREG-nyiso99-import-audit-demand-dropout-"
        "2026-07-29.md, committed AND PUSHED before any LP ran), its blast "
        "radius was measured on the loaders BEFORE solving, and it was "
        "A/B'd ONCE. Nothing was swept and no value was adjusted after the "
        "result — there is no value to adjust."
    ),
    "value": (
        "No parameter. The screen flags demand hours reading EXACTLY 0.0 MW "
        "and linearly interpolates them from their neighbours, the same "
        "repair the pre-existing _screen_demand_spikes and the missing-meter "
        "path already apply. Across all six modeled BAs x 2023-2025 it fires "
        "on exactly five hours, all in NYIS Demand: 2024 h403/6760/6761 and "
        "2025 h354/355. Byte-identical (delta 0.00000 TWh, max |delta| 0.0 "
        "MW) on 16 of the 18 ISO-years; NYISO 2024 +0.05624 TWh (+0.037 %), "
        "NYISO 2025 +0.04345 TWh, 2023 untouched in EVERY ISO."
    ),
    "source": (
        "The artifact is in the source parquet itself (EIA-930 <BA> hourly "
        "extracts). Identified by extending the nyiso-98 zero-block audit "
        "from benchmark series to INPUT series, and corroborated three ways: "
        "the flanking hours read ~17-22 GW; a whole BA's metered demand is "
        "never 0 MW; and the keeper's own solved system_<year>.parquet "
        "reproduces the zeros 1:1 as 0.0 MW of served load. No residual was "
        "consulted (rule 23 [R-FROZEN-DERIVE])."
    ),
    "forward_story": (
        "The repair regenerates identically for any year of any BA from the "
        "source extract alone and responds to changed conditions trivially "
        "(a year with no dropout is a no-op — 16 of 18 ISO-years here). It "
        "is mode-independent: nothing about it is backcast-only, so it "
        "carries no forecast/backcast parity burden (rule 13)."
    ),
    "rule_13_admissibility": (
        "Not an overlay at all. It removes a KNOWN DEFECT from a measured "
        "input series rather than adding information: no measured OUTCOME is "
        "consulted, no residual is targeted, and the repaired quantity "
        "(system demand) is an input the model serves, never a series it is "
        "scored against. Deliberately scoped to DEMAND ONLY, never "
        "interchange — a BA's net interchange legitimately reads 0.0 MW when "
        "its ties are idle (ERCO posts 187/140/113 such hours in 2023/24/25 "
        "on its ~1.2 GW DC ties), so the same screen on an interchange "
        "series would DELETE REAL MEASUREMENTS. That is the rule-14 failure "
        "mode this repair exists to avoid, and the scope line is the whole "
        "of its correctness argument."
    ),
}

ATTESTED_BY = (
    "nyiso-99 OWNER PROMOTION 2026-07-29: the 2026-07-29-nyiso-98-nucavail "
    "keeper recipe re-solved via scripts/replay_keeper.py (which reads the "
    "keeper's own meta.json, so the recipe is reproduced exactly) with ONE "
    "delta — _screen_demand_dropouts, the low-side twin of the existing "
    "_screen_demand_spikes. THE SESSION'S PRIMARY RESULT WAS AN "
    "ADJUDICATION, NOT THIS ARM: matrix section 5.5 item 9 (import hourly "
    "shape) was CLOSED as an attributed C3c symptom, and this repair is the "
    "by-product of the audit that closed it. THE AUDIT CLEARED ITS TARGET — "
    "unlike item 7, the lever queue's premise SURVIVED: EIA-930 NYIS Total "
    "interchange carries 0/6/14 suspect hours against NG:NUC's "
    "1,179/380/117, every one falsified against the INDEPENDENT NYISO MIS "
    "P-32 external schedules (which validate at hourly r 0.910/0.908/0.882 "
    "on the clean hours before being allowed to judge a gap), gap-masking "
    "leaves the item-9 statistic BIT-UNCHANGED (r_hr 0.598/0.624/0.454 -> "
    "0.598/0.624/0.458), and scoring against P-32 instead REPRODUCES it "
    "(0.612/0.611/0.495). NG:WAT clean (0/1/1); NG:OIL's many zeros are "
    "CONFIRMED GENUINE by P-63 (3,074/6,285/7,343). Item 9 was then closed "
    "on attribution: the import node tracks the spread IT IS SHOWN at r "
    "+0.673/+0.686/+0.772 (the seam mechanism is faithful), but that spread "
    "is phase-inverted (r -0.401/-0.236/-0.600) because the seam price is "
    "measured and correct while NYISO's INTERNAL diurnal price swing is "
    "0.58/0.52/0.46 of the real one — i.e. C3c reaching the seam. EXTENDING "
    "THE AUDIT FROM BENCHMARKS TO INPUTS IS WHAT FOUND THIS ARM'S DEFECT. "
    "THE RULE-14 [R-ACCURATE] CASE: an EIA-930 zero-dropout is not accurate "
    "data, and the model was serving 0 MW of load in five hours New York "
    "drew ~20 GW."
)

RESIDUALS_NOTE = (
    "SCORED EFFECT vs the nyiso-98 keeper, which the arm reproduces exactly "
    "in its unaffected year. EVERY PRE-REGISTERED GATE PASSED. G1 CONTROL "
    "IDENTITY: the screen is a proven no-op in 2023, so the arm's OWN 2023 "
    "year is a same-recipe zero-delta control — max |delta class MW| "
    "0.000000 and max |delta price| 0.000000 $/MWh against the keeper. That "
    "single number also discharges two side questions: this container "
    "reproduces the keeper bit-for-bit, and caiso-139's "
    "dump_cost_full_offer_domain (which landed on main mid-session) is "
    "confirmed byte-neutral for NYISO. G2: hours with total served demand "
    "== 0 go 3 -> 0 (2024) and 2 -> 0 (2025). G3 LEVEL NEUTRALITY: served "
    "energy rises by the repaired wedge and nothing else, +0.05624 / "
    "+0.04345 TWh, matching the pre-solve loader measurement exactly. "
    "THE HEADLINE IS THE DUMP AND THE PRICE, NOT THE ENERGY: those five "
    "hours were 100 % OF THE KEEPER'S ENTIRE OVERGENERATION DUMP (22,026.6 "
    "MWh in 2024, 15,587.7 MWh in 2025; 2023 has no dropout hour and no "
    "dump at all) and printed -$26.001 IN ALL FIVE ZONES — the dump-cost "
    "optimum — because with demand pinned at zero the must-run stack "
    "(nuclear, run-of-river hydro, the 900 MW firm HQ import floor, wind, "
    "solar) had nowhere to go. Dump goes 22,026.6 -> 0.0 and 15,587.7 -> "
    "0.0 MWh, EXACTLY zero in both years, and the five fabricated "
    "floor-price hours are gone. SLACK STAYS 0.0 MWh IN EVERY YEAR, so the "
    "restored ~20 GW is served by real resources, not shed; max |delta "
    "price| $121.0 (2024) / $110.0 (2025) is those hours repricing off the "
    "dump floor to a real clearing price. Any price-distribution statistic "
    "computed on the previous bundle — negative-price-hour counts, price "
    "minima, the low tail feeding C3a/C3b — carried all five. G4 C1 "
    "PROTECTION: C1 14/14 free 10/10, UNCHANGED; the knife-edge 2023 "
    "CC_REGULAR cell is BIT-UNCHANGED at 32.5119 TWh (-2.79 of +-2.94) "
    "because the screen is a no-op in 2023 — the ISO's tightest cell cannot "
    "move under this delta by construction; 2024 +0.0121 and 2025 +0.0090 "
    "TWh, about 0.4 % of the band. G5 PROTECTIVE GATES: C7 PASS, C8 PASS; "
    "the fragile 2024 ST_GAS cell moves 30.5 -> 30.4 % forced, i.e. TOWARD "
    "the 30 % cap, grounded above budget on both sides. G6 C3c: BIT-"
    "UNCHANGED, 4/0/7 h >$300 vs actual 10/12/42. REPORTED, NOT CLAIMED: "
    "import r_hr moves 0.624 -> 0.623 (2024) and 0.454 -> 0.453 (2025) — "
    "i.e. not at all; the pre-registration said it would not, and this is "
    "NOT an item-9 fix. LOYO (rule 20): not applicable in the fitted sense "
    "— nothing here is a parameter, so there is no value to overfit; the "
    "2023 no-op IS the held-out year and returns bit-identical. No "
    "out-of-training year was touched (NYISO carries no calibration-"
    "complete marker)."
)

OPEN_ITEMS = (
    "(0) OWNER-ACCEPTED MISREPRESENTATION, CARRIED FORWARD UNCHANGED from "
    "the nyiso-96/98 promotions: CT_PEAKER is under-produced with a large "
    "start deficit, and the promoted tranche_startup_amortization mechanism "
    "moves the model's CT offers in the OPPOSITE direction from the fleet's "
    "measured conduct. This keeper does not touch it (2025 CT_PEAKER "
    "+0.00097 TWh, 2024 +0.00068). Per FINDING-nyiso96 section 5 it is a "
    "KNOWN, DELIBERATELY-ACCEPTED misrepresentation, not an open mechanism "
    "lane; un-accepting it requires a published-primary-source mechanism, "
    "never a floor (rule 17; h14-21 windowed floors OFF by owner directive "
    "2026-07-27). (1) C3c remains the SOLE determination blocker, "
    "BIT-UNCHANGED at 4/0/7 h >$300 vs actual 10/12/42: a DIAGNOSED, "
    "UNCLOSED structural limitation of the five-zone representation with an "
    "EMPTY lever queue (nyiso-94/95/96/97 closed every candidate; re-open "
    "conditions FINDING-nyiso97 section 5, none currently satisfiable). "
    "nyiso-99 ADDS ONE ATTRIBUTED SYMPTOM to it rather than a lever: the "
    "import hourly-shape defect (item 9) is C3c seen from the seam — the "
    "model's internal diurnal price swing is 0.58/0.52/0.46 of the real one "
    "while the seam price is measured and correct, so the spread bottoms "
    "out exactly at the peak (-0.1/+1.8/+5.3 $/MWh at the real peak hour vs "
    "a real +5.6/+9.7/+27.0) and the LP stops importing when NY imports "
    "most. (2) C1 2023 CC_REGULAR passes at -2.79 of +-2.94 — margin 0.15 "
    "TWh, still the ISO's TIGHTEST cell, and BIT-UNCHANGED by this keeper. "
    "Any future arm must budget against this narrower headroom. (3) THE "
    "nyiso-98 AUDIT ITEM IS NOW DISCHARGED for import / NG:WAT / NG:OIL and "
    "for all six BAs' Demand column — see the attested_by note. What "
    "remains open from it: the OTHER EIA-930 component series the repo "
    "scores against in the other five ISOs (only Demand was swept "
    "cross-ISO here; their NG:* component series were not). (4) NEW, "
    "REPORTED AND DELIBERATELY NOT ARMED (rule 24): the 4,350 MW "
    "NYISO_simultaneous_import cap is a hand-set estimate that measurement "
    "contradicts — model import tops out at EXACTLY 4,350 MW, never above "
    "it in any hour of any year, and sits on the cap in 548/689/177 h/yr, "
    "while measured net import exceeds it in 287/314/145 h (max 5,929 MW) "
    "and P-32 SCHEDULED flows exceed it in 865/685/388 h (max 7,078 MW). "
    "It is a live rule-14 reconcile item held back because the P-32 limit "
    "sum (~10 GW) is NOT a simultaneous limit but the sum of parallel paths "
    "the five-zone network collapses into one link — rule 14's named "
    "misalignment clause — so it needs a RECONCILED identification and its "
    "own charter, and relaxing the cap alone would only let the model "
    "import more in its wrong-phase overnight hours. (5) Characterisation, "
    "not a lever: 2,970 MW of the 6,580 MW import ladder (45 %) carries a "
    "per-year CONSTANT price with no hourly signal (HQ_hydro, "
    "IESO_Ontario, PJM_shoulder, eastern_mid), and five of seven rungs sit "
    "at their own cap or at zero in most hours. A finer ladder cannot fix a "
    "spread that peaks at the wrong hour. (6) PRE-EXISTING AND UNCHANGED, "
    "INHERITED NOT CAUSED: D-5 forecast/backcast parity FAILs on "
    "nyiso_local_selfsupply ('active backcast-only for this config but NOT "
    "on the declared backcast-overlay list'). The nyiso-98 keeper's own "
    "committed legitimacy_diagnostics.json carries the identical row. It is "
    "a declaration-list gap, not a dispatch defect, and it needs its own "
    "session. (7) Carried from nyiso-96/98: the keeper-lineage meta still "
    "arms dual_fuel_oil_reattribution for NYISO — a recording basis the CLI "
    "has since pinned NEISO-only; dropping it is a zero-dispatch-delta "
    "cleanup for the next re-solve (queue item 10). (8) Carried from "
    "nyiso-98: two 2025 months (Feb, Apr) hit the frozen nuclear SCALE_CLIP "
    "1.25 and reconcile only to -0.62 %/-0.32 %, inside WEDGE_TOL but at "
    "its edge; re-check if a future NRC year lands (rule 23 — data change "
    "only, never a residual)."
)


def main() -> int:
    """Build nyiso-99's attestation from the nyiso-98 keeper's."""
    att = json.loads(PRIOR_KEEPER.read_text())
    gov = dict(att.get("governance", {}))
    gov["attested_by"] = ATTESTED_BY
    gov["residuals_note"] = RESIDUALS_NOTE
    att["governance"] = gov
    att["_open_items"] = OPEN_ITEMS
    fp = att["free_parameters"]
    names = {e["name"] for e in fp["entries"]}
    if NEW_ENTRY["name"] not in names:
        fp["entries"] = [*fp["entries"], NEW_ENTRY]
    fp["seeded"] = (
        "2026-07-29 nyiso-99 — UNION'd forward from the nyiso-98 keeper "
        "ledger (22 entries) and NOT rebuilt (a blind build_dof_ledger.py "
        "rebuild drops the curated measured/published entries — the failure "
        "mode the nyiso-81/87/89/92/96/98 notes all recorded). ONE new "
        "entry: the EIA-930 demand zero-dropout repair. n_residual STAYS 6 "
        "— the entry adds ZERO free parameters of ANY kind. It is not a "
        "mechanism and not a tunable but a source-data repair under rule 14 "
        "[R-ACCURATE]: a whole BA's metered demand is never 0 MW, so the "
        "flag carries no threshold, percentile or margin, and there is no "
        "ScenarioConfig field because there is nothing to arm."
    )
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )
    DEST.write_text(json.dumps(att, indent=1) + "\n")
    print(
        f"wrote {DEST.relative_to(REPO)} — {fp['n_entries']} DOF entries "
        f"({fp['n_residual']} residual-identified)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
