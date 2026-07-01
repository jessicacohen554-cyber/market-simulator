# PS-04 — Matching Semantics

**Goal:** define precisely what "hourly matching" counts, and how residual grid
purchases are treated for carbon.

## Why it matters

"24/7 CFE" has several definitions. Our metric is annual hourly matching
`1 − Σ grid_buy / Σ load`, with surplus excluded. The strict per-hour variant and
the carbon accounting of the unmatched remainder need explicit decisions.

## Questions to decide

1. **Annual vs strict per-hour.** Mode B supports both (`strict_hourly_matching`).
   Which is the headline? For Mode A, matching is inherently hourly (grid_buy per
   hour) — confirm that's the intended CFE score.
2. **Surplus exclusion.** Confirm surplus clean generation does **not** count
   toward matching (it's sold, not consumed by our load). This is the 24/7 rule.
3. **Storage & matching.** Energy discharged from storage that was charged from
   the grid in an unmatched hour — does it count as clean? (Round-trip provenance.)
   Current model charges storage from the aggregate node; decide the accounting.
4. **Residual carbon.** Attribute grid_buy emissions at the ISO marginal or
   average rate? Report residual tCO₂ per setpoint?
5. **Matching denominator.** Gross load vs load net of any existing on-site clean.

## Inputs to review

- `lp.py` (matching identity, `matching_pct`), `config.strict_hourly_matching`,
  `docs/01-lp-formulation.md`.

## Deliverable

- ADR fixing the matching definition, storage provenance rule, and carbon
  attribution.
- If carbon reporting is added: an emissions-rate input and a `residual_co2`
  output column (spec for PP-06).
