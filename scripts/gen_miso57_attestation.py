"""Generate the miso-57 RDT-congestion candidate calibration_attestation.json.

Carries forward the miso-56 attestation (governance clauses, the ledgered C5b
storage benchmark-basis exception with its magnitude refreshed from this run's
own dispatch) and rewrites the run-specific text for the miso-57 delta:

* ``attested_by`` — the two deliberate changes vs the miso-56 recipe (the
  South-seam external-zone split and the published RDT derate + TCDC tiers).
* ``free_parameters`` — rebuilt by scripts/build_dof_ledger.py (call it FIRST;
  this script only merges back the hand-curated measured-physical rows).
* ``disclosures.note`` — refreshed from the registered metrics by hand after
  scoring (placeholder text written here).

Usage: python scripts/gen_miso57_attestation.py {main|ablation}
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC56 = (
    REPO / "results/calibration/miso56_measured_scarcity/calibration_attestation.json"
)


def main(mode: str) -> None:
    ablate = mode == "ablation"
    out_dir = REPO / (
        "results/calibration/miso57_rdt_congestion" + ("-ablation" if ablate else "")
    )
    att = json.loads(SRC56.read_text())
    dst = out_dir / "calibration_attestation.json"

    # free_parameters must have been rebuilt on THIS bundle by
    # build_dof_ledger.py before this script stamps the rest. Hand-curated
    # measured-physical rows in the miso-56 ledger (no flag hook) still apply
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
        "miso-57 RDT-congestion 2026-07-11: the miso-56 candidate meta.json "
        "replayed in full (scripts/probes/_miso57_rdt_congestion.py, strict "
        "RENAME/SKIP signature-check machinery — errors on unmapped keys) with "
        "exactly two deliberate changes: (1) miso_south_seam_split — the South "
        "seam's reference-price bands re-home onto their own external zone "
        "(transmission.split_miso_south_external_node), severing the shared-"
        "bus wheel that let energy flow South->external->Midwest without "
        "touching any priced band — a fabricated free 3,000 MW bypass around "
        "the RDT contract path, measured by the 2025 diagnostic probe at a "
        "1,255 MW summer mean (1,563 of 2,208 summer hours; 7.7 TWh/yr) while "
        "the RDT S->N link carried 54 MW mean and saturated 13 h/yr; (2) "
        "miso_rdt_tcdc — the static JOA contract limits (3,000 N->S / 2,500 "
        "S->N) become the published operating representation: the 92% default "
        "derate as the free tier and the two-step RDT Transmission Constraint "
        "Demand Curve ($40/MWh at the modeled limit, $500/MWh from 102%, hard "
        "bound at contract) as priced one-way tiers (TransferLink.flow_cost; "
        "2024 MISO SOM §III.B, MISO/SPP JOA Attach. A). Zero fitted scalars: "
        "both mechanisms carry only published market parameters; nothing "
        "chosen against a residual (rules 1/5/13/23)."
    )
    att["governance"]["note"] = (
        "Lane scope was adjudicated on measured data BEFORE the build (2024 "
        "SOM §II.E/III.B; IMM Summer-2025 quarterly pp.4-6/29-31): summer-2025 "
        "RDT flows were predominantly South->North with a $9.31/MWh Midwest-"
        "South separation and $41M RDT+RPE congestion (+121% YoY), while the "
        "model carried ~$0 separation because the shared external bus bypassed "
        "the RDT entirely. The deliberately conservative parameter choice is "
        "the published 92% DEFAULT derate, not the deeper condition-driven "
        "operator derates (utilization averaged 84% of contract when binding "
        "in 2024 — no published hourly derate series exists), so binding-hour "
        "congestion is expected to UNDER-shoot the measured separation rather "
        "than fit a haircut (rule 13). The RPE (Reserve Procurement "
        "Enhancement, $200 demand value, additive with the RDT TCDC in real "
        "violations) is NOT modeled — a documented gap in the same direction "
        "(under-separation). August 2023/24 holds are watched, not tuned: the "
        "derate+TCDC also applies there (RDT bound >25% of RT intervals in "
        "2024 at ~$3/MWh average separation, so mild added separation is the "
        "structurally correct direction)."
    )
    if ablate:
        att["governance"]["note"] += (
            " ZERO-FORCING ABLATION TWIN of 2026-07-11-miso-57-rdt-congestion "
            "(rule 20): merchant floors off, structural floors kept — the "
            "topology split and RDT TCDC are market structure, not floors, "
            "and stay armed."
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
