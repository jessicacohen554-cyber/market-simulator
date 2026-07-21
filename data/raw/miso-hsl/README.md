# MISO HSL — wind on the forecast-uncurtailed reference-rate path; no hourly parquet

No hourly `miso_<year>_hsl_hourly.parquet` exists (misoenergy.org's 5-minute
workbooks stay HTTP 403), so `market_sim.data.renewables._hsl_file` returns
`None` for MISO — there is no *measured hourly* uncurtailed series.

**MISO wind now re-curtails anyway (2026-07-21).** The Potomac Economics annual
aggregate below gives a measured, forward-reproducible wind curtailment RATE
(~4.9% of potential, training-window 2023+2024 firm mean), which
`renewables._miso_wind_reference_curtailment_rate` feeds into the
forecast-uncurtailed gross-up (`delivered ÷ (1 − rate)`, the same mechanism
ERCOT's no-NP6 years use). So MISO wind's renewable bound is `forecast_uncurtailed`
and the LP re-curtails endogenously. **MISO solar** has no published curtailment
series, so it keeps the EIA-930 delivered profile (`delivered_pinned`) — a
documented genuine gap, not a fabricated series. An hourly parquet, if the
workbooks ever unblock, would upgrade wind to `measured_potential`.

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
