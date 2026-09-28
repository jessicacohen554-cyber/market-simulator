SESSION R-CAISO-13 — CAISO: battery discharge timing and the evening under-price, zero LP first
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST: archive the parent session (R-CAISO-12) with mcp__Claude_Code_Remote__archive_session once its PR (branch
claude/r-caiso-12) reads MERGED (check with the GitHub MCP). If it is not merged, do not archive; say so in your first
report. Work on a fresh branch off origin/main.

THEN, before any new work, check for unmerged branches or open PRs for CAISO:
- Salvage anything not on main into your branch.
- Close the open PRs you salvaged.
- Report the leftover branches the owner must delete. Deleting a ref returns 403 here, so do not try.

STATE (2026-09-28):
- Keeper `2026-09-28-caiso-r11-tacpst` (bundle rcaiso11_A_span, 2022–2025) is CALIBRATED.
  - Single ledgered C3c 2024 (0 h vs 35 h > $200).
  - C4 2025 gas NRMSE 0.294 vs ≤0.30.
- The 2019–21 fold `2026-09-28-caiso-r11-tacpst-touchpoints` is NOT-YET, reported only (rule 30(c)).
  2019–20 is data-blocked: there is no hub print, and the ICE daily index was tested and failed (R-CAISO-12 §4).
- R-CAISO-12 was zero LP and found no admissible import lever. The owner card chose THIS object as the next link
  ("Storage timing").

READ FIRST:
- docs/handoffs/r-caiso-12/RESULT-r-caiso-12-2026-09-28.md (all)
- docs/handoffs/r-caiso-11/RESULT-r-caiso-11-2026-09-28.md §1–§2 (the evening gap; the battery census)
- results/calibration/_rcaiso11/object1_dual_census.json and results/calibration/_rcaiso12/import_census.json
- the caiso-253 block in docs/mechanism-testing-matrix.md §5.2 (the hod 22–23 gap re-pointed at STORAGE)
- docs/codebase-site/data/mechanism-matrix/CAISO.js cells battery_dispatch_adder, storage_measured_anchors,
  storage_daily_cycling, ercot_storage_adaptive_expectation, caiso_ps_charge_shape_anchor

OWNER RULINGS IN FORCE (do not re-ask):
- SD import limit: floor at static 1,436 (caiso_import_cap_floor_static). LA Basin: "SD only".
- EIA930_GAS_FOLD_REFUTED for CAISO: "Keep as is".
- `caiso_ra_bridge_startup_aware`: disarmed. Do not re-arm without new evidence.
- `caiso_tac_shares_standard_time`: armed and promoted.
- PUMPED-STORAGE WALL (caiso-141/145): KEPT. No PS envelope, no hydro-minus-PS split, no PS proxy from WAT, no fitted
  PS adder.
- Next-link card (R-CAISO-12): "Storage timing".

WHAT IS ESTABLISHED (do not re-measure):
- The evening under-price is the h16–19 ramp peak. By h21–23 the model and DAM agree; the model prints a flat plateau
  from h18.
- It is NOT a gas shortfall. Against CEMS (C4's basis), model gas is +0.2 to +1.9 GW ABOVE measured at h19–21 and
  −0.4 to −1.5 GW below at h8–16 (R-CAISO-12 §1). The EIA-930 CISO NG cell is registered corrupt: never use it.
- Imports mirror the model-vs-DAM intertie price error. The midday surplus is in the `K` WEIM clean rungs, and the
  export legs clear 0 MW. No import lever (R-CAISO-12 §3).
- The reserve co-opt is inert ($0 dual every hour, caiso-144).
- The battery fleet is interior on SOC and never binds. It discharges about 1 h LATE against CAISO Outlook
  "Total batteries" (data/raw/storage-dispatch-actuals). 2024 h16: −0.18 GW model vs +1.25 GW measured. It
  over-discharges at h20–23, and annual discharge is 11–13 % below measured in 2024–25 (R-CAISO-11 §2).
- CLOCK: every measured hourly series must be put on the model's fixed-PST hour-beginning clock before comparison.
  R-CAISO-12 found the prior hand-off's h15–17 claim was a prevailing hour-ending misread. Check the storage series'
  convention FIRST and state it in the PRECOMMIT.

OBJECT — why the model's batteries discharge late and flat (zero LP first):
- Put the measured battery series on the model clock and re-confirm the 1 h lag. If the lag disappears on the
  correct clock, STOP and report: that is the finding.
- If it survives: an LP with perfect daily foresight and no binding SOC should discharge into the highest-priced
  hours. A late or flat discharge therefore says the model's own price is flat across h17–22, which is the plateau.
  Establish which way causality runs before proposing anything: is storage following a flat price, or making it flat?
- Candidate structure, to be checked against the cells first:
  - the measured anchors / bid-belly construction (storage_measured_anchors K);
  - the power/energy ratio, or duration, of the fleet vs CAISO's measured fleet;
  - round-trip efficiency;
  - charge-side availability at midday.
- Any fix must be ONE config across every scored year (rule 1 (a)–(e)). No per-year fitting, no fitted adder.
  Structure first.

DO NOT re-test (R/G/I cells or censused):
- storage_daily_cycling (G), caiso_ps_charge_shape_anchor (G), ercot_storage_adaptive_expectation (I);
- battery_dispatch_adder as a price lever (caiso-256 measured it; K at 0);
- any pumped-storage restraint (wall kept), the joint hydro+PS WAT envelope (inert);
- the reserve co-opt (inert);
- the import route: the export legs (caiso_p1_export_sink_seam, caiso_corridor_export_path,
  caiso_node_export_constraint), the per-corridor firm-shape idea, and re-sizing the clean-rung depth;
- the ICE daily index as a 2019–20 hub price, and the 2019–20 CC excess without a hub print (STOP);
- raising caiso_ra_min_load_frac; re-arming startup_aware; hydro_pondage_bound on the NID gross-volume artifact;
- a realized-import percentile as an SD cap; the forward reference-price formula as a 2019–21 backcast price.

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
- if CAISO still has rubric failures (the fold years, the ledgered C3c, or anything new), put the next-link choice
  to the owner as a decision card, then launch R-CAISO-14 with these same directions: archive its parent when safe,
  salvage/close CAISO branches and PRs, present decisions as cards, promote if good, PR + merge, archive shards, and
  launch the next link in the chain;
- if at the nesting limit, make the final message a complete handoff prompt in one code block instead.
- Known leftover branches today:
  - claude/r-caiso-10-A-2024
  - claude/r-caiso-11-A-2019 … -2025
