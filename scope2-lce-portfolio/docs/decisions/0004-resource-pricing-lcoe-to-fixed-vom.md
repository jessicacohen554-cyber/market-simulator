# 0004 — Resource pricing: pay-for-capacity from NREL ATB

- **Status:** accepted (stakeholder-decided 2026-07-01)
- **Date:** 2026-07-01
- **Session:** PS-01 (Resource Pricing / LCOE → fixed + VOM)
- **Implemented by:** PP-02

## Context

Each generation resource's cost enters the LP as an annualized fixed expense plus
a variable O&M charge. The original seed table used ATB-ballpark LCOE placeholders
converted via `fixed = lcoe · cf_assumed · 8760`, but this conversion obscures
source, spreads, and the actual cost structure of capital-heavy clean tech.
The decision fixes the cost representation, source vintage, and capital recovery
factor to ground the premium result in defensible data.

## Options considered

1. **Pay-for-capacity** (fixed $/MW-yr + VOM $/MWh) — reflects how the buyer
   procures and pays risk to the developer; penalizes over-build and curtailment
   correctly; harder to match PPA contracts directly.
2. **PPA pay-per-MWh** (lcoe × generation) — mirrors a real power-purchase
   agreement structure but makes curtailed energy free to the buyer, understating
   the over-build cost of renewable portfolios.
3. **Hybrid config flag** — support both modes with a `cost_representation` field
   — rejected for now; revisit only when a use case demands it.

## Decision

Adoption of **pay-for-capacity** representation: each resource incurs an
annualized fixed cost (CAPEX × 1000 × CRF + FOM × 1000) in $/MW-yr plus a
separate variable O&M in $/MWh. Source: **NREL ATB 2024**, with mid = Moderate,
low = Advanced, high = Conservative case; the spread represents technology-cost
and financing trajectories, not resource quality. Capital recovery factor is
computed as CRF = r(1+r)^n / ((1+r)^n − 1), with r = `config.discount_rate`
(default 0.07) and n = ATB capital recovery period (30 yr default, per-tech where
ATB differs). No PPA pay-per-MWh mode in v1 (deferred, pending config-flag proposal).

## Consequences

- `resource_costs.csv` generation rows now include capex ($/kW), fom ($/kW-yr),
  and crf computation; `notes` column documents ATB case and recovery period.
- `cf_assumed` becomes documentation-only; realized CF emerges from dispatch.
- `config.discount_rate` is wired into cost annualization (currently unused
  elsewhere; reserve for future storage/transmission analysis).
- PP-02 rebuilds all generation cost rows from ATB 2024 mid/low/high cases.
