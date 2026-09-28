SESSION R-CAISO-14 — CAISO: solve and promote `caiso_eia930_clock_repair` (new chain root)
DATA PROFILE: caiso
MODEL: Opus or Fable

This session starts a NEW chain. R-CAISO-13 hit the session nesting limit (depth 8), so it could not launch shards.

FIRST:
- Archive R-CAISO-13, session_01U8VMoPkd49fpavZJpVLWTN, with mcp__Claude_Code_Remote__archive_session. Do this once its PR
  (branch claude/r-caiso-13) reads MERGED on the GitHub MCP. If it is not merged, do not archive; say so in your first report.
- Work on a fresh branch off origin/main.
- Check for unmerged CAISO branches and open PRs:
  - salvage anything not on main into your branch;
  - close the open PRs you salvaged;
  - report the leftover branches the owner must delete. Deleting a ref returns 403, so do not try.

STATE (2026-09-28):
- Keeper `2026-09-28-caiso-r11-tacpst` (bundle rcaiso11_A_span, 2022–25) is CALIBRATED: a single ledgered C3c 2024, and
  C4 2025 gas NRMSE 0.294 against ≤ 0.30.
- The fold `2026-09-28-caiso-r11-tacpst-touchpoints` (2019–21) is NOT-YET and reported only (rule 30(c)).
- R-CAISO-13 found a rule-14 data defect and merged the arm `caiso_eia930_clock_repair` (gated, default off, zero
  parameters). The EIA-930 CISO extract is published one hour LATE in two windows:
  - generation, NG:*, and interchange: 2023-11-01 → 2025-12-02;
  - Demand: 2022-06-16 → 2025-12-02.
  This was measured against the OASIS TAC clock and solar geometry. The keeper's own solar centroid sits at 12.9 h PST in
  2024–25, and its battery profile lags CAISO Outlook by +1 h (r 0.99).
- Owner card "Build + solve now" (clock fix). Owner card "Solve + promote only" (next-link scope): do NOTHING else.

READ FIRST:
- docs/handoffs/r-caiso-13/RESULT-r-caiso-13-2026-09-28.md
- docs/handoffs/r-caiso-13/PRECOMMIT-r-caiso-13-2026-09-28.md: §3 holds the pre-registered predictions and the decision
  rule. Do not change them.
- docs/handoffs/r-caiso-13/shard-prompt.md

SOLVE (the parent never solves, rule 32(a)):
- Pin {SHA} to the full 40-char origin/main HEAD. Before pinning, verify it contains:
  - src/market_sim/data/eia930/frames.py::set_caiso_eia930_clock_repair;
  - docs/handoffs/r-caiso-13/shard-prompt.md.
- Launch 7 shards, one per year 2019–2025 (rule 36), each with this short prompt:
  "Read docs/handoffs/r-caiso-13/shard-prompt.md at the pinned commit and follow it EXACTLY with {Y}/{SHA}/{SRC}/{SDCAP}".
- Substitution values:
  - {SRC} = rcaiso11_A_tp_2019_2021 for 2019–21, and rcaiso11_A_span for 2022–25;
  - {SDCAP} = 1436.0 for 2019–23, 2074.0 for 2024, and 2071.0 for 2025.
- The shard prompt's arm-liveness hard stop must print, per year:
  - 2019, 2020, 2021: `0 0 0`
  - 2022: `4776 0 0`
  - 2023: `8752 1140 1465`
  - 2024: `8758 7666 8755`
  - 2025: `8049 6943 8051`
- G-DRIFT: the PRECOMMIT §2 audit covers 9005dc81 → 14c1d70e, and every hunk is INERT. Extend it to your pinned SHA and
  classify each new hunk. Never `git grep` in a partial clone; use rg on the working tree.

PARENT SEAM (unchanged from R-CAISO-11):
- Compose with scripts/probes/rcaiso_compose_span.py, passing repeated --require:
  - caiso_tac_shares_standard_time=true
  - caiso_ra_bridge_startup_aware=false
  - caiso_import_cap_floor_static=true
  - caiso_intertie_partial_year_measured=true
  - caiso_eia930_clock_repair=true
- Build the span 2022–25 and the fold 2019–21, with labels whose shorthands DIFFER.
- Diagnostics: legitimacy_diagnostics.py --bundle <b> --iso CAISO --json-out <b>/legitimacy_diagnostics.json.
- Registration: dashboard_add_run.py --no-prune, then a gen_rcaiso11_attestation.py copy (--source the keeper bundle),
  then register again.
- Stamp the fold with stamp_touchpoint_holdout.py.
- Commit only the keeper shape (the class / class_band / storage / system hourlies plus the json files). Gitignore p0_*
  and the per-year legs.
- Check the pre-registered predictions P1–P5 (PRECOMMIT §3) from the composed hourlies. Re-run the R-CAISO-13 probe
  against the new span, pointing BUNDLE at it.

PROMOTION (PRECOMMIT §3 decision rule):
- If 2022–25 stays CALIBRATED, promote on structure (rule 14):
  1. audit_keepers.py --iso CAISO (E1)
  2. prune_iso_runs.py --iso CAISO --force-uncite --keep <NEW FOLD ID>
  3. build_status.py --iso CAISO
  4. audit_keepers again
  5. re-key calibration-complete.json ("complete".CAISO) and keepers/CAISO.json with json.dump(indent=1)
  6. re-stamp the matrix shard (`keeper:`, `gates:`) and the §5.2 header
  7. set the caiso_eia930_clock_repair cell to K
- If the determination drops, the trade goes to the owner as a decision card. A NOT-YET promotion withdraws the complete
  marker. Never take that in-session.
- If not promoted, set the cell to R and cite the RESULT. Keep the bundles until the owner rules (rule 31).

OWNER RULINGS IN FORCE (do not re-ask):
- SD floor static 1,436; LA Basin: "SD only".
- EIA930_GAS_FOLD_REFUTED: keep as is.
- startup_aware disarmed.
- tac_shares_standard_time armed.
- PS wall kept.
- The caiso-80 supply-consistent demand basis stands. Its 5–8 GW midday gap to TAC is reported and not re-opened.

NOTES:
- A fresh container needs `pip install -e . pytest tzdata`.
- Run `ruff format` in a separate command before any push.
- check_registry_payload_parity flags your local gitignored legs. That is expected (rule 31) and absent in CI.
- tests/unit/data has 4 failures that are red on main too: cc_committed_offer_margin COAL, 2× gas_offer_zonal_anchor_vintage,
  nwpp_demand_plant_basis. They are not this lane's.

HARD RULES: CLAUDE.md is binding, especially rules 1, 13, 14, 19, 21, 23–25, 27, 28, 29(b)/(c), and 30–36.
- Owner decisions go to the owner as clickable decision cards (AskUserQuestion), never inline text.

END OF SESSION:
- Promote if the candidate is good. Create a PR and merge it (rebase-and-merge).
- Archive every shard, and report leftover shard branches for the owner to delete.
- If CAISO still has rubric failures, put the next-link choice to the owner as a decision card. Then launch R-CAISO-15 with
  these same directions: archive its parent when safe, salvage/close CAISO branches and PRs, present decisions as cards,
  promote if good, PR + merge, archive shards, and launch the next link.
- If at the nesting limit, make the final message a complete handoff prompt in one code block.
