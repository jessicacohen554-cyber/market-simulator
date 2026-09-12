# SHARD miso255-sil-2024C — STOPPED AT HARD STOP 3 (disk)

**Outcome: STOPPED BEFORE THE SOLVE. No LP was run. No bundle exists. No gates were scored.**
Per rule 32(c)(7), a shard that stops with a clear report is a SUCCESS; this doc is that report.

## Hard stops

| # | Check | Result |
|---|-------|--------|
| 0 | `git rev-parse HEAD` == `d0fec486fa2218afc55dbd2eb377bc2570e61699` | **PASS** (exact match) |
| 1 | `test_run_year_kwarg_binding.py` + `test_miso_measured_sil_envelope.py` | **PASS** — `14 passed in 2.53s` |
| 2 | `results/calibration/miso_fuelvintage_A/` has `meta.json` + `hourly/class_hourly_2024.parquet` | **PASS** (both present, 17,936 B and 696,592 B) |
| 3 | Free disk >= ~20 GiB | **FAIL — 16.3 GiB free** |
| 4 | Arm-fired marker `aggregate simultaneous-transfer limit REPLACED ... declared scalar 8700 MW` | **NOT REACHED** — no solve was run |

## HARD STOP 3 — the blocker, verbatim

```
$ df -h /
Filesystem      Size  Used Avail Use% Mounted on
/dev/vda        252G   21G   17G  57% /

$ df --output=size,used,avail,pcent -B1 /
   1B-blocks        Used       Avail Use%
270553174016 21831815168 17949073408  55%      # at shard start
                         17476481024           # after `uv` synced its wheel cache
```

Available: **17,476,481,024 B = 16.28 GiB**, against the prompt's `~20 GiB` floor.

### Why this is a real blocker and not a rounding call

Swap is **empty** on this container:

```
$ free -h
               total        used        free      shared  buff/cache   available
Mem:            15Gi       739Mi       1.2Gi          12Mi       14Gi        14Gi
Swap:             0B          0B          0B

$ swapon --show
(no output — no swap device or file)
```

Per CLAUDE.md rule 32 `[R-SHARD]` clause (c)(8), a per-plant MISO year peaks above the
~13.3 GiB nested-cgroup ceiling and only fits because
`scripts/lib/solve_container.ensure_solve_container` provisions a **swapfile of up to 24 GiB**
before the first loader runs. That swapfile is written to this same filesystem. With 16.28 GiB
free it cannot be provisioned at its target size, and the shard prompt forbids
`--no-container-preflight`, forbids hand-provisioning swap, and forbids setting memory env vars.

This is the same failure mode the prompt already attributes to the earlier shard
("an earlier shard died with ENOSPC"): the preflight's own swapfile write is what exhausts the
allowance. Proceeding would have spent ~16 min of LP to reproduce that ENOSPC.

## Disk inventory (read-only; nothing deleted — rule 31 `[R-RETAIN]`)

```
6.4G  data/          (miso profile already hydrated)
830M  results/
 70M  docs/
 66M  frontend/
 16M  scripts/
```

Largest bundles under `results/calibration/`:

```
 91M  caiso275_B_gascoupling_2024
 87M  caiso275_B_gascoupling_2025
 51M  caiso275_B_gascoupling_2022
 48M  caiso275_B_gascoupling_2023
 14M  ercot265_receipts_five_year
 14M  ercot256_five_year_keeper
 13M  ercot261_five_year_keeper
 13M  ercot255_five_year_keeper
7.5M  miso_fuelvintage_A          <- this shard's control, untouched
```

The four CAISO `caiso275_B_gascoupling_*` bundles are ~277 MB together. **They were NOT deleted.**
They are another lane's solved results and rule 31 `[R-RETAIN]` forbids a session removing a result
the owner has not ruled on for promotion. In any case 277 MB does not close a ~4 GiB gap, so no
cleanup within this shard's authority would have made the solve fit.

## What the parent needs to decide

The 16.28 GiB is the container's whole writable allowance, not project litter — `data/` at 6.4 GiB
is the hydrated `miso` profile the solve requires. The gap is between the allowance and what the
preflight swapfile plus the solve need together. This is an **environment provisioning** matter and
is outside a shard's authority to change ("a shard that repairs infrastructure is a FAILURE").

Re-launch on a container with materially more free disk, and the shard prompt is otherwise
unchanged and ready to run as written.

## Nothing was written, pushed, or removed

- No `results/calibration/miso255_sil_2024/` was created.
- No file under `src/`, `scripts/`, or `frontend/data/backcast/**` was touched.
- No result of any lane was deleted.
- This doc is the only new file.
