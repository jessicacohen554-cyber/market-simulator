SHARD r-caiso-4-{ARM}-{Y} — ONE-YEAR CAISO BACKCAST SOLVE ({Y}): KEEPER RECIPE + ARM {ARM} (lane R-CAISO-4)
DATA PROFILE: caiso
MODEL: Opus or Fable

You are a SHARD. You solve ONE year, push its full bundle to your own branch, report numbers, and stop.
"A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE."

FIRST ACTION (exactly this, before anything else):
  git fetch origin 9a1980bc38529de8049cf99f6094868d80a3ce93 || git fetch --unshallow origin main || git fetch origin claude/caiso-margins-pastoria-lgucsd; git checkout --detach 9a1980bc38529de8049cf99f6094868d80a3ce93
Then HARD STOP 1: `git rev-parse HEAD` must print 9a1980bc38529de8049cf99f6094868d80a3ce93. Never rebase, never `git pull`, never "sync", never force-push.

PRECOMMIT: docs/handoffs/r-caiso-4/PRECOMMIT-r-caiso-4-2026-09-26.md (read §1, §2 and §6 only).

SETUP (in this order):
  pip install -r requirements.txt && pip install -e .     (only if imports fail; if PyYAML refuses to uninstall add --ignore-installed PyYAML)
  python3 scripts/hydrate_data.py --profile caiso        (if it refuses because the clone is not partial, continue: blobs fetch on demand)
  PYTHONPATH=. python3 scripts/data/curate_capacity_deliverability.py --isos CAISO

HARD STOPS — check each; if any fails, STOP, do not push, report which one:
2. Before solving: `sha256sum data/raw/campd-unit-outages-shortgas-CAISO.csv data/raw/_processed-legacy/campd_cc_heat_rates_CAISO.csv data/raw/gas-prices/eia_delivered_gas_electric_power_by_state_monthly_2018-2026.csv data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO_gapfill_dam.parquet data/raw/_processed-legacy/plant_emission_rates_v2.parquet` must print, in order:
   cca2338fa7cbd9f15ad13a3a3e761d78ec8816788bea800ddddcdc275a25d5d9
   ab976786a7190694f324cf057b88507332b6502519e1454e4f79ef674a8f8070
   1565a9a9eeb76c3bb56e8e18553a8aceaed5eb0e26a2c1595e2a0abcf03ebf30
   b44acc27df23216811d7e29cf52ebebf61bd81dffab3e5497bff7b7425a46a5d
   22f79da79481864ec4677d46e62eac80cbbc895f2d4a978b9a2aa94821cb9fd7
   15d634654db8f5c6b8cc30d614a702a1800904ffb086a46afcba444d04bdf7b7
3. After the solve, results/calibration/{OUT}/run_config.json scenario_config must show ALL of:
   eia860_vintage_tracks_solve_year=true, measured_cc_heat_rates=true, measured_ct_heat_rates=true,
   measured_st_heat_rates=true, measured_chp_heat_rates=true, egrid_family_heat_rates=true,
   unit_outage_short_windows=true, unit_outage_short_windows_gas=true, unit_partial_outage_windows=true,
   caiso_import_gas_coupling=true, caiso_import_gas_coupling_ladder_only=true,
   caiso_intertie_gap_fill_measured_gas=true, caiso_per_hub_intertie=true, caiso_perhub_firm_base=true,
   use_plant_emission_rates_v2=true, caiso_dam_outages=false, gas_flow_date_year_start_package=true,
   mode="backcast", iso="CAISO",
   {SIG}
   and calibration_flags.offer_curve_overrides == {} and offer_curve_deltas == {}.
   Report resolved_inputs.campd_unit_outages.sha256 (must be cf156483e08dcd701bd89898ca14670d3c797eb09d9ad30efc7f51cb381390b5).

SOLVE (exactly this, unmodified; never pass --no-container-preflight):
  python3 scripts/replay_keeper.py results/calibration/rcaiso3_ABC_span --years {Y} \
    --out-dir results/calibration/{OUT} {SETS} \
    --note "R-CAISO-4 {ARM} {Y}: keeper recipe + {ARMDESC} (PRECOMMIT-r-caiso-4-2026-09-26 §6)"
  Budget: ~25 min. If it approaches 40 min with no bundle, stop and report.

PUSH (rule 34(a) — plain git add, NEVER `git add -f`, NEVER `git add -A` / `git add .`):
  git checkout -b claude/r-caiso-4-{ARM}-{Y}
  printf '\n!results/calibration/{OUT}/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/{OUT}
  git status --short   # must show NOTHING staged outside .gitignore and results/calibration/{OUT}/
  ls results/calibration/{OUT}/dispatch/{Y}_P1.parquet   # must exist and be staged
  git commit -m "r-caiso-4-{ARM}-{Y}: one-year bundle (R-CAISO-4)" && git push -u origin claude/r-caiso-4-{ARM}-{Y}
  (If the push fails with HTTP 408/500: `git config http.version HTTP/1.1` and retry. If a pre-push hook
  blocks on lint of files you did not touch, report it and stop — do not reformat anything.)
  Then verify: `git ls-remote origin claude/r-caiso-4-{ARM}-{Y}` must print your commit sha, and
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
