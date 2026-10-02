# ADDENDUM: L1 pre-launch preflight on the W0 keeper (PRECOMMIT §3)

Written 2026-10-02, **before any L1 shard launched**. Control = the W0 keeper `2026-10-02-w0-settlement` (bundle `results/calibration/w0_ercot_span`, main 18feea61; rule 29). Zero LP.

## 1. Census re-run on the W0 keeper

`scripts/probes/_ercot_closeout_l1_coal_fuel_census.py --bundle results/calibration/w0_ercot_span`. This now covers 2025 as well, because #7038 landed the 2025 Page 5 receipts. Outputs are in `data/l1_coal_census_plant_{year,month}_w0.csv`.

- **2019–2024: no plant-year moved by more than 0.5 TWh.** Every form-B excess is within ±0.01 TWh of FINDING §1.3, and the W0 keeper's coal dispatch matches r-24 to ±0.01 TWh per plant. The §4 predictions for 2019–2024 therefore stand unchanged.
- **2025 is re-pinned** from the ratable proxy to measured receipts:

| Plant | Ratable (FINDING §1.3) | Measured 2025 receipts |
|---|---|---|
| W A Parish (3470) | 2.58 | **1.71** |
| Limestone (298) | 1.00 | **0.67** |
| Coleto Creek (6178) | — | **0.35** |
| Twin Oaks (7030, LIG) | 0.29 | **0.28** |
| Sandy Creek (56611) | — | no 2025 receipts → ratable profile (keeper model 0.61 TWh; slack) |
| Others | 0 | 0 |

**Re-pinned 2025 prediction.** The W0 keeper has COAL_PRB 2025 at +3.53 TWh. The measured ceiling removes 2.7 TWh of PRB, part of which re-dispatches to slack coal. Prediction: **COAL_PRB 2025 ≈ +1.0 to +2.0 TWh**, and **2025 C3a moves up by 0 to 1.5 pt**, from −10.0 % (W0 keeper, NOT-YET). There is no prediction that 2025 C3a clears; the 2025 C3a gap is mainly the West basis and ECRS (FINDING §2, plan §3.5).

## 2. Code delta landed on this branch (PRECOMMIT §2)

- `scripts/run_calibration.py`:
  - `COAL_PLANT_GRAIN_ISOS` gains ERCOT.
  - New `COAL_PILE_CEILING_ISOS = ("ERCOT",)`. `resolve_coal_monthly_pile` / `resolve_coal_measured_receipts` accept a pile with no take floor there. NWPP's floor requirement is unchanged, and ERCOT with a take floor is still refused.
  - A ceiling-only branch builds the pile with `floor_parts=None`.
  - The annual floor reconciliation is skipped for a ceiling-only pile and replaced by a month-grain one.
  - The measured-receipt read is factored into `load_coal_measured_receipts`, with NWPP behaviour unchanged.
- `src/market_sim/data/coal_fuel_inventory.py::reconcile_floors_to_yard_budget`: new optional `month_index`. A multi-column cumulative budget scales a yard's floors by the smallest month-end ratio. The annual path is byte-identical.
- Tests: gate tests (ERCOT ceiling-only allowed; pile without floor refused for NWPP/MISO/NEISO; ERCOT with a take floor refused) and two month-grain reconciliation tests.

## 3. Zero-LP smoke (fleet-only rebuild, `replay_keeper.run_year_kwargs`)

| Year | Yards | Rowed gens | Year-end ceiling | Measured yard rows | Floors scaled |
|---|---|---|---|---|---|
| 2022 | 11 | 44 | 79.7 TWh-eq | 10 | none |
| 2025 | 10 | 40 | 80.6 TWh-eq | 9 | none |

Martin Lake's 2022 December ceiling is 151.3 TBtu against a keeper burn of ≈ 190.6 TBtu, so it binds by ≈ 3.4 TWh, as the census predicts.

The arm for all seven legs is `coal_fuel_inventory_plant_grain=true`, `coal_fuel_inventory_monthly_pile=true`, `coal_monthly_pile_measured_receipts=true`, replayed on `w0_ercot_span` with its 3-config partition.
