# FINDING — NWPP-NEXT-19 phase 0 (ZERO LP): the NW price's missing variance is mostly interface/West-load, not Henry Hub daily gas

Object: keeper #20 (`2026-10-01-nwppnext16c-combined-vintage`): a north-zone price flat within each month (NEXT-17 §3,
NEXT-18). Owner card 2026-10-01: "Both, one census" (gas-daily and priced interface together).

Sources (all committed): WEIM hourly ELAP per BA (`data/raw/nwpp-weim/weim_hourly_by_ba.parquet`, 2023-06 → 2025),
Mid-C Peak daily ICE, CAISO hourly RT (`_validation-source/actual_lmp_hourly_CAISO.parquet`), Henry Hub daily, CA composite
citygate daily (NGI "Cal. Comp. Avg." = Malin + PG&E citygate + SoCal border, via EIA), Sumas weekly. Keeper #20 legs
2022–2025 by full SHA (the `claude/nwppnext16c-*` branches are gone from origin; the commits still resolve):
2022 `11bb59fbf0d6a4b8716362f0e8c2f1899a601d11` · 2023 `a54c7b97a9c588564bab90746f2dbbc44fd56838` ·
2024 `91f0bc2928bd348ac48f9d13c6fce7b3c8b460e8` · 2025 `1a41ba5122095ef749302ddf2cb9d67f4fe89dfe`.
C4 benchmark: the keeper's own EIA-930 frame, restored hash-verified (`run_calibration_full.py --restore-shared-inputs`).
Probe: `scripts/probes/_nwppnext19_price_census_phase0.py <leg root>` prints every table. No LP was run.

## 1. Between days (daily means, demeaned within month — what a mean-preserving daily shape can reach)

Share of variance (R²) explained:

| year | BA | SD $/MWh | HH daily | CA citygate daily | Sumas weekly | gas (HH+CA) | CAISO RT | gas + CAISO | **CAISO increment** |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 (Jun–Dec) | BPAT | 20.3 | 0.04 | 0.43 | 0.28 | 0.43 | 0.43 | 0.56 | 0.12 |
| | PACE | 11.8 | 0.03 | 0.36 | 0.07 | 0.36 | 0.78 | 0.80 | **0.43** |
| | IPCO | 14.6 | 0.05 | 0.50 | 0.29 | 0.50 | 0.47 | 0.63 | 0.12 |
| 2024 | BPAT | 82.4 | 0.69 | 0.66 | 0.31 | 0.69 | 0.52 | 0.80 | 0.11 |
| | PACE | 25.4 | 0.54 | 0.58 | 0.28 | 0.59 | 0.61 | 0.76 | 0.17 |
| | IPCO | 42.3 | 0.58 | 0.57 | 0.29 | 0.59 | 0.67 | 0.82 | 0.23 |
| 2025 | BPAT | 9.2 | 0.03 | 0.21 | 0.06 | 0.24 | 0.51 | 0.52 | 0.28 |
| | PACE | 8.4 | 0.05 | 0.28 | 0.03 | 0.31 | 0.72 | 0.73 | **0.42** |
| | IPCO | 9.3 | 0.05 | 0.27 | 0.06 | 0.29 | 0.66 | 0.67 | 0.37 |

What `gas_daily_shape` (the registered HH mechanism) could add, SD of daily price within month at a 7 MMBtu/MWh marginal heat
rate: **$1.2 (2023), $3.7 (2024), $3.4 (2025)** against measured $8–34. Mid-C Peak daily (bilateral, full years): HH R² 0.00 /
0.74 / 0.00 (2023 / 2024 / 2025).

- **Henry Hub daily explains ~0–5 % of the NW between-day variance**, except 2024, where one event (the January cold snap)
  carries it. The HH shape is the wrong gas signal for the NW.
- **A Western gas hub explains far more** (CA composite 0.21–0.66). But no NW hub has a public daily series: Sumas is weekly
  (R² 0.03–0.31), and Malin, Stanfield, Opal have none (`SOURCES_nwpp_gas.md` §3, re-confirmed). Pricing NW gas off the CA
  composite would be a neighbouring-hub substitution (rule 13, `SOURCES_nwpp_gas.md` §4). The CA composite is also NGI-derived,
  so it carries the open licensing question (`docs/data-licensing.md` §5). **Rule 14: no admissible daily NW gas series exists.**
- **The CAISO-coupled part is as large as or larger than the gas part.** Once gas is controlled for, CAISO's daily price still
  adds 0.11–0.43 R². It is largest at PACE (0.42–0.43 in 2023 and 2025). That is West-wide load and interface coupling, which a
  fixed interchange schedule cannot carry.

## 2. Within the day (hourly, demeaned per day)

| | BPAT | PACE | IPCO | PGE | PSEI |
|---|---|---|---|---|---|
| hourly r with CAISO RT, 2023 / 24 / 25 | 0.21 / 0.12 / 0.22 | 0.71 / 0.54 / 0.68 | 0.55 / 0.37 / 0.40 | 0.20 / 0.14 / 0.39 | 0.12 / 0.16 / 0.22 |
| month × hour-of-day mean-profile r | 0.56 / 0.27 / 0.46 | 0.90 / 0.79 / 0.94 | 0.79 / 0.70 / 0.68 | 0.56 / 0.26 / 0.63 | 0.56 / 0.32 / 0.52 |

- **PACE and IPCO carry CAISO's diurnal shape** (profile r 0.68–0.94). The Pacific NW BAs (BPAT, PGE, PSEI) carry much less
  of it (0.26–0.63).
- **BPAT's low r is real, not a clock artifact.** At lags −2…+2 h, lag 0 is the peak or within 0.02 of it in every month except
  August 2023. That month's apparent +2/+3 h lag (BPAT, PGE; not PACE) is carried by the two heat-event days, Aug 15–16 2023
  (BPAT daily SD $92 and $257), not by a clock offset. BPAT's within-day SD (10–16 $/MWh) is close to CAISO's (15–18), but its
  shape correlates weakly. That is hydro-dominated, imbalance-driven noise, not CAISO's solar duck.

## 3. Price-taker bound: keeper offers against the measured WEIM price

Every coal / gas / oil unit runs at `cap_mw` when the measured zonal ELAP price (zone → BA: NW→BPAT, OR→PGE, INLAND→IPCO,
EAST→PACE, SNV→NEVP) clears its offer, and at its own monthly minimum otherwise. The same rule is applied at the model's own
price as a control. No pile dual and no feedback, so this is a bound, not a forecast.

| TWh | coal model | coal @model price | **coal @WEIM** | CT @model | **CT @WEIM** | CC @model | CC @WEIM |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 Jun–Dec | 28.2 | 25.4 | **28.2** | 2.1 | **5.7** | 40.6 | 39.3 |
| 2024 | 36.3 | 27.1 | **29.7** | 5.0 | **12.2** | 70.4 | 67.4 |
| 2025 | 36.6 | 28.9 | **29.3** | 8.5 | **10.6** | 71.8 | 63.9 |

C4 coal fit on the same hours, against the keeper's own EIA-930 frame (floors r ≥ 0.70, NRMSE ≤ 0.30):

| r / NRMSE | model | price-taker @model | **price-taker @WEIM** |
|---|---|---|---|
| 2023 Jun–Dec | 0.555 / 0.294 | 0.564 / 0.230 | **0.666** / 0.284 |
| 2024 | 0.741 / 0.218 | 0.594 / 0.395 | 0.707 / 0.340 |
| 2025 | 0.712 / 0.249 | 0.516 / 0.405 | 0.714 / 0.370 |

- **The measured price lifts the 2023 coal shape by +0.10 r** over the same rule at the model's price. Bridger 2023 follows
  (Jul 328 → 965 GWh; CEMS 1,155). In 2024–2025, the measured price only recovers what the price-taker simplification loses.
  It is not better than the keeper.
- **CT energy is the largest mover: 2.1–2.7× at the measured price.** Any arm that gives NWPP a West-shaped price must be read
  against CT_PEAKER first (rule 20 forced-energy and C2 volume).
- 2023 Jan–May has no WEIM (OASIS retention), so the full-year C4 record (0.669) cannot be bounded this way.

## 4. Rule 19 / rule 13: the interface as it stands

- **Today:** `nwpp_net_interchange` (`data/eia930/envelopes.py`) is the pool's measured EIA-930 total interchange, hourly. It is
  netted into demand in every zone by load share (`data/eia930/demand.py`). Measured net: −6.6 / −3.1 / +5.4 TWh export-positive
  (2023 / 24 / 25), hourly SD 2.2–2.8 GW. A forecast replays the weather-year's schedule.
- **`priced_interchange` is NOT wired for NWPP, and arming it is a silent hazard.** NWPP has no `IMPORT_ZONE` entry
  (`model/interchange/spec.py:35`). `get_interchange_spec` returns empty, yet the backcast runner still drops the measured
  schedule (`run_calibration.py:3369`, `include_interchange=not priced_interchange`). The result is zero interchange with no
  refusal. `reference_price_interface` forces priced interchange on, so it inherits the same hazard. The NWPP seam specs
  (CAISO@MALIN 6,733 MW, WECC_SW@PALOVRDE, WECC_CAN@Mid-C) exist in `spec.py`, but the node wiring (`IMPORT_ZONE`,
  `IMPORT_NODE_LINKS`, `IMPORT_EFORD`) does not.
- **What would hold annual net-interchange energy once priced:** nothing pins it, as rule 13 requires. Quantity responds to
  the neighbour price against NWPP's own marginal cost, bounded by the seam TTCs. The measured annual net (the `interchange`
  fuel row) becomes a score, not an input. The reference price is forward-reproducible in form (HH × heat rate × neighbour
  EIA-930 load shape^k + hurdle; `data/neighbor_price.py`). However, `import_nodes.py` fails closed for every year ≥ 2026 (no
  EIA-930 extract), so the forecast story is open for every reference-price ISO, not only NWPP. Its between-day level rides
  HH, so it inherits §1's HH weakness. Only its within-day neighbour-load shape is new information.

## 5. Reading

- **`gas_daily_shape` (HH) for NWPP: admissible but weak.** It is measured, forward-reproducible and on in 4 ISOs. Its reach
  is ≤ $1–4 of $8–34 between-day SD, and HH explains ~0 of the NW variance outside January 2024. It would not move C4 coal
  2023 on its own. The NW-hub daily shape that would matter has no admissible public series (rule 14 documents the gap; no
  substitution).
- **The interface is the larger structural object** (§1 CAISO increment, §2 PACE/IPCO diurnal shape, §3 +0.10 r on 2023 coal).
  But it is unwired for NWPP. Arming it needs code: NWPP `IMPORT_ZONE` / node links / EFORD, plus a refusal of
  `priced_interchange` for an ISO with no interface spec. That is a solve-affecting PR (matrix rows, tests) before any shard.
- **Expected gain is bounded and uncertain.** The price-taker bound helps 2023 Jun–Dec coal r (+0.10) but not 2024–2025. The
  CT response (2–2.7×) is a regression risk.
- C3 price is still UNSCORED for NWPP. §1–§2 here and NEXT-17 §3 are the ready benchmark if the scorer lane opens it.

## 6. Addendum after owner card 2026-10-02 ("Both: wire + gas shards"): can the registered seams carry the shape?

The node is now wired (default off, see §7). Before any solve, each registered seam's reference price
(`data/neighbor_price.py::neighbor_reference_price` = annual HH × HR × neighbour EIA-930 load shape) was checked against the
measured prices. Probe §6.

**6a. CAISO seam, registered gross-load shape vs a net-load shape** (r of daily-demeaned hours / of within-month daily means):

| year | shape | within-day r vs CAISO RT | vs PACE | vs BPAT | between-day r vs PACE | vs BPAT | SD $/MWh |
|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | gross (registered) | 0.37 | 0.40 | 0.31 | 0.57 | 0.28 | 8.3 |
| | net | 0.56 | 0.38 | 0.15 | 0.55 | 0.24 | 17.4 |
| 2024 | gross (registered) | 0.24 | 0.26 | 0.15 | 0.23 | 0.06 | 7.7 |
| | net | 0.58 | 0.27 | 0.06 | 0.23 | 0.06 | 15.2 |
| 2025 | gross (registered) | **0.08** | 0.14 | 0.17 | 0.60 | 0.45 | 6.1 |
| | net | **0.62** | 0.53 | 0.13 | 0.61 | 0.45 | 14.5 |

- The registered gross-load form loses CAISO's own within-day price shape as solar grows (r 0.37 → 0.08). The net-load form
  holds at 0.56–0.62. CAISO's price is set by its net load (the duck). `load_shape_kind="net"` already exists and is the form
  the CAISO Desert-SW corridor uses. Choosing it is a categorical, physically grounded registry decision, not a fitted value.
  It is still a change to a registered object, so it needs an owner card before any solve.
- Between days, the two forms are equivalent (gas is annual, so only the neighbour's load moves the price).

**6b. Seam level** (annual mean $/MWh, registered form; measured is the WEIM ELAP mean, 2023 Jun–Dec only):

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| CAISO seam | 41.6 | 35.7 | 56.5 | 84.2 | 49.8 | 40.0 | 37.9 |
| WECC_SW seam | 37.0 | 29.3 | 56.4 | 92.6 | 48.0 | 33.3 | 32.4 |
| **WECC_CAN seam** | 64.7 | 50.2 | 101.4 | **169.7** | **87.2** | 61.5 | 46.3 |
| measured BPAT / PACE / IPCO | — | — | — | — | 48.7 / 39.1 / 43.7 | 45.0 / 31.1 / 35.8 | 34.4 / 28.5 / 31.2 |

- **The WECC_CAN seam sits $12–38 above BPAT in every measured year, and at $170 in 2022.** Its anchor is the Mid-C **Peak**
  daily index. It is peak-only, which NWPP-20 declared as "an upward-biased PROXY". The HR it implies (13.9–37.1; flat
  fallback 27.25 for 2019–2022) turns that bias into a standing export bid of up to 3,475 MW. Armed as registered, NWPP
  would export to Canada in almost every hour. That is a mechanism reaching a number it should not (rule 1).
- CAISO and WECC_SW sit within a few dollars of the measured NW means. They carry no comparable level problem.

**Reading.** The wiring is done, and it is inert by default. **The priced-interface arm is NOT solve-ready as registered.**
Two registered objects need an owner ruling first:
1. the CAISO seam's load-shape kind (gross → net);
2. the WECC_CAN anchor (the peak-only Mid-C proxy and its HR). No admissible off-peak or all-hours Canadian or Mid-C series
   is on disk.

Solving it now would test the WECC_CAN bias, not the interface.

## 7. What landed (code, default-off, keeper byte-identical)

- `IMPORT_ZONE["NWPP"] = "NWPP_external"` and `IMPORT_EFORD["NWPP"] = 0.0`.
- `IMPORT_NODE_LINKS["NWPP"] = seam_derived_border_links("NWPP")`: each border zone is rated at the sum of the registered
  seam limits landing in it, so no new number enters. NW 16,257 · OR 12,782 · SNV 12,782 · INLAND 9,524 · EAST 6,049 MW.
- `require_priced_interchange_rows`: the backcast refuses a priced-interchange build with no rows. Before this, it silently
  zeroed interchange for any ISO without a priced interface (§4).
- NWPP keepers do not arm `priced_interchange` or `reference_price_interface`, so the keeper path is unchanged. CAISO, MISO and
  PJM build rows and pass the refusal unchanged.
