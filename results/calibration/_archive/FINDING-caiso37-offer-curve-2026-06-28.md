# CAISO 37 — CAISO-specific gas offer curve (the domestic midday/body fix)

**Date:** 2026-06-28
**Run:** `results/calibration/caiso37_offer_curve` (3-yr, P1/P2) — KEEPER (promoted over caiso 35)
**Builds on:** caiso 35 (`caiso35_reference_seam`); every seam flag carried verbatim.

## What changed

CAISO had **no ISO-specific thermal offer curve** — it fell through every per-band
ternary in `_calibration_config` to the generic non-PJM/non-ERCOT `else` branch,
whose values were "fit to Colorado Bend II / Wolf Hollow II" (ERCOT plants) and
carried the ERCOT CT_PEAKER `peak` **13.15×** $5,000-ORDC scarcity wall. caiso 37
adds `_CAISO_OFFER_CURVE` (run_calibration.py), deep-merged on `iso == "CAISO"` so
only the named gas classes change (CC_CHP / CT_CHP / ST_GAS / coal keep the generic
defaults; ERCOT/PJM/NYISO stay byte-identical):

- **CC_REGULAR** re-grounded to the measured CAMPD CC marginal-HR shape
  (`econ_low` 1.06→0.95 flat body, `econ_high` 1.27→1.21 SRMC reach — the same fit
  ERCOT/NYISO keepers use; physical F-class duct-fire `peak` 2.25 kept), removing
  the ERCOT level premium on the midday CC body.
- **CT_PEAKER** `peak` capped **13.15→4.0** (CAISO's $1,000–2,000 soft cap, not
  ERCOT's $5,000 ORDC — PJM's reasoning/value); `econ` re-grounded to the DMM
  Default-Energy-Bid cost-plus-adder shape (1.27/1.98→1.10/1.50); `committed` start
  hurdle 1.55→1.35 (NYISO-grounded) so CAISO's fast-start CTs serve the evening ramp.

Grounded in CAISO DMM market structure + measured CAMPD heat rates, **not** the
price residual (rules #1/#11).

## Results (P1)

| Metric | actual | caiso 35 | **caiso 37** |
|---|---|---|---|
| CA-zone (NP15/ZP26/SP15) avg LMP 2023/24/25 | 43.8/33.0/33.6 | 100.0/62.8/68.5 | **95.7/61.0/64.8** |
| Interchange err 2023/24/25 (TWh) | — | +3.56/+2.78/+4.40 | **+1.33/+0.12/+2.78** |
| Interchange diurnal r 2023/24 | — | 0.88/0.93 | 0.85/0.89 |
| System price max 2024/2025 | — | (tail present) | **$84.8 / $90.5** |
| CA hrs > $200 — 2024/2025 | ~tens | some | **0 / 0** |
| CA hrs > $200 — 2023 | 21 | 744 | 744 (see below) |

**Wins:** the CT cap eliminated the 2024/25 high-price tail entirely (max ~$85–90);
the curve modestly lowered the body in all three years; and it **materially improved
interchange** (2023 err +3.56→+1.33, 2024 +2.78→+0.12) — the cheaper, more-
competitive domestic gas stack reduced the structural over-import. Diurnal r slips
mildly (0.88→0.85, 0.93→0.89), an acceptable trade for the large volume-error gain.

## Discovered root cause: the 2023 tail is the January Western gas crisis, NOT the CT wall

The 2023 `> $200` count stayed at **744** despite capping the CT wall — because
those 744 hours are **all of January 2023**, the Western winter gas spike (the
Jan-2023 SoCalGas crisis). CA-zone LMP averages **$314/MWh in January** vs **$76 in
Feb–Dec**; 2024 and 2025 (normal-gas Januaries) have **0** hours over $200. The
January spike alone lifts the 2023 annual mean from ~$76 to $95.7. This is a
separate mechanism (the measured West winter gas / seam passthrough magnitude),
out of this offer-curve task's scope.

## Remaining body residual (next levers, all out of scope here)

Even excluding January, the Feb–Dec body sits at ~$76/$61/$65 vs target ~$33–44.
Consistent with the caiso 36 diagnosis recommendation #1, the residual is the
**domestic offer LEVEL above the econ band** — the P1 startup-amortization markup +
reserve co-optimization adder inflating the marginal gas_cc offer — and the midday
**solar fraction** (model ~10.8 GW midday vs ~13–14 GW utility solar). The grounded
offer curve correctly removes the ERCOT borrow but cannot, by itself, close a
residual whose driver is the startup/reserve adder and the winter-gas passthrough.

## Why it's the keeper

caiso 37 is the **most structurally faithful** CAISO config: it replaces a
cross-ISO ERCOT offer borrow (and the unphysical $5,000-ORDC CT wall) with CAISO's
own DMM/CAMPD-grounded curve, while improving the headline interchange metric and
eliminating the 2024/25 price tail. The body residual is root-caused (January gas +
the startup/reserve adder), not refit (rules #1/#11).
