# PRECOMMIT — SPP-76: is the coal/gas crossover too gas-elastic because SPP's CC / coal heat rates are wrong?

**Zero LP. Pushed before any heat-rate or crossover number below is read.** Base `b024e34c`.
Keeper `2026-09-22-hydro-5-spp-floor` (`hydro5_spp_floor_span`, 2023–2025); rung
`2026-09-22-hydro-5-spp-rung` (`hydro5_spp_floor_rung`, 2019–2022, stamped to it).
Predecessors: `RESULT-spp-69-coal-cost-channel-2026-09-20.md` §4, `RESULT-spp-75-gas-low-side-2026-09-23.md` §2,
`RESULT-spp-41-coal-gas-crossover-2026-09-14.md` §1 (the stack crossing, $2.33–2.65).

## 0. Hypothesis

The model's SPP CC_REGULAR / ST_GAS heat rates are too HIGH and/or its COAL_PRB heat rates too LOW
against CAMPD heat input ÷ gross load (net-converted), so the coal↔gas switch point moves too far per
$/MMBtu of gas. The lever would be an EXISTING, default-off, measured field —
`measured_cc_heat_rates` / `measured_st_heat_rates` / `measured_coal_heat_rates` — fed by SPP's own
artifact from the existing derive (`scripts/data/derive_campd_{cc,gas_st,coal}_heat_rates.py --iso SPP`).
No new field, no fitted value.

## 1. The structural expectation, stated before measuring

The failing pattern is **two-sided** (coal short at $2.03, long at $3.72/$6.45). A **uniform** change
to the HR_cc/HR_coal ratio is **one-sided in sign**: lowering HR_cc makes CC cheaper at every gas price
(more CC in 2020 too, which is the wrong way there); raising HR_coal makes coal dearer in every year.
So a heat-rate swap can pass the (4) test **only through dispersion** — per-plant corrections that
widen the overlap of the coal and CC stacks (flattening the ~$2.4 knife-edge SPP-41 measured). Prior:
the swap is more likely a **level** move (fails (4)) than an elasticity repair.

## 2. Instruments (fixed now)

- **Step 1 — reproduce.** C1 grid-delivered Δ (model − actual) TWh for COAL_PRB / CC_REGULAR / ST_GAS,
  2019–2025, from the committed bundles' scorer path; must match SPP-69 §4 to ±0.05 TWh (rung and
  keeper have moved since SPP-69 — a drift is reported, not hidden). SPP-75 §2 RT≤0 CC+ST year
  pattern via `_spp75_gas_low_side.py` over `class_hourly`; must reproduce 3,548/1,767/426/277 model
  and 3,507/3,229/2,070/2,176 measured MW.
- **Step 2 — measured vs model HR.** Model: per-row offer heat rate (`fleet_arrays.heat_rate`, which
  already carries the band multiplier) and the underlying pre-multiplier base HR, from
  `reconstruct_bundle_fleet` (one interpreter per year), bands parsed with
  `run_calibration_full._tranche_band`. Measured: the existing derives run `--iso SPP --out <scratch>`
  (plant `hr_net`, operating-hour window, pooled 2023–2025, boundary guard kept). A **per-year**
  CAMPD rate (same construction, one year) is reported beside it as a stability check. Compared on
  the SAME net basis; capacity-weighted per class; also generation-weighted at the load each class
  actually runs (CAMPD gross-load-weighted). Coverage (MW covered / class pmax) reported.
  Note: the keeper's recipe applies a uniform 0.93 band multiplier to all ten fossil classes; it
  cancels in the coal/CC ratio and is reported separately, not attributed to heat rates.
- **Step 3 — crossover and first-order shift.** Crossover gas price per year:
  `g* = (c·HR_coal + VOM_coal − VOM_cc) / HR_cc` on capacity-weighted class means, model HR vs
  measured HR. First-order energy shift **holding the stack**: per hour, the energy the model's P1
  dispatched from {COAL_PRB, CC_REGULAR, ST_GAS} is re-dispatched in merit order over those rows'
  (mc, pmax × availability, min_gen) — once with model HRs (the proxy's own baseline) and once with
  measured HRs (covered rows only; uncovered rows keep their HR). Δcoal = proxy(measured) −
  proxy(model). Proxy fidelity (proxy(model) vs P1 class energy) is reported; if it misses P1 class
  energy by more than 25 % in any year, the shift is reported as indicative only.

## 3. Decision rule (ex ante)

**(4) PASSES only if** Δcoal_proxy < 0 in **both** 2021 and 2022 **and** Δcoal_proxy > 0 in 2020,
each with |Δ| ≥ 1.0 TWh (≈ 10 % of the failing row). One-sided, or below 1 TWh in any of the three
→ **FAILS**: reported as a level (or null) finding, **not built, no shard launched**, and the matrix
cells move to reflect the measurement. A measured HR that is materially different from the model's
is still rule-14 accurate data: if (4) fails but the HR error is large, that is **reported and routed**
(a level correction for its own sake is a separate lane question), not armed here.

If (4) passes: rule 19 enumeration, rule 21 `build_dof_ledger.py --iso SPP --check`, rule 25, then
seven per-year shards (rule 36), control + arm each, at one pinned SHA.

## 4. Predictions (scored in the RESULT)

| # | prediction |
|---|---|
| P1 | Step 1 reproduces SPP-69 §4 and SPP-75 §2 (within tolerance, or drift named) |
| P2 | Measured SPP CC net HR is **below** the model's (eGRID annual folds startup fuel) by 2–8 % cap-weighted |
| P3 | Measured COAL_PRB net HR is **below** the model's by 2–8 % (NWPP saw −6.8 %) — i.e. the coal error has the OPPOSITE sign to the hypothesis |
| P4 | Net ratio HR_cc/HR_coal moves by < 5 %, so g* moves by < $0.20/MMBtu |
| P5 | (4) **FAILS**: the swap is one-sided or sub-threshold; the elasticity defect has no heat-rate driver |
| P6 | C3a 2020 direction if armed: HR cuts lower offers → 2020 C3a (+15.5 %) falls; stated, not decisive |

## 5. What is not touched

Dead levers per the brief (gas commitment family, coal markup, band family, CHP-following as solved,
curtailment, demand, reserve, commitment reach, price seasonality). No LP in this session.
