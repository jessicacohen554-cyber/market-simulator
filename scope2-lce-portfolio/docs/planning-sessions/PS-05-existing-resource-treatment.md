# PS-05 — Existing-Resource Treatment & Additionality

**Goal:** decide how already-operating clean resources (existing nuclear, hydro)
enter the portfolio and whether they count toward matching.

## Why it matters

The user explicitly wants existing nuclear available as an input but **capped**.
Existing resources have a very different cost basis (going-forward, not new-build
LCOE) and raise the **additionality** question central to credible 24/7 claims:
does procuring existing clean output actually reduce grid emissions?

## Questions to decide

1. **Cost basis.** Price existing nuclear/hydro at going-forward cost (current
   `nuclear_existing` seed ~$30/MWh) or at a contracted PPA price? Where sourced?
2. **Cap semantics.** Is the cap a share of the ISO's existing fleet the buyer can
   plausibly contract, or a hard resource limit? Per-ISO values.
3. **Additionality.** Do existing resources count toward matching at all, or only
   new/additional builds? Offer an `additionality_only` toggle?
4. **Hydro modeling.** Existing hydro needs a monthly energy budget (not a flat
   CF) — spec the budget input and the LP constraint (mirror the market-sim hydro
   monthly-budget idea, vendored).
5. **Floors vs caps.** Use `resource_floors_mw` for must-take existing PPAs?

## Inputs to review

- `resource_costs.csv` (`nuclear_existing`, `hydro_existing`), `config`
  (`resource_caps_mw`, `resource_floors_mw`), `resources.py`.

## Deliverable

- ADR on cost basis, cap semantics, additionality rule, and hydro-budget modeling.
- Per-ISO cap defaults; any new config toggle (`additionality_only`).
- Hydro monthly-budget spec for PP-02/PP-04.
