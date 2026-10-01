# ASSESSMENT — caiso-213: Branch A executed (**REST CONTINUES**). Full record re-verified on committed bytes at a HEAD that moved again (35 commits since caiso-212's tip); the **conditional carry test on the bench-staleness adjudication was run and BOTH LEGS HOLD** — fingerprint still `dbea7bf45111`, `BUILDER_SOURCES` unmoved, and `run_calibration_full.py` **byte-identical** across `c55da9c..HEAD`, so the frame-builder set could not have moved and the caiso-212 adjudication **carries on its own stated terms**. Keeper unchanged at `2026-08-17-caiso-200-h1-memberpanel` (NOT-YET). **ONE new cross-lane defect found and routed off-lane**: 239 unresolvable mechanism-matrix anchors, foreign in origin (ercot-226) and in the SHARED base file. Owner packet unchanged at **TWO** items

**No solve. No probe. No LP was spent, no bundle produced, no dashboard
registration due.** Everything below is measured from already-committed
artifacts and from git. **No mechanism was tested, so rule 28b does not attach
and no cell verdict moves** (the caiso-206 … caiso-212 precedent, applied
identically).

---

## §0 — Which branch, and why

The charter is explicit: **Branch A is the default and executes unless an owner
order says otherwise; Branch B opens *if and only if* the owner funds
tail-formation object (a) or (b).** No funding order issued into this session.

So caiso-203 **ruling 2 (FINAL)** governs, and it funds neither object. The
blocker is unchanged: the in-model lever queue is **empty with every cell
adjudicated**, re-proven by measurement at caiso-205; the required move is a
broad **~$2–3/h level-down across the sub-$60 buckets** (caiso-202 §B) for
which **no admissible in-model instrument exists** (§F). Reaching C3a through a
§F-killed lever would be a rule-13 act; **NOT-YET is the honest fallback**
(ruling 5).

**Branch A executed. Nothing solved, nothing armed, nothing registered.**

*(Numbering consistent: the charter delivered is the caiso-213 charter, closing
caiso-212's "Next number: caiso-213".)*

---

## §1 — Standing state re-verified (committed bytes only)

`origin/main` at **04605b7** against the **c55da9c** caiso-212 measured from —
**35 commits**, the substantive lanes being ercot-226 (the `ercot_as_held_location`
build and its fixes), nyiso-150 (both arms REJECTED-AS-ARMED), site-facts-2, and
the caiso-212 merge itself (PR #4190). Every standing number below was
re-measured at this HEAD, **never carried**.

| # | check | instrument | result |
|---|---|---|---|
| 1 | keeper identity | `keepers/CAISO.json` | `2026-08-17-caiso-200-h1-memberpanel` — **unchanged** |
| 2 | determination | `calibration_verdict.py --run-id <keeper>` (never a solve) | **NOT-YET**, reproduced exactly; rubric **v3.4**; `reasons` = *"undocumented out-of-tolerance (FAIL) criteria: price_mean"* |
| 3 | keeper text truthfulness | `audit_keepers.py --iso CAISO` | **PASS, 0 failures / 0 warnings** |
| 4 | status sync | `build_status.py --iso CAISO --check` | *"status parts in sync (1 keepers: CAISO)"* |
| 5 | DOF ledger | keeper `calibration_attestation.json` | **10/7** (`free_parameters.n_entries: 10`, `n_residual: 7`) |
| 6 | holdout posture | `calibration-complete.json` | `complete` = {NEISO, NYISO, PJM}; `final` carries **no ISO** (only `_note`); CAISO in `withdrawn` — **in neither grant block**, and its withdrawn entry **byte-equal** across the whole delta (10,846 chars, identical) |
| 7 | spend freeze | `holdout-freeze.json` | **ACTIVE** (`active: true`, declared 2026-07-25, re-armed 2026-08-06) |
| 8 | registrations | registry sidecars + run payloads | keeper + the caiso-205 pair — all three **present and tracked**, years `[2023, 2024, 2025]` each, payloads on disk — **no out-of-training year touched** |
| 9 | matrix cell census | CAISO shard | **K 64 · U 33 · I 15 · R 9 · O 6 · G 5 = 132** — **exactly as the charter pre-registered**; n/a **94 → 96** |
| 10 | matrix integrity | `check_mechanism_matrix.py` | **exit 0**, *"integrity OK"*, keeper stamps match every `keepers/<ISO>.json`, §5.x prose headers match — **but 239 unresolvable anchors, up from 0 (§3)** |
| 11 | **gate-POSTURE cross-check** (caiso-208's protocol) | shard `gates` stamp + §5.2 header read back against the verdict | §5.2 header **CURRENT**. Shard stamp: open-gate content **current**, but its HEAD-relative facts (HEAD sha, n/a count) are superseded — **refreshed this session** on the caiso-208/209/210/212 records-truthfulness precedent |
| 12 | **gate-MAGNITUDE cross-check** (caiso-209's protocol) | `calibration_verdict.py --json` | **every recorded magnitude re-read independently and confirmed** — scorecard below; nothing carried forward unread |

**Scorecard, re-stated in full from this session's own `--json` read**
(`grade_summary`: scored 8, target_grade 6, commercial_grade 0, ledgered 1,
fails 1; `rubric_version` 3.4):

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

Caveat budget: **ledgered 1 of 1, protective 0 of 0** (`budget`:
`protective_max 0`, `ledgered_max 1`) — at budget, not over it.
**C3c standing rule correctly silent**: guard (a) is *lone failure only*, C3a
also fails, so the determination stays **NOT-YET** and C3c reads CAVEAT at full
magnitude, as designed.

**Foreign movements verified legitimate, not assumed.** **Zero movement across
the whole delta** in `calibration_verdict.py`, `audit_keepers.py`,
`build_status.py`, `holdout_policy.py`, `check_mechanism_matrix.py`,
`check_bench_freshness.py` and `bench_stamp.py` — 0 commits each, so every
number above is produced by the same instruments caiso-212 used. The
`calibration-complete.json` top-level key set, and all three grant blocks, are
**structurally identical** across the delta.

**The CAISO shard's cell-key diff across the delta is exactly two additions and
nothing else** — measured, not inferred:

| key | cell | origin |
|---|---|---|
| `ercot_as_held_location` | `.` | `5a5b387` (ercot-226, rule 28c: a new row needs a cell line in EVERY shard) |
| `nyiso_iroquois_winter_spread` | `.` | `2bf4038` (nyiso-150, the row split) |

**Zero keys removed; ZERO CAISO cell verdicts moved.** Both are foreign
rule-28c `·` cells, so they move the **n/a count only** — the caiso-209/212
precedent, not a defect, exactly as the charter anticipated.

**Branch A discipline honoured:** no solve, no probe, no re-litigation of the
C3a basis (CLOSED — caiso-203 ruling 1), no re-run of the caiso-204
identification, the caiso-205 A/B, or the FFR-4F anchor A/B.

---

## §2 — THE CONDITIONAL CHECK, RUN: both carry legs hold, so the bench-staleness adjudication **carries on caiso-212's own terms** and DO-NOT-REDO applies

The charter set an explicit, two-legged carry test, and was equally explicit
that failing **either** leg is the "new evidence" that re-opens the cell on its
own terms. Both legs were **measured, not assumed**.

### 2.1 Leg (a) — the printed fingerprint is still `dbea7bf45111`: **HOLDS**

Every CAISO scorer invocation at this HEAD prints:

> `[!] STALE BENCHMARK: CAISO part(s) 2023.json.gz, 2024.json.gz, 2025.json.gz were NOT written by the builder at HEAD (fingerprint dbea7bf45111).`

**Unchanged from caiso-212.** And this was corroborated independently of the
banner, which matters because the banner is exactly the surface a stale
conclusion would be read off: **all four `BUILDER_SOURCES` files carry 0
commits since `c55da9c`** —

| BUILDER_SOURCES file | commits `c55da9c..HEAD` |
|---|---|
| `scripts/render_calibration_html.py` | **0** |
| `scripts/render_backcast.py` | **0** |
| `scripts/lib/backcast_artifacts.py` | **0** |
| `scripts/lib/bench_stamp.py` | **0** |

The fingerprint is a hash over exactly those four files, so zero movement in the
set is the *cause* of the unchanged digest, not merely consistent with it.

### 2.2 Leg (b) — the frame-builder set: **HOLDS, by whole-file byte identity**

This leg cannot be discharged by the fingerprint, and that is the whole point of
its being a separate leg: under standing defect **D1** the frame-builder tier is
in **neither** `BUILDER_SOURCES` nor `ENGINE_PATHS`, so a change there would
**not** move the digest. caiso-212 demonstrated exactly that (its `_btm_frame`
change moved nothing; the digest moved only because the same sweep touched a
covered file). Leg (b) therefore had to be measured directly:

* **`scripts/run_calibration_full.py` carries 0 commits since `c55da9c`.**
* Line count **12,263 → 12,263**.
* **sha256 of the whole file at `c55da9c` and at HEAD:
  `887d5fa6a8a0995f…be7b12f3b` — IDENTICAL.**

Whole-file byte identity is a **strictly stronger** result than the chartered
per-function AST re-hash: if the file's bytes are identical, the caiso-210
twelve *and* `_btm_frame` *and* every CAISO-path callee within the file are
identical necessarily, with no function-selection judgement left to make. The
re-hash was therefore not merely passed but rendered moot for this delta. (The
working tree is clean against HEAD for both this file and `bench_stamp.py`, so
the measurement is of committed bytes, per Branch A.)

### 2.3 Consequence

**Neither leg failed, so the trigger did not fire.** The caiso-212 adjudication
— **STAMP-ABSENCE, NOT DRIFT**; C1's metered actuals reproducible; no
determination changes — **carries unchanged**, and the charter's DO-NOT-REDO
governs: the exposure was **not** re-derived, CAISO's bench parts were **not**
regenerated (a Branch B act, unfunded), and "0 with engine drift" was **not**
read as evidence for any part (defect D2: never computed).

**Filed item 5 is unchanged and still funding-blocked:** the three CAISO parts
remain unstamped and trip the HARD flag against `dbea7bf45111` on every scorer
run. It is **not a correctness defect** and its discharge stays a **by-product
of the next funded solve, never an errand of its own**.

---

## §3 — THE ONE NEW FINDING: 239 unresolvable mechanism-matrix anchors, foreign in origin and in a SHARED file — routed off-lane

`check_mechanism_matrix.py` still **exits 0** and reports *"integrity OK"*,
keeper stamps matching every `keepers/<ISO>.json`, and §5.x prose headers
matching. But its anchor line has moved materially against the caiso-212 record:

| | caiso-212 (`c55da9c`) | caiso-213 (`04605b7`) |
|---|---|---|
| anchors | *"0 unresolvable beyond the ratchet"* | **"239 unresolvable beyond the ratchet"** |

**Cause, measured.** `src/market_sim/config/scenarios.py` grew **14,381 →
14,429 lines (+48)** across exactly two commits, both ercot-226 —
`5a5b387` (the `ercot_as_held_location` build: field registrations, class
families, LP-builder opt-out) and `31bc76a` (moving the pairing guards from
`__post_init__` to design time). The shared base file
`docs/codebase-site/data/mechanism-matrix.js` was touched in the same sweep (and
by nyiso-150) **but `--fix-anchors` was never re-run**, so its stored
`scenarios.py:N` line digits now point below the shifted definitions. The
warning bodies show precisely that signature — constant offsets (`2047→2058`,
`11535→11571`: +11 before the first insertion point, +36 after the second).

**This is line-digit drift, not a broken matrix.** The checker itself states the
field **NAME** is the durable identifier, the integrity checks all pass, and CI
does not fail on it (warnings, exit 0). No CAISO cell, verdict, evidence
citation or keeper stamp is affected, and **no CAISO number in §1 depends on
it**.

**It is NOT CAISO's to fix (rule 25 `[R-ISO-SCOPE]`, and the rule 28 sharding
discipline).** The drift is in the **shared base row file**, which every ISO's
lane reads; repairing it from the CAISO lane would edit a cross-lane surface,
and `--fix-anchors` rewrites anchors for **all** ISOs' rows at once, not just
CAISO's. It also belongs to the lane that moved `scenarios.py`. **Routed to the
ercot-226 lane or governance as new open cross-lane item 4**, with the one-line
remedy recorded: `python3 scripts/check_mechanism_matrix.py --fix-anchors`
(repairs digits only; the field NAME is durable).

---

## §4 — Owner packet: UNCHANGED at TWO items

Nothing this session changes what the owner is being asked. The packet stays:

1. **Fund tail-formation object (a)** — the walled hourly PS water-state intake
   (caiso-141 / ruling 4, DECLINED three times). Its **most favourable** bound
   covers **62.1 % / 10.4 %** of the required 2024 / 2025 C3a move — **it does
   not close C3a alone**, and any Branch B pre-registration must say up front
   what a partial close is worth and what verdict a partial earns.
2. **Fund object (b)** — the import spot-capacity derivation (direct λ share
   **< 5 %**). Also does not close C3a alone.

**Absent either, the lane rests.** Owner ruling 5 stands: C3a must *genuinely*
pass; **NOT-YET is the honest fallback**; reaching the number through a §F-killed
lever is a rule-13 act. A re-verification that lands on the same conclusion adds
no third item.

---

## §5 — Filed items (unchanged; discharge at whichever session produces a SOLVE or PROMOTION)

1. **Stale DOF text** — `offer_curve_by_group` still reads
   `identification: "residual"`; CAISO's CC_REGULAR/CT_PEAKER bands have been
   measured from OASIS PUB_DAM_GRP since 2026-08-02 (caiso-202 §H).
   **Re-verified still open this session.**
2. **Regenerate the keeper's `legitimacy_diagnostics.json` at HEAD** — one
   `chp_steam` (plant 10034) D-4 row is diagnostics-code vintage drift.
3. **Site retention** — the caiso-205 pair postdates the keeper; prunes as
   prior-to-keeper at the next promotion, in the ordinary way.
4. **A promoting session must re-measure and re-state the WHOLE scorecard** from
   the verdict output, never carry rows forward from a superseded run.
5. **CAISO's three bench parts are UNSTAMPED** and trip the HARD STALE BENCHMARK
   flag on every scorer run, against `dbea7bf45111`. **NOT a correctness
   defect** (re-derived caiso-212 §2; carry test re-run and held here, §2).
   Discharge as a **by-product of the next funded solve**, never as an errand of
   its own.

---

## §6 — Open cross-lane items (NOT CAISO's to fix — rule 25)

1. **`check_bench_freshness` defects D1 + D2** — VERIFIED NOT REPAIRED at
   caiso-212 §2.3 and **unchanged here** (`check_bench_freshness.py` carries 0
   commits across this delta): the frame-builder tier is still in **neither**
   `BUILDER_SOURCES` nor `ENGINE_PATHS` (D1), and the continue-after-HARD still
   makes *"0 with engine drift"* vacuous for every stale part (D2).
   nyiso-148/149's mechanism; route to that lane or governance.
2. **Five-ISO bench regeneration + CI gate** — program-level sequencing; NYISO's
   leg done at its nyiso-149 promotion; **CAISO's leg is filed item 5**,
   funding-blocked.
3. **`cccc911` (2026-08-19) swept all 187 canonical `frontend/data/hindcast`
   sidecars** — stale forecast-run citations program-wide, including the SHARED
   `mechanism-matrix.js` base row for `caiso_ra_mpb_capacity_anchor`. Fixing only
   CAISO's would make the shared file inconsistent.
4. **NEW — 239 unresolvable mechanism-matrix anchors** (§3). Foreign in origin
   (ercot-226 grew `scenarios.py` +48 lines without re-running `--fix-anchors`)
   and located in the SHARED base file. Exit 0 / integrity OK / CI not failing;
   line-digit drift only. Remedy:
   `python3 scripts/check_mechanism_matrix.py --fix-anchors`.

Route all four to a cross-lane or governance session.

---

## §7 — Verdict and next number

**REST CONTINUES.** The keeper stands at `2026-08-17-caiso-200-h1-memberpanel`,
**NOT-YET**, with C3a the sole load-bearing failure and C3c the single ledgered
caveat. Nothing was solved, armed, registered or regenerated; **no cell verdict
moved**; the bench-staleness adjudication **carries on measurement, not on
assumption**; and the owner packet is unchanged at two items.

**Next number: caiso-214.**
