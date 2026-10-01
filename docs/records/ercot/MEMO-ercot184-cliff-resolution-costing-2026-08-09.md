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

## 3. FEASIBILITY AND COST UNDER THE CURRENT LP LAYOUT

All figures below are read off the keeper's own 2023 fleet, reconstructed with
no LP (`scripts/lib/bundle_fleet.reconstruct_bundle_fleet` on
`results/calibration/ercot181_positiontail_B`).

### 3.1 What (c2) can actually reach — the row census

| tranche family | rows | capacity (MW) |
|---|---:|---:|
| `mustrun` | 10 | 3,650 |
| `committed` | 132 | 19,294 |
| **`econc` — the N-slice econ ramp, (c2)'s object** | **864** | **36,115** |
| `econ` — FLAT econ tranche, no ramp | 18 | 8,825 |
| `peak` | 445 | 6,608 |
| other | 311 | 6,253 |
| **total** | **1,780** | **80,745** |

The 864 `econc` rows are **144 plant-groups × exactly 6 equal-width slices** —
verified directly: the within-plant relative capacity spread across a plant's
six slices is **0.000e+00**, i.e. `slice_cap = curve_cap / n` exactly as the code
reads. By class: CC_REGULAR 252 rows / 21,473 MW, CT_PEAKER 336 / 4,493,
CC_CHP 108 / 4,443, ST_GAS 66 / 4,891, CT_CHP 102 / 816.

**A scope limit that must be stated up front: 8,825 MW of econ capacity has no
ramp to refine.** Coal's entire econ band — **6,867 MW across 10 rows** — is a
single flat `econ` tranche, as are ST_GAS 1,949 MW and ST_CHP 9 MW. So (c2)
addresses **80.4 %** of econ capacity and **0 %** of coal's. That matters for
this object specifically: on the top-50 Aug–Sep gap hours COAL_PRB dispatches
9,486 MW against an annual mean of 4,979 (ercot-177 §5), so a materially
non-refinable block sits inside the very hours (c2) is aimed at.

### 3.2 Column count, memory, wall-clock

The flat LP layout is `T × (n_gen + 4·n_zones + 3·n_storage + n_links)`. ERCOT
2023: `T = 8,760`, `n_gen = 1,780`, `n_zones = 7`, `n_storage = 5`,
`n_links = 10` → **16,057,080 columns**. Re-slicing changes `n_gen` only, and
the thermal block dominates the constraint matrix's nonzeros, so column count
is the right first-order scalar:

| scheme | slices/plant | rows | LP columns | vs keeper |
|---|---:|---:|---:|---:|
| keeper (today) | 6 | 1,780 | 16,057,080 | 1.00× |
| R1 — top 1/6 split 6 ways | 11 | 2,500 | 22,364,280 | **1.39×** |
| R3 — geometric top, m = 24 | 24 | 4,372 | 38,763,000 | **2.41×** |
| R2 — uniform 60 | 60 | 9,556 | 84,174,840 | **5.24×** |
| R4 — top 1/6 split 60 ways | 65 | 10,276 | 90,482,040 | **5.64×** |

Against the measured baseline — **~6.6 GB RSS and ~20 min/year** for one ERCOT
per-plant year (PRECOMMIT-ercot181 §9) — even the *modest* R1 lands near 9 GB,
and **R3 at ~16 GB already exceeds this environment's 15 GB budget for a single
year**, before any concurrency. Rule 12's two-concurrent-run cap is forfeited at
every refinement level: a control/arm pair must run strictly sequentially, so a
three-year A/B costs roughly **2 × 3 × (20 min × the column factor)** — R1 ≈ 3.5 h,
R3 ≈ 6 h, R2/R4 ≈ 12–14 h of solve time per adjudication round, in a lane whose
last three rounds each needed several such rounds.

This is real but it is **not the expensive part**. §3.3 is.

### 3.3 What moves in P0 — the P1-only seam is BREACHED, and this is the real cost

Every ERCOT offer-surface mechanism since ERCOT-86 is applied at the
**`mc_bid_adjust` seam** (`pipeline/solve.py`): P0 solves on `mc_base`, then
`mc_bid = mc_base + startup_markup + mc_bid_adjust`. That seam is what lets each
arm be *proved* not to disturb commitment — the family's whole verification
story rests on P0 being bit-identical.

`_econ_curve_steps` writes **heat rates into the base fleet**. Its output is
inside `mc_base`, which *is* the P0 objective. So a slicing change moves P0 by
construction, and the seam does not apply. Quantified:

* **P0's own solve changes** — different column set, different dispatch,
  different warm-start basis. No bit-identity anchor exists anywhere in the run.
* **P0's dispatch feeds `compute_monthly_markup(fleet, fleet_arrays, r0.dispatch,
  …)`**, which sets the P1 startup amortization. **122 `committed` rows carrying
  16,545 MW of gas CC/CT/ST capacity have their P1 bid set by P0 run lengths**
  (CC_REGULAR 9,238 MW, ST_GAS 3,915, CT_PEAKER 3,392). A (c2) build therefore
  reprices **16.5 GW of committed gas** through a channel that has nothing to do
  with offer resolution — capacity sitting directly beneath the object hours'
  marginal rows.
* **The verification cost is the binding one.** The ercot-181 seam proof carried
  eight assertions (SP-α1…α8); **α1, α2, α3 and α5 are byte-identity claims** —
  delta confined to the intended rows, null-encoding composing byte-identically,
  gate-off shas matching the record, frozen artifacts unmoved. **None is
  available to (c2).** Every control-vs-arm difference is confounded with
  commitment-side motion, so the mechanism cannot be isolated by proof, only by
  argument. In a lane where the last two rejections (items 21, 23) turned
  entirely on *decomposing* a headline number into its real and artefactual
  parts, losing the ability to prove isolation is the single largest cost here.

### 3.4 What re-derives — nothing, and this is genuinely cheap

The one clearly favourable finding. The armed measured ladders are keyed on
**(class, net-load bin, position)**, never on the slice count: a re-sliced row
reads the **same frozen artifact at a new position**. So (c2) triggers **no
re-derivation, no new corpus, no new statistic, no rule-23 trigger** — unlike
items 21/22/23, each of which needed a new artifact vintage. Likewise
`gas_offer_margin_markup_mult` interpolates the measured physical basis
`phys_econ_low → phys_econ_high` at the slice's own ramp position, and
`chp_floor_by_suffix` spreads the CHP steam floor across slices in fill order;
both work at any slicing (though the floor's landing changes — 61 of the 144
plant-groups carry econ min-gen).

Two concrete code items a build would have to handle, recorded so they are not
discovered late:

1. **A hard ceiling of 99 slices per plant.**
   `data/fleet/legacy_bins._coal_tranche_rank` maps `econcNN` to
   `2.0 + int(NN)/100.0`, which **collides with `econhi`'s rank 3.0 at NN ≥ 100**
   and would silently corrupt the ERCOT-144 coal per-plant capacity-window
   mapping. The defect is **latent today** (coal carries no `econc` rows — §3.1),
   but the function dispatches on suffix, not fuel, so any ISO or future config
   that gives coal a smoothed ramp at ≥ 100 slices trips it.
2. **Rule 24 / rule 28(c):** a non-uniform scheme is a NEW `ScenarioConfig`
   field, cache-key registered dropped-at-default, with its matrix row in the
   same PR.

---

## 4. THE MEASUREMENT

`scripts/probes/ercot184_cliff_resolution_costing.py` →
`results/calibration/ercot184_cliff_resolution.json`. No LP, no field, no
derive, no registered run.

**Method — invariant-quantity repricing (IQR).** Re-slicing preserves each
plant's total MW, so the quantity the thermal stack must serve in an hour is
unchanged. The measurement therefore holds the **cleared quantity `Q_h` fixed**
and asks what the refined stack prices *at that quantity*. `Q_h` is taken from
the keeper stack's own sorted cumulative capacity at its last in-the-money row,
and both stacks are then read by the **identical rule** — so the read's own
residual cancels out of every delta rather than contaminating it.

### 4.1 Validation — what earns the right to believe the numbers

* **V-0.** The gate-off composed markup's sha reproduces the ercot-178 seam-proof
  record (`25a4ba69…`) at this HEAD. **PASS.**
* **V-1.** The priced row geometry — within-plant cumulative midpoints → `rel` →
  position-tail-completed ladder → composed markup — reproduces the builders'
  own `_compose` output **BYTE-IDENTICALLY** across the 490 priced rows,
  `max|err| = 0.000e+00`. The mirror *is* the builders'.
* **R0, the identity control.** Re-slicing at the keeper's own six equal slices
  returns **Δ = +0.0000/MWh with 0 hours moved**. Every non-zero number below is
  mechanism, not machinery. *(Two defects were found and fixed by this control
  before any result was believed: an ulp gap between `0.5*(x[k]+x[k+1])` and
  `(k+0.5)/n` that perturbed re-sliced costs at 1e-16, and zero-available-
  capacity rows flattening the cumulative-capacity curve so the read landed one
  row low — a one-sided **negative** bias across 339 hours. Both are recorded in
  the probe.)*

**Disclosed approximations, none of which the conclusion turns on.** (i) A pure
merit-order read of the same fleet reproduces the LP's annual load-weighted
price at **$43.02 vs $43.45** (−1.0 %); in the object hours it runs **−$5.52**
low (max abs $294). It cancels in the deltas by construction. (ii) The read is
at system grain — ERCOT's zonal prices are identical in **84.2 %** of 2023
hours. (iii) Non-econ bids omit the P1 startup amortization, which is **zero on
every econ row by construction** (`_econ_curve_steps` sets `startup = 0`) and
identical in both stacks elsewhere. (iv) A re-sliced row's cost is interpolated
in the ramp shape `f(t)` from the keeper's own six slices — exact to machine
precision for most of the 144 plant-groups (median residual 4e-6 $/MWh), p99
$0.50, max $0.59 on a base cost of $17–30, against ladder markups of hundreds to
thousands.

**Object hours** = the top-100 Aug–Sep 2023 gap hours, carrying **68.1 %** of
the annual positive load-weighted gap.

### 4.2 P-1 — where the marginal row sits today. CONFIRMED.

Across the 100 object hours the keeper's marginal row is `peak*` in **55**,
`econc` in **33**, `committed` in 1, other in 11. Its ladder position is

> **rel p50 0.643, min 0.019, MAX 0.802.**

It never reaches even the p90 grid top, let alone reality's q_act 0.9976. This
independently reproduces ercot-181 §4's "p50–p70 region of the measured
ladders" from a different instrument. Among the 33 econ-marginal hours the slice
index is k=5 in 14, k=4 in 11, k=3 in 5, k=2 in 2, k=0 in 1 — so the ramp's
**top slice is marginal in 14 % of object hours**, which is precisely why (c2)
is not trivially inert and deserved measuring.

### 4.3 M-2 — the refinement DOES reach the cliff. (My own structural hypothesis, FALSIFIED.)

Going in, I expected the econ ramp's top not to reach `rel → 1`, since the peak
tranche sits above it in the plant's stack. **That was wrong, and the
measurement says so.** The econ ramp spans a median **61.8 %** of its plant's
stack (p25 0.550, p75 0.769, max 1.000), so refining its top does drive rows to
the top of the plant:

| scheme | slices | max within-plant share | max ladder `rel` | econ rows at `rel` > 0.9 | ladder mult at max `rel` |
|---|---:|---:|---:|---:|---:|
| keeper (n = 6) | 6 | 0.9625 | 0.9427 | 33 | 24.8× gas |
| R1 — top 1/6 split 6 | 11 | 0.9938 | 0.9904 | 382 | 145.1× |
| R2 — uniform 60 | 60 | 0.9963 | 0.9943 | 626 | 1,824.8× |
| **R3 — geometric top, 24** | 24 | 0.9996 | **0.9993** | **2,041** | **3,026.1×** |
| R4 — top 1/6 split 60 | 65 | 0.9994 | 0.9990 | 3,663 | 2,876.1× |

**(c2) works exactly as advertised on its own terms.** It takes the model from
33 rows in the measured top decile to **3,663**, and lets it quote the cliff
face at **3,026× delivered gas** — into the same HCAP wall the position-tail
completed at item 23. Whatever else is true, this is not a mechanism that fails
because it cannot express the cliff.

### 4.4 M-3 — AND THE LP STILL DOES NOT CLEAR THERE. This is the answer to §0.

Under R3 — the scheme whose rows reach `rel` 0.9993 — in the 100 object hours:

| | keeper (coarse) | R3 (refined) |
|---|---:|---:|
| marginal row ladder `rel`, p50 | 0.6432 | **0.6987** |
| marginal row ladder `rel`, max | 0.8020 | **0.8334** |
| **marginal rows at `rel` > 0.9** | 0 / 100 | **0 / 100** |
| marginal rows at `rel` > 0.99 | 0 / 100 | **0 / 100** |
| object-hour price p50 | $155.64 | **$143.59** |
| *(actual object-hour price p50)* | | *$910.66* |

The refined marginal row **is one of the new econ slices in 35 of 100 hours**,
sitting at ramp position `t` p50 0.8825 / max 0.9944 — the refinement's own
slices do become marginal, near the very top of the ramp — **and they still read
ladder position ≤ 0.833.**

**And this holds in EVERY scheme, not just R3** — the marginal row's ladder
position is capped in the same narrow band however hard the curve is refined:

| scheme | refined marginal `rel` p50 | max | **marginal rows at `rel` > 0.9** | object price p50 |
|---|---:|---:|---:|---:|
| R0 control | 0.6432 | 0.8020 | **0 / 100** | $155.64 |
| R1 | 0.6432 | 0.8310 | **0 / 100** | $148.00 |
| R2 | 0.7091 | 0.8310 | **0 / 100** | $143.70 |
| R3 | 0.6987 | 0.8334 | **0 / 100** | $143.59 |
| R4 | 0.6432 | 0.8322 | **0 / 100** | $147.11 |

Not one marginal row, in any scheme, in any of the 100 object hours, ever
reaches `rel` 0.9 — while the same schemes place up to **3,663 rows** above it
(§4.3). And the object-hour median price *falls* in every scheme, against an
actual of $910.66.

> **The clearing position moves by +0.055 of the ladder axis (0.643 → 0.699) and
> ceilings at 0.833. Reality's price forms at 0.9976. The model gains 2,041 rows
> at the cliff and clears on none of them.**

This is item 23's finding reproduced from the opposite direction. Item 23 gave
the model the right conduct above p90 and the LP never read it; (c2) gives the
model rows *at* the cliff and the LP never clears on them. **The clearing
position is a quantity fact — set by demand against total capacity — and no
MW-preserving re-slicing of an offer curve can move it more than marginally.**

### 4.5 The reach — and it SATURATES

| scheme | slices | rows | top slice, % of ramp | **Δ annual lw** | net of shed | % of the +$14.44 bar | shed-exposed h | object-hour mean Δ | G-REACH |
|---|---:|---:|---:|---:|---:|---:|---:|---:|:--|
| R0 identity control | 6 | 1,780 | 16.667 | **+0.0000** | +0.0000 | 0.0 % | 0 | +0.000 | — |
| **R1 top 1/6 × 6** | 11 | 2,500 | 2.778 | **+1.9862** | +1.9862 | **13.8 %** | **0** | +48.889 | **FAIL** |
| R3 geometric top 24 | 24 | 4,372 | 0.189 | +1.7897 | +1.7897 | 12.4 % | 0 | +37.773 | **FAIL** |
| R2 uniform 60 | 60 | 9,556 | 1.667 | +1.7686 | +1.7686 | 12.2 % | 0 | +36.176 | **FAIL** |
| R4 top 1/6 × 60 | 65 | 10,276 | 0.278 | +1.6565 | +1.6565 | 11.5 % | 0 | +36.581 | **FAIL** |

**The reach saturates at ~+$1.7–2.0/MWh and DECLINES with refinement depth.**
The cheapest scheme (R1, 11 slices, ×1.39 columns) is the **best**; the most
aggressive (R4, 65 slices, ×5.64 columns) is the **worst**. Across a 6× range in
slice count and a **90× range in top-slice fineness** the answer never leaves a
±$0.17 band around +$1.8/MWh. **This is a ceiling, not an under-resolved
parameterization** — and that matters, because it forecloses the natural
follow-up ("try more slices"). More slices is measured, and it is worse.

*Why it declines.* Refinement is a two-sided, MW-preserving redistribution: R1
moves 4,488 hours — **1,710 up and 2,778 DOWN**; R2 moves 7,948 — 4,854 up,
3,094 down, to as low as −$29/MWh. The down-moves are the ramp's body being
repriced cheaper as its slices' midpoints fall, and the more you refine the more
of the body you reprice downward. This is the same two-sided channel ercot-178
§7a named as form (a)'s disturbance leg, arriving here by a different route.

### 4.6 G-SHED adjudication — the falsifier does NOT fire, and that is a real finding

| scheme | clamp displacement MW (p50 / max / object p50) | **shed-exposed hours** | share of Δ from exposed hours |
|---|---|---:|---:|
| R1 | 0.0 / 152.5 / 48.5 | **0** | 0.0000 |
| R2 | 0.0 / 178.2 / 91.8 | **0** | 0.0000 |
| R3 | 15.8 / 170.7 / 77.2 | **0** | 0.0000 |
| R4 | 16.1 / 163.7 / 77.3 | **0** | 0.0000 |

**Zero shed-exposed hours, in every scheme, in every hour of 2023.** The MW
displaced above the $4,750 clamp peaks at ~180 MW against object-hour sub-clamp
headroom measured in tens of GW.

So **(c2) is NOT the ercot-48/49 signature.** Where item 21's +$8.18/MWh
headline was **67.5 % manufactured VOLL shortage**, **100 % of (c2)'s +$1.99 is
genuine offer formation.** This is stated plainly because it is the one thing
(c2) does better than every prior candidate in this lane — the pre-registered
primary falsifier was aimed at it and missed cleanly — **and it still does not
save the mechanism.** (c2) is honest. It is simply too small.

---

## 5. THE HONEST REACHABILITY STATEMENT

**Predictions adjudicated at full magnitude** (§2.3, registered before measuring):

| | prediction | verdict |
|---|---|---|
| **P-1** | marginal rows sit well below the refined region | **CONFIRMED** — rel p50 0.643, max 0.802 |
| **P-2** | the ceiling is the within-step spread at the clearing position, far below $14.44 | **CONFIRMED** — ceiling +$1.99, 13.8 % of the bar |
| **P-3** | uniform refinement is no better than top-refinement | **CONFIRMED** — R2 +1.77 vs R1 +1.99 |
| **P-4** | **no MW-preserving re-slicing can move the clearing position** | **CONFIRMED** — +0.055 on the ladder axis, ceiling 0.833 vs 0.9976 |
| *(auxiliary)* | *ramp refinement cannot reach `rel` → 1* | **FALSIFIED** (§4.3) — it reaches 0.9993 / 3,026× gas. Reported at full magnitude; the conclusion is unchanged and better-evidenced |

**The answer to the load-bearing question, stated as the card demanded it:**

> **(c2) does NOT move the LP's clearing position. It prices the top of the
> curve more accurately — dramatically so, from 24.8× to 3,026× delivered gas —
> and the LP goes on clearing at ladder position ~0.70 because what sets the
> clearing position is quantity, not resolution. It is item 23's failure in a
> more expensive form, and this memo says so.**

**Against the family's budget.** The whole conditioning family's *measured*
offer-formation budget is **~$2.6/MWh** (ercot-178 §7a). (c2)'s ceiling is
**+$1.99/MWh** — the **same channel**, slightly **smaller**, and cleaner
(no shed contamination). It does not work a different channel. It works the same
one, from the position axis instead of the hour axis, and arrives in the same
place.

**Against the bar.** C3a-2023 needs **+$14.44/MWh**. (c2)'s measured ceiling
over the entire family of MW-preserving re-slicings is **+$1.99/MWh — 13.8 %**.
The pre-registered G-REACH bar of +$5.00 **FAILS by 2.5×**. The card asked for
this to be said up front, so: **(c2) lands short by a factor of seven**, and
because the measurement is a *ceiling across schemes* rather than one
parameterization's result, failing it closes the option rather than merely
rejecting a tuning.

**What would still be true after a successful (c2) build.** C3a-2023 would move
from −32.4 % to roughly **−29 %**, still 2.9× outside the ±10 % band. ERCOT's
determination would remain **NOT-YET {C3a, C3b}** — unchanged — at a cost of
1.4–5.6× the LP columns, the loss of the offer-surface family's P0 bit-identity
proof (§3.3), and a repricing of 16.5 GW of committed gas through the
commitment channel.

---

## 6. RULE-25 CROSS-ISO SCOPE

**Fleet representation is not ERCOT-gated by construction, and this is the
sharpest governance fact in the memo.** `_econ_curve_steps` lives in
`src/market_sim/data/offer_curves.py` and is called from
`src/market_sim/data/fleet/assembly.py` on the **ISO-agnostic** assembly path.
There is no ISO gate anywhere in it. Measured across all six keepers:

| ISO | keeper | `smoothing_n` | `exp` | `mid` | `committed_ramp_spread` | `plant_level_fleet` |
|---|---|---:|---:|---:|---:|---|
| ERCOT | `2026-08-09-run181-position-tail` | 6 | 1.0 | 0.35 | 0.0 | False |
| CAISO | `2026-08-09-caiso-184-c1-lpbasis` | 6 | 1.0 | — | 0.0 | True |
| PJM | `2026-08-04-pjm-152-collapse` | 6 | 1.0 | 0.35 | 0.0 | True |
| MISO | `2026-08-05-miso-132b-cc-committed` | 6 | 1.0 | — | 0.0 | True |
| NYISO | `2026-08-08-nyiso-132-cf-arm` | 6 | 1.0 | — | 0.0 | True |
| NEISO | `2026-08-06-neiso-87-control` | 6 | 1.0 | — | 0.0 | True |

Consequences a build must respect:

1. **Changing the slicing default moves all six keepers at once.** Every ISO runs
   `n = 6`. A default change is a six-ISO fleet change and would invalidate every
   current keeper simultaneously — inadmissible under rule 25. A non-uniform
   scheme must enter as a **NEW default-off `ScenarioConfig` field**, armed
   per-ISO, cache-key registered dropped-at-default.
2. **Breakpoints fitted on ERCOT's residual are ERCOT's alone.** Each ISO must
   derive its own from its own market's data; the others enter the matrix as
   `U`, never inheriting ERCOT's verdict (rule 28(d)).
3. **A dormant coupling to flag now:** `_econ_curve_steps` is *also* the
   committed-band slicer when `committed_ramp_spread > 0`, sharing the same
   `n_curve`. All six keepers run `0.0`, so the coupling is inert **today** — but
   any ISO that later arms it would silently inherit the new slice count on its
   committed band as well. A per-scheme field must be scoped so this cannot
   happen by accident.
4. **The column cost lands harder elsewhere.** Five of six ISOs run
   `plant_level_fleet = True` (ERCOT is the exception), so their row counts are
   already higher and §3.2's ×1.39–5.64 multipliers apply to a larger base.

---

## 7. GOVERNANCE

* **Rule 1 `[R-STRUCT]`:** no mechanism built, none stretched to reach the band.
  The measurement is reported at full magnitude including the finding that
  falsifies this memo's own structural hypothesis (§4.3).
* **Rule 13 `[R-MEASURED]`:** every figure is diagnostic sizing read off
  committed artifacts and the keeper's own reconstructed fleet. No probe output
  enters any mechanism; no outcome is pinned.
* **Rules 15/16 `[R-DASHBOARD]`/`[R-ALLYEARS]`:** **no run solved, none
  registered — nothing to register.** This is a costing memo, not a mechanism
  test.
* **Rule 22 `[R-HOLDOUT]`:** ERCOT holds no `complete` and no `final` marker.
  Every tool invocation touched **2023 only**; no out-of-training year was
  solved, scored, read or registered.
* **Rule 23 `[R-DOF]` / 24 `[R-REGISTRY]`:** zero new scalars, zero new
  `ScenarioConfig` fields, no derive, no off-registry channel. All seven frozen
  artifacts untouched (read-only).
* **Rule 25 `[R-ISO-SCOPE]`:** ERCOT only. No other ISO's files, bundles, keeper
  shard or matrix column was modified; §6 reads their configs to *scope the
  blast radius*, which is the rule's own requirement.
* **Rule 27 `[R-PUSH]`:** no existing source file ≥300 lines modified; the one
  new file (the probe) is pushed as its exact on-disk bytes and blob-verified.
* **Rule 28 `[R-MECH-MATRIX]`:** **no cell minted, no verdict written.** Nothing
  was armed, built, or tested as a mechanism — duty (b) does not attach. Should
  a build ever be chartered, its row lands in the same PR as its field (duty c).
* **Keeper:** `2026-08-09-run181-position-tail` **untouched** — no promotion, no
  demotion, no re-key, no keeper-shard edit.
* **GitHub Actions:** nothing offloaded; every reconstruction and measurement ran
  in-session.

---

## 8. OWNER DECISION CARD — build (c2), or close the lane?

**Recommendation: CLOSE THE LANE.**

| | |
|---|---|
| **What (c2) delivers** | +$1.99/MWh on C3a-2023 (−32.4 % → ≈ −29 %), **13.8 %** of the +$14.44 bar |
| **Pre-registered build bar (G-REACH)** | +$5.00/MWh — **FAILED by 2.5×** |
| **Is the gain real?** | **Yes — 100 % genuine offer formation, zero shed-exposed hours.** The ercot-48/49 falsifier was aimed at it and missed cleanly |
| **Does it move the clearing position?** | **No.** +0.055 on the ladder axis (0.643 → 0.699), ceiling 0.833, against reality's 0.9976 |
| **Does more resolution help?** | **No — measured.** The reach saturates and then *declines*: 11 slices +$1.99 → 65 slices +$1.66 |
| **Cost** | ×1.39–5.64 LP columns (R3 alone ≈ 16 GB, over this box's budget); **forfeits the offer-surface family's P0 bit-identity proof**; reprices 16.5 GW of committed gas through the commitment channel |
| **Determination effect** | **NONE.** ERCOT stays NOT-YET {C3a, C3b} |
| **Cross-ISO** | Not ERCOT-gated; all six keepers share `n = 6` |

**The one-line reading.** The 2023 miss is not a resolution defect. (c2) resolves
the cliff completely — 33 rows at the measured top decile become 3,663, quoting
3,026× delivered gas — and buys **13.8 %** of the bar, because the LP's clearing
position sits at ladder 0.70 and stays there. **You cannot reach a price by
adding rows above where the market clears.** That is now measured three
independent ways: item 21 (hour axis), item 23 (position axis, level), and this
memo (position axis, resolution).

**What this memo does NOT claim.** It does not say C3a-2023 is unreachable in
principle — only that *offer-curve resolution* cannot reach it, which was the
chartered question. The measurement points at what would have to change: the
clearing position itself, i.e. the **quantity** of cheap capacity the model has
available in those 100 hours. Every face of that has been separately adjudicated
and closed (ercot-177 §6, ercot-181 §7 I-3: reality's ON merchant-gas fleet held
only 0.3–0.9 GW of sub-λ̂ spare), and D5 does not authorize re-opening any of
them.

**The options, plainly:**

* **(A) CLOSE — recommended.** Record (c2) as costed and refused on measured
  reach. C3a-2023 stands as a **model miss at full magnitude (−32.4 %)** with
  the model class named. ERCOT's determination is unchanged either way (decision
  card §2). The program's live returns are **D2** (the fault-3 partial-layer
  re-charter, the only lane that can move C3b-2024), **D3** (the rule-18 grain
  defect), and **D4** (the NP3-965 re-upload) — none of which this lane competes
  with.
* **(B) BUILD ANYWAY.** Defensible only as a *structural-fidelity* purchase
  under rule 1 — the model would represent within-plant offer conduct more
  faithfully, as item 23 was promoted for. But item 23 cost zero LP columns and
  kept a bit-identical P0; (c2) costs 1.4–5.6× columns and the seam proof. On
  the evidence I do not recommend paying that for +$1.99/MWh and no
  determination change.
* **(C) NARROW REBUILD.** If any part is kept, it is **R1 only** (top 1/6 split
  6 ways, ×1.39 columns) — the cheapest scheme *and* the highest-reach. Note it
  still fails G-REACH and still breaches the P0 seam.

**Next shorthand: ercot-186.** *(ercot-185 is the concurrently-running D2 fault-3 partial-layer lane.)*
