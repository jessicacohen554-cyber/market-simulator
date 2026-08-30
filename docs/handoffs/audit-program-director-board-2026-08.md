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
> ### 🟢 NEW AT v14 — A NEW DIRECTOR TOOK THE DESK 2026-08-30, AND EVERY SITTING RULING IS EXECUTED OR HAS A LANE
>
> Four owner rulings from the 2026-08-30 director sitting, all with visible
> outcomes at the pin: **Card 2 — the ERCOT TWO-CONFIG KEEPER — EXECUTED**
> (#4313, the dispatch's own base sha); **O7 RULED** (the §5
> attribution-harness partial AUTHORIZED; keeper-moving restoration DECLINED;
> accept-as-limitation DECLINED — lane dispatched); **the bench re-stamp RULED
> AND ALREADY EXECUTED** (#4321 — the bench gate reads **0 STALE** at the pin);
> **the caiso-217 PRUNE RULED** (lane dispatched, outstanding at the pin).
> Plus a **scorer-only FF-2D re-score AUTHORIZED** at the FR-21 staleness
> threshold (Δ = 12 of 10 at the pin). See D-1…D-7.
>
> ### 🔴 AND: THE CALIBRATED SET NO LONGER EQUALS THE `complete` SET — THE FOUR-INSTRUMENT ALIGNMENT v13 REPORTED IS BROKEN
>
> Two consecutive owner-decided NYISO promotions (**nyiso-155** over a gate
> regression, then **nyiso-157 at this board's own base sha**, #4323) put a
> **NOT-YET** keeper on an ISO that holds a `complete` marker and a ratified
> frontier. The CALIBRATED set is **{PJM, NEISO}**; `complete` is
> **{NEISO, NYISO, PJM}**. Both promotions are owner acts, correctly executed
> and D-5(b)-re-verified — **recorded as state, not drift.** See D-3.
>
> ### 🔵 AND: ERCOT IS THE BOARD'S FIRST TWO-CONFIG KEEPER
>
> Forward keeper `2026-08-25-234-eastex-identity` (2024–2025, **CALIBRATED on
> its designated span**; its registered 3-year NOT-YET on {C3a-2023 −39.7 %,
> C3b-2023 0.730} **stays published at full magnitude**) plus the 2023
> carve-out `2026-08-25-236-swcap-clip-k33` (**CALIBRATED, zero caveats** — the
> ECRS-era regime config). A config carve under the owner's rule-16
> `[R-ALLYEARS]` waiver, never a year drop; the shard records the coverage
> invariant verbatim and **`audit_keepers.py` PASSES on the structure.** The
> ercot-234 rule-16 re-solve v13 reported as OWED has landed — its bundle
> exists and is registered. See D-2.

> **STATUS: PARKED AT G1** — live rollup maintained by the program-director
> session, updated on each owner "refresh". Canonical program definition:
> `docs/model-audit-release-plan-2026-08.md` (its §8 ledger is the durable event
> record; this board is the at-a-glance state). Completion figures are the
> director's estimate against each workstream's full DoD (A+B halves).

**Snapshot (v14):** **BASE SHA FOR EVERY FIGURE ON THIS BOARD: `0a5e896`**
(merge of #4323), derived live from `origin/main` on 2026-08-30 — which
**advanced FOUR TIMES while this lane was measuring** (`f6f2cd1` → `3d8ea01` →
`67f1557` → `4a9ef57` → `0a5e896`; the gap includes a ruled re-stamp executing
(#4321) and an owner-ruled NYISO promotion (#4323) — the base sha itself). The
dispatch's stated base **`f6f2cd1` (merge of #4313) is REACHABLE BUT 10 MERGED
PRs STALE.** Every count below states the window it was measured over. Nothing
is carried from the dispatch, from board v13, or from any table, unverified;
where the pin has moved past the dispatch, **both states are recorded.**

| window | span | commits | non-merge | merged PRs |
|---|---|--:|--:|---|
| **since v13 LANDED** (`b0ee254..0a5e896`) — what the board is stale by | 2026-08-25 → 2026-08-30 | **190** | **132** | **58** (#4266–#4323) |
| **since the dispatch's base** (`f6f2cd1..0a5e896`) — what moved after the prompt was written | 2026-08-30, same day | **24** | **14** | **10** (#4314–#4323) |

**Keeper motion across the board window, re-derived from the shard HISTORIES,
not from the dispatch's list:** **NINE promotion events across four ISOs, plus
the partition formalization** — ERCOT 231 → **`234-eastex-identity`** (the Z-A
rule-16 re-solve v13 recorded as owed, landed and promoted), then the 2023
config line `235-2023-discrete-k24` → **`236-swcap-clip-k33`** (superseded
next-day; the first ERCOT CALIBRATED determination), formalized as the
two-config partition (D-2); CAISO 200 → **`220-c1-crosswalk`**; NYISO 152 →
**`155-hydro-repair`** → **`157-par-attribution`**; MISO 177 →
`186-statusscope` → `187-nucavail` → **`188-rvsscope`** (three promotions the
dispatch's deltas block compresses to its endpoint). Two landed inside the
dispatch window itself — miso-188 (2026-08-30) and nyiso-157 (at this board's
own base sha). **Only PJM and NEISO are unmoved.**

**ZERO open PRs** (live `list_pull_requests` at the pin) and **ZERO branches
ahead of `main`** (`ls-remote`; each surviving branch tip verified inside
main's history, not inferred from the listing). The dispatch's lanes-in-flight
have all either merged (nyiso-eastern-seam #4318 + #4323, branch deleted;
bench-restamp #4321, branch deleted; ercot-239 #4320/#4322, branch survives at
main) or sit at main with nothing unmerged (miso-190); the O7-harness and
FF-2D re-score lanes dispatched at the sitting **show no branch yet.**

**Headline, one line: every sitting ruling landed or has a lane, nine keeper
promotions across four ISOs plus a partition landed in five days, the bench
gate went green by ruled re-stamp — and the audit workstreams did not move at
all.** Verified
rather than assumed: `git diff --name-status` over the full window returns
**empty** for `.github/workflows/` and `results/regression-goldens/`. The one
change from v13's version of that sentence: **this board and the plan DID
move** — the holdout-governance records lane landed the 2026-08-26 sitting's
cards on both files on 2026-08-30 (`7a40c55`/`3643318`/`583d3ad`), which is
that deviation working as designed, not drift.

## What moved — v14 CYCLE (`b0ee254..0a5e896`, "the sitting-execution cycle")

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
branch visible yet at the pin).

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

### D-7 · 🟠 FR-21 AT THRESHOLD — SCORER-ONLY FF-2D RE-SCORE AUTHORIZED (ZERO SOLVES)

At dispatch the forecast-board staleness reached its threshold: **Δ = 10 of
10** solve-affecting commits past the newest scored verdict evidence
(2026-08-25), with **31 of 40 verdict stamps carrying no scored-at date** —
freshness UNKNOWN regardless of the newest. **Owner ruling 2026-08-30: a
scorer-only FF-2D verdict re-score lane is AUTHORIZED — zero solves.**
Dispatched the same sitting (surface: `frontend/data/forecast/`; no branch
visible yet at the pin). **At the pin Δ has grown to 12** — the WARN now
names 12 solve-affecting commits past the evidence, and the re-score lane's
case is stronger than when it was authorized.

---

## What moved — v13 CYCLE (v13 record, RETAINED as history) (`a6886de..99c8cf5`, "the adjudication cycle")

Measured over the **since-v12-landed** window unless a change states otherwise.
Every figure re-derived at `99c8cf5`.

### C-1 · 🟢 THE HEADLINE — the entry-signal thread is ADJUDICATED: `entry_lookahead_reprice`, ERCOT `fc` **K → O**

**Four LP solves**, not one: an ERCOT disarm probe **and a same-tree ERCOT
control**, a CAISO dump-production run **and a same-tree CAISO control**
(`docs/FINDING-entry-signal-disarm-2026-08.md`). The verdict is recorded as what
it is — **NEITHER a promotion NOR a rejection.**

**The disarm hit L-1's storage prediction TO THE MEGAWATT, and that precision
is the point:** ERCOT storage entry goes from a one-shot 5.0 GW
spike (iron_air 3,000 + flow_battery 2,000, 2023 only) to **iron_air at exactly
3,000 MW in EVERY step 2022/2023/2024/2025**; the second storage slot flips
**flow_battery → compressed_air** exactly as L-1 §2.3 predicted; and **wind
enters economically for the first time** (1,092.2 MW in 2022).

**🔵 AND IT FAILED L-1's GAS PREDICTION — IN THE OPPOSITE DIRECTION — WHICH IS
THE INFORMATIVE HALF.** L-1 predicted entering-2024 gas margins turn *positive*
on duals. On the disarm run's **own** forecast-lane duals — priced against a
fleet the model has already over-built — **gas_ct falls from its 3,000 MW cap to
1,000 MW.** L-1 §1.1 had **declared its own bound in writing** (its dual arm used
the *backcast keeper's* duals as a stand-in, so its delta measured signal
construction **plus a fleet/run-identity residual** it could not size). This
solve **sizes that residual**: material for gas, immaterial for storage. **A
failed prediction measured something a confirmed one could not**, and it is only
legible as a measurement because the bound was stated in advance rather than
buried.

**Bands, at full magnitude and in both directions (rule 1 `[R-STRUCT]`):** four
of five addition metrics improve — storage |err| 8.691 → **4.309** GW, gas_ct
7.571 → **5.571** GW, solar 17.987 → **19.987** GW, wind 0.350 → **1.442** GW —
and **ALL FIVE STILL FAIL THEIR BANDS**; gas_cc is cap-bound at 9.000 in both
arms and retirements are 0.000 GW in both. **The cobweb SURVIVES and the
recovery overshoot WORSENS: terminal RM 25.19 → 40.24 %** (down-swing damped
−10.46 → −5.00 pp, rebound amplified +10.54 → **+14.32 pp**).

**The verdict's basis is which object is the real developer pro-forma, and
neither arm is:** the shipped reprice has the right *intent* (forward-looking)
and the wrong *object* (zone-flat by construction — `zonal_mean_range` and
`hourly_cross_zone_spread` measure **exactly 0.0** in both ISOs, ~90 % of its
dispersion being the ORDC adder); the duals fallback has the right *object* (the
locational nodal dual a generator is actually paid) and the wrong *expectation
model* (last year's realized duals = the textbook naive-expectations cobweb).
**The disarm trades one structural defect for another**, so it is **not `R`**
(rejecting it would bury a real finding) and **not `K`** (arming it is the
owner's promotion decision, stated as such in the charter).

**🟢 CAISO DIVERGES FROM ERCOT, AND THAT IS RULE 25 `[R-ISO-SCOPE]` WORKING —
not a contradiction to reconcile.** CAISO's own L-1, measured offline: against
iron-air's **\$12.69/MWh net** requirement the shipped MC-step object delivers
**\$0.00/MWh — 0.0 %** entering-2024 and \$0.49 — 3.9 % entering-2025, while the
model's own duals close **63–85 %** (\$8.00 — 63.1 %, \$10.76 — 84.8 %) **and
still fall short in both years.** In ERCOT the same replacement flipped iron-air
positive; in CAISO it does not. **So CAISO's 0-MW-vs-15,147-actual storage miss
is LARGER than the signal defect**, and its next rung is the **VALUE STACK**
(D-9's missing AS credit — the RA credit at \$77,611/MW-yr against a
\$138,859/MW-yr cost), **not a CAISO disarm.** No CAISO cell verdict moves.

**🟢 THE STOP-THE-LINE METHOD, RECORDED BECAUSE IT RESOLVED THE OTHER WAY.** The
CAISO dump run showed every fleet metric identical to the registered
`score.json` but a **CO2 difference of +68.4 / −49,190.1 / −44,077.4 t**. That is
the charter's stop-the-line signature and the lane **treated it as one — nothing
was pushed on the item until it resolved.** A **control arm** settled it: the
registered posture re-solved with **no flag at all** is **IDENTICAL to the
flag-on run across every field of `score.json`**, and differs from the
*committed* bundle by exactly the same three numbers. **The flag is inert; the
difference is source-tree drift** between the 2026-08-22 registered solve and
HEAD. **Without the control, the honest reading of the naive check would have
been "the flag is not output-only" — which is false.** The consequence worth
carrying: **the committed CAISO registered bundle's `score.json` no longer
reproduces at HEAD**, so any lane treating it as a reproduction baseline must
re-solve first. **ERCOT's does reproduce** (registered CO2 delta 0.0 t all three
scored years; all four `screen_signal_diag_*.npz` byte-identical), which is what
makes the CAISO drift diagnosable rather than ambient.

**🟠 NAMED AND DELIBERATELY NOT CHASED (rule 21 `[R-DOF]`).** The terminal-RM
overshoot invites an elasticity or a damping coefficient. **There is none in
this lane and there should be none** — it is held as an **open root-cause
issue**, owned by D-1's bang-bang volume rule. Recording the restraint matters
as much as recording the result: this is the rule working in the case where
closing the residual would have been easy and wrong.

**One structural cost that appears in no band:** a disarmed run emits **no
`screen_signal_diag_*.npz` at all** (the dump lives inside the reprice gate), so
**the L-5 offline-diagnosis route does not survive the disarm.** Any future
promotion must carry that relocation deliberately rather than discover it.

**Rule 26 duty (b) discharged in-session** — the ERCOT shard cell reads
`cell: "K", fc: "O"` with the full evidence string; `check_mechanism_matrix.py`
**exit 0** re-run at this pin.

### C-2 · 🔴 ERCOT — TWO CARDS SIGNED, A REAL DEFECT FOUND, AND THE REPAIR NOW HALF-LANDED

**(a) Card Y SIGNED (Y-C)**, in-session 2026-08-24 — formal closure of the ERCOT
2023 price object (`docs/DECISION-CARD-ercot233-2023-object-closure-2026-08-24.md`).

**(b) Card Z SIGNED (Z-A)**
(`docs/DECISION-CARD-ercot234-nelob-identity-repair-2026-08-24.md`, signature
recorded 2026-08-25). **The substance must not compress to "a crosswalk fix".**
ERCOT's own definitions deck (2020-02-24) identifies **`NE_LOB` as "North
Edinburg – Lobo" — a South Texas / Rio Grande Valley stability corridor**, still
grouped under *"Valley Area"* in the July-2024 ROS update. **The model read the
name as "Northeast lobe"** and, on that reading: carved a **Northeast zone out
of North expressly "to capture the NE_LOB GTC"**; set the Northeast→North static
export rating to NE_LOB's measured limit-at-bind (**1,300 MW**); overlaid
NE_LOB's measured hourly limits onto that link **in every keeper year**; and
**dismissed EASTEX — ERCOT's actual "flows out of the East Texas area" GTC, the
model boundary's true counterpart — as "intra-zone, unrepresentable."**

**So a KNOWN-WRONG MEASURED INPUT was armed in the designated ERCOT keeper**,
capping a ~8 GW NE lobe at the Valley's 1,245/1,260/1,549 MW p50 series,
binding-heavy in all three years, where the real EASTEX bound 828 → 191 → 3
intervals at ~2× the limit. **Rule 14 `[R-ACCURATE]` is exactly the rule that
refuses the rest-as-is option (Z-C)** — an accurate input is kept even when the
fit worsens, and the worse fit is treated as a discovered bug elsewhere. The
owner signed the **full identity repair including a rule-16 three-year
re-solve.**

**🔵 THE DEFECT CLASS IS THE REUSABLE LESSON: a measured input whose NAME was
mis-read as GEOGRAPHY.** Nothing about the pipeline was broken — the data was
real, the intake was clean, the citation existed. What failed is that **the
crosswalk's own citation never defines the identifier**, so a plausible
expansion of an abbreviation propagated into a zone carve, a static rating and
an hourly overlay. **That failure mode is not ERCOT-specific and no existing
gate detects it.**

**🔴 NEW AT THIS PIN, AND NOT IN THE DISPATCH — THE REPAIR IS HALF-LANDED.** The
dispatch describes this lane as *"MID-FLIGHT, do not disturb"*; it **merged as
#4260 before this lane started.** Re-derived at `99c8cf5`:

- **What LANDED:** the phase-0 boundary verdict (**(a)+(b) MET → Z-A**; EASTEX
  mean-limit-at-bind pooled 2023+2024 = **2,298.4 → 2,300 MW**, corroborated by
  ERCOT market notice #1557 placing the constraint *"around Tyler, Lufkin and
  Nacogdoches"* — all inside the model's Northeast carve); the **code repair**
  (`dc84600`: EASTEX replaces NE_LOB on Northeast→North, static **1,300 →
  2,300**, gloss sweep across `constants.py`, `iso_configs.py`,
  `zone_assignment.py` + tests); the P-6 gates probe; and a re-point of the
  official scorer's validation gate at the ercot-231 keeper (**stale since that
  promotion**).
- **What has NOT landed:** the **rule-16 three-year re-solve.**
  `results/calibration/ercot234_eastex_identity` **does not exist at HEAD**, no
  sidecar is registered, and the keeper is **not re-keyed** — it still reads
  `2026-08-24-231-tie-zone-measured`.

**The consequence, stated plainly because no gate reports it: HEAD's ERCOT
topology no longer matches the designated ERCOT keeper's solved topology.** This
is the **same class** as C-1's CAISO drift finding and now has an ERCOT
instance — **two of six ISOs whose committed keeper bundle no longer reproduces
at HEAD**, one by accident (CAISO, cause unbisected) and one by deliberate
repair (ERCOT). **Any lane using either as a reproduction baseline must re-solve
first.** This is a live state, not a defect to fix on this board.

### C-3 · 🟢 NYISO FRONTIER RATIFIED — v12 owner-queue item 7, SIGNED

Owner decision **2026-08-23**, in session with the program director: *"Ratify
NYISO."* Recorded in `keepers/NYISO.json` `frontier` (declared 2026-08-23),
ratifying `ASSESSMENT-nyiso154-frontier-2026-08-22.md` §3. The recording session
was itself a **records lane** — it re-adjudicated no merits, moved no cell,
changed no determination. **It unblocks the desk's own director session**, which
v12 recorded as idle-blocked on exactly this. **Frontier set is now
{PJM, NYISO, NEISO}** — again exactly the `complete` membership, and again
exactly the CALIBRATED set.

### C-4 · 🟢 MISO 181–185 CLOSED, INCLUDING A **FIFTH** RUNG THE DISPATCH DID NOT HAVE

Recorded so the **DO-NOT-REDO discipline** holds. **Keeper unchanged throughout**
(`2026-08-22-miso-177-rho-measured`); no LP spent in the 181–185 arc.

- **miso-181** — `miso_seam_coincident_envelope` **`R`**.
- **miso-182** — `miso_south_firm_export_block` **`G`**; the South-seam basis
  question routed **V-TRADE**, and it is a **real ≥0.93 GW defect, NOT
  bookkeeping.**
- **miso-183 / miso-184** — **V-DEFECT-COUPLING**: the scarce-tail failure is
  real **but is NOT the price basis**, and the repair licence was **refused**.
- **🆕 miso-185 (2026-08-25, landed after the dispatch was written)** — the
  §6b re-open ladder run to the ground: **V-NEG-ABSENT.** Twelve quarters of
  seller-scoped FERC EQR (**698 seller-quarter reports**, corpus committed) show
  every MISO-South jurisdictional seller selling to **MISO + affiliates ONLY**
  — no pool customer, no pool delivery-BA, largest cross-seam trace
  **\$1.9K/quarter**; the GFA inventory carries **zero** Entergy-legacy rows;
  and TVA's own 10-K disclosures put the real MISO→TVA leg on
  **reserved-transmission + market (SPOT) purchases — the rule-13-INADMISSIBLE
  form.** `miso_south_firm_export_block` **stays `G` with its re-open
  NARROWED**; the honest residual is a **~1.3 GW scarce-export model-class
  concession** going to the owner. **No mechanism cell minted** — no
  mechanism-in-kind was tested, because the conditional build's licence never
  fired.

**The pattern worth naming:** five consecutive MISO rungs, **zero LP spent**,
each one closing a named successor rather than leaving it open — and the last of
them closes a re-open by **proving the data does not exist**, which is a
stronger close than a refutation.

### C-5 · 🟢 CAISO 218 AND 219 — TWO DECISIVE NULLS, AND A RE-LOCATED HYPOTHESIS

**Nulls are results, and are recorded as such.** No LP, no solve, nothing armed,
nothing registered, no cell verdict moved in either.

- **caiso-218** — the Path-15/26 measured operating-limit phase-0 survey:
  **DECISIVE NULL at the cut grain.** CAISO **discontinued the internal-path
  limit as a market object on 2018-11-01**; element-grain limits are published
  only as DMM annual scalars; and the **bounding what-if proves NO static cut
  limit — measured or otherwise — can reproduce reality's split-hour year
  pattern.** That last clause is the valuable half: it forecloses the whole
  lever family, not just the unavailable data.
- **caiso-219** — the §F.3a gen-pocket export-limit survey: a **SECOND decisive
  null on the prerequisite** (CAISO publishes sub-zonal deliverability as an
  **accreditation headroom in a resource-weighted currency, never a flow
  rating**), **plus a RE-LOCATION of the hypothesis** — CAISO's own off-peak
  constraint record puts the belly-hour sub-zonal mass in PG&E Kern/Fresno at
  the **GATES–MIDWAY complex, on the ZP26 side**, with **Tehachapi (SP15)
  carrying ZERO off-peak constraints.** A null that hands the next lane a
  sharper address is worth more than a weak positive.

**Governance note carried from caiso-219's own authority line:** the owner, on
2026-08-24, **chose this lane over the caiso-217 replay.** That is why the
parity gate is red (see Gates).

### C-6 · 🔴 GATES — ONE GREEN CLEARED, ONE RED, AND THE RED IS AN ACCEPTED COST

All three **RUN at `99c8cf5`** in a sparse worktree at `origin/main`, never a
drifted checkout. Exit codes captured directly, not inferred from a pipe.

- **MATRIX — 🟢 GREEN (`exit 0`), and the v12-era WARN IS CLEARED.**
  `check_mechanism_matrix.py` reports integrity OK across the base file + **6
  ISO shards**; anchors checked (**191 field + 49 row + 154 path**, 0
  unresolvable beyond the ratchet); keeper stamps match every
  `keepers/<ISO>.json`; **and "§5.x prose headers match every
  keepers/<ISO>.json"** — the drift v12 flagged, **fixed by the ERCOT lane.**
  **Recorded explicitly so the next director does not re-report a cleared
  warning.**
- **STALENESS — 🟢 OK (`exit 0`).** **50 stamped / 18 scored**, **10 distinct
  config epochs**, board inputs **all present**, solve-affecting delta **2**
  (threshold 10). Per class: **hindcast 9/9 · seed 1/0 · verdicts 40/9**
  (verdicts = gate evidence). **Every one of these is HIGHER than the
  dispatch's expected 48/16, 9 epochs, delta 1, 8/8 + 1/0 + 39/8** — the board
  moved between prompt and launch, which is the whole reason figures are
  re-derived rather than quoted.
  **🔵 THE MEASUREMENT TRAP, RECORDED BECAUSE IT CAUGHT THE DIRECTOR LAST
  CYCLE: run this with `frontend/data/hindcast` PRESENT.** A sparse tree missing
  it reports a **lower** count and the script's own WARN says so. **A zero here
  is a MEASUREMENT failure, not an unstamped board.** Verified present in this
  lane's worktree before the number was taken.
  Two standing WARNs, unchanged in kind: fresher non-gate artifacts (hindcast
  sidecars newer than the verdicts evidence — inputs to a future verdict, never
  a substitute for one), and **31 of 40 verdict stamps record no scored-at
  date**, so their freshness is **UNKNOWN** regardless of the newest.
- **PARITY — 🔴 RED (`exit 1`) on exactly ONE dir**,
  `results/calibration/caiso217_crosswalk` — the documented caiso-217
  registration debt (mid-solve checkpoint, 2023 hourly sidecars only, session
  ended before registering). **NEW CONTEXT, AND IT CHANGES HOW THE RED READS:
  the caiso-219 record shows the owner CHOSE the §F.3a strandedness lane OVER
  the caiso-217 replay on 2026-08-24.** So this is a **DEPRIORITIZED decision,
  not an unserved one, and the red gate is its accepted cost.** **NEVER
  recommend pruning it.**
  Scale at this pin: **54 registered sidecars · 83 bundle dirs ·
  `KEEP_REQUIRED_UNMAPPED_BUNDLES` at 26 entries** (v12: 53 / 76 / 24). **The
  allowlist grew again — 24 → 26 — and the class-level carve-out the 2026-08-20
  finding recommended STILL does not exist** (v12's B-6, unrepaired).

### C-7 · 🅿️ PROGRAM POSTURE — UNCHANGED, AND THAT IS NOT DRIFT

**Parked at G1.** WS3/PERF-B is **paused by owner decision** pending a
calibration freeze the owner has **DEFERRED in order to keep calibration running
on all six ISOs**. **DOCS-B (G2), SITE-A (G3) and AUDIT-B (G3) are waiting BY
DESIGN and are NOT late.** The **golden tier remains PARKED** (owner ruling
2026-08-22). The FFR desk's **Q.2 supersession battery does not commission**
(AS.6). WS1 **~91 %** (O4/O6/O7 open) · WS2 **COMPLETE** · WS4 **~60 %** · WS5
**Job 1 complete** · WS6 **COMPLETE**.

**Verified rather than assumed, over the full `a6886de..99c8cf5` window (141
commits):** `git diff --name-status` returns **empty** for
`.github/workflows/`, for `results/regression-goldens/`, and for **this board
and the plan**. **WS1–WS6 are byte-unmoved**, so the percentages are unchanged
by construction — there was nothing to re-estimate.

---

## Keeper table (read from `frontend/data/backcast/keepers/<ISO>.json` and `status/<ISO>.js` at `0a5e896`)

Determinations and grade summaries parsed live from the status shards. **C3a(RT)
is the load-weighted mean-LMP error against RT actuals, per year 2023 / 2024 /
2025** — printed for every ISO because it is the criterion every NOT-YET fail
set contains, and printing it only for the failures hides how narrow the
margins are. ERCOT's row is the board's first TWO-CONFIG entry (D-2): the
grade column shows forward-span / carve-out / registered-3-year reads.

| ISO | Designated keeper | Determination | Grade (scored/target/fails/ledgered) | C3a(RT) 2023 / 2024 / 2025 |
|-----|-------------------|---------------|---|---|
| ERCOT | **`2026-08-25-234-eastex-identity`** (FORWARD, 2024–2025) **+ `2026-08-25-236-swcap-clip-k33`** (2023 carve-out) ⬅ **TWO-CONFIG since #4313** | forward **`CALIBRATED` on span** · carve-out **`CALIBRATED`** · registered 3-yr `NOT-YET` | 8 / 7 / 0 / 1 · 8 / **8** / 0 / **0** · (8 / 5 / **2** / 1) | **−39.7 % F** (the carve-out's year) / −0.2 % / −7.9 % |
| CAISO | **`2026-08-26-caiso-220-c1-crosswalk`** ⬅ **MOVED** (data-only crosswalk delta) | `NOT-YET` | 8 / 6 / **1** / 1 | +4.0 % / **+12.5 % F** / **+15.5 % F** |
| PJM | `2026-08-15-pjm-162-inputclock` | **`CALIBRATED`** | 8 / **8** / 0 / **0** | +6.2 % / −0.8 % / −7.7 % |
| NYISO | **`2026-08-30-nyiso-157-par-attribution`** ⬅ **MOVED TWICE** (155 → 157, both owner-decided) | `NOT-YET` | 8 / 5 / **3** / 0 | +1.0 % / −2.0 % / **−12.0 % F** |
| NEISO | `2026-08-17-neiso-99-joint-p1` | **`CALIBRATED`** | 8 / 7 / 0 / 1 | +3.1 % / +5.7 % / +1.7 % |
| MISO | **`2026-08-30-miso-188-rvsscope`** ⬅ **MOVED** | `NOT-YET` | 8 / 6 / **1** / 1 | +3.5 % / −4.3 % / **−12.3 % F** |

| ISO | v14 cycle (`b0ee254..0a5e896`) |
|-----|-------------------------------|
| **ERCOT** | **🔵 THE Z-A RE-SOLVE LANDED AND PROMOTED** (231 → 234-eastex-identity, retiring v13's "half-landed" C-2 state); the 2023 config line ran 235-2023-discrete-k24 → **236-swcap-clip-k33** (next-day supersession; **the first ERCOT CALIBRATED determination**, SWCAP clip + k_peak re-selected 24→33); **then the two-config partition was declared and EXECUTED** (D-2, #4313): 234 CALIBRATED on its 2024–2025 span, 236 CALIBRATED zero-caveats on 2023. The G-SPUR gate card **SIGNED Option A** (v13 queue 7 retired). O7 ruled: attribution harness authorized, restoration declined (D-4). ercot-239 zero-solve precommits merged (#4320/#4322) |
| **CAISO** | **🔵 PROMOTED** → 220-c1-crosswalk on **direct owner instruction** — the caiso-216 funded crosswalk intake executed as a **data-only** delta; NOT-YET stands honest (C3a-2024/2025 the sole fails). caiso-221 killed the south-belly surplus-pricing object **with measurement** (#4316). The caiso-217 checkpoint's **prune is RULED** (D-6), outstanding at the pin |
| **PJM** | **UNMOVED and untouched. SIXTH consecutive cycle.** Still the only 8/8 zero-caveat scorecard, still no stage-0 golden — the largest coverage gap and the cheapest capture, for a sixth board running |
| **NYISO** | **🔴 PROMOTED TWICE, both by owner decision:** 155-hydro-repair (over a C3a-2025 gate regression; the truncated-vintage repair restored after its **silent de-arm** at nyiso-108) then **157-par-attribution at this board's own base sha** (#4323; Leg-1 A/B registered #4318, iroquois companion **REJECTED on its own W-gates**). `complete` re-keyed + D-5(b) re-verified both times, **without a solve**. The `frontier` block **still cites superseded nyiso-152** — queue item 1 |
| **NEISO** | **UNMOVED and untouched.** Its entire residual remains the **`final` grant itself** — now explicitly **DATA-BLOCKED** on the 2025 EIA-923 FINAL vintage (queue item 3) |
| **MISO** | **🔵 PROMOTED THREE TIMES** → 186-statusscope (owner posture directive) → 187-nucavail (owner in-session directive) → **188-rvsscope** (registered + promoted 2026-08-30), NOT-YET on the **lone load-bearing FAIL C3a-2025 −12.3 %**. En route: miso-189 phase-0 refuted the Illinois scarce delivered-gas candidate zero-solve. miso-190 lane dispatched (PREREG + gates instrument committed before the mechanism exists); its branch sits at main with nothing unmerged at the pin |

**Markers at `0a5e896`, re-read live this cycle:** `complete` =
**{NEISO, NYISO, PJM}** · **`final` = EMPTY (`_note` only)** ·
**`holdout-freeze.json` `active: true`, TIER-SCOPED to `locked_test` alone**
(the 2026-08-26 card-6 scope; validation years are governed by the `complete`
marker + `--holdout-authorized`) · `withdrawn` = {CAISO, NYISO}. All three
`complete` entries are **re-keyed to their live keepers** (rule 22 D-5(b)) —
NYISO's twice this window, each re-verified from committed artifacts without a
solve — and **`audit_keepers.py` returns PASS: 0 failures, 0 warnings** at the
pin, run not quoted. Rubric **v3.5**.

**NO ISO HAS EVER SPENT A LOCKED-TEST YEAR** — re-verified at the pin, not
restated. Across all **58** registered sidecars the solve-year histogram is
**{2022: 2, 2023: 56, 2024: 54, 2025: 54}**; the only out-of-training
registrations remain the two authorized 2022 validation touchpoints. **No
2019, no H1-2026, for any ISO** (`[R-HOLDOUT]`). NEISO's one-shot stays
**NEVER GRANTED, not spent** (D-23). This line is re-verified and republished
every cycle because WS5 Job 1 found the public site asserting its exact
opposite for two weeks.

**Determinations: PJM, NEISO `CALIBRATED` · ERCOT (registered 3-yr), CAISO,
NYISO, MISO `NOT-YET` — with ERCOT's two designated configs each CALIBRATED
on their own spans.** The alignment v13 celebrated is **broken in one leg**:
CALIBRATED = {PJM, NEISO} ≠ `complete` = {NEISO, NYISO, PJM} = frontier =
forecast gate-(a) passers. **C3a appears in every NOT-YET fail set, and for
CAISO and MISO it is the ONLY failing criterion**; NYISO adds C3b/C3c fails
(8/5/3/0) and ERCOT's registered read adds C3b-2023 — both 2023-legs now
carved to the ECRS-era config on the ERCOT side.

## Workstream rollup

**WS1–WS6 are byte-unmoved across the v14 cycle too.** Verified rather than
assumed: over the full `b0ee254..0a5e896` window (**190 commits**),
`git diff --name-status` returns **empty** for `.github/workflows/` and for
`results/regression-goldens/`. This board and the plan **did** move — the
holdout-governance records lane landing the 2026-08-26 cards (see Snapshot) —
which is records flow, not workstream motion. Percentages are unchanged by
construction; **the table below advances only the cycle counts and the gate
cells.**

| WS | State | Completion | Blockers / next |
|----|-------|------------|-----------------|
| WS1 `AUDIT` | AUDIT-A **completed** (#3991). Rows **O8, O5, O4 CLOSED/RESOLVED**; **O7 now RULED** (D-4: attribution harness authorized, restoration declined — the accept/restore fork the row was open on is decided; the harness lane executes it) | **In progress ~93 %** | **AUDIT-B gated at G3 — waiting by design.** Row **O6** is standing policy (locked-test scheduling, recorded 2026-08-26); O7's harness lane is dispatched |
| WS2 `DEBUG` | **COMPLETED** — DEBUG-A ✓, DEBUG-B ✓, pjm-162 promoted, landing-verify green on merged main | **Completed** | none; no DEBUG-C continuation chartered |
| WS3 `PERF` | PERF-A ✓. **PERF-B PAUSED BY OWNER.** Stage-0: **5 of 6 ISOs captured**, **PJM never captured**. Changes (c)/(d)/(e) merged, (a)/(b) unstarted. `results/regression-goldens/` byte-unmoved again this window | **Paused ~74 %** | **Paused, not blocked — and blocked TWICE at G2.** **0 of 6 goldens match their keeper for a FIFTH consecutive cycle** — every gap held or widened (see Stage-0), and ERCOT now needs **two** captures (forward + carve-out) for full coverage. With the tier parked, byte-green cannot be *claimed* even if captures were current |
| WS4 `DOCS` | DOCS-A **completed** (#3999 + #4005); DOCS-B held | **In progress ~60 %** | **DOCS-B gated at G2 — waiting by design** |
| WS5 `SITE` | **Job 1 (site factual repair, pre-G3) COMPLETE ACROSS BOTH PASSES** (#4120/#4121, #4187/#4191). Job 2 = **SITE-A**, not started | **Job 1 COMPLETED · Job 2 not started** | **SITE-A gated at G3 — waiting by design.** Deferral list unchanged |
| WS6 `BLOAT` | Prunes B-1..B-8 merged; **BLOAT-2 CLOSED**; **BLOAT-3 ADJUDICATED and EXECUTED** (BLOAT-S2, −444.5 MiB at tip). The chartered work stays completed | **Completed (charter) · gate 🟠 RED with a RULED disposition** | **🔴 RED at this pin** (`exit 1`) on exactly one dir, `caiso217_crosswalk` — but the open decision v13 carried is **CLOSED: the owner ruled PRUNE** (D-6), and the red clears when the dispatched lane executes `dashboard_add_run.prune_iso`. The class-level allowlist carve-out (B-8) **still does not exist** — the structural fix outlives this instance |
| — `BENCH FRESHNESS` | `check_bench_freshness.py` / audit S1 lineage | **🟢 GREEN at this pin — 0 STALE of 20 parts** | **The ruled re-stamp EXECUTED (#4321)**: 8 pre-stamp NEISO/PJM parts re-stamped, content bytes untouched, NOT a regeneration, CI wiring explicitly DECLINED (D-5). Six engine-drift WARNs remain (ERCOT @ 13 commits, NYISO @ 16, 2023–2025 each) — not gated; regenerate before trusting a *marginal* C1 verdict |
| — `GOLDEN-TIER-FIX` | **COMPLETED and independently verified** (#4014); first cron RED, diagnosed + fixed same-day (#4071), verified by full local four-step replay | **Completed · tier PARKED** | **🅿️ PARKED BY OWNER RULING 2026-08-22, unchanged.** CI proof **deliberately unspent**. Consequence: byte-green cannot be CLAIMED for G2 while the tier is paused |
| — `MATRIX GUARD` | rule 26 `[R-MECH-MATRIX]` CI enforcement | **🟢 GREEN at this pin** | `check_mechanism_matrix.py` **exit 0**, run not quoted: integrity OK across the base file + **6 ISO shards**; anchors **192 field + 49 row + 151 path**, 0 unresolvable beyond the ratchet; **keeper stamps AND §5.x prose headers match every `keepers/<ISO>.json`** — holding across four promotions, a partition declaration and the nyiso-157 re-stamp this window |

## Stage-0 golden staleness (RECOMPUTED at `0a5e896` — never read from a table)

Re-derived at HEAD from `frontend/data/backcast/keepers/<ISO>.json` and
`results/regression-goldens/perfb-stage0/manifest.json` (`git_sha` **`af1ccb6`**,
still **not a resolvable object** at this pin, `git_dirty: false`,
byte-unmoved again — `git diff` over `results/regression-goldens/` returns
empty across all 190 commits). Each captured bundle mapped back to its keeper
through the manifest's own `keeper_id` field, not by name.

**🔴 THE CONSEQUENCE, STATED AS EVERY BOARD SINCE v11 HAS: BYTE-GREEN CANNOT
BE CLAIMED, so G2 leg 1 has TWO parked dependencies — WS3/PERF-B *and* the
golden tier — not one.**

| ISO | Golden captured against | Designated keeper at `0a5e896` | Verdict |
|-----|-------------------------|--------------------------------|---------|
| ERCOT | `2026-08-15-ercot204-rule26-delete` | `2026-08-25-234-eastex-identity` **+ 236 carve-out** | **🔴 STALE — SIX promotions past capture** (v13: five), **and the partition means full ERCOT coverage now needs TWO captures** — the carve-out config has no golden even in principle yet |
| NEISO | `2026-08-14-neiso-93-envelope` | `2026-08-17-neiso-99-joint-p1` | **STALE — two promotions past capture** (unchanged). The re-stamp-not-re-solve shortcut was established for **neiso-97 only**; re-establish before relying on it |
| CAISO | `2026-08-16-caiso-197-w2-r5` | `2026-08-26-caiso-220-c1-crosswalk` | **🔴 STALE — TWO promotions past capture** (v13: one; the caiso-220 promotion widened it). No longer the narrowest gap |
| MISO | `2026-08-16-miso-160-wefor-shape` | `2026-08-30-miso-188-rvsscope` | **🔴 STALE — ELEVEN promotions past capture** (v13: eight; 177 → 186 → 187 → 188 adds THREE). **The worst gap on the board** |
| NYISO | `2026-08-16-nyiso-140-layup-exclusion` | `2026-08-30-nyiso-157-par-attribution` | **🔴 STALE — TEN promotions past capture** (v13: eight; 152 → 155 → 157 adds two) |
| PJM | — | `2026-08-15-pjm-162-inputclock` | **NO GOLDEN — never captured**, and the keeper has now been stable for **SIX cycles** |

**Count: 5 stale / 0 current / 1 no-golden — 0 of 6 effective coverage for a
FIFTH consecutive cycle.** Every gap held or widened this window; four of the
five held ISOs widened (ERCOT, CAISO, NYISO, MISO — the four that promoted).

- **PJM remains the cheapest capture and the largest gap, for the SIXTH
  consecutive board:** no golden at all, a keeper unmoved for six cycles, the
  only clean scorecard (8/8, zero caveats). Six boards is a decision nobody
  made, restated verbatim from v13 because it is still true.
- **🔵 v13's "which tree is the golden OF" question is SHARPENED, not
  retired, by the re-solves.** The two bundles that did not reproduce at HEAD
  are no longer the designated keepers (D-3) — but every *golden* is still
  captured against a tree that no longer matches HEAD, and the manifest's
  provenance sha still does not resolve. Whoever un-parks WS3 re-captures
  against live keepers on the current tree and verifies via the per-file
  `content_hashes`, which remain valid either way.
- **🆕 The partition adds a capture-coverage concept the manifest does not
  have:** one ISO, two designated configs. A re-capture pass that takes one
  ERCOT golden is no longer full ERCOT coverage.

## Gates

- **G0** adopted ✓ (2026-08-13) · **G1** DECLARED ✓ (2026-08-16, #4006).
- **G2 — UNREACHABLE, still behind TWO owner parks.** Leg 1 is *PERF-B merged
  byte-green*; PERF-B is paused by owner decision **and** the golden tier that
  would certify byte-green is parked by owner ruling. The legs:
  1. **PERF-B merged byte-green** — **doubly blocked, and wider**: 5 of 6
     captured and **all 5 stale for a FIFTH cycle** (four gaps widened this
     window; ERCOT now needs TWO captures — see Stage-0), (c)/(d)/(e) merged,
     (a)/(b) unstarted, the golden tier parked so byte-green cannot be
     claimed, and the manifest's `git_sha` `af1ccb6` still unresolvable.
  2. **One completed fast-tier-green `ci.yml` run** — **🟠 OBTAINABLE ONCE THE
     RULED PRUNE LANDS.** The matrix guard is green at the pin (exit 0). The
     parity gate is red on exactly `caiso217_crosswalk` — but v13's "this leg
     now needs a decision" is **ANSWERED: the owner ruled PRUNE** (D-6). When
     the dispatched lane executes it, this leg goes decision-free again;
     re-run the gates rather than trusting this line.
  3. **A keeper freeze** — **owner call, DEFERRED BY OWNER DIRECTION rather
     than unanswered, and the deferral is visibly active policy:** NINE
     promotion events and a partition landed in this five-day window alone
     (ERCOT 234/235/236, CAISO 220, NYISO 155→157, MISO 186→187→188). **Do
     not read any future quiet week as a freeze arriving on its own.**
  4. **Branch-protection flip** — owner action, memo ready.

  On declaration the PM notifies the FFR desk (Q.2 battery).
- **G3** — unchanged: after G2, **DOCS-B** + the **BLOAT leg**. BLOAT's
  charter is satisfied (#4031 + #4047); its parity gate is **red at the pin
  with a RULED disposition** (prune, D-6) — read it as
  *satisfied-in-charter, gate-red-in-flight*, clearing on execution rather
  than awaiting a decision. The golden-tier proof leg is satisfied by #4014 +
  the green dispatch **as evidence**, though the tier itself remains parked.
- **G4** — unchanged: SITE-A + AUDIT-B. **WS5 Job 1 is not a G4 leg.**

## Watch

- **🅿️ GOLDEN TIER — PARKED BY OWNER RULING 2026-08-22, unchanged for three
  cycles.** The #4071 fix is merged and locally replayed green; the CI proof
  is **deliberately unspent**. Record it as a park, not a blocker — and record
  the consequence: **every byte-green claim remains unprovable**, and G2 leg 1
  is doubly parked.
- **🟢 NEW — THE "NEVER PRUNE caiso217" STANDING NOTE IS RETIRED BY OWNER
  ACT.** v13 carried it as protection against a lane silencing a gate by
  destroying a real solve's only artifact. The owner has now ruled the prune
  (D-6) — the protection did its job (nothing was pruned by inference), and
  the disposition is a decision, not a gate-silencing. The **standing hazard
  underneath it stays on watch**: the parity gate still reports a LIVE lane's
  pre-registered control/recipe dirs as "dead solve output"; before reporting
  a future parity red, check whether the named dirs belong to a running lane
  — **never recommend pruning a dir a live lane owns.** And the class-level
  allowlist carve-out (B-8) **still does not exist**; the allowlist stands at
  26 named entries.
- **🟢 NEW — THE BENCH-FRESHNESS GATE WENT GREEN BY RULED RE-STAMP, AND THE
  RECORD SHOWS WHY THAT WAS LEGITIMATE.** The 8 stale parts were adjudicated
  **UNLABELLED, not wrong** before any ruling
  (`docs/FINDING-bench-fingerprint-adjudication-2026-08.md`); the re-stamp
  (#4321) touched stamps, not content bytes, and CI wiring was **explicitly
  declined** — so the green is a labelling repair, not a regeneration and not
  a new gate. Six engine-drift WARNs remain (ERCOT @ 13, NYISO @ 16 commits)
  — regenerate before trusting a *marginal* C1 verdict.
- **🟠 FORECAST-BOARD STALENESS IS PAST THRESHOLD AND STILL GROWING — Δ = 12
  of 10 at the pin** (10 at dispatch), newest scored verdict evidence
  2026-08-25, **31 of 40 verdict stamps undated** (freshness UNKNOWN), 11
  config epochs on the board. The authorized scorer-only FF-2D re-score lane
  (D-7) is the remedy in flight; until it lands, treat the forecast board's
  verdicts as describing older code.
- **🔴 CARRIED — THE STAGE-0 MANIFEST'S PROVENANCE SHA DOES NOT RESOLVE.**
  `af1ccb6` is still not a valid object at this pin. The per-file
  `content_hashes` remain the verification instrument. Resolve which of
  shallow-clone-vs-rewrite-orphan it is before any re-capture is trusted.
- **🟠 CARRIED, AND THIS CYCLE'S LIVE INSTANCE IS THE QUEUE'S TOP ITEM —
  PUBLISHED STATE DRIFTING FROM THE ARTIFACTS UNDERNEATH IT.** The NYISO
  `frontier` block still cites superseded **nyiso-152**, now **two keepers
  behind** after 155 → 157 (queue item 1, HELD by owner). Same class as the
  matrix-stamp and gate-board instances v13 catalogued: **evidence PROSE is
  not gate-checked anywhere** — the matrix guard checks `keeper:` stamps and
  §5.x headers and passes while citation text beside them goes stale. Still
  worth an explicit ruling on whether any gate should read evidence text.
- **🟠 CARRIED — the cross-ISO scorer-change precedent** (nyiso-143 D-4 rider
  + the shared-benchmark determination flip): one lane's act re-grading
  another lane's committed record, the shape rule 25 `[R-ISO-SCOPE]` exists
  to prevent. Unmoved; no ruling this window.
- **🟠 CARRIED — #4054 / nyiso-140 null-treatment question**, never
  adjudicated — and further out of reach again: the NYISO keeper is now
  **TEN promotions** past the captured nyiso-140 config.
- **DURABLE LESSON (unchanged; the park makes it sharper):**
  `golden-data-tier.yml` is the ONLY workflow that runs
  `scripts/regenerate_clean.py`, so any curation-time defect under
  `scripts/data/curate_*.py` has NO pre-merge signal while the tier is
  parked. **Treat curate-script changes as unguarded.**
- **🟢 DURABLE LESSON, carried from v13 and earned again this cycle — a
  negative result with a bitwise proof beats a positive one without.** This
  window's instances: the nyiso-157 iroquois companion **REJECTED on its own
  pre-registered W-gates**, and caiso-221 killing the south-belly
  surplus-pricing object **with measurement** (#4316) — both closes that
  hand the next lane a sharper address at zero keeper risk.

## Forecast board — gate (a) re-derived at `0a5e896`: verdicts unchanged, FOUR seed stamps stale again, and the re-score lane is authorized

**Re-derived, not carried.** Every `gate.a_keeper_marker.detail` in the
committed seed `frontend/data/forecast/program-status.json` was compared
field-by-field against the live `keepers/<ISO>.json`:

| ISO | Seed names | Live keeper | Gate (a) |
|---|---|---|---|
| ERCOT | `2026-08-24-231-tie-zone-measured` | `234-eastex-identity` (+ 236) | **fail — unchanged** (no `complete` marker), stamp **STALE** |
| PJM | `pjm-162-inputclock` | same | **pass — current** |
| CAISO | `caiso-200-h1-memberpanel` | `caiso-220-c1-crosswalk` | **fail — unchanged**, stamp **STALE** |
| NYISO | `nyiso-155-hydro-repair` | `nyiso-157-par-attribution` | **pass — unchanged**, stamp **STALE** |
| NEISO | `neiso-99-joint-p1` | same | **pass — current** |
| MISO | `miso-177-rho-measured` | `miso-188-rvsscope` | **fail — unchanged**, stamp **STALE** |

**No gate opened, no gate closed, no ISO changed tier** — gate (a)'s test is
charter §2.1b(2)(a), *a designated full-span keeper AND an entry in the
`complete` block*, so every promotion above lands in the same class. **Gate
(a) passers are still {PJM, NYISO, NEISO} — still exactly the `complete`
set.** Said plainly because the alignment break (D-3) makes it easy to
misread: **NYISO passes gate (a) with a NOT-YET keeper** — the gate tests
keeper + marker, not determination. Gates **(b) and (c) remain UNSCORED.**

**The seed-staleness class v12 diagnosed and the capx-D1 refresh re-stamped
has recurred within five days — four of six stamps are one-or-more promotions
stale in id.** That is the recurring cost of promotion velocity, and the
remedy in flight is D-7: the **authorized scorer-only FF-2D re-score (zero
solves)**, whose `--reindex` pass bakes refreshed verdicts and provenance.
FR-21 staleness stands at **Δ = 12 of 10** with **31/40 verdict stamps
undated** — the WARN text itself says the board's verdicts may no longer
describe this code. **No forecast run was solved or re-scored by this lane**;
per rule 15 `[R-DASHBOARD]` the forecast namespace is registered through
`scripts/register_forecast_run.py` alone, and the backcast CI gates stay
blind to it.

## Owner queue at cycle end

Re-served and re-verified at **`0a5e896`**. **The 2026-08-30 sitting retired
FOUR items by ruling** (Card 2 two-config keeper — executed; O7 — harness
authorized, restoration and accept-as-limitation declined; bench re-stamp —
ruled and already executed; caiso-217 — prune ruled), and the ercot-238
session's same-batch signatures retired v13's time-critical item 7 (**G-SPUR
card SIGNED, Option A**). What remains:

1. **🟠 HELD BY OWNER — the NYISO frontier-block citation of superseded
   nyiso-152.** The `frontier` block in `keepers/NYISO.json` still cites
   nyiso-152/nyiso-154 as its basis while the designated keeper has moved
   152 → 155 → **157**, so the citation is now **two keepers behind** — the
   substance is live and sharper than at dispatch. Held deliberately: the
   owner's NYISO session was live at dispatch and has since merged #4318 +
   #4323 (Leg-1 A/B, companion REJECTED, nyiso-157 promoted); serve the
   repair once that lane's arc settles. A one-field records edit when taken.
2. **🔴 CALIBRATION FREEZE / WS3 RESTART — THE G2 GATE — DEFERRED BY OWNER
   DIRECTION, so G2 stays parked BY CHOICE, NOT BY DRIFT.** The board is
   executing an answered question, not waiting on an unanswered one. New
   datum for whenever the direction changes: **nine promotion events and a
   partition landed in five days** — the deferral is buying real calibration
   motion, and the standing recommendation (a scoped, time-boxed freeze
   decided TOGETHER with the golden tier's disposition) remains on the table
   with the af1ccb6 verification step attached.
3. **🟠 NEISO `final` GRANT — DATA-BLOCKED.** The 2025 EIA-923 FINAL vintage
   has **still not landed**; until it does the grant question is not
   servable on the merits. Standing and re-verified at the pin: **no ISO has
   ever spent a locked-test year**, NEISO's one-shot is **NEVER GRANTED, not
   spent** (D-23), and the freeze is tier-scoped to the locked test for
   every ISO. Data intake needs no authorization (rule 22) — the block
   lifts itself when the vintage publishes.
4. **⚪ DORMANT — the ERCOT rule-16 waiver qualifier.** Bounded by the Card-2
   implementation (the coverage invariant + both configs' records published
   at full magnitude); **re-fires only if the carve-out structure changes.**
   Not servable while dormant; recorded so it is not lost.
5. **🟠 CARRIED — rule on the cross-ISO scorer-change precedent** (nyiso-143
   D-4 rider + the shared-benchmark determination flip). No ruling this
   window; both remain one lane's act re-grading another's committed record.
6. **🟠 CARRIED — the T1-H capacity-entry defect (two defects, not one)
   still has no charter and no home.** The storage-entry/backstop mechanism
   and the separate wind leg, per A-7 and v13 item 11. No motion recorded
   this window.
7. **🟠 CARRIED — the caiso NOT-YET determination.** The crosswalk-intake
   half of the caiso-216 packet is now **EXECUTED as the caiso-220 keeper**
   (data-only, owner-instructed) and C3a-2024/2025 still fail at
   +12.5 %/+15.5 % — owner ruling 5 stands: **C3a must genuinely pass;
   NOT-YET is the honest fallback.** The next CAISO rung per caiso-219/221
   remains the GATES–MIDWAY relocation and the value-stack thread.
8. **🟠 CARRIED NOTE — the nyiso-148 2025 dear-gas level card**: no
   signature or decline recorded for it in any window since; its same-day
   UPDATE block should be read before its numbers (the keeper it names is
   now several promotions superseded).
9. **🟢 RETIRED THIS CYCLE (v14) — do not re-serve:**
   - ~~**Card 2 / two-config keeper**~~ — **EXECUTED** (#4313; D-2).
   - ~~**O7 P0 bit-identity forfeiture**~~ — **RULED**: §5 attribution
     harness AUTHORIZED; keeper-moving restoration DECLINED;
     accept-as-limitation DECLINED (D-4). The harness lane executes.
   - ~~**bench fingerprint staleness**~~ — **RULED AND EXECUTED**: re-stamp
     of the 8, content untouched, no CI wiring (#4321; D-5).
   - ~~**caiso-217 registration debt / v13 item 12**~~ — **RULED: PRUNE**
     (D-6). Execution is lane work, not an owner decision; the red parity
     gate clears when it lands.
   - ~~**the ercot-225 G-SPUR band-top gate card / v13 item 7**~~ —
     **SIGNED, Option A**, by the ercot-238 session (D-2), before any
     post-repair keeper was graded lidless.
   - *(Already retired by the 2026-08-26 records pass and listed here once
     for continuity: validation-freeze lift (card 6, executed), O6
     locked-test scheduling (card 7, standing policy), decision-1 ack
     (card 10), the holdout-freeze prose conflict (corrected).)*

## Session roster

> **🟠 v14 STATES ITS OWN LIMIT, as v13 did.** This records lane is **not**
> the director desk and holds no session-listing authority, so it did **not**
> run `list_sessions`. Lane state below is derived from **git** (`ls-remote`
> branch tips, each surviving tip verified inside main's history) plus one
> **live `list_pull_requests`** call at the pin. No row is carried from v13
> or from the dispatch unverified.

### Lane state at `0a5e896`, derived from remote branch tips + live PR list

**ZERO branches are ahead of `main`, and ZERO pull requests are open** (the PR
reading is live, not inferred). Main advanced four times while this lane
measured, and three of the dispatch's five in-flight lanes finished inside
that window:

| Lane (dispatch name) | Branch | State at the pin |
|---|---|---|
| **Records v14 (this lane)** | `claude/director-records-v14-ledger-lhywlm` | **🟢 WORKING** — the §8 ledger entry pushed and blob-verified; this board is its second file |
| **MISO backcast calibration (miso-190)** | `claude/miso-190-backcast-calibration-okt1cn` | Branch exists, **tip AT main, nothing unmerged** — the miso-190 PREREG + gates instrument are committed (frozen before the mechanism exists); the miso-188 registration + promotion were already in main at the dispatch base |
| **NYISO eastern-seam PAR Leg-1** | `claude/nyiso-eastern-seam-par-leg1-w7s8mm` | **MERGED AND BRANCH DELETED** — #4318 (Leg-1 A/B registered; iroquois companion REJECTED on its own W-gates) + **#4323 (nyiso-157 PROMOTED by owner ruling — this board's base sha)** |
| **Bench re-stamp / caiso-217 prune** | `claude/backcast-bench-restamp-ns7tl7` | **HALF-LANDED, BRANCH DELETED** — #4321 executed the re-stamp (bench gate green); **the prune half is outstanding** (parity still red on `caiso217_crosswalk`) |
| **O7 attribution harness** | — | **Dispatched at the sitting; NO BRANCH VISIBLE YET** (surface: `src/` + ERCOT probes) |
| **FF-2D verdict re-score** | — | **Dispatched at the sitting; NO BRANCH VISIBLE YET** (surface: `frontend/data/forecast/`) |
| ercot-239 residual queue | `claude/ercot-239-residual-queue-lbkvbf` | Merged **#4320/#4322** (zero-solve Phase-0 precommits + Amendment 1); branch survives at main — **not an audit-program lane** |
| caiso-221 south-belly | `claude/caiso-south-belly-pricing-24uv07` | Merged **#4316** (object killed with measurement); branch survives at main |
| capx-director desk | `claude/capx-director-session-pacv16` | **A DIFFERENT PROGRAM** (#4317/#4319 — the capx ledger, per the v13 conflation warning); not this board's work |

**The honest reading: the two sitting-dispatched lanes with no branch yet
(O7 harness, FF-2D re-score) are the ones to look for next cycle — by
BRANCH, not by a plausible-sounding commit.** A lane that has run leaves a
branch; this cycle every launched lane's branch was found, and the two
unstarted ones are named rather than assumed launched.

### v13's lane state, retained as history (at `99c8cf5`)

**ZERO branches are ahead of `main`, and ZERO pull requests are open.** Both
re-derived, not assumed — the branch shas were read directly from `ls-remote`
rather than through `FETCH_HEAD`, which resolves misleadingly for a
non-updated branch.

| Branch | Tip | Ahead of `main` | Reading |
|---|---|--:|---|
| `claude/ercot-backcast-calibration-00mjs2` | `99c8cf5` | **0** | **ercot-234.** The dispatch calls this *"MID-FLIGHT, do not disturb"*; **its work MERGED as #4260 before this lane started.** Everything it had is pushed. **Still owed: the rule-16 three-year re-solve** (C-2) |
| `claude/south-firm-export-hunt-23l7er` | `38e0cc1` | **0** (14 behind) | **miso-185.** Merged as #4261. **STALE branch, not a live lane** |
| `claude/capx-director-ledger` | `99c8cf5` | **0** | **A DIFFERENT PROGRAM's ledger** (`docs/handoffs/capx-director-ledger-2026-08.md`). It **moved this window**, and it is **exactly the plausible-sounding commit that would have hidden this board's own non-launch** |
| `claude/ercot-backcast-calibration-9wkxrg` | `282ced9` | **0** (70 behind) | **STALE branch, not a live lane** — its ercot-232 work merged earlier |

**🔴 SO THE HONEST READING IS: NO AUDIT-PROGRAM LANE IS RUNNING AT THIS PIN.**
Four branches exist; **all four are at or behind `main`.** v12 could report four
live lanes; v13 cannot report any, and **should not soften that by listing
recently-completed sessions as though they were current.** The one piece of work
that is genuinely outstanding is the **ercot-234 Z-A re-solve**, and it is
outstanding *without a branch carrying it*.

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

**v14's protocol amendments — one passed check recorded as such, one new:**

- **🟢 THE DISPATCH-VS-LAUNCH CHECK PASSED THIS CYCLE — the first time in four
  boards.** The v14 board-refresh prompt launched (this lane's branch exists
  and both files landed), breaking the v11 → v12 → v13 failure streak. The
  branch check stays: **look for the BRANCH, not a plausible-sounding
  commit** — this cycle the capx-director ledger moved again (#4317/#4319)
  and would again have fooled a commit-list scan. The two lanes dispatched at
  the sitting with **no branch yet** (O7 harness, FF-2D re-score) are named
  on the roster as unstarted rather than assumed launched; **checking for
  those two branches is step 0 of the next refresh.**
- **🔴 NEW — PIN ONCE, THEN RECORD MOTION; A DISPATCH FACT AND A PIN FACT ARE
  DIFFERENT MEASUREMENTS.** `origin/main` advanced FOUR times while this lane
  measured — including a ruled lane executing (#4321 flipped the bench gate
  green mid-measure) and an owner-ruled promotion (#4323) that became the
  base sha. Chasing HEAD re-opens every measurement; freezing at the dispatch
  base reports stale facts as current. The working rule: **fetch until the
  measurements settle, pin ONCE, re-run every volatile check at that pin, and
  record dispatch-time facts and pin facts as separate, labelled states**
  (as D-5's "ruled AND executed" and D-3's "🆕 at the pin" do). The shard
  HISTORY, not the dispatch's endpoint list, is the promotion record — the
  deltas block compressed nine promotion events to four endpoints.

**Carried, restated in one line each** (full text in v10–v13): run the gates,
never quote them (exit codes captured directly, not through a pipe) · quote no
cycle count without its base sha, in the dispatch and on the board · trust no
table, including the dispatch's — re-derive from committed bytes at the pin ·
a refresh is complete when the sessions exist, not when the prompts are
written · check the live roster before declaring a lane unlaunched · read a
content-addressed identity before inferring.

**While the program is parked, the refresh cycle is not the live instrument it
was.** A park-period refresh confirms (a) whether the owner has ruled on
anything in the queue — **four rulings this window, all executed or
dispatched**; (b) whether the keeper freeze has been called — **answered by
direction: calibration continues, nine promotions in five days, G2 parked BY
CHOICE**; and (c) whether the golden tier's park has been lifted — unchanged,
and the CI proof stays deliberately unspent.

## RESTART CHECKLIST — for whoever un-parks the program

**Do these in order. Do not start at change (a).**

0. **🟠 `main` IS HALF-GREEN AT v14 — re-run at `0a5e896`, not quoted:**
   `check_mechanism_matrix.py` **exit 0** · `check_forecast_staleness.py`
   **exit 0 with a live FR-21 WARN (Δ = 12/10)** — the authorized FF-2D
   re-score lane is the remedy; check whether it has landed ·
   `check_registry_payload_parity.py` **exit 1** on `caiso217_crosswalk` —
   **the prune is RULED (D-6)**; if it has not executed yet, that is lane
   work in flight, not a decision to make · `audit_keepers.py` **PASS 0/0**
   · `check_bench_freshness.py` **0 STALE of 20** (ruled re-stamp executed,
   #4321; six ungated engine-drift WARNs). **Always re-run all five rather
   than reading this line.**
0b. **🟢 v13's TWO-ISO REPRODUCTION WARNING IS RESOLVED BY EVENTS — BUT ITS
   LESSON IS PROMOTED INTO THE GOLDEN QUESTION.** The two bundles that did
   not reproduce at HEAD are no longer the designated keepers: ERCOT
   re-solved on the EASTEX topology (ercot-234 bundle committed, registered,
   promoted — plus the 236 carve-out) and CAISO's keeper is now caiso-220
   with a fresh committed bundle. What remains true: **every stage-0 golden
   is captured against a tree that no longer matches HEAD**, the manifest's
   provenance sha (`af1ccb6`) does not resolve, and promotion velocity (nine
   events in five days) means any capture ages in days. Whoever re-captures
   decides, per ISO, *which tree the golden is a golden OF* — and verifies
   via the per-file `content_hashes`, which remain valid either way.
1. **DECIDE THE GOLDEN TIER AND THE FREEZE TOGETHER** — the precondition, not
   a nicety. A freeze buys re-captured goldens; a parked golden tier means
   those captures cannot be certified byte-green, so a freeze alone leaves G2
   leg 1 blocked. Un-parking costs one `workflow_dispatch` (billed minutes —
   why it was parked). **Do not wait for a cheap calibration window; there
   has not been one in thirteen cycles, and this window had nine
   promotions.** Current owner direction is to continue calibration on all
   six ISOs — deferred by choice, not blocked.
2. **RESOLVE THE STAGE-0 MANIFEST'S PROVENANCE SHA BEFORE TRUSTING ANY
   CAPTURE.** `git_sha: af1ccb6` still does not resolve at HEAD — shallow
   clone or 2026-08-16 rewrite orphan; the captures are dated inside the
   rewrite window. **The per-file `content_hashes` are unaffected — verify
   against those.**
3. **Re-verify every stage-0 golden against the then-current keepers** before
   resuming any change. Do not trust this board's staleness table — re-read
   the keeper shards and the manifest at that HEAD and re-derive it, mapping
   captured bundles back through the manifest's `keeper_id` fields. **At
   `0a5e896` the answer is: all five captures stale, PJM never taken, and
   ERCOT needs TWO captures (forward + carve-out) for full coverage.**
4. **Assume every re-capture is a real solve.** The gaps at this pin: **MISO
   eleven** promotions past capture, **NYISO ten**, **ERCOT six** (forward
   line, plus a second designated config with no golden at all), CAISO two,
   NEISO two. The **re-stamp-not-re-solve** shortcut was established for
   **neiso-97 only** — re-establish it before relying on it; re-derive the
   config diff first.
5. **Capture PJM FIRST.** No golden at all, a keeper unmoved for **six**
   cycles, the only clean scorecard on the board (8/8, zero caveats).
   Simultaneously the largest coverage gap and the cheapest capture —
   untaken across six consecutive boards.
6. **Do NOT re-do change (c).** It landed via #3964 and is byte-identical at
   HEAD. Verify the blob (`af34031c`) rather than re-porting it.
7. **Close the #4054 residual if you want belt-and-braces — but re-derive it,
   do not inherit it.** The NYISO keeper is now **TEN promotions** past the
   captured nyiso-140 config.
8. **Then, and only then, resume changes (a)–(e)** — and re-read the G2 leg
   list, because *merged byte-green* is what the gate wants, not captures.
9. **Confirm the golden tier is green IN CI before claiming any byte-green
   result** — which requires un-parking it (step 1). A tier that cannot
   provision `data/clean` cannot prove byte-identity of anything, and a local
   replay is not the gate.
10. **🔴 FIX THE PARITY GATE'S CLASSIFIER, NOT ITS SYMPTOM.** The ruled
    caiso-217 prune retires this instance; the class does not go away —
    `KEEP_REQUIRED_UNMAPPED_BUNDLES` stands at **26 named entries** and the
    class-level carve-out the 2026-08-20 finding recommended (pre-registered
    recipes and in-flight controls legitimately precede any sidecar) **still
    does not exist** (B-8). ~10 lines, and it retires a recurring red for
    good. Explicitly **not** a pre-merge check, which would penalise correct
    pre-registration. **Until then, the gate's green is a maintenance state,
    not a property.**
