# PS-02 — Premium Definition & Excess-Resale Netting
**DECIDED → [ADR 0005](../decisions/0005-premium-definition-excess-resale-netting.md) (2026-07-01)**

**Goal:** nail down exactly what "premium above wholesale" means, and how surplus
clean generation and grid purchases are valued.

## Why it matters

The premium is the headline metric and the Mode-A budget constraint. How we credit
surplus sales is decisive: at full LMP resale, cheap renewables make over-build
almost free and 100% matching looks trivially cheap (we saw this in the sample —
the demo now uses `excess_sale_fraction=0.3` to stay illustrative). This is a
modeling **choice**, not a bug, and needs an explicit decision.

## Questions to decide

1. **Excess credit.** Sell surplus at full LMP (`f=1`), a haircut (`f<1`, basis /
   cannibalization / curtailment risk), or not at all (`f=0`)? Fixed or
   ISO/hour-varying?
2. **Curtailment vs sale.** Is surplus always sellable, or is there a volume cap
   beyond which it's curtailed for zero?
3. **REC/EAC accounting.** Do surplus MWh generate saleable RECs? Do purchased
   unbundled RECs count toward matching (they shouldn't, for 24/7) — confirm.
4. **BAU baseline.** Is BAU "buy all load at LMP" (current), or a
   retail-rate/PPA-inclusive baseline? Does the premium include existing PPAs?
5. **Sign/units.** Premium reported per MWh of load (current). Confirm, and decide
   whether to also report $/yr and % over BAU.

## Inputs to review

- `lp.py` (premium constraint + `net_cost`), `config.excess_sale_fraction`,
  `outputs.py` (frontier fields).
- `docs/01-lp-formulation.md` (premium section).

## Deliverable

- ADR fixing `f` (value + whether it varies), curtailment rule, REC treatment, and
  the BAU baseline definition.
- Config default for `excess_sale_fraction` (and any new fields).
- Note for PP-04 (constraint) and PP-06 (reporting: add $/yr, %-over-BAU columns).
