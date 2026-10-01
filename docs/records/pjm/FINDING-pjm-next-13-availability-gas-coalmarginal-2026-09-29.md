# FINDING — PJM-NEXT-13: availability falsified; the keeper's gas sits above replacement cost in every year; model coal is marginal as often as real coal (zero LP)

**Keeper** `2026-09-28-pjm-next8-exitfix` (bundle `results/calibration/pjmnext8_xf_span`), unchanged. **Zero LP, zero shards, nothing registered.**

**Probes:**
- `scripts/probes/_pjmnext13_fleet_dump.py`: a `fleet_only` rebuild of the keeper recipe, one override. `pjm_da_virtual_bids` is off: those are demand-side rows, and the `_pjmnext8_exitfix_avail_delta.py` precedent applies. The fidelity guard still runs.
- `scripts/probes/_pjmnext13_cards.py` → `results/phase0/pjm/_pjmnext13_cards.json`.

**Intake:** the IMM's monthly Platts spot fuel prices, 2019–2025, were added to `som-competitive-conduct` (546 PJM rows, `spot_price_digitized_usd_per_mmbtu`).
- **Source.** The SOM prints them only as a chart. The chart is vector, so `scripts/data/digitize_pjm_som_spot_fuel.py` reads each point exactly from the PDF drawing paths.
- **Check 1.** The digitized series reproduces the report's own printed year-over-year changes (east +6.0 vs +5.9 %, NAPP −16.1 vs −16.1 %, east 2025 +77.0 vs +77.1 %).
- **Check 2.** Two report vintages agree to ≤ $0.008/MMBtu.
- **Why this source.** EIA's ICE natural-gas files stop at 2017, and EIA's weekly update tabulates only 4 hubs. This is the free production-area series.

## Card 1 — coal availability vs dispatch: FALSIFIED

Per bench COAL_BIT plant-month: CAMPD monthly max hourly output vs the model's max available MW (Σ tranche `pmax × availability`).

| year | C1 gap (TWh) | real max ÷ model available | same, months with a >$80 hour | model energy above the real month's max (TWh) |
|---|---|---|---|---|
| 2019 | +18.76 | 0.979 | 0.979 | 2.91 |
| 2020 | +12.16 | 0.972 | 0.890 | 1.13 |
| 2021 | +15.66 | 0.974 | 0.972 | 1.54 |
| 2022 | +7.61 | 0.967 | 0.967 | 1.42 |
| 2023 | −0.11 | 0.959 | 0.954 | 0.83 |
| 2024 | −0.07 | 0.947 | 0.945 | 1.65 |
| 2025 | +13.71 | 0.989 | 0.989 | 0.71 |

- Real coal reaches 95–99 % of the model's available MW at least once a month, in **every** year.
- The ratio is *lowest* in the fit years (2023/24), which is the wrong direction for a derate story.
- A measured monthly derate at the demonstrated max could remove at most 0.7–2.9 TWh of a 12–19 TWh gap.
- **Verdict:** real coal's flat mid-price loading is not an availability or derate effect. No design card.

## Card 2 — replacement-cost gas: a real, all-year wedge, NOT year-discriminating

The keeper's capacity-weighted CC_REGULAR fuel price is its EIA-923 / N3045 delivered cost. Compared against the IMM's Platts regions ($/MMBtu):

| year | keeper CC | IMM east | IMM west | IMM production | keeper − production |
|---|---|---|---|---|---|
| 2019 | 2.76 | 2.52 | 2.32 | 2.08 | +0.68 |
| 2020 | 2.09 | 1.74 | 1.74 | 1.36 | +0.73 |
| 2021 | 3.78 | 3.58 | 4.24 | 2.99 | +0.80 |
| 2022 | 6.61 | 7.28 | 5.88 | 5.51 | +1.10 |
| 2023 | 2.59 | 2.13 | 2.05 | 1.62 | +0.96 |
| 2024 | 2.44 | 2.25 | 1.98 | 1.67 | +0.77 |
| 2025 | 3.77 | 3.99 | 3.11 | 2.82 | +0.95 |

- **The floor gap largely dissolves at replacement cost.**
  - Measured against the keeper-style gas (HH + PJM delivered basis), 26–45 % of actual RT hours sit below 6.5 × gas (NEXT-12).
  - Measured against IMM production gas, only **1–8 %** do (east gas: 5–28 %).
  - So the real low-end price is an efficient CC burning production-area gas. The model's floor sits higher because its gas is priced at average delivered cost.
- **The wedge is not year-discriminating.** Its static effect on CC offers is largest in 2023 (−$6.1/MWh), where C3a passes. The "bare regional hub" arm, using the zone map in the decision card, gives:

| $/MWh, cap-weighted | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| CC_REGULAR offer Δ | −4.2 | −4.5 | −2.2 | −2.6 | −6.1 | −4.2 | −4.0 |
| CT_PEAKER offer Δ | −5.8 | −5.8 | −0.1 | −6.8 | −9.4 | −7.1 | −7.4 |

- **Rule 14, both ways:**
  - *For delivered.* It is the fuel cost the plant actually paid, measured per plant-month (EIA-923) or per state-month (N3045). It is the keeper's input.
  - *For replacement cost.* A delivered print is an **average**. It carries reservation/demand charges and contracted transport amortized over the month's takes. PJM cost-based offers are built from the fuel-cost policy's expected incremental fuel cost (Manual 15), and the IMM prices its LMP fuel components at Platts spot. The offer object is the marginal MMBtu. So the delivered print is **misaligned to the representation**, which is rule 14's own exception clause.
  - *Against the IMM series.* It is **misaligned** in a different way: 2–4-hub regional averages at monthly grain, which the model would map onto zones.
  - *Precedent.* MISO put the same question to its owner, who ruled **commodity + measured variable transport** (miso-225), not the bare hub and not the average print. Under rule 25 that verdict does not transfer; PJM needs its own ruling and its own measured transport.

## Card 3 — the model's coal-set share: model coal is marginal AT LEAST as often as real coal

A zone-hour counts as coal-marginal when a coal plant's hourly MW (run payload) sits strictly inside one of its econ / sync / peak tranches (rebuilt `pmax × availability`, ±1.5 % of nameplate for the payload's CF-byte quantization). It is **not** the LP marginal emission rate. This is an upper bound: ramp-limited units also sit inside a tranche.

| year | model coal-marginal, load-weighted zone-hours | IMM coal share of RT marginal units | IMM coal-fuel share of RT LMP |
|---|---|---|---|
| 2019 | 0.35 | 0.24 | 0.26 |
| 2020 | 0.33 | 0.18 | 0.24 |
| 2021 | 0.28 | 0.14 | 0.10 |
| 2022 | 0.22 | 0.10 | 0.07 |
| 2023 | 0.14 | 0.09 | 0.14 |
| 2024 | 0.19 | 0.10 | 0.12 |
| 2025 | 0.15 | 0.08 | 0.08 |

- Same year ordering as the IMM, and 1.4–2× its level: coal is **not** under-represented as a price-setter.
- What differs is the price at which it is marginal. The keeper's coal econ bands are floored at PJM's LONG_RUN offers (NEXT-12 §3), and the gas they compete with sits at delivered cost. Together they put every coal-marginal hour above efficient-CC cost at replacement gas.
- The ISO-wide `class_band_hourly` test (any coal band partially loaded) fires in 62–100 % of hours. It is uninformative because a band aggregates many plants, so it is not used.

## Observation for the next lane (not tested here)

- **The same average-vs-replacement question applies to coal.** IMM Platts NAPP spot vs the keeper's EIA-923 delivered coal (bench plants, NEXT-10 §2): 2020 1.68 vs 2.09; 2021 2.39 vs 2.06; 2022 **5.80 vs 2.63**; 2023 2.71 vs 3.08; 2024 2.28 vs 3.01.
- At replacement cost the coal/gas ratio moves the most in 2022 (0.40 → ~1.0). That is the coal-supply year NEXT-10 could not explain.
- Stated as a lead only: whether PJM coal offers reflect contract or spot cost is itself the question.

## Verdict

| object | status | next test |
|---|---|---|
| COAL_BIT over-run 2019/2021/2025, CT_PEAKER 2021 | **OPEN.** Availability falsified (this card), self-scheduling and EcoMax falsified (NEXT-11/12). Model coal is marginal as often as real coal. | Replacement-cost fuel for **both** gas and coal: the joint change moves the coal/gas ratio by year. |
| C3a 2019/2020 and the all-year floor | **OPEN, root cause located.** The floor is a fuel-cost-basis mismatch (delivered average vs replacement), present in every year. | Owner ruling on PJM's gas cost convention (decision card), then a zero-LP offer-array delta and 7 year-isolated shards. |
| C3a/C3b 2022 | pjm-h12 tail compression | the coal-spot lead above also lands on 2022 |

Nothing here is called a model-class limit.

## Addendum (2026-09-30): the ruled arm, built and refuted at zero LP

**Owner rulings.** Card 2 was ruled *"Hub + transport, joint with coal"* and the zone map *"Accept as proposed"*. Both were built as `pjm_replacement_cost_fuel` (default off, every keeper byte-identical):
- `src/market_sim/data/fuel/basis/pjm_replacement.py`;
- the frozen derive `scripts/data/derive_pjm_replacement_fuel.py`;
- new raw intakes `data/raw/eia-coal-mine-region/` (MSHA ID → EIA coal supply region) and `data/raw/eia-coal-transport-rates/` (EIA basin → state → mode transport, $/ton);
- tests and the matrix row.

**Before any solve**, the zero-LP offer delta was taken on paired `fleet_only` rebuilds (`scripts/probes/_pjmnext13_arm_delta.py` → `results/phase0/pjm/_pjmnext13_arm_delta.json`). It reads the P1 bid (`mc_base` + the mid-curve floor) and a static marginal-unit re-pricing of the keeper's own zonal prices, with no re-dispatch.

| year | CC_REGULAR Δfuel / Δbid | CT_PEAKER Δbid | ST_GAS Δbid | COAL_BIT Δbid | static Δ LW price, joint / gas leg only | C3a keeper → static arm |
|---|---|---|---|---|---|---|
| 2019 | −0.02 / −0.07 | +1.66 | +9.87 | +4.08 | +2.71 / +1.25 | +11.8 % → +22.0 % |
| 2020 | −0.06 / −0.42 | +1.73 | +10.11 | +3.81 | +2.10 / +1.02 | +15.9 % → +25.8 % |
| 2021 | +0.17 / +1.45 | +5.63 | +11.86 | +1.65 | +2.60 / +2.22 | +1.8 % → +8.5 % |
| 2022 | +0.13 / +1.12 | −0.18 | +10.32 | +3.04 | +1.85 / +2.01 | −11.5 % → −9.0 % |
| 2023 | −0.24 / −1.99 | −1.68 | +8.93 | +4.23 | +0.53 / −0.11 | +5.2 % → +7.0 % |
| 2024 | −0.05 / −0.37 | +0.60 | +9.52 | +2.93 | +1.37 / +0.89 | +0.5 % → +4.8 % |
| 2025 | −0.03 / −0.24 | +0.55 | +10.39 | +0.49 | +1.48 / +1.46 | −1.9 % → +1.4 % |

**Why the arm moves the wrong way:**
1. **Measured transport cancels the hub gap for the CC fleet.**
   - In the ruled regions (east / west for 6 of 8 zones), the keeper's delivered CC gas is only +0.2–0.5 $/MMBtu above hub.
   - The measured variable transport is +0.244 for the 11 CCs with own receipts. The class pool is +0.535, and it is what the ~240 CCs with no EIA-923 gas print receive.
   - Net CC fuel moves −0.24 to +0.17. Card 2's "+0.7–1.1 over production gas" was a comparison against the cheapest region; under the ruled map it applies only to West_APS / Central_PA.
2. **The coal leg removes a discount.** Rule 19 requires the gas-keyed BIT/PRB passthrough sigmoids off. The BIT sigmoid (floor 0.65) had been bidding coal at a fraction of delivered cost when gas is cheap. Spot + transport ≈ delivered on average, so coal bids rise $0.5–4.2/MWh.
3. **The coal leg contradicts PJM's own offers — a structural falsifier, not a fit statistic.** In the keeper, 41–63 % of COAL_BIT econ capacity-hours are floored UP to PJM's measured offer (the mid-curve surface). In those hours the arm's cost bid EXCEEDS the measured offer 32–61 % of the time (2019 0.61, 2021 0.32, 2023 0.48, 2025 0.32). Real PJM coal offered **below** spot replacement cost. That is consistent with contract / inventory fuel-cost policies, not with a spot opportunity cost.
4. **ST_GAS** takes +$9–12/MWh from a transport pool identified on 2 plants. It is thin identification, stated.

**Owner ruling (2026-09-30), on the decision card presenting the table above: *"Don't solve; record."*** No shard was launched. The field stays in the code default-off, as the record of the tested construction (the matrix cell is R). Deleting it is the next lane's call under rule 26 if no successor uses it.

**What this closes and what stays open:**
- The **floor gap is real** (card 2: real low-end prices are an efficient CC burning production-area gas).
- **"Replace delivered with hub + measured transport" is not the repair.** The measured transport carries most of the delivered premium.
- The next measured test: the low end is priced by **production-area CCs** (West_APS / Central_PA, and Marcellus-connected plants elsewhere) at production-gas cost. That needs:
  - (i) per-plant pipeline receipt points (EIA-176 / EIA-757 or FERC 549 connection data), to map CCs to production vs market-area supply rather than by zone;
  - (ii) the keeper's P1 hourly marginal units in low-price hours, which needs the dispatch parquet (not committed), so a replay of one year.

The field is left as a construction; the lane's status is **OPEN**, not a model-class limit.
