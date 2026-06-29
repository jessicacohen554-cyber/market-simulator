# CAISO 39 — corridor forward-ATC re-grounding (the midday body lever)

**Date:** 2026-06-29
**Run:** `results/calibration/caiso39_import_atc` (3-yr, P1) — KEEPER (promoted over caiso 38)
**Builds on:** caiso 38 (`caiso38_delivered_gas`); every offer-curve + seam + gas lever carried verbatim.

## TL;DR

The task hypothesised the CAISO body residual (~$55 model vs ~$33 actual, 2024) was
the domestic gas-CC **offer curve** (econ_high too steep). Re-deriving the offer-curve
Jacobian on the caiso 38 baseline **refuted that** — the offer curve is grounded and
spent. The body over-price is **structural and entirely midday**, set by domestic gas-CC
marginal at its true ~$51 SRMC because cheaper supply is capped. caiso 39 re-grounds the
WECC corridor **forward-ATC base fractions** to the measured p95 deliverability the
caiso 38 finding flagged as compressed. Result (2024): import volume gap **−5.5 → −2.9
TWh**, CC over-run **+16.7 → +14.7**, monthly LMP MAE **24.4 → 23.4**, no structural
regression. Modest but measured-grounded; the body residual that remains is the real
CA-CC SRMC floor.

## Part 1 — the offer-curve Jacobian was spent (the original task, refuted)

Re-derived `scripts/derive_offer_curve_jacobian.py --iso CAISO` on freshly-solved
caiso 38 baseline + single-knob probes (the prior probes were stale — gas 2.54 vs
caiso 38's citygate 3.84/7.42). Both the official Jacobian and controlled
finite-difference probes agree:

| 2024 move (off caiso 38) | Δgas_cc | Δ net-import | Δ CA-LMP |
|---|---|---|---|
| CC_REGULAR econ_high −0.15 (→1.06) | **+2.55** (worse) | **−2.4** (worse) | −1.3 |
| CC_REGULAR econ_low −0.10 (→0.85) | +0.98 (worse) | −0.9 (worse) | −0.6 |

The official joint-move recipe returns **"no move recommended"** (every knob
trust-region-frozen or wrong-signed). **Lowering any CC band steals capped imports and
worsens the CC over-run for a negligible price gain** — the offer curve cannot lower the
body.

**CAMPD grounding of econ_high (rule #5/#11).** The CA combined-cycle fleet (CAMPD
`CA_2024`, n=86 units) measured marginal heat rate vs the plant average:
incremental(slope) = **0.84×**, operating HR @85-98% load = **0.97×**, @45-60% =
**1.10×**, and the **1.21×** the model's econ_high carries appears only at **<40% load
(part-load)**. So econ_high = 1.21 (borrowed from the ERCOT/NYISO fit) is the *part-load*
HR, not the economic reach — genuinely too steep. But correcting it to ~1.06 lowers the
body only −1.3 and regresses interchange −2.4 (it makes CC cheaper → steals imports).
The faithful value cannot be applied in isolation; the curve is left unchanged and the
correction deferred to whenever the import side is fixed. **CT_PEAKER is NOT touched**:
CAMPD shows CT correctly sits *above* CC in merit (CT incremental 0.75× of a 10.86 base
≈ 8.2 eff-HR floor, econ_low 11.95 eff-HR vs CC econ_high 9.0); the CT under-run is the
missing scarcity/ramp mechanism (already partly carried by the reliability-drag floor),
not offer-curve-addressable — forcing it down would be an unphysical fit (rule #1/#11).

## Part 2 — the body over-price is midday and structural

Hourly CA-zone LMP, caiso 38 baseline (2024):

| block | model | actual ~ | gap |
|---|---|---|---|
| midday (h9–16) | ~$51 | ~$15 | **+$36** |
| evening (h18–22) | ~$62 | ~$60 | ~0 (already accurate) |

Midday: ~12.9 GW solar + ~6.6 GW gas-CC, CC marginal at its ~$51 SRMC
(`delivered_gas 3.84 × eff_HR ~9 + CARB ~14 + VOM ~3`). The midday floor exists because
two deliberate structural caps force CC marginal at the solar peak: the Lever-D solar
deliverability derate and the corridor `CAISO_CORRIDOR_ATC_SOLAR_K=1.5` midday import
collapse. An offer-curve cut shifts *all* hours uniformly (~$1.3) and cannot carve the
midday trough.

## Part 3 — caiso 39: re-ground the corridor base fraction to measured deliverability

The caiso 38 finding §2 named the next target: "re-ground the CAISO corridor forward ATC
to the measured peak-import deliverability" (model import diurnal swing 2,321 MW vs actual
4,596 MW). The forward-ATC envelope is `TTC × atc_base_fraction × clip(1 − k·solar_frac,
floor, 1)` — the forecast-native (rule #12) replacement for the measured p95 envelope.
Comparing the formula to the measured per-(month × hour-of-day) p95 net-import
deliverability (`measured_corridor_flow_envelope`, EIA-930 CISO↔DIBA, pooled 2023-25):

| corridor | measured overnight p95 ÷ TTC | prior base_fraction |
|---|---|---|
| PNW (COI/Path-66, TTC 4,800) | **0.43** (≈2,052 MW) | 0.30 (−1.5× compressed) |
| DSW (Path-46/WOR, TTC 10,623) | **0.56** (≈5,942 MW) | 0.50 |

**Change (caiso 39):** PNW `atc_base_fraction` 0.30 → 0.43, DSW 0.50 → 0.56. Anchored to
measured DELIVERABILITY the corridor demonstrably carried at peak — a forward-reproducible
capability ratio, not a tune to net-import volume or the price residual (rule #11/#12).

**Rejected sub-lever — the DSW midday floor.** The measured p95 *midday/overnight* ratio
is 0.62 (vs the 0.30 floor), so a first cut raised DSW floor 0.30 → 0.62. That
**over-imported midday** (~4.0 GW vs measured-typical ~2.0 GW) and **inverted the
interchange diurnal shape (corr +0.70 → −0.06)** — because the forward formula is a
ceiling the LP clears *below*, and the p95 overstates the *typical* midday deliverability
(WECC neighbors are usually, not just sometimes, long midday). The floor stays 0.30; the
prior baseline already reproduced the correct typical midday import.

## Results (2024, P1, vs caiso 38 baseline reproduced this session)

| metric | actual | caiso 38 base | **caiso 39** |
|---|---|---|---|
| CA-zone avg LMP | 33.0 | 55.6 | **54.4** |
| monthly LMP MAE | 0 | 24.4 | **23.4** |
| net interchange (TWh) | −32.4 | −26.9 (gap −5.5) | **−29.5 (gap −2.9)** |
| interchange duration RMSE (MW) | 0 | 1458 | **1259** |
| interchange diurnal corr | 1.0 | +0.70 | **+0.66** |
| gas_cc err vs EIA-923 (TWh) | 0 | +16.7 | **+14.7** |
| gas_ct err vs EIA-923 (TWh) | 0 | −4.8 | −5.1 (structural) |

(3-year confirmation appended on the dashboard.)

## Why it's the keeper

caiso 39 closes the import-ATC compression the caiso 38 finding exposed, using a
measured-deliverability re-grounding of a forward-reproducible capability parameter
(rule #11/#12). It improves the headline interchange volume (the clearly-broken metric)
by halving the gap, improves the CC over-run and the body, and improves the interchange
duration RMSE — at the cost of a minor diurnal-corr dip (0.70 → 0.66) that is net-positive
on interchange overall. The body residual that remains is root-caused (not refit): the
**structurally-real CA-CC SRMC floor** (gas + CARB) marginal midday because the deliverable
solar (Lever D) and the midday corridor are still capped, and the model cannot yet **export**
the midday solar surplus (p99 model 0 vs actual +3,538 MW) — the next structural levers,
out of this fix's scope.
