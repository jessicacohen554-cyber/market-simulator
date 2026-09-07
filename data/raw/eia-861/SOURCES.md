# `eia-861` — SOURCES

Fetched **2026-09-07** by lane SPP-57 from EIA's public EIA-861 bulk archive over plain
HTTPS (no key). The full zips are NOT committed (4.6 MB each; only the two-utility cut is
needed); their sha256 is recorded so the cut can be re-verified against a re-fetch.

| data year | URL | zip sha256 | member | member sha256 |
|---|---|---|---|---|
| 2023 | `https://www.eia.gov/electricity/data/eia861/archive/zip/f8612023.zip` (the non-archive path `zip/f8612023.zip` returns an HTML page, not the zip) | `0acd67ab84cdaef09fd47b4449f2c944f8731c2b3c695ec3a97bb6c0690a4d61` | `Sales_Ult_Cust_2023.xlsx` | `500214fc20188fa5dab92b445343c4c59b9e7c3d0272d5610724a8ab2dead3d7` |
| 2024 | `https://www.eia.gov/electricity/data/eia861/zip/f8612024.zip` | `77ce49c60ac5a6bad50c442fc401aad5404a21da875dc5cbaba353af5ede54de` | `Sales_Ult_Cust_2024.xlsx` | `78f0a24db2b3eced624311f14974906eb82595e3fed17d910ef3bc8fb755780e` |

Re-fetch:

    curl -sSL -o f8612023.zip https://www.eia.gov/electricity/data/eia861/archive/zip/f8612023.zip
    curl -sSL -o f8612024.zip https://www.eia.gov/electricity/data/eia861/zip/f8612024.zip

Cut: rows with `Utility Number ∈ {15474, 17698}` of `Sales_Ult_Cust_<year>.xlsx` (three
header rows), columns `Data Year, Utility Number, Utility Name, Part, Service Type, State,
Ownership, BA Code, TOTAL Sales (MWh)`.

Licence: EIA data are in the public domain (U.S. federal government work).

## The values, as read (FINDING-spp-57 §2)

| year | PSO (OK) MWh | SWEPCO AR / LA / TX MWh | w_OK |
|---|---:|---:|---:|
| 2023 | 18,421,783 | 3,548,497 / 6,264,772 / 7,081,384 = 16,894,653 | **0.5216** |
| 2024 | 19,127,158 | 3,439,358 / 6,044,274 / 6,920,872 = 16,404,504 | **0.5383** |
| 2025 | — (unpublished at 2026-09-07) | — | hold-last **0.5383** |
