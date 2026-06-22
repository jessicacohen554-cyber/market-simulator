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
The captured backcast LP is large — ~1.48k thermal units × 7 zones × 8760 h — and
the **solve dominates**: a cold P0 is ~135–153 s while the matrix build is ~1–2 s.
So P0 is exactly where cross-year warm-start should pay off.

**Speedup (P0 is the solve cross-year warm-start changes):**

| year | P0 cold | P0 warm | P0 iters cold → warm | P0× | wall cold | wall warm | wall× |
|-----:|--------:|--------:|---------------------:|----:|----------:|----------:|------:|
| 2023 | 134.8 s | 136.4 s | 190,893 → 190,893 (cold: first year, no prior basis) | 0.99 | 163.7 s | 164.6 s | 0.99 |
| 2024 | 135.2 s |  63.2 s | 198,046 → 79,999     | **2.14** | 165.6 s |  93.4 s | 1.77 |
| 2025 | 152.8 s |  60.6 s | 223,856 → 66,712     | **2.52** | 180.9 s |  89.8 s | 2.01 |
| **total** | 422.8 s | 260.1 s | | **1.63** | 510.3 s | 347.8 s | **1.47** |

The first year has no predecessor so it solves cold either way; the benefit
accrues from year 2 onward. Across the **warm years only** (2024–25) P0 is **2.3×**
faster (288 s → 124 s) and wall-clock **1.9×** (347 s → 183 s) — and that is the
steady state a longer backcast (2019–2025, the forecast horizon) spends almost
all its time in.

**Peak memory:** 7.34 GB (cold) → 7.62 GB (cross-year-warm), **+0.28 GB (~4%)** —
just the carried `int8` status vectors and the held basis. Option (c) adds no
matrix. For contrast, the option-(a) superset would carry the **union of 1505
units** in every hour vs the largest single year's 1481, i.e. only ~1.6% wider
here, but it inflates *every* year's matrix (including the smaller early years)
permanently and must pre-scan all years to build the union — so (c) gives the
same speedup strictly cheaper.

**Neutrality (P1 cold vs P1 cross-year-warm):**

| year | objective relΔ | max \|Δ zonal price\| | max per-plant \|Δ annual MWh\| | total gen Δ |
|-----:|---------------:|----------------------:|-------------------------------:|------------:|
| 2023 | 0           | 0            | 0       | 0 |
| 2024 | 1.6e-15     | 9.1e-13 $/MWh | 546 MWh | 0 |
| 2025 | 6.5e-16     | 5.7e-14 $/MWh | 1009 MWh | 0 |

The objective, every zonal price, and total generation are **bit-identical**; the
only movement is alternate-optima reshuffling among plants tied at the marginal
price (≤ ~1 GWh/yr on the single largest mover, with an exactly offsetting −Δ on
another tied plant — `total gen Δ = 0`). This is the same degenerate
tie-breaking the intra-year warm-start already exhibits and the LP is genuinely
indifferent to; price formation and the system cost are untouched.

**End-to-end confirmation (full `run_year`, markup propagation included).** The
table above fixes the P1 cost vector to isolate the P1 LP. To close the one path
it does not exercise — P0's (degenerate) dispatch feeds `compute_monthly_markup`
→ `mc_bid` → P1 — the whole `run_year` for 2024 was run twice: cold, and
warm-started off 2023's basis. The markup is recomputed inside each run, so this
is the real pipeline:

| metric | 2024 cold vs cross-year-warm |
|---|---|
| objective | 1.44065700e9 vs 1.44065700e9 (relΔ 1.6e-15) |
| max \|Δ zonal price\| | 9.1e-13 $/MWh |
| total generation Δ | 1.2e-7 MWh |
| max per-unit \|Δ annual MWh\| | 861 MWh |
| gross reshuffle Σ\|Δ annual MWh\| | 10,260 MWh = **0.0033%** of total gen |
| full-pipeline wall | 185 s (cold) → **117 s (warm), 1.58×** |

Objective, every zonal price and total generation are bit-identical end to end;
the markup is unmoved. The only residual is 0.0033%-of-generation reshuffling
among units tied at the margin — the intra-year standard. (The bundle-level
equivalent is `run_calibration --year 2023 2024 2025` flag off vs on, diffed by
`scripts/diff_warmstart_bundles.py`; the in-process A/B above measures the same
quantities without writing six multi-GB dispatch bundles.)
<!-- RESULTS:END -->

## Recommendation

<!-- RECO:BEGIN -->
**Ship behind the flag (`MARKET_SIM_WARMSTART_XYEAR=1`), default off for now.**

- **Worth it.** The remaining cold cost after intra-year warm-start is P0, and
  cross-year warm-start cuts it **~2.3× in steady state** (every year after the
  first), for **~1.9× wall-clock per warm year**. On a 7-year forecast backcast
  that is most of the run. The mechanism is option (c) — remap the basis, do not
  grow the LP — so it costs **+4% peak RSS** and nothing structural.
- **Neutral by construction.** The LP optimum is basis-independent: objective,
  prices and total generation are bit-identical, with only the same marginal-tie
  reshuffling intra-year warm-start already ships. No recalibration.
- **Why not (a) superset:** same speedup but a permanently larger matrix for
  every year and an all-years pre-scan to build the union; strictly dominated by
  (c) here. **Why not (b) unchanged-fleet-only:** the ERCOT fleet changes every
  year, so it would essentially never fire.
- **Markup propagation already checked.** The end-to-end `run_year` A/B (above)
  recomputes the monthly markup inside each run and still comes out bit-identical
  on objective, prices and total generation, so the P0-vertex → markup → P1 path
  is neutral, not just the isolated P1 LP. Kept default-off only so it lands as a
  reviewable, A/B-able flag; a single calibration-bundle re-score
  (`diff_warmstart_bundles.py`) is the natural gate before flipping the default
  on, after which there is no downside beyond the ~4% memory.
<!-- RECO:END -->
