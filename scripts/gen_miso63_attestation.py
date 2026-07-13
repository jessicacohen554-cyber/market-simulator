"""Generate the miso-63 composed-candidate calibration_attestation.json.

Carries forward the miso-62 keeper attestation (governance clauses + the two
ledgered storage benchmark-basis exceptions, C5b throughput + C5c 2025 shape)
and rewrites the run-specific text for the miso-63 delta:

* ``attested_by`` — the TWO deliberate mechanism changes vs the miso-62
  keeper, both separately evidenced and zero-fitted-parameter:
  ``miso_rpe_pricing`` (the miso-61 registered mechanism — the published
  $200/MWh RPE demand value additive on the RDT TCDC violation tiers) and
  ``unit_outage_short_windows`` (< 5-day baseload-coal CEMS outage windows,
  the July-2025 availability layer; docs/DIAGNOSIS-miso-july2025-lmp-2026-07.md).
* ``note`` — the lanes (miso-62 handoff lane 2 composition + the owner's
  2026-07-13 July-2025 directive), the probe evidence, and the LOYO argument.
* ``free_parameters`` — rebuilt by build_dof_ledger.py (call FIRST); this
  merges back the hand-curated measured-physical rows. Neither change adds a
  fitted parameter (a published tariff constant; each unit's own CEMS record).

Usage: python scripts/gen_miso63_attestation.py {main|ablation}
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC62 = REPO / "results/calibration/miso62_bitpricing/calibration_attestation.json"


def main(mode: str) -> None:
    ablate = mode == "ablation"
    out_dir = REPO / (
        "results/calibration/miso63_shortout_rpe" + ("-ablation" if ablate else "")
    )
    att = json.loads(SRC62.read_text())
    dst = out_dir / "calibration_attestation.json"

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
        "miso-63 shortout-rpe 2026-07-13: the miso-62 KEEPER meta.json "
        "replayed in full (scripts/probes/_miso63_shortout_rpe.py, strict "
        "RENAME/SKIP signature-check machinery) with exactly TWO deliberate "
        "mechanism changes, both separately evidenced and zero-fitted-"
        "parameter. (1) miso_rpe_pricing=True — the miso-61 registered "
        "mechanism (2026-07-12-miso-61-rpe-pricing): MISO enforces "
        "subregional STR requirements 'by enforcing reserve procurement "
        "enhancement (RPE) constraints over the RDT' with a single published "
        "$200/MWh demand value applying ADDITIVELY with the RDT TCDC in real "
        "violations (2024 SOM SS II.E / III.B pp.51-52; IMM Summer-2025 "
        "quarterly). One published tariff constant on the violation tiers' "
        "flow_cost; engages only in the constraint's own driver window "
        "(~30 Aug-2024 hours in miso-61; 2023/2025 byte-identical there). "
        "(2) unit_outage_short_windows=True — the sub-5-day baseload-coal "
        "unit-outage channel (campd-unit-outages-short-MISO.csv, 205 "
        "windows 2023-2025): the >= 5-day detector floor makes event-"
        "coincident short forced outages invisible (Jul 28-29 2025: ~2.8 GW "
        "of coal capability offline at the peak block beyond the overlay — "
        "Cayuga 531 MW, Belle River 700 MW at the event itself), while the "
        "own-fleet temp-capability envelope is FLAT (the fleet loses "
        "discrete units under stress; temp-slope derates stay refuted/off). "
        "Identification guards, all measured (no price/residual input): "
        "coal-only detector + unit annual CF >= 0.55 baseload screen + the "
        "revealed-availability in-merit filter (the full-stop override "
        "cannot engage below the 5-day cap); windows strictly below the "
        "floor so the two extracts are disjoint. Each window is the unit's "
        "own CEMS record — zero fitted parameters "
        "(docs/DIAGNOSIS-miso-july2025-lmp-2026-07.md)."
    )
    att["governance"]["note"] = (
        "Lanes: (a) the miso-62 handoff lane 2 — compose the registered "
        "miso-61 RPE pricing WITH miso-62 into a combined candidate ('they "
        "don't interact: RPE repriced ~30 Aug-2024 hours; BIT is coal "
        "offers'); (b) the owner's 2026-07-13 July-2025 directive — 'double "
        "check the capacity data (outages, summer derates) ... I don't care "
        "if you test two variables at once'. July-2025 diagnosis "
        "(docs/DIAGNOSIS-miso-july2025-lmp-2026-07.md): model 39.48 vs DA "
        "actual 58.79 (Indiana basis) decomposes into the N-S separation "
        "(~$11, lane 3), broad tightness (~$5) and the scarcity tail "
        "(~$3); no import shortage existed (actual event imports 5-9.6 GW; "
        "the model UNDER-imports 2025 by 5.8 TWh). The short-outage channel "
        "is the availability-truth leg: its throwaway 2025-only A/B "
        "(_miso_shortout_probe, rule-16 diagnostic, never registered) "
        "moved July +0.53 (39.48 -> 40.01), annual +0.27, coal -1.8 TWh "
        "against the 2025 +9.9 over-run, tail unchanged — directionally "
        "right everywhere, insufficient alone (the remaining July gap is "
        "owned by lane 3's North supply-curve depth/cost and the unmodeled "
        "CT/CC event unavailability, which needs a max-gen event registry "
        "intake for identification). Composing it with the RPE is testing "
        "two separately-evidenced real mechanisms, not stacking one "
        "phenomenon (rule 19: availability vs violation pricing). LOYO "
        "(rule 22): both changes are zero-scalar booleans arming a "
        "published tariff constant and each unit's own measured CEMS "
        "windows — no year-specific tunable exists to overfit, satisfying "
        "leave-one-year-out by construction (the argument accepted for "
        "miso-59/60/61/62)."
    )
    if ablate:
        att["governance"]["note"] += (
            " ZERO-FORCING ABLATION TWIN of 2026-07-13-miso-63-shortout-rpe "
            "(rule 20): merchant floors off — including "
            "st_gas_mustrun_per_plant (MECH_ABLATION_FIELDS) — structural "
            "mechanisms kept: the topology split, RDT TCDC + RPE violation "
            "pricing, the committed take-or-pay / warm-boiler offer pricing "
            "and the outage overlays (incl. the short-window channel) are "
            "offer structure / availability inputs, not floors, and stay "
            "armed."
        )

    att["disclosures"]["note"] = (
        "PENDING SCORE (filled by the registration step; see metrics.json "
        "determination + reasons)."
    )

    dst.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {dst}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
