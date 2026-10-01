# FINDING — PERF-C S6: a content-addressed cache of the cold P0 solve

**STATUS: RESULT.** Lane shard S6 of the PERF-C program
(`docs/handoffs/PRECOMMIT-perfc-orchestration-2026-09-20.md`). Pinned HEAD
`5cb658922895862852eb58edb4afb8774f5ef7ce` (the composed PERF-C lane, carrying
the S1 seed un-nesting and the S2 slim P0 extraction); branch
`claude/perfc-s6-p0-cache`. DATA PROFILE `neiso`.

**NO TIMING WORK.** The only solves this shard spent are the three NEISO golden
captures of §4, whose job is to prove what did and did not move. The two numbers
it measures deliberately — the digest cost (§5) and the entry size (§6) — are
costs the change *adds*, and it would be dishonest to ship them unquantified.
Wall-clock seconds appear in §4 only because the capture logs print them; no
bench was run and no speed claim rests on them.

---

## Headline

**The cache works and reproduces the P0 solve exactly. It ships DEFAULT OFF,
because reproducing the P0 *answer* is not the same as reproducing the internal
state the *next* pass starts from — and on the route where P1 re-solves the same
live model, the difference moves P1's vertex.**

| capture | verdict |
|---|---|
| (a) before — pinned HEAD, pre-edit code | baseline, fidelity OK (308 recorded flags replayed identically) |
| **(b) miss** — cache armed, empty dir, every year a MISS | **byte gate PASS** at `atol = rtol = 0`, 15 files / 53 numeric columns, `Σ\|hourly Δ\| = 0.0 GWh` in all six years |
| **(c) hit** — cache armed, immediate re-run, every year a HIT at **0 simplex iterations** | **byte gate FAIL** — P1 tie reshuffle 0.079–0.131 % of annual generation, Δ net +0.0000 GWh |

So the added code path is byte-neutral when it misses (b), and the P0 replay is
exact — 0 iterations, objective identical to every printed digit in all six
years — but the *pass* is not reproduced (c). **This is the identical failure
mode, with an almost identical measurement, to the one PERF-C S2 refused**
(`FINDING-perfc-s2-p0-slim-2026-09-20.md` §2), and it gets the identical
disposition: default OFF, measured, available to a lane holding a
warm-start-class mandate.

**Tier A shipped, and Tier B is ruled out rather than deferred** — see §3.

---

## 1. What it is

80–96 % of a calibration year is inside `h.run()`, and the **P0** pass — 80 s on
NEISO, 300–640 s on ERCOT / CAISO / MISO / PJM — is re-solved from cold on every
replay, every re-gate, every touchpoint, and on every knob iteration whose knob
only enters P1. This shard makes that pass replayable from disk.

**The key is the LP itself**, a blake2b digest over the exact bytes handed to
HiGHS:

| component | where it is taken | why it is in the key |
|---|---|---|
| CSR `starts` / `indices` / `values` | `DispatchModel.__init__`, immediately after `addRows` | the constraint matrix |
| `col_lower` / `col_upper` / `row_lower` / `row_upper` | same, **after** the `kHighsInf` substitution | the bounds HiGHS holds, not the pre-substitution ones |
| `layout.total_columns`, `n_rows`, `T`, nnz | same | shape; a cheap collision guard |
| `unit_ids`, in column order | same | two fleets can share a shape, and every extraction slices the generation block positionally |
| the cost vector | `solve()`, after `build_cost_vector`, before `changeColsCost` releases it | the objective |
| `highspy` version **and git hash** | `solve()` | a solver change is a different search |
| `presolve`, `simplex_scale_strategy`, `simplex_strategy`, `solver`, `threads`, `random_seed` | read back **out of** HiGHS, not reconstructed | an option set anywhere in the process is still in the key |
| `MARKET_SIM_HIGHS_THREADS` | `solve()` | the determinism pin, recorded as well as required |

Arrays are hashed through the buffer protocol, so the digest allocates nothing
at the build peak — no `tobytes()` copy, which at ~86 M nonzeros would be a
gigabyte of transient at exactly the wrong moment (miso-253).

**How it differs from `pipeline/basis_cache.py` (H2).** That module persists a
basis keyed on `(iso, year, T)` to *warm-start* a later solve: approximate key,
path-only guarantee, default-OFF since rule 36. Reused here: the npz conventions
(int8 status vectors, `allow_pickle=False`, a gitignored dir behind a
`config/paths.py` constant, delete-and-recapture on any bad read). Not reused:
the key.

## 2. The gate — four clauses, each load-bearing

Served **and** written only for the first solve on a freshly built model that
had no basis pre-installed:

1. **`_lp_structure_digest is not None`** — the digest was taken (switch and pin
   on at build time).
2. **`p0_cache_enabled()`**, re-read at solve time — so the switch can be
   flipped between build and solve and be obeyed.
3. **`_n_solves == 0`.** The digest describes the model **as built**, and
   `model/lp/inplace_floor.py` mutates column bounds on the live model between
   P0 and P1 (`changeColsBounds`). A digest taken at `__init__` would be *stale*
   for that second solve, and a stale digest is the one way a content-addressed
   key could lie. Closed by construction, not by care.
4. **`not _basis_preinstalled`** — set by `apply_cross_year_basis`. A
   pre-installed basis means a warm-start-class route (the cross-year warm
   start, the same-year P1 seed of S1). The cache stays out of it in **both**
   directions: it must not serve the cold vertex into a route that asked for a
   warm one, and it must not record a warm route's vertex as the cold answer.

Clauses 3 and 4 are symmetric between read and write, which states the intended
invariant in one sentence: *the cache replaces a cold first solve with the
answer a cold first solve produced.* §4 is the measurement of how far that
sentence actually reaches.

## 3. Tier A shipped — and Tier B is ruled out, not deferred

**Tier A** (basis + provenance only) is what ships. The brief's Tier-B fallback
was to store `col_value` / `row_dual` / `col_dual` / `row_value` and populate
the `DispatchResult` from them if a zero-iteration re-run differed from the cold
solve at float epsilon. **That is not the failure that occurred, so Tier B would
not have fixed it.** The measurement is unambiguous:

* the replayed P0 reports the cold solve's objective **to every printed digit**
  in all six years, at **0 simplex iterations**;
* the failing files in capture (c) are *all* P1 outputs — `dispatch/<year>_P1`,
  `flows`, `storage`, `system`. Nothing the P0 result carries is wrong.

What moves is **HiGHS's internal state after the P0 pass**: installing an
optimal basis and verifying it in zero iterations is not the same factorization
history as *searching* to that basis over 181,129 iterations, and P1 — on the
route where it re-solves the same live model — starts from that state. No stored
P0 *output* can restore it, because it is not an output. Tier B would have added
~200–400 MB per entry on ERCOT / MISO to fix a result that was already exact,
and left the actual defect untouched. It is therefore not implemented and its
serialization is **not carried as dead code**: `CachedSolve` holds the basis and
the two provenance scalars and nothing else, with the reasoning recorded in its
own docstring so a successor does not re-derive it.

## 4. Byte gate — three NEISO captures, then (b) and (c) re-run on the shipped bytes

Five captures in all. The first three (`perfc-s6-before` / `-miss` / `-hit`)
established the verdicts; two late edits then changed the shipped code — the
switch default flipped to OFF, and the stored iteration count was fixed to be
the value read right after `h.run()` rather than re-read after
`_marginal_emission_rate`'s deliberate zero-iteration re-solve, which had been
recording every cold solve as having spent 0 iterations. Neither can reach a
parquet, but a byte-identity mandate should gate the bytes that ship, so (b) and
(c) were **re-run against the final code** (`perfc-s6-miss2` / `-hit2`, cache
armed explicitly). **Both verdicts reproduced exactly** — the miss gate PASS with
`Σ|hourly Δ| = 0.0 GWh` in all six years, the hit gate FAIL with every
`max_dev` and every reshuffle percentage identical to the digit. The tables
below are the final captures; the provenance fix is visible in them, since the
hit log now reports the true cold-solve counts (181,129 … 188,783) instead of 0,
which is itself an independent confirmation that the stored entries came from
the reference cold solves.

NEISO was the right ISO precisely because it is on the risky route: its logs
read `Solve: 81.240s (cold …)` then `Solve: 34.301s (warm …)` against one matrix
build, so P1 re-solves the live P0 model — the case S2 §2 identified.

### (a) before — pinned HEAD, pre-edit code

`capture_keeper_goldens.py --iso NEISO --stage-tag perfc-s6-before`, run before
any edit; the log carries no `p0-cache:` line, confirming it is a clean
pre-change baseline. Fidelity oracle: *308 recorded flags replayed identically,
scenario_config 856 matched, 0 drifted.*

### (b) miss — armed, empty cache: **PASS**

Every year logged `p0-cache: MISS … — solving cold and storing the result`, and
every cold P0 reproduced the baseline **to the iteration**:

| year | cold P0 iterations, before → miss | P1 warm iterations, before → miss |
|---|---|---|
| 2020 | 181,129 → **181,129** | 63,420 → **63,420** |
| 2021 | 186,283 → **186,283** | 62,390 → **62,390** |
| 2022 | 185,720 → **185,720** | 58,941 → **58,941** |
| 2023 | 187,362 → **187,362** | 61,167 → **61,167** |
| 2024 | 187,155 → **187,155** | 58,346 → **58,346** |
| 2025 | 188,783 → **188,783** | 58,923 → **58,923** |

```
regression_gate.py --mode byte (atol=0.0, rtol=0.0)
PASS  NEISO: 15 files, 53 numeric columns within tolerance
Σ|hourly Δ| (gross reshuffle): 0.0 GWh = 0.000% of total gen, all six years
RESULT: PASS
```

This is the strongest available statement that the *code* is neutral: with the
cache fully armed and doing all of its work except serving, nothing moved. It is
also, a fortiori, the neutrality proof for the shipped default-OFF posture,
where the digest is not even computed.

### (c) hit — armed, immediate re-run: **FAIL**

Every year logged a HIT and solved P0 in **0 simplex iterations**, with the
objective identical to every printed digit:

| year | P0 iterations, before → hit | P0 objective | P1 warm iterations, before → hit |
|---|---|---|---|
| 2020 | 181,129 → **0** | 1066347688.7028 → identical | 63,420 → **63,493** |
| 2021 | 186,283 → **0** | 2211214720.4222 → identical | 62,390 → **62,469** |
| 2022 | 185,720 → **0** | 4070285229.4145 → identical | 58,941 → **58,892** |
| 2023 | 187,362 → **0** | 1661659681.4185 → identical | 61,167 → **61,115** |
| 2024 | 187,155 → **0** | 2067532816.8772 → identical | 58,346 → **58,408** |
| 2025 | 188,783 → **0** | 3605501177.4038 → identical | 58,923 → **58,836** |

P1's objective was also identical in all six years (e.g. 2020
1089646965.7871). The gate:

```
FAIL  NEISO/dispatch/{2020..2025}_P1.parquet:mw   max_dev 4.24e+02 .. 6.14e+02 (abs)
FAIL  NEISO/flows.parquet:mw                      max_dev 3.214e+03 (abs)
FAIL  NEISO/storage.parquet:{charge,discharge,soc} max_dev 6.9e+02 .. 1.448e+03 (abs)
FAIL  NEISO/system.parquet:dump                   max_dev 1.381e+03 (abs)
FAIL  NEISO/system.parquet:price                  max_dev 6.375e-16 (rel)
FAIL  NEISO/system.parquet:reserve_price          max_dev 1.000e+00 (rel)
FAIL  NEISO/system.parquet:marginal_emission_rate max_dev 2.220e-16 (abs)
reshuffle: Σ|hourly Δ| 79.1 - 129.0 GWh = 0.079 % - 0.131 % of annual gen,
           Δ net +0.0000 GWh in every year
RESULT: FAIL
```

**Compare S2 §2's table, which is the same phenomenon from the other side:**
`system.price` 6.375e-16 rel and `marginal_emission_rate` 2.220e-16 abs are the
*same numbers*; the reshuffle band there was 0.081 %–0.132 % against 0.079 %–0.131 %
here. Total generation identical to four decimals, `reserve_price` moving by its
whole value in one hour. Same optimum, different vertex — a byte gate refuses
it, and should.

### What the two captures prove together

* The cache **never returns a wrong P0**: the key is the LP, and the replayed
  objective is exact at zero iterations.
* The cache **does** perturb the pass on the live-model P1 route, because a
  replayed basis is not a searched basis as far as HiGHS's factorization is
  concerned.
* Those are not in tension. The brief's admissibility premise — *"a hit is exact
  by construction"* — is true of the solve it replays and false of the one that
  follows it on that route, and **the default follows the weaker of the two.**

## 5. What the digest costs

Paid on every armed solve, so it is stated as a number rather than waved at.

* **Measured, NEISO keeper LP: 0.528–0.610 s** across twelve builds in two
  captures (final capture: 0.544 / 0.535 / 0.528 / 0.579 / 0.537 / 0.555 s),
  logged at `p0-cache: structure digest <…> in <s>`.
* **blake2b throughput on this container: 571 MiB/s** (measured directly: 256 MiB
  in 0.440 s, 1024 MiB in 1.792 s).

Extrapolating from that throughput rather than claiming an unmeasured solve — the
structural digest on the plant-level **MISO 2023** LP (1,026,876 rows ×
29,643,840 columns, 86 M nnz) hashes ≈ 1.49 GiB: `starts` 4 MB + `indices`
344 MB + `values` 688 MB + column bounds 474 MB + row bounds 16 MB, i.e.
**≈ 2.6 s once per build**. The per-solve cost-vector digest is
29,643,840 × 8 B = 237 MB, **≈ 0.41 s per pass**. Against a MISO year's 320 s P0
that is ~0.9 %; it is not free, and it is why the digest is skipped entirely
when the switch is off.

## 6. Entry size and retention

**7.70–7.88 MB per NEISO year** (six entries, 46 MB total), uncompressed npz
holding the two int8 status vectors plus scalars. Uncompressed deliberately: a
hit must stay cheap, and decompressing on the read path would spend the win.
Scaling by column+row count, an ERCOT keeper year (21.8 M columns) is ~22 MB and
a MISO year (29.6 M) ~30 MB — the ~25 MB the brief predicted for Tier A.

Retention, enforced after every store: **3 entries per LP structure**, **12
structure directories**, **6 GiB total**, evicting oldest mtime first; a load
touches its file so the order reflects use, not just capture.

**Deviation from the brief, with its reason.** The brief specified
`<dir>/<iso>/<key>.npz` and "at most 3 entries per ISO". `DispatchModel` has no
ISO — threading one through `solve_dispatch` and every call site is exactly the
infrastructure edit a shard must not make — so the bucket is the **structural
digest** instead. That is per-ISO-year rather than per-ISO, which is strictly
finer (an ISO's six years are six buckets, so a span replay does not evict
itself), and the disk protection the brief was after is carried by the byte
budget, which is the term that actually binds for large entries.

## 7. Scope — which workflows this could serve, and which it never will

Stated for the successor, since nothing is armed today.

**Would hit.** Any re-run of an identical LP: a keeper replay or golden capture
at the same HEAD, a re-gate that re-solves, a held-out-year touchpoint replaying
a frozen recipe, and every **P1-only knob iteration** — the startup markup, the
ERCOT SWCAP clip, the P1-only offer surfaces, the bid-max seam — whose P0 LP is
byte-identical.

**Never hits**, because the LP is the key: any change to `mc_base`, **the
`offer_curve_by_group` band multipliers included** (the authorized price-tuning
channel of rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]` — a band-multiplier sweep
re-solves P0 in full, every arm); the fleet, outages, demand, renewable CF or
capacity, the network, the reserve specification, any floor that lands as a
bound; and any HiGHS version, option or thread change, or any edit to the matrix
builders.

The split is worth stating plainly: the cache pays for **re-execution**, never
for **search**. A lane exploring offer curves gets nothing from it.

**Inert** whenever `MARKET_SIM_HIGHS_THREADS` is not pinned to `1` — multi-threaded
dual simplex is not bit-reproducible, so a solution captured under it is not a
value another process may be handed. CI never reads or writes the cache, since a
bare `pytest` run sets no pin.

## 8. Rule 24 `[R-REGISTRY]`, stated rather than finessed

The switch was designed as a pure performance knob and **the measurement says it
is not one**: armed, on the live-model P1 route, it moves the reported vertex.
So it is not filed as neutral. Rule 36 `[R-YEAR-ISOLATION]` (e) is the standing
precedent — two solve-path env knobs carried for a year on a basis-neutrality
claim measurement later falsified — and the difference here is only that the
measurement came *before* the landing rather than a year after. A lane that arms
this owes the declaration; a lane that wants it on by default owes rule 36(e)'s
remedy, which is to promote it to `ScenarioConfig` plus the cache key, or to
delete it (rule 26 `[R-DELETE]`: deleted, not zeroed).

No `ScenarioConfig` field is added, so the rule 28 `[R-MECH-MATRIX]` duty (c)
does not bind; `check_mechanism_matrix.py` passes (the three warnings it prints
are pre-existing CAISO/PJM keeper-stamp drift, untouched by this shard).

## 9. For a successor — what would actually make this byte-identical

Two routes, neither attempted here, both named honestly:

1. **Arm it only where P1 cold-rebuilds.** On the cold-P1 route, P1 builds a
   fresh `DispatchModel`, so the P0 model's internal state is irrelevant and a
   P0 hit should be byte-identical end to end. The obstacle is that
   `run_energy_solve` does not know at P0 time whether P1 will rebuild — the
   decision depends on `p1_fleet_prep`, which reads `r0`. A conservative
   predicate (`MARKET_SIM_WARMSTART=0`, or a caller that guarantees a rebuild)
   would fire on a subset. **It cannot be validated on NEISO**, which is the
   warm route by construction, so it needs an ISO whose P1 cold-rebuilds and
   should not be claimed until it has one.
2. **Cache the pass, not the solve.** Storing P0 *and* P1 together makes a full
   replay exact. It does not rescue the headline workflow, though: a P1-only
   knob iteration misses on P1 by definition, and a P0 hit with a P1 miss is
   precisely the broken case measured in §4(c). A genuine pass-level cache would
   have to key on the prep hooks, which are Python callables and not
   content-addressable — which is why the brief scoped this to the LP.

The warm-start-class validator for either is
`scripts/diagnostics/diff_warmstart_bundles.py`, not `--mode byte`; that is the
standing `MARKET_SIM_P1_FLOOR_INPLACE` already has (`pipeline/solve.py`).

## 10. Tests

`tests/unit/model/test_p0_cache.py`, **23 tests**, on the trivial 1-zone LP and
a 2-zone + link + storage system so the round-tripped basis has column families
beyond the generation block:

* the structure digest is stable, and **moves for every one of its eleven
  inputs** — each CSR array, each bound vector, the counts, the horizon, and the
  `unit_ids` (including a pure reordering, since column order is identity);
* the solve key moves with the cost vector, the HiGHS version string, the thread
  pin and the structure;
* a miss writes one entry, a hit reads it, and the hit's `DispatchResult` equals
  the miss's **field for field with no tolerance** (`np.array_equal`) — the
  single-process statement of §3's "the P0 result is exact";
* a different cost vector is a different entry; a second `solve` on a live model
  never touches the cache; a pre-installed basis makes it inert both ways;
* the switch **defaults off** and only an explicit truthy value arms it; an
  unpinned thread count is refused; both inert paths still solve to `Optimal`;
* eviction keeps three per structure, oldest first; store/load round-trips; a
  corrupt, wrong-shaped or schema-mismatched file self-evicts.

Full runs at HEAD: `tests/unit/model` + `tests/unit/pipeline` **1810 passed, 1
xfailed, 124 subtests**; `tests/regression/test_regression_smoke.py` **36
passed**.

**One trap worth recording, because it cost this shard a debugging cycle and is
already documented as a program-wide hazard.** The fixture originally set
`MARKET_SIM_HIGHS_THREADS=1`. Every solving test then passed *alone* and failed
the moment any other model test ran first, with `model status 'Not Set'`: HiGHS
initializes a process-global scheduler on the first `run()` and refuses every
later LP whose `threads` option differs from it. That is exactly the latent,
ordering-dependent CI red recorded in
`docs/FINDING-fast-tier-repair-2026-09.md` §4b/§7.6 and guarded at source by
`capture_keeper_goldens.pin_determinism_env`. **Never set that variable inside a
pytest process that will later solve.** The fixture now patches the
`determinism_pin_ok` *predicate* instead, and the predicate itself is tested in
tests that never solve.

## 11. Files changed

| file | what |
|---|---|
| `src/market_sim/model/lp/p0_cache.py` | **new**, 585 lines — key, entry, store/load, eviction, the process-level provenance record |
| `src/market_sim/model/lp/model.py` | `__init__` digest (`:705-744`); the solve-time gate, hit and provenance (`:1247-1329`); `_highs_option_signature` (`:1810`) + `_store_p0_cache_entry` (`:1852`); `_basis_preinstalled` set in `apply_cross_year_basis` (`:2085`); the `solve()` docstring and the one solve log line |
| `src/market_sim/pipeline/solve.py` | `EnergySolveResult.p0_cache` + its docstring; `reset_last_solve()` before P0; provenance read after P0; the `_PASS_TIMING_LOG` entry |
| `src/market_sim/config/paths.py` | `P0_CACHE_DIR = RESULTS_ROOT / "p0-cache"` |
| `.gitignore` | `/results/p0-cache/` |
| `tests/unit/model/test_p0_cache.py` | **new**, 424 lines, 23 tests |

No LP row, coefficient, bound or objective entry is touched anywhere, which is
what capture (b) measures rather than asserts.
