# SHARD misooom-A-2023 — MISO 2023 keeper replay with the container preflight

Shard under CLAUDE.md rule 32 `[R-SHARD]`. One job: replay the committed MISO keeper
(`results/calibration/miso_fuelvintage_A`) on 2023 at a pinned SHA with the runner exactly as
shipped (no `--no-container-preflight`, no hand-provisioned swap, no solver env vars set by the
shard), and report the memory numbers. Session date 2026-09-12. The bundle and log stay on
local disk only (rule 31 `[R-RETAIN]`); this doc is the sole committed artifact.

## 1. Pin and hard stops

| check | result |
|---|---|
| `git rev-parse HEAD` | `0101b4ced8f88058fed062ce591c255f9c958e18` (matched without a checkout) |
| `grep -c ensure_solve_container scripts/run_calibration_full.py` | 2 |
| `test -f scripts/lib/solve_container.py` | present |

## 2. Ceiling probe BEFORE the run (the correct way: the bash cgroup, not `free`)

```
P=/process_api/01a0934a-a99d-71f0-b1ba-96b64d2a6b2e/claude-code-bash
memory.limit_in_bytes = 14327676928        # 13.34 GiB (MemTotal reads 15.70 GiB)
/proc/swaps: (no swap devices)
df -h /: /dev/vda 252G 21G 17G 56% /
```

Hydration: the clone was a FULL clone (every blob local), so `hydrate_data.py --profile miso`
was a no-op by its own report; `data/raw/MISO-AS` and the keeper `run_config.json` were present.

## 3. Runner log, verbatim

```
2:INFO: container preflight: memory ceiling 13.34 GiB (/sys/fs/cgroup/memory/process_api/01a0934a-a99d-71f0-b1ba-96b64d2a6b2e/claude-code-bash/memory.limit_in_bytes; MemTotal 15.70 GiB), swap 0.0 GiB, target ceiling+swap 24 GiB
3:INFO: container preflight: provisioned 10 GiB swap at /swapfile-marketsim — ceiling 13.34 + swap 10.0 = 23.3 GiB
4:INFO: container preflight: solve profile MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1
5:WARNING: container preflight: ceiling+swap 23.3 GiB is below the 24 GiB target; a per-plant ISO-year LP (MISO, PJM) may be OOM-killed here
215:INFO: MEM after build_constraints: 3478924 kB
216:INFO: MEM after build_constraints: 2954988 kB
217:INFO: MEM after casts/bounds: 3478924 kB
218:INFO: MEM after casts/bounds: 2954988 kB
219:INFO: MEM after addCols: 4692608 kB
220:INFO: MEM after addCols: 4229732 kB
221:INFO: MEM LP size: 1026876 rows x 29643840 cols, 86198400 nnz (indices int32)
222:INFO: MEM after addRows: 7260036 kB
223:INFO: MEM after addRows: 5239880 kB
225:INFO: MEM post-run pre-extraction: 13962528 kB
226:INFO: MEM post-run pre-extraction: 7932564 kB
227:INFO: MEM post col_dual extraction: 13962528 kB
228:INFO: MEM post col_dual extraction: 8511120 kB
229:INFO: MEM post extraction: 13962528 kB
230:INFO: MEM post extraction: 8295952 kB
232:INFO: MEM post-run pre-extraction: 13962528 kB
233:INFO: MEM post-run pre-extraction: 7730488 kB
234:INFO: MEM post col_dual extraction: 13962528 kB
235:INFO: MEM post col_dual extraction: 8308796 kB
236:INFO: MEM post extraction: 13962528 kB
237:INFO: MEM post extraction: 8078736 kB
240:INFO: year 2023 phase timing: data_prep=54.6s solve_p0=525.8s markup=21.2s solve_p1=269.0s results_write=67.0s total=937.6s (markup: setup=0.0s p0_post=9.6s markup=0.8s seam=0.7s p1_post=9.9s tail=0.0s other=0.3s) (results_write: state=1.4s frames=5.3s parquet=6.4s bench=12.2s sidecars=41.7s)
253:INFO: wrote calibration bundle to results/calibration/misooom_A_2023
254:INFO: memory peak: cgroup_peak_rss_gib=13.34, cgroup_peak_rss_plus_swap_gib=18.91, process_vmhwm_gib=13.32, process_vmswap_now_gib=0.07
```

Non-memory WARNING lines (eGRID heat-rate clamps and MISO CC pmax reconciliations omitted; they are the keeper's standing fleet warnings):
```
5:WARNING: container preflight: ceiling+swap 23.3 GiB is below the 24 GiB target; a per-plant ISO-year LP (MISO, PJM) may be OOM-killed here
39:WARNING: capacity-deliverability: clean partition for MISO absent; run scripts/data/curate_capacity_deliverability.py. Returning no limits.
40:WARNING: MISO 2023: capacity-deliverability clean partition absent — falling back to static PY2025-26 summer CIL/CEL caps; run scripts/data/curate_capacity_deliverability.py
250:WARNING: capacity-deliverability: clean partition for MISO absent; run scripts/data/curate_capacity_deliverability.py. Returning no limits.
251:WARNING: no hydro-plant-modes clean partition for MISO — run scripts/data/curate_hydro_plant_modes.py (and review the completion rule for this ISO first)
252:WARNING: no hydro-plant-modes clean partition for MISO — run scripts/data/curate_hydro_plant_modes.py (and review the completion rule for this ISO first)
376:WARNING: legitimacy diagnostics gate FAIL on the replayed bundle (artifact still written; C7/C8 score from its contents — see the report above)
```

No `Killed`, `Error` or `Traceback` line anywhere in the log (`grep -c` = 0 for each). `dmesg` shows only the swapfile add at 407.9 s uptime, no OOM record.

## 4. Shard-side sampled maxima (every 60 s, cgroup files + `/proc/<pid>/status`)

| quantity | bytes | GiB |
|---|---|---|
| `memory.max_usage_in_bytes` | 14,327,676,928 | 13.34 (pinned at the ceiling from t=120 s on) |
| `memory.memsw.max_usage_in_bytes` | 20,304,891,904 | 18.91 |
| swapfile peak `Used` seen | 5,324,628 kB | 5.08 |

**Caveat on the process rows:** the sampler's `pgrep -f replay_keeper.py | head -1` resolved to the
`uv run` wrapper (PID 2329), not the python child (PID 2333), so its `VmHWM` (37.3 MB) and
`VmSwap` (7.4 MB) rows measure the wrapper and are NOT the solver's. The authoritative
process-level figures are the runner's own `memory peak:` line: `process_vmhwm_gib=13.32`,
`cgroup_peak_rss_gib=13.34`, `cgroup_peak_rss_plus_swap_gib=18.91` — which agree with the
cgroup files sampled here.

Full sample series (`t`, `max_usage`, `memsw_max`, swap used):

```
t=0s max_usage=811274240 memsw_max=811274240 swaps=/swapfile-marketsim:10485756:0  | WARNING: container preflig
t=60s max_usage=7682797568 memsw_max=7682797568 swaps=/swapfile-marketsim:10485756:0  | INFO: MEM after addRows
t=120s max_usage=14327676928 memsw_max=16311369728 swaps=/swapfile-marketsim:10485756:2083800  | INFO: MEM
t=180s max_usage=14327676928 memsw_max=16320729088 swaps=/swapfile-marketsim:10485756:2081168  | INFO: MEM
t=240s max_usage=14327676928 memsw_max=16321736704 swaps=/swapfile-marketsim:10485756:2082664  | INFO: MEM
t=300s max_usage=14327676928 memsw_max=16322699264 swaps=/swapfile-marketsim:10485756:2082664  | INFO: MEM
t=360s max_usage=14327676928 memsw_max=16325705728 swaps=/swapfile-marketsim:10485756:2085936  | INFO: MEM
t=420s max_usage=14327676928 memsw_max=16333787136 swaps=/swapfile-marketsim:10485756:2094676  | INFO: MEM
t=480s max_usage=14327676928 memsw_max=16337772544 swaps=/swapfile-marketsim:10485756:2098568  | INFO: MEM
t=541s max_usage=14327676928 memsw_max=16339292160 swaps=/swapfile-marketsim:10485756:2099476  | INFO: MEM
t=601s max_usage=14327676928 memsw_max=19433365504 swaps=/swapfile-marketsim:10485756:4423224  | INFO: MEM
t=661s max_usage=14327676928 memsw_max=19433365504 swaps=/swapfile-marketsim:10485756:4422536  | INFO: MEM
t=721s max_usage=14327676928 memsw_max=19433365504 swaps=/swapfile-marketsim:10485756:4422356  | INFO: MEM
t=781s max_usage=14327676928 memsw_max=19433365504 swaps=/swapfile-marketsim:10485756:4422176  | INFO: MEM
t=841s max_usage=14327676928 memsw_max=19433365504 swaps=/swapfile-marketsim:10485756:5324628  | INFO: MEM
t=901s max_usage=14327676928 memsw_max=20304891904 swaps=/swapfile-marketsim:10485756:785636  | INFO: EIA-
DONE elapsed=961s MAXU=14327676928 MAXSW=20304891904 MAXHWM=37314560 MAXSWAP=7417856
```

## 5. Exit, wall time, swap AFTER the run

| item | value |
|---|---|
| exit | clean; log ends with `wrote calibration bundle to` then `memory peak:`, then the replay's legitimacy-diagnostics report |
| launch → process gone | 01:52:21 UTC → ~02:08:20 UTC, sampler elapsed **961 s** (16.0 min); runner phase timing total 937.6 s |
| phase timing | data_prep 54.6 s · solve_p0 525.8 s · markup 21.2 s · solve_p1 269.0 s · results_write 67.0 s |
| `/proc/swaps` after | `/swapfile-marketsim file 10485756 8 -2` (10 GiB swapfile persists, 8 kB used) |
| legitimacy gate | `WARNING: legitimacy diagnostics gate FAIL on the replayed bundle` — the replay's standard rescore, reported, not this shard's question |

Budget: under the 20-minute shard cap with ~4 minutes to spare. The runner's 24 GiB target was
not reached (13.34 + 10 = 23.3 GiB, warned as such), and the solve still fit: peak RSS+swap 18.91 GiB.

## 6. Price diff against the keeper's committed 2023 sidecar (zero LP)

`hourly/system_2023.parquet`, keeper vs replay, both `(70080, 9)`, columns
`year, pass, zone, hour, price, slack, dump, demand, reserve_price`. The prescribed snippet's
`np.issubdtype` raised on the pandas `StringDtype` of `pass`/`zone`; re-run with
`pd.api.types.is_numeric_dtype` over the same numeric columns (`year, hour, price, slack, dump,
demand, reserve_price`), `atol=1e-9, rtol=0`:

```
differing columns: {}
total differing numeric cells 0 of 490560
price         max abs diff 0.0   mean keeper 33.89972503431436  mean replay 33.89972503431436
reserve_price max abs diff 0.0   mean keeper 0.03778696226751018 mean replay 0.03778696226751018
```

The replay reproduces the keeper's 2023 P1 prices exactly.

## 7. Bundle listing (local disk only, 209 MB, not committed)

```
results/calibration/misooom_A_2023:
btm.parquet  dispatch/  floors/  flows.parquet  hourly/  legitimacy_diagnostics.json
meta.json  run_config.json  storage.parquet  system.parquet

results/calibration/misooom_A_2023/hourly:
class_band_hourly_2023.parquet  class_hourly_2023.parquet  network_2023.parquet
reserve_family_2023.parquet  storage_2023.parquet  system_2023.parquet  unit_hourly_2023.parquet
```
