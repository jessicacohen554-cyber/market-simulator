# SHARD REPORT — nyiso-228 arm **C (CONTROL)**

**Session:** nyiso-228 · **Shard:** C (CONTROL) · **ISO:** NYISO · **Date:** 2026-09-12
**Branch:** `claude/nyiso228-control-span` · **Bundle:** `results/calibration/nyiso228_control_span`
**Charter:** `docs/PRECOMMIT-nyiso228-amplitude-2026-09-12.md` §3 arm C, §6 shard table.

---

## 1. HARD STOPS — all three checked, observed values

| # | stop | required | observed | verdict |
|---|---|---|---|---|
| 1 | `git rev-parse HEAD` | `55cd0a6c8c3e9d63c0184c6f66f0e9f65a490dbe` | `55cd0a6c8c3e9d63c0184c6f66f0e9f65a490dbe` | **PASS** |
| 2 | PRECOMMIT + peak_x150.json exist | both present | `docs/PRECOMMIT-nyiso228-amplitude-2026-09-12.md` (21,997 B) · `results/calibration/nyiso228_peak_x150.json` (339 B) | **PASS** |
| 3 | config signature | see below | pre-checked against the base bundle; re-checked against the written `run_config.json` post-solve | **see §4** |

No rebase, no `git pull`, no sync was performed. Working tree was clean at session start.

### 1.1 Stop 3, pre-check against the replay base

`results/calibration/nyiso223_gapfill_span/run_config.json` (`scenario_config`):

| field | required for arm C | base value | reached by |
|---|---|---|---|
| `nyiso_hub_gap_month_level` | **false** | `True` | `--set nyiso_hub_gap_month_level=false` (the one field that moves — returns the gapfill base to the keeper recipe, PRECOMMIT §3) |
| `nyiso_import_reconciliation` | **true** | `True` | unchanged |
| `offer_curve_by_group["CT_PEAKER"]["peak"]` | **4.0** | `4.0` | unchanged (arm C moves NO offer band — that is arm A's variable) |
| `offer_curve_by_group["ST_GAS"]["peak"]` | **4.2** | `4.2` | unchanged |

## 2. PREP LOG

| step | result |
|---|---|
| `hydrate_data.py --profile nyiso` | no-op — this container is a FULL clone, every blob already local |
| `prepare_solve_container.py` | 8 GiB swap added at `/swapfile-marketsim`; RAM 15.7 + swap 8.0 = 23.7 GiB; 16.9 GiB free disk, 4 cpus |
| env pins | `MALLOC_ARENA_MAX=2` `MARKET_SIM_HIGHS_THREADS=1` `OMP_NUM_THREADS=1` exported into every solve shell |
| pip pins | PyYAML · highspy 1.14.0 · numpy 2.4.6 · scipy 1.17.1 · pandas 3.0.3 · pyarrow 24.0.0 · pydantic 2.13.4 · openpyxl · tzdata — all exit 0 |
| `regenerate_clean.py` (28 partitions) | launched; `data/clean/` is gitignored and started EMPTY |

`curate_lmp.py` was **not** run (charter: known pre-existing `KeyError: 'MGHG'` on a CAISO file, repair out of scope).

## 3. SOLVE — status

**IN FLIGHT at the time of this heartbeat commit.** This commit exists as proof of life before the
first LP (rule 32(b)); the numbered results below are filled in by the post-solve commit on this same
branch.

Command (years sequential inside one invocation, rule 12 — never parallelised):

```
PYTHONPATH=. python3 scripts/replay_keeper.py results/calibration/nyiso223_gapfill_span \
  --set nyiso_hub_gap_month_level=false \
  --out-dir results/calibration/nyiso228_control_span \
  --years 2022 2023 2024 2025 \
  --note "nyiso-228 arm C CONTROL: keeper recipe at HEAD over 2022-2025; earned by the G-DRIFT LIVE hunk reliability_floor_coeffs_NYISO.csv (nyiso-227 NYC ST_GAS re-basing)"
```

## 4. RESULTS

_Pending the solve._

