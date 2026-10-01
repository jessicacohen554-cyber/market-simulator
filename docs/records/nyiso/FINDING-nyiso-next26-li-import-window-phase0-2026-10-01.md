# FINDING — NYISO-NEXT-26 phase 0: Long Island is under-priced because its import security cap is armed in 8 of 24 hours — 2026-10-01

Zero LP. Keeper `2026-10-01-nyisonext21-astoria-hr-span` (+ the stamped 2021 run). Probes
`scripts/probes/nyisonext26_li_gap.py`, `scripts/probes/nyisonext26_li_dlc.py`; records
`results/phase0/nyiso/_nyisonext26_li_gap.json`, `_nyisonext26_li_dlc.json`.

## 1. The Zone K miss is the K-over-J spread, and the spread is congestion

`model_K − DA_K = (model_J − DA_J) + [(model_K − model_J) − (DA_K − DA_J)]`, annual $/MWh:

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| Zone K error vs DA (%) | −16.1 | −11.3 | −13.9 | −12.0 | −12.8 |
| Zone K error ($/MWh) | −8.7 | −10.8 | −5.7 | −5.2 | −8.8 |
| … NYC level error | +0.7 | −1.3 | +0.3 | −1.6 | −6.0 |
| … K-over-J spread error | −9.4 | −9.5 | −5.9 | −3.6 | −2.8 |
| DA K−J spread | 11.5 | 10.8 | 6.8 | 4.0 | 3.5 |
| … of which congestion | 11.1 | 10.1 | 6.3 | 3.6 | 3.1 |
| model K−J spread | 2.2 | 1.3 | 0.9 | 0.4 | 0.6 |

The spread carries the miss in 2021–2024. In 2025 the NYC level dominates (the NEXT-25 object).
NYISO convention verified on the archive: `LBMP = energy + loss − congestion` (energy identical
across zones within $0.02 every hour).

## 2. The congestion is the Zone-K import security set

Hourly DA K-over-J congestion regressed on NYISO's DAM limiting-constraint shadow prices
(`fetch_nyiso_zonal_lmp.py --kind dlc`, new; facilities binding ≥ 40 h):

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| R² | 0.97 | 0.94 | 0.94 | 0.93 | 0.82 |
| Zone-K import set ($/MWh) | 9.7 | 9.3 | 3.9 | 2.1 | 2.7 |
| LI-internal facilities | 0.7 | 0.7 | 1.9 | 1.8 | 0.8 |
| other | 0.5 | −0.1 | 0.4 | −0.4 | −0.2 |

Import set = Y50 Dunwoodie–Shore Road (mostly post-contingency for loss of Y49), Y49 Sprain
Brook–East Garden City, the ConEd–LIPA interface, the Shore Road 345/138 transformer; implied shift
factors 0.75–1.05. That is the interface the TSL report defines and the armed cap represents.

## 3. That set binds all year; the armed cap binds only HB14-21

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| DAM hours the AC import set binds | 5,782 | 5,432 | 5,227 | 3,148 | 1,680 |
| share of those hours outside HB14-21 | 61 % | 60 % | 62 % | 64 % | 58 % |
| share of shadow cost outside HB14-21 | 49 % | 44 % | 52 % | 47 % | 48 % |
| winter binding hours | 1,958 | 1,322 | 1,505 | 778 | 1,202 |

Outside HB14-21 the `NYC>Long_Island` link reads the 1,650 MW Gold-Book seed (`iso_configs.py`,
"Tier 3 — verify"). The keeper's own flows:

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| model hours net import > 940 MW | 2,099 | 1,246 | 1,333 | 1,056 | 1,016 |
| … outside HB14-21 | 1,977 | 1,188 | 1,251 | 1,019 | 970 |
| measured implied net import > 940 MW (h) | 351 | 340 | 133 | 49 | 171 |
| model link dual ≠ 0 (share of h) | 15 % | 10 % | 13 % | 19 % | 24 % |
| DA K−J congestion > $5 (share of h) | 55 % | 48 % | 38 % | 20 % | 20 % |

Measured implied net import = zone K load − CAMPD gross of the model's LI plants − P-32 LI seam
schedules (Neptune, CSC, 1385). Its seasonal p99 is 670–1,190 MW in every season-year; the model's
reaches 1,650. Gross CAMPD understates net import by ~3–5 % of LI generation; non-CAMPD LI supply
(waste-to-energy, solar, South Fork wind) overstates it. The two roughly offset; neither is close to 700 MW.

## 4. The model imports what LI should generate

Annual mean MW, keeper vs measured:

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| LI fossil, model | 874 | 892 | 635 | 891 | 1,017 |
| LI fossil, CAMPD gross | 1,256 | 1,110 | 1,029 | 1,069 | 1,200 |
| net AC import, model | 744 | 586 | 669 | 494 | 422 |
| net AC import, measured implied | 439 | 436 | 340 | 384 | 302 |

So Long Island is supplied ~150–400 MW too much by import and too little by its own fleet. The
import is priced at NYC, so K clears near J.

## 5. What an all-hours cap would do (static bracket, no LP)

The excess over 940 MW is met by the next LI unit in the keeper's own merit order. There is no
redispatch elsewhere, so this is an upper bound. LI headroom covers the excess in every hour.

| Zone K error vs DA | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| keeper | −16.1 | −11.3 | −13.9 | −12.0 | −12.8 |
| static estimate | −9.3 | −8.9 | −11.3 | −9.4 | −11.0 |

Most of the gain is in winter (2021 −13.5 → +4.6 %, 2025 −17.6 → −14.6 %). Summer barely moves
because the window already covers it.

## 6. What this does not close

- **Summer.** Summer K is still −13 to −28 %. The measured set binds at modest net imports there
  (p50 320–520 MW in binding hours). That is Y49/Y50 loading, which depends on the PAR schedules and
  cable outages, and one net link cannot represent it. **Candidate ledger item, not a lever.**
- **LI-internal pockets** (Elwood–Pulaski 69 kV, the Valley Stream 138 kV group): $0.7–1.9/MWh.
  These are below the model's zonal grain.
- **2025** is mostly the NYC level (NEXT-25 arm A).

**Prior verdicts.** nyiso-130/143 put the published 940 MW into the HB14-21 window only. The
off-window 1,650 MW was never tested (PREREG-nyiso130 §3: "off-window bound (untouched)"). So this
is a new cell, not a re-test.

**Caveat.** The 940 MW is computed at summer design conditions (Y50 @ LTE 964 MVA). No winter rating
is in the corpus, and a winter LTE would be at least as high. Measured winter implied net import p99
is 804–1,025 MW, which fits a ceiling near 940–1,000 MW.

## 7. Lever

The new flag `nyiso_li_tsl_all_hours` (default off, zero DOF) applies the same published cap in all
hours. Its basis is rule 17 (the window follows the constraint's measured driver) and rule 14 (a
published limit replaces an unverified seed). PRECOMMIT:
`docs/records/nyiso/PRECOMMIT-nyiso-next26-li-tsl-all-hours-2026-10-01.md`.
