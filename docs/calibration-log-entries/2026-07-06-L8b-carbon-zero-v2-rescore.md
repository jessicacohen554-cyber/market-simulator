# calibration-log entry — L-8b carbon-zero v2 re-scores (2026-07-06)

> Standalone entry file (pushed via the GitHub API; the full `docs/calibration-log.md`
> is 343 KB and cannot be inlined through the API). **Fold this section into
> `docs/calibration-log.md` (append at EOF) on the next git-capable session.**

## 2026-07-06 — Carbon-zero ISOs v2 emission-rate no-solve re-scores (PROBES `ercot32/pjm-77/miso-41 v2rescore`; no keeper swap; lane L-8b)

Executes the two cheap follow-ons `emissions-co2-rate-plan-2026-07.md` §9.6
point 1 recommended immediately: re-score the three **carbon-zero** keepers
(ERCOT `ercot32-ordc-total-rtolcap`, PJM `pjm-77-ct-relfloor`, MISO
`miso-41-ct-evening`) under `use_plant_emission_rates_v2=True`, with **NO LP
solve**, and register each as a dashboard PROBE (rule #15) so the improved CO2
coverage is visible without waiting on the CAISO/NYISO/NEISO re-gates (lanes
L-10/L-11/L-15). The `scenarios.py:389` default is **not** flipped — §9.6
sequences that only after all three carbon-priced ISOs re-gate under v2.

**Dispatch/prices/generation are provably byte-identical (verified).**
`use_plant_emission_rates_v2` only sets each generator's `emission_rate_co2`
(`fleet.apply_plant_emission_rates_v2`); in `fleet.assemble_mc` that rate enters
marginal cost **only** through `emission_rate × carbon_price`. ERCOT/PJM/MISO
are absent from `STATE_CARBON_PRICE_BY_ISO` (only CAISO/NYISO/NEISO have a
program) and the backcast config sets `carbon_price=0`, so `resolve_carbon_price`
returns 0 and the term is identically zero → `mc`, dispatch `P[g,t]`, energy-
balance duals (prices), and all generation are byte-identical whatever basis
books `emission_rate_co2`. `nox_price=0` everywhere too (NOx/SO2 reporting-only).
Concretely: each probe's full dispatch payload was verified byte-identical to
the keeper (base64 blobs diffed identical, 1.17M/1.45M/0.91M chars) before the
committed `runs/<id>.js` was compacted to a CO2/fuelmix registration payload
(per-plant hourly heatmaps dropped — identical to the keeper's — to push via
the GitHub API). This is exactly the R2
carbon-zero "re-score = provable no-op" pattern (`co2-keeper-regate-2026-07-05.md`).

**The v2 re-score moves only CO2 accounting.** Persisted per-plant model
generation (ERCOT: bundle `plant_hourly_fit.model_gwh`; PJM/MISO: the committed
dashboard payload `m_ann`, since no PJM/MISO bundle persists
`plant_hourly_fit` — §9.5) re-scored through the v2 **backcast** rate map
(`emission_rates.measured_plant_rates`, `mode="backcast"`: each plant's own
target-year gen-weighted CEMS intensity, tonnes/MWh net):

| ISO | coverage % (23/24/25) | v2 model CO2 Mt (23/24/25) | matched-subset v2 vs eGRID rate Δ% |
|---|---|---|---|
| ERCOT | 100 / 100 / 100 | 159.7 / 156.3 / 159.6 | −0.04 / −0.50 / +0.55 |
| PJM | 97.4 / 97.5 / 97.6 | 268.7 / 273.1 / 304.3 | +2.49 / +2.09 / +1.56 |
| MISO | 90.2 / 91.1 / 93.5 | 235.6 / 231.8 / 269.1 | −0.53 / −2.65 / −3.30 |

- **Coverage** is the headline improvement: for PJM/MISO these are the ISO's
  **first** measured plant-specific CO2 rates (the legacy
  `plant_emission_rates.parquet` is TX-only — pre-v2 every non-ERCOT plant
  booked the generic `heat_rate × FUEL_CO2_FACTOR` default). For ERCOT the v2
  unit-composition mask dissolves the W A Parish mixed coal+gas exclusion → 100%.
- **matched-subset rate Δ%** (v2 vs `egrid.fossil_co2_rate_map` on the *same*
  plants and generation) isolates the pure rate basis: small everywhere (≤3.3%)
  → v2 reproduces the measured CO2 level, no distortion (rule #13). The larger
  raw MISO total gap is the ~7-10% not-yet-CEMS-covered generation, not a rate
  error. Corroboration: the repo's own no-solve scorer
  `score_backcast_shape_emissions.py` gives ERCOT v2 CO2 **9/9 PASS** vs
  CAMPD-actual (160.9/158.3/160.2 model vs 155.9/155.6/157.7).

**The dashboard C5a CO2 verdict is unchanged.** `render_calibration_html.build_payload`
scores model class-TWh × `egrid.fossil_co2_rate_map` (eGRID + CAMPD-v1) class
intensity — it never reads `plant_emission_rates_v2` — so flipping the flag
moves no committed C5a number for a carbon-zero ISO. These probes are diagnostics
of the v2 accounting coverage/level, not verdict changes; `keepers.json` is
untouched.

**Governance.** No LP solve; no keeper bundle, `keepers.json`, or `src/market_sim`
code modified — only new probe artifacts (registry sidecars, `runs/<id>.js`,
`results/calibration/*_v2rescore/` notes, this log entry). No parameter tuned to
any residual (rules #1/#23). Holdouts **2022/H1-2026 untouched** (rule #22): the
v2 artifact carries no 2022/2026 rows and only 2023-2025 were read; D-6 holdout
quarantine reports "no registered bundle carries a year outside [2023,2024,2025]
— quarantine intact" with the three new probes included. (The D-2 forced-energy
recompute FAIL seen locally is on the caiso-51/pjm-77 **keeper** bundles — a
committed-json-vs-floors-rebuild staleness this lane does not touch, present on
main independent of this change.) Bundles: `results/calibration/ercot32_v2rescore`,
`pjm77_v2rescore`, `MISO/miso41_v2rescore`.
