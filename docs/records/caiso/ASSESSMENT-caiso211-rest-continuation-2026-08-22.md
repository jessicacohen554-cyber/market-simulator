# ASSESSMENT — caiso-211: Branch A executed (**REST CONTINUES**). Full record re-verified on committed bytes — and for the first time since the rest protocol gained its cross-checks, **NO new defect found**: the HEAD delta since caiso-210 is two foreign commits confined to §5.4 (MISO) prose, and every standing number reproduces exactly. Keeper unchanged at `2026-08-17-caiso-200-h1-memberpanel` (NOT-YET); owner packet unchanged at **TWO** items (2026-08-22)

**No solve. No probe. No LP was spent, no bundle produced, no dashboard
registration due.** Everything below is measured from already-committed
artifacts and from git. **No mechanism was tested, so rule 28b does not attach
and no cell verdict moves** (the caiso-206 / caiso-207 / caiso-208 / caiso-209 /
caiso-210 precedent, applied identically).

---

## §0 — Which branch, and why

The charter is explicit: **Branch A is the default and executes unless an owner
order says otherwise; Branch B opens *if and only if* the owner funds
tail-formation object (a) or (b).** No funding order issued into this session.

So caiso-203 **ruling 2 (FINAL)** governs, and it funds neither object. The
blocker is not a planning obstacle to route around — it is the finding itself:
the in-model lever queue is **empty with every cell adjudicated**, re-proven by
measurement at caiso-205 (the last chartered lever came back byte-identical in
2023/2025; floor max $14.5 in 2024 — *an inert arm is not a lever*), and the
required move is a broad **~$2–3/h level-down across the sub-$60 buckets**
(caiso-202 §B) for which **no admissible in-model instrument exists** (§F).
Reaching C3a through a §F-killed lever would be a rule-13 act; **NOT-YET is the
honest fallback** (ruling 5).

**Branch A executed. Nothing solved, nothing armed, nothing registered.**

*(Numbering: the charter delivered is the caiso-211 charter and caiso-210
closed "Next number: caiso-211" — numbering is consistent this session, unlike
the caiso-210 offset it had to record.)*

---

## §1 — Standing state re-verified (committed bytes only)

I re-verified rather than carried forward — the standing protocol since
caiso-208/209, and the discipline that surfaced a new defect in each of the
last three sessions. `origin/main` at **317be02** against the **cf7b3fd**
caiso-210 measured from; the branch for this session was cut from that tip.

| # | check | instrument | result |
|---|---|---|---|
| 1 | keeper identity | `keepers/CAISO.json` | `2026-08-17-caiso-200-h1-memberpanel` — **unchanged** |
| 2 | determination | `calibration_verdict.py --run-id <keeper>` (never a solve) | **NOT-YET**, reproduced exactly; rubric **v3.4**; `reasons` = *"undocumented out-of-tolerance (FAIL) criteria: price_mean"* |
| 3 | keeper text truthfulness | `audit_keepers.py --iso CAISO` | **PASS, 0 failures / 0 warnings** |
| 4 | status sync | `build_status.py --iso CAISO --check` | *"status parts in sync (1 keepers: CAISO)"* |
| 5 | DOF ledger | keeper `calibration_attestation.json` | **10/7** (`n_entries: 10`, `n_residual: 7`) |
| 6 | holdout posture | `calibration-complete.json` | `complete` = {NEISO, NYISO, PJM}; `final` carries no ISO; CAISO in `withdrawn` (declared 2026-08-05, withdrawn 2026-08-06) — **in neither grant block** |
| 7 | spend freeze | `holdout-freeze.json` | **ACTIVE** (`active: true`, declared 2026-07-25) |
| 8 | registrations | registry sidecars + run payloads | keeper + the caiso-205 pair — all three **present and tracked**, years `[2023, 2024, 2025]` each, payloads on disk — **no out-of-training year touched** |
| 9 | matrix cell census | CAISO shard | **K 64 · U 33 · I 15 · R 9 · O 6 · G 5 = 132** — exactly as pre-registered by the charter (plus 92 `·` n/a cells, as always uncounted) |
| 10 | matrix integrity | `check_mechanism_matrix.py` | **exit 0**, *"integrity OK"*, keeper stamps match every `keepers/<ISO>.json`, **§5.x prose headers match every keeper shard**, *"0 unresolvable beyond the ratchet"* |
| 11 | **gate-POSTURE cross-check** (caiso-208's protocol) | shard `gates` stamp + §5.2 header read back against the verdict | **BOTH CURRENT** — no correction needed, so neither surface is touched this session |
| 12 | **gate-MAGNITUDE cross-check** (caiso-209's protocol) | `calibration_verdict.py --json` | **every recorded magnitude re-read independently and confirmed** — see the scorecard below; nothing carried forward unread |

**Scorecard, re-stated in full from this session's own `--json` read**
(`grade_summary`: scored 8, target_grade 6, commercial_grade 0, ledgered 1,
fails 1):

| criterion | tier | status | magnitude (2023 / 2024 / 2025) |
|---|---|---|---|
| C1 fuel-mix | load-bearing | **PASS** | **12/12 rows, free 8/8** (pinned: CC_CHP, ST_CHP) |
| C2 system volume | load-bearing | PASS | — |
| C3a mean LMP | load-bearing | **FAIL** — the SOLE load-bearing failure | model/actual $/MWh **56.40/54.17 (+4.1 %, PASS) / 39.07/34.65 (+12.8 %) / 39.82/34.42 (+15.7 %)**, judged vs ACTUAL RT LMP only |
| C3b price shape | load-bearing | PASS | **NRMSE 0.098 / 0.179 / 0.182** vs ≤0.20 — 2025 margin **0.018**, composition watch live |
| C3c price tail | supporting | **CAVEAT** (the single ledgered) | 0 h vs 47 h; 1 h vs 35 h; **2025 PASS** (0 h vs 8 h) |
| C4 dispatch corr | supporting | PASS | — |
| C6 governance | protective | PASS | — |
| C8 forced share | protective | PASS | — |

Caveat budget: **ledgered 1 of 1, protective 0 of 0** — at budget, not over it.
**C3c standing rule correctly silent**: guard (a) is *lone failure only*, C3a
also fails, so the determination stays **NOT-YET** and C3c reads CAVEAT (never
PASS) at full magnitude, as designed.

**Branch A discipline honoured:** no solve, no probe, no re-litigation of the
C3a basis (CLOSED — caiso-203 ruling 1), no re-run of the caiso-204
identification, the caiso-205 A/B, or the FFR-4F anchor A/B, and no re-derivation
of the caiso-210 bench-staleness exposure.

---

## §2 — The distinctive fact of this session: a **CLEAN re-verification** — and why that claim is meaningful, not complacent

caiso-208 found the stale `gates` stamp; caiso-209 found the superseded C3b
guardrail triplet; caiso-210 found the STALE BENCHMARK flag. Each defect had
survived precisely because numbers were being carried forward unread. This
session ran the same instruments the same way and found **nothing new**. Two
measurements make that a result rather than an assumption:

1. **The HEAD delta is measured, and it is empty of CAISO.** Since caiso-210's
   merge (`627f547`, PR #4174), `origin/main` has moved by exactly **two
   commits**: `57c36e4` (miso-174, *"add the missing §5.4 MISO lever-queue
   stamp"*) and its merge `317be02` (PR #4175). `git diff --stat` over the range
   touches **one file** — `docs/mechanism-testing-matrix.md`, +106/−1 — and the
   single hunk begins at line 4459, immediately above the `### 5.4 MISO` header
   at 4462, i.e. **entirely inside MISO's §5.4 section**. No scorer, no bench
   part, no shard, no keeper file, no `src/` path, no CAISO record moved.

2. **The STALE BENCHMARK banner still fires with the identical fingerprint.**
   All three CAISO parts still trip the HARD flag, and the builder fingerprint
   at HEAD is **`ded4ca25749a` — the same value caiso-210 recorded**. Since the
   fingerprint hashes `BUILDER_SOURCES`, its identity across the two HEADs is an
   independent confirmation that the builder is byte-unchanged since caiso-210
   measured the exposure — so the caiso-210 §2.2 conclusion (**stamp-absence,
   not drift**; payload reproducible at HEAD; C1's 12/12 PASS unaffected)
   **carries forward without re-derivation**, exactly as its own DO-NOT-REDO
   entry requires. Filed item 5 stands: discharge as a **by-product of the next
   funded solve**, never as an errand.

Both guardrail cross-checks — now standing protocol — came back clean on their
first read: the shard `gates` stamp (caiso-210's) and the §5.2 header both
describe the verdict the scorer actually prints, and every magnitude in them
matches the `--json` records re-read this session. **No records repair was
needed, so none was made**: the correct act on a current stamp is to leave it
untouched, not to churn it with a no-change re-stamp.

---

## §3 — The owner packet, unchanged at **TWO** items

Carried from caiso-208 §3 / caiso-209 §4 / caiso-210 §3 with no new evidence in
either direction. **§2 adds no third item** — a clean re-verification is not a
decision.

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
change is **the label on 1,000 MW**. FC-2 row 4 improves *solely* because
capacity moved into a channel the numerator does not count — **channel
substitution, not a gain**.

**Recommendation, for the owner's convenience only: keep default-OFF** absent a
reason unrelated to row 4.

---

## §4 — DO-NOT-REDO

Everything in caiso-206 §B, caiso-207 §5, caiso-208 §4, caiso-209 §5 and
caiso-210 §4 carries forward **verbatim**. In particular: the
caiso-202/203/204/205 lists; the FFR-4F A/B and the 138.36 anchor derivation;
the anchor's `O` cell means *adjudicated, merged, arming owner-pending* —
**never** *untested*; the swept `frontend/data/hindcast/` sidecars **stay
swept**; the C3a basis is CLOSED (actual RT LMP only); the v3.4 C1 re-score is
**not** open (C1 passes 12/12, free 8/8); the retained v3.3 promotion-time
blocks are **not** live; the census is **132**, not 131; **C3b's baseline is
0.098/0.179/0.182** — do not read it as a regression, and do not "fix" it; do
not re-derive the CAISO bench-staleness exposure (the flag is **stamp-absence**);
do not regenerate CAISO's bench parts on this lane; and do not read *"0 with
engine drift"* as evidence for a stale part.

**This session adds no new entry.** No new adjudication was made, so there is
nothing new to freeze.

**New evidence still means exactly one thing: a keeper whose own scored path
spikes.**

---

## §5 — Filed items

All carried, none discharged (each is fixable only at a session that produces a
solve or a promotion); re-verification status noted where this session touched
one:

1. **Stale DOF-ledger text** — `offer_curve_by_group` still reads
   `"identification": "residual"` on the keeper attestation, overstating the
   residual content for CAISO's CC_REGULAR / CT_PEAKER bands (measured from
   OASIS `PUB_DAM_GRP` since 2026-08-02, caiso-202 §H). **Re-verified still open
   by direct read of the attestation this session.**
2. **Diagnostics vintage drift** — keeper-vintage `legitimacy_diagnostics.json`
   differs from fresh bundles on one D-4 row (chp_steam plant 10034). Carried.
3. **Site retention** — the caiso-205 pair postdates the keeper and comes off at
   the next promotion in the ordinary way. Not an anomaly.
4. **Promotion-session duty** — a session that produces a promotion re-measures
   and re-states the whole scorecard from the verdict output, never carrying
   rows forward from a superseded run. (This session's §1 row 12 is the rest-
   session form of the same discipline.)
5. **CAISO's bench parts are unstamped** — still tripping the HARD flag on every
   scorer run (same fingerprint `ded4ca25749a`, §2). Not a correctness defect
   (caiso-210 §2.2). **Discharge as a by-product of the next funded CAISO
   solve**; verify afterwards with `check_bench_freshness.py --iso CAISO` and
   re-run the keeper verdict, since a regeneration CAN move C1's actuals.
6. **Session mechanics** — regenerate `data/clean` before any solve; **ONE**
   CAISO 3-year invocation at a time (~13.3 GiB cgroup cap); this container
   class ships **no scientific stack** (`numpy` absent — confirmed again here;
   the stdlib-only scorer is why Branch A runs at all), so any solve or
   benchmark rebuild installs one first.

**Routed OFF this lane (rule 25), unchanged:**

7. **The two bench-freshness checker defects D1/D2** (caiso-210 §2.3) —
   nyiso-148's mechanism. D1: the five benchmark-frame builders in
   `scripts/run_calibration_full.py` are covered by **neither**
   `BUILDER_SOURCES` nor `ENGINE_PATHS`; D2: `check_bench_freshness.py`
   `continue`s after the HARD branch, so *"0 with engine drift"* is vacuous for
   every stale part.
8. **The five-ISO bench regeneration + CI-gate sequence** — program-level
   (nyiso-148: each ISO regenerates, then the gate goes on); CAISO's leg is
   filed item 5 and is funding-blocked.
9. **Program-wide stale registration citations** — `cccc911` (2026-08-19) swept
   all 187 canonical `frontend/data/hindcast/` sidecars; every ISO's citations
   of registered forecast-run ids, including the **shared** `mechanism-matrix.js`
   base-row text for `caiso_ra_mpb_capacity_anchor`, point at runs no longer on
   the forecast dashboard. Fixing only CAISO's would make the shared file
   inconsistent. Route to a cross-lane or governance session.

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
  due.** The caiso-134/140/150/202/206/207/208/209/210 disposition applies
  unchanged.
* **Rule 16 `[R-ALLYEARS]`.** All three CAISO registrations carry
  `[2023, 2024, 2025]`; no single-year bundle exists on the lane.
* **Rule 22 `[R-HOLDOUT]`.** No year solved, scored or registered. CAISO absent
  from both `complete` and `final` (it sits in `withdrawn`); freeze **ACTIVE**.
* **Rule 25 `[R-ISO-SCOPE]`.** CAISO only. The shared `mechanism-matrix.js` was
  not touched; the routed items are *reported*, not repaired; the §5.4 MISO
  delta was *measured* for CAISO-relevance, never edited.
* **Rule 27 `[R-PUSH]`.** Fable. **No source file under `src/market_sim/` was
  modified** — the deliverable is records only. Every edited file was edited in
  place, never regenerated from response content.
* **Rule 28 `[R-MECH-MATRIX]`.** **No mechanism was tested, so duty (b) does not
  attach and no cell verdict moves.** The §5.2 prose block records the session;
  the shard `gates` stamp was read back current and deliberately left untouched.
  The census is **unchanged at 132**.

---

## §7 — Record changes

- **This file**; `docs/calibration-log/caiso.md` caiso-211 entry; matrix §5.2
  caiso-211 block.
- **Keeper, markers, holdout freeze, DOF ledger, every matrix cell verdict, the
  shard `gates` stamp, the §5.2 header, every bench part, and every source file:
  UNCHANGED.** No run registered (none produced). No cell edited by this lane.
  Nothing regenerated.

Next number: **caiso-212**.
