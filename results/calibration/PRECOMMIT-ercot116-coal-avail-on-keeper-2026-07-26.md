# PRE-COMMIT ADJUDICATION — ERCOT-116 joint arm: measured coal DAM availability on the ercot115 keeper

**Written 2026-07-26, BEFORE any year of the arm was solved.** Rule 1: the criteria are
fixed here so the verdict cannot be reverse-engineered from the residual. The mechanical
scorer (`scripts/probes/ercot116_seasonal_shape.py`) was written and pushed in the same
commit, before any result existed.

## The question this arm answers

ERCOT-116's charter question: **what is the statistical coal-availability model silently
compensating for?** In the keeper, gas is pinned to the measured 60-Day DAM envelope and
coal is not (the standing rule-14 shape, ERCOT-114 `ff0109c`); the class that mis-shapes
seasonally is exactly the class whose availability is a statistical estimate. The direct
arming (`ercot_thermal_dam_availability_coal`, ERCOT-112 arm B) was refuted on annual
LEVEL (C1 16/16 → 12/16) — but nobody had decomposed arm B BY MONTH.

## The no-LP decomposition (run first, this session, before this doc)

All numbers from committed `hourly/` sidecars + measured data — no solve. Metrics:
**excess** = matched-price-band summer-minus-shoulder utilization lift, model minus
actual, mean over 8 fixed absolute price bands (`a2_matched_price_bands` headline, the
metric the charter's ~19 pp is stated in); **spread** = Jun–Sep mean monthly coal ratio
minus Feb–Apr mean.

| arm (code vintage) | config | excess 23/24/25 (pp) | spread 23/24/25 | annual ratio 23/24/25 |
|---|---|---|---|---|
| old keeper `ercot_netrev_margin` (old) | no floor, stat avail | 19.2 / 18.0 / 19.9 *(ERCOT-114)* | — | 1.028 / 1.029 / 0.988 |
| **keeper** `ercot115_coal_floor_only` (`b5449c0`) | floor, stat avail | **19.18 / 18.57 / 20.59** | **+0.435 / +0.591 / +0.333** | 0.952 / 0.973 / 0.951 |
| ERCOT-112 arm B (`3888d01`, old) | no floor, **meas avail** | **7.36 / 10.61 / 11.49** | +0.081 / +0.215 / +0.165 | 1.161 / 1.212 / 1.207 |
| ERCOT-112 arm T (`bcc4887`, old) | floor + **meas avail** | **10.61 / 13.05 / 13.58** | +0.247 / +0.403 / +0.235 | 1.053 / 1.121 / 1.151 |

The charter's decisive question is answered **before** the solve:

* **The measured envelope FIXES the seasonal shape.** Excess falls from ~19–21 pp to
  ~7–11 pp (arm B) and the fix survives the floor (~11–14 pp, arm T). Roughly **half the
  seasonal term is the statistical availability model's seasonal profile** (the measured
  live/rating fraction is 0.10–0.13 HIGHER in summer — real coal takes outages in
  spring/fall — and the statistical estimate misses that asymmetry).
* **The level break is uniform, not seasonal.** Arm B's gap vs the measured envelope is
  positive in EVERY price band of BOTH seasons of ALL years (+2.9 to +18.0 pp) — a
  LEVEL error of the kind the ercot115 floor (a uniform offer-level change) addresses.
* **The floor is roughly shape-neutral in the matched-band metric** (old keeper → keeper:
  19.2/18.0/19.9 → 19.2/18.6/20.6; arm B → arm T: +2–3 pp) while moving annual level
  −0.06 to −0.11. **The two effects are separable.**
* The remaining ~10–13 pp of excess is **within-envelope over-dispatch at matched
  price** — not availability, and not any uniform offer-level lever (ERCOT-115). That is
  the successor question whatever this arm does.

## Why a fresh solve (arm T is not this arm)

Arm T is config-identical to this arm but was solved on `bcc4887` (2026-07-25) — BEFORE
the ERCOT-114 gas-envelope direction fix (`ff0109c`) that is in the keeper's `b5449c0`.
The joint config has never been solved on the current base, where it is keeper + ONE
delta. Single arm, full span, one invocation, years sequential (rules 12 + 16):

```
python scripts/replay_keeper.py results/calibration/ercot115_coal_floor_only \
  --set ercot_thermal_dam_availability_coal=true \
  --out-dir results/calibration/ercot116_coal_avail_on_keeper \
  --years 2023 2024 2025 \
  --note "ERCOT-116: measured coal DAM availability on the ercot115 keeper"
```

## Criteria (fixed now; evaluated by `ercot116_seasonal_shape.py`, thresholds baked there)

**G0 — ARMING + BITE.** The solve log must show BOTH lines in all three years:
`ERCOT coal econ marginal-HR floor (1): COAL_PRB.econ_low 0.400 -> 0.886` AND
`ERCOT measured thermal DAM availability (<year>): COAL plant-grain redistribution`.
`run_config.json['scenario_config']` must carry `coal_econ_marginal_hr_bound=true` AND
`ercot_thermal_dam_availability_coal=true`. Bite: annual coal TWh differs from the
keeper's by > 0.5 TWh in at least one year. Armed-but-inert ⇒ the probe is **void**.

**G1 (PRIMARY) — matched-band excess falls materially in EVERY year.** Excess (keeper:
19.18 / 18.57 / 20.59 pp) must fall by **≥ 5.0 pp in each of the three years**.
Declared with knowledge: arm T's old-code deltas were −8.6 / −5.5 / −7.0 pp, so 5.0 pp
is a materiality line the mechanism has already cleared on the old base — this gate
tests that the fix SURVIVES the corrected gas envelope, not that it exists.

**G2 — monthly-ratio spread narrows in EVERY year.** Spread (keeper: +0.435 / +0.591 /
+0.333) must narrow in all three years, with mean narrowing ≥ 0.10 (arm T's old-code
narrowings vs keeper: 0.19 / 0.19 / 0.10).

**G3 — scarcity not degraded.** Same numerics as ERCOT-112 P2b / ERCOT-115 P2, not
re-invented: C3a (load-weighted price + `ordc_adder` + `rtordpa_overlay`) within
**2.0 pp** of the keeper every year; C3c (settled hours ≥ $200/MWh) within **5 hours**
every year.

**G4 — leave-one-year-out (rule 24).** G1 and G2 are evaluated per-year; **all three**
years must pass. A 2-of-3 pass is a **FAIL** for the shape claim.

## Predictions registered now (so the verdict is auditable)

Excess ~10–14 pp (halved, not closed); spread ~+0.20 to +0.42; annual ratio rises from
0.951–0.973 to roughly **1.00–1.12** (the availability overlay's known level uplift,
partially absorbed by the floor). C1 fuel-mix MAY regress on the coal class — that is
the expected, reported-not-gated outcome.

## Decision rule (fixed now)

* **G0 fails** → report inert/mis-armed; probe void; no keeper change.
* **G1–G4 pass** (expected) → **FINDING:** the ~19 pp seasonal term is at least half the
  statistical availability model's seasonal-profile error; the estimate is compensating
  for a **LEVEL error elsewhere** (within-envelope over-dispatch at matched price — the
  model's coal SRMC top ~$28 vs the real fleet's ~$21 top submitted DAM coal offer, the
  F923 delivered-price question of ERCOT-112 §6, is the named lead). The arm is a
  **PROBE, registered as such** (rule 15). **No promotion is executed in this session.**
  Only if C1 fuel-mix ALSO holds (16/16, free 12/12, dispatch_corr PASS) does this
  become a promotion RECOMMENDATION — and then the session **stops and asks the owner**
  (ERCOT-115 lesson; recommend, never execute).
* **G1 or G2 fails** → the availability shape-fix does not survive the corrected gas
  envelope; the seasonal term is NOT primarily the availability estimate; report, no
  keeper change, back to decomposition.

## Declared in advance: what would NOT count

* Price MAE, in either direction (rule 1). Only the pre-committed gates decide.
* The **annual coal LEVEL regression is expected and is NOT grounds to reject** the
  mechanism (rules 1/13/14): a measured input that worsens the fit is a discovered bug
  elsewhere, and the availability estimate has now been shown to be compensating for it.
  The gate failure mode this arm probes is SHAPE, per the charter's explicit
  instruction: "Gate on SEASONAL SHAPE … NOT on annual level."
* The ≥$300 scarcity set: ERCOT-111 measured coal at 99.5 % of its measured live
  envelope there; C3c stability is a confirmed prediction, not a null result.

## What is already known at write time

Known: everything in the decomposition table above (all four existing bundles' monthly
and matched-band numbers, on their respective code vintages); the ERCOT-112 published
arm results (B: C1 12/16, dispatch_corr FAIL · T: C1 15/16, dispatch_corr PASS); the
keeper's grade (C1 16/16, fails 3); the arming-line grep patterns.

**Not known:** any result of the joint config on the current (`ff0109c`-corrected) base.
No year of `ercot116_coal_avail_on_keeper` had been solved when this document was
written and pushed.
