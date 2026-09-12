# SHARD miso-253 arm C — FEASIBILITY CONTROL: **OOM at the LP solve, arm-independent**

- **Shard:** miso-253 arm C (feasibility control — keeper recipe, arm OFF)
- **Date:** 2026-09-12
- **Pinned SHA:** `eaa9d6f196fcc5103164a6432dcab2856d95bb4c` (verified equal at `git rev-parse HEAD`; no pull, no rebase, no sync)
- **Result:** **FAILED — OOM-killed 89 s after launch. No bundle produced.**
- **Headline:** a MISO 2023 LP **cannot complete at this SHA inside the 13.344 GiB nested-cgroup
  ceiling**, with the arm OFF. The OOM is therefore **independent of the arm** — it is a property of
  the keeper recipe's LP size against this container's memory limit, not of
  `mustrun_chp_btm_holdout`.

---

## 1. True memory ceiling (STEP 0) — and it is NOT higher

The root cgroup reads unlimited and `MemTotal` reads 15.70 GiB; both are misleading. The limit that
binds is on the **nested** cgroup:

| probe | value |
|---|---|
| cgroup v1 path | `/process_api/01a09333-767b-7591-ae7a-50f30d528397/claude-code-bash` |
| `memory.limit_in_bytes` (v1 nested) | **14,327,676,928 B = 13.344 GiB** |
| `memory.max` (v2 nested) | absent (v1 hierarchy only) |
| `MemTotal` (root, misleading) | 16,461,028 kB = 15.70 GiB |
| `nproc` | 4 |

**The expected value is confirmed exactly. Environments do NOT differ** — there is no larger
container to be had by re-launching. No cgroup file was written at any point.

---

## 2. The OOM, in numbers

Kernel oom-killer record (`dmesg`):

```
[  479.802657] python invoked oom-killer: gfp_mask=0x100cca(GFP_HIGHUSER_MOVABLE), order=0
[  479.938636] oom-kill:constraint=CONSTRAINT_MEMCG,
               oom_memcg=/process_api/01a09333-.../claude-code-bash,
               task_memcg=/process_api/01a09333-.../claude-code-bash, task=python, pid=2299
[  479.945954] Memory cgroup out of memory: Killed process 2299 (python)
               total-vm:31774548kB, anon-rss:13943628kB, file-rss:12060kB, pgtables:28104kB
```

| quantity | value |
|---|---|
| **peak RSS at kill (anon)** | **13,943,628 kB = 13.297 GiB** |
| total-vm at kill | 31,774,548 kB = 30.30 GiB |
| `memory.max_usage_in_bytes` | **14,327,676,928 B — the limit, hit exactly** |
| `memory.failcnt` | 21,669 |
| `oom_kill` counter | 1 |
| OOM constraint | `CONSTRAINT_MEMCG` (the nested cgroup, not the host) |

**Wall-clock:**

| event | UTC | offset |
|---|---|---|
| solve launched | 2026-09-12T01:26:45Z | +0 s |
| last Python log write (`MEM after addRows`) | 2026-09-12T01:27:41Z | **+56 s** |
| OOM kill | 2026-09-12T01:28:14Z | **+89 s** |

**Survived 89 seconds.** It never reached the 60-minute allowance, and it never reached a solver
iteration. No traceback and no `MemoryError` — the silent death is the SIGKILL signature.

---

## 3. Where the memory went

LP dimensions actually built:

```
MEM LP size: 1,026,876 rows x 29,643,840 cols, 86,198,400 nnz (indices int32)
```

Python-side checkpoints (`MARKET_SIM_MEM_DEBUG=1`), the complete series before the kill:

| checkpoint | RSS (kB) | RSS (GiB) |
|---|---:|---:|
| after `build_constraints` | 3,546,460 | 3.38 |
| after `build_constraints` | 3,022,732 | 2.88 |
| after casts/bounds | 3,546,460 | 3.38 |
| after casts/bounds | 3,022,732 | 2.88 |
| after `addCols` | 4,760,196 | 4.54 |
| after `addCols` | 4,297,524 | 4.10 |
| **`MEM LP size`** | — | — |
| after `addRows` | 7,327,516 | 6.99 |
| after `addRows` | 5,307,684 | 5.06 |
| *(no further Python checkpoint)* | | |
| **kill** | **13,943,628** | **13.30** |

**The blow-up is downstream of the last Python checkpoint.** Model construction completed at
5.06 GiB; the process then consumed a further **~8.2 GiB in ~33 seconds with no Python-side
allocation logged**, i.e. inside HiGHS's own handling of the 1.03 M x 29.6 M / 86.2 M-nnz model.
Python-side memory work (`_vstack_csr_free`, presolve off) is not the binding constraint — it had
already done its job and handed off at 5.06 GiB.

---

## 4. Arm confirmed OFF (three independent checks)

1. **No flag passed.** The invocation carries no `--mustrun-chp-btm-holdout`.
2. **Not in the replayed recipe.** `results/calibration/miso_fuelvintage_A/run_config.json` does not
   contain the string `mustrun_chp_btm_holdout` anywhere — the arm is absent from the keeper config
   by construction, so the replay is arm-OFF.
3. **No log line.** `grep -icE "must-run CHP/BTM holdout|mustrun_chp_btm_holdout|chp_btm_holdout"
   /tmp/solve.log` = **0**.

No `run_config.json` was written for this run (see §5), so the arm state rests on the three checks
above.

Environment as instructed: `MARKET_SIM_MEM_DEBUG=1`; `MARKET_SIM_HIGHS_LEAN` and
`MARKET_SIM_HIGHS_THREADS` **unset** (verified via `env`); default solver settings.

---

## 5. No bundle — so no model numbers

```
find results/calibration/miso253_armC_control -type f | wc -l   ->  0
```

The out-dir contains only an empty `dispatch/` subdirectory. **Nothing from Step 4 item 3 can be
reported**: no per-class model generation, no model totals, no net imports, no criteria verdicts, no
model LW mean LMP. The solve died before writing anything.

Nothing was pushed but this document — an empty directory is not a git object, and rule 27
`[R-PUSH]` forbids pushing a half-written bundle. No result was deleted (rule 31 `[R-RETAIN]`);
there was no result to delete.

## 5b. What *could* be established at zero LP cost (committed bench, read-only)

From the committed, shared benchmark `frontend/data/backcast/bench/MISO/2023.json.gz` — read, never
written — the **benchmark** halves of the Step 4 asks are confirmed at this SHA:

| bench `classFull` class | TWh | | class | TWh |
|---|---:|---|---|---:|
| CC_REGULAR | 141.817 | | OTHER_FOSSIL | 8.686 |
| COAL_PRB | 121.671 | | CT_CHP | 8.341 |
| wind | 91.715 | | **biomass** | **8.128** |
| nuclear | 87.177 | | COAL_LIGNITE | 7.047 |
| COAL_BIT | 57.069 | | solar | 6.348 |
| CC_CHP | 21.311 | | ST_CHP | 5.203 |
| CT_PEAKER | 17.038 | | oil | 0.462 |
| ST_GAS | 13.940 | | | |
| **OTHER** | **10.325** | | | |
| hydro | 9.979 | | **TOTAL (17 classes)** | **616.259** |

- **`biomass` 8.128 / `OTHER` 10.325 — the un-partitioned values, matching the expected reference
  exactly.** The bench is un-partitioned at this SHA.
- **bench `classFull` TOTAL across all classes = 616.259 TWh.**
- bench CC_REGULAR = **141.817 TWh**, matching the reference for the committed keeper.
- bench load-weighted mean LMP 2023: **DA 34.23 $/MWh**, **RT 32.85 $/MWh** (simple means: DA 32.98,
  RT 31.79).

**No drift detected in anything measurable without a solve.** Every committed-side number this shard
could check matches the reference the parent supplied, which is consistent with the parent's G-DRIFT
conclusion that HEAD has not drifted from the keeper. The model-side halves remain unverified.

---

## 6. What this means for miso-253

- **The OOM is not the arm's fault.** The arm-OFF keeper recipe dies the same way, at the same
  place, on the same SHA, in the same container class. Any arm shard that OOMs is reproducing this,
  not revealing something about `mustrun_chp_btm_holdout`.
- **A MISO year is not solvable in a 13.344 GiB shard at this SHA** with the keeper recipe and
  default solver settings. The deficit is large, not marginal: the process needed >13.30 GiB and was
  still climbing when killed, having only just handed the model to HiGHS.
- **Re-launching more shards of the same shape will not help** — the ceiling is identical across
  containers (§1), so this is not a scheduling or bad-luck outcome.
- The memory is spent **inside HiGHS**, after Python construction completes at 5.06 GiB. Levers
  already spent and explicitly out of scope for this shard (allocator/BLAS vars, `presolve` already
  off, `_vstack_csr_free` already landed, `miso_seam_export_limit=false` worth 18 MiB) all act on the
  Python side or are too small by two orders of magnitude; none of them addresses an ~8.2 GiB
  solver-side allocation.
- **This shard stops here and reports.** It did not modify `src/`, `scripts/`, any cgroup file, or
  any shared/generated file; it did not register anything, open a PR, or delete any result.

---

## 7. Exact invocation

```
export MARKET_SIM_MEM_DEBUG=1
nohup python scripts/run_calibration_full.py \
  --replay-bundle results/calibration/miso_fuelvintage_A \
  --year 2023 \
  --out-dir results/calibration/miso253_armC_control \
  --note "miso-253 arm C: keeper recipe, arm OFF, feasibility control" \
  > /tmp/solve.log 2>&1 &
```

Setup: `uv venv --python 3.11 .venv` + `uv pip install -r requirements.txt` (numpy 2.4.6,
scipy 1.17.1, pandas 3.0.3, pyarrow 24.0.0, pydantic 2.13.4, highspy present and importable);
`hydrate_data.py --profile miso` reported a FULL clone, so every blob was already local and
hydration was a no-op.
