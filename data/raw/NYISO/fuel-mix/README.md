# NYISO aggregate real-time fuel mix (system-wide by fuel class)

Hourly aggregation of the NYISO MIS public 5-minute "Real-Time Fuel Mix"
posting (P-63, `mis.nyiso.com/public/csv/rtfuelmix/`), 2018-01 through 2026-06
(H1-2026 cap), one CSV.GZ per year:

    NYISO_fuelmix_hourly_<year>.csv.gz

Columns: `interval_start_utc, interval_start_local, fuel_category, gen_mw,
n_intervals`.

Built by `scripts/data/fetch_nyiso_fuel_mix.py` (download + documented
5-min→hourly aggregation: mean `Gen MW` per fuel/hour; the raw 5-minute zips
are ~110 MB/year and are not committed — the script's cache regenerates them
from the MIS archive). The source carries an explicit `Time Zone` (EST/EDT)
column, so UTC conversion is exact (EST = UTC-5, EDT = UTC-4) with no
DST-ambiguity guessing. Interior source gaps are filled from the adjacent
actual and marked `n_intervals = 0`; `n_intervals` is normally 12 (twelve
5-minute posts/hour, 24 in the DST fall-back hour) but the source occasionally
posts extra sub-hourly revisions, so counts above 12 occur — the mean is
robust to them and the count is carried so consumers can see it.

**Fuel categories (7, NYISO's own taxonomy):** Dual Fuel, Natural Gas,
Nuclear, Hydro, Wind, Other Renewables, Other Fossil Fuels. This is the NYISO
analogue of the PJM "Generation by Fuel Type" feed
(`data/raw/ISO-specific-gen-data/PJM_<year>_gen_by_fuel.csv`) and gives a
coarse class envelope for the NYISO C1 fuel-mix scoring target, complementary
to the EIA-930 NYIS series already in `data/raw/eia-930/`.

**System-wide, not zonal.** NYISO does **not** publish cleared generation by
zone as a public feed — the fuel mix is NYCA-total only, and the only public
zonal series are the DAM/RT zonal LBMP *prices* (`data/raw/lmp-data/NYISO`,
`mis.nyiso.com/public/csv/{damlbmp,realtime}/<yyyymm01>{damlbmp,realtime}_zone_csv.zip`).
Zonal cleared *generation* is available only through NYISO's restricted /
generator-masked market disclosure, not a free MIS CSV.

Years 2018–2022 and 2026 are out-of-training intake under the session-logged
owner authorization of 2026-07-10 (CLAUDE.md rule 22; itemized in
`docs/out-of-sample-results-2026-07.md` §1.2). Admissibility: this is a
measured market **outcome** series used only as a scoring target / bench —
never fed back into the dispatch as an input (rule 13), so it carries no
forecast-input admissibility burden.

**Licensing note:** NYISO's redistribution terms are unclear/unverified —
see `docs/data-licensing.md` §7.
