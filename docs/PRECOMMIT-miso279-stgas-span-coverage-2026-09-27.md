# PRECOMMIT — miso-279: ST_GAS rows for gas-steam bins the 2023–2025 tranche window never measured

```
LANE    : miso-279 (handoff candidate A, owner pick 2026-09-27; rule 28(a) on-queue: FINDING-miso276 §2 route,
          RESULT-miso278 §3 residual cause (ii))
KEEPER  : 2026-09-27-miso-278-fuelsplit (results/calibration/miso278_span, 2019-2025), legs solved at 257d3c6f
ARM     : keeper recipe + campd_st_gas_span_coverage = true (new field, default False; sub-gate of the keeper's
          campd_unit_fuel_split)
CONTROL : none solved. G-DRIFT 257d3c6f..<pin> (§3); the keeper bundle IS the control (rule 29(b) form 4)
SHARDS  : 7 legs, one year each 2019-2025 (rules 34(c), 36), pinned to this document's commit SHA
DATA    : DATA PROFILE: miso — no intake; four derived '-fuelsplit-stcov-' companions committed before this document
DOF     : +0 (CAMPD primaryFuelInfo/unitType + EIA-860 vintage fleets + the frozen estimator; no parameter)
```

## 1. The object (rule 23 trigger = source coverage, never the C1 residual)

The tranche family is derived over a pooled 2023–2025 window. An ST_GAS bin whose boilers ran only before it has no
row, hence no measured `st_gas_mustrun_per_plant` floor. The backcast span now reaches 2019, where those units ran.
Census and sizing: `docs/FINDING-miso279-stgas-span-coverage-2026-09-27.md` §1 (ceiling ~1.5 TWh of the 2019 gap).

## 2. The delta

- **Derive** `--st-gas-span-coverage` (`st_gas_span_coverage_rows`): for every plant with an ST_GAS vintage bin in
  any of 2019–2025 and no ST_GAS row in the fuel-split companion, route each CAMPD unit on its own fuel and
  prime-mover family over ALL the plant's bins (so Teche's CT stays off the steam bin) and emit the ST_GAS row only.
  Shared estimator `_routed_family_rows` (factored out of miso-278's `unit_fuel_split_rows`; regenerating the four
  fuel-split companions after the refactor reproduces them and their sidecar byte-identically).
- **Companions**: each is the fuel-split companion's exact bytes + appended ST_GAS lines (8 pooled rows, 72 per-year,
  8 p25, 8 oom). Pinned by `tests/unit/data/test_campd_st_gas_span_coverage.py`.

  | companion | sha256 |
  |---|---|
  | `thermal_tranches-fuelsplit-stcov-MISO.csv` | `19f185be1ffec528e0a457979f326d7f65041f2bd4bf3966d855ec1ffcca5e04` |
  | `thermal_tranches_online_frac_by_year-fuelsplit-stcov-MISO.csv` | `532e72f135987a25f87fbac43d32b1a81282169cd8566c0b62bfe2f1ae7a5a12` |
  | `thermal_tranches_p25_level_mw-fuelsplit-stcov-MISO.csv` | `69e7c80ac2a9105b8aa7157ebc0e67ea19ad5ea142ea759cefefa2c3906fd9ee` |
  | `thermal_tranches_oom_level_mw-fuelsplit-stcov-MISO.csv` | `2d26face2c1b9d882c063d338309682491cf553297317d98f67fbac46ecc3260` |

- **Gate** `campd_st_gas_span_coverage` (default False, `_CACHE_KEY_OPTIONAL_FIELDS`): `campd_fuel_split_selector`
  returns the tag `"stcov"` only when BOTH fields are armed; otherwise the same `True`/`False` as before, so every
  keeper's readers, lru keys and cache key are unchanged. `_fuel_split_companion` resolves the stcov file for all four
  readers at once (falls back to the fuel split, never past it).

## 3. G-DRIFT — `257d3c6f..<pin>`

Tree diff over `src/market_sim`, `scripts/run_calibration*.py`, `scripts/lib`, `data/raw/_validation-source`,
`data/raw/reference`.

| hunk | class | reason |
|---|---|---|
| `data/raw/reference/custom-bin-assignments.csv`, `ercot-dam-*` (R-ERCOT-8) | INERT | ERCOT bin sheet / DAM crosswalks |
| `nyiso_li_seam_posted_limit_cap` (run_calibration, run_calibration_full, nyiso_seam_envelope, scenarios) | INERT | NYISO-only, default False, absent from keeper |
| `coal_fuel_inventory_take_floor` (coal_fuel_inventory, run_calibration, LP layout/bounds/costs/rows/model, pipeline spec, `COAL_PLANT_GRAIN_ISOS` += NWPP) | INERT | default False; `resolve_coal_take_floor` raises outside NWPP; `n_take_slack` 0 ⇒ layout unchanged; `yard_keys` is provenance only |
| `unit_outage_full_rederive` (outages, arrays, scenarios) | INERT | default False, absent from keeper; falls through to today's file |
| CAISO WECC import blocks 2019–2021 (interchange/spec) | INERT | CAISO-keyed |
| `forecast_parity_registry` | INERT | declaration table |
| **miso-279 gate + companions** | **LIVE, the delta** | reached only under `campd_st_gas_span_coverage` |
| miso-279 derive refactor (`_routed_family_rows`) | INERT | derive-time; fuel-split output byte-identical, measured |

All non-delta hunks INERT → form 4 holds. The Riverside CAMPD remap (55641 CT-03/04 → 64020) is still held out.

## 4. Zero-LP footprint

FINDING §3: ST_GAS floor +0.839 / +0.795 / +0.312 / +0.311 / +0.285 / +0.005 / +0.006 TWh (2019–2025); no other
group's floor moves; ST_GAS pmax unchanged.

## 5. Predictions (directions and bounds only)

1. ST_GAS energy rises by at most the floor delta in each year (≤ ~0.8 TWh 2019–20, ≤ ~0.3 2021–23, ~0 2024–25).
   Direction of C1 ST_GAS: closer in 2019–2023. Whether C1 2019 crosses its band is **not** a criterion here (rule 1).
2. Coal/CC fall by about the same energy; prices move by a few cents.
3. D-4 unit-conduct exposure at Teche 1400 in 2023 (pooled window over its own 2023 CEMS) — reported, not hidden.

## 6. Decision rule (fixed now)

S-1 recipe = keeper + exactly `campd_st_gas_span_coverage` (shard check HARD 1); S-2 the leg read the four pinned
`-fuelsplit-stcov-` companions (HARD 1b); S-3 inputs/vintage/classifier/log as miso-278. C1–C8 reported per year at
full magnitude vs the keeper. Promotion is the owner's (rule 31); no criterion selects it (rule 1). The structural
case is rule 14/23: a measured row where the window left none.

## 7. Arm command (per year Y, one shard each)

```
python scripts/replay_keeper.py results/calibration/miso278_span --years <Y> \
  --set campd_st_gas_span_coverage=true \
  --out-dir results/calibration/miso279_arm_<Y> \
  --note "miso-279 arm <Y>: ST_GAS span coverage of the fuel-split tranche family"
```

Shard check: `scripts/probes/_miso279_shard_check.py --leg results/calibration/miso279_arm_<Y> --year <Y> --log <log>`.
Compose: `scripts/probes/_miso279_compose_span.py`.

## 8. Launch record

Launched 2026-09-27 22:12–22:15 UTC, all pinned to `47d3f8727fa86f51e5c061273cc1c7c6094d3654`, tagged `miso-279` /
`shard`, auto-PR off. Each pushes `claude/miso279-arm-<Y>` from out-dir `miso279_arm_<Y>` (full bundle incl.
`dispatch/<Y>_P1.parquet`, gitignore negation + plain `git add`, rule 34(a)).

| year | session |
|---|---|
| 2022 (first, slow leg) | `session_018RZe1xJ2sv7E1gd1JiMcXG` |
| 2019 | `session_01U3r6VSU8M8mKvMRaJBWi53` |
| 2020 | `session_01RCbDPaq9iVcQc1ze7mAhP6` |
| 2021 | `session_01NTQoF7rPppUWfc1VGWWkzF` |
| 2023 | `session_01H6Ds4g19YFoqdbBuCb5mEa` |
| 2024 | `session_01VweC5oX3LNcPEDYQTd9wtU` |
| 2025 | `session_017iCavjoRbJbnjdmrhGUM6X` |
