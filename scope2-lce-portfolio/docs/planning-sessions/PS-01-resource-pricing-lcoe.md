# PS-01 — Resource Pricing / LCOE → fixed + VOM
**DECIDED → [ADR 0004](../decisions/0004-resource-pricing-lcoe-to-fixed-vom.md) (2026-07-01)**

**Goal:** decide how each generation resource's cost enters the LP, and pin the
low/mid/high numbers to a defensible source.

## Why it matters

The whole premium result scales with these costs. The current seed table
(`data/lcoe/resource_costs.csv`) uses ATB-ballpark LCOE placeholders converted to
annualized $/MW-yr via `fixed = lcoe · cf_assumed · 8760`. That conversion, the
source, and the sensitivity spread all need a real decision.

## Questions to decide

1. **Cost representation.** Pay-for-capacity (annualized fixed $/MW-yr + VOM,
   current) vs PPA-style pay-per-MWh (`lcoe · gen`)? Pay-for-capacity correctly
   penalizes over-build/curtailment; pay-per-MWh mirrors a real offtake contract.
   Can we support both via a flag?
2. **Source & vintage.** NREL ATB year? Which financial case (R&D vs
   Conservative)? Capital recovery factor / discount rate (`config.discount_rate`
   is currently unused — wire it in?).
3. **What LCOE includes.** Does the LCOE already fold in FOM and VOM? If so keep
   `vom=0`; if not, split them.
4. **cf_assumed.** For the annualization, is `cf_assumed` the ATB reference CF, or
   the resource's realized CF in the target ISO? (These differ; document the choice.)
5. **Sensitivity spread.** What do low/mid/high represent — cost declines,
   financing, or resource quality?

## Inputs to review

- `data/lcoe/resource_costs.csv`, `resources.py` (`load_resource_arrays`).
- NREL ATB tables for the chosen year.
- `docs/03-resource-catalog.md`.

## Deliverable

- ADR in `../decisions/` capturing the representation, source, CRF, and spread.
- Updated `resource_costs.csv` numbers (generation rows) with `notes` provenance.
- If pay-per-MWh is added: a `cost_representation` field in `PortfolioConfig` and
  a branch in `resources.py`/`lp.py` (spec it for PP-02).
