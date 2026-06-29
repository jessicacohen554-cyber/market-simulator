# W4 — Wire Gas Offer Curve (split_gas_tranches) into runner.py Non-CAMPD Path

**Gap ID:** A12 (LOW)  
**Model tier:** Sonnet  
**Estimated diff:** ~10 lines in `runner.py`

## Problem

The calibration path (`scripts/run_calibration.py`, lines 3003–3004) calls `split_gas_tranches()` after `split_coal_tranches()` when `config.gas_offer_curve` is True. This splits each gas unit into committed/economic/peaking tranches with rising heat rates, giving a stepped gas offer curve analogous to the coal take-or-pay split.

The forecast path (`runner.py`) has two fleet-build sub-paths:
- **CAMPD bins** (line 462): uses `campd_tranche_fuel_frac` — gas tranching is embedded in the CAMPD bins already.
- **Non-CAMPD** (line 500, the `else` branch): calls `split_coal_tranches` but **never** calls `split_gas_tranches`. The `gas_offer_curve: true` flag is silently ignored for non-CAMPD ISOs (primarily SPP).

## What to Do

1. **In runner.py's non-CAMPD fleet-build branch** (around line 513, after `split_coal_tranches`), add:
   ```python
   if getattr(config, "gas_offer_curve", False):
       from market_sim.data.fleet import split_gas_tranches
       dispatch_fleet, fuel_fracs = split_gas_tranches(
           dispatch_fleet, fuel_fracs, config
       )
   ```

2. **Verify** — `split_gas_tranches` is in `market_sim.data.fleet` (line 2587). Signature: `(generators: list[Generator], fuel_fracs: list[float], config: ScenarioConfig) -> tuple[list[Generator], list[float]]`.

3. **Note:** This only affects the non-CAMPD path. CAMPD-binned ISOs (ERCOT, PJM, CAISO, etc.) already have gas tranching embedded in the CAMPD binning process. SPP is currently the primary non-CAMPD ISO.

## What NOT to Do

- Do NOT add `split_gas_tranches` to the CAMPD path — CAMPD bins already carry the offer curve.
- Do NOT change the calibration script.
- Do NOT change `dispatch.py`.

## Acceptance Criteria

1. An SPP forecast with `gas_offer_curve: true` and `use_campd_bins: false` produces gas units split into committed/economic/peaking tranches (more generators than input).
2. With `gas_offer_curve: false` (default), behavior is unchanged.
3. CAMPD-binned ISOs are unaffected.
4. Existing tests pass unchanged.
