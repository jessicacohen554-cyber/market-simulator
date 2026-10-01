# HANDOFF — NWPP-NEXT-7: NWPP calibration after keeper #13

```
SESSION NWPP-NEXT-7 — NWPP calibration tuning after keeper #13 (2026-09-26-nwppnext6-path76-ctrederive)
DATA PROFILE: nwpp
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 13, 14, 17, 19, 23, 24, 28, 29 and 31–36. The parent never
solves (rule 32(a)). Every backcast year gets its own shard (rule 36).

STATE ON MAIN
- Keeper #13: 2026-09-26-nwppnext6-path76-ctrederive. Bundle: results/calibration/nwppnext6ab_span. Years: 2019–2025.
- Recipe: keeper #12's recipe (the full --set list is in PRECOMMIT-nwppnext6 §4, including admit_standby_units=true)
  plus two changes:
  - nwpp_path76_alturas_link=true: WECC Path 76, NW<->SNV, one bidirectional 300 MW link.
  - campd_ct_heat_rates_NWPP.csv re-derived on the SB-admitted fleet (owner rule-23 ruling). Fredonia 607 is at
    10.413 and Sun Peak 54854 at 12.893. The re-derive is an artifact change, not a config key.
- Determination: NOT-YET on {fuelmix, dispatch_corr}. C2, C6 and C8 PASS. Price is UNSCORED (rubric v3.8).
  - C1 CC_REGULAR FAILS: 2020 +9.94 TWh and 2024 +8.30 TWh, against a ±8 band. 2019 is +7.77, a near-miss.
  - C4 coal r FAILS in 2023 / 2024 / 2025: 0.673 / 0.582 / 0.655.
  - C4 gas 2020 FAILS: NRMSE 0.307.
  - Unserved load (GWh): 4.5 / 46.6 / 34.0 / 7.5 / 1.5 / 13.6 / 1.2. The 2020–21 remainder is SNV.
  - Path 76 runs at its rating 83–91 % of hours, in both directions. The measured BPAT->NEVP seam averages
    20–28 MW net.
- Records to read first:
  - docs/handoffs/RESULT-nwppnext6-path76-and-ct-rederive-2019-2025-2026-09-26.md (§3 routed list)
  - docs/handoffs/PRECOMMIT-nwppnext6-path76-and-ct-rederive-2019-2025-2026-09-26.md (§4 recipe, §5 hard stops,
    §8 launch record)
  - docs/handoffs/FINDING-nwppnext5-coal-take-obligation-design-2026-09-26.md (owner questions Q1–Q6, still open)
  - docs/calibration-log/nwpp.md
  - docs/codebase-site/data/mechanism-matrix/NWPP.js
  - docs/mechanism-testing-matrix.md §5.9

CLOSED — do NOT redo:
- Coal stacking fix (K).
- SB admission (K).
- Path 76 (K).
- The SB-population CT re-derive (done).
- Demand basis framings 1 and 2.
- Uncoupled-mainstem coupling.
- Pondage.
- CT floors.
- Offer-multiplier tuning on C1, C4 or CT (rules 1 and 13).
- A price-shaped coal take-obligation budget as a C4 fix.
- Derating Path 76 or any link to measured flow (rule 13 answer-key).

OPEN LEVERS, highest value first. Pick one, or state why you go off-queue:

1. C1 CC_REGULAR long (2019 +7.8, 2020 +9.9, 2024 +8.3 TWh). This is now the gate that flips first.
   - Zero-LP diagnosis first, by zone × heat-rate band × month:
     - Where does model CC energy exceed EIA-923?
     - What does it displace: hydro, coal, imports or CT?
   - Check the CC heat-rate artifact coverage (campd_cc_heat_rates_NWPP.csv) against the admitted fleet. The same
     population question as the CT re-derive may apply. A re-derive for population needs an owner rule-23 ruling.
   - Check whether the 2020 and 2024 excess tracks low-hydro years, i.e. whether the model's hydro energy/shape
     under-serves.
   - Do not tune.

2. C4 coal 2023–25 (r 0.58–0.67).
   - Run the zero-LP driver census of real hourly coal swing: net load, hydro, wind, WEIM, unit outages.
   - Answer or route owner questions Q1–Q6 before choosing any mechanism.

3. SNV residual shed (2020: 46.6 GWh; 2021: 34.0).
   - Census the shed hours against:
     - the NEVP served-schedule headroom (Path 81 SNTI 4,533/3,790 MW);
     - the default-off CAISO / WECC_SW NeighborInterface blocks.
   - The question is whether import rigidity, not capacity, is binding.

4. Internal-link over-flow (structural question, not a tuning one).
   - Every NWPP link arbitrages to its rating.
   - Document the measured-vs-model flow on each link (EIA-930 pairwise interchange, 2023–25) as a FINDING.
   - Ask the owner whether a measured-flow basis belongs in the model.

5. Jim Bridger (8066) has no measured COAL tranche row. It needs a rule-23 data-change justification or
   campd_per_unit_attribution (cell U).

PROCEDURE FOR ANY SOLVE — follow PRECOMMIT-nwppnext6 as the template
- Phase 0 zero-LP census, plus G-DRIFT against nwppnext6ab_span's git_sha (read it from its meta.json;
  rule 29(b) form 4).
- Replay source: the NWPP-49 bundle, restored outside the repo:
    git fetch --depth=1 origin 909cdd30bfdd8a398b10a4255b1340d0d9ef1943
    git archive 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 results/calibration/nwpp49_ror_span | tar -x -C /tmp/n49
  Then run python3 scripts/data/curate_hydro_plant_modes.py --iso NWPP.
- replay_keeper.py takes every keeper flag via --set, including nwpp_path76_alturas_link=true. Add
  hydro_backfill_year=null for 2019–2022.
- Push the PRECOMMIT and pin its full 40-character SHA.
  - Every shard prompt pre-authorizes `git fetch --depth=1 origin <PIN> && git checkout --detach <PIN>` and states
    that this checks out the pin and is not a sync.
  - Every shard prompt says: launch the solve with nohup and a PID file, poll inside the turn with ~9-minute Bash
    calls, and never end the turn while it runs.
  - Hard stops include the sha256 of campd_ct_heat_rates_NWPP.csv: 29baa2f1ecfa10d9734c7e44cc306a88d527adb28968ea260f3409de37d7ff92.
- Config hard stop: diff run_config.json scenario_config against keeper #13's run_config_<Y>.json. Only the arm's key
  may change. Fields absent in the keeper and False in the arm are accepted.
- Keeper #13's P1 demand, for the demand hard stop: 279.581 / 292.940 / 289.358 / 298.960 / 280.261 / 290.216 /
  302.532 TWh.
- Shards restart sometimes: four of 14 did in NWPP-NEXT-6 and still finished. Relaunch only on "Setup script failed".
- Each shard pushes its FULL bundle with the .gitignore negation and a plain git add (rule 34(a)).
- Compose with scripts/probes/_nwpp42_compose_span.py --skip-diagnostics, 2023 leg first. Then:
  - legitimacy_diagnostics.py ... --json-out <b>/legitimacy_diagnostics.json
  - attestation: wrap scripts/gen_nwppnext6_attestation.py (it reads commit 909cdd30 — fetch that object first)
  - dashboard_add_run.py --no-prune
  - calibration_verdict.py --run-id <id> --json, then diff per record against keeper #13
- Gitignore your per-year leg dirs with a pattern that does NOT match your _span dir.
- Owner standing ruling: promote if structural integrity improves, even if a gate regresses; report every regression
  at full magnitude.
- Promote by rule 35:
  - keeper_store.py --set NWPP <id>
  - build_status.py --iso NWPP
  - audit_keepers --iso NWPP (E1)
  - prune_iso_runs.py --iso NWPP --force-uncite, and stage the deleted bundle files
  - audit_keepers PASS
  - matrix shard: keeper and gates stamp, plus the cell
  - §5.9 header and the calibration log
  - calibration-keeper-auditor subagent. Check its wording is neutral.
- After a rebase, re-run scripts/check_mechanism_matrix.py --fix-anchors; anchor-digit conflicts in
  mechanism-matrix.js resolve to main's side. Keep your own new rows.

HOUSEKEEPING (owner)
- Leftover shard branches to delete: claude/nwppnext6a-{2019..2025}, claude/nwppnext6ab-{2019..2025}, plus every
  earlier nwppnext*/rnwpp-* list.
- Known pre-existing test failures, not NWPP's:
  - tests/unit/config/test_d53_sector_gate_miso_arming.py
  - tests/unit/config/test_d60_arming_batch.py
  - tests/unit/config/test_reserve_config.py
  - tests/unit/config/test_summer_availability_constants.py
  - the CAISO/SOCO data-dependent tests in tests/unit/data
```
