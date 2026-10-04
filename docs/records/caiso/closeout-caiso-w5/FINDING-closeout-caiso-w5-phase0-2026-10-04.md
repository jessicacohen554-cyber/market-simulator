# FINDING closeout-CAISO-w5: phase 0 (zero LP), the CAISO intra-gas ordering (2026-10-04)

**Charter.** Desk, 2026-10-04: the intra-gas lane, full span, stacked on w3 with w3 as the control. CC_REGULAR
over-runs while CT_PEAKER, ST_GAS and CT_CHP under-run in every year. Find which measured input sets that ordering.
The desk's candidates:
- unit heat rates (CAMPD own-year vs static);
- start/min-run physics (rule 18);
- the RA must-offer bridge's min_gen favouring CCs;
- delivered gas by unit location.

The CHP limb is adjudicated and stays out without new evidence.

**Control.** The w3 probe legs `closeout_caiso_w3_a1_<y>` (P1 `unit_marginal`, `system`, floors) and the span's pinned
shared frames.

**Branch.** `claude/closeout-caiso-w5`, cut from `73d601fe`.

**Outcome.**
- The ordering is not set by a mispriced measured input.
- The CT_PEAKER / ST_GAS energy the model misses is mostly energy that ran when the measured DA and RT trading-hub
  prices were both below the unit's offer: an out-of-market (local) commitment.
- No zero-DOF lever exists on the data in hand.
- The admissible route is the caiso-81 OPEN item: a measured per-year local-commitment source.

## 1. Census of the missed energy

Probe `_closeout_caiso_w5_intragas_census.py`, output `_intragas_census.json`.

Actual = EIA-923 plant-month levelled on the plant's CEMS hourly. "Missed" = plant-hours the plant ran in reality
above its model output.

| TWh | CT_PEAKER 2020 | CT_PEAKER 2023 | ST_GAS 2020 | ST_GAS 2023 |
|---|--:|--:|--:|--:|
| model / actual | 2.96 / 4.86 | 3.01 / 4.15 | 0.52 / 1.76 | 0.04 / 1.31 |
| missed: priced out (offer > model λ) | **3.63** | **2.93** | **1.32** | **1.25** |
| missed: at capability | 0.07 | 0.10 | 0.00 | 0.00 |
| missed: no LP unit | 0.01 | 0.01 | 0.07 | 0.03 |
| offer − model λ, energy-weighted p25 / p50 / p75 | 4.6 / 9.1 / 15.8 | 5.1 / 13.0 / 26.2 | 5.4 / 10.2 / 14.6 | 11.9 / 20.8 / 31.1 |

The CC_REGULAR excess (model above actual, gross) is 15.1 / 10.5 TWh in 2020 / 2023. Of that, the RA must-offer bridge
floor carries 2.44 / 1.60 TWh, and the rest is economic.

The full-span census (all seven years) is appended to the JSON.

## 2. The desk's four candidates

1. **Unit heat rates.**
   - `measured_ct_heat_rates` (K; caiso-146, the CAMPD loaded-window artifact) is in the LP. Sentinel 57482's
     committed tranche is 8.75 against measured 8.83, and 56803's is 8.68 against 8.76.
   - The economic and peak tranches sit ×1.11–1.15 above the measured rate. That is the keeper's measured CAISO bid
     surface (`measured_offer_surface` K, caiso-257: CT-only, from PUB_DAM_GRP bids), consistent with the
     default-energy-bid cost + 10 %. It is real bid structure, not a heat-rate error, and rule 1 forbids tuning it to
     volume.
   - ST_GAS rides `measured_st_heat_rates` (K).
   - Unit-level CAMPD gross rates: peaker CTs 8.47 gen-weighted, ST 13.1, CC 7.38. These sit where the LP's loaded
     rates do once the gross→net and bid-surface layers are accounted for.
2. **Start/min-run physics.** It does not bind. The missed energy is priced, not limited by capability or commitment.
   Peakers are fast-start, and rule 18 forbids bridging them.
3. **The RA bridge.** CC energy at the floor is 2.4 / 1.6 TWh, a minority of the CC excess. Its min-load is measured
   (0.570, owner R-11/R-14).
4. **Delivered gas by location.** `caiso_zonal_gas_basis` is armed (w1 arm 2, measured PG&E/SoCal citygate basis).

## 3. The decisive test: did the missed energy clear the measured market?

Probe `_closeout_caiso_w5_peaker_price_test.py`, output `_peaker_price_test.json`.
- Population: priced-out missed plant-hours, 2021–25 (the years with OASIS prints).
- Comparison: the plant's cheapest available P1 offer against the measured trading-hub print of its zone (TH_NP15 /
  TH_ZP26 / TH_SP15, DAM and RTM hourly).

| TWh | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|--:|--:|--:|--:|--:|
| **CT_PEAKER** DA clears / RT only / **neither** | 0.38 / 0.10 / **1.38** | 0.59 / 0.22 / **2.24** | 1.03 / 0.20 / **1.67** | 0.96 / 0.29 / **2.17** | 0.49 / 0.22 / **1.57** |
| neither: offer − DA, p50 | 25.4 | 42.0 | 29.9 | 20.2 | 23.7 |
| DA clears: model λ − DA, p50 | −16.5 | −21.8 | −22.4 | −15.7 | −12.7 |
| **ST_GAS** DA clears / RT only / **neither** | 0.31 / 0.03 / **0.62** | 0.22 / 0.02 / **0.79** | 0.42 / 0.05 / **0.76** | 0.02 / 0.00 / 0.05 | 0.00 / 0.00 / 0.05 |
| neither: offer − DA, p50 | 32.8 | 46.3 | 34.0 | 19.1 | 27.2 |

2021 also has 0.93 TWh (CT) / 0.21 TWh (ST) with no print, Jan–Apr.

**Reading.**
- **About 60–75 % of the missed peaker and steam energy ran in hours when neither measured market would dispatch it at
  its offer.** The measured DA print sits $20–46 below the offer.
- That is the signature of out-of-market local commitment: exceptional dispatch, RUC, minimum-online constraints for
  contingency positioning, and RMR/RA local must-offer. caiso-71 §3 and the caiso-79/81 design named exactly this, and
  a pure LP merit order cannot produce it.
- **The DA-clears part** (0.4–1.0 TWh of CT) is the model λ running $13–22 below the measured DA print in those hours.
  That is the adjudicated evening under-price (R-CAISO-21: DART basis + C3c tail).
- **The ST_GAS limb vanishes after 2023.** The OTC steam units retired, so 2024–25 hold 0.05 TWh. This is consistent
  with reliability-driven commitment of named local units.

## 4. Why there is no lever today, and the admissible route

**Rejected routes.**
- **The ramp-driven local-commitment floor** (caiso-local-commitment-driver design, 2026-07-12) was REFUTED at its own
  LOYO pre-commitment (caiso-81). Its driver was not year-stable: commitment collapsed 80–97 % in 2025 at
  equal-or-steeper ramps.
- **Pinning units to the observed out-of-market energy** is forbidden (rule 13).
- **Lowering offers to pull the energy into merit** would tune the bid surface to a volume residual (rules 1 and 13).
  The gap is also $20–46, far beyond the ×1.11–1.15 bid layer.

**The admissible route** is the caiso-81 OPEN item: a measured per-year local-commitment source. CAISO DMM publishes
exceptional-dispatch and minimum-online-commitment volumes by type, reason and area (DMM annual and quarterly
reports). That source could size a rule-17 floor with:
- **a window:** the measured on-hours of the named local units;
- **a driver:** a published local reliability requirement (LCR/LCT need by area and year, `lcr_tsl_published` K);
- **a forward story:** the LCR studies publish forward years.

It needs:
- the download (DMM report tables, plus an area→unit crosswalk);
- an owner ruling on the design before any build (rules 13 / 17 / 19). It would replace, not stack on, any existing
  floor on those units.

**Size.** The neither-market energy, CT + ST, is about 1.6–3.0 TWh/yr in 2021–23. If that energy were carried as
local commitment, it would displace CC roughly one for one.
- That is enough to move C1 CC_REGULAR 2020 (+5.00 / ±4.60) into band.
- It would also push CC down in the years already under or near zero (2023 −1.07, 2024 −1.67, 2025 −0.36). Those
  stay inside ±5.1–5.3 at that size.
- That is why the PASS→FAIL watch must be declared in any PRECOMMIT.

## 5. Disposition

- No PRECOMMIT and no shards.
- I've asked the desk to choose between (i) stopping here or (ii) fetching the DMM tables and drafting the design
  PRECOMMIT for an owner card.
- The w3 promotion request stands.
- No `ScenarioConfig` field was added, so there is no matrix row.
