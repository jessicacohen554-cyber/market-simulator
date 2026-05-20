# ERCOT calibration — best config so far

Clocked at git `249fec7` (PRB passthrough 0.83). Run with:
`python scripts/run_calibration_full.py --year 2023 2024 --commitment --no-coal-p2`

## Config (the knobs that matter)
- `td_loss_factor = 0.0` (EIA-930 demand is generation-side; no gross-up).
- `wefor_multiplier = 0.7` (thermal forced-outage lightened ~30%, seasonal
  shape preserved; outage shifted out of summer into shoulder months only).
- `coal_prb_passthrough = 0.83` (PRB tranches above must-run bid VOM + 83% of
  fuel; lignite at full cost).
- Commitment pass on, coal pinned to P1 (`--no-coal-p2`).
- Nuclear ERCOT monthly CF: `[0.97,0.99,0.89,0.78,0.84,0.93,0.95,0.96,0.95,0.72,0.83,0.99]`.

### Coal must-run (CSV, Pct_Must_Run/Committed/Economic/Peaking)
- Lignite — Oak Grove (6180), San Miguel (6183), Major Oak (7030): 35/15/45/5.
- PRB by rail — Limestone (298), Martin Lake (6146): 35/15/45/5 (lignite CSV
  pattern, reclassified to PRB supply).
- PRB by rail — W A Parish (3470), Coleto (6178), Fayette (6179),
  J K Spruce (7097), Sandy Creek (56611): 30/15/50/5.

### Bin corrections in this config
- Limestone (298) & Martin Lake (6146): supply lignite → PRB.
- Sandy Creek: plant code 56257 → 56611.
- Stryker Creek (3504): CT_PEAKER → ST_GAS.
- Barney M Davis (4939): split ST_GAS 352 MW + CC_REGULAR 730 MW.

## Coal results (P1)
| | 2023 | 2024 |
|---|---|---|
| COAL_LIGNITE (vs EIA-923) | +0.9% | −8.7% |
| COAL_PRB (vs EIA-923) | +0.1% | −12.6% |
| total coal (vs EIA-923) | +0.3% (60.59 vs 60.42) | −11.6% (50.91 vs 57.62) |
| total coal (vs EIA-930) | −0.5pp (62.29) | −1.9pp (58.77) |
| coal Pearson r / NRMSE | 0.848 / 0.206 | 0.820 / 0.253 |
| unserved energy | 0.000 | 0.000 |

2023 coal is essentially nailed at this config; 2024 runs ~12% under at the
same 0.83 because 2024 gas was cheaper, pricing PRB out more.
