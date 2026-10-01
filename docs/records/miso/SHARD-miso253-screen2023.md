# SHARD miso-253 — MISO 2023 `mustrun_chp_btm_holdout` SCREEN arm

**Result: OOM-KILLED during the P0 LP solve. No bundle produced. G-1 confirmed exactly;
G-2 through G-7 are unobtainable from this shard.**

Shard contract: one MISO year (2023), arm only, keeper recipe + exactly one boolean
(`mustrun_chp_btm_holdout`). Control is the committed keeper bundle
(`results/calibration/miso_fuelvintage_A`), rule 29(b) form 4 — no control solve was spent.

- Pinned SHA (HARD STOP 1, PASS): `6b82b833ff09b80df440d6da27223280bc6a88bf`
- Config signature (HARD STOP 2, PASS): default OFF; `cache_key()` invariant under
  `mustrun_chp_btm_holdout=False`, moves under `=True`.
- Launched 2026-09-10 19:27:01 UTC. Killed ~19:27:47 UTC (~46 s wall).

---

## 1. THE CEILING — and why HARD STOP 0 did not catch this

**HARD STOP 0 as written reads the WRONG cgroup and reports a ceiling that does not exist.**
It probes `/sys/fs/cgroup/memory.max` (v2, absent here) and
`/sys/fs/cgroup/memory/memory.limit_in_bytes` — the **root** v1 memory cgroup — and then falls
back to `MemTotal`. But the solve does not run in the root cgroup. `/proc/self/cgroup` shows:

```
4:memory:/process_api/01a08cc1-6e89-762b-9b0d-02b1e5901ece/claude-code-bash
```

The binding limit is on that **nested** cgroup, and it is far below `MemTotal`:

| quantity | value | GiB |
|---|---:|---:|
| `MemTotal` (what HARD STOP 0 reported) | 16,461,028 kB | **15.70** |
| root `memory.limit_in_bytes` (what HARD STOP 0 read) | 9223372036854771712 | *unlimited* |
| **nested `claude-code-bash` `memory.limit_in_bytes`** | **14,327,676,928 B** | **13.345** |
| nested `memory.max_usage_in_bytes` after the kill | 14,327,676,928 B | 13.345 (**hit the wall exactly**) |

**The true effective ceiling is 13.345 GiB, which is UNDER the 14 GiB stop threshold.** Read
correctly, HARD STOP 0 would have fired and this shard would have stopped before the solve.
The prompt's stated hypothesis — "~16.46 GB MemTotal = 15.70 GiB, no cgroup limit, giving
~2.4 GiB headroom over the 13.29 GiB peak" — is **false**. Actual headroom over miso-252's
13.29 GiB peak is **≈0.055 GiB**.

The correct probe for a future shard (report only — no code was changed):

```
P=$(grep -E '^[0-9]+:memory:' /proc/self/cgroup | cut -d: -f3)
cat /sys/fs/cgroup/memory$P/memory.limit_in_bytes    # v1, nested
cat /sys/fs/cgroup$P/memory.max                      # v2, nested
```

## 2. PEAK RSS AND THE STAGE IT DIED IN

`MARKET_SIM_MEM_DEBUG=1` prints `VmHWM` then `VmRSS` (that is `/proc/status` order). Build-phase
trace, in kB:

| checkpoint | VmHWM | VmRSS |
|---|---:|---:|
| after `build_constraints` | 3,533,816 | 3,010,092 |
| after casts/bounds | 3,533,816 | 3,010,092 |
| after `addCols` | 4,747,536 | 4,284,856 |
| after `addRows` (last checkpoint reached) | **7,314,884 (6.98 GiB)** | 5,295,016 (5.05 GiB) |

LP size: **1,026,876 rows × 29,643,840 cols, 86,198,400 nnz (indices int32)**.

**Stage of death: inside HiGHS `run()` on the P0 base-cost pass** — after `addRows`, before any
post-solve checkpoint. This is the known owner of the MISO year-solve peak; the emitter's own
docstring in `src/market_sim/model/lp/model.py:44` records it (miso-169: build tops out ~5.1 GB
while solve+extraction reach ~14.4 GB on the plant-level MISO LP). The build is not the problem
and never was.

Kernel OOM record (`dmesg`), the terminal peak:

```
oom-kill: constraint=CONSTRAINT_MEMCG,
  oom_memcg=/process_api/01a08cc1-.../claude-code-bash, task=python, pid=2214
Memory cgroup out of memory: Killed process 2214 (python)
  total-vm:31769608kB, anon-rss:13945644kB, file-rss:12076kB, pgtables:28092kB
```

- **terminal anon-RSS 13,945,644 kB = 13.30 GiB**
- cgroup `total_inactive_anon` 14,290,378,752 B = 13.31 GiB
- total-vm 31,769,608 kB = 30.30 GiB

This reproduces miso-252's 13.29 GiB peak to within 0.01 GiB. The arm's one boolean does not
change the memory profile — the LP has the same shape, so the same wall is hit at the same place.

## 3. G-1 FOOTPRINT CONFINEMENT — **CONFIRMED EXACTLY**

The one gate this shard did reach, and it matched the pre-registered prediction to the digit:

```
INFO: must-run CHP/BTM holdout 2023 MISO: dropping 12.514 TWh of chp=Y host-steam
      generation from the injected residual classes (170 of 2994 rows)
```

| | expected | observed | verdict |
|---|---:|---:|---|
| dropped energy | 12.514 TWh | **12.514 TWh** | MATCH |
| rows touched | 170 of 2994 | **170 of 2994** | MATCH |

## 4. WHAT IS NOT MEASURED

No bundle was written (`results/calibration/miso253_screen2023/` holds only an empty
`dispatch/` subdirectory; nothing was committed — rule 27 `[R-PUSH]`, never push a half-written
bundle). Therefore **unmeasured**:

- **G-1 second limb** — injected/benchmark class totals for `biomass` (exp. 2.3233 TWh) and
  `OTHER` (exp. 3.6165 TWh).
- **G-3 lockstep identity** — `gmModel.biomass` vs bench `classFull.biomass`, same for `OTHER`.
- **G-2 response** — per-class model generation TWh, total generation, net imports.
- **Criteria verdicts** C1/C2/C3a/C3b/C3c/C4/C6/C8 for 2023, and their values.
- **Prices** — model load-weighted mean LMP 2023 and its benchmark.
- **G-5** — `run_config.json` never existed, so `"mustrun_chp_btm_holdout": true` could not be
  read back from it. The arming is nonetheless evidenced by the §3 log line, which only the
  armed path emits.

Control for reference (committed keeper `miso_fuelvintage_A`, unchanged, not re-solved):
determination **CALIBRATED**; C1 C2 C3a C3b C4 PASS, C6 C8 PASS, C3c CAVEAT (ledgered).

## 5. STOP

Per the shard contract, an OOM is reported and the shard stops; per the forbidden list, the
spent memory levers from miso-252 (allocator/BLAS vars, `presolve`, `_vstack_csr_free`,
`miso_seam_export_limit=false`) were not re-tested, and nothing under `src/` or `scripts/` was
edited. Nothing was deleted (rule 31 `[R-RETAIN]`).

**The blocker for the parent is a hard resource fact, not a modelling one: a MISO plant-level
single-year LP needs ~13.3 GiB at the solve, and a Bash-tool cgroup here caps at 13.345 GiB.**
A retry in this container class fails at the same line. The parent needs either a container
whose *nested* cgroup ceiling clears ~14.5 GiB, or a solve-phase memory reduction that has not
already been spent.
