# ADDENDUM nyiso-218 — **S-1 FAILS AS WRITTEN, and the failure is MINE, not the arm's.** The disposition, declared before the span is spent

**Written and pushed BEFORE the full-span solve.** The screen result is in hand; the span result is
not. Nothing below is a restatement of a gate to fit a number — the gate is reported as it failed,
and the number it failed on is given.

## 1. The screen result, whole

Screen year **2023** (declared in the PREREG §5.2 before the solve). Arm bundle
`results/calibration/_nyiso218_screen_2023`, gitignored per rule 31 `[R-RETAIN]` / rule 29(c).
Record: `results/calibration/_nyiso218_screen_gates_2023.json`.

| gate | verdict | |
|---|---|---|
| **S-1** recipe identity | **FAIL** | see §2 — the failure is a defect in my own gate |
| **S-2** passthrough direction + order of magnitude | **PASS** | measured **+0.7167 $/MWh** vs predicted +0.6418 / +0.6715; ratio to the in-zone prediction **1.117**; window [+0.321, +1.343] |
| **S-3** footprint confinement | **PASS** | moved-class aggregate **−0.0947 TWh** (falls, as P5 required); all-class sum −0.0027 TWh against a 0.742 TWh energy-balance tolerance; `ST_CHP` +0.0747 ≤ 0.0947 |
| **S-4** no non-target load-bearing flip | **PASS** | **zero** PASS→FAIL flips on C1 / C2 / C4 |
| **S-5** price tail | reported only | keeper 2 h > $300 / 44 h > $100 → arm **2 / 44**, unchanged |

**Instrument validation (not asserted — measured).** The payload rebuild reproduces the committed
keeper payload **exactly**: `lmp.p` max abs diff **0.0**, `gmModel` max abs diff **0.0**, zones
match, and the rebuilt keeper `fuelRows` gas row is identical to the committed one on every field
(`m` 62.81, `b` 61.00, `r` 0.941, `nrmse` 0.124). Keeper and arm are scored by one instrument on
one basis.

**Reported at full magnitude, gated on nothing** (these are the target family, PREREG §6):

| | keeper | arm |
|---|---|---|
| C3a | PASS **+4.3 %** (33.65 vs 32.25) | PASS **+6.5 %** (34.36 vs 32.25) |
| C3b | PASS 0.122 | PASS **0.132** (bar 0.20) |
| C4 gas | PASS r 0.941 / NRMSE 0.124 | PASS r 0.941 / NRMSE 0.124 |
| C1 CC_REGULAR / CC_CHP / CT_PEAKER / ST_GAS / ST_CHP | +0.79 / +1.10 / −1.72 / +1.67 / +0.20 TWh | +0.74 / +1.06 / −1.71 / +1.61 / +0.28 TWh |

**PREREG §5 predictions, adjudicated:**

* **P1 (construction)** — FIRED (phase 0; re-confirmed by S-1's own sub-limbs, §2).
* **P2 (direction)** — **FIRES.** Measured Δ is positive.
* **P3 (magnitude)** — **FIRES.** +0.7167 is inside [+0.321, +1.343], at 1.117× the in-zone
  prediction. **The phase-0 arithmetic is confirmed to within 12 %**, which is the substantive
  point of the whole screen: the mechanism does what its own arithmetic says it does.
* **P4 (year-invariance)** — **NOT YET TESTABLE**; needs 2024/2025. Untouched.
* **P5 (confinement)** — **FIRES** on all three limbs.

**The number the owner needs, measured:** in 2023 the realized passthrough is
**0.2389 $/MWh per 1 % of energy-band lift** (0.7167 / 3.0). The handoff's ~1:1 assumption implied
~0.34 $/MWh per 1 % at this price level; the realized figure is **~0.70 of it**, for the structural
reason in PREREG §3 C-10 (the anchored net-revenue margin). C3a moved +4.3 % → +6.5 % against a
pre-solve projection of +6.33 / +6.42 %.

## 2. Why S-1 failed, and why it is not about the arm

S-1's substantive limbs **all hold**:

* bands moved: **30**, expected **30**;
* every moved ratio **exactly 1.03** (|ratio − 1.03| ≤ 1e-9), `violations: []`;
* **no** moved `peak`, `phys_*` or structural share;
* `year_selection_keys_excluded: {}` — the replay recorded no `weather_year` /
  `gas_price_override` difference at all.

It failed on **`non_offer_curve_recipe_diff = {ercot_zonal_spread_ep_referenced,
spp_gas_commitment_bridge}`** — two `ScenarioConfig` fields that **did not exist when the keeper
solved at `51f2fc2d`**. The keeper's `run_config.json` therefore has no entry for them; the arm's,
solved at `bfbb0b6a`, records both as **`False`**. The "difference" is `absent → False`.

**This is a drafting defect in my gate, and the information was already in my hand when I wrote
it.** PREREG §4's G-DRIFT audit names both fields explicitly, classifies both INERT, and gives the
reason (new field, dataclass default `False`, declared in `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`,
absent from the keeper recipe, gated on `iso == "SPP"` / ERCOT respectively). nyiso-213's own S-1
had to solve this same problem and did ("the keeper's record PREDATES the field, so absent *means*
False"). I did not encode it. That is my error, not the arm's.

**I am not rewriting S-1 to pass.** It is reported FAILED AS WRITTEN, and this addendum is the
record of why.

## 3. The outcome partition has a GAP, and I am naming it rather than choosing quietly

PREREG §6 defined **K = "S-1 or S-2 or S-3 or S-4 fails"** and sent K-true to branch **(A)**, the
kill. But S-1's declared *meaning* is "**instrument invalid, not a result**" — it exists to catch
"the arm is not the config I think it is". Here the arm **is** the config I think it is, and S-1
says so through its own sub-limbs; what failed is the gate's encoding of a fact I had already
audited. **My partition does not distinguish "the arm is wrong" from "the gate is misdrafted", and
both routes lead to (A).** That is the same class of defect nyiso-215's P2 and nyiso-217's P3
reported against themselves, and it is a RESULT, not a drafting inconvenience.

## 4. The disposition, declared here before the span is spent

**I proceed to the full span**, and I record the reasoning so it is a judgement on the record
rather than a silent re-reading:

1. S-1's purpose is discharged by its own measured sub-limbs (30/30 bands at exactly 1.03, zero
   violations, no moved frozen band, no other live field).
2. The two offending records are `absent → False`, i.e. the **pre-flip posture of fields that are
   inert for a NYISO backcast** — audited as such in the PREREG **before** the solve, and
   corroborated by the keeper's live `cache_key` being unchanged at `95d4d8d167373eb7` at this HEAD.
3. The three substantive gates (S-2, S-3, S-4) — the ones that test whether the mechanism does what
   it claims and breaks nothing — **all cleared**.
4. Proceeding cannot let me cherry-pick: **PREREG §5.4 already stated the span's projected outcome
   before any solve** (2023 +6.33/+6.42 %, 2024 +7.00/+7.23 %, 2025 −6.31/−5.99 %, and 2022 still
   outside ±10 %). The span can only confirm or falsify that; it cannot be used to select anything.

**What this costs, stated plainly:** a reader who applies PREREG §6's partition literally reaches
branch (A) and stops here. That reader would still have the passthrough ratio, which is the number
the owner needs. What they would not have is a promotable full-span bundle — and rule 31
`[R-RETAIN]` is explicit that a session may recommend against promotion but may never foreclose the
owner's decision. Spending the span is the option that keeps the owner's choice open; stopping is
the one that forecloses it.

**The value stays frozen at 1.03.** Nothing about this disposition re-opens condition (c), and no
gate is re-tuned.
