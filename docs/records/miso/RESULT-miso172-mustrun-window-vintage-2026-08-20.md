# RESULT miso-172 (arm 1) — the per-YEAR must-run window: REJECTED-AS-ARMED on K-2, with the target repaired to within 2.2 pp of clearing

**Session miso-172, 2026-08-20.** Executes
`PREREG-miso172-mustrun-window-vintage-2026-08-20.md`, committed before either
arm result was read. Control `miso172_control`, arm `miso172_peryear`, both
`--year 2023 2024 2025` sequential in one invocation (rules 12/16).

**Mechanical verdict: REJECTED-AS-ARMED on K-2** (two of three years outside the
pre-registered liveness band). Under the prereg's own candidate rule — "keeper
candidate iff all kills are silent" — that stands as written and is **not**
reinterpreted here; the forensic in §4 was produced after the result and does
not get to convert a pre-registered kill into a pass (the miso-170 discipline,
second application).

## 1. K-0 — the control is bit-identical, so both new mechanisms are byte-inert when off

Same-recipe `replay_keeper` of the keeper `2026-08-19-miso-170-sitegrain` at this
session's HEAD with **both** new flags default-off:

> **12 of 12 scored sidecars, all three years: `max|diff| = 0.0`, non-numeric
> columns equal.**

Run and reported BEFORE any arm output was read, as pre-registered.

## 2. The gates, as scored

| gate | verdict | measurement |
|---|---|---|
| **K-0** control inertness | **PASS** | 12/12 sidecars, `max\|diff\| = 0.0` |
| **K-1** window exactness | **PASS** | unit grain, from the arm's own `floors/<year>_P1.npz`: every one of the 7 live ST_GAS plants lands inside its per-year `k` in all three years; the control's counts equal the pooled `k` exactly |
| **K-2** liveness | **FAIL AS WRITTEN** | Δ D-2 forced TWh: 2023 **−0.0961** in `[−0.163, −0.054]`; 2024 **−0.0714** vs `[−0.047, −0.016]` **OUT**; 2025 **+0.3086** vs `[+0.094, +0.283]` **OUT** |
| **K-3** conduct failures | **PASS** | 2 → 2, **ZERO NEW**, zero new off-window; the pre-named 1402-2023 survivor present |
| **K-4** C8 | **2023 FAIL exactly as pre-registered** | ST_GAS share 30.53 → 30.21 % (2023), 30.93 → 30.69 % (2024), **42.56 → 43.46 % (2025)** |
| **K-6** ST_GAS shape | **PASS** | `profile_r` 0.950 / 0.957 / 0.972 (control 0.951 / 0.958 / 0.975); `cv_ratio` 1.405 / 1.095 / 1.256 |
| **K-5** record flips | **UNSCORED** | `calibration_verdict.py` resolves only REGISTERED runs; scored after registration (§6) |

## 3. What the lever actually did to its target

Plant 1402 Little Gypsy, the keeper's sole surviving conduct failure and MISO's
sole C8 blocker, from the D-4 per-unit conduct rows of both bundles:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| floored TWh, control → arm | 0.3529 → **0.1254** | 0.4618 → **0.5568** | 0.4819 → **0.6470** |
| binding hours, control → arm | 2,567 → **912** | 3,359 → **4,050** | 3,505 → **4,706** |
| metered zero-share over binding hours | 71.17 % → **52.19 %** | 42.42 → 44.35 % | 33.15 → 34.66 % |
| conduct verdict | FAIL → **FAIL** | pass | pass |

**Down 64.5 % in 2023 and up 20.6 % / 34.3 % in 2024–25** — the directional
signature of a vintage repair, not a haircut. A lever that only ever removed
forcing would be the latter.

**The 2023 conduct rider missed by 2.2 percentage points.** It fails when the
metered median over binding hours is ≤ 0, i.e. at a zero-share ≥ 50 %; the arm
lands at **52.19 %**, against 71.17 % in the control. The prereg predicted the
arm would sit at ~64 % (measured at WINDOW grain); the binding set concentrates
further into the top of the window than the window average, so the outcome beat
the prediction by ~12 pp and came within a hair of clearing.

## 4. Why K-2 missed — the instrument, not the mechanism (post-hoc, non-absolving)

The K-2 predictor was `predicted = control × (est_arm / est_pool)` with
`est(k, level) = Σ_{top-k load hours} min(level, nameplate × availability)`.
Its floor-energy half is **exact** — read off the arm's own floors, plant 1402
lands at 0.1718 TWh against a pre-solve prediction of 0.1716, and 0.7406 /
0.7810 against 0.7406 / 0.7811 in 2024/25 (four decimals, three years).

What the instrument held FIXED, and should not have, is each plant's **at-floor
rate** — the share of its floored hours in which dispatch actually sits at the
floor. Moving the window reshuffles *which* hours bind, so that rate moves too.
The two out-of-band years are carried by plants the lever was never aimed at:
3457 (−11.3 % in 2023, +12.3 % in 2025 against a predicted ∓7 / +5 %) and 6035
(−21.0 % / +14.4 % against −12 % / +12 %). Every plant moved in a direction its
own per-year fraction predicts; none moved perversely.

This is a limitation of the forecast of the mechanism, not evidence the
mechanism misbehaved — **and it does not change the mechanical verdict**, which
is what the pre-registration binds. A successor re-running this lever should
band K-2 on the FLOOR-energy basis (which the instrument predicts exactly) or
widen the D-2 band to absorb at-floor-rate drift.

## 5. Reported against interest

* **2025's ST_GAS forced share rises, 42.56 → 43.46 %**, in the worst year and
  against a 30 % cap. This is the repair working correctly — 1402's true 2025
  synchronization share is 0.658, well above the pooled 0.508 — but it is a real
  regression on C8's budget leg, and it is the reason the lever cannot be sold
  as a C8 win.
* **C8-2023 does NOT clear**, exactly as §3 of the prereg predicted in advance.
* The control's REGENERATED diagnostics carry an extra D-4 failure the committed
  keeper does not: plant 990, 2023, convicted on a `reliability_floor` of
  **0.0000 TWh across ONE binding hour** ("100.0 % of the mechanism's forced
  energy"). Pre-existing rebuild-path exposure (RESULT-miso171 §4's family,
  now measured at MISO), disclosed in the control bundle's own commit. It does
  not contaminate this A/B: `st_gas_mustrun_per_plant` — the sole mechanism the
  arm moves — reproduces EXACTLY (7.2596 / 7.3357 / 9.3426 TWh), and every gate
  compares regen-control to regen-arm through the same path at the same HEAD.

## 6. Open

K-5 and the determination need both bundles registered (`calibration_verdict.py`
resolves only registered runs). Registration is deferred to the end of the
session because the payload render competes with a live ~13 GB solve on a 15 GB
box; it lands with arm 2 (rule 15).

## 7. The successor, identified pre-solve and unchanged by the result

The 2023 residual is an **availability / part-year lay-up** object, not a window
object:

> 1402's outage-extract availability in 2023 is **0.541 in January–February** and
> **~0.95–1.00 in November–December**, while its meter reads **0.000 / 0.015**
> and **0.033 / 0.058** online. The model believes half to all of a 916 MW
> steamer is available in exactly the months it never ran.

Same "laid up but reads ~available" family the miso-170 census repaired, at
**part-year** grain, which that census cannot see (it requires all 18 pooled
(year, 4-hour-block) cells at zero). With the vintage repair now carrying 1402
to within 2.2 pp of the rider, this object has ample room to clear it. Its own
identification, its own A/B, its own DOF answer. **1402 is never added to the
lay-up census** (rules 1/14; the line has now held four times).
