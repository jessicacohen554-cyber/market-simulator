SESSION R-ERCOT-19 — ERCOT: the South merchant over-run (on the EIA-923 basis) and the 2019/2020 residual lane
DATA PROFILE: ercot
MODEL: Opus or Fable (writes core infrastructure — rule 27)
CLAUDE.md is binding — rules 1, 13, 14, 17, 18, 19, 21, 23, 24, 25, 28, 29(b), 31–36 especially.
- The parent never solves (rule 32(a)); every backcast year gets its own shard (rule 36); archive each shard once its bytes are in hand (rule 33).
- Promote only on the owner's say-so or the owner's standing instruction (rules 31/35). A promotion PR also re-keys frontend/data/forecast/program-status.json gate (a) for ERCOT only and passes scripts/check_promotion_completeness.py --iso ERCOT.
- You may launch and archive shards without asking.

HOUSEKEEPING FIRST
- Archive the parent session R-ERCOT-18 (session_01EExfAKWt3k3GUqGQUkzwAA) once get_session shows it idle. Its PR is #6906.
- Check for unmerged ERCOT branches and PRs. Salvage anything needed, close stale PRs, and LIST the refs the owner must delete (sessions cannot delete refs, rule 33(f)).
- Known leftovers with no unique record:
  - claude/r-ercot18-arm-2019 … claude/r-ercot18-arm-2025
  - claude/r-ercot17-arm-2019 … claude/r-ercot17-arm-2025
  - claude/r-ercot-17-south-pool
  - claude/r-ercot-18-drag-index (if the merge did not remove it)

PRECONDITION: frontend/data/backcast/keepers/ERCOT.json on main names keeper 2026-09-30-r-18-drag-index (bundle results/calibration/r_ercot18_span, 2019–2025), ISO NOT-YET. If not, STOP and report.

READ FIRST
- docs/records/ercot/r-ercot/RESULT-r-ercot-18-drag-overnight-index-2026-09-30.md (all of it, incl. the Task 2 characterization)
- docs/records/ercot/r-ercot/PRECOMMIT-r-ercot-18-drag-overnight-index-2026-09-30.md
- docs/records/ercot/RESULT-r-ercot-17-south-texas-pool-2026-09-29.md
- the ERCOT matrix shard docs/codebase-site/data/mechanism-matrix/ERCOT.js and docs/mechanism-testing-matrix.md §5.1 (rule 28(a))

STANDING STATE (r-18 keeper, P1)
- Train tier:
  - 2023 carve-out: C3a −19.8 % / C3b 0.289 (OWNER HOLD on k=33 — do not touch).
  - 2024: C3a −10.7 % FAIL.
  - 2025: CALIBRATED (C3a −9.6 %).
- Validation:
  - 2019: C3a +23.9 %, C3b 0.538, C1 CC_REGULAR +9.70, COAL_PRB −9.48.
  - 2020: C3b 0.229, C1 CC_REGULAR +12.39, COAL_PRB −11.61.
  - 2021 and 2022: CALIBRATED.
- South merchant gas (P1, zone South, CC_REGULAR + CT_PEAKER + ST_GAS) over-runs 1.13–1.24× in 2019 and 2022–2025.

TASK 1 — SOUTH MERCHANT OVER-RUN (phase 0 first, zero LP; PRECOMMIT before any solve)
- R-ERCOT-18's zero-LP read (2019/2022/2024, per-plant model dispatch vs CAMPD) found:
  - The over-run is commitment frequency: South CCs online 63–97 % of hours in the model vs 20–67 % metered, with MW-when-on at or below the meter's.
  - It is uniform by hour of day and is not floor-driven.
  - The efficient 55123 under-runs.
- CAVEAT that voids part of that read: 3559 Silas Ray, 3631 Sam Rayburn and 55086 Gregory carry the benchmark's CT-only CEMS flag (EIA-923 net > 1.1× CAMPD gross). Redo the per-plant comparison on the EIA-923 monthly basis the benchmark itself uses before concluding anything.
- Then characterize the within-South merit order: which tranche of each small CC clears, and why (heat rate, tranche structure, basis). Offer multipliers are FENCED (no re-declaring or sweeping, rule 1(c)). A lever, if one is identified, must be structural and measured.
- The 2024/2025 South/South_Central/North member rows of ercot_zonal_gas_hub.csv are on earlier EIA-923 vintages than the published Finals. This is a rule-23 data update (the source changed). It may be done as its own solve round if phase 0 shows it matters.

TASK 2 — 2019/2020 residual lane (validation tier, never gates the ISO, rule 30(c))
- The objects are listed under STANDING STATE.
- The coal stay-on object stays FENCED: coal offers untouched; coal_offer_level_rebasis R; 2019–22 SCED key declined.
- West Waha 2020/2021: the annual basis is NOT citable. Build it from EIA NGWU weekly prints only if every row the mechanism reads is citable.
- The South CHP shortfall is a separate object. Characterize it; do not fix it blind.

RESIDUAL D-4 st_netload_drag rows (rubric-invisible; all years are below the 30 % cap)
- 3452 in 2020/2021/2023 and 3628 in 2019/2020: small floors that still bind in off hours.
- 3491 Handley in 2024/2025.
- Any structural fix needs the floor to be hour-eligible by the plant's own diurnal commitment. That is a new design, so put it to the owner as a decision card before building. Do not re-open the prior-year index (K) or merit allocation (not promoted) without new evidence.

OWNER DATA DECISION STAYS CLOSED: the 2019–22 SCED key. Do not touch coal offers. 2023 carve-out: OWNER HOLD on k=33. No re-declaring or sweeping offer multipliers (rule 1(c)).

ROUTE, DO NOT FIX
- Other lanes (rule 25 where cross-ISO): SPP-48 Oklaunion (SPP lane); the CAISO gate-(a) row and FR-22 (CAISO lane — check_forecast_parity is red on main for caiso_tac_shares_standard_time); the MISO solve-surface pin (MISO lane); Fusco in MISO's fleet.
- ERCOT data and seam items:
  - the Decker Creek steam retirement seam;
  - the Decker/Silas Ray CAMPD-backfill double count;
  - the split-child bench display row;
  - the COAL-SUB crosswalk coal-row drop;
  - CAMPD TX 2018 off disk (it also keeps the prior-year index fail-closed in 2019);
  - the R2 overlay/cap composition;
  - the mislabelled 60d_DAM_Gen_Resource_Data_2020_Jul-Dec_Oct-Dec.parquet;
  - the frozen GAS_OFFER_MARGIN_ANCHOR_BY_ZONE non-reproduction (rule 23).
- Base-red tests: base-red fast-tier tests (MISO pin, d53/d60 pins, COAL WEFOR subtest, test_ff_readiness_battery, test_soundness, test_export, test_ccs_retrofit, test_gas_offer_zonal_anchor_vintage — identical failure set on main, not ERCOT's).

DO-NOT-REDO (matrix R/I/G or landed)
- Offer and fuel-basis constructions: the vintage anchor (both cells R); coal_offer_level_rebasis; measured_chp_heat_rates; the West/Panhandle split (CLOSED); the pooled South-Texas basis (R-ERCOT-17).
- Window, scarcity and tight-hour work: the window × partial family; the C3c scarcity-tail exhaustion record (ercot-95…231); the 2023 carve-out level (owner hold); the 2024 tight-hour lever (closed at R-ERCOT-12).
- Landed R-ERCOT-11…16 structural corrections: the Parish split, Frontera membership, 2019 LR credit + RTOLCAP cap, Oklaunion membership, ercot_swcap_vintage, the Sandy Creek commission-year key, the curated-sheet coal-HR population, the Oklaunion measured heat rate.
- The prior-year overnight drag index (R-ERCOT-18, K).
- Never revert any of these for fit (rule 14).

LESSONS FROM R-ERCOT-17/18
- The ERCOT zonal spread is recentred to a capacity-weighted mean of zero. Moving one zone's row shifts every other gas unit by the opposite constant.
- Keep the branch rebase-free: merge origin/main into your branch, never rebase it, so the shards' pinned SHA stays in history. A matrix-anchor merge conflict resolves by taking main's mechanism-matrix.js, re-inserting your text, and re-running check_mechanism_matrix.py --fix-anchors.
- The D-4 conduct rider is binary (the median of the meter over the plant's own binding hours). A small residual floor that binds in off hours still convicts. Predict with that in mind.
- Concentrating a mandate onto efficient plants can RAISE realized forced share even when the nominal mandate is preserved.
- Shard prompt template: docs/records/ercot/r-ercot/SHARD-PROMPTS-r-ercot-18.md (keeper bundle r_ercot17_span → use r_ercot18_span).
  - Partition signatures per year (swcap / ep_referenced / CC_REGULAR.peak / CT_PEAKER.peak):

    | Years | swcap | ep_referenced | CC_REGULAR.peak | CT_PEAKER.peak |
    |---|---|---|---|---|
    | 2019–2022 | true | true | 151.008 | 433.95 |
    | 2023 | true | FALSE | 151.008 | 433.95 |
    | 2024–2025 | false | true | 4.576 | 13.15 |

  - Add netload_drag_prior_year_commitment_index = true to every signature, and carry the input sha256 list.
- A fresh container needs `uv sync --frozen` before any python. Disk is ample.

DIRECTIONS FROM THE OWNER (carry forward verbatim in spirit)
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
