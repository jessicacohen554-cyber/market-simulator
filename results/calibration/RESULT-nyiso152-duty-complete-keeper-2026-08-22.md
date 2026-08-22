# RESULT nyiso-152 — the completed duty-role mechanism is KEEPER: `2026-08-22-nyiso-152-duty-complete` (CALIBRATED), promoted on the prereg's own rule; every pre-registered gate PASSES and the control-side capture lands to 0.6 %

Session nyiso-152, 2026-08-22. Prereg
`PREREG-nyiso152-bridge-reserve-duty-exclusion-2026-08-22.md` + mechanism code
committed and pushed BEFORE any solve; grounds
`FINDING-nyiso152-phase0-reserve-posture-overturned-2026-08-22.md` (the
owner-chartered RAMP10 phase-0). Gates record `_nyiso152_ab_gates.json`.
Holdout freeze ACTIVE; every year solved, scored or read is 2023–2025.

## 1. Arms and identity

* **Control** `nyiso152_control` (keeper recipe replay at the post-#4203-merge
  HEAD): **IDENT PASS, max |Δprice| = 0.0** vs the committed
  `nyiso151_control` (≡ the keeper) over every zone-hour of all three years —
  the merged PRs #4199–#4203 (ERCOT RUC logging; this session's own RHO_CLIP
  ruling arriving via #4201) are thereby PROVEN NYISO-keeper-inert. Not
  separately registered (the nyiso-149 convention; this identity is its
  record).
* **ARM SE** `nyiso152_armSE` = keeper recipe + `cc_reserve_duty_split` +
  `nyiso_gas_bridge_reserve_duty_exclusions`. K1 exact BOTH ways: vs control
  = exactly the two flags; vs the committed `nyiso151_armHC` mid-rung =
  exactly the exclusion — so the exclusion's own effect is isolated without a
  third solve.

## 2. Gates (all PASS; `_nyiso152_ab_gates.json`)

* **SE-K2 liveness** — the reserve-duty membership log line fires in every
  year naming 7784; **Allegany's bridge floor is ZERO in all three years**
  (floors npz: no mech-20 rows survive for the plant).
* **SE-K3 mechanism-scoped target** — the pre-registered control-side capture
  (predicted BEFORE the solve from the committed phase-0 decomposition:
  armHC's above-floor piece, **90.4 / 111.8 / 0 GWh**) lands at
  **90.9 / 111.9 / 0.0 GWh** — within **0.6 % / 0.09 % / exact** against a
  ±50 % band. Sterling / Massena / Batavia reproduce their split collapses at
  **93.6–97.8 %** (all ≥ 80 %) in both gated years.
* **SE-K4 (K6′)** — **zero new D-4 failures, zero new D-1 misses**; the few
  D-2 share upticks (≤ 0.13 pp) are denominator effects of the class's total
  energy falling faster than its forced energy — the two-leg K6′ design
  escalates and clears.
* **SE-K5 criteria** — criterion-for-criterion equal to the keeper's:
  C1 PASS (14/14, free 10/10), C2, C3b, C4, C6 (attested), C8 PASS;
  **C3a PASS at +5.3 % / −2.7 % / −8.1 %** vs RT (2024 and 2025 IMPROVE on
  the superseded keeper's −4.2 % / −8.8 %; 2023 moves +3.3 → +5.3 %, well
  inside the ±10 % band — removing ~1.7 TWh of duty-cohort mid-merit energy
  lifts prices slightly); **C3c counts BIT-IDENTICAL** (1/0/0 h vs RT
  10/13/42), the lone ledgered caveat under the standing rule.
* **REPORTED, not gated** (prereg §4): the nyiso-150/151 ≥ 80 %-total-fall
  headline reads **81.9 % (2023) / 78.3 % (2024)**. That bar belonged to the
  split-as-offer-lever arms and their two rejections stand unrewritten; this
  arm's claim was the floor piece, which is delivered exactly.

## 3. What the keeper buys (rule 1 — legitimacy, with fit intact)

Allegany (7784, measured e923 pooled CF 0.0173 ≈ 10–16 GWh/yr):
model/actual **43× / 33× (control) → 7.8× / 7.2×**; the 57.8 / 91.4 GWh of
rule-17 bridge-floor energy at a meter-dark plant is **gone**, and the
remaining 90.9 / 111.9 GWh is peak-band spike-hour economics — the residual
the CLOSED offer lane owns (two levers proven bit-insensitive at nyiso-151).
The whole 7-plant duty cohort is now represented consistently: peak-band
offers (split) + out of the bridge's day-ahead commitment population
(exclusion) — one phenomenon, both halves, **zero new scalars** (DOF ledger
9 → 10 entries: the frozen duty artifact, a plant-code membership set,
`n_residual` unchanged at 6).

## 4. Promotion (the pre-registered §5 rule; no owner ask needed)

Determination **CALIBRATED** on the registration's own
`calibration_verdict` — equal to the superseded keeper's label with the
identical lone C3c caveat, two load-bearing C3a years improving —
and legitimacy strictly better (floor removed; zero new convictions).
Executed: keeper shard swap (prior 151 note preserved verbatim), rule-22
D-5(b) marker re-key with determination re-verification (CALIBRATED →
CALIBRATED; the worse-determination stop does not fire), status rebuild
(`NYISO:CALIBRATED`, `--check` in sync), `audit_keepers --iso NYISO` PASS
0/0, matrix: `gas_commitment_bridge` cell record + `offer_curve_by_group`
correction record (the nyiso-151 re-type overturned; text preserved
verbatim), keeper/gates stamps + §5.5 header re-stamped, checker fully
green. Registration auto-pruned `2026-08-19-nyiso-146-control` (top-15
retention).

## 5. Queue state after nyiso-152

* **CLOSED this session:** the merit-order-inversion object (the nyiso-145
  small-CC family — Sterling/Massena/Batavia by the split, Allegany by
  split + exclusion, Carthage/Syracuse already lay-up-excluded); the hydro
  RAMP10 seams (adjudicated provably LP-inert for NYISO, off the queue; the
  cross-ISO seam note handed to the consuming lanes via the governance log);
  the AS-certification owner-court question (dissolved with it).
* **REMAINING testable:** the Flynn/Bethlehem start-conduct residual; the
  `online_rho` pair A/B (`nyiso_synchronised_reserve` /
  `nyiso_incity_commitment_obligation`, admissible since the RHO_CLIP
  ruling — measured 0.2011 / 0.3014 now solve at their own measurement).
* **OWNER COURT (unchanged):** the winter downstate locational
  identification intake; the Q2 annotation
  (ASSESSMENT-nyiso150-frontier-2026-08-22.md §5).
* C3c stays the ledgered model-class limitation (counts unchanged).

## 6. Reproduction

```
python3 scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso152_control_recipe --out-dir results/calibration/nyiso152_control
python3 scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso152_armSE_recipe  --out-dir results/calibration/nyiso152_armSE
python3 scripts/legitimacy_diagnostics.py --bundle results/calibration/nyiso152_armSE --iso NYISO --json-out results/calibration/nyiso152_armSE/legitimacy_diagnostics.json
python3 scripts/probes/_nyiso152_ab_gates.py --arm-se-log <SE solve log>
```
