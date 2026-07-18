"""Generate the miso-60 ST_GAS-VLR-floor candidate calibration_attestation.json.

Carries forward the miso-59 attestation (governance clauses, the ledgered C5b
storage benchmark-basis exception with its magnitude refreshed from this run's
own dispatch) and rewrites the run-specific text for the miso-60 delta:

* ``attested_by`` — the one deliberate mechanism change vs the miso-59 keeper
  recipe (st_gas_mustrun_per_plant: each gas steamer's measured committed
  tranche forced on in its measured top-online_frac system-load window — the
  Entergy MISO-South VLR/self-commitment trace), plus the rule-15 data-bug
  fix to the MISO-South 2025 delivered-gas basis riding along as an input
  correction (counter-directional; documented, not a mechanism).
* ``free_parameters`` — rebuilt by scripts/build_dof_ledger.py (call it FIRST;
  this script only merges back the hand-curated measured-physical rows).
* ``disclosures.note`` — refreshed from the registered metrics by hand after
  scoring (placeholder text written here).

Usage: python scripts/archive/gen_miso60_attestation.py {main|ablation}
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC59 = REPO / "results/calibration/miso59_coal_warm/calibration_attestation.json"


def main(mode: str) -> None:
    ablate = mode == "ablation"
    out_dir = REPO / (
        "results/calibration/miso60_stgas_vlr" + ("-ablation" if ablate else "")
    )
    att = json.loads(SRC59.read_text())
    dst = out_dir / "calibration_attestation.json"

    # free_parameters must have been rebuilt on THIS bundle by
    # build_dof_ledger.py before this script stamps the rest. Hand-curated
    # measured-physical rows in the miso-59 ledger (no flag hook) still apply
    # verbatim to this run's identical structure, so they are merged back in.
    carried = {
        "MISO COAL SOM near-cost offer floor",
        "COAL_SIGMOID_DEFAULTS[MISO]",
        "gas_daily_shape[MISO]",
        "hydro 2025 completeness (backfill 2024 + EIA-930 monthly repin)",
    }
    if dst.exists():
        cur = json.loads(dst.read_text())
        if "free_parameters" in cur:
            fp = cur["free_parameters"]
            have = {e["name"] for e in fp["entries"]}
            for e in att["free_parameters"]["entries"]:
                if e["name"] in carried and e["name"] not in have:
                    fp["entries"].append(e)
            fp["n_entries"] = len(fp["entries"])
            fp["n_residual"] = sum(
                1 for e in fp["entries"] if e["identification"] == "residual"
            )
            att["free_parameters"] = fp

    att["governance"]["attested_by"] = (
        "miso-60 st-gas-vlr-floor 2026-07-12: the miso-59 keeper meta.json "
        "replayed in full (scripts/probes/_miso60_stgas_vlr.py, strict "
        "RENAME/SKIP signature-check machinery — errors on unmapped keys) "
        "with exactly ONE deliberate mechanism change: "
        "st_gas_mustrun_per_plant=True — the ST_GAS leg of the existing "
        "cc_mustrun_per_plant per-plant local-reliability commitment floor "
        "(new gate + mechanism id MECH_ST_GAS_MUSTRUN_PER_PLANT): each gas "
        "steamer's measured committed tranche (thermal_tranches_MISO.csv "
        "committed_pct, CEMS P5-when-online) is forced on in its measured "
        "top-online_frac system-load window; offers untouched (rule 19). "
        "Grounding: CEMS unit-grain forensics (this session) — the Entergy "
        "MISO-South steam fleet is synchronized a supermajority of ALL hours "
        "under VLR/self-commitment (Nine Mile 98.2% with a 414 MW "
        "P5-all-hours floor, Sabine 85.6%, Lewis Creek 87.8%) while the "
        "model ran the class near-dark (~6 vs 16.4 TWh measured South 2025; "
        "classFull -4.2/-5.1/-9.2), serving the South from Plains coal/CC "
        "over an N->S RDT flow — the FINDING §11 2025 direction reversal. "
        "The thermal-tranche derive class-gated the measured all-hours P5 "
        "floor to COAL by assumption; the measurement itself contradicts "
        "the assumption for these plants. Zero new scalars: one boolean; "
        "committed share + online fraction are CAMPD-measured per plant and "
        "re-derive when the record extends (rules 13/23); self-targeting by "
        "measurement (rule 18 — true cyclers publish small fractions and "
        "force little; the CT G-20 overnight rejection does not transfer "
        "because these steamers' evidence is around-the-clock "
        "synchronization). ALSO in this run (rule 15 data-bug fix, "
        "counter-directional): miso_zonal_gas_hub.csv MISO-South 2025 basis "
        "+0.095 -> +0.343 — the committed value subtracted the full-year "
        "Henry Hub mean from a 6-month LA mean (mismatched windows); the "
        "like-for-like formula that reproduces every other cell gives "
        "+0.343. The buggy value FLATTERED South (so basis was not the "
        "starvation driver); the honest correction is kept although it "
        "worsens the residual direction."
    )
    att["governance"]["note"] = (
        "Lane scope per the miso-59 handoff (2025 Southern-gas starvation / "
        "RDT regional reversal): suspects adjudicated in order on measured "
        "data BEFORE the mechanism build — (1) South delivered-gas basis: "
        "construction bug found and fixed, but counter-directional, NOT the "
        "driver; (2) seam import ladders: measured/frozen, no input defect; "
        "(3) ST_GAS representation: ROOT CAUSE (measured always-online "
        "VLR self-commitment invisible to the model). Expected direction "
        "recorded ex-ante: South ST_GAS floors ~976 MW (Nine Mile 467 / "
        "Sabine 303 / Lewis Creek 106 / Little Gypsy 100) -> South supply "
        "+7-8 TWh, 2025 RDT direction toward S->N-dominant, separation "
        "toward the IMM's $9.31, C3a-2025 toward zero, sysvol-2025 gas "
        "toward the ±5% band. Watched, not tuned: the 2023-24 RDT anchors "
        "(S->N mean-flowing ~1.55 GW / separation-when-binding $2.5-2.9), "
        "August 2023/24, D-2 forced-energy budgets — ST_GAS is expected "
        "ABOVE the 30% cap and escalates via rubric v2.2 "
        "grounded-above-budget (D4_WINDOWS row ships with the mechanism; "
        "D-1 shape gates decide). LOYO (rule 22): the change is a "
        "zero-scalar boolean arming per-plant measured quantities pooled "
        "over 2023-2025 — no year-specific tunable exists to overfit, "
        "satisfying leave-one-year-out by construction (the same argument "
        "accepted for miso-59's coal_warm_committed)."
    )
    if ablate:
        att["governance"]["note"] += (
            " ZERO-FORCING ABLATION TWIN of 2026-07-12-miso-60-stgas-vlr "
            "(rule 20): merchant floors off — including "
            "st_gas_mustrun_per_plant itself (MECH_ABLATION_FIELDS) — "
            "structural mechanisms kept: the topology split, RDT TCDC and "
            "the warm-boiler offer exemption are market structure / offer "
            "pricing, not floors, and stay armed."
        )

    # Placeholder — refreshed with the scored FAIL set after
    # calibration_verdict runs.
    att["disclosures"]["note"] = (
        "PENDING SCORE (filled by the registration step; see metrics.json "
        "determination + reasons)."
    )

    dst.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {dst}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
