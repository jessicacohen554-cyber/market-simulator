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

CENSUS_TABLE

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

OUTAGE_TABLE

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

GDRIFT

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
