# Generic Temperature-Driven Reliability Floor

## Overview

The reliability floor is a temperature-driven commitment mechanism that holds
thermal generators online during weather-driven demand peaks when an energy-only
LP would otherwise decommit them in favour of cheaper baseload. The generic
engine (`transmission.inject_reliability_floor`) replaces six bespoke per-ISO
injectors with **one registry-driven function** that handles any ISO with an
entry in `RELIABILITY_FLOOR_REGISTRY` (defined in `iso_configs.py`).

## Architecture

```
iso_configs.py          scenarios.py              transmission.py
+-----------------+     +-------------------+     +------------------------+
| ReliabilityFloor|     | reliability_floor |---->| inject_reliability_    |
| Spec (dataclass)|     | : bool = False    |     | floor(fleet_arrays,    |
+-----------------+     +-------------------+     |   iso, year, specs,    |
        |                                         |   zone_names)          |
        v                                         +------------------------+
+-------------------+                                      |
| RELIABILITY_FLOOR |                                      v
| _REGISTRY         |                             eia_loader.iso_zone_tmax()
| {"CAISO": [...],  |                             (generic temp loader)
|  "NYISO": [...],  |
|  "NEISO": [...],  |
|  "MISO":  [...]}  |
+-------------------+
```

### Components

1. **`ReliabilityFloorSpec`** (`iso_configs.py`) — frozen dataclass describing
   one temperature-driven limb:
   - `classes`: tuple of plant-group names (e.g. `("CT_PEAKER",)`)
   - `limb`: `"hot"` or `"cold"`
   - `hod_hours`: hour-of-day window (range or explicit set)
   - `tmax_mode`: `"pooled"` (system-wide single series) or `"per_zone"`
   - `t0_c`, `slope_per_c`, `cap`, `base`: regression coefficients
     (scalar or per-class/per-zone dict)
   - `distribution`: `"cheapest_first"` (default) or `"pro_rata"`
   - `base_24h`: persistent 24h baseline per zone (NYISO ST pattern)
   - `outage_exempt`: skip unit-outage overlay for these classes

2. **`RELIABILITY_FLOOR_REGISTRY`** (`iso_configs.py`) — dict mapping ISO code
   to a list of `ReliabilityFloorSpec` limbs. Currently populated for CAISO (1
   limb), NYISO (2 limbs), NEISO (2 limbs), MISO (4 limbs).

3. **`inject_reliability_floor()`** (`transmission.py`) — the single generic
   engine. Iterates specs, loads temperature via `iso_zone_tmax()`, computes
   `frac = clip(base + slope*(driver - t0), base, cap)`, selects in-scope
   units, distributes the floor via `_distribute_group_floor` (cheapest-first)
   or pro-rata, and composes into `FleetArrays.min_gen` via `np.maximum`.

4. **`iso_zone_tmax()`** (`eia_loader.py`) — generic temperature loader.
   Dispatches to existing per-ISO weather files for known ISOs; for new ISOs,
   tries the canonical path `data/raw/<iso>-weather/<iso>_zone_tmax_daily.csv`.

5. **`reliability_floor: bool`** (`scenarios.py`) — single ISO-agnostic config
   flag. When on, the generic engine handles all limbs for the ISO. The legacy
   per-ISO flags (`caiso_ct_reliability_floor`, `nyiso_ct/st_reliability_floor`,
   `neiso_temp_reliability_floor`, `miso_temp_reliability_floor`) are kept for
   back-compat but skipped when `reliability_floor` is on.

## Adding a New ISO

To add temperature-driven reliability floors for a new ISO (e.g. PJM):

1. **Weather data**: place a daily TMAX CSV at
   `data/raw/pjm-weather/pjm_zone_tmax_daily.csv` with columns
   `date,zone,tmax_c` (and optionally `tmin_c` for cold limbs).

2. **Derive coefficients**: run
   `python scripts/derive_reliability_floor.py --iso PJM` or derive manually
   from CAMPD CF-vs-temperature regressions.

3. **Registry entry**: add to `RELIABILITY_FLOOR_REGISTRY` in `iso_configs.py`:
   ```python
   "PJM": [
       ReliabilityFloorSpec(
           classes=("CT_PEAKER",),
           limb="hot",
           hod_hours=(15, 22),
           hod_range=True,
           tmax_mode="per_zone",
           t0_c=25.0,
           slope_per_c={"PJM-East": 0.04, ...},
           cap={"PJM-East": 0.50, ...},
           base=0.0,
       ),
   ],
   ```

4. **Enable**: set `reliability_floor=True` in the calibration config or pass
   `--reliability-floor` on the CLI. No new code required.

## Parity Guarantee

The generic engine produces **numerically identical** `FleetArrays.min_gen`
arrays as the legacy per-ISO injectors for all four calibrated ISOs (CAISO,
NYISO, NEISO, MISO). This is verified by:

- Unit test `TestGenericReliabilityFloor::test_caiso_parity_with_legacy`
  (mocked temperature, identical min_gen assertion)
- Design: same `_distribute_group_floor` helper, same `np.maximum` composition,
  same coefficient values (registry entries mirror the legacy constants exactly)

## Config Flags

| Flag | Scope | Notes |
|------|-------|-------|
| `reliability_floor` | All ISOs | Generic engine, routes through registry |
| `caiso_ct_reliability_floor` | CAISO | Legacy, skipped when `reliability_floor` on |
| `nyiso_ct_reliability_floor` | NYISO | Legacy, skipped when `reliability_floor` on |
| `nyiso_st_reliability_floor` | NYISO | Legacy, skipped when `reliability_floor` on |
| `neiso_temp_reliability_floor` | NEISO | Legacy, skipped when `reliability_floor` on |
| `miso_temp_reliability_floor` | MISO | Legacy, skipped when `reliability_floor` on |
| `neiso_floor_outage_exempt` | NEISO | Triggers on either `neiso_temp_*` or `reliability_floor` |

## Out of Scope

These related mechanisms are **not** part of the generic reliability floor:

- `inject_caiso_gas_commitment_floor` — EIA-930-keyed RA must-offer, not
  temperature-driven
- `inject_neiso_gas_coldsnap_derate` — a gas-availability derate (reduces
  capacity), not a commitment floor (raises min_gen)
- `ct_netload_drag` / `gas_st_netload_drag` — net-load-keyed floors, not
  temperature-keyed
