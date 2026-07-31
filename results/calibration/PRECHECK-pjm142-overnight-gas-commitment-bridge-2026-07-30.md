# PRECHECK — pjm-142: the PJM overnight gas commitment bridge, killed or chartered BEFORE any mechanism code

**Status: pre-registered, committed BEFORE the measurement runs.** This document
states the pre-check's kill thresholds — in MW-at-the-margin, per the pjm-140
§4.1 all-ISO lesson ("pre-check a bound against the bound") — using **only
numbers already committed in
`FINDING-pjm141-overnight-marginal-tranche-is-correct-the-defect-is-a-flat-offer-stack-2026-07-30.md`**.
No probe output existed when these thresholds were fixed. The measurement is
`scripts/probes/_pjm141_overnight_tranche.py`'s new **T7** block (extending the
committed probe per the charter, not a new script), run on the keeper
`pjm140_rampenv_B`'s own fleet with **no LP**.

Charter: `docs/mechanism-testing-matrix.md` §5.3 item 13 (the ONE
non-adjudicated successor), `FINDING-pjm141` §8 lead 1. Matrix cell under test:
`gas_commitment_bridge` PJM (currently `U`, cells `KKUUKK` on E/C/P/M/N/Q).

## §1 — what the bridge would do, and what pjm-141 already refutes

A PJM overnight gas commitment bridge (the `nyiso_gas_commitment_bridge` form:
min-gen floors injected at the P0→P1 seam over gaps between P0-detected runs,
eligibility by unit physics per rule 18) would force merchant slow-start gas
plants that the economic dispatch cycles off overnight to hold at min-load
through h23–h06. In the tranche representation that dispatches their
`committed` rung (p05 $14.50) out of merit, displacing the marginal `econ`
rungs (p05 $16.58–20.35) — the right direction for the overnight half of the
flat-stack amplitude defect (+$6.82 / +$5.78 / +$3.40 too dear).

pjm-141 refutes half the premise ex ante:

* **T4**: overnight thermal volume already matches CAMPD to +0.9 / −2.0 /
  +2.5 % (CC ±1.4 %) — so forced MW must displace, not add;
* **T3**: the LP already loads `committed` preferentially — 28.79 of 36.24 GW
  in merit (79 %) vs `econ` 15.08 of 48.72 (31 %) — so the idle committed pool
  is at most ~7.5 GW across ALL classes before any eligibility gate.

The pre-check must therefore answer: **is the bridge-eligible idle committed
pool big enough to move the overnight clearing point materially, without
breaking a class-volume match that is already correct?**

## §2 — the measurement (T7, no LP)

On the keeper's own offers (`mc_base`), availability, and committed sidecar
prices, per year, at h01–h04 (evening peak h16–h18 carried as control):

1. **The pool `F_pool`.** Committed-tranche available MW of BRIDGE-ELIGIBLE
   plants — `fuel_type == "gas_cc"`, `min_down_hours ≥ 4` (the
   `CC_COMMITMENT_PARAMS` table's own floor, rule 18 `[R-PHYSICS]`; fast-start
   CTs with 1 h min-down are never overnight-bridged), CHP excluded (steam-host
   must-run, per all three existing bridges) — that is live (avail > 1 MW),
   NOT in merit in the overnight hour (own offer above the zone dual), and
   DAY-ANCHORED: the plant's committed rung in merit ≥ 1 h in h07–h22 on BOTH
   flanking calendar days (the no-LP proxy for "P0 runs on both sides of the
   gap", which is what the detector floors). Reported two ways and the
   **larger** taken as `F_pool` (lever-favorable): (a) the committed-tranche
   block itself; (b) 0.574 × plant available capacity — the largest measured
   min-load fraction any ISO's derivation has produced (ERCOT LSL/HSL p50; a
   PJM value would be derived from PJM conduct only if Step 2 fires, rule 25 —
   here it is only an upper-bound scan, also reported at 0.30 / 0.45).
2. **The price move `Δd(F)`.** Static merit-curve walk: per overnight hour,
   the system thermal supply curve (live offers sorted, cumulative available
   MW); current in-merit MW `M_h` (offers below the hour's dual); new dual
   `d′_h(F)` = the offer at cumulative `M_h − F_h`. Reported at `F_pool`, plus
   the inverse `F($1)` = MW needed for a $1.00/MWh mean move. The walk is
   **lever-favorable**: it holds demand, storage, interchange and the DA
   virtual layer fixed (an elastic response would buffer the drop), and the
   thermal-only curve omits the virtual INC rungs (3.2–3.4 % of the marginal
   set).
3. **The volume shift.** The displaced band `[d′_h, d_h)`'s class mix
   (CC/CT/ST families, capacity-weighted) → net family volume change at `F`:
   ΔCC = F − displaced_CC, ΔCT = −displaced_CT, ΔST = −displaced_ST. Compared
   against T4's current match.
4. **The clearing rung** at `d′` (tranche family + class): does `committed`
   actually take marginal ownership?
5. **Cross-check** (the 137.71-GW discipline): per-hour in-merit thermal MW
   vs the committed `class_hourly` P1 thermal MW at h01–h04, reported as a
   ratio — the walk's baseline must reproduce the keeper's own dispatched
   thermal to a few percent or the walk is invalid.
6. **Restart-economics screen** (secondary, informative): share of the pool
   whose 8-h overnight hold is cheaper than a restart under the standard
   inequality `startup_per_mw > (MC − LMP_gap) × mlf × gap_hours` at the
   mlf scan values — reported so Step 2 (if it fires) knows whether the
   economic leg or the physical leg would carry the floor.

## §3 — kill thresholds, fixed ex ante

Derived from `FINDING-pjm141` §3's committed capacity-weighted stack quantiles
(p25→p50 spans 25 % of the 95.9 / 94.4 / 96.5 GW stack at +$8.22 / +$6.74 /
+$9.07), the local merit-curve slope at the overnight clearing point is
**0.343 / 0.286 / 0.376 $/GW** → **2.92 / 3.50 / 2.66 GW per $1/MWh**.

* **K-A (materiality).** The lever FIRES only if `Δd(F_pool) ≥ $1.00/MWh`
  (mean over h01–h04) in **at least 2 of 3 years**. $1.00 is 29 % of the
  smallest overnight error ($3.40, 2025) and 15–17 % of the other two — below
  that the lever is inert on the defect it is chartered against (pjm-140's
  +$0.03–0.07 `ramp_envelopes` price move was adjudicated near-inert; a lever
  an order of magnitude above that is the minimum worth a mechanism, a PREREG
  and two 33-min arms). Ex-ante MW equivalent: **F ≈ 2.9 / 3.5 / 2.7 GW** at
  the average local slope.
* **K-B (volume conservation).** At the smallest `F*` achieving the K-A move
  (or at `F_pool` if smaller), the net overnight volume shift per family must
  stay **≤ 1.0 GW** for each of CC / CT / ST. 1.0 GW ≈ 3 % of measured
  overnight CC (33.5–35.5 GW), i.e. **double the keeper's largest current CC
  error** (+0.48 GW, 2025) and comparable to its largest total-thermal error
  (+1.31 GW). A bridge that must degrade a measured-correct class volume by
  more than that to buy its price move is reaching the right number by making
  a right number wrong — the rule 14 `[R-ACCURATE]` / rule 1 `[R-STRUCT]`
  trade this charter exists to prevent.
* **FIRE rule.** The mechanism is built (Step 2: new `ScenarioConfig` field,
  matrix row, PJM-derived min-load fractions, PREREG, owner sign-off) only if
  **both** K-A and K-B hold in the same ≥2 of 3 years. Otherwise the
  pre-check kills the lever: item 13's cell closes
  (`gas_commitment_bridge` PJM `U` → `R`, pre-check refutation), **no
  mechanism code is written**, and the session records the fall-back (queue
  item 10 on the winter-LEVEL story only) as the handover lead.

Ex-ante tension, stated for the record: K-A needs ~3 GW at the margin; K-B
permits ~1.0–1.7 GW of net shift if the displaced band's CC share is the
marginal-census ~40 %. On the committed numbers these are close to mutually
exclusive — the lever can fire only if the MEASURED per-hour local slope is
materially steeper than the p25–p50 average, or the displaced band is far more
CC-heavy than the marginal count share suggests. That is precisely what T7
measures; the thresholds do not move after the numbers land.

## §4 — standing bounds this pre-check honours

* Judged on the **amplitude** statistic (overnight error), never the annual
  mean (pjm-141 §5.1).
* No solve, no dashboard registration, no keeper change in the kill branch
  (pjm-138/139/141 precedent).
* C3c / C8 / C1 gates are Step-2 (arm-time) concerns; the pre-check cannot
  touch them because it solves nothing.
* DO-NOT-REDO: nothing here re-measures pjm-141's census, re-bins the offer
  surface, or touches any daily gas series.
