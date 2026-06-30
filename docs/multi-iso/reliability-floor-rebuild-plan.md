# Temperature-Driven Reliability Mechanism — Full Rebuild Plan

**Status:** IMPLEMENTED — merged and deployed across all six ISOs (2026-06-30).
**Branch:** `claude/temp-reliability-mechanism-yo6zgc`
**Goal:** Replace the narrow, window-gated, partly outcome-pinned "reliability floors"
with ONE honest, structural, temperature-gated engine covering **every model zone ×
every fossil class** across **all six ISOs**, with each (zone, class) limb
independently toggleable.

This plan satisfies CLAUDE.md #1 (right structure first), #9/#11 (physical inputs
that regenerate forward; never pin to measured outcomes), #12/#13 (dashboard + full
year spans).

---

## 0. Motivation recap (what is wrong today)

The current mechanism (generic `inject_reliability_floor` + `ReliabilityFloorSpec`
registry, plus five legacy injectors) is:

1. **Window-gated** — floors apply only inside arbitrary hour-of-day windows
   ("funky windows": MISO hot HB14–20, MISO/NEISO cold {6,7,8,9,17,18,19,20},
   CAISO HB15–22, NYISO HB14–21, NEISO HB16–21). Physically a committed boiler runs
   the *whole day*, not 14:00–20:59.
2. **Narrow** — only CT_PEAKER / ST_GAS (+ NEISO cold COAL), in a handful of zones,
   often **pooled** where it should be zonal.
3. **Outcome-leaning** — `cap = measured-CF p97` is a measured-outcome ceiling; the
   `ct_mustrun_per_plant` (EIA-923) and `ct_deployment_overlay` (CEMS) floors pin to
   realized generation. These are calibration crutches with no forward analogue.
4. **CAISO floor is net-load-driven**, not temperature-driven — inconsistent with the
   stated physical mechanism.

The fix is **not** to delete the temperature signal — it is to make it honest and
broad: every zone, every fossil class, transparent coefficients, full-day step-gate,
toggleable limbs.

---

## PART A — Temperature data for all six ISOs, every model zone

### A.1 Model zones (confirmed from `config/iso_configs.py`)

| ISO | Floored model zones (fossil-bearing) | Skipped |
|-----|--------------------------------------|---------|
| ERCOT | West, North, Northeast, Houston, South_Central, South | **Panhandle** (load_share 0, no fossil bin) |
| CAISO | NP15, ZP26, SP15 | WECC_import (import node) |
| PJM | PJM_ComEd, PJM_AEP_Ohio, PJM_ATSI, PJM_West_APS, PJM_Central_PA, PJM_Dominion, PJM_EMAAC, PJM_SWMAAC | — |
| MISO | MISO-North, MISO-Central, MISO-South | — |
| NYISO | Upstate_West, Capital_Hudson, Lower_Hudson, NYC, Long_Island | — |
| NEISO | North, Central, Boston, Connecticut | HQ_import (import node) |

Pure import nodes (WECC_import, HQ_import) carry no load/fossil → no weather, no floor.

### A.2 Canonical schema (MISO's, applied to all)

`data/raw/<iso>-weather/<iso>_zone_temp_daily.csv` with columns:
```
date,zone,tmax_c,tmin_c
```
One row per (zone, date). Covers **2023-01-01 … 2025-12-31** (CAMPD-scored span; extend
as years land). Forecast years pin a weather year → same zonal series regenerates
(CLAUDE.md #10).

### A.3 Station-weight table (checked-in, reproducible)

New reference file `data/raw/reference/iso_zone_weather_stations.csv`:
```
iso,zone,station_id,weight,station_name
```
mirrors the hard-coded `MISO_ZONE_STATIONS` / `NEISO_TMAX_STATIONS` dicts but for ALL
zones. Existing MISO/NEISO/NYISO weights are migrated in verbatim. New ERCOT/PJM/CAISO
zonal weights use major load-center airport GHCN stations (load-weighted by metro share
within the zone). Representative station map (exact GHCN IDs finalized in the table):

- **ERCOT** West→Midland (USW00023023); North→Dallas-FW (USW00003927); Northeast→Tyler/Longview;
  Houston→Bush IAH (USW00012960); South_Central→Austin (USW00013904)+San Antonio (USW00012921);
  South→Corpus Christi (USW00012924)+McAllen.
- **PJM** ComEd→Chicago O'Hare (USW00094846); AEP_Ohio→Columbus (USW00014821);
  ATSI→Cleveland (USW00014820)+Akron; West_APS→Pittsburgh (USW00094823);
  Central_PA→Harrisburg (USW00014711); Dominion→Richmond (USW00013740)+Norfolk;
  EMAAC→Philadelphia (USW00013739)+Newark (USW00014734); SWMAAC→Baltimore (USW00093721)+DC (USW00013743).
- **CAISO** NP15→Sacramento (USW00023232)+San Francisco (USW00023234);
  ZP26→Fresno (USW00093193); SP15→Los Angeles (USW00023174)+San Diego (USW00023188).
- **MISO/NYISO/NEISO** migrated from existing derive-script dicts (split NEISO pool into
  the 4 zones: North→Portland ME/Concord/Burlington; Central→Worcester/Providence;
  Boston→Logan; Connecticut→Bradley).

### A.4 Generic fetch/derive script

New `scripts/fetch_zone_temperature.py` (replaces the per-ISO `fetch_*` halves):
```
python scripts/fetch_zone_temperature.py --iso ALL          # or --iso ERCOT PJM …
        [--start 2023 --end 2025] [--no-fetch]
```
- Reads `iso_zone_weather_stations.csv`.
- Fetches NOAA GHCN-Daily per station via the **access CSV** endpoint
  `https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/<station>.csv`
  (confirmed reachable through the agent proxy; HTTP 200) — falls back to the v1 JSON
  service the existing scripts use. TMAX/TMIN are tenths °C → ÷10.
- Load-weights per zone, writes `data/raw/<iso>-weather/<iso>_zone_temp_daily.csv`.
- `--no-fetch` re-derives from a cached raw pull (CI / offline dev).

Migrates pooled CAISO/NYISO/NEISO files to true per-model-zone series (the old
single-series files are deleted; `iso_zone_tmax` updated to the unified path).

### A.5 `eia_loader.iso_zone_tmax` extension

`iso_zone_tmax(iso, year, hours, zone) -> (tmax, tmin)`:
- `_WEATHER_FILES` collapses to one canonical per-ISO path
  `<iso>-weather/<iso>_zone_temp_daily.csv` (per-zone, tmax+tmin).
- Keeps the daily→hourly broadcast (day-of-year lookup) and `ffill/bfill` gap fill.
- Returns `None` when a forecast year has no pinned weather (engine no-ops → graceful
  fallback; unit-tested).

---

## PART B — Honest per-(zone × class) coefficients

### B.1 Class set (from `config/plant_taxonomy.py`)

Fossil classes the engine can floor:
`COAL` (+ ranks COAL_PRB/COAL_BIT/COAL_LIGNITE/COAL_WC), `CC_REGULAR`, `CC_CHP`,
`CT_PEAKER`, `CT_CHP`, `ST_GAS`, `ST_CHP`, and `oil` (oil/oil-steam — note: current
taxonomy lumps all oil into `oil` regardless of prime mover; we floor `oil` as one
class and document the lack of an oil-steam split).

### B.2 Measured class daily CF per zone

Reuse the derive-script helpers (`_zone_class_daily_cf` / `_class_daily_cf`):
1. Get the per-plant **(zone, plant_group, nameplate)** from the **model's own fleet
   builder** — `bin_assignments_<ISO>.csv` (CAISO/MISO/NEISO/NYISO),
   `custom-bin-assignments.csv` (ERCOT), and for **PJM** via
   `data.zone_assignment.build_zone_lookup` + `classify_plant`. Using the model's own
   nameplate as the denominator guarantees the floor is expressed on the same basis the
   LP dispatches on.
2. Join CAMPD unit-level `grossLoad` (`data/raw/campd-unit-level/<STATE>_<year>.parquet`)
   by `facilityId` → daily group MWh.
3. Daily group CF = group MWh / (group nameplate × 24). On a *when-available* basis for
   classes where CAMPD outages materially derate (mirror NYISO ST treatment) so the
   floor is not double-discounted by outages.

### B.3 Regression / coefficient extraction (the honest part)

For each (zone, class), regress daily CF on the zone's daily **TMAX** (hot limb) and
daily **TMIN** (cold limb) and extract:

- **`hot_tmax_c`** — the TMAX threshold where group CF begins to climb above its
  mild-day baseline (day-gate onset). Default prior 25 °C; derived per (zone,class).
- **`cold_tmin_c`** — the TMIN threshold for cold-snap commitment. Physically-grounded
  priors COAL≈5 °C, ST_GAS≈0 °C; derived per (zone,class).
- **`floor_pct`** — decomposed into two physical/structural halves (this is how real
  UC models behave: commit a unit, then enforce `P ≥ Pmin`):
  `floor_pct(group) = commit_frac × min_stable_pct`
    - **`min_stable_pct`** = physical min-stable level (Pmin/Pmax) of the class, from
      bin `Pct_Must_Run` / turbine min-load specs (Handoff #2 physical min-run research).
    - **`commit_frac`** = share of the class's *capacity that is online* on flagged
      days (a commitment count from CAMPD `grossLoad > 0`, NOT an energy/CF ceiling).
      Structural — regenerates for a forward year and responds to weather.
  The result is a floor the LP must meet and may dispatch *above* economically. The
  deprecated p97-CF ceiling is gone.
- Diagnostics reported but **not** baked into the floor: linear `slope`, Spearman ρ,
  sample size `n`, mild-day baseline.

**Enable/disable rule (no forced limbs):** a limb is `enabled=True` only when the
temperature response is real — ρ above a threshold (e.g. ≥0.3), `n` adequate
(e.g. ≥30 flagged days), and `floor_pct` meaningfully above the mild-day baseline.
Otherwise the limb ships `enabled=False`. Weak/insignificant limbs are visible in the
report and shipped OFF — never invented to plug a residual.

**Guardrail (CLAUDE.md #9/#11):** thresholds and floor_pct are derived from the
TEMPERATURE→commitment relationship only. They are **never** tuned to the price/volume
residual, and floor_pct is **never** set to "measured CF so output matches actuals."
The same coefficients regenerate for a forward year and respond to hotter/colder
weather.

### B.4 Coefficient derivation script + table

New `scripts/derive_reliability_coeffs.py --iso ALL`:
- Emits a full per-(zone, class) coefficient table to
  `data/raw/reference/reliability_floor_coeffs.csv`
  (`iso,zone,plant_class,limb,hot_tmax_c,cold_tmin_c,floor_pct,enabled,slope,rho,n,baseline`)
  AND a human-readable markdown report `docs/multi-iso/reliability-floor-coefficients.md`
  with sample sizes and fit quality so weak limbs are visible.
- The registry in `iso_configs.py` is generated/seeded from this CSV (single source of
  truth), so re-deriving is reproducible.

---

## PART C — The mechanism (clean, full-day, customizable)

### C.1 Day gate (no hour-of-day windows)

For (zone, class) limb with the day's zonal daily temps:
- **hot day** ⇔ `tmax_c > hot_tmax_c`
- **cold day** ⇔ `tmin_c < cold_tmin_c`

On any flagged day, pin the in-scope units (that class, that zone) at
`floor_pct × available capacity` for **all 24 hours**; the LP dispatches economically
above the floor. No HB windows anywhere.

### C.2 Steam-gas ruleset (longer min-run)

- **Commitment params:** raise `ST_GAS_COMMITMENT_PARAMS.min_run_hours` in
  `constants.py` (older subcritical 24h → **48h**; efficient steam 12h → **24h**) so a
  boiler committed for a heat-wave/cold-snap stays online across the multi-day event.
- **Floor engine:** ST_GAS (and ST_CHP) limbs carry an optional `min_event_hours`
  (≥ 24, e.g. 48) so an isolated flagged day bridges to adjacent flagged days — the
  floor spans the whole event, not a single calendar day.
- **ISO/class override** threaded through `commitment.py:_commitment_params` via a new
  `ScenarioConfig.class_commitment_overrides` (per ISO×class min_run/min_down), so the
  longer steam min-run can be enabled/tuned per ISO without touching the constant.
- **CT peakers** keep fast-start `min_run_hours=1` but share the daily-temperature gate
  (full-day floor, no event bridging).

### C.3 Config redesign (customizable per (zone, class))

Redesign `ReliabilityFloorSpec` (frozen dataclass) to:
```python
@dataclass(frozen=True)
class ReliabilityFloorSpec:
    zone: str                 # model zone name
    plant_class: str          # plant_group: "ST_GAS", "CT_PEAKER", "COAL", "oil", …
    driver: str               # "tmax" (hot gate) | "tmin" (cold gate) | "netload"
    threshold: float          # °C for tmax/tmin; GW for netload
    floor_pct: float          # = commit_frac × min_stable_pct (see B.3)
    enabled: bool = True       # toggle this exact (iso, zone, class, driver) limb
    min_event_hours: int = 24  # steam-gas event bridging; 24 = single-day
    distribution: str = "cheapest_first"
```
Dropped fields: `hod_hours`, `hod_range`, `slope_per_c`, `cap`, `base`, `base_24h`,
`t0_c`, `tmax_mode`, `limb`. The `driver` field unifies temperature AND net-load limbs
in one registry (per the review decision: each limb's driver is independently chosen and
toggled per (ISO, zone, class) — a net-load-driven limb such as CAISO CT carries NO
temperature gate).

`RELIABILITY_FLOOR_REGISTRY: dict[str, list[ReliabilityFloorSpec]]` — a per-ISO list of
(zone, class) limbs, seeded from `reliability_floor_coeffs.csv`.

**Toggling:** the single `ScenarioConfig.reliability_floor` flag arms the engine;
`ScenarioConfig.reliability_floor_overrides: dict[str, dict]` (keyed
`"<ZONE>:<CLASS>:<limb>"`) overrides individual limbs (`enabled`, `floor_pct`,
thresholds) from a run config / CLI (`--floor-disable ZONE:CLASS`, `--floor-only …`).

### C.4 Engine (`transmission.inject_reliability_floor`)

Rewrite to:
1. Pull `RELIABILITY_FLOOR_REGISTRY[iso]`, apply overrides, skip disabled limbs.
2. Per limb: `iso_zone_tmax(iso, year, hours, zone)` → daily mask → broadcast 24h →
   (steam) bridge to `min_event_hours`.
3. `frac[t] = floor_pct` on flagged hours else 0.
4. Rows = `plant_group == class & zone_idx == zone & pmax > 0`.
5. `_distribute_group_floor(fleet_arrays, rows, frac, hours)` (reused) → composes into
   `min_gen` via `np.maximum` → `dispatch.build_variable_bounds` (unchanged plumbing).
Returns `True` iff any limb floored (byte-identical no-op otherwise).

---

## PART D — Refactor / removal inventory

| Mechanism | File | Action |
|-----------|------|--------|
| Windowed `inject_reliability_floor` + old `ReliabilityFloorSpec`/registry | transmission.py:3013, iso_configs.py:694–882 | **REPLACE** with the step-gate engine + new spec |
| `inject_caiso_ct_reliability_floor` | transmission.py:2183 | **REMOVE** (subsumed; CAISO CT becomes a `driver="netload"` limb in the unified engine — per review, net-load limbs get NO temp gate) |
| `inject_nyiso_ct_reliability_floor` | transmission.py:2305 | **REMOVE** (subsumed) |
| `inject_nyiso_st_reliability_floor` | transmission.py:2468 | **REMOVE** (subsumed) |
| `inject_neiso_temp_reliability_floor` | transmission.py:2657 | **REMOVE** (subsumed) |
| `inject_miso_temp_reliability_floor` | transmission.py:2895 | **REMOVE** (subsumed) |
| ScenarioConfig slope/cap/base/t0 fields + per-ISO floor bools | scenarios.py:572–801 | **REMOVE** (replaced by `reliability_floor` + overrides) |
| `gas_st_summer_mustrun` / `gas_st_offsummer_mustrun` | fleet.py ~1500 | **SUBSUME** → hot-day gate (calendar-month floor deleted) |
| `gas_st_netload_drag` / `ct_netload_drag` | fleet.py ~2084/2147 | **FOLD** into the unified engine as `driver="netload"` limbs (toggleable per zone/class), so net-load and temperature limbs share one registry/engine. CAISO CT becomes a net-load limb with no temp gate. |
| `ct_mustrun_per_plant` (EIA-923) | fleet.py ~1004 | **RETIRE as keeper** → default-off diagnostic probe (CLAUDE.md #9) |
| `ct_deployment_overlay` (CEMS) | fleet.py ~1022 | **RETIRE as keeper** → default-off diagnostic probe |
| `inject_neiso_gas_coldsnap_derate` (availability derate) | transmission.py:2774 | **KEEP** — different physics (gas-pipeline derate, not must-run); document non-overlap |
| `inject_caiso_gas_commitment_floor` (RA must-offer) | transmission.py:2078 | **KEEP** unless it double-counts the new CAISO temp gate — reconcile & document |

Floor plumbing unchanged: limbs → `_distribute_group_floor` (transmission.py:2633) →
`FleetArrays.min_gen` → `dispatch.build_variable_bounds` (dispatch.py:1534).

---

## Deliverables & verification

1. **This plan** (reviewed first).
2. **Data:** `<iso>_zone_temp_daily.csv` for all six ISOs + `fetch_zone_temperature.py`
   + `derive_reliability_coeffs.py` + `iso_zone_weather_stations.csv` +
   `reliability_floor_coeffs.csv` + coefficient markdown report.
3. **Implementation** behind `reliability_floor`, per-(zone,class) overrides, legacy
   floors removed, steam-gas min-run lengthened.
4. **Unit tests** (`tests/test_reliability_floor.py`): trivial fleet (one unit per
   fossil class, 1 zone), hot/cold/normal/no-weather days — assert
   `min_gen == floor_pct·avail` for all 24h on the matching flagged day, `== pmin`
   otherwise; a disabled limb is byte-identical; steam-gas event bridging spans
   consecutive flagged days.
5. **Re-solve all backcast years in one bundle per ISO**, independent invocations
   launched concurrently (cap ~2 for per-plant ISOs):
   `--year 2023 2024 2025` for CAISO/PJM/NEISO/NYISO/MISO; ERCOT its full span.
   Register each on the dashboard via `calibration-report` and commit per-run bundles
   in the same session (CLAUDE.md #12/#13). Lead with the dashboard headline.
6. **Track MAE before/after** but do NOT revert a structurally-correct mechanism
   because the residual worsened (CLAUDE.md #1/#11) — fix the real root cause.
7. **`/sync-docs`** to reconcile `reliability-floor-feature.md` and the methodology
   spec with the new mechanism.

---

## Resolved review decisions (2026-06-29)

1. **floor_pct** = `commit_frac × min_stable_pct` (B.3) — physical min-stable level
   gated by a structurally-derived commitment share; NOT a p97-CF ceiling. Mirrors how
   UC models enforce `P ≥ Pmin` once a unit is committed.
2. **Driver is per-limb and toggleable per (ISO, zone, class).** Temperature limbs use
   `driver="tmax"/"tmin"`; net-load limbs use `driver="netload"` and carry no temp
   gate. CAISO CT stays net-load-driven as a unified-engine limb.
3. **Class breadth:** author coefficients for every fossil class in every zone; ship
   `enabled=True` only where the fit is real (ρ/n threshold); the rest ship
   `enabled=False` and visible in the coefficient report.
4. **Execution:** decomposed into parallel + sequential sessions — see
   `docs/multi-iso/reliability-floor-rebuild-prompts.md`.
