# FINDING — miso-280 phase 0: Riverside remap is a real identity fix but no gate lever; no public VLR input exists; South storm gas has no admissible daily Gulf print

```
LANE    : miso-280 (MISO lever queue §5.4; handoff candidates B, C, D)
KEEPER  : 2026-09-27-miso-279-stcov (results/calibration/miso279_span, 2019-2025) — unchanged
LP      : none (zero-LP phase 0)
PROBES  : scripts/probes/_miso280_riverside_remap_footprint.py -> results/calibration/_miso280_riverside_remap_footprint.json
G-DRIFT : 47d3f872..6ca311d4 (26 solve-path files, 96 commits): ALL INERT for MISO; MISO solve-surface
          fingerprint unchanged (216 rows, hash 2d9f493abe84). Keeper bundle remains a valid form-4 control.
```

## 1. C — Riverside CAMPD remap (55641 CT-03/CT-04 → EIA 64020)

**Identity confirmed.** CAMPD files West Riverside's CTs (EIA 64020: CTG3/CTG4 232.9 MW each + STG2 257.4 MW,
in service 2020) as `CT-03`/`CT-04` under Riverside 55641 (CTG1/CTG2/STG1). CAMPD CT-03+04 gross tracks EIA-923
64020 net within 2 % every year (2023: 4.31 vs 4.25 TWh). Both plants are CC_REGULAR in the MISO fleet.

**Live solve path: inert.** The keeper's fleet build reads no raw CAMPD; `data/outages.py` routes on committed
`facility_id`. Post-solve scoring reads the remap (`_campd_hourly_frame`, `bench_multiclass`).

**Derived artifacts the keeper reads that carry 55641 CT-03/04 rows** (move only on re-derive, rule 23 trigger = this
identity data change): `campd-unit-outages-unitroute-MISO` (65 rows), `-shortgas-` (24), `-maxgen-unitroute-` (10),
`campd_cc_heat_rates_MISO` (55641 flagged `boundary_above_band`; 64020 has no row → fallback rate),
`thermal_tranches-fuelsplit-stcov-MISO` (55641 median CF 150 %), `plant_emission_rates_v2`.

**Availability footprint (fleet-only, outage rows re-routed; TWh):**

| yr | 55641 keeper → remap | 64020 keeper → remap | CC_REGULAR Δ |
|---|---|---|---:|
| 2020 | 0.50 → 2.56 | 4.11 → 2.72 | +0.66 |
| 2021 | 1.47 → 4.07 | 6.01 → 2.70 | −0.71 |
| 2022 | 2.42 → 3.52 | 6.06 → 3.78 | −1.17 |
| 2023 | 3.16 → 4.00 | 5.88 → 4.65 | −0.38 |
| 2024 | 3.19 → 3.73 | 5.95 → 5.20 | −0.21 |
| 2025 | 3.47 → 4.04 | 5.87 → 5.15 | −0.16 |

The mis-route is real (55641 regains 0.5–2.6 TWh), but the fleet net is small and mostly negative: the
miso-274 "2–5 TWh over-removed" reading is **not** confirmed for this bin. Floors 0 at both plants; no other class moves.

**Benchmark.** ISO class totals byte-identical (both CC) → C1 unchanged. Per-plant split moves (2023: 55641
7.99 → 3.68, 64020 0 → 4.31 TWh), so plant-sync and D-1/D-2/D-4 bench rows change.

**Not measured:** the heat-rate / tranche / emissions re-derives (a measured 64020 rate replacing the fallback;
55641's CF-150 % tranche corrected) — their merit effect needs the re-derive.

**Reading.** A correct rule-14 identity repair that targets **no failing criterion** (C1 CC_REGULAR passes every
year). Worth doing on structure; not a route to any open gate. Cost: re-derive ~5 artifact families + 7 shards.

## 2. D — MISO VLR commitment data

**No rule-admissible measured input exists publicly for 2019–2022.** Searched: IMM SOM 2019–2023 (body +
appendices), IMM "Market Outcomes in MISO South" ERSC decks, MISO RSC South Load Pocket Capacity Advisory (2025),
MTEP15 VLR study (PUCT 46416 CWL-4/5), FERC 2018 tech conference, MISO DA/RT cleared-offer files.

| source | gives | class |
|---|---|---|
| IMM SOM / ERSC decks | VLR RSG $ by South/Midwest, monthly/annual | outcome (forbidden as target) |
| MTEP15 VLR study (~2015) | per-pocket VLR-eligible unit lists (Amite South: Waterford, Little Gypsy; DSG: Ninemile, Michoud; WOTAB: Nelson, Sabine, Cypress; West: Lewis Creek …) | eligibility only, no MW/hours |
| MISO RSC advisory (2025) | confirms Operating Guides set N-1-G-1 VLR MW from load forecast & import capability; only deficits announced, from 2025 | requirement exists, **not published** |
| DA/RT cleared offers | must-run flag, no VLR reason; 2019/2021/2022 files 404 | — |

misoenergy.org HTML and the Market Reports directory returned 403 to the session; a MISO commitment report with a
"Commit Reason" field is referenced in a readers' guide but its file was not found. **Open lead for the owner:**
check from a browser whether that report exists back to 2019.

**Reading.** A VLR floor today would need its MW derived from physics (pocket load vs import capability under
N-1-G-1), i.e. a reduced-network pocket model — the same RO-2 class as C3a 2022, not a data intake. Cell
`scuc_load_pocket_commitment` stays `·`; routed.

## 3. B — MISO-South storm-week gas (C3b 2021)

South Feb 2021, $/MMBtu, capacity-weighted (from `results/calibration/_miso277_storm_print_conventions.json`):

| convention | storm Feb 13–16 | calm Feb | burn-weighted |
|---|---:|---:|---:|
| keeper before D1 (923 monthly × calendar shape) | 32.5 | 20.8 | 25.6 |
| **current keeper (D1 as ruled, HH daily)** | **7.7** | **4.9** | **5.9** |
| HH shape, level burn-normalized to each plant's EIA-923 ("paid level") | 27.4 | 17.4 | 22.3 |

- The South fleet's own EIA-923 Feb-2021 cost burn-weights to **$22.3** — about 4× the HH-based array. HH daily
  peaked at $23.86; the Louisiana fleet evidently bought at Gulf/Texas-linked points that printed far higher.
- EIA state delivered-to-power prices for LA / MS / AR are **withheld (NA)** for Jan–Mar 2021; no Gulf daily hub
  (Katy, Houston Ship Channel, Columbia Gulf) is on disk. Plant EIA-923 is the only measured South cost.
- "Paid level" restores the storm to ~$27 but lifts calm days to ~$17 vs traded ~$3–5 — the miso-269 calm-day
  defect in reverse, and close to the pre-D1 keeper construction.

**Reading.** No admissible zero-DOF construction fixes the storm without breaking calm days. Two honest routes:
buy a daily Gulf-hub print (ICE/NGI — a data purchase), or leave C3b 2021 as a routed extreme-event miss.

## 4. Owner questions

1. **C (Riverside):** build the identity remap + re-derive + 7 shards (structural, no gate expected to flip), or record
   and defer.
2. **B (C3b 2021):** buy/intake a daily Gulf hub for South, build "paid level" for South, or leave as routed miss.
