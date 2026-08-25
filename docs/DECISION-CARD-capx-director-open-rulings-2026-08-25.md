# DECISION CARD — capx director: three open owner rulings (leg-(c) consistency · ERCOT entry-signal default · PJM requirement horizon-edge)

> Status: **SIGNED — 2026-08-25.** All three cards signed by the owner **at the recommendation**
> (A-A, B-C, C-A). See §5 RESOLUTIONS for the decisions and the consequences adopted with them.
> The card body below is preserved **as put**, unedited.

**For the owner. Capacity-expansion director session, 2026-08-25, HEAD `99c8cf5`.
NOTHING IS DECIDED HERE.** This card performs **zero new measurements**: every number is read
from a committed artifact named beside it. No LP, no solve, no probe, no mechanism, no matrix
cell verdict (rule 28(b) — nothing tested), no dashboard change, no keeper touched.

Scope: the **forecast** track only. No backcast keeper, marker, `status/*.js`,
`calibration-complete.json`, offer curve or commitment bridge is implicated by any option on any
card. Rule 22 `[R-HOLDOUT]`: the holdout spend freeze is ACTIVE, `final` is empty, and nothing
here proposes solving, scoring or registering an out-of-training backcast year. Forecast-mode
2026+ runs, which two options below would charter, are unrestricted by construction.

**Why these three are on one card.** Each is a decision the director cannot take: A and C change
a **gate outcome**, B sets a **shipped forecast default**. All three became live in the same
cycle, and A is now on the program's critical path.

---

## 0. THE BOARD

| card | decision | blocking? | recommendation |
|---|---|---|---|
| **A** | Gate leg (c): three ISOs have no T1-X run. NEISO is scored `fail` on that basis; CAISO and NYISO still read `na`. Harmonise — and if so, in which direction? | **Blocks the program's first gate opening (NYISO)** | **(A-A)** apply the NEISO reading uniformly, then charter NYISO's T1-X so leg (c) closes on measurement |
| **B** | Arm the `entry_lookahead_reprice` **disarm** as the ERCOT forecast default? | Blocks nothing; sets a shipped default | **(B-C)** hold the shipped default AND charter the developer-pro-forma construction as its successor |
| **C** | PJM's beyond-last-published-FPR requirement convention: hold-last vs the stale composite. | Blocks S-5/S-6 (PJM's whole I7 lane) | **(C-A)** adopt hold-last-FPR, bundle the D-1 checker repair, and re-score |

---

## 1. CARD A — gate leg (c), and why it stopped being cosmetic

### 1.1 What changed under it

**NYISO cleared FC-1 on 2026-08-25.** The D2-NYISO-INTAKE lane added NYISO to
`ADEQUACY_EXTERNAL_TIE_FIRM_MW` at its own published external capacity (2026 Gold Book Table V-1,
3,168.5 MW ICAP × the published NYCA ICAP→UCAP factor 0.8679 = **2,749.9 MW UCAP**), and the
re-scored leg `nyiso-2026-2030-extcap-capxd2` reads **14/14 invariants PASS, FC-2 PASS,
determination HOLD → PROMOTE-WITH-CAVEATS**
(`docs/handoffs/FINDING-capx-d2-nyiso-extcap-2026-08-25.md` §0, §4).

That finding's §7 states the position directly: *"gate (a) already held (marker + keeper
`2026-08-22-nyiso-152-duty-complete`, CALIBRATED); gate (b)'s FC-1/FC-2 now PASS on the bare
`nyiso-t1f` key."*

**NYISO's §2.1b gate therefore reads (a) PASS · (b) PASS · (c) `na` · (d) none.** It is the first
ISO in the program to clear both legs that depend on model quality. Leg (c) is now one of the two
things left — so a cell that was cosmetic while every gate was closed elsewhere is now
load-bearing.

### 1.2 The inconsistency, stated exactly

Charter §2.1b(c) requires **both** FF-3E readiness **and** the T1-X crossover input gap (FC-4)
*measured and reported* for the ISO. Three ISOs have **no T1-X run at all** — no `<iso>-t1x` key
exists in `ff-verdicts.json` and FC-4 reads `n/a` in every one of their verdicts:

| ISO | leg (c) as scored today | basis |
|---|---|---|
| NEISO | **`fail`** | neiso-88 (2026-08-06): *"NEISO has NO T1-X crossover run … only the readiness half is green, so the leg does not pass."* |
| CAISO | `na` | board detail: *"not run (FF-2D scope)."* |
| NYISO | `na` | board detail: *"not run."* |

Same fact pattern, two different scores. The capx-D1 refresh found this and **escalated rather
than edited it** — applying the NEISO reading moves two gate legs, which was outside a
records-only remit (`FINDING-capx-d1-board-refresh-2026-08-23.md` §5, recorded in the board's own
`d1_board_refresh.escalated_not_edited` field so it could not be lost between sessions).

### 1.3 The options

**(A-A) Harmonise to `fail`, then close NYISO's on measurement — RECOMMENDED.**
CAISO and NYISO move `na` → `fail`, `"c"` is added to both `closed_on` lists, and the director
charters a **NYISO T1-X crossover run** so leg (c) closes on a measured FC-4 rather than on an
unscored cell. Consequences to adopt with it:
  - The program's lead ISO is gated on something **actionable** — a run — rather than on an
    ambiguity.
  - NEISO's and CAISO's legs stay `fail` until each gets its own T1-X; that is the honest
    reading, not a penalty.
  - Nothing else moves: all three gates are already `open: false` on other legs, so **no ISO's
    schedulability changes on the day of signature.**

**(A-B) Harmonise to `fail`, charter nothing.** Identical scoring change, no run chartered.
NYISO's gate then sits on (c) with no lane closing it. Choose this if you want the board honest
but the bandwidth spent elsewhere.

**(A-C) Harmonise the other way — `na` for all three, including NEISO.** Semantically defensible:
an unrun leg is *not-yet-assessed*, not *failed*, and `na` says so. But it makes leg (c) **silent**
rather than failing, which weakens the gate: an ISO could reach (d) owner authorization having
never measured its crossover input gap — the precise thing §2.1b(c) exists to require. Recommended
against for that reason, and it would also reverse an adjudication (neiso-88) that no new evidence
disturbs.

**Recommendation: A-A.** It is the reading already adjudicated once, applied uniformly, and it
converts the lead ISO's blocker into a chartered run.

---

## 2. CARD B — the ERCOT `entry_lookahead_reprice` disarm as a shipped default

### 2.1 The record

The ERCOT entry-signal disarm probe adjudicated the cell **fc K → O** and **refused to
self-adopt**, routing the arming decision here in its own words (commit `2aaaffa`):

> *"fc K → O, with the disarm probe's evidence. Not R and not a promotion: the disarm repairs
> measured signal defects L-1 attributed to this mechanism (locational dispersion where the
> shipped object is zone-flat by construction, steady long-duration storage entry, wind entering
> at all), but it trades a forward-looking-but-structurally-wrong object for a
> structurally-right-but-backward-looking one, and it worsens the terminal reserve margin
> 25.19 → 40.24 %. Neither construction is the developer pro-forma, so rule 1 cuts both ways here:
> the cell is not flipped because bands improved, and not held because one worsened. **Arming the
> disarm as the lane default is the owner's decision.**"*

`entry_lookahead_reprice=True` is one of the FF-2C shipping posture flips
(`program-status.json::flip_config`), so this is a **forecast-track default**, not an ERCOT
backcast question — it does not touch the ERCOT 2023 arc that card Y left open.

### 2.2 What makes it a genuine fork

Both constructions are known to be wrong, in opposite ways:

| | shipped (lookahead armed) | disarmed |
|---|---|---|
| entry signal | forward-looking | backward-looking |
| structural fidelity | **wrong** — zone-flat by construction | **right** on locational dispersion |
| measured L-1 defects | present (no dispersion, no steady LDS entry, wind absent) | repaired |
| terminal reserve margin | 25.19 % | **40.24 %** |
| is it the developer pro-forma? | **no** | **no** |

Rule 1 `[R-STRUCT]` forbids picking either on band movement. Neither is the object a developer
actually clears an investment against, which is what the entry screen is trying to represent.

### 2.3 The options

**(B-A) Arm the disarm as the ERCOT forecast default.** Buys the measured L-1 repairs
(dispersion, LDS, wind) at the cost of a backward-looking signal and a terminal reserve margin
that nearly doubles. Defensible under rule 1 if you weigh structural fidelity of the *locational*
object above the horizon-end artifact.

**(B-B) Hold the shipped default; the cell stays `O`; charter nothing.** Zero cost, zero movement.
The named L-1 defects stay live and un-repaired.

**(B-C) Hold the shipped default AND charter the developer-pro-forma construction as the named
successor — RECOMMENDED.** The probe's own sentence — *"neither construction is the developer
pro-forma"* — is the finding. Adopting either known-wrong object as a *default* ratifies it;
building the object the screen is meant to represent is the rule-1 move, and the L-1 measurements
already tell that lane exactly what it must reproduce. Cost: one chartered lane. Fallback if
bandwidth is tight: B-B, which is the same posture without the successor.

**Recommendation: B-C.** B-B is the acceptable low-cost variant of it; B-A is the one I would not
take without the pro-forma question being asked first, because it makes a default of a
construction the probe itself declines to endorse.

---

## 3. CARD C — PJM's beyond-last-published-FPR requirement convention

### 3.1 The finding

From `docs/handoffs/FINDING-capx-d2b-i7-ledger-2026-08-25.md` §5.2, reproduced from constants and
the verdict's own numbers (no solve):

`FORECAST_POOL_REQUIREMENT_BY_ISO["PJM"]` ends at delivery year **2028/29**;
`resolve_forecast_pool_requirement` returns `None` beyond it, so the model falls back to a
composite whose IRM half is **two vintages stale**:

| delivery years | construction | requirement factor (on gross peak) |
|---|---|---:|
| 2026/27 → 2028/29 | published FPR (0.9170 / 0.9260 / 0.9401), **rising** | 0.88063 → 0.90281 |
| 2029/30 + | fallback composite (IRM 17.8 % of 2025/26 × 2026/27 ratio) | **0.87102** |

**Crossing 2028 → 2029 the bar the model builds to DROPS by 3.18 % of peak — 5,492 MW at the 2030
peak** — because PJM's own published series is rising (2027/28 IRM is 20.0 %; the FPR series rises
0.917 → 0.9401) while the composite is pinned to 2025/26.

**Consequence for the verdict:** PJM's reported I7 miss of **366 MW** is the artifact of grading
the horizon edge against the weakest available requirement construction. Against a hold-last-FPR
requirement, 2030's requirement is ~155,946 MW and **the miss is ~5.9 GW — and 2029 plausibly
fails too.** The supply side runs the same direction: the external tie 1,281.7 MW is the 2026/27
BRA cleared UCAP held static, while PJM's published 2027/28 figure is 1,005.9 MW (−275.8 MW).
**Every correction available on either side runs against leniency.**

### 3.2 The related repair, which belongs in the same round

**D-1** (routed to the director by both D2 findings): the invariant checker drops the `year`
argument on PJM's published-FPR path, so for 2026–2028 the *model* builds to the published FPR
while the *checker* grades against the lower fallback. It is **inert for the 2030 leg** (no
published FPR there — both sides use the fallback) but live for 2026–2028. It is the same
machinery and the same scorer/governance round.

### 3.3 The options

**(C-A) Adopt hold-last-FPR as the declared convention — RECOMMENDED.** Past the published table,
hold the last published FPR rather than fall back to the stale composite. Precedent is already in
the repo: `forward_net_cone_anchor` establishes exactly this hold-last convention for the demand
curve's own forward values. Consequences to adopt with it:
  - **PJM's FC-1 verdict changes** — the 2030 miss restates from 366 MW to ~5.9 GW and 2029 may
    join it. This is a **worse** reported result, adopted because it is the more honest bar.
  - It is a **scorer/governance round**: bundle the D-1 checker repair, re-score PJM's T1-F leg,
    and only then run S-6 (the PJM ledger run) so the solo heavy slot measures against the right
    bar.
  - Intake PJM's 2029/30 planning parameters when PJM posts them (rule 23 `[R-FROZEN-DERIVE]`: on
    publication, not on a residual).

**(C-B) Keep the fallback composite.** No change, PJM's 366 MW stands as reported. The cost is
that the number is known to be an understatement produced by a stale vintage, and any future PJM
gate reading inherits it.

**(C-C) Defer until PJM publishes 2029/30 and decide then.** Legitimate if you would rather not
declare a convention at all — but the horizon edge is crossed by **every** T1-F leg that reaches
2029, so deferring leaves the discontinuity in place for all of them, not just PJM's.

**Recommendation: C-A**, bundled with D-1. It is the less lenient reading, it is already
precedented in this repo, and taking it *before* S-6 is what stops a solo heavy-slot run from
measuring against a bar we already know is wrong.

---

## 4. What a signature on any card does NOT do

- **Does not touch the backcast track.** No keeper, marker, `status/*.js`,
  `calibration-complete.json`, offer curve, commitment bridge or backcast matrix cell is
  implicated by any option here.
- **Does not lift or narrow the holdout spend freeze** (rule 22), which stays ACTIVE, or add any
  ISO to `final`, which stays empty.
- **Does not authorize any §2.1b full-solve.** Leg (d) — owner authorization — is untouched by
  every option on card A; no ISO's gate opens on the day of signature.
- **Does not license re-testing any `R`/`I`/`G` matrix cell** without new evidence (rule 28), and
  mints no cell verdict of its own.
- **Card B specifically** does not reach the ERCOT 2023 price object or card Y's Y-C hold — it is
  a forecast-lane default, a different object.

---

## 5. RESOLUTIONS — ALL THREE CARDS SIGNED BY THE OWNER, 2026-08-25 (in-session)

| card | decision | **SIGNED** | vs. recommendation |
|---|---|---|---|
| **A** | leg-(c) consistency | **(A-A) HARMONISE TO `fail`, THEN CLOSE NYISO'S ON MEASUREMENT** | **At** the recommendation |
| **B** | `entry_lookahead_reprice` disarm default | **(B-C) HOLD THE SHIPPED DEFAULT AND CHARTER THE DEVELOPER-PRO-FORMA SUCCESSOR** | **At** the recommendation |
| **C** | PJM beyond-last-FPR convention | **(C-A) ADOPT HOLD-LAST-FPR, BUNDLED WITH THE D-1 CHECKER REPAIR** | **At** the recommendation |

### 5.1 Consequences adopted with the signatures

**A-A.** CAISO and NYISO gate leg (c) moves `na` → `fail`, with `"c"` added to both `closed_on`
lists; NEISO's `fail` stands unchanged. The reading is now uniform across all three ISOs that
have no T1-X run. **A NYISO T1-X crossover run is chartered** (director lane **D10**) so leg (c)
closes on a measured FC-4 rather than on an unscored cell. The scoring edit itself is carried by
the already-issued **D7-NYISO** gate re-score, which now also applies the harmonisation.
*Nothing opened:* all three gates remain `open: false` on other legs, so no ISO's schedulability
changed on the day of signature, and leg (d) is untouched.

**B-C.** The ERCOT shipped default **holds** — `entry_lookahead_reprice=True` stays the forecast
posture and the matrix cell stays **`O`**; no cell verdict is minted by this signature (rule 28:
nothing was tested here). The **developer-pro-forma entry-signal construction is chartered as the
named successor** (director lane **D11**), with the L-1 measurements as its specification. The
signature explicitly does **not** ratify either known-wrong construction as correct.

**C-A.** **Hold-last-FPR is adopted as the declared convention** beyond the last published FPR
table, on the `forward_net_cone_anchor` precedent. Adopted with it, and stated plainly because it
is the point: **PJM's reported I7 miss restates from 366 MW to ~5.9 GW, and 2029 plausibly joins
2030 as a failing year.** This is a worse reported result, taken because it is the more honest
bar. The **D-1 checker repair** (the dropped `year` argument, live for 2026–2028, inert for 2030)
is bundled into the same scorer/governance round. **S-5 is unblocked**; **S-6** (the PJM ledger
run, solo heavy slot) runs only *after* S-5 lands, so it measures against the corrected bar.
PJM's 2029/30 planning parameters are intaken **on publication** (rule 23), never against a
residual.

### 5.2 What the signatures did NOT do

Unchanged by all three, per §4: no backcast keeper, marker, `status/*.js`,
`calibration-complete.json`, offer curve, commitment bridge or backcast matrix cell touched; the
**holdout spend freeze stays ACTIVE** and `final` stays empty; **no §2.1b full-solve is
authorized** and no ISO's gate opened; no `R`/`I`/`G` cell is licensed for re-test. No solve, no
scoring and no registration was performed to produce this signature record.

The director's ledger (`docs/handoffs/capx-director-ledger-2026-08.md` §3) is updated in the same
session, and the card body above is preserved **as put** — the ercot-233 card Y pattern.
