# FINDING — PJM-NEXT card 1, CONTROL leg 2019: solve OOM-killed, no bundle (2026-09-25)

Shard of orchestrator PJM-NEXT. Record: `docs/PRECOMMIT-pjm-next-c1-year-correct-membership-2026-09-25.md` §3/§7.

**Outcome: STOPPED, no bundle pushed.** The keeper-recipe replay for 2019 was OOM-killed by the
container's memory cgroup inside the P1 build/solve, after P0 had solved. No artifact was written
(`results/calibration/pjmnext_ctl_2019/` holds only an empty `dispatch/`). Nothing is pushed except
this doc.

## What ran

- `git rev-parse HEAD` = `7f0953845350089732892f83248726d4b04fb84f` (pin verified before any work).
- `pip install -e .`; `hydrate_data.py --profile pjm` (full clone, no-op); `regenerate_clean.py` full:
  56/58 ok. The two failures were `ercot-wtx-congestion` (exit 1, ERCOT-only) and
  `emissions-unit-annual` (exit **-9**, OOM-killed; it failed identically on a solo re-run). The solve
  never named a missing partition before it died.
- `fetch_pjm_da_virtuals.py --years 2019`: ok, 12 monthly files, no errors.
- Solve, unmodified, no `--set`, no `--no-container-preflight`:
  `replay_keeper.py results/calibration/rpjm2_span --years 2019 --out-dir results/calibration/pjmnext_ctl_2019`

## Measured

- `container preflight: memory ceiling 13.36 GiB (…/claude-code-bash/memory.limit_in_bytes; MemTotal 15.72 GiB), swap 0.0 GiB, target ceiling+swap 24 GiB`
- `container preflight: provisioned 3 GiB swap at /swapfile-marketsim — ceiling 13.36 + swap 3.0 = 16.4 GiB`
- `WARNING: container preflight: ceiling+swap 16.4 GiB is below the 24 GiB target; a per-plant ISO-year LP (MISO, PJM) may be OOM-killed here`
- Swap was capped at 3 GiB by the **disk allowance**: `df /` showed 6.9 GiB available after the
  swapfile, with `data/clean` taking 1.9 GiB.
- P0 completed: `Matrix build: 25.741s, Solve: 347.372s (cold, simplex iterations 391372, objective 8465614252.0130)`.
- Killed about 10 min after launch (1790313622 → 1790314235, 613 s), exit 137. Kernel log:
  `Memory cgroup out of memory: Killed process 7011 (python3) total-vm:27936316kB, anon-rss:13942720kB`.
- cgroup v1: `memory.max_usage_in_bytes` = 14,345,912,320 (= the limit), `memory.memsw.max_usage_in_bytes`
  = 17,567,170,560 (16.36 GiB, i.e. RAM ceiling + the full 3 GiB of swap). The `memory peak:` line was never
  printed because the process was killed.

## Diagnosis

This is an infrastructure capacity limit, not a model or recipe defect. A PJM per-plant year needs
more than 16.4 GiB of RAM plus swap here. The runner's preflight targets 24 GiB, but this container's
disk allowance left room for only 3 GiB of swap. G1 checks (a), (b), (d) and (e) could not be read
from a `run_config.json` because none was written. Check (c), the EIA-860 vintage_2019 log line, was
not reached before the kill.

## What is needed (orchestrator's call)

Re-launch this leg in a container that can back the 24 GiB preflight target: about 11 GiB of free
disk for swap beyond this box's 6.9 GiB, or a larger memory cgroup. The lost cost is about 10 min
(P0 only). Per the shard rules, this shard did not free disk, alter the runner, or retry.
