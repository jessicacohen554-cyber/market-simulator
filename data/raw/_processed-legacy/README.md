# _processed-legacy — raw

Derived/intermediate artifacts (leading `_` = "not yet fully migrated to the
`data/clean` curation seam" per `data/README.md`'s convention). Each file has
its own producing script under `scripts/`, all confirmed by `grep -rl
"_processed-legacy"`:

| File(s) | Producing script |
|---|---|
| `bin_assignments_{CAISO,MISO,NEISO,NYISO}.csv` | `scripts/export_iso_bin_assignments.py` — a committed, reviewable snapshot of the per-plant bins `fleet.fleet_to_bins` synthesizes at runtime for non-ERCOT ISOs (ERCOT has a hand-curated `data/raw/reference/custom-bin-assignments.csv` instead) |
| `campd_ct_run_lengths_NYISO.csv` | `scripts/derive_campd_ct_run_lengths.py` |
| `campd_ramp_envelopes_CAISO.csv` | `scripts/derive_campd_ramp_envelopes.py` |
| `cc_capacity_reconcile_{ERCOT,PJM}.csv` | `scripts/derive_cc_capacity_reconcile.py` |
| `cc_committed_pct.csv` | `scripts/derive_cc_committed_pct.py` |
| `coal_mustrun_floors.csv`, `coal_outage_events.csv` | `scripts/derive_reliability_coeffs.py` |
| `coal_supply_{MISO,NEISO,PJM}.csv` | `scripts/derive_coal_supply.py` |
| `coal_takeorpay_{CAISO,ERCOT,MISO,NEISO,NYISO,PJM,SPP}.csv` | `scripts/derive_coal_takeorpay.py` |
| `eia860_chp_by_year.parquet` | `scripts/build_eia860_chp_by_year.py` (per-year EIA-860 plant CHP flag, from the committed `data/raw/eia-860/` releases) |
| `eia923_monthly_fuel_costs.parquet`, `eia923_monthly_generation.parquet` | `scripts/process_f923_fuel_costs.py` (EIA-923 monthly extracts; committed because small, ~16 KB/~225 KB) |
| `ercot_dam_offer_hrmult_summary.csv`, `ercot_offer_multiplier_summary.csv` | `scripts/derive_dam_offer_hrmults.py` / `scripts/analyze_dam_offer_multipliers.py` |
| `ercot_resource_settlement_crosswalk.csv` | `scripts/parse_ercot_dam_offers.py` |
| `fossil_co2_rates.{csv,parquet}` | `scripts/derive_fossil_co2_rates.py` |
| `gas_takeorpay_ERCOT.csv` | `scripts/derive_gas_takeorpay.py` |
| `offer_curve_jacobian.csv` | `scripts/derive_offer_curve_jacobian.py` (its cache file is gitignored; the CSV itself is committed) |
| `parasitic_load_factors.{csv,parquet}` | `scripts/derive_parasitic_load.py` |
| `plant_emission_rates.{csv,parquet}`, `plant_emission_rates_v2.{csv,parquet}` | `scripts/derive_plant_emissions.py` / `scripts/derive_plant_emissions_v2.py` |
| `thermal_tranches_{CAISO,MISO,NEISO,NYISO,PJM}.csv` | `scripts/derive_thermal_tranches.py` |

All of the above are **derived from other committed raw sources**
(EIA-860/923, CAMPD, model config), not independent upstream downloads —
regenerate by re-running the listed script, not by re-fetching from an
external source. `eia923_monthly_fuel_costs.parquet` /
`eia923_monthly_generation.parquet` now span 2018–2026 (2018–2021 landed
2026-07-08, data-register intake, `docs/data-register-2026-07.md`); see
`data/raw/campd-unit-level/README.md` for the resulting still-open
`derive_parasitic_load.py` v2 re-derivation follow-up (source gap closed,
re-derive not yet run).

**Consumers:** `scripts/curate_chp_btm_share.py`,
`src/market_sim/data/{coal.py,fuel.py,eia923.py,chp.py,fleet.py}`.
