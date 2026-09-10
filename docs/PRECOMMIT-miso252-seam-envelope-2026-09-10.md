# PRECOMMIT — miso-252: arm the MISO seam deliverability envelopes on newly-fetched 2020-2022 measured interchange

```
SESSION      : miso-252
ISO          : MISO
CONTROL      : results/calibration/miso251_tp2021  (COMMITTED; rule 29(b) form 4 — NO control solve)
SCREEN YEAR  : 2021           <-- NAMED HERE, BEFORE THE SCREEN RUNS
SPAN IF CLEAR: 2020 2021 2022 (one shard per year, rule 32)
KEEPER       : 2026-09-09-miso-250-ep-gas — UNTOUCHED, and provably so (§4)
```

## 1. What is being armed, and why it is not a new mechanism

The MISO keeper already arms three measured-seam mechanisms:

```
miso_seam_flow_limit           = True     (import deliverability envelope)
miso_seam_export_limit         = True     (export deliverability envelope)
miso_seam_measured_ladder      = True     (the Q-Q band ladder)
miso_seam_envelope_hour_ending_key = True
```

**In every pre-2023 holdout rung all three silently no-op'd**, because each reads
`data/raw/eia-930-interchange/MISO interchange hourly.parquet` and that file began at
2023-01-01. Measured directly: `measured_seam_import_envelope("MISO", y, ...)` returned
**`None` for 2020, 2021 and 2022, in both directions**.

So the holdout rungs were never replaying the keeper's recipe — rule 30(a) says a touchpoint *is*
the keeper's frozen recipe on a held-out year, and three of its armed flags were inert. **This is a
faithfulness repair, not a new mechanism**: no `ScenarioConfig` field is added, no default flips, no
matrix row is minted (rule 33 duty (c) does not fire), and no value is tuned.

**The input.** `scripts/data/fetch_eia930_interchange.py --ba MISO --source bulk --years 2020 2021
2022 --merge` — the script's own documented keyless route, whose docstring names this exact use
("**Requires NO API key**, which is what makes an out-of-training back-fill possible in an
environment that has no key") and whose usage example is a 2019-2022 back-fill. 241,872 rows added;
DIBAs AEC AECI EEI GLHB IESO LGEE MHEB PJM SIKE SOCO SPA SWPP TVA. Rule 13 `[R-MEASURED]`: a
published physical transfer record entering as a formulaic input, identical construction to the
2023-2025 rows the keeper already uses.

## 2. The defect this repairs, measured

With no envelope the seam has no hourly deliverability cap, so it imports to the **full static
interface limit** whenever its (also-flat, ladder-less) priced spread is positive. `inject_miso_seam_flow_limit`'s
own docstring describes precisely this failure — *"it over-imports on ALL three seams (the
−72/−50/−7 TWh net interchange vs the measured −38/−23/−19)"*.

| year | net seam TWh | hours within 1 % of its own max flow |
|---|---:|---:|
| 2023 / 2024 / 2025 (envelope ARMED) | +43.19 / +27.50 / +20.35 | **3 / 1 / 2 (0.0 %)** |
| **2021 (envelope `None`)** | **+75.93** | **8,654 (98.8 %)** |

## 3. THE PRE-SOLVE DELTA — computed before the solve, so the screen cannot be written to fit it

Sum of the three seams' now-available import caps against each rung's realised hourly import:

| year | unarmed net import | cap-sum mean | hours model > cap | **TWh the envelope removes** |
|---|---:|---:|---:|---:|
| 2020 | 48.694 TWh | 9,098 MW | 1,986 (22.7 %) | 1.403 |
| **2021** | **75.926 TWh** | **7,405 MW** | **7,278 (83.1 %)** | **12.842** |
| 2022 | −22.583 TWh | 7,641 MW | 230 (2.6 %) | 0.193 |

**Screen year = 2021, on the mechanism's own measured footprint — 12.842 TWh, 6.6× the next year.**
Rule 29 forbids choosing on the residual, and this choice is provably not: the largest *residual* is
2022's +50.46 TWh coal excess, and 2022 is the year with the **smallest** footprint here (0.193 TWh).
Footprint and residual point at different years, and I follow the footprint.

## 4. THE KEEPER CANNOT MOVE, AND THAT IS PROVEN, NOT ASSERTED

The fetch merged into a file the keeper reads, so this is checked rather than assumed:

* **Shared keys: 78,831 in 2023, with ZERO value changes.** No 2023-2025 row moved.
* The file gained exactly **9 rows**, all at `2023-01-01 00:00:00` — the hour-ending-midnight
  boundary hour that belongs to 2022's local calendar year and only appears now that 2022 is in
  range.
* **Decisive test:** the keeper-year envelopes were recomputed against the committed file and the
  new file. **All 24 rows (3 years × 2 directions × 4 seams) are IDENTICAL.** The boundary hour does
  not leak into 2023.

MISO's determination is the train-tier verdict (rule 30(c)) and nothing here touches it.

## 5. G-DRIFT (rule 29(b)) — ALL HUNKS INERT, so form 4 holds and NO control solve is spent

`git diff 4d498369 HEAD` over the backcast solve path — 12 files:

| file | classification |
|---|---|
| `data/raw/reference/spp_curtailment_share.csv` | INERT — per-ISO artifact MISO does not have |
| `data/curtailment_share.py`, `runner.py` (+29) | INERT — gated `iso == "SPP"` |
| `data/renewables.py` | INERT — gated `iso == "SPP"` |
| `data/fuel/hubs.py` | INERT — `nyiso_hub_gap_month_level`, default-off, absent from MISO's recipe |
| `model/interchange/caiso.py`, `__init__.py` | INERT — CAISO branch |
| `model/interchange/spec.py` | INERT — CAISO `DSW_lateevening_clean` tables + this session's own comment |
| `config/scenarios.py` | INERT — 4 new fields, **all default-off and ABSENT from MISO's recipe** (verified against `miso251_tp2021/meta.json`) |
| `scripts/run_calibration*.py` | INERT — CLI wiring for those same gates |
| `data/outages.py` | INERT — **verified**: all 11 added `ST_GAS_PEAKER_PLANTS` ids are PJM plants, and **none** is in MISO's 2,861-plant fleet |

## 6. THE SCREEN GATE — STRUCTURAL, STOP-ONLY, and NOT keyed to any residual

The arm is **killed** if any of these fails:

* **G1 direction + magnitude.** Net seam import falls, and the fall is within a factor of 2 of the
  §3 prediction — i.e. 2021 lands in **[63.1, 75.9) TWh** (a drop of 6.4–12.8+ TWh from 75.926).
* **G2 the rail is gone.** Hours within 1 % of max flow drop from 8,654 to **< 4,000** (the keeper
  years read 1–3).
* **G3 confinement.** The response is in the seam rows the mechanism claims: `import` class energy
  moves and no non-seam class moves by more than the seam does.
* **G4 no load-bearing regression.** No non-target load-bearing criterion (C1/C2/C3a/C3b) flips
  PASS → FAIL.

**It may kill the arm; it may never promote one.** No gate reads "did the coal residual improve" —
that would be the fitted-mechanism selection rule 1 `[R-STRUCT]` forbids. A screen that kills the
arm is the session's result and the remaining two years are never spent.

## 7. Rule 31 `[R-RETAIN]`

No bundle is deleted. Shard bundles are gitignored (which is what discharges rule 29(c)), stay on
local disk, and the promotion question goes to the owner before this session ends.
