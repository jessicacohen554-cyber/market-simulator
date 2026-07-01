# PS-03 — Storage Costing (power/energy split, LDES, hydrogen)
**DECIDED → [ADR 0006](../decisions/0006-storage-costing-tranches-power-energy-split.md) (2026-07-01)**

**Goal:** decide how storage capital and efficiency are represented, across
4/8/12-hour batteries, long-duration (LDES), and hydrogen.

## Why it matters

Storage is what buys the last increments of hourly matching (the sample shows
battery MW rising with the premium cap). The current table collapses each tech to
one all-in `$/MW-yr` at a fixed duration — but real storage cost is a **power**
component ($/kW) plus an **energy** component ($/kWh), which is exactly what makes
long-duration cheap per-kWh and short-duration cheap per-kW.

## Questions to decide

1. **Power/energy split.** Move from single `$/MW-yr` to `$/kW-yr(power)` +
   `$/kWh-yr(energy)`, letting the LP also choose duration? Or keep fixed-duration
   tranches (current, simpler)?
2. **LDES & hydrogen.** Iron-air / flow (LDES) and hydrogen round-trip parameters:
   RTE, self-discharge, min/max duration, capital. Hydrogen especially — model as
   a single round-trip block, or separate electrolyzer / storage / turbine?
3. **Degradation & cycling.** Add a throughput/degradation adder beyond the
   `storage_epsilon` tiebreak? Calendar life vs cycle life.
4. **Efficiency convention.** Currently `η = √rte` split evenly charge/discharge.
   Keep, or asymmetric?
5. **Which techs are active by default** per ISO / study.

## Inputs to review

- `resource_costs.csv` (storage rows), `resources.py` (storage handling),
  `lp.py` (SOC dynamics, power/energy bounds).
- ATB / LDES Council / DOE hydrogen cost references.

## Deliverable

- ADR fixing the cost structure (all-in vs power+energy), tech parameters, and
  degradation treatment.
- Updated storage rows (and possibly new table columns / a `StorageTech` spec).
- Note for PP-02 (cost parse) and PP-04 (if duration becomes a variable, add the
  energy-vs-power decision columns and constraints).
