"""Generate the miso-56 measured-scarcity candidate calibration_attestation.json.

Carries forward the miso-55 attestation (governance clauses, the ledgered C5b
storage benchmark-basis exception with its magnitude refreshed from this run's
own dispatch) and rewrites the run-specific text for the miso-56 delta:

* ``attested_by`` — the two deliberate changes vs the miso-55 recipe (the
  measured hourly OR requirement basis and the condition-keyed fast-start
  amortization horizons).
* ``free_parameters`` — rebuilt by scripts/build_dof_ledger.py (call it FIRST;
  this script only merges back the hand-curated measured-physical rows).
* ``disclosures.note`` — refreshed from the registered metrics by hand after
  scoring (placeholder text written here).

Usage: python scripts/archive/gen_miso56_attestation.py {main|ablation}
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC55 = REPO / "results/calibration/miso55_ct_faststart/calibration_attestation.json"


def main(mode: str) -> None:
    ablate = mode == "ablation"
    out_dir = REPO / (
        "results/calibration/miso56_measured_scarcity" + ("-ablation" if ablate else "")
    )
    att = json.loads(SRC55.read_text())
    dst = out_dir / "calibration_attestation.json"

    # free_parameters must have been rebuilt on THIS bundle by
    # build_dof_ledger.py before this script stamps the rest. Hand-curated
    # measured-physical rows in the miso-55 ledger (no flag hook) still apply
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
        "miso-56 measured-scarcity 2026-07-11: the miso-55 candidate meta.json "
        "replayed in full (scripts/probes/_miso56_measured_scarcity.py, strict "
        "RENAME/SKIP signature-check machinery — errors on unmapped keys) with "
        "exactly two deliberate changes: (1) miso_measured_reserve_requirements "
        "— the market-wide RBDC family takes the measured hourly cleared "
        "reg+spin+supp series (data/raw/MISO-AS/asm_rt_cleared_mw_<year>."
        "parquet, loader data/miso_reserve_requirements.py; mean 2,447/2,557/"
        "2,642 MW, event-evening raises carried) in place of the flat "
        "fleet-MSSC+400 estimate (~3,438 MW), and the South zonal family takes "
        "the measured South reservation (mean 321/366/477 MW) in place of the "
        "within-zone-MSSC static (~2,196 MW) that fabricated ~1.8 GW of South "
        "withholding — rule-13 measured AS power reservation, rule-14 "
        "mandatory swap; published curve shapes translate with the hourly "
        "requirement (NYISO #1344 convention); (2) "
        "tranche_startup_conditional_runs (fast-start amortization v4) — the "
        "v3 CAMPD-measured run ceiling scales per hour by the class net-load-"
        "percentile band ratio (derive_campd_ct_run_lengths --condition-bands "
        "-> campd_ct_run_bands_MISO.csv: 61,322 runs, band medians "
        "9/11/11/8/6 h, ratios 0.9/1.1/1.1/0.8/0.6, per-year stable), the "
        "ELMP evening-timing element. Zero fitted scalars: measured cleared "
        "reserve, measured run lengths, published NREL start costs, "
        "forward-native net-load-percentile trigger; nothing chosen against a "
        "residual (rules 13/23)."
    )
    att["governance"]["note"] = (
        "Lane-2 scope was adjudicated on measured data BEFORE the build "
        "(FINDING-miso-august-scarcity-2026-07.md §10): DA reserve MCPs never "
        "hit the RDC steps in 2023-24 (max $27) and once in 2025 ($132), so "
        "the model's 0 binding DA RDC hours is structurally correct — no "
        "mechanism was added to force DA reserve scarcity the measured market "
        "does not have. The 2025 price residual's IMM-measured drivers (RDT "
        "S->N congestion $9.31/MWh separation; June-2025 ELMP ex-post "
        "emergency repricing; hour-18 net-load-ramp RT shortage intervals) "
        "are outside this lane and NOT knobbed here (rules 1/11). The "
        "2025-09-30 shortage-pricing redesign (Pricing VOLL $10k / LOLP ORDC "
        "capped $6k) is deferred as provably zero-effect for 2023-2025 "
        "(post-dates every DA scarcity cluster; Q4-2025 DA MCPs <= $55)."
    )
    if ablate:
        att["governance"]["note"] += (
            " ZERO-FORCING ABLATION TWIN of 2026-07-11-miso-56-measured-scarcity "
            "(rule 20): merchant floors off, structural floors kept."
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
