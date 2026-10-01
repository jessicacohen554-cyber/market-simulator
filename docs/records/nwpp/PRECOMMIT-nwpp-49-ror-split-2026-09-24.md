# PRECOMMIT nwpp-49: NWPP RoR split, regulated chain exempt

**Lane:** NWPP-49 · **Date:** 2026-09-24 · written and pushed **before any leg is launched**.
**Control (rule 29(b) form 4):** keeper `2026-09-22-nwpp-47-grid-wind`,
bundle `results/calibration/nwpp47_gridwind_span`, `git_sha` `f3a883cf`.

## 1. The owner ruling this executes

> "I think 1 and 2 we should adopt the same hydro stuff as other ISOs aside from the unique config
> due to cascade" — then, asked to disambiguate: **"RoR split, chain exempt (Recommended)"**.

"The same hydro stuff as other ISOs" is `hydro_ror_split`. That is K in MISO, NEISO, NYISO, PJM and
SOCO. **No keeper arms `hydro_pondage_bound`**, and NYISO rejected it (R). So pondage (a2) from
`FINDING-nwpp-49-pondage-design-2026-09-23.md` is **not** solved. Its pre-registration stays in
`_nwpp49_gates.py --arm pondage_a2` for the record.

## 2. The change (one field, one classifier rule)

* **Recipe:** the keeper's recipe, unchanged, plus `hydro_ror_split=true` (`replay_keeper.py --set`).
  The cascade, envelope, min-flow floor and grid-carried wind stay armed, exactly as in the keeper.
* **Classifier rule 0, `regulated_chain`** (`scripts/data/curate_hydro_plant_modes.py`): a plant listed
  in `data/raw/<iso>-hydro/<iso>_hydro_chain.csv` is **shapeable**, whatever its EHA label.
  * **Why it is exempt (measured):** CROHMS hourly output at the chain's EHA-"Run-of-river" plants
    (McNary, John Day, The Dalles, Lower Granite, Little Goose, Lower Monumental) has a combined
    within-day sd of **414 / 421 / 372 MW** (2023/24/25). A flat pin contradicts that. Their inflow
    is an upstream release, which the cascade formulation models (rule 19).
  * **Zero DOF.** Membership in a committed registry. No `if iso ==` branch: an ISO without a chain
    file is byte-identical.
* **NWPP registered in the classifier** (`DEFAULT_ISOS`). The per-ISO review:
  * 156/216 plants and 71.1 % of labeled MW are reproduced.
  * The errors under-apply flat (6,239 MW) more than they over-apply it (2,787 MW), the same direction
    as NEISO, MISO and SPP.
* **Result on the NWPP fleet:** 166 RoR-class and 126 reservoir-class plants (EHA). Of those, 27 are
  `regulated_chain`. **153–154 LP plants / 2,373 MW are pinned flat**, all of them off the chain.

## 3. Prediction (zero LP, `scripts/probes/_nwpp49_pondage_phase0.py` → `ror_split_chain_exempt`)

The pro-rata proxy (each plant gets the keeper's fleet hydro shape × its budget share) is replaced by
the mechanism's own flat level, budget/hours clipped to nameplate. This **over-states** the effect, so
it is an upper bound.

| year | hydro intra-day sd ratio (model ÷ EIA-930), keeper → **predicted** | coal r, keeper → bracket | coal r_intra bracket | hydro TWh Δ |
|---|---|---|---|---|
| 2023 | 1.075 → **0.997–1.075** | 0.659 → 0.659–0.682 | 0.374–0.523 | ≈ 0 |
| 2024 | 1.155 → **1.066–1.155** | 0.617 → 0.617–0.682 | 0.396–0.658 | ≈ 0 |
| 2025 | 1.169 → **1.082–1.169** | 0.638 → 0.638–0.700 | 0.365–0.572 | ≈ 0 |

**C4 is predicted to FAIL in 2023 and 2024.** 2025 reaches 0.700 only at the implausible edge where
coal absorbs all the removed swing.

Interaction, stated rather than modelled: the RoR flat base is subsumed into the Q95 min-flow floor.
`build_hydro_fleet` re-spreads the remainder of that floor over the reservoir class, so the total
forced base is unchanged. The proxy ignores this re-spread.

## 4. Kill condition (`scripts/probes/_nwpp49_gates.py --arm ror_chain_exempt`, committed now)

* **INERT → I:** the intra-day ratio falls < 0.010 in **every** year (arm ≥ 1.065 / 1.145 / 1.159).
* **OVERSHOOT → R:** the ratio falls below 0.95 in any year; **or** hydro annual energy moves > 1.0 TWh
  (keeper 106.872 / 107.879 / 113.077); **or** any C1 COAL row leaves ±8.00 TWh.
* C4 is **not** a limb (rule 1). C1 passes by only 0.79 TWh (2023 CC_REGULAR −7.213 vs ±8.00), so any
  flip is reported at full magnitude.

## 5. G-DRIFT (rule 29(b)): `f3a883cf..HEAD`, backcast path

| hunk | verdict | reason |
|---|---|---|
| `demand_balance_screen` field, `eia930/demand.py` screen, CLI plumbing (`run_calibration*.py`, `runner.py`) | INERT | GATED default off, absent from the keeper recipe; the screen runs only when armed |
| `ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE` + `_eia860_current_ba_recoded` | INERT | `{"SOCO": True}` only |
| `benchmark_semantics.EIA930_GAS_FOLD_REFUTED` | INERT | SOCO only; benchmark-only |
| EIA-923 builder repair (`_backfill_eia923_*`, `_operating_window`, `_reattribute_dual_fuel_oil`, `_benchmark_eia923_frame`) | **INERT for the LP**, measured | Regenerated both frames (keeper `84bb6ac40d29`, HEAD `0c4cb0be34ca`). The only change is Hunter 6165 2023 COAL_BIT, +1.21 GWh (16.2300 → 16.2314 TWh class total). Biomass and other classes are identical, so the must-run injection the LP reads is unmoved. The benchmark moves by 0.0014 TWh, which is reported |
| this lane's classifier rule | the arm | acts only when `hydro_ror_split` is armed; NWPP has no committed run that arms it |

**All hunks are INERT, so the keeper's committed bundle is the control. No control solve.**

## 6. Legs (rule 36), and what makes a leg valid

* Three year-isolated shards (2023, 2024, 2025), each pinned to this commit's full SHA. Each runs
  `curate_hydro_plant_modes.py --iso NWPP`, then
  `replay_keeper.py results/calibration/nwpp47_gridwind_span --out-dir results/calibration/nwpp49_ror_<y>
  --years <y> --set hydro_ror_split=true`.
* **Hard stops, checked by the shard:**
  * The curate log shows `'regulated_chain': 27`.
  * The solve log shows `RoR split — N/M plants flat` with N 153–154 (M ≈ 280, the LP hydro fleet).
  * `run_config` reads `hydro_ror_split`, `hydro_cascade_coupling`, `hydro_dispatch_envelope`,
    `hydro_min_flow_floor` and `nwpp_grid_carried_wind_served` all true, with `hydro_backfill_year`
    2024.
* Each shard pushes its FULL bundle, including `dispatch/<y>_P1.parquet` (rule 34(a)). The parent
  composes, scores, registers and asks the promotion question (rule 31). Budget: ~60–100 min per
  shard.

## Addendum (2026-09-24, after launch, before any leg was scored)

* **Hard-stop 2's count was wrong for 2023, and the 2023 shard correctly stopped on it.** The solve
  pins **157** plants flat in 2023, not 153–154. The four extra plants are tiny RoR plants with no
  2023 EIA-923 series: Pilot Butte 674, Drop 2 6507, Drop 3 6508 and Newhalem 9842, about 8 MW in
  total. They enter the 2023 fleet only through the keeper's `--hydro-backfill-year 2024`. My count
  used the budget table's `loader_kept` flag, which predates the backfill. This is fleet composition,
  not a classifier defect. 2024 and 2025 read 154, as pre-registered. The relaunched 2023 shard's
  hard stop is 157.
* No threshold, prediction or kill limb changed.
