# HANDOFF — NWPP-NEXT-9: NWPP calibration after keeper #15

```
SESSION NWPP-NEXT-9 — NWPP calibration tuning after keeper #15 (2026-09-28-nwppnext8-coal-monthly-pile)
DATA PROFILE: nwpp
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 13, 14, 17, 19, 23, 24, 28, 29 and 31–36. The parent never
solves (rule 32(a)). Every backcast year gets its own shard (rule 36).

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_01QbK28JLDy2FijGArJGhW2q (NWPP-NEXT-8).
  Safe means: its PR has merged on main, and get_session shows it idle.
- Check for unmerged NWPP branches and PRs. Salvage anything needed into your branch, and close or merge the PRs.
  Say which branches can be deleted.
- Rebase and merge your work.
- Present every decision for the owner as clickable decision cards (AskUserQuestion), NEVER as inline text.
- When done: promote if it is a good candidate, create a PR and merge it, archive all your shards, and launch the next
  handoff session to continue calibration while rubric failures remain. Give it these same chain directions, including
  "archive the previous session when safe".
- If NWPP becomes calibrated and the rubric clears for all years, check the complete / frontier declaration criteria.
  Settle the keeper config and clear the tasks that enable declaration. If complete / frontier is reached, say so in
  your final message so the owner can approve.
- If you are at the session-nesting limit, make your last message a handoff prompt that starts a new chain.
- Owner standing ruling: promote if structural integrity improves, even if a gate regresses. Report every regression
  at full magnitude.

STATE ON MAIN
- Keeper #15: 2026-09-28-nwppnext8-coal-monthly-pile. Bundle: results/calibration/nwppnext8mp_span. Years: 2019–2025.
- Recipe: keeper #14's recipe (PRECOMMIT-nwppnext7 §4) plus coal_fuel_inventory_monthly_pile=true. The full recipe is
  in PRECOMMIT-nwppnext8 §5.
- The new mechanism, coal_fuel_inventory_monthly_pile:
  - each per-coal-yard row becomes 12 cumulative month-end rows (floor and ceiling);
  - receipts are flat ratable (C/12);
  - month 12 is exactly the annual identity;
  - zero new parameters;
  - owner decision cards 2026-09-28.
- Determination: NOT-YET on {dispatch_corr}, ONE record. C1, C2, C6 and C8 PASS. Price is UNSCORED (rubric v3.8).
  - C4 coal 2023: r 0.695 / NRMSE 0.283 against the 0.70 floor. It is the only failing record.
  - Every other C4 record passes. The lowest are coal 2025 at 0.721 and coal 2019 at 0.733.
  - gas 2025 regressed 0.864 → 0.854 (still PASS).
- Records to read first:
  - docs/records/nwpp/RESULT-nwppnext8-coal-monthly-pile-2019-2025-2026-09-28.md (§3 routed list)
  - docs/records/nwpp/PRECOMMIT-nwppnext8-coal-monthly-pile-2019-2025-2026-09-28.md (§0 seasonal diagnosis, §5 recipe,
    §6 hard stops)
  - docs/calibration-log/nwpp.md, docs/codebase-site/data/mechanism-matrix/NWPP.js, docs/mechanism-testing-matrix.md §5.9

CLOSED — do NOT redo:
- Everything closed in HANDOFF-nwppnext7 and HANDOFF-nwppnext8.
- The monthly pile grain (keeper #15).
- Offer-multiplier tuning on C1, C4 or CT (rules 1 and 13).

OPEN LEVERS, highest value first. Only one record separates NWPP from CALIBRATED.

1. C4 coal 2023 (r 0.695). This is NWPP-NEXT-5 Q6.
   - Model coal 2023 runs hot in Jan–Mar: 5.5 / 4.8 / 4.6 TWh against EIA-930's 4.4 / 3.4 / 3.4. Oct is too cold
     (3.0 vs 4.0).
   - The monthly pile barely binds in 2023 (phase-0 footprint 0.1 TWh), so the cause is elsewhere.
   - Do a zero-LP driver census first, per plant, with CEMS monthly against model m_mon from the keeper payload. Look at
     net load, hydro, WEIM, and unit outages at Colstrip, Bridger and Centralia.
   - Note the winter 2022–23 western gas event: NW delivered gas was ~$18–21/MMBtu in Jan 2023. That makes coal cheap
     relative to gas in the model. Check whether real coal was limited by something the model lacks, such as outages,
     derates or rail/fuel limits.
   - Useful zero-LP tools: the NEXT-8 diagnostic approach (monthly/day/hour r decomposition against EIA-930).
     EIA-930 for NWPP comes from run_calibration_full._eia930_frame(year, 'NWPP', cfg).
2. Colstrip 2020 available energy is 5.86 TWh against 7.94 TWh generated (EIA-923). Check the outage/availability inputs.
3. SNV residual shed (2020: 46.6 GWh; 2021: 34.0).
4. Internal-link over-flow: a structural FINDING plus an owner question.
5. Jim Bridger (8066) has no measured COAL tranche row.
6. Solve time (performance only). The 2019 leg now takes about 3 h; P0 alone was 43 min. A pile-state formulation (12
   carry variables per yard) would replace the cumulative rows and cut non-zeros. It must reproduce keeper #15
   byte-identically before it may be used.

PROCEDURE FOR ANY SOLVE — follow PRECOMMIT-nwppnext8 as the template
- Phase 0 zero-LP census, plus G-DRIFT against nwppnext8mp_span's git_sha (read it from meta.json; rule 29(b) form 4).
- Replay source: the NWPP-49 bundle, restored outside the repo:
    git fetch --depth=1 origin 909cdd30bfdd8a398b10a4255b1340d0d9ef1943
    git archive 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 results/calibration/nwpp49_ror_span | tar -x -C /tmp/n49
  Then run python3 scripts/data/curate_hydro_plant_modes.py --iso NWPP.
- replay_keeper.py takes every keeper flag via --set. Use keeper #15's full --set list, from PRECOMMIT-nwppnext8 §5.
  The shard must first run scripts/data/curate_coal_receipts.py and scripts/data/curate_coal_stocks.py.
  Add hydro_backfill_year=null for 2019–2022.
- Push the PRECOMMIT and pin its full 40-character SHA.
  - Every shard prompt pre-authorizes `git fetch --depth=1 origin <PIN> && git checkout --detach <PIN>` and states
    that this checks out the pin and is not a sync.
  - Every shard prompt says: launch the solve with nohup and a PID file, poll inside the turn with ~9-minute Bash
    calls, and never end the turn while it runs.
  - Hard stops include the sha256 of campd_ct_heat_rates_NWPP.csv: 29baa2f1ecfa10d9734c7e44cc306a88d527adb28968ea260f3409de37d7ff92.
- BUDGETS: 2019 needs 180+ min. Other years take 35–60 min. Give 2019 a 200-min budget up front.
- Config hard stop: diff run_config.json scenario_config against keeper #15's run_config_<Y>.json
  (results/calibration/nwppnext8mp_span). Only the arm's key may change. Fields absent in the keeper and False/None/default
  in the arm are accepted.
- Keeper #15's P1 demand (unchanged from #14), for the demand hard stop: 279.581 / 292.940 / 289.358 / 298.960 / 280.261 /
  290.216 / 302.532 TWh.
- Each shard pushes its FULL bundle with the .gitignore negation and a plain git add (rule 34(a)).
- Compose with scripts/probes/_nwpp42_compose_span.py --out results/calibration/<name>_span --skip-diagnostics, 2023 leg
  first (--out is a PATH). Then:
  - legitimacy_diagnostics.py --bundle <b> --iso NWPP --json-out <b>/legitimacy_diagnostics.json
    (exit code 1 is normal; C8 is scored by the verdict)
  - attestation: wrap scripts/gen_nwppnext8_attestation.py (it chains 7 → 6 and reads commit 909cdd30)
  - dashboard_add_run.py --label ... --bundle <b> --no-prune
  - calibration_verdict.py --run-id <id> --json, then diff per record against keeper #15
- Gitignore your per-year leg dirs with a pattern that does NOT match your _span dir.
- Promote by rule 35:
  - python3 scripts/lib/keeper_store.py --set NWPP <id> --note "..."
  - build_status.py --iso NWPP
  - audit_keepers --iso NWPP (E1)
  - prune_iso_runs.py --iso NWPP --force-uncite
  - audit_keepers PASS
  - check_promotion_completeness.py --iso NWPP
  - matrix shard: keeper and gates stamp, plus the cell
  - §5.9 header and the calibration log
  - calibration-keeper-auditor subagent
- check_registry_payload_parity.py reports RED locally on your own gitignored per-year legs. That is expected; CI does
  not see them.
- After a rebase, re-run scripts/check_mechanism_matrix.py --fix-anchors. Anchor-digit conflicts in mechanism-matrix.js
  resolve to main's side; keep your own new rows.

7. Stale provenance hash, NWPP-owned, pre-existing, zero-LP.
   - tests/unit/data/test_nwpp_demand_plant_basis.py::test_artifact_matches_bench_parts fails on main only on the
     source_sha256 column. TWh values match to 4 dp.
   - A later dashboard registration re-rendered the bench part that the committed plant-basis energy CSV hashes.
   - Re-derive the CSV with scripts/data/derive_nwpp_plant_basis_energy.py.
   - First confirm that only the sha column moves, and whether the CSV is on the solve-surface fingerprint (cache-key
     move). If it is, record that in the PR.

HOUSEKEEPING (owner)
- Leftover shard branches to delete: claude/nwppnext8mp-{2019..2025}.
- Known pre-existing test failures, not NWPP's: the 27 in tests/unit/data/test_firm_import_*,
  test_gas_offer_zonal_anchor_vintage, test_nwpp_demand_plant_basis::test_artifact_matches_bench_parts, and
  tests/unit/results/test_export. They were identical on main at 2026-09-28. Also the four named in HANDOFF-nwppnext8
  (test_d53, test_d60, test_reserve_config, test_ccs_retrofit).
```
