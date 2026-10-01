# PRECOMMIT — NWPP-NEXT-12: Boardman membership repair of the CAMPD outage extract, 2019–2025

Written before any solve. The template is `PRECOMMIT-nwppnext10-exit-ym-routing-2019-2025-2026-09-29.md`.

## 1. Arm

The recipe is keeper #16 (`2026-09-29-nwppnext10-exit-month-routing`) plus exactly one key:
`unit_outage_membership_repair: False → True`.

That key is an existing, default-off field (PJM-NEXT-2). It selects
`data/raw/campd-unit-outages-memberrepair-NWPP.csv`, which is new in this PR:

- sha256 `386a64d34635781c4e9c0dbe9111df4a9c9a8eb09632a3cde2b690c18a4d33b2`, 5,064 rows.
- Rows 1–5,058 are byte-identical to the committed `campd-unit-outages-NWPP.csv` (sha `73f1b0e8…`).
- The six added rows are Boardman 6106's windows (FINDING-nwppnext12 §4).
- It was built with `scripts/data/build_outage_membership_repair.py --iso NWPP --rederive <HEAD standard re-derive
  with --membership-vintage-union>`. The re-derive with or without the union flag gives the same six rows.

Basis: rule 14 (a measured availability event the committed extract failed to scan) and rule 23 (a new derive output
from the same source and the same deriver, citing no residual). **DOF +0.** Offer curves are byte-identical.
One mechanism per phenomenon (rule 19): no other NWPP mechanism floors or caps Boardman.

## 2. Prediction (zero LP), and what would NOT be a reason

- Live only in 2019 and 2020. 2021–2025 inputs are byte-identical, apart from the resolved-inputs path/sha record.
- COAL_PRB energy falls by ≈ 0.3 TWh (2019) and ≈ 0.75 TWh (2020), minus whatever other coal re-dispatch absorbs.
- C4 coal 2023 cannot move.
- The owner's standing ruling applies: promote if structural integrity improves, even if a gate regresses, with every
  regression reported at full magnitude. The decision rests on rule 14, not on the residual.

## 3. G-DRIFT (rule 29(b)) against keeper #16's `git_sha` 0ec8eb79

Keeper #16 solved at `0ec8eb79` (NEXT-10 audited through `526b75ee` plus its own diff). Every commit touching
`src/market_sim`, `scripts/lib`, `scripts/run_calibration*.py` or `data/raw/reference` on main since then:

| commit | what | class |
|---|---|---|
| 8f94addb, 55ce8970, f1de7e7f R-CAISO-15 | `caiso_eia930_clock_repair` HSL term and battery envelope; `paths.restore_eia860_dir` (called only inside the CAISO-gated envelope) | INERT (another ISO's branch) |
| 6dd5d81d, 853ff96f NYISO-NEXT-13 | `nyiso_ne_ac_recon_detach` (default off, NYISO-only); forecast parity registry | INERT |
| 70baf173 NYISO-NEXT-12 | `solve_and_persist` NE AC split, gated `iso == "NYISO"` | INERT |
| e44fd9fa miso-286 | `miso_gas_ecomin_online_floor` (default off, MISO-exclusive) | INERT |
| 196d1e69, c23608b8 spp-102 | `spp_commitment_posture` (default off, SPP-only) | INERT |
| 3c398753 R-ERCOT-15; 82cfdc3e R-ERCOT-14 | ERCOT bin sheet, ERCOT extracts, ERCOT crosswalk | INERT (ERCOT artifacts) |
| c1cb07f0 soco-88 | SOCO rows in `iso-gas-capacity-state-weights.csv` | INERT (another ISO's rows) |

**ALL INERT.** This PR adds no code, only the companion data file. The solve-surface fingerprint in each leg's
`solve_surface.json` is a second, mechanical check.

## 4. Recipe (per shard, year Y)

```
mkdir -p /tmp/n49 && git fetch --depth=1 origin 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 \
  && git archive 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 results/calibration/nwpp49_ror_span | tar -x -C /tmp/n49
python3 scripts/data/curate_hydro_plant_modes.py --iso NWPP
python3 scripts/data/curate_coal_receipts.py && python3 scripts/data/curate_coal_stocks.py
python3 scripts/replay_keeper.py /tmp/n49/results/calibration/nwpp49_ror_span \
  --out-dir results/calibration/nwppnext12mr_<Y> --years <Y> \
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
  [<Y> in 2019, 2020, 2021, 2022 ONLY:] --set hydro_backfill_year=null \
  --note "NWPP-NEXT-12 Boardman membership repair: keeper #16 recipe + unit_outage_membership_repair"
```

## 5. Hard stops (any miss means STOP, and no push)

1. `git rev-parse HEAD` equals the pin.
2. `sha256sum data/raw/_processed-legacy/campd_ct_heat_rates_NWPP.csv` =
   `29baa2f1ecfa10d9734c7e44cc306a88d527adb28968ea260f3409de37d7ff92`, and
   `sha256sum data/raw/campd-unit-outages-memberrepair-NWPP.csv` = `386a64d3…4d33b2` (full value in §1).
3. `scenario_config` in `run_config.json` differs from keeper #16's `run_config_<Y>.json` only in
   `unit_outage_membership_repair` (True). Keys absent in the keeper and False/None/default in the arm are also
   accepted.
4. **Arm-live:** `resolved_inputs.campd_unit_outages.path` = `data/raw/campd-unit-outages-memberrepair-NWPP.csv`,
   with the §1 sha.
5. `meta.json` `hydro_backfill_year` is null for 2019–2022 and 2024 for 2023–2025.
6. P1 summed `demand` equals keeper #16 ±0.05 TWh: 279.581 / 292.940 / 289.358 / 298.960 / 280.261 / 290.216 /
   302.532.
7. The keeper's log lines are present: `coal per-yard budget`, `coal take floor ... M yard rows floored` (M > 0),
   `coal monthly pile ... x 12 month-ends`, `NWPP Path 76 (Alturas)`, and for 2020 only,
   `unit-outage exit_ym routing live (year 2020): plants [6076]`.
8. The bundle contains `dispatch/<Y>_P1.parquet`, `hourly/class_hourly_<Y>.parquet`, `hourly/system_<Y>.parquet` and
   `hourly/hydro_cascade_<Y>.parquet`.
9. The solve is not infeasible. An infeasible or Unknown LP is a STOP, with the log reported and no retry.

## 6. Decision

- Compose with `scripts/probes/_nwpp42_compose_span.py` into `results/calibration/nwppnext12mr_span` (2023 leg first).
  Then run legitimacy diagnostics, the attestation, registration with `--no-prune`, and `calibration_verdict`, diffed
  per record against keeper #16.
- Promote if the arm is live and 2021–2025 reproduce keeper #16. The criterion is structural (rule 14), and every
  moved record is reported at full magnitude.
- Stop and report without promoting if 2021–2025 move by more than LP-tie noise (max |Δ class TWh| > 0.05), since the
  inputs there are identical.
