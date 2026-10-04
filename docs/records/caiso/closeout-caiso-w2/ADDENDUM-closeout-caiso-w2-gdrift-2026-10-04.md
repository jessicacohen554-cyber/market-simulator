# ADDENDUM closeout-CAISO-w2: owner ruling R-63 and G-DRIFT (2026-10-04, zero LP)

## Ruling

**R-63** (2026-10-04, desk relay of the decision card, verbatim): *"A: Arm it, solve 7 years (Recommended)"*.
`PRECOMMIT-closeout-caiso-w2-unprinted-rungs-2026-10-03.md` is therefore live as written. Its bars are unchanged.
The attestation will declare the arm as a ruling-authorised transfer (the R-CAISO-20 pattern plus R-63), not a
rule-13 measured admission.

## G-DRIFT (rule 29(b)): keeper legs `566bc8fa` → shard pin `e8570532` (main after #7184)

**1. Fleet-only input fingerprint.** Probe `scripts/probes/_closeout_caiso_w2_gdrift_fingerprint.py`; outputs
`_gdrift_fp_566bc8fa.json` and `_gdrift_fp_e8570532.json`.
- Method: the keeper recipe was rebuilt with `replay_keeper.run_year_kwargs` + `derived_run_year_inputs` +
  `run_year(fleet_only=True)` in a worktree at each SHA, for every year 2019–2025.
- Hashes compared:
  - unit set, per-unit pmax, availability (8760 h) and P0 marginal cost (every pricing overlay and the per-hub
    intertie injections applied);
  - demand;
  - wind and solar CF, capacity and offers;
  - storage power caps.
- **Result: identical in all 7 years.** Unit counts were 1,756 / 1,783 / 1,767 / 1,803 / 1,792 / 1,791 / 1,797.

**2. Hunk audit of the LP and solve path.** The diff covers 73 files across `src/` and the solve scripts. Every hunk
that could shape the LP after the fingerprinted inputs was classified:

| Area | Classification |
|---|---|
| `model/lp/rows.py`, `reserve_rows.py` | `sp.kron(eye(T), B)` → `lp/layout.kron_hours`. INERT as a byte-identical refactor: indptr, indices, data and dtypes match on 500 random blocks up to T = 8760, including duplicates and explicit zeros. Non-canonical blocks fall back to `sp.kron`. |
| `model/lp/model.py` | basis-status object array; float32 contiguous casts. INERT (same objects; post-solve diagnostics). |
| `model/storage.py` | hod quantile via `(days, 24)` reshape. INERT: identical floats. |
| `model/commitment.py`, `pipeline/commitment.py` | INERT: bool-index order is identical; the other change is SOCO-only. |
| `model/loss_demand.py`, `pipeline/solve.py` `p1_demand` | INERT: `zonal_loss_demand_reconciliation` is absent from the recipe (default False). **Latent:** it would be LIVE for CAISO if armed, because `caiso_zonal_loss_surface` is on. The shard prompts forbid it. |
| `model/lp/hydro_cascade.py`, `data/hydro.py` | INERT: `hydro_cascade_coupling` is off; values are identical. |
| `data/eia930/envelopes.py` | percentile-table refactor (identical floats) feeding consumers that are off for CAISO (`interchange_shaping`, `caiso_gas_commitment_floor`); PJM/NWPP functions. No CAISO corridor or intertie function changed. |
| `data/caiso_as_requirements.py` | INERT: `caiso_locational_as_families` is off. |
| `scripts/run_calibration*.py`, `replay_keeper.py` | NWPP/SPP/SOCO/ERCOT-scoped paths, coal-inventory paths (off), the deleted live-denominator field (rule 26), and `flipped_default_overlay` (it pins only `capacity_screen_peak_measured_hindcast`, which is read only on the forecast runner's hindcast path). All INERT. |
| `scripts/lib/benchmark_semantics.py` | **Scoring only:** R-33 put CAISO into `EIA930_GAS_FOLD_REFUTED`. The keeper's live status is already scored on it (closeout-caiso-impl), so the arm is compared against the HEAD-rescored keeper. |

**Verdict: no LIVE hunk on the CAISO backcast LP path. No control solve is earned.** Under §3 of the PRECOMMIT,
2022–25 remain the empirical tripwire: K5 requires every 2022–25 record to stay within noise of the keeper.

## Shards (launched 2026-10-04 ~00:29Z)

All shards are pinned to `e857053252d65b893bb171422002b5d75428cc36` and run in environment
`env_016R8xUY4maDbppZ6TEns5V8`, with prompts from `scripts/shard_prompt.py` and arm
`--set caiso_dsw_daytime_lateevening_unprinted_arm=true`. Each writes out-dir `closeout_caiso_w2_a1_<y>` on branch
`claude/closeout-caiso-w2-a1-<y>`.

| Year | Shard session |
|---|---|
| 2019 | `session_01PXAjR5KmAHpgiKXNpEHRCU` |
| 2020 | `session_013jsc6uTGNLbzJemJzxDr34` |
| 2021 | `session_015emjtHJFArfxMM7hGpsXx1` |
| 2022 | `session_01Geyosr1jbNBjE8A6isPfu1` |
| 2023 | `session_01JSk4YYrXMeH8LnysP2ZqgY` |
| 2024 | `session_01ARMwKMUz1kZqkXbHuUZKNB` |
| 2025 | queued (6-alive cap) |
