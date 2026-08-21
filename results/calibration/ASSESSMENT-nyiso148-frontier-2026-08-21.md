# ASSESSMENT nyiso-148 — frontier re-statement after nyiso-147, and the `complete` / `final` posture

Session nyiso-148, 2026-08-21. Keeper at HEAD **`2026-08-19-nyiso-146c-state-scoped`**,
unchanged — **nothing is promoted in this part and no keeper shard, marker or
registry file is touched.** No LP was solved for any statement below: every
number is read from committed artifacts, and the two scorers were re-run at
HEAD on committed bundles only.

This document supersedes `ASSESSMENT-nyiso145-frontier-and-complete-2026-08-19.md`
as NYISO's live frontier statement.

---

## 0. THE ANSWER

* **(a) The keeper still merits CALIBRATED, re-verified at HEAD on the current
  rubric AND on the miso-171 scorer.** `calibration_verdict.py --run-id
  2026-08-19-nyiso-146c-state-scoped` returns **CALIBRATED** (C1/C2/C3a/C3b/C4/C6/C8
  PASS, C3c the lone ledgered caveat, 1 of 1 budget); `audit_keepers.py --iso NYISO`
  returns **PASS, 0 failures, 0 warnings**. The miso-171 unit-grain attribution
  repair is measured, not assumed: it moves NYISO by three re-attributed
  `chp_steam` rows and ≤ 0.3 pp of bridge share, flips no C8 record and no
  determination (§1).
* **(b) The frontier statement changes in KIND, and it is now ONE object with a
  PROVEN cause and a NAMED blocker — not an open investigation.** nyiso-145's
  two lane-sized objects are both resolved as *diagnoses*: object 1 (CC
  over-cycling) closed by the keeper, object 2 (merit-order inversion) now known
  to be the visible half of a **capacity** defect whose repair is measured, built
  and shipped default-off. nyiso-147 proves the 2023 upstate level with one
  measured field (+8.7 % → +1.5 %) and proves, in the same run, that the field
  cannot arm until CHP **conduct** is represented. Frontier is **NOT-YET**, on a
  queue that is shorter and better-specified than at nyiso-145 (§2).
* **(c) `complete` is HELD, unchanged, and NOT re-keyed — correctly** (no
  promotion in Part 1; rule 22 D-5(b) re-keys on promotion). The touchpoint-loop
  posture is **unaffected in principle and inert in practice**: the holdout spend
  freeze is ACTIVE, so 2020–2022 cannot be spent regardless. One thing *has*
  changed for the loop: a 2022 touchpoint run today would be scored against a
  keeper whose CHP grid capacities are now KNOWN to be wrong, which is an
  argument for spending it after the CHP repair lands, not before (§3).
* **(d) A `final` request remains NOT-YET on the merits, and nyiso-147
  strengthens that answer rather than weakening it.** Both structural blockers
  re-verified at HEAD stand (H1-2026 unsolvable, 2019 non-discriminating), and
  a third is added by nyiso-147: the keeper's CHP capacity basis carries a
  measured, un-repaired defect, so a touch-once locked-test spend today would
  burn the year on a fleet the model itself now knows is misspecified (§4).

---

## 1. (a) THE KEEPER, RE-SCORED AT HEAD

### 1.1 The determination

`python scripts/calibration_verdict.py --run-id 2026-08-19-nyiso-146c-state-scoped`,
run at this HEAD, committed artifacts only, no solve:

| criterion | tier | verdict |
|---|---|---|
| C1 fuel-mix by class (grid-delivered) | LOAD | **PASS** |
| C2 system volume (gas/coal families) | LOAD | **PASS** |
| C3a mean LMP | LOAD | **PASS** |
| C3b price duration/shape | LOAD | **PASS** |
| C3c price tail / scarcity (RT hourly) | SUPP | **CAVEAT** [ledgered] — model 2 / 0 / 5 h vs RT actual 10 / 13 / 42 h |
| C4 fleet hourly dispatch correlation | SUPP | **PASS** |
| C6 governance gate | PROT | **PASS** |
| C8 forced-energy share (D-2) | PROT | **PASS** |

**Determination: CALIBRATED.** Determination basis: *1 ledgered caveat
(model-class) — REPORTED, and NOT determination-downgrading under rubric v3.3:
C3c price tail / scarcity*. Caveat budget 1 of 1; D-10 free-class C1 10/10
free, `CC_CHP` and `ST_CHP` pinned.

The C3c standing rule fires exactly as its guards require: C3c is the **lone**
non-passing criterion (guard a), C6 **PASSES** (guard b), it is classified
`model-class` on a SUPPORTING-tier criterion (guard c), and it reads CAVEAT and
is reported at full magnitude, never PASS (guard d).

`python scripts/audit_keepers.py --iso NYISO`: **PASS — 0 failures, 0 warnings**,
across the keeper-text check, the holdout check, the marker check (M1, the
D-5(b) re-key) and the status check.

### 1.2 The miso-171 scorer — measured, not assumed

The keeper's committed `legitimacy_diagnostics.json` was written 2026-08-19
(commit `41c5bc6`); the miso-171 unit-grain floor-class attribution
(`FloorClassMatrix`) landed 2026-08-20 (commit `18fd6ba`). So the question is
real: *does the keeper's C8/D-2 verdict survive the repaired attribution?*

It does, and this is checkable without a solve, because
**`2026-08-20-nyiso-147-control` is a byte-identical replay of the keeper**
whose diagnostics WERE regenerated on the repaired scorer (commit `ffd745a`).
Diffing the two D-2 tables:

| change | keeper (pre-repair) | control (post-repair) |
|---|---|---|
| `ST_CHP × chp_steam` rows | absent | **3 new rows** (2023/2024/2025) |
| `CT_CHP × chp_steam` share | 0.1773 / 0.2732 / 0.0626 | 0.1173 / 0.1580 / 0.0324 |
| `CC_REGULAR × nyiso_gas_commitment_bridge` | 0.0529 / 0.0353 | 0.0534 / 0.0362 |
| `ST_GAS × nyiso_gas_commitment_bridge` | 0.0119 / 0.0168 / 0.0095 | 0.0105 / 0.0140 / 0.0092 |
| D-2 gate | PASS | **PASS** |
| D-4 failures | 3 (2480 ×2, 7314-2025) | **3, identical** |

The repair does one thing in NYISO: it moves `chp_steam` forcing that was
credited wholesale to `CT_CHP` onto the `ST_CHP` tranches that actually carry
it — the mis-attribution the repair exists to fix — and shifts bridge shares by
≤ 0.3 pp. **No C8 record flips and no gate approaches its cap** (the CHP classes
are D-2-exempt in any case; the gated merchant shares are 3.5–5.3 % against a
30 % cap).

This agrees with miso-171's own six-keeper sweep, which re-scored NYISO
before/after and recorded `determination_flips_before_to_after: []`,
`d2_share_deltas: {}`, `c8_record_flips: {}`
(`_miso171_d4_attribution_rescore.json`).

**One bookkeeping item, disclosed and not repaired here:** the keeper's own
bundle still carries the pre-repair diagnostics file. It is cosmetic — every
gated record is identical on the regenerated table, which is committed at
`nyiso147_control` — but a future session that regenerates the keeper's bundle
should expect the three `ST_CHP` rows to appear. It is NOT a determination
exposure of the miso-169 K-3 class (where a regenerated table flips a gate);
here the regeneration exists and flips nothing.

### 1.3 What a probe bundle's NOT-YET does and does not mean

Scoring `2026-08-20-nyiso-147-control` directly returns **NOT-YET**, on
*"governance gate UNATTESTED: no governance attestation in bundle"* — probe and
control bundles carry no `calibration_attestation.json`. Every other criterion
is identical to the keeper's, and the NOT-YET is guard (b) of the C3c standing
rule working as designed (an unattested C6 blocks the auto-ledger), not a
statement about the dispatch. The same pattern is already recorded in the
matrix for `2026-08-06-pjm-158-novirtual-disarmed`.

---

## 2. (b) WHAT nyiso-147 CHANGES ABOUT THE FRONTIER STATEMENT

### 2.1 The nyiso-145 queue, re-read

nyiso-145 declared frontier NOT-YET on **two lane-sized modelling objects**,
independent of every pending owner ruling:

| # | nyiso-145 object | status after nyiso-146 + nyiso-147 |
|---|---|---|
| 1 | CC over-cycling (Bethlehem 262–302 starts/yr vs 5–7) | **CLOSED** by keeper `146c` (41/10/15 starts, median runs 68/144/319 h) |
| 2 | Merit-order inversion on mothballed small CCs (25×–225×) | **RE-DIAGNOSED**: it is the *visible half* of a capacity defect, and a second, larger population of it exists on the CHP side |

Object 2 did not survive as stated. nyiso-146b built and froze its repair
(`cc_reserve_duty_split`) and REJECTED it as armed because removing ~1.4 TWh of
phantom cheap upstate energy pushed C3a-2023 from +9.0 % to +11.3 % — the repair
was blocked by a *price level* it could not explain. nyiso-147 explains it.

### 2.2 The 2023 upstate object: root cause PROVEN, repair UNARMABLE

nyiso-147 phase 0 located the whole of C3a-2023 in **Upstate_West** (+9.46 pp of
a +9.2 % system error; +30.8 % on the zone's own mean, year-round), refuted the
upstate fuel-basis candidate (west marginal delivered gas $1.79–1.96 against the
SOM Tenn Z4 annual $1.82), and attributed ~$7.4 of the $8.1 marginal "markup" to
RGGI rather than offer margin — leaving the **marginal unit's identity** as the
object. The cause is a capacity carve: `CHP_BTM_PCT_BY_SECTOR["merchant"] = 35 %`,
a constant whose own citation comment reads *"residual-identified … no
independent source yet"*, removes 35 % of every merchant cogen — and the plants'
own market meters refute it (Gold Book net energy = 100.3 % of EIA-923 net for
Sithe Independence three years running; Brooklyn Navy Yard's carved capacity
implies CF 1.07, which is impossible).

Armed, the single measured field does what a true root cause does:

| | control | arm |
|---|---|---|
| lw system C3a 2023 | **+8.7 %** | **+1.5 %** |
| Upstate_West eqh err 2024 | +3.54 | **+0.89** (−75 %) |
| Upstate_West eqh err 2025 | +5.79 | **−0.38** (−93 %) |

**And it is not armable.** The arm fails three of its own pre-registered gates,
each a real finding rather than a scorer artifact: Selkirk (10725) dispatches
730 GWh against a 92 GWh meter once its capacity is restored (A-K4); CC_CHP
over-runs its own *corrected* bench by +5.0 TWh because the LP runs the restored
plants at their offers' implied capacity factor (A-K5/C1); and C3a-2025 breaks
the band at −12.2 % (A-K5). The owner's structure-over-gates clause was
considered and correctly NOT applied — these are the carve's masked defects
becoming visible, and promoting would swap a CALIBRATED keeper for a NOT-YET
run on three load-bearing criteria.

**The frontier consequence.** Object 2 is no longer "a merit-order inversion in
CC_REGULAR". It is: *the model's CHP grid capacity is measurably wrong; the
correction is derived, built, frozen and shipped; and it cannot be turned on
until the same fleet's operating conduct is represented.* That is a **single
object with a proven cause and a named prerequisite** — a materially better
frontier position than nyiso-145's, and still NOT-YET, because the prerequisite
is unbuilt model-side work.

### 2.3 The 2025 level: a control "pass" that is now known to be cancellation

This is the part of nyiso-147 that changes how the keeper's *own numbers* should
be read, and it is the nyiso-126 lesson one level up.

The keeper's C3a-2025 reads **−2.2 %** — comfortably inside the ±10 % band, and
on its face a pass. nyiso-147 shows it is **~$6/MWh of masked under-pricing**:
with the missing ~1.3 GW of cheap CHP capability restored, every zone falls ~$6
and the year lands at **−12.2 %**. The keeper's 2025 level is therefore held up
by an absence — capacity the model does not carry — and not by price formation
that is right.

The same structure is visible inside the keeper's own zone table, and it is not
2025-specific: **Upstate_West runs +11.4 % (2024) and +10.8 % (2025)** against
downstate under-pricing (NYC −4.4/−7.4 %, LI −9.5/−11.4 %) that nets the system
to +2.2/−1.9 %. The model carries essentially **no zonal gradient** (< $1.5
across all five zones in 2024/2025 against actual gradients of $9–15). C3a-2023
is simply the year the cancellation fails.

**How this must be reported.** C3a is scored on the load-weighted system mean, so
these three C3a PASSes are true as scored and the keeper's CALIBRATED stands —
no criterion is being re-graded here. But the frontier statement may no longer
describe NYISO's 2024/2025 price level as *validated*: two large, opposite-signed
zonal errors that net out are a known defect with a measured magnitude, and any
future arm that adds cheap supply re-exposes it. Recorded here so that no later
session reads a passing C3a-2025 as evidence the 2025 level is right.

### 2.4 The frontier statement at HEAD

> **NOT-YET.** NYISO's remaining queue holds one lane-sized modelling object
> with a proven root cause — the CHP grid-capacity carve, whose measured repair
> is built and frozen and whose arming is blocked on an unbuilt representation
> of CHP operating conduct — plus a second, separable object (the 2025 dear-gas
> level, and behind it the missing zonal gradient) that the first one exposed.
> Both are model-side lane work, not owner rulings. Everything nyiso-145 listed
> as an *open investigation* has become a *specified construction*; the reason
> frontier cannot be declared is that the constructions are not built, not that
> the causes are unknown.

---

## 3. (c) `complete` STANDING AND THE TOUCHPOINT-LOOP POSTURE

**`complete`: HELD, unchanged, NOT re-keyed — and no re-key is owed.** Rule 22
D-5(b) re-keys the marker's `keeper` field and re-verifies its `determination`
**on promotion**. Part 1 promotes nothing: the keeper shard, the
`calibration-complete.json` entry and every registry sidecar are byte-untouched.
The entry's recorded determination (CALIBRATED on
`2026-08-19-nyiso-146c-state-scoped`) was nonetheless re-verified from committed
artifacts this session and **still reads CALIBRATED** (§1), so the marker
asserts nothing that is not true at HEAD.

**Tier standing is unchanged**: validation ONLY (2022 and the ladder to 2020);
NYISO is ABSENT from `final`; its `locked_test` note reads *NOT AUTHORIZED*, and
under the 2026-08-06 D-23 correction that means **never granted**, not spent.

**The touchpoint loop is unaffected in principle and inert in practice.** The
**holdout spend freeze is ACTIVE** (`holdout-freeze.json`, `active: true`,
re-armed 2026-08-06) and outranks every marker, so no NYISO out-of-training year
may be solved, scored or registered today regardless of the `complete` grant.
Nothing in nyiso-147 or this session touches that: every year read, solved or
scored anywhere in this session is 2023, 2024 or 2025.

**What nyiso-147 DOES change is the advisable ORDER of the loop, if and when the
freeze lifts.** The loop's discipline is: run the touchpoint on the frozen
keeper recipe → diagnose the *object* it surfaces → re-train on 2023–2025 around
it → re-test. A 2022 spend today would run a recipe whose CHP grid capacities
are **already known to be wrong by a measured amount** — so a 2022 miss would be
uninterpretable in exactly the way the freeze's own rationale describes (is this
forecast error, or the carve?), and a 2022 *pass* would be actively misleading,
because §2.3 shows the same cancellation that flatters 2025 would flatter it.
This is the neiso-85/86 shape: 2022 surfaced an inverted fuel input, and the fix
was a data repair with zero DOF. Here the data repair is already in hand and
already known to be needed. **Recommendation (advisory, not a request): spend
NYISO's 2022 touchpoint AFTER the CHP capacity+conduct repair lands, not before.**
No lift is requested and none is implied.

---

## 4. (d) `final` — STILL NOT-YET ON THE MERITS

A `final` grant for NYISO remains **NOT YET**, and nyiso-147 strengthens the
answer. The two structural blockers stand, both re-verified at HEAD:

* **H1-2026 is unsolvable on the frozen keeper config.**
  `data/raw/NYISO-AS/requirements/` holds
  `NYISO_reserve_requirements_{2022,2023,2024,2025}.csv` — **no 2026 file** —
  against a loader that raises rather than falling back. Re-confirmed on disk
  this session.
* **2019 cannot discriminate.** Indian Point 2/3 are absent from every
  `eia860_generator*` vintage; `data/raw/lmp-data/NYISO/` holds no 2019 file;
  and 2019 carries **one** actual RT hour above $300, so it cannot discriminate
  on C3c — the very criterion NYISO's determination turns on.
* **NEW, from nyiso-147: the fleet the one-shot would be spent on is known to be
  misspecified.** The locked test is touch-once and its result may never be
  responded to. Spending it against a keeper whose CHP grid capacity carries a
  measured, quantified, already-derived correction — one whose arming moves
  C3a-2023 by 7.2 pp and C3a-2025 by 10 pp — would burn the year on a fleet the
  model itself no longer believes. That is the same argument the holdout freeze
  makes about the availability envelope, applied to capacity.

Nothing here should be read as proposing a grant. NYISO stays absent from
`final`; the gates refuse it; the answer is NOT-YET **on the merits**, not
merely on procedure.

---

## 5. THE QUEUE AFTER THIS ASSESSMENT

| # | object | kind | who decides |
|---|---|---|---|
| 1 | **CHP operating conduct** — lay-up membership + CC_CHP duty, the prerequisite that lets `nyiso_chp_btm_measured` arm | **model-side, lane** | a NYISO lane — **THIS session's Part 2** |
| 2 | **The 2025 dear-gas level**, and behind it the missing zonal gradient (§2.3) | **model-side, lane** | a NYISO lane |
| 3 | `cc_reserve_duty_split` re-arm on its standing prereg (PREREG-nyiso146b §ARM C) | model-side, lane | conditioned on 1 |
| 4 | Flynn start-count excess (right run length, ~3× starts) | model-side, lane | a NYISO lane |
| 5 | `RHO_CLIP` band | governance | owner (D-5(b)) — card delivered nyiso-145 |
| 6 | NYISO hydro 10-min ramp: certification + water limit | data intake | owner (funding/scope) |
| 6b | the three `ramp_capability` seams (nyiso-145 §5) | model-side, lane | a NYISO lane |
| 7 | `nyiso_iroquois_winter_spread` arming + taxonomy | governance ×2 | owner |
| 8 | a vintage guard for D-4's conduct rider | model-side, lane | a NYISO lane |
| 9 | the Astoria campus benchmark attribution | data repair | a NYISO lane |

Items 1 and 2 are the frontier blockers; items 3–9 are unchanged from nyiso-145
except that item 1 replaces its two entries with one better-specified one.

---

## 6. GOVERNANCE RECORD (Part 1)

* **No LP solved for this assessment**; no parameter moved; the keeper, its
  dashboard entry, the keeper shard, `calibration-complete.json` and
  `holdout-freeze.json` are all untouched. The two scorers were run read-only on
  committed bundles.
* **Rule 22**: holdout freeze ACTIVE and untouched; every year read or scored is
  2023, 2024 or 2025. No out-of-training year was solved, scored or registered.
  §3's ordering remark is advisory and requests no lift.
* **Rule 15**: Part 1 produces no registrable run — the two scorer invocations
  write no bundle. Nothing is withheld from the dashboard.
* **Rule 28(a)**: the NYISO shard, its gates stamp and the lever queue were read
  before any lever was proposed; the `chp_btm_measured` cell (R, nyiso-147) is
  the statement this document updates.
* **Rules 25 / 28(d)**: NYISO lane files only. The one cross-ISO artifact cited
  (miso-171's re-score record) is cited as MISO's own committed evidence about a
  SCORER, not transferred as a verdict.
* **DO-NOT-REDO, carried forward**: the measured BTM share values (frozen); the
  upstate fuel-basis candidate (refuted, nyiso-147 phase 0); nyiso-146's
  min-run / online-hours adjudications; `nyiso_downstate_ct_gas_daily` extension
  to LI CC/ST (refuted, nyiso-145); 7314 fuel/heat-rate/outage (refuted,
  nyiso-145); the Zone-K bound (closed, nyiso-143); the LI CC/ST delivered-gas
  re-grounding (refuted, nyiso-145); `nyiso_spin_reserve_online`'s `I`
  (nyiso-110, confirmed nyiso-144).
* **OUT OF LANE and untouched**: `RHO_CLIP` (owner card pending),
  `nyiso_iroquois_winter_spread`, the D-4 vintage-guard charter, the Astoria
  campus attribution.
