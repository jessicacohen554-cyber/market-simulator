# PRECOMMIT nyiso-220 SCREEN — `hydro_budget_period_by_instrument`, one year, structural STOP-only gates

**Session:** nyiso-220. **Branch:** `claude/nyiso-hydro-operating-ranges-4jfj0b`.
**Date:** 2026-09-08. **Keeper:** `2026-09-07-nyiso-213-summer-seam` — to be left untouched.
**Committed and pushed BEFORE the screen solve is launched and before any screen number is read.**

---

## 1. Screen year — named now, and why

**SCREEN YEAR = 2025.** Chosen per rule 29 `[R-SCREEN]` as the year the mechanism's **own measured
footprint is largest**, from the zero-LP phase 0 (`_nyiso220_phase0_period_overlap.json`):

| year | daily footprint (energy crossing day boundaries) | weekly |
|---|---:|---:|
| 2023 | 5.15 % | 3.19 % |
| 2024 | 4.58 % | 2.90 % |
| **2025** | **7.47 %** | **5.18 %** |

**This is explicitly NOT the year with the largest residual**, which rule 29 forbids as a basis. The
2022 holdout is not touched and is not a candidate.

**One year only.** The full 2023–2025 span is spent only if this screen clears, as one
`--year 2023 2024 2025` invocation and one bundle (rule 16 `[R-ALLYEARS]`). The screen bundle is a
**throwaway diagnostic probe**: never registered, never a keeper, never quoted as a keeper number,
and its year is re-solved inside any full bundle. Rule 31 `[R-RETAIN]`: it is **gitignored, not
deleted**, and the promotion question is surfaced before the session ends.

## 2. The gates — STRUCTURAL, STOP-ONLY, and SELF-CONTAINED

Rule 29: the screen asks whether the mechanism **does what its own arithmetic says it does**. It
**may kill the arm; it may never promote it**, and it is **never gated on the target residual**.

**Deliberately self-contained.** Every gate below is checkable **within the armed run alone**, not
by differencing against the keeper. This is a design choice with a reason: 45 files on the solve
path have changed since the keeper's `git_sha` `51f2fc2d`, so a rule 29(b) form-4 control
differencing would need a full hunk-by-hunk G-DRIFT audit to be valid. A STOP-only screen does not
need one if its gates do not rest on control differencing — so they do not. (A full G-DRIFT audit is
still owed before any *promotion*, and is not attempted or claimed here.)

| gate | threshold, written before the solve | if it fails |
|---|---|---|
| **G1 FEASIBILITY** | The LP solves to optimality in the screen year. A shorter period is strictly a *restriction* of the feasible set, so **over-constraint is the predicted failure mode** and infeasibility is a real possible outcome, not a bug to code around. | **KILL** |
| **G2 IDENTITY — monthly energy conserved** | Armed-run annual hydro energy within **0.1 %** of the keeper's 2025 value, and each month within **0.5 %**. This is the identity month-alignment exists to guarantee: the mechanism constrains *when within a month*, never *how much*. A miss means the allocation is wrong. | **KILL** |
| **G3 DIRECTION & MAGNITUDE** | The fleet's cross-day footprint (the phase-0 statistic, recomputed on the armed run's own hourlies) must **FALL** versus the keeper's 2025 value of **7.47 %**, and must **not fall to 0.00 %** — 28.62 % of hydro MW is deliberately unconstrained, so a fall to zero would mean the mechanism reached rows it does not claim. Pre-registered expected band: **a fall to between 1.0 % and 6.0 %.** | outside the band ⇒ **KILL** (the mechanism is not doing what its arithmetic says) |
| **G4 FOOTPRINT CONFINEMENT** | Non-hydro classes' annual energy each within **2 %** of the keeper's 2025 value. The mechanism claims only hydro rows; a larger move means it is reaching rows it does not claim. *(Stated as a bound on the mechanism's reach, not a quality target — hydro is ~20 % of NYISO generation, so some thermal re-dispatch is expected and correct.)* | **KILL** |
| **G5 NO NON-TARGET FLIP** | No **non-hydro, load-bearing** criterion (C1, C2, C3a, C3b) flips PASS → FAIL in the screen year. | **KILL** |

**Explicitly NOT gates, and named so I cannot quietly promote them into gates after seeing them:**
C3a / C3b / C3c levels; the within-month day-to-day **r versus actual**; the amplitude ratio versus
actual; and any price residual. **G3 measures the mechanism's own dispersion, not agreement with
the actual** — that distinction is the whole difference between a structural screen and the
fitted-mechanism selection rule 1 `[R-STRUCT]` forbids. Improving the residual is **not** what
earns the full span; clearing the structural gates is.

**I will not restate any threshold after seeing a number.** Misses are reported in the words above.

## 3. Rule 14 `[R-ACCURATE]`, restated before the number exists

Hydro is ~20 % of NYISO generation, so re-timing it **will** move C3a/C3b/C3c. **If the faithful
representation makes the price fit worse, it STAYS**, and the worse fit is a discovered root-cause
question, not grounds to revert. Precedent: the 2026-07-25 probe made C3a-2023 worse
(+18.3 → +22.2 %) and was still recorded as **mechanism confirmed**. I am recording this before the
solve so that a worse price fit cannot later be used — by me — as a reason to abandon a structurally
correct mechanism.

## 4. What is already established and is NOT re-litigated by this screen

* **Rule 19 `[R-ONE-MECH]` — RECONCILE**, decided at phase 0 on the owner's Q2 overlap arithmetic
  (zero LP), not by preference. Disjoint declared windows: the envelope bounds the **diurnal shape**
  (fleet hourly ceiling on month × hour-of-day); this row bounds **day-to-day reallocation**
  (per-plant energy conservation). The decisive leg: 4.58–7.47 % of annual hydro energy crosses day
  boundaries **in the keeper's own dispatch, with the envelope already armed**.
* **Byte-identity when off**, verified by measurement: the runner returns `UNSET`, `DispatchSpec`
  omits the key, the field is registered in `_CACHE_KEY_OPTIONAL_FIELDS`, and the keeper's
  `cache_key` is **`95d4d8d167373eb7`, unmoved**.
* **Rule 21 `[R-DOF]`** — the period lengths are **not free parameters set here**: 168 h is stated
  in words by the IJC peaking-and-ponding directive; 24 h is derived from the treaty's silence plus
  the measured 0.244 h pondage. **Neither was chosen or swept against any gate**, and no sweep will
  be run: if the screen fails, the arm dies — it is not re-run at another period length.

## 5. The DOF ledger entry this mechanism would carry

| parameter | value | identification source | swept? |
|---|---|---|---|
| St. Lawrence budget period | 168 h | IJC peaking-and-ponding directive, stated verbatim ("the total weekly flow the same"); published categorical duration class (rule 21 case 2) | **no** |
| Niagara budget period | 24 h | derived: governing instruments state no conservation period (verified mechanically), measured NID pondage 0.244 h; 1 h would pin dispatch and destroy the treaty-imposed diurnal swing | **no** |
| within-period allocation | flat | measured near-zero day-to-day inflow variability on both regulated Great-Lakes outflows (within-month daily r 0.079 / 0.080, nyiso-219) | **no** |
| plants covered | 2 of 163 (71.376 % of MW) | the only two with a retrieved governing instrument; 161 domestic-river plants deliberately excluded (rule 14) | **no** |

**Zero fitted scalars. No eighth owner card is opened.**
