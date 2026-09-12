# SHARD miso255-sil-2022C — STOPPED at HARD STOP 3 (free disk)

**Shard:** `miso255-sil-2022C` · **Pin:** `d0fec486fa2218afc55dbd2eb377bc2570e61699` (verified)
**Date:** 2026-09-12 · **Outcome:** STOPPED before the solve. No LP was run. No bundle was
written. Nothing was repaired, patched, deleted or worked around.

## Whether a STOP fired

Yes — **HARD STOP 3 (free disk) fired, and it is the only reason this shard did not solve.** The
prompt's threshold is "under ~20 GiB available, STOP and report the `df` output", with the stated
rationale that a previous shard died with ENOSPC. This container has **16.72 GiB available**
(17,949,097,984 bytes) and **zero swap provisioned**, so the stop condition is met on its face and
is not marginal. HARD STOPS 0, 1 and 2 all PASS: `git rev-parse HEAD` equals the pinned SHA
exactly; the two required test files report `14 passed in 2.79s`; and
`results/calibration/miso251_screen2022/` is present with both `meta.json` (18,027 B) and
`hourly/class_hourly_2022.parquet` (655,709 B). HARD STOP 4 (the
`aggregate simultaneous-transfer limit REPLACED ... declared scalar 8700 MW` marker, which is the
point of the whole shard) was **not reached** — it can only be evaluated from a solve log, and no
solve was started. Per rule 32(c)(7) this shard stops with a clear report rather than fixing
infrastructure; the disk cannot be freed within shard scope because the only materially reclaimable
bytes are other lanes' solved bundles, and deleting a result is forbidden by rule 31 `[R-RETAIN]`.

## HARD STOP 3 — the `df` output, verbatim

```
$ df -h /
Filesystem      Size  Used Avail Use% Mounted on
/dev/vda        252G   21G   17G  55% /

$ df -B1 /
Filesystem        1B-blocks        Used   Available Use% Mounted on
/dev/vda       270553174016 21831790592 17949097984  55% /

$ free -h
               total        used        free      shared  buff/cache   available
Mem:            15Gi       719Mi       1.2Gi       6.0Mi        14Gi        15Gi
Swap:             0B          0B          0B

$ swapon --show
(no output — no swap active)

$ ls -la /swapfile* /var/swap*
(no such files — /swapfile-marketsim does not exist)
```

## Provisioning arithmetic the parent needs in order to rule

Read-only, from `scripts/lib/solve_container.py` at the pinned SHA — stated so the parent can decide
whether to re-launch here rather than having to re-derive it. Nothing below was acted on.

- `DEFAULT_TARGET_GIB = 24` (RAM+swap floor a per-plant ISO-year solve is provisioned to)
- `DISK_RESERVE_GIB = 6` (never consume the last of the allowance — a solve also writes parquet)
- `SWAPFILE = /swapfile-marketsim`
- Cgroup ceiling on this box is the documented ~13.34 GiB, so the deficit against the 24 GiB target
  is ~10.66 GiB, and `add_gib = int(min(deficit, free - reserve)) = int(min(10.66, 10.72)) = 10`.

So the runner **would** provision a 10 GiB swapfile and reach ceiling+swap ≈ 23.3 GiB against its
24 GiB target, leaving ~6.7 GiB of free disk — and a MISO bundle in this tree is single-digit MB
(`miso_fuelvintage_A` is 7.5 MB; the control bundle's whole `hourly/` is ~2.1 MB), not GB. On those
numbers the solve would plausibly fit. **That is explicitly not this shard's call to make.** The
threshold was pre-registered ex ante, the ENOSPC precedent it encodes is named in the prompt, and a
shard overriding its own hard stop on its own arithmetic is the failure mode the stop exists to
prevent. The parent either re-launches this leg on a container with ≥20 GiB free, or amends the
threshold in the next shard prompt with the above arithmetic as its basis.

## Disk census (read-only, for the re-launch decision)

```
830M  results          6.4G  data          6.0G  .git
```

Largest entries under `results/calibration/`: `caiso275_B_gascoupling_2024` 91M, `…_2025` 87M,
`…_2022` 51M, `…_2023` 48M, `ercot265_receipts_five_year` 14M, `ercot256_five_year_keeper` 14M.
All other-lane results; none touched.

## Not collected (no solve ran)

The gate-scorer JSON (`scripts/probes/_miso255_screen_gates.py`), the `container preflight:` lines,
the `memory peak:` line, the `year 2022 phase timing:` line and the G-1 marker line are all absent
because the solve was never started. `results/calibration/miso255_sil_2022/` does not exist.
