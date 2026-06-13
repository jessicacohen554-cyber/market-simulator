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

### 2026-06-11 — CAISO — hydro energy budgets + pumped storage (data stage, multi-iso P4)

- **Benchmark:** EIA-923 monthly net generation 2023–2025; EIA-930 CISO
  hydro (cross-check); EIA-860 2025 ER generator schedule.
- **Scope:** data-stage verification + wiring, not a dispatch calibration
  run. The PJM hydro/PS machinery (2026-06-09 entry) is fully generic —
  `load_hydro_budget` / `_hydro_fleet` / `load_eia860_pumped_storage` work
  for CAISO unmodified; this stage verified the CAISO data through them and
  made the PS dispatch adder a per-ISO default.

**Hydro budgets (EIA-923 `HY`, BA = CISO):**

| Year | Plants | Budget (TWh) | EIA-930 CISO hydro (TWh) | Δ |
|---|---|---|---|---|
| 2023 | 166 | 23.90 | 24.40 (incl. PS net — pre-2024 schema doesn't split) | −2.0% |
| 2024 | 160 | 21.48 | ≈22.76 (12.51 Jan–Jun incl-PS + 10.25 Jul–Dec excl-PS) | −5.6% |
| 2025 | 26 | 12.32 (→ 20.39 backfilled) | 21.35 (excl-PS, full year) | −4.5% backfilled |

- Zones resolve cleanly: NP15 136 / SP15 24 / ZP26 6 plants (2023), no
  blanks; NP15 carries >70% of the 6.4 GW nameplate (Sierra/Cascade hydro
  north of Path 26).
- **Wet/dry swing:** the "~2x wet-vs-dry" expectation is 2022 (dry,
  ~12-13 TWh) vs 2023 (extreme wet) — 2022 is outside the data window. The
  measured 2023→2024 swing is +11.3% (23.90 vs 21.48), confirmed by EIA-930
  (~+7%); the budgets preserve it exactly since they *are* the EIA-923
  monthlies. Acceptance (±10% of EIA-923 for 2023/2024) holds by
  construction and is now pinned by `tests/test_hydro.py` regression
  anchors.
- **2025 coverage caveat:** the 2025 EIA-923 vintage is the early release
  (monthly-survey reporters only): 26 of ~185 CAISO plants, 12.3 of
  ~21.4 TWh. `load_hydro_budget(..., backfill_year=2024)` carries
  non-reporters in at their 2024 monthlies → 20.39 TWh (−4.5% vs EIA-930).
  The CAISO 2025 backcast should pass it (and drop it when the final
  annual file lands). Default off, so ERCOT/PJM runs are byte-identical.
- **Small vs large split — not warranted:** ≤30 MW (CAISO RPS small-hydro
  threshold) is 132 plants but only 0.90 GW (14% of capacity) and
  3.10/2.56 TWh (13.0%/11.9% of 2023/2024 energy). Plant-level budgets
  already individuate each small plant, and EIA-930 carries a single hydro
  series to calibrate against, so a structural class split adds nothing
  today. Min-flow floors stay available via `min_flow_fraction` (default 0,
  as PJM); `HydroBudget.monthly_min_energy` now clips the floor to the
  monthly budget so a nameplate-fraction floor can't render a low-inflow
  month infeasible (CAISO small hydro runs dry autumns at a few percent of
  nameplate-hours).

**Pumped storage (EIA-860 prime mover `PS`, BA = CISO):** 2,078 MW, all
NP15 — Helms 1,053 MW (3×351; PG&E rates the upgraded units ~1,212 MW —
EIA-860 nameplate is the model input), W. R. Gianelli 424, Edward C Hyatt
293, J S Eastwood 200, Thermalito 82, O'Neill 25. Fleet-average params per
the PJM pattern: 10 h duration (DOE PSH 2023 fact sheet), RTE 0.80
(DOE/Sandia ESHB).

- **PS dispatch adder is now a per-ISO default**
  (`PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO`): PJM keeps its calibrated
  $10/MWh reserve-duty proxy (2026-06-10 "pjm 3 ps-adder"); CAISO resolves
  to $0 until a CAISO calibration pass measures Helms' reserve/regulation
  duty. `ScenarioConfig.pumped_storage_dispatch_adder` default changed
  `10.0 → None` (= per-ISO); an explicit number still overrides every ISO.
  Note for the run-classifier: configs recorded before/after this change
  differ on this key (10.0 vs null) with identical PJM behavior.

**Open items:** CAISO calibration pass to set (or confirm zero) the CAISO
PS adder once the P-stage backcast runs; revisit the 2025 hydro backfill
when the final EIA-923 2025 annual file lands.

---

### 2026-06-11 — CAISO — P7 gas + carbon (structural, no full run)

- **Scope:** doc-06 pack P7 — measured monthly gas and CA cap-and-trade in
  CAISO marginal cost. Structural inputs only; no calibration bundle (P11
  runs the smoke backcast once the other Wave-1 packs land).
- **Model changes:** `gas_monthly_actuals` default-on for CAISO backcasts
  (`_calibration_config`); CARB allowance price in `resolve_carbon_price`
  via `STATE_CARBON_PRICE_BY_ISO` (default-on, `state_carbon_pricing`);
  border carbon adjustment on the CAISO import tranches
  (`wecc_border_carbon_adder` feeding `build_import_generators`, CARB
  unspecified EF 0.428 t/MWh).

**Findings (EIA-923 Schedule 5, CAISO plants, quantity-weighted):**

- Measured CAISO delivered-gas basis vs Henry Hub annual average:
  **+$7.06 (2023), +$2.26 (2024), +$1.12 (2025)** against the +1.20
  `GAS_BASIS_DIFFERENTIAL` seed. The seed is ~right for 2025, half the
  2024 reality, and misses 2023 entirely — Jan-2023 delivered gas was
  **$38.7/MMBtu** (Dec-22/Jan-23 western gas crisis) vs ~$4.5 shaped.
- Zonal split (the SoCal vs PG&E premium the per-plant path captures):
  implied annual basis NP15 +7.82 / SP15 +5.38 (2023), NP15 +2.20 /
  SP15 +2.42 (2024), NP15 +0.98 / SP15 +1.59 (2025). Caveat: only 6-7
  CAISO plants (~11-14% of gas burn) report Schedule-5 gas costs; the
  nearby-plant fallback fills the rest at the CA *state* mean (CA spans
  both hubs), so zonal price asymmetry reaches only the reporters
  themselves. The ISO-month volume-weighted series is robust to this.
- Carbon: a 7.0 HR CC carries ~$14/MWh of allowance cost at the 2024
  average CARB price ($35.23/t); the import border adder is ~$15/MWh
  (0.428 × allowance). Without these the CAISO price level cannot
  calibrate (doc-06 design decision 5).
- 168 h CAISO smoke (2024): solves Optimal, measured gas + carbon active
  (F923: 22 own-plant, 550 gap-filled generators), January-week average
  price $63.98/MWh, no slack. ERCOT/PJM regression: full test suite
  green; both ISOs resolve a zero carbon price and keep their gas paths.

---

## Cross-class offer-curve tuning Jacobian (2026-06-11)

**Tool:** `scripts/derive_offer_curve_jacobian.py` → `inputs/processed/offer_curve_jacobian.csv`
(long format: `iso, year, out_class, band, in_class, dTWh_per_unit_mult, n_obs, stderr, confidence`).
Pure parquet/JSON analysis of the existing calibration bundles — no LP re-solve. Re-run it
after every new backcast bundle lands; unknown runs are auto-classified (scenario-config
equality + git diff between recorded shas + note keywords) so it keeps working for every
ISO as tuning sequences accrue. (Complements `scripts/curve_class_jacobian.py`, the step-4
quick-look: that tool fits one pooled regression with year fixed effects across all
bundles; this one restricts to verified pure-curve pairs, fits each year separately,
attaches jackknife errors per cell, and adds the adjacency validation + joint-move solver.)

**Method.** From consecutive run pairs whose only difference is offer-curve band-multiplier
moves, collect observations Δ(band multipliers) → Δ(class TWh) per year and fit a
ridge-regularized linear map `Δgen[class] ≈ Σ S[class,(class2,band)]·Δmult[(class2,band)]`,
with leave-one-pair-out jackknife standard errors. Pairs with structural code/data changes
are excluded via a curated registry in the script: Run-63 (storage fix), Run-64 (ER plant
append), Run-66 (CHP BTM trim), Run-68 (measured PRB fuel), Run-69 (CC_CHP eGRID HR
re-base), Run-71 (demand alignment), Run-73 (CHP steam-floor + Petra Nova), Run-74
(regenerated unit-outage extract — config-identical to Run-73 but the note discloses the
data change, so 73→74 is excluded too). Regression inputs: ERCOT 60→61, 61→62, 64→65,
66→67, 69→70, 71→72 plus the two auto-admitted step-2 peak-sweep A/Bs
(peak145→130→160; single-knob CC_REGULAR.peak moves on identical configs) = 8 pairs ×
3 years; PJM pjm 4→5, 5→6, 6→7 (3 pairs × 2 years). Each year is fitted separately (the
2024 vs 2023/2025 asymmetry is gas-price-driven: $2.54 / $2.19 / $3.52 per MMBtu).

**Sanity anchors reproduced** (Run-72→73, structural — sign checks only, all PASS):
CT_PEAKER committed 1.30→1.10 lifted CT_PEAKER +1.62/+2.10/+1.35 TWh (2023/24/25) while
ST_GAS fell −1.75/−2.44/−2.02; COAL_PRB committed/econ_low −0.10 lifted PRB +0.74/+1.31
(2023/24) while COAL_LIGNITE fell −0.70/−0.88.

**Strongest cross-couplings (ERCOT, TWh per unit of multiplier, high/med confidence):**

| Knob | Responds | 2023 | 2024 | 2025 | Reading |
|---|---|---|---|---|---|
| CT_PEAKER.committed | CC_REGULAR | +5.8 | +5.1 | +3.8 | pricing the CT committed band up pushes its energy into the CC residual |
| CT_PEAKER.committed | COAL_PRB | −4.3 | −3.4 | (low) | dearer CTs raise prices into PRB's econ ramp window |
| CT_PEAKER.committed | CT_PEAKER | −2.6 | −2.7 | −2.8 | own-band loss, roughly half of what CC_REGULAR gains |
| CC_REGULAR.econ_high | CC_REGULAR | −3.8 | −3.1 | −2.4 | the big residual marginal class; its econ_high is the single strongest own-knob |
| CC_REGULAR.econ_high | COAL_PRB | +2.7 | +2.5 | (low) | CC econ_high and PRB econ_high overlap the same $23–35 price window |
| CC_REGULAR.peak | CC_REGULAR / COAL_PRB | (low) | −1.9 / +1.6 | (low) | from the step-2 duct-firing peak sweep; the peak band trades against PRB in 2024 |
| COAL_PRB.econ_high | COAL_PRB | −4.1 | −4.4 | (low) | own-band; 2024 strongest (cheapest gas year squeezes the coal window) |
| COAL_PRB.econ_high | CC_REGULAR | +4.4 | +3.7 | (low) | the PRB↔CC substitution is symmetric to the row above |
| COAL_PRB.econ_high | ST_GAS | +1.4 | +1.9 | (low) | second-order spill into steam gas |
| ST_GAS.committed | CT_PEAKER | −1.5 | −1.5 | −1.6 | cheaper ST_GAS committed crowds CTs out (and vice versa) |
| ST_GAS.econ_high | CC_REGULAR | −2.9 | −2.4 | −2.0 | aliased with the co-moved CC_REGULAR.econ_high (n=2) — treat with care |
| COAL_LIGNITE.econ_high | CT_PEAKER | (low) | −1.5 | (low) | lignite econ band trades against peakers in the tight 2024 stack |

PJM (3 pairs, 2023/24 — treat as provisional): CT_PEAKER econ bands are the dominant
knobs (econ_high −21, econ_low −11 TWh/unit own-class, med confidence), with COAL_BIT
committed ↔ CT_PEAKER the strongest cross (+16 TWh/unit, n=2).

**Caveats.** CT_PEAKER.committed and ST_GAS.committed co-moved identically in two of the
ERCOT pairs, so their attributions are partially aliased — the Run-72→73 anchor (where
CT moved without ST_GAS committed) shows the CT committed knob's nearest substitution
partner is ST_GAS specifically; read the CT→CC_REGULAR row as "CT committed energy goes
to the gas mid-merit pool (CC_REGULAR + ST_GAS)". Cells flagged `low` (n_obs<2 or
|coef|<stderr) are not to be trusted individually. The merit-order adjacency check (band
$/MWh range = band mult × class base HR × monthly fuel price, vs the demand-weighted
clearing-price distribution in each bundle's `system.parquet`) confirms every med/high
regression coupling pairs classes whose offer bands overlap where the price distribution
has mass.

**Joint-move recipe.** Given a target error vector `err` (TWh per class-year, model −
EIA-923), the script solves `min ‖S·Δm + err‖² + λ‖Δm‖²` over the four price bands
(knobs with n_obs ≥ 2), box-constrained to per-step moves |Δm| ≤ 0.15, by projected
gradient. Worked example against Run-74's errors
(`python scripts/derive_offer_curve_jacobian.py --iso ERCOT --validate-run Run-74`):

```
Recommended Δmult            Predicted errors (TWh, model − EIA-923)
CC_REGULAR  econ_high −0.150            err now            err predicted
CC_REGULAR  peak      +0.150            2023  2024  2025   2023  2024  2025
ST_GAS      committed −0.150  CC_REG   −6.01 +3.51 −3.19  −4.90 +4.19 −2.16
ST_GAS      econ_high −0.150  ST_GAS   −0.79 −2.83 −1.89  +0.12 −1.98 −0.97
CT_CHP      committed −0.150  CT_PEAK  +0.08 −1.03 −0.44  +0.27 −0.68 −0.30
CT_CHP      econ_high +0.150  PRB      +1.67 −5.14 +3.04  +1.28 −5.39 +3.04
CT_CHP      peak      −0.150  LIGNITE  −0.68 −2.36 +0.26  −0.57 −2.30 +0.27
CC_CHP      econ_high +0.150  CT_CHP   −1.12 −0.72 +2.48  −1.14 −0.72 +2.37
COAL_LIGNITE econ_high −0.150
COAL_PRB    econ_high −0.121
COAL_PRB    committed +0.082
CT_PEAKER   committed +0.069
```

The solver cheapens the under-running classes (ST_GAS on committed and econ_high;
CC_REGULAR econ_high against the 2023/25 under-run, with peak raised to give 2024 back)
and nudges CT_PEAKER committed up against the residual over-run — but the mixed signs
across years (CC_REGULAR −6.0/+3.5/−3.2, PRB +1.7/−5.1/+3.0) are the honest limit of
what any single multiplier move can fix: those need year-dependent levers
(gas-price-keyed shaping), not more band tuning. Re-derive the matrix and recipe after
each run; one solved joint move per iteration replaces the sequential single-knob walk.

---

## ERCOT E2 — storage realism + nuclear refuel overlay (2026-06-11)

**Scope (E2 backlog, doc 06 §6):** the LP over-cycled the ERCOT BESS fleet
("PS 9–10 TWh vs 3–4" in the audit shorthand; ERCOT has no pumped storage —
the resource is grid batteries) and coal/CT band tuning had absorbed part of
the error; nuclear ran with a refuel question mark. PJM untouched.

**New instrumentation (this session):** calibration bundles now persist
per-unit hourly storage charge/discharge (`storage.parquet`, P1/P2) and an
EIA-930 battery benchmark (`NG: BAT` discharge / `NG: UES` charge; NaN kept
over unreported hours), with a report §3d comparing the model over the
benchmark's reported window. ERCOT coverage: 2025 ≈ full year (5.44 TWh
discharge / 6.67 charge), 2024 ≈ 19% (Nov–Dec window, 0.72 TWh), 2023 none.
`meta.json` also records `highspy_version` (see finding 3).

**Runs** (P1, `--storage-daily-cycling`, Run-77 offer-curve deltas unless
noted; bundles `e2_1_storage_base`, `e2_2_adder20`, `e2_3_adder10`,
`e2_4_retune`; the last two are dashboard `run78 battery adder` /
`run79 storage retune`):

| | model dis TWh 2023/24/25 | vs measured |
|---|---|---|
| e2 1 adder $0 (baseline) | 1.90 / 4.72 / 8.09 | 2025 +48%, 2024 window +33% |
| e2 2 adder $20 | 0.22 / 0.37 / 3.03 | 2025 −44% (overcorrected) |
| e2 3 adder $10 | 1.05 / 1.35 / 5.34 | **2025 −2.0%**, 2024 window −52% |
| e2 4 = e2 3 + band re-tune | 0.99 / 1.40 / 5.36 | **2025 −1.5%** |

**Keeper: e2 4** — `battery_dispatch_adder = 10.0` $/MWh discharged (same
magnitude as the PJM pumped-storage adder; reduced-form cycling degradation +
ancillary-service opportunity cost) plus a Jacobian joint-move re-tune of the
non-CHP bands targeting e2 3's residuals (CHP knobs held per the Run-77
discipline): CC_REGULAR econ_high −0.15 / peak +0.15; COAL_PRB committed
+0.110 / econ_high +0.15 / peak +0.028; COAL_LIGNITE econ_low +0.15 /
econ_high −0.087; ST_GAS committed −0.15 / econ_high −0.15; CT_PEAKER
committed −0.094.

| vs EIA-923 incl. BTM (e2 4) | 2023 | 2024 | 2025 |
|---|---|---|---|
| CC_REGULAR | −1.3% | +2.9% | +0.9% |
| COAL_PRB | −0.8% | −9.9% | −1.5% |
| COAL_LIGNITE | −12.8% | −23.8% | +0.7% |
| CT_PEAKER | −2.6% | −12.8% | −2.9% |
| ST_GAS | +7.4% | −2.7% | +2.8% |
| nuclear | −0.7% | −0.7% | −0.7% |
| coal hourly Pearson r (NRMSE) | 0.940 (0.171) | 0.905 (0.229) | 0.808 (0.162) |
| battery discharge vs 930 window | n/a | −55% (19% cov.) | **−1.5%** |

**Findings:**

1. **The storage error was real and the bands were carrying it.** Killing the
   over-cycling alone (e2 1 → e2 3) recovered CT_PEAKER from −22/−43/−14% to
   −20/−36/−11 and ST_GAS similarly — the rest of the CT/ST deficit is not
   storage, it is the E1 winter/cheap-gas pricing item. With the re-tune on
   top, 2023 and 2025 land essentially everywhere in tolerance (lignite 2023
   excepted) while 2024 keeps the familiar cheap-gas coal deficit
   (PRB −9.9%, lignite −23.8%) that measured monthly gas (E1) owns.
2. **One adder cannot fit both 2024's shoulder window and 2025.** The $10
   value anchors the only full-coverage measured year (2025, −1.5%); the
   Nov–Dec 2024 window runs −55% partly because the model's year-end EIA-860
   fleet (8.1 GW) understates the actual late-2024 fleet and the window is
   shoulder-season (shallow spreads sit right at the adder threshold). A COD
   month intra-year fleet ramp (CAISO P5 pattern) is the structural fix if
   the window matters later.
3. **Reproducibility caveat (important for every future ERCOT pass):** the
   Run-77 config re-run in this session's environment did NOT reproduce
   Run-77's class splits (COAL_PRB 2023 +14% vs Run-77's ~+1%; totals equal
   to 0.01 TWh; duals ±$1 in the cheap-gas years, +$0.08 in 2025). Cheap gas
   puts PRB committed bids on top of gas committed bids — a near-degenerate
   plateau where alternate optimal vertices exist, and a different (then-
   unrecorded) HiGHS build picks a different one. `meta.json` now records
   `highspy_version` (this session: 1.14.0); the keeper's COAL_PRB committed
   +0.110 also lifts that bid off the tie, which should make the split less
   solver-sensitive going forward. Consider pinning `highspy` in
   `pyproject.toml` if cross-machine reproduction matters.
4. **Nuclear was already fixed and is now provably data-derived.** The
   per-year EIA-923 monthly-CF overlay (`NUCLEAR_MONTHLY_CF_BY_YEAR`, PR
   #252) holds nuclear at −0.7% in all three years (the audit's +2.4%
   predates it). New `scripts/derive_nuclear_monthly_cf.py --check`
   regenerates and validates the table from EIA-923 (ERCOT 2023–2025
   reproduce exactly); the residual −0.7% is the CF≤1.0 cap vs winter net
   capability above EIA-860 nameplate — accepted.

**Open items:** lignite 2023/2024 deficit and ST_GAS 2023 +7.4% (both
gas-price-keyed, → E1 measured monthly gas); CT_CHP 2025 +28% is the known
incomplete 2025 CHP benchmark, not a model change; storage intra-year fleet
ramp (finding 2) if the 2024 window becomes a target.

---

## ERCOT Runs 80–81 — coal tuning: lignite price sweep + PRB sigmoid probes (2026-06-11)

**Scope:** the run-79 lignite deficit (−12.8% / −23.8% / +0.7% vs EIA-923,
2023/24/25) and PRB 2024 (−9.9%). Five bundles: `run80a_code_baseline`,
`run80b_lignite_105`, `run80c_lignite_115`, `run80d_prb_floor_068`,
`run80e_prb_shaped`. Dashboard: `run80 lignite 1.15` = bundle
`run80c_lignite_115`; `run81 prb floor` = bundle `run80d_prb_floor_068`
(both registered as rejected probes; the config of record stays run 79's).
PRB sigmoid held at run-79 defaults in the lignite probes; lignite held at
the measured $1.45 in the sigmoid probes.

**Rebaseline (`run80a_code_baseline`).** The exact run-79 config re-run on
current main reproduces run 79's class table to the reported precision in
every class-year: the post-run-79 merges (E3 HSL loader unification,
curtailment report unification, CAISO/PJM-gated loader work) do not move
ERCOT P1 dispatch, and the solve reproduces under highspy 1.14.0 (the
run-77 caveat does not bite here). Not dashboard-registered (numerically
identical to run 79).

**Lignite price sweep (run 80, bundles 80b/80c) — reverted.** Mine-mouth lignite repriced
$1.45 → $1.05/$1.15 (marginal-extraction-cost framing; mine fixed costs
sunk under take-or-pay):

| lignite vs EIA-923 | 2023 | 2024 | 2025 |
|---|---|---|---|
| $1.45 (run79/80a) | −12.8% | −23.8% | +0.7% |
| $1.15 (80c) | +1.9% | −10.6% | +2.2% |
| $1.05 (80b) | +6.2% | −5.0% | +2.2% |

No single price fits both cheap-gas years (the 2023↔2024 trade is
year-keyed), and the cheap-lignite probes bleed PRB (2024 −9.9 →
−11.3/−11.8) and CT_PEAKER share. Decision: keep lignite at the measured
$1.45 — it is grounded in operator/EIA cost data. (Hourly coal NRMSE did
improve under the reprice — 2024 0.229 → 0.202 — recorded for any future
revisit.)

**PRB sigmoid probes (run 81, bundles 80d/80e) — negative result, parameters stay.**
80d cut the cheap-gas floors one step (baseload 0.78 → 0.68, follower
0.68 → 0.58): the gradient is strong (~+4.4 TWh PRB per −0.10 floor in
each cheap-gas year) and 2024/2025 land at +0.1%/0.0%, but 2023 overshoots
−0.8 → +9.0% and the gain displaces CT_PEAKER (2024 −12.8 → −19.4) and
ST_GAS (−2.7 → −8.3) rather than only CC_REGULAR's over-run — net all-class
error worsens in 2023 and 2024. 80e reshaped the logistic
(floor 0.68 / ceil 1.42 / mid 2.65 / slope 3.6, via the new
`--prb-gas-mid`/`--prb-gas-slope` flags) to hold 2023/2025 at run-79
passthrough while keeping 80d's 2024 discount; it failed (PRB 2023 +10.8%)
for a structural reason: **2023's cheap months (gas $2.29–2.45) overlap
2024's range, so no gas-keyed curve can discount 2024 without discounting
a third of 2023.** Annual-average anchors do not hold in monthly space.

**Finding — the PRB residual is two plants, not the curve.** Per-plant
(model − CAMPD, GWh): W A Parish −2064/−3858/−2456 and J K Spruce
−1289/−1728/−1253 under-run in *all* years including dear-gas 2025, masked
at class level by Martin Lake / Sandy Creek / Limestone overshoots. The 80d
floor cut reached the wrong plants (Martin Lake +209 → +1705 in 2023) and
left Parish at −2847 in 2024. Parish (15% MR) and Spruce (12% MR) carry the
lowest must-run floors in `COAL_MUSTRUN_BY_PLANT`; Parish is additionally
the mixed gas/coal facility where coal outages are CAMPD-undetectable.

**Open items:** per-plant Parish/Spruce correction (must-run floors or a
`--plant-tranche-config` sheet row) is the right next coal lever — the
fleet-wide sigmoid is the wrong altitude; lignite 2023/24 and the
remaining 2024 coal deficit stay with E1 (measured monthly gas,
`--gas-monthly-actuals` is now wired); CT_CHP 2025 +28% unchanged
(incomplete 2025 CHP benchmark).

---

## ERCOT Run 82 — Jacobian joint move; BTM-aware CHP panel (2026-06-11)

**Run 82 (`run82_jacobian_joint`, dashboard `run82 jacobian joint`) —
rejected.** The derive_offer_curve_jacobian recipe vs the run-79 error
vector (non-CHP knobs, |Δ| ≤ 0.15) predicted total |err| 28.5 → 25.4 TWh.
Actual: PRB 2023 0.0%, CC_REGULAR 2024/25 and ST_GAS 2023 improve — but
CT_PEAKER explodes to +20.9/+14.2/+21.0% (was −2.6/−12.8/−2.9). Cause: the
recipe's CT_PEAKER committed −0.132 stacked on run-79's −0.34 (cumulative
−0.47 below the calibrated default, mult 1.14 → 0.67) crossed a merit-order
step far outside the regime the matrix sampled. The keeper stays the run-79
config. **Lesson: the Jacobian solves annual class TWh only (no hourly
shape), and its linearization fails when a recipe move stacks onto a knob
already far from the sampled neighborhood — cap cumulative moves and
re-derive locally first.**

**BTM-aware per-plant CHP panel (reporting fix).** The [7]/[7b] per-plant
fit compared grid-facing LP dispatch against whole-plant CAMPD net — for
CHP plants the 35–50% behind-the-meter host-supply share made high CF bands
unreachable by construction (the fleet-wide "CC_CHP has 0 hours above 0.8
CF" read was substantially this artifact). `_plant_hourly_fit` now adds the
flat BTM MW back in hours the grid share runs (Petra Nova excluded — own
parasitic treatment). Honest residuals after the fix (run80a bundle panels
regenerated):

* **CC_CHP**: band overlap improves (Deer Park 0.50 → 0.68, Baytown
  0.48 → 0.62); remaining miss is the model being too *binary* — it
  under-occupies CAMPD's 0.2–0.5 CF range (partial-train operation below
  the modeled must-run floor) and over-occupies 0.9–1.0.
* **CT_CHP**: the original diagnosis survives the fix — CAMPD spends 25%
  of hours above 0.8 CF, the model 1.7%; the model parks at 0.6–0.8. The
  top ~20% of CT_CHP capacity is priced out (econ_high/peak mults plus the
  P1 startup markup, which CHP bins currently pay despite steam-host
  obligations covering their starts).

**Next (run 83 candidates):** exempt CHP classes from the startup
amortization markup (steam host keeps units hot — model bug, not a tuning
knob); then re-read the CT_CHP top bands and CC_CHP partial-train range
against the BTM-aware panel before any tranche-share (pct_peaking) move.

---

## ERCOT Run 83 — CHP startup exemption: no-op, mechanism ruled out (2026-06-11)

**Run 83 (`run83_chp_startup`, dashboard `run83 chp startup`).**
`chp_startup_covered` (CC_CHP/CT_CHP/ST_CHP exempt from the P1 startup
markup) reproduces run 79 exactly in every class-year. Root cause of the
no-op: the bin builder assigns startup cost to the **committed tranche
only** (econ/peak tranches carry 0.0), and CHP committed tranches run
continuously on their must-run floors, so their monthly amortization was
already ~$0/MWh. **Finding: startup cost is ruled out as the cause of the
CT_CHP top-band miss** (BTM-aware panel: CAMPD 25% of hours above 0.8 CF
vs model 1.7%); the miss is the CT_CHP band economics (econ_high 1.30 /
peak 1.32 on high CT heat rates) and/or tranche shares (pct_econ 32 /
pct_peak 5) — a CHP offer-curve/tranche item for the next pass. The flag
stays available (harmless, default off, correctly recorded in run_config
since the prb_overrides recording fix). Keeper remains the run-79 config.

---

## ERCOT Run 84 — coal sigmoids: lignite passthrough + PRB floor retune (2026-06-12)

**Run 84 (`run84_coal_sigmoids`, dashboard `run84 coal sigmoids`) —
rejected, but the lignite mechanism works.** One run, two coal moves on
the run-79 keeper config:

* **(A1) Gas-keyed lignite passthrough sigmoid** (new
  `--coal-lignite-sigmoid`; floor 0.70, ceil 1.00, mid 2.85, slope 2.5 —
  defaults derived from the run-80 flat-reprice anchors: $1.15 ≈ pt 0.79
  fixed 2023, $1.05 ≈ 0.72 fixed 2024, 2025 wants full cost). Mine-mouth
  take-or-pay fixed costs are sunk, so the BID discounts in cheap-gas
  months; the measured $1.45/MMBtu delivered-cost constant is untouched.
  Implementation mirrors the PRB/bit sigmoids end to end
  (`coal_lignite_passthrough_*` in ScenarioConfig,
  `lignite_passthrough_series`, a lignite route in
  `campd_tranche_fuel_frac`; must-run tranches stay VOM-only).
* **(A2) PRB sigmoid floor −0.05** (baseload 0.78 → 0.73, follower
  0.68 → 0.63) — half the run-81 floor gradient (+9.8/+10.0/+1.5 PRB
  points per −0.10), aiming to spread PRB error across years.

**Result vs keeper (2023/24/25):** lignite −12.8/−23.8/+0.7 →
**+5.4/−5.0/+2.1** (balanced, all within ±6 — the sigmoid does what the
flat reprices couldn't, holding 2025 at full cost); PRB −0.8/−9.9/−1.5 →
+1.9/−7.3/−0.9; Martin Lake/Limestone land +0.5/+0.2 TWh over CAMPD (not
the run-81 blow-up); Parish/Spruce structural deficit unchanged (out of
scope). **Rejected on gas collateral:** the cheap 2024 coal eats the gas
classes — CT_PEAKER 2024 −12.8 → −18.6, ST_GAS 2024 −2.7 → −7.2, both
beyond the ~2-point bar. Keeper stays run 79.

**Next:** soften the 2024 discount — lignite floor ~0.75–0.78 and/or the
PRB floor scale nearer 0.4 (floors 0.74/0.64) — and re-read the
CT_PEAKER/ST_GAS columns. (Run 83's `--chp-startup-covered` was a no-op —
see its entry above — so there is nothing to fold into a run-85 candidate
from that probe.) Per-supply sigmoid note (2026-06-12): every coal supply tag now
carries its own independently tunable sigmoid family — PRB
(+follower tier), bituminous, lignite, and a new subbituminous split
(`--coal-sub-sigmoid`, default = inherit PRB exactly as before) — since
each encodes basin/type/transport-specific contract economics.

## Jacobian tool v2 — dispatch-shape + LMP objectives, trust region (2026-06-12)

`scripts/derive_offer_curve_jacobian.py` now regresses three error blocks
per pure pair instead of annual TWh alone:

* **twh** — annual class TWh (unchanged, BTM-aware);
* **shape** — hourly NRMSE of non-CHP gas and coal vs EIA-930 (the [5]
  table convention) plus the mean panel-plant CF-band EMD from
  `plant_cf_bands.parquet`;
* **lmp** — demand-weighted monthly |model − actual RT| from
  `system.parquet` vs the committed `actual_lmp.json` reference.

The joint-move recipe minimizes a weighted sum (`--w-twh/--w-shape/
--w-lmp`, each block normalized to its `--baseline` magnitude, default
run-79) and prints the predicted change PER BLOCK, so a TWh fix that
degrades shape or LMP is visible before any LP solve. A **trust region**
zeroes any knob whose post-move resolved multiplier would exit the value
range actually sampled by the pure pairs (with a "re-derive locally first"
warning) — the run-82 failure mode. Back-test
(`--backtest e2_4_retune run82_jacobian_joint`): the trust region flags
the CT_PEAKER committed move (post-move 1.008 vs sampled [1.140, 1.480]),
and the twh block underpredicts its actual effect (+1.1 vs +2.2 TWh 2024)
— exactly the extrapolation nonlinearity the region guards against.
`inputs/processed/offer_curve_jacobian.csv` is schema v2 (new `metric`
column; `metric == "twh"` reproduces v1). Registry additions classify the
e2/run80/run82 chain (run80b–e as sidecars off run80a — 80d/80e
run_configs predate the sigmoid-provenance fix and must not be trusted for
sigmoid params); config-presence diffs with inert defaults no longer
downgrade pure pairs. Shape/LMP sensitivity cells start data-poor
(historical pairs moved knobs for TWh reasons) and carry the existing
n_obs/stderr confidence flags; expect the LMP block to act as a guardrail
rather than a driver.

---

## NEISO 1 — smoke backcast 2024 (P11, structural-checklist pass) (2026-06-12)

**Run `neiso_smoke_2024`, dashboard `neiso 1 smoke`** — the first NEISO
full-bundle backcast. `run_calibration.py --iso NEISO --year 2024` (fast P1
fuel-mix smoke) then `run_calibration_full.py --iso NEISO --year 2024
--commitment --out-dir results/calibration/neiso_smoke_2024` (P1+P2). All
NEISO structural toggles fire by default in the calibration harness
(`_calibration_config`): `gas_monthly_actuals`, the Algonquin `gas_hub_basis_overlay`,
`dual_fuel_switching`, and RGGI via the state-carbon program (carbon_price=0
→ resolve_carbon_price). Solve logs confirm them live: *254 dual-fuel gas
tranches (6068 MW) capped at the delivered oil price; 20 plants priced from
own F923 + 286 nearby-gap-filled.* **Prereqs:** P0–P9, P13, P2 merged; **P10
held on the LMP upload — no `actual_lmp.json` NEISO block, so the price
benchmark is level-only this pass (modeled level reported, not scored).**
This is a structural-discipline pass (playbook §6): **no offer-band tuning** —
a structural row is red and is filed, not tuned.

### Headline numbers (P2, full bundle)

| Metric | Model | EIA-923 | EIA-930 | Read |
|---|---|---|---|---|
| gas (TWh) | 67.81 | 60.99 | 59.64 | **+11.2% vs 923 — the import wedge** |
| nuclear | 26.48 | 26.55 | 26.41 | ✓ −0.3% |
| hydro | 6.67 | 6.71 | 7.39 | ✓ vs 923 (−9.7% vs 930) |
| wind | 3.45 | — | 3.45 | ✓ (judged vs 930) |
| solar | 1.31 | (4.53) | 1.31 | ✓ vs 930; 923 carries BTM PV — basis artifact, not a miss |
| oil | 0.24 | 0.31 | 0.37 | order-of-magnitude OK; **summer-peaker-weighted, under-burns winter** |
| biomass | 5.16 | — | (eGRID 5.53) | ✓ must-run injection |
| coal | 0.00 | 0.25 | 0.24 | lone Merrimack unit never dispatches (trace) |
| net interchange (TWh) | **0.00** | — | **−10.30** | **RED — wedge entirely unserved** |
| avg price ($/MWh) | 69.99 | — (P10 held) | — | biased high by unserved imports; duration max $292 / p90 $134 / p50 $46 |
| CO2 (Mt) | ~31.5 | eGRID-2023 25.1 | — | downstream of gas; +year-mismatch (eGRID is 2023, gas 53 TWh) |
| PS throughput (TWh) | 1.35 | — | 0.30 | **over-cycles 4.5×** |

### Ranked gap list (structural-checklist order; hypotheses + owning pack)

1. **[RED · demand→interchange] Net interchange is not served on the default
   backcast path.** `load_demand` nets the measured interchange schedule only
   for ERCOT and PJM (`pjm_net_interchange`); NEISO falls through with
   `interchange = 0`, so the LP serves the full 114.5 TWh of metered demand
   internally. ISO-NE is a steady net importer of **−10.30 TWh (−1175 MW avg,
   9% of demand)** — the HQ Phase II + NB + NYISO wedge — and that wedge is
   instead generated by **gas (+6.8 TWh, +11% vs 923)**. The report's [2] line
   reads `model 0.00 TWh (energy-only; no external interchange node)` against
   `actual −10.30 TWh`. Two confirming experiments bracket the truth:
   the default path serves **0** imports (gas +11%, price $70); a
   `--priced-interchange` diagnostic (`neiso_smoke_2024_priced_ix`, not a
   keeper) **over-imports −23.51 TWh** (100% of hours vs actual 83.8%) because
   the HQ tranche ($18/MWh) undercuts gas in nearly every hour, dropping gas to
   45.0 TWh (−26%), oil to 0, and price to $48. Serving the *measured* −10.3
   TWh schedule sits between and lands gas ≈ 60.3 TWh — right on the EIA-923
   60.99. **Hypothesis:** wiring the measured ISNE net-interchange into demand
   (subtract the −10.3 TWh schedule) closes the gas overshoot and pulls the
   price level down toward reality; the priced node remains the *forward*
   mechanism and is validated separately. The offline priced-node fit RMSE is
   already **266 MW** (optimal placement), vs 1563 MW live — so the tranche
   *capacities* fit; the live miss is tranche *price levels* relative to the
   modeled gas, i.e. a calibration item, not a structural one.
   **Owner: P9** (wire `neiso_net_interchange` into `load_demand`, PJM
   precedent; or calibrate the priced-node tranche prices and run NEISO
   backcasts with `--priced-interchange`). **This blocks everything below —
   do not tune offer bands until it is fixed.**

2. **[AMBER · hydro/PS/storage] Pumped storage over-cycles 4.5×.** Northfield +
   Bear Swamp discharge **1.35 TWh modeled vs 0.30 TWh EIA-930** — pure
   price-arbitrage over-cycling, the documented PS failure mode (playbook
   §8.4). Grid batteries also over-cycle (0.27 vs ~0.01 TWh; evening-discharge
   share 86% vs 30%) but the fleet is small. **Note the cross-coupling:** under
   `--priced-interchange` PS self-corrects to exactly 0.30 TWh — cheap imports
   remove the arbitrage spread, so part of gap #2 is a *symptom* of gap #1.
   **Hypothesis:** re-measure PS/BESS throughput after interchange is served;
   if still high, apply the `battery_dispatch_adder` / PS throughput cost
   (default 0 today). **Owner: P4 (PS) / P5 (BESS), after P9.**

3. **[AMBER · gas+AGT+RGGI → dual-fuel/oil] Oil holds at magnitude but is
   season-shifted.** Modeled oil **0.24 TWh** at full-bundle scale — exactly
   P13's 2023 figure (0.24 vs 0.39) and the task's confirm-it-holds check:
   **it holds — not near-zero**, vs EIA-923 0.31 / EIA-930 0.37 (2024). But the
   monthly shape is wrong: oil burns **Jul 148 / Aug 35 / Jun 23 GWh (summer
   peaker scarcity) vs only Jan 17 / Feb 11 / Dec 5 GWh (winter)**. ISO-NE's
   real oil is winter-cold-snap-concentrated. Root cause is the **documented
   P13 limitation**: the committed AGT basis is *monthly*, and monthly averages
   never reach distillate parity (~$18/MMBtu; max Jan-2025 $16.9), so the
   dual-fuel CT/ST switch is wired but does not trip on monthly data — winter
   oil comes only from oil-steam scarcity dispatch. A winter price tail *does*
   exist (duration max $292, p90 $134) but is under-fed on the oil side.
   **Hypothesis:** a daily-AGT basis (upload U4 refinement) would trip the CT
   switch in cold snaps and move oil from summer to winter. **Owner: P7/P13
   (daily AGT basis, U4).** Not blocking the smoke; magnitude is acceptable.

4. **[INFO · price level/duration] Cannot be scored — P10 held.** No NEISO
   `actual_lmp.json` block, so the modeled level ($69.99 default; $48.19 with
   priced imports) is reported, not benchmarked. All five zones price
   identically ($69.99) — **no Boston/CT congestion separation**: the Tier-3
   RSP TTC seeds are non-binding and there are no measured interface limits
   (U6). The $70 default level is biased high by gap #1. **Owner: P10 (U2 LMP
   upload for the level/duration benchmark; U6 for TTC/congestion).**

5. **[INFO · trace] Coal 0.00 vs 0.25 TWh.** The single ~108 MW Merrimack-area
   coal unit never clears; trace, no action.

### Keeper decision

`neiso 1 smoke` registered as the NEISO baseline (first run; top-5 retention
not yet engaged). **Not a calibration keeper for tuning** — gap #1
(interchange) is a structural blocker that must be fixed in P9 before any
offer-band / hydro / gas-basis knob is moved in P12. The fast-P1 smoke and the
P2 bundle agree on the diagnosis; the `--priced-interchange` diagnostic bundle
(`neiso_smoke_2024_priced_ix`) is retained on disk as the bracketing evidence
for gap #1 (not registered — it is a confirmation, not a numbered run).

---

## NYISO P11 — Smoke backcast 2023: structural gap report (2026-06-12)

First NYISO calibration pass (playbook §6 smoke). Year **2023** (full CEMS;
2024 blocked on `NY_2024`, upload U1). Prereqs P0–P9 + P13 merged; **P10 held
on the LMP upload (U2)** — price calibration is **level-only** this pass (no
actual-LBMP duration / zonal-spread comparison). Bundles:
`results/calibration/nyiso_smoke_2023` (dashboard `nyiso p11 smoke 2023`) and
the diagnostic `nyiso_smoke_2023_priced` (dashboard `nyiso p11 diag
priced-interchange`). Per-run detail in
`results/calibration/nyiso_smoke_2023/SUMMARY-nyiso-p11-smoke.md`.

**Headline — one structural miss, not a band problem.** The energy-only
backcast over-generates **+16% on total** (147.31 vs 126.96 TWh EIA-923),
*entirely* in gas (80.11 vs 63.79 TWh, +25.6%). NYISO is a ~16%-of-load net
importer (actual net interchange **−23.45 TWh**, EIA-930) and the default
backcast serves **0 TWh** of imports — `_load_nyiso_hourly_demand` deliberately
does not fold interchange into demand (defers to the priced node, §8.2), and the
priced node only builds under `--priced-interchange`. So the ~24 TWh import
wedge is displaced onto in-state gas. Hydro (−0.1%), nuclear (−0.1%), wind
(−3.6%) are dead-on. **No offer band was tuned** (playbook discipline:
structural rows red).

**Confirmation (`--priced-interchange`).** The P9 node (5 tranches / 5900 MW)
reclaims the whole wedge with no band change: gas 80.11 → **55.51 TWh** (−13%
vs 923), net interchange 0 → **−25.41 TWh** (vs −23.45 actual; import-hours
100% match, diurnal corr +0.80, duration RMSE 442 MW), total 147.31 → 121.75
TWh, avg price $71 → $40/MWh. The energy-only gas_ct +81% / gas_st +113% /
CO2 +57% reads are interchange symptoms.

**Ranked gap list (structural-checklist order; owning pack per fix):**

| # | Row | Status | Finding | Owner |
|---|---|---|---|---|
| 1 | demand / net-load | 🟢 | served = demand 147.05 TWh; FoM convention correct; zonal shares Tier-3 Gold-Book static (U3 not uploaded) | P8 (U3) |
| 2 | **net interchange** | 🔴 dominant | serves 0 vs −23.45 TWh; ~24 TWh dumped on gas; priced node closes it | **P9** |
| 3 | hydro + storage | 🟢 | hydro 28.38/28.40, budget honored; nuclear −0.1%; PS/BESS plausible but unbenchmarked (no EIA-930 BAT/PS column) | — (P5 data gap) |
| 4 | gas + RGGI level | 🟡 | RGGI $13.49/t active; gas on flat HH $2.54 seed (`--gas-monthly-actuals` off, U4 basis absent); level unvalidatable (P10 held) | **P7** |
| 5 | dual-fuel / outages | 🔴 | dual-fuel active (385 tranches/15.9 GW) but oil 0.15→0.00 vs 0.42 (923)/2.17 (930) — flat gas never crosses oil parity; outage overlay healthy (318 derated) | **P13 + P7** (U4) |
| 6 | offer-curve bands | ⏸️ not tuned | rows 2/4/5 red → untouched; gas_ct/gas_st collapse to tolerance once imports served | P2/P12 |

**NYISO watch items:** hydro displacement 🟢 (lands at budget); downstate
congestion separation ⚪ not validated (modeled spread ~$0.5–1.5; P10/U2 held —
cannot compare J−A/K−A LBMP; interface TTCs may need U7); winter dual-fuel 🔴
(gated on U4 winter basis; Jan/Feb actual oil ~365/~454 GWh).

**Next (in order):** (1) P9 serve interchange in NYISO backcasts — default-on
priced node or fold the measured EIA-930 schedule into demand (PJM precedent),
then refine the low-import tail / ~8% over-import; (2) P7 enable
`--gas-monthly-actuals` + U4 winter basis; (3) P13 re-validate winter oil once
U4 lands; (4) P10/U2 + P8/U3 uploads for price/separation/zonal load; (5) only
then (P12) offer-curve bands. Keeper config: none yet — P11 is the structural
diagnosis, not a tuning pass.


## ERCOT Runs 85–87 — coal–gas split + LMP localization (2026-06-12)

**Scope.** Resolve the run-84 finding that any coal bid discount adds coal TWh
by taking them from the wrong gas classes (CT_PEAKER/ST_GAS, already short),
not CC_REGULAR's surplus — three combos (85/86/87) — plus an hourly LMP
residual diagnosis (the 2023 price level is ~$24 modelled vs ~$48 actual).
All three runs rejected; the keeper stays run 79 (`e2_4_retune`). Dashboard:
`run85 coal soft`, `run86 coal gas realloc`, `run87 gas monthly`
(85→prunes run80, 86→run81, 87→run82, top-5 retention).

**New data artifact — ERCOT hourly actual LMP.** `scripts/derive_actual_lmp.py`
now emits `inputs/calibration/actual_lmp_hourly_ERCOT.parquet` (the HB_HUBAVG
hub-average, DAM hourly + RTM 15-min averaged to the hour, on the model's
fixed non-leap 8760 calendar — Feb 29 dropped, DST fall-back averaged via the
repeated-hour rows, spring-forward NaN). The annual/monthly mean formulas are
untouched so `actual_lmp.json` does not drift (verified by diff); ERCOT gains
`da_pct`/`rt_pct` like PJM/CAISO. This unblocks `scripts/analyze_lmp_residual.py`
for ERCOT.

### Run 85 — softer coal dose (REJECTED, dose-response anchor)
Run-79 config + `--coal-lignite-sigmoid --lignite-floor 0.75 --lignite-ceil
1.00 --prb-floor 0.74 --prb-follower-floor 0.64` (about half the run-84
discount). Lignite recovers to **+2.3/-8.8/+1.9** (keeper -12.8/-23.8/+0.7;
run84 +5.4/-5.0/+2.1) — 2024 did not slide past -10 — and the hourly coal/gas
dispatch shape *improves* (coal NRMSE 0.171/0.229 → 0.151/0.198). But the 2024
gas collateral fails the bar: **CT_PEAKER -17.9** (keeper -12.8), **ST_GAS
-6.5** (keeper -2.7), barely better than run-84's -18.6/-7.2 despite half the
dose. 2024 ledger: coal +2.95 TWh (lignite +2.10, PRB +0.85) taken from
CC_REGULAR -1.14 **and** ST_GAS -0.70 / CT_PEAKER -0.42 — the donor mix is
unchanged from run 84, confirming the discounted coal clears against the
already-short peakers/steamers adjacent in the merit order, not CC_REGULAR's
surplus alone. Plant guard clean (Martin Lake 2025 +1.35, no run-81 blow-up).
LMP MAE 31.0/9.1/11.6 vs keeper 30.9/8.9/11.7 — within the ±$1 gate.
**Verdict: no pure-coal dose exists; the collateral scales with the discount.**

### Run 86 — run85 coal + Jacobian gas counter-move (REJECTED)
Derived the joint-move recipe (jacobian v2, `--validate-run run85_coal_soft`)
against run-85's residual. The trust region **froze the entire gas-side
counter-move**: run-79's CC_REGULAR/CT_PEAKER/ST_GAS curves already sit at the
edges of every range sampled by the historical pure pairs, so every move the
optimizer wants exits the region (the run-82 extrapolation lesson, now
enforced). The tool had additionally downgraded run-82's pure pair on an inert
`coal_bit_passthrough_*` provenance diff, narrowing CT_PEAKER.committed to
[1.140, 1.480]; force-including it (`--include-pair run82_jacobian_joint`,
restoring the [1.008, 1.480] the matrix should sample) unfroze exactly one
gas-class knob: **CC_REGULAR peak +0.132** (2.500 → 2.632). CT_PEAKER/ST_GAS
committed refills stayed frozen *and* unrecommended (Δ < 0.005) — the
hypothesised "CT_PEAKER/ST_GAS refill" move is not what the data supports.
Recipe per-block prediction (sidecar verbatim): **twh improves 1.49 → 1.43 but
shape DEGRADES 0.134 → 0.136 and lmp DEGRADES 19.850 → 19.851**. Ran run-85's
coal config + CC_REGULAR peak 0.382. Actual: the peak move barely moves
anything — CT_PEAKER 2024 -17.9 → **-16.6** (still fails the bar vs keeper
-12.8), coal and CC_REGULAR/ST_GAS ≈ run 85; LMP MAE 31.0/9.1/11.7 (within the
±$1 gate), shape ≈ flat (the predicted degradation was negligible). 2024
ledger: CC_REGULAR -1.33 / ST_GAS -0.68 / CT_PEAKER -0.31 gave — the donor mix
is run-85's. **The coal-gas split has no offer-curve gas reallocation within
the trusted region.**

### Run 87 — measured monthly gas (REJECTED, mechanism probe for split + LMP)
Run-79 config + `--gas-monthly-actuals`, no coal flags. ERCOT monthly gas
exists (`fuel.iso_monthly_gas_prices`, 12/12 months all years; 2024 Apr $1.64,
Aug $2.29 genuinely cheap). **(1) Coal-gas split — OVER-corrects.** Measured
gas fixes the 2024 coal deficit (lignite -23.8→+1.2, PRB -9.9→+10.8) but
overshoots (PRB +8.3/+10.8/+1.3) and worsens the gas classes *harder* than the
coal sigmoids did: CT_PEAKER 2024 **-23.1** (keeper -12.8), ST_GAS 2024
**-12.7** (keeper -2.7). 2024 ledger: coal +12.5 TWh, gas -9.7 (CC_REGULAR is
now the largest donor at -6.78, the "right" one, but the move is so large
CT_PEAKER/ST_GAS still bleed in absolute TWh). Martin Lake trips the plant
guard (+1.42/+1.97/+1.51 vs CAMPD). The structural answer is **not** simply the
gas path — the merit-order adjacency problem persists and measured gas
amplifies it. **(2) LMP — confirms the scarcity diagnosis (see below).** 2023
MAE improves 30.9→28.5 (the expensive winter months lift the level) but 2025
MAE degrades 11.7→**17.5** (2025's dear gas over-prices), so it is not a free
LMP win; and the 2023 summer >=$200 scarcity tail still carries ~100% of the
residual while the mid-curve now slightly OVER-prices — exactly the signature
of a scarcity miss, not a fuel-level miss.

### (D) LMP residual localization — the 2023 miss is scarcity, not fuel
`analyze_lmp_residual.py` on the keeper, 2023 Jun–Sep: model **$27.1** vs
actual RT **$96.1** (residual -69.0). The gap is overwhelmingly in the tail:
**89% of the summer $·h gap sits in the actual >=$200 band** (157 hours, actual
mean $1,212 vs model $61); the model clears **0 hours >$500** vs 99 actual, and
5 vs 157 hours >$200. The mid-curve tracks well (full-year p50 residual +0.20;
actual-price bands below $50 within a few $/MWh). By hour-of-day the gap is the
afternoon/evening scarcity window (hours 14–20, peak hour 19 residual -456); by
month it is Aug (-160) / Sep (-61) / Jun (-37). **Read: missing ORDC-style
reserve-scarcity pricing — a MODEL mechanism, scoped as the run-88+ follow-up,
NOT bolted on this session.** Run 87 is the live test of the alternative
(broad fuel offset) branch and rules it out: raising the fuel level
over-corrects the 2023 mid-curve while leaving the scarcity tail miss intact.
Monthly LMP MAE ($/MWh, demand-weighted |model − actual RT|), keeper / 85 / 86
/ 87: 2023 30.9 / 31.0 / 31.0 / 28.5; 2024 8.9 / 9.1 / 9.1 / 9.8; 2025 11.7 /
11.6 / 11.7 / 17.5. The coal runs (85/86) hold the ±$1 gate every year; only
run 87 moves the level materially (2023 better, 2025 worse).

**Keeper decision (revised 2026-06-12).** **Run 85 is promoted to keeper,
superseding run 79** — judged on the size-aware volume bar (≥20 TWh classes on
±5%, <20 TWh on ±1 TWh absolute), run 85 has 4 in-scope fails vs run 79's 5,
cuts total class volume error 24.0 → 20.9 TWh, fixes the worst class (lignite),
improves hourly coal NRMSE, and holds the LMP gate. The flat-percentage "no
class worse by >2 pts" guard had rejected it on a −5 pt CT_PEAKER move that is
only +0.4 TWh on an 8-TWh class — the distortion the size-aware bar removes.
Runs 86 and 87 stay rejected. The one honest caveat on run 85: CT_PEAKER/ST_GAS
are low in the *wrong direction* (EIA says both should run more), but the gap is
now a single 2024 cheap-gas cluster (~1 TWh each, all marginal) — in 2024
CC_REGULAR sits +3.1 TWh too high while coal/peakers/steamers each sit ~1 TWh
too low. The coal-gas split still has no *fleet-wide* offer-curve / fuel fix
(measured gas (87) over-corrects; the Jacobian gas counter-move (86) is
trust-region-frozen because run-79's gas curves sit at the sampled-range
edges); the live levers for the 2024 cluster are the **CC_REGULAR econ-ramp
shape** (`offer_curve_smoothing_mid`, a built-but-unused lever) and the **PRB
sigmoid** retune, with the per-plant Parish/Spruce correction (run-81 finding)
and the ORDC scarcity adder for the 2023 LMP level (run-88+) as the structural
items. `docs/calibration-best-so-far.md` updated to run 85.

---

## NYISO + NEISO P9b — serve measured net interchange in backcasts (2026-06-12)

**Runs `nyiso_smoke_2023`, `neiso_smoke_2024` (re-run in place); dashboard
`nyiso p11 smoke 2023`, `neiso 1 smoke`.** Closes the single red structural
row both P11 smokes flagged: NYISO/NEISO backcasts served **0 TWh** of imports
because the `load_demand` interchange branch was PJM-only, so the LP overfilled
the import wedge with in-state gas. Both ISOs are steady net importers, but the
priced import node only builds under `--priced-interchange`.

**Fix (eia_loader).** Added `nyiso_net_interchange(year)` /
`neiso_net_interchange(year)` sourcing the measured hourly net interchange from
the EIA-930 `NYIS hourly` / `ISNE hourly` parquets' `Total interchange` column
(shared `_eia930_net_interchange` helper). EIA's sign convention is already
export-positive (a net import is negative), so the column is served as-is with
**no** flip — unlike `pjm_net_interchange`, which negates PJM's import-positive
tie-line file. The `load_demand` interchange branch is generalized from PJM-only
to `{PJM, NYISO, NEISO}` (`_SCALAR_INTERCHANGE_ISOS`), default-on for backcast
years (`include_interchange=True`); a net import lowers the residual the
internal fleet serves. ERCOT (islanded; DC ties via its own extract) and CAISO
(imports modeled by the `WECC_import` node, playbook §8.1) stay out. The priced
node remains the *forward* mechanism, used under `--priced-interchange`
(`include_interchange=False`, no double count). Also restored the NEISO P8
demand infrastructure (`_load_neiso_hourly_demand`, `neiso_zonal_load_shares`)
accidentally clobbered by a bad rebase in the NYISO P8 commit, so NEISO demand
reads the ISNE clock and the served interchange is hour-matched.

### Results — both interchange rows now green

**NYISO 2023** (`--commitment`, P10 LMP still held → price level-only):

| fuel | energy-only (old) | **P9b (served)** | EIA-923 | EIA-930 |
|---|---|---|---|---|
| gas (cc+ct+st) | 80.11 (+25.6%) | **57.52 (−9.8%)** | 63.79 | 61.00 |
| nuclear | 27.49 | 27.49 | 27.52 | 24.00 |
| hydro | 28.38 | 28.38 | 28.40 | 26.84 |
| **TOTAL** | **147.31 (+16.0%)** | **123.77 (−2.5%)** | 126.96 | 118.61 |
| net interchange (TWh) | **0.00** 🔴 | **−23.45** 🟢 | — | −23.45 |

Net interchange: model −23.45 vs actual −23.45 TWh (duration RMSE **0 MW**,
import-hours 100% vs 100%, diurnal corr **+1.00** — the served measured
schedule). Avg price $70.99 → **$42.72** (0 negative hours; level **not**
scored, P10 held). The energy-only gas_ct +81% / gas_st +113% / CO2 +57% reads
were interchange symptoms and collapse with the wedge served.

**NEISO 2024** (`--commitment`, P10 LMP held):

| fuel | energy-only (old) | **P9b (served)** | EIA-923 | EIA-930 |
|---|---|---|---|---|
| gas (cc+ct+st) | 67.81 (+11.2%) | **57.94 (−5.0%)** | 60.99 | 59.64 |
| nuclear | 26.48 | 26.48 | 26.55 | 26.41 |
| hydro | 6.67 | 6.67 | 6.71 | 7.39 |
| **TOTAL** | — | **103.96 (+1.1%)** | 102.82 | 98.81 |
| net interchange (TWh) | **0.00** 🔴 | **−10.30** 🟢 | — | −10.30 |

Net interchange: model −10.30 vs actual −10.30 TWh (duration RMSE **0 MW**,
import-hours 83.8% vs 83.8%, diurnal corr **+1.00**). PS over-cycling
self-corrects from the energy-only 1.35 TWh toward EIA-930's 0.30 (now 0.50 —
the gap-#2 cross-coupling the smoke predicted: cheap imports remove part of the
arbitrage spread). Avg price $69.99 → **$55.72**.

**Regression guard.** ERCOT/PJM/CAISO `load_demand` outputs byte-identical
(sha256 over 2023+2024 demand arrays, pre/post). Full suite **1006 passed** (3
pre-existing CAISO zonal-share failures unrelated to this change). New tests:
`nyiso/neiso_net_interchange` import-negative; demand serves the measured wedge
by default; zonal-reconciliation tests isolated with `include_interchange=False`.

**Keeper decision.** Both remain structural-discipline smokes, **not** tuning
keepers — the interchange gate is now green, which *unblocks* the downstream
packs (P7 measured gas + U4 winter basis, P13 winter oil, P10/U2 LMP, P8/U3
zonal load) that were held behind it. No offer band tuned (playbook §6).

---

## ERCOT Runs 89–91 — CC_REGULAR shape + PRB 2024 (2026-06-12)

**Scope.** Close run 85's remaining miss — the single 2024 cheap-gas cluster
(CC_REGULAR +3.1 TWh too high; PRB −7.9% / −3.47 TWh, ST_GAS −1.19,
lignite −1.23, CT_PEAKER −1.48 TWh each ~1 TWh too low) — via the two levers
scoped at the run-85 keeper decision: the never-used econ-ramp midpoint
(`offer_curve_smoothing_mid`, commit c31cd42) and a 2024-keyed PRB sigmoid
retune. **Run 91 is the new keeper** (3 in-scope fails vs run 85's 4, no new
fails, 2024 cluster 7.37 → 3.65 TWh); `docs/calibration-best-so-far.md`
updated. Dashboard: `run89 midpoint`, `run90 prb 2024`, `run91 cc shave`
(top-5 retention prunes run83; the rejected runs 86/87 entries were also
dropped — their bundles stay in `results/calibration`). All scoring below is
the size-aware bar (≥20 TWh classes ±5%, <20 TWh ±1 TWh absolute, CT_CHP
excluded) vs run 85.

### Run 89 — econ-ramp midpoint 0.35 (base B)
Two bundles: `run89_midpoint065` (m=0.65 probe, rejected) and
`run89_midpoint035` (m=0.35, the chosen run 89). The brief's m>0.5 guess
**inverted**: m=0.65 made CC_REGULAR *gain* +1.47 TWh in 2024 and PRB lose
−1.0. Mechanism: the midpoint anchor reshapes every econ ramp, and
CC_REGULAR's ramp is nearly FLAT (econ_low 1.06 → econ_high 0.96), so the
anchor barely moves CC while the steep-ramp classes (PRB 0.40 → 1.38, ST_GAS,
CT) get pricier middles — CC wins the mid-merit hours they vacate. m=0.35
runs the same mechanism in reverse: CC_REGULAR 2024 +3.09 → **+1.37 TWh**
(+0.9%), PRB 2024 −7.9 → −5.5%, CT_PEAKER −17.9 → −15.5%, with small
lignite (−0.17 TWh) / ST_GAS (−0.04) collateral. Same 4 fails as run 85 but
the cluster shrinks 7.37 → 6.28 TWh; LMP MAE 31.2/9.3/11.4 (gate held); 2024
coal NRMSE improves 0.198 → 0.185. **Base B for runs 90–91.** Side effects
to remember: the midpoint costs CC_REGULAR 2023 −1.7 TWh (−2.7 → −3.9%) and
gives PRB 2023 +0.93 — it spends 2023 headroom.

### Run 90 — 2024-keyed PRB sigmoid retune (REJECTED, gradient anchor)
B + reshaped PRB logistic: slope 2.5 → 5 centered 2.85 → $2.45 — between
2024's cheap shaped-gas months ($1.97–2.08; the sigmoid sees annual gas ×
`GAS_MONTHLY_SEASONALITY`, so 2024 = $1.97–2.58, 2023 = $2.29–3.00) and
2023's cheapest ($2.29) — floors −0.06 (0.68/0.58), ceils pinned to run-85
values at ≥$2.5 (1.17/1.04). The shape analysis said 2023's cheap months
keep ~⅓ of 2024's discount; the realized TWh blew through it: PRB 2024
+4.34 TWh (+4.4%, overshoot) but **PRB 2023 +4.09 TWh (+12.4%, FAIL)**,
CC_REGULAR 2023 −5.5% (FAIL), Martin Lake 2023 +2.0 TWh (the run-81 guard
blow-up). 5 fails vs 4. **The quantified lesson (extends run-80e):** the
realized year-gradient is ~65 TWh per unit passthrough in 2024 vs **~142 in
2023** — 2023 sits on the coal-gas knife edge, so even month-deltas of
−0.03 detonate. And the 4-param logistic cannot cut below $2.1 while
tracking run-85's curve at $2.29+: pinning the ceil low leaks discount into
2023 winter/2025; keeping ceil 1.50 with a steep low mid marks up the
$2.4–2.6 overlap months (2024 Dec/Jan = 2023 Mar/Jul/Aug in gas space).
The PRB sigmoid stays at run-85 parameters in the keeper.

### Run 91 — CC_REGULAR per-class shave (KEEPER)
B + CC_REGULAR deltas econ_high −0.45 → −0.40 (+0.05), peak +0.25 → +0.32
(+0.07). Direction from the jacobian (CC_REGULAR.econ_high → PRB 2024
**+6.96 TWh/unit, med conf** — the PRB-2024 fix rides CC's adjacency, not
the coal bid; peak's PRB-2023 row is negative, trimming where headroom is
thinnest), dose from measurement: the full-dose probe (econ_high +0.09 /
peak +0.13, bundle `run91_cc_shave_full`, unregistered) moved every class
the predicted way but ~1.7–3× the jacobian magnitudes in 2023 (CC −5.3%,
PRB +5.3%, ST_GAS +1.06 TWh — three hairline fails, guards +1.05), giving
a measured B→full response vector with feasibility box β ∈ [0.39, 0.74];
the keeper runs β=0.55. Result (`run91_cc_shave055`): **3 fails vs run 85's
4** — PRB 2024 −4.9% PASSES (by 0.04 TWh), CC_REGULAR 2024 +0.4%, 2023/2025
all pass (CC 2023 −4.6%, PRB 2023 +4.3%, ST_GAS 2023 +0.95). Remaining
fails: ST_GAS 2024 −1.12 (run 85 −1.19), CT_PEAKER −1.22 (−1.48), lignite
−1.31 (−1.23, a 0.08 TWh drift — the one nominal regression, size-aware
noise). 2024 ledger vs run 85: CC_REGULAR −2.51 gave, PRB +1.33 / CT +0.26 /
ST_GAS +0.07 took. Guards: Martin Lake/Limestone 2023 +914/+948 GWh; Martin
Lake 2025 +1.50 (run 85 +1.35 — watch). LMP MAE 31.1/9.2/11.5 (gate held);
2024 coal NRMSE 0.198 → 0.182, gas 0.118. Honest caveats: PRB 2024 and
ST_GAS 2023 pass with <0.1 TWh margin (fragile to any further coal/gas
move), and total |class error| is flat (~21.0 TWh) — the 2024 win is paid
for inside CC_REGULAR 2023's tolerance band (−2.7 → −4.6%). The keeper
decision rests on the bar as stated: fewer fails, none new, smaller cluster.

**Open items (runs 92+).** The remaining 2024 trio (ST_GAS/lignite/
CT_PEAKER, all −1.1..−1.3 TWh) has no clean fleet-wide lever left at this
operating point — every coal/gas knob measured this session trades one
hairline constraint for another; the structural items stand: ORDC scarcity
adder for the 2023 LMP level (89% of the summer $·h gap in the ≥$200 band),
per-plant Parish/Spruce correction (under-run all years, −3.9 TWh 2024),
lignite 2024, and the CT_CHP 2025 benchmark gap. A lignite floor probe
(0.75 → 0.72) is the one cheap candidate, but Martin Lake 2023 sits at
+914 GWh with ~86 GWh of guard headroom — re-run the guard before keeping
anything.


## NEISO 2 — full calibration to sign-off 2023–2025 (P12) (2026-06-12)

**Runs `neiso_p12_base_2023`, `neiso_p12_base_2024`, `neiso_p12_hydrofix_2025`;
dashboard `neiso 2 2023`, `neiso 3 2024`, `neiso 4 2025 hydrofix`** — the NEISO
sign-off backcast across 2023–2025, run as three parallel per-year bundles with
distinct `--out-dir` (a combined `--year 2023 2024 2025` bundle hit a warm-start
basis degeneracy in the per-year P2 commitment solves and was abandoned; the
three single-year bundles solve cleanly and reproduce each other to <0.1 TWh).
**Prereqs:** P9b (served interchange) merged, P11 structural rows green. The
keeper is the **NEISO structural defaults — no offer-band tuning** (playbook §6):
served measured net interchange, the Algonquin (AGT) `gas_hub_basis_overlay`,
`dual_fuel_switching`, RGGI via the state-carbon program, `gas_monthly_actuals`,
per-plant F923 gas pricing. The **only** P12 change is a data-vintage fix —
`--hydro-backfill-year 2024` for the 2025 bundle (opt-in, default-None, every
existing run byte-identical; committed in the P12 code change merged via #383).
**P10 still held** (no NEISO `actual_lmp.json`), so price is level-only.

### Scorecard vs the P0 targets

| target | 2023 | 2024 | 2025† | verdict |
|---|---|---|---|---|
| **gas** ±5% | −3.2% / 930 (−5.1% / 923) | −2.8% / 930 (−5.0% / 923) | **−3.9% / 930** | ✅ vs the grid benchmark |
| **nuclear** | −0.2% | −0.2% | +0.7% | ✅ |
| **hydro** | −0.7% / 923 | −0.6% / 923 | +30% (2024 proxy vs 930 5.12) | ✅ 23/24; 25 provisional |
| **oil** | 0.02 vs 0.39 | 0.01 vs 0.31 | 0.01 vs 1.24 | ⚠ winter-shape (U4, filed) |
| **CO₂** ±10% vs eGRID | **−9.2%** (22.81 vs 25.13 Mt) | **−8.5%** (24.52 vs 26.79 Mt) | 24.58 Mt (no eGRID-25) | ✅ |
| **net interchange** ±15% | **exact** (−15.14 TWh, 0 MW RMSE, corr +1.00) | **exact** (−10.30, 0 MW) | **exact** (−8.13, 0 MW) | ✅ |

**Gas benchmark sourcing.** The NEISO model is grid-side (CHP runs its
steam-following grid share; the behind-the-meter host supply is pulled out and
there is no btm.parquet to add back), so total gas is scored against **EIA-930**
— the matching grid-delivered series — at **−3.2 / −2.8 / −3.9%**, comfortably
inside ±5%. The −5% vs EIA-923 is the documented whole-plant offset: 923 reports
gross CHP output including the BTM host slice the grid never sees (the same
923-vs-930 structural gap the ERCOT fuel-split note logs at ~14% on the CHP host
supply). Both benchmarks are reported; they are not mixed within a year.

†2025 EIA-923 is a monthly-survey-only early release; final hydro has not landed
(5 of ~166 plants, 0.09 of ~6 TWh). `--hydro-backfill-year 2024` carries the
non-reporting plants at their 2024 inflow, restoring ~6.6 TWh; **without it 2025
gas was +6.5% vs 930** (the missing inflow served by gas). The 2024 proxy is
wetter than 2025's true 5.12 TWh (EIA-930), so modeled hydro over-states ~1.5 TWh
and gas sits a touch low — a provisional-year artifact that self-corrects on the
final 2025 file.

### Ranked residuals (none band-tunable)

1. **[FILED · winter oil shape] Oil near-zero (0.01–0.02 TWh) vs EIA-923
   0.31–0.39 / EIA-930 0.37–1.24.** Magnitude within ±1 TWh (size-aware) but the
   season shape is wrong: ISO-NE burns oil in cold-snap dual-fuel switches, and
   the **monthly** AGT basis never reaches distillate parity (Jan-2025 HH $3.52 +
   AGT +12.79 ≈ $16.3/MMBtu vs ~$18–20 parity), so the wired CT/ST switch
   correctly does not trip on monthly data; serving interchange also displaces
   the prior oil-steam scarcity burn. **The fix is the daily-AGT U4 upload, not a
   band tune** (task brief; P11 gap #3; doc-08 decision 1). Not tuned.
2. **[AMBER · PS/BESS over-cycling] PS discharge 0.39 / 0.50 / 0.86 TWh vs
   EIA-930 — / 0.30 / 1.93; grid BESS 0.06 / 0.12 / 0.34 vs — / 0.01 / 0.15.**
   Down sharply from the energy-only smoke's 1.35 TWh (P11 gap-#2 cross-coupling:
   served imports remove part of the arbitrage spread). Not a scored target and
   immaterial to fuel-mix / CO₂; `--battery-adder` / a PS throughput cost is the
   lever if it is ever scored. Not tuned (would not move the sign-off metrics).
3. **[INFO · price level, P10 held] All five zones price identically
   ($53.61 / $55.72 / $59.50 for 2023/24/25); no Boston/CT separation** — Tier-3
   RSP TTC seeds non-binding, no measured interface limits (U6). Level reported,
   not scored, until the U2 LMP upload (P10).
4. **[TRACE] Coal 0.00–0.08 vs ~0.2 TWh** — the lone Merrimack unit; trace.

### Keeper decision & provenance

The NEISO **structural defaults are the sign-off keeper** — all three scored
targets (fuel-mix gas ±5% on the grid benchmark, CO₂ ±10% vs eGRID, net
interchange ±15%) pass for the complete-data years 2023/2024; 2025 passes
gas/interchange and is provisional on hydro pending the final EIA-923. **No
offer band was moved** (zero per-class curve overrides), consistent with the
playbook §6 structural discipline. doc-00 Stage G checklist green for NEISO.
Reproduce per year:

```
python scripts/run_calibration_full.py --iso NEISO --year <Y> --commitment \
    [--hydro-backfill-year 2024]   # the bracketed flag for 2025 only
```

**Citations.** eGRID CO₂ benchmark: EPA eGRID2023 (rev2) / eGRID2024, sheet
`SRL23`/`SRL24`, column `SRCO2AN`, subregion `NEWE` — 27.69 / 29.53 M short tons
→ **25.13 / 26.79 Mt** (×0.90718474 short-ton→tonne). Model CO₂ from each plant's
`emission_rate_co2 = heat_rate × FUEL_CO2_FACTOR_PER_MMBTU` (152 NEISO fossil
plants matched, 0 on fallback) — a base-rate figure, so the dispatch's band-HR
multipliers make it conservative (true model CO₂ slightly higher / the gap
smaller). AGT winter basis: `inputs/raw-data/gas_basis_by_iso_month.csv` (ISO-NE
MA gas index, isonewswire monthly posts, 35/36 months 2023–2025). Hydro
early-release backfill rationale documented at `load_hydro_budget`.
---

## NYISO P12 — Full calibration loop to sign-off (2023; 2025/2024 data-blocked) (2026-06-12)

**Keeper: the P9b served-interchange config (`nyiso p11 smoke 2023`, bundle
`results/calibration/nyiso_smoke_2023`), promoted to the P12 sign-off keeper.**
The loop ran the offer-curve / hydro / storage / import / dual-fuel knobs against
the P11+P9b structural config and found **no honest knob that lifts an
out-of-tolerance class without a zero-sum trade against an in-tolerance one or a
convention violation** — so the structural config *is* the keeper. Recorded in
`docs/calibration-best-so-far-nyiso.md`. Branch `claude/nyiso-p12-calibration`.
**P10 LMP still held (U2)** → price level-only, not scored.

### The mix is calibrated; the gas total is a documented basis floor

2023 fuel-mix vs EIA-923 (P2): every renewable/baseload class is inside ±5%
— hydro +1.3%, nuclear −0.1%, wind −3.6%, solar −5.0% (edge), OTHER 0.0%,
CC_REGULAR −2.6%, ST_GAS −0.8% — and net interchange matches exactly (−23.45
vs −23.45 TWh, duration RMSE **0 MW**, import-hours 100%, diurnal corr +1.00).
The one class-level miss is **gas total −9.9%** (57.53 vs 63.84 TWh), and it is
a **demand-basis floor, not a dispatch error**: the in-state fleet's total is
pinned by energy balance to served demand = EIA-930 transmission-metered demand
(147.05) + measured net interchange (−23.45) = **123.77 TWh**, which is 4.5%
below EIA-923's plant-net-generation total (129.67). With every non-gas class
on the EIA-923 mark, the −5.9 TWh total gap must fall on the swing fuel. The
deficit lands on the small **CHP/peaker** classes (CC_CHP −14.6%, CT_CHP
−44.2%, ST_CHP −18.0%, CT_PEAKER −75.2%) while the two big gas classes stay on
target — the least-distorting landing spot. Against EIA-930 (the operationally
consistent basis) gas is **−5.7%**. CO2 ≈ 24 Mt (class-rate approx) vs eGRID-2023
26.9 Mt excl-biogenic ≈ −10%, downstream of the gas total.

**Why no knob closes it (all rejected):**
- **td_loss gross-up** — ruled out by convention: EIA-930 NYIS demand is
  transmission-metered / generation-side (playbook §8.1, the ERCOT
  `td_loss_factor=0` rule), so a distribution-loss gross-up double-counts.
- **import scaling** — serving e.g. −20 TWh (inside the ±15% interchange
  tolerance) would lift the total to ~127 and gas to ~−4%, but the measured
  EIA-930 schedule is matched *exactly* (RMSE 0 MW). Degrading a perfect
  measured match to paper over an EIA-930-vs-EIA-923 *benchmark-basis*
  difference is overfitting, not calibration. **Rejected.**
- **CHP / offer-curve / storage** — reshuffle within the fixed total; the
  obvious CHP lever does not even do that (see `nyiso 2`).

### Passes (one named hypothesis each)

**nyiso 1 gas-actuals** (`--gas-monthly-actuals`, bundle
`nyiso_p12_gasact_2023`) — **REJECTED, no-op.** Hypothesis: measured EIA-923
monthly gas (Jan-2023 $10.02/MMBtu winter spike vs the flat $2.54 HH seed)
re-levels gas and trips the dual-fuel oil switch. Result: **byte-identical**
mix and price duration (gas 57.53, oil 0.013, avg $42.72, max $235.81) — the
harness already enables `gas_monthly_actuals` + `gas_plant_monthly_fuel_pricing`
by default for NYISO (the P11 "flat $2.54 seed" note predated the P9b re-run).
So the winter gas level is already priced in, and oil still does not fire: even
measured monthly Jan gas ($10) stays below distillate parity (~$16/MMBtu), the
documented P13 limitation — **winter oil is gated on the U4 daily Transco-Z6 /
Iroquois gas basis, which is not uploaded for NYISO** (only the NEISO/Algonquin
leg is filled). oil −96.9% is therefore filed to U4, not tunable this pass.

**nyiso 2 chp-covered** (`--chp-startup-covered`, bundle `nyiso_p12_chp_2023`)
— **REJECTED, negligible.** Hypothesis: the CHP under-dispatch is a
startup-amortization artifact — a steam-host cogen pays no energy-market cold
start, so removing the markup lets CC_CHP/CT_CHP/ST_CHP run toward their
must-run reality. Result: CHP moved only **+0.1 TWh total** (CC_CHP +0.027,
ST_CHP +0.051, CT_CHP +0.017; CC_REGULAR −0.033, ST_GAS −0.048; gas total
57.525 → 57.537; avg price $42.72 → $43.02). The CHP/peaker deficit is
**structural** — the model dispatches CHP economically and enforces no hard
steam-host must-run floor — not a startup-cost artifact, and within the fixed
served total there is no room for the CHP classes to recover without displacing
the on-target baseload gas. A hard steam-host / reliability-must-run floor
(EIA-860 cogen steam load + downstate reliability commitments) is the structural
follow-up, filed; it is not an offer-band knob.

### 2025 and 2024 are data-blocked (filed, not calibrated)

The P12 prompt asks for 2023 **+ 2025** in parallel. 2025 is **not yet a valid
backcast year**:
- The EIA-930 `NYIS hourly` extract stops at **Q1 2025** (2,160 of 8,760 h), so
  `nyiso_net_interchange(2025)` returns `None`; `load_demand` falls back to the
  demand-profiles parquet (full-year **gross** demand, 151.6 TWh) and serves
  **0** of the ~−23 TWh import wedge → the 2025 baseline bundle
  (`nyiso_p12_base_2025`) **over-generates +22.7%** (151.9 vs EIA-923 123.8 TWh,
  gas +11.8%, avg price $127) — the exact P11 structural failure, here driven by
  missing data rather than missing code.
- The 2025 EIA-923 benchmark is preliminary (biomass 0.13, solar 0.66, oil 1.06
  TWh — renewables/biomass under-reported), so even with interchange it could
  not be scored.
- **Refresh path:** extend the EIA-930 `NYIS hourly` extract through 2025-12 and
  re-pull final 2025 EIA-923, then re-run `nyiso_p12_base_2025`. Until then the
  2025 bundle is retained on disk as the data-gap evidence, **not registered.**

2024 remains blocked on `NY_2024` unit-level CEMS (only facility-level present)
and the missing `NYISO_2024_renewable_capacity.csv`.

### Keeper decision & sign-off

`nyiso p11 smoke 2023` is the **P12 keeper** (no new tuning bundle — the
structural config is optimal under the binding constraint). 2023 Stage-G
calibration is **green on every scorable target except the gas-total basis floor
and the U4-gated winter oil**, both documented above. Dashboard carries the
keeper; `nyiso_p12_gasact_2023` / `nyiso_p12_chp_2023` / `nyiso_p12_base_2025`
are retained on disk as the rejected-probe / data-gap evidence (not registered —
no keeper among them). `docs/calibration-best-so-far-nyiso.md` records the
config; doc-00 status table + Stage-G checklist updated; citations appended.

---

## CAISO 2 — priced-WECC-node smoke 2023-2025 (P11, structural-checklist pass) (2026-06-12)

**Run `results/calibration/caiso_1_priced_ix`, dashboard `caiso 2 priced-ix`** —
the first CAISO full bundle (`run_calibration_full.py --iso CAISO --year 2023
2024 2025 --hours 8760 --commitment`, P1+P2) solved with the **priced WECC
import/export node ON by default** (`PRICED_INTERCHANGE_DEFAULT_ISOS={CAISO}`,
no `--priced-interchange` flag — `load_demand` does no interchange netting for
CAISO, so the node is the only correct default) and the 2023-2025-fitted
`IMPORT_TRANCHES`/`EXPORT_TRANCHES["CAISO"]` (CHANGELOG 2026-06-12: 6 import
blocks 11.4 GW + 2 export sinks 6.5 GW). Prereqs P0-P10 merged; **P10 is in
level-only mode** — no `actual_lmp.json` CAISO block, so the modeled price level
is reported, not scored. Structural-discipline pass (playbook §6): **no
offer-band tuning** — structural row #2 is red and is **filed**, not tuned.

This pass answers the P9 "remaining" item (re-score the *modeled* net
interchange and clearing frequency vs the solved CAISO price duration curve,
not just the offline price-orthogonal bound).

### Headline numbers (P2 commitment bundle)

| Metric | 2023 | 2024 | 2025 | Benchmark | Read |
|---|---|---|---|---|---|
| gas (TWh) | 44.98 | 54.47 | 62.16 | EIA-923 76.04 / 67.68 / 55.18 | **−41% / −19% / +13% — now UNDER-produces (over-import overshoot)** |
| gas vs EIA-930 | 44.98 | 54.47 | 62.16 | 88.01 / 85.37 / 79.03 | −49% / −36% / −21% |
| nuclear | 17.63 | 18.20 | 17.49 | 930 17.75 / 18.35 / 17.61 | ✓ −0.7% / −0.8% / −0.7% |
| wind | 16.55 | 20.29 | 19.81 | 930 16.40 / 20.06 / 19.82 | ✓ (judged vs 930) |
| solar | 39.79 | 47.91 | 49.81 | 930 37.17 / 44.64 / 49.70 | ✓ +7% / +7% / +0.2% vs 930 |
| hydro | 23.78 | 21.23 | 12.32 | 930 24.42 / 22.73 / 21.34 | ✓ / ✓ / **−42% 2025 (partial-year budget; 923 2025 total 117 TWh = incomplete)** |
| **net interchange (TWh)** | **−61.65** | **−49.26** | **−52.86** | **EIA-930 −28.87 / −32.38 / −36.16** | **RED — +114% / +52% / +46%, far outside ±15%** |
| import-hour share | 99.9% | 100.0% | 100.0% | 85.9% / 89.0% / 90.9% | **RED — node never exports; midday sign-flip absent** |
| diurnal corr | +0.96 | +0.96 | +0.90 | — | shape OK but amplitude tiny (peak→trough 1453/833/462 MW vs 5236/4596/4973 measured) and never crosses zero |
| solar curtailment (TWh) | 0.000 | 0.000 | (no HSL) | reported 2.509 / 3.170 | **RED — model re-curtails ZERO (0% vs 6.3% / 6.6%)** |
| battery discharge (TWh) | 4.99 | 6.86 | 9.61 | — (CISO folds BAT into OTH) | evening share 93% / 85% / 67%; no 930 benchmark |
| PS discharge (TWh) | 1.80 | 1.27 | 0.39 | — | no 930 benchmark |
| avg price ($/MWh) | 77.34 | 53.10 | 56.63 | — (P10 held) | 2023 biased high; **0 negative-price hours all years** (real CAISO has hundreds) |

### Ranked gap list (structural-checklist order; hypotheses + owning pack)

1. **[GREEN · demand/net-load]** CAISO demand is the CISO EIA-930 net-load
   series (no interchange netting — the documented convention, §8.1/§8.2); the
   import↔gas swap below is *not* a demand error. Minor: 2023 TAC-area load
   covers 8759/8760 h, the gap filled with sample-average zone shares (refresh:
   complete the U4 monthly OASIS pulls). No action.

2. **[RED · net interchange] The priced WECC node OVER-imports — it closes the
   old gas-overproduction gap but overshoots into the opposite error.** Modeled
   net interchange **−61.65 / −49.26 / −52.86 TWh vs EIA-930 −28.87 / −32.38 /
   −36.16** (+114% / +52% / +46%, all far outside the ±15% acceptance band).
   The node imports in **~100% of hours vs 86-91% measured** and **never
   exports**, so the midday solar export sign-flip is not reproduced (measured
   p90/p99 are positive — +661/+3574 MW in 2023 — but the model stays −2548 MW
   at p99). **Root cause: tranche *prices*, not capacities.** The offline
   price-orthogonal fit is good (duration RMSE ~560 MW, annual within 1-3%; the
   capacities tile the duration curve), but the static tranche prices
   ($14 PNW_hydro → $92 WECC_scarcity, absolute delivered-WECC-energy costs)
   sit **below the modeled CAISO price duration curve** (p10 $43-48, *zero*
   negative hours) in nearly every hour, so almost the full 11.4 GW import stack
   clears continuously while the $0-8 export sinks essentially never clear (the
   modeled price never collapses midday). Bundle-mode `derive_import_tranches.py
   --bundle caiso_1_priced_ix` confirms it: current constants score
   **216% / 154% / 148% of actual annual** against *this* solved price curve,
   and the re-fit pushes the import/export boundary up to ~$34-48 with import
   blocks layered at $46-275 (2023) / $44-74 (2024) / $48-80 (2025). **This is
   a calibration item, not a structural-machinery one** — the node, zone, links
   and capacities are right; only the price levels relative to the modeled
   CAISO price are off. **Owner: P9/P12** — re-price `IMPORT_TRANCHES`/
   `EXPORT_TRANCHES["CAISO"]` in bundle mode against the solved price duration
   curve, iterating (re-pricing shifts the solved price, so 2-3 passes). **This
   blocks everything below — do not tune offer bands until it is fixed.**

3. **[RED · curtailment] The LP re-curtails zero solar/wind.** Model curtailment
   **0.000 TWh** both HSL years vs reported solar **2.509 (6.3%) / 3.170 TWh
   (6.6%)** and wind 0.151 / 0.229. With 6-8 GW of cheap imports flooding supply
   and **no negative-price hours**, the midday oversupply that should spill
   instead displaces gas/exports — a *symptom of gap #2* (cheap imports remove
   the negative-price regime that drives curtailment) compounded by the P6
   profile path (the LP consumed the delivered/HSL potential and dispatched
   100% of it). 2025 has **no CAISO HSL parquet** (`build_caiso_hsl.py` not yet
   run). **Hypothesis:** re-measure curtailment after gap #2 is fixed; if still
   zero, the renewable feed is delivered-not-potential (P6 fallback). **Owner:
   P6 (HSL build for all years) / re-check after P9/P12.**

4. **[AMBER · gas+carbon level — downstream of #2] Gas no longer overproduces —
   it now UNDER-produces.** The task's confirm-the-headline-gap check: the prior
   energy-only baseline (`caiso 1 baseline`) over-generated gas because it had
   no interchange node for CAISO's ~30 TWh/yr net imports. With the node ON,
   gas falls to **44.98 / 54.47 / 62.16 TWh — now −41% / −19% vs EIA-923 in
   2023/2024** (and +13% in the partial-2025). This is a **direct one-for-one
   swap with gap #2**: the +33 TWh of excess 2023 imports displaces ≈31 TWh of
   gas. So the structural fix (priced node) addressed the right gap, but its
   over-calibration moved gas through the target and out the far side. Gas lands
   right once the node imports the correct ~29 TWh (gap #2 fix). **No gas knob
   this pass** — moving fuel passthrough or offer bands here would bake in a
   compensating error against the over-import (the PJM lesson). **Owner: resolves
   with #2.** Carbon: CARB cap-and-trade enters MC via `state_carbon_pricing`
   (CAISO allowance + border adder on tranches); level not separately scored
   (P10 held).

5. **[AMBER · hydro/PS/battery throughput] 2025 hydro low; storage has no 930
   benchmark.** Hydro ✓ in 2023/2024 (−2.6% / −6.6% vs 930) but **−42% in 2025**
   (12.32 vs 21.34) — the 2025 monthly budget is partial (EIA-923 2025 system
   total is only 117 TWh, an incomplete reporting year), a *data* gap not a
   dispatch one. Battery throughput (4.99→9.61 TWh, growing with the fleet) and
   PS (1.80→0.39 TWh) cannot be scored — the CISO extract folds BAT into `OTH`.
   Evening-discharge share is high (93%→67%, plausibly correct for CA evening
   ramp) but unverifiable. **Hypothesis:** complete the 2025 hydro budget (U4
   refresh); add the storage benchmark when a CISO battery series is available.
   Watch over-cycling after gap #2 (cheap imports inflate arbitrage spread, the
   NEISO PS lesson). **Owner: P4 (2025 budget) / P5 (battery benchmark).**

6. **[INFO · outages]** Historic unit-outage overlay fires (229 CAISO
   plant-tranches derated 2023). No coverage red flag this pass. No action.

7. **[INFO · price level/duration — P10 held]** No `actual_lmp.json` CAISO
   block, so the modeled level (avg $77.34 / $53.10 / $56.63) is reported, not
   benchmarked. All four zones (NP15/SP15/ZP26/WECC_import) price *identically*
   every year — **no NP15↔SP15 separation** (the Tier-3 TTC seeds are
   non-binding) — and **zero negative-price hours** all years, which real CAISO
   contradicts (the midday solar collapse). Both are biased by gap #2 (cheap
   imports prop the floor up). **Owner: P10 (U2 LMP upload + U5 Path 15/26 flows
   for congestion/negatives).**

### Keeper decision

`caiso 2 priced-ix` registered as the second CAISO run (baseline + this; under
the 5-run retention limit, no pruning). **Not a calibration keeper for tuning.**
The priced WECC node is the correct structural mechanism and it closes the
energy-only baseline's headline gas-overproduction gap — but it is **mis-priced
relative to the modeled CAISO price**, so it over-imports (+46-114%) and
suppresses gas below target while never reproducing the midday export sign-flip.
**Acceptance NOT met:** modeled net interchange is far outside ±15% and the
diurnal sign pattern is not reproduced. Per playbook §6 the red structural row
(#2 interchange) is **filed for a bundle-mode tranche-price recalibration
(P9/P12)** — no offer-band, gas, hydro or storage knob is moved this pass, since
all of them would compensate for the over-import and bake in errors that must be
unwound once the node is repriced. The bundle and its `derive_import_tranches.py
--bundle` re-fit boundaries are the evidence for that next pass.

---

---

## ERCOT Run 92 — Kiamichi fleet fix: the missing 1.4 GW CC (2026-06-12)

**Trigger.** Post-run-91 question: why does the model "generate ~470 TWh when
actual is 475"? Reconciliation: the LP serves EIA-930 demand exactly (446.0
TWh 2023, unserved 0); on the 923 basis the model+BTM totals 473.9 vs 475.2.
The wedge decomposes into the solar source difference (model solar follows
930 actuals, +3.8 TWh above what 923 credits) and **one plant**: the 923
CC_REGULAR benchmark includes **Kiamichi Energy Facility (EIA 55501)** —
Kiowa OK, `ba_code ERCO`, 1370 MW F-class 2×(2×1) CC, online 2003, EIA
annual HR 8.119, ~5.0–5.3 TWh/yr — the **single ERCOT-BA plant outside
Texas** (1401 TX + 1 OK), dropped by the TX-state-filtered registry build.
With `use_campd_bins=True` the bins CSV IS the fleet, so the plant never
dispatched. The CC fleet covered the hole by over-running CAMPD (+4.7 TWh
2023, **+13.2 TWh 2024**) — most of run-91's "CC_REGULAR 2023 −4.6%" and
the 2023 gas-split fail were this bias, not mix tuning. CAMPD-vs-923 class
wedge is a stable ~+14 TWh/yr (~5 Kiamichi + ~9 netting).

**Fix (permanent, inputs).** Registry row (EIA-860 facts, CC-fleet medians
for ancillary fields, `has_campd_data=False` — no OK CAMPD extract, so
statistical availability, no outage overlay, absent from per-plant panels)
+ bins row (North / N_CC7 / 25-60-15 committed-econ-peak, HR mults
1.08/1.0/1.55). Smoke-tested: 3 LP tranches, 1370.2 MW, zone North.

**Run 92 (`run92_kiamichi`, dashboard `run92 kiamichi`; prunes run84).**
Run-91 tuning unchanged on the corrected fleet. The targeted cells land:
**CC_REGULAR 2023 −4.6 → −1.3%**, ST_GAS 2023 +0.95 → −0.29 TWh, 2023 fuel
split passes both fuels (gas −1.9 / coal +1.5; was fail/fail), 2024 gas
split +0.2. **The LMP level was the smoking gun: MAE 2025 11.5 → 2.2
$/MWh, 2024 9.2 → 7.3** (2023 32.1, at the ±$1 gate edge) — the model had
been over-pricing tight years because 1.4 GW of real supply was missing.
But the run-91 offer tuning is stale on the bigger CC fleet: Kiamichi's
energy crowds the adjacent classes instead of the incumbent CCs giving
back their over-run — CC_REGULAR 2024 **+4.1%** (+5.9 TWh), CT_PEAKER
fails **all three years** (−1.5/−2.6/−1.7 TWh), PRB 2024 −8.5%, ST_GAS
2024 −13.2%. **6 in-scope class fails vs run 85's 4 → run 92 is NOT the
scored keeper; it is the corrected baseline.** Guards: Martin Lake/
Limestone 2023 +582/+797 (clean).

**Keeper bookkeeping.** Run 91 remains the best scored run, but the fleet
fix is permanent, so run 91 is **not reproducible on current inputs** —
`calibration-best-so-far.md` carries an OPEN status note. The next
campaign re-tunes the offer curves on the corrected fleet: the CC give-back
(econ_high/peak up, now with real 2023 headroom — CC 2023 sits at −1.3%),
CT_PEAKER recovery in all years (year-blind lever is finally safe: CT is
under everywhere; mind the run-82 committed-step explosion zone below mult
~1.0), and the 2024 coal trio. The pre-Kiamichi Jacobian pure pairs no
longer describe the fleet — re-derive with fresh probe pairs before
trusting any recipe.

---

## NEISO price re-score — P12 keepers vs actual_lmp (P10 landed) (2026-06-12)

**Scope.** P10 (the U2 LMP upload) has landed: `inputs/calibration/actual_lmp.json`
now carries a NEISO block (DA + RT hub `.H.INTERNAL_HUB` + the four model-zone
averages, annual/monthly/duration percentiles) and
`actual_lmp_hourly_NEISO.parquet` is the dense 8760 hub-mean sidecar. This pass
**scores the price** of the three P12 sign-off keepers
(`neiso_p12_base_2023`, `neiso_p12_base_2024`, `neiso_p12_hydrofix_2025`) that
were signed off level-only — it does **not** re-tune them (the structural fuel-
mix / CO₂ / interchange rows are green and stay green; zero offer-band moves).
Scored from the existing bundles' `system.parquet` dual prices (no re-solve):
the four model load zones price **identically** every hour, so the modeled hub
is the common internal price (P1 pass, demand-served zones; `HQ_import` carries
zero load and does not enter the demand-weighted level). Comparison convention
follows `scripts/analyze_lmp_residual.py` — modeled vs actual **RT** (DA
reported alongside).

### 1. Level + duration-curve fit (hub `.H.INTERNAL_HUB`)

| metric | 2023 | 2024 | 2025† |
|---|---|---|---|
| modeled hub mean ($/MWh) | 53.58 | 55.68 | 53.44 |
| actual hub RT / DA | 35.70 / 36.82 | 39.54 / 41.51 | 65.89 / 67.86 |
| residual vs RT ($ / %) | **+17.9 / +50%** | **+16.1 / +41%** | **−12.5 / −19%** |
| model p50 / p90 / p99 | 36 / 125 / 150 | 38 / 105 / 125 | 53 / 64 / 94 |
| actual-RT p50 / p90 / p99 | 27 / 57 / 184 | 30 / 68 / 168 | 45 / 144 / 246 |
| >$75 tail share (model / actRT) | **24.7% / 5.9%** | **29.8% / 8.2%** | **5.8% / 27.2%** |
| hourly corr (model vs actRT) | +0.30 | +0.31 | +0.45 |

†2025 is the provisional year (`--hydro-backfill-year 2024`); its actual prices
are final, but the modeled bundle inherits the 2025 hydro/oil data caveats.

**The duration shape is the diagnosis, not the level.** In every year the model
produces a **fat $75–150 plateau with no extreme tail**: model p99 *under-shoots*
actual p99 in all three years (150 vs 184; 125 vs 168; 94 vs 246) while the
>$75 share is 3–5× *too high* in 2023/2024 and 5× too low in 2025. The model
never clears a single hour >$200 in any winter window; actual RT has 44 / 11 /
160. This is the signature of a **monthly** marginal-fuel input meeting a market
whose price is set by **daily** gas spot — see attribution (3).

Per model zone (modeled uniform, no congestion): residual vs actual-zone RT is
≈ uniform — 2023 +20.4..+21.4, 2024 +17.2..+18.5, 2025 −9.3..−11.6 — because
the modeled zones are identical and the actual zones sit within ~$1.5 of each
other (see 2).

### 2. Zonal-spread adequacy (4-zone sufficiency gate) — confirmed, one item filed

The modeled **Boston−Hub and CT−Hub spreads are exactly $0** (all four load
zones price identically; the Tier-3 RSP TTC seeds never bind, no measured
interface limits — U6 not uploaded). The actual day-ahead separation
(`neiso-zonal-adequacy.md`) is itself tiny — signed-mean Boston−Hub +0.30 /
+0.55 / +0.81 and CT−Hub −0.78 / −1.18 / −1.87, every pocket median under
$1/MWh — so the model's zero separation **tracks the actual to within the
documented "level-market" tolerance** for Boston and North, and the adequacy
doc's own conclusion (keep 4 zones on *structural*, not price, grounds) stands.
**The one divergence filed:** the model cannot reproduce **Connecticut's
growing cheap-side tail** (CT−Hub p99 $5.0 → $13.5 across 2023→2025, 7.4% of
2025 hours >$5 below hub) — CT is well-supplied (Millstone + NEEWS imports) and
parts cheap from the hub under cold-snap evening peaks, which a copper-plate
internal price erases. **Do not add zones** (the spread is sub-$2 mean and the
4-zone split is already justified structurally); the lever is the U6 interface-
flow upload to replace the non-binding RSP TTC seeds, not topology. Filed.

### 3. Winter-tail miss attributed to U4 (daily-AGT gap) — NO band tuning

The residual is **concentrated in winter (Jan/Feb/Dec) and a few summer-peak
months**, and the winter miss is the documented monthly-AGT limitation
(neiso-data-audit §2b; doc-08 decision 1; P11 gap #3), **not** offer bands:

- **The modeled winter is a flat monthly plateau.** Jan/Feb model duration:
  2023 p50 $123 → max $147 (a $123–147 band); 2025 p50 $55 → max $66. The
  intra-month hourly spread is ~zero because the committed AGT basis is
  **monthly** — every winter hour inherits the same monthly-mean gas cost.
  Real ISO-NE winter is spiky (2023 Jan/Feb actual p50 $38, p99 $273, max
  $462; 2025 p50 $126, p99 $285) because price is set by **daily** AGT spot
  blowouts.
- **The miss cuts both ways, and both directions are U4.** Where the monthly
  mean over-states the typical hour (2023/2024: many moderate actual hours sit
  below the flat plateau) the model **over-prices the mid-curve** (fat >$75
  band); where the realized daily blowout dwarfs the monthly mean (2025 Jan
  +12.79 / Feb +10.43 / Dec +10.64 basis, actual winter ~$130) the model
  **under-prices catastrophically** (Jan −79, Feb −72, Dec −69). Either way the
  model **never reaches the cold-snap spike tail** (0 hours >$200 vs 44/11/160
  actual) — the p99 under-shoot the task predicted. A daily-AGT series (U4)
  would trip the dual-fuel CT switch and resolve the plateau into spikes; a
  band move cannot manufacture daily price variance from a monthly input.
- **Companion summer-peak over-pricing — same oil-steam family, filed not
  tuned.** Jul-2023 ($128 vs $39) and Aug-2024 ($87 vs $39) are flat
  over-priced *summer* plateaus with **zero slack** (max-slack 0; not VOLL —
  the marginal unit is expensive oil-steam, HR ~10–12 × distillate). This is
  the documented inversion: with the monthly AGT below distillate parity the
  dual-fuel/oil-steam scarcity dispatch lands in summer peak hours instead of
  winter cold snaps (backcast-2024 gap #1, the oil-shape item). The fix is the
  same U4 daily basis, not an offer-band; filed.

The broad year-over-year flatness (model ~$54 every year vs actual rising
$36 → $66) is additionally the served-interchange convention: imports are
netted into demand rather than price-setting, so cheap HQ hydro never sets the
marginal price and the modeled marginal unit is always a dearer internal
generator. The P11 smoke's `--priced-interchange` diagnostic pulled the 2024
level to $48 (vs $56 served, $39.5 actual) — closer but still over; the priced
node remains the forward mechanism. Structural (P9), filed, **not** band-tunable.

### Scored verdict & keeper

Price is now **scored** for 2023–2025 (level + duration + zonal spread); it does
**not** meet the ±5% duration / ±5–10% level target. The miss is **filed**, not
tuned: (a) winter Jan/Feb/Dec tail → **U4 daily AGT** (the make-or-break NEISO
upload), (b) zonal CT cheap tail → **U6** interface limits, (c) mid-curve level
→ priced-interchange node (P9). **No offer band was moved; the structural
fuel-mix / CO₂ / interchange rows are untouched and still green.** The P12
keepers remain the sign-off config. ERCOT / PJM / CAISO / NYISO untouched.
Dashboard runs `neiso 2 2023` / `neiso 3 2024` / `neiso 4 2025 hydrofix`
re-registered so the now-present NEISO `actual_lmp` benchmark drives the price
scorecard. Reproduce: `python scripts/analyze_lmp_residual.py
results/calibration/neiso_p12_base_2023 … --months 1 2 --years 2023 2024 2025`.

---

## ERCOT — ORDC scarcity overlay + AS netting (2026-06-12)

**Campaign: give the energy-only LP the price tail it structurally cannot
produce, post-solve, so capacity-expansion revenue (and therefore the 2040s
fleet behind the emissions answer) stops being computed on duals with zero
scarcity rent. Volumes untouched by construction. Baseline bundle:
`run92_kiamichi` (the corrected-fleet baseline, LMP MAE 32.1 / 7.3 / 2.2);
this campaign is independent of the runs-93-95 volume retune.** Full
methodology + provenance: `docs/ordc-overlay.md`.

**Mechanism (published, zero fitted parameters).** ERCOT's RTORPA as
published (ORDC OBD / NPRR568; 2024 Biennial ORDC Report): two half-hour
LOLP terms — `0.5·(VOLL−λ)·[LOLP(R; μ, σ) + LOLP(R; μ/2, σ/√2)]`, LOLP =
1−NormCDF(R−X) pinned to 1 at R ≤ X — with the post-Uri values as
ScenarioConfig defaults: VOLL `ordc_voll` $5,000 (PUCT 52631, eff.
2022-01-01), X `ordc_mcl_mw` 3,000 MW (OBDRR038/52373), the 2019/2020
PUCT-48551 curve shift `ordc_lolp_shift_sigma` 0.5σ (a mean shift, not σ
inflation — web-verified), and the OBDRR048 multi-step RTORPA floor ($20 ≤
6,500 MW / $10 ≤ 7,000 MW, date-gated at its 2023-11-01 effective date).
All knobs are tier-1/2 scenario fields with citations in the registry; a
PUCT cap change is a runnable scenario (pre-Uri $9,000 tested: 2023 tail
moves up, mean adder $2.97→$5.37, >$500 hours 15→22 — direction correct).
Implementation: `results/scarcity.py` + `scripts/derive_ordc_overlay.py`
(post-processes a bundle; reconstructs the exact hourly availability via a
new `run_year(fleet_only=True)` exit — no LP re-solve) writing
`scarcity.parquet` (lmp + scarcity_adder + lmp_scarcity) next to the
untouched energy-only series; `analyze_lmp_residual.py --with-scarcity`.
RTC+B (2025-12-05) retired the ORDC for AS demand curves — ASDCs stay
VOLL-anchored/ORDC-shaped, so the overlay remains the right first-order
forward-year scarcity representation. RTORDPA (reliability deployments) not
modeled. One genuinely unverifiable input: the seasonal/TOD-block μ/σ
(ERCOT NP6-576-ER — ercot.com egress-blocked from this environment, no
secondary source quotes 2022-25 values). Flat fallback σ=1,400 MW bounded a
priori from the OBDRR048 floor anchor (at σ=2,800 a $10 floor at 7 GW would
be vacuous); `ordc_lolp_params_path` takes the published table when fetched
— the highest-value follow-up.

**Diagnostic first (the honesty gate) — PASSED.** Before any adder:
actual-minus-model residual vs reconstructed model headroom is cleanly
monotone in 2023 (>20 GW: −$1; 6-8 GW: +$860; <4 GW: +$2,181; Spearman
−0.48 Jun-Sep), the actual ≥$200 hours sit at the thin end (median headroom
8.1 vs 23.0 GW overall, 100 of 181 in Aug), and 2024/25 tail hours sit fat
(10.4 / 16.1 GW medians). The outage overlay / load shape is sound; the
miss is the price mechanism, as diagnosed in Runs 85-87 §D.

**AS netting — investigated, REJECTED as default (the campaign's main
empirical finding).** Netting the published AS plan (8,100 MW, IMM 2023
SOM) out of headroom — the brief's proposed reserves definition — puts
model reserves at/below the MCL in 1,000+ hours of 2023 vs 104 actual
>$500 hours: MAE 32.1→512 / 7.3→100 / 2.2→43. Structural reason: ERCOT's
published reserve inputs (RTOLCAP/RTOFFCAP) *count* AS-held capacity as
reserves, so subtracting the AS plan double-counts scarcity. Default
`ordc_as_plan_mw=0`: model headroom (thermal avail − dispatch + storage
cap−dis+chg + renewable curtailment headroom, hydro excluded) plays
RTOLCAP+RTOFFCAP, all-online (the LP has no commitment state — documented
approximation, both directions: perfect-commitment headroom overstates
on-line reserves in shoulder hours; missing Load Resources ~2-3 GW
understates them).

**Validation (gates vs run92_kiamichi, defaults).** Monthly LMP MAE
(demand-weighted): **2023 32.1 → 28.0** (>=$200 hours 0→31 vs 181 actual,
>$500 0→15 vs 104, max $3,131; Jun-Sep $·h gap 12% closed) — the ≤~15
target is **missed honestly**; **2024 7.3 → 7.9 and 2025 2.2 → 2.2 hold
the ±$1 gate** (adder >$1 in 163/28/4 hours per year — the published curve
indeed rarely binds in the comfortable years). σ-sensitivity (reported,
not tuned: σ=2,800 would give 2023 MAE 11.1 and hold the other gates, but
it contradicts the floor anchor and picking it for the score is the
forbidden fit). Remaining-gap attribution: (a) perfect-commitment headroom
in the $100-1,000 shoulder hours, (b) the IMM-documented 2023 artificial
scarcity (conservative ECRS deployment roughly doubled Jun-Dec 2023 RT
prices, >$12B — flowed through RTORDPA/deployments an ORDC-only overlay
correctly does not reproduce), (c) the unverified σ. Volumes tripwire: the
overlay only adds files (`availability.parquet`, `scarcity.parquet`); no
tracked bundle file modified; `_session_score run92_kiamichi` unchanged by
construction. Dashboard monthly-LMP panel deliberately untouched.

**Revenue wiring (the capacity-expansion deliverable).** Audit: forecast
retirement/new-entry/CCS screens consumed raw LP duals
(`runner.py` `prior_results["prices"]` → `capacity.evolve_fleet` →
`apply_economic_retirements` inframarginal margin, `estimate_expected_revenue`)
— the over-retirement bias, confirmed. Fixed: with
`scarcity_pricing_enabled` (ERCOT-only) the runner now hands
`prices + adder` to the capacity-economics path; persisted results and
volumes untouched; capacity-market ISOs untouched. Per-class backcast
revenue with the adder moves in the sane direction and order:
**CT_PEAKER 2023 +83%, storage discharge +168%**, ST_GAS +46%, CC_REGULAR
+20%, wind +9%; 2024 +33/+92%; 2025 ≈ +0% (comfortable reserves). Unit
tests `tests/test_scarcity.py` (13: pin/cap/floor/monotonicity/season-block
mapping/headroom composition/backcast floor gating).

---

## NYISO 2025 — EIA-930 refresh unblock + price re-score (2023 & 2025) (2026-06-12)

**Run `results/calibration/nyiso_p12_2025_refreshed`, dashboard `nyiso 2025
refreshed`.** Unblocks the year P12 had to file as data-blocked and re-scores
the price metrics P12 had to leave as "level-only" (U2/P10 LMP had not landed).
Branch `claude/nyiso-2025-refresh-rescore`.

### The unblock — refreshed EIA-930 NYIS extract spans full 2025

The user re-uploaded the EIA-930 raw long files
(`inputs/raw-data/eia-930/NYIS_region.parquet` + `NYIS_fueltype.parquet`, now
2015–2026). Regenerated the wide hourly with
`python scripts/convert_eia930.py NYIS --input-dir inputs/raw-data/eia-930 --force`:
`NYIS hourly` now carries **8,760 h for 2025** (Demand non-null 8,760/8,760),
where the old extract stopped at **Q1'25 (2,154 h)**. 2023 (8,760) and 2024
(8,784, leap) are byte-identical to the prior file — Demand 147.05/150.88 TWh,
net interchange −23.45/−20.39 TWh, WND 4.60/6.04 TWh all unchanged — so the
2023 keeper, the other ISOs, and every loader test are untouched (only the
NYIS parquet changed). `nyiso_net_interchange(2025)` now returns the measured
series (**−19.09 TWh**, was `None`); `_load_nyiso_hourly_demand(2025)` returns
151.55 TWh on the EIA-930 clock instead of the gross demand-profiles fallback.

### The over-gen closes — interchange served (was the +22.7% wedge)

P12's `nyiso_p12_base_2025` over-generated **+22.7%** (151.9 vs EIA-923 123.8
TWh) purely because `load_demand` fell back to gross demand and served **0** of
the import wedge. With the refreshed parquet the measured net interchange is
served by default:

| | model | actual EIA-930 |
|---|---|---|
| net interchange (TWh) | **−19.09** 🟢 | −19.09 |
| duration RMSE | **0 MW** | — |
| import-hours | 99.8% | 99.8% |
| diurnal corr | **+1.00** | — |

Fuel mix (`--commitment`):

| fuel | model | EIA-930 | Δ930 | EIA-923 (prelim) | Δ923 |
|---|---|---|---|---|---|
| gas | 68.30 | 70.25 | **−2.8%** | 60.21 | +13.4% |
| nuclear | 28.38 | 27.95 | +1.5% | 28.41 | −0.1% |
| wind | 7.05 | 7.05 | exact | — | — |
| hydro | 21.05 | 24.10 | −12.7% | 21.05 | budget |
| oil | 0.02 | 0.18 | — | 1.06 | U4-gated |
| **TOTAL** | **132.76** | 129.54 | **+2.5%** | 115.84 | +14.6% |

**EIA-923 2025 is the preliminary M-file** (total 115.84 TWh, ~17 below served
demand; solar 0.66, biomass/oil under-reported) — **flagged, not chased**.
Against EIA-930 (the operationally consistent basis) gas is **−2.8%** and total
**+2.5%**: the over-gen is gone and the gas level is sane. The +13.4% vs 923
reads off the under-reported preliminary total, the same EIA-930/EIA-923
demand-basis gap documented for the 2023 keeper, not a dispatch error.

### Price re-score — P12's "level-only" metrics now scored (2023 + 2025)

Scored both the 2023 keeper (`nyiso_smoke_2023`) and this 2025 run against
`actual_lmp.json` (per-zone DA/RT levels) + `actual_lmp_hourly_NYISO.parquet`
(system duration, via `scripts/analyze_lmp_residual.py`).

**System level + duration ($/MWh):**

| year | model avg | actual RT | actual DA | resid RT | p50 m/a | p90 m/a | p99 m/a | max m/a |
|---|---|---|---|---|---|---|---|---|
| 2023 | 41.79 | 30.29 | 31.11 | +11.50 | 36/26 | 66/42 | 104/120 | 236/1147 |
| 2025 | 69.24 | 60.73 | 60.71 | +8.51 | 57/45 | 114/114 | 157/222 | 314/2074 |

**Per-zone average (model vs actual DA, resid $/MWh):**

| zone | 2023 model | 2023 actDA | Δ | 2025 model | 2025 actDA | Δ |
|---|---|---|---|---|---|---|
| Upstate_West | 38.94 | 26.08 | +12.86 | 66.82 | 55.89 | +10.93 |
| Capital_Hudson | 43.42 | 36.38 | +7.04 | 70.61 | 65.15 | +5.46 |
| Lower_Hudson | 43.42 | 33.58 | +9.84 | 70.61 | 62.99 | +7.62 |
| NYC | 43.42 | 33.95 | +9.47 | 70.61 | 65.41 | +5.20 |
| Long_Island | 43.42 | 40.77 | +2.65 | 70.61 | 68.87 | +1.74 |

**Reading.** Both years **over-price the mid-merit band** (2025 p50 $57 vs $45)
and **under-price the scarcity tail** (2025 p99 $157 vs $222; max $314 vs
$2,074) — the no-ORDC / no-reserve-scarcity signature (the model carries no
scarcity adder). The 2025 p90 is near-exact ($113.7 vs $113.6). The model
collapses the four downstate zones to one price: it captures the upstate-cheap
/ downstate-dear separation (Upstate_West ≈ $4 below downstate) but not the full
actual J−A spread (≈$13), the documented interface-TTC / downstate-congestion
structural item (U7). Long_Island is the closest zone both years (+$1.7/+$2.7);
the over-pricing is heaviest upstate, consistent with the gas-level floor
sitting above measured upstate LBMP. Per-run detail in the bundle's
`SUMMARY-nyiso-2025-refreshed.md` / `PRICE-RESCORE-*`.

### Discipline & scope

Structural-discipline run (playbook §6): **no offer band tuned**. oil stays
**U4-gated** (no Transco-Z6 / Iroquois daily gas basis uploaded for NYISO —
monthly-average Jan gas stays below distillate parity). **2024 stays blocked**
on `NY_2024` unit-level CEMS + the missing `NYISO_2024_renewable_capacity.csv`.
**ERCOT/PJM/CAISO/NEISO untouched** — the only data change is the `NYIS hourly`
parquet, whose 2023/2024 content is byte-identical pre/post; loader/demand/
renewables tests pass (the 3 CAISO zonal-share failures are pre-existing and
unrelated, per the P9b note). doc-00 status table updated (NYISO now 2023+2025,
price-scored); dashboard carries the run; `docs/multi-iso/nyiso-backcast-2023.md`
and `docs/calibration-best-so-far-nyiso.md` updated with the 2025 results and
the now-scored price metrics.

## ERCOT Runs 93–96 — retune on the corrected fleet (2026-06-12)

**Campaign: re-derive the offer-curve calibration on the post-Kiamichi
fleet (run 92's open item) and name a keeper that beats run 92's 6 class
fails on both gates with no regression. Method: measured probe vectors
(runs 93/94/95/95b — every live lever priced as a pure response vector vs
`run92_kiamichi`), then ONE keeper run (96) with doses solved against the
measured constraint system. Runs 95 and 95b ran in parallel (rule #11);
95b from a sparse git worktree pinned at HEAD so 95's Kiamichi bins edit
could not contaminate it (the bins CSV is re-read per year mid-run).
Result: run 96 = run 92 + a single lignite-floor move, 5 fails,
both gates held — the keeper.** All TWh below are model − benchmark vs
`run92_kiamichi` unless said otherwise; scoring is the size-aware bar +
fuel-split gate of `calibration-best-so-far.md`; LMP is the energy-only
monthly demand-weighted MAE (gate ±$1 of 32.1/7.3/2.2).

### The measured vectors (TWh per unit dose, vs run 92)

| cell | V_CC (93: CC econ_high −0.40→−0.30) | V_CT (94: CT econ_high +0.20→−0.20 + Kiamichi trim v1) | V_floor (95−94: lignite floor 0.75→0.69 + Kiamichi v2) | V_CCc (95b: CC committed −0.05→+0.05) |
|---|---|---|---|---|
| CC 23/24/25 | −2.68/−2.16/−2.15 | −0.24/−0.25/−0.21 | −0.36/−0.40/−0.02 | −2.12/−1.63/−1.51 |
| PRB 23/24/25 | +1.41/+0.91/+0.61 | −0.02/−0.11/0.00 | −0.16/−0.15/−0.00 | +0.83/+0.47/+0.45 |
| ST_GAS 23/24/25 | +0.20/+0.15/+0.35 | −0.19/−0.13/−0.16 | −0.02/−0.03/−0.00 | +0.20/+0.20/+0.25 |
| LIG 23/24/25 | +0.26/+0.23/+0.03 | 0.00/−0.01/−0.00 | **+0.62/+0.71/+0.04** | +0.22/+0.19/+0.02 |
| CT 23/24/25 | +0.01/+0.01/+0.12 | +0.45/+0.49/+0.36 | 0.00/+0.01/−0.00 | +0.06/+0.07/+0.08 |
| 2023 coal split (from +1.5%) | +2.7 | ~0 | +0.7 | +1.7 |
| ML/LS 2023 guard (from 582/797 GWh) | +582/+287 | ~0 | **−67/−28** | +339/+194 |
| LMP (32.06/7.29/2.17) | held | held | held | ≤$0.12 — lever NOT price-aborted |

**Run 93 (`run93_jacobian_probe`, prior session).** CC econ_high give-back
full dose: ~3× the stale pre-Kiamichi jacobian; FAILS 2023 at β=1 (coal
split +4.2%, guards 1164/1084) → β ≤ 0.37 on the split, ≤ ~0.71 on guards.

**Run 94 (`run94_ct_kiamichi`, prior session).** CT recovery γ=1 leaves CT
failing all years and flips ST_GAS 2025 to a NEW fail (−1.15 vs the −0.99
knife-edge pass); Kiamichi cost-side trim v1 (20/65/15, econ HR 1.06,
committed in inputs) moved Kiamichi only −0.12/−0.14/−0.18.

**Run 95 (`run95_lignite_probe`, this session).** Lignite-floor endpoint
probe (0.69 = 2× the 0.72 candidate) on the run-94 base + Kiamichi bins v2
(peaking 15→30). Findings: (a) the floor vector flips lignite 2024
(−1.66 → −0.96) with mild PRB intra-coal steal (−0.15) and +0.7 split
leakage; (b) guards IMPROVE (ML23 582→515 — the floor redistributes
lignite toward the non-guard plants); (c) **Kiamichi v2 is a dead lever**:
6.06/6.85/6.17 → 6.03/6.77/6.17 TWh — the over-run is bid-price-driven,
not capacity-bound; withheld capacity doesn't bind. v2 NOT committed
(inputs stay at the run-94 v1 trim).

**Run 95b (`run95b_cc_committed_probe`, this session).** CC_REGULAR
committed pure pair on the run-92 base, one clean +0.10 step (a measured
endpoint extends the trust region — the run-82 lesson was extrapolating,
not probing). The lever works mechanically (CC sheds −2.12/−1.63/−1.51;
Kiamichi itself sheds 0.40–0.62 — the class-wide committed multiplier
prices its 20% committed tranche; LMP barely moves) **but the 2024 refill
is too dilute**: +0.47 PRB / +0.20 ST_GAS per unit vs the +1.53/+1.40
those flips need, while the costs scale fast (2023 coal split +1.7/unit —
95b itself FAILS the 2023 gate both fuels at δ=1 — guards +339/+194,
gas 2023 −0.7%). **The 4-fail path is measured dead**: within the split
budget (0.7λ + 1.7δ + 2.7β ≤ 1.0 from +1.5) a δ of ~0.2 buys +0.09 PRB
2024 — an order of magnitude short. "Realistic best ≈ 5 fails" confirmed.

### Run 96 — the keeper (`run96_lignite_keeper`, dashboard `run96 lignite keeper`)

Doses solved smallest-first against the constraint system: **λ=1 (lignite
floor 0.69, the measured endpoint), β=γ=δ=0.** γ flips nothing (CT 2023
needs γ≥1.16, blocked by ST_GAS 2025 and partly structural — the IMM 2023
SOM AS-deployment wedge, see the ORDC entry: do NOT chase the last
~1–1.5 TWh of CT with fleet-wide levers); β and δ eat the 2023 coal-split
budget the floor needs (any β>0 at λ=1 breaches +2.5%); δ at the allowed
~0.2 buys only cosmetics. So the keeper is run 92 + one knob. Measured:
**5 in-scope fails vs run 92's 6** — lignite 2024 −1.66 → **−0.95 PASSES**;
remaining: CT_PEAKER −1.51/−2.54/−1.74, PRB 2024 −8.8%, ST_GAS 2024 −2.41.
No new fails, no regressions: ST_GAS 2025 −0.99 (0.01 margin) holds, CC
2023 −1.6%, PRB 2024 drift −3.71→−3.85 inside an already-failing cell
(size-aware noise, run-91 precedent). Splits: 2023 −2.1/+2.3 PASS, 2024
coal −8.3% (improved from −9.3, still the structural residual), 2025 PASS.
Guards ML/LS 2023 546/773 (better than run 92); ML 2025 +1.46 (watch).
LMP MAE 32.06/7.31/2.17 — identical to run 92. Kiamichi 6.04/6.78/6.17 vs
~5.2 actual (within-class watch). PRB mean +1.3/−8.8/−0.1 → −2.5%.
`calibration-best-so-far.md` rewritten (OPEN status cleared).

### ORDC overlay follow-through

`derive_ordc_overlay.py run96_lignite_keeper --revenue-report` (post-solve,
no LP): **the ORDC baseline bundle moves from run92_kiamichi to the
keeper**; `availability.parquet` + `scarcity.parquet` committed in the
bundle. Tail metrics next to the energy-only gate numbers: 2023 MAE
32.1 → **28.0** (>$200 hours 0→31 vs 181 actual, >$500 0→15 vs 104, max
adder $3,131, Jun–Sep $·h gap 12% closed); 2024 7.3 → 7.9 and 2025
2.2 → 2.2 hold the ±$1 gate (adder >$1 in 163/28/4 h). Revenue direction
sane and ordered: CT_PEAKER 2023 +84%, storage discharge +169%, ST_GAS
+46%, CC +20%, wind +9%; 2025 ≈ +0%.

### Bookkeeping

Jacobian: runs 91–96 classified in the deriver REGISTRY (91→91055 pure,
92 structural fleet fix, 92→93 pure, 94/95 sidecars so the chain pairs
93→95b — pure, the corrected-fleet committed step; 96 structural) →
**12 ERCOT pure pairs** in `inputs/processed/offer_curve_jacobian.csv`
(committed). Dashboard keeps 5 ERCOT runs: 92, 94, 95, 95b, 96 (95 pruned
90; 95b pruned 91; 96 pruned 93 — probe vectors live here + in the
sidecar definitions). Probe sidecars marked "MEASURED PROBE, not a
keeper" with their response vectors. Dead levers measured this campaign
(do not re-probe): Kiamichi capacity withholding (v2), CC committed at
meaningful dose (split/guards), CT econ_high beyond the ST_GAS-2025
budget, plus the prior list (CT/ST_GAS peak bands, CT committed,
Kiamichi cost-side nudges).

## ERCOT Runs 97a/97b — per-plant retune + the BTM vintage fix (2026-06-13)

**Campaign: the runs 93–96 retune exhausted the class-wide offer-curve
dose space at 5 fails, so this session localized the remaining fails to
plants (the run-96 bundle's per-plant panels) and fixed what was honestly
fixable. Result: run 97a is the keeper — 4 in-scope fails, both gates, no
regressions, every remaining fail structurally diagnosed. The probes ran
in parallel (97a gas-side in the main tree, 97b coal-side in a sparse
worktree, both off the run-96 config).**

### The per-plant decomposition (run 96 bundle, model − CAMPD/923)

- **ST_GAS 2024 (−2.41) is not diffuse**: V H Braunig −3.2 (and −2.5/−3.7
  in 2023/25!), O W Sommers −0.8, Cedar Bayou −1.1 — the CPS San Antonio
  self-scheduled steamers — offset by over-run elsewhere in the class.
- **PRB 2024 (−3.85) is one plant**: W A Parish −3.7 (Spruce −1.6, offset
  by over-runners). Parish is never off (8,760 CAMPD op-hours every year,
  p10 ≈ the model's 15% floor — the floor is right), median 38–45% of cap
  in 2023/24; it has NO plant-specific F923 coal price (class fallback).
- **CT_PEAKER decomposes three ways**: (1) San Jacinto (7325): bins call it
  CT_PEAKER but it behaves as a refinery cogen (flat ~50% CF; EIA-923 says
  chp=N so the dominant-class override pins the class); its 65% must-run
  share is BTM-removed and added back from the plant's 923 netgen — which
  the incomplete 2025 vintage lacks entirely, zeroing 0.86 TWh of add-back
  while the CAMPD-backfilled benchmark keeps the plant. The CT 2025 "fail"
  was this artifact. (2) ~1.0 TWh/yr of bench sits in non-CEMS small
  peakers (Ector County 649 vs 119 GWh, Permian Basin 460 vs 47, Pearsall,
  …) the merit order can't reach. (3) Of the CEMS-covered CT energy, 31/38/
  44% (2023/24/25) ran in hours with RT price below the unit's marginal
  cost — the AS/RUC deployment + RA wedge, 1.4–2.3 TWh/yr, quantifying the
  IMM-documented structure flagged in the ORDC entry. The model already
  matches CEMS for CAMPD-covered CT plants (2024 model 5.03 vs 5.38 CEMS).
- **Bonus: Sand Hill (7900)** — a CC+CT site flattened to one 7.37-HR
  CC_REGULAR bin, model 3.61 vs 2.13 TWh actual in 2024 = a third of the
  CC 2024 over-run. Its CT capacity dispatches at the CC heat rate.

### Run 97a (`run97a_gas_plants`) — KEEPER, 4 fails

Run-96 config + (1) `--btm-backfill-year 2024` — new flag, mirrors
`--hydro-backfill-year`: a plant whose (plant, class) 923 total is zero
for the year borrows the prior year's, ONLY if CAMPD shows it generating
(CEMS-silent cogens stay dropped on both sides). Measured: CT_PEAKER 2025
BTM 0 → 0.85 (San Jacinto), CC_CHP +0.14, all else ~0 — surgical. (2)
Braunig + Sommers `Pct_Committed` 30 → 40. Measured: **CT_PEAKER 2025
−1.74 → −0.90 PASSES**; ST_GAS 2023 −0.31 → +0.06, 2024 −2.41 → −1.99
(still fails), 2025 margin −0.99 → −0.73; CC/PRB/lignite hold; splits
2023 −2.0/+2.1 PASS; guards 498/760 (best of the campaign); LMP
32.08/7.34/2.16 (gate held). Braunig/Sommers own-gain measured at only
+0.17 TWh each — the ST_GAS committed band carries the startup-spread
markup (Braunig startup 28.5 t CO2, ~12 starts/yr), so the committed-share
lever saturates: ST_GAS 2024 is not reachable representationally. The
Sand Hill committed/peaking CSV edit in the run note was a measured
**no-op** — `cc_committed_per_plant`/`cc_peaking_per_plant` override CSV
shares for CAMPD-covered CC plants (Kiamichi only takes CSV values because
it has no CAMPD extract) — reverted from inputs; per-plant CC surgery
needs `--plant-tranche-config` (follow-up).

### Run 97b (`run97b_coal_plants`) — REJECTED, the screen finding

Parish + Spruce `Pct_Committed` 20 → 30 (econ 50 → 40), the CAMPD-grounded
"self-scheduled baseload" representation. Measured BACKFIRE: PRB 2024
−3.85 → **−4.68** (−0.82), PRB 2023 +0.59 → +0.09, CC 2024 +0.41. The
mechanism: under `commitment_screen_coal` the committed band is screened
for run-length profitability — a bigger committed block that fails the
cheap-gas screen is decommitted wholesale, removing capacity the econ band
previously dispatched hour-by-hour. The coal committed-share lever is
measured DEAD for baseload recovery; Parish's wedge is the same
self-commitment/out-of-merit structure as the CT class. No inputs kept.

### Verdict + follow-ups

Keeper run 97a: 4 fails (CT 2023 −1.53 / CT 2024 −2.56 / PRB 2024 −3.94 /
ST_GAS 2024 −1.99), ties run 85's old 4-fail mark on the corrected fleet,
beats run 96's 5; `calibration-best-so-far.md` updated; ORDC overlay
re-derived on the keeper (2023 MAE 32.1 → 28.0, 2024/25 hold ±$1; baseline
bundle moves run96 → run97a; availability+scarcity committed in-bundle).
All four remaining fails share one structure: **self-committed /
AS-deployed energy the energy-only merit order cannot dispatch** — the
candidate mechanism is an explicit deployment overlay built from measured
out-of-merit CEMS hours (run ≥ X MW while RT < marginal cost), analogous
to the historic outage overlay; that is a methodology change needing user
sign-off. Other follow-ups: Sand Hill per-plant tranche config (~1.5 TWh
of CC 2024 over-run), Cedar Bayou, NP6-576-ER μ/σ (ercot.com still
egress-blocked, 403, retried 2026-06-13). Forecast note: the kept changes
are fleet representation (bins committed shares) and a backcast reporting
flag — the bins edits flow into forecast mode; the flag is
backcast-reporting only and changes no dispatch.

### Bookkeeping

Dashboard: 97a/97b registered; retention prunes run92 + run94 entries
(bundles stay; run92 remains the documented baseline in this log).
Jacobian REGISTRY: 96 → 97a and 97a → 97b classified structural (bins/
reporting, no curve knobs) — 12 ERCOT pure pairs unchanged. New dead
levers (do not re-probe): coal `Pct_Committed` raises under the commitment
screen (97b), ST_GAS committed-share beyond ~+10 pts (startup-spread
saturation, 97a), per-plant CC CSV shares for CAMPD-covered plants (the
override no-op).
## NEISO offer-curve probe panel + Jacobian — P12 keeper sensitivity map (analysis only) (2026-06-13)

**Runs `neiso_probe_base_2024` + 10 single-knob probes; dashboard `neiso 8
probe-cc-eh-plus` / `neiso 9 probe-cc-eh-minus` (9 dominated entries registered
then pruned per the top-5 rule; all 11 bundles kept on disk).** Goal: map the
offer-curve band sensitivities around the NEISO P12 primary-year keeper
(`neiso_p12_base_2024`) to inform any future refinement. **The keeper is NOT
re-tuned** — zero changes to the sign-off config; ERCOT/PJM/CAISO untouched
(their `offer_curve_jacobian.csv` rows byte-identical).

### Panel design

`neiso_probe_base_2024` re-runs the P12 keeper config on current main
(run80a-style code-accumulation anchor): it reproduces the keeper **exactly**
(identical per-class TWh and $57.06 demand-weighted price), so no NEISO code
drift since sha `6fbf83d` and probe deltas read directly against the keeper.
Ten ±0.05 single-knob probes chain off it via `--offer-curve-delta-json`
(each consecutive bundle pair is a verified pure-curve observation; REGISTRY
entries added to `scripts/derive_offer_curve_jacobian.py`, plus the NEISO
state set for the merit-order adjacency check):

CC_REGULAR committed ±, CC_REGULAR econ_high ±, CT_PEAKER committed ±,
ST_GAS committed −, ST_GAS peak −, CC_CHP committed −, CT_CHP committed −.

**No OIL band exists to probe.** `fossil_classes()` carries no OIL/ST_OIL
offer-curve class: the oil-primary steam fleet (Wyman, Canal, …) dispatches
under the non-fossil `oil` class with no band knob, and the dual-fuel CT/ST
gas tranches live in CT_PEAKER/ST_GAS. The ST_GAS probes are therefore the
panel's oil/dual-fuel coverage — and they are **dead knobs** (below).

### Knob → objective map (Jacobian, 10 pure pairs, year 2024)

`python scripts/derive_offer_curve_jacobian.py --iso NEISO --baseline
neiso_p12_base_2024 --validate-run neiso_probe_base_2024` → 70 NEISO cells in
`inputs/processed/offer_curve_jacobian.csv`. High-confidence rows:

| knob | twh (own) | twh (cross) | lmp d(MAE)/d(mult) | shape d(gas NRMSE) |
|---|---|---|---|---|
| CC_REGULAR.econ_high | CC_REGULAR −1.47 ±0.09 | CC_CHP +0.37, CT_PEAKER +0.12 | **+5.4 ±0.7** | −0.0046 |
| CC_REGULAR.committed | CC_REGULAR −0.27 ±0.03 | CC_CHP +0.08 | +2.1 ±0.8 | −0.0019 |
| CT_PEAKER.committed | CT_PEAKER −0.09 ±0.01 | CC_REGULAR +0.07 [low] | +0.02 [low] | +0.0004 |
| CC_CHP.committed | CC_CHP −0.20 [med] | CC_REGULAR +0.18 [med] | −0.02 [low] | ≈0 |
| ST_GAS.committed / .peak | **0 — dead** | 0 | 0 | 0 |
| CT_CHP.committed | +0.06 [low, n=1] | — | — | — |

Reading: **NEISO's TWh block is essentially band-immune.** The largest
sensitivity (CC_REGULAR.econ_high, −1.47 TWh/unit-mult) moves only ±0.07 TWh
at the ±0.05 probe size — with no coal and a trivial CT/ST fleet, the CC class
has no substitution partner and band moves just relabel its own price. Every
cross-coupling is merit-order-adjacency-consistent (overlap mass >99%). The
real leverage is on the **price level**: econ_high ±0.05 moves the
demand-weighted level ∓±~$1/MWh annual; committed ~40% of that.

### Winter-tail caveat (Jan/Feb LMP sensitivity is U4, not a band)

The econ_high price response is **winter-loaded ×2–3** (±0.05 → Jan ∓±2.2,
Feb ∓±1.4, Dec ∓±1.4 $/MWh vs ∓±0.4–0.9 mid-year): in Jan/Feb the marginal
unit is almost always CC_REGULAR on the **monthly** AGT basis, so a band
multiplier scales the documented flat winter plateau up or down. **Do not
read this as a winter-tail knob.** The price re-score attributes the winter
miss to the monthly-AGT limitation (plateau instead of daily-spot spikes;
model never clears an hour >$200 vs 44/11/160 actual) — a multiplier on a
flat plateau cannot manufacture daily variance, and the dead ST_GAS knobs
confirm no band brings the dual-fuel/oil fleet into the winter merit order
(even cheapened −0.05 it never clears; modeled oil stays 0.006 TWh). The fix
remains the **daily-AGT U4 upload** (doc-08 decision 1; P11 gap #3). Equally,
the CHP TWh "errors" (CC_CHP −0.69, CT_CHP −0.79 vs 923) are mostly the
grid-side BTM-host convention (gas vs EIA-930 is green at −2.8%), not
band-tunable — the recipe's no-btm.parquet warning applies.

### Joint-move recipe + backtest

- Default solve (balanced twh/shape/lmp, cap 0.15): **every knob
  trust-region-frozen, no move** — the solver wants extrapolations far outside
  the ±0.05 sampled range to chase structural (U4 / BTM / served-interchange)
  error. The trust region vetoing it is the correct answer.
- Capped to the sampled range (`--cap 0.05`): Δ = {CC_REGULAR committed −0.05,
  econ_high −0.05; CT_PEAKER committed +0.05; ST_GAS committed −0.045, peak
  −0.05} with predicted twh RMS 0.671→0.649, LMP MAE 18.41→18.08 $/MWh, shape
  slightly degrading. **Immaterial vs the 18.4 structural LMP residual — not
  promoted.** It also chases the 2023/24 over-pricing sign: 2025 under-prices
  (−12.5 $/MWh re-score), so the same move worsens 2025. That sign flip is the
  gas-price/U4 asymmetry, knowable from the re-score without new panels —
  2023/2025 panels skipped (the TWh block, which is what a panel uniquely
  measures, showed nothing tunable; LMP-block transfer would only re-measure
  the same plateau scaling).
- Backtest (held-out `neiso_probe_cc_regular_committed_minus`, excluded from
  the fit then predicted): TWh block prediction-error RMS **0.001 TWh**
  (CC_REGULAR +0.012 pred vs +0.013 actual); LMP −0.142 pred vs −0.094 actual
  (the up/down asymmetry of a one-sided fit); the trust region correctly
  flags the held-out one-sided move as outside the remaining sampled range —
  the run-82 regression behavior reproduced for NEISO.

### Verdict

No offer-band refinement is recommended for NEISO: the P12 structural-defaults
keeper stands. The panel's value is the fitted sensitivity matrix (any future
NEISO band discussion starts from "econ_high is the only live knob, it prices
the U4 plateau, and TWh is band-immune") and the dead-knob proof for the
oil/dual-fuel path. Reproduce a probe:
`python scripts/run_calibration_full.py --iso NEISO --year 2024 --commitment
--offer-curve-delta-json '{"CC_REGULAR":{"econ_high":-0.05}}' --out-dir
results/calibration/neiso_probe_cc_regular_econ_high_minus`.

---

## CAISO 3 — offer-curve probe panel + Jacobian (sensitivity map, 2023) (2026-06-13)

**Goal: map CAISO offer-curve band sensitivities to inform calibration — NOT a
tuning pass.** No keeper config is changed; no band move is committed. The
panel quantifies which knobs do what *under the current structural state*, and
that state includes the **OPEN import-tranche mis-pricing (P9/P12)**: the
priced WECC node over-imports +114%/2023 and owns the $45–90 margin (CAISO 2
entry above). Every number below is conditional on that — re-probe after the
re-price.

### Panel design

12 bundles, 2023 only (the keeper-designate `caiso_1_priced_ix` covers
2023-2025; 2023 confirmed as its first dispatch year), all
`run_calibration_full.py --iso CAISO --year 2023 --commitment`:

- **`caiso_probe_base`** — zero-delta code baseline. HEAD had moved 87
  src/inputs files since `caiso_1_priced_ix`'s sha (`a1dc6e2`), so probes
  paired against the old bundle would auto-classify structural; the re-run
  reproduces its 2023 numbers exactly (avg price $77.34, 0 negative hours) —
  the code drift is CAISO-inert, but the chain discipline stands
  (run80a pattern).
- **11 single-knob ±0.05 probes** chained off it (dashboard `caiso 3` +
  `3a–3k`; bundles `results/calibration/caiso_probe_<class>_<band>_<sign>`):
  CC_REGULAR committed −/+ (both signs; the + side run last and **held out**
  for the back-test), econ_low −, econ_high −, peak −; CT_PEAKER committed −,
  econ_low −; ST_GAS committed +, econ_low +; CC_CHP committed −; CT_CHP
  committed −. CAISO has no coal fleet to speak of (COAL 0.39 TWh model, ~0
  benchmark) — **COAL_* knobs skipped**. All pairs classify pure
  (scenario-config-identical, clean `src/ inputs/ data/` git diffs, single
  Δknob each); REGISTRY entries added to `derive_offer_curve_jacobian.py`.
  Solver note: each 8760 h commitment solve peaks ~8 GB — run probes
  sequentially on a 15 GB box (a 2-parallel attempt was OOM-killed).

### Raw panel (ΔTWh vs probe base, 2023; Δavg-price $/MWh)

| probe (Δmult) | CC_REG | CC_CHP | CT_CHP | CT_PK | ST_GAS | **import** | Δprice |
|---|---|---|---|---|---|---|---|
| CC.committed −0.05 | **+0.84** | −0.15 | −0.23 | 0.00 | −0.12 | **−0.28** | −1.21 |
| CC.econ_low −0.05 | **+0.59** | −0.05 | −0.13 | 0.00 | −0.11 | **−0.30** | −0.69 |
| CC.econ_high −0.05 | **+0.50** | −0.04 | −0.10 | 0.00 | −0.13 | **−0.25** | −0.55 |
| CC.peak −0.05 | −0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| CT_PK.committed −0.05 | 0.00 | 0.00 | 0.00 | **0.00** | 0.00 | 0.00 | 0.00 |
| CT_PK.econ_low −0.05 | −0.00 | −0.00 | −0.00 | +0.01 | −0.00 | −0.00 | −0.03 |
| ST_GAS.committed +0.05 | 0.00 | 0.00 | 0.00 | 0.00 | **0.00** | 0.00 | 0.00 |
| ST_GAS.econ_low +0.05 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| CC_CHP.committed −0.05 | −0.15 | **+0.22** | −0.02 | 0.00 | −0.01 | −0.03 | −0.18 |
| CT_CHP.committed −0.05 | −0.20 | −0.03 | **+0.29** | −0.00 | −0.01 | −0.04 | −0.13 |
| CC.committed +0.05 (held out) | **−0.83** | +0.13 | +0.22 | 0.00 | +0.11 | **+0.29** | +1.07 |

Two structure-level reads, before any regression:

1. **The import node is the counterparty to every live knob.** 30–50% of the
   energy a CC_REGULAR band move shifts comes out of (or goes back into) the
   import node, not other gas classes. The Jacobian's class-TWh matrix can't
   show this (import is not a tuned class); it shows up as own-knob
   sensitivities being ~40% larger than the sum of cross-class gains.
2. **Most non-CC knobs are dead.** CT_PEAKER (0 TWh dispatched at base vs 4.15
   TWh EIA-923), CC_REGULAR.peak (34 MWh moved — i.e. nothing), and both
   ST_GAS knobs (+0.05 moved nothing because ST_GAS's 1.7 TWh sits in hours
   where the next import tranche, not ST_GAS, is marginal). The merit-order
   adjacency check confirms the bands overlap the clearing-price mass
   (78–89% for CT_PEAKER/ST_GAS bands) — the knobs are *price-relevant on
   paper* but the 11.4 GW import stack absorbs the substitution.

### Jacobian (twh block, 2023, TWh per unit multiplier; med = |coef| > 2·jackknife-SE would be high, n_obs caps at 2 for single-knob chains)

| knob | own-class | strongest cross | confidence |
|---|---|---|---|
| CC_REGULAR.committed | **−14.7** | CT_CHP +4.1, CC_CHP +2.8, ST_GAS +1.9 | med |
| CC_REGULAR.econ_low | **−9.0** | CT_CHP +2.1, ST_GAS +1.7, CC_CHP +0.7 | med |
| CC_REGULAR.econ_high | **−7.3** | ST_GAS +2.0, CT_CHP +1.5, CC_CHP +0.6 | med |
| CT_CHP.committed | −4.4 | CC_REGULAR +2.9 | low (n=1 after hold-out) |
| CC_CHP.committed | −3.6 | CC_REGULAR +2.2 | med/low |
| CC_REGULAR.peak | (+1.9) | — | **low — measured ≈0, coefficient is ridge noise** |
| CT_PEAKER.committed / econ_low | ≈0 / −0.09 | — | dead knobs |
| ST_GAS.committed / econ_low | +0.24 / +0.21 | — | low; dead knobs |

Shape block: only `gas` NRMSE is meaningful for CAISO —
CC_REGULAR.committed d(NRMSE)/d(mult) +0.157 (med), i.e. lowering CC committed
*improves* the EIA-930 gas shape slightly while it adds gas TWh. The `coal`
NRMSE rows are junk (EIA-930 CAISO coal ≈ 0.01 TWh ⇒ near-zero NRMSE
denominator; baseline "coal NRMSE" 28.8) — they inflate the shape-block scale
and thereby mute the block in the recipe weighting; verified the recipe is
**identical with `--w-shape 0`**, so no harm this pass, but a CAISO shape fit
should filter the coal series. **LMP block: empty** — `actual_lmp.json`'s
CAISO block covers 2024/2025 only (no 2023 `rt_mon`), so price-level
sensitivities are unscored at the panel year; the per-probe Δavg-price column
above is the available evidence (CC committed: ∓$1.1–1.2/MWh per ±0.05).

### Back-test (held-out pair)

`--exclude-pair caiso_probe_cc_regular_committed_plus --backtest
caiso_probe_base caiso_probe_cc_regular_committed_plus`: prediction-error RMS
**0.039 TWh** against an actual-change RMS 0.357 (CC_REGULAR pred −0.74 vs
actual −0.83; CT_CHP +0.20 vs +0.22; CC_CHP +0.14 vs +0.13; ST_GAS +0.10 vs
+0.11). The ±0.05 neighbourhood is linear and near-symmetric
(+0.842/−0.829 TWh for ∓0.05 committed). The trust region correctly flags the
+0.05 endpoint as outside the minus-side-only sampled range.

### Joint-move recipe — reported, NOT applied

`--cap 0.05` (so every step stays inside the sampled trust region):
**CC_REGULAR committed/econ_low/econ_high −0.05 each, ST_GAS econ_low +0.05**;
predicted CC_REGULAR error **−21.05 → −19.47 TWh** (twh-block RMS 9.125 →
8.550), gas shape NRMSE −0.01, CHP classes degrade slightly (CC_CHP −6.24 →
−6.44 grid-only). At the default ±0.15 cap every knob trust-region-freezes at
the ±0.05 sampled edge — the correct conservative answer.

### What the Jacobian CANNOT fix (the structural caveat, quantified)

The maximal in-trust-region joint move buys back **1.6 of the 21.0 TWh**
CC_REGULAR deficit. The deficit is not a band problem: it is the
import-displacement gap (CAISO 2 gap #2 — the mis-priced WECC tranches
over-import ~+33 TWh/2023 and displace gas one-for-one). Pushing bands harder
would (a) extrapolate outside every sampled range, (b) claw energy mostly out
of the import node — i.e. *paper over the import gap with offer-curve error*,
the exact compensating-error failure the playbook §6 discipline exists to
prevent — and (c) still leave CT_PEAKER at zero, since no ±0.05 band move
revives a class the import stack has fully crowded out. Likewise the price
level (2023 biased high, zero negative hours) belongs to the import node:
$0.5–1.2/MWh per capped band move is an order of magnitude short of the gap,
and the missing midday negative-price regime is an export-sink/tranche-price
feature, not an offer-band one. **Owner: P9/P12 import-tranche re-pricing.
After it lands, re-run this exact panel off a fresh code baseline and diff the
two Jacobians** — CT_PEAKER/ST_GAS/peak knobs waking up and the CC→import
coupling shrinking is the merit-order-level acceptance check that the re-price
worked.

### Scope & artifacts

Sensitivity-mapping pass: **no calibration keeper committed; keeper configs,
`config/`, `src/` dispatch math untouched; ERCOT/PJM/NYISO/NEISO untouched**
(Jacobian CSV is additive — 80 new CAISO cells, other ISOs' rows byte-equal;
ERCOT/PJM fits not re-run). Dashboard: `caiso 3 probe-base`, `3a`
(strongest live knob), `3k` (held-out back-test) registered; the 9 dominated
single-knob entries were registered then pruned per the 5-run retention
(`caiso 1`/`caiso 2` retained; all 12 bundles kept under
`results/calibration/caiso_probe_*`). Jacobian:
`inputs/processed/offer_curve_jacobian.csv` (iso=CAISO, year=2023) +
REGISTRY/ISO_STATES entries in `scripts/derive_offer_curve_jacobian.py`.
