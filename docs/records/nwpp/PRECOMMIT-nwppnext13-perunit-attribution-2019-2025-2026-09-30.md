# PRECOMMIT — NWPP-NEXT-13: CAMPD per-unit attribution, 2019–2025

Written before any solve. Template: `PRECOMMIT-nwppnext12-boardman-membership-2019-2025-2026-09-29.md`.
Evidence: `FINDING-nwppnext13-wefor-and-perunit-phase0-2026-09-30.md` §2.

## 1. Arm

Keeper #17 (`2026-09-29-nwppnext12-boardman-membership`) plus exactly one key:
`campd_per_unit_attribution: False → True`. It is an existing, default-off field (nyiso-175b/176) that selects BOTH
NWPP `-perunit-` companions, new in this PR:

| file | sha256 | construction |
|---|---|---|
| `data/raw/campd-unit-outages-perunit-NWPP.csv` | `ff5b0644553095e6600691673f3442877e287b42623a772bda052b4df734e5f3` | `derive_campd_unit_outages.py --iso NWPP --years 2019..2025 --per-unit-crosswalk`, verbatim: keeper #17's extract (Boardman rows included) minus Clark 2322's 2,951 and Silverhawk 55841's 46 GT-peaker windows |
| `data/raw/_processed-legacy/thermal_tranches-perunit-NWPP.csv` | `2c502ad894ca4e029d3df1470bb9ee5293eb563619c7e88f40211094fc40aae5` | `derive_thermal_tranches.py --iso NWPP --years 2023 2024 2025 --per-unit-attribution`, verbatim, with this PR's two deriver repairs |

The per-unit outage selector outranks `unit_outage_membership_repair` (`outages.unit_outage_csv_for_iso`); the key
stays `True` in the recipe and the Boardman windows are carried by the per-unit file itself.

Basis: rule 14 (keeper #17's Clark CC is available 0.002–0.68 TWh/yr against 0.43–0.86 TWh generated; three tranche
rows carry CFs above 100 %; Jim Bridger has no measured COAL row) and rule 23 (new derive outputs, same sources,
fixed deriver, no residual cited). Crosswalk inputs are EIA-860 prime movers, CAMPD unit types and CAMPD
`primaryFuelInfo` (rule 13 forward-regenerable). **DOF +0.** Offer multipliers byte-identical. Rule 19: one field,
both artifacts, by the field's design.

## 2. Prediction (zero LP) — and what would NOT be a reason

- CC_REGULAR available +3.0–3.7 TWh every year (Clark); +2.81 / +2.99 TWh (Silverhawk 2024 / 2025).
- Jim Bridger take-or-pay must-run 953.5 → 351.8 MW (2019–2023), proportionally on the 1,028 MW coal bin in 2024–25.
  Coal energy is expected to fall and CC to rise; C4 coal 2023 can move in either direction.
- Every year moves (the tranche artifact is static across years).
- The owner's standing ruling applies: promote if structural integrity improves, even if a gate regresses, with every
  regression reported at full magnitude. The decision rests on rule 14, not the residual.

## 3. G-DRIFT (rule 29(b)) against keeper #17's `git_sha` 0b1d2cfe

NEXT-12 audited main through `0a5eb910` as all inert; `0b1d2cfe` adds only data. Since then, on the backcast path:

| commit | what | class |
|---|---|---|
| 2386952f, 28fb8c45 R-ERCOT-17 | `ercot_south_texas_pooled_basis` (default off, ERCOT basis module) + `ercot_zonal_gas_hub.csv` rows | INERT (another ISO's branch) |
| 853ff96f NYISO-NEXT-13 | `forecast_parity_registry.py` declaration | INERT (forecast-only) |
| this PR | `scripts/data/derive_thermal_tranches.py` (a deriver, not the solve path); the two `-perunit-` NWPP files (read only under the arm); `campd-unit-outages-short-screened-NWPP.csv` (read only under `wefor_residual_short_screened_coal`, off); probes, tests, docs | INERT except the arm itself |

**ALL INERT.** The solve-surface fingerprint in each leg's `solve_surface.json` is the mechanical second check.

## 4. Recipe (per shard, year Y)

```
mkdir -p /tmp/n49 && git fetch --depth=1 origin 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 \
  && git archive 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 results/calibration/nwpp49_ror_span | tar -x -C /tmp/n49
python3 scripts/data/curate_hydro_plant_modes.py --iso NWPP
python3 scripts/data/curate_coal_receipts.py && python3 scripts/data/curate_coal_stocks.py
python3 scripts/replay_keeper.py /tmp/n49/results/calibration/nwpp49_ror_span \
  --out-dir results/calibration/nwppnext13pu_<Y> --years <Y> \
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
  [<Y> in 2019, 2020, 2021, 2022 ONLY:] --set hydro_backfill_year=null \
  --note "NWPP-NEXT-13 per-unit attribution: keeper #17 recipe + campd_per_unit_attribution"
```

## 5. Hard stops (any miss means STOP, and no push)

1. `git rev-parse HEAD` equals the pin.
2. `sha256sum data/raw/_processed-legacy/campd_ct_heat_rates_NWPP.csv` =
   `29baa2f1ecfa10d9734c7e44cc306a88d527adb28968ea260f3409de37d7ff92`, and both §1 files match their sha256.
3. `scenario_config` in `run_config.json` differs from keeper #17's `results/calibration/nwppnext12mr_span/run_config_<Y>.json`
   only in `campd_per_unit_attribution` (True). Keys absent in the keeper and False/None/default in the arm are accepted.
4. **Arm-live:** `resolved_inputs.campd_unit_outages.path` = `data/raw/campd-unit-outages-perunit-NWPP.csv` and
   `resolved_inputs.thermal_tranches.path` = `data/raw/_processed-legacy/thermal_tranches-perunit-NWPP.csv`, with the
   §1 shas.
5. `meta.json` `hydro_backfill_year` is null for 2019–2022 and 2024 for 2023–2025.
6. P1 summed `demand` equals keeper #17 ±0.05 TWh: 279.581 / 292.940 / 289.358 / 298.960 / 280.261 / 290.216 / 302.532.
7. The keeper's log lines are present: `coal per-yard budget`, `coal take floor ... M yard rows floored` (M > 0),
   `coal monthly pile ... x 12 month-ends`, `NWPP Path 76 (Alturas)`, and for 2020 only
   `unit-outage exit_ym routing live (year 2020): plants [6076]`.
8. The bundle contains `dispatch/<Y>_P1.parquet`, `hourly/class_hourly_<Y>.parquet`, `hourly/system_<Y>.parquet` and
   `hourly/hydro_cascade_<Y>.parquet`.
9. The solve is not infeasible. An infeasible or Unknown LP is a STOP, with the log reported and no retry.

## 6. Decision

- Compose with `scripts/probes/_nwpp42_compose_span.py --skip-diagnostics` into
  `results/calibration/nwppnext13pu_span` (2023 leg first); legitimacy diagnostics; attestation; registration with
  `--no-prune`; `calibration_verdict`, diffed per (criterion, year, key) record against keeper #17.
- Promote if the arm is live in every year and the solves are feasible. The criterion is structural (rule 14), and
  every moved record is reported at full magnitude. The promotion goes to the owner as a decision card.
