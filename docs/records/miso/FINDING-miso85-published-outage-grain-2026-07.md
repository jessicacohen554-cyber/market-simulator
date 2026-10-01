# FINDING (miso-85, 2026-07-24) — MISO's published outage record is fuel-blind, and that grain (not its level) is what breaks the swap

**Context.** `2026-07-24-miso-85-dam-outage` (bundle
`results/calibration/miso_dam_outage_margin`) replaced the CAMPD unit-level
outage derate with MISO's own published Multiday Operating Margin OUTAGE record
on top of the net-revenue gas-offer margin, per owner instruction. It is the
MISO keeper; determination **NOT-YET**.

## 1. The measured level agrees; the measured *attribution* does not

Two independent measured availability records, on the same fleet:

| class (model GW) | CAMPD per-unit measured unavailability 2023 / 2024 / 2025 |
|---|---|
| COAL (44.4) | 0.332 / 0.325 / 0.264 |
| ST_GAS (11.6) | 0.589 / 0.529 / 0.508 |
| CC_REGULAR (28.3) | 0.200 / 0.210 / 0.251 |
| CC_CHP (7.0) | 0.073 / 0.093 / 0.075 |
| CT_PEAKER (22.4), CT_CHP (2.6) | 0.000 — outside the instrument's coverage |
| **MISO published envelope (uniform)** | **0.184 / 0.205 / 0.237** |

Fleet-average, the two records bracket each other (CAMPD 0.236 vs published
unplanned 0.184 in 2023), and the published record's seasonality is exactly what
the physics predicts (`Derated` peaks July–August = ambient capability derate;
`Planned` peaks at 36.4 GW in April = shoulder maintenance). **The level and the
timing are sound.** What the public report cannot supply is *which units* were
out — it publishes region × cause only.

## 2. What the uniform attribution does to the dispatch

Δ vs the `miso-81` keeper, 2023 (TWh): COAL_PRB **+27.2**, COAL_BIT +3.0,
ST_GAS +3.2, CC_REGULAR **−14.4**, CC_CHP −5.7, CT_PEAKER −6.9, CT_CHP −2.3,
imports −7.6. Against actuals that is C1 COAL_PRB **+28.3 TWh** / CC_REGULAR
**−22.7 TWh** (2023) and +21.1 / −14.8 (2024).

Mechanism, in two moves:

1. **Coal is under-derated.** MISO's coal fleet is old and carries ~0.26–0.33
   unavailability against a 0.18–0.24 fleet average, so a uniform rate hands
   back ~5 GW of coal that was actually out. As the cheapest steel in MISO it
   displaces combined-cycle gas immediately.
2. **Peakers are over-derated.** The uniform rate removes ~4–5 GW from a 22.4 GW
   peaking fleet that the per-unit record does not say was out (CTs are outside
   CAMPD's coverage by construction — a peaker's economic idleness is
   indistinguishable from an outage in CEMS). That is what manufactures the 2025
   tail: C3a **+43.5 %**, model **138 h > $200** vs **38 h** actual.

Both are consequences of the record's grain, not of its accuracy.

## 3. Why the cause set is Derated + Forced + Unplanned

Settled on physical feasibility, never a residual
(`scripts/probes/_miso85_outage_composition.py`): summing all four buckets leaves
LESS available thermal capacity than MISO's own metered coal+gas output on
**12 / 15 / 61 days** of 2023 / 2024 / 2025 (worst +12.7 GW; July-2025 mean
headroom 0.3 GW on a 118 GW fleet, before reserves). `Planned` is both the
model's own layer (statistical POF / CAMPD windows / nuclear overlay) and where
the record's non-thermal scheduled work sits. Same call the sibling PJM
instrument made independently (`PJM_OUTAGE_DEFAULT_TYPES`).

## 4. Both named alternatives are closed at this grain

* **Residual composition** (published envelope over what the per-unit windows
  already account for) is **inert**: CAMPD already accounts for 27.9 GW mean
  offline in 2023 vs the record's 21.8 GW unplanned total → residual zero.
* **All-cause residual** is **infeasible** (§3).

## 5. The open lever — fuel attribution, not a parameter

The admissible next mechanism is a **cross-fuel split of the published total**:
MISO's record sets the fleet total (measured, forward-reproducible), and a
measured attribution key — e.g. the per-class outage shares the CAMPD record
itself measures, or EIA-860/GADS class outage rates — distributes it. That keeps
both measured inputs in their competent domain: the ISO's own bookkeeping for
*how much*, the unit-resolved record for *where*. It is a new mechanism needing
its own charter (and a leave-one-year-out score before promotion), not a knob on
this one. Nothing here was tuned to close the residual (rules 1/10), and the
CAMPD path was not reinstated to recover the fit (rule 11).
