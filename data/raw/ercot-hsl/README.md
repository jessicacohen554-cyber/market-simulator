# ercot-hsl — raw

`ercot_2023_hsl_hourly.parquet`, `ercot_2024_hsl_hourly.parquet`,
`ercot_2025_hsl_hourly.parquet` — uncurtailed-renewable-potential (HSL)
hourly series for all three buildable backcast years. `np6/` holds the
source ERCOT NP4-732/733/737/738-CD wind/solar power-production report
archives 2024/2025 are built from — see `np6/README.md`.

**Source (2023):** not ERCOT's own data — cloned from the UMass
`nodal-curtailment-analysis` public dataset,
<https://github.com/codecexp/nodal-curtailment-analysis> (Maji, Irwin,
Shenoy, Sitaraman, ACM e-Energy 2025), a partial-footprint reconstruction the
renewables loader reconciles up to the EIA-930 delivered level. Used only
because no NP6 upload covers 2023; would be superseded by a published
NP4-732/737 upload in `np6/2023/` if one ever lands.

**Source (2024/2025):** ERCOT's own published NP4-732-CD/NP4-742-CD (wind)
and NP4-737-CD (solar) "Power Production — Hourly Averaged Actual and
Forecasted Values" reports, full-footprint system-wide totals — consumed
directly, no reconciliation. See `np6/README.md` for provenance, coverage,
and the one cited known-bad source window.

**Regeneration:** `scripts/build_ercot_hsl.py --year 2023 2024 2025`.

**Consumer:** `market_sim.data.renewables` (HSL loader).
