"""Generate the miso-59 coal-warm-committed candidate calibration_attestation.json.

Carries forward the miso-58 attestation (governance clauses, the ledgered C5b
storage benchmark-basis exception with its magnitude refreshed from this run's
own dispatch) and rewrites the run-specific text for the miso-59 delta:

* ``attested_by`` — the one deliberate change vs the miso-58 keeper recipe
  (coal_warm_committed: the P1 cold-start amortization removed from coal
  committed bands whose mustrun tranche holds the boiler online).
* ``free_parameters`` — rebuilt by scripts/build_dof_ledger.py (call it FIRST;
  this script only merges back the hand-curated measured-physical rows).
* ``disclosures.note`` — refreshed from the registered metrics by hand after
  scoring (placeholder text written here).

Usage: python scripts/archive/gen_miso59_attestation.py {main|ablation}
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC58 = REPO / "results/calibration/miso58_rdt_congestion/calibration_attestation.json"


def main(mode: str) -> None:
    ablate = mode == "ablation"
    out_dir = REPO / (
        "results/calibration/miso59_coal_warm" + ("-ablation" if ablate else "")
    )
    att = json.loads(SRC58.read_text())
    dst = out_dir / "calibration_attestation.json"

    # free_parameters must have been rebuilt on THIS bundle by
    # build_dof_ledger.py before this script stamps the rest. Hand-curated
    # measured-physical rows in the miso-58 ledger (no flag hook) still apply
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
        "miso-59 coal-warm-committed 2026-07-12: the miso-58 keeper meta.json "
        "replayed in full (scripts/probes/_miso59_coal_warm.py, strict "
        "RENAME/SKIP signature-check machinery — errors on unmapped keys) with "
        "exactly ONE deliberate change: coal_warm_committed=True — the P1 "
        "startup-amortization markup (compute_monthly_markup, $100/MW NREL "
        "coal cold-start on the committed band only, amortized over raw P0 "
        "run lengths with no measured ceiling) is exempted for coal bins "
        "whose fuel-free mustrun tranche keeps the boiler online, so "
        "committed-band dispatch is priced as the hot-unit output ramp it "
        "physically is. Grounding: dispatch forensics on the replayed "
        "miso-58 2023 solve measured the fabricated wedge directly (on/off "
        "LMP crossing points: COAL_PRB committed cleared only from $34.6 vs "
        "~$26 static measured-fuel SRMC, COAL_BIT from $43.8 vs ~$29-31, "
        "while the same plants' mustrun bands were online 84-98% of hours), "
        "and the MISO IMM's measured conduct (som-competitive-conduct, "
        "miso-53 adjudication) says offers sit AT cost (system price-cost "
        "markup +3.0%/-2.5%) — self-committed units recover start costs "
        "outside the energy offer. Zero new parameters: one existing "
        "physics-gated boolean (must_run_pct > 0 from the CAMPD-derived "
        "thermal-tranche artifact); nothing chosen against a residual "
        "(rules 1/5/13/23). The ERCOT 98a/98b rejection of this flag was "
        "ERCOT-shaped (2023 coal already calibrated, CT/ST under-running) "
        "and does not cross the ISO boundary (rule 25 symmetry); MISO's "
        "measured residual is its exact mirror (CEMS-basis coal family "
        "-34/-42 TWh 2023/24 with CT_PEAKER +8.8/+16.0 over)."
    )
    att["governance"]["note"] = (
        "Lane scope was adjudicated on measured data BEFORE the build (G-21b "
        "scorer-basis check, 2026-07-12 calibration-log entry): the C2-2025 "
        "sysvol FAIL pair was substantially the documented EIA-930 MISO "
        "coal<->gas attribution swap (~17-21 TWh/yr vs CEMS), so the model "
        "lane targets the REAL 2023/24 mid-merit inversion (coal under / "
        "CC+CT over on the CEMS/classFull basis), not the fabricated 2025 "
        "family miss. Expected direction recorded ex-ante: coal committed "
        "bands re-enter mid-merit at measured-fuel SRMC; COAL_BIT/COAL_PRB "
        "C1 rows close; CC_REGULAR/CT_PEAKER over-runs shrink; C5a CO2 "
        "(-8.4%) closes upward; 2025 movement small (at $3.52 gas the "
        "committed band cleared despite the wedge). Watched, not tuned: the "
        "2023-24 RDT anchors (S->N flow/binding/separation vs 2023/2024 SOM), "
        "2025 RDT direction/separation, August 2023/24, D-2 forced-energy "
        "budgets."
    )
    if ablate:
        att["governance"]["note"] += (
            " ZERO-FORCING ABLATION TWIN of 2026-07-12-miso-59-coal-warm "
            "(rule 20): merchant floors off, structural mechanisms kept — "
            "the topology split, RDT TCDC and the warm-boiler offer "
            "exemption are market structure / offer pricing, not floors, "
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
