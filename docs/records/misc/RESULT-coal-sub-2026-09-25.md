# RESULT — COAL-SUB: the bare `COAL` class is eliminated (2026-09-25)

**Owner instruction (2026-09-25, verbatim):** *"we need to completely eliminate the class Coal From the model altogether all coal should be sorted into its subclass".*

**Scope:** code, data labels, scorer, docs, tests. **No LP was solved.** All evidence is zero-LP: `run_year(..., fleet_only=True)` rebuilds of each ISO's designated keeper recipe, plus re-scoring each committed keeper bundle.

## 1. What changed

- **Every coal generator's `plant_group` is its subclass**: `COAL_LIGNITE` / `COAL_PRB` / `COAL_BIT` / `COAL_WC` (`plant_taxonomy.COAL_CLASSES`). It is resolved at load by `data/coal.py::coal_subclass`, using the `coal_supply_class` chain in unchanged order:
  1. curated ERCOT map
  2. EIA-923 receipts
  3. EIA-860 retiree rank
  4. partial-exit registry
  5. **new, last link:** the unit's own EIA-860 `Energy Source 1`, read off the vintage row the loader is building.
- **The fallback map is the benchmark's own.** The last link uses `COAL_CODE_TO_SUPPLY`: BIT/ANT/RC/SC/SGC → COAL_BIT, SUB → COAL_PRB, LIG → COAL_LIGNITE, WC → COAL_WC. This is the same map `classify_plant` applies to EIA-923 rows, so the fleet and the benchmark classify identically by construction.
- **Resolution is plant-level.** The first coal code registered wins, so one plant always has one subclass. A unit no link resolves **raises**; a subclass is never invented. All 33 plant-years that were previously unresolved resolved (§3), and nothing raised.
- **`COAL` is deleted as a class (rule 26), not aliased.**
  - It is gone from `PLANT_CLASSES`, from every offer-curve registry (generic, PJM, MISO, SPP, backcast base), and from every per-unit parameter table.
  - Per-unit tables are carried to the four subclasses with the identical value: `THERMAL_AVAILABILITY`, `MAINTENANCE_MONTHLY_SHAPE`, `MIN_STABLE_PCT_PHYSICAL`, `CORRELATED_OUTAGE_CURVE`[ERCOT], `BIN_GROUP_TO_FUEL`, `BIN_STARTUP_COST_PER_MW`, `BIN_GROUP_HR_DEFAULT`, `_DEFAULT_HR_MULT_BY_GROUP`, `_DEFAULT_TRANCHE_PCT_BY_GROUP`, `_BIN_GROUP_MEASURED_FAMILY`, `_RAMP_BUCKET_BY_GROUP`, `RAMP10_FRAC_BY_GROUP` and `_PJM_MIDCURVE_SEGMENT_OF`.
  - The last of these gains `COAL_LIGNITE` and `COAL_WC`, which it previously lacked; with the bare group every coal unit read LONG_RUN, and still does.
- **`"COAL"` survives only as the committed artifacts' fuel-family token** (`plant_taxonomy.COAL_ARTIFACT_FAMILY`).
  - Rule 23 freezes the derived artifacts, and a label rename is not a data change. These include the CAMPD outage extracts, `thermal_tranches_<ISO>.csv`, reliability-floor coefficients, ERCOT DAM availability, marginal-HR summaries and the ERCOT envelope tables. All are joined through `artifact_class`.
  - Every mechanism that computes ONE quantity across all coal and distributes it also reads the family. Splitting it by rank would move the answer. These mechanisms are:
    - reliability-floor limbs (cheapest-first)
    - ERCOT class availability water-fill
    - online-capacity envelopes and RTORPA eligibility
    - winter fuel security
    - the EIA-923 fuel-price class donor pool
    - the D-2/D-4 class vote
  - No generator carries the token. `Generator.plant_group` refuses it.
- **Refusal and translation:**
  - `ScenarioConfig` refuses `COAL` in `offer_curve_by_group`, `econ_split_by_group`, `class_commitment_overrides`, `wefor_residual_groups` and `temp_derate_classes` (`BareCoalClassError`).
  - The `--offer-curve-json` / `--offer-curve-delta-json` merges refuse it outright.
  - The one exception: a recorded curve that carries `COAL` alongside all four subclasses is folded, so every committed bundle's config stays readable. There, `COAL` could only have reached a unit whose subclass had no curve.
  - `replay_keeper.translate_legacy_coal_keys` folds the legacy keys in keeper recipes (MISO `prb_overrides.offer_curve_by_group`; PJM/SPP `offer_curve_overrides`).
- **ERCOT:** the 10 coal rows of `data/raw/reference/custom-bin-assignments.csv` carry the curated subclass (`COAL_PLANT_SUPPLY`): 7 × COAL_PRB, 3 × COAL_LIGNITE. Bin labels, zones, bin numbers and every number are unchanged. The four committed `bin_assignments_{PJM,MISO,CAISO,NEISO}.csv` exports are relabelled the same way (label only; their sole runtime reader filters CT_PEAKER).
- **Unit ids keep the historical `COAL_<zone>_p<plant>_<tranche>` token**, so committed dispatch parquets, floors npz files and goldens stay joinable. The id is an identifier; nothing parses its head as a class.

## 2. Byte-identity proof (zero LP)

**Method.** `scripts/probes/coal_subclass_snapshot.py` rebuilds one ISO-year under the designated keeper's recipe with `fleet_only=True` and dumps every per-generator array. It records 1-D arrays exactly and 2-D arrays as one SHA-1 per generator row: `pmax`, `pmin`, `heat_rate`, `vom`, emission rates, `zone_idx`, `availability`, `min_gen`, `min_gen_mechanism`, `ramp10`, and the assembled P0 offer `mc_base`.

`scripts/probes/coal_subclass_compare.py` diffs BEFORE and AFTER with **no tolerance**. The only permitted label change is `COAL` → subclass.

- **BEFORE** = `origin/main` @ `a1b8ebd9` in a worktree over the same data, with the original ERCOT and bin-assignment CSVs.
- **AFTER** = this branch.
- PJM runs with `pjm_da_virtual_bids=false` on both sides, because the gitignored DA-virtuals corpus is absent in the container. Virtual bids append pseudo-generators only, never coal rows.
- CAISO 2019–2021 and NYISO 2019–2020 are not rebuildable under the keeper recipe (missing inputs, both sides). The census covers those years from the raw EIA-860 fleet.

**Result — 58 ISO-years rebuilt:**

| ISO | Year | Generators | Rows that moved | Verdict |
|---|---|---:|---:|---|
| CAISO | 2022 | 1,651 | 0 | byte-identical |
| CAISO | 2023 | 1,633 | 0 | byte-identical |
| CAISO | 2024 | 1,625 | 0 | byte-identical |
| CAISO | 2025 | 1,710 | 0 | byte-identical |
| ERCOT | 2019 | 2,073 | 0 | byte-identical |
| ERCOT | 2020 | 2,076 | 0 | byte-identical |
| ERCOT | 2021 | 2,323 | 0 | byte-identical |
| ERCOT | 2022 | 2,327 | 0 | byte-identical |
| ERCOT | 2023 | 2,326 | 0 | byte-identical |
| ERCOT | 2024 | 2,323 | 0 | byte-identical |
| ERCOT | 2025 | 2,310 | 0 | byte-identical |
| MISO | 2019 | 2,995 | 47 | only generic-bucket plants move |
| MISO | 2020 | 2,989 | 41 | only generic-bucket plants move |
| MISO | 2021 | 2,981 | 27 | only generic-bucket plants move |
| MISO | 2022 | 2,982 | 13 | only generic-bucket plants move |
| MISO | 2023 | 2,736 | 12 | only generic-bucket plants move |
| MISO | 2024 | 2,720 | 6 | only generic-bucket plants move |
| MISO | 2025 | 3,217 | 0 | byte-identical |
| NEISO | 2019 | 759 | 9 | only generic-bucket plants move |
| NEISO | 2020 | 780 | 9 | only generic-bucket plants move |
| NEISO | 2021 | 789 | 0 | byte-identical |
| NEISO | 2022 | 767 | 0 | byte-identical |
| NEISO | 2023 | 743 | 0 | byte-identical |
| NEISO | 2024 | 736 | 0 | byte-identical |
| NEISO | 2025 | 835 | 0 | byte-identical |
| NWPP | 2019 | 623 | 0 | byte-identical |
| NWPP | 2020 | 775 | 0 | byte-identical |
| NWPP | 2021 | 634 | 0 | byte-identical |
| NWPP | 2022 | 628 | 0 | byte-identical |
| NWPP | 2023 | 629 | 0 | byte-identical |
| NWPP | 2024 | 652 | 0 | byte-identical |
| NWPP | 2025 | 653 | 0 | byte-identical |
| NYISO | 2021 | 805 | 0 | byte-identical |
| NYISO | 2022 | 696 | 0 | byte-identical |
| NYISO | 2023 | 685 | 0 | byte-identical |
| NYISO | 2024 | 678 | 0 | byte-identical |
| NYISO | 2025 | 709 | 0 | byte-identical |
| PJM | 2019 | 2,672 | 96 | generic-bucket plants + floor spillover (counterfactual-identical) |
| PJM | 2020 | 2,665 | 54 | generic-bucket plants + floor spillover (counterfactual-identical) |
| PJM | 2021 | 2,675 | 45 | generic-bucket plants + floor spillover (counterfactual-identical) |
| PJM | 2022 | 2,594 | 16 | only generic-bucket plants move |
| PJM | 2023 | 2,556 | 0 | byte-identical |
| PJM | 2024 | 2,514 | 0 | byte-identical |
| PJM | 2025 | 2,953 | 0 | byte-identical |
| SOCO | 2019 | 430 | 0 | byte-identical |
| SOCO | 2020 | 426 | 0 | byte-identical |
| SOCO | 2021 | 435 | 0 | byte-identical |
| SOCO | 2022 | 433 | 0 | byte-identical |
| SOCO | 2023 | 331 | 0 | byte-identical |
| SOCO | 2024 | 332 | 0 | byte-identical |
| SOCO | 2025 | 359 | 0 | byte-identical |
| SPP | 2019 | 1,156 | 0 | byte-identical |
| SPP | 2020 | 1,149 | 0 | byte-identical |
| SPP | 2021 | 1,131 | 0 | byte-identical |
| SPP | 2022 | 1,131 | 0 | byte-identical |
| SPP | 2023 | 1,117 | 0 | byte-identical |
| SPP | 2024 | 1,133 | 0 | byte-identical |
| SPP | 2025 | 1,188 | 0 | byte-identical |

- **Every rank-resolved coal unit, and every non-coal unit, is byte-identical in every array** in all 58 ISO-years, with one exception, PJM 2019–2021, where limb-mate floors move (below).
- **The only movers are the former generic-bucket plants** (§3). They now read their own subclass's offer curve, supply passthrough and delivered-fuel mapping.
- **PJM 2019–2021 — reliability-floor spillover.** The `min_gen` rows of a few rank-resolved plants that share a reliability-floor limb with a generic-bucket plant also move: 876 and 879 in all three years; 3118, 3943 and 3944 in 2019 only. The limb distributes a zone-coal floor cheapest-first by `heat_rate`, and the generic plants' tranche heat rates changed with their curve.
- **Counterfactual proof.** The BEFORE code was rebuilt with the generic-bucket plants' post-change ranks handed to it through its own `register_partial_exit_coal_supply` registry (`--register-supply`). **All 22 ISO-years with a generic-bucket plant are then byte-identical to AFTER, on every array**, PJM 2019–2021 included. So resolving those plants is the only thing that changes any number.
- Raw record: `docs/handoffs/coal-sub/byte-identity-proof.json`.

## 3. Census and the generic-bucket plants

Coal MW by resolved subclass, and MW in the former generic bucket, for 9 ISOs × 2019–2025: `docs/handoffs/coal-sub/census-2019-2025.md` (plant lists in the `.json`).

The generic bucket is empty in 2025 in every ISO except CAISO (Argus Cogen, 15 MW, a CHP-routed industrial cogen). What each generic-bucket plant resolved to, from its own vintage EIA-860 coal code:

| Plant | Name | ISO | Years | Subclass assigned | MW by year |
|---:|---|---|---|---|---|
| 10684 | Argus Cogen Plant | CAISO | 2022–2025 | COAL_BIT | 2022: 15.0, 2023: 15.0, 2024: 15.0, 2025: 15.0 |
| 1104 | Burlington (IA) | MISO | 2019–2021 | COAL_PRB | 2019: 205.3, 2020: 205.3, 2021: 191.2 |
| 1702 | Dan E Karn | MISO | 2019–2022 | COAL_PRB | 2019: 508.0, 2020: 486.0, 2021: 489.2, 2022: 489.2 |
| 1943 | Hoot Lake | MISO | 2019–2020 | COAL_PRB | 2019: 138.0, 2020: 138.0 |
| 2790 | R M Heskett | MISO | 2019–2021 | COAL_LIGNITE | 2019: 104.3, 2020: 104.3, 2021: 104.3 |
| 6089 | Lewis & Clark | MISO | 2019–2020 | COAL_LIGNITE | 2019: 53.1, 2020: 53.1 |
| 6137 | A B Brown | MISO | 2019–2022 | COAL_BIT | 2019: 490.0, 2020: 490.0, 2021: 490.0, 2022: 485.0 |
| 6639 | R D Green | MISO | 2019–2023 | COAL_BIT | 2019: 454.0, 2020: 454.0, 2021: 454.0, 2022: 231.0, 2023: 231.0 |
| 10234 | Biron Mill | MISO | 2019–2022 | COAL_BIT | 2019: 35.3, 2020: 35.3, 2021: 35.3, 2022: 35.3 |
| 10234 | Biron Mill | MISO | 2023–2024 | COAL_PRB | 2023: 19.6, 2024: 19.6 |
| 10686 | Rapids Energy Center | MISO | 2019–2019 | COAL_PRB | 2019: 22.1 |
| 10861 | Archer Daniels Midland Des Moines | MISO | 2019–2023 | COAL_PRB | 2019: 7.3, 2020: 7.3, 2021: 7.3, 2022: 7.3, 2023: 7.3 |
| 10863 | Archer Daniels Midland Mankato | MISO | 2019–2023 | COAL_PRB | 2019: 2.8, 2020: 2.8, 2021: 2.8, 2022: 2.8, 2023: 2.8 |
| 10867 | Tate & Lyle Decatur Plant Cogen | MISO | 2019–2020 | COAL_BIT | 2019: 62.0, 2020: 62.0 |
| 50933 | Rhinelander Mill | MISO | 2019–2023 | COAL_BIT | 2019: 5.9, 2020: 5.9, 2021: 5.9, 2022: 5.9, 2023: 5.9 |
| 54098 | Kaukauna Paper Mill | MISO | 2019–2022 | COAL_BIT | 2019: 11.8, 2020: 11.8, 2021: 11.8, 2022: 11.8 |
| 54201 | Iowa State University | MISO | 2019–2019 | COAL_BIT | 2019: 39.9 |
| 56786 | Spiritwood Station | MISO | 2021–2022 | COAL_BIT | 2021: 70.9, 2022: 92.9 |
| 568 | Bridgeport Station | NEISO | 2019–2020 | COAL_PRB | 2019: 383.4, 2020: 257.6 |
| 2367 | Schiller | NEISO | 2019–2020 | COAL_BIT | 2019: 95.4, 2020: 95.4 |
| 10504 | Amalgamated Sugar Twin Falls | NWPP | 2019–2021 | COAL_BIT | 2019: 7.9, 2020: 4.7, 2021: 4.7 |
| 883 | Waukegan | PJM | 2019–2021 | COAL_PRB | 2019: 689.0, 2020: 689.0, 2021: 689.0 |
| 1554 | Herbert A Wagner | PJM | 2019–2022 | COAL_BIT | 2019: 423.0, 2020: 305.0, 2021: 305.0, 2022: 305.0 |
| 1571 | Chalk Point LLC | PJM | 2019–2020 | COAL_BIT | 2019: 670.0, 2020: 670.0 |
| 1572 | Dickerson | PJM | 2019–2019 | COAL_BIT | 2019: 519.0 |
| 1573 | Morgantown Generating Plant | PJM | 2019–2021 | COAL_BIT | 2019: 1,205.0, 2020: 1,205.0, 2021: 1,205.0 |
| 3140 | Brunner Island | PJM | 2019–2021 | COAL_BIT | 2019: 742.0, 2021: 1,411.0 |
| 3797 | Chesterfield | PJM | 2019–2022 | COAL_BIT | 2019: 1,006.0, 2020: 1,006.0, 2021: 1,006.0, 2022: 1,006.0 |
| 10743 | Morgantown Energy Facility | PJM | 2019–2019 | COAL_WC | 2019: 32.5 |
| 50366 | University of Notre Dame | PJM | 2019–2019 | COAL_BIT | 2019: 5.4 |
| 54081 | Spruance Operating Services LLC | PJM | 2019–2019 | COAL_BIT | 2019: 68.2 |
| 54556 | Ingredion Incorporated | PJM | 2019–2020 | COAL_BIT | 2019: 12.7, 2020: 12.7 |
| 57937 | Western Sugar Coop - Scottsbluff | SPP | 2019–2021 | COAL_PRB | 2019: 4.7, 2020: 4.7, 2021: 4.7 |

Biron Mill (10234) carries both BIT and SUB coal units. Its first-registered code differs by vintage (BIT in 2019–2022, SUB in 2023–2024), so it is plant-consistent within every year.

## 4. Scoring

- **Scorer changes.**
  - `calibration_verdict.COAL_CLASSES` is the four subclasses. The C1 per-class records and every class table use subclasses only.
  - The coal FAMILY totals (C2 / coal anchor) read `COAL_FAMILY_KEYS`: the subclasses plus a legacy `COAL` row a pre-COAL-SUB payload may carry, as a reader of the historical record.
  - `legitimacy_diagnostics` folds the D-2/D-4 class vote to the coal family, so C8's forced-share denominator and rule-20 materiality stay all-coal (see §6).
  - `rubric-consts.js` is regenerated and exports `coalFamilyKeys` for the dashboard's family sums.
- **Re-score of every designated keeper from its committed bundle, old scorer vs new: 0 differing fields in every verdict.** No determination moved.

| ISO | Keeper | Determination (before = after) |
|---|---|---|
| CAISO | 2026-09-24-caiso-r-inputs-vintage | NOT-YET |
| ERCOT | 2026-09-24-r-inputs-2019-2025 | NOT-YET |
| MISO | 2026-09-24-rmiso-arm-b-mid | NOT-YET |
| NEISO | 2026-09-24-r-neiso-inputs-2019 | NOT-YET |
| NWPP | 2026-09-24-rnwpp-inputs-span | NOT-YET |
| NYISO | 2026-09-24-nyiso-r-inputs-860vintage | NOT-YET |
| PJM | 2026-09-25-pjm-r-pjm-2 | NOT-YET |
| SOCO | 2026-09-24-r-soco-corrected-inputs | PHYSICALLY-CALIBRATED (PRICE UNSCORED) |
| SPP | 2026-09-24-r-spp-corrected-inputs | NOT-YET |

## 5. Cost, stated

- **Every ISO's solve-surface key moves**, so there is a one-time cache miss. Seven registry rows moved and two names were added. The pins are advanced with a dated cause block in `tests/regression/test_persisted_identity.py`.
- **MISO, NEISO and PJM change on their next keeper re-solve**, through the generic-bucket plants only:
  - MISO: 2,140 MW in 2019, falling to 20 MW in 2024.
  - NEISO: 479 MW in 2019.
  - PJM: 5,373 MW in 2019, falling to 1,311 MW in 2022.
  - These plants now read their own rank's curve instead of the deleted generic `COAL` curve. For PJM that generic curve was its own fitted {0.648, 0.684, 0.792, 1.044}; each lane re-solves on its own cadence and reports the movement at full magnitude.
- **CAISO, ERCOT, NWPP, NYISO, SOCO and SPP are byte-identical** in every keeper year.
- **PJM/SPP `offer_curve_overrides.COAL` is retired.** It was an authorized price-tuning DOF-ledger entry (rule 1/13 carve-out) that reached only generic-bucket plants. With every plant resolved it has no target; its row should come off each ledger at the lane's next attestation.

## 6. Open question for the owner (rule 31)

C8's forced-energy share is currently scored on **all coal as one class** (the D-2 class vote is folded to the family), so no C8 number moves. Scoring it **per coal subclass** would be the literal reading of "every class table uses subclasses". But that is a rubric change: per-rank denominators and the 2 % materiality line can flip a verdict. That is an owner ruling, not a relabel. **Keep family-level C8, or move C8 to per-subclass?**

## 7. Reproduce

```
python scripts/probes/coal_subclass_snapshot.py --iso <ISO> --year <Y> [--set pjm_da_virtual_bids=false] --out <dir>
python scripts/probes/coal_subclass_compare.py --before <dir> --after <dir> --out <json>
python scripts/probes/coal_subclass_census.py --snap <before dir> --out <json> --md <md>
```
