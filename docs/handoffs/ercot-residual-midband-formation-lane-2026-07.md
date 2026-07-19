# ERCOT-87 (design/charter) — the residual mid-band formation lane: offline-CT RT participation + CC beyond the mitigated SCED2 ceiling

**Status: design/feasibility only. No code, no solve, no registration this
document.** Successor lane to ERCOT-86 (`ercot-moderate-tightness-formation-design-2026-07.md`),
opened per rule 19 (one mechanism per phenomenon — the ERCOT-86 RT/SCED online-spare
wall is closed; what it does *not* reach is a distinct phenomenon with its own
measured basis, not a knob on that wall).

## 0. One-line answer

The ERCOT-86 RT wall closes the annual level and forms the mid-band **where the
online-spare stack genuinely exhausts** (2024: 13/68 hrs; 2025: 6/65 hrs), but
under-fills the $150–500 band ~5–10×. The un-formed ~55–59 hours/year are
structurally out of the online-spare surface's scope for **two independent,
separately-measurable reasons**: (a) **offline quick-start CTs** that clear in
real time via startup-inclusive SCED offers — invisible to a Base-Point→HASL
*online*-spare surface — and (b) **CC spare above the mitigated SCED2 ceiling**
(p90 effective-HR mult caps at ~52 in 2024 / ~29 in 2025 ≈ $90–160, below the
band) in the hours where CC, not CT, is the marginal walled class. Each is a new
mechanism; neither is a cap/boundary retune of the ERCOT-86 wall.

## 1. The target (what ERCOT-86 leaves on the table)

From ERCOT-86 §9/§10, the residual at **actual $150–500 hours** after the RT wall:

| year | actual mid-band hrs | model formed in-band | model p50 / p90 @ actual mid-band | annual resid |
|---|---|---|---|---|
| 2024 | 68 | 13 | $52 / $128 | −0.34 |
| 2025 | 65 | 6 | $65 / $137 | +0.44 |

The level is closed and the formed hours are correctly placed with **zero spurious
hours** — so this lane is **pure shape (band occupancy), never level**. The
un-formed hours are spread across shoulder months (Apr/May/Jul/Oct/Dec), i.e. the
diffuse moderate-tightness regime, not the sharp scarcity tail.

## 2. Why the ERCOT-86 online-spare wall cannot reach them (measured, §9/§10)

The wall's ladder is the **Base Point → HASL** segment of the **SCED2
(as-dispatched, mitigated)** offer curve of **ON-status** merchant CC/CT. Two
structural exclusions follow directly from that construction:

1. **Offline units contribute no online spare.** A CT that is telemetered OFF at
   the tight interval has no Base-Point→HASL headroom, so none of its capability
   enters the surface. Yet in reality ERCOT's fast-start CTs come on *within the
   operating hour* via SCED, and their offers — which must recover startup over a
   few dispatched hours — are exactly the kind of $150–800 marginal offer that
   forms the moderate-tightness band. The online-spare surface is blind to them
   by construction.
2. **CC online spare is mitigation-capped.** SCED2 is the *mitigated* step; the CC
   class's measured p90 effective-HR multiplier caps at ~52 (2024) / ~29 (2025) —
   ≈$90–160 at prevailing gas, structurally **below** the $150–500 band. So in the
   hours where the marginal walled class is CC (not CT), the wall floors CC at its
   own mitigated ceiling and the LP still clears below the band. CT can price the
   band (p90 mult 283–1289) but only where CT online spare is the marginal walled
   supply; in CC-marginal hours the band cannot form from this surface at all.

Confirmed in the artifact (`ercot_sced_offer_wall_condbinned.json`, bins 4–6):
CC p90 mult 28–52 across both years; CT p90 mult 283–1289. The band forms only in
the CT-marginal subset — which is exactly the 6–13 hours that *did* form.

## 3. Candidate mechanisms (design sketch — NOT built)

Both are measured, forward-native, rule-13-admissible in principle; each is a
**separate** apply seam from the ERCOT-86 wall (rule 19), sharing its net-load-bin
conditioning and per-year artifact scoping.

### 3.1 Offline-CT startup-inclusive RT participation
* **Basis.** The same NP3-965 SCED Gen Resource Data already on disk carries, per
  interval per resource, `Telemetered Resource Status` and the SCED2/SCED1 curves
  **including for units that transition OFF→ON within the day**. The measurable
  quantity is the startup-inclusive marginal offer of a CT in its first dispatched
  intervals after a start — a curve segment the online-spare derive currently drops
  (it keeps only Base Point → HASL of already-ON units).
* **Sketch.** Derive a second ladder from the OFF→ON transition intervals (offer
  price as effective-HR multiplier, net-load-binned), and apply it as a *quantity*
  the LP may commit at that offer — i.e. an economic fast-start availability the
  online-spare wall omits. This is commitment-adjacent; it must gate on unit
  physics (`min_down`, startup cost), not class names (rule 12), and must not
  double-floor units the gas commitment bridge already commits (rule 19 — enumerate
  D-2 attribution first).
* **Admissibility.** Startup-inclusive offers regenerate for a forward year from
  forward gas + the same net-load driver (rule 13). **Risk to watch:** must not
  become a min-gen floor binding in hours the driver says CTs are offline
  (rule 12 — CT overnight CF ≈ 0).

### 3.2 CC spare beyond the mitigated SCED2 ceiling
* **Basis.** SCED2 is mitigated; the **SCED1 (pre-mitigation)** curve and the
  **Submitted TPO** points (both already fetched into the parquet, both currently
  unused by the derive) carry the CC offer *above* the mitigation cap. The question
  the derive must answer honestly is *which step reproduces the observed system
  lambda* in CC-marginal mid-band hours — SCED1 or SCED2 (the fetch script kept
  both deliberately for exactly this).
* **Sketch.** Where the mitigated ceiling is demonstrably the wrong basis for CC
  price formation in the band (a measurement, not a residual fit), extend the CC
  ladder's upper rungs to the SCED1/TPO basis in those bins. **This is NOT raising
  the ERCOT-86 CC cap to fit the residual** (rule 1/19) — it is a distinct measured
  basis question adjudicated on which SCED step matches lambda, with the ceiling
  left exactly where mitigation puts it if SCED1 does not measurably reproduce the
  band.

## 4. Feasibility / data

* **On disk already** (no new intake): the NP3-965 parquets carry SCED1, SCED2,
  Submitted TPO, and Telemetered Resource Status for every interval-resource,
  including OFF units — both candidate bases are measurable from the ERCOT-84/86
  sample days without further fetching. 2024 (tail+control) and 2025 (tail+control)
  cover both years the wall ships for.
* **2023 remains blocked** identically to ERCOT-86 §5 (SCED unreachable) — this
  lane inherits the 2024/2025 year-scoping and the 2023 input-blocked caveat.
* **Coverage caveat.** OFF→ON transition intervals and CC-above-ceiling segments
  are *rarer* than online-spare segments; the sample-day corpus may under-sample
  them. Disclose per-bin transition/segment counts in provenance before trusting a
  bin (the ERCOT-86 derive already prints this — extend it), and widen the tail-day
  intake if a bin is thin rather than shipping a thin ladder silently.

## 5. Rule ledger

* **Rule 1/11** — a real market behaviour (fast-start RT participation; unmitigated
  CC formation) stays in even if the residual barely moves; never reject on fit.
  Conversely never *reach* the band by raising the ERCOT-86 cap against the residual.
* **Rule 13** — both bases are ex-ante posted offers, forward-native under the
  net-load driver; year-scoped to derive years; no outcome pin.
* **Rule 12/19** — offline-CT participation gates on unit physics, not class tuples;
  enumerate what already commits/floors CC and CT (gas commitment bridge, cleared-
  share wall) and reconcile — do not stack a third floor on the unexplained residual.
* **Rule 23** — new ladders freeze against residuals; re-derive only on SCED source
  update.

## 6. Recommended path (for the owner to authorize)

1. **Measure first, no apply.** Extend `derive_ercot_sced_offer_wall.py` (or a
   sibling probe) to emit the two candidate ladders + per-bin coverage from the
   SCED1/TPO/OFF-transition data already on disk. Read whether either basis
   measurably reproduces the CC-marginal / offline-CT mid-band hours **before**
   writing an apply seam. If the data does not support it, the lane closes as a
   documented measurement-limit — the ERCOT-86 partial fill stands as the honest
   online-spare result.
2. **If a basis holds**, build ONE mechanism at a time behind its own default-off
   gate, single-year 2024 rule-16 probe, C3a level guard + zero-spurious check,
   then 2025, then full-span LOYO — the ERCOT-86 cadence.
3. **Keeper stays ercot82** throughout (rule 27, owner-only swap).

## 7. Deliverable of this charter

This document only. The build is chartered, not started, pending owner go-ahead.
