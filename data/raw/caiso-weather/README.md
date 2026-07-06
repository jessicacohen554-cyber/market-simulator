# caiso-weather — raw

`caiso_zone_temp_daily.csv` (`date, zone, tmax_c, tmin_c`) and
`caiso_load_weighted_tmax_daily.csv` — NOAA GHCN-Daily station temperature,
load-weighted to CAISO model zones.

**Source:** NOAA GHCN-Daily (public domain, CC0-1.0 — see
`docs/data-licensing.md` §2).

**Regeneration:** `python scripts/fetch_zone_temperature.py --iso CAISO` —
pulls each station's daily record from the NOAA GHCN-Daily access-CSV
endpoint and load-weights TMAX/TMIN per (zone, date) using the station
weights in `data/raw/reference/iso_zone_weather_stations.csv`.

**Consumer:** `scripts/curate_weather.py` (writes the `weather` clean
datatype; the `_load_weighted` sentinel zone is the ISO-level aggregate).
