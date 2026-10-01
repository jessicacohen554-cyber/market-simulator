# PRECOMMIT — nyiso-156 phase 0: the 2025 offer-level object, re-measured on the promoted hydro-repair keeper (NO SOLVE)

**Session:** nyiso-156, 2026-08-25. **Pushed and blob-verified BEFORE any
measurement**, per the lane's prereg-first rail. **HEAD at declaration:**
`6af12ee`.

**Charter:** the 2025 offer-level object — the C3a-2025 failure the hydro
truncation repair unmasked (`docs/FINDING-nyiso-hydro-truncation-repair-2026-08.md`
§4.4; keeper `2026-08-25-nyiso-155-hydro-repair`, determination NOT-YET written
explicitly on owner instruction). The object was ALREADY owner-court before the
repair: `docs/DECISION-CARD-nyiso148-2025-level-remainder-2026-08-21.md`
(owner Q1 pending), decomposed at nyiso-150 into ~2/3 winter locational
(blocked on identification, BLOCKER-B intake class) + ~1/3 the ledgered C3c
summer face. The hydro repair added ~$1.79/MWh of unmasked 2025 under-pricing
whose monthly/zonal/load-conditional location has NEVER been measured — that
measurement is what a sharpened decision card needs and is this phase's whole
scope.

## 1. WHAT THIS PHASE IS AND IS NOT

* **NO SOLVE.** Every number is read from committed artifacts: the two
  registered nyiso-155 bundles' `hourly/` sidecars
  (`results/calibration/nyiso155_hydro_control`, `nyiso155_hydro_repair` —
  same HEAD `ac194ba` pair, so the arm−control delta is exactly the hydro
  repair with no G1 drift inside it) and the committed actuals
  (`data/raw/_validation-source/actual_lmp.json`,
  `actual_lmp_hourly_NYISO.parquet`).
* **REPORT-CLASS THROUGHOUT.** No gate, no bar, no promotion is possible from
  this phase: no mechanism is tested, no arm exists, no determination is
  touched, no matrix cell verdict can move. The output is measurement backing
  a sharpened owner decision card.
* **DIRECTION-BLIND.** Every declared statistic is reported at full magnitude
  whichever way it falls — including any result that makes the 2025 object
  look smaller, larger, or differently typed than the standing record says.
* **STOP RULE.** If any measurement here suggests an armable lever, this
  session does NOT arm or solve it. Admissible-and-identified levers go to a
  successor prereg; everything else goes on the decision card as owner court.
  The offer-side queue was CLOSED at nyiso-151 (two levers proven
  bit-insensitive); nothing here re-opens a cell marked R/I/G.
* **HOLDOUT.** Years read: {2023, 2024, 2025} only. The spend freeze is
  ACTIVE and untouched; nothing here solves, scores, or registers any year.

## 2. DECLARED MEASUREMENTS

Probe: `scripts/probes/_nyiso156_offer_level_phase0.py`, record:
`results/calibration/_nyiso156_offer_level_phase0.json`. All on P1 rows of
the five internal model zones (external node excluded), 2023–2025.

* **M1 — the lw monthly face table.** Model system load-weighted monthly mean
  (price weighted by the bundle's own zone-hour demand) vs the committed
  `rt_lw_mon`, per year, control and arm; the arm−control lw delta by month.
  This locates the ~$1.79 unmasking in the calendar and re-states the
  winter/summer face split ON THE PROMOTED KEEPER (nyiso-150 measured it on
  the nyiso-149 keeper, pre-repair). Anchor check: the annual lw model means
  reproduce the recorded 61.04 / 59.24 (2025 control/arm) to within
  rounding-difference tolerance ($0.15) — a larger residual is reported and
  the construction difference explained before any face number is quoted.
* **M2 — equal-hour vs load-weighted split.** Per year and arm: eqh system
  mean vs eqh actual (`rt`), lw mean vs lw actual (`rt_lw`), and the gap
  decomposition (how much of C3a-2025 is a level miss vs a
  price-error×demand covariance, i.e. a high-load-hour miss). This types the
  object: a flat offer-level deficit and a peak-conditional deficit are
  different identification targets.
* **M3 — load-conditional error profile.** Model−actual hub price error by
  system-demand decile (hourly, model hub = zone-demand-weighted price;
  actual hub = committed hourly `rt`), per year, control and arm. Reported
  for 2023/2024 too: whether the same peak-decile under-pricing exists
  in-band years (hidden by level cancellation) or is 2025-specific.
* **M4 — zone-month eqh tables (nyiso-150 continuity).** The nyiso-150
  phase-0 §1 tables re-computed on control and arm: annual zone errors, the
  eqh zonal gradient (max−min), the winter event-month zone tables, and the
  arm−control delta by zone-month. States whether the repair moved the
  gradient object at all or only the level.
* **M5 — the hydro increment's calendar.** Monthly hydro energy
  (class_hourly, `klass="hydro"`) control vs arm, per year — where the
  restored 3.01 TWh of 2025 hydro (and the removed 1.55/1.09 TWh of
  2023/2024 phantom hydro) actually lands, set against M1's price-delta
  months.
* **M6 — event-window accounting (2025).** The Jun 22–26 and Jul 1/25/28–30
  heat-event windows and the Jan/Feb/Dec winter months: model vs actual lw
  contribution of each window to the annual lw gap, control and arm. Extends
  nyiso-150 §1.3's eqh event measurement to the lw basis C3a actually gates
  on.

## 3. DELIVERABLES

1. The probe + JSON record (committed).
2. **A sharpened owner decision card** —
   `docs/DECISION-CARD-nyiso156-2025-offer-level-2026-08-25.md` — superseding
   the nyiso-148 card's NUMBERS (its questions remain the owner's): Q1
   restated with post-repair magnitudes and the component typing M1–M6
   measure; Q2 re-stated against the fact that its subject (the −2.2 %
   cancellation pass) no longer exists — the keeper now fails C3a-2025
   honestly at −10.8 %.
3. Log entry in `docs/calibration-log/nyiso.md`; matrix shard UNTOUCHED
   (no mechanism tested — stated in the log entry).

## 4. WHAT THIS PHASE CANNOT DO (standing constraints restated)

* The hydro input pair (`hydro_backfill_year=2024`,
  `hydro_eia930_monthly=true`) is CORRECT and STAYS (rule 14); no measurement
  here may be used to re-tune, soften, or revert it. Hydro VOLUME statistics
  are TAUTOLOGICAL BY CONSTRUCTION under the 930 pin and are quoted, if at
  all, only with that label.
* No fitted scalar, adder, haircut, or offset may be proposed as a remedy
  (rules 5/13/21); every candidate remedy on the card must name its
  identification source or be typed owner-court.
* C3c stays a closed queue: its FAIL on the keeper is the silenced
  lone-failure guard, not new evidence; nothing here re-opens a C3c lever.
* Any determination-affecting act is D-5(b)-escalated to the owner; this
  phase performs none.
