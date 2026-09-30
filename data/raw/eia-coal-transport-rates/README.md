# EIA coal transportation rates to the electric power sector (nominal $/short ton)

Source: U.S. EIA, *Coal Transportation Rates to the Electric Power Sector*, "With
final data through 2024", release 2026-02-23,
<https://www.eia.gov/coal/transportationrates/> (files under `excel/`, spaces in
the published names replaced by `_` here). Public domain (EIA). Fetched
2026-09-30 by lane PJM-NEXT-13.

EIA's definition (table notes): the rate is the weighted-average difference
between the **commodity cost and the total delivered cost** of coal shipments to
electric-power plants, by the plant's primary transport mode, from Form EIA-923.
`W` = withheld; `-` = no shipments.

| file | content | sha256 |
|---|---|---|
| `Table_1_Nominal.xlsx` | national, by year and mode | `f982ad8ec91bc77a504aa49dd543729863d82c99ee57f141e4efbf9d16bfb942` |
| `Table_2_Nominal.xlsx` | by mode and coal supply region | `e419ae90f2a77768bc1852efd62a1cd0b3c7f277c4c37a02421dfc63e73a9ead` |
| `Table_3a_Nominal.xlsx` | basin -> destination state, truck | `8ce753c75d547c6386039ab5872105ec0b702952291931da6ad594da903abba7` |
| `Table_3b_Nominal.xlsx` | basin -> destination state, waterway | `67b6dea644ba8c53281d236b4bfeb71cfc6de5cb767f435fdc02be2a08ddc5d8` |
| `Table_3c_Nominal.xlsx` | basin -> destination state, railroad | `8bfb7c5a8f62838c2bf0f65a37e8afcf440416312947efb20263f50cdba619e8` |
| `Table_4a_Nominal.xlsx` | origin state -> destination state, truck | `9072713cfac44d26483e886a4abc443d75a10d616e8e400e28ba0b164e01dc4a` |
| `Table_4b_Nominal.xlsx` | origin state -> destination state, waterway | `3bc2ca30ea08617747f76218d1c2777bba9bbae76f3e8df13f0ec6c2259005c8` |

Consumer: `scripts/data/derive_pjm_replacement_fuel.py` (the coal leg of
`pjm_replacement_cost_fuel`). DATA NEEDED: 2025 rates (not yet published; the
derive holds 2024, declared).
