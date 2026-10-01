# FINDING — I-NYISO: the 2019–2021 NYISO input intake — 2026-09-24

**Session:** I-NYISO (data intake, zero LP; nothing solved, nothing registered).
**Charter:** owner instruction 2026-09-24, "every ISO's backcast covers 2019–2025 on year-correct
inputs" (`docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md`), routed from
R-NYISO `docs/PRECOMMIT-r-nyiso-backcast-inputs-2026-09-24.md` §5 and
`docs/FINDING-nyiso-2020-touchpoint-data-blocked-2026-09-09.md`.

## Headline

| item | input | outcome |
|---|---|---|
| 2 | `NYISO-AS/requirements/NYISO_reserve_requirements_{2019,2020,2021}.csv` | **LANDED.** The same producer derives them from NYISO's published sources, and 2022–2025 regenerate **byte-identically** (§1). |
| 1 | `eia-930/eia_generation_profiles.parquet`, rows for 2019 and 2020 | **STOPPED, as instructed.** The committed 2021–2025 rows **cannot** be reproduced byte-identically from any EIA-930 vintage in the repo. The construction was recovered, and 40 of the 140 EIA-930 rows reproduce exactly. The rest differ because EIA has revised the source values since the table was built (§2). **No row was emitted, and the parquet is untouched.** |

**NYISO year status after this PR:**

- **2021 is UNBLOCKED.** Its generation-profile rows already exist, and its reserve file now exists.
- **2019 and 2020 stay blocked on item 1 alone.** Their reserve files now exist.

---

## 1. Item 2: NYISO reserve requirements, 2019–2021 (landed)

### 1.1 The new source: NYISO's own document-version history

nyiso.com serves the Locational Reserve Requirements posting's Liferay version history at
`…/documents/20142/3694424/Locational-Reserves-Requirements.pdf?version=N`. Each version below was
fetched, md5-hashed and dated from its PDF CreationDate:

| NYISO version | created | md5 | relation to the committed corpus |
|---|---|---|---|
| 1.1 | 2016-08-17 | `6af6bb9b…` | **NEW**, committed as `lrr_nyiso_v1.1_20160817.pdf`. Transcribed as `v2016`: no NYC region, SENY 30-min flat 1,300 (TSA → 0) |
| 1.2 | 2019-06-24 | `53485df7…` | **NEW**, committed as `lrr_nyiso_v1.2_20190624.pdf`. Transcribed as `v2019`: NYC 500/1,000 added; every value equals v1.3 |
| 1.3 | 2020-08-06 | `5d57fe6d…` | byte-identical to `lrr_wayback_20201029.pdf` (`v2020`) |
| 1.4 | 2021-06-17 | `0436d93d…` | byte-identical to `lrr_wayback_20211204.pdf` (`v2021`) |
| 2.0 / 2.1 | 2026-05-13 | `7c1d0e2a…` | byte-identical to `lrr_retrieved_20260710.pdf` (`v2026`) |
| 3.0 | 2026-09-09 | `4dca607f…` | **not transcribed.** 2026 only, outside the backcast span. Named here for the next 2026 lane |

The version chain corroborates the existing transcription: every committed PDF is one of NYISO's own
versions.

### 1.2 Sourced effective dates

These are the new `effective_start` / `effective_source` columns, schema v2.

- **`v2019`: 2019-06-26.** NYISO activated the NYC locational reserve region in the day-ahead and
  real-time markets on Wednesday 2019-06-26. Source: S&P Global, 2019-06-24, republished on nyiso.com
  (*"plans to activate Wednesday a new locational reserve region for New York City"*). Before that
  date, NYC 10-min and 30-min requirements are **0 MW**, because v1.1 publishes no NYC region.
- **`v2020`: 2020-08-06**, the v1.3 CreationDate. Every requirement value is identical to v1.2, so
  this boundary changes no number.
- **`v2021`: 2021-06-17**, from FERC **ER21-625** ("SENY reserve enhancements"):
  - -001 set 2021-06-08;
  - -002 delayed it to 2021-06-10;
  - **-003 (filed 2021-06-08, 86 FR 2021-12370) delayed it to 2021-06-17.** This is the last notice
    in the docket.

  The v1.4 posting is created the same day, at 12:41 ET. The README's earlier guess of "plausibly
  2021-07-13" was the unrelated ORDC compliance date, and is superseded.

### 1.3 Producer change: the same derive, now stitching versions at sourced dates

`scripts/data/derive_nyiso_reserve_requirements_hourly.py`:

- `select_version` becomes `select_regimes`. A version is in force from its `effective_start` (or
  its `evidence_start` when none is sourced) until the next version starts.
- **A version that begins mid-year is admitted only when its `effective_start` is sourced.** An
  unsourced boundary still raises the old error. This keeps the old guard's intent: *"a mid-year
  requirement change must be handled explicitly, never averaged away."*
- A region the in-force version does not publish is 0 MW, and each such case is logged.
- Every year 2022–2025 is still a single regime (`v2021`), and the per-hour arithmetic is unchanged.

### 1.4 Byte-identity proof, 2022–2025

`curate_nyiso_reserve_requirements.py` was run, then `derive_nyiso_reserve_requirements_hourly.py`
on the new transcription and code. `cmp` against the committed files:

| year | sha256 (committed = regenerated) |
|---|---|
| 2022 | `713fd34818781799e863a5cd187fceb66bd2612d0d41a9fb6e52dae0823ed987` |
| 2023 | `2459531da0190d6b1cc3cdd74cc9d49363b3961009772b3129e23f4230df001d` |
| 2024 | `2f572bb2d7e5c2ac4e3597de999e3d06b21cf1c2658f555f79652f2e108db2b1` |
| 2025 | `ca91f137c74294102dd41a71466430a247fffd991bba83e9fd27824ab4358678` |

The pre-change producer was also run first and reproduced the same four files, so the baseline was
confirmed before any edit.

### 1.5 The new files

Each file has 7 series × 8,760 h = 61,320 rows and loads through `load_nyiso_reserve_requirements`.

| year | regimes | TSA windows / hours touched | notable |
|---|---|---|---|
| 2019 | `v2016` to 2019-06-25, then `v2019` | 19 / 100 | NYC total_10 / total_30 are 0 MW for 4,224 h, then 500 / 1,000 |
| 2020 | `v2019` then `v2020` (numerically identical) | 18 / 78 | SENY 30-min flat 1,300; NYC not TSA-zeroed |
| 2021 | `v2020` to 2021-06-16, then `v2021` | 29 / 138 | SENY 30-min steps from 06-17 (e.g. Jun-20 noon 1,800); NYC TSA-zeroing from 06-17 |

sha256 values:

- 2019: `55111df1…0884e`
- 2020: `47eb7d0b…ded6e`
- 2021: `ad36ccfc…0cdee`

The same caveat applies as for 2022–2025: this is the published schedule plus TSA zeroing, i.e. a
documented **lower bound** (the RTD/RTC increments are the still-open B1 request).

**Tests:** `tests/curation/test_derive_nyiso_reserve_requirements_hourly.py` has 13 passing tests.
New tests cover:

- a sourced boundary splitting the year;
- an unsourced boundary raising;
- an uncovered year raising;
- the piecewise derive with a 0-MW pre-activation region.

The curate, data-dictionary-sync and clean-io suites also pass.

---

## 2. Item 1: `eia_generation_profiles.parquet` (STOPPED; closest reconstruction and its diff)

### 2.1 The recovered construction

The code is `scripts/data/reconstruct_eia_generation_profiles.py`. It is **verify-only and never
writes the artifact.**

The table is **two constructions stacked**, each recovered from the committed rows by measurement.

**`local6`: CAISO, ERCOT, PJM, NYISO, NEISO.**

- **Source:** EIA-930 BALANCE `Net Generation (MW) from <fuel>` for the ISO's BA. The legacy and
  2024-H2+ split taxonomies are coalesced.
- **Clock:** the first 8,760 local wall-clock hours. Row `i` is the hour ending at local `i:00`. A
  leap year keeps Feb 29 and loses Dec 31.
- **Truncation:** the source stops at UTC hour-end `<Y>-12-31T01`. That hour and the spring-DST gap
  hour are forward-filled.
- **Value:** `round(x / Σx, 6)`.
- **All-zero series:** a uniform `round(1/8760, 6)`. This is the NYISO solar row, because NYIS
  reports no solar.

**`utc10`: MISO, SPP.**

- **Clock:** UTC hour-end `<Y>-01-01T00…12-31T23`, with Feb 29 dropped.
- **Missing hours:** 0.
- **Value:** `round(x / Σx, 10)`.

**Not constructible from EIA-930:**

- `offshore_wind`: one synthetic profile repeated every year;
- CAISO `geothermal`;
- NYISO `solar_proxy`, which nothing under `src/` reads.

### 2.2 The diff

There are 170 committed rows; 140 have an EIA-930 series. **40 of those 140 are byte-exact**, and
1,061,501 of 1,226,400 cells match (86.55 %).

**% of hours exact, per ISO and year:**

| ISO | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| CAISO | 88.0 | 88.8 | 95.5 | 81.4 | 90.7 |
| ERCOT | 96.5 | 98.2 | 89.5 | 69.0 | 81.9 |
| MISO | **100** | **100** | **100** | **100** | **100** |
| NEISO | 91.9 | 95.7 | 98.1 | 70.5 | 95.7 |
| NYISO | 99.6 | 95.2 | 97.9 | 70.8 | 98.6 |
| PJM | 95.1 | 71.5 | 76.7 | 74.6 | 99.4 |
| SPP | **100** | **100** | **100** | 10.2 | 8.8 |

**Rows that are byte-exact:**

- MISO: all 20;
- SPP 2021–2023: 12;
- NYISO solar, all 5 years;
- NEISO 2021 solar;
- PJM 2021 solar;
- CAISO 2025 nuclear.

**The two rows NYISO's 2019/2020 solve actually reads** are NYISO `solar` (degenerate) and its donor
NEISO `solar`:

- **NYISO solar:** exact in all 5 years.
- **NEISO solar:**

  | year | exact hours | residual |
  |---|---|---|
  | 2021 | 8,760 / 8,760 | none |
  | 2022 | 8,755 | 1 × 10⁻⁶ in the others |
  | 2023 | 8,739 | 1 × 10⁻⁶ in the others |
  | 2024 | 7,928 | up to 4.3 × 10⁻⁴ |
  | 2025 | 8,702 | 1 × 10⁻⁶ in the others |

  The residuals are one unit of the 6-decimal rounding, except in 2024.

### 2.3 Why the residual is not a construction error: the source values moved

Three measurements point to a different source vintage, not a different rule:

- **SPP 2025 nuclear.** It follows the same `utc10` rule that is exact for 2021–2023, yet 199 hours
  differ. The differences are the source values themselves: e.g. 2025-03-01 08:00 UTC, where BALANCE
  reads 2,025 MW and the table implies 2,021 MW. They cluster in the months EIA later revised
  (Mar–Sep).
- **The local6 rows.** For each row, the interval of denominators `D` for which
  `round(x/D, 6) == table` holds in every hour either **excludes** the sum of the on-disk series or is
  empty. Examples:
  - CAISO 2023 solar: feasible `D` ∈ [37,296,804, 37,296,854], against an on-disk Σ of 37.39 M;
  - NEISO 2021 wind: the interval is empty.

  So the builder's series had different hourly values or totals. Per-hour mismatches sit one
  rounding unit off, or at isolated revised hours.
- **The per-BA long-format API pulls are gone.** These are the `<BA>_{fueltype,region}_<year>.parquet`
  files the table was evidently built from, including the Dec-31 T01Z truncation, which fits an API
  pull that ended there (an inference, not measured). They were untracked by BLOAT-S2 and **stripped from history by the 2026-08-16 rewrite**
  (`data/raw/eia-930/README.md`, whose recovery route is re-fetch only). A re-fetch returns EIA's
  *current* vintage, which is the one measured above. `api.eia.gov` is also blocked in CCR sessions.

**Conclusion: byte-identical reproduction of 2021–2025 is impossible from anything the repository
holds.** This is not a matter of more reconstruction effort.

### 2.4 What would unblock 2019/2020: an owner decision, not more intake

Each option is stated at its true cost:

- **(a) Emit 2019/2020 additively with the recovered construction** (MISO/SPP exactly; local6 rule
  for the rest), leaving 2021–2025 untouched.
  - **Cost:** the new years are built on EIA's current vintage while 2021–2025 sit on an older one.
    That is two vintages in one table.
  - The artifact would **not** have a producer that reproduces it end to end.
- **(b) Re-base the whole table** on the current EIA vintage with this producer (2019–2025).
  - **Cost:** every ISO's 2021–2025 rows move, by one 6-dp unit in most local6 hours and more in
    2024. Every keeper that reaches this fallback would then have moved inputs.
  - The keepers that reach it are the NYISO solar path, and any ISO/fuel whose own BA series is
    empty.
- **(c) Obtain the builder's original API pulls** from wherever they still exist, outside this
  repository.

This session did none of them. Option (a) is the smallest move, but it is exactly the
"different construction" risk the charter told this lane to stop on.

---

## 3. Files

**Item 2:**

- `data/raw/NYISO-AS/requirements/`:
  - `NYISO_reserve_requirements_{2019,2020,2021}.csv` (new);
  - `nyiso_locational_reserve_requirements.csv` (+`v2016`, +`v2019`, +`effective_start` /
    `effective_source`);
  - `locational-reserve-requirements/lrr_nyiso_v1.{1,2}_*.pdf` (new);
  - `README.md`.
- `data/dictionary/schema/nyiso-reserve-requirements.schema.yaml` (v2), plus the regenerated
  `data-dictionary.md` and `scripts/render_data_dictionary.py`.
- `scripts/data/`:
  - `derive_nyiso_reserve_requirements_hourly.py`;
  - `curate_nyiso_reserve_requirements.py`;
  - `fetch_nyiso_lrr_pdfs.py` (md5-pinned v1.1 / v1.2; both re-fetched and matched in this session).
- `tests/curation/test_derive_nyiso_reserve_requirements_hourly.py`.

**Item 1:**

- `scripts/data/reconstruct_eia_generation_profiles.py` (verify-only);
- a pointer paragraph in `data/raw/eia-930/README.md`.

**`eia_generation_profiles.parquet` is unchanged**, so every ISO's rows are trivially
byte-identical.
