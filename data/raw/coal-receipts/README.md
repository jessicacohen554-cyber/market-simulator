# `coal-receipts` — plant-level monthly coal receipts (EIA-923 Schedule 5)

The **delivery** half of the coal fuel-inventory state, and the sibling of
`data/raw/coal-stocks/` (the **stock** half). Together they are the two
measured sides of

```
ending[m] = ending[m-1] + receipts[m] - burn[m]
```

which is also the reason both carry the same rule-13 warning at the bottom of
this file.

## Why this intake exists — the legacy extract is incomplete, measured

`data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet` already carries a
`quantity` column derived from this same EIA form. It is an **incomplete
extract** and must not be used for coal tonnage. Measured 2026-09-14 against
the 67 MISO model coal plants:

| | legacy parquet | this datatype |
|---|---:|---:|
| MISO coal plants matched | **55 of 67** | **64 of 67** |
| MISO coal receipts, 2020 | 99.10 Mt | **120.42 Mt** |
| national coal receipts, 2018 | 435.96 Mt | **596.22 Mt** |

The legacy file understates MISO coal receipts by 17–21 % across 2018–2024. A
fuel budget built on it moves two MISO years from inert to marginal, which
would have produced a **false** G-FOOTPRINT failure in the coal-inventory
screen.

## Source

Public domain (US Government work), EIA Form 923, worksheet
**`Page 5 Fuel Receipts and Costs`** of the `EIA923_Schedules_2_3_4_5_M_*`
workbook — the same free, **keyless** annual bulk ZIP the `coal-stocks` intake
reads:

| | |
|---|---|
| landing page | <https://www.eia.gov/electricity/data/eia923/> |
| recent years | `https://www.eia.gov/electricity/data/eia923/xls/f923_<YEAR>.zip` |
| older years | `https://www.eia.gov/electricity/data/eia923/archive/xls/f923_<YEAR>.zip` |

`SHA256SUMS.txt` records each workbook's sha256 and the URL it came from; the
~22 MB source workbooks are **not** retained, and re-fetching is the recovery
route:

```
python scripts/data/fetch_eia923_coal_receipts.py --years 2018 2019 2020
```

## Layout, and the one scoping decision

One CSV per year, `coal_receipts_<YEAR>.csv`, written **verbatim** — every
column of every kept row, no transformation beyond dropping EIA's four banner
rows above the header.

**Kept rows are `FUEL_GROUP == "Coal"` only.** Page 5 is an all-fuel sheet and
this datatype is coal receipts, so the fuel filter is the datatype's own
definition rather than a transformation of what it covers. It is applied at
fetch because it cuts the committed corpus roughly four-fold (~1.6 MB/yr
instead of ~7 MB/yr) for exactly the rows nothing here would ever read.

A raw row is one receipt **lot** — one (plant, month, rank, purchase type,
mine, supplier, transport mode) delivery — so the sheet has no unique key.
`scripts/data/curate_coal_receipts.py` sums lots onto the schema grain and
carries heat content and delivered cost as quantity-weighted means.

## Coverage

| year | plant-level coal receipts |
|---|---|
| 2018–2024 | **yes** (Final Revision vintage) |
| 2025 | **no** — awaiting the EIA-923 2025 Final Revision, same gap the `coal-stocks` README records |

The 2025 gap does **not** block a 2025 budget: a 2025 delivery rate is built
from 2023 + 2024, and a 2025 opening stock is December 2024 — both curated.

Two vintage facts, both handled in the curation script:

* **`Balancing Authority Code` is absent before 2020.** Nullable and
  provenance-only (ISO membership comes from the plant registry), so 2018/2019
  curate cleanly with it null.
* **Blank `Primary Transportation Mode`** becomes the sentinel `UNK` rather
  than null, because it is a key column. A blank provenance field is not a
  reason to drop a real delivery.

Plant id `999999` ("State-Fuel Level Increment") is excluded for the same
reason `coal-stocks` excludes it, though measured it contributes **zero** rows
to this sheet — the synthetic increment is a Page 1 / Page 2 construct. The
exclusion stays so the two intakes cannot drift.

## Known footprint gap — coal received at shared-storage entities

EIA files some coal at third-party **terminal / shared-storage** entities that
hold their own plant id and are not generators, so a footprint built from
modelled *generator* plant ids does not see those deliveries. Measured for
MISO: `DTE-BRSC Shared Storage` (id 8841, the Belle River / St Clair shared
yard) received **32.01 Mt over 2018–2024**, about 3.6 % of the MISO footprint
rate, while Belle River's own id 6034 shows **no receipts at all**. Other
terminals in the record (`CCT Terminal` IL, `Four Rivers Terminal` KY,
`Keystone`/`Conemaugh` PA, …) cannot be tied to a served plant from this data
alone.

This is a rule 14 `[R-ACCURATE]` boundary misalignment: the data is real, but
it is filed at an entity grain the model's fleet does not carry. It is
recorded here rather than silently absorbed, and any budget built on this
datatype should state which side of it that budget sits on.

## Rule 13 `[R-MEASURED]` — read before building a budget on this

`quantity_tons` is a measured **deliveries-to-tank OUTCOME** for the year it is
reported in, and the precedent on it is explicit rather than inferred:
`src/market_sim/data/winter_fuel_inventory.py` records that the F923 petroleum
*receipts* budget was **rejected** as "a measured deliveries-to-tank OUTCOME
inadmissible under CLAUDE.md #13", and that the accepted NEISO budget was
rebuilt from forward-regenerable capacity/logistics quantities instead.

So **year Y's own receipts are not an admissible delivery rate for year Y's
budget**, exactly as year Y's own stock path is not. What is admissible is a
rate derived from years `<= Y-1`: that regenerates for a forward year from
then-current filings and responds to changed conditions.
`src/market_sim/data/coal_receipts.py` exposes exactly that read
(`prior_years_delivery_rate`) and deliberately exposes no convenience function
returning the target year's own receipts.
