# lmp-data — raw

Per-ISO locational marginal price (LMP) downloads, used to validate the
model's LP-dual prices against actual market clearing prices.

| Location | Contents | Source | Regeneration |
|---|---|---|---|
| `CAISO/` | `CAISO_{dam,rtm}_hourly_<year>.csv` (2023–2025) | CAISO OASIS `PRC_LMP` (DAM) / `PRC_INTVL_LMP` (RTM) | `scripts/fetch_caiso_oasis.py` + `scripts/postprocess_oasis_downloads.py` |
| `CAISO/` | `*_{DAM,RTM,HASP}_LMP_GRP_*_csv.zip` — hand-downloaded OASIS bulk (all-node) zips for history aged out of the API's ~39-month retention. 2026-07-14 intake: DAM 19 trade dates over 2023-01-01..25 (folded — filled the Jan hole in `CAISO_dam_hourly_2023.csv`; Jan 6/9/10/16/19/24 + Jan 26–Feb 26 still missing); RTM ~34 scattered hours of Jan 1–4 (**deliberately NOT folded** — too thin to stand for a month; the C3a scorer unmasks a month the moment its mean exists); HASP is a different market run, never folded — the 191 hand-downloaded HASP zips were deleted 2026-07-14 (owner request; no consumer reads HASP). Also present: two browser duplicate copies (`* 2.zip`, skipped by name) and one stray PDF attachment | CAISO OASIS single-zip bulk downloads | `scripts/fold_caiso_oasis_grp_zips.py` (hub + WECC-intertie node extraction) + `scripts/postprocess_oasis_downloads.py`; the S3 bulk-archive route is `.github/workflows/fetch-caiso-oasis-bulk.yml` → `scripts/extract_caiso_hubs.py` |
| `ERCOT/` | empty (`.gitkeep` only) | — | no raw ERCOT LMP exists yet; `scripts/curate_lmp.py` explicitly treats this as out of scope. ERCOT's LZ/HB/SPP settlement-point archives live at the top level instead (see below) |
| `MISO/` | `miso_hub_lmp_<year>_{da,rt}.csv.gz` (already documented — see `MISO/README.md`) | MISO daily market reports | `scripts/fetch_miso_hub_lmp.py` |
| `NEISO/` | `<year>_smd_hourly.xlsx` (2018–2025) | ISO-NE SMD hourly workbooks | **manual download only** — the ISO Express *Zonal Information* page serves these behind a CAPTCHA-gated "Download Selected Files" form, so no committed script can refresh them and an unattended session cannot obtain a year the repo does not already hold (confirmed 2026-08-15, neiso-96). `2022` relocated from the top-level orphan set 2026-07-07 under the NEISO calibration-complete holdout intake (byte-identical move; same sheet/column layout as 2023–2025, verified) |
| `NEISO/smd-zonal-lmp/` | `NEISO_smd_zonal_lmp_<year>.csv` (2026 — H1, 181 operating days) — hourly DA + RT-final LMP for the nine SMD pricing locations (`.H.INTERNAL_HUB` + the eight `.Z.*` load zones), one row per (day, hour, location), carrying the as-published within-day row position `seq` | ISO-NE static historical-report tree — `histRpts/da-lmp/WW_DALMP_ISO_<YYYYMMDD>.csv` and `histRpts/rt-lmp/lmp_rt_final_<YYYYMMDD>.csv`; **ungated**, no credentials | `scripts/data/fetch_neiso_smd_zonal_lmp.py` (reduces ~4.9 MB/day of all-node report to ~8 KB/day). The SAME nine locations the workbook publishes: measured identical to the workbook route at the parquet's float32 precision over 2,640 cells / 11 sampled days by `scripts/probes/neiso96_smd_route_equivalence.py`, so it is a second packaging of one input, not a second input |
| `NYISO/` | `*realtime_zone_csv.zip` (5-min RT zonal LBMP; **21 months are committed** — 2022's twelve from the rule-22 holdout intake 2026-07-12, plus nine scattered 2023–2025 months — and the rest are gitignored/regenerable; the committed `actual_lmp_hourly_NYISO.parquet` is the durable record). **Stamps are interval-ENDING** — see the convention note below | NYISO MIS public RT zonal LBMP monthly archives (`http://mis.nyiso.com/public/csv/realtime/`) | `scripts/data/fetch_nyiso_zonal_lmp.py` (idempotent; skips the committed months, so their bytes are never rewritten) → `scripts/data/derive_actual_lmp.py`; 2022 lander: `.github/workflows/holdout-intake-nyiso-2022.yml` |
| `NYISO/` | `YYYYMM01damlbmp_zone_csv.zip` (**gitignored** — regenerable) + `NYISO_zonal_hourly.zip`, the outer container `derive_actual_lmp.py` reads them from (**gitignored**, staged out) | NYISO MIS public DAM zonal LBMP monthly archives (`http://mis.nyiso.com/public/csv/damlbmp/`) | `scripts/data/fetch_nyiso_zonal_lmp.py --kind da`, which downloads the monthlies **and assembles the outer container** (it replaces the old bare `for m in 01..12; curl -O ...; done` loop); also `scripts/data/build_nyiso_proxy_lmp_neiso.py` (writes the committed `nyiso_proxy_lmp_hourly_NEISO.parquet`, DA-only — untouched by the RT convention repair) |
| `NYISO/` + top level | `dartmonthlylmpindex_<year>.csv` — **misfiled: ISO-NE monthly LMP index reports** (`.H.INTERNAL_HUB`/`.Z.*` locations), not NYISO data (verified 2026-07-12; equivalency-register N2) | ISO-NE web services | out of scope for every curator (unchanged) |
| top level | `DAMLZHBSPP_<year>.zip`, `RTMLZHBSPP_<year>.zip` (2023–2025) | ERCOT LZ/HB/SPP settlement-point archives | manual download (ERCOT MIS) |
| top level | `PJM_<year>_rt_da_monthly_lmps.csv` (2023–2025) | PJM DataMiner2 RT/DA monthly LMP export | manual download (DataMiner2) — see `docs/data-licensing.md` §4 |
| top level | `2020_smd_hourly.xlsx`, `2021_smd_hourly.xlsx` | **orphaned** — pre-dates the `NEISO/` subdirectory split; not read by any script (`2022` moved into `NEISO/` 2026-07-07 for the holdout one-shot) | — |

**KNOWN DEFECT in the 2018–2023 SMD workbook vintage (found 2026-08-15, neiso-96;
reported, NOT repaired).** ISO-NE changed the workbook's shape partway through the
archive. The 2024–2025 workbooks publish the true number of hours on a DST day —
23 on spring-forward, 25 on fall-back, the repeated hour marked `02X` — and agree
with the daily historical reports exactly. The **2018–2023** workbooks publish a
flat **24 rows on every calendar day**: on spring-forward they carry an extra row,
and on fall-back they collapse the repeated hour into its two-instance average.
`derive_actual_lmp._neiso_sheet_series` maps the k-th published row to k real
hours after local midnight, so on those four days per year the rest of the day is
displaced by one hour in `actual_lmp_hourly_NEISO.parquet`. Measured on the four
sampled DST days in `results/calibration/_neiso96_smd_route_equivalence.json`.
It is **not repaired here** because 2023 is a tuned year, so correcting it moves a
scoring target in-sample and needs its own authorization and re-solve.

**NYISO interval convention (REPAIRED 2026-08-16, nyiso-139).** The 5-minute RT
(P-24A) `Time Stamp` labels an interval by its **END**; the hourly DA
(`damlbmp`) stamp labels its interval by its **BEGINNING**. `derive_actual_lmp.
_nyiso_wide` shifts RT back one second before flooring and leaves DA alone; the
archive's own file boundaries corroborate it (a monthly RT zip runs `00:05` on
day 1 to `00:00` on day 1 of the next month, i.e. exactly the intervals *ending*
in that month). Adjudicated against NYISO's own time-weighted hourly product
P-4A, which Manual 12 p. 136 / Manual 14 §4 state is built from these same
5-minute prices: ENDING agrees within the $0.005 rounding bound on every one of
14,905 strict zone-hours, BEGINNING is wrong on 14,174 of 14,828 by up to
$50.01 (`scripts/probes/nyiso_rtd_clock_adjudication.py --strict`). The repair
moves ~95 % of hours but shifts the annual level by ≤0.03 %, and it is RT-only —
the DA block, the `spec.py` import ladder derived from it, and
`nyiso_proxy_lmp_hourly_NEISO.parquet` are all unaffected. Evidence:
`results/calibration/FINDING-nyiso139-rtd-clock-repair-landed-2026-08-16.md`.

**Consumers:** `scripts/curate_lmp.py` (the `lmp` clean-datatype curator —
its docstring is the authoritative per-ISO source map),
`scripts/derive_ercot_zonal_lmp.py` (reads the top-level ERCOT SPP zips
directly for a validation derivation, separate from `curate_lmp.py`'s
ERCOT-is-out-of-scope stance), `scripts/derive_actual_lmp.py`.

**Note:** the two remaining top-level `<year>_smd_hourly.xlsx` files
(2020–2021) predate the current `NEISO/` per-ISO subdirectory convention and
are not referenced by any current script — treat them as historical
leftovers, not an active input, unless you extend a consumer to read them.
(`2022_smd_hourly.xlsx` was moved into `NEISO/` on 2026-07-07 as part of the
NEISO calibration-complete one-shot holdout intake — byte-identical rename,
now an active bench input for the 2022 validation year.)

**Licensing note:** this directory spans multiple ISOs with different terms
— CAISO (unclear/conditional), PJM (conditional, non-member ban), NYISO/
ISO-NE (unclear/unverified), ERCOT (permitted). See `docs/data-licensing.md`
§§3–7.
