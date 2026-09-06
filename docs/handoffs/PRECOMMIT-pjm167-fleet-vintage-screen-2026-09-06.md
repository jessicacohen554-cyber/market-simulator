# PRECOMMIT — pjm-167 F1: the backcast fleet registry tracks the solve year

**Session:** pjm-167 · **Date:** 2026-09-06 · **HEAD at writing:** `82a7742d`
**Branch:** `claude/pjm-price-cc-regular-review-al60pj`
**Evidence:** `results/calibration/FINDING-pjm167-input-clock-2021-2022-2026-09-06.md` §3
**Keeper (control):** `2026-08-15-pjm-162-inputclock` / `pjm_debugb_inputclock_A`

Written **before any LP is solved**, per rule 29 `[R-SCREEN]`. Every gate below is fixed here
and is not revisable after a result is seen.

---

## 1. The defect and the change

The backcast fleet is built from the **2025 Early Release** EIA-860 snapshot in every solve
year, plus a within-window retiree file covering **retirement years 2023–2024 only**
(`process_eia860.py:74`, `RETIREMENT_WINDOW_START = 2023`, commented *"Bump only if the
supported window moves"* — the span moved to 2019–2025 on 2026-08-06 and this did not).
Measured consequence (FINDING §3.3): the model carries an **identical 38,722 MW PJM coal
fleet in 2021, 2022 and 2023**, and in 2021 dispatches **95.4 %** of it.

**The change.** `ScenarioConfig.eia860_vintage_year` and `paths.set_eia860_vintage` already
exist and vintages **2018–2024** are all committed; the knob is a **run-level scalar** while a
rule-16 bundle spans three years, so it cannot express "each year reads its own vintage". Add
one gated field — working name `eia860_vintage_tracks_solve_year: bool = False` — that makes
`runner.run_year` resolve the vintage from the **year being solved**, falling through to the
canonical snapshot when no `vintage_<year>/` directory exists.

- **Zero fitted scalars.** The vintage is selected by calendar year, never by a result.
- **Rule 13/14 admissible.** The year's own EIA-860 annual release is a measured registry that
  regenerates for any year and responds to changed conditions; a forecast keeps the latest
  vintage, exactly as today.
- **Byte-inert while off**, and off for every other ISO. `eia860_vintage_year` keeps its
  current meaning as an explicit override and wins when both are set.

## 2. Screen year, fixed now and chosen on FOOTPRINT

**Screen year = 2021.** Chosen because the mechanism's own measured footprint is largest there —
`ΔCOAL = +9,986 MW` against +3,222 (2022) and −1,605 (2023), from the zero-LP census in FINDING
§3.3. It is **not** chosen for having the largest residual, and no gate below reads the price or
fuel-mix residual.

2021 is **validation tier**. PJM holds the `complete` marker (`calibration-complete.json`,
declared 2026-07-31) and the holdout freeze scope is **locked-test only** since the 2026-08-26
ruling, so the spend is authorized; `--holdout-authorized` is required at launch. The screen
bundle is **never registered** (rule 29 clause 2) and is **deleted before merge** (clause c) —
every number this session will ever cite from it is written into this document or its addendum.

## 3. Control — a same-HEAD control IS earned

Rule 29 (b)'s default is that the incumbent keeper's committed bundle is the control, valid when
a **G-DRIFT** audit classifies every changed solve-path hunk as INERT. **It does not hold here:**

- pjm-166 §6 measured PJM's backcast path **bit-identical** at HEAD `4373b348c` — but that is a
  different HEAD.
- `git diff 4373b348c..82a7742d -- src/market_sim scripts/run_calibration.py
  scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
  is **59 files, +9,088 / −639 lines**, spanning `runner.py`, `pipeline/solve.py`,
  `data/fleet/eia860.py`, `data/fleet/campd_bins.py`, `data/offer_curves.py`,
  `model/commitment.py` and `policy/`. **Not dischargeable at that size** ⇒ treated as **LIVE**,
  which is precisely the case rule 29 (b) says earns a control solve.
- The natural committed control for 2021 is `pjm_tp2022_2021_k162`, solved at `46e08e5b` — also
  drifted, so it cannot serve either.

**Therefore:** control = the keeper recipe at HEAD with the new gate **off**, solved for **2021
only**, in the same session as the arm. Both bundles deleted before merge.

## 4. Pre-registered STOP gates — structural only

The screen may **kill** the arm; it may **never promote** one, and it contributes to no
determination. Gates are evaluated arm-vs-control on the same HEAD, 2021 only.

| # | gate | pass condition | why it is structural |
|---|---|---|---|
| **G1** | fleet identity | arm's PJM COAL registry = **48,708 MW** ± 1 MW; control = **38,722 MW** ± 1 MW | reproduces the §3.3 census inside the solve path — the mechanism moved the object it claims |
| **G2** | direction & order of magnitude | arm coal peak MW **rises** by ≥ 2,000 and ≤ 9,986 vs control | the pre-solve delta is +9,986 MW of nameplate; a deliverable response outside this band means the change is not doing what its arithmetic says |
| **G3** | ceiling released | arm's dispatched coal peak / registry pmax **< 90 %** (control 95.4 %) | the claim is that 2021 is capacity-bound; if the ratio stays pinned the diagnosis is wrong |
| **G4** | phantom capacity gone | arm `ST_GAS` peak ≤ **7,411 MW** (control 8,692 = 117.3 % of the 2021 fleet) | an identity: the model must not dispatch capacity that did not exist |
| **G5** | footprint confined | `nuclear`, `wind`, `solar`, `hydro`, `biomass`, `OTHER` annual energy each move < 1.0 % | the mechanism claims a thermal-registry footprint only |
| **G6** | no non-target load-bearing flip | C2 and C4 do not go PASS → FAIL on 2021 | protective; C1/C3a/C3b are the **targets** and are **not gated** |
| **G7** | EMAAC not made worse by construction | arm slack MWh ≤ control slack MWh | defect 2 is untouched by F1, so its artifact must not grow |

**Not gates, reported only:** C1 `CC_REGULAR`/`ST_GAS`/`COAL_BIT` deltas, C3a, C3b, C3c, mean
LMP. Reading any of these as a pass condition would be the fitted-mechanism selection rule 1
`[R-STRUCT]` forbids, one year at a time.

**Kill rule.** Any of G1–G7 failing ⇒ the arm is dead, that is the session's result, and the
remaining years are never spent.

## 5. If the screen clears

1. **Protective in-sample check first, before any promotion.** Re-solve **2023–2025** with the
   gate armed (one `--year 2023 2024 2025` invocation, one bundle). The census says 2023 loses
   1,605 MW of coal and 5,786 MW total, so this **is not a free input repair** — it can move the
   keeper and must be scored leave-one-year-out within 2023–2025 (rule 22) before anything is
   promoted. A determination that is worse stops the promotion.
2. Only then re-run the 2021/2022 touchpoints on the new recipe and **fold them to the keeper**
   (rule 30 `[R-TOUCHPOINT-FOLD]`: `stamp_touchpoint_holdout.py`, then `build_status.py --iso PJM`).
3. Add the missing `eia860_vintage_year` / new-gate row to
   `docs/codebase-site/data/mechanism-matrix.js` plus a cell in every ISO shard, in the same PR
   (rule 32 duty (c)), and stamp PJM's shard with the verdict (duty (b)).
4. Correct the `eia860_vintage_year` docstring: its *"measured effect is small (~0.4 % of ERCOT
   installed capacity)"* was assessed on ERCOT inside 2023–2025. For PJM 2021 it is **39 % of the
   coal fleet**.

## 6. Explicitly out of scope here

F1b (`RETIREMENT_WINDOW_START` → 2019 + `partial_plant_exit_carry`; needs the raw EIA-860 release
zips, not on disk), F2 (EMAAC interface intake — screened **after** F1 or the two confound), F3
(Linden/Bayonne BA attribution), F4 (offer-anchor extrapolation, screen year 2022). Each earns
its own PRECOMMIT.
