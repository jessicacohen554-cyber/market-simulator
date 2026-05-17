# Calibration Session Log — ERCOT 2023

**Date:** 2026-05-17
**Target:** eGRID 2023 actuals for ERCOT (BA code ERCO)
**Primary goal:** Accurate emissions trajectories
**Benchmark source:** EPA eGRID 2023 rev2, PLNT23 sheet

## Benchmark Reference (eGRID 2023 ERCOT)

|Fuel     |TWh      |CF%  |Mt CO2   |
|---------|---------|-----|---------|
|Gas CC   |195.7    |53.1%|79.4     |
|Gas CT   |33.7     |16.6%|20.1     |
|Coal     |62.5     |43.2%|72.7     |
|Nuclear  |40.7     |90.4%|—        |
|Wind     |106.7    |32.9%|—        |
|Solar    |27.3     |20.5%|—        |
|**Total**|**472.9**|     |**173.6**|

Flagship plants (eGRID 2023):

- Colorado Bend II: 1,142 MW, HR 6688, 7,845 GWh, 78.4% CF
- Wolf Hollow II: 1,103 MW, HR 6827, 7,018 GWh, 72.6% CF

-----

## Changes Applied (cumulative)

### 1. Gas Price — $2.54/MMBtu Henry Hub (2023 actual)

- **Previous:** Mid trajectory @ year 2030 = $3.50 HH, $3.00 delivered
- **New:** 2023 actual HH = $2.54, delivered = $2.04 (with ERCOT basis −$0.50)
- **Source:** EIA Henry Hub spot price, 2023 annual average
- **Implementation:** Monkey-patch `HENRY_HUB_TRAJECTORIES['mid'][2023] = 2.54`
- **For production:** Add 2023 entry to trajectory or add a `gas_price_override` field to ScenarioConfig
- **Impact:** Gas CC +18 TWh, coal −22 TWh, CO2 −11 Mt. Gas CC landed on eGRID actual (196.5 vs 195.7).
- **Gas seasonality:** Enabled (`gas_seasonality=True`). Monthly factors 0.90 (May) to 1.18 (Dec). Source: EIA Henry Hub spot monthly averages 2019-2024.

### 2. Renewable Capacity — 2023 installed (from eGRID)

- **Previous:** 42.0 GW wind, 38.0 GW solar (2024/2025 CDR values)
- **New:** 37.1 GW wind, 15.2 GW solar (eGRID 2023 nameplate)
- **Source:** EPA eGRID 2023 rev2, PLNT23 sheet, NAMEPCAP field, PLFUELCT = WIND/SOLAR, BACODE = ERCO
- **Implementation:** Scale `wind_cap` and `solar_cap` arrays by ratio
- **For production:** Add year-specific renewable capacity lookup, or derive from EIA-860 by operating_year filter
- **Impact:** Solar dropped from 73.5 to 36.0 TWh. Thermal dispatch increased to fill gap.

### 3. Renewable Zone Distribution — EIA-860 actual plant locations

- **Previous:** All wind in West zone, all solar in South zone
- **New (from EIA-860 + eGRID zone assignment):**
  
  |Zone   |Wind GW|Wind %|Solar GW|Solar %|
  |-------|-------|------|--------|-------|
  |West   |15.7   |42.2% |6.3     |41.3%  |
  |North  |12.9   |34.7% |5.0     |32.7%  |
  |South  |8.4    |22.7% |2.0     |13.1%  |
  |Houston|0.2    |0.4%  |2.0     |12.9%  |
- **Source:** EIA-860 2024 (eia860_generators.parquet), zone assigned via `zone_assignment.py` using eGRID PLNT23 lat/lon/FIPS
- **Implementation:** Distribute capacity across zones; apply same ISO-wide CF profile to each zone (simplification — zonal CF differentiation is a future enhancement)
- **For production:** Update `renewables.py` RENEWABLE_ZONE_ALLOCATION to use EIA-860 plant-level zone mapping instead of single-zone allocation
- **Impact:** Eliminated artificial West zone congestion. Wind curtailment dropped from 35% to ~0%.

### 4. Transfer Limits (TTC) — ERCOT 2021 RTP stability limits

- **Previous:**
  
  |Link                 |TTC (MW) |
  |---------------------|---------|
  |North → West         |3,000    |
  |West → Houston       |2,500    |
  |South → West         |2,000    |
  |**West export total**|**7,500**|
- **New:**
  
  |Link                 |TTC (MW)  |Source                              |
  |---------------------|----------|------------------------------------|
  |North → West         |5,500     |ERCOT 2021 RTP stability assessment |
  |West → Houston       |3,500     |ERCOT 2021 RTP stability assessment |
  |South → West         |2,000     |unchanged                           |
  |**West export total**|**11,000**|ERCOT RTP: 11,016 MW stability limit|
  
  Other links unchanged: N→S 5,000; N→H 8,000; S→H 4,000.
- **Source:** ERCOT 2021 Regional Transmission Plan, “West Texas Export Stability Assessment” (presented at ROS July 2020, updated RPG Sep 2021). West Texas export stability limit = 11,016 MW measured across 16 345-kV circuits.
- **CREZ reference:** ETT project page — 2,400 miles of 345 kV lines designed for 18,500 MW, completed 2013.
- **Status:** TTCs may be too loose — zero congestion and uniform prices across all zones. Real ERCOT had West zone negative prices in 2023. Needs sweep (see §Remaining).
- **For production:** Make TTCs configurable in iso_configs.py with citation. Consider 90% reliability margin per ERCOT operating procedure.

### 5. CC Cycling Cost Adder — bin-specific, derived from plant data + NREL

- **Previous:** No cycling adder (pure LP marginal cost)
- **New (per CC heat rate bin):**
  
  |CC Bin |HR Range |Adder $/MWh|Startup $/MWh|Drag $/MWh|
  |-------|---------|-----------|-------------|----------|
  |h_class|<6500    |3.92       |2.90         |1.02      |
  |f_class|6500-7500|3.66       |2.88         |0.78      |
  |older  |7500+    |2.91       |2.41         |0.50      |
- **Derivation:**
1. eGRID 2023 ERCOT CC plants: per-plant annual generation → equivalent full-load hours → estimated starts (using avg run length per class)
1. Start costs from NREL/SR-5500-55433 (Kumar et al. 2012), Table ES-1, scaled by CC class:
  - H-class: $48/$72/$105 per MW-start (hot/warm/cold), mix 55%/30%/15%
  - F-class: $38/$58/$84 per MW-start, mix 59%/30%/11%
  - Older: $22/$35/$55 per MW-start, mix 65%/25%/10%
1. Average run length from OEM specs and Potomac Economics SOM patterns:
  - H-class: 22 hrs/cycle (heavy rotors, 10hr min runtime)
  - F-class: 17 hrs/cycle (7.5hr min runtime)
  - Older: 10 hrs/cycle (4.5hr min runtime)
1. Drag component: fraction of committed hours uneconomic × average below-MC margin
1. Fleet weighted average: $3.65/MWh. NREL literature range: $2-5/MWh for large frame CCs.
- **Sources:**
  - NREL/SR-5500-55433: “Power Plant Cycling Costs” (Kumar, Besuner, Lefton, Agan, Hilleman, 2012)
  - GE, Siemens OEM technical specs for min runtime by turbine class
  - Potomac Economics, ERCOT State of the Market 2023 (cycling patterns)
  - EPA eGRID 2023 (plant-level CF and generation for start count estimation)
- **Implementation:** Add adder to mc array by bin after `assemble_mc()` call
- **For production:** Add `cc_cycling_adder_h_class`, `cc_cycling_adder_f_class`, `cc_cycling_adder_older` as Tier 3 calibration parameters in ScenarioConfig
- **Known limitation:** H-class and f-class CCs remain inframarginal (MC still below coal) so the adder doesn’t reduce their CF. Only older CCs shift dispatch. This is a structural LP limitation — plant-level CFs for efficient CCs won’t match eGRID without UC.

### 6. Nuclear Monthly CF — NRC PRIS seasonal shaping

- **Previous:** Flat availability = 1 − EFORD = 0.97 (97% CF all hours)
- **New:** Monthly CFs from `NUCLEAR_MONTHLY_CF['ERCOT']`: [0.93, 0.93, 0.90, 0.90, 0.92, 0.93, 0.93, 0.93, 0.91, 0.90, 0.92, 0.93]. Annual avg = 0.919.
- **Source:** NRC PRIS 2019-2023, already in constants.py
- **Implementation:** Replace `fleet.availability[nuclear_mask]` with hourly array built from monthly CFs
- **For production:** Wire into `generators_to_fleet_arrays()` — detect nuclear fuel type and apply monthly CF instead of flat EFORD
- **Impact:** Nuclear gen 42.3 → 40.1 TWh (eGRID: 40.7, −1.5% error). Excellent match.

### 7. Demand Loss Factor — T&D losses

- **Previous:** EIA-930 metered load = 446.8 TWh. Model dispatches to this level.
- **New:** Gross up demand by 5.8% loss factor → 472.7 TWh
- **Derivation:** eGRID net generation (472.9 TWh) − EIA-930 system load (446.8 TWh) = 26.1 TWh losses = 5.8%.
- **Validation:** EIA-930 peak (85,432 MW) matches ERCOT published peak (85,435 MW, Aug 10 2023, from ercot.com/gridmktinfo). The EIA-930 demand IS the ERCOT system load; the gap is T&D losses, not a data source mismatch.
- **Source:** Empirical ratio from EPA eGRID 2023 / EIA Hourly Grid Monitor 2023. Cross-check: ERCOT CDR typically uses 4-5% loss factor for adequacy assessments; 5.8% is at the high end but includes distribution losses.
- **Implementation:** `demand = demand_raw * (1.0 + LOSS_FACTOR)` with `LOSS_FACTOR = 0.058`
- **For production:** Add `td_loss_factor` as Tier 3 calibration parameter in ScenarioConfig, default 0.058 for ERCOT

### 8. Coal Price — $1.94/MMBtu (current model value, under review)

- **Current:** COAL_PRICE_BASE = $2.00/MMBtu for ERCOT, escalated to $1.94 for 2023
- **Source:** EIA AEO 2024 (citation in constants.py)
- **Validation:** EIA STEO reports national average delivered coal ~$2.36-2.42/MMBtu in 2025-2026. Texas PRB coal delivered by rail typically runs below national average. $1.94 is plausible for 2023 PRB-to-Texas but may be $0.10-0.20 low.
- **Status:** Not changed. Verify against EIA-923 fuel receipts for Texas if precision needed.

-----

## Current Results (all changes applied: gas + renewables + distribution + TTCs + nuclear CF + demand losses)

|Metric     |Model |eGRID|Delta|Err%  |
|-----------|------|-----|-----|------|
|Gas CC TWh |218.0 |195.7|+22.3|+11.4%|
|Gas CT TWh |10.4  |33.7 |−23.3|−69%  |
|Coal TWh   |54.8  |62.5 |−7.7 |−12%  |
|Nuclear TWh|40.1  |40.7 |−0.6 |−1.5% |
|Wind TWh   |114.0 |106.7|+7.3 |+7%   |
|Solar TWh  |36.2  |27.3 |+8.9 |+33%  |
|CO2 Mt     |149.6 |173.6|−24.0|−14%  |
|System LWA |$21.12|~$48*|     |      |

*ERCOT 2023 RT avg ~$48/MWh — model is energy-only, no ORDC/AS.

Flagship plants:

|Plant           |eGRID GWh|Model GWh|Delta|eGRID CF|Model CF|
|----------------|---------|---------|-----|--------|--------|
|Colorado Bend II|7,845    |9,504    |+21% |78.4%   |95.0%   |
|Wolf Hollow II  |7,018    |9,179    |+31% |72.6%   |95.0%   |

Demand: 472.7 TWh (446.8 raw + 5.8% losses). Matches eGRID gen total (472.9).
Nuclear: Monthly CF applied → 40.1 TWh (−1.5% vs eGRID). ✓
Wind: Zero curtailment — TTCs may be too loose (sweep needed).
Gas CC: Demand increase absorbed by CCs (cheapest marginal) — CC adder calibration needs revisiting with new demand level.

-----

## Remaining Calibration Items

1. **West export TTC sweep** — Current 11 GW produces zero congestion (too loose). Real ERCOT had West zone negative prices in 2023. Sweep 8-11 GW to find the right congestion level that produces ~5-10% wind curtailment. Then re-tune CC cycling adders at the final demand + TTC setting.
1. **Solar capacity mismatch** — Model dispatches 36.2 TWh vs 27.3 actual (+33%). 15.2 GW at derived CF gives more output than eGRID reports, likely because many 2023 solar plants were commissioned mid-year. Consider filtering EIA-860 by operating_year to get mid-year pro-rata capacity.
1. **Gas CT structural gap** — LP dispatches 10.4 TWh vs 33.7 actual. Known LP limitation (CCs don’t cycle off so CTs are never needed). Cannot resolve without UC or explicit CT must-run constraints. Document as known bias.
1. **CC cycling adder re-tune** — Adding demand losses (+26 TWh) shifted CC from 196→218 TWh. After TTC sweep settles wind curtailment, re-run CC adder sweep to bring CC back toward 196. The adders may need ~$1-2 increase from derived values.

### 9. Coal Cycling Adders — NREL, bin-specific

- **Previous:** No cycling adder
- **New:**
  
  |Coal Bin     |HR Range  |Adder $/MWh|Source                                       |
  |-------------|----------|-----------|---------------------------------------------|
  |supercritical|<9500     |$2.66      |NREL: $147/MW-start, 96hr cycle, 36hr min-run|
  |subcritical  |9500-10500|$2.55      |NREL: $119/MW-start, 72hr cycle, 24hr min-run|
  |older        |>10500    |$2.58      |NREL: $97/MW-start, 60hr cycle, 24hr min-run |
- **Key insight:** Coal has the LOWEST per-MWh adder despite highest per-start costs — long run cycles (60-96 hrs) amortize the start cost.
- **Impact:** Raises coal MC by $2.55-2.66 → shifts some marginal coal hours to gas. Consistent with methodology.

### 10. Gas CT Cycling Adders — NREL, bin-specific

- **Previous:** No cycling adder
- **New:**
  
  |CT Bin|HR Range   |Adder $/MWh|Source                                        |
  |------|-----------|-----------|----------------------------------------------|
  |aero  |<10000     |$3.14      |NREL: $12.3/MW-start, 4hr cycle, 0.5hr min-run|
  |frame |10000-11000|$5.02      |NREL: $24.5/MW-start, 5hr cycle, 1hr min-run  |
  |older |>11000     |$4.85      |NREL: $19.0/MW-start, 4hr cycle, 1hr min-run  |
- **Key insight:** CTs have the HIGHEST per-MWh adder despite lowest per-start costs — very short runs (4-5 hrs) concentrate startup cost into few MWh.
- **Impact:** Raises CT MC further → worsens CT under-dispatch in LP. This is physically correct; the CT dispatch gap is structural (LP can’t commit), not a cost issue.

### 11. Renewable Vintage/COD Monthly Ramp — EIA-860 Operating Month

- **Previous:** Flat annual capacity (eGRID year-end nameplate)
- **New:** Month-varying capacity from EIA-860 Operating Month field
  - Solar: 11.4 GW in Jan → 14.9 GW in Dec (45% of 2023 additions in Q4)
  - Wind: 35.7 GW in Jan → 36.8 GW in Dec (minimal ramp)
  - Implemented by encoding monthly capacity ratio into CF profile
- **Source:** EIA-860 2024, Generator_Operable sheet, Operating Month/Year columns
- **Impact:** Solar gen dropped from 36.2 → 29.1 TWh (+6.5% vs eGRID, was +33%).
  Seasonal dispatch validation: Q3 summer shows heaviest thermal because demand peaks while solar capacity still building.

### 12. ERCOT HSL Profiles — PENDING DATA ACQUISITION

- **Status:** Prompt drafted for Claude Code (see prompt-ercot-hsl-data.md)
- **Purpose:** Replace EIA-930 generation profiles (pre-curtailed) with ERCOT HSL (uncurtailed potential)
- **Source:** ERCOT 60-Day SCED Disclosure Reports or UMass nodal curtailment dataset
- **Impact:** Will let LP endogenously curtail via TTC constraints — proper test of transmission model