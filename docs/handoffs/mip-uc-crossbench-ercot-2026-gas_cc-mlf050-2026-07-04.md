# MIP unit-commitment cross-benchmark — ERCOT 2026, first 744h

*Generated 2026-07-04 by `scripts/diag_uc_mip_crossbench.py` (PP-3.4). **DIAGNOSTIC ONLY — production stays pure LP.***

Quantifies the LP-relaxation commitment bias: the production P1 LP has `pmin=0` on every tranche (DP-1), so min-load is emergent, not enforced. This adds true integer commitment (binary on/off + min-load + min-up/min-down + explicit startup cost) on the CAMPD committed tranches and compares.

## Configuration

- **ISO / year / horizon:** ERCOT / 2026 / first 744 h
- **Integer fuel class(es):** gas_cc
- **Committed tranches made integer:** 40
- **Min-load block:** 0.50 x available committed capacity
- **MIP columns / rows:** 628,680 / 196,550 (29,760 binaries)
- **MIP status / gap:** HighsModelStatus.kOptimal / 1.55e-07
- **Wall clock:** 68s

## Results — committed tranches + system CO2

| Solution | Committed energy (MWh) | Committed starts | System CO2 (t) |
|---|---:|---:|---:|
| P1-LP | 2,960,907 | 664 | 17,399,055 |
| LP-relax | 3,924,302 | 66 | 17,387,308 |
| MIP-UC | 3,924,019 | 66 | 17,387,318 |

### Integrality bias (MIP-UC − LP-relax, same objective & constraints)

- **Committed min-load energy:** -283 MWh
- **Committed starts:** +0
- **System CO2:** +10 t

### Versus production P1 (MIP-UC − P1-LP)

- **Committed min-load energy:** +963,112 MWh
- **Committed starts:** -598
- **System CO2:** -11,736 t

## Reading the sign

- **Min-load energy up under the MIP** ⇒ the LP under-books the energy a committed unit must produce once synced (it ramps continuously from 0). That energy displaces marginal generation and shifts the CO2 tally.
- **Starts down under the MIP** ⇒ min-up/min-down suppress the fast on/off cycling the LP relaxation allows for free, so the LP over-books cycling (and under-books the startup fuel/CO2 that EM-5 notes is unmodeled).
- The **MIP−LP-relax** row is the clean integrality bias (identical economics); the **MIP−P1** row also folds in the base-cost vs amortized-bid difference and is the 'vs what production ships' view.

## Caveats

- Integer set restricted to one fuel class for tractability; a bounded MIP gap means the reported MIP is near- not provably-optimal (gap above).
- One month is a commitment snapshot, not an annual bias; widen `--hours` / `--fuel` when runtime allows.
- `min_load_frac=1.0` treats the committed tranche as a full sync block (the strongest min-load); lower it to model partial min-stable-load.
- **This never enters production** (CLAUDE.md pure-LP stack rule); nothing in `src/` imports this script.
