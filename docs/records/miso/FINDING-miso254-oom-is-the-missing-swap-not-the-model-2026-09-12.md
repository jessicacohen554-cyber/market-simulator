# FINDING miso-254 — the MISO OOM is the MISSING SWAP STEP, not a model change; the runners now provision it themselves

**Session:** miso-254, 2026-09-12. **Keeper unchanged:** `2026-09-09-miso-250-ep-gas`
(`results/calibration/miso_fuelvintage_A`). **LP spent in the parent: none** (rule 32(a)).

## 1. What the owner asked

> Diagnose and fix the MISO OOM issue and launch a shard to solve one year to see if it
> resolves. Within the last 48 hours a change was made to the MISO config so it's no longer
> running and keeps OOM-ing in this container despite being able to run 200+ times before.

## 2. The answer, up front

**No MISO config change did this.** The MISO solve recipe is byte-for-byte the keeper's; the
last MISO solves that succeeded (miso-251, 2026-09-10 03:12–03:14 UTC, SHA `a3c806ef` /
`4d498369` / `94bba7e3`) and the first that OOM'd (miso-252/253, 2026-09-10 06:00–19:30 UTC,
SHA `6b82b833`) differ on the MISO solve path by nothing that touches the LP's size. What
differs is the **container recipe**:

| run | swap | outcome |
|---|---|---|
| miso-250 keeper solve, 2026-09-09 (fuelvintage lane) | `prepare_solve_container.py` → 8 GiB swapfile | solved 2023/2024/2025 |
| miso-251 rungs 2020/2021/2022, 2026-09-10 03:xx | "15.7 GiB + 8.0 GiB-swap container" (RESULT §5) | solved, peak RSS 13.30 GB, inside the 20-min cap |
| miso-252 shards ×3, miso-253 shards ×2, 2026-09-10 | **none** — the prompts skipped the step | OOM-killed at anon-RSS 13.30 GiB, inside HiGHS `run()` |
| ee40acd2 / eaa9d6f1 measurement, 2026-09-11 | none | OOM-killed at 13.31 GiB |

Two facts make the mechanism exact:

1. **The binding memory ceiling is 13.34 GiB, not 15.7.** The limit sits on the nested memory
   cgroup `/process_api/<id>/claude-code-bash` (`memory.limit_in_bytes = 14,327,676,928`);
   `free`, `MemTotal` and the root cgroup all read 15.7 GiB. Re-measured in this container:
   identical. miso-253's shards found this too (`docs/SHARD-miso253-screen2023*.md` §1).
2. **The cgroup has NO swap limit** (`memory.memsw.limit_in_bytes` unlimited, swappiness 60).
   With a swapfile present the kernel reclaims the cold part of the simplex workspace to swap
   when RSS reaches 13.34 GiB; without one, the only reclaim left is the OOM killer. That is
   why every swapped run reports "peak RSS 13.30 GB" and finishes, and every unswapped run
   reports "peak RSS 13.30 GiB" and dies — **both numbers are the ceiling, not the demand.**

So "200+ runs before" is true and so is "OOMs every time now": the MISO year LP has needed
more than the bash cgroup allows for weeks (miso-169, 2026-08-19, already measured 13.9–14.4 GB
peaks on this box class and made it fit with *exactly* an 8 GB swapfile), and every run that fit
was swapped. The step lived in prompts — the fuelvintage lane's per-ISO prompt pack cites
`scripts/prepare_solve_container.py` (added 2026-09-09) — and the rule-32 shard prompts written
on 2026-09-10 dropped it. Five shards then diagnosed the OOM as "MISO no longer fits", and
`FINDING-miso252` §1 declared "no MISO LP can run in this infrastructure".

## 3. What DID grow, for the record (not the cause, stated so nobody re-hunts it)

The LP is larger than it was in August, and that is the keeper's own structure, not a
regression:

| | miso-169 (2026-08-19) | miso-253 (2026-09-10) |
|---|---|---|
| rows | 492,516 | 1,026,876 |
| columns | 25,447,800 (2,905 / hour) | 29,643,840 (3,384 / hour) |
| nnz | 50.3 M | 86.2 M |
| build high-water | 5.12 GB | 6.98 GiB |

The +479 columns/hour match the reserve-member census growing 2,547 → ~3,025 (the intermediate
tranche splits and per-plant must-run families that entered the keeper through miso-215..250),
and the row/nnz growth is the zone × product reserve-supply structure over those members.
Every one of those mechanisms is in the keeper recipe that solved on 2026-09-09 **with swap**.
The solve peak was already ≥13.9 GB on 2026-08-19 with the smaller LP, so the growth moved the
peak further past a ceiling it was already past; it did not create the condition. The two
lifetime fixes of 2026-09-11/12 (ee40acd2, eaa9d6f1: −461 MB held across `h.run()`) are
correct and stay; they were never going to be the remedy on their own.

## 4. The fix — the runner provisions the container, so no prompt can forget it

New shared helper `scripts/lib/solve_container.py`, called automatically before the first
loader by **both** solve entry points — `run_calibration_full.solve_and_persist` (hence
`replay_keeper.py`, which calls it directly) and `run_calibration.main`:

- `memory_ceiling()` — the **binding** ceiling: the minimum over `MemTotal` and every finite
  `memory.max` (cgroup v2) / `memory.limit_in_bytes` (cgroup v1) on the process's own cgroup
  path, walked up to the root. Reads 13.34 GiB here where every prior probe read 15.7.
- `provision_swap(24 GiB)` — the `prepare_solve_container` recipe (fallocate + mkswap + swapon
  at `/swapfile-marketsim`), sized to the deficit and bounded by free disk minus 6 GiB,
  **idempotent** (an active swapfile is kept), never raising (not root / no disk → a WARNING
  naming the ceiling, and the solve proceeds).
- the single-thread solve-profile pins (`MALLOC_ARENA_MAX=2`, `MARKET_SIM_HIGHS_THREADS=1`,
  `OMP_NUM_THREADS=1`) as **defaults** — `os.environ.setdefault`, so an operator value wins —
  the profile every golden and wallclock capture already uses. `M_ARENA_MAX` is also applied to
  the live allocator through `mallopt`, since the env var alone is read only at process start.
- `log_peak_memory()` at the end of every invocation: the cgroup's `max_usage_in_bytes` and
  `memsw.max_usage_in_bytes` (v1) / `memory.peak` + `memory.swap.peak` (v2). **A finished
  swapped run finally reports how far over the ceiling the LP really is** — the number no
  record in this repo has, because an OOM-killed process can only ever report the limit.

Opt-out is the CLI flag `--no-container-preflight` on both runners (no env-var knob, rule 24;
and none of this is a `ScenarioConfig` tunable — swap and thread count are workspace choices,
`model/lp/model.py` records that the optimum is identical). `scripts/prepare_solve_container.py`
is now a thin CLI over the same helper, so a hand-prepared container and an auto-prepared one
agree byte for byte. Tests: `tests/unit/pipeline/test_solve_container_preflight.py` (11 cases:
nested-v1 limit binds over an unlimited root and `MemTotal`; v1 "unlimited" sentinel; v2
ancestor limits; dry-run writes nothing; disk-too-small and already-active paths; pins default
but never override; the three pin tables stay equal; the no-provision path writes nothing).

CLAUDE.md rule 32(c) gains item 8: the ceiling is the nested cgroup, never `free`; a
MISO/PJM shard names no memory recipe of its own beyond running the runner unmodified, never
passing `--no-container-preflight`, and reporting the `container preflight:` and `memory peak:`
log lines.

## 5. The shard test (pre-registered here, before any solve)

Two shards, both pinned to the SHA that carries §4, both replaying the committed keeper on
2023 — the keeper's own recipe, `replay_keeper.py results/calibration/miso_fuelvintage_A
--years 2023`, so the control is the committed 2023 sidecar (rule 29(b) form 4) and nothing is
tuned:

| shard | arm | pre-registered reading |
|---|---|---|
| A | runner as shipped (preflight ON) | **must finish inside 20 min.** Reports the `container preflight:` line (ceiling 13.34, swap added), the `MEM LP size` line, the `memory peak:` line (the first honest RSS+swap demand number), wall time, and the P1 price diff against the keeper's committed `hourly/system_2023.parquet` (expected **0 of 52,560 differing cells** — the lifetime fixes are bit-identical by construction). |
| B | `--no-container-preflight` (same SHA, same recipe) | the **negative control**: if B is OOM-killed at ~13.3 GiB while A finishes, the mechanism in §2 is confirmed on the same code and the −461 MB hygiene alone is shown insufficient. If B also finishes, the hygiene sufficed on its own and swap is the belt behind it — a good outcome, recorded as such. |

Neither bundle is registered (rule 29: a keeper replay on a training year is a diagnostic,
not a run) and neither is committed (rule 29(c) / 31: the bundle family is gitignored; the
shard commits only its report doc). The promotion question does not arise — nothing here is a
candidate.

### 5.1 Results (both shards pinned to `0101b4ce`, same environment class, same recipe)

Reports: `docs/SHARD-misooom-A-2023.md` (branch `claude/misooom-A-2023`, commit `3bd2d1be`) and
`docs/SHARD-misooom-B-2023.md` (branch `claude/misooom-B-2023`, commit `c904f667`).

| | shard A — preflight ON | shard B — preflight OFF |
|---|---|---|
| ceiling read (nested v1 memcg) | 14,327,676,928 B = 13.34 GiB; MemTotal 15.70 | identical |
| swap before / after preflight | 0 → **10 GiB** at `/swapfile-marketsim` (runner-provisioned; 23.3 of the 24 GiB target, warned) | 0 (none; `container preflight:` lines = 0) |
| LP | 1,026,876 × 29,643,840, 86,198,400 nnz | identical |
| outcome | **solved**; `wrote calibration bundle` + `memory peak:` | **OOM-killed** ~85 s after launch, memcg `CONSTRAINT_MEMCG`, `failcnt` 20,725, anon-rss 13.28 GiB, `oom_kill 1` |
| phase timing | data_prep 54.6 s · P0 525.8 s · markup 21.2 s · P1 269.0 s · write 67.0 s · **total 937.6 s** | died after `addRows`, before P0 printed anything |
| **honest peak** | `cgroup_peak_rss_gib=13.34` (pinned at the ceiling from t≈120 s), **`cgroup_peak_rss_plus_swap_gib=18.91`**, `process_vmhwm_gib=13.32`; swap in use peaked at 5.08 GiB | `max_usage_in_bytes` = the limit byte-exact; the ceiling, not the demand |
| P1 prices vs the keeper's committed `hourly/system_2023.parquet` | **0 of 490,560 numeric cells differ**; `price` max abs diff 0.0, mean 33.89972503431436 both | no bundle |
| wall inside the 20-min shard cap | yes, 16.0 min launch → exit | n/a |

**Reading.** The negative control reproduces the miso-252/253 incident on the same SHA, same
code, same recipe, same box class: without swap the year dies at the memcg wall. With the
runner-provisioned swap it finishes, reproduces the keeper's prices bit-for-bit, and — for the
first time in this repo — states the demand: **a MISO 2023 per-plant year needs ~18.9 GiB of
RSS+swap at its peak, ~5.6 GiB over the 13.34 GiB bash cgroup.** That number is the target any
genuine solve-phase memory reduction must be measured against; the 461 MB of lifetime hygiene
(ee40acd2 / eaa9d6f1) was never within reach of it. The 10 GiB the runner added is what free
disk allowed (17 GiB free − 6 GiB reserve); it was enough with ~4.9 GiB of swap to spare.

## 6. Stated at the gate

- This does not shrink the LP. A per-plant MISO year still needs more than a 13.34 GiB bash
  cgroup, and a shard on a box that cannot swap (not root, or under ~7 GiB free disk) will
  still die; the preflight now says so in a WARNING before the loaders run instead of the OOM
  killer saying it 46 s into HiGHS. The `memory peak:` line from shard A is the number a real
  reduction would have to be measured against.
- `FINDING-miso252` §1's conclusion ("no MISO LP can run in this infrastructure") is
  superseded by this document; its §1b cgroup correction stands.
