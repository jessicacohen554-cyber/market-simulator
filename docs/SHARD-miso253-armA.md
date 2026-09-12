# SHARD miso-253 arm A — MISO 2023, `mustrun_chp_btm_holdout`, default solver

**Result: OOM-KILLED after 110 seconds. No bundle produced.**
This shard is a complete, negative result: the arm does not fit in the shard
memory ceiling under default solver settings. It is the control arm for the
parent's `MARKET_SIM_HIGHS_LEAN` comparison.

- Pinned SHA: `eaa9d6f196fcc5103164a6432dcab2856d95bb4c` (verified equal at start; no pull/rebase)
- Date: 2026-09-12
- Command:
  `run_calibration_full.py --replay-bundle results/calibration/miso_fuelvintage_A --year 2023
   --mustrun-chp-btm-holdout --out-dir results/calibration/miso253_armA`
- Env: `MARKET_SIM_MEM_DEBUG=1` ONLY. `MARKET_SIM_HIGHS_LEAN` and
  `MARKET_SIM_HIGHS_THREADS` deliberately UNSET (default solver settings).

## 1. True nested memory ceiling (the correct probe)

The root cgroup reads unlimited and `MemTotal` reads 15.70 GiB; neither binds.
The binding limit is on the **nested** cgroup:

| quantity | value |
|---|---|
| cgroup path | `/process_api/01a09330-bdf6-765f-be3e-19cc7ae16f26/claude-code-bash` |
| `memory.limit_in_bytes` (v1, nested) | **14,327,676,928 B = 13,991,872 kB = 13.344 GiB** |
| cgroup v2 (`memory.max`) | absent — this host is cgroup **v1** |
| `MemTotal` (misleading root value) | 16,461,028 kB = 15.70 GiB |
| `nproc` | 4 |

Matches the expected 14,327,676,928 B exactly. No cgroup file was written.

## 2. Peak RSS and the kill

From `dmesg`:

```
[  581.376828] python invoked oom-killer: gfp_mask=0x100cca(GFP_HIGHUSER_MOVABLE), order=0
[  581.507012] oom-kill:constraint=CONSTRAINT_MEMCG, oom_memcg=/process_api/01a09330-bdf6-765f-be3e-19cc7ae16f26/claude-code-bash,
               task=python, pid=2269, uid=0
[  581.513643] Memory cgroup out of memory: Killed process 2269 (python)
               total-vm:31786400kB, anon-rss:13945980kB, file-rss:11996kB,
               shmem-rss:0kB, pgtables:28172kB
```

| quantity | value |
|---|---|
| **peak anon-RSS at kill** | **13,945,980 kB = 13.301 GiB** |
| file-RSS | 11,996 kB |
| total RSS | 13,957,976 kB = 13.311 GiB |
| total-vm | 31,786,400 kB = 30.31 GiB |
| **fraction of the 13.344 GiB ceiling** | **99.67 % (anon) / 99.76 % (total)** |
| kill constraint | `CONSTRAINT_MEMCG` — the nested cgroup, not the host |

The process was killed pressed flat against the limit, not by host exhaustion.

## 3. Survival time

| event | wall clock (UTC) |
|---|---|
| solve launched (`solve.log` birth) | 01:25:07 |
| last log write (post-`addRows`) | 01:26:17 |
| OOM kill (`dmesg` 581.5 s uptime) | 01:26:57 |
| **total survival** | **110 s** |

Breakdown: ~70 s for data load + fleet build + LP build + HiGHS load, then
**~40 s inside the solver** with no further output before the kill. The death is
in the **solve**, not the build — the model was fully loaded into HiGHS first.

## 4. MEM checkpoint ladder (complete)

Each checkpoint prints twice (peak, then current):

| checkpoint | peak kB | current kB | peak GiB |
|---|---|---|---|
| after `build_constraints` | 3,568,188 | 3,044,412 | 3.40 |
| after casts/bounds | 3,568,188 | 3,044,412 | 3.40 |
| after `addCols` | 4,781,336 | 4,318,696 | 4.56 |
| after `addRows` | 7,348,668 | 5,328,844 | **7.01** |
| *(inside HiGHS solve — no checkpoint)* | — | — | **→ 13.30 at kill** |

**LP size: 1,026,876 rows × 29,643,840 cols, 86,198,400 nnz (indices int32).**

The build path peaks at 7.01 GiB — comfortably inside the ceiling. The solver
then adds **~6.3 GiB** on top and overruns. The ~461 MB memory fix carried by
this SHA moved the build ceiling but does not close a gap of this size: the
arm needs materially more than 13.344 GiB under default settings, and because
it died mid-solve the true requirement is unknown, only bounded below.

## 5. G-1 — the holdout line (PASS, exact)

```
INFO: must-run CHP/BTM holdout 2023 MISO: dropping 12.514 TWh of chp=Y
      host-steam generation from the injected residual classes (170 of 2994 rows)
```

| quantity | expected | observed | verdict |
|---|---|---|---|
| TWh dropped | 12.514 | **12.514** | PASS |
| rows | 170 of 2994 | **170 of 2994** | PASS |

The mechanism fires exactly as pre-registered. This is the one substantive
result the shard did produce, and it is clean.

## 6. Bundle — NONE

`results/calibration/miso253_armA/` contains only an empty `dispatch/` directory
(8.0 K, zero files). No parquet, no `metrics.json`, no `run_config.json`.

Therefore **not reportable** from this shard:
class generation table, total generation, net imports, biomass / OTHER totals
(expected 2.3233 / 3.6165 TWh), C1/C2/C3a/C3b/C3c/C4/C6/C8 verdicts, LW mean
LMP, bench `classFull` total, and the `"mustrun_chp_btm_holdout": true`
confirmation in `run_config.json`. Nothing was pushed (rule 27 — no half-written
bundle).

Control for reference (committed keeper, NOT re-solved): determination
CALIBRATED, all PASS except C3c CAVEAT (ledgered); 2023 model CC_REGULAR
138.151 TWh vs bench 141.817; model biomass 8.128, OTHER 10.325; LW mean price
34.467 $/MWh.

## 7. What this settles for the parent

1. **The default-solver arm OOMs**, at 99.7 % of a correctly-probed 13.344 GiB
   nested ceiling, 110 s in, inside HiGHS — not in LP construction.
2. **Build is not the problem.** 7.01 GiB post-`addRows` leaves 6.3 GiB of
   headroom that the solver consumes and exceeds.
3. **The LEAN comparison now has both arms**: default = OOM at 110 s;
   LEAN = survives but had not converged at 6 h 11 m (parent's measurement).
   Neither setting produces a bundle on a 13.344 GiB shard.
4. **G-1 is verified** independently of the solve, so the mechanism's footprint
   is confirmed at 12.514 TWh / 170 of 2994 rows without spending a solve.

No infrastructure was modified: no cgroup write, no edit under `src/` or
`scripts/`, no registration, no PR, no result deleted (rule 31 `[R-RETAIN]`).
