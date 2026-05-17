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

### 2026-05-17 — ERCOT — calibration parameterization

- **Benchmark:** EPA eGRID 2023 ERCOT actuals; EIA-930 ERCOT system load
  2023; EIA Henry Hub spot 2023-2024; EIA-860 2024 plant inventory.
- **Calibration year:** 2023
- **Tolerance:** ±5% (input parity)
- **Overall:** Parameterized — calibration knobs derived in ad-hoc
  scripts and committed to the codebase. Six parameter groups updated.

| Diagnostic | Status | Notes |
|---|---|---|
| 1. Generation mix | Inputs updated | Gas price 2023/2024 historical anchors; thermal cycling adders shift the merit order; ERCOT TTC updates relax West-Texas export. |
| 2. Price duration curve | Inputs updated | Cycling adders raise marginal cost of cycling coal/gas units, sharpening the price shape. |
| 3. Average price | Inputs updated | Gas price historical entries align fuel cost with the 2023 actual ($2.54/MMBtu). |
| 4. Capacity factors | Inputs updated | Renewable zone distribution + vintage monthly ramp align modeled wind/solar siting and ramp-in with EIA-860 plant locations and COD dates. |

**Findings:**

- The gas price trajectory lacked historical 2023/2024 entries, so a
  2023 calibration run could not anchor fuel cost to the realized
  Henry Hub spot price.
- Renewable capacity was parked in a single zone per technology, which
  mis-distributed wind/solar siting relative to EIA-860 plant locations.
- Modeled renewable capacity was static year-end; it ignored the
  intra-year ramp-in from commercial-operation dates (ERCOT 2023 solar
  grew 11.4 GW → 14.9 GW, 45% of additions in Q4).
- The merit order omitted thermal cycling costs; coal and gas units
  that cycle were dispatched as if cycling were free.
- ERCOT West-Texas transfer limits used placeholder TTCs below the
  2021 RTP stability assessment.
- EIA-930 metered load was used directly as generation-side demand,
  omitting the ~5.8% T&D loss gross-up.

**Actions taken:**

- Added EIA Henry Hub spot 2023 ($2.54) and 2024 ($2.19) historical
  entries to all three `HENRY_HUB_TRAJECTORIES` paths.
- Added `ScenarioConfig.td_loss_factor` (0.058, Tier 3); `load_demand`
  grosses metered load up by `(1 + factor)`.
- Replaced the single-zone renewable allocation with an EIA-860
  plant-location distribution; added `ScenarioConfig.vintage_capacity_ramp`
  (Tier 3) for the month-varying capacity ramp from COD dates.
- Added nine Tier-3 thermal cycling cost adders (gas CC / coal / gas CT
  by efficiency bin) and `apply_cycling_adders`, called after
  `assemble_mc` in the dispatch pipeline.
- Updated ERCOT North→West (3000→5500 MW) and West→Houston
  (2500→3500 MW) TTCs to the 2021 RTP West Texas Export stability
  assessment.

---

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
