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
>
> ### 🟢 v18 DELTA (2026-09-01, pin `6c7f82dac015`) — THE STALE-STAMP BREAK ABOVE IS NOW **REPAIRED**, AND ALIGNMENT IS RESTORED
>
> Read the two paragraphs above as **history**: the alignment break they describe
> was recorded at v17 and **executed at v18**. The owed half of owner ruling
> **R-I** is done — all four stale gate-(a) stamps re-keyed, and **ERCOT's leg
> moves `fail → PASS` on the marker**, so the gate-(a) passers are now
> **{ERCOT, PJM, NEISO}** = the full `complete` membership and **four-instrument
> alignment is RESTORED at {ERCOT, NEISO, PJM}**. Per R-I, ERCOT's row cites
> **both** determination values — partition rollup **CALIBRATED** and registered
> run-level **NOT-YET** — neither replacing the other. **No ISO's `open`
> changes.** Three further records repairs land with it, and **two of the three
> came back different from the dispatch**: the `ff-verdicts.json` provenance
> defect is **TWO instances, not one**, and it blinds the staleness anchor; and
> the cascade rule's *"no exposure in the other five ISOs"* finding is
> **OVERTURNED — MISO carries a live sibling defect**, found by #4485 after the
> director's pin. **The v18 block is a DELTA, not a refresh: every figure on this
> board outside those four jobs still carries its v17 pin `d44446e0` and is not
> re-verified.** See **D-1 … D-6**, immediately below.
>
> ### 🔴 v18b COMPLETION (2026-09-01, pin `192460b6`) — THE SITTING'S **SEVENTH** RULING, **R-H**, WAS STILL RECORDED NOWHERE — AND IT HAD ALREADY DECIDED THE CARD THIS BOARD'S QUEUE WAS SERVING
>
> The 2026-08-31 REFRESH sitting produced **SEVEN** rulings. v17 recorded four
> (R-D/R-E/R-F/R-G) on top of the three already merged (R-A/R-B/R-C); the v18
> delta above recorded **R-I**. **R-H reached no artifact at all** — verified at
> this pin before writing: `grep "R-H"` across `docs/` (excluding the rule ID
> `[R-HOLDOUT]`) returns **ZERO**, board and plan §8 included, *after* the v18
> delta landed.
>
> **This was not a cosmetic gap.** R-H **RULED the nyiso-161 winter-face waiver
> card — OPTION A, NOT-YET STANDS** — and **owner-queue item 1 still presented
> that card as *"servable at the next sitting, not waiting on anything."* The
> board was inviting the director to re-serve a card the owner had already
> decided**, which is exactly the failure the never-re-serve duty exists to
> prevent. **D-7 records the ruling; the queue item is RETIRED.**
>
> **And the v18 delta is itself an instance of the failure shape it named.**
> D-5(a) named *"landed but incomplete"* — and the lane that named it **omitted
> R-H**, as did a **second records lane running the same dispatch in parallel at
> the same pin** (D-8b). **Two independent lanes, the same blind spot,
> inherited from the same dispatch: parallelism is not a completeness check.**
>
> **One dated correction to D-4:** MISO's cascade defect was **LIVE when D-4 was
> written and is REPAIRED at this pin** (#4497). The finding stands; its tense
> does not (D-9).

> ### 🟢 v19 FULL REFRESH (2026-09-01, pin `72576ebe`) — TWO SITTINGS OF RECORDS DEBT CLEARED IN ONE LANE: **R-J THROUGH R-O ARE ALL ON THE RECORD**, TWO QUEUE ITEMS RETIRE, AND FOUR-INSTRUMENT ALIGNMENT **HOLDS**
>
> **This is a FULL refresh, not a delta.** Every figure below — keeper table,
> markers, sidecar walk, stage-0 table, all seven gates, the forecast board, the
> queue and the roster — is re-derived at **`72576ebe`**, this lane's own pin.
> The v18/v18b blocks below it are retained as history and their `d44446e0` /
> `6c7f82dac015` / `192460b6` figures are **not** carried forward.
>
> **THE SITTING'S SIX UNRECORDED RULINGS ARE NOW RECORDED — verified absent
> first.** `grep` of each label across `docs/` at the pin returned **ZERO
> occurrences for R-J, R-K, R-M, R-N and R-O**, and R-L existed only in the
> capture lane's own finding and the capx desk's ledger — never on this board or
> in plan §8. **G-1 … G-6 record all six.** Two of the six were already
> *executed* and merely unrecorded (R-J, R-N); two were executed by a dispatched
> lane (R-L) or superseded (R-K); **R-M is executed by this lane**; and **R-O's
> chartered lane has not launched** (G-6).
>
> ### 🟢 AND THE PROGRAM'S TWO OLDEST GATE DEFECTS ARE **FIXED IN CODE**, NOT MERELY DIAGNOSED
>
> R-J's four maintenance items all landed (#4495 ×3, #4502 ×1 — mapping verified
> from commits, not from the dispatch). The parity allowlist is replaced by a
> **class-level classifier**; the bench gate's **date-kind mismatch** — diagnosed
> and re-diagnosed across three board versions — is repaired at source; the
> stage-0 manifest carries **per-entry provenance (schema v2)** with all six shas
> recovered from history; and a **hard CI guard** now holds the forecast gate-(a)
> rows against the backcast store. **Checklist items 2, 10, 11 and 12 are
> discharged by execution, and queue item Q-1 retires with them.** (G-1.)
>
> ### 🟢 AND: STAGE-0 COVERAGE TRIPLED — 1 CURRENT / 5 STALE → **3 CURRENT / 3 STALE**
>
> R-L's capture lane took **NEISO and ERCOT-forward** — the owner's verbatim
> *"Just NEISO and ERCOT"*, deliberately against restart-checklist item 5, which
> **stands**. Both fidelity oracles **PASS with zero config drift**; schema v2 is
> proven by the captures (each changed only its own entry); rule 22 is clean.
> **`results/regression-goldens/` moved for the first time in three cycles**, so
> WS3's completion figure moves by measurement rather than by assumption (G-3,
> G-11). **ERCOT's 2023 carve-out config still has no golden** — the object R-O
> charters a schema lane to make representable.
>
> ### 🟢 AND: ALL SIX FORECAST GATE-(a) STAMPS ARE **CURRENT** — THE FIRST TIME IN PROGRAM HISTORY
>
> v17 reported four of six stale and the alignment broken *on a stamp*. At this
> pin **every one of the six `a_keeper_marker` rows names the live keeper**, the
> R-N micro-supersession having re-keyed the last of them (CAISO, after the new
> guard's **first real firing**). So **CALIBRATED = `complete` = active
> `frontier` = gate-(a) passers = {ERCOT, NEISO, PJM}** — four-instrument
> alignment **HOLDS**, and the three gate-(a) failures are now failures **on the
> merits** (determination / marker), not stamp artefacts. **This is the first
> cycle in which the divergence could not have been a bookkeeping lag.** (G-9.)
>
> ### 🟠 AND TWO JOBS OF THIS LANE'S OWN DISPATCH CAME BACK **ALREADY DONE OR MOVED**
>
> **The anchor repair (job 4) was a NO-OP at the pin**: `--fix-anchors` repairs
> **0**, the gate carries **0 WARNs**, and the ~243 the dispatch reported at
> `8462da22` had already been repaired — **digits-only, correctly, and entirely
> unannounced** — inside an unrelated capx forecast re-score, #4522 (G-8). And
> **R-M's target moved between dispatch and pin**: `neiso-t3` was re-scored onto a
> **reachable** sha, and the defective stamp migrated to a *different key*. The
> annotation was therefore applied **by sha, not by key name** — the dispatch's
> key list would have annotated one healthy verdict and missed one defective one
> (G-4). **"Trust nothing in this prompt" earned its place twice in one lane.**
>
> ### 🔴 AND THE DISPATCH-VS-LAUNCH CHECK IS NOW **3-FOR-3 ON NON-LAUNCHES IN ONE SITTING**
>
> Two prior dispatches of *this* lane never launched (recorded in the protocol
> section, per the director's re-issue), and **R-O's chartered schema lane shows
> no branch and no PR at this pin** (G-6). The R-L capture lane's own finding
> records that **its** first dispatch never launched either. **Four
> non-launches, one sitting.** The check is no longer a formality on this
> program; it is the single highest-yield step in the refresh protocol.

> **STATUS: PARKED AT G1** — live rollup maintained by the program-director
> session, updated on each owner "refresh". Canonical program definition:
> `docs/model-audit-release-plan-2026-08.md` (its §8 ledger is the durable event
> record; this board is the at-a-glance state). Completion figures are the
> director's estimate against each workstream's full DoD (A+B halves).

**Snapshot (v19):** **BASE SHA FOR EVERY FIGURE ON THIS BOARD: `72576ebe`**
(merge of #4527), derived live from `origin/main` on 2026-09-01 17:16 UTC and
**held stable across two polling rounds** before the pin was taken. **The fetch
was NOT a forced update** (`main -> FETCH_HEAD`, fast-forward, both polls) —
recorded because v17's was, and a forced move is the one condition under which a
carried sha silently stops meaning what it meant. The director's two derivation
pins are both **REACHABLE and STALE**: `8462da22` (merge of #4520) by **7 merged
PRs** and `a40cfc68` (merge of #4523) by **4** (#4524–#4527). Every count below
states the window it was measured over. **Nothing is carried from the dispatch,
from board v17/v18/v18b, or from any table, unverified — and FOUR figures the
dispatch asserted are re-derived DIFFERENT (G-12).**

| window | span | commits | non-merge | merged PRs |
|---|---|--:|--:|---|
| **since v17's pin** (`d44446e0..72576ebe`) — the v19 cycle | 2026-08-31 04:26 → 2026-09-01 17:0x UTC | **167** | **104** | **62** (#4465–#4527, no #4480) |
| since the director's first pin (`8462da22..72576ebe`) | same window's tail | **20** | **13** | **7** (#4521–#4527) |
| since the director's post-pin (`a40cfc68..72576ebe`) — what moved after the prompt was re-issued | same | **11** | **7** | **4** (#4524–#4527) |

**Of the 62 merged PRs, classified per lane from the branch name AND the commits
AND the touched paths** (all three, per the v17 protocol amendment — and this
cycle the branch name alone would again have mis-filed six):

- **9 are this program's / 8 lanes**: #4465 (v18 delta), #4472 (the R-D closure
  map), #4488 (gate-(a) repair), #4495 (R-J's three gate repairs), #4498 (v18b),
  #4502 (R-J's stage-0 provenance repair), #4509 + #4517 (the R-L capture lane),
  #4523 (the R-N micro-supersession).
- **28 are the capx desk's / 18 lanes** — a DIFFERENT program: the 22 `capx-*`
  PRs, **plus #4467** and **plus the five PRs of `claude/market-sim-calibration-director-lckr9a`**.
- **25 are the calibration program's / 14 lanes**: MISO 11, NYISO 6, CAISO 5,
  ERCOT 1, cross-ISO 2 (#4466 the C3c charter audit, #4497 the xiso cascade scan).

⚠️ **THE BRANCH-NAME HAZARD REVERSED DIRECTION THIS CYCLE, AND IT IS WORSE IN
THIS DIRECTION.** v17 found *capx* branches wearing calibration-shaped names.
This cycle **`claude/market-sim-calibration-director-lckr9a` IS THE CAPX
DIRECTOR'S DESK** — every one of its commits is titled `capx-director r#22…r#26`
and it touches only `capx-director-{handoff,ledger,prompt-pack}` — and
**`claude/neiso-rc-repair-fymtkz` (#4467) IS A FORECAST/T1-X HINDCAST LANE**, not
a NEISO backcast lane: it writes `frontend/data/forecast`,
`frontend/data/hindcast`, `results/hindcast` and `scripts/register_forecast_run.py`.
Together they are **6 of the capx desk's 28 PRs**. Worse in this direction
because a *calibration*-shaped name in the calibration column looks correct and
raises no flag — v17's capx-shaped names at least announced themselves.
**#4467 is also the lane that minted both of R-M's unverifiable stamps** (G-4).

**Keeper motion: ONE promotion, in CAISO.** Re-derived rather than asserted: all
six `keeper` fields compared byte-for-byte at `d44446e0` and at the pin —
**CAISO `2026-08-26-caiso-220-c1-crosswalk` → `2026-09-01-caiso-231-b1-ungrounded`**
(#4515), the other five byte-identical. **No rule-22 D-5(b) re-key was owed**:
CAISO sits in the `withdrawn` block, not `complete`, and `audit_keepers.py`
returns **PASS 0/0** across the promotion. Recorded, **never adjudicated** (G-10).

**ONE open PR and TWO branches ahead of `main`** (live `list_pull_requests` +
`ls-remote` ancestry test at the pin): **#4530** (`miso-st-gas-steam-chp-calibration`,
opened 17:25 UTC — *after* the pin) and `capx-director-refresh-0z0e0f`. The R-N
lane's branch `claude/audit-program-director-irzj4a` is an **ancestry-tested
merged remnant**, i.e. the supersession is spent and closed. **No other
audit-program lane is running at this pin**; this records lane is the only one,
and it is the dispatched instrument of the standing deviation.

**Headline, one line: six rulings recorded for the first time, two queue items
retired, the program's two oldest gate defects fixed in code, stage-0 coverage
tripled, all six forecast gate-(a) stamps CURRENT and four-instrument alignment
holding at {ERCOT, NEISO, PJM} — while two of this lane's own six jobs came back
already-done or moved-since-dispatch, and the sitting's non-launch count reached
four.**

*(v17's snapshot block below is retained verbatim as that cycle's record. Its
`d44446e0` figures are history and are NOT this board's measurement.)*

**Snapshot (v17, RETAINED AS HISTORY):** **BASE SHA FOR EVERY FIGURE IN THIS
BLOCK: `d44446e0`**
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

## What moved — v19 CYCLE (`d44446e0..72576ebe`, "the records-debt cycle")

**Every figure in this section is derived at `72576ebe` from committed bytes.**
Nothing is read from the dispatch, from v17/v18/v18b, or from any table on this
board. Where a dispatched figure and the pin disagree, the pin wins and the
disagreement is recorded (G-12).

### G-1 · 🟢 RULING **R-J** — ALL FOUR UNBLOCKED MAINTENANCE ITEMS **EXECUTED AND MERGED**, AND THEY RETIRE QUEUE ITEM Q-1 BY EXECUTION

Recorded here for the first time: **`grep "R-J"` across `docs/` at the pin
returns ZERO** (the only near-match is the unrelated word `R-JUDGMENT`). The
ruling authorised the four maintenance items that needed no owner decision. All
four are **merged and verified in the working tree at the pin** — and the
commit→PR mapping was **derived by ancestry, not taken from the dispatch**:

| item | commit | PR | verified at the pin |
|---|---|---|---|
| **Parity allowlist → class-level carve-out** (checklist item 10, BLOAT B-8) | `76c5eed6` | **#4495** | `KEEP_REQUIRED_UNMAPPED_BUNDLES` is now a **residual** enumeration of **8** entries behind a structural two-conjunct classifier (no solve output **AND** named by a committed PREREG/RESULT reproduction) |
| **Bench gate date-kind fix** (checklist item 12) | `d5c3178f` | **#4495** | both sides now use the **committer instant in offset-bearing form**; the docstring records that `--since` is inclusive, verified 2026-09-01 |
| **Stage-0 per-entry provenance** (checklist items 2 + 11) | `362e2771` | **#4502** | manifest **schema v1 → v2**; `provenance` + `keeper_snapshot` per entry; the shared top-level `git_sha`/`git_dirty`/`env` **removed** |
| **`check_gate_a_provenance` hard CI guard** | `3f5a24ae` | **#4495** | wired at `.github/workflows/ci.yml:213`, `python3` stdlib, **exit 0** at the pin |

**🟠 ONE R-J FIGURE THE DISPATCH ASSERTED IS RE-DERIVED DIFFERENT, AND THE TRUE
STORY IS BETTER.** The dispatch said the allowlist went **26 → 3**. Measured at
four shas (`565f555c`, `8462da22`, `a40cfc68`, `72576ebe`) it is **8 at every
one**, and the pre-repair count at `565f555c^` is **40, not 26** — the 26 was the
audit board's *last count*, and the enumeration had grown by 14 in the interim,
exactly as the gate's own docstring warned (*"a stale entry is a re-armable
hole"*). **So the repair is 40 → 8, a larger win than the dispatch claimed**, and
the residual 8 are live-lane control/recipe dirs, not dead output.

**🟢 THE STAGE-0 REPAIR ALSO OVERTURNED TWO OF THIS BOARD'S OWN STANDING
CLAIMS**, and the lane said so in its own commit message rather than quietly
fixing them: **`af1ccb6` DOES resolve and IS an ancestor of `main`** (it is the
CAISO capture commit), and **the five "unrecoverable" shas were recoverable all
along** — every intermediate value had been committed on its way through the
manifest's history. All six were recovered **with evidence and zero UNKNOWN
rows**: ERCOT `ec413d20`, NEISO `ebd31a9`, NYISO `2dd9dbc`, CAISO `9f6ff3e`,
MISO `af1ccb6`, PJM `1cfea72`; the chain **self-corroborates** (CAISO's sha *is*
the NYISO capture commit, MISO's *is* the CAISO one). **v17's "does not resolve"
was a shallow-clone artefact** — see G-13, which this lane hit independently.

**Q-1 IS RETIRED BY EXECUTION**, not by ruling: the thing it asked for exists.

### G-2 · 🟢 RULING **R-K** — STAGE-0 CAPTURES **HOLD**; **SPENT**, SUPERSEDED BY R-L

Recorded for the first time (`grep "R-K"` → **ZERO** at the pin). R-K held the
stage-0 captures. It was superseded within the same sitting by **R-L**, which
authorised two of them by name. **R-K is spent and is not a live constraint**;
it is recorded so the hold and its release are both legible, and so a future
reader does not find R-L acting against an apparently-standing hold.

### G-3 · 🟢 RULING **R-L** — "JUST NEISO AND ERCOT" — **DISCHARGED IN FULL**, WITH ONE DEVIATION THE DIRECTOR ACCEPTED AND THIS BOARD NOW ADOPTS AS STANDING

Owner ruling, verbatim: **"Just NEISO and ERCOT"** — **deliberately against
restart-checklist item 5** (*capture MISO next*), which **STANDS UNCHANGED**;
R-L is an exception for this capture, not an amendment. Executed by
`claude/stage0-capture-neiso-ercot-elgk62` (**#4509** the captures, **#4517** the
finding), **the audit program's first solve lane**.

**Discharge, verified at the pin against the committed manifest — not read off
the finding:**

| leg | evidence at `72576ebe` |
|---|---|
| **Both fidelity oracles PASS, zero config drift** | `keepers.NEISO.fidelity.scenario_config_drift == []` and `keepers.ERCOT.fidelity.scenario_config_drift == []`; 259 / 271 meta flags matched |
| **Schema v2 proven** | each capture wrote **only its own entry**: NEISO `provenance.basis_sha 3c1f9642`, ERCOT `3c1f9642` / `git_sha a64cc7aa`, while CAISO/MISO/NYISO/PJM retain `9f6ff3ee` / `af1ccb6c` / `2dd9dbc9` / `1cfea728` untouched. **The v17 defect — one capture silently re-labelling every earlier one — is structurally impossible now, and this is the demonstration** |
| **Rule 22 clean** | years `[2023, 2024, 2025]` on both entries; no out-of-training year solved, scored or registered |
| **Coverage** | `check_golden_manifest.py` **exit 0**: **3 CURRENT / 3 STALE** |

**🟢 THE ACCEPTED DEVIATION, AND THIS BOARD'S STANDING READING OF IT.** The
capture lane **registered nothing on the backcast dashboard**, and the director
**accepted that**. The reasoning, adopted here as **the program's standing
reading of the stage-0 table's registry column**:

- **A golden's "provenance run" is the KEEPER it was captured against**, not the
  capture itself. That is exactly what schema v2 encodes (`keeper_id` +
  `keeper_snapshot`) and exactly what `check_golden_manifest.py` enforces.
- **The Card-1 precedent registered nothing either**, and **0 of the 60
  registered sidecars is a golden capture** — verified by walking the registry at
  the pin, not asserted.
- **Registering captures would spend top-15-per-ISO retention on regression
  baselines** — which is the *precise* fix **E-7 rejected** (*"do not exempt
  golden runs from retention — that re-creates the parity gate's dead-bundle
  class"*). Registering them is the same error wearing the opposite sign.

**Consequence for how this table is read, going forward:** the registry column
of the stage-0 table asks *"is this golden's provenance KEEPER RUN still
registered?"* — a **retention** question that schema v2's `keeper_snapshot`
already makes survivable — and **never** *"was the capture registered?"*, which
would be a category error. **A golden capture is not a dashboard run and rule 15
`[R-DASHBOARD]` does not reach it.**

### G-4 · 🟢 RULING **R-M** — Q-2's REMEDY **EXECUTED BY THIS LANE**, AND THE TARGET HAD **MOVED** SINCE THE DISPATCH

Recorded for the first time (`grep "R-M"` → **ZERO** at the pin) **and executed
here**, which is the difference between this entry and a finding that describes a
repair. The ruling: the two forecast verdicts whose `scored_at_sha` never reached
`main` are **ANNOTATED AS PERMANENTLY UNVERIFIABLE**.

**🔴 THE DISPATCH'S KEY LIST WAS ALREADY WRONG AT THE PIN, AND FOLLOWING IT WOULD
HAVE ANNOTATED A HEALTHY VERDICT AND MISSED A DEFECTIVE ONE.** The dispatch named
`neiso-t3` @ `89dacc4c0343` and `neiso-t3-pre-fc6` @ `271ad606c3fd`. At the pin:

- **`neiso-t3` no longer carries `89dacc4c0343`.** #4522's FC-6 P1 re-score moved
  it to **`7dffe3341158` @ 2026-09-01T06:12:01Z — REACHABLE in `origin/main`**.
  `neiso-t3` is healthy and was **not** annotated.
- **`89dacc4c0343` migrated to a different key**, `neiso-t3-pre-fc5`, when the
  FC-5 disposition lane preserved the prior verdict under a new name.
- `neiso-t3-pre-fc6` @ `271ad606c3fd` is unchanged.

**So the annotation was applied by SHA, not by key name** — the two verdicts
carrying an unreachable stamp at this pin are **`neiso-t3-pre-fc5`** and
**`neiso-t3-pre-fc6`**. Both are archival *preserved-prior* verdicts; both read
`HOLD`.

**Unreachability re-established, not inherited** — and against the **remote**,
because this container's clone is shallow (G-13). All **43** verdict stamps
carrying a `scored_at_sha` were swept; the four the shallow clone could not see
but which the GitHub API resolves (`8ba592814d92`, `bd97c6ebaa68`,
`e2a422c191aa`, `74775c4d661f`, `6fbd3f28eb9a`, `60e19610e454`) are healthy.
**The strict count is 2 of 43 — the same count v18b reached independently by
un-shallowing, from a different pin and a different method.**

**What was written, and what deliberately was not:**

- **Two additive keys per verdict**, as **siblings of `provenance`, never inside
  it**: `scored_at_sha_unverifiable: true` and
  `scored_at_sha_unverifiable_note` (a one-line cause note citing R-M). Neither
  is a `forecast-provenance/v1` field name (`schema`, `scored_at_sha`,
  `scored_at_date`, `cache_epoch`), and `forecast_provenance.read_stamp()` reads
  only the `provenance` object — **so no instrument can read the annotation as a
  provenance stamp.**
- **No sha altered and none fabricated.** Both historical values stand verbatim.
  Machine-verified: **4 lines added, 0 removed, 0 altered**; both `provenance`
  blocks **byte-identical** before and after; both determinations **`HOLD` →
  `HOLD`**; **no other verdict object touched**, key set unchanged at 55.
- **`check_forecast_staleness.py` re-run after the edit: exit 0**, anchored on
  **`7dffe3341158`**, which is **reachable in `origin/main`** — the ruling's
  explicit precondition, tested rather than assumed.

**Q-2 IS RETIRED.**

### G-5 · 🟢 RULING **R-N** — THE ONE-PUSH MICRO-SUPERSESSION IS **SPENT**, AND THE STANDING DEVIATION IS BACK IN FORCE

Recorded for the first time (`grep "R-N"` → **ZERO** at the pin). The records
path for this sitting was ruled to be **a one-push micro-supersession plus this
lane**. The director spent the supersession as **#4523** (commit `6d700725`,
**5 lines**), re-keying CAISO's forecast gate-(a) stamp to
`2026-09-01-caiso-231-b1-ungrounded`.

**Verified at this pin rather than accepted:** `check_gate_a_provenance.py`
**exits 0** (6 rows: keeper identity + marker state match the backcast store),
CAISO's `a_keeper_marker` names the live keeper, and the branch
`claude/audit-program-director-irzj4a` is an **ancestry-tested merged remnant**.

**Two things worth keeping from how it was executed.** First, it is the **new
guard's FIRST REAL FIRING** — #4495's `check_gate_a_provenance` went red (exit 1)
on the caiso-231 promotion and green after the re-key, which is a guard doing the
job it was built for **eight PRs after it was built**, on a defect class this
board had re-reported for three cycles with no gate able to see it. Second, the
push was **rebased onto #4522's disjoint capx edit** to the same shared file
rather than overwriting it — the shared-surface duty observed in practice, on the
one file three desks write.

**The supersession is SPENT and does not carry forward.** The standing deviation
governs again (*"issue prompts, I don't want you doing it from here"*), and **this
lane is its dispatched instrument**. A future sitting that wants to write
directly needs its own supersession.

### G-6 · 🟠 RULING **R-O** — THE ERCOT CARVE-OUT GOLDEN IS ANSWERED BY **CHARTERING A SCHEMA LANE**, AND THAT LANE HAS **NOT LAUNCHED** AT THIS PIN

Recorded for the first time (`grep "R-O"` → **ZERO** at the pin). R-L's capture
answered the ERCOT-forward config and explicitly reported the **2023 carve-out as
NOT covered and not coverable without a schema change**. R-O's disposition is not
"capture it anyway" but **charter the schema lane**, scoped to three things:

1. **A config-partition representation in the manifest** — today `keepers` is
   keyed one entry per ISO, so a two-config ISO has nowhere to put its second
   golden.
2. **`live_keeper` partition resolution** — `check_golden_manifest.py` compares
   one `keeper_id` against one live keeper; under a partition it must resolve
   *which* config a golden is of before it can call it CURRENT or STALE.
3. **The carve-out capture itself**, once (1) and (2) exist.

**LANE STATE AT THE PIN — the dispatch-vs-launch check applied, as instructed:
NOT LAUNCHED.** `ls-remote` returns four heads (`main`,
`audit-program-director-irzj4a`, `capx-director-refresh-0z0e0f`,
`miso-st-gas-steam-chp-calibration-9snn32`); **none is a schema lane**, and the
live PR list shows **one** open PR, unrelated (#4530). No commit in the window
touches `check_golden_manifest.py`'s partition handling. ⚠️ **The honest limit of
this evidence, stated because this board's own lane is invisible to it:** an
unpushed session is indistinguishable from no session — *this* lane's branch was
also unpushed at the moment of measurement. **What is established is: no branch,
no PR, no commits at `72576ebe`.**

**Standing consequence while the lane is unlaunched:** ERCOT's stage-0 row is
CURRENT **for its forward config only**, and full ERCOT coverage remains **two
captures, not one** — a fact the manifest still cannot express, which is exactly
what R-O exists to fix. Queue item added; see the queue.

### G-7 · 🟢 SEVEN GATES, NOT FIVE — THE ROSTER IS CORRECTED AND ALL SEVEN EXIT **0**

The board's protocol text and restart-checklist item 0 both said **five**; the
director's handoff said **six**; **SEVEN is correct**. Two gates were being
undercounted: **`check_gate_a_provenance.py`** (`ci.yml:213`, a **hard** gate, new
this window under R-J) and **`check_golden_manifest.py`** (`ci.yml:118`, which has
existed and been enforced throughout — **the undercounted seventh**, and the
instrument that now *owns* the stage-0 table). Both the Gates table and
checklist item 0 are corrected.

**All seven re-run at the pin, exit codes captured directly and never through a
pipe.** Readings in the Gates table. **Two of the director's seven readings
re-derive different at this pin**, both benignly: the matrix gate's **+243 anchor
WARNs are gone** (G-8) and the gate-(a) red is **repaired** (G-5) — the dispatch
predicted both would need this lane's action; neither did.

### G-8 · 🟠 JOB 4 — THE ANCHOR REPAIR — WAS **ALREADY DISCHARGED**, BY AN UNRELATED LANE, **UNANNOUNCED**

`python3 scripts/check_mechanism_matrix.py --fix-anchors` at the pin: **"repaired
0 line anchor(s); 0 left in the ratchet"**, `git diff` **empty**, gate **exit 0**
with **0 WARNs**, anchors **194 field + 49 row + 156 path** (v17: 194/49/152).
The ~243 WARNs the dispatch measured at `8462da22` were real and are gone.

**Where they went, established by diff rather than inferred:** `scenarios.py` is
**byte-identical** between `8462da22` and the pin, while
`docs/codebase-site/data/mechanism-matrix.js` changed by **120 insertions /
120 deletions** in exactly one commit — **`369c9bb7`, inside #4522**, the capx
lane whose commit subject is *"Re-score neiso-t3 FC-6 on the repaired P1 arm"*
and whose message **does not mention the matrix at all**.

**It was done correctly.** Verified post hoc by normalising every `:NNNN` token
on both sides of that commit: the two files are then **identical** — so the edit
moved **digits only**. No verdict letter, evidence string, fc posture or keeper
stamp moved, which is the same constraint this lane was given.

**🟠 THE FINDING IS NOT THE REPAIR — IT IS THE SILENCE.** A shared, CI-gated base
file was rewritten across 120 line-pairs by a lane whose declared scope was a
forecast re-score, with no mention in the commit subject or body. It happened to
be correct and happened to be exactly what this lane was dispatched to do. **The
class is a lane touching a shared surface without declaring it** — the same class
#4523 handled *well* one PR later by rebasing rather than overwriting (G-5). On
watch; not adjudicated, and **not a defect in the repair**.

**Protocol consequence, and it is the generalisable one: re-derive a dispatched
job's PRECONDITION before executing it, not only its figures.** Running
`--fix-anchors` blind would have produced an empty commit and a board entry
claiming a repair this lane did not make.

### G-9 · 🟢 FOUR-INSTRUMENT ALIGNMENT **HOLDS** — AND FOR THE FIRST TIME EVER, ALL SIX GATE-(a) STAMPS ARE CURRENT

Re-derived independently from four sources at the pin, with **fail-closed null
handling** — an ISO with a missing or unparseable value counts as **NOT** in the
set, never as a pass:

| instrument | source | membership at `72576ebe` |
|---|---|---|
| **Determination = CALIBRATED** | `status/<ISO>.js` `keeper.determination` | **{ERCOT, NEISO, PJM}** |
| **Rule-22 `complete` marker** | `calibration-complete.json` `complete` block | **{ERCOT, NEISO, PJM}** |
| **Active `frontier`** | per-ISO `frontier` block, **`withdrawn` honoured, absent block ⇒ NOT active** | **{ERCOT, NEISO, PJM}** — NYISO `withdrawn: 2026-08-30`; CAISO and MISO carry **no** frontier block |
| **Forecast gate-(a) passers** | `program-status.json` per-ISO `gate.a_keeper_marker.status` | **{ERCOT, NEISO, PJM}** |

**ALL FOUR AGREE. Alignment HOLDS at {ERCOT, NEISO, PJM}.**

**🟢 AND THE STRUCTURAL POINT IS BIGGER THAN THE MEMBERSHIP.** v17 recorded
**four of six** gate-(a) stamps **stale**, and the alignment break was *entirely*
that staleness — a bookkeeping lag masquerading as a disagreement. At this pin
**every one of the six `a_keeper_marker` rows names its ISO's live keeper**
(ERCOT `234-eastex-identity`, PJM `pjm-162-inputclock`, NEISO `neiso-99-joint-p1`,
CAISO `caiso-231-b1-ungrounded`, MISO `miso-191-bexit`, NYISO
`nyiso-159-loss-surface`) — machine-checked by `check_gate_a_provenance.py`,
**exit 0**. So the three ISOs that fail gate (a) fail it **on the merits**: CAISO
and MISO are `NOT-YET` and hold no marker; NYISO's marker is `withdrawn`.
**This is the first cycle in which the divergence could not have been a stale
stamp** — because a gate now refuses to let one exist.

**The watch item this retires, and the one it does not.** The *stale-stamp*
mechanism is now **gated in CI** and comes off the watch. **What does not retire
is the four-instrument comparison itself**: `check_gate_a_provenance` compares
keeper identity and marker state and **explicitly reads no determination**, and
nothing in the repo compares `frontier` membership against anything. **Three of
the four instruments are now cross-checked; the fourth still is not.**

### G-10 · 🟠 KEEPER MOTION — CAISO 220 → 231 (recorded, NOT adjudicated)

The cycle's **only** promotion: **`2026-08-26-caiso-220-c1-crosswalk` →
`2026-09-01-caiso-231-b1-ungrounded`** (#4515), a rule 25 `[R-ISO-SCOPE]` /
rule 14 `[R-ACCURATE]` structural-integrity repair replacing three
ERCOT-lineage-fitted offer bands (CC_CHP / CT_CHP / ST_GAS) that were sitting
un-grounded on CAISO's binding path. **Determination unchanged at `NOT-YET`;
grade unchanged at 8 / 6 / 1 / 1.** C3a(RT) moves marginally and **not
favourably**: 2023 **+4.0 → +4.1 %**, 2025 **+15.5 → +15.6 %**, 2024 unchanged at
**+12.5 %** — which is rule 1 `[R-STRUCT]` behaving exactly as written, a
structurally-correct repair kept despite a residual that did not improve.

**No rule-22 re-key was owed** (CAISO is `withdrawn`, not `complete`), and
`audit_keepers.py` returns **PASS 0/0** across it. **This board takes no position
on the merits.** Two items in the promotion's own record are noted because they
bear on this program's rules, not on CAISO's: it records a **standing owner
directive of 2026-09-01, "NO CONTROL ARMS"** (a single-delta arm is solved once
and scored against the committed keeper; HEAD drift is not measured with an LP
run), and it **records rather than drops a pre-registered gate it could not
satisfy** (G-STRUCT's DOF leg predicted the `offer_curve_by_group` ledger count
would fall 112 → 103; `build_dof_ledger._count_scalars` is provenance-blind and
measures surface size, not fitted content). **Both recorded, neither adjudicated.**

### G-11 · 🟢 A WORKSTREAM SURFACE MOVED — THE FIRST TIME IN THREE CYCLES

v17 reported the three workstream surfaces byte-untouched *at once*. Re-measured
over `d44446e0..72576ebe` with `git diff --name-status`:

- **`results/regression-goldens/`** — **MOVED**: `perfb-stage0/manifest.json`
  (schema v2 under R-J, then two captures under R-L). **WS3's stage-0 coverage
  figure moves by measurement**, 1/6 → 3/6.
- **`.github/workflows/`** — **MOVED**: `ci.yml`, gaining the
  `check_gate_a_provenance` step.
- **`docs/audit/`** — **byte-untouched**. WS1 is unchanged, and its blocker is
  still the G3 gate, not remaining A-half work.

**What this does NOT do is move G2.** PERF-B is still paused by owner decision
and the golden tier is still parked by owner ruling, so **byte-green cannot be
CLAIMED for the two new captures any more than for the PJM one**. Leg 1 keeps
**both** parked dependencies. Coverage improving while the gate stays shut is the
honest reading.

### G-12 · 🟠 FOUR FIGURES THE DISPATCH ASSERTED ARE RE-DERIVED **DIFFERENT** — WHICH IS THE PROTOCOL WORKING

None was a trap; each is a figure that moved between derivation and pin, or a
shorthand that did not survive measurement. **All four are recorded because the
instruction "trust nothing in this prompt" is not ceremonial.**

| dispatch asserted | re-derived at `72576ebe` |
|---|---|
| parity allowlist **26 → 3** named entries | **40 → 8** (26 was the board's last count; it had grown to 40 by the repair) — G-1 |
| **~243 anchor WARNs** to repair with `--fix-anchors` | **0 WARNs, 0 repaired** — already fixed by #4522 — G-8 |
| gate-(a) **exit 1**, repaired at `a40cfc68` | **exit 0** at the pin ✓ (the repair landed; the *reading* is the post-repair one) — G-5 |
| R-M targets `neiso-t3` + `neiso-t3-pre-fc6` | **`neiso-t3-pre-fc5` + `neiso-t3-pre-fc6`**; `neiso-t3` was re-scored onto a reachable sha — G-4 |

Also re-derived and different from v17's carried figures, none of them the
dispatch's fault: registry sidecars **58 → 60**, parity **58/93 → 60/95**,
staleness **81/49 → 89/57 stamped/scored** and **24 → 25 epochs**, bench engine
drift **19 of 20 → 20 of 20** at **6** engine commits (still **0 STALE**, still
ungated), matrix path anchors **152 → 156**.

### G-13 · 🔴 THE SHALLOW-CLONE TRAP, HIT INDEPENDENTLY FOR THE THIRD TIME IN THIS PROGRAM — AND IT HAS NOW PRODUCED ONE PUBLISHED WRONG READING

**This container's clone is SHALLOW** (`git rev-parse --is-shallow-repository`
→ `true`; earliest reachable commit `e52b90a4`, v16's own landing). Every
`git cat-file` / `merge-base` test against a sha older than that returns *absent*
— **indistinguishable, locally, from a sha that never existed.**

Measured here: of the **13** distinct `scored_at_sha` values on the forecast
board, the shallow clone reports **8 unreachable**; the GitHub API resolves **6
of those 8**. **The true strict count is 2.** Had this lane trusted the local
answer it would have annotated **six healthy verdicts** as permanently
unverifiable and written six fabricated defects onto the record — a strictly
worse outcome than the defect it was sent to annotate.

**The class already has a published casualty.** v17's stage-0 table asserted
`af1ccb6` *"does not resolve"* and built a Watch item and a checklist step on it;
R-J's repair lane found it **resolves and is an ancestor of main**, absent only
from *its* container's depth-258 clone. **Three sessions, three containers, one
trap.** The rule, now stated for the third time and worth stating once more
because it keeps costing:

> **BEFORE REPORTING AN ABSENCE FROM GIT, ESTABLISH THAT THE REPOSITORY COULD
> HAVE SHOWN YOU THE THING.** Check `--is-shallow-repository` first. Then either
> `git fetch --filter=tree:0 --unshallow` (measured at ~2 s by the v18b lane) or
> confirm against the remote API. **A local "not found" is evidence about the
> clone, not about the repository.**

### G-14 · 🔴 THE DISPATCH-VS-LAUNCH CHECK REACHED **FOUR NON-LAUNCHES IN ONE SITTING** — AND ITS YIELD IS NOW THE HIGHEST OF ANY PROTOCOL STEP

Recorded per the director's re-issue instruction, and extended by this lane's own
measurement:

1. **The original v19 records dispatch NEVER LAUNCHED** — no branch, no session,
   confirmed from git and the session roster.
2. **The FIRST RE-ISSUE of the same dispatch NEVER LAUNCHED** — same evidence.
   The records debt therefore stood **two sittings deep**; this lane is the third
   dispatch and the first to run. Both instances are recorded in the protocol
   section, as instructed.
3. **R-L's capture lane's first dispatch never launched** — recorded in that
   lane's own finding (*"Re-issued by the director after the dispatch-vs-launch
   check found the original R-L dispatch never launched"*).
4. **R-O's chartered schema lane has not launched at this pin** — no branch, no
   PR, no commits (G-6).

**Read against v16–v18, the trend is unambiguous.** v16 caught a near-miss; v17's
check returned *done* rather than *launched* on R-E; **this sitting produced four
non-launches, one of them twice**. A dispatched job is not a done job and is not
even a *started* job. **The step costs one `ls-remote` plus one PR list and is
the only thing standing between a ruling and silent evaporation.**

### G-15 · 🟢 QUEUE ITEM **Q-4** IS **ADOPTED BY THE DIRECTOR** INTO THE REFRESH PROTOCOL

v18b proposed Q-4 and explicitly declined to adopt it (*"the refresh protocol is
the director desk's"*). **The director has adopted it.** Both halves are now
standing protocol and both were executed by this lane:

- **`grep` every ruling label of the sitting across `docs/` before a records lane
  closes.** Run at the pin: R-A…R-I and R-L resolved; **R-J, R-K, R-M, R-N, R-O
  returned ZERO** — which is precisely how this cycle's five-ruling gap was
  found, and it is the same instrument that finally caught R-H.
- **Diff every dispatched job against a CHANGED TARGET FILE.** Run at close; the
  table is in the protocol section. **It is what caught G-8** — job 4's target
  file needed no change, so the job was already discharged and a "finding
  describing the repair" would have been false.
- **And its rider stands: a parallel lane is not a completeness check.**
  Redundancy catches measurement error, never scope omission, because both lanes
  inherit scope from one dispatch.

## v18 DELTA — the gate-(a) repair lane (`d44446e0` → `6c7f82dac015`, 2026-09-01)

**THIS IS A DELTA BLOCK, NOT A v18 REFRESH, and the distinction is load-bearing.**
A refresh re-derives the whole board — the PR classification, the keeper table,
the stage-0 table, the parity/bench/matrix gate counts, the sidecar walk. **This
lane re-derived none of that.** It is a repair lane with four jobs, and it
re-derived exactly what those four jobs touch: the six gate-(a) rows, the two
R-D maps' headline figures, every provenance sha in `ff-verdicts.json`, and the
cross-ISO cascade evidence. **Every other figure on this board still carries its
v17 pin `d44446e0` and is NOT re-verified here.** Read it that way.

**PIN: `6c7f82dac015`** (merge of #4485), held stable across two polls. The v17
board's own pin `d44446e0` is **21 commits / 2 merged PRs behind** it — and one
of those two PRs (#4485) **overturns a finding this lane was dispatched to
record** (D-4 below).

**Headline: the R-I repair the last lane was dispatched to make is now MADE — one
gate verdict moves, ERCOT `fail → PASS` — and four-instrument alignment is
RESTORED at {ERCOT, NEISO, PJM}. Three of this lane's four jobs came back
different from the dispatch: one bigger, one overturned, one confirmed exactly.**

### D-1 · 🟢 R-I IS EXECUTED — GATE (a) IS ALIGNED, AND THE ALIGNMENT BREAK OF F-6 IS CLOSED

v17's **F-6** recorded that four of six gate-(a) stamps were stale and that
ERCOT's leg failed *on a stale stamp rather than on a model fact*. **It recorded
it and did not repair it.** This lane repairs it. All six rows re-derived live
from `keepers/<ISO>.json` + `calibration-complete.json` at the pin; **the
director's derivation is confirmed in all six**, keeper ids included.

| ISO | seed's stamp (pre) | live keeper | (a) before | (a) after |
|---|---|---|---|---|
| **ERCOT** | `2026-08-24-231-tie-zone-measured` | `2026-08-25-234-eastex-identity` | fail | **PASS ⬅ MOVED** |
| CAISO | `caiso-200-h1-memberpanel` | `2026-08-26-caiso-220-c1-crosswalk` | fail | fail (stamp only) |
| MISO | `miso-177-rho-measured` | `2026-08-30-miso-191-bexit` | fail | fail (stamp only) |
| NYISO | `nyiso-157-par-attribution` | `2026-08-30-nyiso-159-loss-surface` | fail | fail (stamp only) |
| PJM | `pjm-162-inputclock` | same — current | pass | pass (**untouched, byte-identical**) |
| NEISO | `neiso-99-joint-p1` | same — current | pass | pass (**untouched, byte-identical**) |

**The one verdict that moves moves on the MARKER, not on the re-key.** ERCOT
entered `complete` on 2026-08-31 (ercot-247), so the stale row's assertion
*"Absent from the `complete` block"* was **false at this pin** and is withdrawn.
Gate (a) is decided on the marker — full-span keeper **and** a `complete` entry —
and ERCOT holds both, so the leg passes mechanically.

**Per R-I, ERCOT's row now cites BOTH determination values, neither replacing the
other:** the ISO-level partition rollup **CALIBRATED** (ercot-246 ruling of
2026-08-31, `keepers/ERCOT.json config_partition`; forward keeper on {2024, 2025}
and the 2023 carve-out `236-swcap-clip-k33` on {2023}, both CALIBRATED on their
own spans) **and** the registered run-level **NOT-YET** at full magnitude
(C3a-2023 model 38.75 vs actual 64.32 $/MWh = **−39.7 %**, tol ±10 %; C3b-2023
monthly load-weighted **NRMSE 0.730**, tol ≤0.20 — both re-read from
`status/ERCOT.js`, not from v17's F-5). A reader comparing the two boards now
sees **why** they differ instead of a contradiction.

**The backcast half of R-I was verified already-satisfied** before anything was
edited: `build_status.py` implements the partition rollup (l.515–583) and
`status/ERCOT.js` publishes `determination: CALIBRATED` with
`registered_determination: NOT-YET` preserved beside it.

**Blast radius, stated because a gate row is an expensive object.** Structural
diff of `program-status.json`: **exactly 16 changed leaves**, all inside the four
repaired `a_keeper_marker` rows plus `gate_a_provenance`. **PJM's and NEISO's rows
are byte-identical.** **NO ISO's `open` CHANGES** — ERCOT is now
(a) PASS · (b) fail · (c) pass · (d) `none`, so leg (b) and the absent leg (d)
still close its full-solve gate; `open` stays **false**, and NEISO remains the
only ISO with `open: true`. **Gate-(a) passers are now {ERCOT, PJM, NEISO} = the
full `complete` membership**, so three instruments and the forecast board agree.
Nothing was solved, scored or registered; no keeper shard, marker, freeze file or
matrix shard was touched. `gate_a_provenance` keeps its deliberately-distinct
field names (`derived_at_*`, never `scored_at_*`) — re-verified by running
`check_forecast_staleness.py`, which still classes the seed as **1 stamped,
0 scored**. **No CI guard for gate-(a) staleness was added**; it stays an open
owner queue item (Q-1 below).

### D-2 · 🔴 THE `ff-verdicts.json` PROVENANCE DEFECT IS **TWO**, NOT ONE — AND IT BLINDS THE STALENESS INSTRUMENT

The dispatch named `neiso-t3`'s `scored_at_sha` `89dacc4c0343`. **The count
matters — one instance and twenty are different problems — so all 46 sha
references in the file were tested, not just the named one.**

**⚠️ METHOD NOTE, because the obvious test gives a false answer here.** This
session's checkout is a **shallow clone (256 commits, earliest 2026-08-30)**, so
`git cat-file -t` reports **39 of 46** references unreachable. **That number is an
artifact and must not be quoted.** Re-tested against the **remote** (the
authoritative source), the true figure is:

> **2 of 46 sha references are unreachable. 12 distinct shas, 10 reachable.**

| verdict | field | sha | status |
|---|---|---|---|
| `neiso-t3` | `scored_at_sha` | `89dacc4c0343` | **unreachable** — the one the dispatch named |
| `neiso-t3-pre-fc6` | `scored_at_sha` | `271ad606c3fd` | **unreachable — A SECOND INSTANCE, not in the dispatch** |

Both are NEISO T3 verdicts, both `scored_at_sha`, both stamped 2026-08-31, both
by the `neiso-rc-repair` lane's re-score from branch commits that never reached
`main`. **All five `solved_at_sha` references are reachable.** Both
determinations are **HOLD** and are unaffected — only the provenance is
unverifiable. **No sha was fabricated and nothing was re-scored to obtain one**
(dispatch instruction, honoured).

**The consequence is worse than "unverifiable provenance", and the board should
carry the sharper version.** `89dacc4c0343` is the **newest** scored sha on the
gate-evidence class, i.e. the anchor the staleness instrument measures from — so
`check_forecast_staleness.py` cannot measure distance at all and reports
**"Staleness is UNKNOWN, which is not the same as fresh."** The instrument
already flags this itself, and names the right two causes ("shallow clone, or
scored on an unmerged branch"). **One unreachable stamp on the newest verdict
blinds the whole board's freshness reading.** Same class as the stage-0
manifest's `af1ccb6` (v16 F-5 / v17 E-7). → **Q-2.**

### D-3 · 🟢 THE TWO R-D MAPS AGREE EXACTLY — CROSS-REFERENCED, NEITHER WITHDRAWN

Re-verified independently of the director's check. Both
`DECISION-MAP-ercot-wind-entry-2026-08-31.md` (now 290 lines) and
`MAP-c1-wind-entry-closure-2026-09.md` (now 525 lines) carry **12.313 GW**
(= 12.663 actual − 0.350 model), **1.442 GW** best posture, **8.87 %**
(= 1.092/12.313, arithmetic checked), **13.77 %** naive sum, **0.00 pp**
joint-vs-signal. **No figure disagrees.** A cross-reference header was added to
each naming the other and which is canonical for which purpose — the DECISION-MAP
for the **ruling record**, the MAP for the **fuller closure map**. Neither is
deleted or superseded. The header on the MAP also corrects its own preamble claim
to be *"the first artifact to carry R-D"*: true at its base `54d5772c`, false at
this pin, and left in place as the honest record of what that lane could see.

### D-4 · 🔴 THE CASCADE RULE'S "NO EXPOSURE ELSEWHERE" FINDING IS **OVERTURNED** — MISO CARRIES A LIVE SIBLING DEFECT

**The dispatch asked this lane to record the rule together with a negative
finding: *"a generalizable trap with no evidenced exposure in the other five ISOs
at this pin."* THAT FRAMING DOES NOT SURVIVE AT THIS PIN, and recording it would
have put a false negative on the board.**

The rule itself stands, and is worth stating on **provenance**, not on the word
"nested" — both halves are live in this repo:

> **Summing the shadow prices of distinct nested constraints is CORRECT** (a
> marginal MW relieves all of them — this is what `results/rcpf.py` does to build
> a cumulative posted price). **Summing published cumulative product prices is
> WRONG** — that price already contains the lower products', so the sum
> double-counts. **A NESTED RESERVE CASCADE MUST BE MAXED, NEVER SUMMED.**

**What changed:** PR **#4485** (`nyiso-165`, merged into this pin, **after** the
director's `240e80e4`) ran the cross-ISO scan empirically rather than by
inspection and **found a live MISO instance**. Verified independently by this
lane at the pin, not read from the finding:

- `scripts/probes/_miso171_reserve_product_decomposition.py:205–206` sums MISO's
  **published** `GENREGMCP + GENSPINMCP + GENSUPPMCP` into `total` (and
  `reg + spin` into `regspin`). The cascade is monotone in **100.0000 %** of rows
  in every year and both markets — the identical signature to NYISO's.
- Re-derived from the committed record
  `results/calibration/_miso171_reserve_product_decomposition.json`: **12 summed
  cells, `total/reg` from 1.22× to 2.49×**, concentrating in the tail. The
  finding's two quoted cells reproduce **exactly** (`da_foreseen/rt_mcp`
  $181.40 vs $76.88 = **2.36×**; `scarce47/rt_mcp` $97.62 vs $46.44 = **2.10×**).
- **Mitigations confirmed:** the per-product fields are recorded alongside and are
  correct, so the record is recoverable without a re-solve; and **no prose cites a
  summed figure.** ⚠️ **A grep for `regspin` in `docs/` returns hits that are NOT
  citations** — they are the model-side `miso_rbdc_regspin` *mechanism* family, an
  unrelated name collision. Recorded so the next reader does not mistake them for
  exposure.
- **PJM, NEISO, CAISO, ERCOT are cleared with evidence** (PJM carries the cascade
  but pins a single product; NEISO deliberately uses the cascade top alone; CAISO's
  additions are nested-**region**, the legitimate half; ERCOT's are **MW
  quantities**, legitimately additive). **The director's negative finding was right
  about four of five ISOs and wrong about MISO** — and the difference is that #4485
  measured the data where the director inspected the code.

**Nothing was done about it here, and that is correct.** Rule 25 `[R-ISO-SCOPE]`:
a NYISO verdict never fills MISO's cell. No intake was touched, no cross-ISO audit
opened — **the calibration desk's call, not this program's**. → **Q-3.**

### D-5 · 🟠 THREE DIRECTOR-DESK DEFECTS, RECORDED BECAUSE THIS BOARD TRACKS ITS OWN

- **(a) A NEW FAILURE SHAPE: "LANDED BUT INCOMPLETE."** The v17 records lane was
  dispatched to execute R-I and instead **recorded it as F-6 and moved on**. This
  is *not* the shape the board has been watching for. v17's F-10 and the refresh
  protocol check **dispatch-vs-launch** — the two consecutive *never-launched*
  lanes. A lane that launches, lands, writes a correct finding, and **silently
  omits the repair it was dispatched to make** passes every never-launched check.
  **The next dispatch-vs-launch check must look for "landed but incomplete" as
  well as "never launched"** — i.e. diff each dispatched lane's *jobs* against its
  *artifacts*, not merely confirm a branch merged. Had this repair not been
  re-dispatched, F-6 would have sat on the board as a permanent standing
  observation of a defect that was one edit from repair.
- **(b) THE DUPLICATE R-D DISPATCH — ATTRIBUTED TO THE DIRECTOR.** R-D's map was
  produced twice by two lanes in the same window because the map was dispatched
  *after* the records lane had already executed it. **Neither lane erred**, and
  the two agree exactly (D-3). The dispatch ledger did not reflect work already
  landed at dispatch time — the same root cause as (a), read from the other end.
- **(c) THE DIRECTOR'S OWN DERIVATION BUG — a `null` frontier read as ACTIVE via
  `or {}`.** A withdrawn frontier block that is present-but-`null` fell through an
  `or {}` default and read as active, which **nearly reported CAISO and MISO as
  gaining frontier status**. Caught before publication; the active frontier set
  was and remains **{ERCOT, NEISO, PJM}**. Recorded because a derivation script
  that fails *open* on a governance object is the same class of instrument defect
  the board names in models: `or {}` turns "declared absent" into "not declared",
  and those are opposite facts.

### D-7 · 🔴 v18b — RULING **R-H**, RECORDED FOR THE FIRST TIME: THE nyiso-161 WINTER-FACE WAIVER CARD IS **RULED**, OPTION A, NOT-YET STANDS

**Verified absent before it was written, at pin `192460b6` — i.e. AFTER the v18
delta above had landed.** `grep "R-H"` across `docs/` matches only the rule ID
`[R-HOLDOUT]`; the string as a ruling label appears in **zero** files, this
board and plan §8 included. The 2026-08-31 REFRESH sitting produced **seven**
rulings; six were on the record and **this was the seventh**.

**THE RULING.** On the nyiso-161 winter-face waiver card — the card R-F parked
behind a dated trigger — the owner ruled **OPTION A: NOT-YET STANDS.**
Exhaustively, what A *is*:

- **No rubric amendment.** The rubric is untouched.
- **No new caveat class.** In particular **no access-blocked class** is created —
  which matters beyond NYISO, because CAISO's C3a residual is CEII-blocked on
  both lever routes and would have had an immediate claim on one.
- **The v3.0 tier guard is untouched**, and the line that **only C3c is
  non-downgrading** holds. Nothing joins C3c on the ledgerable list.
- **NOT-YET continues to mean exactly what it has meant**: *one identified input
  missing, everything else clean.* The determination is not redefined to
  accommodate the card.
- **NYISO's determination is unchanged** and stands as published: **NOT-YET on
  {C3a-2025, C3c}**.
- **The MyNYISO stakeholder-account access retry stays OPEN and needs no
  ruling** — a data-access attempt, not a determination question; A does not
  close it.

**🟢 AND THE RECORD MUST CARRY WHY A GOT *STRONGER* AFTER IT WAS RULED. C3c's Q2
STRENGTHENED the basis for A.** Q2 (nyiso-164, **CONFIRM**; independently
replicated by nyiso-165 after that lane first reached the opposite answer and
retracted it) establishes that NYISO's C3c caveat is supported **by NYISO's own
evidence**, not inherited from another ISO — so the **summer face is evidenced
as a genuine model-class limitation** rather than a published quantity the model
fails to bind. That leaves the **structural route intact and better grounded
than when the card was filed**: close the **winter** face → C3a-2025 returns to
≈ **−5.6 %**, inside band → **C3c becomes the lone failure** → the rule-22
standing rule (rubric v3.3) reads **CALIBRATED**. **A is not a dead end; it is
the route that keeps the standing rule honest.**

**CONSEQUENCE, EXECUTED HERE.** Owner-queue **item 1** presented this card as
*"servable at the next sitting, not waiting on anything"* — inviting the
director to re-serve a decided card. It is **RETIRED** in the queue below with
this disposition, and **F-3's closing clause, which carried the same error, is
annotated in place.** **This board does not re-open A, does not weigh it, and
takes no position beyond recording it.**

### D-8 · 🔴 v18b — THE FAILURE SHAPE D-5(a) NAMED HAPPENED **AGAIN, TWICE, IN THE CYCLE THAT NAMED IT**

Recorded plainly, because D-5(a) exists precisely so the next cycle catches this
and the next cycle did not.

- **(a) THE LANE THAT NAMED "LANDED BUT INCOMPLETE" WAS ITSELF INCOMPLETE.** The
  v18 delta executed R-I, cleared three records defects, wrote D-5(a) — and
  **omitted R-H**, leaving the ruled card served as open on the very queue it
  refreshed. D-5(a)'s prescription (*diff each dispatched lane's jobs against its
  artifacts*) would have caught it; the lane applied it to **v17** and not to
  **itself**.
- **(b) 🔴 AND A SECOND RECORDS LANE RAN THE SAME DISPATCH IN PARALLEL, AT THE
  SAME PIN — AND SHARED THE SAME BLIND SPOT.** At pin `6c7f82dac015` two
  audit-program records lanes were live on this identical dispatch:
  `claude/audit-gate-a-repair-12ewmv` (merged as **#4488**, the v18 delta above)
  and this one. **They independently reached the same two dispatch-overturning
  corrections** — MISO's live cascade defect, and *two* unreachable
  `scored_at_sha` rather than one — which is strong evidence that zero-solve
  measurement on committed artifacts reproduces. **And both omitted R-H.**
  **DURABLE LESSON: A DUPLICATE LANE IS NOT A SAFETY NET.** Redundancy catches
  *measurement* error, because two lanes measure independently. It does **not**
  catch a *scope* omission, because both copies inherit the scope from the same
  dispatch. **Only a completeness check against the SITTING'S OWN RULING LIST
  catches that** — `grep` each ruling label, which is exactly how R-H's absence
  was finally established. **Add it to the refresh protocol as a step, not a
  habit.**
- **(c) This is D-5(b)'s root cause repeating, not a new one.** D-5(b) traced the
  duplicate R-D map to *a dispatch ledger that did not reflect work already
  landed at dispatch time*. Here the same ledger did not reflect **work already
  in flight**. **Same defect, one step earlier in the lifecycle.**

### D-9 · 🟢 v18b — DATED CORRECTION TO D-4: MISO'S CASCADE DEFECT WAS LIVE WHEN D-4 WAS WRITTEN AND IS **REPAIRED** AT THIS PIN

**D-4's finding stands in full; only its tense is stale.** D-4 was written at
`6c7f82dac015`, where
`scripts/probes/_miso171_reserve_product_decomposition.py` still summed MISO's
published `GENREGMCP`/`GENSPINMCP`/`GENSUPPMCP`. At **`192460b6`** the
xiso-cascade lane (**#4497**, `2fe2f2db` *"Repair MISO ASM-MCP cascade sum:
aggregate by per-hour top, never sum [R-ACCURATE]"*) has **repaired it at
source**: the probe now emits `top` — the **mean of the per-hour cascade
max** — plus a `sync_only_increment`, and the docstring carries a dated
correction naming the superseded `regspin`/`total` fields. The companion commit
`4ba1ef24` adds dated corrections **at every summed-figure cite site**.

**What this changes and what it does not.** The **rule is unchanged and now
carried in code as well as prose**: *A NESTED RESERVE CASCADE MUST BE MAXED,
NEVER SUMMED*, stated on the **provenance** of the number — summing distinct
nested **shadow prices** is correct and is what
`results/rcpf.py::rcpf_product_prices` legitimately does; summing **published
cumulative product prices** double-counts. **D-4's magnitudes stand** (sum/max
**1.85–2.20×** in hours cleared > $50) as the measurement of what was repaired.
**The queue item D-6/Q-3 routed to MISO's lane is therefore satisfied on its
repair half** — but its **second half is NOT**: #4485 explicitly flagged that
**the fields' downstream use was never audited**, a question neither the scan
nor the repair opened. **That half stays open, and stays MISO's** (rule 25
`[R-ISO-SCOPE]`). **This lane repaired nothing and opened no cross-ISO audit.**

### D-6 · OPEN QUEUE ITEMS ADDED (owner)

| # | item | state |
|---|---|---|
| **Q-1** | **A CI guard for gate-(a) staleness.** Four of six stamps were stale for a second consecutive cycle, and the repair is manual each time. **Deliberately NOT built here** (dispatch instruction). | **OPEN — owner decision** |
| **Q-2** | **Two unreachable `scored_at_sha` in `ff-verdicts.json`** (`neiso-t3`, `neiso-t3-pre-fc6`), blinding the staleness anchor (D-2). Needs an owner call on the remedy: re-score to obtain a real sha, or record the stamps as permanently unverifiable. **No sha may be fabricated.** | **OPEN — owner decision** |
| **Q-3** | **The cascade rule + MISO's sibling defect** (D-4). ⚠️ **UPDATED at v18b (D-9): the REPAIR HALF IS DONE** — #4497 (`2fe2f2db`) fixed the probe at source to aggregate by per-hour cascade max, with dated corrections at every cite site. **The SECOND half stays OPEN and stays MISO's:** the summed fields' **downstream use was never audited**, a question neither the scan nor the repair opened. **Not this program's call.** | **PARTLY CLOSED — repair landed #4497; downstream-use audit still routed to the calibration desk** |
| **Q-4** | 🆕 **v18b — A COMPLETENESS STEP FOR THE REFRESH PROTOCOL.** Two independent records lanes ran the same dispatch at the same pin and **both omitted ruling R-H** (D-7/D-8). Redundancy catches measurement error, not scope omission. **Proposed step, cheap and mechanical: `grep` each ruling label of the sitting against `docs/` before a records lane closes, and diff each dispatched job against a changed target file.** Recorded as a protocol proposal, **not adopted here** — the refresh protocol is the director desk's. | **OPEN — owner/director decision** |

**What this lane did NOT do**, stated so the next director does not infer it: no
solve, no scoring, no registration on either dashboard; no keeper shard,
`calibration-complete.json` or `holdout-freeze.json` edit; no matrix shard touched
(rule 26 — this lane tests no mechanism); no CI guard added; no ISO's intake
touched; neither R-D map deleted.

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

> **🔴 ↳ v18b CORRECTION — "PARKED-AND-RE-SERVABLE" IS SUPERSEDED. THE CARD IS
> NOT RE-SERVABLE; IT IS RULED.** The owner ruled it at the same 2026-08-31
> sitting, as **R-H — OPTION A, NOT-YET STANDS** — and that ruling reached no
> artifact until **v18b** (D-7), which is why this finding, and the queue item
> it fed, carried the card as open for two board versions. **F-3's account of
> R-F is accurate as history and its standing-context paragraph still holds; only
> the "servable at the next sitting" reading is withdrawn.** The queue item is
> **RETIRED**. **Do not re-serve it.**

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


## Keeper table (read from `frontend/data/backcast/keepers/<ISO>.json` and `status/<ISO>.js` at `72576ebe`)

Determinations and grade summaries parsed live from the status shards at the
pin. **C3a(RT) is the load-weighted mean-LMP error against RT actuals, per year
2023 / 2024 / 2025** — printed for every ISO because it is the criterion every
NOT-YET fail set contains, and printing it only for the failures hides how
narrow the margins are. ERCOT's row is the board's TWO-CONFIG entry (v14 D-2):
the grade column shows forward-span / carve-out / registered-3-year reads.

**Five of six `keeper` fields are byte-unchanged from v17 and that is a
re-derivation, not a carry** — all six compared byte-for-byte at `d44446e0` and
at the pin, all six determinations and grade summaries re-parsed, all eighteen
C3a(RT) magnitudes re-read from the shards. **The sixth, CAISO, moved
(220 → 231)** and its whole row is re-derived (G-10). Rubric **v3.5** on every
shard.

| ISO | Designated keeper | Determination | Grade (scored/target/fails/ledgered) | C3a(RT) 2023 / 2024 / 2025 |
|-----|-------------------|---------------|---|---|
| ERCOT | `2026-08-25-234-eastex-identity` (FORWARD, 2024–2025) **+ `2026-08-25-236-swcap-clip-k33`** (2023 carve-out) — TWO-CONFIG | **ISO-level `CALIBRATED`** (ercot-246 partition rollup) · forward `CALIBRATED` on span · carve-out `CALIBRATED` · **registered 3-yr `NOT-YET`, published untouched** | 8 / 5 / **2** / 1 (the registered 3-yr read) | **−39.7 % F** (the carve-out's year) / −0.2 % / −7.9 % |
| CAISO | ⬅ **`2026-09-01-caiso-231-b1-ungrounded`** (was `220-c1-crosswalk`) | `NOT-YET` | 8 / 6 / **1** / 1 | ⬅ **+4.1 %** / **+12.5 % F** / ⬅ **+15.6 % F** |
| PJM | `2026-08-15-pjm-162-inputclock` | **`CALIBRATED`** | 8 / **8** / 0 / **0** | +6.2 % / −0.8 % / −7.7 % |
| NYISO | `2026-08-30-nyiso-159-loss-surface` | `NOT-YET` | 8 / 6 / **2** / 0 | +2.3 % / −1.2 % / **−11.5 % F** |
| NEISO | `2026-08-17-neiso-99-joint-p1` | **`CALIBRATED`** | 8 / 7 / 0 / 1 | +3.1 % / +5.7 % / +1.7 % |
| MISO | `2026-08-30-miso-191-bexit` | `NOT-YET` | 8 / 6 / **1** / 1 | +0.1 % / −4.6 % / **−12.3 % F** |

| ISO | v19 cycle (`d44446e0..72576ebe`) |
|-----|--------------------------------|
| **ERCOT** | **Keeper unmoved — and its stage-0 row went CURRENT for the first time** (R-L, G-3): the forward config's golden is captured at HEAD with the fidelity oracle at **271 flags identical, 0 config drift**. **Its 2023 carve-out config still has no golden and cannot get one** until R-O's schema lane runs (G-6) — so "ERCOT CURRENT" means *forward only*, and full coverage is still two captures. One data-intake lane landed (ercot-248, SCED all-resource). A latent config hazard surfaced in its recorded keeper config — see Watch |
| **CAISO** | **THE CYCLE'S ONLY PROMOTION: 220 → 231** — the un-grounded-class offer re-grounding, three ERCOT-lineage bands removed from CAISO's binding path (G-10). Determination and grade **unchanged** (NOT-YET, 8/6/1/1); C3a 2023 +4.0 → **+4.1 %**, 2025 +15.5 → **+15.6 %** — kept despite a residual that did not improve, which is rule 1 `[R-STRUCT]` working. Also caiso-229 (C3a belly) and caiso-230 (above-floor decomposition). **Its stage-0 gap deepened by this promotion** |
| **PJM** | **UNMOVED and untouched for a TENTH consecutive cycle.** Still the only 8/8 zero-caveat scorecard. Its stage-0 row is CURRENT for a third cycle and is now one of **three**, not one |
| **NYISO** | **No keeper motion; five diagnostic lanes** (nyiso-165/166 AS-reference repair, nyiso-167 C3a-2025 attribution, nyiso-168 supply-curve slope, nyiso-169 congestion-gradient — the last **stopping** rather than arming, its zonal-gradient half found not carried by any binding constraint). Determination unchanged: NOT-YET {C3a-2025 −11.5 %, C3c}. **The nyiso-161 card stays RULED and RETIRED** (R-H, v18b) |
| **NEISO** | **UNMOVED on the backcast, and its stage-0 row went CURRENT** (R-L, G-3) — fidelity oracle **259 flags identical, 0 drift**; the golden is correctly **P1-only**, matching neiso-99's move off the archived P2 pass (audit row O5). Its backcast residual remains the **`final` grant itself**, still DATA-BLOCKED on the 2025 EIA-923 FINAL vintage. On the *forecast* board — a different program's — it is still the only ISO with an OPEN gate |
| **MISO** | **No keeper motion, and the busiest calibration column on the board: ELEVEN PRs across five lanes** (miso-195/196 outage-envelope, miso-197/198 CC_REGULAR + ST_GAS conduct, the xiso cascade repair). **Its stage-0 gap is now the joint-deepest** at two promotions past capture — and **restart-checklist item 5 still names MISO next**, unchanged by R-L |

**Markers at `72576ebe`, re-read live this cycle:** `complete` = **{ERCOT,
NEISO, PJM}** · **`final` = EMPTY (`[]`)** · **`holdout-freeze.json`
`active: true`, TIER-SCOPED to `locked_test` alone** · `withdrawn` = **{NYISO,
CAISO}**. All three `complete` entries remain re-keyed to their live keepers
(rule 22 D-5(b)); **the one ISO that promoted this cycle (CAISO) sits in
`withdrawn`, holds no `complete` marker, and so owed no re-key** — verified, not
assumed. **`audit_keepers.py` returns PASS: 0 failures, 0 warnings** at the pin,
run not quoted.

**NO ISO HAS EVER SPENT A LOCKED-TEST YEAR** — re-verified at the pin by walking
every registry sidecar, not restated. Across all **60** registered sidecars
(v17: 58) the solve-year histogram is **{2022: 2, 2023: 58, 2024: 54, 2025: 54}**
(per-ISO sidecar counts: ERCOT 15, MISO 15, NYISO 15, **CAISO 6**, PJM 5,
NEISO 4). The scan for any year in {≤2018, 2019, 2026} returns **NONE**. The only
out-of-training registrations remain the **two authorized 2022 validation
touchpoints** (`2026-08-05-pjm-2022-touchpoint`,
`2026-08-06-neiso-2022-corrected-basis`). NEISO's one-shot stays **NEVER GRANTED,
not spent** (D-23). *Motion note: the sidecar total rose 58 → 60, both additions
CAISO's (the caiso-231 pair), so the span widened by one ISO's registrations and
by no year.* **And 0 of the 60 is a golden capture** — the measurement behind
G-3's standing reading. This line is re-verified and republished every cycle
because WS5 Job 1 found the public site asserting its exact opposite for two
weeks.

**Determinations: ERCOT (ISO-level), PJM, NEISO `CALIBRATED` · CAISO, NYISO,
MISO `NOT-YET` — with ERCOT's registered 3-year read still NOT-YET and still
published.** **C3a appears in every NOT-YET fail set, and for CAISO and MISO it
is the ONLY failing criterion**; NYISO adds only C3c. **The alignment position
HOLDS this cycle** — see G-9.

## Workstream rollup

**🟢 A WORKSTREAM SURFACE MOVED — the first time in three cycles**, and it moved
by measurement rather than by assertion. Verified over the full
`d44446e0..72576ebe` window (**167 commits, 62 merged PRs**) with
`git diff --name-status`: **`results/regression-goldens/` MOVED** (manifest
schema v2 + two captures) and **`.github/workflows/` MOVED** (`ci.yml` gained the
gate-(a) step); **`docs/audit/` is byte-untouched**. So WS3's completion figure
below changes on evidence, WS1's is carried by measurement, and every row's
blocker is re-stated rather than re-assumed.

| WS | State | Completion | Blockers / next |
|----|-------|------------|-----------------|
| WS1 `AUDIT` | AUDIT-A **completed** (#3991). Rows **O8, O5, O4 CLOSED/RESOLVED**; **O6** is standing policy; **O7 CLOSED** (#4377) — the Door-2 attribution harness built *and* exercised, HP-1 hash-proven bit-identical, keeper untouched | **In progress ~95 %** (unchanged — `docs/audit/` byte-untouched this window) | **AUDIT-B still gated at G3 — waiting by design, and that gate is what caps this row**, not any remaining A-half work. No audit row carries an owner action this board tracks |
| WS2 `DEBUG` | **COMPLETED** — DEBUG-A ✓, DEBUG-B ✓, pjm-162 promoted, landing-verify green on merged main | **Completed** | none; no DEBUG-C continuation chartered |
| WS3 `PERF` | PERF-A ✓. **PERF-B PAUSED BY OWNER.** 🟢 Stage-0: **6 of 6 ISOs captured, and 3 of 6 now CURRENT** — NEISO + ERCOT-forward taken this window under R-L. Changes (c)/(d)/(e) merged, (a)/(b) unstarted | ⬅ **Paused ~82 %** (was ~78 % — moved on measured surface change, not estimate drift) | **Still paused, and still blocked TWICE at G2.** ⬅ 🟢 **The provenance defect that capped this row for four cycles is FIXED**: manifest **schema v2** carries `provenance` + `keeper_snapshot` **per entry**, the shared top-level `git_sha` is **removed**, and all six historical shas were recovered with evidence (G-1). 🟠 **What remains**: three rows STALE (CAISO/MISO/NYISO, each with a **pruned** provenance run — survivable by design via `keeper_snapshot`), and **ERCOT's carve-out config is still unrepresentable** until R-O's schema lane runs |
| WS4 `DOCS` | DOCS-A **completed** (#3999 + #4005); DOCS-B held | **In progress ~60 %** | **DOCS-B gated at G2 — waiting by design** |
| WS5 `SITE` | **Job 1 (site factual repair, pre-G3) COMPLETE ACROSS BOTH PASSES** (#4120/#4121, #4187/#4191). Job 2 = **SITE-A**, not started | **Job 1 COMPLETED · Job 2 not started** | **SITE-A gated at G3 — waiting by design.** Deferral list unchanged |
| WS6 `BLOAT` | Prunes B-1..B-8 merged; **BLOAT-2 CLOSED**; **BLOAT-3 ADJUDICATED and EXECUTED** (BLOAT-S2, −444.5 MiB at tip). ⬅ 🟢 **B-8, the class-level parity carve-out, EXISTS** | **Completed (charter) · gate 🟢 GREEN** | **🟢 GREEN at the pin** — `check_registry_payload_parity.py` **exit 0** (60 runs checked, 95 bundle dirs swept, 0 known-unsynced tolerated). ⬅ **The allowlist is no longer the mechanism**: a two-conjunct structural classifier admits pre-registered campaign points and replay recipe dirs, and the residual enumeration stands at **8** entries, down from **40** (G-1). Checklist item 10 is **discharged** |
| — `BENCH FRESHNESS` | `check_bench_freshness.py` / audit S1 lineage | **🟢 exit 0 at this pin — 0 STALE of 20 parts, 20 of 20 with engine drift at 6 engine commits** | ⬅ 🟢 **THE INSTRUMENT IS REPAIRED** (G-1). The **date-kind mismatch** this board diagnosed across three versions — part date read with `%ad` (author), engine commits filtered with `--since` (committer) — is fixed at source: **both sides now use the committer instant in offset-bearing form**, and `--since`'s inclusivity is verified rather than assumed. The day-granularity artefact goes with it. **So "20 of 20 with drift" is now a TRUE reading of a repaired instrument, not the artefact it was** — and it is the honest one: 6 engine commits under `src/market_sim/{data,config}/` have landed since the parts were committed. **0 STALE is still the reading that matters, and it holds.** Not gated either way; regenerate before trusting a *marginal* C1 verdict |
| — `GOLDEN-TIER-FIX` | **COMPLETED and independently verified** (#4014); first cron RED, diagnosed + fixed same-day (#4071), verified by full local four-step replay | **Completed · tier PARKED** | **🅿️ PARKED BY OWNER RULING 2026-08-22, unchanged.** CI proof **deliberately unspent**. Consequence, now three-wide: **none of the three CURRENT captures — PJM, NEISO, ERCOT-forward — can be certified byte-green** while the tier is paused |
| — `MATRIX GUARD` | rule 26 `[R-MECH-MATRIX]` CI enforcement | **🟢 GREEN at this pin** | `check_mechanism_matrix.py` **exit 0**, run not quoted: integrity OK across the base file + **6 ISO shards**; anchors **194 field + 49 row + 156 path** (v17: 194/49/152 — **+4 path anchors, no new `ScenarioConfig` field**), 0 unresolvable beyond the ratchet; keeper stamps AND §5.x prose headers match every `keepers/<ISO>.json`, held across the CAISO promotion. **`--fix-anchors` repairs 0 at this pin** — the ~243 the dispatch reported were already repaired, digits-only, by #4522 (G-8) |
| — `GATE-(a) PROVENANCE` | 🆕 rule-22 / forecast-seed cross-check | **🟢 NEW GATE, exit 0** | ⬅ Added under R-J (#4495, `ci.yml:213`, **hard**). Holds each `program-status.json` `a_keeper_marker` row against the live backcast keeper + marker state; **reads no determination**. **Fired for real eight PRs after it was built** (the caiso-231 promotion, exit 1 → re-key → exit 0, G-5). It gates the exact defect class this board re-reported for three cycles with no instrument able to see it |
| — `GOLDEN MANIFEST` | the undercounted seventh gate (`ci.yml:118`) | **🟢 exit 0** | Not new — **enforced throughout, and simply not counted** by this board's five-gate roster (G-7). It is now the **owner of the stage-0 table**: 38 manifests / 70 entries (6 enforced, 64 legacy grandfathered by the ratchet), reporting **3 with a pruned provenance run, 3 stale vs the live keeper**. Its own note is the standing reading: *a pruned provenance run is NOT a failure — top-15 retention is correct policy; it is survivable only because each entry carries its own `keeper_snapshot`* |

## Stage-0 golden staleness (RECOMPUTED at `72576ebe` — never read from a table)

Re-derived at the pin from `frontend/data/backcast/keepers/<ISO>.json` and
`results/regression-goldens/perfb-stage0/manifest.json`, **and cross-checked
against `check_golden_manifest.py`'s own output (exit 0)** — which, since R-J,
is the instrument that owns this table rather than a hand recomputation this
board performs alongside it. Each captured bundle is mapped back to its keeper
through the manifest's own `keeper_id` field, not by name.

**🟢 THE TABLE MOVED, AND IT MOVED THE RIGHT WAY FOR THE FIRST TIME.** Coverage
is **3 current / 3 stale**, up from 1 / 5 — R-L's two captures (G-3). One row
also **deepened**: CAISO promoted, so its gap widened.

**🟢 AND THE MANIFEST IS A DIFFERENT ARTIFACT NOW — schema v1 → v2.** There is
**deliberately no shared top-level `git_sha`**; every entry carries its own
`provenance` (`git_sha`, `git_sha_full`, `basis_sha`, `git_dirty`, `recorded_at`,
`env`, `highspy_version`, `source`, `recovery`) **and** a `keeper_snapshot`
copied from its provenance run's sidecar. Two consequences, both verified rather
than assumed: **(1)** the v17 defect — one capture silently re-labelling every
earlier one — is now structurally impossible, and R-L's two captures are the
demonstration (each changed only its own entry, the other four byte-identical);
**(2)** a top-15 retention prune **costs nothing**, because the snapshot outlives
the sidecar. `basis_sha` adopts the repo's existing durable primitive
(`pipeline.persist.basis_sha`), since a capture's own `git_sha` is routinely a
session-local branch commit.

| ISO | Golden captured against | Provenance run in registry | Designated keeper at `72576ebe` | Verdict |
|-----|-------------------------|---|--------------------------------|---------|
| **PJM** | 🟢 `2026-08-15-pjm-162-inputclock` (v16 window, #4369) | ✅ **PRESENT** | `2026-08-15-pjm-162-inputclock` | 🟢 **CURRENT.** Held a third cycle; PJM's keeper has now been still for **ten** |
| **ERCOT (forward)** | ⬅ 🟢 `2026-08-25-234-eastex-identity` (**captured this window**, #4509) | ✅ **PRESENT** | `2026-08-25-234-eastex-identity` | ⬅ 🟢 **CURRENT.** Fidelity oracle **PASS**: 271 meta flags identical, `scenario_config_drift == []` |
| **ERCOT (2023 carve-out)** | ❌ **NONE — and NOT CAPTURABLE at this schema** | — | `2026-08-25-236-swcap-clip-k33` | 🔴 **UNCOVERED.** `keepers` is keyed one entry per ISO, so a two-config ISO has nowhere to put a second golden. **R-O charters the schema lane; it has not launched** (G-6) |
| **NEISO** | ⬅ 🟢 `2026-08-17-neiso-99-joint-p1` (**captured this window**, #4509) | ✅ **PRESENT** | `2026-08-17-neiso-99-joint-p1` | ⬅ 🟢 **CURRENT.** Oracle **PASS**: 259 flags identical, 0 drift. Correctly **P1-only**, replacing the superseded `neiso-93-envelope` entry's P2 parquets |
| **CAISO** | `2026-08-16-caiso-197-w2-r5` (`basis_sha 9f6ff3ee`) | ⚠️ **PRUNED — survivable via `keeper_snapshot`** | ⬅ `2026-09-01-caiso-231-b1-ungrounded` | **🔴 STALE, and it DEEPENED this window** — the cycle's one promotion |
| **MISO** | `2026-08-16-miso-160-wefor-shape` (`basis_sha af1ccb6c`) | ⚠️ **PRUNED — survivable via `keeper_snapshot`** | `2026-08-30-miso-191-bexit` | **🔴 STALE**, two promotions past capture — **joint-deepest on the board, and still restart-checklist item 5's named next capture** |
| **NYISO** | `2026-08-16-nyiso-140-layup-exclusion` (`basis_sha 2dd9dbc9`) | ⚠️ **PRUNED — survivable via `keeper_snapshot`** | `2026-08-30-nyiso-159-loss-surface` | **🔴 STALE** |

**Count: 3 current / 3 stale / 0 without a golden — 3-of-6 effective coverage**,
up from 1-of-6. *(Coverage counts ISOs, not configs: ERCOT's 2023 carve-out has
no golden of its own, so **full** coverage is 7 captures, not 6, and the row above
is listed separately so the gap is not rounded away.)*

- **🟢 "WHICH TREE IS THE GOLDEN OF" IS NOW A WELL-POSED QUESTION** — per entry,
  for the first time. The per-file `content_hashes` remain the verification
  instrument, but they are no longer the *only* sound one.
- **🟢 THE RETENTION/GOLDEN COLLISION IS RECONCILED ON THE MANIFEST SIDE**, as
  E-7 required and **not** by exempting golden runs from retention. Three of six
  entries have a pruned provenance run and the gate reports it as **information,
  not failure** — the correct posture, because retention is correct policy.
- **🟠 THE PROMOTION-GAP COUNTS ARE STILL NOT RE-DERIVABLE FROM COMMITTED BYTES**,
  and are still labelled rather than re-asserted. The per-ISO keeper shards'
  git history begins 2026-08-26 while the remaining captures date 2026-08-16.
  What **is** derived here: each row's **verdict** (exact, `keeper_id` vs live
  `keeper`), the **registry-presence** column, and the **motion since v17**
  (CAISO **+1**, everyone else **+0**, byte-compared). v15's absolutes are
  carried **under v15's label**; MISO's stands at v15's eleven + 1, NYISO's at
  v15's ten + 1.
- **🟠 THE THREE STALE ROWS ARE THE THREE WHOSE KEEPERS KEEP MOVING**, which is
  the same reading as v16 and v17 — but the denominator halved, and **R-L proves
  again what Card 1 proved: a capture does not need a freeze**, only a lane whose
  keeper is still. The freeze question is now about **three** rows, not five.

## Gates

**SEVEN gates, not five — the roster is corrected at v19 (G-7).** The board's
protocol text and restart-checklist item 0 said *five*; the director's handoff
said *six*; **seven is correct**. The two that were being undercounted are
`check_gate_a_provenance.py` (`ci.yml:213`, **hard**, new this window under R-J)
and `check_golden_manifest.py` (`ci.yml:118`, enforced throughout and simply
never counted).

**All seven re-run at the pin. Exit codes captured directly, never through a
pipe; outputs read, not quoted from any previous board — and TWO of the seven
readings differ from what the dispatch asserted, both in the direction of "the
work is already done" (G-12).**

| gate | exit | reading at `72576ebe` |
|---|--:|---|
| `audit_keepers.py` | **0** | **PASS — 0 failures, 0 warnings**, over `complete` = **{ERCOT, NEISO, PJM}**, held across the CAISO promotion. **No D-5(b) re-key was owed** (CAISO is `withdrawn`) — M1 verified that rather than this board asserting it |
| `check_registry_payload_parity.py` | **0** | **OK — 60 runs checked, 95 bundle dirs swept, 0 known-unsynced tolerated** (v17: 58 / 93). ⬅ **The mechanism changed**: a class-level structural classifier now admits pre-registered points and replay recipes; the residual allowlist is **8**, down from **40** (G-1). ⚠️ The parity **red** the dispatch reported at the previous sitting (`caiso231_a0_control`) **resolved transiently** — the caiso-230/231 lane's own registrations (#4506 2026-09-01, #4515 2026-09-01) mapped the dirs; **no parity fix was needed and none was made** |
| `check_mechanism_matrix.py` | **0** | integrity OK, base + **6 ISO shards**; anchors **194 field + 49 row + 156 path** (v17: 194/49/152; **no new `ScenarioConfig` field this cycle**); keeper stamps and §5.x headers match every shard. ⬅ **0 WARNs**, and **`--fix-anchors` repairs 0** — the ~243 the dispatch measured at `8462da22` were repaired inside #4522, digits-only, unannounced (G-8) |
| `check_forecast_staleness.py` | **0** | ⬅ **Δ = 0 of 10** (WARN-level, never blocking) · **89 stamped / 57 scored** board-wide (v17: 81/49) · **31 of 55 verdict stamps undated** · ⬅ **25** distinct config epochs (v17: 24) · board inputs **all present**. **Re-run after this lane's own R-M edit: still exit 0, still anchored on `7dffe3341158`, which is reachable in `origin/main`** |
| `check_bench_freshness.py` | **0** | **20 parts checked, 0 STALE — and 20 of 20 with engine drift at 6 engine commits.** ⬅ **This is now a repaired instrument's true reading, not the artefact it was**: the `%ad`-vs-`--since` date-kind mismatch is fixed at source (G-1). The v17 exemption (MISO/2023) is gone because it was never a repair — it was a rewrite |
| `check_gate_a_provenance.py` | **0** | 🆕 **gate-(a) provenance OK — 6 rows checked: keeper identity + marker state match the backcast store; no determination read.** The dispatch's **exit 1** reading is the *pre-repair* one; **R-N's #4523 re-keyed CAISO and the guard has been green since** (G-5) |
| `check_golden_manifest.py` | **0** | 🆕-to-this-roster. **38 manifests, 70 entries (6 enforced / 64 legacy grandfathered by the ratchet); of the enforced, 3 with a pruned provenance run, 3 stale vs the live keeper.** This is the stage-0 table's instrument, and its own note carries the standing reading: a pruned provenance run **is not a failure** — retention is correct policy, and `keeper_snapshot` is what makes it survivable |

**Three readings moved for reasons worth separating.** Parity **58/93 → 60/95**
is CAISO's two new registrations, not a policy change; staleness
**81/49 → 89/57** and **24 → 25 epochs** are the capx desk's D25/D26/D27 window
absorbed by a different program's namespace; bench **19 → 20 of 20 with drift**
is a **repaired instrument reporting honestly**, not a degradation. **The
persistent WARN is unchanged and is not the Δ: 31 of 55 verdict stamps record no
scored-at date**, so their freshness is UNKNOWN regardless of what the newest
scored one says — and the **25 distinct config epochs** line is the one worth
reading twice: runs on that board are being compared across twenty-five different
config identities.

- **G0** adopted ✓ (2026-08-13) · **G1** DECLARED ✓ (2026-08-16, #4006).
- **G2 — UNREACHABLE, still behind TWO owner parks.** Leg 1 is *PERF-B merged
  byte-green*; PERF-B is paused by owner decision **and** the golden tier that
  would certify byte-green is parked by owner ruling. The legs:
  1. **PERF-B merged byte-green** — **still doubly blocked, and the underlying
     coverage improved for the second consecutive cycle and by more**: 6 of 6
     captured, ⬅ **3 current / 3 stale**, (c)/(d)/(e) merged, (a)/(b) unstarted,
     the golden tier parked so byte-green cannot be claimed for **any** of the
     three current captures. 🟢 **The manifest's provenance defect — a standing
     drag on this leg for four cycles — is FIXED** (schema v2, per-entry, G-1).
     🟠 **A NEW leg-1 sub-blocker is named**: ERCOT's carve-out config cannot be
     captured at all until R-O's schema lane runs (G-6).
  2. **One completed fast-tier-green `ci.yml` run** — **🟢 OBTAINABLE AND
     DECISION-FREE, for a fourth consecutive cycle**, and now on a wider base:
     **all seven** guards exit 0 at the pin, having held green across a 62-PR
     window, two registrations, two golden captures, a keeper promotion and two
     new CI checks. **This is the one G2 leg closeable today without an owner
     decision**; re-run the gates rather than trusting this line.
  3. **A keeper freeze** — **owner call, DEFERRED BY OWNER DIRECTION.** 🆕 **The
     evidence moved again and it cuts back toward v16's reading, not v17's:**
     R-L took **two** captures inside a 62-PR window with no freeze at all, in
     two lanes whose keepers happened to be still. **Two independent
     demonstrations now** (Card 1, R-L) that the scoped-capture route works. The
     freeze question is down to **three** stale rows, from five.
  4. **Branch-protection flip** — owner action, memo ready.

  On declaration the PM notifies the FFR desk (Q.2 battery).
- **G3** — unchanged: after G2, **DOCS-B** + the **BLOAT leg**. BLOAT's charter
  is satisfied (#4031 + #4047), its parity gate is **green at the pin**, and
  ⬅ **its last open recommendation (B-8, the class-level carve-out) now EXISTS**,
  so the leg reads *satisfied-in-charter, gate-green-in-fact, and
  recommendation-discharged*. The golden-tier proof leg is satisfied by #4014 +
  the green dispatch **as evidence**, though the tier itself remains parked.
- **G4** — unchanged: SITE-A + AUDIT-B. **WS5 Job 1 is not a G4 leg.**

## Watch

- **🅿️ GOLDEN TIER — PARKED BY OWNER RULING 2026-08-22, unchanged for seven
  cycles.** The #4071 fix is merged and locally replayed green; the CI proof is
  **deliberately unspent**. Record it as a park, not a blocker — and record that
  ⬅ **the consequence is now THREE-WIDE**: PJM, NEISO and ERCOT-forward are all
  CURRENT and **none of the three can be certified byte-green**, because the tier
  that would certify them is paused. The park is costing more each cycle that
  coverage improves.
- **🟢 RETIRED — THE STAGE-0 MANIFEST'S SINGLE-SHA PROVENANCE DEFECT.** Carried
  and sharpened across v15–v18; **FIXED under R-J** (#4502). Schema v2 gives every
  entry its own `provenance` and `keeper_snapshot`, the shared top-level `git_sha`
  is **removed**, and R-L's two captures **demonstrated** the fix (each changed
  only its own entry). Retired on execution, not on argument.
- **🟢 RETIRED — THE RETENTION/GOLDEN COLLISION.** Also R-J. Reconciled **on the
  manifest side**, exactly as E-7 required and **not** by exempting golden runs
  from retention. Three of six entries have a pruned provenance run; the gate
  reports it as information, and `keeper_snapshot` makes it survivable. The
  dead-bundle class E-7 warned about was never created.
- **🟢 RETIRED — THE BENCH-FRESHNESS DATE-KIND / DAY-BOUNDARY ARTEFACT.** Also
  R-J. Both sides of the comparison now use the **committer instant in
  offset-bearing form**, and `--since`'s inclusivity is verified in the docstring
  rather than assumed. **The reading discipline it forced is retired with it** —
  "20 of 20 with drift" at this pin is a true statement about a repaired
  instrument. **What is NOT retired is the substantive caution**: 0 STALE is the
  reading that matters, engine drift is ungated by design, and a *marginal* C1
  verdict still deserves a bench regeneration first.
- **🟢 RETIRED — THE STALE FORECAST GATE-(a) STAMP CLASS.** Carried since v15 and
  the direct cause of two alignment breaks. **Now gated in CI**
  (`check_gate_a_provenance.py`, hard, `ci.yml:213`) and **proven live**: it went
  red on the caiso-231 promotion and green after R-N's re-key (G-5). ⚠️ **The
  narrower half survives and is recorded so the retirement is not read too
  broadly:** the guard checks **keeper identity + marker state** and **explicitly
  reads no determination**, and **nothing compares `frontier` membership to
  anything**. Three of the four instruments are now cross-checked. The fourth is
  not — see the next item.
- **🟠 CARRIED, NARROWED — NOTHING IN THE REPO COMPARES ALL FOUR INSTRUMENTS.**
  At this pin all four agree at **{ERCOT, NEISO, PJM}** (G-9), and the *mechanism*
  that broke the alignment twice is now gated. But the alignment itself is still
  established **only by this board re-deriving it every cycle**, and the
  `frontier` leg has no instrument at all. **A cycle of agreement is not a closed
  item** — v16 retired this on one cycle's alignment and v17 un-retired it.
- **🟠 NEW — A KEEPER SETTING ONE FIELD THROUGH TWO CHANNELS: the `ercot_wtx_*`
  CONFLICT IN THE ERCOT KEEPER'S RECORDED CONFIG.** Surfaced by R-L's capture
  and recorded verbatim rather than smoothed over: *explicit kwargs
  `{'ercot_wtx_curtailment_driver': False, …}` are stomped by `prb_overrides`
  `{'ercot_wtx_curtailment_driver': True}` in the LIVE solve (`run_year` applies
  `prb_overrides` last); recording the prb values. Pass the driver through ONE
  channel.* **Three things this is NOT**, each stated so nobody over-reads it: it
  is **the keeper's own recorded config**, not something the capture introduced;
  the golden records the `prb` values, i.e. it **reproduces the keeper's live
  behaviour**, which is what a regression baseline must do; and it is **not a
  fidelity failure** — the oracle passed at 271 flags identical, 0 drift. **What
  it IS: a latent rule-24 `[R-REGISTRY]`-adjacent hazard** — a value whose
  effective setting depends on application order rather than on the registry.
  **ROUTED TO THE CALIBRATION DESK, which owns ERCOT's config; it is not this
  program's to fix**, and this board neither adjudicates nor schedules it.
- **🔴 NEW — DO NOT QUOTE MONITORING NOTIFICATIONS; READ LOGS.** R-L's capture
  lane disclosed, rather than quietly dropping, that **three streamed progress
  events its own logs do not corroborate** arrived through session log-tail
  notifications: `Solve: 163.216s (warm)` and `Solve: 342.735s (cold)` appear in
  **no log file** (grep count 0) and match none of the twelve real ERCOT solve
  times — and **ERCOT ran zero warm solves**, so a `(warm)` ERCOT event could not
  have been genuine; `solving ERCOT 2024` **is** real but was **delivered before
  it existed in the file**. **Two fabricated, one premature.** This is an
  **infrastructure observation, not a modelling finding**, and it is on the watch
  because of what it implies for every session on this program: **a streamed
  progress notification is not evidence.** Every timing, count and status in a
  finding must be read from committed logs and artifacts. The capture lane did
  exactly that, which is why its numbers stand.
- **🟠 NEW — A SHARED, CI-GATED BASE FILE WAS REWRITTEN BY A LANE THAT DID NOT
  DECLARE IT.** #4522 (`369c9bb7`) moved **120 line-pairs** of
  `docs/codebase-site/data/mechanism-matrix.js` inside a commit whose subject and
  body are entirely about a forecast FC-6 re-score (G-8). **The edit was correct**
  — verified digits-only by normalisation — and it discharged this lane's job 4.
  **The class is the silence, not the change.** Recorded beside its own
  counter-example one PR later: **#4523 handled the same shared surface well**,
  rebasing onto the disjoint edit rather than overwriting it (G-5). Not
  adjudicated; the matrix is rule 26's surface and three desks write near it.
- **🔴 SHARPENED, THIRD INSTANCE — THE SHALLOW-CLONE TRAP, AND IT HAS COST A
  PUBLISHED READING.** G-13. Three sessions, three containers, one failure: a
  `git cat-file` absence in a shallow clone is **indistinguishable from a sha
  that never existed**. It produced **v17's wrong `af1ccb6` reading** (which R-J's
  lane overturned), and it would have made **this** lane annotate six healthy
  verdicts as permanently unverifiable had it trusted the local answer. **Nothing
  gates it.** The discipline: check `--is-shallow-repository` **before** reporting
  any absence, then `git fetch --filter=tree:0 --unshallow` (~2 s) or confirm
  against the remote API.
- **🔴 CARRIED — TWO LIVE DEFECTS IN A COMMITTED CALIBRATION REFERENCE.**
  `data/raw/_validation-source/actual_as_reserve_NYISO.parquet` — a cascade
  **sum** where the **max** is correct, and a positional `hoy` map that never
  localizes prevailing Eastern to the model's standard-time clock — in **every
  column, every year**. **Blast radius unchanged: NO keeper, NO scored result, NO
  determination**; its only consumer is the post-solve RCPF comparator for
  co-opt-off runs, `nyiso_rcpf_enabled` is False in the NYISO keeper, and rule 19
  `[R-ONE-MECH]` makes arming it alongside `energy_reserve_coopt` a hard error.
  **A trap for DIAGNOSTIC sessions, not a defect in any result.** Still on watch
  because **nothing gates it** — no CI check reads a `_validation-source/`
  reference for internal consistency. ⬅ **The sibling half in MISO is repaired**
  (#4497, D-9); **the NYISO reference itself is not.**
- **🟠 CARRIED — THE FORECAST SEED CARRIES TWO READINGS AT ONCE.** Its top-level
  prose and its per-ISO `gate` blocks disagree about who holds what. **A different
  program's file; recorded, not adjudicated.** The per-ISO blocks are the
  authority, and this board derives gate (a) from them plus the live shards,
  never from the prose. ⬅ **Narrowed in one respect**: the per-ISO blocks' *stamps*
  are now CI-guarded, so the disagreement can no longer be about which keeper a
  row names.
- **🟠 CARRIED — the standing parity-gate hazard, and it recurred this cycle in
  its mildest form.** The gate reports a LIVE lane's pre-registered control /
  recipe dirs as "dead solve output". The dispatch carried a parity **red** on
  `caiso231_a0_control` from the previous sitting; **it resolved transiently when
  that lane's own registrations landed** (#4506, #4515), with no fix made and
  none needed. **Before reporting a future parity red, check whether the named
  dirs belong to a running lane — never recommend pruning a dir a live lane
  owns.** ⬅ **The structural half is now fixed** (B-8 exists; allowlist 40 → 8),
  so the gate's green is closer to a property than the maintenance state it was.
- **🟠 CARRIED — FORECAST-BOARD STALENESS.** Δ = **0** of 10 at the pin (v17: 1).
  What stays on watch is unchanged and is not the Δ: **31 of 55 verdict stamps
  are still undated** (freshness UNKNOWN until each passes through the stamped
  scorer) and **25 config epochs** now sit on the board (v17: 24, v16: 20, v15:
  14 — grown every cycle this board has measured it); confirm mixed-vintage
  comparison is intended before reading any cross-run delta as a model effect.
  ⬅ **Two of those stamps are now annotated as permanently unverifiable** (R-M,
  G-4) — which does not change the count, and is not meant to: the annotation
  records that their freshness can never be established, rather than pretending
  it has been.
- **🟠 CARRIED, AND PARTLY ANSWERED — EVIDENCE PROSE IS GATE-CHECKED NOWHERE.**
  `check_mechanism_matrix.py` validates `keeper:` stamps and §5.x prose headers
  and passes while citation text beside them goes stale. **Whether any gate
  should read evidence text remains unruled.**
- **🟠 CARRIED — #4054 / nyiso-140 null-treatment question**, never adjudicated —
  and now eleven promotions out of reach.
- **DURABLE LESSON (unchanged; the park makes it sharper):**
  `golden-data-tier.yml` is the ONLY workflow that runs
  `scripts/regenerate_clean.py`, so any curation-time defect under
  `scripts/data/curate_*.py` has NO pre-merge signal while the tier is parked.
  **Treat curate-script changes as unguarded.**
- **🟢 DURABLE LESSON, earned again — a negative or zero-solve result with a
  proof beats a positive one without.** This window: **nyiso-169's
  congestion-gradient half found NOT CARRIED by any binding constraint and the
  lane STOPPED**; **nyiso-168 killed its one new mechanism ex ante**;
  **miso-195 refuted the remove-only outage-envelope cap at phase 0**; **caiso-231
  recorded a pre-registered gate it could not satisfy rather than dropping it**;
  and **R-J's repair lane overturned two of THIS BOARD'S standing claims in its
  own commit message**. The sharpest measurements of the cycle again came from
  the negatives and the self-corrections.
- **🆕 DURABLE LESSON — RE-DERIVE A DISPATCHED JOB'S *PRECONDITION*, NOT ONLY ITS
  FIGURES.** v15 taught *re-derive the table that cannot have changed*; v16 added
  *re-derive the reading that improved*; **v19 adds: re-derive that the job still
  needs doing.** Two of this lane's six jobs came back already-discharged (job 4,
  G-8) or moved (R-M's target, G-4). Executing either blind would have produced a
  false record — an empty commit claiming a repair, or an annotation on the wrong
  verdict. **A dispatch describes the world at derivation time; the pin is the
  world.**

## Forecast board — re-derived at `72576ebe`: ALL SIX gate-(a) stamps are CURRENT for the first time, and gate (a) equals the `complete` set again

**Re-derived, not carried — and the seed's schema was re-read rather than
assumed** (the v16 protocol amendment, applied again; this file belongs to a
different program and has been restructured more than once). Every
`gate.a_keeper_marker` was compared field-by-field against the live
`keepers/<ISO>.json` and the live `complete` block at the pin, **and
independently against `check_gate_a_provenance.py`, which now machine-checks the
same identity in CI (exit 0)**. Legs (b)/(c)/(d) and `open` are read from each
ISO's own `gate` block.

| ISO | Seed names (gate a) | Live keeper | (a) | (b) | (c) | (d) | `open` |
|---|---|---|---|---|---|---|---|
| ERCOT | `2026-08-25-234-eastex-identity` | same | ⬅ **pass — CURRENT** | fail | pass | none | false |
| PJM | `2026-08-15-pjm-162-inputclock` | same | **pass — current** | fail | pass | none | false |
| NEISO | `2026-08-17-neiso-99-joint-p1` | same | **pass — current** | pass | pass | **granted** | **TRUE** |
| CAISO | ⬅ `2026-09-01-caiso-231-b1-ungrounded` | same | **fail — ON THE MERITS**, stamp **CURRENT** (`NOT-YET`, absent from `complete`) | fail | fail | none | false |
| MISO | `2026-08-30-miso-191-bexit` | same | ⬅ **fail — ON THE MERITS**, stamp **CURRENT** (`NOT-YET`, absent from `complete`) | fail | pass | none | false |
| NYISO | `2026-08-30-nyiso-159-loss-surface` | same | ⬅ **fail — ON THE MERITS**, stamp **CURRENT** (marker **withdrawn**) | pass | pass | none | false |

**Gate (a) passers = {ERCOT, PJM, NEISO} = the `complete` set = the CALIBRATED
set = the active `frontier` set. FOUR-INSTRUMENT ALIGNMENT HOLDS** (G-9).

**🟢 AND THE STRUCTURAL CHANGE IS THE ONE TO KEEP: ZERO STALE STAMPS.** v17
reported **four of six stale** and recorded that the entire alignment break was
that staleness — a bookkeeping lag wearing the costume of a disagreement. At this
pin **every one of the six rows names its ISO's live keeper**. The last of them,
CAISO's, was re-keyed by R-N's one-push micro-supersession **after the new guard
fired for real** (G-5). **So the three failures above are failures on the merits,
and for the first time this board can say that without a caveat** — because a
hard CI gate now refuses to let a stale stamp exist.

**🟢 THE FIRST OPEN GATE IN PROGRAM HISTORY HOLDS A SECOND CYCLE.** NEISO keeps
all four legs with `open: true`, leg (d) **granted**. **This board adjudicates
none of it**: the forecast namespace is a different program's, its legs move on
that program's rulings, and **every FC-4 behind a passing leg (c) is still a FAIL
reported at full magnitude**. It is recorded because a leg this board published
as `none` for every ISO, every cycle, moved — and has now stayed moved.

**🟠 The seed still carries two readings at once** — its top-level prose and its
per-ISO blocks disagree about who holds what (Watch). ⬅ **Narrowed**: the blocks'
*stamps* are now CI-guarded, so the disagreement can no longer be about which
keeper a row names. Both recorded; **neither adjudicated**.

**🟠 AND TWO FORECAST VERDICTS ON THIS BOARD NOW CARRY A PERMANENT PROVENANCE
CAVEAT.** Under R-M (G-4), `neiso-t3-pre-fc5` and `neiso-t3-pre-fc6` are
annotated as having a `scored_at_sha` that never reached `main` and can never be
resolved. **Both are archival preserved-prior verdicts, both read `HOLD`, and
neither determination was touched.** No live gate leg above rests on either.

**No forecast run was solved or re-scored by this lane**; per rule 15
`[R-DASHBOARD]` the forecast namespace is registered through
`scripts/register_forecast_run.py` alone, and the backcast CI gates stay blind
to it. **The R-M annotation is a records edit to a committed input, not a
re-score**: no scorer ran, no determination moved, and
`check_forecast_staleness.py` exits 0 before and after.

## Owner queue at cycle end

Re-served and re-verified at **`72576ebe`**. **THE 2026-09-01 SITTING RETIRES TWO
ITEMS — Q-1 by EXECUTION (R-J) and Q-2 by EXECUTION HERE (R-M) — and ADOPTS Q-4
into the refresh protocol.** What remains:

1. **🟢 ~~Q-1 — THE FOUR UNBLOCKED MAINTENANCE ITEMS~~ — RETIRED AT v19 BY
   EXECUTION (R-J). DO NOT RE-SERVE.** All four merged and verified in the tree
   at the pin, with the commit→PR mapping derived by ancestry rather than taken
   from the dispatch: the **parity class-level carve-out** (`76c5eed6`, #4495),
   the **bench date-kind fix** (`d5c3178f`, #4495), the **stage-0 per-entry
   provenance / manifest schema v2** (`362e2771`, #4502) and the
   **`check_gate_a_provenance` hard CI guard** (`3f5a24ae`, #4495). **Restart-checklist
   items 2, 10, 11 and 12 are discharged with it.** Retired **by execution, not by
   ruling** — the thing it asked for exists (G-1).
2. **🟢 ~~Q-2 — THE `ff-verdicts.json` UNVERIFIABLE PROVENANCE STAMPS~~ — RETIRED
   AT v19 BY EXECUTION (R-M). DO NOT RE-SERVE.** The ruled remedy — **annotate as
   permanently unverifiable** — is executed in this lane's own commit, not
   described. Two verdicts annotated, **by sha rather than by key**, because the
   target had moved since the dispatch (G-4). No sha altered, none fabricated;
   both determinations `HOLD`, untouched; both `provenance` blocks byte-identical;
   `check_forecast_staleness.py` exit 0, anchored on a **reachable** sha.
3. **🟠 CARRIED, HALF-OPEN AND STAYS MISO'S — Q-3's SECOND HALF.** The repair
   half landed (#4497: the MISO cascade probe emits `top` + `sync_only_increment`
   instead of summing published cumulative product prices, with dated corrections
   at every cite site). **The half that stays open is the one #4485 explicitly
   flagged and neither the scan nor the repair opened: the fields' DOWNSTREAM USE
   was never audited.** It stays **MISO's**, per rule 25 `[R-ISO-SCOPE]`; this
   board opened no cross-ISO audit and this lane repaired nothing. The rule it
   established stands and is now carried in code as well as prose: **a nested
   reserve cascade must be MAXED, never SUMMED** — stated on the *provenance* of
   the number, since summing distinct nested **shadow prices** is correct and is
   what `results/rcpf.py::rcpf_product_prices` legitimately does.
4. **🟢 ~~Q-4 — A COMPLETENESS STEP FOR THE REFRESH PROTOCOL~~ — ADOPTED BY THE
   DIRECTOR AT v19, AND EXECUTED BY THIS LANE.** v18b proposed it and declined to
   adopt it (*"the refresh protocol is the director desk's"*). **The director has
   adopted it**; both halves are now standing protocol and both ran here: `grep`
   every ruling label of the sitting across `docs/` before a records lane closes
   (**which is how this cycle's five-ruling gap was found**), and diff every
   dispatched job against a **changed target file** (**which is what caught G-8**).
   Its rider stands: **a parallel lane is not a completeness check** — redundancy
   catches measurement error, never scope omission (G-15).
5. **🆕 NEW — R-O's SCHEMA LANE IS CHARTERED AND HAS NOT LAUNCHED.** The ERCOT
   carve-out golden is answered by a **schema change, not another capture**:
   config-partition representation in the manifest, `live_keeper` partition
   resolution in `check_golden_manifest.py`, then the carve-out capture. **At this
   pin: no branch, no PR, no commits** (G-6). Until it runs, ERCOT's stage-0 row
   is CURRENT **for its forward config only** and full ERCOT coverage stays at
   **two captures the manifest cannot express**. **Owner/director action: confirm
   the dispatch and check that it launched** — this sitting produced four
   non-launches (G-14).
6. **🔴 CALIBRATION FREEZE / WS3 RESTART — THE G2 GATE — DEFERRED BY OWNER
   DIRECTION, so G2 stays parked BY CHOICE, NOT BY DRIFT.** ⬅ **The question
   shrank this cycle and the evidence now points the other way from v17's
   reading.** R-L took **two** captures inside a 62-PR window with no freeze at
   all — a **second** independent demonstration, after Card 1, that a scoped
   capture needs only a lane whose keeper is still. **The freeze question is now
   about THREE stale rows, not five**, and the **per-entry provenance repair that
   used to be attached to this item is DONE** (R-J). Standing recommendation,
   narrowed: **a scoped, time-boxed decision taken TOGETHER with the golden
   tier's disposition** — because coverage improving while the tier stays parked
   means three CURRENT captures that cannot be certified byte-green.
7. **🟠 NEISO `final` GRANT — DATA-BLOCKED.** The 2025 EIA-923 FINAL vintage has
   **still not landed**; until it does the grant question is not servable on the
   merits. Standing and re-verified at the pin: **no ISO has ever spent a
   locked-test year** (60 sidecars walked, {≤2018, 2019, 2026} returns NONE),
   NEISO's one-shot is **NEVER GRANTED, not spent** (D-23), and the freeze is
   tier-scoped to the locked test. Data intake needs no authorization (rule 22);
   the block lifts itself when the vintage publishes.
8. **⚪ DORMANT — the ERCOT rule-16 waiver qualifier.** Unchanged, and now with a
   second load-bearing dependant: ERCOT's `complete` marker rests on the
   ercot-246 partition rollup, **and R-O's chartered schema work exists only
   because of the same partition**. Still **not servable while dormant**;
   **re-fires only if the carve-out structure changes** — which is now a more
   expensive change than it was.
9. **🟠 CARRIED, DISPOSITION UNCHANGED — the CAISO NOT-YET determination.**
   **TERMINAL REST + MAP** stands (R-3, v15 E-3). ⬅ **This cycle CAISO promoted
   (220 → 231) and the determination did not move** — C3a-2024/2025 still fail at
   **+12.5 % / +15.6 %**, the 2025 figure marginally *worse* after a
   structurally-correct repair, which is rule 1 `[R-STRUCT]` working rather than a
   setback. Owner ruling 5 stands: **C3a must genuinely pass; NOT-YET is the
   honest fallback.** Nothing is owed here.
10. **🟠 CARRIED NOTE — the nyiso-148 2025 dear-gas level card**: no signature or
    decline recorded for it in any window since; its same-day UPDATE block should
    be read before its numbers (the keeper it names is now **six** promotions
    superseded, 148 → 152 → 155 → 157 → 159).
11. **🟢 RETIRED — do not re-serve:**
    - **v19** ~~Q-1 (four maintenance items)~~ — **EXECUTED, R-J** (item 1).
    - **v19** ~~Q-2 (ff-verdicts provenance)~~ — **EXECUTED HERE, R-M** (item 2).
    - **v18b** ~~the **nyiso-161 WINTER-FACE WAIVER CARD**~~ — **RULED R-H:
      OPTION A, NOT-YET STANDS.** Full disposition at D-7. Retired **for good**:
      the owner decided it, so there is nothing left to serve. ⚠️ **Read the delay
      as the lesson it is** — the ruling existed from 2026-08-31 and reached no
      artifact until v18b, sitting on this queue as *"servable at the next
      sitting"* through two board versions and two independent records lanes
      (D-8). **The same failure shape produced this cycle's five-ruling gap.**
    - *(v17 retirements below.)*
    - ~~**arm the T1-H storage-entry repair, or don't**~~ — **RULED R-A ("Arm
      both") AND EXECUTED** (#4442).
    - ~~**the C-1 wind signal-object call**~~ — **RULED R-D: TERMINAL REST +
      MAP**, nothing armed, nothing rejected, 91.1 % of the miss published open.
    - ~~**the nyiso-leg2 promote-or-archive item**~~ — **RULED R-G: CLOSED BY
      ARCHIVE**, retired for good.
    - ~~**a PJM determination-integrity card, conditional on Q1 = PHANTOM**~~ —
      **DOES NOT OPEN.** Q1 returned **REAL**. Recorded so the conditional is
      visibly discharged rather than silently dropped.

## Session roster

> **🟠 v19 STATES ITS OWN LIMIT, as v17, v16, v15, v14 and v13 did.** This
> records lane is **not** the director desk and holds no session-listing
> authority, so it did **not** run `list_sessions`. Lane state below is derived
> from **git** (`ls-remote` branch tips, each tip tested for ancestry inside
> `origin/main` rather than read off the listing) plus one **live
> `list_pull_requests`** call at the pin. No row is carried from v17/v18 or from
> the dispatch unverified. ⚠️ **The limit that matters this cycle: it observes
> BRANCHES, not SESSIONS** — an unpushed lane is invisible to it, this lane's own
> included (G-6).

### Lane state at `72576ebe`, derived from remote branch tips + live PR list

**ONE pull request is open and TWO branches are ahead of `main`** (the PR reading
is live, not inferred). `ls-remote` returns **four** heads; each non-`main` tip
was **ancestry-tested inside `origin/main`** rather than read off the listing.

**The pin was NOT taken under a forced update** — both fetches reported a plain
fast-forward. Recorded because v17's *was*, and the condition is invisible unless
the fetch output is read.

**⚠️ `main` MOVED PAST THE PIN WHILE THIS LANE WAS WRITING** — `ls-remote` at
close reports `main` at **`663605c58e`**. **The pin is NOT moved** (pin once, then
record motion). Every figure on this board is `72576ebe`; the delta is recorded
here and re-derived by the next refresh, not absorbed silently.

| Lane | Branch | State at the pin |
|---|---|---|
| **Records v19 (this lane)** | `claude/audit-records-v19-stg058` | **🟢 WORKING** — the two program record files + the R-M annotation in `ff-verdicts.json`. Branch cut fresh at the pin, so its pack carries only this session's objects. **Not pushed at the moment of measurement, which is why it does not appear in `ls-remote`** — the same blind spot that makes this board's non-launch findings statements about branches, not about sessions (G-6) |
| **R-J — the four gate repairs** | `claude/audit-gate-repairs-sbq7km`, `claude/stage0-provenance-repair-jguqmo` | **MERGED, BRANCHES DELETED** — **#4495** (parity classifier `76c5eed6`, bench date-kind `d5c3178f`, gate-(a) guard `3f5a24ae`) and **#4502** (stage-0 schema v2 `362e2771`). ⚡ **The dispatch-vs-launch check on R-J does not read "dispatched" — it reads DONE, all four, verified in the tree** (G-1) |
| **R-L — the stage-0 capture lane** | `claude/stage0-capture-neiso-ercot-elgk62` | **MERGED, BRANCH DELETED** — **#4509** (the two captures) + **#4517** (the finding). **The audit program's FIRST SOLVE LANE.** Both oracles PASS, 0 config drift; coverage 1/6 → 3/6; **registered nothing, by an accepted deviation this board now adopts as standing** (G-3). ⚡ Its own finding records that **its first dispatch never launched** |
| **R-N — the one-push micro-supersession** | `claude/audit-program-director-irzj4a` | **MERGED, BRANCH DELETED (ancestry-tested remnant)** — **#4523**, commit `6d700725`, **5 lines**. Re-keyed CAISO's gate-(a) stamp after the new guard's **first real firing**; rebased onto #4522's disjoint edit rather than overwriting it. **SPENT; the standing deviation is back in force** (G-5) |
| **R-O — the stage-0 schema lane** | *(none)* | 🔴 **NOT LAUNCHED AT THE PIN** — no branch in `ls-remote`, no open PR, no commit in the window touching `check_golden_manifest.py`'s partition handling (G-6) |
| **Records v18 / v18b (predecessors)** | `claude/audit-gate-a-repair-12ewmv`, `claude/audit-records-v18-repair-zyd5bj` | **MERGED, BRANCHES DELETED** — **#4488** and **#4498**, both inside this window (which is why the v19 span contains both predecessors' landings) |
| **R-D closure map** | `claude/c1-wind-closure-map-i2kqhr` | **MERGED, BRANCH DELETED** — **#4472**. Classified into **this program's** column by commits (*"Map the C-1 ERCOT wind-entry closure frontier (R-D deliverable)"*), not by its ISO-flavoured branch name |
| MISO calibration — 195/196/197/198 + xiso | `claude/miso-196-outage-derate-04ecf4`, `claude/miso-cc-regular-overdispatch-qm6d32`, `claude/miso-st-gas-steam-chp-calibration-9snn32`, `claude/miso-outage-envelope-calibration-w8f3j7`, `claude/xiso-cascade-scan-qqh8jc` | **ELEVEN merged PRs across five lanes** — the busiest column on the board. **#4530 is OPEN** on the ST_GAS lane (created 17:25 UTC, *after* the pin). **No keeper motion.** Not this board's work |
| CAISO calibration — 229/230/231 | `claude/caiso-229-c3a-belly-aeg5cs`, `claude/caiso-230-abovefloor-decomp-t8y4hb` | **ALL MERGED, BRANCHES DELETED** — #4482, #4493, #4499, #4506, **#4515 (the cycle's one promotion, 220 → 231)**. Recorded, not adjudicated (G-10) |
| NYISO calibration — 165–169 | five branches | **SIX merged PRs** — #4473, #4485, #4504, #4518, #4524, #4527. **No keeper motion**; nyiso-169 **stopped** rather than arming. Not this board's work |
| ERCOT calibration — 248 | `claude/ercot-248-sced-allresource-intake-xzg2qy` | **MERGED** — #4484, a SCED all-resource data intake. Not this board's work |
| capx lanes — **A DIFFERENT PROGRAM** | `claude/capx-*` (16 branches), **`claude/neiso-rc-repair-fymtkz`**, **`claude/market-sim-calibration-director-lckr9a`**, `claude/capx-director-refresh-0z0e0f` | **TWENTY-EIGHT merged PRs across EIGHTEEN lanes.** **Not this board's work**, per the standing conflation warning. ⚠️ **The branch-name hazard REVERSED this cycle**: `market-sim-calibration-director` is **the capx director's own desk** (every commit titled `capx-director r#22…r#26`; touches only the capx handoff/ledger/prompt-pack) and `neiso-rc-repair` (#4467) is a **T1-X forecast hindcast lane** (writes `frontend/data/forecast`, `results/hindcast`, `register_forecast_run.py`). Together **6 of the desk's 28 PRs wear calibration-shaped names** — and **#4467 is the lane that minted both of R-M's unverifiable stamps** (G-4). `capx-director-refresh-0z0e0f` is **AHEAD of `main`** at the pin |

**The honest reading: the branch check did its job in both directions again, and
this cycle its most valuable result was a NEGATIVE one.** Every lane this cycle's
PRs imply was found as a branch or as a deleted branch with merged PRs behind it;
**nothing was assumed launched without one**; and **R-O's chartered lane was found
absent**, which is the check's whole purpose (G-6). The methodological sharpening
v17 added has now been paid for twice, in opposite directions: **a branch name is
a hint, not a lane classification, and the dangerous direction is a
calibration-shaped name on a capx lane** — because that one lands in the column
where it looks correct and raises no flag.

*(v17's lane table is superseded by the one above rather than duplicated; it is
recoverable verbatim from this file at `d44446e0`, and v16's at `e52b90a4`. The
v15 block below is retained in place because it carries the "⚡ Post-pin"
annotations that document how that cycle's live lanes resolved.)*

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

**⚠️ THE DEVIATION HAS NOW BEEN SUPERSEDED TWICE, EACH TIME FOR ONE SITTING, AND
IS BACK IN FORCE.** The 2026-08-30 decision-card sitting executed its own records
duties in-session under an explicit one-sitting supersession (v16 F-10); the
2026-09-01 sitting granted a **one-push micro-supersession**, ruling **R-N**,
spent as **#4523** (5 lines, the CAISO gate-(a) re-key — G-5). **Both are spent
and neither carries forward.** The standing deviation governs, this lane is its
dispatched instrument, and a future sitting that wants to write directly needs
its own supersession.

**🟢 Q-4 IS ADOPTED (2026-09-01). Two steps are now MANDATORY before a records
lane closes**, and both ran here (G-15):

- **(i) `grep` EVERY ruling label of the sitting across `docs/`.** Not the ones
  the dispatch highlights — every one, A through the current letter. At this pin
  it returned **ZERO for R-J, R-K, R-M, R-N and R-O**, which is how a
  five-ruling, two-sitting gap was found. It is the same instrument that finally
  caught R-H, and it is mechanical, cheap and unmissable.
- **(ii) Diff EVERY dispatched job against a CHANGED TARGET FILE.** *A finding
  that describes a repair is not the repair.* Run at close for this lane:

  | job | changed target file at close |
  |---|---|
  | 1 · board v19 full refresh | `docs/handoffs/audit-program-director-board-2026-08.md` ✅ |
  | 2 · stage-0 table + R-L discharge + Watch items | same file, stage-0 / Watch sections ✅ |
  | 3 · seven gates + roster-count correction | same file, Gates + checklist item 0 ✅ |
  | 4 · mechanical anchor repair | **NO CHANGED FILE — and that is the correct outcome.** `--fix-anchors` repaired 0; the repair had already landed in #4522 (G-8). **The diff step is exactly what distinguishes "already done" from "not done"** |
  | 5 · record R-J…R-O + execute R-M | `docs/model-audit-release-plan-2026-08.md` §8 + `frontend/data/forecast/ff-verdicts.json` ✅ |
  | 6 · queue maintenance | board, Owner-queue section ✅ |

- **And the rider stands: a parallel lane is NOT a completeness check.**
  Redundancy catches *measurement* error, because two lanes measure
  independently; it does **not** catch a *scope* omission, because both inherit
  the scope from one dispatch. Two lanes both omitted R-H; that is the proof.

**v19's protocol record:**

- **🔴 THE DISPATCH-VS-LAUNCH CHECK PRODUCED FOUR NON-LAUNCHES IN ONE SITTING,
  AND TWO OF THEM WERE THIS LANE.** Recorded at the director's explicit
  instruction. **(a)** The original v19 records dispatch **never launched** — no
  branch, no session, confirmed from git and the session roster. **(b)** The
  **first re-issue of the same dispatch also never launched**, on the same
  evidence; the records debt therefore stood **two sittings deep**, and this is
  the **third** dispatch and the first to run. **(c)** R-L's capture lane's first
  dispatch never launched, recorded in its own finding. **(d)** **R-O's chartered
  schema lane has not launched at this pin** (G-6). **The step's yield is now the
  highest of any in this protocol**, and it costs one `ls-remote` plus one PR
  list. ⚠️ **State its limit honestly**: it observes *branches*, not *sessions* —
  this lane's own branch was unpushed at measurement time and would have failed
  its own test.
- **🆕 ADDED — RE-DERIVE A DISPATCHED JOB'S *PRECONDITION*, NOT ONLY ITS
  FIGURES.** v15: re-derive the table that cannot have changed. v16: re-derive
  the reading that improved. **v19: re-derive that the job still needs doing.**
  **Two of this lane's six jobs came back already-discharged or moved** — job 4's
  anchors were repaired by an unrelated lane between dispatch and pin (G-8), and
  R-M's target verdict was re-scored onto a healthy sha so the defect **migrated
  to a different key** (G-4). Executing either blind produces a *false record*:
  an empty commit claiming a repair, or an annotation on the wrong verdict. **A
  dispatch describes the world at derivation time; the pin is the world.**
- **🆕 ADDED — CHECK `--is-shallow-repository` BEFORE REPORTING ANY ABSENCE FROM
  GIT.** Third instance in this program, and it has now cost a published reading
  (G-13). A shallow clone's `git cat-file` miss is **indistinguishable from a sha
  that never existed**: here it reported 8 of 13 forecast provenance shas
  unreachable when the true count is **2**, and it is what produced v17's wrong
  `af1ccb6` claim. Either `git fetch --filter=tree:0 --unshallow` (~2 s) or
  confirm against the remote API. **Before reporting an absence from git,
  establish that the repository could have shown you the thing.**
- **🆕 ADDED — COUNT THE GATES FROM `ci.yml`, NOT FROM THE LAST BOARD.** The
  roster said five for four cycles, the dispatch said six; **seven is correct**
  (G-7). `check_golden_manifest.py` had been enforced at `ci.yml:118` the entire
  time and was simply never counted — and it is the instrument that *owns* the
  stage-0 table this board recomputes by hand every cycle. **Re-read the
  workflow, not the predecessor's list.**
- **🔴 PIN ONCE, THEN RECORD MOTION — held again, in both directions.**
  `origin/main` was stable across two polling rounds before the pin, and the
  fetch was **not** a forced update. The director's own two pins were **7** and
  **4** merged PRs stale by the time this lane ran, and **`main` moved past the
  pin again while this board was being written** (`663605c58e` at close). **The
  pin was not moved**; the delta is recorded in the roster.
- **🆕 SHARPENED — A BRANCH NAME IS NOT A LANE, AND THE DANGEROUS DIRECTION IS
  THE REVERSE ONE.** v17 found capx branches wearing calibration names. This
  cycle **`market-sim-calibration-director` IS the capx director's desk** and
  **`neiso-rc-repair` is a forecast hindcast lane** — 6 of that desk's 28 PRs.
  **Worse in this direction**, because a calibration-shaped name filed into the
  calibration column looks correct and raises no flag. **Classify from commit
  subjects AND touched paths, both, every cycle.**
- **Carried from v16/v17 and still live:** re-derive the reading that *improved*
  (the bench gate's WARN count *rose* this cycle and that is the repaired
  instrument, not a regression); read a restructured file's schema before its
  values (the stage-0 manifest went v1 → v2 this window — a field-set assumption
  would have read it as gutted rather than as fixed).

**Carried, restated in one line each** (full text in v10–v17): run the gates,
never quote them (exit codes captured directly, not through a pipe) · quote no
cycle count without its base sha, in the dispatch and on the board · trust no
table, including the dispatch's — re-derive from committed bytes at the pin ·
**look for the BRANCH, not a plausible-sounding commit**, and then check the
branch's *commits and paths* · a refresh is complete when the sessions exist, not
when the prompts are written · read a content-addressed identity before inferring
· **confirm `frontend/data/hindcast/` is present before quoting any
stamped/scored count** (done this cycle: *board inputs: all present*) · **say
which figures are derived and which are carried** — this board's stage-0
promotion-gap absolutes remain the current instance, labelled rather than
re-asserted.

**While the program is parked, the refresh cycle is not the live instrument it
was.** A park-period refresh confirms (a) whether the owner has ruled on anything
in the queue — **the 2026-08-31 sitting's nine rulings and the 2026-09-01
sitting's six are now ALL on the record: R-A/R-B/R-C merged before v17,
R-D/R-E/R-F/R-G at v17, R-I at the v18 delta, R-H at v18b, and R-J through R-O at
v19**; (b) whether the keeper freeze has been called — **still deferred, and this
cycle cuts back toward v16: two captures were taken with no freeze at all, and
the question is down to three stale rows**; and (c) whether the golden tier's
park has been lifted — **unchanged, and the CI proof stays deliberately unspent,
which is why none of the three CURRENT captures can be certified byte-green**.

**🟢 AND THE FOURTH THING EVERY RECORDS LANE MUST CONFIRM ABOUT ITSELF — that it
recorded every ruling of the sitting — IS NO LONGER A PROPOSAL. It is Q-4,
adopted, and it is step (i) above.** D-5(a) named *"landed but incomplete"*; the
lane that named it omitted R-H, and so did a second lane on the same dispatch.
**This cycle the same shape recurred at five times the scale — five rulings
unrecorded across two sittings — and the adopted grep is what found them.**

## RESTART CHECKLIST — for whoever un-parks the program

**Do these in order. Do not start at change (a).**

0. **🟢 `main` IS FULLY GREEN AT THE v19 PIN — re-run at `72576ebe`, exit codes
   captured directly: ALL **SEVEN** CHECKS EXIT 0.** ⚠️ **THE ROSTER IS SEVEN,
   NOT FIVE** — this item said *five* for four cycles and the v19 dispatch said
   *six*; both undercounted (G-7). The seven:
   `audit_keepers.py` **PASS 0/0** (over `complete` = {ERCOT, NEISO, PJM}) ·
   `check_registry_payload_parity.py` **exit 0** (60 runs / 95 dirs / 0
   tolerated) · `check_mechanism_matrix.py` **exit 0** (194 field + 49 row +
   **156** path anchors, **0 WARNs**) · `check_forecast_staleness.py` **exit 0,
   Δ = 0/10** (the undated-stamp WARN persists at **31 of 55**) ·
   `check_bench_freshness.py` **exit 0, 0 STALE of 20 — 20 of 20 with engine
   drift, now a REPAIRED instrument's honest reading** ·
   🆕 `check_gate_a_provenance.py` **exit 0** (`ci.yml:213`, **hard**, 6 rows) ·
   🆕 `check_golden_manifest.py` **exit 0** (`ci.yml:118` — enforced all along,
   merely never counted; it is the stage-0 table's instrument). Green for a fifth
   consecutive cycle. **Always re-run all seven rather than reading this line**,
   and **count them from `ci.yml`, not from this list** — at this repo's merge
   cadence (62 PRs in 37 hours this window) the reading ages in minutes.
0b. **🟢 THE GOLDEN PROVENANCE PROBLEM IS FIXED — DO NOT RE-DO IT.** The
   condition this item described for four cycles (one top-level `git_sha` for six
   captures; five provenance runs pruned; `af1ccb6` believed unresolvable) is
   **closed by R-J** (#4502). The manifest is **schema v2**: `provenance` +
   `keeper_snapshot` **per entry**, no shared top-level sha, all six historical
   shas recovered from history **with evidence and zero UNKNOWN rows**, and
   retention reconciled on the manifest side so a prune costs nothing. **Two of
   this board's own former claims were overturned in the process**: `af1ccb6`
   **does** resolve (it is the CAISO capture commit) and the five shas were
   recoverable all along — the "does not resolve" reading was a **shallow-clone
   artefact** (G-13). The per-file `content_hashes` are unaffected and remain a
   sound verification instrument; they are no longer the only one.
1. **DECIDE THE GOLDEN TIER AND THE FREEZE TOGETHER** — the precondition, not a
   nicety. A freeze buys re-captured goldens; a parked golden tier means those
   captures cannot be certified byte-green, so a freeze alone leaves G2 leg 1
   blocked. Un-parking costs one `workflow_dispatch` (billed minutes — why it was
   parked). 🆕 **The question is smaller again: R-L took TWO captures inside a
   62-PR window with no freeze**, after Card 1 took one. **Two independent
   demonstrations.** A freeze is not a precondition for a *scoped* capture; it is
   a question about **the three remaining stale rows** and about certifying any
   capture at all.
2. **🟢 ~~RECORD PROVENANCE PER ENTRY~~ — DONE (R-J, #4502).** Verified in the
   manifest at the pin. **Do not re-do it**; verify existing captures against
   their `content_hashes` and their own per-entry `provenance`.
3. **Re-verify every stage-0 golden against the then-current keepers** before
   resuming any change. **Do not trust this board's staleness table — and you no
   longer have to hand-recompute it**: run `check_golden_manifest.py`, which maps
   each entry back through its own `keeper_id` and reports CURRENT / STALE and
   pruned-provenance status directly. **At `72576ebe` the answer is: PJM, NEISO
   and ERCOT-forward CURRENT; CAISO, MISO and NYISO STALE (all three with a
   PRUNED provenance run, survivable via `keeper_snapshot`); and ERCOT's 2023
   carve-out UNCOVERED and not capturable at this schema.**
4. **Assume every re-capture is a real solve — and budget the memory.** 🆕
   **R-L's capture lane re-measured this and the picture is container-dependent,
   not fixed.** Card 1's PJM capture died on a **13.3 GiB cgroup memcg** at
   13.9 GB RSS and needed a 12 GB swapfile; R-L's container reported an
   effectively **unbounded** `memory.max`, so the binding constraint was physical
   RAM: ERCOT peaked at **12.50 GB** against 15 GB and **never paged** (swap
   usage 0), NEISO at **3.94 GB**. **Budget for ~12.5 GB on ERCOT and check
   `memory.max` rather than assuming Card 1's limit.** Also: R-L's container had
   **no Python dependencies at all** and needed a venv built from the pinned
   `requirements.txt`; hydration was a no-op on its full clone and **no
   converted-corpus re-fetch was required** (unlike PJM's `pjm-da-virtuals`).
   The **re-stamp-not-re-solve** shortcut is still established for **neiso-97
   only** — re-establish before relying on it.
5. **~~Capture PJM FIRST~~ — DONE (#4369). ~~Capture MISO next~~ — R-L took
   NEISO and ERCOT instead, BY OWNER RULING, AND THIS ITEM STANDS.** R-L's
   verbatim *"Just NEISO and ERCOT"* was **deliberately against this item**, for
   that capture only; it is an exception, **not an amendment** (G-3). **MISO is
   still the named next capture**, and its case is unchanged: joint-deepest gap
   on the board at two promotions past capture. **ERCOT still needs a second
   capture** — its 2023 carve-out — and that one is **blocked on R-O's schema
   lane, not on a freeze** (G-6).
6. **Do NOT re-do change (c).** It landed via #3964 and is byte-identical at
   HEAD. Verify the blob (`af34031c`) rather than re-porting it.
7. **Close the #4054 residual if you want belt-and-braces — but re-derive it, do
   not inherit it.** The NYISO keeper is **eleven** promotions past the captured
   nyiso-140 config; MISO is v15's eleven + one.
8. **Then, and only then, resume changes (a)–(e)** — and re-read the G2 leg list,
   because *merged byte-green* is what the gate wants, not captures. **Three
   CURRENT captures still do not close leg 1.**
9. **Confirm the golden tier is green IN CI before claiming any byte-green
   result** — which requires un-parking it (step 1). A tier that cannot provision
   `data/clean` cannot prove byte-identity of anything, and a local replay is not
   the gate. **This applies to all three CURRENT captures.**
9b. **KEEP THE SITTING-HANDOFF QUESTION — it is now the highest-yield step here.**
   *Did the last sitting's records duties get dispatched, or did the session end
   holding them — and if they were dispatched, did the lane LAUNCH?* **The
   2026-09-01 sitting produced FOUR non-launches** (G-14), two of them
   consecutive dispatches of the same records lane, which is why that debt stood
   two sittings deep. `ls-remote` + one live PR list. ⚠️ It observes branches, not
   sessions: an unpushed lane is invisible to it.
10. **🟢 ~~FIX THE PARITY GATE'S CLASSIFIER~~ — DONE (R-J, #4495).** The
    class-level carve-out (B-8) **exists**: a two-conjunct structural test admits
    pre-registered campaign points and replay recipe dirs, and the residual
    enumeration is **8**, down from **40** (the board's last count of 26 was
    itself 14 stale). **The gate's green is now closer to a property than the
    maintenance state it was.** The standing reading discipline survives: before
    reporting a parity red, check whether the named dirs belong to a **live**
    lane — this cycle a red on `caiso231_a0_control` resolved transiently when
    that lane's own registrations landed, and no fix was needed.
11. **🟢 ~~RECONCILE RETENTION WITH THE GOLDEN MANIFEST~~ — DONE (R-J, #4502),
    AND DONE THE WAY E-7 REQUIRED.** Each entry carries a `keeper_snapshot`
    copied from its provenance run's sidecar, so a top-15 prune costs nothing.
    **Fixed on the manifest side, NOT by exempting golden runs from retention** —
    the dead-bundle class E-7 warned about was never created. Three of six
    entries currently have a pruned provenance run and the gate reports it as
    **information, not failure**.
12. **🟢 ~~CHECK THE BENCH GATE'S DRIFT ARITHMETIC~~ — DONE (R-J, #4495).** The
    `%ad`-vs-`--since` **date-kind mismatch** and the day-granularity artefact are
    fixed at source: both sides now use the **committer instant in offset-bearing
    form**, with `--since`'s inclusivity verified rather than assumed. **So the
    reading is trustworthy now, and it reads 20 of 20 with engine drift at 6
    engine commits — a true statement, not the artefact it used to be.** The
    substantive discipline survives unchanged: **0 STALE is the reading that
    matters**, engine drift is ungated by design, and a *marginal* C1 verdict
    still deserves a bench regeneration first.
13. **🆕 RUN R-O's SCHEMA LANE BEFORE CLAIMING FULL ERCOT COVERAGE.** The
    manifest keys `keepers` one entry per ISO, so ERCOT's two-config partition
    **cannot be represented** and its 2023 carve-out golden cannot be taken at
    all. Three parts, in order: config-partition representation in the manifest;
    `live_keeper` partition resolution in `check_golden_manifest.py`; then the
    capture. **Chartered by R-O and NOT LAUNCHED as of `72576ebe`** (G-6). Until
    it runs, "ERCOT CURRENT" means *forward config only* and full coverage is
    **7 captures, not 6**.
