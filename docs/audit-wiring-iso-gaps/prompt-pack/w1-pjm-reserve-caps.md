# W1 — Wire PJM Reserve Supply Cap + Online Gating into runner.py

**Gap ID:** A3 + A4 (HIGH)  
**Model tier:** Sonnet  
**Estimated diff:** ~30 lines in `runner.py`

## Problem

The calibration path's PJM block (`scripts/run_calibration.py`, lines 4032–4118) adds three keys the forecast PJM block omits:

1. **`reserve_supply_cap`** (lines 4093–4101): conditionally added from `pjm_reserve_deliverable_supply_cap_mw()` when `config.pjm_reserve_supply_cap` is True. Caps the total eligible reserve supply at the deliverable ramp limit (~3.4 GW), so the ORDC vertical step fires when cleared reserve approaches the requirement.

2. **`reserve_online_gated`** (lines 4112–4118): conditionally added when `config.pjm_reserve_online_gated` is True. Constrains reserve supply to only online (already-committed) units.

3. **`reserve_online_rho`**: the headroom fraction for online-gated reserve (default 1.0).

Without the supply cap, the PJM forecast co-opt sees ~38 GW of eligible thermal headroom against a ~3.4 GW requirement → the reserve dual is always zero → no scarcity pricing.

## What to Do

1. **In runner.py's PJM block** (lines 710–722), after the existing `reserve_requirement` / `ordc_penalties` update, add:

   ```python
   if getattr(config, "pjm_reserve_supply_cap", False):
       from market_sim.results.scarcity import pjm_reserve_deliverable_supply_cap_mw
       cap = pjm_reserve_deliverable_supply_cap_mw(config, year)
       if cap is not None:
           dispatch_kwargs["reserve_supply_cap"] = cap
   if getattr(config, "pjm_reserve_online_gated", False):
       dispatch_kwargs["reserve_online_gated"] = fleet_arrays.online_flag
       dispatch_kwargs["reserve_online_rho"] = getattr(
           config, "pjm_reserve_online_rho", 1.0
       )
   ```

2. **Verify imports** — `pjm_reserve_deliverable_supply_cap_mw` is in `results/scarcity.py` (line 1458). Confirm signature: `(config, year) -> float | None`. Import from `market_sim.results.scarcity`.

## What NOT to Do

- Do NOT change the existing reserve requirement or ORDC parameters.
- Do NOT add PJM-specific measured data that has no forward analogue.
- Do NOT modify `dispatch.py` — it already supports `reserve_supply_cap` and `reserve_online_gated`.

## Acceptance Criteria

1. A PJM forecast with `pjm_reserve_supply_cap: true` in the config produces `dispatch_kwargs["reserve_supply_cap"]` ≈ 3.4 GW.
2. The reserve dual is non-zero in tight hours (was always zero before).
3. A PJM forecast with `pjm_reserve_online_gated: true` produces the `reserve_online_gated` array.
4. Existing PJM tests pass unchanged.
