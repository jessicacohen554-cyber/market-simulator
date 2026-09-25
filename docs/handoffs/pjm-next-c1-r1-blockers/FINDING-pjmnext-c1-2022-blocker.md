# FINDING — PJM-NEXT card 1, arm shard 2022: BLOCKED, no bundle (2026-09-25)

Shard of orchestrator PJM-NEXT. Pinned commit `7f0953845350089732892f83248726d4b04fb84f`
(verified `git rev-parse HEAD` before any work). Record: `docs/PRECOMMIT-pjm-next-c1-year-correct-membership-2026-09-25.md`.

**Outcome: no bundle pushed.** There are two independent blockers: G1(e) failed, and the solve was OOM-killed
after P0, before any artifact was written. `results/calibration/pjmnext_c1_2022/dispatch/` is empty.

## Command (unmodified runner, no `--no-container-preflight`)

```
python3 scripts/replay_keeper.py results/calibration/rpjm2_span --years 2022 \
  --set mid_vintage_exit_carry=true --set fleet_zone_vintage_coords=true \
  --set benchmark_membership_vintage_union=true \
  --out-dir results/calibration/pjmnext_c1_2022 --note "PJM-NEXT card 1 arm, 2022"
```

Setup: `pip install -e .`. The profile hydration was a no-op because this is a full clone. `regenerate_clean.py`
failed 2 of 58 datatypes: `emissions-unit-annual` exited −9 (killed), and `ercot-wtx-congestion` failed on missing `tzdata`
(ERCOT-only). `fetch_pjm_da_virtuals.py --years 2022` exited 0.

## Blocker 1 — G1(e) FAIL: injected-unit count 77, gate expects 73

Log (INFO), identical on both fleet builds:

```
mid-vintage-year exit carry (PJM 2022): injecting 77 unit(s), 4534 MW — plants [884, 2401, 2836, 2902,
3139, 3142, 3143, 3144, 3146, 3147, 3154, 3155, 6019, 6776, 7770, 7898, 8226, 10043, 10099, 10566, 50385,
50952, 54265, 54781, 56865, 56868, 57406, 59792, 59959, 59960, 60499, 60803]
```

That is **77 units / 32 plants / 4,534 MW**. The PRECOMMIT disagrees with itself on this year:

- §4 G1 expects **N = 73**.
- The §1a census row expects **22 plants / 4,145 MW**.

Neither figure matches the observed values. Note that the zoning line below also reads "73 of 73". The 73 in G1 may
have been copied from that line, not from the mvx census. That is for the parent to adjudicate. This shard does not
decide which number is right.

## Blocker 2 — OOM kill (exit 137) after the P0 solve

```
container preflight: memory ceiling 13.36 GiB (nested cgroup .../claude-code-bash/memory.limit_in_bytes; MemTotal 15.72 GiB), swap 0.0 GiB, target ceiling+swap 24 GiB
container preflight: provisioned 3 GiB swap at /swapfile-marketsim — ceiling 13.36 + swap 3.0 = 16.4 GiB
container preflight: solve profile MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1
WARNING: container preflight: ceiling+swap 16.4 GiB is below the 24 GiB target; a per-plant ISO-year LP (MISO, PJM) may be OOM-killed here
...
Matrix build: 18.970s, Solve: 353.578s (cold, simplex iterations 421062, objective 17141995876.5103)
<killed, exit 137>
```

Only 3 GiB of swap could be provisioned. After the clean-tree regen, root showed only 6.9 GiB free out of 252 GiB total,
which is the per-session disk allowance. The process died after the first LP solve (P0), before P1. No `memory peak:` line was
emitted because the process was killed. Wall time was 594 s.

## G1 status

| check | status |
|---|---|
| (a) keeper flags true in `run_config.json` | NOT CHECKABLE: no `run_config.json` was written |
| (b) `campd_unit_outages.sha256` = `312a11b8…` | NOT CHECKABLE: no `run_config.json` was written |
| (c) log names EIA-860 `vintage_2022` | NOT OBSERVED: the INFO log prints only "Loaded PJM fleet from EIA-860 parquet (2087 generators)", with no vintage path |
| (d) three arm flags true | NOT CHECKABLE: no `run_config.json` was written. The flags visibly took effect: see the (e)/(f) lines |
| (e) mvx injects 73 units | **FAIL: 77 units / 4,534 MW** |
| (f) `fleet_zone_vintage_coords` K > 0 | PASS: "3 of 2087 generators" (fleet); "73 of 73" (injected-retiree frame) |
| (g) EIA-923 2022 = 833.192 TWh | NOT CHECKABLE: no `meta.json` / bundle |

## For the parent

- Reconcile the G1(e) expectation for 2022: 73 (§4), 22 plants / 4,145 MW (§1a), or 77 units / 32 plants / 4,534 MW (observed).
- A re-launch needs a container with enough free disk for about 8 GiB of swap, the recipe prior PJM/MISO solves fit under.
  Here, the regenerated clean tree and the DA-virtuals corpus left only 6.9 GiB free.
- Nothing was deleted. No edits were made under `src/` or `scripts/`.
