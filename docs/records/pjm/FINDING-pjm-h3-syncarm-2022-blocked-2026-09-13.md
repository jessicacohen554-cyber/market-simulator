# FINDING — pjm-h3 SYNC-arm screen (PJM 2022) STOPPED: OOM in P0

**Shard:** pjm-h3 · **Date:** 2026-09-13 · **Status:** STOPPED WITH BLOCKER — no bundle produced,
nothing pushed beyond this doc.

## Verdict

The arm **ARMED CORRECTLY** and then the P0 LP was **OOM-killed by the kernel** at the nested
cgroup ceiling. This is reported as a result, not engineered around: no settings were changed, no
source was patched, no retry with a shrunken problem was attempted.

## Hard stops — all four PASS

| # | Check | Measured |
|---|---|---|
| 1 | `git rev-parse HEAD` | `ed6bb0996d2685884d1f05eb105c3bef4dea138c` (exact) |
| 2 | `pjm_d4_4_TP/meta.json` flat `git_sha` | `f09eddbe` |
| 3 | Control config signature | `energy_reserve_coopt=True`, `pjm_reserve_pergen=True`, `pjm_reserve_supply_cap=True`, `pjm_reserve_pergen_sync=False`, `pjm_reserve_online_gated=False`, `pjm_reserve_commitment_scoped=False` — all six hold |
| 4 | `grep -c pjm_reserve_pergen_sync src/market_sim/config/scenarios.py` | `5` (>= 2) |

## The arm DID install

```
INFO: PJM PER-GEN reserve co-opt ON: 78 R columns / 2682 member units (eligible, ramp10>0;
deliverable ramp mean 38.2 GW), 4 balance families (pjm_primary, pjm_primary_mad, pjm_sync,
pjm_sync_mad), req means [2663, 2662, 1902, 1901] MW — SYNC product split ON
(pjm_reserve_pergen_sync: online-scoped sync caps recomputed at the P0->P1 seam)
```

Four balance families (control has two), `pjm_sync` / `pjm_sync_mad` present. The split installed
as designed. **78 R columns** is the armed count.

## Where it died: P0

Last log line is the per-gen reserve co-opt build above (line 218 of 218). There is **no P0
completion marker, no P1 marker, and no `memory peak:` line at all** — the runner emits that line
at the end of a run, so it never printed. Exit code **137** (SIGKILL).

Kernel evidence:

```
oom-kill:constraint=CONSTRAINT_MEMCG,nodemask=(null),cpuset=/,mems_allowed=0,
  oom_memcg=/process_api/01a09936-7e1f-75ca-82ba-d72139864753/claude-code-bash,
  task_memcg=/process_api/.../claude-code-bash,task=python3,pid=7158,uid=0
Memory cgroup out of memory: Killed process 7158 (python3) total-vm:30185884kB,
  anon-rss:13927636kB, file-rss:8060kB, shmem-rss:0kB, UID:0 pgtables:36888kB oom_score_adj:0
```

- anon-RSS at kill: **13,927,636 kB = 13.28 GiB**
- cgroup `memory.max_usage_in_bytes`: **14,326,067,200 B = 13.34 GiB** — pinned exactly at the ceiling
- cgroup `memory.failcnt`: **1,562,256**

## Container preflight (verbatim)

```
INFO: container preflight: memory ceiling 13.34 GiB (/sys/fs/cgroup/memory/process_api/01a09936-7e1f-75ca-82ba-d72139864753/claude-code-bash/memory.limit_in_bytes; MemTotal 15.70 GiB), swap 4.0 GiB, target ceiling+swap 24 GiB
WARNING: container preflight: swap: /swapfile-marketsim is already active (4.0 GiB) but ceiling+swap is still 6.7 GiB short of the 24 GiB target; leaving it as it is
INFO: container preflight: solve profile MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1
WARNING: container preflight: ceiling+swap 17.3 GiB is below the 24 GiB target; a per-plant ISO-year LP (MISO, PJM) may be OOM-killed here
```

`memory peak:` line: **NONE — the process was killed before the runner could emit it.**

## THE SWAP DID NOT HELP — this is the load-bearing finding

After the kill, `swapon --show` reports the 4 GiB swapfile at **3.4 MB used**. The process died at
the **ceiling alone (13.34 GiB)**, not at ceiling+swap (17.3 GiB).

This container's cgroup is **v1**, where `memory.limit_in_bytes` bounds RSS and only a
correspondingly raised `memory.memsw.limit_in_bytes` lets swap extend the effective ceiling. The
preflight's `ceiling + swap = 17.3 GiB` arithmetic therefore did **not** describe the binding
constraint here. Only ~2 GiB of swap could be provisioned against the 24 GiB target anyway
(the preflight said it was 6.7 GiB short and left it).

Implication for rule 32(c)(8): on a v1 memcg, provisioning a swapfile does not by itself raise
what the LP may use. A PJM per-plant year at doubled R-column count needs a container whose
**ceiling** is above ~13.34 GiB; adding swap under a v1 limit does not substitute.

## Why this arm is heavier than the control

The control's own 2022 solve peaked at 13.94 GB (per the lane prompt) — already above this
container's 13.34 GiB ceiling. The SYNC split doubles the balance families 2 -> 4 and installs 78
R columns. There is no headroom here at all; the control itself would very likely not fit either.

## Environment blockers cleared on the way (for the next shard's benefit)

This container is a **full clone with no `data/clean/` tree and no gitignored raw corpora**. Three
hard-fail blockers were hit and cleared before the LP was reached; each mechanism refuses to
silently no-op, so each is fatal:

1. `transfer-interface-limits` — no clean partition. Cleared with
   `scripts/regenerate_clean.py transfer-interface-limits`.
2. `ramp-capability` — no clean partition for PJM. Cleared by regenerating the **whole** clean tree
   (`scripts/regenerate_clean.py`, no args): **56/56 datatypes ok**, 1.6 GB written, ~13 min.
3. `pjm_da_virtual_bids` — `data/raw/pjm-da-virtuals/` held only its README (gitignored corpus,
   PJM DataMiner2 redistribution restriction). Cleared with
   `scripts/data/fetch_pjm_da_virtuals.py --years 2022 --feeds hrl_da_incs_decs` — 12 monthly
   parquets, 1,947,682 rows, 6.1 MB, ~3.5 min. **Note the default is `--years 2023 2024 2025`; 2022
   must be requested explicitly.** These files stay gitignored and were not committed.

No edit was made under `src/` or `scripts/`. `data/clean/` is gitignored and disposable;
the fetched corpus is gitignored by license.

**A shard prompt for this lane should budget for all three, or the container should be
pre-hydrated.** The previous shard that "died during hydrating PJM data, launching solve" was
almost certainly killed by blocker 1 or 2, not by a foreground-timeout and not by an OOM.

## Wall clock

| Phase | Wall |
|---|---|
| Attempt 1 (died: `transfer-interface-limits`) | ~8 min |
| Clean-tree regeneration (56 datatypes) | ~13 min |
| Attempt 2 (died: `ramp-capability`) | ~1 min |
| Attempt 3 (died: `pjm_da_virtual_bids`) | 24 s |
| PJM 2022 DA virtuals fetch | ~3.5 min |
| **Attempt 4 (armed, OOM in P0)** | **411 s (6 min 51 s)** |
| P0 solve | never completed |
| P1 solve | never reached |

## Artifacts

`results/calibration/pjmh3_syncarm_2022/` contains **only an empty `dispatch/` directory (8 KB)**.
There is no `meta.json`, no `run_config.json`, no `legitimacy_diagnostics.json`, no `hourly/`.

**Nothing was pushed** — rule 27 `[R-PUSH]` / the lane prompt both forbid pushing a half-written
bundle, and rule 34 `[R-SHARD-PROMOTABLE]`'s push duty has no object here. The control bundle
`results/calibration/pjm_d4_4_TP` was **not touched** and was **not re-solved**.

## What the parent still does not have

Items 7 and 8 of the shard report (per-family `reserve_family_2022.parquet` duals; `system_2022.parquet`
prices) are **unavailable** — those artifacts were never written.

## Recommended next step (the parent adjudicates; this shard does not)

Re-launch on a container whose **cgroup ceiling** clears ~16 GiB or more. Re-pin the same SHA
`ed6bb0996d2685884d1f05eb105c3bef4dea138c` and the same control signature, and pre-clear the three
environment blockers above so the ~7 min of loader work is not re-spent before the LP.
