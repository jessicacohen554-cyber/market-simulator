# `eia-861` — EIA-861 Annual Electric Power Industry Report (reduced sidecar)

Opened **2026-09-07** by lane **SPP-57** (`docs/handoffs/PRECOMMIT-spp-57-2026-09-07.md`
§2.2). Source of record: `SOURCES.md` beside this file.

## What this is

A **reduced sidecar** of the EIA-861 `Sales_Ult_Cust_<year>.xlsx` schedule — retail sales
to ultimate customers by utility and state — cut to the two AEP West operating companies
that together form SPP's `CSWS` (AEPW) sub-balancing-authority:

| utility_id | utility | states |
|---|---|---|
| 15474 | Public Service Co of Oklahoma (PSO) | OK |
| 17698 | Southwestern Electric Power Co (SWEPCO) | AR, LA, TX |

`sales_ult_cust_aep_west_2023-2024.csv` carries every `Sales_Ult_Cust` row of those two
utilities (all `Part` / `Service Type` rows — one `A / Bundled` row per utility-state in
both years), columns verbatim from the sheet (`Utility Characteristics` block +
`TOTAL | Sales | Megawatthours`), for data years **2023 and 2024**. Nothing is edited;
the rows are copied, not retyped (the producer is the pandas read recorded in
`docs/handoffs/spp57/` and the FINDING).

## Why it exists — the CSWS sub-allocation (rule 14 misalignment)

EIA-930 reports AEP West as ONE sub-BA (`CSWS`) spanning Oklahoma (PSO) and
Arkansas / Louisiana / east Texas (SWEPCO). The SPP three-zone topology (lane SPP-57)
places PSO's load in `SPP-Oklahoma` and SWEPCO's in the residual `SPP-South`, and no
published hourly series splits the sub-BA. The split is therefore the **measured annual
retail-sales ratio**:

    w_OK(year) = PSO total sales / (PSO + SWEPCO total sales)

applied to the CSWS hourly MW as an identity (`scripts/data/curate_zonal_shares.py`,
`_SPP_CSWS_OKLAHOMA_SHARE_BY_YEAR`). 2025 is a declared **hold-last** of 2024 until EIA-861
2025 is published. Stated misalignment: the CSWS sub-BA also carries non-AEP load (AECC /
ETEC / OMPA / GSEC) whose MW are not separately published, so the AEP retail split is
applied to the whole sub-BA.

## Timezone / units

Annual MWh; no time dimension.
