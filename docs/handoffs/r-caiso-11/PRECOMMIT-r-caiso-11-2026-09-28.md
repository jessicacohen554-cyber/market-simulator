# PRECOMMIT — R-CAISO-11 arm A: `caiso_tac_shares_standard_time` (2026-09-28)

Written and pushed **before** any shard solves.

## §1 The arm

- **Owner decision card 2026-09-28:** "Fix + solve now".
- **Recipe:** the keeper `2026-09-28-caiso-r10-nosa` recipe plus **one** flag: `caiso_tac_shares_standard_time=true`.
- **What the flag does:** it re-parses the OASIS TAC-area zonal shares on the fixed-PST clock the EIA-930 system total rides.
  - The historical parse used prevailing (DST) time, so every Apr–Oct share landed 1 h late.
  - Total load is unchanged. Only the zonal split moves.
- **Parameters:** zero (rule 14 source-clock correction; RESULT §4).
- **Years:** all seven the ISO carries, 2019–2025 (rules 34(c), 35(c), 36). One shard per year.

| Years | Recipe source bundle | SD cap (MW) |
|---|---|---|
| 2019–2021 | `rcaiso10_A_tp_2019_2021` | 1436.0 |
| 2022–2023 | `rcaiso10_A_span` | 1436.0 |
| 2024 | `rcaiso10_A_span` | 2074.0 |
| 2025 | `rcaiso10_A_span` | 2071.0 |

## §2 Controls, G-DRIFT and the promotion rule

**Controls (rule 29(b)).** The keeper's committed bundles are the controls: `rcaiso10_A_span` (2022–25) and `rcaiso10_A_tp_2019_2021` (fold). No control solves.

**G-DRIFT.** `git diff 4caee8d0 HEAD` over `src/market_sim`, `scripts/run_calibration*.py`, `scripts/lib`, `scripts/data/curate_zonal_shares.py`, `data/raw/_validation-source` and `data/raw/reference`. Every hunk is classified below.

| Hunk | Verdict | Reason |
|---|---|---|
| `data/raw/reference/custom-bin-assignments.csv` (W A Parish rows) | INERT | ERCOT sheet |
| `data/fleet/campd_bins.py`: split-child parent map | INERT | The only split children in any committed sheet are ERCOT 34702 and 49392 |
| `data/fleet/campd_bins.py`: `campd_st_gas_span_coverage` sub-gate | INERT | Requires `campd_unit_fuel_split`, which is false in the keeper |
| `data/fleet/campd_bins.py`: `_fuel_split_companion(base, fuel_split)` | INERT | Changes only when `fuel_split` is truthy |
| `data/fleet/arrays.py`, `data/outages.py`, `data/resolved_inputs.py`: `unit_outage_rederive_peaker_windows` (PJM-NEXT-6) | INERT | Default off and absent from the recipe; `resolved_inputs` is provenance accounting |
| `config/scenarios.py`: two new default-off fields | INERT | Absent from the recipe |
| This lane's own flag hunks (`scenarios.py`, `demand.py`, `zonal_shares.py`, `curate_zonal_shares.py`, both runners) | THE ARM | Byte-identical when off: the extra kwarg is passed only when True |

**All non-arm hunks are INERT ⇒ form 4 is valid.**

**Promotion rule, fixed now.** Structure first (rule 1). This is a correctness fix, so it is promotable unless it breaks a load-bearing criterion that the keeper passes on 2022–25. Every movement is reported at full magnitude whichever way it goes. It is never selected on the residual.
