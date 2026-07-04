# Sensitivity tornado — ERCOT forecast 2026-2028

*Generated 2026-07-04 by `scripts/run_sensitivity_tornado.py` (PP-3.1 / CLAUDE.md rule 15 DOF ledger).*

One-at-a-time (OAT) +/- band sensitivity of the highest-leverage forecast knobs. Each row is the full-model swing from the parameter's low band to its high band with every other parameter held at default. This is **measurement, not tuning** — no calibrated value or keeper was changed.

## Run configuration

- **ISO:** ERCOT
- **Horizon:** 2026-2028 (sequential years, rule 12)
- **Fleet representation:** legacy equal-width bins (`use_campd_bins=False`)
- **Base overrides:** `{'use_campd_bins': False}`

### Base case

| Metric | Value |
|---|---|
| CO2 final year (Mt) | 173.9424 |
| CO2 horizon total (Mt) | 494.0633 |
| Avg price ($/MWh) | 23.09 |
| Thermal retired (GW) | 0.0 |

## Tornado rankings

`delta = high - low`. Rows sorted by |delta| (most sensitive first).

### CO2 final year (Mt)

| Rank | Parameter | Cat. | Low | High | delta | |delta| |
|---:|---|---|---:|---:|---:|---:|
| 1 | Demand growth path | forecast | 154.4308 | 210.4929 | +56.06 | 56.06 |
| 2 | Henry Hub gas price level | forecast | 166.7273 | 177.2514 | +10.52 | 10.52 |
| 3 | Carbon price path | forecast | 173.9424 | 164.247 | -9.695 | 9.695 |
| 4 | Renewable capacity-factor scalar | dispatch | 179.0148 | 169.6224 | -9.392 | 9.392 |
| 5 | Battery dispatch adder | dispatch | 173.9424 | 174.6217 | +0.6793 | 0.6793 |
| 6 | Storage deployment pace | forecast | 174.0769 | 173.7869 | -0.29 | 0.29 |
| 7 | Coal FOM multiplier (retirement) | forecast | 173.9424 | 173.9424 | +0 | 0 |
| 8 | Retirement reliability floor | forecast | 173.9424 | 173.9424 | +0 | 0 |
| 9 | Gas-CC consecutive-loss retirement years | forecast | 173.9424 | 173.9424 | +0 | 0 |
| 10 | Coal going-forward FOM bar | forecast | 173.9424 | 173.9424 | +0 | 0 |
| 11 | Gas-CC going-forward FOM bar | forecast | 173.9424 | 173.9424 | +0 | 0 |
| 12 | Gas-CT going-forward FOM bar | forecast | 173.9424 | 173.9424 | +0 | 0 |
| 13 | Renewable buildout pace | forecast | 173.9424 | 173.9424 | +0 | 0 |
| 14 | Value of lost load (price cap) | dispatch | 173.9424 | 173.9424 | +0 | 0 |
| 15 | Coal consecutive-loss retirement years | forecast | 173.9424 | 173.9424 | +0 | 0 |

### CO2 horizon total (Mt)

| Rank | Parameter | Cat. | Low | High | delta | |delta| |
|---:|---|---|---:|---:|---:|---:|
| 1 | Demand growth path | forecast | 451.7178 | 569.4435 | +117.7 | 117.7 |
| 2 | Henry Hub gas price level | forecast | 471.59450000000004 | 502.1957 | +30.6 | 30.6 |
| 3 | Renewable capacity-factor scalar | dispatch | 507.92470000000003 | 480.93129999999996 | -26.99 | 26.99 |
| 4 | Carbon price path | forecast | 494.0633 | 478.5933 | -15.47 | 15.47 |
| 5 | Battery dispatch adder | dispatch | 494.0633 | 495.71720000000005 | +1.654 | 1.654 |
| 6 | Storage deployment pace | forecast | 494.34069999999997 | 493.5405 | -0.8002 | 0.8002 |
| 7 | Coal FOM multiplier (retirement) | forecast | 494.0633 | 494.0633 | +0 | 0 |
| 8 | Retirement reliability floor | forecast | 494.0633 | 494.0633 | +0 | 0 |
| 9 | Gas-CC consecutive-loss retirement years | forecast | 494.0633 | 494.0633 | +0 | 0 |
| 10 | Coal going-forward FOM bar | forecast | 494.0633 | 494.0633 | +0 | 0 |
| 11 | Gas-CC going-forward FOM bar | forecast | 494.0633 | 494.0633 | +0 | 0 |
| 12 | Gas-CT going-forward FOM bar | forecast | 494.0633 | 494.0633 | +0 | 0 |
| 13 | Renewable buildout pace | forecast | 494.0633 | 494.0633 | +0 | 0 |
| 14 | Value of lost load (price cap) | dispatch | 494.0633 | 494.0633 | +0 | 0 |
| 15 | Coal consecutive-loss retirement years | forecast | 494.0633 | 494.0633 | +0 | 0 |

### Avg price ($/MWh)

| Rank | Parameter | Cat. | Low | High | delta | |delta| |
|---:|---|---|---:|---:|---:|---:|
| 1 | Henry Hub gas price level | forecast | 18.343333333333334 | 24.0 | +5.657 | 5.657 |
| 2 | Carbon price path | forecast | 23.09 | 26.563333333333333 | +3.473 | 3.473 |
| 3 | Demand growth path | forecast | 22.650000000000002 | 24.349999999999998 | +1.7 | 1.7 |
| 4 | Renewable capacity-factor scalar | dispatch | 23.47666666666667 | 22.72333333333333 | -0.7533 | 0.7533 |
| 5 | Battery dispatch adder | dispatch | 23.09 | 23.223333333333333 | +0.1333 | 0.1333 |
| 6 | Storage deployment pace | forecast | 23.073333333333334 | 23.116666666666664 | +0.0433 | 0.0433 |
| 7 | Coal FOM multiplier (retirement) | forecast | 23.09 | 23.09 | +0 | 0 |
| 8 | Retirement reliability floor | forecast | 23.09 | 23.09 | +0 | 0 |
| 9 | Gas-CC consecutive-loss retirement years | forecast | 23.09 | 23.09 | +0 | 0 |
| 10 | Coal going-forward FOM bar | forecast | 23.09 | 23.09 | +0 | 0 |
| 11 | Gas-CC going-forward FOM bar | forecast | 23.09 | 23.09 | +0 | 0 |
| 12 | Gas-CT going-forward FOM bar | forecast | 23.09 | 23.09 | +0 | 0 |
| 13 | Renewable buildout pace | forecast | 23.09 | 23.09 | +0 | 0 |
| 14 | Value of lost load (price cap) | dispatch | 23.09 | 23.09 | +0 | 0 |
| 15 | Coal consecutive-loss retirement years | forecast | 23.09 | 23.09 | +0 | 0 |

### Thermal retired (GW)

| Rank | Parameter | Cat. | Low | High | delta | |delta| |
|---:|---|---|---:|---:|---:|---:|
| 1 | Henry Hub gas price level | forecast | 0.0 | 0.0 | +0 | 0 |
| 2 | Demand growth path | forecast | 0.0 | 0.0 | +0 | 0 |
| 3 | Carbon price path | forecast | 0.0 | 0.0 | +0 | 0 |
| 4 | Coal FOM multiplier (retirement) | forecast | 0.0 | 0.0 | +0 | 0 |
| 5 | Retirement reliability floor | forecast | 0.0 | 0.0 | +0 | 0 |
| 6 | Gas-CC consecutive-loss retirement years | forecast | 0.0 | 0.0 | +0 | 0 |
| 7 | Coal going-forward FOM bar | forecast | 0.0 | 0.0 | +0 | 0 |
| 8 | Gas-CC going-forward FOM bar | forecast | 0.0 | 0.0 | +0 | 0 |
| 9 | Gas-CT going-forward FOM bar | forecast | 0.0 | 0.0 | +0 | 0 |
| 10 | Renewable buildout pace | forecast | 0.0 | 0.0 | +0 | 0 |
| 11 | Renewable capacity-factor scalar | dispatch | 0.0 | 0.0 | +0 | 0 |
| 12 | Storage deployment pace | forecast | 0.0 | 0.0 | +0 | 0 |
| 13 | Battery dispatch adder | dispatch | 0.0 | 0.0 | +0 | 0 |
| 14 | Value of lost load (price cap) | dispatch | 0.0 | 0.0 | +0 | 0 |
| 15 | Coal consecutive-loss retirement years | forecast | 0.0 | 0.0 | +0 | 0 |

## Parameter bands

| Parameter | Base | Low | High | Unit | Cat. | Citation |
|---|---|---|---|---|---|---|
| Henry Hub gas price level | mid path (~3.0) | 2.55 (-15%) | 3.45 (+15%) | $/MMBtu | forecast | EIA AEO2025 (HENRY_HUB_TRAJECTORIES, constants.py:673) |
| Demand growth path | mid | low | high | path | forecast | EIA STEO / ERCOT CDR (DEMAND_GROWTH_RATES, constants.py:598) |
| Carbon price path | zero | zero | high | path | forecast | RFF (CARBON_PRICE_PATHS, constants.py:1200) |
| Coal FOM multiplier (retirement) | 1.30 | 1.15 | 1.45 | x | forecast | Lazard LCOE 2024 (scenarios.py:136) |
| Retirement reliability floor | 0.15 | 0.10 | 0.20 | fraction | forecast | Reserve-margin heuristic (scenarios.py:144) |
| Gas-CC consecutive-loss retirement years | 3 | 2 | 4 | years | forecast | Retirement screen threshold (scenarios.py:129-135) |
| Coal going-forward FOM bar | 40.0 | 30.0 | 50.0 | $/kW-yr | forecast | NREL ATB legacy-steam (scenarios.py:146-162) |
| Gas-CC going-forward FOM bar | 12.0 | 9.0 | 15.0 | $/kW-yr | forecast | NREL ATB (scenarios.py:146-162) |
| Gas-CT going-forward FOM bar | 8.0 | 6.0 | 10.0 | $/kW-yr | forecast | NREL ATB (scenarios.py:146-162) |
| Renewable buildout pace | mid | slow | aggressive | pace | forecast | NREL ATB entry (renewable_buildout_pace, scenarios.py:65) |
| Renewable capacity-factor scalar | 1.00 | 0.95 | 1.05 | x | dispatch | Model design scalar (scenarios.py:1635) |
| Storage deployment pace | mid | low | high | pace | forecast | EIA-860 storage pipeline (storage_deployment, scenarios.py:66) |
| Battery dispatch adder | 0.0 | 0.0 | 5.0 | $/MWh | dispatch | Xu et al. 2018 cycle-aging (scenarios.py:2526) |
| Value of lost load (price cap) | 5000 | 4000 | 6000 | $/MWh | dispatch | ISO price cap (iso_configs.py; scenarios.py:41) |
| Coal consecutive-loss retirement years | 1 | 1 | 2 | years | forecast | Retirement screen threshold (scenarios.py:129) |

**Band notes:**
- *Henry Hub gas price level:* Flat pin via gas_price_override isolates the level swing.
- *Carbon price path:* One-sided: forecast default carbon is zero (the floor).
- *Battery dispatch adder:* One-sided: adder floor is 0.
- *Coal consecutive-loss retirement years:* One-sided: coal floor is 1 year.

## Interpretation & caveats

- **OAT ignores interactions.** A tornado shows marginal leverage around the base point only; it does not capture joint moves (e.g. gas x carbon). Use the structured scenario matrix (PP-1.1) for interactions.
- **Short horizon.** Retirement signals accumulate over the run; a 3-year window captures near-term exits, not the 2040 fleet. Re-run with a longer `--end-year` for mid-century leverage.
- **Fleet granularity.** The legacy-bin default trades per-plant fidelity for runtime; the leverage *ranking* is the deliverable and is robust to it.
- **One-sided bands** (carbon, battery adder, coal retire-years) sit at a natural floor; their delta is a one-directional response, not a symmetric band.

## DOF-ledger feed

The forecast-category parameters with the largest CO2 leverage are the free degrees of freedom most in need of an identification source in the keeper attestation (CLAUDE.md rule 21). Ranked CO2-final leverage:

1. **Demand growth path** — 56.06 Mt swing (154.4308 -> 210.4929 Mt)
2. **Henry Hub gas price level** — 10.52 Mt swing (166.7273 -> 177.2514 Mt)
3. **Carbon price path** — 9.695 Mt swing (173.9424 -> 164.247 Mt)
4. **Storage deployment pace** — 0.29 Mt swing (174.0769 -> 173.7869 Mt)
5. **Coal FOM multiplier (retirement)** — 0 Mt swing (173.9424 -> 173.9424 Mt)
6. **Retirement reliability floor** — 0 Mt swing (173.9424 -> 173.9424 Mt)
7. **Gas-CC consecutive-loss retirement years** — 0 Mt swing (173.9424 -> 173.9424 Mt)
8. **Coal going-forward FOM bar** — 0 Mt swing (173.9424 -> 173.9424 Mt)
