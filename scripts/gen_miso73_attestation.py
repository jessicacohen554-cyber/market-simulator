"""Generate the miso-73 (REJECTED-PROBE pair) calibration_attestation.json files.

Carries forward the miso-72 keeper attestation (governance clauses + the
hand-curated measured-physical rows build_dof_ledger does not enumerate) and
writes the run-specific text for the G-23 seam-envelope merit-cap composition
fix and its same-box base replica.

Sequence (matches the miso-68..72 chain):

1. seed both bundles' ``calibration_attestation.json`` from the miso-72
   keeper attestation (``--seed``),
2. ``python scripts/build_dof_ledger.py <bundle> --iso MISO`` on BOTH bundles
   (rebuilds ``free_parameters`` from each bundle's own run_config — the main
   arm picks up the miso_seam_envelope_merit_cap composition-gate entry
   -> 27 entries / 2 residual after the carried-row merge; the base arm stays
   26/2),
3. this script (merges back the carried rows + writes the texts).

Adjudication recorded here (2026-07-18 probe reads, main − same-box base; the
base reproduces the registered miso-72 keeper EXACTLY on every gated criterion
— zero box drift). The frozen charter's structural bands ALL HELD while the R1
veto TRIPPED: net interchange error −2.31/−4.54/−5.11 → +0.79/+0.56/+0.68 TWh
(B1 ≤2.5 held, strictly better every year); per-seam PJM −5.84/−9.86/−11.31 →
−0.68/−2.06/−3.44 and South +3.29/+3.30/+4.01 → +0.52/+0.56/+1.41 toward
measured (B2; SPP-2024 |err| 0.38→0.43 the one 0.05-TWh sub-noise exception);
C3a −1.4/−7.3/−13.7 → −2.5/−9.1/−15.8 % (B3 ≤2.5 pp watch held; the rule-14
re-attribution signature); no overshoot past the offline fixed-price bound
(R3); 2025 moved +5.8 TWh (R2 not-inert); max LMP 198.53 — no fabricated
scarcity (R4). BUT C3b 0.081/0.139/**0.200 FAIL-2025** (base 0.080/0.129/
0.183) — the pre-declared R1 hard veto — with C3c 1/7/1 → 1/7/0 (the single
2025 >$200 hour shaved) and C1 CC_REGULAR-2023 −8.33 → −8.73 TWh (restored
imports displace CC). Disposition per the pre-registered R1: both runs
registered, keeper recommendation STAYS miso-72, the flag stays in code
default-off, and the finding re-attributes to the trough/level price-shape
ledger as an open root-cause — the under-priced flat domestic stack cannot
absorb the real measured seam supply without flattening the 2025 duration
curve past the veto.

Usage: python scripts/gen_miso73_attestation.py [--seed]  (after build_dof_ledger)
"""

import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC72 = REPO / "results/calibration/miso72_winter_citygate/calibration_attestation.json"
MAIN = REPO / "results/calibration/miso73_seam_meritcap"
BASE = REPO / "results/calibration/miso73_seam_meritcap-base"

# Hand-curated measured-physical rows carried across the lineage (not
# enumerated by build_dof_ledger from config).
CARRIED = {
    "MISO COAL SOM near-cost offer floor",
    "COAL_SIGMOID_DEFAULTS[MISO]",
    "gas_daily_shape[MISO]",
    "hydro 2025 completeness (backfill 2024 + EIA-930 monthly repin)",
}

ATTESTED_MAIN = (
    "miso-73 G-23 seam-envelope merit-cap composition fix 2026-07-18 "
    "(REJECTED PROBE per the pre-registered R1 veto; keeper stays miso-72): "
    "the PROMOTED miso-72 keeper recipe (scripts/run_miso73_seam_probe.py — "
    "the miso72_winter_citygate meta.json strict replay via "
    "replay_keeper.build_kwargs) plus ONE composition change through the "
    "generic prb_overrides channel: miso_seam_envelope_merit_cap = True. The "
    "measured (month x hod) EIA-930 seam deliverability envelope is applied "
    "with MERIT-ORDER (waterfall) band bounds — band k keeps clip(cap − "
    "(k−1)·step, 0, step), cheap base rungs full-width, seam total capped at "
    "min(cap, limit) exactly — instead of the uniform per-band derate, under "
    "which the seam reaches its cap only when the internal price clears the "
    "MOST EXPENSIVE Q-Q rung. The uniform derate is the G-23 residual root "
    "cause: the offline uniform-derate replay reproduces the miso-72 "
    "keeper's solved priced-seam net ±0.12 TWh in ALL THREE years (frozen "
    "charter docs/handoffs/miso-g23-seam-envelope-composition-design-"
    "2026-07.md §1, derive-only). ZERO new parameters: the envelope values, "
    "p90 percentile, MISO_SEAM_LADDER_BY_YEAR rungs and 8-band grid are "
    "byte-unchanged; the flag is a composition-semantics gate. Design FROZEN "
    "before the build (charter §3-§5: bands B1-B6, refutations R1-R5 all "
    "pre-registered)."
)

NOTE_MAIN = (
    "G-23 seam-envelope merit-cap composition fix — REJECTED PROBE by the "
    "pre-registered R1 veto (mechanism-only read = main minus a same-box "
    "unchanged-keeper-recipe base replica; the base reproduces the "
    "registered miso-72 keeper EXACTLY on every gated criterion — zero box "
    "drift). THE STRUCTURAL DELIVERABLE HELD IN FULL: net interchange error "
    "−2.31/−4.54/−5.11 → +0.79/+0.56/+0.68 TWh (B1 ≤2.5 held, strictly "
    "better every year; totals +38.70/+23.60/+19.63 vs actual "
    "+37.91/+23.04/+18.95); per-seam (scripts/miso73_perseam_validate.py, "
    "vs measured EIA-930): PJM −5.84/−9.86/−11.31 → −0.68/−2.06/−3.44 TWh "
    "and South-export +3.29/+3.30/+4.01 → +0.52/+0.56/+1.41 toward measured "
    "in every year with duration-RMSE improving (PJM 921/1343/1577 → "
    "704/776/970 MW; South 612/566/793 → 438/407/626 MW); SPP-2024 |err| "
    "0.38→0.43 is the one 0.05-TWh sub-noise exception (its duration RMSE "
    "still improves 634→456); South-2025 monthly MAE 368→399 GWh the other "
    "sub-metric miss (annual + duration improve). The remaining net wedge is "
    "the pre-declared out-of-scope Manitoba firm block (+0.97/+1.64/+2.96 "
    "model-over; import-only annual-flat vs the measured two-way seasonal "
    "hydro seam — the next charter). R2 held (2025 moved +5.8 TWh, not "
    "inert); R3 held (no overshoot past the offline fixed-price bound "
    "+39.6/+24.6/+20.9); R4 held (max LMP $198.53, no fabricated scarcity); "
    "R5 held (no price criterion quoted as validation). B3 held: C3a "
    "−1.4/−7.3/−13.7 → −2.5/−9.1/−15.8 % (Δ ≤2.5 pp/yr as pre-registered — "
    "the rule-14 compensating-error signature: the suppressed seam was "
    "masking the domestic price-level miss). BUT R1 TRIPPED: C3b "
    "0.081/0.139/0.200 with 2025 scored FAIL (base 0.080/0.129/0.183; the "
    "0.017 headroom the charter named the riskiest gate) — the restored "
    "~5-8 TWh/yr of mid-price seam supply flattens the 2025 duration curve "
    "past the ≤0.20 veto. Companions: C3c 1/7/1 → 1/7/0 (the single 2025 "
    ">$200 hour shaved — disclosed watch, no tail closure was claimed); C1 "
    "CC_REGULAR-2023 −8.33 → −8.73 TWh (imports displace CC; the standing "
    "watch deepens). C2/C4/C5a/C6/C7/C8 PASS both arms (same ST_GAS "
    "grounded-above-budget notes; NO new floors — the export cap only "
    "reduces export). DOF main 27/2, base 26/2 (+1 composition-gate entry, "
    "ZERO new scalars, zero new measured series). DISPOSITION (pre-declared "
    "in charter §5 R1): registered per rule 15, NOT recommended as keeper — "
    "keeper stays miso-72; miso_seam_envelope_merit_cap stays in code "
    "default-off as the measured-correct composition awaiting the "
    "trough/level shape root-cause (#1347 / trough-shape ledger), which now "
    "carries a MEASURED bound: the domestic stack must steepen enough to "
    "absorb the real seam supply inside the C3b veto. Per rules 11/14 the "
    "accurate composition is NOT reverted and NOT to be offset by seam-side "
    "tuning (no percentile sweep, no ladder edit)."
)

ATTESTED_BASE = (
    "miso-73 base 2026-07-18 (PROBE drift control): unchanged miso-72 keeper "
    "recipe (miso72_winter_citygate meta.json strict replay via "
    "replay_keeper.build_kwargs, NO override), solved same-box so the "
    "mechanism-only footprint of the paired main run is main - base, never "
    "main - the registered bundle. Reproduces the registered miso-72 keeper "
    "EXACTLY on every gated criterion (C1 CC_REGULAR-2023 −8.33, C3a-2025 "
    "−13.7%, C3b 0.080/0.129/0.183 PASS, C3c 1/7/1 vs RT 30/37/88) — zero "
    "box drift, which certifies the paired mechanism-only read."
)

NOTE_BASE = (
    "Same-box unchanged-recipe drift control for the miso-73 G-23 "
    "seam-envelope merit-cap composition-fix probe (the miso-66 drift "
    "lesson: mechanism-only = probe - base, never probe - registered). Not a "
    "keeper candidate; registered per rule 15 so the paired read is "
    "reproducible from the dashboard."
)


def _finish(dst_dir: Path, attested_by: str, note: str) -> None:
    """Merge carried rows into the ledger-rebuilt attestation + write texts."""
    dst = dst_dir / "calibration_attestation.json"
    att = json.loads(dst.read_text())
    src = json.loads(SRC72.read_text())
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
        "See metrics.json determination + reasons (NOT-YET; main adds the "
        "C3b-2025 FAIL per the pre-registered R1 veto)."
    )
    dst.write_text(json.dumps(att, indent=1) + "\n")
    fpn = att.get("free_parameters", {})
    print(
        f"wrote {dst}  (ledger {fpn.get('n_entries', '?')} entries / "
        f"{fpn.get('n_residual', '?')} residual)"
    )


def seed() -> None:
    """Copy the miso-72 keeper attestation into both bundles (step 1)."""
    for d in (MAIN, BASE):
        shutil.copy(SRC72, d / "calibration_attestation.json")
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
