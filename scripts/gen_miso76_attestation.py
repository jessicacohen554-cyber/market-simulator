"""Generate the miso-76 (loss-surface A/B pair) calibration_attestation.json files.

Carries forward the miso-75 keeper attestation (governance clauses + the
hand-curated measured-physical rows build_dof_ledger does not enumerate) and
writes the run-specific text for the marginal-loss-physics probe and its
same-box miso-75-replica base.

Sequence (matches the miso-68..75 chain):

1. seed both bundles' ``calibration_attestation.json`` from the miso-75 keeper
   attestation (``--seed``),
2. ``python scripts/build_dof_ledger.py <bundle> --iso MISO`` on BOTH bundles
   (rebuilds ``free_parameters`` from each bundle's own run_config — the main
   arm picks up the miso_zonal_loss_surface measured-physical entry after the
   carried-row merge; both arms keep the Manitoba/merit-cap lineage),
3. this script (merges back the carried rows + writes the texts).

Adjudication recorded here (2026-07-19 A/B reads, main − same-box base; the
base reproduces the registered miso-75 keeper on every gated criterion —
C3a −2.5/−8.9/−15.4 %, C3b 0.082/0.137/0.198, C3c 0/6/0 vs RT 30/37/88 —
zero box drift). The FROZEN charter's pre-registered criteria adjudicate the
main arm a REJECTED PROBE:

* R2 (no fabricated separation) TRIPS on East-2025: model annual-mean
  separation −0.066 exceeds 1.0× the measured RT TOTAL mean (+0.033). The
  East−Indiana 2025 monthly surface flips sign 6/6 months (annual net
  −0.0003 dimensionless); a monthly one-way mechanism cannot reproduce the
  near-zero measured annual net that reality's offsetting congestion
  produces — the congestion component is the documented data-blocked M4 gap.
* B1 (the deliverable) lands 5/9 pair-years in [0.5×, 1.5×] of measured DA
  dMLC: 2023 ALL PASS (West 0.57×, Illinois 0.69×, East 1.23×), West-2025
  0.52× PASS; West-2024 0.35× / Illinois-2024 0.47× / Illinois-2025 0.40×
  undershoot (the conservative one-way clamp transmits the DF ratio only in
  typical-direction uncongested marginal hours; realized transmission share
  ≈ 35–70%), East-2025 2.81× overshoots (the cancellation pair-year above).

R1 (the C3b ≤ 0.20 veto) HELD every year — 0.082/0.135/0.198 vs base
0.082/0.137/0.198 (2025 headroom 0.002 unchanged). R3 not inert (moves up to
$0.93). R4 held: C1/C2/C4/C5a/C7/C8 unchanged (C8 ST_GAS grounded-above-
budget, same as the keeper; the loss physics carries NO floor-mechanism id —
D-2 adds no row). B3 disclosure: C3a moved +0.1pp each year (−2.5→−2.4,
−8.9→−8.7, −15.4→−15.3 %) — a side effect, never quoted as validation (R5).
B4 report-only: January MAE Indiana/East/West essentially flat
(−0.34..+0.68). C3c unchanged — the irreducible scarcity tail.

Disposition: REJECTED PROBE per pre-registration (registered per rule 15;
keeper UNCHANGED = 2026-07-18-miso-75-manitoba-meritcap). The mechanism
itself is structurally faithful measured physics and stays merged tier-3
default-OFF (rule 1: a real mechanism is never reverted because a band
tripped — the charter's own R2 verdict governs the run's label, not the
code's existence). The evidenced frontier: loss physics alone closes ~half
the wind-belt separation in-band for 2023 but not uniformly across years;
the remainder needs direction-symmetric loss structure or the congestion
component (M4, own charter).

Usage: python scripts/gen_miso76_attestation.py [--seed]  (after build_dof_ledger)
"""

import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC75 = (
    REPO / "results/calibration/miso75_manitoba_meritcap/calibration_attestation.json"
)
MAIN = REPO / "results/calibration/miso76_loss_surface"
BASE = REPO / "results/calibration/miso76_loss_base"

# Hand-curated measured-physical rows carried across the lineage (not
# enumerated by build_dof_ledger from config).
CARRIED = {
    "MISO COAL SOM near-cost offer floor",
    "COAL_SIGMOID_DEFAULTS[MISO]",
    "gas_daily_shape[MISO]",
    "hydro 2025 completeness (backfill 2024 + EIA-930 monthly repin)",
    "miso_manitoba_seam (Manitoba MHEB two-way priced seam)",
    "miso_seam_envelope_merit_cap (seam envelope merit-order ceiling)",
}

ATTESTED_MAIN = (
    "miso-76 loss-surface probe 2026-07-19 (REJECTED PROBE per the frozen "
    "charter's pre-registered R2): the miso-75 keeper recipe "
    "(miso75_manitoba_meritcap meta.json strict replay via "
    "replay_keeper.build_kwargs) plus ONE change routed through BOTH the "
    "solve kwarg and the generic prb_overrides channel: "
    "miso_zonal_loss_surface = True. The Midwest L1-L6 links split into "
    "one-way pairs (transmission.apply_miso_zonal_loss_links, RDT's "
    "established structure, 0.001 flow tiebreak) and each direction's "
    "receiving-end energy-balance coefficient becomes 1 − eps(month) "
    "(dispatch.build_constraints link_loss), eps derived from MISO's OWN "
    "published per-hub MLC record as the dimensionless marginal "
    "delivery-factor deviation surface (frozen derive "
    "scripts/data/derive_miso_loss_surface.py; per-year rows, DA basis; "
    "offline B1 acceptance 9/9 BEFORE any solve). Losses consume MWh and "
    "zonal duals separate by the measured DF ratio — prices stay LP duals, "
    "ZERO fitted scalars (DOF +1 measured-physical, n_scalars 0). Design "
    "FROZEN before the build (docs/handoffs/miso-nc-price-separation-"
    "design-2026-07.md §4-§6: bands B1-B4, refutations R1-R5 pre-registered)."
)

NOTE_MAIN = (
    "Loss-surface probe — REJECTED PROBE by pre-registration (mechanism-only "
    "read = main minus same-box base = the miso-75 keeper replica, zero box "
    "drift). R2 (no fabricated separation) TRIPPED on East-2025: model "
    "annual-mean separation -0.066 vs measured RT TOTAL +0.033 (the "
    "East-Indiana 2025 monthly surface flips sign 6/6 months, annual net "
    "-0.0003 — reality's offsetting congestion nets the pair to ~zero, and "
    "congestion is the documented data-blocked M4 gap). B1 (the deliverable) "
    "5/9 pair-years in [0.5x,1.5x] of measured DA dMLC: 2023 ALL PASS "
    "(0.57/0.69/1.23), West-2025 0.52 PASS; West-2024 0.35 / Illinois-2024 "
    "0.47 / Illinois-2025 0.40 undershoot — the conservative one-way clamp "
    "transmits the DF ratio only in typical-direction uncongested marginal "
    "hours (realized transmission ~35-70%); East-2025 2.81 overshoots (the "
    "cancellation pair-year). R1 (C3b <=0.20 veto) HELD every year: "
    "0.082/0.135/0.198 (base 0.082/0.137/0.198; the 2025 headroom 0.002 "
    "unchanged). R3 not inert (moves to $0.93). R4 held: C1/C2/C4/C5a/C7/C8 "
    "unchanged (C8 ST_GAS grounded-above-budget, same as the keeper; NO new "
    "floors — the loss physics carries no floor-mechanism id). B3 "
    "disclosure: C3a +0.1pp each year (-2.5->-2.4, -8.9->-8.7, "
    "-15.4->-15.3%) — never quoted as validation (R5; the lane's success "
    "claim was B1 and only B1, and B1 FAILED). B4 report-only: January MAE "
    "Indiana/East/West flat (-0.34..+0.68). C3c unchanged (0/6/0 vs RT "
    "30/37/88) — the irreducible tail. Determination NOT-YET, same 2 fails "
    "as the keeper. DISPOSITION: REJECTED PROBE registered per rule 15; "
    "keeper UNCHANGED (2026-07-18-miso-75-manitoba-meritcap); the mechanism "
    "stays merged tier-3 default-OFF (rule 1 — the charter's R2 verdict "
    "labels the run, not the code). Evidenced frontier: loss physics alone "
    "closes ~half the wind-belt separation (in-band 2023) but not uniformly "
    "across years; the remainder is direction-symmetric loss structure or "
    "the congestion component (M4, contingent own charter)."
)

ATTESTED_BASE = (
    "miso-76 base 2026-07-19 (PROBE drift control): the miso-75 keeper "
    "recipe (miso75_manitoba_meritcap meta.json strict replay via "
    "replay_keeper.build_kwargs, NO loss-surface override), solved same-box "
    "so the mechanism-only footprint of the paired main run is main − base, "
    "never main − the registered bundle. Reproduces the registered miso-75 "
    "keeper on every gated criterion (C3a −2.5/−8.9/−15.4 %, C3b "
    "0.082/0.137/0.198, C3c 0/6/0 vs RT 30/37/88, max LMP $152.01, Midwest "
    "zonal span $0.00 — the flat pool) — zero box drift, which certifies "
    "the paired mechanism-only read."
)

NOTE_BASE = (
    "Same-box miso-75-replica drift control for the miso-76 loss-surface "
    "probe (the miso-66 drift lesson: mechanism-only = probe - base, never "
    "probe - registered). The miso-75 keeper recipe unchanged (loss surface "
    "OFF; Midwest pool exactly flat, span $0.00). Not a keeper candidate; "
    "registered per rule 15 so the paired read is reproducible from the "
    "dashboard."
)


def _finish(dst_dir: Path, attested_by: str, note: str) -> None:
    """Merge carried rows into the ledger-rebuilt attestation + write texts."""
    dst = dst_dir / "calibration_attestation.json"
    att = json.loads(dst.read_text())
    src = json.loads(SRC75.read_text())
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
        "See metrics.json determination + reasons (NOT-YET, same 2 fails as "
        "the miso-75 keeper {C3a-2025, C3c} — the irreducible scarcity "
        "tail). Charter adjudication: REJECTED PROBE (R2 East-2025 trip; B1 "
        "5/9) — keeper unchanged; R1 veto held (C3b-2025 0.198 <= 0.20)."
    )
    dst.write_text(json.dumps(att, indent=1) + "\n")
    fpn = att.get("free_parameters", {})
    print(
        f"wrote {dst}  (ledger {fpn.get('n_entries', '?')} entries / "
        f"{fpn.get('n_residual', '?')} residual)"
    )


def seed() -> None:
    """Copy the miso-75 keeper attestation into both bundles (step 1)."""
    for d in (MAIN, BASE):
        shutil.copy(SRC75, d / "calibration_attestation.json")
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
