# Parameter Citation Registry

_Generated 2026-06-11. Every numeric input to the model traces to a primary source
here. This file is rendered from `frontend/data/parameters.json` by
`scripts/generate_parameter_registry.py`; edit citations in the JSON (or the
constant's comment, then re-run the generator), not here._

This document is the human-readable companion to `frontend/data/parameters.json`
(the machine-readable registry). `scripts/validate_parameters.py` fails CI if any
constant in `src/market_sim/config/constants.py` or any `ScenarioConfig` default
lacks an entry.

Entries flagged **needs-citation** were auto-registered from the constant's
inline comment and still need a dated primary source — search the table for
`needs-citation`.

## How `param_id` is derived

- A module-level constant in `constants.py` becomes its lower-cased name (e.g.
  `HOURS_PER_YEAR` -> `hours_per_year`).
- Nested dicts with string keys are flattened with dots (e.g.
  `HEAT_RATE_BINS["gas_cc"]["h_class"]` -> `heat_rate_bins.gas_cc.h_class`).
- A dict whose keys are all years is treated as a single leaf.
- `ScenarioConfig` dataclass defaults are prefixed with `scenario.`.


**619 parameters registered** (292 flagged `needs-citation`).


## Calibration

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `scenario.basis_differential_factor` | 1.0 | 3 | Market simulator model design decision | 2026-05 | modeled |
| `scenario.battery_dispatch_adder` | 0.0 | 3 | Xu, Zhao, Zheng, Litvinov & Kirschen, 'Factoring the Cycle Aging Co… | 2018-03 | modeled |
| `scenario.cc_cycling_adder_f_class` | 3.66 | 3 | NREL/SR-5500-55433 (Kumar et al. 2012) | 2012-04 | modeled |
| `scenario.cc_cycling_adder_h_class` | 3.92 | 3 | NREL/SR-5500-55433 (Kumar et al. 2012) | 2012-04 | modeled |
| `scenario.cc_cycling_adder_older` | 2.91 | 3 | NREL/SR-5500-55433 (Kumar et al. 2012) | 2012-04 | modeled |
| `scenario.ct_cycling_adder_aero` | 3.14 | 3 | NREL/SR-5500-55433 (Kumar et al. 2012) | 2012-04 | modeled |
| `scenario.ct_cycling_adder_frame` | 5.02 | 3 | NREL/SR-5500-55433 (Kumar et al. 2012) | 2012-04 | modeled |
| `scenario.ct_cycling_adder_older` | 4.85 | 3 | NREL/SR-5500-55433 (Kumar et al. 2012) | 2012-04 | modeled |
| `scenario.renewable_cf_adjustment` | 1.0 | 3 | Market simulator model design decision | 2026-05 | modeled |
| `scenario.storage_vintage_ramp` | False | 3 | EIA Form 860 — 2024 | 2024-06 | modeled |
| `scenario.td_loss_factor` | 0.0 | 3 | EIA-930 ERCOT hourly (Demand + Interchange = Net Generation) | 2026-05 |  |
| `scenario.vintage_capacity_ramp` | True | 3 | EIA Form 860 — 2024 | 2024-06 |  |

## Capacity Expansion

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `new_entry_costs.gas_cc.base_cf` | 0.55 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | modeled |
| `new_entry_costs.gas_cc.capex_per_kw` | 1200.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `new_entry_costs.gas_cc.fom_per_kw_yr` | 30.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `new_entry_costs.gas_cc.learning_rate` | 0.02 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | modeled |
| `new_entry_costs.gas_cc.lifetime_yr` | 30 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `new_entry_costs.solar.base_cf` | 0.27 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | modeled |
| `new_entry_costs.solar.capex_per_kw` | 1100.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `new_entry_costs.solar.fom_per_kw_yr` | 16.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `new_entry_costs.solar.learning_rate` | 0.2 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | modeled |
| `new_entry_costs.solar.lifetime_yr` | 30 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `new_entry_costs.wind.base_cf` | 0.38 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | modeled |
| `new_entry_costs.wind.capex_per_kw` | 1300.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `new_entry_costs.wind.fom_per_kw_yr` | 28.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `new_entry_costs.wind.learning_rate` | 0.12 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | modeled |
| `new_entry_costs.wind.lifetime_yr` | 30 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `queue_cap_gw.CAISO` | 8 | 1 | CAISO Transmission Planning Process (TPP) | 2024-03 |  |
| `queue_cap_gw.ERCOT` | 12 | 1 | ERCOT Capacity, Demand and Reserves (CDR) Report | 2024-05 |  |
| `scenario.discount_rate` | 0.08 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `scenario.renewable_buildout_pace` | mid | 1 | Market simulator model design decision | 2026-05 |  |
| `scenario.retirement_aggressiveness` | mid | 1 | Market simulator model design decision | 2026-05 |  |
| `scenario.retirement_consecutive_years` | 2 | 2 | Market simulator model design decision | 2026-05 | modeled |
| `scenario.sigmoid_midpoint` | 0.5 | 2 | Market simulator model design decision | 2026-05 | modeled |
| `scenario.sigmoid_steepness` | 12.0 | 2 | Market simulator model design decision | 2026-05 | modeled |
| `wright_reference_gw.li_ion` | 130.0 | 2 | IRENA Renewable Capacity Statistics 2024 | 2024-03 |  |
| `wright_reference_gw.solar` | 1800.0 | 2 | IRENA Renewable Capacity Statistics 2024 | 2024-03 |  |
| `wright_reference_gw.wind` | 1150.0 | 2 | IRENA Renewable Capacity Statistics 2024 | 2024-03 |  |

## Cost Trajectories

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `new_entry_costs.nuclear_large.capex_per_kw` | 8500.0 | 2 | $/kW total plant cost (host CCGT + capture island). |  | auto-generated, needs-citation |
| `new_entry_costs.nuclear_large.learning_rate` | 0.03 | 2 | 10% cost reduction per doubling of cumulative deployment. |  | auto-generated, needs-citation |
| `new_entry_costs.nuclear_smr.capex_per_kw` | 6800.0 | 2 | $/kW total plant cost (host CCGT + capture island). |  | auto-generated, needs-citation |
| `new_entry_costs.nuclear_smr.learning_rate` | 0.08 | 2 | 10% cost reduction per doubling of cumulative deployment. |  | auto-generated, needs-citation |
| `scenario.nominal_discount_rate` | 0.08 | 2 | Nominal WACC, $/MWh LCOE basis |  | auto-generated, needs-citation |

## Demand

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `demand_growth_rates.CAISO.high` | 0.022 | 1 | California Energy Commission Integrated Energy Policy Report (IEPR)… | 2024-02 | modeled |
| `demand_growth_rates.CAISO.high.long` | 0.018 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.CAISO.high.near` | 0.025 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.CAISO.low` | 0.005 | 1 | California Energy Commission Integrated Energy Policy Report (IEPR)… | 2024-02 | modeled |
| `demand_growth_rates.CAISO.low.long` | 0.005 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.CAISO.low.near` | 0.005 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.CAISO.mid` | 0.012 | 1 | California Energy Commission Integrated Energy Policy Report (IEPR)… | 2024-02 | modeled |
| `demand_growth_rates.CAISO.mid.long` | 0.01 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.CAISO.mid.near` | 0.015 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.ERCOT.high` | 0.035 | 1 | ERCOT Capacity, Demand and Reserves (CDR) Report | 2024-05 | modeled |
| `demand_growth_rates.ERCOT.high.long` | 0.04 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.ERCOT.high.near` | 0.08 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.ERCOT.low` | 0.01 | 1 | ERCOT Capacity, Demand and Reserves (CDR) Report | 2024-05 | modeled |
| `demand_growth_rates.ERCOT.low.long` | 0.015 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.ERCOT.low.near` | 0.03 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.ERCOT.mid` | 0.02 | 1 | ERCOT Capacity, Demand and Reserves (CDR) Report | 2024-05 | modeled |
| `demand_growth_rates.ERCOT.mid.long` | 0.025 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.ERCOT.mid.near` | 0.05 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.NEISO.high.long` | 0.018 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.NEISO.high.near` | 0.025 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.NEISO.low.long` | 0.005 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.NEISO.low.near` | 0.005 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.NEISO.mid.long` | 0.01 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.NEISO.mid.near` | 0.015 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.NYISO.high.long` | 0.018 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.NYISO.high.near` | 0.025 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.NYISO.low.long` | 0.005 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.NYISO.low.near` | 0.005 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.NYISO.mid.long` | 0.01 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.NYISO.mid.near` | 0.015 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.PJM.high.long` | 0.03 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.PJM.high.near` | 0.06 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.PJM.low.long` | 0.01 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.PJM.low.near` | 0.02 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.PJM.mid.long` | 0.018 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_rates.PJM.mid.near` | 0.035 | 2 | Annual demand growth rates by ISO, scenario path, and era. Near-ter… | 2026 | auto-generated |
| `demand_growth_transition_year` | 2030 | 2 | Year at which demand growth transitions from near-term to long-term… | 2030 | auto-generated |
| `scenario.demand_growth_path` | mid | 1 | "low", "mid", "high" — selects from DEMAND_GROWTH_RATES |  | auto-generated, needs-citation |
| `scenario.demand_growth_rate` | 0.01 | 1 | Market simulator model design decision | 2026-05 | modeled |

## Emerging Tech

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `electrolyzer_params.alkaline.capex_kw` | 800.0 | 2 | $/kW — for LCOH if needed. BNEF 2024 | 2024 | auto-generated |
| `electrolyzer_params.alkaline.efficiency` | 0.63 | 2 | base year. Source: IRENA Green H2 2023 | 2023 | auto-generated |
| `electrolyzer_params.alkaline.efficiency_2035` | 0.68 | 2 | DOE Hydrogen Shot targets |  | auto-generated, needs-citation |
| `electrolyzer_params.alkaline.efficiency_2045` | 0.72 | 2 | DOE long-term targets |  | auto-generated, needs-citation |
| `electrolyzer_params.alkaline.learning_rate` | 0.12 | 2 | aggressive — early on curve. IRENA 2023 | 2023 | auto-generated |
| `electrolyzer_params.pem.capex_kw` | 1200.0 | 2 | $/kW — for LCOH if needed. BNEF 2024 | 2024 | auto-generated |
| `electrolyzer_params.pem.efficiency` | 0.65 | 2 | base year. Source: IRENA Green H2 2023 | 2023 | auto-generated |
| `electrolyzer_params.pem.efficiency_2035` | 0.72 | 2 | DOE Hydrogen Shot targets |  | auto-generated, needs-citation |
| `electrolyzer_params.pem.efficiency_2045` | 0.76 | 2 | DOE long-term targets |  | auto-generated, needs-citation |
| `electrolyzer_params.pem.learning_rate` | 0.18 | 2 | aggressive — early on curve. IRENA 2023 | 2023 | auto-generated |
| `geothermal_params.egs.capacity_factor` | 0.9 | 2 | high availability. DOE GeoVision 2019 | 2019 | auto-generated |
| `geothermal_params.egs.capex_kw` | 5000.0 | 2 | $/kW — high upfront, early-stage. NREL ATB 2024 | 2024 | auto-generated |
| `geothermal_params.egs.fom_kw_yr` | 0.0 | 2 | $/kW-yr — captured in VOM. NREL ATB 2024 | 2024 | auto-generated |
| `geothermal_params.egs.learning_rate` | 0.15 | 2 | steep — analogous to early solar. Fervo, ARPA-E |  | auto-generated, needs-citation |
| `geothermal_params.egs.lifetime_yr` | 30 | 2 | Enhanced geothermal (EGS) parameters. EGS enters as a thermal gener… |  | auto-generated, needs-citation |
| `geothermal_params.egs.pmin_fraction` | 0.2 | 2 | turn down to 20% for flexibility. Fervo 2024 | 2024 | auto-generated |
| `hydrogen_turbine_params.h2_ccgt.capex_kw` | 1800.0 | 2 | $/kW. NREL ATB 2024, BloombergNEF H2 Outlook 2024 | 2024 | auto-generated |
| `hydrogen_turbine_params.h2_ccgt.fom_kw_yr` | 15.0 | 2 | $/kW-yr. NREL ATB 2024 | 2024 | auto-generated |
| `hydrogen_turbine_params.h2_ccgt.learning_rate` | 0.1 | 2 | analogy to gas CT maturation |  | auto-generated, needs-citation |
| `hydrogen_turbine_params.h2_ccgt.lifetime_yr` | 30 | 2 | Hydrogen-fired turbine parameters. H2 turbines are thermal generato… |  | auto-generated, needs-citation |
| `hydrogen_turbine_params.h2_ct.capex_kw` | 1400.0 | 2 | $/kW. NREL ATB 2024, BloombergNEF H2 Outlook 2024 | 2024 | auto-generated |
| `hydrogen_turbine_params.h2_ct.fom_kw_yr` | 12.0 | 2 | $/kW-yr. NREL ATB 2024 | 2024 | auto-generated |
| `hydrogen_turbine_params.h2_ct.learning_rate` | 0.1 | 2 | analogy to gas CT maturation |  | auto-generated, needs-citation |
| `hydrogen_turbine_params.h2_ct.lifetime_yr` | 30 | 2 | Hydrogen-fired turbine parameters. H2 turbines are thermal generato… |  | auto-generated, needs-citation |
| `offshore_wind_min_cf` | 0.08 | 2 | minimum hourly CF — offshore rarely drops to zero |  | auto-generated, needs-citation |
| `offshore_wind_params.fixed_bottom.base_cf` | 0.45 | 2 | annual average. NREL ATB 2024 | 2024 | auto-generated |
| `offshore_wind_params.fixed_bottom.capex_kw` | 4200.0 | 2 | $/kW. NREL ATB 2024 | 2024 | auto-generated |
| `offshore_wind_params.fixed_bottom.fom_kw_yr` | 80.0 | 2 | $/kW-yr — marine access premium. NREL ATB 2024 | 2024 | auto-generated |
| `offshore_wind_params.fixed_bottom.learning_rate` | 0.08 | 2 | NREL ATB 2024, IRENA 2024 | 2024 | auto-generated |
| `offshore_wind_params.fixed_bottom.lifetime_yr` | 30 | 2 | Offshore wind parameters. A separate renewable category from onshor… |  | auto-generated, needs-citation |
| `offshore_wind_params.floating.base_cf` | 0.48 | 2 | annual average. NREL ATB 2024 | 2024 | auto-generated |
| `offshore_wind_params.floating.capex_kw` | 5500.0 | 2 | $/kW. NREL ATB 2024 | 2024 | auto-generated |
| `offshore_wind_params.floating.fom_kw_yr` | 95.0 | 2 | $/kW-yr — marine access premium. NREL ATB 2024 | 2024 | auto-generated |
| `offshore_wind_params.floating.learning_rate` | 0.12 | 2 | NREL ATB 2024, IRENA 2024 | 2024 | auto-generated |
| `offshore_wind_params.floating.lifetime_yr` | 30 | 2 | Offshore wind parameters. A separate renewable category from onshor… |  | auto-generated, needs-citation |
| `offshore_wind_smoothing_hours` | 6 | 2 | rolling-mean window — ocean fetch reduces gustiness |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.CAISO.geothermal` | 3.0 | 2 | engineering judgment, EGS resource potential |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.CAISO.offshore_wind` | 3.0 | 2 | Gulf coast not yet leased. Source: BOEM |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.ERCOT.geothermal` | 2.0 | 2 | engineering judgment, EGS resource potential |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.ERCOT.offshore_wind` | 0.0 | 2 | Gulf coast not yet leased. Source: BOEM |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.MISO.geothermal` | 0.0 | 2 | engineering judgment, EGS resource potential |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.MISO.offshore_wind` | 0.0 | 2 | Gulf coast not yet leased. Source: BOEM |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.NEISO.geothermal` | 0.0 | 2 | engineering judgment, EGS resource potential |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.NEISO.offshore_wind` | 2.0 | 2 | Gulf coast not yet leased. Source: BOEM |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.NYISO.geothermal` | 0.0 | 2 | engineering judgment, EGS resource potential |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.NYISO.offshore_wind` | 1.5 | 2 | Gulf coast not yet leased. Source: BOEM |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.PJM.geothermal` | 0.0 | 2 | engineering judgment, EGS resource potential |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.PJM.offshore_wind` | 2.0 | 2 | Gulf coast not yet leased. Source: BOEM |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.SPP.geothermal` | 0.0 | 2 | engineering judgment, EGS resource potential |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.SPP.offshore_wind` | 0.0 | 2 | Gulf coast not yet leased. Source: BOEM |  | auto-generated, needs-citation |
| `scenario.electrolyzer_efficiency_override` | None | 2 | overrides lookup |  | auto-generated, needs-citation |
| `scenario.electrolyzer_type` | pem | 1 | "pem" or "alkaline" — sets H2 fuel cost |  | auto-generated, needs-citation |
| `scenario.h2_available_year` | 2035 | 1 | was 2032. | 2032 | auto-generated |
| `scenario.ira_h2_45v_last_year` | 2027 | 2 | §45V hydrogen production credit: construction start by Dec 31, 2027. | 2027 | auto-generated |
| `scenario.offshore_wind_available_year` | 2030 | 1 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.offshore_wind_cf_override` | None | 2 | overrides OFFSHORE_WIND_PARAMS |  | auto-generated, needs-citation |
| `scenario.offshore_wind_eligible_isos` | ["CAISO"] | 1 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |

## Emissions

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `co2_rates.biomass.default` | 0.0 | 2 | EPA eGRID 2022 — petroleum-fired units | 2022 | auto-generated |
| `co2_rates.coal.older` | 1.08 | 2 | EPA eGRID2022 | 2024-01 |  |
| `co2_rates.coal.subcritical` | 1.0 | 2 | EPA eGRID2022 | 2024-01 |  |
| `co2_rates.coal.supercritical` | 0.88 | 2 | EPA eGRID2022 | 2024-01 |  |
| `co2_rates.gas_cc.f_class` | 0.38 | 2 | EPA eGRID2022 | 2024-01 |  |
| `co2_rates.gas_cc.h_class` | 0.36 | 2 | EPA eGRID2022 | 2024-01 |  |
| `co2_rates.gas_cc.older` | 0.43 | 2 | EPA eGRID2022 | 2024-01 |  |
| `co2_rates.gas_ct.aero` | 0.51 | 2 | EPA eGRID2022 | 2024-01 |  |
| `co2_rates.gas_ct.frame` | 0.6 | 2 | EPA eGRID2022 | 2024-01 |  |
| `co2_rates.gas_ct.older` | 0.65 | 2 | EPA eGRID2022 | 2024-01 |  |
| `co2_rates.oil.default` | 1.0 | 2 | EPA eGRID 2022 — petroleum-fired units | 2022 | auto-generated |
| `fuel_co2_factor_per_mmbtu.biomass` | 0.0 | 2 | biogenic CO2 carbon-neutral under EPA/RGGI accounting |  | auto-generated, needs-citation |
| `fuel_co2_factor_per_mmbtu.coal` | 0.1 | 2 | coal — implied by EPA eGRID 2022 coal steam rates | 2022 | auto-generated |
| `fuel_co2_factor_per_mmbtu.gas_cc` | 0.057 | 2 | natural gas — implied by EPA eGRID 2022 gas CC rates | 2022 | auto-generated |
| `fuel_co2_factor_per_mmbtu.gas_ct` | 0.057 | 2 | natural gas — same fuel as gas CC |  | auto-generated, needs-citation |
| `fuel_co2_factor_per_mmbtu.gas_st` | 0.057 | 2 | natural gas — legacy gas steam boilers |  | auto-generated, needs-citation |
| `fuel_co2_factor_per_mmbtu.oil` | 0.074 | 2 | distillate/residual fuel oil — EPA emission factors |  | auto-generated, needs-citation |
| `geothermal_params.egs.emission_rate_co2` | 0.0 | 2 | zero direct emissions |  | auto-generated, needs-citation |
| `geothermal_params.egs.nox_rate` | 0.0 | 2 | Enhanced geothermal (EGS) parameters. EGS enters as a thermal gener… |  | auto-generated, needs-citation |
| `hydrogen_turbine_params.h2_ccgt.emission_rate_co2` | 0.0 | 2 | tCO2/MWh — zero direct CO2 (green H2) |  | auto-generated, needs-citation |
| `hydrogen_turbine_params.h2_ccgt.nox_rate` | 0.00012 | 2 | tons NOx/MWh — H2 burns hot. DOE/NETL 2023 | 2023 | auto-generated |
| `hydrogen_turbine_params.h2_ct.emission_rate_co2` | 0.0 | 2 | tCO2/MWh — zero direct CO2 (green H2) |  | auto-generated, needs-citation |
| `hydrogen_turbine_params.h2_ct.nox_rate` | 0.00015 | 2 | tons NOx/MWh — H2 burns hot. DOE/NETL 2023 | 2023 | auto-generated |
| `nox_rates.biomass` | 0.001 | 2 | EPA CEMS 2023 — biomass combustion, high NOx per MWh. | 2023 | auto-generated |
| `nox_rates.coal` | 0.0012 | 2 | EPA Clean Air Markets Program Data (CEMS), 2022 | 2023-02 | stale |
| `nox_rates.gas_cc` | 8e-05 | 2 | EPA Clean Air Markets Program Data (CEMS), 2022 | 2023-02 | stale |
| `nox_rates.gas_ct` | 0.00025 | 2 | EPA Clean Air Markets Program Data (CEMS), 2022 | 2023-02 | stale |
| `nox_rates.gas_st` | 0.00025 | 2 | EPA CEMS 2023 — legacy gas steam boilers, mostly non-SCR. | 2023 | auto-generated |
| `nox_rates.oil` | 0.0004 | 2 | EPA CEMS 2023 — oil-fired peakers/steam, mostly non-SCR. | 2023 | auto-generated |
| `scenario.carbon_price_path` | zero | 1 | "zero", "low", "mid", "high"; used when carbon_price is 0.0 |  | auto-generated, needs-citation |
| `scenario.plant_emission_rates_path` | inputs/processed/plant_emission_rates… | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.so2_price` | 0.0 | 1 | $/ton SO2 |  | auto-generated, needs-citation |
| `scenario.use_plant_emission_rates` | True | 2 | When True, generators pinned to a single plant take that plant's CA… |  | auto-generated, needs-citation |

## Fuel Prices

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `biomass_price_per_mmbtu` | 2.5 | 2 | Delivered biomass fuel price ($/MMBtu) for wood/MSW/landfill-gas un… | 2024 | auto-generated |
| `coal_price_base.CAISO` | 2.5 | 2 | EIA AEO 2024 — delivered coal price | 2024 | auto-generated |
| `coal_price_base.ERCOT` | 2.0 | 2 | EIA AEO 2024 — delivered coal price | 2024 | auto-generated |
| `coal_price_base.PJM` | 2.3 | 2 | Central/Northern Appalachian bituminous + PRB-by-rail |  | auto-generated, needs-citation |
| `coal_price_escalation` | 0.01 | 2 | Annual real escalation rate for coal prices. Reflects mine closures… | 2024 | auto-generated |
| `eac_price_reference.eac_geothermal.high` | 15.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_geothermal.low` | 5.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_geothermal.mid` | 10.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_nuclear_zec.high` | 25.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_nuclear_zec.low` | 10.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_nuclear_zec.mid` | 17.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_offshore_wind.high` | 40.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_offshore_wind.low` | 20.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_offshore_wind.mid` | 30.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_solar.high` | 20.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_solar.low` | 2.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_solar.mid` | 10.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_wind.high` | 15.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_wind.low` | 2.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_wind.mid` | 8.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `gas_basis_differential.CAISO` | 1.2 | 2 | EIA Natural Gas Weekly Update | 2024 |  |
| `gas_basis_differential.ERCOT` | -0.5 | 2 | EIA Natural Gas Weekly Update | 2024 |  |
| `gas_basis_differential.NYISO` | 0.55 | 2 | EIA-923 delivered-gas basis (see below) |  | auto-generated, needs-citation |
| `gas_basis_differential.PJM` | 0.67 | 2 | TETCO M3 / Transco Z6 / Dominion South blend; Tier 3 — verify |  | auto-generated, needs-citation |
| `gas_monthly_seasonality` | {"1": 1.15, "2": 1.1, "3": 1.02, "4":… | 2 | EIA Henry Hub monthly spot prices | 2024 |  |
| `global_annual_deployment_gw.gas_cc` | 20.0 | 2 | was 25. IEA WEO 2025. | 2025 | auto-generated |
| `henry_hub_trajectories.high` | {"2023": 2.54, "2024": 2.19, "2025": … | 1 | EIA Annual Energy Outlook 2025 | 2025-04 | modeled |
| `henry_hub_trajectories.low` | {"2023": 2.54, "2024": 2.19, "2025": … | 1 | EIA Annual Energy Outlook 2025 | 2025-04 | modeled |
| `henry_hub_trajectories.mid` | {"2023": 2.54, "2024": 2.19, "2025": … | 1 | EIA Annual Energy Outlook 2025 | 2025-04 | modeled |
| `oil_price_per_mmbtu` | 18.0 | 2 | Delivered oil fuel price ($/MMBtu) for oil-fired peakers and steam … | 2023 | auto-generated |
| `queue_cap_per_tech_gw.CAISO.gas_cc` | 2.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.ERCOT.gas_cc` | 3.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.MISO.gas_cc` | 3.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.NEISO.gas_cc` | 1.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.NYISO.gas_cc` | 1.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.PJM.gas_cc` | 4.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.SPP.gas_cc` | 2.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `scenario.coal_committed_hr_mult` | 1.22 | 3 | Coal part-load penalty ~22% |  | auto-generated, needs-citation |
| `scenario.coal_drop_pof` | False | 3 | When True, drop the statistical planned-outage (POF) derate on coal… |  | auto-generated, needs-citation |
| `scenario.coal_econ_hr_mult` | 0.97 | 3 | Coal incremental HR |  | auto-generated, needs-citation |
| `scenario.coal_lignite_mustrun_override` | None | 3 | Tier 3 (calibration) — CAMPD coal must-run overrides. When set, rep… |  | auto-generated, needs-citation |
| `scenario.coal_mustrun_per_plant` | False | 3 | When True, coal must-run % comes from the per-plant CAMPD-derived t… |  | auto-generated, needs-citation |
| `scenario.coal_peak_hr_penalty` | 1.08 | 3 | Coal peaking increment |  | auto-generated, needs-citation |
| `scenario.coal_plant_monthly_pricing` | True | 3 | When True (default), coal generators that report EIA-923 monthly fu… |  | auto-generated, needs-citation |
| `scenario.coal_prb_contract_passthrough` | 1.0 | 3 | Tier 3 (calibration) — CAMPD coal pricing. Plant-specific coal deli… |  | auto-generated, needs-citation |
| `scenario.coal_prb_follower_ceil` | 1.35 | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_prb_follower_floor` | 0.68 | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_prb_follower_gas_mid` | 2.85 | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_prb_follower_gas_slope` | 2.5 | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_prb_follower_mustrun_max` | 25.0 | 3 | MR% <= this -> follower tier |  | auto-generated, needs-citation |
| `scenario.coal_prb_mustrun_override` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_prb_passthrough` | 1.0 | 3 | Tier 3 (calibration) — CAMPD coal committed-tranche price-taking. A… |  | auto-generated, needs-citation |
| `scenario.coal_prb_passthrough_ceil` | 1.5 | 3 | dear-gas asymptote (>1 = markup) |  | auto-generated, needs-citation |
| `scenario.coal_prb_passthrough_floor` | 0.78 | 3 | cheap-gas asymptote |  | auto-generated, needs-citation |
| `scenario.coal_prb_passthrough_gas_mid` | 2.85 | 3 | $/MMBtu logistic midpoint |  | auto-generated, needs-citation |
| `scenario.coal_prb_passthrough_gas_slope` | 2.5 | 3 | logistic slope per $/MMBtu |  | auto-generated, needs-citation |
| `scenario.coal_prb_passthrough_sigmoid` | False | 3 | Tier 3 (calibration) — gas-keyed PRB passthrough sigmoid. When True… | 2023 | auto-generated |
| `scenario.coal_prb_passthrough_tiered` | False | 3 | Tier 3 (calibration) — tiered PRB passthrough. When True, PRB plant… |  | auto-generated, needs-citation |
| `scenario.coal_supply_repricing` | True | 3 | When True (default), coal generators are repriced to the flat annua… |  | auto-generated, needs-citation |
| `scenario.dual_fuel_switching` | False | 3 | Tier 3 (calibration) — dual-fuel switching (doc 03 Pack G). Gas uni… |  | auto-generated, needs-citation |
| `scenario.eac_price_geothermal` | 0.0 | 1 | $/MWh, clean firm generation credit |  | auto-generated, needs-citation |
| `scenario.eac_price_nuclear` | 0.0 | 1 | $/MWh, e.g. NY/IL Zero Emission Credit ~$17 |  | auto-generated, needs-citation |
| `scenario.eac_price_offshore_wind` | 0.0 | 1 | $/MWh, offshore-specific EAC (may differ from onshore) |  | auto-generated, needs-citation |
| `scenario.eac_price_solar` | 0.0 | 1 | $/MWh |  | auto-generated, needs-citation |
| `scenario.eac_price_wind` | 0.0 | 1 | $/MWh, onshore wind REC |  | auto-generated, needs-citation |
| `scenario.gas_monthly_actuals` | False | 3 | Tier 3 (calibration) — price gas at the ISO's measured EIA-923 mont… | 2024 | auto-generated |
| `scenario.gas_plant_monthly_fuel_pricing` | False | 2 | Per-plant monthly gas pricing. OFF by default: every gas generator … |  | auto-generated, needs-citation |
| `scenario.gas_price_override` | None | 3 | When set, pins the annual |  | auto-generated, needs-citation |
| `scenario.gas_price_path` | mid | 1 | Market simulator model design decision | 2026-05 |  |
| `scenario.gas_seasonality` | True | 2 | Market simulator model design decision | 2026-05 |  |
| `scenario.gas_st_committed_hr_mult` | 1.32 | 3 | Gas steam part-load penalty ~32% |  | auto-generated, needs-citation |
| `scenario.gas_st_committed_hr_override` | None | 3 | Reliability gas-steam (ST_GAS) tranche heat-rate OVERRIDES (relativ… |  | auto-generated, needs-citation |
| `scenario.gas_st_econ_hr_mult` | 0.97 | 3 | Gas steam incremental HR |  | auto-generated, needs-citation |
| `scenario.gas_st_econ_hr_override` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.gas_st_offsummer_mustrun` | 0.0 | 3 | Off-summer (Oct-Apr) ST_GAS reliability min-gen floor, as a fractio… |  | auto-generated, needs-citation |
| `scenario.gas_st_peak_hr_override` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.gas_st_summer_mustrun` | 0.0 | 3 | Legacy gas-steam (ST_GAS) summer reliability treatment. When gas_st… |  | auto-generated, needs-citation |
| `scenario.nearby_fuel_price_fallback` | False | 3 | Tier 3 (calibration) — "nearby plant" fuel-cost fallback. When True… |  | auto-generated, needs-citation |
| `scenario.nearby_fuel_price_min_state_plants` | 2 | 3 | state-mean sample floor; |  | auto-generated, needs-citation |
| `wright_reference_gw.gas_cc` | 1220.0 | 2 | was 1200. IEA WEO 2025. | 2025 | auto-generated |

## Market Design

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `market_design.CAISO` | {"capacity_market": true, "net_cone_p… | 2 | Per-ISO market design. ISOs absent here fall back to ``DEFAULT_MARK… |  | auto-generated, needs-citation |
| `market_design.ERCOT` | {"capacity_market": false, "net_cone_… | 2 | Per-ISO market design. ISOs absent here fall back to ``DEFAULT_MARK… |  | auto-generated, needs-citation |
| `market_design.NEISO` | {"capacity_market": true, "net_cone_p… | 2 | Per-ISO market design. ISOs absent here fall back to ``DEFAULT_MARK… |  | auto-generated, needs-citation |
| `market_design.NYISO` | {"capacity_market": true, "net_cone_p… | 2 | Per-ISO market design. ISOs absent here fall back to ``DEFAULT_MARK… |  | auto-generated, needs-citation |
| `market_design.PJM` | {"capacity_market": true, "net_cone_p… | 2 | Per-ISO market design. ISOs absent here fall back to ``DEFAULT_MARK… |  | auto-generated, needs-citation |

## Policy

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `carbon_price_paths.high` | {"2026": 0, "2030": 30, "2040": 70, "… | 1 | Resources for the Future (RFF) carbon price scenario set | 2023-09 | modeled |
| `carbon_price_paths.low` | {"2026": 0, "2030": 8, "2040": 18, "2… | 1 | Resources for the Future (RFF) carbon price scenario set | 2023-09 | modeled |
| `carbon_price_paths.mid` | {"2026": 0, "2030": 15, "2040": 35, "… | 1 | Resources for the Future (RFF) carbon price scenario set | 2023-09 | modeled |
| `carbon_price_paths.zero` | {"2026": 0, "2030": 0, "2040": 0, "20… | 1 | Resources for the Future (RFF) carbon price scenario set | 2023-09 | modeled |
| `scenario.carbon_price` | 0.0 | 1 | Market simulator model design decision | 2026-05 |  |
| `scenario.ira_expiry_year` | 2035 | 2 | CBO scoring of Inflation Reduction Act energy provisions | 2023-04 | modeled, stale |
| `scenario.ira_itc_solar` | 0.3 | 2 | IRS Inflation Reduction Act final rules (IRC sections 45, 48, 48E) | 2024-04 |  |
| `scenario.ira_itc_storage` | 0.3 | 2 | IRS Inflation Reduction Act final rules (IRC sections 45, 48, 48E) | 2024-04 |  |
| `scenario.ira_other_clean_last_full_year` | 2028 | 2 | Other clean (storage, nuclear, geothermal, hydro): §48E graduated p… | 2029 | auto-generated |
| `scenario.ira_other_clean_phaseout_end` | 2033 | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.ira_ptc_wind` | 26.0 | 2 | IRS Inflation Reduction Act final rules (IRC sections 45, 48, 48E) | 2024-04 |  |
| `scenario.ira_wind_solar_last_year` | 2027 | 2 | IRA credit schedule per OBBBA (One Big Beautiful Bill Act), enacted… | 2025 | auto-generated |
| `scenario.nox_price` | 0.0 | 1 | Market simulator model design decision | 2026-05 |  |
| `scenario.rps_enabled` | True | 1 | whether to enforce RPS as LP constraint |  | auto-generated, needs-citation |
| `state_rps_floors.CAISO` | {"2026": 0.5, "2030": 0.6, "2040": 0.… | 1 | California SB 100 — The 100 Percent Clean Energy Act of 2018 | 2018-09 | stale |
| `state_rps_floors.ERCOT` | {"2026": 0.0, "2030": 0.0, "2040": 0.… | 1 | Market simulator model design decision | 2026-05 |  |
| `state_rps_floors.NEISO` | {"2026": 0.3, "2030": 0.45, "2040": 0… | 2 | MA Clean Energy Standard + regional state CES blend |  | auto-generated, needs-citation |
| `state_rps_floors.NYISO` | {"2026": 0.4, "2030": 0.7, "2040": 1.… | 2 | NY CLCPA — 70% renewable by 2030, 100% zero-emission by 2040 | 2030 | auto-generated |

## Reliability

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `eford.biomass` | 0.08 | 2 | NERC GADS — biomass steam |  | auto-generated, needs-citation |
| `eford.coal` | 0.08 | 2 | NERC Generating Availability Data System (GADS), 2018-2022 | 2023-08 |  |
| `eford.gas_cc` | 0.05 | 2 | NERC Generating Availability Data System (GADS), 2018-2022 | 2023-08 |  |
| `eford.gas_ct` | 0.06 | 2 | NERC Generating Availability Data System (GADS), 2018-2022 | 2023-08 |  |
| `eford.gas_st` | 0.07 | 2 | NERC GADS — legacy gas steam (older, higher outage rate) |  | auto-generated, needs-citation |
| `eford.nuclear` | 0.03 | 2 | NERC Generating Availability Data System (GADS), 2018-2022 | 2023-08 |  |
| `eford.oil` | 0.1 | 2 | NERC GADS — oil peakers (infrequent run, higher EFOR) |  | auto-generated, needs-citation |
| `gas_availability_factor.CAISO` | 0.89 | 2 | NERC Generating Availability Data System (GADS), 2018-2022 | 2023-08 |  |
| `gas_availability_factor.ERCOT` | 0.85 | 2 | NERC Generating Availability Data System (GADS), 2018-2022 | 2023-08 |  |
| `gas_availability_factor.NEISO` | 0.85 | 2 | NERC GADS 2019-2023, ISO-NE fleet. TODO: verify | 2019 | auto-generated |
| `gas_availability_factor.NYISO` | 0.86 | 2 | NERC GADS 2019-2023, NYISO fleet. TODO: verify | 2019 | auto-generated |
| `gas_availability_factor.PJM` | 0.87 | 2 | NERC GADS 2019-2023, PJM fleet. TODO: verify | 2019 | auto-generated |
| `geothermal_params.egs.eford` | 0.05 | 2 | comparable to nuclear. DOE GeoVision 2019 | 2019 | auto-generated |
| `hydrogen_turbine_params.h2_ccgt.eford` | 0.06 | 2 | above gas CT — immature fleet. Engineering judgment |  | auto-generated, needs-citation |
| `hydrogen_turbine_params.h2_ct.eford` | 0.06 | 2 | above gas CT — immature fleet. Engineering judgment |  | auto-generated, needs-citation |
| `import_eford.CAISO` | 0.02 | 2 | Import tranche forced outage rate, per ISO. CAISO's WECC supply blo… |  | auto-generated, needs-citation |
| `import_eford.PJM` | 0.0 | 2 | Import tranche forced outage rate, per ISO. CAISO's WECC supply blo… |  | auto-generated, needs-citation |
| `nuclear_monthly_cf.CAISO` | [1.0, 0.99, 0.96, 0.95, 0.97, 1.0, 1.… | 2 | NRC / IAEA Power Reactor Information System (PRIS), 2019-2023 | 2024-01 |  |
| `nuclear_monthly_cf.ERCOT` | [0.97, 0.99, 0.89, 0.78, 0.84, 0.93, … | 2 | NRC / IAEA Power Reactor Information System (PRIS), 2019-2023 | 2024-01 |  |
| `scenario.cc_outage_derate_from_top` | False | 2 | Outage capacity comes off the TOP of a CC_REGULAR plant's offer sta… |  | auto-generated, needs-citation |
| `scenario.historic_outage_overlay` | True | 2 | Historic (facility-summed) CAMPD outage overlay: hard-zeros coal/CC… |  | auto-generated, needs-citation |
| `scenario.outage_source` | statistical | 3 | Tier 3 (calibration) — thermal availability source. "statistical" (… |  | auto-generated, needs-citation |
| `scenario.retirement_fom_multiplier_coal` | 1.3 | 2 | coal faces higher effective FOM |  | auto-generated, needs-citation |
| `scenario.retirement_fom_multiplier_gas_cc` | 1.0 | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.retirement_fom_multiplier_gas_ct` | 1.0 | 2 | (regulatory risk, carbon liability, rising insurance). Source: Laza… | 2024 | auto-generated |
| `scenario.retirement_reserve_margin` | 0.15 | 2 | 15% reserve margin over peak net demand |  | auto-generated, needs-citation |
| `scenario.retirement_years_coal` | 1 | 2 | coal retires after 1 unprofitable year |  | auto-generated, needs-citation |
| `scenario.retirement_years_gas_cc` | 3 | 2 | modern CCs get 3 years (most flexible/valuable) |  | auto-generated, needs-citation |
| `scenario.retirement_years_gas_ct` | 2 | 2 | CTs get 2 years |  | auto-generated, needs-citation |
| `scenario.voll` | 5000.0 | 0 | Public Utility Commission of Texas / ERCOT Nodal Protocols | 2023-01 | stale |
| `scenario.wefor_multiplier` | 1.0 | 3 | Global scale on every thermal class's |  | auto-generated, needs-citation |
| `thermal_availability.BIOMASS` | [0.07, 0.1, 0.002, 25, 0.04, 0.0015, 25] | 2 | Thermal-fleet availability model by plant-group category. Three add… |  | auto-generated, needs-citation |
| `thermal_availability.CC_CHP` | [0.05, 0.04, 0.002, 20, 0.02, 0.001, 25] | 2 | Thermal-fleet availability model by plant-group category. Three add… |  | auto-generated, needs-citation |
| `thermal_availability.CC_REGULAR` | [0.05, 0.05, 0.002, 20, 0.02, 0.001, 25] | 2 | Thermal-fleet availability model by plant-group category. Three add… |  | auto-generated, needs-citation |
| `thermal_availability.COAL` | [0.07, 0.12, 0.005, 40, 0.03, 0.002, 35] | 2 | Thermal-fleet availability model by plant-group category. Three add… |  | auto-generated, needs-citation |
| `thermal_availability.CT_CHP` | [0.03, 0.05, 0.002, 20, 0.03, 0.001, 20] | 2 | Thermal-fleet availability model by plant-group category. Three add… |  | auto-generated, needs-citation |
| `thermal_availability.CT_PEAKER` | [0.03, 0.07, 0.003, 20, 0.05, 0.002, 20] | 2 | Thermal-fleet availability model by plant-group category. Three add… |  | auto-generated, needs-citation |
| `thermal_availability.OIL` | [0.06, 0.1, 0.003, 30, 0.04, 0.002, 30] | 2 | Thermal-fleet availability model by plant-group category. Three add… |  | auto-generated, needs-citation |
| `thermal_availability.ST_CHP` | [0.05, 0.08, 0.002, 25, 0.03, 0.0015,… | 2 | Thermal-fleet availability model by plant-group category. Three add… |  | auto-generated, needs-citation |
| `thermal_availability.ST_GAS` | [0.06, 0.21, 0.003, 30, 0.04, 0.002, 30] | 2 | Thermal-fleet availability model by plant-group category. Three add… |  | auto-generated, needs-citation |
| `wecc_import_eford` | 0.02 | 2 | WECC import tranche forced outage rate. Source: NERC GADS — represe… |  | auto-generated, needs-citation |

## Storage

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `eac_price_reference.eac_storage.high` | 10.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_storage.low` | 0.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_storage.mid` | 5.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `pumped_storage_dispatch_adder_by_iso.PJM` | 10.0 | 2 | Pumped-storage dispatch adder ($/MWh discharged) by ISO — the reduc… | 2026-06 | auto-generated |
| `pumped_storage_duration_hours` | 10.0 | 2 | Pumped-storage hydro fleet parameters (EIA-860 PS units enter the s… | 2023 | auto-generated |
| `pumped_storage_rte` | 0.8 | 2 | Round-trip efficiency: mid-range of the 70-85% PSH band (DOE/Sandia… |  | auto-generated, needs-citation |
| `scenario.co2_transport_storage_cost` | 15.0 | 2 | $/tCO2 for captured CO2 |  | auto-generated, needs-citation |
| `scenario.eac_price_storage` | 0.0 | 1 | $/MWh on discharge |  | auto-generated, needs-citation |
| `scenario.pumped_storage_dispatch_adder` | None | 3 | Tier 3 — pumped-storage dispatch adder ($/MWh discharged). PSH pure… |  | auto-generated, needs-citation |
| `scenario.storage_capacity_value` | True | 2 | Storage new-entry value stack. ``storage_capacity_value`` globally … |  | auto-generated, needs-citation |
| `scenario.storage_daily_cycling` | False | 2 | When True, each storage unit's SOC |  | auto-generated, needs-citation |
| `scenario.storage_degradation` | True | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.storage_deployment` | mid | 1 | Market simulator model design decision | 2026-05 |  |
| `scenario.storage_rte_4hr` | 0.85 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `scenario.storage_rte_8hr` | 0.8 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `storage_annual_build_cap_mw.CAISO` | 3000.0 | 2 | Max new storage power per year (MW). Source: ERCOT CDR, CAISO TPP q… |  | auto-generated, needs-citation |
| `storage_annual_build_cap_mw.ERCOT` | 5000.0 | 2 | Max new storage power per year (MW). Source: ERCOT CDR, CAISO TPP q… |  | auto-generated, needs-citation |
| `storage_annual_build_cap_mw.NEISO` | 1200.0 | 2 | Source: ISO-NE interconnection queue 2024 | 2024 | auto-generated |
| `storage_annual_build_cap_mw.NYISO` | 1500.0 | 2 | Source: NYISO interconnection queue 2024 | 2024 | auto-generated |
| `storage_annual_build_cap_mw.PJM` | 4000.0 | 2 | large queue but slower interconnection. Source: PJM queue 2024 | 2024 | auto-generated |
| `storage_base_fleet_mw.CAISO.high` | 12000.0 | 2 | Storage power capacity (MW) for the base year (2026). Subsequent ye… | 2026 | auto-generated |
| `storage_base_fleet_mw.CAISO.low` | 6000.0 | 2 | Storage power capacity (MW) for the base year (2026). Subsequent ye… | 2026 | auto-generated |
| `storage_base_fleet_mw.CAISO.mid` | 8000.0 | 2 | Storage power capacity (MW) for the base year (2026). Subsequent ye… | 2026 | auto-generated |
| `storage_base_fleet_mw.ERCOT.high` | 25000.0 | 2 | Storage power capacity (MW) for the base year (2026). Subsequent ye… | 2026 | auto-generated |
| `storage_base_fleet_mw.ERCOT.low` | 12000.0 | 2 | Storage power capacity (MW) for the base year (2026). Subsequent ye… | 2026 | auto-generated |
| `storage_base_fleet_mw.ERCOT.mid` | 17000.0 | 2 | Storage power capacity (MW) for the base year (2026). Subsequent ye… | 2026 | auto-generated |
| `storage_base_fleet_mw.NEISO.high` | 2000.0 | 2 | Storage power capacity (MW) for the base year (2026). Subsequent ye… | 2026 | auto-generated |
| `storage_base_fleet_mw.NEISO.low` | 500.0 | 2 | Storage power capacity (MW) for the base year (2026). Subsequent ye… | 2026 | auto-generated |
| `storage_base_fleet_mw.NEISO.mid` | 1000.0 | 2 | Storage power capacity (MW) for the base year (2026). Subsequent ye… | 2026 | auto-generated |
| `storage_base_fleet_mw.NYISO.high` | 3000.0 | 2 | Storage power capacity (MW) for the base year (2026). Subsequent ye… | 2026 | auto-generated |
| `storage_base_fleet_mw.NYISO.low` | 1000.0 | 2 | Storage power capacity (MW) for the base year (2026). Subsequent ye… | 2026 | auto-generated |
| `storage_base_fleet_mw.NYISO.mid` | 1500.0 | 2 | Storage power capacity (MW) for the base year (2026). Subsequent ye… | 2026 | auto-generated |
| `storage_base_fleet_mw.PJM.high` | 9000.0 | 2 | Storage power capacity (MW) for the base year (2026). Subsequent ye… | 2026 | auto-generated |
| `storage_base_fleet_mw.PJM.low` | 3000.0 | 2 | Storage power capacity (MW) for the base year (2026). Subsequent ye… | 2026 | auto-generated |
| `storage_base_fleet_mw.PJM.mid` | 5000.0 | 2 | Storage power capacity (MW) for the base year (2026). Subsequent ye… | 2026 | auto-generated |
| `storage_degradation_replacement_fraction` | 0.25 | 2 | Cycling-degradation cost. Each MWh discharged consumes a slice of t… |  | auto-generated, needs-citation |
| `storage_deployment_ceiling_mw.CAISO` | 25000.0 | 2 | ~52% of ~48 GW peak. Source: CAISO IEPR |  | auto-generated, needs-citation |
| `storage_deployment_ceiling_mw.ERCOT` | 45000.0 | 2 | ~53% of ~85 GW peak. Source: ERCOT CDR |  | auto-generated, needs-citation |
| `storage_deployment_ceiling_mw.NEISO` | 13000.0 | 2 | ~50% of ~26 GW peak. Source: ISO-NE CELT Report 2024 | 2024 | auto-generated |
| `storage_deployment_ceiling_mw.NYISO` | 16000.0 | 2 | ~50% of ~32 GW peak. Source: NYISO Gold Book 2024 | 2024 | auto-generated |
| `storage_deployment_ceiling_mw.PJM` | 75000.0 | 2 | ~50% of ~150 GW peak. Source: PJM Load Forecast Report 2024 | 2024 | auto-generated |
| `storage_elcc_by_duration` | [[2.0, 0.4], [4.0, 0.6], [6.0, 0.75],… | 2 | Effective load-carrying capability (ELCC) of storage as a function … |  | auto-generated, needs-citation |
| `storage_elcc_saturation_exponent` | 1.5 | 2 | Marginal ELCC saturation. As cumulative storage power approaches th… |  | auto-generated, needs-citation |
| `storage_tech_build_share_cap` | 0.6 | 2 | Cap on the share of one year's storage build budget that any single… |  | auto-generated, needs-citation |
| `storage_tech_power_share.iron_air` | 0.05 | 2 | Share of deployed storage power by technology type. Source: NREL AT… | 2024 | auto-generated |
| `storage_tech_power_share.li_ion_4hr` | 0.7 | 2 | Share of deployed storage power by technology type. Source: NREL AT… | 2024 | auto-generated |
| `storage_tech_power_share.li_ion_8hr` | 0.25 | 2 | Share of deployed storage power by technology type. Source: NREL AT… | 2024 | auto-generated |
| `storage_techs.compressed_air.capex_per_kw` | 2700.0 | 2 | was 1380. ~$285/kWh × 4hr. NREL ATB 2024b, BNEF 2025. | 2025 | auto-generated |
| `storage_techs.compressed_air.capex_per_kwh` | 150.0 | 2 | was 345. LFP pack costs ~$100/kWh + BOS. |  | auto-generated, needs-citation |
| `storage_techs.compressed_air.cycles` | 10000 | 2 | long cycle life — major advantage. PNNL 2023 | 2023 | auto-generated |
| `storage_techs.compressed_air.duration_hr` | 8 | 2 | Storage technology parameters. Source: NREL ATB 2024 (li-ion), DOE … | 2024 | auto-generated |
| `storage_techs.compressed_air.fom_per_kw_yr` | 10.0 | 2 | was 34.5. |  | auto-generated, needs-citation |
| `storage_techs.compressed_air.learning_rate` | 0.05 | 2 | BNEF lithium-ion learning curve 2024 | 2024 | auto-generated |
| `storage_techs.compressed_air.lifetime_yr` | 40 | 2 | Huntorf plant operating since 1978 | 1978 | auto-generated |
| `storage_techs.compressed_air.rte` | 0.55 | 2 | lower RTE at longer duration. NREL ATB 2024 | 2024 | auto-generated |
| `storage_techs.flow_battery.capex_per_kw` | 4700.0 | 2 | was 1380. ~$285/kWh × 4hr. NREL ATB 2024b, BNEF 2025. | 2025 | auto-generated |
| `storage_techs.flow_battery.capex_per_kwh` | 350.0 | 2 | was 345. LFP pack costs ~$100/kWh + BOS. |  | auto-generated, needs-citation |
| `storage_techs.flow_battery.cycles` | 15000 | 2 | long cycle life — major advantage. PNNL 2023 | 2023 | auto-generated |
| `storage_techs.flow_battery.duration_hr` | 10 | 2 | Storage technology parameters. Source: NREL ATB 2024 (li-ion), DOE … | 2024 | auto-generated |
| `storage_techs.flow_battery.fom_per_kw_yr` | 15.0 | 2 | was 34.5. |  | auto-generated, needs-citation |
| `storage_techs.flow_battery.learning_rate` | 0.1 | 2 | BNEF lithium-ion learning curve 2024 | 2024 | auto-generated |
| `storage_techs.flow_battery.lifetime_yr` | 25 | 2 | Huntorf plant operating since 1978 | 1978 | auto-generated |
| `storage_techs.flow_battery.rte` | 0.7 | 2 | lower RTE at longer duration. NREL ATB 2024 | 2024 | auto-generated |
| `storage_techs.iron_air.capex_per_kw` | 2000.0 | 2 | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | stale |
| `storage_techs.iron_air.capex_per_kwh` | 20.0 | 2 | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | stale |
| `storage_techs.iron_air.cycles` | 3000 | 2 | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | stale |
| `storage_techs.iron_air.duration_hr` | 100 | 2 | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | stale |
| `storage_techs.iron_air.fom_per_kw_yr` | 20.0 | 2 | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | stale |
| `storage_techs.iron_air.learning_rate` | 0.1 | 2 | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | modeled, stale |
| `storage_techs.iron_air.rte` | 0.5 | 2 | DOE Pathways to Commercial Liftoff: Long Duration Energy Storage | 2023-03 | stale |
| `storage_techs.li_ion_12hr.capex_per_kw` | 3100.0 | 2 | was 1380. ~$285/kWh × 4hr. NREL ATB 2024b, BNEF 2025. | 2025 | auto-generated |
| `storage_techs.li_ion_12hr.capex_per_kwh` | 240.0 | 2 | was 345. LFP pack costs ~$100/kWh + BOS. |  | auto-generated, needs-citation |
| `storage_techs.li_ion_12hr.cycles` | 4000 | 2 | long cycle life — major advantage. PNNL 2023 | 2023 | auto-generated |
| `storage_techs.li_ion_12hr.duration_hr` | 12 | 2 | Storage technology parameters. Source: NREL ATB 2024 (li-ion), DOE … | 2024 | auto-generated |
| `storage_techs.li_ion_12hr.fom_per_kw_yr` | 10.0 | 2 | was 34.5. |  | auto-generated, needs-citation |
| `storage_techs.li_ion_12hr.learning_rate` | 0.15 | 2 | BNEF lithium-ion learning curve 2024 | 2024 | auto-generated |
| `storage_techs.li_ion_12hr.lifetime_yr` | 20 | 2 | Huntorf plant operating since 1978 | 1978 | auto-generated |
| `storage_techs.li_ion_12hr.rte` | 0.78 | 2 | lower RTE at longer duration. NREL ATB 2024 | 2024 | auto-generated |
| `storage_techs.li_ion_4hr.capex_per_kw` | 1140.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `storage_techs.li_ion_4hr.capex_per_kwh` | 285.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `storage_techs.li_ion_4hr.cycles` | 5000 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `storage_techs.li_ion_4hr.duration_hr` | 4 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `storage_techs.li_ion_4hr.fom_per_kw_yr` | 30.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `storage_techs.li_ion_4hr.learning_rate` | 0.18 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | modeled |
| `storage_techs.li_ion_4hr.rte` | 0.86 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `storage_techs.li_ion_8hr.capex_per_kw` | 2280.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `storage_techs.li_ion_8hr.capex_per_kwh` | 285.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `storage_techs.li_ion_8hr.cycles` | 5000 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `storage_techs.li_ion_8hr.duration_hr` | 8 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `storage_techs.li_ion_8hr.fom_per_kw_yr` | 48.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `storage_techs.li_ion_8hr.learning_rate` | 0.18 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 | modeled |
| `storage_techs.li_ion_8hr.rte` | 0.86 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |

## Structural

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `end_year` | 2050 | 0 | Market simulator model design decision | 2026-05 |  |
| `hours_per_year` | 8760 | 0 | Market simulator model design decision | 2026-05 |  |
| `scenario.campd_bins_path` | inputs/custom-bin-assignments.csv | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.cc_committed_hr_mult` | 1.23 | 3 | CC part-load penalty ~23% |  | auto-generated, needs-citation |
| `scenario.cc_committed_hr_override` | None | 3 | Combined-cycle tranche heat-rate OVERRIDES (relative to the plant's… |  | auto-generated, needs-citation |
| `scenario.cc_committed_per_plant` | False | 2 | When True, each CC_REGULAR bin's committed-tranche % (minimum stabl… |  | auto-generated, needs-citation |
| `scenario.cc_econ_hr_mult` | 0.96 | 3 | CC incremental HR ~4% below avg |  | auto-generated, needs-citation |
| `scenario.cc_econ_hr_override` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.cc_peak_hr_override` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.cc_peak_hr_penalty` | 1.15 | 3 | CC duct-firing increment |  | auto-generated, needs-citation |
| `scenario.cc_peaking_per_plant` | False | 2 | When True, the CC_REGULAR plants in fleet.CC_REGULAR_PEAKING_PCT_BY… |  | auto-generated, needs-citation |
| `scenario.chp_btm_floor_pct` | 40.0 | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.chp_steam_following` | False | 3 | CHP cogeneration treatment. When chp_steam_following is True, each … |  | auto-generated, needs-citation |
| `scenario.ct_committed_hr_mult` | 1.28 | 3 | CT part-load penalty ~28% |  | auto-generated, needs-citation |
| `scenario.ct_committed_hr_override` | None | 3 | CT_CHP tranche heat-rate overrides (relative to base HR), applied t… |  | auto-generated, needs-citation |
| `scenario.ct_econ_hr_mult` | 0.97 | 3 | CT incremental HR ~3% below avg |  | auto-generated, needs-citation |
| `scenario.ct_econ_hr_override` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.ct_peak_hr_override` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.ct_peak_hr_penalty` | 1.1 | 3 | CT / gas-steam peaking increment |  | auto-generated, needs-citation |
| `scenario.econ_split_by_group` | {} | 2 | Economic-tranche split. Maps a CAMPD bin's Plant_Group to a 3-eleme… |  | auto-generated, needs-citation |
| `scenario.egs_available_year` | 2030 | 1 | year EGS enters the candidate pool |  | auto-generated, needs-citation |
| `scenario.egs_pmin_fraction` | 0.2 | 2 | EGS turn-down floor (fraction of rated) |  | auto-generated, needs-citation |
| `scenario.hours` | 8760 | 0 | Market simulator model design decision | 2026-05 |  |
| `scenario.iso` | ERCOT | 0 | Market simulator model design decision | 2026-05 |  |
| `scenario.mode` | forecast | 0 | "forecast" \| "backcast". Backcast pins the run |  | auto-generated, needs-citation |
| `scenario.must_run_cf` | 0.85 | 3 | assumed CF for CHP must-run emissions post-processing |  | auto-generated, needs-citation |
| `scenario.plant_level_fleet` | False | 3 | Tier 3 (calibration) — keep the non-ERCOT fleet at full per-plant g… |  | auto-generated, needs-citation |
| `scenario.plant_registry_path` | inputs/master-plant-registry.csv | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.use_campd_bins` | True | 2 | Tier 2 (expert/sensitivity) — CAMPD operational binning When True t… |  | auto-generated, needs-citation |
| `scenario.weather_year` | 2024 | 0 | Market simulator model design decision | 2026-05 |  |
| `start_year` | 2026 | 0 | Market simulator model design decision | 2026-05 |  |
| `storage_tiebreaker_epsilon` | 0.001 | 0 | Market simulator model design decision | 2026-05 |  |

## Supply Stack

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `cc_commitment_params` | [[6.5, {"startup_per_mw": 63.8, "min_… | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `cc_startup_params` | [[6.5, 63.8], [7.5, 48.6], [99.0, 24.1]] | 2 | CC/CT startup costs ($/MW per start) keyed by ascending heat-rate c… | 2012 | auto-generated |
| `ccs_retrofit_hr_penalty_reference.default` | 0.12 | 2 | CCS retrofit heat rate penalty: parasitic load from amine scrubbing… | 2021 | auto-generated |
| `ccs_retrofit_hr_penalty_reference.netl_ngcc_range` | [0.1, 0.16] | 2 | CCS retrofit heat rate penalty: parasitic load from amine scrubbing… | 2021 | auto-generated |
| `ccs_retrofit_hr_penalty_reference.source` | NETL Cost & Performance Baseline for … | 2 | CCS retrofit heat rate penalty: parasitic load from amine scrubbing… | 2021 | auto-generated |
| `ccus_params.gas_cc_ccs_90.capex_kw` | 2500.0 | 2 | $/kW installed. NREL ATB 2024 | 2024 | auto-generated |
| `ccus_params.gas_cc_ccs_90.capture_rate` | 0.9 | 2 | fraction of CO2 captured. NETL 2022 Case B31B | 2022 | auto-generated |
| `ccus_params.gas_cc_ccs_90.co2_transport_storage` | 15.0 | 2 | $/tCO2 — pipeline + saline injection. NETL 2022, Gulf Coast | 2022 | auto-generated |
| `ccus_params.gas_cc_ccs_90.fom_kw_yr` | 22.0 | 2 | $/kW-yr. NREL ATB 2024 | 2024 | auto-generated |
| `ccus_params.gas_cc_ccs_90.heat_rate_penalty` | 1.16 | 2 | ×base CC heat rate — 16% parasitic. NETL 2022 Rev 4, Case B31B | 2022 | auto-generated |
| `ccus_params.gas_cc_ccs_90.learning_rate` | 0.05 | 2 | slow — limited deployment. Global CCS Institute 2024 | 2024 | auto-generated |
| `ccus_params.gas_cc_ccs_90.lifetime_yr` | 30 | 2 | Carbon capture, utilization and storage parameters. CCUS is a varia… |  | auto-generated, needs-citation |
| `ccus_params.gas_cc_ccs_90.vom_adder` | 8.0 | 2 | $/MWh — amine solvent, maintenance. NETL 2022 | 2022 | auto-generated |
| `coal_tranches` | [[0.3, 0.0], [0.25, 0.35], [0.45, 1.0]] | 2 | Coal take-or-pay supply-curve tranches: (capacity_fraction, fuel_pa… | 2023 | auto-generated |
| `ct_commitment_params` | [[10.0, {"startup_per_mw": 12.3, "min… | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `ct_startup_params` | [[10.0, 12.3], [11.0, 24.5], [99.0, 1… | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `eac_price_reference.eac_gas_cc_ccs.high` | 25.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_gas_cc_ccs.low` | 10.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_gas_cc_ccs.mid` | 15.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `export_tranches.CAISO` | [["export_sink", 5000.0, 0.0]] | 2 | Export sinks: each block absorbs up to its capacity as *negative* g… |  | auto-generated, needs-citation |
| `export_tranches.PJM` | [["export_firm", 700.0, 42.0], ["expo… | 2 | Export sinks: each block absorbs up to its capacity as *negative* g… |  | auto-generated, needs-citation |
| `geothermal_params.egs.heat_rate` | 0.0 | 2 | no fuel |  | auto-generated, needs-citation |
| `geothermal_params.egs.vom` | 1.0 | 2 | $/MWh — minimal, no fuel. NREL ATB 2024 | 2024 | auto-generated |
| `global_annual_deployment_gw.gas_cc_ccs` | 1.5 | 2 | GW/yr global CCS additions on power plants. |  | auto-generated, needs-citation |
| `global_annual_deployment_gw.nuclear` | 10.0 | 2 | was 8. IAEA 2025. | 2025 | auto-generated |
| `global_annual_deployment_gw.nuclear_large` | 5.0 | 2 | Annual global deployment (GW/yr) by technology, used to project cum… | 2025 | auto-generated |
| `global_annual_deployment_gw.nuclear_smr` | 5.0 | 2 | Annual global deployment (GW/yr) by technology, used to project cum… | 2025 | auto-generated |
| `heat_rate_bins.biomass.default` | 13.5 | 2 | EIA Table 8 — petroleum-fired GT/steam (oil peaker) |  | auto-generated, needs-citation |
| `heat_rate_bins.coal.older` | 10.8 | 2 | EIA Electric Power Annual 2022, Table 8.2 | 2023-10 |  |
| `heat_rate_bins.coal.subcritical` | 10.0 | 2 | EIA Electric Power Annual 2022, Table 8.2 | 2023-10 |  |
| `heat_rate_bins.coal.supercritical` | 8.8 | 2 | EIA Electric Power Annual 2022, Table 8.2 | 2023-10 |  |
| `heat_rate_bins.gas_cc.f_class` | 6.7 | 2 | EIA Electric Power Annual 2022, Table 8.2 | 2023-10 |  |
| `heat_rate_bins.gas_cc.h_class` | 6.3 | 2 | EIA Electric Power Annual 2022, Table 8.2 | 2023-10 |  |
| `heat_rate_bins.gas_cc.older` | 7.5 | 2 | EIA Electric Power Annual 2022, Table 8.2 | 2023-10 |  |
| `heat_rate_bins.gas_ct.aero` | 9.0 | 2 | EIA Electric Power Annual 2022, Table 8.2 | 2023-10 |  |
| `heat_rate_bins.gas_ct.frame` | 10.5 | 2 | EIA Electric Power Annual 2022, Table 8.2 | 2023-10 |  |
| `heat_rate_bins.gas_ct.older` | 11.5 | 2 | EIA Electric Power Annual 2022, Table 8.2 | 2023-10 |  |
| `heat_rate_bins.oil.default` | 13.5 | 2 | EIA Table 8 — petroleum-fired GT/steam (oil peaker) |  | auto-generated, needs-citation |
| `hydrogen_turbine_params.h2_ccgt.heat_rate` | 6.9 | 2 | MMBtu/MWh. GE HA specs, DOE H2 Turbine Program 2023 | 2023 | auto-generated |
| `hydrogen_turbine_params.h2_ccgt.vom` | 3.5 | 2 | $/MWh. NREL ATB 2024 (gas CT analog + H2 premium) | 2024 | auto-generated |
| `hydrogen_turbine_params.h2_ct.heat_rate` | 9.5 | 2 | MMBtu/MWh. GE HA specs, DOE H2 Turbine Program 2023 | 2023 | auto-generated |
| `hydrogen_turbine_params.h2_ct.vom` | 4.0 | 2 | $/MWh. NREL ATB 2024 (gas CT analog + H2 premium) | 2024 | auto-generated |
| `import_tranches.CAISO` | [["PNW_hydro", 3000.0, 15.0], ["DSW_C… | 2 | Priced import/export node, per ISO (playbook §8.2): an interconnect… |  | auto-generated, needs-citation |
| `import_tranches.PJM` | [["import_scarcity_1", 1000.0, 46.0],… | 2 | Priced import/export node, per ISO (playbook §8.2): an interconnect… |  | auto-generated, needs-citation |
| `new_entry_costs.gas_cc_ccs.base_cf` | 0.8 | 2 | Lower than unabated CC (0.85) due to higher MC |  | auto-generated, needs-citation |
| `new_entry_costs.gas_cc_ccs.capex_per_kw` | 2300.0 | 2 | $/kW total plant cost (host CCGT + capture island). |  | auto-generated, needs-citation |
| `new_entry_costs.gas_cc_ccs.fom_per_kw_yr` | 45.0 | 2 | $/kW-yr. Source: NETL Rev 4. |  | auto-generated, needs-citation |
| `new_entry_costs.gas_cc_ccs.learning_rate` | 0.1 | 2 | 10% cost reduction per doubling of cumulative deployment. |  | auto-generated, needs-citation |
| `new_entry_costs.gas_cc_ccs.lifetime_yr` | 30 | 2 | Same as gas CC host plant. |  | auto-generated, needs-citation |
| `new_entry_costs.nuclear_large.base_cf` | 0.92 | 2 | Lower than unabated CC (0.85) due to higher MC |  | auto-generated, needs-citation |
| `new_entry_costs.nuclear_large.fom_per_kw_yr` | 130.0 | 2 | $/kW-yr. Source: NETL Rev 4. |  | auto-generated, needs-citation |
| `new_entry_costs.nuclear_large.lifetime_yr` | 60 | 2 | Same as gas CC host plant. |  | auto-generated, needs-citation |
| `new_entry_costs.nuclear_smr.base_cf` | 0.9 | 2 | Lower than unabated CC (0.85) due to higher MC |  | auto-generated, needs-citation |
| `new_entry_costs.nuclear_smr.fom_per_kw_yr` | 100.0 | 2 | $/kW-yr. Source: NETL Rev 4. |  | auto-generated, needs-citation |
| `new_entry_costs.nuclear_smr.lifetime_yr` | 40 | 2 | Same as gas CC host plant. |  | auto-generated, needs-citation |
| `nuclear_monthly_cf.NEISO` | [1.0, 0.99, 0.95, 0.95, 0.98, 1.0, 1.… | 2 | Nuclear monthly capacity factors (12 values, Jan–Dec) by ISO. Sprin… | 2019 | auto-generated |
| `nuclear_monthly_cf.NYISO` | [1.0, 1.0, 0.95, 0.94, 0.97, 1.0, 1.0… | 2 | Nuclear monthly capacity factors (12 values, Jan–Dec) by ISO. Sprin… | 2019 | auto-generated |
| `nuclear_monthly_cf.PJM` | [1.0, 1.0, 0.95, 0.94, 0.97, 1.0, 1.0… | 2 | Nuclear monthly capacity factors (12 values, Jan–Dec) by ISO. Sprin… | 2019 | auto-generated |
| `nuclear_monthly_cf_by_year.CAISO` | {"2023": [0.96, 1.0, 0.92, 1.0, 1.0, … | 2 | Per-year nuclear monthly capacity factor derived from EIA-923 net g… |  | auto-generated, needs-citation |
| `nuclear_monthly_cf_by_year.ERCOT` | {"2023": [1.0, 1.0, 0.89, 0.75, 0.78,… | 2 | Per-year nuclear monthly capacity factor derived from EIA-923 net g… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.CAISO.nuclear` | 1.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.ERCOT.nuclear` | 2.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.MISO.nuclear` | 1.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.NEISO.nuclear` | 0.5 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.NYISO.nuclear` | 0.5 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.PJM.nuclear` | 1.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.SPP.nuclear` | 0.5 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `scenario.ccs_available_year` | 2030 | 1 | year CCUS enters the candidate pool |  | auto-generated, needs-citation |
| `scenario.ccs_capture_rate` | 0.9 | 2 | fraction of CO2 captured by CCUS |  | auto-generated, needs-citation |
| `scenario.ccs_retrofit_available_year` | 2028 | 2 | Earliest year retrofits can occur. |  | auto-generated, needs-citation |
| `scenario.ccs_retrofit_capex_kw` | 900.0 | 2 | $/kW for post-combustion capture retrofit. |  | auto-generated, needs-citation |
| `scenario.ccs_retrofit_capture_rate` | 0.9 | 2 | Fraction of CO2 captured. 0.90 = 90%. |  | auto-generated, needs-citation |
| `scenario.ccs_retrofit_hr_penalty` | 0.12 | 2 | Fractional heat rate increase from capture parasitic load. |  | auto-generated, needs-citation |
| `scenario.ccs_retrofit_max_gw_per_year` | 3.0 | 2 | GW/yr retrofit throughput cap per ISO. |  | auto-generated, needs-citation |
| `scenario.ccs_retrofit_min_remaining_life` | 15 | 2 | Only retrofit units with ≥ N years remaining useful life. |  | auto-generated, needs-citation |
| `scenario.ccs_retrofit_vom_adder` | 8.0 | 2 | $/MWh additional VOM for capture O&M, solvent, compression. |  | auto-generated, needs-citation |
| `scenario.coal_tranche_1_frac` | 0.3 | 3 | Take-or-pay capacity fraction |  | auto-generated, needs-citation |
| `scenario.coal_tranche_1_fuel_passthrough` | 0.0 | 3 | VOM only — fuel sunk |  | auto-generated, needs-citation |
| `scenario.coal_tranche_2_frac` | 0.25 | 3 | Partially contracted |  | auto-generated, needs-citation |
| `scenario.coal_tranche_2_fuel_passthrough` | 0.35 | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_tranche_3_frac` | 0.45 | 3 | Economic dispatch |  | auto-generated, needs-citation |
| `scenario.coal_tranche_3_fuel_passthrough` | 1.0 | 3 | Full fuel cost |  | auto-generated, needs-citation |
| `scenario.commitment_enabled` | False | 2 | default off — opt-in for calibration. |  | auto-generated, needs-citation |
| `scenario.commitment_irr_hurdle` | 0.07 | 2 | 7% return required on startup cost. |  | auto-generated, needs-citation |
| `scenario.commitment_screen_coal` | True | 2 | When False, CAMPD coal is not |  | auto-generated, needs-citation |
| `scenario.commitment_storage_in_merit_floor` | 0.0 | 2 | 0 disables. When > 0, |  | auto-generated, needs-citation |
| `scenario.commitment_storage_weight` | 1.0 | 2 | 0 disables. The P2 commitment |  | auto-generated, needs-citation |
| `scenario.eac_price_gas_cc_ccs` | 0.0 | 1 | $/MWh, CCS-equipped gas CC only (45Q-linked) |  | auto-generated, needs-citation |
| `scenario.fixed_om_coal` | 40.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `scenario.fixed_om_gas_cc` | 12.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `scenario.fixed_om_gas_ct` | 8.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `scenario.gas_offer_curve` | False | 3 | Tier 3 (calibration) — give the non-ERCOT per-plant gas fleet a ste… |  | auto-generated, needs-citation |
| `scenario.gas_st_startup_spread` | False | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.heat_rate_bin_count` | None | 2 | Override default bin count per fuel type. |  | auto-generated, needs-citation |
| `scenario.ira_ccus_45q_last_year` | 2032 | 2 | §45Q CCUS credit: extended but phasing out post-2032. | 2032 | auto-generated |
| `scenario.offer_curve_by_group` | {} | 2 | Unified thermal offer-curve parameterization (supersedes the legacy… |  | auto-generated, needs-citation |
| `scenario.offer_curve_smoothing_exp` | 1.0 | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.offer_curve_smoothing_mid` | None | 2 | Optional midpoint anchor for the econ ramp shape: the fraction of t… |  | auto-generated, needs-citation |
| `scenario.offer_curve_smoothing_n` | 6 | 2 | N-slice smoothing of the economic offer curve. When offer_curve_smo… |  | auto-generated, needs-citation |
| `scenario.plant_tranche_config_path` | None | 2 | Optional per-plant tranche-config override CSV (one row per plant w… |  | auto-generated, needs-citation |
| `vom.biomass` | 5.0 | 2 | NREL ATB 2024 — biomass (fuel handling raises O&M) | 2024 | auto-generated |
| `vom.coal` | 4.5 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `vom.gas_cc` | 2.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `vom.gas_ct` | 3.5 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `vom.gas_st` | 4.0 | 2 | NREL ATB 2024 — legacy gas steam (higher O&M than CC) | 2024 | auto-generated |
| `vom.hydro` | 1.4 | 2 | NREL ATB 2024 — conventional hydropower | 2024 | auto-generated |
| `vom.nuclear` | 2.5 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `vom.oil` | 4.5 | 2 | NREL ATB 2024 — oil steam/peaker O&M (≈ coal steam) | 2024 | auto-generated |
| `vom.solar` | 0.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `vom.wind` | 0.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `wecc_import_tranches` | [["PNW_hydro", 3000.0, 15.0], ["DSW_C… | 2 | CAISO WECC import supply curve tranches: (name, capacity MW, VOM $/… | 2022 | auto-generated |
| `wright_reference_gw.gas_cc_ccs` | 2.0 | 2 | GW global installed power-sector CCS as of 2024. | 2024 | auto-generated |
| `wright_reference_gw.nuclear` | 445.0 | 2 | was 440. IAEA PRIS 2025. | 2025 | auto-generated |
| `wright_reference_gw.nuclear_large` | 445.0 | 2 | Wright's Law reference cumulative installed capacity (GW global). S… | 2025 | auto-generated |
| `wright_reference_gw.nuclear_smr` | 445.0 | 2 | shares global nuclear fleet |  | auto-generated, needs-citation |

## Transmission

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `import_zone.CAISO` | WECC_import | 2 | Name of each ISO's external import/export zone. CAISO's is baked in… |  | auto-generated, needs-citation |
| `import_zone.PJM` | PJM_external | 2 | Name of each ISO's external import/export zone. CAISO's is baked in… |  | auto-generated, needs-citation |
| `scenario.unknown_zone_default` | South_Central | 2 | zone for bins tagged "Unknown" |  | auto-generated, needs-citation |

## Uncategorized

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `global_annual_deployment_gw.compressed_air` | 0.3 | 2 | GW/yr global CAES additions. Source: IEA 2024 pipeline. | 2024 | auto-generated |
| `global_annual_deployment_gw.flow_battery` | 0.8 | 2 | GW/yr global VRFB additions. Source: BNEF LDES tracker 2024. | 2024 | auto-generated |
| `global_annual_deployment_gw.iron_air` | 1.0 | 2 | was 0.5. |  | auto-generated, needs-citation |
| `global_annual_deployment_gw.li_ion` | 50.0 | 2 | was 30. BNEF 2025. | 2025 | auto-generated |
| `global_annual_deployment_gw.solar` | 400.0 | 2 | was 350. IRENA 2025. | 2025 | auto-generated |
| `global_annual_deployment_gw.wind` | 130.0 | 2 | was 120. IRENA 2025. | 2025 | auto-generated |
| `import_node_links.PJM` | [["PJM_ComEd", 7500.0], ["PJM_AEP_Ohi… | 2 | Links joining an appended external zone to its border zones: (borde… | 2023-24 | auto-generated |
| `inflation_rate` | 0.022 | 2 | Assumed long-run inflation rate for nominal-to-real conversion. Use… |  | auto-generated, needs-citation |
| `mmbtu_per_mwh` | 3.412 | 2 | MMBtu per MWh — thermodynamic identity, used to convert the derived… |  | auto-generated, needs-citation |
| `queue_cap_gw.MISO` | 10 | 2 | Annual interconnection queue caps (GW/yr) by ISO. Source: ERCOT CDR… |  | auto-generated, needs-citation |
| `queue_cap_gw.NEISO` | 4 | 2 | Annual interconnection queue caps (GW/yr) by ISO. Source: ERCOT CDR… |  | auto-generated, needs-citation |
| `queue_cap_gw.NYISO` | 4 | 2 | Annual interconnection queue caps (GW/yr) by ISO. Source: ERCOT CDR… |  | auto-generated, needs-citation |
| `queue_cap_gw.PJM` | 10 | 2 | Annual interconnection queue caps (GW/yr) by ISO. Source: ERCOT CDR… |  | auto-generated, needs-citation |
| `queue_cap_gw.SPP` | 6 | 2 | Annual interconnection queue caps (GW/yr) by ISO. Source: ERCOT CDR… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.CAISO.solar` | 4.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.CAISO.wind` | 3.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.ERCOT.solar` | 5.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.ERCOT.wind` | 5.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.MISO.solar` | 6.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.MISO.wind` | 4.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.NEISO.solar` | 2.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.NEISO.wind` | 1.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.NYISO.solar` | 2.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.NYISO.wind` | 1.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.PJM.solar` | 6.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.PJM.wind` | 1.5 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.SPP.solar` | 3.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.SPP.wind` | 4.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `real_dollar_base_year` | 2026 | 2 | Source: model convention, matches simulation start year |  | auto-generated, needs-citation |
| `renewable_avg_cf.CAISO.solar` | 0.28 | 2 | Annual-average renewable capacity factors (fraction) by ISO and tec… | 2024 | auto-generated |
| `renewable_avg_cf.CAISO.wind` | 0.3 | 2 | Annual-average renewable capacity factors (fraction) by ISO and tec… | 2024 | auto-generated |
| `renewable_avg_cf.ERCOT.solar` | 0.27 | 2 | Annual-average renewable capacity factors (fraction) by ISO and tec… | 2024 | auto-generated |
| `renewable_avg_cf.ERCOT.wind` | 0.35 | 2 | Annual-average renewable capacity factors (fraction) by ISO and tec… | 2024 | auto-generated |
| `renewable_avg_cf.MISO.solar` | 0.22 | 2 | Annual-average renewable capacity factors (fraction) by ISO and tec… | 2024 | auto-generated |
| `renewable_avg_cf.MISO.wind` | 0.34 | 2 | Annual-average renewable capacity factors (fraction) by ISO and tec… | 2024 | auto-generated |
| `renewable_avg_cf.NEISO.solar` | 0.15 | 2 | Annual-average renewable capacity factors (fraction) by ISO and tec… | 2024 | auto-generated |
| `renewable_avg_cf.NEISO.wind` | 0.3 | 2 | Annual-average renewable capacity factors (fraction) by ISO and tec… | 2024 | auto-generated |
| `renewable_avg_cf.NYISO.solar` | 0.15 | 2 | Annual-average renewable capacity factors (fraction) by ISO and tec… | 2024 | auto-generated |
| `renewable_avg_cf.NYISO.wind` | 0.26 | 2 | Annual-average renewable capacity factors (fraction) by ISO and tec… | 2024 | auto-generated |
| `renewable_avg_cf.PJM.solar` | 0.19 | 2 | Annual-average renewable capacity factors (fraction) by ISO and tec… | 2024 | auto-generated |
| `renewable_avg_cf.PJM.wind` | 0.31 | 2 | Annual-average renewable capacity factors (fraction) by ISO and tec… | 2024 | auto-generated |
| `renewable_avg_cf.SPP.solar` | 0.24 | 2 | Annual-average renewable capacity factors (fraction) by ISO and tec… | 2024 | auto-generated |
| `renewable_avg_cf.SPP.wind` | 0.41 | 2 | Annual-average renewable capacity factors (fraction) by ISO and tec… | 2024 | auto-generated |
| `renewable_installed_mw.CAISO.solar` | 22000.0 | 2 | was 25000. Source: EIA Hourly Grid Monitor Oct 2025. | 2025 | auto-generated |
| `renewable_installed_mw.CAISO.wind` | 7000.0 | 2 | was 40000. Source: ERCOT CDR Dec 2024. | 2024 | auto-generated |
| `renewable_installed_mw.ERCOT.solar` | 38000.0 | 2 | was 25000. Source: EIA Hourly Grid Monitor Oct 2025. | 2025 | auto-generated |
| `renewable_installed_mw.ERCOT.wind` | 42000.0 | 2 | was 40000. Source: ERCOT CDR Dec 2024. | 2024 | auto-generated |
| `renewable_installed_mw.MISO.solar` | 7000.0 | 2 | was 25000. Source: EIA Hourly Grid Monitor Oct 2025. | 2025 | auto-generated |
| `renewable_installed_mw.MISO.wind` | 32000.0 | 2 | was 40000. Source: ERCOT CDR Dec 2024. | 2024 | auto-generated |
| `renewable_installed_mw.NEISO.solar` | 2700.0 | 2 | was 25000. Source: EIA Hourly Grid Monitor Oct 2025. | 2025 | auto-generated |
| `renewable_installed_mw.NEISO.wind` | 1400.0 | 2 | was 40000. Source: ERCOT CDR Dec 2024. | 2024 | auto-generated |
| `renewable_installed_mw.NYISO.solar` | 1500.0 | 2 | was 25000. Source: EIA Hourly Grid Monitor Oct 2025. | 2025 | auto-generated |
| `renewable_installed_mw.NYISO.wind` | 2400.0 | 2 | was 40000. Source: ERCOT CDR Dec 2024. | 2024 | auto-generated |
| `renewable_installed_mw.PJM.solar` | 14000.0 | 2 | was 25000. Source: EIA Hourly Grid Monitor Oct 2025. | 2025 | auto-generated |
| `renewable_installed_mw.PJM.wind` | 11000.0 | 2 | was 40000. Source: ERCOT CDR Dec 2024. | 2024 | auto-generated |
| `renewable_installed_mw.SPP.solar` | 600.0 | 2 | was 25000. Source: EIA Hourly Grid Monitor Oct 2025. | 2025 | auto-generated |
| `renewable_installed_mw.SPP.wind` | 34000.0 | 2 | was 40000. Source: ERCOT CDR Dec 2024. | 2024 | auto-generated |
| `wecc_export_cap_mw` | 5000.0 | 2 | CAISO export capability to WECC (MW). Source: placeholder pending E… |  | auto-generated, needs-citation |
| `wright_reference_gw.compressed_air` | 1.5 | 2 | GW global adiabatic/diabatic CAES — Huntorf, McIntosh, |  | auto-generated, needs-citation |
| `wright_reference_gw.flow_battery` | 3.0 | 2 | GW global installed vanadium-redox flow. Source: PNNL 2023, | 2023 | auto-generated |
| `wright_reference_gw.iron_air` | 1.0 | 2 | was 0.5. DOE LDES. |  | auto-generated, needs-citation |
