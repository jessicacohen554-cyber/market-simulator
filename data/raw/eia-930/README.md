# eia-930 — raw

EIA-930 (Hourly Electric Grid Monitor) extracts, three families:

- `EIA930_BALANCE_<year>_{Jan_Jun,Jul_Dec}.parquet` (2022–2026) — the EIA
  bulk six-month balance archive.
- `<BA>_fueltype.parquet` / `<BA>_region.parquet` (`ERCO`, `PJM` for 2022 and
  2026 — the rule-22 holdout-boundary years) — per-BA long-form fuel-type /
  region extracts; `NYIS_fueltype.parquet` / `NYIS_region.parquet` cover the
  full span.
- `eia_demand_meta.parquet`, `eia_demand_profiles.parquet`,
  `eia_demand_profiles_multiyear.json`, `eia_fossil_mix.parquet`,
  `eia_fossil_mix_multiyear.json`, `eia_generation_profiles.parquet`,
  `eia_generation_profiles_multiyear.json` — legacy hand-uploaded per-ISO
  system-total hourly demand/generation profile extracts (per
  `data/dictionary/data-dictionary.md`'s `demand-profile` entry).

**Source:** EIA-930, public domain — see `docs/data-licensing.md` §1.

**Regeneration:**
- `scripts/fetch_eia930_balance.py` — downloads
  `EIA930_BALANCE_<year>_<half>.csv` from
  `https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/` and writes
  the parquet.
- `scripts/fetch_eia930_long.py` — produces `<BA>_fueltype.parquet` /
  `<BA>_region.parquet` via EIA API v2 `electricity/rto/fuel-type-data` and
  `electricity/rto/region-data`.
- `scripts/convert_eia930.py` — pivots the long extracts into the wide
  `data/raw/eia-930-hourly/<BA> hourly.parquet` layout.
- `scripts/build_eia930_hourly_from_raw.py` — offline assembly of the same
  wide schema from these long extracts when `api.eia.gov` is network-blocked.

**No producing script found** for the `eia_demand_*`/`eia_fossil_mix_*`/
`eia_generation_profiles*` legacy files — **hand-assembled, refetch
procedure unknown.** Consumers: `scripts/curate_demand_profile.py`,
`scripts/render_data_dictionary.py`, `src/market_sim/config/constants.py`,
`src/market_sim/data/eia_loader.py`.
