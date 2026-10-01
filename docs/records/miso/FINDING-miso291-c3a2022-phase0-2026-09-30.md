# FINDING — miso-291: C3a 2022 is mostly Indiana-hub congestion the copper-plate model cannot carry. No admissible un-adjudicated lever. No solve.

```
LANE    : miso-291 (owner ruling "Close coal line; C3a 2022 (Recommended)", miso-290 §7)
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), unchanged
LP      : none (committed hourly sidecars, published MISO hub components, one fleet_only rebuild)
PROBE   : scripts/probes/_miso291_c3a2022_decomp.py (main; dispatch_identity; gas_vs_hub)
OUTPUTS : results/calibration/_miso291_{c3a2022_decomp,dispatch_identity,gas_vs_hub_2022}.json
CELLS   : no verdict moves (every candidate already adjudicated)
```

## 1. Answer

The probe reproduces the scored number exactly: model **59.98** vs INDIANA.HUB RT **71.01**, Jan–Oct
(the scorer's coverage mask), **−15.5 %**. Of the −11.03 $/MWh gap:

| piece | $/MWh | status |
|---|---:|---|
| Indiana congestion + losses (MCC 5.84 + MLC 2.63) | **−8.47** | 2023–25 run at −2.3 to −2.5. The model is a copper plate across the Midwest. `internal_congestion_split` **G**, `measured_interface_limits` **R**, no 2022 limit data (miso-277). |
| energy (model − MEC), equal-hour | −4.02 | see §3 |
| scorer load-weight term (model load-weighted, actual equal-hour) | +1.45 | basis defect, §4 |

**If Indiana congestion were at its 2023–25 level, 2022 would read −7.7 % and PASS** on the current
basis. On the consistent load-weighted basis (§4) it would still fail at −12.0 %.

## 2. The comparator is the outlier, not the energy price

Hub congestion + losses, Jan–Oct 2022 ($/MWh, published components):

| MINN | ILLINOIS | **INDIANA** | MICHIGAN | ARKANSAS |
|---:|---:|---:|---:|---:|
| −17.17 | +0.85 | **+8.47** | +4.15 | −3.07 |

C3a scores against one hub, and in 2022 that hub sat $8.47 above MISO's system energy price. The SOM
attributes the 2022 congestion to wind-loaded constraints, overlapping outages and line ratings, all at
facility level (miso-277 §1). A zonal limit tuned to reproduce it is forbidden (rules 1, 13).

## 3. The energy part (model − MEC), by band and hour

Additive contributions to the equal-hour gap vs MEC (bands of actual Indiana RT):

| year | p0–50 | p50–75 | p75–90 | p90–95 | p95–99 | p99+ | net |
|---|---:|---:|---:|---:|---:|---:|---:|
| **2022** | +4.95 | −0.25 | −2.07 | −1.60 | −2.62 | −2.43 | **−4.02** |
| 2023 | +3.82 | +1.40 | +0.21 | −0.34 | −0.98 | −1.34 | +2.77 |
| 2024 | +3.39 | +1.29 | 0.00 | −0.58 | −1.24 | −1.62 | +1.26 |
| 2025 | +4.51 | +1.73 | −0.06 | −0.85 | −2.24 | −3.08 | +0.01 |

| 2022 hour group | contribution | mean model − MEC |
|---|---:|---:|
| night h0–5 | +1.61 | +6.42 |
| day h7–14 | −2.62 | −7.86 |
| evening h15–20 | **−3.50** | **−14.01** |

- **Lower half over-priced (+4.95):** the night overshoot. 2022's part is the coal-budget dual (miso-287),
  now accepted; coal line CLOSED by owner.
- **p75–p99 shoulder (−6.29) and p99+ tail (−2.43):** day/evening under-pricing. Actual has 260 hours
  above $150; the model has none (max $98.59). Tail = C3c overlap, `ordc_scarcity_overlay` **G**.
- **2022-specific shoulder:** the real fleet priced coal scarcity as an opportunity-cost offer adder on
  11–22 GW (IMM 2022 SOM, miso-288). That is the coal line, now closed.

## 4. A basis defect found on the way (reported, not fixed)

2019 and 2022 are the only MISO years scored on the **legacy equal-hour** basis: `lw_retrofit` in
`scripts/data/derive_actual_lmp.py` was never re-run after those years were intaken (miso-251/252). My
reconstruction reproduces the committed `rt_lw` to the cent in all five other years.

| year | equal-hour (scored) | load-weighted (consistent) |
|---|---:|---:|
| 2019 | +5.7 % | +2.8 % |
| **2022** | **−15.5 %** | **−19.5 %** |

No status flips either way. Repairing it means regenerating bench parts, which miso-266 found moves other
actuals, so this goes to the owner.

## 5. Ruled out

| candidate | result |
|---|---|
| Gas level | Model North gas is **above** the Chicago hub in 2022 (Indiana +$0.56, Illinois +$1.30, West +$1.10/MMBtu, annual). Gas pushes price **up**. |
| Dispatch mix | Model gas under EIA-930 by 13–19 % in day hours in **every** year, 2023–25 included; coal +7 % day in 2022 vs +1–4 % other years. Not 2022-specific enough to be the object. |
| Offer multipliers | One config across all years (rule 1). 2023–25 energy sits at or above MEC; a lift would break train years. A 2022-only fix is forbidden. |
| Congestion | `internal_congestion_split` G, `measured_interface_limits` R; MISO binding-constraint history 404 for 2021–22. |
| Tail | `ordc_scarcity_overlay` G. |
| Night / coal | `diurnal_price_amplitude` G; coal budget-grain line closed (owner, 2026-09-30). |

## 6. Where MISO stands

Keeper unchanged. Train 2023–2025 CALIBRATED (C3c ledgered). Full span **NOT-YET** on three routed misses:
C1 ST_GAS 2019, C3a 2022, C3b 2021. **No frontier.** The only structural route left for C3a 2022 is an
owner-chartered reduced-network (flowgate) program, the miso-277 route.

## 7. Owner ruling (2026-09-30)

*"Repair basis (Recommended)"* and *"Charter flowgate program"*. Next lane (miso-292): (1) re-run the
load-weighted C3a basis (`lw_retrofit`) for MISO 2019/2022 only, verifying no other bench field moves
(miso-266 hazard); (2) zero-LP charter of a reduced-network (flowgate) program for MISO's internal
congestion: data plan, admissible limit sources, forward story, kill rule — no tuned limits (rules 1, 13).
