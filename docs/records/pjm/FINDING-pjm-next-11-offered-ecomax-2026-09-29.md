# FINDING — PJM-NEXT-11: offered EcoMax is real but too small, 2022 is explained by PJM's own offers, and C3a 2019/2020 is a level error, not compression (zero LP)

**Keeper** `2026-09-28-pjm-next8-exitfix` (bundle `results/calibration/pjmnext8_xf_span`), unchanged. **Zero LP, zero shards.**
**Corpus:** PJM DataMiner2 `energy_market_offers`, 2019–2025, all 84 month-files re-fetched this session (gitignored, `fetch_pjm_energy_offers.py --years 2019 … 2025`).
**Probes → JSON** (committed):

| probe | output | card |
|---|---|---|
| `scripts/probes/_pjmnext11_offered_ecomax.py` | `results/phase0/pjm/_pjmnext11_offered_ecomax.json` | 1 |
| `scripts/probes/_pjmnext11_ecomax_bound.py` | `results/phase0/pjm/_pjmnext11_ecomax_bound.json` | 1 |
| `scripts/probes/_pjmnext11_c3_compression.py` | `results/phase0/pjm/_pjmnext11_c3_compression.json` | 3 |
| `scripts/probes/_pjmnext11_margin_audit.py` | `results/phase0/pjm/_pjmnext11_margin_audit.json` | audit (a) |
| `scripts/probes/_pjmnext11_bulk_price.py` | `results/phase0/pjm/_pjmnext11_bulk_price.json` | audit (b) |

The LONG_RUN segment is the committed mid-curve surface's own segmentation, **imported** from `derive_pjm_offer_midcurve.py` (`_unit_physics` + `_segments`, own-year medians). Nothing was re-derived and the committed surface is untouched (rule 23).

## 1. Card 1 — offered EcoMax: measured, flat across years, and too small

Per LONG_RUN unit-hour: `E` = `avg_ecomax`, `T` = the offer curve's top breakpoint in the same row. `D` = PJM's own curve read at the actual DA LMP, clipped to `E`. `Dm` = the same curve read at the keeper's P1 price.

| year | units | **E/T** | C1 COAL_BIT | within-synced over-run (TWh) | max cap effect on C1 (TWh) | D/E (actual price) | Dm/E (model price) |
|---|---|---|---|---|---|---|---|
| 2019 | 89 | **0.927** | +10.61 | +10.47 | **−1.53** | 0.55 | 0.67 |
| 2020 | 88 | **0.946** | +3.9 | +7.70 | −0.97 | 0.45 | 0.61 |
| 2021 | 86 | **0.930** | +17.14 | +10.07 | **−1.87** | 0.60 | 0.70 |
| 2022 | 87 | **0.923** | +6.8 | +1.87 | −0.46 | 0.57 | 0.59 |
| 2023 | 80 | **0.947** | +0.3 | −0.58 | −0.15 | 0.43 | 0.52 |
| 2024 | 66 | **0.949** | +0.9 | −2.11 | −0.15 | 0.49 | 0.56 |
| 2025 | 70 | **0.930** | +11.3 | +11.43 | **−1.92** | 0.63 | 0.69 |

**The cap-effect column is an upper bound.** It is the model's COAL_BIT energy above `E/T` × each bench plant's model maximum, minus CAMPD's energy above the same line. It assumes every coal plant carries the segment-mean ratio.

**Reading:**
- **Real.** PJM's LONG_RUN units offer 5–8 % below their own curve top in every year, and the ratio is flat across hours (HE 3/9/15/21 within 0.01) and across net-load bins.
- **Partly year-discriminating.** 2019/2021/2025 (and 2022) sit about 2 points below 2023/24.
- **Too small.** Capping COAL_BIT at its offered EcoMax would close at most 11–14 % of the out-of-span over-run: −1.5 of +10.6 (2019), −1.9 of +17.1 (2021), −1.9 of +11.3 (2025).
- **Misordered.** 2020 over-runs within-synced (+7.7 TWh) at the fit years' ratio (0.946). 2022 has the lowest ratio (0.923) and the smallest over-run.
- **Gas-steam admixture bound** (pjm-h9: ≈18.9 % of LONG_RUN capacity). The ratio is a segment total, so a coal-only ratio could differ from it by at most the admixture share times the gas-steam/coal ratio difference. Even if every point of the 2-point year gap were coal, the bound above already assumes the full gap applies to coal, so the admixture can only shrink it.
- **No status field.** The feed carries no fuel-conservation / max-emergency flag (columns: curve, start costs, `min_runtime`, `min/avg/max_ecomax`, `min/avg/max_ecomin`). Economic and physical EcoMax cannot be separated in it.

**Rule-13 admissibility (stated, then moot).**
- *For:* EcoMax is a unit-submitted MW limit that PJM publishes every year, so a forward year could carry a trailing-years ratio.
- *Against:* EcoMax is itself an economic choice. Units lower it to conserve fuel or to avoid the top of their heat-rate curve, so a same-year ratio carries the outcome it would explain. Only a trailing-years ratio passes the forward test.
- *Moot:* at ≤ 2 TWh of effect, and with the year order wrong, it would not be a lever even if admitted. **No design card, no solve.**

**Offer-implied loading (`D/E`).** PJM's own curves, read at the actual price, imply higher coal-like loading in 2019/2021/2025 (0.55–0.63) than in 2023/24 (0.43–0.49). So real coal *was* more in merit in the over-run years; the model over-loads beyond that. Reading the same curves at the **model's** price adds +0.75 to +7.0 GW (`Dm − D`). But that price-level shift orders the years 2020 > 2019 > 2023 > 2025 > 2024 > 2021 > 2022, which is **not** the over-run order. The model's price level alone does not discriminate 2021/2025 from 2023/24 either.

## 2. Card 2 — 2022 is PJM's own 2022 offers, not a coal-supply ceiling

The keeper floors COAL_BIT econ tranches at PJM's measured LONG_RUN mid-curve (`pjm_offer_midcurve_segments` ⊇ `LONG_RUN`, own-year ladder × daily gas). Converted to $/MWh at the annual gas price:

| year | gas | LONG_RUN offer, s55 / s85 ($/MWh) | coal fuel SRMC at 10.4 HR ($/MWh) | offer ÷ fuel SRMC |
|---|---|---|---|---|
| 2019 | 2.57 | 18.4 / 19.9 | 22.2 | 0.8–0.9 |
| 2020 | 2.03 | 15.8 / 17.3 | 21.7 | 0.7–0.8 |
| 2021 | 3.72 | 23.9 / 27.6 | 21.5 | 1.1–1.3 |
| **2022** | 6.45 | **50.8 / 61.1** | 27.3 | **1.9–2.2** |
| 2023 | 2.54 | 22.5 / 26.5 | 32.0 | 0.7–0.8 |
| 2024 | 2.19 | 20.1 / 23.4 | 31.3 | 0.6–0.7 |

- In 2022, PJM's coal-like units offered at about **2× their delivered fuel cost**, the fuel-scarcity / opportunity-cost bidding of that year. The keeper already carries it through the measured floor, which holds COAL_BIT econ bands at 46 TWh (vs 69 in 2021).
- **The PJM-NEXT-10 fuel-ratio reading (delivered coal ÷ gas) used the wrong operand for 2022.** Delivered cost did not set coal's offer that year; PJM's own offers did.
- **No inventory ceiling is needed to explain 2022.** `coal_fuel_inventory` stays `U` for PJM. It is also no candidate for 2019, a stock-building year, so it could at most touch 2021.

## 3. Card 3 — C3a 2022 / C3b 2022 are the tail object; C3a 2019/2020 are NOT

Model = keeper P1 system price, load-weighted per hour. Actual = PJM RT (the C3a/C3b bench kind). The sorted-quantile bands sum to the equal-hour mean gap ($/MWh):

| year | C3a (LW) | p50 ratio | bottom 90 % of hours | top 10 % | reading |
|---|---|---|---|---|---|
| 2019 | +11.5 % | 1.18 | **+3.93** | −0.79 | **level** (bulk too high) |
| 2020 | +15.6 % | 1.26 | **+4.50** | −0.88 | **level** (bulk too high) |
| 2021 | +1.7 % | 1.16 | +3.49 | −2.38 | cancels |
| 2022 | −11.8 % | 1.12 | +4.36 | **−9.19** | **tail** (compression) |
| 2023 | +4.8 % | 1.20 | +4.12 | −1.89 | cancels |
| 2024 | −0.1 % | 1.13 | +2.83 | −1.96 | cancels |
| 2025 | −2.3 % | 1.14 | +3.10 | −3.03 | cancels |

- **2022 is confirmed as pjm-h12's variance-compression object.** The top-decile shortfall (−$9.19) is twice the bulk excess. C3b 2022 (monthly NRMSE 0.256) is driven by June–August (model $74 vs $89–103) and December / Winter Storm Elliott ($74 vs $129).
- **2019/2020 are NOT compression.** Their miss is a bulk-level excess (median +18 % / +26 %) with little top tail to offset it.
- **The bulk excess is present in EVERY year** (median ratio 1.12–1.26). C3a passes in 2021 and 2023–25 **by cancellation** against the missing top tail. The training-span C3a pass is therefore not evidence that the price level is right. Stated at full magnitude.

## 4. Audit (a) — the over-run is RESPONSE, not price (owner card: *"Do both audits here"*)

Per bench COAL_BIT plant-hour: loading = MW ÷ the plant's CAMPD p99 net output, the same denominator on both sides. Model hours are binned by the keeper's own zonal P1 price, actual hours by the zone's PJM DA hub. The energy gap then splits exactly into **response** (more MW at the same price) + **price** (model hours sitting in dearer bins):

| year | gap (TWh) | **response** | price | median price model / actual |
|---|---|---|---|---|
| 2019 | +18.76 | **+17.87** | +0.89 | 26.9 / 24.6 |
| 2020 | +12.16 | +6.57 | **+5.59** | 22.9 / 19.2 |
| 2021 | +15.66 | **+11.78** | +3.88 | 35.1 / 32.1 |
| 2022 | +7.61 | **+10.17** | −2.56 | 61.6 / 61.3 |
| 2023 | −0.11 | +1.67 | −1.79 | 30.2 / 29.0 |
| 2024 | −0.07 | +2.80 | −2.86 | 27.6 / 27.5 |
| 2025 | +13.71 | **+15.13** | −1.42 | 38.4 / 39.1 |

Loading by price bin shows why:
- **Real PJM coal is much flatter in price.** Across $15–60/MWh it loads at 0.36–0.50 of p99 in 2020–2025, rising only above ~$80. 2019 is the exception: it rises from 0.39 to 0.66 by $55, but still less steeply than the model (0.34 → 0.83).
- **The model's coal is steep:** 0.3–0.4 at $15–25, rising to 0.6–0.9 at $40–80.
- 2023/24 prices sit where the two curves cross, so those years fit. In 2019 (cheap coal) and 2021/2022/2025 (more hours at $35–80), the model loads coal up its offer stack and real coal does not.

**PJM's own offers do not explain the flat curve either.** Their curves read at the actual price imply loading rising with price, the same way the model's does (§1, `D/E`). So the flat actual response is not produced by the offered MW (§1) or by the offered price. Something non-price holds real coal output at intermediate load. The candidate that fits a flat, price-insensitive curve is **DA self-scheduling** (fixed-MW, price-taking blocks), which the PJM IMM reports by fuel in its State of the Market. The offers corpus carries **no self-schedule flag**, so it cannot be tested from data in the repo. **OPEN**, next test named in §6.

## 5. Audit (b) — the bulk price excess is a too-high price FLOOR, the same object seen from the price side

Both prices are divided by the same daily delivered gas series (HH + PJM basis), giving an implied heat rate (MMBtu/MWh):

| year | model p10 / p50 / p90 | actual p10 / p50 / p90 |
|---|---|---|
| 2019 | 7.1 / 8.2 / 10.8 | **5.2** / 7.0 / 10.6 |
| 2020 | 7.1 / 8.5 / 11.2 | **4.8** / 6.7 / 10.6 |
| 2021 | 6.9 / 8.1 / 10.6 | **5.1** / 7.1 / 11.8 |
| 2022 | 7.4 / 8.9 / 10.9 | **5.5** / 8.0 / 13.9 |
| 2023 | 7.6 / 9.5 / 11.5 | **4.9** / 7.8 / 13.6 |
| 2024 | 8.4 / 10.3 / 12.2 | **5.0** / 8.6 / 17.5 |
| 2025 | 7.8 / 9.4 / 12.4 | **5.1** / 8.2 / 16.6 |

- In every year the actual low end prices **below any gas unit's fuel cost** (an implied heat rate of about 5). There the marginal unit is coal, nuclear, imports or renewables, i.e. something cheaper than gas.
- The model almost never goes there: its p10 sits at gas-CC cost (about 7–8).
- Read with §4, this is plausibly **one object**. In reality coal sits partially loaded and price-setting at the low end. In the model it loads fully and hands the margin to gas, which lifts the floor.
- *Caveat:* the model's zone-hour marginal emission rate reads coal-marginal 19–37 % of hours, but an LP marginal emission rate blends units across binding constraints, so it is not a reliable class label. It is not used as evidence.

## 6. Verdict

| object | status | next test |
|---|---|---|
| COAL_BIT out-of-span over-run (2019 +10.61, 2021 +17.14), CT_PEAKER 2021 | **OPEN.** Offered EcoMax falsified (≤ 14 %, misordered). The over-run is response, not price (§4): real coal is much flatter in price than model coal. | Intake PJM's measured **DA self-scheduled MW by fuel, by year** (IMM State of the Market). If coal self-scheduled share is year-discriminating, design a zero-DOF self-schedule block for the coal econ bands. Separately, PJM's published **marginal-fuel shares by year** test §5's "coal is the low-end marginal unit". |
| C3a 2019/2020 | **OPEN — relabelled from "compression" to "price floor"** (§3, §5) | Same data as the row above. The floor and the coal response are plausibly one object and should be tested together. |
| C3a/C3b 2022 | variance-compression object (pjm-h12), confirmed | unchanged |
| 2022 COAL_BIT "exception" | explained: PJM's own 2022 offers, already in the keeper | none |

Nothing here is labelled a model-class limit: no lever was found, and none was shown to be unrepresentable.
