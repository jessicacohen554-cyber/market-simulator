SESSION R-ERCOT-18 — ERCOT: fix the plant-3452 (Lake Hubbard) `st_netload_drag` provenance that denies 2022 its C8 escape; then continue the 2019/2020 residual lane
DATA PROFILE: ercot
MODEL: Opus or Fable (writes core infrastructure — rule 27)
CLAUDE.md is binding — rules 1, 13, 14, 17, 18, 19, 21, 23, 24, 25, 28, 29(b), 31–36 especially. The parent never solves (rule 32(a)); every backcast year gets its own shard (rule 36); archive each shard once its bytes are in hand (rule 33); promote only on the owner's say-so or the owner's standing instruction (rules 31/35). A promotion PR also re-keys frontend/data/forecast/program-status.json gate (a) for ERCOT only and passes scripts/check_promotion_completeness.py --iso ERCOT. You may launch and archive shards without asking.

HOUSEKEEPING FIRST
- Archive the parent session R-ERCOT-17 (session_019jFPNzDT2wAMmxp9itGXGT) once get_session shows it idle. Its PR is #6892.
- Check for unmerged ERCOT branches and PRs. Salvage anything needed, close stale PRs, and LIST the refs the owner must delete (sessions cannot delete refs, rule 33(f)). Known leftovers carry no unique record: claude/r-ercot15-arm-2019, claude/r-ercot15-arm-2020, and claude/r-ercot17-arm-{2019..2025}, unless the merge of #6892 removed them.

PRECONDITION: frontend/data/backcast/keepers/ERCOT.json on main names keeper 2026-09-29-r-17-south-texas (bundle results/calibration/r_ercot17_span, 2019–2025), ISO NOT-YET. If not, STOP and report.

READ FIRST: docs/records/ercot/RESULT-r-ercot-17-south-texas-pool-2026-09-29.md (all of it); docs/records/ercot/PRECOMMIT-r-ercot-17-south-texas-pool-2026-09-29.md; results/calibration/r_ercot17_span/legitimacy_diagnostics.json (D2/D4 rows for ST_GAS and plant 3452, every year); scripts/legitimacy_diagnostics.py (D4_WINDOWS, the unit-conduct check); the st_netload_drag / gas_st_netload_drag mechanism in src/ (its window, driver, per-plant eligibility); the ERCOT matrix shard docs/codebase-site/data/mechanism-matrix/ERCOT.js and docs/mechanism-testing-matrix.md §5.1 (rule 28(a)).

THE OBJECT (R-ERCOT-17, measured)
- 2022 went CALIBRATED → NOT-YET on C8 alone. ST_GAS forced share is 30.4 % (cap 30 %; 28.7 % on the prior keeper). The above-cap escape (rule 21: D-4 window + D-1 shape) fails on one row: D-4 unit-conduct FAIL for st_netload_drag at plant 3452 (Lake Hubbard, North, ST_GAS, 927.5 MW, min-run/down 8 h).
  - The floor binds 4,662 h at 0.43 TWh, window h0-23.
  - The unit's CAMPD meter reads zero 76 % of the time (median 0 MW).
  - The same FAIL is present on the prior keeper (0.4255 TWh, 4,634 h). It is pre-existing, not caused by the pool.
- Rule 17: a floor binding in hours its own driver evidence says the unit is offline is a bug by definition. Characterize at zero LP first:
  - Why does st_netload_drag reach 3452 at all? Check eligibility by unit physics (rule 18), the driver, and the window.
  - Is 3452's measured conduct a mothball or seasonal layup that the mechanism's eligibility should read?
  - Which other plants/years carry the same D-4 FAIL (2020/2021 too, per the shard reports)?
- Fix the provenance, not the cap. Never exempt the unit to pass the gate, never tune the window to the residual, and never stack a new floor (rule 19). If the fix is a structural eligibility change it needs a rule-24 flag and its matrix row, or an explicit statement that it re-derives a frozen parameter because its source changed (rule 23).
- Then solve every year the fix touches (one shard per year, rule 36), compose with the keeper's own untouched legs, and score. Promote under the standing instruction if it is an improvement. If any train-year determination flips worse, send a decision card and keep every bundle (rule 31).

TASK 2 — CONTINUE THE LANE (phase 0 first, zero LP; PRECOMMIT before any solve)
- Remaining 2019/2020 objects on r-17: 2019 C3a +23.9 % / C3b 0.538 / C1 CC_REGULAR +9.70, COAL_PRB −9.48; 2020 C3b 0.229 / C1 CC_REGULAR +12.41, COAL_PRB −11.57.
- NEW (R-ERCOT-17): with the thin-sample row gone, South merchant gas now OVER-runs 1.13–1.24× in 2019 and 2022–2025. Characterize before any lever (is it commitment? heat rate? the South CHP split?).
- The 2024/2025 South/South_Central/North member rows in ercot_zonal_gas_hub.csv are on earlier EIA-923 vintages than the published Finals (rule-23 data update, source changed; see RESULT §2 of the R-ERCOT-17 PRECOMMIT).
- West Waha 2020/2021: the annual basis is NOT citable. 2019 (−1.66) and the neg-day counts are citable. Build from EIA NGWU weekly prints only if every row the mechanism reads is citable.
- The South CHP shortfall is a separate object. Characterize it; do not fix it blind.
- The 2019/2020 coal stay-on object stays FENCED (coal offers untouched; coal_offer_level_rebasis R; 2019–22 SCED key declined).

OWNER DATA DECISION STAYS CLOSED: the 2019–22 SCED key. Do not touch coal offers. 2023 carve-out: OWNER HOLD on k=33. No re-declaring or sweeping offer multipliers (rule 1(c)).

ROUTE, DO NOT FIX: SPP-48 Oklaunion (SPP lane, rule 25); the CAISO gate-(a) row and FR-22 (CAISO lane); the MISO solve-surface pin (MISO lane); the Decker Creek steam retirement seam; the Decker/Silas Ray CAMPD-backfill double count; the split-child bench display row; Fusco in MISO's fleet; the COAL-SUB crosswalk coal-row drop; base-red fast-tier tests (MISO pin, d53/d60 pins, COAL WEFOR subtest); CAMPD TX 2018 off disk; the R2 overlay/cap composition; the mislabelled 60d_DAM_Gen_Resource_Data_2020_Jul-Dec_Oct-Dec.parquet; the frozen GAS_OFFER_MARGIN_ANCHOR_BY_ZONE non-reproduction (rule 23).

DO-NOT-REDO (matrix R/I/G or landed): the vintage anchor (both cells R); the window × partial family; coal_offer_level_rebasis; measured_chp_heat_rates; the West/Panhandle split (CLOSED); the C3c scarcity-tail exhaustion record (ercot-95…231); the 2023 carve-out level (owner hold); the Parish split, Frontera membership, 2019 LR credit + RTOLCAP cap, Oklaunion membership, ercot_swcap_vintage, the Sandy Creek commission-year key, the curated-sheet coal-HR population, the Oklaunion measured heat rate, and the pooled South-Texas basis (landed R-ERCOT-11…17 — never revert any for fit, rule 14); the 2024 tight-hour lever (closed at R-ERCOT-12).

LESSONS FROM R-ERCOT-17
- The ERCOT zonal spread is recentred to a capacity-weighted mean of zero. Moving one zone's row shifts every other gas unit by the opposite constant. Predict with that in mind; prices barely moved there because the cheaper zone then set price in more hours.
- Rebase-free: merge origin/main into your branch, never rebase it, so the shards' pinned SHA stays in history.
- Shard prompt template: docs/records/ercot/r-ercot/SHARD-PROMPTS-r-ercot-17.md (partition signatures per year: 2019–2022 swcap true / ep_referenced true / CC_REGULAR.peak 151.008; 2023 true / FALSE / 151.008; 2024–2025 false / true / 4.576; CT_PEAKER.peak 433.95 / 433.95 / 13.15). Update the zonal-hub sha256 there to the committed value.
- On a fresh container, delete scratch worktrees; the disk allowance is ~8 GB free.

DIRECTIONS FROM THE OWNER (carry forward verbatim in spirit):
- Check for any unmerged branches or PRs for your ISO and decide whether anything needs to be salvaged. If so, integrate it into your branch and close the open PRs, or say what can be deleted. Merge.
- When done, promote if it is a good candidate. If it is an improvement, PROMOTE (owner's standing instruction: "Is it an improvement? Then promote"). Create a PR and merge, archive the shards, and launch a handoff to continue calibrating this ISO if rubric failures remain.
- Present decisions for the owner as clickable decision cards (AskUserQuestion), NOT inline text. Only ask when you genuinely need the owner's input.
- If your lane is calibrated and the rubric clears for all years, check the complete/frontier declaration criteria (calibration-complete.json note, keepers/ERCOT.json frontier_history, Q5 re-entry = a new explicit owner declaration on a CALIBRATED keeper). Settle the keeper config and clear the tasks that block declaration. If you reach complete/frontier, say so plainly in your final message, as a decision card, so the owner can approve. Give this same direction to any chained handoff.
- When you launch the next session, have it archive yours when safe, and give it these same directions, including launching a new handoff to continue the chain. If you are at the nesting limit (create_session refuses at lineage depth 8), make your last message a complete copy-paste handoff prompt to start another chain.

REPORT: lead with the ERCOT headline, then give:
- per-year before/after: C3a, C3b, C3c, C8 ST_GAS, C1 coal/CC/ST_GAS, South merchant gas TWh, LW price, slack, h > $1k;
- the prediction scorecard;
- what is committed/merged;
- the promotion outcome;
- the leftover refs for the owner to delete.
