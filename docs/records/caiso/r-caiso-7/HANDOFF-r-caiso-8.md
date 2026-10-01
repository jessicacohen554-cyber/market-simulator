SESSION R-CAISO-8 — CAISO: (1) 2021 partial-year measured intertie pricing; (2) the SD import-limit construction; (3) the CT_PEAKER peak-band artifact/registry mismatch
DATA PROFILE: caiso
MODEL: Opus or Fable

FIRST: archive the parent session session_01PNnWhfDbPpewfKwWnCcvry (R-CAISO-7) with mcp__Claude_Code_Remote__archive_session once its PR (branch claude/r-caiso-7) reads MERGED (check with the GitHub MCP). If it is not merged, do not archive; say so in your first report.

STATE (2026-09-27):
- Keeper `2026-09-26-caiso-r5-pastoria-co2` (bundle rcaiso5_XE_span, 2022-2025) is CALIBRATED.
  - Single ledgered C3c 2024.
  - C4 2025 0.2987 vs <=0.30 (thin).
- 2019-21 are folded as `2026-09-27-caiso-r6-malin-fold`, NOT-YET, reported only (rule 30(c)).
- R-CAISO-7 was zero LP; the keeper is unchanged.

READ FIRST:
- docs/records/caiso/r-caiso-7/RESULT-r-caiso-7-2026-09-27.md
- results/calibration/_rcaiso7/object1_census.json (probe: scripts/probes/_rcaiso7_dsw_import_census.py)
- docs/records/caiso/r-caiso-6/RESULT-r-caiso-6-2026-09-27.md
- docs/mechanism-testing-matrix.md §5.2
- docs/codebase-site/data/mechanism-matrix/CAISO.js (import_hub_pricing and reference_price_interface notes)

FINDING TO BUILD ON:
- The 2019-21 CC_REGULAR excess (+20 / +25 / +19 TWh) is the DSW import. Model DSW is 20.9 / 17.3 / 15.8 TWh vs EIA-930 44.7 / 41.9 / 40.9, flat across hours and months.
- The cause is no measured intertie hub price in those years.
- In 2021 the hub prints 5,976 of 8,760 h (May-Dec). But:
  - envelopes.measured_import_hub_prices drops the whole year (>25 % gap), so every tranche stays on the static ladder;
  - measured_intertie_hub_price_raw still ARMS ~2.75 GW of DSW clean-depth tranches, which sit on the $180 placeholder and dispatch 0.
- First-order sizing: pricing the printed hours adds up to +24.2 TWh of DSW imports (no price feedback).

OBJECT 1 — the 2021 lever (owner standing instruction: "If structural integrity improves but gates regress that may still be a keeper").
- Add a default-off ScenarioConfig flag, e.g. caiso_intertie_partial_year_measured:
  - each hub is priced at its measured print in printed hours;
  - the static ladder applies only in unprinted hours, per hour, in the per-hub injector;
  - arming and pricing share one gate.
- Constraints:
  - zero new numeric parameters (rules 21/24);
  - matrix row + a cell in EVERY ISO shard in the same PR (rule 28(c));
  - tests: trivial case first; 2022-25 byte-identical.
- G-DRIFT (scripts/probes/_rcaiso6_gdrift_identity.py; edit PIN / BUNDLES) must show 2019, 2020 and 2022-25 byte-identical on every LP-visible array with the flag ON, and only 2021 moving.
- Write the PRECOMMIT with pre-registered directions before any shard:
  - 2021 imports up and CC_REGULAR down;
  - PNW_midC down;
  - C3a 2021 price direction stated.
- Solve: the keeper recipe + the flag, one shard per year (rule 36), 2019-2025 (all 7; rules 34(c) / 35(c)), full bundle pushed (rule 34(a)), SHA pinned.
  - Template: docs/records/caiso/r-caiso-6/shard-prompt.md.
  - Tell shards to run the solve in the FOREGROUND.
  - Per-year legs gitignored in CONTENTS form (results/calibration/<legs>_20*/**).
- Parent seam:
  - compose with scripts/probes/rcaiso_compose_span.py --require ...;
  - legitimacy_diagnostics.py --json-out;
  - attestation (model: scripts/gen_rcaiso6_attestation.py);
  - dashboard_add_run.py --no-prune with a DISTINCT label;
  - stamp_touchpoint_holdout.py for the fold;
  - on promotion: prune_iso_runs.py, build_status.py --iso CAISO, audit_keepers.py --iso CAISO, re-key calibration-complete.json.
- A NOT-YET promotion withdraws the complete marker: surface that trade to the owner, never take it in-session.
- Report 2021 C1 / C3a / C3b / C4 at full magnitude either way.

OBJECT 2 — the SD import limit (zero LP first).
- `caiso_per_year_import_caps` applies the LCT `peak_load − requirement` (a 1-in-10 N-1-1 PLANNING-case capability) as an all-hours TTC.
- Evidence, 2019 leg (386 MW cap): 7,461 binding h, SDGE mean $388.8, 419,683 MWh unserved.
- The 2022 LCT rows (587 MW) are NOT landed; R-CAISO-7 recommends against landing them under this construction.
- Find a measured OPERATING SD import limit (SWPL / Sunrise / IV nomogram, CAISO OASIS transmission interface limits, or the LCT report's own non-contingency import figures), and propose it as the rule-14 reconciled input.
- Census it zero-LP against 2019-21 and 2023-25 before any solve.
- Owner decision before arming. It touches the keeper's 2023-25 caps (1,436 / 2,074 / 2,071), which do not bind much today.

OBJECT 3 — tests/unit/data/test_caiso_st_gas_peak_measured.py fails.
- caiso_offer_curve_measured.json CT_PEAKER peak = 1.154 vs ST_GAS_PEAK_MEASURED_HR_MULT_BY_ISO["CAISO"] = 1.166.
- Find which side moved (git log on a full-history fetch of both files). Fix the stale side only if the data change is cited (rule 23); report if it moves the keeper's recipe.

OWNER DECISIONS STILL OPEN (from R-CAISO-7):
- EIA930_GAS_FOLD_REFUTED for CAISO: 2019-21 C1 misses ≈ +14.9 / +20.9 / +17.0 TWh after the flip vs +20.4 / +24.8 / +19.4 now; 2022-25 unchanged. Propose, never flip silently.

DO NOT re-test (R/G cells or censused):
- the export route: caiso_p1_export_sink_seam, caiso_corridor_export_path, caiso_node_export_constraint;
- the per-corridor firm-shape idea;
- raising caiso_ra_min_load_frac;
- the forward reference-price formula as a 2019-21 backcast price (it rides the forward Henry Hub; censused in R-CAISO-7).
- The 2019-20 hub-price STOP stands.

NOTE: the Fast test tier on main has ~25 pre-existing failures. Not yours unless one is CAISO-scoped and in your diff.

HARD RULES: CLAUDE.md binding, especially 1, 13, 14, 19, 21, 23, 24, 25, 27, 28, 29(b)/(c), 30-36.
- The parent never solves (rule 32(a)).
- End of session:
  - ask the promotion question;
  - archive shards;
  - report leftover shard branches for the owner to delete. Known leftovers today: claude/r-caiso-6, claude/r-caiso-6-O2-2019/2020/2021, claude/r-caiso-7.
