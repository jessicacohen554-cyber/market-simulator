# Temperature reliability-floor coefficients

Derived by `scripts/derive_reliability_coeffs.py`. `floor_pct = commit_frac x min_stable_pct`, where `min_stable_pct` is the class's PHYSICAL Pmin/Pmax of a committed unit (NREL WWSIS-2 Table 7, `constants.MIN_STABLE_PCT_PHYSICAL`), NOT the offer-curve must-run share (never residual-tuned, CLAUDE.md #9/#11). A limb is `enabled` only when `rho >= 0.3`, `n >= 30`, and `commit_frac > baseline_commit` (the flagged-day online share exceeds the mild-day online share — a like-for-like commitment test); weak limbs ship OFF but stay visible below. Onsets (`threshold`, °C) are physical anchors: hot = per-zone p95 tmax (design cooling day); cold = PJM Cold-Weather-Alert −12 °C / −20.5 °C (CT tier), else per-zone p1 tmin. See `threshold_basis` per row.

## ERCOT

| zone | plant_class | driver | threshold | floor_pct | enabled | commit_frac | min_stable_pct | rho | n | baseline | baseline_commit | threshold_basis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| North | COAL | tmax | 38.45 | 0.4 | False | 1.0 | 0.4 | -0.0043 | 55 | 0.6154 | 0.9325 | hot: zone p95 tmax (design cooling day) |
| North | COAL | tmin | -5.52 | 0.4 | False | 1.0 | 0.4 | 0.0092 | 11 | 0.6204 | 0.9352 | cold: zone p1 tmin (design heating day) |
| South | CT_PEAKER | tmax | 38.24 | 0.1699 | False | 0.447 | 0.38 | 0.2259 | 63 | 0.0403 | 0.3007 | hot: zone p95 tmax (design cooling day) |
| South | CT_PEAKER | tmin | 2.35 | 0.1464 | False | 0.3854 | 0.38 | 0.5818 | 11 | 0.0419 | 0.3089 | cold: zone p1 tmin (design heating day) |
| South | CC_REGULAR | tmax | 38.24 | 0.4913 | False | 0.9447 | 0.52 | 0.0061 | 63 | 0.2714 | 0.6483 | hot: zone p95 tmax (design cooling day) |
| South | CC_REGULAR | tmin | 2.35 | 0.4765 | False | 0.9163 | 0.52 | 0.4 | 11 | 0.283 | 0.6631 | cold: zone p1 tmin (design heating day) |
| North | ST_GAS | tmax | 38.45 | 0.1182 | False | 0.9853 | 0.12 | 0.1374 | 55 | 0.1248 | 0.6192 | hot: zone p95 tmax (design cooling day) |
| North | ST_GAS | tmin | -5.52 | 0.1019 | False | 0.849 | 0.12 | 0.812 | 11 | 0.137 | 0.6387 | cold: zone p1 tmin (design heating day) |
| Houston | ST_GAS | tmax | 37.8 | 0.0593 | False | 0.4943 | 0.12 | 0.4643 | 60 | 0.1499 | 0.4943 | hot: zone p95 tmax (design cooling day) |
| Houston | ST_GAS | tmin | -0.65 | 0.0593 | False | 0.4943 | 0.12 | -0.0336 | 9 | 0.1591 | 0.4943 | cold: zone p1 tmin (design heating day) |
| Houston | CT_PEAKER | tmax | 37.8 | 0.3335 | True | 0.8775 | 0.38 | 0.5447 | 62 | 0.0912 | 0.6278 | hot: zone p95 tmax (design cooling day) |
| Houston | CT_PEAKER | tmin | -0.65 | 0.3041 | False | 0.8003 | 0.38 | 0.3031 | 11 | 0.0966 | 0.6403 | cold: zone p1 tmin (design heating day) |
| Houston | CC_REGULAR | tmax | 37.8 | 0.5126 | True | 0.9858 | 0.52 | 0.4664 | 62 | 0.3837 | 0.7638 | hot: zone p95 tmax (design cooling day) |
| Houston | CC_REGULAR | tmin | -0.65 | 0.5089 | False | 0.9786 | 0.52 | 0.5829 | 11 | 0.3929 | 0.7743 | cold: zone p1 tmin (design heating day) |
| Houston | COAL | tmax | 37.8 | 0.4 | False | 1.0 | 0.4 | -0.0316 | 62 | 0.6276 | 1.0 | hot: zone p95 tmax (design cooling day) |
| Houston | COAL | tmin | -0.65 | 0.4 | False | 1.0 | 0.4 | 0.1272 | 11 | 0.6349 | 1.0 | cold: zone p1 tmin (design heating day) |
| West | CT_PEAKER | tmax | 38.9 | 0.2736 | False | 0.7201 | 0.38 | -0.069 | 63 | 0.1122 | 0.5598 | hot: zone p95 tmax (design cooling day) |
| West | CT_PEAKER | tmin | -7.7 | 0.263 | False | 0.692 | 0.38 | 0.691 | 8 | 0.1129 | 0.5691 | cold: zone p1 tmin (design heating day) |
| Northeast | ST_GAS | tmax | 37.2 | 0.12 | False | 1.0 | 0.12 | 0.4215 | 62 | 0.269 | 1.0 | hot: zone p95 tmax (design cooling day) |
| Northeast | ST_GAS | tmin | -4.94 | 0.12 | False | 1.0 | 0.12 | 0.3964 | 11 | 0.2791 | 1.0 | cold: zone p1 tmin (design heating day) |
| South_Central | CT_PEAKER | tmax | 38.75 | 0.3122 | True | 0.8216 | 0.38 | 0.3091 | 55 | 0.0808 | 0.5828 | hot: zone p95 tmax (design cooling day) |
| South_Central | CT_PEAKER | tmin | -4.0 | 0.2641 | False | 0.695 | 0.38 | 0.0909 | 11 | 0.0867 | 0.5964 | cold: zone p1 tmin (design heating day) |
| South_Central | ST_GAS | tmax | 38.75 | 0.1091 | False | 0.9093 | 0.12 | 0.2836 | 55 | 0.2674 | 0.7298 | hot: zone p95 tmax (design cooling day) |
| South_Central | ST_GAS | tmin | -4.0 | 0.1063 | False | 0.8857 | 0.12 | 0.0091 | 11 | 0.2783 | 0.7373 | cold: zone p1 tmin (design heating day) |
| North | CT_PEAKER | tmax | 38.45 | 0.1047 | True | 0.2754 | 0.38 | 0.5087 | 55 | 0.006 | 0.2754 | hot: zone p95 tmax (design cooling day) |
| North | CT_PEAKER | tmin | -5.52 | 0.1047 | False | 0.2754 | 0.38 | 0.6802 | 9 | 0.008 | 0.2754 | cold: zone p1 tmin (design heating day) |
| South_Central | CC_REGULAR | tmax | 38.75 | 0.5179 | False | 0.9959 | 0.52 | 0.2415 | 55 | 0.5287 | 0.8837 | hot: zone p95 tmax (design cooling day) |
| South_Central | CC_REGULAR | tmin | -4.0 | 0.5107 | False | 0.9821 | 0.52 | 0.4273 | 11 | 0.5378 | 0.8884 | cold: zone p1 tmin (design heating day) |
| Northeast | COAL | tmax | 37.2 | 0.4 | False | 1.0 | 0.4 | 0.4695 | 62 | 0.523 | 1.0 | hot: zone p95 tmax (design cooling day) |
| Northeast | COAL | tmin | -4.94 | 0.4 | False | 1.0 | 0.4 | 0.4365 | 11 | 0.5351 | 1.0 | cold: zone p1 tmin (design heating day) |
| South | COAL | tmax | 38.24 | 0.3911 | False | 0.9778 | 0.4 | -0.0077 | 63 | 0.5734 | 0.8487 | hot: zone p95 tmax (design cooling day) |
| South | COAL | tmin | 2.35 | 0.3417 | False | 0.8543 | 0.4 | -0.2636 | 11 | 0.5826 | 0.8575 | cold: zone p1 tmin (design heating day) |
| South_Central | COAL | tmax | 38.75 | 0.3983 | False | 0.9959 | 0.4 | 0.2025 | 55 | 0.4647 | 0.8839 | hot: zone p95 tmax (design cooling day) |
| South_Central | COAL | tmin | -4.0 | 0.3917 | False | 0.9793 | 0.4 | 0.3727 | 11 | 0.4725 | 0.8886 | cold: zone p1 tmin (design heating day) |
| Houston | CT_CHP | tmax | 37.8 | 0.1702 | False | 0.4478 | 0.38 | -0.0733 | 62 | 0.3295 | 0.4545 | hot: zone p95 tmax (design cooling day) |
| Houston | CT_CHP | tmin | -0.65 | 0.1754 | False | 0.4617 | 0.38 | -0.2005 | 11 | 0.3298 | 0.454 | cold: zone p1 tmin (design heating day) |
| South | CC_CHP | tmax | 38.24 | 0.151 | False | 0.2903 | 0.52 | 0.0533 | 63 | 0.1684 | 0.2903 | hot: zone p95 tmax (design cooling day) |
| South | CC_CHP | tmin | 2.35 | 0.151 | False | 0.2903 | 0.52 | 0.0455 | 11 | 0.1708 | 0.2903 | cold: zone p1 tmin (design heating day) |
| Houston | CC_CHP | tmax | 37.8 | 0.4111 | True | 0.7906 | 0.52 | 0.339 | 62 | 0.5554 | 0.7851 | hot: zone p95 tmax (design cooling day) |
| Houston | CC_CHP | tmin | -0.65 | 0.4111 | False | 0.7906 | 0.52 | 0.1539 | 11 | 0.5587 | 0.7854 | cold: zone p1 tmin (design heating day) |
| North | CC_REGULAR | tmax | 38.45 | 0.4713 | False | 0.9063 | 0.52 | 0.2314 | 55 | 0.4937 | 0.8034 | hot: zone p95 tmax (design cooling day) |
| North | CC_REGULAR | tmin | -5.52 | 0.4714 | False | 0.9066 | 0.52 | 0.5275 | 11 | 0.5027 | 0.8076 | cold: zone p1 tmin (design heating day) |
| West | CC_CHP | tmax | 38.9 | 0.52 | False | 1.0 | 0.52 | -0.2153 | 53 | 0.2444 | 1.0 | hot: zone p95 tmax (design cooling day) |
| West | CC_CHP | tmin | -7.7 | 0.52 | False | 1.0 | 0.52 | -0.7092 | 7 | 0.2394 | 1.0 | cold: zone p1 tmin (design heating day) |
| Northeast | CC_REGULAR | tmax | 37.2 | 0.52 | False | 1.0 | 0.52 | 0.2207 | 58 | 0.5253 | 1.0 | hot: zone p95 tmax (design cooling day) |
| Northeast | CC_REGULAR | tmin | -4.94 | 0.52 | False | 1.0 | 0.52 | -0.0691 | 11 | 0.5376 | 1.0 | cold: zone p1 tmin (design heating day) |
| West | CC_REGULAR | tmax | 38.9 | 0.4769 | False | 0.9171 | 0.52 | -0.2601 | 70 | 0.6475 | 0.8893 | hot: zone p95 tmax (design cooling day) |
| West | CC_REGULAR | tmin | -7.7 | 0.4769 | False | 0.9171 | 0.52 | -0.1091 | 8 | 0.651 | 0.8909 | cold: zone p1 tmin (design heating day) |

## CAISO

| zone | plant_class | driver | threshold | floor_pct | enabled | commit_frac | min_stable_pct | rho | n | baseline | baseline_commit | threshold_basis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NP15 | CT_PEAKER | netload | 27.57 | 0.1389 | True | 0.3656 | 0.38 | 0.5146 | 324 | 0.0496 | 0.2126 | netload: system p70 daily-peak net-load (demand - VRE) GW |
| NP15 | CC_REGULAR | tmax | 32.66 | 0.499 | False | 0.9596 | 0.52 | 0.1276 | 55 | 0.4276 | 0.7274 | hot: zone p95 tmax (design cooling day) |
| NP15 | CC_REGULAR | tmin | 1.75 | 0.4382 | False | 0.8426 | 0.52 | -0.2069 | 11 | 0.4392 | 0.738 | cold: zone p1 tmin (design heating day) |
| SP15 | ST_GAS | tmax | 26.7 | 0.0711 | False | 0.5924 | 0.12 | 0.2121 | 56 | 0.2196 | 0.4681 | hot: zone p95 tmax (design cooling day) |
| SP15 | ST_GAS | tmin | 5.66 | 0.0627 | False | 0.5227 | 0.12 | -0.0122 | 10 | 0.2268 | 0.4746 | cold: zone p1 tmin (design heating day) |
| SP15 | CT_PEAKER | netload | 27.57 | 0.1626 | True | 0.4278 | 0.38 | 0.6653 | 322 | 0.0208 | 0.2373 | netload: system p70 daily-peak net-load (demand - VRE) GW |
| SP15 | CC_REGULAR | tmax | 26.7 | 0.3171 | True | 0.6098 | 0.52 | 0.3211 | 56 | 0.2373 | 0.4751 | hot: zone p95 tmax (design cooling day) |
| SP15 | CC_REGULAR | tmin | 5.66 | 0.3292 | False | 0.6331 | 0.52 | 0.0061 | 10 | 0.2447 | 0.4806 | cold: zone p1 tmin (design heating day) |
| NP15 | CC_CHP | tmax | 32.66 | 0.2683 | False | 0.5159 | 0.52 | 0.0033 | 55 | 0.2994 | 0.4188 | hot: zone p95 tmax (design cooling day) |
| NP15 | CC_CHP | tmin | 1.75 | 0.2369 | False | 0.4556 | 0.52 | -0.3357 | 11 | 0.3033 | 0.4238 | cold: zone p1 tmin (design heating day) |
| ZP26 | CT_PEAKER | netload | 27.57 | 0.1231 | True | 0.3239 | 0.38 | 0.3181 | 140 | 0.0179 | 0.2374 | netload: system p70 daily-peak net-load (demand - VRE) GW |
| NP15 | CT_CHP | netload | 27.57 | 0.0863 | True | 0.2271 | 0.38 | 0.4269 | 326 | 0.1112 | 0.1759 | netload: system p70 daily-peak net-load (demand - VRE) GW |
| SP15 | CC_CHP | tmax | 26.7 | 0.0331 | False | 0.0637 | 0.52 | 0.4531 | 22 | 0.0183 | 0.0637 | hot: zone p95 tmax (design cooling day) |
| ZP26 | CT_CHP | netload | 27.57 | 0.0273 | True | 0.0718 | 0.38 | 0.4918 | 248 | 0.0151 | 0.0509 | netload: system p70 daily-peak net-load (demand - VRE) GW |
| ZP26 | CC_REGULAR | tmax | 40.6 | 0.52 | False | 1.0 | 0.52 | 0.2568 | 59 | 0.3228 | 0.7967 | hot: zone p95 tmax (design cooling day) |
| ZP26 | CC_REGULAR | tmin | 1.1 | 0.52 | False | 1.0 | 0.52 | -0.3354 | 5 | 0.3399 | 0.8068 | cold: zone p1 tmin (design heating day) |
| ZP26 | CC_CHP | tmax | 40.6 | 0.52 | False | 1.0 | 0.52 | 0.038 | 46 | 0.7509 | 1.0 | hot: zone p95 tmax (design cooling day) |
| ZP26 | CC_CHP | tmin | 1.1 | 0.52 | False | 1.0 | 0.52 | -0.2236 | 5 | 0.7545 | 1.0 | cold: zone p1 tmin (design heating day) |
