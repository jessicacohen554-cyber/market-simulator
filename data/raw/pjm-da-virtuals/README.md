# pjm-da-virtuals — raw (gitignored)

PJM DataMiner2 Day-Ahead demand-side bid feeds, one compressed Parquet per
feed per calendar month:

* `hrl_da_incs_decs_<year>_<month>.parquet` — hourly INCrement offer
  (virtual supply) and DECrement bid (virtual demand) curves, RTO-aggregated
  by price point: one row per (hour × price point) with `inc_mw` / `dec_mw`.
  These are **submitted ex-ante bid curves** (participant inputs like
  generator energy offers), never cleared outcomes — the G-22 lever-B DA
  procurement-depth mechanism (`ScenarioConfig.pjm_da_virtual_bids`,
  `src/market_sim/data/virtual_bids.py`) clears them endogenously in the LP.
* `hrl_dmd_bids_<year>_<month>.parquet` — hourly total day-ahead demand bid
  MW by area (PJM_RTO / MID_ATLANTIC_REGION / WESTERN_REGION), kept as a
  cross-check of the physical demand-bid base.

**This directory's contents are gitignored** (see `.gitignore`): PJM
DataMiner2 data carries a non-member redistribution restriction (see
`docs/data-licensing.md` §4 and the `pjm-energy-offers` precedent). Only
this README is tracked; the derived, committable artifact is the
condition-binned multiplier surface
`data/raw/_validation-source/pjm_da_virtual_surface_condbinned.json`
(`scripts/derive_pjm_da_virtual_surface.py`) — normalized multipliers, never
prices.

**Regeneration:**

```bash
python scripts/fetch_pjm_da_virtuals.py                # 2023-2025, all months
python scripts/fetch_pjm_da_virtuals.py --years 2024
python scripts/fetch_pjm_da_virtuals.py --feeds hrl_da_incs_decs
python scripts/fetch_pjm_da_virtuals.py --force        # re-download existing
```

Auth uses the public `Ocp-Apim-Subscription-Key` published in DataMiner2's
own `settings.json` (same as `scripts/fetch_pjm_energy_offers.py`).
`hrl_da_incs_decs` is posted monthly on a four-month delay;
`hrl_dmd_bids` daily. Retention is indefinite.
