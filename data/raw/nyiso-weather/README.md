# nyiso-weather — raw

`nyiso_zone_temp_daily.csv`, `nyiso_zone_tmax_daily.csv` — NOAA GHCN-Daily
station temperature per NYISO zone. `nyiso_downstate_tmax_daily.csv` — the
NYC-metro (`_downstate` sentinel: Central Park / LaGuardia / JFK) TMAX-only
aggregate (see `data/dictionary/data-dictionary.md`'s `weather` section).

**Source:** NOAA GHCN-Daily (public domain, CC0-1.0 — see
`docs/data-licensing.md` §2).

**Regeneration:** `python scripts/fetch_zone_temperature.py --iso NYISO` —
same generic per-ISO fetcher used by every `<iso>-weather/` directory.

**Consumers:** `scripts/curate_weather.py`,
`scripts/derive_nyiso_ct_reliability_floor.py`,
`scripts/derive_nyiso_st_reliability_floor.py` (legacy per-ISO consumers).
