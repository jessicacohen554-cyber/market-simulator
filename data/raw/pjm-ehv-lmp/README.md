# `pjm-ehv-lmp/` — PJM 500 kV EHV aggregate-node LMPs (gitignored bulk)

PJM DataMiner2 `da_hrl_lmps` filtered `type = EHV`: the day-ahead LMP and its
published MEC / MCC / MLC components at PJM's `AGGREGATE` pnode for each
extra-high-voltage station — ~135 nodes across 15 zones, including **38 inside
the DOM zone alone** (PLEASANT VIEW, GOOSECRE, LOUDOUN, BRAMBLET, OX,
MORRISVILLE, BRISTERS, CLIFTON in the northern-Virginia data-centre pocket;
SURRY, CARSON, CLOVER, CHICKAHOMINY, BATH COUNTY, YADKIN in the south and
west). 2023–2025.

**Not committed.** Same PJM DataMiner2 non-member redistribution restriction as
`pjm-zonal-lmp/` — see `docs/data-licensing.md` §4. `SHA256SUMS.txt` is
committed as the provenance record.

## Refetch

```
PYTHONPATH=. .venv/bin/python scripts/data/fetch_pjm_ehv_lmp.py
```

One zstd Parquet per month, `da_ehv_lmps_<year>_<month>.parquet`, ~100 k rows
each.

**Gateway note.** The server-side `zone` filter is rejected with HTTP 400 on
archived rows older than ~2 years (verified 2026-07-29: `type=EHV&zone=DOM`
400s for 2023-01-05 while `type=EHV` alone serves that day's 3,240 rows across
15 zones) — the same restriction `fetch_pjm_transmission.py` documents for
`pnode_name`. The fetcher therefore pulls every zone and filters locally, which
is also strictly more useful: it measures the intra-zonal spread of **all eight
model zones**, not just the chartered one.

## Why EHV nodes and not the hubs

`FINDING-pjm136` §3 tested whether the 8-zone reduction can carry the DOM-vs-AEP
separation by comparing PJM's published trading **hubs** that sit inside one
model zone. That test could not be run on `PJM_Dominion`: PJM publishes no hub
there. The EHV aggregate pnodes cover every model zone, so the same
intra-versus-inter comparison finally runs on the zone the whole
pjm-133…pjm-137 lineage is chartered on (CLAUDE.md rule 14 `[R-ACCURATE]`:
measure it rather than assume the reduction is adequate).

## Consumers

* `scripts/probes/_pjm137_intrazonal_ehv_spread.py` — the pjm-137 M4
  intra-zonal dispersion measurement, against the inter-zonal DOM-vs-AEP spread.
