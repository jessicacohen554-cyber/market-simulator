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
