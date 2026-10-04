# FINDING — G-OFF for NWPP and PJM discharged zero-LP: the UC engine is inert on both keeper recipes, every year

Lane UC-1-FINISH (`session_01CghV9pMqkD5TDmYicDuMCx`, Fable), 2026-10-04, chartered by
UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`). Method: the NYISO record
(`FINDING-ucmilp-golden-nyiso-main-drift-2026-10-04.md` §2) and the MISO record
(`FINDING-ucmilp-golden-miso-recipe-gap-2026-10-04.md` §2), zero LP. Every capture
runs the keeper recipe for one year up to `run_calibration.run_energy_solve` and
records its whole argument set, then aborts before any LP.

## 1. Why zero-LP

* **NWPP:** the golden shard (`session_018p9sYjxv2bZqyvNefSqzfX`, report
  `claude/ucmilp-golden-nwpp` @ `ecb1b8df`) solved 2019 only before its 90-minute
  budget (single-thread P0 + P1 ≈ 73 min per year). 2019 read PASS on 5 files and
  26 columns. Main has since promoted a new NWPP keeper, `2026-10-03-nwpp-next-27-path76`
  (bundle `results/calibration/nwppnext27_span`, basis `440ad144`), so the PR lands
  on a recipe the shard never replayed.
* **PJM:** two golden shards (`session_01RCVRyknDphK8VRfoxZzo3D`,
  `session_01K6VgF7ceq6cUf3HgtrVaTp`) were OOM-killed in 2019; the container has
  no swap. Per the charter, no third relaunch.

## 2. Trees and data

| Tree | Checkout |
|---|---|
| main-without-UC | sparse worktree at `origin/main` `d62ae1a7` (the rebase base) |
| branch | the rebased UC-1 tip (UC files byte-identical to `6d47c762`) |

One `data/clean`, regenerated at the branch (`--solve-profile NWPP`, `PJM`), and one
`data/raw` serve both trees. PJM's recipe arms `pjm_da_virtual_bids`, so the DA
virtual-bid parquets were fetched with `scripts/data/fetch_pjm_da_virtuals.py
--years 2019 … 2025` (gitignored, 169 files). Comparison at atol = rtol = 0
(`np.array_equal`; sparse by `(A != B).nnz`) over `mc_base`, `demand`, `FleetArrays`,
every `run_energy_solve` keyword, every `dispatch_kwargs` entry, the fleet, and the
config. Ignored: the nine `uc_*` / `unit_commitment_milp` fields at their defaults,
and checkout-absolute path strings.

## 3. Results

| Keeper (bundle) | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| NWPP `nwppnext27_span` | identical | identical | identical | identical | identical | identical | identical |
| PJM `closeout_pjm_nuc_full_span` | identical | identical | identical | identical | identical | identical | identical |

The only reported difference in any year is a checkout path. For NWPP it is
`config.cc_capacity_reconcile_path` (`/home/user/ms-main2/…` vs
`/home/user/market-simulator/…`, the same file). For PJM it is the in-run
`cache_key()`. Its pre-hash payload differs in one entry,
`cc_capacity_reconcile_path`: the main worktree reaches `data/` through a symlink
outside its own root, so `_normalize_cache_key_paths` does not fold that path to
`<repo>`. No `uc_*` field enters the payload on the branch (G-KEYS).

## 4. Verdicts

* **G-OFF NWPP: PASS (engine-inert) by zero-LP input identity, 2019–2025**, on the
  keeper the PR lands on (`nwppnext27_span`). The partial golden on the previous
  keeper agrees (2019 exact).
* **G-OFF PJM: engine-inert by zero-LP input identity, 2019–2025; full replay not run
  (OOM in the shard container class).**

Both rest on the same argument as NYISO and MISO. The inputs to `run_energy_solve`
are identical, and the only code inside it that differs is the
`if config.unit_commitment_milp:` hunk, which does not run off-gate. The two post-solve
drains (`run_calibration_full.py`, `runner.py`) sit under the same gate. Limit: this
proves input identity, not output identity. It does not test whether the keeper
bundle itself reproduces at HEAD (main drift), which is outside the gate.

## 5. Side finding — the slow UC window test is order-sensitive in one process

`tests/unit/model/uc/test_window_captured.py` calls `uc_bench.capture_year`, which
runs `solve_and_persist` up to the spy. On the way, the solve-container env pins
(`scripts/lib/solve_container.py`) write `MARKET_SIM_HIGHS_THREADS=1`,
`OMP_NUM_THREADS=1` and `MALLOC_ARENA_MAX=2`, and `pin_determinism_env` writes the
two warm-start pins, into `os.environ`. None is restored (measured: the env diff
across one `capture_year` call is exactly these five keys). If an earlier test in
the same process already ran HiGHS at the default thread count, the HiGHS global
scheduler is fixed at that count. Every later `Highs` run with `threads = 1` then
returns model status "Not Set". The symptom: the captured test and all six
toy-window tests fail when they run after `test_stage_pipeline.py`.

| Run | Result |
|---|---|
| `pytest tests/unit/model/uc -m ""` | 7 failed, 12 passed |
| same, `MARKET_SIM_HIGHS_THREADS=1` exported first | 19 passed |
| each file alone | passes |
| fast tier (`-m "not slow …"`, the CI lane) | 11,549 passed, 0 failed |

This is not an engine defect: a solve shard pins the env before its first HiGHS
call (`prepare_solve_container.py --emit-exports`, and the runners' own `ensure_solve_container` before their first solve). It will
bite a full-lane `pytest` run and a ladder rung that varies `threads` inside one
process (rung L2's threads arm). Fix, applied in this lane's PR (the UC-1 files moved off `6d47c762` anyway, for
the `artifact_dir` defect UC-2-SPP routed): an autouse fixture in the captured test
restores the five env keys through `monkeypatch` and calls
`highspy.Highs.resetGlobalScheduler(True)` before and after. After the fix,
`pytest tests/unit/model/uc tests/unit/config/test_uc_fields.py
tests/test_curate_uc_params.py -m ""` reads 45 passed with no env pre-pinned.
Rung L2's threads arm should still run each arm in its own process.

## Appendix — commands

```bash
uv run python scripts/regenerate_clean.py --solve-profile NWPP
uv run python scripts/regenerate_clean.py --solve-profile PJM
uv run python scripts/data/fetch_pjm_da_virtuals.py --years 2019 2020 2021 2022 2023 2024 2025
MAIN=/home/user/ms-main2 ./run_iso.sh nwpp results/calibration/nwppnext27_span            - 2019 2020 2021 2022 2023 2024 2025
MAIN=/home/user/ms-main2 ./run_iso.sh pjm  results/calibration/closeout_pjm_nuc_full_span - 2019 2020 2021 2022 2023 2024 2025
```

`run_iso.sh`, `capture_inputs.py` and `compare.py` are the MISO record's Appendix A
scripts (session scratch, not committed). The key-payload probe wraps
`market_sim.config.scenarios.json.dumps` to keep the last payload `cache_key()`
hashes.
