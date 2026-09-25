# `soco_zonal_gas_hub.csv` — SOURCES

Landed **2026-09-16** by lane **SOCO-32**
(`docs/multi-iso/soco-addition-plan-2026-09.md` §5 row SOCO-32; FINDING
`docs/handoffs/FINDING-soco-32-2026-09-16.md`). Schema is exactly the
MISO/PJM/CAISO/SPP/NWPP one (`zone,year,basis_vs_hh_usd_mmbtu,hub,source`), so
`market_sim.data.fuel.basis.meanzero._zonal_gas_basis_by_zone` reads it with no
new parsing code.

**Derived by** `scripts/data/derive_soco_zonal_gas_hub.py`, whose module
docstring is the method of record. Regenerate with:

    python scripts/data/derive_soco_zonal_gas_hub.py --cross-check

## The committed table

| Zone | 2023 | 2024 | 2025 | Hub |
|---|---:|---:|---:|---|
| SOCO_AL | +0.955 | +0.860 | +0.757 | **MIXED**: SNG / Transco Z4 (AL) + FL-panhandle delivered |
| SOCO_GA | +0.539 | +0.706 | +0.871 | SNG / Transco Z4 (GA, Dalton lateral) |
| SOCO_MS | +0.166 | +0.393 | +0.334 | SNG / Transco Z4 (MS) |

Equal-weight mean-zero spread (what an armed applier would actually see, since
the mean-zero convention re-centres the level away): **0.789 / 0.467 / 0.537
$/MMBtu** in 2023 / 2024 / 2025. Alabama is the premium zone in two years of
three and Mississippi the cheap zone in all three.

## 1. EIA-923 Schedule 2 per-plant delivered gas — the price

`data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`, already
committed, not re-fetched by this lane. Columns `price_per_mmbtu` (natively
**$/MMBtu** — no heat-content conversion anywhere in this table) and `quantity`,
per plant per month. Coverage is complete: **all three zones, all twelve months,
all three years**, 11 / 15 / 3 gas plants in AL / GA / MS, burning
734.6 / 1,033.3 / 333.4 million MMBtu over 2023–2025.

## 2. Henry Hub monthly — the reference

`data/raw/gas-prices/henry_hub_monthly.csv`, the same committed series every
sibling table differences against.

## 3. Zone assignment

`market_sim.data.zone_assignment.build_zone_lookup("SOCO")` — the ruled card-S3
FIPS-state partition, the same key the fleet, the FERC-714 load shares and the
solar shape use, so a plant cannot land in one zone here and another there.

## Why not SOCO-12's state series — the two measured reasons

SOCO-12 committed the EIA delivered-to-electric-power state series
(`N3045{AL,GA,MS}3`, `data/raw/gas-prices/SOURCES_soco_gas.md`) and left the
zone mapping explicitly to this lane. Rule 14 `[R-ACCURATE]` decided it:

**(a) The state boundary is not the zone boundary for `SOCO_AL`.** Card S3 puts
the six SERC Florida-panhandle plants in `SOCO_AL`. Two of them burn gas — Gulf
Clean Energy Center (641) and Lansing Smith (643), **54.3 TBtu/yr, 20–25 % of
the zone's gas burn** — at a basis of **+1.768 / +1.767 / +1.629** $/MMBtu
against the Alabama plants' **+0.700 / +0.603 / +0.556**: a persistent
**~$1.10/MMBtu premium** on a different delivered market that an Alabama state
series cannot see at all. Using it would understate this zone's gas cost by
roughly $0.40/MMBtu every year.

**(b) The state series stops before the backcast does.** EIA publishes nothing
for **GA or MS after 2024-12**. A state-series table would therefore end in 2024
and hand 2025 either no basis at all or — far worse — an AL-only row, letting GA
and MS default to `0.0` and fabricating a ~$0.75/MMBtu cross-zonal spread out of
a publication gap. That is precisely the trap SPP-32 refused for SPP-South.

## The cross-check that validates the route

Where the zone boundary really *is* the state line, the two routes agree.
`--cross-check` output, 2026-09-16:

| Zone | Year | EIA-923 basis | state $/Mcf − HH | state converted (÷1.037) | 923 − converted |
|---|---|---:|---:|---:|---:|
| SOCO_AL | 2023 | 0.955 | 0.548 | 0.438 | **+0.518** |
| SOCO_AL | 2024 | 0.860 | 0.624 | 0.524 | **+0.337** |
| SOCO_AL | 2025 | 0.757 | 0.713 | 0.561 | **+0.195** |
| SOCO_GA | 2023 | 0.539 | 0.698 | 0.582 | −0.044 |
| SOCO_GA | 2024 | 0.706 | 0.778 | 0.672 | +0.034 |
| SOCO_GA | 2025 | 0.871 | — | NOT PUBLISHED | — |
| SOCO_MS | 2023 | 0.166 | 0.294 | 0.193 | −0.028 |
| SOCO_MS | 2024 | 0.393 | 0.518 | 0.422 | −0.028 |
| SOCO_MS | 2025 | 0.334 | — | NOT PUBLISHED | — |

GA and MS reconcile to **≤ 0.044 $/MMBtu**; AL diverges by 0.2–0.5, and reason
(a) is most of why. Decomposed rather than asserted:

* the **FL panhandle** explains the larger part — restricting the zone to its
  *Alabama* plants drops the basis from 0.955 / 0.860 / 0.757 to
  **0.700 / 0.603 / 0.556**, i.e. 0.26 / 0.26 / 0.20 of the gap;
* taking EIA-923 over **all of Alabama** (adding the one non-SOCO gas plant,
  TVA's Colbert, 8.6 TBtu/yr) gives 0.668 / 0.573 / 0.546 against the converted
  state series' 0.438 / 0.524 / 0.561 — so a **residual 0.23 / 0.05 / −0.02**
  remains in which the two EIA products simply disagree for Alabama, almost
  entirely in 2023.

That residual is **reported, not resolved**: this lane has no basis to prefer one
EIA aggregation over the other on a level question, and it does not need one —
the zone-attribution argument (a) stands on its own, GA and MS reconcile, and
the applier is mean-zero anyway. It is flagged to SOCO-DESK in the FINDING.

**A unit observation, reported rather than acted on.** The *converted* state
series is the one that matches EIA-923, which means the raw
`$/Mcf`-minus-`$/MMBtu` convention the MISO / PJM / SPP tables use carries a
~3.5 % level bias. That is those tables' business, not this one's (rule 25
`[R-ISO-SCOPE]`), and it is routed to SOCO-DESK in the FINDING rather than
fixed here. This table needs no conversion at all.

## What this is NOT

* **Not a traded index.** SOCO-12 measured that no free public daily or monthly
  index exists at SOCO's basis — EIA's Weekly Update spot table has no Southeast
  row and the daily Select Spot Prices map has no Southeast region; the daily
  index is a paywalled ICE/NGI product. The `hub` column names the **transport
  system** (Southern Natural Gas, 50 % Southern Company Gas, 10-K FY2025 Item 1;
  Transco into northwest Georgia via the jointly-owned Dalton lateral, 10-K
  Item 2 note (e)) and the value beside it is the measured delivered price.
* **Not a within-month tail.** These are monthly volume-weighted averages, so
  they are mean-preserving and cannot form a cold-snap tail. That caveat is
  load-bearing for SOCO specifically: the footprint's two most recent annual
  peaks are **January** events, and no free daily source exists behind a winter
  gas overlay (SOCO-12 §4).
* **Not armed.** No `ScenarioConfig` field is added and no applier reads this
  file, so no cache key moves (plan §7 gate **G8**). Arming it is SOCO-40's or a
  later lever's call.

## 2019-2022 (I-SOCO, 2026-09-24)

The derive's `YEARS` widened from 2023-2025 to 2019-2025 — a source-coverage
extension, not a re-derivation (rule 23): both committed inputs
(`_processed-legacy/eia923_monthly_fuel_costs.parquet`, 2018+; `gas-prices/
henry_hub_monthly.csv`, 1997+) already spanned the new years and the
construction is unchanged. `python scripts/data/derive_soco_zonal_gas_hub.py`
now writes 21 rows; **all 9 committed 2023-2025 rows are byte-identical**.
The zone lookup maps 25 / 26 / 27 / 28 gas plants in 2019 / 2020 / 2021 / 2022
(28 / 29 / 29 in 2023-2025); one plant (EIA 7) burns only in 2019-2022.

| zone | 2019 | 2020 | 2021 | 2022 |
|---|---:|---:|---:|---:|
| SOCO_AL | 0.426 | 0.484 | 0.366 | 1.035 |
| SOCO_GA | 0.341 | 0.336 | 0.329 | 1.253 |
| SOCO_MS | 0.143 | 0.213 | 0.076 | 0.073 |

$/MMBtu over Henry Hub. 2022's 1.180 $/MMBtu cross-zone range (GA +1.25 vs MS
+0.07) is the widest of the seven years; it is the measured per-plant
delivered price in the year Henry Hub averaged 6.45, reported as measured.
