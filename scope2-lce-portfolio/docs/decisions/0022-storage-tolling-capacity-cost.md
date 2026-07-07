# 0022 — Storage priced as a capacity-grounded tolling fixed cost

- **Status:** accepted
- **Date:** 2026-07-07
- **Session:** scope-2 EAC diagnosis + wiring
- **Implemented by:** `resources.py` / `config.py` / `data/lcoe/resource_costs.csv`

## Context

Storage carries no energy attribute — it re-times clean MWh — so an EAC does not
fit it. Its cost is **capacity-grounded, not generation-grounded**, and the owner
wants to reflect real 5-year tolling agreements and to offer 4/8/12-hour
batteries alongside iron-air LDES and hydrogen. The existing `capex_fixed`
storage treatment is already capacity-grounded (`fixed_mwyr` is a $/MW-yr paid
regardless of dispatch, VOM≈0); what was missing was sourcing that fixed number
from a market tolling price instead of ATB-capex annualization, and a 12-hour
duration row. Full RA/ELCC capacity crediting was explicitly **not** wanted for
this pass.

## Options considered

1. **Full RA constraint + duration-dependent ELCC** — structural, needs per-ISO
   capacity prices and ELCC curves. Deferred (owner: "I don't need the ELCC").
2. **A separate `tolling` cost basis with duplicate battery rows** — clean but
   doubles the storage catalog.
3. **A `storage_pricing` config switch on the existing rows** — chosen.

## Decision

- `config.storage_pricing ∈ {"capex", "tolling"}` (default `"capex"`,
  back-compatible). Under `"tolling"`, fixed-duration storage takes
  `fixed_mwyr = tolling_kw_yr_{sensitivity} × 1000` from the cost table in place
  of `capex × CRF + FOM`. A selected storage row with no tolling price for the
  chosen sensitivity is a hard error.
- New cost-table columns `tolling_kw_yr_{low,mid,high}` and
  `contract_term_years`. The term is the contract commitment length —
  informational in a single representative-year LP; the annual `$/kW-yr` is what
  enters. Storage stays capacity-grounded either way (VOM≈0).
- `battery_12h` added; iron-air LDES and hydrogen keep their split power/energy
  capex basis (unaffected by tolling).

## Consequences

- Storage cost can be sourced from a tolling contract or ATB capex; the shipped
  tolling anchors ≈ each row's own capex-annualized+FOM, pending market quotes.
- Arbitrage value is unchanged — it still flows through the hourly LMP energy
  balance; tolling only changes the fixed capacity number.
- Deferred: true RA/ELCC capacity crediting (a future ADR).
