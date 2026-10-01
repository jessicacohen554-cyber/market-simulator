# PRECOMMIT — NWPP-NEXT-9: same-year measured receipts on the monthly coal pile, 2019–2025

**Control:** keeper #15 `2026-09-28-nwppnext8-coal-monthly-pile`, compared against its committed bundle
`results/calibration/nwppnext8mp_span` (rule 29(b) form 4). No control solve.
**Parent:** zero LP. Seven year-isolated shards (rule 36), one arm.

## 0. Why (zero-LP driver census of the last failing record)

C4 coal 2023 is r 0.695 / NRMSE 0.283 against the 0.70 floor. It reproduces exactly from the keeper's committed
`hourly/class_hourly_2023.parquet` against `run_calibration_full._eia930_frame(2023, 'NWPP')` (0.6949 / 0.2826).

**Per-plant census (keeper #15 payload `m_mon` against CAMPD gross load, 2023, GWh).**

| Plant | Model Jan–Mar | CEMS Jan–Mar | Model Oct | CEMS Oct | Model annual | CEMS annual |
|---|---|---|---|---|---|---|
| Jim Bridger 8066 | 1393 / 1217 / 984 | 906 / 416 / 294 | 629 | 1267 | 9179 | 9109 |
| Hunter 6165 | 898 / 768 / 577 | 648 / 580 / 365 | 226 | 503 | 6455 | 4691 |
| Huntington 8069 | 599 / 541 / 511 | 612 / 389 / 327 | 332 | 215 | 5818 | 3831 |

- Bridger alone is +1.98 TWh of the ~3.7 TWh Jan–Mar over-burn. All four units were **online** Feb–May 2023 at
  ~20 % load (unit peaks of 406–571 MW were still reached). CAMPD outage windows cover only BW73/74 from Mar 10 to May 14.
  So this is fuel conservation, not an availability event.
- **EIA-923 tells the story.** Page 5 receipts (TBtu) 2022 → 2023 fell 105.1 → 86.6 at Bridger, 58.8 → 39.2 at Hunter
  and 56.0 → 26.5 at Huntington.
- December stocks were at record lows: Bridger 1,285 → 798 kt, Hunter 1,244 → 514 kt.
- Bridger's Jan–Apr 2023 receipts were 5.2 / 5.7 / 5.0 / 2.5 TBtu, against the ratable 8.9 TBtu/month the pile assumes
  from the 2021–22 mean. The yard then rebuilt its pile Feb–May, burning 4.8 / 3.7 / 2.1 / 4.2 TBtu.
- **Keeper #15 cannot see this.** Its pile sizes year Y's inflow from Y−1/Y−2 receipts, spread flat (C/12). In 2023
  that overstates PacifiCorp's available coal by ~70 TBtu (~6.5 TWh).

**Rejected at phase 0, never solved: "the pile never drops below the least it has held" (S_min).** This would mirror
the floor's S_max, but the data contradict it: Bridger drew 0.33 Mt below its prior minimum in 2022. It would have
wrongly cut 2021–22 coal by up to 2 TWh (rule 1). Census: `/tmp` scratch, numbers recorded here.

**Upper bounds (scaling the coal hourly monthly; never a prediction).**

| Case | Coal 2023 r |
|---|---|
| Bridger Jan–May at CEMS | 0.747 |
| Bridger all months at CEMS | 0.784 |
| Measured-receipt ceiling, Bridger only, Jan–Apr | ~0.718 |

## 1. Owner decision card (2026-09-28)

| Card | Ruling |
|---|---|
| C4 coal 2023 route | **Backcast receipts overlay** (reopens the NEXT-8 "flat ratable C/12" card on this census) |

## 2. The arm (one config key, one mechanism)

`coal_monthly_pile_measured_receipts`: absent → **True**. It requires `coal_fuel_inventory_monthly_pile` and is gated to
`COAL_TAKE_FLOOR_ISOS` (NWPP). The pile rows are already backcast-only, so the forecast path cannot move.

Per yard and month-end `m`, the ratable `m/12` receipts are replaced by the year's **own** EIA-923 Page 5 lots:

```
max(0, (S_dec − S_max)·hc + cumC_Y(m))  ≤  Σ_{g∈yard, t≤end m} HR·P + shortfall  ≤  S_dec·hc + cumR_Y(m)
```

- `R_Y` is every lot received. `C_Y` is the contract lots (purchase types C / NC / T). Each lot is taken at its own
  reported heat content.
- **Fixed ex ante:**
  - A yard with no same-year Page 5 row keeps the ratable profile. A missing input is never substituted with zero.
  - A year with no curated receipts file keeps every yard ratable. **2025 has no such file, so 2025 is inert.**
  - Both feasibility clips are unchanged: floor ≤ ceiling, and floor ≤ what the rowed units can burn by that month-end.
- **Month 12 is no longer the NEXT-7 annual identity.** The annual inflow becomes the realised R_Y (ceiling) and C_Y
  (floor), in place of the Y−1/Y−2 proxies. Same rows, same identity, realised inflow (rule 19).
- **Rule 13 classification.** This is a backcast overlay of a realised physical fuel-supply quantity. It comes from the
  same Page 5 table the F923 delivered-price overlay reads. It is never a forecast methodology.
  - **Stated risk:** at the mine-mouth yards (Bridger, conveyor/truck), receipts partly follow burn.
- **Zero free parameters.** The DOF ledger is unchanged at 5 entries.

Code:
- `data/coal_fuel_inventory.py::build_coal_measured_receipts`, plus the `measured=` input of `build_coal_monthly_pile`.
- `run_calibration.resolve_coal_measured_receipts`, and the wiring in `run_year`.
- Registration: `_CACHE_KEY_OPTIONAL_FIELDS`, frozen default `"False"`, `TIER_TAGS`, the forecast-parity declaration, and
  the matrix row with a cell in every shard (rule 28(c)).
- Tests: `tests/unit/data/test_coal_measured_receipts.py`, 13 tests. The NEXT-8 pile tests still pass.

## 3. Phase 0 (zero LP): `scripts/probes/_nwppnext9_measured_receipts_phase0.py`

The probe rebuilds keeper #15's fleet on its own recipe plus the arm, and calls the builders exactly as `run_year`
does. Output: `results/phase0/nwpp/_nwppnext9_measured_receipts_phase0.json`. The ratable pile still asserts month 12 =
the annual rows in every year.

Each row sums over yards how far keeper #15's cumulative monthly coal sits **above the measured ceiling** or **below the
measured floor** (TWh). This is the footprint the LP must move.

| Year | Yards measured / ratable | Ceiling excess, Jun / Dec | Floor gap, Jun / Dec |
|---|---|---|---|
| 2019 | 14 / 2 | 0.29 / 1.13 | 0.84 / **3.98** |
| 2020 | 14 / 2 | 0.09 / 0.96 | 1.69 / **2.37** |
| 2021 | 13 / 2 | 0.06 / 0.20 | 0.51 / 0.99 |
| 2022 | 13 / 1 | 0.06 / 1.80 | 0.09 / 0.23 |
| 2023 | 13 / 1 | 1.49 / **4.35** | 0.06 / 0.34 |
| 2024 | 13 / 1 | 0.00 / 0.01 | 0.12 / 1.51 |
| 2025 | none (no 2025 receipts file) | 0 / 0 | 0.05 / 0.05 (keeper #15's own) |

In 2023 the measured ceiling at Bridger / Hunter / Huntington ends at 9.23 / 4.65 / 3.29 TWh, against keeper #15's 9.18 /
6.46 / 5.82 and CEMS gross 9.11 / 4.69 / 3.83.

## 4. G-DRIFT (rule 29(b) form 4) against keeper #15's `git_sha` e7478536

### 4a. Verdict: ALL INERT, so form 4 is valid and keeper #15's bundle is the control

- **Scope.** `git diff e7478536 origin/main(40fc286b)` over `src/market_sim`, `scripts/run_calibration*.py`,
  `scripts/lib`, `data/raw/_validation-source` and `data/raw/reference`: 42 files. The hunk-by-hunk table is in the
  lane's audit, and the classes are summarised here.
- **Unconditional hunks.**
  - New `CAMPD_UNIT_PLANT_REMAP` rows: facilities in LA/OK/WI. CAMPD is read per state and none is in NWPP's states.
  - Split-child heat-rate fallback in `campd_bins.resolve_bin_heat_rates`: ERCOT-only `load_campd_bins`.
  - Plant-entry helpers: `ISO_PLANT_ENTRIES` holds ERCOT only.
- **Flag-gated hunks, off in keeper #15's recipe (absent in every `run_config_<Y>.json`).**
  - `nyiso_ne_ac_node`, `unit_outage_rederive_peaker_windows`, `pjm_da_virtual_settle_financial`.
  - `campd_st_gas_span_coverage`, `campd_split_remap_companions`.
  - `caiso_import_cap_floor_static`, `caiso_tac_shares_standard_time`, `caiso_eia930_clock_repair` (the CISO clock
    repair also needs `ba_code == "CISO"`).
- **Other ISOs' branches:** NYISO, CAISO, PJM, SOCO.
- **Code no solve reaches:** reported-only readers, docstrings and records.
- **Retired `nyiso_firm_imports`:** the recipe value (False) equals the retired value, and `replay_keeper` strips it.
- **Cache key.** Keeper #15's config gives an identical `cache_key()` on both trees:
  2019 `8057c70ec86d3b29`, 2023 `69c0871e61f2af12`, 2025 `947d791fda242da6`. NWPP's solve-surface moved rows are
  identical.
- **Empirical check.** The 2025 leg (arm inert, no 2025 receipts) must reproduce keeper #15's 2025 numbers.

## 5. Recipe (per shard, year Y)

Keeper #15's recipe (PRECOMMIT-nwppnext8 §5), plus one key:

```
mkdir -p /tmp/n49 && git fetch --depth=1 origin 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 \
  && git archive 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 results/calibration/nwpp49_ror_span | tar -x -C /tmp/n49
python3 scripts/data/curate_hydro_plant_modes.py --iso NWPP
python3 scripts/data/curate_coal_receipts.py && python3 scripts/data/curate_coal_stocks.py
python3 scripts/replay_keeper.py /tmp/n49/results/calibration/nwpp49_ror_span \
  --out-dir results/calibration/nwppnext9mr_<Y> --years <Y> \
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
  --set coal_monthly_pile_measured_receipts=true \
  [<Y> in 2019, 2020, 2021, 2022 ONLY:] --set hydro_backfill_year=null \
  --note "NWPP-NEXT-9 measured receipts: keeper #15 recipe + same-year EIA-923 Page 5 receipts on the monthly pile"
```

## 6. Hard stops (any miss means STOP, no push)

1. `git rev-parse HEAD` equals the pin.
2. `sha256sum data/raw/_processed-legacy/campd_ct_heat_rates_NWPP.csv` =
   `29baa2f1ecfa10d9734c7e44cc306a88d527adb28968ea260f3409de37d7ff92`.
3. `scenario_config` in `run_config.json` differs from keeper #15's
   `results/calibration/nwppnext8mp_span/run_config_<Y>.json` only in `coal_monthly_pile_measured_receipts` (True).
   Keys absent in the keeper and False/None/default in the arm are also accepted.
4. `meta.json` `hydro_backfill_year` is null for 2019–2022 and 2024 for 2023–2025.
5. `hourly/system_<Y>.parquet` P1 summed `demand` equals keeper #15 ±0.05 TWh: 279.581 / 292.940 / 289.358 / 298.960 /
   280.261 / 290.216 / 302.532.
6. **Arm-live.** The solve log carries all of these:
   - `coal per-yard budget (NWPP <Y>): N yards`;
   - `coal take floor (NWPP <Y>): M yard rows floored`, with M > 0;
   - `coal monthly pile (NWPP <Y>): N yard rows x 12 month-ends`;
   - `NWPP Path 76 (Alturas): NWPP-NW<->NWPP-SNV 300 MW appended`;
   - for 2019–2024, `coal measured receipts (NWPP <Y>): K yard rows measured` with K equal to §3's count;
   - for 2025, `coal measured receipts (NWPP 2025): no curated same-year receipts`.
7. The bundle contains `dispatch/<Y>_P1.parquet`, `hourly/class_hourly_<Y>.parquet`, `hourly/system_<Y>.parquet` and
   `hourly/hydro_cascade_<Y>.parquet`.
8. The solve is not infeasible. An infeasible or Unknown LP is a STOP, with the log reported and no retry.

## 7. Predicted, reported and never gated

- **2023.** Coal falls ~2–4 TWh, mostly at Bridger Feb–Jun and Hunter/Huntington Jul–Dec. Gas rises. C4 coal 2023 is
  expected to cross 0.70, but thinly: the estimate is ~0.72, and the Hunter/Huntington H2 cut is not in that estimate.
- **2019 and 2020.** The measured contract take raises the floor in H2 (up to 4.0 / 2.4 TWh by December). Keeper #14's
  2019 monthly census had coal *low* in Jun–Oct, so C4 coal 2019 may improve. It is at risk if the floor overshoots.
  The S_max history for 2019 is one year long (2018 only).
- **2022.** The ceiling cuts ~1.8 TWh in H2 (Bridger, Hunter).
- **2025.** Expected byte-identical to keeper #15, which doubles as an empirical drift check on the G-DRIFT audit.
- **C1 annual coal moves** in every year from 2019 to 2024, because month 12 now carries realised inflow. C1 is
  reported, not gated here; its status stays with the verdict.
- Also reported: unserved energy, the per-shard shortfall paid, and solve time.

**Promotion** follows the owner's standing structure ruling: promote if structural integrity improves, with every
regression reported at full magnitude.
