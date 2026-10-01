# RESULT — C8-SUBCLASS: C8 scores each coal subclass as its own class (rubric v3.9, 2026-09-25)

**Owner ruling (2026-09-25):** "Yes" to the open question in `docs/handoffs/RESULT-coal-sub-2026-09-25.md` §6 (PR #6619): *"Keep family-level C8, or move C8 to per-subclass?"* C8 (rule 20 `[R-FORCED-BUDGET]`) now scores `COAL_BIT` / `COAL_PRB` / `COAL_LIGNITE` / `COAL_WC` each as its own class. This completes COAL-SUB: *"we need to completely eliminate the class Coal From the model altogether all coal should be sorted into its subclass"*.

**Scope:** scorer, diagnostics, docs and tests. **No LP was solved.** Every number below comes from zero-LP work: the committed run payloads, `run_year(fleet_only=True)` floor rebuilds, and re-scoring committed artifacts.

## 1. Headline

- **No C8 criterion status changed and no determination changed** on any of the 11 runs registered at session start, which covers all 9 designated keepers, including PJM's newest (`2026-09-25-pjm-next-c1`).
- One of those 11, CAISO `2026-09-24-caiso-r-inputs-vintage`, was pruned on `main` by R-CAISO-3 (rule 35) while this session ran. It stays in the tables as scored, but its artifact is not part of this change. 10 runs remain registered.
- Every non-C8 criterion, every non-coal C8 record, every reason line and every top-level verdict field is byte-identical before and after. The only change in the verdicts is the `rubric_version` field.
- **No coal subclass is over its 30 % cap in any material year of any run.** The highest material share is ERCOT `COAL_PRB` 2020 at **15.3 %** (5.48 of 35.93 TWh). Under the family row it was 13.4 %.
- **Per-year record changes** are reported at full magnitude in §4. There are two kinds:
  - **SPP 2019–2021:** coal moves from SKIPPED to PASS. This removes a gate blindness (§3.2).
  - **Newly immaterial subclasses.** Some subclasses now fall below the 2 % line and read SKIPPED. The case that matters is NEISO `r-neiso-inputs-2019` 2019/2021, where a family PASS becomes a `COAL_BIT` SKIPPED.

## 2. What changed

- **Where the class line is drawn:** `scripts/legitimacy_diagnostics.py::aggregate_floors_by_plant`.
  - The plant-class vote no longer folds coal onto the family (`artifact_class_array`). That fold is deleted, not zeroed (rule 26).
  - So D-2 emits one row per coal subclass. Each subclass gets its own forced share and denominator, its own ≥ 2 %-of-load materiality test on max(model, actual) subclass energy, its own 30 % merchant cap, and its own grounded-above-budget escalation.
  - D-1 already emitted rows per subclass.
  - **D-4 needed no change**: every coal-mechanism window is class-agnostic (`(MECH_COAL_MIN_CONFIG, None)`, `(MECH_COAL_MUSTRUN, None)`, `(MECH_MISO_COAL_NIGHT_FLOOR, None)`), and no window or cap was keyed on `COAL`. **No constant was added or moved.**
- **`_resplit_legacy_coal`** handles floors npz files persisted before COAL-SUB, which label coal `COAL`.
  - Those rows are relabelled to their subclass by joining `unit_id` against a `fleet_only` rebuild. The join is exact and never positional; the floors themselves are untouched.
  - A unit the rebuild does not carry keeps the family label. Nothing is invented.
- **`resplit_coal_d2` + `--resplit-coal-d2`** re-split a committed artifact in place.
  - They swap only the coal D-2 rows, summary rows and failures for those of a zero-LP D-2 recompute. Every non-coal row, D-1, D-4 and every other block stays byte-identical.
  - A `coal_subclass_resplit` block records the provenance and a per-year family cross-check.
  - Some years carry committed coal energy that the recompute cannot see. If the rebuilt fleet's coal that year is a single subclass, those years are relabelled exactly (`relabelled_years`). Otherwise they are kept as the family (`unresolved_years`, which is empty on every registered run).
- **COAL-SUB gap fixed on the way:** `_rebuild_fleet_arrays` now calls `replay_keeper.translate_legacy_coal_keys`.
  - Without it, every rebuild of a keeper whose recipe names the deleted `COAL` class in its offer-curve patches (SPP, PJM `offer_curve_overrides`; MISO `prb_overrides`) raised `BareCoalClassError`.
  - That includes the G-06 `--keepers` D-2 staleness check. The replay lane already translated these keys; this rebuild lane did not.
- **Scorer (`scripts/calibration_verdict.py`):** `RUBRIC_VERSION` 3.8 → **3.9**, with a genealogy block.
  - Its scoring paths already iterated the artifact's own class rows and looked up materiality by that class in `gmModel` / `classFull`.
  - The one logic change repairs the **legacy family reader** (§3.2).
  - `PLANT_GROUP_MEMBERS` / `COAL_FAMILY_KEYS` stay as readers of the historical record.
- **Regenerated:**
  - `frontend/data/backcast/rubric-consts.js` (rubricVersion 3.9)
  - `frontend/data/backcast/status/*.js` (all 9 ISOs + shared), which now carry the per-subclass C8 records
- **Rule 20 text in CLAUDE.md is unchanged.** It never names the coal family.

## 3. Method and basis

### 3.1 The recompute basis, disclosed

- The committed artifacts were written at solve time from `dispatch/<year>_P1.parquet`. That file is gitignored and absent from every bundle.
- The re-split therefore recomputes D-2 on the **rebuildable basis**:
  - the committed run payload (`frontend/data/backcast/runs/<id>.js`, per-plant CF bytes, annual totals exact)
  - plus `fleet_only` floors at this branch's HEAD
- This is the same basis the G-06 staleness check (`run_d2_keepers_verify`) uses.
- Every artifact records, per year, the committed family totals next to the sum over the new subclass rows (`coal_subclass_resplit.family_crosscheck`). The gap between them is the basis difference. In summary:

| ISO / run | Largest family-forced gap (TWh) | Largest family-total gap (TWh) | Note |
|---|---:|---:|---|
| ERCOT `r-4-day-guard` | −0.037 (2022) | ≤ 0.0001 | payload decode tolerance on `coal_min_config` |
| MISO `miso-272` | −0.096 (2022) | +1.41 (2019), ~0.6 % | 2019–2022, the years with the former generic-bucket plants COAL-SUB resolved |
| PJM `pjm-next-c1` | −0.063 (2019) | +0.93 (2020), ~0.5 % | 2019–2021 floors moved under COAL-SUB (generic-bucket plants plus limb-mate spillover, RESULT-coal-sub §2) |
| NEISO `r-neiso-inputs-2019` | +0.064 (2025) | ≤ 0.001 | immaterial class (0.4 % of load) |
| NEISO `neiso114` | −0.008 (2019), −0.007 (2025) | ≤ 0.0004 | immaterial |
| NWPP / SOCO / SPP | 0 (no coal forcing) | ≤ 0.63 (SPP 2023) | SPP 2023 `COAL_LIGNITE` holds a floor-substituted plant, so its share is an upper bound and the pass is sound |
| CAISO ×2 | 0 | 0 | r2's payload omits Argus Cogen's series, so it was relabelled exactly to `COAL_BIT` (single-subclass fleet) |

- None of these gaps comes near a cap. The largest material coal forced share on either basis is ERCOT 2020.

### 3.2 A latent blindness in the legacy family reader (repaired)

- The v2.8 bridge summed the subclasses into a legacy `COAL` row's materiality **only when the `COAL` key read 0.0 on both sides**.
- A pre-COAL-SUB payload carries the former generic bucket under `COAL`. For SPP 2019 that is 0.0389 TWh, from Western Sugar Scottsbluff, a 4.7 MW cogen.
- So the bridge stayed shut, and **SPP's whole coal fleet (74–96 TWh, 29–36 % of load) was read as 0.0 % of load and SKIPPED-immaterial in 2019, 2020 and 2021.**
- Per-subclass scoring removes this: those years now PASS (0.0 % forced).
- The reader now sums the aggregate key and its members unconditionally, so an artifact that still carries a family row cannot fall into this. After the re-split, no registered artifact carries one.

### 3.3 NYISO

- NYISO's rebuild fails on a pre-existing data gap: `nyiso_li_lcr_tsl` finds no published Long Island TSL row for delivery year 2022/2023 in `data/raw/capacity-deliverability/nyiso/nyiso.csv`.
- It needs no re-split. Coal is **0.0 TWh model and 0.0 TWh actual in every year 2022–2025**, and `run_d2` drops a class whose total is ≤ 0.
- Its artifact carries no coal row before or after, and its C8 is unchanged by construction.
- The data gap also blocks NYISO's G-06 recompute. It is reported here and not fixed, because it is out of scope.

### 3.4 Environment notes (no repository change)

- The PJM rebuild needed:
  - the gitignored `data/raw/pjm-da-virtuals/` corpus, re-fetched with `scripts/data/fetch_pjm_da_virtuals.py --years 2019…2025 --feeds hrl_da_incs_decs`, 84 months
  - two derived clean partitions, `transfer-interface-limits` and `ramp-capability`, built with `scripts/regenerate_clean.py`
- CAISO needed `tzdata`.
- None of these is committed.

## 4. Re-score: every registered run, before vs after

Before = `origin/main` @ `c64e69eb` with its committed artifacts and the v3.8 scorer. After = this branch.

| ISO | Run | C8 before | C8 after | Determination before | Determination after |
|---|---|---|---|---|---|
| CAISO | `2026-09-24-caiso-r-inputs-vintage` | PASS | PASS | NOT-YET | NOT-YET |
| NYISO | `2026-09-24-nyiso-r-inputs-860vintage` | PASS | PASS | NOT-YET | NOT-YET |
| NEISO | `2026-09-24-r-neiso-inputs-2019` | PASS | PASS | NOT-YET | NOT-YET |
| SPP | `2026-09-24-r-spp-corrected-inputs` | PASS | PASS | NOT-YET | NOT-YET |
| CAISO | `2026-09-25-caiso-r2-cc-gross` | PASS | PASS | CALIBRATED | CALIBRATED |
| MISO | `2026-09-25-miso-272-edwardsport-block` | PASS | PASS | NOT-YET | NOT-YET |
| NEISO | `2026-09-25-neiso114-coal-mustrun-measured` | PASS | PASS | NOT-YET | NOT-YET |
| NWPP | `2026-09-25-nwppnext2h-cascade-2019` | PASS | PASS | NOT-YET | NOT-YET |
| PJM | `2026-09-25-pjm-next-c1` | PASS | PASS | NOT-YET | NOT-YET |
| ERCOT | `2026-09-25-r-4-day-guard` | PASS | PASS | NOT-YET | NOT-YET |
| SOCO | `2026-09-25-soco67-precod-clip` | PASS | PASS | PHYSICALLY-CALIBRATED (PRICE UNSCORED) | PHYSICALLY-CALIBRATED (PRICE UNSCORED) |

#### CAISO — `2026-09-24-caiso-r-inputs-vintage`

| Year | Family before (forced / total TWh, C8) | Subclass | Forced TWh | Class TWh | Forced share | Load share (D-2 artifact) | C8 after (scorer) |
|---|---|---|---:|---:|---:|---:|---|
| 2022 | 0.0 / 0.105, SKIPPED | COAL_BIT | 0.0 | 0.105 | 0.0 % | 0.1 % | SKIPPED |
| 2023 | 0.0 / 0.0897, SKIPPED | COAL_BIT | 0.0 | 0.0897 | 0.0 % | 0.0 % | SKIPPED |
| 2024 | 0.0 / 0.0473, SKIPPED | COAL_BIT | 0.0 | 0.0473 | 0.0 % | 0.0 % | SKIPPED |
| 2025 | 0.0 / 0.0777, SKIPPED | COAL_BIT | 0.0 | 0.0777 | 0.0 % | 0.0 % | SKIPPED |

#### NYISO — `2026-09-24-nyiso-r-inputs-860vintage`

No coal D-2 row before or after (no coal energy in any year).

#### NEISO — `2026-09-24-r-neiso-inputs-2019`

| Year | Family before (forced / total TWh, C8) | Subclass | Forced TWh | Class TWh | Forced share | Load share (D-2 artifact) | C8 after (scorer) |
|---|---|---|---:|---:|---:|---:|---|
| 2019 | 0.14 / 1.0988, PASS | COAL_BIT | 0.1401 | 1.0988 | 12.8 % | 1.1 % | SKIPPED |
| 2020 | 0.1574 / 0.4292, SKIPPED | COAL_BIT | 0.1572 | 0.4292 | 36.6 % | 0.5 % | SKIPPED |
| 2021 | 0.0573 / 1.5112, PASS | COAL_BIT | 0.0568 | 1.5112 | 3.8 % | 1.5 % | SKIPPED |
| 2022 | 0.0045 / 2.9304, PASS | COAL_BIT | 0.0045 | 2.9303 | 0.1 % | 2.9 % | PASS |
| 2023 | 0.0617 / 0.6446, SKIPPED | COAL_BIT | 0.0612 | 0.6444 | 9.5 % | 0.7 % | SKIPPED |
| 2024 | 0.1212 / 0.403, SKIPPED | COAL_BIT | 0.1205 | 0.403 | 29.9 % | 0.4 % | SKIPPED |
| 2025 | 0.0069 / 0.4824, SKIPPED | COAL_BIT | 0.0707 | 0.4819 | 14.7 % | 0.4 % | SKIPPED |

#### SPP — `2026-09-24-r-spp-corrected-inputs`

| Year | Family before (forced / total TWh, C8) | Subclass | Forced TWh | Class TWh | Forced share | Load share (D-2 artifact) | C8 after (scorer) |
|---|---|---|---:|---:|---:|---:|---|
| 2019 | 0.0 / 89.6185, SKIPPED | COAL_LIGNITE | 0.0 | 11.0081 | 0.0 % | 5.1 % | PASS |
| 2019 | 0.0 / 89.6185, SKIPPED | COAL_PRB | 0.0 | 78.6105 | 0.0 % | 31.3 % | PASS |
| 2020 | 0.0 / 73.7295, SKIPPED | COAL_LIGNITE | 0.0 | 8.2936 | 0.0 % | 4.5 % | PASS |
| 2020 | 0.0 / 73.7295, SKIPPED | COAL_PRB | 0.0 | 65.436 | 0.0 % | 28.8 % | PASS |
| 2021 | 0.0 / 96.1034, SKIPPED | COAL_LIGNITE | 0.0 | 8.9498 | 0.0 % | 4.2 % | PASS |
| 2021 | 0.0 / 96.1034, SKIPPED | COAL_PRB | 0.0 | 87.1521 | 0.0 % | 32.3 % | PASS |
| 2022 | 0.0 / 100.9146, PASS | COAL_LIGNITE | 0.0 | 12.5276 | 0.0 % | 4.8 % | PASS |
| 2022 | 0.0 / 100.9146, PASS | COAL_PRB | 0.0 | 88.387 | 0.0 % | 30.7 % | PASS |
| 2023 | 0.0 / 75.435, PASS | COAL_LIGNITE | 0.0 | 7.8571 | 0.0 % | 3.1 % | PASS |
| 2023 | 0.0 / 75.435, PASS | COAL_PRB | 0.0 | 68.203 | 0.0 % | 25.7 % | PASS |
| 2024 | 0.0 / 67.5044, PASS | COAL_LIGNITE | 0.0 | 6.355 | 0.0 % | 3.1 % | PASS |
| 2024 | 0.0 / 67.5044, PASS | COAL_PRB | 0.0 | 61.1497 | 0.0 % | 22.4 % | PASS |
| 2025 | 0.0 / 83.2889, PASS | COAL_LIGNITE | 0.0 | 6.3777 | 0.0 % | 3.0 % | PASS |
| 2025 | 0.0 / 83.2889, PASS | COAL_PRB | 0.0 | 76.9114 | 0.0 % | 25.5 % | PASS |

#### CAISO — `2026-09-25-caiso-r2-cc-gross`

| Year | Family before (forced / total TWh, C8) | Subclass | Forced TWh | Class TWh | Forced share | Load share (D-2 artifact) | C8 after (scorer) |
|---|---|---|---:|---:|---:|---:|---|
| 2022 | 0.0 / 0.1049, SKIPPED | COAL_BIT | 0.0 | 0.1049 | 0.0 % | 0.1 % | SKIPPED |
| 2023 | 0.0 / 0.0896, SKIPPED | COAL_BIT | 0.0 | 0.0896 | 0.0 % | 0.0 % | SKIPPED |
| 2024 | 0.0 / 0.0463, SKIPPED | COAL_BIT | 0.0 | 0.0463 | 0.0 % | 0.0 % | SKIPPED |
| 2025 | 0.0 / 0.0774, SKIPPED | COAL_BIT | 0.0 | 0.0774 | 0.0 % | 0.0 % | SKIPPED |

relabelled exactly (single-subclass fleet, recompute blind): {'2022': 'COAL_BIT', '2023': 'COAL_BIT', '2024': 'COAL_BIT', '2025': 'COAL_BIT'}

#### MISO — `2026-09-25-miso-272-edwardsport-block`

| Year | Family before (forced / total TWh, C8) | Subclass | Forced TWh | Class TWh | Forced share | Load share (D-2 artifact) | C8 after (scorer) |
|---|---|---|---:|---:|---:|---:|---|
| 2019 | 0.8659 / 246.7459, PASS | COAL_BIT | 0.8046 | 81.1256 | 1.0 % | 13.0 % | PASS |
| 2019 | 0.8659 / 246.7459, PASS | COAL_LIGNITE | 0.0 | 8.9962 | 0.0 % | 1.4 % | SKIPPED |
| 2019 | 0.8659 / 246.7459, PASS | COAL_PRB | 0.0185 | 158.0378 | 0.0 % | 27.0 % | PASS |
| 2020 | 0.5603 / 196.6206, PASS | COAL_BIT | 0.5609 | 60.7628 | 0.9 % | 10.4 % | PASS |
| 2020 | 0.5603 / 196.6206, PASS | COAL_LIGNITE | 0.0 | 9.1943 | 0.0 % | 1.5 % | SKIPPED |
| 2020 | 0.5603 / 196.6206, PASS | COAL_PRB | 0.0101 | 127.8768 | 0.0 % | 22.9 % | PASS |
| 2021 | 0.8476 / 245.2147, PASS | COAL_BIT | 0.5308 | 75.548 | 0.7 % | 12.0 % | PASS |
| 2021 | 0.8476 / 245.2147, PASS | COAL_LIGNITE | 0.0446 | 8.6267 | 0.5 % | 1.4 % | SKIPPED |
| 2021 | 0.8476 / 245.2147, PASS | COAL_PRB | 0.2353 | 162.3339 | 0.1 % | 27.7 % | PASS |
| 2022 | 1.2996 / 227.3145, PASS | COAL_BIT | 0.8107 | 71.5566 | 1.1 % | 11.0 % | PASS |
| 2022 | 1.2996 / 227.3145, PASS | COAL_LIGNITE | 0.0 | 6.3249 | 0.0 % | 1.1 % | SKIPPED |
| 2022 | 1.2996 / 227.3145, PASS | COAL_PRB | 0.3926 | 150.7566 | 0.3 % | 24.9 % | PASS |
| 2023 | 0.6979 / 177.5004, PASS | COAL_BIT | 0.1179 | 53.0909 | 0.2 % | 8.8 % | PASS |
| 2023 | 0.6979 / 177.5004, PASS | COAL_LIGNITE | 0.0 | 6.1769 | 0.0 % | 1.2 % | SKIPPED |
| 2023 | 0.6979 / 177.5004, PASS | COAL_PRB | 0.5797 | 118.6126 | 0.5 % | 20.9 % | PASS |
| 2024 | 0.8044 / 168.6985, PASS | COAL_BIT | 0.6048 | 50.3428 | 1.2 % | 8.5 % | PASS |
| 2024 | 0.8044 / 168.6985, PASS | COAL_LIGNITE | 0.0 | 5.6557 | 0.0 % | 1.1 % | SKIPPED |
| 2024 | 0.8044 / 168.6985, PASS | COAL_PRB | 0.2009 | 112.8538 | 0.2 % | 20.0 % | PASS |
| 2025 | 0.4902 / 193.4752, PASS | COAL_BIT | 0.2099 | 53.7305 | 0.4 % | 8.3 % | PASS |
| 2025 | 0.4902 / 193.4752, PASS | COAL_LIGNITE | 0.0 | 5.2752 | 0.0 % | 1.0 % | SKIPPED |
| 2025 | 0.4902 / 193.4752, PASS | COAL_PRB | 0.2792 | 134.5501 | 0.2 % | 23.0 % | PASS |

#### NEISO — `2026-09-25-neiso114-coal-mustrun-measured`

| Year | Family before (forced / total TWh, C8) | Subclass | Forced TWh | Class TWh | Forced share | Load share (D-2 artifact) | C8 after (scorer) |
|---|---|---|---:|---:|---:|---:|---|
| 2019 | 0.145 / 0.807, SKIPPED | COAL_BIT | 0.1374 | 0.8071 | 17.0 % | 0.8 % | SKIPPED |
| 2020 | 0.1574 / 0.3083, SKIPPED | COAL_BIT | 0.1572 | 0.3083 | 51.0 % | 0.3 % | SKIPPED |
| 2021 | 0.057 / 1.513, SKIPPED | COAL_BIT | 0.0565 | 1.513 | 3.7 % | 1.5 % | SKIPPED |
| 2022 | 0.0045 / 2.9304, PASS | COAL_BIT | 0.0045 | 2.9303 | 0.1 % | 2.9 % | PASS |
| 2023 | 0.0617 / 0.6446, SKIPPED | COAL_BIT | 0.0612 | 0.6444 | 9.5 % | 0.7 % | SKIPPED |
| 2024 | 0.1212 / 0.403, SKIPPED | COAL_BIT | 0.1205 | 0.403 | 29.9 % | 0.4 % | SKIPPED |
| 2025 | 0.0069 / 0.3324, SKIPPED | COAL_BIT | 0.0 | 0.332 | 0.0 % | 0.3 % | SKIPPED |

#### NWPP — `2026-09-25-nwppnext2h-cascade-2019`

| Year | Family before (forced / total TWh, C8) | Subclass | Forced TWh | Class TWh | Forced share | Load share (D-2 artifact) | C8 after (scorer) |
|---|---|---|---:|---:|---:|---:|---|
| 2019 | 0.0 / 56.6147, PASS | COAL_BIT | 0.0 | 18.7369 | 0.0 % | 10.3 % | PASS |
| 2019 | 0.0 / 56.6147, PASS | COAL_PRB | 0.0 | 37.735 | 0.0 % | 15.0 % | PASS |
| 2019 | 0.0 / 56.6147, PASS | COAL_WC | 0.0 | 0.2599 | 0.0 % | 0.2 % | SKIPPED |
| 2020 | 0.0 / 42.5689, PASS | COAL_BIT | 0.0 | 17.0011 | 0.0 % | 8.3 % | PASS |
| 2020 | 0.0 / 42.5689, PASS | COAL_PRB | 0.0 | 25.5069 | 0.0 % | 11.5 % | PASS |
| 2020 | 0.0 / 42.5689, PASS | COAL_WC | 0.0 | 0.1506 | 0.0 % | 0.1 % | SKIPPED |
| 2021 | 0.0 / 54.5564, PASS | COAL_BIT | 0.0 | 24.2553 | 0.0 % | 8.8 % | PASS |
| 2021 | 0.0 / 54.5564, PASS | COAL_PRB | 0.0 | 30.0131 | 0.0 % | 11.6 % | PASS |
| 2021 | 0.0 / 54.5564, PASS | COAL_WC | 0.0 | 0.409 | 0.0 % | 0.2 % | SKIPPED |
| 2022 | 0.0 / 60.5426, PASS | COAL_BIT | 0.0 | 24.9576 | 0.0 % | 8.5 % | PASS |
| 2022 | 0.0 / 60.5426, PASS | COAL_PRB | 0.0 | 35.0441 | 0.0 % | 11.9 % | PASS |
| 2022 | 0.0 / 60.5426, PASS | COAL_WC | 0.0 | 0.5409 | 0.0 % | 0.2 % | SKIPPED |
| 2023 | 0.0 / 48.4483, PASS | COAL_BIT | 0.0 | 19.1331 | 0.0 % | 7.0 % | PASS |
| 2023 | 0.0 / 48.4483, PASS | COAL_PRB | 0.0 | 29.0062 | 0.0 % | 11.7 % | PASS |
| 2023 | 0.0 / 48.4483, PASS | COAL_WC | 0.0 | 0.3089 | 0.0 % | 0.1 % | SKIPPED |
| 2024 | 0.0 / 31.1337, PASS | COAL_BIT | 0.0 | 12.7871 | 0.0 % | 5.6 % | PASS |
| 2024 | 0.0 / 31.1337, PASS | COAL_PRB | 0.0 | 18.177 | 0.0 % | 7.6 % | PASS |
| 2024 | 0.0 / 31.1337, PASS | COAL_WC | 0.0 | 0.1697 | 0.0 % | 0.1 % | SKIPPED |
| 2025 | 0.0 / 30.848, PASS | COAL_BIT | 0.0 | 12.2238 | 0.0 % | 6.9 % | PASS |
| 2025 | 0.0 / 30.848, PASS | COAL_PRB | 0.0 | 18.7194 | 0.0 % | 7.4 % | PASS |
| 2025 | 0.0 / 30.848, PASS | COAL_WC | 0.0 | 0.0113 | 0.0 % | 0.1 % | SKIPPED |

#### PJM — `2026-09-25-pjm-next-c1`

| Year | Family before (forced / total TWh, C8) | Subclass | Forced TWh | Class TWh | Forced share | Load share (D-2 artifact) | C8 after (scorer) |
|---|---|---|---:|---:|---:|---:|---|
| 2019 | 0.1428 / 214.531, PASS | COAL_BIT | 0.0689 | 199.5365 | 0.0 % | 24.9 % | PASS |
| 2019 | 0.1428 / 214.531, PASS | COAL_PRB | 0.0059 | 10.6331 | 0.1 % | 1.3 % | SKIPPED |
| 2019 | 0.1428 / 214.531, PASS | COAL_WC | 0.0053 | 5.2747 | 0.1 % | 0.8 % | SKIPPED |
| 2020 | 0.3288 / 171.2229, PASS | COAL_BIT | 0.1602 | 160.6917 | 0.1 % | 20.9 % | PASS |
| 2020 | 0.3288 / 171.2229, PASS | COAL_PRB | 0.0318 | 7.5499 | 0.4 % | 1.0 % | SKIPPED |
| 2020 | 0.3288 / 171.2229, PASS | COAL_WC | 0.1022 | 3.9276 | 2.6 % | 0.7 % | SKIPPED |
| 2021 | 0.083 / 214.5399, PASS | COAL_BIT | 0.0213 | 194.1865 | 0.0 % | 24.4 % | PASS |
| 2021 | 0.083 / 214.5399, PASS | COAL_PRB | 0.0 | 15.0935 | 0.0 % | 1.9 % | SKIPPED |
| 2021 | 0.083 / 214.5399, PASS | COAL_WC | 0.0603 | 6.2111 | 1.0 % | 0.8 % | SKIPPED |
| 2022 | 0.1161 / 171.2216, PASS | COAL_BIT | 0.075 | 153.8765 | 0.1 % | 19.0 % | PASS |
| 2022 | 0.1161 / 171.2216, PASS | COAL_PRB | 0.0 | 11.8423 | 0.0 % | 1.5 % | SKIPPED |
| 2022 | 0.1161 / 171.2216, PASS | COAL_WC | 0.0413 | 6.4167 | 0.6 % | 0.9 % | SKIPPED |
| 2023 | 0.1855 / 116.5764, PASS | COAL_BIT | 0.1784 | 109.0363 | 0.2 % | 13.9 % | PASS |
| 2023 | 0.1855 / 116.5764, PASS | COAL_PRB | 0.0 | 3.5568 | 0.0 % | 0.5 % | SKIPPED |
| 2023 | 0.1855 / 116.5764, PASS | COAL_WC | 0.0069 | 4.7418 | 0.1 % | 0.8 % | SKIPPED |
| 2024 | 0.3152 / 120.1353, PASS | COAL_BIT | 0.2794 | 111.7453 | 0.2 % | 13.8 % | PASS |
| 2024 | 0.3152 / 120.1353, PASS | COAL_PRB | 0.0 | 4.4034 | 0.0 % | 0.5 % | SKIPPED |
| 2024 | 0.3152 / 120.1353, PASS | COAL_WC | 0.0354 | 4.8489 | 0.7 % | 0.8 % | SKIPPED |
| 2025 | 0.0716 / 146.8411, PASS | COAL_BIT | 0.0624 | 135.5131 | 0.1 % | 16.1 % | PASS |
| 2025 | 0.0716 / 146.8411, PASS | COAL_PRB | 0.0 | 6.7041 | 0.0 % | 0.8 % | SKIPPED |
| 2025 | 0.0716 / 146.8411, PASS | COAL_WC | 0.009 | 5.5065 | 0.2 % | 0.7 % | SKIPPED |

#### ERCOT — `2026-09-25-r-4-day-guard`

| Year | Family before (forced / total TWh, C8) | Subclass | Forced TWh | Class TWh | Forced share | Load share (D-2 artifact) | C8 after (scorer) |
|---|---|---|---:|---:|---:|---:|---|
| 2019 | 4.93 / 64.3441, PASS | COAL_LIGNITE | 1.2725 | 16.4104 | 7.8 % | 4.4 % | PASS |
| 2019 | 4.93 / 64.3441, PASS | COAL_PRB | 3.6291 | 47.9336 | 7.6 % | 15.3 % | PASS |
| 2020 | 6.9698 / 52.2232, PASS | COAL_LIGNITE | 1.4381 | 16.2959 | 8.8 % | 4.7 % | PASS |
| 2020 | 6.9698 / 52.2232, PASS | COAL_PRB | 5.4834 | 35.9272 | 15.3 % | 13.2 % | PASS |
| 2021 | 2.2241 / 71.4433, PASS | COAL_LIGNITE | 0.7204 | 16.8827 | 4.3 % | 4.3 % | PASS |
| 2021 | 2.2241 / 71.4433, PASS | COAL_PRB | 1.4899 | 54.5607 | 2.7 % | 15.1 % | PASS |
| 2022 | 1.0954 / 76.134, PASS | COAL_LIGNITE | 0.3908 | 17.5657 | 2.2 % | 4.1 % | PASS |
| 2022 | 1.0954 / 76.134, PASS | COAL_PRB | 0.6676 | 58.5683 | 1.1 % | 13.7 % | PASS |
| 2023 | 4.4515 / 59.8695, PASS | COAL_LIGNITE | 0.9795 | 16.6381 | 5.9 % | 3.7 % | PASS |
| 2023 | 4.4515 / 59.8695, PASS | COAL_PRB | 3.4567 | 43.2315 | 8.0 % | 10.5 % | PASS |
| 2024 | 4.4943 / 56.5781, PASS | COAL_LIGNITE | 0.9926 | 15.0824 | 6.6 % | 3.3 % | PASS |
| 2024 | 4.4943 / 56.5781, PASS | COAL_PRB | 3.4674 | 41.4958 | 8.4 % | 9.9 % | PASS |
| 2025 | 2.0268 / 64.0286, PASS | COAL_LIGNITE | 1.1903 | 15.0748 | 7.9 % | 3.1 % | PASS |
| 2025 | 2.0268 / 64.0286, PASS | COAL_PRB | 0.8194 | 48.9539 | 1.7 % | 10.2 % | PASS |

#### SOCO — `2026-09-25-soco67-precod-clip`

| Year | Family before (forced / total TWh, C8) | Subclass | Forced TWh | Class TWh | Forced share | Load share (D-2 artifact) | C8 after (scorer) |
|---|---|---|---:|---:|---:|---:|---|
| 2019 | 0.0 / 64.3947, PASS | COAL_BIT | 0.0 | 30.4845 | 0.0 % | 12.4 % | PASS |
| 2019 | 0.0 / 64.3947, PASS | COAL_PRB | 0.0 | 33.9103 | 0.0 % | 13.8 % | PASS |
| 2020 | 0.0 / 46.9591, PASS | COAL_BIT | 0.0 | 25.2555 | 0.0 % | 10.9 % | PASS |
| 2020 | 0.0 / 46.9591, PASS | COAL_PRB | 0.0 | 21.7035 | 0.0 % | 10.3 % | PASS |
| 2021 | 0.0 / 60.8335, PASS | COAL_BIT | 0.0 | 29.6325 | 0.0 % | 12.4 % | PASS |
| 2021 | 0.0 / 60.8335, PASS | COAL_PRB | 0.0 | 31.2009 | 0.0 % | 13.0 % | PASS |
| 2022 | 0.0 / 55.9473, PASS | COAL_BIT | 0.0 | 23.1709 | 0.0 % | 9.5 % | PASS |
| 2022 | 0.0 / 55.9473, PASS | COAL_PRB | 0.0 | 32.7765 | 0.0 % | 13.4 % | PASS |
| 2023 | 0.0 / 29.0284, PASS | COAL_BIT | 0.0 | 8.1635 | 0.0 % | 4.7 % | PASS |
| 2023 | 0.0 / 29.0284, PASS | COAL_PRB | 0.0 | 20.8649 | 0.0 % | 10.2 % | PASS |
| 2024 | 0.0 / 30.4868, PASS | COAL_BIT | 0.0 | 8.033 | 0.0 % | 4.7 % | PASS |
| 2024 | 0.0 / 30.4868, PASS | COAL_PRB | 0.0 | 22.4538 | 0.0 % | 11.2 % | PASS |
| 2025 | 0.0 / 41.6238, PASS | COAL_BIT | 0.0 | 11.5285 | 0.0 % | 5.3 % | PASS |
| 2025 | 0.0 / 41.6238, PASS | COAL_PRB | 0.0 | 30.0954 | 0.0 % | 11.9 % | PASS |


### 4.1 Every per-year coal C8 record whose status moved

| Run | Year | Family (before) | Subclasses (after) | Why |
|---|---|---|---|---|
| SPP `r-spp-corrected-inputs` | 2019, 2020, 2021 | SKIPPED | `COAL_PRB` PASS, `COAL_LIGNITE` PASS | §3.2 blindness removed (0.0 % forced; PRB 29–32 %, lignite 4.2–5.1 % of load) |
| NEISO `r-neiso-inputs-2019` | 2019 | PASS (12.7 % forced; family 2.2 % of load) | `COAL_BIT` SKIPPED (12.8 % forced, 0.8 % of load by the scorer) | the family was made material by the payload's generic-bucket `COAL` value (2.09 TWh — Bridgeport 568's coal, which the D-2 plant vote attributes to gas by capacity); `COAL_BIT` alone is under 2 % |
| NEISO `r-neiso-inputs-2019` | 2021 | PASS (3.8 % forced; family 2.1 % of load) | `COAL_BIT` SKIPPED (3.8 % forced, 1.5 % of load) | the family bridge added `COAL_PRB` (0.60 TWh, Bridgeport); `COAL_BIT` alone is 1.5 % of load |

The following are **new per-subclass records beside a subclass that keeps the family's status**:

- MISO: `COAL_LIGNITE` SKIPPED in every year (1.0–1.5 % of load)
- NWPP: `COAL_WC` SKIPPED (≤ 0.2 %)
- PJM: `COAL_PRB` and `COAL_WC` SKIPPED (0.5–1.9 %)

In every one of those years the material subclasses PASS, as the family did.

**Pre-existing, not introduced here:** a coal subclass inside a plant whose capacity vote goes to another class, such as NEISO Bridgeport's coal unit (`COAL_PRB`, 0.27–0.77 TWh), has no D-2 row of its own at plant grain. It had none under the family fold either. That class is below 2 % of NEISO load in every year. No re-split artifact carries an orphaned coal-subclass floor row, meaning a forced subclass with no denominator.

## 5. Files

- `scripts/legitimacy_diagnostics.py`: class vote, `_resplit_legacy_coal`, `resplit_coal_d2`, `--resplit-coal-d2`, legacy-key translation in `_rebuild_fleet_arrays`
- `scripts/calibration_verdict.py`: v3.9 genealogy and the legacy family reader repair
- `docs/calibration-determination-rubric.md`: C8 per-subclass paragraph and the §9 v3.9 entry
- `tests/scoring/test_c8_coal_subclass.py`: a trivial two-subclass fixture where one subclass is over its cap and one is under, on a family whose pooled share passes; per-subclass materiality; the splice; blind-year relabel and keep; legacy npz re-split; the legacy reader
- `results/calibration/*/legitimacy_diagnostics.json` × 9: every bundle still registered on `main` except NYISO's (§3.3), `frontend/data/backcast/status/*.js`, `frontend/data/backcast/rubric-consts.js`

## 6. Reproduce

```
python3 scripts/legitimacy_diagnostics.py --bundle results/calibration/<bundle> --iso <ISO> --resplit-coal-d2
python3 scripts/calibration_verdict.py --json --run-id <run id>
```

## 7. Addendum: rebase onto `main` (same day)

Four keepers were promoted on `main` while this PR was open. The ones they replaced (NWPP `nwppnext2h-cascade-2019`, SOCO `soco67-precod-clip`, NYISO `nyiso-r-inputs-860vintage`, NEISO `neiso114-coal-mustrun-measured`, plus NEISO's stale `r-neiso-inputs-2019`) were pruned, and their re-split artifacts were dropped in the rebase.

The new keepers were handled the same way as the rest, with before scores from `main`'s v3.8 scorer and after scores from v3.9:

| ISO | Run | C8 before → after | Determination before → after | Coal rows |
|---|---|---|---|---|
| NWPP | `2026-09-25-nwppnext3-plant-basis` | PASS → PASS | NOT-YET → NOT-YET | re-split: `COAL_BIT` and `COAL_PRB` PASS (0.0 % forced), `COAL_WC` SKIPPED (immaterial); family cross-check gap ≤ 0.12 TWh total, 0 forced |
| SOCO | `2026-09-25-soco68-summer-basis` | PASS → PASS | NOT-YET → NOT-YET | re-split: `COAL_BIT` and `COAL_PRB` PASS (0.0 % forced); gap ≤ 0.0001 TWh |
| NEISO | `2026-09-25-neiso114-arm-b-stgas` | PASS → PASS | NOT-YET → NOT-YET | re-split: all NEISO coal is `COAL_BIT`; per-year statuses identical to the family's (2022 PASS, others SKIPPED immaterial); forced gap ≤ 0.0074 TWh |
| MISO | `2026-09-25-miso-273-screened-coal` (registered 2026-09-25, not yet the keeper) | PASS → PASS | NOT-YET → NOT-YET | re-split: `COAL_BIT` and `COAL_PRB` PASS every year, `COAL_LIGNITE` SKIPPED (immaterial); forced gap ≤ 0.077 TWh |
| NYISO | `2026-09-25-nyiso-stgas-ldc-leg` | PASS → PASS | CALIBRATED → CALIBRATED | none (no coal energy) |
| NYISO | `2026-09-25-nyiso-stgas-ldc-2021` | PASS → PASS | CALIBRATED → CALIBRATED | none (no coal energy) |

Across all 11 runs registered after the final rebase, no C8 status and no determination changed. Every non-C8 criterion and every non-coal C8 record is byte-identical before and after.
