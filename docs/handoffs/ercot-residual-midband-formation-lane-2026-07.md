# ERCOT-87 (design/charter) — the residual mid-band formation lane: offline-CT RT participation + CC beyond the mitigated SCED2 ceiling

**Status: §6 step 1 (measure-first) EXECUTED 2026-07-19 — see §8. Basis B
(CC beyond the mitigated ceiling) is MEASUREMENT-REFUTED and closed; basis A
(offline-CT startup-inclusive participation) is measurement-supported. No
apply seam, no solve, no registration — the §6 step 2 build remains
owner-gated.** Successor lane to ERCOT-86 (`ercot-moderate-tightness-formation-design-2026-07.md`),
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

## 8. Measurement results — §6 step 1 executed (2026-07-19)

Probe: `scripts/probes/ercot87_midband_basis_measure.py`; artifact:
`data/raw/_validation-source/ercot87_midband_basis_measurement.json`.
Measurement only — nothing here feeds the model; observed lambda enters only
as the adjudication reference. Corpus: the four on-disk NP3-965 sample-day
parquets (ERCOT-74/75/86 intake, no new fetch). Coverage: **35/68** (2024) and
**37/65** (2025) actual $150–500 hours fall on sample days; the largest
uncovered block is the Jan-2024 winter-morning cluster (Jan 15/16/21–22 —
never intaken; the corpus's 2024 tail days start Mar 4). Actual RT is hourly
(mean of 4–12 SCED intervals), so per-hour reach flags are conservative;
MW-mass fields — not raw curve maxima, which saturate on tiny cap-priced
proxy-extension slivers — carry the evidence.

### 8.1 Basis B — REFUTED and closed

The mitigated-ceiling hypothesis fails its own §3.2 kill criterion: **SCED1
and SCED2 are indistinguishable on the CC online spare** in the covered
mid-band hours — identical spare MW (means 349 vs 349 in 2024, 629 vs 629 in
2025), in-band mass within noise (27 vs 25 MW; 19 vs 21 MW), ladders equal
rung-for-rung within 1–3 mult points in every net-load bin, and
`basisB_gain` (SCED1 reaches lambda where SCED2 does not) fires in **0/72**
covered hours. The Submitted TPO curve tops out *lower* still (median hourly
max $89–104): the high tops on SCED1/SCED2 are the proxy extension, not
submitted offers. So the ~29–52 p90 effective-HR ceiling on CC is the
**submitted offer shape itself, not mitigation** — there is no unmitigated CC
offer mass in the band for an apply seam to recover, on any disclosed step.
The CC half of the residual cannot form from CC offers; in those same hours
the band-priced mass sits in the offline quick-start pool (below), which
unifies the phenomenon under basis A.

### 8.2 Basis A — SUPPORTED

* **The pool exists and is band-priced.** The offline startable CT pool
  (statuses OFFQS/OFFNS; full SCED curves, startup offers and Min Gen Cost
  disclosed) averages 700–800 MW across the covered mid-band hours, of which
  **102–140 MW is priced inside $150–500** and 74–107 MW within ±33% of
  lambda — roughly **5× the in-band mass of the entire online CT spare**
  (24–35 MW) and 6× the CC spare's (19–27 MW). The online-spare wall was not
  mis-priced; it is simply not where the band's offer mass lives.
* **SCED demonstrably uses it.** 4,191 (2024) / 2,988 (2025) OFF→ON CT
  starts in the corpus; in the covered mid-band hours the median hour sees
  **12–18 CT units (215–491 MW) start**, and a just-started CT clears at an
  as-offered price within ±33% of lambda in **25/35** (2024) and **30/37**
  (2025) covered hours.
* **The ladder shape is right where the residual lives.** The pool's
  SCED2-basis p70/p90 rungs in the tight bins (p90/p97 net-load, bins 5–6)
  sit at effective-HR mult ~44–620 (2024) / ~45–356 (2025) ≈ $110–1,800 at
  prevailing gas — the $150–500 band's mult range (~50–200) falls inside the
  pool's upper-rung span in exactly the bins where ERCOT-86's un-formed hours
  cluster. Coverage per bin is 165–512 intervals over 9–35 days (thinnest:
  bin 6, 2024 — 192 intervals/9 days; disclosed, not capped).
* **Honest caveats.** (a) Most *started* MW clears cheap (MW-weighted median
  cleared mult 13–16 ≈ $35–45 — inframarginal reliability/AS starts); the
  band prices on the marginal tail, so an apply seam must offer the pool at
  its ladder and let the LP clear it, never force it. (b) The per-hour max
  cleared price often lands far above lambda (Base Point falling on
  proxy-extension segments), which is why raw-max flags are permissive.
  (c) The pool ladders' p10–p30 rungs are negative (min-gen curve bottoms) —
  an apply seam consumes only the above-LSL startable increment.

### 8.3 What this means for §6 step 2 (still owner-gated)

One mechanism only (basis B is closed): an **economic fast-start
availability** — the offline-CT pool offered to the LP at its measured
per-bin SCED2 ladder, year-scoped 2024/2025 (rule 13, same 2023 bar as the
RT wall), gated on unit physics (min-down ≤ 2 h — rule 12), reconciled with
existing mechanisms per rule 19 (no overlap by construction with the ERCOT
gas commitment bridge, which is merchant gas-**CC** only, and none with the
RT wall, which is ON-status spare only — this pool is disjoint from both by
status and class). D-2 attribution enumeration stays mandatory before the
seam is written. Cadence per §6.2: default-off gate, single-year 2024
rule-16 probe, C3a level guard + zero-spurious check, then 2025, then
full-span LOYO.
