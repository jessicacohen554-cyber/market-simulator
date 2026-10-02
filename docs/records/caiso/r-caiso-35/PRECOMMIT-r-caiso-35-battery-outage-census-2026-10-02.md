# PRECOMMIT — R-CAISO-35 (link 17): battery-outage census and the rule-19 test against the shape anchor

Written and committed **before** any number below is computed. Zero LP, no shard, no `ScenarioConfig` field, no
constant, no matrix cell moved. Owner selection: R-CAISO-32 FINDING §7 point 2. The closeout-CAISO lane's arms are
not touched. Off-plan relative to `docs/backcast-closeout-plan-2026-10.md` §3.7 by owner selection (the chain's
link 17), not by this session's choice.

## 0. Question

Battery resources in the CNOG daily report (`data/raw/caiso-dam-outages`) are offline or derated by **14–21 % of
fleet MW** on average (R-CAISO-32 Part B). None of it reaches a solve. `caiso_storage_shape_anchor` (on in the
keeper) caps each li-ion pool's charge and discharge at `env_p95[year, hod] × power_cap[s, t]`, where `env_p95` is
the p95 across days of measured EIA-930 `NG: OTH` charge/discharge ÷ EIA-860 monthly fleet MW
(`scripts/derive_caiso_storage_shape.py`).

**Rule 19:** before any consumer of the outage MW is proposed, does the envelope already carry the phenomenon?

## 1. Structural reading (stated now, not tested)

The envelope's numerator is realized dispatch, which can never include MW that were on outage; its denominator is
the full EIA-860 fleet, outaged units included. So `env_p95 × fleet` is, by construction, a fleet capability
**net of whatever outages were in force on the p95 days**. A per-resource outage derate applied on top of it
(`power_cap × (1 − o)` under the same `env_p95` multiplier) would remove the outaged MW twice. What that structure
cannot guarantee is the hour-by-hour case: on an hour where outages are deeper than on the days that set the p95,
the envelope can still grant MW the outages had removed. That is what the test measures.

## 2. Inputs (all committed raw inputs; no LP output in the loop)

- CNOG episodes: `data/raw/caiso-dam-outages/caiso-dam-outage-windows.parquet` (2023–25).
- Envelope: `data/raw/reference/caiso-storage-shape-envelope.csv`, columns `chg_frac_p95`, `dis_frac_p95`.
- Fleet denominator: EIA-860 monthly installed battery MW, the **same** function the envelope derive uses
  (`derive_caiso_storage_shape.monthly_battery_fleet_mw`). Sensitivity denominator: RTM storage bidding fleet,
  daily Σ `en_max_mw` over `is_storage_s1` (`data/raw/caiso-rtm-eoh-soc`), the R-CAISO-32 Part B basis.
- Measured dispatch (T2 only): EIA-930 `CISO hourly.parquet` `NG: OTH`, as the derive reads it.
- Clock: the CNOG episode stamps and EIA-930 `Local date`/`Hour` are both Pacific prevailing; the envelope was
  derived on the EIA-930 clock, so the census bins on that clock too. Hours are 8760 per year, Feb 29 dropped as
  the derive does (first 8760 rows).

## 3. Battery population and the crosswalk

- **Census population (primary for T1):** the R-CAISO-32 Part B selector, unchanged — resource id suffix
  `_(BT|BX|ES|BE)<digit>` or a storage/battery/BESS name, solar-only names excluded. Offline MW per resource is
  the sum of overlapping curtailments, capped at the resource Pmax, hour by hour.
- **Crosswalk (the deliverable):** `scripts/data/build_caiso_resource_crosswalk.py --storage` writes a **sibling**
  file `data/raw/reference/caiso-storage-resource-eia-crosswalk.csv`, mapping each census resource to an EIA-860
  energy-storage operable plant (`Plant Code`) in a CAISO zone, by the script's existing name-token score with
  the same `accept_threshold = 0.6` and the same capacity sanity (`resource_pmax ≤ 2 × plant MW`). It is a
  separate file so `market_sim.data.caiso_outages.load_crosswalk` — the thermal overlay's only reader — is
  byte-identical, and no consumer exists. Reported: rows, accepted rows, and the **share of census offline
  MW-hours on accepted resources** (coverage).
- **Sensitivity population for T1:** accepted crosswalk resources only.

## 4. Tests and their pre-registered readings

Notation, per year y ∈ {2023, 2024, 2025}, hour t (8760), direction d ∈ {chg, dis}:
`o(t) = offline_MW(t) / fleet_MW(t)`, `a(t) = 1 − o(t)` (the fleet share the outages leave available),
`e_d(t) = env_p95_d[y, hod(t)]`.

**T1 (primary, the rule-19 test): does the envelope ever grant MW the outages removed?**
`B_{y,d} = share of hours with e_d(t) > a(t)`, on the EIA-860 denominator and the census population.
Also reported: the MW-hour excess `Σ max(0, e_d − a) × fleet` as a share of `Σ e_d × fleet`.

| Reading | Condition (max over y, d of `B_{y,d}`) | Consequence |
|---|---|---|
| **CARRIED** | ≤ 1 % | The envelope sits under the outage-available fleet in effectively every hour. The outage MW leg is already carried by the shape anchor; any consumer stacked on it double-counts (rule 19). No consumer is proposed; the census is a documented reference input. |
| **MARGINAL** | > 1 % and ≤ 5 % | Carried at the annual grain; the binding hours are listed by year/hod/quarter. A consumer is only admissible as a **replacement** (re-derive the envelope's denominator net of outages), never stacked; that is put to the owner, not built. |
| **NOT CARRIED** | > 5 % in any (y, d) | The envelope over-grants on material hours. A consumer must replace or reconcile with the anchor (D-2), never stack; options go to the owner as a card. |

The sensitivity runs (RTM-fleet denominator; crosswalk-only population) are reported beside the primary and do
**not** change the reading unless they cross a band boundary, in which case the reading is the worse band and the
FINDING says so.

**T2 (supporting, basis consistency):** share of hours where measured `|NG: OTH| / fleet_860 > a(t)` — realized
dispatch exceeding the outage-available fleet. Expected ≈ 0. If > 1 % in any year, the CNOG MW and the EIA-860
fleet are on misaligned bases (hybrid / co-located resources, Pmax vs nameplate) and T1 is read with that caveat
named (rule 14 boundary clause).

**T3 (descriptive, no gate):** within-quarter Spearman between the daily mean `o` and the daily max of measured
discharge ÷ fleet. A negative sign says outage depth depresses realized peak dispatch, i.e. the measured series
the envelope is built from responds to it. Reported, not adjudicated.

## 5. What this session will not do

No solve, no `ScenarioConfig` field, no constant, no edit to the envelope CSV or its derive (rule 23: its sources
have not changed), no edit to `load_crosswalk`, no matrix cell moved (no field exists). No consumer is proposed
before T1 is adjudicated. The decision goes to the owner as a card.
