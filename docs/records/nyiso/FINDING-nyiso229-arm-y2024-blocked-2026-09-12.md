# FINDING — nyiso-229 span ARM leg, year 2024: shard STOPPED, no LP solved

**Date:** 2026-09-12
**Shard:** nyiso-229 span ARM leg, YEAR 2024 only (`unit_outage_window_hour_grain=true`)
**Pinned SHA:** `b385f3f3759b95380dc189d529b57d6933484c5f`
**Outcome:** **STOPPED at a hard blocker before any LP ran.** No bundle, no commit, no push,
no PR, nothing deleted. Per the shard charter (rule 32 `[R-SHARD]` (c) 7) — *"a shard that
stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a FAILURE."*

This doc is the record (rule 29 `[R-SCREEN]` (c): the FINDING carries every number the
session will ever cite). It cites no solve numbers because there are none.

---

## 1. Hard stops 0–3 — ALL PASS

| Stop | Check | Result |
|---|---|---|
| 0 | pinned SHA | `git rev-parse HEAD` = `b385f3f3759b95380dc189d529b57d6933484c5f` — PASS. Never rebased, never pulled, never synced. |
| 1 | memory ceiling + swap ≥ 20 GiB | **22.3 GiB** — PASS |
| 2 | `unit_outage_window_hour_grain` in `run_year` signature | **True** — PASS |
| 3 | outage input sha256 | `ee778a87d3739341a7c578078b5e0194545f9231efbef2cd32d72e88e0aa21fa` — PASS (not re-derived) |

Hard stop 4 (config signature) was **never reachable** — no `run_config.json` was written.

### Container preflight, verbatim

```
container preflight: memory ceiling 13.34 GiB (/sys/fs/cgroup/memory/process_api/01a09692-5a31-77ba-acbb-7382fd2df984/claude-code-bash/memory.limit_in_bytes; MemTotal 15.70 GiB), swap 0.0 GiB, target ceiling+swap 24 GiB
container preflight: provisioned 9 GiB swap at /swapfile-marketsim — ceiling 13.34 + swap 9.0 = 22.3 GiB
container preflight: solve profile MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1
container preflight: ceiling+swap 22.3 GiB is below the 24 GiB target; a per-plant ISO-year LP (MISO, PJM) may be OOM-killed here
```

`swapon --show` → `/swapfile-marketsim  file  9G  0B  -2`.

Swap stopped at 9 GiB rather than the 24 GiB target because the root filesystem has
**6.9 GiB free of 252 GiB (82 % used)**. This did **not** cause the failure — the run died
26 s in, long before HiGHS was reached. Recorded because it is a real constraint on this
container class for the sibling legs.

### Resolved package versions

`{'highspy': '1.15.1', 'numpy': '2.4.6', 'scipy': '1.17.1', 'pandas': '3.0.5', 'pyarrow': '25.0.1'}`

---

## 2. The blocker — `data/clean/` does not exist in this container

The launched command was, unmodified and with no `--no-container-preflight`:

```
python3 scripts/replay_keeper.py results/calibration/nyiso_fuelvintage_A \
  --years 2024 --set unit_outage_window_hour_grain=true \
  --out-dir results/calibration/nyiso229_arm_y2024
```

It failed after **26 s**:

```
File "/home/user/market-simulator/scripts/run_calibration.py", line 2829, in run_year
    ttc = apply_nyiso_li_tsl_import_cap(
File "/home/user/market-simulator/src/market_sim/model/interchange/nyiso.py", line 279, in apply_nyiso_li_tsl_import_cap
    raise ValueError(
ValueError: nyiso_li_lcr_tsl=True but no published Long Island transfer_security_limit for
delivery year 2024/2025 in the capacity-deliverability table
(data/raw/capacity-deliverability/nyiso/nyiso.csv); available areas: []
```

### The error message points at the wrong file

The **raw** row is present and correct —
`data/raw/capacity-deliverability/nyiso/nyiso.csv` (3,794 B, 36 lines) contains:

```
NYISO,2024/2025,annual,Long Island,locality,transfer_security_limit,940,,2024-25-Locality-Bulk-Power-Transmission-Capability-Report.pdf,7
```

(all four TSL rows — 2022/23, 2023/24, 2024/25, 2025/26 — are present at 940 MW).

The loader does **not** read that file. `capacity_deliverability._read`
(`src/market_sim/data/capacity_deliverability.py:82-113`) reads the **curated** partition via
`scripts.lib.clean_io.read_clean`, and:

> **`data/clean/` does not exist in this container — the directory is absent entirely (0 entries).**

`available areas: []` is the empty-frame degrade path, not a data gap. The raise itself is
correct behaviour (the mechanism is designed never to silently no-op); the message's file
citation is what misleads.

### This is not one missing partition

`data/clean` is gitignored and derived by design (`.gitignore:226`; the tree is rebuilt by
`scripts/regenerate_clean.py`, its sole entrypoint — `scripts/hydrate_data.py` does **not**
build it). `src/market_sim/` has **57 `read_clean` call sites**. The `nyiso_fuelvintage_A`
keeper arms several mechanisms that each read their own clean partition and, by design,
**hard-raise rather than silently no-op**:

| keeper flag | value | clean datatype |
|---|---|---|
| `nyiso_li_locational_reserve` | True | `capacity-deliverability` ← **the raise above** |
| `nyiso_seam_deliverability_envelope` | True | `nyiso-interface-flows` |
| `nyiso_seam_par_attribution` | True | (par-attribution partition) |
| `nyiso_dynamic_reserve_requirements` | True | `reserve-requirements` |
| `nyiso_import_hub_prices` | True | `lmp` (neighbour price) |
| `nyiso_firm_imports` / `nyiso_import_reconciliation` | True | — |
| `nyiso_scr_edrp`, `priced_interchange`, `egrid_*_heat_rates` | True | various |

`nyiso_seam_envelope.py:235-252` is explicit about the pattern — it re-raises as
`FileNotFoundError` with *"run scripts/regenerate_clean.py nyiso-interface-flows (the
mechanism never silently no-ops)"*. **Clearing the first raise only advances to the next.**

---

## 3. Why the shard stopped rather than repairing

1. The charter forbids pre-emptive datatype regeneration **by name** (*"that cost an earlier
   shard over an hour"*). This is a multi-datatype rebuild, not "regenerate ONLY the
   partition the error names".
2. The single narrowest repair the loader itself prescribes —
   `curate_capacity_deliverability.py --isos NYISO` — was attempted and **denied by the
   permission classifier** (`[Modify Shared Resources]`, writes into `data/clean/`). Both the
   direct and `-m` invocations were blocked. No further workaround was attempted.
3. Rebuilding the clean tree is infrastructure repair, which the charter classifies as a
   shard FAILURE.

---

## 4. Second finding — replay environment drift (independent of the blocker)

This leg's control is the **committed keeper bundle** (rule 29 `[R-SCREEN]` (b) form 4), so
the solver environment matters. `replay_keeper.py` emitted:

```
WARNING: replay environment differs from the bundle's recorded environment — byte-identity is not guaranteed:
  highspy: bundle '1.14.0' != now '1.15.1'
  pandas: bundle '3.0.3' != now '3.0.5'
  pyarrow: bundle '24.0.0' != now '25.0.1'
  pydantic: bundle '2.13.4' != now '2.13.5'
```

| package | keeper `meta.environment` | this container |
|---|---|---|
| highspy | **1.14.0** | **1.15.1** |
| numpy | 2.4.6 | 2.4.6 (match) |
| scipy | 1.17.1 | 1.17.1 (match) |
| pandas | 3.0.3 | 3.0.5 |
| pyarrow | 24.0.0 | 25.0.1 |
| pydantic | 2.13.4 | 2.13.5 |

Keeper base environment: Python 3.11.15, `Linux-6.18.44-fc-v24-x86_64-with-glibc2.39`.

**Why this matters:** a HiGHS minor bump can move duals on a degenerate LP, and prices in this
model *are* the duals (rule 4 `[R-DUALS]`). An arm-vs-committed-keeper delta solved on 1.15.1
would carry a **solver-version confound alongside the mechanism** — the differencing would no
longer isolate `unit_outage_window_hour_grain`. Nothing was changed (the charter said report
versions, change nothing). **All three span shards (2023/2024/2025) inherit this drift**, so
it is a design question for the span, not a per-shard one.

Two options for the parent, neither taken here:
- **(a)** pin `highspy==1.14.0` (and the three others) in the shard container so form-4
  differencing stays clean; or
- **(b)** re-solve the keeper control on the new environment — which costs the LP budget that
  rule 29 (b) exists to avoid, and would need its own G-DRIFT audit.

---

## 5. Numbers requested by the charter

Items 1–6 (firm-load slack, dump, served demand, price bands, reserve shortfall by family,
TWh per klass) are **NOT AVAILABLE** — no `hourly/system_2024.parquet`,
`reserve_family_2024.parquet` or `class_hourly_2024.parquet` was written.

| # | requested | value |
|---|---|---|
| 1 | firm-load slack MWh / hours | not available (no solve) |
| 2 | dump MWh | not available |
| 3 | served demand TWh | not available |
| 4 | price mean / max / hours >150/200/300 | not available |
| 5 | reserve shortfall by family | not available |
| 6 | annual TWh per klass | not available |
| 7 | `container preflight:` / `memory peak:` / versions | preflight + versions in §1; **`memory peak:` never logged** — the process died pre-solve |
| 8 | wall-clock | **26 s** to failure; ~4 min total shard session |

---

## 6. State left behind

- `results/calibration/nyiso229_arm_y2024/` contains only an empty `dispatch/` directory. No
  bundle was written. **Left in place** — rule 31 `[R-RETAIN]`, nothing deleted.
- That path is **already gitignored** by the existing pattern `.gitignore:866`
  `results/calibration/*_y20[0-9][0-9]/`, so the rule 29 (c) delete-before-merge duty is
  discharged by `.gitignore` as rule 31 requires — no `.gitignore` append was needed and
  nothing can reach `main`.
- `git status --short` is **clean**. No branch created (`claude/nyiso229-arm-2024` does not
  exist), no commit, no push, no PR.
- **No edits under `src/` or `scripts/`.** No dashboard, manifest, status or prune script was
  run; nothing under `frontend/data/backcast/**` was touched.

---

## 7. What unblocks this leg

**In the parent / environment image, once — not three times:**

1. Grant write access to `data/clean/` and run `python3 scripts/regenerate_clean.py`
   (or minimally `capacity-deliverability nyiso-interface-flows`, then whatever the next
   raise names — but the full rebuild is the cheaper single action given §2's list).
2. Decide the §4 environment question before relaunching, so the span's deltas are
   attributable to the mechanism rather than to HiGHS 1.14 → 1.15.
3. Relaunch all three shards at the same pinned SHA.

Until (1) is done, **all three span shards fail identically at ~26 s** and the arm cannot be
extended to the keeper's scored years — so no promotion decision on
`unit_outage_window_hour_grain` is possible yet (rule 16 `[R-ALLYEARS]`).

The 2022 screen result is unaffected and still stands (firm-load slack 360.472 → 0.000 MWh;
both VOLL hours cleared; served demand identical).
