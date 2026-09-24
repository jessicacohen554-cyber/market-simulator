### Criterion status, keeper → re-solve (both scored on HEAD's benchmark)

| criterion | keeper | re-solve |
|---|---|---|
| fuelmix | PASS | FAIL |
| sysvol | PASS | PASS |
| price_mean | PASS | PASS |
| price_shape | PASS | PASS |
| price_tail | CAVEAT | CAVEAT |
| dispatch_corr | PASS | PASS |
| governance | PASS | PASS |
| forced_share | PASS | PASS |

Determination: keeper **CALIBRATED** → re-solve **NOT-YET**

### C1 class TWh by year (model − actual), keeper → re-solve; gated rows only

| year | class | actual TWh | keeper model | re-solve model | Δ model | keeper err | re-solve err | band | status |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 2022 | CC_CHP | 8.13 | 8.93 | 8.94 | +0.01 | +0.80 | +0.81 | ±5.01 TWh | PASS→PASS |
| 2022 | CC_REGULAR | 51.61 | 52.86 | 51.86 | -1.00 | +1.25 | +0.25 | ±5.01 TWh | PASS→PASS |
| 2022 | COAL_BIT | 0.07 | 0.00 | 0.00 | +0.00 | -0.07 | -0.07 | ±5.01 TWh | PASS→PASS |
| 2022 | CT_PEAKER | 4.48 | 2.80 | 3.04 | +0.24 | -1.68 | -1.44 | ±5.01 TWh | PASS→PASS |
| 2022 | ST_CHP | 0.05 | 0.00 | 0.00 | +0.00 | -0.05 | -0.05 | ±5.01 TWh | PASS→PASS |
| 2022 | ST_GAS | 1.29 | 0.33 | 0.37 | +0.04 | -0.96 | -0.92 | ±5.01 TWh | PASS→PASS |
| 2023 | CC_CHP | 7.74 | 8.48 | 8.41 | -0.07 | +0.74 | +0.67 | ±5.27 TWh | PASS→PASS |
| 2023 | CC_REGULAR | 51.84 | 47.44 | 46.48 | -0.96 | -4.40 | -5.36 | ±5.27 TWh | PASS→FAIL |
| 2023 | COAL_BIT | 0.06 | 0.00 | 0.00 | +0.00 | -0.06 | -0.06 | ±5.27 TWh | PASS→PASS |
| 2023 | CT_PEAKER | 4.13 | 2.02 | 2.39 | +0.36 | -2.10 | -1.74 | ±5.27 TWh | PASS→PASS |
| 2023 | ST_CHP | 0.06 | 0.00 | 0.00 | +0.00 | -0.06 | -0.06 | ±5.27 TWh | PASS→PASS |
| 2023 | ST_GAS | 1.31 | 0.08 | 0.10 | +0.01 | -1.23 | -1.21 | ±5.27 TWh | PASS→PASS |
| 2024 | CC_CHP | 6.79 | 7.52 | 7.49 | -0.03 | +0.73 | +0.70 | ±5.29 TWh | PASS→PASS |
| 2024 | CC_REGULAR | 45.99 | 45.56 | 44.76 | -0.81 | -0.43 | -1.24 | ±5.29 TWh | PASS→PASS |
| 2024 | COAL_BIT | 0.07 | 0.00 | 0.00 | +0.00 | -0.07 | -0.07 | ±5.29 TWh | PASS→PASS |
| 2024 | CT_PEAKER | 4.33 | 1.60 | 2.11 | +0.50 | -2.73 | -2.22 | ±5.29 TWh | PASS→PASS |
| 2024 | ST_CHP | 0.03 | 0.00 | 0.00 | +0.00 | -0.03 | -0.03 | ±5.29 TWh | PASS→PASS |
| 2024 | ST_GAS | 0.12 | 0.09 | 0.08 | -0.01 | -0.03 | -0.04 | ±5.29 TWh | PASS→PASS |

### C3a mean LMP $/MWh (load-wtd, vs RT)

| year | key | actual | keeper | re-solve | keeper status → re-solve |
|---|---|---|---|---|---|
| 2022 |  | 84.49 | +6.9% | +7.3% | PASS→PASS |
| 2023 |  | 54.17 | +3.0% | +4.4% | PASS→PASS |
| 2024 |  | 34.65 | +7.3% | +7.6% | PASS→PASS |
| 2025 |  | 34.42 | +7.4% | +9.4% | PASS→PASS |

### C3b monthly NRMSE

| year | key | actual | keeper | re-solve | keeper status → re-solve |
|---|---|---|---|---|---|
| 2022 |  | None | NRMSE 0.089 | NRMSE 0.092 | PASS→PASS |
| 2023 |  | None | NRMSE 0.076 | NRMSE 0.084 | PASS→PASS |
| 2024 |  | None | NRMSE 0.138 | NRMSE 0.131 | PASS→PASS |
| 2025 |  | None | NRMSE 0.103 | NRMSE 0.118 | PASS→PASS |

### C3c hours >$200

| year | key | actual | keeper | re-solve | keeper status → re-solve |
|---|---|---|---|---|---|
| 2022 |  | 510.0 | model 483h [energy-only LMP] vs RT actual 510h (0.95×, >$200) | model 482h [energy-only LMP] vs RT actual 510h (0.95×, >$200) | PASS→PASS |
| 2023 |  | 47.0 | model 46h [energy-only LMP] vs RT actual 47h (0.98×, >$200); RT coverage 99.5% — count is a lower bound | model 45h [energy-only LMP] vs RT actual 47h (0.96×, >$200); RT coverage 99.5% — count is a lower bound | PASS→PASS |
| 2024 |  | 35.0 | model 0h [energy-only LMP] vs RT actual 35h (0.00×, >$200) | model 0h [energy-only LMP] vs RT actual 35h (0.00×, >$200) | CAVEAT→CAVEAT |
| 2025 |  | 8.0 | model 0h [energy-only LMP] vs RT actual 8h (small-count |Δ|≤10h, >$200) | model 0h [energy-only LMP] vs RT actual 8h (small-count |Δ|≤10h, >$200) | PASS→PASS |

### C2 system volume

| year | key | actual | keeper | re-solve | keeper status → re-solve |
|---|---|---|---|---|---|
| 2022 | gas | 65.56 | all classes in band (C1) | all classes in band (C1) | PASS→PASS |
| 2023 | gas | 65.08 | all classes in band (C1) | C1 flags: CC_REGULAR | PASS→PASS |
| 2024 | gas | 57.26 | all classes in band (C1) | all classes in band (C1) | PASS→PASS |

### C4 hourly r / NRMSE

| year | key | actual | keeper | re-solve | keeper status → re-solve |
|---|---|---|---|---|---|
| 2022 | gas | None | r=0.889, NRMSE=0.27 | r=0.893, NRMSE=0.266 | PASS→PASS |
| 2023 | gas | None | r=0.882, NRMSE=0.294 | r=0.884, NRMSE=0.297 | PASS→PASS |
| 2024 | gas | None | r=0.919, NRMSE=0.254 | r=0.916, NRMSE=0.259 | PASS→PASS |
| 2025 | gas | None | r=0.879, NRMSE=0.296 | r=0.882, NRMSE=0.295 | PASS→PASS |

### All-class model TWh, re-solve − keeper

cols ['year', 'pass', 'klass', 'hour', 'mw']

### All-class model TWh (P1), re-solve − keeper

| class | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| CC_REGULAR | -1.031 | -0.974 | -0.807 | -1.615 |
| CC_CHP | +0.285 | -0.071 | -0.034 | -0.030 |
| hydro | -0.000 | +0.000 | -0.054 | +0.000 |
| solar | -0.013 | +0.006 | -0.286 | +0.003 |
| ST_GAS | +0.042 | +0.015 | -0.007 | +0.004 |
| CT_CHP | -0.027 | +0.020 | +0.142 | +0.071 |
| CT_PEAKER | +0.264 | +0.371 | +0.504 | +0.421 |
| import | +0.433 | +0.610 | +0.376 | +1.162 |
