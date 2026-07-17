# Parameter Citation Registry

_Generated 2026-07-17. Every numeric input to the model traces to a primary source
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


**1382 parameters registered** (768 flagged `needs-citation`).


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
| `tech_cost_multipliers.nuclear_large.high.capex_per_kw` | 1.15 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.nuclear_large.high.learning_rate` | 0.5 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.nuclear_large.low.capex_per_kw` | 0.9 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.nuclear_large.low.learning_rate` | 1.5 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.nuclear_large.mid.capex_per_kw` | 1.0 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.nuclear_large.mid.learning_rate` | 1.0 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.nuclear_smr.high.capex_per_kw` | 1.25 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.nuclear_smr.high.learning_rate` | 0.5 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.nuclear_smr.low.capex_per_kw` | 0.8 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.nuclear_smr.low.learning_rate` | 1.5 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.nuclear_smr.mid.capex_per_kw` | 1.0 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.nuclear_smr.mid.learning_rate` | 1.0 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.solar.high.capex_per_kw` | 1.15 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.solar.high.learning_rate` | 0.6 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.solar.low.capex_per_kw` | 0.65 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.solar.low.learning_rate` | 1.25 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.solar.mid.capex_per_kw` | 1.0 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.solar.mid.learning_rate` | 1.0 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.wind.high.capex_per_kw` | 1.12 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.wind.high.learning_rate` | 0.65 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.wind.low.capex_per_kw` | 0.85 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.wind.low.learning_rate` | 1.35 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.wind.mid.capex_per_kw` | 1.0 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.wind.mid.learning_rate` | 1.0 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |

## Demand

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `adequacy_demand_response_fraction_by_iso.ERCOT` | 0.058 | 2 | Load-side capacity products netted out of gross peak in the ISO's o… | 2025 | auto-generated |
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
| `miso_rpe_demand_value` | 200.0 | 2 | Reserve Procurement Enhancement (RPE): MISO "models a Reserve Procu… | 2024 | auto-generated |
| `scenario.caiso_demand_clock_realign` | False | 2 | Apply the MEASURED source-data |  | auto-generated, needs-citation |
| `scenario.caiso_ra_min_load_frac` | 0.4 | 2 | Minimum stable load of a committed |  | auto-generated, needs-citation |
| `scenario.caiso_supply_consistent_demand` | False | 2 | Replace the CAISO backcast |  | auto-generated, needs-citation |
| `scenario.ct_netload_drag` | False | 3 | CT_PEAKER net-load reliability drag (the simple-cycle analog of the… | 2023 | auto-generated |
| `scenario.datacenter_load_factor` | 0.85 | 2 | Flat hourly CF of the DC block. |  | auto-generated, needs-citation |
| `scenario.datacenter_load_path` | off | 2 | "off" \| "low" \| "mid" \| "high" — |  | auto-generated, needs-citation |
| `scenario.demand_growth_path` | mid | 1 | "low", "mid", "high" — selects from DEMAND_GROWTH_RATES |  | auto-generated, needs-citation |
| `scenario.demand_growth_percentile` | 0.5 | 1 | Continuous counterpart of |  | auto-generated, needs-citation |
| `scenario.demand_growth_rate` | 0.01 | 1 | Market simulator model design decision | 2026-05 | modeled |
| `scenario.ercot_gas_bridge_min_load_frac` | 0.574 | 2 | Minimum stable load of a bridged ERCOT gas-CC as a fraction of the … | 2023 | auto-generated |
| `scenario.ercot_offer_surface_netload_pcts` | [0.8, 0.9, 0.97] | 2 | Net-load percentile bin EDGES separating the loose / mid / tight re… |  | auto-generated, needs-citation |
| `scenario.ercot_west_netload_gas_shape` | False | 3 | Tier 3 (calibration) — STRUCTURAL net-load-indexed West/Panhandle W… |  | auto-generated, needs-citation |
| `scenario.gas_st_netload_drag` | False | 3 | Net-load-indexed ST_GAS reliability-drag floor — the endogenous, we… | 2023 | auto-generated |
| `scenario.neiso_offer_surface_netload_pcts` | [0.8, 0.9, 0.97] | 2 | Net-load percentile bin EDGES (same contract as the ERCOT field abo… |  | auto-generated, needs-citation |
| `scenario.pjm_offer_surface_netload_pcts` | [0.8, 0.9, 0.97] | 2 | Net-load percentile bin EDGES (same contract as the ERCOT/NEISO fie… |  | auto-generated, needs-citation |
| `scenario.strict_demand_profile` | False | 2 | When True, threaded through to |  | auto-generated, needs-citation |

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
| `renewable_capacity_credit.offshore_wind` | 0.3 | 2 | Capacity credit (ELCC) of variable resources for the planning-reser… |  | auto-generated, needs-citation |
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
| `carb_unspecified_import_ef` | 0.428 | 2 | CARB Mandatory GHG Reporting Regulation (MRR), 17 CCR §95111(b) — d… | 2018-12 |  |
| `carbon_program_price_path_escalation_multiplier.high` | 2.0 | 2 | --- Named carbon-program price paths (P-1D: wires the previously-de… |  | auto-generated, needs-citation |
| `carbon_program_price_path_escalation_multiplier.mid` | 1.0 | 2 | --- Named carbon-program price paths (P-1D: wires the previously-de… |  | auto-generated, needs-citation |
| `co2_rate_class_median_percentile` | 50.0 | 2 | Percentile of the per-class (plant_group × fuel) CAMPD rate distrib… |  | auto-generated, needs-citation |
| `co2_rate_conditioning_enabled` | False | 2 | Whether the operation-conditioned refinement ships enabled. Per the… |  | auto-generated, needs-citation |
| `co2_rate_envelope_gate_l1` | 0.5 | 2 | Envelope-gate threshold: the operation-conditioned nearest-neighbor… | 2023 | auto-generated |
| `co2_rate_trailing_window_years` | 2 | 2 | Trailing-window length (years) for the gen-weighted base rate. 0 = … |  | auto-generated, needs-citation |
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
| `rggi_state_co2_budget.CT` | {"2023": 4566218.0, "2024": 4418921.0… | 2 | RGGI CO2 allowance budgets (short tons/yr), regional ("RGGI") and p… | 2027 | auto-generated |
| `rggi_state_co2_budget.DE` | {"2023": 3178264.0, "2024": 3075739.0… | 2 | RGGI CO2 allowance budgets (short tons/yr), regional ("RGGI") and p… | 2027 | auto-generated |
| `rggi_state_co2_budget.MA` | {"2023": 11220454.0, "2024": 10858504… | 2 | RGGI CO2 allowance budgets (short tons/yr), regional ("RGGI") and p… | 2027 | auto-generated |
| `rggi_state_co2_budget.MD` | {"2023": 15772679.0, "2024": 15263882… | 2 | RGGI CO2 allowance budgets (short tons/yr), regional ("RGGI") and p… | 2027 | auto-generated |
| `rggi_state_co2_budget.ME` | {"2023": 2569587.0, "2024": 2487656.0… | 2 | RGGI CO2 allowance budgets (short tons/yr), regional ("RGGI") and p… | 2027 | auto-generated |
| `rggi_state_co2_budget.NH` | {"2023": 3723549.0, "2024": 3604823.0… | 2 | RGGI CO2 allowance budgets (short tons/yr), regional ("RGGI") and p… | 2027 | auto-generated |
| `rggi_state_co2_budget.NJ` | {"2023": 16380000.0, "2024": 15840000… | 2 | RGGI CO2 allowance budgets (short tons/yr), regional ("RGGI") and p… | 2027 | auto-generated |
| `rggi_state_co2_budget.NY` | {"2023": 27295284.0, "2024": 26414791… | 2 | RGGI CO2 allowance budgets (short tons/yr), regional ("RGGI") and p… | 2027 | auto-generated |
| `rggi_state_co2_budget.RGGI` | {"2023": 112457784.0, "2024": 8416278… | 2 | RGGI regional CO2 allowance budget (short tons/yr). Keyed by "RGGI"… | 2023 | auto-generated |
| `rggi_state_co2_budget.RI` | {"2023": 1763884.0, "2024": 1706986.0… | 2 | RGGI CO2 allowance budgets (short tons/yr), regional ("RGGI") and p… | 2027 | auto-generated |
| `rggi_state_co2_budget.VA` | {"2023": 25480000.0} | 2 | RGGI CO2 allowance budgets (short tons/yr), regional ("RGGI") and p… | 2027 | auto-generated |
| `rggi_state_co2_budget.VT` | {"2023": 507865.0, "2024": 491482.0, … | 2 | RGGI CO2 allowance budgets (short tons/yr), regional ("RGGI") and p… | 2027 | auto-generated |
| `scenario.carbon_price_path` | zero | 1 | "zero", "low", "mid", "high"; used when carbon_price is 0.0 |  | auto-generated, needs-citation |
| `scenario.carbon_program_price_path` | None | 1 | named projected forecast path |  | auto-generated, needs-citation |
| `scenario.plant_emission_rates_path` | /home/user/market-simulator/data/raw/… | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.plant_emission_rates_v2_path` | /home/user/market-simulator/data/raw/… | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.so2_price` | 0.0 | 1 | $/ton SO2 |  | auto-generated, needs-citation |
| `scenario.state_carbon_pricing` | True | 1 | Toggle: charge the ISO's state carbon-program allowance cost (CA ca… | 2026-06 |  |
| `scenario.use_plant_emission_rates` | True | 2 | When True, generators pinned to a single plant take that plant's CA… |  | auto-generated, needs-citation |
| `scenario.use_plant_emission_rates_v2` | True | 2 | v2 mode-aware CO2-rate source (docs/handoffs/emissions-co2-rate-pla… | 2026-07 | auto-generated |
| `state_carbon_price_by_iso.CAISO` | {"2023": 33.03, "2024": 35.23, "2025"… | 2 | CARB / CA-Quebec joint auction current-vintage settlement prices, a… | 2025-11 |  |
| `state_carbon_price_by_iso.NEISO` | {"2023": 14.87, "2024": 22.83, "2025"… | 2 | RGGI, Inc. quarterly auction results press releases ("CO2 Allowance… | 2025-12 |  |
| `state_carbon_price_by_iso.NYISO` | {"2023": 13.49, "2024": 20.71, "2025"… | 2 | RGGI quarterly CO2-allowance auction clearing prices, annual simple… | 2025-12 |  |

## Fuel

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `mmbtu_per_bbl_distillate` | 5.825 | 2 | EIA Monthly Energy Review, Appendix A, Table A1 (Approximate Heat C… | 2026-06 |  |
| `mmbtu_per_bbl_residual` | 6.287 | 2 | EIA Monthly Energy Review, Appendix A, Table A1 (Approximate Heat C… | 2026-06 |  |

## Fuel Prices

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `biomass_price_per_mmbtu` | 2.5 | 2 | Delivered biomass fuel price ($/MMBtu) for wood/MSW/landfill-gas un… | 2024 | auto-generated |
| `caiso_ra_mustoffer_gas_mw` | {"2023": 19130.0, "2024": 15566.0, "2… | 2 | CAISO gas-fired MUST-OFFER Resource-Adequacy capacity (MW), by comp… | 2023 | auto-generated |
| `carb_floor_price` | {"2023": 22.21, "2024": 24.04, "2025"… | 2 | CARB Auction Reserve (floor) price by year ($/tonne), rising 5% + C… | 2023 | auto-generated |
| `coal_delivery_commodity_share.bituminous` | 0.85 | 2 | short-haul Interior/Appalachian rail |  | auto-generated, needs-citation |
| `coal_delivery_commodity_share.lignite` | 1.0 | 2 | mine-mouth, no transport |  | auto-generated, needs-citation |
| `coal_delivery_commodity_share.prb` | 0.42 | 2 | 0.42, long-haul rail |  | auto-generated, needs-citation |
| `coal_delivery_commodity_share.subbituminous` | 0.42 | 2 | same basin economics as prb |  | auto-generated, needs-citation |
| `coal_delivery_commodity_share.waste` | 1.0 | 2 | reclamation fuel, near-mine |  | auto-generated, needs-citation |
| `coal_heat_content_mmbtu_per_ton.ANT` | 25.09 | 2 | anthracite (not in any modeled fleet; completeness) |  | auto-generated, needs-citation |
| `coal_heat_content_mmbtu_per_ton.BIT` | 24.93 | 2 | bituminous |  | auto-generated, needs-citation |
| `coal_heat_content_mmbtu_per_ton.LIG` | 13.3 | 2 | lignite |  | auto-generated, needs-citation |
| `coal_heat_content_mmbtu_per_ton.SUB` | 17.46 | 2 | subbituminous (PRB) |  | auto-generated, needs-citation |
| `coal_max_cf_by_plant` | {"298": 0.95, "6179": 0.99, "7097": 0… | 2 | Per-plant ERCOT coal sustained-output ceilings (fraction of capacit… | 2023 | auto-generated |
| `coal_price_base.CAISO` | 2.5 | 2 | EIA AEO 2024 — delivered coal price | 2024 | auto-generated |
| `coal_price_base.ERCOT` | 2.0 | 2 | EIA AEO 2024 — delivered coal price | 2024 | auto-generated |
| `coal_price_base.MISO` | 1.9 | 2 | MISO's coal fleet burns a Powder River Basin sub-bituminous |  | auto-generated, needs-citation |
| `coal_price_base.NEISO` | 3.0 | 2 | Tier-3 placeholder: PJM bituminous blend (EIA AEO 2024, 2.3) plus a… | 2026-06 | modeled, needs-citation |
| `coal_price_base.NYISO` | 2.3 | 2 | NY grid coal fleet retired (Somerset/Cayuga, 2020); no 2023+ unit p… | 2024 |  |
| `coal_price_base.PJM` | 2.3 | 2 | Central/Northern Appalachian bituminous + PRB-by-rail |  | auto-generated, needs-citation |
| `coal_price_escalation` | 0.01 | 2 | Annual real escalation rate for coal prices. Reflects mine closures… | 2024 | auto-generated |
| `coal_price_trajectories.high` | {"2024": 2.4888, "2025": 2.4729, "202… | 2 | --- National delivered coal-price trajectories (real 2024$/MMBtu) -… | 2024 | auto-generated |
| `coal_price_trajectories.low` | {"2024": 2.4892, "2025": 2.4487, "202… | 2 | --- National delivered coal-price trajectories (real 2024$/MMBtu) -… | 2024 | auto-generated |
| `coal_price_trajectories.mid` | {"2024": 2.4894, "2025": 2.4296, "202… | 2 | --- National delivered coal-price trajectories (real 2024$/MMBtu) -… | 2024 | auto-generated |
| `coal_sigmoid_backcast_gas_min_mmbtu.CAISO` | 3.4 | 2 | Minimum delivered gas price ($/MMBtu) observed over the backcast wi… | 2023 | auto-generated |
| `coal_sigmoid_backcast_gas_min_mmbtu.ERCOT` | 2.0 | 2 | Minimum delivered gas price ($/MMBtu) observed over the backcast wi… | 2023 | auto-generated |
| `coal_sigmoid_backcast_gas_min_mmbtu.MISO` | 2.19 | 2 | Minimum delivered gas price ($/MMBtu) observed over the backcast wi… | 2023 | auto-generated |
| `coal_sigmoid_backcast_gas_min_mmbtu.NEISO` | 3.29 | 2 | Minimum delivered gas price ($/MMBtu) observed over the backcast wi… | 2023 | auto-generated |
| `coal_sigmoid_backcast_gas_min_mmbtu.NYISO` | 2.74 | 2 | Minimum delivered gas price ($/MMBtu) observed over the backcast wi… | 2023 | auto-generated |
| `coal_sigmoid_backcast_gas_min_mmbtu.PJM` | 2.86 | 2 | +0.67 EIA-923 delivered basis (GAS_BASIS_DIFFERENTIAL) |  | auto-generated, needs-citation |
| `coal_sigmoid_baseline_slope` | 2.5 | 2 | Baseline logistic slope (per $/MMBtu) for a coal supply group whose… |  | auto-generated, needs-citation |
| `coal_sigmoid_floor_min` | 0.5 | 2 | Lowest the sigmoid floor may go: a coal plant never bids below this… |  | auto-generated, needs-citation |
| `coal_sigmoid_follower_discount` | 0.87 | 2 | Follower-tier (low-must-run PRB cyclers, mustrun <= coal_prb_follow… |  | auto-generated, needs-citation |
| `coal_sigmoid_rep_hr_coal` | 10.0 | 2 | HEAT_RATE_BINS["coal"]["subcritical"] |  | auto-generated, needs-citation |
| `coal_sigmoid_rep_hr_gas_cc` | 6.7 | 2 | HEAT_RATE_BINS["gas_cc"]["f_class"] |  | auto-generated, needs-citation |
| `coal_sigmoid_slope_max` | 4.0 | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `coal_sigmoid_slope_min` | 1.0 | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
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
| `ercot_as_revenue_per_kw_yr.gas_cc` | 8.0 | 2 | ERCOT ancillary-service market revenue ($/kW-yr) credited in the ca… | 2023 | auto-generated |
| `ercot_as_revenue_per_kw_yr.gas_ct` | 22.0 | 2 | ERCOT ancillary-service market revenue ($/kW-yr) credited in the ca… | 2023 | auto-generated |
| `ercot_as_revenue_per_kw_yr.gas_st` | 15.0 | 2 | ERCOT ancillary-service market revenue ($/kW-yr) credited in the ca… | 2023 | auto-generated |
| `ercot_online_cap_share.COAL` | [[0.9525, 0.9717, 0.9717, 0.9717, 0.9… | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_online_cap_share.ST_GAS` | [[0.0228, 0.0228, 0.0228, 0.1153, 0.1… | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_online_cap_share_extreme.COAL` | [[0.9525, 0.9717, 0.9717, 0.9717, 0.9… | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_online_cap_share_extreme.ST_GAS` | [[0.0228, 0.0228, 0.0228, 0.1153, 0.1… | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_online_cap_share_measured.COAL` | [[0.9525, 0.9717, 0.9717, 0.9717, 0.9… | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_online_cap_share_measured.ST_GAS` | [[0.0228, 0.0228, 0.0228, 0.1153, 0.1… | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_rtolcap_fwd_online_share.COAL` | [[0.611, 0.5678, 0.5251, 0.4928, 0.44… | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `ercot_rtolcap_fwd_online_share.ST_GAS` | [[0.0211, 0.0211, 0.0211, 0.0724, 0.1… | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `gas_basis_differential.CAISO` | 1.2 | 2 | EIA Natural Gas Weekly Update | 2024 |  |
| `gas_basis_differential.ERCOT` | -0.5 | 2 | EIA Natural Gas Weekly Update | 2024 |  |
| `gas_basis_differential.MISO` | 0.3 | 2 | Chicago Citygate footprint blend to Henry Hub. EIA Illinois natural… | 2024 |  |
| `gas_basis_differential.NEISO` | 1.1 | 2 | EIA-923 Schedule 5 fuel receipts: quantity-weighted delivered gas t… | 2026-06 |  |
| `gas_basis_differential.NYISO` | 0.55 | 2 | EIA-923 delivered-gas basis (see below) |  | auto-generated, needs-citation |
| `gas_basis_differential.PJM` | 0.67 | 2 | TETCO M3 / Transco Z6 / Dominion South blend; Tier 3 — verify |  | auto-generated, needs-citation |
| `gas_monthly_seasonality` | {"1": 1.15, "2": 1.1, "3": 1.02, "4":… | 2 | EIA Henry Hub monthly spot prices | 2024 |  |
| `gas_st_econ_hr_override_default` | 1.0 | 2 | gas-steam econ ≈ flat full-load HR |  | auto-generated, needs-citation |
| `gas_st_peak_hr_override_default` | 1.5 | 2 | gas-steam peak ≈ 1.5× base HR |  | auto-generated, needs-citation |
| `global_annual_deployment_gw.gas_cc` | 20.0 | 2 | was 25. IEA WEO 2025. | 2025 | auto-generated |
| `henry_hub_trajectories.high` | {"2023": 2.54, "2024": 2.19, "2025": … | 1 | EIA Annual Energy Outlook 2025 | 2025-04 | modeled |
| `henry_hub_trajectories.hindcast_asknown_aeo2021` | {"2021": 3.07, "2023": 2.86, "2024": … | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `henry_hub_trajectories.hindcast_realized` | {"2021": 3.91, "2023": 2.54, "2024": … | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `henry_hub_trajectories.low` | {"2023": 2.54, "2024": 2.19, "2025": … | 1 | EIA Annual Energy Outlook 2025 | 2025-04 | modeled |
| `henry_hub_trajectories.mid` | {"2023": 2.54, "2024": 2.19, "2025": … | 1 | EIA Annual Energy Outlook 2025 | 2025-04 | modeled |
| `lignite_price_2023_25` | 1.45 | 2 | --- ERCOT lignite / PRB delivered coal cost, 2023-2025 ------------… | 2023 | auto-generated |
| `maintenance_monthly_shape.COAL` | [0.239, 1.125, 1.757, 1.923, 1.559, 0… | 2 | Forecast-mode monthly planned-maintenance shape (12 weights, Jan..D… | 2023 | auto-generated |
| `maintenance_monthly_shape.ST_GAS` | [1.136, 1.553, 1.567, 1.346, 1.14, 0.… | 2 | Forecast-mode monthly planned-maintenance shape (12 weights, Jan..D… | 2023 | auto-generated |
| `min_stable_pct_physical.COAL` | 0.4 | 2 | subcritical/supercritical steam — WWSIS-2 40% |  | auto-generated, needs-citation |
| `min_stable_pct_physical.ST_GAS` | 0.12 | 2 | gas steam — WWSIS-2 12% (older subcritical sits high end) |  | auto-generated, needs-citation |
| `miso_rdt_tcdc_step1_price` | 40.0 | 2 | RDT Transmission Constraint Demand Curve (TCDC): MISO prices RDT vi… | 2024 | auto-generated |
| `miso_rdt_tcdc_step2_price` | 500.0 | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `new_entry_costs.gas_ct.base_cf` | 0.12 | 2 | Lower than unabated CC (0.85) due to higher MC |  | auto-generated, needs-citation |
| `new_entry_costs.gas_ct.capex_per_kw` | 1250.0 | 2 | $/kW total plant cost (host CCGT + capture island). |  | auto-generated, needs-citation |
| `new_entry_costs.gas_ct.fom_per_kw_yr` | 21.0 | 2 | $/kW-yr. Source: NETL Rev 4. |  | auto-generated, needs-citation |
| `new_entry_costs.gas_ct.learning_rate` | 0.02 | 2 | 10% cost reduction per doubling of cumulative deployment. |  | auto-generated, needs-citation |
| `new_entry_costs.gas_ct.lifetime_yr` | 30 | 2 | Same as gas CC host plant. |  | auto-generated, needs-citation |
| `nuclear_fuel_price_historical` | {"2006": 0.5608, "2007": 0.6831, "200… | 2 | --- Nuclear fuel price ($/MMBtu, real 2024$) --- D2 fix (P-1D, CLAU… | 2024 | auto-generated |
| `oil_price_per_mmbtu` | 18.0 | 2 | Delivered oil fuel price ($/MMBtu) for oil-fired peakers and steam … | 2023 | auto-generated |
| `oil_price_trajectories.high` | {"2024": 21.67, "2025": 22.3, "2026":… | 2 | --- Forecast-year oil-price trajectories (real 2024$/MMBtu) --- AEO… | 2024 | auto-generated |
| `oil_price_trajectories.low` | {"2024": 21.67, "2025": 20.49, "2026"… | 2 | --- Forecast-year oil-price trajectories (real 2024$/MMBtu) --- AEO… | 2024 | auto-generated |
| `oil_price_trajectories.mid` | {"2024": 21.67, "2025": 19.07, "2026"… | 2 | --- Forecast-year oil-price trajectories (real 2024$/MMBtu) --- AEO… | 2024 | auto-generated |
| `prb_price_by_year` | {"2023": 2.15, "2024": 2.0, "2025": 2.0} | 2 | PRB-by-rail: measured delivered cost, 2023-2025 (EIA-923 Schedule-5… | 2023 | auto-generated |
| `queue_cap_per_tech_gw.CAISO.gas_cc` | 2.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.CAISO.gas_ct` | 1.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.ERCOT.gas_cc` | 3.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.ERCOT.gas_ct` | 3.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.MISO.gas_cc` | 3.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.MISO.gas_ct` | 2.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.NEISO.gas_cc` | 1.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.NEISO.gas_ct` | 0.5 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.NYISO.gas_cc` | 1.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.NYISO.gas_ct` | 0.5 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.PJM.gas_cc` | 4.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.PJM.gas_ct` | 2.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `scenario.caiso_gas_floor_frac` | 1.0 | 3 | Fraction of the measured EIA-930 NG: NG |  | auto-generated, needs-citation |
| `scenario.caiso_import_gas_coupling` | False | 2 | Shift the gas-set CAISO import |  | auto-generated, needs-citation |
| `scenario.caiso_import_hub_prices` | False | 2 | Price the CAISO priced-import node's |  | auto-generated, needs-citation |
| `scenario.caiso_intertie_reference_price` | False | 1 | Price each CAISO per-hub WECC |  | auto-generated, needs-citation |
| `scenario.caiso_reference_price_seam` | False | 1 | Price BOTH legs of CAISO's two WECC |  | auto-generated, needs-citation |
| `scenario.caiso_zonal_gas_basis` | False | 2 | CAISO per-zone citygate-hub gas basis spread. CAISO's zones buy fro… | 2023 | auto-generated |
| `scenario.class_aware_fuel_price_fallback` | False | 3 | Tier 3 (calibration) — class-aware "nearby plant" donor pools. When… | 2024 | auto-generated |
| `scenario.coal_bit_committed_takeorpay` | False | 3 | Bituminous committed-band take-or-pay bid discount. The `_committed… | 2023 | auto-generated |
| `scenario.coal_bit_dispatchable` | False | 2 | Bituminous spot-coal marginal treatment (PJM): unlike PRB/lignite m… |  | auto-generated, needs-citation |
| `scenario.coal_bit_passthrough_ceil` | None | 3 | dear-gas asymptote (>1 = markup) |  | auto-generated, needs-citation |
| `scenario.coal_bit_passthrough_floor` | None | 3 | cheap-gas asymptote |  | auto-generated, needs-citation |
| `scenario.coal_bit_passthrough_gas_mid` | None | 3 | $/MMBtu logistic midpoint |  | auto-generated, needs-citation |
| `scenario.coal_bit_passthrough_gas_slope` | None | 3 | logistic slope per $/MMBtu |  | auto-generated, needs-citation |
| `scenario.coal_bit_passthrough_sigmoid` | False | 3 | Tier 3 (calibration) — gas-keyed BITUMINOUS passthrough sigmoid (PJ… | 2023 | auto-generated |
| `scenario.coal_committed_hr_mult` | 1.22 | 3 | Coal part-load penalty ~22% |  | auto-generated, needs-citation |
| `scenario.coal_committed_takeorpay_all` | False | 3 | Same grounded committed-band take-or-pay discount as ``coal_bit_com… |  | auto-generated, needs-citation |
| `scenario.coal_committed_takeorpay_regulated` | False | 3 | Regulated-utility-scoped committed-band take-or-pay discount: the s… | 2026-07 | auto-generated |
| `scenario.coal_drop_pof` | False | 3 | When True, drop the statistical planned-outage (POF) derate on coal… |  | auto-generated, needs-citation |
| `scenario.coal_econ_hr_mult` | 0.97 | 3 | Coal incremental HR |  | auto-generated, needs-citation |
| `scenario.coal_econ_srmc_bound` | False | 3 | Marginal-coal measured-SRMC offer bound. The gas-keyed passthrough … | 2026-07 | auto-generated |
| `scenario.coal_lignite_mustrun_override` | None | 3 | Tier 3 (calibration) — CAMPD coal must-run overrides. When set, rep… |  | auto-generated, needs-citation |
| `scenario.coal_lignite_passthrough_ceil` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_lignite_passthrough_floor` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_lignite_passthrough_gas_mid` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_lignite_passthrough_gas_slope` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_lignite_passthrough_sigmoid` | False | 3 | Lignite (mine-mouth; full cost / no sigmoid everywhere today — the … |  | auto-generated, needs-citation |
| `scenario.coal_mustrun_online_pmin` | False | 2 | Online-Pmin coal must-run floor (rebuild step 2): size the coal mus… | 2026-06 | auto-generated |
| `scenario.coal_mustrun_per_plant` | False | 3 | When True, coal must-run % comes from the per-plant CAMPD-derived t… |  | auto-generated, needs-citation |
| `scenario.coal_nameplate_summer_derate` | False | 2 | COAL net-summer capacity derate (coal_nameplate_summer_derate, off … | 2026-07 | auto-generated |
| `scenario.coal_peak_hr_penalty` | 1.08 | 3 | Coal peaking increment |  | auto-generated, needs-citation |
| `scenario.coal_plant_monthly_pricing` | True | 3 | When True (default), coal generators that report EIA-923 monthly fu… |  | auto-generated, needs-citation |
| `scenario.coal_prb_contract_passthrough` | 1.0 | 3 | Tier 3 (calibration) — CAMPD coal pricing. Plant-specific coal deli… |  | auto-generated, needs-citation |
| `scenario.coal_prb_follower_ceil` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_prb_follower_floor` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_prb_follower_gas_mid` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_prb_follower_gas_slope` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_prb_follower_mustrun_max` | 25.0 | 3 | MR% <= this -> follower tier |  | auto-generated, needs-citation |
| `scenario.coal_prb_mustrun_override` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_prb_passthrough` | 1.0 | 3 | Tier 3 (calibration) — CAMPD coal committed-tranche price-taking. A… |  | auto-generated, needs-citation |
| `scenario.coal_prb_passthrough_ceil` | None | 3 | dear-gas asymptote (>1 = markup) |  | auto-generated, needs-citation |
| `scenario.coal_prb_passthrough_floor` | None | 3 | cheap-gas asymptote |  | auto-generated, needs-citation |
| `scenario.coal_prb_passthrough_gas_mid` | None | 3 | $/MMBtu logistic midpoint |  | auto-generated, needs-citation |
| `scenario.coal_prb_passthrough_gas_slope` | None | 3 | logistic slope per $/MMBtu |  | auto-generated, needs-citation |
| `scenario.coal_prb_passthrough_sigmoid` | False | 3 | Tier 3 (calibration) — gas-keyed PRB passthrough sigmoid. When True… | 2023 | auto-generated |
| `scenario.coal_prb_passthrough_tiered` | False | 3 | Tier 3 (calibration) — tiered PRB passthrough. When True, PRB plant… |  | auto-generated, needs-citation |
| `scenario.coal_price_path` | mid | 1 | "low", "mid", "high" — AEO2025 national |  | auto-generated, needs-citation |
| `scenario.coal_sub_passthrough_ceil` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_sub_passthrough_floor` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_sub_passthrough_gas_mid` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_sub_passthrough_gas_slope` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_sub_passthrough_sigmoid` | False | 3 | Subbituminous: the derived EIA-923 rank tag. Historically aliased o… |  | auto-generated, needs-citation |
| `scenario.coal_subbit_passthrough_ceil` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_subbit_passthrough_floor` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_subbit_passthrough_gas_mid` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_subbit_passthrough_gas_slope` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_subbit_passthrough_sigmoid` | False | 3 | Subbituminous (derived EIA-923 rank tag; e.g. PJM's two PRB-by-rail… |  | auto-generated, needs-citation |
| `scenario.coal_supply_repricing` | True | 3 | When True (default), coal generators are repriced to the flat annua… |  | auto-generated, needs-citation |
| `scenario.coal_takeorpay_from_data` | False | 2 | Take-or-pay from data (all coal ranks): replace the hardcoded "must… |  | auto-generated, needs-citation |
| `scenario.coal_warm_committed` | False | 2 | Warm-boiler coal committed band: a CAMPD coal bin with a per-plant … |  | auto-generated, needs-citation |
| `scenario.coal_waste_passthrough_ceil` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_waste_passthrough_floor` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_waste_passthrough_gas_mid` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_waste_passthrough_gas_slope` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.coal_waste_passthrough_sigmoid` | False | 3 | Waste coal (culm/gob/mine-refuse, the PJM COAL_WC class): the fuel … |  | auto-generated, needs-citation |
| `scenario.dual_fuel_oil_reattribution` | False | 3 | Tier 3 (calibration) — re-attribute dual-fuel switched generation t… |  | auto-generated, needs-citation |
| `scenario.dual_fuel_switching` | False | 3 | Tier 3 (calibration) — dual-fuel switching (doc 03 Pack G). Gas uni… |  | auto-generated, needs-citation |
| `scenario.eac_price_geothermal` | 0.0 | 1 | $/MWh, clean firm generation credit |  | auto-generated, needs-citation |
| `scenario.eac_price_nuclear` | 0.0 | 1 | $/MWh, e.g. NY/IL Zero Emission Credit ~$17 |  | auto-generated, needs-citation |
| `scenario.eac_price_offshore_wind` | 0.0 | 1 | $/MWh, offshore-specific EAC (may differ from onshore) |  | auto-generated, needs-citation |
| `scenario.eac_price_solar` | 0.0 | 1 | $/MWh |  | auto-generated, needs-citation |
| `scenario.eac_price_wind` | 0.0 | 1 | $/MWh, onshore wind REC |  | auto-generated, needs-citation |
| `scenario.entry_lookahead_reprice` | False | 1 | GATED, default-OFF growth-scaled |  | auto-generated, needs-citation |
| `scenario.entry_price_signal_alpha` | 1.0 | 2 | EWMA blend of the price signal the |  | auto-generated, needs-citation |
| `scenario.ercot_gas_bridge_da_horizon` | True | 1 | Cap economic bridges at one DA operating day (constants.DA_COMMITME… |  | auto-generated, needs-citation |
| `scenario.ercot_gas_contract_haircut` | False | 3 | Tier 3 (calibration) — MEASURED re-grounding of the West/Waha floor… |  | auto-generated, needs-citation |
| `scenario.ercot_gas_delivered_floor_basis` | None | 3 | Tier 3 (calibration) — delivered-gas floor on the ERCOT zonal basis… | 2024 | auto-generated |
| `scenario.ercot_offer_surface_price_cap_frac` | 0.95 | 2 | Safety cap on the repriced peak offer as a fraction of VOLL, so a m… |  | auto-generated, needs-citation |
| `scenario.ercot_west_gas_collapse_freq` | None | 3 | Optional override of the measured Waha negative-price-day frequency… | 2024 | auto-generated |
| `scenario.ercot_west_gas_delivered_floor` | None | 3 | Burner-tip delivered floor ($/MMBtu) for the COLLAPSE regime of the… |  | auto-generated, needs-citation |
| `scenario.ercot_west_gas_endogenous_collapse` | False | 3 | Make the two-regime split frequency ENDOGENOUS (the forward analogu… |  | auto-generated, needs-citation |
| `scenario.ercot_west_gas_firm_basis` | None | 3 | The high-net-load asymptote of the net-load-indexed West basis abov… |  | auto-generated, needs-citation |
| `scenario.ercot_zonal_gas_basis` | False | 3 | Tier 3 (calibration) — ERCOT per-zone gas-hub basis. ERCOT's model … | 2024 | auto-generated |
| `scenario.fixed_om_gas_st` | 35.0 | 2 | legacy gas steam (boiler/ST) going-forward fixed |  | auto-generated, needs-citation |
| `scenario.gas_daily_shape` | False | 2 | Inject the measured Henry Hub *daily* within-month shape onto the g… |  | auto-generated, needs-citation |
| `scenario.gas_hh_monthly_shape` | False | 3 | Tier 3 (calibration) — replace the generic climatological monthly g… | 2024 | auto-generated |
| `scenario.gas_hub_basis_daily` | False | 3 | Tier 3 (calibration) — daily resolution for the hub-basis overlay a… |  | auto-generated, needs-citation |
| `scenario.gas_hub_basis_overlay` | False | 3 | Market simulator model design decision (doc-08 NEISO design decisio… | 2026-06 | modeled |
| `scenario.gas_monthly_actuals` | False | 3 | Tier 3 (calibration) — price gas at the ISO's measured EIA-923 mont… | 2024 | auto-generated |
| `scenario.gas_plant_monthly_fuel_pricing` | False | 2 | Per-plant monthly gas pricing. OFF by default: every gas generator … |  | auto-generated, needs-citation |
| `scenario.gas_price_factor` | 1.0 | 1 | Forecast-only multiplicative shock applied |  | auto-generated, needs-citation |
| `scenario.gas_price_override` | None | 3 | When set, pins the annual |  | auto-generated, needs-citation |
| `scenario.gas_price_path` | mid | 1 | Market simulator model design decision | 2026-05 |  |
| `scenario.gas_seasonality` | True | 2 | Market simulator model design decision | 2026-05 |  |
| `scenario.gas_st_committed_hr_mult` | 1.32 | 3 | Gas steam part-load penalty ~32% |  | auto-generated, needs-citation |
| `scenario.gas_st_committed_hr_override` | None | 3 | Reliability gas-steam (ST_GAS) tranche heat-rate OVERRIDES (relativ… |  | auto-generated, needs-citation |
| `scenario.gas_st_drag_cap` | 0.34 | 3 | max observed overnight floor fraction (~50 GW) |  | auto-generated, needs-citation |
| `scenario.gas_st_drag_intercept` | -0.1376 | 3 | floor zero-crossing ~15.2 GW |  | auto-generated, needs-citation |
| `scenario.gas_st_drag_slope_per_gw` | 0.00906 | 3 | overnight CF per GW net-load |  | auto-generated, needs-citation |
| `scenario.gas_st_econ_hr_mult` | 0.97 | 3 | Gas steam incremental HR |  | auto-generated, needs-citation |
| `scenario.gas_st_econ_hr_override` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.gas_st_offsummer_mustrun` | 0.0 | 3 | Off-summer (Oct-Apr) ST_GAS reliability min-gen floor, as a fractio… |  | auto-generated, needs-citation |
| `scenario.gas_st_peak_hr_override` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.gas_st_summer_mustrun` | 0.0 | 3 | Legacy gas-steam (ST_GAS) summer reliability treatment. When gas_st… |  | auto-generated, needs-citation |
| `scenario.hindcast_fuel_variant` | realized | 2 | "realized" \| "asknown" |  | auto-generated, needs-citation |
| `scenario.miso_cc_coal_rebalance` | False | 1 | MISO CC_REGULAR / COAL_BIT offer-curve |  | auto-generated, needs-citation |
| `scenario.miso_zonal_gas_basis` | False | 3 | MISO per-zone delivered-gas basis spread. MISO's three zones sit on… |  | auto-generated, needs-citation |
| `scenario.nearby_fuel_price_fallback` | False | 3 | Tier 3 (calibration) — "nearby plant" fuel-cost fallback. When True… |  | auto-generated, needs-citation |
| `scenario.nearby_fuel_price_min_state_plants` | 2 | 3 | state-mean sample floor; |  | auto-generated, needs-citation |
| `scenario.neiso_gas_coldsnap_derate` | False | 1 | NEISO winter gas-fired availability |  | auto-generated, needs-citation |
| `scenario.neiso_gas_derate_cap` | 0.2 | 2 | Max incremental gas-fired forced-out |  | auto-generated, needs-citation |
| `scenario.neiso_gas_derate_slope_per_c` | 0.018 | 3 | Incremental gas forced-out |  | auto-generated, needs-citation |
| `scenario.neiso_gas_derate_t0_c` | -7.0 | 1 | Cold-limb zero-crossing (~20 degF): above |  | auto-generated, needs-citation |
| `scenario.neiso_offer_surface_price_cap_frac` | 0.95 | 2 | Safety cap on the repriced offer as a fraction of VOLL (the measure… |  | auto-generated, needs-citation |
| `scenario.neiso_winter_fuel_inventory` | False | 1 | NEISO winter (Nov-Mar) oil-burn |  | auto-generated, needs-citation |
| `scenario.neiso_winter_fuel_mustrun` | False | 2 | NEISO winter fuel-security |  | auto-generated, needs-citation |
| `scenario.neiso_winter_fuel_start_fill_bbl` | None | 1 | Start-of-winter |  | auto-generated, needs-citation |
| `scenario.neiso_winter_fuelsec_commit_frac` | 1.0 | 2 | Fraction of each fuel-secure |  | auto-generated, needs-citation |
| `scenario.neiso_winter_fuelsec_min_stable_pct` | 0.4 | 2 | Physical minimum-stable |  | auto-generated, needs-citation |
| `scenario.neiso_winter_fuelsec_tmin_c` | -7.0 | 2 | Cold-day gate on zone daily TMIN |  | auto-generated, needs-citation |
| `scenario.nuclear_fuel_price_override` | None | 1 | $/MMBtu. When set, |  | auto-generated, needs-citation |
| `scenario.nyiso_downstate_ct_gas_basis` | False | 3 | ---- NYISO downstate-peaker structural pricing (2026-07, issue #134… | 2026-07 | auto-generated |
| `scenario.nyiso_downstate_ct_gas_daily` | False | 3 | Tier 3 (calibration) — DAILY re-grounding of the same downstate CT-… | 2024 | auto-generated |
| `scenario.nyiso_import_hub_prices` | False | 1 | NYISO priced import-node tranches |  | auto-generated, needs-citation |
| `scenario.nyiso_zonal_gas_basis` | False | 3 | Tier 3 (calibration) — NYISO per-zone gas-hub basis. NYISO's region… |  | auto-generated, needs-citation |
| `scenario.oil_price_path` | mid | 1 | "low", "mid", "high" — AEO2025 |  | auto-generated, needs-citation |
| `scenario.oil_primary_bin_fuel` | False | 3 | Tier 3 (calibration) — MEASURED per-unit fuel correction. A handful… |  | auto-generated, needs-citation |
| `scenario.pjm_offer_surface_price_cap_frac` | 0.95 | 2 | Safety cap on the repriced offer as a fraction of VOLL (the measure… |  | auto-generated, needs-citation |
| `scenario.pjm_zonal_gas_basis` | False | 3 | Tier 3 (calibration) — PJM per-zone gas basis. PJM is priced off a … |  | auto-generated, needs-citation |
| `scenario.reference_price_interface` | False | 1 | Priced-interchange node: serve the |  | auto-generated, needs-citation |
| `scenario.scarcity_price_overlay` | False | 2 | ISO eligibility gate for the |  | auto-generated, needs-citation |
| `scenario.st_gas_intermediate_cf_threshold` | 50.0 | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.st_gas_intermediate_split` | False | 1 | ST_GAS analogue of ct_intermediate_split. MISO's legacy gas-steam f… |  | auto-generated, needs-citation |
| `scenario.st_gas_mustrun_p25_level` | False | 2 | LEVEL SWAP for the st_gas_mustrun_per_plant floor (miso-67). When T… | 2026-07 | auto-generated |
| `scenario.st_gas_mustrun_per_plant` | False | 2 | The ST_GAS leg of the same per-plant local-reliability commitment f… | 2023 | auto-generated |
| `scenario.temp_derate_ref_c_coal` | 25.0 | 2 | coal condenser-derate onset (~77 F) |  | auto-generated, needs-citation |
| `scenario.temp_derate_slope_coal` | 0.004 | 2 | coal fractional loss per C above ref |  | auto-generated, needs-citation |
| `scenario.temp_derate_slope_st_gas` | 0.0054 | 2 | gas-steam fractional loss per C |  | auto-generated, needs-citation |
| `tech_cost_multipliers.gas_cc.high.capex_per_kw` | 1.08 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.gas_cc.high.learning_rate` | 0.5 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.gas_cc.low.capex_per_kw` | 0.95 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.gas_cc.low.learning_rate` | 1.5 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.gas_cc.mid.capex_per_kw` | 1.0 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.gas_cc.mid.learning_rate` | 1.0 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.gas_ct.high.capex_per_kw` | 1.08 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.gas_ct.high.learning_rate` | 0.5 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.gas_ct.low.capex_per_kw` | 0.95 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.gas_ct.low.learning_rate` | 1.5 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.gas_ct.mid.capex_per_kw` | 1.0 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.gas_ct.mid.learning_rate` | 1.0 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `wright_reference_gw.gas_cc` | 1220.0 | 2 | was 1200. IEA WEO 2025. | 2025 | auto-generated |

## Hydro

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `hydro_envelope_percentile` | 95.0 | 2 | --- Hydro hourly deliverability envelope (caiso-72 STEP-2) --------… |  | auto-generated, needs-citation |
| `hydro_year_multiplier.dry` | 0.85 | 2 | Hydro-year scenario lever: a multiplier on the normal-water-year hy… | 2021 | auto-generated |
| `hydro_year_multiplier.normal` | 1.0 | 2 | Hydro-year scenario lever: a multiplier on the normal-water-year hy… | 2021 | auto-generated |
| `hydro_year_multiplier.wet` | 1.15 | 2 | Hydro-year scenario lever: a multiplier on the normal-water-year hy… | 2021 | auto-generated |
| `nyiso_firm_import_floor_frac.HQ_hydro` | 1.0 | 2 | NYISO firm (must-flow) import baseload (transmission.inject_nyiso_f… | 2023 | auto-generated |
| `nyiso_hydro_treaty_min_flow` | {"2693": 0.25, "2694": 0.5} | 2 | NYISO treaty-mandated minimum flows for the two large NYPA hydro pl… | 1957 | auto-generated |
| `renewable_capacity_credit.hydro` | 0.5 | 2 | Capacity credit (ELCC) of variable resources for the planning-reser… |  | auto-generated, needs-citation |
| `scenario.hydro_dispatch_envelope` | False | 2 | GATED default off (caiso-72 |  | auto-generated, needs-citation |
| `scenario.hydro_year` | normal | 1 | "dry" \| "normal" \| "wet" — forecast wet/dry |  | auto-generated, needs-citation |

## Market Design

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `ercot_ecrs_release_reform_hour` | 5088 | 1 | 212 days (Jan-Jul) x 24 h = 5088 — 2024-08-01 00:00 on the model's … | 2024-08-01 |  |
| `ercot_ecrs_release_reform_year` | 2024 | 1 | ERCOT operating-procedure change effective 2024-08-01: ECRS release… | 2024-08-01 |  |
| `market_design.CAISO` | {"capacity_market": true, "net_cone_p… | 2 | Per-ISO market design. ISOs absent here fall back to ``DEFAULT_MARK… |  | auto-generated, needs-citation |
| `market_design.ERCOT` | {"capacity_market": false, "net_cone_… | 2 | Per-ISO market design. ISOs absent here fall back to ``DEFAULT_MARK… |  | auto-generated, needs-citation |
| `market_design.MISO` | {"capacity_market": true, "net_cone_p… | 2 | MISO seasonal Planning Resource Auction (PRA). Anchored on MISO's p… | 2024-09-23 |  |
| `market_design.NEISO` | {"capacity_market": true, "net_cone_p… | 2 | Per-ISO market design. ISOs absent here fall back to ``DEFAULT_MARK… |  | auto-generated, needs-citation |
| `market_design.NYISO` | {"capacity_market": true, "net_cone_p… | 2 | Per-ISO market design. ISOs absent here fall back to ``DEFAULT_MARK… |  | auto-generated, needs-citation |
| `market_design.PJM` | {"capacity_market": true, "net_cone_p… | 2 | Per-ISO market design. ISOs absent here fall back to ``DEFAULT_MARK… |  | auto-generated, needs-citation |
| `market_design_vintages.MISO` | [{"delivery_year": "2021-2022", "net_… | 2 | Per-ISO vintages, ascending by delivery-period start year. A vintag… |  | auto-generated, needs-citation |
| `market_design_vintages.NEISO` | [{"delivery_year": "2020-2021", "net_… | 2 | Per-ISO vintages, ascending by delivery-period start year. A vintag… |  | auto-generated, needs-citation |
| `market_design_vintages.NYISO` | [{"delivery_year": "2021-2022", "net_… | 2 | Per-ISO vintages, ascending by delivery-period start year. A vintag… |  | auto-generated, needs-citation |
| `market_design_vintages.PJM` | [{"delivery_year": "2021/2022", "net_… | 2 | Per-ISO vintages, ascending by delivery-period start year. A vintag… |  | auto-generated, needs-citation |
| `scenario.capacity_market_clearing` | False | 1 | GATED, default-OFF. CR-1 reserve-margin-indexed capacity demand cur… | 2026-07-11 |  |
| `scenario.ercot_market_design` | auto | 1 | ERCOT scarcity-pricing regime: |  | auto-generated, needs-citation |
| `scenario.market_design_retirement_floor` | False | 1 | GATED, default-OFF |  | auto-generated, needs-citation |

## Policy

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `carbon_price_paths.high` | {"2026": 0, "2030": 30, "2040": 70, "… | 1 | Resources for the Future (RFF) carbon price scenario set | 2023-09 | modeled |
| `carbon_price_paths.low` | {"2026": 0, "2030": 8, "2040": 18, "2… | 1 | Resources for the Future (RFF) carbon price scenario set | 2023-09 | modeled |
| `carbon_price_paths.mid` | {"2026": 0, "2030": 15, "2040": 35, "… | 1 | Resources for the Future (RFF) carbon price scenario set | 2023-09 | modeled |
| `carbon_price_paths.zero` | {"2026": 0, "2030": 0, "2040": 0, "20… | 1 | Resources for the Future (RFF) carbon price scenario set | 2023-09 | modeled |
| `scenario.carbon_price` | 0.0 | 1 | Market simulator model design decision | 2026-05 |  |
| `scenario.ira_45u_last_year` | 2032 | 2 | 26 U.S.C. §45U(e) — §45U zero-emission (existing) nuclear PTC termi… | 2025-07 |  |
| `scenario.ira_expiry_year` | 2035 | 2 | CBO scoring of Inflation Reduction Act energy provisions | 2023-04 | modeled, stale |
| `scenario.ira_itc_solar` | 0.3 | 2 | IRS Inflation Reduction Act final rules (IRC sections 45, 48, 48E) | 2024-04 |  |
| `scenario.ira_itc_storage` | 0.3 | 2 | IRS Inflation Reduction Act final rules (IRC sections 45, 48, 48E) | 2024-04 |  |
| `scenario.ira_other_clean_50pct_year` | 2035 | 2 | 26 U.S.C. §45Y(d) / §48E(e) tech-neutral phase-down (non-wind/solar… | 2025-07 | confidence-flagged |
| `scenario.ira_other_clean_75pct_year` | 2034 | 2 | 26 U.S.C. §45Y(d) / §48E(e) tech-neutral phase-down (non-wind/solar… | 2025-07 | confidence-flagged |
| `scenario.ira_other_clean_last_full_year` | 2033 | 2 | 26 U.S.C. §45Y(d) / §48E(e) tech-neutral phase-down (non-wind/solar… | 2025-07 | confidence-flagged |
| `scenario.ira_other_clean_phaseout_end` | 2036 | 2 | 26 U.S.C. §45Y(d) / §48E(e) tech-neutral phase-down (non-wind/solar… | 2025-07 | confidence-flagged |
| `scenario.ira_ptc_wind` | 26.0 | 2 | IRS Inflation Reduction Act final rules (IRC sections 45, 48, 48E) | 2024-04 |  |
| `scenario.ira_wind_solar_last_year` | 2027 | 2 | IRA credit schedule per OBBBA (One Big Beautiful Bill Act), enacted… | 2025 | auto-generated |
| `scenario.nox_price` | 0.0 | 1 | Market simulator model design decision | 2026-05 |  |
| `scenario.rps_enabled` | True | 1 | whether to enforce RPS as LP constraint |  | auto-generated, needs-citation |
| `scenario.wind_ptc_vintage_offers` | False | 1 | ERCOT-65 PTC vintage scoping (structural flag, default off): wind d… | 2026-07 | auto-generated |
| `state_rps_acp.CAISO` | 50.0 | 2 | RPS Alternative Compliance Payment (ACP) ceiling, $/MWh, by ISO.  E… | 2024 | auto-generated |
| `state_rps_acp.NEISO` | 65.0 | 2 | RPS Alternative Compliance Payment (ACP) ceiling, $/MWh, by ISO.  E… | 2024 | auto-generated |
| `state_rps_acp.NYISO` | 40.0 | 2 | RPS Alternative Compliance Payment (ACP) ceiling, $/MWh, by ISO.  E… | 2024 | auto-generated |
| `state_rps_floors.CAISO` | {"2026": 0.5, "2030": 0.6, "2040": 0.… | 1 | California SB 100 — The 100 Percent Clean Energy Act of 2018 | 2018-09 | stale |
| `state_rps_floors.ERCOT` | {"2026": 0.0, "2030": 0.0, "2040": 0.… | 1 | Market simulator model design decision | 2026-05 |  |
| `state_rps_floors.NEISO` | {"2026": 0.3, "2030": 0.45, "2040": 0… | 2 | MA Clean Energy Standard + regional state CES blend |  | auto-generated, needs-citation |
| `state_rps_floors.NYISO` | {"2026": 0.4, "2030": 0.7, "2040": 1.… | 2 | NY CLCPA — 70% renewable by 2030, 100% zero-emission by 2040 | 2030 | auto-generated |
| `wind_ptc_statutory_usd_per_mwh` | {"2023": 28.0, "2024": 29.0, "2025": … | 2 | IRS §45 annual inflation-adjustment notices, wind, facilities place… | 2025-05 | auto-generated |

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
| `gas_availability_factor.CAISO` | 0.866 | 2 | NERC Generating Availability Data System (GADS), Generating Unit St… | 2019-2023 |  |
| `gas_availability_factor.ERCOT` | 0.866 | 2 | NERC Generating Availability Data System (GADS), Generating Unit St… | 2019-2023 |  |
| `gas_availability_factor.NEISO` | 0.866 | 2 | NERC Generating Availability Data System (GADS), Generating Unit St… | 2019-2023 |  |
| `gas_availability_factor.NYISO` | 0.866 | 2 | NERC Generating Availability Data System (GADS), Generating Unit St… | 2019-2023 |  |
| `gas_availability_factor.PJM` | 0.866 | 2 | NERC Generating Availability Data System (GADS), Generating Unit St… | 2019-2023 |  |
| `geothermal_params.egs.eford` | 0.05 | 2 | comparable to nuclear. DOE GeoVision 2019 | 2019 | auto-generated |
| `historic_outage_overlay_by_iso.CAISO` | False | 2 | Effective default for the historic (facility-summed) CAMPD outage o… |  | auto-generated, needs-citation |
| `historic_outage_overlay_by_iso.ERCOT` | True | 2 | Effective default for the historic (facility-summed) CAMPD outage o… |  | auto-generated, needs-citation |
| `historic_outage_overlay_by_iso.NEISO` | False | 2 | Effective default for the historic (facility-summed) CAMPD outage o… |  | auto-generated, needs-citation |
| `historic_outage_overlay_by_iso.NYISO` | False | 2 | Effective default for the historic (facility-summed) CAMPD outage o… |  | auto-generated, needs-citation |
| `historic_outage_overlay_by_iso.PJM` | False | 2 | Effective default for the historic (facility-summed) CAMPD outage o… |  | auto-generated, needs-citation |
| `hydrogen_turbine_params.h2_ccgt.eford` | 0.06 | 2 | above gas CT — immature fleet. Engineering judgment |  | auto-generated, needs-citation |
| `hydrogen_turbine_params.h2_ct.eford` | 0.06 | 2 | above gas CT — immature fleet. Engineering judgment |  | auto-generated, needs-citation |
| `import_eford.CAISO` | 0.02 | 2 | Import tranche forced outage rate, per ISO. CAISO's WECC supply blo… |  | auto-generated, needs-citation |
| `import_eford.MISO` | 0.0 | 2 | Import tranche forced outage rate, per ISO. CAISO's WECC supply blo… |  | auto-generated, needs-citation |
| `import_eford.NEISO` | 0.0 | 2 | Import tranche forced outage rate, per ISO. CAISO's WECC supply blo… |  | auto-generated, needs-citation |
| `import_eford.NYISO` | 0.0 | 2 | Import tranche forced outage rate, per ISO. CAISO's WECC supply blo… |  | auto-generated, needs-citation |
| `import_eford.PJM` | 0.0 | 2 | Import tranche forced outage rate, per ISO. CAISO's WECC supply blo… |  | auto-generated, needs-citation |
| `nuclear_monthly_cf.CAISO` | [1.0, 0.99, 0.96, 0.95, 0.97, 1.0, 1.… | 2 | NRC / IAEA Power Reactor Information System (PRIS), 2019-2023 | 2024-01 |  |
| `nuclear_monthly_cf.ERCOT` | [0.97, 0.99, 0.89, 0.78, 0.84, 0.93, … | 2 | NRC / IAEA Power Reactor Information System (PRIS), 2019-2023 | 2024-01 |  |
| `pjm_primary_reserve_lsc_factor` | 1.5 | 2 | --- PJM Primary Reserve requirement (energy+reserve co-optimization… | 2024 | auto-generated |
| `planning_reserve_margin_by_iso.CAISO` | 0.15 | 2 | Target planning reserve margin per ISO for the reserve-margin adequ… |  | auto-generated, needs-citation |
| `planning_reserve_margin_by_iso.ERCOT` | 0.1375 | 2 | Target planning reserve margin per ISO for the reserve-margin adequ… |  | auto-generated, needs-citation |
| `planning_reserve_margin_by_iso.MISO` | 0.179 | 2 | Target planning reserve margin per ISO for the reserve-margin adequ… |  | auto-generated, needs-citation |
| `planning_reserve_margin_by_iso.NEISO` | 0.157 | 2 | Target planning reserve margin per ISO for the reserve-margin adequ… |  | auto-generated, needs-citation |
| `planning_reserve_margin_by_iso.NYISO` | 0.244 | 2 | Target planning reserve margin per ISO for the reserve-margin adequ… |  | auto-generated, needs-citation |
| `planning_reserve_margin_by_iso.PJM` | 0.178 | 2 | Target planning reserve margin per ISO for the reserve-margin adequ… |  | auto-generated, needs-citation |
| `planning_reserve_margin_icap_to_ucap_ratio_by_iso.MISO` | 0.9325842696629213 | 2 | ICAP-basis planning-reserve-margin correction (stage-5 §6 ICAP/UCAP… | 2026-07 | auto-generated |
| `planning_reserve_margin_icap_to_ucap_ratio_by_iso.PJM` | 0.7699412258606213 | 2 | ICAP-basis planning-reserve-margin correction (stage-5 §6 ICAP/UCAP… | 2026-07 | auto-generated |
| `rggi_reserve_escalation` | 0.07 | 2 | RGGI Cost Containment Reserve (CCR) trigger price rises 7%/yr nomin… | 2017 | auto-generated |
| `scenario.as_reserve_formula` | False | 1 | CAISO backcast: withhold a formula-based |  | auto-generated, needs-citation |
| `scenario.as_reserve_withholding` | False | 1 | ERCOT backcast probe: remove the |  | auto-generated, needs-citation |
| `scenario.caiso_reserve_coopt` | False | 2 | CAISO: enable the per-generator |  | auto-generated, needs-citation |
| `scenario.caiso_reserve_online_scoped` | False | 1 | CAISO: online-quality scoping |  | auto-generated, needs-citation |
| `scenario.cc_outage_derate_from_top` | False | 2 | Outage capacity comes off the TOP of a CC_REGULAR plant's offer sta… |  | auto-generated, needs-citation |
| `scenario.energy_reserve_coopt` | False | 1 | Co-optimize energy and operating |  | auto-generated, needs-citation |
| `scenario.ercot_load_resource_reserve` | False | 1 | ERCOT co-opt: credit the |  | auto-generated, needs-citation |
| `scenario.ercot_load_resource_reserve_from_year` | 2023 | 1 | First weather year the |  | auto-generated, needs-citation |
| `scenario.ercot_noncampd_plant_availability` | False | 2 | ERCOT CAMPD-blind per-plant availability (default off, ERCOT backca… |  | auto-generated, needs-citation |
| `scenario.ercot_nuclear_unit_availability` | False | 2 | ERCOT unit-level (window-grain) nuclear refuel availability (defaul… | 2024 | auto-generated |
| `scenario.ercot_ordc_total_reserve` | False | 1 | ERCOT multi-product co-opt: ALSO |  | auto-generated, needs-citation |
| `scenario.ercot_reserve_supply_cap` | False | 1 | ERCOT: cap the multi-product co-opt's |  | auto-generated, needs-citation |
| `scenario.ercot_reserve_supply_cap_from_year` | 2023 | 1 | First weather year the |  | auto-generated, needs-citation |
| `scenario.ercot_reserve_supply_forward` | False | 1 | ERCOT: source the RTOLCAP / |  | auto-generated, needs-citation |
| `scenario.ercot_thermal_dam_availability` | False | 2 | ERCOT measured CLASS-day thermal availability (default off, ERCOT b… | 2023 | auto-generated |
| `scenario.forecast_fossil_retirement_economic` | True | 1 | In a forecast, fossil |  | auto-generated, needs-citation |
| `scenario.gas_st_wefor_base_override` | None | 3 | ISO-gated gas-steam forced-outage base override. The global ST_GAS … |  | auto-generated, needs-citation |
| `scenario.historic_outage_overlay` | True | 2 | Historic (facility-summed) CAMPD outage overlay: hard-zeros coal/CC… |  | auto-generated, needs-citation |
| `scenario.miso_measured_reserve_requirements` | False | 1 | MISO: replace the |  | auto-generated, needs-citation |
| `scenario.miso_reserve_pergen` | False | 1 | MISO: PER-ASSET reserve co-optimization |  | auto-generated, needs-citation |
| `scenario.miso_zonal_reserve_zones` | None | 1 | Optional override of the zonal reserve family zone set; None -> (MI… | 2026-07-01 |  |
| `scenario.miso_zonal_reserves` | False | 1 | MISO BPM-002 §3.3/§3.3.2 (minimum Zonal Operating Reserve Requireme… | 2022-09-30 |  |
| `scenario.neiso_dynamic_reserve_requirements` | False | 2 | GATED, default-OFF |  | auto-generated, needs-citation |
| `scenario.nuclear_unit_availability` | False | 2 | ISO-generic unit-level (window-grain) nuclear refuel/derate availab… | 2026-07 | auto-generated |
| `scenario.nyiso_dynamic_reserve_requirements` | False | 1 | GATED, default-OFF |  | auto-generated, needs-citation |
| `scenario.nyiso_synchronised_reserve` | False | 1 | NYISO online-gated SPINNING |  | auto-generated, needs-citation |
| `scenario.nysdec_peaker_rule_availability` | False | 1 | NYSDEC 6 NYCRR Subpart 227-3 "peaker rule" availability overlay (NY… | 2023-05 | auto-generated |
| `scenario.ordc_voll` | 5000.0 | 1 | PUCT Project 52631 (Review of the ERCOT Scarcity Pricing Mechanism)… | 2022-01 |  |
| `scenario.outage_source` | statistical | 3 | Tier 3 (calibration) — thermal availability source. "statistical" (… |  | auto-generated, needs-citation |
| `scenario.pjm_reserve_online_gated` | False | 1 | PJM: gate co-opt reserve to ONLINE |  | auto-generated, needs-citation |
| `scenario.pjm_reserve_online_rho` | 1.0 | 1 | online-headroom multiplier for the gated |  | auto-generated, needs-citation |
| `scenario.pjm_reserve_pergen` | False | 1 | PJM: PER-GENERATOR reserve co-optimization |  | auto-generated, needs-citation |
| `scenario.pjm_reserve_pergen_size_split` | False | 1 | PJM: SIZE-SPLIT the pergen |  | auto-generated, needs-citation |
| `scenario.pjm_reserve_pergen_sync` | False | 1 | PJM: per-gen OPPORTUNITY-COST reserve |  | auto-generated, needs-citation |
| `scenario.pjm_reserve_supply_cap` | False | 1 | PJM analogue of ercot_reserve_supply_cap: |  | auto-generated, needs-citation |
| `scenario.planning_reserve_margin` | 0.1375 | 2 | Fallback/override planning |  | auto-generated, needs-citation |
| `scenario.planning_reserve_margin_override` | None | 2 | Sensitivity lever: |  | auto-generated, needs-citation |
| `scenario.reserve_margin_build_enabled` | None | 1 | Adequacy backstop: after the |  | auto-generated, needs-citation |
| `scenario.retirement_fom_multiplier_coal` | 1.3 | 2 | coal faces higher effective FOM |  | auto-generated, needs-citation |
| `scenario.retirement_fom_multiplier_gas_cc` | 1.0 | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.retirement_fom_multiplier_gas_ct` | 1.0 | 2 | (regulatory risk, carbon liability, rising insurance). Source: Laza… | 2024 | auto-generated |
| `scenario.retirement_fom_multiplier_gas_st` | 1.0 | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.retirement_fom_multiplier_nuclear` | 1.0 | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.retirement_fom_multiplier_oil` | 1.0 | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.retirement_years_coal` | 3 | 2 | Measured EIA-860 announced-to-deactivation lag for coal (RE-status … | 2026-07-15 | curated |
| `scenario.retirement_years_gas_cc` | 3 | 2 | modern CCs get 3 years (most flexible/valuable) |  | auto-generated, needs-citation |
| `scenario.retirement_years_gas_ct` | 2 | 2 | CTs get 2 years |  | auto-generated, needs-citation |
| `scenario.retirement_years_gas_st` | 2 | 2 | legacy gas steam — same grace as a CT |  | auto-generated, needs-citation |
| `scenario.retirement_years_nuclear` | 3 | 2 | nuclear — long grace (irreversible exit) |  | auto-generated, needs-citation |
| `scenario.retirement_years_oil` | 2 | 2 | oil/distillate peakers/steam |  | auto-generated, needs-citation |
| `scenario.unit_outage_maxgen_events` | False | 3 | Tier 3 (calibration) — declared-event-window revealed unit derates,… | 2026-07 | auto-generated |
| `scenario.unit_outage_short_windows` | False | 3 | Tier 3 (calibration) — short (1-5 day) unit-outage windows for base… | 2025 | auto-generated |
| `scenario.unit_partial_outage_windows` | False | 3 | Tier 3 (calibration) — unit-grain partial-derate plateaus, the seco… | 2026-07 | auto-generated |
| `scenario.voll` | 5000.0 | 0 | Public Utility Commission of Texas / ERCOT Nodal Protocols | 2023-01 | stale |
| `scenario.wefor_multiplier` | 1.0 | 3 | Global scale on every thermal class's |  | auto-generated, needs-citation |
| `scenario.wefor_residual` | None | 3 | Historic-backcast WEFOR floor for |  | auto-generated, needs-citation |
| `scenario.wefor_residual_groups` | None | 2 | Restrict the WEFOR residual cap (wefor_residual) to a chosen set of… | 2024 | auto-generated |
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
| `ercot_as_revenue_per_kw_yr.storage` | 169.0 | 2 | ERCOT ancillary-service market revenue ($/kW-yr) credited in the ca… | 2023 | auto-generated |
| `ercot_rtolcap_fwd_storage_reserve_frac` | 0.35 | 2 | Forward on-line storage responsive-reserve fraction of installed st… | 2023 | auto-generated |
| `pumped_storage_duration_hours` | 10.0 | 2 | Pumped-storage hydro fleet parameters (EIA-860 PS units enter the s… | 2023 | auto-generated |
| `pumped_storage_rte` | 0.8 | 2 | Round-trip efficiency: mid-range of the 70-85% PSH band (DOE/Sandia… |  | auto-generated, needs-citation |
| `renewable_elcc_curves_by_iso.MISO.wind` | {"penetration_basis": "pct_of_peak_lo… | 2 | Penetration-indexed ELCC accreditation curves per ISO (CR-3.1, plan… | 2026-07 | auto-generated |
| `renewable_elcc_curves_by_iso.NYISO.offshore_wind` | {"penetration_basis": null, "points":… | 2 | Penetration-indexed ELCC accreditation curves per ISO (CR-3.1, plan… | 2026-07 | auto-generated |
| `renewable_elcc_curves_by_iso.NYISO.solar` | {"penetration_basis": null, "points":… | 2 | Penetration-indexed ELCC accreditation curves per ISO (CR-3.1, plan… | 2026-07 | auto-generated |
| `renewable_elcc_curves_by_iso.NYISO.wind` | {"penetration_basis": null, "points":… | 2 | Penetration-indexed ELCC accreditation curves per ISO (CR-3.1, plan… | 2026-07 | auto-generated |
| `renewable_elcc_curves_by_iso.PJM.solar` | {"penetration_basis": "installed_mw",… | 2 | Penetration-indexed ELCC accreditation curves per ISO (CR-3.1, plan… | 2026-07 | auto-generated |
| `renewable_elcc_curves_by_iso.PJM.wind` | {"penetration_basis": "installed_mw",… | 2 | Penetration-indexed ELCC accreditation curves per ISO (CR-3.1, plan… | 2026-07 | auto-generated |
| `scenario.caiso_storage_as_reservation` | False | 2 | Reserve the MEASURED hourly |  | auto-generated, needs-citation |
| `scenario.co2_transport_storage_cost` | 15.0 | 2 | $/tCO2 for captured CO2 |  | auto-generated, needs-citation |
| `scenario.eac_price_storage` | 0.0 | 1 | $/MWh on discharge |  | auto-generated, needs-citation |
| `scenario.ercot_storage_as_deployment` | False | 1 | ERCOT: measured-award energy |  | auto-generated, needs-citation |
| `scenario.ercot_storage_as_deployment_from_year` | 2023 | 1 | First weather year the |  | auto-generated, needs-citation |
| `scenario.ercot_storage_as_duration_gate` | False | 1 | ERCOT endogenous storage AS duration gate: adds the published per-p… | 2022-12 |  |
| `scenario.ercot_storage_as_endogenous` | False | 1 | ERCOT forward (G5): make the |  | auto-generated, needs-citation |
| `scenario.ercot_storage_as_product_credit` | False | 1 | ERCOT multi-product co-opt, |  | auto-generated, needs-citation |
| `scenario.ercot_storage_as_reserve` | False | 1 | ERCOT co-opt: credit the measured |  | auto-generated, needs-citation |
| `scenario.ercot_storage_as_reserve_from_year` | 2025 | 1 | First weather year the |  | auto-generated, needs-citation |
| `scenario.ercot_storage_capability_measured` | False | 2 | ERCOT measured hourly BATTERY-fleet capability re-basis (default of… | 2025-12 | auto-generated |
| `scenario.pumped_storage_dispatch_adder` | None | 3 | Tier 3 — pumped-storage dispatch adder ($/MWh discharged). PSH pure… |  | auto-generated, needs-citation |
| `scenario.renewable_elcc_curves` | True | 2 | CR-3.1 (plan §3.4.1; P-2B Option A |  | auto-generated, needs-citation |
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
| `storage_base_fleet_mw.MISO.high` | 1440.0 | 2 | EIA-860 2025 Early Release energy-storage schedule (data/raw/eia-86… | 2025 | auto-generated |
| `storage_base_fleet_mw.MISO.low` | 600.0 | 2 | EIA-860 2025 Early Release energy-storage schedule (data/raw/eia-86… | 2025 | auto-generated |
| `storage_base_fleet_mw.MISO.mid` | 800.0 | 2 | EIA-860 2025 Early Release energy-storage schedule (data/raw/eia-86… | 2025 | auto-generated |
| `storage_base_fleet_mw.NEISO.high` | 1280.0 | 2 | EIA-860 2025 Early Release energy-storage schedule (data/raw/eia-86… | 2025 | auto-generated |
| `storage_base_fleet_mw.NEISO.low` | 580.0 | 2 | EIA-860 2025 Early Release energy-storage schedule (data/raw/eia-86… | 2025 | auto-generated |
| `storage_base_fleet_mw.NEISO.mid` | 770.0 | 2 | EIA-860 2025 Early Release energy-storage schedule (data/raw/eia-86… | 2025 | auto-generated |
| `storage_base_fleet_mw.NYISO.high` | 280.0 | 2 | EIA-860 2025 Early Release energy-storage schedule (data/raw/eia-86… | 2025 | auto-generated |
| `storage_base_fleet_mw.NYISO.low` | 190.0 | 2 | EIA-860 2025 Early Release energy-storage schedule (data/raw/eia-86… | 2025 | auto-generated |
| `storage_base_fleet_mw.NYISO.mid` | 250.0 | 2 | EIA-860 2025 Early Release energy-storage schedule (data/raw/eia-86… | 2025 | auto-generated |
| `storage_base_fleet_mw.PJM.high` | 870.0 | 2 | EIA-860 2025 Early Release energy-storage schedule (data/raw/eia-86… | 2025 | auto-generated |
| `storage_base_fleet_mw.PJM.low` | 380.0 | 2 | EIA-860 2025 Early Release energy-storage schedule (data/raw/eia-86… | 2025 | auto-generated |
| `storage_base_fleet_mw.PJM.mid` | 500.0 | 2 | EIA-860 2025 Early Release energy-storage schedule (data/raw/eia-86… | 2025 | auto-generated |
| `storage_degradation_replacement_fraction` | 0.25 | 2 | Cycling-degradation cost. Each MWh discharged consumes a slice of t… |  | auto-generated, needs-citation |
| `storage_deployment_ceiling_mw.CAISO` | 25000.0 | 2 | ~52% of ~48 GW peak. Source: CAISO IEPR |  | auto-generated, needs-citation |
| `storage_deployment_ceiling_mw.ERCOT` | 45000.0 | 2 | ~53% of ~85 GW peak. Source: ERCOT CDR |  | auto-generated, needs-citation |
| `storage_deployment_ceiling_mw.NEISO` | 13000.0 | 2 | ~50% of ~26 GW peak. Source: ISO-NE CELT Report 2024 | 2024 | auto-generated |
| `storage_deployment_ceiling_mw.NYISO` | 16000.0 | 2 | ~50% of ~32 GW peak. Source: NYISO Gold Book 2024 | 2024 | auto-generated |
| `storage_deployment_ceiling_mw.PJM` | 75000.0 | 2 | ~50% of ~150 GW peak. Source: PJM Load Forecast Report 2024 | 2024 | auto-generated |
| `storage_elcc_by_duration` | [[2.0, 0.4], [4.0, 0.6], [6.0, 0.75],… | 2 | Effective load-carrying capability (ELCC) of storage as a function … |  | auto-generated, needs-citation |
| `storage_elcc_by_duration_by_iso.PJM` | [[4.0, 0.5], [6.0, 0.58], [8.0, 0.62]… | 2 | Per-ISO published storage ELCC class-rating tables, overriding the … | 2025 | auto-generated |
| `storage_elcc_dilution_ceiling_ratio_by_iso.ERCOT` | 0.7641196013289037 | 2 | The CDR's own fleet-average BESS ELCC ratio at full deployment-ceil… | 2030 | auto-generated |
| `storage_elcc_dilution_reference_mw_by_iso.ERCOT` | 20438.0 | 2 | Dec 2025 CDR: operational + CDR-eligible planned BESS | 2025 | auto-generated |
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
| `thermal_elcc_class_rating_by_iso.PJM.coal` | 0.83 | 2 | Coal |  | auto-generated, needs-citation |
| `thermal_elcc_class_rating_by_iso.PJM.gas_cc` | 0.74 | 2 | Gas Combined Cycle |  | auto-generated, needs-citation |
| `thermal_elcc_class_rating_by_iso.PJM.gas_ct` | 0.6 | 2 | Gas Combustion Turbine |  | auto-generated, needs-citation |
| `thermal_elcc_class_rating_by_iso.PJM.gas_st` | 0.73 | 2 | Steam (gas/oil steam) |  | auto-generated, needs-citation |
| `thermal_elcc_class_rating_by_iso.PJM.nuclear` | 0.95 | 2 | Nuclear |  | auto-generated, needs-citation |
| `thermal_elcc_class_rating_by_iso.PJM.oil` | 0.91 | 2 | Diesel Utility (the 2026/27 official oil/diesel class) | 2026 | auto-generated |

## Structural

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `end_year` | 2050 | 0 | Market simulator model design decision | 2026-05 |  |
| `hours_per_year` | 8760 | 0 | Market simulator model design decision | 2026-05 |  |
| `nyiso_interface_ttc_by_year` | {"2023": {"('Upstate_West', 'Capital_… | 3 | NYISO Central-East interface transfer limit by backcast year, track… | 2024-03 |  |
| `nyiso_rcpf_locational.East.products` | [["east_30min_total", 1200.0, 0.0, 50… | 2 | NYISO requires 1,200 MW of 30-minute Reserves located east of the C… | 2021-07 |  |
| `nyiso_rcpf_locational.East.zones` | ["Capital_Hudson", "Lower_Hudson", "N… | 2 | NYISO 'East' operating-reserve region = load zones F-K (east of the… | 2021-07 |  |
| `nyiso_rcpf_locational.NYC.products` | [["nyc_30min_total", 1000.0, 0.0, 500… | 2 | NYISO procures 500 MW of 10-minute and 1,000 MW of 30-minute Reserv… | 2021-07 |  |
| `nyiso_rcpf_locational.NYC.zones` | ["NYC"] | 2 | NYISO 'New York City' operating-reserve region = load zone J, the m… | 2021-07 |  |
| `nyiso_rcpf_locational.SENY.products` | [["seny_30min_total", 1100.0, 0.0, 50… | 2 | SENY 30-minute reserve demand-curve maximum $500/MWh is sourced (FE… | 2021-07 |  |
| `nyiso_rcpf_locational.SENY.zones` | ["Lower_Hudson", "NYC", "Long_Island"] | 2 | NYISO 'Southeastern New York' (SENY) operating-reserve region = loa… | 2021-07 |  |
| `scenario.as_revenue_enabled` | False | 1 | Credit ERCOT ancillary-service market |  | auto-generated, needs-citation |
| `scenario.as_revenue_multiplier` | 1.0 | 2 | Scenario scale on the calibrated AS |  | auto-generated, needs-citation |
| `scenario.caiso_asymmetric_path_ratings` | False | 2 | CAISO asymmetric measured Path 15 / Path 26 directional ratings. Th… | 2024 | auto-generated |
| `scenario.caiso_bidir_intertie` | False | 2 | Model CAISO's WECC tie as a SINGLE |  | auto-generated, needs-citation |
| `scenario.caiso_citygate_flow_date` | False | 2 | Place each measured daily |  | auto-generated, needs-citation |
| `scenario.caiso_citygate_spot_level` | False | 2 | Level the CAISO gas hub overlay |  | auto-generated, needs-citation |
| `scenario.caiso_corridor_atc_forward` | False | 1 | Cap each CAISO per-hub corridor's |  | auto-generated, needs-citation |
| `scenario.caiso_corridor_flow_limit` | False | 2 | Cap each CAISO per-hub corridor's |  | auto-generated, needs-citation |
| `scenario.caiso_dsw_surplus_clean` | False | 2 | Carry the MEASURED surplus-hour |  | auto-generated, needs-citation |
| `scenario.caiso_firm_import_selfschedule` | False | 2 | Floor the firm/contracted |  | auto-generated, needs-citation |
| `scenario.caiso_firm_import_shape` | False | 2 | Shape the firm/contracted CAISO |  | auto-generated, needs-citation |
| `scenario.caiso_import_solar_shape` | False | 2 | Restore the CAISO negative midday |  | auto-generated, needs-citation |
| `scenario.caiso_locational_as_families` | False | 2 | CAISO: add zone-masked |  | auto-generated, needs-citation |
| `scenario.caiso_per_hub_intertie` | False | 2 | Model CAISO's WECC tie as TWO signed |  | auto-generated, needs-citation |
| `scenario.caiso_per_year_import_caps` | False | 2 | CAISO per-year SP15-pocket import caps. The SP15-split foundation (… | 2026-07 | auto-generated |
| `scenario.caiso_perhub_firm_base` | False | 2 | Keep the firm/contracted import |  | auto-generated, needs-citation |
| `scenario.caiso_ra_bridge_curtailment_release` | False | 1 | CAISO RA bridge |  | auto-generated, needs-citation |
| `scenario.caiso_ra_bridge_decommit` | False | 1 | Solar-proportional / seasonal |  | auto-generated, needs-citation |
| `scenario.caiso_ra_mustoffer` | False | 1 | CAISO Resource-Adequacy must-offer |  | auto-generated, needs-citation |
| `scenario.caiso_ra_mustoffer_quantity_gate` | False | 1 | CAISO RA must-offer |  | auto-generated, needs-citation |
| `scenario.caiso_scarcity_import_headroom` | False | 2 | CAISO: count the hourly |  | auto-generated, needs-citation |
| `scenario.caiso_scarcity_pricing` | False | 1 | CAISO: enable the post-solve |  | auto-generated, needs-citation |
| `scenario.caiso_solar_cap_at_delivered` | False | 1 | INTERIM STOPGAP (Lever-D P6), |  | auto-generated, needs-citation |
| `scenario.caiso_solar_deliverability` | False | 1 | CAISO Lever-D structural solar |  | auto-generated, needs-citation |
| `scenario.caiso_solar_deliverability_floor` | 0.5 | 3 | floor on the derate so even |  | auto-generated, needs-citation |
| `scenario.caiso_solar_deliverability_k` | 0.15 | 3 | local-deliverability sensitivity |  | auto-generated, needs-citation |
| `scenario.caiso_solar_endogenous_spill` | False | 1 | CAISO midday price fix: give the |  | auto-generated, needs-citation |
| `scenario.caiso_solar_shape_nl_hi_pct` | 30.0 | 2 | Net-load percentile (of the |  | auto-generated, needs-citation |
| `scenario.caiso_solar_shape_nl_lo_pct` | 10.0 | 2 | Net-load percentile at/below |  | auto-generated, needs-citation |
| `scenario.campd_bins_path` | /home/user/market-simulator/data/raw/… | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.capacity_deliverability_limits` | False | 2 | GATED, default-OFF locational |  | auto-generated, needs-citation |
| `scenario.capacity_market_clearing_by_iso` | None | 2 | RC-1B |  | auto-generated, needs-citation |
| `scenario.carry_operating_mothballs` | False | 1 | backcast. None (default) uses the canonical 2025-Early-Release snap… | 2025 | auto-generated |
| `scenario.cc_capacity_reconcile` | False | 2 | When True (ERCOT backcast), each CC_REGULAR plant's LP capacity is … |  | auto-generated, needs-citation |
| `scenario.cc_capacity_reconcile_path` | /home/user/market-simulator/data/raw/… | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.cc_committed_hr_mult` | 1.23 | 3 | CC part-load penalty ~23% |  | auto-generated, needs-citation |
| `scenario.cc_committed_hr_override` | None | 3 | Combined-cycle tranche heat-rate OVERRIDES (relative to the plant's… |  | auto-generated, needs-citation |
| `scenario.cc_committed_per_plant` | False | 2 | When True, each CC_REGULAR bin's committed-tranche % (minimum stabl… |  | auto-generated, needs-citation |
| `scenario.cc_duct_peaking` | False | 2 | When True, every CC_REGULAR / CC_CHP plant's peaking-tranche % come… |  | auto-generated, needs-citation |
| `scenario.cc_duct_peaking_cap_pct` | None | 2 | Physical cap (percentage points of capacity) on the per-plant ``cc_… |  | auto-generated, needs-citation |
| `scenario.cc_econ_hr_mult` | 0.96 | 3 | CC incremental HR ~4% below avg |  | auto-generated, needs-citation |
| `scenario.cc_econ_hr_override` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.cc_intermediate_cf_threshold` | 50.0 | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.cc_intermediate_split` | False | 1 | CC_REGULAR analogue of ct_intermediate_split / st_gas_intermediate_… | 2023 | auto-generated |
| `scenario.cc_mustrun_per_plant` | False | 2 | Per-plant gas local-reliability commitment (must-run) floor on the … | 2026-07 | auto-generated |
| `scenario.cc_nameplate_summer_derate` | False | 2 | When True, combined-cycle (CC_REGULAR / CC_CHP) plants in the per-p… |  | auto-generated, needs-citation |
| `scenario.cc_peak_hr_override` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.cc_peak_hr_penalty` | 1.15 | 3 | CC duct-firing increment |  | auto-generated, needs-citation |
| `scenario.cc_peaking_per_plant` | False | 2 | When True, the CC_REGULAR plants in fleet.CC_REGULAR_PEAKING_PCT_BY… |  | auto-generated, needs-citation |
| `scenario.chp_btm_floor_pct` | 40.0 | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.chp_export_floor_measured` | False | 3 | Measured steam-following export floor (backcast/calibration overlay… |  | auto-generated, needs-citation |
| `scenario.chp_steam_floor_p25` | False | 3 | Measured multi-year steam-host operating-level floor (composes with… | 2026-07 | auto-generated |
| `scenario.chp_steam_following` | False | 3 | CHP cogeneration treatment. When chp_steam_following is True, each … |  | auto-generated, needs-citation |
| `scenario.cod_ramp_enabled` | True | 3 | Commercial-operation-date (COD) vintage ramp (market_sim.data.cod_r… |  | auto-generated, needs-citation |
| `scenario.committed_ramp_spread` | 0.0 | 2 | Render the per-plant committed band as an n-slice rising ramp (span… |  | auto-generated, needs-citation |
| `scenario.confirmed_exits_enabled` | True | 2 | GATED, default-ON (flipped 2026-07-05). Owner sign-off once the con… | 2026-07-05 | curated |
| `scenario.control_retrofit_forward` | False | 2 | Forward emission-control retrofit channel (Tier 2; default OFF). do… | 2026-07 | auto-generated |
| `scenario.control_retrofit_path` | /home/user/market-simulator/data/raw/… | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.ct_committed_hr_mult` | 1.28 | 3 | CT part-load penalty ~28% |  | auto-generated, needs-citation |
| `scenario.ct_committed_hr_override` | None | 3 | CT_CHP tranche heat-rate overrides (relative to base HR), applied t… |  | auto-generated, needs-citation |
| `scenario.ct_deployment_floor_frac` | 1.0 | 3 | Fraction of the measured deployment energy to force (1.0 = the full… |  | auto-generated, needs-citation |
| `scenario.ct_deployment_overlay` | False | 3 | CT_PEAKER AS/RUC-deployment energy overlay (backcast only). Distinc… |  | auto-generated, needs-citation |
| `scenario.ct_drag_cap` | 0.47 | 3 | 95th-pct evening CF (hottest ramp hours) |  | auto-generated, needs-citation |
| `scenario.ct_drag_intercept` | -0.1427 | 3 | floor zero-crossing ~20.3 GW |  | auto-generated, needs-citation |
| `scenario.ct_drag_ramp_end` | 22 | 3 | ramp window end hour (exclusive, local std) |  | auto-generated, needs-citation |
| `scenario.ct_drag_ramp_start` | 15 | 3 | ramp window start hour (inclusive, local std) |  | auto-generated, needs-citation |
| `scenario.ct_drag_slope_per_gw` | 0.00703 | 3 | evening CF per GW net-load |  | auto-generated, needs-citation |
| `scenario.ct_econ_hr_mult` | 0.97 | 3 | CT incremental HR ~3% below avg |  | auto-generated, needs-citation |
| `scenario.ct_econ_hr_override` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.ct_intermediate_cf_threshold` | 50.0 | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.ct_intermediate_split` | False | 1 | Intermediate-duty CT split (MISO calibration). EIA-860 confirms MIS… |  | auto-generated, needs-citation |
| `scenario.ct_mustrun_floor_frac` | 1.0 | 3 | Fraction of the observed monthly CT_PEAKER net generation to force … |  | auto-generated, needs-citation |
| `scenario.ct_mustrun_per_plant` | False | 3 | When True, simple-cycle peakers (CT_PEAKER) carry a per-plant month… |  | auto-generated, needs-citation |
| `scenario.ct_peak_hr_override` | None | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.ct_peak_hr_penalty` | 1.1 | 3 | CT / gas-steam peaking increment |  | auto-generated, needs-citation |
| `scenario.datacenter_percentile` | 0.5 | 2 | Continuous PB-2 sampler lever |  | auto-generated, needs-citation |
| `scenario.econ_split_by_group` | {} | 2 | Economic-tranche split. Maps a CAMPD bin's Plant_Group to a 3-eleme… |  | auto-generated, needs-citation |
| `scenario.egs_available_year` | 2030 | 1 | year EGS enters the candidate pool |  | auto-generated, needs-citation |
| `scenario.egs_pmin_fraction` | 0.2 | 2 | EGS turn-down floor (fraction of rated) |  | auto-generated, needs-citation |
| `scenario.eia860_vintage_year` | None | 2 | Year-matched EIA-860 vintage for a |  | auto-generated, needs-citation |
| `scenario.end_year` | None | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.entry_screen_diagnostics` | False | 2 | GATED, default-OFF diagnostic |  | auto-generated, needs-citation |
| `scenario.ercot_as_adequacy_frac` | 1.0 | 2 | AS-aware commitment: the coverage |  | auto-generated, needs-citation |
| `scenario.ercot_as_critical_frac` | 0.0 | 1 | Reserve level (as a fraction of each AS |  | auto-generated, needs-citation |
| `scenario.ercot_as_forward_requirement` | False | 1 | ERCOT: set each multi-product AS |  | auto-generated, needs-citation |
| `scenario.ercot_as_n_ramp` | 12 | 1 | Number of equal-width steps discretizing each AS |  | auto-generated, needs-citation |
| `scenario.ercot_ct_offer_surface` | False | 2 | ERCOT G-22 condition-responsive CT/peaker offer surface (default of… | 2026-07 | auto-generated |
| `scenario.ercot_ecrs_conservative_deployment` | False | 1 | Published pre-reform ECRS deployment design. 2023-06-10 go-live (ER… | 2024-09 |  |
| `scenario.ercot_ecrs_requirement` | False | 1 | ERCOT co-opt: ADD the measured ECRS |  | auto-generated, needs-citation |
| `scenario.ercot_ecrs_requirement_from_year` | 2023 | 1 | First weather year the ECRS |  | auto-generated, needs-citation |
| `scenario.ercot_gtc_limits_measured` | False | 3 | Measured ERCOT GTC transfer limits (backcast/calibration overlay). … |  | auto-generated, needs-citation |
| `scenario.ercot_multiproduct_as_coopt` | False | 1 | ERCOT: replace the single lumped |  | auto-generated, needs-citation |
| `scenario.ercot_offer_surface_binned_path` | None | 2 | Path to the measured condition-binned ladder JSON (default: the fro… |  | auto-generated, needs-citation |
| `scenario.ercot_offer_surface_cleared_share` | False | 1 | ERCOT DAM CLEARED-SHARE offer boundary (ERCOT-72, default off, ERCO… | 2024 | auto-generated |
| `scenario.ercot_offer_surface_cleared_share_path` | None | 3 | Path to the frozen cleared-share boundary JSON (default: data/raw/_… |  | auto-generated, needs-citation |
| `scenario.ercot_offer_surface_cleared_share_state` | False | 1 | ERCOT-73 commitment-STATE conditioning of the cleared-share wall (d… |  | auto-generated, needs-citation |
| `scenario.ercot_offer_surface_cleared_share_state_path` | None | 3 | Path to the frozen commitment-loading state JSON (default: data/raw… |  | auto-generated, needs-citation |
| `scenario.ercot_offer_surface_conditional` | False | 2 | ERCOT G-22 §8 / ercot37-filed HETEROGENEITY-PRESERVING condition-re… | 2026-07 | auto-generated |
| `scenario.ercot_offer_surface_lowcurve` | False | 2 | ERCOT G-22 conditional-offer-distribution LOW leg (default off, ERC… | 2023 | auto-generated |
| `scenario.ercot_offer_surface_lowcurve_floorscoped` | False | 1 | ERCOT FLOOR-SCOPED committed-LSL markdown (default off, ERCOT-gated… |  | auto-generated, needs-citation |
| `scenario.ercot_offer_surface_lowcurve_path` | None | 2 | Path to the measured low-curve condition-binned JSON (default: the … |  | auto-generated, needs-citation |
| `scenario.ercot_offer_surface_midcurve_conditional` | False | 2 | ERCOT MID-CURVE offer surface (G-22 lever A', the ERCOT analogue of… |  | auto-generated, needs-citation |
| `scenario.ercot_offer_surface_midcurve_path` | None | 2 | Path to the frozen mid-curve surface JSON (default: data/raw/_valid… |  | auto-generated, needs-citation |
| `scenario.ercot_offer_surface_min_bin` | 0 | 2 | Minimum net-load bin index (0 = loosest) at which the peak-rung wal… |  | auto-generated, needs-citation |
| `scenario.ercot_online_capacity_envelope` | False | 1 | ERCOT: cap the multi-product |  | auto-generated, needs-citation |
| `scenario.ercot_online_capacity_envelope_extreme` | False | 1 | ERCOT: the |  | auto-generated, needs-citation |
| `scenario.ercot_online_capacity_envelope_measured` | False | 1 | ERCOT: the |  | auto-generated, needs-citation |
| `scenario.ercot_ordc_only_scarcity` | False | 1 | ERCOT: pre-RTC+B ORDC-ONLY reserve |  | auto-generated, needs-citation |
| `scenario.ercot_thermal_as_endogenous` | False | 1 | ERCOT forward: the thermal |  | auto-generated, needs-citation |
| `scenario.ercot_wtx_curtail_depth_solar` | 0.1637 | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.ercot_wtx_curtail_depth_wind` | 0.1004 | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.ercot_wtx_curtailment_driver` | False | 3 | ERCOT West Texas Export corridor VRE curtailment-share driver (back… | 2026-07 | auto-generated |
| `scenario.fixed_om_oil` | 25.0 | 2 | legacy oil/distillate steam & CT — high O&M, |  | auto-generated, needs-citation |
| `scenario.gt_ambient_derate` | False | 2 | Gas-turbine AMBIENT-TEMPERATURE capacity derate (gt_ambient_derate,… |  | auto-generated, needs-citation |
| `scenario.gt_ambient_derate_ref_c` | 35.0 | 2 | net-summer rating reference temp (C) |  | auto-generated, needs-citation |
| `scenario.gt_ambient_derate_slope_cc` | 0.004 | 2 | CC fractional loss per C above ref |  | auto-generated, needs-citation |
| `scenario.gt_ambient_derate_slope_ct` | 0.006 | 2 | CT fractional loss per C above ref |  | auto-generated, needs-citation |
| `scenario.hindcast` | False | 2 | Capacity-hindcast mode (W2-P5): forecast machinery run backwards fr… | 2022 | auto-generated |
| `scenario.hours` | 8760 | 0 | Market simulator model design decision | 2026-05 |  |
| `scenario.interchange_shape_export_pct` | 90.0 | 3 | Percentile of the measured |  | auto-generated, needs-citation |
| `scenario.interchange_shape_import_pct` | 90.0 | 3 | Percentile of the measured |  | auto-generated, needs-citation |
| `scenario.interchange_shaping` | False | 1 | Priced-interchange node: shape the |  | auto-generated, needs-citation |
| `scenario.interchange_shaping_export_only` | False | 1 | Like interchange_shaping but |  | auto-generated, needs-citation |
| `scenario.iso` | ERCOT | 0 | Market simulator model design decision | 2026-05 |  |
| `scenario.limited_foresight_dispatch` | False | 2 | GATED, default-OFF (G-30 in-year |  | auto-generated, needs-citation |
| `scenario.local_capacity_constraints` | False | 3 | GATED, default-OFF local- |  | auto-generated, needs-citation |
| `scenario.maintenance_monthly_shape` | True | 3 | FORECAST-mode planned-maintenance |  | auto-generated, needs-citation |
| `scenario.mass_cap_enabled` | False | 1 | Emissions mass-cap / cap-and-trade LP row (PP-2.1 IPM parity). GATE… | 2026-07 | auto-generated |
| `scenario.mass_cap_program` | None | 1 | pollutant/program label for the row |  | auto-generated, needs-citation |
| `scenario.mass_cap_tons` | None | 1 | explicit annual budget (tons CO2) |  | auto-generated, needs-citation |
| `scenario.maxgen_emergency_tier_pricing` | False | 3 | Declared-window ELMP emergency-tier pricing (the MISO F5 scarcity-d… | 2026-07 | auto-generated |
| `scenario.measured_ramp_capability` | False | 1 | Reconcile FleetArrays.ramp10's |  | auto-generated, needs-citation |
| `scenario.miso_firm_import_floor` | False | 1 | Firm (must-flow) import floor on the |  | auto-generated, needs-citation |
| `scenario.miso_firm_imports` | False | 1 | Manitoba Hydro firm-hydro import block: |  | auto-generated, needs-citation |
| `scenario.miso_pjm_border_anchor` | False | 1 | MISO eastern PJM seam: re-anchor the |  | auto-generated, needs-citation |
| `scenario.miso_pjm_lmp_import_pricing` | False | 1 | MISO PJM seam: price each PJM |  | auto-generated, needs-citation |
| `scenario.miso_rdt_tcdc` | False | 1 | MISO: replace the static JOA contract |  | auto-generated, needs-citation |
| `scenario.miso_rpe_pricing` | False | 1 | MISO: price the Reserve Procurement |  | auto-generated, needs-citation |
| `scenario.miso_seam_export_limit` | False | 1 | MISO reference-price seam: the EXPORT |  | auto-generated, needs-citation |
| `scenario.miso_seam_flow_limit` | False | 1 | MISO reference-price seam: cap each |  | auto-generated, needs-citation |
| `scenario.miso_seam_flow_percentile` | None | 3 | Override the per-seam import |  | auto-generated, needs-citation |
| `scenario.miso_seam_measured_ladder` | False | 1 | MISO reference-price seams: price |  | auto-generated, needs-citation |
| `scenario.miso_south_seam_split` | False | 1 | MISO: host the South seam's |  | auto-generated, needs-citation |
| `scenario.mode` | forecast | 0 | "forecast" \| "backcast". Backcast pins the run |  | auto-generated, needs-citation |
| `scenario.must_run_cf` | 0.85 | 3 | assumed CF for CHP must-run emissions post-processing |  | auto-generated, needs-citation |
| `scenario.negative_renewable_offers` | False | 1 | Let curtailable wind/solar set a |  | auto-generated, needs-citation |
| `scenario.neighbor_hr_forward_skill` | None | 2 | FORWARD-SKILL validation |  | auto-generated, needs-citation |
| `scenario.neiso_offer_surface_binned_path` | None | 2 | Path to the measured NEISO condition-binned ladder JSON (default: t… |  | auto-generated, needs-citation |
| `scenario.neiso_offer_surface_conditional` | False | 2 | NEISO condition-responsive fast-start offer surface — the ISO-NE an… |  | auto-generated, needs-citation |
| `scenario.neiso_offer_surface_min_bin` | 0 | 2 | Minimum net-load bin index at which the wall engages (0 = every bin… |  | auto-generated, needs-citation |
| `scenario.neiso_oil_burn_budget` | False | 1 | NEISO oil-burn inventory budget. |  | auto-generated, needs-citation |
| `scenario.neiso_rcpf_enabled` | False | 1 | Master flag for the NEISO RCPF overlay. |  | auto-generated, needs-citation |
| `scenario.neiso_rcpf_products` | None | 2 | Optional override of the ISO-NE |  | auto-generated, needs-citation |
| `scenario.nyiso_firm_imports` | False | 1 | NYISO firm (must-flow) import baseload: |  | auto-generated, needs-citation |
| `scenario.nyiso_forward_net_import_twh` | None | 2 | FORECAST band |  | auto-generated, needs-citation |
| `scenario.nyiso_import_reconciliation` | False | 1 | NYISO priced import-node |  | auto-generated, needs-citation |
| `scenario.nyiso_iroquois_winter_spread` | False | 1 | NYISO eastern (Iroquois Z2) |  | auto-generated, needs-citation |
| `scenario.nyiso_li_lcr_tsl` | False | 1 | NYISO Long Island Zone-K LCR/TSL mechanism |  | auto-generated, needs-citation |
| `scenario.nyiso_local_selfsupply` | False | 1 | NYISO Long Island (zone K) local |  | auto-generated, needs-citation |
| `scenario.nyiso_nyc_lcr_tsl` | False | 1 | NYISO New York City (Zone J) LCR/TSL |  | auto-generated, needs-citation |
| `scenario.nyiso_rcpf_enabled` | False | 1 | Model design decision — post-solve NYISO Reserve Constraint Penalty… | 2021-07 |  |
| `scenario.nyiso_rcpf_locational` | None | 2 | Model design decision — override of the NYISO locational reserve-re… | 2021-07 |  |
| `scenario.nyiso_rcpf_products` | None | 2 | NYISO operating-reserve requirements (largest single contingency ~1… | 2021-07 |  |
| `scenario.nyiso_spin_headroom_frac` | 1.0 | 2 | Path-B committed-capacity target |  | auto-generated, needs-citation |
| `scenario.ordc_as_plan_mw` | 0.0 | 2 | Default 0: ERCOT's published reserve inputs (RTOLCAP/RTOFFCAP) coun… | 2024-06 |  |
| `scenario.ordc_lolp_mu_mw` | 0.0 | 2 | Neutral fallback (0); ERCOT publishes the seasonal reserve-error me… | 2024-10 |  |
| `scenario.ordc_lolp_params_path` | None | 2 | ERCOT NP6-576-ER 'LOLP Distribution by Season and TOD Block' (repor… | 2024-10 |  |
| `scenario.ordc_lolp_shift_sigma` | 0.5 | 2 | PUCT Project 48551 order of 2019-01-17: two rightward LOLP-curve sh… | 2020-03 |  |
| `scenario.ordc_lolp_sigma_mw` | 1400.0 | 2 | PROVISIONAL flat fallback, bounded from the OBDRR048 floor breakpoi… | 2023-11 |  |
| `scenario.ordc_mcl_mw` | 3000.0 | 1 | OBDRR038 (Minimum Contingency Level Updates to Align with PUCT Orde… | 2022-01 |  |
| `scenario.ordc_multistep_floor` | True | 2 | OBDRR048 multi-step RTORPA price floor, PUCT-approved 2023-10-12, e… | 2023-11 |  |
| `scenario.pjm_congestion` | False | 3 | PJM transmission-congestion lever (break the copper-plate). PJM cle… |  | auto-generated, needs-citation |
| `scenario.pjm_da_virtual_bids` | False | 2 | PJM Day-Ahead virtual-bid layer (G-22 lever B — DA procurement dept… | 2024 | auto-generated |
| `scenario.pjm_da_virtual_surface_path` | None | 2 | Path to the measured condition-binned virtual-bid surface JSON (def… |  | auto-generated, needs-citation |
| `scenario.pjm_east_interface_cut` | False | 3 | PJM measured EAST interface cut (backcast/calibration overlay, pjm-… | 2026-07 | auto-generated |
| `scenario.pjm_measured_interface_limits` | False | 3 | Measured PJM internal interface transfer limits (backcast/calibrati… | 2024 | auto-generated |
| `scenario.pjm_offer_midcurve_conditional` | False | 2 | PJM MID-CURVE offer surface (G-22 lever A', default off, PJM-gated)… |  | auto-generated, needs-citation |
| `scenario.pjm_offer_midcurve_path` | None | 2 | Path to the measured mid-curve surface JSON (default: the frozen da… |  | auto-generated, needs-citation |
| `scenario.pjm_offer_midcurve_segments` | None | 2 | Optional measured-segment scope for the mid-curve floor. None (defa… |  | auto-generated, needs-citation |
| `scenario.pjm_offer_surface_binned_path` | None | 2 | Path to the measured PJM condition-binned ladder JSON (default: the… |  | auto-generated, needs-citation |
| `scenario.pjm_offer_surface_conditional` | False | 2 | PJM condition-responsive energy-offer surface — the PJM analogue of… | 2026-07 | auto-generated |
| `scenario.pjm_offer_surface_min_bin` | 0 | 2 | Minimum net-load bin index at which the wall engages (0 = every bin… |  | auto-generated, needs-citation |
| `scenario.pjm_seam_export_limit` | False | 1 | PJM reference-price seam: the EXPORT |  | auto-generated, needs-citation |
| `scenario.pjm_seam_flow_limit` | False | 1 | PJM reference-price seam: the PJM |  | auto-generated, needs-citation |
| `scenario.pjm_seam_flow_percentile` | None | 3 | Override the per-seam |  | auto-generated, needs-citation |
| `scenario.pjm_seam_measured_ladder` | False | 1 | PJM reference-price seams: price |  | auto-generated, needs-citation |
| `scenario.plant_level_fleet` | False | 3 | Tier 3 (calibration) — keep the non-ERCOT fleet at full per-plant g… |  | auto-generated, needs-citation |
| `scenario.plant_registry_path` | /home/user/market-simulator/data/raw/… | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.policy_bundle` | current | 1 | "current" / "tight" / "rollback" — the |  | auto-generated, needs-citation |
| `scenario.ramp_limits` | False | 3 | GATED, default-OFF plant-group hourly ramp |  | auto-generated, needs-citation |
| `scenario.reliability_deployment_floor_frac` | 1.0 | 3 | Fraction of the measured reliability-deployment energy to force (1.… |  | auto-generated, needs-citation |
| `scenario.reliability_deployment_overlay` | False | 3 | Spatial reliability-deployment overlay (backcast only). The general… |  | auto-generated, needs-citation |
| `scenario.reliability_floor` | False | 1 | ISO-agnostic temperature/net-load |  | auto-generated, needs-citation |
| `scenario.reliability_floor_overrides` | {} | 2 | reliability-commitment floor: look up the ISO in RELIABILITY_FLOOR_… |  | auto-generated, needs-citation |
| `scenario.renewable_keep_running_value` | 20.0 | 2 | $/MWh, the curtailable |  | auto-generated, needs-citation |
| `scenario.retiree_cems_cap` | False | 2 | When True, each within-window retiree plant (fleet.load_retired_wit… |  | auto-generated, needs-citation |
| `scenario.rtcb_reliability_deployment_mw` | 0.0 | 2 | Reliability-deployment offset |  | auto-generated, needs-citation |
| `scenario.scarcity_pricing_enabled` | False | 1 | Model design decision — post-solve ORDC overlay replicating ERCOT r… | 2014-06 |  |
| `scenario.screen_reserve_value_enabled` | True | 1 | Model design decision — the retirement/new-entry screens value each… | 2014-06 |  |
| `scenario.staged_oversupply_thinning` | False | 2 | GATED, default-OFF (G-30 |  | auto-generated, needs-citation |
| `scenario.staged_thinning_max_gw_per_year` | 3.0 | 2 | GW/yr/fuel-class exit budget |  | auto-generated, needs-citation |
| `scenario.start_year` | None | 2 | Simulation horizon. ``None`` defers to constants.START_YEAR / END_Y… | 2026 | auto-generated |
| `scenario.tech_cost_path` | mid | 1 | "low"/"mid"/"high" -> NREL ATB 2024 | 2024 | auto-generated |
| `scenario.tech_cost_percentile` | 0.5 | 1 | Continuous counterpart of |  | auto-generated, needs-citation |
| `scenario.temp_dependent_derate` | False | 2 | TEMPERATURE-DEPENDENT capacity derate (temp_dependent_derate, off b… |  | auto-generated, needs-citation |
| `scenario.temp_derate_ref_c` | 15.0 | 2 | ISO 59 F rating point (GT + gas-steam) |  | auto-generated, needs-citation |
| `scenario.temp_derate_slope_cc` | 0.0076 | 2 | CC fractional loss per C above ref |  | auto-generated, needs-citation |
| `scenario.temp_derate_slope_ct` | 0.0126 | 2 | CT fractional loss per C above ref |  | auto-generated, needs-citation |
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
| `da_commitment_horizon_hours` | 24 | 2 | Day-ahead unit-commitment horizon (hours). CAISO's day-ahead market… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_gas_cc_ccs.high` | 25.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_gas_cc_ccs.low` | 10.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eac_price_reference.eac_gas_cc_ccs.mid` | 15.0 | 2 | Exogenous EAC price reference ranges ($/MWh) by resource type, as l… |  | auto-generated, needs-citation |
| `eford.gas_cc_ccs` | 0.05 | 2 | Equivalent forced outage rate (demand) by technology class. Source:… |  | auto-generated, needs-citation |
| `export_tranches.CAISO` | [["export_solar", 2500.0, 8.0], ["exp… | 2 | Export sinks: each block absorbs up to its capacity as *negative* g… |  | auto-generated, needs-citation |
| `export_tranches.NEISO` | [["export_firm", 700.0, 16.0], ["expo… | 2 | Export sinks: each block absorbs up to its capacity as *negative* g… |  | auto-generated, needs-citation |
| `export_tranches.NYISO` | [["export_surplus", 600.0, 10.0]] | 2 | Export sinks: each block absorbs up to its capacity as *negative* g… |  | auto-generated, needs-citation |
| `export_tranches.PJM` | [["export_firm", 700.0, 36.0], ["expo… | 2 | Export sinks: each block absorbs up to its capacity as *negative* g… |  | auto-generated, needs-citation |
| `gas_tranche_shares_by_group.CC_CHP` | [0.3, 0.6, 0.1] | 2 | Gas offer-curve tranche SHARES (committed / economic / peaking) of … | 2026-07 | auto-generated |
| `gas_tranche_shares_by_group.CC_REGULAR` | [0.3, 0.6, 0.1] | 2 | Gas offer-curve tranche SHARES (committed / economic / peaking) of … | 2026-07 | auto-generated |
| `gas_tranche_shares_by_group.CT_CHP` | [0.0, 0.88, 0.12] | 2 | Gas offer-curve tranche SHARES (committed / economic / peaking) of … | 2026-07 | auto-generated |
| `gas_tranche_shares_by_group.CT_PEAKER` | [0.0, 0.88, 0.12] | 2 | Gas offer-curve tranche SHARES (committed / economic / peaking) of … | 2026-07 | auto-generated |
| `gas_tranche_shares_by_group.ST_CHP` | [0.4, 0.5, 0.1] | 2 | Gas offer-curve tranche SHARES (committed / economic / peaking) of … | 2026-07 | auto-generated |
| `gas_tranche_shares_by_group.ST_GAS` | [0.4, 0.5, 0.1] | 2 | Gas offer-curve tranche SHARES (committed / economic / peaking) of … | 2026-07 | auto-generated |
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
| `import_tranche_ef.CAISO.DSW_CCGT` | 0.37 | 2 | desert-SW combined-cycle gas (~7 HR) |  | auto-generated, needs-citation |
| `import_tranche_ef.CAISO.DSW_CT` | 0.55 | 2 | desert-SW combustion turbine (~10.4 HR) |  | auto-generated, needs-citation |
| `import_tranche_ef.CAISO.DSW_solar_PV` | 0.0 | 2 | desert-SW solar + Palo Verde nuclear |  | auto-generated, needs-citation |
| `import_tranche_ef.CAISO.PNW_hydro_base` | 0.0 | 2 | firm Pacific-NW hydro — specified, zero-EF |  | auto-generated, needs-citation |
| `import_tranche_ef.CAISO.PNW_midC` | 0.0 | 2 | Mid-Columbia hydro/wind |  | auto-generated, needs-citation |
| `import_tranche_ef.CAISO.WECC_scarcity` | 0.428 | 2 | unspecified west-wide |  | auto-generated, needs-citation |
| `import_tranches.CAISO` | [["PNW_hydro_base", 800.0, 28.0], ["P… | 2 | Priced import/export node, per ISO (playbook §8.2): an interconnect… |  | auto-generated, needs-citation |
| `import_tranches.NEISO` | [["HQ_PhaseII", 1000.0, 18.0], ["High… | 2 | Priced import/export node, per ISO (playbook §8.2): an interconnect… |  | auto-generated, needs-citation |
| `import_tranches.NYISO` | [["HQ_hydro", 900.0, 14.0], ["IESO_On… | 2 | Priced import/export node, per ISO (playbook §8.2): an interconnect… |  | auto-generated, needs-citation |
| `import_tranches.PJM` | [["import_scarcity_1", 1000.0, 46.0],… | 2 | Priced import/export node, per ISO (playbook §8.2): an interconnect… |  | auto-generated, needs-citation |
| `import_tranches_by_year.NYISO` | {"2023": [["HQ_hydro", 900.0, 13.0], … | 2 | Export sinks: each block absorbs up to its capacity as *negative* g… | 2023 | auto-generated |
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
| `nuclear_dormant_until` | {"8011": 2027} | 2 | Dormant nuclear plants the EIA-860 operable schedule lists as OP th… | 2019 | auto-generated |
| `nuclear_monthly_cf.MISO` | [0.93, 0.92, 0.85, 0.82, 0.78, 0.91, … | 2 | Nuclear monthly capacity factors (12 values, Jan–Dec) by ISO. Sprin… | 2019 | auto-generated |
| `nuclear_monthly_cf.NEISO` | [1.0, 0.99, 0.95, 0.95, 0.98, 1.0, 1.… | 2 | Nuclear monthly capacity factors (12 values, Jan–Dec) by ISO. Sprin… | 2019 | auto-generated |
| `nuclear_monthly_cf.NYISO` | [1.0, 1.0, 0.95, 0.94, 0.97, 1.0, 1.0… | 2 | Nuclear monthly capacity factors (12 values, Jan–Dec) by ISO. Sprin… | 2019 | auto-generated |
| `nuclear_monthly_cf.PJM` | [1.0, 1.0, 0.95, 0.94, 0.97, 1.0, 1.0… | 2 | Nuclear monthly capacity factors (12 values, Jan–Dec) by ISO. Sprin… | 2019 | auto-generated |
| `nuclear_monthly_cf_by_year.CAISO` | {"2023": [0.96, 1.0, 0.92, 1.0, 1.0, … | 2 | Per-year nuclear monthly capacity factor derived from EIA-923 net g… |  | auto-generated, needs-citation |
| `nuclear_monthly_cf_by_year.ERCOT` | {"2023": [1.0, 1.0, 0.89, 0.75, 0.78,… | 2 | Per-year nuclear monthly capacity factor derived from EIA-923 net g… |  | auto-generated, needs-citation |
| `nuclear_monthly_cf_by_year.MISO` | {"2023": [1.0, 0.94, 0.87, 0.83, 0.76… | 2 | Per-year nuclear monthly capacity factor derived from EIA-923 net g… |  | auto-generated, needs-citation |
| `nuclear_monthly_cf_by_year.NEISO` | {"2023": [0.98, 0.98, 0.99, 0.41, 0.6… | 2 | Per-year nuclear monthly capacity factor derived from EIA-923 net g… |  | auto-generated, needs-citation |
| `nuclear_monthly_cf_by_year.NYISO` | {"2023": [1.0, 0.98, 0.86, 0.74, 0.99… | 2 | Per-year nuclear monthly capacity factor derived from EIA-923 net g… |  | auto-generated, needs-citation |
| `nuclear_monthly_cf_by_year.PJM` | {"2023": [1.0, 0.97, 0.9, 0.85, 0.91,… | 2 | Per-year nuclear monthly capacity factor derived from EIA-923 net g… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.CAISO.nuclear` | 1.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.ERCOT.nuclear` | 2.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.MISO.nuclear` | 1.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.NEISO.nuclear` | 0.5 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.NYISO.nuclear` | 0.5 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `queue_cap_per_tech_gw.PJM.nuclear` | 1.0 | 2 | Per-technology annual interconnection queue caps (GW/yr) by ISO. So… |  | auto-generated, needs-citation |
| `scenario.caiso_commitment_posture` | False | 1 | CAISO: the SAME pooled linear |  | auto-generated, needs-citation |
| `scenario.caiso_gas_commitment_floor` | False | 1 | CAISO Resource-Adequacy |  | auto-generated, needs-citation |
| `scenario.caiso_lcr_commitment_credit` | False | 1 | CAISO: credit the LCR |  | auto-generated, needs-citation |
| `scenario.caiso_ra_bridge_startup_aware` | False | 1 | CAISO RA bridge STARTUP-AWARE |  | auto-generated, needs-citation |
| `scenario.caiso_ra_startup_bridge` | False | 1 | CAISO RA must-offer STARTUP-COST-AWARE |  | auto-generated, needs-citation |
| `scenario.ccs_available_year` | 2030 | 1 | year CCUS enters the candidate pool |  | auto-generated, needs-citation |
| `scenario.ccs_capture_rate` | 0.9 | 2 | fraction of CO2 captured by CCUS |  | auto-generated, needs-citation |
| `scenario.ccs_retrofit_available_year` | 2028 | 2 | Earliest year retrofits can occur. |  | auto-generated, needs-citation |
| `scenario.ccs_retrofit_capex_kw` | 900.0 | 2 | $/kW for post-combustion capture retrofit. |  | auto-generated, needs-citation |
| `scenario.ccs_retrofit_capture_rate` | 0.9 | 2 | Fraction of CO2 captured. 0.90 = 90%. |  | auto-generated, needs-citation |
| `scenario.ccs_retrofit_hr_penalty` | 0.12 | 2 | Fractional heat rate increase from capture parasitic load. |  | auto-generated, needs-citation |
| `scenario.ccs_retrofit_max_gw_per_year` | 3.0 | 2 | GW/yr retrofit throughput cap per ISO. |  | auto-generated, needs-citation |
| `scenario.ccs_retrofit_min_remaining_life` | 15 | 2 | Only retrofit units with ≥ N years remaining useful life. |  | auto-generated, needs-citation |
| `scenario.ccs_retrofit_vom_adder` | 8.0 | 2 | $/MWh additional VOM for capture O&M, solvent, compression. |  | auto-generated, needs-citation |
| `scenario.chp_startup_covered` | False | 2 | Tier 3 (calibration) — CHP startup costs covered by the steam host.… |  | auto-generated, needs-citation |
| `scenario.class_commitment_overrides` | {} | 2 | Per-limb run-config overrides for the generic floor, keyed "<ZONE>:… |  | auto-generated, needs-citation |
| `scenario.coal_sync_srmc_tranche` | False | 2 | SRMC-priced synchronization tranche (rebuild step 3a). Completes th… | 2024 | auto-generated |
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
| `scenario.ercot_as_aware_commitment` | False | 1 | ERCOT: run a P2 commitment screen |  | auto-generated, needs-citation |
| `scenario.ercot_gas_bridge_startup` | True | 1 | Economic (≥ min-down) bridging on the startup-restart inequality — … |  | auto-generated, needs-citation |
| `scenario.ercot_gas_commitment_bridge` | False | 1 | ERCOT gas-CC COMMITMENT BRIDGE (default off, ERCOT-gated): the comm… | 2026-07 | auto-generated |
| `scenario.fixed_om_coal` | 45.0 | 2 | Legacy avoidable-cost estimate (uncited); NREL ATB 2024 is the targ… | 2024-07 |  |
| `scenario.fixed_om_gas_cc` | 30.0 | 2 | Legacy avoidable-cost estimate (uncited); NREL ATB 2024 is the targ… | 2024-07 |  |
| `scenario.fixed_om_gas_cc_ccs` | 25.0 | 2 | CC + capture island going-forward fixed |  | auto-generated, needs-citation |
| `scenario.fixed_om_gas_ct` | 21.0 | 2 | Legacy avoidable-cost estimate (uncited); NREL ATB 2024 is the targ… | 2024-07 |  |
| `scenario.fixed_om_nuclear` | 130.0 | 2 | existing nuclear avoidable fixed O&M |  | auto-generated, needs-citation |
| `scenario.gas_offer_curve` | False | 3 | Tier 3 (calibration) — give the non-ERCOT per-plant gas fleet a ste… |  | auto-generated, needs-citation |
| `scenario.gas_st_startup_cost` | False | 3 | ISO-gated gas-steam startup amortization. The ST_GAS startup cost +… |  | auto-generated, needs-citation |
| `scenario.gas_st_startup_spread` | False | 3 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.heat_rate_bin_count` | None | 2 | Override default bin count per fuel type. |  | auto-generated, needs-citation |
| `scenario.ira_ccus_45q_last_year` | 2032 | 2 | §45Q CCUS credit: extended but phasing out post-2032. | 2032 | auto-generated |
| `scenario.miso_commitment_posture` | False | 1 | MISO: pooled linear commitment- |  | auto-generated, needs-citation |
| `scenario.offer_curve_by_group` | {} | 2 | Unified thermal offer-curve parameterization (supersedes the legacy… |  | auto-generated, needs-citation |
| `scenario.offer_curve_smoothing_exp` | 1.0 | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.offer_curve_smoothing_mid` | None | 2 | Optional midpoint anchor for the econ ramp shape: the fraction of t… |  | auto-generated, needs-citation |
| `scenario.offer_curve_smoothing_n` | 6 | 2 | N-slice smoothing of the economic offer curve. When offer_curve_smo… |  | auto-generated, needs-citation |
| `scenario.pjm_commitment_posture` | False | 1 | PJM: the SAME pooled linear |  | auto-generated, needs-citation |
| `scenario.pjm_reserve_commitment_scoped` | False | 1 | PJM path B (G-20b): scope the |  | auto-generated, needs-citation |
| `scenario.plant_tranche_config_path` | None | 2 | Optional per-plant tranche-config override CSV (one row per plant w… |  | auto-generated, needs-citation |
| `scenario.retirement_fom_multiplier_gas_cc_ccs` | 1.0 | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `scenario.retirement_years_gas_cc_ccs` | 3 | 2 | CCS-equipped CC, like a modern CC |  | auto-generated, needs-citation |
| `scenario.startup_co2_reporting` | False | 3 | EM-5 / plan §5 R6: when True, the calibration bundle adds a reporti… | 2026-07 | auto-generated |
| `scenario.storage_as_commitment` | False | 1 | ERCOT backcast: reserve the measured |  | auto-generated, needs-citation |
| `scenario.tranche_startup_amortization` | False | 1 | Fast-start tranche pricing (ISO-NE Order 825 analogue): when set, t… | 2024 | auto-generated |
| `scenario.tranche_startup_conditional_runs` | False | 1 | Fast-start amortization v4 — CONDITION-KEYED measured horizon (requ… | 2023 | auto-generated |
| `scenario.tranche_startup_measured_runs` | False | 1 | Fast-start amortization v3 — MEASURED run-length basis (requires ``… | 2023 | auto-generated |
| `st_gas_commitment_params` | [[10.0, {"startup_per_mw": 55.0, "min… | 2 | Gas steam (legacy oil/gas boilers): high thermal inertia — slow to … | 2012 | auto-generated |
| `st_gas_startup_params` | [[10.0, 55.0], [99.0, 75.0]] | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `tech_cost_multipliers.gas_cc_ccs.high.capex_per_kw` | 1.2 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.gas_cc_ccs.high.learning_rate` | 0.5 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.gas_cc_ccs.low.capex_per_kw` | 0.85 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.gas_cc_ccs.low.learning_rate` | 1.5 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.gas_cc_ccs.mid.capex_per_kw` | 1.0 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `tech_cost_multipliers.gas_cc_ccs.mid.learning_rate` | 1.0 | 2 | Per-tech capex + learning-rate multipliers for the PB-1 tech-cost u… | 2026-07 | auto-generated |
| `vom.biomass` | 5.0 | 2 | NREL ATB 2024 — biomass (fuel handling raises O&M) | 2024 | auto-generated |
| `vom.coal` | 4.5 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `vom.gas_cc` | 2.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `vom.gas_cc_ccs` | 0.0 | 2 | Variable O&M ($/MWh) by fuel type. Source: NREL ATB 2024. | 2024 | auto-generated |
| `vom.gas_ct` | 3.5 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `vom.gas_st` | 4.0 | 2 | NREL ATB 2024 — legacy gas steam (higher O&M than CC) | 2024 | auto-generated |
| `vom.hydro` | 1.4 | 2 | NREL ATB 2024 — conventional hydropower | 2024 | auto-generated |
| `vom.nuclear` | 2.5 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `vom.oil` | 4.5 | 2 | NREL ATB 2024 — oil steam/peaker O&M (≈ coal steam) | 2024 | auto-generated |
| `vom.solar` | 0.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `vom.wind` | 0.0 | 2 | NREL Annual Technology Baseline 2024 | 2024-07 |  |
| `wecc_import_tranches` | [["PNW_hydro_base", 800.0, 28.0], ["P… | 2 | CAISO WECC import supply curve tranches: (name, capacity MW, VOM $/… | 2022 | auto-generated |
| `wright_reference_gw.gas_cc_ccs` | 2.0 | 2 | GW global installed power-sector CCS as of 2024. | 2024 | auto-generated |
| `wright_reference_gw.nuclear` | 445.0 | 2 | was 440. IAEA PRIS 2025. | 2025 | auto-generated |
| `wright_reference_gw.nuclear_large` | 445.0 | 2 | Wright's Law reference cumulative installed capacity (GW global). S… | 2025 | auto-generated |
| `wright_reference_gw.nuclear_smr` | 445.0 | 2 | shares global nuclear fleet |  | auto-generated, needs-citation |

## Transmission

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `caiso_tac_zone_weights.PGE-TAC.NP15` | 0.86 | 2 | CAISO TAC-area actual hourly load (data.eia_loader) -> model zone w… |  | auto-generated, needs-citation |
| `caiso_tac_zone_weights.PGE-TAC.ZP26` | 0.14 | 2 | CAISO TAC-area actual hourly load (data.eia_loader) -> model zone w… |  | auto-generated, needs-citation |
| `caiso_tac_zone_weights.SCE-TAC.LA_BASIN` | 0.835 | 2 | CAISO TAC-area actual hourly load (data.eia_loader) -> model zone w… | 2026-07 | auto-generated |
| `caiso_tac_zone_weights.SCE-TAC.SP15` | 1.0 | 2 | CAISO TAC-area actual hourly load (data.eia_loader) -> model zone w… |  | auto-generated, needs-citation |
| `caiso_tac_zone_weights.SCE-TAC.SP15_rest` | 0.165 | 2 | CAISO TAC-area actual hourly load (data.eia_loader) -> model zone w… | 2026-07 | auto-generated |
| `caiso_tac_zone_weights.SDGE-TAC.SDGE` | 1.0 | 2 | CAISO TAC-area actual hourly load (data.eia_loader) -> model zone w… | 2026-07 | auto-generated |
| `caiso_tac_zone_weights.SDGE-TAC.SP15` | 1.0 | 2 | CAISO TAC-area actual hourly load (data.eia_loader) -> model zone w… |  | auto-generated, needs-citation |
| `caiso_tac_zone_weights.VEA-TAC.SP15` | 1.0 | 2 | CAISO TAC-area actual hourly load (data.eia_loader) -> model zone w… |  | auto-generated, needs-citation |
| `caiso_tac_zone_weights.VEA-TAC.SP15_rest` | 1.0 | 2 | CAISO TAC-area actual hourly load (data.eia_loader) -> model zone w… | 2026-07 | auto-generated |
| `import_zone.CAISO` | WECC_import | 2 | Name of each ISO's external import/export zone. CAISO's is baked in… |  | auto-generated, needs-citation |
| `import_zone.MISO` | MISO_external | 2 | Name of each ISO's external import/export zone. CAISO's is baked in… |  | auto-generated, needs-citation |
| `import_zone.NEISO` | HQ_import | 2 | Name of each ISO's external import/export zone. CAISO's is baked in… |  | auto-generated, needs-citation |
| `import_zone.NYISO` | NYISO_external | 2 | Name of each ISO's external import/export zone. CAISO's is baked in… |  | auto-generated, needs-citation |
| `import_zone.PJM` | PJM_external | 2 | Name of each ISO's external import/export zone. CAISO's is baked in… |  | auto-generated, needs-citation |
| `miso_south_external_zone` | MISO_external_South | 2 | External zone hosting the MISO-South seam's reference-price bands w… |  | auto-generated, needs-citation |
| `nyiso_interface_ttc_by_month` | {"2023": {"('Upstate_West', 'Capital_… | 2 | Measured calendar-month mean DAM TTC (MW) for the Central-East inte… |  | auto-generated, needs-citation |
| `pjm_measured_internal_ttc` | {"('PJM_AEP_Ohio', 'PJM_Dominion')": … | 2 | (2) Internal interface TTCs read from the measured PJM transfer-lim… | 2023-25 | auto-generated |
| `pjm_rggi_zone_share.PJM_AEP_Ohio` | {"2023": 0.0, "2024": 0.0, "2025": 0.0} | 2 | PJM's footprint straddles RGGI members (MD, DE, NJ; VA was a member… | 2023 | auto-generated |
| `pjm_rggi_zone_share.PJM_ATSI` | {"2023": 0.0, "2024": 0.0, "2025": 0.0} | 2 | PJM's footprint straddles RGGI members (MD, DE, NJ; VA was a member… | 2023 | auto-generated |
| `pjm_rggi_zone_share.PJM_Central_PA` | {"2023": 0.0, "2024": 0.0, "2025": 0.0} | 2 | PJM's footprint straddles RGGI members (MD, DE, NJ; VA was a member… | 2023 | auto-generated |
| `pjm_rggi_zone_share.PJM_ComEd` | {"2023": 0.0, "2024": 0.0, "2025": 0.0} | 2 | PJM's footprint straddles RGGI members (MD, DE, NJ; VA was a member… | 2023 | auto-generated |
| `pjm_rggi_zone_share.PJM_Dominion` | {"2023": 0.9881, "2024": 0.0, "2025":… | 2 | PJM's footprint straddles RGGI members (MD, DE, NJ; VA was a member… | 2023 | auto-generated |
| `pjm_rggi_zone_share.PJM_EMAAC` | {"2023": 0.7327, "2024": 0.7252, "202… | 2 | PJM's footprint straddles RGGI members (MD, DE, NJ; VA was a member… | 2023 | auto-generated |
| `pjm_rggi_zone_share.PJM_SWMAAC` | {"2023": 0.9976, "2024": 0.9976, "202… | 2 | PJM's footprint straddles RGGI members (MD, DE, NJ; VA was a member… | 2023 | auto-generated |
| `pjm_rggi_zone_share.PJM_West_APS` | {"2023": 0.0108, "2024": 0.0, "2025":… | 2 | PJM's footprint straddles RGGI members (MD, DE, NJ; VA was a member… | 2023 | auto-generated |
| `scenario.unknown_zone_default` | South_Central | 2 | zone for bins tagged "Unknown" |  | auto-generated, needs-citation |
| `thermal_accreditation_basis_by_iso.ERCOT` | seasonal_rating | 2 | Thermal accreditation basis for the same adequacy ledger, per ISO. … | 2026 | auto-generated |
| `thermal_accreditation_basis_by_iso.NEISO` | claimed_capability | 2 | Thermal accreditation basis for the same adequacy ledger, per ISO. … | 2026 | auto-generated |
| `thermal_accreditation_basis_by_iso.PJM` | elcc_class_rating | 2 | Thermal accreditation basis for the same adequacy ledger, per ISO. … | 2026 | auto-generated |

## Uncategorized

| param_id | value | tier | source | date | flags |
|---|---|---|---|---|---|
| `adequacy_external_tie_firm_mw.ERCOT` | 817.0 | 2 | Firm import contribution of asynchronous external ties counted by t… | 2023 | auto-generated |
| `caiso_citygate_transport_adder` | 0.46 | 2 | CAISO citygate -> burner-tip transport adder ($/MMBtu). The CAISO g… | 2024 | auto-generated |
| `caiso_curtail_release_eps_mw` | 1.0 | 2 | Float-noise guard on the RA bridge's curtailed-VRE release (gap G-6… |  | auto-generated, needs-citation |
| `cap_and_trade_programs.CAISO` | {"name": "CARB", "member_states": ["C… | 2 | ISO → cap-and-trade program. ERCOT and MISO have no program (no ent… |  | auto-generated, needs-citation |
| `cap_and_trade_programs.NEISO` | {"name": "RGGI", "member_states": ["C… | 2 | ISO → cap-and-trade program. ERCOT and MISO have no program (no ent… |  | auto-generated, needs-citation |
| `cap_and_trade_programs.NYISO` | {"name": "RGGI", "member_states": ["N… | 2 | ISO → cap-and-trade program. ERCOT and MISO have no program (no ent… |  | auto-generated, needs-citation |
| `cap_and_trade_programs.PJM` | {"name": "RGGI", "member_states": ["M… | 2 | ISO → cap-and-trade program. ERCOT and MISO have no program (no ent… |  | auto-generated, needs-citation |
| `capacity_curve_eligible_by_iso.CAISO` | True | 2 | bilateral RA, no demand_curve — eligibility is moot |  | auto-generated, needs-citation |
| `capacity_curve_eligible_by_iso.MISO` | True | 2 | --- CR-1C curve eligibility (governance gate) ---------------------… | 2026-07 | auto-generated |
| `capacity_curve_eligible_by_iso.NEISO` | True | 2 | --- CR-1C curve eligibility (governance gate) ---------------------… | 2026-07 | auto-generated |
| `capacity_curve_eligible_by_iso.NYISO` | False | 2 | R5a pairing adjudicated; owner sign-off pending |  | auto-generated, needs-citation |
| `capacity_curve_eligible_by_iso.PJM` | True | 2 | --- CR-1C curve eligibility (governance gate) ---------------------… | 2026-07 | auto-generated |
| `carb_allowance_budget` | {"2023": 294.1, "2024": 280.7, "2025"… | 2 | California GHG annual allowance budget (MMT CO2e/yr; 1 CA GHG allow… | 2021 | auto-generated |
| `carb_floor_escalation` | 0.07 | 2 | Forward-year allowance-price escalation rates (nominal, per year). … |  | auto-generated, needs-citation |
| `cc_econ_hr_override_default` | 1.2 | 2 | CC economic band ≈ 1.2× base HR |  | auto-generated, needs-citation |
| `cc_peak_hr_override_default` | 1.8 | 2 | CC duct-firing peak ≈ 1.8× base HR |  | auto-generated, needs-citation |
| `cc_regular_peaking_pct_by_plant` | {"58001": 15.0, "58005": 15.0, "59812… | 2 | Per-plant ERCOT CC_REGULAR peaking-tranche % (top slice of nameplat… |  | auto-generated, needs-citation |
| `chp_btm_pct_by_sector.commercial` | 65.0 | 2 | EIA-923 Schedule-8: ~65% of CHP fuel to useful thermal output |  | auto-generated, needs-citation |
| `chp_btm_pct_by_sector.industrial` | 70.0 | 2 | EIA-923 Schedule-8: ~70% of CHP fuel to useful thermal output |  | auto-generated, needs-citation |
| `chp_btm_pct_by_sector.merchant` | 35.0 | 2 | residual-identified, forecast-risk — no independent source yet |  | auto-generated, needs-citation |
| `chp_st_btm_pct` | 90.0 | 2 | ST_CHP group (tiny chemical host-steam): near-full BTM |  | auto-generated, needs-citation |
| `control_retrofit_history_end_year` | 2025 | 2 | -------------------------------------------------------------------… | 2026-07 | auto-generated |
| `control_retrofit_type_map.CD` | ["so2", 0.95] | 2 | Circulating dry scrubber |  | auto-generated, needs-citation |
| `control_retrofit_type_map.DSI` | ["so2", 0.5] | 2 | Dry sorbent injection |  | auto-generated, needs-citation |
| `control_retrofit_type_map.JB` | ["so2", 0.95] | 2 | Jet-bubbling reactor (wet FGD) |  | auto-generated, needs-citation |
| `control_retrofit_type_map.SD` | ["so2", 0.95] | 2 | Spray-dryer / dry FGD |  | auto-generated, needs-citation |
| `control_retrofit_type_map.SN` | ["nox", 0.35] | 2 | Selective non-catalytic reduction (SNCR) |  | auto-generated, needs-citation |
| `control_retrofit_type_map.SR` | ["nox", 0.9] | 2 | Selective catalytic reduction (SCR) |  | auto-generated, needs-citation |
| `ct_econ_hr_override_default` | 1.1 | 2 | CT_CHP economic band ≈ 1.1× base HR |  | auto-generated, needs-citation |
| `ct_peak_hr_override_default` | 1.3 | 2 | CT_CHP peak band ≈ 1.3× base HR |  | auto-generated, needs-citation |
| `datacenter_additions_mw.CAISO.high` | {"2024": 0.0, "2030": 1800.0, "2040":… | 2 | --- Data-center load block (CX-4, gap G-34) -----------------------… | 2026-07 | auto-generated |
| `datacenter_additions_mw.CAISO.low` | {"2024": 0.0, "2030": 0.0, "2040": 0.0} | 2 | --- Data-center load block (CX-4, gap G-34) -----------------------… | 2026-07 | auto-generated |
| `datacenter_additions_mw.CAISO.mid` | {"2024": 0.0, "2030": 1800.0, "2040":… | 2 | --- Data-center load block (CX-4, gap G-34) -----------------------… | 2026-07 | auto-generated |
| `datacenter_additions_mw.ERCOT.high` | {"2024": 0.0, "2030": 122000.0, "2035… | 2 | --- Data-center load block (CX-4, gap G-34) -----------------------… | 2026-07 | auto-generated |
| `datacenter_additions_mw.ERCOT.low` | {"2024": 0.0, "2030": 0.0} | 2 | --- Data-center load block (CX-4, gap G-34) -----------------------… | 2026-07 | auto-generated |
| `datacenter_additions_mw.ERCOT.mid` | {"2024": 0.0, "2030": 37000.0} | 2 | --- Data-center load block (CX-4, gap G-34) -----------------------… | 2026-07 | auto-generated |
| `datacenter_additions_mw.NYISO.high` | {"2025": 0.0, "2031": 10000.0} | 2 | --- Data-center load block (CX-4, gap G-34) -----------------------… | 2026-07 | auto-generated |
| `datacenter_additions_mw.NYISO.low` | {"2025": 0.0, "2031": 0.0} | 2 | --- Data-center load block (CX-4, gap G-34) -----------------------… | 2026-07 | auto-generated |
| `datacenter_additions_mw.NYISO.mid` | {"2025": 0.0, "2031": 3000.0} | 2 | --- Data-center load block (CX-4, gap G-34) -----------------------… | 2026-07 | auto-generated |
| `datacenter_additions_mw.PJM.high` | {"2025": 0.0, "2030": 30000.0, "2040"… | 2 | --- Data-center load block (CX-4, gap G-34) -----------------------… | 2026-07 | auto-generated |
| `datacenter_additions_mw.PJM.low` | {"2025": 0.0, "2030": 0.0} | 2 | --- Data-center load block (CX-4, gap G-34) -----------------------… | 2026-07 | auto-generated |
| `datacenter_additions_mw.PJM.mid` | {"2025": 0.0, "2030": 30000.0} | 2 | --- Data-center load block (CX-4, gap G-34) -----------------------… | 2026-07 | auto-generated |
| `ercot_as_plan_hold_eps` | 0.001 | 2 | --- ERCOT ORDC-only reserve-scarcity pricing (pre-RTC+B design) ---… | 2026-07 | auto-generated |
| `ercot_as_saturation_exponent` | 2.5 | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `ercot_as_saturation_ref_gw` | 4.0 | 2 | AS is a small, quickly-saturated market: per-kW AS revenue falls st… | 2023 | auto-generated |
| `ercot_gtc_link_map.NE_LOB` | [[["Northeast", "North"], 1.0]] | 2 | Crosswalk from ERCOT's published Generic Transmission Constraints (… | 2020 | auto-generated |
| `ercot_gtc_link_map.PNHNDL` | [[["Panhandle", "North"], 1.0]] | 2 | Crosswalk from ERCOT's published Generic Transmission Constraints (… | 2020 | auto-generated |
| `ercot_gtc_link_map.WESTEX` | [[["West", "North"], 0.72727272727272… | 2 | Crosswalk from ERCOT's published Generic Transmission Constraints (… | 2020 | auto-generated |
| `ercot_online_cap_deliv_coef` | 1.083 | 2 | Envelope deliverability coefficient: fit to reproduce the measured … | 2023 | auto-generated |
| `ercot_online_cap_share.CC_CHP` | [[0.6943, 0.6943, 0.6943, 0.6943, 0.6… | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_online_cap_share.CC_REGULAR` | [[0.4194, 0.4974, 0.5762, 0.6525, 0.6… | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_online_cap_share.CT_CHP` | [[0.3241, 0.3422, 0.3422, 0.3422, 0.3… | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_online_cap_share.CT_PEAKER` | [[0.0507, 0.0507, 0.0639, 0.0769, 0.0… | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_online_cap_share.ST_CHP` | [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, … | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_online_cap_share_extreme.CC_CHP` | [[0.6943, 0.6943, 0.6943, 0.6943, 0.6… | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_online_cap_share_extreme.CC_REGULAR` | [[0.4194, 0.4974, 0.5762, 0.6525, 0.6… | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_online_cap_share_extreme.CT_CHP` | [[0.3241, 0.3422, 0.3422, 0.3422, 0.3… | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_online_cap_share_extreme.CT_PEAKER` | [[0.0507, 0.0507, 0.0639, 0.0769, 0.0… | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_online_cap_share_extreme.ST_CHP` | [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, … | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_online_cap_share_measured.CC_CHP` | [[0.8005, 0.8005, 0.8005, 0.8005, 0.8… | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_online_cap_share_measured.CC_REGULAR` | [[0.4859, 0.5753, 0.661, 0.7463, 0.81… | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_online_cap_share_measured.CT_CHP` | [[0.3843, 0.4117, 0.4117, 0.4117, 0.4… | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_online_cap_share_measured.CT_PEAKER` | [[0.057, 0.0604, 0.0739, 0.0901, 0.10… | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_online_cap_share_measured.ST_CHP` | [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, … | 2 | Seasons: 0=winter(DJF) 1=spring(MAM) 2=summer(JJA) 3=fall(SON); eac… |  | auto-generated, needs-citation |
| `ercot_rtolcap_fwd_deliv_coef` | 0.8959 | 2 | Deliverability coefficient: fit to the measured RTOLCAP MW quantity… | 2023 | auto-generated |
| `ercot_rtolcap_fwd_n_decile` | 10 | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `ercot_rtolcap_fwd_n_season` | 4 | 2 | -------------------------------------------------------------------… |  | auto-generated, needs-citation |
| `ercot_rtolcap_fwd_offline_deliv_coef` | 0.7756 | 2 | Off-line deliverability coefficient: fit to the measured RTOFFCAP M… |  | auto-generated, needs-citation |
| `ercot_rtolcap_fwd_offline_share.CT_CHP` | [[0.6759, 0.6578, 0.6578, 0.6578, 0.6… | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `ercot_rtolcap_fwd_offline_share.CT_PEAKER` | [[0.9493, 0.9493, 0.9361, 0.9231, 0.9… | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `ercot_rtolcap_fwd_online_share.CC_CHP` | [[0.3011, 0.2446, 0.2092, 0.1718, 0.1… | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `ercot_rtolcap_fwd_online_share.CC_REGULAR` | [[0.2387, 0.2454, 0.2403, 0.2314, 0.2… | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `ercot_rtolcap_fwd_online_share.CT_CHP` | [[0.0454, 0.0343, 0.0325, 0.0282, 0.0… | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `ercot_rtolcap_fwd_online_share.CT_PEAKER` | [[0.0136, 0.0147, 0.0196, 0.0232, 0.0… | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `ercot_rtolcap_fwd_online_share.ST_CHP` | [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, … | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `ercot_sced_intervals_per_hour` | 12 | 2 | ERCOT SCED cadence: one SCED execution every ~5 minutes (ERCOT Noda… |  | auto-generated, needs-citation |
| `forecast_pool_requirement_by_iso.PJM.2025/2026` | 0.938 | 2 | (1+0.178) x 0.7963; PPP posted 2024-04-08 | 2024-04 | auto-generated |
| `forecast_pool_requirement_by_iso.PJM.2026/2027` | 0.917 | 2 | 146,105 MW UCAP / 159,329 MW peak; PPP 2025-05-09 | 2025-05 | auto-generated |
| `forecast_pool_requirement_by_iso.PJM.2027/2028` | 0.926 | 2 | (1+0.200) x 0.7717; BRA report 2025-12-17 | 2025-12 | auto-generated |
| `global_annual_deployment_gw.compressed_air` | 0.3 | 2 | GW/yr global CAES additions. Source: IEA 2024 pipeline. | 2024 | auto-generated |
| `global_annual_deployment_gw.flow_battery` | 0.8 | 2 | GW/yr global VRFB additions. Source: BNEF LDES tracker 2024. | 2024 | auto-generated |
| `global_annual_deployment_gw.iron_air` | 1.0 | 2 | was 0.5. |  | auto-generated, needs-citation |
| `global_annual_deployment_gw.li_ion` | 50.0 | 2 | was 30. BNEF 2025. | 2025 | auto-generated |
| `global_annual_deployment_gw.solar` | 400.0 | 2 | was 350. IRENA 2025. | 2025 | auto-generated |
| `global_annual_deployment_gw.wind` | 130.0 | 2 | was 120. IRENA 2025. | 2025 | auto-generated |
| `import_node_links.MISO` | [["MISO-Central", 7300.0], ["MISO-Nor… | 2 | Links joining an appended external zone to its border zones: (borde… | 2023-24 | auto-generated |
| `import_node_links.NYISO` | [["Upstate_West", 3000.0], ["NYC", 10… | 2 | Links joining an appended external zone to its border zones: (borde… | 2023-24 | auto-generated |
| `import_node_links.PJM` | [["PJM_ComEd", 7500.0], ["PJM_AEP_Ohi… | 2 | Links joining an appended external zone to its border zones: (borde… | 2023-24 | auto-generated |
| `inflation_rate` | 0.022 | 2 | Assumed long-run inflation rate for nominal-to-real conversion. Use… |  | auto-generated, needs-citation |
| `interface_neighbors.MISO` | [{"name": "PJM", "ba_code": "PJM", "g… | 2 | Per-ISO neighbor registry for the reference-price interface. ISO-ag… | 2024 | auto-generated |
| `interface_neighbors.PJM` | [{"name": "MISO", "ba_code": "MISO", … | 2 | Per-ISO neighbor registry for the reference-price interface. ISO-ag… | 2024 | auto-generated |
| `maintenance_monthly_shape.CC_CHP` | [0.574, 0.851, 1.658, 2.217, 1.775, 0… | 2 | Forecast-mode monthly planned-maintenance shape (12 weights, Jan..D… | 2023 | auto-generated |
| `maintenance_monthly_shape.CC_REGULAR` | [0.608, 0.961, 1.765, 2.175, 1.591, 0… | 2 | Forecast-mode monthly planned-maintenance shape (12 weights, Jan..D… | 2023 | auto-generated |
| `maintenance_monthly_shape.CT_CHP` | [1.261, 1.336, 1.692, 2.107, 1.582, 0… | 2 | Forecast-mode monthly planned-maintenance shape (12 weights, Jan..D… | 2023 | auto-generated |
| `maintenance_monthly_shape.CT_PEAKER` | [0.581, 1.131, 1.719, 1.926, 1.499, 0… | 2 | Forecast-mode monthly planned-maintenance shape (12 weights, Jan..D… | 2023 | auto-generated |
| `maintenance_monthly_shape.ST_CHP` | [0.867, 0.949, 1.495, 1.576, 1.174, 0… | 2 | Forecast-mode monthly planned-maintenance shape (12 weights, Jan..D… | 2023 | auto-generated |
| `maintenance_monthly_shape._POOLED` | [0.581, 1.131, 1.719, 1.926, 1.499, 0… | 2 | Forecast-mode monthly planned-maintenance shape (12 weights, Jan..D… | 2023 | auto-generated |
| `min_stable_pct_physical.CC_CHP` | 0.52 | 2 | combined-cycle cogeneration — same CC physics |  | auto-generated, needs-citation |
| `min_stable_pct_physical.CC_REGULAR` | 0.52 | 2 | combined cycle — WWSIS-2 52% (least-flexible fossil) |  | auto-generated, needs-citation |
| `min_stable_pct_physical.CT_CHP` | 0.38 | 2 | simple-cycle CT cogeneration — same CT physics |  | auto-generated, needs-citation |
| `min_stable_pct_physical.CT_PEAKER` | 0.38 | 2 | simple-cycle CT — WWSIS-2 38% (older frame up to 50–60%) |  | auto-generated, needs-citation |
| `min_stable_pct_physical.ST_CHP` | 0.12 | 2 | gas-steam cogeneration — same steam physics |  | auto-generated, needs-citation |
| `min_stable_pct_physical.oil` | 0.12 | 2 | oil / oil-steam — steam physics (taxonomy lumps oil into one) |  | auto-generated, needs-citation |
| `miso_rdt_contract_n_to_s_mw` | 3000.0 | 2 | -------------------------------------------------------------------… | 2024 | auto-generated |
| `miso_rdt_contract_s_to_n_mw` | 2500.0 | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `miso_rdt_default_derate_frac` | 0.92 | 2 | MISO's standing operating practice derates the modeled RDT limit be… | 2024 | auto-generated |
| `miso_rdt_tcdc_step2_start_frac` | 1.02 | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `miso_seam_flow_percentile` | 90.0 | 2 | Percentile of the per-(month × hour-of-day) measured net-import dis… |  | auto-generated, needs-citation |
| `mmbtu_per_mwh` | 3.412 | 2 | MMBtu per MWh — thermodynamic identity, used to convert the derived… |  | auto-generated, needs-citation |
| `nonfossil_announced_horizon_years` | 5 | 2 | Data-horizon gate for honoring an ANNOUNCED (non-fossil) EIA-860 re… | 2040 | auto-generated |
| `nyiso_firm_import_floor_frac.IESO_Ontario` | 0.0 | 2 | NYISO firm (must-flow) import baseload (transmission.inject_nyiso_f… | 2023 | auto-generated |
| `nyiso_local_selfsupply_frac.Long_Island` | 0.45 | 2 | NYISO local self-supply floors (transmission.inject_nyiso_local_sel… | 2023 | auto-generated |
| `ordc_floor_start_hour_2023` | 7296 | 2 | OBDRR048 effective date 2023-11-01 (ERCOT market notice M-A101623-0… | 2023-11 |  |
| `pjm_external_flow_percentile` | 95.0 | 2 | --- PJM transmission-congestion calibration (config.pjm_congestion)… |  | auto-generated, needs-citation |
| `pjm_interface_link_map` | {"('PJM_AEP_Ohio', 'PJM_Dominion')": … | 2 | (2b) HOURLY measured internal interface limits (ScenarioConfig. pjm… | 2024 | auto-generated |
| `pjm_ordc_curve_path` | /home/user/market-simulator/data/raw/… | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `pjm_seam_flow_percentile` | 90.0 | 2 | PJM analogue: per-(month × hod) percentile of measured per-neighbor… |  | auto-generated, needs-citation |
| `prb_commodity_decline` | 0.015 | 2 | annual, from 2031 as demand falls | 2031 | auto-generated |
| `prb_commodity_flat_through` | 2030 | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `prb_commodity_share` | 0.42 | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `prb_rail_diesel_share` | 0.12 | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `prb_rail_nondiesel_share` | 0.46 | 2 | NEEDS CITATION — no source comment found in code |  | auto-generated, needs-citation |
| `queue_cap_gw.MISO` | 10 | 2 | Annual interconnection queue caps (GW/yr) by ISO. Source: ERCOT CDR… |  | auto-generated, needs-citation |
| `queue_cap_gw.NEISO` | 4 | 2 | Annual interconnection queue caps (GW/yr) by ISO. Source: ERCOT CDR… |  | auto-generated, needs-citation |
| `queue_cap_gw.NYISO` | 4 | 2 | Annual interconnection queue caps (GW/yr) by ISO. Source: ERCOT CDR… |  | auto-generated, needs-citation |
| `queue_cap_gw.PJM` | 10 | 2 | Annual interconnection queue caps (GW/yr) by ISO. Source: ERCOT CDR… |  | auto-generated, needs-citation |
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
| `ra_bridge_econ_min_down_hours` | 4.0 | 2 | Fast-start exclusion for the ECONOMIC (startup-cost) leg of the RA … |  | auto-generated, needs-citation |
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
| `renewable_capacity_credit.solar` | 0.18 | 2 | Capacity credit (ELCC) of variable resources for the planning-reser… |  | auto-generated, needs-citation |
| `renewable_capacity_credit.wind` | 0.16 | 2 | Capacity credit (ELCC) of variable resources for the planning-reser… |  | auto-generated, needs-citation |
| `renewable_capacity_credit_by_iso.ERCOT.solar` | 0.21 | 2 | Per-ISO overrides of RENEWABLE_CAPACITY_CREDIT for the adequacy led… | 2025 | auto-generated |
| `renewable_capacity_credit_by_iso.ERCOT.wind` | 0.2 | 2 | Per-ISO overrides of RENEWABLE_CAPACITY_CREDIT for the adequacy led… | 2025 | auto-generated |
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
| `rggi_member_states_by_year` | {"2023": ["NJ", "VA", "DE", "NH", "NY… | 2 | RGGI member states by year (postal codes). Virginia joined RGGI's C… | 2021 | auto-generated |
| `short_ton_to_metric_tonne` | 0.90718474 | 2 | Short ton -> metric tonne. RGGI allowances are denominated in SHORT… |  | auto-generated, needs-citation |
| `statmode_probe_runs.CAISO` | 2026-07-03-caiso-statmode-d-7 | 2 | Provenance of the fit inputs: the committed D-7 statistical-mode pr… |  | auto-generated, needs-citation |
| `statmode_probe_runs.ERCOT` | 2026-07-04-statmode-d7-probe-ercot32 | 2 | Provenance of the fit inputs: the committed D-7 statistical-mode pr… |  | auto-generated, needs-citation |
| `statmode_probe_runs.MISO` | 2026-07-03-miso-statmode-d-7 | 2 | Provenance of the fit inputs: the committed D-7 statistical-mode pr… |  | auto-generated, needs-citation |
| `statmode_probe_runs.NEISO` | 2026-07-03-neiso-statmode-d-7 | 2 | Provenance of the fit inputs: the committed D-7 statistical-mode pr… |  | auto-generated, needs-citation |
| `statmode_probe_runs.NYISO` | 2026-07-03-nyiso-statmode-d-7 | 2 | Provenance of the fit inputs: the committed D-7 statistical-mode pr… |  | auto-generated, needs-citation |
| `statmode_probe_runs.PJM` | 2026-07-03-pjm-statmode-d-7 | 2 | Provenance of the fit inputs: the committed D-7 statistical-mode pr… |  | auto-generated, needs-citation |
| `structural_prior_convolution_k` | 25 | 2 | Structural draws per parametric draw in the log-space Monte-Carlo p… |  | auto-generated, needs-citation |
| `structural_prior_horizon_lambda` | 0.0 | 2 | Horizon-widening variance multiplier lambda(h), growing with years-… |  | auto-generated, needs-citation |
| `structural_prior_student_t_nu` | 2.0 | 2 | Student-t degrees of freedom for the per-ISO structural-error distr… |  | auto-generated, needs-citation |
| `structural_prior_version` | pb3-statmode-d7-2026-07 | 2 | Version tag stamped into every fitted prior artifact / ensemble_met… |  | auto-generated, needs-citation |
| `weather_year_pool_by_iso.CAISO` | [2019, 2020, 2021, 2023, 2024, 2025] | 2 | Per-ISO weather-year pool (2026-07 widening, docs/handoffs/probabil… | 2026-07 | auto-generated |
| `weather_year_pool_by_iso.ERCOT` | [2019, 2020, 2021, 2023, 2024, 2025] | 2 | Per-ISO weather-year pool (2026-07 widening, docs/handoffs/probabil… | 2026-07 | auto-generated |
| `weather_year_pool_by_iso.MISO` | [2019, 2020, 2021, 2023, 2024, 2025] | 2 | Per-ISO weather-year pool (2026-07 widening, docs/handoffs/probabil… | 2026-07 | auto-generated |
| `weather_year_pool_by_iso.NEISO` | [2019, 2020, 2021, 2023, 2024, 2025] | 2 | Per-ISO weather-year pool (2026-07 widening, docs/handoffs/probabil… | 2026-07 | auto-generated |
| `weather_year_pool_by_iso.NYISO` | [2021, 2023, 2024, 2025] | 2 | Per-ISO weather-year pool (2026-07 widening, docs/handoffs/probabil… | 2026-07 | auto-generated |
| `weather_year_pool_by_iso.PJM` | [2021, 2023, 2024, 2025] | 2 | Per-ISO weather-year pool (2026-07 widening, docs/handoffs/probabil… | 2026-07 | auto-generated |
| `wecc_export_cap_mw` | 2500.0 | 2 | CAISO export capability to WECC (MW). Source: placeholder pending E… |  | auto-generated, needs-citation |
| `wright_reference_gw.compressed_air` | 1.5 | 2 | GW global adiabatic/diabatic CAES — Huntorf, McIntosh, |  | auto-generated, needs-citation |
| `wright_reference_gw.flow_battery` | 3.0 | 2 | GW global installed vanadium-redox flow. Source: PNNL 2023, | 2023 | auto-generated |
| `wright_reference_gw.iron_air` | 1.0 | 2 | was 0.5. DOE LDES. |  | auto-generated, needs-citation |
