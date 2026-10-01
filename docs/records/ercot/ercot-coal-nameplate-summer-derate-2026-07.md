# ERCOT coal net-summer capacity derate (`coal_nameplate_summer_derate`)

**Thread:** ERCOT coal availability / online-capability wedge (ercot51+), coal limb.
**Status:** mechanism built + unit-tested; A/B and 2023–2025 bundle in progress.
**Date:** 2026-07-09. ERCOT-only in practice (rule 24); EIA-860 lookup is ISO-agnostic.

## Problem

The `ercot46_clock_steamgas` keeper over-commits ERCOT coal in **shape** (not
energy level): the model holds PRB and lignite flatter and higher than the real
fleet, with far too many high-CF hours. Reproduced from the committed control
(`_diag_ercot51_baseline`, keeper config, surface off), 2023 P1 vs the shared
CAMPD actuals:

| class | cap | model CF | model hrs>0.8 | model TWh | actual CF | actual hrs>0.8 | actual TWh |
|---|---|---|---|---|---|---|---|
| PRB | 11.4 GW | 0.50 | 1459 | 50.0 | 0.47 | 642 | 47.0 |
| lignite | 2.6 GW | 0.77 | 4807 | 17.3 | 0.70 | 3024 | 15.7 |

Robust across 2023–2025: coal is over-committed by **~1 GW in the tightest
(demand ≥ p95) hours every year** (+997 / +1067 / +1004 MW), and coal energy
runs over the measured C1 line (PRB +3.0 / +0.8 / +1.1 TWh; lignite +1.6 / +1.0
/ +0.6 TWh). The real fleet cycled harder; the model holds coal near baseload.

## Root cause (owner-directed): coal is rated at NAMEPLATE, not net-summer

The model's coal `pmax` is the CAMPD-bin / EIA-860 **nameplate** capacity, and
coal — unlike CC/CT — carries **no net-summer derate** ("COAL / ST_GAS carry no
existing summer derate", `fleet.py` availability loop). An old coal steam unit
physically cannot sustain nameplate in the summer: condenser back-pressure and
cooling-water-temperature limits pull its sustainable rating down to its
published **EIA-860 net-summer capacity**.

Per-plant EIA-860 (Operable, "Conventional Steam Coal" / "Coal IGCC") net-summer
/ nameplate, vs the CEMS-demonstrated summer maximum CF (Jun–Sep, from CAMPD):

| plant | net-summer/NP | CEMS summer max/NP |
|---|---|---|
| Oak Grove (6180) | 0.952 | 0.937 |
| Major Oak (7030) | 0.873 | 0.877 |
| San Miguel (6183) | 0.954 | 0.940 |
| Fayette (6179) | 0.956 | 0.921 |
| J K Spruce (7097) | 0.904 | 0.893 |
| Limestone (298) | 0.913 | 0.820 |
| Parish (3470) | 0.919 | (mixed plant; CEMS incl. gas) |
| Sandy Creek (56611) | 0.925 | 0.980 |
| Martin Lake (6146) | 1.032 → 1.0 | 0.954 |
| Coleto Creek (6178) | 1.052 → 1.0 | 1.011 |

The baseload units (Oak Grove, Major Oak, San Miguel, Fayette, Spruce) top out
in CEMS **at or below net-summer, never near nameplate** — the measured data
confirms the published rating. The model, capping only at nameplate, lets these
units run ~5% higher than they physically can in summer.

## Why this is admissible (and NOT the rejected temp-derate)

- **Published EIA-860 rating** (rule 15: measured replaces estimate). Regenerates
  for any forward year and responds to changed conditions (a re-rated unit gets a
  new net-summer number), so it is rule-11 admissible in **both** backcast and
  forecast — never fitted to a residual.
- **Exact coal analogue of `cc_nameplate_summer_derate`** (same EIA-860 source,
  same summer-only multiplicative application) that CC/CT already use and coal
  alone was omitted from.
- **Distinct from `temp_dependent_derate`** (rejected with cause for ERCOT
  2026-07-09): that was an *incremental literature-slope cut BELOW* net-summer,
  refuted because the gas fleet's measured hot-hour slope is ≈0. This brings coal
  *down to* its net-summer rating, which the per-plant CEMS summer maxima
  above confirm the fleet actually tops out at.
- **Distinct from the 2026-07-08 Lever B rejection**, which tested a *seasonal*
  derate (summer depressed vs shoulder) and correctly found none. The net-summer
  vs nameplate gap is a year-round rating difference, not a seasonal shape — Lever
  B never tested it.

Plants rated at/above nameplate (Martin Lake, Coleto Creek) clamp to 1.0 (no
derate). The mechanism only reduces capacity, only in summer; it can never loosen
the fleet.

## Implementation

- `ScenarioConfig.coal_nameplate_summer_derate: bool = False` (default off).
- `fleet.coal_summer_capacity()` / `fleet.coal_summer_derate_ratio(plant_code)` —
  EIA-860 Operable coal-tech net_summer/nameplate, clamped to (0, 1]; the coal
  mirror of `cc_summer_capacity` / `cc_summer_derate_ratio`.
- Applied in the availability loop's COAL block: `availability[g, summer] *=
  ratio`. Threaded through `run_calibration_full.solve_and_persist` and
  `run_calibration.run_year` beside `cc_nameplate_summer_derate`.
- Tests: `tests/test_fleet.py::TestCoalNameplateSummerDerate`.

## Scope / honest limits

The net-summer derate is ~5% of coal capacity (~0.7 GW fleet ceiling). It targets
the robust tight-hour over-commitment and moves coal energy toward the measured
C1 line, but it is **one limb**: the FINDING §3 online-capability wedge is ~3.2 GW
(of which ~1.7–2 GW is the mispriced peak band, addressed by the G-22 §8 offer
surface, kept default-off). Expect the net-summer derate to improve C1 and thin
the wedge, not to close the C3c tail alone. Test the offer surface ON again after
the coal fix.
