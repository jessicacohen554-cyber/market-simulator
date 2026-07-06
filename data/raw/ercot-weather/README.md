# ercot-weather — raw

`ercot_zone_temp_daily.csv` (`date, zone, tmax_c, tmin_c`, e.g. zone
`Houston`) — NOAA GHCN-Daily station temperature per ERCOT weather zone.

**Source:** NOAA GHCN-Daily (public domain, CC0-1.0 — see
`docs/data-licensing.md` §2).

**Regeneration:** `python scripts/fetch_zone_temperature.py --iso ERCOT` —
same generic per-ISO fetcher used by every `<iso>-weather/` directory; station
weights come from `data/raw/reference/iso_zone_weather_stations.csv`.

**Consumer:** `scripts/curate_weather.py`.
