# FINDING — soco-83: SOCO's gas split is ST boilers committed OUT OF MERIT against Southern's own lambda; neither CC nor ST offers are mis-priced (zero LP)

Lane soco-83, 2026-09-28. Keeper `2026-09-27-soco82-perunitdark-regen` (bundle `results/calibration/soco82_span`).
Probe `scripts/probes/_soco83_gas_split.py` (`plants`, `offers`); table `soco83_gas_offers.csv`. No LP was solved.

## 1. The row, and where the gas split sits

- The ISO-blocking row is **2021 C1 CC_REGULAR +4.99 TWh / +3.05 pp** (band ±3 pp).
- The same shape appears in every year: **CC over-runs and ST_GAS under-runs**.

| year | CC_REGULAR model − bench (TWh) | ST_GAS model − bench (TWh) | CT_PEAKER model − bench (TWh) |
|---|---|---|---|
| 2019 | +5.98 | −4.88 | +6.30 |
| 2020 | +3.73 | −4.39 | +5.11 |
| 2021 | +4.98 | −5.73 | +0.46 |
| 2022 | −4.13 | −5.43 | −1.98 |
| 2023 | +4.12 | −4.78 | +5.44 |
| 2024 | +2.98 | −4.68 | +3.63 |
| 2025 | −0.82 | −4.99 | +0.17 |

- **Where the ST_GAS deficit sits:** three plants every year — Gaston (26), Jack Watson (2049), Yates (728). In 2021 Crist-gas
  (641) also reads 0.00 model TWh against 1.56 bench.
- **Where the CC surplus sits:** Franklin (7710), Ratcliffe (57037) and Harris (7897), at +1 to +2.2 TWh each.

## 2. Offers against Southern's own marginal cost (FERC-714 Sch. 6 lambda, intaken this lane)

**Method.** For each plant-class, the keeper's own `fleet_only` offer (`mc_base`, capacity-weighted across its tranches) is set
against Southern's hourly system lambda. The comparison uses only the hours the plant's CEMS gas units were synchronised. Barry's
gas CEMS units are its CC, so Barry's ST row is excluded as unreadable.

| year | CC offer (TWh-wtd median) | CC: λ < offer, share of synced h | CC: median λ − offer | ST offer | ST: λ < offer | ST: median λ − offer |
|---|---|---|---|---|---|---|
| 2019 | $20.94 | 0.37 | **+$4.32** | $32.80 | **0.85** | **−$6.42** |
| 2020 | $17.72 | 0.45 | +$0.64 | $27.79 | **0.88** | **−$9.10** |
| 2021 | $28.86 | 0.40 | **+$3.26** | $45.91 | **0.71** | **−$12.44** |
| 2022 | $53.14 | 0.43 | +$7.56 | $83.29 | **0.60** | **−$15.17** |
| 2023 | $22.28 | 0.33 | +$2.54 | $34.05 | **0.70** | **−$8.31** |
| 2024 | $20.86 | 0.36 | +$2.89 | $32.59 | **0.72** | **−$8.07** |
| 2025 | $29.79 | 0.44 | +$2.65 | $46.44 | **0.81** | **−$13.92** |

- **CC is economic by Southern's own measure.** Lambda sits a median $0.6–7.6 above the CC offer in CC's synced hours.
- **ST boilers run out of merit.** In 60–88 % of their synced hours lambda is below their offer, by a median $6–15/MWh.
- **2021 at plant grain, the four clean ST plants** (Greene County, Gaston, Yates, Watson):
  - **3.13 of 5.56 TWh** of CEMS gross was produced while lambda sat below the plant's offer.
  - In those hours the boilers ran at a median **13–26 % of nameplate**, i.e. held near minimum load.
- **All years, the same four plants:** out-of-merit ST energy (CEMS gross while λ < offer) / total is 7.14 / 9.62 (2019),
  5.87 / 7.35, 3.13 / 5.56, 3.07 / 7.06, 4.61 / 9.03, 4.21 / 7.90 and 4.63 / 6.73 TWh (2025).
- **Model price vs lambda:** +$4.6 / +$4.2 (2019 / 2020), within ±$2.4 in 2021 and 2023–2025, −$7.3 in 2022 (hourly r 0.43–0.61).
  The price level is not what separates CC from ST.

## 3. Reading

- **Neither offer is mis-priced against Southern's own marginal cost.**
  - CC offers sit below lambda, consistent with Southern running CC as base/intermediate.
  - ST offers sit at their measured cost: `measured_st_heat_rates` (K) and the measured gas basis (soco-72). The ST/CC offer ratio
    is 1.55–1.60, which is the heat-rate ratio.
  - An offer lever that pulled ST below its measured cost would be the fitted mechanism rule 1 forbids.
- **The ST deficit is commitment conduct.** Southern holds boilers committed near minimum load through hours its own lambda says
  are uneconomic for them. A committed unit at minimum load is not marginal, which is exactly what a lambda below its offer
  looks like.
  - This agrees with SOCO-62's decomposition: 66–79 % of the ST deficit is commitment hours.
  - It also agrees with the 2019 coal finding (FINDING-soco-82 §3).
- **The CC surplus is the mirror.** In the model, the energy those boilers produced out of merit is served by the next-cheapest
  units, CC first. The +3.05 pp row is the downstream image of measured non-economic ST commitment.
- **What the incumbent commitment row reaches.** `soco_gas_st_campaign_commitment` (K) holds a committed boiler at its p5
  plant-basis level only inside runs the P0 pass already makes. SOCO-62 measured its full reach at 0.61 / 0.82 TWh (2023 / 2024)
  if every idle measured-synced hour were committed. The measured conduct gap (3.1 TWh in 2021) is several times that.

## 4. Lever queue (§5.8) status

| lever | status | reason |
|---|---|---|
| offer-side levers on CC or ST (bands, incremental HR, start amortization) | refused / G | ST is at its measured cost; incremental-HR bands move the split the wrong way (SOCO-63); `tranche_startup_amortization` is G (owner NO) |
| `soco_gas_st_campaign_commitment` level | do-not-raise | the p5 level is correct (SOCO-62); raising it is fitting |
| `st_gas_mustrun_oom_level` | U for SOCO | the MISO construct conditions a must-run level on out-of-merit hours (MISO: CC-headroom set). The SOCO analogue would condition on λ < offer, a new conditioning set. It is a rule 17 floor whose driver is measured-as-non-economic but **unidentified**, so it needs an owner ruling before any build |
| `st_gas_mustrun_p25` / `_measured_level` | U | same family, same driver question; SOCO carries no `st_gas_mustrun_per_plant` arm, and stacking one on the campaign row is a rule 19 question |

## 5. Decisions put to the owner (decision cards, this session)

1. **How to carry 2021 CC_REGULAR.** Options:
   - build a measured out-of-merit ST commitment level (PRECOMMIT first);
   - extend the v3.10 scoped ledger to the mirror row;
   - rest the row at NOT-YET.
