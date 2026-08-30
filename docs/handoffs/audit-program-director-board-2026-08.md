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
> **The golden tier remains PARKED** by the owner's 2026-08-22 ruling, unchanged
> across both cycles below. Say the consequence plainly, as v11 did: **byte-green
> cannot be CLAIMED for G2 while the tier is paused**, so **G2 leg 1 has TWO
> parked dependencies** — WS3/PERF-B and the golden tier — not one.
>
> ### 🔴 THE DISPATCH-VS-LAUNCH FAILURE HAPPENED A **THIRD** TIME, AND IT IS NOW THE FINDING
>
> **The v13 prompt was issued in the SAME batch as the two entry-signal prompts
> on 2026-08-24. Those two launched and merged (#4248, #4253 — one lane executed
> BOTH). This one did not, so the board sat at v12 across two more director
> cycles.** That is three consecutive boards carrying a dispatch-vs-launch
> failure (v11 → v12 → v13), which stops being an incident and becomes the
> desk's characteristic defect.
>
> **What caught it is worth recording as the method, because the near-miss was
> real:** the director's stated check is *look for the BRANCH, not a
> plausible-sounding commit.* `claude/capx-director-ledger` MOVED this window —
> a director-ledger branch, freshly merged, belonging to a **different program**
> (`docs/handoffs/capx-director-ledger-2026-08.md`). Reading a commit list would
> have shown "director ledger updated" and passed. Only the branch check
> distinguishes them.
>
> ### 🟢 NEW AT v13 — THE ENTRY-SIGNAL THREAD IS **ADJUDICATED**, AND THE FAILED PREDICTION WAS THE INFORMATIVE HALF
>
> `entry_lookahead_reprice`, ERCOT `fc`: **K → O** on four LP solves. The disarm
> hit L-1's storage prediction **to the megawatt** and **failed** its gas
> prediction in the opposite direction — which is what *measured* the
> fleet/run-identity residual L-1 declared but could not size. **Neither a
> promotion nor a rejection.** See change C-1.
>
> ### 🔴 AND: A KNOWN-WRONG MEASURED INPUT WAS FOUND ARMED IN THE ERCOT KEEPER — AND THE REPAIR IS NOW HALF-LANDED
>
> **Card Z SIGNED (Z-A).** ERCOT defines `NE_LOB` as *"North Edinburg – Lobo"*,
> a **South Texas / Rio Grande Valley** stability corridor; the model read it as
> *"**N**orth**e**ast **lob**e"* and built a zone carve, a static rating and an
> hourly overlay on that reading. **The defect class is the reusable lesson, not
> the ERCOT anecdote: a measured input whose NAME was mis-read as geography.**
> Rule 14 `[R-ACCURATE]` is precisely the rule that refuses the leave-it-as-is
> option. **New at this pin and not in the dispatch: the repair's CODE has
> MERGED (#4260) but the rule-16 three-year re-solve has NOT, so HEAD's ERCOT
> topology no longer matches the designated keeper's solved topology.** See
> change C-2.
>
> ### 🟢 AND: **NYISO FRONTIER RATIFIED** — v12's owner-queue item 7, signed
>
> Owner decision 2026-08-23, in session: *"Ratify NYISO."* It retires the item
> that had the desk's own director session idle-blocked, and makes the frontier
> set **{PJM, NYISO, NEISO}** — again exactly the `complete` set.

> **STATUS: PARKED AT G1** — live rollup maintained by the program-director
> session, updated on each owner "refresh". Canonical program definition:
> `docs/model-audit-release-plan-2026-08.md` (its §8 ledger is the durable event
> record; this board is the at-a-glance state). Completion figures are the
> director's estimate against each workstream's full DoD (A+B halves).

**Snapshot (v13):** **BASE SHA FOR EVERY FIGURE ON THIS BOARD: `99c8cf5`**
(merge of #4261), derived live from `origin/main` on 2026-08-25, not taken from
the dispatch. **The dispatch's stated base `b2fef73` is REACHABLE BUT STALE —
`origin/main` had advanced 18 commits / 4 merged PRs past it before this lane
started**, and the single largest thing in that gap is the ercot-234 Z-A repair
merging (#4260), which the dispatch describes as *"MID-FLIGHT, do not disturb"*.
Every count below states the window it was measured over. Nothing is carried
from the dispatch, from board v12, or from any table, unverified.

**Two windows are used deliberately, because they answer different questions
and collapsing them would produce a false "nothing moved":**

| window | span | commits | non-merge | merged PRs |
|---|---|--:|--:|---|
| **since v12 LANDED** (`a6886de..99c8cf5`) — what the board is stale by | 2026-08-23 → 2026-08-25 | **141** | **99** | **42** (#4220–#4261) |
| **since the dispatch's base** (`b2fef73..99c8cf5`) — what moved after the prompt was written | 2026-08-24 → 2026-08-25 | **18** | **14** | **4** (#4258–#4261) |

**This matters for one claim in particular.** The dispatch states *"NO KEEPER
MOVED THIS CYCLE."* That is **true on the narrow window and FALSE on the board's
own window**: **ERCOT promoted `2026-08-20-ercot223-arm-eventrelease` →
`2026-08-24-231-tie-zone-measured`** inside `a6886de..99c8cf5`. Re-derived from
the shards, not from a PR title. The other five are genuinely unmoved.

**Cycle span, re-derived with `git rev-list` against the v11 board's own
derivation pin `04605b7a`:**

| Span | Commits | PRs merged | Registry sidecars added |
|---|--:|--:|--:|
| **Cycle A** `04605b7a..fc9f9ec` | **75** | **16** (#4195–#4210) | **6** |
| **Cycle B** `fc9f9ec..1b8ddac` | **30** | **9** (#4211–#4219) | **0** |
| **Both** `04605b7a..1b8ddac` | **105** | **25** | **6** |

**🔴 CORRECTION TO THE DISPATCH'S OWN CYCLE ARITHMETIC.** The dispatch states
cycle A is *"54 commits / 9 PRs"* and the two-cycle span *"roughly EIGHTY-FOUR
commits and eighteen merged PRs"*. **Cycle B reproduces exactly (30 / 9); cycle
A does not, under any base tried.** From `04605b7a` (the sha v11 actually pinned)
it is **75 / 16**; from `4e1a4bc` (v11's *merge* commit, PR #4200) it is
**47 / 10**; the two-cycle span from `4e1a4bc` is **77 / 19**, which is the
closest thing to the dispatch's "84 / 18" and still not it. **The lesson is not
that the numbers are small or large — it is that a cycle count quoted without
its base sha is not a measurement.** This board states its base sha in the same
sentence as every count, and the next dispatch should too.

**ZERO open PRs** (live `list_pull_requests`) and — for the first time since
v10 — **ZERO unmerged remote branches.** Four branches survive their merges
(`caiso-belly-lever-plan-7d6rwk`, `ercot-energy-tightness-channel-vm4w8k`,
`forecast-gate-refresh-mohs9e`, `miso-offer-dispersion-yk0zsq`), **all four
`ahead=0`**, verified individually with `git merge-base --is-ancestor` rather
than inferred from the listing. **v11's one genuinely-unmerged branch
(`14ce4ce`, the matrix-gate repair) merged during cycle A as #4210** — owner
queue rank 0 is retired.

**Headline, both cycles in one line: the program promoted three keepers and
closed a six-cycle governance item, then spent an entire cycle refuting its own
levers — and the audit workstreams did not move at all.** WS1–WS6 are
**byte-unmoved across both cycles**; the only files either cycle touched that
this board owns are the v11 records lane's own two, and **no `.github/workflows/`
file and no `results/regression-goldens/` file changed in 105 commits** (verified
by `git diff --name-status`, not assumed).

## What moved — v13 CYCLE (`a6886de..99c8cf5`, "the adjudication cycle")

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

## What moved — CYCLE A (v12 record, RETAINED as history) (`04605b7a..fc9f9ec`, "the promotion cycle")

**Character: 75 commits, 16 PRs, six new sidecars, TWO keeper promotions, and
three lane prompts that all launched and all merged.** This is the desk working
as designed.

**A-1. 🟢 ALL THREE DISPATCHED LANE PROMPTS LAUNCHED, RAN AND MERGED.** #4204
(`forecast-gate-refresh`), #4207 (CAISO T1-H), #4209 (ERCOT T1-H). Recorded
because the *next* cycle's failure is exactly the absence of this — a cycle in
which every issued prompt lands is the baseline the desk should be measured
against, not a happy accident.

**A-2. 🟢 THREE PREVIOUSLY-STRANDED BRANCHES MERGED**, which is what unblocked
the rest of the cycle: the **v11 records lane itself** (#4200 —
`director-records-board-ledger-rjauh9`), `nyiso-frontier-status` (#4196/#4201/
#4205/#4208, a four-PR lane) and `ercot-2023-summer-scarcity` (#4195/#4199/
#4202/#4210). The last of those carried the matrix-gate category repair v11
recorded as *"one merge away, no PR open"* — it merged as **#4210**.

**A-3. 🟢 RHO_CLIP CLOSED END TO END — THE CYCLE'S BEST OUTCOME, AND THE OWNER
QUEUE'S RANK-1 ITEM FOR SIX CYCLES IS RETIRED.** Four acts, in order, all on the
record:

1. **REFUTED** on MISO's primary record —
   `FINDING-miso177-rho-clip-floor-identification-2026-08-22.md`: *"the 0.5 floor
   has NO identification — not in this repository, not in MISO's market rules,
   not in the physics — and the negative result is the deliverable."* **No solve
   was spent producing it**; every number is read from committed artifacts, the
   committed source, and MISO's own published manual.
2. **DELETED** by the owner's same-day band ruling (nyiso-151 card, option A).
   Verified at the pin: `src/market_sim/data/online_reserve_rho.py` now reads
   `RHO_CLIP: tuple[float, float] = (0.0, 4.0)` and
   `model/reserves/spec.py` documents it as *"floorless since the 2026-08-22
   owner ruling"*. **The floor is gone, not zeroed into a re-armable parameter**
   — rule 25 `[R-DELETE]` honoured in the act that closed the item.
3. **RE-SOLVED** by a pre-registered A/B (`PREREG-miso177-rho-measured-ab`):
   control **R-0 bit-identical** to the committed keeper, arm at the
   CAMPD-measured **0.17644175978069962**.
4. **PROMOTED** as keeper `2026-08-22-miso-177-rho-measured`, **with ZERO new
   degrees of freedom** — DOF ledger read live from the bundle's own
   `calibration_attestation.json`: **`n_entries` 33 / `n_residual` 2.**

   **RETIRE IT FROM THE OWNER DECISION QUEUE.** It stood at rank 1 for six
   cycles as a live rule 5 `[R-NO-MAGIC]` exposure inside a mechanism MISO had
   been promoted six times on top of. It was closed by measurement plus one
   owner ruling, and the re-solve cost one `--set` exactly as the board predicted.

**A-4. 🟢 TWO KEEPER PROMOTIONS.** Both re-derived from the keeper and status
shards at the pin, not quoted:

- **NYISO → `2026-08-22-nyiso-152-duty-complete`**, determination **`CALIBRATED`**
  (grade summary scored 8 / target-grade 7 / **0 FAILs** / 1 ledgered). C3a(RT)
  **+5.3 % / −2.7 % / −8.1 %**, all three PASS. The completed duty-role mechanism
  for the measured capacity-only CC cohort — `cc_reserve_duty_split` (the offer
  half, twice REJECTED-AS-ARMED bare, **both records standing unrewritten**) plus
  the NEW `nyiso_gas_bridge_reserve_duty_exclusions` (the commitment-population
  half). Promoted on its own pre-registered rule, no owner override. It
  superseded `2026-08-22-nyiso-151-identity-hr`, itself promoted the same day.
- **MISO → `2026-08-22-miso-177-rho-measured`**, determination **`NOT-YET`**
  (scored 8 / target-grade 6 / **1 FAIL** / 1 ledgered). The sole failing
  criterion is **C3a-2025 at −11.75 %** (model $40.12 vs actual $45.46,
  load-weighted RT) — 2023 **+1.3 %** and 2024 **−4.1 %** both PASS. C3c is the
  single ledgered caveat.

**Three CALIBRATED still stands** (PJM, NYISO, NEISO) — see the keeper table.

**A-5. 🟢 THE FORECAST GATE (a) WAS RE-DERIVED, AND THE LANE CORRECTED THREE
LATENT BOARD ERRORS RATHER THAN ONLY ITS OWN.** NYISO's gate (a) moved
**fail → pass**, giving **THREE gate-(a) passers — PJM, NYISO, NEISO — which is
exactly the `complete` marker membership**, the third independent read this
program has produced of the same three-ISO set. The lane also repaired: PJM's
`closed_on` (`['a','b']` → **`['b']`** — PJM was never closed on gate (a)),
MISO's stale *"NONE PARSEABLE"* determination reading, and NEISO's incorrect
sole-passer claim. **Gates (b) and (c) remain UNSCORED and unmoved** — no
forecast run was solved or re-scored to produce any of this, and the lane
deliberately stamped its provenance under field names
`check_forecast_staleness.py` cannot mistake for a re-score.

**A-6. 🟡 NYISO'S TESTABLE SET IS DECLARED EXHAUSTED.** `nyiso-153`
(in-city obligation) came back **REJECTED-AS-ARMED** on its pre-registered
branches, with a durable positive finding kept out of the rejection: *the
downstate under-commitment is REAL, the instrument is wrong*. `nyiso-154` then
found the DA-horizon uncap **effectively inert** and filed
`ASSESSMENT-nyiso154-frontier-2026-08-22.md`: **the testable set is EXHAUSTED,
every remaining open item is an owner decision or a ledgered model-class
limitation, RECOMMENDED FOR OWNER RATIFICATION.** That recommendation is
**still open** and is now owner-queue item 8 — the director desk's own session
is idle-blocked on it at this read.

**A-7. 🔴 CROSS-ISO FINDING — THE ERCOT AND CAISO T1-H HINDCASTS INDEPENDENTLY
REPRODUCED THE SAME CAPACITY-ENTRY DEFECT. RECORD IT AS AN OPEN PROGRAM ITEM.**
Two lanes, two ISOs, no shared author, same failure. Measured from the committed
reports:

| | CAISO (actual → model, GW) | ERCOT (actual → model, GW) |
|---|---|---|
| **storage** | 15.147 → **0.0** (**−100 %**) | 13.691 → **5.0** (**−64 %**) |
| **gas_cc** | 0.0 → 3.0 | 0.244 → **9.0** (**+3,588 %**) |
| **gas_ct** | 0.136 → **11.838** (**+8,630 %**) | 3.692 → 7.571 (+105 %) |

**The shared mechanism is named precisely in the CAISO report and it is a step
ordering, not a tuning gap:** *"step-5 storage entry never fires before the
step-6 backstop"* — so the reserve-margin adequacy backstop fills the entire firm
gap with its only instrument, generic CT, and then **ratchets** (it built
1,676 MW for CAISO's 47.6 GW 2024 peak, **none of which can exit** when the 2025
peak recedes, landing 2025 at RM **28.2 %** against a 15 % target). CAISO's own
summary: *"the volume is right — total decision-basis additions 28.8 GW vs
26.6 GW actual — the technology is wrong."*

**🔴 ONE CORRECTION TO HOW THE DISPATCH STATES THIS FINDING, because it matters
for whoever picks the item up.** The dispatch reads *"storage and wind do not
enter economically"*. **The storage half is cross-ISO and robust. The wind half
is NOT — the two ISOs miss wind in OPPOSITE DIRECTIONS:** ERCOT **−97 %**
(12.663 → 0.35 GW) against CAISO **+757 %** (0.7 → 6.0 GW). CAISO's wind is an
**RPS-ladder artifact with a different root cause**, stated in its own report:
*"renewables are ladder/RPS-driven, not price-formed, and the RPS is at its
escape valve"* — the `rps_dual` sits at exactly **$50.0/MWh**, CAISO's
`STATE_RPS_ACP` escape price, in **every solved year**. **Two defects, not one.**
Chartering them as a single "renewables don't enter" item would send the lane
after a common cause that the evidence says is not there.

**A-8. Lane inventory, cycle A.** Five ISO lanes active — ERCOT 227/228/229,
CAISO 213, MISO 176/177, NYISO 151/152/153/154, plus the forecast-gate and two
T1-H hindcast lanes. Six new registry sidecars: `miso-177-control`,
`miso-177-rho-measured`, `nyiso-151-identity-hr`, `nyiso-152-duty-complete`,
`nyiso-153-incity-obligation`, `nyiso-154-da-horizon`. **Every one of the four
NYISO arms was registered — including the two rejections** (rule 15
`[R-DASHBOARD]` working: a rejected probe is registered, not narrated away).

## What moved — CYCLE B (v12 record, RETAINED as history) (`fc9f9ec..1b8ddac`, "the identification cycle")

**Character, and it is worth naming precisely: five lanes, all diagnostic,
almost no LP, ZERO promotions — and EVERY ONE closed by refuting or bounding its
own lever rather than arming one.** Keepers are unchanged across **all six
ISOs**; `frontend/data/backcast/keepers/`, `status/`, `calibration-complete.json`
and `holdout-freeze.json` are **byte-unmoved** in the whole cycle, and **zero
registry sidecars were added**. A cycle that ends with six unchanged keepers and
five closed questions is not a wasted cycle — but it must be reported as what it
is, and the freeze arithmetic (owner queue item 3) should read it honestly.

**B-1. 🟢 ercot-230 — `ercot_adaptive_fixed_point` is MEASURED-INERT-AT-FIXED-
POINT, and the negative result is unusually strong.** The second adaptation pass
**converged after ZERO additional passes**: the keeper path regenerates its own
floor **bitwise** (sha `44f664bd` on both sides), so pass 3 would solve the
identical LP. The arm is numerically identical to the control on **all seven
sidecars**, official digits unchanged at **−39.7 / 0.729 / 74**, every gate PASS,
**`d_price_at_miss` p50 = max = 0.0**, adoption 0.00 pp against a 1.5 pp bar.
**What it establishes is the point, not the null:** the ercot-221 one-pass
convention is measured **EXACT rather than approximate**, and the bootstrap
starvation (7 model event days against reality's 23) is a property of the
within-year adaptation **map itself** — the conduct channel cannot bootstrap
itself out of the depth gap within a year. Of the FINDING-ercot221 §4 named
successors, only the seasonal end-of-season term is still un-adjudicated. Field
stays default-off.

**B-2. 🟢 ercot-230 ALSO REPAIRED A STALE ERCOT MATRIX STAMP — and the class of
defect is the one this board keeps finding.** HEAD carried ercot-221's
**−39.4 / 0.723** where the designated keeper `ercot223` actually scores
**−39.7 / 0.729**. Verified repaired at the pin: the ERCOT shard now carries
`-39.7`/`0.729` (five occurrences each) with the superseded pair surviving twice
**as history text**, which is correct — the ercot-221 record stands unrewritten.
**Worth a board note because of what it is: published state drifting from the
artifacts underneath it, caught by a LANE rather than by a GATE.** It is the same
class as the forecast gate board's own stale keeper ids (change B-7) and as WS5's
site-facts repairs. The matrix guard now *does* check keeper stamps
(`"keeper stamps match every keepers/<ISO>.json"` in its output) — that check
passes at the pin, which means the drift was in the *evidence text*, which no
gate reads.

**B-3. 🟡 ercot-231 — the N1–N5 non-AS energy/tightness factor program is
pre-committed, and N1a is built DEFAULT-OFF.** `ercot_tie_zonal_interchange`
added to `ScenarioConfig` with a **base matrix row and a cell line in all six
ISO shards**, which is rule 26 `[R-MECH-MATRIX]` duty (c) satisfied in the same
PR that added the field — verified by count, not asserted. Phase-0 probes N1b/
N2/N3/N4/N5 all committed. The lane is **REVIEW_READY** at this read with a
static-TTC control re-solve in flight.

**B-4. 🟢 caiso-215 — the C3a overrun is LOCALISED, and the localisation kills a
whole lever class rather than opening one.** CAISO's 2024/2025 overrun is **a
north–south split at Path 15**: the south (LA_BASIN + SDGE + SP15_rest + ZP26,
~61 % of load) carries **~100 % of the net ISO gap** at +19–27 % per zone, while
**NP15 UNDER-prices** (−6.6 % / −0.8 %). The model's N–S spread has the **wrong
sign** (model −$1.9 to −$2.3 against actual +$5.6 to +$9.1), and reality's split
is **80–90 % congestion the model never develops** — **0 hours** of NP15−SP15
> $15 against **1,310–1,691 actual**. **The load-bearing consequence: every
zonal redistribution nets to ≈ 0 ISO-wide (bridge terms ±$0.15), so NO
MEAN-ZERO ZONAL INSTRUMENT CAN MOVE C3a.** The scored failure remains the common
level term — but the error is now localised to the **southern solar belly**
(35–64 % of the south's gap in hours 10–15), which changes the admissibility
arithmetic: a south-belly-scoped object needs only **~46 %** of the measured
south-hour error to close C3a-2025 and is **2023-safe even at full size**, which
the broad level-down never was. **Nothing armed. No `ScenarioConfig` field. No
LP. No cell verdict moved.**

**B-5. 🟡 caiso-216 — the belly-surplus phase-0 measurement answers the lever
CLASS and files a costed funding ask.** The model's south-of-Path-15 **does**
carry a belly surplus (positive in 72–85 % of reality's south-negative hours,
growing +1.1 → +2.3 → +3.4 GW mean 2023→25) but it is **under-allocated and
invisibly absorbed** — the armed S→N ratings bind **17/234/289 h** against
reality's 1,310–1,691. Root cause is a **zone-assignment defect measured against
CAISO's own `ATL_PNODE_MAP`**: DIABLO and TOPAZ sit in TH_ZP26 (model: NP15),
Tehachapi ALTA/WINDHUB in TH_SP15 (model: ZP26), MUSTANG in TH_NP15 (model:
ZP26). With membership-measured re-allocation — **input arithmetic, no LP** —
bound hours reach **742 h (2024) / 1,143 h (2025) against 342 h (2023)**:
reality's order, in reality's year-ordering, with 2023 3× smaller, i.e. the
2023-safe geometry caiso-215's envelope requires. **The ask is two items: the
measured generator-hub-membership crosswalk intake (zero free parameters) and
ONE 3-year solve under a pre-registered gate table.** That crosswalk lane
**launched at cycle B's refresh and is running now.**

**B-6. 🟡 miso-178 — the C3a-2025 anatomy at the measured-rho keeper.** **82 % of
the −11.75 % miss is an 88-hour tail**, the whole annual target is
deterministic-reachable, and the lever plan is ranked with rule-13 admissibility
and measured reach bounds. **No LP, nothing armed, no field, no registration.**

**B-7. 🟢 miso-179 — THE BEST PROCESS ARTIFACT OF EITHER CYCLE, and it deserves
to be named as such.** `miso_offer_level_dispersion` was **minted `R` at its own
PRE-REGISTERED, NO-LP PRE-CHECKS** — thresholds frozen in a committed prereg
*before* the identification derive or any hour-set-conditioned quantity existed,
pushed at `4712ae8`, derive at `00a81a7`, probe at `492f1d4`, **in the prereg's
own stated order**. Two checks fired:

- **K-PRE-a**: the model's own affected stack already disperses **$36.94/MWh**
  p90−p10 at the 2025 summer top-decile margin against the eligible book's
  **$68.27** — ratio **0.541**, over the frozen ≥ 0.5 kill line. The object is
  roughly **half** the size its attribution implied.
- **K-PRE-c**: the granted rank-mapped LEVEL construction is predicted to move
  C3a-2023 from **+1.28 % to −40.1 %**, ~−42 pp in every year — a faithful level
  transfer **crashes the body**, because below ~p90 MISO's real eligible book
  offers far below the model's.

**K-PRE-b CLEARED** — the family fails on **size and form, not eligibility**,
which is the honest reading and the one that tells the successor lane what to
change. **Verified at the pin: `miso_offer_level_dispersion` has an `R` cell in
the MISO shard and ZERO occurrences in `ScenarioConfig`.** A mechanism
adjudicated `R` with **no field created and no solve spent** is rule 26
`[R-MECH-MATRIX]` and rule 1 `[R-STRUCT]` working exactly as intended, and it is
the cheapest possible way to close a lever. **The successor — MISO-180, anchored
spread-only — launched at cycle B's refresh and is running now.**

**B-8. 🔴 THE PARITY GATE IS GREEN, AND THAT IS NOT THE SAME AS FIXED.** Run at
the pin, `check_registry_payload_parity.py` exits 0: **53 runs checked, 76 bundle
dirs swept, 0 known-unsynced tolerated.** But the mechanism is unchanged.
`KEEP_REQUIRED_UNMAPPED_BUNDLES` is still a hand-maintained frozenset, and it
grew across the cycles exactly as v11 predicted it would:

| Pin | Allowlist entries |
|---|--:|
| `04605b7a` (v11's base) | **15** |
| `fc9f9ec` (end of cycle A) | **24** |
| `1b8ddac` (end of cycle B) | **24** |

**+9 in cycle A; +0 in cycle B only because no lane solved anything.**
**22 of the 24 entries are NYISO.** The 2026-08-20 finding recommended *a
class-level carve-out for meta-only, doc-cited dirs "so this list stops growing
one arm at a time"* and **built the list instead**; three days and one cycle
later the list is 60 % longer. **The gate will re-red on the next NYISO A/B**
unless the carve-out is actually built — and the four lanes running right now
include two that will produce A/B arms. **Green-by-allowlist is a maintenance
debt reporting itself as a pass.** Build the carve-out; the restart checklist
already costs it at ~10 lines.

**B-9. 🔴 DIRECTOR PROCESS FAILURE — RECORDED PLAINLY, BECAUSE THE PROTOCOL
NAMES IT AS THE MOST LIKELY ONE.** Two prompts were issued at the end of cycle A
— the **ENTRY-SCREEN DIAGNOSTIC** (the A-7 cross-ISO capacity finding) and
**DIRECTOR-RECORDS v12** (this board) — and **neither was launched.** The
consequence is measurable and is the whole reason this entry covers two cycles:
**the board was silently wrong for 105 commits and 25 PRs**, asserting two red
gates that had gone green, a keeper set two promotions stale in two ISOs, and an
unmerged branch that had merged. The refresh protocol already carries the rule
(*"a dispatch that is never launched leaves the board silently wrong — verify the
landing before declaring a cycle done"*, added at v11 from the v5→v6 gap); **it
was written and then not applied.** Both prompts were re-issued at cycle B's
refresh and **both are running at this read**, alongside two more. The protocol
amendment this earns is at the bottom of the board: **a refresh is not complete
when the prompts are written — it is complete when the sessions exist.**

## Keeper table (read from `frontend/data/backcast/keepers/<ISO>.json` and `status/<ISO>.js` at `99c8cf5`)

Determinations and grade summaries parsed live from the status shards. **C3a(RT)
is the load-weighted mean-LMP error against RT actuals, per year 2023 / 2024 /
2025** — printed for every ISO because it is the criterion three of the six fail
on, and printing it only for the failures hides how narrow the margins are.

| ISO | Designated keeper | Determination | Grade (scored/target/fails/ledgered) | C3a(RT) 2023 / 2024 / 2025 |
|-----|-------------------|---------------|---|---|
| ERCOT | **`2026-08-24-231-tie-zone-measured`** ⬅ **MOVED this window** | `NOT-YET` | 8 / 5 / **2** / 1 | **−38.0 % F** / +0.4 % / −7.7 % |
| CAISO | `2026-08-17-caiso-200-h1-memberpanel` | `NOT-YET` | 8 / 6 / **1** / 1 | +4.1 % / **+12.8 % F** / **+15.7 % F** |
| PJM | `2026-08-15-pjm-162-inputclock` | **`CALIBRATED`** | 8 / **8** / 0 / **0** | +6.2 % / −0.8 % / −7.7 % |
| NYISO | `2026-08-22-nyiso-152-duty-complete` | **`CALIBRATED`** | 8 / 7 / 0 / 1 | +5.3 % / −2.7 % / −8.1 % |
| NEISO | `2026-08-17-neiso-99-joint-p1` | **`CALIBRATED`** | 8 / 7 / 0 / 1 | +3.1 % / +5.7 % / +1.7 % |
| MISO | `2026-08-22-miso-177-rho-measured` | `NOT-YET` | 8 / 6 / **1** / 1 | +1.3 % / −4.1 % / **−11.75 % F** |

**⬆ ERCOT's row is the one change**, and it is re-derived from the shards, not
from a PR title: the ercot-231 promotion moved C3a-2023 from **−39.7 %** to
**−38.0 %** — a real improvement that **does not clear the band**, and the fail
count is unchanged at 2. **The dispatch's "no keeper moved this cycle" is true
only on the narrow `b2fef73..` window.**

| ISO | v13 cycle (`a6886de..99c8cf5`) |
|-----|-------------------------------|
| **ERCOT** | **🔴 PROMOTED** → `2026-08-24-231-tie-zone-measured` (ercot-231). Then **cards Y and Z both SIGNED**, and the **card-Z identity repair's CODE MERGED without its rule-16 re-solve** — so the keeper's solved topology and HEAD's now disagree (C-2). **The busiest ISO on the board, and the only one carrying a known input defect into its designated keeper** |
| **CAISO** | **UNMOVED.** caiso-218 + caiso-219: **two decisive nulls**, 219 re-locating the belly-hour mass to **GATES–MIDWAY (ZP26 side)** (C-5). Separately, C-1 measured **CAISO's L-1** and found its storage miss is **larger than the signal defect** — next rung is the **value stack**, not a disarm. **Owner chose this lane over the caiso-217 replay**, which is why parity is red |
| **PJM** | **UNMOVED and untouched. FIFTH consecutive cycle.** Still the only ISO with **zero caveats and every criterion PASS** (8/8), still **the largest stage-0 coverage gap (never captured) and the cheapest capture on the board** — now for a **fifth** board running |
| **NYISO** | **UNMOVED as keeper — but 🟢 FRONTIER RATIFIED** by owner decision 2026-08-23 (C-3), retiring v12's owner-queue item 7 and unblocking the desk's own director session |
| **NEISO** | **UNMOVED and untouched.** Its entire residual remains the **`final` grant itself** |
| **MISO** | **UNMOVED.** miso-181→185 closed **five rungs with zero LP**, ending in **V-NEG-ABSENT** on 698 seller-quarter EQR reports (C-4) |
| **ERCOT** | **UNMOVED.** ercot-227 F1/F1b/F3 probes + ercot-228 **F4 DATA-ABSENT** + ercot-229 F1b NSPIN held-depth arm. Fail set unchanged | **UNMOVED.** ercot-230 fixed-point **MEASURED-INERT** (B-1) + the stale matrix stamp repair (B-2); ercot-231 N1–N5 pre-committed, N1a built default-off (B-3). **Two cycles, seven sessions, no promotion** — and every one of them closed a named successor rather than leaving it open |
| **CAISO** | **UNMOVED.** caiso-213 rest continuation — the sixth consecutive, no solve, no probe, no LP | **UNMOVED, but OFF REST.** caiso-215 localised C3a to the **Path-15 north–south split** and killed the whole mean-zero zonal class (B-4); caiso-216 answered the lever class and filed a **two-item costed ask** (B-5), one of which is now running. **The lane rested until it had a question worth an LP** |
| **PJM** | **UNMOVED and untouched** — no PJM calibration lane ran | **UNMOVED and untouched.** **FOURTH consecutive cycle** — and PJM is the only ISO with **zero caveats and every criterion PASS** (target grade 8/8). It is simultaneously the **largest stage-0 coverage gap (never captured) and the cheapest capture on the board**, for the fourth board running |
| **NYISO** | **PROMOTED TWICE** → nyiso-151-identity-hr → **`2026-08-22-nyiso-152-duty-complete`** (`CALIBRATED`), on the prereg's own rule, no owner override. nyiso-153 **REJECTED-AS-ARMED**; nyiso-154 declares the **testable set EXHAUSTED** and recommends frontier ratification (A-6) | **UNMOVED and untouched.** The frontier ratification recommendation is **still unsigned** (owner queue 8), and the desk's own director session is idle-blocked on it |
| **NEISO** | **UNMOVED and untouched by calibration** | **UNMOVED and untouched.** Its entire residual remains the **`final` grant itself** |
| **MISO** | **PROMOTED** → **`2026-08-22-miso-177-rho-measured`**, the RHO_CLIP close-out (A-3), **zero new DOF (33/2)**. miso-176 minted `m2m_seam_entitlement_cap` **`G`** | **UNMOVED.** miso-178 anatomy — **82 % of the −11.75 % is an 88-hour tail** (B-6); miso-179 minted **`R` at its own no-LP pre-checks with no field created** (B-7). Successor MISO-180 running |

**Markers at `99c8cf5`, re-read live this cycle:** `complete` =
**{NEISO, NYISO, PJM}** · **`final` = EMPTY (`_note` only)** ·
**`holdout-freeze.json` `active: true`**, and the freeze outranks both marker
blocks. **`withdrawn` = {NYISO, CAISO}.** The three `complete` entries are **correctly
re-keyed to their live keepers** (rule 22 D-5(b)), verified field-by-field, and
**`audit_keepers.py` returns PASS: 0 failures, 0 warnings** across all six ISOs
plus the holdout / marker / status checks — run, not quoted.

**NO ISO HAS EVER SPENT A LOCKED-TEST YEAR** — verified at the pin rather than
restated. Across all **54** registered sidecars the solve-year histogram is
**{2022: 2, 2023: 52, 2024: 52, 2025: 52}**; the only two out-of-training
registrations are the authorized **2022 validation touchpoints** (PJM
`2026-08-05-pjm-2022-touchpoint`, NEISO `2026-08-06-neiso-2022-corrected-basis`).
**No 2019, no H1-2026, for any ISO** ([R-HOLDOUT]). NEISO's locked test reads
**NEVER GRANTED, NOT SPENT** in its own `locked_test` field (owner decision
D-23) — absence from `final` is not self-explaining and the field is what
distinguishes *never authorized* from *authorized once and spent*. **No ISO is
in the spent state.** This line is re-verified and republished every cycle
because WS5 Job 1 found the public site asserting its exact opposite for two full
weeks after D-23 corrected the record.

**Determinations: PJM, NYISO, NEISO `CALIBRATED` · ERCOT, CAISO, MISO
`NOT-YET`.** The CALIBRATED set is **still exactly the `complete`-marker set,
still exactly the forecast gate-(a) passer set, and now — since the NYISO
ratification — still exactly the FRONTIER set** (`frontier` declared: PJM
2026-07-31, NEISO 2026-07-11, **NYISO 2026-08-23**). **Four independent
instruments agreeing on the same three ISOs across five boards.** **Every one of
the three NOT-YET determinations is C3a**, and in two of the three (CAISO, MISO)
C3a is the *only* failing criterion.

## Workstream rollup

**WS1–WS6 are byte-unmoved across the v13 cycle too.** Verified rather than
assumed: over the full `a6886de..99c8cf5` window (**141 commits**),
`git diff --name-status` returns **empty** for `.github/workflows/`, for
`results/regression-goldens/`, **and for this board and the plan themselves** —
i.e. not even the v12 records lane's own files moved again. Percentages are
unchanged from v12 by construction; nothing moved to re-estimate. **The
workstream table below is therefore carried forward deliberately, with only the
cycle counts and the two gate cells advanced.**

| WS | State | Completion | Blockers / next |
|----|-------|------------|-----------------|
| WS1 `AUDIT` | AUDIT-A **completed** (#3991). Rows **O8 CLOSED**, **O5 CLOSED**, **O4 re-measured and STILL OPEN** (owner card, recommendation (A)) | **In progress ~91 %** | **AUDIT-B gated at G3 — waiting by design.** Rows **O4, O6, O7** open, unmoved two cycles |
| WS2 `DEBUG` | **COMPLETED** — DEBUG-A ✓, DEBUG-B ✓, pjm-162 promoted, landing-verify green on merged main | **Completed** | none; no DEBUG-C continuation chartered |
| WS3 `PERF` | PERF-A ✓. **PERF-B PAUSED BY OWNER.** Stage-0: **5 of 6 ISOs captured**, **PJM never captured**. Changes (c)/(d)/(e) merged, (a)/(b) unstarted. **`results/regression-goldens/` byte-unmoved across both cycles** — verified by `git diff --name-status`, not assumed | **Paused ~74 %** | **Paused, not blocked — and blocked TWICE at G2.** **0 of 6 goldens match their keeper for a THIRD consecutive cycle**, and with the tier parked byte-green cannot be *claimed* even if captures were current |
| WS4 `DOCS` | DOCS-A **completed** (#3999 + #4005); DOCS-B held | **In progress ~60 %** | **DOCS-B gated at G2 — waiting by design** |
| WS5 `SITE` | **Job 1 (site factual repair, pre-G3) COMPLETE ACROSS BOTH PASSES** (#4120/#4121, #4187/#4191). Job 2 = **SITE-A**, not started | **Job 1 COMPLETED · Job 2 not started** | **SITE-A gated at G3 — waiting by design.** Deferral list unchanged: orphaned `forecast-validation.html` nav entry, `model-updates.html` → pointer, site-wide wide-table clipping |
| WS6 `BLOAT` | Prunes B-1..B-8 merged; **BLOAT-2 CLOSED**; **BLOAT-3 ADJUDICATED and EXECUTED** (BLOAT-S2, −444.5 MiB at tip). **The chartered work stays completed** | **Completed (charter) · gate 🔴 RED** | **🔴 RED at this pin** (`exit 1`; **54 sidecars / 83 bundle dirs**, allowlist **26**) on exactly one dir, `caiso217_crosswalk`. **v12's green lasted one board and its stated fragility was correct** — the frozenset grew again **24 → 26** and the class-level carve-out **still does not exist** (B-8). **v12 predicted "it will re-red on the next NYISO A/B"; it re-redded on a CAISO registration debt instead — right mechanism, wrong ISO.** The red is an **accepted cost** of the owner's caiso-219-over-caiso-217 choice (C-6), **not a prune candidate** |
| — `GOLDEN-TIER-FIX` | **COMPLETED and independently verified** (#4014); first cron RED, **diagnosed + fixed same-day** (#4071), deliverables verified by full local four-step replay | **Completed · tier PARKED** | **🅿️ PARKED BY OWNER RULING 2026-08-22, unchanged across both cycles.** CI proof **deliberately unspent**. **Consequence: byte-green cannot be CLAIMED for G2 while the tier is paused** |
| — `MATRIX GUARD` | rule 26 `[R-MECH-MATRIX]` CI enforcement | **🟢 GREEN at this pin, and the v12 WARN is CLEARED** | `check_mechanism_matrix.py` **exit 0**, re-run not quoted: integrity OK across the base file + **6 ISO shards**; anchors **191 field + 49 row + 154 path**, **0 unresolvable beyond the ratchet**; **keeper stamps match every `keepers/<ISO>.json`**; **and "§5.x prose headers match every `keepers/<ISO>.json`"** — the drift v12 flagged, **repaired by the ERCOT lane. Recorded as CLOSED so the next director does not re-report it** |

## Stage-0 golden staleness (RECOMPUTED at `99c8cf5` — never read from a table)

Re-derived at HEAD from `frontend/data/backcast/keepers/<ISO>.json` and
`results/regression-goldens/perfb-stage0/manifest.json` (`git_sha` **`af1ccb6`**,
`git_dirty: false`, **byte-unmoved across three cycles now** — `git diff` over
`results/regression-goldens/` returns empty across all 141 commits) — **not
copied from v12**, and each captured bundle mapped back to its keeper id through
the manifest's own `keeper_id` field rather than by name.

**🔴 THE CONSEQUENCE, STATED AS PLAINLY AS v11 AND v12 DID: BYTE-GREEN CANNOT BE
CLAIMED, so G2 leg 1 has TWO parked dependencies — WS3/PERF-B *and* the golden
tier — not one.**

**🔴 AND A NEW FACT ABOUT THE MANIFEST ITSELF, WHICH NO PRIOR BOARD RECORDED:
`af1ccb6` IS NOT A REACHABLE OBJECT.** `git cat-file -t af1ccb6` returns
*"Not a valid object name"* at this pin. The manifest's own provenance sha
therefore cannot be resolved, so **the goldens cannot be tied back to the tree
they were captured from** by anything stronger than the manifest's own content
hashes. Two readings, both worth carrying: this checkout is shallow (236
commits), so the object may exist upstream and simply be unfetched — **but the
history was force-rewritten on 2026-08-16 and the captures are dated 2026-08-14
to 2026-08-16**, squarely in the window where a pre-rewrite sha would have been
orphaned (`docs/FINDING-history-rewrite-2026-08-16.md`). **Whoever un-parks WS3
must resolve which it is before trusting the manifest's provenance field** — the
per-file `content_hashes` remain valid either way and are the thing to verify
against.

| ISO | Golden captured against | Designated keeper at `99c8cf5` | Verdict |
|-----|-------------------------|--------------------------------|---------|
| ERCOT | `2026-08-15-ercot204-rule26-delete` | `2026-08-24-231-tie-zone-measured` | **🔴 STALE — and the gap WIDENED this cycle** (223 → 231). v12 recorded four promotions past capture; this makes **five**. **And ERCOT is now doubly stale**: its keeper's *solved topology* also disagrees with HEAD after the card-Z code repair (C-2) |
| NEISO | `2026-08-14-neiso-93-envelope` | `2026-08-17-neiso-99-joint-p1` | **STALE — two promotions past capture** (unchanged). The re-stamp-not-re-solve shortcut was established for **neiso-97 only**; re-establish before relying on it |
| CAISO | `2026-08-16-caiso-197-w2-r5` | `2026-08-17-caiso-200-h1-memberpanel` | **STALE — one promotion past capture** (unchanged for a third cycle). Still the narrowest gap on the board |
| MISO | `2026-08-16-miso-160-wefor-shape` | `2026-08-22-miso-177-rho-measured` | **🔴 STALE — EIGHT promotions past capture**, one more this window (175 → 177) |
| NYISO | `2026-08-16-nyiso-140-layup-exclusion` | `2026-08-22-nyiso-152-duty-complete` | **🔴 STALE — EIGHT promotions past capture**, two more this window (149 → 151 → 152). **Tied with MISO for the worst gap on the board** |
| PJM | — | `2026-08-15-pjm-162-inputclock` | **NO GOLDEN — never captured**, and the keeper has now been **stable for FIVE cycles** |

**Count: 5 stale / 0 current / 1 no-golden — 0 of 6 effective coverage for a
FOURTH consecutive cycle**, against 4/1/1 at v8 and v9. **Recomputed at HEAD
against the live keeper shards, not read from v12's table** — the per-ISO
comparison was re-run from `manifest.json`'s `keeper_id` fields against
`keepers/<ISO>.json`, and it reproduces v12's verdicts with **one gap widened**
(ERCOT).

**🔴 THE STRUCTURAL POINT IS NOW A TREND, AND v12 CAN QUANTIFY IT.** Zero
coverage is in its third cycle and its **eighth** consecutive cycle of keepers
outrunning captures. What v12 adds:

- **The gap widened again — and this cycle it widened at ERCOT**, the one ISO
  that had held still through both v12 cycles. **Every ISO on the board has now
  outrun its capture at least once.** MISO and NYISO stay tied at **eight**
  promotions past capture; ERCOT moves to **five**.
- **PJM remains the cheapest capture and the largest gap, for the FIFTH
  consecutive board.** It has no golden at all, a keeper unmoved for five
  cycles, and the only clean scorecard on the board (8/8, zero caveats). **That
  combination has now gone untaken across five boards**, which is long enough to
  stop calling it an oversight and start calling it a decision nobody made.
- **🔴 NEW AT v13, AND IT RAISES THE COST OF WAITING: two ISOs' committed keeper
  bundles no longer reproduce at HEAD** — CAISO by unbisected source-tree drift
  (C-1 §5.2, nine `src/market_sim` commits intervening, `caiso-217`'s crosswalk
  intake the most likely candidate but **not asserted as the cause**) and ERCOT
  by the deliberate card-Z topology repair (C-2). **A golden re-capture taken
  today would therefore be capturing something different from what the keeper
  was scored on, for two of six ISOs.** That is not an argument against
  re-capturing — it is an argument that whoever un-parks WS3 must decide, per
  ISO, *which tree the golden is a golden OF.*
- **The golden-tier park still changes the arithmetic of the freeze, unchanged
  from v11 and worth repeating because the decision is still open:** a
  re-capture can be *taken* but its byte-green claim cannot be *certified*.
  **The freeze alone does not suffice.** Whoever declares it must decide the
  golden tier's disposition in the same act, or WS3 restarts into a gate it
  still cannot pass.
- **And now, additionally: the manifest's provenance sha does not resolve.** Add
  that to the restart checklist before any re-capture is trusted.

## Gates

- **G0** adopted ✓ (2026-08-13) · **G1** DECLARED ✓ (2026-08-16, #4006).
- **G2 — UNREACHABLE, and still behind TWO owner parks rather than one.** Leg 1
  is *PERF-B merged byte-green*; PERF-B is paused by owner decision **and** the
  golden tier that would certify byte-green is parked by owner ruling. No other
  leg substitutes. The legs:
  1. **PERF-B merged byte-green** — **doubly blocked, unchanged**: 5 of 6
     captured and **all 5 stale for a FOURTH cycle**, (c)/(d)/(e) merged, (a)/(b)
     unstarted, **and the golden tier is parked so byte-green cannot be claimed**
     even if captures were current. **Carried from v12: the manifest's own
     `git_sha` `af1ccb6` does not resolve at HEAD** — resolve that before
     trusting any re-capture's provenance. **New at v13: two ISOs' keeper
     bundles no longer reproduce at HEAD** (CAISO drift, ERCOT topology repair),
     so a re-capture now also requires deciding *which tree* it is a golden of.
  2. **One completed fast-tier-green `ci.yml` run** — **🟠 OBTAINABLE, BUT NO
     LONGER FREE.** v12 recorded this as the one G2 leg closeable today without
     an owner decision, because `mechanism-matrix-guard` had gone green. **The
     matrix guard is still green at this pin** (re-run, exit 0 — and its §5.x
     prose WARN is now CLEARED too). **But `check_registry_payload_parity.py` is
     RED again** on `caiso217_crosswalk`, and per C-6 that red is the **accepted
     cost of an owner decision to prioritise the caiso-219 lane**, not an
     unserved defect. **So this leg now needs either the one-replay registration
     (owner queue) or an explicit `KEEP_REQUIRED_UNMAPPED_BUNDLES` entry** — it
     is no longer decision-free.
  3. **A keeper freeze** — **owner call, outstanding across TWELVE director
     cycles, and DEFERRED BY OWNER DIRECTION rather than unanswered.** One
     promotion landed this cycle (ERCOT), and **an owner-signed structural repair
     is mid-execution with its rule-16 re-solve still owed** (C-2) — a promotion
     in flight, not a quiet window. **Do not read the five unmoved ISOs as a
     freeze arriving on its own.**
  4. **Branch-protection flip** — owner action, memo ready.

  On declaration the PM notifies the FFR desk (Q.2 battery).
- **G3** — unchanged: after G2, **DOCS-B** + the **BLOAT leg**. BLOAT's verdict
  and its chartered execution are satisfied (#4031 + #4047); **its parity gate is
  🔴 RED AGAIN at this pin — v12's green lasted exactly one board.** It was green
  by **allowlist growth** (now **24 → 26** entries) rather than by the
  class-level carve-out the 2026-08-20 finding recommended, which **still does
  not exist** (B-8, unrepaired). v12 called this leg *satisfied-but-fragile*;
  **the fragility was correctly called and has now been demonstrated**, so read
  it as **satisfied-in-charter but gate-red in fact**, with the red an accepted
  cost (C-6) rather than a defect to chase. The golden-tier proof
  leg is satisfied by #4014 + the green dispatch **as evidence**, though the tier
  itself remains parked.
- **G4** — unchanged: SITE-A + AUDIT-B. **WS5 Job 1 is not a G4 leg** — it was
  deliberately scoped pre-G3 as factual repair.

## Watch

- **🅿️ GOLDEN TIER — PARKED BY OWNER RULING 2026-08-22, unchanged for two
  cycles.** The #4071 fix is merged and locally replayed green; the CI proof is
  **deliberately unspent**. **Record it as a park, not a blocker** — and record
  the consequence too: **every byte-green claim remains unprovable**, and G2
  leg 1 is doubly parked.
- **🟢 CLOSED — BOTH v11 CI REDS.** `check_mechanism_matrix.py` exits 0
  (integrity OK, **0 unresolvable anchors beyond the ratchet** against v11's
  **239**, keeper stamps matching every shard, §5.x headers matching);
  `check_registry_payload_parity.py` exits 0 (53 runs / 76 bundle dirs / 0
  tolerated). **Both run at the pin, not quoted.** v11's protocol amendment
  *"RUN THE GATES, NEVER QUOTE THEM"* is what makes this line worth anything —
  and it cuts both ways: **the dispatch's assertion that parity was green was
  correct, and its standing-hazard warning was right to be there.**
- **🟠 THE PARITY GATE'S CLASSIFIER IS STILL UNFIXED, AND THE DEBT IS NOW
  MEASURABLE.** `KEEP_REQUIRED_UNMAPPED_BUNDLES` went **15 → 24 entries in cycle
  A**, 22 of 24 NYISO. The class-level carve-out the 2026-08-20 finding
  recommended *"so this list stops growing one arm at a time"* **still does not
  exist**. Green today; red on the next NYISO A/B. **~10 lines, and it retires a
  recurring red for good** (restart checklist step 9).
- **🟠 A STANDING HAZARD IN THE PARITY GATE ITSELF, CARRIED FROM THE DISPATCH
  AND WORTH KEEPING ON THE BOARD.** The gate reports a **LIVE lane's
  control/recipe dirs as "dead solve output"** — several are one-file
  `meta.json` replay **INPUTS**, committed before their arm solves by design.
  **Before reporting parity red, check whether the named dirs belong to a running
  lane.** A stray red usually self-clears when the A/B registers. **NEVER
  recommend pruning a dir a live lane owns** — that is the failure the allowlist
  exists to prevent, and it is why the allowlist keeps growing.
- **🔴 NEW — THE STAGE-0 MANIFEST'S PROVENANCE SHA DOES NOT RESOLVE.**
  `af1ccb6` is not a valid object at this pin. Either the shallow clone lacks it
  or the 2026-08-16 history rewrite orphaned it — the captures are dated
  2026-08-14 to 2026-08-16, inside the rewrite window. **The per-file
  `content_hashes` are unaffected and remain the verification instrument.**
  Resolve which before any re-capture is trusted.
- **🔴 NEW — FORECAST BOARD STALENESS IS *UNKNOWN*, AND UNKNOWN IS NOT FRESH.**
  `check_forecast_staleness.py` at the pin: newest scored sha **`8084b135`** is
  **not reachable in this checkout**, so distance from HEAD **cannot be
  measured**, across **8 distinct config cache epochs**. The script says it
  plainly — *"Staleness is UNKNOWN, which is not the same as fresh"* — and this
  board repeats it rather than rounding it to green. **Eight epochs means
  cross-run deltas on that board are being read across different config
  identities**; confirm that is intended before treating any of them as a model
  effect.
- **🟠 PUBLISHED STATE KEEPS DRIFTING FROM THE ARTIFACTS UNDERNEATH IT — THREE
  INDEPENDENT INSTANCES THIS WINDOW, AND THAT IS A PATTERN, NOT A COINCIDENCE.**
  (i) The ERCOT matrix stamp carried ercot-221's −39.4/0.723 against ercot-223's
  actual −39.7/0.729, **caught by a lane (ercot-230), not a gate**; (ii) the
  forecast gate board named **two keeper ids one promotion stale** (see the
  forecast-board section below), caught by this lane; (iii) cycle A's
  gate-refresh lane found
  **three latent board errors** of the same shape. **The common cause is that
  evidence PROSE is not gate-checked anywhere** — the matrix guard checks
  `keeper:` stamps and §5.x headers, and passes, while the citation text beside
  them goes stale. **Worth an explicit ruling on whether any gate should read
  evidence text**, or whether this is accepted as lane-maintained.
- **🟠 CARRIED, UNCHANGED, AND STILL THE CHEAPEST CORRECTNESS ITEM ON THE
  BOARD — the `holdout-freeze.json` prose conflict.** Verified still present at
  the pin: the file's own prose says intake is permitted *"under session-logged
  owner authorization"*, which the **2026-08-06 rule 22 `[R-HOLDOUT]` amendment
  reversed** (*what is held out is the SCORE, never the DATA or the
  ARCHITECTURE*). **Committed governance data disagreeing with the governing
  rule**, unmoved for four boards. It is a one-sentence edit in a governance
  lane.
- **🟠 #4054 / nyiso-140 null-treatment question — STILL OPEN, NEVER
  ADJUDICATED, and further out of reach again.** The NYISO keeper is now
  **eight promotions** past the captured nyiso-140 config. Any claim that
  re-checking it *"costs a fidelity read, not a solve"* must be **re-derived**,
  not inherited.
- **🟠 CARRIED — the cross-ISO scorer-change precedent, and its near-twin.** The
  nyiso-143 D-4 conduct rider reached MISO's committed diagnostics; separately, a
  shared benchmark re-render silently re-graded a committed determination. Both
  are **one lane's act re-grading another lane's committed record**, which is the
  shape rule 25 `[R-ISO-SCOPE]` exists to prevent. Unmoved.
- **DURABLE LESSON (unchanged, and the park makes it sharper):**
  `golden-data-tier.yml` is the **ONLY** workflow that runs
  `scripts/regenerate_clean.py`, so **any curation-time defect under
  `scripts/data/curate_*.py` has NO pre-merge signal** — invisible to every PR
  check, surfacing only on the weekly cron, compounded by `data/clean` being
  derived and gitignored. **With the tier parked that blind spot is permanent
  until it is un-parked. Treat curate-script changes as unguarded.**
- **🟢 NEW DURABLE LESSON — A NEGATIVE RESULT WITH A BITWISE PROOF IS WORTH MORE
  THAN A POSITIVE ONE WITHOUT.** ercot-230 did not merely fail to improve the
  keeper; it proved the keeper **regenerates its own floor bitwise** (sha
  `44f664bd` both sides, `d_price_at_miss` 0.0, all seven sidecars identical),
  which converts *"one pass is a convention"* into *"one pass is exact"* and
  closes a named successor permanently. **miso-179 is the same lesson at the
  other end of the cost curve** — an `R` verdict minted from frozen thresholds
  with **no field created and no LP spent**. **Both are cheaper and more durable
  than an arm that moves a residual.** When a lane proposes a lever, ask what its
  refutation would cost first.

## Forecast board — gate (a) re-derived at `99c8cf5`: 🟢 THE v12 STALENESS IS CLEARED

**Re-derived, not carried.** Every `gate.a_keeper_marker.detail` in the committed
seed `frontend/data/forecast/program-status.json` was compared field-by-field
against the live `keepers/<ISO>.json`. **All six now name the live keeper**,
including **ERCOT `2026-08-24-231-tie-zone-measured`** — re-stamped by the
capx-D1 board refresh (2026-08-24), a **different program's** lane. **The v12
stale-seed condition below is CLOSED; it is retained as the record of how it was
diagnosed, not as a live defect.**

**🔵 AND A RECORDS-LANE SAFETY CHECK, RUN BECAUSE v12's OWN GATE-(a) RE-KEY WIPED
39 PROVENANCE STAMPS AND ONLY A WARN NOTICED.** Every count this lane touched was
compared against v12's published figures **for direction**: verdicts stamped
**39 → 40**, hindcast sidecars **8 → 9**, stamped/scored **48/16 → 50/18**,
registered sidecars **53 → 54**. **Every one went UP.** No count went down, so
nothing was silently destroyed. **Gate (b) and (c) remain UNSCORED.** Gate (a)
passers are still **PJM, NYISO, NEISO** — unchanged, and still exactly the
`complete` set.

### v12's diagnosis, retained as history — gate (a) keeper ids re-derived in that pass

**What was stale.** `frontend/data/forecast/program-status.json` — the
**committed seed** for the forecast §2.1b gate board — named
`2026-08-22-nyiso-151-identity-hr` and `2026-08-22-miso-175-hourkey` in its
`gate.a_keeper_marker.detail` fields. Both are **one promotion behind** the
designated keepers at HEAD (`nyiso-152-duty-complete`, `miso-177-rho-measured`).
The stamp was taken at `cb7aadf8408a` during cycle A, and both ISOs promoted
after it.

**🟢 THE GATE VERDICTS ARE UNAFFECTED, AND THAT SHOULD BE SAID PLAINLY RATHER
THAN LEFT TO IMPLICATION.** Gate (a)'s test is charter §2.1b(2)(a) — *a
designated full-span keeper AND an entry in the `complete` block* — and **both
sides of each promotion sit in the same determination class**:

| ISO | Seed named | Live keeper | Determination, both | `complete`? | Gate (a) |
|---|---|---|---|---|---|
| NYISO | `nyiso-151-identity-hr` | `nyiso-152-duty-complete` | **CALIBRATED** | yes | **pass — unchanged** |
| MISO | `miso-175-hourkey` | `miso-177-rho-measured` | **NOT-YET** | no | **fail — unchanged** |

**Nothing moved. No gate opened, no gate closed, no ISO changed tier.** The
three gate-(a) passers are still **PJM, NYISO, NEISO** — still exactly the
`complete` membership. Gates **(b) and (c) remain UNSCORED** and are untouched by
this edit; **no forecast run was solved or re-scored**, and the refreshed
provenance stamp deliberately keeps the field names that
`check_forecast_staleness.py` cannot read as evidence of a re-score.

**What this lane committed, and what it deliberately did not.**
`program-status.json` is the **committed seed**; `registry/`, `runs/`,
`manifest.js` and `program-status.js` in the forecast namespace are **GENERATED
and gitignored** — the Pages deploy is their single writer, and `--reindex`
regenerates them locally for the `file://` preview. **Only the seed is
committed here.** Per rule 15 `[R-DASHBOARD]`, the forecast namespace is
registered through `scripts/register_forecast_run.py` alone and **never** through
the backcast registry; the backcast CI gates stay blind to it (forecast plan
§7.5). **No backcast registry file, keeper shard, holdout file or `src/` file was
touched by this lane.**

## Owner queue at cycle end

Re-ordered and re-verified at **`99c8cf5`**. **One item retired this cycle
(NYISO frontier ratification, SIGNED), three retired as the dispatch instructed
(the ercot-231 keeper-candidate escalation — promoted; card Y — signed Y-C; card
Z — signed Z-A).** The remainder are carried with their cycle counts advanced.

**🔴 ONE ITEM IS NEW AND IT IS TIME-CRITICAL IN A WAY THE OTHERS ARE NOT:** the
**ercot-225 G-SPUR band-top gate card** has been **AWAITING SIGNATURE SINCE
2026-08-21** (four days, no RESOLUTION block in the card), Option A recommended,
**scorer-only — no solve, no re-bundle, no keeper change.** Card Z's own record
notes that **signing it BEFORE the Z-A re-solve's gates run makes that repair's
G-SPUR reading lidless from the start.** The Z-A re-solve is the very next thing
the ERCOT lane owes (C-2). **Read one further fact before signing: the card names
keeper `2026-08-20-ercot223-arm-eventrelease`, which has since been superseded
by ercot-231** — the card's substance is unaffected (it is a gate definition,
measured on every registered run) but its keeper reference is stale.

1. **🔴 WS3 RESTART / CALIBRATION FREEZE — DEFERRED BY OWNER DIRECTION, so G2
   stays parked BY CHOICE, NOT BY DRIFT.** The owner has directed that
   calibration continue on all six ISOs. **Record it that way**: the board is not
   waiting on an unanswered question here, it is executing an answered one. The
   standing v10/v11 recommendation — a **scoped, time-boxed** freeze, decided
   **together with** the golden tier's disposition — remains on the table for
   whenever the direction changes, and v12 adds one fact to it: **the manifest's
   provenance sha no longer resolves**, so a restart now carries a verification
   step it did not carry before.
2. **🟢 VALIDATION-FREEZE LIFT — SIGNED (A) 2026-08-26 AND EXECUTED; retire
   from the queue.** Owner ruling (program-director sitting 2026-08-26, card 6)
   took `AUDIT-FOLLOWUP-o5-o4-2026-08-18.md` §2.4 option (A) verbatim: the
   layup charter is **closed with cause** (its new §10 — the detector/seam
   question REMAINS OPEN and is carried explicitly), and `holdout-freeze.json`
   is **re-scoped, not lifted outright**: `active: true` with `scope.tiers =
   ["locked_test"]`, so 2020–2022 are spendable by `complete` ISOs under
   `--holdout-authorized` while **2019/H1-2026 stay frozen for every ISO** —
   verified behaviourally on all three rule-22 gates, 55/55 invocations.
   `final` untouched and still empty. Audit row O4 → RESOLVED. Record:
   `docs/FINDING-holdout-governance-2026-08-26.md`.
3. **🟠 NEISO `final` GRANT.** neiso-101 closed the **data half** of precondition
   #2 with zero tracked files modified; **its entire residual is the grant
   itself**. It also recommends dropping `bench/NEISO/2019` from the precondition
   list as a registration byproduct — accept or reject explicitly rather than
   leaving it on the list. Standing and re-verified this cycle: **no ISO has ever
   spent a locked-test year**, NEISO's one-shot is **NEVER GRANTED, not spent**
   (D-23), and 2019 is unsolvable at HEAD on the Pilgrim gap regardless — so the
   readiness answer stays **NOT YET on the merits**, which is a different
   question from the grant.
4. **🟢 O6 — LOCKED-TEST SCHEDULING — STANDING POLICY RECORDED 2026-08-26
   (owner ruling, card 7); retire from the queue as a decision, the one-shots
   stay unspent.** The precondition for any future `final` grant is now on
   record: an ISO becomes eligible to be *considered* only after its 2020–2022
   touchpoints have been run AND the loop has stopped surfacing repairs;
   eligibility is not a grant — `final` remains an owner act, per ISO, every
   time. No marker changed: `final` still holds only its `_note`, **no ISO has
   ever spent a locked-test year**, and the freeze (now tier-scoped, card 6)
   still refuses 2019/H1-2026 for every ISO. Prior pin re-verification (54
   sidecars, year histogram {2022: 2, 2023: 52, 2024: 52, 2025: 52}) stands.
   **Never let a lane spend one.** Record: CLAUDE.md rule 22 locked-test
   bullet; `rule-history.md` §4; `docs/FINDING-holdout-governance-2026-08-26.md`.
5. **🟠 O7 — ERCOT P0 bit-identity proof forfeited** (accept-and-document, or
   charter restoration). Unmoved two cycles.
6. **🟠 decision-1 ack** — warm-start closed-overtaken; **still unacked, now
   EIGHTEEN cycles**. A one-word ack retires it. It is the longest-standing item
   on the board and the cheapest, and it has now outlasted every other item that
   was open when it was raised.
7. **🔴 NEW AND UNSIGNED FOR FOUR DAYS — the ercot-225 G-SPUR BAND-TOP GATE
   CARD** (`results/calibration/DECISION-ercot225-gspur-bandtop-gate-2026-08-21.md`),
   **Option A recommended**, drafted 2026-08-21, **no RESOLUTION block recorded
   at this pin.** It is **scorer-only**: no verdict of any standing run changes
   under the revision, no LP, no re-bundle, and one recorded artifact-leg FAIL is
   exonerated. **The reason it is time-critical rather than merely old:** card
   Z's record notes that signing it **BEFORE** the Z-A re-solve's gates run makes
   that repair's G-SPUR reading **lidless from the start**, and the Z-A re-solve
   is the ERCOT lane's immediate next deliverable (C-2). **Signing after the
   re-solve means grading a new keeper on a gate revised in response to it.**
   Caveat for the signer: the card names the pre-ercot-231 keeper.
8. **🟠 CARRIED — rule on the cross-ISO scorer-change precedent** (nyiso-143 D-4
   rider + the shared-benchmark determination flip). Both are one lane's act
   re-grading another's committed record.
9. **🟢 CARRIED — the `holdout-freeze.json` prose conflict — CORRECTED
   2026-08-26 as part of the card-6 scope edit; retire from the queue.** The
   freeze file's `note` was rewritten for the tier-scoped lift and the
   offending sentence now states the amended rule 22 (intake needs NO
   authorization; the score is held out, never the data), with the old
   Option-2 wording preserved as a bracketed correction notice. Record:
   `docs/FINDING-holdout-governance-2026-08-26.md`.
10. **🟠 CARRIED — caiso NOT-YET determination.** The CAISO packet has **moved
    substantively this window for the first time in three cycles**: caiso-215
    localised C3a to the Path-15 south and **eliminated the entire mean-zero
    zonal lever class**, and caiso-216 replaced the old two-item packet with a
    concrete **crosswalk-intake + one-solve** ask whose 2023-safety is measured
    ex ante. Owner ruling 5 stands: **C3a must genuinely pass; NOT-YET is the
    honest fallback.**
11. **🔴 NEW — THE T1-H CAPACITY-ENTRY DEFECT IS AN OPEN PROGRAM ITEM WITH NO
    OWNER.** Two ISOs, two independent lanes, one mechanism: **step-5 economic
    storage entry never fires before the step-6 reserve-margin backstop**, which
    then backfills with generic CT and ratchets (A-7). The diagnostic lane
    launched at cycle B's refresh and is running. **It needs a charter and a
    home**, and the charter should carry the correction in A-7: **the wind leg is
    a SEPARATE defect** (ERCOT −97 %, CAISO +757 %, CAISO's being an RPS-ladder
    artifact with `rps_dual` pinned at the $50/MWh ACP escape price in every
    solved year). **Two defects, not one.**
12. **🟠 NEW — THE caiso-217 REGISTRATION DEBT, and it is a DECISION, not a
    defect.** `results/calibration/caiso217_crosswalk` is a **mid-solve
    checkpoint** (2023 hourly sidecars only) whose session ended before
    registering, and it is **the sole reason `check_registry_payload_parity.py`
    exits 1** at this pin. **Recommendation (a): authorize the one-replay
    registration.** **Read it as deprioritized rather than unserved:** the
    caiso-219 record shows the owner, on 2026-08-24, **chose the §F.3a
    strandedness lane over this replay**, so the red gate is that choice's
    accepted cost. **NEVER prune it** — pruning would destroy a real solve's
    only artifact to silence a gate. The alternative to (a), if the replay stays
    deprioritized, is an explicit `KEEP_REQUIRED_UNMAPPED_BUNDLES` entry
    recording *why it outlives its sidecar*, which is what the allowlist is for.
13. **RETIRED ACROSS THE v12 CYCLES:**
    - ~~**the `RHO_CLIP` 0.5-floor ruling**~~ — **CLOSED END TO END** (A-3):
      refuted on the primary record, deleted by owner ruling, re-solved by
      pre-registered A/B, promoted with **zero new DOF**. Rank 1 for six cycles.
    - ~~**merge `14ce4ce` to clear the matrix gate**~~ — **MERGED as #4210**;
      both CI gates green at this pin.
    - ~~**the golden-tier proof-of-fix `workflow_dispatch`**~~ — **PARKED BY
      OWNER RULING** (retired at v11 by decision, not evidence; consequence for
      G2 recorded above).
    - ~~**the benchmark-authority question**~~ — **CLOSED by nyiso-149.**
    - ~~**the five-ISO bench regeneration**~~ — **MOOT** (flag hard-gated
      `iso == "NYISO"`, defaults off).
    - *(Carried note, unchanged and still owed: the five-ISO bench item is still
      listed open in nyiso-148's own §11 item 2 — someone owes that finding a
      one-line amendment.)*
    - The **nyiso-148 2025 dear-gas level card** is **not retired** — no
      signature or decline is recorded for it in this window. Its same-day
      UPDATE block should be read before its numbers, since the keeper it names
      has since been superseded. *(The ercot-225 card was carried here at v12;
      **at v13 it is promoted to a numbered item, #7**, because the Z-A re-solve
      gives it a deadline it did not previously have.)*
14. **🟢 RETIRED THIS CYCLE (v13) — do not re-serve:**
    - ~~**NYISO frontier ratification**~~ — **SIGNED by the owner 2026-08-23**
      (*"Ratify NYISO."*), recorded in `keepers/NYISO.json` `frontier` (C-3).
      **It also unblocks the desk's own director session**, which v12 recorded
      as idle-blocked on exactly this.
    - ~~**the ercot-231 keeper-candidate escalation**~~ — **PROMOTED**;
      `2026-08-24-231-tie-zone-measured` is the designated ERCOT keeper.
    - ~~**card Y (ERCOT 2023 price-object closure)**~~ — **SIGNED Y-C**,
      in-session 2026-08-24.
    - ~~**card Z (NE_LOB identity repair)**~~ — **SIGNED Z-A**, full identity
      repair including the rule-16 three-year re-solve. **Retired as a
      DECISION, not as work** — the re-solve is still owed (C-2).

## Session roster

> **🟠 v13 STATES ITS OWN LIMIT RATHER THAN INHERITING v12's CLAIM.** This
> records lane is **not** the director desk and holds no session-listing
> authority of its own, so it did **not** re-run `list_sessions`. **The lane
> state below is derived from GIT, which is the stronger instrument for the one
> question that actually matters here** (did a dispatched prompt produce work?),
> and every row says which instrument produced it. **No row is trailer-rebuilt
> and no row is carried from v12 unverified.**

### Lane state at `99c8cf5`, derived from remote branch tips (`git ls-remote`)

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

### v12's roster, retained as history

**🟢 FOUR LANES ARE RUNNING RIGHT NOW, ALL LAUNCHED IN THE SAME ~90-SECOND
DISPATCH WAVE AT 18:39–18:41 UTC 2026-08-23** — the refresh that also launched
this records lane. **Two of them are the re-issues of the prompts cycle A
dropped** (B-9), and two are the successors cycle B's refutations earned.

| Lane | Session | Live state |
|------|---------|------------|
| **Records v12 (this lane)** | `session_015BToZSEkYyhY8KvL1JLf9o` | **🟢 WORKING** — branch `claude/director-records-v12-refresh-fvxh5f`. **The re-issue of the prompt cycle A dropped** |
| **T1-H entry-screen capacity defect** | `session_013evGnLhd62SfSKtGmDeYrX` | **🟢 WORKING** — *"Computing CAISO storage break-even"*, branch `claude/entry-screen-t1h-diagnostic-3g78qm`. **The other re-issue** — it owns owner-queue item 11 |
| **CAISO generator-hub membership crosswalk** | `session_017DueKD5o3avqoLaDEU3CTd` | **🟢 WORKING** — *"Explore ATL_PNODE_MAP hub pnode universe"*. **caiso-216's funding ask #1, funded and launched** |
| **MISO-180 anchored spread-only dispersion** | `session_01Pe3KKnSRAFuocfGvmmTT9y` | **🟢 WORKING** — **the miso-179 successor**, taking the D-2/D-3 fallback the `R` verdict routed it to |
| **ERCOT energy/tightness channel (ercot-231)** | `session_011s4TKMY2gspbuQSLbb1H3u` | **REVIEW_READY** — *"commit pushed (#4218); static-TTC control re-solve in flight"* |
| **Audit-program director desk** | `session_01QJjTHnABwshc24grHXTD8V` | **IDLE / BLOCKED** — *"awaiting NYISO frontier ratification (nyiso-154)"*. **Owner-queue item 7 is what unblocks it** |
| MISO across-unit offer dispersion | `session_01CTPLkQTPMvRhPtLooun6Qw` | COMPLETED — **miso-179**, #4216/#4219 |
| CAISO belly lever identification | `session_01SKbzhHoxgQyQrK5eNpzPZD` | COMPLETED — **caiso-216**, #4217 |
| ERCOT 2023 summer scarcity | `session_018v8HgRPKqgJZ1Pnqw1aRKk` | COMPLETED — **ercot-230**, #4212/#4213 |
| CAISO C3a zonal decomposition | `session_0113iGLzdp3cCoa8h8uQoASm` | COMPLETED — **caiso-215**, #4211 |
| MISO C3a-2025 underprice | `session_01UgmvCTxq8BLMvipfCFwX2e` | COMPLETED — **miso-178**, #4214 |
| ERCOT T1-H capacity hindcast | `session_01LBfxu7aEkDmsfkwuandBjj` | COMPLETED — #4209 (cycle A) |
| CAISO T1-H capacity hindcast | `session_01DdKUy1Evh45bCKkNMLbrja` | COMPLETED — #4207 (cycle A) |
| RHO_CLIP identification / forecast gates | `session_01TM83kV5Pv5cKUJBrjyt2wx` | COMPLETED — **miso-177 + the gate-(a) refresh**, #4203/#4204/#4206 |
| NYISO frontier status | `session_01HX7WJaLeSi18NRvvAE9SuY` | COMPLETED — **nyiso-151…154**, #4196/#4201/#4205/#4208 |
| Records v11 | `session_0139EsHUG9wpkrxu3o6sdVYa` | COMPLETED — **#4200**, the board this entry supersedes |

**Live remote branches** (complete set at this pin):

| Branch | ahead of `main` | Read |
|--------|---|------|
| `main` | — | tip `1b8ddac` (merge of #4219) |
| `claude/caiso-belly-lever-plan-7d6rwk` | **0** | merged (#4217), survives deletion |
| `claude/ercot-energy-tightness-channel-vm4w8k` | **0** | merged (#4218) |
| `claude/forecast-gate-refresh-mohs9e` | **0** | merged (#4204) |
| `claude/miso-offer-dispersion-yk0zsq` | **0** | merged (#4219) |

**ZERO unmerged branches and ZERO open PRs — and this time those two readings
agree**, which they did not at v11. Each `ahead=0` was checked individually with
`git merge-base --is-ancestor`, **not inferred from the branch listing**, because
v11's whole point was that neither instrument alone sees the program. **The four
running lanes above hold work that appears in NEITHER instrument** — they have no
branches pushed yet and no PRs open. **Read three instruments, every cycle:
`list_pull_requests`, `ls-remote`, and the session roster.**

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

**v13's protocol amendment — ONE, and it is the same lesson for the THIRD
consecutive board**, on top of v10's two, v11's three and v12's two:

- **🔴 THE DISPATCH-VS-LAUNCH CHECK FAILED A THIRD TIME, AND THE PATTERN IS NOW
  THE FINDING.** The sequence, re-derived from git rather than recalled:
  prompts 7 and 8 (2026-08-23) went unlaunched one cycle, then launched and
  merged (**#4239, #4237**); the two entry-signal prompts issued 2026-08-24
  **launched and merged** (**#4248, #4253** — one lane executed BOTH);
  **THIS board-refresh prompt was issued in the SAME batch and did NOT launch**,
  which is why the board sat at v12 for two more cycles. **v12 made the fix
  mechanical (*call `list_sessions` at the end of every refresh*) and it still
  failed** — so v13 records the sharper, cheaper check that actually catches it:
  **LOOK FOR THE BRANCH, NOT A PLAUSIBLE-SOUNDING COMMIT.** A records lane that
  ran leaves a **branch**. This cycle, `claude/capx-director-ledger` — **a
  DIFFERENT program's director ledger** — moved and merged. **A commit-list scan
  would have shown "director ledger updated" and passed the check.** Only asking
  *"is there a branch named for THIS board's prompt?"* separates them.
  **Corollary, stated because the confusion is now documented as causal:**
  `docs/handoffs/capx-director-ledger-2026-08.md` is **not** this program's
  ledger, and conflating the two is part of why the audit board went
  unrefreshed.

**v12's protocol amendments** — one new, one sharpened, on top of v10's two
(check the live roster before declaring a lane unlaunched; pin the read and say
so) and v11's three (run the gates; read both PR and branch state; read a
content-addressed identity before inferring):

- **🔴 NEW, AND IT IS THE LESSON OF THIS ENTRY — A REFRESH IS COMPLETE WHEN THE
  SESSIONS EXIST, NOT WHEN THE PROMPTS ARE WRITTEN.** v11 already carried the
  rule in words (*"a dispatch that is never launched leaves the board silently
  wrong — verify the landing before declaring a cycle done"*). **It was written
  and then not applied**: two prompts issued at the end of cycle A were never
  launched, and the board went **two cycles / 105 commits / 25 PRs** stale as a
  direct result (B-9). **The fix is mechanical, not exhortative: at the END of
  every refresh, call `list_sessions` again and confirm one running session per
  prompt issued.** A prompt with no session is not a dispatch; it is a draft.
  **A rule that has been stated twice and violated once is now a checklist
  item**, and it is step 0 of the next refresh.
- **🔴 SHARPENED — QUOTE NO CYCLE COUNT WITHOUT ITS BASE SHA.** The dispatch's
  cycle-A arithmetic (54 / 9) does not reproduce from **any** base this lane
  tried: `04605b7a` gives 75 / 16, `4e1a4bc` gives 47 / 10. This is not a
  scoring error — a count without a base is not a measurement at all, and it
  cost this lane real time to discover that no base reproduces it. **State the
  base sha in the same sentence as the count, in the dispatch and on the
  board.** Cycle B's figures reproduced exactly, which is what a properly-based
  count looks like.
- **🟢 CARRIED AND VINDICATED — RUN THE GATES, NEVER QUOTE THEM.** All three
  measurement scripts were executed at the pin. Two had flipped since v11 (both
  reds → green); one reports **UNKNOWN**, which this board prints as UNKNOWN
  rather than rounding to fresh. **The dispatch's own standing-hazard note on
  the parity gate was correct and is preserved on the board** (Watch) — a
  dispatch that hands the next lane a known false-positive pattern is doing the
  job right.
- **🟢 CARRIED — DO NOT TRUST ANY TABLE, INCLUDING THE DISPATCH'S.** Every
  keeper id, determination, grade summary, C3a figure, marker, allowlist count
  and branch state on this board was re-derived from committed bytes at
  `1b8ddac`. **Three dispatch figures did not survive that** (cycle-A commits,
  cycle-A PRs, and the joint framing of the wind leg in A-7); everything else
  did, including every figure the dispatch flagged for re-derivation.

**While the program is parked, the refresh cycle is not the live instrument it
was.** A park-period refresh should confirm only (a) whether the golden tier is
proven green **in CI** — **ANSWERED AND RETIRED at v11**, the tier is parked and
the proof will not be spent, so **do not re-run this leg**; (b) whether the owner
has ruled on anything in the queue — **it has moved this window**, RHO_CLIP
closed end to end and the matrix branch merged; and (c) whether the keeper freeze
has been called — **answered by direction rather than by silence this window:
calibration continues on all six ISOs, so G2 stays parked BY CHOICE.**

## RESTART CHECKLIST — for whoever un-parks the program

**Do these in order. Do not start at change (a).**

0. **🟠 `main` IS HALF-GREEN AT v13 — v12's step 0 IS AMENDED, NOT RETIRED.**
   Re-run at `99c8cf5`, not quoted: `check_mechanism_matrix.py` **exit 0**
   (and its §5.x prose WARN is now **cleared**), `check_forecast_staleness.py`
   **exit 0**, but **`check_registry_payload_parity.py` exits 1** on
   `caiso217_crosswalk`. **v12 predicted parity would re-red on the next NYISO
   A/B; it re-redded on a CAISO registration debt instead — right mechanism,
   wrong ISO.** **G2 leg 2 is therefore no longer decision-free** (owner queue
   #12 — authorize the one-replay registration, or add an explicit allowlist
   entry saying why the bundle outlives its sidecar). **Never prune it.**
   **Always re-run all three gates rather than reading this line.**
0b. **🔴 NEW AND LOAD-BEARING FOR EVERY STEP BELOW — TWO ISOs' COMMITTED KEEPER
   BUNDLES NO LONGER REPRODUCE AT HEAD.** **CAISO**: the registered bundle's
   `score.json` differs from a HEAD re-solve by **+68.4 / −49,190.1 /
   −44,077.4 t** CO2, proven by control arm to be **source-tree drift, not a
   flag** (C-1 §5.2); nine `src/market_sim` commits intervene and the cause is
   **not bisected**. **ERCOT**: the card-Z topology repair **merged without its
   rule-16 re-solve**, so HEAD's Northeast→North boundary is EASTEX at 2,300 MW
   while the designated keeper was solved on NE_LOB at 1,300 MW (C-2).
   **Consequence: any step that treats a committed keeper bundle as a
   reproduction baseline must re-solve first for these two ISOs.** ERCOT's
   *dispatch* was otherwise verified bit-reproducible at one thread, which is
   what makes the CAISO drift diagnosable rather than ambient.
1. **DECIDE THE GOLDEN TIER AND THE FREEZE TOGETHER** — the precondition, not a
   nicety, and two decisions that must be made as one. A freeze buys re-captured
   goldens; **a parked golden tier means those captures cannot be certified
   byte-green**, so a freeze alone leaves G2 leg 1 blocked. Un-parking costs one
   `workflow_dispatch` (billed minutes, which is why it was parked). **Do not
   wait for a cheap calibration window; there has not been one in eleven cycles.**
   Cycle B looked like one and was not — it promoted nothing and ended with four
   lanes running. Consider a **scoped, time-boxed** freeze. **Current owner
   direction is to continue calibration on all six ISOs**, so this step is
   deferred by choice, not blocked.
2. **🔴 NEW — RESOLVE THE STAGE-0 MANIFEST'S PROVENANCE SHA BEFORE TRUSTING ANY
   CAPTURE.** `results/regression-goldens/perfb-stage0/manifest.json` declares
   `git_sha: af1ccb6`, which **does not resolve at HEAD**. Determine whether the
   object is merely unfetched in a shallow clone or was orphaned by the
   2026-08-16 history rewrite (the captures are dated inside that window).
   **The per-file `content_hashes` are unaffected — verify against those.**
3. **Re-verify every stage-0 golden against the then-current keepers** before
   resuming any change. **Do not trust this board's staleness table** — re-read
   the keeper shards and the manifest at that HEAD and re-derive it, **mapping
   captured bundles back through the registry sidecars' `bundle` field** rather
   than by name. **At `1b8ddac` the answer is that all five captures are stale
   and PJM was never taken.**
4. **Assume every re-capture is a real solve.** The gaps are wider than at v11:
   **MISO eight** promotions past capture, **NYISO eight**, ERCOT four, NEISO
   two, CAISO one. The **re-stamp-not-re-solve** shortcut was established for
   **neiso-97 only** and NEISO has since moved to neiso-99 — **re-establish it
   before relying on it.** Apply the sidecar-comparison test per ISO before
   spending a solve, but **re-derive the config diff first.**
5. **Capture PJM FIRST.** No golden at all, a keeper unmoved for **four** cycles,
   and the only clean scorecard on the board (target grade 8/8, zero caveats,
   zero fails). Simultaneously the largest coverage gap and the cheapest capture
   — **untaken across four consecutive boards.**
6. **Do NOT re-do change (c).** It landed via #3964 and is byte-identical at
   HEAD. Verify the blob (`af34031c`) rather than re-porting it.
7. **Close the #4054 residual if you want belt-and-braces** — but **re-derive it,
   do not inherit it.** The NYISO keeper is now **eight promotions** past the
   captured nyiso-140 config.
8. **Then, and only then, resume changes (a)–(e)** — and re-read the G2 leg list,
   because *merged byte-green* is what the gate wants, not captures.
9. **Confirm the golden tier is green IN CI before claiming any byte-green
   result** — which requires un-parking it (step 1). A tier that cannot provision
   `data/clean` cannot prove byte-identity of anything, and a local replay is not
   the gate.
10. **🔴 FIX THE PARITY GATE'S CLASSIFIER, NOT ITS SYMPTOM — and note the debt is
    now measured.** `KEEP_REQUIRED_UNMAPPED_BUNDLES` grew **15 → 24 entries in a
    single cycle**, 22 of 24 NYISO, and stayed flat in cycle B **only because no
    lane solved anything**. The 2026-08-20 repair diagnosed the class correctly
    — pre-registered recipes and in-flight controls both legitimately precede any
    sidecar — and then **allowlisted dirs by name instead of building the
    class-level carve-out it recommended.** **Build the carve-out; ~10 lines, and
    it retires a recurring red for good.** Explicitly **not** a pre-merge check,
    which would penalise correct pre-registration. **Until then, the gate's green
    is a maintenance state, not a property.**
