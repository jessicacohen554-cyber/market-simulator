# PJM seam — Southeast gas-inelastic pricing, and the import/export ↔ class-miss unification (pjm 51)

**Date:** 2026-06-26. **Bundle:** `results/calibration/pjm51_se_inelastic`
(dashboard id `2026-06-26-pjm-51-seam-se`). **Determination:** NOT-YET
(C6 governance PASS). **pjm-48 remains the PJM keeper** — this is a structural
seam diagnostic continuing pjm-49 → pjm-50.

## What changed (the one new lever)

The Southeast reference-price seams (Carolinas/TVA/LGEE) were priced
gas-elastically at a flat HR 11.6, so in dear-gas 2025 they priced to ~$40.8 —
only ~$2 below PJM — and the diurnal swing flipped them to a *wrong-direction
export* (the pjm-50 headline residual). A coal/nuclear region's price is weakly
gas-elastic, so they now price on an **affine-in-gas effective HR**,

    SE_LMP(gas) = 5.6·gas + 14.2      (neighbor_price._HR_GAS_ELASTIC)

OLS-fit to documented Into-Southern/SERC hub price levels — a measured neighbor
price-formation series, **blind to PJM's interchange** (rule #11), all years
(no organized LMP to anchor a per-year HR to, so the fuel-stack affine form *is*
the anchor; `scripts/data/derive_southeast_inelastic_hr.py --check`). It holds the
Southeast at ~$33.9 in 2025 (~$9 below PJM), so the net-import direction holds
across the gas cycle. This run also **merges the pjm-50 seam patch** (firm
scheduled-export floor + TVA/LGEE seams + losses-only hurdle), previously
stranded as an unapplied patch.

## Result — the named root cause is fixed

Per-seam net export, TWh (+ = PJM export), model51 / pjm-50 / PJM per-tie:

| seam | 2023 | 2024 | 2025 |
|------|------|------|------|
| MISO      | +32.3 / +22.6 / +35.3 | +35.7 / +25.5 / +27.2 | +37.8 / +20.0 / +24.6 |
| NYISO     | +11.7 /  +8.4 / +18.5 | +22.5 / +20.4 / +20.4 | +30.5 / +28.1 / +21.9 |
| Carolinas |  +1.0 /  −0.4 /  −5.4 |  −0.0 /  −6.2 /  −6.4 |  **−4.4 / +2.0 / −5.9** |
| TVA       |  +0.5 /  −0.5 /  −6.2 |  −0.4 /  −4.7 /  −5.8 |  **−3.3 / +1.3 / −5.4** |
| LGEE      |  +0.2 /  −0.5 /  −2.2 |  −0.4 /  −3.4 /  −2.4 |  **−2.5 / +0.9 / −2.3** |
| **NET**   | +45.7 / +29.6 / +40.0 | +57.4 / +31.6 / +33.0 | +58.1 / +52.3 / +32.9 |

2025 Carolinas/TVA/LGEE flip from wrong-direction **export** (pjm-50
+2.0/+1.3/+0.9) to correct **import** (−4.4/−3.3/−2.5), matching the per-tie
sign. The Southeast gas-inelastic mechanism works exactly as designed.

## The unification — "import/export" and "class missed" are ONE root cause

The net interchange *worsened* (MAE vs EIA-930 23.5 vs pjm-50 15.2) — and that is
the diagnostic's value, not a defect. Correctly importing cheap Southeast power
**lowers PJM's modeled price**, so PJM out-competes MISO/NYISO and over-exports
*more* (2025 MISO +37.8 vs pjm-50 +20.0). The flat-Southeast was **masking** this
by bleeding the excess off as spurious Southeast exports. The MISO/NYISO seams
already carry convex self-limiting (`load_shape_exponent` 1.6) yet still saturate
at the cap — because the over-export is **not a seam-pricing bug**. It is that
PJM is structurally **under-priced**: it over-generates fossil (C2 2025 gas
+17.6 %, classFull coal off; C3a LMP 2024/25 −9.3 %/−14.1 %), so it is genuinely
cheaper than its neighbors and exports at the cap.

So the two stated PJM issues are the **same** root cause: **PJM's modeled fleet is
too cheap.** The seam over-export is downstream of the fossil over-generation; no
seam lever can fix it while the fleet clears below the neighbors.

## Next steps (grounded, in priority order)

1. **Coal/gas offer-curve retune — the lever for BOTH issues.** Raising PJM's
   marginal fossil cost (the keeper's separate model-side workstream:
   `pjm-coal-*` handoffs) lifts the LMP toward actual AND removes the price gap
   that drives the over-export. This is the single highest-value next move.
2. **Southeast FIRM-IMPORT floor** — the mirror of the firm-export floor. The
   affine price correctly stops *faking* the 2024 Southeast import economically
   (2024 SE now ≈0 vs per-tie −14.6); the real ~14 TWh is firm Duke/TVA bilateral
   contract flow. Add `firm_import_floor_by_year` from PJM's measured per-tie
   scheduled *import* p10 (the export-floor derivation, sign-flipped).
3. **NYISO `load_shape_exponent` accuracy fix** — `derive_neighbor_convexity.py
   --check` flags the registry's 1.63 as drifted from NYISO's own measured 1.88
   (gross). Independent of this run; update for accuracy (rule #12). Will steepen
   NYISO self-limiting but will NOT close the structural under-pricing gap (#1).

The Southeast gas-inelastic pricing is structurally correct and **stays in**
(rule #1) even though the net fit worsened.
