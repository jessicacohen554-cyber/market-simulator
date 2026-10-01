# HANDOFF — NWPP-NEXT-8: NWPP calibration after keeper #14

```
SESSION NWPP-NEXT-8 — NWPP calibration tuning after keeper #14 (2026-09-27-nwppnext7-coal-take-floor)
DATA PROFILE: nwpp
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 13, 14, 17, 19, 23, 24, 28, 29 and 31–36. The parent never
solves (rule 32(a)). Every backcast year gets its own shard (rule 36).

CHAIN DIRECTIONS (owner, standing; pass them on verbatim to every handoff you launch)
- First, when it is safe, archive the previous session: session_01Q7tEEE1oTgUhmzJjSEWwrb (NWPP-NEXT-7).
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
- Keeper #14: 2026-09-27-nwppnext7-coal-take-floor. Bundle: results/calibration/nwppnext7sf_span. Years: 2019–2025.
- Recipe: keeper #13's recipe (PRECOMMIT-nwppnext6 §4) plus the four keys of PRECOMMIT-nwppnext7 §1.
  - coal_fuel_inventory_plant_grain=true
  - coal_fuel_inventory_take_floor=true. This is the SOFT take floor, estimator B net, with shortfall priced at the
    yard's model coal fuel price.
  - coal_takeorpay_from_data=false
  - coal_committed_takeorpay_regulated=false
- Determination: NOT-YET on {dispatch_corr} only. C1, C2, C6 and C8 PASS. Price is UNSCORED (rubric v3.8).
- C4 dispatch_corr FAILS on four records (r / NRMSE; the r floor is 0.70):

  | Record | Keeper #14 | Keeper #13 |
  |---|---|---|
  | gas 2019 | 0.699 / 0.243 | 0.719 (PASS → FAIL) |
  | coal 2019 | 0.690 / 0.264 | 0.701 (PASS → FAIL) |
  | coal 2023 | 0.693 / 0.289 | 0.673 |
  | coal 2025 | 0.678 / 0.261 | 0.655 |

- Records to read first:
  - docs/records/nwpp/RESULT-nwppnext7-coal-take-floor-2019-2025-2026-09-27.md (§3 routed list)
  - docs/records/nwpp/PRECOMMIT-nwppnext7-coal-take-floor-2019-2025-2026-09-27.md (§4 recipe, §5 hard stops, §9 soft floor)
  - docs/records/nwpp/FINDING-nwppnext7-cc-long-is-coal-short-2026-09-26.md
  - docs/records/nwpp/FINDING-nwppnext5-coal-take-obligation-design-2026-09-26.md (Q6 is still open)
  - docs/calibration-log/nwpp.md, docs/codebase-site/data/mechanism-matrix/NWPP.js, docs/mechanism-testing-matrix.md §5.9

CLOSED — do NOT redo:
- Everything closed in HANDOFF-nwppnext7.
- The coal take floor (K) and its hard form, which is refused because it went infeasible.
- C1 CC_REGULAR as a gas-side question.
- Offer-multiplier tuning on C1, C4 or CT (rules 1 and 13).

OPEN LEVERS, highest value first. All four C4 records are within 0.03 of the 0.70 floor.

1. C4 2019 gas and coal, which the take floor just regressed.
   - Zero-LP diffing of keeper #13 vs #14 hourly class/system parquets for 2019 (hourly/ is committed). Which hours and
     zones lost correlation?
   - Is it the take floor forcing coal flat, or the retired per-hour discounts changing the coal offer?
   - The take-floor row duals and per-yard shortfall are not persisted. Consider adding them as a diagnostic output
     (default-off plumbing only).
2. C4 coal 2023 / 2025 (0.693 / 0.678): NWPP-NEXT-5 Q6. What does real NWPP coal swing with?
   - r(actual coal, model price) ≤ 0.32 historically. Run a driver census: net load, hydro, wind, WEIM, unit outages.
3. Colstrip 2020 available energy is 5.86 TWh against 7.94 TWh generated (EIA-923). Check the outage/availability
   inputs. The take floor is capacity-clipped there.
4. SNV residual shed (2020: 46.6 GWh; 2021: 34.0). Is it import rigidity (Path 81 SNTI) or capacity?
5. Internal-link over-flow: a structural FINDING plus an owner question on a measured-flow basis.
6. Jim Bridger (8066) has no measured COAL tranche row.

PROCEDURE FOR ANY SOLVE — follow PRECOMMIT-nwppnext6 as the template
- Phase 0 zero-LP census, plus G-DRIFT against nwppnext7sf_span's git_sha (read it from its meta.json;
  rule 29(b) form 4).
- Replay source: the NWPP-49 bundle, restored outside the repo:
    git fetch --depth=1 origin 909cdd30bfdd8a398b10a4255b1340d0d9ef1943
    git archive 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 results/calibration/nwpp49_ror_span | tar -x -C /tmp/n49
  Then run python3 scripts/data/curate_hydro_plant_modes.py --iso NWPP.
- replay_keeper.py takes every keeper flag via --set, including nwpp_path76_alturas_link=true and the four take-floor keys: coal_fuel_inventory_plant_grain=true,
  coal_fuel_inventory_take_floor=true, coal_takeorpay_from_data=false, coal_committed_takeorpay_regulated=false.
  The shard must first run scripts/data/curate_coal_receipts.py and scripts/data/curate_coal_stocks.py. Add
  hydro_backfill_year=null for 2019–2022.
- Push the PRECOMMIT and pin its full 40-character SHA.
  - Every shard prompt pre-authorizes `git fetch --depth=1 origin <PIN> && git checkout --detach <PIN>` and states
    that this checks out the pin and is not a sync.
  - Every shard prompt says: launch the solve with nohup and a PID file, poll inside the turn with ~9-minute Bash
    calls, and never end the turn while it runs.
  - Hard stops include the sha256 of campd_ct_heat_rates_NWPP.csv: 29baa2f1ecfa10d9734c7e44cc306a88d527adb28968ea260f3409de37d7ff92.
- Config hard stop: diff run_config.json scenario_config against keeper #14's run_config_<Y>.json (results/calibration/nwppnext7sf_span). Only the arm's key
  may change. Fields absent in the keeper and False in the arm are accepted.
- Keeper #14's P1 demand (unchanged from #13), for the demand hard stop: 279.581 / 292.940 / 289.358 / 298.960 / 280.261 / 290.216 /
  302.532 TWh.
- Shards restart sometimes: four of 14 did in NWPP-NEXT-6 and still finished. Relaunch only on "Setup script failed".
- Each shard pushes its FULL bundle with the .gitignore negation and a plain git add (rule 34(a)).
- Compose with scripts/probes/_nwpp42_compose_span.py --out results/calibration/<name>_span --skip-diagnostics, 2023 leg first
  (--out is a PATH; a bare name writes to the repo root). Then:
  - legitimacy_diagnostics.py ... --json-out <b>/legitimacy_diagnostics.json
  - attestation: wrap scripts/gen_nwppnext7_attestation.py (it reads commit 909cdd30 — fetch that object first)
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
- Leftover shard branches to delete: claude/nwppnext7tf-{2019,2021,2025}, claude/nwppnext7sf-{2019..2025}, plus every
  earlier nwppnext*/rnwpp-* list. The merged lane branches claude/nwppnext7-* can also go.
- GitHub Pages: set Settings → Pages → Source to "GitHub Actions". The legacy branch build overwrote the live
  dashboards with a data-less copy on 2026-09-27.
- Known pre-existing test failures, not NWPP's:
  - tests/unit/config/test_d53_sector_gate_miso_arming.py
  - tests/unit/config/test_d60_arming_batch.py
  - tests/unit/config/test_reserve_config.py
  - tests/unit/model/test_ccs_retrofit.py (off_is_byte_identical)
```
