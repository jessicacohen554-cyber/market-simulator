# ERCOT calibration — best config so far

Keeper: **e2 4 / dashboard `run79 storage retune`** (2026-06-11, bundle
`results/calibration/e2_4_retune`, highspy 1.14.0), **revalidated
unchanged on post-E3 main** (bundle
`results/calibration/run80a_code_baseline` reproduces every class-year).
The run-80/81 probes (dashboard `run80 lignite 1.15`, `run81 prb floor`),
the run-82 Jacobian joint move, and the run-84 coal-sigmoid probe (lignite
balanced at +5.4/−5.0/+2.1 but CT_PEAKER/ST_GAS 2024 collateral beyond the
bar) were all net-negative and reverted — see the Runs 80–81, Run 82 and
Run 84 calibration-log entries.
Reproduce with:

```
python scripts/run_calibration_full.py --year 2023 2024 2025 \
    --storage-daily-cycling --battery-adder 10 \
    --offer-curve-delta-json <run79 deltas>   # meta.json offer_curve_deltas
```

## Config (the knobs that matter)

- `td_loss_factor = 0.0` (EIA-930 demand is generation-side; no gross-up).
- Locked tier-pass-2 family: per-plant CAMPD coal must-run, gas-keyed PRB
  passthrough sigmoid (baseload + follower tiers), `coal_drop_pof`,
  historic outage overlay, per-plant monthly coal pricing — all defaults of
  `run_calibration_full.py`.
- `storage_daily_cycling = on` (SOC returns to its day-start level every
  24 h — bounds single-LP perfect foresight to within-day arbitrage).
- **`battery_dispatch_adder = 10.0` $/MWh discharged** (E2, 2026-06-11):
  reduced-form BESS cycling degradation + ancillary-service opportunity
  cost; lands 2025 battery discharge at −1.5% vs the EIA-930 measured
  5.44 TWh (the LP over-cycled +48% without it). Same magnitude as the PJM
  `pumped_storage_dispatch_adder`.
- Nuclear: per-year EIA-923 monthly CF overlay (`NUCLEAR_MONTHLY_CF_BY_YEAR`)
  — nuclear −0.7% every year; validate with
  `scripts/derive_nuclear_monthly_cf.py --check`.
- Offer-curve deltas vs the calibrated defaults (recorded in the bundle's
  `meta.json`): CC_REGULAR {committed −0.05, econ_low −0.10, econ_high
  −0.45, peak +0.25}; CC_CHP {econ_high +0.43, peak −0.50, pct_peaking −4};
  CT_CHP {committed −0.20, econ_low −0.08, econ_high +0.10, peak −0.08};
  CT_PEAKER {committed −0.34, econ_high +0.20}; ST_GAS {committed −0.385,
  econ_low −0.13, econ_high −0.35, peak −1.0}; COAL_PRB {committed −0.04,
  econ_low −0.30, econ_high +0.44, peak +0.082}; COAL_LIGNITE {committed
  −0.07, econ_low +0.076, econ_high −0.037}.

## Results (P1, vs EIA-923 incl. BTM add-back)

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| CC_REGULAR | −1.3% | +2.9% | +0.9% |
| CC_CHP | +1.1% | +0.8% | +2.0% |
| COAL_PRB | −0.8% | −9.9% | −1.5% |
| COAL_LIGNITE | −12.8% | −23.8% | +0.7% |
| CT_PEAKER | −2.6% | −12.8% | −2.9% |
| ST_GAS | +7.4% | −2.7% | +2.8% |
| nuclear | −0.7% | −0.7% | −0.7% |
| coal hourly r (NRMSE) | 0.940 (0.171) | 0.905 (0.229) | 0.808 (0.162) |
| battery dis. vs EIA-930 | n/a | −55% (19% cov. window) | **−1.5%** |

Unserved energy 0.000 in all years. 2024's coal deficit (PRB −9.9, lignite
−23.8) is the known cheap-gas-year signature → E1 (measured monthly gas
backport). Full pass narrative: `docs/calibration-log.md`, "ERCOT E2" entry
(including the solver-version reproducibility caveat — `meta.json` now
records `highspy_version`).

## History

The previous keeper config (flat `coal_prb_passthrough = 0.83`, commitment
pass, 2023/2024 only — git `249fec7`) predates the sigmoid passthrough
family and the Run-60..77 loop and is superseded by the above; see git
history of this file for its details.
