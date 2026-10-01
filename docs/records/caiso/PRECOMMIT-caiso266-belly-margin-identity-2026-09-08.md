# PRECOMMIT — caiso-266: the shoulder-month object, worked in the belly lane

**Session caiso-266, 2026-09-08.** Branch `claude/kind-einstein-vd2l4s`.
Keeper **`2026-09-06-caiso-260-b1-demand`** (`caiso260_demand_vintage`),
**CALIBRATED** (rubric v3.6, 8 scored, 0 FAILs, one ledgered C3c caveat).
CAISO holds the `complete` marker; the holdout freeze is tier-scoped to
locked_test only. **Every read in this session stays inside 2023–2025.**

Charter: the caiso-266 handoff — diagnose and, if a real mechanism is found,
repair the shoulder-month over-pricing named by `FINDING-caiso265` §3,
identified **entirely on 2023–2025** (rule 22), then re-tested on the 2022 rung.
The handoff's binding instruction is rule 19 `[R-ONE-MECH]`: work it inside the
standing CC-side under-dispatch / over-import belly lane (caiso-121 / -131 / -140),
**and verify that identity rather than assume it** (caiso-265 §6 disclosure 4
flags it as an inference).

---

## §0 — DISCLOSURE: what was measured BEFORE this document was written

This is stated first, against interest, so no reader has to reconstruct the
order. Sessions in this lane normally push the precommit before the first
instrument runs (caiso-229 / -232 / -250 / -265). **This one did not.** Before
this document existed I ran six exploratory reads of committed artifacts —
labelled **M0–M10** in the FINDING — on the keeper's `hourly/` sidecars, the
committed actual-LMP reference, the committed `bench/CAISO/<y>.json.gz` parts
and the EIA-930 `CISO hourly` extract. They are **diagnosis, not a test**:

* No mechanism was selected on them, none is armed, and nothing was solved.
* Two of them produced **kills** (a candidate family removed), not promotions;
  a kill cannot be a favourable selection.
* One of them produced an error I found and corrected myself (the EIA-930
  gas-basis trap, FINDING §5) — the correction is reported at full magnitude
  and moves the conclusion **against** the more interesting hypothesis.

What this document pre-registers is everything that comes **after** it: the two
remaining decisive measurements (**M11**, **M12**) with their decision rules
fixed before either is computed, and the conditions under which any LP would be
earned. The M0–M10 results are reported as exploratory and are never quoted as
a pre-registered test.

## §1 — The object, as this session will treat it

`FINDING-caiso265` §3 states the object on a **seasonal** axis: a positive price
bias proportionally largest in low-price months, `corr(err, actual price)`
−0.575 (train) / −0.555 (2022 ex-Dec). The handoff asks whether that is the same
object as the belly lane seen on a different axis.

**M0 (exploratory, already run)** removes the one arithmetic reading that would
have made the seasonal statement vacuous: the correlation is **not** an artifact
of a constant additive bias. Measured on the same 36 training months,
`corr(ABSOLUTE $/MWh error, actual price)` = **−0.572** against the percentage
version's −0.575. The bias is larger *in dollars* where prices are lower, so the
seasonal ordering is a real structural statement and not a denominator effect.

## §2 — Rule 19 `[R-ONE-MECH]`: the identity test (M1–M4, exploratory)

The identity is tested by **composition**, not by signature matching, which is
what caiso-265 §6 disclosure 4 asks for. Reported in the FINDING §2–§4.

## §3 — PRE-REGISTERED: M11, the marginal-rung offer-level check

**Question.** In the hours that carry the residual the model's marginal MW is a
gas CC economic rung. Does CAISO's own **measured** offer surface put that band
BELOW the keeper's armed value — i.e. is there a rule 14 `[R-ACCURATE]`
measured-input re-grounding that moves the belly price down — or AT/ABOVE it,
reproducing caiso-229's sign closure?

**Why it is asked again at all** (rule 28(a) DO-NOT-REDO is respected, not
bypassed). `FINDING-caiso229` closed this door on sign, but it measured on
keeper `2026-08-26-caiso-220-c1-crosswalk`. **The classifier that produces the
measured surface has since changed**: caiso-254/255 found the CT bucket
contaminated by gas steamers and re-cut it at the measured heat-rate antimode,
and caiso-257 promoted that re-cut. That is **new evidence about the
instrument**, which is exactly the condition rule 28(a) requires before a
re-test. The CC bands are re-read on the current artifact and the current keeper.

**Decision rule, fixed before the numbers are read:**

* **LIVE** — the measured `committed` / `econ_low` / `econ_high` CC bands sit
  **below** the keeper's armed values in **≥ 2 of 3** years. Then a
  measured-faithful re-grounding moves the belly price DOWN, it is a rule-14
  repair rather than a residual fit, and the session names it and proceeds to
  M12 sizing and (only if M12 clears) a screen.
* **CLOSED** — the bands sit **at or above** the armed values in ≥ 2 of 3
  years. caiso-229's sign closure is reproduced on the new classifier, the door
  stays shut, **no solve is earned**, and the session ends as a measurement.

The rule is symmetric and the CLOSED branch is the one that costs nothing, so it
carries no incentive. **The band values are never swept, and no value is chosen
by whether a criterion passes** (rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`
condition (c)).

## §4 — PRE-REGISTERED: M12, the sizing test (kill-before-solve)

**Question.** Independently of sign: how deep is the model's own supply stack
between the belly clearing price and the price reality clears at? If closing the
gap requires re-pricing more MW than the entire economic gas band holds, **no
offer repair of any magnitude can reach it** and M11's answer is moot.

This is the caiso-131 §5 kill-before-solve arithmetic run downward instead of
upward, on the current keeper.

**Decision rule, fixed before the numbers are read:** if the MW that must leave
the (target, λ] band exceeds the total gas MW the model dispatches above its own
binding floors in those hours by **more than 2×**, the offer channel is
**arithmetically closed** and the session reports that, whatever M11 says.

## §5 — What this session will NOT do

* **No fit to 2022.** Every identification is on 2023–2025. The 2022 rung is
  touched only if a repair is first identified in-sample and screened, and then
  only as a re-test.
* **No offer-curve multiplier tuned on price.** The rules 1/13 authorized
  channel is available but is **not** used here: any band value that moves must
  come from the measured surface (rule 14), declared ex ante, never swept.
* **No new `ScenarioConfig` field** unless M11 reads LIVE and M12 clears.
* **DO-NOT-REDO honoured**: Panoche CT volume (caiso-261, declared permanent
  residual); the hod 22–23 import object (caiso-261, closed as data-intake);
  whole-plant-off days; the walled PS water-state intake (caiso-141); the
  December-2022 passthrough question; `caiso_fsno_subzonal_topology` (R,
  caiso-224 + caiso-230 DO-NOT-REDO item 2 — locational repricing is never a
  C3a instrument for CAISO); the caiso-221 surplus-pricing representation
  (killed on size); the caiso-256 storage-cycling candidates (every one moves
  battery volume the wrong way on the correct battery-only basis).

## §6 — Governance

* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 only for every identification. CAISO's
  `complete` marker authorizes the 2020–2022 validation ladder; nothing here
  spends it.
* **Rule 29 `[R-SCREEN]`** — zero-LP phase 0 first (done, M0–M10 + M11/M12).
  A screen year, if one is ever earned, is named in an addendum to this document
  **before** it runs, chosen by the mechanism's own measured footprint and never
  by the residual. G-CTRL **form 4**: the keeper's committed bundle is the
  control; no control solve. G-DRIFT is owed only if a solve is earned.
* **Rule 31 `[R-RETAIN]`** — nothing solved is deleted; any bundle produced is
  gitignored, not removed, and the promotion question is surfaced explicitly
  before the session ends.
* **Rule 15 `[R-DASHBOARD]`** — anything solved is registered, keeper or
  rejection.
* **Rule 28 `[R-MECH-MATRIX]`** — the CAISO shard is updated in this session if
  and only if a mechanism cell actually moves.

**Next number: caiso-267.**
