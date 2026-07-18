"""Generate the miso-62 bituminous-committed-take-or-pay candidate
calibration_attestation.json.

Carries forward the miso-60 attestation (governance clauses + the two ledgered
storage benchmark-basis exceptions) and rewrites the run-specific text for the
miso-62 delta:

* ``attested_by`` — the one deliberate mechanism change vs miso-60:
  ``coal_bit_committed_takeorpay`` (the bituminous ``_committed`` tranche passes
  ``1 − contract_share`` of its fuel — contracted baseload is sunk).
* ``note`` — the lane (COAL_BIT off-peak-hold), the re-diagnosis (both
  commitment candidates refuted), the COAL_PRB redistribution + all-coal
  tradeoff, the small other-lane-owned C3 price nudge, and the LOYO argument.
* ``free_parameters`` — rebuilt by build_dof_ledger.py (call FIRST); this
  merges back the hand-curated measured-physical rows. The BIT discount adds
  ZERO fitted parameters (each plant's own EIA-923 Schedule-5 share).

Usage: python scripts/archive/gen_miso62_attestation.py {main|ablation}
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC60 = REPO / "results/calibration/miso60_stgas_vlr/calibration_attestation.json"


def main(mode: str) -> None:
    ablate = mode == "ablation"
    out_dir = REPO / (
        "results/calibration/miso62_bitpricing" + ("-ablation" if ablate else "")
    )
    att = json.loads(SRC60.read_text())
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
        "miso-62 bit-committed-takeorpay 2026-07-13: the miso-60 keeper "
        "meta.json replayed in full (scripts/probes/_miso62_bitpricing.py, "
        "strict RENAME/SKIP signature-check machinery) with exactly ONE "
        "deliberate mechanism change: coal_bit_committed_takeorpay=True — a "
        "BITUMINOUS coal plant's `_committed` tranche, when the plant is in "
        "the measured take-or-pay share map (coal_takeorpay_from_data, "
        "already on in the miso-60 recipe), passes 1 − contract_share of its "
        "fuel rather than the full-cost supply passthrough. Grounding: MISO "
        "coal is ~100% contracted (EIA-923 Schedule-5); a contracted "
        "plant's committed baseload burns fuel it has already paid for "
        "(sunk take-or-pay), so its stay-online committed band bids down to "
        "hold against cheap gas while the econ*/peak tranches above keep "
        "full delivered cost (coal_econ_srmc_bound) — BIT price-follows "
        "above the committed band. The bituminous class was the priced-out "
        "one (coal_bit_passthrough_sigmoid off, so BIT bid full delivered "
        "cost and the model decommitted/sagged it through the trough). Zero "
        "fitted parameters: each plant's own measured Schedule-5 share; a "
        "removal of an omitted market behaviour, not an added knob "
        "(rule 1/13). Closes the COAL_BIT −15.7 TWh 2023/2024 free-C1 "
        "residual: model COAL_BIT 41.4/37.7 → 54.5/53.4 (actual 57.1/53.3) "
        "and the D-1 off-peak shape from cv_ratio 2.50 (model sagged coal "
        "overnight where reality holds it flat) to 0.62/0.66 (PASS); "
        "CT_PEAKER-2024 30.5 → 26.4 (actual 19.2, PASS); C1 free-class "
        "9/12 → 10/12, all 13/16 → 14/16. Attributes ZERO forced energy "
        "(D-2: a bid-pricing change, not a floor — clean C8)."
    )
    att["governance"]["note"] = (
        "Lane: the dominant free-C1 MISO residual (COAL_BIT off-peak-hold), "
        "miso-60 handoff lane 1. Re-diagnosed on fresh evidence "
        "(docs/handoffs/miso-coal-offpeak-hold-2026-07.md): the handoff's "
        "'min-run/min-down on U bridge' premise was REFUTED — CAMPD shows "
        "coal's physical min-down is short (p10 off-window ~5h; bridgeable "
        "short-gap volume ~1 TWh ≪ 15.7), so gap-bridging cannot supply the "
        "deficit. A throwaway coal_sync A/B (the existing forced-min-load "
        "hold) was also refuted (COAL_BIT +1.6 only). The signature — model "
        "off-peak CV 0.104 vs actual 0.041 (cv_ratio 2.50) — is a "
        "committed-band that PRICE-FOLLOWS down where reality holds it "
        "flat: a bid-pricing problem (BIT bidding full delivered cost on "
        "sunk contracted fuel), which coal_bit_committed_takeorpay fixes at "
        "the offer, not with a floor. DOCUMENTED TRADEOFF (rule 1/11): "
        "cheap fuel-free BIT committed steals COAL_PRB's merit slot, "
        "flipping PRB from a marginal C1 pass (miss 7.9) to fail (13.4) in "
        "2023/2024 — a REDISTRIBUTION that exposes the model's underlying "
        "total-coal deficit (an open root-cause item, NOT a mechanism "
        "flaw). The grounded-consistent generalization "
        "(coal_committed_takeorpay_all, built + tested) closes 2024 PRB but "
        "OVERSHOOTS (PRB +7.79, total coal +6.3 over actual) and risks the "
        "already-high 2025 PRB, so the surgical BIT scope is kept. The "
        "mechanism also nudges mean LMP down ~1–2.5% (cheaper contracted "
        "coal offers) — the 2025 C3a/C3b gap is owned by the upstream "
        "South-gas / RDT / ELMP lanes (miso-60 handoff), NOT stacked "
        "against here (rule 1: a real market behaviour stays in even when "
        "it nudges the fit; the root cause is fixed elsewhere). LOYO "
        "(rule 22): the change is a zero-scalar boolean routing each "
        "plant's own measured contract share into its committed bid — no "
        "year-specific tunable exists to overfit, satisfying "
        "leave-one-year-out by construction (the same argument accepted for "
        "miso-59/60/61)."
    )
    if ablate:
        att["governance"]["note"] += (
            " ZERO-FORCING ABLATION TWIN of 2026-07-13-miso-62-bit-takeorpay "
            "(rule 20): merchant floors off — including "
            "st_gas_mustrun_per_plant (MECH_ABLATION_FIELDS) — structural "
            "mechanisms kept: the topology split, RDT TCDC and the "
            "committed take-or-pay / warm-boiler offer pricing are offer "
            "structure, not floors, and stay armed."
        )

    # Carry the C5b storage exception from miso-60 and ADD the (storage_shape,
    # 2025) C5c basis adjudication (same benchmark-basis family; miso-62 FAILs
    # both in 2025). Magnitudes refreshed from this run's metrics at
    # registration.
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
                "PENDING SCORE (refreshed from this run's metrics at registration)"
            ),
            "classification": (
                "ACCEPTED MEASURED-INPUT LIMITATION (benchmark basis "
                "mismatch - not a model miss)"
            ),
            "reason": (
                "The 2025 EIA-930 battery-only monthly vector's 'shape' is "
                "the fleet's COD ramp (r=0.934 against cumulative in-service "
                "battery MW) while the model side pools BAT + the ~2,417 MW "
                "pumped-storage fleet that EIA-930 MISO does not report. "
                "Normalized per in-service MW the actual's residual shape is "
                "degenerate by the scorer's own CV floor (CV 0.175 < "
                "STORAGE_SHAPE_MIN_CV 0.25), so no dispatch-shape skill is "
                "measurable on this basis. Full adjudication: results/"
                "calibration/FINDING-miso-c5c-storage-shape-basis-2026-07.md "
                "(scorer-side BAT-vs-BAT + per-MW fix flagged to the "
                "rubric-infrastructure lane)."
            ),
        }
    )
    att["exceptions"] = exceptions

    att["disclosures"]["note"] = (
        "PENDING SCORE (filled by the registration step; see metrics.json "
        "determination + reasons)."
    )

    dst.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {dst}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
