# PRECOMMIT — SPP-74, THE BODY: where does the rung's ordinary-hour / whole-month price error live?

**Zero LP. Pushed before any decomposition number below was read.** Base: `origin/main` @
`fbe00eb1a2626a44fd8096da6d1abce1f6374a90`. DATA PROFILE: spp. Predecessor:
`docs/handoffs/RESULT-spp-73-commitment-reach-2026-09-22.md` (commitment reach NOT the cause; not
re-opened). Demand (SPP-72), reserve (SPP-55), offer-curve band family (xiso) not re-opened.

## 0. State read before this file was written (NOT pre-registered as findings)

- **The keeper moved after the brief was written.** `keepers/SPP.json` now designates
  `2026-09-22-hydro-5-spp-floor` (bundle `hydro5_spp_floor_span`, 2023–2025, CALIBRATED), with
  the rung `2026-09-22-hydro-5-spp-rung` (`hydro5_spp_floor_rung`, 2019–2022, NOT-YET) stamped
  to it. Single delta on SPP-71's keeper 15: `hydro_min_flow_floor=true`. The spp71 bundles are
  pruned. **This lane measures the CURRENT rung/keeper.**
- `calibration_verdict.py --run-id 2026-09-22-hydro-5-spp-rung` → NOT-YET. Failing rows:
  **C3a 2020 +15.5 %** (19.08 vs 16.52); **C3b 2020 / 2021 / 2022 = 0.257 / 0.234 / 0.208**;
  plus two rows the brief did not list, new on the hydro-5 rung: **C1 COAL_PRB 2022**
  (+9.60 TWh, band ±8.00) and **C2 gas 2022** (NRMSE 0.321, band 0.30). The keeper span
  (`2026-09-22-hydro-5-spp-floor`) reads CALIBRATED, C3c the only caveat.
- Schema only (no values): `spp_zonal_gas_hub.csv` is ANNUAL basis, not monthly; the monthly
  published SPP-area series are EIA `N3045KS3` / `N3045OK3` (natural gas delivered to electric
  power consumers, $/Mcf) in `data/raw/gas-prices/eia_delivered_gas_{KS,OK}_monthly_2019-2022.csv`,
  plus `henry_hub_monthly.csv`. The rung's run_config arms `gas_seasonality`,
  `gas_plant_monthly_fuel_pricing`, `nearby_fuel_price_fallback`, `gas_price_override` 2.03 (2020).
- Matrix cells already read: `negative_renewable_offers` **I** and `wind_ptc_vintage_offers` **I**
  (SPP-51b: wind's offer is already −$26.000 and wind sits at its upper bound in 99.9 % of
  hours); `gas_monthly_actuals` / `gas_daily_shape` **U** with the SPP price-family note that
  measured monthly price correlates with KS/OK gas at only +0.27 vs the model's +0.70.

## 1. The instrument (the scorer's, reproduced)

Model hourly price `p_h` = P1 zonal price demand-weighted across zones from the committed
`hourly/system_<y>.parquet` (`_spp73_commitment_reach.model_price_demand`, re-pointed at the
hydro-5 bundles). Actual `a_h` = measured `rt` on the model clock (SPP-72 `model_clock_index`).
Month m, the scorer's month error:

  **e_m = Σ_{h∈m} (d_h / D_m) p_h − RT_m**  (RT_m = committed `bench.avgLMP.rt_mon[m]`)

Exact additive split: **e_m = B_m + Σ_k S_{m,k}**, where
`B_m = Σ (d_h/D_m) p_h − (1/N_m) Σ p_h` (basis term: demand-weighted vs equal-hour model), and
`S_{m,k} = (1/N_m) Σ_{h∈m, h∈k} (p_h − a_h)` over hour-type k, plus a reconciliation term
`(1/N_m)Σa_h − RT_m` reported (should be ~0; SPP-73 reproduced to $0.005). C3a is the same with
m = the year. Gate: the instrument must reproduce the four scored values to ±0.002 NRMSE /
±0.2 pp before any split is quoted.

**Hour-types k (fixed now):** by measured `a_h` —
`NEG` (a ≤ 0), `LOW` (0 < a ≤ 10), then the remaining hours in within-year RT terciles
`MID1`, `MID2`, `HIGH`, with `TOP` = SPP-73's H_top (top-88 by RT) carved out of HIGH.

## 2. Row ownership rule (fixed now; diagnostic counterfactual, NEVER an input)

For object X occupying hour-set H_X: recompute the row with `p_h := a_h` on H_X (the object's
hourly error removed) — a DIAGNOSTIC only (rule 13: never a model input).
- **OWNS** the row iff removing X alone brings it inside its band.
- **CONTRIBUTES** iff it removes ≥ 50 % of the excess over the band (C3b: NRMSE − 0.20;
  C3a: |pct| − 10) without passing.
- otherwise **MINOR**. A negative reduction (row worsens) is reported as **OPPOSES**.

## 3. The four measurements

**(a) LOW SIDE (R-be).** Per month of 2020 and 2022: count measured RT hours `< 0` and `< −26`,
and model hours `< 0` and at the clamp (`p_h ≤ −25.99`); report `S_{m,NEG}`, `S_{m,LOW}`.
Object (a) = H_NEG ∪ H_LOW. Admissibility reading: (a) is a **measured, forward-reproducible
input the model gets wrong** only if model hours at/below zero are materially fewer than RT's
AND the cause is traceable to a named input (wind availability/curtailment, the −26 clamp,
must-run floors) — NOT merely "RT went negative and the model didn't".

**(b) MARGINAL FUEL (quantity vs level).** Reuse SPP-70's validated merit-order reconstruction
(`_spp70_meritorder_counterfactual.clear`, `reconstruct_bundle_fleet`, one interpreter per year)
on the hydro-5 rung for 2020 and 2022. Gate: reproduction r and mean error reported per year;
a split is quoted only where |mean err| ≤ $1.5. Per ordinary hour (MID1 ∪ MID2):
- marginal row class and `mc` at the model's served thermal `Q_mod` (class_hourly);
- `mc` on the SAME stack at the MEASURED thermal `Q_meas` = EIA-930 SWPP `COL+NG+OIL+OTH`
  (trap-(f) ceilings), i.e. **quantity term** `mc(Q_mod) − mc(Q_meas)` vs **level term**
  `mc(Q_meas) − a_h`. Monthly means of both.
- Verdict: Nov/Dec 2020 is **"gas marginal where cheaper supply was"** iff the quantity term is
  ≥ 50 % of those months' ordinary-hour error with the same sign; **"marginal mc too high"** iff
  the level term is.

**(c) FUEL-PRICE INPUT.** Model monthly delivered gas = capacity-weighted mean of
`fuel_prices[:, month]` over gas rows (reconstruction). Published: `N3045OK3` and `N3045KS3`
monthly, converted $/Mcf → $/MMBtu at 1.036 MMBtu/Mcf (EIA's published average heat content),
fleet-weighted 59 : 41 is NOT used — report OK, KS and their simple mean. Predicted price
effect: `Δgas_m × HR_marg,m` with HR_marg the capacity-weighted HR of the marginal gas rows from
(b). Object (c) **explains** a month iff that predicted effect is ≥ 50 % of `e_m` with the same
sign. Rule 14: both series derive from EIA-923 receipts; a gap between them is first an
aggregation question (plant-month vs state), and is never tuned to the residual.

**(d) CT OVERRUN.** Monthly model CT_PEAKER energy vs CAMPD SWPP-BA CT gross (SPP-73's
`campd_state` classifier, reused). Report the per-month overrun, its correlation with `e_m`
across 12 months, and whether the two largest-|e_m| months carry an overrun above the year's
median. Sign reading: CT running more ⇒ CT marginal more often ⇒ pushes price **up**.

## 4. Verdict rule

A body object is **REAL AND ADMISSIBLE** iff it (i) OWNS or CONTRIBUTES to ≥ 1 of the four rows
under §2, (ii) traces to a named measured, forward-reproducible input or structure whose model
value differs from its measured value, and (iii) is not on the DEAD list (commitment reach,
demand, reserve, offer-curve band family, the wind-side upper bounds, negative_renewable_offers /
wind_ptc_vintage_offers — the latter two may be reopened only with evidence the SPP-51b
verdicts did not have). Else the rows are an **unidentified body-level pricing error**, routed.
Only a REAL AND ADMISSIBLE object earns step 4 (rule 19 / 21 / 25, then shards).

## 5. Predictions (scored in the RESULT)

| # | prediction |
|---|---|
| P1 | Instrument reproduces all four rows within the §1 gate. |
| P2 | 2020: measured RT has ≥ 300 hours < 0; the model has < 50 hours ≤ 0. |
| P3 | Object (a) CONTRIBUTES to (or OWNS) C3a 2020 — NEG ∪ LOW carry ≥ 50 % of the +gap. |
| P4 | Object (a) does not own C3b 2022 (2022's worst months are UNDER-priced, Jun–Aug). |
| P5 | (b): Nov/Dec 2020 ordinary-hour error is mostly LEVEL (marginal mc too high), not quantity. |
| P6 | (c): model gas is flatter than published in 2022; the gas term explains ≥ 50 % of Jul–Aug 2022's under-pricing; it explains < 50 % of Oct/Nov 2020. |
| P7 | (d): the CT overrun is positive in Nov/Dec 2020, correlation with e_m > 0. |
| P8 | C3b 2021 is owned by Feb 2021 (Uri) alone, i.e. TOP — the ledgered wedge. |
| P9 | Overall: no object is REAL AND ADMISSIBLE for C3a 2020; if any is, it is (c) for C3b 2022. |

Expected row movement for any mechanism the verdict admits is stated in the RESULT only if §4
fires; nothing is solved otherwise. 2023–2025 are not touched except to re-run `audit_keepers`.
