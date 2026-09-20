# PRECOMMIT caiso-294 — the CHP steam floor's LEVEL: ARM A measured and falsified, ARM B declared

**Lane:** caiso-294 · **Date:** 2026-09-20 · **Keeper:** `2026-09-20-caiso-290-leftedge`
(bundle `xiso8_leftedge_span`, 2022–2025, DETERMINATION CALIBRATED with a single ledgered C3c).
**Phase 0 LP spent: ZERO** (rule 32 `[R-SHARD]` (a) — the parent never solves).
Predecessor: `docs/PRECOMMIT-caiso293-chp-steam-duty-window-2026-09-20.md` +
`docs/RESULT-caiso293-the-chp-steam-floor-is-an-energy-average-2026-09-20.md`.

**This document is pushed BEFORE the ARM B level statistic is computed.** §3 declares the
percentile ex ante; §5 declares the D-4 outcome ex ante. Nothing in either is swept
(rule 1 `[R-STRUCT]`).

---

## 0. The answer in one paragraph

**ARM A does not do what the lane instruction says it does, and the arithmetic was
checkable before any solve.** The instruction described windowing the diluted level as
"energy-conserving by construction, so G-4 passes trivially". It is not:
`steam_level_cf` is *already* `on_freq × p50(loading-when-on)`, so holding **that** level in
`on_frac` of the hours delivers `on_frac² × p50(on) × H` — the on-frequency is applied
**twice**. Measured on the keeper's own fleet at zero LP, ARM A **removes 80.4–83.8 % of the
class-A/B forced energy** in all four years and also breaks the control gate G-3 in 2022.
It is not a partial repair of the level; it is an ~82 % **deletion** of the floor with a token
residue left in the right hours, and the level it leaves behind is no more physical than the
one it replaces. **ARM B — a never-below-when-online level — is therefore the only arm that
repairs what caiso-293 diagnosed**, and it needs the owner's ruling because it re-runs a frozen
derive (rule 23 `[R-FROZEN-DERIVE]`).

---

## 1. Inherited and reproduced (zero LP)

`scripts/probes/caiso293_gates.py`, re-run unchanged on this tree against the committed
keeper bundle. Every published caiso-293 number reproduces:

| gate | 2022 | 2023 | 2024 | 2025 | verdict |
|---|--:|--:|--:|--:|---|
| **G-1** identity, max abs err over all 13 ISO artifacts | — | — | — | — | **PASS** (0.000000) |
| **G-3** flat-host control, %/yr | 0.831 | 0.363 | 0.505 | 0.050 | **PASS** (< 2 %) |
| **G-4** cyclers energy, %/yr | +4.714 | +3.085 | +6.334 | **−10.220** | **FAIL** (2025) |

G-2 off-inertness is the two-version snapshot diff (`caiso293_g2_snapshot.py`), re-run in §4.
The in-process form is mis-specified by design and is not used.

**Settled, not re-derived** (caiso-293 §1–§3): the defect, the membership falsification, the
level-source falsification, the gross-load window adjudication (lift 5.29 vs 4.55 net-load vs
3.69 own-duty-surface), and the 1,261.879 MW / 7.99–9.22 TWh-yr sizing over 41 plants.

---

## 2. ARM A — MEASURED, AND FALSIFIED ON ITS OWN PREMISE

Probe: `scripts/probes/caiso294_arm_a_energy.py`. ARM A is reached without touching `src/`:
`fleet/assembly.py` consumes the loader's `(on_frac, level_on_cf)` pair as
`chp_duty_on_frac, pmin_cf`, so returning `(on_frac, on_frac × level_on_cf)` puts the level
exactly where the unarmed path puts it (`steam_level_cf`) and moves only the hours. One
respect differs from the control; nothing else.

| year | class A+B forced TWh, keeper | **ARM A** | Δ | **ARM B** (caiso-293, undiluted) | Δ |
|---|--:|--:|--:|--:|--:|
| 2022 | 0.1908 | **0.0374** | **−80.41 %** | 0.1998 | +4.71 % |
| 2023 | 0.1883 | **0.0333** | **−82.30 %** | 0.1825 | +3.08 % |
| 2024 | 0.2412 | **0.0443** | **−81.62 %** | 0.2259 | +6.33 % |
| 2025 | 0.1786 | **0.0290** | **−83.79 %** | 0.1604 | −10.22 % |

And the control gate moves too — ARM A is **not** the measured no-op on the three flat steam
hosts that made caiso-293's arm defensible:

| G-3, flat hosts | 2022 | 2023 | 2024 | 2025 |
|---|--:|--:|--:|--:|
| caiso-293 ARM B | 0.831 % | 0.363 % | 0.505 % | 0.050 % |
| **ARM A** | **2.294 % FAIL** | 1.914 % | 1.841 % | 1.690 % |

**ARM A fails G-4 by eight times the bar in every year and fails G-3 in 2022.** Both are
pre-registered hard STOPs (caiso-293 §4), inherited verbatim by §4 below.

**The structural reading, which is the one that decides it (rule 1 `[R-STRUCT]`).** The owner's
standing guidance is that a gate regression does not by itself kill an arm whose structural
integrity improves. ARM A does not qualify, because its *structure* is the problem rather
than its score: the object it produces says "in the top ~5 % of load hours this cogen must
produce at ~2 % of nameplate". That is neither the plant's steam obligation nor its commercial
output — it is the annual energy average, which is too low by a factor of `on_frac` in exactly
the hours it binds. The diagnosis caiso-293 published is that the floor's **magnitude** is an
energy average worn as an hourly level; ARM A keeps that magnitude, divides the hours, and
therefore makes the magnitude error **worse** while removing four-fifths of the floor. A
deletion is a legitimate outcome for these plants (caiso-293 §4 option 3) — but it should be
taken deliberately and named, not arrived at through a mechanism that presents itself as a
window.

**ARM A is recommended AGAINST and is not carried forward.** The measurement stands in the
record either way.

---

## 3. ARM B — THE LEVEL, DECLARED EX ANTE

> **THE PERCENTILE IS DECLARED HERE, BEFORE IT IS COMPUTED, AND IT IS NOT SWEPT.**
>
> **ARM B's level is `p2` of the ONLINE loading distribution** — i.e. the existing
> `_CHP_PMIN_PCTILE = 2` applied to `on_cat` instead of `all_cat`. New artifact column:
> **`chp_pmin_on_cf`**, the exact sibling of the committed `chp_pmin_cf`.

**Why p2, decided by construction rather than by a result.** `chp_pmin_cf` is this repo's
never-below convention for a CHP host floor: the 2nd percentile, low enough to shed CEMS
metering noise and high enough to be the level the plant does not go below. It is taken over
the **wrong sample** — all hours — which is why it reads `0.0` for every one of these ten
plants and why WP-3 armed the `steam_level_cf` swap to escape that degeneracy. ARM B changes
**the sample and nothing else**. It introduces **no new number**: the percentile is the one
already in the file, the sample is the one `median_cf` and `p25_cf` already use, and the mask
is the same `online` mask the deriver already builds. Under rule 21 `[R-DOF]` the DOF ledger
gains **zero** free parameters.

**Why not `p25_cf`, which would need no derive change at all.** Because the only argument for
it would be that it lands between p2 and p50 — i.e. that it clears G-4 — and selecting a
statistic because it makes a criterion pass is the fitted-mechanism selection rule 1
`[R-STRUCT]` forbids. caiso-293 refused that swap for this reason and this lane inherits the
refusal. A quartile of the online distribution is not a never-below level in any case.

**What ARM B is, in one line each (rule 17 `[R-FLOOR-WINDOW]`):**
* **(a) driver** — the plant's measured synchronization fraction (window) and its measured
  never-below-when-online loading (level), both from the same pooled CAMPD sample.
* **(b) hours** — the top `on_frac × live-hours` of the shared commitment-floor window series
  (gross load), the construction `coal_sync_online_frac` and `cc_mustrun_online_frac` already
  use, adjudicated in caiso-293 §3 against two alternatives.
* **(c) forward story** — both factors re-derive from the next CEMS vintage with no model
  input and respond to changed conditions; rule 13 `[R-MEASURED]` forward-valid, not
  backcast-only.

**What it costs, stated at the gate.** ARM B **re-runs a frozen derive and adds a column**, so
rule 23 `[R-FROZEN-DERIVE]` is engaged and the owner's ruling is required before any committed
artifact byte moves. The motive is a structural defect that caiso-293 measured, not a residual
that moved — which is the admissible ground — but it is not this lane's call. The emit is
purely additive: every existing column is asserted byte-identical by G-5 below, so no
*existing* measured parameter is re-identified.

**Known risk, declared before the number is seen.** p2 of the online sample includes start and
stop ramp hours, so on a plant that ramps through min-load on every start it can read low —
possibly low enough that the floor becomes small or inert. **That is a legitimate outcome and
will be reported as measured.** It is not a reason to move the percentile.

---

## 4. GATES — caiso-293's, INHERITED VERBATIM, PLUS ONE

| id | gate | bar | STOP? |
|---|---|---|---|
| **G-1** | Identity `\|on_frac × median_cf − steam_level_cf\| ≤ 0.05` on every `status=="ok"` CHP row of every ISO artifact | all rows | **yes** |
| **G-2** | Off-inert: gate OFF ⇒ `min_gen` / `min_gen_mechanism` / `chp_grid_pmin_mw` / `pmax` **bit-identical** to HEAD, all four years, by TWO-VERSION SNAPSHOT DIFF | exact | **yes** |
| **G-3** | Control inertness: gate ON ⇒ class-C flat-host forced energy moves **< 2 %** per year | < 2 % | **yes** |
| **G-4** | Energy conservation: class A+B forced energy moves **< 10 %** per year | < 10 % | **yes** |
| **G-5** | *(new, ARM B only)* Derive re-run is **purely additive**: every pre-existing column of every regenerated artifact is byte-identical; only `chp_pmin_on_cf` appears | exact | **yes** |
| **G-6** | D-4 `chp_steam` failing rows against §5's declared prediction | see §5 | no |
| **G-7** | C1 `CC_CHP` / `CT_CHP` volumes, C3a, belly | **reported at full magnitude** | no |

G-1…G-5 are **zero-LP** and all run in the parent before any shard is launched (rule 32(a)).
G-2's in-process form is mis-specified by design; the snapshot diff is the only form used.

---

## 5. THE D-4 PREDICTION, DECLARED EX ANTE

Probe: `scripts/probes/caiso294_d4_prediction.py`, computed from the arm's **own composed
`min_gen` arrays** rather than from an analytic pooled window — tighter than caiso-293's
28 → 20, which was scored on the pooled placement artifact.

**The prediction is LEVEL-INDEPENDENT and therefore covers both arms.** The per-unit conduct
rider convicts on `median(measured MW over the hours the floor binds) ≤ 0`; the statistic reads
an **hour set**, and the floor's magnitude never enters it. ARM A and ARM B place the floor in
identical hours (same `on_frac`, same window series, same top-k-by-load rank), so they carry the
same D-4 prediction.

> **DECLARED: the MECH_CHP_STEAM conduct-rider failing rows fall from 28 to 16 across
> 2022–2025** — per year **7 → 2 / 7 → 5 / 7 → 4 / 7 → 5**. The 12 plant-years predicted to
> clear are `10649-{2022,2023,2024,2025}`, `10650-{2022,2024}`, `54768-{2022,2025}`,
> `10294-{2022,2023}`, `54749-{2022,2024}`. Per-plant detail in
> `results/calibration/_caiso294_d4_prediction.json`.
>
> The probe **reproduces the keeper's committed 28 failing rows exactly** (7 per year, all
> four years) on the control leg, which is what validates its construction. Against
> caiso-293's pooled-window estimate of 28 → 20 this is **more optimistic, and its twelve
> clearing plant-years are a strict superset of caiso-293's eight** (the four additions are
> `10294-{2022,2023}` and `54749-{2022,2024}`) — the expected
> direction, because the hour set here is the one `arrays.py` actually floors (availability
> clip included) rather than an analytic pooled window.
>
> **NEITHER ARM IS EXPECTED TO CLEAR D-4, and that is not a reason to abandon the repair**
> (rule 1 `[R-STRUCT]`; D-4 is not gating this keeper's determination, which reads CALIBRATED
> with D-4 FAIL pre-existing). The two named, un-absorbed reasons are caiso-293 §5's and are
> inherited unchanged: the pooled `on_frac` is a 2023–2025 average over plants whose
> on-frequency collapsed across the window (`mustrun_online_frac_per_year` is the identified
> successor), and a load-ranked window cannot reach precision 1.0 on a unit-specific
> economic dispatch.

**The approximation, stated rather than buried.** The real rider scores
`at_floor_mask(dispatch, min_gen, npl)` — the floored hours where the *solved* dispatch sits at
the floor — and there is no dispatch without an LP. The probe scores the full floored-hour set
(`min_gen > 0`), its superset. The direction is known: hours the LP lifts off the floor are
hours the unit is economic, hence hours it is more likely metered ON, so excluding them can
only lower the median. **The declared prediction is therefore the conservative one** — the solve
may clear more rows than predicted, not fewer.

`D4_WINDOWS[(MECH_CHP_STEAM, None)]` **stays `(0, 24)`** and is not narrowed: the repair's
window is a top-k-by-LOAD rank, not an hour-of-day band, so D-4's window test cannot express it
in either direction. The per-unit conduct rider is what binds.

---

## 6. D-5 — CLEARED, AND IT IS A DECLARATION, NOT A REPAIR

**Landed in this lane; no solve, no gate, no model change.** The keeper's single D-5 failure is
`caiso_ra_mustoffer`: `D5_REGISTRY` declares it `mode="both"`, and the symbol
`caiso_ra_mustoffer_min_gen` is called **twice in `scripts/run_calibration.py` and zero times in
`src/market_sim/runner.py`** (measured, this tree), so the gate saw a backcast-only mechanism
that was not on the declared list.

It is **not a measured overlay**. The bridge reads the model's **own base-cost P0 run pattern**
against the **physical** `CC_COMMITMENT_PARAMS` min-down time, so no measured outcome enters and
it is rule-13 admissible in both modes. The difference is a forecast **wiring gap**
(`w2-caiso-ra-p2`), and the fix is the same posture the `reliability_floor` row already carries:
declare the gap, keep the row visible at `verdict: "declared"`, and name the closure rather than
absorb it. Landed:

1. `docs/backcast-measured-data-audit-2026-06.md` — new section stating what the gap is, why the
   mechanism is admissible, **what the declaration costs** (a CAISO forecast year carries no RA
   must-offer commitment while every CAISO backcast year does — the modes do not run the same
   mechanism set, and the declaration records that rather than claiming it harmless), and the
   named closure.
2. `scripts/legitimacy_diagnostics.py::D5_REGISTRY` — `declared=True` on that one row.
3. `tests/scoring/test_legitimacy_diagnostics.py` — `test_wiring_gap_fails` **retargeted, not
   deleted** (rule 26 `[R-DELETE]`) onto `gas_st_netload_drag`, which is still undeclared and
   still `mode="both"`, so the guard against a *future* undeclared wiring gap is intact; plus a
   new `test_caiso_ra_mustoffer_is_declared` pinning the reported-not-failed posture.

Measured after the change: **D-5 failures `[]`, 12 rows, 0 FAIL rows** on the keeper's own
run-config. The mechanism is the only committed run-config in `results/calibration/` carrying
the flag, so no other ISO's scoring moves. **The committed keeper bundle's
`legitimacy_diagnostics.json` still reads D-5 FAIL** until the bundle is regenerated — the
scorer is fixed, the artifact is a snapshot.

Closing the wiring gap for real is a **forecast-path model change** that arms an extra `min_gen`
bridge in every CAISO forecast and hindcast year. It needs its own PRECOMMIT, its own gates and
an owner ruling, and is deliberately **not** bundled here.

---

## 7. D-1 — MEASURED IMMATERIAL, SO NOTHING IS SPENT ON IT

The keeper's two D-1 failures are `2024 ST_GAS profile r 0.468` and `2025 ST_GAS r −0.036`.
The standalone C7 diurnal gate was retired at rubric v3.1; D-1 now binds only through rule 19
`[R-FORCED-BUDGET]`'s shape leg, which applies to classes at **≥ 2 % of ISO load** measured as
`max(model, actual)`. Measured from the keeper's committed hourly sidecars and the CAMPD bench:

| year | ISO load TWh | 2 % bar TWh | ST_GAS model TWh | ST_GAS **actual** TWh | max/load |
|---|--:|--:|--:|--:|--:|
| 2022 | 219.538 | 4.391 | 0.331 | 1.339 | **0.61 %** |
| 2023 | 207.473 | 4.149 | 0.080 | 1.384 | **0.67 %** |
| 2024 | 212.162 | 4.243 | 0.086 | 0.086 | **0.04 %** |
| 2025 | 204.837 | 4.097 | 0.013 | 0.056 | **0.03 %** |

CAISO `ST_GAS` never reaches a third of the materiality floor, and **in the two failing years it
is 0.04 % and 0.03 % of load — 50–150× below the bar**. Rule 19's shape leg does not bind it, so
the D-1 rows are report-only and **no structural work is spent on them**. Recorded so the next
lane does not re-open the question.

---

## 8. WHAT A SOLVE WOULD COST, AND HOW IT WOULD BE RETRIEVABLE

Only if the owner rules ARM B in. Rules 32 / 34 / 36: **one year per shard, own container,
`--years <single year>`, `source_url` plus a full 40-character `source_revision` pinned to this
document's commit.** CAISO's registered year set is **2022–2025**, so **four shards, all of
them** (rule 34(c); the registry carries no other CAISO year). Each shard pushes its **whole**
bundle including `dispatch/<year>_P1.parquet` via a `.gitignore` negation plus a **plain**
`git add` — never `-f`, never `-A` (rule 34(a)); each builds the curated deliverability
partition first (`PYTHONPATH=.:src python scripts/data/curate_capacity_deliverability.py
--isos CAISO`, 386 rows — `hydrate_data.py` does not build it and the keeper arms
`capacity_deliverability_limits`). The parent composes, scores and registers **once**, and
archives each shard only after fetching, checking out and verifying its bundle (rule 33(a)).

**Retrievability (rule 34(e)):** nothing to retrieve today — **no solve has been run and no
bundle exists.** The probe artifacts (`results/calibration/_caiso294_*.json`) are gitignored and
every number they carry is reproduced in this document.

**G-DRIFT (rule 29 `[R-SCREEN]` (b)):** not spent — no arm has been solved, so no control is
needed. caiso-292's audit (every CAISO solve-path hunk INERT) stands unextended and is cited by
no number here. It would be extended to this lane's base before any shard.

---

## 9. THE DECISION THIS LANE OWES THE OWNER

1. **ARM A is falsified on its own premise** (§2) — measured, not argued. Recommended against.
2. **ARM B needs the rule-23 ruling** (§3) — a purely additive `chp_pmin_on_cf` column at the
   already-committed `p2`, declared above before computation. This is the only arm that repairs
   the diagnosed defect.
3. **Option 3 stays open and is not this lane's to take** (caiso-293 §4): conclude these ten
   plants carry no steam floor at all. It is adjacent to the unruled
   `caiso_ra_bridge_startup_aware` question. ARM A's measurement is *evidence* for it — an 82 %
   deletion is most of the way there — but it should be taken as a deliberate deletion with its
   own justification, not as a side effect.
4. **D-5 and D-1 are settled in this document** (§6, §7) and depend on none of the above.
