# FINDING — ercot-239 (2026-08-30): the 14-hour missed-event family is MEASURED ENERGY-LAMBDA SCARCITY IN TIGHT-ROOM HOURS THAT NO RESERVE ADDER CARRIED — the real prints are RTLMP-side (published RTORPA ≈ 0 in 12 of 14, RTORDPA ≤ $5.44 in all 14, system λ ≈ the print in every hour), the model RANKS 12 of 14 inside its own bottom-5 % reserve room but prices that room at $0.00–$25.68, and the precommit's availability/outage/net-load-ramp priors are largely REFUTED — the object is offer-surface CONDUCT off the August core, landing exactly on the ercot-217 adjudicated conduct/model-class episode

**Session ercot-239, 2026-08-30, branch
`claude/ercot-239-residual-queue-lbkvbf`. ZERO-SOLVE — every number below is
read from committed artifacts (the `ercot236_k33_clip` keeper sidecars, the
committed actuals parquet, the EIA-930 wide extract, the CAMPD outage
records, and the committed measured ORDC/reserves series) — constructions
byte-identical to the ercot-237 probe where shared.** Precommit
`docs/PRECOMMIT-ercot239-missedevents-phase0-2026-08-30.md` pushed +
blob-verified before any measurement; Amendment 1 (the ercot-237 JSON
carries no `lt_200|ge_1000` hour list — V-0 re-based to the 13-h list +
count) and Amendment 2 (the measured reserves series added as a report-only
panel) both recorded and pushed before the measurements they cover.
Probe: `scripts/probes/ercot239_missedevents_phase0.py` →
`results/calibration/ercot239_missedevents_phase0.json` (committed).
The two-config keeper structure (forward `2026-08-25-234-eastex-identity`,
2023 carve-out `2026-08-25-236-swcap-clip-k33`) is UNTOUCHED; no lever is
proposed or armed this round (kill K-3); no matrix cell changes (nothing
tested).

## 0. Verdict in five lines

1. **The real prints were energy lambda, not adders.** In all 14 hours the
   measured `system_lambda` ≈ the RT print ($536–$2,014); published RTORPA
   is ≤ $6.66 in 12 of 14 (h2971 $224, h2058 $28) and RTORDPA ≤ $5.44 in
   all 14. The armed measured-RTORDPA overlay is therefore correctly ~$0
   here — no overlay or adder channel can carry these hours, in the model
   or in reality.
2. **These are genuine tight-room hours, and the model KNOWS it.** Measured
   RTOLCAP sits at p0.1–p17.1 of its year in all 14; the model's own ORDC
   total room sits at ≤ p5 of ITS year in 12 of 14 (h7001 p15.3, h7145
   p91.9) with 0.2–3.6 GW of ORDC-room shortfall in every hour. P1 ("the
   model is far from scarcity") is **REFUTED in the informative
   direction** — the model's tightness *ranking* is nearly perfectly
   aligned with reality's events.
3. **Both ORDC curves are flat there — and both say so.** At those room
   levels the model's ORDC prices $0.00–$25.68, and the REAL ORDC priced
   ≈ $0 too (the measured RTORPA above). Reality's $537–$2,014 came from
   the SCED offer stack pricing tightness the ORDC does not — offer
   CONDUCT, exactly the ercot-217 adjudicated conduct/model-class episode
   object, here enumerated at hour grain outside the August core the k=33
   carve-out lift already covers.
4. The precommit's fixed actual-side drivers under-fire: ramp 4/14, ≥1.5 GW
   net-load gap 2/14 (both wind-led), outage 1/14 (h2058, the March
   outage-season member, overlay at p99.2), tie exports 0/14 (ERCOT was
   net-IMPORTING 111–873 MW in every event hour), 7/14 UNATTRIBUTED at the
   declared thresholds (kill K-2 honoured — reported, not force-fitted).
5. One systematic actual-side signal survives below threshold: the
   event-hour demand gap (EIA-930 actual − model demand) is +651…+873 MW in
   12 of 14 hours against a +98 MW year mean — an event-hour demand
   understatement worth its own bounded look, distinct from the conduct
   object.

## 1. V-0 and the amendments

V-0 passed: the recomputed population {h : model < $200 ∧ actual ≥ $500} is
exactly the 14 committed hours (13-h `lt_200|500_1000` list identity +
`lt_200|ge_1000` count 1 + FINDING-ercot237 §3's h4578), model/actual
series byte-identical to the ercot-237 constructions. Amendment 1 re-based
the cross-check (the committed JSON never carried the corner cell's list);
Amendment 2 added the measured reserves series as a report-only panel after
the declared M-2 measurements surfaced the model-side reserve state as the
discriminating panel. EIA-930 alignment verified: model-vs-actual demand
correlation peaks at lag 0 (0.9997 vs 0.986 at ±1 h).

## 2. The central table (full rows in the committed JSON)

| h | mo | hod | actual | model | meas. RTOLCAP pctl | meas. RTORPA | model room pctl | model ORDC dual | drivers fired |
|---|---|----|--------|-------|--------------------|--------------|-----------------|-----------------|---------------|
| 2058 | 3 | 18 | 742 | 76 | 0.4 | 27.5 | 1.0 | 25.68 | outage (p99.2) |
| 2971 | 5 | 19 | 686 | 35 | 0.1 | 223.6 | 2.3 | 2.51 | ramp |
| 4578 | 7 | 18 | 2014 | 175 | 3.7 | 4.3 | 1.1 | 8.55 | — |
| 4623 | 7 | 15 | 625 | 50 | 16.0 | 0.0 | 5.0 | 0.00 | — |
| 4626 | 7 | 18 | 595 | 58 | 17.1 | 0.0 | 5.0 | 0.01 | — |
| 5369 | 8 | 17 | 676 | 78 | 16.3 | 0.1 | 2.8 | 0.15 | — |
| 5484 | 8 | 12 | 550 | 167 | 9.1 | 1.1 | 2.4 | 0.65 | ramp (p100) |
| 5777 | 8 | 17 | 539 | 92 | 4.9 | 6.7 | 0.9 | 8.55 | — |
| 5943 | 9 | 15 | 537 | 65 | 10.1 | 0.0 | 3.1 | 0.07 | — |
| 5945 | 9 | 17 | 843 | 125 | 10.4 | 0.4 | 2.4 | 0.31 | — |
| 6399 | 9 | 15 | 590 | 77 | 7.2 | 0.7 | 1.4 | 1.30 | netload_gap:wind (2.6 GW) |
| 7001 | 10 | 17 | 696 | 44 | 10.7 | 0.3 | 15.3 | 0.31 | ramp (p95.6) |
| 7145 | 10 | 17 | 650 | 39 | 11.1 | 0.0 | 91.9 | 0.00 | netload_gap:wind (1.8 GW) |
| 7480 | 11 | 16 | 607 | 43 | 12.4 | 0.2 | 1.9 | 0.31 | ramp (p96.1) |

Reading: measured `system_lambda` reproduces the print in every row
(e.g. h4578 λ = 2008.14 vs RT 2014.26), so the events are SCED energy-side.
The model's withheld-family ORDC steps fire in 3 hours (h2058/h4578 at
$833.33 = VOLL/6 on three-to-four families; h5777 at $416.67 = VOLL/12 on
all four) — the sidecar `reserve_price` reaches $1,675–$3,342 there — but
that cross-family sum is the AS-price record, not a component of the scored
energy price, and the ercot-212 anatomy of that seam stands unrevisited.
Room-level caveat: model `held` and RTOLCAP are different boundaries
(the ercot-212 crosswalk: credits ride on the caps; B_model↔RTOLCAP corr
0.18 in-year), so the table compares each series to its OWN distribution;
the `model_minus_measured_room` column in the JSON is reported but not
leaned on.

## 3. Prior grading (declared ex ante, graded as declared)

* **P1 REFUTED** (informative direction): every hour carries positive
  ORDC-room shortfall (184–3,555 MW); family duals exceed $5 in 4 hours
  (three at ORDC steps). The misses are NOT "far from scarcity" — the
  model's room ranking places 12/14 in its bottom 5 %.
* **P2 REFUTED as declared:** 4/14 ramp hours (declared ≥ 8). Ramp
  percentiles are elevated family-wide (median ~p80) but only 4 clear
  p90-of-month.
* **P3 CONFIRMED:** 0/14 tie-export hours (declared ≤ 3); ERCOT imported
  111–873 MW in every event hour (CEN/CFE/SWPP detail in the JSON).
* **P4 REFUTED as declared:** 2/14 hours at ≥ 1.5 GW net-load gap
  (declared ≥ 5) — both wind-led (h6399 2.6 GW, h7145 1.8 GW), the only
  two clean net-load-representation misses in the family.
* **P5 REFUTED:** 2/11 non-August members in ≥ p75 overlay-outage windows
  (h2058 p99.2, h7480 p83.6; declared ≥ 5). Event days outside March are
  mostly LOW-outage days (p2–p19) — the outage overlay is not the object.

## 4. What the family IS (three sub-populations, measured)

1. **The conduct core (11 h):** tight-room hours (measured p0.1–p17, model
   ≤ p5) where reality's offer stack priced $537–$2,014 while both ORDC
   curves priced ≈ 0 and the model's offer surface was mid-merit
   ($35–$175). The k=33 carve-out lift reaches the August scarcity core;
   these hours are the SAME conduct phenomenon off-core
   (Mar/May/Jul/Sep/Oct/Nov + off-core August). This is hour-grain
   confirmation of the ercot-217 adjudication ("the remaining 2023 gap is
   the adjudicated conduct/model-class episode object") — with the new
   fact that the model's own reserve room already IDENTIFIES the hours.
2. **The two wind misses (h6399, h7145):** model wind exceeds actual by
   1.8–2.6 GW net-load-gap-led; h7145 is the family's only hour the model
   room does NOT rank tight (p91.9) — a pure renewable-representation
   miss, not conduct.
3. **h2058 (March, outage season):** the one hour where the availability
   prior holds — overlay outages at p99.2 (24 GW), model thermal at p98.7
   of month, three family steps binding. The model was AT its stack top
   and still $76: conduct again, compounded by outage season.

Supporting systematic: the +651…+873 MW event-hour demand gap (12/14 hours
vs +98 MW year mean) — the model's demand input understates real demand in
exactly these hours; ~0.7–0.9 GW of the tightness reality priced is absent
from the model's energy balance before conduct even enters.

## 5. What this round rules OUT (and what stays closed)

* NOT an overlay-completeness gap: the armed measured RTORDPA overlay is
  correctly ≈ $0 here (its 988 non-zero hours lie elsewhere); RTOFFPA
  stays out-of-basis (ercot-203, adjudicated, untouched).
* NOT the ORDC/adder channel: the REAL ORDC also priced ≈ 0 at these room
  levels — a steeper model ORDC would diverge from the measured design,
  and the ercot-212 net-credits leg on this channel is already
  REJECTED-AS-ARMED (G-SPUR kill). Nothing here re-opens it.
* NOT the outage overlay (P5 refuted), NOT tie flows (P3: importing), NOT
  a ramp family as a class (P2 refuted at threshold; the perfect-foresight
  LP's structural inability to price ramps remains real but explains at
  most the 4 ramp-flagged hours).

## 6. Named candidate objects (NOT chartered — owner-visible queue)

1. **The off-core conduct object (11 + h2058 hours):** the energy offer
   surface's tightness-responsiveness outside the August core. Any lever
   is a NEW precommitted, owner-visible round, and sits under the
   ercot-217 adjudication (conduct/model-class episode; NO admissible
   regime lever was found there). If the owner wants it worked, the
   admissible direction rule-13-wise is a MEASURED conduct
   parameterization (e.g. 60-Day SCED offer-curve dependence on reserve
   room / net load, from the `data/raw/ERCOT/SCED-CT` corpus), never a
   band-targeted lift; the DO-NOT-REDO surface variants
   (`ercot_offer_surface_lowcurve*`, negative-offer variants) stay closed.
2. **The event-hour demand gap (+0.7–0.9 GW in 12/14):** bounded,
   enumerable, measured against EIA-930; candidate root causes worth one
   zero-solve pass (4CP/load-resource response in the demand source,
   EIA-930-vs-MIS boundary, weather-hour alignment) before any input
   change.
3. **The two wind hours (h6399, h7145):** single-hour renewable CF
   over-credit; smallest object, possibly foldable into the standing
   renewables-representation lane.

**Disposition:** characterization complete, zero solves, nothing armed,
keeper structure untouched, kills K-1..K-3 honoured. Deliverables: the
committed probe + JSON + this FINDING + the calibration-log entry. The
queue above goes to the owner; the session continues to the handoff's
priority-2 object (the August steepness) as a separate precommitted round.
