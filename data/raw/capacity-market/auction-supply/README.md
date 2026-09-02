# capacity-market-auction-supply — raw

The supply half of the capacity-auction record (companion to
`../auction-price`, which carries the cleared prices): each auction's
published QUANTITY accounting — offered and cleared MW by planning-resource
category, plus the requirement/commitment ledger rows the same postings
publish (PRMR, FRAP, self-scheduled, committed).

Layout: one unified CSV per ISO at `<iso>/<iso>.csv` with exactly the schema
columns (`data/dictionary/schema/capacity-market-auction-supply.schema.yaml`);
curated by `scripts/data/curate_capacity_market_auction_supply.py` via the
per-ISO registry `scripts/lib/capacity_market_auction_supply/<iso>.py`.

Rule-13 posture (also stated in the schema header): these are the market's
own recurring supply-accounting quantities — admissible as an
ACCOUNTING-BASIS input (identifying the wedge between a census-accreditation
ledger and the market's counted supply) and, for the cleared rows, a
validation observable. NEVER a target to pin a model's cleared quantity or
reserve position to.

Populated ISOs:

- `miso/` — PRA Results Postings PY2023-24 … PY2025-26 (capx D31,
  2026-09-02). See `miso/README.md`.

DATA NEEDED: PJM (BRA offered/cleared UCAP, Table 2/7), ISO-NE (FCA
qualified/de-list/cleared), NYISO (SOM supplied-vs-requirement) — the D28 §6.5
cross-ISO clearing-half sources; intake per ISO when a lane needs them.
