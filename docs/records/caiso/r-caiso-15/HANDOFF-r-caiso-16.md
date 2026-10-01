SESSION R-CAISO-16 — CAISO: per-DIBA interchange-feed clock under `caiso_eia930_clock_repair` (the repair's last live gap)
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-15 (session_01V3pPLe5DdhU7ViyjsdUXXr) with mcp__Claude_Code_Remote__archive_session.
  - Do this once PR #6898 (promotion) and this handoff's PR read MERGED on the GitHub MCP.
  - If either is not merged, do not archive, and say so in your first report.
- Check for unmerged CAISO branches and open CAISO PRs:
  - salvage anything not on main into your branch;
  - close the open PRs you salvaged;
  - report which branches the owner can delete. Deleting a ref returns 403, so do not try.
  - Known leftovers: claude/r-caiso-15-A-2019 … -2025, claude/r-caiso-15-clock-repair-hsl, claude/r-caiso-15-handoff,
    claude/caiso-eia930-clock-repair-8xy6ie.
- Work on a fresh branch off origin/main.

STATE (2026-09-30):
- Keeper `2026-09-29-caiso-r15-clockfull` (bundle rcaiso15_A_span, 2022–25) is CALIBRATED: a single ledgered C3c 2024.
  - C4 gas NRMSE 0.262 / 0.248 / 0.249 / 0.290.
  - Fold `-touchpoints` (2019–21) is NOT-YET and reported only (rule 30(c)).
- `caiso_eia930_clock_repair` is armed. It re-stamps EIA-930 CISO's one-hour-late windows (generation 2023-11-01..2025-12-02)
  at five seams:
  - the frame seam;
  - the caiso-80 demand;
  - the HSL solar/wind generation term;
  - the battery shape envelope;
  - the zero-LP benchmark rebuild.
- Owner card 2026-09-30: next link = "Interchange lag".

THE GAP (docs/handoffs/r-caiso-15/ADDENDUM-r-caiso-15-hsl-2026-09-29.md §4, census row #2):
- `data/raw/eia-930-interchange/CISO interchange hourly.parquet` (the per-DIBA feed) does NOT pass the frame repair seam.
- Its clock comes from fixed lags: `_CAISO_INTERCHANGE_LAG_STD_H=1` / `_DST_H=2` (`data/eia930/envelopes.py:886-910`).
  - Those lags were fitted against the UNREPAIRED extract's `Total interchange` over 2023–25
    (`scripts/validate_caiso_seam_hod_frame.py:47-69`).
  - That column was one hour late for most of that span.
- Readers:
  - `measured_corridor_flow_envelope` (flag `caiso_corridor_flow_limit`);
  - `measured_firm_import_shape` (`caiso_firm_import_shape` / envelope clip).
- Downstream constants (census row #3): the DSW overnight / daytime / late-evening clean-depth, surplus, wedge and
  import-tranche constants (`model/interchange/spec.py`). They read the feed through `_caiso_interchange_model_clock`.

TASK (do nothing else):
1. Phase 0, zero LP.
   - Re-scan the per-DIBA feed's lag, per regime (STD / DST) and per window (in vs out of the generation window), against
     two references:
     - the REPAIRED extract `Total interchange` (arm on);
     - an independent clock: OASIS intertie schedules / DAM flows, if available.
   - Decide from the measurement which is true:
     - (a) the feed's own clock is right and only the reference moved; or
     - (b) the feed shares CISO's late window.
   - Record the table in a PRECOMMIT before anything is built.
2. If (b):
   - Extend the repair to the feed at its reader, under the SAME flag (rule 19), zero parameters, frozen parquet untouched
     (rule 23). Add tests: off path byte-identical, armed path moves only the window.
   - List every row-#3 constant whose hour window depends on the feed. Re-derive only those whose value moves, and only
     with the source-data change cited (rule 23). State the magnitudes.
3. If (a):
   - Build nothing.
   - Record the finding and set the census row to closed.
   - Put the next-link choice to the owner as a card.
4. If anything was built: solve 7 shards, one per year 2019–2025 (rule 36).
   - Use docs/handoffs/r-caiso-15/shard-prompt.md as the template.
   - Update the arm-liveness hard stop with the feed counts.
   - Pin the full SHA after your build PR merges.
   - The parent never solves (rule 32(a)).
5. PARENT SEAM, as R-CAISO-15:
   - compose with scripts/probes/rcaiso_compose_span.py and the five --require flags;
   - legitimacy diagnostics;
   - dashboard_add_run --no-prune;
   - a copy of scripts/gen_rcaiso15_attestation.py;
   - register again;
   - stamp the fold.
   The benchmark rebuild now arms the repair from the bundle, so there is no manual step.
6. Decision rule, pre-registered in your PRECOMMIT:
   - Promote on structure (rule 14) if 2022–25 stays CALIBRATED and the feed repair is complete.
   - Otherwise the trade goes to the owner as a decision card.

OWNER RULINGS IN FORCE (do not re-ask):
- SD floor static 1,436; LA Basin: "SD only".
- EIA930_GAS_FOLD_REFUTED: keep as is.
- startup_aware disarmed.
- tac_shares_standard_time armed.
- PS wall kept.
- The caiso-80 demand basis stands.
- Clock repair complete on frame / demand / HSL / battery envelope ("Promote", 2026-09-29).
- Next link: "Interchange lag" (2026-09-30).

NOTES:
- A fresh container needs `pip install -e . pytest tzdata`.
- Run `ruff format` in a separate command before any push.
- The keeper tracks the solve-year EIA-860 vintage (`eia860_vintage_tracks_solve_year=true`). Any reader-side
  re-derivation that loads the fleet must pin the vintage its committed derivation used and restore the solve's own.
  R-CAISO-15's first shard launch crashed on exactly this (ADDENDUM §8).
- If a leg predates a newly added ScenarioConfig field, compose with `--absent-default KEY=false`, and only for a key
  G-DRIFT shows INERT.
- check_registry_payload_parity flags local gitignored legs. That is expected (rule 31) and absent in CI.
- Never `git grep` in a partial clone; use rg.

HARD RULES: CLAUDE.md is binding, especially rules 1, 13, 14, 19, 21, 23–25, 27, 28, 29(b)/(c), and 30–36.
- Owner decisions go to the owner as clickable decision cards (AskUserQuestion), never inline text.

END OF SESSION:
- Promote if the candidate is good. Create a PR and merge it (rebase-and-merge).
- Archive every shard, and report leftover shard branches for the owner to delete.
- If CAISO still has rubric failures, put the next-link choice to the owner as a decision card. Then launch R-CAISO-17
  with these same directions: archive its parent when safe, salvage/close CAISO branches and PRs, present decisions as
  cards, promote if good, PR + merge, archive shards, and launch the next link.
- If at the nesting limit, make the final message a complete handoff prompt in one code block.
