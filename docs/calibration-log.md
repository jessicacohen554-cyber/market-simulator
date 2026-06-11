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

### 2026-06-10 — PJM — tuning passes 3-7 (pjm 3 ps-adder … pjm 7 ct-depth)

- **Benchmark:** EIA-930 / EIA-923 / CAMPD, 2023 + 2024; actual hub LMP
- **Recommended baseline: `pjm 6 cc-peak`** (results/calibration/pjm_6_ccpeak)
- **Model changes through the loop:** pumped-storage dispatch adder
  ($10/MWh, reduced-form reserve duty — PS was arbitraging ~2.5x observed);
  `gas_monthly_actuals` (measured EIA-923 ISO-monthly delivered gas — Jan-24
  $5.07 vs ~$2.5 shaped); offer-curve deltas per pass (see run notes).

| vs EIA-923 (2023 / 2024) | pjm 2 | pjm 6 |
|---|---|---|
| CC_REGULAR | +2.5% / +5.3% | **−1.9% / +1.6%** |
| COAL_BIT | −6.1% / −13.1% | **+1.8% / −7.8%** |
| CT_PEAKER | −38% / −44% | **−16% / −21%** |
| Avg LMP (act ~29.3/29.8 DA) | 28.28 / 26.44 | 27.49 / 25.78 |
| Jan LMP 2024 (act 38.0 RT) | 33.9 | **38.7** |

**Findings:**

- Coal's flat monthly deficit was the committed (self-scheduled) tranche
  priced out by the CC econ ramp (15% CF); committed −0.10 fixed 2023 and
  halved 2024.
- CC's duct-firing peak band at 1.62× (~$28) was the summer price ceiling;
  raising it to 2.17× landed CC both years and re-opened CT's window.
- Summer LMP remains low (Jul/Aug 2024 ~30/25 vs ~38/31): the summer
  marginal price sits inside the abundant CC econ ramp — an energy-only
  residual (reserves/congestion/uplift), not an offer-band knob. Pass 7
  (deeper CT, more committed coal) confirmed diminishing returns and a
  2023 coal overshoot; pjm 6 is the keeper.

**Open items:** CT winter/shoulder runtime (−5-6 TWh, commitment/dual-fuel
behavior); ST_GAS 2024 winter (−15%); oil ~0 vs 0.9 TWh; nuclear +2.4%
(EIA-860 2025 ER fleet revision; consider refuel-outage overlay); summer
LMP scarcity component; stale `test_coal_supply_pricing_uses_year_trajectory`
on main (asserts pre-measured-PRB constant).

---

## Cross-class offer-curve tuning Jacobian (2026-06-11)

**Tool:** `scripts/derive_offer_curve_jacobian.py` → `inputs/processed/offer_curve_jacobian.csv`
(long format: `iso, year, out_class, band, in_class, dTWh_per_unit_mult, n_obs, stderr, confidence`).
Pure parquet/JSON analysis of the existing calibration bundles — no LP re-solve. Re-run it
after every new backcast bundle lands; unknown runs are auto-classified (scenario-config
equality + git diff between recorded shas + note keywords) so it keeps working for every
ISO as tuning sequences accrue.

**Method.** From consecutive run pairs whose only difference is offer-curve band-multiplier
moves, collect observations Δ(band multipliers) → Δ(class TWh) per year and fit a
ridge-regularized linear map `Δgen[class] ≈ Σ S[class,(class2,band)]·Δmult[(class2,band)]`,
with leave-one-pair-out jackknife standard errors. Pairs with structural code/data changes
are excluded via a curated registry in the script: Run-63 (storage fix), Run-64 (ER plant
append), Run-66 (CHP BTM trim), Run-68 (measured PRB fuel), Run-69 (CC_CHP eGRID HR
re-base), Run-71 (demand alignment), Run-73 (CHP steam-floor + Petra Nova). Regression
inputs: ERCOT 60→61, 61→62, 64→65, 66→67, 69→70, 71→72 (6 pairs × 3 years); PJM
pjm 4→5, 5→6, 6→7 (3 pairs × 2 years). Each year is fitted separately (the 2024 vs
2023/2025 asymmetry is gas-price-driven: $2.54 / $2.19 / $3.52 per MMBtu).

**Sanity anchors reproduced** (Run-72→73, structural — sign checks only, all PASS):
CT_PEAKER committed 1.30→1.10 lifted CT_PEAKER +1.62/+2.10/+1.35 TWh (2023/24/25) while
ST_GAS fell −1.75/−2.44/−2.02; COAL_PRB committed/econ_low −0.10 lifted PRB +0.74/+1.31
(2023/24) while COAL_LIGNITE fell −0.70/−0.88.

**Strongest cross-couplings (ERCOT, TWh per unit of multiplier, high/med confidence):**

| Knob | Responds | 2023 | 2024 | 2025 | Reading |
|---|---|---|---|---|---|
| CT_PEAKER.committed | CC_REGULAR | +5.8 | +5.0 | +3.8 | pricing the CT committed band up pushes its energy into the CC residual |
| CT_PEAKER.committed | COAL_PRB | −4.2 | −3.4 | (low) | dearer CTs raise prices into PRB's econ ramp window |
| CT_PEAKER.committed | CT_PEAKER | −2.6 | −2.7 | −2.8 | own-band loss, roughly half of what CC_REGULAR gains |
| CC_REGULAR.econ_high | CC_REGULAR | −3.8 | −3.1 | −2.4 | the big residual marginal class; its econ_high is the single strongest own-knob |
| CC_REGULAR.econ_high | COAL_PRB | +2.6 | +2.5 | (low) | CC econ_high and PRB econ_high overlap the same $23–35 price window |
| COAL_PRB.econ_high | COAL_PRB | −4.1 | −4.4 | (low) | own-band; 2024 strongest (cheapest gas year squeezes the coal window) |
| COAL_PRB.econ_high | CC_REGULAR | +4.4 | +3.7 | +2.3 | the PRB↔CC substitution is symmetric to the row above |
| COAL_PRB.econ_high | ST_GAS | +1.4 | +1.9 | (low) | second-order spill into steam gas |
| ST_GAS.committed | CT_PEAKER | −1.5 | −1.5 | −1.6 | cheaper ST_GAS committed crowds CTs out (and vice versa) |
| COAL_LIGNITE.econ_high | CT_PEAKER | (low) | −1.5 | (low) | lignite econ band trades against peakers in the tight 2024 stack |

PJM (3 pairs, 2023/24 — treat as provisional): CT_PEAKER econ bands are the dominant
knobs (econ_high −21, econ_low −11 TWh/unit own-class, med confidence), with COAL_BIT
committed ↔ CT_PEAKER the strongest cross (+16 TWh/unit, n=2).

**Caveats.** CT_PEAKER.committed and ST_GAS.committed co-moved identically in two of the
six ERCOT pairs, so their attributions are partially aliased — the Run-72→73 anchor
(where CT moved without ST_GAS committed) shows the CT committed knob's nearest
substitution partner is ST_GAS specifically; read the CT→CC_REGULAR row as "CT committed
energy goes to the gas mid-merit pool (CC_REGULAR + ST_GAS)". Cells flagged `low`
(n_obs<2 or |coef|<stderr) are not to be trusted individually. The merit-order adjacency
check (band $/MWh range = band mult × class base HR × monthly fuel price, vs the
demand-weighted clearing-price distribution in each bundle's `system.parquet`) confirms
every med/high regression coupling pairs classes whose offer bands overlap where the
price distribution has mass.

**Joint-move recipe.** Given a target error vector `err` (TWh per class-year, model −
EIA-923), the script solves `min ‖S·Δm + err‖² + λ‖Δm‖²` over the four price bands
(knobs with n_obs ≥ 2), box-constrained to per-step moves |Δm| ≤ 0.15, by projected
gradient. Worked example against Run-73's errors
(`python scripts/derive_offer_curve_jacobian.py --iso ERCOT --validate-run Run-73`):

```
Recommended Δmult            Predicted errors (TWh, model − EIA-923)
CC_REGULAR  econ_high −0.150            err now            err predicted
ST_GAS      econ_high −0.150            2023  2024  2025   2023  2024  2025
ST_GAS      committed −0.150  CC_REG   −5.95 +3.38 −3.52  −4.57 +4.44 −2.47
CT_PEAKER   committed +0.150  ST_GAS   −1.41 −3.53 −2.71  −0.65 −2.78 −2.00
CT_CHP      committed −0.150  CT_PEAK  +1.42 +0.82 +0.87  +1.30 +0.77 +0.72
CT_CHP      econ_high +0.150  PRB      +1.44 −5.47 +3.04  +0.86 −5.92 +2.94
CT_CHP      peak      −0.150  LIGNITE  −1.20 −2.99 +0.25  −1.26 −3.03 +0.24
COAL_LIGNITE econ_low +0.117  CT_CHP   −1.12 −0.72 +2.46  −1.14 −0.72 +2.34
COAL_PRB    econ_high −0.115
COAL_LIGNITE econ_high −0.104
```

The solver lifts the under-running classes (ST_GAS cheapened on both committed and
econ_high; CC_REGULAR econ_high down against the 2023/25 under-run) and trims the
CT_PEAKER over-run — but the mixed signs across years (CC_REGULAR −6.0/+3.4/−3.5,
PRB +1.4/−5.5/+3.0) are the honest limit of what any single multiplier move can fix:
those need year-dependent levers (gas-price-keyed shaping), not more band tuning.
Re-derive the matrix and recipe after each run; one solved joint move per iteration
replaces the sequential single-knob walk.
