# PREREG nyiso-151 — the Allegany eGRID identity heat-rate repair (ARM H) and the `cc_reserve_duty_split` re-gate on the repaired fleet (ARM HC)

**Session nyiso-151, 2026-08-22. Committed and pushed BEFORE any arm solves.**
Control: `results/calibration/nyiso150_control` — the designated keeper
`2026-08-22-nyiso-149-duty-curve` recipe replayed at HEAD, already proven
bit-identical to the keeper (IDENT gate, max |Δprice| = 0.0 ×3 years,
`_nyiso150_ab_gates.json`). Years 2023/2024/2025, one bundle per arm, years
sequential within each invocation, the two arm invocations concurrent
(rule 12); holdout freeze ACTIVE — every year solved, scored or read is
2023–2025. Identification: `FINDING-nyiso150-allegany-hr-identity-2026-08-22.md`
(the nyiso-150 ARM C′ rejection's successor, re-specified).

## 1. THE MECHANISM (built this session, default off, rule 28(c) row in the same PR)

`ScenarioConfig.egrid_identity_heat_rates` — a CAMPD-less fossil plant whose
measured eGRID history lives under a DIFFERENT ORISPL takes its pooled
PLHTIAN/PLNGENAN rate from the committed per-ISO artifact instead of the
`HEAT_RATE_BINS` vintage class default. Membership is the threshold-free
discovery rule (exact PLNGENAN == EIA-923 annual netgen to <0.5 MWh in EVERY
overlapping eGRID vintage, ≥2 overlaps, same state, different ORISPL), run
mechanically over the ISO's whole population:
`scripts/data/derive_egrid_identity_heat_rates.py` → NYISO artifact = exactly
**{EIA 7784 ↔ eGRID 10619, 7/7 vintages, pooled 8.4209}** out of 108
candidates × 7 vintages. Declared a priori, before any solve: the pooled
all-vintage rate is THE value (8.4209); its leave-one-vintage-out range is
[8.3434, 8.5266], inside the per-vintage envelope [7.9904, 8.6826]. Zero
fitted parameters; the rate is arithmetic on eGRID's own published fields.

Pre-solve verification already run and recorded here: the fleet swap touches
exactly Allegany's two units (7.5 → 8.4209 both; 460-generator fleet
otherwise byte-identical, flag off strictly no-op); the derive `--check`
byte-reproduces; 5 new unit tests pass
(`tests/unit/data/test_egrid_identity_heat_rates.py`); the pinned default
cache key is untouched (hash-drop registration; config suite 53/53).

## 2. THE ARMS

* **ARM H** — `nyiso151_armH`: control + `egrid_identity_heat_rates=true`
  (one field). The measured-input repair alone.
* **ARM HC** — `nyiso151_armHC`: control + `egrid_identity_heat_rates=true`
  + `cc_reserve_duty_split=true`. The nyiso-150 re-gate re-run on the
  repaired fleet — the finding's step (2). Its C-K gates are evaluated vs
  the SAME control, with ARM H reported alongside so the split's own
  contribution is visible.

## 3. KILL GATES — ARM H

* **H-K1 EXACTNESS** — exactly one differing config field.
* **H-K2 CONSTRUCTION** — the solve log carries the apply line ("eGRID
  identity-reconciled heat rates applied to 2 generator(s) across 1
  plant(s)") in every year; an inert arm fails.
* **H-K3 TARGET DIRECTION + BLAST RADIUS** — Allegany (7784) P1 energy FALLS
  vs control in every year (direction only; magnitude not predicted — the
  merit cliff's other side is an empirical question); Bethlehem/cohort
  starts no-degrade per the standing C-K3 table (arm err ≤ 1.5 × control
  err + 5).
* **H-K4 CONDUCT** — zero NEW failing D-1/D-2/D-4 rows; C8 PASS every year.
* **H-K5 CRITERIA** — C1/C2/C3a/C3b/C4/C8: no PASS→FAIL vs control in any
  year; C3c reported at full magnitude (standing ledger).
* **H-K6 LOYO** — derive-side recorded in the artifact (§1: every
  leave-one-vintage-out pooled rate within [8.3434, 8.5266]); gate-side:
  H-K3's direction leg holds in each year separately.

## 4. KILL GATES — ARM HC (the re-gate; PREREG-nyiso146b §C.3 verbatim, on the repaired fleet)

* **HC-K1 EXACTNESS** — exactly two differing fields vs control:
  {`egrid_identity_heat_rates`, `cc_reserve_duty_split`}; exactly one vs
  ARM H.
* **HC-K2 LIVENESS** — the armed cohort logs 7 plants; each of {50744,
  54592, 54593, **7784**}'s model energy falls **≥80 %** vs control in 2023
  and 2024 (2025 reported, preliminary vintage). This is the bar Allegany
  missed at 70 %/60 % on the un-repaired fleet (nyiso-150) — whether the
  corrected base rate (peak offer ≈ +$10 at the 2.25× band) clears it is
  this arm's question.
* **HC-K3 NO-DEGRADE** — non-cohort CC plant-years: start-count error ≤
  1.5 × control error + 5; C1 stays PASS every year.
* **HC-K4 D-4/D-2 (K6′)** — zero new D-4 failures; escalation clears only
  with zero new D-4 AND zero new D-1; C8 PASS.
* **HC-K5** — C1/C2/C3a/C3b/C4/C8: no PASS→FAIL vs control; C3c reported.
* **HC-K6 LOYO** — gate-side: HC-K2 holds in 2023 and 2024 separately
  (membership stability was proven derive-side at nyiso-146b and the
  artifact is frozen, rule 23).

## 5. PROMOTE RULE (pre-registered)

* **Both arms clean** → ARM HC is the promotion candidate (the keeper
  workflow: attestation seeded from the 149 lineage + one NEW DOF-ledger
  entry for the identity artifact — identification `published/measured`,
  `n_scalars` 0; rule 22 D-5(b) re-key with determination re-verification; a
  worse determination stops and escalates).
* **H clean, HC fails HC-K2 again** → ARM H alone is the candidate (a
  measured-input improvement with no criterion cost stands on rule 14), HC
  registers as a rejection, and the graded-duty successor returns to the
  queue with the EIA-923-monthly instrument question.
* **H fails its own gates** → both register as rejections; the finding
  stands as the record and the class-default residual is typed as an open
  measured-input limitation.
* Whatever the outcome, both completed solves register (rule 15) and the
  `egrid_identity_heat_rates` NYISO cell + the `offer_curve_by_group` record
  are stamped in this session (rule 28(b)).

## 6. PREDICTIONS (falsifiable)

* ARM H: Allegany's econ marginal cost rises ≈ +$2–3/MWh (8.4209 vs 7.5 at
  2023–2025 delivered gas), moving it from below Sterling (8.56, measured)
  to just below it — P1 energy falls, but the plant may remain on the cheap
  side of the merit cliff; a partial fall without the split is the expected
  shape.
* ARM HC: the armed peak offer rises from ≈ $47 to ≈ $53 (2023 basis),
  the direction HC-K2 needs; Sterling/Batavia/50744 reproduce their
  93–98 % collapses.
* No gated criterion moves in either arm beyond noise: the whole delta is
  one 67 MW plant's merit position.

## 7. REPRODUCTION

```
python3 scripts/data/derive_egrid_identity_heat_rates.py --iso NYISO --check
python3 scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso151_armH_recipe  --out-dir results/calibration/nyiso151_armH
python3 scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso151_armHC_recipe --out-dir results/calibration/nyiso151_armHC
python3 scripts/legitimacy_diagnostics.py --bundle results/calibration/nyiso151_arm{H,HC} --iso NYISO --years 2023 2024 2025
python3 scripts/probes/_nyiso151_ab_gates.py
```
