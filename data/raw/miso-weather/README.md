# miso-weather — raw

`miso_zone_temp_daily.csv` — NOAA GHCN-Daily station temperature per MISO
model zone.

**Source:** NOAA GHCN-Daily (public domain, CC0-1.0 — see
`docs/data-licensing.md` §2).

**Regeneration:** `python scripts/fetch_zone_temperature.py --iso MISO` —
same generic per-ISO fetcher used by every `<iso>-weather/` directory.

**Consumers:** `scripts/curate_weather.py`,
`scripts/derive_miso_temp_reliability_floor.py` (legacy per-ISO consumer,
superseded by the generic weather datatype for new work).
