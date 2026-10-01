# PRECOMMIT — R-CAISO: CAISO re-solve on corrected backcast inputs (2026-09-24)

Charter: `docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md` §5.3.1. Owner instruction
(2026-09-24): every backcast year runs on the year-correct EIA-860 vintage, plant-specific heat rates (never
the asset-class table), and granular CAMPD outage data. Precondition met: F1 (#6572) and F2 (#6569) merged;
lane cut from `9210075392a128d14a5efb168ab1f9955a9b6946`. The parent solves nothing (rule 32(a)); every
number below is zero LP.

## 0. Year set (rule 34(c) / 35(b)) and the 2019–2021 blocker

**Registered CAISO union, enumerated from `frontend/data/backcast/registry/*.json`: `{2022, 2023, 2024, 2025}`**,
all in one run (`2026-09-20-caiso-290-leftedge`, bundle `xiso8_leftedge_span`); no stamped touchpoint.

**2019, 2020 and 2021 are NOT solved in this lane. A faithful solve is impossible at HEAD**, per a
read-only code-and-data audit (zero LP):

| blocker | 2019 | 2020 | 2021 |
|---|---|---|---|
| `caiso_supply_consistent_demand` (armed) artifact exists for 2022–25 only (`derive_caiso_supply_consistent_demand.py` `YEARS`) → `FileNotFoundError` at `eia930/demand.py:274-278` | **HARD** | **HARD** | **HARD** |
| CA carbon price `STATE_CARBON_PRICE_BY_ISO` covers 2022–25 → silently $0/t (`cap_and_trade.py:141-142, :326`) | silent | silent | silent |
| EIA-930 CISO `NG: WAT` gaps summed as zero → hydro budget rescaled (`envelopes.py:122`, `hydro.py:1299-1322`) | Oct–Dec ≈0 | Jan–Jul 0 (≈4.5 TWh/yr) | ok |
| nuclear per-unit CSV / `NUCLEAR_MONTHLY_CF_BY_YEAR` start 2022 → static CF (`outages.py:2266`) | silent | silent | silent |
| per-hub intertie price series (2021: 1,560 of 8,760 h) → static ladder; DSW clean tranches inert/partial | silent | silent | silent |
| LMP + tail benchmark (`actual_lmp.json`, `actual_tail.json`) 2022+ → C3a/C3b/C3c SKIPPED | unscored | unscored | unscored (raw 2021 LMP exists; reference not derived) |

A shard for these years would either stop at the demand artifact or, once that is patched, solve a year
whose carbon, hydro, nuclear and intertie inputs are silent defaults — the opposite of what the owner
instruction asks for. **Routed to the owner as a data-intake decision** (§7), not solved.

## 1. Recipe (ex ante; offer-curve multipliers UNCHANGED — rule 1(c))

`scripts/replay_keeper.py results/calibration/xiso8_leftedge_span --years <Y>` with exactly these `--set`
overrides and nothing else:

| `--set` | keeper | arm | why |
|---|---|---|---|
| `eia860_vintage_tracks_solve_year=true` | off (recorded False) | **on** | F1 default; `vintage_<Y>` for 2022–24, canonical for 2025 |
| `measured_st_heat_rates=true` | off | **on** | F1 artifact (ST_GAS) |
| `measured_cc_heat_rates=true` | off (absent) | **on** | F1 artifact + the §2 remap fix |
| `unit_outage_short_windows=true` | off (cell I) | **on** | gate carrier for the gas family; coal file is EMPTY for CAISO → inert by construction |
| `unit_outage_short_windows_gas=true` | off (cell U) | **on** | F2 artifact, re-derived hour-grain (§3) |
| `unit_partial_outage_windows=true` | off (cell U) | **on** | F2 artifact; 0 windows every year (no baseload coal) → inert by construction |

Unchanged and asserted: `measured_ct_heat_rates` / `measured_chp_heat_rates` / `egrid_family_heat_rates`
ON; std extract `campd-unit-outages-CAISO.csv` (sha `cf156483…`) ON; `caiso_dam_outages` OFF (§4);
`offer_curve_overrides` / `offer_curve_deltas` `{}`; every other recipe key byte-for-byte the keeper's. No
new `ScenarioConfig` field, no new threshold, no `authorized_price_tuning` block. Cross-year knobs off
(rule 36 defaults).

## 2. Heat-rate census (zero LP; `census_caiso.py`, `census_caiso.json`)

Thermal nameplate at an asset-class (`HEAT_RATE_BINS`) rate, keeper posture → arm posture:

| year | keeper EIA-860 source | keeper class-table MW (share) | arm EIA-860 source | arm class-table MW (share) | arm thermal MW | arm MW-wtd HR CC / ST / CT |
|---|---|---|---|---|---|---|
| 2019 | canonical | 606.9 (2.04 %) | vintage_2019 | **41.0 (0.15 %)** | 28,040.8 | 7.585→7.548 / 15.595→12.271 / 10.165→10.198 |
| 2020 | canonical | 612.3 (2.00 %) | vintage_2020 | **58.8 (0.20 %)** | 29,554.7 | 7.583→7.611 / 15.516→11.444 / 10.101→10.163 |
| 2021 | canonical | 604.1 (2.02 %) | vintage_2021 | **81.8 (0.28 %)** | 29,658.5 | 7.532→7.585 / 15.516→12.537 / 10.047→10.035 |
| 2022 | canonical | 606.7 (2.03 %) | vintage_2022 | **97.4 (0.33 %)** | 29,888.3 | 7.52→7.536 / 15.516→12.066 / 10.102→10.137 |
| 2023 | canonical | 607.0 (2.03 %) | vintage_2023 | **97.4 (0.34 %)** | 29,020.4 | 7.537→7.61 / 15.516→12.108 / 10.081→10.16 |
| 2024 | canonical | 655.0 (2.25 %) | vintage_2024 | **144.6 (0.50 %)** | 29,062.7 | 7.533→7.592 / 14.41→12.375 / 10.061→10.061 |
| 2025 | canonical | 655.0 (2.26 %) | canonical | **145.0 (0.50 %)** | 28,993.1 | 7.533→7.564 / 14.316→11.728 / 10.098→10.098 |

The keeper column is the keeper's flags on HEAD inputs (F1 moved the canonical eGRID join to eGRID 2024), so it isolates the arm's delta. **Residual class-table plants in the arm (absent from every eGRID vintage 2018–2024 AND from CAMPD — none files CEMS):** 55874 Panoche Peaker (gas_ct, 56.7 MW); 66638 Enchanted Rock Lodi (gas_ct, 48.0 MW); 65199 Keysight - Santa Rosa (gas_ct, 4.5 MW); 66146 Kaiser - LA (gas_ct, 4.5 MW); 66148 Kaiser - Woodland Hills (gas_ct, 3.1 MW); 59395 City of Tulare Water Facility (gas_ct, 2.8 MW); 66456 Anheuser Busch - Fairfield (gas_ct, 2.6 MW); 65361 CalTech - Pasadena Wilson Ave (gas_ct, 2.2 MW); 66142 Kaiser - Harbor City (gas_ct, 2.1 MW); 65210 Enloe Medical - Chico (gas_ct, 1.7 MW); 69191 GreenStruxure REP009, LLC (gas_ct, 1.4 MW); 66145 Life Technologies - Fremont (gas_ct, 1.3 MW); 66458 Redlands Community Hospital (gas_ct, 1.1 MW); 64756 EQX005.0 Toyama Fuel Cell (gas_ct, 1.1 MW); 66459 Taylor Farms - Schilling Place (gas_ct, 1.0 MW); 65191 University of San Diego (gas_ct, 1.0 MW); 65192 AT&T San Diego (gas_ct, 1.0 MW); 65193 CalTech - Pasadena (PPA) (gas_ct, 1.0 MW); 65196 SCC - San Jose (gas_ct, 1.0 MW); 65200 DirecTV - Los Angeles (gas_ct, 1.0 MW); 50610 Saint Johns Health Center (gas_ct, 1.0 MW); 65202 CalTech - Pasadena (gas_ct, 1.0 MW); 65203 Beckton Dickenson - San Jose (gas_ct, 1.0 MW); 65204 AT&T - Redwood City (gas_ct, 1.0 MW); 65205 AT&T - Gardena (gas_ct, 1.0 MW); 65206 AT&T - Hawthorne (gas_ct, 1.0 MW); 65208 AT&T - Hayward (gas_ct, 1.0 MW); 65211 Comcast - Universal City (gas_ct, 1.0 MW); 65360 AT&T - San Diego Trade Street (gas_ct, 1.0 MW); 66143 San Diego Community College (gas_ct, 1.0 MW). Largest: Panoche Peaker 55874 (Wellhead, no CEMS; distinct from Panoche Energy Center 56803, which is measured) and Enchanted Rock Lodi 66638 (2024+); the rest are ≤ 4.5 MW behind-the-meter fuel-cell / microturbine sites.

**Defect found and fixed in phase 0 (rule 14).** `scripts/data/derive_campd_cc_heat_rates.py` filtered
CEMS by raw `facilityId`, never routing through `campd.CAMPD_UNIT_PLANT_REMAP` (which the outage and
emissions derives already apply). El Segundo Energy Center (EIA 57901, 510 MW CC; no eGRID row in any
vintage) files CEMS under legacy ORIS 330, so it stayed at the class table in every year; Alamitos (62115,
603 MW) and Huntington Beach (62116, 630 MW) CCs file under 315/335 and got no measured rate. Patched to
re-key before the fleet filter; CAISO's artifact re-derived (rule 23: the data change is the identity
routing, not a residual). Result: the patched file **only adds rows** — 57901 / 62115 / 62116, pooled and
per-year, every one `flag == ok` (boundary 0.94–1.14) — and every pre-existing applied value is
byte-identical. Pooled rates: El Segundo 8.530, Alamitos 6.997, Huntington Beach 6.936 MMBtu/MWh.
**Other ISOs' artifacts were NOT re-derived** (rule 25); NYISO's Astoria Energy II (55375 → 57664) is in
the same remap table and is routed to R-NYISO.

## 3. Outage census (zero LP)

Windows starting in the year / approx. MW-h overlapping the year, CAISO files:

| family (file) | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| partial | 0 / 0.00 TWh | 0 / 0.00 TWh | 0 / 0.00 TWh | 0 / 0.00 TWh | 0 / 0.00 TWh | 0 / 0.00 TWh | 0 / 0.00 TWh |
| short-coal | 0 / 0.00 TWh | 0 / 0.00 TWh | 0 / 0.00 TWh | 0 / 0.00 TWh | 0 / 0.00 TWh | 0 / 0.00 TWh | 0 / 0.00 TWh |
| short-gas | 398 / 5.85 TWh | 320 / 5.03 TWh | 296 / 4.29 TWh | 404 / 5.58 TWh | 402 / 5.28 TWh | 361 / 5.65 TWh | 435 / 7.65 TWh |
| std (armed) | 576 / 42.63 TWh | 555 / 40.37 TWh | 603 / 42.47 TWh | 496 / 35.86 TWh | 584 / 39.43 TWh | 499 / 46.75 TWh | 670 / 58.06 TWh |

std is armed in the keeper already; short-gas is the NEW measured family (≈5–8 TWh·MW-h of capability removed per year, 1–5-day full stops, merit-order guarded); short-coal and partial are empty for CAISO (no baseload coal) and arm as no-ops.

**Short-gas grain repair.** F2 derived `campd-unit-outages-shortgas-CAISO.csv` at DAY grain, while
CAISO's std extract is HOUR grain (caiso-183: day-grain re-expansion asserts up to 23 h per edge the
detector never detected). On 1–5-day windows that edge error is a large fraction of the window, so the file
was re-derived with the SAME F2 invocation plus `--hour-grain`. The deriver asserts in-process that the
base-column projection equals the flag-absent frame; independently verified: base columns identical, 2,616
rows, only `outage_start_hour` / `outage_end_hour` appended. The un-flagged re-derive reproduces F2's
committed file and layup companion byte-for-byte.

## 4. `caiso_dam_outages` — NOT armed (the charter asks for a stated decision)

CAISO's CNOG DAM record is ISO-native and measured, so rule 14 is the right question. The answer at HEAD is
no, for three measured reasons:

1. **Coverage hole.** Every episode on a crosswalked resource starts at or after **2022-11-22** (56
   resources / 43 plants; curtailed MW × h by episode start year: 0.15 TWh in 2022 against 49.1 / 79.9 /
   54.4 TWh in 2023 / 2024 / 2025). The merge
   is per `(plant_code, plant_group)` for the whole year, so arming it in 2022 would replace 43 plants'
   CAMPD windows with an almost-empty series — the silent zeroing its own docstring promises never happens.
2. **Definition seam (caiso-190 §9, never cleared).** The loader sums every nature of work. By MW-h:
   PLANT_MAINTENANCE 28.5 %, ENVIRONMENTAL_RESTRICTIONS 26.4 %, PLANT_TROUBLE 23.5 %, **AMBIENT_DUE_TO_TEMP
   16.2 %** — the last double-counts the armed `temp_dependent_derate` (rule 19), and environmental
   use-limits are not a physical outage.
3. **Scope.** This lane is an input correction; a nature-of-work filter plus a per-date coverage merge is a
   construction change with its own charter. Named successor, matrix cell stays `U`.

## 5. G-DRIFT (rule 29(b)) — keeper pin `e7091f56` → HEAD

The keeper's recorded `git_sha e7091f56` was a rebased lane commit and is not reachable from `main`; its
solve-path tree is `cce686a7` (xiso-8's own commit on `main`, the PRECOMMIT-addendum/anchor commits that
carried the pinned code). `git diff cce686a7 HEAD` over `src/market_sim`, `scripts/run_calibration*.py`,
`scripts/lib`, `data/raw/_validation-source`, `data/raw/reference`: **43 files, 36 non-merge commits, every
hunk classified** (read-only audit):

* **LIVE-F1 (by design):** the six backcast default flips (`scenarios.py`), `data/egrid.py` year-matched
  join, `fleet/eia860.py` (boundary repair per active vintage, per-year measured maps, CC swap, retiree /
  mothball channels take measured swaps), `fleet/campd_bins.py::_measured_rate_map` (solve-year row, else
  pooled), `assembly.py` / `run_calibration.py` threading, `data/chp.py` year argument. **Note: several of
  these move CAISO even at the keeper's flag values** — the canonical snapshot was re-joined eGRID 2023 → 2024,
  and the keeper's own armed `campd_ct` / `chp_power_only` CAISO artifacts were re-derived with per-year rows.
  So the arm-vs-keeper delta is **the whole F1/F2 input correction**, not only the §1 `--set` flags.
* **LIVE-F2 (by design):** the short/partial outage paths reached by §1's `--set`, reading the §3 files.
* **INERT for CAISO:** 15 new `ScenarioConfig` fields (all default False, frozen "False", absent from the
  recipe); p0_cache (`MARKET_SIM_P0_CACHE` unset, default off); P0 slim extraction and row-bound joining
  (byte-identical, NEISO atol=0 gate, e107949d); P1 basis seed (default off, replay pins 0); SOCO/NYISO/NWPP/
  SPP/PJM/MISO-only branches; gated coal/hydro/CHP/outage-denominator mechanisms; IO, CLI (`default=None`)
  and cache-key bookkeeping.
* **LIVE-OTHER: none.**
* **Scoring-only (not the solve):** `run_calibration_full` EIA-923 benchmark construction (ad42fe43: oil
  re-attribution two-sided and before the CAMPD backfill; missing-month fill limited to post-COD months). It
  can move CAISO's C1 class actuals. The comparison in the RESULT therefore scores BOTH the keeper and the arm
  on HEAD's benchmark, and states where a C1 cell moved because the benchmark moved.

Form 4 is valid: the keeper's committed bundle is the control; no control solve is spent.

## 6. Shard plan (rule 32(c), 34(a), 36)

One year per shard, pinned to this PRECOMMIT's SHA, own out-dir / branch, full bundle pushed incl.
`dispatch/<Y>_P1.parquet` via `.gitignore` negation + plain `git add`:

| shard | year | out-dir | branch |
|---|--:|---|---|
| r-caiso-2022 | 2022 | `results/calibration/rcaiso_inputs_2022` | `claude/r-caiso-2022` |
| r-caiso-2023 | 2023 | `results/calibration/rcaiso_inputs_2023` | `claude/r-caiso-2023` |
| r-caiso-2024 | 2024 | `results/calibration/rcaiso_inputs_2024` | `claude/r-caiso-2024` |
| r-caiso-2025 | 2025 | `results/calibration/rcaiso_inputs_2025` | `claude/r-caiso-2025` |

Control = the keeper's committed bundle (G-CTRL form 4); no control solve.

## 7. What would make this NOT a keeper (stated before the solve)

* a load-bearing criterion (C1/C2/C3a/C3b) flipping PASS → FAIL in any year, or a second ledgered caveat;
* the governance gate (C6) or C8 failing;
* any leg whose config signature differs from §1.

A regression is **reported and root-caused (rule 14), never re-tuned**: an input that is more accurate and
fits worse is evidence of a compensating error elsewhere. The owner decides promotion (rule 31).

**Owner decision owed regardless:** the 2019–2021 intake program in §0 (supply-consistent demand for 2019–21,
CA carbon 2019–21, a hydro source for 2019–20, nuclear per-unit 2019–21, the intertie hub series, and the
2021 LMP/tail references).
