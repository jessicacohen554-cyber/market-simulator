# SHARD REPORT — SPP-27 span (2023–2025), `mustrun_window_commitment_grain`

Shard job: solve one SPP calibration replay across 2023–2025 with `mustrun_window_commitment_grain=true`
on top of keeper-8's recipe (`results/calibration/spp64_span`), attest it, register it on the backcast
dashboard, measure it, and push the artifacts.

- HEAD at start: `09d9fc00ea6a9f39eafdf444a6ff8a64d3b515f8` (verified)
- Data profile: `spp` (full clone — hydration is a no-op)
- Control bundle config sanity check: `st_gas_mustrun_per_plant=True`, and
  `st_gas_mustrun_p25_level`, `mustrun_online_frac_per_year`, `mustrun_layup_window_mask`,
  `mustrun_plant_exclusions`, `cc_mustrun_per_plant` all `False` — **all six matched**.

## STEP 1 — the solve

Command:

```
.venv/bin/python scripts/replay_keeper.py results/calibration/spp64_span \
  --years 2023 2024 2025 --out-dir results/calibration/spp27_span \
  --set mustrun_window_commitment_grain=true --note "SPP-27: ..."
```

- **exit code: 0**
- **wall time: 499 s (8 min 19 s)**

Solve-tail notes: legitimacy diagnostics D-5 parity PASS, D-9 overlay quarantine PASS,
D-10 free-class-only rescore PASS; `WARNING: legitimacy diagnostics gate FAIL on the replayed
bundle (artifact still written; C7/C8 score from its contents)`.

## STEP 2 — attestation

```
wrote results/calibration/spp27_span/calibration_attestation.json
  DOF ledger: n_entries=3 n_residual=2
  entries: ['offer_curve_by_group', 'offer_curve_smoothing', 'wefor_multiplier']
```

## STEP 3 — registration (verbatim stdout)

```
INFO: Loaded 304 per-plant CAMPD bins from /home/user/market-simulator/data/raw/reference/custom-bin-assignments.csv (81.7 GW)
  WARNING SPP 2023: 4 plant(s) have NO EIA-860 nameplate in either the operable or the within-window retiree vintage and fall back to npl = 1 MW — their per-plant hourly `campd` blob is NOT usable (c_ann and annual gates are unaffected): 2217, 2302, 2991, 55655
  SPP 2023: CT-only CEMS bench flag (923 net > 1.1x CAMPD gross) — scored on EIA-923 monthly: 57881 Pioneer Generation Station (2.95x), 63628 Tinker (1.66x), 8059 Comanche (OK) (1.62x), 2446:CT_PEAKER Maddox (1.49x), 55457 McClain Energy Facility (1.48x), 2446:ST_GAS Maddox (1.31x), 2240:COAL_PRB Lon Wright (1.16x), 2951:CT_PEAKER Horseshoe Lake (1.11x), 2963:CC_REGULAR Northeastern (1.10x)
  WARNING SPP 2024: 4 plant(s) have NO EIA-860 nameplate in either the operable or the within-window retiree vintage and fall back to npl = 1 MW — their per-plant hourly `campd` blob is NOT usable (c_ann and annual gates are unaffected): 2217, 2302, 2991, 55655
  SPP 2024: CT-only CEMS bench flag (923 net > 1.1x CAMPD gross) — scored on EIA-923 monthly: 63628 Tinker (3.98x), 7887:CT_PEAKER Terry Bundy Generating Station (2.46x), 57881 Pioneer Generation Station (1.73x), 8059 Comanche (OK) (1.66x), 55457 McClain Energy Facility (1.48x), 2963:CC_REGULAR Northeastern (1.38x), 1336:CT_PEAKER Garden City (1.36x), 2240:COAL_PRB Lon Wright (1.27x), 2951:CT_PEAKER Horseshoe Lake (1.12x)
  SPP 2025: CT-only CEMS bench flag (923 net > 1.1x CAMPD gross) — scored on EIA-923 monthly: 7887:CT_PEAKER Terry Bundy Generating Station (3.40x), 55457 McClain Energy Facility (1.49x), 2963:CC_REGULAR Northeastern (1.41x), 2951:ST_GAS Horseshoe Lake (1.23x), 2291:ST_GAS North Omaha (1.19x)
wrote 1 run data files under /home/user/market-simulator/frontend/data/backcast (45.0 MB data, ids: ['2026-09-10-spp-27-commitment-grain'])
registered '2026-09-10-spp-27-commitment-grain' (iso=SPP, bundle=results/calibration/spp27_span)
RUN_ID=2026-09-10-spp-27-commitment-grain
DETERMINATION: CALIBRATED [SPP spp 27 commitment grain] — 1 ledgered caveat(s) (measured-input or model-class) — REPORTED, and NOT determination-downgrading under rubric v3.3: C3c price tail / scarcity (RT hourly)
wrote results/calibration/spp27_span/metrics.json
```

## STEP 4 — measurement (verbatim stdout)

```
=== 1. CONFIG IDENTITY ===
  differing keys: ['mustrun_window_commitment_grain']
     mustrun_window_commitment_grain control= None arm= True
  offer_curve_by_group identical: True
=== 2. SYSTEM P1 2023 ===
  CONTROL: dump=0.0000 slack=0.0000 price_max=59.3126
  ARM: dump=0.0000 slack=0.0000 price_max=59.3126
=== 3. CLASS TWh P1 2023 ===
  CC_CHP         control=    1.8477 arm=    1.8472 delta=  -0.0005
  CC_REGULAR     control=   41.9243 arm=   41.8267 delta=  -0.0976
  COAL_LIGNITE   control=    7.1926 arm=    7.1781 delta=  -0.0145
  COAL_PRB       control=   65.8052 arm=   65.6343 delta=  -0.1709
  CT_CHP         control=    1.2034 arm=    1.2030 delta=  -0.0004
  CT_PEAKER      control=   15.7407 arm=   15.7601 delta=  +0.0195
  OTHER          control=    0.5072 arm=    0.5072 delta=  +0.0000
  ST_CHP         control=    0.2926 arm=    0.2922 delta=  -0.0004
  ST_GAS         control=    9.4181 arm=    9.6983 delta=  +0.2801
  biomass        control=    1.1014 arm=    1.1014 delta=  +0.0000
  hydro          control=    8.3441 arm=    8.3441 delta=  +0.0000
  nuclear        control=   16.9270 arm=   16.9270 delta=  +0.0000
  oil            control=    0.0000 arm=    0.0000 delta=  +0.0000
  solar          control=    0.5875 arm=    0.5875 delta=  +0.0000
  wind           control=  113.7422 arm=  113.7294 delta=  -0.0128
  TOTAL          control=  284.6338 arm=  284.6364 delta=  +0.0026
=== 2. SYSTEM P1 2024 ===
  CONTROL: dump=0.0000 slack=370.1017 price_max=2000.0000
  ARM: dump=0.0000 slack=370.1017 price_max=2000.0000
=== 3. CLASS TWh P1 2024 ===
  CC_CHP         control=    1.8845 arm=    1.8832 delta=  -0.0013
  CC_REGULAR     control=   41.7536 arm=   41.6791 delta=  -0.0745
  COAL_LIGNITE   control=    6.5671 arm=    6.5622 delta=  -0.0049
  COAL_PRB       control=   60.7148 arm=   60.6077 delta=  -0.1071
  CT_CHP         control=    1.2355 arm=    1.2367 delta=  +0.0013
  CT_PEAKER      control=   18.0989 arm=   18.0986 delta=  -0.0003
  OTHER          control=    0.5987 arm=    0.5987 delta=  +0.0000
  ST_CHP         control=    0.3992 arm=    0.3996 delta=  +0.0004
  ST_GAS         control=   12.6745 arm=   12.8748 delta=  +0.2004
  biomass        control=    1.1803 arm=    1.1803 delta=  +0.0000
  hydro          control=    8.9667 arm=    8.9667 delta=  +0.0000
  nuclear        control=   15.0157 arm=   15.0157 delta=  +0.0000
  oil            control=    0.0030 arm=    0.0030 delta=  +0.0000
  solar          control=    1.1939 arm=    1.1941 delta=  +0.0002
  wind           control=  120.7130 arm=  120.7003 delta=  -0.0126
  TOTAL          control=  290.9994 arm=  291.0008 delta=  +0.0014
=== 2. SYSTEM P1 2025 ===
  CONTROL: dump=0.0000 slack=0.0000 price_max=73.7731
  ARM: dump=0.0000 slack=0.0000 price_max=73.7731
=== 3. CLASS TWh P1 2025 ===
  CC_CHP         control=    1.9308 arm=    1.9343 delta=  +0.0035
  CC_REGULAR     control=   34.9578 arm=   34.9097 delta=  -0.0481
  COAL_LIGNITE   control=    6.8367 arm=    6.7981 delta=  -0.0386
  COAL_PRB       control=   80.6176 arm=   80.4149 delta=  -0.2026
  CT_CHP         control=    1.1490 arm=    1.1487 delta=  -0.0003
  CT_PEAKER      control=   14.1782 arm=   14.2422 delta=  +0.0640
  OTHER          control=    0.4891 arm=    0.4891 delta=  +0.0000
  ST_CHP         control=    0.1750 arm=    0.1760 delta=  +0.0010
  ST_GAS         control=   11.7795 arm=   12.0198 delta=  +0.2403
  biomass        control=    0.9490 arm=    0.9490 delta=  +0.0000
  hydro          control=    8.8207 arm=    8.8204 delta=  -0.0003
  nuclear        control=   15.7804 arm=   15.7804 delta=  +0.0000
  oil            control=    0.0000 arm=    0.0000 delta=  +0.0000
  solar          control=    2.3250 arm=    2.3244 delta=  -0.0006
  wind           control=  122.0359 arm=  122.0210 delta=  -0.0148
  TOTAL          control=  302.0245 arm=  302.0280 delta=  +0.0035
=== 4. C3a / C3b ===
  2023 CONTROL {'C3a': {'criterion': 'price_mean', 'key': None, 'year': 2023, 'status': 'PASS', 'classification': None, 'metric': 'system load-weighted mean LMP $/MWh (vs RT (load-weighted))', 'benchmark': 'RT', 'model': 25.38, 'actual': 25.13, 'tol': '±10% target / ±10% commercial', 'magnitude': '+1.0%'}, 'C3b': {'criterion': 'price_shape', 'key': None, 'year': 2023, 'status': 'PASS', 'classification': None, 'metric': 'monthly load-weighted price NRMSE (load-weighted actual)', 'model': 0.173, 'actual': None, 'tol': '≤0.20 target / ≤0.20 commercial', 'magnitude': 'NRMSE 0.173'}}
  2023 ARM {'C3a': {'criterion': 'price_mean', 'key': None, 'year': 2023, 'status': 'PASS', 'classification': None, 'metric': 'system load-weighted mean LMP $/MWh (vs RT (load-weighted))', 'benchmark': 'RT', 'model': 25.37, 'actual': 25.13, 'tol': '±10% target / ±10% commercial', 'magnitude': '+0.9%'}, 'C3b': {'criterion': 'price_shape', 'key': None, 'year': 2023, 'status': 'PASS', 'classification': None, 'metric': 'monthly load-weighted price NRMSE (load-weighted actual)', 'model': 0.173, 'actual': None, 'tol': '≤0.20 target / ≤0.20 commercial', 'magnitude': 'NRMSE 0.173'}}
  2024 CONTROL {'C3a': {'criterion': 'price_mean', 'key': None, 'year': 2024, 'status': 'PASS', 'classification': None, 'metric': 'system load-weighted mean LMP $/MWh (vs RT (load-weighted))', 'benchmark': 'RT', 'model': 25.47, 'actual': 25.45, 'tol': '±10% target / ±10% commercial', 'magnitude': '+0.1%'}, 'C3b': {'criterion': 'price_shape', 'key': None, 'year': 2024, 'status': 'PASS', 'classification': None, 'metric': 'monthly load-weighted price NRMSE (load-weighted actual)', 'model': 0.171, 'actual': None, 'tol': '≤0.20 target / ≤0.20 commercial', 'magnitude': 'NRMSE 0.171'}}
  2024 ARM {'C3a': {'criterion': 'price_mean', 'key': None, 'year': 2024, 'status': 'PASS', 'classification': None, 'metric': 'system load-weighted mean LMP $/MWh (vs RT (load-weighted))', 'benchmark': 'RT', 'model': 25.47, 'actual': 25.45, 'tol': '±10% target / ±10% commercial', 'magnitude': '+0.1%'}, 'C3b': {'criterion': 'price_shape', 'key': None, 'year': 2024, 'status': 'PASS', 'classification': None, 'metric': 'monthly load-weighted price NRMSE (load-weighted actual)', 'model': 0.171, 'actual': None, 'tol': '≤0.20 target / ≤0.20 commercial', 'magnitude': 'NRMSE 0.171'}}
  2025 CONTROL {'C3a': {'criterion': 'price_mean', 'key': None, 'year': 2025, 'status': 'PASS', 'classification': None, 'metric': 'system load-weighted mean LMP $/MWh (vs RT (load-weighted))', 'benchmark': 'RT', 'model': 28.8, 'actual': 28.6, 'tol': '±10% target / ±10% commercial', 'magnitude': '+0.7%'}, 'C3b': {'criterion': 'price_shape', 'key': None, 'year': 2025, 'status': 'PASS', 'classification': None, 'metric': 'monthly load-weighted price NRMSE (load-weighted actual)', 'model': 0.163, 'actual': None, 'tol': '≤0.20 target / ≤0.20 commercial', 'magnitude': 'NRMSE 0.163'}}
  2025 ARM {'C3a': {'criterion': 'price_mean', 'key': None, 'year': 2025, 'status': 'PASS', 'classification': None, 'metric': 'system load-weighted mean LMP $/MWh (vs RT (load-weighted))', 'benchmark': 'RT', 'model': 28.79, 'actual': 28.6, 'tol': '±10% target / ±10% commercial', 'magnitude': '+0.7%'}, 'C3b': {'criterion': 'price_shape', 'key': None, 'year': 2025, 'status': 'PASS', 'classification': None, 'metric': 'monthly load-weighted price NRMSE (load-weighted actual)', 'model': 0.164, 'actual': None, 'tol': '≤0.20 target / ≤0.20 commercial', 'magnitude': 'NRMSE 0.164'}}
=== 5. FLEET-ARRAY GATES (zero LP) ===
  2023 CONTROL implied_starts_mech16= 2843 mechs= {1: {'twh': 16.926975, 'p2m': 1.0}, 2: {'twh': 1.245162, 'p2m': 1.0}, 16: {'twh': 3.870051, 'p2m': 1.2349}}
  2023 ARM implied_starts_mech16= 288 mechs= {1: {'twh': 16.926975, 'p2m': 1.0}, 2: {'twh': 1.245162, 'p2m': 1.0}, 16: {'twh': 4.07049, 'p2m': 1.0}}
  2024 CONTROL implied_starts_mech16= 3002 mechs= {1: {'twh': 15.015699, 'p2m': 1.0}, 2: {'twh': 1.242283, 'p2m': 1.0}, 16: {'twh': 4.198918, 'p2m': 1.2159}}
  2024 ARM implied_starts_mech16= 342 mechs= {1: {'twh': 15.015699, 'p2m': 1.0}, 2: {'twh': 1.242283, 'p2m': 1.0}, 16: {'twh': 4.330413, 'p2m': 1.0}}
  2025 CONTROL implied_starts_mech16= 2792 mechs= {1: {'twh': 15.780396, 'p2m': 1.0}, 2: {'twh': 1.278781, 'p2m': 1.0}, 16: {'twh': 4.263776, 'p2m': 1.2159}}
  2025 ARM implied_starts_mech16= 315 mechs= {1: {'twh': 15.780396, 'p2m': 1.0}, 2: {'twh': 1.278781, 'p2m': 1.0}, 16: {'twh': 4.404441, 'p2m': 1.0}}
=== 6. LEGITIMACY DIAGNOSTICS (arm) ===
  gates: {"d1_min_profile_r": 0.8, "d1_min_cv_ratio": 0.5, "d1_offpeak_last_hour": 14, "d1_gated_classes": ["CT_PEAKER", "ST_GAS", "COAL", "COAL_LIGNITE", "COAL_PRB", "COAL_BIT", "COAL_WC"], "d2_peaker_max_share": 0.15, "d2_merchant_max_share": 0.3, "d2_exempt_classes": ["CC_CHP", "CT_CHP", "ST_CHP", "nuclear"], "d4_max_offwindow_share": 0.05}
  --- D1 passed= True ---
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
    {"year": 2024, "class": "CC_CHP", "profile_r": 0.935, "model_offpeak_cv": 0.035, "actual_offpeak_cv": 0.09, "cv_ratio": 0.385, "gated": false, "verdict": "pass"}
    {"year": 2024, "class": "CC_REGULAR", "profile_r": 0.993, "model_offpeak_cv": 0.165, "actual_offpeak_cv": 0.183, "cv_ratio": 0.903, "gated": false, "verdict": "pass"}
    {"year": 2024, "class": "COAL_LIGNITE", "profile_r": 0.969, "model_offpeak_cv": 0.187, "actual_offpeak_cv": 0.07, "cv_ratio": 2.682, "gated": true, "verdict": "pass"}
    {"year": 2024, "class": "COAL_PRB", "profile_r": 0.989, "model_offpeak_cv": 0.166, "actual_offpeak_cv": 0.155, "cv_ratio": 1.075, "gated": true, "verdict": "pass"}
    {"year": 2024, "class": "CT_CHP", "profile_r": 0.874, "model_offpeak_cv": 0.031, "actual_offpeak_cv": 0.012, "cv_ratio": 2.617, "gated": false, "verdict": "pass"}
    {"year": 2024, "class": "CT_PEAKER", "profile_r": 0.994, "model_offpeak_cv": 0.495, "actual_offpeak_cv": 0.422, "cv_ratio": 1.174, "gated": true, "verdict": "pass"}
    {"year": 2024, "class": "OTHER_FOSSIL", "profile_r": 0.971, "model_offpeak_cv": 0.658, "actual_offpeak_cv": 0.706, "cv_ratio": 0.931, "gated": false, "verdict": "pass"}
    {"year": 2024, "class": "ST_GAS", "profile_r": 0.997, "model_offpeak_cv": 0.302, "actual_offpeak_cv": 0.199, "cv_ratio": 1.515, "gated": true, "verdict": "pass"}
    {"year": 2025, "class": "CC_CHP", "profile_r": 0.981, "model_offpeak_cv": 0.043, "actual_offpeak_cv": 0.111, "cv_ratio": 0.386, "gated": false, "verdict": "pass"}
    {"year": 2025, "class": "CC_REGULAR", "profile_r": 0.996, "model_offpeak_cv": 0.22, "actual_offpeak_cv": 0.192, "cv_ratio": 1.148, "gated": false, "verdict": "pass"}
    {"year": 2025, "class": "COAL_LIGNITE", "profile_r": 0.971, "model_offpeak_cv": 0.158, "actual_offpeak_cv": 0.048, "cv_ratio": 3.32, "gated": true, "verdict": "pass"}
    {"year": 2025, "class": "COAL_PRB", "profile_r": 0.984, "model_offpeak_cv": 0.121, "actual_offpeak_cv": 0.118, "cv_ratio": 1.029, "gated": true, "verdict": "pass"}
    {"year": 2025, "class": "CT_CHP", "profile_r": 0.894, "model_offpeak_cv": 0.036, "actual_offpeak_cv": 0.008, "cv_ratio": 4.624, "gated": false, "verdict": "pass"}
    {"year": 2025, "class": "CT_PEAKER", "profile_r": 0.995, "model_offpeak_cv": 0.421, "actual_offpeak_cv": 0.432, "cv_ratio": 0.975, "gated": true, "verdict": "pass"}
    {"year": 2025, "class": "OTHER_FOSSIL", "profile_r": 0.945, "model_offpeak_cv": 0.24, "actual_offpeak_cv": 0.06, "cv_ratio": 3.985, "gated": false, "verdict": "pass"}
    {"year": 2025, "class": "ST_GAS", "profile_r": 0.992, "model_offpeak_cv": 0.253, "actual_offpeak_cv": 0.189, "cv_ratio": 1.338, "gated": true, "verdict": "pass"}
  --- D2 passed= True ---
  summary: [{"year": 2023, "class": "CC_REGULAR", "forced_twh": 0.0, "class_total_twh": 44.5443, "forced_share": 0.0, "limit": 0.3, "load_share": null, "immaterial": false, "lower_bound": true, "upper_bound": false, "verdict": "pass"}, {"year": 2023, "class": "COAL", "forced_twh": 0.0, "class_total_twh": 70.4726, "forced_share": 0.0, "limit": 0.3, "load_share": null, "immaterial": false, "lower_bound": true, "upper_bound": false, "verdict": "pass"}, {"year": 2023, "class": "CT_PEAKER", "forced_twh": 0.0, "class_total_twh": 12.9825, "forced_share": 0.0, "limit": 0.15, "load_share": null, "immaterial": false, "lower_bound": true, "upper_bound": false, "verdict": "pass"}, {"year": 2023, "class": "ST_GAS", "forced_twh": 2.555, "class_total_twh": 12.0981, "forced_share": 0.2112, "limit": 0.3, "load_share": null, "immaterial": false, "lower_bound": true, "upper_bound": false, "verdict": "pass"}, {"year": 2023, "class": "hydro", "forced_twh": 0.0, "class_total_twh": 8.3441, "forced_share": 0.0, "limit": 0.3, "load_share": null, "immaterial": false, "lower_bound": true, "upper_bound": false, "verdict": "pass"}, {"year": 2024, "class": "CC_REGULAR", "forced_twh": 0.0, "class_total_twh": 44.1433, "forced_share": 0.0, "limit": 0.3, "load_share": null, "immaterial": false, "lower_bound": true, "upper_bound": false, "verdict": "pass"}, {"year": 2024, "class": "COAL", "forced_twh": 0.0, "class_total_twh": 67.7102, "forced_share": 0.0, "limit": 0.3, "load_share": null, "immaterial": false, "lower_bound": true, "upper_bound": false, "verdict": "pass"}, {"year": 2024, "class": "CT_PEAKER", "forced_twh": 0.0, "class_total_twh": 15.1734, "forced_share": 0.0, "limit": 0.15, "load_share": null, "immaterial": false, "lower_bound": true, "upper_bound": false, "verdict": "pass"}, {"year": 2024, "class": "ST_GAS", "forced_twh": 2.5195, "class_total_twh": 12.7962, "forced_share": 0.1969, "limit": 0.3, "load_share": null, "immaterial": false, "lower_bound": true, "upper_bound": false, "verdict": "pass"}, {"year": 2024, "class": "hydro", "forced_twh": 0.0, "class_total_twh": 8.9667, "forced_share": 0.0, "limit": 0.3, "load_share": null, "immaterial": false, "lower_bound": true, "upper_bound": false, "verdict": "pass"}, {"year": 2025, "class": "CC_REGULAR", "forced_twh": 0.0, "class_total_twh": 37.6513, "forced_share": 0.0, "limit": 0.3, "load_share": null, "immaterial": false, "lower_bound": true, "upper_bound": false, "verdict": "pass"}, {"year": 2025, "class": "COAL", "forced_twh": 0.0, "class_total_twh": 83.8812, "forced_share": 0.0, "limit": 0.3, "load_share": null, "immaterial": false, "lower_bound": true, "upper_bound": false, "verdict": "pass"}, {"year": 2025, "class": "CT_PEAKER", "forced_twh": 0.0, "class_total_twh": 12.1688, "forced_share": 0.0, "limit": 0.15, "load_share": null, "immaterial": false, "lower_bound": true, "upper_bound": false, "verdict": "pass"}, {"year": 2025, "class": "ST_GAS", "forced_twh": 2.6803, "class_total_twh": 14.6834, "forced_share": 0.1825, "limit": 0.3, "load_share": null, "immaterial": false, "lower_bound": true, "upper_bound": false, "verdict": "pass"}, {"year": 2025, "class": "hydro", "forced_twh": 0.0, "class_total_twh": 8.8204, "forced_share": 0.0, "limit": 0.3, "load_share": null, "immaterial": false, "lower_bound": true, "upper_bound": false, "verdict": "pass"}]
    {"year": 2023, "class": "", "mechanism": "nuclear_mustrun", "forced_twh": 16.927, "class_total_twh": 16.927, "share_of_class": 1.0}
    {"year": 2023, "class": "CC_CHP", "mechanism": "chp_steam", "forced_twh": 0.0563, "class_total_twh": 1.8472, "share_of_class": 0.0305}
    {"year": 2023, "class": "CT_CHP", "mechanism": "chp_steam", "forced_twh": 0.0486, "class_total_twh": 1.355, "share_of_class": 0.0358}
    {"year": 2023, "class": "ST_CHP", "mechanism": "chp_steam", "forced_twh": 0.0094, "class_total_twh": 0.1402, "share_of_class": 0.0673}
    {"year": 2023, "class": "ST_GAS", "mechanism": "st_gas_mustrun_per_plant", "forced_twh": 2.555, "class_total_twh": 12.0981, "share_of_class": 0.2112}
    {"year": 2024, "class": "", "mechanism": "nuclear_mustrun", "forced_twh": 15.0157, "class_total_twh": 15.018, "share_of_class": 0.9998}
    {"year": 2024, "class": "CC_CHP", "mechanism": "chp_steam", "forced_twh": 0.0404, "class_total_twh": 1.8832, "share_of_class": 0.0214}
    {"year": 2024, "class": "CT_CHP", "mechanism": "chp_steam", "forced_twh": 0.0377, "class_total_twh": 1.464, "share_of_class": 0.0257}
    {"year": 2024, "class": "ST_CHP", "mechanism": "chp_steam", "forced_twh": 0.0076, "class_total_twh": 0.1724, "share_of_class": 0.0439}
    {"year": 2024, "class": "ST_GAS", "mechanism": "st_gas_mustrun_per_plant", "forced_twh": 2.5195, "class_total_twh": 12.7962, "share_of_class": 0.1969}
    {"year": 2025, "class": "", "mechanism": "nuclear_mustrun", "forced_twh": 15.7804, "class_total_twh": 15.7804, "share_of_class": 1.0}
    {"year": 2025, "class": "CC_CHP", "mechanism": "chp_steam", "forced_twh": 0.0611, "class_total_twh": 1.9343, "share_of_class": 0.0316}
    {"year": 2025, "class": "CT_CHP", "mechanism": "chp_steam", "forced_twh": 0.0435, "class_total_twh": 1.1768, "share_of_class": 0.0369}
    {"year": 2025, "class": "ST_CHP", "mechanism": "chp_steam", "forced_twh": 0.0093, "class_total_twh": 0.1479, "share_of_class": 0.063}
    {"year": 2025, "class": "ST_GAS", "mechanism": "st_gas_mustrun_per_plant", "forced_twh": 2.6803, "class_total_twh": 14.6834, "share_of_class": 0.1825}
  --- D4 passed= False ---
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
    {"year": 2024, "check": "window", "floor": "chp_steam", "window": "h0-23", "plant": "", "floored_twh": 0.0856, "offwindow_twh": 0.0, "offwindow_share": 0.0, "binding_hours": "", "measured_median_mw": "", "measured_zero_share": "", "verdict": "pass"}
    {"year": 2024, "check": "unit-conduct", "floor": "chp_steam", "window": "h0-23", "plant": "55064", "floored_twh": 0.0314, "offwindow_twh": "", "offwindow_share": 0.3667, "binding_hours": 526, "measured_median_mw": 204.885, "measured_zero_share": 0.0, "verdict": "pass"}
    {"year": 2024, "check": "unit-conduct", "floor": "chp_steam", "window": "h0-23", "plant": "55176", "floored_twh": 0.0404, "offwindow_twh": "", "offwindow_share": 0.4716, "binding_hours": 517, "measured_median_mw": 229.221, "measured_zero_share": 0.0329, "verdict": "pass"}
    {"year": 2024, "check": "window", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "", "floored_twh": 2.5195, "offwindow_twh": 0.0, "offwindow_share": 0.0, "binding_hours": "", "measured_median_mw": "", "measured_zero_share": "", "verdict": "pass"}
    {"year": 2024, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "1230", "floored_twh": 0.0182, "offwindow_twh": "", "offwindow_share": 0.0072, "binding_hours": 1216, "measured_median_mw": 24.136, "measured_zero_share": 0.4408, "verdict": "pass"}
    {"year": 2024, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "1233", "floored_twh": 0.0261, "offwindow_twh": "", "offwindow_share": 0.0104, "binding_hours": 901, "measured_median_mw": 32.868, "measured_zero_share": 0.1287, "verdict": "pass"}
    {"year": 2024, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "1235", "floored_twh": 0.0113, "offwindow_twh": "", "offwindow_share": 0.0045, "binding_hours": 1040, "measured_median_mw": 0.0, "measured_zero_share": 0.576, "verdict": "FAIL"}
    {"year": 2024, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "1271", "floored_twh": 0.0057, "offwindow_twh": "", "offwindow_share": 0.0023, "binding_hours": 738, "measured_median_mw": 0.0, "measured_zero_share": 0.6938, "verdict": "FAIL"}
    {"year": 2024, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "1416", "floored_twh": 0.0181, "offwindow_twh": "", "offwindow_share": 0.0072, "binding_hours": 292, "measured_median_mw": 292.435, "measured_zero_share": 0.0, "verdict": "pass"}
    {"year": 2024, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "1417", "floored_twh": 0.0451, "offwindow_twh": "", "offwindow_share": 0.0179, "binding_hours": 1420, "measured_median_mw": 73.154, "measured_zero_share": 0.3246, "verdict": "pass"}
    {"year": 2024, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "2226", "floored_twh": 0.0068, "offwindow_twh": "", "offwindow_share": 0.0027, "binding_hours": 343, "measured_median_mw": 22.903, "measured_zero_share": 0.0, "verdict": "pass"}
    {"year": 2024, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "2952", "floored_twh": 0.6196, "offwindow_twh": "", "offwindow_share": 0.2459, "binding_hours": 2912, "measured_median_mw": 423.25, "measured_zero_share": 0.1459, "verdict": "pass"}
    {"year": 2024, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "2956", "floored_twh": 0.2557, "offwindow_twh": "", "offwindow_share": 0.1015, "binding_hours": 2540, "measured_median_mw": 237.704, "measured_zero_share": 0.0811, "verdict": "pass"}
    {"year": 2024, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "2964", "floored_twh": 0.1411, "offwindow_twh": "", "offwindow_share": 0.056, "binding_hours": 5579, "measured_median_mw": 82.139, "measured_zero_share": 0.0335, "verdict": "pass"}
    {"year": 2024, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "2965", "floored_twh": 0.1308, "offwindow_twh": "", "offwindow_share": 0.0519, "binding_hours": 4726, "measured_median_mw": 48.797, "measured_zero_share": 0.1261, "verdict": "pass"}
    {"year": 2024, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "3008", "floored_twh": 0.0394, "offwindow_twh": "", "offwindow_share": 0.0156, "binding_hours": 2449, "measured_median_mw": 0.0, "measured_zero_share": 0.5725, "verdict": "FAIL"}
    {"year": 2024, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "3476", "floored_twh": 0.1561, "offwindow_twh": "", "offwindow_share": 0.062, "binding_hours": 2350, "measured_median_mw": 77.146, "measured_zero_share": 0.2468, "verdict": "pass"}
    {"year": 2024, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "3478", "floored_twh": 0.2136, "offwindow_twh": "", "offwindow_share": 0.0848, "binding_hours": 5292, "measured_median_mw": 88.064, "measured_zero_share": 0.0775, "verdict": "pass"}
    {"year": 2024, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "3482", "floored_twh": 0.1415, "offwindow_twh": "", "offwindow_share": 0.0562, "binding_hours": 2620, "measured_median_mw": 144.682, "measured_zero_share": 0.0885, "verdict": "pass"}
    {"year": 2024, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "3484", "floored_twh": 0.0849, "offwindow_twh": "", "offwindow_share": 0.0337, "binding_hours": 2339, "measured_median_mw": 75.96, "measured_zero_share": 0.1381, "verdict": "pass"}
    {"year": 2024, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "3485", "floored_twh": 0.1055, "offwindow_twh": "", "offwindow_share": 0.0419, "binding_hours": 2467, "measured_median_mw": 58.983, "measured_zero_share": 0.306, "verdict": "pass"}
    {"year": 2024, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "4940", "floored_twh": 0.3276, "offwindow_twh": "", "offwindow_share": 0.13, "binding_hours": 3003, "measured_median_mw": 274.338, "measured_zero_share": 0.0503, "verdict": "pass"}
    {"year": 2024, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "6193", "floored_twh": 0.0154, "offwindow_twh": "", "offwindow_share": 0.0061, "binding_hours": 471, "measured_median_mw": 0.0, "measured_zero_share": 0.7919, "verdict": "FAIL"}
    {"year": 2024, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "7013", "floored_twh": 0.0015, "offwindow_twh": "", "offwindow_share": 0.0006, "binding_hours": 109, "measured_median_mw": 15.001, "measured_zero_share": 0.0, "verdict": "pass"}
    {"year": 2025, "check": "window", "floor": "chp_steam", "window": "h0-23", "plant": "", "floored_twh": 0.1139, "offwindow_twh": 0.0, "offwindow_share": 0.0, "binding_hours": "", "measured_median_mw": "", "measured_zero_share": "", "verdict": "pass"}
    {"year": 2025, "check": "unit-conduct", "floor": "chp_steam", "window": "h0-23", "plant": "55064", "floored_twh": 0.0356, "offwindow_twh": "", "offwindow_share": 0.3126, "binding_hours": 591, "measured_median_mw": 199.971, "measured_zero_share": 0.0, "verdict": "pass"}
    {"year": 2025, "check": "unit-conduct", "floor": "chp_steam", "window": "h0-23", "plant": "55176", "floored_twh": 0.0611, "offwindow_twh": "", "offwindow_share": 0.5364, "binding_hours": 772, "measured_median_mw": 224.509, "measured_zero_share": 0.0, "verdict": "pass"}
    {"year": 2025, "check": "window", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "", "floored_twh": 2.6803, "offwindow_twh": 0.0, "offwindow_share": 0.0, "binding_hours": "", "measured_median_mw": "", "measured_zero_share": "", "verdict": "pass"}
    {"year": 2025, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "1230", "floored_twh": 0.0105, "offwindow_twh": "", "offwindow_share": 0.0039, "binding_hours": 1349, "measured_median_mw": 0.0, "measured_zero_share": 0.7191, "verdict": "FAIL"}
    {"year": 2025, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "1233", "floored_twh": 0.0198, "offwindow_twh": "", "offwindow_share": 0.0074, "binding_hours": 679, "measured_median_mw": 32.942, "measured_zero_share": 0.2297, "verdict": "pass"}
    {"year": 2025, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "1235", "floored_twh": 0.008, "offwindow_twh": "", "offwindow_share": 0.003, "binding_hours": 1150, "measured_median_mw": 0.0, "measured_zero_share": 0.7452, "verdict": "FAIL"}
    {"year": 2025, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "1271", "floored_twh": 0.0072, "offwindow_twh": "", "offwindow_share": 0.0027, "binding_hours": 861, "measured_median_mw": 0.0, "measured_zero_share": 0.6411, "verdict": "FAIL"}
    {"year": 2025, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "1416", "floored_twh": 0.0308, "offwindow_twh": "", "offwindow_share": 0.0115, "binding_hours": 454, "measured_median_mw": 285.927, "measured_zero_share": 0.0, "verdict": "pass"}
    {"year": 2025, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "1417", "floored_twh": 0.0493, "offwindow_twh": "", "offwindow_share": 0.0184, "binding_hours": 2044, "measured_median_mw": 41.194, "measured_zero_share": 0.1854, "verdict": "pass"}
    {"year": 2025, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "2226", "floored_twh": 0.004, "offwindow_twh": "", "offwindow_share": 0.0015, "binding_hours": 210, "measured_median_mw": 23.958, "measured_zero_share": 0.0, "verdict": "pass"}
    {"year": 2025, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "2952", "floored_twh": 0.1597, "offwindow_twh": "", "offwindow_share": 0.0596, "binding_hours": 749, "measured_median_mw": 314.871, "measured_zero_share": 0.1482, "verdict": "pass"}
    {"year": 2025, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "2956", "floored_twh": 0.3852, "offwindow_twh": "", "offwindow_share": 0.1437, "binding_hours": 3630, "measured_median_mw": 271.574, "measured_zero_share": 0.1, "verdict": "pass"}
    {"year": 2025, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "2964", "floored_twh": 0.1094, "offwindow_twh": "", "offwindow_share": 0.0408, "binding_hours": 4676, "measured_median_mw": 38.735, "measured_zero_share": 0.176, "verdict": "pass"}
    {"year": 2025, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "2965", "floored_twh": 0.1138, "offwindow_twh": "", "offwindow_share": 0.0425, "binding_hours": 3902, "measured_median_mw": 38.304, "measured_zero_share": 0.1907, "verdict": "pass"}
    {"year": 2025, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "3008", "floored_twh": 0.04, "offwindow_twh": "", "offwindow_share": 0.0149, "binding_hours": 2421, "measured_median_mw": 0.0, "measured_zero_share": 0.5262, "verdict": "FAIL"}
    {"year": 2025, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "3476", "floored_twh": 0.1798, "offwindow_twh": "", "offwindow_share": 0.0671, "binding_hours": 2745, "measured_median_mw": 76.954, "measured_zero_share": 0.2444, "verdict": "pass"}
    {"year": 2025, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "3478", "floored_twh": 0.2146, "offwindow_twh": "", "offwindow_share": 0.0801, "binding_hours": 4782, "measured_median_mw": 96.853, "measured_zero_share": 0.059, "verdict": "pass"}
    {"year": 2025, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "3482", "floored_twh": 0.1932, "offwindow_twh": "", "offwindow_share": 0.0721, "binding_hours": 3962, "measured_median_mw": 191.859, "measured_zero_share": 0.0581, "verdict": "pass"}
    {"year": 2025, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "3484", "floored_twh": 0.0235, "offwindow_twh": "", "offwindow_share": 0.0088, "binding_hours": 827, "measured_median_mw": 52.211, "measured_zero_share": 0.0314, "verdict": "pass"}
    {"year": 2025, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "3485", "floored_twh": 0.1805, "offwindow_twh": "", "offwindow_share": 0.0673, "binding_hours": 4456, "measured_median_mw": 59.001, "measured_zero_share": 0.3894, "verdict": "pass"}
    {"year": 2025, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "4940", "floored_twh": 0.1907, "offwindow_twh": "", "offwindow_share": 0.0711, "binding_hours": 1880, "measured_median_mw": 217.556, "measured_zero_share": 0.0181, "verdict": "pass"}
    {"year": 2025, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "6193", "floored_twh": 0.5877, "offwindow_twh": "", "offwindow_share": 0.2193, "binding_hours": 5453, "measured_median_mw": 194.242, "measured_zero_share": 0.2179, "verdict": "pass"}
    {"year": 2025, "check": "unit-conduct", "floor": "st_gas_mustrun_per_plant \u00d7 ST_GAS", "window": "h0-23", "plant": "7013", "floored_twh": 0.0015, "offwindow_twh": "", "offwindow_share": 0.0006, "binding_hours": 113, "measured_median_mw": 14.975, "measured_zero_share": 0.0, "verdict": "pass"}
    FAIL: 2023 st_gas_mustrun_per_plant × ST_GAS: plant 1230 is floored for 0.0144 TWh (0.6% of the mechanism's forced energy) while its own measured median output over the 1319 hours the floor actually binds for it (inside h0-23) is 0.000 MW (61.0% of them at zero) — the meter says it is offline in at least half the hours the floor asserts it must be online (per-unit conduct rider)
    FAIL: 2023 st_gas_mustrun_per_plant × ST_GAS: plant 1235 is floored for 0.0138 TWh (0.5% of the mechanism's forced energy) while its own measured median output over the 1138 hours the floor actually binds for it (inside h0-23) is 0.000 MW (56.1% of them at zero) — the meter says it is offline in at least half the hours the floor asserts it must be online (per-unit conduct rider)
    FAIL: 2023 st_gas_mustrun_per_plant × ST_GAS: plant 1271 is floored for 0.0061 TWh (0.2% of the mechanism's forced energy) while its own measured median output over the 851 hours the floor actually binds for it (inside h0-23) is 0.000 MW (58.8% of them at zero) — the meter says it is offline in at least half the hours the floor asserts it must be online (per-unit conduct rider)
    FAIL: 2023 st_gas_mustrun_per_plant × ST_GAS: plant 3008 is floored for 0.0374 TWh (1.5% of the mechanism's forced energy) while its own measured median output over the 2081 hours the floor actually binds for it (inside h0-23) is 0.000 MW (60.0% of them at zero) — the meter says it is offline in at least half the hours the floor asserts it must be online (per-unit conduct rider)
    FAIL: 2024 st_gas_mustrun_per_plant × ST_GAS: plant 1235 is floored for 0.0113 TWh (0.4% of the mechanism's forced energy) while its own measured median output over the 1040 hours the floor actually binds for it (inside h0-23) is 0.000 MW (57.6% of them at zero) — the meter says it is offline in at least half the hours the floor asserts it must be online (per-unit conduct rider)
    FAIL: 2024 st_gas_mustrun_per_plant × ST_GAS: plant 1271 is floored for 0.0057 TWh (0.2% of the mechanism's forced energy) while its own measured median output over the 738 hours the floor actually binds for it (inside h0-23) is 0.000 MW (69.4% of them at zero) — the meter says it is offline in at least half the hours the floor asserts it must be online (per-unit conduct rider)
    FAIL: 2024 st_gas_mustrun_per_plant × ST_GAS: plant 3008 is floored for 0.0394 TWh (1.6% of the mechanism's forced energy) while its own measured median output over the 2449 hours the floor actually binds for it (inside h0-23) is 0.000 MW (57.2% of them at zero) — the meter says it is offline in at least half the hours the floor asserts it must be online (per-unit conduct rider)
    FAIL: 2024 st_gas_mustrun_per_plant × ST_GAS: plant 6193 is floored for 0.0154 TWh (0.6% of the mechanism's forced energy) while its own measured median output over the 471 hours the floor actually binds for it (inside h0-23) is 0.000 MW (79.2% of them at zero) — the meter says it is offline in at least half the hours the floor asserts it must be online (per-unit conduct rider)
    FAIL: 2025 st_gas_mustrun_per_plant × ST_GAS: plant 1230 is floored for 0.0105 TWh (0.4% of the mechanism's forced energy) while its own measured median output over the 1349 hours the floor actually binds for it (inside h0-23) is 0.000 MW (71.9% of them at zero) — the meter says it is offline in at least half the hours the floor asserts it must be online (per-unit conduct rider)
    FAIL: 2025 st_gas_mustrun_per_plant × ST_GAS: plant 1235 is floored for 0.0080 TWh (0.3% of the mechanism's forced energy) while its own measured median output over the 1150 hours the floor actually binds for it (inside h0-23) is 0.000 MW (74.5% of them at zero) — the meter says it is offline in at least half the hours the floor asserts it must be online (per-unit conduct rider)
    FAIL: 2025 st_gas_mustrun_per_plant × ST_GAS: plant 1271 is floored for 0.0072 TWh (0.3% of the mechanism's forced energy) while its own measured median output over the 861 hours the floor actually binds for it (inside h0-23) is 0.000 MW (64.1% of them at zero) — the meter says it is offline in at least half the hours the floor asserts it must be online (per-unit conduct rider)
    FAIL: 2025 st_gas_mustrun_per_plant × ST_GAS: plant 3008 is floored for 0.0400 TWh (1.5% of the mechanism's forced energy) while its own measured median output over the 2421 hours the floor actually binds for it (inside h0-23) is 0.000 MW (52.6% of them at zero) — the meter says it is offline in at least half the hours the floor asserts it must be online (per-unit conduct rider)
=== 7. METRICS SIDECAR ===
{
  "run_id": "2026-09-10-spp-27-commitment-grain",
  "iso": "SPP",
  "label": "spp 27 commitment grain",
  "target_years": [
    2023,
    2024,
    2025
  ],
  "scorable_years": [
    2023,
    2024,
    2025
  ],
  "data_blocked_years": [],
  "rubric_version": 3.7,
  "determination": "CALIBRATED",
  "reasons": [
    "1 ledgered caveat(s) (measured-input or model-class) \u2014 REPORTED, and NOT determination-downgrading under rubric v3.3: C3c price tail / scarcity (RT hourly)"
  ],
  "notes": [],
  "criteria": {
    "fuelmix": {
      "label": "C1 fuel-mix by class (grid-delivered)",
      "tier": "load-bearing",
      "status": "PASS"
    },
    "sysvol": {
      "label": "C2 system volume (gas/coal families)",
      "tier": "load-bearing",
      "status": "PASS"
    },
    "price_mean": {
      "label": "C3a mean LMP",
      "tier": "load-bearing",
      "status": "PASS"
    },
    "price_shape": {
      "label": "C3b price duration/shape",
      "tier": "load-bearing",
      "status": "PASS"
    },
    "price_tail": {
      "label": "C3c price tail / scarcity (RT hourly)",
      "tier": "supporting",
      "status": "CAVEAT",
      "caveat_kind": "ledgered"
    },
    "dispatch_corr": {
      "label": "C4 fleet hourly dispatch correlation",
      "tier": "supporting",
      "status": "PASS"
    },
    "governance": {
      "label": "C6 governance gate",
      "tier": "protective",
      "status": "PASS"
    },
    "forced_share": {
      "label": "C8 forced-energy share (D-2)",
      "tier": "protective",
      "status": "PASS"
    }
  },
  "caveats": {
    "protective": [],
    "ledgered": [
      "C3c price tail / scarcity (RT hourly)"
    ],
    "commercial_band": [],
    "budget": {
      "protective_max": 0,
      "ledgered_max": 1
    }
  },
  "grade_summary": {
    "scored": 8,
    "target_grade": 7,
    "commercial_grade": 0,
    "ledgered": 1,
    "fails": 0
  },
  "reported": {
    "co2": {
      "label": "C5a CO2 vs eGRID (REPORTED-ONLY, v2.9 \u2014 see the CRITERIA note)",
      "years": {
        "2023": "-1.9%",
        "2024": "-1.4%",
        "2025": "+2.7%"
      }
    },
    "diurnal_amplitude": {
      "label": "D-A diurnal price amplitude, hour-of-day (REPORTED-ONLY, BAND-FREE, v3.5 \u2014 no external comparable exists to band it; see the note)",
      "years": {
        "2023": "amplitude 38.8% of measured (hod range $11.45 vs $29.48); peak h17 vs h17, trough h02 vs h01 \u2014 phase OK; hod r +0.946; 364 complete days",
        "2024": "amplitude 38.6% of measured (hod range $14.39 vs $37.29); peak h15 vs h16, trough h02 vs h01 \u2014 phase OK; hod r +0.968; 364 complete days",
        "2025": "amplitude 24.6% of measured (hod range $11.64 vs $47.28); peak h17 vs h17, trough h01 vs h01 \u2014 phase OK; hod r +0.892; 364 complete days"
      }
    }
  },
  "free_class_score": {
    "iso": "SPP",
    "pinned_classes": [
      "CC_CHP",
      "CT_CHP",
      "ST_CHP",
      "hydro",
      "nuclear",
      "solar",
      "wind"
    ],
    "excluded_from_free": [
      "CC_CHP",
      "ST_CHP"
    ],
    "all": {
      "pass": 16,
      "total": 16
    },
    "free": {
      "pass": 12,
      "total": 12
    },
    "headline": "C1 all 16/16 \u00b7 free 12/12"
  }
}

```
