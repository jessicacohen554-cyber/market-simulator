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

## MISO

| zone | plant_class | driver | threshold | floor_pct | enabled | commit_frac | min_stable_pct | rho | n | baseline | baseline_commit | threshold_basis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MISO-South | ST_GAS | tmax | 35.95 | 0.103 | False | 0.8579 | 0.12 | 0.2654 | 55 | 0.3694 | 0.647 | hot: zone p95 tmax (design cooling day) |
| MISO-South | ST_GAS | tmin | -6.06 | 0.1093 | False | 0.9111 | 0.12 | 0.5182 | 11 | 0.3808 | 0.655 | cold: zone p1 tmin (design heating day) |
| MISO-Illinois | COAL | tmax | 32.8 | 0.3633 | False | 0.9082 | 0.4 | 0.1226 | 59 | 0.6983 | 0.8723 | hot: zone p95 tmax (design cooling day) |
| MISO-Illinois | COAL | tmin | -17.13 | 0.3666 | False | 0.9166 | 0.4 | 0.1007 | 11 | 0.7024 | 0.8738 | cold: zone p1 tmin (design heating day) |
| MISO-Illinois | CT_PEAKER | tmax | 32.8 | 0.1818 | False | 0.4785 | 0.38 | 0.1815 | 59 | 0.0458 | 0.1704 | hot: zone p95 tmax (design cooling day) |
| MISO-Illinois | CT_PEAKER | tmin | -17.13 | 0.0811 | False | 0.2133 | 0.38 | 0.0961 | 11 | 0.0508 | 0.1878 | cold: zone p1 tmin (design heating day) |
| MISO-Indiana | CT_PEAKER | tmax | 32.2 | 0.3221 | True | 0.8476 | 0.38 | 0.318 | 66 | 0.4222 | 0.4874 | hot: zone p95 tmax (design cooling day) |
| MISO-Indiana | CT_PEAKER | tmin | -16.6 | 0.2245 | False | 0.5909 | 0.38 | 0.3242 | 10 | 0.434 | 0.5084 | cold: zone p1 tmin (design heating day) |
| MISO-Indiana | ST_GAS | tmax | 32.2 | 0.069 | False | 0.5749 | 0.12 | 0.3331 | 66 | 0.3711 | 0.5749 | hot: zone p95 tmax (design cooling day) |
| MISO-Indiana | ST_GAS | tmin | -16.6 | 0.069 | False | 0.5749 | 0.12 | -0.1896 | 10 | 0.3777 | 0.5749 | cold: zone p1 tmin (design heating day) |
| MISO-Indiana | CC_REGULAR | tmax | 32.2 | 0.5158 | False | 0.992 | 0.52 | 0.294 | 66 | 0.7514 | 0.8615 | hot: zone p95 tmax (design cooling day) |
| MISO-Indiana | CC_REGULAR | tmin | -16.6 | 0.49 | False | 0.9424 | 0.52 | -0.5994 | 10 | 0.758 | 0.8687 | cold: zone p1 tmin (design heating day) |
| MISO-Indiana | COAL | tmax | 32.2 | 0.3741 | True | 0.9353 | 0.4 | 0.3743 | 66 | 0.4458 | 0.8937 | hot: zone p95 tmax (design cooling day) |
| MISO-Indiana | COAL | tmin | -16.6 | 0.3748 | False | 0.937 | 0.4 | -0.159 | 10 | 0.451 | 0.8959 | cold: zone p1 tmin (design heating day) |
| MISO-Plains | CT_PEAKER | tmax | 33.35 | 0.2032 | False | 0.5348 | 0.38 | 0.096 | 54 | 0.0439 | 0.2388 | hot: zone p95 tmax (design cooling day) |
| MISO-Plains | CT_PEAKER | tmin | -17.43 | 0.0787 | False | 0.207 | 0.38 | 0.7615 | 9 | 0.0532 | 0.2643 | cold: zone p1 tmin (design heating day) |
| MISO-Plains | COAL | tmax | 33.35 | 0.3574 | False | 0.8935 | 0.4 | -0.1062 | 57 | 0.5056 | 0.7547 | hot: zone p95 tmax (design cooling day) |
| MISO-Plains | COAL | tmin | -17.43 | 0.3674 | False | 0.9186 | 0.4 | -0.2551 | 11 | 0.5137 | 0.7603 | cold: zone p1 tmin (design heating day) |
| MISO-Plains | ST_GAS | tmax | 33.35 | 0.0618 | True | 0.5148 | 0.12 | 0.4104 | 54 | 0.1124 | 0.3173 | hot: zone p95 tmax (design cooling day) |
| MISO-Plains | ST_GAS | tmin | -17.43 | 0.0501 | False | 0.4177 | 0.12 | 0.1507 | 11 | 0.1161 | 0.3262 | cold: zone p1 tmin (design heating day) |
| MISO-South | CT_CHP | tmax | 35.95 | 0.1383 | False | 0.3639 | 0.38 | -0.063 | 55 | 0.5496 | 0.3639 | hot: zone p95 tmax (design cooling day) |
| MISO-South | CT_CHP | tmin | -6.06 | 0.1383 | False | 0.3639 | 0.38 | 0.1636 | 11 | 0.5473 | 0.3639 | cold: zone p1 tmin (design heating day) |
| MISO-South | COAL | tmax | 35.95 | 0.3877 | True | 0.9692 | 0.4 | 0.3683 | 55 | 0.4406 | 0.7553 | hot: zone p95 tmax (design cooling day) |
| MISO-South | COAL | tmin | -6.06 | 0.3882 | False | 0.9706 | 0.4 | 0.3475 | 11 | 0.4518 | 0.7639 | cold: zone p1 tmin (design heating day) |
| MISO-South | ST_CHP | tmax | 35.95 | 0.0818 | False | 0.6818 | 0.12 | 0.187 | 55 | 0.9522 | 0.5007 | hot: zone p95 tmax (design cooling day) |
| MISO-South | ST_CHP | tmin | -6.06 | 0.0919 | False | 0.7658 | 0.12 |  | 11 | 0.9532 | 0.5072 | cold: zone p1 tmin (design heating day) |
| MISO-South | CC_REGULAR | tmax | 35.95 | 0.4952 | False | 0.9523 | 0.52 | -0.2132 | 55 | 0.5294 | 0.8176 | hot: zone p95 tmax (design cooling day) |
| MISO-South | CC_REGULAR | tmin | -6.06 | 0.481 | False | 0.9251 | 0.52 | 0.0 | 11 | 0.5368 | 0.8233 | cold: zone p1 tmin (design heating day) |
| MISO-South | CT_PEAKER | tmax | 35.95 | 0.2892 | False | 0.7611 | 0.38 | 0.1182 | 55 | 0.3928 | 0.3615 | hot: zone p95 tmax (design cooling day) |
| MISO-South | CT_PEAKER | tmin | -6.06 | 0.2656 | False | 0.699 | 0.38 | 0.7 | 11 | 0.4024 | 0.3783 | cold: zone p1 tmin (design heating day) |
| MISO-East | ST_GAS | tmax | 30.44 | 0.0501 | False | 0.4178 | 0.12 | 0.1296 | 58 | 0.1119 | 0.4137 | hot: zone p95 tmax (design cooling day) |
| MISO-East | ST_GAS | tmin | -16.03 | 0.0355 | False | 0.2959 | 0.12 | -0.3091 | 11 | 0.1201 | 0.4156 | cold: zone p1 tmin (design heating day) |
| MISO-East | COAL | tmax | 30.44 | 0.3886 | False | 0.9714 | 0.4 | 0.288 | 58 | 0.58 | 0.9472 | hot: zone p95 tmax (design cooling day) |
| MISO-East | COAL | tmin | -16.03 | 0.3976 | False | 0.9941 | 0.4 | 0.2 | 11 | 0.5872 | 0.948 | cold: zone p1 tmin (design heating day) |
| MISO-East | CT_PEAKER | tmax | 30.44 | 0.2791 | False | 0.7345 | 0.38 | 0.1814 | 58 | 0.3328 | 0.3474 | hot: zone p95 tmax (design cooling day) |
| MISO-East | CT_PEAKER | tmin | -16.03 | 0.1789 | False | 0.4708 | 0.38 | -0.1727 | 11 | 0.3494 | 0.3669 | cold: zone p1 tmin (design heating day) |
| MISO-West | ST_GAS | tmax | 31.7 | 0.12 | False | 1.0 | 0.12 | 0.1103 | 49 | 0.4207 | 1.0 | hot: zone p95 tmax (design cooling day) |
| MISO-West | ST_GAS | tmin | -22.13 | 0.12 | False | 1.0 | 0.12 | 0.0 | 3 | 0.4352 | 1.0 | cold: zone p1 tmin (design heating day) |
| MISO-West | COAL | tmax | 31.7 | 0.3731 | False | 0.9328 | 0.4 | -0.1446 | 64 | 0.6116 | 0.8843 | hot: zone p95 tmax (design cooling day) |
| MISO-West | COAL | tmin | -22.13 | 0.3885 | False | 0.9712 | 0.4 | 0.7817 | 11 | 0.6164 | 0.8863 | cold: zone p1 tmin (design heating day) |
| MISO-West | CC_REGULAR | tmax | 31.7 | 0.4492 | False | 0.8638 | 0.52 | 0.0236 | 64 | 0.5257 | 0.7323 | hot: zone p95 tmax (design cooling day) |
| MISO-West | CC_REGULAR | tmin | -22.13 | 0.381 | False | 0.7326 | 0.52 | 0.0 | 11 | 0.5387 | 0.7403 | cold: zone p1 tmin (design heating day) |
| MISO-West | CT_PEAKER | tmax | 31.7 | 0.2444 | False | 0.643 | 0.38 | 0.0224 | 64 | 0.1246 | 0.2889 | hot: zone p95 tmax (design cooling day) |
| MISO-West | CT_PEAKER | tmin | -22.13 | 0.0843 | False | 0.2218 | 0.38 | -0.3265 | 11 | 0.1343 | 0.3114 | cold: zone p1 tmin (design heating day) |
| MISO-West | ST_CHP | tmax | 31.7 | 0.011 | False | 0.0916 | 0.12 | 0.3131 | 6 | 0.0113 | 0.0916 | hot: zone p95 tmax (design cooling day) |
| MISO-East | CC_REGULAR | tmax | 30.44 | 0.4543 | False | 0.8737 | 0.52 | 0.0664 | 58 | 0.7535 | 0.7873 | hot: zone p95 tmax (design cooling day) |
| MISO-East | CC_REGULAR | tmin | -16.03 | 0.4324 | False | 0.8316 | 0.52 | -0.0273 | 11 | 0.7619 | 0.7915 | cold: zone p1 tmin (design heating day) |
| MISO-Plains | CC_REGULAR | tmax | 33.35 | 0.5035 | False | 0.9682 | 0.52 | -0.0417 | 57 | 0.5266 | 0.8387 | hot: zone p95 tmax (design cooling day) |
| MISO-Plains | CC_REGULAR | tmin | -17.43 | 0.4503 | False | 0.866 | 0.52 | -0.5558 | 11 | 0.5358 | 0.8457 | cold: zone p1 tmin (design heating day) |
| MISO-East | CC_CHP | tmax | 30.44 | 0.4934 | False | 0.9489 | 0.52 | 0.1107 | 58 | 0.6835 | 0.9281 | hot: zone p95 tmax (design cooling day) |
| MISO-East | CC_CHP | tmin | -16.03 | 0.4929 | False | 0.9479 | 0.52 | 0.1091 | 11 | 0.6853 | 0.929 | cold: zone p1 tmin (design heating day) |
| MISO-East | CT_CHP | tmax | 30.44 | 0.2512 | False | 0.6611 | 0.38 | -0.0593 | 58 | 0.9216 | 0.6222 | hot: zone p95 tmax (design cooling day) |
| MISO-East | CT_CHP | tmin | -16.03 | 0.2278 | False | 0.5993 | 0.38 |  | 11 | 0.9244 | 0.6245 | cold: zone p1 tmin (design heating day) |
| MISO-Indiana | ST_CHP | tmax | 32.2 | 0.0182 | False | 0.1513 | 0.12 | -0.1076 | 64 | 0.2008 | 0.1513 | hot: zone p95 tmax (design cooling day) |
| MISO-South | CC_CHP | tmax | 35.95 | 0.3798 | False | 0.7305 | 0.52 | -0.0855 | 55 | 0.6484 | 0.719 | hot: zone p95 tmax (design cooling day) |
| MISO-South | CC_CHP | tmin | -6.06 | 0.3698 | False | 0.7112 | 0.52 | 0.2091 | 11 | 0.6484 | 0.7196 | cold: zone p1 tmin (design heating day) |
| MISO-West | CC_CHP | tmax | 31.7 | 0.4338 | False | 0.8342 | 0.52 | 0.0608 | 46 | 0.4858 | 0.8342 | hot: zone p95 tmax (design cooling day) |
| MISO-West | CC_CHP | tmin | -22.13 | 0.4338 | False | 0.8342 | 0.52 | -0.8 | 5 | 0.4893 | 0.8342 | cold: zone p1 tmin (design heating day) |
| MISO-Indiana | CT_CHP | tmax | 32.2 | 0.1869 | False | 0.4919 | 0.38 | -0.0831 | 66 | 0.4726 | 0.3677 | hot: zone p95 tmax (design cooling day) |
| MISO-Indiana | CT_CHP | tmin | -16.6 | 0.1186 | False | 0.3121 | 0.38 | -0.6116 | 10 | 0.4797 | 0.3758 | cold: zone p1 tmin (design heating day) |
| MISO-Indiana | CC_CHP | tmax | 32.2 | 0.52 | False | 1.0 | 0.52 | 0.0813 | 66 | 0.5012 | 1.0 | hot: zone p95 tmax (design cooling day) |
| MISO-Indiana | CC_CHP | tmin | -16.6 | 0.52 | False | 1.0 | 0.52 | -0.0367 | 10 | 0.5016 | 1.0 | cold: zone p1 tmin (design heating day) |
| MISO-Illinois | CC_REGULAR | tmax | 32.8 | 0.52 | False | 1.0 | 0.52 | 0.1585 | 39 | 0.6683 | 1.0 | hot: zone p95 tmax (design cooling day) |
| MISO-Illinois | CC_REGULAR | tmin | -17.13 | 0.52 | False | 1.0 | 0.52 | 0.866 | 3 | 0.666 | 1.0 | cold: zone p1 tmin (design heating day) |

## NEISO

The NEISO temperature-limb table lives in the committed
`data/raw/reference/reliability_floor_coeffs_NEISO.csv` (derived 2026-06-30;
this report predates the per-ISO section for it). One limb was ADDED
2026-07-06 — the Connecticut ST_GAS **net-load** limb, the rule-19
re-grounding of the two disabled ST_GAS temperature limbs (tmax ρ=0.23 <
RHO_MIN; tmin n=8 < N_MIN — neither identified the driver). The NEISO
legacy-steam fleet (Montville) is committed by ISO-NE on tight-SYSTEM days,
both cold (Feb-2023 arctic blast) and hot (the post-Mystic Jun–Aug 2024/2025
heat events); daily peak net-load unifies the two (median committed day sits
at the p93 of daily-peak net-load). Same driver family as the CAISO CT limbs
(rebuild-plan review decision 2: a net-load limb carries no temperature gate);
all-24h boiler gate with the standard 48 h steam event bridging.

| zone | plant_class | driver | threshold | floor_pct | enabled | commit_frac | min_stable_pct | rho | n | baseline | baseline_commit | threshold_basis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Connecticut | ST_GAS | netload | 16.02 | 0.0336 | True | 0.2796 | 0.12 | 0.5096 | 329 | 0.005 | 0.013 | netload: system p70 daily-peak net-load (demand - VRE) GW |

Derivation notes (2026-07-06, this limb only): `_group_daily_cf` now counts a
day whose CAMPD rows are all-NaN grossLoad as OFFLINE (cf = 0, online_frac =
0) rather than dropping it — without this a single-plant class conditions
every flagged-day statistic on "was operating" and `commit_frac` saturates at
1.0 (the 2026-06-30 ST_GAS rows show the artifact: commit_frac =
baseline_commit = 1.0). The netload threshold percentile is computed on the
derivation span only (the zone-temperature file's 2023–2025 coverage), so the
2019–2021 EIA-930 backfill and the rule-22 holdout periods never enter it.
The committed temperature-limb rows are NOT re-derived here (rule 23 — their
source data did not change); a future full re-derivation will fold the
offline-day fix into every ISO's table.
