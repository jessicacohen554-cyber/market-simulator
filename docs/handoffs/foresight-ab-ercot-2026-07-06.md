# Foresight A/B — ERCOT forecast 2026-2040

*Generated 2026-07-06 by `scripts/run_foresight_ab.py` (capacity-economics plan 2026-07 §2.4, W2-P3 stage 3).*

Four arms x two demand-growth paths, legacy equal-width bins (runtime fidelity trade, as the sensitivity tornado), adequacy backstop ON so its forced-build MW — the myopia tell — is observable. Forecast probes only: nothing here is a backcast or a dashboard run. Metrics window 2030-2040.

## Arms

| Arm | Overrides |
|---|---|
| base | `(myopic base)` |
| ewma | `{'entry_price_signal_alpha': 0.6}` |
| lookahead | `{'entry_lookahead_reprice': True}` |
| both | `{'entry_price_signal_alpha': 0.6, 'entry_lookahead_reprice': True}` |

## Growth path: high

| Arm | cum CO2 (Mt) | dCO2 vs base | coal TWh | gas_cc TWh | gas_ct+st TWh | retired GW | entered GW | backstop MW | floor MW (max yr) | mean $ | P95 $ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| base | 3090.63 | — | 764.92 | 4151.7 | 1155.37 | 12.1 | 101.0 | 31828.3 | 92215.1 | 825.42 | 2746.14 |
| ewma | 3237.78 | +4.8% | 817.29 | 4129.91 | 1341.64 | 12.1 | 89.0 | 35920.2 | 92809.8 | 763.58 | 2519.84 |
| lookahead | 3651.13 | +18.1% | 1057.64 | 4132.37 | 1665.14 | 0.0 | 57.0 | 91152.5 | 32961.1 | 486.27 | 2747.55 |
| both | 3366.04 | +8.9% | 999.51 | 4767.15 | 821.11 | 0.0 | 79.0 | 69225.0 | 32359.7 | 462.94 | 2645.31 |

### Decision inputs (high)

```json
{
 "ewma": {
  "co2_mt_cum": 3237.78,
  "delta_co2_mt": 147.15,
  "delta_co2_pct": 4.76,
  "backstop_mw_total": 35920.2,
  "material": false,
  "reduces_backstop": false,
  "preferred": false
 },
 "lookahead": {
  "co2_mt_cum": 3651.13,
  "delta_co2_mt": 560.5,
  "delta_co2_pct": 18.14,
  "backstop_mw_total": 91152.5,
  "material": true,
  "reduces_backstop": false,
  "preferred": false
 },
 "both": {
  "co2_mt_cum": 3366.04,
  "delta_co2_mt": 275.41,
  "delta_co2_pct": 8.91,
  "backstop_mw_total": 69225.0,
  "material": true,
  "reduces_backstop": false,
  "preferred": false
 },
 "base": {
  "co2_mt_cum": 3090.63,
  "backstop_mw_total": 31828.3
 }
}
```

## Growth path: mid

| Arm | cum CO2 (Mt) | dCO2 vs base | coal TWh | gas_cc TWh | gas_ct+st TWh | retired GW | entered GW | backstop MW | floor MW (max yr) | mean $ | P95 $ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| base | 2788.35 | — | 1000.42 | 3360.5 | 719.0 | 0.0 | 15.0 | 47087.2 | 86985.7 | 29.87 | 39.3 |
| ewma | 2793.42 | +0.2% | 1000.41 | 3364.44 | 725.71 | 0.0 | 15.0 | 43929.5 | 85166.3 | 29.88 | 39.25 |
| lookahead | 2627.92 | -5.8% | 971.18 | 3405.04 | 459.83 | 0.0 | 39.0 | 43156.3 | 70919.9 | 31.0 | 38.45 |
| both | 2605.96 | -6.5% | 953.72 | 3548.64 | 367.14 | 0.0 | 37.0 | 44135.7 | 75729.4 | 30.85 | 37.8 |

### Decision inputs (mid)

```json
{
 "ewma": {
  "co2_mt_cum": 2793.42,
  "delta_co2_mt": 5.07,
  "delta_co2_pct": 0.18,
  "backstop_mw_total": 43929.5,
  "material": false,
  "reduces_backstop": true,
  "preferred": false
 },
 "lookahead": {
  "co2_mt_cum": 2627.92,
  "delta_co2_mt": -160.43,
  "delta_co2_pct": -5.75,
  "backstop_mw_total": 43156.3,
  "material": true,
  "reduces_backstop": true,
  "preferred": true
 },
 "both": {
  "co2_mt_cum": 2605.96,
  "delta_co2_mt": -182.39,
  "delta_co2_pct": -6.54,
  "backstop_mw_total": 44135.7,
  "material": true,
  "reduces_backstop": true,
  "preferred": true
 },
 "base": {
  "co2_mt_cum": 2788.35,
  "backstop_mw_total": 47087.2
 }
}
```

## Decision rule (plan §2.4)

Promote the simplest material arm (>5% cumulative 2030-2040 fossil CO2 move vs base, preferred if it also reduces backstop MW). Component 1 of the lookahead arm — known-demand substitution in the peak-anchored mechanisms — was promoted unconditionally in stage 2 (a bug-class fix) and is ON in every arm here, including base. If nothing is material, entry_lookahead_reprice stays default-off as a designed probe and the negative result is recorded.
