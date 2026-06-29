# W1 — Wire NEISO Reserve Co-optimization into runner.py

**Gap ID:** A2 (HIGH)  
**Model tier:** Sonnet  
**Estimated diff:** ~60 lines in `runner.py`

## Problem

`runner.py`'s reserve co-opt `elif` chain (lines 644–773) covers ERCOT → PJM → NYISO → MISO but has no NEISO branch. The calibration path (`scripts/run_calibration.py`, lines 4187–4239) has a complete NEISO branch that adds:
- `reserve_requirement` (system-wide 30-min reserve from `neiso_reserve_coopt_inputs`)
- `reserve_eligible` (thermal + storage headroom)
- `reserve_storage=True`
- `ordc_penalties` + `ordc_step_widths` (3-family RCPF demand curves: 30-min, 10-min, 10-min-spin)
- `reserve_balance_zone_mask`, `reserve_balance_ordc_counts`, `reserve_balance_class`

If a NEISO forecast sets `energy_reserve_coopt=True`, the ISO falls through silently — no reserve constraint is built, and scarcity pricing is VOLL-only.

## What to Do

1. **Add an `elif iso == "NEISO"` branch** after the MISO branch in runner.py (after line 773), mirroring the calibration script's structure at lines 4187–4239. The branch should:
   - Import `neiso_reserve_coopt_inputs` from `market_sim.results.scarcity`
   - Call `neiso_reserve_coopt_inputs(config, fleet_arrays, config.hours, zone_names)` to get `req, elig, penalties, widths, zone_mask, ordc_counts, balance_class, online_gated, online_rho`
   - Update `dispatch_kwargs` with `reserve_requirement`, `reserve_eligible`, `reserve_storage=True`, `ordc_penalties`, `ordc_step_widths`, `reserve_balance_zone_mask`, `reserve_balance_ordc_counts`, `reserve_balance_class`

2. **Gate on `energy_reserve_coopt`** — the branch should only fire when `getattr(config, "energy_reserve_coopt", False)` is True, matching the existing pattern.

3. **Verify the import path** — `neiso_reserve_coopt_inputs` is in `results/scarcity.py` (used by the calibration script at line 4201). The call signature matches the NYISO branch pattern in runner.py.

## What NOT to Do

- Do NOT add any measured/backcast-specific data to the forecast path.
- Do NOT modify the existing ERCOT/PJM/NYISO/MISO branches.
- Do NOT change the LP formulation in `dispatch.py`.

## Acceptance Criteria

1. A NEISO forecast with `energy_reserve_coopt: true` in the scenario config produces dispatch_kwargs with `reserve_requirement`, `reserve_eligible`, `ordc_penalties`, `ordc_step_widths`, and all balance keys.
2. The LP solve log shows reserve constraint rows being added for NEISO.
3. The reserve dual is non-zero in tight hours.
4. Existing ERCOT/PJM/NYISO/MISO co-opt tests pass unchanged.
