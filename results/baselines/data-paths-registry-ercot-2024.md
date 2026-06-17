# Golden baseline — ERCOT 2024 backcast (data-paths-registry wave)

Reference backcast captured **before/after** the central path-registry refactor
(`src/market_sim/config/paths.py`). The refactor is behavior-preserving: this
output was verified **byte-for-byte identical** between the refactor branch
(rebased onto `main`) and plain `origin/main` (`cba4b8c`). Use it as the golden
baseline for later data-layout waves (raw/clean migration) — those waves must
reproduce these numbers exactly unless an input genuinely changes.

- Command: `python scripts/run_calibration.py --iso ERCOT --year 2024`
- Date captured: 2026-06-17 (rebased onto main @ `cba4b8c`)
- Solver status: **Optimal**
- Baseline file: `results/baselines/data-paths-registry-ercot-2024.txt`
- Baseline md5: `3f66af9d6c9785a8131d897bc0acd2ef`

## Headline diagnostics

### Generation by fuel
| fuel    | model TWh | EIA-923 TWh | diff % |
|---------|-----------|-------------|--------|
| coal    | 47.51     | 57.62       | -17.5  |
| gas_cc  | 192.03    | 200.46      | -4.2   |
| gas_ct  | 13.25     | 20.29       | -34.7  |
| gas_st  | 14.95     | 18.66       | -19.9  |
| hydro   | 0.46      | —           | —      |
| nuclear | 38.35     | 38.61       | -0.7   |
| oil     | 0.02      | —           | —      |
| solar   | 47.07     | 40.08       | +17.5  |
| wind    | 109.39    | 111.88      | -2.2   |
| TOTAL   | 463.04    | 487.60      | -5.0   |

### CO2 emissions
- model **154.58 Mt**

### System price
- SYSTEM avg **35.63 $/MWh**, 0 negative-price hours (Panhandle 3031 neg-price hrs).

### Hourly dispatch correlation (vs EIA-930)
| fuel | pearson r | nrmse | model TWh | EIA TWh |
|------|-----------|-------|-----------|---------|
| coal | 0.892     | 0.254 | 47.51     | 58.77   |
| gas  | 0.987     | 0.104 | 220.22    | 203.68  |
