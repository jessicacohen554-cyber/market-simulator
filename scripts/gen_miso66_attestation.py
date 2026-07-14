"""Generate the miso-66 candidate calibration_attestation.json.

Carries forward the miso-65 keeper attestation (governance clauses + the two
ledgered storage benchmark-basis exceptions, C5b throughput + C5c 2025 shape)
and rewrites the run-specific text for the miso-66 lane-1 conduct delta:

* ``attested_by`` — the MISO lane-1 regulated-coal conduct complement: the
  miso-65 keeper recipe with the rank-scoped ``coal_bit_committed_takeorpay``
  REPLACED by the conduct-scoped ``coal_committed_takeorpay_regulated`` (rule
  19 reconcile). Zero fitted scalars — a boolean arming measured data.
* ``note`` — the lane, the admissibility argument (rule 13 forward-regenerable
  institutional attribute + measured shares), and the LOYO argument (a
  zero-scalar boolean arming three measured inputs; V1a -> V1b scope fallback
  pre-registered in the design doc before the deciding probe was read).
* ``free_parameters`` — rebuilt by build_dof_ledger.py (call FIRST); this
  merges back the hand-curated measured-physical rows. The change adds ONE
  measured-physical entry (the new flag) and zero fitted scalars -> 19/2.

Usage: python scripts/gen_miso66_attestation.py {main|ablation}
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC65 = REPO / "results/calibration/miso65_outage_regen/calibration_attestation.json"


def main(mode: str) -> None:
    ablate = mode == "ablation"
    out_dir = REPO / (
        "results/calibration/miso66_coalconduct" + ("-ablation" if ablate else "")
    )
    att = json.loads(SRC65.read_text())
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
        "miso-66 coal-conduct 2026-07-14: the MISO lane-1 regulated-coal "
        "conduct complement. The miso-65 KEEPER recipe "
        "(scripts/probes/_miso66_coalconduct.py — the miso-62 meta.json strict "
        "RENAME/SKIP replay + miso_rpe_pricing + unit_outage_short_windows + "
        "class_aware_fuel_price_fallback on the regenerated "
        "campd-unit-outages-MISO.csv) with ONE reconciled swap: the "
        "rank-scoped coal_bit_committed_takeorpay is REPLACED by the "
        "conduct-scoped coal_committed_takeorpay_regulated. The _committed "
        "tranche of a coal plant in the V1b conduct scope (EIA-860 Regulatory "
        "Status RE UNION > 0.5 Schedule-4 cost-of-service ownership by utility "
        "Entity Type I/M/C/P/S/F, operator entity type for sparse-Schedule-4 "
        "plants) passes (1 - contract_share) of its own measured EIA-923 "
        "Schedule-5 take-or-pay share — the identical sunk-contract rule the "
        "_mustrun band and the BIT flag already use; NR merchant committed "
        "bands bid full delivered cost. ZERO fitted scalars: a boolean arming "
        "measured data (MISO SOM Table 7 regulated-vs-merchant conduct split "
        "— regulated self-commit 56%/53% must-run 2023/2024 vs merchant "
        "93%/74% economic; EIA-860 Regulatory Status + Schedule-4 ownership x "
        "Entity Type; EIA-923 Schedule-5 shares; CAMPD committed tranches). "
        "Closes the miso-65 C1-2024 conduct gap {COAL_PRB -10.41 FAIL, "
        "CT_PEAKER +8.30 FAIL} the miso-65 availability truth exposed (rule "
        "15): at $2.19 gas the LP filled missing self-committed coal with CT. "
        "Design + probe evidence: "
        "docs/handoffs/miso-coal-conduct-design-2026-07.md."
    )
    att["governance"]["note"] = (
        "Lane 1 (regulated-coal committed-band conduct). Rule 19 reconcile — "
        "REPLACES the rank-scoped BIT flag rather than stacking a second "
        "mechanism (RE-BIT plants are covered identically; NR-BIT merchants "
        "revert to the economic bidding the SOM measures for them). Rule 17/18 "
        "— a PRICING bid, not a floor (no min-gen row; the LP stays free to "
        "leave the band idle), scoped by an institutional attribute, not a "
        "class-name tuple, and it REMOVES a rank-scoped special case. Rule 13 "
        "(forward-regenerable) — Regulatory Status is a standing institutional "
        "attribute updating each EIA-860 vintage; contract shares regenerate "
        "each EIA-923 Schedule-5 vintage; the discounted bid is "
        "(1-share)xfuel so it moves with the forward fuel trajectory; a "
        "deregulated/retired plant exits the scope; no measured outcome is fed "
        "back (no CEMS generation pinning, no residual scalar). Rule 23 — no "
        "derive script touched; consumes frozen artifacts (re-derive triggers: "
        "new EIA-860 vintage for the scope set, new EIA-923 Schedule-5 vintage "
        "for the shares, new SOM publication for the conduct citation). LOYO "
        "(rule 22): by construction — a zero-scalar boolean arming three "
        "measured inputs (the miso-59..64 accepted lineage argument), and all "
        "three years were probed A/B (exceeds the LOYO-estimation minimum). "
        "The single scope decision made against probe evidence (V1a RE-only -> "
        "V1b RE UNION cost-of-service majority) followed a fallback "
        "pre-declared in the design doc (committed 8bc5b67) BEFORE the deciding "
        "2023 COAL_BIT probe was read (caiso-81 discipline), not residual "
        "tuning."
    )
    if ablate:
        att["governance"]["note"] += (
            " ZERO-FORCING ABLATION TWIN of 2026-07-14-miso-66-coalconduct "
            "(rule 20): merchant floors off — including st_gas_mustrun_per_plant "
            "(MECH_ABLATION_FIELDS) — structural mechanisms kept: the topology "
            "split, RDT TCDC + RPE violation pricing, the outage overlays (incl. "
            "the short-window channel and the regenerated >= 5-day extract), the "
            "class-aware fuel-price donor, AND the regulated committed-band "
            "take-or-pay pricing (coal_committed_takeorpay_regulated) — the last "
            "is an offer PRICING input, not a floor, so it stays ARMED (the "
            "miso-62 precedent for pricing inputs; the twin only zeroes forcing "
            "floors)."
        )

    att["disclosures"]["note"] = (
        "PENDING SCORE (filled by the registration step; see metrics.json "
        "determination + reasons)."
    )

    dst.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {dst}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
