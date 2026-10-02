# PRECOMMIT — SPP W0 ST_GAS: does the statistical WEFOR double-count the measured outage layer? (zero-LP pre-check, then one re-solve), 2026-10-02

**This was written and pushed BEFORE any number below was computed.** The readings, formula, threshold and stop rule are fixed here and fail closed.

- **Lane:** closeout-B W0 phase 3 (session_018DsgkLcN1h8NQc2yJegmdN).
- **Authorisation:** close-out desk relay of 2026-10-02 22:48. Run the zero-LP pre-check. Arm the existing `wefor_residual` relief for SPP ST_GAS only if measured evidence shows the stack double-counts, scoped by class as MISO does. If it does, run one SPP re-solve carrying #7081 plus the relief: promote if the train tier holds, HOLD to the desk if it doesn't. If the pre-check fails, report and stop.
- **Context:** `docs/records/governance/closeout-2026-10/W0-phase3/FINDING-spp-w0-stgas-availability-2026-10-02.md`.
  - W0's `commission_year_cod_fallback` gives SPP ST_GAS rows their true commission years. That makes the age-escalated statistical WEFOR live: −166 MW annual mean available in 2024.
  - SPP backcasts also apply the measured CAMPD outage layer (`outage_source = historic`), with no residual relief.
- **DO-NOT-REDO (rule 28).**
  - `wefor_residual` / `wefor_residual_groups` are armed on MISO (0.0, {CC_REGULAR, ST_CHP, ST_GAS}), PJM and ERCOT, and were adjudicated for CAISO at caiso-187.
  - Rule 25: no value transfers. SPP's value is derived from SPP's own fleet and extract.
  - The SPP cell is untested (U).

## 1. Population

- **Rows:** SPP `ST_GAS` rows of the W0 SPP fleet, i.e. the `w0_spp_span` recipe (spp-107 + the ten W0 defaults).
- **Years:** the train years 2023, 2024 and 2025.
- **Source:** `run_year(..., fleet_only=True)`. Zero LP.

## 2. Readings (fixed)

For each row `r` and year `y`:

- **`W_r`: the statistical forced-outage rate the model applies.**
  - Formula: `(WEFOR_base + max(0, age_r − onset) × rate) × wefor_multiplier`.
  - Parameters: `constants.THERMAL_AVAILABILITY["ST_GAS"]` (unchanged, rule 23), the row's W0 `online_year`, and the keeper's `wefor_multiplier` (0.7, unchanged).
  - This is the rate before any residual cap.
- **`X_r`: the measured outage removal the LP applies to the row.**
  - Formula: `1 − mean over the year's hours of the product of every unit-outage derate multiplier the shipped loaders return for the row's (plant, class) key`.
  - Loaders: `unit_outage_derate_factors`, `unit_outage_short_derate_factors`, `unit_partial_outage_derate_factors`, `unit_outage_maxgen_derate_factors` and `partial_outage_derate_factors`, whichever the recipe calls.
  - The multipliers are captured from the calls the rebuild itself makes, not re-implemented.
- **Aggregation:** pmax-weighted means over rows, pooled across 2023–2025. They are also reported by age band (age < 30, 30–49, 50–59, ≥ 60) and by year.

## 3. Gate (fixed)

- **G1, the stack double-counts:** pooled `X ≥ 0.5 × pooled W`.
  - Reading: the measured layer already removes at least half of what the statistical term asserts for the same rows.
  - If so, both are stacked records of one phenomenon (rule 19).
  - **G1 FAIL → report and stop.** No relief, no re-solve.
- **Reported, not gating:**
  - the age-band profile, i.e. whether `X` rises with age as `W` does;
  - the per-year values.

## 4. Value (fixed formula, computed once)

- `wefor_residual = round(max(0, pooled W − pooled X), 4)`. The `max(0, ·)` is a physical bound; this is caiso-187's identification, applied to the applied rate.
- `wefor_residual_groups = ["ST_GAS"]`. Class scope as the desk ruled; ST_CHP and CC are untouched.
- No sweep, no second value and no sensitivity arm.
- The value is written to `docs/records/spp/spp-w0-stgas-relief-identification.json` and pushed BEFORE the first shard launches. It is frozen from then on.

## 5. Re-solve (only on G1 PASS)

- **Recipe:** the spp-107 keeper + the ten W0 defaults + #7081 (on main) + `wefor_residual` / `wefor_residual_groups` from §4.
- **Solve plan:**
  - seven shards, one year each (rules 32/34/36);
  - auto mode;
  - `source_revision` is the exact main SHA after #7078 and #7081 merge.
- **Determination:**
  - Train tier 2023–25 holds CALIBRATED → promote (on structure, rule 1).
  - It falls → HOLD to the desk.
- **Reporting:** C1 ST_GAS 2024/2025 and C3a are REPORTED, never targeted (rule 1). They are not the promotion basis.
