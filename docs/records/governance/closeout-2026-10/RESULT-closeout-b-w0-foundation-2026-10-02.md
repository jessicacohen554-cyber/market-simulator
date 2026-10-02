# RESULT — closeout-B: W0 EIA-860 settlement foundation (phases 1 + 2, zero LP)

PRECOMMIT: `PRECOMMIT-closeout-b-w0-foundation-2026-10-02.md`. Branch
`claude/closeout-b-w0-foundation` (merged `origin/main` without rebase). **No LP ran in this
session** (rule 32). Phase 3 waits for the desk to merge this PR.

## 1. What landed (phase 1, audit §E.1–E.9)

| Item | Construction | Where |
|---|---|---|
| E.1 | published seasonal envelope per thermal unit (summer Jun–Sep / winter Oct–May of the solved vintage), shares carried through plant×class bins, flat class derate deleted on covered rows; non-CC winter ≤ max(nameplate, summer); CC under the always-on guard | `seasonal_capacity_basis` (NEW, backcast default ON); `paths.set_eia860_seasonal_capacity_basis`; `eia860._rows_to_generators`, `campd_bins.fleet_to_bins`, `assembly.bins_to_fleet`, `arrays._seasonal_basis_pair` |
| E.2/E.5 | operable-sheet `Planned Retirement` never read in a backcast; vintage diffs committed | `backcast_actual_retirement_only` (NEW); `cod_ramp._load_cod_map(dir, True)`; `scripts/data/derive_eia860_vintage_diffs.py` → `W0-census/vintage_diffs/` |
| E.3 | `commission_year_cod_fallback`, `cc_block_summer_rating`, `cc_steam_part_capacity`, `retiree_vintage_status_scope`, `partial_plant_exit_carry`, `mid_vintage_exit_carry` backcast default ON (F1 two-half landing, `--no-…` escapes); steam-part repair in all nine ISOs; NG blocks reconciled where no demonstrated-peak table exists (SPP/NWPP/SOCO); reconstructed outage fleets carry the same repairs | `scenarios.py`, `plant_taxonomy.py`, `paths.set_eia860_fleet_row_repairs` |
| E.4 | `admit_standby_units` backcast default ON; bin constituents read the active status set; OA/OS envelope reported (never fitted) | `cod_ramp._load_unit_cod_map(dir, statuses)` |
| companion | `unit_outage_dispatched_bin_denominator` backcast default ON, yields to an explicit alternative denominator — **desk-confirmed**, conditions (a)–(e) §4 | `scenarios.__post_init__` |
| E.6 | every `eia860_generators.parquet` unfiltered + `nerc_region`; load-time `generator_footprint_mask` / `program_footprint_mask` | `process_eia860.py --unfilter-in-place`; readers in `eia860.py`, `campd_bins.py`, `hydro.py`, `announced_retirements.py`, `derive_egrid_family_heat_rates.py` |
| E.7 | `scripts/build_fleet_census.py` → `fleet_census_<Y>.json`; `promote_keeper.py` preflight step 0c refuses a NEW keeper without it; `audit_keepers.py` E15 (FAIL on a W0 keeper, WARN pre-W0) | |
| Q5 | ERCOT bin-sheet audit per vintage: plants absent, sheet plants absent, carried plants SHORT of their vintage units (split child codes folded) | `--ercot-csv-audit` |
| Q7 | PUDL `core_epa__assn_eia_epacamd_subplant_ids` intaken (`data/raw/pudl/`, CC-BY-4.0); every `CAMPD_UNIT_PLANT_REMAP` row confirmed by EPA/PUDL (14) or a cited override (6) | `data/campd_crosswalk.py` |
| E.8 | the eight named tests + `test_campd_crosswalk.py` | `tests/unit/data/`, `tests/unit/scoring/` |
| E.9 | `solve_surface.json` gains `eia860_vintages: {dir: sha256}`; freeze rule in the EIA-860 README | `config/solve_surface.py` |
| sentinels | EIA-860 Operating Month 88/99 → mid-year fallback (was December / January) — zero sentinel rows in any vintage on disk (INERT today) | `cod_ramp.resolve_eia860_month`, `eia860._operating_month` |
| CAISO | battery-envelope re-derivation loads its committed OP-only fleet under standby admission (switch-and-restore, as it already does for the vintage) | `model/storage.py` |

**E.6 zero-diff proof.** Committed rows are value-identical in all nine tables; the exit-channel presence
sets reproduce the derive-time population exactly in every vintage (joining BAs from their join year, exit
members through their exit year); the W0 census of MISO 2023, NWPP 2023, SOCO 2021, SPP 2019 is identical
before/after, and NWPP 2023's 19 LP fleet arrays + `mc_base` hash identically.

## 2. NEISO guard (PR #7033 spec) and the hard kill rule

Control at base `4d459da3` (sparse worktree, pre-E.6 tables) reproduces the NEISO lane's committed 2019
baseline on all 7 digests. **FAIL**: T1 trips (Kendall 1595 pmax 138.71 → 136.70 MW, E.1; Mystic 1588
CC pmax −2.6 % and 2019 availability ~doubled, E.1 + denominator companion; Canal 3 1599 availability
shape only), T3/T4 trip (2025 total 27,003 → 26,311 MW), T2 holds. **Desk ruling (a) conditional:** NEISO
stays in the W0 defaults; **its phase-3 re-solve is promotable ONLY IF every NEISO year's C3a moves ≤ 2 pp
vs `neiso119_span` AND the determination stays CALIBRATED** (PRECOMMIT §3b). The 2025 moves are named in
`W0-census/NEISO/NOTE-2025-capacity-moves.md`: COAL_BIT 203 → 108 MW = Schiller 2367 units 4/6 (OS in
vintage 2024, retired 2025-10 on the Final-2025 sheet); Androscoggin 55031 (OS, retired 2025-10); Potter
1660 CC2/CC3 (retired 2024-01); ≈ −700 MW E.1 on nameplate-basis CC. All EIA-860 facts.

## 3. Census (zero LP) — per ISO, W0 vs recorded posture

Full per-ISO-year ledgers: `W0-census/<ISO>/fleet_census_<Y>_{w0,recorded}.json` (families, residual
plant rows, OA/OS envelope, planned-retirement binding MW). **ISO report column: n/a** — no ISO report is
on disk (audit §F 6–13 owner downloads); stated, never guessed.

| ISO | years | Δ summer vs 860 (W0) | Δ winter vs 860 (W0) | Δ summer vs 860 (recorded) | Δ winter (recorded) | vs ISO report | families within 1 % (W0, all years) |
|---|---|---|---|---|---|---|---|
| ERCOT | 2019–2025 | +2.9 … +5.7 % | -3.2 … +0.1 % | +2.9 … +5.7 % | -3.2 … +0.0 % | n/a — report not on disk | 0/42 |
| CAISO | 2019–2025 | -7.2 … -2.1 % | -10.5 … -2.5 % | -2.5 … -1.4 % | -9.3 … -4.8 % | n/a — report not on disk | 12/42 |
| PJM | 2019–2025 | -2.5 … +0.5 % | -3.7 … -0.2 % | -1.0 … +1.5 % | -6.1 … -2.5 % | n/a — report not on disk | 1/42 |
| MISO | 2019–2025 | -7.7 … -4.6 % | -9.7 … -6.5 % | -8.3 … -5.7 % | -13.6 … -10.3 % | n/a — report not on disk | 2/42 |
| NYISO | 2021–2025 | -5.8 … -5.1 % | -8.0 … -4.6 % | -2.7 … -2.0 % | -9.7 … -6.8 % | n/a — report not on disk | 1/25 |
| NEISO | 2019–2025 | -3.7 … -2.7 % | -7.3 … -0.2 % | +2.3 … +4.6 % | -6.9 … +1.7 % | n/a — report not on disk | 11/42 |
| SPP | 2019–2025 | -3.2 … -1.1 % | -5.5 … -1.0 % | -4.4 … -1.9 % | -7.9 … -3.0 % | n/a — report not on disk | 8/42 |
| NWPP | 2019–2025 | -3.0 … +1.4 % | -5.6 … +2.7 % | -3.0 … +1.5 % | -9.2 … -1.6 % | n/a — report not on disk | 10/42 |
| SOCO | 2019–2025 | -11.0 … -0.8 % | -13.9 … -0.9 % | -11.1 … -3.7 % | -17.2 … -8.2 % | n/a — report not on disk | 10/42 |

Per ISO-year (MW):

| ISO | Year | 860 summer MW | model summer W0 (recorded) | Δ summer W0 | 860 winter MW | model winter W0 (recorded) | Δ winter W0 | OA/OS env. MW | planned-ret binding MW | ISO report |
|---|---|---|---|---|---|---|---|---|---|---|
| ERCOT | 2019 | 75,530 | 77,931 (77,909) | +3.2 % | 79,356 | 77,830 (77,808) | -1.9 % | 936 | 0 | n/a (not on disk) |
| ERCOT | 2020 | 75,668 | 78,086 (78,063) | +3.2 % | 79,406 | 77,961 (77,938) | -1.8 % | 1,035 | 0 | n/a (not on disk) |
| ERCOT | 2021 | 76,742 | 78,986 (78,960) | +2.9 % | 80,753 | 78,175 (78,150) | -3.2 % | 1,014 | 0 | n/a (not on disk) |
| ERCOT | 2022 | 77,367 | 80,306 (80,283) | +3.8 % | 81,727 | 79,782 (79,760) | -2.4 % | 1,121 | 0 | n/a (not on disk) |
| ERCOT | 2023 | 78,308 | 81,478 (81,456) | +4.0 % | 82,368 | 80,915 (80,893) | -1.8 % | 87 | 0 | n/a (not on disk) |
| ERCOT | 2024 | 78,922 | 81,725 (81,701) | +3.6 % | 83,269 | 81,344 (81,321) | -2.3 % | 5 | 0 | n/a (not on disk) |
| ERCOT | 2025 | 77,484 | 81,902 (81,879) | +5.7 % | 81,854 | 81,902 (81,879) | +0.1 % | 1,018 | 0 | n/a (not on disk) |
| CAISO | 2019 | 30,414 | 29,770 (29,641) | -2.1 % | 31,429 | 30,658 (29,641) | -2.5 % | 585 | 0 | n/a (not on disk) |
| CAISO | 2020 | 31,926 | 29,783 (31,492) | -6.7 % | 33,049 | 29,581 (29,974) | -10.5 % | 536 | 0 | n/a (not on disk) |
| CAISO | 2021 | 32,029 | 29,791 (31,481) | -7.0 % | 33,144 | 30,789 (31,481) | -7.1 % | 474 | 0 | n/a (not on disk) |
| CAISO | 2022 | 32,266 | 29,946 (31,531) | -7.2 % | 33,279 | 30,783 (31,531) | -7.5 % | 483 | 0 | n/a (not on disk) |
| CAISO | 2023 | 31,428 | 29,998 (30,828) | -4.5 % | 32,375 | 30,815 (30,828) | -4.8 % | 516 | 0 | n/a (not on disk) |
| CAISO | 2024 | 31,488 | 29,290 (30,835) | -7.0 % | 32,477 | 30,141 (30,835) | -7.2 % | 539 | 0 | n/a (not on disk) |
| CAISO | 2025 | 31,451 | 29,184 (30,723) | -7.2 % | 32,431 | 30,020 (30,719) | -7.4 % | 509 | 0 | n/a (not on disk) |
| PJM | 2019 | 174,622 | 174,982 (177,247) | +0.2 % | 183,447 | 183,108 (178,827) | -0.2 % | 542 | 0 | n/a (not on disk) |
| PJM | 2020 | 172,381 | 173,292 (174,586) | +0.5 % | 181,349 | 180,413 (174,620) | -0.5 % | 630 | 0 | n/a (not on disk) |
| PJM | 2021 | 176,000 | 171,662 (174,170) | -2.5 % | 185,107 | 178,201 (173,845) | -3.7 % | 617 | 0 | n/a (not on disk) |
| PJM | 2022 | 172,441 | 169,760 (172,412) | -1.6 % | 181,399 | 179,481 (174,060) | -1.1 % | 545 | 0 | n/a (not on disk) |
| PJM | 2023 | 170,869 | 169,511 (171,098) | -0.8 % | 179,982 | 175,667 (170,276) | -2.4 % | 543 | 0 | n/a (not on disk) |
| PJM | 2024 | 170,075 | 166,533 (169,608) | -2.1 % | 178,886 | 173,217 (170,781) | -3.2 % | 1,335 | 0 | n/a (not on disk) |
| PJM | 2025 | 169,260 | 165,845 (168,660) | -2.0 % | 177,897 | 171,829 (168,680) | -3.4 % | 1,131 | 0 | n/a (not on disk) |
| MISO | 2019 | 143,691 | 136,449 (135,251) | -5.0 % | 151,034 | 140,737 (135,030) | -6.8 % | 1,096 | 0 | n/a (not on disk) |
| MISO | 2020 | 144,217 | 135,721 (134,528) | -5.9 % | 151,667 | 138,544 (132,900) | -8.7 % | 660 | 0 | n/a (not on disk) |
| MISO | 2021 | 142,413 | 134,505 (132,954) | -5.6 % | 149,475 | 139,773 (134,115) | -6.5 % | 1,279 | 0 | n/a (not on disk) |
| MISO | 2022 | 139,139 | 132,756 (131,176) | -4.6 % | 146,908 | 136,763 (130,627) | -6.9 % | 1,316 | 0 | n/a (not on disk) |
| MISO | 2023 | 135,881 | 127,773 (126,831) | -6.0 % | 144,035 | 133,255 (127,351) | -7.5 % | 1,254 | 0 | n/a (not on disk) |
| MISO | 2024 | 133,298 | 125,306 (124,416) | -6.0 % | 141,257 | 131,387 (125,679) | -7.0 % | 1,296 | 0 | n/a (not on disk) |
| MISO | 2025 | 133,109 | 122,820 (122,062) | -7.7 % | 141,169 | 127,530 (121,993) | -9.7 % | 1,295 | 0 | n/a (not on disk) |
| NYISO | 2021 | 30,977 | 29,292 (30,282) | -5.4 % | 33,600 | 32,057 (31,325) | -4.6 % | 572 | 0 | n/a (not on disk) |
| NYISO | 2022 | 30,873 | 29,313 (30,270) | -5.1 % | 33,510 | 30,938 (30,265) | -7.7 % | 38 | 0 | n/a (not on disk) |
| NYISO | 2023 | 30,660 | 28,912 (29,826) | -5.7 % | 33,103 | 30,812 (30,242) | -6.9 % | 93 | 0 | n/a (not on disk) |
| NYISO | 2024 | 30,652 | 28,922 (29,882) | -5.6 % | 33,036 | 30,378 (29,903) | -8.0 % | 62 | 0 | n/a (not on disk) |
| NYISO | 2025 | 30,317 | 28,553 (29,496) | -5.8 % | 32,605 | 29,987 (29,495) | -8.0 % | 60 | 0 | n/a (not on disk) |
| NEISO | 2019 | 27,980 | 27,004 (28,627) | -3.5 % | 30,289 | 28,070 (28,196) | -7.3 % | 88 | 0 | n/a (not on disk) |
| NEISO | 2020 | 27,624 | 26,681 (28,436) | -3.4 % | 30,158 | 28,397 (28,456) | -5.8 % | 13 | 0 | n/a (not on disk) |
| NEISO | 2021 | 26,630 | 25,758 (27,436) | -3.3 % | 28,922 | 28,176 (28,334) | -2.6 % | 88 | 0 | n/a (not on disk) |
| NEISO | 2022 | 26,525 | 25,548 (27,239) | -3.7 % | 28,812 | 27,170 (27,368) | -5.7 % | 73 | 0 | n/a (not on disk) |
| NEISO | 2023 | 25,737 | 24,997 (26,823) | -2.9 % | 27,829 | 26,435 (27,066) | -5.0 % | 279 | 0 | n/a (not on disk) |
| NEISO | 2024 | 24,342 | 23,677 (25,186) | -2.7 % | 26,168 | 26,115 (26,617) | -0.2 % | 273 | 0 | n/a (not on disk) |
| NEISO | 2025 | 23,559 | 22,828 (24,648) | -3.1 % | 25,423 | 24,031 (24,668) | -5.5 % | 889 | 0 | n/a (not on disk) |
| SPP | 2019 | 57,836 | 56,791 (56,090) | -1.8 % | 58,789 | 57,540 (56,100) | -2.1 % | 213 | 0 | n/a (not on disk) |
| SPP | 2020 | 56,728 | 56,111 (55,634) | -1.1 % | 57,624 | 57,075 (55,878) | -1.0 % | 228 | 0 | n/a (not on disk) |
| SPP | 2021 | 56,944 | 55,530 (55,092) | -2.5 % | 57,796 | 56,126 (55,092) | -2.9 % | 217 | 0 | n/a (not on disk) |
| SPP | 2022 | 57,720 | 55,874 (55,170) | -3.2 % | 58,509 | 56,351 (55,131) | -3.7 % | 196 | 0 | n/a (not on disk) |
| SPP | 2023 | 56,410 | 55,068 (54,637) | -2.4 % | 57,315 | 56,321 (55,287) | -1.7 % | 186 | 0 | n/a (not on disk) |
| SPP | 2024 | 55,877 | 54,547 (54,240) | -2.4 % | 57,433 | 55,773 (54,225) | -2.9 % | 186 | 0 | n/a (not on disk) |
| SPP | 2025 | 57,009 | 55,316 (54,980) | -3.0 % | 58,920 | 55,687 (54,238) | -5.5 % | 109 | 0 | n/a (not on disk) |
| NWPP | 2019 | 29,968 | 29,185 (29,279) | -2.6 % | 31,457 | 30,465 (29,279) | -3.2 % | 66 | 0 | n/a (not on disk) |
| NWPP | 2020 | 28,116 | 28,517 (28,530) | +1.4 % | 29,614 | 30,411 (29,144) | +2.7 % | 85 | 0 | n/a (not on disk) |
| NWPP | 2021 | 28,734 | 27,871 (27,893) | -3.0 % | 30,151 | 29,112 (27,893) | -3.4 % | 20 | 0 | n/a (not on disk) |
| NWPP | 2022 | 29,115 | 28,231 (28,244) | -3.0 % | 30,318 | 29,283 (28,228) | -3.4 % | 42 | 0 | n/a (not on disk) |
| NWPP | 2023 | 29,121 | 28,234 (28,248) | -3.0 % | 30,482 | 29,365 (28,254) | -3.7 % | 42 | 0 | n/a (not on disk) |
| NWPP | 2024 | 29,634 | 28,771 (28,784) | -2.9 % | 31,031 | 29,304 (28,168) | -5.6 % | 55 | 0 | n/a (not on disk) |
| NWPP | 2025 | 29,588 | 28,740 (28,756) | -2.9 % | 30,933 | 29,878 (28,756) | -3.4 % | 74 | 0 | n/a (not on disk) |
| SOCO | 2019 | 54,896 | 53,539 (52,566) | -2.5 % | 57,689 | 56,559 (52,553) | -2.0 % | 1 | 0 | n/a (not on disk) |
| SOCO | 2020 | 54,926 | 52,545 (52,554) | -4.3 % | 57,707 | 54,512 (52,554) | -5.5 % | 5 | 0 | n/a (not on disk) |
| SOCO | 2021 | 56,099 | 53,969 (53,888) | -3.8 % | 58,713 | 55,893 (53,888) | -4.8 % | 30 | 0 | n/a (not on disk) |
| SOCO | 2022 | 54,520 | 54,100 (52,212) | -0.8 % | 57,311 | 56,774 (52,212) | -0.9 % | 30 | 0 | n/a (not on disk) |
| SOCO | 2023 | 56,848 | 50,601 (50,546) | -11.0 % | 59,716 | 51,428 (49,420) | -13.9 % | 26 | 0 | n/a (not on disk) |
| SOCO | 2024 | 54,901 | 52,888 (52,843) | -3.7 % | 57,742 | 53,711 (51,729) | -7.0 % | 19 | 0 | n/a (not on disk) |
| SOCO | 2025 | 54,861 | 52,845 (52,811) | -3.7 % | 57,764 | 54,787 (52,811) | -5.2 % | 1 | 0 | n/a (not on disk) |


Reading the census honestly: **the W0 posture does not yet land inside the ruled tolerances** (61 of 63
ISO-years OUTSIDE). The model sits BELOW the published ratings in eight ISOs. The named residual rows
point at constructions, not at the basis itself: CHP grid carve-outs (host steam held out), CC plants held
at the measured CAMPD p99.9 / nameplate guard below their published block rating (e.g. MISO 55380, NEISO
60903), classes the model injects from EIA-923 rather than carrying as LP capacity, and oil coverage.
ERCOT sits ABOVE summer because its curated sheet is nameplate-basis (E.1 is scoped out of ERCOT until
the Q5 migration). Each is a phase-3 lane's object, reported rather than tuned (rule 23). Note on the
recorded column: a pre-W0 unit carries no seasonal share, so its "summer" is its pmax (the legacy flat or
ratio derates live in availability, not in the capability column). `planned_retirement_binding_mw` = 0
in every ISO-year (E.5 measured inert, as the audit predicted).

## 4. G-DRIFT (rule 29 (b)), zero LP — each W0 field toggled ALONE on the 2023 keeper recipe

`LIVE` = some LP-visible fleet array or `mc_base` hash moves; `INERT` = none moves; `armed` = the keeper
already arms it (INERT by construction). Evidence: `W0-census/<ISO>/gdrift_2023.json`.

| ISO (2023) | seasonal_capacity_basis | backcast_actual_retirement_only | commission_year_cod_fallback | cc_block_summer_rating | cc_steam_part_capacity | retiree_vintage_status_scope | admit_standby_units | partial_plant_exit_carry | mid_vintage_exit_carry | unit_outage_dispatched_bin_denominator | ALL W0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ERCOT | INERT | INERT | INERT | INERT | INERT | LIVE | LIVE | armed | INERT | INERT | LIVE |
| CAISO | LIVE | INERT | LIVE | INERT | LIVE | INERT | LIVE | LIVE | LIVE | INERT | LIVE |
| PJM | LIVE | INERT | LIVE | INERT | INERT | INERT | LIVE | LIVE | armed | LIVE | LIVE |
| MISO | LIVE | INERT | armed | armed | armed | armed | LIVE | armed | armed | armed | LIVE |
| NYISO | LIVE | INERT | LIVE | INERT | INERT | armed | LIVE | LIVE | armed | INERT | LIVE |
| NEISO | LIVE | INERT | LIVE | INERT | INERT | LIVE | LIVE | armed | armed | LIVE | LIVE |
| SPP | LIVE | INERT | LIVE | LIVE | INERT | LIVE | LIVE | LIVE | armed | INERT | LIVE |
| NWPP | LIVE | INERT | LIVE | INERT | INERT | LIVE | armed | armed | armed | LIVE | LIVE |
| SOCO | LIVE | INERT | LIVE | INERT | INERT | INERT | LIVE | LIVE | LIVE | LIVE | LIVE |

**Every ISO is LIVE at the all-W0 posture → one full-span re-solve per ISO in phase 3.** Code-only hunks,
classified by their own measurement: E.6 regeneration INERT (zero-diff above); month sentinels INERT (0
rows on disk); E.9 stamp, census/promote/audit tooling, crosswalk audit INERT (off the solve path);
`backcast_actual_retirement_only` INERT in all nine (0 MW binding). The denominator companion is LIVE in
PJM, NEISO, NWPP, SOCO and yields (INERT) in CAISO, NYISO, SPP — attributed separately from E.1 as the
desk required.

**Desk conditions on the denominator companion:** (a) `--no-unit-outage-dispatched-bin-denominator` reaches
the pre-arm posture ✔; (b) yield rule tested
(`test_unit_outage_dispatched_bin_denominator.py::test_yields_to_an_explicit_alternative_denominator`) and
listed per ISO in the PRECOMMIT ✔; (c) matrix row states the backcast default, every shard carries its cell ✔;
(d) G-DRIFT attributes it per ISO, separately from E.1 ✔ (table above); (e) NEISO tripwire evaluated with it on ✔.

## 5. Inputs from other lanes, folded in

- closeout-SPP (PR #7024): the flat summer class derate double-counts on SPP's net-summer CT/CC pmax,
  1.90–2.11 GW Jun–Sep every year (`results/phase0/spp/_spp_closeout_ct_pmax_basis.json`) — the measured
  case of the E.1 deletion. Under SPP's MMU offer-unavailability arms the fossil rows already skip it.
- closeout-ERCOT (PR #7029): Decker Creek 3548 steam units absent 2019–2022 — now flagged by the Q5 audit
  (726 / 405 / 405 MW short 2019 / 2020 / 2021), `FINDING-closeout-w1-zero-lp-censuses-2026-10-02.md` row 6.
- closeout-NWPP (PR #7028): audit §C.7's NWPP "discontinuity" corrected (raw AVA Demand artifact; Adjusted
  peaks 46.5 … 51.0 GW), citing `FINDING-nwppnext20-…` §4.

## 6. Findings recorded, not absorbed

- `tests/unit/data/test_st_gas_oom_level.py` pins the pre-W0 commission year: under the plant's real COD
  (W0 `commission_year_cod_fallback`) the MISO ST_GAS oom-off floor window covers 20,876 h vs 17,204 h
  armed, breaking the fixture's "only the level moves" invariant — for the MISO lane.
- `tests/unit/data/test_gas_offer_zonal_anchor_vintage.py` (2 tests) fails on `main` too (pre-existing).
- E.1 scope limits: ERCOT's curated sheet stays nameplate-basis (Q5 migration later); nuclear/oil/biomass
  (no thermal group) stay on net summer. `wefor_residual` re-identification on the seasonal basis (audit
  E.1, caiso-186) is a phase-3 item per ISO.
- EPA NEEDS not intaken (URL 404 from this container) — owner download (audit §F 4).

## 7. Tests

Fast tier (`-m "not slow and not integration and not fulldata"`): all pass except the two pre-existing
zonal-anchor failures. Full lane: see the PR. `check_cache_key_registration.py`, `check_mechanism_matrix.py
--base origin/main`, `ruff check` / `ruff format --check`: clean.

## 8. Phase 3 (after the desk merges)

One full-span re-solve per ISO at the W0 defaults (rules 32/34/36): ERCOT, PJM, MISO, NEISO, SPP, NWPP,
SOCO 7 years each, CAISO 7 (2019–2025), NYISO 5 (2021–2025) = **61 shards**, each pushing its full bundle
with `fleet_census_<Y>.json` (now required by `promote_keeper.py`). NEISO is promotable only under §2's
kill rule. No results were deleted in this session (rule 31).
