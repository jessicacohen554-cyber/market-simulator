# NWPP-38 — PNCA-termination discontinuity measurement (2026-09-16)

Three derived artifacts produced by `scripts/data/measure_nwpp_pnca_discontinuity.py`.
They are **measurement outputs, not model inputs**: nothing in `src/market_sim/` reads
them, no `ScenarioConfig` field refers to them, and no loader resolves them. They exist
so the FINDING's numbers are reproducible without re-deriving the hourly panel.

Written by lane **NWPP-38**; the reading is `docs/handoffs/FINDING-nwpp-38-2026-09-16.md`.
They sit beside — and do not touch — NWPP-32's budget artifacts, which remain that lane's.

| file | grain | what it holds |
|---|---|---|
| `nwpp_pnca_day_metrics.parquet` | balancing authority × local day, 2019-2025 | daily mean/max/min hydro MW, mean absolute hour-to-hour ramp, and the two scale-free day metrics `D1` (diurnal amplitude ÷ mean) and `D2` (mean \|dP/dt\| ÷ mean P). Only clean, complete 24-hour local days appear |
| `nwpp_pnca_month_metrics.csv` | balancing authority × month | `M1` within-month daily-energy CV, `M2` (p95−p5) ÷ mean of hourly MW, the month's mean MW, and the clean-day count. Months with fewer than 26 clean days are absent |
| `nwpp_pnca_links.csv` | adjacent-pair × month | `r0` Pearson correlation of hourly deviations after each balancing authority's own month-by-hour-of-day profile is removed, `rmax`/`lag` the cross-correlation peak over ±6 h, and the hour count |

## Provenance

Source is the committed EIA-930 BALANCE archive
(`data/raw/eia-930/EIA930_BALANCE_<year>_<half>.parquet`, 2019-2025), not the per-BA wide
extracts — those begin at 2023 for this footprint, which would leave a single pre-period
year. The derive re-does for 2019-2022 exactly what
`scripts/data/build_nwpp_ba_hourly_from_balance.py` did for 2023-2025, and the script
asserts the two agree on the overlap: **0 mismatched hours over 26,303 hours × 12
balancing authorities**. The mid-2024 taxonomy revamp is handled per source file; its
pumped-storage column is **null in every hour of every NWPP balancing authority**, so the
two hydro column names are the same basis here and the taxonomy switch cannot be mistaken
for an operating change.

## Screen

Lane NWPP-37's repair of the EIA-930 fuel-column seam had **not** landed at base
`38ecbf0e`, so the defective hours (routed item R-f; `FINDING-nwpp-32-2026-09-14.md` §3.2)
are screened here instead: a defective hour is `|NG: WAT|` above 1.15 × the balancing
authority's EIA-860 conventional-hydro nameplate, below −0.05 × it, or NaN. Defective
hours are **dropped, never imputed**, and the whole local day is dropped from every
day-level metric. Nameplate is on the EIA-930 basis — Priest Rapids counted in GCPD, not
BPAT. EIA's own `(Adjusted)` hydro column is read only as a robustness check, because it
is imputed as well as screened and so cannot be the primary series for a measurement
about shape.

## Regenerate

    python scripts/data/measure_nwpp_pnca_discontinuity.py

Deterministic; no network, no API key, no LP.
