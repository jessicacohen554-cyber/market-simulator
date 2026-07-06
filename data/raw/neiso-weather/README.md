# neiso-weather — raw

`neiso_zone_temp_daily.csv` and `neiso_load_weighted_temp_daily.csv` — NOAA
GHCN-Daily station temperature per ISO-NE zone, plus the ISO-level
load-weighted aggregate (`_load_weighted` sentinel zone).

**Source:** NOAA GHCN-Daily (public domain, CC0-1.0 — see
`docs/data-licensing.md` §2).

**Regeneration:** `python scripts/fetch_zone_temperature.py --iso NEISO` —
same generic per-ISO fetcher used by every `<iso>-weather/` directory.

**Consumers:** `scripts/curate_weather.py`,
`scripts/derive_neiso_temp_reliability_floor.py` (legacy per-ISO consumer).
