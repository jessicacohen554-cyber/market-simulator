# HANDOFF — NWPP-NEXT-8: NWPP calibration after the lever-1 diagnosis

NWPP-NEXT-7 spent no LP. It diagnosed lever 1 and found that it reduces to the open coal take-obligation questions.
Keeper #13 is unchanged.

```
SESSION NWPP-NEXT-8 — NWPP calibration tuning, keeper #13 (2026-09-26-nwppnext6-path76-ctrederive)
DATA PROFILE: nwpp
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 13, 14, 17, 19, 23, 24, 28, 29 and 31–36. The parent never
solves (rule 32(a)). Every backcast year gets its own shard (rule 36).

STATE ON MAIN
- Keeper #13: 2026-09-26-nwppnext6-path76-ctrederive. Bundle: results/calibration/nwppnext6ab_span. Years: 2019–2025.
  Recipe in PRECOMMIT-nwppnext6 §4, plus nwpp_path76_alturas_link=true and the SB-population CT re-derive.
- Determination: NOT-YET on {fuelmix, dispatch_corr}. C2, C6 and C8 PASS. Price is UNSCORED (rubric v3.8).
  - C1 CC_REGULAR FAILS: 2020 +9.94 and 2024 +8.30 TWh (band ±8). 2019 +7.77; 2025 +8.34 (SKIPPED, prelim 923).
  - C4 coal r FAILS 2023 / 2024 / 2025: 0.673 / 0.582 / 0.655. C4 gas 2020 NRMSE 0.307 FAILS.
- NEW (NWPP-NEXT-7, zero LP): docs/handoffs/FINDING-nwppnext7-cc-long-is-coal-short-2026-09-26.md
  - The C1 CC_REGULAR residual mirrors the coal residual: r = −0.974 over 2019–2025. Hydro and total fossil are
    close to EIA-923. The coal CC displaces is Centralia, Colstrip, Jim Bridger (2019–20) and Utah BIT (2024–25).
  - CC heat-rate coverage is 22/23 (Clark missing, and it runs short). There is no hydro-year driver.
  - The NWPP-NEXT-5 coal take floor binds 3.8/5.4/7.2/4.0 TWh (A) or 10.2/21.4/9.4/6.6 TWh (B) in
    2019/2020/2024/2025. At a 1:1 bound A brings every CC year inside ±8 and B over-corrects 2020 to −11.4.
    That table must not select the estimator (rule 1).
- Records to read first: that FINDING; docs/handoffs/FINDING-nwppnext5-coal-take-obligation-design-2026-09-26.md
  (§4 design, §5 Q1–Q5); docs/handoffs/RESULT-nwppnext6-path76-and-ct-rederive-2019-2025-2026-09-26.md;
  docs/calibration-log/nwpp.md; docs/codebase-site/data/mechanism-matrix/NWPP.js; docs/mechanism-testing-matrix.md §5.9.

CLOSED — do NOT redo:
- Everything closed in HANDOFF-nwppnext7.
- Lever 1 as a gas-side question: there is no CC population, heat-rate or hydro driver. Do not re-census it.
- Offer-multiplier tuning on C1, C4 or CT (rules 1 and 13).

OPEN LEVERS, highest value first:

1. Coal take obligation (closes C1 CC_REGULAR and coal volume). BLOCKED on owner Q1–Q5.
   - First action: check whether the owner has answered Q1–Q5 (the user's message, calibration log, the FINDINGs).
     If not, ask them once, in one message, with the NWPP-NEXT-7 §3 table, and then go to lever 2 or 3.
   - If answered: implement exactly the ruled form (the NWPP-NEXT-5 §4 design) as a default-off field, with its
     matrix row and a cell in every shard (rule 28(c)), tests, and the rule-19 retirement of the incumbents if Q5 says
     so. Then solve 7 year-isolated shards on keeper #13's recipe plus the field.
   - Predicted: C1 CC_REGULAR moves toward 0 in 2019/20/24/25, coal volume up, C4 coal r flat to −0.1.
     Report every regression at full magnitude.
2. SNV residual shed (2020: 46.6 GWh; 2021: 34.0), zero LP.
   - Census the shed hours against the NEVP served-schedule headroom (Path 81 SNTI 4,533/3,790 MW) and the
     default-off CAISO / WECC_SW NeighborInterface blocks. Is import rigidity, not capacity, binding?
3. Internal-link over-flow (structural question), zero LP.
   - Every NWPP link arbitrages to its rating. Document measured-vs-model flow per link (EIA-930 pairwise
     interchange, 2023–25) as a FINDING. Ask the owner whether a measured-flow basis belongs in the model.
4. C4 coal 2023–25 (r 0.58–0.67): NWPP-NEXT-5 Q6. What does real NWPP coal swing with? r(actual coal, model price)
   ≤ 0.32 in every year, so no price- or budget-shaped mechanism reaches it.
5. Jim Bridger (8066) has no measured COAL tranche row: needs a rule-23 data-change justification or
   campd_per_unit_attribution (cell U).
6. Benchmark consistency (report only): PGE Beaver 8073 has no CEMS, so no benchmark plant row and no measured CC
   rate. The per-plant CC sum and classFull disagree by −2.2 to +4.6 TWh.

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
  earlier nwppnext*/rnwpp-* list. NWPP-NEXT-7 launched no shards.
- Known pre-existing test failures, not NWPP's: see HANDOFF-nwppnext7.
```
