# Model Audit Program — Director Status Board (2026-08)

> # ⛔ PROGRAM PARKED AT G1 BY OWNER DECISION — WS3/PERF PAUSED FOR CALIBRATION
>
> **This is not drift and nothing below is late.** The owner paused WS3/PERF-B so
> the calibration program can run. *PERF-B merged byte-green* is a G2
> precondition, so **G2 cannot be declared while WS3 is paused** and the program
> sits at **G1**. **DOCS-B** (G2), **SITE-A** (G3) and **AUDIT-B** (G3) are
> **waiting by design**. The FFR desk's **Q.2 supersession battery**, which
> commissions at G2 (`ffr-owner-sitting-2026-08-02.md` AS.6), **does not fire.**
> Whoever un-parks the program starts at the **RESTART CHECKLIST** at the bottom
> of this board, not at change (a).
>
> ### 🟢 NEW AT v8 — RESTART WINDOW OPEN: keepers resting; the owner may declare the freeze and resume WS3.
>
> The park's stated precondition for restart is **keeper stability**, and for the
> first time it is plausibly satisfiable: **every ISO lane is at rest by a
> decision rather than mid-lever** — ERCOT rests (#4084), MISO's blocking lane is
> closed (#4069), NYISO has promoted (#4081), CAISO rests at NOT-YET (#4066) with
> its open finding scorer-only (#4080), NEISO produced a NOT-YET with no keeper
> move (#4082), PJM unmoved since pjm-162. **This is not a freeze — only the owner
> can declare one** — but declaring one would no longer interrupt an armed lane.
> **The option is served, not taken.** The park holds until the owner says
> otherwise.

> **STATUS: PARKED AT G1** — live rollup maintained by the program-director
> session, updated on each owner "refresh". Canonical program definition:
> `docs/model-audit-release-plan-2026-08.md` (its §8 ledger is the durable event
> record; this board is the at-a-glance state). Completion figures are the
> director's estimate against each workstream's full DoD (A+B halves).

**Snapshot (v8):** 2026-08-18 ~03:45 UTC cycle, read completed **04:25 UTC** ·
`origin/main` @ **`7e6da12`** · **ZERO open PRs** · **nine PRs merged since the
v7 records landed** (#4074, 2026-08-17T20:50:49Z): **#4080–#4088**.

**Headline: calibration converged.** ERCOT promoted then rested after three
negative lanes; MISO's C3a-2025 lane closed by owner ruling; NYISO promoted to
the Astoria stack-duplicate intake correction; CAISO scorer-only and resting;
NEISO re-assessed with no keeper move. **Two items the dispatch expected to be
closed are not, and both are recorded as corrections below: the golden tier has
had no CI run since the red, and audit row O4 is still open.**

## What moved this cycle

1. **🟡 GOLDEN-TIER RED RESOLVED — in the code and on a verified local replay,
   NOT yet in CI.** Root cause (#4071):
   `curate_lmp.py::_neiso_flat24_repair` assigned the **string** `"02"` into the
   **int64** `Hr_End` column of the 2018–2023 NEISO flat-24 vintage, which pandas
   3.0.3 raises on where older pandas upcast — introduced by neiso-97's `a2b5e3d`
   (#4043) three hours pre-cron; fixed by relabelling with the integer `2`
   (`d4fbf44`). **Deliverables verified:** the finding's §7 records a **full local
   replay of all four CI job steps, all green** (9/9 datatypes → emissions 2023 →
   pytest tier 44 passed / 2 skipped → loud-failure guard clean), plus the
   standalone step-5 command green and the unit test 7/7.
   **CORRECTION, live-read at 04:23 UTC: no golden-tier run has executed since.**
   Latest run is **still the red `31999181985`**; last green is still
   `31913648051` (2026-08-15 dispatch). **The tier's standing expectation returns
   to green and the next red is again a NEW finding — but BLOAT-S2's D3 leg and
   every byte-green claim stay unprovable until one `workflow_dispatch` runs or
   the Monday 05:37 UTC cron fires.** Owner call, cadence card F.
2. **WS3/PERF close-out landed (#4075)** — wallclock-baseline PERF-B section +
   perf-recheck completion note: per-change deltas, HEAD-era keeper-replay anchor,
   corrected §2.4 attribution, gate record with keeper ids, the keeper-treadmill
   story, environment findings, open items handed forward. **The park is now
   recorded in the lane's own handoff, not just on this board.**
3. **CALIBRATION CONVERGENCE** — per-ISO detail in the keeper table below and in
   §8's `2026-08-18 (03:45 UTC director cycle — calibration convergence)` entry.
4. **GOVERNANCE — the declaration desk sat and said NOT YET three times.** Under
   rubric **v3.3** (#4077, ledgered at v7): **#4083** assessed PJM, NYISO and
   NEISO for `final` — **all three NOT YET on the merits**, NYISO least ready;
   **#4086** re-verified NYISO's against the promoted nyiso-142 keeper,
   recommendation unchanged; **#4082** re-assessed NEISO (neiso-100) — **`final`
   still NOT YET**, nothing granted, keeper unchanged, determination re-verifies
   **CALIBRATED**, frontier probe byte-unchanged (0/0/0 h > $300, RCPF dormant in
   all 78,840 family-hours). `final` remains **empty for every ISO**.
5. **AUDIT ROWS O5/O4 worked (#4085) — with a correction.** **O5 CLOSED**, and
   re-verified on a newer keeper set than the closing session could cite; its
   residual (a **third** ungated recipe-replay path,
   `knob_jacobian.py::solve_year`, outside **both** the legacy-P2 and holdout
   gates — a free `--year 2019` would have solved a locked-test year under an
   active freeze) **found and fixed in-session, solve-neutral**, with 10 tests + 6
   subtests pinning hard-fail-not-rewrite semantics on all three paths.
   **O4 is RE-MEASURED and STILL OPEN**: the numeric premise survives the guard
   (**14.2–36.7 %**, **17 of 18 ISO-years** above the 15 % norm), the *detector*
   question is closed on evidence across four lanes, and what remains is **the
   disposition act alone** — recommendation **(A) close with cause + lift the
   VALIDATION tier only**, `final` untouched. **Open audit rows are therefore
   O4, O6, O7 — not O6 and O7.**

## Keeper table (read from `frontend/data/backcast/keepers/<ISO>.json` at `7e6da12`)

| ISO | Designated keeper | Determination | This cycle |
|-----|-------------------|---------------|------------|
| ERCOT | `2026-08-17-ercot215-arm-decontam` | `NOT-YET` | **Promoted on owner instruction (#4070).** Then ercot-216 (#4076) C3c residual *spent and empty*, ercot-217 (#4079) no admissible regime lever (D-3 negative), **ercot-218 (#4084) direct-driver NOT-TRANSFERABLE on all five gates → backcast lane RESTS**, Door D confirmed as floor. *Post-rest, owner-directed:* research memo (#4087) + **option-B decision card #4088, DRAFT AWAITING SIGNATURE, nothing armed** |
| CAISO | `2026-08-17-caiso-200-h1-memberpanel` | `NOT-YET` | Lane **rests at NOT-YET** by owner ruling caiso-201 (#4066). **C1 band threshold finding recorded scorer-only (#4080)** — no rubric constant edited, no solve: the 8 TWh is a *cap*, band = ±4.148, row misses by 0.0955 TWh (102.2 %); a generation basis would **tighten** to 3.515; "C1 is a C3a symptom" refuted; every candidate widening flips **0** determinations |
| PJM | `2026-08-15-pjm-162-inputclock` | `CALIBRATED` | Unmoved. Assessed for `final` (#4083) — **NOT YET on the merits**; 2020 rung **not data-ready** |
| MISO | `2026-08-16-miso-160-wefor-shape` | `NOT-YET` | **C3a-2025 lane CLOSED by owner ruling as a model-class limit (#4069)** — no solve, no lever, keeper unchanged; the stated Shape-1 data blocker measured **FALSE**, the real blocker is a mechanism already cell `G` and **measured inert**. GADS data ask **resolved against on evidence (#4078)** — FAILS on C and D |
| NYISO | `2026-08-17-nyiso-142-stackdup` | `CALIBRATED` | **PROMOTED (#4081)** — the Astoria stack-duplicate intake correction, A/B pre-registered and solved at nyiso-142 (#4068), **no new solve**. Rule 14, **zero free parameters**, **718/718 `scenario_config` fields identical** ⇒ **not a lever, no cell verdict moves**; all six gates clean, C3c bit-unchanged 21/3/24 h |
| NEISO | `2026-08-17-neiso-99-joint-p1` | `CALIBRATED` | **Unchanged.** Re-assessed under v3.3 (#4082): `final` **still NOT YET** on re-measured blockers (2019 cannot exercise C3c — RT max $261.35; Pilgrim gap ≈ 91 % of the 2019 C1 band; H1-2026 blocked by the six-ISO partial-year gate). **neiso-98's leg 3 has expired** — the 2022 touchpoint now differs on six axes at hash grain; a v3.3 re-score of 2022 was **refused on the active freeze** |

**Markers at HEAD:** `complete` = {NEISO, NYISO, PJM} · **`final` = empty
(`_note` only)** · **no locked-test year has ever been spent by any ISO.**
Determinations: **PJM, NYISO, NEISO `CALIBRATED`** · **ERCOT, CAISO, MISO
`NOT-YET`** — the CALIBRATED set is exactly the `complete`-marker set.

## Workstream rollup

| WS | State | Completion | Blockers / next |
|----|-------|------------|-----------------|
| WS1 `AUDIT` | AUDIT-A **completed** (#3991). Rows **O8 CLOSED**, **O5 CLOSED** (#4072, re-verified **stronger** at #4085 on a newer keeper set, residual third replay path **gated + tested**), **O4 re-measured and STILL OPEN** (#4085 — disposition act only, owner card, recommendation (A)) | **In progress ~91%** | **AUDIT-B gated at G3 — waiting by design.** Rows **O4, O6, O7** open |
| WS2 `DEBUG` | **COMPLETED** — DEBUG-A ✓, DEBUG-B ✓, pjm-162 promoted, sibling-import residue retired, landing-verify green on merged main. Row B1 annotated **STALE** (#4085), no code change | **Completed** | none; no DEBUG-C continuation chartered |
| WS3 `PERF` | PERF-A ✓. **PERF-B PAUSED BY OWNER.** Stage-0: **5 of 6 ISOs captured** (ERCOT #4033, NEISO #4041, NYISO #4050, CAISO #4058, MISO #4060; **PJM never captured**). Changes: **(c) landed via #3964**, **(d)+(e) merged via #4067**, **(a)/(b) unstarted**. **Close-out note + wallclock baseline landed (#4075)** | **Paused ~74%** | **Paused, not blocked — and the restart precondition is now plausibly satisfiable (see banner).** On restart: freeze calibration, then re-verify every golden — RESTART CHECKLIST |
| WS4 `DOCS` | DOCS-A **completed** (#3999 + #4005); DOCS-B held | **In progress ~60%** | **DOCS-B gated at G2 — waiting by design** |
| WS5 `SITE` | Held by design | **Not started** | gated at **G3** |
| WS6 `BLOAT` | Prunes B-1..B-8 merged; **BLOAT-2 CLOSED** (#4032); **BLOAT-3 ADJUDICATED** (#4031) and **EXECUTED** (BLOAT-S2 #4047, −444.5 MiB / 144 files at tip). **The parity RED is CLEARED — gate measured GREEN this cycle** | **Completed** | **none.** `check_registry_payload_parity.py` at `7e6da12`: **"parity OK (26 runs checked, 26 bundle dirs swept, 0 known-unsynced tolerated)"**. The MISO payloads it awaited landed **2026-08-17T01:58:04Z** (`3c2aa5e`), i.e. **before both v7 stamps** — tree-only name-parity also 1:1 at `6cc332e` (20/20) and `f087c67` (26/26). The RED was carried stale for two cycles |
| — `GOLDEN-TIER-FIX` | **COMPLETED and independently verified** (#4014). First scheduled cron came back **RED**, **diagnosed + fixed same-day** (#4071), **deliverables verified by a full local four-step job replay, all green** | **Completed** | **the fix is not in question. The CI proof is: STILL NO RUN since the red at 04:23 UTC.** One `workflow_dispatch` settles it, else the Monday 05:37 UTC cron — **top standing open item** |

## Stage-0 golden staleness (recomputed at `7e6da12`)

Read from the keeper shards and
`results/regression-goldens/perfb-stage0/manifest.json`. **Two ISOs' stale-against
ids moved again since v7** (ERCOT at v7's addendum, NYISO this cycle).

| ISO | Golden captured against | Designated keeper at `7e6da12` | Verdict |
|-----|-------------------------|--------------------------------|---------|
| ERCOT | `2026-08-15-ercot204-rule26-delete` (#4033) | `2026-08-17-ercot215-arm-decontam` | **STALE — keeper moved twice** |
| NEISO | `2026-08-14-neiso-93-envelope` (#4041) | `2026-08-17-neiso-99-joint-p1` | **STALE** — the re-stamp-not-re-solve shortcut was established for **neiso-97 only**; re-establish before relying on it |
| CAISO | `2026-08-16-caiso-197-w2-r5` (#4058) | `2026-08-17-caiso-200-h1-memberpanel` | **STALE** |
| MISO | `2026-08-16-miso-160-wefor-shape` (#4060) | `2026-08-16-miso-160-wefor-shape` | **CURRENT** |
| NYISO | `2026-08-16-nyiso-140-layup-exclusion` (#4050) | `2026-08-17-nyiso-142-stackdup` (#4081) | **STALE — newly, this cycle.** But **cheap to re-establish**: the promotion is a data correction with 718/718 `scenario_config` fields identical, so compare committed sidecars before spending a solve |
| PJM | — | `2026-08-15-pjm-162-inputclock` | **NO GOLDEN — never captured** |

**Count: 4 stale / 1 current / 1 no-golden** (was 3/2/1 at v7).
**The lane's finding still stands:** stage-0 could not converge because ISO
keepers moved faster than captures completed, and it proved itself once more this
cycle. **A calibration freeze remains the precondition for completing WS3** — but
see the banner: for the first time, calling it would interrupt nothing.

## Gates

- **G0** adopted ✓ (2026-08-13) · **G1** DECLARED ✓ (2026-08-16, #4006).
- **G2 — UNREACHABLE while WS3 is paused.** Leg 1 is *PERF-B merged byte-green*,
  PERF-B is paused by owner decision, and no other leg substitutes. The legs:
  1. **PERF-B merged byte-green** — partial: 5 of 6 captured, **4 now stale**,
     (c)/(d)/(e) merged, (a)/(b) unstarted. **Paused and still short:** byte-green
     needs goldens, and byte-green cannot even be *claimed* while the golden tier
     has no green CI run.
  2. **One completed fast-tier-green `ci.yml` run** — the sparse block landed
     (#3964, runner-validated at 31873178938: 6838 passed / 31 skipped).
  3. **A keeper freeze** — **owner call, outstanding across six director cycles.
     NEWLY REACHABLE:** no ISO lane is mid-lever at this HEAD (see banner).
  4. **Branch-protection flip** — owner action, memo ready.

  On declaration the PM notifies the FFR desk (Q.2 battery).
- **G3** — unchanged: after G2, **DOCS-B** + the **BLOAT leg**. BLOAT's verdict,
  its chartered execution **and now its parity gate** are all satisfied
  (#4031 + #4047 + measured green); the golden-tier proof leg is satisfied by
  #4014 + the green dispatch.
- **G4** — unchanged: SITE-A + AUDIT-B.

## Watch

- **🟡 GOLDEN-TIER CI PROOF — the one item this cycle could not close.** Fix
  merged (#4071) and verified by full local job replay; **no CI run since the red
  `31999181985`.** Until one runs, BLOAT-S2's D3 leg and every byte-green claim
  are unprovable. One `workflow_dispatch`, or wait for Monday 05:37 UTC.
- **DURABLE LESSON (unchanged, and the reason the above matters):**
  `golden-data-tier.yml` is the **ONLY** workflow that runs
  `scripts/regenerate_clean.py`, so **any curation-time defect under
  `scripts/data/curate_*.py` has NO pre-merge signal** — invisible to every PR
  check, surfacing only on the weekly cron, and compounded by `data/clean` being
  derived and gitignored (an already-curated local tree shows nothing wrong).
  **Treat curate-script changes as unguarded.**
- **🟠 #4054 / nyiso-140 null-treatment question — STILL OPEN, NEVER ADJUDICATED,
  and now a MATRIX-HYGIENE item rather than a keeper risk.** Verified this cycle:
  nothing merged since the v7 refresh touches it and the dispatched recheck lane
  has produced nothing on main. The NYISO keeper has moved to **nyiso-142**, whose
  promotion is a data correction with **718/718 `scenario_config` fields
  identical** — so the `reliability_floor_plant_exclusions` arm and its cell
  verdict **`K` carry forward unchanged**. What is unproven is the **A/B evidence
  behind the verdict**, not the keeper's numbers. **Re-checking it costs a
  fidelity read, not a solve.** The stage-0 *captures* remain cleared on
  code-state evidence.
- **🟢 CLEARED — BLOAT-2 parity.** Gate run, not inferred: **GREEN at HEAD**
  (26 runs / 26 bundle dirs / 0 tolerated). Retired from the owner queue.

## Owner queue at cycle end

Carried verbatim, plus what this cycle added and removed.

0. **🔴 GOLDEN-TIER PROOF-OF-FIX `workflow_dispatch`** — the #4071 fix is merged
   and locally replayed green; the tier's latest CI run is still the red one.
   Billed minutes, so the owner's call. *(Carried from v7; unchanged.)*
1. **NEISO-100 keeper-candidate + EIA-923-2025-vintage questions** (#4082 — the
   2025 final vintage re-checked and **still not landed**).
2. **Validation-freeze lift signature** — the **O4/O5 card**
   (`AUDIT-FOLLOWUP-o5-o4-2026-08-18.md` §2.4), recommendation **(A) close the
   charter with cause, lift the VALIDATION tier only, leave `final` empty**.
   **The detector question is closed on evidence — "resolve the detector
   question" is no longer one of the choices.**
3. **NYISO frontier re-declaration** — **in flight**.
4. **O6 — locked-test scheduling.** 2019 and H1-2026 are **touch-once** and **no
   ISO has ever spent one**; re-verified at this HEAD (`complete` = {NEISO,
   NYISO, PJM}; `final` holds only its `_note`). **Never let a lane spend one**;
   scheduling is the owner's alone.
5. **O7 — ERCOT P0 bit-identity proof forfeited** (accept-and-document, or
   charter restoration).
6. **decision-1 ack** — warm-start closed-overtaken; **still unacked, FIFTH
   cycle**; a one-word ack retires it.
7. **NEW — ercot-218b option-B decision card (#4088)**, drafted on the owner's
   instruction after the ERCOT lane rested: a structural artificial-shortage
   mechanism (B-1 signature text, three-stage zero-fitted-scalar spec,
   direction-blind kill gates). **DRAFT AWAITING SIGNATURE — nothing armed, no
   `ScenarioConfig` field, no matrix cell minted.**
8. **caiso-199 NOT-YET determination** — carried; the CAISO lane itself now rests
   at NOT-YET by ruling caiso-201 (#4066).
9. **ercot-214 counterpart-decontamination lever** — carried (G-SPUR
   phantom-adder risk); superseded in practice by the ercot215 promotion (#4070),
   which is the decontamination arm.
10. **RETIRED THIS CYCLE:** ~~BLOAT-2 parity RED~~ (gate measured GREEN);
    ~~miso-161 C3a-2025~~ (ruled and merged, #4069).

## Session roster

> **DEVIATION — SECOND CONSECUTIVE CYCLE: this roster is NOT a live
> `list_sessions` read.** The MCP call returned *"requires approval"* on both
> attempts this cycle, as it did across four attempts at v7. The roster below is
> rebuilt from **`Claude-Session` commit trailers on merged `main`** plus the live
> branch / PR / merge state — **stronger than v7's inference (these are actual
> session ids), but still not a live session read.** Re-establish the live read
> next cycle.

**Lanes that landed work this cycle** (session id from the commit trailer; every
branch merged and auto-deleted except where noted):

| Lane | Session | Branch | Landings |
|------|---------|--------|----------|
| ERCOT ercot-218 / 218b | `session_01UiMbYiJGoKXKznPpuaKJRq` | `claude/ercot-218-direct-driver-5ckiur` — **still live at `f872eb5`** (content merged) | #4084 lane close · #4087 research memo · #4088 option-B card |
| Declaration desk | `session_01DF71WcCxRSpHBXbBPd6jLs` | `claude/iso-final-readiness-assessment-gx3iei` | #4083 PJM/NYISO/NEISO `final` readiness · #4086 NYISO re-verify |
| Audit follow-up O5/O4 | `session_01S7DeYvsRhh84mPxMieSwzN` | `claude/audit-followup-o5-o4-99tvxu` | #4085 |
| NEISO neiso-100 | `session_01AeDHzi3JK1aocqXAtofeKU` | `claude/neiso-100-declaration-reassess-mxtkjd` | #4082 |
| NYISO promotion | `session_01EupFoLDBwFCU9uPeUZ7qGs` | `claude/nyiso-calibration-declaration-o7xxcz` | #4081 |
| CAISO C1 band | `session_01B2bqhsVhaSnntaQy5C1NL9` | `claude/caiso-gate-c1-threshold-kf3c3q` | #4080 |

**Live remote branches** (complete set at 04:25 UTC, `git ls-remote --heads`):

| Branch | SHA | Read |
|--------|-----|------|
| `main` | `7e6da12` | tip (merge of #4088) |
| `claude/ercot-218-direct-driver-5ckiur` | `f872eb5` | ERCOT lane; content merged, branch not deleted |
| `claude/director-records-v7-9u1czg` | `277313d` | v7 records; merged via #4074, branch not deleted |
| *(this lane's branch once it pushes)* | — | board v8 + §8 entry |

**PERF-B lanes — STOOD DOWN** (per the owner's pause): `perf-b-ws3-recheck-9r11sg`
(revived post-v7-snapshot for #4067, then **closed out with #4075**),
`perf-b-stage-0-cont-tnyuf2`, `perf-b-stage-0-cont-le1qe9` (its staleness ledger
is the WS3 handover artifact). All merged and deleted.

## Refresh protocol

On each owner "refresh", the director: (1) lists sessions + fetches fresh
`origin/main`, re-reads plan §8 and lane handoffs; (2) reports each workstream
as **not started / in progress with % / completed / pending blockers**;
(3) issues prompts for any lane whose gate has cleared, appends the §8 ledger
entry, and updates this board in the same pass.

**Under the standing deviation, step (3)'s two write duties are dispatched to a
records lane rather than pushed by the director.** A refresh is not complete
until that lane has landed both files — and, per the v5→v6 gap, a dispatch that
is never launched leaves the board silently wrong. **Verify the landing before
declaring a cycle done.**

**While the program is parked, the refresh cycle is not the live instrument it
was.** A park-period refresh should confirm only (a) whether the golden tier is
proven green **in CI** after the #4071 fix, (b) whether the owner has ruled on
anything in the owner queue, and (c) whether the keeper freeze has been called —
that last one is the un-park trigger, **and as of v8 it is the live question, not
a hypothetical**.

## RESTART CHECKLIST — for whoever un-parks the program

**Do these in order. Do not start at change (a).**

1. **FREEZE CALIBRATION FIRST.** The precondition, not a nicety — the owner must
   declare it and no lane can. Until it holds, every golden captured can be staled
   by the next promotion, which is exactly how stage-0 failed to converge across
   six cycles. **At v8 the cost of declaring it is at its lowest: no ISO lane is
   mid-lever.**
2. **Re-verify every stage-0 golden against the then-current keepers** before
   resuming any change. Do not trust this board's staleness table — re-read
   `frontend/data/backcast/keepers/<ISO>.json` and
   `results/regression-goldens/perfb-stage0/manifest.json` at that HEAD and
   re-derive it.
3. **Re-capture what is stale, and know which are cheap.** At `7e6da12`: ERCOT,
   CAISO, NEISO, **NYISO** stale; PJM never captured. **NYISO is the cheap one** —
   nyiso-142 is a data correction with 718/718 `scenario_config` fields identical
   to nyiso-140, so compare committed sidecars first. The
   **re-stamp-not-re-solve** shortcut was established for **neiso-97 only** and
   NEISO has since moved to neiso-99 — **re-establish it before relying on it.**
   Apply the same sidecar-comparison test to every newly-stale ISO before
   spending a solve.
4. **Capture PJM** — the one ISO with no golden at all, and the one gap no amount
   of keeper stability closes.
5. **Do NOT re-do change (c).** It landed via #3964 and is byte-identical at HEAD.
   Verify the blob (`af34031c`) rather than re-porting it.
6. **Close the #4054 residual if you want belt-and-braces** — a fidelity-only
   re-check at HEAD (hash compare, **no solve**) confirms the exclusions were
   active in the NYISO capture. Optional; the captures are already cleared on
   code-state evidence. **The nyiso-140 A/B question is separate, still
   unadjudicated, and is now matrix hygiene** — the cell verdict `K` carries into
   nyiso-142 unchanged, so it bears on the evidence, not the numbers.
7. **Then, and only then, resume changes (a)–(e)** — and re-read the G2 leg list,
   because *merged byte-green* is what the gate wants, not captures.
8. **Confirm the golden tier is green IN CI before claiming any byte-green
   result.** The #4071 fix has landed and replays green locally, but **its CI
   proof is still outstanding** — one `workflow_dispatch`, or the next weekly
   cron. A tier that cannot provision `data/clean` cannot prove byte-identity of
   anything, and a local replay is not the gate.
