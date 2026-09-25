# FINDING — SPP-81: what carries SPP's residual upper-tercile cost object (data intake, zero LP, 2026-09-25)

Parent: `docs/handoffs/FINDING-spp-80-upper-tercile-premium-2026-09-25.md`.
Probe: `scripts/probes/_spp81_residual_upper_tercile.py` (SPP-80's exact hour set: RT p67–p99,
Feb excluded, interval-level scarcity flag). Pin: `5c6e7ab8` (contains SPP-80 `2e1215b5`).
**No LP, no shard, no bundle, no `src/` edit, no `ScenarioConfig` field, no multiplier touched.**

## 0. Headline

**None of the three candidates carries it.** The object is +3.19 / +3.43 HR in 2023 / 2024 on
delivered gas. Measured:

- **Marginal-unit heat-rate mix: about 0.2–0.46 HR (at most about 14 %).** CT and gas-ST did take
  margin share from CC. By the MMU's count, simple-cycle's share of gas-marginal intervals rose
  from 49 % to 63 / 62 %. But unit heat rates are flat, and the stack's p90 heat rate rose only
  +0.22 / +0.44.
- **Gas timing (monthly, daily, SPP's own hubs): it widens the residual.** Monthly delivered gas
  gives +3.70 / +4.04 HR. Shaping by HH daily/monthly gives +3.80 / +4.50. On Panhandle Eastern,
  SPP's own hub, it is +4.32 / +8.99, because the hubs cleared *below* delivered cost
  (delivered ÷ Panhandle 1.37 / 1.68 vs 1.24–1.34 in 2019–20).
- **Ramp/uncertainty dispatch: nothing measurable.** Within net-load bands, cleared ramp-up MW has
  a *negative* coefficient on MEC/gas (−0.05 to −0.18 HR per 100 MW, |r| ≤ 0.07). The ramp product
  was live all of Mar–Dec 2022 with a residual of −0.09. The monthly residual steps up in
  **April 2023**, before the uncertainty product (2023-07-06). Uncertainty MW peaked in 2025
  (781 MW in the upper tercile), when the residual was smallest.

**What is left, restated sharper.** In 2023 / 2024 the hub's MEC ex-scarcity sits **$7.1 / $7.4
per MWh above the fuel cost of the p90 dispatchable gas unit actually running** (CAMPD heat rate ×
delivered gas). In 2019 / 2020 that gap was +$1.2 / −$0.3. It is largest in **Mar–May 2024
(+10 HR)** and Apr–Sep 2023 (+3.6 to +6.4). The MMU's own implied heat rate shows the same shape:
7,500 (2021–22) → 11,000 (2023) → 14,400 (2024) → 11,000 Btu/kWh (2025). The MMU names no cause.

**Rule 13 / SPP-79 coupling.** None of the three is a forward-reproducible input that closes the
object. The heat-rate mix is a dispatch **outcome**, and the model's own stack already sets it.
Gas timing moves the wrong way. The ramp/uncertainty products carry no measurable price effect.
**No measured driver can pair with a body-price lever.** SPP-79's constraint stands: a body lever
alone breaks the 2023–25 C3a pass.

## 1. Per-year table (Δ = against the 2019–21 mean, HR = $/MWh ÷ $/MMBtu)

| year | **SPP-80 residual** (MEC ex-scar ÷ annual delivered gas, ΔHR) | L1 CAMPD p90-flex ΔHR | L1 MMU-mix ΔHR | L2 monthly gas ΔHR | L2 + HH daily shape ΔHR | L2 on Panhandle ΔHR¹ | L3 ramp-up cleared MW (upper tercile) | L3 within-band implied ΔHR | MEC − p90 fuel cost, $/MWh |
|---|---|---|---|---|---|---|---|---|---|
| 2019 | +1.06 | −0.04 | +0.04 | +0.80 | +0.78 | −0.06 | — | — | +1.23 |
| 2020 | +0.31 | −0.15 | −0.04 | +0.49 | +0.47 | +0.06 | — | — | −0.29 |
| 2021 | −1.37 | +0.19 | −0.00 | −1.29 | −1.24 | (Uri) | — | — | −10.01 |
| 2022 | +0.13 | +0.36 | +0.20 | +0.09 | +0.06 | −0.54 | 504 | −0.75 | −6.21 |
| **2023** | **+3.19** | +0.22 | +0.46 | +3.70 | +3.80 | +4.32 | 565 | −0.31 | **+7.06** |
| **2024** | **+3.43** | +0.44 | +0.42 | +4.04 | +4.50 | +8.99 | 571 | −1.03 | **+7.40** |
| 2025 | +1.87 | +0.13 | +0.11 | +2.24 | +2.22 | +0.92 | 577 | −0.66 | +4.27 |

- The SPP-80 column is reproduced exactly: HR 11.678 / 10.934 / 9.257 / 10.750 / 13.811 / 14.051 / 12.494.
- ¹ Panhandle Eastern base is 2019–20 only, because Uri put Panhandle's Feb-2021 month near $22. The
  hub averages are annual and include February.
- Carried = the largest candidate that moves the right way: L1, about +0.46 / +0.44 HR in
  2023 / 2024. **Left after L1: +2.7 / +3.0 HR, about $8–9/MWh.**

## 2. Leg 1: marginal-unit heat-rate mix

**MMU RT "Generation on the margin" (share of intervals), digitized, latest vintage.**

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| gas simple-cycle | 25.5 % | 23.0 % | 20.6 % | 24.4 % | **32.0 %** | **27.2 %** | 23.1 % |
| gas combined-cycle | 25.2 % | 25.3 % | 21.5 % | 19.5 % | 18.9 % | 16.5 % | 20.4 % |
| SC ÷ (SC + CC) | 0.50 | 0.48 | 0.49 | 0.56 | **0.63** | **0.62** | 0.53 |
| wind / coal | 17 / 30 | 22 / 28 | 34 / 23 | 37 / 17 | 30 / 17 | 37 / 17 | 33 / 18 |

- The SC share of gas-marginal intervals tracks the residual's timing: low in 2022, high in
  2023–24, easing in 2025.
- **Its size is small.** Δ(SC share) × (CT − CC heat rate, CAMPD) = +0.46 / +0.42 HR.

**CAMPD SWPP-BA gas, upper-tercile hours** (244–253 units, EIA-860 BA = SWPP).

| | 2019–21 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| unit heat rate, CC / CT / ST_GAS (MMBtu/MWh) | 7.86–7.92 / 10.53–10.59 / 10.51–10.84 | 7.90 / 10.95 / 10.66 | 7.75 / 11.08 / 10.54 | 7.74 / 10.92 / 10.45 | 7.82 / 10.56 / 10.39 |
| gas MW share, CC / CT / ST_GAS | 0.61 / 0.21 / 0.19 | 0.57 / 0.21 / 0.21 | 0.55 / 0.22 / 0.23 | 0.53 / 0.23 / 0.25 | 0.53 / 0.22 / 0.26 |
| dispatchable-range heat rate, mean / p90 | 8.85 / 11.21 | 9.06 / 11.57 | 9.05 / 11.43 | 9.12 / 11.65 | 8.99 / 11.34 |

- "Dispatchable range" means strictly between each unit's own p10-running and p99 output, ±5 %.
  That is the MMU's marginal-unit criterion (not at economic minimum or maximum), proxied.
- **Mix shifted, efficiency did not.** Per-class heat rates are flat or better, and the stack's p90
  moved +0.2 to +0.4.
- The market heat rate on delivered gas is 13.8 / 14.1. That is **about 2.4 HR above the p90 unit
  actually running**, whereas in 2019–20 it sat on it.

## 3. Leg 2: intra-year and intra-month gas cost

- **Monthly delivered gas** (EIA-923, KS/OK/NE, each hour's own month) raises the residual to
  +3.70 / +4.04. Upper-tercile hours did not fall in expensive gas months relative to the base years.
- **Daily.** No free daily Panhandle / OGT / Southern Star series exists:
  - EIA's ICE wholesale file covers seven hubs (Henry, Chicago, Algonquin, TETCO-M3, Malin,
    PG&E, SoCal-Ehrenberg), and its natural-gas archive past 2017 returns HTTP 301
    (`https://www.eia.gov/electricity/wholesale/xls/archive/ice_natgas-{2019,2023,2024}final.xlsx`).
  - The EIA NGWU compact spot table carries no Mid-Continent row.
  - The HH daily ÷ monthly ratio on upper-tercile days was 1.005 / 1.012 (2023 / 2024), against
    1.007–1.018 in the base years. Shaping the monthly price by it gives +3.80 / +4.50.
  - This is a national proxy, stated as such.
- **SPP's own hubs** (MMU SOM annual averages, now transcribed): Panhandle Eastern was
  1.93 / 1.72 / 4.96 / 5.79 / **2.17 / 1.84** / 2.98, and Southern Star tracked it. Hub spot ran
  **below** plant-delivered cost, most of all in 2024 (delivered ÷ hub 1.68). A generator buying
  spot faced *cheaper* gas than the model's delivered price, so the object grows on a hub basis.
- **Verdict: gas timing carries none of it.**

## 4. Leg 3: ramp and uncertainty dispatch

- Cleared MW (new `spp_rtbm_or_cleared_hourly.parquet`, upper-tercile means):
  - ramp-up: 504 / 565 / 571 / 577 (2022–25);
  - uncertainty-up: — / 91 / 202 / 781;
  - reg-up, spin and supp are flat (406–431 / 705–756 / 718–769 across 2019–25).
- **Within 2-GW net-load bins**, the OLS slope of MEC ÷ monthly delivered gas on cleared ramp-up MW
  is −0.15 / −0.05 / −0.18 / −0.11 HR per 100 MW (2022–25), with |r| ≤ 0.07. Holding more ramp
  does not coincide with higher energy prices.
- **Timing.** Residual by window, against the same calendar months of 2019–21:

| window | ΔHR |
|---|---|
| 2022 Mar–Dec (ramp product live) | −0.09 |
| 2023 Jan–Jul 5 (before uncertainty product) | +2.01 |
| 2023 Jul 6–Dec (uncertainty product live) | +4.27 |
| 2024 Jan–Sep | +4.45 |
| 2024 Oct–Dec (uncertainty enhancement) | +2.63 |
| 2025 | +2.24 |

Monthly residual (ΔHR vs 2019–21 same month):

| | Jan | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2022 | 0.85 | 3.77 | −0.47 | −1.97 | −2.65 | −1.07 | −1.43 | 0.05 | −0.48 | 2.76 | 3.65 |
| 2023 | −2.55 | −0.52 | **3.91** | **5.00** | 4.67 | 3.64 | **6.44** | 5.53 | 2.17 | 2.72 | 3.27 |
| 2024 | −1.73 | **10.22** | **10.07** | **10.22** | 2.53 | 3.63 | 3.69 | 5.58 | 4.07 | 4.99 | −0.74 |
| 2025 | 0.27 | 4.92 | 6.85 | 1.03 | 0.58 | 1.70 | 1.70 | 2.89 | 1.75 | 1.41 | 0.90 |

- The step starts in **April 2023**, three months before the uncertainty product.
- The ramp product's first ten months show nothing.
- The H2-2023 jump is partly the summer/Aug peak.
- **Verdict: neither product carries it.**

## 5. What the object now is, and what could still identify it

- It is a **spring-and-summer 2023–24 cost level**, about $7/MWh above the fuel cost of the
  running marginal gas fleet.
- It is not scarcity, congestion, markup, net load, fuel basis, fuel timing, heat-rate mix or
  reserve procurement.
- Candidates this lane could not measure, in order of how directly a public source could settle
  them:
  1. **Mitigated-offer content.** SPP markups are measured against the mitigated offer, so any
     cost inside it moves the price at a flat markup. Examples: fuel-cost-policy intraday or
     next-day gas premiums, gas-day nomination and imbalance charges, and 2023+ changes to
     SPP's Mitigated Energy Offer / Fuel Cost Policy rules. Source: SPP Market Protocols
     revision history and MMU mitigation reports, both text.
  2. **Wind curtailment/offer behavior setting a higher-cost gas unit in spring.** The Mar–May
     2024 +10 HR sits in SPP's windiest months. Source: MMU marginal-by-month bars (charted,
     digitizable).
  3. **Spot premium for real-time incremental gas above the monthly delivered average at SPP
     pipelines.** This needs a paid daily Mid-Con index (NGI/Platts), so it is not free.
- **Rule 13 test.** (1) would be a forward-reproducible input if it proves to be a rule or tariff
  change. (2) is an outcome. (3) is a measured price, admissible if bought.
- **None is a lever today, and nothing here is proposed as a PRECOMMIT.**

## 6. What landed (paths, sizes)

| corpus | content | size |
|---|---|---|
| `data/raw/_validation-source/spp_rtbm_or_cleared_hourly.parquet` (NEW) | RTBM cleared MW (reg, spin, supp, ramp, uncertainty), SPP system row, hourly, 2019–2025, 61,226 h; 2025 sampled 1 interval/h | 1,234,908 B, sha256 `6a5f03d5…a85f40` |
| `scripts/data/fetch_spp_or_cleared.py` (NEW) | producer: range-reads portal `operating-reserves` year zips (one GET per day) | — |
| `data/raw/som-competitive-conduct/som_competitive_conduct.csv` | +62 SPP rows: 35 RT marginal-technology shares (digitized), 6 MMU implied heat rates, 21 hub gas averages, all page-cited | 24,433 → 38,632 B |
| schema + `data-dictionary.md` | units `btu_per_kwh`, `usd_per_mmbtu`; new metric/segment codes | — |

## 7. Sources that failed or fell short

- **Daily Mid-Con gas.** No free series exists. EIA ICE natural-gas archive after 2017 returns
  HTTP 301 (`…/ice_natgas-2019final.xlsx`, `…2023…`, `…2024…`); its current hubs exclude
  Mid-Continent. The EIA NGWU compact table has no Mid-Con row.
- **Operating-reserves 2025** has no year zip (HTTP 404 on `/2025/2025.zip`). It is served per day
  and was sampled at one interval per hour.
- **SOM marginal-technology bars carry no data labels.** 2019–23 vintages were digitized from vector
  geometry and 2024–25 from raster pixels. They reproduce every printed share within 0.4 pt. The
  2023 SOM restated 2022 (simple-cycle 21.5 → 24.1 %).
- **2025 SOM prose contradicts its own chart.** The text says gas SC/CC "decreased" 5/6 pts from DA
  to RT; the chart shows increases. The chart is recorded.
- **Implied heat rate restated.** The 2024 SOM restates 2023's implied heat rate (nearly 11,000 →
  over 12,600). Both are recorded.
- Nothing was egress-blocked. `portal.spp.org` and `www.spp.org` answered every call, and the SOM
  PDFs' sha256 match SPP-80's table.

## 8. Rules and state

- Zero LP; rule 32 was not engaged. No cell verdict changed. Evidence was appended to
  `measured_ct_heat_rates` (K), `measured_ramp_capability` (U), `gas_daily_shape` (U) and
  `offer_curve_by_group` (K) in `docs/codebase-site/data/mechanism-matrix/SPP.js`. The §5.7 note
  sits above SPP-80's.
- Rule 1: no multiplier was re-tuned. The object is year-specific, so the carve-out's single
  year-invariant value cannot be the channel.
- Retrievability (rule 34(e)): no bundle was produced, so there is nothing to promote.
