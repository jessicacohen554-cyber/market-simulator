# NYISO 38 — unified-engine CT/ST continuous-ramp migration (PROBE, NOT-YET)

## What this run is

The keeper-34 (`2026-06-27-nyiso-34-st-tempfloor`) migration off the legacy
per-ISO hardcoded downstate CT/ST reliability floors and onto the unified
registry-driven engine (`--reliability-floor`,
`reliability_floor_coeffs_NYISO.csv`, `transmission.inject_reliability_floor`),
**plus a new structural capability**: a continuous temperature-ramp family in
the floor engine.

### Engine change (kept — correct structure, CLAUDE.md #1)

`inject_reliability_floor` now reads limbs that share a non-empty `ramp_group`
as the `(threshold, floor_pct)` knots of one piecewise-linear commitment curve
and interpolates the floor in the driver temperature (clamped flat outside the
knot range). This reproduces the legacy `clip(base + slope·(T−T0), base, cap)`
downstate CT/ST floor **exactly**, instead of the v-series step that fired one
high `floor_pct` on every evening above 25 °C (the documented over-dispatch).

Downstate CT ramp knots (legacy coefficients, `derive_nyiso_ct_reliability_floor`):
`(25 °C, 0.132) → (35.22 °C, 0.679)`, evening HB14-21, pro-rata, NYC + Long_Island.
ST hot-evening limbs likewise encoded as ramps (NYC/LI/Capital_Hudson).

### Config

Keeper-34 exact: same offer curve, `gas_hub_basis_daily` + `gas_hub_basis_overlay`
(the real Transco Z6 NY daily spot + measured citygate basis), NYISO zonal gas
basis, local-self-supply / firm-imports / import-reconciliation, energy+reserve
co-optimization, monthly gas actuals.

## Result: C1 HARD FAIL (NOT-YET)

| year | class | model | actual | miss | band | verdict |
|------|-------|-------|--------|------|------|---------|
| 2023 | CC_REGULAR | 37.68 | 35.07 | +2.61 | ±1.27 | FAIL |
| 2023 | ST_GAS | 7.35 | 8.65 | −1.30 | ±1.27 | FAIL |
| 2024 | ST_GAS | 8.89 | 10.83 | −1.94 | ±1.35 | FAIL |

(2025 gas classes SKIPPED — preliminary EIA-923 vintage.)

## Root cause — NOT the floor mechanism

The continuous ramp (and gas-hub-basis flags) barely move 2024 ST_GAS
(8.95 → 8.89 TWh) because the ramp only lifts the floor on hot summer evenings,
where ST already dispatches economically, so the floor does not bind. The
persistent base binds on idle hours but produces the same forced energy as the
legacy did (identical coefficients + fleet ⇒ identical `frac·pmax·availability`).

2024 ST_GAS dispatch by zone (this run):

| zone | TWh | CF | persistent floor (base_24h) |
|------|-----|----|----|
| NYC | 3.32 | 0.13 | 0.391 (availability-limited to ~0.33 — Astoria/Arthur Kill idle) |
| Long_Island | 5.08 | 0.28 | 0.289 |
| Capital_Hudson | 0.30 | 0.02 | **0.0** (no floor — data shows CH steam is not temp-committed) |
| Upstate_West | 0.18 | — | — |

The gap is **Capital_Hudson ST**, which has `base_24h = 0` in the measured data
and so runs purely on economics. Keeper 34 (an unrecoverable *dirty* solve at
sha `180d579` + intervening code evolution) let CH ST clear ~1.2 TWh; the
current merit order squeezes it to 0.30. This is an economic merit-order shift,
not a floor-encoding difference.

## Why it is not closed here

- **Option (c) — add a CH persistent base:** forbidden. The CH data gives
  `base_ev = base_24h = 0`; a hand base of ~0.10 to add ~1 TWh is a
  residual-tuned input with no forward analogue (CLAUDE.md #9/#11).
- **Offer-curve recalibration:** forbidden as "do no harm" migration —
  residual-fitting (CLAUDE.md #9).
- The continuous-ramp engine is the correct structure and **stays** even though
  it does not improve the fit (CLAUDE.md #1).

## Recommended follow-up (out of migration scope)

Investigate the Capital_Hudson ST economic squeeze as a genuine merit-order
calibration bug (CLAUDE.md #11: keep the accurate general engine, fix the real
root cause) — why current-codebase economics under-run CH steam vs the
keeper-34 snapshot (upstate CC competition, CH zonal gas basis, import
displacement). Do not bury it back inside a fitted floor.
