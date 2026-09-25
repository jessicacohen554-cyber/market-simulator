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
| CISO | CAISO | 2018-01-01 .. 2026-06-30 (2019-2021 backfilled 2026-07-06; 2018 + H1-2026 landed 2026-07-08; **2022 filled 2026-07-31**) |
| MISO | MISO | 2018-01-01 .. 2026-06-30 (2019-2021 backfilled 2026-07-06; 2018 + H1-2026 landed 2026-07-08; **2022 filled 2026-07-31**) |
| SOCO | SOCO (Southern Co balancing authority) | 2018-12-31 .. 2025-12-31 (**2019-2022 folded in 2026-09-24, I-SOCO**, from the committed BALANCE archive by `scripts/data/extend_eia930_hourly_from_balance.py --ba SOCO --year 2019 --year 2020 --year 2021 --year 2022`; see below) |
| FLA | — (Florida, not a modeled ISO) | 2022-12-31 .. 2025-01-31 |
| BPAT | — (NWPP, not a modeled ISO) | 2019-01-01 .. 2025-12-31 (derived 2026-09-13, NWPP-11; 2019-2022 added 2026-09-24, R-NWPP) |
| PACE | — (NWPP, not a modeled ISO) | 2019-01-01 .. 2025-12-31 (derived 2026-09-13, NWPP-11; 2019-2022 added 2026-09-24, R-NWPP) |
| PACW | — (NWPP, not a modeled ISO) | 2019-01-01 .. 2025-12-31 (derived 2026-09-13, NWPP-11; 2019-2022 added 2026-09-24, R-NWPP) |
| PGE | — (NWPP, not a modeled ISO) | 2019-01-01 .. 2025-12-31 (derived 2026-09-13, NWPP-11; 2019-2022 added 2026-09-24, R-NWPP) |
| PSEI | — (NWPP, not a modeled ISO) | 2019-01-01 .. 2025-12-31 (derived 2026-09-13, NWPP-11; 2019-2022 added 2026-09-24, R-NWPP) |
| AVA | — (NWPP, not a modeled ISO) | 2019-01-01 .. 2025-12-31 (derived 2026-09-13, NWPP-11; 2019-2022 added 2026-09-24, R-NWPP) |
| IPCO | — (NWPP, not a modeled ISO) | 2019-01-01 .. 2025-12-31 (derived 2026-09-13, NWPP-11; 2019-2022 added 2026-09-24, R-NWPP) |
| NWMT | — (NWPP, not a modeled ISO) | 2019-01-01 .. 2025-12-31 (derived 2026-09-13, NWPP-11; 2019-2022 added 2026-09-24, R-NWPP) |
| CHPD | — (NWPP, not a modeled ISO) | 2019-01-01 .. 2025-12-31 (derived 2026-09-13, NWPP-11; 2019-2022 added 2026-09-24, R-NWPP) |
| DOPD | — (NWPP, not a modeled ISO) | 2019-01-01 .. 2025-12-31 (derived 2026-09-13, NWPP-11; 2019-2022 added 2026-09-24, R-NWPP) |
| GCPD | — (NWPP, not a modeled ISO) | 2019-01-01 .. 2025-12-31 (derived 2026-09-13, NWPP-11; 2019-2022 added 2026-09-24, R-NWPP) |
| SCL | — (NWPP, not a modeled ISO) | 2019-01-01 .. 2025-12-31 (derived 2026-09-13, NWPP-11; 2019-2022 added 2026-09-24, R-NWPP) |
| TPWR | — (NWPP, not a modeled ISO) | 2019-01-01 .. 2025-12-31 (derived 2026-09-13, NWPP-11; 2019-2022 added 2026-09-24, R-NWPP) |
| AVRN | — (NWPP, not a modeled ISO) | 2019-01-01 .. 2025-12-31 (derived 2026-09-13, NWPP-11; 2019-2022 added 2026-09-24, R-NWPP) |
| GRID | — (NWPP, not a modeled ISO) | 2019-01-01 .. 2025-12-31 (derived 2026-09-13, NWPP-11; 2019-2022 added 2026-09-24, R-NWPP) |
| WAUW | — (NWPP, not a modeled ISO) | 2019-01-01 .. 2025-12-31 (derived 2026-09-13, NWPP-11; 2019-2022 added 2026-09-24, R-NWPP) |
| NEVP | — (NWPP, not a modeled ISO) | 2019-01-01 .. 2025-12-31 (derived 2026-09-13, NWPP-11; 2019-2022 added 2026-09-24, R-NWPP) |

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

## PJM per-family input-clock convention + DEBUG-B repair (2026-08-15)

The wide extract places each hour hour-ending: a row's `UTC time` labels the
end of the hour `[T-1h, T)`, so `_eia_hourly_frame` sorting by `UTC time` puts
that row on the model's fixed standard-time (EST) chronological slot for
`T-1h`. This is the intended convention for **both** the region family (`Demand`
/ `Demand forecast` / `Net generation` / `Total interchange`) and the fueltype
family (`NG: <code>`).

### History — why the M-1 table below was superseded before it ever applied

The 2026-07-15 M-1 diagnosis
(`docs/DIAGNOSIS-pjm-2025-phase-drift-and-zonal-structure-2026-07.md` §1b) found
**two** independent clock defects in the then-committed PJM rows, anchored
against PJM `hrl_load_metered`, the PJM gen-by-fuel feed, the EIA-930 BALANCE
archive's explicit hour-ending UTC, and the sun:

- **2023 region family — one position LATE** (an hour-beginning/hour-ending
  label mix-up in *that vintage's* construction);
- **fueltype family — one hour EARLY at the EIA-930 source through 2024**
  (fixed upstream ~Feb-2025); July solar generation-weighted centroid ~10.9
  against the astronomically-fixed ~11.9.

Because those two errors offset each other in 2023, M-1's transform was
*2023 region −1 h, 2024 fueltype +1 h, everything else kept*. **That patch was
never applied.** It is archived unapplied at `patches/archive/pjm-m1-code.patch`
(note: `patches/archive/ARCHIVED-2026-08-14-pjm-m1.md`), and the gate figures an
earlier revision of this section quoted were its *predicted* post-repair state,
not a measured property of any committed file.

Meanwhile the committed parquet was **replaced** (last touch PR #3852's lane,
merged 2026-08-10) in a way that healed the region family in all years — and
thereby **exposed** the source's 1 h-early fueltype clock in 2023 that the
offsetting construction error had been masking. Both of M-1's premises died: its
*2023 region −1 h* leg would now double-shift an already-correct family, and its
*2023 fueltype kept* leg would leave the live defect in place.

### The live convention — DEBUG-B repair

Re-measured on main @ `c447199` with the repo's own instruments
(`scripts/probes/_pjm2025_phase_drift.py`, `scripts/probes/_pjm2025_wind_anchor.py`):
the region family is aligned at best-lag 0 in every year and season, and the
`NG: *` fueltype family is one hour early in local-2023 **and** local-2024
(July centroid 10.91 / 10.94; wind/solar/gas diff-lag +1 vs the PJM UTC feed).

**DEBUG-B repair** (`scripts/data/extend_eia930_hourly_from_balance.py
--rebuild-pjm-input-clock`, value-preserving UTC-time re-placement — each cell
keeps its measured value and only moves to the UTC hour it belongs to; rules
13/14, chartered by
`docs/handoffs/debug-b-pjm-input-clock-charter-2026-08.md` under owner decision
D-5):

| year | region family | fueltype family |
|---|---|---|
| 2023 | **kept** (already aligned — do not shift) | shifted **+1 h** (corrects the source's 1 h-early) |
| 2024 | **kept** (already aligned) | shifted **+1 h** (corrects the source's 1 h-early) |
| 2025 | kept | kept (source fixed ~Feb; **Jan-2025 straddles** the upstream switch, centroid 11.15 — left as measured, no fabricated sub-month shift) |

Both shifted blocks are sourced from the *pristine* pre-repair frame, never from
the accumulating output: 2023 and 2024 are adjacent, so sourcing sequentially
would double-shift the single boundary hour `2024-01-01 06:00Z`.

Post-repair gates (source-anchored, residual-blind — never the backcast fit):

| gate | 2023 | 2024 | 2025 |
|---|---|---|---|
| July `NG: SUN` centroid, gate [11.5, 12.3] | 11.90 | 11.93 | 12.03 |
| wind / solar / gas diff-lag vs the PJM UTC feed | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| demand daily-peak mode-0 vs `hrl_load_metered` (≥95 %) | 96.7 % | 97.0 % | 97.0 % |

Byte-verified: of 74,470 rows × 16 columns, the 8 non-fueltype columns (region
family and all four time columns) are identical pre/post at **every** row, the 8
`NG: *` columns are identical at every row outside local-2023/2024 (56,927 rows),
and inside the two shifted blocks (17,543 rows) each cell equals the pristine
value at UTC `T−1h`. NaN count unchanged (49,305). 2022 and earlier are
untouched — see the scope note below.

The four PJM DataMiner read sites that indexed the prevailing
`datetime_beginning_ept` stamp — `pjm_net_interchange`, `pjm_zonal_interchange`
and `pjm_neighbor_interchange` in `src/market_sim/data/eia930/envelopes.py`, and
`parse_pjm_shares` in `scripts/data/curate_zonal_shares.py` — were switched to
the files' own `datetime_beginning_utc` on the same fixed-EST clock
(`Etc/GMT+5`) via `_pjm_utc_hoy`. Measured effect on the interchange files:
byte-identical placement outside DST (67,078 rows/yr) and exactly one hour
earlier inside it (~125,600 rows/yr). `parse_pjm_shares` also gained a `notna()`
guard so unparseable stamps are dropped rather than silently mapped.

**Scope note (open, for the owner).** The extract carries 2018-2026, and the
1 h-early source clock affects **every year before 2025**, not just the two this
repair shifts: the July `NG: SUN` centroid still reads ~10.7 in 2022 (and
similarly early in 2018-2021). The DEBUG-B charter scopes the repair to
local-2023/2024 — the solve span — so those years are deliberately left
as-measured here rather than silently widened. Any lane that trains or validates
PJM on ≤2022 fueltype data is still on the early clock and should charter the
same value-preserving `+1 h` extension first.

## CISO/MISO 2022 fill (2026-07-31)

The 2026-07-08 pass landed the 2022 **long-form** files but its wide extension
covered only 2018 + H1-2026, so `CISO hourly.parquet` carried **9** rows of
local-2022 and `MISO hourly.parquet` **6** — the Jan-1 UTC-boundary spillover
alone, while every other year 2018-2026 was dense. Any wide-extract consumer
silently saw an empty 2022 and fell through to a fallback; for `load_demand`
that fallback was the "corrupted legacy `eia_demand_profiles`" path, with its
own warning.

Filled from the already-landed long-form raws with
`build_eia930_hourly_from_raw.py --ba {CISO,MISO} --fill-years 2022`, a new
flag: keep every existing row byte-identical and splice in only the MISSING
hours of the named local years. `--append-only` cannot reach a hole in the
MIDDLE of an extract (it starts from the last UTC hour), and a plain rebuild
would have rewritten the committed 2023-2025 rows.

    CISO: kept 65,711 rows byte-identical, spliced 8,751 -> local-2022 = 8,760
    MISO: kept 65,712 rows byte-identical, spliced 8,753 -> local-2022 = 8,760

Every pre-existing row verified value-identical before/after for both BAs.
CAISO and MISO 2022 demand now come off the real per-BA extract. Rule-22
Option-2 intake (owner-authorized 2026-07-31), no-LP validation only.

The fill also flushed out a latent `parse_miso_shares` bug the empty 2022 had
been masking — see `scripts/data/curate_zonal_shares.py` and
`docs/iso-2022-holdout-data-availability-audit-2026-07.md` §7.1.

## The 17 NWPP balancing authorities (2026-09-13, NWPP-11)

`BPAT PACE PACW PGE PSEI AVA IPCO NWMT CHPD DOPD GCPD SCL TPWR AVRN GRID WAUW
NEVP`, 2023-2025, **DERIVED from the committed BALANCE archive — no fetch, no
`EIA_API_KEY`, no network call** (`docs/multi-iso/nwpp-addition-plan-2026-09.md`
§2.5, §6 row 2; `docs/handoffs/FINDING-nwpp-11-2026-09-13.md`). Every one of the
17 is already present in `data/raw/eia-930/EIA930_BALANCE_<yr>_<half>.parquet`,
which covers 2019-01 .. 2026-06 for all 62 EIA-930 BAs, so the per-BA load spine
for this footprint is a derive from bytes the repo already holds:

    python scripts/data/build_nwpp_ba_hourly_from_balance.py --all-nwpp

That script is the **create** counterpart of `extend_eia930_hourly_from_balance
.py`'s **extend**: the latter reads an existing extract to learn the target
column layout and so cannot open a BA that has none. Every value mapping is
imported from it and reused verbatim (rule 23 `[R-FROZEN-DERIVE]`).

**Two properties of these files differ from the older siblings — both
deliberate, both documented rather than chosen:**

1. **Three APPENDED columns**: `Demand (Adjusted)`, `Net generation (Adjusted)`,
   `Total interchange (Adjusted)`, carrying EIA's own screened/imputed region
   series alongside the raw one. The plan's §2.5 defect screen found 30 bad
   hours in 394,424 (worst: AVA 810,948 MW at 2025-10-12 10:00 UTC against a
   ~2.5 GW true peak; NWMT 100,285; NEVP ~68-70 GW in six hours; PACE 65,826;
   SCL -54,511), and the `(Adjusted)` family screens every one of them — the
   per-BA raw/adjusted peaks are in the FINDING's table. **NWPP-10 owns the
   ruling on which family every downstream NWPP series reads**; until it lands,
   both are carried, complete and unchosen. All three region series are carried
   rather than demand alone so the `D = NG - TI` triple stays internally
   consistent whichever family is selected. Note the `(Adjusted)` series is
   *imputed as well as screened*, so it can be LARGER than the raw one (SCL
   2025: 9.476 vs 9.420 TWh).
   The first 17 columns are byte-identical in name, order and arrow type to
   `SWPP hourly.parquet`, asserted at write time by the script's
   `verify_schema`.
2. **No `NG: GEO` column.** The siblings' 17-column layout has none, the
   pre-mid-2024 taxonomy does not break geothermal out at all, and adding the
   column would make the same energy jump from `NG: OTH` to `NG: GEO` at the
   2024 H2 boundary. Folding it into `NG: OTH` in both eras is
   `extend_eia930_hourly_from_balance`'s own `_NEW_OPTIONAL_MAP` convention.
   Measured magnitude: **IPCO only, 240,452 MWh over 2024H2-2025**; every other
   NWPP BA reports zero.

**The taxonomy split is load-bearing and is the one real trap here.**
`build_new_rows` detects EIA's mid-2024 revamp with `any("Excluding Pumped
Storage" in c)` over the *concatenated* frame, so a single call spanning the
switch reads as new-taxonomy for **all** rows and returns NaN for every legacy
row's hydro, coal, solar and wind (measured: BPAT 2023-01-01 01:00 local, real
`NG: WAT` 5,324 MW arriving as NaN). The create script therefore calls it once
per `(year, half)` and concatenates. Era boundary at this pin, detected from
each file's own schema, never assumed: **legacy = 2023 Jan_Jun, 2023 Jul_Dec,
2024 Jan_Jun (44 cols); new = 2024 Jul_Dec onward (65 cols)**.

**Reconciliation gate — all 17 BAs x 3 years pass at exactly zero.** The derive
selects, renames and narrows to the sibling schema's float32; it never
transforms a value, so the gate is element-wise exact identity against the
BALANCE source (`mismatched_hours` and `unmatched_hours` both 0) plus a
zero-to-the-MWh annual residual on both the raw and adjusted demand series.
Hour grids are complete: 8,760 / 8,784 / 8,760 rows per BA per year.
Footprint demand 284.26 / 291.58 / 294.87 TWh (2023/2024/2025).

**AVRN and GRID are generation-only balancing authorities** — `Demand` is null
in all 26,304 hours of each, in the source and therefore in these files. That is
structure, not a gap: they hold generation (AVRN 2,848.7 MW wind/solar, GRID
689.4 MW) and no load, and they are not zone candidates on the load side.
Nothing is padded or interpolated to hide it.

### 2019-2022 added (2026-09-24, lane R-NWPP)

Same script, same BALANCE archive, run over 2019-2025:

    python scripts/data/build_nwpp_ba_hourly_from_balance.py --all-nwpp --force \
        --year 2019 --year 2020 --year 2021 --year 2022 --year 2023 --year 2024 --year 2025

Every BA-year reconciles to the BALANCE source with zero residual (raw and
`(Adjusted)`), and every committed 2023-2025 row is **byte-identical** after the
rebuild (verified row-for-row, all 17 files). Owner instruction 2026-09-24: every
backcast year 2019-2025 (`docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md`
§5.3.5).

**A source gap, carried as-is and never padded:** PSEI's `Demand (Adjusted)` is
missing for **8,659 of 8,784 hours of 2020** (raw `Demand`: 8,734 missing) and for
384 hours of 2019 (longest run 192 h). Its fuel-type `NG:` columns are complete.
The NWPP pool frame's member fill interpolates across gaps with no maximum, so
2020 pool demand would be a linear bridge over ~100 points — NWPP 2020 is
therefore not a solvable backcast year from this archive (lane R-NWPP PRECOMMIT).

## SOCO 2019-2022 (I-SOCO, 2026-09-24)

`SOCO hourly.parquet` gained 35,057 rows (local 2019-01-01 .. 2022-12-31) from
`../eia-930/EIA930_BALANCE_{2019..2022}_{Jan_Jun,Jul_Dec}.parquet`, folded in by
the committed extend path; the 26,304 committed 2023-2025 rows and the file's
column dtypes are **byte-identical** afterwards (`extend_ba` now casts the
all-NA new-taxonomy columns `NG: BAT/PS/SNB/OES` to the extract's own float32
instead of letting the concat upcast them). **Same-producer proof:** the
BALANCE path regenerates every committed row of the legacy-taxonomy era
(2023-01 .. 2024-06, 13,134 rows) exactly on every value column; its only
difference is the committed file's own `Hour` label (1..7) on the seven local
2022-12-31 rows the extend keeps untouched. From 2024-07 the two routes diverge
(EIA's taxonomy revamp and later revisions) — irrelevant here, since no
2023-2025 row is rewritten.

Measured defects AT SOURCE, carried unmodified (raw is immutable):

* **2019: 25 NaN hours** in `Demand` / `NG:*` (the loader bridges them and
  says so) and a 6,913 MW minimum-demand hour against a ~16 GW floor in every
  other year.
* **2019 Jan-Aug `Total interchange` is SIGN-INVERTED.** Monthly TI is the
  negative of both `Net generation - Demand` and the sum of the nine DIBA legs
  (Jan -300 vs +300 GWh ... Aug -369 vs +369); from September on all three
  agree. Annual: TI -1.588 TWh vs legs +6.640 TWh. EIA's live
  `EIA930_BALANCE_2019_Jan_Jun.csv` (Last-Modified 2026-09-24) carries the same
  inversion, so it is the publisher's, not this archive's. 2020-2022 TI equals
  the sum of legs to 0.001 TWh. **The SOCO solve serves `Total interchange` as
  its seam (`eia930.envelopes.soco_net_interchange`), so a 2019 SOCO solve
  would read Jan-Aug as net import — routed to the solve lane, not repaired
  here.**
