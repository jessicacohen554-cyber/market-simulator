# `pjm-zonal-lmp/` — PJM transmission-ZONE LMP components (gitignored bulk)

PJM DataMiner2 `da_hrl_lmps` / `rt_hrl_lmps` rows filtered to `type = ZONE`:
hourly LMP with its published `system_energy_price` (MEC), `congestion_price`
(MCC) and `marginal_loss_price` (MLC) components, for all 21 PJM transmission
zones plus the two rollup pnodes (`PJM-RTO`, `MID-ATL/APS`), 2023–2025.

**Not committed.** Same PJM DataMiner2 non-member redistribution restriction as
`pjm-energy-offers/` and `pjm-da-virtuals/` — see `docs/data-licensing.md` §4.
Only the small dimensionless *derivative* is committed:
`data/raw/iso-specific-transmission/PJM_loss_surface.csv`.

## Refetch

```
PYTHONPATH=. .venv/bin/python scripts/data/fetch_pjm_zonal_lmp_components.py
```

One zstd Parquet per feed-month, `<feed>_<year>_<month>.parquet`. Provenance for
each file is recorded in `SHA256SUMS.txt` (rewritten by every run, and by
`--manifest` alone) so a re-fetch can be checked byte-for-byte against the pull
the committed surface was derived from — the MISO `bc_HIST` precedent
(`data/raw/lmp-data/MISO/README.md`).

**Gateway note.** DataMiner2 rejects some multi-day windows on these feeds with
HTTP 400 while serving each half of the same window fine (reproduced
2026-07-28: `da_hrl_lmps` 2024-07-01..31 and 2024-07-16..31 both 400,
2024-07-01..15 fine). The fetcher bisects the window down to single days on a
400 and reports any month that still comes back short, so a truncated month
fails loudly instead of being written.

## Why zone pnodes and not the committed hub file

`data/raw/lmp-data/PJM_<year>_rt_da_monthly_lmps.csv` carries the same four
component columns but only for PJM's twelve trading **hubs**, which are price
baskets that do not align to the model's eight zones: three hubs sit inside
`PJM_ComEd` alone, while `PJM_West_APS`, `PJM_Central_PA` and `PJM_SWMAAC` have
no hub at all — and two of those three are `PJM_Dominion`'s other import paths.
The `type = ZONE` pnodes are the load-weighted zonal prices the model's zonal
duals are the analogue of and crosswalk 1:1 onto every model zone via
`market_sim.data.eia930.zonal_shares._PJM_LOAD_ZONE_GROUPS` (CLAUDE.md rule 14
`[R-ACCURATE]`).

## Consumers

* `scripts/data/derive_pjm_loss_surface.py` — the frozen (rule 23) derive
  producing `PJM_loss_surface.csv`, consumed by
  `ScenarioConfig.pjm_zonal_loss_surface`.
* `scripts/probes/_pjm136_model_vs_measured_zonal.py` — the pjm-136 M1a/M1b/M2b
  measurement of the model's zonal dual structure against PJM's own.
