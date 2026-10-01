# ADDENDUM — R-CAISO-14 (2026-09-29): G-DRIFT extension and pin

Extends PRECOMMIT-r-caiso-13 §2. Written before any shard was launched.

**Pinned SHA:** `332c804834aa08a10d24f48adcb168296139e1f5` (origin/main HEAD). It contains
`frames.set_caiso_eia930_clock_repair` (frames.py:522) and `docs/records/caiso/r-caiso-13/shard-prompt.md`.

## G-DRIFT 14c1d70e → 332c8048 (solve paths)

13 non-merge commits touch the solve-path set. Every hunk is INERT for a CAISO backcast, except the arm itself.

| Commit | Verdict | Gate |
|---|---|---|
| 2ff9c9ae SPP-100 | INERT | `chp_steam_floor_conduct_scope` (default off, absent from recipe) |
| 43b52817 / fbc89ab9 NWPP-NEXT-8 | INERT | `coal_fuel_inventory_monthly_pile`, which needs the plant-grain coal path; all coal-inventory flags are off for CAISO. `lp/rows.py` sits inside `coal_plant_budget is not None`. The parity registry is governance only |
| e6845774 SPP-99 | INERT | `campd_split_remap_companions` (default off) |
| ef941198 NYISO-NEXT-11 | INERT | `nyiso_ne_ac_node` (NYISO, default off). The `_bridge_floored_fleet` bool path is unchanged |
| f26384a7 NYISO-NEXT-11 | INERT | `nyiso_firm_imports` deleted. caiso.py / import_nodes.py changes are docstring only. Retired key at drop value False |
| e9fc1a5e PJM-NEXT-8 | INERT | `unit_outage_exit_cohort_repair` (default off) |
| d8a557bf, 383d1128 soco-84 | INERT | SOCO reported-only intake and scoring; CAISO LMP entries untouched |
| ab2ea9ee, 2af9ab74 R-ERCOT-12 | INERT | `ISO_PLANT_ENTRIES` has an ERCOT key only, so `plant_entry_first_inside_row("CAISO", y) == {}` |
| 695ce419 miso-280 | INERT | The unconditional `CAMPD_UNIT_PLANT_REMAP` row is WI facility 55641; CAISO reads CAMPD for CA and NV only |
| acf38d1e R-CAISO-13 | THE ARM | Gated default off |

**Solve-surface:** CAISO `moved_rows` is byte-identical to the keeper's `solve_surface.moved`. The two new names are dropped at their declared hash.

**Result:** form 4 is valid, and the keeper's committed bundles are the control (rule 29(b)).
