# PJM Coal Bituminous vs CAMPD — the benchmark NaN bug (2026-06)

**TL;DR.** The PJM COAL_BIT *charts-page* comparison against CAMPD was unusable
because the CAMPD hourly **benchmark** (not the model) undercounted multi-unit
coal plants ~2× — a NaN-propagation bug in `campd.plant_hourly_net`. The
CAMPD→net-MWh conversion *formula* was already correct; the hourly aggregator
silently dropped every plant-hour in which any one unit was offline. Fixed by
flooring NaN gross to 0 before accumulation. The LP dispatch is untouched and
EIA-923 remains the class-total gate.

## Symptom

On the deployed dashboard the per-plant CAMPD benchmark summed to **~half** of
EIA-923 for the *same* PJM bituminous plants:

| year | CAMPD COAL_BIT (bench) | EIA-923 COAL_BIT (same plants) |
|---|---|---|
| 2023 | 51.1 TWh | 103.5 TWh |
| 2024 | 48.4 TWh | 105.3 TWh |
| 2025 | 61.5 TWh | 124.5 TWh |

So model COAL_BIT (~110–135 TWh) looked like a +100 %+ overrun against a broken
~50 TWh "actual", and the per-class hourly r / NRMSE were meaningless — you
could not see *where/when* the model overruns. CT_PEAKER had the same halving
(17 vs 38 TWh); CC_REGULAR was fine (310 vs 325).

## Root cause

`campd.plant_hourly_net` placed each unit-hour with
`np.add.at(series, hoy, gross)`. On the **unit-level** CAMPD extracts
(OH/WV/IN/KY/VA — exactly the big PJM bituminous plants: Gavin 8102, Amos 3935,
Cardinal 2828, Clifty Creek 983, Rockport 6166, …) an offline unit writes
`NaN` gross, not 0. `np.add.at` propagates NaN, so a single down unit poisoned
the whole plant-hour; the NaN then vanished downstream (`groupby.sum` skips it,
the bundle's `nan_to_num` floored it to 0), silently deleting every hour any
unit was down. ERCOT never hit this — its CAMPD is **facility-level** (units
pre-summed, no per-unit NaN). The annual aggregates used `nansum` and were
already correct, which is why parasitic factors and EIA-923 reconciliation
looked fine while the hourly series was wrong.

**Fix:** `gross = np.nan_to_num(gross, nan=0.0)` before `np.add.at`
(`src/market_sim/data/campd.py`), with a regression test
(`tests/test_campd.py::TestPlantHourlyNet::test_nan_unit_hour_does_not_poison_multi_unit_plant`).
After the fix Gavin goes NaN→10.34 TWh (923: 10.33), Amos→9.68 (9.61),
Cardinal→9.47 (9.50); the COAL_BIT fleet lands at 106.6 TWh for 2024 (923 ~110).

## Which CAMPD→net-MWh method is most faithful to EIA-923

Tested on the PJM bituminous fleet (34 plants), fleet-total net vs EIA-923
combustion net (`scratchpad/coalbit_method_compare.py`). **`gross × parasitic`
+ heat-input proxy for grossLoad-blank coal is best** and is what the dashboard
uses:

| method | 2023 | 2024 | 2025 |
|---|---|---|---|
| gross only (no parasitic) | +7.5 % | +6.3 % | +5.5 % |
| **gross × parasitic + heat-proxy** | **−1.5 %** | **−2.0 %** | **−2.0 %** |
| heat-input ÷ physical HR | +8.5 % | +6.9 % | +4.2 % |
| (heat − steam) ÷ physical HR | +5.2 % | +3.4 % | +0.6 % |

Per-plant, `gross × parasitic` tracks EIA-923 within ~1 %. Conclusion: the
measured electrical output (gross) scaled by the reconciled parasitic factor is
the truth; heat→MWh is only needed (and only used) for the grossLoad-blank
minority, where the EIA-923-anchored effective HR already absorbs steam
diversion. No explicit steam correction is needed for COAL_BIT.

## Is the model overrun real?

Yes — independent of the benchmark bug. Per `pjm-coal-overrun-decomp-2026-06.md`
(keeper `pjm_38`), the COAL_BIT over is ~92–94 % in the take-or-pay BASE
tranches and is **export-driven**: PJM's modeled LMP clears ~$8–10 below actual,
inflating the export spread so cheap base coal floods across the seam. 2024 is
the closest year because coal/gas parity shrank that spread. The fix here does
not change that finding — it makes the *charts page* able to show it per-plant,
per-month, and per-hour now that the CAMPD coal-bit "actual" is complete.
