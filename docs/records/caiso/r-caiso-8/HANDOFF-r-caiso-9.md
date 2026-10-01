SESSION R-CAISO-9 — CAISO: (1) floor the SD import cap at the static 1,436 MW (owner ruling); (2) the next 2022–25 lever
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST: archive the parent session session_01AGtNdL5bEb4orV4ru6TZhr (R-CAISO-8) with
mcp__Claude_Code_Remote__archive_session once its PR (branch claude/r-caiso-8) reads MERGED (check with the GitHub
MCP). If it is not merged, do not archive; say so in your first report. Work on a fresh branch off origin/main.

THEN, before any new work, check for unmerged branches or open PRs for CAISO:
- Salvage anything not on main into your branch.
- Close the open PRs you salvaged.
- Report the leftover branches the owner must delete. Deleting a ref returns 403 here, so do not try.

STATE (2026-09-27):
- Keeper `2026-09-27-caiso-r8-partial-year` (bundle rcaiso8_A_span, 2022–2025) is CALIBRATED.
  - Single ledgered C3c 2024 (0 h vs 35 h).
  - C4 2025 gas NRMSE 0.299 vs ≤0.30 (thin).
- The 2019–21 fold `2026-09-27-caiso-r8-fold` (bundle rcaiso8_A_tp_2019_2021) is NOT-YET, reported only
  (rule 30(c)). Scores:

  | | 2019 | 2020 | 2021 |
  |---|--:|--:|--:|
  | C1 CC_REGULAR, TWh | +20.4 | +24.8 | +10.1 |
  | C4 gas NRMSE | 0.575 | 0.530 | 0.387 |
  | C3a 2021 | | | +13.5 % |
  | C3b 2021 | | | PASS |

READ FIRST:
- docs/handoffs/r-caiso-8/RESULT-r-caiso-8-2026-09-27.md (Object 2 section and "Owner rulings")
- results/calibration/_rcaiso8/object2_sd_census.json (probe: scripts/probes/_rcaiso8_sd_import_census.py)
- docs/mechanism-testing-matrix.md §5.2
- docs/codebase-site/data/mechanism-matrix/CAISO.js
- runner.py around `caiso_per_year_import_caps` (~line 3368) and model/interchange/caiso.py ~line 1950

OWNER RULINGS (2026-09-27, decision cards — binding, do not re-ask):
- SD import limit: "Floor at static 1,436".
  - Keep the per-year LCT caps (`peak_load − requirement`), but never below the documented static
    `_SDGE_IMPORT_CAP_MW` = 1,436 MW (iso_configs.py).
  - This is a declared rule-14 reconciled estimate. The LCT figure is a 1-in-10 N-1-1 planning-case capability,
    not an operating limit. Measured night-time imports exceed it in 2,773 / 784 / 886 hours in 2019 / 20 / 21.
    The 1,436 floor is itself exceeded 167 h in 2019; say so in the comment.
- EIA930_GAS_FOLD_REFUTED for CAISO: "Keep as is". Do not flip, do not re-raise.

OBJECT 1 — implement the SD floor.
- Add a default-off ScenarioConfig flag, e.g. caiso_import_cap_floor_static:
  - the per-year SDGE cap = max(per-year LCT cap, the static 1,436);
  - zero new numbers (it reuses the existing constant; rules 21/24);
  - registered in the cache-key optional fields + defaults in the same commit;
  - matrix row + a cell in EVERY ISO shard in the same PR (rule 28(c)).
- LA Basin: census the per-year LA caps against the static 12,008 first.
  - If no year falls below it, leave LA untouched and say so.
  - If one does, bring it to the owner. It is not covered by the ruling.
- Tests: trivial case first.
- G-DRIFT (copy scripts/probes/_rcaiso8_gdrift_identity.py; pin 2019–21 and 2022–25 to ee309e39). Expected:
  - flag OFF→ON moves only the 2019–21 link TTC (topology), nothing in 2022–25, since those caps are
    ≥1,436 already;
  - HEAD vs pin moves nothing.
- PRECOMMIT with pre-registered directions for 2019–21:
  - SDGE unserved and SDGE mean price fall (2019: 419,683 MWh unserved, $388.8 mean today);
  - binding hours on SP15_rest>SDGE fall;
  - state the C3a / C3b 2019–21 direction.
- Solve:
  - the keeper recipe + the flag, one shard per year, 2019–2025 (rules 34(c), 35(c), 36);
  - full bundles pushed (34(a)); SHA pinned; solves run in the FOREGROUND;
  - template docs/handoffs/r-caiso-8/shard-prompt.md, with `--set caiso_import_cap_floor_static=true` added;
  - pin the new constants' sha / hashes in the hard stops;
  - per-year legs gitignored in CONTENTS form.
- Parent seam:
  - scripts/probes/rcaiso_compose_span.py --require … (both the new flag and caiso_intertie_partial_year_measured);
  - legitimacy_diagnostics.py --json-out;
  - dashboard_add_run.py --no-prune, then scripts/gen_rcaiso8_attestation.py (adapt the text), then register again;
  - stamp_touchpoint_holdout.py for the fold.
- On promotion:
  - audit_keepers.py --iso CAISO (E1) BEFORE the prune;
  - prune_iso_runs.py --iso CAISO --force-uncite --keep <NEW FOLD ID>. **The --keep is mandatory**: without it the
    script prunes the just-stamped fold, which R-CAISO-8 had to rebuild;
  - build_status.py --iso CAISO; audit_keepers again;
  - re-key calibration-complete.json and keepers/CAISO.json;
  - re-stamp the matrix shard and update the §5.2 header.
- Labels: dashboard_add_run derives the run id from the label's leading words. Give the fold and the span labels
  whose shorthands DIFFER, or the second registration overwrites the first.
- If 2022–25 stay CALIBRATED, it is a promotion candidate. A NOT-YET promotion withdraws the complete marker:
  surface that trade to the owner as a decision card, never take it in-session.

OBJECT 2 — the next 2022–25 lever (zero LP first), in priority order:
- (a) C4 2025 margin (0.299 vs 0.30). R-CAISO-6 found no admissible lever in the midday import shape.
  - Check the matrix lever queue §5.2 before proposing anything.
  - Do NOT re-test R/G/I cells.
- (b) The remaining 2021 DSW gap (−2.9 GW mean at h17–22). Is it the unprinted Jan–Apr hours or the evening rungs?
  - Census it zero-LP on rcaiso8_A_tp_2019_2021 (scripts/probes/_rcaiso8_2021_corridor_census.py).
  - The 2019–20 STOP stands (no hub print).
- Report findings; arm nothing without a PRECOMMIT.

DO NOT re-test (R/G cells or censused):
- the export route: caiso_p1_export_sink_seam, caiso_corridor_export_path, caiso_node_export_constraint;
- the per-corridor firm-shape idea;
- raising caiso_ra_min_load_frac;
- the forward reference-price formula as a 2019–21 backcast price;
- a realized-import percentile as an SD cap (rules 13/21; R-CAISO-8 Object 2).

NOTE: the Fast test tier on main has ~25 pre-existing failures. Not yours unless one is CAISO-scoped and in your
diff.

HARD RULES: CLAUDE.md binding, especially 1, 13, 14, 19, 21, 23, 24, 25, 27, 28, 29(b)/(c), 30–36.
- The parent never solves (rule 32(a)).
- Owner decisions go to the owner as clickable decision cards (AskUserQuestion), never inline text.

END OF SESSION:
- promote if a good candidate; create a PR and merge it (rebase-and-merge);
- archive every shard;
- report leftover shard branches for the owner to delete;
- if CAISO still has rubric failures (the fold years, or anything new), launch the next handoff session
  (R-CAISO-10) with these same directions: archive its parent when safe, salvage/close CAISO branches and PRs,
  present decisions as cards, promote if good, PR + merge, archive shards, and launch the next link in the chain;
- if at the nesting limit, make the final message a complete handoff prompt in one code block instead.
- Known leftover branches today:
  - claude/r-caiso-6, claude/r-caiso-6-O2-2019/2020/2021, claude/r-caiso-7
  - claude/r-caiso-8-A-2019 … -2025
