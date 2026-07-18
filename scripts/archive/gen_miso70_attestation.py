"""Generate the miso-70 (KEEPER CANDIDATE) calibration_attestation.json pair.

Carries forward the miso-68 keeper attestation (governance clauses + the
hand-curated measured-physical rows build_dof_ledger does not enumerate) and
writes the run-specific text for the F5 declared-window ELMP emergency-tier
pricing probe (composed with the M-2 measured derates) and its same-box base
replica.

Sequence (matches the miso-68/miso-69 chain):

1. seed both bundles' ``calibration_attestation.json`` from the miso-68
   keeper attestation (``--seed``),
2. ``python scripts/build_dof_ledger.py <bundle> --iso MISO`` on BOTH bundles
   (rebuilds ``free_parameters`` from each bundle's own run_config — the main
   arm picks up the three maxgen/tier measured-physical entries -> 24
   measured / 2 residual after the carried-row merge; the base arm stays
   21/2),
3. this script (merges back the carried rows + writes the texts).

Adjudication recorded here (2026-07-17 probe reads, main − same-box base;
the base reproduces the registered miso-68 keeper EXACTLY on every gated
criterion — zero box drift): every pre-registered band of the frozen design
(docs/handoffs/miso-f5-scarcity-depth-design-2026-07.md §3) HELD. C3b-2024
0.124 (identical to the keeper — the six Aug-26-2024 Warning hours print
exactly the $500 Tier-1 floor and land on the under-shooting August mean's
correct side, where miso-69's uncapped $1,841-1,985 block broke the 0.20
veto at 0.203); C3b-2025 mechanism-only −0.009; C3c 1/6/1 vs bands
[0,3]/[4,10]/[1,8]; C3a-2025 −14.3% -> −13.7%; in-window ceiling clean
(max = $500.0); zero out-of-window footprint; max class move 0.121 TWh.
KEEPER CANDIDATE — same fail set as the keeper {C1 CC_REGULAR-2023,
C3a-2025, C3c x3} with no gated regression and two additional measured/
documented structures at zero fitted scalars (rule 1: most structurally
faithful). Keeper swap is owner-only.

Usage: python scripts/archive/gen_miso70_attestation.py [--seed]  (after build_dof_ledger)
"""

import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC68 = (
    REPO
    / "results/calibration/miso68_cottonwood_mothballs/calibration_attestation.json"
)
MAIN = REPO / "results/calibration/miso70_tier_pricing"
BASE = REPO / "results/calibration/miso70_tier_pricing-base"

# Hand-curated measured-physical rows carried across the lineage (not
# enumerated by build_dof_ledger from config).
CARRIED = {
    "MISO COAL SOM near-cost offer floor",
    "COAL_SIGMOID_DEFAULTS[MISO]",
    "gas_daily_shape[MISO]",
    "hydro 2025 completeness (backfill 2024 + EIA-930 monthly repin)",
}

ATTESTED_MAIN = (
    "miso-70 declared-window ELMP emergency-tier pricing 2026-07-17 (KEEPER "
    "CANDIDATE, swap owner-only): the miso-68 keeper recipe (scripts/probes/"
    "_miso70_tier_pricing.py — the miso68_cottonwood_mothballs meta.json "
    "strict replay via replay_keeper.build_kwargs) with the F5 composition "
    "through the generic prb_overrides channel: unit_outage_maxgen_events = "
    "True (M-2, the miso-69 measured derates) + maxgen_emergency_tier_pricing "
    "= True (NEW — inside a maxgen-events registry window declared at Max Gen "
    "Warning or higher, the declared region's PHYSICAL zones reprice the "
    "energy-balance load slack from the $2,000 bid cap to min(voll, tier "
    "floor): $500 Tier 1 at Warning/Step 1, $1,000 Tier 2 at Step 2+ — the "
    "SOM-footnoted ELMP emergency-supply offer floors, 2023 SOM fn.21 = "
    "2024/2025 SOM fn.17, ladder scoping 2023 SOM p.10-11; external seam "
    "buses excluded — slack there is phantom import supply and the Tier-1 "
    "'call external capacity' leg is already inside the measured seam "
    "interchange; the RBDC/zonal-ORDC curves are never edited, rule 19). "
    "ZERO fitted scalars: the two $ floors are verbatim tariff/SOM values, "
    "the within-window depth is identified by the ladder's own declaration "
    "discipline (2023 SOM p.11 — each level declared only when its MWs are "
    "needed, so the declared level is the measured depth indicator), and "
    "windows/levels/regions are the registry's rows (F4 — never "
    "reconstructed from prices). Tier-alone was pre-adjudicated analytically "
    "dispatch-inert on the keeper stack (design §2 payload proof); "
    "M-2-alone is miso-69 (REJECTED, C3b-2024 0.203). Design: docs/handoffs/"
    "miso-f5-scarcity-depth-design-2026-07.md (frozen BEFORE the build; "
    "every expected-delta band pre-registered in §3)."
)

NOTE_MAIN = (
    "F5 declared-window ELMP emergency-tier pricing composed with the M-2 "
    "measured derates — KEEPER CANDIDATE (mechanism-only read = main minus "
    "a same-box unchanged-recipe base replica; the base reproduces the "
    "registered miso-68 keeper EXACTLY on every gated criterion — zero box "
    "drift). EVERY pre-registered band of the frozen design held: C3b-2024 "
    "0.124, IDENTICAL to the keeper (band [0.124,0.16], projection "
    "0.127-0.138, veto 0.20) — the six Aug-26-2024 Warning hours that broke "
    "miso-69 at $1,841-1,985 (C3b-2024 0.203) now print EXACTLY the $500.0 "
    "Tier-1 floor (in-window ceiling clean; MISO-South stays $284-314 in "
    "five of them — below the floor, correctly untouched, RDT separation "
    "intact — and ~28.5 GWh of Tier-1-priced emergency supply serves the "
    "six hours), and because the model's August-2024 monthly mean UNDER-"
    "shoots the actual, the tier-priced hours land on the correct side and "
    "C3a-2024 improves right-shaped (DA diagnostic -10.3% -> -9.3%) where "
    "miso-69's overshoot 'improved' it wrong-shaped. C3b mechanism-only: "
    "2023 -0.002, 2025 -0.009 (both improved; gate was <= +0.005). C3c "
    "1/6/1 vs bands [0,3]/[4,10]/[1,8] (RT actual 30/37/88): the 2025 deep "
    "windows under-engage exactly as PRE-DECLARED (design §1e/§4.5 — the "
    "tier treatment caps declared-window formation, it never engages; zero "
    "tier slack dispatched in all of 2025; the one 2025 tail hour is the "
    "alert-only Jul-28 $248 hour, correctly untouched) — the engagement-"
    "depth question (Midwest zonal reserve family / measured-cleared "
    "requirement basis / winter fuel security) stays open in its own "
    "pre-named lanes, NOT force-closed here. C3a-2025 -14.3% -> -13.7%; C1 "
    "CC_REGULAR-2023 -8.28 -> -8.29 (watch unchanged — not this lane's "
    "lever); max class energy move 0.121 TWh (<= 0.5 watch); C2/C4/C5a "
    "PASS both arms; C6/C7/C8 PASS with the same ST_GAS grounded-above-"
    "budget notes (no new floors — the channel is a price-side slack "
    "repricing with no floor-mechanism id; off-window pricing effects are "
    "structurally impossible, slack cost EQUALS voll outside the registry "
    "Warning+ windows by construction). KEEPER CASE (rule 1): the fail set "
    "is EXACTLY the keeper's {C1 CC_REGULAR-2023, C3a-2025, C3c x3} with "
    "no gated regression, C3c strictly closer (1/30 - 6/37 - 1/88 vs "
    "0/30 - 4/37 - 0/88), and TWO additional real structures at zero "
    "fitted scalars: measured event-window availability truth (M-2) + the "
    "documented ELMP tier price formation that miso-69 proved missing. A "
    "more structurally faithful run with no criterion regression is the "
    "keeper definition — recommendation to the owner; swap is owner-only. "
    "No zero-forcing ablation twin (rule 20 as amended 2026-07-14)."
)

ATTESTED_BASE = (
    "miso-70 base 2026-07-17 (PROBE drift control): unchanged miso-68 "
    "keeper recipe (miso68_cottonwood_mothballs meta.json strict replay via "
    "replay_keeper.build_kwargs, NO override), solved same-box so the "
    "mechanism-only footprint of the paired main run is main - base, never "
    "main - the registered bundle. Reproduces the registered miso-68 keeper "
    "EXACTLY on every gated criterion (C1 CC_REGULAR-2023 -8.28, C3a-2025 "
    "-14.3%, C3b 0.081/0.124/0.193 PASS, C3c 0/4/0 vs RT 30/37/88) — zero "
    "box drift, which also certifies cross-run comparability to the "
    "miso-69 pair (whose base matched the keeper identically)."
)

NOTE_BASE = (
    "Same-box unchanged-recipe drift control for the miso-70 F5 composed "
    "probe (the miso-66 drift lesson: mechanism-only = probe - base, never "
    "probe - registered). Not a keeper candidate; registered per rule 15 "
    "so the paired read is reproducible from the dashboard."
)


def _finish(dst_dir: Path, attested_by: str, note: str) -> None:
    """Merge carried rows into the ledger-rebuilt attestation + write texts."""
    dst = dst_dir / "calibration_attestation.json"
    att = json.loads(dst.read_text())
    src = json.loads(SRC68.read_text())
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
    """Copy the miso-68 keeper attestation into both bundles (step 1)."""
    for d in (MAIN, BASE):
        shutil.copy(SRC68, d / "calibration_attestation.json")
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
