# FINDING — PJM-NEXT card 1, arm leg 2020: shard STOPPED (G1 fail + OOM), no bundle pushed

Shard of orchestrator PJM-NEXT, pinned `7f0953845350089732892f83248726d4b04fb84f`
(HEAD verified before any work). Record: `docs/PRECOMMIT-pjm-next-c1-year-correct-membership-2026-09-25.md`.
Command run unmodified (§7 arm command, `--years 2020`, out-dir `results/calibration/pjmnext_c1_2020`).

## Two independent blockers

### 1. G1(e) FAIL — mid-vintage exit carry count differs from the PRECOMMIT

Observed (printed on both the fleet build and the solve build, identical):

```
INFO: mid-vintage-year exit carry (PJM 2020): injecting 35 unit(s), 1167 MW — plants [1555, 1560, 2837, 2840, 7701, 50879, 54934, 55773, 56365, 57843, 57846, 57847, 60213]
```

The PRECOMMIT gives two expectations, and they disagree with each other as well as with the log:

| source | expected | observed |
|---|---|---|
| §4 G1 / shard prompt | 34 units | **35 units** |
| §1a census table | 6 plants, 1,080 MW | **13 plants, 1,167 MW** |

The plant count (13 vs 6) is the larger gap. The orchestrator should re-run the §1a census at this pin
and reconcile it before relaunching. This shard did not diagnose it (no `src/`/`scripts/` edits).

### 2. OOM kill — the solve produced no artifact

- The P0 LP finished (`Matrix build: 18.269s, Solve: 341.743s (cold, simplex iterations 380281,
  objective 6616993389.9049)`). The process was then killed by the memcg OOM killer (exit 137) at
  wall 579 s, before anything was written. `results/calibration/pjmnext_c1_2020/` holds only an empty
  `dispatch/`.
- `container preflight:` lines:
  - `memory ceiling 13.36 GiB (…/claude-code-bash/memory.limit_in_bytes; MemTotal 15.72 GiB), swap 0.0 GiB, target ceiling+swap 24 GiB`
  - `provisioned 3 GiB swap at /swapfile-marketsim — ceiling 13.36 + swap 3.0 = 16.4 GiB`
  - `WARNING: … ceiling+swap 16.4 GiB is below the 24 GiB target; a per-plant ISO-year LP (MISO, PJM) may be OOM-killed here`
- No `memory peak:` line was printed, because the process was killed. The cgroup maxima are
  `memory.max_usage_in_bytes` 14,345,912,320 (13.36 GiB) and `memsw.max_usage_in_bytes`
  17,567,178,752 (16.36 GiB), which is the full ceiling plus swap. The kernel log shows
  `anon-rss:13943260kB`.
- Why swap was only 3 GiB: the root filesystem had **6.9 GiB free** (252 G, 82 % used) after the full
  clone and `regenerate_clean.py`, so the preflight could not provision the 8–11 GiB a PJM year needs.
  This container is a **full** clone (`hydrate_data.py` reported "FULL clone — every blob is already
  local"), not the blobless partial clone `docs/fast-clone.md` prescribes. That is the likely disk sink.
  A relaunch should use a partial clone, or a container with more disk, so the swapfile can reach its
  target.

## G1 status

| check | status | observed |
|---|---|---|
| (a) `scenario_config` keeper flags true | UNVERIFIABLE | run_config.json never written |
| (b) `campd_unit_outages.sha256` starts `312a11b8` | UNVERIFIABLE | run_config.json never written |
| (c) log names EIA-860 `vintage_2020` | NOT SEEN | no line containing `vintage_2020` in the 179-line log (`Loaded PJM fleet from EIA-860 parquet (2126 generators)` only) |
| (d) three arm flags true | UNVERIFIABLE | run_config.json never written |
| (e) carry line, 34 units | **FAIL** | 35 units, 1,167 MW, 13 plants |
| (f) `fleet_zone_vintage_coords` K > 0 | PASS | `102 of 2126` (main fleet); `34 of 34` (carried retirees) |
| (g) EIA-923 2020 = 805.898 TWh | UNVERIFIABLE | no bundle / meta.json |

## Other setup notes

- `fetch_pjm_da_virtuals.py --years 2020`: succeeded (all months written).
- `regenerate_clean.py`: 2 of 58 datatypes failed. `ercot-wtx-congestion` failed on a missing `tzdata`
  module (ERCOT only). `emissions-unit-annual` failed with exit -9 (OOM during regen). The solve did not
  name either as a missing partition before it was killed.

## Retrievability (rule 34(e))

**No bundle exists.** A promotion of this leg needs a full re-solve: ~10 min of LP (P0 alone took
342 s) plus P1, in a container with ≥ 24 GiB of ceiling plus swap. Nothing was deleted. Nothing under
`src/`, `scripts/` or `frontend/` was touched.
