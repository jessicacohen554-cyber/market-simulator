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

> **Status update (reconciled with code).** The 2026-05-17 entry below is the *earliest* ERCOT calibration snapshot and is **superseded** by a long line of later runs (the "run14"–"run24" series tracked in the backcast dashboard / `results/calibration/` bundles — render with `/calibration-report`). Crucially, the Gas-CT under-dispatch it blames on "no unit commitment" was the motivation for the **commitment layer that has since been built** (methodology spec §1.6; opt-in `commitment_enabled`), and ERCOT now defaults to CAMPD per-plant binning with tranche offer curves (§3.3). Read the entry below as history, not current state.

### 2026-05-17 — ERCOT — eGRID 2023 calibration parameterization

- **Benchmark:** EPA eGRID 2023 rev2 ERCOT actuals; EIA-930 ERCOT system
  load 2023; EIA Henry Hub spot 2023-2024; EIA-860 2024 plant inventory.
- **Calibration year:** 2023
- **Tolerance:** ±5%
- **Overall:** FAIL — calibration in progress. Most fuels improved but
  remain outside ±5%; a TTC sweep and CC-adder re-tune are still open.
- **Full session detail:** see [`calibration-session-log.md`](calibration-session-log.md).

This run commits the calibration knobs that were derived in ad-hoc
scripts during the session into the codebase as sourced, parameterized
inputs. The session diagnostics below are the post-change results from
`calibration-session-log.md`.

| Diagnostic | Status | Notes |
|---|---|---|
| 1. Generation mix | FAIL | Gas CC +11%, Gas CT −69%, Coal −12%, Wind +7%, Solar +6.5% (after vintage ramp), Nuclear −1.5%. CO2 −14%. Gas CT gap reflected the pure-merit-order LP with no start-up economics — *since addressed* by the three-solve commitment layer (§1.6); later runs improve this. |
| 2. Price duration curve | Not benchmarked | Model is energy-only (no ORDC/AS); price shape not yet compared to ERCOT RT. |
| 3. Average price | FAIL | Load-weighted avg $21/MWh vs ERCOT 2023 RT ~$48/MWh — expected gap from energy-only formulation. |
| 4. Capacity factors | PARTIAL | Nuclear matches eGRID within 1.5%; efficient CC plants stay inframarginal (no UC), so flagship-plant CFs run high. |

**Findings:**

- The gas price trajectory lacked historical 2023/2024 entries, so a
  2023 run could not anchor fuel cost to the realized Henry Hub spot.
- Renewable capacity was parked in a single zone per technology,
  mis-distributing wind/solar siting vs EIA-860 plant locations.
- Modeled renewable capacity was static year-end; it ignored intra-year
  ramp-in from commercial-operation dates (ERCOT 2023 solar grew
  11.4 GW → 14.9 GW, 45% of additions in Q4). The vintage ramp cut the
  solar generation error from +33% to +6.5%.
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

**Open items** (carried from `calibration-session-log.md`): West-export
TTC sweep to produce realistic congestion; CC cycling-adder re-tune at
the final demand level; Gas CT structural gap (needs unit commitment);
coal price verification against EIA-923 Texas fuel receipts.

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

### 2026-06-09 — PJM — pjm 2 hydro-ps (results/calibration/pjm_2_hydro_ps)

- **Benchmark:** EIA-930 / EIA-923 / CAMPD, 2023 + 2024; actual hub LMP
- **Calibration years:** 2023, 2024
- **Model changes:** LP budget hydro (76 plants, ~3.3 GW, EIA-923 monthly
  budgets), EIA-860 pumped storage (~5.0 GW, 10 h, RTE 0.80), OTHER must-run
  injection un-gated for non-ERCOT (PS held out), EIA-860 2025 ER fleet
  basis, COAL_SUB dead knob removed (subbit → COAL_PRB). Offer curves carried
  unchanged from `pjm_n6_tuned`.

| Diagnostic | Status | Notes |
|---|---|---|
| 1. Generation mix | PARTIAL | gas +7% vs 930 (was +10%); coal −12/−16% vs 930 (was −2/−9%) — see findings |
| 2. Price duration curve | PASS | hours >$500: 11 (2023) / 3 (2024), was ~48; slack 9.6 / 1.9 GWh, was 17.7 / 13.5 |
| 3. Average price | PASS | 2023: 28.28 vs 29.33 DA / 28.44 RT actual (old 32.7); 2024: 26.44 vs 29.78 DA (old 31.8). Jul/Aug spike eliminated (29.5/30.1 vs old 45.5/54.5) |
| 4. Capacity factors | PARTIAL | CT_PEAKER 16.5 vs 29.5 TWh actual; COAL_BIT 91.8 vs 105.7 (2024) |

**Findings:**

- The July/August VOLL price spikes were structural scarcity from the missing
  hydro / pumped-storage / OTHER supply, not offer-curve error. With them in
  the LP the price level and shape land on actuals with the *old* curves.
- Coal and CT now under-dispatch because their tuned curves compensated for
  the scarcity regime: peaks are now served by PS (model PS discharge ~9-10
  TWh/yr vs ~3-4 actual — no cycling cost/outages on PS yet), and coal econ
  bands clear less at the lower price level.
- Nuclear +2.4% vs 930 after the EIA-860 2025 ER refresh (fleet revision).
- Oil still ~0 vs 0.6-0.9 TWh actual — needs winter gas (measured monthly /
  per-plant gas pricing) to bind.

**Actions taken / next:**

- Registered `pjm 2 hydro-ps`; dashboard benchmark now regenerates from the
  newest bundle (stale `pjm_8zone` removed).
- Next tuning run: re-tune CT_PEAKER / COAL_BIT bands for the corrected
  system (knobs now route correctly); consider a PS throughput cost or
  availability derate to pull PS toward its ~3-4 TWh actual; evaluate
  `gas_plant_monthly_fuel_pricing` for the Jan-2024 winter spike.

---
