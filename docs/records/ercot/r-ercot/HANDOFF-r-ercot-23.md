SESSION R-ERCOT-23 — ERCOT: the 2020/2021 ORDC adder over-statement, and what remains open
DATA PROFILE: ercot
MODEL: Opus or Fable (writes core infrastructure — rule 27)

CLAUDE.md is binding. Pay particular attention to rules 1, 13, 14, 17, 18, 19, 21, 23, 24, 25, 28, 29(b), 30(c) and 31–36. Rule 30(c) was amended 2026-09-30: a held-out miss now DOWNGRADES the ISO.
- The parent never solves (rule 32(a)).
- Every backcast year gets its own shard (rule 36).
- Archive each shard once its bytes are in hand (rule 33).
- Promote only on the owner's say-so or standing instruction (rules 31/35).
  - A promotion PR also re-keys `frontend/data/forecast/program-status.json` gate (a), for ERCOT only. KEEP the trailing `marker complete=False final=False …` phrase.
  - It must pass `scripts/check_promotion_completeness.py --iso ERCOT`.
- You may launch and archive shards without asking.

HOUSEKEEPING FIRST
- Archive the parent session R-ERCOT-22 (session_01RUionJjup177UZPunyePCq) once get_session shows it idle.
- Check for unmerged ERCOT branches and PRs. Salvage anything needed, close stale PRs, and LIST the refs the owner must delete (sessions cannot delete refs, rule 33(f)).
- Known leftovers, none holding a unique record:
  - claude/r-ercot22-arm-2019
  - claude/r-ercot21-arm-{2019..2025}
  - claude/r-ercot20-arm-{2019..2025}
  - claude/r-ercot-21-cc2022
  - claude/r-ercot-22-tail-slope (merged)
  - claude/r-ercot-22-handoff (once merged)

PRECONDITION: on main, `frontend/data/backcast/keepers/ERCOT.json` names keeper `2026-10-01-r-22-ordc-shift` (bundle `results/calibration/r_ercot22_span`, 2019–2025), and the ISO reads NOT-YET. If not, STOP and report.

READ FIRST
- docs/handoffs/r-ercot/RESULT-r-ercot-22-ordc-shift-vintage-2026-10-01.md (tail decomposition, RTORPA identification table, scorecard)
- docs/handoffs/r-ercot/PRECOMMIT-r-ercot-22-ordc-shift-vintage-2026-10-01.md
- scripts/probes/_r_ercot22_ordc_shift_id.py, which writes docs/handoffs/r-ercot/r_ercot22_phase0.json
- the ERCOT matrix shard docs/codebase-site/data/mechanism-matrix/ERCOT.js and docs/mechanism-testing-matrix.md §5.1 (rule 28(a))

STANDING STATE (r-22 keeper, P1)
- 2021: CALIBRATED.
- 2025: CALIBRATED (C3a −9.2 %).
- 2024: NOT-YET. C3a −11.1 % is its only failure. It is entirely energy λ in ERCOT's 192 hours above $100, i.e. the closed compressed-distribution object (R-ERCOT-12/20/22). Do not re-open it without new evidence.
- 2023 carve-out: NOT-YET (C3a −24.2 %, C3b 0.380). OWNER HOLD on k=33 — do not touch.
- 2022: NOT-YET (C1 CC_REGULAR −9.87 vs ±8.00). This is the coal-conduct mirror. Coal offers are FENCED, and the 2019–22 SCED data decision stays CLOSED.
- 2019: NOT-YET (C3b 0.231; C1 CC_REGULAR +8.85, COAL_PRB −10.48). C3a is now +7.5 %, a PASS.
- 2020: NOT-YET (C3b 0.221; C1 CC_REGULAR +10.41, COAL_PRB −11.77).

TASK 1 — THE 2020/2021 ORDC ADDER (zero LP first)
- With the PUCT 48551 shift in force, the published RTORPA formula on ERCOT's measured RTOLCAP/RTOFFCAP/λ still reads 1.45× (2020) and 1.59× (2021) of measured RTORPA. 2022–2024 read 1.08 / 1.09 / 0.89×. See r_ercot22_phase0.json `rtorpa_identification`.
- Identify the cause the same way R-ERCOT-22 did: published inputs only, reproduced against measured RTORPA, and never fitted to RTORPA.
- Candidates:
  - ERCOT's per-year NP6-576 μ/σ tables. These are not on disk. The committed `data/raw/_validation-source/ercot_ordc_lolp_params.csv` is undated and overstates by 2–4× in every year, so do not use it.
  - The 2020/2021 RTOFFCAP definition or basis.
  - Any other published ORDC order change in 2020–2021 (check the PUCT/ERCOT record).
- If the cause is a data intake, follow the data-intake skill and the network policy. If the source is unreachable, say so plainly and card it.
- The model's 2020 adder gap is small on LW (+0.5 $/MWh over the tight hours). 2021's is +22.5 (the Uri hours). Predict by hour band before any solve.
- Any lever must be structural, measured and zero-DOF. Offer multipliers stay FENCED (rule 1(c)). Write the PRECOMMIT before any solve.

TASK 2 — CARD, DO NOT BUILD
- The 2019/2020 C1 coal/CC mirror is fenced coal conduct. Raise it to the owner only if you find new admissible evidence.

ROUTE, DO NOT FIX
- Wharton CC over-run (marginal-HR estimator would be a derive — card only).
- Bench display rows omit 7512 / 55501 / 55545.
- Other ISOs' CC heat-rate artifacts and stale solve-surface pins (rule 25 — their lanes).
- The pre-existing main failure `tests/unit/config/test_d53_sector_gate_miso_arming.py`.
- Everything already routed by R-ERCOT-20/21/22.

DO-NOT-REDO (matrix R/I/G, or landed)
- Everything in R-ERCOT-20/21/22's lists.
- The 2024 tight-hour decomposition. R-ERCOT-22 showed the ORDC families are byte-flat and the miss is energy λ.
- The ORDC shift vintage. It has landed; never revert it for fit (rule 14).

LESSONS FROM R-ERCOT-22
- **Read the reserve-family sidecars before blaming the ORDC.** Under the measured RTOLCAP cap the reserve level is exogenous, so fleet changes move the energy dual.
- **Identify published parameters by recomputing the published formula on ERCOT's own measured inputs** (system λ, RTOLCAP, RTOFFCAP, RTORPA in data/raw/ercot/ercot_<Y>_ordc_reserves_hourly.parquet).
- **Run G-DRIFT before launching shards.** When it is all INERT and the change touches only some years, re-solve only those years and recompose the rest from the keeper's legs.
- **Year-driven fields must be listed in `stamp_config_partition.YEAR_DRIVEN_FIELDS`.**
- **Mechanics:**
  - Shard prompts: docs/handoffs/r-ercot/SHARD-PROMPTS-r-ercot-22.md.
  - Compose with scripts/probes/_r_ercot_compose_span.py --side arm --chp-off.
  - Run stamp_config_partition with --leg Y=run_config_Y.json for each year.
  - Copy the keeper's calibration_attestation.json and prepend to governance.attested_by.
  - Score the incumbent BEFORE registering.
  - Register with dashboard_add_run.py --no-prune.
  - A fresh container needs `uv sync --frozen`.

DIRECTIONS FROM THE OWNER (carry forward verbatim in spirit)
- **Branches and PRs.** Check for any unmerged branches or PRs for your ISO and decide whether anything needs to be salvaged. If so, integrate it into your branch and close the open PRs, or say what can be deleted. Merge.
- **Promotion.** When done, promote if it is a good candidate. If it is an improvement, PROMOTE (owner's standing instruction: "Is it an improvement? Then promote"). Create a PR and merge, archive the shards, and launch a handoff to continue calibrating this ISO if rubric failures remain.
- **Decision cards.** Present decisions for the owner as clickable decision cards (AskUserQuestion), NOT inline text. Only ask when you genuinely need the owner's input.
- **Complete/frontier.** If your lane is calibrated and the rubric clears for all years, check the complete/frontier declaration criteria: the calibration-complete.json note, keepers/ERCOT.json frontier_history, and Q5 re-entry (a new explicit owner declaration on a CALIBRATED keeper). Settle the keeper config and clear the tasks that block declaration. If you reach complete/frontier, say so plainly in your final message, as a decision card, so the owner can approve. Give this same direction to any chained handoff.
- **Chaining.** When you launch the next session, have it archive yours when safe, and give it these same directions, including launching a new handoff to continue the chain. If you are at the nesting limit (create_session refuses at lineage depth 8), make your last message a complete copy-paste handoff prompt to start another chain.

REPORT
- Lead with the ERCOT headline.
- Then give:
  - the per-year before/after (C3a, C3b, C3c, C8 ST_GAS, C1 coal/CC/ST_GAS, LW price, slack, h > $1k)
  - the identification table
  - the prediction scorecard
  - what is committed and merged
  - the promotion outcome
  - the leftover refs for the owner to delete
