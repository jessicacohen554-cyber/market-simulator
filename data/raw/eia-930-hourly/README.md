# EIA-930 per-BA wide hourly extracts

One `<BA> hourly.parquet` per EIA-930 balancing authority (built by
`scripts/convert_eia930.py` / refreshable via `scripts/fetch_eia930_hourly.py`).
Columns: `UTC time`, `Local time`, `Local date`, `Demand`, `Demand forecast`,
`Net generation`, `Total interchange`, and one `NG: <code>` column per fuel type
the BA reports. Consumed by `src/market_sim/data/eia_loader.py`
(`_eia_hourly_frame*`, `load_demand`, `load_eia_hourly_renewable_gen`, …) and
`src/market_sim/data/renewables.py` (`load_renewable_profiles`).

## Coverage on disk (checked 2026-07-08)

| BA | ISO | Span |
|---|---|---|
| ERCO | ERCOT | 2015-07-01 .. 2026-06-30 |
| ISNE | NEISO | 2015-07-01 .. 2026-05-20 |
| NYIS | NYISO | 2015-07-01 .. 2026-06-13 |
| SWPP | — (SPP, not a modeled ISO) | 2015-07-01 .. 2026-05-20 |
| PJM | PJM | 2018-01-01 .. 2026-06-30 (2019-2021 backfilled 2026-07-06; 2018 backfilled 2026-07-08) |
| CISO | CAISO | 2018-01-01 .. 2026-06-30 (2019-2021 backfilled 2026-07-06; 2018 + H1-2026 landed 2026-07-08) |
| MISO | MISO | 2018-01-01 .. 2026-06-30 (2019-2021 backfilled 2026-07-06; 2018 + H1-2026 landed 2026-07-08) |
| SOCO | — (Southern Co, not a modeled ISO) | 2022-12-31 .. 2025-12-31 |
| FLA | — (Florida, not a modeled ISO) | 2022-12-31 .. 2025-01-31 |

2018 H1 (Jan-Jun) carries demand/net-generation/total-interchange only — EIA-930
per-fuel reporting hadn't started yet for any of these three BAs (`NG: *` columns
are all `NaN`, a real reporting gap, not a fabricated split); PJM's per-fuel
reporting itself only ramps up gradually across 2018 H2 (0% of hours in
Jul/Aug, ~40% in Sep, 100% from October on) — a genuine phased-rollout
artifact of the source, not a processing bug.

## 2019-2021 CAISO / PJM / MISO backfill (2026-07-06)

The 2026-07 weather-year pool widening
(`docs/handoffs/probability-bounds-plan-2026-07.md` §2.1,
`docs/weather-pool-coverage-2026-07.md`) originally added 2019-2021 only to
ERCOT/NEISO (NYISO got 2021 only) because CAISO/PJM/MISO had no raw coverage
that far back. Extending them via `scripts/fetch_eia930_hourly.py` (EIA API
v2, `api.eia.gov`) was believed blocked by this sandbox's network allowlist
at the time (no `EIA_API_KEY` was configured in that session) — **that has
since changed: a working `EIA_API_KEY` is now present in the repo's `.env`,
and `api.eia.gov` is directly reachable (confirmed 2026-07-08). The note
below about the BALANCE bulk archive as a workaround is kept for the
2019-2021 wide-hourly backfill (still the right tool for folding years into
the wide extract), but the API itself is no longer assumed unreachable —
see the 2026-07-08 section.**

The six-month **BALANCE bulk archive**
(`www.eia.gov/electricity/gridmonitor/sixMonthFiles/`, a different host,
already used by `scripts/fetch_eia930_balance.py` for 2022+), which carries
the same demand + fuel-type generation series back to 2019. 2019-2021 were
fetched into `data/raw/eia-930/EIA930_BALANCE_{year}_{half}.parquet` and
folded into `CISO`/`PJM`/`MISO hourly.parquet` here via
`scripts/extend_eia930_hourly_from_balance.py` (never altering an
already-committed row — a UTC-time dedup keeps the pre-existing row on any
overlap, e.g. PJM's 2021/2022 boundary).

CAISO and MISO now resolve the full 2019-2021 span end-to-end (demand +
renewables); PJM's demand doesn't route through this extract at all (always
falls back to `eia_demand_profiles.parquet`, whose own floor is 2021), so
only 2021 landed in PJM's pool despite its renewables now resolving for
2019/2020 too. See `docs/weather-pool-coverage-2026-07.md`'s 2026-07-06
addendum for the full verification table and the geothermal/battery fidelity
caveat (the BALANCE bulk archive's legacy taxonomy doesn't split those out;
they fold into `NG: OTH` as `NaN`, not fabricated zero, for these three
years).

## 2018 backfill + H1-2026 extension + 2022/H1-2026 long-form intake (2026-07-08)

CLAUDE.md rule 22 was amended 2026-07-06 (Option 2,
`docs/handoffs/holdout-policy-memo-2026-07.md` §(e)) to split **data intake**
for any out-of-training year (2018, 2019, ≤2021, 2022, H1-2026) — allowed any
time, any ISO, under explicit session-logged owner authorization, validated
no-LP only — from **solve/score/registration**, which stays fully quarantined
until the ISO's `calibration-complete` marker exists. Under that authorization
(logged in `frontend/data/backcast/calibration-complete.json`'s `intake_log`),
this session:

- **Backfilled 2018** for PJM/CISO/MISO via the BALANCE bulk archive
  (`extend_eia930_hourly_from_balance.py --year 2018`, generalized from the
  2019-2021 pass to take `--year`/`--half`). 2018 H1 has no per-fuel columns
  in EIA's own source at all (see the coverage table note above); the script
  was fixed so a source year genuinely missing fuel-type columns reindexes
  them in as `NaN` (`fetch_eia930_balance.py`) instead of erroring, and so the
  `NG: OTH` fold no longer fabricates a `0` when every "other"-bucket source
  column is absent for an hour (it previously always did, via an
  unconditional `.fillna(0.0)` — a real bug, now fixed for both the legacy
  and the mid-2024-revamped BALANCE taxonomies).
- **Extended CISO/MISO through H1-2026** by folding the already-fetched
  `EIA930_BALANCE_2026_Jan_Jun.parquet` (new 65-column taxonomy) into the wide
  extracts. The extend script now maps Geothermal/Battery Storage 1:1 into
  `NG: GEO`/`NG: BAT` when the target extract carries that column (CISO has
  `NG: GEO`, MISO has `NG: BAT`), and sums the hydro/solar/wind
  pumped-storage/battery-integration splits back into the one `NG: WAT` /
  `NG: SUN` / `NG: WND` code the legacy taxonomy uses.
- **Intook CAISO/MISO 2022 and H1-2026 fuel-type/region long-form data**
  (`data/raw/eia-930/{CISO,MISO}_{fueltype,region}_{2022,2026}.parquet`) via
  `scripts/fetch_eia930_long.py` against the now-reachable `api.eia.gov`,
  matching the schema of the existing ERCO/PJM 2022/2026 siblings exactly.

All of the above is byte-identity-verified against the pre-existing
2019-2025 rows (0 mismatched cells) — no-LP intake per rule 22, not a solve
or a score.

## PJM per-family input-clock convention + M-1 repair (2026-07-15)

The wide extract places each hour hour-ending: a row's `UTC time` labels the
end of the hour `[T-1h, T)`, so `_eia_hourly_frame` sorting by `UTC time` puts
that row on the model's fixed standard-time (EST) chronological slot for
`T-1h`. This is the intended convention for **both** the region family (`Demand`
/ `Demand forecast` / `Net generation` / `Total interchange`) and the fueltype
family (`NG: <code>`). Two independent clock defects had crept into PJM's rows
(diagnosed in `docs/DIAGNOSIS-pjm-2025-phase-drift-and-zonal-structure-2026-07
.md` §1b, anchored against PJM `hrl_load_metered`, the PJM gen-by-fuel feed, the
EIA-930 BALANCE archive's explicit hour-ending UTC, and the sun):

- **2023 region family — was one position LATE** (an hour-beginning/hour-ending
  label mix-up in that vintage's construction; verified value-identical to the
  BALANCE archive placed hour-ending but shifted +1 slot). Its `Demand` peaked
  +1 h vs `hrl_load_metered`.
- **Fueltype family — was one hour EARLY at the EIA-930 source through 2024**
  (fixed upstream ~Feb-2025). July solar generation-weighted centroid ~10.9 vs
  the astronomically-fixed ~11.9.

Because the two errors offset in 2023, its fueltype was already aligned; 2024's
region was already correct. **M-1 repair** (`scripts/extend_eia930_hourly_from_
balance.py --rebuild-pjm-input-clock`, value-preserving UTC-time re-placement —
each cell keeps its measured value, only moves to the UTC hour it belongs to;
rule 13/14, cites the diagnosis, rule 23):

| year | region family | fueltype family |
|---|---|---|
| 2023 | shifted **-1 h** (→ hour-ending, aligns demand to meter) | kept (already aligned by the offsetting errors) |
| 2024 | kept (already correct) | shifted **+1 h** (corrects the source's 1 h-early) |
| 2025 | kept | kept (source fixed ~Feb; **Jan-2025 straddles** the upstream switch, centroid 11.15 — left as measured, no fabricated sub-month shift) |

Post-repair gates (source-anchored, residual-blind — diagnosis §6): demand
daily-peak mode-0 vs `hrl_load_metered` ≥95 %/yr (2023 96.4 % / 2024 96.7 % /
2025 97.0 %); July solar centroid ∈ [11.5, 12.3] each year (11.90 / 11.93 /
12.03); wind & gas diff-series best-lag 0 vs the PJM UTC feed each year. Every
cell outside the two shifted (family, year) blocks is byte-identical to the
pre-fix file (2022 and out-of-training rows untouched). The three PJM DataMiner
loaders that indexed the prevailing `datetime_beginning_ept` stamp
(`pjm_net_interchange`, `pjm_zonal_interchange` in `eia_loader.py`,
`parse_pjm_shares` in `scripts/curate_zonal_shares.py`) were switched to the
files' own `datetime_beginning_utc` on the same fixed-EST clock (byte-identical
outside DST, exactly one hour earlier inside).
