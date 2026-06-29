# W1 — Wire Reference-Price Interface into runner.py

**Gap ID:** A7 (HIGH)  
**Model tier:** Opus  
**Estimated diff:** ~120 lines in `runner.py`

## Problem

The calibration path (`scripts/run_calibration.py`, lines 2587–2657, 3603–3659) implements the **forecast-grade reference-price interface** — a priced import/export node where each seam is priced hourly from `gas × heat_rate × load_shape ± hurdle`, regenerating for any forward year. Three functions are involved:

- `build_reference_price_node(iso)` — constructs flow-banded import/export pseudo-generators
- `inject_reference_price_mc(fleet_arrays, mc_base, iso, year, gas_price_path)` — overwrites each seam row's mc with the hourly reference price
- `inject_reference_price_firm_export(fleet_arrays, iso, year)` — floors the must-flow export tranche

The forecast path (`runner.py`) hardcodes `build_import_generators(iso, ...) + build_export_sinks(iso)` — the static fitted tranche ladder — and never branches on `config.reference_price_interface`. The config field is documented as "the forward-scenario mechanism" and "Priced-interchange node: serve the seam through the forecast-grade reference-price interface."

## What to Do

1. **In runner.py's import-node construction** (around line 560–590 where `import_generators` is built), add a branch:
   ```python
   if getattr(config, "reference_price_interface", False) and iso in INTERFACE_NEIGHBORS:
       import_generators = build_reference_price_node(iso)
   else:
       import_generators = build_import_generators(iso, border_carbon) + build_export_sinks(iso)
   ```
   Import `build_reference_price_node` from `market_sim.model.transmission` and `INTERFACE_NEIGHBORS` from `market_sim.config.constants`.

2. **After mc assembly** (after `assemble_mc`, around line 600), add:
   ```python
   if getattr(config, "reference_price_interface", False) and iso in INTERFACE_NEIGHBORS:
       inject_reference_price_mc(fleet_arrays, mc_base, iso, year, config.gas_price_path)
       inject_reference_price_firm_export(fleet_arrays, iso, year)
   ```
   Import both from `market_sim.model.transmission`.

3. **Handle the CAISO special case.** The calibration script has a separate `caiso_reference_price_seam` path that also does per-hub corridor splitting and CARB border carbon. For now, the generic path should exclude CAISO (`iso != "CAISO"`) matching the calibration script's gate. The CAISO reference-price seam can be wired separately.

4. **Handle the MISO firm-imports add-on.** If `config.miso_firm_imports` is True, the calibration script appends `build_miso_firm_imports(iso, year=year, mode=config.mode)` to `import_generators`. Mirror this in runner.py.

## What NOT to Do

- Do NOT wire the measured-interchange path (`include_interchange=not priced_interchange` on demand) — the forecast demand already includes interchange via the demand trajectory.
- Do NOT wire the measured OASIS per-hub pricing (CAISO `caiso_import_hub_prices`) — that's backcast-only measured data. The reference-price seam IS the forward replacement.
- Do NOT change the LP formulation in `dispatch.py`.
- Do NOT change the calibration script.

## Acceptance Criteria

1. A PJM forecast with `reference_price_interface: true` produces import generators from `build_reference_price_node` (verify by checking generator names contain "ref_price" or similar).
2. The mc array for seam rows shows hourly variation (not flat static tranches).
3. The firm-export floor is applied (check log message).
4. A MISO forecast with both `reference_price_interface: true` and `miso_firm_imports: true` includes Manitoba firm hydro generators.
5. Existing tests pass unchanged.

## CLAUDE.md Rules

- Rule #1: The reference-price interface is a structural mechanism (priced seam responding to gas prices), not a fit. It stays regardless of backcast residual.
- Rule #12: The reference price uses `gas × HR × load_shape` — a forward-derivable formula. It is NOT the measured neighbor LMP.
