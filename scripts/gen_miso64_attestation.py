"""Generate the miso-64 candidate calibration_attestation.json.

Carries forward the miso-63 keeper attestation (governance clauses + the two
ledgered storage benchmark-basis exceptions, C5b throughput + C5c 2025 shape)
and rewrites the run-specific text for the miso-64 delta:

* ``attested_by`` — the ONE deliberate mechanism change vs the miso-63
  keeper: ``class_aware_fuel_price_fallback`` (the lane-1(b) class-aware F923
  gap-fill donor; docs/DIAGNOSIS-miso-july2025-lmp-2026-07.md §6).
* ``note`` — the lane, the measured evidence, and the LOYO argument.
* ``free_parameters`` — rebuilt by build_dof_ledger.py (call FIRST); this
  merges back the hand-curated measured-physical rows. The change adds no
  fitted parameter (the donor pools are the ISO's own F923 filings).

Usage: python scripts/gen_miso64_attestation.py {main|ablation}
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC63 = REPO / "results/calibration/miso63_shortout_rpe/calibration_attestation.json"


def main(mode: str) -> None:
    ablate = mode == "ablation"
    out_dir = REPO / (
        "results/calibration/miso64_classdonor" + ("-ablation" if ablate else "")
    )
    att = json.loads(SRC63.read_text())
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
        "miso-64 classdonor 2026-07-13: the miso-63 KEEPER config replayed in "
        "full (scripts/probes/_miso64_classdonor.py — the miso-62 meta.json "
        "strict RENAME/SKIP replay + miso_rpe_pricing + "
        "unit_outage_short_windows, both kept armed) with exactly ONE "
        "deliberate mechanism change: class_aware_fuel_price_fallback=True — "
        "the F923 'nearby plant' gap-fill donor pools consult same-class "
        "reporting plants FIRST (same-class state mean, then same-class zone "
        "mean), the class-blind fuel-group-wide pools remaining the fallback. "
        "Measured basis (2024 F923, capacity-weighted): MISO CT filers pay "
        "$4.13/MMBtu vs CC filers $2.57 (+$1.56 small-volume/retail-transport "
        "premium), but the class-blind pool is quantity-weighted and hence "
        "CC-burn-dominated (~$2.6), so the ~33% of CT_PEAKER capacity without "
        "its own filing was priced ~$16-20/MWh below its measured class cost "
        "— feeding the 2024 CT_PEAKER +7.1 TWh economic over-run at PRB's "
        "expense AND July-2025's too-cheap North margin "
        "(docs/DIAGNOSIS-miso-july2025-lmp-2026-07.md §6, lane 1(b)). "
        "No-LP wiring check on the 2024 fleet "
        "(scripts/probes/_miso_classdonor_wiring.py): 12.0 GW of gap-filled "
        "CT_PEAKER moves $3.62 -> $4.48/MMBtu cap-wtd; CC_REGULAR -$0.06 "
        "(it already dominates the blind pool); CT_CHP -$0.26 (industrial "
        "contracts are genuinely cheaper — class fidelity cuts both ways); "
        "unmoved units byte-identical. Zero fitted parameters: the donor "
        "pools are the ISO's own EIA-923 Schedule-5 filings, re-aggregated "
        "by the recipient's own plant class."
    )
    att["governance"]["note"] = (
        "Lane: the miso-63 handoff lane 1 (total-coal deficit root cause), "
        "measured anchor (b) — 'the F923 gas gap-fill donor is CLASS-BLIND + "
        "quantity-weighted'. The fix is a donor-pool correction toward the "
        "measured class cost, not a price lever: no residual is consulted, "
        "and the mechanism regenerates for a forward year from whatever "
        "filings exist (rule 14 admissibility: delivered fuel prices are the "
        "canonical formulaic measured input). Forward story: forecast years "
        "use the AEO trajectory + basis, not F923, so the gate is "
        "backcast-shaping only through the same overlay that already exists; "
        "it changes WHICH measured filings a non-filing plant inherits, "
        "never inventing a price. LOYO (rule 22): a zero-scalar boolean "
        "arming the ISO's own measured filings — no year-specific tunable "
        "exists to overfit, satisfying leave-one-year-out by construction "
        "(the argument accepted for miso-59/60/61/62/63)."
    )
    if ablate:
        att["governance"]["note"] += (
            " ZERO-FORCING ABLATION TWIN of 2026-07-13-miso-64-classdonor "
            "(rule 20): merchant floors off — including "
            "st_gas_mustrun_per_plant (MECH_ABLATION_FIELDS) — structural "
            "mechanisms kept: the topology split, RDT TCDC + RPE violation "
            "pricing, the committed take-or-pay / warm-boiler offer pricing, "
            "the outage overlays (incl. the short-window channel) and the "
            "class-aware fuel-price donor are offer structure / pricing "
            "inputs, not floors, and stay armed."
        )

    att["disclosures"]["note"] = (
        "PENDING SCORE (filled by the registration step; see metrics.json "
        "determination + reasons)."
    )

    dst.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {dst}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
