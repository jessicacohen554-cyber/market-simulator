# FINDING — NWPP-NEXT-17 phase 0 (ZERO LP): Bridger's Jun–Oct trough is a flat NWPP price, not its offer alone

Object: keeper #20 (`2026-10-01-nwppnext16c-combined-vintage`), C4 coal 2023 r 0.669 / NRMSE 0.313, the only failing record.
Source: keeper #20's own 2023 leg (`a54c7b97`, `results/calibration/nwppnext16c_2023`, extracted with `git archive`; its
`unit_hourly` carries `mc` and `red_cost`, `system.parquet` the zonal duals). Raw: EIA-923 Page 5 receipts, WEIM hourly
ELAP (`data/raw/nwpp-weim`), NID pondage. Probe: `scripts/probes/_nwppnext17_bridger_price_phase0.py`. No LP was run.

## 1. What the LP sees at Bridger (8066), 2023

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| model GWh | 1393 | 1218 | 993 | 623 | 189 | 242 | 328 | 1412 | 316 | 215 | 795 | 795 |
| CEMS GWh | 906 | 416 | 294 | 164 | 345 | 662 | 1155 | 1171 | 892 | 1267 | 879 | 960 |
| econ offer $/MWh | 40.8 | 42.3 | 40.8 | 37.9 | 38.7 | 39.0 | 41.5 | 39.5 | 39.2 | **51.0** | 47.9 | 47.5 |
| pile dual $/MWh | −5.56 | −5.56 | −5.56 | −5.56 | −5.56 | −5.56 | −5.56 | −5.56 | −5.56 | −5.56 | −5.21 | −0.47 |
| NWPP-EAST price, mean | 163.6 | 66.1 | 45.1 | 34.8 | 25.7 | 25.1 | 32.9 | 34.4 | 31.6 | 32.6 | 42.7 | 47.0 |
| NWPP-EAST price, P10–P90 | 145–231 | 37–81 | 43–47 | 34–37 | 22–30 | 23–30 | 32–36 | 34.0–34.0 | 31–34 | 31–34 | 42.7 | 47.0 |

- **The take floor is one annual dual.** It is a flat −$5.56/MWh credit (≈ $0.50/MMBtu) from January through October. That is
  the soft cumulative floor binding at Oct-end and Dec-end (FINDING-nwppnext14 §1). Bridger's effective offer is about $33–36
  in Jun–Sep.
- **The price Bridger faces is flat within each month.** In Jul–Oct the NWPP-EAST P10–P90 spread is $1–4. August sits at
  $34.0 in every hour, exactly Bridger's effective offer, so Bridger is the knife-edge unit for the month. In Jun, Jul, Sep and
  Oct the price sits $1–10 below the effective offer, and Bridger idles to its must-run tranche.
- **The October offer spike is real data, and it is not the lever.** Jim Bridger Mine's captive delivered price jumps
  $3.6–3.7 → $5.2–5.4/MMBtu in Oct–Dec 2023 (Black Butte and NARM stay at $2.1–2.9). The plant-monthly seam passes this
  into the offer ($39 → $51). Holding Oct–Dec at the Jan–Sep fuel price adds only ~0.08 TWh in October (price-taker
  estimate), because October's flat $32.6 is below Bridger's offer even without the spike.

## 2. Who sets that flat price

- NWPP-EAST, INLAND, NW and OR clear at one price (equal monthly means; SNV differs). So the price is a **system** price.
- In NWPP-EAST, a hydro unit is marginal in 500–700 hours of every month. In 80–95 % of those hours, at least one marginal
  unit has ≥ 720 h of NID pondage (e.g. 61853, 13 MW, 8,559 h; 64123, 7.5 MW, 12,490 h). The zone holds only 228 MW of hydro
  in 42 plants. These small plants share the system λ, which is the **monthly hydro water value**, the dual of the monthly
  energy budget.
- So `hydro_pondage_bound` on low-pondage plants would not remove the flat price: the large-storage plants would still carry it.

## 3. Measured vs model price (2023, Jun–Dec; WEIM RTPD ELAP, hourly on the model clock)

| | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---:|---:|---:|---:|---:|---:|---:|
| PACE mean | 25.6 | 52.9 | 38.4 | 31.0 | 40.3 | 45.7 | 39.6 |
| IPCO mean | 26.6 | 51.8 | 39.2 | 33.3 | 56.0 | 53.4 | 45.2 |
| BPAT mean | 28.9 | 55.3 | 48.9 | 37.6 | 65.5 | 56.8 | 47.1 |
| **model EAST mean** | 25.1 | **32.9** | 34.4 | 31.6 | **32.6** | 42.7 | 47.0 |
| PACE within-day SD | 9.7 | 36.3 | 12.2 | 7.5 | 11.2 | 13.0 | 8.4 |
| PACE between-day SD | 7.4 | 21.2 | 9.0 | 5.9 | 6.3 | 15.6 | 8.2 |
| **model EAST within-day SD** | 2.8 | 1.3 | 1.5 | 0.8 | 1.3 | 1.5 | 0.8 |
| **model EAST between-day SD** | 1.6 | 1.0 | 1.2 | 0.7 | 0.7 | 1.0 | 0.4 |

- The model has about **one tenth** of the measured variance, both within days and between days, in every month.
- The July and October levels are **$15–30 low** against every BA. WEIM is a real-time imbalance price, and it sits 22–38 %
  *below* the Mid-C Peak index (`data/raw/nwpp-weim/gate.json`, D3), so the bilateral energy value is higher still.

## 4. Bridger's offer against the measured price (price-taker, no pile dual)

| TWh | Jun | Jul | Aug | Sep | Oct | Nov | Dec | Jun–Dec |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| model | 0.24 | 0.33 | 1.41 | 0.32 | 0.22 | 0.79 | 0.79 | 4.1 |
| CEMS | 0.66 | 1.16 | 1.17 | 0.89 | 1.27 | 0.88 | 0.96 | 7.0 |
| keeper offer × PACE price | 0.36 | 0.96 | 0.68 | 0.42 | 0.43 | 0.73 | 0.51 | 4.1 |
| keeper offer × IPCO price | 0.39 | 0.99 | 0.73 | 0.49 | 0.67 | 0.86 | 0.64 | 4.8 |

With the measured price, July recovers most of its gap. Aug–Oct still under-run by 0.4–0.8 TWh/month. Bridger ran
baseload at prices below its F923 average cost. This is consistent with non-cycling commitment or a captive-mine variable
cost below the average. Arm D's form of the captive-mine price was tested and rejected (NEXT-16).

## 5. Reading (rules 1, 13, 14, 19)

- **The lever as handed off ("Bridger seasonal offer") is mis-targeted.** Bridger's summer trough is mainly a
  price-formation defect: NWPP's system price is the monthly hydro water value, flat within the month. Any Bridger-specific
  offer change that closed C4 would be fitted to that price error. That is a tuned passthrough (rules 1 and 13, closed).
- **The structural object is NWPP hydro's within-month freedom.** The monthly budget lets the LP shave every peak to one
  water value. This is the same defect NYISO-218 localised, and that `hydro_budget_period_by_instrument` addresses (NWPP cell
  `U`, no registry entries). The NYISO arm was rejected (`R`) for an NYISO-specific reason. The NWPP-49 pondage design (a2)
  would not reach the large-storage price setters (§2).
- **Two residual items are real but small:** (i) the Oct–Dec captive-mine price spike (§1; an inventory-cost question, about
  0.1 TWh); (ii) the Aug–Oct gap that remains at measured prices (§4; commitment or variable cost).
- C3 (price) is UNSCORED for NWPP, so nothing in the rubric currently sees §3. C4 coal 2023 is its visible symptom.
