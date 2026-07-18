"""Generate the miso-74 (Manitoba two-way seam pair) calibration_attestation.json files.

Carries forward the miso-72 keeper attestation (governance clauses + the
hand-curated measured-physical rows build_dof_ledger does not enumerate) and
writes the run-specific text for the Manitoba two-way seam swap and its
same-box base replica.

Sequence (matches the miso-68..73 chain):

1. seed both bundles' ``calibration_attestation.json`` from the miso-72
   keeper attestation (``--seed``),
2. ``python scripts/build_dof_ledger.py <bundle> --iso MISO`` on BOTH bundles
   (rebuilds ``free_parameters`` from each bundle's own run_config — the main
   arm picks up the miso_manitoba_seam measured-physical entry after the
   carried-row merge; the base arm keeps the firm-block lineage),
3. this script (merges back the carried rows + writes the texts).

Adjudication recorded here (2026-07-18 probe reads, main − same-box base; the
base reproduces the registered miso-72 keeper EXACTLY on every gated criterion
— zero box drift). The Manitoba seam is a STRICT IMPROVEMENT over the miso-72
keeper — fewer fails AND more structurally faithful:

* C1 fuelmix FAIL → PASS (all 16/16 classes in band; free 11/12 → 12/12): the
  standing CC_REGULAR-2023 fail recovers −8.33 → −7.23 TWh into band. The
  import-only firm block was OVER-importing (+0.97/+1.64/+2.96 TWh vs measured)
  and displacing domestic CC — a compensating error; the measured two-way seam
  removes it and CC recovers (rule 11 exactly: the estimate was silently
  compensating a domestic deficit).
* C3b ≤0.20 veto (R4) HELD, even IMPROVED (0.183 → 0.181-2025 — the
  supply-removal un-flattening the charter pre-registered); C3a moved toward
  actual every year (−1.4/−7.3/−13.7 → −0.8/−6.7/−13.3 %).
* Structural deliverable: the two-way physics the flat import block cannot
  represent is reproduced — 2025 realizes a net EXPORT (Manitoba −0.38 vs the
  block's +1.96; measured −0.99), per-seam duration RMSE improves every year
  (827/853/737 → 631/636/563 MW) and hourly correlation is restored (nan →
  +0.67/+0.63/+0.52). Zero fitted scalars (retires the 3 firm-block MW values).

Determination stays NOT-YET but improves 3 fails → 2 {C3a-2025, C3c}, BOTH the
irreducible scarcity tail (Phase-A §0: C3a-2025 is ~78% out-of-representation
tail; the maxgen/engagement scarcity is already at its legitimate extent). Per
the pre-registered rule-14 signature (B3) the TOTAL net interchange diagnostic
WORSENED (err −2.31/−4.54/−5.11 → −5.46/−7.38/−7.27 TWh) — the firm block's
over-import was masking the priced-seam (PJM/South) under-import, which
re-attributes to the merit-cap lane (miso-73); it is a diagnostic, not a gated
criterion. The one band miss is B1's annual-net |err| in 2023/2024 (Manitoba
+2.60/+1.37 vs measured +5.39/+3.01): the seam clears economically against the
model's OWN internal price, which sits below the measured DA the ladder is
derived against (the C3a-2025 tail residual), so it under-clears the deep
import rungs — a symptom of the price residual, not a seam defect (2025, where
the price is closest and the flow reverses, lands B1 at +0.61).

Disposition: PROMOTED to keeper (owner-authorized 2026-07-18) — per rules 1/11
the most structurally faithful AND best-scoring MISO surface to date (real
two-way seam physics replacing a known-wrong import-only stopgap; fixes a
load-bearing C1 fail; clears the veto; zero fitted scalars; remaining fails the
irreducible tail). The {Manitoba + merit-cap} composition is the NEXT lane —
it closes the net-interchange volume on top of this keeper (restores the
priced-seam imports the merit-cap was R1-vetoed for, while Manitoba's supply
removal offsets the flattening within the 0.017-pp C3b headroom Manitoba opens).

Usage: python scripts/gen_miso74_attestation.py [--seed]  (after build_dof_ledger)
"""

import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC72 = REPO / "results/calibration/miso72_winter_citygate/calibration_attestation.json"
MAIN = REPO / "results/calibration/miso74_manitoba_seam"
BASE = REPO / "results/calibration/miso74_manitoba_base"

# Hand-curated measured-physical rows carried across the lineage (not
# enumerated by build_dof_ledger from config).
CARRIED = {
    "MISO COAL SOM near-cost offer floor",
    "COAL_SIGMOID_DEFAULTS[MISO]",
    "gas_daily_shape[MISO]",
    "hydro 2025 completeness (backfill 2024 + EIA-930 monthly repin)",
}

ATTESTED_MAIN = (
    "miso-74 Manitoba two-way seam 2026-07-18 (PROMOTED keeper, "
    "owner-authorized — a strict improvement over miso-72): the prior miso-72 "
    "keeper recipe (scripts/run_miso74_manitoba_probe.py — the "
    "miso72_winter_citygate meta.json strict replay via "
    "replay_keeper.build_kwargs) plus ONE change through the generic "
    "prb_overrides channel: miso_manitoba_seam = True. The import-only "
    "annual-flat Manitoba (MHEB) firm block (726/531/224 MW) is REPLACED by a "
    "fourth MEASURED two-way priced seam — the MISO_MANITOBA_SEAM_SPEC bands "
    "priced by the frozen Q-Q ladder MISO_SEAM_LADDER_BY_YEAR['Manitoba'] "
    "(scripts/derive_miso_seam_ladders.py, the same construction as "
    "PJM/SPP/South) and capped by the measured (month x hod) two-way MHEB "
    "deliverability envelope (MISO_SEAM_DIBA['Manitoba']) — reusing the "
    "existing seam machinery end-to-end and composing with "
    "miso_seam_envelope_merit_cap through the shared "
    "inject_miso_seam_flow_limit path (no fork). ZERO new fitted parameters: "
    "the interface limit is physically pinned (measured +2,827 MW import "
    "extreme), the emission factor 0.0 (hydro); it retires the 3 firm-block MW "
    "values. Offline P9 reproduces measured MHEB net flow +/-0.02 TWh/yr incl. "
    "the 2025 net export. Design FROZEN before the build "
    "(docs/handoffs/miso-manitoba-seam-design-2026-07.md §3-§5: bands B1-B7, "
    "refutations R1-R6 all pre-registered)."
)

NOTE_MAIN = (
    "Manitoba two-way seam — PROMOTED keeper, a STRICT improvement over miso-72 "
    "(mechanism-only read = main minus a same-box unchanged-keeper-recipe base "
    "replica; the base reproduces the registered miso-72 keeper EXACTLY on "
    "every gated criterion, zero box drift). SCORES BETTER: fails 3 → 2. C1 "
    "fuelmix FAIL → PASS (all 16/16 in band, free 11/12 → 12/12) — CC_REGULAR-"
    "2023 recovers −8.33 → −7.23 TWh into band: the firm block was over-"
    "importing (+0.97/+1.64/+2.96 vs measured) and displacing domestic CC, a "
    "compensating error the measured two-way seam removes (rule 11). C3b ≤0.20 "
    "veto (R4) HELD and IMPROVED — 0.080/0.124/0.181 all PASS (base "
    "0.080/0.128/0.183; 2025 0.183 → 0.181, the pre-registered supply-removal "
    "un-flattening). C3a moved toward actual every year (−1.4/−7.3/−13.7 → "
    "−0.8/−6.7/−13.3 %). MORE STRUCTURALLY FAITHFUL: the two-way physics the "
    "flat import block cannot represent is reproduced — 2025 realizes a net "
    "EXPORT (Manitoba −0.38 vs block +1.96; measured −0.99), R2 passed; "
    "per-seam duration RMSE improves EVERY year (Manitoba 827/853/737 → "
    "631/636/563 MW) and hourly correlation is restored (flat block nan → "
    "+0.67/+0.63/+0.52; scripts/miso73_perseam_validate.py vs measured "
    "EIA-930). R1 held (2025 Manitoba net moved 2.34 TWh, not inert); R3 held "
    "(no import overshoot); R5 held (max LMP $214.42 < base $247.99, no "
    "fabricated scarcity). The 2 remaining fails {C3a-2025 −13.3%, C3c 0/6/1 "
    "vs RT 30/37/88 (base 1/7/1)} are BOTH the irreducible scarcity tail (Phase-A §0: "
    "C3a-2025 ~78% out-of-representation; maxgen/engagement scarcity already at "
    "its legitimate extent). Per the pre-registered rule-14 signature (B3) the "
    "TOTAL net interchange DIAGNOSTIC worsened (err −2.31/−4.54/−5.11 → "
    "−5.46/−7.38/−7.27 TWh): the firm block's over-import was masking the "
    "priced-seam (PJM/South) under-import — a diagnostic (not a gated "
    "criterion) that re-attributes to the merit-cap lane. The one band miss is "
    "B1's annual-net |err| in 2023/2024 (Manitoba +2.60/+1.37 vs measured "
    "+5.39/+3.01, >1.5): the seam clears economically at the model's OWN "
    "internal price, which sits below the measured DA the ladder is derived "
    "against (the C3a-2025 tail residual), so it under-clears the deep import "
    "rungs — a symptom of the price residual, not a seam defect (2025, where "
    "the price is closest and the flow reverses, lands B1 at +0.61). "
    "C2/C4/C5a/C6/C7/C8 hold (NO new floors — the export envelope only reduces "
    "export). DOF measured-for-measured: the miso_manitoba_seam entry is "
    "measured-physical n_scalars 0 and retires the 3 firm-block MW values "
    "(main 27/2, base 26/2). DISPOSITION: PROMOTED to keeper (owner-authorized "
    "2026-07-18) per rules 1/11 — most structurally faithful AND best-scoring. "
    "NEXT lane: the {Manitoba + merit-cap} composition closes the "
    "net-interchange volume on top of this keeper (restores the priced-seam "
    "imports the merit-cap was R1-vetoed for while Manitoba's supply removal "
    "offsets the flattening within the C3b headroom Manitoba opens)."
)

ATTESTED_BASE = (
    "miso-74 base 2026-07-18 (PROBE drift control): unchanged miso-72 keeper "
    "recipe (miso72_winter_citygate meta.json strict replay via "
    "replay_keeper.build_kwargs, NO override — the Manitoba firm block "
    "intact), solved same-box so the mechanism-only footprint of the paired "
    "main run is main - base, never main - the registered bundle. Reproduces "
    "the registered miso-72 keeper EXACTLY on every gated criterion (C1 "
    "CC_REGULAR-2023 −8.33, C3a-2025 −13.7%, C3b 0.080/0.128/0.183 PASS, C3c "
    "1/7/1 vs RT 30/37/88) — zero box drift, which certifies the paired "
    "mechanism-only read."
)

NOTE_BASE = (
    "Same-box unchanged-recipe drift control for the miso-74 Manitoba two-way "
    "seam probe (the miso-66 drift lesson: mechanism-only = probe - base, "
    "never probe - registered). Manitoba firm block intact. Not a keeper "
    "candidate; registered per rule 15 so the paired read is reproducible from "
    "the dashboard."
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
        "See metrics.json determination + reasons (NOT-YET, fails 3 → 2 vs "
        "miso-72: C1 fuelmix FAIL → PASS; remaining {C3a-2025, C3c} are the "
        "irreducible scarcity tail). PROMOTED keeper — the merit-cap "
        "composition is the next lane to close the net-interchange volume."
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
