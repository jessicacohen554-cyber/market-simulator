SHARD r-caiso-6-O2-{Y} — ONE-YEAR CAISO BACKCAST SOLVE ({Y}): XE KEEPER RECIPE + OBJECT-2 INTAKE (lane R-CAISO-6)
DATA PROFILE: caiso
MODEL: Opus or Fable

You are a SHARD. You solve ONE year, push its full bundle to your own branch, report numbers, and stop.
"A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE."

FIRST ACTION (exactly this, before anything else):
  git fetch origin {SHA} || git fetch origin claude/r-caiso-6; git checkout --detach {SHA}
Then HARD STOP 1: `git rev-parse HEAD` must print {SHA}. Never rebase, never `git pull`, never "sync", never force-push.

PRECOMMIT: docs/records/caiso/r-caiso-6/PRECOMMIT-r-caiso-6-2026-09-27.md (read §2 and §4 only).

SETUP (in this order):
  pip install -r requirements.txt && pip install -e .     (only if imports fail; if PyYAML refuses to uninstall add --ignore-installed PyYAML)
  python3 scripts/hydrate_data.py --profile caiso        (if it refuses because the clone is not partial, continue)
  PYTHONPATH=. python3 scripts/data/curate_capacity_deliverability.py --isos CAISO     (MANDATORY: the Malin rows reach the solve only through this clean partition)

HARD STOPS — check each; if any fails, STOP, do not push, report which one:
2. Before solving: `sha256sum data/raw/capacity-deliverability/caiso/caiso.csv data/raw/campd-unit-outages-CAISO.csv data/raw/_processed-legacy/plant_emission_rates_v2.parquet` must print, in order:
   e58594ae05df0c520d37cfc8aa89e0f4330937f612ff2be7a28b653dfa1506dc
   cf156483e08dcd701bd89898ca14670d3c797eb09d9ad30efc7f51cb381390b5
   15d634654db8f5c6b8cc30d614a702a1800904ffb086a46afcba444d04bdf7b7
3. After the solve, results/calibration/rcaiso6_O2_{Y}/run_config.json must show:
   resolved_inputs.seam_import_cap.by_year."{Y}".cap_mw == {CAP} and source == "mic_partition";
   scenario_config: unit_outage_extract_basis_share=true, unit_outage_lp_capacity_basis=false,
   cc_eia923_identity_emission_basis=true, capacity_deliverability_limits=true, caiso_per_year_import_caps=true,
   caiso_firm_import_shape=true, caiso_perhub_firm_base=true, mode="backcast", iso="CAISO";
   calibration_flags.offer_curve_overrides == {} and offer_curve_deltas == {}.
   The solve log must contain "firm import blocks shaped".

SOLVE (exactly this, unmodified; never pass --no-container-preflight):
  python3 scripts/replay_keeper.py results/calibration/rcaiso5_XE_tp_2019_2021 --years {Y} \
    --out-dir results/calibration/rcaiso6_O2_{Y} \
    --note "R-CAISO-6 O2 {Y}: XE keeper recipe + 2019-21 firm rows + MIC Malin repair (PRECOMMIT-r-caiso-6-2026-09-27 §4)"
  Budget: ~25 min. If it approaches 40 min with no bundle, stop and report.

PUSH (rule 34(a) — plain git add, NEVER `git add -f`, NEVER `git add -A` / `git add .`):
  git checkout -b claude/r-caiso-6-O2-{Y}
  printf '\n!results/calibration/rcaiso6_O2_{Y}/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/rcaiso6_O2_{Y}
  git status --short   # must show NOTHING staged outside .gitignore and results/calibration/rcaiso6_O2_{Y}/
  ls results/calibration/rcaiso6_O2_{Y}/dispatch/{Y}_P1.parquet   # must exist and be staged
  git commit -m "r-caiso-6-O2-{Y}: one-year bundle (R-CAISO-6)" && git push -u origin claude/r-caiso-6-O2-{Y}
  (If the push fails with HTTP 408/500: `git config http.version HTTP/1.1` and retry. If a pre-push hook
  blocks on lint of files you did not touch, report it and stop — do not reformat anything.)
  Then verify: `git ls-remote origin claude/r-caiso-6-O2-{Y}` must print your commit sha, and
  `git ls-tree -r HEAD -- results/calibration/rcaiso6_O2_{Y} | wc -l` must be > 10.

FORBIDDEN, by name: `git add -A`, `git add .`, `git add -f`; scripts/dashboard_add_run.py, build_manifest.py,
build_status.py, prune_iso_runs.py, anything under frontend/data/backcast/**; ANY edit under src/ or scripts/
(except running them); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.

REPORT in your final message, in numbers:
- HEAD sha; the pushed commit sha (FULL 40 chars); the ls-tree file count
- the `container preflight:` and `memory peak:` log lines; wall time of the solve
- hard-stop 3 values as read from run_config.json
- per-class annual TWh (model) from hourly/class_hourly_{Y}.parquet, pass P1: CC_REGULAR, CT_PEAKER, import, ST_GAS, CC_CHP, hydro
- any WARNING about a fallback / missing input
