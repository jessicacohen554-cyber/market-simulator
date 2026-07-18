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
`scripts/diff_warmstart_bundles.py` alongside P-2's existing diff-gate):

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
