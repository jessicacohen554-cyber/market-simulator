# PRECOMMIT — NWPP-NEXT-7: per-yard coal take floor (owner rulings Q1–Q5), 2019–2025

**Control:** keeper #13 `2026-09-26-nwppnext6-path76-ctrederive`, compared against its committed bundle
`results/calibration/nwppnext6ab_span` (rule 29(b) form 4). No control solve.
**Parent:** zero LP. There are seven year-isolated shards (rule 36), one arm.

## 0. Owner rulings (2026-09-27, decision cards, on `FINDING-nwppnext5-coal-take-obligation-design` §5)

| Q | Ruling |
|---|---|
| Q1 | Generalise `coal_fuel_inventory_plant_grain`: a LOWER bound on the existing per-yard row, with NWPP added to its ISO gate |
| Q2/Q3 | Annual period, a floor (`≥`), not an equality |
| Q4 | Estimator **B net**: `max(0, Y-1 contract tons + Dec(Y-1) stock − max month-end stock ≤ Y-1) × hc`. The owner asked for a recommendation. B was recommended on structure: A under-reads rolling contracts. The 2020 CC overshoot risk under B was stated before the ruling. |
| Q5 | Retire `coal_takeorpay_from_data` and `coal_committed_takeorpay_regulated` in the same arm (rule 19) |

## 1. The arm (four config keys, one mechanism)

- `coal_fuel_inventory_plant_grain`: False → **True**. This is the yard row and its existing ceiling,
  `Dec stock + mean Y-2..Y-1 receipts`.
- `coal_fuel_inventory_take_floor`: absent → **True**. This is the new floor field.
- `coal_takeorpay_from_data`: True → **False** (Q5).
- `coal_committed_takeorpay_regulated`: True → **False** (Q5).

Code:
- `data/coal_fuel_inventory.py::build_coal_take_floor`.
- `model/lp/rows.py`: the yard rows' lower bound.
- `run_calibration.resolve_coal_take_floor`. It raises if the floor is armed with either discount, without the yard
  rows, or outside NWPP.

The floor has two feasibility clips, fixed here before any solve:
- it never exceeds the yard's own ceiling;
- it never exceeds `Σ HR·pmax·availability` of the yard's rowed units.

**Zero free parameters.** Contract purchase types are C/NC/T, the census set.

## 2. Phase 0 (zero LP): `scripts/probes/_nwppnext7_take_floor_phase0.py`

The probe rebuilds keeper #13's fleet (`run_year(fleet_only=True)`, keeper recipe + arm) and calls the builders
exactly as `run_year` does. The gate resolved `(pooled False, yard True)`, floor True, and both discounts False in all
7 years.

| Year | Yards | Floor TWh | Census B-net | Ceiling | Keeper #13 coal (rowed yards) | Floor binds | Ceiling binds | Clips (ceil/cap) |
|---|---|---|---|---|---|---|---|---|
| 2019 | 16 | 56.63 | 56.68 | 72.52 | 51.51 | 10.15 | 1.99 | 1 / 1 |
| 2020 | 16 | 47.98 | 56.56 | 72.30 | 38.44 | 12.77 | 0.44 | 0 / 4 |
| 2021 | 15 | 47.80 | 48.86 | 70.43 | 52.88 | 2.63 | 1.70 | 0 / 3 |
| 2022 | 14 | 43.44 | 43.94 | 62.90 | 60.05 | 0.13 | 4.05 | 1 / 1 |
| 2023 | 14 | 38.83 | 38.45 | 57.15 | 47.03 | 2.43 | 0.81 | 0 / 2 |
| 2024 | 14 | 32.20 | 33.66 | 53.75 | 29.01 | 7.86 | 0.61 | 1 / 1 |
| 2025 | 14 | 34.82 | 35.15 | 55.00 | 31.14 | 6.35 | 0.68 | 1 / 1 |

TWh-equivalent at each yard's fleet heat rate. "Binds" means relative to keeper #13's per-plant dispatch.

- The built floor reproduces the census at 11 or more yards each year.
- **2020 differs by 8.6 TWh.** The capacity clip binds at Colstrip (5.86 vs 13.26), Centralia (4.98 vs 5.77) and
  Naughton.
- **A second defect is exposed, reported and not fixed.** The model's Colstrip 2020 available energy is 5.86 TWh, below
  its measured 2020 generation of 7.94 TWh (EIA-923). That is an outage/availability input question, routed to the
  next lane.
- Unrowed coal plants (no curated record, never substituted): 10504, 10784, 57915, 62319, all small.

**Removing the discounts** raises coal offers wherever the floor is slack. Coal may therefore fall further in
2021–2023, where the ceiling also binds (2022: 4.05 TWh).

## 3. G-DRIFT, keeper `git_sha` `0a84941d` → pin (form 4)

Every changed solve-path hunk is **INERT** for NWPP:

| Change | Why inert for NWPP |
|---|---|
| `neiso_winter_fuelsec_conduct_roster`, `winter_fuel_inventory.py` and its constant | NEISO flags, off |
| `unit_outage_coal_extract_basis_share` (SPP-86), `outages.py`, `arrays.py`, `floors.py` | Default off and absent from the keeper. The extract index stays None when both basis flags are off, and `unit_outage_extract_basis_share` is False in all 7 keeper configs |
| `campd_bins.py` `_mg` | Differs only under `campd_outage_merit_order_guard`, which is False in the keeper |
| `fuel_trajectories.py` | The SOCO table only |
| `forecast_parity_registry.py` | Metadata |

This lane's own changes are live only when armed.

## 4. Recipe (per shard, year Y)

```
mkdir -p /tmp/n49 && git fetch --depth=1 origin 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 \
  && git archive 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 results/calibration/nwpp49_ror_span | tar -x -C /tmp/n49
python3 scripts/data/curate_hydro_plant_modes.py --iso NWPP
python3 scripts/data/curate_coal_receipts.py && python3 scripts/data/curate_coal_stocks.py
python3 scripts/replay_keeper.py /tmp/n49/results/calibration/nwpp49_ror_span \
  --out-dir results/calibration/nwppnext7tf_<Y> --years <Y> \
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
  [<Y> in 2019, 2020, 2021, 2022 ONLY:] --set hydro_backfill_year=null \
  --note "NWPP-NEXT-7 take floor: keeper #13 recipe + per-yard coal take floor (B net), take-or-pay discounts retired"
```

## 5. Hard stops (any miss means STOP, no push)

1. `git rev-parse HEAD` equals the pin.
2. `sha256sum data/raw/_processed-legacy/campd_ct_heat_rates_NWPP.csv` =
   `29baa2f1ecfa10d9734c7e44cc306a88d527adb28968ea260f3409de37d7ff92`.
3. `scenario_config` in `run_config.json` differs from keeper #13's `results/calibration/nwppnext6ab_span/run_config_<Y>.json`
   only in the four §1 keys, plus keys absent in the keeper and False in the arm.
4. `meta.json` `hydro_backfill_year` is null for 2019–2022 and 2024 for 2023–2025.
5. `hourly/system_<Y>.parquet` P1 summed `demand` equals keeper #13 ±0.05 TWh: 279.581 / 292.940 / 289.358 / 298.960 /
   280.261 / 290.216 / 302.532.
6. **Arm-live.** The solve log carries both `coal per-yard budget (NWPP <Y>): N yards` and
   `coal take floor (NWPP <Y>): M yard rows floored`, with M > 0, and
   `NWPP Path 76 (Alturas): NWPP-NW<->NWPP-SNV 300 MW appended`.
7. The bundle contains `dispatch/<Y>_P1.parquet`, `hourly/class_hourly_<Y>.parquet`, `hourly/system_<Y>.parquet` and
   `hourly/hydro_cascade_<Y>.parquet`.
8. The solve is not infeasible. An infeasible LP is a STOP, with the log reported and no retry.

## 6. Predicted, reported and never gated

- C1 CC_REGULAR moves toward 0 in 2019/2020/2024/2025 as coal rises. B may push 2020 negative; the 1:1 bound was −11.4
  before the capacity clip.
- Coal volume rises in 2019/2020/2024/2025. It may fall in 2021–2023, where the ceiling binds and the offers rise.
- C4 coal r is flat to −0.1 (FINDING-nwppnext5 §3).
- Also reported: unserved energy, and the take-floor row duals (take-or-pay shadow price) by yard.

**Promotion** follows the owner's standing structure ruling: promote if structural integrity improves, with every
regression reported at full magnitude.

## 7. Cost and retrievability

- 7 shards in parallel, about 15–45 min per year.
- Each pushes its full bundle to `claude/nwppnext7tf-<Y>` (rule 34(a): a `.gitignore` negation and a plain
  `git add`).
- The parent composes (2023 leg first), registers, and lands the bundle on `main` if promoted (rule 33(f)).

## 8. Launch record (appended after the pin; nothing above it changed)

- **Pin** `821069f3cd65ad6c287ac3aac0280138a6b3eb87`. All 7 shards were launched 2026-09-27 18:53–18:54 UTC.

| Year | Session |
|---|---|
| 2019 | `session_015UzeFpYZtuCVYVeC22uJk5` |
| 2020 | `session_01SSnQpzbWfwQchFry7oBJ3s` |
| 2021 | `session_01SmeXb9Mf8HkwiwKb8KoVxk` |
| 2022 | `session_017TwCLeR5ViTddQ1isByCQ8` |
| 2023 | `session_01CUBhQjL6iuhtwUymGm1BuY` |
| 2024 | `session_01ErmbW8Abxx8ZesFSgkhbeb` |
| 2025 | `session_01H4onUSo8bk9UkFgqmzBXNe` |

## 9. Addendum (2026-09-27, before the soft-floor solves): hard floor → soft floor

**What happened on the hard floor** (pin `821069f3`). The legs are kept as a record and superseded.

| Year | Result |
|---|---|
| 2021 | Solved |
| 2025 | Solved |
| 2019 | Solved after 80 min |
| 2020 | P0 infeasible |
| 2022 | HiGHS status Unknown |
| 2023 | HiGHS status Unknown |
| 2024 | HiGHS status Unknown |

- Each failing year had a yard whose floor was clipped exactly to its ceiling or to its full capacity.
- That leaves the row satisfiable only at a corner.

**Owner ruling (decision card, 2026-09-27): soft floor, measured penalty.**
- Each yard row gets a shortfall column in every hour (`layout.n_take_slack`, the RPS ACP escape pattern).
- The column is priced at the yard's own model coal fuel price: the resolved `fuel_prices` for its rowed units,
  year-mean and weighted by `coeff × pmax` (`coal_take_shortfall_price`).
- Economic meaning: take-or-pay. Unburned contracted coal is paid for anyway, so the yard's coal is sunk up to the
  take, and the row dual is capped at the fuel price.
- Zero free parameters.
- Recipe, config keys and hard stops 1–5, 7 and 8 are unchanged. §2's floors and clips are unchanged.

**Changes for the re-solve:**
- **New pin:** recorded below.
- **Out-dir** `results/calibration/nwppnext7sf_<Y>`, branch `claude/nwppnext7sf-<Y>`.
- **Hard stop 6** additionally requires the log line `coal take floor (NWPP <Y>): soft, shortfall priced per yard at`.
- **Reported:** the per-yard shortfall paid (TWh-equivalent). A large shortfall means the take could not be burned,
  and it is reported at full magnitude.
