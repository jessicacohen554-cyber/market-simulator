# FINDING — I-SOCO: SOCO 2019–2022 input intake (manifest row 9)

**Lane:** I-SOCO (data intake). **Date:** 2026-09-24. **Base:** `origin/main` @ `8ebb7805`.
**Charter:** owner instruction 2026-09-24, "every ISO's backcast covers 2019–2025 on year-correct
inputs" (`docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md`). Work list: the
missing-input table of R-SOCO's `docs/handoffs/r-soco/PRECOMMIT-r-soco-2026-09-24.md` §2 (branch
`claude/r-soco-2019-2025-inputs`), which refused 2019–2022 with
`ValueError: No EIA-930 data for ISO 'SOCO' in year 2022`. SOCO addition plan §6 **row 9**.
**LP spent: ZERO.** Nothing solved, scored or registered; no keeper, matrix or dashboard file touched.
**DATA PROFILE:** soco (+ shared).

---

## 0. Headline

The blocker is gone. `run_year(Y, "SOCO", fleet_only=True)` on the soco61 keeper recipe
— which exits at `run_calibration.py:5816`, after demand, zonal shares, renewables, hydro, fuel,
outage and fleet assembly — now completes for **2019, 2020, 2021 and 2022**, reading the new solar shape and both FERC-714
files with no skip or fallback warning (before, 2022 raised at the first loader). Every input the PRECOMMIT's table names landed for 2019–2022 with the producer that
built 2023–2025, and **every committed 2023–2025 row regenerates byte-identically** (§2). Two items
did not land and are stated in §3; neither is a solve input. Three **source-side facts** a
2019–2022 solve must know are in §4 — the first of them is live on the solve path.

## 1. What landed

| # | input | file(s) | producer | 2019–2022 |
|---|---|---|---|---|
| 1 | EIA-930 SOCO hourly (demand, `NG:*` benchmark, `Total interchange`) | `eia-930-hourly/SOCO hourly.parquet` | `extend_eia930_hourly_from_balance.py --ba SOCO --year 2019..2022` (committed BALANCE archive; no network) | +35,057 rows |
| 2 | FERC-714 zonal demand (zonal shares) | `zone-specific-demand/SOCO/soco_ferc714_hourly_planning_area_demand_2019-2022.parquet` | PUDL nightly; `slice_soco_ferc714_pudl.py` (NEW — SOCO-11's hand slice, committed) | 280,505 rows |
| 3 | BA-to-BA interchange | `eia-930-interchange/SOCO interchange hourly.parquet` | `fetch_eia930_interchange.py --ba SOCO --source bulk --merge` (keyless) | +338,951 rows |
| 4 | delivered gas AL / GA / MS | `gas-prices/eia_delivered_gas_{AL,GA,MS}_monthly_2019-2022.csv` | `cut_eia_state_delivered_gas_xls.py` (NEW — SOCO-12's hand transcription, committed) from the committed dnav workbooks | 48 months each |
| 5 | zonal gas hub | `soco_zonal_gas_hub.csv` | `derive_soco_zonal_gas_hub.py` (`YEARS` → 2019–2025) | +12 rows |
| 6 | solar zone shape | `soco-solar-shape/soco_<Y>_solar_zone_shape.parquet` | `build_soco_solar_shape.py --years …` (NASA POWER, keyless) | see §1.1 |
| 7 | calibration reference + renewable-capacity benchmark | `_validation-source/calibration_reference.json` (SOCO block), `SOCO_<Y>_renewable_capacity.csv` | `build_calibration_reference.py --isos SOCO` (`CALIBRATION_YEARS_BY_ISO["SOCO"]` → 2019–2025) | 4 blocks + 4 CSVs |

Already present before this lane (F1/F2 or older), re-verified by the fleet trace: CAMPD CEMS AL/GA/MS
2019–2025, the four CAMPD outage families, EIA-860 vintages 2019–2024, EIA-923 monthly generation /
fuel costs 2018+, the CAMPD/CHP/eGRID heat-rate artifacts (per-year rows 2019–2025), the EIA-923
hydro budget (2022: 42 plants, 8.03 TWh).

Code changes, all under `scripts/data/` (no `src/`, no `ScenarioConfig`, no cache-key move):

* `extend_eia930_hourly_from_balance.py::extend_ba` — casts each new column to the extract's own
  dtype. Without it the all-`pd.NA` new-taxonomy columns (`NG: BAT/PS/SNB/OES`) upcast the
  **committed** rows float32 → float64. Test: `tests/curation/test_extend_eia930_hourly_from_balance.py`
  (fails on the old code, passes on the fix).
* `curate_zonal_shares.py` — reads every present file in `_SOCO_FERC714_FILES`. Test:
  `test_year_split_across_the_two_committed_pulls`.
* `derive_soco_zonal_gas_hub.py` — `YEARS` widened; `--cross-check` reads every per-state window.
* `build_calibration_reference.py` — `CALIBRATION_YEARS_BY_ISO["SOCO"]` widened.
* NEW `slice_soco_ferc714_pudl.py`, `cut_eia_state_delivered_gas_xls.py` — the two hand-built
  2023–2025 artifacts now have committed producers, each with a `--check` that proves the committed
  window.

### 1.1 Solar shape

`python scripts/data/build_soco_solar_shape.py --years 2023 2019 2020 2021 2022 2024 2025 --reconcile`
(NASA POWER all-sky DNI/DIFF at every operable solar plant, keyless). Every built year places at a
**zero-hour best shift** against EIA-930 `NG: SUN`:

| year | generators | AL / GA / MS MW | r at shift 0 | built vs measured mean hour |
|---|---:|---|---:|---|
| 2019 | 81 | 217.2 / 1,461.9 / 158.0 | 0.9667 | 11.12 vs 11.13 |
| 2020 | 109 | 291.7 / 2,193.5 / 158.0 | 0.9842 | 11.10 vs 11.09 |
| 2021 | 120 | 366.2 / 3,063.4 / 158.0 | 0.9770 | 11.08 vs 11.09 |
| 2022 | 131 | 440.7 / 3,625.2 / 158.0 | 0.9859 | 11.07 vs 11.06 |

Each 2019–2022 file is 8,760 rows, no NaN. The rebuilt 2023/2024/2025 frames equal the committed
ones exactly; only the parquet writer metadata bytes differ, so the committed 2023–2025 files are
kept as landed (not rewritten).

## 2. Byte-identity proofs (every committed 2023–2025 row)

| input | proof | result |
|---|---|---|
| `SOCO hourly.parquet` | committed 26,304 rows vs the same rows in the extended file (`assert_frame_equal`, exact); schema dtypes compared | **identical**, schema unchanged |
| — same-producer check | BALANCE path rebuild of the legacy-taxonomy era 2023-01 .. 2024-06 (13,134 rows) vs committed | **exact on all 16 value columns + UTC/local time**; only diff the committed file's own `Hour` label 1..7 on 7 local-2022-12-31 rows (kept untouched). 2024-07 onward the routes diverge (EIA taxonomy revamp/revisions) — no such row is rewritten |
| FERC-714 2023–2025 | `slice_soco_ferc714_pudl.py --check` on today's nightly | 0/0 row-set diff; **`demand_reported_mwh` and 5 other columns identical, same order, all 210,431 rows**; `demand_imputed_pudl_mwh` (PUDL-derived, read by nothing) moved ≤ 1.06 MWh between nightlies — committed file left as landed |
| zonal shares 2023–2025 | old parser + old extract vs new parser + both 714 files + extended extract | **byte-identical** `(3, 8760)` arrays, all three years |
| interchange | `--years 2023 2024 2025` re-fetch into scratch vs committed | **exact frame** (incl. category set); post-merge every committed row present unchanged |
| delivered gas CSVs | `cut_eia_state_delivered_gas_xls.py --check` | **byte-identical** (AL, GA, MS) |
| zonal gas hub | committed CSV lines vs regenerated | **9/9 committed rows byte-identical** |
| calibration reference | JSON SOCO 2023/2024/2025 blocks, `egrid_benchmark`, every other ISO | **identical** (only `generated` date moves); `SOCO_202{3,4,5}_renewable_capacity.csv` untouched by the rebuild |
| solar shape | rebuilt 2023/2024/2025 frames vs committed | **frame-exact** (`assert_frame_equal`, all 8,760 × 4, all three years); committed file bytes kept |

Tests: 296 passed across the 16 test files touching these producers (incl. the two new tests).

## 3. Not landed — stated, not proxied

1. **`SOCO_{region,fueltype}.parquet` (EIA-930 API long files) — producer needs `EIA_API_KEY`,
   unset in this container.** `fetch_eia930_long.py` is API-only. These files are an OPTIONAL
   gap-fill (`eia930.frames`: NaN hours of the wide extract are filled from them when present,
   otherwise pass through to the loaders' interpolation). No ISO carries them before 2023, and the
   2019–2022 wide extract has 25 NaN hours (all 2019) — bridged and logged by the loader. Not a
   blocker. A keyed session can run `fetch_eia930_long.py --ba SOCO --start 2019-01-01 --end
   2022-12-31` if the owner wants them.
2. **`reference/soco_seam_*.csv` — left at 2023–2025, unchanged.** Derive-only (they "arm nothing";
   no solve reads them — the SOCO seam is the served BA `Total interchange`). Their generator exists
   only as a listing inside `FINDING-soco-33-2026-09-16.md`; it reproduces all five committed files
   byte-for-byte on the pre-intake inputs, but (a) `hr_elasticity` is ONE fit over its year set, so
   any widening moves every committed row by construction; (b) the only anchor (MISO-South LMP) is
   absent before 2022 and the generator's own guard refuses; (c) the widened interchange file now
   carries the hour-ending `2023-01-01 00:00` record (2022's last hour) and the generator buckets
   by `local_time.dt.year`, so its 2023 duration / limit / served rows would move by that hour, and
   its 2019–2021 `AEC` leg divides by zero. Extending the family means fixing the generator's
   year convention — a change to committed 2023 numbers, which is the SOCO-56 lever lane's call,
   not an intake's. **Consequence of this intake, stated:** the doc-embedded generator no longer
   runs as-is against the widened interchange file.

## 4. Source-side facts a 2019–2022 SOCO solve must know

1. **LIVE ON THE SOLVE PATH — EIA's 2019 Jan–Aug SOCO `Total interchange` is sign-inverted.**
   Monthly TI is the exact negative of `Net generation − Demand` and of the sum of the nine DIBA
   legs (Jan −300 vs +300 GWh … Aug −369 vs +369); Sep–Dec all three agree. Annual 2019 TI
   −1.588 TWh vs legs +6.640 TWh. EIA's LIVE `EIA930_BALANCE_2019_Jan_Jun.csv` (Last-Modified
   2026-09-24) carries it too, so it is the publisher's. 2020–2022 TI = legs to 0.001 TWh. The SOCO
   keeper serves `eia930.envelopes.soco_net_interchange(year)` = this column, so **a 2019 solve
   would model SOCO as a net importer Jan–Aug** unless the solve lane decides a repair (the
   identity `TI = NG − D` and the independent legs both give the correct sign). Raw left immutable.
2. **PowerSouth (`AEC`) joined the SOCO BA on 2021-09-01.** The `AEC` interchange leg runs
   2019-01-01 .. 2021-09-01 00:00 and stops; EIA-860 vintages code PowerSouth's six plants `AEC`
   in 2019–2021 and `SOCO` from 2022. So 2019–2020 are self-consistent (load and plants both
   outside), but **Sep–Dec 2021 EIA-930 demand includes PowerSouth load while the vintage-2021
   fleet excludes its plants.**
3. **Delivered-gas state series are mostly withheld 2019–2021** (AL/MS publish 2022 only; GA
   misses Apr–Dec 2021). This does not reach the solve — the zone basis is the per-plant EIA-923
   route, which covers every year — but a cross-check reader will see it.

Also measured, not repaired: 2019 carries one 6,913 MW demand hour against a ~16 GW floor in every
other year; the soco_gas_st campaign parameters the keeper arms are a pooled 2023–2025 measurement
keyed per plant (`load_gas_st_campaign_params(iso)` is year-free), so they apply to 2019–2022 as
measured on 2023–2025.

## 5. For the successor (R-SOCO 2019–2022 legs)

Run `scripts/data/curate_demand_profile.py` (writes the gitignored clean `demand-profile` SOCO
2019–2025; `build_calibration_reference` and `load_demand_meta` read it) and
`curate_hydro_plant_modes.py --iso SOCO` before solving, as the PRECOMMIT's recipe already does.
Decide §4.1 before launching 2019. Then one shard per year (rule 36) on the PRECOMMIT §5 recipe.
