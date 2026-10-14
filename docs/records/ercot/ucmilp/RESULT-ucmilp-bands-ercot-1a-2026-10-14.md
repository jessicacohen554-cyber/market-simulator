# RESULT — UC-BANDS-ERCOT phase 1a: measured SCED bands on the UC basis (zero LP)

Lane UC-BANDS-ERCOT, 2026-10-14. Authorized by UC-DESK under owner decision 8. Phase 1a runs zero LP and lands no solve-affecting change.
PRECOMMIT: `PRECOMMIT-ucmilp-bands-ercot-2026-10-14.md`. Phase 0: `FINDING-ucmilp-bands-ercot-2026-10-14.md`. Rule-14 follow-up: `FINDING-ucmilp-bands-ercot-rule14-2026-10-14.md`.
**No ScenarioConfig field and no change to `src/`. Nothing solved, registered or deleted.**

| Artifact | Path |
|---|---|
| Derive | `scripts/data/derive_ercot_sced_uc_bands.py` |
| Band artifact | `data/raw/_validation-source/ercot_sced_uc_bands.json` |
| Re-price script | `data/bands/reprice_2019.py` |
| Re-price output | `data/bands/reprice_2019.json` |

**Update (same day, UC-DESK approval of rule-14 item 2).**
- **The artifact is now normalized on the dispatch basis.** Gas is Henry Hub daily plus the measured monthly EP basis. The heat rate is the fleet's CAMPD-measured operating rate.
- **Why.** The first cut used the lineage basis: HH − 0.50 and the bin `Plant_Avg_HR`. ERCOT-117 proved that basis inconsistent with dispatch. In 2023 the gas ratio was 0.797; the heat-rate ratios were CC 0.987, CT 1.051 and ST 1.015.
- **The lineage numbers are still reproducible.** Re-running with `--gas-basis hh --hr-basis bin` gives the first cut back byte-for-byte; it is checked. Both sets are shown below.
- `reprice_2019.json` now holds the dispatch-basis readings.

## 0. Answer

1. **Bands derived.** They come from 60-Day SCED Submitted-TPO offers: 323 publication shards, delivery 2023, 221 CC / 147 CT / 38 ST resources. One value covers every scored year: no × 33, no deltas.
2. **The basis-error stop check passes.** It compares like with like, on the lineage basis. The SCED CC econ_low (0.978) and econ_high (1.642) both sit inside the DAM-measured p25–p75: [0.829, 1.136] and [1.247, 2.228].
3. **Fixed-dispatch 2019 re-price of the body tranches** (every tranche except peak):

   | Structure | Lineage basis (first cut) | **Dispatch basis (current)** |
   |---|---|---|
   | Keeper (C3a +6.2 %) | +$4.38 → +15.6 % | **−$0.71 → +4.6 %** |
   | UC (C3a +18.8 %) | +$3.06 → +25.4 % | **−$1.95 → +14.6 %** |
   | UC, CT committed variant included | +$2.44 → +24.1 % | **−$3.06 → +12.3 %** |

   - **The first cut's rise was the basis error.** On a consistent basis, the measured bands lower the keeper's 2019 price slightly (to +4.6 %).
   - **The UC gap stays.** On the consistent basis, the measured bands take the UC from +18.8 % to +14.6 %, or +12.3 % with the CT committed variant. That is about a quarter to a third of the gap.
   - The largest downward leg is CT_PEAKER econ: −$2.05 in the UC. With fewer gas units committed, CT sets the price far more often, and its measured offer (0.96 at econ_high) sits well below the keeper's fitted 2.18.
4. **The peak leg (−$5.6 in both structures) is not credible at fixed dispatch.** It comes from 16–33 marginal unit-hours in which a × 33 peak tranche (~$2,800–9,000) is re-priced to ~$30. A solve would clear those hours on the next unit or on ORDC. The ×33-strip solve (R-51 record) is the only measured reading of that leg: 2019 C3a +6.2 % → −6.4 %.

## 1. Bands (fleet-basis multipliers, cap-weighted p50 [p25–p75], n resources)

Each multiplier is the offer ÷ (delivered gas × the group's fleet heat rate), so it is what the model multiplies its own fleet heat rate and dispatch gas by.

| class · band | keeper 2019 | DAM measured p50 (lineage basis) | SCED, lineage basis (first cut) | **SCED, dispatch basis (artifact)** |
|---|---|---|---|---|
| CC_REGULAR committed | 0.998 | 1.048 (Min Gen Cost, all-in) | 0.974 | **0.775** [0.634–0.964], 221 |
| CC_REGULAR econ_low | 0.723 | 0.963 | 0.978 | **0.787** [0.634–0.987], 216 |
| CC_REGULAR econ_high | 1.324 | 1.454 | 1.642 | **1.285** [1.067–1.709], 216 |
| CC_REGULAR peak | 151.008 (× 33) | 4.326 | 1.760 | **1.384** [1.163–3.331], 221 |
| CC_CHP c / el / eh / pk | 1.029 / 0.946 / 1.857 / 123.684 | 1.029 / 0.946 / 1.427 / 4.248 | 0.945 / 0.948 / 1.593 / 1.708 | **0.742 / 0.754 / 1.231 / 1.326** |
| CT_PEAKER econ_low | 1.27 | 1.146 | 0.855 | **0.637** [0.386–0.950], 147 |
| CT_PEAKER econ_high | 2.18 | 1.413 | 1.288 | **0.962** [0.765–1.114], 147 |
| CT_PEAKER peak | 433.95 (× 33) | 5.388 | 1.524 | **1.132** [0.851–1.437], 147 |
| CT_PEAKER committed (variant only) | 1.14 (start proxy) | 1.315 | 0.847 | **0.622** [0.434–0.950], 147 |
| ST_GAS committed | 0.91 | 2.605 | 1.075 | **0.823** [0.784–0.880], 38 |
| ST_GAS econ_low | 1.02 | 1.731 | 1.075 | **0.828** [0.791–0.977], 38 |
| ST_GAS econ_high | 1.20 | 2.043 | 3.166 | **2.419** [1.013–3.426], 38 |
| ST_GAS peak | 105.6 (× 33) | 4.096 | 3.230 | **2.472** [1.074–4.808], 38 |

**Fleet heat-rate divisor (2023)**, capacity-weighted, with the bin `Plant_Avg_HR` in brackets: CC_REGULAR 7.553 [7.649], CC_CHP 7.884 [7.884], CT_PEAKER 11.778 [11.209], ST_GAS 11.360 [11.191].

**Incremental-to-average heat-rate ratio** (CAMPD TX 2023 unit OLS, cap-weighted). The ratio has no units, so the basis change leaves it unchanged. The artifact's `bands_incremental_basis_p50` divides each band by it.

| Group | Ratio | No-load share of fuel at p99 load | Units |
|---|---|---|---|
| CC_REGULAR | 0.836 | 12.5 % | 122 |
| CC_CHP | 0.804 | | 32 |
| CT_PEAKER | 0.799 | 17.6 % | 100 |
| ST_GAS | 0.863 | 7.9 % | 41 |

- `fleet_HR × band = slope_HR × (band ÷ ratio)`. Carrying the slope as its own fleet field (Q2) therefore moves no offer. It only states the band on its proper basis.
- The CC no-load share (12.5 %) agrees with phase 0's UC no-load reading (10.9 % of CC energy cost).

**Read.**
- **Measured CC and CT offers on the dispatch basis sit below the keeper's fitted bands.**
  - The committed and econ_low bands are at 0.6–0.8 of the fleet average rate. That is consistent with incremental cost below average cost (ratio 0.80–0.84).
  - The CT econ_high is 0.96, against the keeper's 2.18.
- **The SCED top of curve is low.** The CC peak is 1.38, the CT peak 1.13. This matches R-ERCOT-9's measured DAM top offers (CCGT median $24).
- **ST_GAS keeps a steep upper range.** Its econ_high is 2.42, against the keeper's 1.20. It is a broad hockey-stick shape on units that do run (FINDING-rule14 §0 (a)).

## 2. Fixed-dispatch re-price, 2019, dispatch-basis artifact (`reprice_2019.json`)

Each marginal gas tranche of a re-banded class is scaled as `Δmc = mc · (m_new/m_old − 1)`. The econ-slice position comes from the registered ramp geometry (n = 6, mid = 0.35, top-refine). A zone takes the mean Δmc of its own marginal units, otherwise the hour's mean. Contributions are additive and sum exactly to the total.

| leg ($/MWh, load-weighted) | keeper | UC | UC + CT committed variant |
|---|---|---|---|
| CT_PEAKER econ | −0.81 | −2.05 | −2.05 |
| CT_PEAKER committed | — | — | −1.11 |
| ST_GAS econ | +0.46 | +0.57 | +0.57 |
| ST_GAS committed | −0.15 | −0.06 | −0.06 |
| CC_CHP econ | −0.26 | −0.32 | −0.32 |
| CC_REGULAR econ / committed | +0.07 / −0.03 | −0.10 / 0.00 | −0.10 / 0.00 |
| **body subtotal** | **−0.71** | **−1.95** | **−3.06** |
| peak (marginal rows CC_CHP / CC_REGULAR / ST_GAS: keeper 13 / 3 / 17, UC 13 / 3 / 2) | −5.69 | −5.63 | −5.63 |
| LW mean: base → body-only | $49.41 → $48.70 | $55.32 → $53.37 | → $52.26 |
| C3a body-only | +4.6 % | +14.6 % | +12.3 % |

First cut on the lineage basis, for the record: body +4.38 / +3.06 / +2.44, of which CC_REGULAR econ was +3.23 / +3.25.

**Biases, stated.**
- **No re-dispatch.**
  - Cheaper CT and CC offers would pull those units in.
  - A steeper ST top would push ST out.
  - A first-order reading therefore over-states the size of each leg.
  - The peak leg prices a ~$2,800 tranche down to ~$30 without letting the next unit or ORDC set the price. It over-states the fall by far.
- **The whole offer is scaled.** VOM and the additive P1 adjusters scale with it: start markup, `cc_committed_offer_margin`, the conditional surfaces.
- **The 2019 values are extrapolated.** They come from 2023 offers on the 2023-normalized multiplier; no SCED exists for 2019.

## 3. What this says for the owner

- **On a consistent basis, the measured bands are close to neutral for the keeper.** 2019 C3a moves +6.2 % → +4.6 % at fixed dispatch.
- **For the UC they close about a quarter to a third of the 2019 gap.** C3a goes +18.8 % → +14.6 %, or +12.3 % with the CT committed variant. The largest downward leg is the CT econ band.
- **About 12–15 points of UC C3a remain unexplained.** They sit in the hours where the UC holds cheap capacity offline (phase 0 §3). Only phase 1b can show the merit-order response. Phase 1b is held until the owner rules on Q2 and the CT stacked proxy, and UC-3-ERCOT reports.
- **The keeper path's own basis fix, `ercot_offer_hrmult_ep_rebasis`, is routed to the owner.** UC-DESK has not acted on it.

## Log entry

- 2026-10-14 · UC-BANDS-ERCOT phase 1a · zero LP.
  - SCED UC-basis bands derived (2023 delivery, one value for all years); stop check PASS.
  - Re-normalized the same day on the dispatch basis (EP monthly gas, fleet measured HR), on UC-DESK approval.
  - Fixed-dispatch 2019 body re-price, dispatch basis: keeper −$0.71 (+4.6 %), UC −$1.95 (+14.6 %), CT variant −$3.06 (+12.3 %). Lineage first cut: +$4.38 / +$3.06 / +$2.44.
  - The peak (× 33 removal) leg is −$5.6 and not credible at fixed dispatch.
  - No field added; no matrix cell moved.
