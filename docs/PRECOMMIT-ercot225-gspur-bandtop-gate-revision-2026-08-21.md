# PRECOMMIT — ercot-225: the G-SPUR band-top blindness OWNER GATE REVISION, drafted as an owner decision card. Revised spec + re-reading protocol fixed HERE, pushed and blob-verified BEFORE any re-reading is computed. NO LP, no solve, no re-bundle, no registration, NO GATE CHANGE — the gate files are not edited; the card awaits owner sign-off.

**Session ercot-225, 2026-08-21, branch `claude/ercot-225-gspur-gate-z1q0f6`.**
Keeper resolved fresh at dispatch: `2026-08-20-ercot223-arm-eventrelease`
(NOT-YET, fail set {C3a-2023 −39.7 %, C3b-2023 0.729}, C3c ledgered CAVEAT ×3)
— UNTOUCHED this session. Queue basis: the R-A re-pointed queue's last
standing item (item-8's reopen screen was SPENT NEGATIVE at ercot-224; do not
re-screen). This is scorer/gate work under the ercot-163/170/208/214/224
no-LP precedent.

## 0. The defect being adjudicated (already on the record — not re-derived here)

`FINDING-ercot214-gspur-phase0-2026-08-17.md` §5 (flagged not fixed) + §3 fn¹:
G-SPUR counts spurious hours as `model ∈ [150, 500] & actual < 150`. The
**upper lid at $500 makes the gate blind to phantom adders that overshoot the
top**: a phantom hour pushed past $500 *leaves* the count, so making an hour
strictly worse reads as an improvement, and repairing it reads as a
regression. The two hours measured on the record:

* **h5822-2023** (Aug 31 14h): control $172.74 + phantom adder $410.53 =
  $583.26 in the ercot-213 arm vs actual **$145** — left the band upward,
  so the arm's banded count read 17 where the population was 18.
* **h3355-2025** (May 20 19h): $1,411 in the ercot-213-recipe control
  (λ $214.30 + phantom adder $1,196.56) vs actual **$134.84** — invisible at
  0; the ercot-215 decontamination brought it back into band and G-SPUR read
  a 0→1 "regression" for repairing it.

## 1. What this session does and does not do

**Does:** (a) fix the revised gate spec and the re-reading protocol in this
precommit; (b) push + blob-verify it; (c) ONLY THEN compute the re-readings
for every registered ERCOT run from committed artifacts; (d) draft the owner
decision card with the measured effects and the verdict-flip table; (e) land
FINDING + log + matrix §5.1 re-stamp.

**Does not:** edit `scripts/probes/ercot221_gates.py`, `ercot219_gates.py`,
`_ercot173_ab.py` or any scorer; solve anything; touch any bundle,
registration, sidecar or baseline constant; move the keeper; mint any matrix
cell verdict (no mechanism is tested — rule 28(b) evidence duty discharged
via the §5.1 stamp, the ercot-224 pattern). **The gate itself changes only on
owner sign-off, in a later session, against this card.**

## 2. The revised spec — the owner's three options (fixed here, chosen by the owner)

Let, per run-year, on the price basis of §3:

* `S_band  = #{h : model(h) ∈ [150, 500] & actual(h) < 150}` — the CURRENT
  gated quantity.
* `S_top   = #{h : model(h) > 500 & actual(h) < 150}` — the band-top blind
  population (phantom overshoot).
* `S_nolid = S_band + S_top = #{h : model(h) ≥ 150 & actual(h) < 150}` — the
  lidless count.

**Option A (recommended in the card): gate on `S_nolid`.** The gated
quantity becomes the lidless count; `S_band`/`S_top` remain reported as the
decomposition. Bar semantics are UNCHANGED in form: the A/B scorers'
"must not increase in any year" rule and the baseline-bar scorers' "+5/yr vs
baseline" rule keep their shape, with the baseline re-read as
`S_nolid(baseline bundle)` in the same commit that changes the gate.
Rationale: a gate whose purpose is "no new spurious high-price hours" must
not be escapable by pricing the phantom hour HIGHER.

**Option B: keep the banded gate, add `S_nolid`/`S_top` as a mandatory
side-by-side report** (no gating change; blindness documented per run rather
than closed).

**Option C: status quo** (decline; the flag stays a standing caveat on every
future G-SPUR reading).

Under Option A the baseline numbers proposed to replace the 9/11/1 constant
are exactly the §3 re-reading of the baseline bundle — proposed in the card,
minted only on sign-off.

## 3. The re-reading protocol (pre-registered; committed artifacts ONLY)

**Universe — all 11 registered ERCOT runs** (every ERCOT sidecar in
`frontend/data/backcast/registry/`, enumerated pre-reading; all carry
committed `hourly/system_<year>.parquet` for 2023/2024/2025):

| run id | bundle |
|---|---|
| 2026-08-15-ercot204-rule26-delete | results/calibration/ercot204_rule26_delete |
| 2026-08-16-ercot213-ctl-headbase | results/calibration/ercot213_control_A |
| 2026-08-16-ercot213-arm-pubanchor | results/calibration/ercot213_anchor_B |
| 2026-08-17-ercot215-ctl-headbase | results/calibration/ercot215_control_A |
| 2026-08-17-ercot215-arm-decontam | results/calibration/ercot215_decontam_B |
| 2026-08-18-ercot219-ctl-headbase | results/calibration/ercot219_control_A |
| 2026-08-18-ercot219-arm-optionb | results/calibration/ercot219_optionb_B |
| 2026-08-19-ercot221-ctl-headbase | results/calibration/ercot221_control_A |
| 2026-08-19-ercot221-arm-adaptive | results/calibration/ercot221_adaptive_B |
| 2026-08-20-ercot223-ctl-headbase | results/calibration/ercot223_control_replay |
| 2026-08-20-ercot223-arm-eventrelease | results/calibration/ercot223_release_arm |

**Conventions** (the shared convention of BOTH standing scorers):

* Model price: `_ercot173_ab.lw_price` — demand-weighted P1 system price
  from the run's own committed `hourly/system_<year>.parquet`
  (`Σ price×demand / Σ demand` per hour, `pass == "P1"`).
* Actuals: committed
  `data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet`, column `rt`.
* Mask: `isfinite(model) & isfinite(actual)` (the `_ercot173_ab` rule). The
  probe ALSO computes every count under the `ercot221_gates._spur_hours`
  NaN rule (`actual NaN → +∞`, `model NaN → 0`) and reports any run-year
  where the two conventions disagree; the `_ercot173_ab` rule is primary.
* Band edges verbatim: `MID_BAND = (150.0, 500.0)`; `S_top` uses
  `model > 500` so that `S_band + S_top ≡ S_nolid` exactly (lower edge ≥,
  upper edge > per the existing `<=` band).
* Per run-year the probe emits `S_band`, `S_top`, `S_nolid`, and the `S_top`
  hour list with (model, actual) pairs — listed in full when ≤ 24 hours,
  else first 24 + exact count.
* Output: `scripts/probes/ercot225_gspur_bandtop_reread.py` →
  `results/calibration/ercot225_gspur_bandtop_reread.json`. Read-only; no
  bundle byte is written.

## 4. Verdict re-derivation and the flip rule (fixed BEFORE reading)

The recorded G-SPUR verdicts on the register, each with its OPERATIVE rule:

| # | A/B | recorded verdict | operative rule | recorded numbers (banded) |
|---|---|---|---|---|
| V1 | ercot-204 (base→probe) | PASS | no-increase/yr (`ercot204_ab.json`) | 9→9 / 11→11 / 0→0 |
| V2 | ercot-213 (ctl→arm) | **FAIL → REJECTED-AS-ARMED on G-SPUR** (owner-promoted over it) | +5 bar vs ctl (`PRECOMMIT-ercot213`); strict no-increase leg also recorded FAIL (`ercot213_ab.json`) | 9→17 / 11→13 / 0→0 |
| V3 | ercot-215 (ctl→arm) | session gate **PASS** (+5 bar, `PRECOMMIT-ercot215` §gates); strict `_ercot173_ab` leg recorded **FAIL on 2025 0→1 alone** (`ercot215_ab.json`) | both on record | 17→9 / 13→11 / 0→1 |
| V4 | ercot-219 (arm) | FAIL | +5/yr vs 9/11/1 (`ercot219_gates.json`) | 273 / 671 / 1239 |
| V5 | ercot-221 (arm) | PASS | +5/yr vs 9/11/1 (`ercot221_gates.json`) | 11 / 10 / 1 |
| V6 | ercot-223 (arm) | PASS | +5/yr vs 9/11/1 (`ercot223_gates.json`) | 11 / 11 / 1 |

**Re-derivation:** each verdict is recomputed with `S_nolid` substituted for
the banded count on BOTH sides of its own operative rule:

* V1–V3: A/B legs use `S_nolid(arm) vs S_nolid(ctl)` under the same rule
  (+5 bar where the session gated on +5; the strict no-increase leg
  re-derived separately where it is separately on record).
* V4–V6: bar becomes `S_nolid(ercot215_decontam_B, year) + 5` — the same
  baseline bundle that minted 9/11/1, re-read under the same spec.

**Flip rule:** a verdict FLIPS iff its overall PASS/FAIL status changes.
Leg-level changes that do not change the overall status are reported as
leg notes. The card states, for each of V1–V6: flipped / not flipped, and
for V2 whether the historical owner-promotion context would have differed
(reported, never re-adjudicated — the promotions stand regardless).

## 5. Declared priors (two-sided, falsifiable — recorded before any reading)

* **P1 (V3, the exoneration prior):** the strict-leg FAIL on 2025 0→1
  dissolves iff `S_nolid` counts h3355 in the CONTROL at $1,411 (expected:
  ctl 2025 `S_nolid` = 1 = arm) AND the 2023/2024 legs stay non-increasing
  lidless. Expected: 2023 ctl (the ercot-213-keeper recipe) carries a LARGE
  `S_top` (the FINDING-214 §2 phantom deep population where actual < 150)
  against arm ≈ 0, so the leg strengthens. If instead the ARM carries new
  `S_top` hours the flip does NOT occur — recorded either way.
* **P2 (V2, a-fortiori prior):** ercot-213 stays FAIL, and worsens —
  arm-2023 `S_top` ≥ 1 (h5822) plus whatever share of its 117 deep-adder
  hours sat on actual < $150. A smaller-than-banded gap would be evidence
  AGAINST the revision's materiality; recorded either way.
* **P3 (V4):** stays FAIL trivially (273/671/1239 already ≫ bar).
* **P4 (V5/V6, the live-keeper question):** expected PASS retained. If the
  adaptive-floor keepers put > bar-margin hours above $500 on actual < 150
  hours, the CURRENT keeper's G-SPUR flips PASS→FAIL under Option A — a
  live consequence the card must surface FIRST, and still a card item, not
  a keeper action.
* **P5 (V1):** stays PASS by construction (byte-equal comparison).

## 6. Standing hygiene note to verify in passing (report-only)

`ercot221_gates.py::SPUR_BASELINE` carries 2023/2024 baseline HOUR LISTS
([4283, 4404, …] / [4749, 4750, …]) whose identities do not match the sets
the same file's own `_member` construction yields on the registered
baseline-recipe bundles ([5438, 5439, …] / [336, 337, …] per
`ercot219_gates.json`/`ercot221_gates.json` control legs), though the counts
(9/11/1) agree — the gate compares counts only, so no recorded verdict is
affected. The probe recomputes the baseline bundle's banded hour lists to
settle the identities; the card carries it as a hygiene note.

## 7. Fences

Rule 22: years {2023, 2024, 2025} only; committed artifacts only; the
actuals parquet is the standing committed validation source (data-not-score;
no out-of-training year touched). Rule 25: ERCOT only. Rule 27: local edits,
exact on-disk bytes pushed, ≥300-line pushed files blob-verified — and this
precommit itself blob-verified before any reading. Rule 28: no mechanism
tested ⇒ no cell verdict; §5.1 stamp in the same session. No LP, no new
workflows, no cron, no PR — push-and-stop on the designated branch. If the
owner is not in-session, the card lands as a pushed doc awaiting sign-off
and the gate is NOT changed.

## 8. Deliverables and ordering

1. THIS precommit — pushed + blob-verified first.
2. `scripts/probes/ercot225_gspur_bandtop_reread.py` +
   `results/calibration/ercot225_gspur_bandtop_reread.json`.
3. `results/calibration/DECISION-ercot225-gspur-bandtop-gate-2026-08-21.md`
   — the owner decision card (options §2, measured effects, flip table §4,
   recommendation).
4. `docs/FINDING-ercot225-gspur-bandtop-card-2026-08-21.md`.
5. Log entry `docs/calibration-log/ercot.md` (ercot-225; next shorthand
   ercot-226, ercot-199 unclaimed).
6. Matrix §5.1 re-stamp (queue item → card drafted, awaiting owner
   sign-off).
