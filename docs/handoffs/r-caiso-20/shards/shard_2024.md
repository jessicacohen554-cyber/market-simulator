SHARD r-caiso-20-A-2024 — ONE-YEAR CAISO BACKCAST SOLVE (2024): KEEPER RECIPE + caiso_dsw_overnight_clean_unprinted_arm=true (lane R-CAISO-20)
DATA PROFILE: caiso
MODEL: Opus or Fable

You are a SHARD. You solve ONE year, push its full bundle to your own branch, report numbers, and stop.
"A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE."

FIRST ACTION (exactly this, before anything else):
  git fetch origin cd5897987106193b34b84c5f4bb4a7c9bb1e4760 || git fetch origin main; git checkout --detach cd5897987106193b34b84c5f4bb4a7c9bb1e4760
Then HARD STOP 1: `git rev-parse HEAD` must print cd5897987106193b34b84c5f4bb4a7c9bb1e4760. Never rebase, never `git pull`, never "sync", never force-push.

PRECOMMIT: docs/handoffs/r-caiso-20/PRECOMMIT-r-caiso-20-2026-09-30.md (read §2, §3 and §5 only).

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
   Also (THE NEW ARM, R-CAISO-20): `PYTHONPATH=src python3 -c "import numpy as np; from market_sim.data.eia930.envelopes import measured_intertie_hub_unprinted_year_mask as M; from market_sim.config.interchange_config import CAISO_DSW_OVERNIGHT_CLEAN_DEPTH_BY_YEAR as D, CAISO_DSW_OVERNIGHT_CLEAN_DEPTH_STATIC as S; print(int((M('CAISO',2024,8760,'PALOVRDE',gap_fill_measured_dam=True)&(np.arange(8760)%24<=5)).sum()), D.get(2024,S))"`
   must print EXACTLY: 2019 -> `2190 6566.0`; 2020 -> `2190 7166.0`; 2021 -> `696 6187.0`; 2022 -> `0 6309.0`; 2023 -> `0 5870.0`; 2024 -> `0 6205.0`; 2025 -> `0 6487.0`.
   Also (THE PRICING ARM, R-CAISO-18, unchanged): `PYTHONPATH=src python3 -c "import numpy as np; from market_sim.data.eia930.envelopes import measured_import_hub_prices as M; p=M('CAISO',2024,8760,gap_fill_measured_gas=True,gap_fill_measured_dam=True,partial_year_measured=True,unprinted_year_measured_gas=True)['DSW_CCGT']; print(int(np.isfinite(p).sum()), round(float(np.nanmean(p)),2))"`
   must print EXACTLY: 2019 -> `8760 28.12`; 2020 -> `8760 30.03`; 2021 -> `8760 55.05`; 2022 -> `8760 82.95`; 2023 -> `8760 57.67`; 2024 -> `8760 33.34`; 2025 -> `8760 32.47`.
   Also: `sha256sum data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet data/raw/gas-prices/eia_delivered_gas_electric_power_by_state_monthly_2018-2026.csv` must print, in order:
   173b0b7ca93d7f99d877c1e5154d243129bb02fd8a9bb3d112c8cfd22c00da59
   1565a9a9eeb76c3bb56e8e18553a8aceaed5eb0e26a2c1595e2a0abcf03ebf30
   Also: `python3 -c "from market_sim.config.constants import ST_GAS_PEAK_MEASURED_HR_MULT_BY_ISO as M; print(M)"` must print {'CAISO': 1.154}.
   Also: `python3 -c "from market_sim.config.iso_configs import get_iso_config as g; from market_sim.model.transmission import apply_caiso_local_import_limits as f; print({(l.from_zone,l.to_zone):l.ttc_mw for l in f(g('CAISO'),'CAISO',2024,sd_floor_static=True).links}[('SP15_rest','SDGE')])"`
   must print 2074.0 (2019–2023: 1436.0; 2024: 2074.0; 2025: 2071.0).
   Also (the arm is live, frame + caiso-80 demand + HSL generation term; TI NOT moved; the EARLY window 2019-01 .. 2022-06-13 moves NG cells in 2019-2022): `PYTHONPATH=src python3 -c "import numpy as np; from market_sim.data.eia930 import frames as F; from market_sim.data.eia930.demand import _load_caiso_supply_consistent_demand as SC; from market_sim.data.renewables import load_hsl_hourly as H; a=F._eia_hourly_frame_filled('CISO',2024).copy(); da=SC(2024); ha=H('CAISO',2024); F.set_caiso_eia930_clock_repair(True); b=F._eia_hourly_frame_filled('CISO',2024); db=SC(2024); hb=H('CAISO',2024); ne=lambda c: int((~np.isclose(a[c].to_numpy(float),b[c].to_numpy(float),equal_nan=True)).sum()); nh=lambda c: int((~np.isclose(ha[c].to_numpy(float),hb[c].to_numpy(float))).sum()); print(ne('Demand'), ne('NG: SUN'), int((np.abs(da-db)>1e-6).sum()), nh('solar_gen_mw'), nh('wind_gen_mw'), ne('Total interchange'))"`
   must print EXACTLY (per year): 2019 -> `0 7007 8752 7007 8729 0`; 2020 -> `0 7119 8757 7117 8739 0`; 2021 -> `0 7321 8753 7321 8741 0`; 2022 -> `4776 3530 3934 3530 3931 0`; 2023 -> `8752 1140 1466 1140 1454 0`; 2024 -> `8758 7666 8753 7664 8743 0`; 2025 -> `8049 6943 8048 6943 8031 0`.
   (2019-2022 non-zero NG: SUN is the R-CAISO-17 build. If 2019/2020/2021 read `0 0 0 0 0 0` or 2022 reads `4776 0 0 0 0 0`, the build is missing — STOP. The last number must be 0 in every year.)
   Also (battery envelope arm, owner card 2026-09-29 "Add battery envelope"): `PYTHONPATH=src python3 -c "import numpy as np, pandas as pd; from market_sim.data.eia930 import frames as F; from market_sim.model import storage as S; from market_sim.config.paths import RAW_DIR; e=pd.read_csv(RAW_DIR/'reference'/'caiso-storage-shape-envelope.csv'); u=max([y for y in sorted(e.year.unique()) if y<=2024] or [2023]); r=e[e.year==u].sort_values('hod'); F.set_caiso_eia930_clock_repair(True); c,d=S._caiso_storage_envelope_clock_repaired(u); print(u, int((c!=r.chg_frac_p95.to_numpy()).sum()+(d!=r.dis_frac_p95.to_numpy()).sum()))"`
   must print EXACTLY: 2019/2020/2021/2022/2023 -> `2023 34`; 2024 -> `2024 40`; 2025 -> `2025 38`.
   (2019-2022 borrow the 2023 envelope, so they are NO LONGER expected to be byte-identical — ADDENDUM §7.)
3. After the solve, results/calibration/rcaiso20_A_2024/run_config.json must show:
   scenario_config: caiso_dsw_overnight_clean_unprinted_arm=true (THE NEW ARM — if it reads false or is absent, STOP), caiso_intertie_unprinted_year_measured_gas=true, caiso_dsw_overnight_clean=true, caiso_eia930_clock_repair=true, caiso_tac_shares_standard_time=true, caiso_supply_consistent_demand=true,
   caiso_ra_bridge_startup_aware=false, caiso_ra_mustoffer=true,
   caiso_ra_startup_bridge=true, caiso_ra_bridge_decommit=true, caiso_ra_min_load_frac=0.26,
   caiso_import_cap_floor_static=true, caiso_intertie_partial_year_measured=true,
   caiso_st_gas_peak_measured=true, caiso_per_hub_intertie=true, caiso_perhub_firm_base=true,
   caiso_import_gas_coupling_ladder_only=true, caiso_intertie_gap_fill_measured_dam=true,
   cc_eia923_identity_emission_basis=true, capacity_deliverability_limits=true, caiso_per_year_import_caps=true,
   mode="backcast", iso="CAISO"; calibration_flags.offer_curve_overrides == {} and offer_curve_deltas == {};
   calibration_flags.coal_prb_sigmoid_overrides.caiso_eia930_clock_repair == true (if that dict carries it).
   hourly/p0_dispatch_2024.parquet must exist (from --persist-p0-dispatch).
   The solve log must contain "firm import blocks shaped".

SOLVE (exactly this, unmodified, IN THE FOREGROUND — never nohup / & / run_in_background; never pass --no-container-preflight):
  python3 scripts/replay_keeper.py results/calibration/rcaiso18_A_span --years 2024 \
    --set caiso_eia930_clock_repair=true --set caiso_intertie_unprinted_year_measured_gas=true --set caiso_dsw_overnight_clean_unprinted_arm=true --persist-p0-dispatch \
    --out-dir results/calibration/rcaiso20_A_2024 \
    --note "R-CAISO-20 A 2024: keeper recipe + caiso_dsw_overnight_clean_unprinted_arm=true (owner ruling 2026-09-30; PRECOMMIT-r-caiso-20)"
  Budget: ~25 min. If it approaches 40 min with no bundle, stop and report.

PUSH (rule 34(a) — plain git add, NEVER `git add -f`, NEVER `git add -A` / `git add .`):
  git checkout -b claude/r-caiso-20-A-2024
  printf '\n!results/calibration/rcaiso20_A_2024/**\n' >> .gitignore
  git add .gitignore && git add results/calibration/rcaiso20_A_2024
  git status --short   # must show NOTHING staged outside .gitignore and results/calibration/rcaiso20_A_2024/
  ls results/calibration/rcaiso20_A_2024/dispatch/2024_P1.parquet   # must exist and be staged
  git commit -m "r-caiso-20-A-2024: one-year bundle (R-CAISO-20)" && git push -u origin claude/r-caiso-20-A-2024
  (If the push fails with HTTP 408/500: `git config http.version HTTP/1.1` and retry. If a pre-push hook
  blocks on lint of files you did not touch, report it and stop — do not reformat anything.)
  Then verify: `git ls-remote origin claude/r-caiso-20-A-2024` must print your commit sha, and
  `git ls-tree -r HEAD -- results/calibration/rcaiso20_A_2024 | wc -l` must be > 10.

FORBIDDEN, by name: `git add -A`, `git add .`, `git add -f`; scripts/dashboard_add_run.py, build_manifest.py,
build_status.py, prune_iso_runs.py, anything under frontend/data/backcast/**; ANY edit under src/ or scripts/
(except running them); opening a PR; deleting any result (rule 31); rebasing / pulling / force-pushing.

REPORT in your final message, in numbers:
- HEAD sha; the pushed commit sha (FULL 40 chars); the ls-tree file count
- the `container preflight:` and `memory peak:` log lines; wall time of the solve
- hard-stop 3 values as read from run_config.json
- the D-2 row for ra_mustoffer_bridge in legitimacy_diagnostics.json (forced TWh and forced share of CC_REGULAR), if present
- per-class annual TWh (model) from hourly/class_hourly_2024.parquet, pass P1: CC_REGULAR, CT_PEAKER, import (and per corridor WECC_PNW / WECC_DSW if the file splits them), ST_GAS, CC_CHP, hydro
- from hourly/system_2024.parquet, pass P1: SDGE annual slack (unserved) MWh, SDGE mean price, and the count of hours with price(SDGE) − price(SP15_rest) > 0.01
- whether the log contains "per-hub WECC intertie" AND "OVERNIGHT clean import depth armed" for this year (both MUST appear in every year; if either is absent in 2019/2020/2021, report it prominently)
- from dispatch/2024_P1.parquet: annual TWh of WECC_DSW_DSW_overnight_clean, and its TWh in months Jan-Apr
- per-unit P1 annual TWh of every import unit (unit_id starting WECC_) from dispatch/2024_P1.parquet, and annual TWh of flows.parquet P1 from_zone WECC_DSW and WECC_PNW
- the SP15_rest mean price over hours h17-22 and h8-16 (hour = hour-of-year % 24), and SDGE / LA_BASIN / NP15 annual mean price
- any WARNING about a fallback / missing input
- the SOLAR centroid: from hourly/class_hourly_2024.parquet (klass == "solar", pass P1), sum(mw * (hour%24 + 0.5)) / sum(mw) over Jun-Sep (hours 3624-6551)
- from hourly/storage_2024.parquet (tech li_ion, pass P1): annual discharge and charge TWh
