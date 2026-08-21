# ASSESSMENT — caiso-209: Branch A executed (**REST CONTINUES**). Full record re-verified on committed bytes at a HEAD that had moved again — and **one new defect found**: the lane's standing **C3b guardrail figures are the SUPERSEDED caiso-197 keeper's**, not the caiso-200 keeper's own. Keeper unchanged at `2026-08-17-caiso-200-h1-memberpanel` (NOT-YET); owner packet unchanged at **TWO** items (2026-08-21)

**No solve. No probe. No LP was spent, no bundle produced, no dashboard
registration due.** Everything below is measured from already-committed
artifacts. **No mechanism was tested, so rule 28b does not attach and no cell
verdict moves** (the caiso-206 / caiso-207 / caiso-208 precedent, applied
identically).

---

## §0 — Which branch, and why

The charter is explicit: **Branch A is the default and executes unless an owner
order says otherwise; Branch B opens *if and only if* the owner funds
tail-formation object (a) or (b).** No funding order issued into this session.

So caiso-203 **ruling 2 (FINAL)** governs, and it funds neither object. The
blocker is not a planning obstacle to route around — it is the finding itself:

* the in-model lever queue is **empty with every cell adjudicated** (caiso-185,
  re-confirmed 188/191/202), and
* that emptiness was **re-proven by measurement** at caiso-205 — the last
  chartered lever was built, A/B'd against a zero-delta control, passed every
  pre-registered gate, and came back **byte-identical in 2023/2025** (floor max
  $14.5 in 2024). *An inert arm is not a lever.*
* The required move is a broad **~$2–3/h level-down across the sub-$60 buckets**
  (caiso-202 §B), and **no admissible in-model instrument of that size exists**
  (§F). Reaching the number through a §F-killed lever would be a rule-13 act;
  **NOT-YET is the honest fallback** (ruling 5).

**Branch A executed. Nothing solved, nothing armed, nothing registered.**

---

## §1 — Standing state re-verified (committed bytes only)

I re-verified rather than carried forward, because **HEAD had moved past the
caiso-208 baseline** — `origin/main` at **6fa0de2** (PR #4168), against the
**79d3da3** the charter recorded. That decision is what surfaced §2 and §3.

| # | check | instrument | result |
|---|---|---|---|
| 1 | keeper identity | `keepers/CAISO.json` | `2026-08-17-caiso-200-h1-memberpanel` — **unchanged** |
| 2 | determination | `calibration_verdict.py --run-id <keeper>` (never a solve) | **NOT-YET**, reproduced exactly; rubric **v3.4** |
| 3 | keeper text truthfulness | `audit_keepers.py --iso CAISO` | **PASS, 0 failures / 0 warnings** |
| 4 | status sync | `build_status.py --iso CAISO --check` | *"status parts in sync (1 keepers: CAISO)"* |
| 5 | DOF ledger | keeper `calibration_attestation.json` | **10/7** (`n_entries: 10`, `n_residual: 7`) |
| 6 | holdout posture | `calibration-complete.json` | `complete` = {NEISO, NYISO, PJM}; `final` **empty of every ISO**; CAISO in `withdrawn` — **in neither grant block** |
| 7 | spend freeze | `holdout-freeze.json` | **ACTIVE** (`active: true`, declared 2026-07-25, re-armed 2026-08-06) |
| 8 | registrations | registry sidecars + run payloads | keeper + caiso-205 pair (`caiso205-ctl-headbase`, `caiso205-arm-adaptive`) all **present and tracked**, years `[2023, 2024, 2025]` each — **no out-of-training year touched** |
| 9 | matrix cell census | CAISO shard | **K 64 · U 33 · I 15 · R 9 · O 6 · G 5 = 132** — see §2 |
| 10 | matrix integrity | `check_mechanism_matrix.py` | **exit 0**, *"integrity OK"*, *"keeper stamps match every keepers/&lt;ISO&gt;.json"* |
| 11 | **gate-posture cross-check** (caiso-208's addition to the rest protocol) | shard `gates` stamp + §5.2 header **read back against the verdict output** | **BOTH CURRENT** — the caiso-208 repair held; no drift |

**Scorecard, re-verified in full** (`grade_summary`: scored 8, target_grade 6,
commercial_grade 0, ledgered 1, fails 1):

| criterion | tier | status | magnitude (2023 / 2024 / 2025) |
|---|---|---|---|
| C1 fuel-mix | load-bearing | **PASS** | **12/12 rows, free 8/8** |
| C2 system volume | load-bearing | PASS | — |
| C3a mean LMP | load-bearing | **FAIL** — the SOLE load-bearing failure | **+4.1 % (PASS) / +12.8 % / +15.7 %**, judged vs ACTUAL RT LMP only |
| C3b price shape | load-bearing | PASS | **NRMSE 0.098 / 0.179 / 0.182** vs ≤0.20 — **see §3** |
| C3c price tail | supporting | **CAVEAT** (the single ledgered) | 0 h vs 47 h; 1 h vs 35 h; **2025 PASS** (0 h vs 8 h, small-count) |
| C4 dispatch corr | supporting | PASS | — |
| C6 governance | protective | PASS | — |
| C8 forced share | protective | PASS | — |

Determination basis: *undocumented out-of-tolerance (FAIL) criteria:
price_mean*. Caveat budget: **ledgered 1 of 1, protective 0 of 0** — at budget,
not over it.

**C3c standing rule correctly silent.** Guard (a) is *lone failure only* — C3a
also fails, so the rule does not fire and the determination stays **NOT-YET**.
C3c reads CAVEAT (never PASS), at full magnitude, as designed.

**Branch A discipline honoured:** no solve, no probe, no re-litigation of the
C3a basis (CLOSED — caiso-203 ruling 1), no re-run of the caiso-204
identification, the caiso-205 A/B, or the FFR-4F anchor A/B.

---

## §2 — The census moved 131 → 132, and the mover is FOREIGN and LEGITIMATE

The charter pre-registered the expected census as **131 cells** (K 64 / U 32 /
I 15 / R 9 / O 6 / G 5). I measure **132** — `U` is **33**, everything else
exact.

**The whole delta is one cell added by another ISO's lane under rule 28c.**
Diffing the CAISO shard across the charter's own baseline
(`79d3da3..HEAD`) returns **exactly one added line**:

```
mustrun_layup_window_mask: { cell: "U", ev: "row added with the field
  2026-08-20 (miso-173, rule 28c); never armed here. Entering as U per rule
  28(d). The DEFECT is code-generic … but the VERDICT is per-ISO (rule 25) and
  the mask is inert wherever no per-plant must-run floor is armed …" }
```

This is rule 28(c) working exactly as written — *"a PR that adds a new
solve-affecting mechanism adds its matrix row in the same PR (base row + a cell
line in every ISO shard — the one deliberately non-parallel edit)"* — and rule
28(d) entering it as `U`, since a MISO identification transfers nothing to
CAISO. **No CAISO verdict moved.** The census is re-baselined at **132** for the
next session.

---

## §3 — THE NEW FACT: the lane's standing **C3b guardrail figures belong to the superseded caiso-197 keeper**

**No prior CAISO record carries this**, and it is the one substantive thing this
session adds.

### What is wrong

Every carried-forward statement of the lane's C3b guardrail — the caiso-209
charter's *"MUST NOT REGRESS … C3b (0.097/0.174/0.181 vs 0.20)"*, and the
scorecard row at `ASSESSMENT-caiso200-frontier-2026-08-17.md` line 52 — reads
**0.097 / 0.174 / 0.181**.

The keeper does not measure that. Re-scored at HEAD on its own committed bytes,
`2026-08-17-caiso-200-h1-memberpanel` measures:

| year | recorded | **measured at HEAD** | tol |
|---|---|---|---|
| 2023 | 0.097 | **0.098** | ≤0.20 |
| 2024 | 0.174 | **0.179** | ≤0.20 |
| 2025 | 0.181 | **0.182** | ≤0.20 |

**0.097 / 0.174 / 0.181 is the `2026-08-16-caiso-197-w2-r5` keeper's triplet** —
the run caiso-200 superseded. It is recorded as caiso-197's own number, correctly,
at `docs/calibration-log/caiso.md` line 8084 (*"C3b closed at 0.097/0.174/0.181
vs 0.20"*, inside the caiso-197 promotion entry) and in the §5.2 header's
caiso-197 superseded block. The caiso-200 assessment carried that row forward
instead of measuring caiso-200's own.

### Why transcription, not a moved measurement

The scoring inputs and the metric have all been stable, and the physics says the
number had to move:

1. **Inputs unchanged.** `bench/CAISO/{2023,2024,2025}.json.gz` and the keeper's
   run payload landed together at the promotion and have not been touched since.
   The only later commit in scope, **568699d** (the rubric v3.4 C1 re-score),
   touched `keepers/CAISO.json`, the registry sidecar, `status/CAISO.js` and
   `metrics.json` — and **not** the payload.
2. **Metric unchanged.** C3b's *load-weighted* basis dates to rubric **v2.4**,
   long before caiso-200 was scored at v3.3. Since the visible history root the
   only two scorer commits — **b7a2874** (v3.4) and **0ef672a** (nyiso-143) —
   contain **zero** `price_shape`/NRMSE hunks.
3. **The price vector demonstrably moved.** caiso-200 is caiso-197 *plus* the
   fleet-member panel, and its C3a moved in **all three years**
   (+4.0/+12.1/+15.6 → +4.1/+12.8/+15.7 %). A monthly load-weighted NRMSE that
   is bit-identical to three decimals in all three years across a recipe change
   that moved the mean in all three years is not a credible measurement.
4. **C3b does move at this precision between CAISO recipes.** The caiso-19x PS
   plant-params rung measured **0.098/0.178/0.183** (log line 8069) — a distinct
   triplet from both.

*Stated honestly:* the visible git history is **root-truncated at d985fca**
(partial clone), so I cannot diff the scorer across the promotion boundary
itself. That is the one check I could not run. Every check I could run points the
same way, and in any case the **reproducible number at HEAD is
0.098 / 0.179 / 0.182** — that is what a future session will measure.

### Why it matters — it is a live trap, of exactly the caiso-208 species

**It changes no determination.** C3b **PASSES all three years under both
readings** (worst 0.182 vs 0.20). C3b is not, and has never been, part of this
lane's failing-gate set.

The damage is to the **guardrail**. The charter instructs the next session:
*"MUST NOT REGRESS on any backcast solve: C3b (0.097/0.174/0.181 vs 0.20)."* A
Branch B session that solves, measures 0.098/0.179/0.182, and checks it against
that line would read a **regression in all three years** — when it is in fact the
**unchanged keeper baseline**, arrived at by no mechanism at all. It would be
diagnosing a delta that does not exist, against a run that no longer exists.

This is structurally identical to the caiso-208 gate-posture finding: a number
that three consecutive rest sessions (206, 207, 208) carried forward without ever
reading it back against the verdict, surviving in the gap between records that
were each individually checked. caiso-208 added the **gate-posture** cross-check
to the rest protocol; this session's cross-check found the **magnitude** half
uncovered.

Also worth carrying: 2025's true margin is **0.018** (0.182 vs 0.20), tighter
than the 0.019 the recorded figure implies. The **composition watch** the
caiso-19x PS rung opened at 0.017 is live at 0.018, not resting at 0.019.

### What I did

**Recorded, not retracted** — this lane's standing form:

* **Annotated** the caiso-200 assessment's C3b row inline with the measured
  triplet and its provenance. The promotion-time text is retained verbatim.
* **Stamped the measured C3b baseline onto both live guardrail surfaces** (the
  CAISO shard `gates` stamp and the §5.2 header), which previously carried C3b
  only as *"PASS"* with no magnitude — which is precisely why the wrong triplet
  had nowhere to be checked against.
* **Extended the rest protocol**: the gate-posture cross-check now reads the
  recorded **magnitudes** back against the verdict, not just the pass/fail
  posture.

### Authority for the repair

* **Rule 28b does not attach** — nothing was tested, no cell verdict moves.
* **Precedent is exact:** **caiso-208** (2026-08-20), itself on **neiso-100**
  (2026-08-18) — a no-solve session refreshing its own ISO's `gates` stamp with
  *"NO CELL VERDICT MOVES"* stated on its face.
* **Rule 25 `[R-ISO-SCOPE]` clean** — CAISO's own shard, CAISO's own §5.2
  section, CAISO's own assessment. The shared `mechanism-matrix.js` base rows
  were **not** touched.

---

## §4 — The owner packet, unchanged at **TWO** items

Carried from caiso-208 §3 with no new evidence in either direction. **§3 does not
add a third item** — it is a records correction, not a decision.

### (1) Fund a tail-formation object

| object | status | measured reach |
|---|---|---|
| **(a) PS water-state hourly intake** | declined **3×** | **62.1 % / 10.4 %** of the required 2024 / 2025 C3a move **at its most favourable bound** |
| **(b) import spot-capacity derivation** | not funded | direct λ share **< 5 %** of the positive gap |

**Neither closes C3a on its own arithmetic.** If no funding order issues, **rest
is correct**. Should one issue, Branch B's pre-registration must state up front
what a **partial** close is worth and what verdict a partial earns — object (a)
cannot reach the number even at its most favourable bound.

### (2) F-3 — arming posture of `caiso_ra_mpb_capacity_anchor`

Built, measured, merged, **default-OFF**, keeper-inert by construction. Arming
is an owner decision. FFR-4F's pre-registered **trap test fired**: total thermal
built is **identical to the megawatt** in both arms (10,186.3 MW), and the only
change is **the label on 1,000 MW** (backstop −1,000, economic +1,000, two years
later). FC-2 row 4 improves *solely* because capacity moved into a channel the
numerator does not count — **channel substitution, not a gain** (FFR-4F D-2).

**Recommendation, for the owner's convenience only: keep default-OFF** absent a
reason unrelated to row 4. Arming to capture row 4 would be the rule 1
`[R-STRUCT]` trap the owner declined this anchor as a route to (D-15).

---

## §5 — DO-NOT-REDO

Everything in caiso-206 §B, caiso-207 §5 and caiso-208 §4 carries forward
**verbatim**. In particular: the caiso-202/203/204/205 lists; the FFR-4F A/B and
the 138.36 anchor derivation; the anchor's `O` cell means *adjudicated, merged,
arming owner-pending* — **never** *untested*; the swept
`frontend/data/hindcast/` sidecars **stay swept**; the C3a basis is CLOSED
(actual RT LMP only); the v3.4 C1 re-score is **not** open (C1 passes 12/12, free
8/8); the retained v3.3 promotion-time blocks are **not** live.

**Added by this session:**

1. **Do not "fix" C3b, and do not read 0.098/0.179/0.182 as a regression.** It is
   the keeper's own unchanged baseline, arrived at by no mechanism. C3b PASSES
   all three years and is not in the failing-gate set. The superseded
   0.097/0.174/0.181 belongs to `2026-08-16-caiso-197-w2-r5`.
2. **Do not re-derive the census as 131.** It is **132** since miso-173's rule
   28c row addition (2026-08-20). No CAISO verdict moved.

**New evidence still means exactly one thing: a keeper whose own scored path
spikes.**

---

## §6 — Filed items

1. **Stale DOF-ledger text** — `offer_curve_by_group` still reads
   `"identification": "residual"` on the keeper attestation, overstating the
   residual content for CAISO's CC_REGULAR / CT_PEAKER bands (measured from
   OASIS `PUB_DAM_GRP` since 2026-08-02, caiso-202 §H). **Re-verified still open
   by direct read of the ledger's 10 entries this session.**
2. **Diagnostics vintage drift** — keeper-vintage `legitimacy_diagnostics.json`
   differs from fresh bundles on one D-4 row (chp_steam plant 10034). Carried.
3. **Site retention** — the caiso-205 pair postdates the keeper and comes off at
   the next promotion in the ordinary way. Not an anomaly.
4. **Session mechanics** — regenerate `data/clean` before any solve; **ONE**
   CAISO 3-year invocation at a time (~13.3 GiB cgroup cap).
5. **NEW — C3b magnitude on the keeper's own assessment.** §3's inline
   annotation is the honest minimum. The caiso-200 assessment's scorecard row
   remains a promotion-time record; a session that produces a **promotion**
   should re-measure and re-state the whole scorecard from the verdict output
   rather than carrying rows forward from the superseded run.

Each is fixable only at a session that produces a **promotion**; none is fixable
without one.

**Routed OFF this lane (rule 25):**

6. **Program-wide stale registration citations.** `cccc911` (2026-08-19) swept
   all **187** canonical `frontend/data/hindcast/` sidecars, so every ISO's
   citations of registered forecast-run ids now point at runs no longer on the
   forecast dashboard — including the **shared** `mechanism-matrix.js` base-row
   text for `caiso_ra_mpb_capacity_anchor`. Fixing only CAISO's would make the
   shared file inconsistent; fixing all is off-lane. **Still routed** to a
   cross-lane or governance session. *(Also off-lane, observed by the guard this
   session: an NYISO §5.x prose-header keeper-name warning. The `scenarios.py`
   anchor line-number drift caiso-208 observed now reports **0 unresolvable
   beyond the ratchet** — 1 unresolvable path remains, inside the ratchet.)*

---

## §7 — Governance

* **Rule 1 `[R-STRUCT]`.** Nothing tuned to a residual; no mechanism added,
  armed or removed. §4(2) explicitly declines to recommend arming for the row-4
  improvement, because that improvement is channel substitution.
* **Rule 12 `[R-PARALLEL]` / mechanics.** No solve run, so neither the year loop
  nor the memory cap was engaged.
* **Rule 13 `[R-MEASURED]`.** No measured outcome fed back; §0 records why
  reaching C3a through a §F-killed lever would be a rule-13 act.
* **Rule 15 `[R-DASHBOARD]`.** **No run was produced, so no registration is
  due.** The caiso-134/140/150/202/206/207/208 disposition applies unchanged.
* **Rule 22 `[R-HOLDOUT]`.** No year solved, scored or registered. CAISO absent
  from both `complete` and `final` (it sits in `withdrawn`); freeze **ACTIVE**;
  all three registrations carry years `[2023, 2024, 2025]` only.
* **Rule 25 `[R-ISO-SCOPE]`.** CAISO only. The shared `mechanism-matrix.js` was
  not touched; the program-wide sweep consequence is *reported*, not repaired.
* **Rule 27 `[R-PUSH]`.** Opus. **No source file under `src/market_sim/` was
  modified** — the deliverable is records only. Every edited file was edited in
  place, never regenerated from response content.
* **Rule 28 `[R-MECH-MATRIX]`.** **No mechanism was tested, so duty (b) does not
  attach and no cell verdict moves.** The `gates` stamp edit is a
  records-truthfulness correction on the caiso-208 / neiso-100 precedent, not a
  verdict change; the §5.2 prose block records the session. The census change is
  another lane's duty-(c) edit, verified foreign and legitimate (§2).

---

## §8 — Record changes

- **This file**; `docs/calibration-log/caiso.md` caiso-209 entry; matrix §5.2
  caiso-209 block.
- **CORRECTED (the one substantive change):** the C3b guardrail triplet. The
  measured baseline **0.098 / 0.179 / 0.182** is stamped onto the CAISO shard
  `gates` stamp and the §5.2 header; the caiso-200 assessment's row is annotated
  inline with the measured value and its provenance, promotion-time text
  retained verbatim.
- **Keeper, markers, holdout freeze, DOF ledger, every matrix cell verdict, and
  every source file: UNCHANGED.** No run registered (none produced). No cell
  edited by this lane.

Next number: caiso-210.
