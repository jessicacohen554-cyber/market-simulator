# FINDING — caiso-73: the measured shaped firm import base clears the C7 CT diurnal gate and moves the C1/C2 volume cluster the right way; the residual evening CT gap is now battery/commitment + demand basis (2026-07-10)

**Probe:** `2026-07-10-caiso-73-firm-shape` (+ `2026-07-10-caiso-73-firmshape-ablation`
twin), pre-registered single-delta A/B on the caiso-72 recipe:
`caiso_firm_import_shape=True` — the firm/contracted import blocks' hourly
availability shaped by the measured revealed import base. Year LEVEL = the
published DMM annual RA-import capacity × MIC corridor split
(`interchange_config.IMPORT_TRANCHES_BY_YEAR`: 2023 total 2,323 MW, 2024/25
3,371 MW); SHAPE = the unit-mean per-(month × hod) median of measured total
CISO corridor net imports (`eia_loader.measured_firm_import_shape`,
`CAISO_FIRM_IMPORT_SHAPE_PERCENTILE=50`, EIA-930 per-DIBA extract on the model
clock via the measured lag constants). Mean(w)=1 conserves the DMM annual firm
energy — the measured series contributes only the shape (rule 13: EIA-930 net
flows cannot size a gross firm block). Driver:
`FINDING-caiso72-hydro-envelope-2026-07-10.md` live lead #1 /
`FINDING-caiso72-step0-evening-displacement-2026-07-10.md` channel #2 /
`docs/handoffs/caiso-transmission-ttc-diagnosis-2026-07-09.md` §4 (Tier-2).
Scripts: `scripts/probes/_caiso73_firm_shape_ab.py`. Scored on rubric v2.4.
Registered per rule 15; NOT proposed for promotion.

## STEP-0 sizing (caiso73_step0_diag2024 — caiso-72 recipe re-measure)

- Model deep-evening (h19-22) corridor imports 3,341 MW (DSW 1,602 + PNW
  1,739) vs measured 2024 total 4.9-5.6 GW → deficit −1.6..−2.2 GW,
  concentrated on DSW (measured DSW evening 2.7-4.7 GW vs model 1.5-1.9).
- Model midday h14 imports 3,445 MW vs measured 0.9-1.3 GW → +2.3 GW over.
- Measured all-corridor net imports (model-clock): overnight 5.3-6.3 GW,
  midday 0.2-1.3 GW, evening ramp back to 5.4-6.2 GW (all three years).
- Shaped block (2024): ~5.0 GW overnight / 1.0-1.5 GW midday / 4.2-4.9 GW
  deep evening; per-corridor maxima (PNW 3.1, DSW 3.6 GW) below the link TTCs
  (COI 4.8, Path-46/WOR 10.6 GW) — the corridor p95 ATC envelope and the
  simultaneous-import interface limit still bound the delivered flow.

## Pre-registered directions vs outcome (2023/2024/2025)

| metric | caiso-72 main | **caiso-73 main** | direction called | actual |
|---|---|---|---|---|
| C7 D-1 CT profile_r | 0.782 / 0.771 / (0.68) | **0.817 / 0.819** / (0.715) | (not called — emergent) | gate 0.8; **C7 FAIL → PASS** |
| CC_REGULAR (TWh) | 61.38 / 64.76 / 65.25 | 62.30 / **63.36** / **64.03** | down ✓ (2024/25) | C1 2024 +9.0 → **+7.64 TWh** |
| 2025 gas (C2) | +8.5% | **+6.5%** | down ✓ | tolerance ±5% |
| deep-evening h19-22 imports (2024, MW) | 3,341 | **3,930** | up toward measured ✓ (partial) | 4,900-5,600 |
| h14 imports (2024, MW) | 3,445 | **3,201** | down toward ~1,100 ✓ (small) | 0.9-1.3 GW |
| LA_BASIN mean LMP | 70.20 / 47.19 / 51.47 | 71.13 / **46.67** / **50.79** | ease or hold ✓ (2024/25) | SP15 49.39 / 32.68 / 32.22 |
| C3a mean LMP vs RT | +21 / +35 / +49% | +23.5 / **+33.8** / **+47.4%** | evening eases ✓ (2024/25) | — |
| CT_PEAKER (TWh) | 1.40 / 1.23 / 0.87 | **1.68** / 1.13 / 0.79 | AMBIGUOUS (disclosed) | 4.56 / 5.24 / 3.09 |
| 2023 hrs>$200 (zonal max) | 473 | 480 | either way (disclosed) | 21 RT / 41 DA |
| C5a CO2 | +8 / +20 / +48% (approx) | **+7.1 (CAVEAT)** / +19.0 / +46.0% | down ✓ (small) | — |

Both disclosed risks resolved exactly as pre-registered:

1. **2024/25 CT slips as evening imports rise** (1.23→1.13, 0.87→0.79 TWh)
   while the CT *shape* improves decisively (profile_r 0.771→0.819 clears the
   0.8 gate). The imports took the flat overnight/belly CT plateau, not the
   evening ramp — attribution evidence that the REMAINING CT volume gap
   (~4.1 TWh in 2024) sits in the battery operational-realism and
   commitment/RA-bridge channels, per the caiso-70/72 ledger. NOT a reason to
   haircut imports (rules 1/14).
2. **2023 shifts domestic**: the firm level drops to the year's own DMM
   measurement (2,323 vs the static 3,371 MW the per-hub node carried), so
   CC +0.9 TWh, CT +0.28 TWh, LA_BASIN +0.9$, tail 473→480 h. This is the
   year-grounded published sizing doing its job; the 2023 system-tail root
   cause remains open (unchanged from caiso-72).

**Verdict (v2.4): NOT-YET — but C7 diurnal shape (protective) flips
FAIL→PASS**, the first C7 pass for CAISO; C6 governance PASS (attestation
carried, ZERO new free parameters) and C8 PASS. Remaining FAILs: C1 (2024
CC_REGULAR +7.64 TWh, down from +9.0), C2 (2025 gas +6.5%, down from +8.5%),
C3a (+23.5/+33.8/+47.4% vs RT — the offer-curve level step, rule-1 LAST),
C3b, C3c (2024/25 local tail still needs topology), C4 (gas r 0.802/0.566),
C5a (2023 now a CAVEAT at +7.1%).

## Ablation twin

Zero-forcing ablation (merchant floors/bridges off; hydro envelope AND firm
shape kept — both are caps/capabilities, they survive ablation by
construction): CT_PEAKER 2.81/1.86/0.98 TWh vs main 1.68/1.13/0.79. The
RA-bridge forced CC still crowds ~0.7-1.1 TWh of CT out of the pockets (the
caiso-70 signature), unchanged by the import shape — the commitment-side
displacement is floor-borne, not import-borne.

## What this closes / what remains (probe queue)

- ~~Import base/shape (Tier-2 of the TTC diagnosis)~~ — **closed by a
  measured mechanism**: evening firm capability now lands at the measured
  revealed schedule; keep `caiso_firm_import_shape=True` in every subsequent
  CAISO recipe (rule 1: a real market structure stays in). The LP fills only
  ~+0.6 GW of the +1.5 GW evening capability it was offered — the residual
  evening deficit is now *economic* (evening spot hubs priced above domestic
  CC/battery), not a capability miss.
- **Live lead #1 — battery operational realism** (was #2): model batteries
  discharge h15-17 (real fleet still charging) and h21-23 (real fleet
  SOC-spent); honest mechanism = measured storage-AS power reservation
  (rule 13's own worked example); needs a NEW DATA INTAKE (CAISO storage AS
  award volumes — DMM reports / OASIS AS results).
- **Live lead #2 — demand basis** (was #3): EIA-930 `Demand` (the model
  input) runs 1.4-1.7 GW below the supply-implied actual load at h14-17
  (the actual CT ramp window); rule-14 adjudication between conflicting
  published measurements — a data decision, document it, don't tune it.
- **Offer-curve level (C3a +23..+47%)** — LAST, only after the mix is right
  (rule 1). Note C3a improved in 2024/25 purely from structure.
- **The missing 2024/25 LOCAL tail (C3c)** needs finer local topology (Bay
  Area pockets copperplated into NP15) — scope like the SP15 split
  (`docs/handoffs/caiso-sp15-split-implementation-scope-2026-07-09.md`).
