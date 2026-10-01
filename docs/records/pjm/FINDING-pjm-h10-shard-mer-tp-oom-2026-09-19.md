# FINDING — pjm-h10 shard: PJM 2020-2022 touchpoint MER replay OOM-killed, and three missing-input blockers before it

Shard of session **pjm-h10** (PJM energy-identity lane). Pinned HEAD
`4583e70b864a7d5c99a206b06eddf3c36af495bf`. MER commit
`2ec096633f5624585eb9db1728ebc7c8ca5ccbdf` confirmed an ancestor.

**Outcome: NO BUNDLE. Nothing pushed.** The replay of
`results/calibration/pjm_d4_4_TP` → `pjm_h10_mer_TP` was **OOM-killed by the
binding memcg** during the 2020 **P1** pass. Per the shard prompt this is a
reportable finding, not a model regression.

## 1. The OOM (the headline)

```
oom-kill:constraint=CONSTRAINT_MEMCG,oom_memcg=/process_api/01a0bab8-.../claude-code-bash,task=python,pid=1639
Memory cgroup out of memory: Killed process 1639 (python)
  total-vm:31045096kB  anon-rss:13949260kB  file-rss:7328kB  pgtables:39036kB
```

* `anon-rss` **13,949,260 kB = 13.30 GiB** against a **13.36 GiB** ceiling —
  the identical 13.30 GiB figure CLAUDE.md rule 32(c)(8) records for the
  miso-252/253 incident.
* Died **after** 2020 P0 completed (`Matrix build 21.289s, Solve 574.607s,
  382,243 simplex iterations, objective 6,743,757,838.05`), during the P0→P1
  seam / P1 build. No P1 `Matrix build` line was ever emitted.
* The python process alone held essentially the whole ceiling; concurrent
  shell processes in the same cgroup were <2 MB (bash 1,535 kB, sleep 365 kB
  in the OOM task dump). **Not** caused by shard tooling.

### The swapfile did not and cannot help here

Preflight, verbatim:

```
INFO: container preflight: memory ceiling 13.36 GiB (.../claude-code-bash/memory.limit_in_bytes; MemTotal 15.72 GiB), swap 5.0 GiB, target ceiling+swap 24 GiB
WARNING: container preflight: swap: /swapfile-marketsim is already active (5.0 GiB) but ceiling+swap is still 5.6 GiB short of the 24 GiB target; leaving it as it is
INFO: container preflight: solve profile MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1
WARNING: container preflight: ceiling+swap 18.4 GiB is below the 24 GiB target; a per-plant ISO-year LP (MISO, PJM) may be OOM-killed here
```

At the moment of the kill `/proc/swaps` showed **Used = 0** on the active
5.0 GiB swapfile. The kernel OOM-killed rather than swapping
(`constraint=CONSTRAINT_MEMCG`); `memory.memsw.limit_in_bytes` is unreadable
in this cgroup, `memory.swappiness` = 60. **The runner's swap mitigation was
inert** — worth noting against rule 32(c)(8), which assumes a provisioned
swapfile is what lets a per-plant PJM/MISO year fit. Disk had only 7.0 GiB
free, so a larger swapfile was not available either.

**No retry was spent.** The failure is deterministic (same LP, same build
order, swap provably unusable, preflight predicted it), so an identical
re-run would only reproduce it; the remaining budget was spent recording
this instead. Attributing the OOM specifically to the MER dual is **not
possible from this run** — the dual cannot be toggled at this HEAD without a
code edit, which the shard is forbidden to make. What *is* established: 2020
P0 solved and printed its objective, so the crash is in the P0→P1 seam, and
the container was flagged under-provisioned before the dual was reached. The
attribution is therefore **confounded and open**.

## 2. Three missing-input blockers preceded the solve

The shard prompt asserted "the bundle was solved off the raw tree and the
runner reads it directly." That premise is **false in three places** in a
fresh container. Each hard-raises ("the mechanism never silently no-ops"):

| # | Blocker | Kind | Resolved by |
|---|---|---|---|
| 1 | `transfer-interface-limits` clean partition absent (`pjm_measured_interface_limits=True`) | derived clean tree | `scripts/data/curate_transfer_interface_limits.py --isos PJM` → 7 partitions (2019-2025), 87,600 rows each |
| 2 | `ramp-capability` clean partition absent (`measured_ramp_capability=True`) | derived clean tree | `scripts/data/curate_ramp_capability.py --isos PJM` → 749 rows |
| 3 | `data/raw/pjm-da-virtuals/hrl_da_incs_decs_{2020,2021,2022}_*` absent (`pjm_da_virtual_bids=True`) | **licensed raw corpus, gitignored, not in git at all** | `scripts/data/fetch_pjm_da_virtuals.py --years 2020 2021 2022 --feeds hrl_da_incs_decs` → 36 files, 15 MB, 577 s |

Notes:

* `data/clean` **did not exist at all** in this container; it is derived,
  disposable and gitignored. `hydrate_data.py --profile pjm` is a no-op here
  (full clone) and cannot supply any of the three.
* Blocker 3 is the sharp one: `build_pjm_da_virtual_units`
  (`src/market_sim/data/virtual_bids.py:335`) has **no fallback and no year
  gate**, so the committed touchpoint's container demonstrably held these
  2020-2022 parquets. The fetch restores the control's own input rather than
  adding a new one. The corpus stays gitignored
  (`.gitignore:101 data/raw/pjm-da-virtuals/*`), so PJM DataMiner2's
  non-member redistribution restriction is respected — nothing was committed.
* `scripts/regenerate_clean.py` was **not** run (forbidden by the prompt); only
  the two narrow per-datatype curate scripts the runtime log itself names.
* The curate docstring's "committed 2023-2025 raw drops" is **stale**: the
  PJM raw feed on disk covers 2019-2026.
* The container also shipped **no Python dependencies** (`numpy` absent);
  `uv sync --no-dev` installed the `uv.lock` pins, which match the source
  bundle's recorded environment exactly (highspy 1.14.0, numpy 2.4.6,
  scipy 1.17.1, pandas 3.0.3, pyarrow 24.0.0, pydantic 2.13.4; Python 3.11.15).

## 3. Source bundle signature — verified, matched

`results/calibration/pjm_d4_4_TP`: iso `PJM` · mode `backcast` · hindcast
`False` · plant_level_fleet `True` · use_campd_bins `True` ·
measured_ct_heat_rates `True` · gas_daily_shape `True` · meta years
`[2020, 2021, 2022]`. All seven match. (The seven fields live under
`run_config.json → scenario_config`, not at its top level.)

Its recorded `git_sha` `f09eddbe` is **unresolvable** in this clone —
consistent with the documented 2026-08-16 history rewrite — so no
code-history drift check on the blockers was possible.

## 4. What did get confirmed about the drift the parent predicted

The 2020 build logged:

```
INFO: PJM mid-curve offer surface: priced 657 econ/long-run tranche rows at the
measured capacity-share offer level (4 net-load bins, tightest bin 263/8760 hours,
year table 2020, level scope -, peak scope -); P1-only
```

**`year table 2020`** — i.e. 2020 now draws its own PJM midcurve offer table
rather than the pooled 2023-2025 fallback, exactly the HEAD change the
parent's zero-LP drift audit expected. No scored number survives to quantify it.

## 5. What a next attempt needs

A container whose **binding cgroup** (not `free`, not MemTotal) exceeds
~13.36 GiB, or usable swap charged to that cgroup. PJM at per-plant
granularity across 8 zones needs >13.3 GiB anon in the P0→P1 seam alone.
The three inputs above must be materialized first; on a fresh container that
is ~10 min of curate + fetch before any LP starts.

Recorded by the pjm-h10 shard, 2026-09-19.
