# 0008 — Existing-resource treatment: going-forward cost + EAC premium

- **Status:** accepted (stakeholder-decided 2026-07-01)
- **Date:** 2026-07-01
- **Session:** PS-05 (Existing-Resource Treatment & Additionality)
- **Implemented by:** PP-02

## Context

Existing nuclear and hydro are available at a fraction of new-build LCOE, raising
the **additionality** question: does procuring existing clean output reduce grid
emissions, or merely transfer existing supply? Cost structure and matching rules
must reflect this distinction.

## Options considered

1. **Full-LCOE existing** — treat existing same as new; inconsistent with real
   procurement; overstates cost.
2. **Going-forward only** — no credit for clean attribute; ignores the buyer's
   actual offer to procure incremental energy; understates impact.
3. **Going-forward + EAC premium** (chosen) — split cost into energy and attribute
   value; allows additionality toggle and PPA premium pricing.

## Decision

Existing nuclear/hydro are priced at **going-forward cost (energy basis, e.g.
nuclear ~$25–30/MWh)** PLUS a separate per-MWh **EAC premium** — a new
`eac_premium_mwh` cost component representing the price of the clean attribute
purchased on top of energy. Total variable cost = going-forward $/MWh +
eac_premium_mwh. `eac_premium_mwh` is a resource-level table column with
per-resource defaults, overridable via config. **Matching:** existing resources
count toward matching by default; an `additionality_only` config toggle (default
False) excludes them from the matching numerator when set. **Caps:** per-ISO caps
in the resource_caps table represent the plausibly-contractable share of the
existing fleet (not the whole fleet). **Hydro:** existing hydro is constrained by
a monthly energy budget (12 values, MWh/month) rather than a flat CF; budget input
specced for PP-02, LP constraint for PP-04. `resource_floors_mw` remains available
for must-take existing PPAs.

## Consequences

- `resource_costs.csv` gains eac_premium_mwh column for nuclear/hydro resources.
- New config field: `additionality_only` (default False).
- Per-ISO cap defaults go into resource_caps.csv (ADR 0009).
- New data input: monthly hydro energy budget (12 values per existing hydro
  resource, MWh/month). PP-02 specifies the schema.

## Amendment (2026-07-02, audit finding LP-1)

The additionality exclusion applies to existing generation **that serves
load**, not to exported existing energy. ADR 0007 (ratified) excludes surplus
from the matching metric entirely; counting exported existing MWh as
*unmatched load* both mis-stated the metric (matched% + unmatched% ≠ 100% of
load) and — in Mode B — let the matching constraint cap profitable existing
exports at the `(1 − target)·Σload` headroom, distorting the solve. The
accounting is now::

    unmatched_t = grid_buy_t + max(0, Σ_{r∈existing} gen[r,t] − excess_t)

with excess attributed to existing generation **first** (existing-first
attribution — the only LP-expressible choice; pro-rata needs a nonlinear
share and new-first needs integer logic). Implemented via the `exc_ex[t]`
auxiliary columns in `lp.py` (see `docs/01-lp-formulation.md`).
