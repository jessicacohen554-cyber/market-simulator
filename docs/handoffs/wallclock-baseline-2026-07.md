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

**Neutrality (cold vs warm-from-persisted, per year — `scripts/diff_warmstart_bundles` +
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
