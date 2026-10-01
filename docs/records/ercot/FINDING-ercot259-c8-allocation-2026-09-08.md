# FINDING — the 2021 C8 defect is the drag's UNIFORM ALLOCATION, it is visible IN-SAMPLE, and the named successor is refuted (ercot-259)

**Session** ercot-259 · **ISO** ERCOT · 2026-09-08 · **ZERO LP — no solve was run**
**Measured on** `2026-09-08-ercot256-drag-layup-mask` (`results/calibration/ercot256_five_year_keeper`, `git_sha 92dee13c`)

Every number is a read of committed artifacts (the keeper's `legitimacy_diagnostics.json`
and `hourly/` sidecars) or of the meter (`data/raw/campd-unit-level/TX_<year>.parquet`)
and `data/raw/reference/custom-bin-assignments.csv`. No parameter was tuned, no config
was changed. Rule 29 `[R-SCREEN]` clause 0: phase 0 refuted the named arm, so no screen
year was named and no LP was spent.

---

## 1. HEADLINE

| | |
|---|---|
| **Is the sub-5-day grain instrument the right successor?** | **NO — refuted on the codebase's own precedent.** §5 |
| **Is the drag CURVE wrong in 2021?** | **NO.** 2021 sits on the 2023–25 curve at every net-load bin. §2 |
| **Is the C8 defect 2021-specific?** | **NO — plant 3452 fails the identical D-4 conduct check in 2023, a TRAINING year.** §3 |
| **What is the defect?** | The drag's **uniform `floor_frac × pmax`** allocation. The convicted plant is, 5 years for 5, that year's **least-committed** plant. §4 |
| **Is there a successor that survives?** | **Yes, one** — and the obvious alternative is disqualified because it would make C8 *blind*. §6 |
| **Was anything solved?** | **No.** Phase 0 killed the arm; that is the intended rule-29 outcome. |

**Consequence for the lane: 2021 is no longer needed to work this defect.** It reproduces
in 2023/2024/2025 on the keeper's own committed diagnostics, so the repair is identified,
screened and gated entirely inside the training window (rule 22 step 3).

---

## 2. The drag curve is NOT the defect — 2021 is on it

The curve (`0.00906·NL_GW − 0.1376`, cap 0.34) was fitted on 2023–25 overnight CF vs
net-load. 2021 was never in the fit. Measured **median overnight (23h–05h) ST_GAS
non-peaker fleet CF** by net-load bin, net-load reconstructed identically in every year
from the keeper's own `system_*` / `class_hourly_*` sidecars:

| net-load GW | 2021 | 2023 | 2024 | 2025 | curve |
|---|---|---|---|---|---|
| 16–20 | 0.046 | 0.035 | 0.042 | 0.062 | 0.025 |
| 20–24 | 0.047 | 0.039 | 0.078 | 0.076 | 0.062 |
| 24–28 | 0.070 | 0.058 | 0.103 | 0.105 | 0.098 |
| 28–32 | 0.103 | 0.099 | 0.109 | 0.113 | 0.134 |
| 32–36 | 0.137 | 0.139 | 0.140 | 0.125 | 0.170 |
| 36–40 | 0.155 | 0.171 | 0.156 | 0.143 | 0.207 |
| 40–44 | 0.189 | 0.204 | 0.198 | 0.163 | 0.243 |
| 44–48 | 0.194 | 0.297 | 0.257 | 0.203 | 0.279 |

2021 sits inside the 2023–25 spread at **every** bin. Whole-year overnight
curve/measured ratio is **1.16 / 1.15 / 1.04 / 1.17** for 2021/23/24/25 — 2021 is not an
outlier; the curve over-predicts slightly and *uniformly* in every year. 2021's lower
mean net-load (31.9 GW vs ~34.7) already gives it a proportionally lower floor.

**The curve extrapolates correctly. Do not re-open it.**

---

## 3. The defect is IN-SAMPLE — and the gate simply never looks

`st_netload_drag` D-4 **per-unit conduct** rows, from the keeper's own committed
`legitimacy_diagnostics.json`, all five years:

| year | convicted plant | binding h | measured median MW | measured zero-share | verdict |
|---|---|---|---|---|---|
| 2021 | **3452** Lake Hubbard | 2,614 | 0.000 | 0.777 | **FAIL** |
| 2022 | **3452** Lake Hubbard | 4,704 | 0.000 | 0.782 | **FAIL** |
| **2023** | **3452** Lake Hubbard | 2,869 | 0.000 | 0.594 | **FAIL** |
| 2024 | **3491** Handley | 3,476 | 0.000 | 0.659 | **FAIL** |
| 2025 | **3491** Handley | 4,395 | 0.000 | 0.643 | **FAIL** |

**A D-4 conduct FAIL exists in every scored year, 2023 included.** It is invisible to the
rubric in 2023/24/25 only because C8's forced share is under the 30 % cap there
(13.4 / 12.7 / 16.6 %), and rule 16's escalation — hence `_d4_provenance` — fires *only*
above budget (`calibration_verdict.score_forced_share`). 2021 is not a different
phenomenon; it is the same defect with a smaller denominator (the class runs 11.2 TWh in
2021 against 16–20 TWh in 2023–25).

---

## 4. The defect is the UNIFORM ALLOCATION, and the correspondence is 5 for 5

`apply_netload_reliability_floor` computes one hourly scalar and applies it to every row:

```python
target = np.minimum(floor_frac * pmax[g], basis * pmax[g])   # same floor_frac, every g
```

`floor_frac` is a **fleet capacity factor**. Applied per plant it asserts that *every*
ST_GAS plant is committed at that fraction in every hour. The meter says the fleet is
lumpy, and the ordering is not stable. Measured online fraction (share of hours with
gross > 0), CAMPD, non-peaker ST_GAS:

| plant | HR | 2021 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| 3612 V H Braunig | 8.49 | 92.4 | 95.4 | 97.1 | 91.4 |
| 6243 Dansby | 9.96 | 92.7 | 69.4 | 73.5 | 85.3 |
| 3460 Cedar Bayou | 10.71 | 54.9 | 57.9 | 65.3 | 45.0 |
| 3601 Sim Gideon | 10.90 | 37.4 | 59.1 | 58.1 | 49.1 |
| 3611 O W Sommers | 10.97 | 53.8 | 65.4 | 82.1 | 69.1 |
| **3452 Lake Hubbard** | 11.45 | **22.0** | **42.4** | 53.7 | 62.7 |
| **3491 Handley** | 12.58 | 44.2 | 48.7 | **30.7** | **31.9** |
| 3628 R W Miller | 13.02 | 37.9 | 44.5 | 61.5 | 88.0 |

**The convicted plant is that year's least-committed plant — 2021, 2022, 2023, 2024,
2025, five for five** (bold cells). That is the "forcing variables are wrong" signal
rule 16 `[R-FORCED-BUDGET]` exists to raise, and it is an allocation error, not a level
error.

The error is large in **both** directions. Floor integral vs measured energy, 2021:

| plant | uniform floor | measured | ratio |
|---|---|---|---|
| **3452 Lake Hubbard** | **1.22 TWh** | **0.36 TWh** | **3.4× OVER** |
| 3612 V H Braunig | 1.50 TWh | 3.72 TWh | 0.40× UNDER |

The model forces more energy out of Lake Hubbard than the plant produced all year, while
flooring the fleet's genuine workhorse at 40 % of what it actually ran.

**A static per-plant exclusion or ordering is refuted by the same table**: the convicted
plant *changes* (3452 → 3491), and 3452 pools to ~53 % online on 2023–25 against 22 % in
2021, so any ordering identified legitimately on the training window still floors it
through thousands of dark 2021 hours.

---

## 5. Why the NAMED successor (the sub-5-day grain) is refuted

`RESULT-ercot256` §10 names "a conduct instrument that sees idleness below the extract's
5-day floor". The repo has **already adjudicated this exact question**, in the opposite
branch of the same 2×2, and its answer disqualifies the instrument for these units.

`scripts/data/derive_campd_unit_outages.py`, `--short-windows` mode, verbatim:

```python
SHORT_BASELOAD_CF: float = 0.55
# only units that normally run near their ceiling qualify, because a cycling
# unit's brief stop can be economic dispatch while a baseload unit's 1-5 day
# full stop (given 10+ h starts and take-or-pay fuel) is a forced event.
```

The sub-5-day extract admits **only** units at CF ≥ 0.55, precisely because a cycler's
short stop is indistinguishable from economic dispatch. Every plant this card would need
it for is a cycler: 3452 runs 22–63 % of hours, 3491 runs 31–49 %. They are the exact
population the guard excludes.

The card asked for the separation to be stated before building. **It is: there isn't one.**
The only signal that separates a 2-day lay-up from 2-day cycling in a low-duty-cycle unit
is the unit's own metered on/off state, and consuming that hour-by-hour is pinning the
floor to observed CEMS commitment — rule 13 `[R-MEASURED]`, which forbids exactly that.
Extending the ≥5-day lay-up mask downward would mask ordinary cycling.

**Matrix disposition: `R` (rejected), on identification, at zero LP.**

---

## 6. The successor that survives — and the one that must NOT be built

### 6a. Disqualified: a class-level LP constraint

The tempting fix is to replace the per-plant floor with one constraint per hour,
`Σ_{ST_GAS} P[g,t] ≥ floor_frac(t) · Σ pmax`, letting the LP choose the units. **It would
game the gate rather than repair the model.** `run_d2` attributes forced energy from the
**per-row** `min_gen` and `mechanism` arrays — *"forced energy is `dispatch` MWh in
at-floor row-hours, attributed to the binding mechanism id."* A class-level row carries no
per-generator floor and no mechanism id, so ST_GAS forced share would report ≈ 0 % and C8
would PASS **because the diagnostic went blind, not because the forcing stopped**. Rule 1
`[R-STRUCT]` forbids reaching the right number through a mechanism that isn't real; this is
the same defect one level down. **Do not build it.**

### 6b. Survives: merit-order allocation of the same fleet target

Keep the per-row `min_gen` floor and the same `mech_id` — so D-2/D-4 attribution and C8
stay fully honest — and change **only the level source per row**, the exact pattern
`st_gas_mustrun_level_p25` already establishes (rule 19 `[R-ONE-MECH]`: the level is
replaced, no second floor is stacked):

* hourly fleet target `floor_frac(t) · Σ pmax` — **unchanged driver, unchanged aggregate**;
* filled cheapest-first across the ST_GAS rows, each at its own measured min-stable level,
  the marginal plant spilling to available capacity so the aggregate is preserved exactly;
* min-stable levels from a frozen derive on **2023–25 only** (rule 22 step 3, rule 23).

Pre-solve delta (zero LP; availability ignored on both sides, so like-for-like):

| year | plant | uniform floor | merit-order floor |
|---|---|---|---|
| 2021 | **3452** (convicted) | 1.22 TWh / 8,609 h | **0.01 TWh** / 4,677 h |
| 2024 | **3491** (convicted) | 2.00 TWh / 8,512 h | **0.53 TWh** / 5,307 h |
| 2025 | **3491** (convicted) | 2.02 TWh / 8,398 h | **0.57 TWh** / 5,604 h |
| 2021 | 3612 Braunig (workhorse) | 1.50 TWh | **2.83 TWh** |

Both errors move the right way, and the mechanism's own arithmetic — not the residual —
predicts it: expensive plants sit at the end of the fill and take only the remainder.

### 6c. The weakness, stated at the gate and NOT tuned around

The fill orders by cost, and cost is an imperfect proxy for commitment. Spearman(heat
rate, online fraction):

| 2021 | 2023 | 2024 | 2025 |
|---|---|---|---|
| −0.714 | −0.833 | −0.690 | **−0.286 (p = 0.49)** |

**2025 breaks it**: R W Miller, the most expensive plant in the fleet (HR 13.02), ran
88.0 % of hours — the second-most-committed unit that year. Cost order is right in three
of four years and materially wrong in one. This is reported at full magnitude; it is a
limitation of the proxy, not something to fit around, and any screen of 6b must be gated
on the mechanism's own footprint (rule 29), never on C8.

---

## 7. What this changes for the lane

1. **The 2021 C3b/C3a level half is untouched by this finding** and remains data-blocked
   exactly as `FINDING-ercot258` left it.
2. **The C8 half no longer needs 2021.** The defect, its repair and its gates all live in
   2023–2025.
3. **The sub-5-day instrument should be struck from the lever queue** (§5).
4. **The class-level constraint should be struck before anyone builds it** (§6a).
5. 6b is designed but **not built** — its cost-proxy weakness (§6c) is a judgement call
   about how the fleet's commitment order should be identified, and it is put to the owner
   rather than chosen unilaterally inside a session.

---

*Generated by [Claude Code](https://claude.ai/code)*
