# NYISO 2025 refresh + price re-score (2026-06-12)

Re-run of the NYISO 2025 backcast after the EIA-930 `NYIS hourly` extract was
regenerated from the refreshed upload (`inputs/raw-data/eia-930/NYIS_region.parquet`
+ `NYIS_fueltype.parquet`, now spanning full 2015–2026) with
`python scripts/convert_eia930.py NYIS --input-dir inputs/raw-data/eia-930 --force`.
The previous extract stopped at Q1'25 (2,154 h), so `nyiso_net_interchange(2025)`
returned `None`, `load_demand` fell back to the gross demand-profiles parquet
and served **0** of the import wedge — the P12 `nyiso_p12_base_2025` +22.7%
over-generation. 2023/2024 demand & interchange are byte-identical pre/post
(2023 −23.45 TWh, 2024 −20.39 TWh), so the keeper and the other ISOs are
untouched.

Bundle: `run_calibration_full.py --iso NYISO --year 2025 --commitment`.

## Interchange — now served exactly (was 0)

| | model | actual EIA-930 |
|---|---|---|
| net interchange (TWh) | **−19.09** | −19.09 |
| duration RMSE | **0 MW** | — |
| import-hours | 99.8% | 99.8% |
| diurnal corr | **+1.00** | — |

## Fuel mix (model vs EIA-930 vs EIA-923 2025 *preliminary*)

| fuel | model | EIA-930 | Δ930 | EIA-923 (prelim) | Δ923 |
|---|---|---|---|---|---|
| gas | 68.30 | 70.25 | **−2.8%** | 60.21 | +13.4% |
| nuclear | 28.38 | 27.95 | +1.5% | 28.41 | −0.1% |
| wind | 7.05 | 7.05 | exact | — | — |
| solar | 3.56 | 0.00 | (BTM in 930) | 0.66 | — |
| hydro | 21.05 | 24.10 | −12.7% | 21.05 | budget |
| oil | 0.02 | 0.18 | — | 1.06 | −98% (U4-gated) |
| **TOTAL** | **132.76** | 129.54 | **+2.5%** | 115.84 | +14.6% |

**EIA-923 2025 is the preliminary M-file** (total 115.84 TWh — ~17 below the
served demand basis; solar/biomass/oil under-reported). Flagged, not chased:
EIA-930 (129.54) is the operationally consistent benchmark, against which gas
is **−2.8%** and the total is **+2.5%** — the gas over-gen has closed. Against
EIA-923 the +13.4% gas reads off the under-reported preliminary total, not a
dispatch error (the same EIA-930/EIA-923 basis gap documented for 2023).

## Price re-score (P10/U2 now landed — no longer level-only)

Scored vs `inputs/calibration/actual_lmp.json` (per-zone levels) +
`actual_lmp_hourly_NYISO.parquet` (system duration). Method:
`scripts/analyze_lmp_residual.py` (system duration, P1 demand-weighted) +
per-zone model average vs `actual_lmp.json` zone DA/RT.

**System level + duration**

| year | model avg | actual RT | actual DA | resid vs RT | p50 m/a | p90 m/a | p99 m/a |
|---|---|---|---|---|---|---|---|
| 2023 | $41.79 | $30.29 | $31.11 | +$11.50 | 36/26 | 66/42 | 104/120 |
| 2025 | $69.24 | $60.73 | $60.71 | +$8.51 | 57/45 | 114/114 | 157/222 |

**Per-zone average ($/MWh; model vs actual DA, resid)**

| zone | 2023 model | 2023 actDA | Δ | 2025 model | 2025 actDA | Δ |
|---|---|---|---|---|---|---|
| Upstate_West | 38.94 | 26.08 | +12.86 | 66.82 | 55.89 | +10.93 |
| Capital_Hudson | 43.42 | 36.38 | +7.04 | 70.61 | 65.15 | +5.46 |
| Lower_Hudson | 43.42 | 33.58 | +9.84 | 70.61 | 62.99 | +7.62 |
| NYC | 43.42 | 33.95 | +9.47 | 70.61 | 65.41 | +5.20 |
| Long_Island | 43.42 | 40.77 | +2.65 | 70.61 | 68.87 | +1.74 |

**Reading.** Both years over-price the mid-merit band (2025 p50 $57 vs $45) and
**under-price the scarcity tail** (2025 p99 $157 vs $222, max $314 vs $2,074) —
the no-ORDC / no-reserve-scarcity signature; the model has no scarcity adder.
The 2025 p90 is near-exact ($113.7 vs $113.6). The model collapses the four
downstate zones to one price ($70.61) — it captures the upstate-cheap /
downstate-dear separation (Upstate_West $66.8 vs downstate $70.6, ≈$3.8) but
not the full actual J−A spread (≈$13), the documented interface-TTC /
downstate-congestion structural item (U7). Long_Island is the closest zone in
both years (+$1.7 / +$2.7); the over-pricing is heaviest upstate, consistent
with the gas-level floor sitting above measured upstate LBMP.

See `PRICE-RESCORE-lmp-residual.md` (full duration / hour-of-day / band
breakdown) and `PRICE-RESCORE-zone-level.txt` in this bundle.

## Discipline

Structural-discipline run (playbook §6): no offer band tuned. oil stays
U4-gated (no Transco-Z6 / Iroquois daily basis uploaded for NYISO). 2024 stays
blocked on `NY_2024` unit-level CEMS. ERCOT/PJM/CAISO/NEISO untouched (only the
`NYIS hourly` parquet changed; 2023/2024 content byte-identical).
