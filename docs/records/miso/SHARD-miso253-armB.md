# SHARD miso-253 arm B — MISO 2023, `mustrun_chp_btm_holdout`, `MARKET_SIM_HIGHS_THREADS=1` (scaling ON)

**Outcome: OOM-KILLED. No bundle produced. The thread cap alone is NOT enough.**

- Pinned SHA: `eaa9d6f196fcc5103164a6432dcab2856d95bb4c` (verified before any work)
- Config under test: `MARKET_SIM_HIGHS_THREADS=1`, `MARKET_SIM_MEM_DEBUG=1`,
  **`MARKET_SIM_HIGHS_LEAN` deliberately NOT set** (HiGHS scaling left ON).
- Command:
  `run_calibration_full.py --replay-bundle results/calibration/miso_fuelvintage_A --year 2023
   --mustrun-chp-btm-holdout --out-dir results/calibration/miso253_armB`

## 1. Memory ceiling and the kill

| quantity | value |
|---|---|
| **TRUE nested cgroup ceiling** (v1, `/process_api/01a09332-…/claude-code-bash`) | **14,327,676,928 B = 13.344 GiB** |
| `MemTotal` (misleading — do not use) | 16,461,028 kB = 15.70 GiB |
| `nproc` | 4 |
| **Peak RSS at kill** (`anon-rss`, oom-killer line) | **13,946,972 kB = 13.301 GiB** |
| `total-vm` at kill | 31,778,164 kB = 30.306 GiB |
| cgroup `memory.max_usage_in_bytes` | 14,327,676,928 B — **pinned exactly at the limit** |
| cgroup `memory.failcnt` | 13,011 |
| OOM constraint | `CONSTRAINT_MEMCG`, `oom_memcg=/process_api/…/claude-code-bash` |

dmesg, verbatim:

```
[  428.231475] Memory cgroup out of memory: Killed process 2240 (python)
  total-vm:31778164kB, anon-rss:13946972kB, file-rss:12060kB, shmem-rss:0kB,
  UID:0 pgtables:28112kB oom_score_adj:0
```

**Survival time: 113.4 s** (launch 01:24:07Z → OOM 01:26:00Z, 2026-09-12).

## 2. Where it died — the solve, not the build

`MARKET_SIM_MEM_DEBUG=1` checkpoints (pairs are `VmHWM` peak then `VmRSS` current,
in `/proc/self/status` order):

| checkpoint | VmHWM | VmRSS |
|---|---|---|
| after `build_constraints` | 3,564,396 kB = 3.399 GiB | 3,040,632 kB = 2.900 GiB |
| after casts/bounds | 3,564,396 kB = 3.399 GiB | 3,040,632 kB = 2.900 GiB |
| after `addCols` | 4,777,744 kB = 4.556 GiB | 4,314,984 kB = 4.115 GiB |
| **after `addRows` (LAST checkpoint reached)** | **7,345,096 kB = 7.005 GiB** | 5,325,132 kB = 5.078 GiB |
| *(next checkpoint — never reached)* | — | — |

LP size: **1,026,876 rows × 29,643,840 cols, 86,198,400 nnz (indices int32)**.

The last log write was `MEM after addRows` at 01:25:19Z; the kill was at 01:26:00Z.
So **~41 s elapsed inside HiGHS `run()`** — between handing HiGHS the rows and the kill —
and memory went **7.005 → 13.301 GiB (+6.30 GiB) inside the solver's own setup**
(scaling / presolve-off path / factorization), never reaching the first post-solve checkpoint.

This matches the `_log_rss` docstring's own miso-169 measurement (build tops out ~5.1 GB;
solve+extraction reach ~14.4 GB on the plant-level MISO LP) — the solve owns the peak, and
capping HiGHS to one thread does not touch that ownership.

## 3. G-1 — the holdout footprint (the one gate that DID clear)

Log line, verbatim:

```
INFO: must-run CHP/BTM holdout 2023 MISO: dropping 12.514 TWh of chp=Y host-steam
generation from the injected residual classes (170 of 2994 rows)
```

**12.514 TWh, 170 of 2994 rows — EXACTLY the expected value.** The mechanism's
pre-solve footprint is confirmed at this SHA; only the LP failed to complete.

## 4. Items 3 (bundle numbers) — NOT AVAILABLE

No bundle was written. `results/calibration/miso253_armB/` contains only an empty
`dispatch/` directory; zero parquet, zero `metrics.json`, zero `run_config.json`.
Per the shard brief, **nothing half-written was pushed**. Therefore none of the
following can be reported from this shard: biomass/OTHER totals, the per-class
generation table, C1/C2/C3a/C3b/C3c/C4/C6/C8 verdicts, LW mean LMP, bench
`classFull` TOTAL, or the `run_config.json` flag confirmation.

## 5. Wall clock

| phase | duration |
|---|---|
| data prep + LP build (launch → `MEM after addRows`) | **72 s** |
| HiGHS `run()` before OOM | **~41 s** |
| **total to kill** | **113.4 s** |

For comparison against the parent's other arms: this is **not** a convergence problem —
it never got far enough to converge or fail to converge. It is a hard allocation wall
hit ~41 s into the solver. The 6 h 11 m LEAN run (scaling OFF) is the opposite failure
mode: it survives the allocation and then cannot converge. The thread cap keeps scaling
ON, so convergence was never in question here — the arm simply cannot fit.

## 6. Verdict for the parent

**`MARKET_SIM_HIGHS_THREADS=1` on top of this SHA's ~461 MB memory fix does not avoid the
OOM on plant-level MISO 2023.** The headroom needed is ≈ 6.30 GiB above the post-`addRows`
7.005 GiB peak, against a 13.344 GiB ceiling; the thread cap moves none of it, because the
allocation belongs to the single-threaded scaling/factorization path, not to per-thread
working sets. A shard with a larger memory ceiling, or a structural reduction in the
29.6 M-column LP, is what this arm needs — not another HiGHS env lever.

No infrastructure was modified. No cgroup file was written. No `src/` or `scripts/` edit.
