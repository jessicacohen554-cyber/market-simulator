# FINDING — ERCOT 2021: path A is blocked, hypothesis B is dead, and the "second factor" was already found (ercot-258)

**Session** ercot-258 · **ISO** ERCOT · 2026-09-08 · **ZERO LP — no solve was run**
**Measured on** `2026-09-08-ercot256-drag-layup-mask` (`results/calibration/ercot256_five_year_keeper`, `git_sha 92dee13c`)

Every number below is a read of committed artifacts (the keeper's `hourly/` sidecars,
its three `run_config_*.json`, `data/raw/_validation-source/actual_lmp.json`,
`frontend/data/backcast/bench/ERCOT/`) or a call of the model's own resolvers. No
parameter was tuned. Rule 29 `[R-SCREEN]` clause 0: the phase-0 work killed the
candidate arm, so no screen year was named and no LP was spent.

---

## 1. HEADLINE

| card option | verdict |
|---|---|
| **A — HSL intake** | **BLOCKED.** No 2021/2022 NP6 archives exist, and the route was already adjudicated **ungettable** on 2026-07-10. Not re-opened. |
| **B — k_peak 33.0 is the second factor** | **DEAD.** Killed at zero LP on its own footprint. |
| **C — `ercot_ep_gas_basis_monthly`** | **Refused — but NOT on C3c.** C3c does *not* block under rubric v3.6. **C3b does**, and C3b is load-bearing. |

**And the question B was asking is already answered.** The second factor is not the
offer curve — it is the **Uri-contaminated annual EP gas basis** that ercot-254 measured
and documented the day before this card was written
(`docs/FINDING-ercot254-2021-offer-level-root-cause-2026-09-07.md`). B and C are the
same object seen from two ends.

---

## 2. B is dead: the carve-out has no footprint where the defect lives

The carve-out and forward configs differ in **exactly one thing** — every `peak` and
`phys_peak` band multiplied by **33.0**, uniformly across all eight groups (plus
`ercot_offer_swcap_clip`). `committed`, `econ_low`, `econ_high` and every `phys_*`
band below peak are **byte-identical**.

So the hypothesis is testable without a solve: *does the `peak` band touch the bottom
of the 2021 price distribution?* Measured on the keeper's own
`class_band_hourly_2021.parquet`:

| | 2021 | 2022 | 2023 |
|---|---|---|---|
| peak-band energy | **0.357 TWh — 0.091 % of all dispatch** | 0.425 TWh (0.099 %) | 0.390 TWh (0.088 %) |
| hours with any peak-band MW | 722 (8.2 %) | 993 (11.3 %) | 2,171 (24.8 %) |
| **minimum price in those hours** | **$51.57** | $28.70 | $24.88 |
| peak-band MW in hours near the **p25** price | **mean 0.013 MW**, max 2.94 | mean 0.181 | **0.000** |
| peak-band MW in hours near the **p50** price | **mean 0.036 MW**, max 2.94 | mean 0.074 | mean 0.016 |

The peak band is **never live below $51.57** in 2021, and carries a mean of
**0.013 MW** in the p25-price hours — against ~40 GW of load. The entire 2021 defect
lives at p5/p25/p50 (+$34.92 / +$39.35 / +$40.49). **A multiplier on a band that is
absent from those hours cannot move them.** Setting k_peak 33.0 → 1.0 is measurably
inert against the target.

A second, independent argument needs no measurement at all: **the carve-out is
identical in 2021 and 2022.** A factor common to both years cannot explain a
difference between them — and the difference is large (below).

---

## 3. The defect is NOT a ratio artifact — and that is what makes it real

The finding ercot-256b flagged 2022 (p25 ratio 1.37×) as evidence that HSL alone
does not explain 2021 (3.19×). Ratios on different price levels can manufacture that,
so it was worth checking in absolute dollars. **It is not an artifact:**

| year | HSL | actual p25 | model p25 | ratio | **absolute error** |
|---|---|---|---|---|---|
| **2021** | **NO** | 18.00 | 57.35 | 3.19× | **+39.35** |
| **2022** | **NO** | 27.34 | 37.48 | 1.37× | **+10.14** |
| 2023 | YES | 15.69 | 20.97 | 1.34× | +5.28 |
| 2024 | YES | 13.37 | 19.20 | 1.44× | +5.83 |
| 2025 | YES | 19.46 | 24.66 | 1.27× | +5.20 |

2021's bottom-of-stack error is **~4× larger in absolute dollars than 2022's and ~7×
the HSL years'**. A real second factor exists. ercot-256b §5 was right to flag it.

---

## 4. What the second factor is — corroborated from a second direction

ercot-254 measured it directly: `ercot_electric_power_gas_basis` reduces the monthly
EIA N3045TX3 series to **one annual mean**, and `apply_ercot_zonal_gas_basis` adds that
scalar to **every ERCOT gas unit in all 8,760 hours**. February 2021 prints
**$61.88/Mcf** — 30.7σ above the other eleven months — so 2021's flat level correction
is **+5.778 $/MMBtu** against +0.199 / +0.504 in 2022 / 2023.

This session reached the same number from the opposite end, without touching the fuel
arrays. Regressing the model's **monthly median price** on the **monthly Henry Hub
price** (February dropped, so Uri is not in the fit):

| year | slope (implied HR) | intercept $/MWh | implied gas adder $/MMBtu | R² |
|---|---|---|---|---|
| **2021** | 6.06 | **+43.65** | **+7.20** | 0.74 |
| 2022 | 10.72 | −16.77 | −1.56 | 0.93 |
| 2024 | 4.27 | +14.23 | +3.33 | 0.26 |
| *2021 **actuals*** | *5.74* | *+12.47* | *+2.17* | — |

A two-point fit on the same data (January vs October 2021) gives **c = +$4.98/MMBtu at
HR 7.36** — i.e. a gas-independent component of roughly $5/MMBtu, against the
documented +5.778. Two unrelated instruments, one object.

The signature is visible without any fit: **2021's model price is nearly
gas-insensitive.** Across the year gas moves 2.62 → 5.51 ($/MMBtu, ×2.1) while the
model's monthly median moves only 56.59 → 77.18 (×1.36). Implied market heat rate runs
**14–24 in 2021 against 7–10 in every other year** — exactly what a large flat adder
under a variable fuel price produces.

**And the dispatch is right while the price is wrong**, which is what pins this to the
offer *level* rather than the merit order:

| 2021, TWh | model | actual (EIA-930) |
|---|---|---|
| coal (PRB + lignite) | 76.20 | 75.10 |
| gas (all classes) | 160.39 | 163.92 |
| wind | 95.98 | 95.47 |
| solar | 15.53 | 15.24 |
| nuclear | 39.97 | 40.47 |

Scarcity overlays are not involved: `ordc_adder` and `rtordpa_overlay` are **exactly
zero** at the 2021 p25 and p50. The bottom of the 2021 stack is pure merit order,
priced off a gas cost that carries a +$5.78/MMBtu Uri artifact in all 8,760 hours.

---

## 5. C: the blocker is C3b, not C3c — the card's worry was misplaced

Scored live on the keeper (`scripts/calibration_verdict.py --run-id 2026-09-08-ercot256-drag-layup-mask`).

**C3c does not block.** 2021 is validation tier, so under rubric **v3.6** the C3c
standing rule's lone-failure condition is dropped and C3c reads **CAVEAT** on a
held-out year whatever else that year does. Guard (b) is satisfied — **C6 governance
PASSES** on this keeper. The 234 → 688 h blow-out would therefore be auto-ledgered, not
fatal. *(It also would not spend a second ledger slot: C3c already carries the ERCOT
model-class ledger entry on 2024/2025.)*

**C3b blocks.** `PRICE_SHAPE_NRMSE_MAX = 0.20`, and C3b is **TIER_LOAD** —
load-bearing, never caveat-able (rule 22's guard (c) admits `model-class` only for a
supporting-tier criterion). The arm moves it **0.361 → 0.501**, i.e. **2.5× the gate and
materially worse**:

| 2021 | control | `ercot_ep_gas_basis_monthly` | gate | verdict |
|---|---|---|---|---|
| **C3b** NRMSE | 0.361 | **0.501** | ≤ 0.20 | **FAIL, and worse** — load-bearing, blocks |
| C3c h > $200 | 234 (0.907×) | 688 (2.67×) | [0.5×, 2×] | FAIL → **ledgered CAVEAT** under v3.6 |

So C is refused on a load-bearing criterion **regardless of** the C3c question the card
posed. Answering the C3c question does not unblock it.

---

## 6. A successor that looks right and is NOT — recorded so it is not spent on

RESULT-ercot254 names the successor as a **daily** delivered-gas basis, and ercot-255
phase 0 established no daily Waha/HSC/Katy series is on disk or free from EIA.

An apparently cheaper route suggests itself: the repo **already has Henry Hub daily**
(`data/raw/gas-prices/henry_hub_daily.csv`, already consumed by `gas_daily_shape`), and
it concentrates Uri correctly — Feb 2021 runs ~$2.9 baseline with **6.50 / 6.12 / 11.32
/ 23.86 / 8.56 / 4.96** on Feb 11–19. Shaping February's EP basis by that daily curve
would appear to fix the "672 flat hours vs ~5 storm days" breadth defect.

**It does not work, on arithmetic.** The February *mean* basis is itself the
contaminated object (~$54/MMBtu). Any **mean-preserving** within-month reshaping still
averages $54, so the 23 calm days keep ~$28–30/MMBtu of basis they never paid. A
multiplicative reconstruction off HH daily fails the same way. Recovering breadth
requires the **actual daily delivered** series, not a reshaping of a contaminated
monthly mean — i.e. exactly the intake ercot-255 found unavailable. Route closed.

---

## 7. Two card corrections

1. **ERCOT's 2021/2022 bench parts are no longer empty — ercot-256 rebuilt them**
   (`0 → 94 and 98 plants`; 2023/24/25 carry 99/100/100). The card's "ZERO plants …
   C1 is UNSCORED for 2021/2022 … ERCOT 2021 is scored on PRICE AND FORCING ALONE" was
   written against the pre-ercot-256 state and is **stale**. On the current keeper
   **C1, C2 and C4 all PASS**, 2021 included, and C1's 2021 fuel mix is good to ~1 TWh
   per family (§4). The D-4 per-unit conduct rider likewise runs — the scorer names
   plant 3452 by id on the 2021 C8 row. **A hand recomputation of the rider is not
   needed**, contrary to the card.
2. **The keeper's run-level determination is NOT-YET, and every FAIL is 2021**
   (C3a +26.4 %, C3b 0.334, C8 ST_GAS 33.1 % forced). 2023–2025 are clean, so the
   **train tier is CALIBRATED** and rule 30(c) holds the ISO's headline — consistent
   with the card, but worth stating as measured rather than assumed.

---

## 8. Where this leaves 2021

Both identified defects are **data asks, not levers**, and both need the same kind of
thing — measured ERCOT data behind an owner-credentialed portal:

| defect | effect | status |
|---|---|---|
| **No HSL parquet** (ercot-256b) | no curtailment ⇒ **zero hours ≤ $0**, model min +$17.57 vs actual −$31.65 | needs NP6 2021/2022 upload → `data/raw/ercot-hsl/np6/2021/`, `…/2022/` |
| **Uri-contaminated annual EP gas basis** (ercot-254) | **+5.778 $/MMBtu flat on all 8,760 h** ⇒ the +$40/MWh level error | needs a **daily** delivered-gas series (Waha / HSC) |

Neither is closable from this session. No LP was spent, and per rule 29 clause 0 that
is the intended outcome when phase 0 kills the arm.

---

*Generated by [Claude Code](https://claude.ai/code)*
