# Cross-year LP warm-starting

**Status: default ON for the calibration/backcast path** (the calibration CLIs
`scripts/run_calibration.py` / `scripts/run_calibration_full.py` set
`MARKET_SIM_WARMSTART_XYEAR=1` unless `--no-xyear-warmstart` is passed or the env
var is set explicitly). The forecast path (`runner.py`) **is wired** behind
`ScenarioConfig.forecast_xyear_warmstart` (D-9, 2026-07-26) but every forecast
**bundle** runs it OFF (D-10, 2026-08-04, for resume-reproducibility) — so in
practice the forecast is cold-only. The section titled
[Why the forecast path is not wired](#why-the-forecast-path-is-not-wired) is the
pre-D-9 record; read its two status updates at the end for the current state.
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
`scripts/diagnostics/diff_warmstart_bundles.py`; the in-process A/B above measures the same
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
(default), then diffed with `scripts/diagnostics/diff_warmstart_bundles.py` and a price /
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

**Status update (wave 4C, 2026-07-25): the screen-side blocker is closed; the
flag is unchanged.** The "separate change to the economics" named above has now
landed in two parts, so the two `Σ_t …·dispatch[i]` terms quoted at the top of
this section are both stale:

* the **energy margin** became the basis-independent attainable (pro-forma)
  margin `max(0, price − mc, reserve) × pmax × availability` (earlier work, the
  Potomac SOM net-revenue construction); and
* the **attribute-revenue term** (EAC / RPS / §45U) — the last remaining
  realized-dispatch reader — is now credited on attainable in-merit generation
  `cap_mw × 1[price > mc]`, with §45U's gross-receipts phase-down taken on that
  same attainable basis on both sides of its ratio
  (`capacity_evolution/retirements.apply_economic_retirements`).

The retire/keep decision is therefore a function of prices, `mc` and capacity
only, and is invariant to any marginal-tie reshuffle — pinned by
`tests/test_forecast_warmstart_tie_invariance.py`.

Wave 4C itself did **not** flip anything — it removed the mechanism that made
warm start non-neutral, which is a *precondition* for the D-9 default flip, not
the flip.

**Status update (D-9, 2026-07-26): the A/B has now been run and the forecast
path IS wired, default ON.** The measured table at the top of this section is
therefore historical — it records the pre-4C behaviour and must not be quoted as
current.

* The switch is `ScenarioConfig.forecast_xyear_warmstart` (default **True**), a
  registry field rather than an env knob (rule 24 [R-REGISTRY]). `runner.py`
  gates its year-loop basis holder on it and passes it to `run_energy_solve` as
  an explicit `xyear_warmstart` override, so the calibration CLIs' default-ON
  `MARKET_SIM_WARMSTART_XYEAR` can never decide the forecast's behaviour. Set
  the field `False` for a strictly cold forecast; that value enters the
  `cache_key` as a distinct scenario.
* An explicitly-gated caller also bypasses the persisted year-1 basis NPZ cache
  (`pipeline.basis_cache`), which is keyed `(iso, weather_year, hours)` with no
  sim-year — seeding a 25-year horizon from it would make a run depend on
  whatever solved before it.
* **The guardrail passed.** Full-horizon ERCOT 2026-2050, 8760 h, threads=1:
  every capacity quantity — per-fuel capacity, builds, retirements, reserve
  margin, peak demand, max hourly price — **bit-identical in all 25 years**,
  against 51.1 min → 25.1 min wall (2.04× overall, 2.20× on the warm-startable
  years). Residuals are marginal-tie/dual noise only: load-weighted price
  2.5e-5, CO2 6.6e-6 relative. The same 168 h 2026→2032 experiment tabulated
  above, re-run post-4C, now shows **no divergence at all**.
* Note the honest limit: 4C removed the realized-*dispatch* reader, but the
  screen still reads **prices**, which are duals and can pick a different
  optimal vertex under degeneracy. So the guardrail was a genuine test; what it
  shows is that the residual dual noise is ~1e-5 and tips no retire/keep
  decision at ERCOT full-horizon scale — not that invariance is proven by
  construction.

**Multi-ISO follow-through (2026-07-27).** The flip is default-ON for every ISO,
so the ERCOT-only evidence was extended to the ISOs that exercise the paths
ERCOT does not have — the CR-1 sloped capacity demand curve and reserve
co-optimization, i.e. a wider degeneracy surface on exactly the dual channel the
bullet above leaves open. Result, in full: **all six ISOs pass the 168 h
pre-screen** (capacity trajectory identical, no price/CO2/reserve-margin delta),
and **three pass at full horizon 2026-2050** — ERCOT above, plus NEISO
(`lw_price` 1.5e-05 the only residual) and NYISO (every quantity 0.000e+00),
both with the §2.1a capacity-market clearing ON in both arms. The warm start was
verified to actually install a basis in every ISO rather than assumed
(`attempts=3 installed=3` warm vs `attempts=0` cold,
`scripts/probes/_d9_warmstart_spy.py`).

CAISO/PJM/MISO were **not** completed at full horizon — stopped by owner call at
three ISOs. The default is unchanged. The reasoning behind stopping matters more
than the missing runs: horizon length is not the informative variable for this
question — warm start reaches the forecast only by tipping a discrete
retire/keep threshold, so what bounds it is the dual noise measured against each
unit's distance to its threshold, not the number of years solved. Full record,
including the margin analysis that would actually bound it:
`docs/handoffs/wallclock-baseline-2026-07.md` §H3b.

Full experiment record, including the wall-clock table and the contention
caveat: `docs/handoffs/wallclock-baseline-2026-07.md` §H3/Exp 5.

**Status update (D-10, 2026-08-04): DISARMED on the forecast lane.** The field
still exists and still defaults `True`; what changed is that every shipped
forecast runner now passes `False` explicitly, so **forecast bundles run
cold-only again** — `run_full_horizon.reference_config`,
`run_capacity_hindcast.build_config` (T1-H / T1-X / T1-FF) and
`ff_readiness_battery.golden_posture_config`, all through the one reader
`scripts/lib/forecast_posture.shipped_forecast_xyear_warmstart`.

The cause is a case D-9's guardrail could not see, because it compared two
uninterrupted runs. A **resumed** run loads its earlier years from cache, and a
cache-loaded year never enters the solve branch, so it exports no basis: the
first freshly-solved year after a resume runs cold while the same year in an
uninterrupted control runs warm. The two land on different vertices of a
degenerate optimal face, so **a killed-and-resumed forecast is not reproducible
from its own cache**. FFR-3M measured this causally on NEISO 2026-2028 (drill
FAIL at the default; two independent no-kill controls byte-identical, ruling out
run-to-run nondeterminism; the same drill GREEN with the flag off, all three
years byte-identical including the freshly-solved one) and found the **cold
answer is the canonical one** — the ablation's value equals the resume leg's,
not the warm control's.

Pinning a basis so warm and cold agree was put to the owner and **refused**: the
retirement screen reads per-unit dispatch volumes, so a pinned vertex would let
a solver setting silently select which marginal units retire (the tie-flip
measured earlier in this document). The ~2.3× P0 speedup is an **accepted cost**
of the decision — at horizon scale, ERCOT 2026-2050 returns from 25.1 min to
51.1 min — and is not to be recovered by re-arming, tie-breaking or ordering
freezes.

Implementation note that matters for anyone reading a cache: the disarm is an
explicit argument, **not** a default flip, because a default flip would have
left every forecast cache key colliding with its warm predecessor (a registered
optional field drops at the *live* default) while moving all six backcast keeper
keys (which carry an explicit `true`). Measured both ways in
`docs/handoffs/ffr-3t-warmstart-off-2026-08-04.md`; cache epoch 2026-08-04 in
`src/market_sim/results/cache.py`. Decision record: sitting Addendum K.3
(`docs/handoffs/ffr-owner-sitting-2026-08-02.md`); adjudication:
`docs/handoffs/ffr-3m-kill-resume-verdict-2026-08-04.md`.

## Same-year P1 basis seed — the cold-rebuilt P1 seeded from the P0 basis (wallclock item B, 2026-09-06)

**Decision (2026-09-06): calibration-CLI default ON, `--no-p1-basis-seed` to opt
out, env var `MARKET_SIM_P1_BASIS_SEED` honored; inert under the goldens/replay
pin and on the forecast path.** Owner memo
`docs/handoffs/p1-basis-seed-decision-memo-2026-09.md` (the B-0 bench that
produced the number), signed **(A) FLIP** 2026-09-06 by chat instruction;
evidence for the shipped surface in
`docs/handoffs/wallclock-baseline-2026-07.md` §WALLCLOCK B.

> **SUPERSEDED TWICE — read this box before the section.**
>
> **(1) 2026-09-19, rule 36 `[R-YEAR-ISOLATION]` (owner ruling, miso-262): the
> default is now OFF.** `resolve_p1_basis_seed_default` returns `False` when
> the env var is unset. The ruling's evidence is about state crossing a *year*
> boundary (MISO's keeper reproduced the first year of each solve leg and
> diverged by 7.16–24.18 TWh in the later ones), and both env knobs were
> flipped together **because `pipeline/solve.py` armed the seed only inside the
> cross-year gate** — not because the same-year seed was measured at fault.
> Rule 36(e) withdrew the neutrality claims for both.
>
> **(2) 2026-09-20, PERF-C S1: the seed is no longer nested in the cross-year
> gate.** `docs/handoffs/FINDING-perfc-s1-p1-seed-2026-09-20.md`. The two knobs
> are now independently gateable, so the same-year seed can be defaulted ON
> while the cross-year one stays OFF — **that is an owner decision and it has
> not been taken; the default is still OFF.** PERF-C S1 changed the gate and
> added an optimality guard; it produced no new timing evidence and ran no
> solve to measure speed. **The "Gate" and "Class" paragraphs below are
> amended in place; the measured tables are the 2026-09-06 numbers and stand
> as history, under the caveat rule 36(e) attaches to them.**

**What it is.** On the ISOs whose keeper carries a P1-native floor bridge —
ERCOT (`ercot_gas_commitment_bridge`), NYISO (`nyiso_gas_commitment_bridge`),
CAISO (`caiso_ra_mustoffer`) — the P1 pass cannot re-cost the live P0 model in
place: the bridge replaces the fleet, the in-place refloor declines (the raised
availability feeds reserve-headroom / ramp *rows*), and `run_energy_solve`
builds a **second `DispatchModel`** on the floored fleet and, until this change,
solved it **from no basis at all** — a full cold P1 costing about as much as P0
(the "P1 ≈ P0" signature in the memo's §2 table). The seed is the shipped
cross-year machinery applied to the one place in a year it never reached: the
P0 model's optimal basis is exported once (the same `export_cross_year_basis`
the cross-year holder already takes on that branch, now taken whenever the seed
is armed) *before* the model is released, and the
second model installs it through `apply_cross_year_basis` before its first
solve — same `T`, same `unit_ids`, so `_cross_year_column_map` is the identity on
every per-hour block; `alien=True`, so HiGHS repairs the few statuses the
bridge's raised bounds make bound-inconsistent. The row copy is the shipped
conservative one (energy-balance + storage-SOC rows; every other row family
defaults to basic slack) — the form the memo measured; a same-year full-row copy
is a possible later tightening, gated exactly like the seed, and no number here
depends on it.

**The adaptive-pass leg.** The ercot-221 pass 2 and every ercot-230 fixed-point
iteration reach `run_energy_solve` with `reuse_p0_from` (C-1b) and therefore no
live P0 model. Their P1 is the identical floored LP under a different storage
discharge cost, so the *previous pass's P1 basis* is the closer seed: a pass
that may be followed by another passes `export_p1_basis=True`, the cold-rebuilt
P1 model's basis is exported onto `EnergySolveResult.p1_basis`, and the next
pass seeds from it (else from the P0 basis the previous cold route left in the
holder). The final iteration's export is one wasted `getBasis()` (the stop is
known only after the solve) — accepted.

**Gate (amended PERF-C S1, 2026-09-20).** Three conditions, all required, in
`pipeline/solve.py::run_energy_solve`:

1. `_warm` — the intra-year warm start (`MARKET_SIM_WARMSTART`) must be on,
   because the seed's *source* is the live P0 `DispatchModel` and
   `MARKET_SIM_WARMSTART=0` builds none. **This condition replaces `_xwarm`.**
   The old text read "the seed sits **inside** the cross-year gate, so
   `MARKET_SIM_WARMSTART_XYEAR=0` / `--no-xyear-warmstart` — the goldens,
   replay and merge-base-control pin — implies seed OFF with no second knob to
   remember", and that convenience is exactly what took the same-year seed down
   with rule 36's cross-year ruling. **There is now a second knob, and the
   places that relied on the implication pin it explicitly:** the
   `DETERMINISM_ENV` of `scripts/capture_keeper_goldens.py` and of
   `scripts/replay_keeper.py` both carry `MARKET_SIM_P1_BASIS_SEED=0` beside
   `MARKET_SIM_WARMSTART_XYEAR=0`. Nothing else read the implication.
2. `xyear_warmstart is None` — the backcast callers only. The forecast passes
   an explicit bool and is left cold by design, so no forecast cache key,
   resume reproducibility or trajectory is touched (rule 24 `[R-REGISTRY]`).
   **Unchanged.**
3. The env var itself, global default OFF, resolved by
   `resolve_p1_basis_seed_default` (`scripts/run_calibration.py`, the sibling
   of `resolve_xyear_warmstart_default` with the same precedence:
   `--no-p1-basis-seed` > explicit env var > default). Since rule 36 that
   default is **OFF**, so a fresh calibration solve no longer arms it either.

`--report` / `--replay-bundle` / `--rebuild-benchmark` and the direct
`solve_and_persist` callers (`capture_keeper_goldens.py`, `replay_keeper.py`)
stay at the global default OFF. Inert wherever the P1 re-solves the live P0
model (NEISO / PJM / MISO keepers, and any run with no floor hook).

**No cross-year state, by construction and by test.** The seed exports *this*
year's P0 basis and applies it to *this* year's P1, inside one
`run_energy_solve` call. When `_p1_seed` is armed and `_xwarm` is not, the
export runs but the cross-year holder is **not** written and the disposable
NPZ basis cache is hard-off (`basis_cache_enabled()` still requires
`MARKET_SIM_WARMSTART_XYEAR`), so nothing reaches the next year — which is the
property rule 36 `[R-YEAR-ISOLATION]` is protecting. Pinned by
`tests/unit/pipeline/test_xyear_warmstart_default.py::TestP1BasisSeedGate::test_seed_fires_with_the_cross_year_gate_off`.

**Optimality guard (PERF-C S1).** An alien basis is a starting point, and HiGHS
is documented to repair one — but rule 36(e) is the record of a
basis-neutrality claim that did not survive measurement, so the seeded answer
is checked rather than trusted. If the seeded `h.run()` does not report
`Optimal` (or `DispatchModel.solve` raises, which it does on an infeasible
primal), a WARNING names the status, the basis is discarded, and the same LP is
re-solved **cold** through `solve_dispatch` — byte-for-byte the answer an
unseeded pass produces. The seed can therefore cost a wasted `h.run()`, never
an answer. Provenance rides the existing channel: `EnergySolveResult.p1_seeded`
reports the P1 that is *actually returned* (so it is `False` after a rollback),
and the sibling `p1_seed_fallback` carries the offending status; both appear on
the pass-timing log entry. A genuinely infeasible LP raises again on the cold
re-solve, so nothing is masked. Scope: only a pass that was actually seeded can
roll back — a declined apply or an unseeded route is untouched.

**Class.** WARM-START CLASS, not byte-identical — the memo's §4 standard, the
one every shipped warm start was promoted on: objective and total generation
identical, per-unit differences marginal-tie only (`total gen Δ = 0`), price
differences confined to dual-degenerate hours. It cannot be proved on
`regression_gate.py --mode byte` between a seeded and an unseeded bundle, and
must not be; the byte gate's job is to prove the switch is dead when OFF
(merge-base control vs branch under the pin — see §WALLCLOCK B). Keeper goldens
do not move (cold-vs-cold under the pin), and a keeper's committed bundle stays
the G-CTRL form-4 control (rule 29 `[R-SCREEN]` (b)).

**A latent crash fixed on the same branch.** The cold-P1 branch exported the
cross-year basis from `model` guarded on the gate but not on the model's
existence, and a reused-P0 pass (C-1b) has none — so under the calibration
CLI's default `MARKET_SIM_WARMSTART_XYEAR=1` every ERCOT adaptive pass 2 raised
`AttributeError: 'NoneType' object has no attribute 'export_cross_year_basis'`
(reproduced on the trivial LP at the merge base; the s3 measurements ran under
the `XYEAR=0` pin and never saw it). The export is now guarded on the model, and
`tests/unit/pipeline/test_xyear_warmstart_default.py` pins the case with the
seed off and on.

**Measured (this wave — the shipped surface, determinism pin except the two gate
env vars, one ERCOT arm at a time, 6 GiB swapfile):**

| ISO-year | `solve_p1` OFF → ON | P1 iterations OFF → ON | objective / total gen | prices | per-unit reshuffle |
|---|---|---|---|---|---|
| ERCOT 2025 (one-pass) | 349.2 → **142.0 s** (2.46×) | 273,893 → **78,856** | identical / Δ 0 MWh | max \|Δ\| 1.1e-12, 0 degenerate hours | 16 unit-hours, 0.0007 % |
| ERCOT 2024 (two-pass; pass 2 seeded from pass 1's P1) | 628.1 → **225.1 s** (295.3→132.2 + 332.9→92.8) | 252,042 / 250,291 → **83,748 / 69,667** | identical / Δ 0 | max \|Δ\| 3.7e-13, 0 | 4 unit-hours, 0.00001 % |
| NYISO 2023 | 96.4 → **67.6 s** | 268,305 → **108,037** | identical / Δ 0 | max \|Δ\| 2.2e-13, 0 | 7,290 unit-hours, 0.031 %, LMP identical on all |
| CAISO 2023 | 354.5 → **123.1 s** (2.88×) | 290,022 → **94,098** | identical / Δ 0 | CA zones bit-identical; 1,315 zone-hours differ on the zero-load import nodes WECC_PNW/DSW (dual degeneracy, up to 88 $/MWh, not scored) | 5,783 unit-hours, 0.041 %, LMP identical on all |

Byte gate with the seed OFF (merge-base control `34f3ce35` vs branch, determinism pin):
`regression_gate.py --mode byte` check [1] **PASS** — ERCOT 2024–2025 (7 files, 28 numeric
columns) and NEISO 2023 (5 files, 20 columns) at atol=rtol=0; zero reshuffle. Full record,
phase lines, peak RSS (+0.6 GB on ERCOT) and the CAISO reading: baseline doc §WALLCLOCK B.

Pinning tests: `tests/unit/pipeline/test_xyear_warmstart_default.py`
(`TestResolveP1BasisSeedDefault`, `TestP1BasisSeedGate`) — resolver precedence,
the seed applied inside the gate and neutral on the trivial LP, inert under the
pin, inert on the forecast gate argument, never reaching a warm P1, the
adaptive-pass leg (export → reuse), the regression pin for the crash above, and
the `getattr`-tolerant contract on a solve-only `DispatchModel` double.
