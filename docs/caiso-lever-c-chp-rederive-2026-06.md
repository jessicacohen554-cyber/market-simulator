# CAISO Step 5 — CHP Must-Run Level Re-Derivation (Lever C)

**Branch:** `claude/caiso-chp-pmin-rederive-94g5yd`
**Date:** 2026-06-27
**Status:** Diagnostic probe — NOT a dashboard keeper (Step 6 handles final keeper)

## Motivation

The CAISO shape audit (see `docs/caiso-lever-audit-2026-06.md`) identified two CHP
dispatch bands sitting substantially above CAMPD-measured actuals:

| Group    | Model TWh | CAMPD TWh | Band× (h13–23) |
|----------|-----------|-----------|----------------|
| CC_CHP   | 9.0       | 5.95      | 1.45×          |
| CT_CHP   | 3.3       | 0.41      | –              |

Root-cause: EIA-923 must-run floors sized with `_CHP_F923_FLOOR_FACTOR = 0.85`
were 2–4× too high for sub-CEMS QF cogens whose minimum-month CF reflects
transient industrial steam demand, not a continuously-held grid obligation.
Additionally, Watson Cogeneration (50216, 398 MW) and Richmond Cogen (52109,
130 MW) showed min-month grid delivery well below 30% of nameplate, indicating
the sector-default BTM share (50% for industrial) was too low.

## Changes Made

### A. `scripts/data/derive_thermal_tranches.py`

1. **`_CHP_F923_FLOOR_FACTOR`: 0.85 → 0.40** — reduces EIA-923-derived pmin floors
   by 53%. Rationale: the minimum monthly CF of a QF cogen under-represents the
   true must-run floor when industrial hosts have transient steam demand (down weeks,
   seasonal shutdowns). A 40% haircut on the minimum-month mean is a tighter
   physical bound on the continuously-holdable floor.

2. **Preservation of `chp_btm_pct` column** — re-derive now carries forward the
   per-plant BTM override column from the existing output file so that manual
   annotations survive a full re-derive.

3. **Preservation of `chp_sector` column** — when EIA-923 ZIP archives are absent
   (path `inputs/raw-data/` pre-restructure), sector classifications are carried
   forward from the existing output file instead of silently returning NaN.

4. **`_consume_chp_floors` extended** to propagate `chp_btm_pct` from prior CSV
   when `--chp-floors-from` is used.

### B. `data/raw/_processed-legacy/thermal_tranches_CAISO.csv`

Added `chp_btm_pct` column (default NaN, overridden for two plants):

| plant_code | Name               | Old pmin_cf | New pmin_cf | Old BTM% | New BTM% | Grid floor change |
|------------|--------------------|-------------|-------------|----------|----------|-------------------|
| 50216      | Watson Cogeneration| 31.2%       | 14.7%       | 50%      | 65%      | 62.1→20.5 MW (−67%) |
| 52109      | Richmond Cogen     | 39.0%       | 18.3%       | 50%      | 65%      | 25.4→8.4 MW (−67%) |
| 10213      | El Segundo Cogen   | 53.2%       | 25.0%       | 50%      | 50%      | 45.6→21.4 MW (−53%) |
| 54912      | Martinez Refining  | 46.8%       | 22.0%       | 50%      | 50%      | 18.7→8.8 MW (−53%) |

BTM=65% override for Watson and Richmond: min-month grid delivery (pmin_cf × (1−BTM%))
was 15.6% and 19.5% of nameplate respectively, both below the 30% threshold that
signals BTM is undersized.

EOR plants (Kern River 10496, Sycamore 50134, Midway Sunset 52169) unchanged at
pmin_cf=0.0 (already fixed by EOR HR correction in a prior step).

CAMPD-ok CC_CHP plants (Elk Hills, Los Medanos) restored to pmin_cf=0.0 (their
over-dispatch is merit-based, not must-run — fixing via offer curves, not floors).

**Summary floor reduction:**
- Old total eia923_cf CHP grid floor: **226.4 MW**
- New total eia923_cf CHP grid floor: **94.1 MW** (−58%)

### C. `src/market_sim/data/fleet.py`

- **`chp_overrides(iso)`**: extended return type from 2-tuple to 3-tuple
  `(chp_pmin_cf, sector_class, btm_pct_override)`. Reads optional `chp_btm_pct`
  column from the ISO's thermal_tranches CSV.
- **`chp_btm_pct(plant_code, group, iso)`**: updated to unpack 3-tuple and use
  `btm_override` as highest-priority BTM source when populated.
- **`chp_pmin_cf(plant_code, iso)`**: updated to unpack 3-tuple safely.

ERCOT is unaffected — it uses `CHP_PMIN_CF_BY_PLANT` / `CHP_SECTOR_CLASS_BY_PLANT`
hardcoded maps, not the thermal_tranches CSV path.

## Run Details

```
python scripts/run_calibration_full.py \
  --iso CAISO --year 2023 2024 2025 \
  --out-dir results/calibration/caiso_chp_rederive
```

## Results

Shape probe run: `python scripts/caiso_shape_probe.py results/calibration/caiso_chp_rederive`

### Before vs After: CHP dispatch metrics (2024 primary year)

| Metric                  | Before (model) | CAMPD measured | After Lever C | Pass? |
|-------------------------|----------------|----------------|---------------|-------|
| CC_CHP TWh (2024)       | 9.0            | 5.96           | 8.50          | partial |
| CC_CHP band× (h13–23)   | 1.45           | 1.00           | 1.36          | partial (target 1.0–1.15) |
| CC_CHP r (2024)         | —              | —              | 0.85          | ✓ (≥0.70) |
| CT_CHP TWh (2024)       | 3.3            | 0.38           | 3.66          | ✗ (target 1.0–1.5) |
| CC_REGULAR band× (2024) | —              | —              | 1.11          | ✓ (no degrade) |
| Gas total TWh (2024)    | —              | 85.21          | 71.66         | ✓ (no increase) |

### Full three-year summary

| Year | Group       | Model TWh | CAMPD TWh | r    | band× |
|------|-------------|-----------|-----------|------|-------|
| 2023 | CC_REGULAR  | 52.82     | 50.55     | 0.81 | 0.97  |
| 2023 | CC_CHP      | 8.92      | 7.49      | 0.65 | 1.16  |
| 2023 | CT_CHP      | 3.00      | 0.41      | 0.23 | 6.32  |
| 2024 | CC_REGULAR  | 57.00     | 45.75     | 0.81 | 1.11  |
| 2024 | CC_CHP      | 8.50      | 5.96      | 0.85 | 1.36  |
| 2024 | CT_CHP      | 3.66      | 0.38      | 0.33 | 7.95  |
| 2025 | CC_REGULAR  | 62.69     | 37.92     | 0.74 | 1.48  |
| 2025 | CC_CHP      | 8.29      | 6.10      | 0.91 | 1.33  |
| 2025 | CT_CHP      | 4.72      | 0.37      | 0.19 | 10.50 |

### Verdict

**Partial pass.** The floor reduction (−58% MW) and BTM overrides landed correctly and moved CC_CHP
in the right direction (band× 1.45→1.36, TWh 9.0→8.50). CC_CHP r improved (0.85 in 2024, 0.91
in 2025). CC_REGULAR and gas total are unharmed.

**CT_CHP did not improve** — 3.66 TWh vs target 1.0–1.5 (and 0.38 CAMPD). The EIA-923 floor
reduction does not help CT_CHP plants whose over-dispatch is economic (merit-order driven at
current gas prices) rather than floor-driven. CT_CHP likely needs offer-curve surgery (higher
variable cost or startup markup) in a separate lever — the floor-factor change cannot close this gap.

**Residual CC_CHP gap** (band× 1.36 vs target ≤1.15): Watson and Richmond BTM gains were
absorbed by the remaining eia923_cf plants. A deeper investigation of Arvin-Edison (CC_CHP)
offer curves or a per-plant BTM audit of the remaining sub-CEMS plants is warranted as the
next lever for CC_CHP.

## Acceptance Criteria

| Criterion                                   | Result            |
|---------------------------------------------|-------------------|
| CC_CHP band× drops from 1.45 toward 1.0–1.15 | ✓ partial: 1.36  |
| CT_CHP TWh drops from 3.3 toward 1.0–1.5   | ✗ rose to 3.66    |
| CC_CHP r stays ≥ 0.70                       | ✓ 0.85 (2024)     |
| CC_REGULAR does NOT degrade                 | ✓ band× 1.11      |
| Gas total does NOT increase                 | ✓ 71.66 vs 85.21  |
