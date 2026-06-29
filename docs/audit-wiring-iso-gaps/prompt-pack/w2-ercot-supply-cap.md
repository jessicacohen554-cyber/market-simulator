# W2 — Wire ERCOT Single-Product Reserve Supply Cap into runner.py

**Gap ID:** A5 (MEDIUM)  
**Model tier:** Sonnet  
**Estimated diff:** ~10 lines in `runner.py`

## Problem

The ERCOT reserve co-opt `elif` chain in `runner.py` (lines 644–702) has two sub-branches:

- **Multi-product** (lines 645–686): calls `ercot_multiproduct_reserve_coopt_inputs` and then applies the RTOLCAP supply cap via `ercot_rtolcap_supply_cap_mw()` (lines 684–686). This path is correct.
- **Single-product fallback** (lines 687–702): calls `ercot_reserve_coopt_inputs` but **never** applies the RTOLCAP supply cap.

The calibration path (`scripts/run_calibration.py`, lines 4018–4031) applies the supply cap in **both** single-product and multi-product modes. Without the cap on the single-product path, the forecast sees ~38 GW of uncapped headroom against a ~3.4 GW requirement → the reserve dual is always zero.

## What to Do

1. **In runner.py's ERCOT single-product branch** (after the `dispatch_kwargs.update` at lines 696–702), add the same supply-cap logic that the multi-product branch has:
   ```python
   # Apply RTOLCAP supply cap (same as multi-product path)
   coopt_supply_cap = ercot_rtolcap_supply_cap_mw(config, config.hours)
   if coopt_supply_cap is not None:
       dispatch_kwargs.update(reserve_supply_cap=coopt_supply_cap)
   ```

2. `ercot_rtolcap_supply_cap_mw` is already imported (line 96 of runner.py from `market_sim.results.scarcity`). No new imports needed.

## What NOT to Do

- Do NOT modify the multi-product branch — it already has the supply cap.
- Do NOT change the calibration script.
- Do NOT change `dispatch.py`.

## Acceptance Criteria

1. An ERCOT forecast with `energy_reserve_coopt: true` and `ercot_multiproduct_as_coopt: false` (single-product path) produces `dispatch_kwargs["reserve_supply_cap"]`.
2. The reserve dual is non-zero in tight hours (was always zero before on single-product path).
3. The multi-product path continues to work identically.
4. Existing ERCOT tests pass unchanged.
