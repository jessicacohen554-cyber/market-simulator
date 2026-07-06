# ercot — raw

The largest raw source in the repo (~805 MB, 107 files): the ERCOT MIS
report family behind ancillary-services awards, disclosure, load, and
real-time price-adder data. Filename families (year suffix stripped):

| Pattern | ERCOT MIS report |
|---|---|
| `2_DAY_AS_DISCLOSURE_2d_{Agg,Cleared,Self_Arranged}_DAM_AS_Offers_<PROD>_*.parquet` | 2-Day AS Disclosure (NP3-911-ER family) |
| `2_DAY_SCED_AS_DISCLOSURE_2day_Agg_SCED_AS_Offers_<PROD>_*.parquet` | 2-Day SCED AS Disclosure |
| `60_DAY_DAM_DISCLOSURE_60d_DAM_{EnergyBidAwards,EnergyBids,EnergyOnlyOfferAwards,EnergyOnlyOffers,Gen_Resource_Data,Load_Resource_ASOffers,PTPObligationBidAwards,PTPObligationBids,PTP_Obligation_Option,QSE_Self_Arranged_AS}_*.parquet` | 60-Day DAM Disclosure |
| `ACTUALSYSLOADFZNP6346_<year>.parquet`, `ACTUALSYSLOADWZNP6345_<year>.parquet` | NP6-345/346-CD Actual System Load by Weather/Forecast Zone |
| `ASPLANNP433_<year>.parquet` | NP4-33 (ASPLAN) |
| `DAMASAGGNP419_*.parquet`, `DAMASSOLDNP4532_2025.parquet` | NP4-19/NP4-532 DAM AS awards/sold |
| `DRUCASDCNP4214_*.parquet`, `DRUCASDFNP5527_*.parquet`, `HRUCASDFNP5528_*.parquet` | day-ahead/hour-ahead reliability-unit-commitment AS disclosure |
| `RTSCEDPRICEADDERNP6323_*.parquet` | NP6-323 Real-Time SCED price adders (ORDC/reliability-deployment) |
| `ercot_<year>_dam_as_mcpc_hourly.parquet`, `ercot_<year>_ordc_reserves_hourly.parquet` | derived (see below) |

**Source:** ERCOT MIS (`ercot.com`), public/redistributable per ERCOT's
raw-data terms — see `docs/data-licensing.md` §3.

**Regeneration:**
- The disclosure/load/ASPLAN parquets are converted from ERCOT MIS report
  downloads (re-fetch via the ERCOT Data Portal / MIS report list for the
  report IDs above).
- `scripts/fetch_ercot_ordc_reserves.py` → `ercot_<year>_ordc_reserves_hourly.parquet`
  (ERCOT MIS report NP6-905-CD "Historical Real-Time Price Adders by SCED
  Interval", reportTypeId 13231 — public, no API key).
- `scripts/build_ercot_dam_as_mcpc.py` → `ercot_<year>_dam_as_mcpc_hourly.parquet`.

**Consumers:** `scripts/curate_ancillary_services.py` (cleared MW per AS
product from the 2-Day AS Disclosure Cleared files), `scripts/parse_ercot_dam_offers.py`,
`scripts/build_ercot_as_2023.py`, `scripts/build_ercot_as_withholding.py`,
`scripts/build_ercot_storage_as_2023_estimate.py`, `scripts/derive_dam_offer_hrmults.py`,
`scripts/derive_gas_takeorpay.py`, `scripts/curate_gtc_limits.py`. Note:
`scripts/derive_load_shares.py`'s ERCOT branch reads the *separately
converted* NP6-345-CD copies under `data/raw/reference/`, not this
directory's `ACTUALSYSLOADWZNP6345_<year>.parquet`. ERCOT settlement-point
LMP is **not** curated from here — `scripts/curate_lmp.py` notes ERCOT has
no raw LMP source yet (`data/raw/lmp-data/ERCOT/` is empty).
