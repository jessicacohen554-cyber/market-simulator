# FINDING — miso-296: at low load the model's marginal unit is gas CC and the seam; the real market's is coal. The gap is the offer level at the margin, not quantity. No solve.

```
LANE    : miso-296 (owner ruling 2026-10-01, miso-295 card: "C3a 2020 low-load stack (Recommended)")
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), unchanged
LP      : none. Keeper P1 hourly sidecars, zone-resolved hub RT, measured zonal demand, EIA-930, CAMPD,
          Chicago Citygate daily, fleet-only rebuilds of the keeper recipe (base and bid stacks)
PROBE   : scripts/probes/_miso296_lowload_stack.py  (~6 min/year; blocks A-E)
OUTPUT  : results/calibration/_miso296_lowload_stack.json
SOURCES : Potomac Economics, MISO State of the Market Reports: 2020 (Table 1 p.6; Appendix Fig. A6 p.7-8),
          2022 (Table 1 p.6), 2023 (Table 1 p.6), 2024 (Table 1 p.6; Table 7 p.45). Fetched from
          potomaceconomics.com; cited, not committed, not a model input (rule 13). Page numbers are printed pages.
CELLS   : no verdict moves; no R/I/G cell re-tested (rule 28). Evidence notes added to
          gas_marginal_commodity_pricing (O), gas_variable_transport (O), seam_neighbour_hourly_ladder (K)
```

## 1. Answer

1. **C3a 2020 (+11.6 %, +$2.54/MWh) is a level shift over the bottom four load quintiles, not a night object
   and not a tail object.** Quintiles 1–4 each contribute +$0.67 to +$0.73 of the +$2.54; quintile 5 gives back
   −$0.26. Night hours (h0–5) carry +$1.09 and day hours +$1.45. Hours with an actual price below $10 contribute
   +$0.25; hours between $10 and $20 (5,032 of them) contribute +$3.21. The same low-load overshoot is present in
   **every** year (quintile 1: +$1.6 to +$7.2; quintile 2: +$0.6 to +$5.1). 2020 reads worst because quintiles
   1–4 are all +$3.4 to +$4.5 and the top-quintile tail deficit that offsets it in 2021/2022/2025 (−$9 / −$19 /
   −$12) is only −$1.0.
2. **Who is marginal.** In the lowest load quintile the model's marginal row is gas in 65 %, the seam
   (PJM/SPP/South import ladders) in 28 % and coal in 7 % of hours (bid stack, 2020). The IMM reports that coal set
   MISO's system marginal price in **40 % of 2020 intervals, "generally in off-peak hours"**, gas in 57 %
   (2020 SOM Table 1). Over all hours the model has coal marginal 25 % and the seam 21 %; the seam is not a
   price-setting category in the IMM table at all. Across years the model's all-hours coal share is 0.42 / 0.25 /
   0.37 / 0.19 / 0.21 / 0.20 / 0.28 (2019–2025) against the IMM's 0.47 / 0.40 / 0.35 / 0.24 / 0.36 / 0.36 — about
   half the IMM's in the low-gas years 2020 / 2023 / 2024, close in 2019 / 2021 / 2022 — and in the model coal's
   share **rises** with load (2020 bid stack: quintile 1 7 %, quintile 5 46 %), the reverse of "generally
   off-peak".
3. **What the marginal offer is made of (2020, quintiles 1–2).** When a CC_REGULAR econ tranche is marginal
   (997 of 3,504 hours) its offer is $18.14 = 7.41 MMBtu/MWh × $2.165 + $2.00 VOM, with zero startup markup.
   The same day's Chicago Citygate flow-day price is $1.72, so the fuel print carries a **+$0.34/MMBtu = +$2.57/MWh
   wedge** over the traded hub, against a bid-minus-actual gap of +$3.66 in those hours. The wedge is 70 % of the
   gap at the CC margin. In every year the wedge at the CC margin is the largest single component: $2.9 / 2.6 /
   2.0 / 0.9 / 5.4 / 6.0 / 4.8 per MWh (2019–2025) against gaps of $3.5 / 3.7 / 3.5 / 0.3 / 5.8 / 4.8 / 5.8 — the
   print premium over the hub grew from $0.27–0.39/MMBtu (2019–2021) to $0.64–0.84 (2023–2025). This is the miso-224/225 object (`gas_marginal_commodity_pricing`,
   `gas_variable_transport`, both O; the owner-ruled form is hub + variable transport, of which the measured
   variable leg for CC_REGULAR is $0.21/MMBtu).
4. **Coal is not at the margin because the model's coal offer curve has a hole where the real one is flat.**
   In the low-load hours of 2020 the model's coal runs 18.8 GW: mustrun 9.3 GW at $4.5 (VOM only), committed
   8.7 GW at a cap-weighted $9 (the regulated take-or-pay discount; p50 $8.6), then econ 6.4 GW PRB / 3.2 GW BIT
   at a cap-weighted **$29.6** (HR 13.0 × $1.91 + $4.50; p10 $17.2). Between the committed band's median and the
   econ band's p10 there is no coal offer. CAMPD coal in the same hours is 17.8 GW. The real fleet, with 1 GW less
   on, set the price at ~$15. The model's cheapest undispatched coal econ MW sits $0.13 above the clearing price
   (every year: $0.02–0.16) — coal econ is co-marginal at its own level, which is ~$10 above the real
   coal-marginal price. In 2019 / 2020 / 2023 / 2024 the keeper dispatches only 7–16 % of its coal econ capacity
   in these hours; in 2021 / 2022 / 2025 (gas $3.4–5.9) it dispatches 39 / 83 / 35 % and coal is marginal at low
   load 38 / 35 / 22 % of the time — so the model only reproduces the IMM's off-peak coal margin when gas is dear
   enough to lift CC above the ~$30 coal econ level.
5. **Quantity is not the object.** Model minus CAMPD in the low-load hours: CC_REGULAR +0.2 GW, COAL_PRB +1.0,
   COAL_BIT −0.1, ST_GAS −1.1, CT_CHP −0.7 (host-steam basis), CT_PEAKER −0.3. The model never curtails wind and
   never dumps (0 hours); the actual price is below $10 in 2.8 % of hours and the model's in 0.0 %, but those
   hours carry only +$0.25 of the +$2.54. Imports: model 5.5 GW vs EIA-930 6.7 GW net import.
6. **West/Plains congestion is a distinct, adjudicated part.** The zone error is West +$5.87, Plains +$4.04,
   South +$3.12, Illinois +$2.15, Indiana +$1.20, East +$0.04. If West and Plains carried the rest-of-footprint
   error, C3a 2020 would read **+7.2 %** (PASS); 2019 +8.7 → +5.6 %, 2024 +5.1 → +4.5 %, 2023 unchanged at
   +8.4 %. That part is the wind-congestion separation of the West hub (`internal_congestion_split`, G, killed
   2026-10-01) and is not re-opened here. It is worth about 4.4 of the 11.6 points in 2020; the other 7.2 points
   are the margin-level object of items 3–4, present in every zone.

(Section 1 is 2020; §§2–6 carry every year. Where a number is quoted without a year it is 2020.)

## 2. Where the C3a 2020 error lives (block A)

**Annual load-weighted price (model / actual), zone-resolved basis, hours with a published actual (2022: 7,560 h; the scorer masks Nov–Dec as partially staged months and reads −5.1 %):**

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| model | 27.91 | 24.51 | 37.03 | 59.47 | 32.74 | 30.78 | 41.67 |
| actual | 25.67 | 21.97 | 39.23 | 63.28 | 30.19 | 29.28 | 42.12 |
| err | +2.24 | +2.54 | -2.20 | -3.81 | +2.54 | +1.50 | -0.46 |
| pct | +8.7 % | +11.6 % | -5.6 % | -6.0 % | +8.4 % | +5.1 % | -1.1 % |

**Error by load quintile and hour block, $/MWh (contribution to the annual error in brackets; the five quintile contributions sum to the annual error):**

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| q1 | +3.96 (+0.65) | +4.50 (+0.73) | +1.58 (+0.26) | +7.23 (+1.23) | +6.16 (+1.02) | +4.54 (+0.75) | +6.58 (+1.07) |
| q2 | +3.68 (+0.67) | +3.72 (+0.67) | +0.63 (+0.11) | +1.65 (+0.30) | +5.13 (+0.94) | +3.70 (+0.68) | +2.75 (+0.50) |
| q3 | +4.01 (+0.79) | +3.51 (+0.69) | -1.24 (-0.24) | -1.20 (-0.23) | +3.36 (+0.65) | +2.40 (+0.47) | +3.09 (+0.60) |
| q4 | +2.69 (+0.57) | +3.36 (+0.71) | -0.31 (-0.06) | +0.40 (+0.08) | +3.62 (+0.75) | +1.11 (+0.23) | +1.87 (+0.40) |
| q5 | -1.77 (-0.43) | -1.04 (-0.26) | -9.07 (-2.26) | -19.45 (-5.19) | -3.32 (-0.83) | -2.53 (-0.63) | -12.05 (-3.02) |
| night_h0_5 | +3.97 (+0.87) | +4.96 (+1.09) | +2.29 (+0.50) | +7.46 (+1.65) | +5.54 (+1.23) | +4.38 (+0.97) | +5.48 (+1.22) |
| day_h6_23 | +1.76 (+1.37) | +1.86 (+1.45) | -3.46 (-2.70) | -7.00 (-5.46) | +1.69 (+1.32) | +0.67 (+0.52) | -2.15 (-1.67) |

**Where the actual price was: contribution of each actual-price band to the annual error (hours):**

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| actual lt_0 | +0.00 (0) | +0.03 (14) | +0.00 (0) | +0.01 (1) | +0.01 (4) | +0.02 (7) | +0.00 (0) |
| actual lt_10 | +0.01 (10) | +0.25 (249) | +0.00 (0) | +0.06 (18) | +0.13 (91) | +0.13 (125) | +0.03 (18) |
| actual lt_20 | +1.43 (2180) | +3.46 (5281) | +0.71 (828) | +0.23 (93) | +1.52 (1769) | +1.95 (2848) | +0.59 (542) |
| actual ge_20 | +0.82 (6579) | -0.92 (3479) | -2.91 (7931) | -4.04 (7467) | +1.03 (6991) | -0.46 (5912) | -1.04 (8217) |

**Share of hours below $10 / $20, actual vs model (%):**

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| < $10 actual / model | 0.1 / 0.0 | 2.8 / 0.0 | 0.0 / 0.0 | 0.2 / 0.0 | 1.0 / 0.0 | 1.4 / 0.0 | 0.2 / 0.0 |
| < $20 actual / model | 24.9 / 0.7 | 60.3 / 21.6 | 9.4 / 0.0 | 1.2 / 0.0 | 20.2 / 1.6 | 32.5 / 7.7 | 6.2 / 0.0 |

**Zone error (model − actual, zone-demand-weighted, $/MWh) and the counterfactual in which West and Plains carry the demand-weighted error of the other four zones:**

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| MISO-West | +5.02 | +5.87 | -2.25 | +10.52 | +2.33 | +1.57 | -1.64 |
| MISO-Plains | +3.54 | +4.04 | -2.63 | +1.32 | +2.86 | +2.32 | -0.27 |
| MISO-Illinois | +2.05 | +2.15 | -3.02 | -8.48 | +3.36 | +2.75 | +0.91 |
| MISO-Indiana | +0.33 | +1.20 | -4.62 | -16.07 | -0.25 | -1.61 | -4.35 |
| MISO-East | +0.20 | +0.04 | -2.77 | -11.40 | +1.69 | -0.63 | -4.32 |
| MISO-South | +3.05 | +3.12 | +0.13 | +0.30 | +4.41 | +4.17 | +5.15 |
| err if West+Plains at rest-of-footprint err | +1.45 | +1.59 | -2.10 | -7.64 | +2.53 | +1.32 | -0.25 |
|   -> C3a pct | +5.6 % | +7.2 % | -5.4 % | -12.1 % | +8.4 % | +4.5 % | -0.6 % |
|   West+Plains demand share | 0.278 | 0.280 | 0.281 | 0.282 | 0.286 | 0.283 | 0.286 |

## 3. Who sets the price: IMM vs model (block B)

**Share of hours the marginal row belongs to each family. IMM = Potomac SOM Table 1, SMP column (share of real-time intervals; 2025 not yet published). Model = marginal row of the merit clear at the keeper's thermal quantity (P0 base stack; P1 bid stack = base + startup markup):**

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| IMM SMP coal | 0.47 | 0.40 | 0.35 | 0.24 | 0.36 | 0.36 | n/a |
| P0 stack all-hours coal | 0.38 | 0.20 | 0.38 | 0.19 | 0.18 | 0.17 | 0.27 |
| bid stack all-hours coal | 0.42 | 0.25 | 0.37 | 0.19 | 0.21 | 0.20 | 0.28 |
| IMM SMP gas | 0.51 | 0.57 | 0.64 | 0.75 | 0.63 | 0.63 | n/a |
| P0 stack all-hours gas | 0.41 | 0.58 | 0.53 | 0.65 | 0.58 | 0.63 | 0.56 |
| bid stack all-hours gas | 0.39 | 0.55 | 0.52 | 0.64 | 0.55 | 0.58 | 0.53 |
| P0 stack all-hours seam | 0.21 | 0.23 | 0.10 | 0.16 | 0.24 | 0.20 | 0.17 |
| bid stack q1 coal | 0.14 | 0.07 | 0.38 | 0.35 | 0.10 | 0.08 | 0.22 |
| bid stack q1 gas | 0.62 | 0.65 | 0.51 | 0.50 | 0.67 | 0.67 | 0.61 |
| bid stack q1 seam | 0.24 | 0.28 | 0.12 | 0.15 | 0.23 | 0.24 | 0.17 |
| bid stack q2 coal | 0.31 | 0.11 | 0.41 | 0.21 | 0.16 | 0.13 | 0.31 |
| bid stack q2 gas | 0.47 | 0.60 | 0.48 | 0.59 | 0.56 | 0.64 | 0.51 |
| bid stack q2 seam | 0.22 | 0.29 | 0.11 | 0.20 | 0.28 | 0.23 | 0.18 |
| bid stack q5 coal | 0.66 | 0.46 | 0.29 | 0.05 | 0.29 | 0.33 | 0.17 |
| bid stack q5 gas | 0.23 | 0.43 | 0.58 | 0.77 | 0.50 | 0.46 | 0.64 |
| bid stack q5 seam | 0.12 | 0.11 | 0.13 | 0.18 | 0.21 | 0.21 | 0.19 |

**Price medians by load quintile, $/MWh (keeper P1 / rebuilt bid stack / actual):**

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| q1 P1 / bid / actual | 23.4 / 22.2 / 19.2 | 19.1 / 18.0 / 15.1 | 28.9 / 27.2 / 23.3 | 47.2 / 40.3 / 40.2 | 26.3 / 24.9 / 19.6 | 21.9 / 21.2 / 16.9 | 31.4 / 30.1 / 24.2 |
| q2 P1 / bid / actual | 26.4 / 25.1 / 21.1 | 21.6 / 21.0 / 17.1 | 31.8 / 29.7 / 25.8 | 51.7 / 45.1 / 48.4 | 29.7 / 28.1 / 23.1 | 25.4 / 24.5 / 20.4 | 35.7 / 33.4 / 27.7 |
| q5 P1 / bid / actual | 30.3 / 29.6 / 25.9 | 27.9 / 27.0 / 22.6 | 43.8 / 36.0 / 40.9 | 74.8 / 61.2 / 85.9 | 37.4 / 36.4 / 34.5 | 34.8 / 34.1 / 31.0 | 49.4 / 45.8 / 45.6 |

Reading:
- The IMM's coal share is the share of five-minute intervals in which a coal resource set the SMP; the model's is
  the share of hours in which a coal row is the marginal row of a merit clear at the keeper's own thermal quantity
  (the P0 base stack and the P1 bid stack; the bid stack reproduces P1 within the miso-287 residual).
- The model's seam rows (import ladders priced at the neighbour's own DA hub) are marginal in 21–28 % of hours.
  The IMM table has no import category: scheduled interchange is price-taking in MISO's SMP.
- Coal's model share rises with load (bid stack 2020: q1 7 %, q5 46 %) — the opposite of the IMM's "generally in
  off-peak hours". The model's coal is marginal when its ~$30 econ tranches are reached at high load; the real
  fleet's coal is marginal at low load, around $15.

## 4. What the marginal offer is made of (block C)

**Hours in load quintiles 1–2 where a CC_REGULAR econ tranche is the marginal row of the bid stack (medians).** `fuel_print` is the row's delivered gas price in the keeper (EIA-923 plant monthly print, the keeper's `gas_electric_power_monthly_level` / zonal-basis chain); `chicago_hub` is the Chicago Citygate flow-day staircase the same day (`data/raw/gas-prices/miso_citygate_daily.csv`); `wedge_mwh` = (print − hub) × HR:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| n | 894 | 997 | 965 | 916 | 854 | 841 | 885 |
| mc_bid_med | 21.98 | 18.14 | 27.22 | 45.23 | 24.55 | 20.88 | 28.98 |
| hr_med | 7.50 | 7.41 | 7.30 | 7.29 | 7.32 | 7.36 | 7.38 |
| fuel_print_med | 2.667 | 2.165 | 3.400 | 5.883 | 3.054 | 2.526 | 3.638 |
| chicago_hub_med | 2.250 | 1.720 | 2.850 | 5.600 | 2.190 | 1.640 | 3.040 |
| wedge_mmbtu_med | +0.386 | +0.343 | +0.272 | +0.130 | +0.753 | +0.836 | +0.641 |
| wedge_mwh_med | +2.94 | +2.57 | +1.99 | +0.92 | +5.43 | +6.04 | +4.80 |
| vom_med | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 |
| markup_med | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| bid_minus_actual_med | +3.49 | +3.66 | +3.47 | +0.27 | +5.79 | +4.84 | +5.81 |
| p1_minus_actual_med | +4.70 | +4.86 | +5.42 | +6.32 | +6.92 | +5.74 | +7.50 |

**All marginal rows in quintiles 1–2, the capacity-weighted gas print over those hours, and the coal / seam marginal rows:**

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| all marginal mc_bid_med | 23.59 | 19.74 | 28.58 | 42.73 | 26.65 | 22.81 | 31.96 |
| all marginal p1_minus_actual_med | +4.87 | +4.97 | +5.30 | +7.52 | +7.05 | +5.86 | +7.90 |
| all marginal bid_minus_actual_med | +3.63 | +3.89 | +3.29 | +0.54 | +5.84 | +4.96 | +6.19 |
| cc_regular_fuel_print_cap_wtd | 2.639 | 2.184 | 3.864 | 6.498 | 2.890 | 2.288 | 3.527 |
| fuel_print_cap_wtd | 2.890 | 2.327 | 4.077 | 6.575 | 3.032 | 2.391 | 3.667 |
| chicago_hub_mean | 2.334 | 1.817 | 3.472 | 5.915 | 2.246 | 1.709 | 3.076 |
| henry_hub_annual | 2.570 | 2.030 | 3.720 | 6.450 | 2.540 | 2.190 | 3.520 |
| coal marginal n | 793 | 314 | 1371 | 832 | 458 | 374 | 932 |
| coal marginal mc_bid_med | 27.06 | 22.48 | 29.40 | 37.43 | 31.05 | 27.32 | 33.79 |
| seam marginal n | 815 | 1003 | 404 | 534 | 884 | 824 | 610 |
| seam marginal mc_bid_med | 23.80 | 19.88 | 31.27 | 45.56 | 27.01 | 22.93 | 32.38 |

Reading:
- At the CC_REGULAR margin, the fuel print's wedge over the Chicago Citygate flow-day hub is the largest single
  component of the gap in every year it can be measured. The variable-transport leg the owner's convention keeps
  is $0.21/MMBtu for CC_REGULAR (miso-225); the ruled form would remove roughly (wedge − 0.21) × HR of it.
- The startup markup at the low-load margin is zero in every year (the markup lives on the units that start, not on
  the CC that is already on).
- The coal econ offer anatomy: cap-weighted HR 12.6–13.0 (the econ_high multiplier 1.309 × the tranche heat rate),
  the plant's own EIA-923 delivered price, $4.50 VOM, and the ×1.10 non-steam lift (miso-220) on committed /
  econ_low / econ_high / peak. The resulting ~$30 (2020) offer is what keeps coal out of the low-load margin.

## 5. Quantities and coal bands in the low-load hours (blocks D, E)

**Coal position in quintiles 1–2** (`cheapest undispatched coal econ − price`: the offer of the cheapest coal econ MW the bid-stack clear left undispatched, minus the clearing price; capacity-weighted coal econ offer anatomy; the keeper P1 coal band MW):

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| cheapest undispatched coal econ - price, med | +0.06 | +0.13 | +0.02 | +0.10 | +0.12 | +0.16 | +0.06 |
| coal econ offer cap-wtd mc | 31.34 | 35.10 | 37.43 | 34.33 | 37.19 | 35.86 | 34.96 |
| coal econ hr | 12.79 | 12.92 | 12.82 | 12.71 | 12.88 | 12.72 | 12.62 |
| coal econ fuel print | 2.094 | 2.356 | 2.532 | 2.336 | 2.527 | 2.465 | 2.405 |
| coal econ dispatched share of cap | 0.119 | 0.070 | 0.387 | 0.830 | 0.161 | 0.092 | 0.345 |
| coal mustrun MW | 11,789 | 9,334 | 10,276 | 9,308 | 7,627 | 7,098 | 7,377 |
| coal committed MW | 10,800 | 8,671 | 10,370 | 9,837 | 8,643 | 8,316 | 9,205 |
| coal econ MW | 1,575 | 743 | 3,518 | 3,921 | 1,113 | 785 | 2,265 |
| coal total MW | 24,181 | 18,760 | 24,210 | 23,143 | 17,400 | 16,212 | 18,896 |

**Quantities in quintiles 1–2, mean MW.** EIA-930 rows: model class sum vs the BA series (930 interchange is + = net export, so −6,695 is 6.7 GW of net import against the model's 5.5 GW import row; 930 coal sits below the plant-matched EIA-923 by ~1–1.5 GW, miso-295 §2, so the CAMPD rows are the class comparison). CAMPD rows: model − CAMPD net MW by keeper class (CHP classes carry the host-steam basis caveat, miso-116):

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 930 coal model/actual | 24,181 / 21,317 | 18,760 / 16,003 | 24,210 / 21,772 | 23,143 / 19,823 | 17,400 / 15,645 | 16,212 / 14,426 | 18,896 / 17,526 |
| 930 gas model/actual | 14,331 / 17,611 | 13,872 / 17,977 | 12,176 / 15,700 | 14,421 / 18,125 | 18,261 / 22,404 | 19,509 / 23,668 | 17,805 / 20,746 |
| 930 nuclear model/actual | 10,812 / 11,492 | 10,693 / 10,290 | 10,300 / 10,663 | 9,897 / 9,947 | 9,514 / 9,500 | 9,947 / 10,044 | 9,887 / 10,027 |
| 930 wind model/actual | 7,433 / 7,070 | 9,406 / 8,946 | 10,898 / 10,364 | 12,486 / 11,875 | 12,123 / 11,529 | 13,161 / 12,517 | 13,069 / 12,429 |
| 930 hydro model/actual | 986 / 1,050 | 1,083 / 1,114 | 898 / 965 | 867 / 966 | 890 / 911 | 853 / 914 | 873 / 950 |
| 930 other model/actual | 2,355 / 656 | 2,267 / 712 | 2,322 / 784 | 2,375 / 754 | 2,037 / 433 | 1,706 / 281 | 934 / 340 |
| 930 interchange model/actual | 4,758 / -5,792 | 5,536 / -6,695 | 2,902 / -3,845 | 1,381 / -4,170 | 4,053 / -4,153 | 2,379 / -2,607 | 2,032 / -2,164 |
| CAMPD COAL_PRB diff | -79 | +1,025 | -83 | +342 | -579 | -214 | -1,031 |
| CAMPD COAL_BIT diff | +9 | -143 | -77 | +894 | -14 | -23 | -25 |
| CAMPD CC_REGULAR diff | +747 | +192 | -639 | -508 | -423 | +587 | +1,281 |
| CAMPD CC_CHP diff | -2,456 | -2,340 | -1,986 | -2,111 | -2,155 | -2,127 | -1,914 |
| CAMPD ST_GAS diff | -997 | -1,072 | -664 | -433 | +244 | -536 | -645 |
| CAMPD CT_PEAKER diff | -143 | -267 | -295 | -246 | -333 | -292 | -285 |
| CAMPD CT_CHP diff | -753 | -703 | -627 | -765 | -835 | -1,038 | -671 |
| dump hours / curtailed wind hours | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |

Reading:
- CC_REGULAR matches CAMPD within ±0.75 GW in the low-load hours of every year except 2025 (+1.3 GW). Coal is
  +1.0 GW (PRB) in 2020 and within ±1.0 GW elsewhere. The gas shortfall against CAMPD is ST_GAS, CT_CHP and
  CT_PEAKER — the C1 ST_GAS object (routed) and the CHP host-steam basis (miso-116), not the margin. The
  miso-295 §3 gas baseline (model gas 1–3 TWh/month under plant-matched EIA-923) is therefore not a low-load
  margin object: the margin-setting class is on at the measured level.
- The model never spills: zero dump hours and zero wind-curtailed hours in every year. The real market clears
  below $10 in 2.8 % (2020) of hours; this tail is worth +$0.25 of the 2020 gap and is the West wind-congestion
  object (G).
- Model net imports sit 1.0–2.8 GW under EIA-930's net import at low load in 2019–2022 and within 0.3 GW in
  2023–2025; the seam ladder's volume behaviour is adjudicated (miso-262, K) and is not re-opened.
- The keeper's coal in the low-load hours is 94–96 % mustrun + committed in 2019 / 2020 / 2023 / 2024 (coal econ
  dispatched 7–16 % of its capacity). The real coal fleet runs about the same MW and is the price-setting
  resource; the model's coal at that operating point is a block (≤ $9) with its next MW at ~$30.

## 6. What this is, and what it is not

- **Not coal inventory** (miso-295): 2020 is a glut year; the budget dual is ≤ $0.94 of the night residual.
- **Not commitment** (miso-286): flooring online CC at EcoMin moves the night median ≤ $0.12.
- **Not startup markup** (miso-287): zero at the low-load margin.
- **Not quantity**: class MW match CAMPD at the margin-setting classes.
- **It is the offer level of the two rows that are marginal at low load — the CC fuel print over the hub and the
  coal econ tranche level — plus the West/Plains congestion separation (G).**

The IMM's description of the real conduct is consistent with the data: regulated utilities "often continue to
operate their units as 'must-run,' running them regardless of the price" (2024 SOM p.45–46; Table 7: 2019–2022
regulated coal starts 42 % offered economically, 42 % must-run and profitable, 16 % must-run and unprofitable).
A self-committed unit is a price-taker at its schedule and dispatchable above it at its incremental offer; MISO's
off-peak SMP in 2020 (actual q1 median $15.1) says that incremental offer sat near $15, below the delivered-fuel
cost the model charges its econ tranches ($1.9 × 10.6 + $4.5 ≈ $25 at the mustrun heat rate; ~$30 at the econ
tranche heat rate). The model's regulated take-or-pay discount reaches the mustrun and committed bands only.

## 7. Admissible levers, by rule

| lever | status | what it would do here |
|---|---|---|
| `offer_curve_by_group` coal `econ_low`/`econ_high` (and the ×1.10 lift) | owner-authorized price channel, rule 1 (a)–(e); one value all years, ex ante, never swept | lowers the coal econ tranche offers toward the real coal-marginal level; merit-order change is an intended effect. Risk: one config across years also lowers coal offers in 2021–22, where the model already over-burns coal (+5.3/+10.3 TWh vs EIA-923). |
| `miso_gas_marginal_commodity_pricing` + `miso_gas_variable_transport` | O; owner-ruled form (hub + variable transport, 2026-09-06); killed standalone (miso-224 G-3/G-4: coal collapsed −13 TWh) and jointly with the seam (miso-225, G-3 by 37 MW) | removes ~(wedge − 0.21) × HR at the CC margin: about $1.0/MWh in 2020. Named successor was a JOINT test with a coal-side mechanism, because hub gas alone undercuts the ~$30 coal econ tranches wholesale. |
| coal self-commitment floor | refused at phase 0 (miso-224, rule 19): miso-53's per-plant must-run band is the self-commitment representation | — |
| `internal_congestion_split` | G (killed 2026-10-01; reopens on RO-1 only) | the West/Plains part (~+3 pp of the +11.6 %) |
| `negative_renewable_offers` / `wind_ptc_vintage_offers` | `·` for MISO (never adjudicated) | the <$10 tail: +$0.25 of +$2.54 — too small to carry the gate |
| seam ladder level | `seam_neighbour_hourly_ladder` K (miso-262) | marginal 21–28 % of low-load hours at the PJM DA level; not re-opened |

The owner-ruled gas form alone (hub + the $0.21 variable leg) removes (wedge − 0.21) × HR at the CC margin:
about $1.3 / 1.0 / 0.5 / 0 / 4.0 / 4.6 / 3.2 per MWh in 2019–2025 — in 2020 a quarter of the +$3.7 at that margin,
in 2023–2024 most of it. The one combination that is both admissible and sized to the object is the first two
rows together: price gas at the owner-ruled convention (removing the print wedge the CC margin carries) **and**
move the coal econ tranches through the authorized channel so coal stays in merit where the real fleet's coal
was marginal. miso-224 showed
that the first without the second collapses coal (C1); this record shows why — the model's coal econ sits at ~$30
against a real coal-marginal price of ~$15, so any gas repricing below $30 takes coal's energy. Whether to spend a
PRECOMMIT on that joint arm is an owner decision (§8). No value is proposed here, because a multiplier chosen from
these residuals would be a swept value (rule 1 (c)); a PRECOMMIT would have to identify it ex ante from a
declared source (candidates: the IMM Table 1 coal SMP share reproduced at zero LP by the stack census; or the
pre-lift table, as miso-275 did for CC).

## 8. Owner decision

Put as decision cards in the session's final message. Options recorded here so the record is complete:
(A) PRECOMMIT a joint arm — gas at hub + variable transport (O cells, owner-ruled form) + coal econ band
multiplier set ex ante through the authorized channel, one value all years, kill rules on C1 coal/gas and on the
coal marginal share moving toward IMM Table 1; (B) the coal channel alone (exempt coal from the ×1.10 lift, the
miso-275 precedent, or a declared econ value); (C) record and leave C3a 2020 as a known miss, move the chain to
the next failure.

## 9. Where MISO stands

Keeper unchanged. Train 2023–2025 CALIBRATED (C3c ledgered). Full span NOT-YET on C1 ST_GAS 2019 (routed),
C3a 2020 (+11.6 %) and C3b 2021 (0.201). **No frontier** (owner, 2026-09-28: routed misses are failures).

## Retrievability

No solve. The probe, its JSON output and this record are in this PR. The six SOM PDFs are not committed. The
first all-years run left `annual_lw` / `zone_err_lw` null in 2019 / 2021 / 2022 / 2025 (one unpublished hub hour
per year, 1,200 in 2022, leaked through an unmasked sum); the sums were masked, those two fields were recomputed
on the identical construction, and 2019 was re-run end-to-end with the fixed probe (block A reproduces the
scorer's C3a values in every fully covered year).
