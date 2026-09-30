# RESULT — R-ERCOT-19: EIA-923 Finals zonal-gas refresh PROMOTED; the commitment-profile sub-gates stay off

**Owner decision card, answer verbatim: "Promote A only (Recommended)".**
Keeper `2026-09-30-r-19-eia-923` (bundle `results/calibration/r_ercot19a_span`, 2019–2025) supersedes `2026-09-30-r-18-drag-index`.
PRECOMMIT: `PRECOMMIT-r-ercot-19-south-overrun-and-hub-refresh-2026-09-30.md` (§§1–7, addenda A and B).

## What was promoted

- **Arm A = a data correction (rule 23/14).** The 2024/2025 North / Northeast / South / South_Central member rows of `data/raw/ercot_zonal_gas_hub.csv` are re-derived on the EIA-923 Sch5 **Finals**.
- The recipe is byte-equal to the prior keeper (`config_partition_overrides` equal). 2019–2023 are byte-identical. 2024/2025 were re-solved.
- DOF ledger unchanged. Offer multipliers untouched.

## Three arms vs the keeper

| Year | Keeper r-18 | A: data refresh (**promoted**) | B: A + both commit limbs | C: A + CC limb only |
|---|---|---|---|---|
| 2019 | NOT-YET | NOT-YET (byte-identical) | NOT-YET (fail-closed) | NOT-YET (fail-closed) |
| 2020 | NOT-YET · C1 CC +12.39 | NOT-YET · same | NOT-YET · C1 CC +11.33 | NOT-YET · C1 CC +11.21 |
| 2021 | CALIBRATED | CALIBRATED | CALIBRATED | CALIBRATED |
| 2022 | CALIBRATED · C1 CC −7.69 | CALIBRATED · same | **NOT-YET** · C1 CC −8.42 | **NOT-YET** · C1 CC −8.66 |
| 2023 (carve-out) | NOT-YET · C3a −19.8 % | NOT-YET · same | NOT-YET · −19.4 % | NOT-YET · −19.5 % |
| 2024 | NOT-YET · C3a −10.7 % | NOT-YET · −10.7 % | **CALIBRATED** · −9.88 % | NOT-YET · −10.04 % |
| 2025 | CALIBRATED · C3a −9.6 % | CALIBRATED · −9.8 % | CALIBRATED · −9.0 % | CALIBRATED · −9.0 % |
| C8 ST_GAS | 16–30 % | ≈ keeper | +0.7 to +3.4 pp | ≈ keeper |

- C1 tolerance is ±8.00 TWh. C3a is ±10 %.
- Arm B: the drag-hour limb **missed its object**. D-4 `st_netload_drag` FAILs went 8 → 8, the same rows.
- Arm B's 2024 pass rests on $0.05/MWh of LW price (28.09 vs 28.04 in arm C).

## Why A only

- A corrects an input and changes no determination.
- B and C each move one validation year worse (2022), and neither moves a train year cleanly better.
- The over-run the commit limbs targeted is carried mostly by the `econ*` tranches. Neither limb touches them (PRECOMMIT §1).

## Standing state

- ISO stays **NOT-YET**: 2023 carve-out (owner hold k=33) and 2024 C3a −10.7 %.
- 2025 C3a −9.8 % is now 0.2 pp from the edge.
- Both sub-gates stay in code, **default off**: `cc_committed_prior_year_commitment_eligibility` and `netload_drag_prior_year_hour_profile`. Their matrix cells record them as probes.

## Provenance and retrievability

- Arm A legs (rule 33(d), provenance only): pinned `a63b8e945c88fa397e06d1d8698692c8f2b94c60`. 2024 `adfb6b34112add3a7452df8e1aa79964975eaa41`, 2025 `29adb8831884545b72f6706506cd169ce22a4d48`.
- Arm B/C legs: pinned solve SHA `41e0f2422bf7147a2f66652aa5bcefeffe0d1e27`. Branches `claude/r-ercot19{b,c}-arm-*`.
- The keeper bundle is on `main`. Runs B and C were pruned at this promotion (rule 35). Reproducing either costs about 7 × 25 min of shard LP.
- The 16 shard branches `claude/r-ercot19*-arm-*` are left for the owner to remove, because a session cannot delete refs.
