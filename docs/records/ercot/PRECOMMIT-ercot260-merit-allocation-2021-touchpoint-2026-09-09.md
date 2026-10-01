# PRECOMMIT — the 2021 validation touchpoint re-test of `netload_drag_merit_allocation` (ercot-260, card 2)

> **Pushed before the LP runs.** Every gate, the control basis, the drift
> evidence, the decision rule and all five predictions are registered here,
> upstream of the solve.

## 1. What this is, and what it is NOT

This is a **rule 22 `[R-HOLDOUT]` validation touchpoint re-test** — step 4 of the
touchpoint loop (*"re-test the touchpoint to see whether it resolved"*) — **not**
a rule 29 `[R-SCREEN]` screen. The distinction is binding on how the year is
chosen:

* The mechanism is **already built and already screened**. ercot-259 screened it
  on **2023**, named ex ante on the mechanism's own largest footprint (1.4270 TWh
  of mandated MW changing hands), and it cleared all five STOP gates with the
  reallocation reproducing the zero-LP census to ratios **0.994–1.015**. Its
  arithmetic is not re-litigated here.
* **2021 is chosen because it is the held-out year whose C8 gate FAILS** — the
  breach the mechanism was built to close (`0.3313` against a `0.30` cap). Under
  rule 29 that choice would be residual-driven and forbidden; under rule 22 it is
  the *definition* of a touchpoint. Owner directive, 2026-09-09, verbatim:
  *"If it improves then screen 21 and decide on promotion. We should only be
  running 2021 now since it's the only miss year."*
* **Nothing is identified, fitted or tuned on 2021.** The mechanism's parameters
  were derived on 2023–2025 and are frozen. This measures an already-frozen
  recipe on a held-out year, which is precisely what rule 22 permits and what
  makes the number diagnostic evidence rather than a skill claim.

Rule 22 authorization: ERCOT holds the **`complete`** marker (declared
2026-08-31), which authorizes the 2020–2022 validation ladder; the holdout
**freeze** scope is `tiers: ["locked_test"]` only, so the validation tier is not
frozen. The solve passes `--holdout-authorized`. 2019 / H1-2026 are untouched.

## 2. What is solved — ONE LP

The keeper `results/calibration/ercot256_five_year_keeper` replayed on
**`--year 2021`** (its **carve-out** recipe) plus **`--netload-drag-merit-allocation`
and nothing else**. Written outside `results/calibration/`; **never registered**
(rule 29 clause c / rule 31 `[R-RETAIN]` — a touchpoint probe is not a keeper).

**This solve is only correct because of card 1.** Before this session's fix, a
`--replay-bundle` of a carve-out year silently solved the FORWARD config; the
2021 leg needs `ercot_offer_swcap_clip=true` and the ×33.0 `offer_curve_by_group`
peak bands, which no `meta.json` recorded. That is now consumed automatically and
**proved bit-identical on 2023**.

## 3. CONTROL — the keeper's committed 2021 leg (G-CTRL form 4). No control solve.

Rule 29(b): *"stop doing control solves … just use the last keeper as the
control."* The control is the keeper's own committed 2021 artifacts
(`hourly/class_hourly_2021.parquet`, `hourly/system_2021.parquet`,
`legitimacy_diagnostics.json`).

**G-DRIFT is MEASURED here, not audited.** The usual question — has the solve
path moved between the keeper's `git_sha` and HEAD? — was answered empirically
by this session's card-1 proof: a replay of the keeper at HEAD reproduced its
committed **2023** leg **bit-identically** (61,320 P1 zone-hour rows, max \|Δ\|
`0.000000e+00` on price, demand, slack, dump, reserve price). That is strictly
stronger than a hunk-by-hunk classification. **Stated residual:** it exercises the
shared ERCOT backcast path, not any 2021-specific branch, so a year-scoped code
change would not be caught by it; no such change is known.

## 4. GATES — STOP-only, structural, and NEVER read against the target

A gate may **kill** this arm; none can promote it. C8 is the target criterion and
is therefore **NOT a gate** (rule 1 `[R-STRUCT]` — gating on the target is the
fitted-mechanism selection the rule forbids); it is **reported at full
magnitude** in §6 instead.

| gate | test | STOP threshold |
|---|---|---|
| **G-A feasibility** | LP slack and dump, 2021 | either > 0.0000 TWh ⇒ STOP |
| **G-B footprint confinement** | annual TWh of every class the drag does **not** own, arm vs the keeper's committed `class_hourly_2021.parquet` | any non-ST_GAS, non-gas-displacement class moving > **0.15 TWh** ⇒ STOP |
| **G-C mandate neutrality** | total drag-mechanism mandated MWh in the arm's `floors/2021_P1.npz` vs the analytic `Σ_t floor_frac(t)·Σpmax` the frozen drag curve implies | relative error > **0.5 %** ⇒ STOP |

G-B's threshold is set from ercot-259's measured 2023 non-target maximum
(0.026 TWh, CC_CHP `chp_steam`) with headroom for 2021's different fleet; it is
**not** tuned to any 2021 quantity, none of which has been observed.

## 5. DECISION RULE — registered before the solve

Read on **2021 ST_GAS C8 forced share**, keeper control **0.3313**, cap **0.30**:

* **falls below 0.30** ⇒ the arm **resolves** the 2021 breach ⇒ **recommend PROMOTE**, and the full-span re-solve is the next step.
* **falls but stays ≥ 0.30** ⇒ **partial**: the breach is not closed but the direction is right ⇒ report and put to the owner, no recommendation either way.
* **rises** ⇒ the arm makes the failing gate **fail harder** ⇒ **recommend AGAINST promotion**, and the remaining years are **not** spent.

Rule 30(c) is noted and does not apply as a defence here: a validation-tier
result never downgrades ERCOT's determination, and this session will not claim it
does — the ISO's headline is its 2023–2025 train-tier verdict either way.

## 6. PREDICTIONS — registered, and scored honestly whichever way they fall

| # | prediction |
|---|---|
| **P1** | 2021 ST_GAS C8 forced share **RISES** from 0.3313 and **stays FAIL** (> 0.30). Basis: the mechanism is mandate-neutral but not *realized-forcing*-neutral — flooring a cheap plant at its full committed block is a higher bar than 15 % of `pmax`, so it binds where the smear did not (measured on 2023: 0.1340 → 0.1775, **+4.3 pt**). |
| **P2** | Plant **3452**'s D-4 row: floored energy and binding hours fall **≥ 40 %**, and the conviction **does NOT clear** (measured median in binding hours stays 0.000 MW). Basis: the 2023 measurement, −55 % on both with median unmoved. |
| **P3** | System load-weighted mean LMP **RISES**, by **< $2.00/MWh**. Basis: 2023 rose +$0.1422/MWh; 2021 is a higher-priced year so the same mechanism scales up, but not by an order of magnitude. |
| **P4** | ST_GAS annual class energy **FALLS**, by **< 1.5 TWh** (2023: −0.605 TWh on a 19.0 TWh class; 2021's class is 11.2 TWh). |
| **P5** | **No** non-target load-bearing criterion flips PASS → FAIL. Note 2021's C3a already **FAILS** at +26.4 % in the keeper, so it cannot flip; the live risk is C1/C2/C4. |

**Ex-ante statement of the likely outcome, so the result cannot be re-framed
afterwards:** P1 says this arm is expected to make the 2021 gate **worse**, which
under §5 means **recommend against promotion**. The run is worth its 30 minutes
because 2021 is the only year that can settle it and has **never been measured**
for this mechanism — ercot-259 could only predict it from 2023, and predicted the
2023 C8 direction **wrong**. If P1 is wrong and the share falls, that is a real
result and §5 says promote.

---

*Generated by [Claude Code](https://claude.ai/code)*
