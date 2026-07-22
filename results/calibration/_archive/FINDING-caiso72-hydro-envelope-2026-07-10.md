# FINDING — caiso-72: the measured hydro deliverability envelope moves the CT/mix cluster the right way; the residual CT gap is import-shape + battery/commitment, not water (2026-07-10)

**Probe:** `2026-07-10-caiso-72-hydro-envelope` (+ `2026-07-10-caiso-72-hydroenv-ablation`
twin), pre-registered single-delta A/B on the caiso-70 recipe:
`hydro_dispatch_envelope=True` — the joint water fleet (conventional hydro +
pumped-storage net discharge) capped hourly at the measured per-(month × hod)
p95 of EIA-930 `NG: WAT` (`constants.HYDRO_ENVELOPE_PERCENTILE`,
`eia_loader.measured_hydro_hourly_envelope`, model-clock row-order bucketing).
Driver: `FINDING-caiso72-step0-evening-displacement-2026-07-10.md` (the STEP-0
displacement ledger). Scripts: `scripts/probes/_caiso72_hydro_envelope_ab.py`.
Scored on rubric v2.4. Registered per rule 15; NOT proposed for promotion.

## Pre-registered directions vs outcome (2023/2024/2025)

| metric | caiso-70 main | **caiso-72 main** | direction called | actual |
|---|---|---|---|---|
| CT_PEAKER (TWh) | 0.90 / 0.92 / 0.82 | **1.40 / 1.23 / 0.87** | up ✓ | 4.56 / 5.24 / 3.09 |
| evening (h17-22) water vs measured | +0.8 GW over (2024) | **on the measured level** (3,929 vs ~3,900 MW, 2024) | down to measured ✓ | — |
| 2023 hrs>$200 (zonal max) | 540 | **473** | disclosed as may-worsen — **improved** | 21 (RT) / 41 (DA) |
| 2024/25 hrs>$200 | 0 / 0 | 0 / 0 | local tail cannot form yet (topology) | 35 / 8 |
| LA_BASIN mean LMP | 70.05 / 47.65 / 51.45 | 70.20 / **47.19** / 51.47 | ease or hold ✓ | SP15 49.39 / 32.68 / 32.22 |
| CC_REGULAR (TWh) | 61.94 / 65.05 / 65.32 | 61.38 / 64.76 / 65.25 | down ✓ (small) | — |
| C7 D-1 CT profile_r | 0.74-0.77 band | **0.782 / 0.771** (gate 0.8) | toward gate ✓ | — |

Every pre-registered direction held, including the risk disclosure resolving
favourably: capping the 2023 wet-year evening hoard *reduced* the spurious
system tail (473 vs 540 h) instead of inflating it — the hoard was part of the
tail's formation (water crowding the belly pushed the scarcity-priced hours
into a narrower, higher stack), not its relief.

**Verdict (v2.4): NOT-YET — but C6 governance PASS (attestation carried from
caiso-70, ZERO new free parameters) and C8 PASS.** Fails: C1 (2024 CC_REGULAR
+9.0 TWh), C2 (2025 gas +8.5 %), C3a (+21/+35/+49 % vs RT; +9.6/+23.4/+45.1 %
vs DA), C3b, C3c, C4 (gas r 0.80/0.57), C5a, C7 (CT profile_r 0.78/0.77 vs
0.8 — 2025 CT now below the 2 % materiality floor). The cluster moved together
as the STEP-0 finding predicted, by ~+0.3-0.5 TWh of the 3.7-4.4 TWh CT gap.

## Ablation twin

Zero-forcing ablation (merchant floors/bridges off, envelope kept — it is a
cap, not a floor, so it survives ablation by construction): CT_PEAKER
2.72/1.98/1.08 TWh vs main 1.40/1.23/0.87. The RA-bridge forced CC still
crowds ~0.7-1.3 TWh of CT out of the pockets (the caiso-70 signature), and the
ablation's higher CT confirms the remaining commitment-side displacement is
floor-borne, not water-borne.

## What this closes / what remains (probe queue)

- ~~Hydro/water hoarding as an evening displacer~~ — **closed by a measured
  mechanism** (structurally-correct, rule 14; evening water now sits on the
  measured level in all three years). Keep `hydro_dispatch_envelope=True` in
  every subsequent CAISO recipe: it is a real capability limit whatever the
  residual does (rule 1).
- **Live lead #1 — shaped firm import base** (STEP-0 channel #2, Tier-2 of the
  TTC diagnosis): the deep-evening import deficit (−1.4..−2.2 GW vs measured)
  is now the largest single evening supply-side miss. Measured DMM RA-import +
  EIM shape; rule-14 input; expected to relieve the evening price level (C3a)
  and let the pocket stack thin toward CT in the ramp.
- **Live lead #2 — battery operational realism**: model batteries discharge
  into h15-17 (real fleet still charging) and h21-23 (real fleet SOC-spent);
  needs a measured storage-AS power reservation (rule 13's own example) —
  data intake required (CAISO storage AS awards).
- **Live lead #3 — demand basis**: EIA-930 `Demand` (the model input) runs
  1.4-1.7 GW below the supply-implied actual load in the h14-17 ramp where
  actual CT ramps; adjudicate 930-Demand vs net_gen−interchange vs CAISO TAC
  actuals (rule 14 conflict between published measurements).
- The C3a price *level* (+21..+49 %) remains the offer-curve step (rule 1
  order: structure first, level second) — untouched by this probe.
