# W3 — Wire CT/ST Netload Drag Floors into runner.py

**Gap ID:** A8 (MEDIUM)  
**Model tier:** Sonnet  
**Estimated diff:** ~30 lines in `runner.py`

## Problem

The calibration path (`scripts/run_calibration.py`, lines 3088–3126) calls `apply_gas_st_netload_drag_floor()` and `apply_ct_netload_drag_floor()` when `config.gas_st_netload_drag` and `config.ct_netload_drag` are True, respectively. These functions raise the `min_gen` floor on steam-turbine gas and CT peaker units proportional to net load — a forward-native replacement for the measured must-run pin.

The forecast path (`runner.py`) never calls either function. `gas_st_netload_drag: true` and `ct_netload_drag: true` in the config are silently ignored. Without the floor, gas ST units in CAISO/NYISO/NEISO/MISO and CT peakers have no weather-driven min-gen and can shut down completely in low-net-load hours where they historically stay online for reliability.

## What to Do

1. **In runner.py**, after `fleet_arrays` is built (after `generators_to_fleet_arrays` at line 537) and after `inject_offshore_wind_availability` (line 548), compute net load and apply the drag floors:

   ```python
   if getattr(config, "gas_st_netload_drag", False) or getattr(
       config, "ct_netload_drag", False
   ):
       net_load = (
           year_demand.sum(axis=0)
           - (np.asarray(solar_cap)[:, None] * solar_cf).sum(axis=0)
           - (np.asarray(wind_cap)[:, None] * wind_cf).sum(axis=0)
       )
       if apply_gas_st_netload_drag_floor(
           fleet_arrays, dispatch_fleet, net_load, config
       ):
           logger.info(
               "%s %d: ST_GAS net-load reliability-drag floor applied",
               iso, year,
           )
       if apply_ct_netload_drag_floor(
           fleet_arrays, dispatch_fleet, net_load, config
       ):
           logger.info(
               "%s %d: CT_PEAKER net-load reliability-drag floor applied",
               iso, year,
           )
   ```

2. **Add imports** at the top of runner.py:
   ```python
   from market_sim.data.fleet import (
       apply_gas_st_netload_drag_floor,
       apply_ct_netload_drag_floor,
   )
   ```
   These functions are in `src/market_sim/data/fleet.py` (lines 2082 and 2145).

3. **Placement note:** The drag floors modify `fleet_arrays.min_gen` in-place, so they must run after `generators_to_fleet_arrays` but before `dispatch_kwargs` construction. In the calibration script they run between fleet-array build and mc assembly; match that ordering. Note that `year_demand` is computed at line 550 and `fleet_arrays` at line 537 — the drag floor call must come after both.

## What NOT to Do

- Do NOT change the calibration script's drag floor calls.
- Do NOT change the drag floor functions themselves.
- Do NOT change `dispatch.py`.

## Acceptance Criteria

1. A CAISO/NYISO forecast with `gas_st_netload_drag: true` shows ST_GAS units with elevated `min_gen` proportional to net load.
2. A forecast with `ct_netload_drag: true` shows CT peakers with elevated `min_gen` during the ramp window (`ct_drag_ramp_start` to `ct_drag_ramp_end`).
3. With both flags false (default), behavior is unchanged.
4. Existing tests pass unchanged.

## CLAUDE.md Rules

- Rule #12: Net-load drag is forward-native (net load is a forward-derivable signal). It is NOT a measured-outcome pin.
