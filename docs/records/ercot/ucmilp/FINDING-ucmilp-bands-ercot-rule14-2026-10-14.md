# FINDING — UC-BANDS-ERCOT, rule-14 follow-up: heat-rate and gas basis (b), ST_GAS econ_high (a)

Lane UC-BANDS-ERCOT, 2026-10-14. Authorized by UC-DESK (zero LP, no solves, apply nothing).
Follows `RESULT-ucmilp-bands-ercot-1a-2026-10-14.md` §3, which named candidates (a) and (b).

Files in `data/bands/`:
- `basis_factors.json` (the measured ratios);
- `reprice_basis_2019.{py,json}`: keeper bands with a basis-consistent factor;
- `reprice_sced_basis_2019.json`: the phase-1a SCED bands with the same factor, produced by `reprice_2019.py`.

## 0. Answer

1. **(b) is a real input-derivation defect, almost all of it on the gas side.**
   - **Heat rate:** small. The fleet multiplies the CAMPD operating rate, while the bands were normalized on the bin `Plant_Avg_HR`. Fleet ÷ normalizer, capacity-weighted, 2019: CC_REGULAR 0.986, CC_CHP 1.000, CT_PEAKER 1.055, ST_GAS 1.028.
   - **Gas:** large.
     - The DAM and SCED bands were normalized on **Henry Hub − 0.50**.
     - Dispatch prices gas on the **EP-anchored zonal delivered series** (`ercot_zonal_gas_basis` and the EP monthly flags, all armed in the keeper).
     - Over the 2023–25 DAM window, HH−0.50 is **0.885** of the dispatch series. In 2023 alone, the SCED derivation year, it is **0.797**.
     - So every measured band reproduces its offer about 13 % high on the DAM lineage, and about 25 % high for SCED. This is the inconsistency ERCOT-117 proved causal (calibration-log/ercot.md, 2026-07-26).
2. **The (b) fix removes most of the keeper's 2019 C3a error, but only about a third of the UC's** (fixed dispatch, body tranches).

   | | keeper C3a | UC C3a |
   |---|---|---|
   | as solved | +6.2 % | +18.8 % |
   | heat-rate factor only | +6.0 % | +18.4 % |
   | gas factor, CC classes only (the DAM-measured core) | +3.0 % | +15.5 % |
   | heat-rate × gas, CC only | +3.3 % | +15.8 % |
   | heat-rate × gas, all four gas classes | **+1.0 %** | **+13.0 %** |
   | SCED bands × basis factor | +5.4 % | +15.5 % (CT committed variant: +13.2 %) |

   - **(b) does not explain the UC gap.** About 13 points of C3a remain after a basis-consistent normalization.
3. **(a) ST_GAS econ_high 3.17 is a broad measured shape, not a few resources and not a tail.**
   - 38 resources carry an econ_high. 28 of them, **65 % of the capacity**, sit above 2.0.
   - The distribution is bimodal:

     | cluster | capacity | econ_high range | units |
     |---|---|---|---|
     | cheap | 35 % | 1.18–1.82 | Lake Hubbard, Cedar Bayou, W A Parish, R W Miller |
     | steep | 58 % | 2.2–7.6 | Braunig, Sommers, Gideon, Handley 4/5, Graham, Stryker Creek, Trinidad, Mountain Creek |

   - Three outliers sit above 12: Barney Davis 12.2, Dansby 16.2, Handley 3 23.1 (7 % of capacity). They do not move the p50.
   - **The steep units do run in 2019 CEMS, about as much as the cheap ones.** Capacity-weighted 2019 on-fraction is 0.267 for the steep cluster and 0.262 for the cheap one; CF is 0.128 and 0.149.
   - **The shape is a hockey stick.** On most steep units the committed / econ_low band is near cost (0.23–1.2) and the top third is posted at 3–7× cost.
   - It is conduct posted on the upper range of units that mostly run low. Price-taking at minimum load is visible on Graham and Trinidad (committed 0.23–0.27).

## 1. (b) detail

**Gas basis on each side.**

| side | series | source |
|---|---|---|
| DAM band derivation (cconly, 2023–25) | HH daily − 0.50 | `derive_dam_offer_hrmults.py` `ERCOT_GAS_BASIS` |
| SCED band derivation (phase 1a, 2023) | HH daily − 0.50 | `derive_ercot_sced_uc_bands.py` (lineage basis) |
| dispatch (keeper 2019–25) | EP-anchored zonal delivered; capacity-weighted mean = `_gas_series` | `ercot_zonal_gas_basis`, `ercot_ep_gas_basis_monthly/_corroborated/_receipts_fallback` |
| markup anchor | `gas_offer_margin_anchor_by_zone` (EP-delivered window means) | `gas_offer_net_revenue_margin` |

**Annual means ($/MMBtu), keeper's own per-year config:**

| year | dispatch series | HH−0.50 | ratio |
|---|---|---|---|
| 2019 | 2.352 | 2.049 | 0.871 |
| 2023 | 2.544 | 2.027 | 0.797 |
| 2024 | 2.104 | 1.748 | 0.831 |
| 2025 | 3.057 | 3.040 | 0.994 |

- The window ratio (2023–25, ratio of means) is **0.8845**.
- An offer-weighted ratio would differ somewhat. The one-row-per-zone `zonal_anchor` probe refuses ERCOT because its applier is capacity-weighted.

**Heat-rate basis (2019 fleet, capacity-weighted):**

| class | fleet HR | bin `Plant_Avg_HR` | fleet ÷ bin | measured coverage (capacity) |
|---|---|---|---|---|
| CC_REGULAR | 7.543 | 7.649 | 0.986 | 99 % |
| CC_CHP | 7.884 | 7.884 | 1.000 | 0 % (`measured_chp_heat_rates` off) |
| CT_PEAKER | 11.826 | 11.209 | 1.055 | 73 % |
| ST_GAS | 11.504 | 11.191 | 1.028 | 82 % |

- Fleet HR = `campd_bins.measured_{cc,ct,st}_heat_rates("ERCOT", 2019)` where present, otherwise the bin rate.
- The DAM summary's frozen divisor (CC 7.741) also differs from today's bin file (7.649), a further 1.2 %.

**Factor applied.** The consistent band is `m' = m × (HR_norm/HR_fleet) × (g_norm/g_dispatch)`. The offer scales by the same factor.
- **Keeper re-price.** It applies `0.8845 ÷ (fleet/bin)` per class. The CC-only rows are the honest reading for the keeper: its CT and ST bands are residual-fitted, not normalized, so the basis argument does not strictly reach them.
- **SCED re-price.** It applies the 2023 ratio, `0.7968 ÷ (fleet/bin)`.
- **Biases:** those of `reprice_2019.py`. There is no re-dispatch, the whole offer is scaled, and the peak leg is excluded.

**Read.**
- The gas-basis inconsistency is the dominant normalization error.
- It explains most of the keeper's 2019 over-price, which the keeper's residual CC deltas (econ_low −0.24) were partly absorbing.
- It leaves about 13 points of the UC's +18.8 % unexplained. That remainder still sits in the hours where the UC holds cheap capacity offline (phase 0 §3, 92 %), so the measured bands do not close it at fixed dispatch.

## 2. Fix, routed (not applied)

1. **The keeper path already has it, built.** `ScenarioConfig.ercot_offer_hrmult_ep_rebasis` (ERCOT-118) re-derives the CC DAM bands on the EP basis from the frozen artifact `offer_curve_dam_hrmults_ep_yearly.json`.
   - It is default off and not armed in the keeper.
   - Its record reads as a rejected probe with a keeper-grade mechanism: ERCOT-118/119 drained C3c through the econ legs.
   - Re-arming it is an owner decision on a keeper lane, not this lane's.
2. **The SCED UC-basis derive** (`derive_ercot_sced_uc_bands.py`, unmerged #7242) should normalize on the EP dispatch series rather than HH−0.50 before any phase 1b.
   - **Rule-23 citation:** this changes no data. It corrects a measured identification basis proven inconsistent by ERCOT-117. The derive is not frozen yet (nothing reads it), so the correction lands before the artifact is consumed. It is not a re-derive against a residual.
   - Proposed as a one-flag change to #7242, for UC-DESK to rule on.
3. **The heat-rate divisor.** The class `Plant_Avg_HR` divisor should be the fleet's own measured operating rate (the same `measured_*_heat_rates`), so that band × fleet HR reproduces the offer. The effect is ≤ 5.5 % (CT). This is the same kind of fix in the same derive.
4. **(a) needs no fix.** ST_GAS econ_high is a measured posted shape on units that run. Whether the model should carry the upper-range conduct as a band is phase 1b's question.

## Log entry

- 2026-10-14 · UC-BANDS-ERCOT rule-14 (b)/(a) · zero LP.
  - Gas basis (HH−0.50 vs EP dispatch) is 0.885 over the window, 0.797 in 2023. HR basis: CC 0.986, CT 1.055, ST 1.028.
  - Fixed-dispatch basis-consistent re-price: keeper C3a +6.2 → +1.0 %, UC +18.8 → +13.0 %. (b) is real but does not explain the UC gap.
  - ST_GAS econ_high: a broad hockey-stick shape (28/38 resources, 65 % capacity > 2.0), and the steep units run in 2019 CEMS as much as the cheap ones.
  - Fixes routed, not applied.
