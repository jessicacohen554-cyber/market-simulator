SESSION R-ERCOT-24 — ERCOT: the ORDC curve-parameter vintage, and what remains open
DATA PROFILE: ercot
MODEL: Opus or Fable (writes core infrastructure — rule 27)

CLAUDE.md is binding. Pay particular attention to rules 1, 13, 14, 17, 18, 19, 21, 23, 24, 25, 28, 29(b), 30(c) and 31–36. Rule 30(c) was amended 2026-09-30: a held-out miss DOWNGRADES the ISO.
- The parent never solves (rule 32(a)).
- Every backcast year gets its own shard (rule 36).
- Archive each shard once its bytes are in hand (rule 33).
- Promote only on the owner's say-so or standing instruction (rules 31/35).
  - A promotion PR also re-keys `frontend/data/forecast/program-status.json` gate (a), for ERCOT only. KEEP the trailing `marker complete=False final=False …` phrase.
  - It must pass `scripts/check_promotion_completeness.py --iso ERCOT`.
- You may launch and archive shards without asking.

HOUSEKEEPING FIRST
- Archive the parent session R-ERCOT-23 (session_018ReW9F6fcamHfnwY6ejsNP) once get_session shows it idle.
- Check for unmerged ERCOT branches and PRs. Salvage anything needed, close stale PRs, and LIST the refs the owner must delete (sessions cannot delete refs, rule 33(f)).
- Known leftovers, none holding a unique record:
  - claude/r-ercot23-arm-2019
  - claude/r-ercot23-arm-2021
  - claude/r-ercot22-arm-2019
  - claude/r-ercot-22-handoff (merged)
  - claude/r-ercot-22-tail-slope (merged)
  - claude/r-ercot-23-ordc-2021 (once merged)

PRECONDITION: on main, `frontend/data/backcast/keepers/ERCOT.json` names keeper `2026-10-01-r-23-swcap-hourly` (bundle `results/calibration/r_ercot23_span`, 2019–2025), and the ISO reads NOT-YET. If not, STOP and report.

READ FIRST
- docs/records/ercot/r-ercot/RESULT-r-ercot-23-swcap-effective-hourly-2026-10-01.md (identification table §2, scorecard, cards §6)
- docs/records/ercot/r-ercot/PRECOMMIT-r-ercot-23-swcap-effective-hourly-2026-10-01.md
- scripts/probes/_r_ercot23_lcap_id.py, which writes docs/records/ercot/r-ercot/r_ercot23_phase0.json
- the ERCOT matrix shard docs/codebase-site/data/mechanism-matrix/ERCOT.js and docs/mechanism-testing-matrix.md §5.1 (rule 28(a))

STANDING STATE (r-23 keeper, P1)
- 2021: CALIBRATED (C3a +1.0 %).
- 2025: CALIBRATED (C3a −9.2 %).
- 2024: NOT-YET. C3a −11.1 % is its only failure: energy λ in the 192 hours above $100 — the closed compressed-distribution object (R-ERCOT-12/20/22). Do not re-open without new evidence.
- 2023 carve-out: NOT-YET (C3a −24.2 %, C3b 0.380). OWNER HOLD on k=33 — do not touch.
- 2022: NOT-YET (C1 CC_REGULAR −9.87 vs ±8.00). The coal-conduct mirror; coal offers FENCED; the 2019–22 SCED data decision stays CLOSED.
- 2019: NOT-YET (C3b 0.219; C1 CC_REGULAR +8.85, COAL_PRB −10.48). C3a +7.0 % PASS.
- 2020: NOT-YET (C3b 0.221; C1 CC_REGULAR +10.41, COAL_PRB −11.77).

TASK 1 — THE ORDC CURVE-PARAMETER VINTAGE (zero LP first; OWNER-GATED BEFORE ANY SOLVE)
- R-ERCOT-23 found two structural deviations from ERCOT's published ORDC, both zero-DOF:
  - (a) the OBD's 30-minute curve takes mean 0.5·(μ + Sσ); `results.scarcity.lolp` / `ercot_ordc_demand_steps` apply μ/2 + S·(σ/√2);
  - (b) the model uses a flat μ = 0, σ = 1,400 fallback where ERCOT publishes seasonal μ (shift included) and σ (2022 Biennial ORDC Report Fig. 3: ≈640/1,210 MW 2019, ≈900/1,210 2020–21, ≈880/1,280 2022).
- Diagnostic on measured inputs: with both, the formula reads 0.94 / 0.85 / 1.06 / 0.88× of measured RTORPA for 2019–2022, vs 1.04 / 1.43 / 1.14 / 1.08× today.
- To build: obtain exact published μ/σ (ERCOT posts them per season; the 2024 Biennial ORDC Report should cover 2022-09 → 2024; Figure digitization is ±15 MW and is a declared rule-14 reconciliation at best). If unreachable, say so and card it.
- It MOVES EVERY YEAR including the 2023 owner-hold year. Present the owner a decision card (AskUserQuestion) before solving: build for all years except 2023, all years incl. 2023, or hold.
- Predict per year by hour band before any solve; write the PRECOMMIT first.

TASK 2 — CARD, DO NOT BUILD
- The 2019/2020 C1 coal/CC mirror is fenced coal conduct. Raise it only with new admissible evidence.

ROUTE, DO NOT FIX
- Wharton CC over-run (marginal-HR estimator would be a derive — card only).
- Bench display rows omit 7512 / 55501 / 55545.
- Other ISOs' CC heat-rate artifacts and stale solve-surface pins (CAISO/MISO/NEISO/NYISO; rule 25).
- Pre-existing main failures (identical on clean main): test_d53_sector_gate_miso_arming, test_ccs_retrofit / test_d60_arming_batch Q42 pins, test_export, test_soundness end-to-end, test_fleet_arrays_golden ERCOT 2023.

DO-NOT-REDO
- Everything in R-ERCOT-20/21/22/23's lists.
- The 2021 LCAP window / protocol price cap (`ercot_swcap_effective_hourly`, matrix K). Never revert it for fit (rule 14).
- The 2024 tight-hour decomposition.

LESSONS FROM R-ERCOT-23
- **Measured RTOFFPA isolates RTORPA's full-hour term**; split the two terms before blaming a parameter. A uniform offset in BOTH terms is a (VOLL − λ) / reserve-basis change, not μ/σ.
- **Monthly decomposition finds regime changes** (2021 Uri reproduced; Mar–Dec 10× over).
- **The keeper's adder is the in-LP ORDC family dual (VOLL-anchored)**, not the post-solve published-anchor branch — a VOLL change belongs in the LP cost block (`ordc_penalty_hour_scale`).
- **Leg recovery:** reused legs are fetchable by SHA from `keepers/ERCOT.json` `*_extension.legs` even after their branches are deleted (`git fetch origin <sha>` then `git checkout <sha> -- <dir>`); verify their hourlies byte-match the keeper.
- **Mechanics** (as R-22): shard prompts `SHARD-PROMPTS-r-ercot-23.md` (`replay_keeper.py results/calibration/r_ercot23_span --years Y --set <flag>=true`); compose with `scripts/probes/_r_ercot_compose_span.py --side arm --chp-off`; `stamp_config_partition` with `--leg Y=run_config_Y.json` per year then `--check`; copy the keeper's calibration_attestation.json and prepend governance.attested_by; score the incumbent first; `dashboard_add_run.py --no-prune`; audit_keepers → prune --force-uncite → audit_keepers → check_promotion_completeness. A fresh container needs `uv sync --frozen`. Locally, the parity gate goes RED on your own gitignored leg dirs — expected (rule 31 note).

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
