# PRECOMMIT — NWPP-NEXT-14: EIA-923 CC-family heat rate (Clark) + per-unit fuel-split tranches (Bridger), 2019–2025

Written before any solve. Template: `PRECOMMIT-nwppnext13-perunit-attribution-2019-2025-2026-09-30.md`.
Evidence: `FINDING-nwppnext14-bridger-and-clark-phase0-2026-09-30.md`. Owner cards (2026-09-30): "EIA-923 CC-family HR",
"Both".

## 1. Arm

Keeper #18 (`2026-09-30-nwppnext13-per-unit-attribution`) plus exactly two keys:

| key | keeper #18 | arm | what it reads |
|---|---|---|---|
| `eia923_cc_family_heat_rates` (new, this PR) | absent / False | True | `data/raw/_processed-legacy/eia923_cc_family_heat_rates_NWPP.csv`, sha `cc9ac299d93ad256e7315c86b24cd9abed2535625561e496cf1dae32dada9d38` (`derive_eia923_cc_family_heat_rates.py --iso NWPP`) |
| `campd_unit_fuel_split` (existing; composes with per-unit since this PR) | False | True | `data/raw/_processed-legacy/thermal_tranches-perunit-fuelsplit-NWPP.csv`, sha `cf912778763969061ac5073859145830c27b5a4206487934577de0658fab4a96` (`derive_thermal_tranches.py --iso NWPP --years 2023 2024 2025 --per-unit-attribution --unit-fuel-split`) |

Both are rule-14 repairs with zero DOF: Clark 2322's CC rows load an impossible 3.007 MMBtu/MWh (EIA-923 measures
9.0–9.6), and Jim Bridger's per-unit coal row divides 2023 four-unit conduct by the 2025 bin. Rule 19: the heat-rate
field skips plants the eGRID family construction covers, and the fuel-split companion replaces the per-unit lines
rather than stacking on them. Offer multipliers are byte-identical. **DOF +0.**

## 2. Prediction (zero LP), and what would NOT be a reason

- LP-array delta: only Clark's three CC bins (heat rate 3.007 → 9.0–9.6) and Bridger's must-run split
  (351.8 → 343.3 MW in 2023; 174.1 → 169.9 in 2024–25) move.
- Clark CC falls from ~3.7 TWh/yr toward its EIA-923 0.43–0.86. C1 CC_REGULAR over-dispatch (2024–25) shrinks and
  CT_PEAKER under-dispatch shrinks. C4 coal 2023 moves little and in either direction.
- Owner standing ruling: promote if structural integrity improves, even if a gate regresses, and report every
  regression at full magnitude. The decision is rule 14, not the residual.

## 3. G-DRIFT (rule 29(b)) against keeper #18

Keeper #18's shards pinned `f2cfda46`, a pre-rebase commit of the NEXT-13 branch that is no longer reachable (the
shard branches were deleted on merge). The audit base is therefore keeper #18's own merge, `38c64917`: its PR carried
the pinned code plus composition and docs. Solve-path diff `38c64917..5e0599c8`:

| commits | what | class |
|---|---|---|
| 7105f162, 400d7bd6, 190af2c0 SPP-105 | `spp_gas_crow_residual_outage` (default off; `arrays.py` branch gated `_iso == "SPP"` + historic outages) and `spp_gas_outage.py` | INERT (another ISO's branch, default off) |
| 1f4793ae, 4ddb0ae4 NYISO-NEXT-17 | `nyiso_fg_split` (default off; every hunk gated `iso == "NYISO"` or `nyiso_fg_split_active()`) | INERT (another ISO's branch) |
| d757b216 R-CAISO-18 | `caiso_intertie_unprinted_year_measured_gas` (default off); `electric_power.state_electric_power_monthly_gas_eia923`, a new function reached only by that flag | INERT (another ISO's branch) |
| 13b721ea miso-292 | `_validation-source/actual_lmp.json` MISO rows (scorer bench) | INERT (another ISO's scorer data) |
| this PR | `eia860.py` seam (off unless armed); `campd_bins.py` selector (changes only when `campd_unit_fuel_split` AND `campd_per_unit_attribution`; no committed run arms both); deriver scripts; the two artifacts | INERT except the arm itself |

**ALL INERT.** The solve-surface fingerprint is unchanged (`solve_surface_register.py --diff origin/main`: 0 values
moved, 0 names added). `solve_surface.json` in each leg is the mechanical second check.

## 4. Recipe (per shard, year Y)

Identical to PRECOMMIT-nwppnext13 §4, with the two new `--set` lines and a new out-dir:

```
mkdir -p /tmp/n49 && git fetch --depth=1 origin 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 \
  && git archive 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 results/calibration/nwpp49_ror_span | tar -x -C /tmp/n49
python3 scripts/data/curate_hydro_plant_modes.py --iso NWPP
python3 scripts/data/curate_coal_receipts.py && python3 scripts/data/curate_coal_stocks.py
python3 scripts/replay_keeper.py /tmp/n49/results/calibration/nwpp49_ror_span \
  --out-dir results/calibration/nwppnext14_<Y> --years <Y> \
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
  --set unit_outage_exit_ym_from_eia860=true \
  --set unit_outage_membership_repair=true \
  --set campd_per_unit_attribution=true \
  --set eia923_cc_family_heat_rates=true --set campd_unit_fuel_split=true \
  [<Y> in 2019, 2020, 2021, 2022 ONLY:] --set hydro_backfill_year=null \
  --note "NWPP-NEXT-14: keeper #18 recipe + eia923_cc_family_heat_rates + campd_unit_fuel_split"
```

## 5. Hard stops (any miss means STOP, and no push)

1. `git rev-parse HEAD` equals the pin.
2. sha256: `data/raw/_processed-legacy/campd_ct_heat_rates_NWPP.csv` = `29baa2f1ecfa10d9734c7e44cc306a88d527adb28968ea260f3409de37d7ff92`;
   `data/raw/campd-unit-outages-perunit-NWPP.csv` = `ff5b0644553095e6600691673f3442877e287b42623a772bda052b4df734e5f3`;
   and both §1 files at their shas.
3. `scenario_config` in `run_config.json` differs from keeper #18's `results/calibration/nwppnext13pu_span/run_config_<Y>.json`
   only in `eia923_cc_family_heat_rates` (True) and `campd_unit_fuel_split` (True).
4. **Arm-live:** `resolved_inputs.thermal_tranches.path` = `data/raw/_processed-legacy/thermal_tranches-perunit-fuelsplit-NWPP.csv`,
   and the solve log carries `EIA-923 CC-family heat rate (NWPP): plant 2322 CC rows`.
5. `meta.json` `hydro_backfill_year` is null for 2019–2022 and 2024 for 2023–2025.
6. P1 summed `demand` equals keeper #18 ±0.05 TWh: 279.581 / 292.940 / 289.358 / 298.960 / 280.261 / 290.216 / 302.532.
7. The keeper's log lines are present: `coal per-yard budget`, `coal take floor`, `coal monthly pile ... 12 month-ends`,
   `NWPP Path 76 (Alturas)`, and for 2020 `unit-outage exit_ym routing live (year 2020): plants [6076]`.
8. The bundle contains `dispatch/<Y>_P1.parquet`, `hourly/class_hourly_<Y>.parquet`, `hourly/system_<Y>.parquet` and
   `hourly/hydro_cascade_<Y>.parquet`.
9. The solve is feasible. An infeasible or Unknown LP is a STOP, with the log reported and no retry.

## 6. Decision

Compose with `scripts/probes/_nwpp42_compose_span.py --skip-diagnostics` into `results/calibration/nwppnext14_span`
(2023 leg first); legitimacy diagnostics; attestation; registration with `--no-prune`; `calibration_verdict`, diffed per
(criterion, year, key) record against keeper #18. The promotion goes to the owner as a decision card, on structure
(rule 14), with every moved record at full magnitude.
