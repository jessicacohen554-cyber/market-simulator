# EIA-860 CAPACITY / VINTAGE / COD — cross-ISO audit and settlement specification (2026-10-02, read-only shard)

Scope: the capacity pipeline as it exists at HEAD (`main`; keepers registered 2026-09-26 … 2026-10-01), every recorded 860 defect since June 2026, the pattern behind the recurrence, a zero-LP census over all 9 ISOs × 2019-2025, an external best-practice review, and a testable definition of "settled". Zero LP. Zero repo edits. Every number is read from code, committed records, committed `run_config.json`s, parquet under `data/raw/` and `results/`, or the public web.

---

## A. The capacity pipeline at HEAD

### A.0 What is on disk (`data/raw/eia-860/`, its README)

| Item | Content | Note |
|---|---|---|
| top level `eia860_*.parquet` | **2025 Early Release** (June 2026): operable / proposed / retired-and-canceled / plant / owner / utility / wind / solar / storage / multifuel / enviro | README L1-14. Read by every forecast and by the backcast **for solve year 2025** (no `vintage_2025/`). **EIA published Final 2025 on 2026-09-10** (`eia8602025.zip`, [eia.gov/eia860](https://www.eia.gov/electricity/data/eia860/)); the repo does not have it. |
| `vintage_2018 … vintage_2022` | full sheet set incl. `eia860_generator_retired_and_canceled.parquet` (5 retired files each) | year-matched Final releases |
| `vintage_2023`, `vintage_2024` | operable / proposed / plant / owner / utility / wind / solar / storage / multifuel — **no retired sheet** (0 files) | README "Vintage snapshot completeness". A plant that retired *during* 2023 or 2024 is in neither sheet of its own vintage → `mid_vintage_exit_carry` exists only to patch this (§B). |
| `eia860_generator_retired_within_window.parquet` | whole-plant exits 2019+ projected from the 2018-2022 retired sheets + the current release (`RETIREMENT_WINDOW_START=2019`, `scripts/data/process_eia860.py:139`) | status forced `OP`, actual `Retirement Month/Year` written into `planned_retirement_*` (`process_eia860.py:630-676`) |
| EIA-860M | **not on disk** (`grep -ri 860m` hits only probes/docs) | latest 860M = August 2026 inventory, released 2026-09-24 ([eia.gov/eia860m](https://www.eia.gov/electricity/data/eia860m/)) |
| raw zips | not committed; `.gitignore:72` ignores `data/raw/eia-860/*.csv` | regeneration needs a re-download |
| `_processed-legacy/eia860_chp_by_year.parquet` | per-year plant CHP flag from every annual zip (`scripts/data/build_eia860_chp_by_year.py`) | |
| `reference/camd-eia-crosswalk/epa_eia_crosswalk.csv` | the official EPA CAMD-EIA crosswalk | used only through hand-grown `CAMPD_UNIT_PLANT_REMAP` rows (`src/market_sim/data/campd.py:297`) |
| `reference/custom-bin-assignments.csv` | ERCOT's hand-curated plant×tranche sheet, 310 rows, `Nameplate_MW`, one snapshot for every year | the ERCOT fleet of record (§A.1 step 8) |

### A.1 Steps 1-12, with the exact transformation (backcast path; forecast differences noted)

| # | Step (file:line) | Transformation | ISOs |
|---|---|---|---|
| 1 | `scripts/data/process_eia860.py::extract_all_workbooks` L204 → `build_generator_table` L234 | Raw zip → one parquet per sheet; `eia860_generators.parquet` = operable sheet joined to the plant's BA code, **filtered at derive time to `BA_CODE_TO_ISO`** (`_admit_footprint` L50; NWPP adds NERC=WECC, `fleet/models.py:301`). eGRID `PLHTRT` plant heat rate joined per matching vintage (`_join_egrid_heat_rate` L468, F1 2026-09-24). | all |
| 1b | `rescope_generator_table_from_parquet` L280 | Strictly additive re-derive of a vintage's generator table from its own committed sheets when a BA joins the program (SPP-38) or a BA/plant joins/leaves a region (`--admit-ba`, `--admit-plant`). Derive-time filtering is why SWPP was absent from 4 of 7 vintages (SPP-40). | SPP, SOCO |
| 2 | `config/paths.py::resolve_backcast_eia860_vintage` L218 → `set_eia860_vintage` L140 | explicit `eia860_vintage_year` > `eia860_vintage_tracks_solve_year` (default **True** in backcast since F1, `scenarios.py:5936`; coerced off outside backcast) → `vintage_<Y>/`; a year with no dir (2025) falls to the 2025ER. Process-global directory; `@lru_cache` loaders key on it (`tests/unit/data/test_eia860_vintage_cache_keying.py`). | all 9 keepers read `True` (§A.3) |
| 3 | `paths.py::set_eia860_standby_admission` L203 → `eia860_operable_statuses` L186 | Admitted status set `{OP}` (default) or `{OP, SB}` under `admit_standby_units` (`scenarios.py:12890`), applied at the one seam `eia860._rows_to_generators` (status filter `eia860.py:1430`). | NWPP keeper `True`; 8 keepers `False` |
| 4 | `data/fleet/eia860.py::_load_fleet_from_parquet` L2224 | BA membership `ba_codes(iso) + joining_ba_codes(iso, year)` (`ISO_BA_JOINS` `constants.py:2658`: SOCO AEC 2021-09, PJM OVEC 2019-01) ∪ `_exit_member_mask` L2212 (`ISO_BA_EXITS` L2694: SOCO Gulf→FPL 2022-07-13 12:00) − `drop_current_ba_recoded_rows` (`ba_membership.py:281`; `ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE` L2590, SOCO only). CHP flag joined per vintage; **`Operating Month` joined per unit from the raw operable sheet** (`_operating_month_by_unit` L2182, SOCO-15). Optional `cc_block_summer_rating` block reconcile before the row loop (`_apply_cc_block_summer_rating` L2042; predicate `_cc_block_summer_ratings` L1909, non-NG blocks only). | the 8 plant-level ISOs; ERCOT only for unbinned rows |
| 5 | `_rows_to_generators` L1349, row loop L1600-1630 | **pmax = `Summer Capacity (MW)` (net summer), else `Nameplate Capacity (MW)`** (L1607-1611, year-round); `online_year = Operating Year or 2000` (sentinel "unknown", L1613); `online_month` default 1; `retirement_year/month = Planned Retirement` (L1615-1616); pmin by class literal (nuclear 0.9, coal 0.4, else 0; L1623-1629). Heat-rate seams (eGRID boundary repair, simple-cycle floor, family/identity/EIA-923 family, measured CAMPD CT/coal/ST/CC). CC steam-part repair/reclass gated by `CC_STEAM_PART_REPAIR_ISOS={MISO}` / `_RECLASS_ISOS={NEISO}` (`plant_taxonomy.py:303,334`). | all |
| 6 | `_reconcile_cc_pmax_to_nameplate` L1022 (**always on, ungated**) | Per CC_REGULAR plant, if Σpmax > max(Σnameplate, CAMPD p99.9)×tol, scale every row down (double-filed-phantom guard: Keys 60302, Camden 10751). Demonstrated peaks from `_processed-legacy/cc_capacity_reconcile_<ISO>.csv` — tables exist for 6 ISOs; **SPP/NWPP/SOCO have none** → clip to nameplate. | all |
| 7 | Backcast-only injection channels: `load_retired_within_window` L3371 (+ `retiree_vintage_status_scope` via `_retiree_vintage_status` L3040, `partial_plant_exit_carry` via `_partial_plant_exit_rows` L3103, `mid_vintage_exit_carry` via `_mid_vintage_exit_rows` L3180), `load_mothballed_but_operating` L3615 (`carry_operating_mothballs`) | Units the active snapshot cannot carry. With a year-matched vintage the whole-plant retiree channel is a no-op; only `mid_vintage_exit_carry` (plant retired during Y — needs the retired sheets `vintage_2023/2024` lack) and `partial_plant_exit_carry` still add rows. Forecast mirror: `load_planned_additions` L3785 (proposed sheet, status U/V/TS). | per-ISO flags, §A.3 |
| 8 | ERCOT only: `campd_bins.py::load_campd_bins` → `capacity_mw = Nameplate_MW` from the hand CSV (L1563, L1644); `_reconcile_cc_capacity` L1243 lifts/caps to the demonstrated peak | EIA-860 reaches ERCOT's fleet only through the COD map, the CHP flag and the per-plant summer ratios. Jack Fusco 55357 (676 MW) was absent from the CSV until 2026-09-27. | ERCOT (`use_campd_bins`; `CAMPD_BINNING_ISOS`, `capacity_market.py:4869`) |
| 9 | Other 8 ISOs: `fleet_to_bins` → `assembly.py::bins_to_fleet` L164 | Generators binned per plant × class into tranches; `_commission_year` L349: registry (ERCOT-only file) → COD map (`commission_year_cod_fallback`, MISO only) → **literal 2010** (L357). `cc_capacity_reconcile` (per-plant CAMPD p99.9 cap/raise table) after any nameplate rescale. | plant_level_fleet ISOs |
| 10 | `data/fleet/arrays.py::_availability_matrix` L499 | availability = (1 − WEFOR·`wefor_multiplier`) × POF (dropped for CC/ST under `coal_drop_pof`, `_POF_DROP_GROUPS` L210) × age derate (`THERMAL_AVAILABILITY`, `fuel_trajectories.py:1079`) × seasonal shape (`SUMMER_WEFOR_SHARE=0.30` L1148 or `summer_wefor_share_override`) × flat `SUMMER_CLASS_DERATE` (CC 10 %, CT 12.5 %, L1174; suppressed per plant under `summer_derate_basis_aware`) or the per-plant `net_summer/nameplate` ratio under `cc_nameplate_summer_derate` (`scenarios.py:16708`; reconciled-basis variant `cc_summer_derate_reconciled_basis` L16760; published envelope `cc_winter_capability_basis` L17903, CAISO R / NYISO G) × CAMPD outage overlay × AS withholding (anchor branch L1270-1340). | per-ISO |
| 11 | `cod_ramp.generator_online_mask` L732 (via `effective_cod` L675, `bin_online_fraction` L544, `monthly_online_mask` L576), applied **last** in `generators_to_fleet_arrays` (`cod_ramp_enabled`, default on, `scenarios.py:5913`) | Raw unit: own `(Operating Year, Month)` wins (SOCO-15); plant-level bin: nameplate-weighted online fraction of its own constituents (`load_unit_cod_map` L440); retirement: own per-unit retirement if present, else the plant-collapsed **latest** (`_load_cod_map` L349). `COD_FALLBACK_MONTH=7`. `min_gen` zeroed in offline months. | all |
| 12 | LP: `col_upper = pmax × availability`, `min_gen` floor | Capacity reaches the LP as an 8760-vector per unit. Forecast capacity screens read `capacity_screen_peak_measured_hindcast` (`scenarios.py:22132`); a backcast runs no evolution. | all |

Forecast-only (not on the backcast path): `confirmed_exits_enabled` (`data/confirmed_retirements.py:105`), `fossil_announced_exits_enabled` (`data/announced_retirements.py:318`, owner-filed Schedule-3 dates, vintage-gated, verified against later vintages), `load_planned_additions`. `data/ownership.py::load_eia860_ownership` L185 feeds emissions attribution only — **no ownership share ever enters the LP**; a jointly-owned unit is whole in its plant's BA, which is also how EIA-923/930 count it. `data/neiso_operable_capacity.py::neiso_thermal_availability_series` L73 (ISO-NE Morning Report fleet availability) is built, default off, in no keeper. `data/wecc_west_fleet.py` = CAISO endogenous WECC node, default off.

### A.2 Capacity basis by class, as the keepers carry it

| Class | Plant-level ISOs (8) | ERCOT |
|---|---|---|
| CC_REGULAR / CC_CHP | pmax = net summer year-round unless `cc_nameplate_summer_derate` (then nameplate with a Jun-Sep ratio): **PJM, NYISO, NEISO, CAISO = nameplate basis; MISO, SPP, NWPP, SOCO = net-summer basis** + flat 10 % Jun-Sep derate (double count unless `summer_derate_basis_aware`: MISO, SOCO) | bin nameplate (CSV) + per-plant ratio |
| CT_PEAKER / CT_CHP | net summer year-round + flat 12.5 % Jun-Sep (double count; `summer_derate_basis_aware` fixes MISO/SOCO only) | bin nameplate + 12.5 % |
| COAL_* | net summer year-round (no class derate); `coal_nameplate_summer_derate` = ERCOT only | bin nameplate + measured ceiling |
| ST_GAS / oil / nuclear / biomass | net summer year-round | bin nameplate |

Five flags (`cc_nameplate_summer_derate`, `summer_derate_basis_aware`, `cc_summer_derate_reconciled_basis`, `cc_winter_capability_basis`, `coal_nameplate_summer_derate`) answer the one question "which published rating is the LP bound in which month", and no two keepers answer it the same way. Measured size of the question (§C): net winter exceeds net summer by 3-9 % (NYISO/NEISO 8-9 %), nameplate exceeds net summer by 9-17 % — exactly the size of the flat class derate that six keepers re-apply on a net-summer basis.

### A.3 Per-keeper posture (read from `results/calibration/<bundle>/run_config.json` → `scenario_config`)

| flag | ERCOT `r_ercot23_span` | CAISO `rcaiso20_A_*` | PJM `pjmnext16_A_span` | MISO `miso280_span` | NYISO `nyisonext21_*` | NEISO `neiso119_span` | SPP `spp100_arm_span` | NWPP `nwppnext16c_span` | SOCO `soco96_span` |
|---|---|---|---|---|---|---|---|---|---|
| years in bundle | 2019-25 | 2022-25 + tp 2019-21 | 2019-25 | 2019-25 | 2021 + 2022-25 | 2019-25 | 2019-25 | 2019-25 | 2019-25 |
| `eia860_vintage_tracks_solve_year` | T | T | T | T | T | T | T | T | T |
| `plant_level_fleet` | F (CSV bins) | T | T | T | T | T | T | T | T |
| `cc_nameplate_summer_derate` | F | T | T | F | T | T | F | F | F |
| `summer_derate_basis_aware` | F | F | F | T | F | F | F | F | T |
| `cc_summer_derate_reconciled_basis` | F | F | F | F | T | F | F | F | F |
| `cc_capacity_reconcile` | F (bins' own table) | F | T | T | T | F | F | F | F |
| `cc_block_summer_rating` | F | F | F | T | F | F | F | F | F |
| `cc_steam_part_capacity` / `_reclass` | F/F | F/F | F/F | T/F | F/F | F/T | F/F | F/F | F/F |
| `commission_year_cod_fallback` | F | F | F | T | F | F | F | F | F |
| `admit_standby_units` | F | F | F | F | F | F | F | T | F |
| `retiree_vintage_status_scope` | F | F | F | T | T | F | F | F | F |
| `partial_plant_exit_carry` | T | F | F | T | F | T | F | T | F |
| `mid_vintage_exit_carry` | F | F | T | T | T | T | T | T | F |
| `carry_operating_mothballs` | F | F | F | T | F | F | F | F | F |
| `fleet_zone_vintage_coords` | F | F | T | F | T | F | F | F | F |
| `benchmark_membership_vintage_union` | F | F | T | F | F | F | F | F | F |
| `campd_per_unit_vintage_denominator` / `unit_outage_exit_ym_from_eia860` | F/F | F/F | F/F | F/F | F/F | F/F | F/F | T/T | F/F |
| `unit_outage_precod_clip` | F | F | F | F | F | F | F | F | T |
| `coal_nameplate_summer_derate` | T | F | F | F | F | F | F | F | F |
| `wefor_multiplier` / `wefor_residual` | 0.7 / 0.02 | 1.0 / 0.0 | 0.7 / 0.015 | 1.0 / 0.0 | 0.7 / – | 0.7 / – | 0.7 / – | 0.7 / – | 0.7 / – |

`iso_configs.py` `default_scenario_overrides` carries **none** of these (zero hits in any `_<iso>_config`); every posture lives only in the keeper recipe. The mechanism-matrix cells (`docs/codebase-site/data/mechanism-matrix/<ISO>.js`) agree: `commission_year_cod_fallback` K only MISO, U ×8; `retiree_vintage_status_scope` K MISO/NYISO, U ×7; `cc_block_summer_rating` K MISO, U ×8; `admit_standby_units` K NWPP, U ×8; `cc_winter_capability_basis` R CAISO / G NYISO / U ×7; `cc_capacity_reconcile` K PJM/MISO/NYISO, R CAISO, U ×5; `cc_steam_part_capacity` K MISO, I NEISO, `.` ERCOT/PJM/NYISO, U ×4.

---

## B. Every recorded 860 / vintage / COD / capacity defect and repair (June → October 2026)

| date | ISO | defect (plants, MW) | repair | status across ISOs | regression test |
|---|---|---|---|---|---|
| 2026-06-17 | all | two overlapping COD implementations (year-prorate `ramp_bins` vs month mask) | unified `cod_ramp_enabled` (`docs/cod-vintage-ramp.md` "Reconciliation note") | all | `tests/unit/data/test_cod_ramp.py` (72) |
| 2026-06-30 | 6 ISOs | CC at net summer year-round: 87 plants / 3,569 MW winter understated; CAMPD facility ≠ EIA plant at 40 plants / 8,360 MW (Elwood 55199, Indian River 594, Astoria 55375, Channelview 55187, Linden 50006) | `cc_nameplate_summer_derate` recommended for CAISO/MISO (`docs/capacity-audit-860-923-campd.md`) | CAISO armed; **MISO/SPP/NWPP/SOCO still net-summer** | `test_fleet.py::test_summer_derate_applies_only_in_summer` |
| 2026-07 | PJM | CC component/total double-filing (Keys 60302, Camden 10751) | always-on `_reconcile_cc_pmax_to_nameplate` + per-ISO `cc_capacity_reconcile` tables (`docs/records/pjm/pjm-cc-capacity-reconcile-2026-07.md`, `docs/cc-capacity-reconcile-unification-2026-07.md`) | guard everywhere; tables for 6 ISOs | `test_fleet.py::test_total_on_one_row_clamped_to_nameplate`, `::test_demonstrated_peak_above_nameplate_wins` |
| 2026-07-15 / 08-06 | NYISO, MISO, all | ER retired sheet prunes older retirements: Indian Point 3 (8907), Palisades (1715); 106 of 442 2021-22 retirees absent | `build_capacity_actuals.py` reads the whole release series; `_validation-source/retired_sheet_coverage_gaps.csv` (README RD-5 / FFR-7A) | forecast scoring only; **§C measures the pruning: PJM 2019 retirements 7,579 MW (vintage sheet) vs 2,108 MW (2025ER)** | `tests/scoring/test_capacity_hindcast_scoring.py` |
| 2026-07-16 | MISO | Cottonwood 55358: 4 of 8 units OA in 2025ER, OP in 2023/2024 vintages; 576 MW running 88-91 % of 2023 hours | `carry_operating_mothballs` (`docs/records/miso/miso-cc-vintage-undercarry-plan-2026-07.md`) | MISO only (superseded in effect by year-matched vintages) | `test_mothballed_but_operating.py` (10) |
| 2026-07-31 | NEISO | Kendall 1595 CAMPD 278-299 MW vs EIA 213 MW | ARTIFACT (CAMPD grossLoad embeds district steam) — no change (`FINDING-neiso73`) | adjudicated | — |
| 2026-08-04 | MISO | CC steam parts dropped because the `CA` row's `Energy Source 1` is the duct fuel: 290.4 MW (55088, 50973) | `cc_steam_part_capacity` (`FINDING-miso126`) | **MISO only** by `CC_STEAM_PART_REPAIR_ISOS`; CAISO/SPP/NWPP/SOCO U | `test_cc_steam_part_capacity.py` (18) |
| 2026-08-04 | NEISO | Stony Brook 6081 CA1 96 MW carried as `oil` | `cc_steam_part_reclass` (`FINDING-neiso80`) | **NEISO only** | `test_cc_steam_part_reclass.py` |
| 2026-08-07/09 | MISO | flat 10/12.5 % summer derate re-applied on a net-summer pmax: 5,933 / 5,853 / 5,686 MW summer capability removed (2023/24/25) | `summer_derate_basis_aware` (`FINDING-miso141`, `miso148`) | MISO, SOCO K; **PJM/SPP/NWPP/NEISO/NYISO/CAISO still double-count CT** | `test_summer_availability_constants.py` |
| 2026-08-09 | CAISO | outage-derate denominator on the wrong capacity basis (4.5-7.0 % of envelope) | `unit_outage_lp_capacity_basis` (`FINDING-caiso184`) | CAISO K | `test_unit_outage_*basis*.py` |
| 2026-08-14/15 | MISO (all non-ERCOT) | `_commission_year` literal 2010 for every non-ERCOT plant: 108.7 GW at one vintage; registry hit 0 % outside ERCOT | `commission_year_cod_fallback` (`FINDING-miso159`; `results/phase0/miso/_miso158_vintage_census.json`) | **MISO only**; 7 ISOs still price the age derate off 2010 | `test_summer_availability_constants.py` |
| 2026-08-15 | CAISO | El Segundo CEMS ORIS 330 → EIA 57901 (3.2 TWh/yr phantom) | `CAMPD_UNIT_PLANT_REMAP` entry (`FINDING-caiso196`) | hand rows: CAISO 315/335/330, NYISO, SPP (Stall 56565 ← 1416), MISO (West Riverside 64020 ← 55641) | `test_outages.py` |
| 2026-08-30 | MISO | Grand Tower 862 dark since 2022, carried to its paper retirement | `retiree_vintage_status_scope` (`FINDING-miso188`) | MISO, NYISO K; U ×7 | `test_retiree_vintage_status_scope.py` (9) |
| 2026-08-30/31 | MISO | partial-plant mid-window exits in neither channel: Sherco-2 682 MW, SOC 5+6, A B Brown 1+2, Dan E Karn ×4, Petersburg-ST2, Teche-3 (7.68 TWh 2023) | `partial_plant_exit_carry` + binning-aware exit cohorts (miso-190/191) | MISO, ERCOT, NEISO, NWPP K; CAISO/PJM/NYISO/SPP/SOCO U | `test_partial_plant_exit_carry.py` (13) |
| 2026-09-06 | PJM | fleet frozen on 2025ER: coal 38.72 GW every year vs vintages 48.71 / 41.94 / 37.12 GW (2021-23); ST_GAS peak 117 % of what existed | `eia860_vintage_tracks_solve_year` (`FINDING-pjm167`; pjm-168 R reopened by the 09-24 audit) | default-on in backcast (F1); all keepers T | `test_eia860_vintage_tracking.py` (7), `test_f1_backcast_heat_rate_vintage_defaults.py` (17) |
| 2026-09-07 | NYISO | Cricket Valley 57185: summer ratio applied on a reconciled capacity → 470 MW Jun-Sep removed across 12 plants | `cc_summer_derate_reconciled_basis` (`FINDING-nyiso212`) | NYISO K; U elsewhere | `test_cc_summer_derate_reconciled_basis.py` |
| 2026-09-09 | PJM / all | `RETIREMENT_WINDOW_START` 2023→2019 claimed inert on 2023-25; PJM: 720 MW coal retired May 2020 dispatchable in 2023 | routed, not unilaterally repaired (`FINDING-pjm-retiree-window-redistribution`) | superseded by per-year vintages; residual for 2025 (no vintage) | `test_retiree_window_extension.py` (13) |
| 2026-09-09 | ERCOT | retiree window 2023-24 only: 35.8 MW (2021) / 510.2 MW (2022) TX retirements missing | window widened to 2019 (`FINDING-ercot260` §1) | all | same |
| 2026-09-13 | SPP | SWPP absent from `vintage_2018/2019/2021/2022` generator parquets (0 rows) — derive-time BA filter | `rescope_generator_table_from_parquet` (SPP-38; `FINDING-spp40`) | SPP; reused for SOCO AEC / FPL | `tests/curation/*` |
| 2026-09-13 | SOCO (all) | Vogtle 3/4 (649) online all of 2023 from the plant-mean COD (2005-05): +12.98 TWh phantom nuclear | per-unit COD wins in `effective_cod` (card S12; `docs/calibration-log/soco.md:397`) | all, no flag; spill: ERCOT 2023 price +2.34 $/MWh | `test_cod_ramp.py::test_brownfield_unit_prefers_own_online_date_over_plant_mean` |
| 2026-09-18/19 | SPP | plant retiring DURING its vintage year in neither sheet (vintage_2023/2024 have no retired sheet) | `mid_vintage_exit_carry` (SPP-48) | PJM/MISO/NYISO/NEISO/SPP/NWPP K; **ERCOT/CAISO/SOCO off** | `test_mid_vintage_exit_window_fallback.py` (3) |
| 2026-09-24 | all | AUDIT D1-D6: vintages carried no heat rate (95-100 % class table 2019-22); only SPP armed vintages; NWPP/SOCO zero retirees; vintage_2023/24 lacked the utility sheet | F1 (vintage-matched eGRID join, `--rejoin-heat-rate`, `--rescope-retired-window`, default flips) (`docs/records/governance/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md`) | all | `test_f1_backcast_heat_rate_vintage_defaults.py` |
| 2026-09-25 | NWPP (systemic) | SB units dropped by the OP filter while their EIA-923 is in the benchmark: Fredonia 607 + Sun Peak 54854, 598 MW, 0.25-1.0 TWh/yr; "PJM, SPP and MISO carry comparable generating SB gas" | `admit_standby_units` (`FINDING-nwppnext2-standby-census`) | NWPP K; MISO-284: a faithful arm cannot be built (Taconite Harbor 155 MW SB, 0 op-hours every year) | `test_admit_standby_units.py` (6) |
| 2026-09-25 | PJM | 3,824 / 3,561 / 2,900 MW mis-zoned 2019-21 (plants eGRID-2023 lacks) + benchmark membership drift | `fleet_zone_vintage_coords`, `benchmark_membership_vintage_union` (`RESULT-pjm-next-c1`) | PJM, NYISO K (zone); PJM, SPP K (union); others O/U | `test_benchmark_membership_vintage_union.py` |
| 2026-09-25 | MISO | Edwardsport 1004 IGCC: block summer 555 MW on the CA row + blank CTs nameplate-filled → 1,036 MW carried, 481 MW phantom | `cc_block_summer_rating` (non-NG blocks; `RESULT-miso272`) | MISO K; U ×8 (§C: 20-156 summer>nameplate rows per ISO-year remain unscreened) | `test_cc_block_summer_rating.py` (11) |
| 2026-09-25/28 | SOCO | Gulf Power plants coded SOCO in vintages 2019-23 but outside EIA-930 SOCO; PowerSouth joined 2021-09-01 | `ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE`, `ISO_BA_JOINS`, `ISO_BA_EXITS` (dated 2022-07-13 12:00) | SOCO K; registries empty elsewhere | `test_ba_membership.py` (13) |
| 2026-09-27 | ERCOT | Jack Fusco 55357 (676 MW CC) absent from the bin CSV; 22 of the 59 2023 hours > $1k formed by the missing MW | row added (`RESULT-r-ercot-8`); 2023 flipped CALIBRATED → NOT-YET | ERCOT | none (CSV content) |
| 2026-09-28 | ERCOT | W A Parish split 34702 on the wrong boundary (294 MW coal in the gas row; split child on the coal heat rate) | boundary + measured ST rates (`RESULT-r-ercot-11`) | ERCOT | none |
| 2026-09-28/29 | ERCOT | Frontera 55098 entered 2023-04-13; Oklaunion 127 left 2020-10-01 | `ISO_PLANT_ENTRIES` / `ISO_PLANT_EXITS` (`constants.py:2720, 2742`) | ERCOT | `test_ba_membership.py` |
| 2026-09-28 | SPP, MISO | CEMS→EIA split remaps (Stall ← Arsenal Hill; West Riverside ← Riverside) + companion re-derives | `CAMPD_UNIT_PLANT_REMAP`, `campd_split_remap_companions` | SPP, MISO K; `.` elsewhere | `test_outages.py` |
| 2026-09-29/30 | NWPP | Boardman 6106 membership window; Bridger/Naughton coal→gas conversions: per-unit rows divided by each year's own vintage nameplate (2023: COAL +1,324 MW ↔ ST_GAS −1,324 MW) | `unit_outage_membership_repair`, `campd_per_unit_vintage_denominator` (`results/phase0/nwpp/_nwpp51_vintage_census.json`) | NWPP | `test_unit_outage_*` |
| 2026-09-30 | ERCOT | simple-cycle GTs inside three CC plants carried as CC | GT split (R-ERCOT-20) | ERCOT | none |
| 2026-09-30 | PJM | OVEC outside the PJM BA code in 2019/2020 | `ISO_BA_JOINS["PJM"]={"OVEC": (2019,1)}` | PJM | `test_ba_membership.py::test_pjm_ovec_admitted_all_year_in_2019_and_2020` |

### B.1 The pattern — why it keeps coming back

1. **One snapshot, five patches.** The 2025ER snapshot can only *lose* units through the COD ramp; it can never add one it does not carry. Retired, mothballed (OA), partially retired, mid-vintage-retired and recoded-BA units each got an injection channel. Year-matched vintages (F1) make three of the five redundant, but the vintages are **incomplete** (`vintage_2023/2024` without retired sheets, no `vintage_2025`, no 860M), so the patches survive, armed in different subsets (§A.3).
2. **Filtering at derive time.** `eia860_generators.parquet` is a BA-filtered derivative; every program-scope change (SPP joins, PowerSouth → SOCO, OVEC → PJM) is a data repair instead of a load-time predicate. SPP-40, R-SOCO-B and PJM-NEXT-16 are one defect three times.
3. **Plant grain vs unit grain.** Eight ISOs bin per plant×class; ERCOT uses a plant-level hand CSV. Every unit-grain fact (brownfield COD, a single unit's retirement, a unit's status, a GT inside a CC plant, a boiler converted to gas) is lost at the bin and re-discovered as a phantom: Vogtle, Homer City, Sherco-2, Parish, Bridger, Fusco.
4. **EIA-860 row semantics never encoded once.** Summer blank → nameplate fill (§C: 3,924 MW of MISO thermal rows carry no summer rating every year); block rating on the CA row (20-156 summer>nameplate rows per ISO-year); `CA` rows with duct fuel; `Operating Month` only in the raw sheet. Each was found at one plant and gated to one ISO (rule 25), so eight ISOs' instances remain `U`.
5. **Facility-ID crosswalk by hand.** CAMPD ORIS vs EIA plant id splits are fixed one remap row at a time, although the official EPA crosswalk is on disk and PUDL's subplant crosswalk resolves exactly this.
6. **Status codes vs the benchmark population.** The fleet keeps `OP` only; the EIA-923 benchmark has no status filter (`_iso_plant_ids`; nwppnext2 verdict (1)). §C: SB alone is 1.6-2.5 GW in MISO and 1.5-2.2 GW in PJM every year; OA is 2.3-3.1 GW in NWPP.
7. **No single capacity basis** (§A.2): five flags, no two keepers alike; the net-summer-year-round basis plus a flat class derate is a known double count in six keepers; caiso-186 refused the published-envelope form on a WEFOR double-count ground, so the right answer has no home.
8. **No committed fleet census.** Keeper bundles carry no fleet file; `unit_marginal_<Y>.parquet` exists only in PJM's bundle (rule 15 asks for every ISO since 2026-10-01); `legitimacy_diagnostics` rebuilds a *different* fleet (caiso-291: 1,859 vs 1,705 rows). Nobody can diff "what the LP carried" against EIA-860 or an ISO report, so drift is found through price residuals one plant at a time.
9. **Rule 25 by design.** ISO-scoped verdicts mean a registry-read correctness repair is still re-tested nine times. Until a class of repairs is declared structural and default-on everywhere, recurrence is guaranteed.

---

## C. Zero-LP census (run in this session; `.venv/bin/python`, ~90 s; CSVs at `eia860_vintage_census_2019_2025.csv`, `eia860_retired_census_2019_2025.csv` beside this file)

Membership = the vintage plant sheet's BA code ∈ `ba_codes(iso)` (NWPP + NERC=WECC), vintage = `vintage_<Y>/` for 2019-2024 and the 2025ER top level for 2025, "thermal" = prime movers CA/CT/CS/GT/ST/IC/CC. Nameplate / `Summer Capacity (MW)` / `Winter Capacity (MW)` are the raw sheet fields the loader reads (step 5).

**C.1 Thermal OP capacity by basis (MW) — the three numbers the LP could carry**

| ISO | 2019 S / W / NP | 2021 S / W / NP | 2023 S / W / NP | 2025ER S / W / NP | W/S−1 | NP/S−1 |
|---|---|---|---|---|---|---|
| ERCOT | 76,233 / 80,087 / 84,411 | 77,246 / 81,268 / 85,170 | 78,652 / 82,723 / 86,936 | 77,820 / 82,157 / 86,221 | 5-6 % | 10-11 % |
| CAISO | 33,550 / 34,516 / 37,359 | 35,053 / 36,144 / 38,948 | 34,354 / 35,278 / 38,256 | 34,110 / 35,095 / 37,927 | 3 % | 11 % |
| PJM | 174,985 / 183,662 / 192,316 | 176,518 / 185,545 / 193,473 | 170,912 / 179,922 / 186,265 | 170,269 / 178,847 / 185,543 | 5 % | 9-10 % |
| MISO | 142,675 / 147,256 / 160,398 | 140,493 / 146,452 / 157,530 | 134,581 / 141,419 / 151,774 | 131,969 / 138,754 / 148,190 | 3-5 % | 12-13 % |
| NYISO | 32,603 / 34,990 / 35,516 | 30,788 / 33,396 / 33,728 | 30,220 / 32,647 / 33,013 | 29,795 / 32,065 / 32,657 | 7-9 % | 9-10 % |
| NEISO | 28,452 / 30,740 / 31,587 | 26,982 / 29,251 / 30,038 | 26,156 / 28,260 / 29,247 | 23,968 / 25,883 / 26,697 | 7-9 % | 11-12 % |
| SPP | 56,617 / 56,594 / 63,090 | 55,660 / 54,741 / 61,496 | 55,158 / 55,609 / 61,150 | 55,861 / 57,649 / 61,709 | −2…+3 % | 7-11 % |
| NWPP | 30,497 / 31,930 / 35,575 | 29,072 / 30,407 / 34,085 | 29,391 / 30,668 / 33,098 | 29,823 / 31,087 / 33,664 | 4-5 % | 13-17 % |
| SOCO | 54,917 / 57,739 / 60,213 | 56,079 / 58,728 / 61,157 | 56,790 / 59,678 / 61,673 | 55,117 / 58,039 / 59,756 | 5 % | 8-10 % |

Reading: the four net-summer-basis keepers (MISO, SPP, NWPP, SOCO) carry Oct-May thermal capacity 3-5 % (MISO ≈ 6.8 GW in 2023) below the published winter rating, and six keepers re-apply a 10-12.5 % class derate on CT/CC rows whose summer rating already embeds a 9-17 % loss. ERCOT's CSV nameplate basis (86.9 GW-equivalent) sits 10.5 % above the published summer rating before its per-plant ratios.

**C.2 Status census (nameplate MW, all prime movers) — what the `OP` filter drops**

| ISO | SB 2019 → 2025 | OA 2019 → 2025 | OS 2019 → 2025 |
|---|---|---|---|
| ERCOT | 104 → 90 | 13 → 553 | 975 → 2,201 |
| CAISO | 367 → 389 | 774 → 703 (1,508 in 2024) | 1,681 → 730 |
| PJM | 2,234 → 1,520 | 580 → 414 | 263 → 765 (1,548 in 2024) |
| MISO | 1,964 → 1,577 (2,458 in 2021) | 409 → 1,636 | 2,158 → 1,507 |
| NYISO | 273 → 386 | 36 → 262 (632 in 2024) | 1,505 → 886 |
| NEISO | 357 → 164 | 12 → 10 (677 in 2023) | 121 → 1,266 |
| SPP | 912 → 684 | 187 → 61 | 473 → 139 |
| NWPP | 714 → 759 | 2,893 → 2,827 | 816 → 992 |
| SOCO | 184 → 149 | 0 → 1 | 28 → 54 |

SB admission (E.4) is a 1.5-2.5 GW question in PJM and MISO, 0.7-0.9 GW in SPP/NWPP, < 0.4 GW elsewhere. NWPP's 2.3-3.1 GW of OA is the largest status envelope anywhere and is adjudicated by nothing today (`carry_operating_mothballs` is MISO-only and the per-year vintage already encodes the year's own OA).

**C.3 Row-semantics defects per vintage (thermal OP rows)**

| ISO | blank summer rating → nameplate-filled (MW, 2019 / 2023 / 2025) | rows with summer > nameplate (2019 / 2023 / 2025) |
|---|---|---|
| ERCOT | 0 / 0 / 0 | 28 / 26 / 26 |
| CAISO | 0 / 0 / 0 | 36 / 38 / 36 |
| PJM | 484 / 746 / 746 | 76 / 94 / 100 |
| MISO | 3,924 / 3,932 / 3,931 | 156 / 144 / 136 |
| NYISO | 304 / 492 / 552 | 31 / 33 / 26 |
| NEISO | 544 / 514 / 514 | 26 / 25 / 20 |
| SPP | 796 / 883 / 883 | 44 / 41 / 39 |
| NWPP | 0 / 0 / 0 | 8 / 14 / 20 |
| SOCO | 1,772 / 1,772 / 1,366 | 48 / 58 / 53 |

The blank-summer rows are the population the Edwardsport block fill came from; the summer>nameplate rows are the block-on-one-row candidates. `cc_block_summer_rating` screens only MISO, and only non-NG blocks. Every other ISO-year has an unscreened population here (CT-only CC filers, cold-weather over-ratings, and genuine block-on-one-row filings are mixed in — the ledger must classify them).

**C.4 In-year CODs and retirements (vintage of the year)**

| ISO | OP units with Operating Year == Y (2019 … 2025) | nameplate MW of those (2019 … 2025, all PMs) | retired-sheet MW with Retirement Year == Y (2019 / 2020 / 2021 / 2022; 2023-24 no sheet; 2025ER) |
|---|---|---|---|
| ERCOT | 30 / 76 / 206 / 89 / 112 / 131 / 140 | 4,168 / 4,897 / 10,076 / 8,725 / 7,436 / 13,903 / 15,279 | 983 / 423 / 187 / 471 ; – ; 2 |
| CAISO | 58 / 72 / 111 / 91 / 78 / 130 / 120 | 1,225 / 3,614 / 3,496 / 4,609 / 5,706 / 6,514 / 6,198 | 1,791 / 1,143 / 445 / 62 ; – ; 316 |
| PJM | 89 / 109 / 132 / 73 / 138 / 142 / 143 | 3,954 / 3,206 / 5,010 / 3,629 / 7,886 / 4,036 / 3,304 | 7,579 / 3,659 / 1,498 / 6,734 ; – ; 671 |
| MISO | 177 / 215 / 155 / 103 / 115 / 130 / 181 | 4,363 / 7,545 / 5,640 / 4,074 / 4,871 / 7,083 / 10,160 | 4,264 / 3,314 / 3,791 / 4,670 ; – ; 460 |
| NYISO | 60 / 64 / 50 / 64 / 62 / 127 / 98 | 210 / 1,485 / 392 / 322 / 874 / 1,022 / 440 | 392 / 2,126 / 1,022 / 623 ; – ; 28 |
| NEISO | 77 / 76 / 136 / 76 / 79 / 99 / 50 | 1,415 / 362 / 660 / 343 / 358 / 515 / 795 | 746 / 40 / 1,358 / 292 ; – ; 359 |
| SPP | 17 / 28 / 34 / 22 / 23 / 20 / 48 | 1,872 / 3,742 / 3,905 / 3,228 / 2,064 / 1,144 / 3,907 | 364 / 1,838 / 13 / 295 ; – ; 28 |
| NWPP | 21 / 63 / 29 / 43 / 28 / 76 / 50 | 696 / 2,261 / 1,670 / 1,517 / 1,694 / 4,488 / 3,471 | 218 / 2,168 / 23 / 23 ; – ; 66 |
| SOCO | 21 / 33 / 17 / 11 / 31 / 11 / 2 | 749 / 806 / 2,031 / 671 / 3,331 / 1,974 / 340 | 2,440 / 0 / 17 / 2,864 ; – ; 137 |

`Planned Retirement Year == Y` on the operable sheet is **0 MW in every ISO-year** — in a year-matched vintage a unit retiring in Y is already on the retired sheet, so `Planned Retirement` never matters for a backcast (E.5). Month-grain in-year CODs are large (ERCOT 7-15 GW/yr, MISO 4-10 GW/yr) — the month mask is load-bearing, not cosmetic.

**C.5 The 2025ER retired sheet is pruned — sized**

| retirement year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| PJM: vintage sheet → 2025ER | 7,579 → 2,108 | 3,659 → 1,992 | 1,498 → 1,090 | 6,734 → 2,997 | ? → 5,120 | ? → 1,322 |
| MISO | 4,264 → 3,678 | 3,314 → 2,195 | 3,791 → 3,682 | 4,670 → 3,181 | ? → 3,628 | ? → 3,587 |
| ERCOT | 983 → 397 | 423 → 322 | 187 → 37 | 471 → 406 | ? → 1,016 | ? → 79 |
| CAISO | 1,791 → 1,285 | 1,143 → 242 | 445 → 264 | 62 → 17 | ? → 115 | ? → 186 |
| NYISO | 392 → 29 | 2,126 → 117 | 1,022 → 312 | 623 → 34 | ? → 75 | ? → 33 |
| NEISO | 746 → 12 | 40 → 67 | 1,358 → 455 | 292 → 17 | ? → 22 | ? → 103 |
| SPP | 364 → 133 | 1,838 → 1,223 | 13 → 12 | 295 → 299 | ? → 894 | ? → 1,012 |
| NWPP | 218 → 221 | 2,168 → 2,122 | 23 → 5 | 23 → 59 | ? → 155 | ? → 188 |
| SOCO | 2,440 → 2,343 | 0 → 538 | 17 → 3 | 2,864 → 2,864 | ? → 264 | ? → 13 |

The only retired-sheet record on disk for 2023 and 2024 retirements is the pruned ER (`?`). That is the hard gap: `mid_vintage_exit_carry` is reconstructing 2023/2024 in-year exits from an ER that the 2019-2022 columns prove to be 30-95 % incomplete. The Final 2023/2024/2025 zips (§F 1) close it with no code.

**C.6 Model-side census — what exists today.** Only PJM's keeper carries `hourly/unit_marginal_<Y>.parquet` (columns `unit_id, plant_code, plant_group, fuel, zone, hour, mw, cap_mw, mc, marginal`). Σ max-hour `cap_mw` per unit, PJM 2023: CC_REGULAR 59,281 + CC_CHP 1,502 + COAL 37,328 + CT 23,110 + ST 10,054 + unlabeled (nuclear/oil/biomass) 41,268 + hydro 2,769 = **175,310 MW**, vs EIA-860 vintage_2023 PJM thermal OP summer 170,912 / winter 179,922 / nameplate 186,265 — i.e. the PJM keeper sits ~1 % above the summer rating (nameplate basis on CC, summer on the rest), 2.6 % below winter. That is the first row of the E.7 ledger; no other ISO can produce one until its bundle carries the slim layer (rule 15 preflight).

**C.7 External sanity — EIA-930 peak hourly demand (MW, sum of member BAs; `data/raw/eia-930-hourly/`)**: ERCOT 75,610 / 75,646 / 76,783 / 81,476 / 86,895 / 87,055 / 85,282 (2019-25); PJM 150,903 … 157,644; MISO 125,217 … 124,970; CAISO 44,286 … 44,367 (50,485 in 2020 and 51,317 in 2022 look like raw-series artifacts); NYISO 29,871 … 30,398; NEISO 24,530 … 25,800; SPP 52,368 … 58,277; SOCO 44,030 … 45,913; **NWPP 68,649 / 68,742 (2019-20) then 49,954 … 49,932 (2021-25)** — a series discontinuity in the pool's EIA-930 demand, outside this shard's scope but worth a NWPP lane's attention. Thermal summer capacity / peak: ERCOT 0.90, PJM 1.12, MISO 1.05, CAISO 0.75, NYISO 1.04, NEISO 1.11, SPP 0.95, SOCO 1.25 (2023) — no ISO's 860 thermal set is implausible against its own peak once hydro/VRE/imports are added.

**ERCOT CDR:** only 12 derived planned-addition rows (Dec-2025 "Seasonal Summary") are on disk (`data/raw/benchmark-corridor/ercot-cdr-2025/`); an installed-capacity reconciliation needs the CDR xlsx unit lists (§F 6).

---

## D. External best practice

| Topic | Primary source says | Implication |
|---|---|---|
| EIA-860 cadence | Early Release (June) then Final (Sept). **"Release Date: September 10, 2026, Final 2025 data"; "Next … June 2027, Early release 2026 data"**; zips `eia8602016.zip … eia8602025.zip` ([eia.gov/eia860](https://www.eia.gov/electricity/data/eia860/)) | Final 2025 exists; the repo's 2025 is the ER. |
| EIA-860M | Latest **August 2026**, released 2026-09-24, next 2026-10-23; `<month>_generator<year>.xlsx`; "capacities … are best estimates … not … capacity commitments"; "Estimates will be corrected without … explanation in subsequent month's inventory" ([eia.gov/eia860m](https://www.eia.gov/electricity/data/eia860m/)) | Right source for months after the latest Final in a forecast base year and for in-year COD/retirement confirmation; **not** a capacity basis of record. |
| Status codes | OP = in service; **SB = "available for service but not normally used"**; OA = out of service, returns next calendar year; OS = out of service, not expected back (Form EIA-860 instructions, [reginfo.gov](https://www.reginfo.gov/public/do/DownloadDocument?objectID=126696301)) | SB is physically available → admit by status; OA = the Cottonwood case (the contemporaneous vintage says OP); OS = out. |
| Operating Month/Year | "month/year of initial commercial operation"; `99`/`88` = unknown month; retired sheet carries actual `Retirement Month/Year`, operable sheet `Planned Retirement` (instructions, as above) | Loader already prefers the retired sheet's actual date; `_to_month` must treat 88/99 as unknown (E.8 test). |
| Net summer vs nameplate | Net summer = max output demonstrated by multi-hour test at summer peak (Jun 1-Sep 30), net of station service ([EIA glossary](https://www.eia.gov/tools/glossary/index.php?id=net+summer+capacity)); nameplate = manufacturer rating | EIA's capacity of record is net summer; net winter is the published off-summer capability. A year-round net-summer bound understates Oct-May by the §C.1 W/S gap; nameplate overstates station service. |
| NREL ReEDS | "The existing fleet … is taken from the NEMS unit database from AEO 2023, … supplemented from the March 2024 EIA 860M"; uses **net summer and net winter capacity**, heat rate, VOM, FOM per unit; 860M capacities "often retroactively fixed and … not … as reliable as those in the annual form" ([ReEDS docs, NREL 93617](https://docs.nrel.gov/docs/fy26osti/93617.pdf); [ReEDS-2.0 sources](https://github.com/NatLabRockies/ReEDS-2.0/blob/main/sources_documentation.md)) | Industry practice = seasonal pair at unit grain; 860M as supplement only. |
| EPA NEEDS | **"NEEDS for EPA 2025 Reference Case: rev 11-28-2025"** (`needs-for-2025-reference-case.xlsx`, 5.64 MB); unit records used to build IPM model plants, with on-line year, planned retirement, CAMD crosswalk, heat rate, controls (Chapter 4) ([epa.gov NEEDS](https://www.epa.gov/power-sector-modeling/national-electric-energy-data-system-needs)) | Free, curated, unit-level, EPA-maintained ORIS↔EIA mapping — the natural independent cross-check for every ISO and for the CEMS↔EIA crosswalk. |
| PUDL | EIA-860 2001-2025; quarterly 860M merged with `data_maturity = monthly_update`; `core_eia860__scd_generators` (slowly-changing dimension by `report_date`), `core_eia860__scd_plants`, `core_eia860__scd_ownership`, `core_epa__assn_eia_epacamd`, `core_epa__assn_eia_epacamd_subplant_ids`; Zenodo 10.5281/zenodo.4127026; viewer data.catalyst.coop ([docs](https://docs.catalyst.coop/pudl/en/latest/data_sources/eia860.html); [subplant table](https://data.catalyst.coop/preview/pudl/core_epa__assn_eia_epacamd_subplant_ids)) | The SCD table is "every vintage, one row per unit-year" — the cleanest view of a unit whose Operating Year or rating changes across vintages. The subplant crosswalk is the crosswalk of record for CAMPD facility splits. |
| ISO reports | ERCOT CDR xlsx (May/Dec; unit lists + "Seasonal Summary") ([ercot.com/gridinfo/resource](https://www.ercot.com/gridinfo/resource)); CAISO annual NQC list ([caiso notice](https://www.caiso.com/notices/2025-net-qualifying-capacity-values-for-resource-adequacy-resources-posted)); SPP Resource Adequacy Report ([2025](https://www.spp.org/documents/74099/2025%20spp%20summer%20resource%20adequacy%20report.pdf)); WECC WARA / Loads & Resources ([wecc.org](https://www.wecc.org/program-areas/reliability-planning-performance-analysis/reliability-assessments)); NYISO Gold Book ([nyiso.com/planning](https://www.nyiso.com/planning)); ISO-NE CELT ([iso-ne.com](https://www.iso-ne.com/)); PJM IMM SOM §12 "installed capacity 198,841.1 MW at 2024-12-31" ([SOM 2024 §12](https://www.monitoringanalytics.com/reports/PJM_State_of_the_Market/2024/2024-som-pjm-sec12.pdf)); MISO PRA results ([misoenergy.org](https://www.misoenergy.org/)) | Each publishes installed capacity on its own footprint and basis (ICAP/UCAP/NQC/SCC/DMNC). The ledger (E.7) states the basis translation, never mixes silently. |

**Cross-check of record per ISO (free; unit-level where it exists):** ERCOT → CDR unit lists (seasonal MW) + NEEDS; PJM → IMM SOM §12 + PJM existing-generation list + NEEDS; MISO → PRA results + OMS-MISO survey + NEEDS (unit grain); NYISO → Gold Book Table III-2 (per unit, summer/winter DMNC, in-service date); NEISO → CELT Section 2 (per unit, summer/winter SCC, COD); CAISO → NQC list (per resource, monthly; NQC/NDC ≈ 0.9595 for gas per the 2026 SLRA); SPP → RA Report (accredited by fuel) + NEEDS; NWPP → WECC L&R / WARA resource list + NEEDS; SOCO → FERC-714 + Southern Company IRP + NEEDS (the only unit-level independent list).

---

## E. The settlement specification — "860 is settled" means all nine hold

**E.1 Capacity basis (one rule, every class, every ISO).** The LP bound for a thermal unit in month m is the **published seasonal capability of the solved year's own vintage**: `Summer Capacity (MW)` in Jun-Sep, `Winter Capacity (MW)` in Oct-May (EIA definitions, §D), nameplate only where both are blank (§C.3 names the population), and never above `max(nameplate, CAMPD p99.9)` for CC with a complete CEMS record (the existing guard). The flat `SUMMER_CLASS_DERATE` is deleted for plant-level fleets (it is the nameplate→summer loss the rating embeds, miso-141; §C.1 sizes it at 9-17 %); ERCOT's bins carry `Nameplate_MW × (season rating / nameplate)` from the same vintage. This collapses the five basis flags into one default-on construction (rule 19). caiso-186's G-NOCONTRA objection (WEFOR double count on nameplate headroom) is answered in the same change: WEFOR/POF apply to the seasonal rating, the measured overlay replaces them where it covers, and `wefor_residual` is re-identified once on that basis — **owner ruling Q1**.

**E.2 Vintage rule.** Solved year Y reads the **Final** EIA-860 release for Y (`vintage_Y/`, full sheet set incl. retired-and-canceled and utility). 2025 reads `vintage_2025/` built from `eia8602025.zip` (Final, 2026-09-10). The top-level directory is the latest Final and serves forecasts only; 860M (latest month) is layered on it in the forecast base year, tagged `monthly_update`, never in a backcast. When a unit's `Operating Year` or rating differs between vintages, the solved year's own vintage wins; the diff is written to a committed `data/raw/eia-860/vintage_diffs/<Y>_<Y+1>.csv` so the change is visible.

**E.3 Unit grain.** The fleet record of truth is one row per EIA generator in the vintage. A CC block = all `OP` rows sharing `(Plant Code, Unit Code)`; a `CA` row is a steam part iff it has an NG `CT` sibling under the same Unit Code not younger than it (the miso-126 predicate) — everywhere, not `{MISO}`; a block rated on one row is reallocated by nameplate (miso-272) everywhere, NG blocks included where no demonstrated peak exists (SPP/NWPP/SOCO have no reconcile table). Bins keep plant×class grain, but every per-unit fact (COD month, retirement month, status, fuel conversion) flows through `load_unit_cod_map`/`bin_online_fraction` and the exit cohorts; `unit_marginal_<Y>.parquet` is the committed record of what each tranche carried. **Crosswalk of record** for CAMPD↔EIA = EPA CAMD-EIA crosswalk + PUDL subplant ids; `CAMPD_UNIT_PLANT_REMAP` keeps only rows the crosswalk gets wrong, each citing the crosswalk row it overrides. ERCOT's `custom-bin-assignments.csv` gains a per-year audit against `vintage_Y` (units in the vintage's ERCO footprint absent from the CSV and vice-versa), committed with each keeper.

**E.4 Status rule.** Admit `OP` and `SB` in every ISO (SB = available by EIA's definition; zero DOF; forward-regenerable). `OA`/`OS` are out **in the vintage that says so** — with per-year vintages the contemporaneous status is the oracle, so `carry_operating_mothballs` and `retiree_vintage_status_scope` become default behaviour and lose their flags. The EIA-923 benchmark applies the **same** status set (`_iso_plant_ids` gains the filter, or the fleet admits what the benchmark counts — one population). MISO-284's zero-conduct SB units (Taconite Harbor) are reported, not fitted: admitted, and the LP decides.

**E.5 Retirement rule.** Backcast: a unit is online through its **actual** `Retirement Month/Year` from the retired-and-canceled sheet of the first vintage that lists it (requires retired sheets in `vintage_2023/2024/2025` — §C.5 shows the ER is 30-95 % incomplete); `Planned Retirement` is never read in a backcast (§C.4: 0 MW ever binds). A unit whose `Status` history reads `OS` before its paper date exits at physical cessation (`build_capacity_actuals.physical_exit_year`, adopted for the LP fleet). Mid-year = month-precise mask; unknown month = `COD_FALLBACK_MONTH`. Forecast: step 0/1 as today.

**E.6 Ownership / BA membership.** Membership = the vintage plant sheet's `Balancing Authority Code` (NWPP plus NERC=WECC) applied at **load time**, never at derive time (`eia860_generators.parquet` stops being BA-filtered; `build_generator_table` keeps every BA). Dated joins/exits/entries stay in the four constants registries, each with an hour and a citation. Ownership shares never split a unit: whole in its BA for the LP, EIA-923 and EIA-930 alike (document in `docs/us-gen-ownership.md`).

**E.7 Reconciliation ledger** — per ISO-year, committed in the keeper bundle as `fleet_census_<Y>.json`, produced by one script `scripts/build_fleet_census.py` (the §C code generalized), checked by `audit_keepers.py` (new E-check) and refused by `promote_keeper.py` preflight when absent. Columns: class | EIA-860 vintage OP+SB nameplate | summer | winter | model Σpmax (from `unit_marginal`) | model peak-month available MW | ISO report capacity (basis named) | Δ model−860 | Δ model−ISO | explained residual rows (plant, MW, reason: CT-only CEMS, crosswalk, guard clip, status, blank summer). Tolerance: |Δ model−860 season rating| ≤ 1 % per class and ≤ 0.5 % total thermal (anything larger is a named plant row); |Δ model−ISO report| ≤ 3 % total after the stated basis translation. Sign-off: the lane produces it in phase 0 (zero LP); the owner signs it on the promotion card.

**E.8 Regression tests to add (trivial cases; behaviour, never digests).**
- `tests/unit/data/test_capacity_basis_seasonal.py`: one CC unit (nameplate 100, summer 90, winter 100) → pmax 90 in Jun-Sep, 100 in Oct-May, no flat class derate; blank winter → summer; blank both → nameplate; summer > nameplate → block reallocation.
- `tests/unit/data/test_vintage_selection_2025_final.py`: solve 2025 resolves `vintage_2025/` when present else the canonical; forecast never reads a vintage; 860M layer only in forecast.
- `tests/unit/data/test_cc_block_rules_all_isos.py`: the miso-126/272 predicates on a 3-row fixture give the same result for every ISO code.
- `tests/unit/data/test_status_admission_fleet_equals_benchmark.py`: a plant with one SB generator is in both the fleet and `_iso_plant_ids`; an OS-only plant in neither.
- `tests/unit/data/test_retirement_actual_vs_planned.py`: Planned 2024-12 + actual 2023-07 (retired sheet) masks out from Aug-2023; OS-before-paper exits at the OS vintage.
- `tests/unit/data/test_membership_load_time.py`: a generator parquet containing an unregistered BA still loads the registered ones; registering a BA needs no data regeneration.
- `tests/unit/scoring/test_fleet_census_ledger.py`: the census script on a 3-unit fixture reports Δ per class; `audit_keepers` fails a keeper missing `fleet_census_<Y>.json`.
- `tests/unit/data/test_eia860_month_sentinels.py`: Operating Month 88/99 → unknown → `COD_FALLBACK_MONTH`.

**E.9 Freeze rule (rule 23 form).** EIA-860 inputs re-derive only on (a) an EIA Final release (each Sept; an ER is never a vintage of record), (b) an 860M month in the forecast base year, (c) a crosswalk release (EPA/PUDL), (d) a program-scope change (BA/plant registry). The commit cites the release; `solve_surface.json` carries the sha256 of each `vintage_<Y>/` directory the bundle read, so a re-keyed keeper is attributed to the data change, never to a residual.

**Open 860 questions needing an OWNER RULING**

| # | Question | Recommendation |
|---|---|---|
| Q1 | One capacity basis (E.1: published seasonal pair, class derate deleted) across all 9 ISOs, re-keying every keeper? | **Yes**; one foundation lane; zero-LP census per ISO first (§C is the template), then one re-solve per ISO; caiso-186's WEFOR objection answered inside the lane. |
| Q2 | Admit `SB` fleet-wide (E.4) given MISO-284's zero-conduct SB units? | **Yes**, by status alone; report the envelope (§C.2), never select on 923 (rule 13). |
| Q3 | Download Final 2025 and re-process the 2023/2024 zips so every vintage has a retired sheet; make `vintage_2025/` the 2025 record (moves every ISO's 2025)? | **Yes** — retires `mid_vintage_exit_carry` and the ER caveat in one data change (§C.5 sizes the hole). |
| Q4 | Flip the registry-read correctness flags default-on in backcast everywhere (`commission_year_cod_fallback`, `retiree_vintage_status_scope`, `partial_plant_exit_carry`, `mid_vintage_exit_carry`, `fleet_zone_vintage_coords`, `benchmark_membership_vintage_union`, `cc_block_summer_rating`, steam-part predicates), with a per-ISO zero-LP census as the only gate? | **Yes**; zero DOF; the F1 pattern (default flip + `--no-…`, frozen cache-key drop value). |
| Q5 | ERCOT: keep the hand CSV with a per-year vintage audit (E.3), or migrate ERCOT to the vintage-driven per-unit path? | **Audit now, migrate later**: the CSV carries measured tranche shares the vintage path lacks; the audit catches the next Fusco. |
| Q6 | Load-time BA filtering (E.6) — regenerate `eia860_generators.parquet` unfiltered for every vintage? | **Yes**; one additive run, blob-verified. |
| Q7 | Crosswalk of record = EPA CAMD-EIA + PUDL subplant ids; hand remaps only as cited overrides? | **Yes**; intake `core_epa__assn_eia_epacamd_subplant_ids` once. |
| Q8 | E.7 tolerances (1 % class / 0.5 % total vs 860; 3 % vs ISO report) | Adopt; revisit only on a measured basis mismatch. |

---

## F. Free data download list for the owner

| # | What | URL / directions | Lands under |
|---|---|---|---|
| 1 | **EIA-860 Final 2025** (`eia8602025.zip`, 2026-09-10) + re-download `eia8602023.zip`, `eia8602024.zip` (to add the missing Retired-and-Canceled sheets) | https://www.eia.gov/electricity/data/eia860/ → ZIP column, 2023-2025. Then `python scripts/data/process_eia860.py --zip data/raw/eia-860/eia8602025.zip --out-dir data/raw/eia-860/vintage_2025` and `--retired-window-from` for the retiree parquet; re-run `--rejoin-heat-rate` (eGRID 2024 is the latest). | `data/raw/eia-860/vintage_2025/`; retired sheets into `vintage_2023/`, `vintage_2024/` |
| 2 | **EIA-860M latest** (`august_generator2026.xlsx`; next 2026-10-23) | https://www.eia.gov/electricity/data/eia860m/ (archive months 2015+) | `data/raw/eia-860m/<month>_generator<year>.xlsx` (new; forecast-only layer) |
| 3 | **EIA-923 2025** (Final expected on the same Sept cycle; check the page's release date) | https://www.eia.gov/electricity/data/eia923/ → `f923_2025.zip` | `data/raw/eia-923-generation-fuel/` (existing `fetch_eia923_generation_fuel.py`) |
| 4 | **EPA NEEDS for 2025 Reference Case, rev 11-28-2025** + Chapter 4 documentation | https://www.epa.gov/power-sector-modeling/national-electric-energy-data-system-needs | `data/raw/epa-needs/needs-for-2025-reference-case.xlsx` (new) |
| 5 | **PUDL**: `core_eia860__scd_generators`, `core_eia860__scd_plants`, `core_eia860__scd_ownership`, `core_epa__assn_eia_epacamd`, `core_epa__assn_eia_epacamd_subplant_ids`, `core_eia860m__changelog_generators` | https://data.catalyst.coop/ (parquet/CSV per table); raw archives https://doi.org/10.5281/zenodo.4127026 | `data/raw/pudl/<table>.parquet` (new) |
| 6 | **ERCOT CDR** xlsx, every May/Dec issue 2019-2025 (Dec-2025: `CapacityDemandandReservesReport_December2025.xlsx`) | https://www.ercot.com/gridinfo/resource → "Capacity, Demand and Reserves Report" | `data/raw/ercot-cdr/<issue>.xlsx` |
| 7 | **NYISO Gold Book** 2019-2025 (pdf + Excel appendix, Table III-2) | https://www.nyiso.com/planning → "Load & Capacity Data (Gold Book)" | `data/raw/nyiso-gold-book/` |
| 8 | **ISO-NE CELT** 2019-2025 (Section 2 generator list, xlsx) | https://www.iso-ne.com/system-planning/system-plans-studies/celt | `data/raw/neiso-celt/` |
| 9 | **PJM** IMM SOM §12 + PJM existing-generation list | https://www.monitoringanalytics.com/reports/PJM_State_of_the_Market/ ; https://www.pjm.com/planning/resource-adequacy-planning | `data/raw/pjm-capacity-report/` |
| 10 | **MISO** PRA results 2019/20-2025/26 + OMS-MISO survey | https://www.misoenergy.org/ (Markets → Planning Resource Auction) | `data/raw/miso-pra/` |
| 11 | **CAISO NQC list** 2019-2025 (xlsx per year) | https://www.caiso.com/ → Resource Adequacy → "Net qualifying capacity (NQC) and effective flexible capacity (EFC)" | `data/raw/caiso-nqc/` |
| 12 | **SPP Resource Adequacy Report** 2019-2025 (June issues) | https://www.spp.org/ (documents 64801 / 67297 / 69529 / 71804 / 74099) | `data/raw/spp-resource-adequacy/` |
| 13 | **WECC** Loads & Resources / WARA generation resource list (xlsx) | https://www.wecc.org/program-areas/reliability-planning-performance-analysis/reliability-assessments | `data/raw/wecc-loads-resources/` |
| 14 | SOCO: FERC Form 714 (already `data/raw/ferc-714/`) + Southern Company IRP capacity tables | https://www.ferc.gov/industries-data/electric/general-information/electric-industry-forms/form-no-714 | existing |

All free / public domain; licensing notes go in `docs/data-licensing.md` on intake (data-intake skill).

---

### One-paragraph verdict

The pipeline is sound in shape (vintage per solved year, month-precise COD, per-unit COD since S12, always-on CC guard) but not settled, because (i) the vintages are incomplete — 2023/2024 without retired sheets, 2025 on an Early Release whose retired sheet §C.5 shows to be 30-95 % pruned while the Final has been public since 2026-09-10, no 860M; (ii) the capacity basis is five flags with no two keepers alike, against a measured 3-9 % winter/summer and 9-17 % nameplate/summer spread; (iii) a dozen registry-read repairs are armed in one ISO and `U` in eight because rule 25 treats them like tuning — §C.2/C.3 show the unscreened populations (1.5-2.5 GW SB in PJM/MISO, 3.9 GW blank-summer rows in MISO, 20-156 summer>nameplate rows per ISO-year); and (iv) no keeper but PJM commits a fleet census, so drift is discovered through price residuals one plant at a time (Fusco, Parish, Edwardsport, Cottonwood, Vogtle, Stall, Boardman). Settling it is one data download (§F 1), one foundation lane (E.1-E.6 with E.8 tests), one census script with a ledger (E.7), and eight owner rulings (Q1-Q8).
