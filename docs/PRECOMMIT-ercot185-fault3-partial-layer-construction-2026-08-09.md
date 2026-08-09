# PRECOMMIT — ercot-185: the FAULT-3 PARTIAL-LAYER CONSTRUCTION re-charter

**Pre-registered and pushed BEFORE any measurement, any derive run, and any
solve.** Decision rules, the construction, its measured basis, the DO-NOT-REDO
check, the seam proofs, the pre-solve screen and the kill gates are fixed here
and are **not renegotiated after measurement**. Keeper at session start:
`2026-08-09-run181-position-tail` (bundle
`results/calibration/ercot181_positiontail_B`), **NOT-YET {C3a, C3b}**.

---

## 0. Authorization, scope, and what this session may NOT do

**Signed authorization** — owner sitting 2026-08-09, decision card D2, option C.
Ruling recorded verbatim
(`docs/DECISION-CARD-ercot182-c3a2023-reachability-2026-08-09.md` §4 + §10):

> *"The ceiling lane stays frozen for composition-rule work; a fault-3
> partial-layer construction re-charter is authorized as its successor, with
> G-COAL148 carried live."*

**Rule 23 `[R-FROZEN-DERIVE]` trigger, stated before the derive is touched.**
The trigger for re-deriving the partial-outage extract is **(a) the SIGNED OWNER
RULING above and (b) the ercot-172 fault-3 measurement** — a multi-week average
plateau applied as an hourly ceiling, measured at MW grain across nine named
plants (`FINDING-ercot172` §3/§4). It is **NOT** a residual. No bar, band,
window or constant in this session moves because a metric moved. The derive
commit cites this paragraph.

**Scope fences (binding):**

* **ERCOT only** (rule 25 `[R-ISO-SCOPE]`). No other ISO's cell, extract,
  keeper or artifact is read or written.
* **`--year 2023 2024 2025` only, ONE invocation, years sequential** (rules
  12/16/22). ERCOT holds **no** `complete` and **no** `final` marker, so 2019,
  2020, 2021, 2022 and H1-2026 stay quarantined, unsolved and unread.
* **ERCOT-148/149 is NOT repealed.** The product cap stays armed. If the
  repaired layer makes the double-count removal safe, that removal is a
  **separate later adjudication**, explicitly not this session's.
* **No composition change of any kind.** This session changes how ONE layer is
  *constructed*; the `f_window × f_partial` composition is untouched.

---

## 1. The object — ercot-172 fault 3, at code grain

`scripts/lib/outage_detect.py::_detect` emits, per detected plateau spanning
days `[i, j)`:

```python
ceiling = float(np.median(dmax[i:j]))                 # ONE number for the whole window
out.append((i, j, round(min(1.0, ceiling / ref), 3))) # applied to every hour of every day
```

`derive_partial_outages.py` writes that single `derate_factor` on one row
spanning the whole plateau; `outages.py::partial_outage_derate_factors` expands
it to a flat `(hours,)` array; `fleet/arrays.py` multiplies availability by it
(line 1346) **and** composes it into the ERCOT-148/149 event-cap ceiling (line
1743). So a **multi-week median of daily maxima is imposed as an HOURLY
availability ceiling**.

The measured consequence (`FINDING-ercot172` §3): W A Parish carries a single
`derate_factor 0.363` spanning 2024-03-04 → 2024-05-04; at h2827
(2024-04-28 19:00 CST) the composed ceiling reads **0.2539** against the plant's
own same-hour fuel-matched CEMS of **0.7843**. Martin Lake 0.502 over
04-10 → 06-06; J K Spruce 0.208 over 04-24 → 05-04; Guadalupe 0.482; Sandy
Creek 0.485. `FINDING-ercot174` §3b item 3 names this **the only remaining
structural route to the 2024 object**, untouched by any composition rule.

**Target** (stated, not promised): C3b-2024 **0.205 → ≤ 0.20** without
disturbing 2023 or 2025.

---

## 2. THE CONSTRUCTION — the day-shaped plateau derate

### 2a. What it is

Replace the plateau's single flat `derate_factor` with a **day-resolved derate
series over the same plateau**, taken from the detector's **own** smoothed
daily-ceiling statistic:

```
incumbent :  derate(d) = median(dmax[i:j]) / ref            for every day d in [i, j)
SHAPED    :  derate(d) = min(1.0, sm[d] / ref)              for each day d in [i, j)
```

where, **imported verbatim from the frozen detector and never re-valued**:

* `dmax[d]` — the day's maximum capacity factor (the plant's revealed daily
  ceiling), the detector's own statistic;
* `sm = pd.Series(dmax).rolling(_SMOOTH_DAYS, center=True, min_periods=4).median()`
  — the detector's own centered 7-day rolling median of `dmax`, **the exact
  series the detector already thresholds on to decide plateau membership**
  (`partial = running & (sm < _CEILING_FRAC * ref)`);
* `ref` — the detector's own normal ceiling, the 90th percentile of `dmax` over
  running days (`dmean > _RUN_FLOOR_CF`).

The incumbent is the **window-median coarsening of exactly this series**. The
change is therefore a **grain refinement of one measured statistic**, formally
the same class of change as the ercot-174 unit-attribution (proved grain-only
by BE-1/2/3) — one grain finer in **time** rather than in **unit**.

### 2b. Why `sm[d]` and not `dmax[d]` — stated before measurement

A pure per-day `dmax[d]` would be maximally hourly-faithful and **structurally
wrong**: on a day the plant chose not to run hard, `dmax[d]` is low and the
derate would book **economic part-load as unavailability** — the exact defect
class the ERCOT-79 revealed-availability filter exists to prevent. `sm[d]` rides
through single-day blips in **both** directions and is already the detector's
plateau-membership statistic, so it introduces nothing. This choice is made on
structural grounds (rule 1 `[R-STRUCT]`), before any residual is seen, and is
not revisited if a metric disagrees.

### 2c. Why CEMS-shaped and not duration-scoped

The charter names two candidates. **Duration-scoping is refused here on a
governance ground, not a performance one:** shortening or splitting the detected
windows would **restrict the event-window population**, which trips **G-NEUT**
(the ercot-171 gate: any proposal restricting the event-window population must
clear G-NEUT *before* it may be built — `FINDING-ercot172` §4). The day-shaped
construction restricts **no** population: same plateaus, same spans, same
covered hours, only the within-window profile changes. **G-NEUT is therefore not
reached**, exactly as it was not reached for C1/C2.

### 2d. Rule 13 `[R-MEASURED]` admissibility

The shaped derate is an **availability envelope**, not an outcome pin.

* It is built from `dmax` — the plant's revealed **daily ceiling** (capability),
  smoothed — never from the hour's own output. It does not encode *when* the
  plant chose to run, only *how high it could reach* in that period.
* It is **not** ercot-172's C3 ("floor the ceiling at the plant's
  contemporaneous output"), which that FINDING flagged as least admissible and
  recommended against. C3 reads the hour's own outcome; this reads a smoothed
  multi-day capability statistic the detector already computes.
* Rule 13's test — *could this quantity be produced for a forward year from
  forward drivers, and would it respond to changed conditions?* — is answered
  identically to the incumbent flat plateau it replaces: run the same detector
  on the year's CEMS. It is regenerable exactly as the incumbent is, and neither
  reads the model's own output.

### 2e. Zero DOF (rule 23 `[R-DOF]` / G-DOF)

`_MIN_DAYS`, `_SMOOTH_DAYS`, `_CEILING_FRAC`, `_RUN_FLOOR_CF` are imported from
the frozen detector and never re-valued. `ref` is the detector's own. **No new
scalar of any kind is introduced.** The 3-dp rounding of the emitted
`derate_factor` is the incumbent's own `round(..., 3)`.

### 2f. Wiring — the smallest change that carries it

* **Deriver**: `scripts/data/derive_partial_outages.py --emit-shaped` writes
  `data/raw/campd-partial-outages-shaped.csv` in the **identical 7-column
  schema**. Each plateau is emitted as consecutive **day sub-windows** whose
  derate is constant after 3-dp rounding; the last sub-window inherits the
  plateau's own `outage_stop` verbatim (including the incumbent's
  end-of-horizon clamp), so the covered hour set is identical by construction.
  The committed plant-grain `campd-partial-outages.csv` is **written unchanged**
  by the same run.
* **Loader**: `partial_outage_derate_factors(..., shaped: bool = False)` reads
  the shaped file when `shaped=True`. **No other loader logic changes** — the
  existing per-row `arr[mask] = np.minimum(arr[mask], derate_factor)` already
  handles many rows per plant.
* **Config**: `ScenarioConfig.ercot_partial_outage_shaped_derate: bool = False`,
  one gate, registered in the cache-key default-drop list and in the mechanism
  matrix in the same PR (rules 24 / 28c).
* **Consumers**: BOTH ERCOT consumers of the layer see the repaired layer —
  the base availability derate (`arrays.py` ~1333) and the event-cap ceiling
  (`arrays.py` ~1743). That is deliberate and rule-19 `[R-ONE-MECH]`-clean: one
  layer, one construction, one repair.

---

## 3. DO-NOT-REDO check (rule 28a) — pre-registered

| dead arm | what it was | why this is not it |
|---|---|---|
| blanket `min()` (ercot-173, **R**) | **composition** rule over two layers | this changes the **construction of one layer**; composition untouched |
| unit-scoped `min()` (ercot-174, stopped, ρ=0.94–0.96) | **composition**, unit-conditioned | same — no composition rule is read or written |
| finer-grain-wins (named, not built) | **composition** | same |
| ercot-172 C3 (contemporaneous-output floor) | outcome pin, rule-13 inadmissible | §2d: capability statistic, not the hour's outcome |

**The categorical difference, stated so it can be falsified.** Every composition
arm is **restore-only** — ercot-174 SP-5 proved `product ≤ unit-scoped ≤ min`
pointwise, so those arms can only lift the ceiling. The shaped construction is
**two-sided within each plateau**: it lifts the derate on days whose smoothed
ceiling sat above the window median and **lowers** it on days below. If
measurement shows it is in fact restore-only, it is behaving like the rejected
family and §5 is the binding response.

**Reported DO-NOT-REDO evidence (measured, non-selecting):**

* **ρ_shaped** — the share of the ercot-173 blanket arm's total ceiling lift
  that the shaped arm reproduces, on the ercot-174 AT-2 bin-hours basis.
  REPORTED, not a stop bar (the mechanism is categorically different and may be
  two-sided); the binding stop is §5.
* **Two-sidedness** — the share of changed plant-hours where shaped > incumbent
  vs shaped < incumbent, per year.

---

## 4. Seam proofs — ALL must PASS before any solve

| id | claim | falsifier |
|---|---|---|
| **SP-0** | the unmodified deriver reproduces the committed `campd-partial-outages.csv` byte-for-byte (sha256) over its committed span | any hash difference ⇒ the tree moved under the extract; stop and report |
| **SP-1** | with `--emit-shaped` in place, the plant-grain file the SAME run writes is sha256-identical to the committed extract | any difference ⇒ the shaped path perturbed detection; **stop-the-line** |
| **SP-2** | per plant-year, the shaped extract's **covered hour set** is identical to the incumbent's (`outage_hour_mask` union, all three years) | any hour added or dropped ⇒ this is a population change, not a re-shaping ⇒ G-NEUT is reached ⇒ stop |
| **SP-3** | the gate at its **default (off)** reproduces the incumbent availability array exactly, at BOTH consumers | max abs Δ > 0 ⇒ the gate is not inert at default; stop |
| **SP-4** | with the gate ON and every event-cap gate OFF, the composed availability differs from control **only** on plateau hours | any out-of-plateau Δ ⇒ leakage; stop |
| **SP-5** | the shaped derate is **two-valued nowhere by construction**: within each plateau the emitted sub-window factors reproduce `min(1, sm[d]/ref)` for every day, max abs dev ≤ 1e-9 | dev above tolerance ⇒ the emitted extract is not the stated construction |

SP-2 is the load-bearing one: it is the formal statement that this is a
**re-shaping and not a population change**, which is what keeps G-NEUT out of
scope (§2c).

---

## 5. PRE-SOLVE SCREEN — the bounded G-COAL148 predictor (BINDING)

G-COAL148 measures **coal dispatch above the incumbent product ceiling**. That
quantity is **hard-bounded, with no LP**, by the coal ceiling **lift energy**:

```
BOUND(y) = Σ_{coal bins b, hours t}  max(0, ceil_arm(b,t) − ceil_incumbent(b,t)) × pmax(b)      [TWh]
```

Because the cap applies `availability = min(availability, ceiling)`, dispatch can
never exceed the armed ceiling; and the control's own above-ceiling energy is
≥ 0. Therefore

```
Δ(coal above incumbent ceiling)  =  arm_above − control_above  ≤  arm_above  ≤  BOUND(y)
```

**This is an upper bound, not an estimate.** Pre-registered three-way rule,
fixed now:

* **BOUND ≤ 0.5 TWh in every year ⇒ G-COAL148 is PASSED BY CONSTRUCTION**,
  recorded pre-solve; proceed to the A/B.
* **BOUND ≥ 2.0 TWh in any year ⇒ STOP before the solve.** The bar is anchored
  to the rejected arm's own **measured realized** flood (ercot-173:
  +0.98 / +1.95 / +2.73 TWh) — a lift bound in that range means the shaped arm
  is in the rejected family's magnitude. Report as a DO-NOT-REDO recurrence,
  register nothing, do not solve. (Precedent: ercot-174's AT-2 pre-solve stop.)
* **0.5 < BOUND < 2.0 TWh ⇒ SOLVE**, and G-COAL148 is adjudicated from the
  solved pair by the ercot-173 instrument (per-plant, bundle dispatch parquets
  vs the loader product ceiling — the 4.36/4.98/5.01 TWh comparability basis).

---

## 6. KILL GATES — inherited verbatim, G-COAL148 carried live

Any A/B is full-span `--year 2023 2024 2025` in **one** bundle each, and **BOTH
runs are registered whatever the outcome** (rules 15/16).

* **G-BIT / G-SPAN — the conditional pair, resolved NOW, pre-solve.** The shaped
  construction is **year-agnostic** (it applies to every year's plateaus
  identically), so **G-BIT is declared N/A with that reason recorded here,
  before the solve**, and **G-SPAN applies**.
* **G-SPAN** — in 2023 and 2025: no class's annual energy moves more than
  **0.5 %**; the shed-hour count does not increase; the ledgered C3c tail counts
  do not degrade.
* **G-SHED** — the 2024 shed-hour count must **fall**, and **no year's shed
  count may rise**. Baseline **4 / 2 / 0** (2023/2024/2025).
* **G-SPUR** — the C3c spurious mid-band tail-hour count must not increase in
  any year.
* **G-C3c** — the three ledgered tail counts **61/181, 25/53, 3/31** must not
  degrade.
* **G-COAL148 — CARRIED LIVE per the ruling.** Coal dispatch above the measured
  **product** ceiling may not rise more than **+0.5 TWh in ANY year**.
* **G-DOF** — **zero** new fitted scalars (§2e).
* **G-D2** — no class's forced share may cross its rule-20 `[R-FORCED-BUDGET]`
  cap as a result of the arm.
* **G-OWNER** — **C3a-2024 and C3a-2025 keep PASS**, and **C3a-2025 does not go
  beyond −9.1 %**. Baseline: C3a-2024 **+2.5 %**, C3a-2025 **−8.0 %** (PASS band
  ±10 %). This gate exists because the rejected arm moved C3a-2025 by −2.41 pp.
* **Rule 22 LOYO** — leave-one-year-out within 2023–2025 **before any
  promotion**.

**Failing any live gate ⇒ REJECTED-AS-ARMED, reported as such. The gates are not
renegotiated after the solve.**

---

## 7. PREDICTIONS — falsifiable, fixed before measurement

* **P-1 (span identity).** SP-2 passes in all three years: the shaped extract
  covers exactly the incumbent's hours. *Falsifier: any hour added/dropped.*
* **P-2 (two-sidedness).** The shaped derate moves the ceiling in **both**
  directions; the share of changed plant-hours with shaped > incumbent lies
  strictly between 5 % and 95 % in each year. *Falsifier: ≥95 % (restore-only,
  i.e. the rejected family's signature) or ≤5 %.* REPORTED; §5 binds.
* **P-3 (the ercot-172 object).** At h2827 (2024-04-28 19:00) the shaped partial
  factor for (3470, COAL) is **≥ 0.50**, against the incumbent **0.363** and the
  plant's same-hour CEMS-implied **0.7843**. *Falsifier: < 0.50.*
  **If P-3 fails**, the construction is still correct but the W A Parish plateau
  is genuinely flat — i.e. **fault 3 is not the driver at that plant**, which
  refutes the DECISION-MEMO §2 premise. That is reported as a finding, not
  smoothed over, and the arm is still adjudicated on §5/§6.
* **P-4 (C3b-2024).** The arm's C3b-2024 **falls** from 0.205. Whether it
  crosses the 0.20 PASS bar is exactly the question the solve answers; **no
  pass is predicted**. *Falsifier of the direction: C3b-2024 rises.*
* **P-5 (G-COAL148 entailment).** If §5 reads BOUND ≤ 0.5 TWh in every year,
  then G-COAL148 PASSES on the solved pair. *Falsifier: §5 passes and the solved
  G-COAL148 fails — which would mean the bound argument is wrong and must be
  reported as such.*

---

## 8. DECISION RULE

1. **SP-0 … SP-5 all PASS** — else stop, report, register nothing.
2. **§5 screen** — `≥2.0 TWh` ⇒ STOP pre-solve. Else proceed.
3. **A/B pair**, `scripts/replay_keeper.py` on `ercot181_positiontail_B`,
   control and arm **STRICTLY SEQUENTIAL** (~6.6 GB RSS, ~20 min/year each; two
   concurrent ERCOT per-plant solves OOM a 15 GB box).
4. **Legitimacy diagnostics + attestation, then scoring**, both runs.
5. **Both runs registered** on the dashboard whatever the outcome (rules 15/16).
6. **Every live gate passes AND LOYO clears ⇒ promotion candidate.** Any live
   gate fails ⇒ **REJECTED-AS-ARMED**, reported at full magnitude.

---

## 9. Governance, bookkeeping, retention

* **Rule 15 `[R-DASHBOARD]`** — both runs registered + committed + pushed in
  **this** session; the FINDING and the dashboard carry the result, not chat.
* **Rule 16 `[R-ALLYEARS]`** — 2023 + 2024 + 2025 in ONE invocation, ONE bundle
  each. No single-year keeper.
* **Rule 22 `[R-HOLDOUT]`** — ERCOT holds no marker; `--year` never leaves
  {2023, 2024, 2025}. The derive spans the extract's own committed years as
  **data prep**, which the 2026-08-06 amendment places outside the spend gate
  ("prep it, apply it to every year, keep it consistent").
* **Rule 23 `[R-FROZEN-DERIVE]`** — trigger is §0's signed ruling + the
  ercot-172 measurement; cited in the derive commit. No constant re-valued.
* **Rule 24 `[R-REGISTRY]`** — one registered `ScenarioConfig` field,
  cache-key-dropped at its default, recorded in both bundles' `run_config.json`.
* **Rule 25 `[R-ISO-SCOPE]`** — ERCOT-scoped throughout.
* **Rule 27 `[R-PUSH]`** — every push touching a ≥300-line file is
  blob-verified against the **remote** before the next commit.
* **Rule 28 `[R-MECH-MATRIX]`** — the new field's matrix row lands in the same
  PR as the field (duty c); the cell verdict + citation is stamped in **this**
  session (duty b).
* **Retention (top-15 per ISO).** ERCOT stands at **15** registered runs.
  Registering the pair evicts the two oldest, neither protected:
  **`2026-08-04-ercot165-unpooled-tie`** and
  **`2026-08-04-ercot165-unpooled-share`**. Named here, before the fact.

---

## 10. What this session does NOT claim, and does NOT touch

* **No repeal of ERCOT-148/149.** The product cap stays armed; the
  double-count removal is a separate later adjudication.
* **No composition change** — blanket `min()` stays **R**, unit-scoped stays
  default-off with its record, finer-grain-wins stays unbuilt.
* **No claim on C3a-2023.** That is the D1(c)/D5 lane's object, not this one.
* **The ercot-167 SOC re-gate** is not re-scored unless this arm LANDS; its
  reopen condition is unchanged.
* **The keeper-reproduction drift at HEAD** (ercot-173 §5, carried through
  ercot-174 §5 item 4) is surfaced again, not adjudicated: it is why the A/B is
  a **same-HEAD pair** and why the control is replayed rather than assumed.
* **DO-NOT-REDO honoured in full** — no coal offer lane, no depth lever, no
  storage offer surface, no aggregate or per-hour telemetered-HSL cap, the
  West/Panhandle topology stays closed, `ercot_storage_rt_offer_surface` stays
  **R**, the CC-headroom crosswalk stays FILED-UNLICENSED, no rule-18 grain
  work (that is D3, sequenced after this).

**Next shorthand: ercot-185.**
