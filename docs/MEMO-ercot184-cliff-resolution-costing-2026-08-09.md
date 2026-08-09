# MEMO — ercot-184: costing the (c2) cliff-resolving offer-curve refinement

**Session ercot-184, 2026-08-09, opened at HEAD `51d4e98e`. COSTING MEMO ONLY —
NO BUILD, NO `ScenarioConfig` FIELD, NO DERIVE, NO LP SOLVE, NO REGISTERED RUN,
NO MATRIX CELL.** The ERCOT keeper `2026-08-09-run181-position-tail` is
untouched. ERCOT only (rule 25). Every year touched is inside {2023, 2024, 2025}
(rule 22 — ERCOT holds no `complete` and no `final` marker).

**Authorization:** owner sitting 2026-08-09, cards **D1(c) + D5**, SIGNED
(`docs/DECISION-CARD-ercot182-c3a2023-reachability-2026-08-09.md` §5 + §10). D1
REFUSED the C3a ledger carve-out and authorized the model-class lane to fix the
2023 object on the merits — *"I want to actually fix the 2023 pricing"* — and D5
scopes its first step to a costing memo with no build authorization. (c1)
sub-hourly is refused on scale and is not revisited here.

---

## 0. THE LOAD-BEARING QUESTION, AND THE STANDARD OF SUCCESS

> **Can a resolution change MOVE THE LP'S CLEARING POSITION up the curve, or
> does it only price the top of the curve more accurately?**

Item 23 (the ercot-181 position-tail) already proved the second **inert**: it
added exactly the right measured cliff conduct above p90 and moved C3a-2023 by
**+$0.0004/MWh**, because the LP clears at q_mod ≈ 0.912 while the cliff lives
at q_act ≈ 0.9976. If (c2) cannot move the clearing position, it is the same
failure in a more expensive form, and **this memo must say so.**

**A memo that concludes UNREACHABLE is a full success.** It is not a failed
lane; it is the costing doing its job before a build is authorized.

---

## 1. THE OBJECT — what (c2) actually proposes to change

`src/market_sim/data/offer_curves.py::_econ_curve_steps` slices each plant's
economic ramp into `offer_curve_smoothing_n = 6` **equal-width MW blocks**:

```python
slice_cap = curve_cap / n              # EQUAL WIDTH — the object
for k in range(n):
    t = (k + 0.5) / n                  # midpoint rule on the position axis
    f = 2.0 * mid * t if t <= 0.5 else mid + (1.0 - mid) * (2.0 * t - 1.0)
    mult = lo_mult + (pk_mult - lo_mult) * f
    steps.append((f"econc{k:02d}", slice_cap, base_hr * mult, 1.0, 0, 0, 0.0))
```

So the finest within-plant position the model can express is **1/6 of the econ
ramp**, and each slice is priced at its own **midpoint**. Reality's marginal
price forms inside the top **0.24 %** of the marginal resource's own submitted
curve (q_act p50 = 0.9976, ercot-180). (c2) = replace equal-width slicing with
**non-uniform slicing that refines the TOP of each curve**, preserving total
curve MW.

**The ERCOT keeper's actual shape parameters** (read from
`results/calibration/ercot181_positiontail_B/meta.json`): `offer_curve_smoothing_n
= 6` (ScenarioConfig default), `offer_curve_smoothing_mid = 0.35`. The `mid`
form is the two-segment piecewise-linear ramp `f(0)=0, f(0.5)=0.35, f(1)=1`, so
the top half of every econ ramp already rises **1.857×** faster than the bottom
half. **The price axis of the ramp is therefore already a tunable shape control;
what (c2) adds is refinement of the WIDTH axis.** That distinction governs the
whole costing and is picked up again in §5.

**The second, larger channel.** The keeper arms the measured offer surfaces
(`ercot_offer_surface_conditional = True`, `..._cleared_share = True`, plus the
item-23 `..._position_tail`). The wall and fast-start-pool markups are read at
each row's **within-plant cumulative-capacity midpoint**
(`mids = (cum - 0.5 * caps) / total`, then
`rel = (share_g - boundary) / (1 - boundary)`, then
`np.interp(rel, LADDER_Q, ladder)`). **Re-slicing the econ ramp therefore moves
every slice's `rel`, hence its markup** — and that ladder spans 1× delivered gas
to the HCAP wall (2023 top bin: CC 202× at p90 rising to 2659.6× at x = 1.0).
The heat-rate ramp is worth single-digit $/MWh; the ladder is worth thousands.
**Any honest costing of (c2) must measure the ladder channel, not the heat-rate
channel.**

---

## 2. G-SHED — THE EX-ANTE PRIMARY FALSIFIER

**Written and committed BEFORE any reach measurement was run**, at HEAD
`51d4e98e`, per card §5 item 2 and D5. Nothing below was adjusted after seeing a
number.

### 2.1 Why this is the primary falsifier and not a protective afterthought

The ercot-48/49 **manufactured-shortage signature** has killed this object
**twice**:

* **ercot-48/49** (2026-07-09): rejected with cause by the owner —
  *"it manufactured the tail through physical shortage … right-number-wrong-mechanism."*
* **ercot-178, item 21** (2026-08-08): the continuous-grain arm posted the
  largest single-mechanism 2023 move on the ERCOT record, C3a-2023 −32.4 % →
  −19.7 % (**+$8.18/MWh**). On decomposition, **67.5 % of that gain
  (+$5.53/MWh) was ten NEW VOLL shed hours**, and only **+$2.62/MWh was genuine
  offer formation**. The arm overshot the actual by > 1.5× in 7 of the 10
  (2023-08-26 18:00: actual $570 → arm $5,000). Reality had **4 hours ≥ $4,500
  in all of 2023**; the arm posted 14 shed hours at ~$5,000.

**(c2) is MORE shed-exposed than either, not less, and the exposure is
structural.** The composition clamps a repriced target at
`ercot_offer_surface_price_cap_frac × VOLL = 0.95 × $5,000 = $4,750`. A
top-refined slicing deliberately pushes the topmost sliver of every plant's econ
ramp toward `rel → 1`, i.e. toward the HCAP end of the ladder — **which is
precisely the operation that moves MW from below the clamp to above it.** Any
hour whose residual demand can no longer clear below $4,750 sheds at VOLL. The
mechanism by which measured conduct becomes false shortage is the same one
ercot-178 §7a already named.

### 2.2 The gates, stated verbatim and in advance

**G-SHED (PRIMARY, build-free form — this memo's own bar).** Because no LP is
solved here, shed is measured as **exposure**, not as an outcome:

* **G-SHED-A — clamp displacement.** For every object hour, compute
  `ΔMW_above_clamp` = the MW that the candidate refinement moves from a composed
  bid ≤ $4,750 to a composed bid > $4,750, holding total curve MW fixed. Report
  its distribution over the object hours at full magnitude.
* **G-SHED-B — headroom test.** An hour is **SHED-EXPOSED** when
  `ΔMW_above_clamp` exceeds that hour's own sub-clamp headroom (the coarse
  stack's MW available at or below $4,750 in excess of the quantity it must
  serve). Report the count of shed-exposed object hours per candidate.
* **VERDICT RULE:** any reach this memo reports must be stated **net of
  shed-exposed hours**, decomposed the ercot-178 §7 P-3 way (gain in hours that
  clear without shed vs. gain in hours pushed into shortage). **A candidate whose
  reach is dominated by shed-exposed hours is reported REFUTED, not as a build
  candidate — whatever its headline number.** Rule 1 `[R-STRUCT]` bites directly:
  never reach the right number through a mechanism that isn't real.
* **CARRY-FORWARD:** should a build ever be authorized, `shed_hours must not
  rise in ANY year` is a PRIMARY kill gate, not an inherited protective clause —
  ercot-178 §7a's own wording, adopted here in advance.

**G-REACH (the build bar, fixed ex ante).** The measurement below computes an
**upper bound over the entire family** of MW-preserving re-slicings (§4.2). A
build is chartered only if that ceiling, load-weighted over 2023 and **net of
shed-exposed hours**, exceeds **+$5.00/MWh** — about 35 % of the +$14.44/MWh bar
C3a-2023 needs. Rationale, fixed now so it cannot be moved later:

1. the whole conditioning family's *measured* offer-formation budget is
   **~$2.6/MWh** (ercot-178 §7a), and a build that re-opens P0 (§3) must clear
   meaningfully more than a family already rejected at that budget;
2. anything below roughly a third of the bar cannot close C3a-2023 even stacked
   with every other live lane, so it would buy a P0 re-open for a residual that
   still fails;
3. because the measured quantity is a **ceiling over all slicings**, failing it
   closes (c2) definitively rather than merely rejecting one parameterization.

**G-BIT (scope).** Any future build must leave 2024/2025 byte-identical or
prove no degradation; the owner's standing instruction is *under 10 % without
disturbing 2024/2025*.

### 2.3 Predictions, registered before measuring

* **P-1.** The model's marginal rows in the object hours sit at a within-plant
  position **well below** the region a top-refinement touches (ercot-181 §4
  measured them reading the **p50–p70** region of the ladders, control prices
  $100–360 ≈ multipliers 40–140). If so, top-refinement re-prices only
  **supramarginal** rows — item 23's exact failure mode, at a P0 cost item 23
  did not have to pay.
* **P-2.** The invariant-quantity ceiling (§4.2) is bounded by the **within-step
  ladder spread at the model's own clearing position**, and lands **far below**
  $14.44/MWh.
* **P-3.** *Uniform* refinement — which does reach the marginal row — has a
  near-zero mean effect, because midpoint pricing is unbiased to first order on
  a locally-linear ladder; whatever survives is the second-order **Jensen
  (convexity)** term only, positive but small.
* **P-4.** The clearing **position** is a quantity fact set by demand and total
  capacity. **No MW-preserving re-slicing can move it.** If P-4 holds, the
  answer to §0's load-bearing question is *"it only prices the position more
  accurately"*, and the lane closes.

**Adjudication of all four is reported at full magnitude in §4, including any
that falsifies this memo's own expectation.**

---

*(§3 onward — feasibility and cost, the measurement, the reachability statement,
cross-ISO scope, and the owner decision card — are appended after the
measurement is run against this pre-registration.)*
