# RESULT — UC-BANDS-ERCOT phase 1a: measured SCED bands on the UC basis (zero LP)

Lane UC-BANDS-ERCOT, 2026-10-14. Authorized by UC-DESK under owner decision 8. Phase 1a runs zero LP and lands no solve-affecting change.
PRECOMMIT: `PRECOMMIT-ucmilp-bands-ercot-2026-10-14.md`. Phase 0: `FINDING-ucmilp-bands-ercot-2026-10-14.md`.
**No ScenarioConfig field and no change to `src/`. Nothing solved, registered or deleted.**

| Artifact | Path |
|---|---|
| Derive | `scripts/data/derive_ercot_sced_uc_bands.py` |
| Band artifact | `data/raw/_validation-source/ercot_sced_uc_bands.json` |
| Re-price script | `data/bands/reprice_2019.py` |
| Re-price output | `data/bands/reprice_2019.json` |

## 0. Answer

1. **Bands derived.** They come from 60-Day SCED Submitted-TPO offers: 323 publication shards, delivery 2023, 221 CC / 147 CT / 38 ST resources. One value covers every scored year: no × 33, no deltas.
2. **The basis-error stop check passes.** The SCED CC econ_low (0.978) and econ_high (1.642) both sit inside the DAM-measured p25–p75: [0.829, 1.136] and [1.247, 2.228].
3. **At fixed dispatch, the measured bands raise the 2019 body price.** The body here means every tranche except peak.

   | Structure | Body change | 2019 C3a after the body change |
   |---|---|---|
   | Keeper | **+$4.38/MWh** | +6.2 % → +15.6 % |
   | UC | **+$3.06** | +18.8 % → +25.4 % |
   | UC, CT committed variant included | +$2.44 | +24.1 % |

   - The largest single leg is the removed CC residual delta: CC econ_low goes from 0.723 to 0.978.
   - **The measured bands do not close the UC 2019 gap. They widen it.**
4. **The peak leg reads −$5.6 in both structures, and it is not credible at fixed dispatch.** It comes from 16–33 marginal unit-hours in which a × 33 peak tranche (~$2,800–9,000) is re-priced to ~$30. In a solve, those hours would clear on the next unit or on ORDC.
   - The full fixed-dispatch readings are therefore an outer bound, not an estimate: keeper +3.4 %, UC +13.4 %.

## 1. Bands (fleet-basis multipliers, cap-weighted p50 [p25–p75], n resources)

The divisor is the DAM lineage's own: delivered gas (Henry Hub + ERCOT basis) × the output group's cap-weighted `Plant_Avg_HR`. That makes each value directly comparable to the keeper's 2019 band.

| class · band | keeper 2019 | DAM measured p50 (cconly / summary) | **SCED UC-basis** | incremental-basis equivalent |
|---|---|---|---|---|
| CC_REGULAR committed | 0.998 | 1.048 (Min Gen Cost, all-in) | **0.974** [0.787–1.219], 221 | 1.165 |
| CC_REGULAR econ_low | 0.723 | 0.963 | **0.978** [0.789–1.256], 216 | 1.170 |
| CC_REGULAR econ_high | 1.324 | 1.454 | **1.642** [1.324–2.083], 216 | 1.964 |
| CC_REGULAR peak | 151.008 (× 33) | 4.326 | **1.760** [1.444–4.156], 221 | 2.105 |
| CC_CHP c / el / eh / pk | 1.029 / 0.946 / 1.857 / 123.684 | 1.029 / 0.946 / 1.427 / 4.248 | **0.945 / 0.948 / 1.593 / 1.708** | 1.176 / 1.179 / 1.982 / 2.125 |
| CT_PEAKER econ_low | 1.27 | 1.146 | **0.855** [0.515–1.279], 147 | 1.070 |
| CT_PEAKER econ_high | 2.18 | 1.413 | **1.288** [1.028–1.504], 147 | 1.612 |
| CT_PEAKER peak | 433.95 (× 33) | 5.388 | **1.524** [1.149–1.920], 147 | 1.907 |
| CT_PEAKER committed (variant only) | 1.14 (start proxy) | 1.315 | **0.847** [0.586–1.282], 147 | 1.060 |
| ST_GAS committed | 0.91 | 2.605 | **1.075** [1.050–1.159], 38 | 1.245 |
| ST_GAS econ_low | 1.02 | 1.731 | **1.075** [1.050–1.297], 38 | 1.245 |
| ST_GAS econ_high | 1.20 | 2.043 | **3.166** [1.328–4.401], 38 | 3.668 |
| ST_GAS peak | 105.6 (× 33) | 4.096 | **3.230** [1.424–6.035], 38 | 3.742 |

**Incremental-to-average heat-rate ratio** (CAMPD TX 2023 unit OLS, cap-weighted):

| Group | Ratio | No-load share of fuel at p99 load | Units |
|---|---|---|---|
| CC_REGULAR | 0.836 | 12.5 % | 122 |
| CC_CHP | 0.804 | | 32 |
| CT_PEAKER | 0.799 | 17.6 % | 100 |
| ST_GAS | 0.863 | 7.9 % | 41 |

- **The incremental column is the same offer stated on the slope heat rate.** `base_HR × band = slope_HR × (band ÷ ratio)`. Carrying the slope as its own fleet field (Q2) therefore moves no offer; it only states the band on its proper basis.
- The CC no-load share (12.5 %) agrees with phase 0's UC no-load reading (10.9 % of CC energy cost).

**Read.**
- **The SCED top of curve is low.** The CC peak is 1.76, against the DAM mode-B 4.33 and the keeper's 151. This matches R-ERCOT-9's measured DAM top offers (CCGT median $24).
- **ST_GAS is the outlier.**
  - Its measured econ_high (3.17) is 2.6× the keeper's 1.20.
  - Its committed (1.075) sits near cost, unlike the DAM all-in 2.6.
  - n = 38, with a wide p25–p75.
- **The keeper's sub-measured CC econ_low (0.723) and ST bands are what the measured data removes.** They are the residual deltas phase 0 flagged.

## 2. Fixed-dispatch re-price, 2019 (`reprice_2019.json`)

Each marginal gas tranche of a re-banded class is scaled as `Δmc = mc · (m_new/m_old − 1)`. The econ-slice position comes from the registered ramp geometry (n = 6, mid = 0.35, top-refine). A zone takes the mean Δmc of its own marginal units, otherwise the hour's mean. Contributions are additive and sum exactly to the total.

| leg ($/MWh, load-weighted) | keeper | UC | UC + CT committed variant |
|---|---|---|---|
| CC_REGULAR econ | +3.23 | +3.25 | +3.25 |
| ST_GAS econ | +1.54 | +1.24 | +1.24 |
| ST_GAS committed | +0.29 | +0.12 | +0.12 |
| CT_PEAKER econ | −0.57 | −1.42 | −1.42 |
| CT_PEAKER committed | — | — | −0.63 |
| CC_CHP econ | −0.10 | −0.12 | −0.12 |
| **body subtotal** | **+4.38** | **+3.06** | **+2.44** |
| peak (marginal rows CC_CHP / CC_REGULAR / ST_GAS: keeper 13 / 3 / 17, UC 13 / 3 / 2) | −5.67 | −5.61 | −5.61 |
| total | −1.29 | −2.55 | −3.17 |
| LW mean: base → body-only | $49.41 → $53.80 | $55.32 → $58.38 | → $57.75 |

**Biases, stated.**
- **No re-dispatch.**
  - In the body, rising CC / ST offers would push some of those units out of merit, which caps the rise.
  - Cheaper CT offers would pull CT energy in.
  - The body readings therefore over-state the rise.
  - The peak leg prices a ~$2,800 tranche down to ~$30 without letting the next unit or ORDC set the price. It over-states the fall by far.
- **The whole offer is scaled.** VOM and the additive P1 adjusters scale with it: start markup, `cc_committed_offer_margin`, the conditional surfaces.
- **The 2019 values are extrapolated.** They come from 2023 offers on the 2023-normalized multiplier; no SCED exists for 2019.
- **Gas basis.** It is Henry Hub + ERCOT basis, the cconly lineage's basis. PRECOMMIT §2 named the EP-anchored basis. This deviates from that, so that the values compare directly with the keeper bands and the margin anchors, which are identified on the same HH basis. An EP version is a one-flag re-run if the owner prefers it.

## 3. What this says for the owner

- **The measured bands do not rescue the UC 2019 price level.**
  - Remove the residual deltas and use measured offers, and the body price rises in both structures.
  - In the keeper, C3a moves +6.2 % → +15.6 %.
  - The only downward leg is the × 33 removal, in a few scarcity hours. Fixed dispatch cannot size it, and the ×33-strip probe (R-51 record) measured it with a solve: 2019 C3a +6.2 % → −6.4 %.
- **Rule 14 applies:** a worse fit after swapping in measured data is a bug found elsewhere, not a reason to keep the residual bands. Phase 0's candidates for that bug:
  - the ST_GAS conduct structure (netload drag / steam cliff);
  - the CC fleet heat-rate basis (the bands are divided by the custom-bin `Plant_Avg_HR`, but the fleet multiplies the CAMPD operating rate).
- **Phase 1b (7 shards) is the only way to see the merit-order response.** It needs the owner's ruling, with Q2 and the CT committed / stacked-proxy question. Expected direction, at fixed dispatch only: body ↑, scarcity hours ↓.

## Log entry

- 2026-10-14 · UC-BANDS-ERCOT phase 1a · zero LP.
  - SCED UC-basis bands derived (2023 delivery, one value for all years); stop check PASS.
  - Fixed-dispatch 2019 body re-price: keeper +$4.38, UC +$3.06 (CT variant +$2.44).
  - The peak (× 33 removal) leg is −$5.6 and not credible at fixed dispatch.
  - No field added; no matrix cell moved.
