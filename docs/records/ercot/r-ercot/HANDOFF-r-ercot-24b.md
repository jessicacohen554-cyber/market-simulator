SESSION R-ERCOT-24b — ERCOT: solve, score and promote the published ORDC curve (new chain root)
DATA PROFILE: ercot
MODEL: Opus or Fable (writes core infrastructure — rule 27)

CLAUDE.md is binding. Pay particular attention to rules 1, 13, 14, 19, 21, 28, 29(b), 30(c) and 31–36.
- The parent never solves (rule 32).
- Every backcast year gets its own shard (rule 36).
- Archive each shard once its bytes are in hand (rule 33).
- You may launch and archive shards without asking.

WHY THIS SESSION EXISTS
- R-ERCOT-24 (session_0168mZ9QtCr2rsh7EXcWwbw3) built and merged the change, then hit the lineage-depth limit (8) before it could launch shards. You are a new chain root.
- Archive R-ERCOT-24 once get_session shows it idle.
- Also archive R-ERCOT-23 (session_018ReW9F6fcamHfnwY6ejsNP). R-ERCOT-24's archive call was refused by its permission classifier.

PRECONDITION
- On main, `frontend/data/backcast/keepers/ERCOT.json` names keeper `2026-10-01-r-23-swcap-hourly` (bundle `results/calibration/r_ercot23_span`).
- `ScenarioConfig.ercot_ordc_published_curve` exists (default off).
- Commit `02f67d135c729345371d156cadec29bb697432d6` is reachable from main.
- If any of these fails, STOP and report.

READ FIRST
- docs/records/ercot/r-ercot/PRECOMMIT-r-ercot-24-ordc-published-curve-2026-10-01.md: the predictions and the promotion rule, fixed before any solve. Do not edit §5/§6.
- docs/records/ercot/r-ercot/r_ercot24_phase0.json (scripts/probes/_r_ercot24_ordc_vintage_id.py)
- docs/records/ercot/r-ercot/SHARD-PROMPTS-r-ercot-24.md: seven ready prompts pinned to 02f67d13.
- The owner decision card is already answered: "All years incl. 2023 (Recommended)". Do not re-ask.

TASK 1 — SOLVE (seven shards, one per year 2019–2025)
- For each LEG in SHARD-PROMPTS-r-ercot-24.md, call create_session with:
  - source_url https://github.com/jessicacohen554-cyber/market-simulator
  - source_revision 02f67d135c729345371d156cadec29bb697432d6
  - the leg's text block verbatim as the prompt.
- Gate on each shard's report:
  - the hard stops;
  - `git ls-tree -r <sha> -- results/calibration/r_ercot_24_<Y>` is non-empty and lists dispatch/<Y>_P1.parquet.
- Fetch the bytes, then archive the shard.

TASK 2 — COMPOSE, SCORE, PREDICTION SCORECARD
- Compose with `scripts/probes/_r_ercot_compose_span.py --side arm --chp-off` into `results/calibration/r_ercot24_span`.
- Run `stamp_config_partition` with `--leg Y=run_config_Y.json` for each year, then `--check`.
- Copy the keeper's calibration_attestation.json and prepend governance.attested_by.
- Score the incumbent first (`calibration_verdict --years`), then the arm.
- Per year, report: C3a, C3b, C3c, C8 ST_GAS, C1 coal/CC/ST_GAS, LW price, ORDC adder LW (against measured RTORPA), slack, and h > $1k. Score each against PRECOMMIT §5.
- Write `RESULT-r-ercot-24-ordc-published-curve-<date>.md`.
- Update the ERCOT matrix cell `ercot_ordc_published_curve` (O → K or R, with citation) and docs/mechanism-testing-matrix.md §5.1.

TASK 3 — PROMOTION (PRECOMMIT §6)
- **Promote** under the owner's standing instruction ("Is it an improvement? Then promote") if both hold:
  - the ORDC adder moves toward measured RTORPA in 2019, 2020, 2022, 2023 and 2024;
  - no year's determination worsens.
  This holds even if 2022 C3a crosses −10 %.
- **Otherwise**, present the owner a decision card (AskUserQuestion).
- **Mechanics** (as R-23):
  - `dashboard_add_run.py --no-prune`, then promote_keeper;
  - audit_keepers → prune --force-uncite → audit_keepers;
  - `check_promotion_completeness --iso ERCOT` must pass.
- **The promotion PR also:**
  - re-keys `frontend/data/forecast/program-status.json` gate (a) for ERCOT only, keeping the trailing `marker complete=False final=False …` phrase;
  - updates keepers/ERCOT.json `*_extension.legs` with the seven leg SHAs.
- Merge it.

ROUTE, DO NOT FIX (unchanged from R-ERCOT-24)
- 2019/2020 C1 coal/CC mirror: fenced coal conduct; raise only with new admissible evidence.
- Wharton CC marginal-HR estimator (card only).
- Bench display rows 7512 / 55501 / 55545.
- Other ISOs' CC heat-rate artifacts and stale solve-surface pins.
- Pre-existing main failures, identical on clean main:
  - test_golden_manifest_provenance (11 errors + 4 failures)
  - test_bench_stamp_payload::test_d
  - test_d60_arming_batch Q42
  - test_gas_offer_zonal_anchor_vintage (2)
  - test_ccs_retrofit (2)
  - plus the R-23 list.

DO-NOT-REDO
- Everything in R-ERCOT-20/21/22/23's lists.
- The digitization: two independent reads agree to one pixel. The exact NP6-576 tables are retention-expired on the free MIS path, and the credentialed API is owner-declined. Reopen only with a new free source.
- The 2023 carve-out k=33 stays on owner hold. Only its ORDC curve moves, per the owner card.

LESSONS FROM R-ERCOT-24
- Phase 0 re-prices the keeper's cleared ORDC reserve level as `req_total_K − shortfall` from `reserve_family_<Y>.parquet`. It reproduced the keeper's family dual at r ≥ 0.99.
- With the right published curve, the formula on hourly-mean measured reserves reads ~0.85× of RTORPA. That is the convexity (Jensen) sign, not a defect. Do not "correct" it.
- Run G-DRIFT with the AST diff (docstrings stripped): 133 of 147 files were comment-only.

DIRECTIONS FROM THE OWNER (carry forward verbatim in spirit)
- **Branches and PRs.** Check for any unmerged branches or PRs for your ISO and decide whether anything needs to be salvaged. If so, integrate it into your branch and close the open PRs, or say what can be deleted. Merge.
- **Promotion.** When done, promote if it is a good candidate. If it is an improvement, PROMOTE ("Is it an improvement? Then promote"). Create a PR and merge, archive the shards, and launch a handoff to continue calibrating this ISO if rubric failures remain.
- **Decision cards.** Present decisions for the owner as clickable decision cards (AskUserQuestion), not inline text. Only ask when you genuinely need the owner's input.
- **Complete/frontier.** If your lane is calibrated and the rubric clears for all years, check the complete/frontier declaration criteria: the calibration-complete.json note, keepers/ERCOT.json frontier_history, and Q5 re-entry (a new explicit owner declaration on a CALIBRATED keeper). If you reach complete/frontier, say so plainly as a decision card. Give this same direction to any chained handoff.
- **Chaining.** When you launch the next session, have it archive yours when safe, and give it these same directions, including launching a new handoff. At the nesting limit (create_session refuses at lineage depth 8), make your last message a complete copy-paste handoff prompt to start another chain.

REFS FOR THE OWNER TO DELETE (sessions cannot delete refs)
- claude/r-ercot23-arm-2019
- claude/r-ercot23-arm-2021
- claude/r-ercot22-arm-2019
- claude/r-ercot-23-ordc-2021 (merged)
- claude/r-ercot-24-ordc-vintage (once merged)
- the seven claude/r-ercot-24-<Y> shard branches, after promotion

REPORT
- Lead with the ERCOT headline.
- Then give:
  - the per-year before/after (C3a, C3b, C3c, C8 ST_GAS, C1 coal/CC/ST_GAS, LW price, slack, h > $1k);
  - the prediction scorecard;
  - what is committed and merged;
  - the promotion outcome;
  - the leftover refs.
