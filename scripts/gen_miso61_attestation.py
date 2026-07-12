"""Generate the miso-61 RPE-pricing candidate calibration_attestation.json.

Carries forward the miso-60 attestation (governance clauses, the ledgered C5b
storage benchmark-basis exception with its magnitude refreshed from this run's
own dispatch) and rewrites the run-specific text for the miso-61 delta:

* ``attested_by`` — the one deliberate mechanism change vs the miso-60 keeper
  recipe (miso_rpe_pricing: the published Reserve Procurement Enhancement
  $200/MWh demand value added to both RDT violation tiers — the 2023-2025
  market's measured additive violation pricing, 2024 SOM §II.E/§III.B).
* ``exceptions`` — ADDS the (storage_shape, 2025) ledgered entry adjudicated
  this session (results/calibration/FINDING-miso-c5c-storage-shape-basis-
  2026-07.md): the 2025 actual's monthly "shape" is the battery fleet's COD
  ramp (r=0.934 vs cumulative in-service MW) on a battery-only basis the
  BAT+PS model doesn't share; per-MW the actual is degenerate by the
  scorer's own CV floor. Ledgered caveats total 2 of the budgeted 3.
* ``free_parameters`` — rebuilt by scripts/build_dof_ledger.py (call it FIRST;
  this script only merges back the hand-curated measured-physical rows).
* ``disclosures.note`` — refreshed from the registered metrics by hand after
  scoring (placeholder text written here).

Usage: python scripts/gen_miso61_attestation.py {main|ablation}
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC60 = REPO / "results/calibration/miso60_stgas_vlr/calibration_attestation.json"


def main(mode: str) -> None:
    ablate = mode == "ablation"
    out_dir = REPO / (
        "results/calibration/miso61_rpe_pricing" + ("-ablation" if ablate else "")
    )
    att = json.loads(SRC60.read_text())
    dst = out_dir / "calibration_attestation.json"

    # free_parameters must have been rebuilt on THIS bundle by
    # build_dof_ledger.py before this script stamps the rest. Hand-curated
    # measured-physical rows in the miso-60 ledger (no flag hook) still apply
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
        "miso-61 rpe-pricing 2026-07-12: the miso-60 keeper meta.json "
        "replayed in full (scripts/probes/_miso61_rpe_pricing.py, strict "
        "RENAME/SKIP signature-check machinery — errors on unmapped keys) "
        "with exactly ONE deliberate mechanism change: miso_rpe_pricing=True "
        "— the published Reserve Procurement Enhancement demand value "
        "(constants.MISO_RPE_DEMAND_VALUE, $200/MWh) added to the flow_cost "
        "of both VIOLATION tiers of each one-way RDT link "
        "(transmission.apply_miso_rdt_tcdc; free tier below the derated "
        "modeled limit untouched). Grounding: MISO 'enforces STR "
        "requirements in its two subregions by enforcing reserve "
        "procurement enhancement (RPE) constraints over the RDT' and the "
        "RPE has 'a single demand value of $200 per MWh'; in the 2023-2025 "
        "design the RDT TCDC and RPE demand values 'apply additively' in "
        "real violations — measured subregion-wide $700 spreads ($500+$200) "
        "with small violations overpriced 'by $200 per MWh' ($40+$200=$240) "
        "(2024 MISO SOM §II.E p.9, §III.B pp.51-52; IMM Summer-2025 "
        "quarterly: $41M RDT+RPE congestion, +121% YoY). The IMM's "
        "cap-at-$500 recommendation was NOT implemented in-window; if MISO "
        "adopts it, the re-anchor is date-gated to the tariff change "
        "(rule 23). Zero new scalars: one boolean arming one published "
        "market-design constant. Deliberately conservative, documented "
        "one-way gap: the RPE's STR-scarcity binding channel ('RPE Only' — "
        "it binds with NO RDT violation when importing-subregion STR is "
        "limited, IMM Summer-2025 quarterly p.29) is unrepresented because "
        "the LP carries no STR product, so modeled separation UNDER-states "
        "the measured $9.31 Summer-2025 Midwest-South spread. ALSO this "
        "session (data, not a mechanism): the measured RDT binding record "
        "intaken as the transfer-constraint-binding clean datatype "
        "(MISO {da,rt}_pbc, 2023-2025, hourly DA / 5-min RT shadow prices "
        "by direction) — a VALIDATION series only (rule 13: binding is a "
        "dispatch outcome), upgrading the RDT anchors from SOM annual "
        "aggregates (scripts/probes/_miso61_rdt_anchors.py; the hourly "
        "LIMIT series itself remains unpublished — re-verified, still "
        "data-blocked)."
    )
    att["governance"]["note"] = (
        "Lane scope per the miso-60 handoff (2025 price side, lanes in "
        "order): (1) RPE constraint family — BUILT here; (2) hourly "
        "measured RDT limit intake — re-verified DATA-BLOCKED for the limit "
        "series (RT Data Broker RDT endpoint deprecated without archive; "
        "Data Exchange key-gated; pbc reports carry no limit MW); the "
        "admissible measured series (the pbc BINDING record) is intaken as "
        "validation anchors instead. Measured basis notes recorded ex-ante: "
        "the pbc series is the RDT-PROPER record (RT ~7.5% of 2024 "
        "intervals; DA 8/241/947 binding hours 2023/24/25 S->N) while the "
        "SOM's '>25% of RT intervals' counts the RDT+RPE constraint FAMILY "
        "('Tx Only'/'Both'/'RPE Only', IMM Summer-2025 quarterly p.29) — "
        "the model's single RDT constraint stands in for the family, so its "
        "binding frequency is expected BETWEEN the two measured bases; "
        "model zonal separation compares against measured |shadow| PLUS the "
        "unobserved RPE contribution. Expected direction recorded ex-ante: "
        "violation hours reprice $40->$240 / $500->$700, so the LP "
        "redispatches up to $240 before violating or pays the real "
        "violation price; 2023/24 anchors must HOLD or move toward measured "
        "(separation-when-binding toward ~$3); 2025 moves only to the "
        "extent the model's S->N flow reaches the violation region — "
        "July-2025's monthly gap was pre-adjudicated (FINDING §10) to ELMP "
        "ex-post/emergency constructs + deeper operator derates + the "
        "upstream mid-merit split and is NOT expected to close here. "
        "LOYO (rule 22): the change is a zero-scalar boolean arming one "
        "published tariff constant — no year-specific tunable exists to "
        "overfit, satisfying leave-one-year-out by construction (the same "
        "argument accepted for miso-59/60)."
    )
    if ablate:
        att["governance"]["note"] += (
            " ZERO-FORCING ABLATION TWIN of 2026-07-12-miso-61-rpe-pricing "
            "(rule 20): merchant floors off — including "
            "st_gas_mustrun_per_plant (MECH_ABLATION_FIELDS) — structural "
            "mechanisms kept: the topology split, RDT TCDC, the RPE "
            "violation pricing and the warm-boiler offer exemption are "
            "market structure / offer pricing, not floors, and stay armed."
        )

    # Exceptions ledger: carry the C5b entry (magnitude refreshed post-score)
    # and ADD the (storage_shape, 2025) basis adjudication from this session.
    exceptions = [
        e
        for e in att.get("exceptions", [])
        if not (e.get("criterion") == "storage_shape" and e.get("year") == 2025)
    ]
    exceptions.append(
        {
            "criterion": "storage_shape",
            "year": 2025,
            "metric": "C5c monthly storage dispatch shape (pearson r)",
            "magnitude": (
                "PENDING SCORE (miso-60 read r=0.469 vs floor 0.50; refreshed "
                "from this run's metrics at registration)"
            ),
            "classification": (
                "ACCEPTED MEASURED-INPUT LIMITATION (benchmark basis "
                "mismatch - not a model miss)"
            ),
            "reason": (
                "The 2025 EIA-930 battery-only monthly vector's 'shape' is "
                "the fleet's COD ramp — r=0.934 against cumulative "
                "in-service battery MW (EIA-860: 198->804 MW in-year, 660 of "
                "804 MW carry 2025 Operating Months) — while the model side "
                "pools BAT + the 2,417 MW pumped-storage fleet (~93% of "
                "throughput) that EIA-930 MISO does not report. Normalized "
                "per in-service MW the actual's residual shape is degenerate "
                "by the scorer's own standard (CV 0.175 < "
                "STORAGE_SHAPE_MIN_CV 0.25), so no dispatch-shape skill is "
                "measurable on this basis in either direction. Full "
                "adjudication: results/calibration/"
                "FINDING-miso-c5c-storage-shape-basis-2026-07.md (same "
                "family as the carried C5b exception; scorer-side BAT-vs-BAT "
                "+ per-MW fix flagged to the rubric-infrastructure lane)."
            ),
        }
    )
    att["exceptions"] = exceptions

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
