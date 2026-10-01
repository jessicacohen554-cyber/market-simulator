SESSION R-CAISO-15 — CAISO: complete `caiso_eia930_clock_repair` (HSL generation term), solve, promote if good
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST:
- Archive R-CAISO-14 (session_01RiESkX4rPKmgM1CAqyVBF7) with mcp__Claude_Code_Remote__archive_session. Do this once its
  PR (branch claude/caiso-eia930-clock-repair-8xy6ie) reads MERGED on the GitHub MCP. If it is not merged, do not
  archive; say so in your first report.
- Check for unmerged CAISO branches and open CAISO PRs:
  - salvage anything not on main into your branch;
  - close the open PRs you salvaged;
  - report which branches the owner can delete. Deleting a ref returns 403, so do not try.
  - Leftover refs from R-CAISO-14: claude/r-caiso-13-A-2019 … -2025 (shard legs of the superseded run).
- Work on a fresh branch off origin/main.

STATE (2026-09-29):
- Keeper `2026-09-28-caiso-r11-tacpst` (bundle rcaiso11_A_span, 2022–25) is CALIBRATED: a single ledgered C3c 2024,
  and C4 2025 gas NRMSE 0.294 against ≤ 0.30.
- The fold `-touchpoints` (2019–21) is NOT-YET and reported only (rule 30(c)).
- R-CAISO-14 solved `caiso_eia930_clock_repair=true`. The span stayed CALIBRATED, but the repair is INCOMPLETE.
  - It moves Demand and the caiso-80 SC demand 1 h earlier.
  - Solar and wind come from `data/raw/caiso-hsl/caiso_{Y}_hsl_hourly.parquet`, which `scripts/data/build_caiso_hsl.py`
    builds offline as EIA-930 delivered + CAISO 5-min curtailment. `renewables._hsl_file` reads it, and the arm never
    reaches it. Its `solar_gen_mw` centroid is 12.5–13.0 h PST from Nov 2023 to Nov 2025.
  - So demand and solar are now 1 h apart. P1–P3 FAIL, P4 PASS; C4 gas NRMSE 2024 0.254 → 0.262 and
    2025 0.294 → 0.300.
- Owner card 2026-09-29: "Complete repair, re-solve". Build the extension below, then solve and apply the decision rule.
  Do NOTHING else.

READ FIRST:
- docs/records/caiso/r-caiso-14/RESULT-r-caiso-14-2026-09-29.md
- docs/records/caiso/r-caiso-14/ADDENDUM-r-caiso-14-gdrift-2026-09-29.md
- docs/records/caiso/r-caiso-13/PRECOMMIT-r-caiso-13-2026-09-28.md: §3 holds the predictions and decision rule, reused
  unchanged.
- docs/records/caiso/r-caiso-13/shard-prompt.md: the template for your shard prompt.

BUILD (zero parameters; rules 14, 19, 23):
- Under the SAME flag `caiso_eia930_clock_repair` (one mechanism, rule 19), extend the repair to the HSL reader. When the
  flag is armed and the ISO is CAISO:
  - shift `wind_gen_mw` / `solar_gen_mw` one hour EARLIER inside `EIA930_CISO_CLOCK_LATE_WINDOWS_UTC`'s generation
    window, using the same row mapping the frame seam uses;
  - keep the curtailment term (`*_hsl_mw − *_gen_mw`), which is CAISO 5-min data already on the model clock;
  - recompose `*_hsl_mw = shifted gen + curtailment`.
- Do NOT rewrite the committed parquet (rule 23 frozen derive).
- Check every other CAISO consumer of EIA-930-derived artifacts for the same gap: EIA-930 wind/solar fallbacks,
  interchange, NG cells, and the hydro/storage actuals built from 930. Record the census in the PRECOMMIT.
- Unit tests: the off path is byte-identical; the armed path moves the 2024–25 HSL solar centroid to 11.5–12.0 h in every
  month; curtailment totals are conserved.
- Write a PRECOMMIT addendum before any solve, recording:
  - the arm-liveness row counts per year (new HSL counts alongside the frame counts);
  - a G-DRIFT extension from 332c8048 to your pin.

SOLVE (the parent never solves, rule 32(a)):
- Pin {SHA} to the full 40-char origin/main HEAD after your build PR merges.
- Launch 7 shards, one per year 2019–2025 (rule 36). Use a new shard prompt that updates the arm-liveness hard stop and
  names out-dir rcaiso15_A_{Y} / branch claude/r-caiso-15-A-{Y}.
- Substitution values:
  - {SRC} = rcaiso11_A_tp_2019_2021 for 2019–21, and rcaiso11_A_span for 2022–25;
  - {SDCAP} = 1436.0 for 2019–23, 2074.0 for 2024, and 2071.0 for 2025.

PARENT SEAM (as R-CAISO-14):
- Compose with scripts/probes/rcaiso_compose_span.py, passing repeated --require:
  - caiso_tac_shares_standard_time=true
  - caiso_ra_bridge_startup_aware=false
  - caiso_import_cap_floor_static=true
  - caiso_intertie_partial_year_measured=true
  - caiso_eia930_clock_repair=true
- Build the span 2022–25 and the fold 2019–21, with labels whose shorthands DIFFER.
- Diagnostics: legitimacy_diagnostics.py --bundle <b> --iso CAISO --json-out <b>/legitimacy_diagnostics.json.
- Registration: dashboard_add_run.py --no-prune, then a copy of scripts/gen_rcaiso14_attestation.py (--source the keeper
  bundle), then register again.
- Stamp the fold with stamp_touchpoint_holdout.py.
- Commit only the keeper shape. Gitignore p0_* and the per-year legs.
- Check P1–P5 from the composed hourlies:
  - the solar centroid by month;
  - scripts/probes/_rcaiso13_storage_timing.py with BUNDLE pointed at the new span (battery lag, Jun–Sep peak hour).
- A NON-promoted run must NOT be committed to main: audit_keepers E13 fails any CAISO run that is neither the keeper nor
  stamped to it. Keep it local (rule 31), and put its numbers in the RESULT.

PROMOTION (PRECOMMIT-r-caiso-13 §3 decision rule):
- If 2022–25 stays CALIBRATED AND the repair is complete (P1/P2 hold), promote on structure (rule 14):
  1. audit_keepers.py --iso CAISO (E1)
  2. prune_iso_runs.py --iso CAISO --force-uncite --keep <NEW FOLD ID>
  3. build_status.py --iso CAISO
  4. audit_keepers again
  5. re-key calibration-complete.json ("complete".CAISO) and keepers/CAISO.json with json.dump(indent=1)
  6. re-stamp the matrix shard (`keeper:`, `gates:`) and the §5.2 header
  7. set the caiso_eia930_clock_repair cell to K
- If the determination drops (C4 2025 is at 0.300 against ≤ 0.30), the trade goes to the owner as a decision card. Never
  take it in-session.

OWNER RULINGS IN FORCE (do not re-ask):
- SD floor static 1,436; LA Basin: "SD only".
- EIA930_GAS_FOLD_REFUTED: keep as is.
- startup_aware disarmed.
- tac_shares_standard_time armed.
- PS wall kept.
- The caiso-80 demand basis stands.
- "Complete repair, re-solve" (2026-09-29).

NOTES:
- A fresh container needs `pip install -e . pytest tzdata`.
- Run `ruff format` in a separate command before any push.
- check_registry_payload_parity flags your local gitignored legs. That is expected (rule 31) and absent in CI.
- tests/unit/data has 4 failures that are red on main too: cc_committed_offer_margin COAL, 2× gas_offer_zonal_anchor_vintage,
  nwpp_demand_plant_basis.
- Never `git grep` in a partial clone; use rg.

HARD RULES: CLAUDE.md is binding, especially rules 1, 13, 14, 19, 21, 23–25, 27, 28, 29(b)/(c), and 30–36.
- Owner decisions go to the owner as clickable decision cards (AskUserQuestion), never inline text.

END OF SESSION:
- Promote if the candidate is good. Create a PR and merge it (rebase-and-merge).
- Archive every shard, and report leftover shard branches for the owner to delete.
- If CAISO still has rubric failures, put the next-link choice to the owner as a decision card. Then launch R-CAISO-16
  with these same directions: archive its parent when safe, salvage/close CAISO branches and PRs, present decisions as
  cards, promote if good, PR + merge, archive shards, and launch the next link.
- If at the nesting limit, make the final message a complete handoff prompt in one code block.
