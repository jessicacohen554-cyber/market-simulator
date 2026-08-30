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
> ### 🟢 NEW AT v15 — EVERY 2026-08-30 PM-SITTING RULING IS EXECUTED, NOT MERELY DISPATCHED
>
> v14 closed with four rulings *ruled*; v15 opens with all four **landed and
> verified at the pin**. **R-1** — the NYISO frontier block now carries its
> currency annotation (#4342, `4c63b05`), retiring v14 owner-queue item 1, the
> board's top item for two cycles. **R-2** — ercot-240 was **chartered and
> COMPLETED the same day** (#4341 precommit → #4344/#4345/#4348): the event-hour
> "demand gap" is adjudicated as the **DC-TIE NET IMPORT IDENTITY, exactly and
> everywhere**; the model's demand input is *not* understating real demand, and
> all three chartered demand-source candidates are REFUTED as gap carriers.
> **R-3** — caiso-222 Q1 ruled **TERMINAL REST + MAP** (#4342, `634927a`).
> **R-4** — Q2 routes (i)+(iii) armed/chartered, route (ii) **CEII access
> DECLINED**; route (iii) executed the same day as **caiso-223** (#4347/#4350).
> See E-1…E-4.
>
> ### 🟢 AND: THREE OF THE FOUR INSTRUMENTS RE-ALIGNED — THE FRONTIER SET IS NOW THE LONE OUTLIER
>
> v14 reported the four-instrument alignment **broken** (a NOT-YET keeper sitting
> on a `complete` marker). It is repaired — **not by NYISO becoming calibrated,
> but by the marker being withdrawn.** The capx **Q5-W** lane (#4343 — a
> DIFFERENT program acting on the shared marker file under its own charter)
> withdrew NYISO's `complete` marker on the uniform rule *a `complete` marker
> cannot stand on a NOT-YET keeper*, the 2026-08-06 CAISO precedent applied
> evenly. At the pin: **CALIBRATED = {PJM, NEISO} = `complete` = {NEISO, PJM} =
> forecast gate-(a) passers = {PJM, NEISO}** — three instruments agreeing — while
> **`frontier` = {PJM, NYISO, NEISO}** stands alone. **Recorded as state, not
> drift**, and the misalignment simply moved instruments rather than
> disappearing. See E-5.
>
> ### 🔵 AND: THE ercot-239 ARMED SOLVE APPEARED — AND WAS REJECTED ON ITS OWN GATES
>
> v14's dispatch named the ercot-239 r2 armed solve as an outstanding look-for.
> It **appeared and closed inside this window** (#4356): the graded ladder is a
> **REJECTED A/B probe** (kills clean, officials collapse to pre-k33, spur
> 74 → 11), escalated, **keeper untouched** — the cycle's fourth negative result
> carrying its own measurement. Its registration also pruned `ercot204` under
> top-15 retention, which **removed the ERCOT stage-0 golden's provenance run
> from the registry** (E-7).

> **STATUS: PARKED AT G1** — live rollup maintained by the program-director
> session, updated on each owner "refresh". Canonical program definition:
> `docs/model-audit-release-plan-2026-08.md` (its §8 ledger is the durable event
> record; this board is the at-a-glance state). Completion figures are the
> director's estimate against each workstream's full DoD (A+B halves).

**Snapshot (v15):** **BASE SHA FOR EVERY FIGURE ON THIS BOARD: `69ae4dc7`**
(merge of #4359), derived live from `origin/main` on 2026-08-30 — which
**advanced FIVE TIMES while this lane was measuring** (`f9eb73c7` → `a2820bdb`
→ `51f8200f` → `f02f0a4a` → `69ae4dc7`, then held stable across two polling
rounds ≈ 5 minutes before the pin was taken). The director's own derivation
base **`158a688` (merge of #4354) is REACHABLE BUT 5 MERGED PRs STALE**
(#4355–#4359). Every count below states the window it was measured over.
Nothing is carried from the dispatch, from board v14, or from any table,
unverified; **where the pin has moved past the dispatch, both states are
recorded as separate labelled measurements** (the v14 protocol amendment,
applied).

| window | span | commits | non-merge | merged PRs |
|---|---|--:|--:|---|
| **since v14's base LANDED** (`def338e..69ae4dc7`) — the v15 cycle | 2026-08-30 10:42 → 12:25 PDT | **66** | **42** | **24** (#4336–#4359) |
| since v14's addendum landed (`97ab0a5..69ae4dc7`) | same day | **60** | **39** | **21** (#4339–#4359) |
| **since the director's derivation** (`158a688..69ae4dc7`) — what moved after the prompt was written | same day | **16** | **11** | **5** (#4355–#4359) |

**Keeper motion across the board window: NONE. Zero promotions, in any ISO —
the first such cycle this board has recorded.** Re-derived rather than
asserted: every one of the six `keepers/<ISO>.json` `keeper` fields is
**byte-identical at `def338e` and at the pin**, and `git diff` over
`frontend/data/backcast/keepers/` returns **empty** across `158a688..69ae4dc7`.
The only keeper-shard byte-motion in the entire window is the **R-1 currency
annotation** on NYISO (#4342) — an annotation that explicitly rewrites no
declaration text and moves no keeper. After nine promotion events in v14's
five days, **this cycle promoted nothing and adjudicated instead**: two
findings, four phase-0/precommit rounds, one rejected A/B, one owner-ruling
execution pass.

**ONE open PR** (live `list_pull_requests` at the pin: **#4360**, caiso-224)
and **TWO branches ahead of `main`** (`ls-remote`, each tip tested for
ancestry in main rather than inferred): `claude/caiso-backcast-next-run-5u7ob7`
(+2, caiso-224 — the open PR) and `claude/ercot-239-residual-queue-lbkvbf`
(+1, ercot-239 **r3**, no PR yet). **After four consecutive cycles reporting
zero live lanes, the audit-adjacent calibration program has two running.**

**Headline, one line: every PM-sitting ruling executed, zero keeper promotions
for the first time on this board, three of four alignment instruments repaired
by a marker withdrawal rather than a calibration win, all five gates green —
and the audit workstreams did not move at all, for a third consecutive cycle.**

**⚡ POST-PIN RESOLUTION — ONE labelled follow-up measurement at `4c93575`
(merge of #4362), taken under the v14 sanctioned exception because the two
lanes this board records as LIVE both resolved while it was being written.**
The pin readings above are NOT re-pinned; this block is the second labelled
state. **caiso-224 MERGED** (#4360, `22a6a60`) — the gated
`caiso_fsno_subzonal_topology` (default off) + the G-CTRL bit-zero comparator
probe + the committed FSNO membership crosswalk. **ercot-239 r3 MERGED**
(#4361, `f375ef3`) — h3068-2024 attributed to event-exit lag; FINDING, probe,
log close and matrix note. Plus **#4362**, the capx desk's refresh #13 (a
DIFFERENT program). **So at `4c93575` there are ZERO branches ahead of main
and ZERO open PRs again** — the Session-roster reading above is a true dated
statement of the pin, and this is its resolution. **Keeper shards, the
`complete`/`withdrawn`/`final` marker file and the registry are all verified
BYTE-UNMOVED `69ae4dc7` → `4c93575`**, so every keeper-table, marker, holdout
and Stage-0 figure on this board stands unchanged. **ALL FIVE GATES RE-RUN
GREEN at `4c93575`** (exit codes captured directly, unpiped): audit_keepers
**PASS 0/0** · parity **exit 0, 56/93/0** · matrix **exit 0** · staleness
**exit 0, Δ = 4/10** · bench **exit 0, 0 STALE / 6 engine-drift**. The single
moving reading is staleness **Δ = 3 → 4**, continuing the cross-program engine
drift noted under Gates — still WARN-level, still never blocking. **Nothing in
E-1…E-7, the queue, or the checklist changes.**

## What moved — v15 CYCLE (`def338e..69ae4dc7`, "the ruling-execution cycle")

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

## What moved — v14 CYCLE (v14 record, RETAINED as history) (`b0ee254..0a5e896`, "the sitting-execution cycle")

Measured over the **since-v13-landed** window unless a change states otherwise.
Every figure re-derived at `0a5e896`. The plan's §8 ledger entry dated
2026-08-30 is the durable record of this cycle; this board is the at-a-glance
state.

### D-1 · 🟢 A NEW DIRECTOR TOOK THE DESK — and the standing deviation held

A new program-director session took over the audit-program desk on 2026-08-30.
**The standing deviation is unchanged and restated as every director entry
does:** the director issues prompts in chat and pushes NOTHING from the
director container (*"issue prompts, I don't want you doing it from here"*);
the owner launches all lanes; durable records land via a dispatched records
lane — this one. **The sitting produced four rulings and three lane
dispatches, and every one has a visible outcome at the pin** (D-2, D-4, D-5,
D-6, D-7). One protocol note recorded with relief rather than alarm: **the
dispatch-vs-launch check PASSED this cycle** — the board-refresh prompt
launched (this lane's branch exists), breaking a three-board failure streak
(v11 → v12 → v13).

### D-2 · 🟢 CARD 2 EXECUTED — ERCOT IS THE BOARD'S FIRST TWO-CONFIG KEEPER, AND THE LANE BUILT THE MACHINERY

**The owner's 2026-08-26 ruling, verbatim in the shard:** *"The keeper should
be the 2023 config that works plus the 2024-2025 keeper from before, so two
different configurations with 2024/2025 config being the forward keeper for
use in the model and 2023 as a carve out designed to address unique market
conditions for that year."* Executed by session ercot-238 and merged as
**#4313 (`f6f2cd1` — the dispatch's own base sha).**

- **Shard state, re-read live:** `keeper` = **`2026-08-25-234-eastex-identity`**
  (role FORWARD, years 2024–2025, **CALIBRATED on its designated span**,
  8/7/0/1 with the lone ledgered C3c non-downgrading under rubric v3.3) plus
  `config_partition` carve-out **`2026-08-25-236-swcap-clip-k33`** (2023,
  **CALIBRATED, zero caveats**, 8/8/0/0 — the ECRS-era regime config, ECRS
  introduced 2023-06-10). **The forward keeper's registered 3-year NOT-YET on
  {C3a-2023 −39.7 %, C3b-2023 0.730} STAYS PUBLISHED at full magnitude** —
  the coverage invariant is recorded verbatim in the shard: every training
  year covered by EXACTLY ONE designated config, a config carve under the
  owner's 2026-08-25 rule-16 `[R-ALLYEARS]` waiver (the ercot-235 charter),
  **never a year drop.**
- **The dispatch's stop condition ("report what the machinery would need and
  STOP") never fired, because the lane built the machinery:**
  `scripts/build_status.py` (partition block in the status shard),
  `scripts/calibration_verdict.py` (`years` span restriction — verdicts
  stamped `span_restricted` so a span read can never be mistaken for a
  registered determination), `scripts/dashboard_add_run.py` (every
  partition-designated run is live for retention/parity) and
  `docs/codebase-site/js/calibration-status.js` (renders both configs) all
  express two designated configs. **`audit_keepers.py` PASSES on the
  structure** — re-run at the pin, 0 failures / 0 warnings.
- **The same session executed two more signed rulings**, retiring v13 queue
  items: ruling 1 = the 59→61 band-count correction pass; ruling 2 = **the
  ercot-225 G-SPUR band-top gate card SIGNED, Option A** — v13's
  time-critical queue item 7, now closed before any post-repair keeper was
  graded lidless.
- Record: `docs/FINDING-ercot-two-config-keeper-2026-08-26.md`.

### D-3 · 🔴 THE KEEPER MOTIONS — the dispatch's three, a fourth at this board's own base sha, and the fuller shard-history inventory — AND THE ALIGNMENT BREAK

None of these had been ledgered in plan §8 before this cycle. The dispatch
names three; **the shard histories show NINE promotion events across the
window** — the dispatch's deltas block compresses each ISO to its endpoint.
The intermediates, named so the record is not lossy: ERCOT's 2023 config
passed through `235-2023-discrete-k24` (2026-08-25, owner-renewed signature
under the invoked rule-16 waiver) before `236-swcap-clip-k33` superseded it
next day, and MISO passed through `186-statusscope` (owner posture directive)
and `187-nucavail` (owner in-session directive) before 188. The endpoints,
each verified against its shard at the pin:

- **caiso-220** — `2026-08-26-caiso-220-c1-crosswalk` promoted on **direct
  owner instruction**: a measured-crosswalk **DATA-ONLY** delta (the caiso-216
  funded intake ask, executed), **NOT-YET** (8/6/1/1; C3a-2024/2025
  +12.5 %/+15.5 % F — C3a is the sole failing criterion).
- **nyiso-155** — `2026-08-25-nyiso-155-hydro-repair` promoted by **owner
  decision over a gate regression**: the chartered hydro truncated-vintage
  repair pair (armed at nyiso-108, **SILENTLY LOST from the lineage**) was
  restored and A/B'd; the repair arm registered NOT-YET on a C3a-2025
  downgrade and the owner promoted it anyway
  (`docs/FINDING-nyiso-hydro-truncation-repair-2026-08.md`).
- **miso-188** — `2026-08-30-miso-188-rvsscope` registered AND promoted
  2026-08-30, **NOT-YET on a lone load-bearing FAIL: C3a-2025 −12.3 %**
  (8/6/1/1; 2023 +3.5 % and 2024 −4.3 % both PASS).
- **🆕 nyiso-157 — AT THE PIN, NOT IN THE DISPATCH.** PR #4323 (`0a5e896`)
  promoted NYISO to **`2026-08-30-nyiso-157-par-attribution`** by owner
  ruling while this lane was measuring: shard re-keyed, `complete` entry
  re-verified per rule 22 `[R-HOLDOUT]` D-5(b) **without a solve** —
  **NOT-YET**, 8/5/3/0 (C3a-2025 −12.0 % F plus C3b and C3c fails). The same
  lane's Leg-1 A/B registered on #4318 with the **iroquois companion arm
  REJECTED on its own W-gates.**

**The consequence, stated plainly: the CALIBRATED set is now {PJM, NEISO} and
no longer equals the `complete` set {NEISO, NYISO, PJM}** — v13's
four-instrument alignment (complete = CALIBRATED = frontier = forecast
gate-(a) passers) is broken in its CALIBRATED leg by two consecutive
owner-decided NYISO promotions. The other three instruments still agree.
**And v13's "two ISOs' committed keeper bundles no longer reproduce at HEAD"
standing fact is RESOLVED BY EVENTS:** ERCOT re-solved on the EASTEX topology
(the ercot-234 bundle exists, registered, promoted — the owed Z-A re-solve
landed) and CAISO's designated keeper is now caiso-220 with a fresh committed
bundle. The restart checklist's step 0b is rewritten accordingly.

### D-4 · 🟠 O7 PHASE 0 — ESCALATE, AND THE OWNER RULED: ATTRIBUTION HARNESS AUTHORIZED, RESTORATION DECLINED

`docs/FINDING-o7-p0-seam-restoration-2026-08-26.md` (filed 2026-08-30,
`dd669d0`): **the ERCOT P0 bit-identity restoration is UNACHIEVABLE without
moving the CALIBRATED keeper** — the charter's own stop-rule fired, and the
finding escalated rather than entering Phase 1. **The P0 exposure is INHERENT,
not incidental:** R1 is a fleet-representation (cost-model) change whose
entire object is LP column structure; P0 and P1 share one `DispatchModel`'s
columns with an objective-only seam; and **the gas-commitment-bridge min-gen
floors are detected from the P0 run pattern, so P0 motion reaches P1 BOUNDS,
not just P1 prices.** Measured, not asserted: 73 of 132 committed rows —
12,474 MW, 55.3 % of the committed fleet — change commitment state in
ercot-188's own P0-delta probe; predicted keeper cost order +$1–3/MWh on the
2023 load-weighted price. **Owner ruling 2026-08-30 (director sitting,
decision card): the §5 ATTRIBUTION-HARNESS partial is AUTHORIZED** — the
decomposition harness at the existing `mc_bid_adjust` seam that makes the
P1-ladder leg of any future R1 A/B **bit-identical in P0 by construction**
(hash-provable), restoring attribution with the keeper and the mechanism
untouched; **keeper-moving restoration DECLINED; accept-as-limitation
DECLINED.** Lane dispatched the same sitting (src/ + ERCOT probes surface; no
branch visible yet at the pin). **⚡ Post-pin: the lane ran** — ex-ante
precommit (#4332, HP-1..HP-3, capture-dir discipline) and the harness probe +
toy-system tests (#4334) merged by `def338e`. **⚡⚡ 2026-08-30 (later
sitting, `claude/o7-attribution-harness-fjuvgd`): the precommitted real-year
exercise RAN AND CLOSED THE ROW — HP-1 PASS (de-laddered leg's P0 / markup /
bridge floors hash-identical to the keeper's, both adaptive passes), and the
decomposition split the 2023 236-recipe A/B into pricing −$0.02/MWh vs
commitment+interaction +$2.26/MWh of a +$2.24 whole (74/132 committed rows /
12,380 MW fresh at 236). Audit row O7 CLOSED; keeper untouched.**
(`docs/FINDING-o7-attribution-harness-2026-08-30.md`;
`results/calibration/o7_attribution_harness_2023.json`.)

### D-5 · 🟢 BENCH FINGERPRINTS — RULED, AND EXECUTED BEFORE THIS BOARD LANDED

At dispatch: stale parts **11 → 8** (NEISO 2022–2025 + PJM 2022–2025
remaining; three cleared incidentally by later registrations), with the
adjudication finding establishing the 8 are **UNLABELLED, not wrong** —
pre-stamp parts whose content is correct
(`docs/FINDING-bench-fingerprint-adjudication-2026-08.md`). **Owner ruling
2026-08-30: RE-STAMP the 8, authorized — content bytes untouched, NOT a
regeneration, and CI wiring explicitly DECLINED.** The dispatched lane
**executed before this entry landed: PR #4321 (`aeb56e8`) re-stamped all 8**,
and `check_bench_freshness.py` at the pin reads **0 STALE of 20 parts** (exit
0). Six engine-drift WARNs remain and are not gated: ERCOT 2023–2025 at 13
engine commits since write, NYISO 2023–2025 at 16 — regenerate before
trusting a *marginal* C1 verdict.

### D-6 · 🟠 caiso217_crosswalk — THE PRUNE IS RULED, REVERSING v13's STANDING NOTE BY OWNER ACT; EXECUTION OUTSTANDING

**Owner ruling 2026-08-30: PRUNE** via `dashboard_add_run.prune_iso` — the
three stores together. **This reverses v13's "NEVER prune it" standing note by
explicit owner act**: v13 read the red parity gate as the accepted cost of the
owner's caiso-219-over-caiso-217 choice; the owner has now served the decision
the other way — the replay stays deprioritized and the mid-solve checkpoint
goes. Lane dispatched the same sitting (the bench-restamp lane's second half).
**At the pin the bundle dir still exists and
`check_registry_payload_parity.py` still exits 1 on exactly that one dir** —
the red is now a ruled-disposition-in-flight, not an open decision.
**⚡ Post-pin: EXECUTED** (#4324, `f608370`) — the bundle is pruned via
`dashboard_add_run.prune_iso` and **parity exits 0 at `def338e`**. The
recurring-red era ends by executed ruling; the class-level carve-out (B-8)
remains unbuilt and stays on the restart checklist.

### D-7 · 🟠 FR-21 AT THRESHOLD — SCORER-ONLY FF-2D RE-SCORE AUTHORIZED (ZERO SOLVES)

At dispatch the forecast-board staleness reached its threshold: **Δ = 10 of
10** solve-affecting commits past the newest scored verdict evidence
(2026-08-25), with **31 of 40 verdict stamps carrying no scored-at date** —
freshness UNKNOWN regardless of the newest. **Owner ruling 2026-08-30: a
scorer-only FF-2D verdict re-score lane is AUTHORIZED — zero solves.**
Dispatched the same sitting (surface: `frontend/data/forecast/`; no branch
visible yet at the pin). **At the pin Δ has grown to 12** — the WARN now
names 12 solve-affecting commits past the evidence, and the re-score lane's
case is stronger than when it was authorized. **⚡ Post-pin: EXECUTED**
(#4325) — the 7 re-scorable verdicts re-scored at HEAD, `ff-verdicts.json`
refreshed, and **FR-21 reset to Δ = 0 at `def338e`** (newest scored
2026-08-30T17:18:18Z; `docs/FINDING-ff2d-verdict-rescore-2026-08-30.md`).
The **31-of-40 undated-stamp caveat persists** — those verdicts predate the
stamped scorer and stay freshness-UNKNOWN until each is re-scored through it.

---

## Keeper table (read from `frontend/data/backcast/keepers/<ISO>.json` and `status/<ISO>.js` at `69ae4dc7`)

Determinations and grade summaries parsed live from the status shards at the
pin. **C3a(RT) is the load-weighted mean-LMP error against RT actuals, per year
2023 / 2024 / 2025** — printed for every ISO because it is the criterion every
NOT-YET fail set contains, and printing it only for the failures hides how
narrow the margins are. ERCOT's row is the board's TWO-CONFIG entry (v14 D-2):
the grade column shows forward-span / carve-out / registered-3-year reads.

**Every cell below is byte-unchanged from v14** — and that is a re-derivation,
not a carry: all six `keeper` fields compared byte-for-byte at `def338e` and at
the pin, all six determinations and grade summaries re-parsed, all eighteen
C3a(RT) magnitudes re-read from the shards. **Zero promotions this cycle.**

| ISO | Designated keeper | Determination | Grade (scored/target/fails/ledgered) | C3a(RT) 2023 / 2024 / 2025 |
|-----|-------------------|---------------|---|---|
| ERCOT | `2026-08-25-234-eastex-identity` (FORWARD, 2024–2025) **+ `2026-08-25-236-swcap-clip-k33`** (2023 carve-out) — TWO-CONFIG | forward `CALIBRATED` on span · carve-out `CALIBRATED` · registered 3-yr **`NOT-YET`** | 8 / 7 / 0 / 1 · 8 / **8** / 0 / **0** · (8 / 5 / **2** / 1) | **−39.7 % F** (the carve-out's year) / −0.2 % / −7.9 % |
| CAISO | `2026-08-26-caiso-220-c1-crosswalk` | `NOT-YET` | 8 / 6 / **1** / 1 | +4.0 % / **+12.5 % F** / **+15.5 % F** |
| PJM | `2026-08-15-pjm-162-inputclock` | **`CALIBRATED`** | 8 / **8** / 0 / **0** | +6.2 % / −0.8 % / −7.7 % |
| NYISO | `2026-08-30-nyiso-157-par-attribution` | `NOT-YET` | 8 / 5 / **3** / 0 | +1.0 % / −2.0 % / **−12.0 % F** |
| NEISO | `2026-08-17-neiso-99-joint-p1` | **`CALIBRATED`** | 8 / 7 / 0 / 1 | +3.1 % / +5.7 % / +1.7 % |
| MISO | `2026-08-30-miso-188-rvsscope` | `NOT-YET` | 8 / 6 / **1** / 1 | +3.5 % / −4.3 % / **−12.3 % F** |

| ISO | v15 cycle (`def338e..69ae4dc7`) |
|-----|--------------------------------|
| **ERCOT** | **The busiest lane, and it promoted nothing.** ercot-240 chartered and CLOSED same-day — the event-hour demand gap is the **DC-tie net import identity** (E-2). ercot-239 r2's armed solve **appeared and was REJECTED on its own gates** (#4356; spur 74 → 11, escalated, keeper untouched), then r3 precommitted (h3068-2024). ercot-241 phase-0 **measured**: kills clear, **Phase-1 gate OPEN**. Its registration pruned `ercot204` — **which was the ERCOT stage-0 golden's provenance run** (E-7) |
| **CAISO** | **Q1 ruled TERMINAL REST + MAP; Q2 routes armed/chartered/declined** (E-3/E-4). caiso-223 executed route (iii) zero-solve: partition **P-A′** adjudicated, membership derived (42 plants / 2,701 MW), **LDF 13/13 PASS**, two-way control EXACT. Successor **caiso-224 is the cycle's live lane** (#4360 open, `caiso_fsno_subzonal_topology` **default off**). Keeper unchanged; C3a fails stand |
| **PJM** | **UNMOVED and untouched. SEVENTH consecutive cycle.** Still the only 8/8 zero-caveat scorecard, still **no stage-0 golden** — the largest coverage gap and the cheapest capture, for a seventh board running |
| **NYISO** | **Promoted nothing; annotated once.** R-1 executed — the `frontier` block now carries its currency annotation (E-1), retiring the board's top queue item. Its **`complete` marker was WITHDRAWN** by a different program's lane (#4343, E-5), so it no longer passes forecast gate (a). Two phase-0s landed: **nyiso-158** (C3b-2025 is **wholly the two faces**, 98.4 % of squared error; iroquois re-open bar **not reached**) and **nyiso-159** (loss component measured + PREREG) |
| **NEISO** | **UNMOVED and untouched.** Its entire residual remains the **`final` grant itself** — still **DATA-BLOCKED** on the 2025 EIA-923 FINAL vintage. Now one of only **two** ISOs holding a `complete` marker |
| **MISO** | **UNMOVED and untouched — the quietest MISO cycle in five boards**, after three promotions in v14. **miso-190's registration watch stays OPEN** for a third cycle (verified: no `miso-19*` sidecar; branch 139 behind main, nothing unmerged) |

**Markers at `69ae4dc7`, re-read live this cycle:** `complete` =
**{NEISO, PJM}** ⬅ **NYISO WITHDRAWN this window** (#4343) ·
**`final` = EMPTY (`_note` only)** · **`holdout-freeze.json` `active: true`,
TIER-SCOPED to `locked_test` alone** (the 2026-08-26 card-6 scope; validation
years are governed by the `complete` marker + `--holdout-authorized`) ·
`withdrawn` = **{NYISO, CAISO}** ⬅ NYISO added. Both surviving `complete`
entries are **re-keyed to their live keepers** (rule 22 D-5(b)) — and neither
keeper moved this cycle, so no re-key was owed — and **`audit_keepers.py`
returns PASS: 0 failures, 0 warnings** at the pin, run not quoted. Rubric
**v3.5**.

**NO ISO HAS EVER SPENT A LOCKED-TEST YEAR** — re-verified at the pin by
walking every registry sidecar, not restated. Across all **56** registered
sidecars the solve-year histogram is **{2022: 2, 2023: 54, 2024: 51,
2025: 51}** (per-ISO sidecar counts: ERCOT 15, MISO 15, NYISO 15, PJM 5,
NEISO 4, CAISO 2). The scan for any year in {≤2018, 2019, 2026} returns
**NONE**. The only out-of-training registrations remain the **two authorized
2022 validation touchpoints**. NEISO's one-shot stays **NEVER GRANTED, not
spent** (D-23). *Motion note: v14's post-pin histogram was {2022: 2, 2023: 54,
2024: 52, 2025: 52} over 56 sidecars; the count is unchanged because this
window pruned one 3-year run (`ercot204`) and registered one 2023-only run
(`239-graded-ladder`) — the 2024/2025 decrements are that trade, not a lost
year.* This line is re-verified and republished every cycle because WS5 Job 1
found the public site asserting its exact opposite for two weeks.

**Determinations: PJM, NEISO `CALIBRATED` · ERCOT (registered 3-yr), CAISO,
NYISO, MISO `NOT-YET` — with ERCOT's two designated configs each CALIBRATED on
their own spans.** Unchanged from v14 in every cell. **C3a appears in every
NOT-YET fail set, and for CAISO and MISO it is the ONLY failing criterion**;
NYISO adds C3b/C3c fails (8/5/3/0) and ERCOT's registered read adds C3b-2023 —
both 2023 legs carved to the ECRS-era config on the ERCOT side. **The
alignment position has changed even though no determination did** — see E-5.

## Workstream rollup

**WS1–WS6 are byte-unmoved across the v15 cycle — a third consecutive cycle.**
Verified rather than assumed: over the full `def338e..69ae4dc7` window
(**66 commits**), `git diff --name-status` returns **empty** for
`.github/workflows/` and for `results/regression-goldens/`. This board and the
plan **did** move (the PM-sitting records lane's §8 entry, #4346; and this
refresh) — records flow, not workstream motion. Percentages are unchanged by
construction; **the table below advances only the cycle counts and the gate
cells.**

| WS | State | Completion | Blockers / next |
|----|-------|------------|-----------------|
| WS1 `AUDIT` | AUDIT-A **completed** (#3991). Rows **O8, O5, O4 CLOSED/RESOLVED**; **O7 RULED** in v14 (attribution harness authorized, restoration declined) and its **probe phase landed** (#4332/#4334) | **In progress ~93 %** | **AUDIT-B gated at G3 — waiting by design.** Row **O6** is standing policy (locked-test scheduling, 2026-08-26). O7's harness is past probe; no further motion this window |
| WS2 `DEBUG` | **COMPLETED** — DEBUG-A ✓, DEBUG-B ✓, pjm-162 promoted, landing-verify green on merged main | **Completed** | none; no DEBUG-C continuation chartered |
| WS3 `PERF` | PERF-A ✓. **PERF-B PAUSED BY OWNER.** Stage-0: **5 of 6 ISOs captured**, **PJM never captured**. Changes (c)/(d)/(e) merged, (a)/(b) unstarted. `results/regression-goldens/` byte-unmoved again | **Paused ~74 %** | **Paused, not blocked — and blocked TWICE at G2.** **0 of 6 goldens match their keeper for a SIXTH consecutive cycle.** 🔴 **NEW: the ERCOT golden's provenance run was pruned out from under it this window** (E-7) — the row now carries two broken provenance links (pruned run + unresolvable `af1ccb6`) |
| WS4 `DOCS` | DOCS-A **completed** (#3999 + #4005); DOCS-B held | **In progress ~60 %** | **DOCS-B gated at G2 — waiting by design** |
| WS5 `SITE` | **Job 1 (site factual repair, pre-G3) COMPLETE ACROSS BOTH PASSES** (#4120/#4121, #4187/#4191). Job 2 = **SITE-A**, not started | **Job 1 COMPLETED · Job 2 not started** | **SITE-A gated at G3 — waiting by design.** Deferral list unchanged |
| WS6 `BLOAT` | Prunes B-1..B-8 merged; **BLOAT-2 CLOSED**; **BLOAT-3 ADJUDICATED and EXECUTED** (BLOAT-S2, −444.5 MiB at tip). The chartered work stays completed | **Completed (charter) · gate 🟢 GREEN** | **🟢 GREEN at the pin** — `check_registry_payload_parity.py` **exit 0** (56 runs checked, 93 bundle dirs swept, 0 known-unsynced tolerated), holding across a prune and a registration this window. The class-level carve-out (B-8) **still does not exist**; allowlist stands at **26** named entries |
| — `BENCH FRESHNESS` | `check_bench_freshness.py` / audit S1 lineage | **🟢 GREEN at this pin — 0 STALE of 20 parts** | Green since v14's ruled re-stamp (#4321). **Six engine-drift WARNs remain and WIDENED this window: ERCOT + NYISO, 2023–2025 each, now at 15 engine commits** (v14: 13/16) — the capx D11-R engine landings are the driver. Not gated; regenerate before trusting a *marginal* C1 verdict |
| — `GOLDEN-TIER-FIX` | **COMPLETED and independently verified** (#4014); first cron RED, diagnosed + fixed same-day (#4071), verified by full local four-step replay | **Completed · tier PARKED** | **🅿️ PARKED BY OWNER RULING 2026-08-22, unchanged.** CI proof **deliberately unspent**. Consequence: byte-green cannot be CLAIMED for G2 while the tier is paused |
| — `MATRIX GUARD` | rule 26 `[R-MECH-MATRIX]` CI enforcement | **🟢 GREEN at this pin** | `check_mechanism_matrix.py` **exit 0**, run not quoted: integrity OK across the base file + **6 ISO shards**; anchors **192 field + 49 row + 151 path**, 0 unresolvable beyond the ratchet; **keeper stamps AND §5.x prose headers match every `keepers/<ISO>.json`** — and this cycle it held across an anchor re-fix after a cross-program rebase (#4355) |

## Stage-0 golden staleness (RECOMPUTED at `69ae4dc7` — never read from a table)

Re-derived at the pin from `frontend/data/backcast/keepers/<ISO>.json` and
`results/regression-goldens/perfb-stage0/manifest.json` (`git_sha` **`af1ccb6`**,
**re-checked at the pin and still not a resolvable object**, `git_dirty: false`,
byte-unmoved — `git diff` over `results/regression-goldens/` returns empty
across all 66 commits). Each captured bundle mapped back to its keeper through
the manifest's own `keeper_id` field, not by name.

**🔴 THE CONSEQUENCE, STATED AS EVERY BOARD SINCE v11 HAS: BYTE-GREEN CANNOT
BE CLAIMED, so G2 leg 1 has TWO parked dependencies — WS3/PERF-B *and* the
golden tier — not one.**

**Promotion-gap counts are UNCHANGED from v14 in every row**, because no ISO
promoted this cycle — the first board on which the staleness table holds still.
**What did change is the ERCOT row's provenance** (E-7).

| ISO | Golden captured against | Designated keeper at `69ae4dc7` | Verdict |
|-----|-------------------------|--------------------------------|---------|
| ERCOT | `2026-08-15-ercot204-rule26-delete` ⬅ **registry sidecar PRUNED this window** (`e51a8a7d`, #4356) | `2026-08-25-234-eastex-identity` **+ 236 carve-out** | **🔴 STALE — SIX promotions past capture** (unchanged), **and now provenance-broken twice over**: the capture's run has no committed registry record and the manifest sha does not resolve. Full ERCOT coverage still needs **TWO** captures |
| NEISO | `2026-08-14-neiso-93-envelope` | `2026-08-17-neiso-99-joint-p1` | **STALE — two promotions past capture** (unchanged). The re-stamp-not-re-solve shortcut was established for **neiso-97 only**; re-establish before relying on it |
| CAISO | `2026-08-16-caiso-197-w2-r5` | `2026-08-26-caiso-220-c1-crosswalk` | **🔴 STALE — TWO promotions past capture** (unchanged) |
| MISO | `2026-08-16-miso-160-wefor-shape` | `2026-08-30-miso-188-rvsscope` | **🔴 STALE — ELEVEN promotions past capture** (unchanged). **The worst gap on the board** |
| NYISO | `2026-08-16-nyiso-140-layup-exclusion` | `2026-08-30-nyiso-157-par-attribution` | **🔴 STALE — TEN promotions past capture** (unchanged) |
| PJM | — | `2026-08-15-pjm-162-inputclock` | **NO GOLDEN — never captured**, and the keeper has now been stable for **SEVEN cycles** |

**Count: 5 stale / 0 current / 1 no-golden — 0 of 6 effective coverage for a
SIXTH consecutive cycle.** No gap widened this window (nothing promoted); the
ERCOT gap **deepened in kind rather than in count**.

- **PJM remains the cheapest capture and the largest gap, for the SEVENTH
  consecutive board:** no golden at all, a keeper unmoved for seven cycles, the
  only clean scorecard (8/8, zero caveats). Seven boards is a decision nobody
  made, restated because it is still true — **and this is the first cycle in
  which a quiet keeper table made the capture cheap in practice, not just in
  principle.**
- **🔴 "Which tree is the golden OF" is now also "which RUN is it of."** E-7's
  prune means the ERCOT `keeper_id` names a run with no committed registry
  record. The per-file `content_hashes` remain valid and remain the
  verification instrument — but a re-capture pass can no longer reconstruct
  what the ERCOT baseline was *a baseline of* from the registry alone.
- **The partition still adds a capture-coverage concept the manifest does not
  have:** one ISO, two designated configs. A re-capture pass that takes one
  ERCOT golden is not full ERCOT coverage.

## Gates

**All five re-run at the pin. Exit codes captured directly, never through a
pipe; outputs read, not quoted from any previous board.**

| gate | exit | reading at `69ae4dc7` |
|---|--:|---|
| `audit_keepers.py` | **0** | **PASS — 0 failures, 0 warnings**, now over `complete` = {NEISO, PJM} |
| `check_registry_payload_parity.py` | **0** | **OK — 56 runs checked, 93 bundle dirs swept, 0 known-unsynced tolerated** (held across a prune + a registration) |
| `check_mechanism_matrix.py` | **0** | integrity OK, base + **6 ISO shards**; anchors **192 field + 49 row + 151 path**; keeper stamps and §5.x headers match every shard |
| `check_forecast_staleness.py` | **0** | **Δ = 3 of 10** (WARN-level, never blocking) · 59 stamped / 27 scored board-wide · **31 of 43 verdict stamps undated** · **14** distinct config epochs · board inputs **all present** |
| `check_bench_freshness.py` | **0** | **20 parts checked, 0 STALE**, 6 engine-drift WARNs **@ 15 commits** |

**Two readings moved since the director's derivation at `158a688`, both from
the same cause and both recorded as separate labelled states:** staleness
**Δ = 1 → 3** and bench engine-drift **13 → 15 commits**. The driver is the
capx **D11-R** landing (#4355), which added `entry_margin_exhaustion` under
`src/market_sim/` — **a different program's engine change moving this
program's freshness instruments.** Neither is gated; both are working as
designed.

- **G0** adopted ✓ (2026-08-13) · **G1** DECLARED ✓ (2026-08-16, #4006).
- **G2 — UNREACHABLE, still behind TWO owner parks.** Leg 1 is *PERF-B merged
  byte-green*; PERF-B is paused by owner decision **and** the golden tier that
  would certify byte-green is parked by owner ruling. The legs:
  1. **PERF-B merged byte-green** — **doubly blocked**: 5 of 6 captured and
     **all 5 stale for a SIXTH cycle**, (c)/(d)/(e) merged, (a)/(b) unstarted,
     the golden tier parked so byte-green cannot be claimed, the manifest's
     `git_sha` `af1ccb6` still unresolvable — **and now the ERCOT capture's
     provenance run pruned from the registry** (E-7).
  2. **One completed fast-tier-green `ci.yml` run** — **🟢 OBTAINABLE AND
     DECISION-FREE, for a second consecutive cycle.** Both CI guards exit 0 at
     the pin and have now held green across a registry prune, a new
     registration and a cross-program rebase. **This is the one G2 leg
     closeable today without an owner decision**; re-run the gates rather than
     trusting this line.
  3. **A keeper freeze** — **owner call, DEFERRED BY OWNER DIRECTION.** 🆕 **The
     evidentiary picture changed this cycle in the freeze's favour and should
     be served as such:** after nine promotion events in v14's five days, this
     window promoted **nothing** while still landing five calibration rounds.
     A quiet keeper table is exactly the condition a re-capture pass needs —
     **but read it as one data point, not a trend, and NOT as a freeze
     arriving on its own** (two calibration lanes are live at the pin).
  4. **Branch-protection flip** — owner action, memo ready.

  On declaration the PM notifies the FFR desk (Q.2 battery).
- **G3** — unchanged: after G2, **DOCS-B** + the **BLOAT leg**. BLOAT's charter
  is satisfied (#4031 + #4047) and its parity gate is **green at the pin**, so
  the leg reads *satisfied-in-charter and gate-green-in-fact* for a second
  cycle. The golden-tier proof leg is satisfied by #4014 + the green dispatch
  **as evidence**, though the tier itself remains parked.
- **G4** — unchanged: SITE-A + AUDIT-B. **WS5 Job 1 is not a G4 leg.**

## Watch

- **🅿️ GOLDEN TIER — PARKED BY OWNER RULING 2026-08-22, unchanged for four
  cycles.** The #4071 fix is merged and locally replayed green; the CI proof is
  **deliberately unspent**. Record it as a park, not a blocker — and record the
  consequence: **every byte-green claim remains unprovable**, and G2 leg 1 is
  doubly parked.
- **🔴 NEW — A RETENTION PRUNE REMOVED A STAGE-0 GOLDEN'S PROVENANCE RUN, AND
  NOTHING CHECKED.** E-7. The prune was legitimate (top-15 retention, rule 15
  `[R-DASHBOARD]`) and every gate stayed green — **which is the point.** The
  registry-retention policy and the WS3 golden manifest reference the same run
  ids and **know nothing about each other**; a correct act in one silently
  degraded provenance in the other. Cheap mitigation for whoever un-parks WS3:
  have the re-capture pass record its provenance **inside** the manifest
  (the `content_hashes` already are) rather than by reference to a sidecar that
  retention may reclaim. **Do not "fix" this by exempting golden runs from
  retention** — that re-creates the parity gate's dead-bundle class the board
  already watches.
- **🟠 CARRIED, AND SHARPENED — EVIDENCE PROSE IS GATE-CHECKED NOWHERE.** v14's
  live instance (the NYISO frontier citation) is **CLOSED by R-1** (E-1), by
  hand, one field. The **class is untouched**: `check_mechanism_matrix.py`
  validates `keeper:` stamps and §5.x prose headers and passes while citation
  text beside them goes stale. **Whether any gate should read evidence text
  remains unruled** — now the queue's standing structural question rather than
  a live defect.
- **🆕 THE FOUR-INSTRUMENT ALIGNMENT HAS NO OWNER AND NO CHECK.** E-5. Three of
  four instruments agree at the pin; `frontier` = {PJM, NYISO, NEISO} does not.
  Nothing in the repo compares them — `audit_keepers.py` checks marker/keeper
  re-keying, not frontier membership. A `frontier` entry is a dated
  lever-queue statement, **not** a holdout authorization, so this is **not** a
  spend hazard; it is a published-state consistency question, and it is the
  reason the board must keep re-deriving all four every cycle.
- **🟠 CARRIED — THE STAGE-0 MANIFEST'S PROVENANCE SHA DOES NOT RESOLVE.**
  `af1ccb6` re-checked at this pin: still not a valid object. The per-file
  `content_hashes` remain the verification instrument. Resolve which of
  shallow-clone-vs-rewrite-orphan it is before any re-capture is trusted.
- **🟠 CARRIED — the standing parity-gate hazard.** The gate still reports a
  LIVE lane's pre-registered control/recipe dirs as "dead solve output"; before
  reporting a future parity red, check whether the named dirs belong to a
  running lane — **never recommend pruning a dir a live lane owns.** With two
  lanes live at this pin (caiso-224, ercot-239 r3), this is a live risk again,
  not a theoretical one. The class-level carve-out (B-8) **still does not
  exist**; the allowlist stands at **26** named entries.
- **🟠 CARRIED — FORECAST-BOARD STALENESS.** Δ = 3 of 10 at the pin (up from 1,
  cross-program cause — see Gates). What stays on watch is unchanged and is not
  the Δ: **31 of 43 verdict stamps are still undated** (they predate the
  stamped scorer — freshness UNKNOWN until each passes through it) and **14
  config epochs** sit on the board (up from 11); confirm mixed-vintage
  comparison is intended before reading any cross-run delta as a model effect.
- **🟠 CARRIED — the cross-ISO scorer-change precedent** (nyiso-143 D-4 rider +
  the shared-benchmark determination flip): one lane's act re-grading another
  lane's committed record, the shape rule 25 `[R-ISO-SCOPE]` exists to prevent.
  Unmoved; no ruling this window. **Adjacent and new: #4343 is a different
  program writing this program's marker file** — correctly, under its own
  charter and a uniform rule, but it is the same structural shape and belongs
  beside this item.
- **🟠 CARRIED — #4054 / nyiso-140 null-treatment question**, never
  adjudicated — and still ten promotions out of reach.
- **DURABLE LESSON (unchanged; the park makes it sharper):**
  `golden-data-tier.yml` is the ONLY workflow that runs
  `scripts/regenerate_clean.py`, so any curation-time defect under
  `scripts/data/curate_*.py` has NO pre-merge signal while the tier is parked.
  **Treat curate-script changes as unguarded.**
- **🟢 DURABLE LESSON, earned again and now four instances deep — a negative
  result with a bitwise proof beats a positive one without.** This window:
  the **ercot-239 graded ladder REJECTED on its own pre-registered gates**
  (#4356), **ercot-240** refuting all three chartered demand-gap candidates,
  **nyiso-158** closing the iroquois re-open bar on measurement, and
  **caiso-223** ending on a sufficiency gap list rather than an arm. **Zero
  keepers moved and five addresses got sharper** — this cycle is the cleanest
  demonstration of the lesson the board has recorded.

## Forecast board — gate (a) re-derived at `69ae4dc7`: ONE GATE CLOSED, and the stale-stamp count fell to three

**Re-derived, not carried.** Every `gate.a_keeper_marker.detail` in the
committed seed `frontend/data/forecast/program-status.json` was compared
field-by-field against the live `keepers/<ISO>.json` and the live `complete`
block at the pin.

| ISO | Seed names | Live keeper | Gate (a) |
|---|---|---|---|
| ERCOT | `2026-08-24-231-tie-zone-measured` | `234-eastex-identity` (+ 236) | **fail — unchanged** (no `complete` marker), stamp **STALE** |
| PJM | `pjm-162-inputclock` | same | **pass — current** |
| CAISO | `2026-08-17-caiso-200-h1-memberpanel` | `caiso-220-c1-crosswalk` | **fail — unchanged**, stamp **STALE** |
| NYISO | `nyiso-157-par-attribution` | same | **🔴 FAIL — FLIPPED FROM PASS**, stamp **CURRENT** (re-stamped by #4343 in the same act) |
| NEISO | `neiso-99-joint-p1` | same | **pass — current** |
| MISO | `2026-08-22-miso-177-rho-measured` | `miso-188-rvsscope` | **fail — unchanged**, stamp **STALE** |

**ONE GATE CLOSED — the first gate-(a) transition this board has recorded, and
it closed downward.** NYISO's `complete` marker was withdrawn (#4343, E-5), and
gate (a)'s test is charter §2.1b(2)(a) — *a designated full-span keeper AND an
entry in the `complete` block* — so removing the marker fails the gate even
though the keeper is unchanged and current. **Gate (a) passers are now
{PJM, NEISO}, still exactly the `complete` set.** Gates **(b) and (c) remain
UNSCORED.**

**🟢 And the seed-staleness class IMPROVED for the first time: four stale
stamps → THREE** (ERCOT, CAISO, MISO). NYISO's stamp is now **current** — the
Q5-W lane re-stamped it in the same act that flipped the gate, which is the
right pattern: **the lane that moves a marker re-stamps the board it drives.**
The three that remain are stale in id by one-or-more promotions and are the
residue of v14's promotion velocity; a quiet cycle did not clear them because
nothing re-stamped them.

**No forecast run was solved or re-scored by this lane**; per rule 15
`[R-DASHBOARD]` the forecast namespace is registered through
`scripts/register_forecast_run.py` alone, and the backcast CI gates stay blind
to it.

## Owner queue at cycle end

Re-served and re-verified at **`69ae4dc7`**. **The 2026-08-30 PM sitting
retired FOUR items by ruling, all now EXECUTED** (R-1 frontier annotation;
R-2 ercot-240; R-3 caiso-222 Q1; R-4 Q2 routes), which clears v14's item 1 —
the board's top item for two cycles. What remains, **with one NEW item**:

1. **🆕 NEW — THE FOUR-INSTRUMENT DIVERGENCE NOW SITS ON `frontier` ALONE.
   Does a ratified frontier need a currency rule?** At the pin: CALIBRATED =
   `complete` = gate-(a) passers = **{PJM, NEISO}**, while `frontier` =
   **{PJM, NYISO, NEISO}**. The NYISO frontier block is now *annotated* as to
   currency (R-1) but **still ratified**, on an ISO that is neither CALIBRATED
   nor `complete`. **Nothing checks this and nothing is spendable on it** — a
   frontier is a dated lever-queue statement, not a holdout authorization — so
   this is a published-consistency question, not a governance breach. The
   servable form is narrow: **should a `frontier` entry carry a standing
   currency rule (auto-annotate on promotion, or lapse when its ISO leaves
   `complete`), or is the R-1 hand-annotation the permanent pattern?** A
   records-only change either way. *(Raised because the divergence is new at
   this pin; the board takes no position on which answer is right.)*
2. **🔴 CALIBRATION FREEZE / WS3 RESTART — THE G2 GATE — DEFERRED BY OWNER
   DIRECTION, so G2 stays parked BY CHOICE, NOT BY DRIFT.** The board is
   executing an answered question. 🆕 **New datum, and it cuts the other way
   from v14's:** this window landed **zero promotions** while still running
   five calibration rounds — the first quiet keeper table on this board.
   **That is the cheap re-capture window the restart checklist says has never
   existed**, and it exists right now. It is also fragile (two lanes live at
   the pin). The standing recommendation is unchanged: **a scoped, time-boxed
   freeze decided TOGETHER with the golden tier's disposition**, with the
   `af1ccb6` verification step attached — and **E-7 adds a second reason to
   decide soon**, since retention is now demonstrably eroding golden
   provenance while WS3 sits parked.
3. **🟠 NEISO `final` GRANT — DATA-BLOCKED.** The 2025 EIA-923 FINAL vintage
   has **still not landed**; until it does the grant question is not servable
   on the merits. Standing and re-verified at the pin: **no ISO has ever spent
   a locked-test year**, NEISO's one-shot is **NEVER GRANTED, not spent**
   (D-23), and the freeze is tier-scoped to the locked test for every ISO.
   Data intake needs no authorization (rule 22) — the block lifts itself when
   the vintage publishes. 🆕 NEISO is now one of only **two** `complete` ISOs.
4. **⚪ DORMANT — the ERCOT rule-16 waiver qualifier.** Bounded by the Card-2
   implementation (the coverage invariant + both configs' records published at
   full magnitude); **re-fires only if the carve-out structure changes.** Not
   servable while dormant; recorded so it is not lost.
5. **🟠 CARRIED — rule on the cross-ISO scorer-change precedent** (nyiso-143
   D-4 rider + the shared-benchmark determination flip). No ruling this window.
   🆕 **Adjacent instance to weigh with it:** #4343, a different program
   writing this program's marker file — correctly and under a uniform rule, but
   the same structural shape.
6. **🟠 CARRIED — the T1-H capacity-entry defect (two defects, not one) still
   has no charter and no home.** The storage-entry/backstop mechanism and the
   separate wind leg, per A-7 and v13 item 11. No motion recorded this window.
7. **🟠 CARRIED, NOW WITH ITS DISPOSITION RULED — the CAISO NOT-YET
   determination.** **R-3 ruled Q1 = TERMINAL REST + MAP** (E-3): the C3a
   residual is **attributed and closed at this representation grain**, with
   W-1/W-2/W-3 armed as the **only sanctioned re-checks**. C3a-2024/2025 still
   fail at **+12.5 % / +15.5 %** and owner ruling 5 stands: **C3a must
   genuinely pass; NOT-YET is the honest fallback.** The live route is now the
   **sub-zonal representation program** (R-4 route (iii) → caiso-223 → the open
   caiso-224), explicitly a grain program and not a lever. **Nothing is owed
   here unless caiso-224 asks to arm.**
8. **🟠 CARRIED NOTE — the nyiso-148 2025 dear-gas level card**: no signature or
   decline recorded for it in any window since; its same-day UPDATE block
   should be read before its numbers (the keeper it names is now several
   promotions superseded).
9. **🟢 RETIRED THIS CYCLE (v15) — do not re-serve:**
   - ~~**the NYISO frontier-block citation of superseded nyiso-152** (v14 item
     1, v13 item 7)~~ — **RULED R-1 AND EXECUTED** (#4342; E-1). The *class*
     stays on Watch; the instance is closed.
   - ~~**the ercot-240 event-hour demand-gap question**~~ — **CHARTERED AND
     CLOSED same-day** (R-2; #4344/#4345/#4348): the gap is the **DC-tie net
     import identity**; the demand input is not understating demand (E-2).
   - ~~**the caiso-222 Q1 C3a disposition**~~ — **RULED: TERMINAL REST + MAP**
     (R-3; E-3). Folded into item 7 above as its ruled disposition.
   - ~~**the caiso-222 Q2 route census**~~ — **RULED: (i)+(iii)
     ARMED/CHARTERED, (ii) CEII DECLINED** (R-4; E-4). Route (iii) executed
     same-day as caiso-223.
   - ~~**the ercot-239 r2 armed-solve look-for**~~ — **APPEARED AND CLOSED
     REJECTED** on its own gates (#4356), keeper untouched. Not an owner item;
     retired here because v14's dispatch carried it.

## Session roster

> **🟠 v15 STATES ITS OWN LIMIT, as v14 and v13 did.** This records lane is
> **not** the director desk and holds no session-listing authority, so it did
> **not** run `list_sessions`. Lane state below is derived from **git**
> (`ls-remote` branch tips, each tip tested for ancestry inside `origin/main`
> rather than read off the listing) plus one **live `list_pull_requests`** call
> at the pin. No row is carried from v14 or from the dispatch unverified.

### Lane state at `69ae4dc7`, derived from remote branch tips + live PR list

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

### v14's lane state, retained as history (at `0a5e896`)


**ZERO branches are ahead of `main`, and ZERO pull requests are open** (the PR
reading is live, not inferred). Main advanced four times while this lane
measured, and three of the dispatch's five in-flight lanes finished inside
that window:

| Lane (dispatch name) | Branch | State at the pin |
|---|---|---|
| **Records v14 (this lane)** | `claude/director-records-v14-ledger-lhywlm` | **🟢 WORKING** — the §8 ledger entry pushed, blob-verified, **⚡ and merged (#4330)**; this board is its second file (v14 base merged #4335; this post-pin addendum follows on the recreated branch) |
| **MISO backcast calibration (miso-190)** | `claude/miso-190-backcast-calibration-okt1cn` | Branch exists, **tip AT main, nothing unmerged** — the miso-190 PREREG + gates instrument are committed (frozen before the mechanism exists); the miso-188 registration + promotion were already in main at the dispatch base |
| **NYISO eastern-seam PAR Leg-1** | `claude/nyiso-eastern-seam-par-leg1-w7s8mm` | **MERGED AND BRANCH DELETED** — #4318 (Leg-1 A/B registered; iroquois companion REJECTED on its own W-gates) + **#4323 (nyiso-157 PROMOTED by owner ruling — this board's base sha)**; ⚡ #4326 added the keeper-auditor pass (sidecar house-style repair, stale governance.note re-stamped at the generator) |
| **Bench re-stamp / caiso-217 prune** | `claude/backcast-bench-restamp-ns7tl7` | At the pin: half-landed (#4321, re-stamp — bench gate green). **⚡ Post-pin: FULLY LANDED — the prune executed (#4324, `f608370`), parity `exit 0` at `def338e`.** Branch deleted |
| **O7 attribution harness** | `claude/o7-ercot-attribution-harness-aa7yeu` | At the pin: no branch yet. **⚡ Post-pin: RAN ITS PROBE PHASE AND MERGED** — #4332 (ex-ante precommit, HP-1..HP-3) + #4334 (harness probe + toy-system tests, per-row stats kept capture-dir-only). Branch deleted |
| **FF-2D verdict re-score** | `claude/ff-2d-verdict-rescore-jh3xfs` | At the pin: no branch yet. **⚡ Post-pin: EXECUTED AND MERGED** — #4325 (7 re-scorable verdicts re-scored, FR-21 reset to Δ = 0, finding filed). Branch deleted |
| ⚡ caiso-222 owner-sitting packet | `claude/caiso-c3a-owner-decision-zwib71` | **Post-pin: MERGED #4333** — owner-sitting packet + C3a disposition probe, caiso-205 pair prune executed (sidecars 58 → 56), matrix §5.2 + CAISO shard gates stamp recorded. Branch deleted |
| ercot-239 residual queue | `claude/ercot-239-residual-queue-lbkvbf` | Merged **#4320/#4322** (zero-solve Phase-0 precommits + Amendment 1); branch survives at main — **not an audit-program lane** |
| caiso-221 south-belly | `claude/caiso-south-belly-pricing-24uv07` | Merged **#4316** (object killed with measurement); branch survives at main |
| capx-director desk | `claude/capx-director-session-pacv16` | **A DIFFERENT PROGRAM** (#4317/#4319 — the capx ledger, per the v13 conflation warning); not this board's work |

**The honest reading, post-pin: EVERY sitting-dispatched lane has now run,
merged, and deleted its branch** — the two this table originally named as
look-fors (O7 harness, FF-2D re-score) both appeared and merged within the
hour. At `def338e` the only surviving lane branches are this records lane's
and `miso-190` (at main, nothing unmerged). The branch check did its job in
both directions this cycle: every launched lane's branch was found, and
nothing was assumed launched without one.


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

**v15's protocol amendments — one passed check, one sharpened:**

- **🟢 THE DISPATCH-VS-LAUNCH CHECK PASSED AGAIN — two cycles running.** The
  v15 board-refresh prompt launched (this lane's branch exists and both files
  landed). The branch check stays: **look for the BRANCH, not a
  plausible-sounding commit.** This cycle the capx desk merged **seven** PRs
  and would again have fooled a commit-list scan. **The v14 amendment's step 0
  — check for the branches of lanes dispatched without one — was executed and
  RESOLVED:** the ercot-239 r2 armed solve, named as an outstanding look-for,
  was found by branch (`claude/ercot-239-residual-queue-lbkvbf`) and had
  already merged as #4356.
- **🔴 SHARPENED — PIN ONCE, THEN RECORD MOTION.** `origin/main` advanced
  **five times** while this lane measured (`f9eb73c7` → `a2820bdb` →
  `51f8200f` → `f02f0a4a` → `69ae4dc7`). **The v14 rule was applied literally
  and it worked:** fetch until the measurements settle (here: poll until the
  tip held stable across two rounds, ≈ 5 minutes), **pin ONCE**, then re-run
  **every** volatile check at that pin. The gates were run twice for exactly
  this reason — an early read at `f9eb73c7` and the authoritative read at the
  pin — and **two readings had moved between them** (staleness Δ 1 → 3, bench
  drift 13 → 15), both from a cross-program engine landing. **Only the pin
  reading is published as current; the dispatch-time reading is labelled as
  the director's and dated.** The sanctioned exception (one labelled follow-up
  measurement when a recorded state resolves mid-write) was **not needed this
  cycle** and no ⚡ block appears.
- **🆕 ADDED — RE-DERIVE THE TABLE THAT "CANNOT HAVE CHANGED".** The Stage-0
  staleness table's promotion counts were unchanged in every row this cycle
  (nothing promoted), and reading it forward from v14 would have been
  defensible and wrong: **re-deriving it is what surfaced E-7**, the pruned
  ERCOT provenance run, which changed no count and no gate. The rule the board
  already had — *trust no table, including this one* — needs the corollary that
  **a table whose headline numbers are stable can still be materially stale.**

**Carried, restated in one line each** (full text in v10–v14): run the gates,
never quote them (exit codes captured directly, not through a pipe) · quote no
cycle count without its base sha, in the dispatch and on the board · trust no
table, including the dispatch's — re-derive from committed bytes at the pin ·
a refresh is complete when the sessions exist, not when the prompts are
written · check the live roster before declaring a lane unlaunched · read a
content-addressed identity before inferring · **confirm
`frontend/data/hindcast/` is present before quoting any stamped/scored count**
(done this cycle: present, 16 entries, and `check_forecast_staleness.py`
reports *board inputs: all present*).

**While the program is parked, the refresh cycle is not the live instrument it
was.** A park-period refresh confirms (a) whether the owner has ruled on
anything in the queue — **four rulings from the PM sitting, ALL EXECUTED this
window**; (b) whether the keeper freeze has been called — **still deferred by
direction, but the evidence shifted: zero promotions this cycle**; and
(c) whether the golden tier's park has been lifted — unchanged, and the CI
proof stays deliberately unspent.

## RESTART CHECKLIST — for whoever un-parks the program

**Do these in order. Do not start at change (a).**

0. **🟢 `main` IS FULLY GREEN AT THE v15 PIN — re-run at `69ae4dc7`, not
   quoted: ALL FIVE CHECKS PASS.** `audit_keepers.py` **PASS 0/0** ·
   `check_registry_payload_parity.py` **exit 0** (56 runs / 93 dirs / 0
   tolerated) · `check_mechanism_matrix.py` **exit 0** ·
   `check_forecast_staleness.py` **exit 0, Δ = 3/10** (WARN-level; the 31/43
   undated-stamp WARN persists) · `check_bench_freshness.py` **0 STALE of 20**
   (six ungated engine-drift WARNs, now at 15 commits). Green for a second
   consecutive cycle. **Always re-run all five rather than reading this line**;
   at this repo's merge cadence the reading ages in hours — it aged twice
   inside this lane's own session.
0b. **🔴 THE GOLDEN PROVENANCE PROBLEM GOT WORSE WHILE THE TIER WAS PARKED.**
   Two independent breaks now sit on the ERCOT row: the manifest's `git_sha`
   **`af1ccb6` still does not resolve**, and the capture's `keeper_id`
   **`2026-08-15-ercot204-rule26-delete` was pruned from the registry**
   (`e51a8a7d`, #4356) under top-15 retention (E-7). Neither was caused by
   error; both are the cost of parking WS3 while the calibration program runs.
   **The per-file `content_hashes` are unaffected and remain the verification
   instrument.** Whoever re-captures decides, per ISO, *which tree and which
   run the golden is a golden OF* — and should record that provenance **inside**
   the manifest rather than by reference to a sidecar retention may reclaim.
1. **DECIDE THE GOLDEN TIER AND THE FREEZE TOGETHER** — the precondition, not a
   nicety. A freeze buys re-captured goldens; a parked golden tier means those
   captures cannot be certified byte-green, so a freeze alone leaves G2 leg 1
   blocked. Un-parking costs one `workflow_dispatch` (billed minutes — why it
   was parked). 🆕 **The "there has never been a cheap calibration window"
   argument is, for the first time, not true: this cycle promoted ZERO
   keepers** while running five calibration rounds. Treat that as an
   opportunity, not a trend — two lanes are live at the pin and either could
   promote.
2. **RESOLVE THE STAGE-0 MANIFEST'S PROVENANCE SHA BEFORE TRUSTING ANY
   CAPTURE.** `git_sha: af1ccb6` still does not resolve at the pin — shallow
   clone or 2026-08-16 rewrite orphan; the captures are dated inside the
   rewrite window. **The per-file `content_hashes` are unaffected — verify
   against those.**
3. **Re-verify every stage-0 golden against the then-current keepers** before
   resuming any change. Do not trust this board's staleness table — re-read the
   keeper shards and the manifest at that HEAD and re-derive it, mapping
   captured bundles back through the manifest's `keeper_id` fields. **At
   `69ae4dc7` the answer is unchanged in count: all five captures stale, PJM
   never taken, ERCOT needs TWO captures (forward + carve-out) — and the ERCOT
   capture's run is no longer registered.**
4. **Assume every re-capture is a real solve.** The gaps at this pin, all
   unchanged: **MISO eleven** promotions past capture, **NYISO ten**, **ERCOT
   six** (forward line, plus a second designated config with no golden at all),
   CAISO two, NEISO two. The **re-stamp-not-re-solve** shortcut was established
   for **neiso-97 only** — re-establish it before relying on it; re-derive the
   config diff first.
5. **Capture PJM FIRST.** No golden at all, a keeper unmoved for **seven**
   cycles, the only clean scorecard on the board (8/8, zero caveats).
   Simultaneously the largest coverage gap and the cheapest capture — untaken
   across seven consecutive boards, and **cheapest right now**, with PJM's lane
   quiet and the keeper table still.
6. **Do NOT re-do change (c).** It landed via #3964 and is byte-identical at
   HEAD. Verify the blob (`af34031c`) rather than re-porting it.
7. **Close the #4054 residual if you want belt-and-braces — but re-derive it,
   do not inherit it.** The NYISO keeper is still **TEN promotions** past the
   captured nyiso-140 config.
8. **Then, and only then, resume changes (a)–(e)** — and re-read the G2 leg
   list, because *merged byte-green* is what the gate wants, not captures.
9. **Confirm the golden tier is green IN CI before claiming any byte-green
   result** — which requires un-parking it (step 1). A tier that cannot
   provision `data/clean` cannot prove byte-identity of anything, and a local
   replay is not the gate.
10. **🔴 FIX THE PARITY GATE'S CLASSIFIER, NOT ITS SYMPTOM.**
    `KEEP_REQUIRED_UNMAPPED_BUNDLES` stands at **26 named entries** and the
    class-level carve-out the 2026-08-20 finding recommended (pre-registered
    recipes and in-flight controls legitimately precede any sidecar) **still
    does not exist** (B-8). ~10 lines, and it retires a recurring red for good.
    Explicitly **not** a pre-merge check, which would penalise correct
    pre-registration. **Until then, the gate's green is a maintenance state,
    not a property** — and with two lanes live at this pin, the next red is
    likelier than it has been in three cycles.
11. **🆕 RECONCILE RETENTION WITH THE GOLDEN MANIFEST.** E-7: top-15 registry
    retention and the WS3 manifest reference the same run ids and know nothing
    about each other, so a correct prune silently degraded a golden's
    provenance and **every gate stayed green**. Fix it on the manifest side
    (self-contained provenance), **not** by exempting golden runs from
    retention — that re-creates the dead-bundle class the parity gate already
    struggles with.
