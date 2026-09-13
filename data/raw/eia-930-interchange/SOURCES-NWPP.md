# NWPP per-counterparty interchange provenance (NWPP-11, 2026-09-13)

`<BA> interchange hourly.parquet` for the 17 NWPP balancing authorities —
`BPAT PACE PACW PGE PSEI AVA IPCO NWMT CHPD DOPD GCPD SCL TPWR AVRN GRID WAUW
NEVP` — long form, one row per `(BA, directly-interconnected BA, hour)`,
`2023-01-01 01:00 .. 2026-01-01 00:00` on each BA's local hour-ending clock.

Schema, identical to the CISO/MISO/SWPP siblings: `diba` (category), `mw`
(float32), `local_time` (datetime64[us], naive).

## Source and route — KEY-FREE, and why

Fetched through the existing `scripts/data/fetch_eia930_interchange.py` with no
edits:

    python scripts/data/fetch_eia930_interchange.py --ba <BA> --source bulk \
        --years 2023 2024 2025

`--source bulk` is EIA's **Hourly Electric Grid Monitor six-month bulk CSVs**,

    https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_INTERCHANGE_<year>_<Jan_Jun|Jul_Dec>.csv

**`EIA_API_KEY` was UNSET in this session's container and no `.env` carried
one** (plan §2.4 re-measured it at the desk's own pin), so the default `api`
route — EIA Open Data v2 `electricity/rto/interchange-data` — was not available.
The bulk route needs **no registration and no key**, and `neiso-93` (2026-08-14)
verified it equivalent to the `api` route over the committed 2023-2025 ISNE
span, so this is a documented-equivalent substitution, not a downgrade. It is
also the route the charter named as the key-free fallback (plan §6 row 3).

The bulk CSV carries `Local Time at End of Hour` directly, so these files land
on the same hour-ending local clock the `api` path derives by tz-converting a
UTC period — no timezone round-trip, and no dependence on the `BA_TIMEZONE` map.
Each 100 MB+ CSV is streamed and filtered to one BA chunk-by-chunk; none is
written to disk.

## Sign convention — STATED, because every downstream reading depends on it

**`mw` is positive when the named BA EXPORTS to the DIBA**, negative when it
imports. This is EIA's own convention for the `TI` family and is inherited
unchanged from the source; `fetch_eia930_interchange.py`'s module docstring
states the same.

An internal pair (both BAs in the footprint) is therefore reported **twice**,
once from each side, and the two legs should be exact negatives. They are not
always — see the asymmetry finding in
`docs/handoffs/FINDING-nwpp-11-2026-09-13.md` §4, which is entirely a BPAT
phenomenon and is a **source** property, carried unmodified.

## What is NOT here

`Total Interchange` and `Sum(Valid DIBAs)` at the BA level are already in the
committed BALANCE archive and in the derived `data/raw/eia-930-hourly/<BA>
hourly.parquet` extracts (`Total interchange`, and `Total interchange
(Adjusted)`). These files add only the **per-counterparty** resolution that
BALANCE does not carry.

2019-2022 and H1-2026 are not fetched by this lane (plan §6 row 13 puts the
back years after W4); the same keyless command lands them when they are wanted.
