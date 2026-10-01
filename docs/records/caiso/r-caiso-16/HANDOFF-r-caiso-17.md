SESSION R-CAISO-17 — CAISO: pre-2022 EIA-930 CISO clock scan (NG / TI / Demand vs OASIS TAC, 2019–2022)
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-16 (session_01DjpeWfYodDqoSuiD5PWaX6) with mcp__Claude_Code_Remote__archive_session.
  - Do this only once PR #6907 (promotion) and this handoff's PR read MERGED on the GitHub MCP.
  - If either is not merged, do not archive, and say so in your first report.
- Check for unmerged CAISO branches and open CAISO PRs:
  - salvage anything not on main into your branch;
  - close the open PRs you salvaged;
  - report which branches the owner can delete. Deleting a ref returns 403, so do not try.
  - Known leftovers:
    - the R-CAISO-15 legs `claude/r-caiso-15-A-2019` … `-2025`, plus `claude/r-caiso-15-clock-repair-hsl` and `claude/r-caiso-15-handoff`;
    - the R-CAISO-16 legs `claude/r-caiso-16-A-2019` … `-2025`, plus `claude/r-caiso-16-interchange-lag`, `claude/r-caiso-16-promote` and `claude/r-caiso-16-handoff`.
  - None of these carries anything that is not on main (the per-year legs are transport only, rule 33(f)).
- Work on a fresh branch off origin/main.

STATE (2026-09-30):
- Keeper `2026-09-30-caiso-r16-tiontime` (bundle rcaiso16_A_span, 2022–25) is CALIBRATED: a single ledgered C3c 2024.
  - C4 gas NRMSE 0.262 / 0.247 / 0.247 / 0.288.
- Fold `-touchpoints` (2019–21, bundle rcaiso16_A_tp_2019_2021) is NOT-YET on fuelmix, price_mean and dispatch_corr.
  It is reported only (rule 30(c)).
- `caiso_eia930_clock_repair` is armed. It re-stamps CISO NG cells + Net generation over UTC 2023-11-01 08:00 .. 2025-12-02 22:00,
  and Demand over 2022-06-16 08:00 .. 2025-12-02 22:00.
  - Total interchange is NOT re-stamped: R-CAISO-16 measured it on the true clock.
- Owner card 2026-09-30: next link = "Pre-2022 clock scan".

THE LEAD (docs/handoffs/r-caiso-16/PRECOMMIT-r-caiso-16-2026-09-30.md §7; phase0-ti-vs-tac.csv):
- Probe `scripts/probes/_rcaiso16_ti_vs_tac.py` regresses d(OASIS TAC) on d(NG shifted j) + d(−TI shifted k).
- For 2019–2021 (outside every registered window) it prefers either (NG −1 h, TI 0) or (NG 0, TI +1) over (0,0).
  - 2021: R² 0.826 / 0.803 vs 0.736.
  - 2019: 0.688 / 0.618 vs 0.643.
  - 2020: 0.676 / 0.651 vs 0.599.
- This is weaker than the 2023–25 evidence (R² ≤ 0.83), and 2022 prefers (0,0) at 0.844.
- Three hypotheses are open:
  - (i) a real EIA-930 publisher clock window in 2019–21;
  - (ii) an OASIS TAC-file clock artifact in those years (the `CAISO_tac_load_hourly_{2019..2021}.csv` files may have been fetched
    differently from 2023+);
  - (iii) regression noise from missing data (the NG: WAT gap 2019-10..2020-08, repaired by `caiso_hydro_backfill`).

TASK (do nothing else):
1. Phase 0, zero LP.
   - Re-scan each column family's clock for 2019–2022 at monthly and daily resolution: NG (and NG: SUN via solar geometry, as
     R-CAISO-13 did), TI and Demand.
   - Use at least two references independent of each other:
     - OASIS TAC. First verify the TAC files' own clock: e.g. the TAC DST-transition hours, and TAC vs the EIA-930 Demand cell,
       which R-CAISO-13 found at lag 0 through 2022-06-13.
     - Solar geometry: the NG: SUN production centroid by month (solar noon ≈ 12.0 h PST at the fleet longitude).
     - The counterparty legs (BPAT / PACW / NEVP interchange files) where they cover the years.
   - Decide from the measurement which holds:
     - (a) no publisher window before 2022-06 (build nothing); or
     - (b) a window exists.
   - Record the table in a PRECOMMIT before anything is built.
2. If (b):
   - Register the window in `EIA930_CISO_CLOCK_LATE_WINDOWS_UTC` (or an EARLY-window sibling if the stamps are early), under the
     SAME flag (rule 19), zero parameters, frozen parquet untouched (rule 23).
   - Make sure every armed seam honours it: frame, caiso-80 demand term, HSL generation term, battery envelope, zero-LP benchmark
     rebuild.
   - Tests: off path byte-identical; armed path moves only the window.
   - Update the shard hard-stop counts.
3. If (a):
   - Build nothing.
   - Record the finding.
   - Put the next-link choice to the owner as a decision card.
4. If anything was built: solve 7 shards, one per year 2019–2025 (rule 36).
   - Use docs/handoffs/r-caiso-16/shard-prompt.md as the template; `{SRC}` = rcaiso16_A_tp_2019_2021 (2019–21) /
     rcaiso16_A_span (2022–25).
   - Pin the full SHA after your build PR merges.
   - The parent never solves (rule 32(a)).
5. PARENT SEAM, as R-CAISO-16:
   - compose with scripts/probes/rcaiso_compose_span.py and the five --require flags:
     caiso_eia930_clock_repair=true, caiso_tac_shares_standard_time=true, caiso_ra_bridge_startup_aware=false,
     cc_eia923_identity_emission_basis=true, caiso_supply_consistent_demand=true;
   - `legitimacy_diagnostics.py --bundle … --iso CAISO --json-out …`;
   - `dashboard_add_run --no-prune`;
   - a copy of scripts/gen_rcaiso16_attestation.py;
   - register again;
   - stamp the fold.
   - PRUNE WITH `prune_iso_runs.py --iso CAISO --force-uncite --keep <new fold id>`. Without `--keep` it deletes the fold you
     just stamped (R-CAISO-16 RESULT, process note).
6. Decision rule, pre-registered in your PRECOMMIT:
   - Promote on structure (rule 14) if 2022–25 stays CALIBRATED and the window repair is complete.
   - Report the fold's movement: this link exists for the fold, which can never downgrade the ISO (rule 30(c)).
   - Otherwise the trade goes to the owner as a decision card.

OWNER RULINGS IN FORCE (do not re-ask):
- SD floor static 1,436; LA Basin: "SD only".
- EIA930_GAS_FOLD_REFUTED: keep as is.
- startup_aware disarmed.
- tac_shares_standard_time armed.
- PS wall kept.
- The caiso-80 demand basis stands.
- Clock repair complete on frame / demand / HSL / battery envelope ("Promote", 2026-09-29).
- TI kept on its true clock ("Narrow the repair", 2026-09-30).
- Next link: "Pre-2022 clock scan" (2026-09-30).

NOTES:
- A fresh container needs `pip install -e . pytest tzdata`.
- Run `ruff format` in a separate command before any push.
- The keeper tracks the solve-year EIA-860 vintage. Any reader-side re-derivation that loads the fleet must pin the vintage its
  committed derivation used and restore the solve's own (R-CAISO-15 ADDENDUM §8).
- The model clock is the extract's row POSITION grid, which is local STANDARD time (UTC−8) start-of-hour. It is NOT the wall
  clock in PDT; R-CAISO-16's first scan went wrong on exactly this.
- check_registry_payload_parity flags local gitignored legs. That is expected (rule 31) and absent in CI.
- Never `git grep` in a partial clone; use rg.

HARD RULES: CLAUDE.md is binding, especially rules 1, 13, 14, 19, 21, 23–25, 27, 28, 29(b)/(c), and 30–36.
- Owner decisions go to the owner as clickable decision cards (AskUserQuestion), never inline text.

END OF SESSION:
- Promote if the candidate is good. Create a PR and merge it (rebase-and-merge).
- Archive every shard, and report leftover shard branches for the owner to delete.
- If CAISO still has rubric failures, put the next-link choice to the owner as a decision card. Then launch R-CAISO-18
  with these same directions: archive its parent when safe, salvage/close CAISO branches and PRs, present decisions as
  cards, promote if good, PR + merge, archive shards, and launch the next link.
- If at the nesting limit, make the final message a complete handoff prompt in one code block.
