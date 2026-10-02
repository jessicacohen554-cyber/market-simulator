# ADDENDUM: PJM-NEXT-26 solves the PJM-NEXT-25 arm at the W0 posture

Written 2026-10-02, **before any PJM-NEXT-26 shard launched**. Zero LP. Amends only the control and the
recipe of `PRECOMMIT-pjm-next-25-2026-10-02.md`; its S1–S4 / P1–P2 statements and decision rule are
unchanged.

## 1. Why

`main` moved 25 merges past the arm's base (`06f1258c` → `3ec2fd3e`). They include the W0 EIA-860
settlement (#7037, #7047, #7049), which is LIVE on every PJM year (W0 census: model summer Σpmax moves
−2.5 … +0.5 %), and the PJM renewables membership fix (#7040). W0 is armed for PJM by `--set` on the
replayed recipe, not by the keeper's recorded config: a bare replay of `pjmnext16_A_span` would solve the
pre-W0 posture on post-W0 code, which no keeper carries and `promote_keeper.py` preflight 0c (fleet
census) would refuse.

The W0 phase-3 PJM legs (closeout-B, `results/calibration/w0_pjm_<Y>`, branches
`claude/w0-pjm-<Y>-fix2` and kept legs per `W0-phase3/KEPT-LEG-INERT-PROOF-2026-10-02.md`, pinned at
`25da6022`) are the PJM W0 control.

## 2. Recipe

`results/calibration/pjmnext16_A_span` replayed with the ten W0 overrides the W0 PJM legs carry, verbatim:
`seasonal_capacity_basis`, `backcast_actual_retirement_only`, `commission_year_cod_fallback`,
`cc_block_summer_rating`, `cc_steam_part_capacity`, `retiree_vintage_status_scope`, `admit_standby_units`,
`partial_plant_exit_carry`, `mid_vintage_exit_carry`, `unit_outage_dispatched_bin_denominator` = true.
The arm itself stays data only (the appended `thermal_tranches_PJM.csv`, sha256 `31455aaa…`).

## 3. G-DRIFT `25da6022` → `3ec2fd3e` (rule 29(b)), PJM backcast path

| Hunk | Class | Reason |
|---|---|---|
| `backcast_config.caiso_ra_min_load_frac` 0.26 → 0.570 | INERT | CAISO-only expression; PJM records 0.40 either way |
| `run_calibration.COAL_PLANT_GRAIN_ISOS` + ERCOT; `COAL_PILE_CEILING_ISOS = ("ERCOT",)`; ceiling-only pile branch; `load_coal_measured_receipts` refactor | INERT | every branch is behind the coal-pile / take-floor flags and ISO tuples; PJM is in none |
| `coal_fuel_inventory.reconcile_floors_to_yard_budget(month_index=)` | INERT | annual path byte-identical; only the multi-column budget branch is new |
| `scripts/lib/replay_recipe.py` rule-26 inert skip | INERT | replay guard tooling, no solve input |

All INERT. With the W0 overrides, the candidate differs from the W0 PJM control by the appended rows only.

## 4. Reading

- **Primary control:** the composed W0 PJM span. S1 (slack + dump), S2 (cohort contrast), S3 (rule 20 /
  D-4) and S4 (2023–25 training-tier verdicts) are read against it. This is the single-delta comparison
  the PRECOMMIT intended.
- **Reported:** the same rows against the incumbent keeper `pjmnext16_A_span`. That comparison is
  W0 + rows and is never used to accept or reject the arm.
- **Promotion order.** The PJM W0 span is closeout-B's to promote. If S1–S4 hold, this lane promotes after
  the W0 span is the keeper, or presents the owner a decision card if it is not yet.
