# PRECOMMIT — NWPP-NEXT-4: coal committed band nested on must-run (owner card D3), 2019–2025

**Lane:** NWPP-NEXT-4, after keeper #10 `2026-09-25-nwppnext3-plant-basis`.
**Arm id (on registration):** `2026-09-25-nwppnext4-coal-nested`.
**Lever:** queue item 1 (C4 coal amplitude). Phase 0 found the cause, and the one structural defect in it is
owner card D3, the FINDING-nwpp-48 §6 stacking defect (deferred at NWPP-49, never refused).
**Written before any leg is solved.** The parent session runs no LP (rule 32(a)).
**Probe:** `scripts/probes/_nwppnext4_coal_census.py` → `results/calibration/_nwppnext4_coal_census.json`.
It reproduces keeper #10's C4 coal r in all seven years exactly (0.759 / 0.718 / 0.747 / 0.769 / 0.683 / 0.617 / 0.689).

## 0. In one paragraph

In 2024–25, 84–99 % of the coal energy at Colstrip, Hunter, Huntington, Bonanza, Dave Johnston and Jim Bridger comes
from the fuel-cheap `_mustrun` + `_committed` block ($4.5–5.3/MWh), which runs in every hour. The bands above it are
**bang-bang**: at cap or at zero, almost never partial. They are at zero in most hours of 2024–25 because Utah's
measured delivered coal cost roughly **doubled** from 2022 to 2024 (EIA-923: Hunter $1.83 → $3.46/MMBtu, Huntington
$2.11 → $3.66, Bonanza $2.38 → $3.36). That puts the econ offers at $40–48, against model prices of $17–27 from March
to September. So the model plant is a flat block plus an econ tranche that is almost never on. That is why 2019–22 pass
C4 and 2023–25 fail. Separately, the flat block is **2.0× the measured minimum stable load**: the tranche artifact
defines both shares as levels from 0 MW, and the fleet builder stacks them. This lane repairs that stacking and
nothing else. **The zero-LP prediction is that C4 gets worse, not better.** It is solved anyway as a rule-14
accuracy repair under the owner's standing structure ruling, and every cost is stated here before the solve.

## 1. Phase 0 (zero LP)

### 1.1 Where each plant's energy sits (keeper #10, P1)

`cheap` is the `_mustrun` + `_committed` share of plant energy. `sd` is in MW: I is the mean within-day sd, D is the sd of
daily means. `p10r` is the CAMPD running-hour p10 gross output.

| year | plant | model TWh | CAMPD TWh | cheap share | sd I model / CAMPD | sd D model / CAMPD | r (plant hourly) |
|---|---|---|---|---|---|---|---|
| 2021 | Hunter 6165 | 10.47 | 10.06 | 0.45 | 4 / 135 | 153 / 143 | 0.41 |
| 2022 | Huntington 8069 | 6.45 | 6.17 | 0.39 | 10 / 127 | 181 / 180 | 0.60 |
| 2024 | Colstrip 6076 | 8.89 | 9.92 | 0.99 | 2 / 87 | 453 / 506 | 0.85 |
| 2024 | Jim Bridger 8066 | 5.02 | 5.09 | 0.84 | 21 / 178 | 169 / 272 | 0.42 |
| 2024 | Hunter 6165 | 4.63 | 4.64 | 0.94 | 33 / 112 | 152 / 200 | 0.22 |
| 2024 | Bonanza 7790 | 3.50 | 3.42 | 0.99 | 1 / 68 | 54 / 87 | 0.28 |
| 2024 | Huntington 8069 | 3.21 | 3.06 | 0.88 | 2 / 107 | 135 / 143 | 0.01 |
| 2025 | Hunter 6165 | 5.00 | 7.56 | 0.92 | 34 / 193 | 140 / 155 | 0.25 |
| 2025 | Huntington 8069 | 2.96 | 4.74 | 0.93 | 22 / 166 | 79 / 195 | 0.22 |

The full census, every plant and year, is in the JSON.

### 1.2 Band states: bang-bang (hours at cap / partial / at zero, econ_low band)

| plant | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| Hunter | 8709 / 33 / 18 | 8720 / 32 / 8 | 4697 / 157 / 3834 | 366 / 129 / 8265 | 622 / 83 / 8055 |
| Huntington | 8004 / 116 / 640 | 8566 / 58 / 88 | 6713 / 139 / 1908 | 756 / 6 / 7998 | 406 / 36 / 8318 |
| Bonanza | 5547 / 0 / 2085 | 7665 / 4 / 827 | 6033 / 2 / 2413 | 1295 / 1 / 7320 | 1538 / 2 / 4316 |
| Jim Bridger | 3659 / 382 / 4719 | 7530 / 407 / 823 | 2134 / 186 / 6440 | 1729 / 76 / 6955 | 1595 / 64 / 7101 |

- The econ, econ_high and peak bands of a plant carry identical offers (NWPP-46), so the plant's upper half flips
  wholesale.
- Intra-day swing therefore exists only in the few hours a band sits at the margin.
- `_mustrun` and `_committed` are at cap in ≥ 8,048 hours of every plant-year listed.

### 1.3 The flat block against the measured minimum stable load (2024)

| plant | stacked block (keeper) MW | nested block MW | CAMPD running p10 MW |
|---|---|---|---|
| Colstrip 6076 | 1,450 | 776 | 598 |
| Hunter 6165 | 608 | 304 | 231 |
| Dave Johnston 4158 | 717 | 360 | 296 |
| Bonanza 7790 | 442 | 221 | **221** |
| Huntington 8069 | 355 | 177 | **182** |
| North Valmy 8224 | 218 | 109 | **114** |
| TS Power 56224 | 184 | 92 | **92** |
| Naughton 4162 | 225 | 113 | 95 |

The block is nameplate × pct, before availability.

- `derive_thermal_tranches.py` defines `committed_pct` as the P5 of online-hour CF and `mustrun_pct` as the P5 of
  all-hour CF. Both are **levels from 0 MW**.
- `bins_to_fleet` sizes `_committed` = committed × nameplate **on top of** `_mustrun` = mustrun × nameplate.
- At an always-online plant the two levels coincide, so the block is exactly 2× the measured level.
- The nested block lands on the CAMPD running p10 within 5 MW at four plants.
- Total moved: **2,047.9 MW** from the cheap block to the econ band, at 9 plants.
- Untouched:
  - Jim Bridger (8066) and the four small plants: no measured COAL row, so they keep the group default, whose shares
    are increments by design.
  - Centralia, Wyodak, Hardin and Sunnyside: mustrun ≈ 0, so there is nothing to nest.

## 2. What changes (one new gated field, zero free parameters)

`ScenarioConfig.coal_committed_nested_on_mustrun` is default off and ISO-agnostic.

- **Seam:** `data/fleet/campd_bins.py::fleet_to_bins`. A coal plant **with a measured artifact row** takes
  `pct_mc = max(0, committed_pct − mustrun_pct)`.
- `_mustrun` is unchanged, its price is unchanged, and no floor is added. NWPP carries no coal sync pmin.
- The removed share falls to `pct_econ`, so the plant keeps every MW.
- Cache key: registered in `_CACHE_KEY_OPTIONAL_FIELDS` / `_DEFAULTS` at `"False"` in the same commit.
- Matrix: a row, plus a cell in all nine ISO shards (NWPP `O`, the rest `U`).
- Test: `tests/unit/data/test_coal_committed_nested_on_mustrun.py`, on NWPP's own fleet. Off is byte-identical and
  every non-target row is byte-identical.
- **Arming:** `--set coal_committed_nested_on_mustrun=true` on the replay recipe. No other ISO moves.
- **Rule 14:** this corrects a units misread of a measured artifact. It is not a new level.
- **Rule 1 / rule 17:** it is not a floor and not a tuned value. It withdraws half of a price-cheap block that has no
  measurement behind it.
- **Rule 19:** it moves the size of one band. The NWPP-44 regulated take-or-pay pricing of the committed band is
  untouched and still prices whatever committed band remains.
- **Offer fingerprint:** `sha256(json.dumps(sc["offer_curve_by_group"], sort_keys=True))` is unchanged at `6a13731e…`.
  The field changes band sizes, not multipliers.
- `authorized_price_tuning`: none. Price is unscored (rubric v3.8).

## 3. Zero-LP prediction (price-taker bracket), reported rather than gated

**How the bracket is built:**
- In an hour where the plant's econ band clears (reduced cost ≤ 0), the moved MW still run, so output is unchanged.
- Otherwise the committed MW above the new cap are lost.
- "full" assumes every such hour loses them. "half" assumes half. Price feedback (gas or hydro setting a higher price
  when coal withdraws) puts the truth between "half" and "full". It can also make coal marginal, which is the only
  route to intra-day swing.

| year | C4 coal r keeper | full | half | coal TWh keeper | lost (full) | EIA-930 coal TWh |
|---|---|---|---|---|---|---|
| 2019 | 0.759 | 0.681 | 0.723 | 57.71 | 10.20 | 54.55 |
| 2020 | 0.718 | 0.716 | 0.729 | 43.71 | 6.94 | 51.94 |
| 2021 | 0.747 | 0.731 | 0.741 | 55.14 | 5.22 | 50.14 |
| 2022 | 0.769 | 0.756 | 0.766 | 60.77 | 5.05 | 49.41 |
| 2023 | 0.683 | 0.631 | 0.659 | 49.49 | 6.59 | 42.27 |
| 2024 | 0.617 | 0.557 | 0.592 | 36.98 | 10.41 | 38.30 |
| 2025 | 0.689 | 0.581 | 0.644 | 35.93 | 9.18 | 42.26 |

**Stated costs before the solve:**
- **C4 is predicted to get worse.** In 2023–25 it is still FAIL either way. **2019 can flip PASS → FAIL.**
- **Coal volume falls.** In 2021–23 that moves toward actual (coal is long by +7.7 / +13.5 / +9.3 TWh; queue item 3).
  In 2024–25 it moves away (coal goes short).
- The gas family absorbs the difference. **CC_REGULAR 2024 (+3.90 against ±8.00) can flip C1 to FAIL** if more than
  about 4 TWh lands there.

**What the arm does not do:**
- It does not fix the fuel-price and price-level mismatch in §0. That is the real C4 driver in 2023–25, and it is
  routed (§7).

## 4. G-DRIFT: keeper `git_sha` `dad798cd` → pin (rule 29(b) form 4)

The diff is `git diff dad798cda0ab4c5f1ab2ea7241c364fbd684576e <pin> --name-status` over `src/market_sim`,
`scripts/run_calibration*.py`, `scripts/replay_keeper.py`, `scripts/lib`, `_validation-source`, `reference`,
`_processed-legacy` and `nwpp-hydro`.

| Hunk | Class | Why |
|---|---|---|
| `nyiso_ldc_generator_delivered_gas` (scenarios field, fuel/basis/nyiso.py, fuel/__init__ exports, run_calibration call) | INERT | Default-off field, absent from the NWPP recipe. The function returns at `if not getattr(config, …)` and again at `if config.iso != "NYISO"`. |
| miso-273 `wefor_residual_short_screened_coal` (scenarios field + cache key, fleet/arrays.py, outages.py `short_screened_coal_shares`, floor_mechanisms registry default) | INERT | Default-off field, absent from the NWPP recipe. The arrays.py branch runs only under `getattr(config, "wefor_residual_short_screened_coal", False)`, and the outages.py helpers are called only from there. |
| **This lane** (scenarios field + cache-key registration, campd_bins seam) | **LIVE** | The arm. Off-path byte-identity is pinned by test. |

**Verdict:** form 4 is valid. The committed `nwppnext3_span` bundle is the control, and no control solve is spent.

## 5. Recipe (per shard): the keeper #10 recipe plus ONE `--set`

```
mkdir -p /tmp/n49 && git archive 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 results/calibration/nwpp49_ror_span | tar -x -C /tmp/n49
python3 scripts/data/curate_hydro_plant_modes.py --iso NWPP
python3 scripts/replay_keeper.py /tmp/n49/results/calibration/nwpp49_ror_span \
  --out-dir results/calibration/nwppnext4_<Y> --years <Y> \
  --set eia860_vintage_tracks_solve_year=true \
  --set measured_ct_heat_rates=true --set measured_coal_heat_rates=true \
  --set measured_st_heat_rates=true --set measured_cc_heat_rates=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_partial_outage_windows=true \
  --set mid_vintage_exit_carry=true --set partial_plant_exit_carry=true \
  --set nwpp_demand_plant_basis=true \
  --set coal_committed_nested_on_mustrun=true \
  [<Y> in 2019, 2020, 2021, 2022 ONLY:] --set hydro_backfill_year=null \
  --note "NWPP-NEXT-4: keeper #10 recipe + coal_committed_nested_on_mustrun (owner card D3)"
```

## 6. Years, shards and hard stops

**Years (rules 34(c), 35(c), 36):** the registered NWPP set is {2019 … 2025}. All seven are solved, one shard per year.

**Shard hard stops.** Any miss means STOP, with no push.
1. `git rev-parse HEAD` equals the pin. The pre-authorized command is
   `git fetch --depth=1 origin <PIN> && git checkout --detach <PIN>`. It checks out the pin; it is not a sync.
2. `run_config.json` `scenario_config` shows every §5 flag true, including `nwpp_demand_plant_basis` and
   `coal_committed_nested_on_mustrun`. The offer fingerprint is `6a13731e…`.
3. `meta.json` `hydro_backfill_year` is null for 2019–2022 and 2024 for 2023–2025.
4. `hourly/system_<Y>.parquet`, pass P1: summed `demand` equals keeper #10 ±0.05 TWh. The values are 279.581 /
   292.940 / 289.358 / 298.960 / 280.261 / 290.216 / 302.532.
5. **Arm-live check.** In `hourly/unit_hourly_<Y>.parquet`, the `_committed` units of plants 6165, 8069, 7790, 8224
   and 56224 carry `cap_mw` sum 0 (or are absent). Plant 6076's `_committed` max `cap_mw` is ≤ 35 MW (the keeper's is
   ~688).
6. The bundle contains:
   - `dispatch/<Y>_P1.parquet`
   - `hourly/class_hourly_<Y>.parquet`
   - `hourly/system_<Y>.parquet`
   - `hourly/unit_hourly_<Y>.parquet`
   - `hourly/hydro_cascade_<Y>.parquet`

   `run_config_<Y>.json`, `metrics.json` and `legitimacy_diagnostics.json` are not required.

## 7. Reported, never gated; routed

**Reported, never gated:**
- C1–C8 per year against keeper #10.
- Class TWh deltas, coal r, slack/VOLL and CT_PEAKER.
- Promotion follows the owner's standing instruction: promote on improved structure, with regressions reported at full
  magnitude. Otherwise the promotion question is asked (rule 31).

**Routed, not absorbed:**
1. **The C4 driver in 2023–25 is the econ band's bang-bang against the price level.** Real PacifiCorp coal runs at
   ~40 % CF and swings while its measured average fuel cost sits above the model price. That is conduct under a
   period fuel-take obligation (an energy budget), and the model has no mechanism for it.
   - `coal_fuel_inventory` raises outside MISO.
   - Any budget sized from same-year receipts is rule-13 forbidden.
   - This is an owner design question, not a lane lever.
2. **Jim Bridger has no measured COAL row** (the NWPP-48 attribution defect). It keeps the 45 % default must-run and
   is untouched here.
3. **The measured coal ladder** (NWPP-46, 0.821 / 0.932 / 1.004 / 1.029) stays routed. With bands at cap or zero,
   a 7.7 % slope cannot act.

## 8. Cost and retrievability

- Seven shards run in parallel, about 15–45 min per year.
- Each pushes its full bundle to `claude/nwppnext4-<Y>` (rule 34(a)), using the `.gitignore` negation and a plain
  `git add`.
- The parent composes (2023 leg first), registers, and lands the bundle on `main` before this lane's PR merges
  (rule 33(f)).
