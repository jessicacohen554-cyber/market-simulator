# PRECOMMIT — ercot-239 round 3 (2026-08-30): Phase-0 bounded diagnosis of h3068-2024, the standing band-top-blind hour — ZERO-SOLVE, measurement only, NO lever, NO gate change

**Session ercot-239, branch `claude/ercot-239-residual-queue-lbkvbf`.**
Charter: the residual-queue handoff's priority 3 — h3068-2024 (May 8,
20:00 CST), "the standing band-top-blind hour, now permanently counted
under the lidless G-SPUR — model $676–798 vs actual $110.41, present in
EVERY lineage … a named object for a bounded diagnosis"
(FINDING-ercot225 §1: *"the hour after the May-8 evening event, where the
model holds a deep price after reality came off the peak … the same May-8
evening whose shed the ercot-223 event-release guard repaired; the
price-side residual at the following hour remains"*). FORWARD-keeper
lane object (2024 ∈ the forward span); the diagnosis reads the forward
keeper's committed sidecars. This precommit is pushed + blob-verified
BEFORE any measurement (round-1/2 discipline).

## 1. Sources and V-0

All zero-solve, committed artifacts + measured inputs only:

* Forward keeper bundle `results/calibration/ercot234_eastex_identity`
  (hourly sidecars 2024: system / class_hourly / reserve_family /
  storage / adaptive — `adaptive_2024.parquet` carries the
  storage-adaptive-expectation state: `s_model_day`, `p_hat_day`,
  `floor_usd`).
* Actuals `actual_lmp_hourly_ERCOT.parquet` (2024 `rt`); EIA-930 wide
  `ERCO hourly.parquet` (local-2024 rows, the round-1 convention,
  alignment lag-check asserted); measured
  `ercot_2024_ordc_reserves_hourly.parquet` (`rtolcap`, `prc`,
  `rtorpa`, `rtordpa`, `system_lambda`).
* Model price = the demand-weighted zonal construction (round-1
  verbatim), on 2024.

**V-0 (hard assert, run first):** the keeper's h3068 demand-weighted
price reproduces the card's $798.20 (±$0.05) and the actual reproduces
$110.41 (±$0.05). Mismatch STOPS the probe (Amendment protocol).

## 2. What is measured (probe `scripts/probes/ercot239_h3068_phase0.py` → `results/calibration/ercot239_h3068_phase0.json`)

Over the event window **h3060–h3078** (May 8 12:00 – May 9 06:00 CST),
per hour:

* **M-1 model-side:** lw price, zonal price min/max, slack, dump,
  reserve_price, ordc_adder, rtordpa_overlay; per-family reserve rows
  (dual / requirement / held / shortfall); class dispatch (fossil
  thermal, wind, solar; the round-1 taxonomy); storage charge /
  discharge; the adaptive state (`s_model_day`, `p_hat_day`,
  `floor_usd`).
* **M-2 actual-side:** RT price; EIA-930 Demand / WND / SUN / net load /
  1h ramp / Total interchange; measured rtolcap (+ year percentile),
  prc, rtorpa, rtordpa, system_lambda.
* **M-3 the release comparison:** the hour each side "comes off the
  peak" — actual: the first hour after the window's RT-price peak with
  RT < $200; model: the first hour after its lw-price peak with
  lw < $200; and the same construction on net load (first hour ≥ 2,000
  MW below the window peak). Reported as the model−actual release lag in
  hours, for price and for net load separately.
* **M-4 marginal-setter attribution at h3068 (and h3067, h3069):**
  whether the model lw price sits within $150 of (a) the adaptive
  `floor_usd`, (b) an ORDC/reserve construction (ordc_adder or
  reserve_price), (c) a thermal offer level (the graded census's
  implied levels); storage discharge MW at the hour; slack/dump.
  Every leg is reported; the attribution names the closest.

## 3. Declared priors (graded in the FINDING; never selection criteria)

* **P1 (mechanism-side hold):** at h3068 the model price sits within
  $150 of the storage adaptive `floor_usd` with storage discharging
  ≥ 500 MW — the hold is the adaptive-expectation floor, not thermal
  scarcity. (Basis: PRECOMMIT-ercot223 §"h3068 keeps its floor (pass-1
  settle $675 < $1,000)".)
* **P2 (reality released):** the actual RT at h3068 is < $200 while
  h3066–h3067 ≥ $500, and measured rtorpa/rtordpa at h3068 are < $50 —
  reality's event ended before hod 20. (Basis: the card's "came off the
  peak"; actual $110.41.)
* **P3 (inputs are not the carrier):** the model's NET-LOAD release lag
  vs actual (M-3) is ≤ 1 hour — the price hold is mechanism-side, not a
  demand/renewables input artifact. (Basis: the demand identity settled
  at ercot-240; weather-pinned renewables.)
* **P4 (not reserve scarcity):** every reserve family at h3068 shows
  zero shortfall and dual ≤ $50 in the model. (Basis: the hold is an
  offer/floor phenomenon, not co-opt scarcity.)

## 4. What this round may and may not do

* MAY: read the artifacts above; compute M-1…M-4; record JSON + FINDING
  + a calibration-log addendum; grade priors; name the candidate object
  for the owner queue (expected shape: the adaptive-expectation floor's
  event-release behaviour — the `ercot_storage_adaptive_expectation`
  K-cell's named residual).
* MAY NOT: solve anything; edit any mechanism, gate, or config; stamp
  any matrix verdict (nothing tested; an evidence NOTE on the storage
  adaptive cell is permitted if the attribution lands there); touch
  either keeper.
* Years ⊂ {2024}; no `--holdout-authorized`, no marker (rule 22); ERCOT
  surfaces only (rule 25); no run produced ⇒ rule 15 not triggered.

## 5. Amendment protocol

Any deviation from §1–§2's constructions discovered mid-round is
recorded as an Amendment BEFORE any further measurement, pushed, and the
FINDING cites it — never silently absorbed.
