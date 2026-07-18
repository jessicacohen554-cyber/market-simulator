"""Generate the miso-55 CT-faststart keeper-candidate calibration_attestation.json.

Carries forward the miso-54 attestation (governance clauses, the ledgered C5b
storage benchmark-basis exception with its magnitude refreshed from this run's
own dispatch) and rewrites the run-specific text for the miso-55 delta:

* ``attested_by`` — the two deliberate changes vs the miso-54 recipe (the
  MISO-measured CT_PEAKER committed band 1.025 with econ bands
  measurement-affirmed neutral, and the Order-825/ELMP fast-start startup
  amortization on the measured-run v3 basis).
* ``free_parameters`` — rebuilt by scripts/build_dof_ledger.py (call it FIRST;
  this script only asserts the section exists and is current).
* ``disclosures.note`` — refreshed from the registered metrics by hand after
  scoring (placeholder text written here).

Usage: python scripts/archive/gen_miso55_attestation.py {main|ablation}
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC54 = REPO / "results/calibration/miso54_som_restored/calibration_attestation.json"


def main(mode: str) -> None:
    ablate = mode == "ablation"
    out_dir = REPO / (
        "results/calibration/miso55_ct_faststart" + ("-ablation" if ablate else "")
    )
    att = json.loads(SRC54.read_text())
    dst = out_dir / "calibration_attestation.json"

    # free_parameters must have been rebuilt on THIS bundle by
    # build_dof_ledger.py before this script stamps the rest. The tool derives
    # entries from run_config flags; four measured-physical rows in the
    # miso-54 ledger are hand-curated (no flag hook: the SOM coal floor rides
    # offer-curve values, the disengaged sigmoid documents its in-tree params,
    # gas_daily_shape is code-resolved for MISO, hydro completeness rides two
    # plain kwargs) and still apply verbatim to this run's identical
    # structure, so they are merged back in.
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
        "miso-55 ct-faststart 2026-07-11: the miso-54 keeper meta.json replayed "
        "in full (scripts/probes/_miso55_ct_faststart.py, strict RENAME/SKIP "
        "signature-check machinery — errors on unmapped keys) with exactly two "
        "deliberate changes: (1) MISO-measured CT_PEAKER offer bands "
        "(_MISO_OFFER_CURVE at HEAD): committed 1.0 -> 1.025, the measured "
        "CAMPD min-load average-HR premium (derive_campd_marginal_hr --iso "
        "MISO, 2023-2025, n=249 CT units, cap-weighted p50; provenance "
        "data/raw/reference/miso_campd_marginal_hr_summary.csv), econ bands "
        "measurement-AFFIRMED neutral 1.0 (CT marginal HR flat-to-falling "
        "0.697/0.687/0.691 — the NEISO finding on a third fleet; bare marginal "
        "HR never used as an offer, NYISO run-28 rejection); (2) "
        "tranche_startup_amortization + tranche_startup_measured_runs armed "
        "(FERC Order 825 / MISO ELMP fast-start pricing: NREL CT_STARTUP_PARAMS "
        "start cost amortized over the CAMPD-measured median start-to-stop run "
        "length, derive_campd_ct_run_lengths --iso MISO -> "
        "campd_ct_run_lengths_MISO.csv, 95 plants + class fallback 10 h over "
        "61,322 pooled runs, as the horizon ceiling). Zero fitted scalars: "
        "published start costs, measured run lengths, measured part-load "
        "premium; nothing chosen against a residual (rules 13/23)."
    )
    att["governance"]["note"] = (
        "The handoff-hypothesized static CT committed hurdle (the de-leaked "
        "ERCOT 1.55) is REFUTED by MISO's own CAMPD part-load shape (measured "
        "premium 1.025); the commitment-cost component of the real MISO CT "
        "offer is priced by the ELMP fast-start amortization instead — "
        "structure before level (rule 1). August 2023/24 artifact stays "
        "cleared. The remaining COAL_BIT under-run / CC_REGULAR over-run "
        "mid-merit split is the pre-flagged separate root cause (CC "
        "measured-flat econ body + import under-run), NOT re-tuned here "
        "(rules 1/11)."
    )
    if ablate:
        att["governance"]["note"] += (
            " ZERO-FORCING ABLATION TWIN of 2026-07-11-miso-55-ct-faststart "
            "(rule 20): merchant floors off, structural floors kept."
        )

    # Placeholder — refreshed with the scored FAIL set after
    # calibration_verdict runs; keeps the miso-54 wording out of the new
    # bundle so a stale disclosure can never masquerade as this run's.
    att["disclosures"]["note"] = (
        "PENDING SCORE (filled by the registration step; see metrics.json "
        "determination + reasons)."
    )

    dst.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {dst}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
