# W2 — Wire Negative Renewable Offer Floor into runner.py

**Gap ID:** A6 (HIGH)  
**Model tier:** Sonnet  
**Estimated diff:** ~10 lines in `runner.py`

## Problem

The calibration path (`scripts/run_calibration.py`) calls `apply_negative_renewable_offer_floor()` when `config.negative_renewable_offers` is True, setting `wind_mc` and `solar_mc` to negative values that reflect the keep-running value of PTCs/RECs. This lets renewables bid below zero — a real market behavior in CAISO and SPP midday hours.

The forecast path (`src/market_sim/runner.py`) never calls this function. The config field `negative_renewable_offers` is silently ignored. `wind_mc` and `solar_mc` stay at their default non-negative dispatch credits, so CAISO forecast can never produce negative midday prices regardless of the config.

## What to Do

1. **In runner.py**, after the `wind_mc, solar_mc` computation (after `compute_dispatch_credits` around line 581) and the EAC subtraction (around line 598), add the negative-offer floor:
   ```python
   if getattr(config, "negative_renewable_offers", False):
       from market_sim.policy.eac import apply_negative_renewable_offer_floor
       wind_mc, solar_mc = apply_negative_renewable_offer_floor(
           wind_mc, solar_mc, config
       )
   ```

2. **Verify the import path** — `apply_negative_renewable_offer_floor` is in `policy/eac.py` (line 100). Signature: `(wind_mc, solar_mc, config: ScenarioConfig) -> tuple[np.ndarray | float, np.ndarray | float]`.

## What NOT to Do

- Do NOT change the existing `compute_dispatch_credits` or `compute_eac_dispatch_credits` calls.
- Do NOT change the LP formulation in `dispatch.py`.
- Do NOT change the calibration script.

## Acceptance Criteria

1. A CAISO forecast with `negative_renewable_offers: true` produces negative `wind_mc` or `solar_mc` values.
2. Midday prices in CAISO with high solar penetration can go negative.
3. With `negative_renewable_offers: false` (default), behavior is unchanged.
4. Existing tests pass unchanged.
