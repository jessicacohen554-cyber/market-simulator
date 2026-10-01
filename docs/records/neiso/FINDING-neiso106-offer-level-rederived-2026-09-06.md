# FINDING neiso-106 — the re-derived scalar lands on its pre-registered target to 0.02 pp, and the neiso-104 refutation turns out to have been a screen-year artifact

**Session.** neiso-106, NEISO lane. Branch `claude/neiso-106-fossil-scalar-2vb759`, cut from
`origin/main` at **`013826a4`**. 2026-09-06. **DATA PROFILE: neiso.**
Pre-registration: `PREREG-neiso106-offer-level-rederived-2026-09-06.md` (committed `773411e5`,
**before the solve**); governance addendum `ADDENDUM-neiso106-prereg-collision-2026-09-06.md`.

**LP spent: ONE full-span invocation (2023 · 2024 · 2025), one bundle. No screen, no control.**
All six solves were genuine, not cache hits.

---

## 0. Headline

**KEEPER → `2026-09-06-neiso-106-fossil-offer`, DETERMINATION `CALIBRATED`, criterion for criterion
identical to the superseded keeper.** A single scalar **0.95470** (a **4.530 %** cut) on the same
12 markup bands, replacing **0.93391** (6.609 %). **Only the coefficient in the sizing division
moved; the target never did.**

**The arm lands where it was pre-registered, to 0.02 pp on every one of the three years** — which
is the result, because the landing was predicted from measured per-year coefficients *before* the
LP ran and could have refuted the whole identification.

| year | pre-cut (neiso-99) | superseded keeper (neiso-105) | **this keeper** | **pre-registered** | error |
|---|---:|---:|---:|---:|---:|
| 2023 | +3.131 % | −3.361 % | **−1.338 %** | −1.319 % | **−0.019 pp** |
| 2024 | +5.664 % | −0.019 % | **+1.764 %** | +1.768 % | **−0.004 pp** |
| 2025 | +1.647 % | −1.893 % | **−0.769 %** | −0.779 % | **+0.010 pp** |
| **in-sample geometric-mean bias** | **+3.467 %** | **−1.767 %** | **−0.124 %** | **−0.119 %** | **−0.005 pp** |
| **in-sample MAE** | 3.481 % | 1.758 % | **1.290 %** | 1.289 % | — |

**Three results beyond the scalar, in ascending order of how much they should change what other
lanes do:**

1. **The PREREG's named live risk did not fire.** C3b price duration/shape PASSES, so rubric v3.3
   guard (a) holds and NEISO stays `CALIBRATED` rather than dropping to `NOT-YET`. §3.
2. **The rule-29 `[R-SCREEN]` mechanics point neiso-105 filed is now PROVEN, with a receipt.** §4.
3. **This arm's 2025 solve is bit-identical to the neiso-104 screen arm that rule 29(c) required to
   be deleted** — reconstructing a deleted result inside a registrable bundle, and upgrading a
   claim neiso-104 had to state weakly after its own correction. §5.

---

## 1. What changed, and why it is identification rather than a sweep

`0.034678 / 0.76550 = 0.045301` → scalar **0.95470**.

- **Numerator (target): UNCHANGED, and never has changed.** +3.4678 %, the in-sample 2023–2025
  geometric-mean price bias, fixed in `PREREG-neiso104` §3.1 before any LP ran. Reproduced in this
  session from the committed sidecars at **0.034674** — agreement to 4×10⁻⁶ — and this lane still
  divides by the **declared** 0.034678, because a target that moves when you recompute it is not a
  fixed target.
- **Denominator (coefficient): replaced with a strictly better measurement of the same physical
  quantity.** The neiso-104 screen measured pass-through on **one year at one depth** (0.5247,
  2025). The superseded keeper's own full-span solve measures it on **three years**: the geometric
  mean of its in-sample price moves (−5.0592 %) over the cut that produced them (6.609 %) =
  **0.76550**.

A pass-through coefficient is a measured physical response (dPrice/dMultiplier), not a criterion
outcome. **No gate was consulted to choose it**, one value was declared before the solve, and
`PREREG-neiso106` §6 pre-commits this as the third and **last** sizing.

**The estimator choice, disclosed rather than presented clean** (the `PREREG-neiso104` §3.4
discipline). All three candidates were computed before choosing:

| estimator | pass-through | implied cut | implied scalar |
|---|---:|---:|---:|
| **geometric mean of the three in-sample moves ÷ cut** | **0.76550** | **4.5301 %** | **0.954699** |
| arithmetic mean of the three per-year pass-throughs | 0.76441 | 4.5366 % | 0.954634 |
| log-elasticity d ln P / d ln(multiplier) | 0.75929 | 4.5672 % | 0.954328 |

The geometric one is declared because the *target* is a geometric mean and the two halves of one
division must share a geometry. **The choice is immaterial**: the three span scalars
0.95433–0.95470 — 0.034 pp of cut, about 0.03 % of price against a ±10 % band. No reader need take
the estimator argument on trust.

**The governance disclosure is `PREREG-neiso106` §1 plus its addendum, and it is not softened
here.** This is the third sizing (4.53 % → 6.609 % → 4.530 %); `PREREG-neiso105` §3 pre-committed
the scalar would not move again in either direction; that lane-level stop rule is overridden by
owner direction, not reasoned away. What the addendum adds is that neiso-105's **own matrix stamp**
had already drawn the line — *"a future in-sample re-derivation on the full-span coefficient …
**is legitimate** (the target never moved); a second resize against the gates would not be"* — so
the incumbent lane wrote the test its successor is judged by, before knowing which way it would
cut, and this lane is on the licensed side of it.

---

## 2. Identity and footprint, re-checked on this arm's own artifacts

Not inherited from neiso-104's screen — re-measured here, against the **pre-cut neiso-99 base**:

| check | measured | verdict |
|---|---|---|
| bands moved | **exactly 12**, the declared set | PASS |
| ratios | **one distinct ratio, 0.954700**, on all 12 | PASS (a single scalar, not 12 numbers) |
| out-of-scope band moves | **0** | PASS |
| `phys_*` / all four `peak` / `econ_low_share` / `pct_peaking` | **bit-identical** | PASS |
| largest out-of-scope class energy move (2025) | **0.0017 TWh** (CT_CHP) against ~114 TWh | PASS |

Energy response, arm − superseded keeper, 2025 (TWh): CC_REGULAR −0.0151, CC_CHP +0.0104, ST_GAS
+0.0024, CT_PEAKER −0.0013 — all in scope; CT_CHP +0.0017, oil +0.0002, COAL_BIT +0.0002, ST_CHP
+0.0001 — second-order re-dispatch. Nothing in the must-run, renewable, hydro or interchange rows
is repriced.

---

## 3. The gates, and the risk that did not fire

`scripts/calibration_verdict.py --run-id 2026-09-06-neiso-106-fossil-offer`:

| criterion | tier | this keeper | superseded keeper |
|---|---|---|---|
| C1 fuel-mix by class | load-bearing | **PASS** (all 12/12, free 8/8) | PASS (12/12, free 8/8) |
| C2 system volume | load-bearing | **PASS** | PASS |
| C3a mean LMP | load-bearing | **PASS** | PASS |
| **C3b price duration/shape** | load-bearing | **PASS** | PASS |
| C3c price tail / scarcity | supporting | CAVEAT [ledgered] | CAVEAT [ledgered] |
| C4 fleet hourly dispatch r | supporting | **PASS** | PASS |
| C6 governance | protective | **PASS** | PASS |
| C8 forced-energy share | protective | **PASS** | PASS |
| **determination** | | **CALIBRATED** | CALIBRATED |
| grade summary | | scored 8 / target 7 / commercial 0 / ledgered 1 / **0 FAILs** | identical |

**C3b was the pre-registered live exposure** (`PREREG-neiso106` §6): NEISO's `CALIBRATED` rests on
C3c being the *lone* failure under rubric v3.3 guard (a), so any second criterion flipping takes
the ISO to `NOT-YET`. It did not flip, and the PREREG's structural reason is the one that held:
**0.95470 lies strictly between two configurations that both scored C3b PASS on these same three
years** (neiso-99 at 1.0, neiso-105 at 0.93391), with all 12 bands monotone in the scalar — the arm
is bracketed, not extrapolated.

**Promotion bar met.** The superseded keeper re-verifies at HEAD to the identical criterion set and
the identical grade summary, so the arm is **NOT WORSE** and the rule 22 D-5(b) stop does not fire.
The promotion buys accuracy inside an unchanged verdict.

**Two diagnostic rows moved and neither reaches a gate; recorded because they are the only things
that got worse.** D-4 off-window binding goes PASS → FAIL on one row — 2024 `chp_steam`, plant
54605 (Pratt & Whitney, 26 MW CT_CHP), floored for **0.0001 TWh**, 0.2 % of that mechanism's forced
energy, over 25 binding hours whose measured median output is 0 MW. D-2 forced shares move
CT_PEAKER 2023 21.4 → 20.9 %, ST_GAS 2024 37.0 → 32.3 %, ST_GAS 2025 31.7 → 30.6 % — all three
*toward* their caps. **C8 PASSES** because every one of those classes is immaterial under rule 20's
own 2 %-of-load floor (CT_PEAKER 0.5–1.5 %, ST_GAS 0.1–0.3 %, COAL 0.2–0.3 %), so they are reported
by the diagnostics and not gated. The D-4 row is a **0.0001 TWh** artifact at a 26 MW plant; it is
named here rather than left in a JSON file, and it is not worked, because working it would be
chasing four parts in a billion.

---

## 4. The rule-29 finding, with its receipt

**Pass-through is strongly YEAR-dependent and tracks delivered gas inversely and monotonically:**

| delivered gas $/MMBtu | 1.98 (2020) | 2.93 (2023) | 3.07 (2024) | 4.50 (2021) | 6.24 (2025) |
|---|---:|---:|---:|---:|---:|
| pass-through | **1.3055** | **0.9525** | **0.8138** | **0.7061** | **0.5269** |

2022, the highest-priced year in the record, sits at **0.4126** and completes the ordering. The
spread is **3.2×** across the six solved years.

**It is NOT depth-dependent**, which `PREREG-neiso105` §3 had named as the live hazard and which is
now measured rather than assumed. 2025 is the only year solved at two cut depths:

| cut depth | 2025 move | 2025 pass-through |
|---|---:|---:|
| 4.53 % (neiso-104 screen) | −2.38 % | 0.5254 |
| 6.609 % (neiso-105 keeper) | −3.482 % | 0.5269 |

**Ratio 1.0029** — depth-invariant to 0.29 % over a 46 % change in depth. So a coefficient measured
at one depth may be reused at another, and the *inward* extrapolation this lane performed (6.609 %
→ 4.530 %, inside the measured interval) carries essentially no depth risk. The 0.02 pp landing in
§0 is the independent confirmation.

**The defect this exposes in rule 29 `[R-SCREEN]`.** The rule requires the screen year be *the year
the mechanism's own measured footprint is largest*. For a multiplier on `HR × fuel` that is
necessarily the **highest-gas** year — which the table shows is the **lowest-pass-through** year.
The rule therefore prescribes measuring a mechanism's response where it is least like the span, and
then sizing from that measurement.

**The receipt, which is what makes this more than an argument.** `PREREG-neiso104` §3.2 declared a
pass-through of **0.765** from an across-year delivered-gas elasticity. Its 2025 screen measured
0.525, and `FINDING-neiso104` recorded that identification **REFUTED**, over-predicting by 46 %.
**The full-span measurement of the actual mechanism is 0.7655** — the refuted number was right to
within **0.07 %**. What was wrong was never neiso-104 §3.2; it was reading a 2025-only screen as a
measurement of the span, which is what rule 29 told it to do. The measured cost in this lane was a
46 % sizing error, one superseded keeper, and one extra full-span solve.

**Escalated to the owner, not acted on.** `PREREG-neiso106` §7 proposes a narrow amendment: where a
mechanism's *response coefficient* is itself the object being measured and the screen is being used
to size it, the screen year should be the year whose response is **most representative of the
scored span** (nearest the span median of the driver the coefficient tracks), named in the PRECOMMIT
before the screen runs — the existing largest-footprint rule retained for its original purpose,
establishing that a mechanism does something at all. **No rule was amended by this lane**, and the
decision to go straight to the full span here rests on three independent reasons (`PREREG-neiso106`
§5), none of which requires the amendment.

---

## 5. An unexpected cross-check: the deleted screen arm is reproduced bit-for-bit

Noticed in the solve log rather than looked for. This arm's **2025** solve reports:

| | neiso-104 screen arm (2026-09-06, **deleted** under rule 29(c)) | **this arm** |
|---|---|---|
| P0 objective | 3,554,608,783.6457 | **3,554,608,783.6457** |
| P0 simplex iterations | 188,740 | **188,740** |
| P1 simplex iterations | 59,473 | **59,473** |
| highspy / pandas / pydantic | 1.15.1 / 3.0.5 / 2.13.5 | **1.14.0 / 3.0.3 / 2.13.4** |

Three consequences, in ascending order of usefulness:

1. **The declared scalar reproduces neiso-104's config exactly.** 0.95470 is numerically the
   `0.9547` that PREREG declared — reached here from the measured full-span response, there from an
   across-year gas elasticity. The agreement of the *configs* is arithmetic; the agreement of the
   *derivations* is §4's finding.
2. **The deleted screen result is reconstructed inside a registrable bundle.** Rule 29(c) required
   both neiso-104 bundles deleted before merge, and `FINDING-neiso104` recorded that its
   measurement "cannot now be tightened without a re-solve". It has been, at zero marginal cost.
3. **It upgrades a claim neiso-104 had to state weakly.**
   `ADDENDUM-neiso104-env-correction-2026-09-06.md` retracted that session's "bit-identical" wording
   down to *4 dp on load-weighted price and 0.001 TWh per class*, because no per-cell comparison had
   been run. The LP objective agreeing to **13 significant figures** with an identical simplex path,
   **across the same four environment deltas in reverse**, is a stronger statement about that
   environment pair than the one that was retracted — and it is reported at the strength actually
   measured, not beyond it.

---

## 6. Environment, read rather than assumed

The replay driver's guard printed this in its **first four lines**, and it is recorded verbatim
because not reading it is precisely the neiso-104 error:

```
WARNING: replay environment differs from the bundle's recorded environment — byte-identity is not guaranteed:
  highspy: bundle '1.15.1' != now '1.14.0'
  pandas: bundle '3.0.5' != now '3.0.3'
  pydantic: bundle '2.13.5' != now '2.13.4'
```

This session installed from the repo's **pinned** `requirements.txt`, so its environment matches the
**neiso-99** bundle exactly and differs from **neiso-105's**. Package versions were read with
`importlib.metadata.version`, **not** `highspy.Highs().version()` — which returns the bundled
*solver* version 1.14.0 and would have read as a false match. §5 then measures the delta pair
inert at bit level, so the mismatch is disclosed *and* answered.

The touchpoint replay in §7 printed **no** such warning, because its source bundle was solved in
this same environment.

---

## 7. Governance ledger for this run

- **G-CTRL form 4 — the incumbent's committed bundle IS the control. No control LP spent.**
  Validated by **G-DRIFT**, recorded in `PREREG-neiso106` §5 before the arm was solved: the
  superseded keeper's `git_sha` **`8b2c890d` resolves and is an ancestor of HEAD** — asserted, not
  assumed, because the clone is shallow and an unresolvable anchor makes `git diff` silently report
  no drift — and all **12** changed solve-path files classify INERT for a NEISO backcast (PJM
  forecast accreditation; the MISO seam ladder behind a default-off flag verified `False` in this
  recipe; a `_inject_seam_ladder` signature change that is provably the pre-change line when
  unarmed; a **docstring-only** `cache.py` hunk with 0 deletions; another ISO's input CSVs).
- **Rule 1 `[R-STRUCT]` conditions (a)–(e)**: (a) the channel is `offer_curve_by_group` markup bands
  only; (b) ONE config across every scored year; (c) declared ex ante and committed before the
  solve, never swept against the gates; (d) merit-order adjustment is intended; (e) declared in the
  attestation's `authorized_price_tuning` block, with `no_fit_to_price_residuals` **FALSE** and
  scoped by the declaration rather than claimed away. **C6 PASSES.**
- **Rule 21 `[R-DOF]`**: **one** ledgered free parameter, `offer_curve_fossil_level_scalar` =
  0.95470, identification source *"price residual, authorized channel (rules 1/13 amendment
  2026-09-05)"* — the ruling, not a measured input — reported at full magnitude. It is a
  re-derivation of the same knob, **not an additional one**; the ledger entry count does not rise.
- **Rule 16 `[R-ALLYEARS]`**: one `--year 2023 2024 2025` invocation, one bundle.
- **Rule 22**: the in-sample solve spends no tier. The touchpoints spend the **validation** tier,
  which NEISO's `complete` marker authorizes and the freeze does not cover
  (`scope.tiers = ['locked_test']`); the driver printed the iterable-selection-evidence warning and
  the registration-time marker re-check (owner ruling R-AZ) was re-run at registration.
  **The touch-once locked test (2019 / H1-2026) is UNTOUCHED and remains frozen for every ISO.**
- **Rule 25 `[R-ISO-SCOPE]`**: no other ISO's shard, keeper, status part or board row was touched;
  no `ScenarioConfig` default moved.
- **Rules 28b/28d**: no new mechanism was tested and **no cell verdict moves** — the channel is the
  same `offer_curve_by_group` cell, already `K`, and only its magnitude changed.

---

## 8. What this does not close

- **The C3c scarcity tail is untouched** and remains the lone ledgered caveat at the same
  magnitude (model 0 h > $300/MWh against RT actuals 15 / 8 / 20 h). Nothing in a markup scalar can
  reach it, and it must never be reached by an offer adder tuned to the tail. The 2026-07-11
  frontier designation stands.
- **The level bias is now small, not zero** (−0.124 % in-sample). §6's stop rule binds: the residual
  is reported and the next move on it is structural, not a fourth sizing.
- **The diurnal price amplitude gap is unchanged and large** — 26.4 / 22.4 / 32.7 % of measured hod
  range, band-free and reported-only under rubric v3.5. A level scalar cannot move a shape.
- **The D-4 row in §3** is disclosed and not worked.
- **The rule-29 amendment is an owner ask, not a change.** Nothing in this session depends on its
  outcome.
