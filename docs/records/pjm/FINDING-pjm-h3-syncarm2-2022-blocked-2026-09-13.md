# FINDING — pjm-h3 attempt 3 (syncarm2) BLOCKED: OOM in P0, disk-bound swap provisioning

**Lane:** pjm-h3 · **Shard:** attempt 3 (`claude/pjm-h3-syncarm2-2022`) · **Date:** 2026-09-13
**Pinned HEAD:** `ed6bb0996d2685884d1f05eb105c3bef4dea138c`
**Outcome:** SOLVE OOM-KILLED (SIGKILL, exit 137) in **P0**. No bundle. Nothing pushed but this doc.

## 1. Headline — the attempt-2 diagnosis was wrong about the mechanism

Attempt 2 concluded its container held a **stale 4 GiB `/swapfile-marketsim`** which
`ensure_solve_container` "keeps and never re-creates", leaving ceiling+swap at 17.3 GiB.

This container started with **zero swap** (`swapon --show` empty, `free -g` Swap total 0).
The preflight therefore took its *create* path — and still produced **exactly 4 GiB**, landing on
the identical 17.3 GiB and emitting the identical warning.

**The 4 GiB is not a stale artifact. It is disk-bound.** After the `pjm` data profile is hydrated:

```
/dev/vda  252G  31G used  6.4G AVAIL  83% /
```

`ensure_solve_container` targets 24 GiB ceiling+swap ⇒ needs a **~10.7 GiB** swapfile on a
filesystem with **6.4 GiB free**. It cannot get there, writes what fits, warns, and proceeds.
A fresh container does not fix this; any container with this disk allowance plus a hydrated PJM
profile reproduces it.

## 2. The kill

```
SOLVE START 2026-09-13T06:29:35Z
SOLVE END   2026-09-13T06:39:44Z      EXIT=137   (10 min 09 s)
```

Killed immediately after the co-opt build line, **before any P0 solve completion output**.
P0 did not finish; P1 never started.

```
Memory cgroup out of memory: Killed process 2146 (python3)
  total-vm:30206260kB  anon-rss:13927736kB  file-rss:7608kB  pgtables:36912kB
oom-kill:constraint=CONSTRAINT_MEMCG,
  oom_memcg=/process_api/01a0996a-.../claude-code-bash, task=python3, pid=2146
```

| quantity | value |
|---|---|
| anon-RSS at kill | 13,927,736 kB = **13.28 GiB** (attempt 2: 13.28 GiB — same) |
| total-vm at kill | 30,206,260 kB = 28.8 GiB |
| `memory.limit_in_bytes` | 14,326,067,200 = 13.34 GiB |
| `memory.max_usage_in_bytes` | 14,326,067,200 — **pinned at the ceiling** |
| `memory.failcnt` | **1,144,459** |
| `memory.memsw.max_usage_in_bytes` | 18,605,129,728 = **17.33 GiB** |
| `memory.memsw.limit_in_bytes` | unlimited (`memsw.failcnt` 0) |

**The load-bearing number is `memsw.max_usage` = 17.33 GiB = ceiling 13.34 + swap 4.00, exactly.**
The solve consumed **100 % of RAM *and* 100 % of swap** and was still killed. Swap was not idle
and the 4 GiB was not wasted — the job simply needs **more than 17.3 GiB**. This is not a marginal
miss that a slightly larger swapfile would clear; the 24 GiB target is the real requirement.

## 3. Environment, verbatim

```
INFO: container preflight: memory ceiling 13.34 GiB (/sys/fs/cgroup/memory/process_api/
      01a0996a-7a2b-7689-97e5-b3b38975f423/claude-code-bash/memory.limit_in_bytes;
      MemTotal 15.70 GiB), swap 0.0 GiB, target ceiling+swap 24 GiB
INFO: container preflight: provisioned 4 GiB swap at /swapfile-marketsim
      — ceiling 13.34 + swap 4.0 = 17.3 GiB
INFO: container preflight: solve profile MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1
      OMP_NUM_THREADS=1
WARNING: container preflight: ceiling+swap 17.3 GiB is below the 24 GiB target;
         a per-plant ISO-year LP (MISO, PJM) may be OOM-killed here
```

Pre-solve state: `swapon --show` → empty · `free -g` → Mem total 15, available 14; Swap 0
cgroup **v1**, `memory.memsw.limit_in_bytes` unlimited, `vm.swappiness` 60.

## 4. The arm DID arm — this is not a mechanism failure

```
INFO: PJM PER-GEN reserve co-opt ON: 78 R columns / 2682 member units (eligible, ramp10>0;
deliverable ramp mean 38.2 GW), 4 balance families (pjm_primary, pjm_primary_mad, pjm_sync,
pjm_sync_mad), req means [2663, 2662, 1902, 1901] MW — SYNC product split ON
(pjm_reserve_pergen_sync: online-scoped sync caps recomputed at the P0->P1 seam)
```

Byte-for-byte the attempt-2 signature (4 families, 78 R columns, req means
`[2663, 2662, 1902, 1901]` MW), plus the explicit `SYNC product split ON` clause.
`pjm_reserve_pergen_sync=true` reached the LP. **The mechanism is not what is blocked.**

## 5. Hard stops — all four PASS

| # | check | measured |
|---|---|---|
| 1 | `git rev-parse HEAD` | `ed6bb0996d2685884d1f05eb105c3bef4dea138c` ✓ |
| 2 | control `meta.json` flat `git_sha` | `f09eddbe` ✓ |
| 3 | control signature (6 flags) | `energy_reserve_coopt` T, `pjm_reserve_pergen` T, `pjm_reserve_supply_cap` T, `pjm_reserve_pergen_sync` F, `pjm_reserve_online_gated` F, `pjm_reserve_commitment_scoped` F ✓ |
| 4 | `grep -c pjm_reserve_pergen_sync scenarios.py` | 5 (≥2) ✓ |

## 6. Environment blockers — all three cleared, ~4 min (they parallelize)

`transfer-interface-limits` (7 clean files) · `ramp-capability` · PJM 2022 `hrl_da_incs_decs`
(12 monthly parquets, 6.1 MB — `--years 2022` required; the default is 2023-2025).
The two `regenerate_clean.py` calls and the fetch touch different trees and ran **concurrently**
without incident: ~4 min wall, versus ~10 min serial. All three are gitignored; nothing committed.

**Note for the next attempt:** the virtuals land **flat** at
`data/raw/pjm-da-virtuals/hrl_da_incs_decs_2022_MM.parquet`, not under a
`hrl_da_incs_decs/` subdirectory.

## 7. Bundle state — nothing to push

```
results/calibration/pjmh3_syncarm_2022/
└── dispatch/          (empty)          total 8.0K
```

No `meta.json`, no `run_config.json`, no `hourly/`. Per the shard contract a half-written bundle is
never pushed, so **commit 1 and commit 2 were both correctly skipped**. Rule 31 `[R-RETAIN]`:
nothing was deleted — there is nothing to retain.

## 8. What this shard did NOT do (deliberately)

No source patched, no swapfile resized, no `--no-container-preflight`, no solve-setting change,
no retry with shrunk parameters, no re-solve of the control. Per the shard contract an OOM is a
**reportable result**, not a thing to engineer around.

## 9. For the parent — the decision this surfaces

The blocker is **environmental and reproducible**, not stochastic, and it is now measured twice at
the same anon-RSS. A fourth attempt under the same shape will fail the same way. The choices are
disk or ceiling, and they are the parent's/owner's to make:

1. **Free disk before the solve** so the preflight can reach its 24 GiB target — it needs ~10.7 GiB
   of swapfile against 6.4 GiB free. Whether ~4.3 GiB is reclaimable on a PJM-hydrated container
   (other bundles under `results/calibration/`, `data/clean/`) is a rule-31 question, since those
   may be results nobody has ruled on. **Not a shard's call.**
2. **A container with a larger memory ceiling or larger disk allowance**, if the environment offers
   one. 13.34 GiB of RAM is below what a per-plant PJM year needs even with swap.
3. **Subdivide** — rule 32(b) permits per-zone/per-pass subdivision for DIAGNOSTIC work that will
   never be registered. This screen is a throwaway probe whose numbers live in the PRECOMMIT, so it
   may qualify; a registrable run would not.

Option 3 is the only one a shard could execute unaided, and it is a scope change, so it is
reported rather than taken.
