# FINDING — C2 2025 gas-excess root cause: the 2025 hydro budget rides a 26-of-185-plant preliminary EIA-923 vintage (12.3 of the measured 21.3 TWh); the missing 9 TWh of inflow is served by gas, imports and un-curtailed solar; the evening-CC commitment build is gated OFF by its own §0 re-measure (2026-07-11)

**STEP-0 decomposition + rule-14 data adjudication** (no mechanism until
measured; the probe on the resulting fix is caiso-76). Answers the caiso-76
session task: decompose the 2025 C2 gas excess (+6.5 %, the single
promotion-critical gate vs the keeper's CAVEAT) by class × month × hod,
reconcile the C5a 2025 +46 % CO2, and re-measure the evening-CC design's §0
gate on the caiso-75 line. Model side throughout: the committed caiso-75
payload (`2026-07-11-caiso-75-demand-clock`, decoded via the scorers' own
`legitimacy_diagnostics.load_payload_plants`). Reproduce:
`scripts/caiso_belly_commitment_probe.py --run-id
2026-07-11-caiso-75-demand-clock`, the analysis blocks below off
`data/raw/campd-unit-level/CA_{2023..2025}.parquet`,
`data/raw/eia-930-hourly/CISO hourly.parquet`, and
`market_sim.data.hydro.load_hydro_budget` /
`market_sim.data.eia_loader.measured_monthly_hydro`.

## 1. The §0 re-measure gate: evening-CC build is OFF for now

`caiso_belly_commitment_probe` on the caiso-75 line (CC_REGULAR+CC_CHP GW
online, model / actual / gap):

| year | belly h9-15 | evening h18-21 |
|---|---|---|
| 2023 | 5.3 / 6.3 / **+1.1** | 9.1 / 10.8 / **+1.7** |
| 2024 | 5.1 / 6.0 / **+0.9** | 8.9 / 10.0 / **+1.1** |
| 2025 | 5.8 / 5.0 / **−0.8** | 8.3 / 8.5 / **+0.3** |

The 2025 evening gap is under the design doc's ~0.5 GW build threshold and
the 2025 belly has FLIPPED to model-over (−0.8 GW). Per
`docs/handoffs/caiso-evening-cc-commitment-design-2026-07.md` §0 the
mechanism is not built this session: a floor that ADDS evening CC energy
cannot address a C2 gate that is an annual-volume EXCESS, and 2023/24's
remaining evening gap must be re-measured on the caiso-76 line first (the
hydro fix moves evening supply — hydro peak-shaves exactly there).

## 2. The 2025 excess is off-peak CC flatness, not evening posture and not a fuel-split error

Model-vs-CAMPD class × month × hod (2025, summer months 6-9, CC_REGULAR
mean GW): overnight h0-6 model 9.4-9.7 vs actual 7.7-8.5 (**+1.2 to +1.7
GW**); belly h9-15 model ~7.0 vs actual ~5.0 (**+2.0 GW**); evening ramp
model LATE (h17: 7.3 vs 9.0, h18: 8.2 vs 9.6). Reality's 2025 CC fleet
cycles hard; the model's runs flat. The excess concentrates Apr-Oct
(model−CAMPD monthly delta swings ~+1.2 TWh/month against the 2024
basis relationship). D-2 attribution rules out the floors: the RA bridge
forces only 1.59 TWh of 2025 CC_REGULAR (2.5 % of class) — the flatness is
*economic* dispatch, i.e. an input error, not a forcing mechanism.

Every independent actual says 2025 gas genuinely fell and the model missed
it: EIA-930 CISO NG 85.4 → 79.0 TWh (−7.5 %, July −30 %), CAMPD CA gross
74.9 → 63.5 (−15 %), CAMPD-implied CAISO CO2 27.0 → 21.7 Mt (−20 %); the
model is flat (72.5 → 73.0 on the C2 grid basis).

## 3. Root cause: the 2025 conventional-hydro budget is missing 9.0 TWh

The year-over-year supply-mix table (model `gmModel` vs measured EIA-930):

| supply (TWh) | 2023 m/a | 2024 m/a | 2025 m/a |
|---|---|---|---|
| hydro (NG: WAT) | 23.8 / 24.4 | 21.2 / 22.8 | **12.3 / 21.3** |
| gas (C2 basis) | 73.2 / 71.8 | 72.5 / 69.4 | 73.0 / 68.5 |
| net imports | 34.0 / 28.5 | 32.2 / 30.8 | 40.7 / 35.9 |
| solar | 39.8 / 37.1 | 47.8 / 44.7 | 53.2 / 49.7 |

2023/2024 ride final annual EIA-923 vintages and land within 0.5/1.6 TWh of
the 930 hydro actual. The 2025 vintage is the monthly-survey-only early
release: `load_hydro_budget('CAISO', 2025)` returns **26 of ~185 plants,
12.32 TWh** against the measured 21.32 (930 `NG: WAT`). The missing 9.0 TWh
of zero-carbon, mid-merit inflow is served by gas (+4.4 TWh over the
deflated-930 family actual = the C2 FAIL), imports (+4.8 over measured) and
un-curtailed solar (+3.6 over 930) — and, because hydro is the
peak-shaving resource, its absence also flattens the CC posture (§2) and
inflates C5a. The C1 2023/24 CC_REGULAR over-run (+5.4/+7.6 TWh) is NOT
this defect (their budgets are near-measured) — that cluster stays open.

**Rule-14 decision: fix with the existing measured machinery** —
`hydro_backfill_year=2024` (carry non-reporting plants at their 2024
monthly generation: per-plant coverage + MW envelope; restores 160 plants)
+ `hydro_eia930_monthly=True` (repin every year's monthly budget to the
measured 930 `NG: WAT` total: 2023 23.90→24.40, 2024 21.48→22.68, 2025
12.32→**21.32** TWh). Built for exactly this failure mode (NEISO-2025
precedent in the flag help); first keeper-line use. Zero fitted
parameters; forward story by construction (forecast keeps its climatology
budget; the correction regenerates on the early-release cadence and dies
when the final 923 file lands). Consistent with the standing
`hydro_dispatch_envelope` (caiso-72): the envelope's measured hourly
ceiling was already 930-shaped — the restored budget dispatches *into* it.

Disclosures: (a) with `backfill_year=2024`, 2023 carries 5 plants
(+0.42 TWh pre-repin) absent from its final vintage; the repin rescales the
total back to the measured 24.40, so only per-plant shares shift. (b) CISO
930 `NG: WAT` includes pumped-storage net output (no separate PS series) —
the repin target slightly understates conventional hydro by PS pumping
losses; same like-for-like note as the envelope cap.

## 4. C5a reconcile: the 2025 CO2 actual is itself vintage-understated (bench intake follow-up)

Model 31.66 vs bench actual 21.68 Mt (+46 %). The gas-volume excess at CC
intensity (~0.4 Mt/TWh × 4.4 TWh ≈ 1.8 Mt) explains a fraction; the hydro
fix will remove most of that fraction plus mix effects. But the bench
actual itself is derived by applying eGRID/CAMPD intensities to the
**preliminary-923 class generation** — its CO2-implied CAISO CC_REGULAR
generation is 37.5 TWh full-plant, inconsistent with the 930 family actual
(~68.5 TWh grid gas) the same year's C2 gate scores. Expect C5a-2025 to
improve materially under caiso-76 but NOT to clear the ±10 % band until the
2025 bench CO2 actual is rebuilt on a complete-coverage basis
(**follow-up filed**: rescale the 2025 CAMPD-derived CO2 the way C2's
family fallback rescales generation, or wait for eGRID 2025). This is a
benchmark-vintage caveat, never a tuning target (rule 13).

## 5. Also measured this session (context for the queued battery-economics lead)

From the `storage-as-awards` raw quarterly files (LESR = batteries, RTD
market, `TYPE=EN` schedules; HYBD excluded — its EN carries co-located
solar): actual CAISO battery discharge 5.7 (2023) → 10.0 (2024) → **12.1
TWh (2025)** (IFM: 9.8 in 2025); charge centered h10-15 (solar belly, zero
overnight beyond ~0.3 GW), discharge h17-24 (peak 6.5 GW at HE20 in 2025)
plus a morning spike (1.9 GW at HE7). Model 2025 throughput 10.48 TWh sits
between DA and RT — battery cycling VOLUME is roughly right on the
caiso-75 line, so the caiso-74 re-attributed "battery over-cycling"
hypothesis is NOT the C2 driver; the cycling-cost adder (Task 3) remains a
physical-realism item, evaluated after the hydro correction lands.

## 6. Probe caiso-76 (pre-registered before solving)

Single delta on caiso-75: `hydro_backfill_year=2024` +
`hydro_eia930_monthly=True` (`scripts/probes/_caiso76_hydro_budget_ab.py`,
main + zero-forcing ablation twin, 2023-2025 one bundle). Directions,
called before the solve:

- **2025**: gas family falls from +6.5 % toward the ±2.5 % band; imports
  fall toward measured 35.9; C5a falls materially (full clearance NOT
  expected — §4); off-peak CC flatness eases; C4 gas r rises; C7/C8 hold.
- **2024**: budget +1.2 TWh → gas ~−1 TWh; C1 CC_REGULAR +7.64 eases
  slightly.
- **2023**: budget +0.5 TWh; near-neutral; C3a/C3c tail effects second-order.
- DISCLOSED RISK: gas may not reach the band (the C1 CC-over cluster is a
  separate open defect); the measured budget stays in regardless of the
  residual (rule 14).
