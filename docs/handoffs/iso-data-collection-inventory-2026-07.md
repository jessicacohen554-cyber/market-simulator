# ISO data-collection inventory: 2023–2025 baseline vs 2021 / 2022 / H1-2026 holdout gaps (2026-07-07)

**Purpose.** A per-ISO, per-datatype inventory of what is on disk in `data/raw/`
for the current 2023–2025 calibration window, and what is missing for the
years a holdout-fidelity test would need: **2021**, **2022**, and **H1-2026**.
Read-only audit — no fetch, derive, solve, or intake was run to produce this.

**Policy framing (read before acting on any row below).** CLAUDE.md rule 22
designates exactly **2022 and H1-2026** as quarantined holdouts. Under the
2026-07-06 Option-2 decision (`docs/handoffs/holdout-policy-memo-2026-07.md`
§e), **data intake** for those two windows is owner-authorized/no-LP-allowed
at any time, but **solving or scoring** them is blocked per-ISO until that
ISO carries a `declared` entry in
`frontend/data/backcast/calibration-complete.json` — today only **NEISO**
(2026-07-07). **2021 is not a rule-22 holdout at all** — `CALIBRATION_YEARS`
in `scripts/data/build_calibration_reference.py` already spans 2021–2025 as a
default, and ERCOT/PJM's reference-year builder already resolves 2021 today.
Treating 2021 as a third holdout is a new policy choice this doc doesn't make
for you — flagged explicitly in §4.

---

## 1. Per-ISO in-sample calibration years (baseline, for reference)

| ISO | Calibration years (`CALIBRATION_YEARS_BY_ISO`) | Note |
|---|---|---|
| ERCOT | 2023, 2024, 2025 (falls back to default `(2021,2022,2023,2024,2025)` but keeper recipes only ever solve 2023-2025) | reference calibrator; the CAMPD reference case |
| PJM | 2023, 2024, 2025 | same default fallback |
| CAISO | 2023, 2024, 2025 | explicit override |
| MISO | 2023, 2024, 2025 | explicit override |
| **NYISO** | **2023, 2025 — 2024 is skipped** | not a holdout issue; NY_2024 CEMS unit-outage gating is an **open in-sample gap**, unrelated to 2021/2022/2026 |
| NEISO | **2022**, 2023, 2024, 2025 | first ISO with `calibration-complete` marker (2026-07-07); 2022 added as the authorized one-shot holdout target, not a calibration year |

---

## 2. What's collected for 2023–2025 (the baseline every ISO has)

This is the common floor. Every ISO below has, for **2023, 2024, 2025**, full
or effectively-full coverage of:

| Category | Datatype | Path pattern |
|---|---|---|
| Driver | Hourly demand (EIA-930 wide bench) | `eia-930-hourly/{BA} hourly.parquet` |
| Driver | Zone-level daily temperature (tmin/tmax) | `{iso}-weather/{iso}_zone_temp_daily.csv` |
| Driver | Henry Hub + citygate gas basis | `gas-prices/henry_hub_*.csv`, `gas_basis_by_iso_month.csv` |
| Driver | Zone-specific metered load | `zone-specific-demand/` (ISO-specific format) |
| Fleet | CAMPD unit-level hourly CEMS (binning) | `campd-unit-level/{STATE}_{YEAR}.parquet` |
| Fleet | eGRID fossil emission-rate vintage | `fleet-egrid/egrid2023_data_rev2 2.xlsx` (+ 2022/2024) |
| Overlay | Derived unit-outage windows | `campd-unit-outages{,-<ISO>}.csv` |
| Overlay | Ancillary-services clearing (ERCOT/PJM/MISO/NYISO) | `{iso}-AS/` |
| Overlay | HSL / curtailment (ERCOT/CAISO) | `{iso}-hsl/`, `caiso-curtailment/` |
| Overlay | Capacity-deliverability planning parameters | `capacity-deliverability/` |
| Bench | EIA-930 fuel-mix actuals | same `eia-930-hourly` file |
| Bench | LMP actuals (DA/RT) | `lmp-data/{ISO}/` |
| Bench | Per-plant coal pricing / CO2 rate overlays | `_processed-legacy/*.parquet` |
| Bench | Renewable-capacity validation | `_validation-source/renewable_capacity_{ISO}.csv` |

This is the floor a 2021/2022/H1-2026 solve needs to match before the year is
"scorable" per the same standard 2023-2025 is scored on today.

---

## 3. Gap matrix — what's missing for 2021 / 2022 / H1-2026, by ISO

Legend: ✅ present & full · ⚠️ present but partial/broken · ❌ absent

### 3a. Fleet & bench (CAMPD unit-level CEMS — the binning + generation-actuals backbone)

| ISO (CAMPD states) | 2021 | 2022 | H1-2026 |
|---|:--:|:--:|:--:|
| ERCOT (TX) | ✅ | ✅ | ✅ (Q1 only — EPA hasn't posted Q2-2026) |
| PJM (14 states) | ✅ | ✅ | ✅ (Q1 only, all 14 states) |
| CAISO (CA) | ✅ | ❌ | ❌ |
| MISO (14 states) | ✅ | ⚠️ IL/IN/KY/MI/TX only (overlap with PJM/ERCOT intake) | ⚠️ same overlap states only |
| NYISO (NY, NJ) | ✅ | ⚠️ NJ only (NY absent) | ⚠️ NJ only |
| NEISO (ME/NH/MA/CT/RI/VT) | ✅ | ❌ — **tooling merged 2026-07-07, binary landing pending** (`.github/workflows/holdout-intake-neiso-2022.yml` not yet run/merged) | ❌ (H1-2026 not authorized yet — see memo §4) |

**Read this row carefully for MISO/NYISO**: the "partial" coverage is not a
MISO/NYISO intake — it's a side effect of ERCOT/PJM's own 2022/2026 intake
landing files for states that MISO's/NYISO's `ISO_STATES` tuple also lists
(IL/IN/KY/MI/TX overlap PJM+ERCOT; NJ overlaps PJM). No MISO- or NYISO-owned
intake has run.

### 3b. `campd-facility-level/` (facility-grain derive input)

**No ISO** has 2021, 2022, or 2026 here — only 2023–2025 exist for any state.
ERCOT and PJM don't need this (unit-level fallback covers them, confirmed
bit-for-bit equivalent per the 2026-07-04 F6 close-out); any ISO relying on
the facility-grain path for a holdout year needs this closed first or must
confirm the same unit-level fallback applies.

### 3c. EIA-930 wide bench file (`eia-930-hourly/{BA} hourly.parquet` — what `load_eia_hourly_benchmark` actually reads)

Directly checked row counts per year (2026-07-07):

| BA (ISO) | 2021 | 2022 | H1-2026 |
|---|:--:|:--:|:--:|
| ERCO (ERCOT) | ✅ 8,760h | ✅ 8,760h | ✅ 4,343h (through Jun 30) |
| PJM | ✅ 8,760h | ✅ 8,760h | ✅ 4,343h |
| ISNE (NEISO) | ✅ 8,760h | ✅ 8,760h | ⚠️ 3,359h (~mid-May cutoff, short of Jun 30) |
| NYIS (NYISO) | ✅ 8,760h | ✅ 8,760h | ⚠️ 3,912h (~early June) |
| **CISO (CAISO)** | ✅ 8,760h | ❌ **9 hours only — effectively absent** | ❌ **0 hours** |
| **MISO** | ✅ 8,760h | ❌ **7 hours only — effectively absent** | ❌ **0 hours** |

**This is the sharpest fidelity trap in the whole inventory.** The wide
bench file already carries 2021/2022 (and partial 2026) rows for ERCOT, PJM,
NEISO, and NYISO — someone could reasonably assume EIA-930 bench coverage is
uniform across ISOs. It is not: CAISO and MISO's 2022 rows are a data-quality
artifact (9 and 7 hours respectively, not a real year) and their 2026 rows
don't exist at all. Any holdout scoring run for CAISO/MISO must not silently
consume this near-empty 2022 slice — `load_eia_hourly_benchmark`'s
short-year padding (pads to 8760 with monthly means) would mask this as a
"complete" year without an explicit row-count check, exactly the honesty
gap `scripts/verify_holdout_intake.py` was built to catch for ERCOT/PJM.

The narrower per-BA-per-year supplement files
(`eia-930/{ERCO,PJM}_{fueltype,region}_2022.parquet` /`_2026.parquet`) that
back the wide file's ERCOT/PJM rows exist **only for ERCO and PJM** — no
equivalent supplement was ever fetched for CISO, MISO, ISNE, or NYIS, which
is presumably why CISO/MISO's wide-file rows are broken and ISNE/NYIS's
apparent completeness is coming from a *different*, wider historical pull
(2015–2026) rather than a targeted holdout intake.

### 3d. Derived unit-outage overlay

| ISO | 2021 | 2022 | H1-2026 |
|---|:--:|:--:|:--:|
| ERCOT (`campd-unit-outages.csv`) | ❌ (windows start 2022-01-01) | ✅ | ✅ clipped 2026-03-24 |
| PJM (`campd-unit-outages-PJM.csv`) | ❌ | ✅ | ✅ clipped 2026-03-20 |
| CAISO / MISO / NYISO / NEISO (per-ISO CSVs) | ❌ | ❌ (windows start 2023-01-01) | ❌ |

None of the four un-intaken ISOs has any 2021 or 2022 outage-window
derivation yet; ERCOT/PJM's own all-ISO/PJM files don't reach back to 2021
either (2022 is the earliest window in both).

### 3e. Delivered gas / zonal basis

| ISO | 2021 | 2022 | H1-2026 |
|---|---|:--:|:--:|
| ERCOT `ercot_zonal_gas_hub.csv` | ❌ | ✅ (F1 closed 2026-07-04) | ⚠️ partial (Jan–Apr, EIA lag) |
| PJM `pjm_zonal_gas_hub.csv` | ❌ | ✅ | ⚠️ partial (Jan–Apr) |
| MISO `miso_zonal_gas_hub.csv` | ❌ | ❌ | ❌ |
| NYISO `nyiso_zonal_gas_hub.csv` | ❌ | ❌ | ❌ |
| CAISO (no zonal hub file exists at all) | ❌ | ❌ | ❌ |
| NEISO (no zonal hub file exists at all) | ❌ | ❌ | ❌ |
| **All ISOs**, `gas_basis_by_iso_month.csv` (citygate fallback) | ✅ 2015–2026 for all 7 ISO columns incl. CAISO/MISO/NEISO/NYISO | ✅ full 12 months, all ISOs | ⚠️ 2–3 months only (EIA publication lag), all ISOs |

The **citygate fallback file already has full 2021/2022 coverage for every
ISO** — this is the one input class where CAISO/MISO/NYISO/NEISO are not
blocked, provided the model's per-ISO offer path is allowed to fall back to
citygate basis rather than requiring the finer zonal hub series.

### 3f. Weather (zone daily tmin/tmax — reliability-floor & winter-mechanism input)

**No ISO has 2021, 2022, or H1-2026 weather data.** Every one of
`ercot-weather`, `caiso-weather`, `pjm-weather`, `miso-weather`,
`nyiso-weather`, `neiso-weather` is uniformly capped to **2023-01-01 through
2025-12-31**. This blocks any ISO's temperature-conditioned reliability
floor and (for NEISO) the winter fuel-security mechanisms on 2021/2022/2026
regardless of CAMPD/EIA-930 status — a hard floor under every ISO's holdout
readiness, not just the four un-intaken ones.

### 3g. Ancillary services / HSL / LMP actuals (scoring-side, ERCOT/PJM/MISO/NYISO/CAISO)

`{iso}-AS/`, `{ercot,caiso}-hsl/`, `lmp-data/{ISO}/` are **uniformly capped
to 2023–2025** for every ISO that has them (ERCOT's raw current-year zips are
the one exception, but they aren't parsed into the 2023-2025-style parquet
yet). No 2021/2022/2026 AS-clearing or LMP-actuals data exists anywhere.
`miso-hsl/`, `pjm-energy-offers/`, `nyiso-downstate-gas/`, `ramp-capability/`
are empty (README-only) even for 2023-2025 — pre-existing gaps, not holdout-specific.

### 3h. eGRID fossil emission-rate vintage

| Vintage | Status |
|---|---|
| eGRID2022 | ✅ true 2022 vintage landed 2026-07-04 (was previously silently riding the 2024 stand-in) |
| eGRID2023 | ✅ |
| eGRID2024 | ✅ |
| eGRID2026 | doesn't exist yet (EPA hasn't published) — forward convention rides the 2024 stand-in |

Not ISO-partitioned (one national workbook per vintage) — this input is
**closed for 2022** for every ISO simultaneously; no per-ISO gap here.

### 3i. `_processed-legacy` per-plant overlays (coal pricing, CO2 rates, parasitic load)

| File | 2021 | 2022 | H1-2026 |
|---|:--:|:--:|:--:|
| `eia923_monthly_fuel_costs.parquet` / `_generation.parquet` | ❌ | ✅ (ERCOT+PJM only, per F5) | ⚠️ Jan-Apr, ERCOT+PJM only |
| `fossil_co2_rates.parquet` | ❌ | ✅ (true eGRID2022 vintage, ERCOT+PJM) | ✅ (rides 2024 stand-in, ERCOT+PJM) |
| `plant_emission_rates.parquet` (v1) | ❌ | ⚠️ Q1-weighted, ERCOT only | — |
| `plant_emission_rates_v2.parquet` (all 6 ISOs, one file) | ✅ | **❌ missing for every ISO** | **❌ missing for every ISO** |
| `parasitic_load_factors.parquet` | ❌ | ✅ ERCOT+PJM (564 rows) | ❌ deferred — CAMPD Q1 vs F923 Jan-Apr window mismatch |

`plant_emission_rates_v2.parquet` is the one overlay confirmed **entirely
absent for 2022/2026 across all six ISOs**, including ERCOT/PJM — the
2026-07-07 NEISO intake commit (`bc78449`) added the marker-gated
`--holdout-intake` escape to `derive_plant_emissions_v2.py` but the binary
merge hasn't landed yet (same pending-carrier-workflow status as §3a).

### 3j. Zone-specific metered demand

| ISO | 2021 | 2022 | H1-2026 |
|---|:--:|:--:|:--:|
| ERCOT | ❌ | ✅ (`ERCOT_Native_Load_2022.xlsx`) | ❌ (files stop at 2025) |
| CAISO | ❌ | ❌ (files start 2023) | ❌ |
| PJM | ❌ | ❌ (files start 2023) | ❌ |
| MISO | ❌ | ❌ (single combined 2023-2025 file) | ❌ |
| NYISO | ❌ | ❌ (files start 2023) | ⚠️ raw monthly zips extend to 2026-06 (unprocessed) |
| NEISO | no directory exists at all | — | — |

---

## 4. Action list to close the gaps

Ordered by what's cheapest / already has a working pattern to copy.

1. **Land the two pending NEISO 2026-07-07 carrier-workflow binaries.**
   `holdout-intake-neiso-2022.yml` (CAMPD unit-level for CT/MA/ME/NH/RI/VT
   2022, `plant_emission_rates_v2.parquet` merge, LMP rebuild) is merged to
   main but hasn't been dispatched/completed — this is the templated pattern
   (`fetch-caiso-oasis.yml`-style) for every other ISO's binary landing too.
2. **CAISO / MISO: fix the near-empty 2022 EIA-930 wide-bench rows before
   anything else.** 9 and 7 hours respectively is not a partial year, it's
   broken — re-run the per-BA-per-year fetch (`fetch_eia930_long.py`
   pattern used for ERCO/PJM 2022/2026, i.e. `CISO`/`MISO` BA codes) to
   produce the missing `{fueltype,region}_2022.parquet` supplements, the
   same mechanism that already backfilled ERCO/PJM's wide file.
3. **CAISO / MISO / NYISO: CAMPD unit-level 2022 + H1-2026 for their own
   (non-overlap) states** — same `fetch_campd_unit_level.py` pattern as the
   2026-07-04 ERCOT/PJM intake (PRs #1298/#1300/#1304). NYISO specifically
   needs `NY_2022`/`NY_2026` (currently only `NJ` landed, as a PJM-overlap
   side effect).
4. **Weather (all six ISOs): extend `{iso}_zone_temp_daily.csv` to 2021,
   2022, and H1-2026.** This is the single gap common to every ISO and
   blocks the reliability-floor / winter mechanisms uniformly — closing it
   is a prerequisite for *any* ISO's holdout solve regardless of intake
   status elsewhere, and there's no ISO-specific fetcher documented in this
   inventory to point at, so it likely needs a new/extended weather-pull
   script (cf. `docs/weather-pool-coverage-2026-07.md` if a fetcher already
   exists there — not checked in this pass).
5. **Zonal gas hub: MISO / NYISO 2022+2026; CAISO / NEISO need the file
   built at all** (falls back to the citygate `gas_basis_by_iso_month.csv`
   today, which already has 2021/2022/2026 coverage — lower priority unless
   the per-ISO keeper recipe requires the finer zonal series).
6. **Derived unit-outage overlay for CAISO/MISO/NYISO/NEISO, 2021/2022/2026**
   — depends on #3 (needs the CAMPD unit-level extract first), then
   `derive_campd_unit_outages.py --years 2022 2026` per ISO, same as the
   ERCOT/PJM 2026-07-04 run.
7. **`plant_emission_rates_v2.parquet` 2022/2026, all six ISOs** — script
   support exists (`derive_plant_emissions_v2.py --holdout-intake`, landed
   2026-07-07) but the actual merge run + binary landing is outstanding for
   every ISO, ERCOT/PJM included.
8. **2021 specifically**: no ISO has outage windows, zonal gas hub, or
   `_processed-legacy` overlays for 2021 — only CAMPD unit-level (all ISOs),
   EIA-930 wide bench (ERCOT/PJM/NEISO/NYISO only, not CAISO/MISO), citygate
   gas basis, and `eia_demand_profiles` (2021–2025 aggregate) currently
   reach back that far. Confirm with the owner whether 2021 is being added
   as a designated holdout (requires a CLAUDE.md rule-22 amendment) or is a
   separate diagnostic year outside the quarantine — the two have different
   authorization requirements before any solve.

## 5. Authorization reminder before acting on any of the above

Per rule 22 (Option 2): **intake** (items 1-7 above) is owner-authorized and
no-LP at any time — but do not skip session-logging the authorization the way
the 2026-07-04 and 2026-07-07 intakes did. **Solving or scoring** 2022/H1-2026
for any ISO still requires that ISO's `calibration-complete` marker (only
NEISO has one today) plus `run_calibration_full.py --holdout-authorized`.
**2021** has no marker mechanism at all yet — treat any 2021 solve as
requiring the same explicit sign-off pattern until the owner decides how it's
governed.
