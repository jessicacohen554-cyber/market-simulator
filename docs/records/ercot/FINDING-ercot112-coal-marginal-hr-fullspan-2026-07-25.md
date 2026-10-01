# FINDING — ERCOT-112: the coal econ marginal-HR floor holds across the full span (4/4 pre-committed criteria PASS)

**Date** 2026-07-25 · **ISO** ERCOT · **Years** 2023–2025 (one invocation each, years sequential) ·
**Gate** `ScenarioConfig.coal_econ_marginal_hr_bound` (default **off**; keeper unchanged) ·
**Pre-commit** `results/calibration/PRECOMMIT-ercot112-coal-marginal-hr-fullspan-2026-07-25.md`
(written and pushed **before** any 2024/2025 result was read) ·
**Scorer** `scripts/probes/ercot112_score_coal_arms.py`

| arm | run id | delta vs keeper `ercot_netrev_margin` |
|---|---|---|
| **B** baseline | `2026-07-25-ercot112-coal-dam-availability` | `ercot_thermal_dam_availability_coal` |
| **T** treatment | `2026-07-25-ercot112-coal-marginal-hr` | + `coal_econ_marginal_hr_bound` |

Arm B exists because ERCOT-110 only ever solved 2023; without it a T-vs-keeper comparison would
confound two deltas. Both arms are full-span, so the comparison is like-for-like in every year.

## 1. The trap, cleared

An availability overlay keyed on `COAL_PRB` matches **no generator** — the ERCOT LP assigns the
whole coal fleet `plant_group = "COAL"`, and the PRB/lignite split exists only at reporting time —
so it can run silently inert through a full solve with no error. Both arming lines were verified in
the solve log **for all three years** before anything was scored:

```
INFO: ERCOT coal econ marginal-HR floor (1): COAL_PRB.econ_low 0.400 -> 0.886
INFO: ERCOT measured thermal DAM availability (20XX): COAL plant-grain redistribution
      — 10 crosswalked plant(s), 0 unmapped tranche(s)
```

Arm B carries the redistribution line only, and no floor line — exactly as designed.

## 2. Result

| year | arm | coal TWh | actual | **ratio** | Jun–Sep | gas TWh | actual | C3a | C3c |
|---|---|---|---|---|---|---|---|---|---|
| 2023 | baseline | 72.32 | 62.29 | 1.161 | 1.207 | 189.46 | 201.46 | −25.2 % | 50/181 |
| 2023 | **floor** | 65.57 | 62.29 | **1.053** | 1.169 | 196.20 | 201.46 | −24.3 % | 50/181 |
| 2024 | baseline | 71.27 | 58.77 | 1.213 | 1.333 | 189.58 | 203.68 | −7.1 % | 7/53 |
| 2024 | **floor** | 65.96 | 58.77 | **1.122** | 1.292 | 194.88 | 203.68 | −5.8 % | 7/53 |
| 2025 | baseline | 76.48 | 63.37 | 1.207 | 1.284 | 184.08 | 200.21 | −5.2 % | 1/31 |
| 2025 | **floor** | 72.93 | 63.37 | **1.151** | 1.256 | 187.60 | 200.21 | −4.2 % | 1/31 |

2023 replicates the published ERCOT-111 single-year probe **exactly** (coal 65.57, ratio 1.053,
JAS 1.169, gas 196.20, C3a −24.3 %, C3c 50/181), confirming the full-span replay reproduces it.

## 3. Verdict against the pre-committed criteria

| criterion | result |
|---|---|
| **P1** direction — 2024 *and* 2025 annual coal ratio move toward 1.0 vs the same-config baseline | **PASS** (all three years, not just the two required) |
| **P2a** no over-fire — `ratio >= 0.90` every year | **PASS** (min 1.053; never undershoots) |
| **P2b** scarcity not degraded — C3a within 2 pp, C3c within 5 h | **PASS** (C3a *improves* every year; C3c identical every year) |
| **P3** leave-one-year-out (rule 24) — ≥2/3 improve, none degrade > 0.05 | **PASS** (3/3 improve; zero degradations) |

`|ratio − 1|`: 2023 0.161 → 0.053, 2024 0.213 → 0.122, 2025 0.207 → 0.151. Same sign, same
mechanism, every year. This is not a single-year-carried result, which is what rule 24 exists to
catch — in-sample gain with held-out degradation would be overfitting, and there is none here.

Coal moves toward actual in every year **and the displaced energy lands in gas**, which also moves
toward actual in every year (189.46→196.20, 189.58→194.88, 184.08→187.60 against actuals of 201.46,
203.68, 200.21). The floor is not shuffling error into slack or dump.

## 4. What this does NOT close

* **The residual is reduced, not closed.** Coal is still +5.3 % / +12.2 % / +15.1 % over actual, and
  the summer leg is barely touched — Jun–Sep stays at 1.169 / 1.292 / 1.256. The monthly tables show
  the same signature in all three years: shoulder months at or below 1.0, **June–September at
  1.16–1.32**. Whatever drives the summer over-run is a different mechanism and remains open.
* **Scarcity hours are untouched by construction.** ERCOT-111 measured the arms byte-identical in
  140 of 144 actual ≥$300 hours: at scarcity the model already runs coal at 99.5 % of its measured
  live envelope, so no offer-level change can move it. The floor bites where coal is **marginal**
  ($10–25/MWh, most hours) and is inert where coal is **capped**. C3c being identical in all three
  years is that prediction confirmed, not a null result.
* **2024/2025 have far less scarcity than 2023** (actual ≥$200 RT hours: 181 → 53 → 31), so the C3a
  improvement in those years is a mid-merit-order effect, not a tail effect.

## 5. Status

**PROBE. Not promoted.** The keeper remains `2026-07-23-ercot100-netrev-margin-keeper` and
`coal_econ_marginal_hr_bound` stays **default off** until the owner promotes it. What this session
establishes is the rule-24 promotion precondition: the mechanism is a measured rule-13 input
(the ISO's own CAMPD marginal-HR p50, replacing a fitted 0.400 that had no measurement behind it),
it fires where intended, and it improves every year in the training window without degrading the
scarcity criteria.

Per rules 1 and 14 the mechanism stays in regardless — a measured input is not reverted because a
residual moved. This gate decides only readiness for promotion, not legitimacy.

## 6. Open, not touched here

* The model's full-passthrough coal SRMC tops out near $28/MWh while the real fleet's top submitted
  DAM coal offer is ~$21 — an F923 delivered-fuel-price question, its own charter with receipts.
* The **summer** coal over-run (Jun–Sep 1.17–1.29 in all three years) is the live successor lane.
* `coal_econ_marginal_hr_bound` is ISO-generic and reads each ISO's own artifact (PJM 0.803/0.809,
  MISO 0.838/0.838, NEISO 0.933/0.631; CAISO/NYISO have no COAL row and no-op). Untested there;
  belongs to those lanes.
