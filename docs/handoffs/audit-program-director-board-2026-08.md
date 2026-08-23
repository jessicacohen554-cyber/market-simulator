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
> ### 🟡 THIS ENTRY COVERS TWO CYCLES, BECAUSE THE v12 LANE WAS DISPATCHED LAST CYCLE AND NEVER LAUNCHED
>
> The board sat at **v11** across **two full director cycles**. Everything below
> is written as **two clearly separated sub-entries** — **cycle A** (the
> promotion cycle) and **cycle B** (the identification cycle) — because they have
> genuinely different characters and collapsing them would hide both.
>
> ### 🟢 NEW AT v12 — **BOTH GATES THAT WERE RED AT v11 ARE GREEN**, and one of them is green for the wrong reason
>
> `check_mechanism_matrix.py` and `check_registry_payload_parity.py` both **exit
> 0** at this pin, run rather than quoted. But the parity green is **not** the
> fix v11 asked for: the `KEEP_REQUIRED_UNMAPPED_BUNDLES` allowlist grew
> **15 → 24 entries in cycle A** and the class-level carve-out the 2026-08-20
> finding recommended **still does not exist**. See change B-6.
>
> ### 🟢 AND: **RHO_CLIP IS CLOSED END TO END** — the owner queue's rank-1 item for six cycles, retired on evidence
>
> Refuted on MISO's primary record, deleted by owner ruling, re-solved by a
> pre-registered A/B, promoted as keeper **with zero new degrees of freedom**.
> This is what closing a governance item on evidence looks like, and it is the
> single best outcome of either cycle.
>
> ### 🔴 AND: A DIRECTOR PROCESS FAILURE, RECORDED PLAINLY
>
> **Two prompts issued at the end of cycle A — the ENTRY-SCREEN DIAGNOSTIC and
> DIRECTOR-RECORDS v12 — were never launched.** This is the exact failure the
> desk's own refresh protocol names as most likely, and it is why this board was
> two cycles stale. Both were re-issued at cycle B's refresh and **both are
> running now** (roster below). See change B-8.

> **STATUS: PARKED AT G1** — live rollup maintained by the program-director
> session, updated on each owner "refresh". Canonical program definition:
> `docs/model-audit-release-plan-2026-08.md` (its §8 ledger is the durable event
> record; this board is the at-a-glance state). Completion figures are the
> director's estimate against each workstream's full DoD (A+B halves).

**Snapshot (v12):** dispatch written against `1b8ddac`; **this records lane
re-derived every figure live on 2026-08-23 at ~18:50 UTC against `origin/main`,
pinned at `1b8ddac`** — which is reachable and is the tip (merge of #4219), so
for the first time in three boards the dispatch's stated base and the derived
pin **agree**. Nothing below is carried from the dispatch, from board v11, or
from any table, unverified.

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

## What moved — CYCLE A (`04605b7a..fc9f9ec`, "the promotion cycle")

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

## What moved — CYCLE B (`fc9f9ec..1b8ddac`, "the identification cycle")

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

## Keeper table (read from `frontend/data/backcast/keepers/<ISO>.json` and `status/<ISO>.js` at `1b8ddac`)

Determinations and grade summaries parsed live from the status shards. **C3a(RT)
is the load-weighted mean-LMP error against RT actuals, per year 2023 / 2024 /
2025** — printed for every ISO because it is the criterion three of the six fail
on, and printing it only for the failures hides how narrow the margins are.

| ISO | Designated keeper | Determination | Grade (scored/target/fails/ledgered) | C3a(RT) 2023 / 2024 / 2025 |
|-----|-------------------|---------------|---|---|
| ERCOT | `2026-08-20-ercot223-arm-eventrelease` | `NOT-YET` | 8 / 5 / **2** / 1 | **−39.7 % F** / +0.4 % / −7.6 % |
| CAISO | `2026-08-17-caiso-200-h1-memberpanel` | `NOT-YET` | 8 / 6 / **1** / 1 | +4.1 % / **+12.8 % F** / **+15.7 % F** |
| PJM | `2026-08-15-pjm-162-inputclock` | **`CALIBRATED`** | 8 / **8** / 0 / **0** | +6.2 % / −0.8 % / −7.7 % |
| NYISO | `2026-08-22-nyiso-152-duty-complete` | **`CALIBRATED`** | 8 / 7 / 0 / 1 | +5.3 % / −2.7 % / −8.1 % |
| NEISO | `2026-08-17-neiso-99-joint-p1` | **`CALIBRATED`** | 8 / 7 / 0 / 1 | +3.1 % / +5.7 % / +1.7 % |
| MISO | `2026-08-22-miso-177-rho-measured` | `NOT-YET` | 8 / 6 / **1** / 1 | +1.3 % / −4.1 % / **−11.75 % F** |

| ISO | Cycle A | Cycle B |
|-----|---------|---------|
| **ERCOT** | **UNMOVED.** ercot-227 F1/F1b/F3 probes + ercot-228 **F4 DATA-ABSENT** + ercot-229 F1b NSPIN held-depth arm. Fail set unchanged | **UNMOVED.** ercot-230 fixed-point **MEASURED-INERT** (B-1) + the stale matrix stamp repair (B-2); ercot-231 N1–N5 pre-committed, N1a built default-off (B-3). **Two cycles, seven sessions, no promotion** — and every one of them closed a named successor rather than leaving it open |
| **CAISO** | **UNMOVED.** caiso-213 rest continuation — the sixth consecutive, no solve, no probe, no LP | **UNMOVED, but OFF REST.** caiso-215 localised C3a to the **Path-15 north–south split** and killed the whole mean-zero zonal class (B-4); caiso-216 answered the lever class and filed a **two-item costed ask** (B-5), one of which is now running. **The lane rested until it had a question worth an LP** |
| **PJM** | **UNMOVED and untouched** — no PJM calibration lane ran | **UNMOVED and untouched.** **FOURTH consecutive cycle** — and PJM is the only ISO with **zero caveats and every criterion PASS** (target grade 8/8). It is simultaneously the **largest stage-0 coverage gap (never captured) and the cheapest capture on the board**, for the fourth board running |
| **NYISO** | **PROMOTED TWICE** → nyiso-151-identity-hr → **`2026-08-22-nyiso-152-duty-complete`** (`CALIBRATED`), on the prereg's own rule, no owner override. nyiso-153 **REJECTED-AS-ARMED**; nyiso-154 declares the **testable set EXHAUSTED** and recommends frontier ratification (A-6) | **UNMOVED and untouched.** The frontier ratification recommendation is **still unsigned** (owner queue 8), and the desk's own director session is idle-blocked on it |
| **NEISO** | **UNMOVED and untouched by calibration** | **UNMOVED and untouched.** Its entire residual remains the **`final` grant itself** |
| **MISO** | **PROMOTED** → **`2026-08-22-miso-177-rho-measured`**, the RHO_CLIP close-out (A-3), **zero new DOF (33/2)**. miso-176 minted `m2m_seam_entitlement_cap` **`G`** | **UNMOVED.** miso-178 anatomy — **82 % of the −11.75 % is an 88-hour tail** (B-6); miso-179 minted **`R` at its own no-LP pre-checks with no field created** (B-7). Successor MISO-180 running |

**Markers at `1b8ddac`, re-read live this cycle:** `complete` =
**{NEISO, NYISO, PJM}** · **`final` = EMPTY (`_note` only)** ·
**`holdout-freeze.json` `active: true`**, and the freeze outranks both marker
blocks. **All three files are byte-unmoved across cycle B.**

**NO ISO HAS EVER SPENT A LOCKED-TEST YEAR** — verified at the pin rather than
restated. Across all **53** registered sidecars the solve-year histogram is
**{2022: 2, 2023: 51, 2024: 51, 2025: 51}**; the only two out-of-training
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
and still exactly the forecast gate-(a) passer set** — three independent
instruments agreeing on the same three ISOs across four boards. **Every one of
the three NOT-YET determinations is C3a**, and in two of the three (CAISO, MISO)
C3a is the *only* failing criterion.

## Workstream rollup

**WS1–WS6 are byte-unmoved across BOTH cycles.** Verified rather than assumed:
across all 105 commits the only WS-owned files that changed are the v11 records
lane's own two (this board and the plan, at `0b9adc6` and `637affa`, both inside
cycle A), **no `.github/workflows/` file changed**, and **no
`results/regression-goldens/` file changed**. Percentages are unchanged from v11
by construction — nothing moved to re-estimate.

| WS | State | Completion | Blockers / next |
|----|-------|------------|-----------------|
| WS1 `AUDIT` | AUDIT-A **completed** (#3991). Rows **O8 CLOSED**, **O5 CLOSED**, **O4 re-measured and STILL OPEN** (owner card, recommendation (A)) | **In progress ~91 %** | **AUDIT-B gated at G3 — waiting by design.** Rows **O4, O6, O7** open, unmoved two cycles |
| WS2 `DEBUG` | **COMPLETED** — DEBUG-A ✓, DEBUG-B ✓, pjm-162 promoted, landing-verify green on merged main | **Completed** | none; no DEBUG-C continuation chartered |
| WS3 `PERF` | PERF-A ✓. **PERF-B PAUSED BY OWNER.** Stage-0: **5 of 6 ISOs captured**, **PJM never captured**. Changes (c)/(d)/(e) merged, (a)/(b) unstarted. **`results/regression-goldens/` byte-unmoved across both cycles** — verified by `git diff --name-status`, not assumed | **Paused ~74 %** | **Paused, not blocked — and blocked TWICE at G2.** **0 of 6 goldens match their keeper for a THIRD consecutive cycle**, and with the tier parked byte-green cannot be *claimed* even if captures were current |
| WS4 `DOCS` | DOCS-A **completed** (#3999 + #4005); DOCS-B held | **In progress ~60 %** | **DOCS-B gated at G2 — waiting by design** |
| WS5 `SITE` | **Job 1 (site factual repair, pre-G3) COMPLETE ACROSS BOTH PASSES** (#4120/#4121, #4187/#4191). Job 2 = **SITE-A**, not started | **Job 1 COMPLETED · Job 2 not started** | **SITE-A gated at G3 — waiting by design.** Deferral list unchanged: orphaned `forecast-validation.html` nav entry, `model-updates.html` → pointer, site-wide wide-table clipping |
| WS6 `BLOAT` | Prunes B-1..B-8 merged; **BLOAT-2 CLOSED**; **BLOAT-3 ADJUDICATED and EXECUTED** (BLOAT-S2, −444.5 MiB at tip). **The chartered work stays completed** | **Completed (charter) · gate GREEN** | **🟢 GREEN at this pin** (53 runs / 76 bundle dirs / 0 tolerated) — **but green by ALLOWLIST GROWTH, not by repair.** The frozenset went **15 → 24** in cycle A and the recommended class-level carve-out **still does not exist** (B-8). **It will re-red on the next NYISO A/B** |
| — `GOLDEN-TIER-FIX` | **COMPLETED and independently verified** (#4014); first cron RED, **diagnosed + fixed same-day** (#4071), deliverables verified by full local four-step replay | **Completed · tier PARKED** | **🅿️ PARKED BY OWNER RULING 2026-08-22, unchanged across both cycles.** CI proof **deliberately unspent**. **Consequence: byte-green cannot be CLAIMED for G2 while the tier is paused** |
| — `MATRIX GUARD` | rule 26 `[R-MECH-MATRIX]` CI enforcement | **🟢 GREEN at this pin** | `check_mechanism_matrix.py` **exit 0**: integrity OK, **0 unresolvable anchors beyond the ratchet** (v11 read **239**), **keeper stamps match every `keepers/<ISO>.json`**, §5.x prose headers match. The category typo merged as **#4210**; the 239-anchor defect is closed by a ratchet |

## Stage-0 golden staleness (recomputed at `1b8ddac`)

Re-derived at HEAD from `frontend/data/backcast/keepers/<ISO>.json` and
`results/regression-goldens/perfb-stage0/manifest.json` (`git_sha` **`af1ccb6`**,
`git_dirty: false`, **byte-unmoved across both cycles**) — **not copied from
v11**, and each captured bundle mapped back to its registered run id through the
registry sidecars' `bundle` field rather than by name.

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

| ISO | Golden captured against | Designated keeper at `1b8ddac` | Verdict |
|-----|-------------------------|--------------------------------|---------|
| ERCOT | `2026-08-15-ercot204-rule26-delete` | `2026-08-20-ercot223-arm-eventrelease` | **STALE — four promotions past capture** (unchanged; ERCOT promoted nothing in either cycle) |
| NEISO | `2026-08-14-neiso-93-envelope` | `2026-08-17-neiso-99-joint-p1` | **STALE — two promotions past capture** (unchanged). The re-stamp-not-re-solve shortcut was established for **neiso-97 only**; re-establish before relying on it |
| CAISO | `2026-08-16-caiso-197-w2-r5` | `2026-08-17-caiso-200-h1-memberpanel` | **STALE — one promotion past capture** (unchanged for a third cycle). Still the narrowest gap on the board |
| MISO | `2026-08-16-miso-160-wefor-shape` | `2026-08-22-miso-177-rho-measured` | **🔴 STALE — EIGHT promotions past capture**, one more this window (175 → 177) |
| NYISO | `2026-08-16-nyiso-140-layup-exclusion` | `2026-08-22-nyiso-152-duty-complete` | **🔴 STALE — EIGHT promotions past capture**, two more this window (149 → 151 → 152). **Tied with MISO for the worst gap on the board** |
| PJM | — | `2026-08-15-pjm-162-inputclock` | **NO GOLDEN — never captured**, and the keeper has now been **stable for FOUR cycles** |

**Count: 5 stale / 0 current / 1 no-golden — 0 of 6 effective coverage for a
THIRD consecutive cycle**, against 4/1/1 at v8 and v9.

**🔴 THE STRUCTURAL POINT IS NOW A TREND, AND v12 CAN QUANTIFY IT.** Zero
coverage is in its third cycle and its **eighth** consecutive cycle of keepers
outrunning captures. What v12 adds:

- **The gaps widened again, and the widening is concentrated.** MISO went from
  seven promotions past capture to **eight**; NYISO from six to **eight**. **All
  three of those promotion events landed in cycle A alone** — cycle B added none,
  because cycle B promoted nothing. **The board should not read cycle B's
  stability as a capture window opening:** every ISO that rested in cycle B has a
  successor lane running right now.
- **PJM remains the cheapest capture and the largest gap, for the fourth
  consecutive board.** It has no golden at all, a keeper unmoved for four
  cycles, and the only clean scorecard on the board (8/8, zero caveats). **That
  combination has now gone untaken across four boards**, which is long enough to
  stop calling it an oversight and start calling it a decision nobody made.
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
     captured and **all 5 stale for a third cycle**, (c)/(d)/(e) merged, (a)/(b)
     unstarted, **and the golden tier is parked so byte-green cannot be claimed**
     even if captures were current. **New at v12: the manifest's own `git_sha`
     `af1ccb6` does not resolve at HEAD** — resolve that before trusting any
     re-capture's provenance.
  2. **One completed fast-tier-green `ci.yml` run** — **🟢 THE BLOCKER v11
     RECORDED HERE IS GONE.** v11 warned that a green `ci.yml` was *"not
     obtainable at this pin until `14ce4ce` merges"*, because `main` failed
     `mechanism-matrix-guard`. **That branch merged as #4210 and both gates run
     green at this pin.** This leg is **obtainable now** — nothing structural
     stands between the program and satisfying it, which makes it the one G2 leg
     that could be closed today without an owner decision.
  3. **A keeper freeze** — **owner call, outstanding across ELEVEN director
     cycles.** Three promotion events landed in cycle A; cycle B promoted nothing
     but has **four lanes running at this read**, two of which will produce A/B
     arms. **Cycle B is not the quiet window** — it is the identification phase
     that precedes the next promotion wave, and reading it as a lull would repeat
     the error v11 corrected in the other direction.
  4. **Branch-protection flip** — owner action, memo ready.

  On declaration the PM notifies the FFR desk (Q.2 battery).
- **G3** — unchanged: after G2, **DOCS-B** + the **BLOAT leg**. BLOAT's verdict
  and its chartered execution are satisfied (#4031 + #4047); **its parity gate is
  GREEN at this pin for the first time in three boards** — but green by
  allowlist growth, not by the repair the finding recommended (B-8), so **treat
  this leg as satisfied-but-fragile** rather than closed. The golden-tier proof
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

## Forecast board — gate (a) keeper ids re-derived in this pass

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

Re-ordered and re-verified at `1b8ddac`. **Four items retired across the two
cycles**; the remainder are carried with their cycle counts advanced.

1. **🔴 WS3 RESTART / CALIBRATION FREEZE — DEFERRED BY OWNER DIRECTION, so G2
   stays parked BY CHOICE, NOT BY DRIFT.** The owner has directed that
   calibration continue on all six ISOs. **Record it that way**: the board is not
   waiting on an unanswered question here, it is executing an answered one. The
   standing v10/v11 recommendation — a **scoped, time-boxed** freeze, decided
   **together with** the golden tier's disposition — remains on the table for
   whenever the direction changes, and v12 adds one fact to it: **the manifest's
   provenance sha no longer resolves**, so a restart now carries a verification
   step it did not carry before.
2. **🔴 VALIDATION-FREEZE LIFT — the O4/O5 card, recommendation (A).**
   `AUDIT-FOLLOWUP-o5-o4-2026-08-18.md` §2.4: **close the charter with cause,
   lift the VALIDATION tier only, leave `final` EMPTY.** The detector question is
   closed on evidence; *"resolve the detector question"* is not among the
   choices. **Unmoved for a fourth cycle.** `holdout-freeze.json` is still
   `active: true` and outranks every marker.
3. **🟠 NEISO `final` GRANT.** neiso-101 closed the **data half** of precondition
   #2 with zero tracked files modified; **its entire residual is the grant
   itself**. It also recommends dropping `bench/NEISO/2019` from the precondition
   list as a registration byproduct — accept or reject explicitly rather than
   leaving it on the list. Standing and re-verified this cycle: **no ISO has ever
   spent a locked-test year**, NEISO's one-shot is **NEVER GRANTED, not spent**
   (D-23), and 2019 is unsolvable at HEAD on the Pilgrim gap regardless — so the
   readiness answer stays **NOT YET on the merits**, which is a different
   question from the grant.
4. **🟠 O6 — LOCKED-TEST SCHEDULING.** Re-verified exhaustively at this pin
   across all **53** registered sidecars (year histogram {2022: 2, 2023: 51,
   2024: 51, 2025: 51}). `complete` = {NEISO, NYISO, PJM}; `final` holds only its
   `_note`; the freeze is `active: true` and outranks both. **Never let a lane
   spend one**; scheduling is the owner's alone.
5. **🟠 O7 — ERCOT P0 bit-identity proof forfeited** (accept-and-document, or
   charter restoration). Unmoved two cycles.
6. **🟠 decision-1 ack** — warm-start closed-overtaken; **still unacked, now
   FIFTEEN cycles**. A one-word ack retires it. It is the longest-standing item
   on the board and the cheapest.
7. **🟢 NEW — NYISO FRONTIER RATIFICATION, per nyiso-154.** The lane declares the
   **testable set EXHAUSTED** on the merits and recommends ratification
   (`ASSESSMENT-nyiso154-frontier-2026-08-22.md`): keeper **CALIBRATED**,
   `audit_keepers` 0/0, independent keeper-auditor PASS, `complete` marker held
   and correctly keyed, `final` **not** proposed, holdout freeze ACTIVE and
   unspent. **The director desk's own session is idle-blocked on exactly this**
   (`session_01QJjTHnABwshc24grHXTD8V`, *"awaiting NYISO frontier ratification
   (nyiso-154)"*). **It is a signature, not an investigation.**
8. **🟠 CARRIED — rule on the cross-ISO scorer-change precedent** (nyiso-143 D-4
   rider + the shared-benchmark determination flip). Both are one lane's act
   re-grading another's committed record.
9. **🟠 CARRIED — the `holdout-freeze.json` prose conflict.** Verified still
   present. Committed governance data disagreeing with the governing rule.
   **Still the cheapest correctness item on the board.**
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
12. **RETIRED ACROSS THESE TWO CYCLES:**
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
    - The **ercot-225 G-SPUR band-top card** and the **nyiso-148 2025 dear-gas
      level card** (v11 items 3 and 4) are **not listed above and are not
      retired** — no signature or decline is recorded for either in this window.
      They are carried as **awaiting owner sign-off**, and the nyiso-148 card's
      same-day UPDATE block should be read before its numbers, since the keeper
      it names has since been superseded twice.

## Session roster

> **🟢 LIVE READ — the session-read deviation stays CLOSED for a FOURTH
> consecutive cycle.** `list_sessions(mine: true)` returned **30 rows,
> `has_more: true`**, at ~18:50 UTC 2026-08-23. **No row below is
> trailer-rebuilt.** Honest limit, unchanged in kind: the page is bounded, so
> lanes older than 2026-08-16 fall outside it — none of these two cycles' do.

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

0. **🟢 `main` IS GREEN — v11's step 0 IS RETIRED.** Both CI gates that blocked
   this checklist at v11 run **exit 0** at `1b8ddac`. **G2 leg 2 (one completed
   fast-tier-green `ci.yml` run) is obtainable now** and is the only G2 leg that
   needs no owner decision. **Re-run both gates before relying on this** — parity
   is green by allowlist growth and will re-red on the next NYISO A/B (step 9).
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
