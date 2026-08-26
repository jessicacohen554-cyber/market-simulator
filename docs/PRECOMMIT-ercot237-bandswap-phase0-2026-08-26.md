# PRECOMMIT — ercot-237 (2026-08-26): Phase-0 characterization of the keeper's band-structure residual — WHICH hours/months swap bands. ZERO-SOLVE, measurement only, NO lever, NO gate change

**Session ercot-237, branch `claude/ercot-236-merge-owner-queue-k97n01`.**
Charter: the post-CALIBRATED continuation handoff's item C — the optional
bounded diagnostic on the keeper's REPORTED band-structure residual
([500,1000) under-fills 18 vs 43 while [200,500) over-fills 103 vs 77;
C3b passes regardless at 0.102). The handoff authorizes Phase-0
characterization only: *"characterize WHICH hours/months swap bands before
proposing any lever; any lever proposal is a new precommitted round,
owner-visible. Do not solve to look busy."* This precommit is pushed and
verified BEFORE any measurement is computed (ercot-224/225 Phase-0
precedent).

Keeper resolved fresh at dispatch: **`2026-08-25-236-swcap-clip-k33`**
(CALIBRATED, rubric v3.4, zero caveats; bundle
`results/calibration/ercot236_k33_clip`, merged to main in PR #4288 and
live on the deployed dashboard — verified this session). The cross-year
reference `2026-08-25-234-eastex-identity` is NOT touched.

## 1. What is measured (all zero-solve, committed artifacts only)

Inputs, byte-identical constructions to the ercot-236 point scorer
(`scripts/probes/ercot236_h4097_repair.py::_lw` / `score_point`):

* **Model series** — the keeper sidecar
  `results/calibration/ercot236_k33_clip/hourly/system_2023.parquet`,
  P1 rows, per-hour demand-weighted zonal `price` (`Σ price·demand /
  Σ demand`), reindexed to 8760, `np.nan_to_num` (NaN → 0).
* **Actual series** — `data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet`,
  `year == 2023`, sorted by `hour`, column `rt`, first 8760 values.
* **Bands** — `[200, 500)`, `[500, 1000)`, `>= 1000` on both series
  (the point scorer's `model_band_hours_vs_actual` edges), plus the
  residual band `< 200`.

Measurements (the probe, `scripts/probes/ercot237_bandswap_phase0.py`,
writes `results/calibration/ercot237_bandswap_phase0.json`):

1. **V-0 identity gate (hard assert, run first):** the recomputed 2023
   band counts must reproduce the keeper's registered values EXACTLY —
   model 103 / 18 / 59, actual 77 / 43 / 59
   (`ercot236_point_score.json::model_band_hours_vs_actual`). Any
   mismatch STOPS the probe (no result is recorded) and is reported as a
   construction drift, not worked around.
2. **The joint band matrix** — 4×4 cross-tab of (model band × actual
   band) over all 8760 hours, hour lists attached for every off-diagonal
   cell that touches `[200,500)` or `[500,1000)`.
3. **Per-population detail** (hour, month, hour-of-day CST = h mod 24,
   model $, actual $) for:
   a. the 43 actual-`[500,1000)` hours (where does the model put them?);
   b. the model-`[200,500)` hours whose actual is `< 200` (the over-fill's
      spurious member set);
   c. the model-`[200,500)` hours whose actual is `>= 500` (band
      under-shoot members, if any).
4. **Overlap with known objects** (report-only): the 68 G-SPUR banded
   hours (`model ∈ [150,500] & actual < 150`, the ercot-225 card's
   population) ∩ population (b); the clip-saturated hours
   (max zonal λ ≥ $4,999) ∩ population (a); month × hour-of-day
   histograms of (a) and (b).

## 2. Declared priors (resolvable, no gate hangs on them)

* **P1** — the majority of the 43 actual-`[500,1000)` hours are modeled
  BELOW $500 (shoulder under-shoot), not above $1,000: the under-fill is
  a level gap on event-shoulder hours, not the surface overshooting
  through the band. (Basis: the ≥$1,000 tail is EXACT 59 = 59, so the
  deep-event population is already placed; what is missing is the band
  below it.)
* **P2** — the model-`[200,500)` over-fill's spurious members (actual
  < $200) overlap the 68 G-SPUR banded hours substantially (≥ half of
  the spur set appears), since G-SPUR's `[150,500]` window nests the
  band above $200. (Basis: spur 68 was reported unchanged across the
  re-bracket — the same blunt-instrument level lift feeds both counts.)
* **P3** — both mismatch populations concentrate in Jun–Sep, the
  `[500,1000)` under-fill specifically in late-afternoon/evening hours
  (HE 17–21 CST). (Basis: the keeper's monthly residual is summer-carried;
  off-season months are within $2 of actuals.)

Priors are expectations to be graded, never selection criteria — nothing
in this round selects, arms, or tunes anything.

## 3. What this round may and may not do

* MAY: read committed sidecars + the committed actuals parquet, compute
  the measurements above, record them in a results JSON + FINDING doc,
  grade the priors, name candidate objects (hours/populations) for the
  owner-visible queue.
* MAY NOT: solve anything; edit any gate, config, offer curve, or
  mechanism; stamp any matrix cell (no mechanism is tested); propose-and-
  execute a lever (a lever proposal, if the characterization suggests
  one, is a NEW precommitted round, owner-visible, per the handoff).
* Registration: no run is produced, so rule 15 does not trigger; the
  deliverable is the committed probe + JSON + FINDING + calibration-log
  entry (ercot-224/225 zero-solve precedent).

## 4. Amendment protocol

Any deviation from §1's constructions discovered mid-round (e.g. an
actual-side count that does not reproduce 77/43/59) is recorded as an
Amendment to this precommit BEFORE any further measurement, pushed, and
the FINDING cites it — never silently absorbed.
