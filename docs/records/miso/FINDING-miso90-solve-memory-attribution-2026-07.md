# FINDING (miso-90, 2026-07-26) — the module `lru_cache` hypothesis for MISO's cross-year resident floor is REFUTED by measurement (~0.02 GB, not ~1 GB); the residual is now instrumented instead of guessed

**Lane.** LANE C' of the miso-89 handoff: cut the memory that blocks a
multi-year MISO run. Cross-year *retention* was already partly fixed by
miso-89's `malloc_trim(0)` (`c4be52d`), which cut the year-to-year hand-off from
2.98 → 1.56 GB. What still blocks a 3-year single-process run is the **~14.4 GB
single-year peak** against a 15 GB box — leaving <0.6 GB of headroom, which is
why the handoff's target was a **baseline under ~0.6 GB**.

**Bottom line: the named lever does not work, and now we know by how much.**
The handoff's lead hypothesis — the ~26 unbounded module-level `lru_cache`
memoizations, "four `maxsize=None` caches over per-year arrays" in
`data/miso_outages.py` alone — holds **0.019 GB** on the MISO data path.
Clearing all of them is worth ~2 % of the 1.56 GB floor and ~0.1 % of the
14.4 GB peak. It is not the lever.

---

## 1. What was measured

Loading the MISO outage/fleet data path for **two** years in one process
(`unit_outage_derate_factors`, `miso_outage_mw_series`,
`miso_native_outage_derate_factors`, and the `_iso_plant_capacity` /
`_load_estimated` / eGRID-repair caches they pull in):

| stage | RSS |
|---|---|
| bare interpreter | 0.008 GB |
| + numpy / pandas | 0.097 GB |
| + `market_sim` imports | 0.116 GB |
| + year 2023 loaders | 0.240 GB |
| + year 2024 loaders | **0.240 GB** (+0.000) |

Two observations, both decisive:

1. **A second year adds nothing.** The caches are keyed by year, but a second
   year's entries cost ~0 GB — so they cannot be the mechanism by which the
   floor rises year over year.
2. **Clearing every cache frees 0.019 GB.** With 9 caches populated (14
   entries), `gc.collect()` + `malloc_trim(0)` alone took 0.240 → 0.211 GB;
   clearing all caches then took it to 0.191 GB.

Cache census after two years — note how small `currsize` is:

```
  4  market_sim.data.miso_outages.miso_outage_mw_series
  2  market_sim.data.outages.unit_outage_derate_factors
  2  market_sim.data.miso_outages.miso_native_outage_derate_factors
  1  market_sim.data.outages._iso_plant_capacity
  1  market_sim.data.miso_outages._load_estimated
  1  market_sim.data.miso_outages._miso_thermal_capacity_mw
  1  market_sim.data.chp._chp_by_plant
  1  market_sim.data.fleet.eia860._cc_demonstrated_peaks
  1  market_sim.data.fleet.eia860._egrid_boundary_hr_repairs_for
```

All 26 unbounded caches live in the outage-loader family
(`outages.py` 15, `miso_outages.py` 4, `pjm_outages.py` 2,
`neiso_operable_capacity.py` 2, `caiso_outages.py` 1, `fleet/eia860.py` 1,
`coal.py` 1). The three non-MISO ISO modules never populate in a MISO run, so
the measurement above covers the whole live set.

**The second named lever is already done.** "Release/rebuild fleet objects
between years" — the fleet is built per year inside the solve context and is
already released by the existing `del result, context, result_p1, p2_state, …`
block.

## 2. Why the hypothesis was wrong, and what the floor must therefore be

Attributing the 1.56 GB post-release resident:

| component | GB | source |
|---|---|---|
| interpreter + numpy/pandas/imports | ~0.12 | measured above |
| module `lru_cache` memoizations | ~0.02 | measured above |
| cross-year accumulator frames | ~0.07 | miso-89, existing telemetry |
| **unattributed** | **~1.35** | — |

~86 % of the floor was never accounted for by any hypothesis on record. Plausible
remaining candidates, none yet measured: HiGHS/`highspy` internal state surviving
the Python-side `del`; glibc arenas that `malloc_trim` cannot return because live
allocations are interleaved with freed ones (trim only releases *fully* free
arenas and the top of heap); and long-lived module state that is not an
`lru_cache`.

## 3. What was built instead: attribution, so the next attempt starts from a measurement

Three sessions have now proposed a memory lever from a plausible story rather
than a number. The deliverable here is to end that.

**`src/market_sim/data/cache_control.py`** (new, tested):

* `iter_cached_functions()` / `cache_report()` — census every populated
  `lru_cache` in the **already-imported** package (never imports, so asking the
  question cannot itself allocate).
* `clear_all_caches()` — kept as a diagnostic. **Deliberately NOT wired into
  the year loop**: it buys ~0.02 GB against a ~1.35 GB unattributed gap, and
  clearing a cache is only sound if every caller treats the cached value as
  read-only — a nonzero correctness risk for no meaningful benefit. Adding a
  mechanism that does not address the cause is the thing rule 1 warns about.
* `retained_footprint(*roots)` — walks the live object graph and reports the
  ndarray / pandas / scipy-sparse payload actually retained.

**Wired into the runner's release block** (`run_calibration_full.py`), so every
year now logs *what* its resident consists of, next to the existing
resident/peak line.

### Two real bugs found while validating that tool — recorded because they generalise

Both would have made the telemetry **silently under-report**, which is worse
than no telemetry (the same failure mode as an integrity guard that fails open).
Both were caught only by validating against a known-size allocation rather than
eyeballing plausible output.

1. **`gc.get_objects()` never returns a numeric ndarray.** A plain `float64`
   array is not GC-tracked, so the first implementation reported **0.000 GB**
   while 200 MB sat live. Worse, CPython leaves a *container* untracked when all
   its values are untracked, so `{"x": np.zeros(...)}` is invisible too — one
   level of `gc.get_referents()` is not enough either. Fixed by walking
   referents **transitively** from the tracked set.
2. **Running-function locals are unreachable, full stop.** CPython 3.11
   materialises a frame object only on demand, so anything held solely in a
   caller's local — which is exactly what the runner's per-year accumulator
   lists are — cannot be found from the GC graph at any traversal depth. Fixed
   by making `retained_footprint` accept explicit `*roots`; the runner passes
   its accumulators. The limitation is documented in the docstring and **pinned
   by a test** (`test_running_frame_locals_are_the_documented_blind_spot`) so it
   cannot silently become a false "we measured everything" claim.

## 4. What this does NOT claim

* **Not** a reduction in the 14.4 GB single-year peak. Nothing here touches it.
  MISO's P1 re-solves the same model in place (`_warm_p1`), so unlike the cold-P1
  path there is no second model to release at the seam; the peak is one model and
  is irreducible without shrinking the LP itself.
* **Therefore the staged one-year-per-process `--reuse-solved` recipe remains
  necessary** for MISO on this box. Unchanged from miso-89.
* **Not** a licence to enable cross-year warm start. `MARKET_SIM_WARMSTART_XYEAR`
  makes this *worse* (it retains the prior year's basis) and is deliberately off
  on the forecast path for a correctness reason — `docs/cross-year-warmstart.md`.

## 5. Next lever, and how to aim it

Run any single MISO year and read the two new telemetry lines. They will say
whether the ~1.35 GB is live Python payload (in which case
`retained_footprint`'s ndarray/pandas split names the owner) or **not** — and if
the live payload is small, the residual is allocator/HiGHS-side, which is a
different fix entirely (arena tuning via `M_ARENA_MAX`/`mallopt`, or explicitly
destroying the HiGHS model object rather than relying on Python `del`).

That is a measurement to take, not a hypothesis to argue. It costs one year of
solve time and it should be taken before any further memory work is chartered.
