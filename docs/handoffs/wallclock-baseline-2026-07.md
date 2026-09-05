# Wallclock Efficiency Refactor — Baseline (2026-07-12)

Companion to `docs/handoffs/wallclock-efficiency-plan-2026-07.md` (P-0, Wave 1). This is the
pre-refactor per-phase timing anchor every later prompt (P-1…P-4) reports before/after against.
Captured with the phase-timing instrumentation merged in PR #2137
(`claude/wallclock-p0-instrumentation-2kts91`): one summary log line per year emitted by both
orchestrators — `data_prep / solve_p0 / markup / solve_p1 / results_write / total`.

## Capture conditions

- **Config:** default backcast path, **cold** (no cross-year warm-start —
  `MARKET_SIM_WARMSTART_XYEAR` unset, the current default). P0→P1 intra-year warm-start on (default).
- **Command:** `scripts/run_calibration_full.py --iso <ISO> --year 2023 2024 2025` to a throwaway
  `--out-dir`. **Not registered on the dashboard** (not calibration runs).
- **Host:** 4 vCPU, 16 GB RAM, HiGHS threads unset (auto), presolve off.
- **Solves per year:** exactly 2 (P0 base-cost + P1 bid-cost); all scarcity overlays post-solve NumPy.

## ERCOT — plant-level, 7 zones, 8760 h

| Year | data_prep | solve_p0 | markup | solve_p1 | results_write | **total** |
|------|-----------|----------|--------|----------|---------------|-----------|
| 2023 | 53.5s | 174.7s | 5.4s | 25.0s | 13.1s | **271.7s** |
| 2024 |  6.6s | 133.0s | 5.5s | 26.4s | 11.6s | **183.1s** |
| 2025 |  7.8s | 143.4s | 5.3s | 22.8s | 12.2s | **191.5s** |

- Solve share (P0+P1) ≈ **74–83 %** of year total; cold **P0 dominates** (≈133–175s).
- Year-2023 `data_prep` is inflated (53.5s vs ~7s) by the **one-time binned-fleet-cache rebuild**
  (`ercot_fleet_binned.parquet`); years 2–3 read the cache and drop to ~7s. Warm-cache steady state
  is ~183–192s/year.

## MISO — zonal (6 zones) + reserve co-optimization, 8760 h

| Year | data_prep | solve_p0 | markup | solve_p1 | results_write | **total** |
|------|-----------|----------|--------|----------|---------------|-----------|
| 2023 | 36.7s | 208.7s | 9.7s | 50.7s | 33.4s | **339.2s** |
| 2024 |  9.3s | 218.7s | 9.8s | 49.2s | 32.0s | **319.0s** |
| 2025 |  9.4s | 200.7s | 9.1s | 41.0s | 32.5s | **292.6s** |

- Reserve co-opt makes MISO's per-year total larger than ERCOT and heavier in **P1** (~41–51s vs
  ERCOT ~23–26s) and **results_write** (~32–33s vs ~12s).
- Same year-1 `data_prep` bump (36.7s → ~9s) from the fleet-cache rebuild.

## What this anchors (lever → phase it should move)

| Prompt | Lever | Target phase(s) |
|--------|-------|-----------------|
| **P-1** | data-layer caches (fleet CSV re-parse, `load_campd_bins`, double demand load, registry, iterrows) | `data_prep` (esp. the year-1 rebuild + per-plant CSV re-reads); some `markup`/write |
| **P-2** | cross-year warm-start default ON (backcast) | `solve_p0` on years ≥2 (benchmarked ~2.3× on warm years) |
| **P-3** | `--reuse-solved` opt-in | whole years skipped on reporting-only re-runs |
| **P-4** | HiGHS IPM+crossover / numpy setBasis / threads (bench-first) | cold `solve_p0` |

Negative results from P-4 experiments (any lever that fails the ≥10 % / identical-output adoption
rule) get recorded **in this file** so they are not re-run.

## Operational note — memory

Running **ERCOT (plant-level) and a reserve-co-opt ISO (MISO/PJM) concurrently OOMs** a 16 GB host:
MISO alone peaks ≈10.8 GB RSS, and the two peaks overlap. The first concurrent attempt here was
OOM-killed mid-2023; MISO was re-run **solo** to capture its table. Keep big co-opt ISOs to **one at
a time** alongside anything else on a 16 GB box (CLAUDE.md rule 12: cap ~2 simultaneous per-plant
multi-zone LPs, fewer when co-opt is involved).

## P-4 — HiGHS cold-first-solve experiments (bench-first)

Three bounded solver experiments on the cold P0 (the dominant phase above), run with
`scripts/archive/bench_cold_solve.py` on **real captured** ISO-year LPs (the pipeline
`solve_dispatch` seam, captured under `MARKET_SIM_WARMSTART=0`, then re-solved directly).
**Host:** 4 vCPU, 15 GB RAM, HiGHS presolve off (as in production). Captures:
**ERCOT 2023** (plant-level, 7 zones, n_gen 1458, 13.23 M LP columns, model peak ≈5.9 GB) and
**MISO 2024 + energy-reserve co-opt** (6 zones, n_gen 2821, market-wide RBDC + 8 ORDC steps,
2359 reserve-eligible units, model peak ≈11.5 GB).

**Adoption rule (per experiment):** adopt a default change only on **≥10 % cold-solve-wall
improvement AND identical objective/prices** (marginal-tie-only diffs); otherwise the result is
recorded here so it is not re-run. Feasibility tolerances were **never** touched.

### Summary verdicts

| # | Experiment | ERCOT | MISO (co-opt) | Verdict |
|---|-----------|-------|---------------|---------|
| 1 | IPM + crossover for cold P0 | P0 136 s → **>300 s cap, unconverged** | P0 234 s → **>400 s cap, unconverged** | **REJECT** — no default change |
| 2 | numpy/array `setBasis` in `apply_cross_year_basis` | array API unavailable; list build 10.6 s → **0.59 s** (memoized enum), byte-identical | (column-count driven; same hot path) | **No default change here** — records the negative array result + a byte-identical follow-on for P-2 |
| 3 | `MARKET_SIM_HIGHS_THREADS` {1, 4, unset} | P0 135/142/141 s, RSS flat | P0 234/239/233 s, RSS flat | **No default change** — no thread scaling; single-thread stays golden |
| 4 | HiGHS `parallel` {choose, on, off} (PAMI simplex) | P0 175.1/175.3/170.6 s; **RSS 5.83 → 7.13 GB on `on`** | see Exp 4 | **REJECT** — no default change; `on` costs RAM and buys no wall |

### Exp 1 — IPM (`solver=ipm`, `run_crossover=on`) for the cold P0 — REJECT

Set `solver=ipm` + `run_crossover=on` for the first (cold) P0 solve only, then revert to simplex
and hand the crossover basis to the existing P1 warm-start (`changeColsCost`). Crossover is
required (an interior point has no basis, and no vertex duals/prices to compare).

- **ERCOT 2023:** dual-simplex baseline P0 = **136.0 s** (188,794 simplex iterations), P1 warm =
  25.4 s. IPM+crossover P0 **did not converge within a 300 s cap** (`time_limit` reached, no basis
  returned); an earlier **uncapped** run exceeded **13 minutes** on the same solve before being
  terminated (≥5×). The bottleneck is the crossover push-to-vertex on a highly degenerate
  13.2 M-column dispatch LP.
- **MISO 2024 (co-opt, threads=1):** dual-simplex baseline P0 = **233.7 s** (237,934 simplex
  iterations), P1 warm = 72.7 s. IPM+crossover P0 **did not converge within a 400 s cap** (≈1.8×
  the baseline; `time_limit` reached, no basis). Same crossover pathology, and the co-opt reserve
  rows make the LP *more* degenerate, not less.

Dual simplex + P0→P1 basis reuse is already well-tuned for this LP family; IPM+crossover is far
slower and fails the ≥10 % test decisively (it is *slower*, not faster). **Not adopted; do not
re-run.** (Feasibility tolerances left at defaults throughout.)

### Exp 2 — `setBasis` materialization in `apply_cross_year_basis` — no default change; hand-off to P-2

**Array result (the experiment as posed): negative — not re-run.** `apply_cross_year_basis`
(cross-year warm-start, P-2) must hand HiGHS a `Sequence[HighsBasisStatus]`. **highspy 1.14.0
rejects raw int / numpy-array input** to `HighsBasis.col_status`
(`TypeError: incompatible function arguments … Sequence[HighsBasisStatus]`), so the numpy-array
`setBasis` path the plan hoped for **does not exist in the installed build** — the existing
list-comp fallback (`dispatch.py:4184-4185`) stands unchanged. Re-check only if highspy is upgraded.

**What the bench did surface (measured, byte-identical follow-on for P-2).** Measured on the ERCOT
capture (**13.23 M columns** — the plan's "~1.8 M" was stale), the *cost* of that mandatory
list-comp is large, and how it is built matters:

| col_status list build (13.23 M elems, best of 3) | time |
|---|---|
| (a) `HighsBasisStatus(int(s))` per element (current `dispatch.py`) | **10,639 ms** |
| (b) memoized enum LUT `[_LUT[s] for s in status]` (LUT = the 5 status objects by code) | **592 ms** |

94 % faster, **statuses byte-identical** (verified element-wise on 100 k samples + the full
`test_cross_year_warmstart.py` suite), so the resulting basis — and therefore the solve — is
unchanged. Full `apply_cross_year_basis` (both lists + `setBasis`) drops from ≈11.7 s to ≈1 s per
warm-year apply.

**Not adopted in this (P-4) session — by the letter of the adoption rule.** The gate scores the
**cold-solve wall**; this is cross-year warm-start *setup*, which is inert on the default path
(`MARKET_SIM_WARMSTART_XYEAR` unset) and only becomes live once **P-2** flips xyear default-on for
the backcast. So P-4 changes no defaults, and the optimization is handed to P-2 as a ready,
byte-identical two-line change to fold in with the flag flip (verify with
`scripts/diagnostics/diff_warmstart_bundles.py` alongside P-2's existing diff-gate):

```python
# module level, near _BASIS_LOWER/_BASIS_BASIC (dispatch.py:3205):
_BASIS_STATUS_OBJS = [highspy.HighsBasisStatus(i) for i in range(5)]  # by-code cache
# in apply_cross_year_basis (dispatch.py:4184-4185), replace the two per-element list-comps:
basis.col_status = [_BASIS_STATUS_OBJS[s] for s in col_status]
basis.row_status = [_BASIS_STATUS_OBJS[s] for s in row_status]
```

When a future highspy accepts array input, that array path can replace the list-comp with no
behavior change.

### Exp 3 — HiGHS threads {1, 4, unset} — no default change; per-ISO note

Cold-P0 wall and peak RSS per `MARKET_SIM_HIGHS_THREADS` setting (isolated subprocess each, so
peak RSS is clean). Objective identity across settings is checked (a thread count must not change
the optimum beyond marginal ties).

**ERCOT 2023 (plant-level, n_gen 1458, 7 zones):**

| threads | build | P0 cold | peak RSS | obj |
|---|---|---|---|---|
| unset (auto) | 1.83 s | 135.2 s | 5.72 GB | 2.17138325e+09 |
| 1 | 1.82 s | 141.9 s | 5.72 GB | 2.17138325e+09 |
| 4 | 1.86 s | 140.6 s | 5.72 GB | 2.17138325e+09 |

Objective **bit-identical** (max rel Δ = 0.00e+00); P0 wall within **±5 %** (auto marginally
fastest); peak RSS unchanged.

**MISO 2024 (co-opt, n_gen 2821, 6 zones):**

| threads | build | P0 cold | peak RSS | obj |
|---|---|---|---|---|
| unset (auto) | 5.40 s | 233.8 s | 13.17 GB | 6.77162818e+09 |
| 1 | 5.24 s | 238.8 s | 13.17 GB | 6.77162818e+09 |
| 4 | 5.28 s | 233.4 s | 13.17 GB | 6.77162818e+09 |

Objective **bit-identical across all three** (max rel Δ = 0.00e+00); P0 wall spread **~2 %**;
peak RSS unchanged. HiGHS's dual simplex on this LP is effectively serial — 4 threads neither
speed it up nor cost extra RAM (no parallel factorization is triggered), so there is no wall to
buy and no memory penalty to fear here.

**Recommendation (per-ISO):** **leave `MARKET_SIM_HIGHS_THREADS` unset for all ISOs.** On both
ERCOT and MISO the cold-P0 dual simplex shows no useful thread scaling (wall spread ≤5 %, and
`unset`/auto is at least as fast as any pinned count), so a thread
default would trade the single-thread marginal-tie determinism for nothing. Single-thread stays
the **golden/repro pin** — the golden capture (`scripts/capture_keeper_goldens.py`) and any
reproducibility baseline keep threads at 1. (The env knob remains available for a future
large-ISO LP that *does* parallelize, but no current capture justifies flipping it.)

### Exp 4 — HiGHS `parallel` {choose, on, off} (PAMI parallel simplex) — REJECT

The one un-run HiGHS bench from the refactor-consolidation plan (§7-H4). **This is not Exp 3
re-run.** `threads` (Exp 3) bounds how many threads HiGHS *may* use; `parallel` selects whether the
**parallel simplex variant is engaged at all** (`simplex_strategy` dual-tasks / dual-multi "PAMI").
A thread count with no parallel algorithm engaged cannot show scaling — which is precisely what
Exp 3 measured — so this is a genuinely different lever and gets its own numbered slot.

Run with `scripts/diagnostics/bench_highs_parallel.py` on the same archived-capture seam Exp 1–3
used (`scripts/archive/bench_cold_solve.py capture`), one **isolated subprocess per arm** so peak
RSS is clean, threads left **unset** (the production default, so the parallel path is not starved
of threads). Baseline is `choose` — the production default, since the model builder
(`src/market_sim/model/lp/model.py`) sets only `threads` and `presolve`, never `parallel`.
`off` is included to show whether `choose` was already picking a parallel path.

**ERCOT 2023 (plant-level, n_gen 1458, 7 zones, 13.23 M columns):**

| `parallel` | resolved | `simplex_strategy` | build | P0 cold | P0 simplex it | P1 warm | peak RSS | objective |
|---|---|---|---|---|---|---|---|---|
| `choose` (default) | choose | 1 | 4.78 s | **175.14 s** | 191,986 | 50.33 s | **5.83 GB** | 2.08683147e+09 |
| `on` | on | 1 | 2.76 s | **175.31 s** | 194,115 | 55.85 s | **7.13 GB** | 2.08683147e+09 |
| `off` | off | 1 | 3.55 s | 170.56 s | 191,986 | 34.43 s | 5.83 GB | 2.08683147e+09 |

**Verdict: REJECT — no default change.** Three things, in order of what they settle:

1. **PAMI never engages.** With `parallel=on` accepted by HiGHS (the option reads back as `on`),
   `simplex_strategy` stays at **1** — plain dual simplex. The iteration count barely moves
   (191,986 → 194,115), which is what a *serial* dual simplex on a marginally different path looks
   like, not a parallel one. On this LP family HiGHS declines the parallel variant even when asked.
2. **No wall to buy.** P0 cold is **−0.1 %** vs the default (175.14 → 175.31 s) — inside noise, and
   nowhere near the ≥10 % adoption bar. `off` is 2.6 % *faster* than `choose`, also noise-level.
3. **It costs RAM.** `on` raises peak RSS **5.83 → 7.13 GB (+22 %)** for that zero wall gain. On a
   16 GB host this is the opposite of free: rule 12 already caps concurrency on memory, so a
   default that inflates the per-solve peak by a fifth would tighten the concurrency budget while
   buying nothing.

Outputs are unaffected either way — objective agrees to **3.43e-16 relative** and the full price
vector to **1.42e-14 $/MWh** (`off` is bit-identical to `choose`, 0.00e+00 on both). So this is a
clean negative on cost, not a correctness question. Feasibility tolerances were **never** touched.

**Recommendation: leave `parallel` unset (HiGHS `choose`) for all ISOs, and do not re-run this
bench.** It is recorded here precisely so the "we never tried PAMI" thread is closed.

## H2 — Persisted year-1 basis cache (refactor-consolidation plan §7)

The recurring cold P0 the P-4 experiments could not move is the **first year of every
calibrate-iterate run**: cross-year warm-start already makes years ≥2 warm, but year-1 has no
prior-year basis in-process, so it always solves cold. H2 persists each solved year's exported
optimal basis to a disposable NPZ (`results/basis-cache/<ISO>_<year>_T<hours>.npz`, gitignored;
int8 status vectors + `unit_ids` + a layout fingerprint, never pickle — compat clause 4) and, at
the top of a fresh year with no in-run basis, seeds `xyear_cache` from it so the P0 warm-starts.

Wired in `pipeline/solve.py::run_energy_solve` (the shared P0/P1 core both calibration CLIs reach;
the key is `config.iso/weather_year/hours`, which `backcast_config` pins to the solved ISO-year-T).
Gated by `basis_cache_enabled()` (= the cross-year gate): default ON for the calibration CLIs,
**hard-OFF under the goldens/replay determinism env** (`MARKET_SIM_WARMSTART_XYEAR=0`), where seed
and persist return before touching the LP so the solve is byte-identical.

**Timing — year-1 cold vs warm-from-persisted-basis** (host: 4 vCPU / 15 GB, `HIGHS_THREADS=1`,
`MALLOC_ARENA_MAX=2`; throwaway `--out-dir`, not dashboard-registered). Each ISO run twice for
2023: a first run with an empty cache (cold year-1 P0, persists the basis), then a second run that
seeds year-1 from that basis:

| ISO | year | P0 cold | P0 warm (seeded) | **P0×** | total cold | total warm |
|-----|-----:|--------:|-----------------:|--------:|-----------:|-----------:|
| ERCOT (plant-level, 7 zones) | 2023 | 211.5 s | **38.0 s** | **5.6×** | 339.7 s | 174.7 s |
| MISO (zonal + reserve co-opt) | 2023 | 352.8 s | **92.9 s** | **3.8×** | 571.0 s | 334.1 s |

The persisted basis is a same-ISO-year, near-identical LP, so year-1 P0 converges in far fewer
iterations than a cold start — a bigger win than the ~2.3× the adjacent-year cross-year warm-start
buys on years ≥2. A stale basis (config changed by a tuned knob) still applies: `apply_cross_year_
basis` remaps/repairs and falls back cold, so it costs iterations, never correctness.

**Neutrality (cold vs warm-from-persisted, per year — `scripts/diagnostics/diff_warmstart_bundles` +
`system.parquet`).** Same standard the shipped cross-year warm-start was promoted under
(`docs/cross-year-warmstart.md`): objective and total generation bit-identical; price and per-unit
dispatch differences confined to marginal ties (primal) and their dual analogue (degeneracy).

| ISO | objective / total gen | max \|Δ zonal price\| | dual-degenerate hours | per-unit dispatch reshuffle |
|-----|-----------------------|-----------------------|-----------------------|-----------------------------|
| ERCOT 2023 | total gen Δ = **0.000000 TWh** (446.1579 both); mean price identical | 6.77e-2 $/MWh | 30 / 61,320 (0.05 %) | ≤ 1,022 MWh/unit, `total gen Δ = 0` |
| MISO 2023 | total gen Δ = **-6.4e-5 TWh** on 641.71 TWh (~1e-7, display rounding); mean price identical | **1.4e-14 $/MWh** | 0 | ≤ 52 MWh/unit |

MISO 2023 prices are bit-identical (1.4e-14, floating-point noise). ERCOT 2023 shows the same dual
degeneracy the shipped feature accepted at promotion (MISO-2025 there: 0.1495 $/MWh over 182
zone-hours) — here **smaller** (0.068 $/MWh over 30 hours) and via the same channel: year-1's warm
P0 lands on a different-but-equally-optimal degenerate vertex, feeding `compute_monthly_markup` a
marginally different run pattern; the primal (served load, total gen, objective) is untouched. This
is the neutrality class the calibration path already lives in, negligible for scoring.

Byte-identity under the determinism env is additionally confirmed empirically: an ERCOT 2023 solve
with the feature **OFF** (`MARKET_SIM_WARMSTART_XYEAR=0`) reproduces the empty-cache cold run,
i.e. the seed/persist machinery does not perturb the solve. (The full keeper goldens gate is not
re-run because the change is provably inert under that env — the gate's own pin — and the unit
suite pins the gate behavior.)

## H3 / Exp 5 — Forecast-path cross-year warm-start, default flipped ON (owner decision D-9)

The third wall-clock lever in plan §7-H: the forecast solves 25 sequential years and every one of
them was cold, because `runner.py` passed `xyear_cache=None`. The blocker was never the LP — it was
that the marginal-tie reshuffle a warm start produces used to be read by the economic retirement
screen through per-unit **realized** dispatch, so a pure wall-clock lever could tip a retire/keep
decision and change the *next* year's fleet (`docs/cross-year-warmstart.md` "Why the forecast path
is not wired", where the original 168 h A/B diverged at 2028: objective 8.3e-4, 0.19 $/MWh).

Wave 4C closed that reader (attainable pro-forma margin + attribute revenue on attainable in-merit
generation). D-9 authorized the flip **conditional on a full-horizon A/B showing the capacity
trajectory unchanged**. This is that A/B.

**Wiring.** `ScenarioConfig.forecast_xyear_warmstart` (registry field, rule 24 [R-REGISTRY] — not
an env knob) gates `runner.py`'s year-loop basis holder, and is passed to `run_energy_solve` as an
explicit `xyear_warmstart` override so the calibration CLIs' default-ON `MARKET_SIM_WARMSTART_XYEAR`
can never reach the forecast trajectory. An explicitly-gated caller also bypasses the H2 persisted
year-1 NPZ cache: that cache is keyed `(iso, weather_year, hours)` with no sim-year, so seeding a
25-year horizon from it would make a run depend on whatever solved before it. The backcast passes
no override (gate `None`) and is unchanged.

**Capture conditions.** ERCOT 2026-2050, 8760 h, per-plant CAMPD bins (every ScenarioConfig field
at its default except mode/iso/horizon), `MARKET_SIM_HIGHS_THREADS=1 MALLOC_ARENA_MAX=2
OMP_NUM_THREADS=1`. Single-thread is mandatory here, not a preference: multi-threaded dual simplex
breaks marginal ties nondeterministically, so at the default thread setting even a cold-vs-cold
control drifts and the comparison would measure the solver rather than the warm start. Two arms as
two concurrent invocations, each `--out-dir` isolated and each a distinct `cache_key`, years
sequential within each (rule 12). Driver: `scripts/probes/_d9_forecast_warmstart_ab.py`.

### Wall clock — per year (s)

| year | cold | warm | × | | year | cold | warm | × |
|-----:|-----:|-----:|--:|-|-----:|-----:|-----:|--:|
| 2026 | 171.3 | 190.3 | 0.90× | | 2039 | 114.7 | 50.6 | 2.27× |
| 2027 | 150.7 | 79.9 | 1.89× | | 2040 | 118.9 | 53.4 | 2.23× |
| 2028 | 152.9 | 81.3 | 1.88× | | 2041 | 117.2 | 50.0 | 2.34× |
| 2029 | 152.5 | 75.2 | 2.03× | | 2042 | 107.0 | 44.7 | 2.39× |
| 2030 | 135.9 | 69.1 | 1.97× | | 2043 | 106.8 | 41.7 | 2.56× |
| 2031 | 136.4 | 74.5 | 1.83× | | 2044 | 101.3 | 40.7 | 2.49× |
| 2032 | 131.0 | 59.8 | 2.19× | | 2045 | 107.7 | 41.2 | 2.61× |
| 2033 | 140.9 | 64.7 | 2.18× | | 2046 | 102.5 | 39.7 | 2.58× |
| 2034 | 129.5 | 61.1 | 2.12× | | 2047 | 100.9 | 38.4 | 2.63× |
| 2035 | 130.2 | 64.0 | 2.03× | | 2048 |  95.9 | 37.8 | 2.54× |
| 2036 | 135.3 | 60.2 | 2.25× | | 2049 |  96.2 | 37.1 | 2.59× |
| 2037 | 119.6 | 60.0 | 1.99× | | 2050 |  96.3 | 36.8 | 2.62× |
| 2038 | 114.6 | 54.0 | 2.12× | |      |       |      |       |

- **Total: 3,066.3 s (51.1 min) cold → 1,506.3 s (25.1 min) warm = 2.04×.**
- **Years 2027-2050** (the warm-startable ones): 2,894.9 s → 1,315.9 s = **2.20×**.
- **2026 is cold in BOTH arms** (nothing carries a basis into the first solve of a process) — the
  0.90× is noise from the two arms contending, not a warm-start cost.
- Speedup **grows down the horizon** (1.9× early → 2.6× by 2050) because the fleet's year-over-year
  churn shrinks as the build-out settles, so the remapped basis is a progressively better guess.
- Peak RSS 3.76 GB cold → 4.02 GB warm (**+7 %**, one retained `CrossYearBasis`) — the same order as
  the +4 % the backcast flip paid.

**Contention caveat (read before quoting the 2.04×).** The arms were launched together, but the
warm arm finished in 25.1 min and the cold arm ran on to 51.1, so cold years **2037-2050 ran
uncontended** on a free box while every warm year ran contended. That biases the cold total
*downward*, i.e. **2.04× is conservative**. Restricting to 2027-2036, where both arms were
genuinely running side by side: cold 1,395.3 s vs warm 689.8 s = **2.02×** — statistically the same
number, so contention is not what produces the result.

### D-9 guardrail — capacity trajectory

**PASS. The capacity trajectory is bit-identical in all 25 years.** Max relative delta, warm vs
cold, over the whole horizon:

| quantity | max relative Δ |
|---|---|
| `total_cap_mw`, `thermal_mw`, `firm_clean_mw`, `vre_mw`, `storage_mw` | **0.000e+00** |
| `builds_thermal_mw`, `builds_renew_mw`, `builds_storage_mw`, `retire_mw` | **0.000e+00** |
| per-fuel `capacity_by_fuel_mw` (every fuel, every year) | **0.000e+00** |
| `peak_demand_mw`, `reserve_margin`, `max_hourly_price` | **0.000e+00** |
| `annual lw_price` | 2.5e-05 (2031) |
| `co2_mt` | 6.6e-06 (2028) |

I1-I14 invariant **statuses are identical** in both arms (3 FAIL / 1 WARN, same ids, same years);
the detail strings differ only where they embed a price or CO2 figure that moves in its last digit.

The two residuals are the marginal-tie / dual-degeneracy channel, not a capacity decision. Worth
stating precisely, because wave 4C did **not** make the screen strictly basis-invariant: it removed
the realized-*dispatch* reader, but the screen still reads **prices**, and prices are LP duals — a
warm start can land on a different optimal *dual* vertex under degeneracy (H2 above measured exactly
that on ERCOT 2023: max |Δ zonal price| 6.8e-2 over 30/61,320 hours). So the guardrail was a real
test, not a formality. What it establishes is that at ERCOT full-horizon scale that dual noise is
~1e-5 and lands nowhere near a retire/keep threshold: no unit changes state in any year.

For scale, both residuals are **three orders of magnitude inside** every band the forecast golden
is checked against (`scripts/golden_forecast_bands.py`: CO2 2 %, load-weighted price 5 %, system
cost 2 %, end-year capacity 1,000 MW absolute), so the flip cannot move
`tests/golden/ercot_2026_2040.json` off its bands. Nothing was regenerated.

### Reduced-horizon pre-screen (the experiment that originally refuted the wiring)

ERCOT 2026-2032 at **168 h**, the exact setup of the `docs/cross-year-warmstart.md` table where the
2028 fleet diverged, re-run against the post-4C screen: **capacity trajectory identical, and no
price / CO2 / reserve-margin delta at all** (cold 38.9 s → warm 34.1 s, 1.14×). The mechanism is
confirmed live rather than silently inert — spying `DispatchModel.apply_cross_year_basis` on a
4-year warm run gives `attempts=3 installed=3` versus `attempts=0` cold.

### Default-off byte-identity (pre-flip)

Before the flip, the branch at its default was checked against main (`b054dfe`) by running main's
`src/market_sim` from a shadow tree extracted with `git archive` — the package `__path__` is bound
before anything manipulates `sys.path`, so every `market_sim.*` submodule resolves from the shadow.
ERCOT 2026-2032 forecast: `full_horizon_summary` **trajectory and invariants byte-equal**. (Incidental
finding for anyone repeating this: `ScenarioConfig` carries absolute paths, so `cache_key` is
location-dependent and the shadow's keys legitimately differ from the working tree's.)

**Verdict: FLIP.** `ScenarioConfig.forecast_xyear_warmstart` default `False → True` (2026-07-26).
The pinned default `cache_key` is unmoved at `edbc1b103207170a` across the flip — the field drops
out of the hash at whatever its default is — and a run that opts out (`False`) enters the key as a
distinct scenario, which is the escape hatch for a strictly cold forecast. Cache epoch (compat
clause 2): forecast years cached before the flip were solved cold under this same key and stay
valid, because the A/B measured the trajectory bit-identical.

## H3b — D-9 multi-ISO follow-through: the same A/B on the five capacity-market ISOs

The flip above is default-ON for **every** ISO, but its evidence was ERCOT-only, and ERCOT is the
one ISO that exercises none of the paths the gap is about. ERCOT is energy-only — no capacity
market, so no CR-1 sloped demand curve and no locational-deliverability leg — and PJM/MISO add
reserve co-optimization on top, i.e. more duals and therefore more degeneracy surface. That matters
because the residual channel D-9 leaves open is explicitly the **dual** one: wave 4C removed the
realized-dispatch reader, but `runner.py` still hands the retirement screen `price_signal =
econ_prices`, and prices are LP duals that can land on a different optimal vertex under degeneracy.
ERCOT showed that noise at ~1e-5 tipping nothing; that is not evidence for a co-opt ISO. This
section runs the same A/B per ISO and records each verdict either way.

**Capture conditions.** Identical to §H3 — 2026-2050, 8760 h, every `ScenarioConfig` field at its
default except mode/iso/horizon, `MARKET_SIM_HIGHS_THREADS=1 MALLOC_ARENA_MAX=2 OMP_NUM_THREADS=1`,
years sequential inside each invocation (rule 12). Two deliberate differences from the ERCOT run:

* **Both arms carry the §2.1a golden posture** (`--golden-posture`, per-ISO capacity-market
  clearing ON — resolved True for all five, and inert for ERCOT). Running these ISOs at `cmc=False`
  would have left the sloped-curve path — the whole reason to extend the A/B — unexercised. The
  posture is the same in both arms, so the comparison still isolates the warm start.
* **PJM and MISO run their two arms sequentially, not side by side.** Two full-scale co-opt LPs at
  once is the pairing the memory note below records an OOM from, and this box has 15 GB against a
  measured ~4-6 GB per arm. The cost is wall-clock; the benefit is that their speedups carry no
  contention caveat at all.

**The mechanism is live in every ISO, not silently inert.** An identical trajectory proves nothing
if the warm arm never installed a basis, so `scripts/probes/_d9_warmstart_spy.py` counts
`DispatchModel.apply_cross_year_basis` per arm. All five ISOs report `attempts=3 installed=3` warm
against `attempts=0` cold on a 4-year run — the check the ERCOT record made by hand.

### Reduced-horizon pre-screen (168 h, 2026-2032, all five)

| ISO | capacity trajectory | price / CO2 / reserve-margin delta | cold → warm |
|---|---|---|---|
| CAISO | identical | none | 34.5 s → 34.6 s (1.00×) |
| PJM   | identical | none | 34.7 s → 34.2 s (1.02×) |
| NYISO | identical | none | 32.3 s → 31.4 s (1.03×) |
| MISO  | identical | none | 32.8 s → 33.4 s (0.98×) |
| NEISO | identical | none | 29.8 s → 29.6 s (1.01×) |

No ISO moves at 168 h, so all five went on to the full horizon (a mover would have gone straight to
identification instead). The ~1.0× is expected and is not a finding: at 168 h the LP is small enough
that the basis remap costs about what it saves — ERCOT's own 168 h pre-screen was 1.14×.

### Full horizon (2026-2050, 8760 h)

| ISO | verdict | capacity trajectory | largest non-capacity residual | wall cold → warm | concurrent-window × | peak RSS |
|---|---|---|---|---|---|---|
| NEISO | **FLIP-CLEAR** | identical, all 25 years | `lw_price` 1.5e-05 (2035) | 2,473.3 s → 1,350.6 s (**1.83×**) | 1.72× (2026-2043) | 4.02 → 4.20 GB |
| NYISO | **FLIP-CLEAR** | identical, all 25 years | none — every quantity 0.000e+00 | 2,083.8 s → 1,110.5 s (**1.88×**) | 1.54× (2026-2036) | 3.24 → 4.23 GB |
| CAISO | **no verdict** — cold arm stopped at 22/25 years (below) | — | — | warm arm 7,346.6 s (122.4 min), 25 years | — | warm 8.71 GB |
| PJM | **not run** (below) | — | — | — | — | — |
| MISO | **not run** (below) | — | — | — | — | — |

For the two ISOs that completed, every quantity in the guardrail set — `total_cap_mw`,
`thermal_mw`, `firm_clean_mw`, `vre_mw`, `storage_mw`, `builds_thermal_mw`, `builds_renew_mw`,
`builds_storage_mw`, `retire_mw`, per-fuel `capacity_by_fuel_mw`, plus `peak_demand_mw`,
`reserve_margin` and `max_hourly_price` — is **0.000e+00** in all 25 years. I1-I14 invariant
statuses are identical between the arms in both ISOs (NEISO 3 FAIL / 2 WARN, NYISO 2 FAIL / 3 WARN,
same ids, same years); the detail strings differ only where they embed a figure that moves in its
last digit, and on I1, whose text carries the LP feasibility residual (NEISO 8.6e-10 cold vs
4.7e-10 warm, against a tolerance of 1.0).

Note what those FAIL counts mean for the reading: these ISOs' forecasts do **not** pass their own
invariants. That does not invalidate the guardrail — it is a *neutrality* test, and a
wrong-but-identical trajectory answers it exactly as well as a right one; the invariants failing
**identically in both arms** is itself part of the evidence. But nothing here should be read as
saying these ISOs' forecasts are good.

NYISO is the stronger of the two: identical on `lw_price` and `co2_mt` as well, i.e. not even the
dual-noise residual ERCOT and NEISO show. NEISO's 1.5e-05 on the annual load-weighted price is the
same marginal-tie / dual-degeneracy channel §H3 describes, three orders of magnitude inside the 5 %
load-weighted-price band `scripts/golden_forecast_bands.py` checks the forecast golden against.

**On the two wall-clock columns.** The arms are launched together but do not finish together — the
warm arm ends first and the cold arm's remaining years then run on a free box, which biases the cold
total *downward* and makes the headline speedup conservative. The concurrent-window column restricts
the comparison to the leading years during which both arms were genuinely competing
(`scripts/probes/_d9_relative_deltas.py`). For NEISO the two numbers are close (1.83× vs 1.72×), so
contention is not what produces the result; NYISO's window is shorter and its restricted number
correspondingly softer (1.54×), which is a property of where the arms happened to cross, not of the
warm start.

**Operational note (memory).** CAISO's warm arm peaked at **8.71 GB** — roughly double NEISO/NYISO,
and enough that two CAISO arms side by side would not fit the 15 GB box. Anyone repeating this for
PJM or MISO should assume the same and run the arms sequentially; the "Operational note — memory"
section's OOM warning applies to same-ISO arm pairs, not just to two different co-opt ISOs.

### Stopped at three ISOs — owner call, 2026-07-27

**CAISO's cold arm was stopped at 22/25 years and PJM/MISO were never launched** (owner:
"3 ISOs is enough evidence for now"). The default is **unchanged** —
`ScenarioConfig.forecast_xyear_warmstart` stays `True`, `cache_key` unmoved at
`edbc1b103207170a`. The evidence base for it is now **three ISOs at full horizon**
(ERCOT §H3, NEISO, NYISO) plus **all six at the 168 h pre-screen**, rather than the five-of-five
this session set out to produce.

Recorded so it is not re-run, and because the methodological objection behind the stop is correct
and should govern any resumption:

* **Horizon length is the wrong lever for this question.** An LP's optimum is basis-independent by
  construction, so warm start cannot change the objective. Its only route into the forecast is
  degenerate alternate optima → the screen reads a dual that differs → a discrete retire/keep flips
  → the next year's fleet differs. Whether that fires is a property of how close a unit sits to its
  threshold relative to the dual noise — **not** of how many years are solved. A 25-year run buys
  more draws at the lottery, bounds nothing, and says nothing about year 26. Two full-horizon ISOs
  and their own 168 h pre-screens agreed exactly, which is the expected result if the horizon is
  not the informative variable.
* **The measurement that would actually bound it** — not run, and the natural resumption point —
  is a margin analysis rather than another solve: (1) the dual noise warm start injects (already
  known: ~1e-5 relative on annual load-weighted price; H2 measured 6.8e-2 $/MWh on 30 of 61,320
  zone-hours at the hourly level), against (2) the distribution of each unit's distance to its
  retire/keep threshold in $/MW-yr, read out of years already solved. If the nearest unit sits
  orders of magnitude outside the noise band, the verdict holds at any horizon; if any unit sits
  inside it, that is the finding, and it would surface in year 2 as readily as year 24. (2) is the
  half nobody has measured, on ERCOT either.
* Probe arms live in the gitignored `results/d9-ab/`; the CAISO partial (22 cold years, 25 warm) is
  there but carries no verdict and must not be quoted as one.

## H4 — `results_write` sub-instrumentation (refactor-consolidation plan §7-H4)

`results_write` was a single merged window in both orchestrators, so the tables above could say
the phase costs ~12 s on ERCOT and ~32 s on MISO but **not what it is spending that on** — which
is the precondition the plan sets for the parquet-compression lever ("only if parquet dominates").
It is now split, in one shared helper (`src/market_sim/pipeline/timing.py`, which both
orchestrators finally call — it had shipped with zero consumers):

| Orchestrator | Components reported |
|---|---|
| backcast (`run_calibration_full.solve_and_persist`) | `state` (p2_state pickle + per-pass min-gen floor arrays) · `frames` (per-pass dispatch/system/storage/posture/flows/BTM construction) · `parquet` (the per-pass dispatch parquet writes) · `bench` (CAMPD hourly + EIA-923/930 benchmark-scoring frames) |
| forecast (`runner.run_scenario_iso`) | `legacy_p2` (the archived P2 screen, inert by default) · `parquet` (`save_result`) |

The components are measured on **disjoint, exhaustive** segments of the window, so they sum to
`results_write` exactly. **The parsed format is unchanged**: `data_prep / solve_p0 / markup /
solve_p1 / results_write / total` keep their exact spelling, order and position, and the breakdown
is appended as a trailing `(results_write: …)` clause, so every capture parsed against the tables
above still parses. `tests/test_pipeline_timing.py` pins that the no-breakdown line is
byte-identical to the recorded lines here.

### Measured — ERCOT keeper replay (`2026-07-23-ercot100-netrev-margin-keeper`, 8760 h, threads=1)

Captured by `scripts/capture_keeper_goldens.py` under the determinism pin, so this is the real
production write path, not a microbench:

| Year | `results_write` | `state` | `frames` | `parquet` | `bench` | year `total` |
|------|----------------:|--------:|---------:|----------:|--------:|-------------:|
| 2023 | 16.8 s | 0.8 s | **10.8 s** | 3.4 s | 1.7 s | 615.8 s |
| 2024 | 16.1 s | 0.7 s | **10.3 s** | 3.3 s | 1.8 s | 622.8 s |
| 2025 | 15.8 s | 0.6 s | **10.3 s** | 3.4 s | 1.6 s | 704.3 s |

**Parquet does not dominate — frame construction does.** The parquet write is **~21 %** of
`results_write` and **~0.5 %** of the year; building the per-pass dispatch/system/storage/posture/
flows/BTM frames is **~65 %** of it. `results_write` as a whole is **~2.5 %** of a year
(solve is ~85 % on this keeper), so the phase is a minor lever however it is split.

### Parquet-compression pre-check — the gates do NOT hash bundle bytes (finding, nothing adopted)

The plan gates a compression change (lz4 / dictionary-off) on "bytes change ⇒ check golden hashing
first". Checked, and the answer is **no gate is byte-sensitive** — every bundle-adjacent hash in the
tree hashes the **decoded frame**, never the file:

- `scripts/capture_keeper_goldens.py::_content_hash` reads the parquet with `pd.read_parquet` and
  hashes sorted-column float64 bytes plus the shape. Its own docstring gives the reason: a raw-file
  hash "picks up parquet's embedded creation metadata" and is not reproducible.
  `manifest.json` records this as `hash_scheme: sha256-of-canonical-column-float64-bytes`.
- `scripts/regression_gate.py --mode byte` delegates to `regression_check.compare_parquet`, which
  `pd.read_parquet`s both sides and compares **numeric columns** at `atol=rtol=0`.
- `scripts/lib/bundle_io.py::content_hash` (the shared-input store's dedupe key) hashes
  `pd.util.hash_pandas_object` + column names and documents itself as "independent of parquet
  encoding/metadata".

So a codec swap would be hash-transparent — it is *not* blocked by the gates.

**It was not adopted, and on the measured split it is not worth pursuing.** The plan makes the
compression bench conditional on parquet dominating `results_write`; it does not. At ~3.4 s of a
~620 s year, a codec change could not buy more than **~0.5 % of wall** even if it made the write
free — well under the ≥10 % adoption bar every other experiment here is scored against, and
`frames` (10.3–10.8 s) is the larger target if this phase is ever worth attacking. The codec stays
at the pandas/pyarrow default; no bench was run, because the pre-check that gates it came back
negative.

## PERF-B — applied wins, measured (2026-08-17)

Execution record for `docs/handoffs/perf-recheck-2026-08.md`'s five changes (its own §4
completion note carries the full session narrative). Conditions: determinism pin
(`MARKET_SIM_HIGHS_THREADS=1`, `WARMSTART=1`, `WARMSTART_XYEAR=0`), 4 vCPU / 15 GB
container, `uv.lock` env (pandas 3.0.3 / pyarrow 24.0.0), keeper-recipe replays via
`scripts/capture_keeper_goldens.py`. **Host-noise caveat governing every wall number
here:** identical-recipe cross-run solve walls on this shared container vary up to
±35 % (measured: the same ERCOT-2025 P0 solved in 574.5 s and 363.6 s in back-to-back
byte-identical arms), so *phase-structure* deltas are the reliable signal; solve-wall
deltas between sessions are not.

| Change | Where landed | Measured effect (keeper replays) |
|---|---|---|
| (a) `results_write` frames as `Categorical.from_codes` | on main via the 2026-08-16 rewrite graft (707db3ef) | `frames` 10.3–10.8 s (H4 July keeper replay) → **2.1–3.7 s/yr** on ERCOT; MISO frames → 2.6–4.1 s. `results_write` 15.8–16.8 → 8.1–12.6 s (ERCOT). MISO/PJM `results_write` is now **`bench`-dominated** (20.9–34.7 s of CAMPD/EIA-923 benchmark frames) — the next lever if the phase is ever attacked again. |
| (b) basis-status LUT in `apply_cross_year_basis` | on main via the same graft (707db3ef) | inert under the determinism pin by construction; PERF-A's bench (13,363 → 899 ms per warm apply) stands — no re-measurement possible in a pinned session. |
| (c) ci.yml fast-tests sparse block + timeout 20 | on main via acf784ec | fast tier green in production CI: 9m19s–10m36s observed job walls; the first-ever complete fast-tier runs in repo history. |
| (d) memoize `zone_assignment.build_zone_lookup` | PERF-B commit dcae1559 | byte-identical on a 5-ISO gate (ERCOT/NYISO/NEISO full-8760, MISO/PJM 4368 h). `data_prep` deltas: ERCOT y1 98.4 → 90.3 s (−8 %); NEISO warm years −8/−10 %; NYISO warm years −12/−23 %; MISO/PJM inside noise. **PERF-A §2.4 corrected:** `_load_cod_map` and the eGRID boundary repair were *already* `lru_cache`d when profiled — their cum-time was cache-miss work under two EIA-860 vintage keys — so the zone lookup was the only real memoization target and the ~40–55 s projection does not exist. |
| (e) basis export gated on its consumer (`_xwarm`) | PERF-B commit b6ae8216 | byte-identical (ERCOT full-8760 gate). `markup` window 81.3/74.8/64.4 → **51.6/50.7/46.5 s** (−18 to −30 s/yr, ~25–37 % of the window) on every goldens capture / keeper replay / repro baseline. Exceeds PERF-A's 10–16 s estimate because the ercot213 keeper's LP outgrew the recipe PERF-A profiled. |

**HEAD-era keeper-replay anchor** (@ `6cc332e7`, 2026-08-17 keepers ercot213-arm-pubanchor /
nyiso-140-layup-exclusion / neiso-97-dstrepair, determinism pin — these are *keeper-recipe*
walls, not the plain-CLI recipe the 2026-07 tables above anchor):

| ISO-year | data_prep | solve_p0 | markup | solve_p1 | results_write | total |
|---|---|---|---|---|---|---|
| ERCOT 2023/24/25 (post-(d),(e)) | 108.4/43.5/35.7 | 473.0/416.7/416.1 | 51.6/50.7/46.5 | 447.1/321.8/344.8 | 12.6/12.8/14.8 | **1092.6/845.5/857.9** |
| NYISO 2023/24/25 (post-(d), paired) | 74.7/8.4/5.3 | 180.1/149.5/97.7 | 26.8/24.9/21.0 | 170.7/172.7/99.7 | 7.0/6.0/5.4 | 459.3/361.4/229.1 |
| NEISO 2023/24/25 (post-(d), paired) | 189.6/118.2/123.2 | 105.8/104.1/114.1 | 15.3/13.6/13.8 | 43.3/35.0/36.1 | 7.6/6.7/6.6 | 361.5/277.6/293.8 |

Two standing observations from the anchor: **keeper-recipe growth dominates phase wins**
(the ercot213 pubanchor arm alone is ~+40 % of ERCOT year wall vs ercot204), and **NEISO's
`data_prep` is 118–190 s *every* year — the largest phase of its whole year** — an
unattributed anomaly worth its own charter.

**Environmental negatives (this container class, not the model):** the PJM keeper replay
(~14.5 GB peak) and the miso-160 keeper replay (≥13.9 GB) cannot fit the ~14.0 GB memory
cgroup this session's runner imposes under the host's 15 GB (cgroup swap accounting is
zero — a host swapfile goes unused). Full-8760 gates for those two need a box without the
cap; the 4368 h keeper-recipe pair method used here is the in-container fallback.

## PERF-B RESUME — the handed-forward `bench` lever, measured (2026-09-02)

WS3 resumed by owner ruling R-V (2026-09-01). Session `perf-b-apply`, branch
`claude/perf-b-apply-nabnpi`. Full narrative, attribution and gate record:
`docs/handoffs/perf-recheck-2026-08.md` §5. Conditions as §PERF-B above
(determinism pin, 4 vCPU / 15 GB with the 14.33 GB shell cgroup re-measured this
session, `uv.lock` env).

The five §PERF-B changes were re-verified present at HEAD; the charter's four
dispatch items are all landed or closed and needed no new code (perf-recheck §5.1).
This section records the one change this session added.

| Change | Where landed | Measured effect |
|---|---|---|
| (f) CAMPD normalization: parse `facilityId` over its uniques, skip the no-op split-facility remap, skip the no-op Feb-29 filter in a non-leap year | branch commit `27b3a92c` | `load_campd_hourly` PJM **−63.7 to −71.0 %** (best-of-3, arms alternating in one process: 19.43→6.55 / 21.04→6.11 / 14.03→5.09 s for 2023/24/25). Whole `_campd_hourly_frame`, cold: PJM 50.96→21.18 s, MISO 29.08→16.17 s. In-solve `bench` on the NEISO gate arms: 2.1/1.6/1.9 → **0.9/0.7/0.9 s** (−55 to −57 %); its `data_prep` also −5 to −34 % (CAMPD loads there too). **Reach is ISO-dependent** — see below. |

**Reach caveat, load-bearing.** `load_campd_hourly` reads one extract per (state,
year), so the win scales with an ISO's CAMPD footprint: 14 states for PJM/MISO
(`bench` 20.9–34.7 s/yr), 6 for NEISO (~2 s), **1 for ERCOT (0.9 s — the change is
wallclock-inert there)**. The percentages above must not be transferred across ISOs.
Against the ≥10 %-wall adoption rule: cleared on `results_write` for the 14-state
ISOs; **not** cleared as a share of total year wall anywhere (~2–4 % PJM/MISO, ~0 %
ERCOT).

**Byte gate.** NEISO full 8760 × 2023–2025, keeper `2026-08-17-neiso-99-joint-p1`,
arms differing only in `campd.py`: `regression_gate.py --mode byte` **check [1]
golden bundle diff PASS** (9 files, 32 numeric columns, atol=rtol=0), zero reshuffle
in all three years, smoke PASS, `audit_keepers` PASS, manifest pre-screen 10/10
artifacts matching. The script's overall `RESULT: FAIL` is check [4]
`legitimacy(--keepers)`, proven **pre-existing by control** (identical failure with
`campd.py` reverted, same exception and line, exit 1 both times) — a NYISO
capacity-deliverability data gap on main. **That makes `regression_gate.py` return
FAIL for every change on main right now**, which any lane running it needs to know
before reading its own verdict. Manifests committed under
`results/regression-goldens/perfb-campd-{before,after}/`.

**Merge is HELD, not blocked by this change.** Per the dispatch, a cross-ISO change
merges only once every ISO it touches has a current stage-0 golden;
`check_golden_manifest` reads **3 current (ERCOT, NEISO, PJM) / 3 stale (CAISO, MISO,
NYISO)**. CAISO/NYISO have a live capture lane; **MISO has none**, and `miso-200` is
moving that keeper, so a MISO golden captured now would be stale on arrival. That
sequencing is the director's call, not this lane's.

## WALLCLOCK A-3 — class-band sidecar vectorized, sidecar block put on the clock (2026-09-05)

Wallclock desk item A-3 (`docs/handoffs/wallclock-opportunities-2026-09.md` §2 A-3;
desk log `docs/handoffs/wallclock-desk-log-2026-09.md`). Branch
`claude/wc-a3-band-sidecar-clock-hfflwe` off `2886235c`. Conditions as §PERF-B above
(determinism pin, 4 vCPU / 15 GB, `uv.lock` env pandas 3.0.3 / pyarrow 24.0.0), NEISO
keeper `2026-08-17-neiso-99-joint-p1` replayed full 8760 × 2023–2025 through
`scripts/capture_keeper_goldens.py` on the merge-base tree (`wc-a3-before`, a sparse
worktree at `2886235c`) and the branch tree (`wc-a3-after`); **the two arms solved
concurrently** (peak 4.3–4.4 GB each), so every solve wall below carries the host-noise
caveat and only the phase-structure deltas are the signal. `scripts/run_calibration_full.py`
only; `pipeline/timing.py` untouched.

| Change | Where landed | Measured effect |
|---|---|---|
| (g) `_write_class_band_hourly_sidecar`: band once per distinct `unit_id` (`_band_categorical` — `_tranche_band` over the categorical's categories, indexed by codes) instead of per row | branch commit `4d5a59b2` | On the real NEISO 2023 P1 frame (6,718,920 rows, 767 distinct ids): the band `Categorical` **15.63 s → 0.16 s**, categories (`str` dtype), codes and values identical. The whole writer, end-to-end on that frame, **16.8 / 15.6 s → 4.6 / 5.3 s** (two rounds, measured while two solves shared the CPU), same output sha `de9e5a3f…`. Zero LP change by construction. |
| (h) the `hourly/` sidecar block moved from AFTER `log_year_phase_timing` to before it, as the new `sidecars` entry of `results_write_parts` | same commit | The six frozen fields are unchanged and `results_write == state + frames + parquet + bench + sidecars` exactly. Before, the block sat between one year's `_t_end` and the next year's `_t_year` — booked to no phase and no year's `total`. After (branch arm): `results_write` 12.4 / 10.0 / 10.9 s with `sidecars` **8.0 / 5.9 / 7.2 s** (2023/24/25) versus the control's 4.8 / 4.5 / 4.9 s with no sidecar term; the ~6–8 s/yr now visible is what remains of the block AFTER (g), the control's invisible block being that plus (g)'s ~11–12 s. |

**Byte gate.** Every `hourly/` sidecar (7 kinds × 3 years, 21 files) and every dispatch
frame sha256-identical between the arms; `class_band_hourly_{2023,2024,2025}`
`frame.equals` True (429,240 × 7 each). `scripts/regression_gate.py --mode byte`:
**check [1] golden bundle diff PASS** (NEISO, 9 files, 32 numeric columns, atol=rtol=0),
zero reshuffle in all three years, smoke PASS (24). Check [4] is **pre-existing by
control**: `legitimacy(--keepers)` is the standing NYISO `nyiso_li_lcr_tsl` capacity-
deliverability data gap (§PERF-B RESUME above), and `audit_keepers` reads the same
S1 stale-`status/NEISO.js` failure with byte-identical output on the merge-base tree.
Manifests committed under `results/regression-goldens/wc-a3-{before,after}/`.

**Phase lines, both arms (concurrent):**

| arm | year | data_prep | solve_p0 | markup | solve_p1 | results_write | total | results_write parts |
|---|---|---|---|---|---|---|---|---|
| before | 2023 | 116.0 | 109.1 | 6.4 | 42.1 | 4.8 | 278.3 | state=0.3 frames=0.9 parquet=1.8 bench=1.8 |
| before | 2024 | 9.6 | 119.2 | 6.6 | 36.7 | 4.5 | 176.6 | state=0.2 frames=0.7 parquet=1.6 bench=2.0 |
| before | 2025 | 7.2 | 123.1 | 6.1 | 41.6 | 4.9 | 183.0 | state=0.2 frames=0.9 parquet=2.0 bench=1.8 |
| after | 2023 | 89.8 | 116.5 | 6.8 | 43.3 | 12.4 | 268.7 | state=0.2 frames=1.0 parquet=1.8 bench=1.4 **sidecars=8.0** |
| after | 2024 | 8.4 | 120.4 | 6.0 | 35.1 | 10.0 | 179.9 | state=0.2 frames=1.0 parquet=1.5 bench=1.4 **sidecars=5.9** |
| after | 2025 | 6.3 | 108.6 | 6.5 | 35.9 | 10.9 | 168.1 | state=0.2 frames=0.9 parquet=1.5 bench=1.1 **sidecars=7.2** |

**Fast tier** on the branch: 8,104 passed / 3 failed. Both failures are not this change's:
`test_golden_manifest_provenance … carveout_bundle` fails identically on the merge-base
tree (its docstring: "Y-11 STOP (2026-09-05), left RED deliberately"), and
`TestDispatchPerformance::test_full_year_200_generator_fleet` is a 15 s solve-wall
threshold that read 20.2 s while the two replays were running and passes alone (5.6 s).
