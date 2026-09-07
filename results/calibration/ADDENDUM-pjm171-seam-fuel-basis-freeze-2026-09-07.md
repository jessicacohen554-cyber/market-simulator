# ADDENDUM — pjm-171: **PJM's priced-interchange seam is FROZEN AT 2023 CONDITIONS in every year before 2023, while the ISO's own units burn the measured year price**

**Session** pjm-171 · **ISO** PJM · **Date** 2026-09-07 · **ZERO LP SOLVED**
**Parent** `FINDING-pjm171-2021-c3a-is-the-flat-stack-without-its-offset-2026-09-07.md`
**Keeper UNCHANGED** `2026-08-15-pjm-162-inputclock`. Nothing promoted, nothing registered.
**Trigger:** owner question — *"Are imports being repriced each year? If not they should be."*

---

## 1. ANSWER: no, not before 2023 — and it binds

**In 2023–2025 the seam and the ISO see the identical Henry Hub level, exactly as
`neighbor_gas_price`'s own docstring promises (*"a neighbor and its bordering ISO see the same
Henry Hub level"*). In every year before 2023 that contract FAILS**, through two independent
freezes that stack:

| freeze | object | coverage | pre-2023 behaviour |
|---|---|---|---|
| **F-A** gas level | `constants.HENRY_HUB_TRAJECTORIES` (`low`/`mid`/`high`) | first knot **2023** | `_hold_flat_extrapolate` returns the **2023** knot ($2.54) for every earlier year |
| **F-B** heat-rate anchor | `NeighborInterface.hr_by_year` (spec.py) | **{2023, 2024, 2025}** only | falls through to the **gas-elastic forward formula** — the forecast-lane construction |

Measured, on the resolver itself:

| year | PJM's own gas ($/MMBtu) | seam's neighbour gas | **error** |
|---|---|---|---|
| 2019 | 2.56 | 2.54 | −1 % |
| 2020 | 2.03 | 2.54 | +25 % |
| **2021** | **3.72** | **2.54** | **−32 %** |
| **2022** | **6.45** | **2.54** | **−61 %** |
| 2023 | 2.54 | 2.54 | 0 % |
| 2024 | 2.19 | 2.19 | 0 % |
| 2025 | 3.52 | 3.52 | 0 % |

**It binds.** `reference_price_interface = True` and `priced_interchange = True` in **both** the
designated keeper (`pjm_debugb_inputclock_A`) and the registered 2021/2022 touchpoint
(`pjm169_tp2022_2021_f2arm`). This is not an inert path.

Resolved seam marginal heat rates, showing F-B: 2021 and 2022 are **identical** to each other
(MISO 12.90/12.90, NYISO 10.40/10.40, Carolinas-TVA-LGEE 11.19/11.19) against measured 2023–2025
anchors that move year to year (MISO 12.38/13.92/12.03, NYISO 8.65/10.85/11.59).

---

## 2. THE MEASURED CONSEQUENCE — the seam's net position

Model net export vs EIA-930 measured (`Total interchange`, int32 sentinels masked; positive =
net export):

| year | model net export | measured | **error** |
|---|---|---|---|
| **2021** | 23.43 | 37.94 | **−14.51 TWh** |
| **2022** | 21.65 | 31.64 | **−9.99 TWh** |
| 2023 | 27.47 | 39.87 | −12.40 TWh |
| 2024 | 20.45 | 32.56 | −12.12 TWh |
| 2025 | 23.23 | 17.97 | +5.26 TWh |

The model is too **import-ward** in 2021–2024. Under-priced imports are the mechanism the
lane's own derive script already names, verbatim: *"the single mean over-prices the neighbor in
the dear-gas year and under-prices it in the cheap-gas year, opening (closing) a fake export
spread on the seam — **the root of the PJM 2025 over-export / 2024 under-export**"*
(`scripts/data/derive_neighbor_hr_by_year.py`).

**2021 and 2022 are the two DEAREST-gas years in the span** — precisely the case that docstring
identifies as worst — and they are exactly the years the fix was never applied to.

**Demand is NOT implicated and is ruled out here.** Model LP demand vs EIA-930 measured:
+0.0 % (2021), +0.3 % (2022), +0.2 % (2023), −0.1 % (2024), −0.0 % (2025). This is *not* the
2020-style inflated-zonal-demand blocker.

---

## 3. WHY THIS IS A RULE 22 + RULE 14 DEFECT, not a tuning opportunity

Rule 22 `[R-HOLDOUT]`, verbatim: *"Measured data inputs are collected once and applied
CONSISTENTLY ACROSS ALL YEARS against the keeper. There is no such thing as an input that is
'held out' … if it is [the best measured representation], it belongs in **every** year — 2019
through 2025 alike."* The measured seam anchor exists, is derived by a committed script, and is
applied to the three training years **only**. That is an input-parity break on the face of it.

Rule 14 `[R-ACCURATE]`: the held-out years currently run an **estimate** (a forward formula at a
frozen 2023 gas level) where **measured data is on disk** — `henry_hub_monthly.csv` carries
1997→2025, and the `hindcast_realized` trajectory already carries a 2021 knot, so the pattern is
established rather than novel.

**Stated against the session's own charter:** correcting this is expected to move 2021's C3a
**further from the band, not toward it**. Dearer imports ⇒ PJM imports less and exports more ⇒ it
climbs its own stack ⇒ price rises, and it rises most in the low-load hours where the seam is most
competitive — the very leg the parent finding measures as already +$3.56/MWh too high. Rough
scale: closing a 14.5 TWh net-position gap is ~1.66 GW of additional average generation on a
~91 GW mean load. **That is a prediction, not a measurement — it needs a screen.** Under rule 14 a
worse fit is a discovered bug elsewhere, never a reason to keep the estimate.

---

## 4. THE REPAIR, AND ITS ONE UNUSUALLY CLEAN PROPERTY

**It is inert in the training window and in every forecast year, by construction.**
`_hold_flat_extrapolate` returns the exact knot whenever the year is present, so adding
pre-2023 knots cannot change 2023+; and adding `hr_by_year` entries for 2021/2022 cannot change
the 2023–2025 lookups. **So the repair moves ONLY pre-2023 backcast years: the keeper is
untouched, no training-year re-solve is needed, no determination is re-verified, nothing is
promoted.**

Two parts:

- **F-A** — carry the measured Henry Hub annual means for 2019–2022 on the backcast seam path
  (measured: 2019 2.565 · 2020 2.034 · **2021 3.910** · **2022 6.419**). *Design fork, §5.*
- **F-B** — run `derive_neighbor_hr_by_year.py` for 2021/2022. **Input coverage checked:**
  NYISO realized LMP is on disk 2018–2026 (2021 ✓, 2022 ✓); MISO's is 2022–2026, so **2022 ✓ but
  2021 has no MISO anchor** and falls back to the structural `marginal_heat_rate` — which is that
  script's own designed behaviour (*"used whenever a year has no measured LMP"*), not a gap.

---

## 5. THE ONE DECISION THIS NEEDS AN OWNER FOR

`HENRY_HUB_TRAJECTORIES` is a **shared** constants table read by every ISO. Two admissible shapes:

1. **Add pre-2023 knots to the shared trajectories.** Simplest, and matches the existing
   `hindcast_realized` precedent. But it is a shared-table edit, so every ISO's pre-2023 path
   must be re-checked for a reader that currently depends on the held-flat $2.54.
2. **Give the seam its own measured-backcast gas resolution**, mirroring the ISO's own
   `gas_price_override` path, leaving the shared trajectories untouched. Narrower blast radius,
   one more code path.

**Cross-ISO exposure, stated not acted on (rule 25 `[R-ISO-SCOPE]`):** the freeze is in shared
code, so any ISO arming `reference_price_interface` on a pre-2023 year hits it. Today that is PJM
(keeper + touchpoints) and MISO (`miso233_sppseam_K`, 2023–2025 only, so currently unaffected).
**Every lane must verify its own exposure before spending a pre-2023 touchpoint** — no verdict
here transfers.

Either shape is solve-affecting and needs its own PRECOMMIT and screen under rule 29
`[R-SCREEN]` before anything is built.

---

## 6. WHAT THIS DOES **NOT** EXPLAIN

The seam freeze is a real, binding, measured defect, but it is **not** the whole 2021 volume
miss and it is **not** the parent finding's trough defect:

- 2023 and 2024 carry seam errors of −12.40 / −12.12 TWh **with correct gas and a measured
  per-year anchor**, so the seam has a level problem the freeze does not account for.
- The parent finding's trough over-pricing (+$0.82 → +$4.24/MWh) is present in all five years
  including the correctly-priced ones.

Both remain open, and this addendum re-scopes neither.

---

## 7. PLANT-LEVEL CORROBORATION (the owner's Bergen observation, confirmed)

PJM 2021, model vs **EIA-923** (and vs CEMS), TWh, on the 221 bench-matched plants:

| zone | model | CEMS | EIA-923 | model − 923 |
|---|---|---|---|---|
| **PJM_EMAAC** | 61.70 | 39.97 | 48.72 | **+12.98** |
| PJM_SWMAAC | 21.35 | 16.40 | 16.39 | +4.96 |
| PJM_ATSI | 17.98 | 17.62 | 17.62 | +0.35 |
| PJM_Central_PA | 88.60 | 83.74 | 88.40 | +0.20 |
| PJM_West_APS | 91.50 | 89.20 | 92.18 | −0.68 |
| PJM_AEP_Ohio | 141.42 | 139.17 | 143.08 | −1.66 |
| PJM_ComEd | 21.64 | 23.33 | 23.34 | −1.70 |
| PJM_Dominion | 59.68 | 55.01 | 61.43 | −1.75 |

**EMAAC is confirmed as the dominant zone** (+12.98 vs EIA-923; **+21.7 vs CEMS**, which is the
basis on which the owner's "+18 TWh" sits). By class the miss is **CC_REGULAR +26.77** (vs 923),
against COAL_BIT −6.84 and CT_PEAKER −11.40.

**One correction to the owner's read:** AEP Ohio nets **−1.66 TWh** against EIA-923, i.e. it
under-runs overall. It does contain plant-level over-runs (Rockport COAL_BIT +1.60, Hanging Rock
CC +1.10), but they are more than offset within the zone.

Top over-runs, 2021 (TWh):

| plant | zone | class | npl MW | model | CEMS | EIA-923 | **model−923** | ratio | `nodata` |
|---|---|---|---|---|---|---|---|---|---|
| **Bergen Generating Station** | EMAAC | CC_REGULAR | 1401 | **5.586** | 1.104 | **1.740** | **+3.847** | **3.21×** | **False** |
| Linden Generating Station | EMAAC | CC_REGULAR | 1356 | 6.177 | 3.547 | 3.539 | +2.637 | 1.75× | False |
| Red Oak Power LLC | EMAAC | CC_REGULAR | 821 | 5.054 | 1.574 | 2.418 | +2.636 | 2.09× | False |
| Wildcat Point | SWMAAC | CC_REGULAR | 1114 | 5.498 | 3.460 | 3.462 | +2.036 | 1.59× | False |
| York Energy Center | Central PA | CC_REGULAR | 1449 | 9.455 | 7.720 | 7.649 | +1.806 | 1.24× | False |
| Hay Road | EMAAC | CC_REGULAR | 1098 | 2.886 | 1.115 | 1.209 | +1.677 | 2.39× | False |
| Chalk Point Power | SWMAAC | ST_GAS | 1318 | 1.644 | 0.067 | 0.107 | +1.536 | **15.31×** | False |

**The owner's CEMS point is correct and worth recording precisely.** Bergen's `nodata` flag is
**False** — the model does *not* treat it as CEMS-missing. CEMS (1.104) sits *below* EIA-923
(1.740), so CEMS does under-report it by 0.64 TWh — but **the model is above BOTH**, at 3.21× the
923 figure. No CEMS coverage argument reaches a 3.2× over-run against 923. Bergen's model capacity
factor is **45.5 %** against a 923-implied **14.2 %**; Red Oak's is 70.3 % against 33.6 %.

The concentration in EMAAC CC plants with *low measured utilisation* is consistent with the
open **availability-envelope over-count** the touchpoint sidecar's own `envelopeCaveat` records
(*"the residual over-count that keeps the holdout freeze active is … baked into the TUNED years
too"*) — i.e. the owner's "too much available capacity for CC_REGULAR". **That link is a
hypothesis here, not a measurement**: this addendum did not test whether these plants' laid-up
windows are detected. It is the natural next probe and is named in §8.

---

## 8. SUCCESSOR — three separable objects, in priority order

1. **The seam fuel-basis freeze (this addendum).** Needs the §5 owner decision, then a PRECOMMIT
   and a screen. Highest confidence, cleanest repair, inert in the training window.
2. **The EMAAC CC availability envelope.** Do these plants' measured laid-up windows reach the
   model? Bergen at 45.5 % model CF against 14.2 % measured, with `nodata` False, is the sharpest
   single test case in the fleet. Zero-LP: reconstruct the 2021 fleet and compare each plant's
   availability series against its CEMS operating state.
3. **The trough over-pricing** (parent finding §3) — behind adjudicated cells, owner-facing.

None of the three is a route to "2021 inside ±10 %", and (1) is expected to move it the wrong
way. Rule 30(c) holds PJM's headline at **CALIBRATED** throughout.

---

## 9. A SMALL CORRECTION TO A COMMITTED RECORD

`ASSESSMENT-neiso-pjm-validation-touchpoints-2026-09-05.md` §3.4 states that the three corrupt
PJM 2021 hours *"carry 2,147,480,064 MW (2³¹ − 3,584) in BOTH the `Demand` and `Net generation`
columns"*. Only **one** of the three does. Measured at HEAD:

| local hour | Demand | Net generation |
|---|---|---|
| 2021-10-18 23:00 | 1,527,760,000 | 1,527,330,000 |
| 2021-10-18 24:00 | **2,147,480,000** | **2,147,480,000** |
| 2021-10-19 01:00 | 431,044,000 | 430,497,000 |

The conclusion of that section is unaffected (all three are corrupt, all three are repaired by
`load_demand`'s spike guard before the solve, and none reaches a scored criterion). But a guard
written to the literal sentinel value catches only one of the three — a `> 1e6 MW` bound is the
safe test, and is what §2's demand and interchange figures use.
