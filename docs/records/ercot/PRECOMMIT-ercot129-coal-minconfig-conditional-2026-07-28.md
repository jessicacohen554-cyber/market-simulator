# PRE-COMMIT — ERCOT-129: the availability-CONDITIONAL coal min-config floor

**Date** 2026-07-28 · **ISO** ERCOT · **Lane** ercot129-conditional ·
**Keeper** `2026-07-26-ercot115-coal-marginal-hr` (untouched) ·
**Control** `2026-07-28-ercot128-unit-grain-coal`
(`results/calibration/ercot128_unit_grain`) — the availability-SCALED arm this
one corrects ·
**Arm bundle** `results/calibration/ercot129_conditional` ·
**Written and pushed BEFORE any year is solved.** Nothing below may be edited
after the first solve starts; a gate that fails, fails.

---

## 0. The single change

ERCOT-128 §P4 root-caused its own failure: the coal min-config floor is applied
as `min_config_share × pmax × availability[g,t]`, i.e. **availability-SCALED**,
and that is the wrong physics. A minimum online configuration does not shrink
when units go out — a 4-unit plant with 2 units on outage still cannot run below
**one unit's** 175 MW; it makes 175 MW or it is **off**. ERCOT coal availability
under the DAM water-fill sits well below 1.0 in most hours, so the applied floor
landed *below* the physical minimum exactly where the defect lives, and the arm
removed **none** of the impossible loadings (14,582 → 14,886 plant-hours).

The correction is availability-**CONDITIONAL**, evaluated on the **plant's**
available capacity and then allocated across its tranches in fill order using
each tranche's *available* capacity in that hour:

```
avail_cap[k,t] = availability[k,t] × pmax[k]                 # per tranche k of plant p
total[p,t]     = Σ_k avail_cap[k,t]

if total[p,t] ≥ min_config_mw[p]:
    floor[k,t] = clip(min_config_mw[p] − Σ_{j<k} avail_cap[j,t], 0, avail_cap[k,t])
else:
    floor[k,t] = 0            # the plant cannot reach its minimum configuration
```

`availability` is **exogenous data, not a decision variable**, so the conditional
is a data-side computation with **no integrality** — it stays inside the pure-LP
rule. It is what ERCOT-128 §1.3's exactness proof always described: that proof
was conditional on *at least one unit online*, and the scaled build silently
dropped the condition.

**No new `ScenarioConfig` field.** The same `ercot_coal_min_config_floor` flag,
the same `coal_min_config_ERCOT.csv` artifact, the same `MECH_COAL_MIN_CONFIG`
id, the same `D4_WINDOWS` (0,24) declaration. The default cache key therefore
does not move and **ERCOT-128 is a true A/B control on one expression**.

```
python scripts/replay_keeper.py results/calibration/ercot115_coal_floor_only \
  --set ercot_coal_min_config_floor=true \
  --out-dir results/calibration/ercot129_conditional \
  --years 2023 2024 2025
```

One invocation, years sequential (rule 12), full span in one bundle (rule 16),
holdout years untouched (rule 22).

## 1. Phase 1 ex-ante bound — run BEFORE this document, on the control's own committed dispatch

**Leg (a) — can the conditional form even reach the defect?** Classifying every
impossible coal plant-hour in the control (online but below `min_u MinLoad_u`) by
whether the plant's available capacity that hour clears `min_config_mw`:

| year | impossible plant-hours | **A: reachable** (conditional LIFTS) | B: `avail×pmax < min_config` (conditional RELEASES) |
|---|---|---|---|
| 2023 | 14,886 | **13,785 — 92.6 %** | 1,101 — 7.4 % |
| 2024 | 13,051 | **11,539 — 88.4 %** | 1,512 — 11.6 % |
| 2025 | 9,561 | **9,561 — 100.0 %** | 0 — 0.0 % |

**Leg (b) — the C1 risk.** Lift-in-place upper bound (no LP redistribution), plus
the energy released where the floor drops to zero:

| year | lift TWh | release TWh | net | control C1 | **projected C1** |
|---|---|---|---|---|---|
| 2023 | 0.889 | 0.053 | +0.836 | −0.955 | **−0.119** |
| 2024 | 0.881 | 0.186 | +0.695 | −0.102 | **+0.593** |
| 2025 | 0.427 | 0.000 | +0.427 | −1.678 | **−1.251** |

All three inside G2's ±2.0, and this is a **hard upper bound** — ERCOT-128
realised only ~40 % of its own ex-ante lift (0.30/0.34/0.41 TWh against
0.66/1.09/1.13), because the LP displaces other supply and re-shapes coal above
the floor.

**Both legs clear, so Phase 2 runs.** Had leg (a) come in small the fix would
have been inert and this lane would have stopped without a solve, as
ERCOT-124/125/127 and ERCOT-128 Phase 1 all did.

## 2. The gates — fixed now, scored as written

| gate | criterion | keeper | control (ercot128) | verdict rule |
|---|---|---|---|---|
| **G0** arming + bite | 3/3 solve logs `ARMED`; `run_config` carries the flag; non-zero D-2 `coal_min_config` row | no COAL row | 1.749 / 1.679 / 1.393 TWh | a silent arm FAILS |
| **G1** loading-vs-price | fleet-aggregate, `\|model − actual\| ≤ 0.05`, 21 bands, `ercot128_coal_unit_grain.py --arm-bundle` | 19/21 | 19/21 | **DO-NO-HARM: < 19/21 FAILS** |
| **G2** C1 coal level | within **2.0 TWh** of actual, every year | −1.08 / −0.29 / −1.93 | −0.96 / −0.10 / −1.68 | any year outside ±2.0 FAILS. Ex-ante projection −0.12 / +0.59 / −1.25 |
| **G3** D-1 coal | the **scorer's own** gate: `profile_r ≥ 0.8` **and** `cv_ratio ≥ 0.5`; and **no coal class-year may flip pass → fail** vs the keeper | 2023 `COAL_LIGNITE` FAIL, 5/6 pass | same 5/6 | a new pass→fail FAILS. *(Stated as the live gate deliberately: ERCOT-128's absolute-0.030 tolerance on a ratio spanning 0.294–1.612 was a mis-specification and is not repeated.)* |
| **G4** rubric + C8 | C1 16/16 · free 12/12; `coal_min_config` forced share < 30 % | — | 16/16 · 12/12; 2.9 / 2.9 / 2.3 % | over cap FAILS. Expected to RISE (the floor now bites); still expected well under 30 % |
| **G5** LOYO | per-year within 2023–2025 on the G1/G2/G7 verdicts | — | — | **2-of-3 is a FAIL** |
| **G6** DOF ledger | measured, `lineage_solves = 0` | — | — | unchanged parameter; a residual-identified value FAILS |
| **G7** ⭐ **structural** | online plant-hours below `min_u MinLoad_u` must fall **≥ 50 %** against the control, **every year** | 14,582 / 13,020 / 9,558 | 14,886 / 13,051 / 9,561 | **< 50 % reduction in any year FAILS.** This is the gate ERCOT-128 lacked as a gate, and it is the reason this lane exists |

**G7 is the win condition; G1 and G3 are do-no-harm bounds.** Per the owner's
rule-1 direction, improving G1/G3 is not required and their improvement is not
evidence for promotion. Passing G7 while holding the rest is.

## 3. What would make me recommend AGAINST, stated before seeing a number

* G7 below 50 % in any year — the fix does not bite and the lane is refuted for
  the second and last time;
* any absolute gate fails (G0, G2, G4, G5, G6);
* G1 below 19/21, or any coal class-year flipping D-1 pass → fail;
* per-plant p05 loading **overshooting** the real fleet's on a material plant —
  the floor would then sit above the true minimum online configuration, i.e. the
  artifact is wrong. Reported for every plant-year whatever it shows;
* the released category-B hours (plant cannot reach `min_config` at all, 7.4 /
  11.6 / 0.0 % of impossible hours) growing rather than shrinking: those need an
  **upper** bound (cap the plant off), which is a separate leg and is **not**
  built here. It is reported, not fixed.

## 4. Scope and standing constraints

`frontend/data/backcast/keepers/ERCOT.json` is **NOT** touched under any outcome
— a promotion recommendation is a recommendation. Holdout years 2022 / 2019 /
≤2021 / H1-2026 untouched (rule 22). One invocation, years sequential (rules 12,
16). No GitHub Actions workflow; the solve runs in-session.
`scripts/data/derive_eia860_coal_min_config.py` is **not re-run and not edited**
(rule 23) — the artifact is unchanged and is the control's, so the only
difference between the two bundles is the floor expression. ERCOT-116 is neither
armed nor promoted. The closed lanes stay closed, including the
availability-SCALED floor itself (ERCOT-128 §P3–P4), which appears here only as
the control.
