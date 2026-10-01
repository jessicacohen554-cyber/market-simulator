SESSION R-ERCOT-20 — ERCOT: the 2024 C3a price deficit (−10.7 %) and the CC merit-compression object
DATA PROFILE: ercot
MODEL: Opus or Fable (writes core infrastructure — rule 27)
CLAUDE.md is binding — rules 1, 13, 14, 17, 18, 19, 21, 23, 24, 25, 28, 29(b), 31–36 especially.
- The parent never solves (rule 32(a)); every backcast year gets its own shard (rule 36); archive each shard once its bytes are in hand (rule 33).
- Promote only on the owner's say-so or the owner's standing instruction (rules 31/35). A promotion PR also re-keys frontend/data/forecast/program-status.json gate (a) for ERCOT only and passes scripts/check_promotion_completeness.py --iso ERCOT.
- You may launch and archive shards without asking.

HOUSEKEEPING FIRST
- Archive the parent session R-ERCOT-19 (session_014RbGr2xVQzYoC3QCdvLnn8) once get_session shows it idle.
- Check for unmerged ERCOT branches and PRs. Salvage anything needed, close stale PRs, and LIST the refs the owner must delete (sessions cannot delete refs, rule 33(f)).
- Known leftovers with no unique record: claude/r-ercot19-arm-{2024,2025}, claude/r-ercot19b-arm-{2019..2025, 2021r}, claude/r-ercot19c-arm-{2019..2025, 2022r}, plus the r-ercot17/18 arm refs if still present.

PRECONDITION: frontend/data/backcast/keepers/ERCOT.json on main names keeper 2026-09-30-r-19-eia-923 (bundle results/calibration/r_ercot19a_span, 2019–2025), ISO NOT-YET. If not, STOP and report.

READ FIRST
- docs/handoffs/r-ercot/RESULT-r-ercot-19-south-overrun-and-hub-refresh-2026-09-30.md
- docs/handoffs/r-ercot/PRECOMMIT-r-ercot-19-south-overrun-and-hub-refresh-2026-09-30.md (all of it — §1 is the merit-compression measurement; addenda A/B are the two rejected commit-profile arms)
- the ERCOT matrix shard docs/codebase-site/data/mechanism-matrix/ERCOT.js and docs/mechanism-testing-matrix.md §5.1 (rule 28(a))

STANDING STATE (r-19 keeper, P1)
- Train tier:
  - 2023 carve-out: C3a −19.8 % / C3b 0.289 (OWNER HOLD on k=33 — do not touch).
  - 2024: C3a −10.7 % FAIL (LW 27.84 vs 31.17 $/MWh). The only non-held train blocker.
  - 2025: CALIBRATED (C3a −9.8 %, 0.2 pp from the edge).
- Validation (never gates the ISO, rule 30(c)): 2019 C3a +23.9 %, C3b 0.538, C1 CC_REGULAR +9.70, COAL_PRB −9.48; 2020 C3b 0.229, C1 CC_REGULAR +12.39, COAL_PRB −11.60; 2021 and 2022 CALIBRATED (2022 C1 CC_REGULAR −7.69 vs ±8.00 — thin).
- Measured (R-ERCOT-19 §1): ISO-wide CC merit compression by heat rate. corr(measured HR, log model/923) 0.68–0.80 every year; HR > 9.0 CCs run 1.6–5.0× their EIA-923 energy, HR ≤ 7.0 run 0.80–1.01×. The ERCOT-139 committed block bids ~flat in HR (consistent with measured DAM conduct); the econ* tranches carry most of the over-run. The LP has no no-load/start coupling.

TASK 1 — DECOMPOSE THE 2024 C3a DEFICIT (zero LP, from the committed keeper hourlies)
- Where is the −$3.33/MWh LW gap? Split by hour class (trough / shoulder / peak / tight hours > $100), by month, and by zone. Report the share of the gap each carries.
- Tie it to the marginal unit: per hour, which class/tranche sets the P1 dual, vs the SCED marginal fuel where measurable.
- Hypotheses to test, not assume: (a) cheap over-committed inefficient CCs depress shoulder prices; (b) a tight-hour deficit (but the 2024 tight-hour lever is CLOSED at R-ERCOT-12 — only re-open with new evidence); (c) a fuel-basis level issue (the frozen GAS_OFFER_MARGIN_ANCHOR_BY_ZONE non-reproduction is routed, rule 23).
- PRECOMMIT before any solve. Any lever must be structural, measured and zero-DOF. Offer multipliers are FENCED (rule 1(c)).

TASK 2 — THE MERIT-COMPRESSION OBJECT (design, owner decision card before building)
- Both commit-profile sub-gates are adjudicated (R-ERCOT-19 arms B/C, default-off, not promoted: both flipped 2022 NOT-YET on C1 CC_REGULAR). Do NOT re-test them without new evidence.
- The open question: why do high-HR CCs' econ tranches clear so often? Measure the model econ-tranche mc vs the 60-Day DAM offer curve at the same MW point, per HR cohort, 2024–2025. If a measured, HR-dependent discrepancy exists on the econ segment specifically, that is a candidate design — card it.

RESIDUAL D-4 st_netload_drag rows (rubric-invisible): 3452 (2020/21/23), 3628 (2019/20), 3491 (2024/25). The month × hour profile limb missed (R-ERCOT-19 arm B, 8 → 8). A day-grain design would be new — card it; do not build blind.

OWNER DATA DECISION STAYS CLOSED: the 2019–22 SCED key. Do not touch coal offers. 2023 carve-out: OWNER HOLD on k=33. No re-declaring or sweeping offer multipliers (rule 1(c)).

ROUTE, DO NOT FIX
- Other lanes (rule 25 where cross-ISO): SPP-48 Oklaunion (SPP); the CAISO gate-(a) row and FR-22 (CAISO); the MISO solve-surface pin (MISO); Fusco in MISO's fleet.
- ERCOT data and seam items: the Decker Creek steam retirement seam; the Decker/Silas Ray CAMPD-backfill double count; the split-child bench display row; the COAL-SUB crosswalk coal-row drop; CAMPD TX 2018 off disk (keeps both prior-year sub-gates fail-closed in 2019); the R2 overlay/cap composition; the mislabelled 60d_DAM_Gen_Resource_Data_2020_Jul-Dec_Oct-Dec.parquet; the frozen GAS_OFFER_MARGIN_ANCHOR_BY_ZONE non-reproduction (rule 23); the South CHP bench-basis gap (six South CHP plants with no bench row); West Waha 2020/21 (not citable).
- Base-red fast-tier tests identical on main (MISO pin, d53/d60 pins, COAL WEFOR subtest, test_ff_readiness_battery, test_soundness, test_export, test_ccs_retrofit, test_gas_offer_zonal_anchor_vintage) — not ERCOT's.

DO-NOT-REDO (matrix R/I/G or landed)
- Offer and fuel-basis: the vintage anchor (both R); coal_offer_level_rebasis; measured_chp_heat_rates; the West/Panhandle split (CLOSED); the pooled South-Texas basis (R-ERCOT-17); the EIA-923 Finals zonal-gas refresh (R-ERCOT-19, landed).
- Commitment: cc_committed_prior_year_commitment_eligibility and netload_drag_prior_year_hour_profile (R-ERCOT-19 probes, not promoted).
- Window, scarcity, tight-hour: the window × partial family; the C3c scarcity-tail exhaustion record (ercot-95…231); the 2023 carve-out level (owner hold); the 2024 tight-hour lever (closed at R-ERCOT-12).
- Landed R-ERCOT-11…18 structural corrections (Parish split, Frontera, 2019 LR credit + RTOLCAP, Oklaunion membership/HR, swcap vintage, Sandy Creek key, curated coal HR, prior-year overnight drag index). Never revert any of these for fit (rule 14).

LESSONS FROM R-ERCOT-17/18/19
- The ERCOT zonal spread is recentred to a capacity-weighted mean of zero: moving one zone's row shifts every other gas unit the opposite way.
- 2024 C3a and 2022 C1 CC_REGULAR sit on edges; a CC-dispatch lever tends to trade one for the other. Predict both before solving.
- Keep the branch rebase-free (merge origin/main in). A mechanism-matrix.js merge conflict is almost always scenarios.py line anchors: take main's side hunk-by-hunk except hunks that differ in non-digit text, then check_mechanism_matrix.py --fix-anchors and --base origin/main.
- The D-4 conduct rider is binary; a small residual floor binding off-hours still convicts.
- Shard prompts: docs/handoffs/r-ercot/SHARD-PROMPTS-r-ercot-19C.md (keeper bundle → r_ercot19a_span). Partition signatures (swcap / ep_referenced / CC_REGULAR.peak / CT_PEAKER.peak): 2019–2022 true/true/151.008/433.95; 2023 true/FALSE/151.008/433.95; 2024–2025 false/true/4.576/13.15; plus netload_drag_prior_year_commitment_index=true everywhere; carry the input sha256 list (ercot_zonal_gas_hub.csv a6946073…ec26).
- If only 2024/2025 inputs move, re-solve only those years and recompose 2019–2023 from the keeper legs (R-ERCOT-19 arm A pattern) — the composer is scripts/probes/_r_ercot_compose_span.py.
- A fresh container needs `uv sync --frozen` before any python. Watch disk: seven full legs + a span is ~1.2 GB; delete owner-ruled legs.

DIRECTIONS FROM THE OWNER (carry forward verbatim in spirit)
- Check for any unmerged branches or PRs for your ISO and decide whether anything needs to be salvaged. If so, integrate it into your branch and close the open PRs, or say what can be deleted. Merge.
- When done, promote if it is a good candidate. If it is an improvement, PROMOTE (owner's standing instruction: "Is it an improvement? Then promote"). Create a PR and merge, archive the shards, and launch a handoff to continue calibrating this ISO if rubric failures remain.
- Present decisions for the owner as clickable decision cards (AskUserQuestion), NOT inline text. Only ask when you genuinely need the owner's input.
- If your lane is calibrated and the rubric clears for all years, check the complete/frontier declaration criteria (calibration-complete.json note, keepers/ERCOT.json frontier_history, Q5 re-entry = a new explicit owner declaration on a CALIBRATED keeper). Settle the keeper config and clear the tasks that block declaration. If you reach complete/frontier, say so plainly in your final message, as a decision card, so the owner can approve. Give this same direction to any chained handoff.
- When you launch the next session, have it archive yours when safe, and give it these same directions, including launching a new handoff to continue the chain. If you are at the nesting limit (create_session refuses at lineage depth 8), make your last message a complete copy-paste handoff prompt to start another chain.

REPORT: lead with the ERCOT headline, then give:
- per-year before/after: C3a, C3b, C3c, C8 ST_GAS, C1 coal/CC/ST_GAS, LW price, slack, h > $1k;
- the 2024 C3a decomposition table;
- the prediction scorecard;
- what is committed/merged;
- the promotion outcome;
- the leftover refs for the owner to delete.
