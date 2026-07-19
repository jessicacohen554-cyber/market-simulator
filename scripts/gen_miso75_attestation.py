"""Generate the miso-75 ({Manitoba + merit-cap} composition pair) calibration_attestation.json files.

Carries forward the miso-74 keeper attestation (governance clauses + the
hand-curated measured-physical rows build_dof_ledger does not enumerate) and
writes the run-specific text for the seam-envelope merit-cap composition and its
same-box {Manitoba only} base.

Sequence (matches the miso-68..74 chain):

1. seed both bundles' ``calibration_attestation.json`` from the miso-74 keeper
   attestation (``--seed``),
2. ``python scripts/build_dof_ledger.py <bundle> --iso MISO`` on BOTH bundles
   (rebuilds ``free_parameters`` from each bundle's own run_config — the main
   arm picks up the miso_seam_envelope_merit_cap measured-physical entry after
   the carried-row merge; both arms keep the miso_manitoba_seam lineage),
3. this script (merges back the carried rows + writes the texts).

Adjudication recorded here (2026-07-18 probe reads, main − same-box base; the
base reproduces the registered miso-74 keeper on every gated criterion — zero
box drift, C3b 2024 0.124 → 0.126 within noise). This is the pre-registered
composition of the miso-74 Manitoba two-way seam (keeper-on) and the miso-73
seam-envelope merit-cap (default-off, R1-vetoed as a standalone on the miso-72
base because it flattened C3b-2025 0.183 → 0.200). Both flags flow through the
shared ``inject_miso_seam_flow_limit`` path (no fork), ZERO fitted scalars. The
pre-registered success case held on both gates:

* R1 (the C3b ≤0.20 veto) HELD every year: 0.082/0.137/0.198 all PASS (base
  0.080/0.126/0.181). 2025 flattened to 0.198 exactly as pre-registered (base
  0.181 + the merit cap's ~+0.017) — Manitoba's 2025 supply removal held it
  0.002 under the veto (tight but PASS).
* B1 (net-interchange volume, the deliverable) STRICTLY closed every year:
  total net err −5.46/−7.38/−7.27 → −0.58/−1.21/−2.40 TWh. B2: every priced
  seam improves every year — PJM −5.36/−9.56/−11.19 → −0.42/−1.69/−3.13, South
  +3.41/+3.42/+4.06 → +0.59/+0.65/+1.47, Manitoba −2.79/−1.64/+0.61 →
  −0.81/−0.67/−0.58 (the merit cap also un-suppresses Manitoba's own deep
  import rungs, fixing the miso-74 B1 annual-net miss), SPP flat/better; per-
  seam duration RMSE better every seam-year. The merit cap restores the priced-
  seam imports the uniform derate suppressed.

Per the pre-registered rule-14 signature (B3) C3a moved DOWN every year
(−0.8/−6.7/−13.3 → −2.5/−8.9/−15.4 %) from the restored net supply — a disclosed
side effect, never the objective, not gated. C3c unchanged (0/6/1 → 0/6/0 vs RT
30/37/88) — the irreducible scarcity tail. R5 held: max LMP fell (main 2025
$152.01 vs base $214.42), no fabricated scarcity. Determination stays NOT-YET,
the same 2 fails {C3a-2025, C3c} — both the irreducible tail (Phase-A §0).

Disposition: keeper-upgrade CANDIDATE, recommended per rules 1/11 (the most
structurally faithful MISO surface — the correct merit-order seam semantics
composed on the correct two-way seam; closes a large net-interchange diagnostic
while holding every gated criterion and the veto; zero fitted scalars). The
swap is OWNER-ONLY — NOT self-promoted; keepers.json stays
2026-07-18-miso-74-manitoba-seam until owner authorization. The one caveat: the
C3b-2025 0.198 headroom to the 0.20 veto is 0.002 (disclosed).

Usage: python scripts/gen_miso75_attestation.py [--seed]  (after build_dof_ledger)
"""

import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC74 = REPO / "results/calibration/miso74_manitoba_seam/calibration_attestation.json"
MAIN = REPO / "results/calibration/miso75_probe_acc/main_final"
BASE = REPO / "results/calibration/miso75_probe_acc/base_final"

# Hand-curated measured-physical rows carried across the lineage (not
# enumerated by build_dof_ledger from config).
CARRIED = {
    "MISO COAL SOM near-cost offer floor",
    "COAL_SIGMOID_DEFAULTS[MISO]",
    "gas_daily_shape[MISO]",
    "hydro 2025 completeness (backfill 2024 + EIA-930 monthly repin)",
    "miso_manitoba_seam (Manitoba MHEB two-way priced seam)",
}

ATTESTED_MAIN = (
    "miso-75 {Manitoba + seam-envelope merit-cap} composition 2026-07-18 "
    "(keeper-upgrade CANDIDATE, owner-only swap — NOT self-promoted): the "
    "miso-74 Manitoba keeper recipe (scripts/run_miso75_composition_probe.py — "
    "the miso74_manitoba_seam meta.json strict replay via "
    "replay_keeper.build_kwargs, so miso_manitoba_seam rides through) plus ONE "
    "change via the generic prb_overrides channel: "
    "miso_seam_envelope_merit_cap = True. The measured (month x hod) seam "
    "deliverability envelope is applied as a merit-order (waterfall) ceiling "
    "ub_k = clip(cap-(k-1)*step, 0, step) over EVERY seam (PJM/SPP/South AND the "
    "two-way Manitoba seam) through the shared "
    "model.transmission.inject_miso_seam_flow_limit path (no fork), replacing "
    "the uniform per-band derate that suppressed the priced-seam imports. ZERO "
    "new fitted parameters — a composition-semantics gate (n_scalars 0): the "
    "envelope and the Q-Q ladder (both already ledgered) are byte-unchanged. "
    "This is the pre-registered composition partner of the miso-74 Manitoba "
    "seam and the miso-73 merit-cap. Design FROZEN before the build "
    "(docs/handoffs/miso-manitoba-meritcap-composition-design-2026-07.md §4-§5: "
    "bands B1-B7, refutations R1-R5 all pre-registered)."
)

NOTE_MAIN = (
    "{Manitoba + merit-cap} composition — keeper-upgrade CANDIDATE (owner-only "
    "swap, NOT self-promoted; mechanism-only read = main minus a same-box "
    "{Manitoba only} base = the miso-74 keeper replica, zero box drift). The "
    "pre-registered success case held on BOTH gates. R1 (the C3b <=0.20 veto) "
    "HELD every year — 0.082/0.137/0.198 all PASS (base 0.080/0.126/0.181); "
    "2025 flattened to 0.198 exactly as pre-registered (base 0.181 + the merit "
    "cap's ~+0.017), Manitoba's 2025 supply removal holding it 0.002 under the "
    "veto (tight but PASS — the disclosed caveat). B1 (net-interchange volume, "
    "the deliverable) STRICTLY closed every year: total net err "
    "-5.46/-7.38/-7.27 -> -0.58/-1.21/-2.40 TWh. B2: every priced seam improves "
    "every year (scripts/miso73_perseam_validate.py vs measured EIA-930) — PJM "
    "-5.36/-9.56/-11.19 -> -0.42/-1.69/-3.13, South +3.41/+3.42/+4.06 -> "
    "+0.59/+0.65/+1.47, Manitoba -2.79/-1.64/+0.61 -> -0.81/-0.67/-0.58 (the "
    "merit cap un-suppresses Manitoba's own deep import rungs, FIXING the "
    "miso-74 B1 annual-net miss while 2025 stays net export), SPP flat/better; "
    "per-seam duration RMSE better every seam-year. Per the pre-registered "
    "rule-14 signature (B3) C3a moved DOWN every year (-0.8/-6.7/-13.3 -> "
    "-2.5/-8.9/-15.4 %) from the restored net supply — a disclosed side effect, "
    "not gated, not the objective. C3c unchanged (0/6/1 -> 0/6/0 vs RT "
    "30/37/88). R5 held: max LMP FELL (main 2025 $152.01 vs base $214.42), no "
    "fabricated scarcity. Determination NOT-YET, same 2 fails {C3a-2025 -15.4%, "
    "C3c} — BOTH the irreducible scarcity tail (Phase-A §0). C1/C2/C4/C5a/C6/C7/"
    "C8 hold (NO new floors — the merit cap only re-shapes existing seam band "
    "availability). DOF measured-for-measured: the "
    "miso_seam_envelope_merit_cap entry is measured-physical n_scalars 0 (main "
    "one entry more than base, zero new scalars, 2 residual unchanged). "
    "DISPOSITION: keeper-upgrade CANDIDATE recommended per rules 1/11 (most "
    "structurally faithful, closes the volume, holds every gate) — OWNER-ONLY "
    "swap, keepers.json stays 2026-07-18-miso-74-manitoba-seam pending owner "
    "authorization."
)

ATTESTED_BASE = (
    "miso-75 base 2026-07-18 (PROBE drift control): the miso-74 keeper recipe "
    "(miso74_manitoba_seam meta.json strict replay via "
    "replay_keeper.build_kwargs, NO merit-cap override — the Manitoba two-way "
    "seam intact, uniform per-band derate), solved same-box so the "
    "mechanism-only footprint of the paired main run is main - base, never "
    "main - the registered bundle. Reproduces the registered miso-74 keeper on "
    "every gated criterion (C3b 0.080/0.126/0.181 PASS, C3a -0.8/-6.7/-13.3 %, "
    "C3c 0/6/1 vs RT 30/37/88, total net interchange err -5.46/-7.38/-7.27 TWh) "
    "— zero box drift (C3b-2024 0.124 -> 0.126 within noise), which certifies "
    "the paired mechanism-only read."
)

NOTE_BASE = (
    "Same-box {Manitoba only} drift control for the miso-75 {Manitoba + "
    "merit-cap} composition probe (the miso-66 drift lesson: mechanism-only = "
    "probe - base, never probe - registered). The miso-74 keeper recipe "
    "unchanged (merit cap OFF). Not a keeper candidate; registered per rule 15 "
    "so the paired read is reproducible from the dashboard."
)


def _finish(dst_dir: Path, attested_by: str, note: str) -> None:
    """Merge carried rows into the ledger-rebuilt attestation + write texts."""
    dst = dst_dir / "calibration_attestation.json"
    att = json.loads(dst.read_text())
    src = json.loads(SRC74.read_text())
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
        "See metrics.json determination + reasons (NOT-YET, same 2 fails as the "
        "miso-74 keeper {C3a-2025, C3c} — the irreducible scarcity tail). "
        "keeper-upgrade CANDIDATE: R1 held (C3b 0.198-2025 <=0.20) and B1 closed "
        "the net-interchange volume; owner-only swap."
    )
    dst.write_text(json.dumps(att, indent=1) + "\n")
    fpn = att.get("free_parameters", {})
    print(
        f"wrote {dst}  (ledger {fpn.get('n_entries', '?')} entries / "
        f"{fpn.get('n_residual', '?')} residual)"
    )


def seed() -> None:
    """Copy the miso-74 keeper attestation into both bundles (step 1)."""
    for d in (MAIN, BASE):
        shutil.copy(SRC74, d / "calibration_attestation.json")
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
