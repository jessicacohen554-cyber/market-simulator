# PRECOMMIT — ercot-263: the 2021 C3b object is a BENCHMARK-BASIS hole, not a market mechanism

**Session:** ercot-263, 2026-09-09. Branch `claude/ercot-c3b-closure-uon654`.
**Base:** `74671cca7bfdded461ec9e8eb179cac0063b2933` (origin/main at session start).
**Keeper under test:** `2026-09-09-ercot261-corroborated-gas-level` (C3b 2021 = 0.238 vs a 0.20 gate;
the ISO's only remaining five-year rubric failure).

Rule 29 `[R-SCREEN]` phase 0 — **zero LP spent, and on the finding below none is needed.**
This document seals every prediction BEFORE the repair is computed.

---

## 1. Phase 0 (zero-LP): the handoff's own framing is arithmetically wrong

The handoff directs October first: *"OCTOBER (+140.3%) is the outlier and the obvious first
object"*. That ranks months by **percentage** bias. C3b does not. It is an **absolute-dollar**
NRMSE over 12 monthly points (`calibration_verdict.py::_nrmse`), so a month's contribution is
`(model − actual)²` in $/MWh, not in percent.

Decomposing the keeper's committed 2021 payload against the committed bench:

| month | model | actual | err $ | err % | **SSE share** | NRMSE if this month were EXACT |
|---|---:|---:|---:|---:|---:|---:|
| Jan | 26.48 | 20.79 | +5.69 | +27.4% | 0.2% | 0.2378 |
| **Feb** | **1422.13** | **1521.84** | **−99.71** | **−6.6%** | **58.5%** | **0.1533** |
| Mar | 26.63 | 19.42 | +7.21 | +37.1% | 0.3% | 0.2376 |
| Apr | 67.57 | 46.80 | +20.77 | +44.4% | 2.5% | 0.2350 |
| May | 28.60 | 23.39 | +5.21 | +22.3% | 0.2% | 0.2378 |
| Jun | 67.73 | 38.39 | +29.34 | +76.4% | 5.1% | 0.2319 |
| Jul | 63.00 | 36.80 | +26.20 | +71.2% | 4.0% | 0.2331 |
| Aug | 55.79 | 35.37 | +20.42 | +57.7% | 2.5% | 0.2351 |
| Sep | 55.29 | 41.57 | +13.72 | +33.0% | 1.1% | 0.2367 |
| **Oct** | 112.62 | 46.87 | +65.75 | +140.3% | **25.4%** | **0.2055** |
| Nov | 43.16 | 40.38 | +2.78 | +6.9% | 0.0% | 0.2379 |
| Dec | 30.78 | 25.82 | +4.96 | +19.2% | 0.1% | 0.2378 |

**Two conclusions that redirect the session:**

1. **February carries 58.5% of the SSE**, not October. A −6.6% relative miss on Winter Storm
   Uri ($1,521.84/MWh) is a −$99.71/MWh absolute error — larger than October's +$65.75 and
   larger than the other eleven months combined.
2. **October is not closable on its own.** Setting October EXACTLY equal to the actual still
   leaves **0.2055 > 0.20 — still FAIL.** An October-scoped mechanism, however good, cannot
   deliver the five-year determination. The handoff's recommended object is insufficient by
   construction.

## 2. Why February is wrong: ERCOT 2021 and 2022 are scored on a DIFFERENT BASIS than 2023–2025

`score_price_shape` picks the actual through a basis ladder:
`rt_lw_mon` (load-weighted) → `da_lw_mon` → `rt_mon` (labelled **"LEGACY equal-hour basis"**).
The **model** side is always load-weighted — `render_calibration_html.py` builds `pMon` as
`Σ(price·demand)/Σdemand` within each month, then the scorer re-weights across zones by `dMon`.

Committed `data/raw/_validation-source/actual_lmp.json`, ERCOT:

| year | 2018 | 2019 | 2020 | **2021** | **2022** | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|
| basis | legacy | **LW** | **LW** | **legacy** | **legacy** | **LW** | **LW** | **LW** |

**ERCOT 2021 and 2022 compare a load-weighted model against an equal-hour actual.** The three
training years do not. Uri is the worst possible month for that mismatch: price and load are
extremely correlated, so the two weightings diverge maximally there.

**This is a coverage hole, not a data boundary.** Every input the retrofit needs is committed
and complete for both years:

- `actual_lmp_hourly_ERCOT.parquet` — 2021 and 2022: **8,760 h each, 0 NaN**.
- `actual_lmp_zonal_ERCOT.parquet` — 2021 and 2022: **131,385 rows, 15 settlement points,
  0 NaN — byte-for-byte the same shape as 2023, 2024 and 2025.**

Cross-ISO census of the same field makes it unambiguous. Every other ISO's legacy years are a
contiguous **prefix** (the oldest years, where the source genuinely stops); **ERCOT is the only
ISO with an interior hole** — LW on both sides (2020 and 2023) and legacy in between:

```
ISO      2018   2019   2020   2021   2022   2023   2024   2025
CAISO     -      -      -      -      LW     LW     LW     LW
ERCOT   legacy   LW     LW   legacy legacy   LW     LW     LW     <-- interior hole
MISO      -      -      -      -   legacy    LW     LW     LW
NEISO    LW     LW     LW     LW     LW     LW     LW     LW
NYISO    LW     LW     LW     LW     LW     LW     LW     LW
PJM     legacy   LW     LW     LW     LW     LW     LW     LW
SPP       -      -      -      -      -      LW     LW     LW
```

`derive_actual_lmp.py::lw_retrofit` was run on ERCOT for {2019, 2020} in one pass and
{2023, 2024, 2025} in another. **2021 and 2022 fell between the two passes and were never
retrofitted.** Nothing about them is unobtainable.

## 3. The repair, and why it is NOT residual-driven selection

**The repair:** `python3 scripts/data/derive_actual_lmp.py --lw-retrofit --isos ERCOT --years 2021 2022`
— the script already committed, already run for five of ERCOT's other seven years, with no new
code and no new parameter.

Governance basis, stated before the number is known:

- **Rule 14 `[R-ACCURATE]`.** The load-weighted basis is the accurate one and the scorer says so
  in its own output string. `_lw_fields` mirrors the scorer's exact model-side formula on the
  actual side for ERCOT (per-model-zone LZ series × that zone's measured demand, then
  demand-weighted across zones). The equal-hour fallback is a **system-hub simple mean** — a
  different object, not a coarser version of the same one.
- **Rule 22 `[R-HOLDOUT]`, as amended 2026-08-06.** *"What is held out is the SCORE, never the
  DATA."* An input is applied **consistently across all years** or it is not an input. Five ERCOT
  years carry this derivation; two do not; that is the defect.
- **Rule 21 `[R-DOF]`: zero free parameters.** No multiplier, adder, offset or haircut. Nothing
  is swept. No `ScenarioConfig` field moves.
- **Rule 1 `[R-STRUCT]` / rule 13 `[R-MEASURED]`: no LP is solved and no model output changes.**
  The model's `pMon` is byte-identical before and after. Only the benchmark's weighting basis
  moves, and it moves to the basis the training years already use.
- **Not an "answer key."** The repair is blind to the model: `lw_retrofit` reads only the measured
  price series and measured demand. It cannot see the residual it is about to move.

**Marker status:** ERCOT holds the `complete` marker (declared 2026-08-31), so the validation tier
{2020, 2021, 2022} is authorized and iterable. The holdout freeze scopes to `locked_test` alone.
Data intake is unfrozen unconditionally. Nothing here touches 2019 or H1-2026.

## 4. SEALED PREDICTIONS — written before the retrofit is run

**P1 (mechanism).** The retrofit will produce non-null `rt_lw_mon` for ERCOT 2021 and 2022 with a
`src_lw` string identical to the one 2023–2025 carry. *Falsified if either year returns None.*

**P2 (Feb 2021 direction — this one cuts AGAINST the session).** ERCOT price and load correlate
positively in every year measured (`rt_lw` exceeds `rt` by +12% to +33% in all five ERCOT years
that carry both). Uri is the extreme case. So the load-weighted February actual will be **HIGHER**
than the equal-hour $1,521.84 — and since the model is already **below** at $1,422.13, **February's
error will get WORSE**, and February is 58.5% of the SSE.

**P3 (the other eleven months).** The same positive correlation raises every other month's actual
too. The model is biased **high** in all eleven non-February months, so all eleven errors
**shrink**.

**P4 (net direction on C3b 2021 is genuinely UNKNOWN ex ante).** P2 pushes the NRMSE up through a
month carrying 58.5% of the SSE; P3 pulls it down through months carrying 41.5%. **I do not know
which wins, and I am recording that ignorance rather than resolving it after the fact.**

**P5 (accept-either-way — the binding commitment).** Per rule 14, **the repair stays whichever way
the number moves.** If C3b 2021 gets worse, the correct reading is that the equal-hour basis was
silently flattering the model and the true residual is larger than the keeper's registered 0.238 —
that is a discovered defect to report at full magnitude, not a reason to revert. **This session
will not revert the repair on an unfavourable result, and will not go looking for a second
mechanism to offset it.**

**P6 (blast radius).** 2023, 2024 and 2025 already carry `rt_lw_mon` and must be **byte-identical**
after the retrofit. 2022 is on the legacy basis and **will** move — it is not the target, and its
movement is reported, not managed. C3a (`price_mean`) reads the same basis ladder and will also
move for 2021/2022; **any non-target load-bearing criterion flipping PASS → FAIL is a STOP** under
rule 29's screen gate, and the session reports the flip rather than working around it.

**P7 (what this does NOT claim).** If C3b 2021 still fails after the repair, the repair is still
correct and still lands, and the remaining gap is a genuine model question handed to a follow-up
lane with the October and Jun–Aug clusters as its objects. **A basis repair is not a market
mechanism and this session will not present it as one.**

## 5. G-DRIFT (rule 29(b))

**Not engaged: no solve is spent.** Form 4 is not merely valid, it is unnecessary — the keeper's
committed payload IS the model side, unchanged, and the only thing that moves is the benchmark.
Should the repair prove insufficient and a mechanism arm become necessary, G-DRIFT is run then,
in its own addendum, before any LP.

## 6. Rule 31 `[R-RETAIN]`

No bundle is produced. Nothing is deleted. If a later arm in this session solves anything, its
bundle is gitignored, never `rm`'d, and the promotion question goes to the owner before the
session ends.
