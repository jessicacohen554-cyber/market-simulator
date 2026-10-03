# RESULT-phase1 — closeout-SOCO-3: all three PRECOMMIT-phase1 bars clear (zero LP)

The bars were fixed in `PRECOMMIT-phase1-closeout-soco-3-2026-10-03.md` (pushed at `bd94ae26` before computing).

- **Probe:** `scripts/probes/_closeout_soco3_phase1_reach.py`, which imports `reach_table` from
  `_closeout_soco3_pile_reach.py`.
- **Inputs:** the 2015–2017 Page 2 stocks from PR #7134 (`065f38d1`), read from the raw CSVs.
- **Outputs:** `phase1_reach_plant_year.csv`, `phase1_c1.csv`, `phase1_bars.json`.

## Bars

| Bar | Reading | Result |
|---|---|---|
| B1 CC_REGULAR 2019 passes C1 at f = 0.5 | **+2.91 pp PASS** (113.8 vs 110.6 TWh). At f = 1.0 it is +2.39 PASS. Minimum passing f = **0.45** | **CLEAR**, thin: 0.09 pp margin |
| B2 no plant-year floor > 0.5 TWh above actual | worst **0.18 TWh** (Barry 2021). The 2020 total is 0.10 TWh, down from 1.55 under 2018-start history | **CLEAR** |
| B3 no C1 PASS→FAIL, any class or year, at f = 1.0 and f = 0.5 | none at either | **CLEAR** |

Reported, not gating: COAL_BIT 2019 reads **−3.04 pp FAIL** at both f (keeper −4.25). It stays the ledgered row.

## Reach (field construction, S_max over 2015 … Y−1)

Units are TWh.

| Year | Added | Cut | Net | Floor > actual |
|---|---|---|---|---|
| 2019 | 3.47 (Barry 1.93, Crist 1.53) | 0.94 (Hammond 0.49, Miller 0.44) | +2.53 | 0.00 |
| 2020 | 2.73 | 0.12 | +2.60 | 0.10 |
| 2021 | 1.57 | 0.29 | +1.28 | 0.18 |
| 2022 | 0.00 | 6.58 | −6.58 | 0.00 |
| 2023 | 1.62 | 0.00 | +1.62 | 0.00 |
| 2024 | 1.78 | 0.00 | +1.78 | 0.03 |
| 2025 | 0.00 | 2.08 | −2.08 | 0.00 |

The deeper yard history leaves headroom of 0.39–0.57 at the 2019 cyclers, where the phase-0 field construction had
0.00–0.33. The 2019 floor falls from +5.39 to +3.47 TWh, and Gaston drops out of it entirely.

## Next (R-49 step 3)

1. Verify R-49 on `main`.
2. SOCO gate lift (`src`/`scripts`, Opus).
3. A solve PRECOMMIT with G-DRIFT keeper → pin, and these kills: C4 coal 2020 > 0.30, unserved energy, C6, C8,
   recipe diff.
4. 7 year-isolated shards.

**Risk to carry:** the B1 margin is 0.09 pp at f = 0.5. The real LP's soft floor and capacity clip deliver less than
this upper bound, and its displacement mix is unknown. CC 2019 can therefore miss the bar in the solve.
