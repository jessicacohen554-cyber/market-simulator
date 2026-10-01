# FINDING — PJM-NEXT-10: the COAL_BIT over-run is synced-unit loading in coal-cheap years; no admissible lever found yet (zero LP)

> **RELABELLED 2026-09-29 (owner instruction, same session): OPEN, not a model-class limit.** This session found no admissible lever; it did NOT show the LP is structurally unable to reproduce the loading. The over-run is year-dependent (2023/24 fit) and tracks the coal/gas ratio, which points to a fixable merit-order or offer input. Next test queued for PJM-NEXT-11: PJM's own offered EcoMax for the LONG_RUN segment by year (§5).

**Keeper** `2026-09-28-pjm-next8-exitfix` (bundle `results/calibration/pjmnext8_xf_span`), unchanged. **Zero LP.**
Probe `scripts/probes/_pjmnext10_coal_phase0.py` writes `results/calibration/_pjmnext10_coal_phase0.json`.
Inputs: the keeper's run payload, the bench, its committed `hourly/system_<y>.parquet`, CAMPD unit-level
hourly, the keeper's outage extracts, EIA-923 coal receipts, PJM DA hub LMPs, and PJM DA binding constraints.
**Owner cards:** *"Record as limit"* (card 1) and *"Record, no successor"* (cards 2–3), both **superseded the same day** by *"Relabel as open and queue the test. Have the next session fetch the data."*

## 1. Where the over-run sits (bench COAL_BIT plants, model − CAMPD, TWh)

| year | total | above synced (availability) | within synced (loading) | no CEMS | C1 (vs EIA-923) |
|---|---|---|---|---|---|
| 2019 | +18.76 | +6.43 | **+10.47** | +1.85 | +10.61 |
| 2020 | +12.16 | +4.28 | **+7.70** | +0.17 | +3.9 |
| 2021 | +15.66 | +4.96 | **+10.07** | +0.63 | +17.14 |
| 2022 | +7.61 | +5.06 | +1.87 | +0.68 | +6.8 |
| 2023 | −0.11 | +1.22 | −0.58 | −0.75 | +0.3 |
| 2024 | −0.07 | +2.30 | −2.11 | −0.25 | +0.9 |
| 2025 | +13.71 | +2.90 | **+11.43** | −0.62 | +11.3 |

- **Online hours match CAMPD** at every large plant (e.g. Gavin, Amos, Mitchell, Rockport: within ±1 %).
- **The gap is MW-when-on.** For example, in 2025 Mitchell runs 947 MW when on in the model vs 624 actual, and Amos 1,481 vs 1,140.
- **It is flat in time:** +2.1 GW (2019), +1.8 (2021), +1.6 (2025), ≈0 (2023/24). It is the same at night and in the day, and the same on weekdays and weekends. That rules out price-shape and commitment-cycling stories.

## 2. It tracks coal's depth in merit

EIA-923 delivered coal (bench plants, MMBtu-weighted) ÷ the keeper's gas price:

| year | gas $/MMBtu | coal $/MMBtu | coal/gas | C1 COAL_BIT |
|---|---|---|---|---|
| 2024 | 2.19 | 3.01 | 1.38 | +0.9 |
| 2023 | 2.54 | 3.08 | 1.21 | +0.3 |
| 2020 | 2.03 | 2.09 | 1.03 | +3.9 |
| 2019 | 2.57 | 2.14 | 0.83 | +10.6 |
| 2021 | 3.72 | 2.06 | 0.55 | +17.1 |
| 2022 | 6.45 | 2.63 | 0.41 | +6.8 |

2025 has no receipts file on disk. 2022 is the exception: it is the coal-supply-constrained year (stocks 9–14 Mt, `coal_fuel_inventory` cell).

**Reading:**
- When coal is cheap relative to gas, the LP loads every synced coal unit up its offer steps.
- Real units stay at intermediate load: 76–86 % of synced capability at $25–50 in 2019/2021/2025. Near-max hours are rare in reality (Mitchell 2025: 2 %) but common in the model (17 %).
- When coal is dear (2023/24), both sit near the floor and agree.

## 3. Ruled out, measured

| candidate | result | verdict |
|---|---|---|
| Outage windows (availability) | Windows cover **90–99 %** of dark coal capacity-hours in every year and every price bin | not it |
| Pmax / capability | Σ per-plant p99 output: model vs CAMPD **−5.2 % to +5.5 %** | not it |
| West-side congestion (AEP → east) | AEP GEN HUB − WESTERN HUB DA congestion is **−0.28 / −0.31 / −0.56 $/MWh** in 2019/20/21 (R² 0.85–0.91), spread over many 115–138 kV facilities; −1.8 to −4.2 in 2022–25 | cannot move 2019/21 |
| Price level at coal zones | 2021 +2 % at AEP, 2025 −6 % at AEP / −17 % at West_APS vs hubs; over-run largest there anyway | not it |
| PJM's own offers | pjm-h9c: own-year 2020–22 offers are *cheaper* than pooled; installing them raised 2021 coal +25 TWh | wrong sign |
| Incremental-HR econ pricing (`coal_econ_two_sided`) | Prices econ at incremental < average HR, which makes coal cheaper | wrong sign |
| PJM min-load offers on the committed rung (`pjm_offer_midcurve_minload_segments`, R) | Cuts hardest where LMP often sits below the committed price, i.e. LOW-price years (2020/23/24) | wrong year sign |
| Authorized offer-band channel (rule 1 carve-out) | No ex-ante value exists that is not read off this residual. The econ bands already sit at 0.93–1.04× PJM's measured offers (pjm-h8) | refused, rule 1 (c) |

**Also examined, and not the driver:** per-plant floor overshoot, where the model's p5 MW-when-on sits above CAMPD's (Mountaineer ≈1,000 vs 520–770 MW; East Bend 547 vs 255–360). Its upper bound is 6.8–13.2 TWh a year, but it is present in 2023/24 too, where it is offset by under-loading at Rockport and Gavin. It is the h8 committed-band object, and its correction carries the wrong year sign (row above).

## 4. Cards 2–3 (reported, out-of-span)

- **CT_PEAKER 2019–22 under-run.** In 2021, 6.2 of the 8.4 TWh bench shortfall falls *outside* the actual top-10 % price hours, spread across shoulder months. That is the same coal-displaces-gas swap as §2, not a scarcity-tail object.
- **Energy balance, 2023** (the one year with EIA-930 BA totals on disk):
  - Demand matches: 784.8 vs 783.0 TWh.
  - The model exports **11.8 TWh less** (28.1 vs 39.9) and runs **6.6 TWh less hydro** (8.9 vs 930 WAT 15.5).
  - The bench EIA-930 rows show the same export deficit in 2019–2024 (−9.5 to −13.6 TWh); 2025 is +5.0.
  - Matching actual exports would *add* fossil. **Interchange does not explain the fossil surplus.**
- **C3a 2020 (+17.5 % load-weighted) / 2022 (−7.8 %) and C3b 2022.** Price-distribution compression:
  - 2020: actual has 18 % of hours ≤ $15 vs 1 % in the model.
  - 2022: actual p99 is $210 vs $105.
  - This is the variance-compression object pjm-h12 named. No new operand.

## 5. Verdict

**COAL_BIT's out-of-span over-run (2019 +10.61, 2021 +17.14) and CT_PEAKER 2021 (−9.59) are OPEN: no admissible lever found yet.** The LP loads synced coal to its offer steps whenever coal clears, while real PJM coal holds intermediate load in coal-cheap years. That describes the symptom; it is **not** shown to be structural. Three reasons against a limit label:

- The error is year-dependent. 2023/24 fit, and the error tracks the coal/gas ratio, which a structural LP limit would not do.
- 2022 breaks the fuel-ratio story (the cheapest coal relative to gas, yet a small over-run). That was explained as a coal-supply year, untested.
- PJM's offered EcoMax was dismissed as needing unit-identified data. It does not: the LONG_RUN segment can be totalled by year without unit identity.

The out-of-span rows stay reported and non-gating (rule 30(c)). The training span's one failure (CC_REGULAR 2023 +8.48) is a separate, already-recorded limit (PJM-NEXT-9, `internal_congestion_split` G).

**Queued for PJM-NEXT-11 (zero LP first):**
1. **Offered EcoMax.** Re-fetch the PJM energy-offers corpus for 2019–2025 (`fetch_pjm_energy_offers.py --years 2019 … 2025`). Total `avg_ecomax` against offered capacity for the LONG_RUN segment (the `derive_pjm_offer_midcurve.py` segmentation) by year and hour. If real coal-like units offered materially less MW in 2019/21/25 than in 2023/24, that is a measured input (rule 14) and the candidate lever.
2. **2022 coal-supply check.** Test whether 2022's small over-run reflects the coal-supply constraint (`coal_fuel_inventory`), or whether the fuel-ratio story is wrong.
3. **C3a 2020/2022, C3b 2022.** Verify, rather than assume, that these are the pjm-h12 variance-compression object.
