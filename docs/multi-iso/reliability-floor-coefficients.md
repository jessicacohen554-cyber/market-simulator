# Temperature reliability-floor coefficients

Derived by `scripts/derive_reliability_coeffs.py`. `floor_pct = commit_frac x min_stable_pct` (never residual-tuned, CLAUDE.md #9/#11). A limb is `enabled` only when `rho >= 0.3`, `n >= 30`, and `floor_pct > baseline`; weak limbs ship OFF but stay visible below.

## ERCOT

| zone | plant_class | driver | threshold | floor_pct | enabled | commit_frac | min_stable_pct | rho | n | baseline |
|---|---|---|---|---|---|---|---|---|---|---|
| North | COAL | tmax | 25.0 | 0.3272 | False | 0.9348 | 0.35 | 0.471 | 681 | 0.595 |
| North | COAL | tmin | 0.0 | 0.3378 | False | 0.965 | 0.35 | 0.3034 | 53 | 0.6175 |
| South | CT_PEAKER | tmax | 25.0 | 0.0 | False | 0.3243 | 0.0 | 0.3476 | 844 | 0.0299 |
| South | CT_PEAKER | tmin | 0.0 | 0.0 | False | 0.4827 | 0.0 | -0.4857 | 6 | 0.0418 |
| South | CC_REGULAR | tmax | 25.0 | 0.0 | False | 0.6741 | 0.0 | 0.5789 | 872 | 0.2399 |
| South | CC_REGULAR | tmin | 0.0 | 0.0 | False | 1.0 | 0.0 | -0.7143 | 6 | 0.2832 |
| North | ST_GAS | tmax | 25.0 | 0.0 | False | 0.704 | 0.0 | 0.5244 | 649 | 0.0783 |
| North | ST_GAS | tmin | 0.0 | 0.0 | False | 0.7062 | 0.0 | 0.4288 | 51 | 0.137 |
| Houston | ST_GAS | tmax | 25.0 | 0.0 | False | 0.4943 | 0.0 | 0.3923 | 559 | 0.1201 |
| Houston | ST_GAS | tmin | 0.0 | 0.0 | False | 0.4943 | 0.0 | 0.3151 | 11 | 0.1595 |
| Houston | CT_PEAKER | tmax | 25.0 | 0.0056 | False | 0.6934 | 0.0081 | 0.5413 | 781 | 0.0693 |
| Houston | CT_PEAKER | tmin | 0.0 | 0.0059 | False | 0.7242 | 0.0081 | 0.2914 | 15 | 0.0967 |
| Houston | CC_REGULAR | tmax | 25.0 | 0.0 | False | 0.8151 | 0.0 | 0.6623 | 781 | 0.3344 |
| Houston | CC_REGULAR | tmin | 0.0 | 0.0 | False | 0.9494 | 0.0 | 0.7693 | 15 | 0.3927 |
| Houston | COAL | tmax | 25.0 | 0.25 | False | 1.0 | 0.25 | 0.5616 | 781 | 0.53 |
| Houston | COAL | tmin | 0.0 | 0.25 | False | 1.0 | 0.25 | 0.0701 | 15 | 0.6342 |
| West | CT_PEAKER | tmax | 25.0 | 0.0 | False | 0.5858 | 0.0 | 0.0726 | 618 | 0.107 |
| West | CT_PEAKER | tmin | 0.0 | 0.0 | False | 0.5038 | 0.0 | 0.172 | 86 | 0.1151 |
| Northeast | ST_GAS | tmax | 25.0 | 0.0 | False | 1.0 | 0.0 | 0.4558 | 516 | 0.2525 |
| Northeast | ST_GAS | tmin | 0.0 | 0.0 | False | 1.0 | 0.0 | 0.5246 | 36 | 0.2743 |
| South_Central | CT_PEAKER | tmax | 25.0 | 0.0 | False | 0.6292 | 0.0 | 0.4853 | 676 | 0.0727 |
| South_Central | CT_PEAKER | tmin | 0.0 | 0.0 | False | 0.5868 | 0.0 | 0.3282 | 34 | 0.0868 |
| South_Central | ST_GAS | tmax | 25.0 | 0.0 | False | 0.7869 | 0.0 | 0.6616 | 771 | 0.2109 |
| South_Central | ST_GAS | tmin | 0.0 | 0.0 | False | 0.754 | 0.0 | 0.3932 | 43 | 0.2787 |
| North | CT_PEAKER | tmax | 25.0 | 0.0 | False | 0.2754 | 0.0 | 0.4293 | 565 | 0.005 |
| North | CT_PEAKER | tmin | 0.0 | 0.0 | False | 0.2754 | 0.0 | 0.3554 | 35 | 0.0079 |
| South_Central | CC_REGULAR | tmax | 25.0 | 0.0776 | False | 0.9052 | 0.0857 | 0.7016 | 771 | 0.4594 |
| South_Central | CC_REGULAR | tmin | 0.0 | 0.0824 | False | 0.9614 | 0.0857 | 0.1474 | 43 | 0.5376 |
| Northeast | COAL | tmax | 25.0 | 0.25 | False | 1.0 | 0.25 | 0.4795 | 689 | 0.496 |
| Northeast | COAL | tmin | 0.0 | 0.25 | False | 1.0 | 0.25 | 0.1596 | 50 | 0.5338 |
| South | COAL | tmax | 25.0 | 0.2819 | False | 0.8675 | 0.325 | 0.5098 | 763 | 0.5654 |
| South | COAL | tmin | 0.0 | 0.2597 | False | 0.799 | 0.325 | -0.6571 | 6 | 0.5836 |
| South_Central | COAL | tmax | 25.0 | 0.222 | False | 0.8882 | 0.25 | 0.6271 | 771 | 0.4442 |
| South_Central | COAL | tmin | 0.0 | 0.2407 | False | 0.963 | 0.25 | 0.371 | 43 | 0.47 |
| Houston | CT_CHP | tmax | 25.0 | 0.2749 | False | 0.4531 | 0.6067 | 0.2681 | 781 | 0.3447 |
| Houston | CT_CHP | tmin | 0.0 | 0.2792 | False | 0.4602 | 0.6067 | -0.1158 | 15 | 0.3296 |
| South | CC_CHP | tmax | 25.0 | 0.1742 | True | 0.2903 | 0.6 | 0.3939 | 868 | 0.1609 |
| South | CC_CHP | tmin | 0.0 | 0.1742 | False | 0.2903 | 0.6 | -0.0286 | 6 | 0.1709 |
| Houston | CC_CHP | tmax | 25.0 | 0.4715 | False | 0.7858 | 0.6 | 0.6263 | 781 | 0.5542 |
| Houston | CC_CHP | tmin | 0.0 | 0.4743 | False | 0.7906 | 0.6 | 0.324 | 15 | 0.5584 |
| North | CC_REGULAR | tmax | 25.0 | 0.0 | False | 0.8399 | 0.0 | 0.6144 | 681 | 0.4286 |
| North | CC_REGULAR | tmin | 0.0 | 0.0 | False | 0.8711 | 0.0 | 0.2922 | 53 | 0.4992 |
| West | CC_CHP | tmax | 25.0 | 0.6 | False | 1.0 | 0.6 | -0.128 | 373 | 0.2374 |
| West | CC_CHP | tmin | 0.0 | 0.6 | False | 1.0 | 0.6 | -0.2213 | 36 | 0.242 |
| Northeast | CC_REGULAR | tmax | 25.0 | 0.0 | False | 1.0 | 0.0 | 0.2102 | 487 | 0.5391 |
| Northeast | CC_REGULAR | tmin | 0.0 | 0.0 | False | 1.0 | 0.0 | 0.1146 | 51 | 0.5312 |
| West | CC_REGULAR | tmax | 25.0 | 0.0 | False | 0.9037 | 0.0 | 0.187 | 677 | 0.588 |
| West | CC_REGULAR | tmin | 0.0 | 0.0 | False | 0.905 | 0.0 | 0.3585 | 100 | 0.6513 |
