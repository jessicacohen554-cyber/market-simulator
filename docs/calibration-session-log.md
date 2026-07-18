# Calibration Session Log — ERCOT 2023

> **Historical snapshot (2026-05-17).** This is the *first* ERCOT calibration
> session and is preserved as-is for the record. Several conclusions here have
> since been overtaken — notably the "Gas CT gap cannot be resolved without
> unit commitment": the opt-in commitment layer (methodology spec §1.6) and
> CAMPD per-plant binning (§3.3) were subsequently built to address exactly
> this. For current calibration state see the "run14"–"run24" bundles in
> `results/calibration/` (render with `/calibration-report`). Do not read the
> forward-looking statements below as current methodology.

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
-----

## PJM backcast tuning — 2023, 2024 (+2025 informational), n=6 smooth offer curve

**Date:** 2026-06-09. **Scope:** Calibrate the PJM thermal offer curve (the
per-class `offer_curve_by_group` heat-rate-multiplier bands rendered as the
n=6 smooth economic ramp) against the 2023 & 2024 EIA-930 fuel mix and the PJM
hub-average LMP, mirroring the ERCOT plant-classification workflow (per-plant
EIA-860 fleet, supply-class coal BIT/SUB/WC, per-plant EIA-923 fuel cost, CAMPD
unit-outage overlay). Result baked into `run_calibration._PJM_OFFER_CURVE`.

**Unit outages:** regenerated `campd-unit-outages-PJM.csv` to cover 2023, 2024
and 2025 (`derive_campd_unit_outages.py --iso PJM`). 2023 now derates 741
plant-tranches (was 0 — 2023 had no unit-outage rows before). 2025 derates 337
once the KY/OH/VA/WV/IN/DC 2025 unit-level CAMPD extracts are present; IL/NJ/PA
2025 extracts are still missing from the repo, so 2025 outage coverage is
partial.

**Method (two stages, per the operator's framing):**
1. SHAPE — relative band multipliers set the generation mix. Landed CC/CT/ST
   split and coal-vs-gas: raised CT to cut a +25-30% CT overrun, lowered ST to
   fix a −20-40% ST shortfall, trimmed CC econ to pull 2023 coal down.
2. LEVEL — scaled every band by a single global factor (~0.72) to drop the
   cleared LMP from ~+50% to within ~+8-16% of the PJM hub average while
   holding the mix ratio fixed, and capped the CT scarcity (`peak`) band at 4.0
   (the ERCOT-style 13x wall was inflating the high-price tail — operator hint).

**Converged result (vs EIA-923 ref; dashboard tol ±3% OR ±1 TWh, "ok" ≤6%):**

| class   | 2023 err | 2024 err |
|---------|----------|----------|
| coal    | +4.1% ok (≈0% vs EIA-930) | −3.9% ok |
| gas_cc  | +3.0% ✓  | +5.4% ok |
| gas_ct  | +2.0% ✓  | −2.0% ✓  |
| gas_st  |  0.0% ✓  | −20.5% ⚠ |
| nuclear/wind/solar | ✓/ok/✓ | ✓/✓/⚠(BTM) |
| **LMP (load-wtd)** | $32.9 vs RT $28.4 (+16%) / DA $29.3 (+12%) | $31.8 vs RT $29.5 (+8%) / DA $29.8 (+7%) |

2025 (informational; EIA-923 incomplete so mix not a valid test): gas_cc +4.9%,
gas_ct +34.6%, nuclear +0.8%; coal/wind large vs the incomplete 923 benchmark;
**load-weighted LMP $41.7 vs actual RT $42.9 (−3%)** — the meaningful 2025 check,
and it lands once the 2025 unit outages are applied (coal 194→171 TWh, LMP
−22%→−3%).

**Known residuals a single static curve cannot remove (flagged):**
- *2024 gas-steam −20%*: the model's economic gas-steam falls as 2024 gas
  cheapens, but the EIA-923 actual rises — a gas-price-year effect (the same
  reason 2023 coal sits high). 2023 gas-steam is exact; one committed band can't
  satisfy both years. A gas-keyed gas-steam/coal passthrough (à la the ERCOT PRB
  sigmoid) would be needed.
- *Grid solar −10 to −15%*: PJM distributed/BTM solar never reaches the
  wholesale grid the LP dispatches; the gap is a benchmark-scope issue, not an
  offer-curve knob.
- *LMP residual +8-16%*: floored by PJM delivered gas (~$3.21/MMBtu = Henry Hub
  + the EIA-923 +0.67 basis) × realistic CC heat rates; closing it fully would
  need an unphysical scale or a gas-cost change, neither warranted.

-----

## ERCOT runs 73-76 — CHP steam floors, Petra Nova, CT/ST seesaw (2026-06-11)

**Baseline Run-72; bundles in `results/calibration/Run-73..76`; dashboard keeps 74/75/76.**

**Structural fixes (Run-73, in `src/market_sim/data/fleet.py`):**

1. *CHP steam-floor clipping.* The steam-following grid floor (`chp_grid_pmin_mw`) was
   pinned entirely on the FIRST n=6 econ smoothing slice, then clipped to that slice's
   pmax x availability — Sweeny's intended 185 MW floor collapsed to ~48 MW, Bayou's
   104 -> ~20 MW, Deer Park's 258 / Baytown's 171 MW similarly. Floors now spread across
   econ slices in fill order. Sweeny grid LP 497 -> 1,451 GWh, Bayou 244 -> 827. This was
   the "missing steam obligation component": the data was never missing — the floor was.
   (The plants' EIA-923 "OTHER" rows are refinery off-gas burned in the same turbines,
   already injected exogenously as OTHER must-run; no double count.)
2. *Petra Nova (58378) classified on its own.* Outage windows WERE applied (the facility
   overlay covers CT_CHP); the miss was price-following when on. Now a single tranche at
   net-of-capture-parasitic capacity (40%, measured: 1 - 923net/CAMPD = 39.8%/40.9% in
   2023/24) forced to 92% CF whenever available (45Q makes it price-insensitive).
   Model 99/184/190 GWh vs 923's 109/201/(no 2025 data).

**Curve walk (resolved multipliers, run57-base deltas in each run_config.json):**

| run | move | outcome |
|---|---|---|
| 73 | user-directed: CT_PEAKER committed 1.30->1.10 econ_high 2.08->2.18; ST_GAS peak 4.2->3.2; COAL_PRB 0.65/0.40/1.38/1.505; CC_REGULAR -0.05 all bands; + structural fixes | PRB 2024 -15.5->-12.5; CT overshot +18/+10/+12; ST collapsed -8/-19/-18 (displaced by cheap CTs + 3.5 TWh forced CHP floor energy) |
| 74 | CT committed walk-back 1.10->1.22; lignite 0.88/0.92 | CT lands +1.0/-12.5/-5.9; ST still -4.7/-15.6/-12.4 |
| 75 | ST_GAS cheapened 0.60/1.02/1.50 | ST recovers +4.5/-6.7/-2.8; CT slides -4.0/-17.5/-11.0 — CT/ST committed-band seesaw confirmed (~1.5 TWh/unit, matches the Jacobian tool's coupling) |
| 76 | seesaw split: CT committed 1.22->1.16, ST held | **both land**: CT +3.9/-7.7/-3.0, ST +2.8/-8.6/-5.3, CC_REGULAR +1.9% in 2024, PRB 2024 -13.1 |

**Run-76 vs Run-72 baseline:** CT_PEAKER 2024 -15.5 -> -7.7, COAL_PRB 2024 -15.5 -> -13.1,
CC_REGULAR 2024 +3.0 -> +1.9, CHP plant-level hourly shape massively better (Sweeny/Bayou/
Deer Park/Baytown floors real, Petra Nova on its outage windows). Costs: CC_REGULAR 2023
-3.7 -> -4.7 (the forced CHP grid energy squeezes the CC residual; the -0.05 band cut did
not offset it in 2023).

**Known residuals a static curve cannot remove:** (1) lignite/PRB/CT 2024 under-runs are
the cheap-gas-year asymmetry ($2.19 vs $2.54/$3.52) — a gas-keyed band (a la the retired
PRB sigmoid) is the structural fix; (2) CT_CHP 2025 +31% is 2025 EIA-923 incompleteness
(ST_CHP shows +4,900% on the same benchmark) — mask 2025 CHP targets before trusting any
solver move against them; (3) next step: run the Jacobian joint-move solver
(`scripts/data/derive_offer_curve_jacobian.py --validate-run Run-76`) instead of further manual
seesaw steps; consider its CC_REGULAR econ_high-down/peak-up band reshape for the 2023 CC
under-run.

**Data note:** Run-74+ include the regenerated unit-outage nameplates (Rio Nogales units
189->223.5 MW, C.R. Wing 77.5->84.9; windows unchanged — ERCOT otherwise unaffected by the
2026-06-10 multi-ISO outage regeneration).

-----

## ERCOT Run-77 — gas_monthly_actuals backport experiment: REJECTED (2026-06-11)

**Question:** does the PJM 2026-06 measured EIA-923 ISO-month gas pricing
(`gas_monthly_actuals`), backported to the ERCOT backcast, close the 2024 coal
under-run (PRB −13.1%) before touching `coal_prb_passthrough`?
**Bundles:** `results/calibration/Run-77-gasact-2023/-2024` — exact Run-76 config +
`--gas-monthly-actuals` (config diff verified: that one flag only). 2025 not re-run.

**Answer: no — the gap doesn't close, it blows through zero into a larger overshoot,
and 2023 breaks tolerance.** Run-76 → Run-77, diff % vs EIA-923:

| class | 2023 | 2024 |
|---|---|---|
| COAL_PRB | +2.7 → **+23.3** | −13.1 → **+17.2** |
| COAL_LIGNITE | −4.8 → **+10.3** | −17.7 → +5.0 |
| CC_REGULAR | −4.7 → **−10.4** | +1.9 → −5.6 |
| CT_PEAKER | +3.9 → −2.6 | −7.7 → **−21.3** |
| ST_GAS | +2.8 → −2.3 | −8.6 → **−18.8** |

Coal hourly *shape* also degrades (2024 Pearson 0.901 → 0.795, NRMSE 0.229 → 0.271):
this is not an overshoot of the right signal.

**Why (data misalignment, the documented rule-13 exception):** ERCOT's EIA-923
Schedule-5 gas receipts cover only ~20% of burn (20–23 plants), skewed to
muni/co-op/regulated reporters whose *delivered contract* cost embeds firm transport
and distribution adders. The volume-weighted ISO-month series runs ~+$1/MMBtu above
the merchant-hub level the (non-reporting, ~80%) merchant fleet actually pays
(2023: measured avg ~$3.0 vs $2.04 delivered HH+basis; 2024: ~$2.7 vs $1.69). At ERCOT
heat rates that flips the gas-CC/coal merit order in most months. PJM's reporter sample
was representative of its hub; ERCOT's is not — the measured series is on a different
cost boundary than the marginal hub price our gas offer model needs.

**What survives:** the 2024 coal under-run *is* gas-price-sensitive (raising gas
swings PRB 2024 by +30 pp), confirming the cheap-gas-year-asymmetry diagnosis. The
measured monthly *shape* is also real (Jan-2024 winter event: $4.45 measured vs $1.94
generic shape). A reconciled variant — measured month shape renormalized to the trusted
annual HH+basis level — is the candidate structural fix to evaluate before any
`coal_prb_passthrough` retune; the raw level swap is rejected. `gas_monthly_actuals`
stays off for ERCOT (Run-76 remains the baseline); PJM unchanged (flag was already
opt-in per ISO run).
