# W4 — Wire storage_vintage_ramp + storage_cap_profiles into runner.py

**Gap ID:** C3 (LOW)  
**Model tier:** Sonnet  
**Estimated diff:** ~25 lines in `runner.py`

## Problem

The calibration path calls `storage_cap_profiles()` when `config.storage_vintage_ramp` is True, producing 2-D time-varying (monthly) power and energy caps for storage units that ramp up mid-year based on their commission date (COD). This means a battery that comes online in July contributes only 6/12 of its annual capacity.

The forecast path (`runner.py`) never calls `storage_cap_profiles`. Storage units always have flat (1-D) power/energy caps regardless of the `storage_vintage_ramp` config setting. For ISOs with significant mid-year storage additions (CAISO, ERCOT, NEISO), this overstates storage capacity in the first half of the year.

Currently this is latent for the forecast path because `build_default_storage` doesn't populate monthly COD fields. It becomes relevant once the storage builder is updated to include COD data (e.g., after C2 wires pumped storage from EIA-860 which carries COD).

## What to Do

1. **In runner.py**, after `storage_units_to_arrays` (around line 428), add:
   ```python
   if getattr(config, "storage_vintage_ramp", False):
       from market_sim.model.storage import storage_cap_profiles

       power_cap_2d, energy_cap_2d = storage_cap_profiles(
           storage_units, storage, config.hours
       )
       if power_cap_2d is not None:
           storage = storage._replace(
               power_cap=power_cap_2d,
               energy_cap=energy_cap_2d,
           )
           logger.info(
               "%s %d: storage vintage ramp applied — %d units with mid-year COD",
               iso, year,
               int((power_cap_2d != power_cap_2d[:, :1]).any(axis=1).sum()),
           )
   ```

2. **Verify the function** — `storage_cap_profiles` is in `market_sim.model.storage` (line 438). Signature: `(units: list[StorageUnit], arrays: StorageArrays, hours: int) -> tuple[np.ndarray, np.ndarray]`.

3. **Check StorageArrays type.** Confirm that `StorageArrays` supports `_replace` (NamedTuple) or attribute mutation. Adjust the replacement pattern accordingly.

## What NOT to Do

- Do NOT change `build_default_storage` — the storage builder is a separate concern.
- Do NOT change the calibration script.
- Do NOT change `dispatch.py`.

## Acceptance Criteria

1. With `storage_vintage_ramp: true`, storage units with mid-year COD have time-varying (2-D) power/energy caps.
2. Units with January COD (or no COD) have flat caps (identical to current behavior).
3. With `storage_vintage_ramp: false` (default), behavior is unchanged.
4. Existing tests pass unchanged.
