# PRECOMMIT — NWPP-NEXT-28: per-BA BAL-002-WECC contingency reserve, 2019–2025

- **Phase 0:** `FINDING-nwppnext28-ba-reserve-phase0-2026-10-04.md`.
- **Owner card:** 2026-10-04, "Build reserve, solve (Recommended)".
- **Control:** keeper `2026-10-03-nwpp-next-27-path76`, read from its committed bundle
  `results/calibration/nwppnext27_span` (rule 29b: no control solve).
- **Arm:** the keeper recipe plus two keys, `energy_reserve_coopt=true` and `nwpp_ba_contingency_reserve=true`. The
  first is the shared co-opt gate, which the second requires.
- **Free parameters added:** zero.
  - BAL-002-WECC-2a fractions 0.03 / 0.03 / 0.5: published.
  - rho 0.2130: CAMPD-measured, `campd_online_reserve_rho_NWPP.csv`, family set `nwpp_spin`.
  - Hydro 10-minute ramp 1.0 × nameplate: class physics, the CAISO constant's source.
  - Shortfall priced at the region's registered `voll` ($2,000).
- **Shards:** seven, one per year (rules 16 and 36).

## G-DRIFT (pin against the NEXT-27 leg pin `440ad144`)

- `model/interchange/caiso.py` and `model/interchange/spec.py`, plus the field
  `caiso_dsw_daytime_lateevening_unprinted_arm`: CAISO-only and default off. INERT for NWPP.
- `data/eia930/frames.py`: `_pool_hourly_frame`'s per-member net-generation block moves into
  `_pool_member_net_generation`, statement for statement. INERT: the same code runs.
  `tests/unit/data/test_nwpp_ba_contingency_basis.py::test_member_demand_sums_to_pool_frame` pins that the member sum
  equals the pool frame.
- `model/reserves/spec.py`: `caiso_pergen_structure`'s body moves into `_hydro_backfilled_pergen_structure`. This is
  INERT for NWPP, which never calls it, and the CAISO reserve tests pass. The new `_nwpp_design` is reached only when
  armed.
- `pipeline/kwargs.py` and `runner.py`: refusals only.
- `config/scenarios.py`: the new field, plus its registrations.
- Verdict: no LIVE hunk at the off posture, so no control solve.

## Ex-ante predictions (fixed before any solve)

1. **Construction.** The log reads
   `NWPP <Y> BAL-002-WECC contingency reserve: 10 families over <n> pools, rho 0.2130`. The zone requirement means
   match FINDING §A to ±0.5 MW.
2. **Reserve met.** The requirement is met in ≥ 99.5 % of zone-hours. Shortfall steps price at $2,000, and any hour
   at that step is reported.
3. **CC_REGULAR (footprint) falls** by −0.4 … −1.8 TWh in 2024, and −0.3 … −1.5 TWh in each other year.
   - The cut is concentrated in SNV and EAST.
   - The upper bound is FINDING §B's 1.8 TWh, before re-dispatch. Part returns through other zones' CCs and imports.
   - C1 CC_REGULAR 2024 (+12.15) stays FAIL. The 2019 knife-edge (+7.50, band 8.00) moves away from the band.
4. **CT_PEAKER rises** in SNV and EAST (online CTs carry spin) by +0.1 … +0.8 TWh/yr. This risks the C1 CT_PEAKER
   2024 PASS (+1.56).
5. **Price.**
   - The reserve opportunity cost lifts the SNV and EAST energy duals slightly.
   - C3a 2024 (−9.96 $/MWh) moves by 0 … +2.
   - C3b 2023 (0.202, 0.002 over the band) could move either way.
   - The price is unscored 2019–2022.
6. **Risks.**
   - Shortfall-hour price spikes.
   - C4 gas r in SNV and EAST, because headroom flattens the CC shape.
   - D-1.
   - LP size: pergen 2·n_r columns per hour plus 10 family rows, which is small.
   Every regression will be reported at full magnitude.

## Decision rule

- **Promotion candidate** under the owner standing ruling ("promote if structural integrity improves, even if a gate
  regresses"). A missing BAL-002 reserve design is a structural gap, so the candidate qualifies when all three hold:
  - each hard stop holds;
  - reserve is met (prediction 2);
  - no new FAIL appears outside the predicted risk list.
- The promotion goes on ONE owner card in every case, with the full verdict diff against the keeper.

## Addendum (2026-10-05): per-plant spinning pools. Pin 1 legs are superseded.

**What the pin-1 legs showed** (pin `971685b4`, all hard stops passed, zero shortfall hours):

| leg | commit | CC_REGULAR vs keeper | coal vs keeper | spin duals |
|---|---|---|---|---|
| 2022 | `072f715a` | +0.82 TWh | −0.40 TWh | — |
| 2023 | `f4486f64` | +0.45 TWh | −0.17 TWh | — |
| 2024 | `603b275e` | +0.00 TWh | — | ≈ 0 |

Predictions 3 and 4 failed: CC_REGULAR rose or held instead of falling.

**Cause: the pooling, not the obligation.**
- (Zone, fuel-class) pools put an offline plant's idle capacity in the same `ΣP + R ≤ Σcap` row as an online plant's
  output. The gate `R ≤ rho·ΣP` then counted that idle capacity as spinning headroom.
- In 2024, mean pooled spin available was SNV 501 MW and EAST 606 MW, against a requirement of 134 and 182 MW.

**Fix: `nwpp_pergen_structure`.**
- Pools are per thermal (plant, fuel class). Hydro stays zone-pooled.
- An offline plant now backs no spin.
- Test: `test_idle_plant_backs_no_spin_for_a_loaded_one`.

**Zero-LP check at keeper dispatch** (`scripts/probes/_nwppnext28_perplant_spin.py`): the spin shortfall the LP must
close by re-dispatch, in TWh.

| zone | layout | 2019 | 2022 | 2023 | 2024 | 2025 |
|---|---|---:|---:|---:|---:|---:|
| SNV | per-plant | 0.13 | 0.31 | 0.37 | 0.26 | 0.37 |
| SNV | pooled | 0.00 | 0.11 | 0.14 | 0.03 | 0.09 |
| EAST | per-plant | 0.26 | 0.79 | 0.34 | 0.29 | 0.54 |
| EAST | pooled | 0.11 | 0.55 | 0.20 | 0.00 | 0.08 |
| OR | per-plant | 0.03 | 0.12 | 0.17 | 0.20 | 0.23 |
| NW | both | ≈ 0 | ≈ 0 | ≈ 0 | ≈ 0 | ≈ 0 |
| INLAND | both | ≈ 0 | ≈ 0 | ≈ 0 | ≈ 0 | ≈ 0 |

**Revised predictions for the pin-2 legs** (replacing 3 and 4):
- **3′ CC_REGULAR (footprint).** It falls by 0 … −0.8 TWh in each year. The SNV and EAST per-plant shortfall bounds the
  cut before re-dispatch; part of it returns through other CCs and imports. C1 CC_REGULAR 2024 stays FAIL.
- **4′ CT_PEAKER.** It moves by ±0.3 TWh.
- **Unchanged:** predictions 1, 2, 5 and 6.
- **Solve time.** It roughly doubles: P1 took 47–83 min on pin 1, so the budget is now 360 min.
