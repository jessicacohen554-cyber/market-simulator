# Cross-year LP warm-starting (prototype)

## Problem

The calibration solves one ISO-year per `DispatchModel`. Two warm-start levels
exist around it:

- **Intra-year (shipped, default on):** P0 (base marginal cost) and P1 (base +
  startup markup) solve the *same* LP and differ only in the objective, so the
  model is built once and P1 re-costs P0's optimal basis in place
  (`changeColsCost`). P1 then converges in a handful of simplex iterations — the
  ~5x the calibration banks. Toggle `MARKET_SIM_WARMSTART=0`.
- **Cross-year (this prototype, `MARKET_SIM_WARMSTART_XYEAR=1`):** once intra-year
  warm-start has made the P1 second solve cheap, the one remaining cold solve in
  each year is **P0**. Adjacent years share zones, network and most units, so the
  previous year's optimal basis is a strong warm start for this year's P0.

`runner.py` (the frontend / scenario-export path) previously did **two cold**
`solve_dispatch` calls for P0/P1, ignoring intra-year warm-start entirely. This
PR also unifies it onto the build-once / re-cost `DispatchModel` pattern (gated
by the same `MARKET_SIM_WARMSTART` flag) — the free ~5x that the calibration
already had.

## The hard part: matching LP dimensions

HiGHS can only *load* a basis whose dimensions match the target LP, and the fleet
changes year to year (retirements/additions), so the column count differs. Three
options were considered:

- **(a) Superset fleet** — one constraint matrix over the union of units across
  all years, availability zeroed for absent units. Dimensionally stable, the
  basis transfers directly, but the matrix is permanently sized to *every* unit
  that ever runs: a wider thermal block in **every** hour, i.e. a larger,
  more memory-hungry LP for all years, including the early ones.
- **(b) Consecutive-year warm-start only when the fleet is unchanged** — trivial,
  but in a real backcast the fleet changes every year (ERCOT adds batteries and
  gas, retires coal), so it would essentially never fire.
- **(c) Map/pad the prior basis onto the new column set (shipped here)** — carry
  the basis plus enough layout identity to remap it: surviving generators matched
  by `unit_id`, index-stable per-hour blocks (wind/solar/storage/flow/slack/dump,
  by zone/unit position) copied directly, new columns left nonbasic-at-bound and
  new rows left basic so HiGHS repairs the few inconsistencies. **No memory cost**
  — each year keeps its own, smaller matrix.

Key structural fact that makes (c) cheap and safe: **a generator add/retire
changes only columns** — capacity is a column bound and generation enters the
energy balance through coefficients, not new rows — so the energy-balance rows
(`n_zones*T`, hour-major) and storage SOC rows (`n_storage*T`, unit-major) are
the two dimensionally well-defined blocks the prior basis maps onto. And because
**an LP's optimum is independent of the starting basis**, a wrong or partial
mapping costs only solver iterations, never correctness — the same neutrality
guarantee the intra-year warm-start relies on.

We ship **(c)** behind a flag: it captures the bulk of the benefit with zero
memory penalty, where (a) would inflate every year's matrix.

## Implementation

- `DispatchModel.export_cross_year_basis()` — snapshots the current optimal
  basis as compact `int8` status vectors plus the layout/`unit_id` identity.
- `DispatchModel.apply_cross_year_basis(prev)` — remaps `prev` onto this model's
  columns/rows and loads it as an *alien* HiGHS basis. Must precede the first
  `solve`. Returns `False` (cold fallback) on horizon mismatch.
- `scripts/run_calibration.py` threads a single-element `xyear_cache` through
  `main()` → `run_year()`: each year applies the prior basis to P0 and stores its
  own basis for the next year. Years run in the order requested, so list them
  chronologically.
- Regression test `tests/test_cross_year_warmstart.py` pins generation/price
  neutrality across a changed fleet.

## Measured results (ERCOT 2023 → 2024 → 2025, 8760h)

Benchmark: `scripts/bench_warmstart_xyear.py` (captures the real backcast LP per
year once, then times cold vs cross-year-warm). Full output in
`results/warmstart_xyear_bench.txt`.

<!-- RESULTS:BEGIN -->
_(filled from the benchmark run — see results/warmstart_xyear_bench.txt)_
<!-- RESULTS:END -->

## Recommendation

<!-- RECO:BEGIN -->
_(filled below from the measured speedup / drift)_
<!-- RECO:END -->
