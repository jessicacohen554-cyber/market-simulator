# PRE-COMMIT — ERCOT-132 leg B: the ERCOT-122 coal offer-LEVEL controlled refutation

**Date** 2026-07-28 · **ISO** ERCOT · **Lane** ercot132 leg B ·
**Run id (to be registered)** `ercot122-offerlevel` ·
**Bundle** `results/calibration/ercot122_offerlevel` ·
**Keeper (untouched)** `2026-07-28-ercot129-conditional-coal-min`
(`results/calibration/ercot129_conditional`) ·
**Status: NOT a keeper candidate.** A registered controlled refutation for the
record, on the ERCOT-118 / ERCOT-119 precedent, run under an owner overrule of
`DIAGNOSIS-ercot122` §5.1's recommend-and-STOP.

**This document is written and pushed BEFORE the solve.** Its predictions are on
the record ahead of the number. `DIAGNOSIS-ercot122` §5.1 is the substantive
pre-commit; this restates its expectation in my own words, pins the arm's exact
spec, and adds the ex-ante measurements that specifying the arm turned up.
**The prediction is that the arm FAILS. Confirming that is a successful
session.**

---

## 1. What is being run, exactly

One `replay_keeper` invocation, full span in one bundle (rules 12/16), a single
delta against the keeper: the coal offer LEVEL is moved onto the measured
fleet-representative level from
`data/raw/_validation-source/offer_curve_dam_hrmults_coal_yearly.json`.

Per §5.3 the licensed pair is the artifact's **`econ_low`** and
**`peak_typical`** — the only two coal bands with **100 % capacity coverage** in
every year and the only two that are LOYO-stable. Each is the mean of the three
measured delivery years (spreads 0.025–0.107 hr-mult); the config surface holds
one number per band, so this is a summary of an already-stable measured series,
**not a refit** — no residual was consulted (rule 23).

| class | band | keeper resolved | **arm resolved (measured)** |
|---|---|---|---|
| COAL_LIGNITE | `econ_low` | 1.216 | **1.3803** |
| COAL_LIGNITE | `peak` | 1.550 | **1.4157** |
| COAL_PRB | `econ_low` | 0.886 | **0.9777** |
| COAL_PRB | `peak` | 1.562 | **1.0027** |

`econ_high` and `committed` are **deliberately untouched** and keep the keeper's
resolved values: §5.2 forbids re-arming the pooled `econ_high` 2.856, §1 refutes
the measured `econ_high` as fleet-representative in *every* year (21–47 %
coverage), and the `committed` band was destroyed by the 2026-07-22 raw slimming
(§2). There is no licensed measured value for either.

### 1.1 Two spec corrections found while building the arm (verified, not assumed)

Both were caught by an ex-ante no-LP capture
(`scripts/probes/ercot132_coal_offerlevel_precommit.py`, which reproduces
`DIAGNOSIS-ercot122` §3's model-side band table **to the cent** on the BASE arm —
a cross-validation of this session's whole pipeline against that one). Passing
the measured numbers naively would have run a different experiment than the one
claimed:

1. **`--offer-curve-json` REPLACES `offer_curve_overrides` wholesale.** The
   keeper carries `CC_REGULAR` and `CC_CHP` entries there. A coal-only payload
   would silently drop them and re-price the gas fleet, so the arm would not be
   a single-delta coal probe at all. **The CC entries are carried through
   verbatim** and are verified byte-identical in the resolved config.
2. **The keeper's `offer_curve_deltas` are added ON TOP of the overrides**
   (`COAL_PRB` `econ_low` −0.30 / `peak` +0.082; `COAL_LIGNITE` `econ_low`
   +0.076), and `coal_econ_marginal_hr_bound` then clamps the econ bands up to
   the measured CAMPD marginal HR (0.886/0.898). Written naively, `COAL_PRB`
   `econ_low` 0.9777 resolved to **0.886** — the arm's headline band would not
   have moved at all. Each written value is therefore **`measured − delta`**, so
   the RESOLVED band lands on the measured level exactly. This is arithmetically
   identical to zeroing the coal run delta and setting the base to the measured
   value; the fitted delta is *replaced*, which is the arm's whole premise.

Resolved-config verification (2023 capture, no LP): all four coal bands land on
the measured values in the table above; `CC_REGULAR`/`CC_CHP` byte-identical.

## 2. The prediction

### 2.1 Direction — and a correction to `DIAGNOSIS-ercot122` §3, stated ex ante

§3 predicted the measured rebasis "**LOWERS** the model's coal offers over ~6.6
GW and makes coal run **MORE**". Applied band-faithfully through the registered
channel, **it does the opposite.** Measured ex ante (2023, cap-weighted P1 bid
$/MWh, no LP):

| supply | band | pmax MW | keeper | arm | Δ summer |
|---|---|---|---|---|---|
| lignite | `econlo` | 545 | 21.13 | 23.38 | **+2.25** |
| lignite | `econhi` | 435 | 19.72 | 19.72 | 0.00 |
| lignite | `peak` | 128 | 26.96 | 25.02 | −1.95 |
| prb | `committed` | 2,493 | 20.57 | 20.57 | 0.00 |
| prb | `econ_ramp` | 5,886 | 23.99 | 24.93 | **+0.94** |
| prb | `peak` | 570 | 32.17 | 22.26 | −9.91 |

**6,432 MW made DEARER against 698 MW made cheaper.** Two reasons, both
structural:

* §3 compared the model's `econ_ramp`/`peak` bids against the measured
  *top-of-curve* and inferred a 6.6 GW markdown. But the model's `econ_ramp` is
  the smoothed ramp spanning `econ_low → econ_high`, and `econ_high` has **no
  licensed measured value** (§1/§5.2). Its top therefore does not come down —
  and its *bottom* rises, because measured `econ_low` (0.9777) sits **above**
  the keeper's (0.886). The ramp moves up, not down.
* The artifact's hr-mults are formed on a **pooled divisor** (base HR 10.341 ×
  a flat delivered-coal price), while the model prices each plant on its **own**
  base heat rate through the gas-keyed passthrough sigmoids
  (`coal_lignite_passthrough_floor` 0.675, `coal_prb_passthrough_floor` 0.76).
  A measured *multiplier* transplanted into the model's band therefore does not
  reproduce the measured *$/MWh*: lignite `econ_low` is nominally $20.5 measured
  against the model's $21.13, yet transplanting the multiplier moves the model
  **to $23.38**.

This is a real basis mismatch in the lever itself, and it is why the arm cannot
be read as "adopt the measured $/MWh level".

### 2.2 Consequences I expect, pre-registered

* **P1 — arming and bite.** The four coal bands appear at the measured values in
  the arm's `run_config.json`; coal energy changes materially in all three years.
  (The band resolution half is already verified above, without a solve.)
* **P2 — direction.** **Coal energy FALLS in every year** against the keeper's
  60.791 / 58.414 / 61.047 TWh. This is the load-bearing prediction.
* **P3 — C1 level.** The keeper sits at **+0.371 / +0.794 / −1.163 TWh** against
  actual (60.42 / 57.62 / 62.21), mean absolute **0.776**. A fall moves 2023 and
  2024 toward zero and pushes 2025 further below. I predict the mean-absolute
  C1 coal error does **not** improve enough to justify adoption, and that **2025
  degrades**.
* **P4 — G1 price-conditional loading.** The keeper passes 19 of 21 bands, and
  ERCOT-127 §1 established the failures are almost entirely at the **bottom**
  (`<$15`, 2023 and 2025) while the top is already matched. Making the econ band
  dearer works against the bands that already pass. I predict **G1 regresses**.
* **P5 — verdict.** **REJECTED.** Registered as a controlled refutation, not a
  keeper candidate.

### 2.3 What would falsify the prediction

The arm would be adoptable only if **all** of: (a) C1 coal mean-absolute error
improves on 0.776 TWh; (b) G1 does not regress below 19/21; (c) no new C-gate
FAIL. I predict it clears none of (a)–(c) cleanly and fails at least (b).
**If it does clear all three I will STOP and surface it rather than promote it**
— there is no promotion path from this lane, and
`frontend/data/backcast/keepers/ERCOT.json` is not touched either way.

## 3. Constraints honoured

* **§5.2** — the pooled `econ_high` 2.856 is **not** re-armed, on any basis; the
  pooled artifacts stay frozen as the old-basis record.
* **§5.3** — the measured `econ_low`/`peak_typical` pair is used as published
  and **not refitted**.
* **§4 / §5.4** — the real coal defect is offer **REACH** (coal exposes
  0.168/0.184/0.161 of online headroom to DAM merit against CC's
  0.622/0.594/0.677; the model offers ~100 %). **No reach mechanism is built
  here.** It stays routed to the SCED TPO instrument (`FINDING-ercot117` §E);
  pricing the unoffered ~83 % without that evidence would be a fitted wall
  (rule 13) and a second mechanism on one phenomenon (rule 19).
* **Rule 22** — holdout years untouched; the span is exactly {2023, 2024, 2025}.
* **Rule 16** — full span in one bundle, one invocation, years sequential.
* **Rule 15** — registered on the backcast dashboard in this session whatever it
  shows, as a REJECTED PROBE, with a hand-written sidecar `definition`.
* **Rule 26** — the coal offer-surface matrix cell is updated in this session.

## 4. The reading NOT taken, declared so the owner can redirect

There is a second admissible construction: additionally set `econ_high` to the
measured top-of-curve, flattening the whole model curve onto the measured
$20.5–21.8 and producing the ~6.6 GW markdown §3's arithmetic assumed. **I did
not take it**, because §5.3 licenses only the `econ_low`/`peak_typical` pair and
§1 refuses `econ_high` a fleet-representative value in every year — assigning it
one would be choosing a price for a band the measurement declined to describe,
which is the fitted wall §5.4 warns against. If the owner wants that variant it
is a separate arm and a separate bundle; this document is the reason it is not
folded in here.
