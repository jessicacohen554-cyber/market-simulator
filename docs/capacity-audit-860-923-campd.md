# Capacity Audit: EIA-860 / EIA-923 / CAMPD Cross-ISO

**Date:** 2026-06-30  
**Scope:** All 6 backcast ISOs — ERCOT, CAISO, PJM, MISO, NYISO, NEISO  
**Year:** 2023  
**Method:** Compare CAMPD facility-level hourly gross generation (×parasitic factor) against EIA-860 capacity used as the LP's pmax bound.

## Executive Summary

The model's implied capacity (`pmax_mw`) is set from `net_summer_capacity_mw` (EIA-860) for each generator. CAMPD hourly generation exceeds this bound at **~250 plants** across ISOs, concentrated in three root causes:

| Root Cause | Plants | Excess MW | Fix |
|---|---|---|---|
| CC summer derate (nameplate > summer) | 87 | 3,569 | Enable `cc_nameplate_summer_derate` for CAISO/MISO |
| CAMPD data mismatch (retired units, split facilities) | 40 | 8,360 | Not a model bug — CAMPD facility aggregation |
| CT/other summer-only gap | 105 | 1,328 | Known seasonal derate, handled by class derate |
| Cold-weather over-rating (gross > nameplate) | 15 | 205 | CC reconciliation script covers this |

**The actionable finding is #1: the `cc_nameplate_summer_derate` flag is off for CAISO and MISO.** These ISOs' CC fleets carry net-summer capacity year-round, understating winter capacity by 10-28% per plant (33 GW of CC capacity nationally has a 14% mean summer derate).

## How Capacity Flows Through the Model

```
EIA-860 Generator Sheet
  ↓ prefer net_summer_capacity_mw (fleet.py:3154)
  ↓ fallback: nameplate_capacity_mw
  → Generator.pmax_mw
  ↓
  fleet_to_bins() [non-ERCOT]  or  load_campd_bins() [ERCOT]
    └─ If cc_nameplate_summer_derate: CC cap rescaled summer→nameplate
  ↓
  generators_to_fleet_arrays() → FleetArrays
    ├─ Statistical WEFOR/POF/age derate
    ├─ Historic outage overlay (backcast)
    ├─ CC summer derate (per-plant measured ratio, Jun-Sep)
    ├─ AS reserve withholding
    └─ COD ramp
  ↓
  dispatch.py: col_upper = pmax × availability
```

**Key asymmetry:** The model loads `net_summer_capacity_mw` as the base capacity for ALL generators (fleet.py line 3154). For CC plants, this is a hot-weather rating 10-28% below nameplate. Without `cc_nameplate_summer_derate=True`, the LP carries this derated capacity year-round — even in winter when the plant physically runs at full nameplate.

## Per-ISO Findings

### ERCOT
- `cc_nameplate_summer_derate = False` (all keepers)
- 58 plants over model capacity, but **dominated by CAMPD data issues** (12 plants, +2,181 MW excess) and CC summer derate (19 plants, +1,030 MW)
- ERCOT CAMPD bins use `Nameplate_MW` from the curated CSV (fleet.py:5228), so the capacity base is already nameplate — the summer derate issue is less acute here since the bins CSV was hand-curated
- Remaining 25 are CT summer-cap-only gap

### CAISO
- `cc_nameplate_summer_derate = False` (all keepers)
- 30 plants over model capacity
- **4 CC plants** with summer derate (+88 MW excess): Gilroy (22% derate), Los Medanos (18%), Sutter (17%), Metcalf (12%)
- **36 CC plants** have >3% nameplate-to-summer gap totaling 16,944 MW nameplate
- Moss Landing (27% derate, 378 MW gap), Magnolia (22%, 87 MW gap), Sunrise (18%, 124 MW gap) are major
- 10 cold-weather over-rating CTs (+86 MW) — within noise

### PJM
- `cc_nameplate_summer_derate = True` (all recent keepers)
- 44 plants over model capacity, but with nameplate already enabled, the CC issue is largely resolved
- Remaining: 6 CAMPD data mismatches (Indian River retired coal, Elwood co-located units), 19 CT summer-only gap
- **The flag is working correctly for PJM**

### MISO
- `cc_nameplate_summer_derate = False` (all keepers)
- 70 plants over model capacity (40.9%)
- **23 CC plants** with summer derate (+1,195 MW excess)
- Note: MISO/ERCOT state overlap (TX, IL, IN) inflates the count. Many ERCOT plants appear here.
- 53 CC plants have >3% nameplate-to-summer gap totaling 42,240 MW nameplate
- This is the **largest unaddressed CC capacity gap** across ISOs

### NYISO
- `cc_nameplate_summer_derate = True` (all recent keepers)
- 34 plants over model capacity, but many are CAMPD data issues (Astoria Energy 55375 has 4 CAMPD units vs 3 EIA gens)
- **17 CC plants** with summer derate (+486 MW) — these have the flag ON, so the excess is from plants where CAMPD peak exceeds even the nameplate-restored capacity (cold-weather over-rating)
- Sithe Independence (1158 MW NP, 996 MW summer) runs at 1211 MW gross peak in winter

### NEISO
- `cc_nameplate_summer_derate = True` (all recent keepers)
- 14 plants over model capacity
- **7 CC plants** with summer derate (+167 MW)
- Kendall Square (1595) has a genuine CAMPD mismatch: 326 MW gross peak vs 235 MW EIA — possibly co-located or retired units filing under the same ORIS

## Alamitos (Plant 62115) Specific

AES Alamitos Energy Center is a CC plant in CAISO:
- **Nameplate:** 678 MW (CT: 231+231, CA: 216)
- **Summer:** 603 MW (CT: 194+194, CA: 215)
- **Winter:** 678 MW
- **Summer derate:** 11.1%
- **CAMPD peak:** 346 MW gross (est. 329 MW net)
- **Model capacity:** 603 MW (net_summer)

Alamitos's CAMPD peak (346 MW) is well below its summer capacity (603 MW), so it is **not** running at 101% in CAMPD data. The "101% regularly" observation likely refers to the **model's dispatch** exceeding the derated capacity during backcast. The root cause: if the model applies an additional availability derate on top of the already-derated net_summer capacity, the effective bound can drop below what the plant actually produced. With `cc_nameplate_summer_derate=False`, the 603 MW summer capacity is the year-round cap; if shoulder/winter availability is then derated by WEFOR (~5%), the effective cap is ~573 MW — correctly above CAMPD peak but potentially below during peak winter hours if the model's statistical derate is too aggressive.

**For Alamitos to hit 101%, the issue is likely in how availability stacks on top of the summer capacity base.** The fix would be `cc_nameplate_summer_derate=True` for CAISO, which would set winter capacity to 678 MW and summer to 603 MW, giving proper seasonal headroom.

## Root Cause Details

### 1. CC Summer Derate (the actionable fix)

The `cc_nameplate_summer_derate` flag controls whether CC plants use nameplate (winter) or net_summer (year-round) capacity:

- **ON** (PJM, NYISO, NEISO): CC capacity = nameplate, with per-plant measured summer derate applied Jun-Sep
- **OFF** (ERCOT, CAISO, MISO): CC capacity = net_summer year-round

With the flag **OFF**, CC plants lose 10-28% of their winter capacity permanently. This means:
- Winter peak dispatch is capacity-constrained at the summer rating
- CAMPD-observed winter generation routinely exceeds the model's pmax
- The LP dispatches other (more expensive) units instead

**432 CC plants nationally** have >5% nameplate-to-summer gap, totaling **33,186 MW** of capacity that is seasonally unavailable to the model.

### 2. CAMPD Data Mismatches (not a model bug)

40 plants where CAMPD facility-level data grossly exceeds EIA-860 capacity. Root causes:

| Plant | Issue |
|---|---|
| Indian River (594) | Retired coal unit 4 (446 MW) still filing CAMPD in 2023 |
| Elwood (55199) | CAMPD has 9 units (1,575 MW peak) vs EIA 3 GTs (576 MW) — co-located facility |
| Astoria Energy (55375) | CAMPD has 4 CTs vs EIA 3 gens — likely adjacent Astoria units filing under same ORIS |
| Bayswater (55699) | CAMPD has 2 units (120 MW) vs EIA 1 GT (60 MW) |
| Channelview (55187) | CAMPD 4 units peak 310 MW each (~1240 MW) vs EIA 918 MW |
| Linden Cogen (50006) | CAMPD 6 units sum ~1,272 MW vs EIA 974 MW |
| Stony Brook (54149) | CAMPD peak 78 MW vs EIA 47 MW — genuine over-rating |

These are CAMPD-to-EIA mapping issues, not model capacity errors. The model correctly uses EIA-860 capacity per generator.

### 3. CT/ST Summer Capacity Gap

105 plants where the CT/ST summer capacity is below nameplate (typical 10-30% for CTs due to ambient temperature). The model handles this via the `_SUMMER_CLASS_DERATE` constants (10% CC, 12.5-15% CT) applied in `generators_to_fleet_arrays()`. This is working as designed — the small over-capacity is within the derate precision.

### 4. Cold-Weather Over-Rating

15 plants where CAMPD peak net exceeds nameplate by 0-5%. This is the known phenomenon where gas turbines produce more power in cold, dense air. The `derive_cc_capacity_reconcile.py` script handles this for CC plants via the P99.9 demonstrated peak.

## Recommendations

1. **Enable `cc_nameplate_summer_derate=True` for CAISO and MISO.** This is the single largest capacity accuracy fix available. It unlocks ~3,600 MW of winter CC capacity that the model currently leaves on the table.

2. **ERCOT is a special case.** ERCOT CAMPD bins already use `Nameplate_MW`, so the base capacity is nameplate. The flag's effect is only on the per-plant summer derate seasonal shaping, which is less impactful when the bin CSV is already curated.

3. **No action needed on CAMPD data mismatches.** These are CAMPD reporting artifacts (retired units, co-located facilities). The model correctly uses EIA-860 per-generator capacity, not CAMPD facility totals.

4. **Consider CT-specific nameplate-to-summer handling.** 105 CTs are above model capacity due to summer rating. The class derate (12.5-15%) is applied but is imprecise — per-plant measured derates (like the CC approach) would be more accurate.

## Script

Audit script: `scripts/archive/audit_capacity_vs_campd.py`  
Usage: `python scripts/archive/audit_capacity_vs_campd.py --year 2023 [--iso CAISO]`
