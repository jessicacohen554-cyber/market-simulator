"""Generate the miso-67 candidate calibration_attestation.json.

Carries forward the miso-66 keeper attestation (governance clauses + the
hand-curated measured-physical rows build_dof_ledger does not enumerate, and the
two ledgered storage benchmark-basis exceptions C5b throughput + C5c 2025 shape)
and rewrites the run-specific text for the ST_GAS p25-LEVEL swap:

* ``attested_by`` — the miso-66 keeper recipe with ONE single-delta override:
  the ``st_gas_mustrun_per_plant`` floor LEVEL swapped from the committed
  tranche (P5-of-online = LSL) to the plant's measured p25-of-online
  available-CF x nameplate. Same driver, same window, same mechanism id
  (rule 19 level replace). Zero fitted scalars — a boolean arming measured data.
* ``note`` — the admissibility argument (rule 13 forward-regenerable measured
  input; rule 23 no deriver touch) and the mechanism-only read discipline.
* ``free_parameters`` — rebuilt by build_dof_ledger.py (call FIRST); this merges
  back the hand-curated measured-physical rows. build_dof_ledger already adds
  the ONE new measured-physical p25 entry, so with the 4 carried rows the count
  is 20 measured / 2 residual (miso-66 was 19/2).

No zero-forcing ablation twin (rule 20 as amended 2026-07-14 — legitimacy rests
on the DOF ledger + legitimacy_diagnostics.json D-1/D-2/D-4 alone).

Usage: python scripts/gen_miso67_attestation.py
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC66 = REPO / "results/calibration/miso66_coalconduct/calibration_attestation.json"


def main() -> None:
    out_dir = REPO / "results/calibration/miso67_stgas_vlr_level"
    att = json.loads(SRC66.read_text())
    dst = out_dir / "calibration_attestation.json"

    # Hand-curated measured-physical rows carried across the lineage (they are
    # not enumerated by build_dof_ledger from config, so the attestation merges
    # them back onto its output).
    carried = {
        "MISO COAL SOM near-cost offer floor",
        "COAL_SIGMOID_DEFAULTS[MISO]",
        "gas_daily_shape[MISO]",
        "hydro 2025 completeness (backfill 2024 + EIA-930 monthly repin)",
        "st_gas_mustrun_per_plant (ST_GAS local-reliability "
        "commitment floor, measured committed window)",
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
        "miso-67 ST_GAS p25-LEVEL 2026-07-15: the miso-66 keeper recipe "
        "(scripts/probes/_miso67_stgas_vlr_level.py — the miso66_coalconduct "
        "meta.json strict replay via replay_keeper.build_kwargs) with ONE "
        "single-delta override applied through the generic prb_overrides "
        "channel: st_gas_mustrun_p25_level = True. The override swaps the LEVEL "
        "of the existing st_gas_mustrun_per_plant floor for each gate-armed "
        "ST_GAS plant from the committed tranche (committed_pct = P5-of-online "
        "= the LSL) to the plant's measured 25th-percentile-of-online "
        "available-CF (thermal_tranches_MISO.csv p25_cf, the SAME frozen "
        "derive_thermal_tranches.py estimator that writes committed_pct / "
        "online_frac) times nameplate, held in the SAME top-online_frac "
        "system-load window and distributed cheapest-first across the plant's "
        "tranches, clipped to pmax*availability. Same driver, same window, same "
        "mechanism id (MECH_ST_GAS_MUSTRUN_PER_PLANT) — ONLY the level source "
        "changes (rule 19 level replace, no second floor). ZERO fitted "
        "scalars: p25_cf is the measured 25th-percentile dispatch level of the "
        "Entergy MISO-South VLR steam fleet (Sabine 32.9%, Harding Street "
        "36.7%, Nine Mile 49.4%), which ran 30-67% CF despite local LMP at/"
        "below SRMC (out-of-market VLR dispatch — Amite South / DSG / WOTAB, "
        "MISO SOM). Design: docs/handoffs/miso-run66-triage-design-2026-07.md "
        "Issue-2."
    )
    att["governance"]["note"] = (
        "ST_GAS VLR level swap. Rule 19 — REPLACES the committed-tranche level "
        "of the existing st_gas_mustrun_per_plant floor rather than stacking a "
        "second mechanism; same mechanism id, so D-2/D-4 attribution is "
        "unchanged. Rule 13 (forward-regenerable) — p25_cf re-derives from each "
        "new multi-year CAMPD vintage exactly like committed_pct/online_frac; "
        "the level stays BELOW available capacity so the floor never pins the "
        "plant and dispatch above it is free (no outcome pinning: dispatch is "
        "not held to any measured generation, the class lands BELOW actual even "
        "at the floor ceiling). Rule 23 — no derive script touched; the p25_cf "
        "column already exists in the frozen artifact (re-derive triggers with "
        "committed_pct/online_frac on a new CAMPD vintage). Rule 25 — the "
        "boolean is ISO-generic, default-off everywhere; the arming evidence is "
        "MISO's own SOM + CAMPD. MECHANISM-ONLY read (probe minus a same-box "
        "unchanged-recipe base replica, both solved in this box): ST_GAS-2024 "
        "base -8.65 FAIL -> main -6.37 PASS (+2.28 TWh), ST_GAS up +2.3/+2.3/"
        "+3.2 TWh across 2023/24/25; CC/COAL/CT displaced only -0.5..-1.8 TWh "
        "(all stay PASS); C3b-2025 mechanism-only +0.007 (absolute 0.187 <= "
        "0.20 veto holds); C3a-2025 mechanism -0.47 (the inframarginal floor "
        "weakly lowers the level; the S->N separation channel is real but "
        "negligible — July-2025 N-S spread 0.33 -> 0.42, S->N flow +0.1 GW); "
        "C3c unchanged. No zero-forcing ablation twin (rule 20 as amended "
        "2026-07-14). NOTE: the same-box base is 14/16 (CC_REGULAR-2023 FAILs "
        "on current main, a code-drift regression vs the miso-66 solve commit "
        "5c7ed9c — 293 src/scripts/data files changed since), so the OVERALL "
        "determination stays NOT-YET; the p25 mechanism cleanly fixes "
        "ST_GAS-2024 but does not by itself flip the fail set."
    )

    att["disclosures"]["note"] = (
        "PENDING SCORE (filled by the registration step; see metrics.json "
        "determination + reasons)."
    )

    dst.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {dst}")


if __name__ == "__main__":
    main()
