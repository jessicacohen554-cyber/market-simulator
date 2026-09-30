# SPP — capacity of generation on outage, hourly, by fuel (2019–2025)

- **Source:** the SPP Marketplace portal product `capacity-of-generation-on-outage`, which reports the hourly
  capacity of generation on outage by fuel.
  - Year zips: `https://portal.spp.org/file-browser-api/download/capacity-of-generation-on-outage?path=%2F<Y>%2F<Y>.zip`.
  - The 2025 year zip downloads empty (0 bytes; measured 2026-09-26 and 2026-09-30), so 2025 is assembled from
    the 365 daily files: `?path=%2F2025%2F<MM>%2FCapacity-Gen-Outage-<YYYYMMDD>.csv`.
- **File:** `spp_capacity_gen_outage_hourly.csv`.
  - It has one row per `Market Hour` (61,358 hours) and keeps the portal's own column names (whitespace stripped):
    `Outaged MW`, `Coal MW`, `Diesel Fuel Oil MW`, `Hydro MW`, `Natural Gas MW`, `Nuclear MW`, `Solar MW`,
    `Waste Disposal MW`, `Wind MW`, `Waste Heat MW`, `Other MW`.
  - The daily files overlap at the day seam; the **last** snapshot of each market hour is kept (SPP-84's convention).
- **Re-fetch:** `python scripts/data/fetch_spp_capacity_gen_outage.py` (or `--from-dir <dir of o<Y>.zip + <Y>/*.csv>`).
- **Identity:** `SHA256SUMS.txt`.
- **Annual means, Natural Gas MW:**

  | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
  |---|---|---|---|---|---|---|
  | 10,195 | 8,128 | 8,032 | 7,226 | 7,927 | 9,654 | 8,988 |

- **Definition (SPP-85):** CROW outages, including Reserve Shutdown as Planned Outage, plus Derate types.
  - There is fuel grain only, with no technology split (DESIGN-spp-105 §3).
  - Ambient derates are not reported to CROW (MMU, *Unavailable Generation Capacity*, Dec 2025, §3.3.1.2).
- **Read by:**
  - `market_sim.data.spp_gas_outage`, under `ScenarioConfig.spp_gas_crow_residual_outage` (SPP-105, default off);
  - the SPP-84 / SPP-104 / SPP-105 probes.
