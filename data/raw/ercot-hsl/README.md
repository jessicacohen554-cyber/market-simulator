# ercot-hsl — raw

`ercot_2023_hsl_hourly.parquet` — 2023 uncurtailed-renewable-potential (HSL)
fallback, and `np6/` — the drop zone for ERCOT's own NP4-732/733/737/738-CD
wind/solar power-production reports (2024/2025); **currently empty** (see
`np6/README.md` for that report family's DATA NEEDED status and the
Data-Access-Portal 401 blocker).

**Source (2023 fallback):** not ERCOT's own data — cloned from the UMass
`nodal-curtailment-analysis` public dataset,
<https://github.com/codecexp/nodal-curtailment-analysis> (Maji, Irwin,
Shenoy, Sitaraman, ACM e-Energy 2025), used only because no NP6 upload
covers 2023.

**Regeneration:** `scripts/build_ercot_hsl.py` — builds the 2023 fallback
from the UMass repo; would build 2024/2025 from `np6/` uploads once ERCOT's
Data Access Portal registration is obtained (see `np6/README.md` and
`docs/ercot-hsl-2024-25-intake-attempt-2026-07.md` for the full blocker log —
`mis.ercot.com`'s report-list download path was retired in favor of
`apiexplorer.ercot.com`, which 401s without a registered API key).

**Consumer:** `market_sim.data.renewables` (HSL loader).
