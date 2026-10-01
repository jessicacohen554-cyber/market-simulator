# PRECOMMIT — R-NEISO: re-solve NEISO 2019–2025 on corrected backcast inputs (2026-09-24)

**Lane:** R-NEISO (`docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md` §5.3.4) ·
**ISO:** NEISO · **Mode:** backcast · **LP spent before this doc:** zero ·
**Base:** `9210075392a128d14a5efb168ab1f9955a9b6946` (main after F1 #6572 and F2 #6569 merged; precondition met).

Owner instruction (2026-09-24): every backcast year 2019–2025 runs on the year-correct EIA-860 vintage,
plant-specific heat rates (never the asset-class table), and granular CAMPD outage data.

## 0. Incumbent and year set (rules 34(c) / 35(b))

| | |
|---|---|
| keeper | `2026-09-22-hydro-5-neiso-ror`, bundle `results/calibration/hydro5_neiso_ror_span`, solved at `fda9ece3` |
| registered NEISO runs | exactly one — that keeper (no touchpoint stamped to it) |
| registered year set | **2020, 2021, 2022, 2023, 2024, 2025** |
| this lane's year set | **2019–2025** (adds 2019; covers the registered set, so a promotion would not shrink it) |
| benchmarks | present for every year 2019–2025: `calibration_reference.json` NEISO 2019–2025, `actual_lmp_hourly_NEISO.parquet`, `lmp-data/NEISO/<Y>_smd_hourly.xlsx` 2019–2025, `actual_tail.json` NEISO 2018–2026 |

## 1. Recipe — the keeper plus input corrections only

Every leg is `scripts/replay_keeper.py results/calibration/hydro5_neiso_ror_span --years <Y>` with the
`--set` deltas below (eight flips, two kept arms restated). **Offer-curve multipliers UNCHANGED** — byte-identical `offer_curve_overrides`
(rule 1(c): an input correction, never a re-tune against the gates). No new tuning channel, no new DOF.

| field | keeper | R-NEISO | source |
|---|---|---|---|
| `eia860_vintage_tracks_solve_year` | False | **True** | F1 default (backcast); `vintage_<Y>` for 2019–2024, canonical for 2025 |
| `measured_ct_heat_rates` | True | True | kept (keeper arm) — artifact re-derived by F1 (pooled + per-year rows) |
| `measured_chp_heat_rates` | True | True | kept (keeper arm) — artifact re-derived by F1 |
| `measured_st_heat_rates` | False | **True** | F1 default; `campd_st_heat_rates_NEISO.csv` |
| `measured_cc_heat_rates` | False | **True** | F1 default; `campd_cc_heat_rates_NEISO.csv` |
| `measured_coal_heat_rates` | False | **True** | F1 default; NEISO **does** carry coal in-window — Merrimack 2364 (438.5 MW, 2019–2025) and Bridgeport Harbor 568 (unit 3, 257.6 MW, retired 2021). eGRID-vs-measured net rate: Merrimack 15.01 → 12.52, Bridgeport Harbor 6.63 → 10.19 MMBtu/MWh |
| `unit_outage_short_windows_gas` | False | **True** | F2 `campd-unit-outages-shortgas-NEISO.csv` (merit-guarded, 99–138 windows/yr) — made armable alone, §3 |
| `unit_partial_outage_windows` | False | **True** | F2 `campd-partial-outages-NEISO.csv` — **0 rows in every year: armed as instructed, INERT by data** |
| `mid_vintage_exit_carry` | False | **True** | a year-END vintage table drops a plant that retired DURING the year; this carries it through its EIA retirement month (§3b). Pilgrim 2019, Mystic 2024, … |
| `partial_plant_exit_carry` | False | **True** | the unit-grain twin: a unit retired during the year inside a surviving plant (Bridgeport Harbor 3 coal, 2021; Mystic 7, 2021) (§3b) |
| `unit_outage_short_windows` (coal) | False | **False** | stays **R** (neiso-69) — §2 |
| `hydro_ror_split` and every other keeper flag | as keeper | unchanged | |

Standard ≥5-day extract: `data/raw/campd-unit-outages-NEISO.csv`, **re-derived for 2019–2021** in this
commit (§4), sha256 `aaa3bb379eb7655276401d6d7726cfd783007d81a6eeb7234a879a69c9f85881`.

## 2. Short-coal stays R — the rejection did not run on contaminated inputs

neiso-69 (`results/calibration/FINDING-neiso69-unit-availability-windows-2026-07-28.md`) rejected the
family **on provenance, not fit**: its one 2023 window (Merrimack u2, Feb 1–3) is contradicted by the
unit's own hourly CEMS (it produced in 72 of 72 masked hours, peaking at 441 MW), and the baseload guard
judges Merrimack on 6–10 % of the year. That evidence is CEMS generation, not heat rate — D1 (vintage
tables with no heat rate) could not reach it because NEISO never armed vintage tracking, and D2 (eGRID
2023 for retirees) has no bearing on a detector that reads CEMS operation. F2's extension adds 3 windows
in 2021 and none that answer the provenance objection. **Not re-opened.**

## 3. Two code changes, both gated and inert for every registered run

### 3a. The gas sub-5-day scope is armable without the coal scope

`unit_outage_short_windows_gas` was read only inside the `unit_outage_short_windows` gate
(`data/fleet/arrays.py`), so for NEISO arming it would have meant re-arming the rejected coal family. The
two families are disjoint by plant group (rule 19 — nothing stacks). The fix adds
`coal_scope` (default `True`) to `outages.unit_outage_short_derate_factors` and enters the block when
either flag is set; with the coal flag set the call is byte-identical. **No committed
`run_config*.json` carries `gas=True, coal=False`** (checked over every `results/calibration/*`), so no
registered run moves; cache-epoch ledger entry in `results/cache.py`. Test:
`tests/unit/data/test_outages.py::…::test_gas_scope_armable_without_the_coal_scope`. The ERCOT branch
(`arrays.py` capability-envelope layer) is ERCOT-only and untouched.

### 3b. Mid-vintage-year exits for a vintage with no Retired-and-Canceled sheet

Found by this lane's census, and a defect in the F1 default, not a NEISO quirk. Under
`eia860_vintage_tracks_solve_year` the 2019–2024 fleet is the vintage's **year-end** operable sheet, so a
plant that retired **during** the solved year is absent from it. `mid_vintage_exit_carry` (SPP-48) exists
for exactly that, but it reads the vintage's own Retired-and-Canceled sheet — and **`vintage_2023` /
`vintage_2024` ship none**, so the channel returned `None` there. Measured on NEISO 2024: **Mystic 1588
(1,493 MW incl. its steam parts, retired 2024-06 per EIA) vanished** from the fleet (thermal 23,672 →
21,756 MW; mean unavailable MW 7,512 → 5,517). F1's RESULT said the retiree gap "no longer reaches a solve
(2019–2024 read the vintage operable sheets)"; that is true only of plants retiring AFTER the vintage year.

Fix: `eia860._mid_vintage_exit_rows_from_window` — when the vintage has no retired sheet, the **same
selection rule** (retired in the solved year, in the region, plant absent from the vintage's operable
sheet) is applied to the canonical whole-plant retiree parquet, which carries each unit's EIA retirement
month and its F1 eGRID heat rate. Zero free parameters. Only reachable with `mid_vintage_exit_carry` on AND
a vintage lacking the sheet (2023/2024); the only committed run arming the flag is SPP's 2019–22 rung
(sheets present), so **no registered run moves**. Test: `tests/unit/data/test_mid_vintage_exit_window_fallback.py`.
Measured injections (B): 2019 736 MW (Pilgrim 1590 nuclear, …), 2020 5, 2021 134, 2022 197, 2023 254
(South Meadow, Androscoggin Mill, …), **2024 1,493 (Mystic, Tanner Street, Newark America)**.

`partial_plant_exit_carry` (miso-190) is the unit-grain twin and reads the vintage's retired sheet, which
2019–2022 and the canonical 2025 table carry; injections 8 / 32 / 974 / 882 / — / — / 581 MW
(2019…2025). In 2023–2024 it self-neutralizes (no sheet) — the NEISO exposure there is 1.2 MW (2023) and
80.1 MW (2024: Potter Station 2, Digital Fairfield), **stated, not fixed**. **Other ISOs' R-lanes inherit the
same Mystic-class loss on 2023/2024 unless they arm `mid_vintage_exit_carry`** — reported for them.

## 4. Std extract re-derived for 2019–2021 (F2 FINDING §3 item 5, rule 23)

`derive_campd_unit_outages.py --iso NEISO --years 2019…2025 --merit-order-guard` at HEAD reproduces the
committed 2022–2025 rows **byte-identically and in order**, and adds **+18 / +20 / +4** windows in
2019 / 2020 / 2021 for three plants that joined the fleet / retiree set after the extract was derived:
Capitol District 50498 (10 / 11 / 0), Pawtucket Power 54056 (6 / 6 / 2), West Springfield 1642
(2 / 3 / 2). Installed as a pure addition (42 lines added, 0 deleted; 2018 and 2026 committed rows
untouched); the layup companion regenerates identically in every year and is unchanged. Rule 23: the
data change cited is the fleet / retiree membership change, not a residual. A `.meta.json` sidecar now
records the invocation.

## 5. Phase-0 census (zero LP) — `docs/handoffs/r-neiso/phase0_census.{py,json}`

`run_year(fleet_only=True)` per year, recipe **A** = keeper at this HEAD with F1's vintage + coal/ST/CC
flags forced off (isolates the flag posture; the F1-rejoined eGRID data is read by both), **B** = the
R-NEISO recipe (all eight deltas), **B-nosg** = B without short-gas. Thermal = every unit with a heat rate.

| year | EIA-860 dir A → B | thermal MW A → B | class-table MW, exact (A → B) | any bin-value MW (A → B) | mean unavailable MW A → B | of which short-gas |
|---|---|---:|---:|---:|---:|---:|
| 2019 | `eia-860` → `vintage_2019` | 23,488 → 25,326 | 188.4 → 194.0 | 193.4 → 207.7 | 8,129 → 8,777 | +307 |
| 2020 | `eia-860` → `vintage_2020` | 23,488 → 25,145 | 188.4 → 194.0 | 193.4 → 203.3 | 7,479 → 8,226 | +261 |
| 2021 | `eia-860` → `vintage_2021` | 23,505 → 25,065 | 188.4 → 187.6 | 193.4 → 792.4 | 7,320 → 8,322 | +348 |
| 2022 | `eia-860` → `vintage_2022` | 23,513 → 24,896 | 188.4 → 187.6 | 195.3 → 829.2 | 7,478 → 8,324 | +333 |
| 2023 | `eia-860` → `vintage_2023` | 23,682 → 23,740 | 188.4 → 187.6 | 195.3 → 189.1 | 8,214 → 7,588 | +269 |
| 2024 | `eia-860` → `vintage_2024` | 23,672 → 23,247 | 188.4 → 188.4 | 195.3 → 192.4 | 7,512 → 6,789 | +286 |
| 2025 | `eia-860` → `eia-860` | 23,673 → 24,196 | 188.4 → 188.4 | 195.3 → 264.0 | 7,134 → 7,928 | +344 |

MW @ MW-weighted heat rate (MMBtu/MWh), A → B:

| group | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| COAL | 108 @ 14.20 → 917 @ 10.85 | 108 @ 14.20 → 792 @ 10.76 | 108 @ 14.20 → 696 @ 10.31 | 108 @ 14.20 → 696 @ 10.44 | 108 @ 14.20 → 438 @ 10.70 | 108 @ 14.20 → 438 @ 14.62 | 108 @ 14.20 → 461 @ 12.44 |
| CC_REGULAR | 15,450 @ 8.69 → 15,454 @ 8.90 | 15,450 @ 8.69 → 15,726 @ 8.91 | 15,520 @ 8.71 → 15,800 @ 8.87 | 15,520 @ 8.71 → 15,675 @ 8.86 | 15,781 @ 8.71 → 15,581 @ 8.84 | 15,781 @ 8.71 → 15,242 @ 8.67 | 15,781 @ 8.71 → 15,860 @ 8.86 |
| CC_CHP | 544 @ 9.84 → 563 @ 10.07 | 544 @ 9.92 → 563 @ 10.13 | 490 @ 9.91 → 490 @ 9.58 | 490 @ 9.77 → 490 @ 9.67 | 321 @ 9.93 → 321 @ 9.93 | 321 @ 9.93 → 321 @ 9.93 | 321 @ 9.93 → 321 @ 9.93 |
| ST_GAS | 179 @ 10.27 → 1,295 @ 14.08 | 179 @ 10.27 → 1,382 @ 13.83 | 179 @ 10.27 → 1,382 @ 9.88 | 191 @ 10.15 → 470 @ 10.11 | 278 @ 8.37 → 520 @ 7.95 | 272 @ 8.38 → 835 @ 10.86 | 272 @ 8.38 → 296 @ 8.40 |
| CT_PEAKER | 1,280 @ 12.66 → 1,482 @ 11.54 | 1,280 @ 12.74 → 1,482 @ 15.03 | 1,280 @ 12.69 → 1,491 @ 13.74 | 1,277 @ 12.75 → 1,530 @ 12.80 | 1,277 @ 12.78 → 1,121 @ 13.15 | 1,267 @ 12.79 → 1,213 @ 12.83 | 1,268 @ 12.69 → 1,272 @ 12.69 |
| ST_CHP | 32 @ 6.17 → 25 @ 5.96 | 32 @ 6.17 → 23 @ 6.13 | 32 @ 6.17 → 31 @ 5.97 | 31 @ 5.96 → 31 @ 5.97 | 23 @ 6.01 → 22 @ 5.98 | 24 @ 6.31 → 23 @ 6.31 | 24 @ 6.31 → 24 @ 6.31 |
| CT_CHP | 72 @ 6.69 → 159 @ 5.59 | 72 @ 6.70 → 152 @ 5.96 | 72 @ 6.60 → 165 @ 6.27 | 72 @ 6.58 → 163 @ 5.82 | 72 @ 6.63 → 72 @ 6.63 | 74 @ 6.78 → 74 @ 6.78 | 74 @ 6.78 → 81 @ 7.17 |
| (unbinned: oil / nuclear / other) | 5,823 @ 13.42 → 5,430 @ 12.53 | 5,823 @ 13.42 → 5,025 @ 17.04 | 5,823 @ 13.42 → 5,010 @ 15.82 | 5,823 @ 13.42 → 5,841 @ 13.86 | 5,823 @ 13.42 → 5,665 @ 15.53 | 5,823 @ 13.42 → 5,100 @ 13.81 | 5,823 @ 13.42 → 5,882 @ 13.42 |

**Class-table residual (B).** **Exact measure** (a plant with no joined eGRID rate in its vintage table whose loaded rate is a class value): **GenConn Middletown 57068 (oil, 187.6–194.0 MW) in every year**, plus Stamford Health 68586 (0.8 MW, 2024–25) — both on F1's no-eGRID-in-any-vintage list, and neither in any measured artifact (no measured-oil channel exists). **Coarser any-bin-value measure** adds the rows the exact measure cannot see because they come from the retired sheet, which carries no heat rate: the partial-exit carry's oil units in 2021–2022 — **Mystic 7 (1588, 512.4 MW RFO steam, retired 2021-06; in the 2022 fleet only as a zero-availability row)**, Cleary Flood 1682 (26 MW), Bridgeport Harbor's kerosene CT (568, 16.6 MW), oil units at plants 1642 (West Springfield), 1643 and 1631 (~16 MW each) and ≤7 MW behind-the-meter units — and in 2025 the same rows as dead (retired-before-2025) entries. Bridgeport Harbor 3 **coal** itself is carried at its measured CAMPD rate. The residual is oil steam and CT capacity: NEISO has no measured-oil heat-rate mechanism, and joining eGRID's PLANT rate onto a retired unit of a mixed plant would give Mystic 7 the CC's 7.6 — worse than the class value. **Stated and routed, not fixed** (successor: a unit-grain measured oil/ST rate for retired-sheet rows).

**Reading the table.** A → B is the vintage switch plus the carries plus the measured rates. COAL: the keeper carried **108 MW in every year** (one Merrimack unit — the canonical 2025ER table's state); the vintages carry Merrimack's both units (438.5 MW) plus Bridgeport Harbor 3 (257.6 MW, to 2021-05) and Schiller (2367, 95 MW, 2019–20), at measured rates. ST_GAS / unbinned swaps (Newington 8002, Canal 1599, New Haven Harbor 6156, Middletown 562) follow each vintage's reported primary fuel and operating status — Middletown is absent from the keeper's fleet in every year and present in 2019–2024. The unavailable MW column counts a carried unit as unavailable after its retirement month, which is why the carries raise it; the short-gas column is the pure availability effect of the new family (+261 to +348 MW mean, ~1.7–2.0 % of the gas fleet, matching F2's table).

## 6. G-DRIFT (rule 29(b)) — keeper `fda9ece3` → `9210075`

`fda9ece3..40f4ed7a` was audited by neiso-113 (`docs/RESULT-neiso113-bench-refresh-2026-09-24.md` §1):
every hunk INERT for NEISO except the EIA-923 benchmark builder (post-LP, BENCHMARK). `40f4ed7a..9210075`:

| commit / hunk | verdict | reason |
|---|---|---|
| F1 `59ba7ca9` / merge `ca208aa9` — `egrid.py`, `eia860.py`, `campd_bins.py`, `chp.py`, `runner.py`, `run_calibration*.py`, `scenarios.py` defaults, `heat_rate_years.py`, + the re-joined EIA-860 tables and measured artifacts | **LIVE (by design)** | the input correction this lane exists to solve on |
| F2 `4efebee0` — `campd.py` merit-panel pin | INERT | deriver-only (`merit_panel_states_for_iso`), SPP / SOCO scoped |
| F2 data — `campd-unit-outages-shortgas-NEISO.csv`, `-short-NEISO.csv` (+3 rows), layup companions | **LIVE** (short-gas, armed here) / INERT (short-coal, stays off) | |
| pjm-h22 `da9fc148` — `capacity_market.py` RGGI zone shares, `fuel_trajectories.py` PJM allowance price 2020–22 | INERT | PJM tables only; NEISO's RGGI price rows untouched |
| Y-28 `bb749a94` — cache-key registration of an existing field | INERT | key bookkeeping, no behaviour |
| Y-29 / Y-30 — gate-(a) rows, import-cycle break (`model/lp/model.py`), ruff | INERT | governance / AST-equivalent import |
| `6831b110` storage dispatch comparison, `forecast_parity_registry.py` | INERT | report-only / forecast registry |
| this commit — `outages.py` / `arrays.py` `coal_scope` | **LIVE** (only via the armed gas flag) | §3a |
| this commit — `eia860._mid_vintage_exit_rows_from_window` | **LIVE** (only via the armed carry, 2023/2024) | §3b |
| this commit — std extract rows 2019–2021 | **LIVE** (2019–2021 only) | §4 |

Form 4 stands: the committed keeper bundle is the control. Legs are compared to it per year, and every
move is attributed to the LIVE set above.

## 7. Gates — declared before any solve (structural; rule 1)

A failing gate does not kill the recipe and a passing one does not promote it: this is an owner-ordered
input correction, and a faithful input that makes the fit worse stays (rule 14 → root-cause the gate).

- **G1 — the recipe is what was declared.** `shard_check.py` passes on every leg: scenario_config =
  keeper + exactly §1's eight flips (plus `weather_year` / `gas_price_override` for 2019); offer curves
  byte-identical; std extract sha256 as §1; classifier `02c3f7710de08661`.
- **G2 — the inputs are live.** Each leg's log shows the short-gas line `(coal off, gas on)` with a
  plant-tranche count > 0 and the mid-vintage / partial-exit carry lines with §3b's MW; the census
  (§5 B) is the prediction of the fleet each leg dispatches.
- **G3 — no silent breakage.** C1, C2, C3a, C3b, C4, C8 re-scored per year against the keeper with the
  same scorer and the committed bench held fixed (`screen_collateral_gate.py` on the composite); C3c
  reported. Every move reported at full magnitude; a PASS→FAIL flip opens a root-cause question and is
  not a kill.

## 8. Shard plan — one shard per year (rule 36), full bundle pushed (rule 34(a))

Seven shards, 2019–2025, launched at once, each pinned to **this doc's commit SHA** (recorded in §9).
Out-dir `results/calibration/rneiso_<Y>/`, branch `claude/rneiso-<Y>`. Each runs:

```
python3 scripts/hydrate_data.py --profile neiso   # no-op on a full clone
uv run python scripts/data/curate_hydro_plant_modes.py --iso NEISO
MARKET_SIM_WARMSTART_XYEAR=0 MARKET_SIM_P1_BASIS_SEED=0 uv run python scripts/replay_keeper.py \
  results/calibration/hydro5_neiso_ror_span --years <Y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_ct_heat_rates=true \
  --set measured_chp_heat_rates=true --set measured_st_heat_rates=true \
  --set measured_cc_heat_rates=true --set measured_coal_heat_rates=true \
  --set unit_outage_short_windows_gas=true --set unit_partial_outage_windows=true \
  --set mid_vintage_exit_carry=true --set partial_plant_exit_carry=true \
  --out-dir results/calibration/rneiso_<Y> \
  --note "R-NEISO: keeper + F1/F2 corrected backcast inputs, <Y> (rule 36 single-year)"
uv run python docs/handoffs/r-neiso/shard_check.py --leg results/calibration/rneiso_<Y> --year <Y>
```

The parent fetches each leg, verifies (`git ls-tree` > 0 files, shard_check re-run), composes 2019–2025
(zero LP), attests (keeper DOF ledger inherited, no new DOF, multipliers byte-identical), scores,
registers and updates the NEISO matrix shard. **The parent never solves** (rule 32(a)). Promotion is the
owner's (rule 31): nothing is promoted or pruned by this lane.

## 9. Launch record

All seven pinned to **`c265c1c30ce0e51bffa5e0e5f5db76eafe54ae3e`** (this doc's first commit), created
2026-09-24 17:58–18:00 UTC, tag `r-neiso`. First hard stop in each: `git checkout -B claude/rneiso-<Y> <sha>`
+ `git rev-parse HEAD` equality; no rebase / pull / merge.

| year | shard session | branch / out-dir |
|---|---|---|
| 2019 | `session_01XsUDib96z253kbGH1C2JSi` | `claude/rneiso-2019` / `rneiso_2019` |
| 2020 | `session_01FNuQqbLFifsLPbTLXuKjCG` | `claude/rneiso-2020` / `rneiso_2020` |
| 2021 | `session_01Fm3gGxsL6k4dWbDSPZksNE` | `claude/rneiso-2021` / `rneiso_2021` |
| 2022 | `session_0179ZMfFdxfwJ74YS2S5kkpN` | `claude/rneiso-2022` / `rneiso_2022` |
| 2023 | `session_01Vpv11ZARtXNrh7vkRsmNLz` | `claude/rneiso-2023` / `rneiso_2023` |
| 2024 | `session_01Nwioy6utrNLDqjWBbCM5Wb` | `claude/rneiso-2024` / `rneiso_2024` |
| 2025 | `session_01HFxkUpJf4Vya9x5BGEkqKg` | `claude/rneiso-2025` / `rneiso_2025` |
