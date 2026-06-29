# W3 — Add Pumped Storage to Forecast Storage Builder

**Gap ID:** C2 (MEDIUM)  
**Model tier:** Opus  
**Estimated diff:** ~60 lines in `runner.py`, possibly `model/storage.py`

## Problem

The calibration path builds storage by loading **both** battery storage (`load_eia860_storage`) **and** pumped storage (`load_eia860_pumped_storage`) from the EIA-860 actuals, giving a complete storage fleet (~20 GW of existing PS nationally).

The forecast path (`runner.py`) uses `build_default_storage()` which builds a **parameterized** battery-storage fleet from scenario config — but **never** includes pumped storage. The ~20 GW of existing PS capacity is simply absent from the forecast dispatch, removing a significant source of peak-shaving and price-smoothing flexibility.

This is a design question: pumped storage is existing installed capacity with no growth (no new PS is being built), so using EIA-860 actuals for PS is appropriate even in forecast mode — it's the installed base, not a measured outcome.

## What to Do

1. **In runner.py**, after `build_default_storage` is called (around line 428 where `storage_units_to_arrays` converts units to arrays), load pumped storage and prepend it to the storage fleet:

   ```python
   from market_sim.model.storage import load_eia860_pumped_storage

   ps_units = load_eia860_pumped_storage(iso, year, config=config)
   if ps_units:
       storage_units = ps_units + storage_units
       logger.info(
           "%s %d: %d pumped-storage units (%.0f MW) from EIA-860",
           iso, year, len(ps_units),
           sum(u.power_cap_mw for u in ps_units),
       )
   ```

2. **Placement:** PS units should be added **before** `storage_units_to_arrays` converts the list to arrays, and **before** the new-entry screen that grows batteries year-over-year. PS is existing capacity; it doesn't participate in the endogenous entry screen.

3. **Verify the function** — `load_eia860_pumped_storage` is in `market_sim.model.storage` (line 517). Signature: `(iso: str, year: int, config: ScenarioConfig | None = None) -> list[StorageUnit]`.

4. **Consider zone assignment.** `load_eia860_pumped_storage` returns `StorageUnit` objects with zone assignments from EIA-860. These must be consistent with the forecast's `zone_names` for the ISO. Verify that the zone names used by the PS loader match the zones in `iso_configs.py`.

## What NOT to Do

- Do NOT use PS measured dispatch data (EIA-930 or CEMS) — the PS units dispatch endogenously in the LP via charge/discharge variables with round-trip efficiency.
- Do NOT add PS to the endogenous storage growth screen — PS is fixed existing capacity.
- Do NOT change `build_default_storage` — batteries still come from the parameterized builder.
- Do NOT change the calibration script.
- Do NOT change `dispatch.py`.

## Acceptance Criteria

1. A NEISO/NYISO/PJM/CAISO forecast includes pumped-storage units in the storage fleet (verify by checking storage unit names or tech type).
2. PS units dispatch in the LP (charge/discharge cycles with round-trip efficiency losses).
3. PS capacity does NOT grow year-over-year (fixed existing fleet).
4. Battery storage from `build_default_storage` continues to work and grow via the entry screen.
5. Existing tests pass unchanged.

## CLAUDE.md Rules

- Rule #1: Pumped storage is a structural mechanism (existing installed capacity providing flexibility). It stays regardless of backcast residual.
- Rule #12: EIA-860 installed capacity is a physical asset registry, not a measured outcome. Using it for PS is analogous to using it for the thermal fleet — admissible in forecast.
