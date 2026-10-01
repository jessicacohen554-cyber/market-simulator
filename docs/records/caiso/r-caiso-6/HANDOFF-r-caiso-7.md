SESSION R-CAISO-7 — CAISO: (1) the 2019-21 CC_REGULAR over-dispatch (+19 to +25 TWh); (2) the routed 2022 LCT area-peak rows; (3) the C4 2025 thin margin (0.2987 vs <=0.30)
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST: archive the parent session session_01SjQUcbEjNjjaY3Hf635Va5 (R-CAISO-6) with
mcp__Claude_Code_Remote__archive_session once PR #6785 reads MERGED (check with the GitHub MCP). If it is not
merged, do not archive; say so in your first report.

STATE (2026-09-27):
- Keeper `2026-09-26-caiso-r5-pastoria-co2` (bundle rcaiso5_XE_span, 2022-2025) is CALIBRATED.
  - Single ledgered C3c 2024.
  - C4 2025 gas NRMSE 0.2987 vs <=0.30 (thin).
- 2019-2021 are folded as `2026-09-27-caiso-r6-malin-fold` (rcaiso6_tp_2019_2021), reported only (rule 30(c)).
  - NOT-YET: C1 CC_REGULAR, C3a 2021, C3b 2021, C4.
  - CC_REGULAR model vs actual: 56.5 / 67.9 / 68.6 vs 36.1 / 43.1 / 49.2 TWh.
- Recipe = XE. DOF 9/6. Offer curves unchanged.

READ FIRST:
- docs/handoffs/r-caiso-6/RESULT-r-caiso-6-2026-09-27.md and PRECOMMIT §1-§3;
- docs/handoffs/r-caiso-5/RESULT-r-caiso-5-2026-09-26.md §5-§6;
- docs/mechanism-testing-matrix.md §5.2;
- docs/codebase-site/data/mechanism-matrix/CAISO.js.

OBJECT 1 — why 2019-21 over-dispatch CC_REGULAR by ~20 TWh (zero LP first).
- Split the gap by class and window against EIA-923 / CEMS per plant. The fold payload carries per-plant model vs
  CEMS.
- Candidate measured-input suspects, each to be CHECKED, not assumed:
  - hydro (2019 wet year: model 29.2 TWh vs 930);
  - imports vs EIA-930 by corridor (use scripts/probes/_rcaiso6_corridor_split.py adapted to the fold bundle);
  - the bench basis: gas_foldin_deflation vs the CEMS anchor. EIA930_GAS_FOLD_REFUTED for CAISO would raise the
    2019-21 targets by +5.5 / +3.9 / +2.4 TWh. That is an owner decision; propose it with before/after, never flip
    it silently;
  - BTM / CHP accounting;
  - demand vintage.
- Only a measured-input defect is a lever.
- DO NOT re-test R/G cells:
  - the export route: caiso_p1_export_sink_seam, caiso_corridor_export_path, caiso_node_export_constraint;
  - the per-corridor firm-shape idea (censused in R-CAISO-6, ±130 MW);
  - raising caiso_ra_min_load_frac (rule 23).
- The 2019-20 hub-price STOP stands.

OBJECT 2 — the 2022 LCT area rows (routed by R-CAISO-6).
- Final 2022 LCT gives LA Basin 18,929 and SD-IV 4,580 MW peak_load (Table 3.3-74 / 3.3-83). Landing them arms
  caiso_per_year_import_caps in the keeper's 2022 leg: the SD cap becomes 587 MW vs the static 1,436.
- Owner decision: put the before/after zero-LP census to the owner first. If ruled in, re-solve 2022 (one shard)
  and recompose the keeper span.

OBJECT 3 — C4 2025 margin.
- Nothing is armed for it. Report whether Objects 1-2 move it, at full magnitude.

HARD RULES: CLAUDE.md binding, especially 1, 13, 14, 19, 21, 23, 25, 27, 28, 29(b)/(c), 30-36.
- The parent never solves (rule 32(a)). One shard per year (rule 36), full bundle pushed (rule 34(a)); pin a full
  SHA. Template: docs/handoffs/r-caiso-6/shard-prompt.md.
- Per-year legs are gitignored in CONTENTS form (results/calibration/<legs>_20*/**); a directory-form pattern
  blocks the shard's negation.
- G-DRIFT: scripts/probes/_rcaiso6_gdrift_identity.py (edit PIN / BUNDLES).
- Parent seam:
  - compose with scripts/probes/rcaiso_compose_span.py --require ...;
  - legitimacy_diagnostics.py --json-out;
  - dashboard_add_run.py --no-prune with a DISTINCT label;
  - attestation via scripts/gen_rcaiso6_attestation.py as a model;
  - re-register, stamp_touchpoint_holdout.py for folds;
  - prune_iso_runs.py (--force-uncite only for superseded runs);
  - build_status.py --iso CAISO, audit_keepers.py --iso CAISO.
- A NOT-YET promotion withdraws the complete marker: surface that trade to the owner, never take it in-session.
- End of session:
  - ask the promotion question;
  - archive shards;
  - report leftover shard branches for the owner to delete. Known leftovers today:
    claude/r-caiso-6-O2-2019/2020/2021 and claude/r-caiso-5-XE-2019/2020/2021.
