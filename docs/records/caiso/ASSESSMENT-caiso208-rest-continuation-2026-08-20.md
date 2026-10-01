# ASSESSMENT — caiso-208: Branch A executed (**REST CONTINUES**). The full record re-verified on committed bytes at a HEAD that had moved — and **one new defect found and repaired**: the lane's own gate posture was **stale on both matrix surfaces**, reading `TWO load-bearing FAILs` three days after the rubric v3.4 re-score made it **ONE**. Keeper unchanged at `2026-08-17-caiso-200-h1-memberpanel` (NOT-YET); owner packet unchanged at **TWO** items (2026-08-20)

**No solve. No probe. No LP was spent, no bundle produced, no dashboard
registration due.** Everything below is measured from already-committed
artifacts. **No mechanism was tested, so rule 28b does not attach and no cell
verdict moves** (the caiso-206 / caiso-207 precedent, applied identically).

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
caiso-207 baseline** — `origin/main` at PR **#4160**, against the **#4154** the
charter recorded. That decision is what surfaced §2.

| # | check | instrument | result |
|---|---|---|---|
| 1 | keeper identity | `keepers/CAISO.json` | `2026-08-17-caiso-200-h1-memberpanel` — **unchanged** |
| 2 | determination | `calibration_verdict.py --run-id <keeper>` (never a solve) | **NOT-YET**, reproduced exactly |
| 3 | keeper text truthfulness | `audit_keepers.py --iso CAISO` | **PASS, 0 failures / 0 warnings** |
| 4 | status sync | `build_status.py --iso CAISO --check` | *"status parts in sync (1 keepers: CAISO)"* |
| 5 | DOF ledger | keeper `calibration_attestation.json` | **10/7** (`n_entries: 10`, `n_residual: 7`) |
| 6 | holdout posture | `calibration-complete.json` | `complete` = {NEISO, NYISO, PJM}; `final` **empty of every ISO** — **CAISO in neither** |
| 7 | spend freeze | `holdout-freeze.json` | **ACTIVE** (`active: true`, declared 2026-07-25, re-armed 2026-08-06) |
| 8 | registrations | registry sidecars + run payloads | keeper + caiso-205 pair (`caiso205-ctl-headbase`, `caiso205-arm-adaptive`) all **present and tracked**, years `[2023, 2024, 2025]` each — **no out-of-training year touched** |
| 9 | matrix cell census | CAISO shard | **K 64 · U 32 · I 15 · R 9 · O 6 · G 5 = 131 cells** — **no verdict moves** |
| 10 | matrix integrity | `check_mechanism_matrix.py` | **exit 0**, *"integrity OK"*, *"keeper stamps match every keepers/&lt;ISO&gt;.json"* |

**Scorecard, re-verified in full:** C1 fuel-mix PASS (**12/12, free 8/8**) · C2
system volume PASS · **C3a mean LMP FAIL — the SOLE load-bearing failure** (2023
PASS **+4.1 %**; 2024 **+12.8 %**; 2025 **+15.7 %**, judged vs actual RT LMP only)
· C3b PASS · **C3c the SINGLE ledgered caveat** (2023 model 0 h vs actual 47 h;
2024 1 h vs 35 h; 2025 PASS) · C4 PASS · C6 governance PASS · C8 forced-energy
PASS. Determination basis: *undocumented out-of-tolerance (FAIL) criteria:
price_mean*.

**C3c standing rule correctly silent.** Guard (a) is *lone failure only* — C3a
also fails, so the rule does not fire and the determination stays **NOT-YET**.
C3c reads CAVEAT (never PASS), at full magnitude, as designed.

**Branch A discipline honoured:** no solve, no probe, no re-litigation of the
C3a basis (CLOSED — caiso-203 ruling 1), no re-run of the caiso-204
identification, the caiso-205 A/B, or the FFR-4F anchor A/B.

---

## §2 — THE NEW FACT: the lane's own gate posture was stale on **both** matrix surfaces

**No prior CAISO record carries this**, and it is the one thing this session
changes.

### What was wrong

The keeper was **re-scored under rubric v3.4 on 2026-08-18** (owner amendment:
the C1 volume band is floored at **3 % of actual total generation** = **±5.27
TWh**, superseding the old 2 %-of-load term that gave ±4.15). The unchanged
**−4.243 TWh** 2023 CC_REGULAR row sits **inside** the floored band, so **C1
flipped FAIL → PASS** and the load-bearing count went **TWO → ONE**.

That re-score updated the keeper shard (`keepers/CAISO.json`, commit
**568699d**). It did **not** update either matrix surface:

| surface | read before this session | correct reading |
|---|---|---|
| `docs/codebase-site/data/mechanism-matrix/CAISO.js` → `gates` | *"TWO load-bearing FAILs … C1 … 11/12, free 7/8"* | **ONE** — C3a alone; C1 **12/12, free 8/8** |
| `docs/mechanism-testing-matrix.md` §5.2 header | same v3.3 text | same correction |

### Why it survived three sessions

The caiso-204 and caiso-205 shard touches (2026-08-19) moved **cells** and never
re-stamped `gates`. caiso-206 and caiso-207 both re-verified the **verdict**
— and both correctly reported C1 **12/12, free 8/8** — but neither read the
**matrix text** back against it. The drift lived in the gap between two records
that were each individually checked.

### Why it matters

Consulting the matrix for an ISO's open-gate set is **exactly** what rule 28a
DO-NOT-REDO and the lever-queue discipline require *before proposing a lever*. A
reader doing that correctly would have read **C1 fuel-mix as an open failing
gate inviting a lever** — when it is closed, and C3a is the sole load-bearing
failure. That is a live misdirection of the one workflow the matrix exists to
serve.

### What I did

**Repaired in both places**, in this lane's standing *nothing-is-retracted*
form: the promotion-time (2026-08-17, rubric v3.3) record is **retained
verbatim**, with the live posture prepended to the shard stamp and annotated
inline in the §5.2 header.

**The C1-2023 residual is UNCHANGED AS A PHYSICAL OBJECT.** The band shift
changes what the rubric **charges** for it, not the physics. The standing
CC-side under-dispatch / over-import lane (caiso-121 surplus-belly, caiso-135
ride-through, caiso-140 §B) stays open exactly as before, and the caiso-200
measurement that only **+0.003 TWh** of the deficit was instrument artifact is
untouched.

### Authority for the repair

* **Rule 28b does not attach** — nothing was tested, no cell verdict moves.
* **Precedent is exact:** **neiso-100** (2026-08-18) — a no-solve
  DECLARATION RE-ASSESSMENT session that refreshed its own ISO's `gates` stamp
  with *"NO CELL VERDICT MOVES"* stated on its face. Same shape, same day as
  the v3.4 amendment.
* **Rule 25 `[R-ISO-SCOPE]` clean** — CAISO's own shard and CAISO's own §5.2
  section only. The shared `mechanism-matrix.js` base rows were **not** touched.

---

## §3 — The owner packet, unchanged at **TWO** items

Carried from caiso-207 §4 with no new evidence in either direction.

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

## §4 — DO-NOT-REDO

Everything in caiso-206 §B and caiso-207 §5 carries forward **verbatim**. In
particular: the caiso-202/203/204/205 lists; the FFR-4F A/B and the 138.36
anchor derivation; the anchor's `O` cell means *adjudicated, merged, arming
owner-pending* — **never** *untested*; the swept `frontend/data/hindcast/`
sidecars **stay swept**; the C3a basis is CLOSED (actual RT LMP only).

**Added by this session:**

1. **Do not re-verify the v3.4 C1 re-score as though it were open.** C1 **passes
   at 12/12, free 8/8**; the −4.243 TWh row is unchanged and in-band. Both matrix
   surfaces now say so.
2. **Do not read the retained v3.3 promotion-time blocks as live.** They are
   labelled promotion-time records and are retained deliberately, not stale
   leftovers.

**New evidence still means exactly one thing: a keeper whose own scored path
spikes.**

---

## §5 — Filed items

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

Each is fixable only at a session that produces a **promotion**; none is fixable
without one.

**Routed OFF this lane (rule 25):**

5. **Program-wide stale registration citations.** `cccc911` (2026-08-19) swept
   all **187** canonical `frontend/data/hindcast/` sidecars, so every ISO's
   citations of registered forecast-run ids now point at runs no longer on the
   forecast dashboard — including the **shared** `mechanism-matrix.js` base-row
   text for `caiso_ra_mpb_capacity_anchor`. Fixing only CAISO's would make the
   shared file inconsistent; fixing all is off-lane. **Still routed** to a
   cross-lane or governance session. *(Unrelated and also off-lane, observed by
   the guard this session: pre-existing `scenarios.py` anchor line-number drift
   across the shared base rows, and an NYISO §5.x prose-header keeper-name
   warning.)*

---

## §6 — Governance

* **Rule 1 `[R-STRUCT]`.** Nothing tuned to a residual; no mechanism added,
  armed or removed. §3(2) explicitly declines to recommend arming for the row-4
  improvement, because that improvement is channel substitution.
* **Rule 12 `[R-PARALLEL]` / mechanics.** No solve run, so neither the year loop
  nor the memory cap was engaged.
* **Rule 13 `[R-MEASURED]`.** No measured outcome fed back; §0 records why
  reaching C3a through a §F-killed lever would be a rule-13 act.
* **Rule 15 `[R-DASHBOARD]`.** **No run was produced, so no registration is
  due.** The caiso-134/140/150/202/206/207 disposition applies unchanged.
* **Rule 22 `[R-HOLDOUT]`.** No year solved, scored or registered. CAISO absent
  from both `complete` and `final`; freeze **ACTIVE**; all three registrations
  carry years `[2023, 2024, 2025]` only.
* **Rule 25 `[R-ISO-SCOPE]`.** CAISO only. The shared `mechanism-matrix.js` was
  not touched; the program-wide sweep consequence is *reported*, not repaired.
* **Rule 27 `[R-PUSH]`.** Opus. **No source file under `src/market_sim/` was
  modified** — the deliverable is records only. Both edited files are well under
  the 300-line rewrite threshold in change size and were edited in place, never
  regenerated.
* **Rule 28 `[R-MECH-MATRIX]`.** **No mechanism was tested, so duty (b) does not
  attach and no cell verdict moves.** The `gates` stamp repair is a
  records-truthfulness correction on the neiso-100 precedent, not a verdict
  change; the §5.2 prose block records the session.

---

## §7 — Record changes

- **This file**; `docs/calibration-log/caiso.md` caiso-208 entry; matrix §5.2
  caiso-208 block.
- **REPAIRED (the one substantive change):** the stale v3.3 gate posture in
  `docs/codebase-site/data/mechanism-matrix/CAISO.js` (`gates` stamp) and in the
  `docs/mechanism-testing-matrix.md` §5.2 header — promotion-time text retained
  verbatim, live posture prepended/annotated.
- **Keeper, markers, holdout freeze, DOF ledger, every matrix cell verdict, and
  every source file: UNCHANGED.** No run registered (none produced). No cell
  edited.

Next number: caiso-209.
