# ERCOT-155 — the evening mid-merit "dispersion" object is NOT an offer-slope or a fleet-composition defect: it is a COMMITMENT-STATE defect. ERCOT runs its online thermal fleet at 92–96 % of HSL with 0.9–2.8 GW of energy headroom and 17–23 GW cold; the model runs at 66–68 % with 15.3–17.5 GW of headroom, all dispatchable at fuel cost. The chartered offer-dispersion arm is REFUSED, and the successor is the energy-side analogue of the reserve cap the keeper already arms.

**Session 2026-08-03. Keeper: `2026-08-02-ercot150b-zonal-anchor` (NOT-YET; open
gates C3a 2023-only −32.6 %, C3b 2023-only 0.616, C3c, C7 2023-lignite cv-leg).
Phase 1 only — NO LP built, NO year solved, NO mechanism armed, NO flag added,
keeper UNCHANGED.** Probe
`scripts/probes/ercot155_dispersion_census.py`; committed record
`results/calibration/ercot155_dispersion_census.json`. Every input is already
committed: the ercot150b keeper's `meta.json` + hourly sidecars, the four
60-Day SCED extracts, `data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet`.

## 0. Verdict

**The chartered Phase-2 arm is REFUSED, and the charter's (c) question resolves
to a third answer neither of its branches anticipated.**

1. **ERCOT-154 §4's premise is CORRECTED.** "~25 GW of thermal headroom priced
   within 1.6 $/MWh per GW" took the gap between the ANNUAL MAXIMUM thermal
   dispatch (60.4–61.1 GW) and the evening MEAN (35.3–35.7 GW) as if it were
   headroom available in an evening hour. Measured on the keeper's own arrays,
   the evening thermal headroom is **17.49 / 15.51 / 15.34 GW** (2023/24/25),
   and the stack over it is **convex, not flat** — 1.1–1.2 $/MWh per GW for the
   first ~5 GW, 7.8–13.4 $/MWh per GW by 60–90 % of headroom, reaching only
   **$103–116** at the 90 % rung before a 38 MW West CT tail (HR 155.17
   MMBtu/MWh) jumps to $2,797.56. The empirical 1.557/1.616 $/MWh per GW is a
   correctly-measured LOCAL slope at the operating point, not a property of the
   whole stack.
2. **The instrument validates.** The P0 offer-census near-margin slope
   (1.2–1.9 $/MWh per GW over the first 1 GW) reproduces ERCOT-154's
   independently-measured P1 REALIZED matched-hour slope (1.557/1.616). The P1
   startup markup is therefore second-order for this object and `mc_base` is a
   faithful instrument — established by measurement, not assumed.
3. **The real market's near-margin stack is 2–6.5× steeper, on matched days.**
   Over the first 1 GW above the dispatch point — the widest band the SCED
   corpus actually covers (per-offset coverage 0.93/0.83 at +1 GW, 0.65/0.53 at
   +2 GW) — ERCOT's own conduct rises **+2.97 / +8.52** $/MWh per GW on control
   days and **+16.84 / +12.00** on event days, against the model's
   **+1.42 / +1.41 / +2.59 / +1.89** on the same calendar days.
4. **THE DECISIVE MEASUREMENT — it is not a pricing defect, it is a
   commitment-state defect.** In the evening ERCOT holds **159–224** thermal
   resources online at **92.0–96.2 % of HSL**, leaving **0.92–2.80 GW** of
   energy headroom, with **128–196** resources and **17.05–22.94 GW** of
   thermal HSL sitting OFFLINE and therefore absent from the 5-minute stack
   entirely. The model has **53.1–54.4 GW** of available thermal at **65.7–68.0 %**
   loading — **15.3–17.5 GW** of headroom, **5.5–19× the real market's**, every
   MW of it dispatchable from zero at its marginal cost in any hour, because the
   LP carries no integer commitment.
5. **The model gets the right energy from the right fleet by the wrong route.**
   Evening thermal dispatch is 35.70/36.09/36.09 GW against a real Base-Point
   sum of 34.33 GW (control) / 41.02 GW (event) — C1 16/16 and C2 PASS. Same
   MWh, same classes; a fleet 68 %-loaded across 53 GW instead of 93 %-loaded
   across 40 GW. That single difference is why the price never has to climb.

## 1. Why an offer/dispersion arm is refused rather than merely unpromising

The tempting Phase-2 move is to re-price the model's upper tranches until its
band reproduces ERCOT's +$3–17/GW. **That is barred, and not on fit grounds.**

The MW being re-priced are not the MW ERCOT prices there. ERCOT's steep first
GW is the top steps of units *already synchronised and already loaded to 92–96 %
of HSL*; the model's first GW is drawn from 15–17 GW of capacity that ERCOT
keeps **cold**. Assigning event-day conduct prices to capacity the real market
does not have online is a fitted proxy for a missing physical constraint — the
"right number through a mechanism that isn't real" that rule 1 `[R-STRUCT]`
forbids, with no forward analogue under rule 13 `[R-MEASURED]` and no
identification source under rule 20 `[R-DOF]`.

The across/within decomposition confirms the defect is not *inside* the offer
surface. On the comparable 1 GW band both sides are ACROSS-dominated, and the
model's across-term is 4–25× too small — but the absolute magnitudes are
$2.66–47.43 (SCED) against $0.71–2.18 (model), i.e. **tens of dollars, not the
hundreds the C3c tail needs**. There is no offer-side dispersion parameter that
reaches a $200+ tail from a stack whose 90 % rung is $103.

| 1 GW band, matched days | across $ | within $ | share of band MW > $100 |
|---|---|---|---|
| SCED 2024 control | 2.66 | 0.58 | 0.000 |
| MODEL 2024 control | 0.71 | 0.03 | 0.000 |
| SCED 2025 control | 10.49 | 1.77 | 0.000 |
| MODEL 2025 control | 1.11 | 0.05 | 0.000 |
| SCED 2024 **event** | 45.34 | 2.54 | **0.238** |
| MODEL 2024 event | 2.18 | 0.31 | **0.000** |
| SCED 2025 **event** | 47.43 | 4.91 | **0.533** |
| MODEL 2025 event | 1.90 | 0.38 | **0.000** |

On event evenings ERCOT prices 24–53 % of its first marginal GW above \$100.
The model prices **none of it** above \$75 in any of the four cells.

## 2. Composition is exonerated

The band's class occupancy is a plausible merit-order tail and stable across
years — CT_PEAKER 0.265–0.299, ST_GAS 0.271–0.289, CC_REGULAR 0.211–0.252,
CC_CHP ~0.09, COAL 0.071–0.111, CT_CHP ~0.025. The fleet is the same physical
fleet ERCOT dispatches (C1 16/16 all-class, 12/12 free-class), the offer LEVEL
program is closed and independently corroborated (capped at \$200 the model's
mean is within **−5.1/+0.5/−4.5 %** of the capped actual, ERCOT-144). Nothing in
the census supports "too many near-identical-cost units in the band" as the
cause: the units are the right units at the right costs, and there are simply
15 GW of them available that should not be.

## 3. This is the SAME defect the repo already fixed on the reserve side

`results/scarcity.py::ercot_rtolcap_supply_cap_mw` states it in its own words:

> The ERCOT co-opt's shared-headroom rows count every reserve-eligible thermal
> unit's *full installed* headroom as reserve supply — **including cold
> slow-start units a perfect-foresight LP leaves idle but still scores as
> "available"** — so modeled reserve never tightens into the ~8-12 GW band where
> ERCOT's ORDC adder actually fires.

That sentence is true of the ENERGY stack verbatim, and the energy stack is
uncapped. The keeper arms `ercot_reserve_supply_cap=True` on the measured
RTOLCAP series; nothing constrains energy to the online fleet. The measured
instrument is already committed, in the same file, for all three years:
`ercot_<year>_ordc_reserves_hourly.parquet` carries **`rtolhsl`** (online HSL,
evening mean 58.87/62.64/67.81 GW) and `rtolcap`/`rtoffcap`.

**Consequences, all previously-separate ERCOT residuals, all downstream of this
one gap:**
- **C3a-2023 (−32.6 %)** is ~entirely tail wedge: capped at \$200 the model is
  within −5.1 %, while hours >\$200 are **63 vs 181** and the >\$200 wedge is
  \$7.21 vs \$18.61 per MWh of annual mean.
- **The ECRS mechanism under-delivers although it is correctly armed and
  correctly dated.** `ercot_ecrs_conservative_deployment=True` models the
  pre-reform non-releasable ECRS as a rigid VOLL step from the measured
  ASPLANNP433 onset (2023 h3839 ≈ June 9–10, ECRS go-live June 10 2023) through
  the published 2024-08-01 operating-procedure reform
  (`ERCOT_ECRS_RELEASE_REFORM_HOUR = 5088`), and scarcity does collapse across
  the years as the reform says (reserve price >\$1 in 54/14/0 h; LMP >\$1000 in
  22/7/0 h). Withdrawing 1–3 GW of ECRS from a **15 GW cushion** simply cannot
  move a dual.
- **ERCOT-153's \$20–66/MWh evening-ramp premium has no former**, and
  **ERCOT-154's storage re-pricing could buy only \$1.38/\$3.05** — both are the
  same cushion measured through different instruments.

## 4. What this hands the lane

**Named successor (UNCHARTERED — needs its own charter and owner
authorization): an energy-side measured online-capability constraint, the
analogue of `ercot_reserve_supply_cap`.** It is a *structural* mechanism (a new
upper-bound row family in the LP), not a Phase-2 offer arm, and it is
deliberately NOT built here. Before it can be chartered:

- **Rule 19 `[R-ONE-MECH]` reconciliation is mandatory and non-trivial.** The
  availability lane (`ercot_thermal_dam_availability*`, the ERCOT-148/149 event
  caps) models **outages**; a commitment ceiling models **online state**. They
  are different quantities and must compose by an explicit precedence rule, not
  stack. The commitment BRIDGES (`ercot_gas_commitment_bridge`, keeper-armed)
  already own the *lower* bound from the P0 run pattern; the ceiling is their
  upper-bound counterpart and must be reconciled with them, not layered on.
- **Identification must come from ERCOT's own measured online state** — the
  committed `rtolhsl` series (all three years) and/or CAMPD unit-hour operation,
  never a value tuned to a price residual (rules 13/20/23).
- **The pure-LP architecture is a hard constraint** (CLAUDE.md forbids MIP), so
  the mechanism must be an availability-shaped bound, not integer commitment.
- **Data scope:** `rtolhsl` covers 2023–2025 on disk. The SCED corpus that
  validates it is **2024/2025-only** (no 2023 corpus — NP3-965 re-upload
  OWNER-DECLINED 2026-08-02) and is a 47-day sample split 36 event / 46 control
  day-files, so any derivation is sample-bounded and must report it.

**Do NOT re-open, from this session's evidence:**
- **An offer-side dispersion/slope parameter for the evening band** — refused
  here on §1. The measured across-resource spread on the comparable band is
  tens of dollars; the object needs hundreds, and the MW it would re-price are
  MW ERCOT keeps offline.
- **The "flat 25 GW at 1.6 \$/MWh per GW" framing** — corrected in §0.1. The
  stack is convex and the headroom is 15.3–17.5 GW; quoting the 25 GW figure
  forward would re-import the error.
- **Re-deriving the offer LEVEL program** (ERCOT-99/100/118/119/136–140/144/150)
  — closed, and independently corroborated here by the capped-at-\$200 result.

## 5. Governance

No mechanism tested in the LP sense, no flag added, no `ScenarioConfig` field
added, no solve, no registration (the ERCOT-142/143/145/147/152/154 no-LP
pattern). Holdouts untouched: 2023–2025 only, and the SCED corpus is 2024/2025
by construction. ERCOT-scoped (rule 25) — no other ISO's cell is touched.
Rule 28(b) duty discharged: new matrix row `energy_online_capability_cap`
(ERCOT `U`, the named successor) and the §5.1 queue re-pointed. The keeper
disposition is UNCHANGED and is surfaced to the owner, not self-decided.

### 5.1 Method notes (what a successor must not silently re-break)

- **Both sides are read at ABSOLUTE MW offsets above each interval's own
  realized dispatch point**, never at fractions of headroom: the model's
  headroom includes MW its co-optimization holds as AS, while SCED's HASL has
  already netted the AS award out. The thermal AS carve-out is small (HSL−HASL
  = 0.24–0.38 GW), but the headroom denominators differ by 5–19×, so a
  fractional band would compare unlike regions.
- **The SCED stack spans `[0, HASL]`,** including each resource's must-take
  `[0, LSL]` block at its own first curve step. Without it the stack starts at
  LSL while Base Point is measured from zero and every interval reads as having
  negative headroom — the bug that produced an empty first pass here.
- **Event and control day-files are never pooled.** Three of the four extracts
  are event-day samples; pooling would overstate ERCOT's dispersion by ~5× on
  the across-term.
- **Offsets past the top of a stack read NaN, never the last rung.** Clipping
  reports the 38 MW West CT tail at \$2,797.56 as though it were the band, which
  is what produced the spurious "110 \$/MWh per GW" first reading.
