# PREREG neiso-106 — the fossil offer-level scalar re-derived on the FULL-SPAN pass-through

**2026-09-06, session neiso-106 (continuing the neiso-104 → neiso-105 lane).** Written and
**committed before the solve**, per rule 1 `[R-STRUCT]` condition (c). Branch
`claude/neiso-106-fossil-scalar-2vb759`, cut from `origin/main` at **`013826a4`**.
**DATA PROFILE: neiso. ZERO LP MINUTES SPENT AT WRITING** — every number in §2–§4 is computed
from committed sidecars, reproduced in-session, and the reproduction script's output is committed
as `_neiso106_offer_level_phase0.json`.

Supersedes `PREREG-neiso105-offer-level-resized-2026-09-06.md` **on the VALUE only**. Carried
forward unchanged: neiso-104 §2.1 scope (the same 12 bands), neiso-104 §3.1 target, neiso-105 §5
risk register.

---

## 0. What this proposes, in one line

Replace the keeper's single scalar **0.93391** (a 6.609 % cut) with **0.95470** (a **4.530 % cut**)
on the same 12 markup bands — because the coefficient the 6.609 % was sized on was measured on one
year, and the full span has since measured it directly.

---

## 1. The governance collision, named first rather than buried

**`PREREG-neiso105-offer-level-resized-2026-09-06.md` §3 pre-committed that this scalar would not
move again**, in terms that plainly cover both directions: *"This number does not move again"*
(§2), and *"the scalar is NOT raised a second time — a third sizing iteration would be a sweep by
accumulation, whatever each single step's justification. It stops and the residual is reported"*
(§3). neiso-105 honoured that clause when the overshoot appeared, and said so on the dashboard.

**This session moves it a third time, on owner direction of 2026-09-06** (the session's own task
description: *"Re-derive the fossil offer-level scalar on the FULL-SPAN pass-through
coefficient"*). A lane's self-imposed stop rule is binding on the lane; it is not binding on the
owner, who is the authority that set the tuning channel's conditions in the first place. But the
clause existed, it was a good clause, and the honest record is that it is being overridden from
above rather than reasoned away from within. **This paragraph is the disclosure**, in the
neiso-104 §3.4 tradition of recording the thing a later reader would otherwise have to discover.

**Why the substance is identification and not the accumulation neiso-105 feared.** The
accumulation risk §3 named was *iterating the value against the residual it produces* — size,
look, resize, look. That is not what happens here, and the difference is checkable rather than
asserted:

- **The TARGET has never moved.** +3.4678 % (in-sample 2023–2025 geometric-mean price bias) was
  fixed in `PREREG-neiso104` §3.1 before any LP ran, on a stated principle, and is used here
  unaltered. §2.2 below reproduces it from the committed sidecars at **0.034674** — a 4×10⁻⁶
  agreement — and this lane still sizes on the **declared 0.034678**, because a target that moves
  when you recompute it is not a fixed target.
- **Only the COEFFICIENT changes, and a pass-through coefficient is a measured physical response**
  (dPrice/dMultiplier), not a criterion outcome. No gate was consulted to choose it.
- **The coefficient's replacement is a strictly better measurement of the same quantity**: the
  neiso-104 screen measured it on **one year** at one depth; neiso-105 measured it on **the whole
  scored span**, with the actual mechanism, at a second depth. Preferring the full-span measurement
  of a quantity to a one-year measurement of it is rule 14 `[R-ACCURATE]` reasoning, not selection.
- **It is not swept.** One value is declared here, before the solve, and §6 states the stop rule.

---

## 2. The arithmetic, redone from committed artifacts

Reproduced in-session from `hourly/system_<y>.parquet` (`pass == "P1"`, load-weighted on the
sidecar's own `demand`) and `frontend/data/backcast/bench/NEISO/<y>.json.gz :: bench.avgLMP.rt_lw`.
The pre-cut column reproduces `PREREG-neiso104` §1 to 3 dp.

### 2.1 What the 6.609 % cut actually delivered

| year | actual RT (lw) | pre-cut (neiso-99) | bias | **keeper (neiso-105)** | bias | move | **pass-through** |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2020 | 25.14 | 28.5859 | +13.707 % | 26.1196 | +3.897 % | −8.628 % | **1.3055** |
| 2021 | 47.77 | 52.1072 | +9.079 % | 49.6757 | +3.989 % | −4.666 % | **0.7061** |
| 2022 | 91.15 | 90.6026 | −0.601 % | 88.1319 | −3.311 % | −2.727 % | **0.4126** |
| **2023** | 38.10 | 39.2931 | +3.131 % | 36.8195 | −3.361 % | −6.295 % | **0.9525** |
| **2024** | 41.68 | 44.0407 | +5.664 % | 41.6720 | −0.019 % | −5.378 % | **0.8138** |
| **2025** | 70.23 | 71.3866 | +1.647 % | 68.9007 | −1.893 % | −3.482 % | **0.5269** |

### 2.2 The target (numerator) — FIXED, reproduced, not re-derived

Geometric mean of the three in-sample pre-cut model/actual ratios: **0.034674**. The declared
target from `PREREG-neiso104` §3.1 is **0.034678**. They agree to 4×10⁻⁶ (a rounding artifact of
the source table's 3-dp prices). **This lane sizes on the declared 0.034678.**

### 2.3 The coefficient (denominator) — measured on the full span

Three estimators of the same full-span response, all computed before choosing (disclosed rather
than presented as a single clean number, per the neiso-104 §3.4 discipline):

| estimator | pass-through | implied cut | implied scalar |
|---|---:|---:|---:|
| **geometric mean of the three in-sample moves ÷ cut** | **0.76550** | **4.5301 %** | **0.954699** |
| arithmetic mean of the three per-year pass-throughs | 0.76441 | 4.5366 % | 0.954634 |
| log-elasticity d ln P / d ln(multiplier) | 0.75929 | 4.5672 % | 0.954328 |

**Declared: 0.76550, the geometric estimator.** Stated reason, and it is the same principle §3.1
used to pick the target: the target is a geometric mean of ratios, so the coefficient that
converts it into a cut must be measured on the same geometry, or the two halves of one division
are not commensurable. **The choice is immaterial in any case** — the three span scalars
0.95433–0.95470, i.e. 0.034 pp of cut, i.e. about 0.03 % of price against a ±10 % C3a band. That
is worth stating plainly: this is not a knife-edge, and no reader need take the estimator argument
on trust.

### 2.4 The depth-linearity risk neiso-105 §3 named is now MEASURED, and it is small

neiso-105's named failure mode was that pass-through is measured at one depth and assumed linear.
**2025 is the only year solved at two depths, and it answers the question:**

| cut depth | 2025 move | 2025 pass-through |
|---|---:|---:|
| 4.53 % (neiso-104 screen) | −2.38 % | 0.5254 |
| 6.609 % (neiso-105 keeper) | −3.482 % | 0.5269 |

Ratio **1.0029** — depth-invariant to 0.29 % over a 46 % change in depth. So applying a coefficient
measured at 6.609 % to size a 4.530 % cut carries essentially no depth extrapolation, and this
lane's own extrapolation is *inward* (to a shallower cut inside the measured interval), which is
interpolation, not extrapolation. **What is NOT small is the YEAR dependence** — §3.

---

## 3. The finding this lane surfaces, which is worth more than the scalar

**Pass-through is strongly year-dependent and tracks delivered gas INVERSELY**, monotonically over
every solved year:

| delivered gas $/MMBtu | 1.98 (2020) | 2.93 (2023) | 3.07 (2024) | 4.50 (2021) | 6.24 (2025) |
|---|---:|---:|---:|---:|---:|
| pass-through | 1.3055 | 0.9525 | 0.8138 | 0.7061 | 0.5269 |

(2022, the highest-priced year in the record, sits at 0.4126 and completes the ordering.)

**Consequence, and it is a defect in rule 29 `[R-SCREEN]` rather than in either prior session.**
Rule 29 requires the screen year be *the year the mechanism's own measured footprint is largest*.
For a multiplier on `HR × fuel` that is, necessarily, the **highest-gas** year — which this table
shows is the **lowest-pass-through** year. So the rule prescribes screening where the mechanism's
response is least representative of its span-average, and then sizing from that screen.

**That is exactly what happened, and the receipt is now available.** neiso-104 declared a
pass-through of **0.765** from an across-year gas elasticity; its 2025 screen measured 0.525 and
the lane recorded the 0.765 identification as **REFUTED**. The full-span measurement of the actual
mechanism is **0.7655**. *The refuted number was right to within 0.07 %.* What was wrong was not
neiso-104 §3.2 — it was reading a 2025-only screen as a measurement of the span, which is what
rule 29 told it to do. **Escalated to the owner in §7; not acted on unilaterally here.**

This is also why this lane does **not** re-screen (see §5).

---

## 4. The declared value, and the pre-registered landing

> **DECLARED: a single scalar `0.95470` (a 4.530 % cut) applied to the SAME 12 markup bands** of
> `PREREG-neiso104` §2.1 — `committed` / `econ_low` / `econ_high` of CC_REGULAR, CC_CHP, CT_PEAKER,
> ST_GAS — computed against the **pre-cut (neiso-99) base values**, not compounded onto neiso-105's.
> Derivation, fixed: `0.034678 / 0.76550 = 0.045301`. Bands in
> `results/calibration/_neiso106_arm_offer_curve.json`, committed with this file.
>
> **Unchanged and still excluded**, exactly as in both prior PREREGs: all four `peak` bands (three
> equal their `phys_peak`; CT_PEAKER's 4.0 is the ISO-NE offer cap), every `phys_*`,
> `econ_low_share`, `pct_peaking`, and the declared-neutral CT_CHP group.

**A coincidence that must be named, not left for a reader to find: `0.95470` is numerically the
scalar `PREREG-neiso104` §3.3 declared (`0.9547`).** It is **not** the same number recovered — it
is the same number *re-derived from a different quantity*. neiso-104 got there from an **across-year
delivered-gas elasticity**, an analogy argument, which its own screen then rejected. This lane gets
there from the **directly measured full-span response of this mechanism itself** — 12 bands, three
years, one solve. The agreement is a *result* (§3: the analogy was in fact sound and the screen
year was the problem), not a derivation reused. Nothing in §2 depends on neiso-104 §3.2 being right.

**Headroom against measured physics at 4.530 %** — strictly less binding than the keeper's 6.609 %,
so every disclosure below is a *relaxation* of one already carried: CC_REGULAR `econ_low`
1.00→0.9547 (phys 0.854) and `econ_high` 1.15→1.0979 (0.940); ST_GAS 0.85→0.8115 / 0.89→0.8497
(0.692/0.731); CT_PEAKER 1.00→0.9547 (0.745/0.700). All above their measured marginal.
`CC_CHP.committed` and `ST_GAS.committed` remain below their `avg_committed_p50` — the pre-existing
neiso-104 §2.1 disclosure, **shallower** here than in the incumbent keeper.

### 4.1 Pre-registered landing, every year, before the solve

Predicted at each year's **own measured** pass-through (§2.1), which §2.4 licenses:

| year | tier | pre-cut | keeper (k105) | **predicted** | predicted C3a |
|---|---|---:|---:|---:|---|
| 2020 | validation | +13.707 % | +3.897 % | **+6.983 %** | PASS |
| 2021 | validation | +9.079 % | +3.989 % | **+5.590 %** | PASS |
| 2022 | validation | −0.601 % | −3.311 % | **−2.458 %** | PASS |
| **2023** | train | +3.131 % | −3.361 % | **−1.319 %** | PASS |
| **2024** | train | +5.664 % | −0.019 % | **+1.768 %** | PASS |
| **2025** | train | +1.647 % | −1.893 % | **−0.779 %** | PASS |

In-sample geometric-mean bias **−0.119 %** (keeper −1.767 %, pre-cut +3.467 %); in-sample MAE
**1.289 %** (keeper 1.758 %). Unlike neiso-104 §3.3, **no year's C3a margin is inside the method's
own error** — the tightest is 2020 at 3.0 pp of slack — so this lane pre-registers all six as PASS
rather than pre-registering one as undetermined.

**C3a is therefore NOT the informative gate on this arm.** Its landing is arithmetic from measured
per-year coefficients and would be a poor test of anything. **The informative gates are the
non-target ones** — C3b, C1, C2, C8 — which §6 makes the promotion condition.

---

## 5. Execution

- **STRAIGHT TO THE FULL SPAN.** One `--year 2023 2024 2025` invocation, one bundle (rule 16
  `[R-ALLYEARS]`). **No screen**, for three independent reasons, any one sufficient: (i) rule 29's
  screen gate is **structural**, and neiso-104 already ran it on these same 12 bands — G2 footprint
  PASS (largest out-of-scope move 0.005 TWh against ~114 TWh), G3 identity PASS (exactly 12 bands
  moved, every `phys_*` and all four `peak` bit-identical) — and neither gate can change when only
  the magnitude does; (ii) §2.4 measures depth-invariance directly, so the one thing a re-screen
  could test is already measured; (iii) §3 shows the prescribed screen year would be the least
  representative year in the record. Re-screening would spend an LP to re-confirm two gates that
  cannot move, on the worst available year.
- **G-CTRL form 4: the keeper's committed bundle IS the control. No control solve.** neiso-104
  MEASURED this on this ISO at this HEAD-distance — a same-HEAD control replay reproduced the
  then-keeper to 4 dp on load-weighted price and 0.001 TWh on every class, across 111
  live-candidate solve-path files **and four environment deltas**.
- **G-DRIFT (rule 29(b)), run and recorded here before the arm is solved.** The keeper's
  `git_sha` **`8b2c890d` resolves and is an ancestor of HEAD** (asserted, not assumed — the clone
  is shallow and an unresolvable anchor would make `git diff` silently report no drift).
  `git diff 8b2c890d..HEAD -- src/market_sim scripts/run_calibration.py
  scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
  touches 12 files. **Every hunk classifies INERT for a NEISO backcast:**

  | file(s) | classification |
  |---|---|
  | `config/iso_configs.py` (+67) | capx D75-R-ARM: `pjm_vre_accreditation_vintage` armed via `_pjm_config` `default_scenario_overrides` — **another ISO's branch**, and forecast-only capacity accreditation a `mode="backcast"` run never enters |
  | `config/scenarios.py` (+44) | adds `miso_seam_neighbour_hourly_ladder` (+ its cache-key entries) — **default-off, absent from this keeper's recipe** (verified `False` in the keeper `run_config.json`), MISO-scoped |
  | `config/constants.py` (+1) | one re-export, `PJM_SOLAR_CLASS_MIX_FIXED_TILT_SHARE` — **another ISO, forecast-only path** |
  | `scripts/run_calibration.py` (+38) | the `miso_seam_neighbour_hourly_ladder` guard and log text, reached only inside `reference_price_interface and iso in INTERFACE_NEIGHBORS` — **`reference_price_interface: False` in this keeper's recipe** |
  | `model/interchange/spec.py` (+134), `miso.py` (+55) | MISO seam ladder registry and injector — **another ISO's branch** |
  | `model/interchange/import_nodes.py` (+19) | `_inject_seam_ladder` gains one optional `hourly_anchor=None` parameter; with the default, the assignment is the pre-change `mc[row, :] = prices[k]` line — **provably inert when unarmed** |
  | `results/cache.py` (+32, **0 deletions**) | module-docstring cache-epoch ledger entry only — **no executable line changed** |
  | `data/raw/reference/caiso-supply-consistent-demand/*` (3 CSV + provenance) | **another ISO's input** |

  **All INERT ⇒ G-CTRL form 4 is valid and no control LP is spent.**
- **Environment, read from the driver's own guard rather than assumed** (the neiso-104 §0 error,
  corrected by `ADDENDUM-neiso104-env-correction-2026-09-06.md`, is not repeated). This session
  installed from the repo's pinned `requirements.txt` and gets **highspy 1.14.0 / pandas 3.0.3 /
  pydantic 2.13.4 / numpy 2.4.6 / scipy 1.17.1 / pyarrow 24.0.0** (verified with
  `importlib.metadata.version`, **not** `Highs().version()`, which returns the bundled *solver*
  1.14.0 and would read as a false match). That **matches neiso-99's** bundle environment exactly
  and **differs from neiso-105's** (highspy 1.15.1, pandas 3.0.5, pydantic 2.13.5) — i.e. the
  neiso-104 delta pair, reversed. neiso-104 measured that pair inert to 4 dp on load-weighted price
  and 0.001 TWh per class. The driver prints its own mismatch warning in its first four lines; it
  will be **read and recorded verbatim in the finding**, whatever it says.
- **Gates on the full span**: C1, C2, C3a, C3b, C3c, C4, C6, C8 by `scripts/calibration_verdict.py`
  after registration. C6 needs a `calibration_attestation.json` written into the replay bundle
  (a replay carries none) with the `authorized_price_tuning` block declared and
  `no_fit_to_price_residuals` **FALSE**, scoped by the declaration.
- **DOF ledger (rule 21 `[R-DOF]`, owner ruling R-AY)**: `0.95470` is a free parameter whose
  identification source is **the ruling** — *"price residual, authorized channel (rules 1/13
  amendment 2026-09-05)"* — reported at full magnitude, not presented as a measured input.
- **Rule 30(c) holds**: the touchpoints are reported, never chased. NEISO's determination is its
  train-tier verdict.

---

## 6. The promotion bar, and the risk that decides it

**Restated at full strength, unchanged from neiso-105 §5 because the exposure is unchanged:
NEISO's `CALIBRATED` rests on C3c being the LONE failure** (rubric v3.3 guard (a)). The incumbent
scores 0 FAILs with C3c the single ledgered caveat. **If this arm flips any second criterion, the
standing rule goes silent, BOTH failures stand, and NEISO reads `NOT-YET`.** C3b price
duration/shape is the live exposure: the level moves while the four physically-pinned `peak` bands
stay put.

**One structural argument reduces that exposure, and it is stated as a reason for confidence, not
a prediction of the gate**: this arm's scalar **0.95470 lies strictly between two configurations
that both scored C3b PASS on these same three years** — neiso-99 at 1.0 and neiso-105 at 0.93391 —
and every one of the 12 bands moves monotonically in the scalar. The arm is bracketed, not
extrapolated. It is bracketed *closer to the incumbent's predecessor*, which is the direction of
less change from the longest-standing PASS.

**Promotion condition, pre-committed: the determination must be NOT WORSE** (rule 22 D-5(b),
re-verified on committed artifacts with `calibration_verdict.py --run-id`, no solve, before any
re-key). **If the re-derived scalar improves C3a but flips anything else, the incumbent stands and
this lane reports that as its result.** The arm is registered either way (rule 15
`[R-DASHBOARD]`).

**Stop rule, pre-committed.** This is the **third and last** sizing of this scalar. The coefficient
has now been measured on the full span with the actual mechanism at two depths; there is no better
measurement of it left to make, so there is no legitimate reason for a fourth. **If this arm
overshoots or undershoots its −0.119 % prediction, the scalar is not moved again in either
direction** — the residual is reported and the next move is a structural one. neiso-105 wrote the
same clause and honoured it; the only thing that reopened it was a *better measurement of the
coefficient*, and that route is now closed.

---

## 7. Owner ask (filed, not acted on)

**Rule 29 `[R-SCREEN]`'s screen-year selection rule is defective for level-multiplier mechanisms,
and §3 is the receipt.** The rule selects the year of largest absolute footprint; for a multiplier
on `HR × fuel` that is the highest-gas year; and pass-through varies inversely and monotonically
with gas (1.31 at $1.98 down to 0.53 at $6.24). So the rule prescribes measuring the mechanism's
response where it is least like the span, and the measured cost of that in this lane was a 46 %
sizing error and one extra full-span solve. **Proposed narrow amendment, for the owner to accept,
modify or refuse:** where a mechanism's response coefficient is *itself* the object being measured
and the screen is being used to size it, the screen year should be the year whose response is
**most representative of the scored span** (nearest the span median of the driver the coefficient
tracks), with the driver and the choice named in the PRECOMMIT before the screen runs — the
existing largest-footprint rule being retained for its original purpose, which is establishing that
a mechanism *does something at all*.

**This lane does not act on the proposal**; it goes straight to the full span for the three reasons
in §5, each of which stands independently of whether the rule is ever amended.
