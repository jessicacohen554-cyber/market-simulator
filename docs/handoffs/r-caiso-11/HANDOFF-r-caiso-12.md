SESSION R-CAISO-12 — CAISO: the h15–17 ramp (imports vs gas) and the 2019–21 fold, zero LP first
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST: archive the parent session (R-CAISO-11) with mcp__Claude_Code_Remote__archive_session once its PR (branch
claude/r-caiso-11) reads MERGED (check with the GitHub MCP). If it is not merged, do not archive; say so in your first
report. Work on a fresh branch off origin/main.

THEN, before any new work, check for unmerged branches or open PRs for CAISO:
- Salvage anything not on main into your branch.
- Close the open PRs you salvaged.
- Report the leftover branches the owner must delete. Deleting a ref returns 403 here, so do not try.

STATE (2026-09-28):
- Keeper `2026-09-28-caiso-r11-tacpst` (bundle rcaiso11_A_span, 2022–2025) is CALIBRATED.
  - Single ledgered C3c 2024 (0 h vs 35 h).
  - C4 2025 gas NRMSE 0.294 vs ≤0.30.
  - Arm vs R-CAISO-10: `caiso_tac_shares_standard_time` (TAC zonal shares on the fixed-PST clock, rule 14).
    No criterion changed status.
- The 2019–21 fold `2026-09-28-caiso-r11-tacpst-touchpoints` (bundle rcaiso11_A_tp_2019_2021) is NOT-YET, reported
  only (rule 30(c)):

  | | 2019 | 2020 | 2021 |
  |---|--:|--:|--:|
  | C1 CC_REGULAR model / actual TWh | 59.1 / 36.1 | 68.4 / 43.1 | 59.7 / 49.2 |
  | C4 gas NRMSE | 0.570 | 0.529 | 0.382 |
  | C3a | unscoreable | unscoreable | 57.09 vs 50.87 |
  | C3c h > $200 (RT 27) | — | — | 87 |

READ FIRST:
- docs/handoffs/r-caiso-11/RESULT-r-caiso-11-2026-09-28.md (§1–§7)
- results/calibration/_rcaiso11/{object1_dual_census,ps_boundary_footprint}.json
- docs/mechanism-testing-matrix.md §5.2 and docs/codebase-site/data/mechanism-matrix/CAISO.js

OWNER RULINGS IN FORCE (do not re-ask):
- SD import limit: floor at static 1,436 (caiso_import_cap_floor_static). LA Basin: "SD only".
- EIA930_GAS_FOLD_REFUTED for CAISO: "Keep as is".
- `caiso_ra_bridge_startup_aware`: disarmed. Do not re-arm without new evidence.
- `caiso_tac_shares_standard_time`: armed and promoted (R-CAISO-11, "Fix + solve now").
- PUMPED-STORAGE WALL (caiso-141/145): KEPT (R-CAISO-11 card "Keep wall"). No PS envelope, no hydro-minus-PS split,
  no PS proxy from WAT, no fitted PS adder.

WHAT R-CAISO-11 ESTABLISHED (do not re-measure):
- The evening under-price is the h16–19 ramp peak. By h21–23 the model and DAM agree. The model prints a flat plateau
  from h18.
- The evening reserve dual is $0 in every hour (the co-opt is inert, caiso-144).
- The battery fleet is interior on SOC: it never binds, so it propagates a level rather than setting it. It
  discharges about 1 h late vs the CAISO Outlook measured battery series.
- Like-for-like hydro + PS vs EIA-930 WAT (which folds PS): the model shifts 0.3–0.5 GW midday→evening every year.
  The only instrument that reaches this is walled. The joint-envelope cap is provably INERT (0 hours).
- Demand clock (realign + supply-consistent armed) and the 2019-10..2020-08 WAT hole (backfill live) are NOT defects.

OBJECT 1 — the h15–17 ramp: imports up, gas down (zero LP first).
- In Jun–Sep 2022–25 at h15–17 the model imports +1.0–2.1 GW MORE than EIA-930 (−TI) and runs 3–5 GW LESS gas.
  At h18–21 imports are 0.4–4.1 GW BELOW measured, in every year and season.
- Identify which import tranche / corridor / hub-price window carries the h15–17 surplus. Use the keeper's committed
  class_hourly / system sidecars; if you need per-corridor flows, flows.parquet is in the local legs only
  (re-solve ~25 min/yr).
- Check every idea against the DO-NOT-REDO list below. In particular, the per-corridor firm-shape idea is EXCLUDED,
  and the caiso-252/253 at-hub WEIM windows are adjudicated (hod 22–23 demoted).
- Any fix must be ONE config across every scored year (rule 1 (a)–(e)). No per-year fitting. Structure first.

OBJECT 2 — the 2019–21 fold (zero LP).
- Test whether Object 1 explains the fold's CC excess before proposing anything fold-specific. The 2019–20 CC excess
  without a hub print stays STOPPED.

DO NOT re-test (R/G/I cells or censused):
- the export route: caiso_p1_export_sink_seam, caiso_corridor_export_path, caiso_node_export_constraint;
- the per-corridor firm-shape idea;
- raising caiso_ra_min_load_frac;
- the forward reference-price formula as a 2019–21 backcast price;
- a realized-import percentile as an SD cap;
- the 2019–20 CC excess without a hub print (STOP stands);
- re-arming startup_aware;
- hydro_pondage_bound on the NID gross-volume artifact;
- any pumped-storage restraint (wall kept);
- the joint hydro+PS WAT envelope (inert);
- the reserve co-opt (inert).

SOLVE RECIPE, if anything is armed:
- keeper recipe + the flag, one shard per year, 2019–2025 (rules 34(c), 35(c), 36);
- template docs/handoffs/r-caiso-11/shard-prompt.md (give the shard a short prompt pointing at that file with
  {Y}/{SHA}/{SRC}/{SDCAP}; swap the --set line and the hard-stop-3 arm field);
  - {SRC} is rcaiso11_A_tp_2019_2021 for 2019–21 and rcaiso11_A_span for 2022–25;
  - {SDCAP} is 1436.0 for 2019–23, 2074.0 for 2024 and 2071.0 for 2025;
- G-DRIFT: git diff the keeper solve sha 9005dc81 → HEAD over the solve paths; classify every hunk. Never
  `git grep` in this partial clone (it lazily fetches blobs); use rg on the working tree.
- Parent seam:
  - scripts/probes/rcaiso_compose_span.py with repeated --require (pass caiso_tac_shares_standard_time=true,
    caiso_ra_bridge_startup_aware=false, caiso_import_cap_floor_static=true,
    caiso_intertie_partial_year_measured=true, plus the new flag);
  - legitimacy_diagnostics.py --bundle <b> --iso CAISO --json-out <b>/legitimacy_diagnostics.json;
  - dashboard_add_run.py --no-prune, then a gen_rcaiso11_attestation.py copy (--source the keeper bundle), then
    register again;
  - stamp_touchpoint_holdout.py for the fold;
  - commit only the keeper shape (class / class_band / storage / system hourlies + json). Gitignore p0_* and the
    per-year legs.
- On promotion:
  - audit_keepers.py --iso CAISO (E1) BEFORE the prune;
  - prune_iso_runs.py --iso CAISO --force-uncite --keep <NEW FOLD ID>;
  - build_status.py --iso CAISO; audit_keepers again;
  - re-key calibration-complete.json ("complete".CAISO) and keepers/CAISO.json with json.dump(indent=1);
  - re-stamp the matrix shard (`keeper:`, `gates:`) and the §5.2 header.
- Give the fold and span labels whose shorthands DIFFER.
- A NOT-YET promotion withdraws the complete marker: surface that trade to the owner as a decision card, never take
  it in-session.

NOTES:
- A fresh container needs `pip install -e . pytest tzdata`.
- The ruff pre-push hook checks the whole command, so run `ruff format` in a separate command before any push.
- check_registry_payload_parity flags your local gitignored legs; that is expected (rule 31) and absent in CI.

HARD RULES: CLAUDE.md binding, especially 1, 13, 14, 19, 21, 23, 24, 25, 27, 28, 29(b)/(c), 30–36.
- The parent never solves (rule 32(a)).
- Owner decisions go to the owner as clickable decision cards (AskUserQuestion), never inline text.

END OF SESSION:
- promote if a good candidate; create a PR and merge it (rebase-and-merge);
- archive every shard;
- report leftover shard branches for the owner to delete;
- if CAISO still has rubric failures (the fold years, or anything new), launch the next handoff session
  (R-CAISO-13) with these same directions: archive its parent when safe, salvage/close CAISO branches and PRs,
  present decisions as cards, promote if good, PR + merge, archive shards, and launch the next link in the chain;
- if at the nesting limit, make the final message a complete handoff prompt in one code block instead.
- Known leftover branches today:
  - claude/r-caiso-10-A-2019 … -2025
  - claude/r-caiso-11-A-2019 … -2025
