# FINDING — miso-277: phase 0 on the three open MISO objects. No lever earns a solve on C3a 2022; the declined D1 arm was mis-built for MISO-South; the CAMPD–EIA crosswalk is intaken.

```
LANE    : miso-277 (MISO lever queue §5.4; routed by FINDING-miso276 §5)
KEEPER  : 2026-09-26-miso-275-cc-exempt (results/calibration/miso275_span) — unchanged
LP      : none (zero-LP phase 0)
PROBES  : scripts/probes/_miso277_c3a2022_congestion.py     -> results/calibration/_miso277_c3a2022_congestion.json
          scripts/probes/_miso277_storm_print_conventions.py -> results/calibration/_miso277_storm_print_conventions.json
          scripts/probes/_miso277_crosswalk_footprint.py     -> results/calibration/_miso277_crosswalk_footprint.json
CODE    : src/market_sim/data/fuel/basis/miso.py::_miso_zone_hub_kind (bug fix, default-off paths only)
DATA    : DATA PROFILE: miso
```

## 1. C3a 2022: the West→East spread is real congestion, the model is a copper plate, and no admissible limit exists

**Where it is (Jan–Oct 2022, RT, the scorer's mask).**

| hub | actual $/MWh | model |
|---|---:|---:|
| West (MINN) | 45.4 | 56.64 in every Midwest zone |
| Illinois | 63.4 | 56.64 |
| Indiana | 71.0 | 56.64 |
| East | 66.7 | 56.64 |
| South | 61.4 | separates via RDT only |

- The step is **West vs everything east of it** (West−Illinois −18.0; Illinois−Indiana −7.6).
- Indiana−West: **25.64 actual vs 0.00 model**. Other years 0.75–5.03.
- Hours with |West−Indiana| > $10: **68.7 %** in 2022 vs 11.6–33.3 % in other years.
- Every month is wide (peak June $40.7). Midday is widest (HE12–15, $32–38).
- The published hub components split it **$18.47 congestion (72 %) / $7.17 losses**. Congestion in 2023–25 is only
  $1.1–2.2.
- 2022 MISO SOM (hand-read, not intaken): RT congestion $3.7 B, of which wind-loaded constraints > $1.5 B; overlapping
  outages $1.1 B; understated line ratings $540 M (pp. xiv–xv, 58, 73–74). All facility-level, none a zonal limit.

**The model side.** Midwest zonal prices differ in **0.0000** of 2022 hours. Links L1–L6 are an inline 40,000 MW
never-bind placeholder (`iso_configs.py:788`), with no `constants.py` entry.

**Is there a measured 2022 limit? No.**
- MISO binding-constraint history (`YYYY_rt_bc_HIST.csv`) returns **404 for 2021 and 2022**; 2023 exists.
- RDT PBC and M2M flowgate records on disk cover 2023–25 only.
- Hub congestion components exist but are the **answer class** (rule 13): localization only.
- The only measured zonal limits are the LOLE-study CIL/CEL (PY2022-23: West export 3,273 / import 4,629 MW). They are
  RA deliverability quantities, not dispatch transfer limits, and `measured_interface_limits` is already **R**
  (miso-174).

**Already adjudicated** (not re-proposed): `internal_congestion_split` G (reopens only on RO-1, MISO publishing shift
factors / zone-aligned limits, or RO-2, an owner-chartered reduced-network program; miso-79 found 88–99.7 % of
congestion inside single BAs); `measured_interface_limits` R; `zonal_loss_surface` R; `miso_rdt_measured_limit` R;
`rdt_tcdc` K; `seam_flow_envelopes` K; miso-270 "no north congestion".

**Verdict: no solve.** A limit tuned to reproduce the spread is what rules 1 and 13 forbid. The remaining route is
RO-2 — an owner decision to charter a reduced-network (flowgate) program — not a lever.

## 2. C1 ST_GAS: the CAMPD–EIA crosswalk

_(filled from the intake agent's report — §2 below)_

## 3. C3b 2021: the declined D1 arm did not implement the ruling for MISO-South

**Defect.** `_miso_zone_hub_kind` reads `miso_zonal_gas_hub.csv` by year. **MISO-South has rows only from 2022**, so in
2019–2021 South fell through the caller's `"chicago"` default. In the miso-276 D1 run, South gas in Feb 2021 was priced
on the **$129.52 Chicago Uri weekend print**, not Henry Hub (≤ $23.86) as the owner ruled.

**Fixed** (this lane): a zone missing from a year takes its hub from the nearest year the table carries (a hub is
geographic; the basis value stays year-specific). Test:
`test_miso_zone_hub_kind_maps_south_to_henry_in_years_without_a_south_row`. Only the two default-off appliers call it
(`miso_winter_gas_daily_delivered`, `miso_gas_marginal_commodity_pricing`); **no keeper arms either**, so every keeper
is byte-identical. The registered `2026-09-26-miso-276-winter-daily` run no longer reproduces at HEAD for 2019–2021;
it stays as the record of the as-built arm.

**Feb-2021 gas, keeper fleet, capacity-weighted $/MMBtu (zero LP):**

| convention | storm Feb 13–16 | calm Feb | burn-weighted Feb | South storm |
|---|---:|---:|---:|---:|
| keeper (923 monthly level × calendar-normalized shape) | 29.7 | 11.9 | 18.2 | 32.5 |
| D1 **as built** (South on Chicago) | 102.3 | 5.5 | 25.6 | 111.5 |
| D1 **as ruled** (South on Henry Hub) | 56.4 | 5.4 | 13.0 | 7.7 |
| keeper shape, burn-normalized to 923 level | 31.6 | 10.7 | 16.0 | 27.4 |
| D1 print shape, burn-normalized to 923 level ("paid level") | 71.5 | 3.9 | 16.0 | 94.1 |
| D1 as ruled, burn-normalized to 923 level | 42.0 | 9.6 | 16.0 | 27.4 |

Burn weights: each plant's own CAMPD daily gas heat input (85.5 % of gas pmax covered; the rest keep calendar weights).

**What the burn-weighted column says.** EIA-923 is what the fleet reported paying per MMBtu received in Feb 2021.
Weighted by what it burned, the D1 print series implies **$25.6** against the fleet's own **$16.0**; in Indiana / East
**$23–25 vs $5.4–5.8**. The Midwest fleet did not pay the storm print on most of the gas it burned (storage, firm
and bidweek-indexed supply). That is measured, not assumed, and it is the zero-DOF basis for a "paid level" convention.

**Read-outs.**
- Fixing South alone removes about half of the D1 storm uplift (102 → 56). The storm-week *LMP* effect is not
  measurable at zero LP.
- "Paid level" conventions keep the daily shape from the print but pin the monthly level to what each plant paid.
  Zero fitted scalars. The limitation: they lower calm-day gas where 923 is low (Indiana calm 1.8), the miso-269
  below-commodity symptom persists in the Chicago zones.
- Every row stays inside `miso_winter_gas_daily_delivered`'s scope (Dec–Feb). No threshold is chosen anywhere.

The owner question built on this table is §4.

## 4. Owner questions

_(filled at the end of the session)_
