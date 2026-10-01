# SHARD REPORT — SPP-27 SCREEN shard B (2023)

- **Shard:** SPP-27 SCREEN shard B
- **Pin:** `1d175c88b6f99738c4e32a96c3b6438d742335cb` — VERIFIED (`git rev-parse HEAD` matched)
- **HARD STOP 2 (control config signature `results/calibration/spp64_span`):** PASS — `st_gas_mustrun_per_plant: true`, `st_gas_mustrun_p25_level: false`, `mustrun_online_frac_per_year: false`, `mustrun_layup_window_mask: false`, `mustrun_plant_exclusions: false`, `cc_mustrun_per_plant: false`
- **Command:** `python3 scripts/replay_keeper.py results/calibration/spp64_span --years 2023 --out-dir results/calibration/spp27_screen_2023 --set mustrun_window_commitment_grain=true`
- **Exit code:** `0`
- **Wall time:** `311 s` (5 min 11 s)
- **Environment note (no repo edit):** the container had no Python deps installed (`ModuleNotFoundError: No module named 'numpy'` on the first invocation). Resolved with `uv sync` (the repo's documented dependency path) and the solve was run with `.venv/bin/python`. No file under `src/` or `scripts/` was touched.
- **Solve tail warning (verbatim):** `WARNING: legitimacy diagnostics gate FAIL on the replayed bundle (artifact still written; C7/C8 score from its contents — see the report above)`

## Verbatim measurement stdout

```
=== 1. CONFIG IDENTITY ===
  mustrun_window_commitment_grain: control=None arm=True
  st_gas_mustrun_per_plant: control=True arm=True
  st_gas_mustrun_p25_level: control=False arm=False
  mustrun_online_frac_per_year: control=False arm=False
  mustrun_layup_window_mask: control=False arm=False
  mustrun_plant_exclusions: control=False arm=False
  cc_mustrun_per_plant: control=False arm=False
  offer_curve_by_group byte-identical: True
  ALL differing scenario_config keys: ['mustrun_window_commitment_grain']
     mustrun_window_commitment_grain: control=None arm=True
=== 2. SYSTEM (P1) ===
  CONTROL: dump=0.0000 MWh  slack=0.0000 MWh  price_max=59.3126
  ARM: dump=0.0000 MWh  slack=0.0000 MWh  price_max=59.3126
=== 3. CLASS TWh (P1) ===
  CC_CHP         control=    1.8477  arm=    1.8472  delta=  -0.0005
  CC_REGULAR     control=   41.9243  arm=   41.8267  delta=  -0.0976
  COAL_LIGNITE   control=    7.1926  arm=    7.1781  delta=  -0.0145
  COAL_PRB       control=   65.8052  arm=   65.6343  delta=  -0.1709
  CT_CHP         control=    1.2034  arm=    1.2030  delta=  -0.0004
  CT_PEAKER      control=   15.7407  arm=   15.7601  delta=  +0.0195
  OTHER          control=    0.5072  arm=    0.5072  delta=  +0.0000
  ST_CHP         control=    0.2926  arm=    0.2922  delta=  -0.0004
  ST_GAS         control=    9.4181  arm=    9.6983  delta=  +0.2801
  biomass        control=    1.1014  arm=    1.1014  delta=  +0.0000
  hydro          control=    8.3441  arm=    8.3441  delta=  +0.0000
  nuclear        control=   16.9270  arm=   16.9270  delta=  +0.0000
  oil            control=    0.0000  arm=    0.0000  delta=  +0.0000
  solar          control=    0.5875  arm=    0.5875  delta=  +0.0000
  wind           control=  113.7422  arm=  113.7294  delta=  -0.0128
  TOTAL          control=  284.6338  arm=  284.6364  delta=  +0.0026
=== 4. C3a / C3b ===
  CONTROL {'C3a': {'criterion': 'price_mean', 'key': None, 'year': 2023, 'status': 'PASS', 'classification': None, 'metric': 'system load-weighted mean LMP $/MWh (vs RT (load-weighted))', 'benchmark': 'RT', 'model': 25.38, 'actual': 25.13, 'tol': '±10% target / ±10% commercial', 'magnitude': '+1.0%'}, 'C3b': {'criterion': 'price_shape', 'key': None, 'year': 2023, 'status': 'PASS', 'classification': None, 'metric': 'monthly load-weighted price NRMSE (load-weighted actual)', 'model': 0.173, 'actual': None, 'tol': '≤0.20 target / ≤0.20 commercial', 'magnitude': 'NRMSE 0.173'}}
  ARM {'C3a': {'criterion': 'price_mean', 'key': None, 'year': 2023, 'status': 'PASS', 'classification': None, 'metric': 'system load-weighted mean LMP $/MWh (vs RT (load-weighted))', 'benchmark': 'RT', 'model': 25.37, 'actual': 25.13, 'tol': '±10% target / ±10% commercial', 'magnitude': '+0.9%'}, 'C3b': {'criterion': 'price_shape', 'key': None, 'year': 2023, 'status': 'PASS', 'classification': None, 'metric': 'monthly load-weighted price NRMSE (load-weighted actual)', 'model': 0.173, 'actual': None, 'tol': '≤0.20 target / ≤0.20 commercial', 'magnitude': 'NRMSE 0.173'}}
=== 5. LEGITIMACY DIAGNOSTICS (arm) ===
  gates: {"d1_min_profile_r": 0.8, "d1_min_cv_ratio": 0.5, "d1_offpeak_last_hour": 14, "d1_gated_classes": ["CT_PEAKER", "ST_GAS", "COAL", "COAL_LIGNITE", "COAL_PRB", "COAL_BIT", "COAL_WC"], "d2_peaker_max_share": 0.15, "d2_merchant_max_share": 0.3, "d2_exempt_classes": ["CC_CHP", "CT_CHP", "ST_CHP", "nuclear"], "d4_max_offwindow_share": 0.05}
  --- D1 passed=True ---
  summary: []
    {"year": 2023, "class": "CC_CHP", "profile_r": 0.953, "model_offpeak_cv": 0.052, "actual_offpeak_cv": 0.123, "cv_ratio": 0.421, "gated": false, "verdict": "pass"}
    {"year": 2023, "class": "CC_REGULAR", "profile_r": 0.997, "model_offpeak_cv": 0.186, "actual_offpeak_cv": 0.19, "cv_ratio": 0.98, "gated": false, "verdict": "pass"}
    {"year": 2023, "class": "COAL_LIGNITE", "profile_r": 0.988, "model_offpeak_cv": 0.19, "actual_offpeak_cv": 0.055, "cv_ratio": 3.427, "gated": true, "verdict": "pass"}
    {"year": 2023, "class": "COAL_PRB", "profile_r": 0.98, "model_offpeak_cv": 0.186, "actual_offpeak_cv": 0.158, "cv_ratio": 1.178, "gated": true, "verdict": "pass"}
    {"year": 2023, "class": "CT_CHP", "profile_r": 0.893, "model_offpeak_cv": 0.065, "actual_offpeak_cv": 0.01, "cv_ratio": 6.35, "gated": false, "verdict": "pass"}
    {"year": 2023, "class": "CT_PEAKER", "profile_r": 0.992, "model_offpeak_cv": 0.541, "actual_offpeak_cv": 0.572, "cv_ratio": 0.946, "gated": true, "verdict": "pass"}
    {"year": 2023, "class": "OTHER_FOSSIL", "profile_r": 0.932, "model_offpeak_cv": 0.511, "actual_offpeak_cv": 0.081, "cv_ratio": 6.289, "gated": false, "verdict": "pass"}
    {"year": 2023, "class": "ST_CHP", "profile_r": 0.983, "model_offpeak_cv": 0.808, "actual_offpeak_cv": 0.52, "cv_ratio": 1.554, "gated": false, "verdict": "pass"}
    {"year": 2023, "class": "ST_GAS", "profile_r": 0.987, "model_offpeak_cv": 0.451, "actual_offpeak_cv": 0.269, "cv_ratio": 1.672, "gated": true, "verdict": "pass"}
  --- D2 passed=True ---
  summary: [{"year": 2023, "class": "CC_REGULAR", "forced_twh": 0.0, "class_total_twh": 44.5443, "forced_share": 0.0, "limit": 0.3, "load_share": null, "immaterial": false, "lower_bound": true, "upper_bound": false, "verdict": "pass"}, {"year": 2023, "class": "COAL", "forced_twh": 0.0, "class_total_twh": 70.4726, "forced_share": 0.0, "limit": 0.3, "load_share": null, "immaterial": false, "lower_bound": true, "upper_bound": false, "verdict": "pass"}, {"year": 2023, "class": "CT_PEAKER", "forced_twh": 0.0, "class_total_twh": 12.9825, "forced_share": 0.0, "limit": 0.15, "load_share": null, "immaterial": false, "lower_bound": true, "upper_bound": false, "verdict": "pass"}, {"year": 2023, "class": "ST_GAS", "forced_twh": 2.555, "class_total_twh": 12.0981, "forced_share": 0.2112, "limit": 0.3, "load_share": null, "immaterial": false, "lower_bound": true, "upper_bound": false, "verdict": "pass"}, {"year": 2023, "class": "hydro", "forced_twh": 0.0, "class_total_twh": 8.3441, "forced_share": 0.0, "limit": 0.3, "load_share": null, "immaterial": false, "lower_bound": true, "upper_bound": false, "verdict": "pass"}]
    {"year": 2023, "class": "", "mechanism": "nuclear_mustrun", "forced_twh": 16.927, "class_total_twh": 16.927, "share_of_class": 1.0}
    {"year": 2023, "class": "CC_CHP", "mechanism": "chp_steam", "forced_twh": 0.0563, "class_total_twh": 1.8472, "share_of_class": 0.0305}
    {"year": 2023, "class": "CT_CHP", "mechanism": "chp_steam", "forced_twh": 0.0486, "class_total_twh": 1.355, "share_of_class": 0.0358}
    {"year": 2023, "class": "ST_CHP", "mechanism": "chp_steam", "forced_twh": 0.0094, "class_total_twh": 0.1402, "share_of_class": 0.0673}
    {"year": 2023, "class": "ST_GAS", "mechanism": "st_gas_mustrun_per_plant", "forced_twh": 2.555, "class_total_twh": 12.0981, "share_of_class": 0.2112}
  --- D4 passed=False ---
  summary: []
    {"year": 2023, "check": "window", "floor": "chp_steam", "window": "h0-23", "plant": "", "floored_twh": 0.1143, "offwindow_twh": 0.0, "offwindow_share": 0.0, "binding_hours": "", "measured_median_mw": "", "measured_zero_share": "", "verdict": "pass"}
    {"year": 2023, "check": "unit-conduct", "floor": "chp_steam", "window": "h0-23", "plant": "55064", "floored_twh": 0.0414, "offwindow_twh": "", "offwindow_share": 0.3622, "binding_hours": 685, "measured_median_mw": 204.872, "measured_zero_share": 0.0058, "verdict": "pass"}
    {"year": 2023, "check": "unit-conduct", "floor": "chp_steam", "window": "h0-23", "plant": "55176", "floored_twh": 0.0563, "offwindow_twh": "", "offwindow_share": 0.4926, "binding_hours": 666, "measured_median_mw": 231.524, "measured_zero_share": 0.0, "verdict": "pass"}
    {"year": 2023, "check": "window", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "", "floored_twh": 2.555, "offwindow_twh": 0.0, "offwindow_share": 0.0, "binding_hours": "", "measured_median_mw": "", "measured_zero_share": "", "verdict": "pass"}
    {"year": 2023, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "1230", "floored_twh": 0.0144, "offwindow_twh": "", "offwindow_share": 0.0057, "binding_hours": 1319, "measured_median_mw": 0.0, "measured_zero_share": 0.6096, "verdict": "FAIL"}
    {"year": 2023, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "1233", "floored_twh": 0.0295, "offwindow_twh": "", "offwindow_share": 0.0115, "binding_hours": 1007, "measured_median_mw": 37.248, "measured_zero_share": 0.007, "verdict": "pass"}
    {"year": 2023, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "1235", "floored_twh": 0.0138, "offwindow_twh": "", "offwindow_share": 0.0054, "binding_hours": 1138, "measured_median_mw": 0.0, "measured_zero_share": 0.5606, "verdict": "FAIL"}
    {"year": 2023, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "1271", "floored_twh": 0.0061, "offwindow_twh": "", "offwindow_share": 0.0024, "binding_hours": 851, "measured_median_mw": 0.0, "measured_zero_share": 0.5875, "verdict": "FAIL"}
    {"year": 2023, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "1416", "floored_twh": 0.0305, "offwindow_twh": "", "offwindow_share": 0.012, "binding_hours": 493, "measured_median_mw": 331.16, "measured_zero_share": 0.0, "verdict": "pass"}
    {"year": 2023, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "1417", "floored_twh": 0.0313, "offwindow_twh": "", "offwindow_share": 0.0123, "binding_hours": 1086, "measured_median_mw": 38.823, "measured_zero_share": 0.1538, "verdict": "pass"}
    {"year": 2023, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "2226", "floored_twh": 0.0048, "offwindow_twh": "", "offwindow_share": 0.0019, "binding_hours": 240, "measured_median_mw": 23.986, "measured_zero_share": 0.0, "verdict": "pass"}
    {"year": 2023, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "2952", "floored_twh": 0.2094, "offwindow_twh": "", "offwindow_share": 0.082, "binding_hours": 1057, "measured_median_mw": 275.061, "measured_zero_share": 0.1552, "verdict": "pass"}
    {"year": 2023, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "2956", "floored_twh": 0.2829, "offwindow_twh": "", "offwindow_share": 0.1107, "binding_hours": 2310, "measured_median_mw": 339.942, "measured_zero_share": 0.0355, "verdict": "pass"}
    {"year": 2023, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "2964", "floored_twh": 0.1461, "offwindow_twh": "", "offwindow_share": 0.0572, "binding_hours": 5758, "measured_median_mw": 77.84, "measured_zero_share": 0.0406, "verdict": "pass"}
    {"year": 2023, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "2965", "floored_twh": 0.0674, "offwindow_twh": "", "offwindow_share": 0.0264, "binding_hours": 3475, "measured_median_mw": 31.331, "measured_zero_share": 0.1266, "verdict": "pass"}
    {"year": 2023, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "3008", "floored_twh": 0.0374, "offwindow_twh": "", "offwindow_share": 0.0146, "binding_hours": 2081, "measured_median_mw": 0.0, "measured_zero_share": 0.6002, "verdict": "FAIL"}
    {"year": 2023, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "3476", "floored_twh": 0.1169, "offwindow_twh": "", "offwindow_share": 0.0458, "binding_hours": 1747, "measured_median_mw": 77.108, "measured_zero_share": 0.071, "verdict": "pass"}
    {"year": 2023, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "3478", "floored_twh": 0.2203, "offwindow_twh": "", "offwindow_share": 0.0862, "binding_hours": 4744, "measured_median_mw": 114.627, "measured_zero_share": 0.0249, "verdict": "pass"}
    {"year": 2023, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "3482", "floored_twh": 0.2319, "offwindow_twh": "", "offwindow_share": 0.0908, "binding_hours": 4053, "measured_median_mw": 118.797, "measured_zero_share": 0.0928, "verdict": "pass"}
    {"year": 2023, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "3484", "floored_twh": 0.1676, "offwindow_twh": "", "offwindow_share": 0.0656, "binding_hours": 5228, "measured_median_mw": 75.963, "measured_zero_share": 0.0891, "verdict": "pass"}
    {"year": 2023, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "3485", "floored_twh": 0.339, "offwindow_twh": "", "offwindow_share": 0.1327, "binding_hours": 4526, "measured_median_mw": 62.786, "measured_zero_share": 0.2614, "verdict": "pass"}
    {"year": 2023, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "4940", "floored_twh": 0.3161, "offwindow_twh": "", "offwindow_share": 0.1237, "binding_hours": 2410, "measured_median_mw": 264.687, "measured_zero_share": 0.0, "verdict": "pass"}
    {"year": 2023, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "7013", "floored_twh": 0.0035, "offwindow_twh": "", "offwindow_share": 0.0014, "binding_hours": 256, "measured_median_mw": 15.047, "measured_zero_share": 0.3516, "verdict": "pass"}
    FAIL: 2023 st_gas_mustrun_per_plant × ST_GAS: plant 1230 is floored for 0.0144 TWh (0.6% of the mechanism's forced energy) while its own measured median output over the 1319 hours the floor actually binds for it (inside h0-23) is 0.000 MW (61.0% of them at zero) — the meter says it is offline in at least half the hours the floor asserts it must be online (per-unit conduct rider)
    FAIL: 2023 st_gas_mustrun_per_plant × ST_GAS: plant 1235 is floored for 0.0138 TWh (0.5% of the mechanism's forced energy) while its own measured median output over the 1138 hours the floor actually binds for it (inside h0-23) is 0.000 MW (56.1% of them at zero) — the meter says it is offline in at least half the hours the floor asserts it must be online (per-unit conduct rider)
    FAIL: 2023 st_gas_mustrun_per_plant × ST_GAS: plant 1271 is floored for 0.0061 TWh (0.2% of the mechanism's forced energy) while its own measured median output over the 851 hours the floor actually binds for it (inside h0-23) is 0.000 MW (58.8% of them at zero) — the meter says it is offline in at least half the hours the floor asserts it must be online (per-unit conduct rider)
    FAIL: 2023 st_gas_mustrun_per_plant × ST_GAS: plant 3008 is floored for 0.0374 TWh (1.5% of the mechanism's forced energy) while its own measured median output over the 2081 hours the floor actually binds for it (inside h0-23) is 0.000 MW (60.0% of them at zero) — the meter says it is offline in at least half the hours the floor asserts it must be online (per-unit conduct rider)
```
