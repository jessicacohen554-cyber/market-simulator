# Model Audit Program — Director Status Board (2026-08)

> # ⛔ PROGRAM PARKED AT G1 BY OWNER DECISION — WS3/PERF PAUSED FOR CALIBRATION
>
> **This is not drift and nothing below is late.** The owner paused WS3/PERF-B so
> the calibration program can run. *PERF-B merged byte-green* is a G2
> precondition, so **G2 cannot be declared while WS3 is paused** and the program
> sits at **G1**. **DOCS-B** (G2) and **AUDIT-B** (G3) are **waiting by design**;
> **SITE-A** (G3) likewise. The FFR desk's **Q.2 supersession battery**, which
> commissions at G2 (`ffr-owner-sitting-2026-08-02.md` AS.6), **does not fire.**
> Whoever un-parks the program starts at the **RESTART CHECKLIST** at the bottom
> of this board, not at change (a).
>
> ### 🔴 NEW AT v10 — THE LARGEST CYCLE OF THE PROGRAM. Four of six keepers moved; **not one stage-0 golden now matches its keeper.**
>
> v9 retracted the v8 restart window because the ISO lanes had re-armed. **They
> did not merely stay armed — they ran flat out.** Fifty-five lane PRs merged in
> roughly twenty-four hours, **ERCOT promoted twice**, **MISO promoted four
> times**, **NYISO promoted three times**, and the stage-0 golden count went from
> 4 stale / 1 current to **5 stale / 0 current**. The park holds. The freeze is
> more expensive today than at v9, and the evidence that WS3 cannot converge
> without one is now arithmetic rather than argument.
>
> **WS5 moved off zero for the first time** — Job 1 (site factual repair) is
> merged, and it found that the public site had been asserting a **locked-test
> holdout result that does not exist** for two weeks after the record corrected
> it.

> **STATUS: PARKED AT G1** — live rollup maintained by the program-director
> session, updated on each owner "refresh". Canonical program definition:
> `docs/model-audit-release-plan-2026-08.md` (its §8 ledger is the durable event
> record; this board is the at-a-glance state). Completion figures are the
> director's estimate against each workstream's full DoD (A+B halves).

**Snapshot (v10):** dispatch written against `b12ad140`; **this records lane
re-derived every figure live on 2026-08-20 at ~05:50 UTC against `origin/main`,
pinned at `e0c1f0e`** · **ZERO open PRs** (live) · **fifty-six PRs merged since
the v9 snapshot base `598554e`**: **#4108–#4163**, of which **#4112 is the v9
records lane itself** — so **55 PRs of lane work**, across **153 commits** since
the v9 board commit `17ed9b9`. **`main` advanced twice during this read**
(`e90b916` → `66ae225` → `e0c1f0e`); the board is pinned at the last of those and
says so rather than pretending to a stationary HEAD.

**Headline: the program's biggest cycle, and the dispatch's own keeper list was
stale before it was written.** Four of six keepers moved — but **two moved past
the runs the dispatch names**: ERCOT is at **ercot-223**, not ercot-221, and MISO
is at **miso-172**, not miso-170-sitegrain. The parity gate is **RED at 8 dead
dirs, not 9**, and its repair lane **is running right now**, contrary to the
dispatch's "never launched". Two things the cycle *confirms* rather than
corrects: **the golden tier still has had no CI run since the red**, and **no ISO
has ever spent a locked-test year**. The session-read deviation **stays closed**.

## What moved this cycle

**Read the corrections first — the dispatch's cycle facts were written before the
last three keeper promotions landed.**

1. **🔴 CORRECTION — the cycle is BIGGER than the dispatch says, at both ends.**
   The dispatch reports "~42 PRs (#4116–#4157)". Measured at the pin: **#4108
   through #4163, fifty-six PRs**, of which **#4112 is v9's own records lane**,
   leaving **55 PRs of lane work** over **153 commits**. The dispatch's window
   misses eight PRs below its floor and six above its ceiling. It is still the
   right headline — *the largest cycle of the program* — just under-measured.

2. **🔴 CORRECTION — the ERCOT keeper is `2026-08-20-ercot223-arm-eventrelease`,
   not the ercot-221 the dispatch names. ERCOT PROMOTED TWICE.** ercot-221 (the
   adaptive-expectation storage offer) *was* promoted on 2026-08-19 — on the
   owner's standing structural standard **over** the lane's own pre-registered
   mechanical verdict of **REJECTED-AS-ARMED on G-SHED** (one new 17.9 MW shed
   hour at 2024 h3066, a real storm hour with actual RT $2,451; the
   ercot-188/213/215 pattern, **fourth** application, both records standing).
   **ercot-223 then repaired exactly that failing gate and superseded it on
   2026-08-20.** The delta is `ercot_adaptive_event_release`: an
   **event-realized release guard** that masks the pass-2 floor at in-window
   hours whose pass-1 settle basis already clears the existing **$1,000** event
   constant — **zero new numeric constants**
   (`PRECOMMIT-ercot223-event-release-guard-2026-08-19.md`). **Every
   pre-registered gate PASSES, including G-SHED tightened to zero NEW shed**
   against the original 0/1/0; the arm's 2024 shed set returns to {3067}. The
   market story is a claim about *when* the fleet releases, not the social cost
   of its stored energy — on the real May-8-2024 storm evening the fleet
   discharged into the event. Fail set unchanged: **C3a-2023 and C3b-2023**;
   determination stays **NOT-YET**. An `ercot-222` cross-year-seeded-expectation
   Phase-0 lane also ran and archived between them.

3. **🔴 CORRECTION — the MISO keeper is `2026-08-20-miso-172-p25mw`, not
   miso-170-sitegrain. MISO PROMOTED FOUR TIMES IN THIS CYCLE.** The chain, each
   link a single delta with its own zero-delta control:
   - **miso-169 → `2026-08-19-miso-169-online-gated`** — the escalated promotion
     v9 recorded as *pending two owner answers* was **taken by explicit owner
     direction**. One field, `miso_reserve_online_gated=true`; reserve **supply**
     restricted to synchronised capacity for the products MISO defines as
     synchronised; **zero free parameters**; control reproduces the committed
     keeper bit-identically (max|diff| = 0).
   - **miso-170 → `-membership`** — promoted over the lane's **own** mechanical
     REJECTED-AS-ARMED, both records standing; but **the structure-over-gates
     clause was NOT needed**: at record grain the arm differs in **exactly one of
     67 records and it is an improvement** (C8 ST_GAS 2024 FAIL → PASS, the first
     MISO year ever to clear C8's grounded-above-budget leg). It executes the
     miso-169 SS5 ask on its second branch — **the nyiso-143 D-4 conduct rider is
     RIGHT and the floors were WRONG** — and is the third and last mechanism in
     the lay-up-membership family (nyiso-140 → nyiso-144 → miso-170), rule 19
     `[R-ONE-MECH]` one mechanism later. D-4 conduct failures **18 → 3, zero
     new**; ~**2.34 TWh** of three-year forcing removed from plants whose own
     meter reads zero.
   - **miso-170b → `-sitegrain`** (same day) — **the delta is DATA, not
     mechanism**: the same 15-plant lay-up census re-stamped at **SITE** grain, so
     a floor reaches every limb a site's tranches occupy, not just its majority
     class. Repairs the predecessor's K-1 residual (Burlington IA's CT tranches
     floored 777/763 unit-hours while the site metered dark in **98.7 %/91.8 %**
     of exactly those binding hours — rule 17 `[R-FLOOR-WINDOW]`). C8-2025 FAIL →
     PASS, joining 2024.
   - **miso-172 → `-p25mw`** — **on the arm's own pre-registered gates, every gate
     passing, no owner override needed.** A **dropped-basis repair with zero free
     parameters**: the frozen deriver measures `p25_cf` as a fraction of
     *available* capacity, and `campd_bins.thermal_tranche_p25_level` rebuilt the
     runtime floor as `p25_cf × nameplate`, **dropping the `avail_mult` it had
     been divided by** — so every plant with a deep availability derate was
     over-floored by `1/avail_mult`. The replacement takes the same percentile of
     the same online sample **directly in MW**, via a script that *imports* the
     frozen deriver rather than restating it (rule 23 `[R-FROZEN-DERIVE]`
     satisfied, frozen deriver untouched, zero bytes). Rule 14 `[R-ACCURATE]`
     governs. Determination stays **NOT-YET** (C3a-2025 + C8-2023, the latter now
     alone, on the 1402 pooled-window defect whose per-year `online_frac`
     successor is already named and **running**).

4. **🟢 CONFIRMED — the NYISO keeper is `2026-08-19-nyiso-146c-state-scoped`, as
   the dispatch says.** NYISO promoted **three times** across the 146 family
   (146 → 146b → 146c), on top of the 143 → 144 pair v9 recorded — **five NYISO
   promotions in two days.** 146c is the **online-hours LSL state floor,
   duty-scoped by the measured run-length gap**: two fields over nyiso-144
   (`nyiso_gas_bridge_online_hours`, the ercot141 `floor_online_hours` detector
   leg scoped to gas_cc, plus the state-scoping leg), carrying the committed-state
   inflexibility of a synchronised CC at its measured min stable load.
   Determination **CALIBRATED**; `complete` re-keyed to 146c (rule 22 D-5(b)).
   *Observation for the NYISO lane, not repaired here:* commit `41c5bc6` changed
   **only** the shard's `keeper` field, so `promotion_note`, `determination_note`
   and `superseded` in `keepers/NYISO.json` still describe **nyiso-144**. The
   `keeper` field and the `calibration-complete` entry are both correct; it is the
   prose around them that lags. Keeper shards are out of this lane's scope.

5. **🔴 CORRECTION + DIRECTOR MISS — WS6 parity is RED at EIGHT dead dirs, not
   nine, and the repair lane IS LAUNCHED.** Two halves, and the director's own
   record is wrong on both:
   - **The count is 8, and it is now entirely NYISO.** Run at the pin,
     `check_registry_payload_parity.py` **exits 1** on
     `nyiso144_arm_recipe`, `nyiso146_arm_recipe`, `nyiso146b_armB_recipe`,
     `nyiso146b_armC_recipe`, `nyiso146c_armB2_recipe`, `nyiso147_armA_recipe`,
     `nyiso147_armB_recipe`, `nyiso147_control`. The dispatch's list names
     `miso172_control` and it is **not flagged** — it registered. v9's
     `ercot221_control_A` **cleared itself**, exactly as v9 predicted it would
     when the ercot-221 A/B registered. So the trajectory is **2 → 9 → 8**: not a
     monotone worsening, but a queue the NYISO lane is filling faster than
     registration drains it.
   - **The dispatch says the repair prompt "was issued on 2026-08-19 and NEVER
     LAUNCHED". That is false at this read.** The live session list shows
     `session_01AF4gAXqqBa235VGTuRDdSM`, **"WS6 parity repair: nine dead bundle
     dirs"**, branch `claude/ws6-parity-repair-hvmt54`, **RUNNING** at
     2026-08-20T05:49:01Z with task summary *"Comparing recipe configs to the arms
     they produced"*. Its own title says **nine**, which dates its launch to when
     the count was 9. **The miss is real but narrower than stated:** the prompt
     was not lost, it was launched late, after the count had more than
     quadrupled. It has **not pushed a branch** (`git ls-remote` shows no
     `ws6-parity-repair` ref), so nothing has landed yet. **Do not re-issue it —
     it is in flight.** What the owner still owes is nothing; what the *director*
     owes is checking the live roster before declaring a lane unlaunched.

6. **🟢 WS5 MOVED OFF ZERO — Job 1 COMPLETE and merged (#4120 + #4121; commits
   `5f4a6af`, `cd8293b`; record `docs/FINDING-site-facts-repair-2026-08-19.md`,
   321 lines).** Fifteen repairs across the codebase-site: **twelve ordinary
   staleness, three governance-grade.** Every number was re-derived from
   `src/`, `scripts/` or committed data — not copy-edited. **The worst one, in
   full, because it is the kind of defect this program exists to catch:**

   > `model-validity.html` §4 asserted that NEISO *"carries a complete marker …
   > **its 2019 + H1-2026 one-shot was scored once with the then-frozen
   > `neiso-53` config and stands**."*

   **It had not been scored. No ISO has ever spent a locked-test year.** The
   `final` block carries only its `_note`. This was **not a new discovery** — it
   is precisely the claim **owner decision D-23 corrected on the record on
   2026-08-06**, and the site never followed for **two weeks**. A reader of the
   public site would have concluded the model held a **certified out-of-sample
   result that does not exist**, on the one page whose entire subject is
   out-of-sample discipline. Figure MV2's caption carried the same claim
   independently. Repaired by **stating the correction explicitly** rather than
   silently swapping the text. The other two governance-grade items: **the
   holdout spend freeze was invisible site-wide** (`active: true`, checked
   *before* the marker, failing closed — a reader could reasonably have concluded
   the three `complete` ISOs were free to spend 2022 today; they are not), and
   **marker state was wrong on two pages in both directions** (`model-validity`
   listed NEISO only and pilled PJM/NYISO as "quarantined";
   `calibration-rubric` said NYISO *"carries a frontier designation but no
   complete marker"* — **both halves backwards**). Among the twelve ordinary
   repairs, two worth naming: the landing page advertised **seven ISOs including
   SPP** — there are six, and **SPP appears in the codebase only as a MISO seam
   comment for a wheeled external contract path and in `paths.py` where "SPP"
   means *Settlement Point Price*, a different noun entirely** — and **"50+
   transmission links", which was never true at any point (46)**. Also repaired:
   P2 presented as a live third solve on four pages, the retired ablation twin
   presented as a live keeper obligation, a topology JSON that **rendered a
   network the model does not have**, and the rubric page pinned at v3.1 (now
   3.4). **SITE-A (plan §7.6) remains gated at G3 and NOT started** — Job 1 was
   explicitly scoped as pre-G3 factual repair, not restructure.

7. **🟡 CONFIRMED, NOT CORRECTED — GOLDEN-TIER CI STILL HAS NO RUN SINCE THE
   RED.** Live `actions_list` on `golden-data-tier.yml` at this read returns
   **five runs, unchanged for a third consecutive cycle**: latest is still the
   red **`31999181985`** (schedule, 2026-08-17T05:48:08Z, main); last green is
   still **`31913648051`** (workflow_dispatch, 2026-08-15T23:01:19Z, branch
   `claude/golden-tier-emissions-oom-03qlck`). The #4071 fix is **not** in
   question — its finding records a full local four-step job replay, all green.
   **The CI proof is.** Cadence: the red *was* the Monday cron; today is
   **Thursday 2026-08-20**, so the next scheduled firing is **Monday 2026-08-24
   05:37 UTC** — four days out.
   *Numbering corrected:* the dispatch calls this the **eighth** cycle as top
   standing item. **v9 (`17ed9b9`) recorded it as the sixth**, and v10 is the
   next cycle, so it is the **SEVENTH**. The same +2 drift applies to the
   decision-1 ack. Corrected here rather than carried, per this board's own
   standing instruction that HEAD and the prior record win over a dispatch.

8. **STAGE-0 GOLDENS CROSSED ZERO.** Recomputed at the pin — **5 STALE / 0
   CURRENT / 1 NO-GOLDEN**, against 4/1/1 at both v8 and v9. MISO was the last
   current golden and lost it to the miso-169→170→170b→172 chain. Detail and the
   structural reading below.

## Keeper table (read from `frontend/data/backcast/keepers/<ISO>.json` at `e0c1f0e`)

| ISO | Designated keeper | Determination | This cycle |
|-----|-------------------|---------------|------------|
| ERCOT | **`2026-08-20-ercot223-arm-eventrelease`** | `NOT-YET` | **MOVED TWICE — and past what the dispatch names.** ercot-221 promoted 2026-08-19 on the owner's standing structural standard **over** a pre-registered **REJECTED-AS-ARMED on G-SHED** (one manufactured 17.9 MW shed at 2024 h3066; ercot-188/213/215 pattern, **fourth** application, both records standing). **ercot-223 (2026-08-20) repaired that exact gate and superseded it**: `ercot_adaptive_event_release` masks the pass-2 floor where the pass-1 settle basis already clears the existing **$1,000** event constant — **zero new numeric constants**, **every gate PASSES** incl. G-SHED tightened to **zero NEW shed**, 2024 shed set back to {3067}. Fail set unchanged {C3a-2023, C3b-2023}. ercot-222 (cross-year-seeded expectation, Phase-0) ran and archived between them; **ercot-224 opened 2026-08-20** (#4163, read-only Phase-0 precommit: the item-8 CME/NYMEX basis-swap reopen screen) |
| CAISO | `2026-08-17-caiso-200-h1-memberpanel` | `NOT-YET` | **UNMOVED — and the lane deliberately did not move it.** caiso-205 A/B'd the **adaptive-expectation storage offer** (the ERCOT ercot-221 mechanism, transferred as a rule 26 `[R-MECH-MATRIX]` candidate with **its own CAISO-derived constants** — half-life 30 d, beta **0.5945**, $200 event, h18-21 PT) and **registered it as a PROBE, armed-and-inert, explicitly NOT a keeper**; its control G-REPRO'd **9/9 committed keeper hourly sidecars sha256-identical**. caiso-206 confirmed rest; **caiso-208 (#4162) re-verified Branch A at rest and repaired a stale v3.3 gate posture on both matrix surfaces**. Determination holds **NOT-YET** on the lone C3a `price_mean` FAIL |
| PJM | `2026-08-15-pjm-162-inputclock` | `CALIBRATED` | **Unmoved, and untouched for a second consecutive cycle** — no PJM calibration lane ran. A **PJM T1-H hindcast 2021–2025** lane ran and archived (forecast family; separate dashboard namespace, plan §7.5). Still `final`-NOT-YET on the merits (#4083); 2020 rung not data-ready |
| NYISO | **`2026-08-19-nyiso-146c-state-scoped`** | `CALIBRATED` | **PROMOTED THREE TIMES THIS CYCLE (146 → 146b → 146c), five times in two days counting v9's 143 → 144.** 146c is the **online-hours LSL state floor, duty-scoped by the measured run-length gap** — two fields over nyiso-144, carrying a synchronised CC's committed-state inflexibility at its measured min stable load (the DAM commits for operating days, not for the LP's hourly bid-cost re-decision). `complete` **re-keyed to 146c** with determination re-verified from committed artifacts, no solve (rule 22 D-5(b)). **NYISO is also the sole source of all 8 parity-RED bundle dirs** |
| NEISO | `2026-08-17-neiso-99-joint-p1` | `CALIBRATED` | **Unmoved and untouched.** A **NEISO T1-H hindcast 2021–2025** lane ran and archived (forecast family, separate namespace). **EIA-923 2025 final vintage STILL NOT LANDED** — re-checked, unchanged |
| MISO | **`2026-08-20-miso-172-p25mw`** | `NOT-YET` | **FOUR PROMOTIONS — the most any ISO has taken in one cycle.** miso-169 (the escalation v9 recorded as *pending two owner answers* — **taken by explicit owner direction**) → miso-170-membership (**one of 67 records differs and it is an improvement**; D-4 conduct failures **18 → 3, zero new**; ~**2.34 TWh** of forcing removed from plants metering zero) → miso-170-sitegrain (**data, not mechanism**: the census re-stamped at SITE grain; Burlington's CTs floored 777/763 unit-hours while the site metered dark in **98.7 %** of exactly those hours) → **miso-172-p25mw**, a **dropped-basis repair with zero free parameters** — `p25_cf × nameplate` had **dropped the `avail_mult` it was divided by**, over-flooring every deeply-derated plant by `1/avail_mult`. **Promoted on its own pre-registered gates, all passing, no override.** C8 now fails **2023 alone**; its per-year `online_frac` successor (miso-173) is **running at this read** |

**Markers at HEAD (`e0c1f0e`, re-read this cycle):** `complete` =
**{NEISO, NYISO, PJM}** · **`final` = empty (`_note` only)** · **`holdout-freeze.json`
`active: true`**, and it outranks both marker blocks. **NO ISO HAS EVER SPENT A
LOCKED-TEST YEAR** — verified exhaustively rather than asserted: across all
**52** registered sidecars (34 at v9; **18 added this cycle**) the solve-year
histogram is **{2022: 2, 2023: 50, 2024: 50, 2025: 50}**, and the only two
out-of-training registrations are the authorized **2022 validation touchpoints**
(PJM `2026-08-05-pjm-2022-touchpoint`, NEISO
`2026-08-06-neiso-2022-corrected-basis`). **No 2019, no H1-2026, anywhere**
([R-HOLDOUT]).
**This line is re-verified and republished every cycle for a reason, and this
cycle supplied it:** WS5 Job 1 found the public site asserting the exact
opposite — that NEISO's locked-test one-shot *had been scored and stood* — for a
full two weeks after owner decision D-23 corrected it on the record (§ item 6).
A governance fact that is true in the JSON and false on the site is not a fact
the program can claim. **Restate it, re-derive it, and check where else it is
published.**
Determinations: **PJM, NYISO, NEISO `CALIBRATED`** · **ERCOT, CAISO, MISO
`NOT-YET`** — the CALIBRATED set is still exactly the `complete`-marker set.

## Workstream rollup

| WS | State | Completion | Blockers / next |
|----|-------|------------|-----------------|
| WS1 `AUDIT` | AUDIT-A **completed** (#3991). Rows **O8 CLOSED**, **O5 CLOSED** (#4072, re-verified **stronger** at #4085 on a newer keeper set, residual third replay path **gated + tested**), **O4 re-measured and STILL OPEN** (#4085 — disposition act only, owner card, recommendation (A)) | **In progress ~91%** | **AUDIT-B gated at G3 — waiting by design.** Rows **O4, O6, O7** open |
| WS2 `DEBUG` | **COMPLETED** — DEBUG-A ✓, DEBUG-B ✓, pjm-162 promoted, sibling-import residue retired, landing-verify green on merged main. Row B1 annotated **STALE** (#4085), no code change | **Completed** | none; no DEBUG-C continuation chartered |
| WS3 `PERF` | PERF-A ✓. **PERF-B PAUSED BY OWNER.** Stage-0: **5 of 6 ISOs captured** (ERCOT #4033, NEISO #4041, NYISO #4050, CAISO #4058, MISO #4060; **PJM never captured**). Changes: **(c) landed via #3964**, **(d)+(e) merged via #4067**, **(a)/(b) unstarted**. Close-out note + wallclock baseline landed (#4075). **`results/regression-goldens/` is byte-unmoved this cycle** — verified, not assumed | **Paused ~74%** | **Paused, not blocked. The restart precondition is FURTHER away than at v9 and the case for it is now arithmetic: 0 of 6 goldens match their keeper.** On restart: freeze calibration, then re-verify every golden — RESTART CHECKLIST |
| WS4 `DOCS` | DOCS-A **completed** (#3999 + #4005); DOCS-B held | **In progress ~60%** | **DOCS-B gated at G2 — waiting by design** |
| WS5 `SITE` | **OFF ZERO. Job 1 (site factual repair, pre-G3) COMPLETED and merged** — #4120 + #4121, record `docs/FINDING-site-facts-repair-2026-08-19.md`. 15 repairs over 19 site files; **3 governance-grade**, incl. a false locked-test-spent claim live for two weeks (§ item 6). Job 2 = **SITE-A**, not started | **Job 1 completed · Job 2 not started** | **SITE-A gated at **G3** — waiting by design.** Job 1 was scoped pre-G3 precisely because false statements should not wait on a gate |
| WS6 `BLOAT` | Prunes B-1..B-8 merged; **BLOAT-2 CLOSED** (#4032); **BLOAT-3 ADJUDICATED** (#4031) and **EXECUTED** (BLOAT-S2 #4047, −444.5 MiB / 144 files at tip). **The chartered work stays completed — the parity GATE is RED for a second consecutive cycle** | **Completed (charter) · gate RED** | **RED, 8 dead dirs, ALL NYISO** (`nyiso144_arm_recipe`, `nyiso146_arm_recipe`, `nyiso146b_armB/armC_recipe`, `nyiso146c_armB2_recipe`, `nyiso147_armA/armB_recipe`, `nyiso147_control`). v9's `ercot221_control_A` **cleared itself** on registration, as v9 predicted; `miso172_control` **registered** and is not flagged. **Trajectory 2 → 9 → 8.** **The repair lane IS RUNNING** (`claude/ws6-parity-repair-hvmt54`, live roster) — **do not re-issue**; it has pushed no branch yet |
| — `GOLDEN-TIER-FIX` | **COMPLETED and independently verified** (#4014). First scheduled cron came back **RED**, **diagnosed + fixed same-day** (#4071), **deliverables verified by a full local four-step job replay, all green** | **Completed** | **the fix is not in question. The CI proof is: STILL NO RUN since the red**, re-read live this cycle (5 runs total, unchanged; latest `31999181985` red; last green `31913648051`). Next cron **Monday 2026-08-24 05:37 UTC**. One `workflow_dispatch` settles it — **top standing open item, seventh cycle** |

**WS1–WS4 are byte-unmoved this cycle; WS5 moved and WS6's gate changed.**
Verified rather than assumed: across all 56 merges the only WS-owned documents
touched are this board, the plan's §8 ledger, and — for the first time — the
**19 `docs/codebase-site/` files** of WS5 Job 1. **No `.github/workflows/` file
changed**, and **no `results/regression-goldens/` file changed**. Rows **O4, O6,
O7** remain the open audit rows, all three gated at G3 or awaiting an owner act.

## Stage-0 golden staleness (recomputed at `e0c1f0e`)

Re-derived at HEAD from `frontend/data/backcast/keepers/<ISO>.json` and
`results/regression-goldens/perfb-stage0/manifest.json` (`git_sha` **`af1ccb6`**,
`git_dirty: false`, unchanged this cycle) — **not copied from v9.**

| ISO | Golden captured against | Designated keeper at `e0c1f0e` | Verdict |
|-----|-------------------------|--------------------------------|---------|
| ERCOT | `2026-08-15-ercot204-rule26-delete` (#4033) | `2026-08-20-ercot223-arm-eventrelease` | **STALE — keeper moved four times since capture** |
| NEISO | `2026-08-14-neiso-93-envelope` (#4041) | `2026-08-17-neiso-99-joint-p1` | **STALE** — the re-stamp-not-re-solve shortcut was established for **neiso-97 only**; re-establish before relying on it |
| CAISO | `2026-08-16-caiso-197-w2-r5` (#4058) | `2026-08-17-caiso-200-h1-memberpanel` | **STALE** — unchanged from v9; the only ISO whose gap did not widen |
| MISO | `2026-08-16-miso-160-wefor-shape` (#4060) | `2026-08-20-miso-172-p25mw` | **🔴 STALE — LOST THIS CYCLE.** Four promotions past its capture |
| NYISO | `2026-08-16-nyiso-140-layup-exclusion` (#4050) | `2026-08-19-nyiso-146c-state-scoped` | **STALE — the worst gap on the board.** Five promotions past its capture |
| PJM | — | `2026-08-15-pjm-162-inputclock` | **NO GOLDEN — never captured** |

**Count: 5 stale / 0 current / 1 no-golden** — against **4 / 1 / 1** at both v8
and v9.

**🔴 THE STRUCTURAL POINT, AND THE BOARD SHOULD SAY IT PLAINLY: not one stage-0
golden now matches its keeper.** This is the **sixth consecutive cycle in which
keepers moved faster than captures could complete**, and it is the first in which
the count reached zero. That is no longer a scheduling accident, and it should
stop being reported as one:

- **Five of the six captures were paid for and are now unusable as byte-baselines.**
  The sixth (PJM) was never taken. The tier's *effective* coverage of the current
  model is **0/6**.
- **The failure is not that captures are slow — it is that they are chasing a
  moving target.** MISO held the last current golden for four days and lost it to
  a **four-link promotion chain in a single cycle**. NYISO staled its own golden
  twice in one day at v9 and three more times at v10. No plausible capture
  cadence outruns that.
- **Therefore WS3 cannot converge without a declared calibration freeze.** Not
  "would benefit from" — *cannot*. Every golden captured before a freeze is
  staled by the next promotion, and the promotions are not slowing: this cycle
  produced **nine keeper promotions across three ISOs**. G2's leg 1 (*PERF-B
  merged byte-green*) is unreachable by effort alone.
- **The corollary the owner should weigh:** the freeze is expensive *because* the
  lanes are productive. Four keepers moved this cycle and most of the moves were
  real structural repairs with zero free parameters (miso-172's dropped
  `avail_mult`, miso-170b's site-grain census, ercot-223's gate repair). **The
  choice is not freeze-versus-drift; it is which of two goods to buy first.** The
  director's recommendation is in owner-queue rank 5 and it has changed.

## Gates

- **G0** adopted ✓ (2026-08-13) · **G1** DECLARED ✓ (2026-08-16, #4006).
- **G2 — UNREACHABLE while WS3 is paused.** Leg 1 is *PERF-B merged byte-green*,
  PERF-B is paused by owner decision, and no other leg substitutes. The legs:
  1. **PERF-B merged byte-green** — **worse than at v9**: 5 of 6 captured and
     **all 5 now stale**, (c)/(d)/(e) merged, (a)/(b) unstarted. Byte-green needs
     goldens; it cannot even be *claimed* while the golden tier has no green CI
     run.
  2. **One completed fast-tier-green `ci.yml` run** — the sparse block landed
     (#3964, runner-validated at 31873178938: 6838 passed / 31 skipped).
  3. **A keeper freeze** — **owner call, outstanding across eight director
     cycles, and its cost is now at its HIGHEST.** Nine promotions across three
     ISOs landed this cycle; at this pin **three calibration lanes are running**
     (miso-173, ercot-224, plus a NYISO upstate-price lane idle-with-work) and a
     WS6 repair lane is mid-flight. There is no quiet window in view.
  4. **Branch-protection flip** — owner action, memo ready.

  On declaration the PM notifies the FFR desk (Q.2 battery).
- **G3** — unchanged: after G2, **DOCS-B** + the **BLOAT leg**. BLOAT's verdict
  and its chartered execution are satisfied (#4031 + #4047); **its parity gate is
  RED again** and is the one G3 leg that regressed. The golden-tier proof leg is
  satisfied by #4014 + the green dispatch.
- **G4** — unchanged: SITE-A + AUDIT-B. **WS5 Job 1 is not a G4 leg** — it was
  deliberately scoped pre-G3 as factual repair, and closing it does not advance
  G4.

## Watch

- **🟡 GOLDEN-TIER CI PROOF — seventh cycle, and unchanged for three reads.**
  Fix merged (#4071) and verified by full local job replay; **no CI run since the
  red `31999181985`**, re-read live. Until one runs, BLOAT-S2's D3 leg and every
  byte-green claim are unprovable. Next cron **Monday 2026-08-24 05:37 UTC** (four
  days out). One `workflow_dispatch` settles it.
- **🔴 STAGE-0 COVERAGE HIT ZERO.** 0 of 6 goldens match their keeper. See the
  structural point above — this is the single strongest piece of evidence the
  program has produced for the freeze, and it arrived as arithmetic rather than
  argument.
- **🔴 BLOAT-2 parity RED for a second cycle, now ALL NYISO.** 8 dead bundle
  dirs, every one from the 144/146/147 promotion chain. **The repair lane is
  RUNNING** (`claude/ws6-parity-repair-hvmt54`) and has pushed nothing yet —
  **do not re-issue it.** Standing structural note: **the NYISO lane is
  generating unregistered arm bundles faster than it registers them**, which is
  the actual root cause and is not fixed by one prune pass.
- **🟠 THE UNCITED `RHO_CLIP` 0.5 FLOOR — PREPARED, WAITING, AND STILL
  UNRULED.** Verified at the pin: `src/market_sim/data/online_reserve_rho.py:87`
  still reads `RHO_CLIP: tuple[float, float] = (0.5, 4.0)`. The work is **done** —
  nyiso-145 produced both findings
  (`FINDING-nyiso143-online-rho-unidentified`,
  `FINDING-nyiso144-downstate-scarcity-and-rho`), and the module's own comment
  block now states the defect in plain terms: **both measured NYISO values fall
  BELOW the floor** (`incity_obligation` 0.3014, `nyc_spin` 0.2011), so
  `rho_used` returns **the floor, not the measurement**. MISO's measured rho is
  **0.1764** — also below. **MISO therefore dispatches its keeper on a clipped-up
  rho whose floor carries no citation**, a live rule 5 `[R-NO-MAGIC]` exposure
  inside a mechanism that has now been promoted **four times** on top of it. The
  code itself says the resolution is an owner call, not a session's. **The
  re-solve is one `--set`.**
- **🔴 THE CROSS-ISO GOVERNANCE COLLISION — RESOLVED IN SUBSTANCE, worth
  recording as closed-by-execution.** v9 raised the nyiso-143 D-4 per-unit
  conduct rider as C8-FAILing any regenerated MISO artifact. **miso-170 answered
  it on its second branch — the rider is RIGHT and the floors were WRONG** — and
  the repair has since carried through miso-170b and miso-172, taking D-4 conduct
  failures **18 → 3 with zero new**. The rule 25 `[R-ISO-SCOPE]` *question* (a
  scorer-side change made in one ISO's lane reaching another's committed
  diagnostics) was never formally adjudicated; it was **overtaken by the target
  ISO agreeing with it**. Worth an owner line so the precedent is explicit rather
  than implied.
- **DURABLE LESSON (unchanged, and the reason the golden item matters):**
  `golden-data-tier.yml` is the **ONLY** workflow that runs
  `scripts/regenerate_clean.py`, so **any curation-time defect under
  `scripts/data/curate_*.py` has NO pre-merge signal** — invisible to every PR
  check, surfacing only on the weekly cron, and compounded by `data/clean` being
  derived and gitignored. **Treat curate-script changes as unguarded.**
- **🟠 NEW — PUBLISHED GOVERNANCE FACTS DRIFT FROM THE JSON THAT HOLDS THEM.**
  WS5 Job 1's finding is not only a site bug: it is evidence that **the marker
  state, the freeze state and the holdout tier rules are published in more places
  than the program was checking**. The site was wrong for two weeks about
  something CLAUDE.md, `calibration-complete.json` and `holdout-freeze.json` all
  had right. The finding also flags **a live disagreement inside committed
  governance data**: `holdout-freeze.json`'s own prose still says intake is
  permitted *"under session-logged owner authorization"*, which the **2026-08-06
  amendment reversed** (*what is held out is the score, never the data or the
  architecture*). **Not repaired by WS5** — it is governance data, not site
  content — and it belongs to a governance lane.
- **🟠 #4054 / nyiso-140 null-treatment question — STILL OPEN, NEVER ADJUDICATED,
  and now further out of reach.** The NYISO keeper has moved **five promotions**
  past the captured nyiso-140 config. Any claim that re-checking it "costs a
  fidelity read, not a solve" must be **re-derived**, not inherited.
- **🟢 CARRIED CLOSED — the ≥24 GB MISO container ask** (retired at v9 on
  miso-169's measurement, 13.95 → 12.40 GB peak) has stayed retired across four
  further MISO promotions on the 15 GB box.

## Owner queue at cycle end

Carried from v9, **re-ordered and re-verified at `e0c1f0e`**. Two v9 items are
retired: rank 1 (*say "go" on the WS6 lane*) is **retired as launched — the lane
is running**, and rank 2's D-4 conduct rider half is **retired as
closed-by-execution** (miso-170 agreed with it). Its `RHO_CLIP` half survives and
is promoted.

0. **🔴 GOLDEN-TIER PROOF-OF-FIX `workflow_dispatch`** — the #4071 fix is merged
   and locally replayed green; the tier's latest CI run is still the red one,
   re-read live for a third consecutive cycle. **Seventh cycle** (the dispatch's
   "eighth" is corrected — v9 recorded the sixth). Billed minutes, so the owner's
   call; the passive alternative is **Monday 2026-08-24 05:37 UTC**.
1. **🔴 THE `RHO_CLIP` 0.5-FLOOR RULING — PREPARED AND WAITING, and now the
   oldest piece of *finished* work on the board.** nyiso-145 did the work and
   filed both findings; the constant is **unchanged at
   `online_reserve_rho.py:87`**; MISO's measured rho is **0.1764** and is being
   clipped up to 0.5 with no citation, under a keeper that has been **promoted
   four times on top of it** (rule 5 `[R-NO-MAGIC]`). The code's own comment says
   resolving the band is an owner call. **The re-solve is one `--set`.** Nothing
   is blocked on investigation — only on a ruling.
2. **🔴 WS3 RESTART / CALIBRATION FREEZE — RE-SERVED, AND REFRAMED.** The
   director did **not** serve a restart option at v9, and this board judges that
   a mistake. **The freeze has been framed for eight cycles as a precondition to
   schedule around — something to declare once the lanes go quiet. That framing
   is wrong and this cycle proves it.** The lanes have not gone quiet in eight
   cycles; they have accelerated (nine promotions across three ISOs this cycle
   alone), and stage-0 coverage has fallen to **0 of 6**. **The freeze is not a
   cost imposed on WS3 by the calibration program — it is the only thing that
   makes WS3 finishable at all.** Waiting for a cheap window is not a strategy
   with a terminal state: every cycle spent waiting makes the freeze more
   expensive *and* destroys more captured goldens. **Recommendation: declare a
   scoped, time-boxed freeze — long enough to re-capture six goldens and land
   changes (a)/(b) — rather than an open-ended one.** That converts the question
   from *"when will the lanes stop?"* (never) to *"how many days of calibration
   are six goldens worth?"*, which is answerable.
3. **NEISO-100/101 keeper-candidate + EIA-923 2025 vintage.** neiso-101 closed
   the **data half** of `final` precondition #2 with zero tracked files modified;
   **the 2025 final vintage is re-checked and STILL NOT LANDED**, and one
   remaining item is explicitly **not** a data item. NEISO was untouched by
   calibration this cycle.
4. **Validation-freeze lift signature** — the **O4/O5 card**
   (`AUDIT-FOLLOWUP-o5-o4-2026-08-18.md` §2.4), recommendation **(A) close the
   charter with cause, lift the VALIDATION tier only, leave `final` empty**. The
   detector question is closed on evidence; "resolve the detector question" is
   not one of the choices. **Unmoved this cycle.**
5. **🟠 NEW — rule on the cross-ISO scorer-change precedent.** The nyiso-143 D-4
   conduct rider reached MISO's committed diagnostics and MISO **agreed with
   it** (miso-170). The outcome was good; the *mechanism* — a scorer-side change
   in one ISO's lane silently re-grading another ISO's artifacts — is the shape
   rule 25 `[R-ISO-SCOPE]` exists to prevent. **A one-line ruling** on whether
   that route is permitted-when-correct or requires a cross-ISO notice would set
   the precedent explicitly instead of by outcome.
6. **🟠 NEW — the `holdout-freeze.json` prose conflict.** Its text still says
   intake is permitted *"under session-logged owner authorization"*; the
   **2026-08-06 rule 22 amendment reversed that** (*what is held out is the
   score, never the data or the architecture*). Committed governance data
   disagreeing with the governing rule. Surfaced by WS5 Job 1, out of that lane's
   scope. **Cheapest correctness item on the board.**
7. **O6 — locked-test scheduling.** 2019 and H1-2026 are **touch-once** and **no
   ISO has ever spent one** — re-verified exhaustively at this pin across all
   **52** registered sidecars (year histogram {2022: 2, 2023: 50, 2024: 50,
   2025: 50}). `complete` = {NEISO, NYISO, PJM}; `final` holds only its `_note`;
   the freeze is `active: true` and outranks both. **Never let a lane spend one**;
   scheduling is the owner's alone. *This cycle supplied the reason the line is
   republished every time: the site claimed the opposite for two weeks.*
8. **O7 — ERCOT P0 bit-identity proof forfeited** (accept-and-document, or
   charter restoration).
9. **decision-1 ack** — warm-start closed-overtaken; **still unacked, seventh
   cycle** (the dispatch's "eighth" corrected against v9's "sixth"); a one-word
   ack retires it.
10. **caiso-199 NOT-YET determination** — carried. The CAISO lane produced a
    registered **probe** (caiso-205, armed-and-inert, explicitly not a keeper),
    a rest confirmation (caiso-206) and a matrix-posture repair (caiso-208, #4162)
    and **moved no keeper** — the most disciplined lane on the board this cycle.
11. **ercot-214 counterpart-decontamination lever** — carried; superseded in
    practice by the ercot215 promotion, which is the decontamination arm.
12. **RETIRED THIS CYCLE:** ~~"say go on the WS6 register/prune lane"~~
    (**LAUNCHED — the lane is running; do not re-issue**); ~~the nyiso-143 D-4
    conduct rider adjudication~~ (**closed by execution — miso-170 agreed with
    it**; the residual *precedent* question is re-entered at rank 5, which is a
    smaller thing).

## Session roster

> **🟢 LIVE READ — the deviation stays CLOSED, for a second consecutive cycle.**
> The dispatch pre-authorised a commit-trailer rebuild on the expectation that
> `list_sessions` would fail *"requires approval"* for a fourth straight cycle.
> **It did not fail. It returned 40 sessions** (`mine: true`, `has_more: true`).
> The dispatch's premise was already stale at v9, which recorded the deviation
> closed on a successful 30-session read; **v10 confirms it was not a one-off.**
> The fallback was not needed and no row below is trailer-rebuilt. Honest limit:
> the page is capped at 40 with `has_more: true`, so lanes older than
> 2026-08-15 fall outside it — none of this cycle's lanes do.

**Lanes active this cycle**, live status as read at ~05:50 UTC 2026-08-20:

| Lane | Session | Branch | Landings | Live state |
|------|---------|--------|----------|------------|
| **Records v10 (this lane)** | `session_01742S6hAxywEqz5LraeoRWy` | `claude/director-records-v10-2d9md2` | board v10 + §8 entry | RUNNING |
| **Program director** | `session_01FKuWvSm52VoT7nhffjQ3J3` | `main-fresh` | — | **IDLE** |
| **WS6 parity repair** | `session_01AF4gAXqqBa235VGTuRDdSM` | `claude/ws6-parity-repair-hvmt54` — **no remote ref yet** | none yet | **🟢 RUNNING** — *"Comparing recipe configs to the arms they produced"*. Title reads *"nine dead bundle dirs"*; **8 at this pin.** **The lane the dispatch calls never-launched** |
| MISO miso-173 | `session_017s7GidPQ6o57YXEM6tru4b` | `claude/miso-1402-seasonal-p25-v45gb8` — no remote ref yet | none yet | **RUNNING** — *"miso-173: swap armed, installing deps, reading docs"*. The named successor to miso-172's remaining C8-2023 failure |
| ERCOT ercot-224 | `session_01PHDYyW8Lfgz2BxTvq7aJRv` | `claude/ercot-224-calibration-ye2ivp` @ `d68a449` (**merged** #4163) | #4163 | **RUNNING** — *"precommit verified, reading CME delisting notice for HSC/Waha"* |
| CAISO caiso-208 | `session_01Hp1a2tCoiYVjpxcodrE6T1` | `claude/caiso-backcast-verify-o9ls2p` @ `79d3da3` (**merged** #4162) | #4162 | IDLE |
| NYISO upstate price | `session_01EbfG3BcFfkQAgXxHhh7uL1` | `claude/nyiso-upstate-price-2023-8mr558` — no remote ref yet | none yet | IDLE — *"NYISO 2023 upstate price level"* |
| MISO 1402 window successor | `session_014Uvbe17idaGwwA4WBaprm6` | `claude/miso-1402-window-online-frac-omld8m` | #4160 · #4161 | ARCHIVED |
| MISO miso-172 / p25 | (within the 1402 chain above) | — | #4159 and below | ARCHIVED |
| ERCOT ercot-223 | `session_01F2y2SwMbziBKj6uxDnEBNq` | `claude/ercot-223-keeper-shed-8iztwv` | ercot-223 promotion | ARCHIVED |
| ERCOT ercot-222 | `session_01GhwFqJ2v8ZSqGENAXEYQ8M` | `claude/ercot-222-cross-year-seed-44of8n` | Phase-0 | ARCHIVED |
| ERCOT ercot-221 | `session_0115rcLjfbtGgG4xnKdviREz` | `claude/ercot-221-adaptive-expectation-xwkpk2` | ercot-221 promotion | ARCHIVED |
| MISO miso-170 ST_GAS repair | `session_01KPjzWtLDzNXu27Yvu11asu` | `claude/miso-170-st-gas-repair-65ph5r` | #4113 | ARCHIVED |
| MISO 2025 pricing analysis | `session_014cQoBnp9tAMnnndn8pP3xw` | `claude/miso-2025-pricing-analysis-a4cby5` | — | ARCHIVED |
| MISO reserve decomposition | `session_01NbHuMN9kmWAtQF2p1ExK3X` | `claude/miso-reserve-decomposition-e4gsv9` | — | ARCHIVED |
| NYISO 146 / frontier re-assess | `session_01Ba2pz1dXNEJiPRkZW7taWq` | `claude/nyiso-frontier-complete-kwtujn` | 146-family | ARCHIVED |
| NYISO CC min-run per-plant | `session_013FamABdE7ypkeX9tANwxES` | `claude/nyiso-cc-min-run-per-plant-cwfin5` | 146-family | ARCHIVED |
| **WS5 site facts repair** | `session_017nPWrrLwKbcfqKiNqVQZYH` | `claude/site-facts-repair-f3tkm1` | **#4120 · #4121** | ARCHIVED — **WS5 Job 1** |
| CAISO caiso-205 adaptive | `session_01GRkRtgxjkxjVLr7REd2s1J` | `claude/caiso-adaptive-storage-offer-l4bx2t` | #4114 | ARCHIVED |
| CAISO caiso-205 charter | `session_01S8XVCuAG2qEjxtgnkUKJoP` | `claude/caiso-205-owner-charter-ct7g53` | — | ARCHIVED |
| CAISO caiso-206 rest | `session_012K3NW65VimDu4aq8B6aFtU` | `claude/caiso-206-rest-confirmation-lf1xvi` | — | ARCHIVED |
| CAISO RA capacity anchor (forecast) | `session_01QpTSRU3PDsTj4jTW5TqLXW` | `main` | — | ARCHIVED |
| NEISO T1-H hindcast (forecast) | `session_018zb9TfK1E9jrbVYhobrrRF` | `claude/neiso-hindcast-2021-2025-nldv41` | — | ARCHIVED |
| PJM T1-H hindcast (forecast) | `session_01BdTKsJvLVLL1PuZ2mePkJS` | `claude/pjm-hindcast-2021-2025-er2ocx` | — | ARCHIVED |
| Forecast runs cleanup | `session_01A29Gvw8g4JuBGHjGjAgge1` | `claude/forecast-runs-hindcast-calibration-n5soqe` | — | ARCHIVED |
| Records v9 | `session_015jiqUxjYAVkaZhTEijkRPG` | `claude/director-records-v9-x2upg1` | **#4112** | ARCHIVED |

**Live remote branches** (complete set at this pin, `git ls-remote --heads`):

| Branch | SHA | Read |
|--------|-----|------|
| `main` | `e0c1f0e` | tip (merge of #4163) |
| `claude/caiso-backcast-verify-o9ls2p` | `79d3da3` | **merged** (#4162); branch not deleted |
| `claude/ercot-224-calibration-ye2ivp` | `d68a449` | **merged** (#4163); branch not deleted |
| *(this lane's branch once it pushes)* | — | board v10 + §8 entry |

**ZERO genuinely unmerged remote branches** — both live branches are ancestors of
the pin, verified by `git merge-base --is-ancestor`. Note what this *hides*:
**three running lanes hold work on branches that do not exist on the remote yet**
(`ws6-parity-repair-hvmt54`, `miso-1402-seasonal-p25-v45gb8`,
`nyiso-upstate-price-2023-8mr558`). **A branch-only read of this program now
understates it** — v9's roster could be reconciled against `ls-remote`; v10's
cannot. The live session read is no longer a convenience, it is the only
instrument that sees in-flight work.

## Refresh protocol

On each owner "refresh", the director: (1) lists sessions + fetches fresh
`origin/main`, re-reads plan §8 and lane handoffs; (2) reports each workstream
as **not started / in progress with % / completed / pending blockers**;
(3) issues prompts for any lane whose gate has cleared, appends the §8 ledger
entry, and updates this board in the same pass.

**v9's lesson held and earned its keep.** *"A records lane that transcribes a
director read is a liability on a program whose lanes merge hourly."* At v10 the
dispatch was stale on **five** counts before it was read — the PR range at both
ends, the ERCOT keeper, the MISO keeper, the parity dead-dir count and list, and
the cycle numbering — and on one it was stale in the *opposite* direction from
what a records lane would expect: it reported a lane as **never launched** that
was **running at the moment of the read**. Keep the verify-against-HEAD
instruction in every records prompt.

**v10 adds two protocol amendments:**

- **🔴 CHECK THE LIVE SESSION ROSTER BEFORE DECLARING A LANE UNLAUNCHED.** The
  WS6 miss was not a stale fact — it was a fact that could only be checked with
  `list_sessions`, and the dispatch asserted it from branch state alone. **Branch
  state no longer sees in-flight work** (three running lanes have no remote ref
  at this pin). A "never launched" claim needs the roster, not `ls-remote`.
- **🔴 PIN THE READ AND SAY SO.** `main` advanced **twice during this read**
  (`e90b916` → `66ae225` → `e0c1f0e`, two merges landing mid-verification). At
  this merge rate no board is a snapshot of "HEAD" — it is a snapshot of a
  **named commit**. Every figure above is pinned at `e0c1f0e` and re-derived
  there after the second advance, not carried across it.

**Under the standing deviation, step (3)'s two write duties are dispatched to a
records lane rather than pushed by the director.** A refresh is not complete
until that lane has landed both files — and, per the v5→v6 gap, a dispatch that
is never launched leaves the board silently wrong. **Verify the landing before
declaring a cycle done.**

**While the program is parked, the refresh cycle is not the live instrument it
was.** A park-period refresh should confirm only (a) whether the golden tier is
proven green **in CI** after the #4071 fix, (b) whether the owner has ruled on
anything in the owner queue, and (c) whether the keeper freeze has been called —
that last one is the un-park trigger. **At v10, (a) is unchanged for a third
read, (b) is unchanged, and (c) has moved further out of reach — but the *case*
for it is now the strongest it has ever been** (§ stage-0, § owner-queue rank 2).

## RESTART CHECKLIST — for whoever un-parks the program

**Do these in order. Do not start at change (a).**

1. **FREEZE CALIBRATION FIRST.** The precondition, not a nicety — the owner must
   declare it and no lane can. Until it holds, every golden captured can be
   staled by the next promotion, which is exactly how stage-0 failed to converge
   across eight cycles and how its effective coverage reached **zero** at v10.
   **Do not wait for a cheap window; there has not been one in eight cycles and
   this cycle was the busiest yet.** Consider a **scoped, time-boxed** freeze —
   long enough to re-capture six goldens and land (a)/(b) — rather than an
   open-ended one (owner-queue rank 2).
2. **Re-verify every stage-0 golden against the then-current keepers** before
   resuming any change. Do not trust this board's staleness table — re-read
   `frontend/data/backcast/keepers/<ISO>.json` and
   `results/regression-goldens/perfb-stage0/manifest.json` at that HEAD and
   re-derive it. **At `e0c1f0e` the answer is that ALL FIVE captures are stale
   and PJM was never taken — there is no shortcut left to inherit.**
3. **Assume every re-capture is a real solve.** v8's "cheap sidecar-compare"
   shortcut is dead for **every** ISO now, not just NYISO: ERCOT is four
   promotions past its capture, NYISO five, MISO four. The **re-stamp-not-
   re-solve** shortcut was established for **neiso-97 only** and NEISO has since
   moved to neiso-99 — **re-establish it before relying on it.** Apply the
   sidecar-comparison test per ISO before spending a solve, but **re-derive the
   config diff first** rather than inheriting a prior cycle's label.
4. **Capture PJM** — the one ISO with no golden at all, and the one gap no amount
   of keeper stability closes. It is also the **only ISO whose keeper has not
   moved in two cycles**, which makes it the cheapest capture on the board and
   arguably the one to take *first*.
5. **Do NOT re-do change (c).** It landed via #3964 and is byte-identical at HEAD.
   Verify the blob (`af34031c`) rather than re-porting it.
6. **Close the #4054 residual if you want belt-and-braces** — but **re-derive it,
   do not inherit it.** The NYISO keeper has moved **five promotions** past the
   captured nyiso-140 config, so any "this costs a fidelity read, not a solve"
   claim must be re-established at that HEAD first.
7. **Then, and only then, resume changes (a)–(e)** — and re-read the G2 leg list,
   because *merged byte-green* is what the gate wants, not captures.
8. **Confirm the golden tier is green IN CI before claiming any byte-green
   result.** The #4071 fix has landed and replays green locally, but **its CI
   proof is still outstanding after three director reads** — one
   `workflow_dispatch`, or the next weekly cron. A tier that cannot provision
   `data/clean` cannot prove byte-identity of anything, and a local replay is not
   the gate.
9. **Drain the parity queue and fix its source.** 8 dead bundle dirs at v10, all
   NYISO. A prune pass clears the symptom; **the NYISO lane registering arm
   bundles slower than it produces them is the cause**, and a freeze period is
   the natural moment to close that gap for good.
