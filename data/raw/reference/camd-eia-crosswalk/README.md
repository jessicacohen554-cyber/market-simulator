# camd-eia-crosswalk — raw

The **EPA CAMD–EIA Power Sector Data Crosswalk**: EPA Clean Air Markets
Division's published identifier map from a CAMPD/CEMS `(facility, unit,
generator)` to the EIA-860 `(plant, generator, boiler)` it belongs to. A static
identifier map, not a measurement of conduct.

Profile: `shared` (no ISO token in the path; verified with
`scripts/hydrate_data.py::owner_of`).

## Files

| File | What it is | sha256 |
|---|---|---|
| `epa_eia_crosswalk.csv` | The crosswalk, byte-identical to upstream `master` (git blob `5b245fb2`) — 6,935 rows, 33 columns | see `SHA256SUMS.txt` |
| `UPSTREAM-README.md` | Upstream `README.md` at the same commit (git blob `fa249879`): methodology, match steps, full column descriptions | see `SHA256SUMS.txt` |

## Source

- Repository: <https://github.com/USEPA/camd-eia-crosswalk>, branch `master`,
  commit `3c7d6724cddee38dfb6a06debca732c33a227ed6` (2022-10-03, "Update manual
  matches and exclusions (#34)").
- Fetched 2026-09-26 from
  `https://raw.githubusercontent.com/USEPA/camd-eia-crosswalk/master/epa_eia_crosswalk.csv`
  and `.../master/README.md`.
- Landing page: <https://www.epa.gov/airmarkets/power-sector-data-crosswalk>.
- Citation: Huetteman, J.; Tafoya, J.; Johnson, T.; Schreifels, J. 2021.
  *EPA-EIA Power Sector Data Crosswalk*.
- License: US Government work, public domain (upstream `LICENSE`).

## Version and vintage

- **Release v0.3** (October 2022: manual unit-by-unit matches added, sequence
  numbers fixed).
- **EIA side: EIA-860 data year 2018** (`3_1_Generator_Y2018`,
  `6_1_EnviroAssoc_Y2018`, `2___Plant_Y2018`). The `EIA_UNIT_TYPE` /
  `EIA_FUEL_TYPE` columns are **2018 codes** and go stale on later conversions
  (e.g. Burlington 1104 unit 1 reads `SUB`, but it burns gas from 2022).
  Consumers should take the prime mover and energy source from the
  solve-year `data/raw/eia-860/vintage_<year>/` and use this file only for the
  identifier join.
- **CAMD side:** the FACT `/facilities` inventory as pulled for v0.3
  (latest `CAMD_STATUS_DATE` 2022-08-31).
- **Newer upstream?** Checked 2026-09-26 by a blobless clone of the upstream
  repo. `master` has not moved since 2022-10-03. A `development` branch
  (head `3423b2ab`, 2025-10-08) is reworking the R script (heat-input and
  nameplate matching, `epa_*` column renames). Its committed CSV was last
  regenerated 2025-06-24, is **still built on 2018 data**, has fewer rows
  (5,810), and is not a release. It was **not** taken.

## Columns

Upstream names are kept exactly as published. Full descriptions are in
`UPSTREAM-README.md` §Output.

| Column | Meaning |
|---|---|
| `SEQUENCE_NUMBER` | Row order |
| `CAMD_STATE`, `CAMD_FACILITY_NAME` | CAMPD facility state and name |
| `CAMD_PLANT_ID` | CAMPD facility id (ORISPL). **CAMPD key** |
| `CAMD_UNIT_ID` | CAMPD combustion unit (boiler / turbine / stack). **CAMPD key**. Equals `unitId` in `data/raw/campd-unit-level` |
| `CAMD_GENERATOR_ID` | Generator id as CAMPD records it |
| `CAMD_NAMEPLATE_CAPACITY` | MW, CAMPD |
| `CAMD_FUEL_TYPE` | CAMPD primary fuel (e.g. `Pipeline Natural Gas`, `Coal`) |
| `CAMD_LATITUDE`, `CAMD_LONGITUDE` | degrees |
| `CAMD_STATUS`, `CAMD_STATUS_DATE`, `CAMD_RETIRE_YEAR` | `OPR` / `LTCS` / `RET`, change date, retire year (0 = none) |
| `MOD_CAMD_UNIT_ID`, `MOD_CAMD_GENERATOR_ID` | CAMPD ids after the fuzzy-match normalization step |
| `EIA_STATE`, `EIA_PLANT_NAME` | EIA plant state and name |
| `EIA_PLANT_ID` | EIA-860 plant code. **EIA key**. Can differ from `CAMD_PLANT_ID` (see `PLANT_ID_CHANGE_FLAG`) |
| `EIA_GENERATOR_ID` | EIA-860 generator id. **EIA key**. Empty when unmatched |
| `EIA_NAMEPLATE_CAPACITY` | MW, EIA-860 2018 |
| `EIA_BOILER_ID` | EIA-860 boiler id (EnviroAssoc), when matched through a boiler |
| `EIA_UNIT_TYPE` | EIA-860 **prime mover**, 2018 (`ST`, `GT`, `CT`, `CA`, `CS`, `IC`, …) |
| `EIA_FUEL_TYPE` | EIA-860 energy source 1, 2018 (`NG`, `SUB`, `BIT`, `PC`, …) |
| `EIA_LATITUDE`, `EIA_LONGITUDE`, `EIA_RETIRE_YEAR` | EIA-860 2018 |
| `PLANT_ID_CHANGE_FLAG`, `MOD_EIA_PLANT_ID` | 1 when the EIA plant id was remapped to the CAMPD ORIS per eGRID's known-discrepancy list |
| `MOD_EIA_BOILER_ID`, `MOD_EIA_GENERATOR_ID_BOILER`, `MOD_EIA_GENERATOR_ID_GEN` | EIA ids after normalization |
| `MATCH_TYPE_GEN`, `MATCH_TYPE_BOILER` | How the row matched: exact / fuzzy step, `Manual Match`, or `CAMD Unmatched` / `Manual CAMD Excluded` |

Cardinality: one CAMPD unit can map to several generators (a CC turbine row
repeats the shared steam turbine), and several units can map to one generator
(Dan E Karn 1 maps to generators 1A and 1B). Choose a collapse grain before
summing anything.

## Known limitations

1. **Vintage (the main one).** Units built or re-registered after the 2018
   EIA-860 / 2022 CAMD pull are absent. Measured on MISO CAMPD gross load
   (`results/calibration/_miso277_crosswalk_footprint.json`): matched share
   **98.99 % (2019) → 96.9 → 95.5 → 93.5 → 91.37 % (2023)**. The 2023 misses are
   post-2018 plants (Blue Water 62192, Montgomery County 60925, St. Charles
   60926, Lake Charles 60927, R D Morrow repower 6061), plus **Riverside 55641
   CT-03/CT-04**, plus Mankato 56104 CT-1 (a genuine miss from 2006).
2. **Riverside / West Riverside is NOT resolved.** The crosswalk has only
   55641 CT-01/CT-02 and no row for EIA plant 64020. CAMPD still files West
   Riverside's turbines as 55641 CT-03/CT-04 (4.31 TWh gross in 2023), and
   EIA-860 2023 carries them as 64020 CTG3/CTG4/STG2 (built 2020). That re-route
   needs a separately cited manual match, the same way the CA-only
   `campd.CAMPD_UNIT_PLANT_REMAP` works.
3. The EIA prime mover and fuel columns are 2018 values (see Vintage above).
4. Upstream calls v0.3 "a work in progress". Auxiliary boilers (e.g. Dan E Karn
   A/B) are left `CAMD Unmatched`.

## Consumers

None in the model. Read only by `scripts/probes/_miso277_crosswalk_footprint.py`
(zero-LP footprint for FINDING-miso276 §2/§4).

## Regeneration

Re-fetch the two files from the commit pinned above. Check the new bytes
against `SHA256SUMS.txt`. A newer upstream release would be a new vintage, so
put it next to this one; never overwrite in place.
