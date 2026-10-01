SESSION R-CAISO-10 — CAISO: the next 2022–25 lever and the 2019–21 fold, zero LP first
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST: archive the parent session (R-CAISO-9) with mcp__Claude_Code_Remote__archive_session once its PR (branch
claude/r-caiso-9) reads MERGED (check with the GitHub MCP). If it is not merged, do not archive; say so in your first
report. Work on a fresh branch off origin/main.

THEN, before any new work, check for unmerged branches or open PRs for CAISO:
- Salvage anything not on main into your branch.
- Close the open PRs you salvaged.
- Report the leftover branches the owner must delete. Deleting a ref returns 403 here, so do not try.

STATE (2026-09-28):
- Keeper `2026-09-28-caiso-r9-sd-floor` (bundle rcaiso9_A_span, 2022–2025) is CALIBRATED.
  - Single ledgered C3c 2024 (0 h vs 35 h).
  - C4 2025 gas NRMSE 0.299 vs ≤0.30 (thin).
- The 2019–21 fold `2026-09-28-caiso-r9-fold` (bundle rcaiso9_A_tp_2019_2021) is NOT-YET, reported only
  (rule 30(c)):

  | | 2019 | 2020 | 2021 |
  |---|--:|--:|--:|
  | C1 CC_REGULAR, TWh | +22.9 | +25.1 | +10.4 |
  | C4 gas NRMSE | 0.570 | 0.528 | 0.383 |
  | C3a | unscoreable | unscoreable | +12.5 % |
  | C3c h > $200 (RT 27) | — | — | 90 |

READ FIRST:
- docs/records/caiso/r-caiso-9/RESULT-r-caiso-9-2026-09-28.md (Object 2 section)
- results/calibration/_rcaiso9/object2_census.json (probe: scripts/probes/_rcaiso9_object2_census.py)
- docs/mechanism-testing-matrix.md §5.2 and docs/codebase-site/data/mechanism-matrix/CAISO.js

OWNER RULINGS IN FORCE (do not re-ask):
- SD import limit: floor at static 1,436 (armed as caiso_import_cap_floor_static). LA Basin: "SD only".
- EIA930_GAS_FOLD_REFUTED for CAISO: "Keep as is". Do not flip, do not re-raise.

OBJECT 1 — C4 2025 margin (zero LP first).
- R-CAISO-9 split the midday (h9–16) CC_REGULAR deficit per plant:
  - −947 MW from units CEMS shows on but the model has off;
  - −668 MW from lower loading;
  - +793 MW over elsewhere.
- Census which of those "CEMS-on / model-off" plants the RA must-offer bridge (caiso_ra_mustoffer) covers:
  - Were they detected in P0?
  - Why does the bridge not hold them midday?
  - Use the 2025 leg's P0/P1 dispatch (re-solve cost ~20 min if the leg is gone; state it before spending).
- Propose an arm only with a PRECOMMIT, a measured source and a forward story (rules 13, 17, 18, 19).
- Raising caiso_ra_min_load_frac is DO-NOT-RETEST.

OBJECT 2 — the 2021 evening price shape (zero LP).
- In the hub-printed 2021 evenings (h17–22), model SP15_rest is $68.9 vs measured DAM TH_SP15 $77.8, and midday is
  $3.0 high. DSW imports (hub $79.1) are priced out.
- Census which unit/tranche sets the model's evening price in those hours vs 2023–25 evenings (where C3a passes).
- Any fix must be ONE config across every scored year (rule 1 carve-out conditions (a)–(e)). No per-year fitting.

DO NOT re-test (R/G/I cells or censused):
- the export route: caiso_p1_export_sink_seam, caiso_corridor_export_path, caiso_node_export_constraint;
- the per-corridor firm-shape idea;
- raising caiso_ra_min_load_frac;
- the forward reference-price formula as a 2019–21 backcast price;
- a realized-import percentile as an SD cap;
- the 2019–20 CC excess without a hub print (STOP stands).

SOLVE RECIPE, if anything is armed:
- keeper recipe + the flag, one shard per year, 2019–2025 (rules 34(c), 35(c), 36);
- template docs/records/caiso/r-caiso-9/shard-prompt.md (swap the --set line and the hard-stop 3 fields);
- G-DRIFT via a copy of scripts/probes/_rcaiso9_gdrift_identity.py pinned to 980f2ed6;
- parent seam:
  - rcaiso_compose_span.py --require … (caiso_import_cap_floor_static and caiso_intertie_partial_year_measured,
    plus the new flag);
  - legitimacy_diagnostics.py --json-out;
  - dashboard_add_run.py --no-prune, then a gen_rcaiso9_attestation.py copy, then register again;
  - stamp_touchpoint_holdout.py for the fold.
- On promotion:
  - audit_keepers.py --iso CAISO (E1) BEFORE the prune;
  - prune_iso_runs.py --iso CAISO --force-uncite --keep <NEW FOLD ID> (the --keep is mandatory);
  - build_status.py --iso CAISO; audit_keepers again;
  - re-key calibration-complete.json and keepers/CAISO.json;
  - re-stamp the matrix shard and the §5.2 header.
- Give the fold and span labels whose shorthands DIFFER.
- A NOT-YET promotion withdraws the complete marker: surface that trade to the owner as a decision card, never take
  it in-session.

NOTES:
- A fresh container needs `pip install -e . pytest tzdata` (and `--ignore-installed PyYAML` for requirements.txt).
- Shards tend to run the solve in the background despite the prompt; check each shard's branch landed with
  `git ls-remote` before archiving.

HARD RULES: CLAUDE.md binding, especially 1, 13, 14, 19, 21, 23, 24, 25, 27, 28, 29(b)/(c), 30–36.
- The parent never solves (rule 32(a)).
- Owner decisions go to the owner as clickable decision cards (AskUserQuestion), never inline text.

END OF SESSION:
- promote if a good candidate; create a PR and merge it (rebase-and-merge);
- archive every shard;
- report leftover shard branches for the owner to delete;
- if CAISO still has rubric failures (the fold years, or anything new), launch the next handoff session
  (R-CAISO-11) with these same directions: archive its parent when safe, salvage/close CAISO branches and PRs,
  present decisions as cards, promote if good, PR + merge, archive shards, and launch the next link in the chain;
- if at the nesting limit, make the final message a complete handoff prompt in one code block instead.
- Known leftover branches today:
  - claude/r-caiso-8, claude/r-caiso-8-A-2019 … -2025
  - claude/r-caiso-9-A-2019 … -2025
