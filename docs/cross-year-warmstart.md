# Cross-year LP warm-starting

**Status: default ON for the calibration/backcast path** (the calibration CLIs
`scripts/run_calibration.py` / `scripts/run_calibration_full.py` set
`MARKET_SIM_WARMSTART_XYEAR=1` unless `--no-xyear-warmstart` is passed or the env
var is set explicitly). The forecast path (`runner.py`) stays **cold-only** —
see [Why the forecast path is not wired](#why-the-forecast-path-is-not-wired).
Reproducibility baselines (`scripts/replay_keeper.py`,
`scripts/capture_keeper_goldens.py`, the D-13 `bench-repro.yml` gate) pin it OFF
so byte-identity stays basis-independent.

## Problem

The calibration solves one ISO-year per `DispatchModel`. Two warm-start levels
exist around it:

- **Intra-year (shipped, default on):** P0 (base marginal cost) and P1 (base +
  startup markup) solve the *same* LP and differ only in the objective, so the
  model is built once and P1 re-costs P0's optimal basis in place
  (`changeColsCost`). P1 then converges in a handful of simplex iterations — the
  ~5x the calibration banks. Toggle `MARKET_SIM_WARMSTART=0`.
- **Cross-year (`MARKET_SIM_WARMSTART_XYEAR`, default on for calibration):** once
  intra-year warm-start has made the P1 second solve cheap, the one remaining cold
  solve in each year is **P0**. Adjacent years share zones, network and most
  units, so the previous year's optimal basis is a strong warm start for this
  year's P0. The calibration CLIs enable it by default (`--no-xyear-warmstart`
  opts out); the forecast path stays cold-only.

`runner.py` (the frontend / scenario-export path) previously did **two cold**
`solve_dispatch` calls for P0/P1, ignoring intra-year warm-start entirely. This
PR also unifies it onto the build-once / re-cost `DispatchModel` pattern (gated
by the same `MARKET_SIM_WARMSTART` flag) — the free ~5x that the calibration
already had.

**Cross-year warm-start is deliberately scoped to the calibration/backcast path
only** — it is *not* wired into `runner.py`'s forecast loop. The forecast evolves
the fleet year-by-year, and that feedback loop makes cross-year warm-start
non-neutral on the forecast trajectory even though it stays bit-neutral within
each year. See [Why the forecast path is not wired](#why-the-forecast-path-is-not-wired)
for the investigation and measurements.

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
- `scripts/run_calibration.py` and `scripts/run_calibration_full.py` each thread
  a single-element `xyear_cache` through their sequential year loop → `run_year()`:
  each year applies the prior basis to P0 and stores its own basis for the next
  year. Years run in the order requested, so list them chronologically.
- `resolve_xyear_warmstart_default()` (in `run_calibration.py`, shared by both
  CLIs) resolves the gate: `--no-xyear-warmstart` forces OFF, an explicit
  `MARKET_SIM_WARMSTART_XYEAR` env var is honored, otherwise it defaults ON. It
  runs only on the fresh-solve path — `--report`/`--replay-bundle`/
  `--rebuild-benchmark` and the direct `solve_and_persist` callers
  (`scripts/replay_keeper.py` et al.) stay at the global default OFF.
- Regression tests: `tests/test_cross_year_warmstart.py` pins generation/price
  neutrality across a changed fleet; `tests/test_xyear_warmstart_default.py` pins
  the default-resolution precedence and the forecast cold-only invariant
  (`runner.py` passes `xyear_cache=None`).

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
**Default ON for the calibration/backcast path** (`MARKET_SIM_WARMSTART_XYEAR`,
flipped from default-off after the single-bundle A/B gate below passed for ERCOT
and MISO). The calibration CLIs (`run_calibration.py`, `run_calibration_full.py`)
enable it unless `--no-xyear-warmstart` is passed or the env var is set
explicitly; the forecast path (`runner.py`) stays cold-only, and reproducibility
baselines pin it off.

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
  is neutral, not just the isolated P1 LP. The gate before flipping the default
  on was a single calibration-bundle re-score (`diff_warmstart_bundles.py`) for
  ERCOT and a big co-opt ISO (MISO) — see [Bundle-level gate](#bundle-level-gate-ercot--miso-full-8760h)
  below. That passed, so the default is now ON for calibration — the only
  downside is the ~4% memory.
<!-- RECO:END -->

## Bundle-level gate (ERCOT + MISO, full 8760h)

The pre-flip gate: full 3-year backcast (2023→2024→2025, 8760 h, one-thread so
cold-vs-cold is deterministic) solved cold (`--no-xyear-warmstart`) and warm
(default), then diffed with `scripts/diff_warmstart_bundles.py` and a price /
served-load check on `system.parquet`.

**Speedup — the warm-year P0 (the solve cross-year warm-start changes):**

| ISO | year | P0 cold | P0 warm | P0× | total cold | total warm |
|-----|-----:|--------:|--------:|----:|-----------:|-----------:|
| ERCOT | 2023 | 195.9 s | 197.2 s | 0.99 (first year, no prior basis) | 318.0 s | 312.7 s |
| ERCOT | 2024 | 194.5 s |  93.3 s | **2.08** | 281.7 s | 181.8 s |
| ERCOT | 2025 | 224.0 s |  87.2 s | **2.57** | 300.7 s | 178.9 s |
| MISO  | 2023 | 311.6 s | 312.6 s | 1.00 (first year) | 513.2 s | 517.0 s |
| MISO  | 2024 | 312.5 s | 124.2 s | **2.52** | 473.9 s | 309.3 s |
| MISO  | 2025 | 267.0 s | 104.6 s | **2.55** | 401.3 s | 267.7 s |

Across the warm years only (2024–25): ERCOT P0 **2.32×** (418.5 → 180.5 s), MISO
P0 **2.53×** (579.5 → 228.8 s). Whole-run wall: ERCOT 933 → 706 s (1.32×), MISO
1400 → 1106 s (1.27×) — diluted by the always-cold first year and the fixed
data-prep / markup / results-write overhead a single 3-year run also carries.

**Neutrality (cold vs warm, per year):**

- **Objective:** identical — an LP's optimum value is basis-independent and both
  solves reach it.
- **Served load** (`demand − slack`) **and dump/spill:** bit-identical in every
  ISO-year (max |Δ| = 0 MW).
- **Total generation:** bit-identical (|Δ| ≤ 0.06 GWh on 463–664 TWh, i.e.
  ~1e-7 relative — display rounding).
- **Zonal prices:** bit-identical for ERCOT (all three years, max |Δ| ≤ 2e-14
  $/MWh) and MISO 2023–2024. **MISO 2025** is the one exception: 182 of 61,320
  zone-hours (0.3 %) report a **0.1495 $/MWh** price difference (load-weighted
  Δ = 2.4e-4 $/MWh). This is **dual degeneracy** — the price analogue of the
  primal marginal-tie reshuffle: at a degenerate optimal vertex the marginal
  unit is not unique (here two units at mc 32.59 vs 32.74), so cold and warm
  report different-but-equally-optimal clearing duals. The primal (served load,
  total gen, objective) is untouched.
- **Per-unit dispatch reshuffle** (Σ|Δ hourly MW| / total gen): ERCOT 0.038 %
  (2024) / 0.112 % (2025); MISO 0.004 % (2024) / 0.005 % (2025) — all confined
  to units tied at the marginal price, the same alternate-optima the intra-year
  warm start already ships (`total gen Δ = 0`).

Verdict: objective, served load and total generation identical; price and
per-unit dispatch differences confined to marginal ties (primal) and their dual
analogue (MISO-2025 degeneracy). Passed → default flipped ON for calibration.

## Why the forecast path is not wired

The natural follow-on is to thread the same `xyear_cache` through `runner.py`'s
year loop: the forecast (`run_scenario_iso`) runs a long, chronological year
horizon in one process, so the ~2.3× steady-state P0 speedup would compound far
more there than in the 1–3 year calibration. This was prototyped and then
**rejected** — on the forecast path cross-year warm-start is *not* neutral, and
the speedup is not worth perturbing the forecast trajectory.

**The forecast has a feedback loop the calibration does not.** In the calibration
each backcast year's fleet is built independently from data, so a year's solve
never feeds the next year's inputs — the cross-year basis only changes the solve
path, and the A/Bs above are bit-identical. In the forecast each year's fleet is
*evolved from the prior year's dispatch*: `capacity.evolve_fleet` runs an economic
retirement / new-entry screen whose per-unit inputs come from
`prior_results["dispatch_result"]`. The retirement screen (`capacity.py`) scores
each unit on its annual energy revenue and inframarginal margin,
`Σ_t price·dispatch[i]` and `Σ_t (price − mc[i])·dispatch[i]` — both **per-unit
dispatch volumes**.

**Within-year neutrality does not survive that loop.** Cross-year warm-start is
still bit-neutral *within* each year — objective, every zonal price and total
generation are identical — but the one thing it does move, the alternate-optima
reshuffling among units tied at the marginal price (the same ≤0.0033% churn the
intra-year warm-start already ships), is exactly the per-unit dispatch the
retirement screen reads. A reshuffle that the LP is genuinely indifferent to can
nudge a unit sitting near the retire/keep threshold across it, so the *next*
year's fleet — and therefore its prices and dispatch — differ.

**Measured (ERCOT, reduced 168 h, `MARKET_SIM_HIGHS_THREADS=1` so the solve is
deterministic, forecast 2026→2032).** Cold (`MARKET_SIM_WARMSTART_XYEAR=0`) vs
warm (`=1`), diffing each cached year:

| year | objective relΔ | max \|Δ zonal price\| | note |
|-----:|---------------:|----------------------:|------|
| 2026 | 0 | 0 | first year solves cold either way |
| 2027 | 2.6e-16 | 7.1e-15 $/MWh | within-year neutral; per-unit dispatch reshuffles (~hundreds of MWh on a tied unit) |
| 2028 | 8.3e-4 | 0.19 $/MWh | reshuffle tipped a 2027 retire/keep decision → different 2028 fleet |
| 2029 | 4.9e-5 | 0.39 $/MWh | |
| 2030 | 1.9e-6 | 5.6e-3 $/MWh | |
| 2031 | 5.6e-16 | 2.1e-14 $/MWh | back to bit-identical |
| 2032 | 3.1e-4 | 0.20 $/MWh | |

The divergence is **bounded and intermittent**, not compounding (some years
return to bit-identical, the gen count matches every year), but it is real and
attributable to the mechanism: the **cold-vs-cold** control at `THREADS=1` is
bit-identical across all years, so this is the warm-start reshuffle propagating
through a discrete capacity decision, not solver nondeterminism. (At the default
multi-threaded setting even cold-vs-cold drifts, because parallel dual simplex
breaks marginal ties nondeterministically — which is the same class of effect,
just from a different source.)

**Decision: keep cross-year warm-start to the calibration path only.** Wiring the
forecast would trade a real (if small, ≤~0.4 $/MWh) change to the forecast
trajectory for the solve speedup, which is not an acceptable swap for a flag whose
whole premise is neutrality. Making it neutral would require the capacity screen
to depend only on the basis-independent quantities (prices, system totals) rather
than per-unit marginal-tie dispatch — a separate change to the economics that
needs its own validation, not a warm-start change. Until then the forecast loop
stays on intra-year warm-start (`MARKET_SIM_WARMSTART`, bit-neutral) only.
