# lmp-data — raw

Per-ISO locational marginal price (LMP) downloads, used to validate the
model's LP-dual prices against actual market clearing prices.

| Location | Contents | Source | Regeneration |
|---|---|---|---|
| `CAISO/` | `CAISO_{dam,rtm}_hourly_<year>.csv` (2023–2025) | CAISO OASIS `PRC_LMP` (DAM) / `PRC_INTVL_LMP` (RTM) | `scripts/fetch_caiso_oasis.py` + `scripts/postprocess_oasis_downloads.py` |
| `ERCOT/` | empty (`.gitkeep` only) | — | no raw ERCOT LMP exists yet; `scripts/curate_lmp.py` explicitly treats this as out of scope. ERCOT's LZ/HB/SPP settlement-point archives live at the top level instead (see below) |
| `MISO/` | `miso_hub_lmp_<year>_{da,rt}.csv.gz` (already documented — see `MISO/README.md`) | MISO daily market reports | `scripts/fetch_miso_hub_lmp.py` |
| `NEISO/` | `<year>_smd_hourly.xlsx` (2023–2025) | ISO-NE SMD hourly workbooks | manual download (ISO-NE report archive) |
| `NYISO/` | `*realtime_zone_csv.zip`, `dartmonthlylmpindex_<year>.csv` | NYISO OASIS realtime-zone LBMP | manual download (NYISO OASIS) |
| `NYISO/` | `YYYYMM01damlbmp_zone_csv.zip` (2023-2025, **gitignored** — ~13 MB, regenerable) | NYISO MIS public DAM zonal LBMP monthly archives (`http://mis.nyiso.com/public/csv/damlbmp/`) | `for y in 2023 2024 2025; do for m in 01..12; curl -O .../\${y}\${m}01damlbmp_zone_csv.zip; done` then `scripts/build_nyiso_proxy_lmp_neiso.py` (writes the committed `nyiso_proxy_lmp_hourly_NEISO.parquet`) |
| top level | `DAMLZHBSPP_<year>.zip`, `RTMLZHBSPP_<year>.zip` (2023–2025) | ERCOT LZ/HB/SPP settlement-point archives | manual download (ERCOT MIS) |
| top level | `PJM_<year>_rt_da_monthly_lmps.csv` (2023–2025) | PJM DataMiner2 RT/DA monthly LMP export | manual download (DataMiner2) — see `docs/data-licensing.md` §4 |
| top level | `2020_smd_hourly.xlsx`, `2021_smd_hourly.xlsx`, `2022_smd_hourly.xlsx` | **orphaned** — pre-dates the `NEISO/` subdirectory split; not read by any script | — |

**Consumers:** `scripts/curate_lmp.py` (the `lmp` clean-datatype curator —
its docstring is the authoritative per-ISO source map),
`scripts/derive_ercot_zonal_lmp.py` (reads the top-level ERCOT SPP zips
directly for a validation derivation, separate from `curate_lmp.py`'s
ERCOT-is-out-of-scope stance), `scripts/derive_actual_lmp.py`.

**Note:** the three top-level `<year>_smd_hourly.xlsx` files (2020–2022)
predate the current `NEISO/` per-ISO subdirectory convention and are not
referenced by any current script — treat them as historical leftovers, not
an active input, unless you extend a consumer to read them.

**Licensing note:** this directory spans multiple ISOs with different terms
— CAISO (unclear/conditional), PJM (conditional, non-member ban), NYISO/
ISO-NE (unclear/unverified), ERCOT (permitted). See `docs/data-licensing.md`
§§3–7.
