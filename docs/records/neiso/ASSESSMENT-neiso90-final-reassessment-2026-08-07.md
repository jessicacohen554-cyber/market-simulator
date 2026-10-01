# ASSESSMENT — neiso-90: re-asking the `final` question on the closed prerequisites

**Session:** neiso-90, 2026-08-07 · **Branch:** `claude/neiso-90-final-reassessment-3gqho8`
**Keeper:** `2026-08-05-neiso-83-ca1-reclass` (read from `frontend/data/backcast/keepers/NEISO.json`)
**Markers:** `complete` HELD (re-keyed to the live keeper) · `final` EMPTY
**Freeze:** `holdout-freeze.json` ACTIVE (re-armed 2026-08-06)

**NO OUT-OF-TRAINING YEAR WAS SOLVED, SCORED OR REGISTERED.** No LP was constructed. The only
executions are loader-resolvability probes and one re-score of the keeper's **committed**
artifacts (`calibration_verdict.py --run-id`, no solve). Under rule 22 as rewritten 2026-08-06
— *"WHAT IS HELD OUT IS THE SCORE, NEVER THE DATA"* — inspecting inputs is unrestricted; the
spend is looking at an answer, which nothing here does. No mechanism was tested, no lever
opened, no matrix cell verdict minted, the keeper is unchanged.

Probe: `scripts/probes/neiso90_final_prereq_audit.py` → `results/calibration/_neiso90_prereq_audit.json`.

---

## 0. Recommendation

> ### DO NOT GRANT `final` YET — but **every reason neiso-87 gave has expired**, and the one that survives is different, sharper, and permanent.
>
> **2019 is now fully prepared.** Every input the keeper consumes resolves at HEAD for 2019 and
> 2020 alike. The one apparent gap — no NEISO 2019 row in `actual_tail.json` — is **not a data
> gap and not a blocker**: the source series holds 8,760 h at coverage 1.000, and the row is
> withheld by the deriver's *own tier gate*, which requires the `final` marker. It is circular
> and self-healing — granting `final` unlocks it.
>
> **The surviving objection is that 2019 cannot exercise C3c, and no future work can change
> that.** Actual RT hours > $300 at the NEISO hub in 2019: **zero**. The whole-year RT maximum
> is **$261.35** — $38.65 *below* the threshold. C3c's small-count branch then passes any model
> tail from 0 to 10 h. This is not a prediction: **NEISO 2024 already takes exactly this silent
> free PASS in-sample** (actual 8 h < 10, model 0 h), which is why the keeper shows C3c CAVEAT
> rows for 2023 and 2025 only.
>
> **And the same is true of every other untouched year.** 2020 actual = 0, 2021 = 2 — both free
> passes. **The only out-of-training year in NEISO's entire 2019–2025 working span that can fail
> C3c is 2022** (actual 117 h), which is validation tier: already authorized, already spent
> twice, re-spendable. So **no never-touched year can test the frontier criterion, and none ever
> will.**
>
> **The condition that would change this recommendation** is the C3c lane arming a tail-forming
> mechanism — and then 2019 becomes valuable for the *opposite* reason from the one neiso-87
> imagined. Not as a **sensitivity** test (can the model find scarcity?), which 2019 can never
> be, but as a **specificity** test (does the new mechanism *invent* scarcity in a year that had
> none?). At actual = 0 the small-count guard FAILS any model tail > 10 h, and 2019 is the
> cleanest zero-scarcity year on the record. Today, with the model's tail identically 0
> everywhere, that test is trivially passed and carries no information.

| question | answer |
|---|---|
| **1** Is 2019 now fully prepared? | **YES.** One gap remains and it is the grant's own downstream artifact (§2). |
| **2** Does 2019 still fail to discriminate? | **YES, and permanently** — and the mechanism is already visible in-sample at 2024 (§3). |
| **3** Has 2020 become the better instrument? | **It strictly dominates 2019 — but not on C3c, where it is equally powerless. 2021 is better still** (§4). |
| **4** Recommendation on `final`? | **Not yet, on the merits.** Named condition in §5. H1-2026, the grant's other half, is **independently hard-blocked** (§5.3). |

---

## 1. The one remaining data blocker — established before recommending anything

### 1.1 What a missing `actual_tail` row actually does: it **SKIPs**, and a SKIP is not free

`scripts/calibration_verdict.py::score_price_tail`, line 1595:

```python
tail_rec = _tail_part().get(iso, {}).get(str(year))
if tail_rec is None or tail_rec.get(gate_key) is None:
    out.append(_skip("price_tail", year,
        f"no committed {gate_lbl} actual tail for this ISO-year …"))
```

So C3c returns a SKIPPED record — **not** the "free small-count PASS" neiso-87 predicted, because
the small-count branch is never reached. Downstream (line ~2420):

```python
skipped = [cid for cid, c in per_criterion.items()
           if cid != "governance" and c["status"] == SKIPPED]
...
if n_caveats == 0 and not skipped and not data_blocked:
    determination = CALIBRATED
else:
    determination = CALIBRATED_CAVEATS
```

**A SKIP caps the determination at CALIBRATED-WITH-CAVEATS and names C3c in the reasons as
unscored.** It cannot FAIL and cannot be silently passed over.

**The C3c standing rule does not reach it.** `_apply_c3c_standing_rule` opens with
`fails = [r for r in records if r["status"] == FAIL]; if not fails … return`. A SKIP is not a
FAIL, so the rule is silent — the prompt's suspicion is correct. The rule was written to stop a
lone C3c *failure* sinking an out-of-training run to NOT-YET; it has nothing to say about a
criterion that was never scored.

### 1.2 It is the tier gate, not the data — and the grant unlocks it

The source series is complete. Read directly from
`data/raw/_validation-source/actual_lmp_hourly_NEISO.parquet`:

| year | hours | RT coverage | RT max $/MWh | RT mean | **RT h > $300** | DA h > $300 |
|---|---|---|---|---|---|---|
| 2018 | 8,760 | 1.000 | 2,454.57 | 43.55 | 32 | 4 |
| **2019** | **8,760** | **1.000** | **261.35** | **30.67** | **0** | **0** |
| **2020** | **8,760** | **1.000** | **236.11** | **23.39** | **0** | **0** |
| 2021 | 8,760 | 1.000 | 375.28 | 44.84 | 2 | 0 |
| 2022 | 8,760 | 1.000 | 2,254.35 | 84.92 | **117** | 27 |
| 2023 | 8,760 | 1.000 | 1,161.97 | 35.70 | 15 | 5 |
| 2024 | 8,760 | 1.000 | 2,112.77 | 39.54 | 8 | 5 |
| 2025 | 8,760 | 1.000 | 1,110.22 | 65.88 | 20 | 12 |

The row is absent from `actual_tail.json` because `derive_actual_tail._year_emittable` refuses it.
Re-running the deriver's own predicate under a hypothetical marker (in memory; **nothing
written**):

```
marker at HEAD:  complete = [NEISO, NYISO, PJM]      final = []   (only a _note)

  NEISO 2019: emittable at HEAD = False | with a final marker = True  | tier = locked_test
  NEISO 2020: emittable at HEAD = True  | with a final marker = True  | tier = validation
  NEISO 2022: emittable at HEAD = True  | with a final marker = True  | tier = validation
  NEISO 2023: emittable at HEAD = True  | with a final marker = True  | tier = train
```

**Verdict: not a blocker on the grant — it is downstream of it.** neiso-89 (PR #3693) deleted the
`CONSIDERED_HOLDOUT_YEARS` ladder that used to gate emission independently, leaving the tier
marker as the single point of control. The 2019 row therefore materialises the moment `final`
names NEISO and the deriver is re-run.

### 1.3 But it is a real ORDERING HAZARD, and it is the one operational thing to get right

`derive_actual_tail.py` is **not** run by the solve or scoring path — it is a committed part,
regenerated by hand. So:

> **If `final` is granted and 2019 is solved without re-running
> `scripts/data/derive_actual_tail.py`, C3c SKIPs and the touch-once year is spent with the
> criterion NEISO's frontier is declared on literally unscored.**

That is unrecoverable — the locked tier cannot be re-scored. If the owner ever does grant
`final`, re-running the deriver must be step one of the grant, before any solve. Recommended
wording for the marker entry is in §5.4.

---

## 2. Q1 — Is 2019 now fully prepared? **Yes.**

Every input the keeper's `run_config.json` arms, walked at HEAD for **2019 and 2020**, with
**2023 carried as a control** so a "gap" is only real when the control behaves differently.
Loader-resolvability only — no LP built, no model output produced.

| input | 2019 | 2020 | 2023 (control) | vs neiso-87 §3.2 |
|---|---|---|---|---|
| **`load_demand`** (the array `runner.py:961` builds the LP from) | ✅ (5, 8760), peak 20,617 MW, 95.54 TWh | ✅ (5, 8760), peak 21,524 MW, 92.10 TWh | ✅ peak 20,347 MW, 96.86 TWh | **WAS ❌ BLOCKING → OK.** neiso-87 probed `load_demand_meta`, which has no solve-path consumer (neiso-88 §2.3). |
| **`backcast_config`** (the keeper recipe, assembled) | ✅ builds | ✅ builds | ✅ builds | new check |
| **`calibration_reference.json`** (C1/C2 target) | ✅ `isos.NEISO.2019`, 4 keys | ✅ `isos.NEISO.2020`, 4 keys | ✅ 4 keys | **WAS ❌ BLOCKING → OK** (neiso-89) |
| **`NEISO_<y>_renewable_capacity.csv`** | ✅ 120 rows | ✅ 120 rows | ✅ 120 rows | **WAS ❌ BLOCKING → OK** (neiso-89) |
| **`actual_tail.json`** (C3c part) | ⚠️ **absent — tier-gated, §1.2** | ✅ rt 0 h, da 0 h, cov 1.0 | ✅ rt 15 h | **WAS ❌ BLOCKING → self-healing.** 2020/2021 newly emitted by neiso-89. |
| `actual_lmp_hourly_NEISO` (C3a/C3b/C3c upstream) | ✅ 8,760 h, cov 1.000 | ✅ 8,760 h, cov 1.000 | ✅ 8,760 h | ✅ unchanged |
| `henry_hub_actual` (per-year gas price) | ✅ $2.57 | ✅ $2.03 | ✅ $2.54 | new check |
| **`gas_basis_by_iso_month.csv`** | ✅ **12/12 months, every one MEASURED** (ISO-NE newswire recaps) | ✅ **12/12 MEASURED** | ✅ 12/12 | ✅ neiso-86 repair confirmed to cover **both** probe years |
| `algonquin_citygate_daily.csv` | ✅ 56 prints | ✅ 45 prints | ✅ 44 prints | ✅ unchanged |
| `campd-unit-outages-NEISO.csv` | ✅ 483 windows | ✅ 441 windows | ✅ 367 windows | **WAS ⚠️ (vintage split) → OK.** Split CLOSED at neiso-89 (`60288d16`). |
| `plant_emission_rates_v2` | ✅ 4,346 rows | ✅ 4,271 rows | ✅ 4,127 rows | ✅ unchanged |
| `fossil_co2_rates` | ✅ 2,547 rows | ✅ 2,536 rows | ✅ 2,518 rows | ✅ unchanged |
| `load_hydro_budget` (neiso-72 window) | ✅ 169 plants, 7.64 TWh, 1,914 MW | ✅ 170 plants, 6.64 TWh, 1,917 MW | ✅ 168 plants, 8.55 TWh | new check |
| reserve requirements (as the keeper holds them) | ✅ static 1,800 / 1,200 / 600 MW | ✅ same | ✅ same | year-independent by construction |
| `parasitic_load_factors` | ✅ pooled map, 463 plants | ✅ same | ✅ same | **WAS ⚠️ → OK, see below** |
| EIA-930 `ISNE_fueltype` / `ISNE_region` | ✅ 140,160 / 35,040 rows | ✅ 140,544 / 35,136 | ✅ 140,160 / 35,040 | ✅ unchanged |
| `capacity_actuals_neiso.csv` | ⚪ window 2021–2025 | ⚪ window 2021–2025 | ✅ 107 rows | **not a backcast input — see below** |

**Two rows that neiso-87 flagged and that dissolve on inspection of the code path:**

- **`parasitic_load_factors` is year-independent.** neiso-87 marked the missing 2019/2020
  per-year rows ⚠, as "the same per-year provenance split the gas basis had". It is not. The
  only solve-path consumer, `fleet.campd_bins._ramp_parasitic_factor_map`, reads the **pooled
  `year == 0` rows exclusively** (463 plants); the per-year rows (2022–2025) are the derive's
  intermediate and have **no consumer anywhere in `src/market_sim/`**. Nothing is disadvantaged.
- **`capacity_actuals_neiso.csv` is not a `final` prerequisite.** Zero consumers in
  `src/market_sim/`; read only by `scripts/score_capacity_hindcast.py` and forecast-lane probes.
  Its own header declares it the capacity-hindcast scoring target on a deliberate 2021–2025
  window. It has no bearing on a backcast of 2019.

**Also confirmed not a per-year asymmetry:** the zonal-load-file warning
(`NEISO_load_hourly_<y>.csv … skipping`) fires identically on 2019, 2020 **and the 2023 control**
— it is a constant of the NEISO configuration, not a holdout-year deficiency. And `bench/NEISO/`
holding only 2022–2025 is not a gap: `dashboard_add_run.py` *writes* the bench part at
registration time from the actuals.

> **Conclusion: 2019 is prepared. The keeper recipe assembles for it, every measured input it
> consumes resolves, and the single outstanding artifact is produced by the act of granting.**

---

## 3. Q2 — Does 2019 still fail to discriminate? **Yes, and the mechanism is already running in-sample.**

The C3c band, read from `calibration_verdict.py`: `TAIL_SMALL_COUNT = 10`, band `[0.5×, 2.0×]`,
`TAIL_THRESHOLD["NEISO"] = 300.0`. Below 10 actual hours a ratio is degenerate, so the criterion
switches to `|model − actual| ≤ 10`. Applying that to a model tail of 0 h — which is what this
keeper produces in **every** year, on both the energy-only and settlement bases (frontier
re-verification, neiso-84):

| actual RT h > $300 | branch | C3c on a 0 h model |
|---|---|---|
| **0** (2019, 2020) | small-count `\|Δ\| ≤ 10` | **PASS** — free |
| **2** (2021) | small-count | **PASS** — free |
| **8** (2024) | small-count | **PASS** — free |
| 15 (2023) | ratio, 0.00× | FAIL → ledgered CAVEAT |
| 20 (2025) | ratio, 0.00× | FAIL → ledgered CAVEAT |
| **117** (2022) | ratio, 0.00× | **FAIL** |

**This is confirmed empirically, not projected.** Re-scoring the keeper from its committed
artifacts (`calibration_verdict.py --run-id 2026-08-05-neiso-83-ca1-reclass`; no solve)
reproduces CALIBRATED-WITH-CAVEATS, 0 FAILs, C3c the sole ledgered caveat — and the C3c block
prints CAVEAT rows for **2023 and 2025 only**. There is no 2024 gated row because **2024 already
passed silently**, on exactly this small-count branch, with a model tail of 0 against an actual
of 8. One of the three tuned years is already non-discriminating on C3c today.

**So neiso-87 §3.3 holds, and strengthens.** Two sharpenings:

1. **The margin is larger than "zero hours".** 2019's *entire-year* RT hub maximum is **$261.35**
   — the market never came within $38.65 of the threshold. 2020's is $236.11. These are not years
   that narrowly missed having a tail; they are years with no scarcity formation at all.
2. **At HEAD the outcome is a SKIP, not a free PASS** (§1.1) — and a SKIP is the *worse* of the
   two. A free PASS at least records a comparison. A SKIP caps the determination and names C3c
   as unscored, meaning the touch-once year would be spent producing a verdict that says nothing
   whatever about the frontier.

Either way the criterion cannot be failed, so **2019 cannot test the open question**, and no
amount of preparation changes that: the constraint is a property of the 2019 market, not of the
model or the repo.

---

## 4. Q3 — Has 2020 become the better instrument? **It dominates 2019 — but 2021 is better still, and neither tests C3c.**

**2020 strictly dominates 2019 as an instrument**, on four independent counts:

| | 2019 | 2020 |
|---|---|---|
| tier | locked test — **touch-once, ever** | validation — **iterable by design** |
| authorization needed | a `final` grant that can never be re-taken | already covered by the `complete` marker NEISO holds |
| still blocking | freeze lift **+** owner grant | **freeze lift only** |
| preparedness | complete (§2) | complete (§2), incl. its `actual_tail` row |
| if it surfaces a defect | cannot re-test after the fix | re-testable — that is the point of the tier |

Rule 22's touchpoint loop exists for exactly this: run the frozen recipe → **diagnose the
object** → re-train on 2023–2025 around it → re-test. NEISO has already run that loop once to
good effect: the 2022 touchpoint surfaced a seasonally-inverted gas-basis input (neiso-85), the
fix was a zero-DOF data repair (neiso-86), and the year was re-spent against the corrected input.
Nothing was fitted to 2022.

**But the honest comparison is not 2019 vs 2020 — it is 2021 ≥ 2020 > 2019**, and none of the
three can test C3c:

- **On C3c specifically, 2020 is no better than 2019.** Actual = 0, whole-year max $236.11 — the
  identical free pass. Choosing 2020 over 2019 buys reversibility and cheapness, **not**
  discriminating power on the frontier.
- **2021 is the better rung.** It is equally prepared (demand 98.55 TWh, `calibration_reference`,
  renewable capacity and an `actual_tail` row all present), it is adjacent to the already-worked
  2022 so a regression between them is interpretable, and it avoids 2020's confound: **2020 is
  the COVID demand year** — 92.10 TWh against 95.54 in 2019 and 98.55 in 2021, the lowest in the
  span. Demand is a measured input in backcast mode, so that dip does not bias C1/C2 directly,
  but it does put the fleet in an unusual economic regime, and a miss there is one more thing to
  disentangle.
- **The finding that matters most:** *the only out-of-training year in NEISO's entire 2019–2025
  working span that can fail C3c is 2022*, and it is validation tier — already authorized,
  already spent twice, re-spendable at will. A corollary worth putting on the record: the C3c
  standing rule declared 2026-08-06 has, in NEISO's whole out-of-training span, **exactly one
  year it can ever fire on** — 2022, which was spent the day before the rule was declared.

**Recommendation on the instrument question: if the owner wants out-of-training evidence now,
spend a validation touchpoint — 2021 first, 2020 second — and not 2019.** It needs only a freeze
lift, the marker is already held, both years are fully prepared, and the evidence is reversible.
Neither will move C3c; both exercise C1 / C2 / C3a / C3b / C4 against a structurally different
pre-2021 fleet, which is real value the frontier criterion is not.

---

## 5. Q4 — The recommendation on `final`

### 5.1 Recommendation: **DO NOT GRANT — not yet, on the merits.**

Not because 2019 is unprepared. It is prepared (§2), and neiso-87's stated reason — "2019 cannot
be dispatched" — is withdrawn. The reason is now narrower and it is not going to erode:

> Granting `final` spends the single most irreversible resource in the policy on a year that
> **cannot exercise the criterion NEISO's frontier is declared on**, in exchange for evidence on
> C1/C2/C3a/C3b/C4 that 2020 and 2021 supply reversibly, under a marker NEISO already holds.

There is no upside to paying an irreversible price for a reversible good.

### 5.2 The condition that would change it

> **The C3c lane arming a tail-forming mechanism.**

This is the inverse of the reason neiso-87 gave for waiting, and the inversion is the point.
Resolving C3c does **not** make 2019 able to test *sensitivity* — the actual tail is 0 and always
will be, so the model can never be caught missing scarcity there. What resolving C3c does is make
2019 able to test **specificity**: with actual = 0, the small-count guard **FAILS any model tail
above 10 h**. That is the invented-tail guard doing genuine work, and 2019 — the lowest-priced,
zero-scarcity year in the record — is the cleanest possible year to run it on. A new
scarcity-formation mechanism that fires in 2019 is over-firing, and 2019 is the only untouched
year that can prove it.

Today, with the model's tail identically 0 in every year, that test is passed trivially and
carries no information. It becomes informative the moment the tail is non-zero. **That is when
the one-shot is worth spending, and it is a real, reachable trigger — not an indefinite hold.**

Two subordinate conditions, both cheap:

- **Re-run `scripts/data/derive_actual_tail.py` as step one of any grant** (§1.3), before any
  solve, or C3c SKIPs and the one-shot is wasted.
- **Resolve the H1-2026 half first or split the grant** (§5.3).

### 5.3 H1-2026 — the grant's other half is independently HARD-BLOCKED

`final` authorizes **2019 and H1-2026 together**. The H1-2026 half cannot be scored at all:

- `data/raw/_validation-source/actual_lmp_hourly_NEISO.parquet` carries **2018–2025 and no 2026
  rows whatsoever** — so C3a (mean LMP), C3b (duration/shape) and C3c (tail) have no benchmark.
- `bench/NEISO/` holds 2022–2025 only.
- Supporting series are thin where they exist at all: the gas basis has 5 months of 2026, and
  `algonquin_citygate_daily.csv` carries **one** 2026 print (neiso-87 §3.2, unchanged).

This is a pure data gap, unlike §1.2's tier gate — no marker unlocks it, and closing it is
ordinary unrestricted intake under rule 22. **If the owner ever wants to grant `final`, granting
it while H1-2026 is unscoreable spends a touch-once authorization on half a test.** Either close
the 2026 actuals intake first, or split the marker so the two locked-test years can be granted
independently.

### 5.4 If the owner grants anyway — the minimum safe procedure

Recorded so the decision is not lost to ordering, since it is not recoverable after the fact:

1. Re-run `scripts/data/derive_actual_tail.py` **and commit the emitted NEISO 2019 row** — the
   grant unlocks it, but nothing runs it automatically.
2. Confirm the 2019 row reads `rt_gt: 0` (it will) and record **in advance** that C3c is
   therefore a structurally free PASS on this year and carries no frontier evidence. Pre-register
   it so the PASS is never later quoted as C3c skill.
3. Solve 2019 with the frozen keeper recipe, unmodified, `--holdout-authorized`.
4. Score and register. Record the determination whatever it is; no calibration change may respond
   to it.
5. Leave H1-2026 unspent unless its actuals have landed (§5.3).

### 5.5 What this session does NOT do

`final` is an owner declaration. Nothing here declares, grants or prepares a grant. The marker
files are untouched. The freeze is untouched and was not engaged.

---

## 6. Secondary findings — flagged for the owner, not acted on

**The D-23 record correction has largely landed** — `calibration-complete.json` now carries
`locked_test_scored_on_WITHDRAWN`, a corrected `locked_test_note` ("NEVER BEEN GRANTED AND NEVER
BEEN SPENT"), a corrected `final._note`, and CLAUDE.md rule 22 carries the correction. **Two
residues survive**, both in owner-editable governance files, both quoted verbatim:

1. **`holdout-freeze.json` contradicts itself.** Its `lift_scope` field was corrected per D-23,
   but the **2026-08-06 `re-armed` history entry still asserts the withdrawn claim**: *"not 2019
   or H1-2026 (locked tier; `final` remains empty and **the SPENT one-shot stands as scored on
   the input it consumed**)"*. One file, two incompatible statements about whether NEISO's locked
   test was spent. This file is read by a live gate (`enforce_holdout_year_gate`), so it is the
   worst place for the claim to persist.

2. **`calibration-complete.json`'s `final._note` cites a withdrawn reason.** It reads: *"neiso-87
   section 3 answers it NOT YET on the merits: **2019 is unsolvable at HEAD (no NEISO demand rows
   before 2021)** and could not discriminate on C3c even if it were"*. The first clause was
   withdrawn by neiso-88 and is refuted again in §2 here. The **conclusion is still correct** and
   this assessment reaches it independently — but on the second clause alone. Worth correcting so
   the ungranted question is not carried on a reason that no longer exists.

Neither is edited here: both are locked-tier governance artifacts and correcting them is an
owner act (the same posture neiso-87 §1 took, and the route by which D-23 was in fact signed).

**Carried forward, unchanged and still open** (not re-investigated this session): the committed
keeper no longer reproduces at HEAD in 2025 — January-only, mean Δλ −0.334 $/MWh — so any future
NEISO A/B must solve its own same-HEAD control (neiso-87 §4.0, materiality re-assessed at
neiso-88 §5(i)). And NEISO remains the only one of six ISOs running the archived P2 commitment
pass (keeper frontier note item 5), escalated and unresolved.

---

## 7. Rule compliance

| rule | status |
|---|---|
| 1 `[R-STRUCT]` | No mechanism armed or proposed; nothing judged by a residual. |
| 13 `[R-MEASURED]` | No measured outcome fed back anywhere. §1.2 and §3's tail counts are **actuals-only statistics**, no model output involved. |
| 15 `[R-DASHBOARD]` | **No run produced ⇒ nothing to register.** The keeper re-score is `--run-id` on committed artifacts, not a run. |
| 16 `[R-ALLYEARS]` | Not engaged — no bundle produced. Flagged in §5.4 for any future grant. |
| 22 `[R-HOLDOUT]` | **NO out-of-training year solved, scored or registered.** Freeze ACTIVE, untouched, not engaged. All probes are loader/on-disk inspection, which the 2026-08-06 rewrite places outside the marker regime ("what is held out is the SCORE, never the DATA"). The §1.2 marker experiment is **in-memory only — no file written**, and emits no locked-tier row. NEISO's locked test is **UNSPENT AND NEVER GRANTED**; the withdrawn "spent" claim is not repeated (§6). No skill claim from any out-of-training number. |
| 24 `[R-REGISTRY]` | No tunable touched; the probe reads only. |
| 25 `[R-ISO-SCOPE]` | **NEISO files only.** No other ISO's row, cell, keeper shard or marker entry touched. |
| 27 `[R-PUSH]` | Opus session (`claude-opus-5`). Edits made locally, pushed as exact on-disk bytes; no file ≥300 lines rewritten. |
| 28 `[R-MECH-MATRIX]` | **No mechanism tested ⇒ NO cell verdict minted** (duty d). No new `ScenarioConfig` field ⇒ duty (c) not engaged. §5.6 block added recording that the session ran and moved nothing (duty b). |

---

## Appendix — reproduction

```
uv run python scripts/probes/neiso90_final_prereq_audit.py
uv run python scripts/calibration_verdict.py --run-id 2026-08-05-neiso-83-ca1-reclass
```

Machine-readable audit: `results/calibration/_neiso90_prereq_audit.json`.
