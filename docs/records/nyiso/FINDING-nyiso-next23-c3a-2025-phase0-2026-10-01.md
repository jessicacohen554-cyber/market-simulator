# FINDING — NYISO-NEXT-23 phase 0: C3a 2025 is a winter-tail object, and NYISO's daily gas is trade-dated

```
LANE      : NYISO-NEXT-23 (orchestrator, rule 32 (a))
LP        : none. No shard launched. No ScenarioConfig field written. Keeper unchanged.
KEEPER    : 2026-10-01-nyisonext21-astoria-hr-span (+ -2021 stamped)
BASIS     : NEXT-22 zone-resolved C3a/C3b actual (PR #6976). Probes read
            data/raw/_validation-source/actual_lmp_hourly_zonal_NYISO.parquet, which lands with #6976.
PROBES    : scripts/probes/nyisonext23_c3a_tail_split.py, scripts/probes/nyisonext23_flow_date_footprint.py
```

## 1. Level or tail? Tail, plus a winter day-ahead gap

Load-weighted miss against the zone-resolved RT actual (keeper sidecars; ±0.4 pt off the scorer's
rounding):

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| model vs RT | +3.3 % | −1.4 % | +1.8 % | −4.0 % | **−11.6 %** |
| model vs DA | +4.6 % | +2.6 % | +0.3 % | −5.3 % | **−9.1 %** |
| miss in actual-RT deciles 1–8 ($/MWh) | +6.9 | +14.6 | +5.4 | +3.2 | **+3.4** |
| miss in decile 10 ($/MWh) | −5.1 | −13.0 | −4.8 | −4.2 | **−10.0** |
| miss from hours actual > $150 | −2.5 | −13.1 | −2.8 | −2.7 | **−8.8** |

- **2025 is not a broad level gap.** Deciles 1–8 run *high* (+$3.4). Hours above $150 carry
  −$8.8 of the −$8.0 miss. The top 30 days carry −$7.9.
- **Two clusters.** June 23–25 and July heat (−$3.2 from June alone) is a real-time scarcity spike: on
  6/24 the model tracks DA ($176–321 vs DA $189–365), while RT ran $649–2,134. That is the ledgered
  C3c object, and no energy-offer lever reaches it. January–February is different: the model is
  **below DA too** (Jan model $102 vs DA $125; −$2.2 of the −$6.1 DA miss comes from January alone).

## 2. The January gap: the dual-fuel parity cap, fed by a mis-dated gas series

On the cold days (1/17–1/22) the marginal unit is ST_GAS econ at about $206/MWh. That is the parity
cap, `min(gas, oil) × gas HR`, at about $19.9/MMBtu. Available CC is fully loaded and oil generation is
about 0.

**(a) The daily Transco Z6 NY series is placed on its TRADE date and linearly interpolated.**
`hubs._nyiso_hub_daily_gas_prices` keys each EIA print to its trade day and runs `np.interp` across
weekends. The index is next-day delivery, and Friday's trade prices the Sat–Mon(+holiday) package.
This is the convention `_flow_date_staircase` already encodes for CAISO (`caiso_citygate_flow_date`)
and MISO. Measured, MLK weekend 2025:

| date | current factor | flow-date factor | NYC DA $/MWh |
|---|---:|---:|---:|
| Fri 1/17 | **6.03** | 0.23 | 117 |
| Sat 1/18 | 4.95 | 5.04 | 106 |
| Mon 1/20 | 2.78 | 5.04 | 277 |
| Tue 1/21 | 1.70 | 5.04 | 302 |
| Wed 1/22 | 1.08 | 1.42 | 299 |

The $97.90 print (trade 1/17, flow 1/18–1/21) lands on a day whose DA was $117, then decays across
the four days it actually priced.

**Correlation of the daily gas factor with NYC DA daily** (diagnostic only; the case is the source
convention, rule 14):

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| current | 0.29 | 0.30 | 0.18 | 0.38 | 0.24 |
| flow-date staircase | 0.42 | 0.60 | 0.49 | 0.58 | 0.41 |
| winter (J/F/D), current → flow | 0.35→0.51 | 0.30→0.74 | 0.18→0.53 | 0.45→0.70 | 0.33→0.61 |

**New evidence against nyiso-242 §4.2.** That section "refuted" the flow-date defect by shifting the
*whole* series ±k days and keeping the interpolation. A uniform shift is not the convention: it never
spreads the Friday print over its package and never removes the interpolation. The correct
construction improves the fit in **5 of 5** years, not 2 of 4. No matrix cell recorded that
refutation, so this is a first test, not a re-test.

**(b) The parity switch assumes every switch-capable unit switches. Measured conduct says most did not.**
`derive_measured_oil_burn_days.py --iso NYISO` (CAMPD CO2/heat-input identity, zero parameters).
2025 oil share of gas-unit heat input is **1.7 %**. On the generator-days where the model's cap binds:

| zone | MW-wtd measured oil share | share of capped MW burning < 1 % oil |
|---|---:|---:|
| Capital_Hudson | 0.16 | 0.80 |
| NYC | 0.18 | 0.73 |
| Long_Island | 0.43 | 0.41 |

The armed-elsewhere overlay `dual_fuel_measured_oil_burn` (soco-96; NYISO cell **U**) cannot use this
as written. It writes only plant-days with oil share > 0, so a measured 0 % day keeps the parity cap.
It would also price uncovered gas at the model's delivered spot, which on capped January cells averages
**$55.7/MMBtu**, far above anything NYC DA implies (≈ $28–31 at HR 10.5 on 1/20–1/22). Part of that
$55.7 is the mis-dating in (a). **Fix (a) before measuring (b).**

## 3. Routing

1. **LEAD — flow-date the NYISO Transco Z6 daily** (new shared-style flag, default off, zero free
   parameters, reuses `_flow_date_staircase`, keeps the monthly mean-preserving renormalisation).
   Rule 14 on the source convention. Expected to move **timing (C3b)** more than the C3a level,
   because each month's mean is preserved. Stated before any solve: it will **not** by itself close
   C3a 2025.
2. **Then re-measure (b)** on the flow-dated series. If capped MW still mostly burns gas, the parity
   cap is a structural misrepresentation. Possible routes: symmetric measured-mix pricing in backcast,
   or an oil-burn restriction with a forward story. That is an owner decision card, not a session call.
3. **June/July RT scarcity** stays the ledgered C3c object. Note: it now also drives a load-bearing C3a
   fail in 2025.

## 4. Process note

Merging #6976 (NEXT-22) is blocked on doc/status merge conflicts with `main`:
`docs/calibration-log/nyiso.md`, `docs/codebase-site/data/mechanism-matrix/NYISO.js`,
`docs/mechanism-testing-matrix.md`, `docs/rubric-v24-price-basis-memo-2026-07.md`,
`frontend/data/backcast/status/NYISO.js`. Code auto-merges. Every red CI check on #6976 is red on
`main` with an identical failure set (verified locally over the 11 failing test files: 24 = 24).
