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
> of this board, not at change (a). **The golden tier remains PARKED** (owner
> ruling 2026-08-22, unchanged): **byte-green cannot be CLAIMED for G2 while the
> tier is paused**, so **G2 leg 1 has TWO parked dependencies** — WS3/PERF-B and
> the golden tier — not one.
>
> ### 🟢 NEW AT v17 — THE REFRESH SITTING'S FOUR RULINGS ARE ON THE RECORD, AND THREE OF THE FOUR ARE ALREADY *PAST* EXECUTION
>
> v16 recorded the 2026-08-30 decision cards executed. v17 records a **third
> sitting** — the 2026-08-31 **REFRESH** — whose seven rulings split into the
> three v16's post-pin block caught as *ruled* (**R-A / R-B / R-C**, all three
> now **EXECUTED AND MERGED**: #4442, #4439, #4431) and the four this records
> lane executes (**R-D / R-E / R-F / R-G**). **R-D rests the C-1 wind question**
> at this representation grain with a decision map; **R-G closes nyiso-160/leg2
> by archive**; **R-F parks the nyiso-161 card behind a dated trigger** — and
> **that trigger is already met at this pin** (F-3). **R-E's chartered Q1+Q2 have
> BOTH already reported**, Q1 **REAL** and Q2 **CONFIRM** (F-2).
>
> ### 🟢 AND: ERCOT IS DECLARED `complete` AND `frontier` — THE FIRST ERCOT RULE-22 MARKER EVER
>
> Re-derived at this pin, not carried: `complete` = **{ERCOT, NEISO, PJM}** and
> the active `frontier` set = **{ERCOT, NEISO, PJM}**. ERCOT reads **CALIBRATED**
> at ISO level under the ercot-246 two-config partition ruling. `final` is still
> **EMPTY**, no ISO has ever spent a locked-test year, and the freeze is still
> tier-scoped to the locked test. See F-4.
>
> ### 🔴 AND: FOUR-INSTRUMENT ALIGNMENT BROKE AGAIN THE MOMENT IT WAS RESTORED — AND THE OUTLIER IS AN INSTRUMENT, NOT A MODEL
>
> v16's headline was alignment restored at {PJM, NEISO}. One cycle later
> **three** instruments agree at **{ERCOT, NEISO, PJM}** — CALIBRATED, `complete`,
> `frontier` — and the **forecast gate-(a) passers are still {PJM, NEISO}**. The
> break is **not** a substantive disagreement: ERCOT's seed gate-(a) stamp names
> `2026-08-24-231-tie-zone-measured` against a live `234-eastex-identity`, i.e. it
> **fails on a stale stamp**. **Four of six seed stamps are stale** (ERCOT, CAISO,
> NYISO, MISO). See F-5.

> **STATUS: PARKED AT G1** — live rollup maintained by the program-director
> session, updated on each owner "refresh". Canonical program definition:
> `docs/model-audit-release-plan-2026-08.md` (its §8 ledger is the durable event
> record; this board is the at-a-glance state). Completion figures are the
> director's estimate against each workstream's full DoD (A+B halves).

**Snapshot (v17):** **BASE SHA FOR EVERY FIGURE ON THIS BOARD: `d44446e0`**
(merge of #4464), derived live from `origin/main` on 2026-08-31 and **held stable
across two polling rounds** before the pin was taken. **The fetch that took it
was a FORCED UPDATE** (`3d8ea013...d44446e0 main -> origin/main (forced
update)`), recorded because a forced move of `main` is the one condition under
which a carried sha silently stops meaning what it meant. The director's own
derivation base **`4bdb2d60` (merge of #4454) is REACHABLE (ancestry-tested
inside `origin/main`) but 10 MERGED PRs STALE** (#4455–#4464), and unlike v16's
two-PR gap **this one moves real figures on this board** — the MISO keeper, the
ERCOT markers, three of the five gate readings and both C3c program answers all
landed inside it. Every count below states the window it was measured over.
**Nothing is carried from the dispatch, from board v16, or from any table,
unverified — and three figures the dispatch asserted are re-derived DIFFERENT
(F-8).**

| window | span | commits | non-merge | merged PRs |
|---|---|--:|--:|---|
| **since v16's pin** (`54ca19ae..d44446e0`) — the v17 cycle | 2026-08-31 00:19 → 04:26 UTC | **93** | **57** | **36** (#4429–#4464) |
| since v16's board LANDED (`e52b90a4..d44446e0`) | same day | **79** | **48** | **31** |
| **since the director's derivation** (`4bdb2d60..d44446e0`) — what moved after the prompt was written | same day | **23** | **13** | **10** (#4455–#4464) |

**Of the 36 merged PRs, classified per lane from BOTH the branch name and the
commits behind it** (v16 classified by branch name alone; that no longer
suffices — see the protocol amendment): **6 are this program's / 4 lanes**
(#4430/#4432/#4439 the R-B joint-wind lane, #4442 the R-A arming lane, #4431
the R-C re-verify lane, #4434 v16's own landing); **12 are the capx desk's /
8 lanes** (#4429, #4436, #4441, #4446, #4447, #4452, #4453, #4455, #4457,
#4458, #4460, #4461 — a DIFFERENT program); **18 are the calibration
program's / 10 lanes** (#4433, #4435, #4437, #4438, #4440, #4443, #4444,
#4445, #4448, #4449, #4450, #4451, #4454, #4456, #4459, #4462, #4463, #4464).
⚠️ **THREE capx lanes carry branch names that read as calibration work** —
`miso-t1h-retire-g3-regression` (capx-D3), `ercot-i3-slack-measure`
(capx D4-I3) and `calibration-workstream-relaunch` (the capx **director's own
refresh desk**, r#21) — **and account for 6 of the desk's 12 PRs.** A
branch-name-only classification would have mis-filed **half** the capx desk
into the calibration column.

**Keeper motion: ONE promotion, in MISO.** Re-derived rather than asserted: all
six `keeper` fields compared byte-for-byte at `54ca19ae` and at the pin —
**MISO `2026-08-30-miso-188-rvsscope` → `2026-08-30-miso-191-bexit`**, the other
five byte-identical. The keeper-shard byte-diff over the whole window is **two
files, +7/−1**: MISO's one-line keeper swap and **ERCOT's new six-line `frontier`
block**.

**ZERO open PRs** (live `list_pull_requests` at the pin) and **ZERO branches
ahead of `main`**: `ls-remote` returns **five** heads, and all four non-`main`
tips (`capx-d8-re-emission`, `miso-t1h-retire-g3-regression`,
`model-audit-director-workstream`, `pjm-164-c3c-phantom-audit`) are
**ancestry-tested INSIDE `origin/main`** — merged, not ahead. **No audit-program
lane is running at the pin**; this records lane is the only one, and it is the
dispatched instrument of the standing deviation.

**Headline, one line: all four refresh rulings executed — the ERCOT wind
question rested with a map, leg2 closed by archive, the nyiso-161 card parked
behind a trigger that has ALREADY fired, and the C3c program's Q1 and Q2 both
already answered (REAL, CONFIRM) and then INDEPENDENTLY REPLICATED post-pin —
while ERCOT took the program's first-ever ERCOT `complete`+`frontier` markers and
four-instrument alignment broke again on a STALE STAMP rather than on a model
fact.**

**⚡ POST-PIN RESOLUTION — ONE labelled follow-up measurement at `54d5772c`
(merge of #4466), taken under the v14 sanctioned exception because BOTH of
R-E's answers were INDEPENDENTLY REPLICATED while this board was being written.**
The pin readings above are NOT re-pinned; this block is the second labelled
state.

**A THIRD LANE ran R-E's Q1 AND Q2 in parallel, blind to the two that had
already answered them — and both verdicts SURVIVED.** Read from the landed
artifacts, not from a listing:

- **Q1 = REAL, replicated by a DIFFERENT CONSTRUCTION** (pjm-165,
  `docs/FINDING-c3c-q1-pjm-phantom-audit-2026-08-31.md`). pjm-164 overlapped the
  model's C3c **tail hours** against the actual RT LMP tail; this lane overlapped
  the model's **positive-reserve-dual hours** against PJM's **published
  reserve-market record**. Four legs pjm-164 did not carry: the requirement is an
  **exact published identity in 26,229 family-hours**; the channel **never
  touches a penalty step** and is structurally bounded below the published $300
  one; the positive-dual hours coincide with PJM's posted shortage intervals at
  **75–91× base rate (p ≤ 9.7e-11)**; and the model **UNDER**-prices reality by
  **2.7–7×**. **No disagreement on the verdict.** F-2 stands, strengthened.
- **Q2 = CONFIRMED, and the replication is the more interesting one because it
  first got the OPPOSITE answer and RETRACTED it** (nyiso-165,
  `docs/FINDING-c3c-q2-nyiso-nyca-shortage-2026-08-31.md`). Running blind, it
  measured *"reality WAS NYCA-short"*, found nyiso-164's record afterwards,
  re-derived from the raw CSVs and **reproduced nyiso-164's numbers exactly** —
  NYCA-tier tail-hour mean **$306.74 / $254.62 / $393.31**, ceiling test **0 of
  65**. **nyiso-164 is right; the parallel lane's first reading was wrong**, and
  it says so in its own title. F-3's trigger reading is unaffected.
- **🔴 AND THE RETRACTION FOUND SOMETHING THIS BOARD SHOULD CARRY: TWO LIVE
  DEFECTS IN A COMMITTED CALIBRATION REFERENCE.**
  `data/raw/_validation-source/actual_as_reserve_NYISO.parquet` is wrong on
  **both** counts — a cascade **sum** where the **max** is correct, and a
  positional `hoy` map that never localizes prevailing Eastern to the model's
  standard-time clock — in **every column, every year**. **Blast radius: NO
  keeper, NO scored result, NO determination** (its only consumer is the
  post-solve RCPF comparator for co-opt-off runs; `nyiso_rcpf_enabled` is False
  in the keeper and rule 19 `[R-ONE-MECH]` makes arming it alongside
  `energy_reserve_coopt` a hard error). **It is a trap for diagnostic sessions,
  not a defect in any result — and it caught one.** The repair is cheap and
  regenerable in-session from committed CSVs; the lane deliberately did **not**
  do it mid-audit and filed it for a data lane or an owner grant. **Recorded on
  this board's Watch, not adjudicated.**
- **🟢 The duplication is itself a finding, and the governance log now carries
  the cross-ISO synthesis both first-execution lanes deliberately deferred.**
  Three lanes, two questions, each executed twice in parallel by lanes that could
  not see each other — **and both replications agreed** (Q2 after correction).
  That is the strongest evidence this program has produced that a zero-solve
  measurement on committed artifacts reproduces.

**A statement about R-F's card, made by the replicating lane and RULED BY
NOBODY.** Its §6 records that the corrected Q2 result **strengthens** the
nyiso-161 card's characterisation of its **summer** half and removes an
objection to it: had the false positive stood, the summer face would have been a
published in-representation reserve-shortage quantity the model simply fails to
bind — a *defect*, not a model-class limitation — contradicting the card's own
phrase *"the ledgered C3c limitation"*. It does not stand. **Three
qualifications the lane states itself:** it bears only on the summer half (the
winter face's AORR identification block is untouched); it is about
*characterisation*, not arithmetic, caveat budget or the standing rule; and
**that lane rules nothing on the card**. **Neither does this board** — R-F parked
it for the DIRECTOR to re-serve, and F-3's reading is unchanged: the trigger is
met and the card is re-servable.

**Every keeper shard, `calibration-complete.json`, `holdout-freeze.json`, the
registry, `results/regression-goldens/`, `.github/workflows/` and `docs/audit/`
are verified BYTE-UNMOVED `d44446e0` → `54d5772c`**, so every keeper-table,
marker, holdout, stage-0 and workstream figure above stands unchanged.

**ALL FIVE GATES RE-RUN at `54d5772c`** (exit codes captured directly, unpiped):
audit_keepers **PASS 0/0** · parity **exit 0, 58 / 93 / 0** · matrix **exit 0,
194 + 49 + 153** (⬅ **+1 path anchor**, the new findings' citations) · staleness
**exit 0, Δ = 1 → 0**, and **stamped/scored 81/49 → 83/51** · bench **exit 0, 0
STALE, 19 of 20 with engine drift — unchanged**.

**Lane state at the second reading: FOUR merged PRs** (#4466 the c3c replication
lane, #4467 NEISO-RC-R Phase B, #4468 miso-194, #4469 the calibration director's
refresh), **and this lane's own branch is now the only one ahead of `main`.**

**Nothing else changes.** F-1…F-8, the keeper table, the stage-0 table, the
gates table, the forecast board and the queue are unaffected; **F-2's and F-3's
verdicts are confirmed rather than rewritten**, and this block reads as what
happened next.

## What moved — v17 CYCLE (`54ca19ae..d44446e0`, "the refresh-ruling cycle")

**Read F-1…F-3 as one act:** they are the 2026-08-31 owner **REFRESH sitting**,
executed by this dispatched records lane under the standing deviation (the
supersession v16 recorded was one-sitting and is spent).

### F-1 · 🟢 R-D EXECUTED — THE C-1 WIND QUESTION IS RESTED AT THIS GRAIN, WITH A MAP, AND NOTHING IS ARMED OR REJECTED

Owner ruling R-D, on `docs/FINDING-c1-joint-wind-ab-2026-08-31.md` (R-B's
chartered A/B; both kill-gates PASS; **`NON_COMPLEMENTARY`**). Executed per the
**caiso-222 §1(c) option-3 pattern** — the residual is designated **ATTRIBUTED
AND CLOSED at this representation grain** with a decision map attached rather
than an open investigation. **Retires v16 owner-queue item 2.**

**The measurement, re-read from the finding at this pin.** The joint arm builds
wind **1.442 GW** — to the megawatt the committed signal-alone arm's number —
closing **8.87 %** of the **12.313 GW** miss, while **the volume rule contributes
exactly ZERO wind** on a dual-based level (naive sum of the singles 13.77 %; best
single 8.87 %; joint 8.87 %; difference **0.00 pp**). The walk is **live, not
inert**: it changes **exactly one decision** in the whole 2021–2025 window —
entering-2023 solar **5,550 MW → 0** — with everything else byte-identical to the
pure disarm arm. The volume rule's 4.91 % under the *shipped* signal is
identified as a **shipped-signal artifact**.

**The attribution.** A **zone-flat, ORDC-dominated signal at hub grain**:
`zonal_mean_range` and `hourly_cross_zone_spread` measured **exactly 0.0**, ~90 %
of the dispersion is the ORDC adder, West build-zone capture **0.494/0.805/0.927**
shipped against **0.988/0.988/1.055** on the model's own duals.

**Published open, not retired: 91.1 % of the miss stays open**, every addition
band FAILs in both arms, and the dual level's adequacy cost is **terminal RM
25.19 → 38.84 %, +13.65 pp** on a [13.8 %, 28.7 %] band. **Nothing is armed** —
`entry_lookahead_reprice` verified at `ScenarioConfig` default `True`
(`scenarios.py:3919`) — and **nothing is rejected**. **Re-open conditions,
exhaustive:** a NEW MEASURED DRIVER (rule 13 `[R-MEASURED]`), or an
OWNER-CHARTERED REPRESENTATION-GRAIN CHANGE (the caiso-223 class — a program, not
a lever). Neither is reachable by re-running a lever at hub grain.

**Records:** `docs/DECISION-MAP-ercot-wind-entry-2026-08-31.md` (new) ·
`docs/calibration-log/ercot.md` · `docs/calibration-log/governance.md` · R-D
ruling stamps appended to the **evidence strings only** of the two joint-wind
ERCOT cells. **⚠️ ONE DISPATCH CORRECTION:** the dispatch said "cells stay O".
Re-read at the pin, the two cells are **`entry_lookahead_reprice` cell K / fc O**
and **`entry_margin_exhaustion` cell O / fc K** — neither is "O/O". The binding
instruction (**no verdict letter changes**) was followed exactly; both cells are
byte-unchanged except for the appended stamp, and `check_mechanism_matrix.py`
exits **0** after the edit (2 lines changed, 2 inserted / 2 deleted, whole file).

### F-2 · 🔵 R-E RECORDED — AND ITS TWO CHARTERED QUESTIONS HAVE ALREADY REPORTED AT THIS PIN: Q1 **REAL**, Q2 **CONFIRM**

R-E charters the C3c scarcity program's **Q1 + Q2, chained** (Q1 the PJM phantom
audit first; Q2 opens only on Q1 = REAL), with **Q3 unopened and explicitly not
recommended** — it is an architecture decision colliding with rules 4
`[R-DUALS]`, 8 `[R-8760]` and the no-MIP constraint. Its execution lane is
dispatched separately. **The dispatch-vs-launch check on it does not read
"launched" — it reads DONE:**

- **Q1 = REAL** — pjm-164, **#4456**,
  `docs/FINDING-pjm164-c3c-phantom-audit-2026-09-01.md`, zero solve. PJM's
  reserve-dual channel is **not** the ercot-214 phantom: 2025 model-tail overlap
  with reality's tail **14 of 32** hours (0.44 of the model tail, 0.24 of the
  actual), **13** of them with a positive reserve dual, against published
  DataMiner2 reserve MCPs; 2023–24 near-zero overlap but near-zero reserve
  involvement, so that mis-timing is not the reserve channel's. Three honest
  caveats, **none determination-level**.
- **Q2 = CONFIRM** — nyiso-164, **#4459**,
  `docs/FINDING-nyiso164-c3c-product-level-2026-09-01.md`, zero solve. The
  pre-registered kill gate fires on **both** clauses (NYCA-tier reserve price
  never exceeds the concurrent LMP in **65/65** tail hours; model carries
  **5.08/3.92/2.99 GW** of reserve-carrying headroom against a 2,620 MW NYCA
  30-min requirement, NYCA families at zero dual and zero shortfall in all
  **26,280** hours). **NYISO's C3c ledger is CONFIRMED on its own evidence**, and
  the lane reports the interpretation reversal rather than burying it.

**Two consequences for this board's queue, both derived rather than assumed:**
the **PJM determination-integrity card the dispatch made conditional on Q1 =
PHANTOM does NOT open** — no PJM keeper rests on a phantom channel; and **R-F's
trigger is met** (F-3). **Neither lane moved a keeper, marker, determination or
matrix cell, and neither spent a holdout year.**

### F-3 · 🟠 R-F EXECUTED — THE nyiso-161 CARD IS PARKED BEHIND A DATED TRIGGER, AND THE TRIGGER HAS ALREADY FIRED

Owner ruling R-F: **neither A (NOT-YET stands) nor C (declare CALIBRATED)**. The
card **stays filed** and moves from *open-undecided* to **PARKED — re-serve when
the C3c program's Q1/Q2 report lands**. **NYISO's determination is unchanged and
restated: NOT-YET on {C3a-2025 −11.5 %, C3c}.**

**Re-derived at this pin, and it changes how the item must be carried: the report
has landed and Q1 returned REAL, not PHANTOM** (F-2). So the card is not
*waiting* — it is **PARKED-AND-RE-SERVABLE, servable at the next sitting.**
Carrying it as "waiting on a report" would leave the next reader expecting
something that has already arrived. **The deferral itself is untouched: the owner
deferred, and only the owner un-defers.** Standing context, unchanged: the
**AORR access route is PERMANENTLY CLOSED by owner decision** and **nyiso-97 §5
re-open condition 3 is WITHDRAWN** (conditions 1 and 2 stay live passive watch
items), so the winter face of C3a-2025 is **permanently unidentifiable from
obtainable data**; **option B is dominated** (marker re-entry needs CALIBRATED,
not CWC); and **the precedent surface is not NYISO-only** — CAISO's C3a residual
is CEII-blocked on both lever routes and would have an immediate claim on any
access-blocked caveat class.

### F-4 · 🟢 R-G EXECUTED — nyiso-160/leg2 CLOSED BY ARCHIVE, AND THE PROMOTE-OR-ARCHIVE ITEM RETIRES FOR GOOD

On `docs/FINDING-nyiso-leg2-reverify-2026-08-31.md` (nyiso-162, #4431, R-C's
zero-solve re-verification), the owner ruled **archive**. The re-verification
dissolved its own question: **there is NO candidate** — leg2 produced a stop with
cause at access, not an object (no prereg, no mechanism, no A/B pair, no control)
— and the object that *does* exist is the keeper's own recipe re-established at
HEAD, scoring **identically** to the live keeper: **zero record-level differences
across 60 scored records** (the sole difference anywhere is the C6 attestation
narrative string), **0 solve-affecting levers**, **max |Δ| = 0 over 1,043,280
hourly rows**, `metrics.json` 58/60 leaves identical. Promotion would have been a
formal no-op that **weakened** the designation's evidentiary basis; archiving
costs nothing evidentially. **The registered runs and the findings stay on the
record**; the item is **not re-servable**, because the object it named does not
exist. Keeper and determination untouched, `audit_keepers --iso NYISO` PASS 0/0,
**no matrix cell moves**.

### F-5 · 🟢 ERCOT TOOK ITS FIRST RULE-22 MARKER EVER — AND ITS FIRST FRONTIER — IN THE SAME OWNER UTTERANCE

Re-derived from the live files, not from the dispatch (which did not mention it
at all). `frontend/data/backcast/calibration-complete.json` `complete` now holds
**{ERCOT, NEISO, PJM}**; `keepers/ERCOT.json` carries a new `frontier` block
`declared: 2026-08-31`. Owner, quoted in the marker: *"I think you can declare it
complete / frontier."* The determination basis is the **ercot-246 ruling** — a
partitioned keeper's ISO-level determination is the **worst config determination
over the DESIGNATED spans** — under which the forward config on {2024, 2025} and
the 2023 carve-out on {2023} both read CALIBRATED, so ERCOT reads **CALIBRATED**.
The marker's own text carries the honest record at full magnitude: the forward
keeper's **registered unrestricted 3-year determination is still NOT-YET** on
{C3a-2023 −39.7 %, C3b-2023 0.730}, and that registered record stands published
untouched. `audit_keepers` M1b was extended in the same commit to re-verify the
partition rollup live rather than read the shard's assertion, and it **PASSES**
at this pin.

**Scope, stated because a marker is the most expensive object on this board:**
`complete` authorizes the **validation tier only**. `final` is **EMPTY**
(`_note` only), ERCOT is absent from it, the freeze stays tier-scoped to the
locked test for every ISO, and **no ISO has ever spent a locked-test year** —
re-verified at the pin by walking all **58** sidecars (year histogram
**{2022: 2, 2023: 56, 2024: 52, 2025: 52}**; the scan for {≤2018, 2019, 2026}
returns **NONE**; the only out-of-training registrations remain the two
authorized 2022 touchpoints).

### F-6 · 🔴 FOUR-INSTRUMENT ALIGNMENT BROKE AGAIN — AND THE OUTLIER IS A STALE STAMP, NOT A MODEL FACT

v16's headline was alignment restored at {PJM, NEISO}. At this pin **three of
four agree at {ERCOT, NEISO, PJM}** — CALIBRATED = `complete` = active
`frontier` — and the **forecast gate-(a) passers remain {PJM, NEISO}**.

Re-derived field-by-field against the live shards, exactly as v16's protocol
requires (the seed is a different program's file and its schema is re-read, not
assumed):

| ISO | seed's gate-(a) keeper | live keeper | (a) | (b) | (c) | (d) | `open` |
|---|---|---|---|---|---|---|---|
| ERCOT | `2026-08-24-231-tie-zone-measured` | ⬅ `234-eastex-identity` | **fail — STALE stamp** | fail | pass | none | false |
| PJM | `pjm-162-inputclock` | same | **pass — current** | fail | pass | none | false |
| CAISO | `caiso-200-h1-memberpanel` | `caiso-220-c1-crosswalk` | fail — STALE | fail | fail | none | false |
| NYISO | `nyiso-157-par-attribution` | `nyiso-159-loss-surface` | fail — STALE | pass | pass | none | false |
| NEISO | `neiso-99-joint-p1` | same | **pass — current** | pass | pass | **granted** | **TRUE** |
| MISO | `miso-177-rho-measured` | ⬅ `miso-191-bexit` | fail — STALE | fail | pass | none | false |

**The break is instrument-side.** ERCOT now holds `complete` and reads
CALIBRATED, and its gate-(a) fails **on a stamp naming a keeper two promotions
old**. **Four of six stamps are stale** (ERCOT, CAISO, NYISO, MISO) — the same
count as v16 but with MISO now two promotions behind rather than one.

**🟢 AND A FIRST: NEISO'S FULL-SOLVE AUTHORIZATION GATE IS OPEN.** v16 recorded
*"NO ISO'S FULL-SOLVE AUTHORIZATION GATE OPENS, and none opened from this
refresh"*, with leg (d) `none` everywhere. At this pin NEISO reads
**(a)+(b)+(c)+(d) all held, `open: true`** — leg (d) **granted** by the
T3-NEISO-GOLDEN lane, which also measured NEISO's T3 BAU golden (25/25 years).
**This is the forecast program's board and this lane adjudicates none of it**;
it is recorded because a leg this board has published as `none` for every ISO,
every cycle, has moved.

### F-7 · 🔵 THE CALIBRATION SWEEP — 18 PRs ACROSS 10 LANES, AND EXACTLY ONE PROMOTION (recorded, not adjudicated)

Recorded from the merge subjects and the landed artifacts, never adjudicated by
this board:

- **ERCOT — the biggest state change of the window, and it is not a keeper.**
  The ercot-245 Phase-0 census **KILLED the per-class commitment-state bound**
  (K-A ST mass, K-C saturation, K-T gas classes fire; Phase-1 **not licensed**),
  **ercot-246** ruled the ISO-level determination of a partitioned keeper, and
  **ercot-247** took the `complete` + `frontier` declaration (F-5). Keeper
  `2026-08-25-234-eastex-identity` **unmoved**.
- **MISO — the cycle's only promotion**, `miso-188-rvsscope` →
  **`2026-08-30-miso-191-bexit`** (binning-aware exit-cohort delivery, #4433 +
  the registrations). Its C3a row moved **+3.5 % → +0.1 % (2023)** and
  **−4.3 % → −4.6 % (2024)**; **C3a-2025 −12.3 % is unchanged and still the lone
  fail**. Separately **miso-192** (D-4 posture) and **miso-193**
  (`cc_duct_peaking`, registered as a rejected probe with its bundle sidecars,
  cell **U → K**) landed.
- **CAISO — UNMOVED.** caiso-226 (OFO intake) and **caiso-227** (C3a-2025
  root-cause / PS intake) landed, and **caiso-228's SoCalGas OFO gas-deliverability
  arm DIED AT GATE D1 with no solve**. Terminal rest undisturbed; C3a-2024/2025
  still +12.5 / +15.5 %.
- **NYISO — no keeper motion; four records sessions.** nyiso-162 (R-C), nyiso-163
  (+163b: the AORR access route **permanently closed**, the C3c program opened),
  nyiso-164 (**Q2 = CONFIRM**). Determination unchanged.
- **PJM — untouched for a NINTH consecutive cycle, and it was audited rather than
  changed.** pjm-164 ran **Q1** against its own CALIBRATED keeper and returned
  **REAL** (F-2). Still the only 8/8 zero-caveat scorecard and still the only
  current stage-0 row.
- **NEISO — UNMOVED on the backcast**; its `final` grant stays **DATA-BLOCKED**.
  On the forecast board it became the first ISO with an **open** gate (F-6).
- **The capx desk (a DIFFERENT program) merged 12 PRs across 8 lanes** — D12-A
  (#4429), D3 (#4455/#4458), D4-I3 (#4460), D8-RE (#4457), the S-6 and S-123-V
  verifies (#4436/#4441), the T3 NEISO golden (#4447/#4452) and three
  `calibration-workstream-relaunch` **director refreshes** (#4446/#4453/#4461).
  **Recorded only for shared-surface touches.** ⚠️ **Three of its eight branch
  names read as calibration lanes** and were reclassified by commit content —
  they account for **6 of its 12 PRs** (F-8's methodological half).

### F-8 · 🟠 THREE FIGURES THE DISPATCH ASSERTED ARE RE-DERIVED **DIFFERENT** — WHICH IS THE PROTOCOL WORKING

Recorded plainly because the dispatch instructed *"trust nothing in this
prompt"*, and the instruction earned its keep:

| dispatch asserted | re-derived at `d44446e0` |
|---|---|
| parity **60 runs / 95 dirs** | **58 runs / 93 bundle dirs** |
| bench **0 STALE, 0 drift** | **0 STALE, 19 of 20 parts WITH engine drift** |
| the two joint-wind cells "stay **O**" | **cell K / fc O** and **cell O / fc K** — neither is O/O |

The bench line is the substantive one: v16 predicted the WARNs return "on the
first engine commit dated 2026-08-31 or later", then measured **20 of 20** in its
post-pin block. At this pin it is **19 of 20** — and the one part that does *not*
WARN is **MISO/2023**, which was **rewritten by the miso-191 registration**
(`1b419b7b`, 2026-08-31 00:33 UTC) and is therefore *newer* than the three engine
commits, not fresher in any repaired sense. The instrument is behaving exactly as
v16 diagnosed it; nothing was repaired.

## What moved — v16 CYCLE (v16 record, RETAINED as history) (`69ae4dc7..54ca19ae`, "the decision-card cycle")

**Read F-1…F-4 as one act.** They are the 2026-08-30 owner **decision-card**
sitting — a *second, later* sitting than v15's PM rulings — all four cards
executed inside the same window, and, by an explicit one-sitting owner
supersession of the standing deviation, executed **by the director desk itself**
rather than dispatched (F-10).

### F-1 · 🟢 CARD 1 EXECUTED — THE PJM STAGE-0 GOLDEN IS CAPTURED, AND THE STAGE-0 TABLE HAS ITS FIRST CURRENT ROW

The capture this board has called *the cheapest and the largest gap* on
**seven consecutive boards** was taken (#4369). Re-derived at the pin from the
committed manifest, not read from the ledger entry:
`results/regression-goldens/perfb-stage0/manifest.json` `keepers` now holds
**all six ISOs** (v15: five), the PJM entry's `keeper_id` is
**`2026-08-15-pjm-162-inputclock`** which **byte-matches the live keeper**, its
`years` are `[2023, 2024, 2025]` (rule 16, the keeper's own recorded span), and
its per-file `content_hashes` are present. The manifest's top-level `git_sha` is
**`1cfea72`**, which `git cat-file` resolves **and** `merge-base --is-ancestor`
places **inside `origin/main`** — the `af1ccb6` defect is not repeated for this
capture.

**The scope was exactly the card and no more: WS3 stays PARKED.** Card 1
explicitly DECLINED the full freeze + golden-tier restart and the
captures-only option. So **G2 leg 1 keeps both of its parks** — this is a
scoped capture inside a parked workstream, not a restart, and nothing in the
G2 leg list moves.

The capture's own operational record is on the plan's §8 entry and is honest
about what it cost: the first attempt died on the container's 13.3 GiB cgroup
RAM limit and succeeded only after a 12 GB swapfile; it needed a re-fetch of
the converted `pjm-da-virtuals` corpus; and it WARNed on a missing PJM
hydro-plant-modes partition. **Fidelity oracle: 256 recorded flags replayed
identically, `scenario_config` 713 matched / 0 drifted, 15 HEAD-only meta keys
(post-freeze `ScenarioConfig` additions).** For whoever un-parks WS3 the
operational half is the transferable part: **assume a re-capture is a real
solve, and assume it needs the swapfile.**

### F-2 · 🔵 CARD 2 EXECUTED — THE HOMELESS T1-H CAPACITY-ENTRY DEFECT GOT A CHARTER, A LANE, AND A MEASURED A/B IN ONE DAY

v15's owner-queue item 6 — *"the T1-H capacity-entry defect (two defects, not
one) still has no charter and no home"*, carried since v13 item 11 across
**three boards** — is **retired**. The charter
`docs/PRECOMMIT-t1h-capacity-entry-2026-08-30.md` was written and then run to
completion in the same window:

- **Phase 0** (#4369, `docs/FINDING-t1h-capacity-entry-phase0-2026-08-30.md`) —
  zero-solve characterization from committed T1-H artifacts.
- **Phase 1 Leg A** (#4419 + #4426,
  `docs/FINDING-t1h-capentry-phase1-ab-2026-08-30.md`) — the storage-entry
  **D-2 + D-3 joint repair A/B'd on one HEAD**. Both charter kill-gates PASS:
  **K1 had nothing to fire on** (every addition-metric band identical between
  arms to the digit) and **K2 (inert) does not fire** (the storage-mix rows
  differ). The arm reproduces the Phase-0 §3.3 pre-registered signature
  byte-exact: `iron_air` 3,000 + `flow_battery` 2,000 MW (64.0 h, li-ion 0 %)
  → **`li_ion_4hr` 3,000 + `li_ion_8hr` 2,000 MW (5.6 h, li-ion 100 %)** —
  the 1.6 h class ERCOT actually built. Couplings reported at full magnitude:
  the ledger reserve-margin path shifts **down** (8.54 → 6.98 / 14.65 → 13.10
  / 25.19 → 23.61 %) with **no downstream decision flipping**, and co2
  (reported-only) moves −0.49 / −0.52 / **+0.34** Mt.
- **ERCOT matrix cells verified at the pin, not asserted:**
  `storage_entry_availability_gate` and `storage_entry_cost_normalized_rank`
  both read **`cell: "O", fc: "O"`** in `mechanism-matrix/ERCOT.js` with the
  Leg-A A/B as citation — **`U` → `O`, measured, ARMING OPEN**.

**Nothing is armed, and arming is an owner decision on this A/B record** — the
charter's own line, and the lane held it: both `ScenarioConfig` fields ship
**default-OFF**, registered on the **forecast** namespace only, with the
backcast registry, every keeper shard, `calibration-complete.json`,
`holdout-freeze.json` and `program-status.json` untouched.

**Leg B (the separate wind leg) is a measurement rung and stayed one.** The
dual-based signal object closes **8.87 %** of the wind entry miss (model
0.350 → 1.442 GW against 12.663 GW actual; remaining gap 12.313 → 11.221 GW),
**leaving 91.1 % open** — and the same run's terminal reserve margin *worsens*
25.19 → 40.24 % and its gas_ct and storage bands move the other way. The
finding proposes no lever and states so: *"Leg B does not become a repair rung
on this evidence."* The measured input for the owner's **C-1 signal-object
call** is delivered; the call is not made.

### F-3 · 🟢 CARD 3 EXECUTED — "RE-VERIFY REQUIRED" IS NOW A STANDING RULE

The cross-lane re-grade precedent carried on this board since v13 (the
nyiso-143 D-4 rider + the shared-benchmark determination flip) has a rule.
Verified in place at the pin: `docs/calibration-log/governance.md`, the
2026-08-30 entry, **Ruling 1 — CROSS-LANE RE-GRADE: RE-VERIFY REQUIRED
(standing rule)**. A scorer or shared-file change that flips another lane's or
program's committed state now requires **the affected lane's own D-5(b)-style
re-verification from committed artifacts, never a solve**, before the flip
publishes — and a disagreeing re-verification **stops** the flip and escalates.
**Retires v15 owner-queue item 5.** The *adjacent* instance v15 attached to
that item (#4343, a different program writing this program's marker file) is
now covered by the rule going forward, and the Watch entry is re-scoped to the
class rather than the instance.

### F-4 · 🟢 CARD 4 EXECUTED — THE NYISO FRONTIER IS REVERTED, AND ALL FOUR INSTRUMENTS ALIGN

Owner, verbatim on the record: *"NYISO is not frontier it was reverted bc it's
not yet so it's PJM and NEISO only."* Executed as the **append-only**
`reverted_2026-08-30` key in `keepers/NYISO.json` `frontier` — the 2026-08-23
ratification and R-1's currency annotation are **retained as history**, not
deleted. Verified at the pin: the block carries `declared: 2026-08-23`,
`withdrawn: 2026-08-30`, `keeper_at_withdrawal:
2026-08-30-nyiso-157-par-attribution`, the owner verbatim, **and** the
`calibration-keeper-text-auditor`'s machine-readable `withdrawn` /
`withdrawn_note` mirror, added specifically so
`docs/codebase-site/js/calibration-status.js` `frontierActive()` **suppresses
the FRONTIER badge** rather than leaving the dashboard asserting a reverted
claim. That mirror is the interesting half: **v15's Watch item "evidence prose
is gate-checked nowhere" got its first machine-readable answer** — one field,
one ISO, by hand, but a rendering-drift gap closed at the renderer rather than
in prose.

**Retires v15 owner-queue item 1** (the board's top item for two cycles in one
form or another) and sets the standing rule **marker-master**: a frontier does
not survive its ISO leaving CALIBRATED/`complete`.

*(Records note, no action: `keeper_at_withdrawal` names nyiso-157, which the
same window superseded with nyiso-159. That is correct as history — it records
the keeper at the moment of withdrawal — and is flagged only so a later reader
does not mistake it for a stale currency defect of the R-1 class.)*

### F-5 · 🔴 RE-DERIVING E-7 FOUND IT IS FIVE-WIDE, AND THE `af1ccb6` DEFECT WAS OVERWRITTEN RATHER THAN RESOLVED

v15's E-7 recorded that a top-15 retention prune removed the **ERCOT** stage-0
golden's provenance run from the registry. **Re-deriving the whole table rather
than carrying it — the v15 protocol amendment, applied — shows the ERCOT case
was the visible instance of a five-wide condition.** At the pin, each capture's
`keeper_id` tested for a committed registry sidecar:

| capture's `keeper_id` | registry sidecar |
|---|---|
| `2026-08-15-ercot204-rule26-delete` | **MISSING** |
| `2026-08-16-caiso-197-w2-r5` | **MISSING** |
| `2026-08-16-miso-160-wefor-shape` | **MISSING** |
| `2026-08-14-neiso-93-envelope` | **MISSING** |
| `2026-08-16-nyiso-140-layup-exclusion` | **MISSING** |
| `2026-08-15-pjm-162-inputclock` | **PRESENT** |

**All five were already missing at `69ae4dc7`** (tested at both revs) — so this
is not new damage this window; it is v15 having reported the *motion* (ERCOT's
prune happened in its window) where the *condition* already covered five. **The
only capture whose provenance run is registered is the one taken this window.**

**And the manifest's provenance sha problem changed shape.** `af1ccb6` no
longer appears anywhere in the manifest (`grep` count 0). It was not resolved —
the Card-1 capture's diff is `-  "git_sha": "af1ccb6",` / `+  "git_sha":
"1cfea72",` against **124 inserted lines that add only the PJM entry**. The
manifest has **one** top-level `git_sha` for **six** captures taken at six
different trees and **no per-entry provenance sha** (entry fields verified:
`bundle`, `content_hashes`, `defaulted_unrecorded_params`,
`dropped_dead_config_keys`, `fidelity`, `hours`, `keeper_id`,
`recorded_flag_count`, `years`). So the five older captures now carry a sha
that **resolves and is wrong** — strictly harder to notice than one that did
not resolve at all.

**This is a schema limitation, not an error by the Card-1 lane** — the lane
wrote the field its script writes, and recorded a resolvable sha, which is the
improvement it was asked for. The consequence for WS3 is unchanged in kind and
sharper in fact: **the per-file `content_hashes` remain the only sound
verification instrument**, and the restart checklist's item 11 (record
provenance *inside* the manifest) now has a second, independent reason —
**per-entry**, not just self-contained.

### F-6 · 🟢 AUDIT ROW O7 IS CLOSED — THE FIRST WS1 ROW TO MOVE IN THREE CYCLES

`docs/audit/third-party-audit-2026-08.md` row **O7** reads **CLOSED 2026-08-30**
at the pin (#4377; the row's own diff is the only change to `docs/audit/` in the
whole window). The owner's Door-2 ruling — *keeper-moving restoration DECLINED,
accept-as-limitation DECLINED, the §5 attribution-harness partial AUTHORIZED* —
was built **and exercised** on a real year:

- **HP-1 PASS**: a de-laddered leg whose **P0, startup markup, bridge min-gen
  floors and committed-row run stats are hash-provably BIT-IDENTICAL** to the
  keeper's, both adaptive passes — which is precisely the attribution the
  forfeiture had cost.
- **The decomposition is itself a finding**: on the 2023 `ercot236_k33_clip`
  A/B, the ladder's **pricing** channel at the keeper's own commitment state is
  **−$0.02/MWh**, while **commitment + interaction carries +$2.26/MWh of the
  +$2.24/MWh whole** (74/132 committed rows, 12,380 MW commitment delta). The
  ladder is essentially **not** a pricing mechanism at this recipe; it is a
  commitment mechanism.
- What stays true permanently, now measured rather than open: **R1's own
  arm/off comparison remains whole-solve** — the forfeiture is a property of
  the mechanism, not of its wiring — carried as the ERCOT keeper's **named
  permanent limitation** (ercot-188/E2, unexpired). **Keeper untouched.**

Records: `docs/FINDING-o7-attribution-harness-2026-08-30.md`;
`results/calibration/o7_attribution_harness_2023.json`; harness
`scripts/probes/o7_attribution_harness.py` (+17 toy tests).

### F-7 · 🟠 NYISO PROMOTED (157 → 159) — THE ONE KEEPER MOTION, AND IT IMPROVED THE SCORECARD

The cycle's only promotion. Re-read from the shards at the pin, not carried:
`2026-08-30-nyiso-159-loss-surface`, determination **`NOT-YET`**, grade
**8 scored / 6 target / 2 fails / 0 ledgered** against nyiso-157's
**8 / 5 / 3 / 0**. **C3b (`price_shape`) left the fail set** — the measured
zonal loss surface closed it — leaving **{C3a-2025, C3c}**. C3a(RT) moves
+1.0 → **+2.3 %** (2023), −2.0 → **−1.2 %** (2024), −12.0 → **−11.5 %** (2025).

Two governance readings, both verified rather than assumed:

- **C3c reads FAIL, not CAVEAT, and that is the standing rule working.** The
  C3c standing rule requires C3c to be the **lone** failing criterion; C3a-2025
  also fails, so guard (a) keeps the rule silent and **both failures stand**.
  `caveats.ledgered` is empty for this keeper.
- **No `complete` re-key was owed.** NYISO's `complete` marker was withdrawn on
  2026-08-30 (Q5-W), so rule 22 D-5(b)'s re-key-on-promotion duty does not
  attach. Verified: `complete` = **{NEISO, PJM}**, both re-keyed to their live
  keepers, and `audit_keepers.py` PASS 0/0.

**The successor lane's audit is the more interesting artifact for this board.**
nyiso-160 ran a zero-delta replay of the *new* keeper at HEAD and audited it
from committed bytes: **max abs divergence 0.0 on every hourly-sidecar value
column, all three years**; C3a reproduces to 0.00 pp; the two differing
recorded keys are post-recording rule-24 schema growth at registered default
`False`, proven inert. **Verdict: NO G1-class drift.** That is the strongest
keeper-reproducibility evidence on this board, and it bears directly on the
re-capture question (F-8, checklist item 4).

### F-8 · 🔵 THE CALIBRATION SWEEP — SIX LANES, THIRTY PRs, AND A LOT OF KILLS (recorded, not adjudicated)

Recorded because it is the board's context, **not** adjudicated — none of it is
this program's to rule on:

- **ERCOT** — **ercot-242** room-axis extension of the RT/SCED wall registered
  (`2026-08-30-run242-room-axis` sidecar present). **ercot-243** killed at
  census (population is h3068-2024 alone; K-1 and K-3 fire, lane stops).
  **ercot-244** rtolhsl ceiling **KILLED AT CENSUS**. **ercot-245** per-class
  commitment-state Phase-0 precommit + probe + Amendment 1.
- **NYISO** — the **158 → 159 → 160 → 161** arc, ending in the 159 promotion
  (F-7). **⚡ Past the dispatch:** the dispatch listed the **nyiso-leg2**
  winter-locational candidate as *awaiting owner promote-or-archive*; at this
  pin that lane's branch is **deleted** and **nyiso-160 recorded a Leg-2 STOP
  WITH CAUSE at access** (the MyNYISO AORR artifacts never landed; the owner,
  asked in-session, answered *"Cannot produce them"* — the nyiso-97
  stop-if-walled class, no substitute mechanism invented). The winter face of
  C3a-2025 is now **identification-blocked on both legs**; determination
  consequence **none**; **no matrix cell verdict moves**. **nyiso-161** then
  filed an **owner-ordered winter-face waiver decision card**. Recorded as a
  second, labelled state — see the Owner queue.
- **MISO** — **⚡ Past the dispatch:** miso-190's registration watch **CLOSES**
  (sidecars `2026-08-30-miso-190-control` and `-ppexit` both present, #4370 —
  a third-cycle watch item ends), and **miso-191 has LANDED** (#4379 + #4384,
  binning-aware exit-cohort delivery), not "in flight" as the dispatch had it.
- **CAISO** — caiso-224 merged (#4390/#4395/#4415 + the #4401 parity fix), and
  **caiso-225's watch sweep came back ALL NULL** (#4425, zero solves): W-1,
  W-2, W-3 and the F2 derate all still blocked, A3's SoCalGas OFO record
  confirmed **available + feasible but unfunded**, nothing fires, no intake
  charter opens, **keeper/matrix/markers untouched**. **Terminal rest
  re-affirmed** — new evidence for owner-queue item 7.
- **Crossover** — the **CO2 grain repair** landed (#4388 + the capx D5/D5-R
  pair), which is why the forecast board's co2 magnitudes are restated (F-9).

### F-9 · 🟢 THE FORECAST BOARD'S GATE LEGS ARE SCORED FOR THE FIRST TIME — AND NEISO IS THE FIRST THREE-LEG ISO

v15 recorded gate legs **(b) and (c) UNSCORED**. At this pin the committed seed
`frontend/data/forecast/program-status.json` — **restructured this window; its
schema was re-read, not assumed** (it now carries `gate_reading`, `readiness`,
`gate_a_provenance` and six per-lane record blocks) — scores **all four legs
for all six ISOs**. Re-derived leg-by-leg from `isos.<ISO>.gate`:

| ISO | (a) | (b) | (c) | (d) | legs held |
|---|---|---|---|---|---|
| NEISO | pass | pass | pass | none | **THREE — the first in program history** |
| NYISO | fail | pass | pass | none | two |
| PJM | **pass** | fail | pass | none | two |
| ERCOT | fail | fail | pass | none | one |
| MISO | fail | fail | pass | none | one |
| CAISO | fail | fail | fail | none | none |

**`open` is `false` for all six and leg (d) is `none` everywhere — no ISO's
full-solve authorization gate opens, and none opened from this refresh.** Legs
(b)/(c) moved on the owner's **Q7 ruling about what leg (c) MEASURES** (FC-4
measured and reported, never in-band) plus NEISO's first T1-X, **not** on any
improvement in the model — and every FC-4 that passes leg (c) is itself a
**FAIL quoted at full magnitude**.

**Gate (a), this board's own column, re-derived field-by-field against the live
keepers and the live `complete` block:** passers = **{PJM, NEISO}** = the
`complete` set, unchanged in membership from v15.

**🔴 Seed staleness went the wrong way: three stale stamps → FOUR.** ERCOT
(names `231-tie-zone-measured` vs live `234-eastex-identity`), CAISO (`200-h1-
memberpanel` vs `220-c1-crosswalk`), MISO (`177-rho-measured` vs
`188-rvsscope`) — and **NYISO is newly stale** (`157-par-attribution` vs
`159-loss-surface`), re-staled by its own promotion two hours after the Q5-W
lane had re-stamped it current. PJM and NEISO are current. **The v15 pattern
held and then broke in the same window**: the lane that moves a marker
re-stamps the board it drives — but the lane that moves a *keeper* did not.

**🟠 And the seed carries two readings at once again.** Its top-level
`gate_reading` prose still says *"nobody holds three"* and names lane D14 as
the lane that **would** produce a first three-leg ISO, while a bracketed
in-line UPDATE and the per-ISO `gate` block both record that D14 landed and
NEISO holds three. That is the **same class of defect the D13 reconcile lane
was raised to repair**, re-appearing inside one window because the board's
prose and its data move at different cadences. **Recorded, not adjudicated** —
the forecast namespace is a different program's, and the per-ISO blocks are
the authority.

*No forecast run was solved or re-scored by this lane*; per rule 15
`[R-DASHBOARD]` the forecast namespace is registered through
`scripts/register_forecast_run.py` alone, and the backcast CI gates stay blind
to it.

### F-10 · 🟠 THE DEVIATION WAS SUPERSEDED FOR ONE SITTING, AND A DISPATCH-VS-LAUNCH NEAR-MISS WAS CAUGHT

**On the record as a protocol fact, not a complaint.** The 2026-08-30
decision-card sitting's records duties were executed **in-session by the
director desk** under an **explicit one-sitting owner supersession** of the
standing deviation (owner, verbatim in the plan's §8: *"give me decision
cards … make real progress"*, with the deviation change recorded as
owner-directed). **That supersession is spent.** The standing deviation —
*the director issues prompts and pushes nothing* — **is back in force**, and
this lane is its dispatched records instrument.

**And a near-miss was caught rather than suffered:** the prior director session
**archived before issuing this dispatch**, which the **2026-08-31 director
startup** noticed and repaired by dispatching this lane. Recorded as a
**dispatch-vs-launch near-miss caught by startup**, explicitly **not** as a
failure streak — the check that v14 added as step 0 (*look for the BRANCH, not
a plausible-sounding commit*) is the same check that catches this class, and
it worked from the other direction this time: not "was a dispatched lane
launched?" but "was a completed sitting's dispatch issued at all?"
## What moved — v15 CYCLE (v15 record, RETAINED as history) (`def338e..69ae4dc7`, "the ruling-execution cycle")

**Read E-1…E-4 as one act.** They are the 2026-08-30 PM sitting's four rulings,
all executed inside a single 103-minute window, three of them by the same
records lane and one by the calibration lane it chartered.

### E-1 · 🟢 R-1 EXECUTED — THE NYISO FRONTIER CITATION IS ANNOTATED, RETIRING THE BOARD'S TOP QUEUE ITEM

v14's owner-queue item 1 (and v13's item 7 before it) was the `frontier` block
in `keepers/NYISO.json` citing **superseded nyiso-152** while the designated
keeper had moved 152 → 155 → 157. **Ruled R-1 and executed** (#4342,
`4c63b05`): the block now carries `currency_annotation_2026-08-30`, which
states in terms that the inline *"KEEPER: 2026-08-22-nyiso-152-duty-complete,
determination CALIBRATED"* describes **the keeper AT DECLARATION, not the
current keeper**, names both subsequent moves, and records the current
determination as **NOT-YET**.

**The shape of the fix is the point.** It is an **annotation, not a rewrite**:
no declaration text above it is altered, `keeper_at_declaration` stays, and the
ratification itself is explicitly unchanged. That is the correct disposition
for a dated owner act — the record of what was ratified stays true, and the
currency question is answered beside it rather than by editing history. **One
field, zero solves, zero determination change.**

**The class it belongs to is NOT retired.** Evidence PROSE is still gate-checked
nowhere: `check_mechanism_matrix.py` validates `keeper:` stamps and §5.x prose
headers and passes while citation text beside them goes stale. This instance is
closed by hand; the next one will also have to be. **Whether any gate should
read evidence text remains unruled** — it stays on Watch and is now the queue's
standing structural question rather than a live defect.

### E-2 · 🔵 R-2 EXECUTED — ercot-240 CHARTERED AND COMPLETED THE SAME DAY: THE "DEMAND GAP" IS THE DC-TIE NET IMPORT IDENTITY

Chartered at the sitting, precommitted (#4341, `0a7ed18`), measured and closed
within hours (#4344 probe + JSON, #4345 FINDING, #4348 calibration-log entry).
**ZERO-SOLVE** — every number read from committed artifacts and raw measured
inputs (the `ercot236_k33_clip` keeper sidecar, the EIA-930 wide extract, the
ERCOT MIS native-load record NP3-565-CD, the committed actuals parquet, the
committed ercot-239 JSON), with the model demand series recomputed through the
engine's own loader and gated against the sidecar.

**The adjudication:** the event-hour "demand gap" is the **DC-TIE NET IMPORT
IDENTITY, exactly and everywhere.** The model's demand input is **NOT**
understating real demand — it serves the measured net-generation boundary,
correctly. All three chartered demand-source candidates (4CP/load response,
the 930-vs-MIS boundary, weather-hour alignment) are **REFUTED as gap
carriers** under the precommitted rules, and the phase-0 §0.5/§4 framing is
re-adjudicated.

**Why this is a good outcome and not a null.** A "demand gap" that had been
read as a *model input defect* turns out to be an **accounting identity** —
the boundary the model is built to serve. That closes a candidate root cause
for the ERCOT 2023 C3a residual by showing it was never a cause at all, at the
cost of one zero-solve day. Rule 1 `[R-STRUCT]` reading: the mechanism was
already right; the framing was wrong.

### E-3 · 🟢 R-3 EXECUTED — caiso-222 Q1 IS **TERMINAL REST + MAP**

Recorded #4342 (`634927a`, the CAISO calibration log + the packet §9). Q1 is
ruled **§1(c) option 3 — TERMINAL REST + MAP**: the CAISO C3a residual
(**+12.5 % 2024 / +15.5 % 2025**, re-derived at the pin below) is designated
**ATTRIBUTED AND CLOSED at this representation grain**, with a decision map
attached rather than an open investigation.

This is the disposition v14's queue item 7 was waiting on. **It does not make
CAISO CALIBRATED** — the determination stays `NOT-YET` and the C3a fails stay
published at full magnitude — it rules that *further pursuit at this grain is
not the route*. Owner ruling 5 (*C3a must genuinely pass; NOT-YET is the honest
fallback*) is untouched and still governs.

### E-4 · 🔵 R-4 EXECUTED — Q2 ROUTES (i)+(iii) ARMED/CHARTERED, (ii) CEII **DECLINED**; ROUTE (iii) RAN AS caiso-223 THE SAME DAY

**The ruling** (#4342): route **(i) ARMED** — W-1/W-2/W-3 become **standing
watch items**, each arming only with its own precommit, and the armed watch
tests are the **ONLY sanctioned re-checks** of the Q1 terminal rest. Route
**(iii) CHARTERED** as the sub-zonal topology program's opening round. Route
**(ii) DECLINED** — CEII access (FERC 18 C.F.R. §388.113, the A-1/A-2/A-3
filing/agreement class); the option stays on the record for any future owner
act.

**The execution** — caiso-223, #4347 (precommit, criteria/tiers/gates fixed
*ex ante*) then #4350 (artifacts + FINDING + log). **ZERO-SOLVE; nothing
armed; keeper `2026-08-26-caiso-220-c1-crosswalk` UNCHANGED.** What it
delivered:

- **Partition PROPOSED AND ADJUDICATED (P-A′)** — one new San-Joaquin-Valley
  pocket zone **FSNO** between two element-grounded cuts, replacing the single
  Path-15 link that the **DMM record says does NOT bind**, while the two cuts
  that **DO** bind are invisible at hub grain. That is a rule 14
  `[R-ACCURATE]` argument made against a measured record, not a residual.
- **Membership DERIVED** — 42 crosswalk plants / **2,701 MW** into FSNO, pnode
  map committed, **zero silent defaults**.
- **Load split MEASURED** — the caiso-172 ATL_LDF method, 3-way: **FSNO
  0.1326 / ZP26 0.1148 / NP15 0.7526** of DLAP_PGAE. **Gates 13/13 PASS**, and
  the two-way control reproduces the committed caiso-172 artifact **EXACTLY**.
- The round **ends on a sufficiency gap list** rather than an arm.

**Declared a REPRESENTATION-GRAIN PROGRAM, NOT A LEVER.** That is the
distinction rule 1 `[R-STRUCT]` turns on, and it is why the round is legible:
it changes what the model can *see*, and it is required to earn its arming
separately. Its successor **caiso-224** is the cycle's live lane (#4357
precommit merged; #4360 open — the gated `caiso_fsno_subzonal_topology`,
**default off**, plus a G-CTRL bit-zero comparator probe).

### E-5 · 🟢 THE ALIGNMENT BREAK v14 REPORTED IS REPAIRED — BY MARKER WITHDRAWAL, NOT BY A CALIBRATION WIN

**Re-derived at the pin from `calibration-complete.json`, the six keeper
shards, and the forecast seed — not carried.**

The capx **Q5-W** lane (#4343) withdrew **NYISO's `complete` marker** to the
`withdrawn` block, on the Q5 uniform rule — *a `complete` marker cannot stand
on a NOT-YET keeper* — applying the 2026-08-06 CAISO precedent evenly. **This
is a DIFFERENT program's act on the shared marker file**, taken under its own
charter; it is recorded here because this board's instruments read that file.

| instrument | v14 (`0a5e896`) | v15 (`69ae4dc7`) |
|---|---|---|
| CALIBRATED | {PJM, NEISO} | **{PJM, NEISO}** |
| `complete` block | {NEISO, NYISO, PJM} | **{NEISO, PJM}** |
| forecast gate (a) passers | {PJM, NYISO, NEISO} | **{PJM, NEISO}** |
| `frontier` | {PJM, NYISO, NEISO} | **{PJM, NYISO, NEISO}** ⬅ **unmoved** |

**Three instruments now agree; `frontier` is the lone outlier.** Two honest
readings, both of which belong on the record:

1. **The break did not close by NYISO improving.** NYISO's keeper, its
   `NOT-YET` determination and its 8/5/3/0 scorecard are all byte-unchanged.
   The instruments agree because one of them was *withdrawn*.
2. **The misalignment moved rather than vanished.** `frontier` still contains
   an ISO that is neither CALIBRATED nor `complete`. Unlike v14's break, this
   one is **not** a governance hazard — a ratified frontier is a dated
   statement about lever-queue exhaustion, not a holdout authorization, and
   nothing is spendable on it. But it *is* the fourth instrument disagreeing
   with the other three, and **nothing in the repo checks that.**

**`final` remains EMPTY (`_note` only). No ISO has ever spent a locked-test
year** — re-verified below, not restated.

### E-6 · 🔵 FOUR CALIBRATION ROUNDS OPENED, ONE A/B CLOSED REJECTED — AND NOT ONE OF THEM MOVED A KEEPER

The cycle's calibration content, all of it zero-solve or kill-gated, none of it
promoting:

| lane | PRs | what landed |
|---|---|---|
| **ercot-239 r2 → r3** | #4351, **#4356**, #4359 | precommit round 2 (graded measured `peak_ladder` under the calibrated top, August steepness) → Stage-A census + **Amendment 1** (G-A(iv) proxy re-based to the measured invariant) → Stage-B A/B driver → **REGISTERED AND REJECTED** (`2026-08-30-239-graded-ladder`, ERCOT, **2023 only**): kills clean, officials collapse to pre-k33, spur **74 → 11**; escalated, **keeper untouched**. Then r3 precommit — h3068-2024 bounded diagnosis |
| **ercot-241** | #4349, **#4358** | Phase-0 precommit for the off-core conduct-parameterization screen → **phase-0 MEASURED**: kills clear, **Phase-1 gate OPEN**, dependence is position/participation-carried |
| **nyiso-158** | #4339 | phase-0 winter-face diagnosis: the binding-depth differential **is the measured Transco TTC step**; **no measured driver reaches the sharpened iroquois re-open bar** (first leg closed, Leg-2-only); **C3b-2025 is wholly the two faces** (98.4 % of squared error; either face alone restores the band); the CE-util overshoot is **not** an envelope defect |
| **nyiso-159** | #4352 | phase-0: the NYISO loss component measured on the completed 36-month record, **+ PREREG** of the zonal loss surface |
| **caiso-223 → caiso-224** | #4347, #4350, #4357, **#4360 (open)** | E-4 above; successor gated **default off** |

**The pattern is worth naming: this cycle bought five sharpened addresses and
one clean rejection for zero keeper risk.** v14's durable lesson — *a negative
result with a bitwise proof beats a positive one without* — is not merely
carried this cycle, it is **the whole cycle**. The ercot-239 graded ladder was
rejected **on its own pre-registered gates**, exactly as v14's nyiso-157
iroquois companion was; the model of "arm, measure, kill, escalate, keeper
untouched" now has four consecutive instances across three ISOs.

**miso-190's registration watch stays OPEN** — verified at the pin, not
assumed: no `miso-19*` sidecar exists in `frontend/data/backcast/registry/`
(newest MISO sidecars are `188-control` / `188-rvsscope`), and the branch
`claude/miso-190-backcast-calibration-okt1cn` sits **139 commits behind main
with nothing unmerged**. Third consecutive cycle open.

### E-7 · 🔴 NEW — THE ERCOT STAGE-0 GOLDEN'S PROVENANCE RUN WAS PRUNED OUT FROM UNDER IT

Discovered by re-deriving the Stage-0 table rather than reading v14's, and it
is the cycle's one genuinely adverse finding.

`results/regression-goldens/perfb-stage0/manifest.json` maps the ERCOT golden
to `keeper_id: 2026-08-15-ercot204-rule26-delete`. **That run's registry
sidecar was DELETED this window** — commit `e51a8a7d` (#4356), under **top-15
retention**, in the same commit that registered the 239 graded ladder. Its
bundle directory `results/calibration/ercot204_rule26_delete` went with it.

**The prune itself is legitimate and correctly executed** — top-15-per-ISO
retention is rule 15 `[R-DASHBOARD]` policy, the run was long superseded, and
parity exits 0 at the pin. **The collision is with WS3, which nothing checks.**
Stated precisely, and verified at the pin:

- At the pin, **none of the five golden `keeper_id`s resolves to a registered
  sidecar.** ERCOT's is the one that demonstrably **left this window** (its
  deletion commit exists and is named above); for the other four, no commit
  ever touched a registry path under those exact ids, so they were never
  registered under their manifest names — a **different** condition, recorded
  as such rather than merged into one alarming sentence.
- The manifest is **byte-unmoved**: `git diff` over
  `results/regression-goldens/` returns **empty** across all 66 commits.
- **The per-file `content_hashes` are unaffected and remain the verification
  instrument** — every manifest entry carries them, and they do not depend on
  the registry.

**So nothing is lost that was not already gitignored, and no gate went red.**
What changed is the *provenance chain*: the ERCOT golden now names a run with
**no committed registry record at all**, on top of a manifest `git_sha`
(`af1ccb6`) that **still does not resolve** (re-checked at the pin). Whoever
un-parks WS3 now has two broken provenance links on the ERCOT row, not one.
**Recommended, and cheap: capture PJM first anyway (it has no golden and the
only clean scorecard), and treat every re-capture as re-establishing
provenance rather than refreshing it.**


## Keeper table (read from `frontend/data/backcast/keepers/<ISO>.json` and `status/<ISO>.js` at `d44446e0`)

Determinations and grade summaries parsed live from the status shards at the
pin. **C3a(RT) is the load-weighted mean-LMP error against RT actuals, per year
2023 / 2024 / 2025** — printed for every ISO because it is the criterion every
NOT-YET fail set contains, and printing it only for the failures hides how
narrow the margins are. ERCOT's row is the board's TWO-CONFIG entry (v14 D-2):
the grade column shows forward-span / carve-out / registered-3-year reads.

**Five of six `keeper` fields are byte-unchanged from v16 and that is a
re-derivation, not a carry** — all six compared byte-for-byte at `54ca19ae` and
at the pin, all six determinations and grade summaries re-parsed, all eighteen
C3a(RT) magnitudes re-read from the shards. **The sixth, MISO, moved
(188 → 191)** and its whole row is re-derived (F-7). **ERCOT's determination
column changed WITHOUT its keeper moving** — the ercot-246 ruling made the
ISO-level read the worst config over the designated spans, so the shard now
renders **CALIBRATED** while its grade summary still carries the registered
3-year read (8 / 5 / **2** / 1). Rubric **v3.5** on every shard.

| ISO | Designated keeper | Determination | Grade (scored/target/fails/ledgered) | C3a(RT) 2023 / 2024 / 2025 |
|-----|-------------------|---------------|---|---|
| ERCOT | `2026-08-25-234-eastex-identity` (FORWARD, 2024–2025) **+ `2026-08-25-236-swcap-clip-k33`** (2023 carve-out) — TWO-CONFIG | ⬅ **ISO-level `CALIBRATED`** (ercot-246 partition rollup) · forward `CALIBRATED` on span · carve-out `CALIBRATED` · **registered 3-yr `NOT-YET`, published untouched** | 8 / 5 / **2** / 1 (the registered 3-yr read) · forward 8 / 7 / 0 / 1 · carve-out 8 / **8** / 0 / **0** | **−39.7 % F** (the carve-out's year) / −0.2 % / −7.9 % |
| CAISO | `2026-08-26-caiso-220-c1-crosswalk` | `NOT-YET` | 8 / 6 / **1** / 1 | +4.0 % / **+12.5 % F** / **+15.5 % F** |
| PJM | `2026-08-15-pjm-162-inputclock` | **`CALIBRATED`** | 8 / **8** / 0 / **0** | +6.2 % / −0.8 % / −7.7 % |
| NYISO | `2026-08-30-nyiso-159-loss-surface` | `NOT-YET` | 8 / 6 / **2** / 0 | +2.3 % / −1.2 % / **−11.5 % F** |
| NEISO | `2026-08-17-neiso-99-joint-p1` | **`CALIBRATED`** | 8 / 7 / 0 / 1 | +3.1 % / +5.7 % / +1.7 % |
| MISO | ⬅ **`2026-08-30-miso-191-bexit`** (was `188-rvsscope`) | `NOT-YET` | 8 / 6 / **1** / 1 | ⬅ **+0.1 %** / ⬅ **−4.6 %** / **−12.3 % F** |

| ISO | v17 cycle (`54ca19ae..d44446e0`) |
|-----|--------------------------------|
| **ERCOT** | **The window's biggest state change, and it is not a keeper.** ercot-245's Phase-0 census **KILLED the per-class commitment-state bound** (K-A/K-C/K-T all fire; **Phase-1 not licensed**); **ercot-246** ruled that a partitioned keeper's ISO-level determination is the **worst config over the designated spans**; **ercot-247** took the **first ERCOT rule-22 `complete` marker ever, plus a `frontier` declaration**, in one owner utterance (F-5). Keeper **unmoved**. **R-D rested its wind entry question with a map** (F-1). Its **carve-out config still has no stage-0 golden** |
| **CAISO** | **UNMOVED.** caiso-226 (OFO intake) + **caiso-227** (C3a-2025 root-cause / PS intake) landed; **caiso-228's SoCalGas OFO arm DIED AT GATE D1, no solve.** Terminal rest undisturbed; C3a-2024/2025 stand at +12.5 / +15.5 % |
| **PJM** | **UNMOVED and untouched for a NINTH consecutive cycle — and this cycle it was AUDITED rather than changed.** pjm-164 ran the C3c program's **Q1 against PJM's own CALIBRATED keeper** and returned **REAL** (F-2) — the audit that could have invalidated it, run and survived. Still the only 8/8 zero-caveat scorecard and the only CURRENT stage-0 row |
| **NYISO** | **No keeper motion; FOUR records sessions.** nyiso-162 (R-C re-verify) · nyiso-163 + **163b** (the **AORR access route PERMANENTLY CLOSED** by owner decision; nyiso-97 re-open condition 3 **withdrawn**; the C3c program opened) · **nyiso-164 = Q2 CONFIRM** (F-2). **R-F parks the nyiso-161 card behind a trigger that has already fired** (F-3); **R-G closes leg2 by archive** (F-4). Determination unchanged: NOT-YET {C3a-2025 −11.5 %, C3c} |
| **NEISO** | **UNMOVED and untouched on the backcast.** Its entire residual remains the **`final` grant itself** — still **DATA-BLOCKED** on the 2025 EIA-923 FINAL vintage. Now one of **three** `complete` ISOs, and — on the *forecast* board, a different program's — the **first ISO whose full-solve authorization gate is OPEN** (F-6) |
| **MISO** | **THE CYCLE'S ONLY PROMOTION: 188 → 191** (binning-aware exit-cohort delivery). C3a 2023 **+3.5 → +0.1 %**, 2024 **−4.3 → −4.6 %**; **C3a-2025 −12.3 % unchanged and still the lone fail**. **miso-192** (D-4 posture) and **miso-193** (`cc_duct_peaking`, registered as a rejected probe with sidecars, cell **U → K**) also landed. Its stage-0 gap is now **two promotions** deep — the deepest on the board |

**Markers at `d44446e0`, re-read live this cycle:** `complete` = ⬅ **{ERCOT,
NEISO, PJM}** (ERCOT NEW) · **`final` = EMPTY (`_note` only)** ·
**`holdout-freeze.json` `active: true`, TIER-SCOPED to `locked_test` alone** ·
`withdrawn` = **{NYISO, CAISO}**. All three `complete` entries are **re-keyed to
their live keepers** (rule 22 D-5(b)); the one ISO that promoted this cycle
(MISO) **holds no marker**, so **no re-key was owed anywhere**. ERCOT's new entry
carries a **determination re-verification performed without a solve**
(`calibration_verdict.py`, committed artifacts, both configs live), and
`audit_keepers` **M1b was extended in the same commit** to recompute the
partition rollup live rather than read the shard's own assertion.
**`audit_keepers.py` returns PASS: 0 failures, 0 warnings** at the pin, run not
quoted.

**NO ISO HAS EVER SPENT A LOCKED-TEST YEAR** — re-verified at the pin by walking
every registry sidecar, not restated. Across all **58** registered sidecars the
solve-year histogram is **{2022: 2, 2023: 56, 2024: 52, 2025: 52}** (per-ISO
sidecar counts: ERCOT 15, MISO 15, NYISO 15, PJM 5, CAISO 4, NEISO 4). The scan
for any year in {≤2018, 2019, 2026} returns **NONE**. The only out-of-training
registrations remain the **two authorized 2022 validation touchpoints**
(`2026-08-05-pjm-2022-touchpoint`, `2026-08-06-neiso-2022-corrected-basis`).
NEISO's one-shot stays **NEVER GRANTED, not spent** (D-23). *Motion note: the
sidecar total is flat at 58 — four MISO additions (miso-191 pair, miso-193 pair)
against four MISO prunes under top-15 retention — so the span did not widen.*
**ERCOT's new `complete` marker does not change this line**: it authorizes the
validation tier only, and ERCOT has spent nothing. This line is re-verified and
republished every cycle because WS5 Job 1 found the public site asserting its
exact opposite for two weeks.

**Determinations: ERCOT (ISO-level), PJM, NEISO `CALIBRATED` · CAISO, NYISO,
MISO `NOT-YET` — with ERCOT's registered 3-year read still NOT-YET and still
published.** **C3a appears in every NOT-YET fail set, and for CAISO and MISO it
is the ONLY failing criterion**; NYISO adds only C3c. **The alignment position
changed again even though the CALIBRATED set only gained one member** — see F-6.

## Workstream rollup

**NO WORKSTREAM MOVED this cycle — the motion v16 recorded was one window,
not a trend.** Verified rather than assumed over the full
`54ca19ae..d44446e0` window (**93 commits, 36 merged PRs**):
`git diff --name-status` returns **EMPTY for all three workstream surfaces at
once** — `.github/workflows/`, `results/regression-goldens/` and `docs/audit/`.
**The workstream-surface diff of this cycle is the empty set**, so every
completion figure below is carried unchanged by measurement rather than by
assumption, and every row's blocker is the same blocker.

| WS | State | Completion | Blockers / next |
|----|-------|------------|-----------------|
| WS1 `AUDIT` | AUDIT-A **completed** (#3991). Rows **O8, O5, O4 CLOSED/RESOLVED**; **O6** is standing policy; 🟢 **O7 CLOSED this window** (#4377) — the Door-2 attribution harness built *and* exercised, HP-1 hash-proven bit-identical, keeper untouched | **In progress ~95 %** (unchanged — `docs/audit/` byte-untouched this window) | **AUDIT-B still gated at G3 — waiting by design, and that gate is what caps this row**, not any remaining A-half work. O7's closure leaves no audit row carrying an owner action this board tracks |
| WS2 `DEBUG` | **COMPLETED** — DEBUG-A ✓, DEBUG-B ✓, pjm-162 promoted, landing-verify green on merged main | **Completed** | none; no DEBUG-C continuation chartered |
| WS3 `PERF` | PERF-A ✓. **PERF-B PAUSED BY OWNER.** 🟢 Stage-0: **6 of 6 ISOs captured** — PJM taken this window under Card 1. Changes (c)/(d)/(e) merged, (a)/(b) unstarted | **Paused ~78 %** (unchanged — `results/regression-goldens/` byte-untouched this window) | **Still paused, and still blocked TWICE at G2.** **1 of 6 goldens matches its keeper** (PJM), unchanged. 🔴 **The provenance defect is unchanged in kind and WORSE in fact**: `af1ccb6` remains *overwritten rather than resolved* (manifest `git_sha` `1cfea72`, `git_dirty: false`, one sha for six captures taken at six trees), **five of six captures' provenance runs are still absent from the registry**, and **MISO's stale row is now TWO promotions deep** (`miso-160-wefor-shape` captured vs `miso-191-bexit` live) |
| WS4 `DOCS` | DOCS-A **completed** (#3999 + #4005); DOCS-B held | **In progress ~60 %** | **DOCS-B gated at G2 — waiting by design** |
| WS5 `SITE` | **Job 1 (site factual repair, pre-G3) COMPLETE ACROSS BOTH PASSES** (#4120/#4121, #4187/#4191). Job 2 = **SITE-A**, not started | **Job 1 COMPLETED · Job 2 not started** | **SITE-A gated at G3 — waiting by design.** Deferral list unchanged |
| WS6 `BLOAT` | Prunes B-1..B-8 merged; **BLOAT-2 CLOSED**; **BLOAT-3 ADJUDICATED and EXECUTED** (BLOAT-S2, −444.5 MiB at tip). The chartered work stays completed | **Completed (charter) · gate 🟢 GREEN** | **🟢 GREEN at the pin** — `check_registry_payload_parity.py` **exit 0** (58 runs checked, 93 bundle dirs swept, 0 known-unsynced tolerated), holding across **four MISO registrations and four MISO prunes** this window (net sidecar total flat at 58). The class-level carve-out (B-8) **still does not exist**; allowlist stands at **26** named entries |
| — `BENCH FRESHNESS` | `check_bench_freshness.py` / audit S1 lineage | **🟢 exit 0 at this pin — 0 STALE of 20 parts, but 19 of 20 WITH ENGINE DRIFT** | 🔴 **The WARNs returned exactly as v16 predicted, and nothing about the instrument was repaired.** v16's rollup predicted their return "on the first engine commit dated 2026-08-31 or later"; its own post-pin block then measured **20 of 20**. At this pin the reading is **19 of 20 at 3 engine commits** — and the one part that does *not* WARN is **MISO/2023**, which the miso-191 registration **rewrote** (`1b419b7b`, 2026-08-31 00:33 UTC), making it newer than those commits rather than fresher in any repaired sense. The mechanism v16 diagnosed stands as diagnosed: day granularity, plus a **date-kind mismatch** — the checker reads a part's date with `%ad` (**author**) and filters engine commits with `--since` (**committer**). **The dispatch asserted "0 STALE 0 drift"; that is not what the checker returns here** (F-8). Not gated either way; regenerate before trusting a *marginal* C1 verdict |
| — `GOLDEN-TIER-FIX` | **COMPLETED and independently verified** (#4014); first cron RED, diagnosed + fixed same-day (#4071), verified by full local four-step replay | **Completed · tier PARKED** | **🅿️ PARKED BY OWNER RULING 2026-08-22, unchanged.** CI proof **deliberately unspent**. Consequence: byte-green cannot be CLAIMED for G2 while the tier is paused — **and the new PJM capture cannot be certified byte-green either** |
| — `MATRIX GUARD` | rule 26 `[R-MECH-MATRIX]` CI enforcement | **🟢 GREEN at this pin** | `check_mechanism_matrix.py` **exit 0**, run not quoted: integrity OK across the base file + **6 ISO shards**; anchors **194 field + 49 row + 152 path** (v16: 194/49/151 — one new path anchor, no new `ScenarioConfig` field), 0 unresolvable beyond the ratchet; **keeper stamps AND §5.x prose headers match every `keepers/<ISO>.json`**, held across the MISO promotion **and across this lane's own R-D evidence-string edit** |

## Stage-0 golden staleness (RECOMPUTED at `d44446e0` — never read from a table)

Re-derived at the pin from `frontend/data/backcast/keepers/<ISO>.json` and
`results/regression-goldens/perfb-stage0/manifest.json` (`git_sha`
**`1cfea72`**, `git_dirty: false` — **byte-unchanged this window**; the whole
`results/regression-goldens/` tree is untouched across `54ca19ae..d44446e0`).
Each captured bundle mapped back to its keeper through the manifest's own
`keeper_id` field, not by name — and every row's registry-presence column
re-tested at this pin rather than carried.

**🟠 THE TABLE DID NOT MOVE, AND ONE ROW GOT DEEPER.** No capture was taken;
MISO promoted, so its gap widened from one promotion to **two**. Coverage is
**1 current / 5 stale**, unchanged in count. **The consequence for G2 is
unchanged: byte-green still cannot be CLAIMED, so G2 leg 1 keeps BOTH parked
dependencies** — WS3/PERF-B *and* the golden tier.

| ISO | Golden captured against | Provenance run in registry | Designated keeper at `d44446e0` | Verdict |
|-----|-------------------------|---|--------------------------------|---------|
| **PJM** | 🟢 `2026-08-15-pjm-162-inputclock` (captured in the v16 window, #4369) | ✅ **PRESENT** | `2026-08-15-pjm-162-inputclock` | 🟢 **CURRENT — 0 promotions past capture.** Held a second cycle; PJM's keeper has now been still for **nine** |
| ERCOT | `2026-08-15-ercot204-rule26-delete` | ❌ MISSING (pruned `e51a8a7d`, #4356) | `2026-08-25-234-eastex-identity` **+ 236 carve-out** | **🔴 STALE**, and full ERCOT coverage still needs **TWO** captures — the carve-out config has none |
| NEISO | `2026-08-14-neiso-93-envelope` | ❌ MISSING | `2026-08-17-neiso-99-joint-p1` | **STALE.** The re-stamp-not-re-solve shortcut was established for **neiso-97 only**; re-establish before relying on it |
| CAISO | `2026-08-16-caiso-197-w2-r5` | ❌ MISSING | `2026-08-26-caiso-220-c1-crosswalk` | **🔴 STALE** |
| MISO | `2026-08-16-miso-160-wefor-shape` | ❌ MISSING | ⬅ `2026-08-30-miso-191-bexit` | **🔴 STALE, and it DEEPENED this window** — the cycle's one promotion; the deepest gap on the board |
| NYISO | `2026-08-16-nyiso-140-layup-exclusion` | ❌ MISSING | `2026-08-30-nyiso-159-loss-surface` | **🔴 STALE** (deepened in the v16 window, unchanged here) |

**Count: 1 current / 5 stale / 0 without a golden — 1-of-6 effective coverage,
unchanged from v16.** *(Coverage counts ISOs, not configs: ERCOT's 2023
carve-out config has no golden of its own, so **full** coverage is 7 captures,
not 6.)*

**On the promotion-gap counts, stated honestly rather than carried:** the
absolute "N promotions past capture" figures **are not re-derivable from
committed bytes at this pin**. The per-ISO keeper shards' git history begins
**2026-08-26** (the 2026-08-16 history rewrite plus the per-ISO shard split
truncated it), while the captures date 2026-08-14/15/16, and the shards'
embedded supersession chains reach only three deep. What **is** derived here:
each row's **verdict** (exact, from `keeper_id` vs the live `keeper`), the
**registry presence** column, and the **motion since v16** (MISO **+1**, every
other ISO **+0**, byte-compared). v15's absolute figures — ERCOT six, MISO
eleven, NYISO ten, CAISO two, NEISO two — are **carried under v15's label, not
re-asserted as this board's measurement**; NYISO's became v15's ten + 1 at v16
and is unchanged here, and MISO's becomes **v15's eleven + 1**.

- **PJM's capture keeps paying, and the reason is worth restating:** it was
  cheap because that keeper had been still for seven cycles — the exact
  condition the restart checklist says a re-capture pass needs. **The five
  stale rows are the five whose keepers keep moving**, and MISO — the ISO that
  promoted this cycle — is the one whose gap grew.
- **🔴 "Which tree is the golden OF" is now WORSE-POSED, not better.** One
  top-level `git_sha` serves six captures taken at six trees, and it was
  rewritten to the newest capture's. **The per-file `content_hashes` remain the
  verification instrument** — the only one — and a re-capture pass should record
  provenance **per entry**, inside the manifest (F-5; checklist item 11).
- **The partition still adds a capture-coverage concept the manifest does not
  have:** one ISO, two designated configs. **A re-capture pass that takes one
  ERCOT golden is still not full ERCOT coverage.**
- 🟢 **The checklist-item-4 evidence was INDEPENDENTLY RE-MEASURED this cycle,
  and it strengthened.** v16 recorded nyiso-160's bit-identical HEAD replay.
  R-C's re-verification (F-4) re-derived the same identity from committed bytes
  at a later head — **max |Δ| = 0 over 1,043,280 hourly data rows**, and, the
  new part, **the identity held ACROSS A SOLVER-VERSION CHANGE** (HiGHS 1.15.1
  vs 1.14.0, plus pandas/pyarrow/pydantic differences). That still does not
  establish the re-stamp-not-re-solve shortcut for any *golden* — a golden is a
  capture of a config at a tree, not a replay — but it is now a two-session,
  two-head, cross-solver result rather than a single observation.

## Gates

**All five re-run at the pin. Exit codes captured directly, never through a
pipe; outputs read, not quoted from any previous board — and three of the five
readings differ from what the dispatch asserted (F-8).**

| gate | exit | reading at `d44446e0` |
|---|--:|---|
| `audit_keepers.py` | **0** | **PASS — 0 failures, 0 warnings**, now over `complete` = **{ERCOT, NEISO, PJM}**, held across the MISO promotion, the new ERCOT marker **and the M1b partition-rollup extension that landed with it** |
| `check_registry_payload_parity.py` | **0** | **OK — 58 runs checked, 93 bundle dirs swept, 0 known-unsynced tolerated** (**not** the 60/95 the dispatch asserted; held across four MISO registrations and four MISO prunes, net flat) |
| `check_mechanism_matrix.py` | **0** | integrity OK, base + **6 ISO shards**; anchors **194 field + 49 row + 152 path** (v16: 194/49/151; **no new `ScenarioConfig` field this cycle**); keeper stamps and §5.x headers match every shard. **Re-run after this lane's own R-D evidence-string edit: still exit 0** |
| `check_forecast_staleness.py` | **0** | **Δ = 1 of 10** (WARN-level, never blocking) · **81 stamped / 49 scored** board-wide (v16: 73/41) · **31 of 50 verdict stamps undated** · **24** distinct config epochs (v16: 20) · board inputs **all present** |
| `check_bench_freshness.py` | **0** | **20 parts checked, 0 STALE — and 19 of 20 WITH ENGINE DRIFT at 3 engine commits.** The dispatch asserted "0 drift". See F-8 and the BENCH row |

**Two readings moved and both are cross-program, not this program's:** staleness
**stamped/scored 73/41 → 81/49** and **epochs 20 → 24** (the forecast namespace
absorbed the capx desk's D3/D4-I3/D8-RE/T3-golden window); bench engine-drift
**20 of 20 → 19 of 20**, the one exemption being MISO/2023's rewrite rather than
any repair. **The persistent WARN is unchanged and is not the Δ: 31 of 50
verdict stamps record no scored-at date**, so their freshness is UNKNOWN
regardless of what the newest scored one says — and the **24 distinct config
epochs** line is the one worth reading twice: runs on that board are being
compared across two dozen different config identities.

- **G0** adopted ✓ (2026-08-13) · **G1** DECLARED ✓ (2026-08-16, #4006).
- **G2 — UNREACHABLE, still behind TWO owner parks.** Leg 1 is *PERF-B merged
  byte-green*; PERF-B is paused by owner decision **and** the golden tier that
  would certify byte-green is parked by owner ruling. The legs:
  1. **PERF-B merged byte-green** — **still doubly blocked, but the underlying
     coverage improved for the first time**: 6 of 6 captured (PJM taken under
     Card 1), **1 current / 5 stale**, (c)/(d)/(e) merged, (a)/(b) unstarted,
     the golden tier parked so byte-green cannot be claimed for *any* capture
     including the new one — and the manifest's provenance sha is now
     resolvable but serves six captures from one field (F-5).
  2. **One completed fast-tier-green `ci.yml` run** — **🟢 OBTAINABLE AND
     DECISION-FREE, for a third consecutive cycle.** Both CI guards exit 0 at
     the pin and have now held green across a 67-PR window, four registrations,
     three prunes and a golden capture. **This is the one G2 leg closeable
     today without an owner decision**; re-run the gates rather than trusting
     this line.
  3. **A keeper freeze** — **owner call, DEFERRED BY OWNER DIRECTION.** 🆕 **The
     evidence moved again, and this time it cuts back toward v14's reading:**
     v15's "zero promotions" window was **one data point, not a trend**, exactly
     as it warned — this window promoted once and ran six calibration lanes and
     thirty PRs. **But Card 1 proves the freeze is not a precondition for a
     capture**: one was taken inside a busy window, in a lane whose keeper
     happened to be still. **The scoped-capture route is demonstrated; the
     freeze question is now only about the five stale rows.**
  4. **Branch-protection flip** — owner action, memo ready.

  On declaration the PM notifies the FFR desk (Q.2 battery).
- **G3** — unchanged: after G2, **DOCS-B** + the **BLOAT leg**. BLOAT's charter
  is satisfied (#4031 + #4047) and its parity gate is **green at the pin**, so
  the leg reads *satisfied-in-charter and gate-green-in-fact* for a third
  cycle. The golden-tier proof leg is satisfied by #4014 + the green dispatch
  **as evidence**, though the tier itself remains parked.
- **G4** — unchanged: SITE-A + AUDIT-B. **WS5 Job 1 is not a G4 leg.**

## Watch

- **🅿️ GOLDEN TIER — PARKED BY OWNER RULING 2026-08-22, unchanged for six
  cycles.** The #4071 fix is merged and locally replayed green; the CI proof is
  **deliberately unspent**. Record it as a park, not a blocker — and record the
  consequence: **the PJM golden — the board's only current row — still cannot be
  certified byte-green**, because the tier that would certify it is paused. It
  has now held that status for two cycles.
- **🔴 SHARPENED — THE STAGE-0 MANIFEST'S PROVENANCE IS ONE FIELD FOR SIX
  CAPTURES, AND IT WAS OVERWRITTEN THIS WINDOW.** F-5. `af1ccb6` is gone but
  was never resolved: the Card-1 capture rewrote the single top-level `git_sha`
  to its own tree (`1cfea72`, resolvable and in main), so the **five older
  captures now carry a sha that resolves and is wrong** — harder to notice than
  one that did not resolve. There is **no per-entry provenance sha**. Fix it on
  the manifest side, per entry.
- **🔴 SHARPENED — THE RETENTION/GOLDEN COLLISION IS FIVE-WIDE, NOT ONE.**
  v15's E-7 reported ERCOT; re-deriving found **five of six captures' provenance
  runs absent from the registry**, all five already absent at the v15 pin
  (v16 F-5). Only PJM's (taken in the v16 window) has a registered provenance run — re-tested at this pin, unchanged.
  The registry-retention policy and the WS3 manifest reference the same run ids
  and **know nothing about each other**; every gate stayed green throughout,
  which is the point. **Do not "fix" this by exempting golden runs from
  retention** — that re-creates the parity gate's dead-bundle class.
- **🔴 CONFIRMED BY PREDICTION — THE BENCH-FRESHNESS ENGINE-DRIFT SIGNAL IS
  TIMEZONE- AND DAY-BOUNDARY DEPENDENT.** v16 predicted the WARNs return "on the
  first engine commit dated 2026-08-31 or later"; at this pin **19 of 20 parts
  WARN at 3 engine commits**, and the one exemption (MISO/2023) is a part the
  miso-191 registration **rewrote**, not one that was repaired. The v16
  diagnosis therefore stands **confirmed rather than argued**, and it carries the
  sharpening its post-pin block added: a **date-kind mismatch** (the checker
  reads a part's date with `%ad`, author, but filters engine commits with
  `--since`, committer) layered on the day-granularity issue. The mechanism, as
  first stated:
  the checker compares a `--date=short` last-commit date against
  `--since="<date> 23:59:59"` evaluated in the *runner's* local timezone, so
  any window in which bench touches and engine commits share one calendar day
  reads **0 drift**, and the same bytes read differently from a container in a
  different timezone. The gate is ungated by design and this does not change
  that — but **do not read "0 engine drift" as evidence the benches are fresh**,
  and equally **do not read 19 WARNs as evidence they are stale**: 0 STALE is
  the reading that matters, and it holds. **The dispatch that produced this
  board asserted "0 STALE 0 drift"; the checker returns 19 of 20 with drift**
  (F-8).
- **🟠 CARRIED, AND PARTLY ANSWERED — EVIDENCE PROSE IS GATE-CHECKED NOWHERE.**
  The class is unchanged: `check_mechanism_matrix.py` validates `keeper:` stamps
  and §5.x prose headers and passes while citation text beside them goes stale.
  🆕 **The first machine-readable answer appeared this window** — Card 4's
  execution added a `frontier.withdrawn` mirror **specifically so the
  dashboard's `frontierActive()` suppresses a badge**, i.e. a rendering-drift
  gap closed at the renderer rather than in prose (v16 F-4). One field, one ISO, by
  hand. **Whether any gate should read evidence text remains unruled.**
- **🟠 CARRIED — THE FORECAST SEED CARRIES TWO READINGS AT ONCE.** F-6. Its
  top-level prose and its own per-ISO `gate` blocks disagree about who holds
  what — and the gap widened this cycle, since NEISO now holds **four** legs with
  `open: true` while the prose still leads on the FC-1 blocker. The same class the
  D13 reconcile lane was raised to repair, re-appearing inside one window
  because prose and data move at different cadences. **A different program's
  file; recorded, not adjudicated.** The per-ISO blocks are the authority, and
  this board derives gate (a) from them plus the live shards, never from the
  prose.
- **🔴 SHARPENED — THE LANE THAT MOVES A KEEPER OR A MARKER DOES NOT RE-STAMP
  THE FORECAST SEED, AND IT NOW COSTS AN INSTRUMENT ALIGNMENT.** F-6. v15
  praised the inverse pattern; v16 recorded the nyiso-159 promotion re-staling
  its own stamp. **This cycle the miso-191 promotion took MISO's stamp two
  promotions behind, and — the new and expensive part — ERCOT's brand-new
  `complete` marker landed against a stamp naming a keeper two promotions old,
  so ERCOT fails forecast gate (a) while holding the marker gate (a) is
  supposed to read.** The four-instrument divergence this board just un-retired
  is *entirely* this defect. Still not a defect in any lane — **nobody owns the
  cross-program stamp** — which is exactly why it recurs, and why it should
  probably be owned.
- **🔴 UN-RETIRED — the four-instrument divergence is BACK, one cycle after
  Card 4 closed it.** v16 retired this item on the alignment at {PJM, NEISO}.
  At this pin **CALIBRATED = `complete` = active `frontier` = {ERCOT, NEISO,
  PJM}** while **forecast gate-(a) passers = {PJM, NEISO}** (F-6). **The
  structural half is exactly why it came back and is unchanged: nothing in the
  repo compares the four.** `audit_keepers.py` checks marker/keeper re-keying,
  not frontier membership and not the forecast seed's stamps; **the divergence
  here is a STALE STAMP in a different program's file**, which no gate on either
  side reads. The board keeps re-deriving all four every cycle because that is
  the only check there is — and this cycle is the demonstration that a
  one-cycle alignment is not a closed item.
- **🔴 NEW — TWO LIVE DEFECTS IN A COMMITTED CALIBRATION REFERENCE, FOUND BY A
  RETRACTION.** `data/raw/_validation-source/actual_as_reserve_NYISO.parquet` is
  wrong on **both** counts in **every column, every year** — a cascade **sum**
  where the **max** is correct, and a positional `hoy` map that never localizes
  prevailing Eastern to the model's standard-time clock (builder
  `scripts/data/process_nyiso_as.py::build_reference`). **Blast radius: NO
  keeper, NO scored result, NO determination** — its only consumer is the
  post-solve RCPF comparator for co-opt-off runs, `nyiso_rcpf_enabled` is False
  in the NYISO keeper, and rule 19 `[R-ONE-MECH]` makes arming it alongside
  `energy_reserve_coopt` a hard error. **So it is a trap for DIAGNOSTIC
  sessions, not a defect in any result — and it caught one**, producing a false
  positive that survived until the lane re-derived from the raw CSVs. The repair
  is cheap and regenerable in-session from committed bytes; the finding lane
  deliberately did not do it mid-audit and **filed it for a data lane or an owner
  grant**. On watch because **nothing gates it**: no CI check reads a
  `_validation-source/` reference for internal consistency, and the next
  diagnostic session will read it exactly as this one did.
- **🟠 CARRIED — the standing parity-gate hazard.** The gate still reports a
  LIVE lane's pre-registered control/recipe dirs as "dead solve output"; before
  reporting a future parity red, check whether the named dirs belong to a
  running lane — **never recommend pruning a dir a live lane owns.** It went
  live in the v16 window (#4401, a caiso-224 parity fix); **no parity fix was
  needed this cycle** and the gate held exit 0 across four MISO registrations
  and four MISO prunes. The class-level carve-out (B-8) **still does not
  exist**; the allowlist stands at **26** named entries.
- **🟠 CARRIED — FORECAST-BOARD STALENESS.** Δ = 1 of 10 at the pin, unchanged.
  What stays on watch is unchanged and is not the Δ: **31 of 50 verdict stamps
  are still undated** (they predate the stamped scorer — freshness UNKNOWN until
  each passes through it) and **24 config epochs** now sit on the board (v16:
  20, v15: 14 — the count has grown every cycle this board has measured it);
  confirm mixed-vintage comparison is intended before reading any cross-run
  delta as a model effect.
- **🟢 PARTLY RETIRED — the cross-ISO scorer-change precedent.** Card 3 gave
  the class a standing rule (v16 F-3), **and this cycle it was exercised
  correctly without being invoked by name**: ERCOT's `complete` marker carried a
  determination re-verification from committed artifacts with no solve, and
  `audit_keepers` M1b was extended in the same commit to recompute the partition
  rollup live rather than read the shard's assertion. The rule: re-verify from committed artifacts before a
  cross-lane flip publishes; a disagreeing re-verification stops it. The
  *instance* v15 attached (#4343) is covered going forward. What is **not**
  retired is the older nyiso-143 D-4 rider + shared-benchmark flip, which
  happened before the rule and was never separately adjudicated.
- **🟠 CARRIED — #4054 / nyiso-140 null-treatment question**, never
  adjudicated — and now eleven promotions out of reach.
- **DURABLE LESSON (unchanged; the park makes it sharper):**
  `golden-data-tier.yml` is the ONLY workflow that runs
  `scripts/regenerate_clean.py`, so any curation-time defect under
  `scripts/data/curate_*.py` has NO pre-merge signal while the tier is parked.
  **Treat curate-script changes as unguarded.**
- **🟢 DURABLE LESSON, earned again — a negative result with a bitwise proof
  beats a positive one without.** This window: **ercot-243 and ercot-244 both
  KILLED AT CENSUS** before any solve; **caiso-225's watch sweep ALL NULL**,
  re-affirming terminal rest with zero solves; **nyiso-160's Leg-2 STOP WITH
  CAUSE** at access, with no substitute mechanism invented; **T1-H Leg B
  measuring 8.87 % and proposing nothing**; and **O7 closing on a hash-proven
  bit-identical leg**. Five negative or zero-solve results, one promotion, and
  the sharpest measurements of the cycle came from the negatives.
- **🆕 DURABLE LESSON — RE-DERIVE THE TABLE THAT "CANNOT HAVE CHANGED", AND
  THEN RE-DERIVE THE ROW THAT DID.** v15 added the first half and it paid again:
  re-deriving the stage-0 table is what found the five-wide prune (v16 F-5) and the
  overwritten provenance sha. **The new half is the bench row** — a gate whose
  reading *improved* was worth the same scepticism as one that degraded, and
  checking it found an instrument artifact rather than a repair. **A green that
  arrives without a cause is a measurement you have not made yet.**

## Forecast board — re-derived at `d44446e0`: gate (a) membership unchanged while the CALIBRATED set GREW, and leg (d) is GRANTED for the first time

**Re-derived, not carried — and the seed's schema was re-read rather than
assumed** (the v16 protocol amendment, applied again; this file belongs to a
different program and was restructured once already). Every
`gate.a_keeper_marker` was compared field-by-field against the live
`keepers/<ISO>.json` and the live `complete` block at the pin; legs (b)/(c)/(d)
and `open` are read from each ISO's own `gate` block.

| ISO | Seed names (gate a) | Live keeper | (a) | (b) | (c) | (d) | `open` |
|---|---|---|---|---|---|---|---|
| ERCOT | `2026-08-24-231-tie-zone-measured` | ⬅ `234-eastex-identity` (+ 236) | **fail — stamp STALE** *(and ERCOT now HOLDS `complete`)* | fail | pass | none | false |
| PJM | `pjm-162-inputclock` | same | **pass — current** | fail | pass | none | false |
| CAISO | `2026-08-17-caiso-200-h1-memberpanel` | `caiso-220-c1-crosswalk` | fail, stamp **STALE** | fail | fail | none | false |
| NYISO | `nyiso-157-par-attribution` | `nyiso-159-loss-surface` | fail (marker withdrawn), stamp **STALE** | pass | pass | none | false |
| NEISO | `neiso-99-joint-p1` | same | **pass — current** | pass | pass | ⬅ **granted** | ⬅ **TRUE** |
| MISO | `2026-08-22-miso-177-rho-measured` | ⬅ `miso-191-bexit` | fail, stamp **STALE — now TWO promotions behind** | fail | pass | none | false |

**Gate (a) passers = {PJM, NEISO} — UNCHANGED in membership for a third
consecutive cycle. But the `complete` set grew to {ERCOT, NEISO, PJM} this
cycle, so gate (a) is no longer equal to it**, and the difference is entirely
ERCOT's **stale stamp**, not a substantive disagreement (F-6). **Four of six
stamps are stale** — same count as v16, one of them deeper.

**🟢 THE FIRST OPEN GATE IN PROGRAM HISTORY.** v16 recorded, in these words,
*"`open` is `false` for all six and leg (d) is `none` everywhere: NO ISO'S
FULL-SOLVE AUTHORIZATION GATE OPENS."* At this pin **NEISO holds all four legs
with `open: true`** — leg (d) **granted**, by the T3-NEISO-GOLDEN lane which
also measured NEISO's T3 BAU golden (25/25 years). **This board adjudicates none
of it**: the forecast namespace is a different program's, its legs move on that
program's rulings (leg (c) moved on owner ruling Q7 about what leg (c)
*measures*, not on any model improvement), and **every FC-4 behind a passing leg
(c) is still a FAIL reported at full magnitude**. It is recorded because a leg
this board has published as `none` for every ISO, every cycle, has moved.

**🟠 The seed still carries two readings at once** — its top-level prose and its
per-ISO blocks disagree about who holds what (Watch). Both recorded; **neither
adjudicated**.

**No forecast run was solved or re-scored by this lane**; per rule 15
`[R-DASHBOARD]` the forecast namespace is registered through
`scripts/register_forecast_run.py` alone, and the backcast CI gates stay blind
to it.

## Owner queue at cycle end

Re-served and re-verified at **`d44446e0`**. **The 2026-08-31 REFRESH sitting
retired THREE carried items by ruling** (R-A → item 1, EXECUTED and merged;
R-D → item 2; R-G → item 7), **and its R-F left one PARKED with a trigger that
has since fired.** What remains, with the parked item and one new one:

1. **🟠 PARKED-AND-RE-SERVABLE — THE nyiso-161 WINTER-FACE WAIVER CARD (R-F).**
   The owner ruled **neither A (NOT-YET stands) nor C (declare CALIBRATED)** and
   parked the card behind a dated trigger: *re-serve when the C3c program's
   Q1/Q2 report lands.* **That trigger is MET at this pin** — Q1 returned
   **REAL** and Q2 returned **CONFIRM**, both landed (F-2/F-3) — so this item is
   **servable at the next sitting, not waiting on anything.** Read it with:
   the **AORR access route is PERMANENTLY CLOSED by owner decision** and
   **nyiso-97 re-open condition 3 is WITHDRAWN**, so the winter face of
   C3a-2025 is permanently unidentifiable from obtainable data; **option B
   (CWC) is dominated** (marker re-entry needs CALIBRATED); and **the precedent
   surface is not NYISO-only** — CAISO's C3a residual is CEII-blocked on both
   lever routes and would have an immediate claim on any access-blocked caveat
   class. **NYISO stays NOT-YET on {C3a-2025 −11.5 %, C3c} meanwhile.** *(This
   board takes no position on which way.)*
2. **🆕 NEW — THE C3c PROGRAM'S Q3 IS THE ONLY UNANSWERED QUESTION IN IT, AND IT
   IS AN ARCHITECTURE DECISION, NOT A LANE.** R-E chartered Q1+Q2 chained; both
   have reported (**REAL**, **CONFIRM**) and **the program's measurement half is
   spent**. What Q1 and Q2 settled is that the cross-ISO C3c ledger is telling
   the truth about **both** PJM (its PASS is a real co-optimization channel, not
   the ercot-214 phantom) and NYISO (its caveat is supported by NYISO's own
   evidence, not inherited). **Neither closed C3c anywhere**, exactly as the
   charter predicted. **Q3 — the probabilistic RT premium — is where the
   residual actually lives for CAISO, MISO, NEISO and ERCOT's conduct variant,
   and crossing it needs a different model class** (stochastic or
   multi-settlement), which collides with rules 4 `[R-DUALS]`, 8 `[R-8760]` and
   the no-MIP constraint. **The charter does not recommend opening it as a
   calibration lane, and R-E did not open it.** It is on the queue as an
   *architecture* question so it is not lost, not as a dispatchable session.
3. **🔴 CALIBRATION FREEZE / WS3 RESTART — THE G2 GATE — DEFERRED BY OWNER
   DIRECTION, so G2 stays parked BY CHOICE, NOT BY DRIFT.** Unchanged in shape,
   and this cycle supplies the counter-evidence to its own optimistic reading:
   v16 argued the question had shrunk to *the five stale rows*, because Card 1
   proved a capture can be taken without a freeze. **This cycle took no capture,
   promoted once, and MISO's row got deeper** — so the five stale rows are five
   because their keepers keep moving, which is the thing a freeze addresses.
   Standing recommendation unchanged: **a scoped, time-boxed decision taken
   TOGETHER with the golden tier's disposition**, with the **per-entry
   provenance** repair attached (one `git_sha` still serves six captures taken
   at six trees).
4. **🟠 NEISO `final` GRANT — DATA-BLOCKED.** The 2025 EIA-923 FINAL vintage has
   **still not landed**; until it does the grant question is not servable on the
   merits. Standing and re-verified at the pin: **no ISO has ever spent a
   locked-test year** (58 sidecars walked, {≤2018, 2019, 2026} returns NONE),
   NEISO's one-shot is **NEVER GRANTED, not spent** (D-23), and the freeze is
   tier-scoped to the locked test. **ERCOT's new `complete` marker does not
   touch this** — it authorizes the validation tier only, and `final` is still
   empty. Data intake needs no authorization (rule 22); the block lifts itself
   when the vintage publishes.
5. **⚪ DORMANT — the ERCOT rule-16 waiver qualifier.** Unchanged, and now
   worth re-reading once: ERCOT's `complete` marker rests on the **ercot-246
   partition rollup**, so the carve-out structure is load-bearing for a marker
   as well as for a determination. Still **not servable while dormant**;
   **re-fires only if the carve-out structure changes** — which the marker makes
   a more expensive change than it was.
6. **🟠 CARRIED, DISPOSITION UNCHANGED — the CAISO NOT-YET determination.**
   **TERMINAL REST + MAP** stands (R-3, v15 E-3), re-affirmed on evidence by
   caiso-225's all-NULL watch sweep. This cycle added two more null results
   rather than a change: caiso-226/227 landed and **caiso-228's SoCalGas OFO arm
   DIED AT GATE D1 with no solve** — the A3 route v16 recorded as
   *available and feasible but unfunded* was attempted and did not clear its own
   gate. C3a-2024/2025 still fail at **+12.5 % / +15.5 %** and owner ruling 5
   stands: **C3a must genuinely pass; NOT-YET is the honest fallback.** Nothing
   is owed here.
7. **🟠 CARRIED NOTE — the nyiso-148 2025 dear-gas level card**: no signature or
   decline recorded for it in any window since; its same-day UPDATE block should
   be read before its numbers (the keeper it names is now **six** promotions
   superseded, 148 → 152 → 155 → 157 → 159).
8. **🟢 RETIRED THIS CYCLE (v17) — do not re-serve:**
   - ~~**arm the T1-H storage-entry repair, or don't** (v16 item 1)~~ —
     **RULED R-A ("Arm both") AND EXECUTED**: both `ScenarioConfig` fields now
     default `True` (verified in `scenarios.py` at the pin), armed as one
     posture, **no re-solve**, with a **declared cache epoch** and the
     **unmeasured combined-posture note** carried (#4442).
   - ~~**the C-1 wind signal-object call** (v16 item 2)~~ — **RULED R-D:
     TERMINAL REST + MAP** at this representation grain, with
     `docs/DECISION-MAP-ercot-wind-entry-2026-08-31.md` filed, nothing armed,
     nothing rejected, and **91.1 % of the miss published open** (F-1).
   - ~~**the nyiso-leg2 promote-or-archive item** (v16 item 7's other half)~~ —
     **RULED R-G: CLOSED BY ARCHIVE**, and retired **for good** — it is not
     re-servable, because the re-verification established the object it named
     does not exist as a candidate (F-4).
   - ~~**a PJM determination-integrity card, conditional on Q1 = PHANTOM**~~ —
     **DOES NOT OPEN.** Q1 returned **REAL**; no PJM keeper rests on a phantom
     channel. Recorded here so the conditional is visibly discharged rather
     than silently dropped.

## Session roster

> **🟠 v17 STATES ITS OWN LIMIT, as v16, v15, v14 and v13 did.** This records
> lane is **not** the director desk and holds no session-listing authority, so
> it did **not** run `list_sessions`. Lane state below is derived from **git**
> (`ls-remote` branch tips, each tip tested for ancestry inside `origin/main`
> rather than read off the listing) plus one **live `list_pull_requests`** call
> at the pin. No row is carried from v16 or from the dispatch unverified.

### Lane state at `d44446e0`, derived from remote branch tips + live PR list

**ZERO pull requests are open and ZERO branches are ahead of `main`** — the
quietest lane state this board has recorded. `ls-remote` returns **five** heads;
**all four non-`main` tips PASSED the `merge-base --is-ancestor` test**, i.e.
they are merged remnants, not live work. **No audit-program lane is running at
this pin**; this records lane is the only one, and its branch is not yet pushed
at the time of measurement.

**The pin itself was taken under a FORCED UPDATE of `main`**
(`3d8ea013...d44446e0 (forced update)` on the first fetch, stable on the
second). Recorded in the roster because a forced move is the one condition that
silently invalidates a carried sha, and because every figure on this board was
re-derived *after* it rather than before.

| Lane | Branch | State at the pin |
|---|---|---|
| **Records v17 (this lane)** | `claude/audit-program-2026-08-refresh-l13h5f` | **🟢 WORKING** — the two program record files + the new decision map + the governance/per-ISO log entries + the two ERCOT matrix cells' evidence strings. Branch cut fresh at the pin, so its pack carries only this session's objects |
| **R-A — T1-H storage-entry arming** | `claude/t1h-storage-entry-arming-0yo1wq` | **MERGED, BRANCH DELETED** — **#4442**. Both fields flipped to `ScenarioConfig` default `True` **as one posture**, **no re-solve** (the registered repair arm IS the evidence), with a **declared cache epoch** and the **unmeasured combined-posture note**. Verified in `scenarios.py` at the pin, not read off the PR |
| **R-B — C-1 joint wind A/B** | `claude/joint-wind-charter-ab-58rowa` | **MERGED, BRANCH DELETED** — **#4430** (charter, pushed before any solve), **#4432**, **#4439** (both arms solved, registered, finding). Kill-gates PASS; **`NON_COMPLEMENTARY`**; nothing armed. The input R-D ruled on (F-1) |
| **R-C — nyiso-162 leg2 re-verify** | `claude/nyiso-leg2-reverify-keeper-pudq8n` | **MERGED, BRANCH DELETED** — **#4431**. Zero-solve, committed artifacts only; **found no candidate exists**. The input R-G ruled on (F-4) |
| **R-E Q1 — pjm-164 C3c phantom audit** | `claude/pjm-164-c3c-phantom-audit-yg0bs6` | **MERGED, BRANCH DELETED** — **#4456**. ⚡ **The dispatch-vs-launch check on R-E's execution lane does not read "dispatched" or "launched" — it reads DONE: verdict REAL** (F-2) |
| **R-E Q2 — nyiso-164 product-level** | `claude/nyiso-c3c-product-shortage-d2ek0l` | **MERGED, BRANCH DELETED** — **#4459**. Q2 opened *because* Q1 returned REAL, exactly as chained; **verdict CONFIRM**, kill gate fires on both clauses |
| **Records v16 (predecessor)** | `claude/audit-records-v16-refresh-r3qa3z` | **MERGED, BRANCH DELETED** — **#4434**, inside this window (which is why the v17 cycle span contains v16's own landing) |
| ERCOT 245/246/247 | `claude/ercot-245-phase0-census-0f5d8h` | **MERGED, BRANCH DELETED** — #4443/#4448/#4451/#4454. Census kills (Phase-1 **not licensed**), the ercot-246 partition-rollup ruling, and **ercot-247's first-ever ERCOT `complete` + `frontier`** (F-5) |
| NYISO 163 / 163b / AORR gate | `claude/nyiso-163-aorr-access-gate-4hquff` | **MERGED, BRANCH DELETED** — #4438/#4445. The on-receipt identifiability gate built and validated, then the **owner's permanent closure of the AORR access route** and the opening of the C3c program |
| MISO 191 / 192 / 193 | `claude/miso-191-binning-aware-exit-8kloqx`, `claude/miso-192-d4-posture-6p2jp7`, `claude/miso-cc-duct-peaking-5ww6h1` | **ALL MERGED** — #4433 (191, **the cycle's one promotion**), #4437/#4440 (192 D-4 posture), #4444/#4449/#4463/#4464 (193 `cc_duct_peaking`, registered as a rejected probe, cell `U → K`). The `miso-cc-duct-peaking` tip is one of the four merged remnants |
| CAISO 226 / 227 / 228 | `claude/caiso-226-ofo-intake-7seccx`, `claude/caiso-227-c3a-2025-4om104`, `claude/caiso-228-ofo-arm-yydzmo` | **ALL MERGED, BRANCHES DELETED** — #4435, #4450, #4462. **caiso-228's arm DIED AT GATE D1, no solve**; keeper and terminal rest unmoved |
| capx lanes — **A DIFFERENT PROGRAM** | `claude/capx-*`, `claude/miso-t1h-retire-g3-regression-i97mkq`, `claude/ercot-i3-slack-measure-qzh1rh`, `claude/calibration-workstream-relaunch-bml7zm` | **TWELVE merged PRs across EIGHT lanes** — #4429, #4436, #4441, #4446, #4447, #4452, #4453, #4455, #4457, #4458, #4460, #4461. **Not this board's work**, per the standing conflation warning. ⚠️ **THREE of its eight branch names read as calibration lanes** (`miso-t1h-retire-g3-regression` = capx-D3; `ercot-i3-slack-measure` = capx D4-I3; `calibration-workstream-relaunch` = the capx **director's own refresh desk**, r#21) **and were reclassified by reading their commits, not their branches — they are 6 of the desk's 12 PRs**, so the branch-name heuristic v16 relied on would have mis-filed HALF this desk into the calibration column |

**The honest reading: the branch check did its job in both directions, and this
time its most useful result was a NEGATIVE one.** Every lane this cycle's PRs
imply was found as a branch or as a deleted branch with merged PRs behind it;
nothing was assumed launched without one; **and R-E's execution lane, which the
dispatch described as separately dispatched, was found already MERGED with both
its findings landed** — the check's whole purpose. The one methodological
sharpening: **branch names are not lane classification.** Two capx lanes carry
calibration-shaped branch names this cycle, so the classification was done from
commit subjects and touched paths instead.

*(v16's own lane table is superseded by the one above rather than duplicated;
it is recoverable verbatim from this file at `e52b90a4`. The v15 block below is
retained in place because it carries the "⚡ Post-pin" annotations that document
how that cycle's live lanes resolved.)*

### v15's lane state, retained as history (at `69ae4dc7`)

*Derived at the v15 pin from remote branch tips + a live PR list; retained
verbatim as that cycle's record. Every "⚡ Post-pin" annotation below is v15's
own, and every lane it names has since merged.*

**ONE pull request is open and TWO branches are ahead of `main`** (the PR
reading is live, not inferred). **This ends four consecutive cycles of "no
audit-adjacent lane is running"** — v13 and v14 could each report only
completed work.

| Lane | Branch | State at the pin |
|---|---|---|
| **Records v15 (this lane)** | `claude/audit-records-v15-refresh-ob75pb` | **🟢 WORKING** — the two chartered files; branch cut fresh off `origin/main` at the pin. *(Charter named a `claude/director-records-v15-*` branch; the session's designated branch is this one, and the standing branch mandate governs — same lane, same scope, recorded so the name is not read as a second lane.)* |
| **CAISO sub-zonal (caiso-224)** | `claude/caiso-backcast-next-run-5u7ob7` | **🟢 LIVE — +2 ahead, PR #4360 OPEN.** The gated `caiso_fsno_subzonal_topology` (**default off**) + a G-CTRL bit-zero comparator probe against the committed caiso-220 sidecars. The successor to caiso-223 (R-4 route (iii)); its precommit merged as #4357. **⚡ Post-pin: MERGED (#4360) and branch deleted** |
| **ERCOT residual queue (ercot-239 r3)** | `claude/ercot-239-residual-queue-lbkvbf` | **🟢 LIVE — +1 ahead, NO PR YET.** h3068-2024 attributed (event-exit lag) — FINDING + probe + log close + matrix note. Its r2 arc merged this window (#4351 → **#4356 rejected/escalated** → #4359 r3 precommit). **⚡ Post-pin: MERGED (#4361) and branch deleted** |
| **MISO backcast calibration (miso-190)** | `claude/miso-190-backcast-calibration-okt1cn` | Branch exists, **139 commits BEHIND main, nothing unmerged**. The PREREG + gates instrument remain committed (frozen before the mechanism exists). **Registration watch OPEN for a third cycle** — verified by the absence of any `miso-19*` registry sidecar, not by the branch alone |
| ercot-240 demand gap | `claude/ercot-240-demand-gap-xbdwn5` | **MERGED AND BRANCH DELETED** — #4341 (precommit) + #4344/#4345/#4348 (probe, FINDING, log). Chartered and completed the same day (E-2) |
| audit-rulings PM records | `claude/audit-rulings-0830pm-thxtdd` | **MERGED AND BRANCH DELETED** — #4342 (R-1 annotation + R-3/R-4 rulings record) + #4346 (the §8 ledger entry for the sitting, incl. sub-entry (k)) |
| caiso-223 sub-zonal scope | `claude/caiso-223-subzonal-scope-x5egla` | **MERGED AND BRANCH DELETED** — #4347 (precommit) + #4350 (partition + membership + LDF 13/13 + FINDING). Superseded by caiso-224 above |
| nyiso-158 winter-face phase-0 | `claude/nyiso-seam-diagnosis-phase0-sl2opv` | **MERGED AND BRANCH DELETED** — #4339 |
| nyiso-159 zonal loss surface | `claude/nyiso-zonal-loss-surface-b3zm2r` | **MERGED AND BRANCH DELETED** — #4352 (phase-0 + PREREG) |
| ercot-241 conduct screen | `claude/ercot-241-conduct-param-adpfmm`, `claude/ercot-241-backcast-8horad` | **MERGED, BOTH BRANCHES DELETED** — #4349 (precommit) + #4358 (phase-0 measured; Phase-1 gate OPEN) |
| Records v14 (predecessor) | `claude/director-records-v14-ledger-lhywlm` | **MERGED AND BRANCH DELETED** — #4338, the post-pin addendum at `def338e` |
| capx lanes — **A DIFFERENT PROGRAM** | `claude/capx-*`, `claude/q5w-nyiso-marker-withdrawal-5yzj0s` | #4336, #4337, #4340, **#4343**, #4353, #4354, #4355 — the capx expansion desk. **Not this board's work**, per the standing conflation warning. **#4343 is recorded on this board only because it wrote the shared marker file** (E-5), and **#4355 only because its engine change moved two of this board's gate readings** (Gates) |

**The honest reading: the branch check did its job in both directions again.**
Every lane this cycle's PRs imply was found as a branch or as a deleted branch
with merged PRs behind it; **nothing was assumed launched without one**; and
the two live lanes were found by ancestry testing, **not** by reading the
`ls-remote` listing (which shows `main` itself as a row and would have been
misread). The capx branches remain the exact class of plausible-sounding
commits that would fool a commit-list scan — this cycle they merged **seven**
PRs, two of which genuinely touched this program's surfaces and five of which
did not.


## Refresh protocol

On each owner "refresh", the director: (1) lists sessions + fetches fresh
`origin/main`, re-reads plan §8 and lane handoffs; (2) reports each workstream
as **not started / in progress with % / completed / pending blockers**;
(3) issues prompts for any lane whose gate has cleared, appends the §8 ledger
entry, and updates this board in the same pass.

**Under the standing deviation, step (3)'s two write duties are dispatched to a
records lane rather than pushed by the director.** The director session pushes
nothing itself, by standing owner instruction (*"issue prompts, I don't want you
doing it from here"*). **A refresh is not complete until that lane has landed
both files.**

**⚠️ THE DEVIATION WAS SUPERSEDED FOR ONE SITTING AND IS BACK IN FORCE.** The
2026-08-30 decision-card sitting executed its own records duties in-session
under an **explicit one-sitting owner supersession** (v16 F-10). That supersession
is **spent**; the standing deviation governs again, and this lane is its
dispatched instrument. A future sitting that wants to write directly needs its
own supersession — the 2026-08-30 one does not carry forward.

**v17's protocol record — the dispatch-vs-launch check paid off, and its
answer was better than "launched":**

- **🟢 THE 2026-08-31 STARTUP'S DISPATCH-VS-LAUNCH CHECK PASSED 4-FOR-4, AND
  THE R-E EXTENSION RETURNED *DONE* RATHER THAN *LAUNCHED*.** The dispatch
  instructed a dispatch-vs-launch branch check on R-E's separately-dispatched
  execution lane. Run at the pin, it found **both** chartered questions already
  merged with landed findings — pjm-164 (#4456, Q1 = **REAL**) and nyiso-164
  (#4459, Q2 = **CONFIRM**) — so the item the board would otherwise have carried
  as *pending* is carried as *answered* (F-2), and one conditional queue item
  (the PJM determination-integrity card) is **visibly discharged rather than
  silently dropped**. **This is the check's whole purpose, and it is the first
  cycle it returned a resolution rather than a gap.**
- **🆕 ADDED — A LANE'S BRANCH NAME IS NOT ITS PROGRAM.** v16's classification
  heuristic was *classify by branch name, not by commit title*, because thirty
  capx PRs would have fooled a title scan. This cycle **capx lanes carry
  calibration-shaped branch names** (`miso-t1h-retire-g3-regression` = capx-D3;
  `ercot-i3-slack-measure` = capx D4-I3) and the branch heuristic alone
  mis-files both — and a **third**, `calibration-workstream-relaunch`, is the
  capx **director's own refresh desk**. Together those three are **6 of the
  desk's 12 PRs**, so branch-name-only classification mis-files **half** of it.
  **Classify from commit subjects AND touched paths; the branch name is a hint,
  not the answer.**
- **🆕 ADDED — RECORD A FORCED UPDATE OF `main` WHEN THE PIN IS TAKEN UNDER ONE.**
  This pin's first fetch reported `3d8ea013...d44446e0 main -> origin/main
  (forced update)`. A forced move is the single condition under which a sha
  carried from a previous board or a dispatch silently stops meaning what it
  meant, and it is invisible unless the fetch output is read. **Record it in the
  snapshot, and re-derive after it rather than before.**
- **🔴 PIN ONCE, THEN RECORD MOTION — held again, and this time the delta was
  MATERIAL.** `origin/main` was stable across two polling rounds before the pin.
  But unlike v16, whose dispatch-to-pin delta touched only another desk's
  handoffs, **this cycle's `4bdb2d60..d44446e0` delta is 10 merged PRs that move
  real figures on this board** — the MISO keeper, ERCOT's markers, three of five
  gate readings and both C3c answers. **The dispatch-vs-pin delta must be
  measured, not assumed small, every cycle; v16's "no figure differs" was a
  finding about that window, not a rule.**
- **🆕 ADDED — RE-DERIVE THE DISPATCH'S OWN ASSERTED NUMBERS, NOT JUST THE
  BOARD'S.** The dispatch carried three figures for this lane to reuse; **all
  three are wrong at the pin** (parity 60/95 vs **58/93**; bench 0-drift vs
  **19 of 20**; the two joint-wind cells "stay O" vs **K/O and O/K**) — F-8.
  None was a trap; each is a figure that moved between derivation and pin, or a
  shorthand. **The instruction "trust nothing in this prompt" is not
  ceremonial.**
- **Carried from v16 and still live:** re-derive the reading that *improved*
  (the bench WARNs returned this cycle exactly as predicted, confirming the
  instrument diagnosis rather than any repair); read a restructured file's
  schema before its values (the forecast seed again — leg (d) moved from `none`
  to `granted` this cycle, and a field-set assumption would have missed it).

**Carried, restated in one line each** (full text in v10–v15): run the gates,
never quote them (exit codes captured directly, not through a pipe) · quote no
cycle count without its base sha, in the dispatch and on the board · trust no
table, including the dispatch's — re-derive from committed bytes at the pin ·
**look for the BRANCH, not a plausible-sounding commit** — and then check the
branch's *commits*, because two capx branch names read as calibration lanes this
window · a refresh is complete when the sessions exist, not when the prompts
are written · read a content-addressed identity before inferring · **confirm
`frontend/data/hindcast/` is present before quoting any stamped/scored count**
(done this cycle: `check_forecast_staleness.py` reports *board inputs: all
present*) · **say which figures are derived and which are carried** — this
board's stage-0 promotion-gap counts are the current instance, and they are
labelled rather than silently re-asserted.

**While the program is parked, the refresh cycle is not the live instrument it
was.** A park-period refresh confirms (a) whether the owner has ruled on
anything in the queue — **seven rulings across the 2026-08-31 refresh sitting,
R-A/R-B/R-C executed and merged before this lane opened, R-D/R-E/R-F/R-G
executed here**; (b) whether the keeper freeze has been called — **still
deferred, and this cycle cuts back the other way: no capture was taken, one ISO
promoted, and a stale row got deeper**; and (c) whether the golden tier's park
has been lifted — **unchanged, and the CI proof stays deliberately unspent,
which is why even the PJM capture cannot be certified byte-green**.

## RESTART CHECKLIST — for whoever un-parks the program

**Do these in order. Do not start at change (a).**

0. **🟢 `main` IS FULLY GREEN AT THE v17 PIN — re-run at `d44446e0`, exit codes
   captured directly: ALL FIVE CHECKS EXIT 0.** `audit_keepers.py` **PASS 0/0**
   (now over `complete` = {ERCOT, NEISO, PJM}) ·
   `check_registry_payload_parity.py` **exit 0** (58 runs / 93 dirs / 0
   tolerated) · `check_mechanism_matrix.py` **exit 0** (194 field + 49 row +
   **152** path anchors) · `check_forecast_staleness.py` **exit 0, Δ = 1/10**
   (WARN-level; the undated-stamp WARN persists at **31 of 50**) ·
   `check_bench_freshness.py` **exit 0, 0 STALE of 20 — and 19 of 20 WITH
   ENGINE DRIFT**, the WARNs having returned exactly as v16 predicted. Green for
   a fourth consecutive cycle. **Always re-run all five rather than reading this
   line**; at this repo's merge cadence (36 PRs in four hours this window) the
   reading ages in minutes — and the dispatch that produced this board asserted
   two of these five figures wrongly (F-8).
0b. **🔴 THE GOLDEN PROVENANCE PROBLEM CHANGED SHAPE AND IS NOW HARDER TO SEE.**
   The manifest's `git_sha` **resolves** (`1cfea72`, reachable in main) — but it
   was **overwritten by the PJM capture, not resolved**, and the manifest holds
   **one** top-level sha for **six** captures taken at six trees, with **no
   per-entry provenance field**. So the five older captures now carry a sha that
   is *valid and wrong*. Separately, **five of the six captures' provenance runs
   are ABSENT from the registry** (only PJM's is present) — a five-wide
   condition, not the one-off v15 reported (v16 F-5). Neither was caused by error;
   both are the cost of parking WS3 while the calibration program runs at
   thirty PRs a window. **The per-file `content_hashes` are unaffected and
   remain the only sound verification instrument.**
1. **DECIDE THE GOLDEN TIER AND THE FREEZE TOGETHER** — the precondition, not a
   nicety. A freeze buys re-captured goldens; a parked golden tier means those
   captures cannot be certified byte-green, so a freeze alone leaves G2 leg 1
   blocked. Un-parking costs one `workflow_dispatch` (billed minutes — why it
   was parked). 🆕 **The question is now smaller: Card 1 took a capture inside
   a 67-PR window with no freeze at all**, in a lane whose keeper was still. So
   a freeze is not a precondition for a *scoped* capture; it is a question about
   **the five stale rows** and about certifying any of them.
2. **~~RESOLVE THE MANIFEST'S PROVENANCE SHA~~ → RECORD PROVENANCE PER ENTRY.**
   The old step is overtaken: `af1ccb6` is gone because it was overwritten. The
   step that replaces it is **give each capture its own provenance sha inside
   the manifest** — otherwise the next capture silently re-labels every earlier
   one, exactly as this one did. Verify existing captures against their
   `content_hashes`, never against the top-level sha.
3. **Re-verify every stage-0 golden against the then-current keepers** before
   resuming any change. Do not trust this board's staleness table — re-read the
   keeper shards and the manifest at that HEAD and re-derive it, mapping
   captured bundles back through the manifest's `keeper_id` fields. **At
   `d44446e0` the answer is: PJM CURRENT, the other five STALE, ERCOT needing
   TWO captures (forward + carve-out), five of six capture provenance runs
   unregistered — and MISO now TWO promotions past its capture.**
4. **Assume every re-capture is a real solve — and budget the memory.** The
   Card-1 capture died first on the container's **13.3 GiB cgroup RAM limit**
   (memcg OOM at 13.9 GB RSS) and succeeded only after a **12 GB swapfile**; it
   also needed a re-fetch of the converted `pjm-da-virtuals` corpus, whose
   loader hard-fails rather than no-ops. The **re-stamp-not-re-solve** shortcut
   was established for **neiso-97 only** — re-establish it before relying on it;
   re-derive the config diff first. 🆕 nyiso-160's committed-bytes audit (a
   *keeper* replaying bit-identically at HEAD, max abs divergence 0.0, all three
   years) is the first fresh evidence of the kind such a shortcut would need,
   though it proves a replay, not a capture. 🆕 **That evidence was
   independently re-measured this cycle and strengthened**: R-C's zero-solve
   re-verification reproduced max |Δ| = 0 over **1,043,280** hourly rows at a
   later head, **and across a solver-version change** (HiGHS 1.15.1 vs 1.14.0).
   Two sessions, two heads, one cross-solver result — still a replay, not a
   capture.
5. **~~Capture PJM FIRST~~ — DONE (#4369). Capture MISO next — and the case got
   stronger, not weaker.** MISO carries the deepest gap on the board and it
   **deepened again this cycle** (188 → 191), so it is now two promotions past
   its capture. **ERCOT still needs two** — and ERCOT now holds a `complete`
   marker and a `frontier` declaration resting on the two-config partition, so
   its uncaptured carve-out config is load-bearing for more than a
   determination.
6. **Do NOT re-do change (c).** It landed via #3964 and is byte-identical at
   HEAD. Verify the blob (`af34031c`) rather than re-porting it.
7. **Close the #4054 residual if you want belt-and-braces — but re-derive it,
   do not inherit it.** The NYISO keeper is **eleven** promotions past the
   captured nyiso-140 config (v15's ten + v16's one), unchanged this cycle; MISO
   is v15's eleven + one.
8. **Then, and only then, resume changes (a)–(e)** — and re-read the G2 leg
   list, because *merged byte-green* is what the gate wants, not captures.
   **Card 1 is a capture, and captures do not close leg 1.**
9b. **🆕 ADD THE SITTING-HANDOFF QUESTION TO THE CHECKLIST** (v16's amendment,
   restated because it paid off this cycle): *did the last sitting's records
   duties get dispatched, or did the session end holding them?* The
   2026-08-31 startup's dispatch-vs-launch check **passed 4-for-4** and, on
   R-E's lane, returned *done* rather than *launched* — which is what let this
   board discharge a conditional queue item instead of carrying it.
9. **Confirm the golden tier is green IN CI before claiming any byte-green
   result** — which requires un-parking it (step 1). A tier that cannot
   provision `data/clean` cannot prove byte-identity of anything, and a local
   replay is not the gate. **This applies to the new PJM capture too.**
10. **🔴 FIX THE PARITY GATE'S CLASSIFIER, NOT ITS SYMPTOM.**
    `KEEP_REQUIRED_UNMAPPED_BUNDLES` stands at **26 named entries** and the
    class-level carve-out the 2026-08-20 finding recommended (pre-registered
    recipes and in-flight controls legitimately precede any sidecar) **still
    does not exist** (B-8). ~10 lines, and it retires a recurring red for good.
    Explicitly **not** a pre-merge check, which would penalise correct
    pre-registration. **Until then, the gate's green is a maintenance state, not
    a property** — this window needed a dedicated parity fix (#4401) to keep it.
11. **🔴 RECONCILE RETENTION WITH THE GOLDEN MANIFEST — and note the class is
    FIVE-WIDE, not the single instance v15 reported.** Top-15 registry retention
    and the WS3 manifest reference the same run ids and know nothing about each
    other, so correct prunes have silently left **five of six** captures without
    a registered provenance run, and **every gate stayed green** throughout. Fix
    it on the manifest side (self-contained, **per-entry** provenance), **not**
    by exempting golden runs from retention — that re-creates the dead-bundle
    class the parity gate already struggles with.
12. **🆕 CHECK THE BENCH GATE'S DRIFT SIGNAL AGAINST ITS OWN ARITHMETIC BEFORE
    TRUSTING A GREEN.** `check_bench_freshness.py`'s engine-drift leg compares a
    `--date=short` last-commit date against `--since="<date> 23:59:59"` in the
    runner's local timezone, so it reads **0 drift** whenever bench touches and
    engine commits share a calendar day — and the same bytes can read
    differently from a container in another timezone. Ungated by design, so this
    is a reading discipline, not a defect to fix before restarting; but do not
    cite "0 engine drift" as evidence a bench is fresh.
