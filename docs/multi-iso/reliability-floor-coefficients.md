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
| NP15 | CT_PEAKER | netload | 0.0 | 0.2128 | False | 0.5601 | 0.38 | 0.2437 | 55 | 0.055 | 0.2431 | net-load ramp (duck-curve); per-zone net load not yet plumbed (Phase-2 placeholder) |
| NP15 | CC_REGULAR | tmax | 32.66 | 0.499 | False | 0.9596 | 0.52 | 0.1276 | 55 | 0.4276 | 0.7274 | hot: zone p95 tmax (design cooling day) |
| NP15 | CC_REGULAR | tmin | 1.75 | 0.4382 | False | 0.8426 | 0.52 | -0.2069 | 11 | 0.4392 | 0.738 | cold: zone p1 tmin (design heating day) |
| SP15 | ST_GAS | tmax | 26.7 | 0.0711 | False | 0.5924 | 0.12 | 0.2121 | 56 | 0.2196 | 0.4681 | hot: zone p95 tmax (design cooling day) |
| SP15 | ST_GAS | tmin | 5.66 | 0.0627 | False | 0.5227 | 0.12 | -0.0122 | 10 | 0.2268 | 0.4746 | cold: zone p1 tmin (design heating day) |
| SP15 | CT_PEAKER | netload | 0.0 | 0.1823 | False | 0.4797 | 0.38 | 0.2595 | 56 | 0.031 | 0.2873 | net-load ramp (duck-curve); per-zone net load not yet plumbed (Phase-2 placeholder) |
| SP15 | CC_REGULAR | tmax | 26.7 | 0.3171 | True | 0.6098 | 0.52 | 0.3211 | 56 | 0.2373 | 0.4751 | hot: zone p95 tmax (design cooling day) |
| SP15 | CC_REGULAR | tmin | 5.66 | 0.3292 | False | 0.6331 | 0.52 | 0.0061 | 10 | 0.2447 | 0.4806 | cold: zone p1 tmin (design heating day) |
| NP15 | CC_CHP | tmax | 32.66 | 0.2683 | False | 0.5159 | 0.52 | 0.0033 | 55 | 0.2994 | 0.4188 | hot: zone p95 tmax (design cooling day) |
| NP15 | CC_CHP | tmin | 1.75 | 0.2369 | False | 0.4556 | 0.52 | -0.3357 | 11 | 0.3033 | 0.4238 | cold: zone p1 tmin (design heating day) |
| ZP26 | CT_PEAKER | netload | 0.0 | 0.1442 | False | 0.3794 | 0.38 | 0.0699 | 42 | 0.0217 | 0.2651 | net-load ramp (duck-curve); per-zone net load not yet plumbed (Phase-2 placeholder) |
| NP15 | CT_CHP | netload | 0.0 | 0.1039 | False | 0.2735 | 0.38 | 0.3618 | 55 | 0.1114 | 0.1876 | net-load ramp (duck-curve); per-zone net load not yet plumbed (Phase-2 placeholder) |
| SP15 | CC_CHP | tmax | 26.7 | 0.0331 | False | 0.0637 | 0.52 | 0.4531 | 22 | 0.0183 | 0.0637 | hot: zone p95 tmax (design cooling day) |
| ZP26 | CT_CHP | netload | 0.0 | 0.0373 | False | 0.0982 | 0.38 | 0.263 | 58 | 0.017 | 0.0571 | net-load ramp (duck-curve); per-zone net load not yet plumbed (Phase-2 placeholder) |
| ZP26 | CC_REGULAR | tmax | 40.6 | 0.52 | False | 1.0 | 0.52 | 0.2568 | 59 | 0.3228 | 0.7967 | hot: zone p95 tmax (design cooling day) |
| ZP26 | CC_REGULAR | tmin | 1.1 | 0.52 | False | 1.0 | 0.52 | -0.3354 | 5 | 0.3399 | 0.8068 | cold: zone p1 tmin (design heating day) |
| ZP26 | CC_CHP | tmax | 40.6 | 0.52 | False | 1.0 | 0.52 | 0.038 | 46 | 0.7509 | 1.0 | hot: zone p95 tmax (design cooling day) |
| ZP26 | CC_CHP | tmin | 1.1 | 0.52 | False | 1.0 | 0.52 | -0.2236 | 5 | 0.7545 | 1.0 | cold: zone p1 tmin (design heating day) |

## PJM

| zone | plant_class | driver | threshold | floor_pct | enabled | commit_frac | min_stable_pct | rho | n | baseline | baseline_commit | threshold_basis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PJM_AEP_Ohio | CT_PEAKER | tmax | 32.2 | 0.3106 | False | 0.8172 | 0.38 | 0.1671 | 67 | 0.115 | 0.5521 | hot: zone p95 tmax (design cooling day) |
| PJM_EMAAC | ST_GAS | tmax | 33.3 | 0.0933 | True | 0.7775 | 0.12 | 0.5176 | 54 | 0.0673 | 0.5351 | hot: zone p95 tmax (design cooling day) |
| PJM_EMAAC | ST_GAS | tmin | -12.0 | 0.12 | False | 1.0 | 0.12 | -1.0 | 2 | 0.0852 | 0.5736 | cold: PJM Manual 13 Cold Weather Alert (tmin<=10F/-12C) |
| PJM_SWMAAC | COAL | tmax | 33.66 | 0.4 | False | 1.0 | 0.4 | 0.1943 | 58 | 0.3186 | 1.0 | hot: zone p95 tmax (design cooling day) |
| PJM_ComEd | COAL | tmax | 32.8 | 0.3833 | True | 0.9583 | 0.4 | 0.3956 | 58 | 0.2981 | 0.755 | hot: zone p95 tmax (design cooling day) |
| PJM_ComEd | COAL | tmin | -12.0 | 0.3823 | True | 0.9558 | 0.4 | 0.4603 | 38 | 0.2988 | 0.761 | cold: PJM Manual 13 Cold Weather Alert (tmin<=10F/-12C) |
| PJM_ComEd | CT_PEAKER | tmax | 32.8 | 0.2315 | False | 0.6092 | 0.38 | 0.054 | 59 | 0.0562 | 0.2573 | hot: zone p95 tmax (design cooling day) |
| PJM_ComEd | CT_PEAKER | tmin | -20.5 | 0.1659 | False | 0.4367 | 0.38 | -0.7379 | 4 | 0.0653 | 0.2817 | cold: PJM Manual 13 CT-mobilization tier (tmin<=-5F/-20.5C) |
| PJM_AEP_Ohio | COAL | tmax | 32.2 | 0.3808 | False | 0.9519 | 0.4 | -0.0136 | 67 | 0.4926 | 0.8388 | hot: zone p95 tmax (design cooling day) |
| PJM_AEP_Ohio | COAL | tmin | -12.0 | 0.3922 | False | 0.9804 | 0.4 | 0.2881 | 17 | 0.4983 | 0.8436 | cold: PJM Manual 13 Cold Weather Alert (tmin<=10F/-12C) |
| PJM_AEP_Ohio | ST_GAS | tmax | 32.2 | 0.1102 | False | 0.9187 | 0.12 | -0.0156 | 63 | 0.6033 | 0.9187 | hot: zone p95 tmax (design cooling day) |
| PJM_AEP_Ohio | ST_GAS | tmin | -12.0 | 0.1102 | False | 0.9187 | 0.12 | 0.0777 | 17 | 0.6113 | 0.9187 | cold: PJM Manual 13 Cold Weather Alert (tmin<=10F/-12C) |
| PJM_SWMAAC | CT_PEAKER | tmax | 33.66 | 0.3333 | False | 0.877 | 0.38 | 0.207 | 58 | 0.125 | 0.3273 | hot: zone p95 tmax (design cooling day) |
| PJM_SWMAAC | ST_GAS | tmax | 33.66 | 0.12 | False | 1.0 | 0.12 | 0.1996 | 54 | 0.2776 | 1.0 | hot: zone p95 tmax (design cooling day) |
| PJM_EMAAC | CT_PEAKER | tmax | 33.3 | 0.2838 | True | 0.7469 | 0.38 | 0.4772 | 55 | 0.2667 | 0.4246 | hot: zone p95 tmax (design cooling day) |
| PJM_EMAAC | CC_REGULAR | tmax | 33.3 | 0.5092 | True | 0.9793 | 0.52 | 0.5701 | 55 | 0.4087 | 0.7438 | hot: zone p95 tmax (design cooling day) |
| PJM_EMAAC | CC_REGULAR | tmin | -12.0 | 0.5124 | False | 0.9854 | 0.52 | 1.0 | 2 | 0.4228 | 0.7552 | cold: PJM Manual 13 Cold Weather Alert (tmin<=10F/-12C) |
| PJM_ATSI | CT_PEAKER | tmax | 30.71 | 0.3153 | False | 0.8298 | 0.38 | 0.2488 | 57 | 0.1748 | 0.5381 | hot: zone p95 tmax (design cooling day) |
| PJM_West_APS | CC_REGULAR | tmax | 31.7 | 0.5065 | False | 0.9741 | 0.52 | 0.2166 | 61 | 0.7338 | 0.8325 | hot: zone p95 tmax (design cooling day) |
| PJM_West_APS | CC_REGULAR | tmin | -12.0 | 0.4746 | False | 0.9126 | 0.52 | 0.4889 | 20 | 0.7391 | 0.8391 | cold: PJM Manual 13 Cold Weather Alert (tmin<=10F/-12C) |
| PJM_Central_PA | CT_PEAKER | tmax | 32.8 | 0.1367 | False | 0.3596 | 0.38 | 0.0237 | 58 | 0.11 | 0.2906 | hot: zone p95 tmax (design cooling day) |
| PJM_West_APS | COAL | tmax | 31.7 | 0.3547 | True | 0.8868 | 0.4 | 0.3691 | 61 | 0.3586 | 0.6394 | hot: zone p95 tmax (design cooling day) |
| PJM_West_APS | COAL | tmin | -12.0 | 0.3632 | False | 0.9079 | 0.4 | -0.068 | 20 | 0.3675 | 0.6484 | cold: PJM Manual 13 Cold Weather Alert (tmin<=10F/-12C) |
| PJM_Central_PA | ST_GAS | tmax | 32.8 | 0.1168 | True | 0.9737 | 0.12 | 0.3881 | 58 | 0.206 | 0.6123 | hot: zone p95 tmax (design cooling day) |
| PJM_Central_PA | ST_GAS | tmin | -12.0 | 0.0994 | False | 0.8285 | 0.12 | 0.9244 | 9 | 0.225 | 0.6304 | cold: PJM Manual 13 Cold Weather Alert (tmin<=10F/-12C) |
| PJM_West_APS | CT_PEAKER | tmax | 31.7 | 0.3208 | True | 0.8442 | 0.38 | 0.3812 | 61 | 0.2685 | 0.587 | hot: zone p95 tmax (design cooling day) |
| PJM_West_APS | ST_GAS | tmax | 31.7 | 0.12 | False | 1.0 | 0.12 | -0.0514 | 61 | 0.3854 | 1.0 | hot: zone p95 tmax (design cooling day) |
| PJM_West_APS | ST_GAS | tmin | -12.0 | 0.12 | False | 1.0 | 0.12 | -0.0076 | 20 | 0.4023 | 1.0 | cold: PJM Manual 13 Cold Weather Alert (tmin<=10F/-12C) |
| PJM_Central_PA | CC_REGULAR | tmax | 32.8 | 0.5181 | False | 0.9964 | 0.52 | 0.0262 | 58 | 0.7696 | 0.9317 | hot: zone p95 tmax (design cooling day) |
| PJM_Central_PA | CC_REGULAR | tmin | -12.0 | 0.5158 | False | 0.9918 | 0.52 | 0.7395 | 9 | 0.774 | 0.9347 | cold: PJM Manual 13 Cold Weather Alert (tmin<=10F/-12C) |
| PJM_Dominion | ST_GAS | tmax | 33.74 | 0.12 | False | 1.0 | 0.12 | 0.1475 | 40 | 0.2044 | 1.0 | hot: zone p95 tmax (design cooling day) |
| PJM_Dominion | CC_REGULAR | tmax | 33.74 | 0.5187 | False | 0.9976 | 0.52 | 0.1164 | 55 | 0.6993 | 0.8012 | hot: zone p95 tmax (design cooling day) |
| PJM_Dominion | CT_PEAKER | tmax | 33.74 | 0.3325 | False | 0.875 | 0.38 | 0.2004 | 55 | 0.2518 | 0.5442 | hot: zone p95 tmax (design cooling day) |
| PJM_Dominion | COAL | tmax | 33.74 | 0.2293 | False | 0.5732 | 0.4 | 0.2852 | 44 | 0.211 | 0.5732 | hot: zone p95 tmax (design cooling day) |
| PJM_EMAAC | CC_CHP | tmax | 33.3 | 0.4866 | False | 0.9358 | 0.52 | 0.1163 | 55 | 0.712 | 0.8224 | hot: zone p95 tmax (design cooling day) |
| PJM_EMAAC | CC_CHP | tmin | -12.0 | 0.4866 | False | 0.9358 | 0.52 | -1.0 | 2 | 0.7194 | 0.8279 | cold: PJM Manual 13 Cold Weather Alert (tmin<=10F/-12C) |
| PJM_EMAAC | CT_CHP | tmax | 33.3 | 0.1764 | True | 0.4641 | 0.38 | 0.4199 | 55 | 0.299 | 0.4026 | hot: zone p95 tmax (design cooling day) |
| PJM_Central_PA | COAL | tmax | 32.8 | 0.1885 | False | 0.4714 | 0.4 | 0.1489 | 58 | 0.3659 | 0.4092 | hot: zone p95 tmax (design cooling day) |
| PJM_Central_PA | COAL | tmin | -12.0 | 0.1349 | False | 0.3374 | 0.4 | -0.3025 | 9 | 0.3695 | 0.4132 | cold: PJM Manual 13 Cold Weather Alert (tmin<=10F/-12C) |
| PJM_EMAAC | ST_CHP | tmax | 33.3 | 0.0914 | False | 0.7618 | 0.12 | -0.0858 | 55 | 0.9788 | 0.7618 | hot: zone p95 tmax (design cooling day) |
| PJM_EMAAC | ST_CHP | tmin | -12.0 | 0.0914 | False | 0.7618 | 0.12 |  | 2 | 0.9797 | 0.7618 | cold: PJM Manual 13 Cold Weather Alert (tmin<=10F/-12C) |
| PJM_Dominion | CC_CHP | tmax | 33.74 | 0.52 | False | 1.0 | 0.52 | 0.3481 | 55 | 0.4904 | 1.0 | hot: zone p95 tmax (design cooling day) |
| PJM_ComEd | CC_CHP | tmax | 32.8 | 0.5121 | False | 0.9848 | 0.52 | 0.1917 | 52 | 0.3316 | 0.9848 | hot: zone p95 tmax (design cooling day) |
| PJM_ComEd | CC_CHP | tmin | -12.0 | 0.5121 | True | 0.9848 | 0.52 | 0.3776 | 38 | 0.3374 | 0.9848 | cold: PJM Manual 13 Cold Weather Alert (tmin<=10F/-12C) |
| PJM_Central_PA | ST_CHP | tmax | 32.8 | 0.0046 | False | 0.0385 | 0.12 |  | 58 | 0.9998 | 0.0385 | hot: zone p95 tmax (design cooling day) |
| PJM_Central_PA | CT_CHP | tmax | 32.8 | 0.3349 | False | 0.8814 | 0.38 | -0.3076 | 58 | 0.6668 | 0.8814 | hot: zone p95 tmax (design cooling day) |
| PJM_SWMAAC | CC_CHP | tmax | 33.66 | 0.4918 | False | 0.9458 | 0.52 | 0.238 | 58 | 0.2229 | 0.9458 | hot: zone p95 tmax (design cooling day) |
| PJM_ComEd | CC_REGULAR | tmax | 32.8 | 0.5018 | False | 0.9651 | 0.52 | 0.224 | 59 | 0.5467 | 0.7983 | hot: zone p95 tmax (design cooling day) |
| PJM_ComEd | CC_REGULAR | tmin | -12.0 | 0.4509 | False | 0.8671 | 0.52 | -0.0338 | 38 | 0.5539 | 0.8052 | cold: PJM Manual 13 Cold Weather Alert (tmin<=10F/-12C) |
| PJM_AEP_Ohio | CC_REGULAR | tmax | 32.2 | 0.5031 | False | 0.9674 | 0.52 | 0.1393 | 67 | 0.7582 | 0.914 | hot: zone p95 tmax (design cooling day) |
| PJM_AEP_Ohio | CC_REGULAR | tmin | -12.0 | 0.5018 | False | 0.9649 | 0.52 | 0.2614 | 17 | 0.7621 | 0.9165 | cold: PJM Manual 13 Cold Weather Alert (tmin<=10F/-12C) |
| PJM_ATSI | CC_REGULAR | tmax | 30.71 | 0.5173 | False | 0.9949 | 0.52 | 0.2164 | 57 | 0.7783 | 0.9031 | hot: zone p95 tmax (design cooling day) |
| PJM_ATSI | CC_REGULAR | tmin | -12.0 | 0.52 | False | 1.0 | 0.52 | -0.0485 | 20 | 0.7817 | 0.9061 | cold: PJM Manual 13 Cold Weather Alert (tmin<=10F/-12C) |
| PJM_SWMAAC | CC_REGULAR | tmax | 33.66 | 0.517 | False | 0.9942 | 0.52 | 0.2354 | 58 | 0.4671 | 0.8507 | hot: zone p95 tmax (design cooling day) |
| PJM_West_APS | CC_CHP | tmax | 31.7 | 0.52 | False | 1.0 | 0.52 | -0.2945 | 61 | 0.5384 | 1.0 | hot: zone p95 tmax (design cooling day) |
| PJM_West_APS | CC_CHP | tmin | -12.0 | 0.52 | False | 1.0 | 0.52 | 0.0234 | 20 | 0.5333 | 1.0 | cold: PJM Manual 13 Cold Weather Alert (tmin<=10F/-12C) |

## MISO

| zone | plant_class | driver | threshold | floor_pct | enabled | commit_frac | min_stable_pct | rho | n | baseline | baseline_commit | threshold_basis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MISO-South | ST_GAS | tmax | 35.95 | 0.103 | False | 0.8579 | 0.12 | 0.2654 | 55 | 0.3694 | 0.647 | hot: zone p95 tmax (design cooling day) |
| MISO-South | ST_GAS | tmin | -6.06 | 0.1093 | False | 0.9111 | 0.12 | 0.5182 | 11 | 0.3808 | 0.655 | cold: zone p1 tmin (design heating day) |
| MISO-Central | COAL | tmax | 31.3 | 0.3777 | False | 0.9443 | 0.4 | 0.1465 | 55 | 0.5451 | 0.9059 | hot: zone p95 tmax (design cooling day) |
| MISO-Central | COAL | tmin | -16.07 | 0.3839 | False | 0.9598 | 0.4 | 0.2636 | 11 | 0.5502 | 0.9073 | cold: zone p1 tmin (design heating day) |
| MISO-Central | CT_PEAKER | tmax | 31.3 | 0.2758 | False | 0.7257 | 0.38 | 0.0681 | 55 | 0.2859 | 0.3387 | hot: zone p95 tmax (design cooling day) |
| MISO-Central | CT_PEAKER | tmin | -16.07 | 0.1745 | False | 0.4592 | 0.38 | 0.0818 | 11 | 0.2983 | 0.3571 | cold: zone p1 tmin (design heating day) |
| MISO-Central | ST_GAS | tmax | 31.3 | 0.0567 | False | 0.4722 | 0.12 | -0.0218 | 55 | 0.18 | 0.3869 | hot: zone p95 tmax (design cooling day) |
| MISO-Central | ST_GAS | tmin | -16.07 | 0.0428 | False | 0.3564 | 0.12 | -0.0091 | 11 | 0.1864 | 0.3915 | cold: zone p1 tmin (design heating day) |
| MISO-Central | CC_REGULAR | tmax | 31.3 | 0.4282 | False | 0.8234 | 0.52 | -0.046 | 55 | 0.6757 | 0.736 | hot: zone p95 tmax (design cooling day) |
| MISO-Central | CC_REGULAR | tmin | -16.07 | 0.3897 | False | 0.7494 | 0.52 | 0.2273 | 11 | 0.6825 | 0.7403 | cold: zone p1 tmin (design heating day) |
| MISO-North | CT_PEAKER | tmax | 32.19 | 0.2344 | False | 0.6169 | 0.38 | 0.1244 | 55 | 0.0895 | 0.2354 | hot: zone p95 tmax (design cooling day) |
| MISO-North | CT_PEAKER | tmin | -19.56 | 0.06 | False | 0.158 | 0.38 | 0.1091 | 11 | 0.0979 | 0.2562 | cold: zone p1 tmin (design heating day) |
| MISO-North | COAL | tmax | 32.19 | 0.3662 | False | 0.9154 | 0.4 | 0.0055 | 55 | 0.5497 | 0.8083 | hot: zone p95 tmax (design cooling day) |
| MISO-North | COAL | tmin | -19.56 | 0.3779 | False | 0.9447 | 0.4 | -0.1 | 11 | 0.556 | 0.8124 | cold: zone p1 tmin (design heating day) |
| MISO-North | ST_CHP | tmax | 32.19 | 0.0044 | False | 0.0364 | 0.12 | -0.3714 | 6 | 0.0043 | 0.0364 | hot: zone p95 tmax (design cooling day) |
| MISO-North | ST_GAS | tmax | 32.19 | 0.0665 | True | 0.5541 | 0.12 | 0.3475 | 54 | 0.1256 | 0.3284 | hot: zone p95 tmax (design cooling day) |
| MISO-North | ST_GAS | tmin | -19.56 | 0.0508 | False | 0.4233 | 0.12 | 0.0818 | 11 | 0.1312 | 0.3389 | cold: zone p1 tmin (design heating day) |
| MISO-South | CT_CHP | tmax | 35.95 | 0.1383 | False | 0.3639 | 0.38 | -0.063 | 55 | 0.5496 | 0.3639 | hot: zone p95 tmax (design cooling day) |
| MISO-South | CT_CHP | tmin | -6.06 | 0.1383 | False | 0.3639 | 0.38 | 0.1636 | 11 | 0.5473 | 0.3639 | cold: zone p1 tmin (design heating day) |
| MISO-Central | ST_CHP | tmax | 31.3 | 0.0411 | False | 0.3422 | 0.12 | 0.0799 | 55 | 0.2842 | 0.338 | hot: zone p95 tmax (design cooling day) |
| MISO-Central | ST_CHP | tmin | -16.07 | 0.0448 | False | 0.3737 | 0.12 | 0.8337 | 11 | 0.2838 | 0.3378 | cold: zone p1 tmin (design heating day) |
| MISO-South | CC_REGULAR | tmax | 35.95 | 0.5147 | False | 0.9898 | 0.52 | -0.2132 | 55 | 0.5502 | 0.8498 | hot: zone p95 tmax (design cooling day) |
| MISO-South | CC_REGULAR | tmin | -6.06 | 0.5 | False | 0.9615 | 0.52 | 0.0 | 11 | 0.5579 | 0.8557 | cold: zone p1 tmin (design heating day) |
| MISO-South | CT_PEAKER | tmax | 35.95 | 0.2892 | False | 0.7611 | 0.38 | 0.1182 | 55 | 0.3928 | 0.3615 | hot: zone p95 tmax (design cooling day) |
| MISO-South | CT_PEAKER | tmin | -6.06 | 0.2656 | False | 0.699 | 0.38 | 0.7 | 11 | 0.4024 | 0.3783 | cold: zone p1 tmin (design heating day) |
| MISO-North | CC_REGULAR | tmax | 32.19 | 0.4784 | False | 0.9201 | 0.52 | -0.1034 | 55 | 0.5085 | 0.7496 | hot: zone p95 tmax (design cooling day) |
| MISO-North | CC_REGULAR | tmin | -19.56 | 0.3909 | False | 0.7517 | 0.52 | 0.2909 | 11 | 0.5212 | 0.7584 | cold: zone p1 tmin (design heating day) |
| MISO-South | COAL | tmax | 35.95 | 0.3927 | True | 0.9818 | 0.4 | 0.3307 | 55 | 0.4475 | 0.779 | hot: zone p95 tmax (design cooling day) |
| MISO-South | COAL | tmin | -6.06 | 0.3869 | False | 0.9673 | 0.4 | 0.3146 | 11 | 0.4592 | 0.7873 | cold: zone p1 tmin (design heating day) |
| MISO-Central | CC_CHP | tmax | 31.3 | 0.4275 | False | 0.8221 | 0.52 | -0.013 | 55 | 0.5575 | 0.8044 | hot: zone p95 tmax (design cooling day) |
| MISO-Central | CC_CHP | tmin | -16.07 | 0.4232 | False | 0.8138 | 0.52 | 0.0 | 11 | 0.5591 | 0.8052 | cold: zone p1 tmin (design heating day) |
| MISO-South | ST_CHP | tmax | 35.95 | 0.0542 | False | 0.4519 | 0.12 |  | 55 | 1.0 | 0.4519 | hot: zone p95 tmax (design cooling day) |
| MISO-South | ST_CHP | tmin | -6.06 | 0.0542 | False | 0.4519 | 0.12 |  | 11 | 1.0 | 0.4519 | cold: zone p1 tmin (design heating day) |
| MISO-Central | CT_CHP | tmax | 31.3 | 0.2075 | False | 0.546 | 0.38 | -0.14 | 55 | 0.8688 | 0.4695 | hot: zone p95 tmax (design cooling day) |
| MISO-Central | CT_CHP | tmin | -16.07 | 0.1693 | False | 0.4456 | 0.38 | -0.1619 | 11 | 0.8736 | 0.4737 | cold: zone p1 tmin (design heating day) |
| MISO-South | CC_CHP | tmax | 35.95 | 0.4395 | False | 0.8451 | 0.52 | -0.0855 | 55 | 0.7502 | 0.8318 | hot: zone p95 tmax (design cooling day) |
| MISO-South | CC_CHP | tmin | -6.06 | 0.4279 | False | 0.8228 | 0.52 | 0.2091 | 11 | 0.7501 | 0.8326 | cold: zone p1 tmin (design heating day) |
| MISO-North | CC_CHP | tmax | 32.19 | 0.3546 | False | 0.6819 | 0.52 | 0.0261 | 39 | 0.3963 | 0.6819 | hot: zone p95 tmax (design cooling day) |
| MISO-North | CC_CHP | tmin | -19.56 | 0.3546 | False | 0.6819 | 0.52 | 0.2 | 4 | 0.3998 | 0.6819 | cold: zone p1 tmin (design heating day) |

## NYISO

| zone | plant_class | driver | threshold | floor_pct | enabled | commit_frac | min_stable_pct | rho | n | baseline | baseline_commit | threshold_basis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Capital_Hudson | ST_GAS | tmax | 31.1 | 0.0973 | True | 0.8105 | 0.12 | 0.3917 | 65 | 0.1298 | 0.4854 | hot: zone p95 tmax (design cooling day) |
| Capital_Hudson | ST_GAS | tmin | -14.9 | 0.0807 | False | 0.6729 | 0.12 | 0.4545 | 11 | 0.142 | 0.526 | cold: zone p1 tmin (design heating day) |
| Capital_Hudson | CT_PEAKER | tmax | 31.1 | 0.1957 | False | 0.515 | 0.38 | 0.0459 | 11 | 0.0193 | 0.447 | hot: zone p95 tmax (design cooling day) |
| Capital_Hudson | CT_PEAKER | tmin | -14.9 | 0.2794 | False | 0.7353 | 0.38 | -1.0 | 2 | 0.0224 | 0.4481 | cold: zone p1 tmin (design heating day) |
| NYC | ST_GAS | tmax | 31.7 | 0.1195 | True | 0.996 | 0.12 | 0.3305 | 65 | 0.1839 | 0.8694 | hot: zone p95 tmax (design cooling day) |
| NYC | ST_GAS | tmin | -7.72 | 0.106 | False | 0.8833 | 0.12 | 0.0335 | 11 | 0.207 | 0.8769 | cold: zone p1 tmin (design heating day) |
| NYC | CT_CHP | tmax | 31.7 | 0.3303 | False | 0.8693 | 0.38 | 0.3064 | 65 | 0.6873 | 0.8693 | hot: zone p95 tmax (design cooling day) |
| NYC | CT_CHP | tmin | -7.72 | 0.3303 | False | 0.8693 | 0.38 | -0.2635 | 11 | 0.6897 | 0.8693 | cold: zone p1 tmin (design heating day) |
| NYC | ST_CHP | tmax | 31.7 | 0.12 | False | 1.0 | 0.12 | 0.3181 | 65 | 0.7388 | 1.0 | hot: zone p95 tmax (design cooling day) |
| NYC | ST_CHP | tmin | -7.72 | 0.12 | False | 1.0 | 0.12 | -0.2635 | 11 | 0.7447 | 1.0 | cold: zone p1 tmin (design heating day) |
| NYC | CT_PEAKER | tmax | 31.7 | 0.1833 | True | 0.4824 | 0.38 | 0.4741 | 65 | 0.0506 | 0.2601 | hot: zone p95 tmax (design cooling day) |
| NYC | CT_PEAKER | tmin | -7.72 | 0.1186 | False | 0.3122 | 0.38 | -0.3833 | 11 | 0.0594 | 0.2734 | cold: zone p1 tmin (design heating day) |
| NYC | CC_REGULAR | tmax | 31.7 | 0.3763 | True | 0.7236 | 0.52 | 0.3092 | 65 | 0.7655 | 0.6762 | hot: zone p95 tmax (design cooling day) |
| NYC | CC_REGULAR | tmin | -7.72 | 0.3763 | False | 0.7236 | 0.52 | 0.2779 | 11 | 0.7773 | 0.6786 | cold: zone p1 tmin (design heating day) |
| Long_Island | CT_PEAKER | tmax | 30.0 | 0.3443 | False | 0.9061 | 0.38 | 0.2536 | 66 | 0.3619 | 0.6852 | hot: zone p95 tmax (design cooling day) |
| Long_Island | CT_PEAKER | tmin | -8.8 | 0.2574 | False | 0.6773 | 0.38 | 0.2283 | 11 | 0.3873 | 0.6987 | cold: zone p1 tmin (design heating day) |
| Long_Island | ST_GAS | tmax | 30.0 | 0.12 | True | 1.0 | 0.12 | 0.3498 | 66 | 0.2381 | 0.9227 | hot: zone p95 tmax (design cooling day) |
| Long_Island | ST_GAS | tmin | -8.8 | 0.1182 | False | 0.9851 | 0.12 | 0.7397 | 11 | 0.257 | 0.9268 | cold: zone p1 tmin (design heating day) |
| Upstate_West | ST_GAS | tmax | 30.0 | 0.1013 | False | 0.8445 | 0.12 | 0.2227 | 62 | 0.5687 | 0.7461 | hot: zone p95 tmax (design cooling day) |
| Upstate_West | ST_GAS | tmin | -13.8 | 0.1067 | False | 0.8889 | 0.12 | 0.2773 | 9 | 0.57 | 0.7504 | cold: zone p1 tmin (design heating day) |
| Capital_Hudson | CC_REGULAR | tmax | 31.1 | 0.5003 | False | 0.9622 | 0.52 | -0.0019 | 66 | 0.5423 | 0.8025 | hot: zone p95 tmax (design cooling day) |
| Capital_Hudson | CC_REGULAR | tmin | -14.9 | 0.3406 | False | 0.655 | 0.52 | -0.6364 | 11 | 0.5575 | 0.8137 | cold: zone p1 tmin (design heating day) |
| Upstate_West | CT_PEAKER | tmax | 30.0 | 0.38 | False | 1.0 | 0.38 | -0.0936 | 29 | 0.6584 | 1.0 | hot: zone p95 tmax (design cooling day) |
| Upstate_West | CT_PEAKER | tmin | -13.8 | 0.38 | False | 1.0 | 0.38 | -0.1566 | 8 | 0.6202 | 1.0 | cold: zone p1 tmin (design heating day) |
| Long_Island | CC_REGULAR | tmax | 30.0 | 0.4735 | True | 0.9105 | 0.52 | 0.3436 | 66 | 0.5312 | 0.7278 | hot: zone p95 tmax (design cooling day) |
| Long_Island | CC_REGULAR | tmin | -8.8 | 0.407 | False | 0.7826 | 0.52 | 0.1963 | 11 | 0.5385 | 0.7384 | cold: zone p1 tmin (design heating day) |
| Upstate_West | CC_REGULAR | tmax | 30.0 | 0.246 | True | 0.4731 | 0.52 | 0.3706 | 58 | 0.1123 | 0.3285 | hot: zone p95 tmax (design cooling day) |
| Upstate_West | CC_REGULAR | tmin | -13.8 | 0.2527 | False | 0.4859 | 0.52 | 0.4538 | 9 | 0.1176 | 0.337 | cold: zone p1 tmin (design heating day) |
| Capital_Hudson | CC_CHP | tmax | 31.1 | 0.4481 | True | 0.8618 | 0.52 | 0.3439 | 66 | 0.3369 | 0.5229 | hot: zone p95 tmax (design cooling day) |
| Capital_Hudson | CC_CHP | tmin | -14.9 | 0.2295 | False | 0.4414 | 0.52 | 0.5091 | 11 | 0.3534 | 0.546 | cold: zone p1 tmin (design heating day) |
| Upstate_West | CC_CHP | tmax | 30.0 | 0.432 | True | 0.8309 | 0.52 | 0.4145 | 63 | 0.43 | 0.6502 | hot: zone p95 tmax (design cooling day) |
| Upstate_West | CC_CHP | tmin | -13.8 | 0.4297 | False | 0.8263 | 0.52 | -0.1681 | 9 | 0.4351 | 0.6595 | cold: zone p1 tmin (design heating day) |
| NYC | CC_CHP | tmax | 31.7 | 0.1634 | False | 0.3141 | 0.52 | 0.1684 | 65 | 0.1943 | 0.2775 | hot: zone p95 tmax (design cooling day) |
| NYC | CC_CHP | tmin | -7.72 | 0.1445 | False | 0.2778 | 0.52 | -0.345 | 11 | 0.1953 | 0.2797 | cold: zone p1 tmin (design heating day) |
| Long_Island | CT_CHP | tmax | 30.0 | 0.3553 | False | 0.9349 | 0.38 | 0.032 | 65 | 0.9843 | 0.9349 | hot: zone p95 tmax (design cooling day) |
| Long_Island | CT_CHP | tmin | -8.8 | 0.3553 | False | 0.9349 | 0.38 | 0.1481 | 11 | 0.9837 | 0.9349 | cold: zone p1 tmin (design heating day) |

## NEISO

| zone | plant_class | driver | threshold | floor_pct | enabled | commit_frac | min_stable_pct | rho | n | baseline | baseline_commit | threshold_basis |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Connecticut | ST_GAS | tmax | 32.2 | 0.12 | False | 1.0 | 0.12 | 0.2307 | 41 | 0.3414 | 1.0 | hot: zone p95 tmax (design cooling day) |
| Connecticut | ST_GAS | tmin | -14.3 | 0.12 | False | 1.0 | 0.12 | 0.7178 | 8 | 0.4139 | 1.0 | cold: zone p1 tmin (design heating day) |
| Connecticut | CC_REGULAR | tmax | 32.2 | 0.5178 | False | 0.9959 | 0.52 | 0.0161 | 64 | 0.659 | 0.8797 | hot: zone p95 tmax (design cooling day) |
| Connecticut | CC_REGULAR | tmin | -14.3 | 0.4745 | False | 0.9126 | 0.52 | -0.4118 | 9 | 0.6676 | 0.8863 | cold: zone p1 tmin (design heating day) |
| Boston | CC_CHP | tmax | 30.73 | 0.52 | False | 1.0 | 0.52 | -0.3058 | 55 | 0.9797 | 1.0 | hot: zone p95 tmax (design cooling day) |
| Boston | CC_CHP | tmin | -10.5 | 0.52 | False | 1.0 | 0.52 |  | 9 | 0.9789 | 1.0 | cold: zone p1 tmin (design heating day) |
| Boston | CT_PEAKER | tmax | 30.73 | 0.2703 | True | 0.7113 | 0.38 | 0.4286 | 55 | 0.0851 | 0.5404 | hot: zone p95 tmax (design cooling day) |
| Boston | CT_PEAKER | tmin | -10.5 | 0.2196 | False | 0.5778 | 0.38 | 0.1429 | 9 | 0.0909 | 0.5513 | cold: zone p1 tmin (design heating day) |
| Central | CC_REGULAR | tmax | 29.92 | 0.499 | True | 0.9596 | 0.52 | 0.337 | 58 | 0.3349 | 0.6265 | hot: zone p95 tmax (design cooling day) |
| Central | CC_REGULAR | tmin | -11.69 | 0.3173 | False | 0.6103 | 0.52 | 0.5727 | 11 | 0.35 | 0.6445 | cold: zone p1 tmin (design heating day) |
| North | COAL | tmax | 30.02 | 0.4 | False | 1.0 | 0.4 | 0.244 | 43 | 0.6821 | 1.0 | hot: zone p95 tmax (design cooling day) |
| North | COAL | tmin | -17.92 | 0.4 | False | 1.0 | 0.4 |  | 7 | 0.6604 | 1.0 | cold: zone p1 tmin (design heating day) |
| Connecticut | CT_PEAKER | tmax | 32.2 | 0.2595 | True | 0.6828 | 0.38 | 0.3847 | 62 | 0.0541 | 0.539 | hot: zone p95 tmax (design cooling day) |
| Boston | CC_REGULAR | tmax | 30.73 | 0.5103 | False | 0.9813 | 0.52 | 0.2401 | 55 | 0.2624 | 0.7357 | hot: zone p95 tmax (design cooling day) |
| Boston | CC_REGULAR | tmin | -10.5 | 0.4549 | False | 0.8747 | 0.52 | -0.4202 | 9 | 0.273 | 0.747 | cold: zone p1 tmin (design heating day) |
| Connecticut | CC_CHP | tmax | 32.2 | 0.2554 | False | 0.4912 | 0.52 | 0.3099 | 41 | 0.0968 | 0.4912 | hot: zone p95 tmax (design cooling day) |
| Connecticut | CC_CHP | tmin | -14.3 | 0.2554 | False | 0.4912 | 0.52 |  | 2 | 0.0959 | 0.4912 | cold: zone p1 tmin (design heating day) |
| Central | CC_CHP | tmax | 29.92 | 0.52 | False | 1.0 | 0.52 | 0.3329 | 52 | 0.2172 | 1.0 | hot: zone p95 tmax (design cooling day) |
| North | CT_PEAKER | tmax | 30.02 | 0.38 | False | 1.0 | 0.38 | 0.463 | 30 | 0.0735 | 1.0 | hot: zone p95 tmax (design cooling day) |
| Central | CT_PEAKER | tmax | 29.92 | 0.337 | False | 0.8869 | 0.38 | 0.2101 | 56 | 0.5139 | 0.8869 | hot: zone p95 tmax (design cooling day) |
| Central | CT_PEAKER | tmin | -11.69 | 0.337 | False | 0.8869 | 0.38 | -0.1539 | 5 | 0.5723 | 0.8869 | cold: zone p1 tmin (design heating day) |
| Connecticut | CT_CHP | tmax | 32.2 | 0.0964 | False | 0.2536 | 0.38 | -0.0025 | 56 | 0.1585 | 0.2536 | hot: zone p95 tmax (design cooling day) |
| North | CC_REGULAR | tmax | 30.02 | 0.4863 | False | 0.9351 | 0.52 | 0.2128 | 55 | 0.373 | 0.7255 | hot: zone p95 tmax (design cooling day) |
| North | CC_REGULAR | tmin | -17.92 | 0.4182 | False | 0.8043 | 0.52 | -0.1818 | 11 | 0.3843 | 0.7353 | cold: zone p1 tmin (design heating day) |
