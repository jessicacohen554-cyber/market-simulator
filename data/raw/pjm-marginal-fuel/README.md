# PJM real-time marginal fuel — IMM "Marginal Fuel Postings"

Hourly share of PJM real-time 5-minute intervals in which units of each fuel
set (or jointly set) the LMP. Intaken 2026-10-02 for the PJM close-out step 0e
census (`docs/backcast-closeout-plan-2026-10.md` §3.6; research shard §6 row 1).

## Source

- **Publisher**: Monitoring Analytics, LLC (PJM Independent Market Monitor).
- **Page**: <https://www.monitoringanalytics.com/data/marginal_fuel.shtml>
  ("Marginal Fuel Posting"); data description
  <https://www.monitoringanalytics.com/data/docs/data-description.pdf>.
- **Files**: `https://www.monitoringanalytics.com/data/marginal_fuel_type/<YYYYMM>_Marginal_Fuel_Postings.csv`
  (one per month, posted ~1–2 months after month end; 2009-01 onward).
- PJM's page <https://www.pjm.com/markets-and-operations/energy/real-time/historical-bid-data/marg-fuel-type-data.aspx>
  embeds a listing (`/pjmfiles/pub/market/energy/marginal-fuel-type/`) that
  stops at 2008-12. Data Miner 2 has no marginal-fuel feed (API feed list
  checked 2026-10-02).
- **Retrieved**: 2026-10-02, months 2019-01 → 2025-12 (84 files).
- **Licence**: "Monitoring Analytics ©2026 – All rights reserved"; the site's
  legal page states access "does not confer any license". Redistribution terms
  are unverified, so the data bytes are **gitignored** (see `.gitignore`);
  this README, `SHA256SUMS.txt` and the fetch script are committed. Owner
  review item, alongside `docs/data-licensing.md` §4/§8.

## Method (from the IMM data description)

Each 5-minute interval gives weight 1/n to each of its n marginal units
(several under congestion); a fuel's hourly share is the mean weight over the
hour's intervals, so one hour's shares sum to 1. Fuel is the unit's primary
fuel (IMM-assigned from public data). Note this is **time-weighted**; the IMM
SOM table "Type of fuel used and technology (By real-time marginal units)" is a
count of marginal units, so its coal share runs ~1.3–1.7× lower than this
file's annual mean (2019–2025).

## Files

- `monthly/<YYYYMM>_Marginal_Fuel_Postings.csv` — immutable raw pull
  (gitignored, ~6.6 MB). Columns: `HOUR` (hour beginning, `DDMONYYYY:HH:MM:SS`,
  EPT), `MMS_TIMEZONE` (EST/EDT; the repeated fall hour is EST),
  `FUEL_TYPE` (verbatim label), `PERCENT_MARGINAL` (fraction 0..1).
- `by-year/pjm_marginal_fuel_<YEAR>.csv` — tidy per-year form (gitignored,
  ~1.4–1.7 MB/yr), schema `data/dictionary/schema/pjm-marginal-fuel.schema.yaml`:
  `hour_beginning_ept`, `mms_timezone`, `fuel_type`, `percent_marginal`,
  `source_file`. 8760/8784 hours per year, every hour sums to 1 ± 2e-4.
- `SHA256SUMS.txt` — sha256 of every raw monthly file (committed).

DATA NEEDED: none for 2019–2025 (re-run the fetch on a fresh checkout).

## Regenerate

```bash
python scripts/data/fetch_pjm_marginal_fuel.py --start 2019-01 --end 2025-12
```

## Consumption

Diagnostic comparator only (rule 13: an observed outcome, never a model input):
`scripts/probes/_pjmco_0e_marginal_fuel_census.py` compares it with the
keeper's `hourly/unit_marginal_<y>.parquet` layer. Not a `data/clean`
datatype yet (no curate step, no `config/paths.py` constant).
