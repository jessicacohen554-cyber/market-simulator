# Wallclock Efficiency Refactor — Plan & Prompt Pack (2026-07-12)

## Context

Per-year runs feel slower than expected. A four-way code audit (LP build/solve path,
orchestration, data layer, prior perf work) was run against the actual source — every finding
below was verified at the cited file:line, not taken from docs. Headline: **the solve path is
already mature** (bulk `addCols`/`addRows`, fully vectorized kron/COO matrix assembly, presolve
deliberately off, P0→P1 intra-year warm-start shipped and default-on, exactly 2 LP solves per
year with all scarcity overlays as post-solve NumPy). There is no "iterative looping" pathology
in the hot path. What remains is a small set of concrete, low-risk levers — the largest being a
**config-default flip on an already-validated cross-year warm-start** (~1.5–2× on years ≥2 of a
multi-year backcast) and a handful of **missing caches that re-parse the same CSV hundreds of
times per fleet build**.

Measured anchor (ERCOT, per-plant 7-zone, 8760 h): cold P0 solve ≈ 135–153 s, matrix build ≈
1–2 s, full year wall ≈ 165–185 s. The LP solve is ~82 % of the year; the rest is data prep +
results writing. Larger ISOs (PJM/MISO reserve co-opt) are minutes per year and RAM-bound.

**Integrity constraint for every change:** LP optimum, prices, dispatch, and bundle outputs must
be bit-identical (or provably marginal-tie-only, as with warm starts) — this is a wallclock
refactor, not a model change. Years stay sequential within a run (CLAUDE.md rule 12).

## What is already optimal — do not touch

Verified compliant; re-litigating these wastes a session:

- **Matrix build**: `sp.kron(eye(T), …)` energy balance (`dispatch.py:2489`), single-COO SOC
  block (`dispatch.py:2574`), one-shot `_vstack_csr_free` stack (`dispatch.py:2843`). No loops
  over 8760 anywhere; remaining loops are over families/zones/tiers (single digits).
- **HiGHS ingestion**: one `addCols` + one `addRows` from CSR buffers (`dispatch.py:3656,3680`),
  scipy shell `del`'d before ingest. `passModel` would break the placeholder-cost warm-start
  design — rejected.
- **Presolve off** (`dispatch.py:3650`): measured ~17 s pure overhead on the 1.8M-col LP.
- **P0→P1 warm-start** (`pipeline/solve.py:143–198`, `changeColsCost` at `dispatch.py:3925`):
  one model built per year, P1 converges in a few simplex iterations (~5×). Default on.
- **P0 is not wasted**: its run-lengths feed `compute_monthly_markup` (`solve.py:155–165`) and
  its basis warm-starts P1. Do not try to remove it.
- **No hidden re-solves**: ORDC/CAISO scarcity overlays and lookahead reprice are post-solve
  NumPy (`runner.py:1582–1699,1742`); reserve co-opt is extra rows in the same LP, not a second
  solve. Default path = exactly 2 solves/year.
- **Forecast year loop already hoists** all year-invariant loads (`runner.py:490–641`); backcast
  frees LP/demand state between years (`run_calibration_full.py:2628–2630`).
- **Data layer architecture**: runs read small curated Parquet artifacts, not the 100s-of-MB raw
  trees (curation is offline). EIA-930 hourly, EIA-923 fuel cost, eGRID rates all flow through
  existing `lru_cache`/module caches. Solution/dual extraction is vectorized.
- **Forecast cross-year warm-start stays OFF**: the marginal-tie reshuffle can flip a
  retire/keep decision in `capacity.evolve_fleet` (measured ≤0.4 $/MWh trajectory drift). This
  rejection is correct; the flip below is backcast-only.

## Findings and plan

### Tier 1 — biggest wins, already validated or measured

**T1.1 — Flip cross-year warm-start ON by default for the calibration/backcast path.**
`MARKET_SIM_WARMSTART_XYEAR` (default off) gates `apply_cross_year_basis`
(`dispatch.py:4111–4188`, threaded via `pipeline/solve.py:145,215` and
`run_calibration.py:3885`). Already benchmarked on real ERCOT 2023–2025 LPs: P0 2.3× faster on
warm years, ~1.47× total 3-year wall, +4 % RSS, objective/prices/total-gen identical (only
marginal-tie reshuffle ~0.003 %). The remaining work is a default flip in the calibration
scripts plus one `diff_warmstart_bundles.py` re-score gate per ISO. Forecast path unchanged.
*Impact: high (every multi-year backcast). Risk: none beyond the already-characterized tie
reshuffle; gated by bundle diff.*

**T1.2 — Kill the per-plant CSV re-parse in fleet build.**
`st_gas_intermediate_plants` (`fleet.py:6960`) and `cc_intermediate_plants` (`fleet.py:6991`)
lack the `@lru_cache(maxsize=8)` their identical-signature sibling `ct_intermediate_plants`
(`fleet.py:6906`) has. They are called from `_offer_curve_for_group`
(`offer_curves.py:280,294`) once per CC/ST plant inside the `bins_to_fleet` per-plant loop
(`fleet.py:7388`), so `thermal_tranches_<ISO>.csv` is `pd.read_csv`'d **hundreds of times per
fleet build** with the intermediate-split defaults on. Two decorator lines.
*Impact: med-high on non-ERCOT fleet builds, per run-year. Risk: none (pure function of
hashable args; mirrors the existing cached sibling).*

**T1.3 — Optional skip-solved flag for calibration re-runs.**
`solve_and_persist` (`run_calibration_full.py:2278`) always re-solves every `--year` into a
fresh timestamped bundle; `results/cache.py::is_cached` protects only the forecast path
(`runner.py:1036`). Add an **opt-in** `--reuse-solved <bundle>` that reuses a prior bundle's
per-year solve artifacts when the config hash matches, re-running only reporting/diagnostics.
Never a silent default — fresh-bundle-per-invocation is the current contract.
*Impact: high for iterate-on-reporting workflows; zero when solving new configs. Risk: low,
opt-in only, keyed on `ScenarioConfig.cache_key()`.*

### Tier 2 — zero-risk Python overhead (single session, batched)

- **T2.1** `load_demand` parsed twice per backcast year — `run_calibration_full.py:2284` and
  again inside `run_year` (`run_calibration.py:1443`), and it is not cached
  (`eia_loader.py:2809`). Pass the loaded array into `run_year` (preferred, explicit) rather
  than adding a cache keyed on a config object.
- **T2.2** Memoize `load_campd_bins` (`fleet.py:6226`) — re-parses + re-post-processes
  `custom-bin-assignments.csv` ≥2× per year-solve (`fleet.py:8031`, `outages.py:610`). Manual
  dict memoize keyed on args, **return a defensive copy** (callers may mutate).
- **T2.3** `bins_to_fleet` row loop `for _, b in bins.iterrows()` (`fleet.py:7230`) →
  `itertuples`/`to_dict("records")` (materially faster row access; object construction is
  inherently row-wise and stays).
- **T2.4** Cache `load_plant_registry` (`fleet.py:5556`, bare `read_csv` of the 120 KB
  registry, called from `bins_to_fleet` at `fleet.py:7142`).
- **T2.5** `backcast_config` rebuilt twice more per run just to read two fields for `meta`
  (`run_calibration_full.py:2713,2716`) — reuse the year-loop `cfg`.
- **T2.6** `renewables.py:791` iterrows over proposed plants; `fleet.py:7067` iterrows over the
  small override sheet — convert while in the file, low value alone.

*Impact: bounded by the ~18 % non-solve share (~15–30 s/year ERCOT-scale, more for big fleets).
Risk: none — every fix is caching or access-pattern only, gated by byte-identity replay.*

### Tier 3 — bench-first experiments (adopt only on measured win)

- **T3.1** IPM (`solver=ipm`, `run_crossover=on`) for the **first cold P0 only**, handing the
  crossover basis to P1. Options block is `dispatch.py:3636–3652`; today only presolve/threads/
  scaling are set — solver choice, crossover, and parallelism knobs are unexplored. Dual simplex
  + basis reuse is well-tuned, so this may lose; bench with the existing
  `scripts/bench_warmstart.py` harness before touching defaults. **Never touch feasibility
  tolerances** (accuracy).
- **T3.2** numpy-array `setBasis` in `apply_cross_year_basis` — the two Python list-comps over
  ~1.8 M columns (`dispatch.py:4184–4185`) exist only because of the highspy list API; newer
  highspy accepts arrays. Check installed build; fall back to list-comp otherwise.
- **T3.3** Threads: `MARKET_SIM_HIGHS_THREADS` is unset by default (HiGHS auto). Bench a
  documented per-ISO recommendation (parallel dual simplex trades RAM and marginal-tie
  determinism for speed); keep single-thread the golden/repro default.

### Explicit skips (audited, rejected)

- **P2 warm-start off P1's basis**: both cold `solve_dispatch` P2 calls
  (`pipeline/commitment.py:691,842`) live inside `run_commitment_pass` — the **archived legacy
  P2 path** no keeper uses (CLAUDE.md "P2 is ARCHIVED"). Not worth code risk on a dead path.
- **Parallelizing years within a run** — forbidden (RAM, rule 12).
- **Removing P0 / collapsing to one solve** — changes P1 bid cost (markup needs P0 run-lengths).
- **`data/clean` seam "activation" for speed** — it replaces already-curated Parquet, not raw
  CSV; no wallclock lever there.
- **Per-generator markup loop** (`model/commitment.py:282`) — accuracy-load-bearing run-length
  detection, small next to the solve; flag only.
- **Forecast prior-year `DispatchResult` slimming** (`runner.py:1823–1896`) — RAM lever, not
  wallclock; optional follow-on, needs a field-usage audit of the capacity screens first.

### Instrumentation first (P-0, enabler)

There is no prep/solve/write split anywhere: the forecast logs only total year wall
(`runner.py:1039,1548`) and `solve_and_persist` logs none (`run_calibration_full.py:2314`).
`DispatchResult.build_time/solve_time` already exist (`dispatch.py:3352,3867,3927`). Add a
per-year phase-timing log line (data-prep / solve P0 / markup / solve P1 / results-write) to
both orchestrators so every later change is quantified against a real baseline.

## Verification protocol (applies to every prompt)

1. **Byte-identity gate**: capture goldens before the change with
   `scripts/capture_keeper_goldens.py` (runs `MARKET_SIM_WARMSTART_XYEAR=0`, single thread),
   re-run after, diff. Tier-2 changes must be **bit-identical**. Warm-start changes use
   `scripts/diff_warmstart_bundles.py` (objective/prices/total-gen identical; per-unit diffs
   confined to documented marginal ties).
2. **Timing evidence**: report before/after per-phase timings from the P-0 instrumentation on
   at least ERCOT + one big co-opt ISO (PJM or MISO), all three backcast years.
3. **Tests**: full pytest; `tests/test_dispatch.py::TestSolverBenchmark` bounds still hold.
4. **No new tuning surface**: no env-var knobs that change results (rule 24) — speed-only
   toggles are fine but must be results-neutral by construction.
5. No dashboard registration — these are not calibration runs; keeper bundles are untouched.

## Execution order

| # | Workstream | Prompt | Model | Expected win |
|---|-----------|--------|-------|--------------|
| 0 | Phase-timing instrumentation + baseline capture | P-0 | Sonnet 5 | enabler |
| 1 | Data-layer cache batch (T1.2, T2.1–T2.6) | P-1 | Opus 4.8 | 10–30 s/yr, more on big fleets |
| 2 | Cross-year warm-start default flip, backcast only (T1.1) | P-2 | Opus 4.8 | ~1.5–2× on years ≥2 |
| 3 | Calibration `--reuse-solved` opt-in (T1.3) | P-3 | Fable 5 | whole solves skipped on re-runs |
| 4 | HiGHS bench: IPM+crossover, numpy setBasis, threads (T3) | P-4 | Opus 4.8 | measure first |

### Waves (parallel vs sequential)

```
Wave 1:  P-0  ──────────────► merge to main   (blocking; everyone rebases on it)
                                │
Wave 2:         ┌──────────────┴──────────────┐
                P-1 ‖ P-4   (parallel)  ──────► merge each
                                │
Wave 3:                        P-2 ──► merge ──► P-3 ──► merge
```

- **Wave 1 — blocking:** P-0 lands the phase-timing log lines every later prompt cites for
  before/after evidence, plus the baseline doc. Merge before launching anything.
- **Wave 2 — fully parallel, zero conflict:** P-1 (data layer: `fleet.py`, `offer_curves.py`,
  demand-load region) and P-4 (`dispatch.py` options block + bench scripts) touch disjoint files.
- **Wave 3 — sequential:** P-2 then P-3 both add argparse flags and edit `solve_and_persist` in
  `run_calibration_full.py` — a hard conflict if simultaneous. Run P-2 (bigger win) first, merge,
  then P-3 rebases on top. P-1's `run_calibration_full.py` edits are in different functions, so it
  coexists with Wave 3 fine.
- Alternative: run Waves 2+3 all at once and eat one manual P-2/P-3 merge resolution — trades one
  conflict cleanup for wall-clock.

Model rationale: P-0 is mechanical instrumentation whose wallclock is in the solves, not the
reasoning (Sonnet 5). P-1/P-2 are mostly mechanical but cross-cutting — kwargs-equivalence
reasoning, forecast-path quarantine, repro pins — with a byte-identity gate as the safety net
(Opus 4.8). P-3 has the highest correctness stakes in the pack: a cache key that under-covers
silently serves stale solves as fresh science, and the contract design is judgment-heavy
(Fable 5). P-4's adoption rule is mechanical (≥10 % + identical outputs), so bench execution
fits Opus 4.8.

## Prompt pack

Each prompt is self-contained for a fresh session on a fresh branch off `main`.

### P-0 — timing instrumentation + baseline — **model: Sonnet 5**

```
In market-simulator, add per-year phase timing to both orchestrators, then capture a baseline. This is a wallclock-efficiency enabler; outputs must be byte-identical.

1. In scripts/run_calibration_full.py::solve_and_persist (year loop at ~line 2278) and src/market_sim/runner.py::run_scenario_iso (year loop at ~line 652), add time.perf_counter() phase marks and ONE summary log line per year: data_prep_s, solve_p0_s, markup_s, solve_p1_s, results_write_s, total_s. Reuse DispatchResult.build_time/solve_time (src/market_sim/model/dispatch.py, populated at ~3352/3867/3927) instead of re-timing the solve. Logging only — no behavior change, no new files, no env knobs.
2. Run the ERCOT backcast (scripts/run_calibration_full.py --iso ERCOT --year 2023 2024 2025, throwaway --out-dir, do NOT register on the dashboard) and one big co-opt ISO (PJM or MISO, same years) and record the per-phase table in docs/handoffs/wallclock-baseline-2026-07.md.
3. Verify: full pytest passes; a golden replay (scripts/capture_keeper_goldens.py before/after on one keeper) is byte-identical.
Commit with the baseline doc. Do not change any solver options or caching in this session.
```

### P-1 — data-layer cache batch (zero-risk, byte-identical) — **model: Opus 4.8**

```
In market-simulator, apply a batch of caching/access-pattern fixes in the data layer. Hard requirement: model outputs must be BYTE-IDENTICAL — capture goldens with scripts/capture_keeper_goldens.py before starting and diff after each item. No accuracy, no new tunables.

1. src/market_sim/data/fleet.py:6960 (st_gas_intermediate_plants) and :6991 (cc_intermediate_plants): add @lru_cache(maxsize=8), exactly mirroring ct_intermediate_plants at :6906. These are called once per CC/ST plant from _offer_curve_for_group (src/market_sim/data/offer_curves.py:280,294) inside the bins_to_fleet per-plant loop, re-reading thermal_tranches_<ISO>.csv hundreds of times per fleet build.
2. src/market_sim/data/fleet.py:6226 (load_campd_bins): memoize with a module-level dict keyed on its args (pattern: _PLANT_MONTHLY_CACHE in src/market_sim/data/fuel.py:526). Return a defensive .copy() — callers may mutate. Call sites: fleet.py:8031, src/market_sim/data/outages.py:610.
3. Eliminate the double demand load per backcast year: scripts/run_calibration_full.py:2284 loads demand, then run_year (scripts/run_calibration.py:~1443) loads it again. Thread the loaded demand array from solve_and_persist into run_year via a new optional parameter (default None → load as today); verify both call sites resolve identical kwargs before wiring (strict_demand_profile / caiso_demand_clock_realign / include_interchange must match or the pass-through must carry them).
4. src/market_sim/data/fleet.py:7230 (bins_to_fleet): replace `for _, b in bins.iterrows()` with itertuples or to_dict("records") row access. Keep the per-row Generator construction as-is.
5. src/market_sim/data/fleet.py:5556 (load_plant_registry): cache the read (lru_cache on a path-string wrapper or dict memoize + defensive copy). Check no caller mutates the frame first.
6. scripts/run_calibration_full.py:2713,2716: stop rebuilding backcast_config twice for meta — reuse a config already built in the year loop.
Verification: (a) golden replay byte-identical per item (revert any item that isn't and report why); (b) full pytest; (c) before/after per-phase timings from the P-0 instrumentation for ERCOT + PJM or MISO backcast years, reported in the PR body. Watch memory: new caches are small (CSV-derived frames/frozensets), but confirm no growth in peak RSS on a big-ISO year.
```

### P-2 — cross-year warm-start default ON for backcast — **model: Opus 4.8**

```
In market-simulator, flip the already-validated cross-year warm-start to default ON for the calibration/backcast path only. Context: MARKET_SIM_WARMSTART_XYEAR (default off) gates apply_cross_year_basis (src/market_sim/model/dispatch.py:4111-4188), threaded through pipeline/solve.py:145,215 and the xyear_cache in scripts/run_calibration.py:~3885. Benchmarked on real ERCOT 2023-2025 LPs (docs/cross-year-warmstart.md): P0 2.3x faster on warm years, ~1.47x total 3-year wall, +4% RSS, objective/prices/total-gen identical, ~0.003% marginal-tie reshuffle only.

1. Make the calibration scripts (scripts/run_calibration.py, scripts/run_calibration_full.py) enable cross-year warm-start by default, with an explicit --no-xyear-warmstart opt-out and the env var still honored. The forecast path (runner.py) must remain COLD-only — the capacity-evolution tie-flip rejection stands; assert/verify runner.py cannot pick up the new default.
2. Keep golden/repro paths cold: scripts/capture_keeper_goldens.py already pins MARKET_SIM_WARMSTART_XYEAR=0 (line ~83) — confirm replay_keeper.py / bench-repro.yml likewise pin it, and pin where missing, so reproducibility baselines stay basis-independent.
3. Gate: for ERCOT and one big co-opt ISO (PJM or MISO), run the full 3-year backcast cold vs warm and diff with scripts/diff_warmstart_bundles.py — objective, prices, total generation identical; per-unit diffs confined to documented marginal ties. Include the diff summary and before/after wall-clock per year in the PR body.
4. Do NOT register these probe runs on the dashboard. Update docs/cross-year-warmstart.md's "default" wording and CHANGELOG.
```

### P-3 — opt-in reuse of solved years in calibration re-runs — **model: Fable 5 (high reasoning)**

```
In market-simulator, add an OPT-IN way to skip re-solving unchanged years when re-running scripts/run_calibration_full.py. Today solve_and_persist (line ~2278) always re-solves every --year into a fresh timestamped bundle; results/cache.py::is_cached protects only the forecast path (runner.py:1036).

1. Add --reuse-solved <prior_bundle_dir>: for each year, if the prior bundle's persisted run_config.json/config hash matches the current ScenarioConfig.cache_key() for that year AND the per-year solve artifacts exist, load them instead of solving; otherwise solve fresh. Mixed bundles must be clearly labeled in meta (which years reused, from which bundle, with hashes).
2. Never a default: absent the flag, behavior is byte-identical to today (fresh timestamped bundle, all years solved). The flag description must say reused years are NOT fresh evidence — for keeper promotion a full fresh solve is still required.
3. Hash coverage is the correctness crux: the reuse key must cover everything that changes a solve (full ScenarioConfig via cache_key(), plus the git-tracked state of derived inputs the config doesn't capture — at minimum refuse to reuse when the working tree is dirty under src/ or the relevant data artifacts' mtimes/sizes changed; document what the key does NOT cover).
4. Verify: (a) reuse run vs fresh run of an identical config produces identical bundle payloads (minus timestamps/meta); (b) changing any config field forces a re-solve of the affected year; (c) full pytest. Report wall-clock for a reporting-only re-run (3 years reused) in the PR body.
```

### P-4 — HiGHS solver experiments (bench-only; adopt on measured win) — **model: Opus 4.8**

```
In market-simulator, run three bounded HiGHS experiments for the cold first solve. These are BENCH-FIRST: no default changes unless the bench shows a clear win with unchanged results. Options block: src/market_sim/model/dispatch.py:3636-3652 (currently: output_flag off, presolve off, optional threads/scale via env). Harnesses: scripts/bench_warmstart.py and scripts/bench_warmstart_xyear.py (capture real ERCOT year LPs and time cold/warm solves).

1. IPM for the cold P0: solver=ipm + run_crossover=on for the FIRST solve of a year only, then hand the crossover basis to the existing P1 warm-start (changeColsCost path at dispatch.py:3925). Bench cold-P0 wall and P1 iterations vs the dual-simplex baseline on ERCOT and one big co-opt ISO capture. NEVER touch primal/dual feasibility tolerances.
2. numpy setBasis: apply_cross_year_basis materializes two Python lists over ~1.8M columns (dispatch.py:4184-4185). If the installed highspy accepts array input for setBasis, use it with a list-comp fallback; bench the xyear apply overhead before/after.
3. Threads: bench MARKET_SIM_HIGHS_THREADS in {1, 4, unset} on the big-ISO capture, recording wall and peak RSS. Deliverable is a documented per-ISO recommendation in the docs, not a default change — single-thread stays the golden/repro pin.
Adoption rule per experiment: adopt only if >=10% cold-solve wall improvement AND objective/prices identical (marginal-tie-only diffs); otherwise record the negative result in docs/handoffs/wallclock-baseline-2026-07.md so it is not re-run. Full pytest + golden replay for anything adopted.
```

## Expected end state

For a 3-year backcast on ERCOT-scale: ~165–185 s/year today → P-1 trims the ~18 % non-solve
share, P-2 cuts warm-year solves ~2.3×, landing roughly 1.5–1.8× total wall; big co-opt ISOs
should gain proportionally more from P-2/P-4. P-3 makes reporting-only re-runs near-free.
Nothing in the pack changes model outputs beyond the already-characterized marginal-tie
reshuffle of warm starts, and every prompt carries its own byte-identity gate.
