# Parameter Citation Registry

_Generated 2026-05-16. Every numeric input to the model traces to a primary source here._

This document is the human-readable companion to `frontend/data/parameters.json` (the machine-readable registry, consumed by the parameter-citation browser). Both are produced from one source so they stay consistent. `scripts/validate_parameters.py` fails CI if any constant in `src/market_sim/config/constants.py` or any `ScenarioConfig` default lacks an entry.

## How `param_id` is derived

- A module-level constant in `constants.py` becomes its lower-cased name (e.g. `GAS_PRICE_ESCALATION` -> `gas_price_escalation`).
- Nested dicts with string keys are flattened with dots (e.g. `HEAT_RATE_BINS["gas_cc"]["h_class"]` -> `heat_rate_bins.gas_cc.h_class`).
- A dict whose keys are all years (e.g. a carbon-price trajectory) is treated as a single leaf; its value is the full trajectory.
- `ScenarioConfig` dataclass defaults are prefixed with `scenario.` (e.g. `scenario.discount_rate`).

**Totals:** 125 parameters | 33 model-sourced | 13 flagged stale (source older than 3 years).

## Structural

| param_id | value | unit | tier | source | date | page / table | old repo location | notes |
|---|---|---|---|---|---|---|---|---|
| `storage_tiebreaker_epsilon` | 0.001 | $/MWh | 0 | Market simulator model design decision | 2026-05 | model-methodology-spec.md / market-sim-build-plan.md | — | Small cost on charge+discharge to prevent degenerate simultaneous cycling in the LP. |
| `hours_per_year` | 8760 | hours | 0 | Market simulator model design decision | 2026-05 | model-methodology-spec.md / market-sim-build-plan.md | — | Full annual hourly resolution; no representative days. |
| `start_year` | 2026 | year | 0 | Market simulator model design decision | 2026-05 | model-methodology-spec.md / market-sim-build-plan.md | — | First simulated year. |
| `end_year` | 2050 | year | 0 | Market simulator model design decision | 2026-05 | model-methodology-spec.md / market-sim-build-plan.md | — | Last simulated year. |
| `scenario.weather_year` | 2024 | year | 0 | Market simulator model design decision | 2026-05 | model-methodology-spec.md / market-sim-build-plan.md | — | Default weather/profile year; aligns with EIA-930 hourly data availability. |
| `scenario.iso` | ERCOT | - | 0 | Market simulator model design decision | 2026-05 | model-methodology-spec.md / market-sim-build-plan.md | — | Default ISO for a single-scenario run. |
| `scenario.hours` | 8760 | hours | 0 | Market simulator model design decision | 2026-05 | model-methodology-spec.md / market-sim-build-plan.md | — | Hours simulated per year. |

## Supply Stack

| param_id | value | unit | tier | source | date | page / table | old repo location | notes |
|---|---|---|---|---|---|---|---|---|
| `heat_rate_bins.gas_cc.h_class` | 6.3 | MMBtu/MWh | 2 | EIA Electric Power Annual 2022, Table 8.2 | 2023-10 | Table 8.2 — Average Tested Heat Rates by Prime Mover and Fuel Type | `lmp_engine.py:85-113 (EFFICIENCY_BINS)` | Average tested heat rate for newest H-class combined-cycle units; lower means higher thermal efficiency. |
| `heat_rate_bins.gas_cc.f_class` | 6.7 | MMBtu/MWh | 2 | EIA Electric Power Annual 2022, Table 8.2 | 2023-10 | Table 8.2 — Average Tested Heat Rates by Prime Mover and Fuel Type | `lmp_engine.py:85-113 (EFFICIENCY_BINS)` | Average tested heat rate for F-class combined-cycle units; lower means higher thermal efficiency. |
| `heat_rate_bins.gas_cc.older` | 7.5 | MMBtu/MWh | 2 | EIA Electric Power Annual 2022, Table 8.2 | 2023-10 | Table 8.2 — Average Tested Heat Rates by Prime Mover and Fuel Type | `lmp_engine.py:85-113 (EFFICIENCY_BINS)` | Average tested heat rate for legacy combined-cycle units; lower means higher thermal efficiency. |
| `heat_rate_bins.gas_ct.aero` | 9.0 | MMBtu/MWh | 2 | EIA Electric Power Annual 2022, Table 8.2 | 2023-10 | Table 8.2 — Average Tested Heat Rates by Prime Mover and Fuel Type | `lmp_engine.py:85-113 (EFFICIENCY_BINS)` | Average tested heat rate for aeroderivative combustion turbines; lower means higher thermal efficiency. |
| `heat_rate_bins.gas_ct.frame` | 10.5 | MMBtu/MWh | 2 | EIA Electric Power Annual 2022, Table 8.2 | 2023-10 | Table 8.2 — Average Tested Heat Rates by Prime Mover and Fuel Type | `lmp_engine.py:85-113 (EFFICIENCY_BINS)` | Average tested heat rate for heavy-frame combustion turbines; lower means higher thermal efficiency. |
| `heat_rate_bins.gas_ct.older` | 11.5 | MMBtu/MWh | 2 | EIA Electric Power Annual 2022, Table 8.2 | 2023-10 | Table 8.2 — Average Tested Heat Rates by Prime Mover and Fuel Type | `lmp_engine.py:85-113 (EFFICIENCY_BINS)` | Average tested heat rate for legacy combustion turbines; lower means higher thermal efficiency. |
| `heat_rate_bins.coal.supercritical` | 8.8 | MMBtu/MWh | 2 | EIA Electric Power Annual 2022, Table 8.2 | 2023-10 | Table 8.2 — Average Tested Heat Rates by Prime Mover and Fuel Type | `lmp_engine.py:85-113 (EFFICIENCY_BINS)` | Average tested heat rate for supercritical steam units; lower means higher thermal efficiency. |
| `heat_rate_bins.coal.subcritical` | 10.0 | MMBtu/MWh | 2 | EIA Electric Power Annual 2022, Table 8.2 | 2023-10 | Table 8.2 — Average Tested Heat Rates by Prime Mover and Fuel Type | `lmp_engine.py:85-113 (EFFICIENCY_BINS)` | Average tested heat rate for subcritical steam units; lower means higher thermal efficiency. |
| `heat_rate_bins.coal.older` | 10.8 | MMBtu/MWh | 2 | EIA Electric Power Annual 2022, Table 8.2 | 2023-10 | Table 8.2 — Average Tested Heat Rates by Prime Mover and Fuel Type | `lmp_engine.py:85-113 (EFFICIENCY_BINS)` | Average tested heat rate for legacy subcritical steam units; lower means higher thermal efficiency. |
| `vom.gas_cc` | 2.0 | $/MWh | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 — Variable operations & maintenance cost | — | Non-fuel variable operating cost by fuel type. |
| `vom.gas_ct` | 3.5 | $/MWh | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 — Variable operations & maintenance cost | — | Non-fuel variable operating cost by fuel type. |
| `vom.coal` | 4.5 | $/MWh | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 — Variable operations & maintenance cost | — | Non-fuel variable operating cost by fuel type. |
| `vom.nuclear` | 2.5 | $/MWh | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 — Variable operations & maintenance cost | — | Non-fuel variable operating cost by fuel type. |
| `vom.wind` | 0.0 | $/MWh | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 — Variable operations & maintenance cost | — | Non-fuel variable operating cost by fuel type. |
| `vom.solar` | 0.0 | $/MWh | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 — Variable operations & maintenance cost | — | Non-fuel variable operating cost by fuel type. |
| `scenario.fixed_om_gas_cc` | 12.0 | $/kW-yr | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | — | Fixed O&M for combined-cycle gas. |
| `scenario.fixed_om_gas_ct` | 8.0 | $/kW-yr | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | — | Fixed O&M for combustion-turbine gas. |
| `scenario.fixed_om_coal` | 40.0 | $/kW-yr | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | — | Fixed O&M for coal steam. |

## Emissions

| param_id | value | unit | tier | source | date | page / table | old repo location | notes |
|---|---|---|---|---|---|---|---|---|
| `co2_rates.gas_cc.h_class` | 0.36 | tCO2/MWh | 2 | EPA eGRID2022 | 2024-01 | eGRID2022 unit-level emission rates | `lmp_engine.py (CO2_RATES)` | Derived from heat rate x fuel emission factor; bins mirror HEAT_RATE_BINS. |
| `co2_rates.gas_cc.f_class` | 0.38 | tCO2/MWh | 2 | EPA eGRID2022 | 2024-01 | eGRID2022 unit-level emission rates | `lmp_engine.py (CO2_RATES)` | Derived from heat rate x fuel emission factor; bins mirror HEAT_RATE_BINS. |
| `co2_rates.gas_cc.older` | 0.43 | tCO2/MWh | 2 | EPA eGRID2022 | 2024-01 | eGRID2022 unit-level emission rates | `lmp_engine.py (CO2_RATES)` | Derived from heat rate x fuel emission factor; bins mirror HEAT_RATE_BINS. |
| `co2_rates.gas_ct.aero` | 0.51 | tCO2/MWh | 2 | EPA eGRID2022 | 2024-01 | eGRID2022 unit-level emission rates | `lmp_engine.py (CO2_RATES)` | Derived from heat rate x fuel emission factor; bins mirror HEAT_RATE_BINS. |
| `co2_rates.gas_ct.frame` | 0.6 | tCO2/MWh | 2 | EPA eGRID2022 | 2024-01 | eGRID2022 unit-level emission rates | `lmp_engine.py (CO2_RATES)` | Derived from heat rate x fuel emission factor; bins mirror HEAT_RATE_BINS. |
| `co2_rates.gas_ct.older` | 0.65 | tCO2/MWh | 2 | EPA eGRID2022 | 2024-01 | eGRID2022 unit-level emission rates | `lmp_engine.py (CO2_RATES)` | Derived from heat rate x fuel emission factor; bins mirror HEAT_RATE_BINS. |
| `co2_rates.coal.supercritical` | 0.88 | tCO2/MWh | 2 | EPA eGRID2022 | 2024-01 | eGRID2022 unit-level emission rates | `lmp_engine.py (CO2_RATES)` | Derived from heat rate x fuel emission factor; bins mirror HEAT_RATE_BINS. |
| `co2_rates.coal.subcritical` | 1.0 | tCO2/MWh | 2 | EPA eGRID2022 | 2024-01 | eGRID2022 unit-level emission rates | `lmp_engine.py (CO2_RATES)` | Derived from heat rate x fuel emission factor; bins mirror HEAT_RATE_BINS. |
| `co2_rates.coal.older` | 1.08 | tCO2/MWh | 2 | EPA eGRID2022 | 2024-01 | eGRID2022 unit-level emission rates | `lmp_engine.py (CO2_RATES)` | Derived from heat rate x fuel emission factor; bins mirror HEAT_RATE_BINS. |
| `nox_rates.gas_cc` | 0.0001 | tNOx/MWh | 2 | EPA Clean Air Markets Program Data (CEMS), 2022 | 2023-02 | Hourly emissions, 2022 annual rollup | `egrid_emission_rates.json` | Fleet-average NOx emission rate from continuous emissions monitoring. **[STALE]** |
| `nox_rates.gas_ct` | 0.0003 | tNOx/MWh | 2 | EPA Clean Air Markets Program Data (CEMS), 2022 | 2023-02 | Hourly emissions, 2022 annual rollup | `egrid_emission_rates.json` | Fleet-average NOx emission rate from continuous emissions monitoring. **[STALE]** |
| `nox_rates.coal` | 0.0015 | tNOx/MWh | 2 | EPA Clean Air Markets Program Data (CEMS), 2022 | 2023-02 | Hourly emissions, 2022 annual rollup | `egrid_emission_rates.json` | Fleet-average NOx emission rate from continuous emissions monitoring. **[STALE]** |

## Reliability

| param_id | value | unit | tier | source | date | page / table | old repo location | notes |
|---|---|---|---|---|---|---|---|---|
| `gas_availability_factor.ERCOT` | 0.83 | fraction | 2 | NERC Generating Availability Data System (GADS), 2018-2022 | 2023-08 | GADS five-year fleet-average availability statistics | `lmp_engine.py` | ERCOT gas fleet deterministic availability derate (Pmax multiplier). |
| `gas_availability_factor.CAISO` | 0.88 | fraction | 2 | NERC Generating Availability Data System (GADS), 2018-2022 | 2023-08 | GADS five-year fleet-average availability statistics | `lmp_engine.py` | CAISO gas fleet deterministic availability derate (Pmax multiplier). |
| `nuclear_monthly_cf.ERCOT` | [0.93, 0.93, 0.9, 0.9, 0.92, 0.93, 0.93, 0.93, 0.91, 0.9, 0.92, 0.93] | fraction (Jan-Dec) | 2 | NRC / IAEA Power Reactor Information System (PRIS), 2019-2023 | 2024-01 | U.S. reactor monthly capacity factors, 2019-2023 | `pipeline_config.py` | Twelve monthly capacity factors; spring/fall dips reflect scheduled refueling outages. |
| `nuclear_monthly_cf.CAISO` | [0.93, 0.92, 0.91, 0.9, 0.91, 0.93, 0.93, 0.93, 0.92, 0.9, 0.91, 0.93] | fraction (Jan-Dec) | 2 | NRC / IAEA Power Reactor Information System (PRIS), 2019-2023 | 2024-01 | U.S. reactor monthly capacity factors, 2019-2023 | `pipeline_config.py` | Twelve monthly capacity factors; spring/fall dips reflect scheduled refueling outages. |
| `eford.gas_cc` | 0.05 | fraction | 2 | NERC Generating Availability Data System (GADS), 2018-2022 | 2023-08 | GADS five-year fleet-average availability statistics | — | Equivalent forced outage rate (demand) by technology class. |
| `eford.gas_ct` | 0.06 | fraction | 2 | NERC Generating Availability Data System (GADS), 2018-2022 | 2023-08 | GADS five-year fleet-average availability statistics | — | Equivalent forced outage rate (demand) by technology class. |
| `eford.coal` | 0.08 | fraction | 2 | NERC Generating Availability Data System (GADS), 2018-2022 | 2023-08 | GADS five-year fleet-average availability statistics | — | Equivalent forced outage rate (demand) by technology class. |
| `eford.nuclear` | 0.03 | fraction | 2 | NERC Generating Availability Data System (GADS), 2018-2022 | 2023-08 | GADS five-year fleet-average availability statistics | — | Equivalent forced outage rate (demand) by technology class. |
| `scenario.voll` | 5000.0 | $/MWh | 0 | Public Utility Commission of Texas / ERCOT Nodal Protocols | 2023-01 | Value of Lost Load (system-wide offer cap basis) | — | ERCOT value of lost load (system-wide offer cap basis); CAISO ISOConfig uses 2000. **[STALE]** |

## Demand

| param_id | value | unit | tier | source | date | page / table | old repo location | notes |
|---|---|---|---|---|---|---|---|---|
| `demand_growth_rates.ERCOT.low` | 0.01 | fraction/yr | 1 | ERCOT Capacity, Demand and Reserves (CDR) Report | 2024-05 | May 2024 CDR — load forecast and interconnection data | `pipeline_config.py` | low annual demand growth path; planning forecast, not observed history. **[MODELED]** |
| `demand_growth_rates.ERCOT.mid` | 0.02 | fraction/yr | 1 | ERCOT Capacity, Demand and Reserves (CDR) Report | 2024-05 | May 2024 CDR — load forecast and interconnection data | `pipeline_config.py` | mid annual demand growth path; planning forecast, not observed history. **[MODELED]** |
| `demand_growth_rates.ERCOT.high` | 0.035 | fraction/yr | 1 | ERCOT Capacity, Demand and Reserves (CDR) Report | 2024-05 | May 2024 CDR — load forecast and interconnection data | `pipeline_config.py` | high annual demand growth path; planning forecast, not observed history. **[MODELED]** |
| `demand_growth_rates.CAISO.low` | 0.005 | fraction/yr | 1 | California Energy Commission Integrated Energy Policy Report (IEPR) 2023 | 2024-02 | 2023 IEPR California electricity demand forecast | `pipeline_config.py` | low annual demand growth path; planning forecast, not observed history. **[MODELED]** |
| `demand_growth_rates.CAISO.mid` | 0.012 | fraction/yr | 1 | California Energy Commission Integrated Energy Policy Report (IEPR) 2023 | 2024-02 | 2023 IEPR California electricity demand forecast | `pipeline_config.py` | mid annual demand growth path; planning forecast, not observed history. **[MODELED]** |
| `demand_growth_rates.CAISO.high` | 0.022 | fraction/yr | 1 | California Energy Commission Integrated Energy Policy Report (IEPR) 2023 | 2024-02 | 2023 IEPR California electricity demand forecast | `pipeline_config.py` | high annual demand growth path; planning forecast, not observed history. **[MODELED]** |
| `scenario.demand_growth_rate` | 0.01 | fraction/yr | 1 | Market simulator model design decision | 2026-05 | model-methodology-spec.md / market-sim-build-plan.md | — | Scalar default; per-ISO/path values live in DEMAND_GROWTH_RATES. **[MODELED]** |

## Fuel Prices

| param_id | value | unit | tier | source | date | page / table | old repo location | notes |
|---|---|---|---|---|---|---|---|---|
| `gas_price_base.ERCOT.low` | 2.5 | $/MMBtu | 1 | EIA Annual Energy Outlook 2024 | 2024-03 | AEO2024 natural gas price projections (Reference and side cases) | — | low delivered gas price path; AEO is a projection model, not observed price. **[MODELED]** |
| `gas_price_base.ERCOT.mid` | 3.5 | $/MMBtu | 1 | EIA Annual Energy Outlook 2024 | 2024-03 | AEO2024 natural gas price projections (Reference and side cases) | — | mid delivered gas price path; AEO is a projection model, not observed price. **[MODELED]** |
| `gas_price_base.ERCOT.high` | 5.5 | $/MMBtu | 1 | EIA Annual Energy Outlook 2024 | 2024-03 | AEO2024 natural gas price projections (Reference and side cases) | — | high delivered gas price path; AEO is a projection model, not observed price. **[MODELED]** |
| `gas_price_base.CAISO.low` | 3.0 | $/MMBtu | 1 | EIA Annual Energy Outlook 2024 | 2024-03 | AEO2024 natural gas price projections (Reference and side cases) | — | low delivered gas price path; AEO is a projection model, not observed price. **[MODELED]** |
| `gas_price_base.CAISO.mid` | 4.25 | $/MMBtu | 1 | EIA Annual Energy Outlook 2024 | 2024-03 | AEO2024 natural gas price projections (Reference and side cases) | — | mid delivered gas price path; AEO is a projection model, not observed price. **[MODELED]** |
| `gas_price_base.CAISO.high` | 6.5 | $/MMBtu | 1 | EIA Annual Energy Outlook 2024 | 2024-03 | AEO2024 natural gas price projections (Reference and side cases) | — | high delivered gas price path; AEO is a projection model, not observed price. **[MODELED]** |
| `gas_price_escalation` | 0.02 | fraction/yr | 1 | EIA Annual Energy Outlook 2024 | 2024-03 | AEO2024 natural gas price projections (Reference and side cases) | — | Annual real escalation applied to base gas prices; AEO projection. **[MODELED]** |
| `scenario.gas_price_path` | mid | - | 1 | Market simulator model design decision | 2026-05 | model-methodology-spec.md / market-sim-build-plan.md | — | Default lever selecting which GAS_PRICE_BASE path to use. |

## Storage

| param_id | value | unit | tier | source | date | page / table | old repo location | notes |
|---|---|---|---|---|---|---|---|---|
| `storage_techs.li_ion_4hr.duration_hr` | 4 | hours | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `pipeline_config.py:368-397` | duration_hr for the li_ion_4hr storage technology. |
| `storage_techs.li_ion_4hr.rte` | 0.86 | fraction | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `pipeline_config.py:368-397` | rte for the li_ion_4hr storage technology. |
| `storage_techs.li_ion_4hr.cycles` | 5000 | cycles | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `pipeline_config.py:368-397` | cycles for the li_ion_4hr storage technology. |
| `storage_techs.li_ion_4hr.capex_per_kw` | 1380.0 | $/kW | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `pipeline_config.py:368-397` | capex_per_kw for the li_ion_4hr storage technology. |
| `storage_techs.li_ion_4hr.capex_per_kwh` | 345.0 | $/kWh | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `pipeline_config.py:368-397` | capex_per_kwh for the li_ion_4hr storage technology. |
| `storage_techs.li_ion_4hr.fom_per_kw_yr` | 34.5 | $/kW-yr | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `pipeline_config.py:368-397` | fom_per_kw_yr for the li_ion_4hr storage technology. |
| `storage_techs.li_ion_4hr.learning_rate` | 0.18 | fraction | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `pipeline_config.py:368-397` | learning_rate for the li_ion_4hr storage technology. Learning rate is a modeling assumption. **[MODELED]** |
| `storage_techs.li_ion_8hr.duration_hr` | 8 | hours | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `pipeline_config.py:368-397` | duration_hr for the li_ion_8hr storage technology. |
| `storage_techs.li_ion_8hr.rte` | 0.86 | fraction | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `pipeline_config.py:368-397` | rte for the li_ion_8hr storage technology. |
| `storage_techs.li_ion_8hr.cycles` | 5000 | cycles | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `pipeline_config.py:368-397` | cycles for the li_ion_8hr storage technology. |
| `storage_techs.li_ion_8hr.capex_per_kw` | 2760.0 | $/kW | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `pipeline_config.py:368-397` | capex_per_kw for the li_ion_8hr storage technology. |
| `storage_techs.li_ion_8hr.capex_per_kwh` | 345.0 | $/kWh | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `pipeline_config.py:368-397` | capex_per_kwh for the li_ion_8hr storage technology. |
| `storage_techs.li_ion_8hr.fom_per_kw_yr` | 55.2 | $/kW-yr | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `pipeline_config.py:368-397` | fom_per_kw_yr for the li_ion_8hr storage technology. |
| `storage_techs.li_ion_8hr.learning_rate` | 0.18 | fraction | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `pipeline_config.py:368-397` | learning_rate for the li_ion_8hr storage technology. Learning rate is a modeling assumption. **[MODELED]** |
| `storage_techs.iron_air.duration_hr` | 100 | hours | 2 | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | Iron-air / multi-day storage cost and performance | `pipeline_config.py:368-397` | duration_hr for the iron_air storage technology. **[STALE]** |
| `storage_techs.iron_air.rte` | 0.5 | fraction | 2 | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | Iron-air / multi-day storage cost and performance | `pipeline_config.py:368-397` | rte for the iron_air storage technology. **[STALE]** |
| `storage_techs.iron_air.cycles` | 3000 | cycles | 2 | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | Iron-air / multi-day storage cost and performance | `pipeline_config.py:368-397` | cycles for the iron_air storage technology. **[STALE]** |
| `storage_techs.iron_air.capex_per_kw` | 2000.0 | $/kW | 2 | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | Iron-air / multi-day storage cost and performance | `pipeline_config.py:368-397` | capex_per_kw for the iron_air storage technology. **[STALE]** |
| `storage_techs.iron_air.capex_per_kwh` | 20.0 | $/kWh | 2 | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | Iron-air / multi-day storage cost and performance | `pipeline_config.py:368-397` | capex_per_kwh for the iron_air storage technology. **[STALE]** |
| `storage_techs.iron_air.fom_per_kw_yr` | 20.0 | $/kW-yr | 2 | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | Iron-air / multi-day storage cost and performance | `pipeline_config.py:368-397` | fom_per_kw_yr for the iron_air storage technology. **[STALE]** |
| `storage_techs.iron_air.learning_rate` | 0.1 | fraction | 2 | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | Iron-air / multi-day storage cost and performance | `pipeline_config.py:368-397` | learning_rate for the iron_air storage technology. Learning rate is a modeling assumption. **[MODELED] [STALE]** |
| `scenario.storage_deployment` | mid | - | 1 | Market simulator model design decision | 2026-05 | model-methodology-spec.md / market-sim-build-plan.md | — | Default storage deployment pace lever. |
| `scenario.storage_rte_4hr` | 0.85 | fraction | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | — | Round-trip efficiency sensitivity knob; STORAGE_TECHS li_ion_4hr rte is 0.86. |
| `scenario.storage_rte_8hr` | 0.8 | fraction | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | — | Round-trip efficiency sensitivity knob; STORAGE_TECHS li_ion_8hr rte is 0.86. |

## Capacity Expansion

| param_id | value | unit | tier | source | date | page / table | old repo location | notes |
|---|---|---|---|---|---|---|---|---|
| `queue_cap_gw.ERCOT` | 12 | GW/yr | 1 | ERCOT Capacity, Demand and Reserves (CDR) Report | 2024-05 | May 2024 CDR — load forecast and interconnection data | `step6_1:94-103` | Annual interconnection queue throughput cap. |
| `queue_cap_gw.CAISO` | 8 | GW/yr | 1 | CAISO Transmission Planning Process (TPP) | 2024-03 | 2023-2024 TPP interconnection throughput | `step6_1:94-103` | Annual interconnection queue throughput cap. |
| `new_entry_costs.wind.capex_per_kw` | 1300.0 | $/kW | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `step6_1:107-168` | capex_per_kw for new wind build. |
| `new_entry_costs.wind.fom_per_kw_yr` | 28.0 | $/kW-yr | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `step6_1:107-168` | fom_per_kw_yr for new wind build. |
| `new_entry_costs.wind.learning_rate` | 0.12 | fraction | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `step6_1:107-168` | learning_rate for new wind build. Modeling assumption, not a directly observed value. **[MODELED]** |
| `new_entry_costs.wind.base_cf` | 0.38 | fraction | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `step6_1:107-168` | base_cf for new wind build. Modeling assumption, not a directly observed value. **[MODELED]** |
| `new_entry_costs.wind.lifetime_yr` | 30 | years | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `step6_1:107-168` | lifetime_yr for new wind build. |
| `new_entry_costs.solar.capex_per_kw` | 1100.0 | $/kW | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `step6_1:107-168` | capex_per_kw for new solar build. |
| `new_entry_costs.solar.fom_per_kw_yr` | 16.0 | $/kW-yr | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `step6_1:107-168` | fom_per_kw_yr for new solar build. |
| `new_entry_costs.solar.learning_rate` | 0.2 | fraction | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `step6_1:107-168` | learning_rate for new solar build. Modeling assumption, not a directly observed value. **[MODELED]** |
| `new_entry_costs.solar.base_cf` | 0.27 | fraction | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `step6_1:107-168` | base_cf for new solar build. Modeling assumption, not a directly observed value. **[MODELED]** |
| `new_entry_costs.solar.lifetime_yr` | 30 | years | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `step6_1:107-168` | lifetime_yr for new solar build. |
| `new_entry_costs.gas_cc.capex_per_kw` | 1200.0 | $/kW | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `step6_1:107-168` | capex_per_kw for new gas_cc build. |
| `new_entry_costs.gas_cc.fom_per_kw_yr` | 30.0 | $/kW-yr | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `step6_1:107-168` | fom_per_kw_yr for new gas_cc build. |
| `new_entry_costs.gas_cc.learning_rate` | 0.02 | fraction | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `step6_1:107-168` | learning_rate for new gas_cc build. Modeling assumption, not a directly observed value. **[MODELED]** |
| `new_entry_costs.gas_cc.base_cf` | 0.55 | fraction | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `step6_1:107-168` | base_cf for new gas_cc build. Modeling assumption, not a directly observed value. **[MODELED]** |
| `new_entry_costs.gas_cc.lifetime_yr` | 30 | years | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | `step6_1:107-168` | lifetime_yr for new gas_cc build. |
| `wright_reference_gw.wind` | 1020.0 | GW | 2 | IRENA Renewable Capacity Statistics 2024 | 2024-03 | Global cumulative installed capacity by technology | `step6_1:540-573` | Reference global cumulative installed onshore + offshore wind for learning-curve cost projection. |
| `wright_reference_gw.solar` | 1420.0 | GW | 2 | IRENA Renewable Capacity Statistics 2024 | 2024-03 | Global cumulative installed capacity by technology | `step6_1:540-573` | Reference global cumulative installed solar PV for learning-curve cost projection. |
| `wright_reference_gw.li_ion` | 90.0 | GW | 2 | IRENA Renewable Capacity Statistics 2024 | 2024-03 | Global cumulative installed capacity by technology | `step6_1:540-573` | Reference global cumulative installed li-ion grid storage for learning-curve cost projection. |
| `scenario.renewable_buildout_pace` | mid | - | 1 | Market simulator model design decision | 2026-05 | model-methodology-spec.md / market-sim-build-plan.md | — | Default renewable buildout pace lever. |
| `scenario.retirement_aggressiveness` | mid | - | 1 | Market simulator model design decision | 2026-05 | model-methodology-spec.md / market-sim-build-plan.md | — | Default thermal retirement pace lever. |
| `scenario.discount_rate` | 0.08 | fraction | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | ATB2024 cost & performance tables | — | Real discount rate / WACC for annualized capital cost. |
| `scenario.retirement_consecutive_years` | 2 | years | 2 | Market simulator model design decision | 2026-05 | model-methodology-spec.md / market-sim-build-plan.md | `step2_3_de_pathway_tf.py:1837-1890` | Consecutive unprofitable years before a unit retires; modeling assumption. **[MODELED]** |
| `scenario.sigmoid_midpoint` | 0.5 | fraction | 2 | Market simulator model design decision | 2026-05 | model-methodology-spec.md / market-sim-build-plan.md | `step2_3_de_pathway_tf.py:1837-1890` | Midpoint of the retirement sigmoid; modeling assumption. **[MODELED]** |
| `scenario.sigmoid_steepness` | 12.0 | dimensionless | 2 | Market simulator model design decision | 2026-05 | model-methodology-spec.md / market-sim-build-plan.md | `step2_3_de_pathway_tf.py:1837-1890` | Steepness of the retirement sigmoid; modeling assumption. **[MODELED]** |

## Policy

| param_id | value | unit | tier | source | date | page / table | old repo location | notes |
|---|---|---|---|---|---|---|---|---|
| `carbon_price_paths.zero` | 2026: 0, 2030: 0, 2040: 0, 2050: 0 | $/tCO2 | 1 | Resources for the Future (RFF) carbon price scenario set | 2023-09 | RFF carbon pricing scenario trajectories | `pipeline_config.py (CO2_PRICES)` | zero carbon price trajectory; scenario assumption from another model, not an observed price. **[MODELED]** |
| `carbon_price_paths.low` | 2026: 0, 2030: 8, 2040: 18, 2050: 25 | $/tCO2 | 1 | Resources for the Future (RFF) carbon price scenario set | 2023-09 | RFF carbon pricing scenario trajectories | `pipeline_config.py (CO2_PRICES)` | low carbon price trajectory; scenario assumption from another model, not an observed price. **[MODELED]** |
| `carbon_price_paths.mid` | 2026: 0, 2030: 15, 2040: 35, 2050: 50 | $/tCO2 | 1 | Resources for the Future (RFF) carbon price scenario set | 2023-09 | RFF carbon pricing scenario trajectories | `pipeline_config.py (CO2_PRICES)` | mid carbon price trajectory; scenario assumption from another model, not an observed price. **[MODELED]** |
| `carbon_price_paths.high` | 2026: 0, 2030: 30, 2040: 70, 2050: 110 | $/tCO2 | 1 | Resources for the Future (RFF) carbon price scenario set | 2023-09 | RFF carbon pricing scenario trajectories | `pipeline_config.py (CO2_PRICES)` | high carbon price trajectory; scenario assumption from another model, not an observed price. **[MODELED]** |
| `state_rps_floors.ERCOT` | 2026: 0.0, 2030: 0.0, 2040: 0.0, 2045: 0.0 | clean energy fraction | 1 | Market simulator model design decision | 2026-05 | model-methodology-spec.md / market-sim-build-plan.md | `pipeline_config.py` | Texas has no binding statewide clean-energy mandate; floor set to zero by design. |
| `state_rps_floors.CAISO` | 2026: 0.5, 2030: 0.6, 2040: 0.8, 2045: 1.0 | clean energy fraction | 1 | California SB 100 — The 100 Percent Clean Energy Act of 2018 | 2018-09 | SB 100 statutory clean-energy targets | `pipeline_config.py` | California SB 100 statutory clean-energy trajectory (60% by 2030, 100% by 2045). **[STALE]** |
| `scenario.carbon_price` | 0.0 | $/tCO2 | 1 | Market simulator model design decision | 2026-05 | model-methodology-spec.md / market-sim-build-plan.md | — | Default explicit carbon price (none). |
| `scenario.nox_price` | 0.0 | $/tNOx | 1 | Market simulator model design decision | 2026-05 | model-methodology-spec.md / market-sim-build-plan.md | — | Default explicit NOx price (none). |
| `scenario.ira_ptc_wind` | 26.0 | $/MWh | 2 | IRS Inflation Reduction Act final rules (IRC sections 45, 48, 48E) | 2024-04 | PTC/ITC credit values, 2024 inflation adjustment | — | IRA production tax credit for wind (IRC section 45), 2024 inflation-adjusted. |
| `scenario.ira_itc_solar` | 0.3 | fraction | 2 | IRS Inflation Reduction Act final rules (IRC sections 45, 48, 48E) | 2024-04 | PTC/ITC credit values, 2024 inflation adjustment | — | IRA investment tax credit for solar (30%). |
| `scenario.ira_itc_storage` | 0.3 | fraction | 2 | IRS Inflation Reduction Act final rules (IRC sections 45, 48, 48E) | 2024-04 | PTC/ITC credit values, 2024 inflation adjustment | — | IRA investment tax credit for standalone storage (30%). |
| `scenario.ira_expiry_year` | 2035 | year | 2 | CBO scoring of Inflation Reduction Act energy provisions | 2023-04 | IRA energy tax credit duration / phase-out projections | — | Assumed IRA credit phase-out year; projection/assumption, not a fixed statutory date. **[MODELED] [STALE]** |

## Calibration

| param_id | value | unit | tier | source | date | page / table | old repo location | notes |
|---|---|---|---|---|---|---|---|---|
| `scenario.renewable_cf_adjustment` | 1.0 | multiplier | 3 | Market simulator model design decision | 2026-05 | model-methodology-spec.md / market-sim-build-plan.md | — | Tier-3 calibration knob; neutral default of 1.0. **[MODELED]** |
| `scenario.basis_differential_factor` | 1.0 | multiplier | 3 | Market simulator model design decision | 2026-05 | model-methodology-spec.md / market-sim-build-plan.md | — | Tier-3 calibration knob; neutral default of 1.0. **[MODELED]** |

## Flagged: model-sourced parameters (not empirical data)

These values come from another model's assumptions or projections (forecasts, scenario trajectories, learning-rate assumptions, calibration knobs) rather than measured/observed data. Treat them as inputs to test, not as ground truth.

| param_id | source | notes |
|---|---|---|
| `demand_growth_rates.ERCOT.low` | ERCOT Capacity, Demand and Reserves (CDR) Report | low annual demand growth path; planning forecast, not observed history. |
| `demand_growth_rates.ERCOT.mid` | ERCOT Capacity, Demand and Reserves (CDR) Report | mid annual demand growth path; planning forecast, not observed history. |
| `demand_growth_rates.ERCOT.high` | ERCOT Capacity, Demand and Reserves (CDR) Report | high annual demand growth path; planning forecast, not observed history. |
| `demand_growth_rates.CAISO.low` | California Energy Commission Integrated Energy Policy Report (IEPR) 2023 | low annual demand growth path; planning forecast, not observed history. |
| `demand_growth_rates.CAISO.mid` | California Energy Commission Integrated Energy Policy Report (IEPR) 2023 | mid annual demand growth path; planning forecast, not observed history. |
| `demand_growth_rates.CAISO.high` | California Energy Commission Integrated Energy Policy Report (IEPR) 2023 | high annual demand growth path; planning forecast, not observed history. |
| `gas_price_base.ERCOT.low` | EIA Annual Energy Outlook 2024 | low delivered gas price path; AEO is a projection model, not observed price. |
| `gas_price_base.ERCOT.mid` | EIA Annual Energy Outlook 2024 | mid delivered gas price path; AEO is a projection model, not observed price. |
| `gas_price_base.ERCOT.high` | EIA Annual Energy Outlook 2024 | high delivered gas price path; AEO is a projection model, not observed price. |
| `gas_price_base.CAISO.low` | EIA Annual Energy Outlook 2024 | low delivered gas price path; AEO is a projection model, not observed price. |
| `gas_price_base.CAISO.mid` | EIA Annual Energy Outlook 2024 | mid delivered gas price path; AEO is a projection model, not observed price. |
| `gas_price_base.CAISO.high` | EIA Annual Energy Outlook 2024 | high delivered gas price path; AEO is a projection model, not observed price. |
| `gas_price_escalation` | EIA Annual Energy Outlook 2024 | Annual real escalation applied to base gas prices; AEO projection. |
| `carbon_price_paths.zero` | Resources for the Future (RFF) carbon price scenario set | zero carbon price trajectory; scenario assumption from another model, not an observed price. |
| `carbon_price_paths.low` | Resources for the Future (RFF) carbon price scenario set | low carbon price trajectory; scenario assumption from another model, not an observed price. |
| `carbon_price_paths.mid` | Resources for the Future (RFF) carbon price scenario set | mid carbon price trajectory; scenario assumption from another model, not an observed price. |
| `carbon_price_paths.high` | Resources for the Future (RFF) carbon price scenario set | high carbon price trajectory; scenario assumption from another model, not an observed price. |
| `storage_techs.li_ion_4hr.learning_rate` | NREL Annual Technology Baseline 2024 | learning_rate for the li_ion_4hr storage technology. Learning rate is a modeling assumption. |
| `storage_techs.li_ion_8hr.learning_rate` | NREL Annual Technology Baseline 2024 | learning_rate for the li_ion_8hr storage technology. Learning rate is a modeling assumption. |
| `storage_techs.iron_air.learning_rate` | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | learning_rate for the iron_air storage technology. Learning rate is a modeling assumption. |
| `new_entry_costs.wind.learning_rate` | NREL Annual Technology Baseline 2024 | learning_rate for new wind build. Modeling assumption, not a directly observed value. |
| `new_entry_costs.wind.base_cf` | NREL Annual Technology Baseline 2024 | base_cf for new wind build. Modeling assumption, not a directly observed value. |
| `new_entry_costs.solar.learning_rate` | NREL Annual Technology Baseline 2024 | learning_rate for new solar build. Modeling assumption, not a directly observed value. |
| `new_entry_costs.solar.base_cf` | NREL Annual Technology Baseline 2024 | base_cf for new solar build. Modeling assumption, not a directly observed value. |
| `new_entry_costs.gas_cc.learning_rate` | NREL Annual Technology Baseline 2024 | learning_rate for new gas_cc build. Modeling assumption, not a directly observed value. |
| `new_entry_costs.gas_cc.base_cf` | NREL Annual Technology Baseline 2024 | base_cf for new gas_cc build. Modeling assumption, not a directly observed value. |
| `scenario.demand_growth_rate` | Market simulator model design decision | Scalar default; per-ISO/path values live in DEMAND_GROWTH_RATES. |
| `scenario.retirement_consecutive_years` | Market simulator model design decision | Consecutive unprofitable years before a unit retires; modeling assumption. |
| `scenario.sigmoid_midpoint` | Market simulator model design decision | Midpoint of the retirement sigmoid; modeling assumption. |
| `scenario.sigmoid_steepness` | Market simulator model design decision | Steepness of the retirement sigmoid; modeling assumption. |
| `scenario.ira_expiry_year` | CBO scoring of Inflation Reduction Act energy provisions | Assumed IRA credit phase-out year; projection/assumption, not a fixed statutory date. |
| `scenario.renewable_cf_adjustment` | Market simulator model design decision | Tier-3 calibration knob; neutral default of 1.0. |
| `scenario.basis_differential_factor` | Market simulator model design decision | Tier-3 calibration knob; neutral default of 1.0. |

## Flagged: stale parameters (source older than 3 years)

Source publication date is before 2023-05 (more than 3 years before the 2026-05-16 verification date). Schedule a refresh review to confirm a newer edition has not superseded these values.

| param_id | source | source_date | notes |
|---|---|---|---|
| `nox_rates.gas_cc` | EPA Clean Air Markets Program Data (CEMS), 2022 | 2023-02 | Fleet-average NOx emission rate from continuous emissions monitoring. |
| `nox_rates.gas_ct` | EPA Clean Air Markets Program Data (CEMS), 2022 | 2023-02 | Fleet-average NOx emission rate from continuous emissions monitoring. |
| `nox_rates.coal` | EPA Clean Air Markets Program Data (CEMS), 2022 | 2023-02 | Fleet-average NOx emission rate from continuous emissions monitoring. |
| `storage_techs.iron_air.duration_hr` | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | duration_hr for the iron_air storage technology. |
| `storage_techs.iron_air.rte` | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | rte for the iron_air storage technology. |
| `storage_techs.iron_air.cycles` | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | cycles for the iron_air storage technology. |
| `storage_techs.iron_air.capex_per_kw` | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | capex_per_kw for the iron_air storage technology. |
| `storage_techs.iron_air.capex_per_kwh` | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | capex_per_kwh for the iron_air storage technology. |
| `storage_techs.iron_air.fom_per_kw_yr` | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | fom_per_kw_yr for the iron_air storage technology. |
| `storage_techs.iron_air.learning_rate` | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | learning_rate for the iron_air storage technology. Learning rate is a modeling assumption. |
| `state_rps_floors.CAISO` | California SB 100 — The 100 Percent Clean Energy Act of 2018 | 2018-09 | California SB 100 statutory clean-energy trajectory (60% by 2030, 100% by 2045). |
| `scenario.voll` | Public Utility Commission of Texas / ERCOT Nodal Protocols | 2023-01 | ERCOT value of lost load (system-wide offer cap basis); CAISO ISOConfig uses 2000. |
| `scenario.ira_expiry_year` | CBO scoring of Inflation Reduction Act energy provisions | 2023-04 | Assumed IRA credit phase-out year; projection/assumption, not a fixed statutory date. |

## Source reference

| key | source | date | url |
|---|---|---|---|
| EIA_T8 | EIA Electric Power Annual 2022, Table 8.2 | 2023-10 | https://www.eia.gov/electricity/annual/ |
| EGRID | EPA eGRID2022 | 2024-01 | https://www.epa.gov/egrid |
| CEMS | EPA Clean Air Markets Program Data (CEMS), 2022 | 2023-02 | https://campd.epa.gov/ |
| ATB24 | NREL Annual Technology Baseline 2024 | 2024-07 | https://atb.nrel.gov/electricity/2024/ |
| GADS | NERC Generating Availability Data System (GADS), 2018-2022 | 2023-08 | https://www.nerc.com/pa/RAPA/gads/Pages/default.aspx |
| PRIS | NRC / IAEA Power Reactor Information System (PRIS), 2019-2023 | 2024-01 | https://www.nrc.gov/reading-rm/doc-collections/datasets/ |
| ERCOT_CDR | ERCOT Capacity, Demand and Reserves (CDR) Report | 2024-05 | https://www.ercot.com/gridinfo/resource |
| CAISO_IEPR | California Energy Commission Integrated Energy Policy Report (IEPR) 2023 | 2024-02 | https://www.energy.ca.gov/data-reports/reports/integrated-energy-policy-report |
| AEO24 | EIA Annual Energy Outlook 2024 | 2024-03 | https://www.eia.gov/outlooks/aeo/ |
| RFF | Resources for the Future (RFF) carbon price scenario set | 2023-09 | https://www.rff.org/ |
| LDES | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | https://liftoff.energy.gov/long-duration-energy-storage/ |
| IRENA24 | IRENA Renewable Capacity Statistics 2024 | 2024-03 | https://www.irena.org/Publications/2024/Mar/Renewable-capacity-statistics-2024 |
| SB100 | California SB 100 — The 100 Percent Clean Energy Act of 2018 | 2018-09 | https://www.energy.ca.gov/sb100 |
| CAISO_TPP | CAISO Transmission Planning Process (TPP) | 2024-03 | https://www.caiso.com/planning/Pages/TransmissionPlanning/Default.aspx |
| IRS_IRA | IRS Inflation Reduction Act final rules (IRC sections 45, 48, 48E) | 2024-04 | https://www.irs.gov/inflation-reduction-act-of-2022 |
| CBO_IRA | CBO scoring of Inflation Reduction Act energy provisions | 2023-04 | https://www.cbo.gov/ |
| ERCOT_VOLL | Public Utility Commission of Texas / ERCOT Nodal Protocols | 2023-01 | https://www.ercot.com/mktrules/nprotocols |
| MODEL_DESIGN | Market simulator model design decision | 2026-05 | — |

---

_Maintenance: regenerate both artifacts whenever a constant or `ScenarioConfig` default changes, then run `python scripts/validate_parameters.py`._
