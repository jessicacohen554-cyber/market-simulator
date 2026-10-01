# FINDING — PJM-NEXT-12: self-scheduling does not discriminate the years; the price-floor object is real, in every year, and coal-marginal only in 2019/2020 (zero LP)

**Keeper** `2026-09-28-pjm-next8-exitfix` (bundle `results/calibration/pjmnext8_xf_span`), unchanged. **Zero LP, zero shards, nothing registered.**

**Intake (card 1 + 2).** PJM IMM (Monitoring Analytics) *State of the Market*, Section 3, 2019–2025, transcribed into the existing datatype `som-competitive-conduct` (`iso == PJM`, 105 rows). Source URLs, sha256 and each vintage's printed definition are in `data/raw/som-competitive-conduct/README.md`. PDFs are not committed (© Monitoring Analytics; numbers + page citations only, as for SPP).

**Probe:** `scripts/probes/_pjmnext12_selfsched_marginal.py` → `results/phase0/pjm/_pjmnext12_selfsched_marginal.json`.

## 1. The table

| year | C1 COAL_BIT gap (TWh) | of which response | IMM coal **must-run** share of DA offered MW | IMM coal share of **RT marginal units** | IMM **coal-fuel share of RT LMP** | hours priced below 6.5 × gas: model / actual |
|---|---|---|---|---|---|---|
| 2019 | +18.76 | +17.87 | 0.245 † | **0.244** | **0.264** | 0.02 / **0.36** |
| 2020 | +12.16 | +6.57 | 0.192 | **0.175** | **0.237** | 0.03 / **0.45** |
| 2021 | +15.66 | +11.78 | **0.187** | 0.142 | 0.103 | 0.03 / 0.40 |
| 2022 | +7.61 | +10.17 | 0.255 ‡ | 0.100 | 0.071 | 0.00 / 0.27 |
| 2023 | −0.11 | +1.67 | 0.276 ‡ | 0.091 | 0.144 | 0.01 / 0.30 |
| 2024 | −0.07 | +2.80 | **0.296** ‡ | 0.103 | 0.121 | 0.01 / 0.26 |
| 2025 | +13.71 | +15.13 | n/a § | 0.079 | 0.077 | 0.00 / 0.27 |

- Gap and response: PJM-NEXT-11 audit (a).
- "Gas" = HH daily + PJM delivered basis (the series `_pjmnext11_bulk_price.py` uses). 6.5 MMBtu/MWh ≈ an efficient CC's full-load heat rate. It is a reporting line only; 6.0 and 7.0 are in the JSON and do not change the reading.
- † 2019 layout: fixed-output 0.020 + self-scheduled eco-min 0.225.
- ‡ 2022–24 wording: "submitted MW of must-run units" (2020–21: "eco-min MW"). There may be a level break at 2022.
- § The 2025 table was redesigned and has no must-run column.

## 2. Card 1: self-scheduling is falsified as the COAL_BIT lever

- **Wrong direction.** The hypothesis needs more real self-scheduling in the over-run years. The data show the opposite:
  - 2021 has the lowest measured must-run share (18.7 %) and the second-largest over-run.
  - 2023/24 have the highest shares (27.6 / 29.6 %) and fit.
- **Same-definition pairs cannot explain it either.**
  - 2020 vs 2021 (19.2 vs 18.7 %) have nearly the same share, but the response over-run is +6.6 vs +11.8 TWh.
  - Within 2022–24, a higher share goes with a *smaller* over-run.
- **Wrong mechanism.** A must-run block is a floor. It cannot cap loading, and the over-run sits in the $35–80 bins (NEXT-11 §4). Real coal loads lower there than the model at the same price.
- **Already represented.** `coal_mustrun_per_plant` (K) already floors COAL_BIT from measured data. A second self-schedule floor would stack on it (rule 19).
- **Rule-13 admissibility, stated then moot.**
  - *For:* PJM's IMM publishes the must-run share every year, so a trailing-years value regenerates for a forward year.
  - *Against:* a same-year share is a participant *choice* observed after the fact, i.e. an outcome. Only a trailing construction passes the forward test.
  - The question is moot, because the share does not discriminate the years in the needed direction.
- **No design card, no solve.**

## 3. Card 2: the price-floor object is real; coal explains 2019/2020 only

- **Floor gap in every year, training span included.**
  - Actual PJM RT prices sit below an efficient CC's fuel cost (at this gas series) in 26–45 % of hours.
  - The keeper's P1 price does so in 0–3 %.
  - The model essentially never clears below gas-CC cost. This extends NEXT-11 §5 from quantiles to hour shares.
- **Coal as price-setter is year-discriminating, but only for 2019/2020.**
  - Coal set 24–26 % of the RT LMP (fuel component) and was 18–24 % of RT marginal units in 2019/2020, against 7–14 % / 8–14 % in 2021–25.
  - 2019/2020 are exactly the C3a over-price years (+11.8 / +15.9 %).
  - So the §5 reading ("real coal is the low-end price-setter") holds for C3a 2019/2020.
  - It does **not** hold for the COAL_BIT over-run in 2021/2025, where coal's marginal role is as small as in the fit years.
- **Coal cannot account for the whole below-gas-cost share.**
  - Coal + wind + nuclear together were 15–30 % of RT marginal units; gas was 60–83 %.
  - Their combined share accounts for much of the 26–45 % of below-cost hours, but not all of it.
  - The remainder has to be **gas units clearing below HH + 0.67 × 6.5**.
  - The IMM prices its decomposition at Platts spot, including *production-area* gas (Dominion South, Tennessee Z4, Leidy). The keeper prices gas at EIA-923 **delivered** cost (plant prints + a mean-zero zonal basis).
  - A replacement-cost vs delivered-cost gap on western/production-area gas would lift the model's floor in exactly this way. **Not measured here:** the IMM prints hub levels only as a chart, and no production-area daily series is in the repo.
- **Why model coal never sets a sub-gas price.** The keeper floors coal econ bands at PJM's own LONG_RUN mid-curve offers:
  - 2019: $18.4–19.9 at gas 2.57 (≈ 7.2–7.7 × gas).
  - 2020: $15.8–17.3 at gas 2.03 (≈ 7.8–8.5 × gas).
  - A coal-marginal model hour therefore prices *above* 6.5 × gas. How real coal set sub-gas-cost prices in 2019/2020 while offering at those levels is itself **OPEN**. Candidates:
    - self-scheduled coal eco-min acting as price-taking MW, which pushes the marginal unit down to cheaper resources;
    - intervals where coal ran on lower curve segments;
    - IMM sensitivity-factor weighting.
- **The model's marginal emission rate is not used** (it blends units; coal band 19–37 % of hours, inconsistent with 0–3 % sub-gas-cost hours).

## 4. Verdict

| object | status | next test |
|---|---|---|
| COAL_BIT over-run 2019/2021/2025, CT_PEAKER 2021 | **OPEN.** Self-scheduling falsified (wrong direction, floor not cap); offered EcoMax falsified (NEXT-11). The over-run is price *response*, and coal's marginal role is small in 2021/2025. | Is real coal's mid-price partial loading an **availability** effect rather than a dispatch effect? Per plant-month, compare the model's available MW (`fleet_only` rebuild: pmax × availability) against CAMPD's monthly max output, by year. If real monthly max falls well below the model's available MW in 2019/2021/2025 but not in 2023/24, the lever is a measured derate / partial-outage input (rule 13-admissible), not an offer. |
| C3a 2019/2020 (and the all-year floor) | **OPEN, narrowed.** Real coal was the price-setter in 2019/2020 (IMM, measured). There is also an all-year gap in sub-gas-cost pricing that coal does not cover. | (a) Intake a production-area gas series (check EIA's ICE wholesale gas files for Eastern Gas South / Dominion South / TETCO M2 / Leidy; else FERC Form 552 / state reports). Measure replacement-cost vs the keeper's delivered-cost gas by zone and year. (b) Reconstruct the model's coal-set share of LMP from `class_band_hourly` + a `fleet_only` band-capacity rebuild (partially loaded coal band = coal marginal) and compare it to the IMM's 26/24/10/7/14/12/8 %. |
| C3a/C3b 2022 | pjm-h12 tail compression (unchanged) | — |

Nothing here is called a model-class limit: two hypotheses are falsified and two measured next tests are named.
