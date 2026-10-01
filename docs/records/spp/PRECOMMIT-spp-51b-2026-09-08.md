# PRECOMMIT — SPP-51b: the C3a/C3b price level

**Lane** SPP-51b · **Model** Opus 5 (`claude-opus-5`) · **Date** 2026-09-08 ·
**Branch** `claude/spp-c3a-c3b-price-1i4bgi` · **Base** `15bbb371` (`origin/main` at launch) ·
**Data profile** `spp` · **Charter** `docs/multi-iso/spp-addition-plan-2026-09.md` §8 W5-r#15 ·
**Owner ruling** P15 ("open the price level") · **Control** keeper-3
`2026-09-07-spp-3-screened-input` / `results/calibration/spp43_screened_B` (committed bundle) plus
the registered `2026-09-08-spp-50-rebaseline` sidecar (no `hourly/`).

**This document is pushed before the remaining phase-0 legs are computed and before any LP is
considered.** §1 records what has already been measured, with its ordering disclosed against
interest; §2–§5 pre-register the legs that have *not* been run, with sign, magnitude, an
against-interest prediction, an exhaustive outcome partition and an instrument-failure branch.

---

## 0. Ordering disclosure (against interest, stated first)

The session prompt requires the PRECOMMIT to be pushed "before any number is read". **That is not
what happened, and I am not going to describe it as if it were.** Phase-0 leg 0.1 — the
decomposition of the C3a level error by measured-price bucket, §1 below — was computed *before*
this document existed, from the keeper's committed hourly sidecars and SPP's committed actual RT
LMP series.

Why I judge the record still clean, and what would make it unclean:

- Leg 0.1 is a **descriptive decomposition of committed artifacts**, not a selection among arms.
  It partitions an already-registered residual by an axis (the measured actual price) fixed before
  the lane opened. No parameter was chosen by it and no arm was rejected by it.
- **No arm has been solved, screened, swept or scored** — this lane has spent zero LP and, on the
  §5 partition below, expects to spend zero.
- What would make it unclean is a value *selected* against a residual. Nothing in §1 selects
  anything. Every leg that could still select something — the fuel level (§2), the reach of the
  candidate structural repair (§3), the cell adjudications (§4) — is pre-registered below with its
  bar written before the number exists.

The charter's binding form of this rule is "pushed in the PRECOMMIT before you read any **screen**
result" (§8 W5-r#15). That form is met exactly and unconditionally.

---

## 1. Phase 0 leg 0.1 — ALREADY MEASURED (the decomposition)

**Instrument.** Model side: `spp43_screened_B/hourly/system_<year>.parquet`, P1 pass, system
load-weighted price `Σ_z p_z·d_z / Σ_z d_z` per hour. Actual side:
`data/raw/_validation-source/actual_lmp_hourly_SPP.parquet` column `rt`, restricted to the hours
where it is non-null (8,754 / 8,748 / 8,754).

**Instrument validation, declared as the precondition for believing any of this:** the load-weighted
actual this instrument computes must reproduce the committed bench `rt_lw`, and the load-weighted
model mean must reproduce the registered C3a. Measured: actual **24.438 / 24.531 / 27.957** against
bench `rt_lw` 24.44 / 24.53 / 27.96; C3a **+14.10 / +7.41 / +7.20 %** against the registered
+14.1 / +7.5 / +7.2 %. **PASS** (≤ 0.1 pp in every year).

### 1.1 The result

| year | LW model | LW actual | C3a | total LW gap |
|---|---|---|---|---|
| 2023 | 27.883 | 24.438 | **+14.10 %** | +3.445 $/MWh |
| 2024 | 26.349 | 24.531 | **+7.41 %** | +1.818 $/MWh |
| 2025 | 29.969 | 27.957 | **+7.20 %** | +2.012 $/MWh |

Decomposed by **measured** RT price bucket; `gap_contrib` is that bucket's contribution to the
whole-year LW gap, so the column sums to the gap.

| measured RT bucket | 2023 hrs / contrib | 2024 hrs / contrib | 2025 hrs / contrib |
|---|---|---|---|
| **< $0** | 992 / **+3.761** | 1,172 / **+4.043** | 1,018 / **+3.861** |
| $0–10 | 920 / +1.888 | 1,164 / +2.202 | 1,038 / +2.358 |
| $10–20 | 2,203 / +2.636 | 2,384 / +2.493 | 1,487 / +2.149 |
| $20–30 | 2,554 / +1.416 | 2,153 / +1.089 | 2,467 / +1.759 |
| $30–40 | 1,056 / −0.429 | 790 / −0.372 | 1,304 / −0.247 |
| $40–60 | 570 / −1.225 | 506 / −1.169 | 841 / −1.425 |
| $60–100 | 307 / −1.766 | 319 / −1.869 | 386 / −1.963 |
| $100–200 | 110 / −1.495 | 201 / −2.647 | 145 / −1.852 |
| **> $200** | 42 / −1.343 | 59 / −1.952 | 68 / −2.628 |

**The negative-price hours alone contribute 109 % / 222 % / 192 % of the entire C3a level error.**
With the $0–10 bucket: 164 % / 344 % / 309 %. The whole of the remainder is offset by the model
being far too CHEAP above $40 (−5.8 / −7.6 / −7.9 $/MWh of contribution).

### 1.2 The census behind it

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| measured hours < $0 | **992** | **1,172** | **1,018** |
| **model** hours < $0 | **4** | **7** | **0** |
| measured hours < $5 | 1,381 | 1,687 | 1,486 |
| **model** hours < $5 | **7** | **9** | **4** |
| mean measured price in the measured-negative hours | −11.94 | −10.71 | −11.44 |
| mean **model** price in those same hours | **+23.33** | **+21.06** | **+23.98** |
| measured hours > $200 (C3c) | 42 | 59 | 68 |
| **model** hours > $200 | **0** | **3** | **1** |

### 1.3 What leg 0.1 establishes, and what it does not

**Establishes.** SPP's modelled price surface is **compressed at both ends**. It has no low tail
(4 / 7 / 0 negative hours against ~1,000; 7 / 9 / 4 sub-$5 hours against ~1,500) and no high tail
(C3c, already routed to SPP-55). The C3a level error is the arithmetic residue of the missing low
tail net of the missing high tail. **A multiplier scales a surface; it cannot create a tail.** That
is, independently, the mechanical reason the price-family lane's G-2 steepening gate fired at
`+0.5 %` against a required `≥ 1.783`: the arm was a level lever aimed at a shape defect.

**Does not establish.** *Which* structure is missing. §2–§3 pre-register that question.

**Surface caveat, stated once and carried everywhere.** These numbers are keeper-3's, i.e. the
**pre-repair** input surface. `main` now carries SPP-48's wind repair and SPP-49's two input seams,
under which SPP-50 measured C3a **+15.0 / +12.1 / +14.2 %** — uniformly ~7 pp richer. SPP-50's
bundle did not survive its container, so no hourly decomposition of the current surface exists and
**none is claimed**. Every number in §1 is labelled keeper-3.

---

## 2. PRE-REGISTERED LEG A — the fuel-basis leg (charter 0.2), NOT YET COMPUTED

The charter requires the fuel leg to be tested *before* any multiplier, because a fuel-basis error
is a rule-14 input repair with zero DOF and would be worth more than a passing C3a.

**Test.** Compare the model's own SPP gas fuel-price array (keeper-3 `run_config` / the fleet
rebuild at HEAD) against SPP's committed measured references, on the same $/MMBtu basis.

**Declared predictions, with magnitude:**

- **A-1 (sign + magnitude).** The model's SPP gas price is **not** systematically ~13 % above the
  measured SPP-region reference: pooled 2023–2025 |bias| **< 10 %**.
- **A-2 (AGAINST INTEREST — this one hurts my preferred answer).** If the measured bias is
  **≥ +10 %** (model gas dearer than SPP's own delivered reference), then **(A) is live, it
  outranks (B), and this lane's result becomes "route the fuel-basis repair first"** — even though
  §1 makes the tail story attractive. I will say so in those words.
- **A-3 (structural, independent of A-1's value).** *Whatever* the fuel bias is, a fuel-price change
  is a **multiplicative level lever** and therefore cannot create the 992 / 1,172 / 1,018 missing
  negative hours: gas-marginal prices scale with gas, and no positive gas price produces a negative
  LMP. So A cannot be the *whole* cause. A-3 is falsified if a fuel change is shown to be capable of
  producing sub-$0 prices in this LP.

## 3. PRE-REGISTERED LEG B — the reach of the candidate structural object, NOT YET COMPUTED

**The candidate, named before it is measured.** SPP's wind bound is
`delivered_EIA930(t) / (1 − 0.096501)` — a **flat** per-hour gross-up that preserves the
**delivered** shape. `market_sim/data/renewables.py`'s own module docstring states the design
intent of the reference-rate gross-up as *"so the LP still curtails endogenously"*; the keeper
re-curtails **0.00058 / 0.00172 / 0.00030 %** against SPP's measured **9.65 %**. Real curtailment
is concentrated in the oversupply hours, so a flat gross-up systematically **under**-states the
potential exactly where the market went negative, and over-states it everywhere else.

**Candidate construction (stated in full before its reach is computed, so it cannot be shaped to
the answer):** `potential(t) = max( delivered(t), Â · SHAPE_sys(t) )`, where `SHAPE_sys(t) =
Σ_z cap_z · SHAPE_z(t)` is the already-committed NASA-POWER reanalysis fleet shape
(`data/raw/spp-wind-shape/spp_<Y>_wind_zone_shape.parquet`, the SPP-48 R-LEVEL construction) and
`Â` is the unique scalar solving `Σ_t potential(t) = Σ_t delivered(t) / (1 − 0.096501)`. **Zero new
free parameters**: the annual potential is SPP-32's already-measured rate, unchanged; `Â` is
determined by that identity; the shape is an already-committed measured input. The `max()` is a
physical constraint, not a fit — delivered can never exceed potential.

**Declared predictions:**

- **B-1 (instrument check, and the branch that voids this whole leg).** Model wind must equal
  `1.106808 × delivered(t)` hour by hour, to within the LP's measured re-curtailment. **If the
  hourly ratio is not flat — if the model's wind bound already carries an hour-varying gross-up —
  then my reading of the mechanism is wrong, leg B is VOID, and I report an instrument failure and
  stop rather than reinterpreting it.** Bar: ≥ 99 % of hours within ±0.5 % of 1.106808.
- **B-2 (reach, sign + magnitude).** In the measured-negative hours, the candidate construction
  raises the mean wind bound above today's by between **+1.0 and +5.0 GW**, and the share of hours
  receiving any gross-up at all is between **10 % and 60 %** (today: 100 % of hours, uniformly).
- **B-3 (the deficit, which is the honest denominator).** I will compute the **oversupply
  deficit** — how much additional zero-or-negative-cost energy the LP would need in the
  measured-negative hours before wind becomes marginal and the price can go sub-$0 — as
  `load − (model wind + nuclear + hydro + solar + net imports + thermal at its realised floor)`.
- **B-4 (AGAINST INTEREST — the prediction that hurts).** **I expect B-2 to be SMALLER than B-3**,
  i.e. the wind-shape repair alone is **necessary but not sufficient** to create SPP's negative-price
  regime, because keeper-3 already carries ~18 GW of wind in those hours against ~10–11 GW of
  thermal that the LP is choosing *economically* rather than holding at a floor. If that is what the
  numbers say, **the honest verdict is "one limb of a two-limb object", and I will report the
  candidate as insufficient on its own rather than promote it as the answer.**

## 4. PRE-REGISTERED LEG C — two cell adjudications at zero LP

- **C-1 `negative_renewable_offers` (SPP cell `U`).** Predicted **INERT on the wind limb**: SPP's
  keeper already carries `ira_ptc_wind = 26.0`, so wind's dispatch offer is already **−$26/MWh** and
  the flag's `min()` floor at `renewable_keep_running_value = 20.0` cannot make it more negative.
  Predicted **rule-25 REFUSED on the solar limb**: $20 is the adjudicated *CAISO* RPS/REC value and
  the field's own docstring forbids re-use on another ISO.
- **C-2 `wind_ptc_vintage_offers` (SPP cell `U`).** Predicted **INERT**, and for a reason that
  matters more than the verdict: it makes the wind offer **less** negative, and it is unreachable
  in either direction while wind is at its upper bound in ~100 % of hours and therefore never
  marginal. **A bid change on a column that is never marginal cannot move a price.**
- Falsifier for both: any hour in the keeper bundle where wind is strictly interior to its bound
  *and* sets the price. Measured re-curtailment is 6e-4 %, so I expect ~none.

## 5. THE OUTCOME PARTITION — exhaustive, with the instrument-failure branch

Exactly one of these is this lane's result, and I commit to reporting whichever it is:

1. **(A) FUEL.** A-2 fires (measured gas bias ≥ +10 %). Result: route the fuel-basis repair as the
   first object; (B) waits behind it; no band.
2. **(B-SUFFICIENT).** B-2 ≥ B-3. Result: the wind-potential shape repair is the named object and
   is on its own sufficient to create the regime; route it as a build with the reach measured.
3. **(B-PARTIAL).** B-2 < B-3, both material. Result — **the outcome I predict** — the object is
   named as **two limbs** (the flat gross-up's shape, plus the absence of any thermal commitment
   floor holding SPP's coal fleet above economics), each with its measured reach; both routed; no
   band, no LP.
4. **(B-NULL).** B-2 immaterial (< 1 GW) *and* B-3 immaterial. Result: the missing negative regime
   is not a system-energy-balance phenomenon at all — most likely locational/congestion — and the
   object is routed to SPP's topology lane instead.
5. **(C) BAND.** Reached **only** if 1–4 are all falsified, i.e. no structural object survives. In
   that case, and only then, the rule-1 carve-out is opened with (a)–(e) satisfied and its config
   declared in an addendum *before* the solve. **On the §1 evidence I do not expect to reach 5, and
   I record now that "C3a improved" is not, and will not be made, a reason to reach it.**
6. **INSTRUMENT FAILURE.** B-1 fails, or the §1.1 validation stops reproducing at HEAD. Result:
   report the failure, void the affected legs, spend nothing.

**A threshold that misses is reported in the words above, never restated.** In particular: if the
measured gas bias lands at, say, +11 %, A-2 has fired and the lane's answer is (A), regardless of
how much better §1's story reads.

## 6. Rule postures

- **Rule 29 `[R-SCREEN]`.** Phase 0 is the whole lane on partition 1–4. No screen year is named
  because no screen is planned; if partition 5 were reached, a screen year would be named in an
  addendum pushed before it ran.
- **Rule 29(b) / G-DRIFT.** Not run, because no arm is solved and therefore no control is used.
  Recorded instead: **keeper-3 does not reproduce on `main`'s own inputs** (SPP-48 wind + SPP-49
  seams are LIVE input-side hunks), so form 4 does not hold for SPP, and every §1 number is
  labelled as keeper-3's surface rather than HEAD's. The prompt's cache-key caution is moot for the
  same reason: no cached solve is reused.
- **Rule 31 `[R-RETAIN]`.** No bundle is written. If one were, `results/calibration/_spp51b_*`
  would be gitignored at the moment of writing and never `rm`'d.
- **Rule 28 `[R-MECH-MATRIX]`.** `offer_curve_by_group` is `R` for SPP and this lane **does not
  re-test it**; §1 is new evidence *for the R*, not against it. The cells this lane may move are
  those in §4, both `U`.
- **Files.** PRECOMMIT/FINDING/`docs/handoffs/spp51b/`, `.gitignore`, and SPP's shard cell lines
  only. No source file, no plan, no ledger, no log, no keeper shard, no other ISO's anything.
