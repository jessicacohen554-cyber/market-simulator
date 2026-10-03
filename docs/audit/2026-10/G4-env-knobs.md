# G4 — Environment-variable solve knobs (audit A5, rule 24)

Owner ruling 2026-10-03: fingerprint the env-var solve knobs in the solve
surface, or prove them inert with a zero-LP audit. Zero-LP audit of every
`os.environ` / `getenv` read in `src/market_sim`, `scripts/lib`, `scripts/run_*.py`
at `1f983982` (branch `claude/audit-rulings-2026-10`). No LP was solved.

## Classification

LIVE = can move which degenerate vertex (and returned dual) HiGHS lands on, or
which input bytes the LP is built from; never the optimum. INERT = cannot touch
the solution or any scored output.

| Variable | Read at | What it changes | Class | Recorded (before → after) |
|---|---|---|---|---|
| `MARKET_SIM_WARMSTART` (default `1`) | `pipeline/solve.py:490`, `pipeline/basis_cache.py:107` | Builds a persistent P0 `DispatchModel`; P1 warm-starts from the P0 basis. `0` = cold P1 rebuild | LIVE | no → `environment.env_solve_choices.warmstart` |
| `MARKET_SIM_WARMSTART_XYEAR` (default `0`) | `pipeline/solve.py:538`, `basis_cache.py:108`, `scripts/run_calibration.py:8786-8791` | Cross-year basis carry (rule 36) | LIVE | no (only in prose) → `…warmstart_xyear` |
| `MARKET_SIM_P1_BASIS_SEED` (default `0`) | `pipeline/solve.py:579`, `run_calibration.py:8718-8723` | Same-year P0→P1 basis seed | LIVE | no → `…p1_basis_seed` |
| `MARKET_SIM_P1_FLOOR_INPLACE` (default `0`) | `pipeline/solve.py:758,780` | In-place P1 refloor on the warm model vs cold rebuild | LIVE | no → `…p1_floor_inplace` |
| `MARKET_SIM_P0_CACHE` (default off) | `model/lp/p0_cache.py:174` (switch), `:190` (`MARKET_SIM_HIGHS_THREADS==1` pin), `:197` | Hands a stored P0 solution/basis to the solve; effective only with the pin | LIVE | no → `…p0_cache` (effective bool) |
| `MARKET_SIM_HIGHS_THREADS` | `model/lp/model.py:678-680` (`setOptionValue("threads")`), `p0_cache.py:190`, `model.py:1890` (log only), pinned to `1` by `scripts/lib/solve_container.py:63-67` | HiGHS thread option; multi-threaded dual simplex is not bit-reproducible (`docs/cross-year-warmstart.md`) | LIVE | log string only → `…highs_threads` (int option value, 0 = automatic) |
| `MARKET_SIM_HIGHS_LEAN` | `model/lp/model.py:687-688` | `simplex_scale_strategy = 0` | LIVE | no → `…highs_simplex_scale_strategy` (option value; solver default when off) + `…highs_lean` |
| `MARKET_SIM_USE_CLEAN` | `data/clean_access.py:39` and 11 sibling loaders (`campd.py:63`, `renewables.py:1789`, `fleet/models.py:52`, `hydro.py:57`, `outages.py:82`, `fuel/_shared.py:115`, `cod_ramp.py:81`, `neighbor_price.py:859`, `zone_assignment.py:54`, `eia930/frames.py:293`) | Curated-Parquet read path instead of raw | LIVE (input routing; identical bytes only when `data/clean` is current) | no → `…use_clean` |
| `MARKET_SIM_DATA_ROOT` | `config/paths.py:45` | Relocates the data/results root; `cache_key` folds it to a sentinel | INERT | already: `environment.market_sim_data_root`, `cache_key_path_roots` |
| `MARKET_SIM_MEM_DEBUG` | `model/lp/model.py:60,640` | VmRSS/VmHWM log lines | INERT | not needed |
| `MARKET_SIM_RESERVE_DUAL_DUMP` | `scripts/run_calibration_full.py:7336` | Writes a separate `reserve_diag/*.npz` sidecar | INERT | not needed |
| `MARKET_SIM_NEIGHBOR_HR_FORWARD_SKILL` | none (comment at `config/scenarios.py:7950`) | Removed; now `ScenarioConfig.neighbor_hr_forward_skill` | — | `scenario_config` |
| `HIGHS presolve` | `model.py:686` hard-coded `"off"` (no env) | — | — | recorded as `…highs_presolve` so the HiGHS option triple is complete |

Out of the `MARKET_SIM_*` inventory but found by the grep: nine `ERCOT_*`
diagnostic flags read at `pipeline/backcast_config.py:1413-1510`
(`ERCOT_ZONAL_GAS`, `ERCOT_GAS_FLOOR`, `ERCOT_GAS_FLOOR_BASIS`, `ERCOT_GAS_HAIRCUT`,
`ERCOT_OIL_PRIMARY`, `ERCOT_WEST_NETLOAD_GAS`, `ERCOT_WEST_GAS_FIRM_BASIS`,
`ERCOT_WEST_GAS_COLLAPSE_FREQ`, `ERCOT_WEST_ENDOGENOUS_COLLAPSE`,
`ERCOT_WEST_GAS_DELIVERED_FLOOR`). LIVE, but each resolves into a
`ScenarioConfig` field, so the value is already in `scenario_config` and in
`cache_key`. They are still env-var channels in the letter of rule 24; left for
an owner ruling (promote to CLI flags, or delete under rule 26). The
`SOLVE_ENV_PINS` (`MALLOC_ARENA_MAX`, `OMP_NUM_THREADS`) are allocator/BLAS
settings, inert to the LP.

## The fix

`src/market_sim/pipeline/persist.py`: new `env_solve_choices()` (+
`ENV_SOLVE_KNOBS`, `HIGHS_OPTION_DEFAULTS`), nested as
`environment.env_solve_choices` in `environment_block()` — the existing
mechanism that already records `MARKET_SIM_DATA_ROOT` and is stamped into both
`meta.json` and the top-level `run_config.json` (`scripts/lib/run_record.py:453`,
`persist.py:389`). Each knob is parsed exactly as its reader parses it, so an
unset variable records the solve-path default. The two HiGHS knobs record the
option VALUE installed on the `Highs` object (threads int; `simplex_scale_strategy`
0 under LEAN, else the default queried from a fresh `Highs()` — 2 on the pinned
highspy 1.14.0 — with a constant fallback for solver-less checkouts).

Not fingerprinted into `cache_key`: re-keying would orphan every committed
keeper's `solve_surface.json`. Additive and inert like the enclosing block:
`cache_key` never reads it, `--reuse-solved` diffs only `scenario_config`,
`replay_keeper._warn_on_environment_mismatch` compares three version fields,
`audit_keepers` E11 excludes `environment`. Only runs solved after this lands
carry the block.

Docs: `docs/codebase/08-config-reference.md` §8.4a (the table),
`docs/codebase/02-lp-dispatch.md` (thread bullet), `docs/user-manual.md`
(the `MARKET_SIM_WARMSTART_XYEAR` default read **ON**; it is OFF since 2026-09-19).

## Test

`tests/unit/pipeline/test_persist_env_solve_choices.py` (fast lane, zero-LP):
defaults when unset; `MARKET_SIM_HIGHS_LEAN=1` records `simplex_scale_strategy=0`;
`MARKET_SIM_P0_CACHE=1` without the thread pin records `p0_cache=false`;
`run_record.write_run_config` carries the block.

```
$ .venv/bin/python -m pytest -q tests/unit/pipeline/test_persist_env_solve_choices.py -x
4 passed in 1.98s
$ .venv/bin/python -m pytest -q tests/regression/test_run_record_provenance.py \
    tests/regression/test_persisted_identity.py \
    tests/regression/test_script_import_env_hygiene.py \
    tests/unit/pipeline/test_xyear_warmstart_default.py
68 passed, 109 subtests passed in 22.16s
$ ruff check / ruff format --check (persist.py, the test): clean
$ python -m compileall -q src scripts: clean
```
