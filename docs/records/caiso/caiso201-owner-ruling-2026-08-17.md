# caiso-201 — OWNER RULING RECORD: THE CAISO BACKCAST LANE RESTS AT NOT-YET — 2026-08-17

**This document RECORDS the ruling the owner gave on 2026-08-17 via the caiso-201 session.
It is quoted as a RULING, not a proposal — nothing below is re-argued, and nothing below is
this session's recommendation.** The decision packet it answers is
`results/calibration/ASSESSMENT-caiso200-frontier-2026-08-17.md` §5 (Q1/Q2/Q3), whose own §0
recommendation was Q1.

Session caiso-201 is **READ-AND-WRITE-DOCS ONLY**: no code, no config, no data file, no
keeper, no status, no attestation, no marker touched; **no solve run**; **no run registered**;
no matrix cell verdict moved. Keeper unchanged at **`2026-08-17-caiso-200-h1-memberpanel`**
(NOT-YET; load-bearing FAILs C1-2023 CC_REGULAR −4.243 TWh vs ±4.15 and C3a +4.1 PASS / +12.8 /
+15.7 % vs ±10 %; C3c the single ledgered caveat; C6/C8 PASS; DOF 10/7). Those magnitudes
appear here only as the recorded state of the keeper — **C3a was not read as a number to act
on**, and no number in this document was produced by a new solve.

---

## The ruling

### Q1 — ACCEPT THE LANE'S RESTING STATE: **GRANTED.**

The CAISO backcast **holds at `NOT-YET`**, and that is recorded as the **designed honest
outcome of the program, not a failure of process**. Owner ruling 5 (caiso-191, 2026-08-11) —
*"C3a must genuinely pass; NOT-YET is the honest fallback"* — is discharged here exactly as
written: the criterion did not come to pass, so the lane reports the miss rather than
manufacturing the number.

**The lane goes quiet.** No further CAISO calibration session is opened without new funded
data. This is a *resting state*, not a closure of the question: the lane re-opens the moment
the owner funds one of the two standing objects below (or authorizes a genuinely new one under
rule 23), and it re-opens on the identical keeper recipe — nothing is retracted, dismantled or
frozen out.

What the lane rests on, stated so the resting state is auditable without replaying a solve:

* **The most structurally faithful configuration the program has produced for CAISO** — a
  fully-identified outage instrument (CC_REGULAR population coverage 1.000000; every fleet
  window testable against a panel its own plant belongs to), zero-forcing-clean, DOF ledger
  10/7 with zero fitted parameters in the caiso-198→200 delta, C6 and C8 protective gates
  green.
* **A C3a miss that is real and honestly declared** (+12.8 % / +15.7 %), never ledgered,
  never closed by an adder.
* **A C1 single-row miss measured — not asserted — to be the same root-cause lane.** caiso-200's
  pre-registered return watch answered **NO** at **+0.003 TWh** of a ~0.116 TWh restorable
  bound: the LP, offered the restored spring capacity, barely dispatches it. C1-2023 is
  thereby measured **~97 % structural** — the volume face of the standing CC-side
  under-dispatch / over-import lane (caiso-121 surplus-belly, caiso-135 ride-through,
  caiso-140 §B belly wedge), whose price face is C3a. **One lane owns both open faces.**

**`complete` is NOT declared and NOT supportable on the merits** (ASSESSMENT §0; owner ruling
5). **`final` is moot at two levels** (ASSESSMENT §6): `complete` is absent, so no validation
touchpoint may be spent, and the locked test is not reachable. CAISO holds **no `complete` and
no `final` marker**; `holdout-freeze.json` stays **ACTIVE**; **no out-of-training year was
touched** in this session or the one before it.

### Q2 — FUND EITHER STANDING OBJECT: **NEITHER FUNDED.**

A "no" to both is a "yes" to Q1 (ASSESSMENT §5), and that is the ruling given. Both objects
**remain available for future funding**; neither is retracted, and neither is re-argued here.

* **(a) The walled hourly PS water-state intake** (caiso-141 §G / ruling 4). **NOT funded** —
  ruling 4's DECLINE stands undisturbed. Recorded with its own disclosed limit: the
  owner-sitting arithmetic (caiso-186 §a) bounded its most favourable reach at **62.1 % /
  10.4 %** of the required 2024/2025 C3a move, so it is **partial by its own arithmetic** and
  likely does not close 2025 even fully funded. Fabricating the shape from monthly nets, from
  the model's own arbitrage profile, or from any assumed/fitted allocation stays **forbidden**
  under rule 13 `[R-MEASURED]` — an outcome-pin wearing a data costume.
* **(b) A new-evidence search for the 8,800 MW import spot capacities** (caiso-191 §4).
  **NOT funded** — the desk-adjudicated NO stands, and the four scalars stay a **declared
  residual** on the backcast binding path. Any future re-opening still requires the new
  citable evidence the **caiso-188 §7 fences** demand, and is a **data-intake session, not a
  solve**.

### Q3 — RATIFY THE RECORD CORRECTION: **RATIFIED (awareness only; no action).**

The caiso-199 §3 item-3 reading *"run Y reclassifies 9 of the 158, leaving 149 mechanical"* is
**corrected on measurement**: **all 158 Desert Star windows stay mechanical** — the fail-safe
was right for 100 % of them — and the 9 movers are pre-existing borderline **CA-facility**
windows (oom 0.900–0.932) tipped by the member CC's small RCC dip. The correction
**strengthens** the closure's case. It was already carried in `FINDING-caiso200 §3`, the
keeper shard, the matrix cell and ASSESSMENT §5; this ruling makes it owner-visible and
closes the item. Nothing was re-measured for it in this session.

---

## What is NOT ruled here

* **Nothing is retracted.** Every registered determination, gate record, caveat and finding in
  the CAISO lane stands exactly as scored.
* **No rubric amendment.** C3a stays un-ledgerable (v3.1 `LEDGERABLE_CRITERIA = {price_tail}`);
  ruling 5's inheritance arithmetic is untouched.
* **No marker, no grant, no spend.** No `complete`, no `final`, no touchpoint, no locked test.
* **No DO-NOT-REDO cell re-opened.** Export/absorption (caiso-142 §H), offer rungs (caiso-131
  §10), reserve tiers (caiso-144), `hydro_ror_split` (caiso-194), lane 6 without new evidence
  (caiso-191 §4), the caiso-197 composed cells, the caiso-198 unpinned CA+NV re-derive, the
  caiso-199 state-list pin legs and the caiso-200 §3b membership legs (G-DELTA (a)/(b) proven
  byte-identical both ways) all stay closed.
* **Cross-ISO: NOTHING TRANSFERS** (rule 25 `[R-ISO-SCOPE]`). The caiso-200 panel
  fleet-blindness closure is CAISO's verdict for CAISO alone; NYISO (NY+NJ), PJM and MISO each
  measure their own market. This ruling carries no verdict, posture or number into any other
  lane.

## Rule-15/16 note — why this session registers no run

Rule 15 `[R-DASHBOARD]` binds *completed backcast runs*, and rule 16 `[R-ALLYEARS]` binds the
year span of a run. **caiso-201 ran no LP**, so there is no bundle, no sidecar and no dashboard
registration — stated explicitly so the absence is not read as a skipped duty (the ercot-175 §0
/ ercot-177 precedent for recording a no-run session). The CAISO dashboard lane stays **the
keeper alone**, per the standing 2026-08-15 site-retention directive.

## Reference chain (nothing new is argued in this record)

1. `results/calibration/ASSESSMENT-caiso200-frontier-2026-08-17.md` — the decision packet: §0
   the recommendation, §1 the measured keeper state, §2 what caiso-200 settled about C1-2023,
   §3 the citation chain, §4 the two objects, §5 the sitting, §6 `final` readiness.
2. `results/calibration/FINDING-caiso200-panel-membership-2026-08-17.md` — the last in-model
   object landed, promoted, and its C1 hypothesis measured at +3 GWh; §3 the record correction.
3. `results/calibration/caiso191-owner-rulings-2026-08-11.md` — ruling 4 (PS purchase
   DECLINED), ruling 5 (C3a ledgering DECLINED), lane 6 (desk-adjudicated NO), and the CLOSED
   lane inventory: *"the campaign outcome is an exhaustion memo, not an improvised new lane."*
4. `results/calibration/FINDING-caiso197-wave2-promotion-2026-08-16.md` §4 — the close-out
   campaign exhausted as chartered, with the C3a residual honestly declared.
5. `docs/calibration-log/caiso.md` — the caiso-201 lane entry recording this ruling.
