# ADDENDUM 3 to PRECOMMIT-nyiso229 — the first screen shard was OOM-KILLED, and the legs are re-split one per container

**Session:** nyiso-229 · **Date:** 2026-09-12 · **ZERO LP in the parent** (rule 32 `[R-SHARD]` (a)).
**No screen result exists yet. Nothing armed, nothing promoted, keeper unchanged.**

This records a failed spend honestly and changes **one** thing: the two legs move from one shared
container to **one container each**. No gate, no screen year, no reporting rule moves.

---

## 1. WHAT HAPPENED

Shard `session_0163Xva3Mh4S5T7sMoznnbki`, launched at the pinned SHA `d0694aa7`, was asked to solve
both legs sequentially in one container (ADDENDUM 1 §3). Its own report:

> control leg failed at dispatch (**OOM**) at ~4 min; arm leg **skipped**; environment drift noted
> (**highspy 1.14 → 1.15.1**, **pandas 3.0.3 → 3.0.5**); *"repair is parent's decision per rule 32"*.

**The shard did exactly the right thing**, and it is recorded as a success of the charter rather than
a failure of the shard: rule 32(c)(7) — *"a shard that stops with a clear report is a SUCCESS; a shard
that repairs infrastructure is a FAILURE."* It did not patch the runner, did not disable the
preflight, did not push a half-written bundle, and did not attempt the arm on a container it had just
watched die. It also surfaced the version drift unprompted, which is the more interesting half.

## 2. WHAT I CHECKED IN THE PARENT, at zero LP

| check | result |
|---|---|
| Is the preflight reached through `replay_keeper`? | **YES** — `ensure_solve_container` sits inside `run_calibration_full.solve_and_persist` (line ~3953), which `replay_keeper` calls. It ran. |
| Does it actually provision swap here? | **YES** — ceiling **13.34 GiB** (the exact figure rule 32(c)(8) names), swap 0 → **9 GiB provisioned**, total **22.3 GiB**, pins `MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1`. |
| Does swap actually *extend* the cgroup limit, or is it capped? | **It extends it.** `memory.memsw.limit_in_bytes` is effectively unlimited (9.22e18) against a `memory.limit_in_bytes` of 14,327,676,928, so swap is not accounted against the ceiling. The preflight's approach is sound. |
| Does the preflight warn? | **YES, and it was right**: *"ceiling+swap 22.3 GiB is below the 24 GiB target; a per-plant ISO-year LP may be OOM-killed here."* |
| Are dependencies pinned? | **NO.** `pyproject.toml` carries `highspy>=1.7`, `numpy>=1.26`, `pandas>=2.1`, … — every one a floor, no ceiling. A fresh container resolves **highspy 1.15.1 / pandas 3.0.5 / numpy 2.4.6 / scipy 1.17.1 / pyarrow 25.0.1**. |

**So the OOM is environmental, not intrinsic to the year.** NYISO 2022 has been solved before, twice:
the committed keeper touchpoint `nyiso_fuelvintage_H2` is a 2022 solve, and nyiso-228's arm-C span
solved 2022–2025 in a single shard in ~14 minutes. The year fits. What changed is the container and
the resolved package set.

## 3. THE CHANGE: ONE LEG PER CONTAINER

Two shards, launched in parallel, one leg each — `nyiso229_ctrl_y2022` and `nyiso229_arm_y2022`. Rule
12 `[R-PARALLEL]` caps per-plant multi-zone concurrency at ~2 simultaneous invocations; this is
exactly 2. Each leg gets the whole 22.3 GiB instead of following another leg's allocator in the same
process.

**ADDENDUM 1 §3's common-mode argument SURVIVES the split, and this is the part worth being precise
about.** What that argument needed was that the *solve profile* be identical on both sides, not that
the two legs share a process. The pins are applied by the **same code path** (`ensure_solve_container`)
in both containers, from the **same pinned SHA**, and both shards `pip install -e .` from the **same
unpinned spec at the same time**, so they resolve the same versions. The thread count, arena cap and
HiGHS thread setting are therefore identical on both sides — which is the whole of what the
OMP-drift concern required.

**What the split does cost, stated rather than glossed:** the two legs no longer share one *process*,
so a hypothetical allocator- or ordering-dependent difference would no longer cancel. I judge that
negligible against a documented OOM, and the version report from both shards will show whether the
resolved sets actually matched. If they differ, that is a finding and the screen is re-run, not
reinterpreted.

Both shards additionally carry a **pre-solve memory hard stop**: run the preflight, report its lines,
and if ceiling+swap is below 20 GiB free disk and retry — *"do not solve into an OOM"* — and the arm
shard carries a **silent-no-op hard stop**: if it resolves the day-grain `-perunitmerit-` file instead
of `-perunitmerithour-`, it stops and does not push, because that is the one outcome that would make
the screen uninterpretable.

## 4. THE DEPENDENCY DRIFT IS A REAL FINDING, AND IT IS NOT THIS ARM'S TO FIX

Every runtime dependency is floor-pinned only. A container provisioned today therefore solves on a
different HiGHS than every committed bundle it is compared against, and **nothing in the repository
records which one a bundle solved on** — `meta.json` carries the config and the `git_sha`, not the
resolved package set. That is a reproducibility gap of exactly the class nyiso-177 flagged for the
outage extract (*"carries a null `derive_invocation` and cannot be reproduced at HEAD at any flag
setting"*), one layer down.

It is **filed, not acted on**: pinning the solve stack, or recording the resolved versions into
`meta.json`, changes the solve environment of every ISO's lane and is a program-level decision, not a
NYISO calibration arm's. Both shards report their versions so this arm at least knows what it ran on.
*(Related and already known: neiso-106 found a 2025 solve **bit-identical** across four package-version
deltas — same P0 objective to 13 significant figures — so drift is not automatically material. It is
the memory footprint, not the arithmetic, that is in question here.)*

## 5. WHAT DOES NOT CHANGE

Screen year **2022**. All seven gates verbatim, G-DEMAND still on **served demand**. The C3c
precision/recall reporting rule. The ex-ante price direction, still not gated on. Rule 16
`[R-ALLYEARS]` if the screen clears. Rule 31 `[R-RETAIN]` — nothing deleted, and the promotion
question is the owner's. **No LP cost has been recovered and none is hidden:** one shard-container of
~4 minutes was spent and produced no bundle.
