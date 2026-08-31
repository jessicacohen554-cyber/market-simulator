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
> ### 🟢 NEW AT v16 — ALL FOUR 2026-08-30 DECISION CARDS ARE EXECUTED, AND THE STAGE-0 TABLE HAS ITS FIRST CURRENT ROW
>
> v15 recorded four PM-sitting rulings executed. v16 records a **second, later
> sitting** — the owner's four **decision cards** — all four EXECUTED and
> verified at this pin. **CARD 1** captured the **PJM stage-0 golden**, untaken
> across seven consecutive boards: `perfb-stage0/manifest.json` now carries
> **ALL SIX** keepers and **PJM reads CURRENT against its live keeper** — the
> first non-stale row this table has ever had (F-1). **CARD 2** chartered the
> homeless T1-H capacity-entry defect and ran it to a measured A/B in one day
> (F-2). **CARD 3** recorded the cross-lane re-grade standing rule (F-3).
> **CARD 4** reverted the NYISO frontier (F-4). *(The plan's §8 entries for the
> cards were appended in the sitting itself; this board records their verified
> outcomes, not the cards again.)*
>
> ### 🟢 AND: FOUR-INSTRUMENT ALIGNMENT IS RESTORED — FIRST TIME SINCE v13
>
> All four re-derived independently at this pin: **CALIBRATED = `complete` =
> `frontier` = forecast gate-(a) passers = {PJM, NEISO}**. v15 had three of four
> agreeing with `frontier` = {PJM, NYISO, NEISO} the lone outlier; Card 4 closed
> it, and the standing rule the card set is **marker-master** — a frontier does
> not survive its ISO leaving CALIBRATED/`complete`. This retires v15 owner-queue
> item 1. See F-4 and F-9.
>
> ### 🔴 AND: THE STAGE-0 PROVENANCE PROBLEM CHANGED SHAPE RATHER THAN CLOSING
>
> The manifest's unresolvable `git_sha` **`af1ccb6` is gone** — but it was
> **overwritten, not resolved**. The Card-1 capture rewrote the single top-level
> `git_sha` to its own tree (`1cfea72`, which *does* resolve and *is* reachable
> in main), so the **five older captures now sit under a provenance sha naming a
> tree they were never captured against** — a reading that is no longer
> unresolvable, it is silently wrong. And re-deriving E-7 rather than carrying it
> found the prune class is **five-wide, not one**: **five of six captures'
> provenance runs are absent from the registry** (only PJM's is registered), and
> all five were already absent at the v15 pin. See F-5.

> **STATUS: PARKED AT G1** — live rollup maintained by the program-director
> session, updated on each owner "refresh". Canonical program definition:
> `docs/model-audit-release-plan-2026-08.md` (its §8 ledger is the durable event
> record; this board is the at-a-glance state). Completion figures are the
> director's estimate against each workstream's full DoD (A+B halves).

**Snapshot (v16):** **BASE SHA FOR EVERY FIGURE ON THIS BOARD: `54ca19ae`**
(merge of #4428), derived live from `origin/main` on 2026-08-31 and **held
stable across FOUR polling rounds** before the pin was taken. The director's own
derivation base **`ee75a0b` (merge of #4426) is REACHABLE BUT 2 MERGED PRs
STALE** (#4427, #4428 — both the capx desk; `git diff ee75a0b..54ca19ae` touches
only `docs/handoffs/capx-director-*`, so **no figure on this board differs
between the two states** and that is a measurement, not an assumption). Every
count below states the window it was measured over. Nothing is carried from the
dispatch, from board v15, or from any table, unverified.

| window | span | commits | non-merge | merged PRs |
|---|---|--:|--:|---|
| **since v15's pin** (`69ae4dc7..54ca19ae`) — the v16 cycle | 2026-08-30 12:25 → 17:12 PDT | **175** | **108** | **67** (#4360–#4428) |
| since v15's board LANDED (`6d3148d..54ca19ae`) | 2026-08-30 12:45 → 17:12 PDT | **163** | **101** | **62** |
| **since the director's derivation** (`ee75a0b..54ca19ae`) — what moved after the prompt was written | same day | **2** | **1** | **1** (#4428) |

**This is the busiest window this board has recorded — 67 merged PRs in four
hours and forty-seven minutes, against v15's 24 and v14's 21.** Of the 67:
**30 are the capx desk** (a DIFFERENT program — `capacity-expansion-director`
11, `capx-*` 18, plus #4428's `calibration-workstream-relaunch` refresh #20),
**30 are the calibration program**, and **7 are this program's** (#4365 v15's
own landing, #4368/#4377 the O7 lane, #4369/#4386 the director desk's card
execution, #4419/#4426 the T1-H Leg-A lane). The lane classification is derived
from the merge subjects' branch names, not from the commit titles — **the capx
desk merged thirty PRs and would have overwhelmed a commit-list scan.**

**Keeper motion: ONE promotion, in NYISO.** Re-derived rather than asserted:
all six `keepers/<ISO>.json` `keeper` fields compared byte-for-byte at
`69ae4dc7` and at the pin — **NYISO `2026-08-30-nyiso-157-par-attribution` →
`2026-08-30-nyiso-159-loss-surface`**, and the other five byte-identical. The
**only keeper-shard byte-motion in the entire window is NYISO's** (`git diff`
over `frontend/data/backcast/keepers/` returns that one file, +35/−21), and it
carries **both** the 159 promotion **and** Card 4's frontier revert.

**ONE open PR** (live `list_pull_requests` at the pin: **#4424**, capx D12-A)
and **ONE branch ahead of `main`** (`ls-remote`, tip ancestry-tested inside
`origin/main` rather than inferred): `claude/capx-d12a-arming-0ibtzh` (+2, the
open PR). **Neither is this program's, and no audit-program lane is running at
the pin** — this records lane is the only one, and it is the dispatched
instrument of the standing deviation.

**Headline, one line: every decision card executed, the PJM stage-0 golden
captured after seven boards of never being taken, four-instrument alignment
restored, audit row O7 closed, all five gates green — and the stage-0
provenance problem changed shape rather than closing, in a window where the
repo merged 67 PRs and this program merged seven of them.**

## What moved — v16 CYCLE (`69ae4dc7..54ca19ae`, "the decision-card cycle")

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


## Keeper table (read from `frontend/data/backcast/keepers/<ISO>.json` and `status/<ISO>.js` at `54ca19ae`)

Determinations and grade summaries parsed live from the status shards at the
pin. **C3a(RT) is the load-weighted mean-LMP error against RT actuals, per year
2023 / 2024 / 2025** — printed for every ISO because it is the criterion every
NOT-YET fail set contains, and printing it only for the failures hides how
narrow the margins are. ERCOT's row is the board's TWO-CONFIG entry (v14 D-2):
the grade column shows forward-span / carve-out / registered-3-year reads.

**Five of six cells are byte-unchanged from v15 and that is a re-derivation,
not a carry** — all six `keeper` fields compared byte-for-byte at `69ae4dc7`
and at the pin, all six determinations and grade summaries re-parsed, all
eighteen C3a(RT) magnitudes re-read from the shards. **The sixth, NYISO, moved
(157 → 159) and its whole row is re-derived** (F-7). Rubric **v3.5** on every
shard.

| ISO | Designated keeper | Determination | Grade (scored/target/fails/ledgered) | C3a(RT) 2023 / 2024 / 2025 |
|-----|-------------------|---------------|---|---|
| ERCOT | `2026-08-25-234-eastex-identity` (FORWARD, 2024–2025) **+ `2026-08-25-236-swcap-clip-k33`** (2023 carve-out) — TWO-CONFIG | forward `CALIBRATED` on span · carve-out `CALIBRATED` · registered 3-yr **`NOT-YET`** | 8 / 7 / 0 / 1 · 8 / **8** / 0 / **0** · (8 / 5 / **2** / 1) | **−39.7 % F** (the carve-out's year) / −0.2 % / −7.9 % |
| CAISO | `2026-08-26-caiso-220-c1-crosswalk` | `NOT-YET` | 8 / 6 / **1** / 1 | +4.0 % / **+12.5 % F** / **+15.5 % F** |
| PJM | `2026-08-15-pjm-162-inputclock` | **`CALIBRATED`** | 8 / **8** / 0 / **0** | +6.2 % / −0.8 % / −7.7 % |
| NYISO | ⬅ **`2026-08-30-nyiso-159-loss-surface`** (was `157-par-attribution`) | `NOT-YET` | 8 / **6** / **2** / 0 | +2.3 % / −1.2 % / **−11.5 % F** |
| NEISO | `2026-08-17-neiso-99-joint-p1` | **`CALIBRATED`** | 8 / 7 / 0 / 1 | +3.1 % / +5.7 % / +1.7 % |
| MISO | `2026-08-30-miso-188-rvsscope` | `NOT-YET` | 8 / 6 / **1** / 1 | +3.5 % / −4.3 % / **−12.3 % F** |

| ISO | v16 cycle (`69ae4dc7..54ca19ae`) |
|-----|--------------------------------|
| **ERCOT** | **Busiest lane again, promoted nothing again.** ercot-242 room-axis **registered**; **ercot-243 killed at census** (population is h3068-2024 alone); **ercot-244 rtolhsl ceiling KILLED AT CENSUS**; ercot-245 commitment-state Phase-0 precommit + probe. Separately its audit row closed: **O7 CLOSED**, the ladder decomposed into pricing −$0.02 vs commitment+interaction +$2.26/MWh (F-6), **keeper untouched**. Its **carve-out config still has no stage-0 golden** |
| **CAISO** | **UNMOVED.** caiso-224 merged; **caiso-225's watch sweep came back ALL NULL** — every armed watch (W-1/W-2/W-3, F2 derate) still blocked, A3's OFO record available+feasible but **unfunded**, nothing fires, **terminal rest re-affirmed** (#4425). Keeper unchanged; C3a-2024/2025 fails stand at +12.5 / +15.5 % |
| **PJM** | **UNMOVED and untouched for an EIGHTH consecutive cycle — and for the first time that is an asset, not a gap.** Still the only 8/8 zero-caveat scorecard, and **now the only ISO whose stage-0 golden is CURRENT** (F-1). The seven-board "cheapest capture, largest gap" line is retired |
| **NYISO** | **THE CYCLE'S ONLY PROMOTION: 157 → 159** (F-7). C3b leaves the fail set (8/5/3/0 → 8/6/2/0); C3a-2025 −12.0 → −11.5 %. Its frontier was **REVERTED by Card 4** (F-4), its `complete` marker stays withdrawn (so no D-5(b) re-key was owed), **Leg-2 STOPPED WITH CAUSE at access** (nyiso-160), and nyiso-161 filed an owner-ordered winter-face **waiver card**. nyiso-160 also proved the new keeper replays **bit-identically at HEAD** — no G1-class drift |
| **NEISO** | **UNMOVED and untouched.** Its entire residual remains the **`final` grant itself** — still **DATA-BLOCKED** on the 2025 EIA-923 FINAL vintage. One of only **two** `complete` ISOs, and — on the *forecast* board, a different program's — now the **first ISO ever to hold three §2.1b gate legs** (F-9) |
| **MISO** | **UNMOVED and untouched.** **miso-190's registration watch CLOSES** after three cycles (both sidecars present, #4370), and **miso-191 landed** (binning-aware exit-cohort delivery). Its stage-0 gap is still the deepest on the board |

**Markers at `54ca19ae`, re-read live this cycle:** `complete` =
**{NEISO, PJM}** · **`final` = EMPTY (`_note` only)** ·
**`holdout-freeze.json` `active: true`, TIER-SCOPED to `locked_test` alone**
(scope re-read at the pin: `isos: ALL`, `tiers: ["locked_test"]`,
`frozen_operations: solve / score / dashboard registration`; the validation
tier 2020–2022 is explicitly **not** frozen and is governed by the `complete`
marker + `--holdout-authorized`) · `withdrawn` = **{NYISO, CAISO}**. Both
surviving `complete` entries are **re-keyed to their live keepers** (rule 22
D-5(b)) — and neither of those two ISOs promoted this cycle, so **no re-key was
owed anywhere**, including for the one ISO that did promote, whose marker is
withdrawn. **`audit_keepers.py` returns PASS: 0 failures, 0 warnings** at the
pin, run not quoted.

**NO ISO HAS EVER SPENT A LOCKED-TEST YEAR** — re-verified at the pin by
walking every registry sidecar, not restated. Across all **58** registered
sidecars (v15: 56) the solve-year histogram is **{2022: 2, 2023: 56,
2024: 52, 2025: 52}** (per-ISO sidecar counts: ERCOT 15, MISO 15, NYISO 15,
PJM 5, CAISO 4, NEISO 4). The scan for any year in {≤2018, 2019, 2026} returns
**NONE**. The only out-of-training registrations remain the **two authorized
2022 validation touchpoints** (`2026-08-05-pjm-2022-touchpoint`,
`2026-08-06-neiso-2022-corrected-basis`). NEISO's one-shot stays **NEVER
GRANTED, not spent** (D-23). *Motion note: the +2 sidecars and the +2/+1/+1
year counts are the caiso-224 pair (CAISO 2 → 4) plus the miso-190 pair against
two MISO prunes and the ERCOT top-15 trade — not a widened span.* This line is
re-verified and republished every cycle because WS5 Job 1 found the public site
asserting its exact opposite for two weeks.

**Determinations: PJM, NEISO `CALIBRATED` · ERCOT (registered 3-yr), CAISO,
NYISO, MISO `NOT-YET` — with ERCOT's two designated configs each CALIBRATED on
their own spans.** **C3a appears in every NOT-YET fail set, and for CAISO and
MISO it is the ONLY failing criterion**; NYISO now adds only C3c (8/6/2/0,
C3b closed this cycle) and ERCOT's registered read adds C3b-2023 — both 2023
legs carved to the ECRS-era config on the ERCOT side. **The alignment position
changed even though only one determination did** — see F-4 and F-9.

## Workstream rollup

**WS1 and WS3 both moved this cycle — the first workstream motion in four
boards.** Verified rather than assumed over the full `69ae4dc7..54ca19ae`
window (**175 commits**): `git diff --name-status` returns **empty** for
`.github/workflows/`, and returns exactly **`M results/regression-goldens/
perfb-stage0/manifest.json`** (the Card-1 capture) and **`M docs/audit/
third-party-audit-2026-08.md`** (the O7 closure). Those two files are the
entire workstream-surface diff of a 67-PR window.

| WS | State | Completion | Blockers / next |
|----|-------|------------|-----------------|
| WS1 `AUDIT` | AUDIT-A **completed** (#3991). Rows **O8, O5, O4 CLOSED/RESOLVED**; **O6** is standing policy; 🟢 **O7 CLOSED this window** (#4377) — the Door-2 attribution harness built *and* exercised, HP-1 hash-proven bit-identical, keeper untouched | **In progress ~95 %** (was ~93 %) | **AUDIT-B still gated at G3 — waiting by design, and that gate is what caps this row**, not any remaining A-half work. O7's closure leaves no audit row carrying an owner action this board tracks |
| WS2 `DEBUG` | **COMPLETED** — DEBUG-A ✓, DEBUG-B ✓, pjm-162 promoted, landing-verify green on merged main | **Completed** | none; no DEBUG-C continuation chartered |
| WS3 `PERF` | PERF-A ✓. **PERF-B PAUSED BY OWNER.** 🟢 Stage-0: **6 of 6 ISOs captured** — PJM taken this window under Card 1. Changes (c)/(d)/(e) merged, (a)/(b) unstarted | **Paused ~78 %** (was ~74 %) | **Still paused, and still blocked TWICE at G2** — the capture was scoped by the card, which DECLINED the restart. 🟢 **1 of 6 goldens now matches its keeper** (PJM), ending six cycles at zero. 🔴 **NEW: the provenance defect changed shape** — `af1ccb6` was *overwritten*, not resolved, so five captures now carry a resolvable-but-wrong sha, and **five of six captures' provenance runs are absent from the registry** (F-5) |
| WS4 `DOCS` | DOCS-A **completed** (#3999 + #4005); DOCS-B held | **In progress ~60 %** | **DOCS-B gated at G2 — waiting by design** |
| WS5 `SITE` | **Job 1 (site factual repair, pre-G3) COMPLETE ACROSS BOTH PASSES** (#4120/#4121, #4187/#4191). Job 2 = **SITE-A**, not started | **Job 1 COMPLETED · Job 2 not started** | **SITE-A gated at G3 — waiting by design.** Deferral list unchanged |
| WS6 `BLOAT` | Prunes B-1..B-8 merged; **BLOAT-2 CLOSED**; **BLOAT-3 ADJUDICATED and EXECUTED** (BLOAT-S2, −444.5 MiB at tip). The chartered work stays completed | **Completed (charter) · gate 🟢 GREEN** | **🟢 GREEN at the pin** — `check_registry_payload_parity.py` **exit 0** (58 runs checked, 93 bundle dirs swept, 0 known-unsynced tolerated), holding across **four registrations and three prunes** this window plus a dedicated parity fix (#4401). The class-level carve-out (B-8) **still does not exist**; allowlist stands at **26** named entries |
| — `BENCH FRESHNESS` | `check_bench_freshness.py` / audit S1 lineage | **🟢 GREEN at this pin — 0 STALE of 20 parts AND 0 engine drift** | 🔴 **Read the drift clearing as an instrument artifact, not a repair — this was checked, not celebrated.** v15's six WARNs @ 15 commits are gone, and **nothing in the repository cleared them**: the ERCOT and NYISO bench parts and `check_bench_freshness.py`/`bench_stamp.py` are **byte-identical across `69ae4dc7..54ca19ae`** (only MISO's three parts moved, #4370), and re-running the checker's own arithmetic **at the v15 pin in this container reproduces 0 drift for all 20 parts**. The cause is the checker's day granularity: it takes the part's last-commit date via `--date=short` and then filters engine commits with `--since="<that date> 23:59:59"` **in the runner's local timezone**. Every bench touch and every engine commit currently sits inside the single calendar day **2026-08-30**, so the comparison collapses to zero. *(Corroborating: v15 reported drift on ERCOT+NYISO but not CAISO/MISO, though all four share the same last-touch commit `8990eee` — structurally impossible under this checker, so the v15 figure is not reproducible from committed bytes at the sha it was published against.)* **Expect the WARNs to re-appear on the first engine commit dated 2026-08-31 or later.** Not gated either way; regenerate before trusting a *marginal* C1 verdict |
| — `GOLDEN-TIER-FIX` | **COMPLETED and independently verified** (#4014); first cron RED, diagnosed + fixed same-day (#4071), verified by full local four-step replay | **Completed · tier PARKED** | **🅿️ PARKED BY OWNER RULING 2026-08-22, unchanged.** CI proof **deliberately unspent**. Consequence: byte-green cannot be CLAIMED for G2 while the tier is paused — **and the new PJM capture cannot be certified byte-green either** |
| — `MATRIX GUARD` | rule 26 `[R-MECH-MATRIX]` CI enforcement | **🟢 GREEN at this pin** | `check_mechanism_matrix.py` **exit 0**, run not quoted: integrity OK across the base file + **6 ISO shards**; anchors **194 field + 49 row + 151 path** (v15: 192/49/151 — the two new fields are the T1-H Leg-A pair), 0 unresolvable beyond the ratchet; **keeper stamps AND §5.x prose headers match every `keepers/<ISO>.json`**, held across the NYISO promotion |

## Stage-0 golden staleness (RECOMPUTED at `54ca19ae` — never read from a table)

Re-derived at the pin from `frontend/data/backcast/keepers/<ISO>.json` and
`results/regression-goldens/perfb-stage0/manifest.json` (`git_sha`
**`1cfea72`** — ⬅ **CHANGED this window; it resolves, and it is reachable in
`origin/main`**; `git_dirty: false`). Each captured bundle mapped back to its
keeper through the manifest's own `keeper_id` field, not by name.

**🟢 THE TABLE MOVED FOR THE FIRST TIME IN SEVEN CYCLES, AND ONE ROW IS
CURRENT.** **🔴 The consequence for G2 is nevertheless unchanged: byte-green
still cannot be CLAIMED, so G2 leg 1 keeps BOTH parked dependencies** —
WS3/PERF-B *and* the golden tier. Card 1 was a scoped capture, not a restart,
and it said so.

| ISO | Golden captured against | Provenance run in registry | Designated keeper at `54ca19ae` | Verdict |
|-----|-------------------------|---|--------------------------------|---------|
| **PJM** | 🟢 **`2026-08-15-pjm-162-inputclock`** ⬅ **CAPTURED THIS WINDOW** (#4369) | ✅ **PRESENT** | `2026-08-15-pjm-162-inputclock` | 🟢 **CURRENT — 0 promotions past capture.** The board's first non-stale row |
| ERCOT | `2026-08-15-ercot204-rule26-delete` | ❌ MISSING (pruned `e51a8a7d`, #4356) | `2026-08-25-234-eastex-identity` **+ 236 carve-out** | **🔴 STALE**, and full ERCOT coverage still needs **TWO** captures — the carve-out config has none |
| NEISO | `2026-08-14-neiso-93-envelope` | ❌ MISSING | `2026-08-17-neiso-99-joint-p1` | **STALE.** The re-stamp-not-re-solve shortcut was established for **neiso-97 only**; re-establish before relying on it |
| CAISO | `2026-08-16-caiso-197-w2-r5` | ❌ MISSING | `2026-08-26-caiso-220-c1-crosswalk` | **🔴 STALE** |
| MISO | `2026-08-16-miso-160-wefor-shape` | ❌ MISSING | `2026-08-30-miso-188-rvsscope` | **🔴 STALE — the deepest gap on the board** |
| NYISO | `2026-08-16-nyiso-140-layup-exclusion` | ❌ MISSING | ⬅ `2026-08-30-nyiso-159-loss-surface` | **🔴 STALE, and it DEEPENED this window** — the only gap that grew, by the cycle's one promotion |

**Count: 1 current / 5 stale / 0 without a golden — 1-of-6 effective coverage,
up from 0-of-6 held for six consecutive cycles.**

**On the promotion-gap counts, stated honestly rather than carried:** the
absolute "N promotions past capture" figures **are not re-derivable from
committed bytes at this pin**. The per-ISO keeper shards' git history begins
**2026-08-26** (the 2026-08-16 history rewrite plus the per-ISO shard split
truncated it), while the captures date 2026-08-14/15/16, and the shards'
embedded supersession chains reach only three deep. What **is** derived here:
each row's **verdict** (exact, from `keeper_id` vs the live `keeper`), the
**registry presence** column, and the **motion since v15** (NYISO **+1**, every
other ISO **+0**, byte-compared). v15's absolute figures — ERCOT six, MISO
eleven, NYISO ten, CAISO two, NEISO two — are **carried under v15's label, not
re-asserted as this board's measurement**; MISO's *eleven* was spot-checked
against that ISO's own calibration log and reconciles, and NYISO's becomes
**v15's ten + 1**.

- **PJM's seven-board line is retired**, and the reason it finally happened is
  worth keeping: **the capture was cheap because the keeper had been still for
  seven cycles** — exactly the condition the restart checklist says a
  re-capture pass needs, and the first time this board could report it.
- **🔴 "Which tree is the golden OF" is now WORSE-POSED, not better.** One
  top-level `git_sha` serves six captures taken at six trees, and it was
  rewritten to the newest capture's. **The per-file `content_hashes` remain the
  verification instrument** — the only one — and a re-capture pass should record
  provenance **per entry**, inside the manifest (F-5; checklist item 11).
- **The partition still adds a capture-coverage concept the manifest does not
  have:** one ISO, two designated configs. **A re-capture pass that takes one
  ERCOT golden is still not full ERCOT coverage.**
- 🟢 **New evidence bearing on checklist item 4:** nyiso-160's committed-bytes
  audit proved a *keeper* replays **bit-identically at HEAD** (max abs
  divergence 0.0 on every hourly-sidecar value column, all three years). That
  does not establish the re-stamp-not-re-solve shortcut for any golden — a
  golden is a capture of a *config at a tree*, not a replay — but it is the
  first same-HEAD reproducibility proof on this board since neiso-97, and it is
  the kind of evidence the shortcut would need.

## Gates

**All five re-run at the pin. Exit codes captured directly, never through a
pipe; outputs read, not quoted from any previous board.**

| gate | exit | reading at `54ca19ae` |
|---|--:|---|
| `audit_keepers.py` | **0** | **PASS — 0 failures, 0 warnings**, over `complete` = {NEISO, PJM}, held across the NYISO promotion |
| `check_registry_payload_parity.py` | **0** | **OK — 58 runs checked, 93 bundle dirs swept, 0 known-unsynced tolerated** (held across four registrations, three prunes and a dedicated fix) |
| `check_mechanism_matrix.py` | **0** | integrity OK, base + **6 ISO shards**; anchors **194 field + 49 row + 151 path** (+2 fields: the T1-H Leg-A pair); keeper stamps and §5.x headers match every shard |
| `check_forecast_staleness.py` | **0** | **Δ = 1 of 10** (WARN-level, never blocking) · **73 stamped / 41 scored** board-wide · **31 of 47 verdict stamps undated** · **20** distinct config epochs · board inputs **all present** |
| `check_bench_freshness.py` | **0** | **20 parts checked, 0 STALE, 0 engine-drift** — see the rollup's BENCH row before reading the drift clearing as a repair |

**Three readings moved since v15 and all three are cross-program or
instrument-side, not this program's:** staleness **Δ = 3 → 1** and **epochs
14 → 20** and **stamped/scored 59/27 → 73/41** (the forecast namespace absorbed
a large capx/FF window, including the crossover CO2 grain repair); bench
engine-drift **15 commits → 0** (the day-boundary artifact above). **The
persistent WARN is unchanged and is not the Δ: 31 of 47 verdict stamps record
no scored-at date**, so their freshness is UNKNOWN regardless of what the
newest scored one says.

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

- **🅿️ GOLDEN TIER — PARKED BY OWNER RULING 2026-08-22, unchanged for five
  cycles.** The #4071 fix is merged and locally replayed green; the CI proof is
  **deliberately unspent**. Record it as a park, not a blocker — and record the
  consequence, which now has a fresh instance: **the PJM golden captured this
  window cannot be certified byte-green either**, because the tier that would
  certify it is paused.
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
  (F-5). Only the capture taken *this* window has a registered provenance run.
  The registry-retention policy and the WS3 manifest reference the same run ids
  and **know nothing about each other**; every gate stayed green throughout,
  which is the point. **Do not "fix" this by exempting golden runs from
  retention** — that re-creates the parity gate's dead-bundle class.
- **🆕 THE BENCH-FRESHNESS ENGINE-DRIFT SIGNAL IS TIMEZONE- AND DAY-BOUNDARY
  DEPENDENT.** Its clearing this cycle was **not** a repair (rollup, BENCH row):
  the checker compares a `--date=short` last-commit date against
  `--since="<date> 23:59:59"` evaluated in the *runner's* local timezone, so
  any window in which bench touches and engine commits share one calendar day
  reads **0 drift**, and the same bytes read differently from a container in a
  different timezone. The gate is ungated by design and this does not change
  that — but **do not read "0 engine drift" as evidence the benches are fresh**,
  and expect the WARNs back on the first engine commit dated past the parts'
  last-touch day.
- **🟠 CARRIED, AND PARTLY ANSWERED — EVIDENCE PROSE IS GATE-CHECKED NOWHERE.**
  The class is unchanged: `check_mechanism_matrix.py` validates `keeper:` stamps
  and §5.x prose headers and passes while citation text beside them goes stale.
  🆕 **The first machine-readable answer appeared this window** — Card 4's
  execution added a `frontier.withdrawn` mirror **specifically so the
  dashboard's `frontierActive()` suppresses a badge**, i.e. a rendering-drift
  gap closed at the renderer rather than in prose (F-4). One field, one ISO, by
  hand. **Whether any gate should read evidence text remains unruled.**
- **🟠 NEW — THE FORECAST SEED CARRIES TWO READINGS AT ONCE AGAIN.** F-9. Its
  top-level `gate_reading` prose says *"nobody holds three"* while its own
  per-ISO `gate` block records NEISO holding three — the same defect class the
  D13 reconcile lane was raised to repair, re-appearing inside one window
  because prose and data move at different cadences. **A different program's
  file; recorded, not adjudicated.** The per-ISO blocks are the authority, and
  this board derives gate (a) from them plus the live shards, never from the
  prose.
- **🟠 NEW — THE LANE THAT MOVES A KEEPER DOES NOT RE-STAMP THE FORECAST SEED.**
  F-9. v15 praised the inverse pattern (the Q5-W lane re-stamped NYISO when it
  moved the marker). Two hours later the nyiso-159 promotion re-staled that same
  stamp, taking the seed from three stale to **four**. Not a defect in either
  lane — nobody owns the cross-program stamp — which is exactly why it recurs.
- **🟢 RETIRED — the four-instrument divergence.** v15's newest watch item is
  closed by Card 4: all four instruments agree at **{PJM, NEISO}** (F-4/F-9).
  What stays is the *structural* half, and it is unchanged: **nothing in the
  repo compares them.** `audit_keepers.py` checks marker/keeper re-keying, not
  frontier membership. The board keeps re-deriving all four every cycle because
  that is the only check there is.
- **🟠 CARRIED — the standing parity-gate hazard.** The gate still reports a
  LIVE lane's pre-registered control/recipe dirs as "dead solve output"; before
  reporting a future parity red, check whether the named dirs belong to a
  running lane — **never recommend pruning a dir a live lane owns.** It went
  live again this window (#4401 was a caiso-224 parity fix) and the class-level
  carve-out (B-8) **still does not exist**; the allowlist stands at **26**
  named entries.
- **🟠 CARRIED — FORECAST-BOARD STALENESS.** Δ = 1 of 10 at the pin (down from
  3). What stays on watch is unchanged and is not the Δ: **31 of 47 verdict
  stamps are still undated** (they predate the stamped scorer — freshness
  UNKNOWN until each passes through it) and **20 config epochs** now sit on the
  board (up from 14); confirm mixed-vintage comparison is intended before
  reading any cross-run delta as a model effect.
- **🟢 PARTLY RETIRED — the cross-ISO scorer-change precedent.** Card 3 gives
  the class a standing rule (F-3): re-verify from committed artifacts before a
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
  re-deriving the stage-0 table is what found the five-wide prune (F-5) and the
  overwritten provenance sha. **The new half is the bench row** — a gate whose
  reading *improved* was worth the same scepticism as one that degraded, and
  checking it found an instrument artifact rather than a repair. **A green that
  arrives without a cause is a measurement you have not made yet.**

## Forecast board — re-derived at `54ca19ae`: gate (a) unchanged in membership, legs (b)/(c) SCORED for the first time

**Re-derived, not carried — and the seed's schema was re-read rather than
assumed.** `frontend/data/forecast/program-status.json` was **restructured this
window** by the capx desk (it now carries `gate_reading`, `readiness`,
`gate_a_provenance`, `d13_board_reconcile`, `d5r_co2_grain_repair` and three
more per-lane record blocks). Every `gate.a_keeper_marker.detail` was compared
field-by-field against the live `keepers/<ISO>.json` and the live `complete`
block at the pin; legs (b)/(c)/(d) are read from each ISO's own `gate` block.

| ISO | Seed names (gate a) | Live keeper | (a) | (b) | (c) | (d) |
|---|---|---|---|---|---|---|
| ERCOT | `2026-08-24-231-tie-zone-measured` | `234-eastex-identity` (+ 236) | **fail** — no `complete` marker, stamp **STALE** | fail | pass | none |
| PJM | `pjm-162-inputclock` | same | **pass — current** | fail | pass | none |
| CAISO | `2026-08-17-caiso-200-h1-memberpanel` | `caiso-220-c1-crosswalk` | **fail**, stamp **STALE** | fail | fail | none |
| NYISO | `nyiso-157-par-attribution` | ⬅ `nyiso-159-loss-surface` | **fail** (marker withdrawn), stamp ⬅ **NEWLY STALE** | pass | pass | none |
| NEISO | `neiso-99-joint-p1` | same | **pass — current** | pass | pass | none |
| MISO | `2026-08-22-miso-177-rho-measured` | `miso-188-rvsscope` | **fail**, stamp **STALE** | fail | pass | none |

**Gate (a) passers = {PJM, NEISO} = exactly the `complete` set — unchanged in
membership from v15**, and now equal to the CALIBRATED set and the `frontier`
set as well (F-4).

**🟢 Legs (b) and (c) are SCORED for the first time on this board** (v15:
UNSCORED). **NEISO holds (a)+(b)+(c) — the first ISO in program history to hold
three legs.** Three ISOs hold two legs by different pairs; CAISO holds none.
**But `open` is `false` for all six and leg (d) is `none` everywhere: NO ISO'S
FULL-SOLVE AUTHORIZATION GATE OPENS, and none opened from this refresh.** The
legs that moved moved on the owner's **Q7 ruling about what leg (c) measures**
(FC-4 measured and reported, never in-band) and on NEISO's first T1-X — **not
on any improvement in the model** — and every FC-4 behind a passing leg (c) is
itself a **FAIL reported at full magnitude**. That is the honest reading and
the seed states it in those terms.

**🔴 Seed staleness went from three stale stamps to FOUR**, NYISO newly stale
by its own promotion (F-9). **🟠 And the seed carries two readings at once
again** — its top-level prose says nobody holds three legs while its per-ISO
blocks say NEISO does (Watch). Both recorded; **neither adjudicated — the
forecast namespace is a different program's.**

**No forecast run was solved or re-scored by this lane**; per rule 15
`[R-DASHBOARD]` the forecast namespace is registered through
`scripts/register_forecast_run.py` alone, and the backcast CI gates stay blind
to it.

## Owner queue at cycle end

Re-served and re-verified at **`54ca19ae`**. **The 2026-08-30 decision-card
sitting retired THREE carried items by ruling, all now EXECUTED and verified**
(Card 4 → item 1; Card 3 → item 5; Card 2 → item 6). What remains, **with three
NEW items, all three arising from work the cards themselves commissioned**:

1. **🆕 NEW — ARM THE T1-H STORAGE-ENTRY REPAIR, OR DON'T. The A/B is on the
   record and the decision is explicitly the owner's.** Card 2's charter
   reserved arming to the owner *on the A/B record*, and that record now exists
   (F-2): both kill-gates PASS, the arm reproduces the pre-registered
   signature byte-exact, both `ScenarioConfig` fields ship **default-OFF**, and
   both ERCOT matrix cells read **`O` — measured, ARMING OPEN**. The couplings
   are measured and stated in both directions (reserve-margin path down, no
   downstream decision flips; co2 −0.49/−0.52/**+0.34** Mt). **Nothing else is
   owed before this can be decided** — it is a one-bit call on a complete
   record. *(This board takes no position on which way.)*
2. **🆕 NEW — THE C-1 WIND SIGNAL-OBJECT CALL, with its measured input
   delivered.** T1-H Leg B measured that the dual-based signal object closes
   **8.87 %** of the wind entry miss and leaves **91.1 %** open, while the same
   run's terminal reserve margin *worsens* 25.19 → 40.24 % and its gas_ct and
   storage bands move the other way. **The lane proposes no lever and says so.**
   The servable question is narrow: **is the dual-based signal the right signal
   object for `entry_lookahead_reprice` in ERCOT, on an 8.9 % closure with those
   couplings?** Note for whoever answers: signal (+1.092 GW) and volume (D11-R
   exhaustion, +0.604 GW) are two partial closures that **have never been
   measured together and are not additive by construction** — both act on the
   same shared queue budget.
3. **🔴 CALIBRATION FREEZE / WS3 RESTART — THE G2 GATE — DEFERRED BY OWNER
   DIRECTION, so G2 stays parked BY CHOICE, NOT BY DRIFT.** 🆕 **The question
   is materially smaller than it was, because Card 1 answered part of it by
   demonstration:** a capture was taken **inside a 67-PR window** without a
   freeze, in a lane whose keeper happened to be still — so **a freeze is not a
   precondition for a scoped capture**, and the remaining question is only
   about the **five stale rows** (and ERCOT's second config, which has no
   golden at all). v15's "zero promotions" datum was one point, not a trend, as
   it warned: this window promoted once and ran thirty calibration PRs. The
   standing recommendation is unchanged: **a scoped, time-boxed decision taken
   TOGETHER with the golden tier's disposition** — 🆕 now with the *per-entry
   provenance* repair attached (F-5) rather than the `af1ccb6` resolution step,
   which was overtaken by being overwritten.
4. **🟠 NEISO `final` GRANT — DATA-BLOCKED.** The 2025 EIA-923 FINAL vintage has
   **still not landed**; until it does the grant question is not servable on the
   merits. Standing and re-verified at the pin: **no ISO has ever spent a
   locked-test year** (58 sidecars walked, {≤2018, 2019, 2026} returns NONE),
   NEISO's one-shot is **NEVER GRANTED, not spent** (D-23), and the freeze is
   tier-scoped to the locked test for every ISO. Data intake needs no
   authorization (rule 22) — the block lifts itself when the vintage publishes.
5. **⚪ DORMANT — the ERCOT rule-16 waiver qualifier.** Bounded by the Card-2
   implementation of v14 (the coverage invariant + both configs' records
   published at full magnitude); **re-fires only if the carve-out structure
   changes.** Not servable while dormant; recorded so it is not lost.
6. **🟠 CARRIED, DISPOSITION UNCHANGED AND RE-EVIDENCED — the CAISO NOT-YET
   determination.** **TERMINAL REST + MAP** stands (R-3, v15 E-3): the C3a
   residual is attributed and closed at this representation grain, with
   W-1/W-2/W-3 armed as the **only** sanctioned re-checks. 🆕 **caiso-225 ran
   exactly that sweep and it came back ALL NULL** (#4425, zero solves): W-1,
   W-2, W-3 and the F2 derate all still blocked; A3's SoCalGas OFO record is
   **available and feasible but unfunded** (new filed item 10); nothing fires;
   no intake charter opens; keeper/matrix/markers untouched. **Terminal rest is
   re-affirmed on evidence rather than by default**, and the dated next-sweep
   trigger is Order 881 AARs, effective ≤ 2026-12-01. C3a-2024/2025 still fail
   at **+12.5 % / +15.5 %** and owner ruling 5 stands: **C3a must genuinely
   pass; NOT-YET is the honest fallback.** Nothing is owed here.
7. **🆕 NEW — THE nyiso-161 WINTER-FACE WAIVER CARD IS FILED AND UNANSWERED.**
   ⚡ **Past the dispatch, and it replaces the item the dispatch expected.** The
   dispatch listed the **nyiso-leg2** winter-locational candidate as *awaiting
   owner promote-or-archive at the calibration desk*; at this pin that branch is
   **deleted** and the lane resolved differently: **nyiso-160 STOPPED Leg 2
   WITH CAUSE at access** (the MyNYISO AORR artifacts never landed; the owner,
   asked in-session, answered *"Cannot produce them"*), so with Leg 1 executed
   and its companion closed on measurement, **the winter face of C3a-2025 is
   identification-blocked on both legs** — determination consequence **none**,
   **no matrix cell verdict moves**, re-open conditions are the nyiso-97 ones
   verbatim. **nyiso-161 then filed an owner-ordered winter-face waiver decision
   card, which is what is actually pending.** Both states recorded; this board
   adjudicates neither.
8. **🟠 CARRIED NOTE — the nyiso-148 2025 dear-gas level card**: no signature or
   decline recorded for it in any window since; its same-day UPDATE block should
   be read before its numbers (the keeper it names is now **six** promotions
   superseded, 148 → 152 → 155 → 157 → 159).
9. **🟢 RETIRED THIS CYCLE (v16) — do not re-serve:**
   - ~~**does a ratified `frontier` need a currency rule?** (v15 item 1)~~ —
     **ANSWERED BY CARD 4 AND EXECUTED**: the NYISO ratification is reverted,
     all four instruments align at {PJM, NEISO}, and the standing rule is
     **marker-master** — a frontier does not survive its ISO leaving
     CALIBRATED/`complete` (F-4).
   - ~~**rule on the cross-ISO scorer-change precedent** (v15 item 5)~~ —
     **RULED BY CARD 3 AS A STANDING RULE**: RE-VERIFY REQUIRED, recorded in
     `docs/calibration-log/governance.md` (F-3). The pre-rule nyiso-143 instance
     stays on Watch, unadjudicated.
   - ~~**the T1-H capacity-entry defect has no charter and no home** (v15 item
     6, v13 item 11 — homeless three boards)~~ — **CHARTERED BY CARD 2 AND RUN
     TO A MEASURED A/B THE SAME DAY** (F-2). It leaves behind items 1 and 2
     above, which are decisions rather than homelessness.
   - ~~**the miso-190 registration watch**~~ — **CLOSED**: both sidecars are
     committed (#4370). Not an owner item; retired here because it ran three
     cycles on this board.

## Session roster

> **🟠 v16 STATES ITS OWN LIMIT, as v15, v14 and v13 did.** This records lane is
> **not** the director desk and holds no session-listing authority, so it did
> **not** run `list_sessions`. Lane state below is derived from **git**
> (`ls-remote` branch tips, each tip tested for ancestry inside `origin/main`
> rather than read off the listing) plus one **live `list_pull_requests`** call
> at the pin. No row is carried from v15 or from the dispatch unverified.

### Lane state at `54ca19ae`, derived from remote branch tips + live PR list

**ONE pull request is open and ONE branch is ahead of `main`** — and they are
the same lane, which is **not this program's**. `ls-remote` returns exactly
**two** heads (`main` and one other); the non-`main` tip failed the
`merge-base --is-ancestor` test and is +2 ahead. **No audit-program lane is
running at this pin**; this records lane is the only one, and its branch is not
yet pushed at the time of measurement.

| Lane | Branch | State at the pin |
|---|---|---|
| **Records v16 (this lane)** | `claude/audit-records-v16-refresh-r3qa3z` | **🟢 WORKING** — the two chartered files; branch cut fresh off `origin/main` at the pin, so its pack carries only this session's objects |
| **capx D12-A arming** — **A DIFFERENT PROGRAM** | `claude/capx-d12a-arming-0ibtzh` | **🟢 LIVE — +2 ahead, PR #4424 OPEN** (created 2026-08-30T23:52Z): arms `entry_margin_exhaustion` + `entry_forward_reserve_leg` as ERCOT **forecast** defaults (Q15) and stamps the ERCOT matrix shard. **Not this board's work** — recorded because it is the only live lane in the repo and because it touches an ERCOT matrix shard this board reads |
| **Director desk (card execution)** | `claude/model-audit-program-director-1wz2n7` | **MERGED, BRANCH DELETED** — #4369 (Card 1 capture + Card 2 Phase-0 + Card 3 governance entry + Card 4 revert) and #4386 (matrix rows + the T1-H storage-entry fields). The one-sitting deviation supersession (F-10) |
| **T1-H capacity entry (Card 2, Phase-1 Leg A)** | `claude/t1h-storage-entry-ab-mk10lx` | **MERGED, BRANCH DELETED** — #4419 + #4426. Both kill-gates PASS, cells `U → O`, **nothing armed** (F-2) |
| **O7 attribution harness** | `claude/o7-attribution-harness-fjuvgd` | **MERGED, BRANCH DELETED** — #4368 + #4377. **Audit row O7 CLOSED** (F-6) |
| **Records v15 (predecessor)** | `claude/audit-records-v15-refresh-ob75pb` | **MERGED, BRANCH DELETED** — #4365, inside this window (which is why the v16 cycle span contains v15's own landing) |
| **MISO backcast calibration (miso-190)** | `claude/miso-190-backcast-calibration-okt1cn` | **MERGED, BRANCH DELETED** — #4370. **The three-cycle registration watch CLOSES**: both sidecars (`-control`, `-ppexit`) are committed and were verified present at the pin, not inferred from the merge |
| NYISO 159/160/161 arc | `claude/nyiso-run-159-backcast-ejyvn8`, `claude/nyiso-leg2-winter-locational-wymoa4`, `claude/nyiso-161-backcast-calibration-qha5am` | **ALL MERGED, BRANCHES DELETED** — #4363/#4378 (159, the cycle's one promotion), #4385/#4393 (160: **Leg-2 stop with cause** + the bit-identical touchpoint-prep audit), #4420 (161: owner-ordered waiver card) |
| ERCOT 242/243/244/245 | `claude/ercot-242-sced-phase1-sb3zj7`, `-243-release-exit-r7owkv`, `-244-online-cap-xi7kvo`, `-245-commitment-state-bzqneg` | **ALL MERGED, BRANCHES DELETED** — #4371/#4380 (242 registered), #4383 (243 killed at census), #4404/#4407/#4411/#4412 (244 killed at census), #4417/#4421 (245 Phase-0) |
| CAISO 224/225 | `claude/caiso-backcast-next-run-5u7ob7`, `claude/caiso-224-fsno-finisher-sa7uox`, `claude/caiso-225-watch-sweep-2ruedq`, `claude/ci-parity-caiso224-bundles-xfpsek` | **ALL MERGED, BRANCHES DELETED** — six + one + one + one PRs; **caiso-225's sweep ALL NULL**, terminal rest re-affirmed |
| MISO 191 / M2M intake | `claude/miso-191-binning-aware-exit-8kloqx`, `claude/miso-m2m-flowgates-raw-u47nkt` | **MERGED, BRANCHES DELETED** — #4379/#4384, #4409. ⚡ Past the dispatch, which had miso-191 "in flight" |
| Crossover CO2 grain repair | `claude/crossover-co2-grain-repair-oycsy6` | **MERGED, BRANCH DELETED** — #4388 |
| capx lanes — **A DIFFERENT PROGRAM** | `claude/capacity-expansion-director-*`, `claude/capx-*`, `claude/calibration-workstream-relaunch-bml7zm` | **THIRTY merged PRs this window**, spanning refreshes #13–#20 and lanes D5/D5-R/D8/D12/D12-C/D13/D14/D16/S-1..S-6/T3/neiso-rc. **Not this board's work**, per the standing conflation warning. Recorded here only because (i) the volume would dominate any commit-list scan, (ii) #4388/#4403 moved the forecast board's co2 magnitudes this board reads, and (iii) #4424 is the only open PR in the repo |

**The honest reading: the branch check did its job in both directions again,
and it had thirty decoys to survive.** Every lane this cycle's PRs imply was
found as a branch or as a deleted branch with merged PRs behind it; nothing was
assumed launched without one; and the single live lane was found by **ancestry
testing**, not by reading the `ls-remote` listing (which shows `main` itself as
a row and would have been misread). **The capx desk merged thirty PRs — the
exact class of plausible-sounding commits that would fool a commit-list
scan** — of which two genuinely touched surfaces this board reads and
twenty-eight did not.

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
under an **explicit one-sitting owner supersession** (F-10). That supersession
is **spent**; the standing deviation governs again, and this lane is its
dispatched instrument. A future sitting that wants to write directly needs its
own supersession — the 2026-08-30 one does not carry forward.

**v16's protocol amendments — one near-miss caught, one rule extended:**

- **🟠 THE DISPATCH-VS-LAUNCH CHECK CAUGHT A NEAR-MISS FROM THE OTHER
  DIRECTION.** For two cycles the check asked *"was a dispatched lane actually
  launched?"* This cycle the failure mode was upstream of that: **the prior
  director session archived before issuing this dispatch at all**, and the
  **2026-08-31 director startup** caught it and dispatched. **Record it as a
  near-miss caught by startup, not a failure streak** — and add the question to
  the checklist: *did the last sitting's records duties get dispatched, or did
  the session end holding them?* A sitting that executes in-session under a
  supersession (F-10) is exactly the shape that can leave the **next** cycle's
  dispatch unissued, because nothing is left obviously outstanding.
- **🔴 PIN ONCE, THEN RECORD MOTION — held, cheaply, for the first time.**
  `origin/main` advanced **once** while this lane was measuring
  (`ee75a0b` → `54ca19ae`, #4427 + #4428), then **held stable across four
  polling rounds** before the pin was taken. Every volatile check was run at
  that pin. **And the dispatch-vs-pin delta was measured rather than assumed**:
  `git diff ee75a0b..54ca19ae` touches only `docs/handoffs/capx-director-*`, so
  the director's derivation and this board's pin agree on every figure — which
  is itself the second labelled state, and a short one.
- **🆕 EXTENDED — RE-DERIVE THE READING THAT *IMPROVED*, NOT JUST THE ONE THAT
  "CANNOT HAVE CHANGED".** v15's amendment (re-derive the stable table) paid
  again: it surfaced the five-wide prune and the overwritten provenance sha
  (F-5). **The new half:** the bench gate's six engine-drift WARNs **cleared**,
  and the dispatch asked what cleared them rather than celebrating. The answer
  is **nothing in the repository did** — the parts and the checker are
  byte-identical across the window, and the checker's own arithmetic re-run at
  the *v15* pin in this container reproduces 0 drift for all 20 parts. It is a
  timezone/day-boundary artifact of the instrument. **A gate reading that gets
  better deserves the same re-derivation as one that gets worse; a green with
  no cause is a measurement not yet made.**
- **🆕 ADDED — READ A RESTRUCTURED FILE'S SCHEMA BEFORE READING ITS VALUES.**
  The forecast seed was restructured by another program inside this window
  (F-9). Reading it with v15's field expectations would have silently missed
  that legs (b)/(c) are now scored and that NEISO holds three. **Re-read the
  key set, not just the keys you used last time.**

**Carried, restated in one line each** (full text in v10–v15): run the gates,
never quote them (exit codes captured directly, not through a pipe) · quote no
cycle count without its base sha, in the dispatch and on the board · trust no
table, including the dispatch's — re-derive from committed bytes at the pin ·
**look for the BRANCH, not a plausible-sounding commit** (thirty capx PRs this
window) · a refresh is complete when the sessions exist, not when the prompts
are written · read a content-addressed identity before inferring · **confirm
`frontend/data/hindcast/` is present before quoting any stamped/scored count**
(done this cycle: `check_forecast_staleness.py` reports *board inputs: all
present*) · **say which figures are derived and which are carried** — this
board's stage-0 promotion-gap counts are the current instance, and they are
labelled rather than silently re-asserted.

**While the program is parked, the refresh cycle is not the live instrument it
was.** A park-period refresh confirms (a) whether the owner has ruled on
anything in the queue — **four decision cards, ALL EXECUTED this window**;
(b) whether the keeper freeze has been called — **still deferred, and Card 1
shrank the question by taking a capture without one**; and (c) whether the
golden tier's park has been lifted — **unchanged, and the CI proof stays
deliberately unspent, which is why even the new PJM capture cannot be certified
byte-green**.

## RESTART CHECKLIST — for whoever un-parks the program

**Do these in order. Do not start at change (a).**

0. **🟢 `main` IS FULLY GREEN AT THE v16 PIN — re-run at `54ca19ae`, not
   quoted: ALL FIVE CHECKS PASS.** `audit_keepers.py` **PASS 0/0** ·
   `check_registry_payload_parity.py` **exit 0** (58 runs / 93 dirs / 0
   tolerated) · `check_mechanism_matrix.py` **exit 0** (194 field + 49 row +
   151 path anchors) · `check_forecast_staleness.py` **exit 0, Δ = 1/10**
   (WARN-level; the 31/47 undated-stamp WARN persists) ·
   `check_bench_freshness.py` **0 STALE of 20, 0 engine drift** — but read the
   rollup's BENCH row before trusting that last figure: **the drift signal
   cleared by day-boundary artifact, not by repair.** Green for a third
   consecutive cycle. **Always re-run all five rather than reading this line**;
   at this repo's merge cadence (67 PRs in under five hours this window) the
   reading ages in minutes.
0b. **🔴 THE GOLDEN PROVENANCE PROBLEM CHANGED SHAPE AND IS NOW HARDER TO SEE.**
   The manifest's `git_sha` **resolves** (`1cfea72`, reachable in main) — but it
   was **overwritten by the PJM capture, not resolved**, and the manifest holds
   **one** top-level sha for **six** captures taken at six trees, with **no
   per-entry provenance field**. So the five older captures now carry a sha that
   is *valid and wrong*. Separately, **five of the six captures' provenance runs
   are ABSENT from the registry** (only PJM's is present) — a five-wide
   condition, not the one-off v15 reported (F-5). Neither was caused by error;
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
   `54ca19ae` the answer is: PJM CURRENT, the other five STALE, ERCOT needing
   TWO captures (forward + carve-out), and five of six capture provenance runs
   unregistered.**
4. **Assume every re-capture is a real solve — and budget the memory.** The
   Card-1 capture died first on the container's **13.3 GiB cgroup RAM limit**
   (memcg OOM at 13.9 GB RSS) and succeeded only after a **12 GB swapfile**; it
   also needed a re-fetch of the converted `pjm-da-virtuals` corpus, whose
   loader hard-fails rather than no-ops. The **re-stamp-not-re-solve** shortcut
   was established for **neiso-97 only** — re-establish it before relying on it;
   re-derive the config diff first. 🆕 nyiso-160's committed-bytes audit (a
   *keeper* replaying bit-identically at HEAD, max abs divergence 0.0, all three
   years) is the first fresh evidence of the kind such a shortcut would need,
   though it proves a replay, not a capture.
5. **~~Capture PJM FIRST~~ — DONE (#4369). Capture MISO next.** MISO carries the
   deepest promotion gap on the board and its keeper has now been still since
   2026-08-30; NYISO's gap deepened again this window. **ERCOT still needs
   two.**
6. **Do NOT re-do change (c).** It landed via #3964 and is byte-identical at
   HEAD. Verify the blob (`af34031c`) rather than re-porting it.
7. **Close the #4054 residual if you want belt-and-braces — but re-derive it,
   do not inherit it.** The NYISO keeper is now **eleven** promotions past the
   captured nyiso-140 config (v15's ten, plus this cycle's one).
8. **Then, and only then, resume changes (a)–(e)** — and re-read the G2 leg
   list, because *merged byte-green* is what the gate wants, not captures.
   **Card 1 is a capture, and captures do not close leg 1.**
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
