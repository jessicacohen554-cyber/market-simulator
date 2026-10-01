SESSION R-CAISO-11 — CAISO: the evening price shape and the 2019–21 fold, zero LP first
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST: archive the parent session (R-CAISO-10) with mcp__Claude_Code_Remote__archive_session once its PR (branch
claude/r-caiso-10) reads MERGED (check with the GitHub MCP). If it is not merged, do not archive; say so in your first
report. Work on a fresh branch off origin/main.

THEN, before any new work, check for unmerged branches or open PRs for CAISO:
- Salvage anything not on main into your branch.
- Close the open PRs you salvaged.
- Report the leftover branches the owner must delete. Deleting a ref returns 403 here, so do not try.

STATE (2026-09-28):
- Keeper `2026-09-28-caiso-r10-nosa` (bundle rcaiso10_A_span, 2022–2025) is CALIBRATED.
  - Single ledgered C3c 2024 (0 h vs 35 h).
  - C4 2025 gas NRMSE 0.294 vs ≤0.30.
  - Arm vs R-CAISO-9: `caiso_ra_bridge_startup_aware` disarmed (owner card "Test disarm, 7 shards").
- The 2019–21 fold `2026-09-28-caiso-r10-nosa-fold` (bundle rcaiso10_A_tp_2019_2021) is NOT-YET, reported only
  (rule 30(c)):

  | | 2019 | 2020 | 2021 |
  |---|--:|--:|--:|
  | C1 CC_REGULAR, TWh over actual | +23.0 | +25.2 | +10.6 |
  | C4 gas NRMSE | 0.570 | 0.528 | 0.383 |
  | C3a | unscoreable | unscoreable | +12.3 % |
  | C3c h > $200 (RT 27) | — | — | 87 |

READ FIRST:
- docs/handoffs/r-caiso-10/RESULT-r-caiso-10-2026-09-28.md
- results/calibration/_rcaiso10/object2_price_setter.json (probe: scripts/probes/_rcaiso10_object2_price_setter.py)
- docs/mechanism-testing-matrix.md §5.2 and docs/codebase-site/data/mechanism-matrix/CAISO.js

OWNER RULINGS IN FORCE (do not re-ask):
- SD import limit: floor at static 1,436 (armed as caiso_import_cap_floor_static). LA Basin: "SD only".
- EIA930_GAS_FOLD_REFUTED for CAISO: "Keep as is". Do not flip, do not re-raise.
- `caiso_ra_bridge_startup_aware`: disarmed and promoted (R-CAISO-10). Do not re-arm without new evidence.

OBJECT 1 — the cross-year evening under-price (zero LP first).
- In PALOVRDE-printed hours, model SP15_rest h17–22 is below measured DAM TH_SP15 in every year:

  | | 2021 | 2022 | 2023 | 2024 | 2025 |
  |---|--:|--:|--:|--:|--:|
  | model $/MWh | 69.1 | 109.7 | 57.2 | 43.7 | 43.1 |
  | DAM $/MWh | 77.8 | 117.5 | 78.1 | 53.9 | 47.5 |

- Middays are too high (e.g. 2024 model $23.6 vs DAM $13.0).
- The rubric's reported D-A amplitude is 70–89 % of measured. C3a passes on the annual mean because the two errors
  offset.
- Hydro is the partially-loaded marginal unit in 30–55 % of evening hours. Its hourly shape already matches EIA-930 in
  2023–25, so hydro's price is its budget dual: something ELSE sets the level of that dual.
- Census what sets that dual:
  - storage SOC duals;
  - the evening import ladder / hub price in the hours where no thermal is marginal (none_thermal 9–44 %);
  - the evening reserve product.
- Use the legs' unit_hourly / storage / system sidecars. Per-year legs are NOT on main; re-extracting needs a
  ~20 min re-solve each. The composite hourly sidecars on main (class_hourly, system, storage) may be enough; start
  there.
- Any fix must be ONE config across every scored year (rule 1 carve-out (a)–(e)). No per-year fitting.
- The hydro pondage bound is NOT the lever: its gross-volume artifact under-constrains (NYISO R), and CAISO hydro
  shape is already right in 2023–25.

OBJECT 2 — 2021 fold (zero LP).
- 2021 over-concentrates evening hydro (evening/mean 1.83 vs EIA-930 1.62), about +270 MW in the evening.
- DSW imports (hub $79.1) are priced out by a $68.9 model evening.
- Test whether Object 1's root cause also explains 2021 before proposing anything 2021-specific.

DO NOT re-test (R/G/I cells or censused):
- the export route: caiso_p1_export_sink_seam, caiso_corridor_export_path, caiso_node_export_constraint;
- the per-corridor firm-shape idea;
- raising caiso_ra_min_load_frac;
- the forward reference-price formula as a 2019–21 backcast price;
- a realized-import percentile as an SD cap;
- the 2019–20 CC excess without a hub print (STOP stands);
- re-arming startup_aware;
- hydro_pondage_bound on the NID gross-volume artifact.

SOLVE RECIPE, if anything is armed:
- keeper recipe + the flag, one shard per year, 2019–2025 (rules 34(c), 35(c), 36);
- template docs/handoffs/r-caiso-10/shard-prompt.md (give the shard a short prompt pointing at that file with
  {Y}/{SHA}/{SRC}/{SDCAP}; swap the --set line and the hard-stop 3 arm fields);
  - {SRC} is rcaiso10_A_tp_2019_2021 for 2019–21 and rcaiso10_A_span for 2022–25;
  - {SDCAP} is 1436.0 for 2019–23, 2074.0 for 2024 and 2071.0 for 2025;
- G-DRIFT: git diff the keeper solve sha 4caee8d0 → HEAD over the solve paths; classify every hunk.
- Parent seam:
  - scripts/probes/rcaiso_compose_span.py with repeated --require (it now overrides keeper-posture keys; pass
    caiso_ra_bridge_startup_aware=false, caiso_import_cap_floor_static=true,
    caiso_intertie_partial_year_measured=true, plus the new flag);
  - legitimacy_diagnostics.py --json-out;
  - dashboard_add_run.py --no-prune, then a gen_rcaiso10_attestation.py copy, then register again;
  - stamp_touchpoint_holdout.py for the fold.
- On promotion:
  - audit_keepers.py --iso CAISO (E1) BEFORE the prune;
  - prune_iso_runs.py --iso CAISO --force-uncite --keep <NEW FOLD ID> (the --keep is mandatory);
  - build_status.py --iso CAISO; audit_keepers again;
  - re-key calibration-complete.json ("complete".CAISO) and keepers/CAISO.json — preserve the JSON's ASCII escaping
    (json.dumps(indent=1), no ensure_ascii=False);
  - re-stamp the matrix shard (`keeper:` field and `gates:`) and the §5.2 header.
- Give the fold and span labels whose shorthands DIFFER.
- A NOT-YET promotion withdraws the complete marker: surface that trade to the owner as a decision card, never take
  it in-session.

NOTES:
- A fresh container needs `pip install -e . pytest tzdata`.
- Shards often background the solve and go idle, then resume. Poll with `git ls-remote` and a send_later check-in;
  archive each shard once its bytes are fetched, extracted and verified.

HARD RULES: CLAUDE.md binding, especially 1, 13, 14, 19, 21, 23, 24, 25, 27, 28, 29(b)/(c), 30–36.
- The parent never solves (rule 32(a)).
- Owner decisions go to the owner as clickable decision cards (AskUserQuestion), never inline text.

END OF SESSION:
- promote if a good candidate; create a PR and merge it (rebase-and-merge);
- archive every shard;
- report leftover shard branches for the owner to delete;
- if CAISO still has rubric failures (the fold years, or anything new), launch the next handoff session
  (R-CAISO-12) with these same directions: archive its parent when safe, salvage/close CAISO branches and PRs,
  present decisions as cards, promote if good, PR + merge, archive shards, and launch the next link in the chain;
- if at the nesting limit, make the final message a complete handoff prompt in one code block instead.
- Known leftover branches today:
  - claude/r-caiso-9
  - claude/r-caiso-10-A-2019 … -2025
