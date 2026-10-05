# G-DRIFT — closeout-MISO-w3e: control pin 381ee26c → lane head (zero LP)

**Scope.** This audit covers `git diff 381ee26c..bf2a9688` (and 66677404, a test-only reformat) over `src/`, `scripts/run_calibration*.py`, `scripts/replay_keeper.py`, `scripts/lib/` and `scripts/data/build_bench_part_zero_lp.py`.

**What changed in that range.**
- uc-milp UC-1
- closeout-ERCOT-w3 cliff split
- closeout-SOCO-w3 metered coal floor and rebuild-reader fix
- `nuclear_winter_capability_basis` (PJM)
- closeout-CAISO-w6 `caiso_chp_btm_measured`
- this lane's `miso_chp_btm_measured`

**What does not change.** `iso_configs.py` is unchanged and arms none of the new fields. The keeper recipe names none of them, and every one is a default-off cache-key optional, so the MISO `cache_key` is unchanged.

| hunk | verdict | reason |
|---|---|---|
| 14 new ScenarioConfig fields plus the UC refusal validator | INERT | All are default off or neutral. The validator runs only under `unit_commitment_milp`. |
| `NUCLEAR_MONTHLY_CF_UNCLIPPED_BY_YEAR`; `_apply_nuclear_winter_basis` | INERT | PJM only, gated on its flag. |
| `paths.EIA_923_DISPOSITION_*` | INERT | Read by the derive scripts only. |
| `assembly._coal_cliff_split_frac` and `legacy_bins.coal_curve_cliff_boundary` | INERT | Gated on `coal_perplant_cliff_split`. |
| `assembly.bins_to_fleet` CHP carve via `chp_btm_measured_armed` | INERT off / **LIVE arm** | Off, MISO returns False (the old branch was NYISO-only). On, the measured share replaces the default (`chp_steam_following=True`). |
| `coal_metered_online.py`; the `pipeline/commitment` diagnostic wrapper and its call sites | INERT | The wrapper returns `base_prep` unchanged when its flag is False. |
| `floor_mechanisms` MECH 28/29 labels | INERT | Labels only. |
| `pipeline/solve.py` UC block; `pipeline/uc.py`; `model/uc/*`; UC sidecars | INERT | Gated on `unit_commitment_milp`. |
| `run_calibration_full` new CLI flags | INERT | Tri-state, default None. |
| `_btm_frame` bench pin; `build_bench_part_zero_lp` | **LIVE (bench), declared** | Only `btm.parquet` `btm_bench_twh` changes. The LP is untouched (post-solve). The run-side `btm_twh` follows the flag. |
| `_run_config_mustrun_chp_btm` (SOCO rebuild-reader fix) | INERT | `mustrun_chp_btm_holdout` is False in the MISO recipe. |
| `clean_profiles` `uc-params` source | INERT (solve) | Built, but read only under the UC gate. |
| `uc_bench`, `uc_params/*` | INERT | Diagnostic scripts only. |

**Verdict.**
- For the control (flag off), no LP input changes. The only live hunk is the declared bench pin, which the PRECOMMIT handles by rebuilding the control's bench on the measured basis.
- For the arm, that bench pin plus the measured CHP capacity carve and its run-side add-back.

**No control solve is needed** (rule 29b).
