# FINDING — pjm-h11 ARM C-1 2021 shard: OOM-killed in the P0 post-solve window

**Session:** pjm-h11 solve shard, ARM arm (card C-1), year 2021, cold single-year.
**SHA:** `3b7194840aa74020824f02dd09e198684469ab0b` (ARM sha, verified).
**Outcome:** NO BUNDLE. The solve was OOM-killed after P0 completed. Not retried (prompt instruction).
**Date:** 2026-09-19.

## 1. What was verified before the solve

| check | expected | observed |
| --- | --- | --- |
| `git rev-parse HEAD` | `3b719484…ab0b` | matches |
| `grep -c '^    2020: {' src/market_sim/model/interchange/spec.py` | 2 (ARM) | **2** |
| `sorted(PJM_SEAM_LADDER_BY_YEAR)` | `[2019…2025]` | matches |
| `L[2020]['MISO']['export']` | `(66.93, 57.12, 36.2, 25.46, 20.05, 15.95, 11.93, 8.68)` | matches |

The 2021 build log confirms 2021 took its **own** measured ladder entry, not the gas-elastic
forecast fallback the 2020 gap fell through to:

> `INFO: PJM 2021: seam bands repriced to the MEASURED per-seam Q-Q ladders (tie-line flow
> durations x PJM DA system quantiles; MISO/NYISO/Carolinas/TVA/LGEE, import + export; no added
> hurdle; firm-export floor displaced)`

This is consistent with the parent's zero-LP finding (0 of 240 shared rungs moved), but it is
**not** the invariance check itself — that needed the completed P1 metrics, which do not exist.

## 2. The kill

```
oom-kill:constraint=CONSTRAINT_MEMCG,nodemask=(null),cpuset=/,mems_allowed=0,
  oom_memcg=/process_api/01a0bbc8-9b8f-70a3-86ce-dd5b11344539/claude-code-bash,
  task_memcg=/process_api/01a0bbc8-9b8f-70a3-86ce-dd5b11344539/claude-code-bash,
  task=python3,pid=814,uid=0
Memory cgroup out of memory: Killed process 814 (python3) total-vm:31013448kB,
  anon-rss:13931256kB, file-rss:7564kB, shmem-rss:0kB, UID:0 pgtables:38948kB oom_score_adj:0
```

- **Binding cgroup ceiling:** 14,345,912,320 B = 13.36 GiB, read from
  `/sys/fs/cgroup/memory/process_api/01a0bbc8-9b8f-70a3-86ce-dd5b11344539/claude-code-bash/memory.limit_in_bytes`.
- **anon-rss at kill:** 13,931,256 kB = **13.29 GiB**, *plus* `total_swap 5,341,450,240` B
  = 4.97 GiB already swapped out. Committed anonymous footprint ≈ **18.3 GiB** against the
  18.4 GiB ceiling+swap. `memory.failcnt` 1,732,998; `memory.oom_control` `oom_kill 1`.
- The 5 GiB swap was **fully consumed**, not spare headroom.

## 3. The phase, pinned

The kill is bounded to the window that opens at `model/lp/model.py:1181` — the
`Matrix build/Solve` log call, which fires *immediately after* P0's `h.run()` returns — and
closes before the first P1 log line, of which there is none.

- P0 `Solve` line written **22:47:41.6 UTC**
- OOM **22:50:44.0 UTC** (dmesg 1366.335 s; boot 22:27:57.657)
- **182.4 s of zero log output** in between.

That window contains, in order: P0 solution extraction (`model.py:1194–1521`),
**`_marginal_emission_rate` (`model.py:1522`)**, `DispatchResult` construction, the P0→P1 seam,
and the P1 matrix build. `_marginal_emission_rate` is ungated and unconditional at this HEAD and
executes a **second HiGHS `run()`** inside exactly this window — its own docstring names it as
"the same post-solve window that owns the measured year peak (miso-253)". The evidence does not
isolate it from the other three candidates: there is no log line between them, so the 182.4 s and
the 18.3 GiB cannot be attributed to one of the four by this run's data alone.

## 4. Contributing cause worth acting on: the swap was short by disk, not by code

Preflight ran unmodified and did its job, but could only get 5 GiB of the 24 GiB target, and said so:

```
INFO: container preflight: memory ceiling 13.36 GiB (…memory.limit_in_bytes; MemTotal 15.72 GiB), swap 0.0 GiB, target ceiling+swap 24 GiB
INFO: container preflight: provisioned 5 GiB swap at /swapfile-marketsim — ceiling 13.36 + swap 5.0 = 18.4 GiB
INFO: container preflight: solve profile MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1
WARNING: container preflight: ceiling+swap 18.4 GiB is below the 24 GiB target; a per-plant ISO-year LP (MISO, PJM) may be OOM-killed here
```

The binding constraint was **free disk**: `/` shows 7.0 GiB available *after* the 5 GiB swapfile,
i.e. ~12 GiB free at preflight, against a 24 GiB target that needs ~10.6 GiB of swapfile. A PJM
per-plant shard needs a container with **≥ 12 GiB free disk** for preflight to reach its target,
and this one did not have it. The warning at line 7 predicted this kill exactly.

## 5. State left behind

- `results/calibration/pjm_h11_arm_2021/` — **0 files**. Nothing half-written, nothing pushed.
- `git status` clean; `data/clean/` and `data/raw/pjm-da-virtuals/` are gitignored and were not committed.
- No `memory peak:` line exists: the process was killed before the runner could log one.

## 6. What the parent still needs

Card C-1's 2021 invariance check is **unanswered**. Re-running it needs a container with more
disk (see §4), not a code change — and per rule 31 `[R-RETAIN]` nothing here was deleted. Cost of
a re-solve from cold: ~7 min P0 LP (measured: 419.4 s) plus setup, plus the unmeasured P1.

---
_Generated by [Claude Code](https://claude.ai/code)_
