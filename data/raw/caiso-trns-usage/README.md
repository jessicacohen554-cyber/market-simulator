# CAISO OASIS `TRNS_USAGE` (DAM): intertie transmission ratings and usage

Intake: R-CAISO-30 (2026-10-01). Data intake only: nothing in the model reads this today.

## What it is

The CAISO OASIS report `TRNS_USAGE`, market `DAM`, gives hourly values for each intertie scheduling
constraint (`TI_ID`, the ITC/ISL names CAISO schedules imports and exports against) and each direction
(`I` import, `E` export). It covers 13 items. The ones that matter here:

| item | OASIS label | meaning |
|---|---|---|
| `TTC_MW` | Seasonal TTC | path rating |
| `OTC_MW` | Hourly TTC | operating transfer capability after derates |
| `TRM_MW` (+ `_UF`/`_FTO`/`_SPI`) | Total TRM | reliability margin and its components |
| `MKT_XFER_CAP_MW` | Market Transfer Capability | the limit IFM enforces |
| `ENE_IMPORT_MW` | Scheduled net energy from imports/exports | DAM schedule, **not a metered flow** |

The other items (`CBM_MW`, `CONSTRAINT_MW`, `AS_IMPORT_MW`, `USEAGE_MW`, `ATC_MW`) are kept in the
parquet. `99999` is OASIS's "unlimited" sentinel (the `CISO_NET_*` aggregates) and is kept verbatim.

## Files

- `caiso_trns_usage_dam_<year>.parquet`: **committed**, one per Pacific operating year. Wide layout with
  key (`interval_start_utc`, `ti_id`, `ti_constraint_id`, `direction`) and one float column per item.
  This reshape loses no information: the dropped CSV columns are derivable, constant for this query,
  or a pure function of the item, and the fetcher asserts this for every window
  (`scripts/data/fetch_caiso_trns_usage.py` docstring).
- `SHA256SUMS.txt`: identity record of the committed parquets.
- `windows/`: per-request staging, **gitignored**.

Curated into the `transfer-interface-limits` clean datatype (CAISO spec
`scripts/lib/transfer_interface_limits/caiso.py`). That gives four series per ITC and direction,
`"<ti_id>|<I|E>|<OTC|TTC|TRM|MTC>"`, on the Pacific non-leap 8760 clock. Hours before retention starts
are absent, not filled in.

## Source and re-fetch

`https://oasis.caiso.com/oasisapi/SingleZip?queryname=TRNS_USAGE&market_run_id=DAM&startdatetime=<UTC>&enddatetime=<UTC>&version=1&resultformat=6`

```
python scripts/data/fetch_caiso_trns_usage.py --start 2023-06-19 --end 2026-01-01   # stage windows
python scripts/data/fetch_caiso_trns_usage.py --fold                                 # -> committed parquets
```

- Request windows must start and end on Pacific-day boundaries: 07Z in PDT months, 08Z in PST months.
  An 08Z start in a PDT month returns an empty zip.
- An 11-day window is about 2 MB zipped (about 55 MB CSV) and takes 1 to 2 minutes server-side.

## Retention: what is lost

OASIS keeps about 39 months of this report, on a rolling basis. **Measured 2026-10-01: the earliest
trade date served was 2023-06-19.** 2023-06-17 and 2023-06-18 returned `ERR_CODE 1000` "No data
returned". The start date moves forward by one day for each calendar day that passes.

- **Lost from the API:** everything before 2023-06-19. That covers the keeper's 2022 training year, the
  2019 to 2021 fold years, and 2023-01-01 to 2023-06-18.
- **Retained here:** 2023-06-19 to 2025-12-31. These committed parquets are the only copy once those
  months also age out of OASIS. There is no other public archive of this report known to this repo.

## Admissibility (rules 13 and 14)

Hourly OTC and TTC are CAISO's published operating transfer capability. They are a reproducible physical
input that would regenerate for any year from the same feed. `ENE_IMPORT_MW` is a market outcome (the
DAM schedule) and may be used only as a diagnostic, never as an input or a target.
