# load-forecast-vintages — ISO short-term hourly load-forecast vintages (raw)

Every issued vintage of an ISO's own short-term hourly load forecast, kept by issue time. Intake lane UC-DF-AUDIT
(owner ruling UC-DESK r14, 2026-10-16) for the reliability-commitment (RUC) load basis
(`docs/records/governance/uc-milp-2026-10/DESIGN-ucmilp-ruc-stage-2026-10-16.md` §2.2) and the DF audit
(`docs/records/governance/uc-milp-2026-10/FINDING-ucmilp-df-audit-2026-10-16.md`).

Clean contract: `data/dictionary/schema/load-forecast-vintages.schema.yaml`; curate with
`python -m scripts.data.curate_load_forecast_vintages` (or `scripts/regenerate_clean.py load-forecast-vintages`);
read with `market_sim.data.load_forecast_vintages`.

## spp/ — SPP Mid-Term Load Forecast (MTLF)

| file | source | vintages |
|---|---|---|
| `2019.zip` … `2024.zip` | SPP's own year archive, byte-for-byte | 8,727–8,755 / yr |
| `2025.zip` | **repacked here**: 2025 had no year zip at fetch (2026-10-16); the 8,730 hourly files were downloaded one by one and zipped with SPP's member layout (`2025/MM/DD/OP-MTLF-*.csv`), file bytes unchanged, member timestamps fixed at 2025-01-01 | 8,730 |

- **Source:** SPP portal file browser, folder `mtlf-vs-actual`; anonymous HTTPS, no login.
  - year archive: `https://portal.spp.org/file-browser-api/download/mtlf-vs-actual?path=%2F<YYYY>%2F<YYYY>.zip`
  - live layout: `https://portal.spp.org/file-browser-api/download/mtlf-vs-actual?path=%2F<YYYY>%2F<MM>%2F<DD>%2FOP-MTLF-<YYYYMMDDHH>00.csv`
  - listing: `https://portal.spp.org/file-browser-api/?fsName=mtlf-vs-actual&path=%2F<YYYY>&type=folder`
  - Folders go back to 2013.
- **File:** `OP-MTLF-YYYYMMDDHH00.csv`, one per hour, stamp = local Central prevailing hour; posted at about HH:05.
  Columns `Interval` (local interval end), `GMTIntervalEnd` (UTC interval end), `MTLF`, `Averaged Actual`;
  193 rows: stamp + 168 h back to stamp − 24 h. The past rows carry SPP's averaged actual; the hour in progress
  at issue is a partial-hour average.
- **Quirks handled by the parser** (`scripts/lib/load_forecast_vintages/spp.py`):
  - The repeated fall-back hour is labelled `…0200d.csv`. The 07 UTC vintage is `0200` and the 08 UTC one is
    `0200d`, so the issue time comes from the horizon (`max(GMTIntervalEnd) − 168 h`). It is cross-checked
    against the stamp everywhere outside ±2 h of a DST change.
  - Some 2020 files drop the seconds from the timestamps.
  - A `BAA` column (`SPP`, `SWPW`) appears with the April 2026 RTO West expansion. Files without it are the SPP
    balancing authority alone and get area `SPP`.
- **Gaps:** 5–33 hourly vintages per year are not published (portal folder listings confirm it; e.g. 2025-10-28
  18:00–20:00). The 2025 portal returned HTTP 404 for 30 of 8,760 stamps.
- **Footprint (rule 14):** SPP's own averaged actual matches EIA-930 `SWPP` `Demand` at the same UTC hour end:
  ratio 0.996–1.003 and median |Δ| 69–106 MW in 2019–2025. The finding's table A has the details.
- **Integrity:** `spp/SHA256SUMS.txt`. A mismatch on re-fetch means SPP re-published the archive. Treat that as
  a finding, not something to overwrite silently.

DATA NEEDED: none for 2019–2025. Years 2013–2018 and 2026 are at source and not landed; 2026 needs the `BAA`
split and has no year zip yet.
