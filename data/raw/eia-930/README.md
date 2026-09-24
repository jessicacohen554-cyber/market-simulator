# eia-930 — raw

EIA-930 (Hourly Electric Grid Monitor) extracts, three families:

- `EIA930_BALANCE_<year>_{Jan_Jun,Jul_Dec}.parquet` (2019–2026) — the EIA
  bulk six-month balance archive. 2019-2021 were fetched 2026-07-06
  specifically to backfill `data/raw/eia-930-hourly/{CISO,PJM,MISO} hourly.parquet`
  (see `docs/weather-pool-coverage-2026-07.md`); 2019-2021 use the legacy
  44-column taxonomy (no separate geothermal/battery/pumped-storage columns),
  vs. the 65-column taxonomy 2024H2+ files carry.
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
- `scripts/extend_eia930_hourly_from_balance.py` — prepends BALANCE-bulk years
  to an existing `<BA> hourly.parquet` (used for CISO/PJM/MISO's 2019-2021
  backfill, since `api.eia.gov` is blocked in this sandbox but the BALANCE
  bulk host isn't); never alters an already-committed row.

**No producing script found** for the `eia_demand_*`/`eia_fossil_mix_*`/
`eia_generation_profiles*` legacy files — **hand-assembled, refetch
procedure unknown.** *(2026-09-24, session I-NYISO: the construction of
`eia_generation_profiles.parquet` was recovered —
`scripts/data/reconstruct_eia_generation_profiles.py`, verify-only — and
reproduces 40 of its 140 EIA-930 rows byte-exactly (every MISO row, SPP
2021-2023, NYISO solar); the rest differ because EIA revised the source values
after the table was built, so the table is still NOT reproducible end to end
and was not extended to 2019/2020. See
`docs/handoffs/FINDING-i-nyiso-2019-2021-intake-2026-09-24.md` §2.)* Consumers: `scripts/curate_demand_profile.py`,
`scripts/render_data_dictionary.py`, `src/market_sim/config/constants.py`,
`src/market_sim/data/eia_loader.py`.

## Bulk payloads UNTRACKED at tip (BLOAT-S2, 2026-08-17)

Two payload classes are **gitignored** since the Stage-2 (a)-only untrack
(O2 grant, `docs/DECISION-CARD-bloat3-stage2-charter-2026-08-16.md`; evidence
pass `docs/FINDING-bloat-s2-evidence-passes-2026-08-17.md` §4):

- the per-BA per-year long files `<BA>_{fueltype,region}_<year>.parquet`
  (CISO/ERCO/MISO/PJM/ISNE/NYIS, incl. `NYIS_*_2025ext`) — rebuild inputs for
  the committed `data/raw/eia-930-hourly/<BA> hourly.parquet` wide extracts,
  which stay tracked (and golden-listed) and are what every solve reads;
- `EIA930_BALANCE_2018_{Jan_Jun,Jul_Dec}.parquet` — 2018 is outside the
  program's working span.

**STILL TRACKED (deliberately):** `EIA930_BALANCE_2019..2026_*.parquet`
(`derive_wecc_west_supply.py` rebuilds the clean `wecc-west-supply` datatype
from them, a CAISO solve-time input — rule-22 vintages 2019-2026 stay); the
7 hand-assembled `eia_*` files (**no producing script / refetch unknown** —
no (a) story exists, so they can never be untracked under the O2 grant); and
the unsuffixed `NYIS_fueltype.parquet`/`NYIS_region.parquet` full-span pair.

**Recovery is re-fetch ONLY** (story (a); no pin/history route). Measured
2026-08-17: the EIA bulk host served `sixMonthFiles/EIA930_BALANCE_2018_
Jul_Dec.csv` and `_2019_Jan_Jun.csv` (HTTP 200) — a stable federal archive
covering the corpus's oldest vintage. Instruments:

    # BALANCE halves (any year):
    python scripts/data/fetch_eia930_balance.py --year 2018 --half Jul_Dec
    # per-BA long files, 2018 (v2-API floor is 2019 — bulk route):
    python scripts/data/fetch_eia930_bulk_long.py --year 2018 --ba PJM ...
    # per-BA long files, 2019+ (EIA v2 API, EIA_API_KEY):
    python scripts/data/fetch_eia930_long.py ...

`api.eia.gov` is network-blocked in CCR sessions; the sixMonthFiles bulk host
(first two instruments) is reachable and is the measured route. Re-fetch
BEFORE re-running `build_eia930_hourly_from_raw.py` /
`extend_eia930_hourly_from_balance.py` (wide-extract rebuilds) or any probe
that reads the long files. `SHA256SUMS.txt` records the exact removed bytes
(a re-fetch reproduces the data, not necessarily the parquet serialization).
