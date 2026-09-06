# Scenario Readiness Desk — Ledger

Standing coordination ledger for the SCN track, implementing
`docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` ("the plan"). Maintained by the
desk session; one refresh = one commit = one small PR. The desk charters lanes and tracks
state — it never solves, never edits `src/market_sim/` or `scripts/`, and never charters
backcast-calibration work or anything on the capacity-expansion director's queue
(`docs/handoffs/capx-director-ledger-2026-08.md`), which it deconflicts with at every refresh.

**Charter date:** 2026-09-05 · **Last refresh:** 2026-09-06 (refresh #6, amendment 1) ·
**r#6 am.1 — RULING S5 SPLITS STAGE A IN TWO.** D-7 is ruled: **hold the policy half, run the
load half now.** Stage A is no longer one campaign. **STAGE A-LOAD** — `REF` /
`LOAD-HI` / `LOAD-HI-ORGANIC` across six ISOs, plus the pure-carbon T0 probes **below 2028** —
has **no `gas_cc_ccs` exposure at all** and proceeds as soon as SCN-WS4c lands. **STAGE A-POLICY**
— every CES case, every carbon case at or above `ccs_retrofit_available_year` (2028), `ALL-CLEAN`,
and the `VOL-*` cases when they exist — **HOLDS until the capx CCS emission-rate seam is
repaired**. The ruling buys the campaign's uncontaminated half now and spends no LP twice.
**Routed to the capx director as a priority signal**: their CCS repair now gates half of a
chartered campaign, which it did not before. **The desk issues nothing on this ruling** — A-LOAD's
own precondition (SCN-WS4c) is still in flight, so the sequencing is recorded and the lane is
issued the refresh WS-4c lands.
*(previous)* **r#6 (HEAD `ad45b0e4`):**
**r#6 (HEAD `ad45b0e4`):** **ALL FOUR RULING-RELEASED LANES LANDED IN ONE DAY — and SCN-WS2b
found a defect that SIGN-FLIPS the campaign's headline answer.** Landed: **SCN-WS1c** (ruling S2
executed — the federal price is now a floor under the state program, matrix re-stamped, full-suite
parity accounted, and a second copy of the replace assertion found by parity), **SCN-WS2b** (the
ERCOT + NEISO ladders re-proved at HEAD, the national clearing script, the ERCOT/NEISO cells
re-stamped), **SCN-LEVELS** (S3 executed, `CES-T80` made live, levels measured to be the levels
the lanes actually ran), **SCN-LOAD** (S4 executed — six published ISO load forecasts curated as
the `load-forecast` datatype, with an obtainability-measured scope note pushed first) ·
**THE FINDING THAT MATTERS MORE THAN ANY OF THEM: a CCS emission-rate seam defect that INVERTS
NEISO's headline CO2 answer.** Retrofitted `gas_cc_ccs` units are credited at 0.95 by the CES
while carrying an **uncaptured** `emission_rate` in the dispatch fleet — measured on one unit
across its own retrofit year, `fuel_type` flips ✓, `heat_rate` rises ×1.12 ✓, and `emission_rate`
stays **0.3745 → 0.3745** ✗; three writes in one block of `ccs.py`, two persist, one is
overwritten downstream. As scored, the CES premium **raises** NEISO 2030 CO2 by **+9.99 Mt**; with
the intended 90 % capture applied at fixed dispatch it **cuts** it by **−6.01 Mt**. **This is a
capx-track file and not the desk's to fix — routed** — but it bears directly on the owner's actual
question, so **card D-7 is presented**: does Stage A run before it is repaired? · **SCN-WS4c is IN
FLIGHT** (PRECOMMIT, a zero-LP phase 0, harness and the first T0 slim artifacts) · **SCN-WS1b has
produced nothing for two refreshes and SCN-WS3b has never appeared — status ASKED, neither graded
lost**, per the standing change this desk made at r#5 after getting exactly that call wrong ·
**the CI-red SCN-WS1c routed is already GREEN** — the capx track discharged it; verified, not
assumed.
*(previous)* **r#5, amendment 1:**
**r#5 am.1 — FOUR OWNER RULINGS, RECORDED VERBATIM AS S1–S4, AND EVERY ONE OF THEM UNBLOCKS A
LANE.** **S1 (D-3) = YES**, a voluntary clean-demand scenario axis is admissible as a declared,
forecast-only, publicly-anchored axis — the ffr-5b ruling is held to be about a *fitted driver*,
a different admissibility class. **D-3b is settled with it: in-LP hourly 24/7 stays DEFERRED** to
the isolated portfolio tool (the owner took the recommended option, not the hourly-too variant).
**S2 (D-1) = FLOOR**, `effective = max(RFF path(year), program trajectory(year))` on a program
ISO — with the measured consequence accepted, that the floor makes `policy_bundle="tight"` an
exact no-op on CAISO/NYISO/NEISO rather than an increase. **S3 (D-2) = the plan's §3.5 table as
the committed default**, which converts SCN-WS2a's labelled-illustrative CES target
{2026: current, 2035: 0.80, 2050: 1.00} / ACP $50 into a committed level **with no re-solve**,
because the lane built and probed against exactly it. **S4 (D-4) = FUND THE FULL DATATYPE** —
this OVERRIDES the desk's and the lane's recommendation to defer, and it is the largest scope of
the three options offered. **ISSUED ON THE RULINGS: SCN-WS1c** (the floor repair, i.e. the WS-1a
item 1 the card gate withheld), **SCN-WS3b** (the voluntary build), **SCN-LEVELS** (commit the
§3.5 levels), **SCN-LOAD** (the full six-source load-forecast intake) · **Stage A's critical path
is now: WS-1b + WS-2b + WS-4c landing, and WS-3b → WS-3c landing.** D-3 no longer blocks it; it
schedules it · still OPEN: **D-3c** (the voluntary eligible set — the memo's box 3, which WS-3b
builds against the memo's recommendation and flags), **D-6** (attribute netting), **D-5** (the
Stage-B grant, correctly held until Stage A's cost table exists).
*(previous)* **r#5 (HEAD `3dcf1b22`):** **THE WAVE-2 SET IS ESSENTIALLY IN. SCN-WS4c IS UNBLOCKED AND
ISSUED — the last lane before Stage A.** Landed since r#4: **SCN-WS2a COMPLETE** (the NEISO T0
target-row pair registered, FINDING, and the matrix row + one cell per shard as its last
commit — every item of its charter), **SCN-WS4b** (both named cases, the six per-ISO
pre-declared adequacy readings, the `backstop-built` column + test), **SCN-MX-R-r2** (the CI
diagnosis, the epoch entry, and a correction to this ledger). **SCN-WS1b and SCN-WS2b are IN
FLIGHT with PRECOMMITs pushed before their solves**, exactly as rule 29 requires ·
**TWO CORRECTIONS THE DESK OWES, BOTH AGAINST ITS OWN RECORD.** (1) **r#4 graded SCN-WS4b LOST
and "never launched". That was wrong in fact** — the lane launched between r#4 and r#5 on
`claude/scn-ws4b-load-hi-adequacy-jvv96t` and landed complete. The r#4 call followed the
charter's two-refresh threshold correctly, but the threshold mis-fired, and the honest record
is *launched late*, not *never launched*. (2) **The desk asserted across r#2, r#3 and r#4 that
`check_mechanism_matrix.py`'s duty-(c) half "did not fire" because it exited 0. It DID fire and
it DID fail** — SCN-MX-R-r2 found job `101393800190` printing both `::error … not registered`
lines and exiting 1 on PR #4870, which was **created and merged five seconds apart with seven
red checks**, the guard not being a required status. The desk's three exit-0 readings were the
checker's **validate-only mode**, which returns before the registration leg exists in the
control flow and was never a registration verdict. The real defect is a merge-protection gap
plus a blind spot for any shared, forecast-only or keeper-unarmed field · **Stage-B picture
has widened and is not this desk's to move: THREE ISOs now hold CALIBRATED keepers while absent
from `complete`** — NYISO (my r#4 routing landed → capx card C-19/Q51 + D70, **Q51 ruled HOLD
ONE REFRESH**), MISO (C-17/Q49, **declined**) and CAISO (C-18/Q50, **hold until caiso-253**).
`complete` still reads {ERCOT, NEISO, PJM} · **CLAUDE.md changed under us**: rule 1 now carries
an **authorized offer-curve price-tuning carve-out**, rule 13 its one exception, rule 29 gains
clause **(c) DELETE BEFORE MERGE**, and a **new rule 30 `[R-TOUCHPOINT-FOLD]`** exists — all
four are written into SCN-WS4c's charter.
*(previous)* **r#4 (HEAD `21deb4a7`):** **NOTHING NEW IS UNBLOCKED BY CODE — and the one real unblock this
refresh is GOVERNANCE, is not this desk's to take, and nobody has taken it.** NYISO promoted
`2026-09-06-nyiso-196-extract-basis` — **CALIBRATED, grade 7, zero fails, C3c the lone ledgered
caveat** — and the withdrawal block's own re-entry clause reads *"re-entry is a NEW explicit
owner declaration on a keeper scoring CALIBRATED."* **That condition is now MET and the marker
has NOT been re-declared**: `complete` still reads {ERCOT, NEISO, PJM}, so NYISO's §2.1b leg (a)
is still FAIL and Q45's lapsed premise is still lapsed — **on a technicality that a single owner
declaration clears.** Disclosed and routed to the capx director per charter §0.4; this desk
declares no marker · **SCN-WS4b and SCN-MX-R are LOST** — issued r#2, re-emitted r#3, still no
branch and no PR at r#4, which is the charter's two-refresh threshold → **relaunched verbatim
under `-r2` stems, recorded never-launched against interest, NOT graded as running** ·
**SCN-WS2a's PRECOMMIT and docs legs merged** (#4892) but the probe, the FINDING and the CES
matrix row are still owed — the lane has PRs so it is not lost, it is owed · SCN-WS1b and
SCN-WS2b launched by the owner; no branches yet, which is expected within a refresh · the desk's
own r#3 PR merged (#4888), so the ledger conflict is closed · §2.1b gate unchanged **today**:
**NEISO only** — and NYISO is one declaration away from being the second.
*(previous)* **r#3 (HEAD `ea273339`):** **BOTH r#2 FINDINGS WERE SELF-CORRECTED BY THE LANES THEMSELVES,
BEFORE ANY r#2 PROMPT WAS DISPATCHED** — SCN-WS0 landed items 5 and 6 plus the G-E4 rider
(`e8c7072d`, `79034547`, `47ba0610`) and SCN-WS1a minted the `carbon_price_path` +
`policy_bundle` rows with a cell in every shard (`717de664`) and scored its CAISO T0
(`a147362b`). **THREE OF THE FOUR r#2 CHARTERS ARE THEREFORE WITHDRAWN UNDISPATCHED**:
SCN-WS0-R (its whole scope landed), SCN-WS2a-R (**SCN-WS2a IS LIVE** — two unmerged commits
on its branch, the docs leg and a pushed PRECOMMIT, so dispatching -R would build a twin),
and SCN-MX-R's carbon half. **SCN-MX-R survives NARROWED** to the one thing still unowned:
why `check_mechanism_matrix.py` exited 0 on a PR that added two `ScenarioConfig` fields with
no row · **the desk's r#2 PR conflicted on the ledger and is resolved here by rebuild** —
this refresh is r#2's record plus r#3's, on top of `ea273339`, with SCN-WS0's own §3 edits
taken over the desk's (better sourced) · **WS-0's T0 returns the campaign's first substantive
result and it is a CARBON-LEAKAGE number**: $25/t cuts NEISO's modeled in-ISO CO2 −2.71 Mt
(−16.6 %) while the reported import line rises **+1.85 Mt on a single NYISO rung**, so
**about two thirds of the headline reduction leaves the scored basis** — and at a CT-realistic
0.53 t/MWh instead of the 0.428 disclosure default the net shrinks to ≈ −0.42 Mt. Every
campaign delta must now be read with the import line beside it, per ISO · **ISSUED: SCN-WS1b
and SCN-WS2b (both newly UNBLOCKED by WS-0 item 5), SCN-MX-R (narrowed); SCN-WS4b RE-EMITTED
verbatim** (issued r#2, no branch at r#3 — one refresh, so NOT graded lost; dispatch status
asked) · no card ruled: **D-1, D-2, D-3, D-4, D-6 and the new sub-boxes all still OPEN** ·
§2.1b gate unchanged, **NEISO only**; no Stage-B lane issuable, none issued.
*(previous)* **r#2 (HEAD `db8b6015`):** **ALL FIVE WAVE-1 LANES LAUNCHED AND LANDED WORK — three complete, two
CHECKPOINTS.** WS-1a delivered items 2–4 + the Phase-0 table + the D-1 memo and **STOPPED on its
card gate exactly as chartered** — and its Phase 0 **proves G-C1 with a number**: `policy_bundle
="tight"` is a carbon-price CUT of **$16–$102/t in every one of 25 years** on CAISO/NYISO/NEISO,
and under the recommended FLOOR the RFF mid path **never once exceeds** a program trajectory, so
the floor makes `tight` an exact **no-op** there rather than a fix — a new D-1 sub-question, not a
new answer · WS-4a **complete**: ERCOT was already fully populated (the plan's "only for PJM" line
was stale), MISO populated from the 2026 LTLF regional decomposition validated on the deck's own
published totals, NEISO `{}` re-confirmed, D-4 gap list presentable unedited · WS-3a **complete**
(and **launched twice** — two branches ran the same charter; the second merged as a cross-check
addendum, no divergence) · **WS-0 CHECKPOINT** (items 1–4 + PRECOMMIT landed; the `scenario`
registration kind and the paired T0 owed) · **WS-2a CHECKPOINT** (the row + two fields landed;
postures/probe/matrix/docs owed) · **GRADED AGAINST CLAIM, TWICE: no matrix row or cell exists for
`carbon_price_path`, `policy_bundle`, or `federal_ces_target_by_year`** — WS-1a's own scorecard
edit reads "stamped … minted at WS-1a" and it never committed to `docs/codebase-site/data/` at
all; WS-2a added two solve-affecting `ScenarioConfig` fields with no row, **and CI passed**, so
`check_mechanism_matrix.py`'s duty-(c) half did not catch them (routed, not fixed) · **ISSUED:
SCN-WS0-R, SCN-WS2a-R, SCN-MX-R, SCN-WS4b** · **cards D-1 and D-3 RE-PRESENTED on new evidence,
D-4 PRESENTED** (its gap list now exists); D-2 and D-6 stand presented, unmoved · no card has been
ruled — **D-1, D-2, D-3, D-6 all still OPEN** · §2.1b gate unchanged: **NEISO only**; no Stage-B
lane issuable, none issued · capx r#41 deconflicted: D62/D65 issued, D60-R2 status ASKED not
graded lost, none holds an SCN file.
*(previous)* **r#1 (HEAD `d01ab8b0`):** the desk opens. Ledger created; plan read whole; capx r#40 read for
deconfliction (**D60-R2 RUNNING**, D61/D64 issued-unlaunched, D58 released-pending-D60, D63
queued — none holds a wave-1 SCN file, but D60-R2 and the owner's backcast lanes append to the
six matrix shards continuously, so the last-commit one-line shard protocol is MANDATORY, not
advisory) · **WAVE 1 ISSUED IN FULL — SCN-WS0, WS-1a, WS-2a, WS-3a, WS-4a** (five disjoint-file
lanes, no owner ruling required to start any of them) · **cards D-1, D-2, D-3, D-6 PRESENTED**;
D-4 held for WS-4a's gap list, D-5 held for Stage A's measured cost table · **§2.1b gate read at
the pin: NEISO ONLY** — NYISO's `complete` was withdrawn again on 2026-09-05 (nyiso-193
executing the owner's nyiso-192 promotion ruling; Q5 uniform rule), so `complete` =
{ERCOT, NEISO, PJM} and Q45's premise has lapsed. No Stage-B lane is issuable at this refresh
and none is issued.

**Transport note (r#1):** this session's harness assigns the branch
`claude/scn-desk-charter-x9v4k4` and forbids pushing elsewhere, so this refresh lands there
rather than on the charter's nominal `claude/scn-desk-ledger`. Successor refreshes should use
`claude/scn-desk-ledger` unless their own harness says otherwise; the ledger file path is
unchanged and is what matters.

---

## 0. Refresh log (newest first)

### r#6 amendment 1 — 2026-09-06: ruling S5 on card D-7

**S5 (2026-09-06), verbatim in effect: HOLD THE POLICY HALF; RUN THE LOAD HALF NOW.** Stage A
splits along the one line the defect actually draws — whether a case moves `gas_cc_ccs`.

| | cases | CCS exposure | status |
|---|---|---|---|
| **STAGE A-LOAD** | `REF`, `LOAD-HI`, `LOAD-HI-ORGANIC` across six ISOs at T1-F 2026–2030; plus the pure-carbon **T0 2026** probes | **none** — the retrofit screen is inert below `ccs_retrofit_available_year` (2028) by construction, and a 2026-only T0 never reaches it | **RELEASED.** Issued the refresh SCN-WS4c lands (its probes are this half's T0 leg). |
| **STAGE A-POLICY** | every `CES-*` case, every carbon case at or above 2028 (`CARB-*` T1-F legs), `ALL-CLEAN`, and `VOL-*` / `CES-P20+VOL-HI` when they exist | **yes** — these are the cases whose CO2 number may be sign-wrong | **HELD** until the capx CCS emission-rate seam is repaired and a paired check confirms `emission_rate` follows the retrofit. |

**Why this is the cheap answer, stated so a successor does not re-litigate it.** The alternative
the desk offered — run everything now, re-solve the affected cases after the repair — spends the
LP twice on most of the policy half (six ISOs × the CES ladder + the 2028+ carbon legs), and the
alternative of holding *everything* would park the load half behind a defect it has no exposure
to. S5 takes the only split that costs neither.

**What the desk does with it, and what it does not.** Recorded here and in plan §6; **routed to
the capx director as a priority signal** — the CCS repair (D50/D60/D65 lane) now gates half of a
chartered campaign, which it did not before this refresh. The desk **issues nothing on this
ruling today**: Stage A-LOAD's precondition is SCN-WS4c, still in flight. When WS-4c lands, the
six `SCN-WS5A-LOAD-<ISO>` lanes and their synthesis are issuable **without a further card** —
S5 is the authorization for that half.

**One scope note recorded against interest.** The `VOL-*` cases are placed in A-POLICY, not
A-LOAD, even though the voluntary row's default eligible set is renewable-only and does not credit
CCS. The reason is that a voluntary attribute row still *displaces thermal*, and in a 2026–2030
window NEISO's CCS fleet exists from 2028 — so a `VOL-*` leg can move `gas_cc_ccs` indirectly. It
is moot for sequencing today (SCN-WS3b has not started), but the placement is deliberate rather
than inherited.

---

### r#6 — 2026-09-06, main HEAD `ad45b0e454022e55ac76d1e03e0e6c207ae86be2`

*(PR #4970.)* Delta from the r#5 pin `3dcf1b22`: **113 commits**. The four lanes released by
rulings S1–S4 were issued and, for three of the four, launched and landed inside a single day.

**GRADED BY CONTENT:**

| lane | verdict | evidence |
|---|---|---|
| **SCN-WS1c** | The floor repair — plan §7 "WS-1a" item 1, released by S2 | **LANDED r#6** | `claude/scn-ws1c-carbon-floor-tmlmjl` (PRs #4956/#4961/#4967) | **Fable** | Ruling S2 executed. PRECOMMIT predicted the repair before the code; a **second copy of the replace assertion** was found by the parity sweep; full suite accounted to baseline (264−20=244); matrix re-stamped. Routed a CI-red it had not caused rather than reaching into another track's file — **now green** (§0 r#6). |
| **SCN-WS2b** | Premium-ladder re-prove at HEAD posture + `scripts/ces_national_clearing.py` | **LANDED r#6 — the session's most consequential lane** | `claude/scn-ws2b-ces-clearing-y40sks` (PRs #4909/#4963-adj) | **Opus** | All six ladder legs solve and register; the clearing script closes the G-S2 bracket for one cell (NEISO 2026, 0.00 pp, and honest about *why*); ERCOT saturates \$20–\$40 on `iso_budget_exhausted`. **Found the CCS emission-rate seam that sign-flips NEISO's headline CO2 (+9.99 → −6.01 Mt)** and routed it rather than fixing another track's file. |
| **SCN-LEVELS** | Commit the §3.5 campaign levels, released by S3 | **LANDED r#6** | `claude/scn-levels-*` | **Fable** | S3 executed: levels committed, `CES-T80` made live, docstrings de-illustrated. Its FINDING **measures** rather than asserts that the committed levels are the levels the lanes ran. |
| **SCN-LOAD** | The full six-source `load-forecast` curated datatype, released by S4 | **LANDED r#6** | `claude/scn-load-forecast-intake-t17qxj` (PR #4970) | **Opus** | S4 executed. Scope note pushed first with **obtainability measured per source**, so the closure is scored against a prediction; the six published forecasts curated as the datatype. |
| **SCN-WS4c** | Six T0 LOAD-HI probes + NEISO/ERCOT T1-F, scored against WS-4b's pre-declared readings | **IN FLIGHT r#6** | `claude/scn-ws4c-load-hi-probes-o85iyi` | **Opus** | PRECOMMIT + a **zero-LP phase 0** confirming WS-4b's arithmetic is HEAD's (rule 29 step 0 working) + harness + the first T0 slim artifacts. Owed: the rest of the battery, the two T1-F legs, the HIT/MISS scoring, the FINDING. |
| **SCN-WS1b** | Six-ISO carbon paired T0 probe + NEISO/ERCOT delta ladder + the per-ISO leakage line | **STALLED r#6 — status ASKED** | merged through `main` at r#5 | **Opus** | PRECOMMIT + instruments landed r#5; **nothing since, across two refreshes**. Holds merged PRs, so the relaunch protocol does not apply on its face. **Asked, not graded lost** — the r#5 correction exists because this desk got exactly that call wrong on SCN-WS4b. |
| **SCN-WS3b** | Voluntary-demand build, released by S1 | **NOT SEEN r#6 — status ASKED** | `claude/scn-ws3b-voluntary-demand-n5wq` | **Fable** | No branch, no commit, one refresh after issuance — inside the threshold. Asked. **It and SCN-WS3c are two of the three lanes between here and Stage A.** |

**THE HEADLINE FINDING, AND IT IS NOT A CES FINDING.** SCN-WS2b's re-prove existed to catch
exactly this class of thing, and it did. In NEISO the CES premium's **entire** response is
`gas_cc_ccs` (17.1 → 59.7 TWh at 2030), and **those retrofitted units are credited at 0.95 by the
CES while carrying an UNCAPTURED emission rate in the dispatch fleet.** Measured on a single unit
across its own retrofit year:

| field | before | after | verdict |
|---|---|---|---|
| `fuel_type` | `gas_cc` | `gas_cc_ccs` | ✓ |
| `heat_rate` | 7.5101 | 8.4113 (×1.12, the parasitic penalty) | ✓ |
| `emission_rate` | 0.3745 | **0.3745** | ✗ **unchanged to four decimals** |

Three writes in the same block of `ccs.py`; two persist, one is overwritten downstream. **The
consequence is a sign flip on the campaign's own headline metric:** as scored the premium *raises*
NEISO 2030 CO2 by **+9.99 Mt**; with the intended 90 % capture applied as an accounting
recomputation at fixed dispatch it *cuts* it by **−6.01 Mt**.
**Not this desk's to fix and not SCN-WS2b's** — `ccs.py`, `data/fleet/` and `runner.py` are all
outside that lane's regions and the CCS seam belongs to the capx D50 / D60 / D65 lane. **Routed
to the capx director** with the arithmetic attached (WS-2b FINDING §8). What the desk adds is the
scope statement the routing needs: **every campaign case that moves `gas_cc_ccs` has a CO2 number
that may be sign-wrong until this is repaired** — which is the CES cases, the carbon cases above
`ccs_retrofit_available_year` (2028), and `ALL-CLEAN`. That is most of Stage A's policy half, and
it is why **card D-7 is presented** rather than the desk quietly sequencing around it.

**A SECOND, OPPOSITE LEAKAGE RESULT — the campaign is now measuring something real.** WS-0
measured a $25/t carbon adder exporting two thirds of its NEISO CO2 reduction across the NYISO
seam. WS-2b measures the CES premium doing **the reverse**: `import_co2_mt_reported` **falls**
6.38 → 3.36 Mt at 2030 (−3.02 Mt) as 17.5 TWh of imports are repatriated. Two instruments, two
opposite signs, both measured — the import line WS-0 built is earning its place.

**OTHER SUBSTANTIVE RESULTS WORTH THE OWNER'S ATTENTION.**
- **The ERCOT ladder now SATURATES between \$20 and \$40**, because the binding constraint in
  every premium year is `iso_budget_exhausted`, **not economics**. Direction holds table by table
  against July; levels do not, and every level change is charged to a named flip or reported as
  unattributed — which is what item 1 was for. ERCOT's BAU commissioned VRE collapses
  **14 GW → 0.65 GW** and its CES-40 build falls **37 GW → 24 GW** since July.
- **The G-S2 bracket CLOSES for one cell, and closes for an honest reason.** SCN-WS2a's target-row
  probe landed mid-session, so the uniform-share half existed after all: at NEISO 2026 both
  representations read **0.3447**, gap **0.00 pp** — and they agree **because neither moves
  anything** (the premium is dispatch-inert there; the 0.55 target row escapes at its ACP). The
  cross-ISO spread under a uniform price grows **8.7 pp (2026) → 35.2 pp (2030)**.

**THE ROUTED CI-RED IS ALREADY GREEN — verified, not assumed.** SCN-WS1c routed a rule-28(c)
breach on pristine `main`: `capacity_going_forward_bar_published_by_iso`, a shared field landed
with the capx D60-R3 merge, had no matrix row and no ratchet entry, turning `mechanism-matrix-guard`
red on every open PR. The lane correctly refused to fix another track's cell (rule 28(d)) and
routed it. At this pin the desk re-ran `scripts/check_mechanism_matrix.py` on a clean checkout:
**exit 0, "absent-shared ratchet OK".** The capx track discharged it. Closed, with the lane's
handling recorded as correct: it reported a red gate it had not caused and did not reach into
another lane's file to clear its own PR.

**RULE CHANGES SINCE r#5 — three, and two bind SCN lanes directly.**
- **Rule 21 `[R-DOF]`** gains the R-AY cross-reference: an authorized `offer_curve_by_group`
  multiplier IS a ledgered free parameter, identified by the ruling rather than a measured source,
  and its presence does not by itself make the residual it closes an open root-cause issue.
- **Rule 22 `[R-HOLDOUT]` gains the R-AZ registration-time marker re-check** — the launch gate
  read the marker once, so a multi-hour solve could outlive its authorization;
  `dashboard_add_run.py` now re-asks at registration, **with no bypass flag**. Binds any SCN lane
  registering a run: a refused registration is not a registration.
- **Rule 30 `[R-TOUCHPOINT-FOLD]`** is now written out in full (stamp to the keeper, rebuild the
  status ladder, a held-out year never downgrades the ISO) plus rubric **v3.6** (on an
  out-of-training year C3c's lone-failure condition is dropped). No SCN lane touches a touchpoint.

**WHAT IS UNBLOCKED: nothing new, and the reason is worth stating.** SCN-WS3c still needs
SCN-WS3b, which has not started. Stage A still needs SCN-WS1b, SCN-WS4c and the WS-3b→WS-3c pair.
**The gate on Stage A is no longer a ruling — it is three lanes and one defect.**

**Issued:** nothing. **Cards:** **D-7 PRESENTED** (Stage A vs the CCS seam). D-3c and D-6 remain
open; D-5 remains correctly held.

---

### r#5 — 2026-09-06, main HEAD `3dcf1b220ed2cf2bbb62e38b4af3906510c83a5f`

*(PR #4921.)* Delta from the r#4 pin `21deb4a7`: **79 commits** — the largest since the desk
opened. SCN contributed fourteen; the rest is capx r#42 (+2 amendments), the audit program's
Y-15/Y-16/G-3 lanes, owner-track miso-221 / nyiso-197, and three CLAUDE.md rule changes.

**GRADED BY CONTENT:**

| lane | verdict | evidence |
|---|---|---|
| **SCN-WS2a** | The endogenous national CES **target** row (G-S1, G-S3) + the two new fields + the three state/federal postures | **LANDED r#5 — COMPLETE** | `claude/scn-ws2a-federal-ces-qm512t` (PRs #4870/#4892/#4902) | **Fable** | Every charter item in: the row on the clean-tier family, the coupling relaxation (WS-3b's precondition), two fields, the postures, the docs legs, the **NEISO T0 probe registered** (`c5f9358a`), the FINDING, and the matrix row + one cell per shard as its **last commit** (`d57cf785`). |
| **SCN-WS4b** | Pre-declared adequacy reading per ISO under LOAD-HI + the LOAD-HI / LOAD-HI-ORGANIC cases + the `backstop-built` column | **LANDED r#5** | `claude/scn-ws4b-load-hi-adequacy-jvv96t` (PR #4916) | **Fable** | **The r#4 LOST call is WITHDRAWN — launched late, not never launched** (§0 r#5 correction 1). Both cases declared, six per-ISO readings pre-declared in `load-hi-adequacy-reading-2026-09-06.md`, the column + its test. No solve by charter. **Unblocks SCN-WS4c.** |
| **SCN-MX-R-r2** | The rule-28 duty-(c) CI diagnosis; the verified-outstanding cache-epoch entry; the CES row conditionally | **LANDED r#5** | `claude/scn-mxr2-matrix-duty-repair-lk9ndd` (PR #4910) | **Fable** | Diagnosed the gap and **corrected the desk's own reading of it** (§0 r#5 correction 2); wrote the epoch entry; **left the CES row to live SCN-WS2a rather than racing it**, exactly as chartered — and WS-2a then landed it. |
| **SCN-WS1c** | The floor repair — plan §7 "WS-1a" **item 1**, released by ruling S2 | **ISSUED r#5 am.1** | `claude/scn-ws1c-carbon-floor-v2rk` | **Fable** | The item SCN-WS1a's card gate correctly withheld. Owns `policy/cap_and_trade.py`, the D34 guard, one `results/cache.py` epoch entry, the carbon tests. Byte-identity for every keeper and every zero-path forecast bundle is a deliverable. |
| **SCN-WS3b** | Voluntary-demand build, released by ruling S1 | **ISSUED r#5 am.1** | `claude/scn-ws3b-voluntary-demand-n5wq` | **Fable** | Builds the WS-3a memo's signed design: the annual volumetric row (D-3b deferred, so **no hourly block**), the DC-linked volume resolver, three fields, constants with citations, matrix row + six cells. **D-3c is still open** — builds the memo's recommended eligible set and flags it. |
| **SCN-LEVELS** | Commit the §3.5 campaign levels, released by ruling S3 | **ISSUED r#5 am.1** | `claude/scn-levels-d2-commit-c3jx` | **Fable** | Records lane, **zero solves and zero numeric change**: relabels SCN-WS2a's illustrative CES target / ACP as committed, writes the levels into the campaign YAML and the plan §3.5 table. Takes `configs/scenario_campaign_matrix.yaml` ownership from SCN-WS4b. |
| **SCN-LOAD** | The full six-source `load-forecast` curated datatype, released by ruling S4 | **ISSUED r#5 am.1** | `claude/scn-load-forecast-intake-w9tf` | **Opus** | **S4 overrode the desk's own recommendation to defer.** Uses the `data-intake` skill. The MISO driver-level 403 host wall is flagged at the gate. Closes G-D4-1..G-D4-4; G-D4-5 (`DEMAND_GROWTH_TRANSITION_YEAR`, no published source) stays a disclosed null. |
| **SCN-WS1b** | Six-ISO carbon paired T0 probe + NEISO/ERCOT delta ladder + the per-ISO leakage line | **IN FLIGHT r#5** | merged through `main` (`ed7fd527`, `acf5ed1f`, `e68e1971`) | **Opus** | PRECOMMIT pushed before any solve (rule 29 honoured); T0 scoring instrument, both leg launchers, registration helper and bundle gitignore in. **Owed: the twelve registrations, the ladder legs, the leakage table, the FINDING.** |
| **SCN-WS2b** | Premium-ladder re-prove at HEAD posture + `scripts/ces_national_clearing.py` | **IN FLIGHT r#5** | `claude/scn-ws2b-ces-clearing-y40sks` (live; PR #4909 merged item 2) | **Opus** | PRECOMMIT pushed before any solve; **item 2 landed — the uniform-price half of the G-S2 bracket**. Owed: item 1's ERCOT+NEISO ladder re-prove, the July table-by-table attribution, the FINDING. |

**CORRECTION 1 — the r#4 LOST call on SCN-WS4b was wrong in fact.** The charter's rule is *no
branch and no PR two refreshes after issuance ⇒ LOST*, and at the r#4 pin that was literally
true. The lane then launched on `claude/scn-ws4b-load-hi-adequacy-jvv96t` — a third name,
neither of the two stems the desk issued — and landed its whole charter. So "never launched"
is **withdrawn**; the record is **launched late**. What this says about the threshold: a
two-refresh window measured in hours is too tight when refreshes are hours apart rather than
days, and branch-name matching is a weak detector because the harness never uses the issued
stem. Standing change for r#6 onward: **before grading a lane LOST, ask dispatch status
first** and treat absence as evidence only alongside it. The relaunch cost nothing here (the
`-r2` charter was never dispatched either), but the grading was wrong and is recorded as such.

**CORRECTION 2 — the desk's CI-gap claim was wrong, and the truth is worse than the claim.**
Across r#2, r#3 and r#4 this ledger asserted that `check_mechanism_matrix.py` "exited 0", so
its duty-(c) half "did not fire", confirmed "across three pins". SCN-MX-R-r2 established
otherwise (`FINDING-scn-mxr-2026-09-06.md` §1.1):
- On PR #4870 the guard **ran and failed** — job `101393800190` prints both
  `::error … new ScenarioConfig field … is not registered` lines and exits 1.
- The PR was **created at 23:28:44Z and merged at 23:28:49Z** — five seconds — so the failure
  was reported to an already-merged PR. The guard is **not a merge-blocking required status**,
  and **seven of its eleven checks were red** (fast tests, refactor guards, quarantine gates,
  forecast parity, invariant audit, shrink-guard, this one).
- The desk's three exit-0 readings were the checker's **validate-only mode** (no `--base`),
  which returns at `if not args.base:` *before* the registration diff leg — it asserts store
  integrity and keeper-stamp parity and **never was a registration verdict**. Reading it as one
  was the desk's error.
- The durable hole it *does* have: **any shared (no ISO stem), forecast-only, or
  keeper-unarmed `ScenarioConfig` field that reaches `main` without its row is invisible to
  every later run** — `gap_ratchet` only walks ISO-stemmed fields and `shared_gap_ratchet` only
  sees fields armed on a backcast keeper, which a forecast-only field refused in backcast mode
  can never be. A `carbon_*`, `storage_*`, `ccs_*` or `entry_*` field would be swallowed the
  same way.
Routed by the lane to the capx/audit track, which owns the CI surface. **Not this desk's to
repair**, and the desk states plainly that its own three-pin "confirmation" was an artifact of
running the checker in the wrong mode.

**WHAT IS NOW UNBLOCKED — one lane, and it is the last one before Stage A.**
- **SCN-WS4c — UNBLOCKED, ISSUED.** Its three preconditions (WS-0, WS-4a, WS-4b) are all on
  main; WS-4b's own FINDING closes with *"This landing is the LAST thing blocking SCN-WS4c."*
- **SCN-WS3b** — still blocked on **card D-3 alone**, open since r#1. Both code preconditions
  have been met since r#3.
- **SCN-WS5A ×6 + SYNTH** — the gate is now: WS-1b and WS-2b landing, WS-4c landing, and
  **either D-3 ruled YES with WS-3b/c landed, or D-3 ruled NO** (in which case the `VOL-*` and
  `CES-P20+VOL-HI` cases drop from the campaign with a ledger note). **D-3 is on the critical
  path to Stage A now**, which it was not at r#1 — worth the owner knowing.
- **Stage B** — unchanged: needs card D-5 **and** an open §2.1b gate at issuance.

**THE STAGE-B PICTURE WIDENED, AND NONE OF IT IS THIS DESK'S TO MOVE.** Three ISOs now hold
CALIBRATED keepers while absent from `complete`, so their gate leg (a) reads FAIL:
| ISO | keeper | card | ruling |
|---|---|---|---|
| **NYISO** | `2026-09-06-nyiso-196-extract-basis` | C-19 / **Q51** — served by capx r#42 am.1 after **this desk's r#4 routing** | **HOLD ONE REFRESH** |
| **MISO** | promoted CALIBRATED (capx r#42) | C-17 / Q49 | **DECLINED** |
| **CAISO** | promoted CALIBRATED (capx r#42) | C-18 / Q50 | **HOLD until caiso-253** |
`complete` still reads {ERCOT, NEISO, PJM}. The desk records the state and the consequence — if
all three were declared, five of six ISOs would clear leg (a) and card D-5 would be a very
different question — and declares nothing.

**RULE CHANGES SINCE r#4, all four written into SCN-WS4c's charter.**
- **Rule 1 `[R-STRUCT]` amendment (owner, 2026-09-05):** the registered `offer_curve_by_group`
  band multipliers are an **authorized price-tuning channel**, under five binding conditions
  (band multipliers only; one config across every scored year; declared ex ante in the PREREG
  and **never swept against the gates**; merit-order movement is intended; declared in the
  attestation's `authorized_price_tuning` block and carried as a DOF free parameter). The first
  half of rule 1 is untouched.
- **Rule 13 `[R-MEASURED]`** carries the same exception, for the offer curve and nothing else.
- **Rule 29 gains clause (c) DELETE BEFORE MERGE** *(owner ruling R-AV)*: a screen bundle, and
  any control bundle a screen earns, **is deleted from `results/calibration/` before its PR
  merges** — the doc carries every number, and an unregistered bundle dir is a parity gate RED,
  not an allowlist candidate. Binds any SCN lane that produces a screen bundle.
- **New rule 30 `[R-TOUCHPOINT-FOLD]`:** a touchpoint publishes AS the keeper, not beside it.
  No current SCN lane touches a touchpoint; recorded so none assumes otherwise.

**Capx deconfliction (r#42 + two amendments).** **D60-R2 is DEAD** after four silent sittings →
**D60-R3 issued** with the D71 drift bisect folded in; **D65 Act A landed** and its own G-DRIFT
was wrong, surfacing material reproducible HEAD drift → D71; Q47 arm coupled after D60-R3 →
D65-B. No capx branch is live at this pin. The matrix tree now has SCN-WS2a's landed row plus
capx D65's — the last-commit one-line protocol held on both, with no conflict.

**Issued:** SCN-WS4c.
**Cards:** none newly ruled on the SCN side. **D-3 has moved onto Stage A's critical path.**

---

### r#4 — 2026-09-06, main HEAD `21deb4a75fd2d2c1d1b2c8ed4070968fe818313c`

*(PR #4894.)* Delta from the r#3 pin `ea273339`: **14 commits** — the desk's own r#3 (#4888,
merged), SCN-WS2a's two branch commits (#4892), wallclock A-2/A-6, and nyiso-196.

**THE ANSWER TO "WHAT ELSE IS UNBLOCKED": nothing, by code.** Checked against every queued
lane's actual precondition, not its label:

| lane | precondition | state at `21deb4a7` |
|---|---|---|
| **SCN-WS4c** | Six T0 LOAD-HI probes + NEISO/ERCOT T1-F, scored against WS-4b's pre-declared readings | **ISSUED r#5** | `claude/scn-ws4c-loadhi-probes-q8vd` | **Opus** | **UNBLOCKED** — WS-0, WS-4a and WS-4b all on main. The last lane before Stage A. |

| **SCN-WS5A** ×6 | the whole wave-2 set | blocked — WS-1b/WS-2b in flight, WS-2a owed, WS-4b/c not started |
| **Stage B** | card D-5 **and** an open §2.1b gate | not issuable; D-5 is held until Stage A's measured cost table exists, which is the correct order |

**THE ONE REAL UNBLOCK IS GOVERNANCE, AND IT IS NOT THIS DESK'S TO TAKE.** On 2026-09-06 the
owner-track lane nyiso-196 promoted `2026-09-06-nyiso-196-extract-basis` and it reads
**CALIBRATED — grade 7, fails 0, C3c the lone ledgered caveat**, on a rule 14 + rule 13 + rule 1
basis with zero free parameters and zero new DOF entries. NYISO's `withdrawn` block states its
own re-entry condition verbatim: *"re-entry is a NEW explicit owner declaration on a keeper
scoring CALIBRATED."* **The condition is satisfied. The declaration has not been made** —
`calibration-complete.json` `complete` still reads {ERCOT, NEISO, PJM} at this pin. Consequences,
stated because they are this desk's to track even though the act is not:
- FF §2.1b leg (a) for NYISO stays **FAIL** while the marker is absent, so no NYISO forecast
  campaign is authorizable, and **Q45's premise stays lapsed** — the capx director recorded at
  r#40 that no re-authorization card is served until a CALIBRATED NYISO keeper returns. **It has
  returned.**
- If and when the owner re-declares, NYISO becomes the **second** ISO whose Stage-B campaign is
  askable, behind NEISO — which changes what card D-5 should ask for when Stage A lands.
- **This desk declares nothing.** Markers, keepers and defaults are the owner's, and the backcast
  records lane is the capx director's queue (charter §0.4: disclose per case, never fix).
  **Routed to the capx director**; surfaced to the owner in this refresh's report. Recorded here
  so that if the marker is *deliberately* being withheld, the reason is asked for rather than
  assumed.

**LOST — two lanes, and the charter's own threshold decides it, not judgement.** SCN-WS4b and
SCN-MX-R were issued at r#2 and re-emitted/narrowed at r#3. At r#4 `git ls-remote origin
'refs/heads/claude/scn-*'` returns **nothing** for either, and no PR exists. That is **two
refreshes after issuance**, which is the charter's LOST threshold. Applying the relaunch protocol
exactly as written: **re-issued verbatim under fresh `-r2` stems, recorded "never launched"
against interest, and NOT re-graded as running.** The r#2/r#3 stems are burned. This is the
second time the desk has had to note the same asymmetry: the five r#1 lanes all launched within
hours, so a lane that shows no branch across two refreshes was almost certainly never dispatched
rather than silently failing.

**RE-GRADED — SCN-WS2a, the one lane still mid-charter.** Its two branch commits merged at #4892:
`73e5351f` (the `05-policy.md` + G-S6 docstring legs, item 6's doc half) and `6e6449ab` (the
NEISO T0 PRECOMMIT, `PRECOMMIT-scn-ws2a-2026-09-05.md`, pushed before the solve as rule 29
requires). **Still owed: the probe result, the postures tests, the FINDING, and the CES matrix
row** — `federal_ces_target_by_year` remains absent from `mechanism-matrix.js` at this pin
(verified: 0 occurrences), so the rule 28 duty-(c) gap SCN-MX-R was chartered to diagnose is now
confirmed across **three** pins. The lane holds merged PRs, so it is **owed, not lost**; the
relaunch protocol does not apply to it and SCN-WS2a-R stays withdrawn.

**Launched by the owner, not yet visible:** SCN-WS1b and SCN-WS2b. No branches at this pin, which
is normal inside one refresh — both were dispatched after r#3. They are graded RUNNING on the
owner's statement, and will be graded by content at r#5.

**Capx deconfliction.** No new capx lane since r#3; D65's branch is still live (`43b3a737`) and
touches no SCN region. The matrix tree has three pending SCN writers (WS-1b, WS-2b, live WS-2a)
plus capx — the last-commit one-line protocol stands unchanged.

**Issued:** SCN-WS4b-r2, SCN-MX-R-r2 (both verbatim relaunches).
**Cards:** none ruled; all open. **One new routing item, not a card:** the NYISO marker
re-declaration, which belongs to the owner and the capx director.

---

### r#3 — 2026-09-06, main HEAD `ea2733395077f15b365273032c8821f86b18b1fb`

*(PR #4891.)* Delta from the r#2 pin
`db8b6015`: **18 commits**, of which nine are SCN and the rest are capx D65 and owner-track
nyiso-196.

**WHY THIS REFRESH EXISTS: the desk's own r#2 PR would not merge.** `git merge-tree
origin/main HEAD` conflicted on `docs/handoffs/scenario-desk-ledger-2026-09.md` — SCN-WS0
edited the ledger's §1 row and §3 rows 6–7 on main while the desk's r#2 commit rewrote the
same sections. **Resolved by rebuild, per the charter's own instruction to recreate the branch
fresh off `origin/main` at every refresh:** this branch is `ea273339` + the r#2 content +
r#3, with **SCN-WS0's §3 edits taken over the desk's** wherever they overlap (the lane's
version is sourced to its own FINDING and is the better record) and the desk's structural
sections preserved. The plan file merged cleanly and its r#2 card-status and §9 blocks are
re-applied on top of main's SCN-WS0 additions. No content from either side was dropped.

**RE-GRADED BY CONTENT — the r#2 verdicts that moved:**

| lane | r#2 verdict | r#3 verdict | what changed |
|---|---|---|---|
| **SCN-WS0** | CHECKPOINT, 4 of 6 | **LANDED — all six items** | `e8c7072d` (5/6, the `scenario` registration kind grouped by campaign with a CO2 delta-vs-reference), `79034547` (6/6, the paired NEISO T0), `47ba0610` (**the G-E4 cap-row rider the desk was about to charter, closed by the lane itself**), `f6abf592` (slim artifacts). `FINDING-scn-ws0-2026-09-05.md` on main. Both arms registered under `scn-ws0-smoke`; 0 FAIL / 0 WARN on all 14 invariants per arm; 2.3 / 2.2 min, 3.31 / 2.94 GB. |
| **SCN-WS1a** | LANDED, **matrix duty NOT discharged** | **LANDED, duty DISCHARGED** | `717de664` mints the `carbon_price_path` and `policy_bundle` base rows plus a cell line in every shard — verified at the pin (2 rows present). `a147362b` scores the CAISO T0 pair against the precommit: every structural gate row passes. The r#2 finding was true at the r#2 pin and the lane repaired it on its own; recorded that way, not as a desk intervention. |
| **SCN-WS2a** | CHECKPOINT, items 1–2 | **CHECKPOINT — and LIVE** | Branch `claude/scn-ws2a-federal-ces-qm512t` carries two commits ahead of main: `73e5351f` (the 05-policy.md + G-S6 docstring legs) and `6e6449ab` (**the NEISO T0 PRECOMMIT, pushed before the solve**, exactly as rule 29 requires). The lane is working its owed items now. |
| **SCN-WS3a / SCN-WS4a** | LANDED | LANDED, unchanged | — |

**THE SUBSTANTIVE RESULT OF THE WEEK — carbon leakage, measured.** SCN-WS0's exercising T0 is
the first case run through the new emissions surface, and it is not a plumbing result. A
$25/tCO2 adder cuts NEISO's modeled in-ISO CO2 by **−2.71 Mt (−16.6 %)** and simultaneously
raises `import_co2_mt_reported` by **+1.85 Mt**, *all of it on one rung* — `NYISO_CT_peak`,
+4.32 TWh, while both firm Hydro-Québec seams barely move. On the scored `emissions_mt` basis
the case reads as a 16.6 % cut; with the disclosure line beside it the modeled net is nearer
**−0.85 Mt (−5.2 %)**. And 0.428 t/MWh is the CARB *unspecified* default for a seam with no
derived EF — at a gas-CT-realistic 0.53, which is what the rung is named for, the net shrinks
again to **≈ −0.42 Mt**. This is G-E3 (plan §2.5) measured on a real case for the first time.
Three consequences the desk carries forward, all now written into the lanes:
1. **Every campaign delta is read with the import line beside it, per ISO — never a generic
   sentence.** Folded into SCN-WS1b's charter as a deliverable, since it is the lane that runs
   all six ISOs.
2. **The NEISO seam EF is now a number with a magnitude attached, not a placeholder.** It
   attaches to card D-4 as a second, sharper instance of the same provenance question.
3. The lane also found and fixed, in the same commit, that **export sinks share the `import`
   fuel type and dispatch negative**, so the import CO2 line was differencing them against
   imports — an unearned offset, now clamped rather than netted. Inert on this T0; fixed
   before it was not.

**WITHDRAWALS — three r#2 charters, none dispatched, none re-issued.** The charter forbids
re-issuing a lane that already landed, and the capx twin-check doctrine forbids building a
twin of a live lane:
- **SCN-WS0-R — WITHDRAWN.** Its entire scope (items 5–6, rider A the G-E4 cap-row export,
  rider A the G-E4 cap-row export) is on main. **Rider B is the one exception and it is
  CHECKED, not assumed: `results/cache.py` has not changed since the r#2 pin**, so the
  cache-epoch entry SCN-WS4a routed — recording that MISO forecast bundles are stale at the
  same key after the DC-share change — is still outstanding. It is one ledger entry, not a
  lane: **re-assigned to SCN-MX-R**, whose scope is widened by exactly this one file, stated
  in its charter and here in §4.
- **SCN-WS2a-R — WITHDRAWN.** SCN-WS2a is live with a pushed PRECOMMIT. Dispatching -R now
  would be the twin the D60-R2 precedent exists to prevent. If SCN-WS2a goes silent for two
  refreshes, the relaunch protocol applies then — not now.
- **SCN-MX-R — NARROWED, not withdrawn.** Its carbon half is done. What survives is real and
  unowned: `federal_ces_target_by_year` and `federal_ces_acp_usd_per_mwh` are still absent
  from the matrix at this pin, **and `check_mechanism_matrix.py` still exits 0** — so the
  duty-(c) enforcement gap is confirmed across two pins, not a one-off. The CES row itself
  belongs to live SCN-WS2a (rule 28(b): the session that tests the mechanism stamps it), so
  MX-R diagnoses the gate and stamps the row **only if** WS-2a lands without it.

**NEWLY UNBLOCKED, ISSUED THIS REFRESH.** WS-0 item 5 was the single blocker on both:
- **SCN-WS1b** — the six-ISO carbon paired probe + the NEISO/ERCOT T1-F ladder. Card D-1 is
  still open, so it runs the **reduced form** its charter names (`--set carbon_price_delta=25`
  rather than `carbon_price_path=mid`), and says so in its PRECOMMIT.
- **SCN-WS2b** — the premium-ladder re-prove at HEAD posture + the national clearing script.
  Independent of SCN-WS2a and SCN-WS2a-R; it consumes committed legs, not the target row.

**SCN-WS4b — RE-EMITTED VERBATIM, not graded lost.** Issued at r#2; no branch and no PR at
r#3. That is **one** refresh, and the charter's LOST threshold is two. Every r#1 lane launched
within hours, so the practical read is that it was never dispatched — the capx relaunch
doctrine for exactly this case is *ask, re-emit verbatim, do not grade lost*, and that is what
this refresh does. If it is absent again at r#4 it is LOST and gets a `-r2` stem.

**Capx deconfliction (D65 landed since r#2).** `4b28c93f` — capx D65 minted its own
mechanism-matrix row and a `U` cell in all six shards, i.e. **the capx track is writing the
matrix tree right now**. The last-commit one-line protocol is load-bearing for every SCN lane
this refresh; SCN-MX-R in particular must rebase immediately before its single stamping
commit. D65's code scope (`capacity_evolution/ccs.py` and the CCS cost anchors) touches no SCN
region. D60-R2 still unreported.

**Issued:** SCN-WS1b, SCN-WS2b, SCN-MX-R (narrowed), SCN-WS4b (re-emitted).
**Cards:** none ruled; all open, unchanged from r#2 except that WS-0's leakage number attaches
to D-4 as a second instance.

---

### r#2 — 2026-09-05, main HEAD `db8b6015a1534873dac50ddda0dce9372d099305`

`db8b6015` = PR #4885. Delta from the r#1 pin `d01ab8b0`: **111 commits**, of which the SCN track
contributed five merged PRs (#4853 desk, #4856/#4860/#4867 WS-1a, #4857/#4859 WS-3a, #4863 WS-4a,
#4869 WS-0, #4870 WS-2a). The rest is owner-track backcast (caiso-252 → CAISO keeper CALIBRATED,
miso-220 → MISO keeper CALIBRATED, nyiso-195/196, NEISO/PJM touchpoints), capx r#41 + D61/D64, and
CI plumbing (Y-13/Y-14).

**Graded BY CONTENT — every wave-1 lane:**

| lane | verdict | what is on main | what is owed |
|---|---|---|---|
| **SCN-WS1a** | **LANDED (complete under its gate)** | Phase-0 trajectory table + machine-readable JSON/py/txt (`docs/handoffs/scn-ws1a/`), items 2+3 (G-C2 `spec.py` corridor adder off the resolver; G-C3 membership-weighted column at `assemble_mc`), item 4 pre-declared, `FINDING-scn-ws1a-2026-09-05.md` incl. the D-1 evidence memo §6 | **item 1 correctly NOT executed** (D-1 open — the gate worked). **Matrix duty NOT discharged** (§below). Its §4.3 routes the cap-row slack/dual export to WS-0 as a G-E4 rider. |
| **SCN-WS3a** | **LANDED** | `voluntary-clean-demand-design-memo-2026-09-05.md`, 8 sections + 5 owner boxes (D-3, new D-3b, new D-3c, the D-6 brief, the D-2 voluntary sub-levels) + Addendum A | nothing. **Launched twice** — `…-s8iukw` and `…-9f1you` both ran the charter; the second merged with an add/add resolution as a cross-check addendum and reports no divergence. Recorded, not a fault of either lane: the desk issued one stem and the harness provisioned two. |
| **SCN-WS4a** | **LANDED** | ERCOT verified already-populated since 2026-07-21 (plan §2.4's "only for PJM" line was **stale**, corrected in-lane); MISO shares from 2026 LTLF slide 21 validated on the deck's own totals (9.6 TWh 2026, 266 TWh 2046, ~58 % Central); NEISO `{}` re-confirmed against the 2026 CELT with the arithmetic written out; `FINDING-scn-ws4a-2026-09-05.md` §4 = the D-4 gap list | nothing in scope. Routes **one cache-epoch entry** (`results/cache.py`, WS-1a's region) it correctly refused to write. |
| **SCN-WS0** | **CHECKPOINT — 4 of 6 items** | (1/6) emissions grain, (2/6) matrix frame + `report_scenario_deltas.py`, (3/6) `collate_scenario_campaign.py`, (4/6) the six-ISO scenario YAML set + `configs/scenario_campaign_matrix.yaml` + the `--set` override, plus `PRECOMMIT-scn-ws0-t0-2026-09-05.md` | **item 5** (the `scenario` kind on `register_forecast_run.py` + the campaign grouping / delta sparkline — verified absent) and **item 6** (the paired NEISO T0 through the new tables, both arms registered under campaign `scn-ws0-smoke`). No `FINDING-scn-ws0`. |
| **SCN-WS2a** | **CHECKPOINT — items 1–2** | one commit: the federal CES target row on the clean-tier family, the `rows.py:1346` coupling relaxation (WS-3b's precondition, delivered), `federal_ces_target_by_year` + `federal_ces_acp_usd_per_mwh` with `__post_init__` guards and cache-key registration at `None` | **item 3** (the three postures documented + tested), **item 4** (the NEISO 2026 T0 probe — no PRECOMMIT, no registration), **item 6** (matrix), `docs/codebase/05-policy.md` + the `constraints.py` docstring (G-S6), no `FINDING-scn-ws2a`, scorecard row unmoved. |

**THE FINDING OF THIS REFRESH — two undischarged matrix duties, one of them claimed as done.**
Grep at the pin over `docs/codebase-site/data/mechanism-matrix.js` and all six shards:

- `carbon_price_path` — **0 rows, 0 cells** (one incidental prose mention inside an unrelated
  NYISO note). `policy_bundle` — **0 rows, 0 cells**. Yet the ledger §3 row-5 Carbon cell, edited
  by SCN-WS1a itself, reads *"stamped (`carbon_price_path` + `policy_bundle` rows minted at
  WS-1a)"*. `git log --grep=SCN-WS1a -- docs/codebase-site/data/` returns **nothing**: the lane
  never committed to that tree. The claim is corrected in §3 below **against the lane's own
  record**, which is what grading by content is for. Rule 28 duty (b) undischarged.
- `federal_ces_target_by_year` / `federal_ces_acp_usd_per_mwh` — two solve-affecting
  `ScenarioConfig` fields added by SCN-WS2a with **no base row and no cell in any shard**. Rule 28
  duty (c) says that row belongs in the same PR and CI enforces it — **yet
  `scripts/check_mechanism_matrix.py` exits 0 at the pin** (warnings only, all pre-existing anchor
  drift). So the CI half that is supposed to catch a new field without a row **did not fire**.
  That is a gate defect, not an SCN mechanism question, and `scripts/` is not this desk's to edit:
  **routed** to SCN-MX-R to diagnose and report, and to the capx/audit track to fix if the repair
  is in the checker.

**Branch-stem divergence, recorded so §5 reconciles.** Every lane was provisioned by the harness
on its own branch name rather than the stem the desk issued (`scn-ws0-k7m2-8743yi`,
`scn-ws1a-carbon-d1-eupbi5`, `scn-ws2a-federal-ces-qm512t`, `scn-ws3a-voluntary-demand-{s8iukw,
9f1you}`, `scn-ws4a-datacenter-shares-yf7wvi`). WS-4a's FINDING flags it explicitly. No collision
resulted; §5 now records both the issued stem and the realized branch, and future issuance treats
the stem as advisory.

**Graded by content — capx deconfliction (capx r#41, HEAD `5cc1e7ce`):** D61 and D64 **landed**
and each relocated its object (the PJM D57 price ratio is the going-forward bar + census, not the
E&AS operand; the CCS carbon-0 closure rests on an **uncited** `ccs_retrofit_vom_adder` 8.0,
2.7–3.6× every published basis) → **D62 and D65 ISSUED** (D65's branch is live). **D60-R2: nothing
since #4824, status ASKED, not graded lost.** Files: D62/D65 are capacity-evolution and CCS
cost-leg lanes (`capacity_evolution/ccs.py`, `new_entry.py`, `constants.py`'s CCS anchors);
D60-R2 still holds `scripts/forecast_verdict.py` + `frontend/data/forecast/`. **No collision with
any r#2 SCN lane** — but note SCN-WS4b and SCN-MX-R both append to matrix shards, so the
last-commit protocol binds harder than ever (capx parity is RED on two unmapped bundles and the
owner's backcast track promoted two keepers today).

**Wave-2 unblocking, measured against the actual preconditions:**
- **SCN-WS1b** — BLOCKED. Its charter registers twelve arms; the `scenario` registration kind is
  WS-0 item 5 and is not on main.
- **SCN-WS2b** — BLOCKED, same reason (it registers ladder legs).
- **SCN-WS4b** — **UNBLOCKED and ISSUED.** Everything it consumes landed in WS-0 items 2 and 4
  (`report_scenario_deltas.py`, `configs/scenario_campaign_matrix.yaml`) and WS-4a; it registers
  nothing, so item 5 does not gate it. Campaign-YAML ownership **transfers to it** (§4).
- **SCN-WS4c** — BLOCKED on WS-4b.
- **SCN-WS3b** — BLOCKED on card D-3, still open. Its two code preconditions are now MET
  (WS-2a's coupling relaxation, WS-4a's DC module).

**Issued:** SCN-WS0-R, SCN-WS2a-R, SCN-MX-R, SCN-WS4b (§5).
**Cards:** D-1 and D-3 RE-PRESENTED on new evidence; D-4 PRESENTED; D-2, D-6 stand.

---

### r#1 — 2026-09-05, main HEAD `d01ab8b0ea5e3c6e1a68c86f8daad1b4b6d605e9`

`d01ab8b0` = PR #4840 (`claude/miso-219-evening-scarcity-qrliuv`), Sat 2026-09-05 15:25:45
−0700. The plan was surveyed at `4d4dc6ce`; the delta to the pin is owner-track backcast work
(miso-219 and predecessors) plus capx records lanes — **no file in any wave-1 SCN region moved**,
so every plan §2 file:line citation is used as written and each lane re-verifies its own anchors
at its branch point (each prompt says so).

**Read this refresh:** CLAUDE.md; the plan entire (§1 definition of done, §2 per-mechanism
state, §3 workstreams, §3.5 case set, §4 constraints, §5/§5.1 sequencing + scorecard, §6 owner
boxes, §7 prompts, §8 findings); FF plan §2.1b (window cap + four-leg gate), §2.4 (budget
anchors + the `data/clean` prerequisite), §7; capx ledger top block + §1 scoreboard;
`docs/mechanism-testing-matrix.md` §5 and the six shards.

**Graded by content — SCN lanes:** none exist. `git ls-remote origin 'refs/heads/claude/scn-*'`
returns empty; no `FINDING-scn-*` doc on main; plan §5.1 unmoved from v1. This is the first
refresh, so nothing is LOST and no relaunch protocol applies.

**Graded by content — capx deconfliction (from capx r#40, HEAD `4d4dc6ce`):**

| capx lane | status | files it holds | collision with wave 1? |
|---|---|---|---|
| **D60-R2** | RUNNING (PR #4824) | `scripts/forecast_verdict.py` (the `_dof_ledger_row` builder + six new (ISO, field) rows), `frontend/data/forecast/` board + verdict re-scores, the finding | **NO** on `src/`; **SHARD-ADJACENT** — its re-scores can append to matrix shards. Mitigated by the last-commit protocol. |
| **D61** | ISSUED, unlaunched | docs only (PJM E&AS operand Phase 0) | no |
| **D64** | ISSUED r#40, unlaunched | docs only (CCS ΔFOM / capture VOM Phase 0) | no |
| **D58** | RELEASED, dispatch after D60 lands | `frontend/data/forecast/` PJM board t1f row; solves | **NO** on `src/`; WS-0 must not touch `program-status.json`. |
| **D63** | queued-named | MISO/CAISO DOF-row identification | no |
| **T3-NYISO-GOLDEN** | HELD (precondition lapsed) | — | no |

**Conclusion: no HOLD is required for any wave-1 lane.** The capx track's live writers are in
`scripts/forecast_verdict.py` and `frontend/data/forecast/`; wave 1's `src/` regions
(`policy/carbon.py`, `policy/cap_and_trade.py`, `policy/federal_ces.py`, `policy/clean_tiers.py`,
`model/lp/rows.py`, `model/interchange/spec.py`, `results/export.py|outputs.py|emissions.py`,
`src/market_sim/matrix.py`, `data/datacenter.py`, and the four named `runner.py` /
`scenarios.py` / `constants.py` regions) are unheld. The one live shared surface is the six
matrix shards, written by capx re-scores AND by the owner's backcast lanes several times a day
(`3eaf7918` caiso-252, `fe38a699` nyiso-194 both landed on 2026-09-05) — hence the protocol.

**Issued:** SCN-WS0, SCN-WS1a, SCN-WS2a, SCN-WS3a, SCN-WS4a (§5).
**Cards presented:** D-1, D-2, D-3, D-6.

---

## 1. Lane scoreboard

| lane | scope | status | branch | model | evidence / notes |
|---|---|---|---|---|---|
| **SCN-WS0** | Emissions grain (by fuel / by zone / import line / unserved) + multi-metric matrix frame + `report_scenario_deltas.py` + `collate_scenario_campaign.py` + the scenario YAML set + `--set` override + `scenario` registration kind; one paired NEISO T0 to exercise it | **LANDED r#3 — all six items** | `claude/scn-ws0-k7m2-8743yi` (merged, PRs #4869/#4877) | **Opus** | Completed itself between refreshes, **including the G-E4 cap-row rider the desk was about to charter**. T0 STOP gate PASS, 0 FAIL/0 WARN × 14 invariants per arm, both arms registered (`scn-ws0-smoke`). `FINDING-scn-ws0-2026-09-05.md`. **Its result is the leakage number** (§0 r#3). Unblocks WS-1b, WS-2b, WS-4b/c, WS-5. **SCN-WS0-R WITHDRAWN undispatched.** |
| **SCN-WS1a** | Federal carbon-price semantics (G-C1, gated on D-1) + the two seam defects (G-C2, G-C3) + the pre-declared `CAP-STATE-TIGHT` case | **LANDED r#3 (complete under its card gate, matrix duty discharged)** | `claude/scn-ws1a-carbon-d1-eupbi5` (merged, PRs #4856/#4860/#4867/#4887) | **Fable** | Items 2–4 + Phase 0 + the D-1 evidence memo; item 1 correctly withheld on the open card. **`717de664` minted the `carbon_price_path` + `policy_bundle` rows and a cell in all six shards** — the r#2 finding was true at its pin and the lane repaired it itself. `a147362b` scored the CAISO T0: every structural gate row passes. Item 1 remains the only thing D-1 blocks. |
| **SCN-WS2a** | The endogenous national CES **target** row (G-S1, G-S3) + the two new fields + the three state/federal postures | **CHECKPOINT r#4 — OWED, not lost** | `claude/scn-ws2a-federal-ces-qm512t` (all merged, PRs #4870/#4892) | **Fable** | Items 1–2, the docs legs (`73e5351f`) and the T0 PRECOMMIT (`6e6449ab`, pushed before the solve) all on main. **Still owed: the probe result, the postures tests, the FINDING, and the CES matrix row** (`federal_ces_target_by_year` absent from the matrix at three consecutive pins). Holds merged PRs → the relaunch protocol does NOT apply; SCN-WS2a-R stays withdrawn. |
| **SCN-WS3a** | Voluntary clean-demand **design memo** (no code, no solve) | **LANDED r#2** | `claude/scn-ws3a-voluntary-demand-{s8iukw, 9f1you}` (both merged, PRs #4857/#4859) | **Fable** | Memo + 5 owner boxes (D-3, new **D-3b**, new **D-3c**, the D-6 brief, the D-2 voluntary sub-levels) + a cross-check addendum. **Launched twice**; no divergence between the instances. |
| **SCN-WS4a** | DC zone shares for ERCOT + MISO; NEISO `{}` re-check; the D-4 constant-vs-published gap list | **LANDED r#2** | `claude/scn-ws4a-datacenter-shares-yf7wvi` (merged, PR #4863) | **Opus** | ERCOT already populated (plan §2.4 corrected); MISO populated + validated on published totals; NEISO `{}` re-confirmed; D-4 gap list presentable unedited. |
| **SCN-WS1b** | Six-ISO carbon paired T0 probe + NEISO/ERCOT T1-F ladder + the per-ISO leakage line | **RUNNING r#4** (owner-confirmed launch; no branch yet, normal inside one refresh — graded by content at r#5) | `claude/scn-ws1b-carbon-sixiso-h6rt` | **Opus** | UNBLOCKED by WS-0 item 5. Runs the **reduced form** (`--set carbon_price_delta=25`) while D-1 is open. Carries WS-0's leakage duty: the import line beside CO2, per ISO. |
| **SCN-WS2b** | Premium-ladder re-prove at HEAD posture + `scripts/ces_national_clearing.py` | **RUNNING r#4** (owner-confirmed launch; no branch yet — graded by content at r#5) | `claude/scn-ws2b-ces-ladder-clearing-p9wf` | **Opus** | UNBLOCKED by WS-0 item 5. Independent of live SCN-WS2a — it consumes committed premium legs, not the target row. |
| **SCN-WS0-R** | *(WS-0's owed half)* | **WITHDRAWN r#3, NEVER DISPATCHED** | — | — | Its entire scope landed on main between r#2 and r#3, riders included. Recorded so no successor re-issues it. |
| **SCN-WS2a-R** | *(WS-2a's owed half)* | **WITHDRAWN r#3, NEVER DISPATCHED** | — | — | SCN-WS2a is live with a pushed PRECOMMIT; dispatching -R would build the twin the D60-R2 precedent exists to prevent. If WS-2a is silent for two refreshes the relaunch protocol applies then. |
| **SCN-MX-R** | *(the r#2/r#3 stem)* | **LOST r#4 — NEVER LAUNCHED** | `claude/scn-mxr-matrix-duty-repair-j5tv` (burned) | — | No branch, no PR, two refreshes after issuance. Relaunch protocol applied; not re-graded as running. |
| **SCN-MX-R-r2** | Diagnose why `check_mechanism_matrix.py` exits 0 on a PR adding two `ScenarioConfig` fields with no row (now confirmed across **three** pins); the one verified-outstanding cache-epoch entry; the CES row **only if** SCN-WS2a lands without it | **RELAUNCHED r#4 (verbatim)** | `claude/scn-mxr2-matrix-duty-repair-t7bq` | **Fable** | `scripts/` stays un-edited: diagnose and route. |
| **SCN-WS4b** | *(the r#2/r#3 stem)* | **LOST r#4 — NEVER LAUNCHED** | `claude/scn-ws4b-loadhi-adequacy-b2np` (burned) | — | No branch, no PR, two refreshes after issuance. Relaunch protocol applied; not re-graded as running. |
| **SCN-WS4b-r2** | *(the r#4 relaunch)* | **SUPERSEDED r#5, NEVER DISPATCHED** | `claude/scn-ws4b2-loadhi-adequacy-x3mc` (burned) | — | The original lane landed the charter. The relaunch was never needed; recorded so no successor dispatches it. |
| **SCN-WS4c** | Six T0 LOAD-HI probes + NEISO/ERCOT T1-F | **BLOCKED (wave 2)** | — | Opus | WS-0 ✓, WS-4a ✓. **Blocked on SCN-WS4b-r2 alone.** |
| **SCN-WS3b** | Voluntary-demand build | **BLOCKED (wave 2) — on the CARD only** | — | Fable | Both code preconditions now MET (WS-2a's `rows.py` coupling relaxation landed and documents the second-consumer seam; WS-4a's DC module landed). Blocked solely on **D-3 + the memo's boxes D-3b/D-3c/D-2-voluntary**, all open. |
| **SCN-WS3c** | Voluntary-demand probe (ERCOT T0 → T1-F) | **QUEUED — precondition now reachable** | — | Opus | Precondition: SCN-WS3b on main, which S1 has now released. Issued the refresh WS-3b lands. |
| **SCN-WS5A-LOAD-\<ISO\>** ×6 + **-SYNTH** | **Stage A-LOAD** — `REF`/`LOAD-HI`/`LOAD-HI-ORGANIC`, T1-F 2026–2030, six ISOs | **RELEASED by S5 — issues when SCN-WS4c lands** | — | Opus | No CCS exposure (the retrofit screen is inert below 2028). **Needs no further card**: S5 authorizes this half. |
| **SCN-WS5A-POLICY-\<ISO\>** ×6 + **-SYNTH** | **Stage A-POLICY** — the CES cases, the 2028+ carbon legs, `ALL-CLEAN`, `VOL-*` | **HELD by S5 on the CCS seam** | — | Opus | Precondition: WS-0, WS-1a/b, WS-2a/b, WS-4a/b/c on main; WS-3b/c on main **or** D-3 ruled NO (then VOL-\* and CES-P20+VOL-HI drop, with a ledger note). |
| **Stage B** | Full-horizon legs | **NOT ISSUABLE** | — | — | Needs card D-5 **and** an OPEN §2.1b gate for the named ISO at issuance. At the r#1 pin only NEISO is open. Re-check at issuance, never at planning. |

---

## 2. Owner cards

| card | question | status | recorded ruling |
|---|---|---|---|
| **D-1** | Federal carbon price on a program ISO: **replace** (today), **floor** (`max`), or **additive**? | **RULED r#5 am.1 — S2** | **S2 (2026-09-06): FLOOR.** `effective = max(RFF path(year), program trajectory(year))` on a program ISO, the path alone elsewhere. `carbon_price` (scalar) keeps its Q26 replace semantics untouched. Ruled with the measured consequence on the record: the RFF mid path never exceeds a program trajectory in any year, so the floor makes `tight` an exact **no-op** on CAISO/NYISO/NEISO rather than an increase. → **SCN-WS1c issued.** |
| **D-1(b)** | *(new, raised by the evidence)* Once the floor is in, `policy_bundle="tight"` is an exact **no-op** on CAISO/NYISO/NEISO — the RFF mid path never exceeds a program trajectory in any year. Should `tight` mean something else on a program ISO? | **PRESENTED r#2** | — |
| **D-1(c)** | *(new)* PJM's partial RGGI footprint under a federal floor — floor against what, when only part of the fleet faces the state program? | **PRESENTED r#2** | — |
| **D-2** | Campaign levels — carbon paths, CES premium ladder, **CES target schedule + ACP**, voluntary levels, load-high pairing. | **RULED r#5 am.1 — S3** | **S3 (2026-09-06): the plan's §3.5 table is the COMMITTED default.** Carbon RFF low/mid/high; CES premium {10, 20, 30}; **CES target {2026: current, 2035: 0.80, 2050: 1.00} with ACP $50**; LOAD-HI = growth high + DC high. No re-solve is owed: SCN-WS2a built and probed against exactly this and labelled it illustrative, so the change is to the label, not the number. The WS-3a memo box 5 voluntary sub-levels ride the same ruling on the plan's defaults. → **SCN-LEVELS issued.** **EXECUTED 2026-09-06 by SCN-LEVELS** (`FINDING-scn-levels-2026-09-06.md`): the committed levels are written into `configs/scenario_campaign_matrix.yaml`, the two CES field docstrings, plan §3.5 + §5.1 and this ledger; **`CES-T80` went LIVE** (its fields landed with WS-2a, its level with S3) at `{2026: 0.55, 2035: 0.80, 2050: 1.00}` / ACP 50.0; **zero numbers moved, zero defaults moved, 91 pre-existing cache keys measured byte-identical, no solve.** **THREE LEVELS S3 DID NOT REACH and that the lane refused to infer — re-present them:** (i) `CAP-STATE-TIGHT`'s declining budget (§3.5 names no number; the slope is still the OWNER level of `FINDING-scn-ws1a-2026-09-05.md` §4.2); (ii) the voluntary `f_commit` **mid** and the WTP-ceiling **level**, which the memo's box 5 itself leaves owner-set even as S3 commits "the box-5 defaults"; (iii) the carbon ladder's **form** — S3 commits the RFF *path* ladder, which cannot go live until SCN-WS1c lands S2's floor, so the campaign still runs the additive `carbon_price_delta` interim whose {15, 25, 50} knots are a desk stand-in and NOT ruled levels. |
| **D-3** | Is a voluntary clean-demand **scenario axis** admissible given ffr-5b's inadmissibility ruling on corporate PPA demand as a *driver*? | **RULED r#5 am.1 — S1** | **S1 (2026-09-06): YES — a declared, forecast-only, publicly-anchored, default-off scenario axis.** The ffr-5b ruling is held to be about a *fitted driver*, a different admissibility class; its null is preserved in REF and every scored lane. → **SCN-WS3b issued**, WS-3c follows it. |
| **D-3b** | *(memo box 2)* Does in-LP hourly (24/7) matching stay deferred to the isolated `scope2-lce-portfolio` tool? | **RULED r#5 am.1 — with S1** | **DEFERRED.** The owner took S1's recommended form rather than the hourly-in-LP variant, so 24/7 stays in the isolated tool, fed the campaign's LMPs. WS-3b builds the annual volumetric row only. |
| **D-3c** | *(memo box 3, NEW)* The eligible set — renewable-only by default (incl. offshore wind), carbon-free (nuclear/CCS) only as a labelled override; credit all eligible units or new builds only? | **PRESENTED r#2 — STILL OPEN after S1/S3** | — · S1 ruled the AXIS admissible and S3 ruled its LEVELS; neither reaches the eligible SET. SCN-WS3b therefore builds against the memo's **recommendation**, which stays labelled a recommendation and is the one place SCN-LEVELS deliberately left the illustrative-class wording standing (`FINDING-scn-levels-2026-09-06.md` §4). |
| **D-4** | Fund the `load-forecast` curated intake? | **RULED r#5 am.1 — S4** | **S4 (2026-09-06): FUND THE FULL DATATYPE.** All six published sources curated through the data-intake skill. **This OVERRIDES the desk's and SCN-WS4a's recommendation to defer**, and is the largest of the three options offered — recorded as the owner's call on a question the desk had answered the other way. → **SCN-LOAD issued**, with the known 403 host wall on MISO's driver-level data flagged at the gate rather than discovered mid-lane. **LANDED 2026-09-06 — the ruling is vindicated on evidence neither recommendation had.** All six sources obtainable and on disk; G-D4-1/-2/-4 CLOSED, G-D4-3 partial (ERCOT verified, PJM's Table B-9b read but the shares deliberately not rewritten — routed), G-D4-5 a disclosed null; the MISO 403 wall re-confirmed BLOCKED. The return was NOT the provenance upgrade the card was argued on: the intake found an era-window error in every rate and a table silently mixing peak- and energy-derived bases, worth up to **+31 % of the 2030 demand scalar**, while NYISO — the one row already properly derived — reproduced to four decimals. `FINDING-scn-load-2026-09-06.md`; six items routed to this desk. |
| **D-7** | Does Stage A run before the CCS emission-rate seam is repaired? | **RULED r#6 am.1 — S5** | **S5 (2026-09-06): HOLD THE POLICY HALF, RUN THE LOAD HALF NOW.** Stage A splits at the `gas_cc_ccs` line: **A-LOAD** (`REF`/`LOAD-HI`/`LOAD-HI-ORGANIC` six-ISO T1-F + the sub-2028 carbon T0 probes) is released and issues when SCN-WS4c lands, needing no further card; **A-POLICY** (every CES case, every 2028+ carbon case, `ALL-CLEAN`, `VOL-*`) holds until the capx CCS seam is repaired and a paired check confirms `emission_rate` follows the retrofit. Routed to the capx director as a priority signal. |
| **D-5** | Per-campaign §2.1b grant for the NEISO scenario campaign (Stage B). | **HELD** — presented only with Stage A's measured cost table on the dashboard. | — |
| **D-6** | Attribute netting between a federal CES row and a voluntary-demand row. Recommendation: **counts toward**, report both. | **PRESENTED r#1 — STILL OPEN after S3** | — · S3 did not reach it. `CES-P20+VOL-HI` therefore reports BOTH nettings and asserts neither; the memo §4.3 is the brief and Addendum A.2 the dissent to weigh beside it. |

Rulings are recorded verbatim and numbered **S1, S2, …** here and appended to the plan's §6 row
as `RULED <date>: …` in the same refresh commit.

---

## 3. Readiness scorecard (the plan's §5.1, kept current here)

State at r#1 = plan v1, unmoved. Each landing lane updates BOTH this table and the plan's §5.1.

| Criterion (plan §1) | Carbon | CES premium | CES target | Voluntary | Load-HI | Emissions |
|---|---|---|---|---|---|---|
| 1 expressible in committed config | yes — **G-C1 CLOSED** (SCN-WS1c 2026-09-06, executing owner ruling **S2**/card D-1): `resolved = max(RFF path, program trajectory)` on a program ISO, the path alone elsewhere. The `tight` cut of $16–$102/t on CAISO/NYISO/NEISO is gone — corrected +$15.98 to +$102.29/t in all 25 yrs, and **no cell anywhere falls**. Gates: 450/450 cells match WS-1a's committed `floor` prediction; footprint exactly 3×25 cells; 0 of 90 committed run_configs on the changed branch and 0 keys moved. **`tight` is now an exact NO-OP on the three program ISOs** — the ruled outcome; **D-1(b)** (what `tight` should mean there) and **D-1(c)** (PJM's partial footprint) stay OPEN. `FINDING-scn-ws1c-2026-09-06.md` | yes | **yes** (SCN-WS2a: `federal_ces_target_by_year` + `federal_ces_acp_usd_per_mwh`; illustrative level, D-2 open) | **no** | **yes (SCN-WS4b 2026-09-06)** — `LOAD-HI` / `LOAD-HI-ORGANIC` disclosed in the campaign YAML (ERCOT tail regime in 2030 only; ORGANIC byte-identical on PJM/CAISO/NEISO through 2030) + the six-ISO adequacy reading pre-declared (`FINDING-scn-ws4b-2026-09-06.md` §2) + the `backstop_built_mw`/`_mwh` column; siting sourced for ERCOT/PJM/MISO (SCN-WS4a). **Inputs re-derived 2026-09-06 (SCN-LOAD, ruling S4)** — the growth/DC/electrification constants now derive from the curated `load-forecast` datatype; demand at 2030 moves +30.9 % (ERCOT mid) / +17.8 % (PJM mid), and the `LOAD-HI` case comment's ERCOT tail-regime arithmetic is stale (block share 97.3 % → 44.1 %, routed). `FINDING-scn-load-2026-09-06.md` | **yes r#2** — six-ISO REF bases + `scenario_campaign_matrix.yaml` + the `--set` override (WS-0 item 4) |
| 2 reaches dispatch + deployment | yes (G-C2 + G-C3 closed at WS-1a; cap-row dual NOT exported — G-E4 rider now assigned to **SCN-WS0-R**) | yes | **yes** (SCN-WS2a: the row → dispatch; dual → the existing `max()` screen seam; deployment leg not exercised by the 1-yr T0) | **no** | yes | — |
| 3 paired probe right-signed, per ISO | NEISO only | **ERCOT + NEISO at HEAD posture (SCN-WS2b)** — direction holds table by table vs the July surface, invariant pattern identical; ERCOT saturates above ~$20/MWh on the queue budget and its price/deployment levels are not campaign-grade (adequacy collapse, G-S4 stands); NEISO right-signed on share/price/imports but its CO2 read-out is governed by the CCS emission-rate seam (`FINDING-scn-ws2b-2026-09-06.md` §5.3, routed) | NEISO only, escape regime (dual = ACP $50 exactly; CO2 +2e-4 reported not smoothed — `FINDING-scn-ws2a-2026-09-05.md` §4.3). **Quotable as a CAMPAIGN-LEVEL result since S3**, having been run at exactly the committed level | **no** | **no** | — |
| 4 backcast byte-identity | yes (WS-1a: no key moves; keeper + forecast key list, FINDING §5) — **re-measured at the S2 floor** (SCN-WS1c): 0 keys moved, default `e5ecd4105ada3e58` stable, **0 of 90** committed `run_config.json` on the changed branch, backcast 2023–25 trajectories identical in all six ISOs; six keeper bundles named, `FINDING-scn-ws1c-2026-09-06.md` §4 | yes | yes (SCN-WS2a: six keeper keys byte-identical, FINDING §5) | — | yes | — |
| 5 matrix duty | stamped — `carbon_price_path` + `policy_bundle` base rows and a cell in every shard at `717de664` (on main). The r#2 "NOT stamped" reading was true at `db8b6015`; the lane's claim ran one PR ahead of its commit and the lane closed it itself. Verified on disk by SCN-MX-R-r2 (r#4, `FINDING-scn-mxr-2026-09-06.md` §5). | stamped | stamped (`federal_ces_target` row + six cells, SCN-WS2a last commit) | — | stamped | — |
| 6 emissions grain | by fuel / by zone | by fuel / by zone | by fuel / by zone | by fuel / by zone | by fuel / by zone | **G-E1..E5 CLOSED** (SCN-WS0, all six items landed 2026-09-05); G-E6 / G-E7 stay OPEN as declared disclosure items |
| 7 registered probes on dashboard | NEISO FC-6 pair | **six ladder legs** `{ercot,neiso}-2026-2030-scn-ws2-ladder-{bau,ces-20,ces-40}` (kind `scenario`, campaign `scn-ws2-ladder`) — G-S5 CLOSED, the pruned POC evidence restored at HEAD | NEISO T0 pair `neiso-2026-2026-scn-ws2a-neiso-2026-t0-{ref,target}` (kind `scenario`) | — | none | `scn-ws0-smoke` REF/CARB pair |

**The CES-target column's level became COMMITTED with no evidence change** (SCN-LEVELS,
2026-09-06). D-2 → S3 committed the plan's §3.5 table, and SCN-WS2a had already built and
probed the target row against exactly those values under an "illustrative" label — so **no
cell of this table moved on the evidence**: rows 2, 4, 5 and 7 are untouched, row 1 changes
only its label, and row 3's probe becomes quotable as a campaign result rather than as
machinery. Measured: 91 pre-existing cache keys byte-identical, no `ScenarioConfig` default
moved, no solve. The three levels S3 did **not** reach are named in §2's D-2 row and must be
re-presented, not inferred.

**Open lane assignments against the scorecard:** ~~WS-0 → the Emissions column entire (criterion
6) + criterion 1's harness half~~ — **LANDED 2026-09-05, ALL SIX ITEMS**, G-E1..E5 closed and
criterion 1's harness half with them; G-E6/G-E7 remain open as declared disclosure items
(`docs/handoffs/FINDING-scn-ws0-2026-09-05.md`); WS-1a → Carbon row 1 (the G-C1 defect) and rows 4/5; WS-1b →
Carbon rows 3/7; WS-2a → the CES-target column rows 1/2/4/5 and its probe half of row 3; WS-2b →
CES-premium rows 3/7; WS-3a → nothing (memo); WS-4a → Load-HI row 1 (partial → the siting half)
— **LANDED 2026-09-05**: MISO populated from the 2026 LTLF regional DC decomposition, ERCOT
verified already-populated (the plan §2.4 "only for PJM" line was stale and is corrected), NEISO
`{}` re-confirmed with its arithmetic; the named case remains SCN-WS4b's and is NOT claimed. **WS-4b → Load-HI row 1's case half — LANDED 2026-09-06** (branch `claude/scn-ws4b-load-hi-adequacy-jvv96t`; the §5 stem rows name `-b2np`, the r2 charter `scn-ws4b2-…-x3mc` — reconcile): the case comment completed, the reading pre-declared per ISO against the bare `ff-verdicts.json` keys, the report column with 13 tests; six items routed in its FINDING §5, first among them that the board's `gate_reading` prose is stale for CAISO/MISO. **SCN-WS4c is unblocked.**
The D-4 gap list is `docs/handoffs/FINDING-scn-ws4a-2026-09-05.md` §4, presentable unedited; that
FINDING §6 routes one cache-epoch ledger entry (MISO forecast bundles stale at the same key) that
SCN-WS4a may not write, `results/cache.py` being another lane's region.

---

## 4. Collision register (file → owning lane → wave)

**Wave-1 shared-file protocol** (written verbatim into every wave-1 prompt):

1. `config/scenarios.py` and `runner.py` are touched by WS-1a and WS-2a in the **named disjoint
   regions ONLY**. Any edit outside your region is a **STOP** — route it to SCN-DESK in your
   FINDING; do not widen.
2. The six matrix shards (`docs/codebase-site/data/mechanism-matrix/<ISO>.js`) and
   `docs/codebase-site/data/mechanism-matrix.js`: make the edit your **LAST commit**, after
   `git fetch origin main` + rebase, as **one appended cell line per ISO**, so any conflict is
   one line. This is not advisory — capx D60-R2's re-scores and the owner's backcast lanes
   append to these files several times a day (`3eaf7918`, `fe38a699` both on 2026-09-05).
   Merge order if WS-1a and WS-2a are both ready: **WS-1a first, WS-2a rebases.** CI
   (`scripts/check_mechanism_matrix.py`) enforces that a new `ScenarioConfig` field carries its
   base row + a cell line in every shard **in the same PR** (rule 28 duty c).
3. **`configs/scenario_campaign_matrix.yaml` OWNERSHIP TRANSFERS to SCN-WS4b at r#2** — WS-0's
   YAML work (item 4) landed and its owed items 5–6 do not touch the file. SCN-WS0-R must not
   edit it.
3a. **MATRIX-TREE PROTOCOL, AMENDED r#3.** The r#2 freeze is **lifted** — SCN-WS1a minted its
   own rows and cells, so there is no longer one repair lane holding the tree. The standing
   rule returns to protocol item 2 (**last commit, after rebase, one appended line per ISO**),
   and it binds harder than at r#2: capx D65 stamped its own row and six cells at `4b28c93f`,
   so the capx track is an active concurrent writer. Live SCN-WS2a stamps the CES row itself
   (rule 28(b) — the session that tests the mechanism stamps it); SCN-MX-R stamps it **only
   if** WS-2a lands without it. SCN-WS1b and SCN-WS2b stamp their own cells, last commit.
4. **Nobody touches `frontend/data/forecast/program-status.json`** — it is the capx board,
   written by D60-R2 and D58.

| file / region | owning lane | wave | note |
|---|---|---|---|
| `src/market_sim/results/export.py`, `results/outputs.py`, `results/emissions.py` | SCN-WS0 | 1 | |
| `src/market_sim/matrix.py`, `scripts/collate_full_horizon.py` | SCN-WS0 | 1 | |
| new `scripts/report_scenario_deltas.py`, new `scripts/collate_scenario_campaign.py` | SCN-WS0 | 1 | WS-4b adds the "backstop-built" column to the former **after** WS-0 lands. |
| `scripts/run_full_horizon.py`, `scripts/run_ces_leg.py` | SCN-WS0 | 1 | **the `--set` override ONLY** |
| `scripts/register_forecast_run.py`, the forecast dashboard pages | SCN-WS0 | 1 | NOT `frontend/data/forecast/program-status.json` |
| `configs/scenarios/*`, `configs/scenario_campaign_matrix.yaml` | SCN-WS0 | 1 | sole writer this wave |
| `src/market_sim/policy/carbon.py`, `policy/cap_and_trade.py`, `config/scenario_resolvers.py` | SCN-WS1a | 1 | |
| `src/market_sim/model/interchange/spec.py` — **the one carbon-adder line (~:1931)** | SCN-WS1a | 1 | |
| `runner.py` — **REGION: the `assemble_mc` call site (~:2561-2575)** | SCN-WS1a | 1 | |
| `config/scenarios.py` — **REGION: the D34 guard in `__post_init__` (~:15572)** | SCN-WS1a | 1 | |
| `src/market_sim/results/cache.py` — **one epoch entry** | SCN-WS1a (LANDED) → SCN-WS0-R (WITHDRAWN) → **SCN-MX-R at r#3** | 1–3 | The WS-4a-routed entry (MISO forecast bundles stale at the same key after the DC-share change) did **not** land — verified: the file is unchanged since `db8b6015`. MX-R's scope is widened by this one file only, and it writes a ledger entry, never a key. |
| `tests/unit/policy/test_cap_and_trade.py`, `test_carbon_price_below_base_guard.py` | SCN-WS1a | 1 | |
| `src/market_sim/model/lp/rows.py` | SCN-WS2a | 1 | WS-3b is the next writer (wave 2), **after** WS-2a merges. |
| `src/market_sim/policy/federal_ces.py`, `policy/clean_tiers.py` | SCN-WS2a | 1 | |
| `runner.py` — **REGION: RPS/clean-row arming + dual plumbing (~:1195-1229, :2851-2864, :4484-4521)** | SCN-WS2a | 1 | |
| `config/scenarios.py` — **REGION: the `federal_ces_*` block (~:3084-3157) + its `__post_init__` guard (~:15584)** | SCN-WS2a | 1 | |
| `docs/codebase/05-policy.md`, `policy/constraints.py` docstring (G-S6) | SCN-WS2a | 1 | |
| `docs/handoffs/voluntary-clean-demand-design-memo-2026-09-05.md` (new) | SCN-WS3a | 1 | memo only |
| `config/constants.py` — **REGION: `DATACENTER_ZONE_SHARE` / `DATACENTER_ADDITIONS_MW` only** | SCN-WS4a | 1 | `VOLUNTARY_*` anchors are WS-3b's separate region, wave 2. |
| `src/market_sim/data/datacenter.py`, `tests/unit/data/test_datacenter.py` | SCN-WS4a | 1 | WS-3b's DC-linked volume helper is the next writer, **after** WS-4a merges. |
| the six matrix shards + `mechanism-matrix.js` | **SCN-MX-R ONLY until it merges**; then ALL, last commit only | 1–3 | see protocol items 2 and 3a |
| `scripts/register_forecast_run.py`, `configs/scenarios/*` | SCN-WS0 (LANDED) → **SCN-WS0-R** | 1–2 | |
| `configs/scenario_campaign_matrix.yaml` | SCN-WS0 (LANDED) → **SCN-WS4b** | 1–2 | transfer recorded at r#2 |
| `scripts/check_mechanism_matrix.py` | **NOBODY on the SCN track** | — | the duty-(c) CI gap is diagnosed and reported by SCN-MX-R and routed to the capx/audit track; `scripts/` is not this desk's to repair |
| `scripts/forecast_verdict.py`, `frontend/data/forecast/program-status.json` | **capx D60-R2 / D58** | — | **no SCN lane may touch these** |

---

## 5. Issuance record

Stems are recorded so a relaunch (`…-r2`) can never collide with the original.

| refresh | lane | model (id) | branch stem issued | **branch realized** | data profile | plan §7 body used |
|---|---|---|---|---|---|---|
| r#1 | SCN-WS0 | **Opus** `claude-opus-5` | `claude/scn-ws0-k7m2` | `claude/scn-ws0-k7m2-8743yi` | `neiso` | §7 "WS-0", verbatim |
| r#1 | SCN-WS1a | **Fable** `claude-fable-5-1` | `claude/scn-ws1a-p4qd` | `claude/scn-ws1a-carbon-d1-eupbi5` | `caiso` | §7 "WS-1a", verbatim + the D-1 gate split (item 1 conditional) |
| r#1 | SCN-WS2a | **Fable** `claude-fable-5-1` | `claude/scn-ws2a-t9xb` | `claude/scn-ws2a-federal-ces-qm512t` | `neiso` | §7 "WS-2a", verbatim |
| r#1 | SCN-WS3a | **Fable** `claude-fable-5-1` | `claude/scn-ws3a-r6vn` | `claude/scn-ws3a-voluntary-demand-{s8iukw, 9f1you}` **(twice)** | `code` | §7 "WS-3a", verbatim |
| r#1 | SCN-WS4a | **Opus** `claude-opus-5` | `claude/scn-ws4a-h3zc` | `claude/scn-ws4a-datacenter-shares-yf7wvi` | `all` | §7 "WS-4" **items 2 and 5 only** (items 1/3/4 split to WS-4b/WS-4c, wave 2) |

**r#2 issuance.**

| refresh | lane | model (id) | branch stem issued | data profile | body used |
|---|---|---|---|---|---|
| r#2 | SCN-WS0-R | **Opus** `claude-opus-5` | `claude/scn-ws0r-registration-t0-m4qk` | `neiso` | plan §7 "WS-0" **items 5 and 6 only** + the G-E4 cap-row rider (routed from WS-1a §4.3) + the WS-4a cache-epoch entry |
| r#2 | SCN-WS2a-R | **Fable** `claude-fable-5-1` | `claude/scn-ws2ar-ces-postures-probe-w8dr` | `neiso` | plan §7 "WS-2a" **items 3 and 4** + the G-S6 doc legs; matrix withheld to SCN-MX-R |
| r#2 | SCN-MX-R | **Fable** `claude-fable-5-1` | `claude/scn-mxr-matrix-duty-repair-j5tv` | `code` | not a plan §7 body — a rule-28 repair charter written at r#2 from the refresh's own finding |
| r#2 | SCN-WS4b | **Fable** `claude-fable-5-1` | `claude/scn-ws4b-loadhi-adequacy-b2np` | `all` | plan §7 "WS-4" **items 1 and 3** (the split recorded at r#1), no solve |

**r#3 issuance.**

| refresh | lane | model (id) | branch stem issued | data profile | body used |
|---|---|---|---|---|---|
| r#3 | SCN-WS1b | **Opus** `claude-opus-5` | `claude/scn-ws1b-carbon-sixiso-h6rt` | `all` | plan §7 "WS-1b", verbatim + the reduced-form D-1 gate + WS-0's per-ISO leakage duty |
| r#3 | SCN-WS2b | **Opus** `claude-opus-5` | `claude/scn-ws2b-ces-ladder-clearing-p9wf` | `ercot` then `neiso` | plan §7 "WS-2b", verbatim |
| r#3 | SCN-MX-R | **Fable** `claude-fable-5-1` | `claude/scn-mxr-matrix-duty-repair-j5tv` | `code` | r#2 repair charter, **narrowed at r#3** to the CI-gate diagnosis + a conditional CES stamp |
| r#3 | SCN-WS4b | **Fable** `claude-fable-5-1` | `claude/scn-ws4b-loadhi-adequacy-b2np` | `all` | r#2 charter **re-emitted verbatim** |

**r#4 issuance (relaunches).**

| refresh | lane | model (id) | branch stem issued | data profile | body used |
|---|---|---|---|---|---|
| r#4 | SCN-WS4b-r2 | **Fable** `claude-fable-5-1` | `claude/scn-ws4b2-loadhi-adequacy-x3mc` | `all` | the r#3 charter **verbatim** |
| r#4 | SCN-MX-R-r2 | **Fable** `claude-fable-5-1` | `claude/scn-mxr2-matrix-duty-repair-t7bq` | `code` | the r#3 narrowed charter **verbatim** |

**r#5 amendment 1 issuance — the four ruling-released lanes.**

| refresh | lane | model (id) | branch stem issued | data profile | released by | body used |
|---|---|---|---|---|---|---|
| r#5 am.1 | SCN-WS1c | **Fable** `claude-fable-5-1` | `claude/scn-ws1c-carbon-floor-v2rk` | `neiso` | **S2** | plan §7 "WS-1a" **item 1**, verbatim |
| r#5 am.1 | SCN-WS3b | **Fable** `claude-fable-5-1` | `claude/scn-ws3b-voluntary-demand-n5wq` | `ercot` | **S1** | plan §7 "WS-3b", verbatim + the memo's signed design |
| r#5 am.1 | SCN-LEVELS | **Fable** `claude-fable-5-1` | `claude/scn-levels-d2-commit-c3jx` | `code` | **S3** | not a plan §7 body — a records charter written from the ruling |
| r#5 am.1 | SCN-LOAD | **Opus** `claude-opus-5` | `claude/scn-load-forecast-intake-w9tf` | `all` | **S4** | plan §3 WS-4 **item 4** (the intake), scope set by the ruling |

**r#5 issuance.**

| refresh | lane | model (id) | branch stem issued | data profile | body used |
|---|---|---|---|---|---|
| r#5 | SCN-WS4c | **Opus** `claude-opus-5` | `claude/scn-ws4c-loadhi-probes-q8vd` | `all` | plan §7 "WS-4" **item 4**, verbatim + WS-4b's pre-declared readings as the scoring target + the four post-r#4 rule changes |

**Burned stems, never to be reused:** `claude/scn-ws4b-loadhi-adequacy-b2np`,
`claude/scn-ws4b2-loadhi-adequacy-x3mc` (superseded — the original lane landed),
`claude/scn-mxr-matrix-duty-repair-j5tv` (LOST at r#4), plus the r#3 withdrawals below.

**Withdrawn at r#3, never dispatched:** SCN-WS0-R (`claude/scn-ws0r-registration-t0-m4qk`) and
SCN-WS2a-R (`claude/scn-ws2ar-ces-postures-probe-w8dr`). Their stems are burned and must not be
reused; a future lane needing that scope takes a new stem.

**Branch stems are ADVISORY, not binding** (r#2): every r#1 lane was provisioned by the harness on
its own branch name. The stem's purpose — stopping a relaunch from colliding with an original — is
served by the realized-branch column above, which every future relaunch must check first.

### 5.1 Model assignment — the standing rule and the r#1 assignments

**The rule, in force for every SCN lane at every refresh.** Rule 27 `[R-PUSH]` second half: any
session whose scope writes core infrastructure — anything under `src/market_sim/`,
`scripts/run_*.py` / `scripts/score_*.py`, `CLAUDE.md`, `model-methodology-spec.md`, or
`.github/workflows/` — is **Opus or Fable, never Sonnet**. The desk charter tightens this to
**no Sonnet on any SCN lane at all**, docs-only lanes included, so rule 27 is never the binding
constraint here — the plan's own label is. Within Opus/Fable the split follows the director's
r#20 doctrine, restated at plan §3: **`[FABLE]` for structural / adjudication work** (a design
whose shape is still being decided, a semantics change, an argument against a standing ruling)
and **`[OPUS]` for pre-declared execution** (a charter whose deliverables and gates are already
written down and whose job is to carry them out exactly).

| lane | label | model id | why this side of the split |
|---|---|---|---|
| SCN-WS0 | `[OPUS]` | `claude-opus-5` | Execution. Six enumerated deliverables, each with its own commit and its own trivial-first test; the paired T0's gate is arithmetic (by-fuel CO2 sums to `emissions_mt`). Nothing here is a judgment call. Writes `src/` + `scripts/` → rule 27 binds. |
| SCN-WS1a | `[FABLE]` | `claude-fable-5-1` | Adjudication. It changes what an existing registered field *resolves to* on three ISOs, argues the D-1 evidence memo the owner rules on, and must prove byte-identity across every keeper key. Writes `src/` → rule 27 binds. |
| SCN-WS2a | `[FABLE]` | `claude-fable-5-1` | Structural. A new LP row family, a coupling relaxation (`rows.py:1346`) that a later lane inherits, two new fields with a mutual-exclusion guard, and three postures to document. Writes `src/` → rule 27 binds. |
| SCN-WS3a | `[FABLE]` | `claude-fable-5-1` | Pure adjudication — the memo argues, line by line, that a declared scenario axis is a different admissibility class from the driver `ffr-5b` ruled out. Docs-only, so rule 27's letter would permit Sonnet; **the charter forbids it**, and this is the least Sonnet-shaped task in the wave. |
| SCN-WS4a | `[OPUS]` | `claude-opus-5` | Execution. Transcribe published siting geography with citations, hold shares to 1.0, re-check one immateriality arithmetic, enumerate a gap list. Rule 14 provenance work with a fixed shape. Writes `config/constants.py` → rule 27 binds. |

**Queued lanes carry their labels forward** (assigned now so a relaunch cannot drift): SCN-WS1b
Opus, SCN-WS2b Opus, SCN-WS4b **Fable** (it is the adequacy *adjudication* — it pre-declares how
each ISO's high case is read, and pre-declaring a reading is the Fable half of plan §3 WS-4),
SCN-WS4c Opus, SCN-WS3b **Fable** (build-from-a-signed-design, but it is the first writer of a
new mechanism), SCN-WS3c Opus, SCN-WS5A-\<ISO\> ×6 + -SYNTH Opus.

**The desk itself.** The charter assigns **Fable** to SCN-DESK; this session is configured
`claude-opus-5` and the serving model may differ again. Recorded against interest — it is a
divergence from the charter, it affects only adjudication tone and not any lane's assignment,
and a successor desk session should be opened on Fable.

**Splits and gates applied to the plan's §7 bodies (never widenings):**
- WS-1a: plan item 1 is conditional on card D-1 reading FLOOR; unsigned → items 2–3 + the
  Phase-0 trajectory table + the D-1 evidence memo, then stop.
- WS-4: the plan's single §7 "WS-4" prompt is split three ways by the charter's wave plan —
  items 2+5 to **WS-4a** (wave 1), items 1+3 to **WS-4b** (wave 2, Fable), item 4 to **WS-4c**
  (wave 2, Opus) — because items 1 and 4 depend on WS-0's campaign YAML and harness, which do
  not exist yet.
- No other lane's body was edited.
