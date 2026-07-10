# FINDING — caiso-73: the measured shaped firm import base (DRAFT — outcomes pending solve)

**Probe:** `2026-07-10-caiso-73-firm-shape` (+ ablation twin), pre-registered
single-delta A/B on the caiso-72 recipe: `caiso_firm_import_shape=True`.

## Mechanism

Replaces the flat 3.37 GW firm/contracted import block with an hour-varying
pmax capability: year LEVEL = published DMM annual RA-import capacity × MIC
corridor split (`IMPORT_TRANCHES_BY_YEAR`: 2023 total 2,323 MW, 2024/25
3,371 MW); SHAPE = unit-mean per-(month × hod) median of measured total CISO
corridor net imports (`eia_loader.measured_firm_import_shape`, EIA-930
per-DIBA extract on the model clock). Mean(w)=1 conserves the DMM annual firm
energy — the measured series contributes only the shape (rule 13).

## STEP-0 sizing (caiso73_step0_diag2024, caiso-72 recipe re-measure)

- Model deep-evening (h19-22) corridor imports 3,341 MW (DSW 1,602 + PNW
  1,739) vs measured 2024 total 4.9-5.6 GW → deficit −1.6..−2.2 GW, all DSW
  (measured DSW evening 2.7-4.7 GW vs model 1.5-1.9).
- Model midday h14 imports 3,445 MW vs measured 0.9-1.3 GW → +2.3 GW over.
- Measured all-corridor net imports (model-clock): overnight 5.3-6.3 GW,
  midday 0.2-1.3 GW, evening ramp back to 5.4-6.2 GW (2023-2025).
- Shaped firm block (2024): ~5.0 GW overnight / 1.0-1.5 GW midday / 4.2-4.9
  GW deep evening; per-corridor maxima (PNW 3.1, DSW 3.6 GW) below link TTCs.

## Pre-registered directions (from the probe script docstring)

1. Deep-evening (h19-22) imports UP toward measured; midday h14 over-import
   DOWN.
2. Evening C3a price level eases; CC_REGULAR DOWN (C1 2024 +9.0 TWh target);
   C5a CO2 down.
3. CT_PEAKER: AMBIGUOUS by design — disclosed risk that added evening import
   supply displaces the CT the hydro envelope recovered; if CT falls, that is
   attribution evidence for the battery/commitment channel (queue #2/#3),
   NOT a reason to haircut imports (rules 1/14).
4. 2023 firm level drops to the year's own DMM measurement (2,323 vs static
   3,371 MW) — the 2023 tail may move either way (disclosed, non-gating).

## Outcome (TO FILL)

| metric | caiso-72 main | **caiso-73 main** | direction called | actual |
|---|---|---|---|---|
| CT_PEAKER (TWh) | 1.40 / 1.23 / 0.87 | TBD | ambiguous (disclosed) | 4.56 / 5.24 / 3.09 |
| CC_REGULAR (TWh) | 61.38 / 64.76 / 65.25 | TBD | down | — |
| deep-evening imports (2024, MW) | 3,341 | TBD | up toward 4,900-5,600 | measured |
| h14 imports (2024, MW) | 3,445 | TBD | down toward ~1,100 | measured |
| LA_BASIN mean LMP | 70.20 / 47.19 / 51.47 | TBD | ease or hold | SP15 49.39 / 32.68 / 32.22 |
| 2023 hrs>$200 (zonal max) | 473 | TBD | either way (disclosed) | 21 RT / 41 DA |

## Verdict / closes / opens (TO FILL)
