# PRECOMMIT — O7 Phase 0: the predicted cost, in keeper results, of restoring the ERCOT P0 bit-identity seam

**Date:** 2026-08-30 · **Lane:** O7 P0 bit-identity restoration (owner ruling
2026-08-26: charter a restoration, accept-and-document rejected) ·
**Branch:** `claude/ercot-p0-bit-identity-o7-tuzrjm` · **Phase:** 0 (scope only —
zero solves run, zero solves predicted about are authorized here)

This document fixes, BEFORE any measurement, the answer to the charter's
decisive question: **would moving `ercot_econ_curve_top_refine` off P0 change
the CALIBRATED ERCOT keeper's numbers?** The full trace and adjudication live in
`docs/FINDING-o7-p0-seam-restoration-2026-08-26.md` (pushed after this
precommit). Per the charter, if the answer is yes, restoration is a mechanism
change to a CALIBRATED keeper and ESCALATES to the owner rather than
proceeding.

## 1. The construction being predicted about

The only construction that restores control-vs-arm P0 bit-identity while
keeping the refinement expressible (Finding §3, "Construction B"): the 2n−1
refined slice GEOMETRY becomes unconditional on the ERCOT CAMPD path, every top
sub-slice carries the COARSE top-block heat rate in the base fleet (so
`mc_base`, the P0 objective, presents the identical supply function armed and
unarmed), and the refined ladder is applied as a P1-only additive
`mc_bid_adjust` component. Arm-vs-control P0s are then bit-identical by
construction. The prediction below is about what that construction does to the
keeper — i.e. Construction-B-armed vs the current `ercot236_k33_clip` /
`ercot234_eastex_identity` recipes.

## 2. Predictions — fixed now, never renegotiated

* **P-1 (commitment reversal).** Construction B's P0 presents the CONTROL's
  supply function, not the keeper's: the keeper's P0 carries the refined ladder
  in its objective. Predicted: the ercot-188-measured control-vs-arm P0
  commitment delta REVERSES at its measured order — a double-digit share of
  committed rows (the 188-era measurement: 73 of 132 rows, 12,474 MW) changes
  commitment pattern relative to the keeper's P0, and the
  `ercot_gas_commitment_bridge` floored unit-hours (armed `true` in BOTH
  keepers, detected from the P0 run pattern) move back toward control-side
  values in all three years (2023/2024/2025 directionally per FINDING-ercot188
  §6: 12,309→~12,375-scale at the 188-era recipe; direction, not exact counts,
  at the 236/234 recipes).
* **P-2 (price level).** The 2023 annual load-weighted price moves by order
  **+$1 to +$3/MWh** versus the keeper (center ≈ **+$2.2/MWh**), the sign and
  scale of FINDING-ercot188 §6.2's confounded commitment channel run in
  reverse: the IQR priced the ladder channel at +$1.99/MWh quantity-fixed, the
  whole-solve arm delivered −$0.21/MWh, and Construction B keeps the ladder in
  P1 while stripping its commitment-side half.
* **P-3 (determination motion).** A move of that scale is 3–10 % of the annual
  price level — C3a-2023 (currently PASS at −7.3 % on the CALIBRATED keeper)
  moves materially, whatever its direction; C3b/C3c and the G-SHED shed counts
  (the signature that has killed this object twice) move unpredictably.
  **Predicted verdict: the keeper's scored numbers CHANGE ⇒ restoration is a
  mechanism change to a CALIBRATED keeper ⇒ ESCALATE, do not build.** Per rule
  1 `[R-STRUCT]`, whether any of these moves *improves* the fit is irrelevant
  to this verdict and is not predicted.
* **P-4 (degeneracy hazard, secondary).** Construction B's unarmed/armed P0
  carries n identical-cost columns where control carried one — manufactured LP
  degeneracy inside the field of view of the run-length detector and the
  bridge's P0-pattern scan. Predicted: per-row run patterns on those columns
  are tie-break-unstable, so even the "control" leg is equivalent to the
  historic coarse fleet only by argument, never byte-identical — the proof
  instrument B exists to restore is degraded by B itself.

## 3. What could surprise this precommit, and disclosure

The falsifying measurement is a Construction-B A/B against the keeper recipe —
**not run in Phase 0 and not authorized by it**: building B is itself the
mechanism change being escalated, so the measurement is owner-ordered or not
run at all. If it ever runs and the keeper's scored numbers do NOT move beyond
tie-break noise, P-1–P-3 are wrong and restoration becomes a refactor — that
outcome would reopen Phase 1 with no escalation needed.

**Disclosure:** this precommit was written after reading the committed record —
`FINDING-ercot188-cliff-offer-curve-2026-08-11.md` (incl. the §6 P0-delta
probe table), `PRECOMMIT-ercot188` §2.6/§3, the two keeper `run_config.json`s,
and the live code path. No solve, probe, or new measurement of any kind was run
before or while writing it. The predictions are derived from that committed
evidence; the thing they predict — Construction B's effect — has never been
measured by anyone.
