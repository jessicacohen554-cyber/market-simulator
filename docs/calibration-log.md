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
