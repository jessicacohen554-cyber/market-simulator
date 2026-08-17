# data/raw/PJM — orphaned PJM DataMiner2 exports (payloads untracked)

**The payloads in this directory are GITIGNORED at tip** (BLOAT-S2 Stage-2
(a)-only untrack, 2026-08-17, O2 grant —
`docs/DECISION-CARD-bloat3-stage2-charter-2026-08-16.md`; evidence pass
`docs/FINDING-bloat-s2-evidence-passes-2026-08-17.md` §2). Only this README,
`SHA256SUMS.txt` (the identity record of the removed bytes) and `.gitkeep`
stay tracked.

## What the files were

| File | Feed | Years |
|---|---|---|
| `PJM_<year>_rt_hrl_lmps.csv` | DataMiner2 `rt_hrl_lmps` (hourly RT LMPs) | 2018–2022 |
| `PJM_gen_by_fuel_<year>.csv` | DataMiner2 `gen_by_fuel` | 2018–2025 |

## Zero consumers — the naming trap (measured 2026-08-17)

This corpus was an **orphan**: no file under `src/`, `scripts/`, or `tests/`
reads it. The live corpora sit elsewhere with near-identical names:

- gen-by-fuel: `data/raw/ISO-specific-gen-data/PJM_<year>_gen_by_fuel.csv`
  (year-before-fuel; read by `scripts/data/curate_generation.py`).
- LMP actuals/bench: `data/raw/lmp-data/PJM_<year>_rt_da_monthly_lmps.csv`
  (read by `scripts/data/derive_actual_lmp.py` and `scripts/data/curate_lmp.py`;
  golden-tier-listed).

Do NOT re-commit payloads here; extend the live corpora instead.

## Recovery — re-fetch only (story (a); no pin, no history route)

Source: PJM DataMiner2 REST API (`https://api.pjm.com/api/v1/<feed>`), public
subscription key embedded in DataMiner2's own settings — the shared client is
`scripts/lib/pjm_dataminer.py`. **Measured 2026-08-17:** both feeds served
2018-01-01 rows live through that client (`rt_hrl_lmps`, `gen_by_fuel`) —
Data-Miner-class stable archive, retention reaches the corpus's oldest
vintage. Feed reference: `https://dataminer2.pjm.com/feed/gen_by_fuel`,
`https://dataminer2.pjm.com/feed/rt_hrl_lmps`. Licensing:
`docs/data-licensing.md` §4 (non-member redistribution restriction — the same
posture as `pjm-energy-offers`).

`SHA256SUMS.txt` records the exact removed bytes (a re-fetch returns the same
data but not necessarily byte-identical CSV serialization).
