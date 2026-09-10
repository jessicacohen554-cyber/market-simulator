# SHARD miso-253 — 2023 `mustrun_chp_btm_holdout` arm — **OOM, NO SOLVE**

**Shard result: STOPPED with a clear report.** The LP was OOM-killed by the kernel during
HiGHS solve setup. No bundle was produced. The single most valuable finding is not the arm's
numbers (there are none) but **why HARD STOP 0 failed to catch this** — the prescribed
ceiling check reads the wrong cgroup in this container family, which is almost certainly why
session miso-252 lost three containers the same way.

Pinned SHA (HARD STOP 1, PASSED): `6b82b833ff09b80df440d6da27223280bc6a88bf`
Config signature (HARD STOP 2, PASSED): `config signature OK`

---

## 1. Ceiling + peak RSS — and the HARD STOP 0 defect

**THE PRESCRIBED CHECK IS WRONG IN THIS CONTAINER. DO NOT REUSE IT.**

The shard prompt directs:

```
cat /sys/fs/cgroup/memory/memory.limit_in_bytes   # -> 9223372036854771712
head -3 /proc/meminfo                             # -> MemTotal: 16461028 kB
```

and says that a v1 limit of `9223372036854771712` means "there is NO cgroup limit; the ceiling
is MemTotal". Following that rule verbatim yields **15.70 GiB**, which is above the 14 GiB stop
line, so the shard proceeded. **That reading is false.** `/sys/fs/cgroup/memory/memory.limit_in_bytes`
is the *root* memory cgroup. The Bash tool's processes do not run there. From `/proc/self/cgroup`:

```
4:memory:/process_api/01a08cc6-7150-72a3-92e9-9a7e3dd5c03c/claude-code-bash
```

The limit that actually binds is on that **nested** cgroup:

| path | limit |
|---|---|
| `/sys/fs/cgroup/memory/memory.limit_in_bytes` (root, what the prompt reads) | unlimited |
| `/sys/fs/cgroup/memory/process_api/<id>/memory.limit_in_bytes` | unlimited |
| **`/sys/fs/cgroup/memory/process_api/<id>/claude-code-bash/memory.limit_in_bytes`** | **14,327,545,856 B = 13.344 GiB** |

**EFFECTIVE CEILING = 13.344 GiB**, not 15.70 GiB. `memory.max_usage_in_bytes` on that cgroup
reads **13.344 GiB** — i.e. it ran the limit exactly to the wall.

**13.344 GiB < 14 GiB, so HARD STOP 0's own rule says STOP. Correctly evaluated, this shard
should never have attempted the solve.**

### The kill

```
oom-kill:constraint=CONSTRAINT_MEMCG,
  oom_memcg=/process_api/01a08cc6-.../claude-code-bash,
  task=python, pid=2204
Memory cgroup out of memory: Killed process 2204 (python)
  total-vm:31766440kB  anon-rss:13943944kB  file-rss:12356kB  pgtables:28100kB
```

- **Peak anon-RSS at kill: 13,943,944 kB = 13.30 GiB**
- Total VM at kill: 31,766,440 kB = 30.30 GiB
- **Did it OOM: YES.** Wall time to kill: ~90 s after launch.

**This reproduces miso-252's 13.29 GiB peak to within 0.01 GiB.** MISO's single-year LP is not
marginally over this ceiling by chance — it lands on the same number every time, and the
ceiling is 13.344 GiB. The margin is ~40 MiB. That is why three containers died.

### Stage it died in

Last MEM trace lines before the kill (`MARKET_SIM_MEM_DEBUG=1`), HWM / current:

| stage | HWM | current |
|---|---|---|
| after `build_constraints` | 3,560,756 kB (3.40 GiB) | 3,036,992 kB (2.90 GiB) |
| after casts/bounds | 3,560,756 kB (3.40 GiB) | 3,036,992 kB (2.90 GiB) |
| after `addCols` | 4,774,040 kB (4.55 GiB) | 4,311,164 kB (4.11 GiB) |
| **after `addRows`** | **7,341,276 kB (7.00 GiB)** | 5,321,312 kB (5.08 GiB) |
| — killed inside HiGHS setup/solve, no further trace — | | |

**LP size: 1,026,876 rows × 29,643,840 cols, 86,198,400 nnz (int32 indices).**

So ~7.0 GiB is ours at handoff to HiGHS, and HiGHS then adds ~6.3 GiB before the wall. Env in
force: `MARKET_SIM_HIGHS_THREADS=1`, `MARKET_SIM_HIGHS_LEAN=1`, `MARKET_SIM_MEM_DEBUG=1`.

---

## 2. G-1 footprint confinement — **PASSED, EXACTLY ON THE PRE-REGISTERED VALUE**

This is the one gate that got measured, and it landed on the pre-registration to the digit.

```
INFO: must-run CHP/BTM holdout 2023 MISO: dropping 12.514 TWh of chp=Y host-steam
      generation from the injected residual classes (170 of 2994 rows)
```

| quantity | expected | observed | verdict |
|---|---|---|---|
| dropped energy | 12.514 TWh | **12.514 TWh** | EXACT |
| rows dropped | 170 of 2994 | **170 of 2994** | EXACT |

### Class totals — arithmetic confirmation of confinement (zero-LP, from committed bench)

The arm's injected/benchmark totals could not be read from a bundle (none was written), but
the confinement is checkable without one. The committed control bench
`frontend/data/backcast/bench/MISO/2023.json.gz` → `bench.classFull` gives the pre-arm values,
and the pre-registered arm expectations differ from them by exactly the holdout drop:

| class | control `classFull` (TWh) | expected arm (TWh) | implied drop (TWh) |
|---|---|---|---|
| `biomass` | 8.1281 | 2.3233 | 5.8048 |
| `OTHER` | 10.3253 | 3.6165 | 6.7088 |
| **sum** | | | **12.5136** |

**12.5136 TWh vs the logged 12.514 TWh — agreement to 0.0004 TWh.** The drop is fully
accounted for by `biomass` + `OTHER` and touches no other class. **G-1 confinement holds.**

Full control bench `classFull` for 2023 (used for G-6 below):

```
CC_CHP 21.3113 | CC_REGULAR 141.817 | COAL_BIT 57.0694 | COAL_LIGNITE 7.0468
COAL_PRB 121.671 | CT_CHP 8.3415 | CT_PEAKER 17.0383 | OTHER 10.3253
OTHER_FOSSIL 8.6863 | ST_CHP 5.2027 | ST_GAS 13.9398 | biomass 8.1281
hydro 9.979 | nuclear 87.1773 | oil 0.4624 | solar 6.348 | wind 91.715
```

---

## 3. G-3 lockstep identity — **NOT MEASURED**

Requires the arm's `gmModel.biomass` / `gmModel.OTHER` against the arm's regenerated bench
`classFull`. Both sides live downstream of a completed solve. **No bundle → not measurable.**
Note the arm moves BOTH sides, so this gate cannot be inferred from the control.

## 4. G-2 response (per-class model generation) — **NOT MEASURED**
No solve, no dispatch output. `results/calibration/miso253_screen2023b/` contains only an
empty `dispatch/` directory.

## 5. Criteria verdicts (C1/C2/C3a/C3b/C3c/C4/C6/C8) — **NOT MEASURED**
No `metrics.json` was written.

**Control for reference** (`results/calibration/miso_fuelvintage_A/metrics.json`, rubric
determination `CALIBRATED`, years 2023–2025):

| criterion | tier | status |
|---|---|---|
| C1 `fuelmix` fuel-mix by class (grid-delivered) | load-bearing | PASS |
| C2 `sysvol` system volume (gas/coal families) | load-bearing | PASS |
| C3a `price_mean` mean LMP | load-bearing | PASS |
| C3b `price_shape` price duration/shape | load-bearing | PASS |
| C3c `price_tail` price tail / scarcity (RT hourly) | supporting | **CAVEAT (ledgered)** |
| C4 `dispatch_corr` fleet hourly dispatch correlation | supporting | PASS |
| C6 `governance` governance gate | protective | PASS |
| C8 `forced_share` forced-energy share (D-2) | protective | PASS |

## 6. Prices — **NOT MEASURED**
No solve.

## 7. G-6 bench `classFull` TOTAL (reported, not a kill)
Summing the control 2023 `classFull` above: **616.259 TWh** across all 17 classes.
The arm's own regenerated bench was not produced.

## 8. G-5 `run_config.json` contains `"mustrun_chp_btm_holdout": true` — **NOT MEASURED**
The process died before `run_config.json` was written. The flag *was* passed
(`--mustrun-chp-btm-holdout`) and it demonstrably took effect — the holdout INFO line in §2 is
emitted only on the arm path — but the on-disk artifact does not exist.

---

## 9. What the parent should do next

1. **Fix the HARD STOP 0 recipe before launching another MISO shard.** The check must read the
   process's own cgroup, not the root one:
   ```
   awk -F: '/^[0-9]+:memory:/{print $3}' /proc/self/cgroup
   cat /sys/fs/cgroup/memory$(awk -F: '/^[0-9]+:memory:/{print $3}' /proc/self/cgroup)/memory.limit_in_bytes
   ```
   In this container family that returns **13.344 GiB**, and every MISO single-year shard
   launched against a 15.70 GiB reading will die at ~90 s.
2. **A MISO single-year LP does not fit in a 13.344 GiB bash cgroup at this HEAD.** Peak is
   13.30 GiB against a 13.344 GiB wall — a ~40 MiB margin, i.e. no margin. Retrying in an
   identical container is not a coin flip that sometimes lands; it is the same kill.
3. The memory levers this shard was forbidden to re-test (allocator/BLAS vars, `presolve`,
   `_vstack_csr_free`, `miso_seam_export_limit`) are all already spent by miso-252 and would
   not close a 6.3 GiB HiGHS-side gap anyway. **Closing this needs either a container with a
   larger `claude-code-bash` cgroup, or an LP-side reduction** — and the latter is `src/` work,
   which is outside a shard's remit. Escalate rather than shard again.
4. Rule 31 `[R-RETAIN]`: nothing was deleted. The empty
   `results/calibration/miso253_screen2023b/` remains on local disk; it holds no results.

## 10. Rules observed
No edits under `src/` or `scripts/`. No `git add -A`/`git add .`. No pull/rebase/sync. No
dashboard, manifest, status, prune, or `frontend/data/backcast/**` writes. No PR. No results
deleted. **No half-written bundle was pushed** — the bundle dir is empty and is therefore not
committed; per the shard charter this doc is the durable record.
