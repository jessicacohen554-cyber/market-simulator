SHARD r-caiso-3-{ARM}-{Y} — ONE-YEAR CAISO BACKCAST SOLVE ({Y}): KEEPER RECIPE + ARM {ARM} (lane R-CAISO-3)
DATA PROFILE: caiso
MODEL: Opus or Fable

You are a SHARD. You solve ONE year, push its full bundle to your own branch, report numbers, and stop.
"A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE."

FIRST ACTION (exactly this, before anything else):
  git fetch origin {SHA} || git fetch --unshallow origin main; git checkout --detach {SHA}
Then HARD STOP 1: `git rev-parse HEAD` must print {SHA}. Never rebase, never `git pull`, never "sync", never force-push.

PRECOMMIT: docs/handoffs/r-caiso-3/PRECOMMIT-r-caiso-3-2026-09-25.md (read §2 and §4 only).

HARD STOPS — check each; if any fails, STOP, do not push, report which one:
2. Before solving: `sha256sum data/raw/campd-unit-outages-shortgas-CAISO.csv data/raw/_processed-legacy/campd_cc_heat_rates_CAISO.csv data/raw/gas-prices/eia_delivered_gas_electric_power_by_state_monthly_2018-2026.csv` must print
   cca2338fa7cbd9f15ad13a3a3e761d78ec8816788bea800ddddcdc275a25d5d9, 0d5e457c77eb1d2439c10ad7504c4875bfca4c5557cc7337d066a9988e7bfb38, 1565a9a9eeb76c3bb56e8e18553a8aceaed5eb0e26a2c1595e2a0abcf03ebf30.
3. After the solve, results/calibration/{OUT}/run_config.json scenario_config must show ALL of:
   eia860_vintage_tracks_solve_year=true, measured_cc_heat_rates=true, measured_ct_heat_rates=true,
   measured_st_heat_rates=true, measured_chp_heat_rates=true, egrid_family_heat_rates=true,
   unit_outage_short_windows=true, unit_outage_short_windows_gas=true, unit_partial_outage_windows=true,
   caiso_import_gas_coupling=true, caiso_per_hub_intertie=true, caiso_perhub_firm_base=true,
   caiso_dam_outages=false, gas_flow_date_year_start_package=true, mode="backcast", iso="CAISO",
   {SIG}
   and calibration_flags.offer_curve_overrides == {} and offer_curve_deltas == {}.
   Report resolved_inputs.campd_unit_outages.sha256 (must be cf156483e08dcd701bd89898ca14670d3c797eb09d9ad30efc7f51cb381390b5).

SETUP (in this order):
  pip install -r requirements.txt && pip install -e .     (only if imports fail; if PyYAML refuses to uninstall add --ignore-installed PyYAML)
  python3 scripts/hydrate_data.py --profile caiso
  PYTHONPATH=. python3 scripts/data/curate_capacity_deliverability.py --isos CAISO

SOLVE (exactly this, unmodified; never pass --no-container-preflight):
  python3 scripts/replay_keeper.py results/calibration/rcaiso2_ccid_span --years {Y} \
    --out-dir results/calibration/{OUT} {SETS} \
    --note "R-CAISO-3 {ARM} {Y}: keeper recipe + {ARMDESC} (PRECOMMIT-r-caiso-3-2026-09-25 §4)"
  Budget: ~25 min. If it approaches 40 min with no bundle, stop and report.

PUSH (rule 34(a) — plain git add, NEVER `git add -f`, NEVER `git add -A` / `git add .`):
  git checkout -b claude/r-caiso-3-{ARM}-{Y}
  printf '\n!results/calibration/{OUT}/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/{OUT}
  git status --short   # must show NOTHING staged outside .gitignore and results/calibration/{OUT}/
  ls results/calibration/{OUT}/dispatch/{Y}_P1.parquet   # must exist and be staged
  git commit -m "r-caiso-3-{ARM}-{Y}: one-year bundle (R-CAISO-3)" && git push -u origin claude/r-caiso-3-{ARM}-{Y}
  (If git push fails with HTTP 408/500: `git config http.version HTTP/1.1` and retry.)
  Then verify: `git ls-remote origin claude/r-caiso-3-{ARM}-{Y}` must print your commit sha, and
  `git ls-tree -r HEAD -- results/calibration/{OUT} | wc -l` must be > 10.

FORBIDDEN, by name: `git add -A`, `git add .`, `git add -f`; scripts/dashboard_add_run.py, build_manifest.py,
build_status.py, prune_iso_runs.py, anything under frontend/data/backcast/**; ANY edit under src/ or scripts/
(except running them); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.

REPORT in your final message, in numbers:
- HEAD sha; the pushed commit sha; the ls-tree file count
- the `container preflight:` and `memory peak:` log lines; wall time of the solve
- hard-stop 3 values as read from run_config.json
- per-class annual TWh (model) from the bundle (hourly/class_hourly_{Y}.parquet, pass P1: CC_REGULAR, CT_PEAKER, import, ST_GAS, CC_CHP), and January + February import TWh
- load-weighted mean P1 price over the load zones if printed
- any WARNING about a fallback / missing input
