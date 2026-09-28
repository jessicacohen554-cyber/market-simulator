# PRECOMMIT — NWPP-NEXT-8: monthly pile grain of the per-yard coal identity, 2019–2025

**Control:** keeper #14 `2026-09-27-nwppnext7-coal-take-floor`, compared against its committed bundle
`results/calibration/nwppnext7sf_span` (rule 29(b) form 4). No control solve.
**Parent:** zero LP. There are seven year-isolated shards (rule 36), one arm.

## 0. Why (zero-LP diagnosis of keeper #14's C4 failures)

C4 compares hourly model coal/gas against EIA-930. Split each series into a monthly-mean component, a
daily-within-month component and an hourly-within-day component. **65–81 % of the coal squared error is monthly**
(2019, 2023, 2025). The model's coal swings too far across the year: winter too high, spring and summer too low.

| 2019, TWh | J | F | M | A | M | J | J | A | S | O | N | D |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Coal, EIA-930 | 5.6 | 5.0 | 4.5 | 3.1 | 2.6 | 3.7 | 5.0 | 5.4 | 5.0 | 4.6 | 4.7 | 5.2 |
| Coal, keeper #13 | 6.2 | 6.2 | 5.1 | 3.4 | 2.1 | 2.9 | 3.9 | 4.3 | 4.0 | 3.6 | 4.2 | 6.1 |
| Coal, keeper #14 | 7.0 | 6.3 | 6.3 | 4.1 | 2.3 | 3.1 | 4.3 | 4.8 | 4.6 | 4.4 | 6.0 | 6.6 |
| Gas, EIA-930 | 5.6 | 4.5 | 4.9 | 4.0 | 3.3 | 5.0 | 7.1 | 7.6 | 6.2 | 4.7 | 4.9 | 6.1 |
| Gas, keeper #14 | 4.5 | 2.9 | 3.2 | 3.7 | 3.8 | 5.5 | 7.3 | 7.3 | 6.3 | 4.9 | 3.9 | 5.5 |

- Demand and hydro match EIA-930 monthly; the misfit is a coal↔gas swap by season.
- **Cause.** NW delivered gas (EIA-923, quantity-weighted, NW states) ran $3.78 / 5.09 / 4.54 in Jan–Mar 2019 and
  $2.16–2.45 from Jun to Oct. The LP fuel-switches textbook-fashion. Real NW coal is mostly captive or contracted.
  CEMS shows it running near-flat through the summer.
- **The annual take floor made this worse.** It fixes only the year's total, so the LP banks the obligated burn in the
  dear-gas months: keeper #14 added +0.8 / +1.2 / +1.8 TWh of coal in Jan / Mar / Nov 2019.
- **Upper bound (not a prediction).** If keeper #14's monthly means were replaced by EIA-930's monthly shape, every C4
  record would clear r ≥ 0.80: coal 2019 0.690→0.859, 2023 0.693→0.895, 2025 0.678→0.835; gas 2019 0.699→0.807.

## 1. Owner decision cards (2026-09-28)

| Card | Ruling |
|---|---|
| Floor grain (reopens Q2 "annual") | **Monthly pile balance** |
| Receipt profile | **Flat ratable C/12** |
| Sides | **Both floor and ceiling** |

## 2. The arm (one config key, one mechanism)

`coal_fuel_inventory_monthly_pile`: absent → **True**. Requires `coal_fuel_inventory_take_floor` and is gated to
`COAL_TAKE_FLOOR_ISOS` (NWPP).

Each yard row becomes 12 **cumulative** month-end rows (`m` = 1..12):

```
max(0, (S_dec − S_max) + m/12 · C) · hc  ≤  Σ_{g∈yard, t≤end m} HR·P + shortfall  ≤  S_dec·hc + m/12 · (budget − S_dec·hc)
```

- The pile never goes negative (ceiling) and never overflows the most it has ever held (floor). Receipts are flat
  ratable within the year.
- **Month 12 is exactly keeper #14's annual floor and ceiling, clips included.** It is the same identity at a finer
  grain (rule 19). Phase 0 asserts this on the real fleet in all 7 years.
- The two feasibility clips are the annual ones applied per month: floor ≤ ceiling, and floor ≤ what the rowed units
  can burn by that month-end.
- The soft floor's per-hour shortfall column enters every later month-end row, so a missed take is paid **once**.
  This is unit-tested: a take unmet in both months costs 5,000, not 10,000.
- **Zero free parameters.** The DOF ledger is unchanged at 5 entries.

Code:
- `data/coal_fuel_inventory.py::build_coal_monthly_pile`.
- `model/lp/rows.py`: a block-lower-triangular running sum on the yard block, applied only when the budget has more
  than one month column. With one column (the annual form) nothing changes, so every existing run is byte-identical.
- `run_calibration.resolve_coal_monthly_pile`.
- Tests: `tests/unit/data/test_coal_monthly_pile.py`.

## 3. Phase 0 (zero LP): `scripts/probes/_nwppnext8_monthly_pile_phase0.py`

The probe rebuilds keeper #14's fleet on its own recipe plus the arm and calls the builders exactly as `run_year`
does. The gate resolved `(pooled False, yard True)`, floor True and monthly pile True in all 7 years. Output:
`results/calibration/_nwppnext8_monthly_pile_phase0.json`.

| Year | Yards | Annual floor TWh | Annual ceiling | Keeper #14 coal (rowed) | Peak floor gap vs #14 (month) | Peak ceiling excess (month) | Clipped cells (ceil / cap) |
|---|---|---|---|---|---|---|---|
| 2019 | 16 | 56.63 | 72.52 | 59.31 | 2.39 (Oct) | 0.48 (Mar) | 12 / 13 |
| 2020 | 16 | 47.98 | 72.30 | 48.89 | 2.15 (Aug) | 0.06 | 0 / 45 |
| 2021 | 15 | 47.80 | 70.43 | 53.22 | 2.48 (Jun) | 0.06 | 0 / 28 |
| 2022 | 14 | 43.44 | 62.90 | 56.58 | 0.44 (Apr) | 0.04 | 12 / 18 |
| 2023 | 14 | 38.83 | 57.15 | 48.49 | 0.12 (Jun) | 0.17 (Apr) | 0 / 12 |
| 2024 | 14 | 32.20 | 53.75 | 36.74 | 0.52 (Jun) | 0.14 (Feb) | 12 / 9 |
| 2025 | 14 | 34.82 | 55.00 | 36.55 | 0.91 (Oct) | 0.14 (Oct) | 12 / 10 |

- "Floor gap": summed over yards, how far keeper #14's cumulative burn sits below the cumulative floor at a month-end.
  It is TWh-equivalent at each yard's fleet heat rate.
- The per-plant monthly model coal is read from keeper #14's payload `m_mon`.
- **The footprint is material in 2019–2021 and small in 2022–2025.** In 2023 it is nearly nil.
- The 12 ceiling-clipped cells in 2019, 2022, 2024 and 2025 are the one yard already clipped annually (NEXT-7 §2),
  carried through 12 months.

## 4. G-DRIFT, keeper `git_sha` `2162cef5` → pin (form 4)

Scope: `git diff 2162cef5 origin/main` over the solve paths (26 files). Every hunk is **INERT** for NWPP, checked
against all seven keeper `run_config_<Y>.json`:

| Change | Why inert for NWPP |
|---|---|
| `retiree_cems_cap` deleted (scenarios, arrays, outages, backcast_config, persist, run_calibration*, replay_keeper) | False in all 7 keeper configs; its off path never ran. It drops from the cache key at False |
| `coal_econ_marginal_hr_two_sided` and its `assembly.py` / `campd_bins.py` reprice | Default off and absent from the keeper; `_inc_hr_ratio` is `{}` when it is off |
| SPP West/East partition (`iso_configs`, `topology_variant`, `runner`, `eia860`, `zone_assignment`, `renewables`, `zonal_shares`, `spp_plant_reserve_zone.csv`) | Gated to SPP plus `spp_west_east_active()`; forced to `north_south` for other ISOs |
| CAISO `partial_year_measured` (`envelopes.py`, `interchange/caiso.py`) and `ST_GAS_PEAK_MEASURED_HR_MULT_BY_ISO["CAISO"]` | CAISO-only |
| `pjm_offer_midcurve_shape_segments` (`offer_surfaces.py`) | PJM-only, None |
| NYISO import ladders (`interchange/spec.py`) | NYISO keys only |
| `actual_lmp.json`, `actual_lmp_zonal_ERCOT.parquet` | ERCOT scoring artifacts, never LP inputs |

This lane's own change is live only when armed.

## 5. Recipe (per shard, year Y)

Keeper #14's recipe (PRECOMMIT-nwppnext7 §4), plus one key:

```
mkdir -p /tmp/n49 && git fetch --depth=1 origin 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 \
  && git archive 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 results/calibration/nwpp49_ror_span | tar -x -C /tmp/n49
python3 scripts/data/curate_hydro_plant_modes.py --iso NWPP
python3 scripts/data/curate_coal_receipts.py && python3 scripts/data/curate_coal_stocks.py
python3 scripts/replay_keeper.py /tmp/n49/results/calibration/nwpp49_ror_span \
  --out-dir results/calibration/nwppnext8mp_<Y> --years <Y> \
  --set eia860_vintage_tracks_solve_year=true \
  --set measured_ct_heat_rates=true --set measured_coal_heat_rates=true \
  --set measured_st_heat_rates=true --set measured_cc_heat_rates=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_partial_outage_windows=true \
  --set mid_vintage_exit_carry=true --set partial_plant_exit_carry=true \
  --set nwpp_demand_plant_basis=true \
  --set coal_committed_nested_on_mustrun=true \
  --set admit_standby_units=true \
  --set nwpp_path76_alturas_link=true \
  --set coal_fuel_inventory_plant_grain=true --set coal_fuel_inventory_take_floor=true \
  --set coal_takeorpay_from_data=false --set coal_committed_takeorpay_regulated=false \
  --set coal_fuel_inventory_monthly_pile=true \
  [<Y> in 2019, 2020, 2021, 2022 ONLY:] --set hydro_backfill_year=null \
  --note "NWPP-NEXT-8 monthly pile: keeper #14 recipe + cumulative month-end yard rows (flat ratable receipts)"
```

## 6. Hard stops (any miss means STOP, no push)

1. `git rev-parse HEAD` equals the pin.
2. `sha256sum data/raw/_processed-legacy/campd_ct_heat_rates_NWPP.csv` =
   `29baa2f1ecfa10d9734c7e44cc306a88d527adb28968ea260f3409de37d7ff92`.
3. `scenario_config` in `run_config.json` differs from keeper #14's
   `results/calibration/nwppnext7sf_span/run_config_<Y>.json` only in `coal_fuel_inventory_monthly_pile` (True).
   Keys absent in the keeper and False in the arm are also accepted.
4. `meta.json` `hydro_backfill_year` is null for 2019–2022 and 2024 for 2023–2025.
5. `hourly/system_<Y>.parquet` P1 summed `demand` equals keeper #14 ±0.05 TWh: 279.581 / 292.940 / 289.358 / 298.960 /
   280.261 / 290.216 / 302.532.
6. **Arm-live.** The solve log carries all of these:
   - `coal per-yard budget (NWPP <Y>): N yards`;
   - `coal take floor (NWPP <Y>): soft, shortfall priced per yard at`;
   - `coal take floor (NWPP <Y>): M yard rows floored`, with M > 0;
   - `coal monthly pile (NWPP <Y>): N yard rows x 12 month-ends`;
   - `NWPP Path 76 (Alturas): NWPP-NW<->NWPP-SNV 300 MW appended`.
7. The bundle contains `dispatch/<Y>_P1.parquet`, `hourly/class_hourly_<Y>.parquet`, `hourly/system_<Y>.parquet` and
   `hourly/hydro_cascade_<Y>.parquet`.
8. The solve is not infeasible. An infeasible or Unknown LP is a STOP, with the log reported and no retry.

## 7. Predicted, reported and never gated

- Coal moves from Nov–Dec (and, via the ceiling, Jan–Mar) into May–Oct in 2019–2021. Gas moves the opposite way.
- **C4 coal and gas 2019 improve.** Coal 2023 is roughly flat (its footprint is 0.1 TWh). Coal 2025 moves a little
  (0.9 TWh). The §0 upper bound is not a prediction; this arm closes only part of the monthly gap.
- Annual coal totals are nearly unchanged, since month 12 is the same identity. C1 moves only through the shortfall
  paid.
- Solve time rises: each yard carries ~6.5× its annual non-zeros.
- Also reported: unserved energy, and the per-shard shortfall paid from the log.

**Promotion** follows the owner's standing structure ruling: promote if structural integrity improves, with every
regression reported at full magnitude.

## 8. Launch record (appended after the pin; nothing above it changed)

- **Pin** `e7478536f46cade23e0aea71e79a329c0e29202a`. All 7 shards were launched 2026-09-28 00:37–00:40 UTC.
- Unit suite at the pin: 27 failures, the same test IDs as `origin/main` (`test_firm_import_*`,
  `test_gas_offer_zonal_anchor_vintage`, `test_nwpp_demand_plant_basis`, `results/test_export`). None come from this
  lane.

| Year | Session |
|---|---|
| 2019 | `session_01Jw3MQPBETS1uKj7VYVFAhz` |
| 2020 | `session_015XJwKpuaDKTJS6itqAoZjt` |
| 2021 | `session_01ErY21i1rSkGxrbozjLYLjF` |
| 2022 | `session_012nFDDkKi3LP1E12vqcjUY9` |
| 2023 | `session_013hUChwwKXquVEsjBj1FiUe` |
| 2024 | `session_01Ly4aNfS2ymBUm5foP6XLSE` |
| 2025 | `session_01Hsk3bRN91t9i7zJDgSY5td` |
