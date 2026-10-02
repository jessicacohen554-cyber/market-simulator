SESSION R-ERCOT-25 — ERCOT: triage the remaining rubric failures on the r-24 keeper, then arm at most one admissible lever
DATA PROFILE: ercot
MODEL: Opus or Fable (may write core infrastructure — rule 27)

CLAUDE.md is binding. Pay particular attention to rules 1, 13, 14, 19, 21, 28, 29(b), 30(c) and 31–36.
- The parent never solves (rule 32).
- Every backcast year gets its own shard (rule 36).
- Archive each shard once its bytes are in hand (rule 33).
- You may launch and archive shards without asking.

START
- Create your own working branch off origin/main, named claude/r-ercot-25-<short-topic>. Keep it rebase-free.
- Archive R-ERCOT-24b (the session that launched you) once get_session shows it idle.

PRECONDITION
- On main, `frontend/data/backcast/keepers/ERCOT.json` names keeper `2026-10-02-r-24-ordc-published` (bundle `results/calibration/r_ercot24_span`, 2019–2025).
- `audit_keepers --iso ERCOT --check` reads 0 failures.
- If either fails, STOP and report.

READ FIRST
- docs/records/ercot/r-ercot/RESULT-r-ercot-24-ordc-published-curve-2026-10-02.md (§2 per-year table, §6 open gates).
- docs/records/ercot/r-ercot/r_ercot24_scorecard.json; scripts/probes/_r_ercot24_scorecard.py scores any bundle the same way.
- docs/mechanism-testing-matrix.md §5.1 (lever queue) and docs/codebase-site/data/mechanism-matrix/ERCOT.js (cell verdicts).
- FINDING-r-ercot-20-2024-c3a-and-gt-in-cc-2026-09-30.md and FINDING-r-ercot-21-2022-cc-and-wharton-hr-2026-10-01.md.

WHERE ERCOT STANDS (keeper r-24, calibration_verdict --years)
- ISO NOT-YET. CALIBRATED: 2021, 2025.
- 2019 NOT-YET: C3b 0.228; C1 CC_REGULAR +8.85, COAL_PRB −10.48 TWh.
- 2020 NOT-YET: C3b 0.209; C1 CC_REGULAR +10.21, COAL_PRB −11.83 TWh; C3c ledgered (22/56 h).
- 2022 NOT-YET: C1 CC_REGULAR −10.07 TWh (band ±8.00).
- 2023 carve-out NOT-YET: C3a −24.5 %, C3b 0.385 (owner hold, k=33).
- 2024 NOT-YET: C3a −11.4 % (band ±10 %).

TASK 1 — PHASE 0 TRIAGE (zero LP)
- For each open gate above, list the ERCOT matrix cells still `U` or `O` that could plausibly move it, and the evidence each needs. Many `U` cells are transfers from other ISOs (e.g., the CC capacity / summer-derate family for 2022 CC_REGULAR, `gas_basis_measured_by_year`, `coal_captive_marginal_fuel_price`). Check each against rules 1/13/14/19 before treating it as admissible.
- Never re-test a cell adjudicated R/I/G without new evidence (rule 28). The DO-NOT-REDO list below is binding.
- Compute everything you can from committed artifacts (the r-24 bundle carries hourly sidecars and unit_marginal for every year).
- Write a FINDING with the per-gate triage table: candidate, admissibility, the zero-LP expected move, and the decision.

TASK 2 — AT MOST ONE ARM
- If the triage finds an admissible, zero-DOF, structurally real lever with a predicted move on an open gate:
  - build it default-off (with its matrix row and a cell in every shard if it is a new ScenarioConfig field);
  - write the PRECOMMIT (predictions and promotion rule) before any solve;
  - launch one shard per year it moves (`scripts/shard_prompt.py`, full 40-char SHA); compose with `scripts/probes/_r_ercot_compose_span.py --side arm --chp-off`; `stamp_config_partition --check`; register (`dashboard_add_run.py --no-prune`) so `calibration_verdict --years` can score it; run the scorecard probe on both bundles.
- If no admissible lever exists, say so plainly and put the owner a decision card (AskUserQuestion). Options might include: lifting the 2023 k=33 hold, procuring a named data source, or ledgering the remaining gates as accepted model-class limitations. Do not invent a lever to have something to solve.

TASK 3 — PROMOTION (if an arm ran)
- The owner's standing instruction: "Is it an improvement? Then promote." Promote if your PRECOMMIT rule holds; otherwise use a decision card.
- Mechanics (as R-24b):
  - `promote_keeper.py --iso ERCOT --bundle …` (its audit stops on the expected E13 for the outgoing keeper);
  - `prune_iso_runs --iso ERCOT --force-uncite`;
  - re-point `config_partition.configs[*].run_id/bundle` in keepers/ERCOT.json (and add an `r_ercot25_extension` with the leg SHAs);
  - `build_status --iso ERCOT`; `audit_keepers --iso ERCOT --check` must read 0 failures; `check_registry_payload_parity`; `check_mechanism_matrix --base origin/main`.
  - `promote_keeper` rewrites keepers/ERCOT.json and forecast/program-status.json with a different JSON indent. Restore each file's own format (indent 2 / indent 1, respectively) so the diff shows only real changes. Rewrite the ERCOT gate (a) `detail` with the new numbers, keeping the `marker complete=False final=False …` phrase, and prepend `corrected_by`.
  - `check_promotion_completeness` no longer exists (removed at cleanup-A); the audit and parity gates replace it.
  - The keeper bundle commits `hourly/unit_marginal_<year>.parquet` for every year (rule 15).
- Update the matrix keeper stamp + cell, §5.1 header, the calibration log; write the RESULT.
- Create the PR and merge it.

ROUTE, DO NOT FIX
- 2019/2020 C1 coal/CC mirror: fenced coal conduct; raise only with new admissible evidence.
- Wharton CC marginal-HR estimator (card only).
- Bench display rows 7512 / 55501 / 55545.
- Other ISOs' CC heat-rate artifacts and stale solve-surface pins.
- Pre-existing main failures (identical on clean main): test_golden_manifest_provenance (11 errors + 4 failures); test_bench_stamp_payload::test_d; test_d60_arming_batch Q42; test_gas_offer_zonal_anchor_vintage (2); test_ccs_retrofit (2); test_d53_sector_gate_miso_arming; test_export; test_soundness end-to-end; test_fleet_arrays_golden (ERCOT 2023 golden); CAISO/MISO/NEISO/NYISO solve-surface pins.

DO-NOT-REDO
- Everything in R-ERCOT-20/21/22/23/24's lists.
- 2024 C3a: R-ERCOT-20 closed it as the compressed-distribution / tight-hour object (scarcity exhaustion ercot-95…231; R-ERCOT-12). Reopen only with genuinely new evidence.
- The ORDC curve: the published curve is now armed (R-ERCOT-24). Its ~0.85× reading vs RTORPA is the Jensen sign (hourly-mean reserves on a convex curve), not a defect. Do not "correct" it.
- The ORDC digitization (two reads agree to one pixel; NP6-576 retention-expired on the free path; the credentialed API is owner-declined). Reopen only with a new free source.
- Daily Waha/HSC gas: no free source; paid sources refused by owner ruling 2026-08-04.
- The 2023 carve-out k=33 stays on owner hold.

LESSONS FROM R-ERCOT-24b
- `calibration_verdict` only scores a registered run: register the arm with `dashboard_add_run.py --no-prune` before scoring.
- The per-year shard dirs must be removed locally after promotion, or `check_registry_payload_parity` flags them as dead output. Their bytes stay on the shard branches by SHA.
- The zero-LP re-pricing predicted 2020–2023 inside every band. Re-dispatch pushed 2024/2025 slightly below the bands, and 2019's adder moved about a third as much as predicted.

DIRECTIONS FROM THE OWNER (carry forward verbatim in spirit)
- **Branches and PRs.** Check for any unmerged branches or PRs for your ISO and decide whether anything needs to be salvaged. If so, integrate it into your branch and close the open PRs, or say what can be deleted. Merge.
- **Promotion.** When done, promote if it is a good candidate. If it is an improvement, PROMOTE ("Is it an improvement? Then promote"). Create a PR and merge, archive the shards, and launch a handoff to continue calibrating this ISO if rubric failures remain.
- **Decision cards.** Present decisions for the owner as clickable decision cards (AskUserQuestion), not inline text. Only ask when you genuinely need the owner's input.
- **Complete/frontier.** If your lane is calibrated and the rubric clears for all years, check the complete/frontier declaration criteria: the calibration-complete.json note, keepers/ERCOT.json frontier_history, and Q5 re-entry (a new explicit owner declaration on a CALIBRATED keeper). If you reach complete/frontier, say so plainly as a decision card. Give this same direction to any chained handoff.
- **Chaining.** When you launch the next session, have it archive yours when safe, and give it these same directions, including launching a new handoff. At the nesting limit (create_session refuses at lineage depth 8), make your last message a complete copy-paste handoff prompt to start another chain.

REFS FOR THE OWNER TO DELETE (sessions cannot delete refs)
- claude/r-ercot23-arm-2019, claude/r-ercot23-arm-2021, claude/r-ercot22-arm-2019
- claude/r-ercot-23-ordc-2021 (merged), claude/r-ercot-24-ordc-vintage (merged)
- claude/r-ercot-24-2019 … claude/r-ercot-24-2025 (seven shard branches)
- claude/r-ercot-24b-handoff-zi0io4 (merged)

REPORT
- Lead with the ERCOT headline.
- Then give the per-gate triage outcome; any arm's per-year before/after and prediction scorecard; what is committed and merged; the promotion outcome; the leftover refs.
