# FINDING — NWPP-NEXT-7: C1 CC_REGULAR "running long" is the mirror of coal running short (zero LP)

**Lane:** NWPP-NEXT-7, lever 1 of `HANDOFF-nwppnext7-2026-09-26.md`. **LP spent: none.** No shard was launched.
**Keeper read:** #13 `2026-09-26-nwppnext6-path76-ctrederive` (committed bundle, run payload and benchmark).
**Probe:** `scripts/probes/_nwppnext7_cc_long_census.py` → `results/calibration/_nwppnext7_cc_long_census.json`.

## 1. Answer

C1 CC_REGULAR is not a gas-side defect. It is a **gas↔coal substitution error**. In every year the CC_REGULAR
residual and the coal-family residual are near-mirror images: **r = −0.974** over 2019–2025. Total fossil, hydro,
wind, solar and nuclear are all close to EIA-923, so nothing else is displaced.

| Year | CC_REGULAR Δ (C1) | Coal family Δ | Hydro Δ | All-fossil Δ | Hydro actual |
|---|---|---|---|---|---|
| 2019 | **+7.8** | −4.4 | +0.4 | +0.9 | 118.4 |
| 2020 | **+9.9 FAIL** | −9.2 | −0.2 | +2.4 | 131.0 |
| 2021 | −0.6 | +5.7 | +1.7 | +0.4 | 116.1 |
| 2022 | −7.5 | +13.2 | +0.8 | +1.7 | 129.2 |
| 2023 | −1.0 | +7.0 | +2.6 | +0.3 | 104.2 |
| 2024 | **+8.3 FAIL** | −5.1 | +2.8 | +0.6 | 105.0 |
| 2025 | +8.3 (SKIPPED, prelim 923) | −10.9 | +2.8 | −0.0 | 110.3 |

TWh, model − EIA-923. Band ±8.00 TWh.

## 2. The handoff's three questions

1. **Where is CC long?** Nevada (SNV) and Utah (EAST) plants in the low-gas-price years:
   Chuck Lenzie, Apex, Higgins, Harry Allen, Tracy, Silverhawk, Lake Side, Currant Creek.
   Each is +0.5 to +2.5 TWh in 2019 / 2020 / 2024. NW and OR CCs run **short in every year** (Chehalis, River Road,
   Mint Farm, Port Westward).
2. **What does it displace?** Coal. The coal deficit in the CC-long years is concentrated in:

   | Plant | 2019 | 2020 | 2024 | 2025 |
   |---|---|---|---|---|
   | Centralia 3845 (NW) | −5.8 | −5.1 | −2.2 | −1.6 |
   | Colstrip 6076 (INLAND) | −3.9 | −4.5 | −2.1 | −0.3 |
   | Jim Bridger 8066 (EAST) | −2.2 | −2.1 | +0.3 | −0.9 |
   | Hunter + Huntington (EAST) | −1.0 | −0.7 | −2.1 | −6.5 |

   Model Centralia runs ~0 GWh from March to November in 2019, 2020 and 2024, against a measured 200–880 GWh/month.
   Centralia and Colstrip are 100 % contract coal (Colstrip is captive mine-mouth) and file no delivered price.
   Hydro, imports and CT are not the displaced resource: hydro is within ±3 TWh every year, and the all-fossil total
   is within +2.4 TWh.
3. **Does it track low-hydro years?** No. 2020 and 2022 are both high-hydro years with opposite CC signs. 2023 is the
   lowest hydro year and CC is only −1.0. The sign tracks the gas↔coal relative price instead.

**CC heat-rate artifact coverage is not the cause.** `campd_cc_heat_rates_NWPP.csv` covers 22 of 23 benchmark CC
plants. It misses only Clark 2322, which runs **short**. Every long plant except Beaver (§4) has a measured row, at
model/measured ratios of 0.97–1.07.
No population re-derive (rule 23) is indicated.

## 3. The lever that reaches it already exists as a design: the coal take obligation

`FINDING-nwppnext5-coal-take-obligation-design-2026-09-26.md` designed a per-yard annual coal take **floor**
(generalising `coal_fuel_inventory_plant_grain`). It was never solved because owner questions Q1–Q5 are open.
Its binding energy on keeper #13's per-plant coal, and the C1 CC_REGULAR it would leave if every added coal MWh
displaced CC 1:1 (an **upper bound** on the CC reduction; some would displace CT or imports instead):

| Year | Binding, estimator A | Binding, estimator B | CC Δ after A | CC Δ after B |
|---|---|---|---|---|
| 2019 | 3.84 | 10.20 | +3.9 | −2.4 |
| 2020 | 5.36 | 21.35 | +4.6 | **−11.4** |
| 2021 | 0.84 | 3.74 | −1.4 | −4.3 |
| 2022 | 0.16 | 0.51 | −7.7 | **−8.0** |
| 2023 | 1.46 | 2.26 | −2.4 | −3.2 |
| 2024 | 7.20 | 9.43 | +1.1 | −1.1 |
| 2025 | 3.98 | 6.59 | +4.4 | +1.8 |

These are the census's `burn_floor_*` values, which are the `_net` (stock-slack) form. *(Corrected 2026-09-27: first
published as "gross".)*

- **Estimator A** would bring every CC year inside the band at the 1:1 bound.
- **Estimator B** over-corrects 2020 to −11.4 and puts 2022 on the band edge.
- Neither result may **choose** the estimator. Rule 1 and the NWPP-NEXT-5 design both say A vs B is fixed ex ante by
  the owner, on structure. This table only says what each would do.
- The same FINDING predicts C4 coal r flat to −0.1 under either estimator. The mechanism is a C1 and volume
  mechanism, not a C4 one.

**So lever 1 collapses into lever 2's owner questions.** No new mechanism is proposed, and no LP was spent. Anything
else acting on CC energy would either be a second coal floor (rule 19) or tuning (rules 1 and 13).

## 4. Secondary items found

- **PGE Beaver (8073) has no benchmark plant row.** Its 1974 simple-cycle CTs are Acid-Rain-exempt, so there is
  no CEMS record. The per-plant table therefore omits it, but C1's class total (EIA-923) includes it. It is also absent
  from the CC heat-rate artifact.

  | TWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
  |---|---|---|---|---|---|---|---|
  | Model CC | 0.84 | 2.41 | 0.34 | 1.36 | 0.03 | 1.91 | 3.33 |
  | EIA-923 CC | 0.50 | 0.37 | 0.84 | 0.87 | 1.69 | 1.70 | 1.86 |

  Beaver contributes +2.0 TWh of 2020's +9.9. It is reported, not a lever: its heat rate falls back to the eGRID
  annual average because it has no CEMS series to measure a steady-state rate from.
- **The benchmark's per-plant CC sum and its class total disagree** by −2.2 to +4.6 TWh. For example, 2021 plants
  sum to 58.39 against a classFull of 53.83. C1 scores on classFull, so this does not move a gate. It does mean
  per-plant Δs (§2) do not add up to the C1 Δ. It is routed as a benchmark-consistency question.

## 5. Owner questions (restated, unchanged from NWPP-NEXT-5 §5)

- **Q1.** Generalise `coal_fuel_inventory_plant_grain` with a lower bound, or add a new row family? (Recommend
  generalise.)
- **Q2.** Annual or monthly period? (Recommend annual.)
- **Q3.** Floor or equality? (Recommend floor.)
- **Q4.** Estimator A or B, and the `_net` adjustment?
- **Q5.** Retire `coal_takeorpay_from_data` and `coal_committed_takeorpay_regulated` in the same arm (rule 19)?

With those answered, the next lane can build the arm and solve it as seven year-isolated shards on keeper #13's
recipe.
