# `coal-stocks` — plant-level monthly ending coal stocks (EIA-923 Schedule 2)

The measured fuel-**inventory** state for coal. Coal units in this model carry
take-or-pay and must-run **floors** and no **ceiling**, and the only
fuel-inventory mechanism in the codebase is NEISO winter oil
(`src/market_sim/data/winter_fuel_inventory.py`). `docs/FINDING-miso256-2022-
passthrough-inversion-2026-09-13.md` §4 identified that missing limb as the
mechanism behind MISO's flat +4.3 GW 2022 coal block; this is the measured
input it needs.

## Why this needed no credential

`FINDING-miso256` §5 recorded these stocks as **"not on disk"**, named an
`EIA_API_KEY` as the unblocker, and reported the EIA API v2 as blocked from the
session. The API route *is* key-gated — `https://api.eia.gov/v2/coal/...`
returns **HTTP 403** without a key, re-confirmed 2026-09-14. But the same
quantity ships in EIA's **free annual bulk workbook**, which needs no
credential at all. This is the same shape as that document's own §0 lesson
about the MISO LMP families: an exhaustive-looking audit of an incomplete
search space.

## Source

Public domain (US Government work), EIA Form 923, worksheet
**`Page 2 Coal Stocks Data`** of the `EIA923_Schedules_2_3_4_5_M_*` workbook:

| | |
|---|---|
| landing page | <https://www.eia.gov/electricity/data/eia923/> |
| recent years | `https://www.eia.gov/electricity/data/eia923/xls/f923_<YEAR>.zip` |
| older years | `https://www.eia.gov/electricity/data/eia923/archive/xls/f923_<YEAR>.zip` |

## Layout

One CSV per year, `coal_stocks_<YEAR>.csv`, written **verbatim** from the
worksheet — every column, no transformation beyond dropping EIA's five banner
rows (agency / title / sources / blank / a merged "Total Month Ending Stocks"
super-header) above the real header. The source workbooks are ~20 MB each and
are **not** retained; `SHA256SUMS.txt` records each one's sha256 and source URL,
and re-fetching is the recovery route:

```
python scripts/data/fetch_eia923_coal_stocks.py --years 2018 2019 2020
```

Wide layout: twelve `Quantity <Month>` columns carrying that month's **ending**
stock in short tons. `scripts/data/curate_coal_stocks.py` melts it long.

## Coverage, and the gaps — stated rather than discovered later

| year | plant-level coal stocks | note |
|---|---|---|
| 2018–2024 | **yes** | Final Revision vintage |
| 2025 | **no** | see below |

**DATA NEEDED: `coal_stocks_2025.csv` — awaiting the EIA-923 2025 Final
Revision.** The 2025 release on disk at EIA (`f923_2025.zip`, workbook stamped
`20FEB2026`) carries `Page 2 Stocks Data` and `Page 2 Oil Stocks Data` but
**no** `Page 2 Coal Stocks Data`. Its combined sheet is *census-division /
state aggregate in thousand tons with withheld (`W`) cells* — 67 rows, not
plant-level — so it cannot substitute. The plant-level coal split appears only
in the Final Revision. Re-run the fetch script once EIA publishes it.

Two further vintage facts, both handled in the curation script:

* **`Balancing Authority Code` is absent before 2020.** Nullable and
  provenance-only (ISO membership comes from the plant registry, not this
  column), so 2018/2019 curate cleanly with it null.
* **Plant id `999999` is not a plant.** It is EIA's synthetic
  *"State-Fuel Level Increment"* — the imputed residual for plants below the
  reporting threshold, filed per state × sector × fuel (141–172 rows/yr). It is
  **excluded**: this datatype's grain is a real plant the fleet can join to, and
  a state residual summed in would be a fictitious stockpile no modelled unit
  can burn. It is also the sole reason a naive `(plant, fuel)` key looks
  massively duplicated — with it removed, genuine duplicate pairs are **0 in
  five of the seven published years** (2 in 2019, 1 in 2024).

## Rule 13 `[R-MEASURED]` — read before building a budget on this

`ending_stock_tons` is a measured **state**, and its 12-month path embeds the
burn a backcast is being asked to reproduce:

```
ending[m] = ending[m-1] + receipts[m] - burn[m]
```

So an admissible energy budget for year *Y* reads the **opening** stock
(December of *Y−1*) plus a delivery rate derived from years **≤ *Y−1***, and
never year *Y*'s own stock path or receipts. The NEISO oil precedent is
explicit that F923 *receipts* are "a measured deliveries-to-tank OUTCOME
inadmissible under CLAUDE.md #13", so the target year's receipts are not a
delivery rate either. `market_sim.data.coal_stocks.opening_stock_tons` exists
to make the admissible read the easy one.

## Consumers

**None in the LP.** Intake-only as of miso-258 — there is no `ScenarioConfig`
flag and no mechanism. The read seam is
`src/market_sim/data/coal_stocks.py`; the zero-LP use it was built for is
`docs/FINDING-miso258-coal-stock-falsification-2026-09-14.md`.
