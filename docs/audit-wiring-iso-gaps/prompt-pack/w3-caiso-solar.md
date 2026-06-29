# W3 — Wire CAISO Solar Deliverability Derate into runner.py

**Gap ID:** A9 (MEDIUM)  
**Model tier:** Sonnet  
**Estimated diff:** ~20 lines in `runner.py`

## Problem

The calibration path (`scripts/run_calibration.py`, lines 1870–1897) calls `caiso_solar_deliverability_derate()` when `config.caiso_solar_deliverability` is True, applying a local-area congestion derate to CAISO solar capacity factors. The structural path uses `year`, `hours`, `k` (slope), and `floor` — all forward-derivable parameters from ScenarioConfig.

The forecast path (`runner.py`) never calls this function. `caiso_solar_deliverability: true` is silently ignored. CAISO forecast solar is uncurtailed by local congestion regardless of penetration level.

## What to Do

1. **In runner.py**, after `solar_cf` is loaded but before it enters `dispatch_kwargs`, add a CAISO solar deliverability derate:

   ```python
   if (
       getattr(config, "caiso_solar_deliverability", False)
       and iso == "CAISO"
   ):
       from market_sim.model.transmission import caiso_solar_deliverability_derate

       derate = caiso_solar_deliverability_derate(
           year,
           config.hours,
           float(getattr(config, "caiso_solar_deliverability_k", 0.15)),
           float(getattr(config, "caiso_solar_deliverability_floor", 0.50)),
       )
       if derate is not None:
           solar_cf = solar_cf * derate[None, :]
           logger.info(
               "CAISO %d: solar deliverability derate applied (k=%.3f, floor=%.2f)",
               year,
               float(getattr(config, "caiso_solar_deliverability_k", 0.15)),
               float(getattr(config, "caiso_solar_deliverability_floor", 0.50)),
           )
   ```

2. **Placement:** This should go after `solar_cf` is first loaded (around the weather-year inputs section, after line 198) and before `dispatch_kwargs` construction. If `solar_cf` is loaded once and reused across years, the derate should be inside the year loop so `year` is correct.

3. **Verify the function** — `caiso_solar_deliverability_derate` is in `market_sim.model.transmission` (line 849). Signature: `(year: int, hours: int, k: float, floor: float) -> np.ndarray | None`.

## What NOT to Do

- Do NOT wire the diagnostic/backcast-only measured HSL path (`caiso_solar_cap_at_delivered`).
- Do NOT apply the derate to non-CAISO ISOs.
- Do NOT change the calibration script.
- Do NOT change `dispatch.py`.

## Acceptance Criteria

1. A CAISO forecast with `caiso_solar_deliverability: true` produces `solar_cf` values reduced by the derate in midday hours.
2. The derate uses forward-derivable parameters (`k` and `floor` from ScenarioConfig), not measured outcomes.
3. Non-CAISO ISOs are unaffected.
4. With `caiso_solar_deliverability: false` (default), behavior is unchanged.
5. Existing tests pass unchanged.

## CLAUDE.md Rules

- Rule #12: The structural derate uses forward solar penetration signal and config parameters, NOT measured HSL actuals.
