# iso-specific-transmission — raw transfer-limit / interchange sources

Immutable raw drops of per-ISO transmission data. Never modified in place.

## PJM (present)

- `PJM_<year>_transfer_limits_and_flows.csv` — PJM Data Miner 2
  `transfer_limits_and_flows` (hourly interface transfer limits & flows).
- `PJM_<year>_import_export_act_sch_interchange.csv` — Data Miner 2 actual +
  scheduled interchange by interface.

## ERCOT NP6-86 SCED binding-constraint archives (DATA NEEDED)

`DATA NEEDED:` the ERCOT **NP6-86-CD "SCED Shadow Prices and Binding
Transmission Constraints"** monthly archives for the backcast years
(2023, 2024, 2025), named `*SCEDBTCNP686*.zip`. Consumed by

- `scripts/curate_gtc_limits.py` → the `gtc-limits` clean datatype (measured
  hourly Generic Transmission Constraint limits on the model clock), and
- `scripts/derive_ttc_limits.py` (static limit-at-bind summary that seeded
  the `ttc_mw` values in `iso_configs._ercot_config`).

Expected layout, exactly as the ERCOT Data Portal bundles them: one zip per
month containing one inner zip per SCED execution (~5 min), each holding one
CSV with columns `SCEDTimeStamp, RepeatedHourFlag, ConstraintID,
ConstraintName, ContingencyName, ShadowPrice, MaxShadowPrice, Limit, Value,
ViolatedMW, FromStation, ToStation, FromStationkV, ToStationkV, CCTStatus`.
Loose per-interval `*SCEDBTCNP686*` zips/CSVs (the MIS current-window naming
`cdr.00012302.*.SCEDBTCNP686*.csv`) are also accepted.

Authoritative source: <https://data.ercot.com/data-product-archive/NP6-86-CD>
(EMIL NP6-86-CD, reportTypeId 12302). The live MIS listing
(`https://www.ercot.com/misapp/servlets/IceDocListJsonWS?reportTypeId=12302`)
retains only ~7 days; historical months require an ERCOT Data Portal sign-in,
so the archives must be supplied manually — they cannot be fetched
autonomously. A previous session's upload of the full 2023–2024 monthly set
(202,512 SCED intervals) has not been re-committed; this directory keeps only
what fits the repo.

The 5-minute GTC rows are identified by an **empty `FromStation`** (a GTC
caps a weighted flow sum across several elements, not one monitored line).
