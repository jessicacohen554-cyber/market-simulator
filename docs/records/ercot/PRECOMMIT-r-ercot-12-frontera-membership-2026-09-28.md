# PRECOMMIT — R-ERCOT-12: Frontera (55098) dated ERCOT membership, fleet + benchmark

**Session:** R-ERCOT-12, 2026-09-28. **Keeper (control, rule 29(b) form 4):** `2026-09-28-r-11-parish-split`, bundle `results/calibration/r_ercot11_parish_split_span`.

**Owner ruling** (decision card, verbatim answer): **"Fleet + benchmark (Recommended)"**. SCED key card: **"Still declined"**, so coal offers stay untouched and `coal_offer_level_rebasis` stays R.

## 1. Phase 0 (zero LP)

- **Lever 1, the 2024 tight hours, closes with no arm.** 87 % of the 2024 flip is ONE hour: the prior keeper shed 3.1 MWh at Panhandle on 2024-05-07 19:00. See `FINDING-r-ercot-12-2024-tight-hours-2026-09-28.md`.
- **Lever 2, Frontera, is not an ERCOT resource before 2023-04-13.** Three independent records agree:
  - ERCOT's 60-Day DAM first lists `FRONT_EC_CC1` on 2023-04-13.
  - EIA-860 vintages 2018–2022 carry no 55098 row at all; 2023+ codes it ERCO.
  - EIA-923 has no rows for 2019–22 or for Jan–May 2023.
- **Yet it is in ERCOT everywhere:**
  - **Fleet:** the static bin sheet (`custom-bin-assignments.csv:55`) carries it in every year, and no loader BA filter reaches bin units.
  - **Benchmark:** both CAMPD backfills re-book it from TX CEMS through the same bin sheet.

## 2. What changes (one rule-14 membership correction, zero free parameters, no `ScenarioConfig` field)

- **`constants.ISO_PLANT_ENTRIES = {"ERCOT": {55098: "2023-04-13 06:00"}}`.**
  - It is the plant-grain twin of `ISO_BA_JOINS` / `ISO_BA_EXITS`, read only by `data.ba_membership`.
  - The stamp is hour-ending UTC, on the EIA-930 clock (operating day 2023-04-13 HE01 CDT).
- **Solve-surface declaration.** It is declared at the pre-arm (empty-table) hash, as SOCO's joins/exits were, so ERCOT backcast keys move.
- **Three seams, one boundary (rule 19):**
  - **Fleet:** an hour mask in `fleet.arrays`, backcast-only. Frontera is offline all year in 2019–22 and before LP row 2447 in 2023.
  - **Benchmark 923 frame:** the plant is removed before 2023 (`_iso_plant_ids`), with a month split in 2023 (`plant_entry_month_share`).
  - **Both CAMPD backfills:** pre-entry CEMS hours are zeroed (`zero_pre_entry_campd`). Zeroed, not dropped, because the missing-month fill reads each series by position; the first attempt dropped rows and shifted months, and was caught and fixed before this commit.
- **Measured benchmark effect**, zero-LP `build_benchmark_frames` A/B on the keeper recipe: CC_REGULAR **−3.100 / −2.756 / −2.193 / −3.042 / −0.260 TWh** (2019–2023).
  - This equals FINDING-r-ercot-11's Frontera column to the MWh.
  - 2024/2025 are byte-identical, and no other class moves.
- **Measured fleet effect**, zero-LP `fleet_only` (`scripts/probes/_r_ercot12_frontera_fleet_mask.py`):
  - 2021: 17 Frontera rows, 529 MW, available energy **0.000**.
  - 2023: masked before row 2447.
  - Log line: `plant entry (ERCOT <Y>)`.
- **Tests:** `tests/unit/data/test_plant_entry_membership.py` (5 tests), and `test_ba_membership.py` passes unchanged.

## 3. G-DRIFT (keeper SHA `d6ffbda9` → `main` `8e13f763`)

The solve-path hunks since the keeper SHA are:
- CAISO `caiso_import_cap_floor_static`;
- PJM `unit_outage_rederive_peaker_windows`;
- MISO `campd_st_gas_span_coverage` (the `stcov` companions, fuel-split sub-gate).

All are default-off and absent from every ERCOT year's recipe. **Every hunk is INERT for ERCOT, so form 4 is valid.** The only LIVE change is this lane's §2.

## 4. Sealed predictions (arm vs keeper, P1)

Keeper C1 CC_REGULAR (model − bench, TWh): +7.95 / +8.03 / −3.11 / −10.26 / +2.30 / −1.35 / −1.48. Band ±8.00.

- **P1 (fleet).** Frontera P1 energy is exactly 0 in 2019–22. In 2023 it is 0 in LP rows before 2447.
- **P2 (2024/2025 identity).** The fleet, benchmark and recipe are unchanged. Every scored number reproduces the keeper to ≤ 0.01 TWh per class and ≤ $0.02 LW.
- **P3 (C1 CC_REGULAR).** It moves by the bench removal minus the un-replaced share of Frontera's dispatch. Replacement share by other CC is assumed in [0.3, 0.9].
  - 2019: [+9.1, +10.8], FAIL (worse).
  - 2020: [+9.3, +10.6], FAIL.
  - 2021: [−1.9, −1.1], PASS.
  - **2022: [−8.7, −7.4], KNIFE EDGE.** It flips to PASS if replacement is ≥ ~0.7.
  - 2023: [+2.4, +2.6], PASS.
- **P4 (price).** Removing 529 MW of efficient CC raises LW slightly in 2019–22, by 0 to +2 %.
  - 2019 C3a stays FAIL (+24.8 % → [+24.8, +27]).
  - 2022 C3a (−10.3 %) moves to [−10.3, −8.5] and may flip to PASS.
- **P5 (C8, 2022).** ST_GAS energy rises or holds, so the ST_GAS forced share falls or holds from 30.3 % and may clear 30 %.
- **P6 (determinations).**
  - 2019 and 2020 stay NOT-YET.
  - 2021 stays CALIBRATED.
  - 2022 may flip to CALIBRATED only if C1 CC, C3a and C8 all clear; predicted to stay NOT-YET.
  - Train years 2023/2024/2025 are unchanged (NOT-YET / NOT-YET / CALIBRATED). ERCOT stays NOT-YET.

## 5. Decision rule (fixed now)

Rule 14 governs. The correction is kept on its identity, never on its scores.
- **No train-year determination moves → recommend promote.** This is the owner's standing instruction, "Is it an improvement? Then promote". The validation-year C1 worsening in 2019/2020 is reported at full magnitude.
- **A train-year determination moves** (not expected, since only 2023's Jan–Apr is touched) → put it to the owner with no recommendation to revert.
- **Nothing is pruned before the owner rules** (rules 31/35).

## 6. DOF ledger

The keeper's 12 entries are carried verbatim, and this arm adds none. The stamp is a measured publisher record (rules 21/24).

## 7. Execution

- **Shards:** seven, one per year 2019–2025 (rules 34(c)/36). Prompts are in `docs/records/ercot/r-ercot/SHARD-PROMPTS-r-ercot-12.md`, pinned to the SHA of the commit carrying this file.
- **Each shard** runs `replay_keeper.py results/calibration/r_ercot11_parish_split_span --years <Y>` with no overrides. The arm is the registry.
- **The parent** then:
  1. composes the legs;
  2. runs `stamp_config_partition --check`;
  3. attests and registers;
  4. scores each year on the keeper's basis, with the benchmark rebuilt at HEAD;
  5. writes the RESULT.
