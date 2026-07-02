# Vendored code

This directory holds logic **copied** from the market simulator (`src/market_sim`)
so the LCE portfolio tool is 100% standalone — there is no `import market_sim`
anywhere in this project.

## Rules

1. Every vendored module records at the top:
   - **What** was copied (function/behavior),
   - **From** which upstream file **and git revision** (`git rev-parse HEAD`),
   - **How** to re-sync (what to re-copy and what local adaptations to keep).
2. Keep vendored code minimal — copy only the slice you need, not whole modules.
3. Never import from `market_sim` to "save" a copy. The isolation guarantee is the
   whole point.
4. When upstream changes, re-sync deliberately (see each module's header) rather
   than silently drifting.

## Current contents

- `renewable_shapes.py` — renewable capacity-factor shape logic
  (`derive_cf_profile`, `derive_offshore_wind_profile`) from
  `src/market_sim/data/renewables.py`, plus the original single-node
  `capacity_weighted_collapse` reconciliation primitive (ADR 0011).
- `fossil_avg_rate.py` — `compute_fossil_avg_rate` from
  `src/market_sim/results/emissions.py`: the hourly fossil-only average CO2
  rate used to attribute residual carbon to unmatched grid purchases
  (ADR 0013). Parity with upstream is enforced by
  `tests/test_emissions.py::TestVendoredParityScope2` in the *market_sim*
  test tree (that test imports market_sim, so it cannot live here).
