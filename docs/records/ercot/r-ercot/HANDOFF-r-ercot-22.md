SESSION R-ERCOT-22 — ERCOT: why 365 MW of CC moves the scarcity tail, and the 2024 C3a edge
DATA PROFILE: ercot
MODEL: Opus or Fable (writes core infrastructure — rule 27)
CLAUDE.md is binding — rules 1, 13, 14, 17, 18, 19, 21, 23, 24, 25, 28, 29(b), 30(c) (amended 2026-09-30: a held-out miss DOWNGRADES the ISO), 31–36 especially.
- The parent never solves (rule 32(a)); every backcast year gets its own shard (rule 36); archive each shard once its bytes are in hand (rule 33).
- Promote only on the owner's say-so or standing instruction (rules 31/35). A promotion PR also re-keys frontend/data/forecast/program-status.json gate (a) for ERCOT only (KEEP the trailing `marker complete=False final=False …` phrase — check_promotion_completeness requires it) and passes scripts/check_promotion_completeness.py --iso ERCOT.
- You may launch and archive shards without asking.

HOUSEKEEPING FIRST
- Archive the parent session R-ERCOT-21 (session_01UroA4AtXfFhjTNEnGwknmK) once get_session shows it idle.
- Check for unmerged ERCOT branches and PRs; salvage anything needed, close stale PRs, LIST the refs the owner must delete (sessions cannot delete refs, rule 33(f)). Known leftovers, no unique record: claude/r-ercot21-arm-{2019..2025}, claude/r-ercot20-arm-{2019..2025}, claude/r-ercot-20-c3a-decomp, claude/r-ercot-21-cc2022 (once merged).

PRECONDITION: frontend/data/backcast/keepers/ERCOT.json on main names keeper 2026-10-01-r-21-lostpines-ccid (bundle results/calibration/r_ercot21_span, 2019–2025), ISO NOT-YET. If not, STOP and report.

READ FIRST
- docs/handoffs/r-ercot/RESULT-r-ercot-21-lostpines-cc-identity-2026-10-01.md (per-year table, where-the-price-fell decomposition, prediction scorecard)
- docs/handoffs/r-ercot/FINDING-r-ercot-21-2022-cc-and-wharton-hr-2026-10-01.md (2022 CC = coal mirror; Wharton HR; Lost Pines)
- docs/handoffs/r-ercot/PRECOMMIT-r-ercot-21-lostpines-cc-identity-2026-10-01.md
- the ERCOT matrix shard docs/codebase-site/data/mechanism-matrix/ERCOT.js and docs/mechanism-testing-matrix.md §5.1 (rule 28(a))

STANDING STATE (r-21 keeper, P1)
- 2021 CALIBRATED; 2025 CALIBRATED (C3a −9.2 %).
- 2024 NOT-YET: C3a −11.1 % (was −9.9 % on r-20; the only 2024 failure).
- 2023 carve-out NOT-YET: C3a −24.2 % / C3b 0.380 (OWNER HOLD on k=33 — do not touch).
- 2022 NOT-YET: C1 CC_REGULAR −9.87 vs ±8.00 (coal-conduct mirror; coal offers FENCED; the 2019–22 SCED data decision stays CLOSED).
- 2019 NOT-YET: C3a +19.4 %, C3b 0.446, C1 CC_REGULAR +8.85, COAL_PRB −10.48. 2020 NOT-YET: C3b 0.221, C1 CC_REGULAR +10.41, COAL_PRB −11.77.

TASK 1 — THE SCARCITY-TAIL SENSITIVITY (zero LP first)
- R-ERCOT-21 restored 365 MW of real CC capacity (Lost Pines). LW fell $2.92 (2019) and $3.73 (2023), 82–83 % of it in hours the r-20 keeper priced above $200. One mid-merit CC should not move the tail that much unless the tail is a knife-edge on online reserve.
- Decompose hour-by-hour on the committed hourlies (r-21 on main; r-20's are in git history at the R-ERCOT-21 merge parent `dfbbf599`): in the hours that left the > $200 band, which reserve row / ORDC adder / online-capacity envelope binding changed (hourly/reserve_family_<Y>.parquet, system ordc_adder, class_hourly). Compare the model's tight-hour reserve margin against the ERCOT-measured one (the RTORPA / RTOLCAP series on disk).
- The question is structural: is the model's tight-hour supply stack or ORDC response mis-specified (rule 1), in a way that also explains 2024 C3a −11.1 %? The R-ERCOT-12 2024 tight-hour lever is CLOSED (100 % system-level) — do not re-open it without new evidence. This is a different question (the slope of price on reserve).
- PRECOMMIT before any solve. Any lever must be structural, measured, zero-DOF. Offer multipliers FENCED (rule 1(c)).

TASK 2 — ATTRIBUTION (optional, owner card first)
- The R-ERCOT-21 arm moved two inputs at once. If Task 1 needs to know which one moved the tail, a Lost-Pines-only arm (7 shards, ~35 min) separates them. Card the cost before spending it.

ROUTE, DO NOT FIX
- Wharton CC over-run (3.31 vs 0.56 TWh 2024): class marginal-HR curve on a 1974 CC; steam_not_metered means no CAMPD per-plant curve exists. A new per-plant marginal-HR estimator would be a derive — card it, do not build.
- Bench per-plant display rows omit 7512 / 55501 / 55545 (classFull is correct; display only).
- The other ISOs' CC heat-rate artifacts are stale against the deriver (rule 25 — their lanes).
- Everything routed by R-ERCOT-20/21 (Silas Ray GT, ST_GAS mixed plants, Decker seam, CAMPD TX 2018 off disk, etc.).

DO-NOT-REDO (matrix R/I/G or landed)
- Everything in R-ERCOT-20/21's lists; the 2022 CC decomposition (R-ERCOT-21: coal mirror, fenced); the GT split and the Lost Pines / identity corrections (landed — never revert for fit, rule 14).

LESSONS FROM R-ERCOT-21
- Capacity added in tight hours moves C3a far more than a mid-merit estimate predicts; predict price effects by hour band, using the committed tail.
- A bench-side BTM change moves C1's actual too: predict both sides of the C1 identity.
- The shared bench parts are rewritten by every registration — score the incumbent against its own committed bench, not the working tree.
- Shard prompts: docs/handoffs/r-ercot/SHARD-PROMPTS-r-ercot-21.md (replay_keeper on the keeper bundle, no --set, signature + input sha256 hard stops). Compose with scripts/probes/_r_ercot_compose_span.py --side arm --chp-off; stamp_config_partition with --leg Y=run_config_Y.json for each year; copy the keeper's calibration_attestation.json and prepend to attested_by; register with dashboard_add_run.py --no-prune.
- A fresh container needs `uv sync --frozen`.

DIRECTIONS FROM THE OWNER (carry forward verbatim in spirit)
- Check for any unmerged branches or PRs for your ISO and decide whether anything needs to be salvaged. If so, integrate it into your branch and close the open PRs, or say what can be deleted. Merge.
- When done, promote if it is a good candidate. If it is an improvement, PROMOTE (owner's standing instruction: "Is it an improvement? Then promote"). Create a PR and merge, archive the shards, and launch a handoff to continue calibrating this ISO if rubric failures remain.
- Present decisions for the owner as clickable decision cards (AskUserQuestion), NOT inline text. Only ask when you genuinely need the owner's input.
- If your lane is calibrated and the rubric clears for all years, check the complete/frontier declaration criteria (calibration-complete.json note, keepers/ERCOT.json frontier_history, Q5 re-entry = a new explicit owner declaration on a CALIBRATED keeper). Settle the keeper config and clear the tasks that block declaration. If you reach complete/frontier, say so plainly in your final message, as a decision card, so the owner can approve. Give this same direction to any chained handoff.
- When you launch the next session, have it archive yours when safe, and give it these same directions, including launching a new handoff to continue the chain. If you are at the nesting limit (create_session refuses at lineage depth 8), make your last message a complete copy-paste handoff prompt to start another chain.

REPORT: lead with the ERCOT headline, then: per-year before/after (C3a, C3b, C3c, C8 ST_GAS, C1 coal/CC/ST_GAS, LW price, slack, h > $1k); the tail decomposition table; the prediction scorecard; what is committed/merged; the promotion outcome; the leftover refs for the owner to delete.
