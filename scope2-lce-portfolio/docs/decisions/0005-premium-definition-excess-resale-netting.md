# 0005 — Premium definition & excess-resale netting

- **Status:** amended & ratified (stakeholder session 2026-07-02) — surplus is
  credited at the **full hourly ISO-average LMP** (`excess_sale_fraction = 1.0`);
  the provisional 0.75 haircut is removed. See Amendment below.
- **Date:** 2026-07-01 (amended 2026-07-02)
- **Session:** PS-02 (Premium Definition & Excess-Resale Netting)
- **Implemented by:** PP-04/PP-06

## Context

The premium is the headline metric and the Mode-A budget constraint. How surplus
clean generation is credited against grid purchases is decisive: at full-LMP
resale, cheap renewables make over-build almost free; a haircut surfaces the true
economic cost. This choice materially changes results and needs explicit anchor.

## Options considered

1. **Full-LMP resale** (f = 1.0) — surplus MWh paid at LMP; models ideal
   arbitrage; implies over-build is cheap for storage-plus-renewables.
2. **Haircut resale** (f < 1.0) — surplus credited at some fraction of LMP,
   representing basis/cannibalization/curtailment risk; more conservative;
   default f = 0.75.
3. **No resale** (f = 0) — surplus curtailed for zero value; overly pessimistic
   and doesn't reflect merchant opportunity.

## Decision

Surplus clean generation is credited at **excess_sale_fraction × LMP** with
**default excess_sale_fraction = 0.75**. The 0.75 haircut reflects
basis/cannibalization and curtailment risk; it is a fixed scalar, not
hour-varying or capped by volume. Curtailment emerges naturally when LMP ≤ 0
makes selling worthless. BAU baseline = buy all load at hourly LMP. Purchased
unbundled RECs do NOT count toward matching in v1 (Scope 2 focus). Premium is
reported per MWh of load, with outputs also showing $/yr and % over BAU.

## Consequences

- `config.excess_sale_fraction` defaults to 0.75; user overridable per sweep.
- Surplus at LMP × 0.75 appears in the net-cost calculation (lp.py constraint).
- PP-06 adds reporting columns: premium_per_mwh, premium_per_year, premium_pct_over_bau.
- No credit for surplus RECs in v1 (reserve REC monetization for future phase).

## Amendment (stakeholder ratification session, 2026-07-02)

**Decision changed: surplus clean generation is credited at the FULL hourly
ISO-average LMP — `excess_sale_fraction` default becomes 1.0.** The 0.75
haircut is removed as double-counting: surplus is already valued at the
model's *hourly* LMP, so renewable price cannibalization (surplus clearing in
depressed-price hours) is built into the credit by construction. Stakeholder
rationale (paraphrased): sellers should get the full LMP for that hour because
cannibalization is already built in; and since the tool has no locational
precision on where the renewable projects sit, the right price is the
**ISO-average** LMP — which is exactly the series the tool already consumes
(one price per ISO-hour, load-weighted average of zonal LMPs per the ADR 0011
export contract / `intake.collapse_zonal_lmp`). No separate nodal-basis or
curtailment haircut is applied at this granularity.

- The `excess_sale_fraction` config knob is **retained** (still validated in
  [0, 1]) for sensitivity runs; only its default changes.
- RECs remain out of scope: this netting is wholesale *energy* resale only;
  surplus RECs earn no credit in v1 (unchanged).

**Implementation note (follow-up build item, not yet applied):** change
`PortfolioConfig.excess_sale_fraction` default from `0.75` to `1.0` in
`src/lce_portfolio/config.py`, update its docstring (haircut rationale →
full-LMP rationale + ISO-average caveat), and adjust any tests/examples that
assume 0.75.
