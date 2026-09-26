# RESULT — miso-277: D1 re-solved as ruled (MISO-South on Henry Hub). C3b 2021 improves 0.290 → 0.254 but still fails; the storm week is now under-priced. No criterion flips.

```
LANE     : miso-277 (owner ruling 2026-09-26 "Re-solve D1 as ruled (Recommended)")
PREREG   : docs/PRECOMMIT-miso277-d1-as-ruled-2026-09-26.md (pin bd0329ed)
KEEPER   : 2026-09-26-miso-275-cc-exempt (miso275_span) — unchanged
RUN      : 2026-09-26-miso-277-d1-as (results/calibration/miso277_span, 2019-2025), registered
DELTA    : miso_winter_gas_daily_delivered = true, with MISO-South on Henry Hub in every year. DOF +0
CONTROL  : keeper bundle (G-DRIFT e5acf0fe..bd0329ed, all non-delta hunks INERT; rule 29(b) form 4)
VERDICT  : full span NOT-YET (fuelmix, price_mean, price_shape — the keeper's same three criteria)
           train 2023-2025 CALIBRATED (unchanged); zero criterion-year status flips vs the keeper
```

## 1. Legs

Seven single-year shards pinned to `bd0329ed`. Every leg passed the shard check in the parent (recipe, vintage,
inputs, hydro classifier, log incl. `MISO-South=henry`). Each bundle has 18 files incl. `dispatch/<Y>_P1.parquet`.
All 7 shard sessions archived.

| year | leg commit (provenance) | LW internal price keeper → arm $/MWh |
|---|---|---|
| 2019 | `46acc4cb` | 27.796 → 27.911 |
| 2020 | `eaba8fa8` | 24.377 → 24.546 |
| 2021 | `059c060e` | 38.677 → **37.079** (miso-276: 40.688) |
| 2022 | `f50d300b` | 58.582 → 58.399 (= miso-276) |
| 2023 | `0b2a73ba` | 33.256 → 32.675 (= miso-276) |
| 2024 | `582acc5b` | 30.498 → 30.730 (= miso-276) |
| 2025 | `b4204f50` | 41.792 → 41.670 (= miso-276) |

2022–2025 reproduce miso-276 exactly, as predicted (South already had hub-table rows). The miso-276 South slack
(4 h, 2,021 MWh on Feb 15 2021) is **gone**: 0 MWh.

## 2. Gates (live scorer, rubric 3.9)

| criterion-year | keeper miso-275 | miso-276 (as built) | **miso-277 (as ruled)** |
|---|---|---|---|
| **C3b 2021** (≤ 0.20) | 0.290 FAIL | 0.416 FAIL | **0.254 FAIL** |
| C3a 2021 (±10 %) | −4.8 % | +0.1 % | **−8.7 %** (PASS, near edge) |
| C3a 2022 | −15.4 % FAIL | −15.8 % FAIL | −15.8 % FAIL |
| C1 ST_GAS 2019 | −8.46 FAIL | −8.60 FAIL | −8.56 FAIL |
| C3b 2020 / 2023 | 0.100 / 0.069 | 0.106 / 0.059 | 0.109 / 0.059 |
| C3a 2019 / 2020 / 2023–25 | +5.2 / +6.0 / +1.2 / −5.6 / −8.1 | +5.9 / +6.5 / −0.5 / −4.9 / −8.3 | +5.7 / +6.8 / −0.5 / −4.9 / −8.3 |
| legitimacy D1/D2/D4 | 12 findings | 12 (same set) | 12 (same set) |
| determination | NOT-YET (3) | NOT-YET (3) | NOT-YET (3) |

**Feb 2021, equal-hour internal LMP $/MWh:**

| | Feb | storm Feb 13–16 | 2021 max |
|---|---:|---:|---:|
| actual RT | 60.6 | 191.6 | — |
| keeper | 62.5 | 122.3 | 240.5 |
| miso-276 as built | 84.5 | 333.4 | 392.6 |
| **miso-277 as ruled** | **45.8** | **74.0** | 166.2 |

## 3. Reading

- **The ruled construction, built correctly, under-prices the storm.** With South on Henry Hub (≤ $24 print) and the
  flow-date staircase, MISO-South gas in Feb 13–16 sits at ~$8 while the real Louisiana fleet paid far more (its own
  EIA-923 Feb cost burn-weights to ~$22; FINDING-miso277 §3). The storm week lands at 74 vs 192.
- **C3b 2021 improves anyway** (0.290 → 0.254) because the rest of the winter tracks better: calm-day gas is at the
  traded commodity in every zone, and the miso-276 South blow-up and slack are gone.
- **The cost:** Feb-2021 mean falls below actual (45.8 vs 60.6) and C3a 2021 moves −4.8 % → −8.7 %, still PASS.
- **Net:** a correct build of the owner's ruling. It is a structural repair (rule 14) that improves the one failing
  object it targets without flipping it, and it moves the storm-week error from +211 (as built) to −118 (keeper −69).
  Under rule 1 neither the better C3b nor the under-priced storm selects it.

## 4. Where the bytes are

The composite `miso277_span` lands on `main` with this lane's PR: the slim bundle (47 files, ~23 MB incl. `hourly/`),
attestation (keeper's plus a `miso277` block, DOF +0), regenerated diagnostics, stamped partition (identical to the
keeper's, passes `--check`), the registry sidecar and the payload. **Promotion from there costs zero re-solves.**
Per-year leg dirs are on this session's disk only, gitignored; the SHAs above are provenance (rule 33(d)).

## 5. Promotion — the owner's call (rule 31)

Year set (rule 35(b)): outgoing {2019–2025}, incoming {2019–2025}, covered.

- **For:** it is the owner's D1 ruling built as ruled; it replaces gas priced below the traded commodity (rule 14);
  C3b 2021 improves; no gate worsens in status; no new legitimacy finding.
- **Against:** no status flips; the 2021 storm week is under-priced by a margin comparable to the keeper's (−118 vs
  −69), and C3a 2021 moves toward its band edge.
