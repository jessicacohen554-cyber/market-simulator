"""Generate the miso-68 candidate calibration_attestation.json.

Carries forward the miso-67 keeper attestation (governance clauses + the
hand-curated measured-physical rows build_dof_ledger does not enumerate, and
the two ledgered storage benchmark-basis exceptions C5b throughput + C5c 2025
shape) and rewrites the run-specific text for the mothballed-but-operating
re-carry (the Cottonwood lane):

* ``attested_by`` — the miso-67 keeper recipe with ONE single-delta override:
  ``carry_operating_mothballs = True`` (its own dedicated solve kwarg). The
  gate re-carries each OA unit the canonical 2025ER snapshot's OP filter drops
  for solve year Y iff it is OP in the year-matched EIA-860 vintage_<Y> — the
  zero-DOF vintage-status availability oracle. Zero fitted scalars — a boolean
  arming measured data.
* ``note`` — the admissibility argument (rule 13 forward-regenerable measured
  input; rules 1/11 real-fleet structure, never the phantom) and the
  mechanism-only read (main − same-box base).
* ``free_parameters`` — rebuilt by build_dof_ledger.py (call FIRST); this
  merges back the hand-curated measured-physical rows. build_dof_ledger
  already adds the ONE new measured-physical carry_operating_mothballs entry,
  so with the 4 carried rows the count is 21 measured / 2 residual (miso-67
  was 20/2).

No zero-forcing ablation twin (rule 20 as amended 2026-07-14 — legitimacy
rests on the DOF ledger + legitimacy_diagnostics.json D-1/D-2/D-4 alone).

Usage: python scripts/archive/gen_miso68_attestation.py
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SRC67 = REPO / "results/calibration/miso67_stgas_vlr_level/calibration_attestation.json"


def main() -> None:
    out_dir = REPO / "results/calibration/miso68_cottonwood_mothballs"
    att = json.loads(SRC67.read_text())
    dst = out_dir / "calibration_attestation.json"

    # Hand-curated measured-physical rows carried across the lineage (they are
    # not enumerated by build_dof_ledger from config, so the attestation merges
    # them back onto its output).
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
        "miso-68 mothballed-but-operating re-carry 2026-07-16: the miso-67 "
        "keeper recipe (scripts/probes/_miso68_cottonwood_mothballs.py — the "
        "miso67_stgas_vlr_level meta.json strict replay via "
        "replay_keeper.build_kwargs) with ONE single-delta override applied "
        "through its own dedicated solve kwarg: carry_operating_mothballs = "
        "True. The gate re-carries each OA (mothballed) unit the canonical "
        "2025ER snapshot's OP filter drops for backcast solve year Y iff it "
        "is OP in the year-matched EIA-860 vintage_<Y> — EIA's own "
        "contemporaneous status, the zero-DOF rule-13 availability oracle (a "
        "unit truly idle in Y is OA in vintage_<Y> too, so OA status alone "
        "never re-carries capacity). Per-UNIT injection from the vintage rows "
        "(year-matched net-summer capacity): Cottonwood 55358's partial "
        "mothball (4 of 8 units OA — the CAMPD-demonstrated ~570 MW behind "
        "the sole C1 fail CC_REGULAR-2023) re-carries only its "
        "OA-but-operating units and leaves the 4 surviving OP units "
        "untouched; MISO-wide the oracle also sweeps ~35 MW of small "
        "partial-mothball plants (all <=28 MW). 2025 has no committed "
        "vintage and carries nothing (accepted under-carry, charter owner "
        "default). ZERO fitted scalars: the year-matched vintage's own "
        "status is the oracle. Design: "
        "docs/handoffs/miso-cc-vintage-undercarry-plan-2026-07.md §5-§8."
    )
    att["governance"]["note"] = (
        "Mothballed-but-operating re-carry (the Cottonwood lane). Rules 1/11 "
        "— fixes the real fleet-provenance defect the 2026-07-16 bisect "
        "exposed (the 2025ER snapshot used to represent 2023/2024 drops ~570 "
        "MW of demonstrably-operating capability); carries REAL units at "
        "their availability bounds, never the removed double-filed phantom. "
        "Rule 13 (forward-regenerable) — the vintage-status oracle would "
        "regenerate for any forward vintage and responds to changed "
        "conditions; the LP dispatches the carried units freely (no outcome "
        "pinning: main-2023 dispatches Cottonwood ~4.0 TWh at ~40% CF where "
        "CAMPD shows near-continuous operation — dispatch follows the "
        "model's own economics, not the measured MWh). Rule 24/25 — gated "
        "ScenarioConfig boolean, default off, ISO-agnostic status/physics "
        "trigger, no per-plant dict, recorded in run_config.json/meta.json. "
        "Rule 23 — no deriver touched (the cc_capacity_reconcile --mode both "
        "re-derive is prior work, commit 775eea1). MECHANISM-ONLY read (main "
        "minus a same-box unchanged-recipe base replica, both solved in this "
        "box; the base reproduces the registered keeper's CC_REGULAR-2023 "
        "-9.79 exactly — zero box drift): CC_REGULAR-2023 -9.79 FAIL -> "
        "-8.28 FAIL (+1.51 TWh toward actual; tol ±8.00 TWh, 0.28 short of "
        "the band), CC_REGULAR-2024 -4.22 -> -2.98 (stays PASS, margin "
        "widens), 2025 byte-identical (no vintage). Displacement is the "
        "expected mid-merit pattern (2023: COAL_PRB -0.41, CT_PEAKER -0.33, "
        "import -0.31, ST_GAS -0.20 TWh; every displaced class stays PASS; "
        "worst adverse move -0.14 TWh, deep in band). Zero C1 status flips: "
        "the fail set is unchanged (15/16, sole fail CC_REGULAR-2023, "
        "magnitude shrunk). C3b price-shape veto holds (PASS both arms); "
        "C3a/C3c FAIL in both arms (the F4-blocked MISO price-formation "
        "lane, untouched — its own charter). LOO within 2023-2025: zero "
        "fitted DOF (nothing refit per fold); 2023 improves, 2024 "
        "independently improves, 2025 untouched — no held-out degradation. "
        "No zero-forcing ablation twin (rule 20 as amended 2026-07-14)."
    )

    att["disclosures"]["note"] = (
        "PENDING SCORE (filled by the registration step; see metrics.json "
        "determination + reasons)."
    )

    dst.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {dst}")


if __name__ == "__main__":
    main()
