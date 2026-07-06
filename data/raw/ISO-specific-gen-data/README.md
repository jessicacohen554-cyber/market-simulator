# ISO-specific-gen-data — raw

`PJM_<year>_gen_by_fuel.csv` (2020–2026) — PJM's own "Generation by Fuel Type"
feed: `datetime_beginning_utc, datetime_beginning_ept, fuel_type, mw,
fuel_percentage_of_total, is_renewable`.

**Source:** PJM DataMiner2 (`dataminer2.pjm.com`) generation-by-fuel-type
report. PJM's own feed is preferred over the EIA-930 PJM balancing-authority
series because it carries the `is_renewable` flag directly
(`scripts/curate_generation.py`).

**Regeneration: hand-assembled — no fetch script in this checkout.** No
`fetch_*.py` script references this directory or the `gen_by_fuel` naming
pattern; the files were pulled manually from DataMiner2. To refresh, use the
DataMiner2 "Generation by Fuel Type" feed following the auth/pagination
pattern documented in `scripts/fetch_pjm_energy_offers.py` (same API family,
different feed name) and write the CSV in the columns above.

**Licensing note:** PJM DataMiner2 data carries redistribution conditions —
see `docs/data-licensing.md` §4.

**Consumer:** `scripts/curate_generation.py` (`PJM_GEN_DIR`).
