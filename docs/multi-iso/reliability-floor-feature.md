# Per-(Zone, Class) Temperature / Net-Load Reliability Floor

## Overview

The reliability floor is a temperature- and net-load-driven commitment
mechanism that holds thermal generators online during weather-driven demand
peaks when an energy-only LP would otherwise decommit them in favour of
cheaper baseload. A single ISO-agnostic engine
(`transmission.inject_reliability_floor`) reads a CSV-seeded registry of
per-(zone, plant_class, driver) limbs and applies full-day step-function
floors to `FleetArrays.min_gen` — one registry row per limb, no per-ISO
code.

All six ISOs (ERCOT, CAISO, PJM, MISO, NYISO, NEISO) have derived
coefficient CSVs with ~221 total limbs (~30 enabled across the six ISOs
based on the ρ/n enable gate). The engine replaces the five legacy
per-ISO injectors (`inject_caiso_ct_reliability_floor`,
`inject_nyiso_ct_reliability_floor`, `inject_nyiso_st_reliability_floor`,
`inject_neiso_temp_reliability_floor`, `inject_miso_temp_reliability_floor`)
and the old windowed `ReliabilityFloorSpec` (with `slope_per_c`/`cap`/
`base`/`t0_c`/`hod_hours`/`tmax_mode`/`base_24h` fields), all of which are
removed.

## Architecture

```
data/raw/reference/                  config/iso_configs.py
  reliability_floor_coeffs_<ISO>.csv   ReliabilityFloorSpec (frozen dataclass)
  (one row per (zone, class, driver)     ↕
   limb — single source of truth)      _load_reliability_floor_registry()
                                         ↓
                                       RELIABILITY_FLOOR_REGISTRY
                                       dict[iso] → list[ReliabilityFloorSpec]

config/scenarios.py                  model/transmission.py
  reliability_floor: bool = False      inject_reliability_floor(
  reliability_floor_overrides: dict      fleet_arrays, iso, year, specs,
      ↓                                  zone_names, *, demand, wind_cf,
  apply_reliability_floor_overrides()    wind_cap, solar_cf, solar_cap)
                                         ↓
                                       _distribute_group_floor()  (cheapest-first)
                                       or pro_rata
                                         ↓
                                       FleetArrays.min_gen (in-place, via np.maximum)
```

### Components

1. **`ReliabilityFloorSpec`** (`config/iso_configs.py`) — frozen dataclass
   describing one (zone, class, driver) limb:
   - `zone: str` — model zone name (e.g. `"NP15"`, `"Houston"`)
   - `plant_class: str` — plant group (`"CT_PEAKER"`, `"ST_GAS"`, `"COAL"`,
     `"CC_REGULAR"`, `"oil"`, etc.)
   - `driver: str` — `"tmax"` (hot gate), `"tmin"` (cold gate), or
     `"netload"` (system net-load stress gate)
   - `threshold: float` — °C for tmax/tmin drivers; GW for netload
   - `floor_pct: float` — `commit_frac × min_stable_pct` (a structural
     commitment share times the class's physical minimum-stable level —
     never a measured-CF ceiling; see §B.3 of the rebuild plan)
   - `enabled: bool = True` — toggle this exact limb on/off
   - `min_event_hours: int = 24` — steam-gas event bridging (48 for
     ST_GAS/ST_CHP so a boiler spans multi-day events; 24 = single-day
     for fast-start classes)
   - `distribution: str = "cheapest_first"` — `"cheapest_first"` (default)
     or `"pro_rata"` (each unit floored at `frac × its own available
     capacity`)

2. **Coefficient CSVs**
   (`data/raw/reference/reliability_floor_coeffs_<ISO>.csv`) — one file per
   ISO, one row per (zone, class, driver) limb. Required columns: `zone`,
   `plant_class`, `driver`, `threshold`, `floor_pct`, `enabled`. Optional:
   `min_event_hours`, `distribution`. Metadata columns (not consumed by the
   engine): `commit_frac`, `min_stable_pct`, `rho`, `n`, `baseline`,
   `baseline_commit`, `threshold_basis`. Derived by
   `scripts/data/derive_reliability_coeffs.py` from CAMPD CF-vs-temperature
   regressions; see coefficient methodology below.

3. **`RELIABILITY_FLOOR_REGISTRY`** (`config/iso_configs.py`) — `dict[str,
   list[ReliabilityFloorSpec]]` populated at import time by
   `_load_reliability_floor_registry()`, which reads the CSV for every
   registered ISO. Steam classes (`ST_GAS`, `ST_CHP`) default to
   `min_event_hours=48`; all others default to 24.

4. **`inject_reliability_floor()`** (`model/transmission.py`) — the single
   generic engine:
   1. Iterate enabled specs (skip `enabled=False`).
   2. For temperature drivers: load the zone's daily weather via
      `eia_loader.iso_zone_tmax()` (tmax/tmin). For netload drivers:
      compute system net-load from exogenous demand, wind, solar (not
      endogenous dispatch — avoids circularity).
   3. Build the **full-day step-function gate** — no hour-of-day windows:
      - `driver="tmax"` → flag every hour of a day where `tmax_c > threshold`
      - `driver="tmin"` → flag where `tmin_c < threshold`
      - `driver="netload"` → flag all 24h of days with peak net-load (GW)
        above threshold
   4. For steam classes with `min_event_hours > 24`, bridge isolated flagged
      days via `_bridge_flagged_runs()` so a committed boiler spans the
      full multi-day event.
   5. Set `frac = floor_pct` on flagged hours (0 elsewhere); select units
      matching `plant_group == plant_class & zone_idx == zone & pmax > 0`.
   6. Distribute the floor into `FleetArrays.min_gen` via
      `_distribute_group_floor()` (cheapest-first) or pro-rata, composing
      with any existing floor via `np.maximum`.

5. **Config flags** (`config/scenarios.py`):
   - `reliability_floor: bool = False` — single ISO-agnostic master switch.
     When on, the engine processes all enabled limbs for the running ISO.
   - `reliability_floor_overrides: dict[str, dict]` — per-limb run-config
     overrides keyed `"<ZONE>:<CLASS>:<driver>"` →
     `{"enabled"?: bool, "floor_pct"?: float, "threshold"?: float}`.
     Applied via `apply_reliability_floor_overrides()` before the engine
     runs, so a single limb can be toggled or re-tuned without editing the
     registry CSV.

6. **`class_commitment_overrides`** (`config/scenarios.py`) — per-ISO×class
   `min_run_hours`/`min_down_hours` overrides, threaded through
   `commitment._commitment_params`. Used to lengthen steam-gas min-run
   (24→48 h) so a boiler committed for a heat-wave stays online across the
   multi-day event.

## Coefficient Methodology

Coefficients are derived from CAMPD CF-vs-temperature regressions per
(zone, class) and are **forward-reproducible** — they satisfy the
admissibility test (CLAUDE.md Non-Negotiable Rules #9/#10/#11):

1. **Measured class daily CF per zone** — per-plant CAMPD `grossLoad`
   joined to the model's own fleet builder (bin assignments + classify),
   daily group MWh / (group nameplate × 24), on a when-available basis
   for classes where CAMPD outages materially derate.

2. **Regression** — daily CF regressed on the zone's daily TMAX (hot limb)
   / TMIN (cold limb) to extract:
   - `threshold` — the temperature at which group CF begins to climb above
     its mild-day baseline (day-gate onset). Default prior: hot ≈ zone p95
     TMAX; cold ≈ zone p1 TMIN.
   - `commit_frac` — share of the class's capacity that is online on
     flagged days (a commitment count from CAMPD `grossLoad > 0`, NOT an
     energy/CF ceiling). Structural — regenerates for a forward year.
   - `min_stable_pct` — physical min-stable level (Pmin/Pmax) of the class,
     from bin `Pct_Must_Run` / turbine min-load specs.
   - `floor_pct = commit_frac × min_stable_pct` — the floor the LP must
     meet; dispatch above it is economic.

3. **Enable/disable gate** — a limb is `enabled=True` only when the
   temperature response is real: Spearman ρ above threshold (≥0.3),
   adequate sample size `n` (≥30 flagged days), and `floor_pct`
   meaningfully above the mild-day baseline. Weak/insignificant limbs ship
   `enabled=False` — never invented to plug a residual.

4. **Guardrail** — thresholds and floor_pct are derived from the
   TEMPERATURE→commitment relationship only. They are **never** tuned to
   the price/volume residual, and floor_pct is **never** set to a measured
   CF so output matches actuals. The p97-CF ceiling used by the old
   mechanism is gone.

Scripts: `scripts/data/derive_reliability_coeffs.py --iso ALL` (main deriver);
per-ISO legacy scripts (`scripts/data/derive_*_reliability_floor.py`) are
archived but superseded.

## Adding a New ISO or Limb

To add reliability floors for a new ISO (or new limbs in an existing ISO):

1. **Weather data**: place a daily temperature CSV at
   `data/raw/<iso>-weather/<iso>_zone_temp_daily.csv` with columns
   `date,zone,tmax_c,tmin_c`. For net-load limbs, EIA-930 demand and
   renewable profiles are used.

2. **Derive coefficients**: run
   `python scripts/data/derive_reliability_coeffs.py --iso <ISO>` — writes
   `data/raw/reference/reliability_floor_coeffs_<ISO>.csv`.

3. **Enable**: set `reliability_floor=True` in the calibration config or
   pass `--reliability-floor` on the CLI. No new code required — the engine
   picks up the CSV rows automatically.

4. **Override individual limbs** (optional): use
   `reliability_floor_overrides` in the run config to toggle or re-tune
   specific limbs without editing the CSV.

## Steam-Gas Longer Min-Run

ST_GAS/ST_CHP limbs carry `min_event_hours=48` by default so a committed
boiler stays online across multi-day heat-waves or cold-snaps. The
`_bridge_flagged_runs()` helper merges isolated flagged days separated by
sub-event gaps. Additionally, `class_commitment_overrides` can lengthen
ST_GAS `min_run_hours` (24→48h) in `commitment._commitment_params` so the
P2 commitment screen respects the longer commitment.

CT peakers keep fast-start `min_run_hours=1` and share the daily
temperature/net-load gate (full-day floor, no event bridging).

## Out of Scope

These related mechanisms are **not** part of the generic reliability floor:

- `inject_caiso_gas_commitment_floor` — EIA-930-keyed RA must-offer, not
  temperature-driven
- `inject_neiso_gas_coldsnap_derate` — a gas-availability derate (reduces
  capacity), not a commitment floor (raises min_gen)
- `ct_mustrun_per_plant` (EIA-923) / `ct_deployment_overlay` (CEMS) —
  demoted to default-off diagnostic probes (measured-outcome floors with no
  forward analogue; CLAUDE.md #9)
