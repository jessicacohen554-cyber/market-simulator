# v2 emission-rate no-solve re-score — PJM keeper `2026-07-05-pjm-77-ct-relfloor`

**Date:** 2026-07-06 · **Lane:** L-8b · **Type:** PROBE (rule 15) — NOT a keeper swap.
**Decision memo:** `docs/handoffs/emissions-co2-rate-plan-2026-07.md` §9.6.

## Claim: dispatch / prices / generation are byte-identical (no LP solve)

`use_plant_emission_rates_v2` only sets each generator's `emission_rate_co2`
(`fleet.apply_plant_emission_rates_v2`). In the LP objective
(`fleet.assemble_mc`) that rate enters marginal cost **only** through
`emission_rate × carbon_price`. For PJM there is no state carbon program
(`STATE_CARBON_PRICE_BY_ISO` registers only CAISO/NYISO/NEISO) and the backcast
calibration config uses `carbon_price = 0`, so `resolve_carbon_price` returns 0 and
the `emission_rate × carbon_price` term is identically zero. Therefore `mc`, the LP
dispatch `P[g,t]`, the energy-balance duals (prices), and all generation are
**provably byte-identical** whether `emission_rate_co2` is booked from the legacy
artifact, v2, or the generic fuel-class default. `nox_price = 0` everywhere too, so
the NOx/SO2 rates v2 also carries are reporting-only. The committed `runs/2026-07-06-pjm-77-v2rescore-probe.js`
carries a **compact** CO2/fuelmix registration payload — the per-plant panels are omitted (their data is identical to the keeper's); the
full payload was verified byte-identical to the keeper before compaction (only
the JS run-id key differed), the concrete proof that no dispatch/price/generation
number moved.

## What the v2 re-score changes: CO2 accounting only

Persisted per-plant model generation source: `committed dashboard payload m_ann (per-plant model annual GWh)`.
The v2 rate is the mode-aware **backcast** source (`emission_rates.measured_plant_rates`,
`mode='backcast'`): each plant's own **target-year** measured intensity, gen-weighted
over its CEMS units (tonnes CO2 / MWh net).

| year | model fossil GWh | coverage % | v2 model CO2 (Mt) | matched-subset v2 vs eGRID rate Δ% |
|---|---|---|---|---|
| 2023 | 480060 | 97.4 | 268.71 | +2.49% |
| 2024 | 501489 | 97.5 | 273.11 | +2.09% |
| 2025 | 532479 | 97.6 | 304.28 | +1.56% |

- **Coverage** = share of model fossil GWh now carrying a *measured* plant-specific
  v2 CO2 rate. For PJM/MISO these are the ISO's **first** measured plant rates (the
  legacy `plant_emission_rates.parquet` is TX-only; pre-v2 every non-ERCOT plant booked
  the generic `heat_rate × FUEL_CO2_FACTOR` default). For ERCOT the v2 unit-composition
  mask dissolves the W A Parish mixed coal+gas exclusion → 100%.
- **matched-subset rate Δ%** compares the v2 rate basis against the
  `egrid.fossil_co2_rate_map` (eGRID + CAMPD-v1) basis on the *same* plants and the
  *same* generation, so it isolates the pure rate-basis difference (small everywhere
  — v2 reproduces the measured CO2 level, no distortion; rule 13).

## Dashboard C5a verdict is unchanged

The dashboard/`calibration_verdict` C5a CO2 gate scores model class-TWh ×
`egrid.fossil_co2_rate_map` class intensity vs the same eGRID actual
(`render_calibration_html.build_payload`, `egrid.fossil_co2_rate_map`). It never reads
`plant_emission_rates_v2`, so flipping the flag does not move any committed C5a number
for a carbon-zero ISO. This probe is a **diagnostic** of the v2 accounting coverage/
level, not a verdict change — exactly the §9.6 point-1 no-solve re-score.

## Governance

No LP solve. No keeper bundle, `keepers.json`, or `src/market_sim` code modified. No
parameter tuned to any residual (rules #1/#23). Holdouts **2022 / H1-2026 untouched**
(rule #22): the v2 artifact contains no 2022/2026 rows and only 2023-2025 were read.
The `scenarios.py` default flip stays deferred to §9.6's sequencing (after CAISO/
NYISO/NEISO re-gate under v2 — lanes L-10/L-11/L-15), NOT this lane.
