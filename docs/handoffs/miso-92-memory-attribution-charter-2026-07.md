# CHARTER — miso-92 LANE 2: read the year-release memory telemetry

**Written before the solve was read.** Committed alongside the instrumentation
commit (`8f6bd81`) and before any telemetry line existed to look at, so the
decision rule below is pre-registered rather than fitted to the answer.

**Lane:** 2 of the miso-92 handoff — "READ THE MEMORY TELEMETRY (still unread)".
**Keeper:** `2026-07-25-miso-88-egrid-hr`, **unchanged by this lane**.
**Determination:** CALIBRATED-WITH-CAVEATS, 3/3 ledgered caveats —
**this lane cannot change it**, see §5.

---

## 1. What this lane is, and what it is not

It is a **measurement**, not a mechanism. miso-90 attributed MISO's 1.56 GB
cross-year resident floor as ~0.12 GB imports + ~0.02 GB module `lru_cache`
memoizations + ~0.07 GB cross-year accumulator frames, leaving **~1.35 GB (86 %)
unattributed**, and refuted the standing `lru_cache` hypothesis by measurement
(0.019 GB — ~2 % of the floor). Its closing instruction was explicit: *"That is a
measurement to take, not a hypothesis to argue."*

So this charter proposes **no mechanism, no floor, no parameter, and changes no
value**. The rubric fields a mechanism charter must fill — driver, the hours it
may bind, forward story — are **not applicable by construction**: nothing here
enters the LP. The corresponding commitment is therefore the stronger one, and it
is verifiable: **dispatch must be byte-identical to the keeper's 2023** (§4).

Three sessions in a row proposed a memory lever from a plausible story rather
than a number. This lane exists to end that, and it accordingly **pre-commits to
proposing no fix at all** until the measurement names an owner.

## 2. The instrument

The two telemetry lines miso-90 wired into the year-release seam of
`scripts/run_calibration_full.py` already answer *"how much of the resident is
live Python payload?"* via `cache_control.retained_footprint`.

This lane adds one line, `_glibc_arena_gb()` (`mallinfo2`, glibc ≥ 2.33), for a
reason internal to the pre-registered rule: miso-90's *"ndarray small"* branch is
not one outcome but **two, needing opposite fixes** —

* memory glibc has **freed but retained** (fragmentation) → the fix is arena
  tuning (`M_ARENA_MAX`/`mallopt`), entirely outside the model; versus
* memory a **C++ allocator still owns** (HiGHS surviving the Python-side `del`)
  → the fix is explicitly destroying the model object.

`mallinfo2` separates those directly (`fordblks` vs `uordblks`), so **one solve
resolves the whole rule** instead of landing on the small branch and costing a
second solve-year to disambiguate. It is read-only accounting: it allocates
nothing the solve depends on and cannot change dispatch.

## 3. Pre-registered decision rule and pass/fail bar

Thresholds are stated **as fractions of the ~1.35 GB unattributed gap** so the
read cannot be rationalised after the fact.

**Primary split — `ndarray_gb` at the post-release seam:**

| reading | verdict | where the next lane aims |
|---|---|---|
| **≥ 0.50 GB** (≳37 % of the gap) | LARGE — live Python payload owns the floor | the ndarray/pandas/sparse split names the owner; fix is in the model |
| **< 0.20 GB** (≲15 %) | SMALL — payload is not the owner | allocator/HiGHS side; go to the secondary split |
| 0.20–0.50 GB | MIXED | report both halves; no single owner claimed |

**Secondary split (SMALL branch only) — `mallinfo2`:**

| reading | owner | fix class |
|---|---|---|
| `free_in_arena` ≥ 0.50 GB | glibc retaining freed memory | arena tuning — outside the model |
| `in_use` ≫ `ndarray_gb` | C-side live allocation (HiGHS) | destroy the model object explicitly |
| `mmapped` large | live mmapped blocks | trace the allocation site |

**The lane PASSES if the floor is attributed** — i.e. the unattributed share
falls from ~86 % to a named owner with a number against it. It does **not** pass
by reducing memory, and it does **not** fail if memory is unchanged: reducing the
floor is the *follow-on* lane this measurement aims. A measurement that comes
back "the gap is X, owned by Y" is a complete deliverable.

**The lane FAILS** if the telemetry is absent, self-inconsistent, or under-reports
(miso-90 recorded two real bugs that made an earlier version silently report
0.000 GB against 200 MB live — that failure mode is the one to guard).

## 4. Verification obligations

* **Dispatch byte-identity** against the keeper's 2023 outputs. The
  instrumentation is diagnostic-only, so anything else is a bug in this lane.
* Telemetry sanity: the reported components must not exceed process RSS, and
  `arena + mmapped` must be of the same order as RSS.
* `ruff format --check` on the touched file; targeted regression baseline
  **8 failed / 186 passed** (all 8 pre-existing `test_pipeline_facade_shims`).
* Rule 27: `run_calibration_full.py` is ≫300 lines — edited in small hunks via
  the Edit tool, never rewritten from regenerated content; pushed blob verified.

## 5. Scope fences — what this lane will NOT do

* **Will not wire `clear_all_caches()` into the year loop.** 0.02 GB against a
  1.35 GB gap, with real correctness risk. miso-90 left it a diagnostic on
  purpose; adding a mechanism that does not address the cause is what rule 1
  warns against.
* **Will not enable cross-year warm start.** `MARKET_SIM_WARMSTART_XYEAR` makes
  retention *worse* and is deliberately off on the forecast path
  (`docs/cross-year-warmstart.md`).
* **Will not register the probe bundle on the dashboard.** It is a single-year
  solve, which rule 16 permits *only* as a throwaway diagnostic and forbids
  registering. Rule 15's register-every-run duty binds calibration results; this
  produces none — the keeper's 2023 dispatch is reproduced, not re-scored. Stated
  explicitly rather than silently skipped.
* **Will not propose a memory fix in this lane.** Per §1, the fix is chartered
  from the measurement, not alongside it.
* **Cannot consume ledger budget.** The caveat budget is 3/3 and this lane
  touches no scoring criterion, so there is nothing here to ledger and no
  BUILD-or-nothing exposure. The keeper, its determination and its DOF ledger
  are all untouched.

## 6. Standing constraint this does not lift

Whatever the reading, the **~14.4 GB single-year peak** against a 15 GB box is
untouched — MISO's P1 re-solves the same model in place (`_warm_p1`), so the peak
is one model and is irreducible without shrinking the LP. **The staged
one-year-per-process `--reuse-solved` recipe therefore remains required**, and no
result in this lane may be read as lifting it.
