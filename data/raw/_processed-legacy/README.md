# _processed-legacy — raw

Derived/intermediate artifacts (leading `_` = "not yet fully migrated to the
`data/clean` curation seam" per `data/README.md`'s convention). Each file has
its own producing script under `scripts/`, all confirmed by `grep -rl
"_processed-legacy"`:

| File(s) | Producing script |
|---|---|
| `bin_assignments_{CAISO,MISO,NEISO,NYISO}.csv` | `scripts/export_iso_bin_assignments.py` — a committed, reviewable snapshot of the per-plant bins `fleet.fleet_to_bins` synthesizes at runtime for non-ERCOT ISOs (ERCOT has a hand-curated `data/raw/reference/custom-bin-assignments.csv` instead) |
| `campd_ct_heat_rates_NYISO.csv` (+ `_units.csv`) | `scripts/data/derive_campd_ct_heat_rates.py` — per-plant CAMPD-measured **loaded** heat rate (MMBtu/net MWh) for the `CT_PEAKER` class, the rule-14 replacement for eGRID's plant-average annual rate; method and provenance in `SOURCES_campd_ct_heat_rates.md` |
| `egrid_family_heat_rates_NYISO.csv` (+ `_vintages.csv`) | `scripts/data/derive_egrid_family_heat_rates.py` — eGRID PRIME-MOVER-FAMILY heat rates (Σ `UNT.HTIAN` / Σ `GEN.GENNTAN` per family, the same vintage the plant-grain join reads) at plants hosting ≥ 2 prime-mover families, consumed under `ScenarioConfig.egrid_family_heat_rates` (default off) by `fleet/eia860._apply_egrid_family_heat_rates`; the companion `_vintages.csv` records every on-disk vintage's value and is never applied (nyiso-184, `PREREG-nyiso184-stgas-heat-rate-basis.md` §3 R1) |
| `egrid_steam_collapse_heat_rates_NYISO.csv` | `scripts/data/derive_egrid_steam_collapse_heat_rates.py` — the CT-heat identity `PLHTIAN / Σ GENNTAN(CT) / (1 + the plant's own T1-clean median steam share)` for combined cycles whose eGRID steam-generator filing collapsed (T1 zero test, or a steam share below the plant's own record by more than the record's range, with the CT filing intact), one row per (plant, vintage) over every on-disk eGRID vintage with the admissibility record; only `applied & admitted` rows are read, under `ScenarioConfig.egrid_steam_collapse_heat_rates` (default off) by `fleet/eia860.apply_egrid_steam_collapse_heat_rates` (nyiso-189, `PREREG-nyiso189-steam-collapse-identity-ab.md`) |
| `campd_ct_run_lengths_NYISO.csv` | `scripts/derive_campd_ct_run_lengths.py` |
| `campd_ramp_envelopes_CAISO.csv` | `scripts/derive_campd_ramp_envelopes.py` |
| `cc_capacity_reconcile_{ERCOT,PJM}.csv` | `scripts/derive_cc_capacity_reconcile.py` |
| `cc_committed_pct.csv` | `scripts/derive_cc_committed_pct.py` |
| `coal_mustrun_floors.csv`, `coal_outage_events.csv` | `scripts/derive_reliability_coeffs.py` |
| `coal_supply_{MISO,NEISO,PJM,SPP,SOCO}.csv` | `scripts/data/derive_coal_supply.py` — per-plant coal rank (`prb` / `bituminous` / `lignite` / `waste`) from EIA-923, resolver step 2 of `data.coal.coal_supply_class`. **Census provenance (`--census-vintage`) matters and is per-ISO:** the census — which plants get a row — reads the canonical EIA-860 snapshot by default, and `--census-vintage <years>` UNIONs in each solved year's own `vintage_<year>/` release so a plant that burned coal in a solved year but was re-fuelled by the snapshot's vintage still gets a rank instead of a bare `COAL` class the EIA-923 benchmark has no row for (rule 14 `[R-ACCURATE]`). **SPP was derived with `--census-vintage 2023 2024 2025`** (lane SPP-62, `docs/handoffs/PRECOMMIT-spp-62-2026-09-10.md`); **SOCO was derived with `--census-vintage 2023 2024 2025`** (lane SOCO-40, 2026-09-16, on the owner's in-session instruction "Coal should be split into types. Completely eliminate the single coal class" — 6 rows: Barry 3 / E C Gaston 26 / Bowen 703 `bituminous`, Miller 6002 / Daniel 6073 / Scherer 6257 `prb`; every SOCO coal plant resolves, bare `COAL` = 0.0 MW; `docs/handoffs/PRECOMMIT-soco-40-2026-09-16.md` §11); MISO / NEISO / PJM were derived on the canonical census alone. **Do not re-derive MISO or PJM at HEAD without first reconciling the lost receipts source**: the raw `f923_*.zip` corpus those two were built from is no longer under `data/raw`, so a re-derive at HEAD re-ranks 5 PJM and 10 MISO plants with no code change at all (SPP-62 §5). |
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
