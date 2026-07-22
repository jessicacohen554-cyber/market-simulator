# CAISO 38 — CA delivered-gas fidelity (citygate overlay, census-reconciled)

**Date:** 2026-06-29
**Run:** `results/calibration/caiso38_delivered_gas` (3-yr, P1) — KEEPER (promoted over caiso 37)
**Builds on:** caiso 37 (`caiso37_offer_curve`); every offer-curve + seam lever carried verbatim.

## What changed

CAISO priced its gas off the EIA-923 ISO-month delivered series, which for CAISO
is volume-weighted across only **7 plants** that report Schedule-5 gas receipts
(Gateway / Colusa / Lodi — PG&E + NCPA NorCal — plus SDGE Palomar): a
NorCal/SDGE-skewed sample. It assigned the marginal CC **$4.45/MMBtu (2024)** —
~$0.6 above the full-census CA electric-power delivered gas (EIA **N3045CA3**,
2024 = $3.98/Mcf = **$3.84/MMBtu**) and well above the measured CA citygate the
SP15-dominated marginal CC actually prices off (EIA **N3050CA3**, 2024 =
$3.38/MMBtu; SoCal border fell to a *discount* to Henry Hub in summer 2024).

caiso 38 reprices CAISO gas off the measured **SoCal / PG&E Citygate** via the
doc-08 trading-hub overlay (`gas_hub_basis_overlay`, the same mechanism NEISO
uses), keyed on the in-repo measured basis rows
(`data/raw/gas_basis_by_iso_month.csv`, EIA N3050CA3 − Henry Hub), then
reconciled **up to the census delivered-to-electric-power level** with the
measured citygate→burner-tip intrastate-transport differential
(`CAISO_CITYGATE_TRANSPORT_ADDER` = +0.46 = N3045CA3 − N3050CA3, 2024). Delivered
gas becomes **$7.42 / $3.84 / $4.42** (2023/24/25) vs the skewed 7-plant
$9.60 / $4.45 / $4.65. Measured, forward-reproducible (rule #11), **not**
residual-tuned. The overlay captures both the Jan-2023 western gas crisis
(+$24/MMBtu basis) and the summer-2024 SoCal discount. ERCOT/PJM/NYISO/NEISO
byte-identical.

## Results (P1)

| Metric (2023/24/25) | actual | caiso 37 | **caiso 38** |
|---|---|---|---|
| CA-zone (NP15/ZP26/SP15) avg LMP | 43.8/33.0/33.6 | 95.7/61.0/64.8 | **85.7/57.1/62.5** |
| CA-zone err % | — | +118/+85/+93 | **+96/+73/+86** |
| Interchange err (TWh) | — | +1.33/+0.12/+2.78 | **−2.38/−5.46/—** |
| Diurnal r 2023/24 | — | 0.85/0.89 | **0.82/0.79** |
| CA hrs > $200 (2023/24/25) | ~tens | 744/0/0 | **738/0/0** |

The gas correction lowered the body in all three years (2024 61.0→57.1) and the
2024/25 high-price tail stays eliminated. The 2023 tail (738 h) is again the
January Western winter-gas crisis (citygate Jan-2023 basis +$24/MMBtu), a
separate mechanism, not the body.

## Two grounded conclusions

**1. The body residual is the structurally-real CA-CC SRMC floor — not gas, seam,
or imports.** Even with census-correct gas, the 2024 body sits at $57 vs target
$33. The CA gas-CC marginal bid decomposes as `delivered_gas × eff_HR(~9) +
CARB_carbon + VOM` = `3.84×9 + ~14 + ~3 ≈ $51-55`. A CA CC's true SRMC genuinely
is ~$50-55 (CA gas + CARB cap-and-trade); actual CAISO $33 sits *below* it
because actual CAISO is set ~half the time by cheaper imports/hydro. This is
structural and cannot be closed by the offer curve (grounded, spent) or the seam
(see #2). Per rule #1 the gas fix stays even though the body residual remains.

**2. The seam import PRICE is correct; the discovered bug is the import-ATC.**
The task hypothesized the seam import price was ~$10-20 over the measured WECC
hub. It is **not**: the committed seam HR anchors (`INTERFACE_NEIGHBORS["CAISO"]`,
DSW `hr_by_year` 17.01/13.39/8.50, PNW 22.50/21.20/11.80) are derived to
reproduce the measured Palo Verde ($48.3/33.3/32.5) and Malin ($50.4/40.1/38.0)
hub means exactly (`scripts/derive_caiso_seam_hr_by_year.py`); PNW imports
correctly carry zero CARB (firm hydro), DSW carries the 0.37 t/MWh border CCGT
rate. The seam is right.

What the gas fix **exposed** (rule #11 — "if swapping a hand estimate for real
data makes the backcast worse, the estimate was silently compensating"): caiso
37's inflated 7-plant gas ($4.45) was silently propping up imports — making
domestic gas artificially expensive so imports cleared to the right volume
(+0.12 TWh in 2024). With correct census gas ($3.84), the domestic CC drops to
~$51 and imports under-clear by **5.5 TWh** (2024 model 26.9 vs actual 32.4 TWh).
The model imports in 97.5% of hours (vs actual 89%) but cannot reach actual's
high-import hours — the model import diurnal swing is **2321 MW vs actual 4596
MW**, i.e. the **forward-ATC ceiling is compressed** below actual peak
deliverability. The correct fix is to re-ground the CAISO corridor forward ATC
to the measured peak-import deliverability (NOT to re-inflate gas, which would
bury the error back in an inaccurate input — rule #11). **This is the next
target (caiso 39).**

## Why it's the keeper

caiso 38 is the **most structurally faithful** CAISO config: it replaces a
sparse, NorCal/SDGE-skewed 7-plant gas sample with the measured CA citygate
reconciled to the EIA electric-power census — the gas the marginal CC actually
burns (rule #11). The body improves; the interchange regression is **not** a
reason to revert (rule #11 forbids burying the accurate input back in the skewed
estimate) — it is the honest exposure of a pre-existing import-ATC
miscalibration that the skewed gas was masking, now the explicit next root-cause
target. The body residual above target is root-caused to the structural CA-CC
SRMC floor, not refit.
