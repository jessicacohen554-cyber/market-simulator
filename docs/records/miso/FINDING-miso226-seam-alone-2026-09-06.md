# FINDING miso-226 — THE SEAM ARM ALONE **SURVIVES ITS SCREEN**: unconfounded, the neighbour anchor moves cheap-hour imports **+581 MW** where the joint arm measured **−75**, at **0.83×** its static prediction. AND IT DELIVERS ONLY **3 %** OF THE RESPONSIVENESS REPAIR — measured, not inferred: the model's imports still track its own price at r = +0.725 against a measured −0.101, and every thermal C1 cell moves AWAY from actual (2026-09-06)

**KEEPER UNCHANGED → `2026-09-05-miso-220-nonsteam-lift`** (bundle
`results/calibration/miso220_nonsteamlift_B`), determination **CALIBRATED**, C3c the single
ledgered caveat. **No promotion is proposed, and a survived screen cannot make one**: rule 29
`[R-SCREEN]` clause (2) — a screen "may kill an arm; it may never promote one". The screen
bundle `miso226_seamalone_S` (2023 only) is NOT registered and is **DELETED before this PR
merges** (clause (c), owner ruling R-AV): every number cited here lives in this document or in a
committed JSON. Rule 22 `[R-HOLDOUT]`: 2023–2025 only; ONE LP was scored (2023); 2024/2025 never
spent.

Records: `PRECOMMIT-miso226-seam-alone-2026-09-06.md` (pushed with the blind scorer **before**
the solve, `1230bf1d`); instruments `scripts/probes/_miso226_seam_static_remerit_phase0.py`,
`_miso226_coal_hold_attribution_phase0.py`, `_miso226_import_duration_shape.py` → their
`_miso226_*.json`; blind scorer `_miso226_screen_gates.py` → `_miso226_screen_gates.json`.
Mechanism: `miso_seam_neighbour_anchored_ladder` (`ScenarioConfig`, default off, minted by
miso-225); matrix row `seam_neighbour_anchored_ladder`, MISO cell **`O`**.

---

## 0. Verdict in one paragraph

miso-225 screened this mechanism inside a joint arm, watched imports **fall 75 MW** when every
PJM band had got $2.3–4.6 cheaper, and diagnosed the miss as a confound plus a structural
defect: its fuel partner had pulled MISO's price down $1.92, and *an anchor changes a fixed
ladder's LEVELS and not its RESPONSIVENESS*. **Both halves of that diagnosis are now measured,
and both are right.** Run alone, with no exogenous price shock, the same mechanism in the same
year moves cheap-hour imports **3,043 → 3,624 MW, +581**, against a pre-registered bar of +150
and a phase-0 static prediction of +700.7 — a **0.829×** conversion, more than double the
0.27–0.39× either predecessor achieved on any leg. Its footprint is confined to the rows its own
arithmetic claims to a degree no previous MISO screen has shown: **+527 MW in the hours a band
actually crosses merit, +1.9 MW in the hours none does**, a 277× ratio. **All five
pre-registered gates PASS and the arm survives.** And the second half of the diagnosis is the
half that matters for what to build next: the anchor repairs the seam's **level** and barely
touches its **slope**. The model's imports still rise with the model's own price — correlation
**+0.750 → +0.725** against a measured **−0.101**, i.e. **3 %** of the way — the price-decile
slope closes **10 %** of its sign error, the annual import total moves **further** from every
measured comparator on record (45.754 → 48.934 TWh), and **every thermal C1 class moves AWAY
from actual**, because the +3.18 TWh of imports comes out of classes that were already short.
The mechanism is real, it is not refuted, and on this evidence it is **not the repair the seam
needs**: the ruling says imports are offered at the exporting market's own measured price, and
the implementation prices each band at a FROZEN ANNUAL QUANTILE of that price — which discards
exactly the hourly variation the ruling is about.

## 1. THE GATE TABLE, exactly as the blind scorer printed it

| gate | scorer | measured | reading |
|---|---|---|---|
| **S-1** config scoping | **PASS** (S-1b) | armed field `ok: True`; `other_diffs = ['ccs_retrofit_vom_adder']`, all of it on the ex-ante exempt list; `other_diffs_not_exempt = []` | the re-scoping declared before the solve (§2). **S-1a, the identity leg, still FAILS** and is reported |
| **S-2** liveness + isolation | **PASS** | neighbour seam line PRESENT (`PJM WESTERN-BORDER DA quantiles`); fuel marginal-commodity line ABSENT; transport clause ABSENT; winter-shape line present (report-only, the keeper's own behaviour) | the arm is isolated — this is the seam and nothing else |
| **G-2** seam direction & footprint *(frozen verbatim from miso-225)* | **PASS** | cheap-hour imports 3,043 → **3,624 MW (+581**, needed ≥ +150); annual 45.754 → 48.934 TWh (**+3.18**) | **the joint arm's −75 MW was the confound.** +581 vs −75, same mechanism, same year, same measurement |
| **G-4** no C1 flip *(construction unchanged from miso-225)* | **PASS** | flips `[]`; **`CT_PEAKER` INCONCLUSIVE**; band 8.0 TWh | no kill, but see §5 — CT_PEAKER is pushed past its band edge |
| **G-5** footprint confinement *(new)* | **PASS** | import Δ **+527.2 MW** in the 6,022 re-merit hours vs **+1.9 MW** in the 2,738 zero-re-merit hours; Δslack = Δdump = 0.0000 TWh | **277×** concentration — the change lands exactly where the arithmetic put it |
| price | **REPORT ONLY** | body −$0.308, tail −$0.094, annual LW −$0.257 | 16 % of the joint arm's −$1.917 (§4) |

**ARM SURVIVES THE SCREEN.** Under rule 29 that is a licence to ask the owner for the full span,
and nothing else.

## 2. S-1: the re-scoping was declared BEFORE the solve, and the identity leg is still reported as a FAIL

miso-225's S-1 failed on a real fourth config difference — `ccs_retrofit_vom_adder` 8.0 → 2.95
from capx D65-B on `main` — which its own G-DRIFT had already classified inert-for-this-solve,
and its FINDING §2 set the successor's obligation verbatim: *"A successor that wants S-1 to mean
'differs only in fields that can reach this solve' must say so in its own PRECOMMIT, before its
solve."*

PRECOMMIT §4 did exactly that, at `1230bf1d`, before any LP ran. The STOP leg (**S-1b**) exempts
a **closed, explicitly enumerated list of one field name**, with its reachability reason —
never a rule that could swallow a reachable field — and any other non-arm diff still stops the
arm. **The identity leg (S-1a) is computed and printed and still reads FAIL**, on the same
single field, so nothing is hidden by the re-scoping: the config genuinely differs, the
difference genuinely cannot reach a `mode="backcast"` 2023 solve, and both facts are on the
record. `other_diffs_not_exempt_STOP` is empty, which is the substantive result.

## 3. THE LEVEL REPAIR — real, large, and confined

### 3.1 What phase 0 predicted, before the solve

`_miso226_seam_static_remerit.json`, computed at the keeper's own committed `MISO_external` bus
price with everything else fixed: **+700.7 MW** over the frozen 1,230-hour set (+534.9 MW annual
≈ +4.69 TWh). Two ex-ante cross-checks, both in the PRECOMMIT:

- the annual static landed within **2 %** of the **≈ +4.8 TWh** miso-225 §4 attributed to the
  anchor by a completely independent route (scaling the bare-hub arm's import loss to the ruled
  arm's price move) — two instruments sharing no input;
- the overlay's **export leg was measured structurally inert** (0 hours in merit under either
  ladder, against a $34.5 bus price), so the gross-import measurement is the whole mechanism and
  not the net of two offsetting effects.

### 3.2 What the LP did

**+581 MW realized against +700.7 predicted = 0.829×.** For scale: miso-224 converted its static
at 0.27×, miso-225 at 0.275× (coal) and 0.394× (gas). This arm converts at three times either
rate, and the reason is visible in G-5: an import band is a single LP row whose only obstacle is
its own price, where a coal displacement has to travel through commitment, reserves and the
network (§6).

The self-limiting feedback named ex ante in PRECOMMIT §4 as the second likeliest kill **is real
and is small**: the body price falls **$0.308**, which claws back part of the static, and the
arm still delivers 83 % of it. The prediction was right in sign and wrong in magnitude, in the
arm's favour; that is recorded here as a prediction that did not bind, not as a success.

### 3.3 Against the measured deficit

In the frozen hour set the measured seam carried **4,890 MW** (miso-224's comparator) against the
keeper's 3,043. The arm closes **31.5 %** of that gap (1,847 → 1,266 MW short). **Clearing G-2 is
not "solving the seam"**, exactly as PRECOMMIT §5 said before the solve.

## 4. THE RESPONSIVENESS DEFECT — miso-225 inferred it; this arm MEASURES it, and it is the finding

`_miso226_import_duration_shape.json`. Bin 2023 by the **measured** MISO-Indiana hub price and
read three import series in the same bins (MW):

| decile | actual hub | measured PJM seam | keeper | arm | arm − keeper |
|---|---:|---:|---:|---:|---:|
| d1 (cheapest) | | **5,739** | 2,837 | 3,417 | +580 |
| d2 | | 5,321 | 3,801 | 4,362 | +561 |
| d3 | | 5,002 | 4,540 | 5,011 | +471 |
| d5 | | 4,535 | 5,296 | 5,636 | +340 |
| d8 | | 4,244 | 6,283 | 6,533 | +250 |
| d10 (dearest) | | **4,417** | 6,410 | 6,634 | +224 |
| **slope d1 − d10** | | **+1,322** | **−3,573** | **−3,217** | |

**The measured seam slopes DOWN in MISO's price and the model slopes UP.** MISO really imports
most when it is cheapest (5,739 MW in d1) because the neighbour is cheaper still; the keeper does
the opposite (2,837 in d1, 6,410 in d10). The neighbour anchor lifts **every** decile — most at
the cheap end (+580) and least at the dear end (+224), so it is pushing the right way — and
closes **10.0 %** of the slope's sign error (−3,573 → −3,217).

The same thing said as a correlation with each series' **own** price signal:

| | corr(imports, own price) |
|---|---:|
| measured PJM seam vs the measured hub | **−0.101** |
| keeper vs its own model price | **+0.750** |
| **arm** vs its own model price | **+0.725** |

**The anchor moves the correlation 0.025 of the 0.851 it would have to travel — 3 %.**

**Why, structurally.** The owner ruled that imports are offered at *the exporting market's own
measured price*. The implementation prices band *k* at the **annual quantile** of the PJM border
DA whose exceedance duration equals the band's depth — a **frozen 8-rung annual ladder**. So an
hour in which PJM is cheap and MISO is dear is given the *same* band prices as an hour in which
both are dear, and the LP then clears that fixed ladder against its own hourly price. The
ladder's levels now come from the neighbour; **its hour-to-hour variation still comes only from
MISO.** That is the whole gap between the ruling and its current implementation, and it is now a
measured 0.025-of-0.851 rather than an assertion.

## 5. REPORTED AGAINST THE ARM, IN FULL — every thermal C1 cell moves AWAY from actual

This is the half of the result that argues against the mechanism, and it is larger than the half
that argues for it.

C1 by delta transfer, 2023, band 8.0 TWh (TWh):

| class | actual | keeper (err) | arm (err) | Δ TWh | reading |
|---|---:|---:|---:|---:|---|
| CC_REGULAR | 141.817 | 137.645 (−4.172) | 136.384 (**−5.433**) | −1.261 | pass, **AWAY** |
| **CT_PEAKER** | 17.038 | 9.053 (**−7.985**) | 8.749 (**−8.289**) | −0.304 | **INCONCLUSIVE** — pushed 0.289 TWh past the ±8.00 edge (§5.1) |
| COAL_PRB | 121.671 | 120.114 (−1.557) | 119.398 (−2.273) | −0.716 | pass, AWAY |
| COAL_BIT | 57.069 | 54.146 (−2.923) | 54.021 (−3.048) | −0.125 | pass, AWAY |
| CC_CHP | 21.311 | 19.627 (−1.684) | 19.341 (−1.970) | −0.286 | pass, AWAY |
| ST_CHP | 5.203 | 2.530 (−2.672) | 2.497 (−2.706) | −0.034 | pass, AWAY |
| COAL_LIGNITE | 7.047 | 6.382 (−0.665) | 6.351 (−0.696) | −0.031 | pass, AWAY |
| **ST_GAS** | 13.940 | 14.483 (+0.544) | 14.118 (**+0.178**) | −0.365 | pass, **TOWARD** — the one favourable cell |

**Seven of eight thermal cells move away from actual, and the eighth is the only class the model
over-produces.** The arithmetic is not subtle: every one of those classes is already BELOW
actual, the arm adds **+3.18 TWh** of imports, and the LP takes it out of them — the class deltas
sum to **−3.12 TWh** against the import +3.18, which is the energy-balance identity closing (G-5
leg b: slack and dump are 0.0000 TWh in both bundles, so nothing is being absorbed by an
infeasibility). **The mechanism displaces generation the model does not have to spare.**

**And the annual import total moves further from every measured comparator on record.** Model
all-seam **45.754 → 48.934 TWh**. The two measured comparators in the repo disagree with each
other and are on different bases — 40.94 TWh gross inbound on the PJM seam alone (EIA-930, the
ladder's own source, computed here) and the 37.9 TWh figure miso-224's stamp cites against the
model's all-seam total — and **this session adjudicates neither**, because it does not have to:
the arm moves *away* from both.

**G-2 as frozen therefore rewarded a change that also worsens the annual total.** The gate
required annual imports to RISE, which was the right test in miso-225's context (a joint arm
destroying imports) and is a blunt one here. **The gate was frozen and it was not edited** — the
scorer is byte-identical to the one pushed before the solve — and this defect is disclosed rather
than repaired after the fact, which is the miso-223/224/225 discipline. A successor writing its
own gate should score the seam's **duration shape**, not its total.

### 5.1 CT_PEAKER, named before it was scored

miso-225's PREREG named CT_PEAKER-2023 as the keeper's fragile edge — **−7.985 against ±8.00,
0.015 TWh of headroom** — and PRECOMMIT §5 carried it forward as a watch item. The arm pushes it
to **−8.289**, i.e. **0.289 TWh past the band edge**. By the pre-registered rule (a miss within
±1.5 TWh of the edge is INCONCLUSIVE, not a kill, because the per-class delta transfer is
approximate) this is INCONCLUSIVE and G-4 passes. **It is not a pass for CT_PEAKER**, and any
full-span run of this mechanism must re-check that cell on a real scored bundle rather than a
delta transfer. Reported here at full magnitude.

## 6. QUEUE ITEM 2 — WHAT HOLDS MISO'S CHEAP-HOUR COAL, answered at phase 0 with no LP

The queue head's second item asked what holds the LP's cheap-hour coal at 0.275× the static,
given it is not forcing (keeper D-2: MISO COAL forced energy 0.30 / 0.34 / 0.17 % of the class).
`_miso226_coal_hold_attribution.json` answers it from the committed sidecar plus one on-recipe
`build_year` rebuild — **zero LP minutes** — and the answer reframes the question.

**(A) The keeper's cheap-hour coal, by band family** (committed `class_band_hourly_2023.parquet`,
the 1,230-hour set, mean MW):

| band | all hours | **cheap hours** | share of cheap-hour coal |
|---|---:|---:|---:|
| `mustrun` (fuel-free price-taker) | 7,825 | **8,000** | 43.6 % |
| `committed` (take-or-pay) | 9,237 | **8,900** | 48.5 % |
| `econ*` (the rising ramp) | 3,486 | **1,415** | 7.7 % |
| `peak` | 92 | 35 | 0.2 % |
| **total** | 20,639 | **18,349** | |

**92.1 % of the keeper's cheap-hour coal — 16,900 of 18,349 MW — sits in the price-taker
`mustrun` band and the take-or-pay `committed` band.** Only **1,449 MW** is in bands whose offer
a gas move can outbid at all.

**(B) Which bands the static actually demanded** (the miso-225 static re-merit re-run on the same
two bases, recording the displacement by band; it reproduces the pre-registered total at **−1,473
MW** against −1,470, so it is the same object):

| band | static displacement | in merit, keeper basis | in merit, ruled basis |
|---|---:|---:|---:|
| `mustrun` | **−5** | 7,536 | 7,531 |
| `committed` | **−371** | 9,472 | 9,101 |
| `econ*` | **−1,094** | 2,315 | 1,220 |
| `peak` | −3 | 14 | 11 |

**The reframing.** The `mustrun` band is untouched by the fuel move (−5 MW of 7,536), exactly as
miso-53's adjudication of it as a measured price-taker offer implies — so it is **not** the
object, and it should not be re-opened. What the static demanded was **−1,094 MW out of an econ
band the LP dispatches at 1,415 MW**, i.e. the evacuation of **77 %** of the entire
price-responsive coal position in those hours, plus **−371 MW out of the take-or-pay `committed`
band** the LP has committed. The LP surrendered **404 MW = 28.6 % of its whole econ position**.

So the 0.275× is not a mysterious hold. **The static's denominator counted a displacement the LP
had almost no room to make.** The two named objects for a successor, in order of size, are the
**`committed` take-or-pay band (8,900 MW, 48.5 % of cheap-hour coal)** — which the static
believed it could displace by 371 MW and the LP did not — and whatever keeps the **econ band's
remaining 1,011 MW** in merit through hours its own offer loses, for which the leading candidate
is the reserve co-optimization (2,606 reserve-eligible units pooled into 60 R columns) paying
coal to stay online. Rule 19 `[R-ONE-MECH]`: those are **reconciliation** targets, not slots for
a new floor. **This is measurement, not a proposal, and nothing here licenses a mechanism.**

## 7. WHAT THIS DOES AND DOES NOT LICENSE, and the cell

- **No keeper, no promotion, no registration.** A survived screen never promotes (rule 29(2)).
  PRECOMMIT §0 narrowed the path ex ante to screen → **owner** → full span, so the next step is
  an owner decision on whether to spend 2024/2025, not a full-span run taken unilaterally.
- **`seam_neighbour_anchored_ladder` MISO cell stays `O`.** Not `K` — nothing is promoted. Not
  `R` — it cleared every pre-registered gate, at 0.83× its own arithmetic, with a 277× confined
  footprint. What changed is that the cell's `O` now rests on a **cleared, unconfounded screen**
  plus a **measured** statement of what the mechanism does not do, where before it rested on a
  confounded joint failure.
- **miso-225's §4 diagnosis is CONFIRMED in both halves**, and its refusal to score the joint
  failure as a refutation is vindicated: the same mechanism reads −75 MW confounded and +581 MW
  clean.
- **The evidence argues against arming this form as it stands.** It buys 31.5 % of the cheap-hour
  deficit at the cost of moving seven of eight thermal C1 cells away from actual, widening the
  annual over-import, and pushing CT_PEAKER past its band edge — while repairing 3 % of the
  responsiveness defect that is the seam's actual disease. That is a level fix applied to a
  slope problem. **This document does not propose it as a keeper and does not recommend the full
  span for this form.**
- **The named successor, and it is buildable from data already in the repo.** An **hourly**
  neighbour anchor: price the seam's import rows off the hourly PJM western-border DA
  (`data/raw/_validation-source/pjm_border_lmp_hourly_MISO.parquet`, which the incumbent derive
  already loads) rather than off a frozen annual quantile of it. That is what the owner's ruling
  says on its face — *offered at the exporting market's own measured price* — it carries **zero
  fitted parameters**, it has an exact forward analogue (a forward year's neighbour price), and
  it is the only construction on the board that can move the +0.725 correlation rather than its
  level. It is a **new mechanism** and would need its own field, matrix row (rule 28c) and
  screen; **it is named here as the queue head, not proposed or built in this session.**
- **The transport table and the ladder derive are untouched.** Nothing in this screen bears on
  either.
- **Reported against interest, in full**: S-1a still fails on a real config difference (§2);
  seven of eight thermal C1 cells move away from actual and the class sum is −3.12 TWh (§5); the
  annual import total moves away from both measured comparators (§5); CT_PEAKER is pushed 0.289
  TWh past its band edge and reads INCONCLUSIVE rather than pass (§5.1); and G-2 as frozen
  rewarded a change that worsens the annual total, disclosed and not edited (§5).

## 8. GOVERNANCE — what happened, in the order it happened

- **PRECOMMIT and the blind scorer committed and pushed BEFORE the solve** (`1230bf1d`), with the
  phase-0 instrument and its JSON in the same push, and the three pushed blobs verified
  byte-equal on the remote before the LP was launched. **No band, kill condition or
  pre-registered value was edited at any point**, and the scorer that produced §1 is
  byte-identical to the one pushed before the solve.
- **Phase 0 ran first and shaped the screen** (rule 29 clause 0): the static re-merit sized the
  arm (+700.7 MW), measured the export leg structurally inert, and reproduced the keeper's own
  3,042.8 MW cheap-hour baseline before any LP existed.
- **The solve was restarted once, before any result was read**, because the first launch warned
  that the replay environment differed from the keeper's recorded environment (pydantic 2.13.5 vs
  the bundle's 2.13.4). The partial output was deleted, pydantic pinned to 2.13.4 and the screen
  re-run from scratch, so the scored bundle matches the control's recorded environment and no
  environment caveat is carried. Cost: ~1 minute of a build that had not reached the LP.
- **The LP**: P0 cold 346.8 s / 387,804 simplex iterations, P1 warm 184.1 s / 238,284 iterations,
  sidecars written, 8 GB swapfile created and confirmed live from a separate call
  (`/proc/swaps`, 8,388,604 kB) before launch and untouched during it.
- **No control solve.** G-DRIFT `07099620..47e306d3`: eight files, 204 insertions, 47 deletions,
  **ALL INERT** — two pure formatter reflows (`run_calibration.py`'s `print_cells` ternary,
  `data/fuel/basis/miso.py`'s hub ternary), capx D78's forecast-mode capacity-evolution sector
  gate, a **comment-only** `scenarios.py` hunk, a cache-epoch note, and the nyiso-201
  diagnostics census (`screen_stats` is `None` by default and reads into no floor arithmetic;
  the roll-up is NYISO-only). Form 4: the committed keeper is the control. The one hunk that
  surfaced downstream — `ccs_retrofit_vom_adder` — surfaced in S-1a, not in dispatch, exactly as
  an inert-for-the-solve classification predicts.
- **Rule 27** `[R-PUSH]`: every file was edited locally and pushed as on-disk bytes, with each
  ≥300-line blob verified equal on the remote after its push.
- **Rule 28** `[R-MECH-MATRIX]`: no `ScenarioConfig` field is added, so no base row is minted;
  the MISO cell for `seam_neighbour_anchored_ladder` is re-stamped in this session, and the
  `gas_variable_transport` cell is annotated with §6's reframing of the G-3 denominator.
- **Rule 29(c)**: the screen bundle is deleted before this PR merges. Every number this session
  will ever cite from it is in this document or in a committed `_miso226_*.json`.
- **DOF ledger unchanged at 41/2**: zero fitted scalars minted, and no `ScenarioConfig` field
  added.
- **Disclosed, not this lane's to fix**, carried forward: `main` carries 18 pre-existing failures
  in the pinned-default-cache-key tests, left stale by the capx D65-B flip. This session adds no
  field and cannot move the default key.
