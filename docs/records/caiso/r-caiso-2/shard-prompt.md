SHARD r-caiso-2-{Y} — ONE-YEAR CAISO BACKCAST SOLVE ({Y}): KEEPER RECIPE + CC GROSS-NET IDENTITY REPAIR (lane R-CAISO-2)
DATA PROFILE: caiso
MODEL: Opus or Fable

You are a SHARD. You solve ONE year, push its full bundle to your own branch, report numbers, and stop.
"A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE."

PRECOMMIT: docs/handoffs/r-caiso-2/PRECOMMIT-r-caiso-2-2026-09-25.md (read §2 and §4 only).

HARD STOPS — check each; if any fails, STOP, do not push, report which one:
1. `git rev-parse HEAD` must equal {SHA}. Never rebase, never `git pull`, never "sync", never force-push.
2. After the solve, results/calibration/rcaiso2_ccid_{Y}/run_config.json scenario_config must show ALL of:
   eia860_vintage_tracks_solve_year=true, measured_st_heat_rates=true, measured_cc_heat_rates=true,
   measured_ct_heat_rates=true, measured_chp_heat_rates=true, egrid_family_heat_rates=true,
   unit_outage_short_windows=true, unit_outage_short_windows_gas=true, unit_partial_outage_windows=true,
   caiso_dam_outages=false, gas_flow_date_year_start_package=true, mode="backcast", iso="CAISO",
   and calibration_flags.offer_curve_overrides == {} and offer_curve_deltas == {}.
   Report run_config.json resolved_inputs.campd_unit_outages.sha256 (must be cf156483e08dcd701bd89898ca14670d3c797eb09d9ad30efc7f51cb381390b5).
3. Before solving: `sha256sum data/raw/campd-unit-outages-shortgas-CAISO.csv data/raw/_processed-legacy/campd_cc_heat_rates_CAISO.csv` must print
   {SG_SHA} and {CC_SHA} respectively.

SETUP (in this order):
  pip install -r requirements.txt && pip install -e .     (if imports fail)
  python3 scripts/hydrate_data.py --profile caiso
  PYTHONPATH=. python3 scripts/data/curate_capacity_deliverability.py --isos CAISO
  (the keeper arms capacity_deliverability_limits, whose curated partition hydrate does not build)

SOLVE (exactly this, unmodified; never pass --no-container-preflight):
  python3 scripts/replay_keeper.py results/calibration/rcaiso_inputs_span --years {Y} \
    --out-dir results/calibration/rcaiso2_ccid_{Y} \
    --note "R-CAISO-2 {Y}: keeper recipe + CC gross-net identity repair (PRECOMMIT-r-caiso-2-2026-09-25 §4)"
  (NO --set of any kind. The arm is the re-derived CC heat-rate artifact already on the pinned SHA.)
  Budget: ~20 min. If it approaches 40 min with no bundle, stop and report.

PUSH (rule 34(a) — plain git add, NEVER `git add -f`, NEVER `git add -A` / `git add .`):
  git checkout -b claude/r-caiso-2-{Y}
  printf '\n!results/calibration/rcaiso2_ccid_{Y}/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/rcaiso2_ccid_{Y}
  git status --short   # must show NOTHING outside .gitignore and results/calibration/rcaiso2_ccid_{Y}/
  ls results/calibration/rcaiso2_ccid_{Y}/dispatch/{Y}_P1.parquet   # must exist and be staged
  git commit -m "r-caiso-2-{Y}: one-year bundle (R-CAISO-2)" && git push -u origin claude/r-caiso-2-{Y}
  (If git push fails with HTTP 408/500: `git config http.version HTTP/1.1` and retry.)

FORBIDDEN, by name: `git add -A`, `git add .`, `git add -f`; scripts/dashboard_add_run.py, build_manifest.py,
build_status.py, prune_iso_runs.py, anything under frontend/data/backcast/**; ANY edit under src/ or scripts/
(except running them); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.

REPORT in your final message, in numbers:
- HEAD sha; the pushed commit sha; `git ls-tree -r <pushed sha> -- results/calibration/rcaiso2_ccid_{Y} | wc -l`
- the `container preflight:` and `memory peak:` log lines; wall time of the solve
- hard-stop 2 values as read from run_config.json; resolved EIA-860 source for {Y} if logged
- per-class annual TWh (model) from the bundle, and mean LMP by zone if printed
- any WARNING about a fallback / missing input
