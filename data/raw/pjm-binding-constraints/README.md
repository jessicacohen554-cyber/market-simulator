# `pjm-binding-constraints/` — PJM day-ahead binding transmission constraints (gitignored bulk)

PJM DataMiner2 `da_marginal_value` (and its `da_transconstraints` event
companion): one row per **binding** transmission constraint per day-ahead hour,
carrying the `monitored_facility`, the `contingency_facility` and the
constraint's `shadow_price` — PJM's own answer to *which* facility limited the
day-ahead dispatch and by how much. 2023–2025, ~55–80 k constraint-hours per
year across 840–1,060 distinct facilities.

This is the PJM analogue of MISO's `bc_HIST` binding-constraint feed
(`data/raw/lmp-data/MISO/README.md`), and it is a **directly comparable
quantity to the model's own transmission-constraint duals**: the day-ahead
market is the hourly, commitment-aware full-network optimization the LP mirrors,
so its shadow price and the model's dual are the same object measured on the two
networks.

**Not committed.** Same PJM DataMiner2 non-member redistribution restriction as
`pjm-energy-offers/`, `pjm-da-virtuals/` and `pjm-zonal-lmp/` — see
`docs/data-licensing.md` §4. `SHA256SUMS.txt` is committed so a re-fetch can be
checked byte-for-byte against the pull the pjm-137 measurement was taken from.

## Refetch

```
PYTHONPATH=. .venv/bin/python scripts/data/fetch_pjm_binding_constraints.py
```

One zstd Parquet per feed-month, `<feed>_<year>_<month>.parquet`. The fetcher
bisects a window on DataMiner2's HTTP 400 (the same gateway behaviour
`pjm-zonal-lmp/README.md` documents) and flags any month that comes back thin.

## Why this feed answers a question the LMP components cannot

The zonal LMP intake decomposes a price *difference* into congestion and loss,
but it cannot say **which constraint** produced the congestion, or whether that
constraint is a boundary the model's 8-zone reduction even represents. This feed
names the facility. Read at pjm-137 across 2023–2025 it says PJM's day-ahead
congestion is overwhelmingly **sub-zonal**: only 3.1–6.3 % of the absolute
shadow-price record sits on a named zonal-scale transfer interface (AEP-DOM,
APSOUTH, BED-BLA, WEST, EAST, CENTRAL), while 80–88 % sits on individual
monitored facilities rated 230 kV and below. The `AEP-DOM` interface the model
carries as `PJM_AEP_Ohio ↔ PJM_Dominion` is 0.04 / 0.07 / 0.24 % of it.

## Consumers

* `scripts/probes/_pjm137_dominion_ct_congestion.py` — the pjm-137 M2
  binding-constraint anatomy (interface-vs-facility rent split, voltage bands,
  and the constraints that dominate the hours Dominion separates from
  AEP-Dayton).
