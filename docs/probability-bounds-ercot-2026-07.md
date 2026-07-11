# ERCOT probability-bounded emissions forecast — PB-5 production run (2026-07)

**STATUS: RUN IN PROGRESS — numbers in this file are placeholders until the
assembly step fills them; do not quote until this banner is removed.**

The first real probability-bounded emissions forecast for ERCOT (the calibrated
reference ISO): the landed PB-0..PB-4 machinery driven end-to-end on real HiGHS
solves, forecast mode 2026–2050. Design: `docs/handoffs/probability-bounds-plan-2026-07.md`;
this document is the PB-5 deliverable report that plan's prompt pack requires.

## Headline (placeholders)

| Year | P10 | P50 | P90 |
|---|---|---|---|
| 2030 | TBD | TBD | TBD |
| 2050 | TBD | TBD | TBD |

Published band = parametric ⊕ structural (dispatch-conditional). Fan chart:
`docs/codebase-site/forecast-bands.html#` ensemble `ercot-pb5-band-v2`.

## What was run (filled as phases complete)

- Step 0 (measurement): TBD
- Phase 1 — n=16 LHS sampler, 2026–2050, seed 7: TBD
- Phase 2 — 13-case scenario matrix: TBD
- Phase 3 — A-2 rho sensitivity (paired n=8 × {0.0, 0.6}): TBD

## Honest limitations

See `results/ensemble/ercot-pb5-band-v2/honest_limitations.json` (surfaced
verbatim on the fan-chart page) — dispatch-conditional λ(h)=0, datacenter axis
absent, AEO2025 anchors, n=16 vs the n=64 spec batch, weather pool restricted
to 2021/2023–2025 by forecast-path coverage, structural-prior basis-stale
carbon-priced ISOs, sensitivity at paired n=8.

## Findings log (filled as discovered)

- Forecast-path weather coverage gap: `WEATHER_YEAR_POOL_BY_ISO` 2019/2020
  entries fail in forecast mode (generation-distribution parquet floor 2021).
