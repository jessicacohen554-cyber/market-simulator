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

> **STATUS: PARKED AT G1** — live rollup maintained by the program-director
> session, updated on each owner "refresh". Canonical program definition:
> `docs/model-audit-release-plan-2026-08.md` (its §8 ledger is the durable event
> record; this board is the at-a-glance state). Completion figures are the
> director's estimate against each workstream's full DoD (A+B halves).

**Snapshot (v7):** 2026-08-17 ~09:25 UTC · `origin/main` @ **`6cc332e`** ·
**ZERO open PRs** — #4051, the duplicate MISO stage-0 capture, was **closed
unmerged at 09:21:38Z** (`mergeable_state: dirty`, stale on arrival), which is
the correct disposition and empties the queue.

**Three corrections carried into this snapshot**, all detailed in the §8 entry
`2026-08-17 (owner decision: WS3 paused, program parked at G1)`:

1. **Change (c) is ALREADY LANDED, not "landable standalone".** The `ci.yml`
   fast-tier sparse block + `timeout-minutes: 20` merged via **#3964** (owner,
   2026-08-15T16:56:40Z); the file at HEAD is byte-identical (blob `af34031c`)
   to the prototype head. Nothing left to port; an empty-diff PR is impossible.
2. **neiso-97 IS the designated NEISO keeper** — the pause dispatch recorded it
   as "NOT A KEEPER". `keepers/NEISO.json` at HEAD carries
   `2026-08-17-neiso-97-dstrepair` (promoted #4055, re-verified twice). What is
   true is the *measurement*, not the disposition: the DST-repaired re-solve
   moved **nothing** (sidecars bit-identical to the superseded keeper).
3. **WS3 is one ISO further along than the dispatch recorded** — five of six
   captured (MISO landed via **#4060**), and the staleness picture has already
   changed again: **3 stale / 2 current / 1 no-golden**.

## Workstream rollup

| WS | State | Completion | Blockers / next |
|----|-------|------------|-----------------|
| WS1 `AUDIT` | AUDIT-A **completed** (#3991); **row O8 CLOSED** — NEISO SMD DST-naive clock repaired (#4043), keeper recipe re-solved at the repaired instrument (#4052), FINDING + probe landed (#4049); **O5 sharpened** (#4063) | **In progress ~87%** | **AUDIT-B gated at G3 — waiting by design.** Rows O4, O5, O6, O7 open |
| WS2 `DEBUG` | **COMPLETED** — DEBUG-A ✓, DEBUG-B ✓, pjm-162 promoted, sibling-import residue retired (census **0 bare sites / 0 live files**), landing-verify green on merged main | **Completed** | none; no DEBUG-C continuation chartered |
| WS3 `PERF` | PERF-A ✓. **PERF-B PAUSED BY OWNER.** Stage-0 partial: **5 of 6 ISOs captured** — ERCOT #4033, NEISO #4041, NYISO #4050, CAISO #4058, MISO #4060; **PJM never captured**. Changes **(a)–(e) UNSTARTED**; **(c) already landed via #3964** (not a standalone item) | **Paused ~65%** | **Paused, not blocked.** On restart: freeze calibration, then re-verify every golden — see RESTART CHECKLIST |
| WS4 `DOCS` | DOCS-A **completed** (#3999 + #4005); DOCS-B held | **In progress ~60%** | **DOCS-B gated at G2 — waiting by design** |
| WS5 `SITE` | Held by design | **Not started** | gated at **G3** |
| WS6 `BLOAT` | Prunes B-1..B-8 merged; **BLOAT-2 CLOSED** (Class-E rule adopted + parity sweep, #4032); **BLOAT-3 ADJUDICATED** (O2 staged (a)-only GO, #4031) and **EXECUTED — BLOAT-S2 merged #4047, −444.5 MiB / 144 files at tip** | **Completed but for one RED** | **BLOAT-2 registry/payload parity gate RED**, pending a MISO payload push — **currently UNOWNED** |
| — `GOLDEN-TIER-FIX` | **COMPLETED and independently verified** (#4014); authorized dispatch `31913648051` SPENT + GREEN. **But the first scheduled cron firing is RED** — see *Watch* | **Completed** | the fix is not in question; the **tier is not green on a scheduled firing at HEAD** |

## Stage-0 golden staleness at the pause (recomputed at `6cc332e`)

Read from the keeper shards and
`results/regression-goldens/perfb-stage0/manifest.json` — not inferred from PR
titles. This table supersedes the #4061 ledger's headline (*2 stale / 2 current
/ 2 no-golden* at `5b89e84`), which #4060 and #4065 overtook **within two
minutes of its own merge**.

| ISO | Golden captured against | Designated keeper at HEAD | Verdict |
|-----|-------------------------|---------------------------|---------|
| ERCOT | `2026-08-15-ercot204-rule26-delete` (#4033) | `2026-08-16-ercot213-arm-pubanchor` | **STALE — keeper moved** |
| NEISO | `2026-08-14-neiso-93-envelope` (#4041) | `2026-08-17-neiso-97-dstrepair` | **STALE by keeper id** — but the sidecars are bit-identical, so re-capture is a **re-stamp, not a re-solve** |
| CAISO | `2026-08-16-caiso-197-w2-r5` (#4058) | `2026-08-17-caiso-200-h1-memberpanel` | **STALE — staled 88 s after the ledger called it CURRENT** (#4065, 05:03:11Z) |
| MISO | `2026-08-16-miso-160-wefor-shape` (#4060) | `2026-08-16-miso-160-wefor-shape` | **CURRENT** |
| NYISO | `2026-08-16-nyiso-140-layup-exclusion` (#4050) | `2026-08-16-nyiso-140-layup-exclusion` | **CURRENT** |
| PJM | — | `2026-08-15-pjm-162-inputclock` | **NO GOLDEN — never captured** |

**The lane's finding, recorded as a finding:** stage-0 could not converge
because **ISO keepers moved faster than captures completed**. CAISO is the
sharpest instance — the ledger recording its golden CURRENT merged at 05:01:43Z
and the caiso-200 promotion staled it 88 seconds later. **A calibration freeze
is the precondition for completing WS3.** The director escalated this across
five cycles; it is **moot until WS3 restarts, and it will bind again on
restart.**

## Gates

- **G0** adopted ✓ (2026-08-13) · **G1** DECLARED ✓ (2026-08-16, #4006).
- **G2 — UNREACHABLE while WS3 is paused.** Stated in those words deliberately:
  leg 1 is *PERF-B merged byte-green*, PERF-B is paused by owner decision, and
  no other leg can substitute. The remaining legs, for the record:
  1. **PERF-B merged byte-green** — partial (5 of 6 captured, 3 already stale,
     changes (a)–(e) unstarted). **Paused.**
  2. **One completed fast-tier-green `ci.yml` run** — the sparse block itself
     **already landed** (#3964, runner-validated at 31873178938: 6838 passed /
     31 skipped), so this leg is no longer waiting on PERF-B to *land code*.
  3. **A keeper freeze** — **owner call, outstanding across five director
     cycles.** Unreachable at this snapshot by observation: CAISO promoted
     (#4065), ERCOT / NYISO / NEISO all moved 03:37–05:03Z, and a live CAISO
     lane branch sits off main.
  4. **Branch-protection flip** — owner action, memo ready.

  On declaration the PM notifies the FFR desk (Q.2 battery).
- **G3** — unchanged: after G2, **DOCS-B** + the **BLOAT leg**. BLOAT's verdict
  *and* its chartered execution are now satisfied (#4031 + #4047); the
  golden-tier proof leg is satisfied by #4014 + the green dispatch.
- **G4** — unchanged: SITE-A + AUDIT-B.

## Watch

- **🔴 GOLDEN-TIER WEEKLY CRON FIRED AND FAILED — a NEW finding, discharged
  here.** Run **31999181985**, `event: schedule`, **2026-08-17T05:48:08Z**, head
  **`6cc332e7`**, conclusion **FAILURE** (job 95296191095, 6 m 24 s). Died in
  step 5 *"Provision data/clean"*: **`curate_lmp.py` was the sole failing
  datatype** (`1/9 datatype(s) failed`; all others `[ ok ]`), so pytest never
  ran (*"junit report tier-report.xml does not exist — the tier did not run"*)
  and the loud-failure guard failed the job.
  - **BLOAT-S2's post-merge proof leg (D3 = "the first weekly golden-tier cron
    green after merge") is NOT satisfied — it is RED.**
  - Last golden-tier green remains `workflow_dispatch` **31913648051**
    (2026-08-15 23:01 UTC, `ccca569c`).
  - **Not diagnosed** — this records lane is docs-only with no `src/`/`scripts/`
    scope. **Needs a dispatched diagnostic lane.** Lead to clear first:
    `lmp-data` non-golden is *precisely* the corpus whose BLOAT-S2 evidence pass
    **FAILED** and which therefore **stays tracked**, so the Stage-2 untrack is
    not the obvious cause — but it is adjacent enough to rule in or out
    explicitly, together with the MISO-archive decay the same finding measured
    (2022 already 404).
- **#4054 / nyiso-140 null-treatment question — OPEN.** The stage-0 *captures*
  are cleared (see below); the **A/B itself is not**.

## Owner rulings outstanding at the pause

Carried forward verbatim; this list replaces the former alerts section.

1. **caiso-199** — NOT-YET determination (#4037 landed the FINDING, matrix cell
   and log entry; the disposition is the owner's).
2. **miso-161 C3a-2025** — charter C3c under frontier terms, or close as a
   model-class limit. **The lane is BLOCKED on this.**
3. **ercot-214 counterpart-decontamination lever** — G-SPUR phantom-adder risk
   (#4057 identified the mid-band spill's maker exactly and escalated).
4. **BLOAT-2 parity RED** — needs a MISO payload push; **unowned**.
5. **decision-1 ack** — warm-start closed-overtaken; a one-word ack retires it.
6. **Audit rows O4, O5, O6, O7.**
7. **O6 standing guard — restated and VERIFIED at HEAD.** 2019 and H1-2026 are
   **touch-once** and **no ISO has ever spent one**:
   `frontend/data/backcast/calibration-complete.json` carries `complete` =
   {NEISO, NYISO, PJM} and a `final` block holding **only** its `_note` — **no
   ISO holds a `final` marker at all.** **Never let a lane spend one**; the
   scheduling decision is the owner's alone.

**Also on the record — the [R-REGISTRY] defect (#4054), second of its class in
this program.** #4054 restored the `reliability_floor_plant_exclusions` override
block in `run_year`, a **silent no-op on main**; nyiso-140 introduced a lever on
that channel (#4026) and was promoted (#4042) *inside that window*. The
**stage-0 captures are cleared** — only the named-kwarg channel was broken, the
apply site was functional, and `capture_keeper_goldens.py` replays the recorded
config through `with_overrides`, so NYISO (the only keeper arming it) captured
with exclusions **ACTIVE** (`recorded_flag_count` 248, `scenario_config_drift:
[]`). **The nyiso-140 A/B null-treatment question stays open** with the
dispatched read-only recheck lane. Tails: #4059 de-duplicated the restored
block; #4044 repaired the duplicate-parameter `SyntaxError` that had broken 32
test modules and every calibration-solve import.

## Session roster

> **DEVIATION — this roster is NOT a live `list_sessions` read.** The dispatch
> specified one; the tool required an approval that never arrived across four
> attempts. The roster below is rebuilt from **live GitHub branch, PR and merge
> evidence** at 09:25 UTC. **Lane *sessions* are therefore inferred; lane
> *branches, PRs and merges* are live-read and exact.** Re-establish the live
> read next cycle.

**PERF-B lanes — STOOD DOWN** (per the owner's pause):

| Lane | Branch | Last landing | Status |
|------|--------|--------------|--------|
| PERF-B (first session) | `claude/perf-b-ws3-recheck-9r11sg` — **branch gone** | #4033 (ERCOT capture) | **STOOD DOWN.** Its follow-up #4051 **closed unmerged 09:21:38Z** |
| PERF-B (continuation) | `claude/perf-b-stage-0-cont-tnyuf2` — merged + deleted | #4041 NEISO · #4046 tool fix · #4050 NYISO · #4058 CAISO · #4060 MISO | **STOOD DOWN** |
| PERF-B (staleness ledger) | `claude/perf-b-stage-0-cont-le1qe9` — merged + deleted | #4061 (staleness ledger) | **STOOD DOWN** — its ledger is the WS3 handover artifact |

**Live branches at HEAD** (the only three that exist on the remote):

| Branch | SHA | Read |
|--------|-----|------|
| `main` | `6cc332e` | tip |
| `claude/nyiso-st-gas-underproduction-ev8gml` | `6cc332e` | NYISO nyiso-141/142 lane, level with main (#4062 landed) |
| `claude/caiso-backcast-calibration-2yk22l` | `f7c9dfa` | **live CAISO lane off main** — calibration running into the pause |
| `claude/director-records-v7-gsefnf` | this lane | board v7 + §8 entry |

**Recently landed and closed out** (branches merged and auto-deleted): WS6
BLOAT-3 charter (#4031) · WS6 BLOAT-2 Class-E (#4032) · **WS6 BLOAT-S2**
(#4047) · caiso-199 (#4037) · caiso-200 (#4040/#4048/#4053/**#4065
promotion**) · ercot-213 (#4036/#4045) · **ercot-214** (#4057) · **ercot-215**
(#4064, 12/12 sidecars byte-identical) · nyiso-140 (#4026/#4034/#4042) ·
miso-160 (#4035/#4044) · miso-161 (#4039/#4056) · miso-162 (#4059) ·
**neiso-97** (#4043/#4049/#4052/#4055) · **neiso-98** (#4063) · director
records v6 (#4038).

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
was.** Nothing in WS1/WS4/WS5 can advance and WS3 is stood down; a park-period
refresh should confirm only (a) that the golden-tier RED is owned, (b) whether
the owner has ruled on anything in *Owner rulings outstanding*, and (c) whether
the keeper freeze has been called — that last one is the un-park trigger.

## RESTART CHECKLIST — for whoever un-parks the program

**Do these in order. Do not start at change (a).**

1. **FREEZE CALIBRATION FIRST.** This is the precondition, not a nicety — the
   owner must declare the freeze, and it cannot be declared by any lane. Until
   it holds, every golden captured is a golden that can be staled by the next
   promotion, which is exactly how stage-0 failed to converge across five
   cycles.
2. **Re-verify every stage-0 golden against the then-current keepers** before
   resuming any change. Do not trust this board's staleness table — it is a
   snapshot of `6cc332e` and will be wrong the moment a keeper moves. Re-read
   `frontend/data/backcast/keepers/<ISO>.json` and
   `results/regression-goldens/perfb-stage0/manifest.json` at that HEAD, and
   re-derive the table.
3. **Re-capture what is stale, and know which are cheap.** At this snapshot:
   ERCOT, CAISO, NEISO stale; PJM never captured. **NEISO is a re-stamp, not a
   re-solve** — its keeper's sidecars are bit-identical to the golden's. Check
   whether the same is true of any newly-stale ISO before spending a solve.
4. **Capture PJM** — the one ISO with no golden at all, and the one gap that no
   amount of keeper stability closes.
5. **Do NOT re-do change (c).** It landed via #3964 and is byte-identical at
   HEAD. Verify the blob (`af34031c`) rather than re-porting it.
6. **Close the #4054 residual if you want belt-and-braces** — a fidelity-only
   re-check at HEAD (hash compare, **no solve**) confirms the exclusions were
   active in the NYISO capture. The captures are already cleared on code-state
   evidence; this is optional. **The nyiso-140 A/B question is separate and
   stays with its own lane.**
7. **Then, and only then, resume changes (a)–(e)** — and re-read the G2 leg list
   above, because *merged byte-green* is what the gate wants, not captures.
8. **Clear the golden-tier RED before claiming any byte-green result.** A tier
   that cannot provision `data/clean` cannot prove byte-identity of anything.
