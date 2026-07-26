# Session handoff — cross-year LP warm-starting

Paste this as the opening prompt for the next session.

---

## Context

You are continuing a prototype that **warm-starts the calibration dispatch LP
across simulation years**. Background: each year solves a HiGHS LP. Intra-year
warm-start already exists (P0 and P1 share the LP; P1 re-costs P0's basis via
`changeColsCost`, ~5× on the second solve). The remaining cold cost is each
year's **P0** first solve. Adjacent years share zones, network and most units, so
a prior year's optimal basis is a strong warm start for the next year's P0.

That cross-year mechanism is **built, tested, benchmarked, and pushed** on branch
`claude/cross-year-warmstart-prototype-zwz3ov` (off `main`). It ships **behind a
flag, default off**. This handoff is to continue the follow-on work.

## What already landed (read these first)

- **`docs/cross-year-warmstart.md`** — the full design, options (a/b/c) tradeoff,
  measured results, and recommendation. Single best starting read.
- **Mechanism** — `src/market_sim/model/dispatch.py`:
  `CrossYearBasis` dataclass, `DispatchModel.export_cross_year_basis()` /
  `apply_cross_year_basis(prev)`, and `_cross_year_column_map(...)`. Approach is
  **option (c)**: remap a prior basis onto the new fleet (surviving units by
  `unit_id`; index-stable per-hour blocks + energy/storage rows by position; new
  columns nonbasic-at-bound, new rows basic; loaded as an *alien* HiGHS basis).
  No LP growth → no memory cost. Chosen over (a) superset matrix and (b)
  unchanged-fleet-only.
- **Calibration wiring** — `scripts/run_calibration.py`: a one-element
  `xyear_cache` list is threaded `main()` → `run_year(...)`, gated by
  `MARKET_SIM_WARMSTART_XYEAR=1` (mirrors `MARKET_SIM_WARMSTART`). The basis is
  exported after P1 and applied before P0 of the next year.
- **runner.py unification** — `src/market_sim/runner.py` P0/P1 now build one
  `DispatchModel` and re-cost (the intra-year ~5×) instead of two cold
  `solve_dispatch` calls. **Cross-year is NOT yet wired into runner.py** (that is
  follow-on #1 below). The P2 commitment pass is still a separate cold solve.
- **Tests** — `tests/test_cross_year_warmstart.py` (neutrality across a changed
  fleet; horizon-mismatch fallback). `tests/test_runner.py` updated to mock the
  build-once path via `_FakeDispatchModel`.
- **Benchmark** — `scripts/bench_warmstart_xyear.py` captures the real ERCOT
  2023/2024/2025 LPs once (pickled to `results/warmstart_xyear_capture.pkl`),
  then times cold vs cross-year-warm and diffs neutrality. Output at
  `results/warmstart_xyear_bench.txt`.

## Key facts that make this safe / cheap

- **An LP's optimum is basis-independent** → warm-start can only change the solve
  *path*, never cleared prices/generation. A wrong/partial mapping costs
  iterations, not correctness. This is why neutrality is essentially guaranteed.
- A **generator add/retire changes only columns** (capacity is a column bound;
  generation enters energy balance via coefficients). Storage changes touch both
  columns and the storage SOC rows (unit-major `s*T + hour`). Energy-balance rows
  are `n_zones*T`, hour-major.
- The big LP cost is the **solve** (~135–153 s cold P0), not the build (~1–2 s).

## Measured results (ERCOT, 8760 h) — already in the doc

- **P0 speedup**: 2.14× (2024), 2.52× (2025); ~2.3× steady-state. Year 1 is cold
  either way (no predecessor). Per-warm-year wall ~1.9×; 3-year total 1.47×.
- **Memory**: 7.34 → 7.62 GB (+4%) — option (c) adds only int8 status vectors.
- **Neutral**: isolated-LP A/B and a full-`run_year` end-to-end A/B (markup
  recomputed) are both bit-identical on objective (relΔ ~1e-15), zonal prices
  (Δ ≤ 9e-13 $/MWh) and total generation (Δ ≈ 0); only ~0.0033%-of-generation
  reshuffling among units tied at the margin (the intra-year standard).

## How to reproduce / validate

```bash
pip install -e .            # highspy etc. (fresh container has no deps)
python -m pytest tests/test_cross_year_warmstart.py -q
# Benchmark (capture is ~15 min the first time, then cached):
MARKET_SIM_WARMSTART=0 MARKET_SIM_HIGHS_THREADS=4 \
  python scripts/bench_warmstart_xyear.py     # capture needs WARMSTART=0
# Turn the feature on in a real run:
MARKET_SIM_WARMSTART_XYEAR=1 python scripts/run_calibration.py --year 2023 2024 2025
```

Gotchas: capture must run with `MARKET_SIM_WARMSTART=0` (so both P0/P1 go through
the spied `solve_dispatch`). Years must run **in one process, chronological order**
for the in-memory cache to help. A pre-existing formatter drifts
`tests/test_caiso_import_solar_shape.py` — keep it reverted, it's unrelated.

## Your task — follow-on, in priority order

**#1 (highest value): wire cross-year warm-start into the forecast path
(`runner.py`).** The forecast evolves the fleet year-by-year over a long horizon
(not just 3 backcast years), so the ~2.3× steady-state compounds far more there.
The mechanism already exists; this is mostly threading an `xyear_cache` through
`runner.py`'s year loop the way `run_calibration.py` does, behind the same flag,
plus a neutrality A/B. Scope into this branch or a fresh one off it.

Backlog (do as separate, smaller PRs):
- **#2 Promotion gate**: bundle-level `run_calibration` flag off vs on →
  `scripts/diagnostics/diff_warmstart_bundles.py` per `plant_code` + re-score, then flip
  `MARKET_SIM_WARMSTART_XYEAR` on by default. (Only when ready to ship the
  default.)
- **#3 Serialize `CrossYearBasis`** into the bundle dir so per-year parallel runs
  (separate `--out-dir`, different processes) can load the predecessor's basis.
- **#4 Extend the basis remap to co-opt families** (reserve/ORDC) + hydro/RPS
  rows — ERCOT-coopt and PJM reserve runs currently warm-start weaker (speed
  only; energy-only ERCOT already gets the full 2.3×).
- **#5 Map storage by unit id, not position** (robust to reordering; speed only).
- **#6 Other ISOs**: one neutrality A/B each (NYISO/CAISO/MISO/PJM).

Do NOT conflate with the P0-elimination idea — cross-year warm-start keeps full
fidelity and is the bigger prize. Develop on
`claude/cross-year-warmstart-prototype-zwz3ov` (or a branch off it); commit and
push there; do not open a PR unless asked.
