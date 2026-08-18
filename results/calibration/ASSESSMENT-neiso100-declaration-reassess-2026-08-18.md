# ASSESSMENT — neiso-100: NEISO's `frontier` / `complete` / `final` declarations re-assessed under rubric v3.3

**Session:** neiso-100 · **Date:** 2026-08-18 · **Keeper at HEAD:** `2026-08-17-neiso-99-joint-p1`
**Mode: NO-SOLVE.** No LP was constructed. No year of any tier was solved, scored or registered.
**Nothing is granted.** `final` remains the owner's call and this session does not make it.

---

## 0. Headline

| question | answer at HEAD |
|---|---|
| **Frontier** — does it still hold on the current keeper? | **YES**, re-measured on the keeper's own bytes. Both legs reproduce exactly. |
| **Frontier** — does v3.3 change what it claims? | **NO** — but *not* because declarations are rubric-independent. It survives on the **ledgerability invariant**, argued in §1.2. |
| **Complete** — does the determination re-verify? | **YES — `CALIBRATED`**, on committed artifacts, no solve. 0 FAILs, C3c the lone ledgered caveat. |
| **Complete** — is the promotion-time prose stale? | **HISTORICAL RECORD, not stale state.** Left verbatim; one mis-scoped cross-reference repaired. §2. |
| **Final** — grantable? | **NOT YET.** Both halves still blocked, both re-measured rather than quoted. Decision card at §4. |
| 2025 EIA-923 final vintage | **STILL NOT LANDED.** Re-checked; NEISO CC_REGULAR 13/30 missing (57 % reporting), CC_CHP 3/7. |

Two standing escalations that every session since neiso-83 could only re-confirm as open are
**confirmed CLOSED at HEAD** (§5). One cross-lane item filed by neiso-99 is **already resolved** and
is not carried forward (§6).

---

## 1. FRONTIER — re-verified on the current keeper, and the v3.3 question answered

### 1.1 The measurement (probe `scripts/probes/neiso99_declaration_recheck.py`, re-run at HEAD)

The keeper has **not moved** since neiso-99, so the probe is correctly targeted and was re-run
unmodified. Its record `results/calibration/_neiso99_declaration_recheck.json` came back
**byte-unchanged against the committed copy** — the strongest form of "the declaration still holds":
the re-derivation is bit-reproducible, not merely concordant.

| leg | measured on `neiso99_joint_B/hourly/` |
|---|---|
| C3c model tail > $300/MWh | **0 h in 2023, 2024, 2025** on the now-sole **P1** production pass |
| agreement with published payload | `ordc.hoursGt200.model` **0 / 0 / 0** vs RT actuals **15 / 8 / 20** — one measurement, not two |
| annual maxima (max-across-zones) | 248.9682 / 218.2412 / **280.8542** $/MWh |
| closest approach | **$19.15 short of $300 (93.6 %)**, 2025 — not a near miss |
| RCPF co-optimization | **DORMANT**: `shortfall_mw = 0.0`, `held_mw ≥ requirement` in **all 78,840** family-hours |
| requirements | checked against `NEISO_RCPF_PRODUCTS` (1,800 / 1,200 / 600 MW), not read off the artifact |
| max \|dual\| | **exactly 0.000e+00** |

**No C3c lever was opened** (rule 28a DO-NOT-REDO on every `R`/`I`/`G` cell in the NEISO shard).
No mechanism was tested; no cell verdict moves on a mechanism basis.

### 1.2 Does v3.3 change what "frontier" claims for NEISO? **No — and the reason is not "rubric-independence"**

The prompt's prior was that the declaration is rubric-independent because it is a statement about
admissible mechanisms tried rather than about a determination band. **That prior is too strong, and
the repo contains the counter-example.** It is argued rather than assumed here.

**The counter-example: CAISO, v3.1, 2026-08-06.** Rubric v3.1 narrowed ledgering to C3c alone.
CAISO's C3a caveats became `FAIL`, its determination went `CALIBRATED-WITH-CAVEATS → NOT-YET`, and
**its `complete` marker *and its frontier claim* were withdrawn the same day**
(`docs/calibration-determination-rubric.md` §9 v3.1; `calibration-complete.json`.`withdrawn`.CAISO).
So a rubric amendment demonstrably *can* strip a frontier claim. A blanket
"frontier is rubric-independent" argument is false and would have been refuted by that precedent.

**What the CAISO withdrawal actually turned on** is stated explicitly in the same passage, and it is
the load-bearing distinction:

> Its frontier *evidence* is not retracted (…) what is withdrawn is the claim that an empty lever
> queue on C3a is terminal. **On a non-ledgerable criterion an empty queue is an *open root-cause
> item*, not a documentable bound.**

This decomposes a frontier declaration into two separable parts:

1. **Frontier evidence** — the adjudicated mechanism ledger: what was tried, what was refuted, what
   was proven inert. This is *never* retracted by a rubric change and stays DO-NOT-REDO.
2. **The frontier claim** — that an exhausted admissible-mechanism queue on this criterion is a
   **documentable bound** rather than an open root-cause item. This is rubric-dependent, and the
   property it depends on is precisely **whether the criterion is LEDGERABLE**.

**NEISO's frontier is declared on C3c**, which since v3.1 is the *only* ledgerable criterion.
**v3.3 leaves that property untouched.** Checked against the amendment's own text, all four guards
survive: (a) lone-failure only, (b) governance must PASS, (c) **supporting tier only, fail-closed** —
so C3c's tier is unchanged, and (d) it is **never a PASS**, still reported at full magnitude, still
named on the determination basis, still counted in `caveats.ledgered`, still spending the single
ledgerable slot. What v3.3 changed is *only what a ledgered caveat COSTS the determination band*
(downgrade → report-only). It changed nothing about ledgerability, tier, magnitude or evidence.

**Therefore:** the declaration survives v3.3 on the **ledgerability invariant**, not on categorical
rubric-independence. Stated as a falsifiable rule for future sessions:

> A NEISO frontier claim on C3c is disturbed by any amendment that removes C3c from
> `LEDGERABLE_CRITERIA`, or that promotes it out of the SUPPORTING tier. It is *not* disturbed by an
> amendment that only re-prices what a ledgered caveat costs the determination band. v3.3 is the
> second kind.

### 1.3 One governance observation, recorded against interest

v3.3 makes a ledgered C3c **cheaper to carry** — the same residual, at the same magnitude, no longer
costs a determination band. The frontier's DO-NOT-REDO discipline is unchanged and no lever is
re-opened here, but the *incentive* to charter the named successor (a **new measured identification**
on oil-parity / import / DA-bid offer formation, which is the declaration's own stated exit route) is
reduced by exactly that amount. This is worth the owner's attention as a standing-incentive effect,
not as an argument against the amendment. **It is not a request to re-open C3c.**

**`frontier.reverified` is re-stamped either way**, as the charter requires.

---

## 2. COMPLETE — determination re-verified, and the prose adjudicated as HISTORICAL RECORD

### 2.1 The re-verification (rule 22 D-5(b), committed artifacts, **no solve**)

`scripts/calibration_verdict.py --run-id 2026-08-17-neiso-99-joint-p1` at HEAD:

```
CALIBRATION DETERMINATION: CALIBRATED
  scorable years: 2023, 2024, 2025
  C1 PASS · C2 PASS · C3a PASS · C3b PASS · C4 PASS · C6 PASS · C8 PASS
  C3c CAVEAT [ledgered]  — model 0 h vs RT actual 15 / 8 / 20 h > $300
  D-10 free-class C1: all 12/12 · free 8/8
  determination basis: 1 ledgered caveat — REPORTED, and NOT determination-downgrading under v3.3
```

`scripts/audit_keepers.py --iso NEISO` → **PASS, 0 failures / 0 warnings** (check M1 included).
**D-5(b)'s worse-determination stop does not fire** — the determination is not worse.

### 2.2 The prose question: **HISTORICAL RECORD (leave), with one mis-scoped pointer repaired**

The prompt's premise is **partly superseded and is corrected here rather than acted on blindly**:
`calibration-complete.json`'s NEISO `determination` **already reads `CALIBRATED`** — it was re-keyed
under v3.3 by the cross-ISO `nyiso-calibration-declaration` session, with the pre-amendment text
preserved after a `||` marker. Nothing there is stale. Likewise `keepers/NEISO.json` already carries
a top-level `determination_amendment` recording the v3.3 re-read.

What remains narrating `CALIBRATED-WITH-CAVEATS` is `keepers/NEISO.json`.`disposition_note`, and it
opens: *"DETERMINATION CALIBRATED-WITH-CAVEATS on 2026-08-17-neiso-99-joint-p1, verified by
`calibration_verdict.py --run-id` on COMMITTED ARTIFACTS **at promotion** (rule 22 D-5(b))"*.

**That is a dated, scoped assertion about what was verified at the promotion, and it was correct
when made.** Rewriting it would falsify what the neiso-99 promotion actually asserted about itself —
the same reason neiso-99 gave for declining to repair a registered run's evidence record. **It is
left verbatim as historical record.**

**One real defect IS repaired**, because it is a cross-reference rather than an assertion:
`determination_amendment` scopes itself with *"The notes above are left verbatim"* — but it is the
**first** key in the shard, so there are no notes above it, and a reader cannot tell which fields the
amendment covers. The pointer is repaired to **name the fields** (`note`, `prior_keeper_note`,
`disposition_note`, `holdout_touchpoint`). Substance untouched; no determination statement is edited.

---

## 3. The 2022 touchpoint — the standing "not worth re-iterating" claim RE-MEASURED, and one leg of it has expired

The charter said to re-measure rather than repeat this. Doing so found that **neiso-98's argument
had three legs and neiso-99 asserted the third one forward without measuring it.**

neiso-98 §3.3 concluded a 2022 re-iteration was not worth requesting **on instrument-repair
grounds**, resting on:

| leg | status at HEAD |
|---|---|
| 1. C3c untouched by construction — 2022's max repaired cell $138.65 vs the $300 threshold | **STANDS.** Unaffected by anything since. |
| 2. C3a untouched to scored precision — 47/8,760 RT cells, effect ≤ $0.008/MWh | **STANDS.** |
| 3. *"The model side has not moved either"* (neiso-97 dispatch bit-identical) | **EXPIRED.** neiso-99 is the first non-no-op keeper change since neiso-93. |

**neiso-99 §6's forward-assertion — "this session's model-side change is small enough that the same
holds" — is measured here, and it is not quite right as stated.** Measured at hash grain on
`meta.json`'s content-addressed `shared_inputs`, the standing touchpoint
`2026-08-06-neiso-2022-corrected-basis` (bundle `neiso86_2022_corrected`) now differs from the
designated keeper on **six axes**, not zero — of which **three were already stale at neiso-98** and
went unreported there, while neiso-99 added the outage pair *and* the scored pass:

| axis | touchpoint | keeper | |
|---|---|---|---|
| scored pass | `commitment=True`, `["P1","P2"]` | `commitment=False`, `["P1"]` | **differs** |
| `unit_outages` | `d2df8f1e6357` | `c6be5bbb89ab` | **differs** (pre-guard extract) |
| `unit_outages_layup` | `cb80c81b7c2b` | `c622c4d5058e` | **differs** |
| `campd` | `39ee0bebce26` | `28501f5539d0` | **differs** |
| `eia923` | `6fe297dbc11e` | `a2384ce8cfeb` | **differs** |
| `eia930` | `fa8cba2e1ec2` | `d398d867c742` | **differs** |
| `unit_outages_{short,partial,e923}` | — | — | identical |

Three of these (`campd`, `eia923`, `eia930`) were **already** stale at neiso-98 and went unreported
there; neiso-99 added the outage pair **and the scored pass**. So the touchpoint is not merely
instrument-stale — **it is on the archived P2 basis that neiso-99 just moved the keeper off**.

### 3.1 The magnitude, bounded by measurement on 2022 itself rather than by analogy

The obvious objection to bounding this from the tuned years is that 2022's exposure could be larger.
**Measured directly**, by diffing the pre-guard extract (`ef9e911^`) against HEAD on a
`(facility_id, unit_id, outage_start, outage_end)` key and counting windows that **overlap** each
calendar year:

| year | guard-removed windows overlapping | MW-window sum |
|---|---|---|
| 2021 | 24 | 1,282.0 |
| **2022** | **19** | **1,419.0** |
| 2023 | 29 | 1,856.0 |
| 2024 | 28 | 1,784.0 |
| 2025 | 37 | 2,557.0 |

**2022 carries the *smallest* window count of any year 2018–2025**, and a MW-window sum **24 % below
2023, 20 % below 2024 and 45 % below 2025**. The routing leg's measured effect in the tuned years is
mean λ **−0.0162 / −0.0133 / −0.1112 $/MWh** with annual maxima unmoved; 2022's exposure is strictly
smaller than any of them, so its routing effect is bounded below that band **by measurement, not by
extrapolation**.

The basis leg (P2 → P1) is a **pure re-render** — neiso-99 proved it bit-identical to the superseded
keeper's own persisted P1 across 192,720 rows/year — so it moves the *published* statistic, not the
dispatch; on the tuned years it is worth mean λ −0.0575 / −0.0110 / −0.0378 $/MWh.

**Conclusion, stated at the honest strength.** The touchpoint's determination almost certainly
reproduces: the combined 2022 effect is bounded well under ±0.2 $/MWh on mean λ (orders inside any
C3a band), and **C3c cannot move at all** — the model tail is 0 h and its 2022 maximum would have to
climb to $300 to register against a 117-hour actual tail. But that is now a *bound on the expected
delta*, **not** the "like-for-like, nothing moved" standing neiso-98 could claim. **A 2022
re-iteration is still NOT requested** — the expected information is near zero and the freeze is the
owner's — but the record should say **why** it is not worth spending (small measured bound) rather
than **that nothing changed** (no longer true).

### 3.2 A re-score of the touchpoint under v3.3 was **considered and refused**

The 2022 touchpoint's registered determination is `CALIBRATED-WITH-CAVEATS` carrying **C3c as its
sole caveat** — exactly the shape v3.3 reclassifies. Re-reading it would plausibly return
`CALIBRATED` on already-committed artifacts with no solve.

**It was not run.** `frontend/data/backcast/holdout-freeze.json` is `active: true` and its
`scope.frozen_operations` names **`solve`, `score`, `dashboard registration`** across **ALL** ISOs
and **both** tiers. "Score" is frozen, and the freeze **outranks the `complete` marker** and is
checked first. A scorer-side re-read is still a score. **Fail-closed discipline applies: not run,
and flagged for the owner instead.** If the owner wants the touchpoint's v3.3 re-read, it is a
one-command, no-solve operation gated behind a freeze decision — not a session's call.

### 3.3 Non-guard churn in the same diff — measured, and it touches nothing

The pre/post extract diff carries 257 removed rows in total. The **guard** accounts for **239** at
the four plants neiso-99 names (568 Bridgeport, 1588 Mystic, 1595 Kendall, 6081 Stony Brook).
**This reconciles exactly with neiso-99's "236 rows"**: 6081 004 (74) + 005 (74) + 1595 S6 (53) +
568 BHB4 (11) + 1588 MJ-1 (24) = **236**; the extra 3 are 568 BHB3 (1) and 6081 001/003 (1 each) —
**sibling window re-merges downstream of the removals**, not guard removals, and independently
visible as 6081 001 going 22 → 21 rows and 003 going 7 → 6.

The remaining **18** rows are whole-file re-derive churn at seven other plants, and they are
**confined entirely to 2019, 2020 and 2026 — ZERO in 2021 through 2025**. Five are Merrimack COAL
window-boundary shifts (2019–2020); thirteen are 2026 windows from a still-accumulating CAMPD tail.
**The churn touches neither the training window nor the 2022 touchpoint.**

---

## 4. FINAL — re-answered on the merits: **NOT YET.** Owner decision card

**This grants nothing.** NEISO stays absent from `final`; its locked test remains **NEVER GRANTED
and NEVER SPENT** (owner decision D-23 — the withdrawn "spent 2026-07-07" claim is not repeated).
Every blocker below is **re-measured at HEAD**, not quoted.

### 4.1 The 2019 half — **still NO**

**(a) 2019 cannot exercise C3c — the criterion NEISO's frontier is declared on.** Re-measured on the
DST-repaired instrument (`actual_lmp_hourly_NEISO.parquet`, an INPUT read; no model side, nothing
scored):

| year | RT max | RT h > $300 | DA max | DA h > $300 | rows | coverage |
|---|---|---|---|---|---|---|
| **2019** | **$261.35** | **0** | $178.43 | 0 | 8,760 | 1.0000 |
| 2020 | $236.11 | **0** | $155.02 | 0 | 8,760 | 1.0000 |
| 2021 | $375.28 | 2 | $203.41 | 0 | 8,760 | 1.0000 |
| 2022 | $2,254.35 | **117** | $374.98 | 27 | 8,760 | 1.0000 |

The real 2019 market had **zero** RT hours over $300. C3c would return a free small-count PASS
whatever the model did. **Spending the touch-once year buys a verdict silent on the open question.**
**2020 is C3c-degenerate the same way** — of the whole validation ladder only **2022** exercises the
criterion decisively, and 2021 offers 2 hours.

**(b) The Pilgrim fleet-vintage gap — a cross-ISO charter, and a hard precondition.** Re-measured
(`neiso94_pilgrim_vintage_audit.py`): Pilgrim (EIA 1590, 670 MW) ran Jan–May 2019 and retired
31 May 2019, and is absent from the EIA-860 operable snapshot. The 2019 monthly gap carries the
step signature exactly — **Jan–May −2.146 TWh, Jun–Dec +0.023 TWh** — against a 2019 C1 volume band
of **2.366 TWh**, i.e. **~91 % of the band consumed by a known fleet-vintage defect** before the
model is asked anything. Blast radius of lowering `RETIREMENT_WINDOW_START` 2023 → 2019: **264
plants / 21,467.5 MW across all six ISOs** (NEISO 21 / 914.2 MW). Chartered at
`docs/handoffs/fleet-vintage-retiree-window-charter-2026-08.md`. **Not a NEISO lane item.**
It does **not** touch 2023–2025: every affected plant retired before the training window.

**(c) One stale clause in the owner's `locked_test` field, measured false at HEAD — flagged, NOT
edited (third session running).** The field reads *"2019 is UNSOLVABLE at HEAD
(`eia_demand_profiles.parquet` carries NEISO 2021-2025 only, so the LP cannot be constructed)"*. Its
premise about that **fallback** file is true, but the **primary** path resolves — measured directly:

```
_eia_hourly_frame('ISNE', 2019) -> 8760 rows      _eia_hourly_frame('ISNE', 2022) -> 8760 rows
_eia_hourly_frame('ISNE', 2020) -> 8760 rows      _eia_hourly_frame('ISNE', 2023) -> 8760 rows
_eia_hourly_frame('ISNE', 2021) -> 8760 rows      _eia_hourly_frame('ISNE', 2026) -> None (REJECTED)
```

**2019 is demand-solvable at HEAD.** The clause's *conclusion* is unaffected — legs (a) and (b) are
live and each is sufficient on its own — but its *stated reason* is wrong, and a future reader could
act on it. It is **left unedited**: it is the owner's reasoning, and this session's authority is the
D-5(b) determination re-verification, not a rewrite of that field. To stop the drift persisting
invisibly a fourth time, here is the exact replacement the owner could adopt verbatim:

> *2019 is DEMAND-SOLVABLE at HEAD (`ISNE_region.parquet` returns 8,760 rows for 2019 via
> `eia930.frames._eia_hourly_frame`; the `eia_demand_profiles.parquet` 2021–2025 limit is a fallback
> path only). It is nonetheless NOT READY: 2019 cannot exercise C3c (RT max $261.35, 0 hours > $300),
> and the Pilgrim fleet-vintage gap costs ~91 % of the 2019 C1 volume band.*

### 4.2 The H1-2026 half — **still NO, and the blocker is not NEISO's**

The six-ISO partial-year solve gate is **live at HEAD**, measured rather than read:
`_eia_hourly_frame('ISNE', 2026)` → **`None` (REJECTED)**. `ISNE_region.parquet` holds **13,460 rows
for 2026 against 35,040 for a full year — 3,365 distinct hours of 8,760**, across all four types
(D / DF / NG / TI). `frames.py` gates on `len(df) != HOURS_PER_YEAR`, in **shared code, blind to
ISO**: the model cannot build a partial-year solve **for anybody**. Structural, six-ISO, tractable —
**that lane's, not this one's.**

### 4.3 Decision card — what would have to change to make 2019 informative

The `final` grant is the owner's. **Nothing here requests it.** What it would take, in dependency
order:

| # | precondition | owner? | status |
|---|---|---|---|
| 1 | **Fleet-vintage retiree window** — `RETIREMENT_WINDOW_START` 2023 → 2019, cross-ISO (264 plants / 21.5 GW). Without it a 2019 solve is short ~2.15 TWh of nuclear, ~91 % of the C1 band. | cross-ISO charter | **OPEN**, chartered, not a NEISO lane item |
| 2 | **Three absent 2019 scoring inputs** — `calibration_reference`, `actual_tail`, renewable-capacity (neiso-87 §3). `bench/NEISO/` holds 2022–2025 only; `actual_tail.json` has no 2019 row. | data intake — **unrestricted** under rule 22's 2026-08-06 clarification (intake is never held out) | **OPEN**, and preparable *today* without any grant |
| 3 | **Accept that 2019 cannot discriminate on C3c** — 0 actual RT hours > $300. The touch-once year returns a verdict silent on the criterion the frontier is declared on. | owner judgement | **structural — cannot be fixed**, only accepted or worked around |
| 4 | **Holdout spend freeze** lifted or narrowly scoped | owner | **ACTIVE** since 2026-07-25 |
| 5 | **`final` marker** granted for NEISO | owner | **ABSENT** — never granted |

**The honest framing of #3, which is the crux.** #1 and #2 are engineering and will resolve. #3 will
not. NEISO's frontier is declared on C3c, and 2019 is the one year on the board that **cannot** test
it. Three readings are open to the owner, and this session recommends the third:

- **(i) Spend 2019 anyway**, accepting a certified out-of-sample number that is informative on
  C1/C2/C3a/C3b/C4 and *vacuous on C3c*. Legitimate — those are five load-bearing criteria — but it
  permanently consumes the touch-once year without touching the open question.
- **(ii) Hold 2019 indefinitely** until a C3c-bearing locked-test year exists. There is none: the
  locked tier is {2019, H1-2026}, and H1-2026 is blocked by a six-ISO gate with no owner in this lane.
- **(iii) RECOMMENDED — ask the owner to designate a replacement locked-test year that can
  discriminate**, and treat 2019 as a *supporting* out-of-sample check rather than *the* test.
  Rule 22 already contemplates this ("*No calibration change may respond to a locked-test result
  without designating a new never-touched year as its replacement*"). NEISO's never-touched,
  C3c-bearing candidates are **2021** (2 RT hours > $300 — thin) and, if the ladder were ever
  extended below 2020, earlier years — but **note honestly that 2018 and earlier are DROPPED and
  unrepairable for NEISO** (the ISO-NE newswire migration left Mar–Jun 2018 on the inverted EIA
  N3050MA3 proxy). **The realistic candidate set is thin, and that is itself the finding worth
  surfacing: NEISO may simply have no locked-test year capable of certifying the criterion its
  frontier rests on.**

**Recommendation to the owner: do NOT grant `final` for NEISO now.** Resolve #1 and #2 first — #2 can
proceed immediately with no grant of any kind — and settle #3 as an explicit decision before any
2019 spend, because the spend is irreversible and, as things stand, would not answer the question.

---

## 5. Standing escalations — both CONFIRMED CLOSED at HEAD

Re-measured with `scripts/probes/neiso98_escalations_and_final_readiness.py`; its record
`_neiso98_escalations.json` is updated in place and the diff **is** the closure evidence.

**Audit row O5 — the archived-P2 scoring basis. CLOSED, and now across all six ISOs:**

| ISO | keeper | `commitment` | `passes` |
|---|---|---|---|
| CAISO | `2026-08-17-caiso-200-h1-memberpanel` | false | `["P1"]` |
| ERCOT | `2026-08-17-ercot215-arm-decontam` | false | `["P1"]` |
| MISO | `2026-08-16-miso-160-wefor-shape` | false | `["P1"]` |
| **NEISO** | **`2026-08-17-neiso-99-joint-p1`** | **false** | **`["P1"]`** |
| NYISO | `2026-08-16-nyiso-140-layup-exclusion` | false | `["P1"]` |
| PJM | `2026-08-15-pjm-162-inputclock` | false | `["P1"]` |

`isos_on_legacy_p2: []`. NEISO was the sole holdout across three keeper generations; it is no longer.

**The Stony Brook 6081 outage routing. CLOSED.** Units **004 and 005 are gone** from
`campd-unit-outages-NEISO.csv` (74 rows each pre-fix); only the genuine CC units 001 / 002 / 003
remain, at 21 / 30 / 6 rows.

---

## 6. Data wait, and cross-lane items

**2025 EIA-923 final vintage: STILL NOT LANDED.** Re-checked with
`scripts/audit_eia923_completeness.py --year 2025 --no-write` (no write, canonical part untouched).
NEISO reproduces the committed block exactly: **CC_REGULAR INCOMPLETE, 13/30 prior plants missing
(57 % reporting); CC_CHP INCOMPLETE, 3/7 (57 %)**; CT_CHP 15/24 (38 %). The 2025 C1 CC rows stay
**SKIPPED by design** and C2's 2025 gas row stays SKIPPED. **Nothing estimated around it.**

**Carried forward for other lanes (rule 25 `[R-ISO-SCOPE]`), still open.** The neiso-99 liquid-fuel-CT
routing guard would drop mis-routed rows at **PJM** 593 Edge Moor 10 (33), **MISO** 2001 New Ulm 7
(114) and 8056 Waterford 4 (103), and **NYISO** 2516 Northport UGT001 (42). Each needs that lane's
own re-solve. **No cell outside NEISO is stamped here.**

**NOT carried forward — already resolved.** `scripts/check_registry_payload_parity.py` was reported
failing at HEAD on `results/calibration/ercot215_control_A`. **Re-run this session: `registry/payload
parity OK (26 runs checked, 26 bundle dirs swept, 0 known-unsynced tolerated)`.** The ERCOT lane
closed it; it is dropped from the carry-forward list rather than repeated.

---

## 7. Rule compliance

* **Rule 1 `[R-STRUCT]`** — no mechanism was tested, tuned or judged by a residual.
* **Rule 15 `[R-DASHBOARD]`** — **no run was produced, so nothing is registrable.** The session left
  **zero in-sample delta**: the keeper is unmoved, the frontier probe's record is byte-unchanged, the
  determination re-verifies, `audit_keepers --iso NEISO` passes 0/0.
* **Rule 16 `[R-ALLYEARS]`** — not engaged; no solve.
* **Rule 22 `[R-HOLDOUT]`** — **no out-of-training year was solved, scored or registered.** Every
  out-of-training read was of a **measured input** with no model side (rule 22's 2026-08-06
  clarification: what is held out is the *score*, never the *data*). The freeze was verified
  **ACTIVE** and a candidate 2022 re-score was **refused** on it (§3.2). NEISO's locked test remains
  **NEVER GRANTED, NEVER SPENT**.
* **Rule 25 `[R-ISO-SCOPE]`** — only NEISO's keeper shard, status and matrix shard are touched.
* **Rule 28 `[R-MECH-MATRIX]`** — `docs/codebase-site/data/mechanism-matrix/NEISO.js` re-stamped
  (keeper + gates). **No cell verdict moves**: no mechanism was tested.

## 8. Artifacts

* This assessment.
* `results/calibration/_neiso98_escalations.json` — re-measured at HEAD (both escalations closed).
* `results/calibration/_neiso99_declaration_recheck.json` — re-run, **byte-unchanged**.
* `results/calibration/_neiso94_pilgrim_vintage_audit.json` — re-measured at HEAD.
* `scripts/probes/neiso100_touchpoint_staleness.py` — new; the §3 hash-grain and window-overlap
  measurement, with its record `_neiso100_touchpoint_staleness.json`.

**Next shorthand: `neiso-101`.** No NEISO tuning lever is open. The lane's remaining items are the
**data wait** (2025 EIA-923 final vintage) and **three owner decisions**: the `final` grant (§4.3),
the touchpoint v3.3 re-read behind the freeze (§3.2), and the stale `locked_test` clause (§4.1c).
