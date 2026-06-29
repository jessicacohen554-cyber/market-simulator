# W2 — Wire MISO Reserve Co-opt into Calibration _run_dispatch

**Gap ID:** A13 (MEDIUM) — REVERSE gap  
**Model tier:** Sonnet  
**Estimated diff:** ~50 lines in `scripts/run_calibration.py`

## Problem

This is a **reverse** gap: `runner.py` (line 761) already has a MISO reserve co-opt branch using `miso_reserve_coopt_inputs`, but the calibration script's `_run_dispatch` reserve co-opt `elif` chain (starting around line 3919) covers ERCOT → PJM → NYISO → NEISO and has **no** MISO branch.

If a MISO calibration run sets `energy_reserve_coopt=True`, it silently falls through — no reserve constraint is built, and the backcast comparison is against an LP with VOLL-only scarcity pricing.

## What to Do

1. **In `scripts/run_calibration.py`'s `_run_dispatch` function**, after the NEISO reserve co-opt branch (around line 4239), add an `elif` for MISO that mirrors the runner.py pattern:

   ```python
   elif getattr(config, "energy_reserve_coopt", False) and config.iso == "MISO":
       from market_sim.results.scarcity import miso_reserve_coopt_inputs

       (
           coopt_req,
           coopt_elig,
           coopt_pens,
           coopt_widths,
       ) = miso_reserve_coopt_inputs(config, fleet_arrays, config.hours)
       dispatch_kwargs.update(
           reserve_requirement=coopt_req,
           reserve_eligible=coopt_elig,
           ordc_penalties=coopt_pens,
           ordc_step_widths=coopt_widths,
       )
       logger.info(
           "energy+reserve co-opt (MISO): system-wide RBDC, "
           "%d ORDC steps ($%.0f-$%.0f), %d reserve-eligible units",
           len(coopt_pens),
           float(coopt_pens.min()) if len(coopt_pens) else 0.0,
           float(coopt_pens.max()) if len(coopt_pens) else 0.0,
           int(coopt_elig.sum()),
       )
   ```

2. **Verify the function signature** — `miso_reserve_coopt_inputs` is in `market_sim.results.scarcity` (line 2067). Signature: `(config, fleet_arrays: FleetArrays, hours: int, n_ramp: int = 8) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]`.

## What NOT to Do

- Do NOT modify the existing ERCOT/PJM/NYISO/NEISO branches in the calibration script.
- Do NOT modify the runner.py MISO branch (it already works).
- Do NOT change `dispatch.py`.

## Acceptance Criteria

1. A MISO calibration run with `energy_reserve_coopt: true` produces `dispatch_kwargs` with `reserve_requirement`, `reserve_eligible`, `ordc_penalties`, `ordc_step_widths`.
2. The MISO LP log shows reserve constraint rows being added.
3. Existing ERCOT/PJM/NYISO/NEISO co-opt branches pass unchanged.
4. The runner.py MISO branch continues to work identically.
