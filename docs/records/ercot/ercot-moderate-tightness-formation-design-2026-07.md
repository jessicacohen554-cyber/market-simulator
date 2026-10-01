# ERCOT-86 (design/feasibility) — the moderate-tightness ($150–500 middle) formation mechanism

**Status: DESIGN + FEASIBILITY ONLY. No solve, no registration, keeper UNCHANGED
(`2026-07-18-ercot82-measured-rtolcap`).** This charter converts the gap that the
ercot85 measured-availability re-architecture *exposed* into a named, admissible,
buildable mechanism — and states exactly where it is buildable now vs owner-gated.

## 0. One-line answer

The mechanism that forms the $150–500 middle **already exists in the codebase** —
`ercot_offer_surface_cleared_share` floors the above-boundary CC/CT `econ*`
tranches at a measured, net-load-binned offer wall. It cannot form the mid-band
because its **data basis is the 60-Day *DAM* disclosure**, whose above-boundary
offers are measured *cheap* ($25–47, ERCOT-84 Finding 1); the real $150–800
mid-band cleared on **RT/SCED** offers of the online spare, a surface the DAM
disclosure genuinely does not contain. **The build is a RT/SCED-basis variant of
the wall's ladder — same apply seam, same net-load conditioning, zero fitted
scalars, just the correct offer surface.** It is buildable for **2024** (solid),
thin for **2025** (needs tail-day SCED), and **blocked for 2023** (SCED
permanently unreachable on the free path *and* a distinct market regime — the
one genuine owner decision).

## 1. The gap ercot85 exposed (the target)

ercot85 (`ercot_thermal_dam_availability=true`, `wefor_residual=0.02`) replaced the
statistical WEFOR over-derate with measured DAM class-day availability. Effect on
the moderate-tightness lane (handoff record, not re-solved this session):

* **The empty $150–500 middle persists in ALL years** — 0–1 model hours vs 60–73
  actual. The model climbs its offer stack to ~$40 at moderate net load, then
  jumps to the ORDC/VOLL scarcity cliff in genuinely-tight hours, forming
  essentially nothing in the $150–500 band.
* **2024 / 2025 annual LEVELS are already excellent** on the measured-availability
  base (resid −2.75 / −0.90). Their residual gap is **middle-band SHAPE**
  (C3b/C3c band occupancy), not level.
* **2023 summer COLLAPSES** (Aug −108, Sep −46 → annual −18.5). This is a **LEVEL**
  collapse: 2023 rode the statistical over-derate for its summer tightness; with
  the phantom removed, the still-missing moderate-tightness formation is
  un-hidden and the level falls out from under 2023 summer. Per rules 1/11 this is
  a *discovered bug*, not a reason to revert measured availability.

So the target splits by regime:
| regime | year(s) | residual character | target |
|---|---|---|---|
| current-design | 2024, 2025 | level OK, mid-band SHAPE empty | fill $150–500 occupancy without over-lifting the (good) annual level |
| conservative-ops | 2023 | LEVEL collapse (summer) | form the 2023 summer mid-band — offer-basis-blocked |

## 2. Why the resident mechanisms don't form it (enumerated, so we don't re-tread)

1. **DA-expressible offer/AS formation — REFUTED (ERCOT-69).** The model's gas
   offers already *exceed* measured DAM at every within-plant share and net-load
   bin, so a `max(0, measured − model)` DAM floor bites almost nothing on the
   classes it can touch, and where it bites it lands in the wrong (winter-tight)
   hours. The resident ORDC reserve-demand curve is the published RTC+B ASDC and
   over-corrects when forced. "The gap is which units clear, not what they offer"
   — *at the DAM level*.
2. **Supply-mix (phantom cheap capacity) — largely HANDLED (ERCOT-70/71 + ercot85).**
   ERCOT-70 named +1.2–1.7 GW phantom CC_REGULAR in four CAMPD-invisible plants
   (Kiamichi/Hidalgo/Arthur Von Rosenberg/EG178) carrying flat statistical
   availability. The keeper now runs `ercot_noncampd_plant_availability=True`
   (ERCOT-71 per-plant DAM-disclosure availability for the blind plants) **and**
   ercot85 adds measured DAM class-day availability for the covered gas classes.
   The cheap-availability half of the supply-mix residual is therefore
   substantially retired — which is *why* ercot85 eliminated the April-2024
   over-formation. What remains is not "too much cheap capacity available" but
   "the available marginal capacity is priced too low."
3. **The cleared-share wall EXISTS but is DAM-basis (the actual root cause).**
   `ercot_offer_surface_cleared_share` (+`_state`) is ON in the keeper. It floors
   each merchant gas `econ*` tranche above the net-load bin's measured cleared
   boundary, at the bin's measured **DAM offered-but-uncleared** price ladder
   (`scripts/data/derive_ercot_dam_cleared_share.py`, reading
   `*60d_DAM_Gen_Resource_Data_*`). ERCOT-84 Finding 1 measured that ladder
   directly over the Aug-2023 mid-band window: the *entire* submitted DAM curve
   mass prices $13–44 (q97 $44); the $150–800 marginal offers that formed the
   real λ were **real-time (SCED)** offers of the ~3 GW online spare beyond the
   nonreleasable AS carve-out. A DAM-basis wall is therefore *measured cheap* and
   cheap CC routes straight through it — exactly the handoff's symptom.

**Conclusion:** the correct apply-seam, class scope, net-load conditioning and
rule-19 ownership are all already built and validated in the cleared-share wall.
The single wrong ingredient is the **offer surface feeding the wall ladder** — DAM,
where it must be RT/SCED.

## 3. The buildable mechanism — a RT/SCED-basis cleared-share wall (2024/2025)

This is the ERCOT-84 Finding 3 charter made concrete. It is a **data-basis
correction of an existing mechanism**, not a new stacked floor (rule 19-clean).

### 3.1 Derive (frozen artifact, rule 23)
`scripts/data/derive_ercot_sced_offer_wall.py` (new), reading the on-disk 60-Day
**SCED** Gen Resource Data sample days (`*60d_SCED_Gen_Resource_Data_*`):

* For each SCED interval, per merchant gas class (CCGT90/CCLE90→CC_REGULAR,
  SCGT90/SCLE90→CT_PEAKER; ST_GAS excluded — rule 19, owned by the drag), segment
  the **energy-dispatchable online spare** offer curve between **Base Point → HASL**
  (net of AS responsibility; the exact construction in
  `scripts/probes/_ercot84_sced_spare_offers.py`, promoted from probe to derive).
* Bin each interval by its **within-year net-load percentile** (join EIA-930 net
  load; reuse the cleared-share derive's binning at edges 0.80/0.90/0.97 so the
  RT wall shares the DAM wall's bin geometry).
* Emit, per (class × net-load bin), **capacity-weighted quantiles** of the spare
  segments' price-as-effective-HR-multiplier ladder →
  `data/raw/_validation-source/ercot_sced_offer_wall_condbinned.json` (its own
  artifact; the DAM `ercot_dam_cleared_share_condbinned.json` stays byte-stable).
* Frozen against residuals (rule 23): re-derives only when the SCED source updates.

### 3.2 Apply (P1-only, the existing seam)
Reuse `build_ercot_offer_surface_cleared_share_markup`'s wall path with the RT
ladder selected by a new gate. Two admissible compositions to A/B:
* **(A) replace** the DAM ladder with the RT ladder for the same above-boundary
  rows (cleanest — one wall, correct basis); or
* **(B) a disjoint RT tier** above the DAM wall's reach (rows the DAM wall leaves
  at/below its cheap ceiling get the RT ladder). (A) is preferred unless the A/B
  shows the DAM boundary itself is mis-placed.

Same guarantees as the DAM wall: floor only ever RAISES a bid, capped below
`price_cap_frac × VOLL`, targets CC_REGULAR/CT_PEAKER `econ*` rows only (PEAK rungs
stay `ercot_offer_surface_conditional`'s; committed/mustrun blocks the bridge's;
ST_GAS the drag's — rule 19), P0 run lengths and startup coupling byte-identical.

### 3.3 Config
`ercot_offer_surface_cleared_share_rt: bool = False` (+ `_rt_path: str | None = None`),
ERCOT-gated, mutually exclusive with the DAM wall under composition (A) (hard
error, like the midcurve/cleared-share exclusion). On-registry per rule 24, zero
fitted scalars per rules 13/20/26 (trigger = within-year net-load percentile,
forward-native; levels = measured SCED quantiles; frozen).

### 3.4 Admissibility (rule 13)
The SCED spare offer ladder is a **measured, physics/market-grounded input with a
forward analogue**: it is the RT supply curve of the online spare, regenerable for
a forward year from the forward fleet's offer posture and responsive to changed
conditions (a tighter forward year climbs higher up the *same* measured ladder).
It is **not** an outcome pin — the wall never references the price it forms; it
raises *offers*, and the LP still decides whether the dual reaches them. This is
the same admissibility class as the adopted top-of-curve conditional surface, one
tier lower on the merit order.

### 3.5 Tests
`tests/test_ercot_offer_surface_cleared_share_rt.py`: RT ladder ≥ DAM ladder in the
mid-band bins; floor monotonic & VOLL-capped; ST_GAS/coal/CHP untouched; mutual
exclusion error; byte-identity of the DAM artifact.

## 4. Feasibility — SCED data on disk (the hard constraint)

On-disk 60-Day SCED Gen Resource Data is **scoped sample days**, not full-year:

| year | files | days | months covered | tail (scarcity) days? |
|---|---|---|---|---|
| 2024 | ercot74 tail + ercot75 control | 47 | Feb–Dec (all) | **YES** (ercot74) |
| 2025 | ercot75 control only | 24 | Jan–Dec (all) | **NO** (control only) |
| 2023 | — | 0 | — | unreachable (free-path retention ~2.3 yr; earliest ~2024-01) |

* **2024 — BUILDABLE.** 47 days × 288 intervals ≈ 13.5k intervals, stratified to
  *populate* the high net-load bins (tail days) that carry the mid-band exactly
  where the surface is conditioned — arguably ideal for a net-load-binned wall.
* **2025 — THIN.** Control days only; the high-net-load / scarcity bins are
  under-sampled. Options: (i) a small **2025 tail-day SCED intake** (the ercot74
  scoped-day pattern, free-path reachable for 2025), or (ii) borrow 2024's
  high-bin ladder shape within the same current-design regime (defensible but a
  regime-transfer assumption to disclose). Recommend (i) — cheap, in-regime, honest.
* **2023 — BLOCKED (see §5).**

## 5. The 2023 blocker — the one genuine owner decision

The 2023 summer collapse (the sharpest exposure, annual −18.5) **cannot be formed
at the offer level from any on-disk or free-path data**, for two independent reasons:

1. **Provenance.** 2023 SCED Gen Resource Data is permanently unreachable on the
   free path (ERCOT-84 Finding 2); the credentialed api.ercot.com / data.ercot.com
   archive is owner-declined-to-date. Rule 13 forbids reconstructing the 2023 RT
   offers from the price they formed.
2. **Regime.** 2023 was the post-Uri **conservative-operations** regime — high RT
   offers on the online spare — whereas 2024/2025 shifted to a competitive,
   near-exhaustion-shaped tail (ERCOT-84 Finding 3). A 2024/2025-derived RT wall
   **must NOT be applied to 2023** (rule 13: wrong-regime input, and it would be a
   surface tuned outside 2023 papering 2023's collapse). The RT wall is therefore
   *year-scoped to its own derive years*.

**Owner decision (pick one):**
* **(a) Authorize a scoped credentialed 2023 SCED intake** — Jun–Sep 2023 tail-day
  clusters (the ERCOT-74 scoped-day pattern) would suffice to derive the 2023 RT
  wall and form the summer collapse honestly. This is the ERCOT-84 Finding 2 filed
  owner ask. (Data intake under rule 22 quarantine clauses: 2023 is a *training*
  year, so no holdout issue; the ask is the credentialed-source authorization.)
* **(b) Accept the 2023 mid-band as a documented measured-representation-limit
  CAVEAT** — the price-forming input (2023 RT offers) is unobtainable on the
  authorized data path; the 2023 summer under-price is ledgered as an input-blocked
  limitation, not a model defect, and the RT wall ships for 2024/2025 only.

## 6. Recommended path

1. **Build the RT wall for 2024 first** (data solid), A/B composition (A) vs (B) on
   the ercot85 measured-availability base — single-year 2024 rule-16 throwaway
   probe. Success criterion: the $150–500 band fills toward the ~60–73 actual hours
   **without** over-lifting the (already-good) 2024 annual level (guard C3a). If the
   mid-band fills but C3a over-corrects, the wall's cap/boundary is the knob to
   re-examine — never a fitted scalar.
2. **If 2024 clears**, resolve 2025 coverage (§4 option (i): small 2025 tail-day
   SCED intake) and extend, then full-span 2024+2025 with LOYO (rule 22) before any
   promotion talk.
3. **2023** proceeds only on owner decision §5 — (a) unblocks a full-span
   2023+2024+2025 keeper; (b) ships 2024/2025 and ledgers 2023.
4. Keeper stays ercot82 throughout (rule 27, owner-only swap). ercot85 remains the
   structural-record probe.

## 7. Rule ledger

* **Rule 1/11** — measured availability (ercot85) stays in; the 2023 collapse is a
  discovered bug this charter addresses, not a revert trigger.
* **Rule 13** — RT wall is a measured forward-native input; year-scoped to its
  derive years; no outcome pin; 2024/2025 wall barred from 2023.
* **Rule 19** — data-basis correction of the existing cleared-share wall, not a new
  floor; class scope disjoint from conditional (peak), bridge (committed), drag
  (ST_GAS), take-or-pay (coal). Composition (A) is mutually exclusive with the DAM
  wall (hard error).
* **Rule 20/24/26** — on-registry config, zero fitted scalars, frozen artifact,
  deleted-means-deleted (no re-armable knob).
* **Rule 22** — 2024/2025 are training years (no holdout issue); the 2023 SCED
  intake is a credentialed-source authorization, not a holdout solve.
* **Rule 23** — derive frozen against residuals; re-derives only on SCED source update.

## 8. Deliverables of this design session

This document; no code, no solve, no registration, keeper unchanged. The build
(`derive_ercot_sced_offer_wall.py` + the `_rt` gate + tests) is chartered, not
started, pending owner go-ahead on §6 step 1 and the §5 2023 decision.

## 9. BUILD + 2024 A/B PROBE RESULTS (session 2026-07-19, ercot86)

§6 step 1 executed. Built (branch `claude/ercot-86-rt-wall-nrxeun`): the §3.1
derive (`scripts/data/derive_ercot_sced_offer_wall.py`, frozen rule 23, DAM bin
geometry imported so agreement holds by construction, per-bin coverage
disclosed in provenance), the 2024 artifact
(`data/raw/_validation-source/ercot_sced_offer_wall_condbinned.json`, 47 sample
days, no pooled fallback, no ST block; DAM artifact byte-stable), the §3.2/3.3
apply gate (`ercot_offer_surface_cleared_share_rt` + `_rt_path` + `_rt_mode`,
both compositions; the RT leg is **never state-weighted** — the SCED spare is
measured on the online fleet, so the ERCOT-73 commitment-state correction is
already conditioned into the surface, and weighting it again would
double-count), and the §3.5 tests (13, all green; existing wall suite green).

**Measured surface (2024).** The thesis held in the data: the CT online-spare's
upper rungs carry the RT surface the DAM lacks (q90 effective-HR multipliers
217–1289 in the p50–p90 bins vs DAM's 25–42 → $540–3,200 at 2024 gas); CC caps
near multiplier 52 (≈$130–160 — the mitigated SCED2 ceiling). RT is NOT
uniformly ≥ DAM: the CC tight-bin DAM upper rungs (q90 196.9 in >p97) exceed
RT's (52.4) — the compositions handle this divergence honestly.

**Probe (rule 16 throwaway, NOT registered; slim bundles committed at
`results/calibration/ercot86_rtwall_2024_{A,B}`).** Single-year 2024 on the
ercot85 base (keeper + `ercot_thermal_dam_availability` + `wefor_residual=0.02`):

| metric (2024) | ercot85 base | A (replace) | B (tier) | actual |
|---|---|---|---|---|
| annual mean resid | −2.75 | **−0.34** | −0.32 | — |
| $150–500 hrs | ~0–1 | **13** | 13 | 68 |
| $500–2k hrs | (unrec.) | 2 | 2 | 13 |
| $2k+ hrs | (unrec.) | 3 | 3 | 3 |

* **C3a guard CLEARS**: the annual level moves −2.75 → −0.34, i.e. the wall
  *closes* level residual without over-lifting.
* **Partial mid-band formation, correctly placed**: 12 of the 13 model
  mid-band hours are the real Jan-15 winter event (model $172–238 vs actual
  $114–244); the 13th is Aug-19 h18 (model $230 vs actual $3,060 — an
  under-formation, not an over-). Zero spurious mid-band hours.
* **The remaining 55/68 hours are the spread-out shoulder/summer
  moderate-tightness hours** (Apr 11, May 11, Oct 6, Aug 6 actual hrs …). At
  actual mid-band hours the model now prices p50 $52 / p90 $128 — up from the
  ~$40 stack ceiling, but short of $150. Structure of the shortfall: the wall
  floors only ABOVE-boundary CC/CT econ rows, and in those hours the LP still
  finds un-walled supply (below-boundary rows, other classes) before the RT
  rungs; the CC ladder's mitigated-ceiling cap (~$130–160) sits below the
  band in exactly the bins where CC is the marginal walled class.
* **A ≈ B** (hourly |Δ| ≤ $1.60, 1,356 hrs differ, band occupancy identical):
  the RT ladder dominates the state-weighted DAM leg in every operative bin,
  so the tier composition adds nothing. **Composition A (replace) is the
  recommended form** — cleaner ownership (one ladder source per bin), same
  result.

**Verdict.** The mechanism is structurally validated — it forms the mid-band
where the supply stack genuinely exhausts, prices the formed hours in-band,
and repairs the annual level as a side effect — but the measured online-spare
wall alone under-fills the band ~5×. The un-formed remainder is consistent
with the charter's own scope note: the RT wall prices the *online spare*; the
spread-out mid-band hours in reality also involve offline-CT RT participation
(startup-inclusive offers) and the CC spare beyond the mitigated ceiling,
neither of which this surface contains. That residual formation gap is a NEW
named lane, not a knob on this one (rule 19 — no cap/boundary retune against
the residual).

**Open owner decisions (unchanged from §5/§6):** 2025 tail-day SCED intake
(§4 option i) before any 2024+2025 span; 2023 credentialed intake vs caveat
(§5). OOM note for successors: two concurrent ERCOT per-plant co-opt solves
exceed the 15 GB session container — run year-probes sequentially despite
rule 12's ~2-run allowance.

## 10. 2025 EXTENSION + FULL-SPAN CANDIDATE (session 2026-07-19b, ercot86-2025)

**Owner decisions resolved (this round).** (1) 2023 SCED is permanently
unreachable on the free path (retention ~2.3 yr) and the credentialed archive is
owner-declined → **§5 option (b) ADOPTED**: RT wall ships 2024/2025 only; the
2023 summer mid-band under-price is a documented **input-blocked
measured-representation caveat**, not a model defect. 2023 keeps the DAM basis
automatically (year-scoped artifact, rule 13) — nothing is retuned to paper it.
(2) 2025 tail days fetched free-path in-session.

**2025 tail-day SCED intake (task 1).** 11 RT-tail delivery days (Jan 15,
Feb 19/20, May 16/30, Jul 1/11/30, Oct 21, Dec 1/15 — RT>$200 clusters that land
in the p80/p90/p97 net-load bins), full-day, via `fetch_ercot_60day_sced_gen_resource.py`
→ `data/raw/ercot/…_2025_ercot86_tail_days.parquet` (66 MB, verified: no dup
(interval,resource) rows; 15-min publish cadence except Dec 15 at 5-min; all days
reachable). Re-derive `--years 2024 2025` (rule 23 source-data addition):
**2024 tables byte-identical** (input unchanged); 2025 tail bins now
**312/304/168 intervals** (was 172/144/40, control-only), each ≥10 sample days —
coverage adequate, no thin-bin caveat.

**2025 single-year probe A (rule-16 throwaway, NOT registered; slim record at
`results/calibration/ercot86_rtwall_2025_A`).** ercot85 base + RT wall
(composition A). Effective price = demand-weighted `price` column, which already
sums the co-opt energy dual + RTORPA overlay (this keeper carries **no** post-solve
`ordc_adder` — scarcity is endogenous in the co-opt; the generic "price+ordc_adder"
convention would double-count / mis-measure here).

| metric (2025) | ercot85 base | A (replace) | actual |
|---|---|---|---|
| annual mean resid | −0.90 | **+0.44** | — |
| $150–500 hrs | ~0–1 | **6** | 65 |
| $500–2k hrs | (unrec.) | 1 | 3 |
| model @ actual mid-band (p50/p90) | ~$40 ceiling | **$65 / $137** | — |

* **C3a guard CLEARS**: |resid| shrinks 0.90 → 0.44; the +$0.44/MWh sign-flip
  (1.4 % of the $32 mean) is within noise — the wall closes the level without
  material over-lift.
* **6 model mid-band hours, ALL correctly placed, ZERO spurious**: Feb 20 h6–7
  (winter morning, actual $188/$250) and Aug 20 h18–21 (summer evening, actual
  $104–175). No model >$150 hour where actual ≤$100.
* **Same partial-fill structure as 2024**: the wall lifts the model at genuine
  tight hours from the ~$40 stack ceiling to p50 $65 / p90 $137, crossing 6 of 65
  actual mid-band hours into the band; the remaining 59 (spread Apr/May/Jul/Dec
  shoulder) sit $50–120 — the same out-of-scope online-spare shortfall (offline-CT
  startup-inclusive RT participation + CC spare beyond the mitigated SCED2 ceiling),
  the §11 residual lane, not a knob here (rule 19).

**Verdict: 2025 CLEARS.** The mechanism generalizes — 2024 and 2025 both form the
mid-band where the stack genuinely exhausts, price the formed hours in-band, and
close the annual level as a side effect, with zero spurious hours. Because the wall
is derived independently per-year from that year's own measured SCED offers with
**zero fitted scalars**, each year's improvement is itself leave-one-year-out
evidence (no cross-year parameter sharing to overfit).

**Full-span candidate (task 4).** 2023+2024+2025 in one bundle
(`results/calibration/ercot86_rtwall_fullspan`), RT wall on; 2023 auto-retains the
DAM basis (year-scoped). Scored LOYO within 2023–2025, registered on the dashboard
with the 2023 input-blocked caveat in the run note. Keeper swap remains OWNER-ONLY
(rule 27) — ercot82 stays the keeper.
