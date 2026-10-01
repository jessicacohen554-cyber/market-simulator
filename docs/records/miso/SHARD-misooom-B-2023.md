# SHARD misooom-B-2023 — MISO 2023 keeper replay with the container preflight OFF (negative control)

Shard report (rule 32 `[R-SHARD]`). Session 2026-09-12. One job: replay the committed MISO keeper
`results/calibration/miso_fuelvintage_A` on 2023 at a pinned SHA with the container preflight
DISABLED, and report numbers. The expected outcome — an OOM kill inside HiGHS at the nested-cgroup
ceiling — is what happened. **Result: OOM-KILLED, no bundle written. Control is valid.**

## 1. Hard stops

| check | result |
|---|---|
| `git rev-parse HEAD` | `0101b4ced8f88058fed062ce591c255f9c958e18` (pinned SHA, no checkout needed) |
| `uv run python3 scripts/run_calibration_full.py --help \| grep -c no-container-preflight` | `2` (≥ 1, PASS) |
| `ls data/raw/MISO-AS \| head -3` | `README.md`, `asm_damcp_zonal_2023.parquet`, `asm_damcp_zonal_2024.parquet` |
| keeper `run_config.json` present | `keeper-present` |
| hydrate | clone was already FULL; `hydrate_data.py --profile miso` reported nothing to fetch |

## 2. Ceiling probe (before launch)

```
P=/process_api/01a0934b-3130-73d6-8277-94619cae9297/claude-code-bash
memory.limit_in_bytes = 14327676928      # 13.34 GiB (v1 memcg)
/proc/swaps: (header only — NO swap)
df -h /: /dev/vda 252G 21G 17G 56% /
```

No swap was created by hand; `prepare_solve_container.py` was NOT run. No solver env vars set
except `MARKET_SIM_MEM_DEBUG=1` as the prompt directs.

## 3. Launch

`replay_keeper.py results/calibration/miso_fuelvintage_A --years 2023 --out-dir
results/calibration/misooom_B_2023`, invoked through a one-line python wrapper that set
`scripts.run_calibration_full.CONTAINER_PREFLIGHT_ENABLED = False` (the same module object
`replay_keeper.py` imports as `rcf`; no file under `scripts/` edited).

- launched: **01:53:17 UTC**, uv pid 2337, python child pid **2343**
- OOM kill: **≈01:54:40 UTC** (dmesg uptime 510.91 s), child gone by the 01:54:51 sample
- **wall time launch→kill ≈ 83–90 s**

## 4. Log evidence (`results/calibration/misooom_B_2023.log`, 219 lines)

- lines containing `container preflight:` : **0** (proves the control ran without the fix)
- lines containing `memory peak:` : **0**
- lines containing `wrote calibration bundle` / `Traceback` / `Killed` / `MemoryError` : **0** —
  the log stops mid-solve with no traceback, the OOM signature.

Every `MEM ` stage line, verbatim (line numbers 211–219; the two values per stage are the two
figures the debug hook prints, RSS then RSS-after-GC):

```
211:INFO: MEM after build_constraints: 3535328 kB
212:INFO: MEM after build_constraints: 3011480 kB
213:INFO: MEM after casts/bounds: 3535328 kB
214:INFO: MEM after casts/bounds: 3011480 kB
215:INFO: MEM after addCols: 4748484 kB
216:INFO: MEM after addCols: 4285756 kB
217:INFO: MEM LP size: 1026876 rows x 29643840 cols, 86198400 nnz (indices int32)
218:INFO: MEM after addRows: 7315804 kB
219:INFO: MEM after addRows: 5295904 kB
```

Last 5 lines of the log:

```
INFO: MEM after addCols: 4748484 kB
INFO: MEM after addCols: 4285756 kB
INFO: MEM LP size: 1026876 rows x 29643840 cols, 86198400 nnz (indices int32)
INFO: MEM after addRows: 7315804 kB
INFO: MEM after addRows: 5295904 kB
```

Non-MEM lines are the usual eGRID heat-rate clamp / CC pmax reconciliation WARNINGs, the
"capacity-deliverability clean partition absent" fallback WARNING, and the maxgen tier-pricing
INFO — no P0/P1 line was ever reached.

## 5. Sampled maxima (30 s cadence, nested cgroup, never `free`)

| counter | bytes | GiB |
|---|---|---|
| `memory.max_usage_in_bytes` | 14,327,676,928 | **13.34** (== limit, byte-exact) |
| `memory.memsw.max_usage_in_bytes` | 14,327,939,072 | 13.34 |
| `memory.failcnt` | **20,725** | — |
| python child `VmHWM` (last sample before kill, 01:54:21) | 7,315,804 kB | 6.98 |
| python child `VmSwap` | 0 kB | 0 |
| dmesg `anon-rss` at kill | 13,928,044 kB | 13.28 |
| dmesg `total-vm` at kill | 31,763,532 kB | 30.3 |

cgroup timeline: t=0 s 0.75 GiB → t=30 s 2.20 GiB → t=60 s 7.20 GiB (after addRows) → t=90 s
ceiling hit, failcnt 20,725, usage back to 57 MB (child dead). The VmHWM sampler's last reading
(6.98 GiB) predates the final ~6 GiB HiGHS allocation burst, which happened inside the 30 s
window before the kill; the dmesg anon-rss (13.28 GiB) is the true peak.

`memory.oom_control`: `oom_kill_disable 0 / under_oom 0 / oom_kill 1`.

dmesg (readable):

```
[  510.762654] python3 invoked oom-killer: gfp_mask=0x100cca(GFP_HIGHUSER_MOVABLE), order=0, oom_score_adj=0
[  510.910332] oom-kill:constraint=CONSTRAINT_MEMCG,nodemask=(null),cpuset=/,mems_allowed=0,oom_memcg=/process_api/01a0934b-3130-73d6-8277-94619cae9297/claude-code-bash,task_memcg=/process_api/01a0934b-3130-73d6-8277-94619cae9297/claude-code-bash,task=python3,pid=2343,uid=0
[  510.917639] Memory cgroup out of memory: Killed process 2343 (python3) total-vm:31763532kB, anon-rss:13928044kB, file-rss:12208kB, shmem-rss:0kB, UID:0 pgtables:28092kB oom_score_adj:0
```

## 6. Exit status

Killed by SIGKILL from the memcg OOM killer (`CONSTRAINT_MEMCG`, oom_kill count 1) — the
equivalent of exit 137 / signal 9. The wrapper was `nohup`'d from a separate shell so no `$?` was
captured; dmesg is the authoritative record. The run reached the HiGHS model-load stage (after
`addRows`) and died before `run()` printed anything.

## 7. Bundle / price diff

No bundle: `results/calibration/misooom_B_2023/` contains only an empty `dispatch/` directory.
The price-diff step was therefore not run (nothing to compare). The log, pid file and the empty
out-dir are left on local disk uncommitted (rule 31 `[R-RETAIN]`).

## 8. Reading

The control reproduces the miso-252/253 incident exactly: with the preflight off (no swap, no
solve-profile pins), a MISO 2023 per-plant year (1.03 M rows × 29.6 M cols, 86.2 M nnz) exceeds
the 13.34 GiB nested-cgroup ceiling inside HiGHS and is OOM-killed ~85 s after launch. The
positive arm (preflight on) is the other shard's job; this shard makes no infrastructure change.
