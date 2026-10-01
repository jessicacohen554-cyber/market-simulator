SESSION R-ERCOT-21 — ERCOT: the 2022 CC_REGULAR under-run and the residual Wharton CC over-run
DATA PROFILE: ercot
MODEL: Opus or Fable (writes core infrastructure — rule 27)
CLAUDE.md is binding — rules 1, 13, 14, 17, 18, 19, 21, 23, 24, 25, 28, 29(b), 30(c) (amended 2026-09-30: a held-out miss DOWNGRADES the ISO), 31–36 especially.
- The parent never solves (rule 32(a)); every backcast year gets its own shard (rule 36); archive each shard once its bytes are in hand (rule 33).
- Promote only on the owner's say-so or standing instruction (rules 31/35). A promotion PR also re-keys frontend/data/forecast/program-status.json gate (a) for ERCOT only and passes scripts/check_promotion_completeness.py --iso ERCOT.
- You may launch and archive shards without asking.

HOUSEKEEPING FIRST
- Archive the parent session R-ERCOT-20 (session_01YbKFYAc4g2WNaP7qqu7bo4) once get_session shows it idle.
- Check for unmerged ERCOT branches and PRs; salvage anything needed, close stale PRs, LIST the refs the owner must delete (sessions cannot delete refs, rule 33(f)). Known leftovers, no unique record: claude/r-ercot20-arm-{2019..2025}, claude/r-ercot19-arm-{2024,2025}, claude/r-ercot19b-arm-{2019,2020,2021r,2022,2023,2024,2025}, claude/r-ercot19c-arm-{2019,2020,2021,2022r,2023,2024,2025}.

PRECONDITION: frontend/data/backcast/keepers/ERCOT.json on main names keeper 2026-09-30-r-20-gt-split (bundle results/calibration/r_ercot20_span, 2019–2025), ISO NOT-YET. If not, STOP and report.

READ FIRST
- docs/handoffs/r-ercot/RESULT-r-ercot-20-gt-split-2026-09-30.md (the per-year table + prediction scorecard)
- docs/handoffs/r-ercot/FINDING-r-ercot-20-2024-c3a-and-gt-in-cc-2026-09-30.md (2024 C3a decomposition; econ-vs-DAM test)
- docs/handoffs/r-ercot/PRECOMMIT-r-ercot-20-gt-split-2026-09-30.md
- docs/handoffs/r-ercot/DESIGN-r-ercot-20-d4-day-grain-drag-mask-2026-09-30.md (HELD by owner — do not build)
- the ERCOT matrix shard docs/codebase-site/data/mechanism-matrix/ERCOT.js and docs/mechanism-testing-matrix.md §5.1 (rule 28(a))

STANDING STATE (r-20 keeper, P1)
- 2024 CALIBRATED (C3a −9.9 %, 0.1 pp inside the edge); 2025 CALIBRATED (C3a −8.2 %); 2021 CALIBRATED.
- 2023 carve-out NOT-YET: C3a −18.5 % / C3b 0.270 (OWNER HOLD on k=33 — do not touch).
- 2022 NOT-YET: C1 CC_REGULAR −8.83 TWh vs ±8.00 (the only 2022 failure; COAL_PRB +5.99, C3a −7.7 %). Under amended rule 30(c) this held-out miss downgrades the ISO.
- 2019 NOT-YET: C3a +25.7 %, C3b 0.566, C1 CC_REGULAR +8.03, COAL_PRB −9.05. 2020 NOT-YET: C3b 0.236, C1 CC_REGULAR +10.81, COAL_PRB −11.04.

TASK 1 — THE 2022 CC_REGULAR UNDER-RUN (zero LP first, from the committed keeper hourlies + per-plant legs)
- Where is the −8.83 TWh? By plant (EIA-923 basis, CC portion only — CT+CA prime movers), by month, by hour class. 2022 is the high-gas-price year: test whether coal (COAL_PRB +5.99) is displacing CC in shoulder hours, and whether that is a coal offer/availability object (coal offers are FENCED — do not touch coal offers; owner data decision on the 2019–22 SCED key stays CLOSED) or a CC availability/commitment object.
- The R-ERCOT-19 arms B/C and R-ERCOT-20 all moved 2022 CC down by ~1 TWh: any CC-dispatch lever trades 2022 C1 against 2024 C3a (now 0.1 pp inside). Predict both before solving.
- PRECOMMIT before any solve. Any lever must be structural, measured, zero-DOF. Offer multipliers FENCED (rule 1(c)).

TASK 2 — THE RESIDUAL WHARTON CC OVER-RUN (data, rule 14)
- After the split, Wharton's CC half (3469, 663.6 MW) still runs 3.17 TWh vs 0.56 EIA-923 CC in 2024. Its base HR is eGRID PLHTRT 10.43 (a plant average INCLUDING the now-split GTs); the measured CAMPD CC rate is flagged steam_not_metered. Measure an EIA-923 CC-only heat rate (CT+CA elec fuel / net gen ≈ 9.5 in 2024) and assess whether the heat-rate resolver should read it (a measured input on the right boundary) — and how the CC econ multiplier (~0.70 × base from the class CAMPD marginal-HR summary) applies to a 1974 CC. Card before building.

ROUTE, DO NOT FIX
- Silas Ray (3559) 61 MW GT: not split (EIA-923 class override + mixed_fossil_plants relabel would mismatch classes). ST_GAS mixed plants (Braunig 3612, 3628, 6243, 3576) carry GTs too, but model ST caps sit below ST nameplate — needs its own phase 0.
- D-1 diagnostic compares the CC-only parent against the whole-plant CEMS actual at the three split plants (display/diagnostic only).
- Everything in R-ERCOT-20's handoff ROUTE list (Decker Creek seam, Decker/Silas Ray CAMPD double count, split-child bench display row, COAL-SUB crosswalk coal-row drop, CAMPD TX 2018 off disk, R2 overlay/cap, mislabelled 60d_DAM 2020 file, GAS_OFFER_MARGIN_ANCHOR_BY_ZONE non-reproduction (rule 23), South CHP bench gap, West Waha 2020/21).

DO-NOT-REDO (matrix R/I/G or landed)
- Everything in R-ERCOT-20's list, plus: the 2024 tight-hour lever (closed R-ERCOT-12; R-ERCOT-20 re-confirmed: 100 % system-level, zonal spread contributes exactly 0); the econ-vs-DAM HR test (R-ERCOT-20: corr 0.80 vs 0.80 — no offer-shape defect); the R-ERCOT-19 commit-profile sub-gates; the D-4 1–5-day lay-up companion read (D-A, tested, misses); the GT split itself (landed — never revert for fit, rule 14).

LESSONS FROM R-ERCOT-20
- A per-plant over-run that scales with heat rate can be a CAPACITY-BOUNDARY defect, not an offer one: check EIA-860 prime movers against the model's class capacity before designing commitment mechanics.
- Shard prompts: docs/handoffs/r-ercot/SHARD-PROMPTS-r-ercot-20.md (replay_keeper on the keeper bundle, no --set, signature + input sha256 hard stops). Compose with scripts/probes/_r_ercot_compose_span.py --side arm --chp-off; stamp_config_partition with --leg Y=run_config_Y.json for each year.
- A fresh container needs `uv sync --frozen`. Seven legs + a span is ~2.2 GB.

DIRECTIONS FROM THE OWNER (carry forward verbatim in spirit)
- Check for any unmerged branches or PRs for your ISO and decide whether anything needs to be salvaged. If so, integrate it into your branch and close the open PRs, or say what can be deleted. Merge.
- When done, promote if it is a good candidate. If it is an improvement, PROMOTE (owner's standing instruction: "Is it an improvement? Then promote"). Create a PR and merge, archive the shards, and launch a handoff to continue calibrating this ISO if rubric failures remain.
- Present decisions for the owner as clickable decision cards (AskUserQuestion), NOT inline text. Only ask when you genuinely need the owner's input.
- If your lane is calibrated and the rubric clears for all years, check the complete/frontier declaration criteria (calibration-complete.json note, keepers/ERCOT.json frontier_history, Q5 re-entry = a new explicit owner declaration on a CALIBRATED keeper). Settle the keeper config and clear the tasks that block declaration. If you reach complete/frontier, say so plainly in your final message, as a decision card, so the owner can approve. Give this same direction to any chained handoff.
- When you launch the next session, have it archive yours when safe, and give it these same directions, including launching a new handoff to continue the chain. If you are at the nesting limit (create_session refuses at lineage depth 8), make your last message a complete copy-paste handoff prompt to start another chain.

REPORT: lead with the ERCOT headline, then: per-year before/after (C3a, C3b, C3c, C8 ST_GAS, C1 coal/CC/ST_GAS, LW price, slack, h > $1k); the 2022 CC decomposition table; the prediction scorecard; what is committed/merged; the promotion outcome; the leftover refs for the owner to delete.
