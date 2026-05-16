# Calibration Log

This log records calibration runs that compare simulated results against
published benchmarks on common inputs. Each run is produced by
`market_sim.results.calibration.run_calibration_check`, which loads one
cached scenario-year and walks four diagnostics. Add an entry here whenever
a scenario is calibrated against a benchmark source.

## Calibration targets

All diagnostics use a ±5% tolerance unless a run notes otherwise
(`market-sim-build-plan.md` Phase 7).

- **Generation mix** — within ±5% of the benchmark for every fuel type.
- **Price duration curve** — P10 / P50 / P90 / mean within ±5% of the benchmark.
- **Average price** — within ±5% of the benchmark.
- **Capacity factors** — within ±5% of the benchmark per fuel.

## Diagnostic order

Diagnostics run in a fixed order so an upstream failure explains the ones
below it. Read the results top-down and stop at the first failure — fixing
it often clears the rest.

1. **Generation mix** — wrong dispatch volumes invalidate every downstream check.
2. **Price duration curve** — wrong price *shape* points at marginal-cost or
   scarcity-pricing issues.
3. **Average price** — a price-*level* offset on an otherwise correct shape.
4. **Capacity factors** — per-fuel utilization, the finest-grained check.

Workflow: establish input parity first, then compare dispatch, then prices.

## Benchmark sources

| Source | Coverage | Notes |
|---|---|---|
| _e.g._ EIA-930 | ISO hourly generation by fuel | Common-input historical year |
| _e.g._ ISO market reports | Hourly LMP / settlement prices | Price duration curve, avg price |
| _e.g._ NRC PRIS, EIA-860 | Capacity factors by fuel | Per-fuel utilization |

## Runs

<!-- Copy the block below for each calibration run. Newest first. -->

### YYYY-MM-DD — &lt;ISO&gt; — &lt;scenario cache_key&gt;

- **Benchmark:** &lt;source, year&gt;
- **Calibration year:** &lt;year&gt;
- **Tolerance:** ±5%
- **Overall:** PASS / FAIL

| Diagnostic | Status | Notes |
|---|---|---|
| 1. Generation mix | | |
| 2. Price duration curve | | |
| 3. Average price | | |
| 4. Capacity factors | | |

**Findings:**

-

**Actions taken:**

-

---
