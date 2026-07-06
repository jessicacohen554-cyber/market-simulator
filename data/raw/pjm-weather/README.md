# pjm-weather — raw

`pjm_zone_temp_daily.csv` — NOAA GHCN-Daily station temperature per PJM
model zone.

**Source:** NOAA GHCN-Daily (public domain, CC0-1.0 — see
`docs/data-licensing.md` §2).

**Regeneration:** `python scripts/fetch_zone_temperature.py --iso PJM` —
same generic per-ISO fetcher used by every `<iso>-weather/` directory.

**Consumer:** `scripts/curate_weather.py`.
