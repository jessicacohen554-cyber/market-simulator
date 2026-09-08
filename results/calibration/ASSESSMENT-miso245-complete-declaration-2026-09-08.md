# ASSESSMENT — **is MISO ready for a `complete` marker (the 2022 validation touchpoint)?** ZERO LP, committed artifacts only

**Answer: YES ON THE MERITS, and one owner declaration away — but the case is weaker than PJM's was
in one specific, named respect, and that respect is stated in §6 rather than buried.**

**This document decides nothing.** `complete` is an explicit owner act, per ISO, every time (rule 22
`[R-HOLDOUT]`). Nothing here grants it, and no out-of-training year was solved, scored or registered
to produce it. **No LP was spent.** Every number below is read from committed artifacts or measured
from the committed matrix.

---

## 1. THE GATE, MEASURED — the freeze is not the obstacle; the marker is

`scripts/lib/holdout_policy.py`, read against the committed
`calibration-complete.json` + `holdout-freeze.json`:

```
tier_for_year(2022)  = validation
frozen tiers         = {locked_test}          ← the VALIDATION tier is NOT frozen
                                                (lifted 2026-08-26, owner ruling card 6)

registration_refusals([2022], "MISO")  -> REFUSED:
    "MISO year(s) [2022] are validation-tier, and MISO does not carry the
     'complete' marker ... AT REGISTRATION TIME"

registration_refusals([2022], iso) for NYISO / CAISO / ERCOT / PJM / NEISO  -> ALLOWED
```

**MISO is the ONLY one of the six ISOs without a `complete` marker.** `complete` currently holds
ERCOT, NEISO, PJM, CAISO, NYISO; `withdrawn` is empty; `final` holds no ISO at all. So the single
thing standing between MISO and its 2022 touchpoint is the marker — not the freeze, not data, not
tooling.

*(Note against interest: the freeze file's own prose still reads "ERCOT/CAISO/MISO hold no `complete`
marker". That sentence is **stale** — it was written 2026-08-26 and ERCOT and CAISO have since been
granted. The machine check above, not the prose, is what refuses MISO.)*

## 2. THE DETERMINATION, RE-VERIFIED WITHOUT A SOLVE

`scripts/calibration_verdict.py --run-id 2026-09-08-miso-245-ladderfix`, committed artifacts only:

```
CALIBRATION DETERMINATION: CALIBRATED
  scorable years: 2023, 2024, 2025
  [✓] PASS  LOAD  C1 fuel-mix by class      — all 16/16, free 12/12
  [✓] PASS  LOAD  C2 system volume (gas/coal families)
  [✓] PASS  LOAD  C3a mean LMP
  [✓] PASS  LOAD  C3b price duration/shape
  [~] CAVEAT SUPP C3c price tail / scarcity  [ledgered, non-downgrading, rubric v3.6]
  [✓] PASS  SUPP  C4 fleet hourly dispatch correlation
  [✓] PASS  PROT  C6 governance gate
  [✓] PASS  PROT  C8 forced share
  grade summary: scored 8 / target 7 / ledgered 1 / fails 0      DOF ledger: 41 / 2
```

C3c at full magnitude, reported and not softened: **model 3 / 7 / 11 h > $200 against a measured
30 / 37 / 88 h (0.10× / 0.19× / 0.12×)**. It is the single ledgered caveat and the designated frontier
since 2026-07-20, and it is the **same caveat five of the six ISOs carry**.

**Stated in place: 2025 C1 is SKIPPED on eight classes** on the preliminary EIA-923 vintage
(26–85 % reporting). No 2025 C1 pass is read as evidence anywhere in this assessment, and C2's family
grid reconcile is what covers those classes.

## 3. WHAT `complete` ACTUALLY ASSERTS — read from the entries that already exist

From PJM's entry (`by`, owner verbatim 2026-07-31): *"complete only means 2022 test point can run. No
training on 2022 data, just test and then train issues back on 2023-2025."* And its
`tier_authorized`: *"validation ONLY (2022). NOT training … A 2022 number is selection evidence,
never a certified out-of-sample skill number."*

So the marker is **not** a statement that the model is finished. It authorises the touchpoint loop
rule 22 describes: run 2022 on the frozen recipe → **diagnose the object it surfaces** → re-train on
2023–2025 → re-test. The substantive question is therefore narrower than "is MISO done": it is
**has in-sample work stopped producing information, so that a held-out year is now the cheapest way to
find the next object?**

The bar PJM was granted on is its `frontier_basis` field: *"Structural lever queue measured EMPTY at
pjm-142."*

## 4. THE CASE FOR — and the strongest item is the one that cost this lane a promotion

1. **ELEVEN CONSECUTIVE SESSIONS ARMED NOTHING.** miso-235 through miso-245 produced **zero new
   `ScenarioConfig` fields, zero armed mechanisms and no cell verdict move in either direction**.
   The DOF ledger has stood at **41/2** across all of them.
2. **BOTH PROMOTIONS IN THAT WINDOW WERE CORRECTNESS RE-DERIVES, NOT CALIBRATION LEVERS** — miso-243
   (a cross-year pairing defect) and miso-245 (a stale derivation vintage). Neither added a
   parameter; both are rule-14 `[R-ACCURATE]` repairs to committed inputs.
3. **THE MOST RECENT PROMOTION MOVED ZERO SCORED NUMBERS.** miso-245: **245 of 246 verdict numeric
   leaves byte-equal** to its predecessor, the single move a reported-only `co2` record at
   **+0.001 Mt**. When the best available in-sample repair changes nothing that is scored, in-sample
   work has stopped discriminating between configurations — which is precisely the condition a
   held-out year exists to break.
4. **THE LANE'S OWN NAMED FRONTIER IS REFUSED ON A DATA BOUNDARY, NOT A WORK BOUNDARY.** The SPP
   quantity-side charter is **REFUSED for want of a DOF-free form** (miso-241 §5, candidates C1–C7,
   with the C7 census over **all of `data/raw`** completed). No amount of further in-sample effort
   opens it; a new measured series or an owner ruling does.
5. **EVERY OTHER SEAM ROUTE IS ADJUDICATED**, not merely unexplored: queue item 1 ANSWERED AND
   DECOMPOSED; the merit test's sign and basis REFUTED; the external-bus-price identification CLOSED;
   the per-seam external-node split REFUSED at zero LP; saturation REFUTED; the (month × hod)
   template REMOVED; the PJM import/export asymmetry CLOSED; South's neighbour-state route CLOSED on
   a data boundary (SOCO and TVA publish no hub price); `miso_manitoba_seam` CLOSED as already-armed.
6. **THE OPEN-CELL COUNT IS NOT AN OBSTACLE, MEASURED RATHER THAN ASSUMED.** MISO's matrix shard
   carries **8 `O` cells of 312**; **PJM, which already holds `complete`, carries 7**. So an "empty
   queue" in the sense PJM was granted on has never meant zero open cells, and MISO's census sits in
   the same range as a granted ISO's.
7. **THE MARKER IS RE-KEYABLE AND ITS SPEND IS ITERABLE.** A validation number is model-SELECTION
   evidence by rule 22's own words, re-spendable, and can never certify or decertify the ISO
   (rule 30 (c)). The downside of granting it early is bounded; the downside of withholding it is
   that the lane keeps spending sessions on in-sample questions that no longer move anything.

## 5. THE CASE AGAINST — at full magnitude, and it is not empty

1. **THE STRUCTURAL ITEM RULE 1 NAMES IS OPEN.** The model's SPP seam is **0.70–0.79
   spread-correlated** while the measured one is **+0.0409 / −0.0200 / +0.0502**. The seam being idle
   is not the anomaly; **its being spread-driven is.** A 2022 miss on interchange would land on top of
   a known-open mechanism and would be that much harder to attribute.
2. **THREE NAMED ZERO-LP DIAGNOSTIC ITEMS HAVE NEVER BEEN TAKEN**: the model bus-price
   **compression** (miso-242 Q-B — σ(p_bus) 6.09 / 16.51 / 15.22 against σ(MISO DA)
   12.81 / 19.89 / 26.12, unresolved); **Manitoba determinism** (miso-236 §5.3 — measured
   (month × hod) template 0.7380 / 0.7205 / 0.6594 against the model's 0.6036 / 0.5207 / **0.2869**,
   a 2.3× gap by 2025 against an envelope the model already carries); and **CC_REGULAR's 2024→2025
   shape emergence** (open since miso-234). Each is an *attribution* question with no admissible
   lever attached — but none has been answered.
3. **TWO PROMOTIONS HAVE NOW BOUGHT STRUCTURE AND NOT FIT.** That is legitimate under rule 1, and it
   is also a reason to be honest that MISO's *fit* has not improved since miso-233.
4. **C3c IS UNCHANGED AND UNCHARTERED.** It stays the designated frontier and opens only by a new
   admissible measured identification plus an owner ruling.

## 6. **WHAT I DID NOT MEASURE — the one respect in which MISO's case is weaker than PJM's**

PJM's grant rests on a **formal, pre-registered census**: *"Structural lever queue measured EMPTY at
pjm-142"*, with the last non-adjudicated successor killed at a no-LP pre-check. **MISO has no
equivalent artifact.** What §4 offers instead is *circumstantial*: eleven sessions that armed nothing,
a frontier refused on a data boundary, and a promotion that moved zero scored numbers. That is a
strong pattern, **but it is a pattern, not a census**, and I am not going to dress it up as one.

**A MISO equivalent is cheap and is the honest alternative to granting on the pattern alone:** a
zero-LP session that enumerates every remaining backcast-lane route for MISO, adjudicates each as
`R`/`I`/`G`/refused-for-want-of-a-DOF-free-form, and either finds a live lever or records the queue
empty with its own pre-registered rule. The three items in §5.2 are the obvious first sweep. **If the
owner wants the PJM standard applied to MISO, that session is the prerequisite; if the owner is
satisfied by the pattern, the marker can be granted now.** Both are defensible and the choice is not
mine.

## 7. RECOMMENDATION

**GRANT `complete` for MISO.** The marker authorises exactly one thing — solving, scoring and
registering the 2022 validation touchpoint on the frozen keeper recipe — and MISO's in-sample work has
demonstrably stopped discriminating (§4.3 is the decisive number). The open items of §5 are
**attribution questions with no admissible lever**, which is the state in which a held-out year is the
cheapest remaining instrument, and a validation number cannot certify or decertify the ISO in either
direction.

**The honest caveat on that recommendation, stated rather than left to be inferred:** MISO's case is
made on a *pattern* where PJM's was made on a *census* (§6). A reader who holds the two to the same
standard should require the §6 sweep first. **I would not object to that**, and it costs one zero-LP
session.

## 8. IF THE MARKER IS GRANTED — the exact spend, fixed here before it runs

1. **Write the `complete` entry** in `frontend/data/backcast/calibration-complete.json` carrying:
   `declared`, `by` (the owner's verbatim ruling), `keeper` = `2026-09-08-miso-245-ladderfix`,
   `keeper_at_declaration` (same), the `determination` re-verified in §2 **without a solve**,
   `tier_authorized` = validation ONLY (2022), `locked_test` = **NOT AUTHORIZED** (MISO is absent from
   `final`, has never scored 2019 or H1-2026, and the locked tier stays frozen for every ISO),
   `frontier_basis` = §4 + §6 **verbatim, including the weakness**, and `keeper_rekey_policy` =
   re-key on promotion with per-promotion determination re-verification (owner decision D-5(b)).
2. **Solve 2022 on the frozen recipe**, ONE invocation:
   `replay_keeper.py results/calibration/miso245_ladderfix_K --years 2022 --holdout-authorized
   --out-dir results/calibration/miso_2022_touchpoint` — ~12 min LP, ~13 GB peak, 8 GB swap,
   `MARKET_SIM_HIGHS_THREADS=4`. **Nothing is tuned to 2022. Ever.**
3. **Carry the attestation forward** (replay_keeper does not write one) or C6 reads `UNATTESTED` and
   the determination is NOT-YET for that reason alone.
4. **Register it, then FOLD IT INTO THE KEEPER** (rule 30 `[R-TOUCHPOINT-FOLD]`):
   `scripts/stamp_touchpoint_holdout.py --run-id <touchpoint> --keeper-id
   2026-09-08-miso-245-ladderfix`, then `build_status.py --iso MISO` so the holdout ladder carries the
   per-year row. **A touchpoint is the keeper on another year — it is never a separate dashboard
   card.**
5. **A degraded rung does NOT decertify MISO** (rule 30 (c)): the ISO's determination is the
   train-tier verdict and nothing else. Report the rung, keep the headline.
6. **Then diagnose the object it surfaces and re-train on 2023–2025** — step 3 of rule 22's touchpoint
   loop is the only place fitting ever happens.

## 9. NON-CLAIMS

1. **This grants nothing.** MISO stays absent from `complete` until an explicit owner act, and the
   machine gate refuses 2022 until then.
2. **No out-of-training year was solved, scored or registered** to produce this document, and **no LP
   was spent.**
3. **Nothing here is evidence about MISO's out-of-sample skill.** A validation number would be
   model-selection evidence by rule 22's own words, and this document is not even that.
4. **MISO has no failing gate**, this assessment does not invent one, and C3c is untouched.
5. **`final` is not sought, implied or eligible.** MISO has never spent a locked-test year, the
   locked tier remains frozen for every ISO, and rule 22's scheduling precondition requires the
   2020–2022 touchpoints to have been run first — none has.
6. **2025 C1 is SKIPPED on eight classes** on the preliminary EIA-923 vintage and no 2025 C1 pass is
   read as evidence above.
