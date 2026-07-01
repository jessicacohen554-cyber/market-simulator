# 0006 — Storage costing: tranches for Li-ion, power/energy split for LDES & H₂

- **Status:** accepted (stakeholder-decided 2026-07-01)
- **Date:** 2026-07-01
- **Session:** PS-03 (Storage Costing: power/energy split, LDES, hydrogen)
- **Implemented by:** PP-02/PP-04

## Context

Storage capital cost decomposes into power ($/kW-yr) and energy ($/kWh-yr)
components; capturing this split lets the LP choose duration and matches real
procurement. Batteries are fixed-duration tranches (4h, 8h); long-duration storage
(LDES, iron-air) and hydrogen are power-plus-energy built separately, with the LP
choosing duration within bounds.

## Options considered

1. **Fixed-duration tranches only** (current 4h, 8h, 12h) — simpler, less code
   and constraint complexity; loses LDES/H₂ economics where energy is
   cheaper/dominant per kWh.
2. **Power/energy split for all techs** — most flexible; adds a second build
   variable and duration-bound constraints per split tech; requires energy-build
   costing in the objective.
3. **Hybrid** — batteries stay fixed-duration tranches (refined from ATB 2024),
   LDES and H₂ get power/energy split (chosen).

## Decision

**Hybrid representation.** Li-ion batteries (battery_4h, battery_8h) remain
fixed-duration procurement tranches with one all-in annualized $/MW-yr each,
refined from ATB 2024 with power+energy bundled at the quoted duration;
battery_12h is dropped from defaults (LDES covers that band). LDES (iron-air) and
hydrogen are split: two build variables per tech — power MW costed at $/kW-yr
(annualized power-train capex) and energy MWh at $/kWh-yr (annualized energy
capex). The LP chooses duration continuously within per-tech bounds: LDES 50–150
h, hydrogen 24–500 h. Efficiency η = √RTE split evenly across charge/discharge.
Degradation is NOT modeled beyond the `storage_epsilon` tiebreak (revisit if
cycling becomes abusive). Hydrogen modeled as a single round-trip block, not
separate electrolyzer/storage/turbine units.

## Consequences

- `resource_costs.csv` storage rows gain cost_power_kw_yr / cost_energy_kwh_yr /
  duration_min_h / duration_max_h columns for split techs.
- PP-04 adds an energy-build decision variable and constraints that relate power
  MW × duration_hours = energy MWh within per-tech bounds.
- ATB 2024 (Li-ion), LDES Council / DOE Long-Duration Storage Shot (LDES), DOE
  Hydrogen Program record (H₂) are the cost sources.
