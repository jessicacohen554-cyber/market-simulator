# FINDING — ercot-167: the measured storage AS SOC reservation, built, probed on 2023, A/B-tested full-span — arm REJECTED-AS-ARMED on its own pre-registered gates, with a cited reopen condition

**Charter:** mechanism-testing-matrix §5.1 **item 10** (owner-chartered at ercot-166 — the
`FINDING-ercot162` §2 named successor: "the AS/energy split of storage capability at scarcity", a
QUANTITY object). **Owner execution directive** (2026-08-05): run all 3 years, but 2023's distinct
scarcity-pricing design warrants a separate 2023 test before the full sequential span. Gates were
pre-registered in `docs/PRECOMMIT-ercot167-storage-as-soc-reserve-2026-08-05.md` BEFORE any solve;
two feasibility amendments were recorded there mid-probe (below), neither touching a gate.

**Mechanism** (`ercot_storage_as_soc_reserve`, default off, zero fitted scalars): floor each ERCOT
battery unit's SOC at the measured AS award × the published per-product SOC duration
(RegUp/RRS 1 h, ECRS 2 h, Non-Spin 4 h — `ERCOT_AS_PRODUCT_DURATION_H`, Nodal Protocols §3.17.3),
per-product shares measured from the 60-Day corpus
(`scripts/data/derive_ercot_storage_as_products.py`; reconstruction reproduces the committed total
EXACTLY for 2023/2024), normalized to the SAME committed award total `storage_as_commitment` docks
from the power cap — whose own docstring names the gap this closes ("this reserves *power*, not
state of charge — the first-order constraint that binds in the scarcity hours where the LP
over-discharges").

## 1. Probe history (2023-only, throwaway per rule 16 — never registered)

- **v1: LP-INFEASIBLE.** The armed `ercot_storage_as_deployment` force-discharges the award
  draw-down at the ramp while midday charge power is award-docked to ~0.3 GW; a floor tracking the
  award LEVEL never releases the energy the forced discharge spends. Fix (amendment 1): the floor
  nets the **intra-day cumulative deployment** (deployed AS energy leaves the tank; its backing is
  spent) — same measured series both sides.
- **v2: STILL INFEASIBLE.** Localized exactly via an LP-bounds dump at the raise site + a per-unit
  feasibility LP on the captured arrays: the **daily-pin coupling** — `storage_daily_cycle_hours`
  pins every day-start SOC to ONE shared S0, and the West unit's floor at high-award midnights
  (889 MWh) exceeded its energy cap at capability-dip midnights elsewhere (546 MWh; the Oct-2023
  capability-hole boundary; max feasible uniform floor scale 0.997). Fix (amendment 2):
  `_pin_reachability_clip` — the floor is bounded by the unit's max-reachable SOC path under the
  model's own scaffolding (S0 capped at the tightest pin-hour energy cap; within-day forward pass
  at docked charge power net of forced deployment; backward return-to-S0 pass). Measured arrays
  only; verified on the dumped failing bounds — removes **0.16 %** of floor MWh, all five units
  feasible at η=√0.85.
- **v3: SOLVED — all 2023 gates GREEN.** Discharge in the 61 actual >$1000 hours 666 → **520 MW**
  (measured actual 423 — 60 % of the physical gap closed, no overshoot); spurious tail 4→3; shed
  4→4; tail 58→61 (+3 real); C3a −30.3 → −29.9 %.

## 2. Full-span A/B (control `ercot167_control_A`, arm `ercot167_socreserve_B`)

| gate | 2023 | 2024 | 2025 |
|---|---|---|---|
| G1 target (2023 only): dis in act>$1000 h | **666→520 MW (act 423) PASS** | — | — |
| G4 C3a A→B | −30.3→−29.9 % (n/a-2023) | +9.0→**+10.4 % FAIL** (band ±1.0 pp) | −1.5→−0.8 % PASS |
| G4 C3b NRMSE A→B | 0.621→0.613 | 0.227→0.238 PASS | 0.073→0.068 PASS |
| G3 zero-spurious | 4→3 PASS | 7→7 PASS | 0→**1 KILL** |
| G5 shed hours | 4→4 PASS | 2→2 PASS | 0→0 PASS |
| G2 930 NG:BAT ratio (arm) | n/a (no 2023 series) | 0.65 (15 % coverage, report) | **0.72 PASS** (≥0.70) |
| C3c report (tail>200) | 58→61 / act 181 | 20→25 / act 53 | 0→3 / act 31 |
| evening 17–20h lw gap | −49.5→−49.2 | −3.7→−1.6 | −13.8→−12.3 |
| annual discharge TWh | 0.83→0.67 | 2.14→1.76 | 4.48→3.93 |

2025 evening net-discharge shape (arm vs EIA-930, HOD 17/18/19/20): 1,227/3,033/3,374/1,569 vs
actual 1,818/2,995/2,634/1,283 — the control's 18h/19h over-discharge (+462/+1,268) drops to
+38/+740; 17h swings under.

## 3. Verdict: REJECTED-AS-ARMED (two pre-registered kills fired; precommit: "kill gates bind, no post-hoc softening")

Drilldown on the two trips, recorded for the reopen condition, not to relitigate them:

- **G4-2024 (+1.4 pp)** concentrates on the KNOWN maintenance-season fabricated-spike days
  `FINDING-ercot166` §5 already flagged: the largest B−A day-lifts are Nov 9 (+$19.7/h-day),
  **Apr 27 (+$19.1)**, **May 7 (+$8.7)**, Apr 15, Aug 19 — on an April already +72 % over in the
  CONTROL (43 vs actual 25 $/MWh). The arm amplifies a pre-existing over-tightness defect; it does
  not create one.
- **G3-2025 (one hour)** is 2025-10-21 19:00 — model $235 vs actual $192 (a $43 graze at the $200
  threshold) — whose two NEIGHBOR hours (17:00/18:00, actual $214/$210) are newly-captured REAL
  tail hours the control missed at $96. One real October evening event, one hour running hot.

**Reopen condition (cited, rule-1-compatible):** re-gate the IDENTICAL arm — no parameter exists
to change — after the 2024 maintenance-season availability defect (handoff H4 item 4 phase-0 →
its fix) lands; both fired kills localize to that separate defect plus a single threshold graze
adjacent to newly-captured real hours. The mechanism itself is real market design (protocol SOC
backing), measured, zero-DOF, and hits its chartered quantity object dead-on in the year it was
chartered for; under CLAUDE.md rule 1 a structurally-correct mechanism that worsens a residual
signals the OTHER miscalibration, and the owner's standing promotion standard ("if structural
integrity improves but gates regress that may still be a keeper") makes promotion an available
owner decision on this record — this session executes its own precommit verdict and does not
self-promote.

## 4. Registration & bookkeeping

Both runs registered (rule 15): control `2026-08-05-ercot167-control` (fresh same-HEAD replay;
also the measurement of regenerated-input drift vs the committed keeper — the GTC clean partition
was regenerated in-container from the committed raw archives before any full-span solve) and arm
`2026-08-05-ercot167-socreserve` (REJECTED-AS-ARMED). Matrix §5.1 item 10 stamped tested-with-
verdict + reopen condition; `ercot_storage_as_soc_reserve` def registration carries the citation.
The C3c model-class ledger entries (rubric v3.0) are UNAFFECTED — the arm's tail movement
(58→61 / 20→25 / 0→3 vs [0.5×] bands 91/27/16) does not approach a PASS, so the entries stay live.
