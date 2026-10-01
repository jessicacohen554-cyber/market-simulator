SHARD r-caiso-13-A-{Y} — ONE-YEAR CAISO BACKCAST SOLVE ({Y}): KEEPER RECIPE + caiso_eia930_clock_repair=true (lane R-CAISO-13)
DATA PROFILE: caiso
MODEL: Opus or Fable

You are a SHARD. You solve ONE year, push its full bundle to your own branch, report numbers, and stop.
"A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE."

FIRST ACTION (exactly this, before anything else):
  git fetch origin {SHA} || git fetch origin claude/r-caiso-13; git checkout --detach {SHA}
Then HARD STOP 1: `git rev-parse HEAD` must print {SHA}. Never rebase, never `git pull`, never "sync", never force-push.

PRECOMMIT: docs/records/caiso/r-caiso-13/PRECOMMIT-r-caiso-13-2026-09-28.md (read §2 and §4 only).

SETUP (in this order):
  pip install -r requirements.txt && pip install -e .     (only if imports fail; if PyYAML refuses to uninstall add --ignore-installed PyYAML; if zoneinfo cannot find US/Pacific, `pip install tzdata`)
  python3 scripts/hydrate_data.py --profile caiso        (if it refuses because the clone is not partial, continue)
  PYTHONPATH=. python3 scripts/data/curate_capacity_deliverability.py --isos CAISO     (MANDATORY)

HARD STOPS — check each; if any fails, STOP, do not push, report which one:
2. Before solving: `sha256sum data/raw/capacity-deliverability/caiso/caiso.csv data/raw/campd-unit-outages-CAISO.csv data/raw/_processed-legacy/plant_emission_rates_v2.parquet data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet data/raw/_validation-source/caiso_offer_curve_measured.json` must print, in order:
   e58594ae05df0c520d37cfc8aa89e0f4330937f612ff2be7a28b653dfa1506dc
   cf156483e08dcd701bd89898ca14670d3c797eb09d9ad30efc7f51cb381390b5
   15d634654db8f5c6b8cc30d614a702a1800904ffb086a46afcba444d04bdf7b7
   b44acc27df23216811d7e29cf52ebebf61bd81dffab3e5497bff7b7425a46a5d
   a5ab4c925a1291820d63c33c3777fa57982d506e2c66d7275fedaafda49182e5
   Also: `python3 -c "from market_sim.config.constants import ST_GAS_PEAK_MEASURED_HR_MULT_BY_ISO as M; print(M)"` must print {'CAISO': 1.154}.
   Also: `python3 -c "from market_sim.config.iso_configs import get_iso_config as g; from market_sim.model.transmission import apply_caiso_local_import_limits as f; print({(l.from_zone,l.to_zone):l.ttc_mw for l in f(g('CAISO'),'CAISO',{Y},sd_floor_static=True).links}[('SP15_rest','SDGE')])"`
   must print {SDCAP} (2019–2023: 1436.0; 2024: 2074.0; 2025: 2071.0).
   Also (the arm is live): `PYTHONPATH=src python3 -c "import numpy as np; from market_sim.data.eia930 import frames as F; from market_sim.data.eia930.demand import _load_caiso_supply_consistent_demand as SC; a=F._eia_hourly_frame_filled('CISO',{Y}).copy(); da=SC({Y}); F.set_caiso_eia930_clock_repair(True); b=F._eia_hourly_frame_filled('CISO',{Y}); db=SC({Y}); ne=lambda c: int((~np.isclose(a[c].to_numpy(float),b[c].to_numpy(float),equal_nan=True)).sum()); print(ne('Demand'), ne('NG: SUN'), int((np.abs(da-db)>1e-6).sum()))"`
   must print EXACTLY (per year): 2019/2020/2021 -> `0 0 0`; 2022 -> `4776 0 0`; 2023 -> `8752 1140 1465`; 2024 -> `8758 7666 8755`; 2025 -> `8049 6943 8051`.
   (2019-2022 are EXPECTED to be inert in the LP — solve them anyway; that is not a stop.)
3. After the solve, results/calibration/rcaiso13_A_{Y}/run_config.json must show:
   scenario_config: caiso_eia930_clock_repair=true (THE ARM — if it reads false or is absent, STOP), caiso_tac_shares_standard_time=true, caiso_supply_consistent_demand=true,
   caiso_ra_bridge_startup_aware=false, caiso_ra_mustoffer=true,
   caiso_ra_startup_bridge=true, caiso_ra_bridge_decommit=true, caiso_ra_min_load_frac=0.26,
   caiso_import_cap_floor_static=true, caiso_intertie_partial_year_measured=true,
   caiso_st_gas_peak_measured=true, caiso_per_hub_intertie=true, caiso_perhub_firm_base=true,
   caiso_import_gas_coupling_ladder_only=true, caiso_intertie_gap_fill_measured_dam=true,
   cc_eia923_identity_emission_basis=true, capacity_deliverability_limits=true, caiso_per_year_import_caps=true,
   mode="backcast", iso="CAISO"; calibration_flags.offer_curve_overrides == {} and offer_curve_deltas == {};
   calibration_flags.coal_prb_sigmoid_overrides.caiso_eia930_clock_repair == true (if that dict carries it).
   hourly/p0_dispatch_{Y}.parquet must exist (from --persist-p0-dispatch).
   The solve log must contain "firm import blocks shaped".

SOLVE (exactly this, unmodified, IN THE FOREGROUND — never nohup / & / run_in_background; never pass --no-container-preflight):
  python3 scripts/replay_keeper.py results/calibration/{SRC} --years {Y} \
    --set caiso_eia930_clock_repair=true --persist-p0-dispatch \
    --out-dir results/calibration/rcaiso13_A_{Y} \
    --note "R-CAISO-13 A {Y}: keeper recipe + caiso_eia930_clock_repair=true (PRECOMMIT-r-caiso-13-2026-09-28)"
  Budget: ~25 min. If it approaches 40 min with no bundle, stop and report.

PUSH (rule 34(a) — plain git add, NEVER `git add -f`, NEVER `git add -A` / `git add .`):
  git checkout -b claude/r-caiso-13-A-{Y}
  printf '\n!results/calibration/rcaiso13_A_{Y}/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/rcaiso13_A_{Y}
  git status --short   # must show NOTHING staged outside .gitignore and results/calibration/rcaiso13_A_{Y}/
  ls results/calibration/rcaiso13_A_{Y}/dispatch/{Y}_P1.parquet   # must exist and be staged
  git commit -m "r-caiso-13-A-{Y}: one-year bundle (R-CAISO-13)" && git push -u origin claude/r-caiso-13-A-{Y}
  (If the push fails with HTTP 408/500: `git config http.version HTTP/1.1` and retry. If a pre-push hook
  blocks on lint of files you did not touch, report it and stop — do not reformat anything.)
  Then verify: `git ls-remote origin claude/r-caiso-13-A-{Y}` must print your commit sha, and
  `git ls-tree -r HEAD -- results/calibration/rcaiso13_A_{Y} | wc -l` must be > 10.

FORBIDDEN, by name: `git add -A`, `git add .`, `git add -f`; scripts/dashboard_add_run.py, build_manifest.py,
build_status.py, prune_iso_runs.py, anything under frontend/data/backcast/**; ANY edit under src/ or scripts/
(except running them); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.

REPORT in your final message, in numbers:
- HEAD sha; the pushed commit sha (FULL 40 chars); the ls-tree file count
- the `container preflight:` and `memory peak:` log lines; wall time of the solve
- hard-stop 3 values as read from run_config.json
- the D-2 row for ra_mustoffer_bridge in legitimacy_diagnostics.json (forced TWh and forced share of CC_REGULAR), if present
- per-class annual TWh (model) from hourly/class_hourly_{Y}.parquet, pass P1: CC_REGULAR, CT_PEAKER, import (and per corridor WECC_PNW / WECC_DSW if the file splits them), ST_GAS, CC_CHP, hydro
- from hourly/system_{Y}.parquet, pass P1: SDGE annual slack (unserved) MWh, SDGE mean price, and the count of hours with price(SDGE) − price(SP15_rest) > 0.01
- whether the log contains "per-hub WECC intertie" for this year
- the SP15_rest mean price over hours h17-22 and h8-16 (hour = hour-of-year % 24), and SDGE / LA_BASIN / NP15 annual mean price
- any WARNING about a fallback / missing input
- the SOLAR centroid: from hourly/class_hourly_{Y}.parquet (klass == "solar", pass P1), sum(mw * (hour%24 + 0.5)) / sum(mw) over Jun-Sep (hours 3624-6551)
- from hourly/storage_{Y}.parquet (tech li_ion, pass P1): annual discharge and charge TWh
