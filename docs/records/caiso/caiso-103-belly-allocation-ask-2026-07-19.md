# CAISO-103 owner ask — the belly ALLOCATION mechanism (volume-holding, margin-re-pricing): design + authorization request

**Status: PENDING owner ruling.** No mechanism LP has been built or solved
(charter discipline: the caiso-102 §7 re-charter is owner-gated BEFORE any
solve). Everything below is measured from committed data
(`scripts/probes/_caiso103_alloc_stats.py`, NEW this session) plus the
FINDING-caiso102 channel measurements; the design statistics are in
FINDING-caiso103 §1-§2.

## 1. The problem the mechanism must solve

Post-hourfix keeper (`2026-07-19-caiso-102-hourfix`) ladder: belly
+6.0/+6.6/+4.3 $/MWh (2023/24/25). The caiso-100/101/102 arc established:

- The measured fleet's charge **volume is fixed upstream of the RT margin**:
  the DAM allocates 76-84 % of realized charge (belly windows 82-91 %), the
  FMM covers 94-97 %, RT additions are reg-down-deployment conduct
  (FINDING-caiso102 §1-§3).
- A **marginal-cost bid cannot carry the correction**: the derived $14.25
  cycling adder moved the belly λ exactly as predicted but was REJECTED on
  the pre-registered two-sided throughput gates — the real fleet buys its
  volume DESPITE a revealed $11-17 conduct cost (caiso-101 arc 1, the
  volume-refuted family; NOT re-proposed here).
- The LP's remaining defect is **allocation geometry at a price the market
  doesn't pay**: the keeper charges 9.37 TWh in the 2025 belly vs 8.26
  measured (RTD basis) at a charge-weighted λ $5.8-12.2 above reality's
  glut floor, while missing the non-belly conduct charge (overnight second
  cycle: model 0.05 vs 0.36 TWh; the morning gap mostly closed by the
  hourfix). In the single-market LP the battery's charge bid IS elastic
  high-value demand, so belly λ is propped at the fleet's arbitrage value;
  in reality the DA-allocated schedule is price-inelastic in RT and belly
  RT λ falls to the renewable-glut floor.

"Hold the volume, re-price the margin" therefore means: make the intra-day
charge allocation follow the measured DAM-allocation conduct so the hour-level
charge decision stops bidding the belly up, while the charge VOLUME decision
stays endogenous (nothing new pushes volume up or down — the property whose
violation killed the adder).

## 2. New measurements this session (the design statistics)

`_caiso103_alloc_stats.py` on the committed Daily Energy Storage Report
(LESR, IFM layer), EIA-860 monthly fleet basis (the caiso-99 envelope's exact
denominator):

- **(A) The fleet-normalized DA-allocation shape is fleet-size-invariant.**
  Mean IFM charge rate by hod, ÷ monthly fleet MW: pairwise cross-year
  r = 0.998/0.994/0.996 while the fleet grew 4.4 → 15.4 GW (3.5×); per-hod
  CV ≤ 0.15 through the whole core support (hod 8-15), ≤ 0.30 in the
  overnight shoulder. Strongest possible rule-13 stability evidence — the
  same class of forward story as the caiso-99 p95 envelope (shape × future
  fleet), with materially better cross-year stability than the envelope's
  own derivation showed.
- **(A) hod-share of annual IFM charge** (2025): overnight ramp hod 2-3
  ~1.2-1.5 % each, morning hod 8/9 = 6.2/10.4 %, belly hod 10-14 =
  13.9/15.9/16.3/14.7/11.0 %, pm-shoulder hod 15/16 = 4.7/1.7 %, evening ≈ 0.
  2023/2024 within ~1 pp per hod.
- **(B) Window share of daily IFM charge** (p25/p50/p75 across days, 2025):
  overnight .003/.024/.055, morning .076/.142/.250, belly .663/.726/.786,
  pm-shoulder .010/.041/.097, evening/late ≡ 0.
- **(C) SOC trajectory**: RTD SOC hod-mean ÷ fleet MWh: trough at hod 7
  (0.28/0.19/0.12), peak hod 15-16 (0.79/0.78/0.77); the normalized trough
  DEEPENS as the fleet grows (the AS/positioning floor does not scale with
  fleet energy).
- **(D) The overnight second cycle does NOT fleet-scale**: RTD overnight
  charge 0.334/0.360/0.357 TWh — flat in absolute terms across a 3.5× fleet
  (per fleet-MWh it falls 0.049 → 0.031 → 0.022), and it is DA-scheduled
  (IFM overnight ≈ RTD overnight in every year).
- **(E) The RD book also does not fleet-scale** (per-MW belly-window RD
  award 0.17 → 0.12 → 0.09): the reg-down requirement is system-sized, not
  fleet-sized.

## 3. Candidate mechanisms (the charter's three shapes, adjudicated on the measurements)

### M1 (RECOMMENDED) — DA-allocation-profile charge schedule

The caiso-99 envelope's conduct sibling: where the envelope caps the fleet's
hourly RATE (capability), the schedule constrains the intra-day ALLOCATION
(conduct), with a bounded free slice for the RT margin the LP legitimately
prices.

Per solve-day `d`, one new scheduled-volume variable `S[d] >= 0`, and for the
fleet battery charge `Chg[h,d]` (sum over battery units, PS excluded):

```
Chg[h,d]  >=  alloc_share[hod(h)] × S[d]          (24 floor rows / day)
Sum_h Chg[h,d]  <=  S[d] / da_frac                (1 cap row / day)
```

with `alloc_share[·]` the measured hod-share of annual IFM charge (Σ = 1,
statistic (A)) and `da_frac` the measured DA-share of realized charge
(0.840/0.799/0.760 — FINDING-caiso102 §1). Equivalently: every charged MWh
buys the measured allocation BUNDLE across the day's shape, except a free
slice bounded to the measured RT-margin share (16-24 %) which the LP may
still place at will (mirroring the real RT re-timing). ~9.1k sparse rows +
365 variables per year; no integer variables; composes with the caiso-99
envelope as `share×S ≤ Chg ≤ env_p95×fleet` (the schedule allocates INSIDE
the capability cap — one mechanism per phenomenon, rule 19: envelope =
capability, schedule = allocation; the adder family = economics, stays out).

- **Volume-holding by construction**: `S[d]` and the day total are
  endogenous; a zero-charge day stays feasible (S=0 forces nothing). No new
  cost or credit enters the objective — the charge-volume economics are
  byte-identical to the keeper's. The caiso-100 failure mode (volume
  collapse) is structurally excluded.
- **Margin re-pricing**: the hour-grain charge variable is no longer free to
  concentrate at the belly floor-hours' margin; the marginal stored MWh
  prices at the shape-weighted day bundle, so belly λ decouples from the
  battery's arbitrage value — exactly the DAM/RT split the measured channels
  show (the LP keeps pricing only the 16-24 % the real RT margin re-times).
- **Rule 12**: driver = the measured DAM allocation conduct (IFM schedules
  76-84 % of realized charge; FINDING-caiso102 §1). Window = every day's
  charge-shape support (hod 1-17; evening/late shares are measured ≈ 0, so
  the floor forces nothing there by construction). Forward story =
  `alloc_share × S` regenerates for any forward year (shape is
  fleet-invariant, r ≥ 0.994 across 3.5× growth; volume endogenous);
  `da_frac` carries the latest measured year forward (or its mild 0.84→0.76
  maturity trend — owner sub-choice, see §5). Responds to changed
  conditions: more solar/bigger fleet → bigger endogenous S; the shape is
  conduct, exactly as the envelope's p95 is.
- **Rule 13 admissibility**: same construction class as the caiso-99
  envelope (measured per-MW conduct statistic × model-endogenous scale). No
  actual hourly series enters any constraint; nothing pins model output to
  a measured outcome (the model remains free to charge nothing, or twice
  reality, on any day).
- **D-2/C8**: charge-side allocation floors create no generation and no
  merchant-class forced energy — C8 untouched by construction. New D-2
  mechanism id (`storage_alloc_schedule`) with a D4_WINDOWS entry (its
  declared window = the measured shape support); binding hours and forced
  MWh (share×S vs unconstrained counterfactual) reported in
  `legitimacy_diagnostics.json`.
- **DOF ledger delta**: 24 shape values + 1 `da_frac` per year — ALL
  measured statistics from one committed source (storage report IFM layer),
  zero residual-fitted values; quantile/statistic choices fixed a priori
  (mean-share shape, annual grain — the envelope precedent). Identification
  source: `scripts/derive_caiso_charge_allocation.py` (new rule-23 derive,
  to be written on grant).

Known limitation (disclosed): the annual-hod grain ignores seasonal shape
drift (winter mornings vs summer bellies). The (B) day-share IQRs show the
day-to-day dispersion is real; the schedule's free slice absorbs part of it.
A month×hod refinement (288 values) is measurable from the same source if
the annual-grain B-leg under-delivers — NOT proposed for v1 (parameter
parsimony; envelope precedent is annual).

### M2 (fallback) — window-share bands (inequality-only variant)

Per day, window-grain share bands `share_lo_w × Daily ≤ Chg_w ≤ share_hi_w ×
Daily` from the measured day-share quantiles (B). Weaker: with bands at
reality's own p25/p75, reality's day distribution violates its own IQR half
the time by construction — the honest outer band (p05/p95) rarely binds and
moves little; and within-window hour choice keeps the belly margin
battery-priced. Kept on the menu only if the owner prefers zero equality
structure; the measured statistic is already committed either way.

### M3 (measured, DEFERRED) — AS-obligation SOC term (the overnight second cycle)

The only channel that can create the missing overnight charge (model 0.05 vs
0.36 TWh) — but the measurements argue AGAINST building it now: the second
cycle does NOT fleet-scale (statistic D: flat ~0.35 TWh absolute, per-MWh
falling 3×), so a shape×fleet construction would overbuild it in every
forward year (and the RD book it tracks is system-sized, statistic E — its
forward driver is the AS requirement, not the fleet). It also overlaps the
frozen-off `caiso_storage_as_reservation` family (rule 19 conflict to
resolve first), and its λ target is small (overnight resid +0.8/−0.0/+1.4;
0.3 TWh at $38-58). Recorded as a non-target of M1 (M1's overnight floor
share is the measured IFM overnight share ~2-6 %, which partially covers it);
re-charter only if the post-M1 overnight residual grows.

## 4. Interactions (the charter's named list)

- **caiso-76** (battery adder no-change ruling) / **caiso-100/101** (derived
  $14.25 REJECTED on volume gates): M1 adds NO cost term — the ruling and the
  rejection are untouched. The effective $5 fallback adder (issue #2546,
  honestly recorded since caiso-101) stays as-is pending that issue's own
  disposition. M1 is deliberately orthogonal: if a future owner ruling
  revisits the cost question, the composition (schedule holds volume, cost
  prices margin) is a NEW ask with the caiso-100 volume gates re-registered.
- **caiso-99 envelope**: composes, not stacks (capability cap vs allocation);
  the envelope is NOT tightened (frozen per the caiso-102 handoff).
- **caiso_storage_as_reservation**: stays off (M3 deferred).
- **caiso-87/97 import mechanisms, WP-3 steam level**: no interaction (charge
  side only).

## 5. THE ASK

1. **Authorize M1**: the rule-23 derive
   (`scripts/derive_caiso_charge_allocation.py` →
   `data/raw/reference/caiso-charge-allocation-profile.csv`: per-year
   24-value `alloc_share` + `da_frac`, from the storage-report IFM layer),
   the `ScenarioConfig.caiso_charge_allocation_schedule` gate (default off),
   the dispatch.py constraint rows above, and ONE single-delta B-leg
   (keeper recipe + the gate, 2023-2025 one bundle, sequential) against the
   same-machine `caiso102_repro_A` baseline — with gates pre-registered in a
   FINDING §6-style block BEFORE the solve (drafted: belly λ falls all three
   years, no overshoot; annual + belly charge volume within a tight band of
   the A-leg (the volume-holding property is the mechanism's own claim — a
   volume move > 5 % fails it); evening λ must not regress deeper; overnight
   λ no new under-price; C1 12/12, C7/C8 PASS; C5a no regression; binding
   share and forced-MWh reported via D-2). Registered whatever the result
   (rule 15); promotion on no-status-regression, owner call.
2. **Sub-choice on `da_frac` forward semantics** (only if 1 granted):
   latest-measured-year carry (envelope precedent, recommended) vs the
   0.84→0.76 trend endpoint.
3. **M3 disposition**: ratify DEFERRED with the fleet-scaling evidence (D/E),
   or re-charter it despite it.
4. If M1 is REFUSED: the belly residual re-charter needs a new hypothesis
   family — the measured channels are now exhausted at the allocation layer
   (bid-cost refuted by volume, allocation is the remaining conduct surface).

**Sequencing note:** the B-leg solves only after this ask is ruled; nothing
in the priority-2 evening lane depends on it (separate mechanism surface).
