# FINDING — pjm-170: the coal-sigmoid ceiling arm is REJECTED at the 2022 screen

**Session** pjm-170 · **ISO** PJM · **Branch** `claude/pjm-coal-sigmoid-ceiling-a97so9`
**PRECOMMIT** `docs/handoffs/PRECOMMIT-pjm170-coal-sigmoid-ceiling-2026-09-07.md`
(committed 03478006, before any build or solve; Amendment 1 24454429; Addendum A
234ec26f; Addendum B before the solve)
**Keeper UNCHANGED** `2026-08-15-pjm-162-inputclock`. **Nothing is promoted.**
**PJM headline UNCHANGED: CALIBRATED** (rule 30(c) — a held-out year never downgrades).

---

## 1. RESULT

The arm — one declared delta, `coal_bit_passthrough_ceil` **1.32 → 1.00** — cleared
every zero-LP gate and then **FAILED S5** on the 2022 screen.

| # | gate | pass condition (PRECOMMIT §5) | **measured** | verdict |
|---|---|---|---|---|
| **S1** | only `ceil` differs | `{0.65, 1.32, 3.40, 2.5}` → `{0.65, 1.00, 3.40, 2.5}` | **PASS** |
| **S2** | `Δpassthrough = s(g)·(1.00−1.32)` ≤1e-12 | max abs resid **2.220e-16** | **PASS** |
| **S3** | measured = predicted ≤1e-6 $/MWh, negative | **−9.226726** vs **−9.226726**, err **0.000e+00** | **PASS** |
| **S4-A** | zero unpredicted movers, zero predicted non-movers | predicted **243**, moved **243**, **0** / **0** | **PASS** |
| **S4-B** | re-allocation not creation | total energy **+0.0003 %** (bound 0.5 %); slack **0.0→0.0**, dump **0.0→0.0** | **PASS** |
| **S4-C** | direct class up, ≤ headroom | DIRECT **90.762 → 92.152 TWh**, **+1.390** (bound **32.441**) | **PASS** |
| **S5** | no criterion PASSing on the control 2022 may FAIL | **C3a `price_mean` PASS → FAIL, −9.9 % → −10.1 %** | **FAIL** |

**KILL RULE APPLIED (PRECOMMIT §5).** S5 fails ⇒ **the arm is dead, the remaining
years (2023/2024/2025) are NEVER spent, and nothing is promoted.** The full-span
step is not taken.

Objectives: P0 **17.668e9 → 16.885e9**, P1 **19.433e9 → 19.127e9** — the sign a
lowered offer stack must have. Arm determination on 2022: **NOT-YET**, the same as
the control (recorded, not a result).

### 1.1 The gate that killed it, stated precisely and NOT re-read

C3a's commercial-grade outer band is **±10 %** (`PRICE_MEAN_COMMERCIAL = 0.10`).
The control sits at **−9.9 %** (gap −7.34 $/MWh), 0.1 pp *inside*; the arm at
**−10.1 %** (gap −7.51 $/MWh), 0.1 pp *outside*. The movement is 0.17 $/MWh across
a threshold the control was already sitting on.

**It would be easy, and wrong, to call that a band-edge artifact and wave it
through.** C3a was named in S5's protected set in Addendum A, scored from committed
artifacts, and committed **before the arm existed**, precisely so it could not be
adjusted once a number was on the table. Re-reading it now — having seen that it is
the one thing that kills the arm — is the fitted-mechanism selection rule 29 and
rule 1 `[R-STRUCT]` exist to forbid, and it is the exact error pjm-169 §9.2
identified and refused. **The verdict stands. The arm is REJECTED on its own
pre-registered gate.**

*(Instrument note: S5 was scored with `scripts/screen_collateral_gate.py` — the same
`calibration_verdict` scorer run in memory on the unregistered bundle, with the
committed bench parts HELD FIXED on both sides, so the comparison measures the
mechanism and not a benchmark refresh. The bundle was never registered.)*

---

## 2. WHAT THE SCREEN ACTUALLY REVEALED — the substantive finding

**The arm did not create a price defect. It removed something that was masking one.**

At `ceil` 1.00 — i.e. with PJM bituminous bidding **exactly its own measured
delivered fuel cost** and no markup — PJM's 2022 mean LMP lands **10.1 % below the
measured actual**. The rest of the offer stack does not support the observed 2022
price level without a **32 % markup on measured coal fuel cost** whose entire
recorded provenance is *"PJM run 16: trims the dear-gas-2025 BIT over-run"*.

And the control is only at **−9.9 %** — 0.1 pp inside the band **with** the markup
carrying it. So the markup is not comfortably propping the level up; it is barely
holding it inside. That is a **rule 14 `[R-ACCURATE]` signal in its textbook form**:
*"if swapping a hand estimate for real data makes the backcast worse, that is a
signal that something else in the model is miscalibrated and the estimate was
silently compensating for it."*

The screen has therefore done its job in the more useful direction: it did not
license the change, and it **located a real defect the incumbent configuration is
concealing** — a PJM 2022 price level that is ~10 % low on its own merits.

### 2.1 A second, independent pointer at the same object

Phase 0's §3.3 reconciliation (Addendum B.3) measured the model's own delivered
coal price against the derive script's reconstruction:

| PJM bituminous delivered coal $/MMBtu | value |
|---|---|
| the model's own (measured EIA-923 monthly, capacity-weighted, 243 DIRECT rows) | **2.786** |
| `derive_coal_sigmoid.py`'s reconstruction (annual ACR f.o.b. ÷ 0.85) | **4.307** |
| **model-consistent crossover** `2.786 × 11.02 / 6.7` | **4.58** |
| **live `gas_mid`** | **3.40** |

The live sigmoid is centred **$1.18/MMBtu below** the crossover the model's own fuel
prices imply, so it rises too early in gas-price space. A curve that rises too early
and a ceiling raised to 1.32 are **two errors pointing the same way**, and the
2026-06-17 floor moves (0.82 → 0.80 → 0.76 → 0.65) are a third. This is one
mis-grounded curve, not one bad asymptote — which is why the ceiling could not be
fixed alone.

### 2.2 What is NOT claimed

- **Not** that `ceil` 1.32 is admissible. PRECOMMIT §1(a)–(c) stands untouched: it
  marks a measured cost input up 32 % through a channel that is **not** in the
  rules 1/13 authorized `offer_curve_by_group` carve-out, and its provenance is a
  volume residual. The screen adjudicated **this arm**, not that question.
- **Not** that lowering the ceiling is the fix. On this evidence it is not — alone.
- **Not** anything about ERCOT's `ceil` 1.50 / 1.35 (rule 25 `[R-ISO-SCOPE]`).

---

## 3. Reported at full magnitude, gating nothing (PRECOMMIT §5, §B.4)

Class energy, control → arm, 2022 (TWh):

| class | control | arm | Δ |
|---|---|---|---|
| COAL_BIT | 138.817 | 140.206 | **+1.389** |
| CC_REGULAR | 319.149 | 318.530 | −0.619 |
| CT_PEAKER | 15.490 | 15.249 | −0.241 |
| VIRTUAL_DEC | −20.449 | −20.581 | −0.132 |
| VIRTUAL_INC | 10.117 | 10.025 | −0.091 |
| ST_GAS | 13.458 | 13.375 | −0.083 |
| import (net) | −21.650 | −21.732 | −0.082 |
| COAL_PRB | 9.649 | 9.580 | −0.069 |
| CC_CHP | 7.278 | 7.235 | −0.043 |
| COAL_WC | 6.740 | 6.727 | −0.013 |
| CT_CHP | 1.161 | 1.151 | −0.010 |

Criterion moves (none of these is a pass condition):

| criterion | key | status | control → arm | direction |
|---|---|---|---|---|
| C1 fuelmix | CC_REGULAR | FAIL → FAIL | +22.02 → **+21.40 TWh** | toward |
| C1 fuelmix | COAL_BIT | PASS → PASS | +2.70 → +4.09 TWh | away |
| C1 fuelmix | CT_PEAKER | PASS → PASS | −2.97 → −3.22 TWh | away |
| C1 fuelmix | ST_GAS | PASS → PASS | +7.67 → +7.59 TWh | toward |
| C2 sysvol | gas | PASS → PASS | 27.36 → 26.37 | toward |
| C2 sysvol | coal | PASS → PASS | 2.49 → 3.79 | away |
| C3a price_mean (DA diag) | — | SKIPPED both | −6.2 % → −6.4 % | away |
| C6 governance | — | PASS → **UNATTESTED** | not scorable at a screen | — |

**The C1 improvement is NOT a rescue and was pre-declared as such** (Addendum B.4,
written before the solve): `CC_REGULAR`'s over-run falls 0.62 TWh and gas sysvol
moves toward actual. Rule 1 `[R-STRUCT]`: an arm killed on a pre-registered
structural gate is not revived by a target improving. It is recorded because §5
requires the magnitudes be reported, never as a pass condition.

C6 reading UNATTESTED is **not a flip** — a screen bundle carries no attestation by
construction, and the gate tool classifies it "not scorable at a screen".

---

## 4. The displacement-aware footprint gate WORKED — the card's DO item 2

pjm-169's S4 (*"every non-gas class < 1.0 % annual energy"*) killed the F4 arm on
`COAL_BIT +3.28 %`, and its own §9.2 diagnosed the gate as unable to separate a
confound from ordinary merit-order displacement.

This card's replacement (PRECOMMIT §4.2) separated them cleanly:

- **Limb A** bounded where the mechanism **ACTS**, at zero LP, with zero tolerance:
  **243 predicted, 243 moved, 0 unpredicted, 0 non-movers.** Exact.
- **Limb B** confirmed the dispatch response was a **transfer**: total energy moved
  **+0.0003 %**, slack and dump exactly **0.0 → 0.0**.
- **Limb C** confirmed the direct class **answered its own price**: bid down
  $9.23/MWh ⇒ energy **+1.390 TWh**, up, at 4.3 % of the 32.441 TWh headroom.
- **No limb bounded any indirect class.** `CC_REGULAR −0.619`, `CT_PEAKER −0.241`
  and the rest re-allocated freely and were **reported, never gated**.

Under pjm-169's S4 this arm would have been killed by `COAL_BIT +1.389/138.8 =
+1.0 %` — at the threshold, for behaving correctly. Under the new gate it passed
the footprint test and was killed by a **price-level** gate instead, which is a
true and different fact about it. **The gate change was load-bearing, and it
changed the reason, not the outcome.**

### 4.1 Amendment 1 was necessary, and phase 0 proved it

The bituminous fleet carries **284** rows: **25** `_mustrun`, **16** `_sync`, **243**
DIRECT. Limb A *as first written* would have counted those 16 `_sync` rows as
predicted-but-not-moved and **failed the arm** — for rows that cannot move by
construction (`legacy_bins.py:449` returns a hard-coded 1.0 without consulting
`passthrough_by_supply`). It was caught by reading the routing code before anything
was built, amended on the record, and the amendment made the gate **harder** (an
exact two-sided claim). Without it this card would have reproduced pjm-169's error
in its own first gate.

---

## 5. G-CTRL / G-DRIFT — zero control LP spent

G-CTRL **form 4**: the control is the committed `pjm169_tp2022_2021_f2arm` 2022.
G-DRIFT classified all **55** changed files between the control's `f36cee6e` and
HEAD `5930e533` as **INERT** for a PJM backcast (SPP registration / ERCOT-only /
MISO-only / NYISO default-off / PJM forecast-only coerced at `scenarios.py:17531`),
corroborated by an identical PJM solve-surface fingerprint **`0f749d17202c32d9`**
at both revisions, and by **bit-parity on all seven recorded package versions**.
No control solve was spent. Full audit: PRECOMMIT §6.

Two `regenerate_clean` failures were checked and are **inert for this solve**:
`lmp` (CAISO `KeyError: 'MGHG'`) is read only behind `MARKET_SIM_USE_CLEAN`, which
is unset, so the raw committed LMP product is used; `emissions-unit-annual` (OOM) is
read only by offline derive scripts, never by the model package.

---

## 6. Rule 29(c) — the bundle is DELETED

`results/calibration/pjm170_screen2022_ceil10` is **deleted before this PR merges**.
This document carries every number this session will ever cite from it; git history
is the record for the bytes. Retained artifacts (both small, both zero-LP or
scorer-only): `results/calibration/_pjm170_ceil_census.json` (phase 0) and
`results/calibration/_pjm170_g4.json` (the G-4 record).

---

## 7. What the successor should do — routed, not absorbed

**Do NOT re-run this arm.** The `ceil`-alone cell is adjudicated **R** for PJM
(matrix `coal_passthrough_sigmoids`), and re-testing it without new evidence is
barred by the DO-NOT-REDO discipline (rule 32).

The live object is now **the whole PJM bituminous curve, not its ceiling**, and it
has a **source-data** basis and two independent pointers (§2, §2.1):

1. **`gas_mid` is mis-grounded.** The model-consistent crossover from the model's
   OWN measured delivered coal price is **$4.58/MMBtu**; the live value is **3.40**
   and the derive script's is **7.08** (built on a reconstruction that overstates
   delivered coal by **+54.6 %**, so it must NOT be transcribed — rule 14).
2. **The PJM 2022 price level is ~10 % low on its own merits**, and the ceiling is
   masking it. Whatever closes that is upstream of the coal curve.

A successor card should take **(2) first** — a price-level defect that a coal
markup is concealing is the root cause, and re-grounding the coal curve on top of an
unexplained 10 % price deficit would just move the compensation somewhere else
(rule 19 `[R-ONE-MECH]`). It needs its own PRECOMMIT, its own phase 0 and its own
screen.

**Out of scope here and left untouched:** `floor` 0.65-vs-0.50, `gas_mid`
3.40-vs-4.58-vs-7.08, `gas_slope` 2.5-vs-1.0 (PRECOMMIT §3.4); F1, F1b, F3, F4; and
pjm-166 §7.4's coal-CC framing.
