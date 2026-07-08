# MISO HSL (uncurtailed renewable potential) — coarse aggregate collected, hourly build still open

No hourly `miso_<year>_hsl_hourly.parquet` exists yet, so
`market_sim.data.renewables._hsl_file` still returns `None` for MISO and the
backcast falls back to EIA-930 MISO delivered wind/solar generation (which
embeds the historical curtailment).

`misoenergy.org` and `cdn.misoenergy.org` — MISO's own Market Reports site,
which would carry a CAISO-style 5-minute curtailment workbook — remain
HTTP 403 (allowlist-blocked) as of 2026-07-08, same as the 2026-06-22/
2026-07-05 audits (`docs/multi-iso/miso-data-audit.md`).

**2026-07-08 update:** collected a reachable alternate source instead —
Potomac Economics (MISO's Independent Market Monitor) publishes annual State
of the Market reports and quarterly IMM reports on `potomaceconomics.com`,
which quantify system-wide wind curtailment (annual average/peak MW back to
2021, quarterly average/peak MW for 2023-Spring 2026). See `SOURCES.md` for
full provenance and `miso_wind_curtailment_annual.csv` /
`miso_wind_curtailment_quarterly.csv` / `miso_wind_curtailment_quarterly_
forecast_method.csv` for the transcribed figures. This is coarser than an
hourly series (annual/quarterly aggregates, not 8760 hourly rows), so it is
**not** yet the `miso_<year>_hsl_hourly.parquet` the loader expects.

To finish populating (next step, not done in this collection pass): spread
these annual/quarterly aggregate MW figures across hours using a physically
motivated shape (e.g. the existing `data/raw/miso-wind-shape/` NASA POWER
reanalysis, which is already reconciled to EIA-930 MISO-wide generation),
then build per-year parquets following `scripts/build_caiso_hsl.py`'s
pattern with `HSL = EIA-930 delivered + reported curtailment` (schema
`renewables._HSL_COLUMNS`):

    data/raw/miso-hsl/miso_<year>_hsl_hourly.parquet

The loader will pick them up automatically once written. Note this
construction is materially different from CAISO/ERCOT's (which have a real
measured hourly/5-minute curtailment series to work from) — the MISO
hourly shape would be *modeled*, not *measured*, so it needs its own
documented methodology and rule-#12 admissibility check before it is used
as more than a diagnostic.
