# W3 — Wire NYISO Import Node Reconciliation (Forecast Mode) into runner.py

**Gap ID:** A11 (LOW)  
**Model tier:** Opus  
**Estimated diff:** ~40 lines in `runner.py`

## Problem

The calibration path (`scripts/run_calibration.py`, lines 3911–3917) passes `import_node_gen_idx`, `import_node_monthly_lo`, and `import_node_monthly_hi` to `dispatch_kwargs` when import-node reconciliation is active. These keys create monthly band constraints on the import/export node in the LP, bounding its aggregate generation to a narrow range each month.

The forecast path (`runner.py`) never sets these three keys. When a NYISO forecast runs with `nyiso_import_reconciliation: true`, the import node is unconstrained at the monthly level — it can import/export freely up to TTC each hour, with no band forcing aggregate monthly net imports to match a target.

The reconciliation function `build_import_node_reconciliation` (in `market_sim.model.transmission`, line 3128) already supports a forecast mode: when `mode="forecast"`, it uses `nyiso_forward_net_import_twh` (a config parameter giving the target annual net import in TWh) shaped by forecast load instead of measured EIA-930 data.

**Depends on Wave 1 / A7** — the reference-price interface must be wired first, because the import-node reconciliation constrains the import generators that the reference-price interface builds.

## What to Do

1. **In runner.py**, after the import generators are built (after line 189) and after the reference-price interface branch (from W1/A7), build the reconciliation if enabled:

   ```python
   import_node_recon = None
   if (
       getattr(config, "nyiso_import_reconciliation", False)
       and iso == "NYISO"
       and import_generators
   ):
       from market_sim.model.transmission import build_import_node_reconciliation

       import_node_recon = build_import_node_reconciliation(
           fleet_arrays,
           iso,
           year,
           mode="forecast",
           forward_net_import_twh=getattr(config, "nyiso_forward_net_import_twh", None),
           system_demand=year_demand,
       )
   ```

2. **Add `import_node_gen_idx`, `import_node_monthly_lo`, `import_node_monthly_hi` to `dispatch_kwargs`** (around line 605):
   ```python
   if import_node_recon is not None:
       node_idx, recon_lo, recon_hi = import_node_recon
       dispatch_kwargs.update(
           import_node_gen_idx=node_idx,
           import_node_monthly_lo=recon_lo,
           import_node_monthly_hi=recon_hi,
       )
   ```

3. **Ordering note:** `build_import_node_reconciliation` needs `fleet_arrays` (to find the import-node generators) and `year_demand` (for shaping in forecast mode), so it must be called after both are available. This means it goes inside the year loop, after fleet-array build and demand scaling, but before `dispatch_kwargs` construction.

4. **Verify function signature** — `build_import_node_reconciliation` is in `market_sim.model.transmission` (line 3128). Signature: `(fleet_arrays, iso: str, year: int, band_frac: float = ..., *, mode: str = "backcast", forward_net_import_twh: ... = None, ...) -> tuple | None`.

## What NOT to Do

- Do NOT use `mode="backcast"` in the forecast path — the backcast mode uses measured EIA-930 monthly imports.
- Do NOT wire this for non-NYISO ISOs unless they gain import-node reconciliation.
- Do NOT change the calibration script.
- Do NOT change `dispatch.py`.

## Acceptance Criteria

1. A NYISO forecast with `nyiso_import_reconciliation: true` and `nyiso_forward_net_import_twh` set produces `import_node_gen_idx`, `import_node_monthly_lo`, `import_node_monthly_hi` in `dispatch_kwargs`.
2. The monthly band is shaped by forecast load (not measured EIA-930 data).
3. With `nyiso_import_reconciliation: false` (default), behavior is unchanged.
4. Existing tests pass unchanged.

## CLAUDE.md Rules

- Rule #12: The forecast mode uses `forward_net_import_twh` (a scenario parameter), NOT measured monthly EIA-930 interchange. The measured path is backcast-only.
