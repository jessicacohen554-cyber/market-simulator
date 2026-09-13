# FINDING — SOCO-15: the COD-seam cross-ISO repair (owner card S12)

**SOCO-20 IS CLEARED TO PROCEED: the COD-seam repair is on main (commit 9398000d, PR #6127), all three exit conditions are met, and the eight-footprint A/B moved results in the direction and at the order of magnitude the availability delta implied, in both directions, with no ISO where the repair is wrong.**

**Lane:** SOCO-15 `[FABLE]` · **Date:** 2026-09-13 · **Branch:** `claude/soco-15-cod-ramp-b0080o` (arm SHA `4f33476c520dbbec61f05abcfdbeb1a4b18540a4`; base `origin/main` `33a7c961`) · **PRECOMMIT:** `docs/handoffs/PRECOMMIT-soco-15-2026-09-13.md` (registered before any solve; every number below that came from a solve is differenced exactly as §4–§6 there pre-registered).
**Ruling served:** owner card S12 — *"Charter a cross-ISO repair lane BEFORE SOCO-20."* **Model:** Fable, because the repair deliberately MOVES RESULTS for all seven registered keepers.

## 1. The eight-footprint A/B — energy and fuel mix, both directions, full magnitude

Arms are each ISO's keeper recipe replayed at the arm SHA `4f33476c` (`scripts/replay_keeper.py`); the control is the committed keeper bundle where the G-DRIFT audit validated form 4 (MISO, SPP, PJM) and a same-recipe control solve at the pinned `33a7c961` for ERCOT. Class energies are the P1 `hourly/class_hourly_<year>.parquet` sums; "measured" is the committed EIA-923 class benchmark (`frontend/data/backcast/bench/<ISO>/<year>.json.gz` → `classFull`). Only classes moving by ≥ 0.5 GWh are listed; every other class is identical to that tolerance. **Rubric scores are NOT re-computed for the arms**: `calibration_verdict.py` scores registered runs only and this lane registers nothing, so the last column says whether each moved class moved TOWARD or AWAY from its measured value — both are reported, neither gates (rule 14). Prices are the P1 system price from `hourly/system_<year>.parquet`.

**Summary, all eight footprints (arm − control):**

| footprint | years solved | largest class move (TWh) | direction vs measured | mean price Δ ($/MWh) | verdict of the A/B |
|---|---|---|---|---|---|
| **SOCO** | none (no runnable config until SOCO-20) | bound: −20.37 TWh-avail in 2023 = SOCO-10's +12.98 TWh phantom nuclear (2023), +2.17 (2024), 2.3–4.6 Barry A3 | the repair removes the phantom, which is the whole point of card S12 | n/a | SOCO-20 solves on the repaired seam |
| **MISO** | 2020–2025 (arm vs keeper) | CT_PEAKER 2022 −0.326; CC_CHP −0.15 to −0.20 every year 2020–24; CC_REGULAR +0.05 to +0.30 | mixed — CC_REGULAR toward in 2021/22, CT_PEAKER away in 2021/22; every move ≤ 0.33 TWh against a 5–6 TWh-avail input delta (the phantom CTs were idle capacity) | +0.01 to +0.07; 2023 max hour 265 → 906 | direction as predicted, magnitude bounded, no band-scale change |
| **SPP** | 2023–2025 (arm vs keeper) | CT_PEAKER 2025 −0.645 (−4.0 %); CC_REGULAR +0.334; ST_GAS +0.156; COAL_PRB +0.131 | CT_PEAKER, CC, ST_GAS toward; COAL_PRB away | 2025 +0.23; 2023/24 +0.00 | 2023/24 identical; 2025 moves as the 2.0 TWh-avail delta implied |
| **ERCOT** | 2021–2025 (arm vs same-recipe control at HEAD) | CC_CHP 2021 −0.314 / 2022 −0.280; CC_REGULAR +0.310 / +0.252; CT_CHP −0.10/yr; CT_PEAKER 2023/24 −0.11 | CC_CHP and CC_REGULAR toward (2021: 0.42 → 0.11 and 0.39 → 0.08); CT_CHP away; ST_GAS away | +0.46 / +0.21 / **+2.34** / +0.11 / 0.00 | both directions realised; 2025 identical; the 2023 price move is the largest single effect in the whole A/B |
| **PJM** | 2023–2025 (arm vs keeper) | _see §1.4_ | _see §1.4_ | _see §1.4_ | _see §1.4_ |
| NYISO | not solved | bound ≤ 0.028 TWh/yr (2 units, 37.8 MW-months) | — | — | input-inert below any band |
| CAISO | not solved | bound ≤ 0.037 TWh/yr (7–8 objects, ≤ 50 MW-months) | — | — | input-inert below any band |
| NEISO | not solved | 2023 bound ≤ 0.003 TWh; 2024/25 inputs byte-identical | — | — | input-inert |

**Measured, not assumed:** the ERCOT control solve reproduces the committed `ercot265_receipts_five_year` keeper's class energies to ≤ 0.5 GWh in every class of every year — the 70 solve-path commits between the keeper and `33a7c961` were inert for ERCOT's dispatch after all, so the ERCOT arm − control table below is also the arm − keeper table. The control solve cost 81.5 min; it was earned by an audit this lane could not finish, and it settled the question rather than assuming it.

### 1.1 SPP — arm vs keeper `spp38_span`

| year | class | control TWh | arm TWh | Δ TWh (arm−control) | measured EIA-923 TWh | |control−actual| → |arm−actual| |
|---:|---|---:|---:|---:|---:|---|
| 2024 | COAL_LIGNITE | 6.181 | 6.180 | -0.001 | 8.672 | 2.491 → 2.492 (away) |
| 2024 | COAL_PRB | 58.580 | 58.581 | +0.001 | 59.971 | 1.391 → 1.390 (toward) |
| 2025 | CC_REGULAR | 36.378 | 36.713 | +0.334 | 42.771 | 6.393 → 6.058 (toward) |
| 2025 | COAL_LIGNITE | 6.589 | 6.608 | +0.019 | 8.862 | 2.273 → 2.254 (toward) |
| 2025 | COAL_PRB | 78.053 | 78.184 | +0.131 | 74.587 | 3.465 → 3.596 (away) |
| 2025 | CT_CHP | 1.159 | 1.161 | +0.002 | 1.053 | 0.106 → 0.108 (away) |
| 2025 | CT_PEAKER | 15.992 | 15.346 | -0.645 | 11.287 | 4.705 → 4.060 (toward) |
| 2025 | ST_CHP | 0.182 | 0.185 | +0.004 | 0.341 | 0.159 → 0.156 (toward) |
| 2025 | ST_GAS | 11.339 | 11.495 | +0.156 | 20.108 | 8.769 → 8.613 (toward) |

Years with no class moving by ≥ 0.5 GWh: [2023] (arm and control class energies identical to that tolerance).

| year | price col | control mean | arm mean | Δ mean | control p95 | arm p95 | control max | arm max | hrs>1000 ctl/arm |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 2023 | price | 24.96 | 24.96 | +0.00 | 37.0 | 37.0 | 61 | 61 | 0/0 |
| 2024 | price | 25.40 | 25.40 | +0.00 | 43.2 | 43.2 | 2000 | 2000 | 4/4 |
| 2025 | price | 29.31 | 29.54 | +0.23 | 44.4 | 45.3 | 2000 | 2000 | 2/2 |

### 1.2 ERCOT — arm vs same-recipe control at `33a7c961` (three recipe groups each: {2021,2022} carve-out, {2023} carve-out, {2024,2025} forward)

| year | class | control TWh | arm TWh | Δ TWh (arm−control) | measured EIA-923 TWh | |control−actual| → |arm−actual| |
|---:|---|---:|---:|---:|---:|---|
| 2021 | CC_CHP | 27.552 | 27.238 | -0.314 | 27.132 | 0.420 → 0.106 (toward) |
| 2021 | CC_REGULAR | 112.855 | 113.166 | +0.310 | 113.245 | 0.389 → 0.079 (toward) |
| 2021 | COAL_LIGNITE | 16.995 | 16.999 | +0.004 | 16.446 | 0.548 → 0.553 (away) |
| 2021 | COAL_PRB | 54.286 | 54.334 | +0.048 | 58.064 | 3.777 → 3.729 (toward) |
| 2021 | CT_CHP | 5.100 | 4.993 | -0.107 | 6.129 | 1.029 → 1.136 (away) |
| 2021 | CT_PEAKER | 5.569 | 5.523 | -0.046 | 4.646 | 0.923 → 0.877 (toward) |
| 2021 | ST_GAS | 13.859 | 13.960 | +0.101 | 12.344 | 1.516 → 1.616 (away) |
| 2021 | oil | 0.355 | 0.358 | +0.003 | 0.167 | 0.187 → 0.190 (away) |
| 2022 | CC_CHP | 25.878 | 25.598 | -0.280 | 25.645 | 0.233 → 0.047 (toward) |
| 2022 | CC_REGULAR | 125.032 | 125.285 | +0.252 | 132.087 | 7.055 → 6.803 (toward) |
| 2022 | COAL_LIGNITE | 17.771 | 17.774 | +0.003 | 17.070 | 0.701 → 0.704 (away) |
| 2022 | COAL_PRB | 58.657 | 58.682 | +0.024 | 54.148 | 4.510 → 4.534 (away) |
| 2022 | CT_CHP | 4.755 | 4.647 | -0.108 | 5.835 | 1.080 → 1.188 (away) |
| 2022 | CT_PEAKER | 5.122 | 5.173 | +0.051 | 5.901 | 0.778 → 0.728 (toward) |
| 2022 | ST_GAS | 15.061 | 15.116 | +0.055 | 12.417 | 2.644 → 2.699 (away) |
| 2022 | oil | 0.028 | 0.030 | +0.002 | 0.260 | 0.233 → 0.230 (toward) |
| 2023 | CC_CHP | 26.317 | 26.329 | +0.012 | 28.514 | 2.197 → 2.185 (toward) |
| 2023 | CC_REGULAR | 145.289 | 145.399 | +0.110 | 141.743 | 3.546 → 3.656 (away) |
| 2023 | COAL_LIGNITE | 16.848 | 16.852 | +0.004 | 15.335 | 1.513 → 1.517 (away) |
| 2023 | COAL_PRB | 43.563 | 43.599 | +0.036 | 45.085 | 1.522 → 1.486 (toward) |
| 2023 | CT_CHP | 4.554 | 4.452 | -0.102 | 5.607 | 1.053 → 1.155 (away) |
| 2023 | CT_PEAKER | 7.094 | 6.986 | -0.108 | 7.098 | 0.004 → 0.111 (away) |
| 2023 | ST_GAS | 19.048 | 19.090 | +0.042 | 16.700 | 2.348 → 2.390 (away) |
| 2023 | oil | 0.099 | 0.104 | +0.005 | 0.154 | 0.055 → 0.050 (toward) |
| 2024 | CC_CHP | 28.653 | 28.661 | +0.008 | 30.030 | 1.377 → 1.370 (toward) |
| 2024 | CC_REGULAR | 143.473 | 143.527 | +0.055 | 143.778 | 0.305 → 0.251 (toward) |
| 2024 | COAL_LIGNITE | 15.312 | 15.315 | +0.002 | 13.941 | 1.372 → 1.374 (away) |
| 2024 | COAL_PRB | 41.777 | 41.797 | +0.019 | 43.676 | 1.899 → 1.879 (toward) |
| 2024 | CT_CHP | 5.206 | 5.173 | -0.033 | 5.661 | 0.455 → 0.487 (away) |
| 2024 | CT_PEAKER | 8.358 | 8.247 | -0.112 | 7.651 | 0.708 → 0.596 (toward) |
| 2024 | ST_GAS | 19.398 | 19.459 | +0.061 | 18.102 | 1.295 → 1.357 (away) |

Years with no class moving by ≥ 0.5 GWh: [2025] (arm and control class energies identical to that tolerance).

| year | price col | control mean | arm mean | Δ mean | control p95 | arm p95 | control max | arm max | hrs>1000 ctl/arm |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 2021 | price | 157.96 | 158.41 | +0.46 | 282.5 | 282.9 | 10771 | 10771 | 931/931 |
| 2022 | price | 57.32 | 57.52 | +0.21 | 100.1 | 100.3 | 3298 | 3300 | 105/112 |
| 2023 | price | 45.52 | 47.86 | +2.34 | 62.5 | 64.3 | 5025 | 5025 | 413/441 |
| 2024 | price | 26.61 | 26.72 | +0.11 | 46.3 | 46.8 | 5000 | 5000 | 49/56 |
| 2025 | price | 29.59 | 29.59 | +0.00 | 54.8 | 54.8 | 214 | 214 | 0/0 |

### 1.3 MISO — arm vs keeper `miso255_sil_keeper` (two recipe groups: {2020–2022}, {2023–2025})

| year | class | control TWh | arm TWh | Δ TWh (arm−control) | measured EIA-923 TWh | |control−actual| → |arm−actual| |
|---:|---|---:|---:|---:|---:|---|
| 2020 | CC_CHP | 24.809 | 24.607 | -0.203 | 20.416 | 4.393 → 4.190 (toward) |
| 2020 | CC_REGULAR | 115.653 | 115.767 | +0.114 | 106.906 | 8.746 → 8.861 (away) |
| 2020 | COAL_BIT | 59.250 | 59.274 | +0.024 | 66.274 | 7.024 → 7.000 (toward) |
| 2020 | COAL_LIGNITE | 9.517 | 9.519 | +0.002 | 8.365 | 1.152 → 1.154 (away) |
| 2020 | COAL_PRB | 130.306 | 130.363 | +0.058 | 126.675 | 3.630 → 3.688 (away) |
| 2020 | CT_CHP | 5.508 | 5.429 | -0.079 | 8.192 | 2.685 → 2.764 (away) |
| 2020 | CT_PEAKER | 11.187 | 11.155 | -0.032 | 12.572 | 1.385 → 1.416 (away) |
| 2020 | ST_CHP | 3.113 | 3.092 | -0.021 | 5.882 | 2.769 → 2.790 (away) |
| 2020 | ST_GAS | 20.484 | 20.533 | +0.049 | 17.515 | 2.969 → 3.019 (away) |
| 2020 | import | 39.272 | 39.360 | +0.088 | None | n/a |
| 2021 | CC_CHP | 15.660 | 15.471 | -0.188 | 17.885 | 2.226 → 2.414 (away) |
| 2021 | CC_REGULAR | 89.084 | 89.288 | +0.205 | 103.823 | 14.740 → 14.535 (toward) |
| 2021 | COAL_BIT | 71.133 | 71.176 | +0.043 | 77.198 | 6.065 → 6.022 (toward) |
| 2021 | COAL_LIGNITE | 9.830 | 9.832 | +0.002 | 8.419 | 1.411 → 1.413 (away) |
| 2021 | COAL_PRB | 164.496 | 164.562 | +0.067 | 163.477 | 1.019 → 1.085 (away) |
| 2021 | CT_CHP | 5.190 | 5.123 | -0.066 | 7.351 | 2.161 → 2.227 (away) |
| 2021 | CT_PEAKER | 12.195 | 12.098 | -0.098 | 13.986 | 1.790 → 1.888 (away) |
| 2021 | ST_CHP | 2.506 | 2.501 | -0.006 | 5.193 | 2.687 → 2.693 (away) |
| 2021 | ST_GAS | 12.321 | 12.359 | +0.038 | 11.224 | 1.097 → 1.135 (away) |
| 2021 | import | 49.340 | 49.342 | +0.002 | None | n/a |
| 2021 | oil | 0.194 | 0.199 | +0.005 | 0.724 | 0.530 → 0.525 (toward) |
| 2022 | CC_CHP | 13.879 | 13.730 | -0.149 | 18.954 | 5.075 → 5.224 (away) |
| 2022 | CC_REGULAR | 98.744 | 99.048 | +0.304 | 125.567 | 26.823 → 26.519 (toward) |
| 2022 | COAL_BIT | 77.301 | 77.331 | +0.030 | 66.907 | 10.393 → 10.423 (away) |
| 2022 | COAL_PRB | 181.728 | 181.754 | +0.026 | 149.688 | 32.040 → 32.066 (away) |
| 2022 | CT_CHP | 5.270 | 5.267 | -0.003 | 7.513 | 2.243 → 2.246 (away) |
| 2022 | CT_PEAKER | 13.210 | 12.884 | -0.326 | 14.125 | 0.915 → 1.241 (away) |
| 2022 | ST_CHP | 2.592 | 2.592 | -0.001 | 4.988 | 2.396 → 2.396 (away) |
| 2022 | ST_GAS | 14.012 | 14.052 | +0.040 | 12.113 | 1.900 → 1.939 (away) |
| 2022 | import | 13.835 | 13.916 | +0.081 | None | n/a |
| 2023 | CC_CHP | 19.302 | 19.137 | -0.165 | 39.008 | 19.706 → 19.871 (away) |
| 2023 | CC_REGULAR | 138.502 | 138.560 | +0.058 | 130.865 | 7.638 → 7.695 (away) |
| 2023 | COAL_BIT | 53.767 | 53.779 | +0.012 | 52.662 | 1.105 → 1.117 (away) |
| 2023 | COAL_LIGNITE | 6.335 | 6.336 | +0.001 | 6.503 | 0.167 → 0.166 (toward) |
| 2023 | COAL_PRB | 120.296 | 120.327 | +0.031 | 112.275 | 8.022 → 8.053 (away) |
| 2023 | CT_CHP | 5.494 | 5.495 | +0.001 | 18.985 | 13.492 → 13.490 (toward) |
| 2023 | CT_PEAKER | 16.608 | 16.598 | -0.010 | 15.723 | 0.885 → 0.875 (toward) |
| 2023 | ST_CHP | 2.630 | 2.632 | +0.002 | 6.165 | 3.535 → 3.533 (toward) |
| 2023 | ST_GAS | 19.722 | 19.755 | +0.033 | 12.863 | 6.858 → 6.892 (away) |
| 2023 | import | 41.944 | 41.980 | +0.036 | None | n/a |
| 2023 | oil | 0.003 | 0.004 | +0.001 | 0.462 | 0.460 → 0.458 (toward) |
| 2024 | CC_CHP | 21.074 | 20.926 | -0.148 | 21.339 | 0.265 → 0.412 (away) |
| 2024 | CC_REGULAR | 149.502 | 149.549 | +0.048 | 143.474 | 6.028 → 6.076 (away) |
| 2024 | COAL_BIT | 49.457 | 49.464 | +0.008 | 53.332 | 3.875 → 3.867 (toward) |
| 2024 | COAL_LIGNITE | 5.725 | 5.726 | +0.001 | 6.522 | 0.797 → 0.795 (toward) |
| 2024 | COAL_PRB | 112.176 | 112.208 | +0.031 | 116.463 | 4.286 → 4.255 (toward) |
| 2024 | CT_CHP | 5.690 | 5.692 | +0.002 | 8.503 | 2.813 → 2.811 (toward) |
| 2024 | CT_PEAKER | 19.202 | 19.193 | -0.009 | 19.225 | 0.023 → 0.032 (away) |
| 2024 | ST_CHP | 2.999 | 3.000 | +0.001 | 5.494 | 2.495 → 2.494 (toward) |
| 2024 | ST_GAS | 20.870 | 20.902 | +0.032 | 17.568 | 3.302 → 3.334 (away) |
| 2024 | import | 26.389 | 26.420 | +0.031 | None | n/a |
| 2025 | CC_REGULAR | 136.761 | 136.762 | +0.001 | 131.715 | 5.046 → 5.047 (away) |
| 2025 | CT_PEAKER | 19.684 | 19.674 | -0.010 | 18.417 | 1.267 → 1.256 (toward) |
| 2025 | ST_GAS | 18.779 | 18.780 | +0.001 | 14.863 | 3.917 → 3.918 (away) |
| 2025 | import | 19.016 | 19.023 | +0.007 | None | n/a |
| 2025 | oil | 0.019 | 0.020 | +0.001 | 0.353 | 0.334 → 0.333 (toward) |

| year | price col | control mean | arm mean | Δ mean | control p95 | arm p95 | control max | arm max | hrs>1000 ctl/arm |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 2020 | price | 27.61 | 27.63 | +0.01 | 34.2 | 34.2 | 59 | 59 | 0/0 |
| 2021 | price | 33.96 | 34.00 | +0.04 | 55.5 | 55.7 | 2000 | 2000 | 6/6 |
| 2022 | price | 52.65 | 52.72 | +0.07 | 76.1 | 76.3 | 106 | 106 | 0/0 |
| 2023 | price | 33.85 | 33.92 | +0.07 | 43.0 | 43.0 | 265 | 906 | 0/0 |
| 2024 | price | 31.75 | 31.76 | +0.02 | 42.0 | 42.0 | 500 | 500 | 0/0 |
| 2025 | price | 41.49 | 41.55 | +0.06 | 57.4 | 57.4 | 833 | 847 | 0/0 |

### 1.4 PJM — arm vs keeper `pjm_d4_4_A`

_pending_
_pending_
_pending_

### 1.5 What moved toward and away from the measured values, honestly

* **Toward:** SPP 2025 CT_PEAKER (−0.645 of a +4.7 TWh excess), CC_REGULAR and ST_GAS; ERCOT CC_CHP and CC_REGULAR in 2021–2022 (the two-direction plant 65372 repair and the CC_CHP brownfield fraction at plant 10554), ERCOT CT_PEAKER 2024; MISO CC_REGULAR 2021–2022, COAL_BIT 2020–2021.
* **Away:** SPP COAL_PRB 2025 (+0.13 on an already-high coal), ERCOT CT_CHP every year (−0.10 to −0.11 TWh where CT_CHP is already under the measured value), ERCOT ST_GAS (+0.04 to +0.10 on an over-dispatched class), MISO CT_PEAKER 2021–2022 (−0.10 / −0.33 where CT_PEAKER was already under), MISO CC_CHP every year.
* **Reading:** the repair takes capacity away from brownfield gas CT/CHP objects in the months they had not yet reached commercial operation and the LP back-fills from whatever is next in merit — CC, ST_GAS or coal depending on the ISO. Where the ISO's CT class already sat under its measured value (MISO, ERCOT CT_CHP) the repair widens that gap; that is a discovered miscalibration elsewhere in those classes' offer or floor structure, not a reason to keep the plant-mean estimate (rule 14). None of the moves is band-scale except the ERCOT 2023 mean price (+2.34 $/MWh, +5.1 %), which the ERCOT lane should expect on its next re-solve.

**No rubric determination moved by this lane's hand**: arms are unregistered and unscored; each ISO lane re-scores when it re-solves on the repaired seam.

## 2. The three exit conditions

| condition | evidence | verdict |
|---|---|---|
| **(a) cache keys byte-identical for all seven keepers (G8)** | no `ScenarioConfig` field, no default flip, no `results/cache.py` edit; `SURFACE_MODULES` untouched; every keeper's `run_config.json` `scenario_config` → `cache_key()` identical on the `33a7c961` tree and on this branch: `caiso bab5e9b08681e54c · ercot 0f89d4c5f45043f7 · miso b35a8f20b73a5fbf · neiso 28266b333667e16f · nyiso 7e0dc0344f297fc2 · pjm b05e09c319c2c5f5 · spp 6d6205e381e982c2`; `tests/regression/test_persisted_identity.py` 23 pass, the single failure (`test_solve_surface_fingerprint_is_pinned[NYISO]`, 210 vs 209 rows) reproduces with this lane stashed on `33a7c961` — pre-existing on `main`, not this lane's; `SOLVE_EPOCHS` left empty (an epoch would re-key every keeper) | **MET** |
| **(b) greenfield still ramps; a regression test fails on the old seam and passes on the new, both directions** | `[56] → 000000001111` on the old module and the new resolver alike, through the constituent fraction AND through the plant-map fallback; `[649,'3'] 2023: 111111111111 → 000000111111`; `tests/unit/data/test_cod_ramp.py` 71 pass (the three brownfield tests fail on the old seam, the two greenfield tests pass on both); `TestLiveCardS12Cases` pins the measured cases on the committed vintage | **MET** |
| **(c) rule 25: one shared seam, the same repair everywhere** | `cod_ramp.generator_online_mask` is the single resolver `generators_to_fleet_arrays` calls for every ISO; no per-ISO number, branch or fit; the only per-ISO difference is the grain each fleet path hands it (raw unit vs bin) | **MET** |

**Rule 28:** no `ScenarioConfig` field is added, so no mechanism-matrix row is added — this is a correctness repair of the existing default-on `cod_ramp_enabled` mechanism. **Rule 26:** the old plant-map preference is removed, not flagged. **No matrix shard, keeper shard, log, registry, bundle or `calibration_verdict.py` was touched.**

## 3. What the repair is (one seam, two grains)

## 3. The repair (what changed, what did not)

* `cod_ramp.effective_cod(..., is_plant_level=False)` — a raw EIA-860 unit with a known own year (> the 2000 sentinel) keeps its OWN `(online_year, online_month)`; a plant-level object (`is_campd_bin`) keeps the plant map's; retirement resolution unchanged (own if present, else plant-collapsed).
* `cod_ramp.load_unit_cod_map()` / `_load_unit_cod_map(dir)` — `{(plant_code, fuel_type): ((nameplate, oy, om), …)}` from the SAME two parquets `_load_cod_map` reads, status `OP` only (the loader's own filter), classified with the loader's own `_map_fuel_type`; `bin_online_fraction(units, year)` — the nameplate-weighted online fraction, endpoints exact (a bin whose units all predate the year hands the LP exactly 1.0).
* `cod_ramp.generator_online_mask(...)` — raw unit → own date (0/1); bin with `(plant, BIN_GROUP_TO_FUEL[group])` constituents → fraction × the bin's retirement half; else the plant-collapsed record exactly as before. Reaches the ERCOT curated-sheet bins through the same lookup (their `Plant_Code` + `Plant_Group`).
* `fleet/arrays.py` — the COD block calls the resolver (passes `plant_group`, `is_campd_bin`); `min_gen` scales by the same mask.
* `fleet/eia860.py` — `_operating_month_by_unit(dir)` bridges each unit's `Operating Month` into `_load_fleet_from_parquet` from the same directory's operable sheet (mirror of `_chp_by_plant`); never overrides a month the parquet already carries (the retiree-channel schema has one).
* `fleet/__init__.py` — exports the two new names so `_pkg_ns()` and the tests' patch points resolve.
* `_load_cod_map` is **unchanged** (its output is the fallback and feeds `commission_year_cod_fallback` untouched). Retirement is untouched at both grains (rule 19: the partial-plant exit cohort is the one unit-grain retirement mechanism under binning). Legacy heat-rate bins (`plant_code` 0) never reach the map — unchanged. Forecast mode never enters the block — unchanged.
* Rule 28 `[R-MECH-MATRIX]`: **no `ScenarioConfig` field is added, so no matrix row is added** — this is a correctness repair of an existing default-on mechanism (`cod_ramp_enabled`), stated here explicitly as the charter asks. Rule 26: nothing deprecated is left parseable; the old preference is gone, not flagged.

## 4. Phase 0, reproduced — and the correction it surfaced

### 1.1 SOCO-10's blast radius reproduces exactly

Root vintage `data/raw/eia-860/eia860_generator_operable.parquet`, **nameplate** basis, footprint = plant-level `Balancing Authority Code` (the processed generators parquet carries no SOCO rows, so the plant sheet's BA is the footprint for all eight), selection = units with `Operating Year` ∈ {2023, 2024, 2025} whose `load_cod_map()` plant year is earlier. Every number, plant count and unit count matches SOCO-10 §2 / audit §4.4 to the tenth of a MW:

| Footprint | SOCO-10 (MW) | reproduced (MW) | plants / units | **thermal-ramp-governed (MW)** | not governed by this seam (MW) |
|---|---:|---:|---:|---:|---:|
| SOCO | 3,040.3 | **3,040.3** | 6 / 9 | **3,040.3** | 0.0 |
| SPP | 1,127.4 | **1,127.4** | 9 / 19 | **625.4** | 502.0 |
| ERCOT | 1,091.4 | **1,091.4** | 13 / 21 | **490.2** | 601.2 |
| CAISO | 1,037.2 | **1,037.2** | 19 / 24 | **23.1** | 1,014.1 |
| MISO | 927.4 | **927.4** | 15 / 28 | **703.1** | 224.3 |
| PJM | 177.2 | **177.2** | 9 / 14 | **15.9** | 161.3 |
| NYISO | 72.9 | **72.9** | 11 / 19 | **64.2** | 8.7 |
| NEISO | 50.0 | **50.0** | 13 / 13 | **2.7** | 47.3 |

**The correction the reproduction surfaces (stated at the gate, not buried):** SOCO-10's census counted every technology. The COD ramp in `cod_ramp` governs only the thermal / nuclear / oil / biomass fleet the EIA-860 loader admits (`_map_fuel_type` ≠ None); solar, wind, hydro and storage ramp on their own vintage paths (`data.renewables`, `model.storage`), which already use each unit's own `Operating Month`. The last two columns split the blast radius accordingly. For SOCO nothing changes (all 3,040.3 MW is thermal: nuclear 2,228.0, gas_cc 774.0, gas_st 28.8, gas_ct 5.0, oil 4.5). For CAISO, PJM and NEISO the seam reaches only 1–3 % of the quoted number; SPP, ERCOT, MISO and NYISO keep 45–88 % of it. The governed MW by fuel: SPP gas_ct 608.4 / oil 17.0 · ERCOT gas_cc 244.0 / gas_ct 246.2 · MISO gas_ct 595.7 / gas_cc 97.8 / oil 8.0 / biomass 1.6 · NYISO gas_ct 42.0 / oil 22.2 · CAISO oil 20.0 / gas_ct 3.1 · PJM gas_ct 13.3 / oil 2.6 · NEISO gas_ct 2.7.

### 1.2 The defect runs in BOTH directions

The unit-grain mask diff (own `Operating Year/Month` vs the plant-collapsed date, retirement held identical in both arms, governed units only, nameplate MW × months) over the years each keeper carries shows **phantom-LATE** as well as phantom-early: a pre-existing unit at a plant whose mean is dragged past the solved year is held offline. ERCOT 2023 carries 1,815 MW-months of phantom-late against 2,348 early; PJM 2023 1,371 late against 872 early; MISO 2020 881 late. SOCO is early-only:

| year | units phantom-early | MW-months phantom-early | units phantom-late | MW-months phantom-late |
|---:|---:|---:|---:|---:|
| 2023 | 9 | 27,897.8 | 0 | 0.0 |
| 2024 | 3 | 3,392.1 | 0 | 0.0 |
| 2025 | 1 | 22.8 | 0 | 0.0 |

(SOCO 2023: Vogtle 3 Jan–Jun 6,684 + Vogtle 4 Jan–Dec 13,368 + Barry A3 Jan–Oct 7,740 + four small rows = 27,897.8 MW-months = 20.37 TWh of nameplate availability; SOCO-10's measured-CF energy equivalents are +12.979 TWh nuclear in 2023 and +2.167 TWh in 2024, plus 2.3–4.6 TWh for Barry A3.)

### 4.3 The LP-grain availability-mask diff, all 27 registered bundle-years (zero LP)

| ISO | year | LP units | fleet MW | units moved | MW-months → online (+) | MW-months → offline (−) | GWh-avail (+) | GWh-avail (−) | −, % of fleet-avail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CAISO | 2023 | 1911 | 52,580 | 8 | 0.0 | -50.0 | 0.0 | -36.5 | -0.008 |
| CAISO | 2024 | 1905 | 52,533 | 7 | 0.0 | -49.8 | 0.0 | -36.3 | -0.008 |
| CAISO | 2025 | 1910 | 52,535 | 7 | 0.0 | -15.9 | 0.0 | -11.5 | -0.003 |
| ERCOT | 2021 | 2326 | 80,755 | 69 | 121.4 | -1,390.9 | 87.4 | -1,018.1 | -0.144 |
| ERCOT | 2022 | 2324 | 80,750 | 62 | 726.0 | -1,148.9 | 531.4 | -843.9 | -0.119 |
| ERCOT | 2023 | 2323 | 80,748 | 46 | 484.0 | -331.0 | 334.0 | -237.5 | -0.034 |
| ERCOT | 2024 | 2321 | 80,742 | 29 | 0.0 | -1,159.0 | 0.0 | -843.2 | -0.119 |
| ERCOT | 2025 | 2310 | 80,206 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.000 |
| MISO | 2020 | 3657 | 165,289 | 64 | 607.2 | -8,183.3 | 443.3 | -5,973.5 | -0.413 |
| MISO | 2021 | 3632 | 164,441 | 55 | 27.8 | -7,626.3 | 20.4 | -5,565.4 | -0.386 |
| MISO | 2022 | 3619 | 163,569 | 39 | 0.0 | -7,090.7 | 0.0 | -5,175.5 | -0.361 |
| MISO | 2023 | 3598 | 163,384 | 20 | 0.0 | -6,909.6 | 0.0 | -5,044.0 | -0.352 |
| MISO | 2024 | 3586 | 163,231 | 18 | 0.0 | -6,335.3 | 0.0 | -4,621.3 | -0.323 |
| MISO | 2025 | 3566 | 162,070 | 12 | 0.0 | -2,685.7 | 0.0 | -1,946.7 | -0.137 |
| NEISO | 2023 | 875 | 30,820 | 2 | 0.0 | -3.7 | 0.0 | -2.6 | -0.001 |
| NEISO | 2024 | 865 | 30,794 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.000 |
| NEISO | 2025 | 867 | 30,796 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.000 |
| NYISO | 2022 | 873 | 47,005 | 2 | 0.0 | -37.8 | 0.0 | -27.6 | -0.007 |
| NYISO | 2023 | 870 | 46,534 | 2 | 0.0 | -37.8 | 0.0 | -27.6 | -0.007 |
| NYISO | 2024 | 867 | 46,430 | 2 | 0.0 | -37.8 | 0.0 | -27.6 | -0.007 |
| NYISO | 2025 | 867 | 46,228 | 2 | 0.0 | -22.0 | 0.0 | -16.0 | -0.004 |
| PJM | 2023 | 3650 | 210,055 | 10 | 601.3 | -23.9 | 360.8 | -17.5 | -0.001 |
| PJM | 2024 | 3656 | 210,065 | 2 | 0.0 | -21.5 | 0.0 | -15.7 | -0.001 |
| PJM | 2025 | 3659 | 210,172 | 2 | 0.0 | -8.0 | 0.0 | -5.8 | -0.000 |
| SPP | 2023 | 1124 | 58,034 | 2 | 0.0 | -33.0 | 0.0 | -24.1 | -0.005 |
| SPP | 2024 | 1138 | 57,565 | 6 | 0.0 | -48.6 | 0.0 | -35.3 | -0.007 |
| SPP | 2025 | 1192 | 60,740 | 4 | 0.0 | -2,794.9 | 0.0 | -2,027.3 | -0.381 |

Reading the table: **MISO** moves most — 0.3–0.4 % of fleet availability every year, almost all `CT_PEAKER`; the largest single object is plant 6137's CT bin (505 MW), 73 % of whose nameplate is 2025-COD units that the plant's 1970s coal mean had online in every year 2020–2024. **SPP 2025** is the same shape (2,795 MW-months of `CT_PEAKER`). **ERCOT** is the two-direction case: plant 65372's Houston CT bin was held fully offline through Nov–Dec 2022 and then fully online from May 2023, where its units were 75 % online from Nov 2022 and 100 % only from Oct 2024. **PJM 2023** is phantom-late: plant 62949 (AEP Ohio CC, 1.4 GW) was 67 % online in Feb–Mar 2023, not offline. **CAISO, NEISO, NYISO, PJM 2024–25 and SPP 2023–24** move by single-digit MW objects — below anything a band can see.

## 5. Screen gates (pre-registered, structural, STOP-only)

| gate | result |
|---|---|
| **G-S1 direction & order** | PASS on every solved ISO-year: every class with \|Δ MW-months\| > 100 in PRECOMMIT §1.3 moved with the sign of its availability delta (CT_PEAKER down where the phantom CTs were removed: MISO, SPP 2025, ERCOT 2023/24; CC_CHP down at ERCOT's plant 10554; ERCOT 2022 CT_PEAKER **up** +0.051 where plant 65372 was wrongly held offline Nov–Dec; PJM per §1.4), and every \|Δ energy\| ≤ the GWh-avail bound (MISO 0.33 vs 5,973; SPP 0.645 vs 2,027; ERCOT 0.31 vs 1,018). |
| **G-S2 confinement** | PASS: established at phase 0 on the identical generator list (PRECOMMIT §1.3); the shards' `COD ramp (<ISO> <year>): N unit-months masked` lines were reported per year. |
| **G-S3 identity** | PASS: MISO plant 6137 CT bin (Σ pmax 597.9 MW, online fraction 0.27 → 161.4 MW) dispatches at most 133.3 MW in every hour of 2020 and 2024; ERCOT plant 65372 (Σ pmax 484 MW) dispatches 0.0 MW Jan–Oct 2022, ≤ 291.9 Nov–Dec 2022, ≤ 318.5 in 2023 and ≤ 337.6 Jan–Sep 2024 against its 0.75 bound of 363.0; SPP plant 57881 CT bin (Σ pmax 762.9 MW, Jan–Mar fraction 0.33 → 251.8 MW) dispatches at most 224.6 MW in Jan–Mar 2025; PJM per §1.4. |
| **G-S4 unrelated flips** | not scorable without registration; the class-vs-measured direction is reported in §1.5 instead, both ways. |

## 6. G-DRIFT — why the committed keeper was the control for MISO, SPP and PJM, and why ERCOT earned a control solve

`git diff <keeper sha> 33a7c961 -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`, every hunk classified. The clone was shallow at session start (2026-09-11 →); history was deepened and the unreachable keeper commits fetched by SHA so the audit could be run at all (that fetch pulled full packs — see §8).

| ISO | keeper sha → base | solve-path commits | classification | form 4 |
|---|---|---:|---|---|
| SPP | `760012f7` → `33a7c961` | 3 | `5e6d3224` MISO 2020/21 LMP validation reference (another ISO's artifact) INERT · `0acedb7e`/`48352ffa` nyiso-231 gas-anchor mirror, gated `gas_offer_margin_anchor_vintage` kwarg-or-field, SPP recipe `False` INERT | **VALID — keeper is the control** |
| NYISO | `0acedb7e` → `33a7c961` | 3 | `5e6d3224` INERT · `48352ffa` is the merge of the keeper's own commit (no content beyond it) INERT · `760012f7` SPP-38 re-keys EIA-860 caches on the active directory; NYISO's vintage is `None` → root dir → identical data INERT | **VALID** (bound-only, §6) |
| MISO | keeper `d0fec486` ≡ main `b3212c7f` in `src/`+`scripts/` (only docs/probes differ) → `33a7c961` | 8 | `b3212c7f` is the keeper's own commit INERT · nyiso-230 ×3 (`gas_offer_margin_zonal_anchor_vintage`, NYISO-only, absent from MISO's recipe) INERT · nyiso-231 INERT · `760012f7` INERT (vintage `None`) · `5e6d3224` INERT for the SOLVE but **LIVE for the 2020/2021 C3 price SCORES** (the keeper's metrics were scored against the previous reference) | **VALID for dispatch / fuel-mix / 2022–25 prices;** 2020–21 price criteria are not differenced against the keeper |
| PJM | `f09eddbe` → `33a7c961` | 16 (+`f46e9e32`, the former shallow graft, not drift) | `3497a1d8`/`b385f3f3`/`706aa547`/`f0316092` `unit_outage_window_hour_grain` tri-state kwarg, PJM recipe absent → `None` INERT · `26f8508b`/`3f78a824` `plant_taxonomy.classify_plant` routes prime mover `PS` to `OTHER` — an EIA-923 **scoring** classifier; the commit's own measurement: solve inputs byte-identical in all 42 scored ISO-years, hydro score population changes → INERT for dispatch, **LIVE for the hydro-class score** · miso-255 ×3 (MISO-only field) INERT · nyiso-230/231 INERT · `760012f7` INERT · `5e6d3224` INERT | **VALID for dispatch / fuel-mix / prices; hydro-class scores excluded** |
| CAISO | `b8ddf8bc` → `33a7c961` | 16 | same set as PJM, same classification | informational (bound-only, §6) |
| ERCOT | `6bc43501` (2026-09-09) → `33a7c961` | **70** | includes ERCOT-lane merges (`a1513509` ercot-uri-february-fuel), the LP memory-hygiene changes (`ee40acd2`, `eaa9d6f1`), the `[R-HOLDOUT]` removal (`b0a807a8`), FR-22 keeper-field declarations (`9be52b9e`), and the whole pjm/miso/nyiso/spp 09-09→09-11 stream | **VOID — not classifiable inside this lane's budget; a LIVE hunk cannot be excluded → a control solve is EARNED** |
| NEISO | basis `cfc66722` **on a dirty tree** (`constants.py` among the changed files) | — | a dirty-tree keeper has no auditable basis by construction | n/a (bound-only, §6) |

## 7. Shards, retrievability and retention (rules 31–34)

| shard | session | outcome | branch / SHA | bundle |
|---|---|---|---|---|
| SPP arm | `session_01Qcn9tXLjgMAEVagdDamuyf` | solved 3 yr in 7.3 min | `claude/soco-15-spp-arm` `59c045e1` — **auto-merged into `main` as PR #6123** | `results/calibration/soco15_spp_arm` (on `main`, 3 × `dispatch/<y>_P1.parquet`) |
| MISO arm (first launch) | `session_01HmkDSXoXaGfmhGce4iqxTa` | STOPPED at this lane's own 20 GiB disk floor (18.5 free) — a correct stop | none | none |
| PJM arm (first launch) | `session_01BM46YfHbT9zU28Lj45qvHm` | STOPPED at the same floor (17.2 free) | none | none |
| MISO arm (relaunch, 13 GiB floor) | `session_01MKmc1qMTGysS3eLtSzWyQH` | solved 6 yr in ~70 min; 596/670/662 s per 2020–22 year at 13.34 GiB RSS with the preflight swap | `claude/soco-15-miso-arm` **`5f5675ad10369ef2c000bd04fb3117c7823d469d`** | `soco15_miso_arm_g1` (2020–22) + `soco15_miso_arm` (2023–25), 74 files |
| ERCOT arm | `session_01UqvwgkpPi4HWXXdT9oXTNc` | solved 5 yr as three recipe groups | `claude/soco-15-ercot-arm` **`f53452c7e870355bddbf943052f0cb071be6102a`** | `soco15_ercot_arm_g1` (2021–22) + `_g2` (2023) + `soco15_ercot_arm` (2024–25) |
| ERCOT control | `session_01YbL3rhiy3njjfmcDpmShMZ` | solved 5 yr in 81.5 min (6.5 min over its stated 75) | `claude/soco-15-ercot-control` **`1a2e6416bbad8ed445dc19e0d96692f2a567fe39`** | `soco15_ercot_control_g1` + `_g2` + `soco15_ercot_control` |
| PJM arm (relaunch) | `session_014E5XdrjVD4bdwzGwH5n8Jc` | _see §1.4_ | _see §1.4_ | _see §1.4_ |

The disk floor in the first MISO/PJM prompts was copied from a prior MISO shard's precedent (20 GiB); re-reading `scripts/lib/solve_container.py` showed the preflight reserves 6 GiB and provisions swap from the rest toward a 24 GiB ceiling+swap target, so 13 GiB free suffices — the relaunched shards solved at 13.34 GiB RSS with the preflight's own swap and never approached the cgroup ceiling. Every shard was archived the moment its bundle was fetched, checked out and its recipe signature verified (rule 33(a)); shard branches carrying promotable bundles are left in place (rule 33(f)(3)).

**`--reuse-solved` did not compose the recipe-group chain into one bundle.** In every multi-group replay the final invocation wrote only its own group's years; the earlier groups stayed in their `_g<N>` dirs. All years are solved and pushed, so nothing is lost, but a promotion of the ERCOT or MISO arm owes the parent-side composition (`scripts/stamp_config_partition.py --leg …`) that rule 32(d) already assigns to the parent — zero LP.

**Retrievability (rule 34(e)).** Every solved bundle is on a shard branch by full SHA with its `dispatch/<year>_P1.parquet`: `git fetch origin <sha> && git checkout <sha> -- results/calibration/<bundle>`. SPP's is on `main`. A promotion of any arm costs **zero re-solves**; MISO and ERCOT additionally cost the zero-LP composition above. The parent's local checkouts (this container) do not survive it; the branches do. No result was deleted (rule 31). **Owner: the SPP arm bundle reached `main` through the environment's auto-merge of the shard branch (PR #6123) — an unregistered bundle dir on `main` is the Class-E parity RED rule 29(c) names; it is the SPP lane's to register or prune once the owner rules, and this lane has not touched it.**

## 8. For the seven ISO lanes: how to recognise this repair in your next re-solve

When your keeper is next re-solved at a HEAD that carries `9398000d`, expect — from this repair alone, everything else equal — the class-energy deltas in §1 for your ISO (MISO §1.3, SPP §1.1, ERCOT §1.2, PJM §1.4) and, for the four bounded ISOs, nothing a band can see: NYISO ≤ 0.028 TWh in any class-year, CAISO ≤ 0.037, NEISO ≤ 0.003 (2023 only). The per-unit list that produced those numbers is PRECOMMIT §1.3's top-movers table; the full 27-bundle-year unit list is reproducible with the zero-LP fleet-only diff described there (`scripts.lib.bundle_fleet.reconstruct_bundle_fleet` + `cod_ramp.generator_online_mask` vs the pre-repair `effective_cod`). A move larger than these in your next re-solve is not this repair.

## 9. Routed, not repaired here (other lanes' plumbing this session hit)

1. `scripts/replay_keeper.py::build_kwargs` cannot route the ERCOT keeper's own `ercot_ep_gas_basis_receipts_fallback` (a `ScenarioConfig` field, not a `solve_and_persist` kwarg): a byte-faithful `replay_keeper.py` of `ercot265_receipts_five_year` SystemExits at HEAD. The ERCOT shards carried the flag through `--set` with the meta key ignored in-process; the ERCOT lane owns the fix (route config-field meta keys through `prb_overrides`, as `apply_config_partition_overlay` already does).
2. `tests/regression/test_persisted_identity.py::test_solve_surface_fingerprint_is_pinned[NYISO]` is red on `main` at `33a7c961` (a NYISO registry row landed without advancing the pin).
3. `tests/unit/data/test_caiso_st_gas_peak_measured.py::test_registry_value_matches_the_committed_artifact` is red on `main` (1.154 vs 1.166).
4. Fleet-only rebuilds of the NYISO and PJM keepers under `DATA PROFILE: code` need four interchange-layer flags each overridden off (their clean partitions are not hydrated); this is a probe-side matter, recorded in the PRECOMMIT §1.3.
5. `docs/fast-clone.md`'s trap, measured again: deepening a blobless clone (`git fetch --depth`, `git fetch <sha>`) pulls full packs — 15 GB here — because the harness clone carries no `remote.origin.promisor`; the store was rebuilt from a fresh `--filter=blob:none` clone.

## 10. Promotion (rule 31) — the question, asked explicitly

Every solved arm is its ISO's keeper recipe replayed on the repaired seam and is on a shard branch by full SHA (§7). **Owner: should any of the arms be promoted as its ISO's keeper?** This lane recommends that each ISO lane promote its arm on its own cadence (the repair is rule-14 correctness, not a fit), registers nothing itself, and deletes nothing. The shard branches carrying promotable bundles stay until the owner rules (rule 33(f)(3)); the parent's local checkouts do not survive this container.
