# Foresight A/B — ERCOT forecast 2026-2040

*Generated 2026-07-07 by `scripts/run_foresight_ab.py` (capacity-economics plan 2026-07 §2.4, W2-P3 stage 3).*

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
| base | 3117.92 | — | 777.67 | 4147.15 | 1179.46 | 11.41 | 101.0 | 28512.5 | 74199.9 | 807.32 | 2746.14 |
| ewma | 3261.21 | +4.6% | 829.6 | 4126.33 | 1359.74 | 6.32 | 89.0 | 32675.8 | 78113.5 | 755.12 | 2519.9 |
| lookahead | 2908.92 | -6.7% | 899.35 | 4344.56 | 509.45 | 0.0 | 165.0 | 0.0 | 0.0 | 423.07 | 2644.39 |
| both | 2809.38 | -9.9% | 887.79 | 4112.05 | 506.63 | 0.0 | 154.0 | 0.0 | 0.0 | 423.68 | 2644.37 |

### Decision inputs (high)

```json
{
 "ewma": {
  "co2_mt_cum": 3261.21,
  "delta_co2_mt": 143.29,
  "delta_co2_pct": 4.6,
  "backstop_mw_total": 32675.8,
  "material": false,
  "reduces_backstop": false,
  "preferred": false
 },
 "lookahead": {
  "co2_mt_cum": 2908.92,
  "delta_co2_mt": -209.0,
  "delta_co2_pct": -6.7,
  "backstop_mw_total": 0.0,
  "material": true,
  "reduces_backstop": true,
  "preferred": true
 },
 "both": {
  "co2_mt_cum": 2809.38,
  "delta_co2_mt": -308.54,
  "delta_co2_pct": -9.9,
  "backstop_mw_total": 0.0,
  "material": true,
  "reduces_backstop": true,
  "preferred": true
 },
 "base": {
  "co2_mt_cum": 3117.92,
  "backstop_mw_total": 28512.5
 }
}
```

## Growth path: mid

| Arm | cum CO2 (Mt) | dCO2 vs base | coal TWh | gas_cc TWh | gas_ct+st TWh | retired GW | entered GW | backstop MW | floor MW (max yr) | mean $ | P95 $ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| base | 2791.2 | — | 1001.14 | 3363.04 | 717.54 | 0.0 | 15.0 | 40968.0 | 69639.7 | 30.05 | 39.67 |
| ewma | 2787.75 | -0.1% | 1002.11 | 3360.72 | 709.81 | 0.0 | 15.0 | 38637.8 | 69823.5 | 30.12 | 39.96 |
| lookahead | 1942.75 | -30.4% | 287.89 | 3927.61 | 213.04 | 12.68 | 91.0 | 0.0 | 4488.0 | 157.42 | 1166.36 |
| both | 2363.53 | -15.3% | 819.94 | 3810.73 | 77.37 | 0.0 | 72.0 | 0.0 | 0.0 | 26.8 | 36.34 |

### Decision inputs (mid)

```json
{
 "ewma": {
  "co2_mt_cum": 2787.75,
  "delta_co2_mt": -3.45,
  "delta_co2_pct": -0.12,
  "backstop_mw_total": 38637.8,
  "material": false,
  "reduces_backstop": true,
  "preferred": false
 },
 "lookahead": {
  "co2_mt_cum": 1942.75,
  "delta_co2_mt": -848.45,
  "delta_co2_pct": -30.4,
  "backstop_mw_total": 0.0,
  "material": true,
  "reduces_backstop": true,
  "preferred": true
 },
 "both": {
  "co2_mt_cum": 2363.53,
  "delta_co2_mt": -427.67,
  "delta_co2_pct": -15.32,
  "backstop_mw_total": 0.0,
  "material": true,
  "reduces_backstop": true,
  "preferred": true
 },
 "base": {
  "co2_mt_cum": 2791.2,
  "backstop_mw_total": 40968.0
 }
}
```

## Decision rule (plan §2.4)

Promote the simplest material arm (>5% cumulative 2030-2040 fossil CO2 move vs base, preferred if it also reduces backstop MW). Component 1 of the lookahead arm — known-demand substitution in the peak-anchored mechanisms — was promoted unconditionally in stage 2 (a bug-class fix) and is ON in every arm here, including base. If nothing is material, entry_lookahead_reprice stays default-off as a designed probe and the negative result is recorded.
