# PP-02 — Resource Catalog & Costs

**Upstream:** PS-01 (pricing/LCOE), PS-03 (storage), PS-05 (existing), PS-06 (caps).
**Targets:** `data/lcoe/resource_costs.csv` (+ any caps file), `resources.py`.
**Status:** minimal done (seed table + `load_resource_arrays`).

## Build

1. **Generation costs (PS-01).** Replace seed numbers with the sourced ATB values;
   record provenance in `notes`. If pay-per-MWh representation was chosen, add a
   `cost_representation` branch (fixed vs per-MWh) in `resources.py` and thread it
   into `lp.py` (coordinate with PP-04). Wire `config.discount_rate`/CRF if used.
2. **Storage costs (PS-03).** If the power/energy split was chosen, extend the
   table schema (`power_cost`, `energy_cost`) and have `resources.py` build both
   components; otherwise refine the all-in `$/MW-yr` numbers. Add degradation adder
   if decided.
3. **Existing resources (PS-05).** Set `nuclear_existing`/`hydro_existing` cost
   basis and per-ISO caps; add `additionality_only` handling if adopted. Spec the
   hydro monthly-budget input.
4. **Caps (PS-06).** If per-ISO caps were chosen, add `data/caps/…` and a loader;
   support load-relative caps if decided. Build the eligibility matrix (which
   resources per ISO).

## Acceptance

`test_resources` covers cost conversion for both representations, sensitivity
selection, cap/floor overrides, per-ISO caps, and eligibility filtering.
