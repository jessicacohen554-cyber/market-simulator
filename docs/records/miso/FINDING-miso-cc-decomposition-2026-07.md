# FINDING — MISO C1 CC_REGULAR +44 TWh: merit-order decomposition and the one grounded lever

**Date:** 2026-07-06. **Lane:** Wave-3 MISO L-14 (gap register G-23, the rubric's canonical
structural miss). **Baseline:** keeper `2026-07-05-miso-41-ct-evening` (CC_REGULAR +44.35 /
+43.22 / +26.80 TWh vs actual, 2023/24/25). All numbers from the keeper's registered payload +
bench (no new solve needed for the decomposition; the lever run is registered separately).

## 1. What CC is displacing (annual supply balance, model − actual, TWh)

| bucket | 2023 | 2024 | 2025 |
|---|---|---|---|
| **CC_REGULAR** | **+44.35** | **+43.22** | **+26.80** |
| CC_CHP | +7.41 | +5.38 | +6.26 |
| net imports (interchange) | **−23.2** | **−19.4** | −24.1 |
| CT_PEAKER | −12.05 | −9.32 | −9.78 |
| ST_GAS | −10.86 | −14.27 | −12.32 |
| ST_CHP + CT_CHP + OTHER_FOSSIL | −10.59 | −12.93 | −7.35 |
| coal family | −5.95 | −8.32 | **+16.89** |
| hydro + oil | −1.66 | −2.11 | −9.26 |

- **NOT coal (2023/24)** — the coal family *under-runs* the actuals in both CC-exemplar years;
  the statmode "+30–36 TWh coal over-run" is an overlays-off artifact, not the keeper's state.
  2025 flips (coal +16.9) — the dear-gas year where below-SRMC coal out-competes $3.52-gas CC.
- **NOT wind curtailment** — wind/solar ride the L1 delivered-outcome bound (D-10 pinned);
  their deltas are ~0 by construction and cannot absorb dispatch error.
- **Imports are the single biggest bucket** (−19 to −24 TWh/yr): the model imports 14.7 vs
  actual 37.9 TWh (2023), 3.7 vs 23.1 (2024), and net-EXPORTS 5.1 vs actual net-imports 19.0
  (2025). With the model's internal LMP $4–5 too low (C3a −9.8/−15.6/−19.5%), the priced
  interchange sees neighbors as expensive and starves the import channel; domestic CC is the
  cheap headroom that fills the hole.
- **Intra-gas misallocation is the other half**: the real market ran 33–36 TWh/yr more
  CT_PEAKER/ST_GAS/CHP/OTHER_FOSSIL than the model, while real CC ran 44 less. The
  perfect-foresight, no-commitment P1 dispatches the efficient class and never needs the
  inefficient ones (their SRMC $26–40 cannot clear a $25.9 price ceiling set by
  discounted coal — they are priced out *by the same coal underpricing*).

## 2. Where and when (zone × month × hour structure)

- **~73% of the CC over-run is MISO-South** (the Entergy gas belt): +32.5 of +44.35 (2023),
  +25.4 of +43.22 (2024) — model South CC 97.5/91.6 vs actual 65.1/66.2 TWh. Midwest CC zones
  are close to actual (East −5.8/−0.7, Indiana −1.0/−0.5). South's surplus serves South load,
  displaces South imports (SPP/TVA/SOCO seams clip toward zero import in the measured
  envelope), and exports north over the RDT (capped 2,500 MW S→N, correctly encoded).
- **Every month over-runs; shoulder months worst** (Mar–May and Oct–Dec at +2.4–4.8 TWh/mo vs
  +0.2–2.7 in Jan/Jun–Sep): the hours where real CC decommits/does maintenance-economics
  backdowns but the LP keeps running whatever the CAMPD outage overlay leaves available.
- **Flat across the day**: gas-family hourly r = 0.99 / NRMSE 0.07 and CC profile_r 0.99 with
  model off-peak CV *below* actual (0.064 vs 0.077) — the over-run is a near-uniform baseload
  lift, not a peak-hours phenomenon.
- **CC is NOT availability-bound**: fleet-only reconstruction gives CC_REGULAR
  Σ pmax×availability = 230 TWh/yr; the model dispatches 180/187 (78/81%) vs actual 135.6/143.5
  (59/62%). The LP does back CC down in low-residual hours — merit-order economics, not an
  availability error, sets the level. Levers that change relative offers/imports CAN move it.

## 3. Candidate levers, adjudicated

1. **Coal marginal-tranche measured-SRMC bound — CHOSEN (implemented as
   `coal_econ_srmc_bound`, run miso-42).** The named open thread (burndown Evidence 2): the
   gas-keyed sigmoids discount even the marginal (econ/peak) coal tranches $4–5/MWh below their
   measured F923 delivered SRMC (BIT passthrough 0.61× at $2.19 gas), capping the model price at
   $25.9 — below the cheapest measured coal tranche ($28.3) — which (a) sets the too-low C3a
   level, (b) prices ST_GAS/CT out of the stack entirely (their −25 TWh under-run), (c) starves
   the priced-interchange import channel (−20 TWh), and (d) in dear-gas 2025 lets below-cost
   coal over-run +16.9 TWh. The fix removes a fitted discount from tranches whose fuel is bought
   at market (no take-or-pay story) — a DOF *reduction*, forward-valid (offer ≥ full delivered
   fuel cost regenerates from any forward fuel trajectory). It attacks the price ceiling that
   the import and intra-gas buckets hang off; the direct CC-row effect is expected to be
   partial (CC stays deeply inframarginal at $2.19–3.52 gas).
2. **Commitment posture (P1 no-min-load) — DEFERRED TO DESIGN (rule against stacking; G-25).**
   The DP-1 MIP crossbench measured P1 carrying +34% committed CC energy vs a MIP with
   min-load/min-run — and +34% on actual CC (135.6 × 1.34 = 181.7) reproduces the model's 179.9
   almost exactly. Magnitude-consistent with the *whole* CC row, and it is the mechanism behind
   the shoulder-month/off-peak flatness signature (§2). But a commitment-posture build is a
   structural workstream (it must not be a P2 bolt-on; P1 is THE scored run), so it is designed
   — not built — in `docs/multi-iso/miso-scarcity-posture-design-2026-07.md` (it is the same
   lever the scarcity tail needs).
3. **Import-price / seam levers (`miso_pjm_lmp_import_pricing`, firm-import floor) — REJECTED
   for this session.** The import shortfall is largely *downstream* of the internal price level:
   priced imports clear only when the neighbor price beats the internal LMP, so measured-LMP
   import pricing against a $25.9 internal level would import even less. Re-evaluate after the
   coal bound lands; `miso_firm_import_floor` exists but forces a measured outcome level onto
   the seam (rule-13 tension) and is not touched.

## 4. Rule compliance

- One lever implemented (`coal_econ_srmc_bound`), zero new fitted parameters (a boolean gate
  that *removes* a fitted discount from the marginal tranches; the bound's value is the plant's
  own measured delivered cost, not a tuned number). No floor, no forced energy, no residual
  target (rules 13/17–20).
- Scored full-span 2023 2024 2025 in one invocation (rule 16), registered whatever the result
  (rule 15) as `miso-42-coal-econ-srmc`; keeper recommendation left to the owner in the
  calibration log (no in-session swap).
