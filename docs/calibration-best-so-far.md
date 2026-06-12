# ERCOT calibration — best config so far

Keeper: **run 85 / dashboard `run85 coal soft`** (2026-06-12, bundle
`results/calibration/run85_coal_soft`, highspy 1.14.0). **Supersedes run 79
(`e2_4_retune`)** on the size-aware volume bar (see "Success bar" below): run 85
cuts total class volume error 24.0 → 20.9 TWh, fixes the worst class (lignite
2024 −23.8% → −8.8%, 2023 −12.8% → +2.3%), improves hourly coal NRMSE
(0.229 → 0.198 in 2024) and holds the LMP gate. It adds the gas-keyed coal
passthrough sigmoids (lignite + a deeper PRB floor) on top of run 79's config;
everything else is unchanged. Reproduce with:

```
python scripts/run_calibration_full.py --year 2023 2024 2025 \
    --storage-daily-cycling --battery-adder 10 \
    --offer-curve-delta-json <run79 deltas> \   # meta.json offer_curve_deltas
    --coal-lignite-sigmoid --lignite-floor 0.75 --lignite-ceil 1.00 \
    --prb-floor 0.74 --prb-follower-floor 0.64
```

Run 79 (`e2_4_retune`) remains the documented predecessor and the zero-point
for the coal sigmoids; its config and table are in the git history of this file
and the "ERCOT E2" / "ERCOT Runs 85–87" calibration-log entries.

## Success bar (size-aware)

Judge each class by size, not a flat percentage (a flat % is loosest exactly
where the system mix is dominated):

- class total **≥ 20 TWh** (CC_REGULAR, CC_CHP, COAL_PRB): within **±5%** every
  year.
- class total **< 20 TWh** (ST_GAS, COAL_LIGNITE, CT_PEAKER, CT_CHP): within
  **±1 TWh** (absolute) every year.
- CT_CHP excluded (known +28% 2025 CHP-benchmark gap).

Never regress a class vs the keeper. Under this bar run 85 has 4 in-scope fails
vs run 79's 5, and **all four of run 85's misses are in the single 2024
cheap-gas year** (PRB −7.9%, ST_GAS −1.19 TWh, lignite −1.23 TWh, CT_PEAKER
−1.48 TWh), all marginal — in 2024 CC_REGULAR sits +3.1 TWh too high while
coal/peakers/steamers each sit ~1 TWh too low (the "right donor" gap, now ~3 TWh
in one year). That 2024 cluster is the live target for runs 88+.

## Config (the knobs that matter)

- `td_loss_factor = 0.0` (EIA-930 demand is generation-side; no gross-up).
- Locked tier-pass-2 family: per-plant CAMPD coal must-run, gas-keyed PRB
  passthrough sigmoid (baseload + follower tiers), `coal_drop_pof`,
  historic outage overlay, per-plant monthly coal pricing — all defaults of
  `run_calibration_full.py`.
- **Coal passthrough sigmoids (the run-85 add, vs run 79):**
  - `coal_lignite_passthrough_sigmoid = on`, floor 0.75 / ceil 1.00 (gas_mid /
    gas_slope at their built-in defaults). Mine-mouth take-or-pay fixed costs
    are sunk, so the lignite BID discounts in cheap-gas months; the measured
    $1.45/MMBtu delivered-cost constant is untouched.
  - `coal_prb_passthrough_floor = 0.74`, `coal_prb_follower_floor = 0.64`
    (tiered baseload + follower) — half the run-81 floor gradient, spreading
    the PRB discount across years rather than overshooting 2023.
- `storage_daily_cycling = on` (SOC returns to its day-start level every 24 h).
- **`battery_dispatch_adder = 10.0` $/MWh discharged** (E2): reduced-form BESS
  cycling degradation + AS opportunity cost; inherited from run 79 unchanged
  (lands 2025 battery discharge at −1.5% vs EIA-930).
- Nuclear: per-year EIA-923 monthly CF overlay — inherited from run 79
  unchanged (−0.7% every year).
- Offer-curve deltas vs the calibrated defaults (recorded in the bundle's
  `run_config.json`, identical to run 79): CC_REGULAR {committed −0.05, econ_low
  −0.10, econ_high −0.45, peak +0.25}; CC_CHP {econ_high +0.43, peak −0.50,
  pct_peaking −4}; CT_CHP {committed −0.20, econ_low −0.08, econ_high +0.10,
  peak −0.08}; CT_PEAKER {committed −0.34, econ_high +0.20}; ST_GAS {committed
  −0.385, econ_low −0.13, econ_high −0.35, peak −1.0}; COAL_PRB {committed
  −0.04, econ_low −0.30, econ_high +0.44, peak +0.082}; COAL_LIGNITE {committed
  −0.07, econ_low +0.076, econ_high −0.037}.

## Results (P1, vs EIA-923 incl. BTM add-back)

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| CC_REGULAR | −2.7% | +2.1% | +0.7% |
| CC_CHP | +1.0% | +0.8% | +2.0% |
| COAL_PRB | +1.3% | −7.9% | −1.0% |
| COAL_LIGNITE | +2.3% | −8.8% | +1.9% |
| CT_PEAKER | −3.8% | −17.9% | −3.1% |
| ST_GAS | +5.5% | −6.5% | +2.6% |
| nuclear | −0.7% | −0.7% | −0.7% |
| coal hourly r (NRMSE) | 0.934 (0.151) | 0.908 (0.198) | 0.800 (0.164) |
| LMP MAE vs actual RT ($/MWh) | 31.0 | 9.1 | 11.6 |
| battery dis. vs EIA-930 | n/a | (run-79 storage) | **−1.5%** |

Total class volume error 20.9 TWh (run 79: 24.0). Unserved energy 0.000 in all
years. The residual is the 2024 cheap-gas cluster above; the 2023 LMP level
miss is missing scarcity pricing (ORDC), localized in the "ERCOT Runs 85–87"
log entry and scoped to runs 88+.

## History

Run 79 (flat run, dashboard `run79 storage retune`) was the keeper through
2026-06-12; it predates the coal passthrough sigmoids and is superseded by the
above. The run-80/81/82/84 probes and runs 86/87 were net-negative — see the
Runs 80–81, Run 82, Run 84 and Runs 85–87 calibration-log entries. The previous
flat `coal_prb_passthrough = 0.83` keeper (git `249fec7`) predates the sigmoid
passthrough family entirely.
