# ercot-AS — raw

ERCOT MIS ancillary-services report bundles:

- `00013057.np3-911-er.2d_cleared_dam_as_<PROD>.<timestamp>_json.zip` — NP3-911-ER
  "2-Day Cleared DAM AS" per product (ECRSM, ECRSS, NSPIN, NSPNM, REGDN,
  REGUP, RRSFFR, RRSPFR, RRSUFR).
- `00013051.np3-966-er.60d_dam_as_only_awards.<timestamp>_json.zip` —
  NP3-966-ER "60-Day DAM AS Only Awards".
- `00013052.np3-965-er.60d_sced_as_offer_updates.<timestamp>_json.zip` —
  NP3-965-ER "60-Day SCED AS Offer Updates".
- `ercot_<year>_as_by_restype_hourly.parquet`,
  `ercot_<year>_as_up_mw.parquet` — derived (see below).

**Source:** ERCOT MIS reports (`ercot.com`), public/redistributable per
ERCOT's raw-data terms — see `docs/data-licensing.md` §3.

**Regeneration:**
- The raw json.zip bundles are ERCOT MIS report downloads (re-fetch via the
  ERCOT Data Portal / MIS report list for report types NP3-911-ER,
  NP3-966-ER, NP3-965-ER).
- `scripts/build_ercot_as_by_restype_from_60day.py` →
  `ercot_<year>_as_by_restype_hourly.parquet`.
- `scripts/build_ercot_as_2023.py`, `scripts/build_ercot_as_withholding.py` →
  `ercot_<year>_as_up_mw.parquet`.

**Consumers:** `scripts/curate_ancillary_services.py` (reads the MCPC award
prices from the 60-day DAM AS awards zips — `zone="SYSTEM"`, ERCOT is a
single-zone AS market), `scripts/build_ercot_storage_as_2023_estimate.py`.
