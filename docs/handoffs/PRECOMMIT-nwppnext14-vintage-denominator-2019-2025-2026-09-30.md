# PRECOMMIT — NWPP-NEXT-14: per-unit tranche vintage denominator + CC heat-rate floor (Clark), 2019–2025

Written before any solve. Template: `PRECOMMIT-nwppnext13-perunit-attribution-2019-2025-2026-09-30.md`.
Evidence: `FINDING-nwppnext14-bridger-c4-decomposition-2026-09-30.md` §3 and §5. Owner cards (2026-09-30): "Arm vintage
denominator", then "Build + solve with vintage" (the Clark CC heat-rate repair joins the same span; attribution per
key by the zero-LP census).

## 1. Arm

Keeper #18 (`2026-09-30-nwppnext13-per-unit-attribution`) plus exactly two keys, both new default-off fields in this
PR: `campd_per_unit_vintage_denominator: False → True` and `cc_subfloor_eia923_heat_rates: False → True`.

**Key 1, `campd_per_unit_vintage_denominator`.** This is a new default-off field (this PR), a sub-gate of
`campd_per_unit_attribution` (already True in the recipe). It selects one companion, new in this PR:

| file | sha256 | construction |
|---|---|---|
| `data/raw/_processed-legacy/thermal_tranches-perunit-vintage-NWPP.csv` | `6fe20358860f826f8051ccf8989c46a34bb5347e0ff2e8adf5d60b9bbbe65ab9` | `derive_thermal_tranches.py --iso NWPP --years 2023 2024 2025 --per-unit-attribution --vintage-denominator`, verbatim |

The unit-outage extract is unchanged (`campd-unit-outages-perunit-NWPP.csv`, sha `ff5b0644…`). The control derive
(flag off) reproduces the committed `-perunit-` artifact byte-for-byte.

- **Basis:** rule 14. The per-unit deriver divided pre-conversion coal years by the post-conversion nameplate. At
  Jim Bridger, 46 % of the 2023 samples exceed 100 % CF; at North Valmy, two units sit over one unit's nameplate in
  2023–24.
- **Rule 23:** the trigger is the defect, and no residual is cited. The arm is **not** expected to repair C4 coal
  2023 (FINDING §3).
- **DOF:** +0. Offer multipliers are byte-identical.

**Key 2, `cc_subfloor_eia923_heat_rates`.** The CC mirror of the SPP-49 simple-cycle floor. A non-CHP CC-part row
(CT/CA/CS/CC) whose eGRID plant rate is below `HEAT_RATE_BINS["gas_cc"]["h_class"]` = 6.3 takes the plant's own
EIA-923 Page 1 CC prime-mover rate (`data/raw/eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv`, no new
file). The floor applies only where that rate is unusable.

- Basis: rule 14. Clark 2322 is priced at 3.007 against its measured 9.0–9.6 (FINDING §5).
- DOF: +0 (aliases of cited constants and a measured filing).

## 2. Prediction (zero LP: `docs/handoffs/nwppnext14/vintage_census.json`, `ccfloor_census.json`, `both_census.json`)

**Key 2.** Only Clark 2322's three CC_REGULAR tranches (462 MW) move. Their heat rate goes
3.703 / 3.394 / 3.007 ×5 → 9.376 / 9.272 / 9.592 / 9.299 / 9.476 / 9.004 / 9.038 (2019–2025). Class availability
is unchanged. Expected effect: Clark CC falls from 3.69 TWh/yr toward its 0.43–0.86 TWh actual, with the energy
moving to other CC and to CT. This is the direction of both C1 residuals (CC_REGULAR over, CT_PEAKER under).

**Key 1.**

Class availability is byte-identical in every year; only tranche splits move, at five plants:

| unit | 2019–2023 | 2024 | 2025 |
|---|---|---|---|
| North Valmy 8224 must-run | 212.45 → 127.89 MW | same | 109.08 → 65.66 |
| Jim Bridger 8066 must-run | 351.75 → 326.33 MW (+2.12 MW committed) | 174.13 → 161.55 | same as 2024 |
| Evander Andrews 7953 CT committed | ~106–121 → ~85–98 MW | 110.65 → 89.15 | 95.94 → 77.30 |
| Langley Gulch 57028 CC committed | −4.5 to −4.8 MW | | |
| Bennett Mountain 55733 CT committed | +0.7 to +0.8 MW | | |

- Forced coal falls by about 0.9 TWh/yr at the ceiling (Valmy) plus about 0.2 TWh/yr (Bridger). Realized coal
  energy moves less, because these tranches still dispatch economically.
- C4 coal can move in either direction.
- The decision rests on rule 14 under the owner's standing ruling, not on the residual. Every regression is reported
  at full magnitude.

## 3. G-DRIFT (rule 29(b)) against keeper #18's `git_sha` f2cfda46

Audited over `src/market_sim`, `scripts/run_calibration.py`, `scripts/run_calibration_full.py`, `scripts/lib`,
`scripts/replay_keeper.py`, `data/raw/_validation-source` and `data/raw/reference`. The span runs from `f2cfda46` to
this branch rebased on main `46e1b31e` (audit first run at `c018dcba`, then extended to the key-2 commit).

- **Base.** f2cfda46 sits on the NWPP-NEXT-13 branch (merge base `cc02e191`, with no audited-path diff between them),
  so every hunk is a `main`-side change.

| source | what | class |
|---|---|---|
| NYISO-NEXT-17 (`nyiso_fg_split`, iso_configs `_nyiso_config`, topology_variant, zonal_shares, zone_assignment, interchange/import_nodes/spec/nyiso, lp import-link rows, pipeline/ttc, nyiso_* modules, fgsplit solar csv) | NYISO-only, under the NYISO gate plus a default-off flag; `import_link_band=None` elsewhere | INERT (another ISO) |
| R-CAISO-17/18 (eia930 frames/demand/envelopes, caiso_hydro_backfill, renewables, storage, neighbor_price, fuel/electric_power, interchange/caiso, CISO clock constants) | CAISO/CISO-only, under `caiso_eia930_clock_repair` (False in the recipe) and new default-off kwargs | INERT (another ISO) |
| SPP `spp_ct_lole_efor` (fleet/arrays, fleet/ct_lole_efor, constants) | SPP-only, default off, absent from the recipe | INERT |
| PJM-NEXT-13 (`pjm_replacement_cost_fuel`, fuel/basis pjm*, reference csvs) | PJM-only; returns None when off | INERT |
| R-ERCOT-18 (`netload_drag_prior_year_commitment_index`, fleet/floors, ercot csv) | ERCOT-keyed, default off (k = 1.0 exactly) | INERT |
| solve_surface_declared, forecast_parity_registry | declarations only (names at their live hash) and forecast governance | INERT |
| `actual_lmp.json` (miso-292) | MISO scoring basis, no NWPP key | INERT (scoring only) |
| this PR: `campd_per_unit_vintage_denominator` (scenarios, campd_bins, the `-perunit-vintage-` companion) | default off | ARM key 1 |
| this PR: `cc_subfloor_eia923_heat_rates` (scenarios, constants `EGRID_CC_HR_PHYSICAL_FLOOR` + its declaration, eia860 seam + threading, assembly, run_calibration) | default off; off path returns before any frame change | ARM key 2 |
| this PR: `derive_thermal_tranches.py --vintage-denominator`, probes, tests, docs | off the solve path | INERT |

**ALL INERT; no LIVE hunk. Form 4 is valid and keeper #18's committed bundle is the control.**
- `_nwpp_config` and NWPP's `default_scenario_overrides` are untouched.
- No existing default changed.
- No other NWPP input changed.
- The mechanical second check is each leg's `solve_surface.json` fingerprint.

### 3.1 Addendum: main `46e1b31e` → `ecadf27c` (merged before the pin)

| source | what | class |
|---|---|---|
| SPP-105 `spp_gas_crow_residual_outage` (fleet/arrays, spp_gas_outage, paths) | SPP-only; `__post_init__` refuses non-SPP; `crow_rate_out=None` otherwise | INERT |
| R-ERCOT-19 `netload_drag_prior_year_hour_profile`, `cc_committed_prior_year_commitment_eligibility` (floors, offer_curves, commitment_profile, ercot csv) | default off; `hour_profile=None` makes the refactored `targets` arithmetically identical; `cc_committed_offer_margin` is False in the recipe | INERT |
| soco-96 rubric v3.13 (held-out years gate the determination) | scorer, not the solve | INERT for the solve; **the verdict diff reads both keepers under the same rubric** |

**Still ALL INERT.**

## 4. Recipe (per shard, year Y)

The NEXT-13 §4 recipe verbatim, plus one `--set`:

```
mkdir -p /tmp/n49 && git fetch --depth=1 origin 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 \
  && git archive 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 results/calibration/nwpp49_ror_span | tar -x -C /tmp/n49
python3 scripts/data/curate_hydro_plant_modes.py --iso NWPP
python3 scripts/data/curate_coal_receipts.py && python3 scripts/data/curate_coal_stocks.py
python3 scripts/replay_keeper.py /tmp/n49/results/calibration/nwpp49_ror_span \
  --out-dir results/calibration/nwppnext14vd_<Y> --years <Y> \
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
  --set campd_per_unit_vintage_denominator=true \
  --set cc_subfloor_eia923_heat_rates=true \
  [<Y> in 2019, 2020, 2021, 2022 ONLY:] --set hydro_backfill_year=null \
  --note "NWPP-NEXT-14: keeper #18 recipe + campd_per_unit_vintage_denominator + cc_subfloor_eia923_heat_rates"
```

## 5. Hard stops (any miss means STOP, and no push)

1. `git rev-parse HEAD` equals the pin.
2. sha256 checks:
   - `data/raw/_processed-legacy/campd_ct_heat_rates_NWPP.csv` = `29baa2f1ecfa10d9734c7e44cc306a88d527adb28968ea260f3409de37d7ff92`;
   - `data/raw/campd-unit-outages-perunit-NWPP.csv` = `ff5b0644553095e6600691673f3442877e287b42623a772bda052b4df734e5f3`;
   - the §1 file = `6fe20358…65ab9`.
3. `scenario_config` in `run_config.json` differs from keeper #18's
   `results/calibration/nwppnext13pu_span/run_config_<Y>.json` only in `campd_per_unit_vintage_denominator` and
   `cc_subfloor_eia923_heat_rates` (both True).
   Keys absent in the keeper and False/None/default in the arm are accepted.
4. **Arm live:** `resolved_inputs.thermal_tranches.path` = `data/raw/_processed-legacy/thermal_tranches-perunit-vintage-NWPP.csv`
   with the §1 sha, and `resolved_inputs.campd_unit_outages.path` = `data/raw/campd-unit-outages-perunit-NWPP.csv`.
   The solve log carries `eGRID plant 2322 heat rate ... below the combined-cycle physical floor 6.300 ... EIA-923 CC
   prime-mover rate` with the §2 value for year Y.
5. `meta.json` `hydro_backfill_year` is null for 2019–2022 and 2024 for 2023–2025.
6. P1 summed `demand` equals keeper #18 ±0.05 TWh: 279.581 / 292.940 / 289.358 / 298.960 / 280.261 / 290.216 /
   302.532.
7. The keeper's log lines are present:
   - `coal per-yard budget`;
   - `coal take floor ... M yard rows floored` (M > 0);
   - `coal monthly pile ... x 12 month-ends`;
   - `NWPP Path 76 (Alturas)`;
   - for 2020 only, `unit-outage exit_ym routing live (year 2020): plants [6076]`.
8. The bundle contains `dispatch/<Y>_P1.parquet`, `hourly/class_hourly_<Y>.parquet`, `hourly/system_<Y>.parquet` and
   `hourly/hydro_cascade_<Y>.parquet`.
9. The solve is not infeasible. An infeasible or Unknown LP is a STOP, with the log reported and no retry.

## 6. Decision

- Compose with `scripts/probes/_nwpp42_compose_span.py --skip-diagnostics` into
  `results/calibration/nwppnext14vd_span` (2023 leg first). Then run legitimacy diagnostics, the attestation, and
  registration with `--no-prune`.
- Diff `calibration_verdict` per (criterion, year, key) record against keeper #18.
- Promotion goes to the owner as a decision card. The criterion is structural (rule 14): the arm is live in every
  year and every solve is feasible. Every moved record is reported at full magnitude.
