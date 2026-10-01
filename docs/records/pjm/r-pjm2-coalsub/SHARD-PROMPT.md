SHARD r-pjm2cs-{Y} — ONE-YEAR PJM BACKCAST SOLVE ({Y}) — PJM KEEPER RECIPE (RGGI + corrected inputs) ON COAL-SUB HEAD (lane R-PJM2-CS)
DATA PROFILE: pjm
MODEL: Opus or Fable

You are a SHARD. You solve ONE year, push its full bundle to your own branch, report numbers, and stop.
"A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE."

PRECOMMIT: docs/handoffs/r-pjm2-coalsub/PRECOMMIT.md (read §2 and §6 only).

HARD STOPS — check each; if any fails, STOP, do not push, report which one:
1. `git rev-parse HEAD` must equal {SHA}. Never rebase, never `git pull`, never "sync", never force-push.
2. Before solving: `sha256sum data/raw/campd-unit-outages-PJM.csv` must start with 312a11b84778.
3. After the solve, results/calibration/rpjm2cs_{Y}/run_config.json must show, in scenario_config:
   mode="backcast", iso="PJM", eia860_vintage_tracks_solve_year=true, measured_ct_heat_rates=true,
   measured_coal_heat_rates=true, measured_st_heat_rates=true, measured_cc_heat_rates=true,
   measured_chp_heat_rates=true, pjm_rggi_allowance_pricing=true, pjm_da_virtual_bids=true;
   and calibration_flags.offer_curve_overrides must have NO "COAL" key and
   COAL_BIT == {committed 0.548, econ_high 1.2664, econ_low 0.6556, econ_low_share 0.55, peak 1.044};
   resolved_inputs.campd_unit_outages.sha256 must start with 312a11b84778.
4. The solve log must carry the line `PJM {Y}: partial-footprint carbon adder … (program RGGI, P $/t)` with
   P = {RGGI_P} and N > 0 generators.
5. No generator may carry plant_group "COAL" (COAL-SUB raises BareCoalClassError if one does — if you see
   that error, STOP and report it verbatim; do not work around it).

SETUP (in this order):
  pip install -r requirements.txt && pip install -e .     (if imports fail)
  python3 scripts/hydrate_data.py --profile pjm
  PYTHONPATH=. python3 scripts/data/curate_transfer_interface_limits.py --isos PJM
  PYTHONPATH=. python3 scripts/regenerate_clean.py ramp-capability
  PYTHONPATH=. python3 scripts/data/fetch_pjm_da_virtuals.py --years {Y} --feeds hrl_da_incs_decs
     (the keeper arms pjm_da_virtual_bids; its corpus is gitignored. A failed fetch is a HARD STOP.)
  If the solve raises FileNotFoundError naming "run scripts/regenerate_clean.py <datatype>", running
  exactly that regenerate command (it writes only gitignored data/clean) and re-launching is PERMITTED.
  Nothing else is.

SOLVE (exactly this, unmodified; never pass --no-container-preflight):
  python3 scripts/replay_keeper.py results/calibration/rpjm2_span --years {Y} \
    --out-dir results/calibration/rpjm2cs_{Y} \
    --note "R-PJM2-CS {Y}: PJM keeper recipe (h22 RGGI + corrected inputs) on COAL-SUB HEAD"
  (replay_keeper folds the recipe's legacy bare "COAL" offer key itself — do NOT edit the recipe.)
  Budget: ~30 min of solve. If it approaches 60 min with no bundle, stop and report.

PUSH (rule 34(a) — plain git add, NEVER `git add -f`, NEVER `git add -A` / `git add .`):
  git checkout -b claude/rpjm2cs-{Y}
  printf '\n!results/calibration/rpjm2cs_{Y}/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/rpjm2cs_{Y}
  git status --short   # must show NOTHING staged outside .gitignore and results/calibration/rpjm2cs_{Y}/
  ls results/calibration/rpjm2cs_{Y}/dispatch/{Y}_P1.parquet   # must exist and be staged
  git commit -m "rpjm2cs-{Y}: one-year bundle (R-PJM2-CS)" && git push -u origin claude/rpjm2cs-{Y}
  (If git push fails with HTTP 408/500: `git config http.version HTTP/1.1` and retry.)

FORBIDDEN, by name: `git add -A`, `git add .`, `git add -f`; scripts/dashboard_add_run.py, build_manifest.py,
build_status.py, prune_iso_runs.py, anything under frontend/data/backcast/**; ANY edit under src/ or scripts/
(running them is fine); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.

REPORT in your final message, in numbers:
- HEAD sha; the pushed commit sha; `git ls-tree -r <pushed sha> -- results/calibration/rpjm2cs_{Y} | wc -l`
- the `container preflight:` and `memory peak:` log lines; wall time of the solve
- hard-stop 3 values as read from run_config.json; the RGGI log line verbatim; the EIA-860 source for {Y} if logged
- per-class annual TWh (model) from the bundle (coal by subclass), and mean price by zone if printed
- any WARNING about a fallback / missing input
