# FINDING — PERF-C S2: P0 extraction slimming, and the one trim that is NOT byte-neutral

**STATUS: RESULT.** Lane shard S2 of the PERF-C program
(`docs/handoffs/PRECOMMIT-perfc-orchestration-2026-09-20.md` lever **L2**).
Pinned HEAD `2a87343f8d7302ce84e66f45430a8d3b9e807d80`; branch
`claude/perfc-s2-p0-slim`. DATA PROFILE `neiso`.

## Headline

**Three of the four proposed trims land. The fourth — skipping
`_marginal_emission_rate` on P0 — is REFUSED on measured evidence: it is
warm-start-class, not byte-identical, and the NEISO byte gate caught it.**

| # | change | verdict |
|---|---|---|
| 1 | P0 extraction slimming (`full_extract=False`) | **LANDED** — byte-identical |
| 2 | skip `_marginal_emission_rate` on P0 | **NOT LANDED** — warm-start-class, measured below |
| 3 | collapse the `row_lower`/`row_upper` concatenate chain | **LANDED** — byte-identical |
| 4 | memoize `_fleet_group_by_code` | **LANDED** — byte-identical, and worth **zero** on the solve path (§4) |

Byte gate with 1/3/4 in: **PASS at `atol = rtol = 0`** — 15 files / 53 numeric
columns, `Σ|hourly Δ| = 0.0 GWh` in every one of NEISO's six years, and all
**16** golden files identical by content hash.

**NO TIMING WORK WAS DONE.** The owner ruled there is already ample wall-clock
evidence, so this shard ran no bench and reports no seconds. The only solves it
spent are golden captures whose whole job is to prove nothing moved. Every claim
below about what a change *costs* describes work skipped, not a measured second;
where an expected win is zero, that is said rather than implied.

---

## 1. Change 1 — P0 extraction slimming (LANDED)

**What.** `DispatchModel.solve` gains `full_extract: bool = True`
(`src/market_sim/model/lp/model.py:1054`, documented `:1070-1093`).
`solve_dispatch` forwards it verbatim (`src/market_sim/model/lp/__init__.py:474`,
`:598-604`, `:730`). The P0 call site — and only the P0 call site — passes
`full_extract=False` (`src/market_sim/pipeline/solve.py:512-526`, both the warm
`model.solve` branch and the cold `solve_dispatch` branch). Every other caller is
untouched and still gets the full result, P1 included.

### The P0 consumer enumeration

By grep over `src/`, `scripts/` and `tests/` for `r0.<attr>` and `.r0`, then
reading each hit. This is **every** read of a P0 `DispatchResult` in the repo:

| consumer | file:line | attributes read |
|---|---|---|
| startup-markup coupling (`compute_monthly_markup`) | `src/market_sim/pipeline/solve.py:533` | `dispatch` |
| pass timings into `EnergySolveResult` | `src/market_sim/pipeline/solve.py:857,862` | `build_time`, `solve_time` |
| CAISO RA must-offer detector | `src/market_sim/pipeline/commitment.py:353-355,365-366` | `wind_dispatched`, `solar_dispatched`, `dispatch`, `prices` |
| ERCOT gas bridge (`_floor_for` / `_fleet_prep` / `bid_prep`) | `src/market_sim/pipeline/commitment.py:609-640` (prices via `:614`) | `dispatch`, `prices` |
| NYISO gas bridge | `src/market_sim/pipeline/commitment.py:1204-1206` | `dispatch`, `prices` |
| further bridge / floor preps | `src/market_sim/pipeline/commitment.py:1378-1380,1549-1550,1865,1883,2000,2434` | `dispatch` (`prices` at `:1380`) |
| PJM / CAISO `p1_kwargs_prep` | `src/market_sim/pipeline/commitment.py:1859,1885,1994` | `dispatch`, via the fleet prep they wrap |
| ERCOT low-curve `p1_bid_adjust_prep` | `scripts/run_calibration.py:4951-4958` | `dispatch` |
| opt-in `hourly/p0_commitment_<year>.parquet` | `scripts/run_calibration.py:6979` → `scripts/run_calibration_full.py:784-814` | `dispatch` |
| opt-in `hourly/p0_dispatch_<year>.parquet` | `scripts/run_calibration.py:6995,7000` → `scripts/run_calibration_full.py:849-908` | `dispatch`, `prices` |
| O7 attribution harness `p0_hashes` | `scripts/probes/o7_attribution_harness.py:130-159,559,571,584` | `dispatch`, `wind_dispatched`, `solar_dispatched`, `slack`, `dump`, `prices`, `storage_charge`, `storage_discharge`, `storage_soc`, `flows`, `objective_value` |
| suite assertions on `res.r0` | `tests/unit/pipeline/test_pipeline_solve.py:105,196,230-231,292`; `test_pipeline_commitment.py:641` | `dispatch`, `slack`, `build_time`, `solve_time` |

**The union is exactly the REQUIRED fields of `DispatchResult`** — the twelve
data fields plus the two timings, i.e. every field the dataclass has no default
for (`src/market_sim/model/lp/__init__.py:127-140`). That makes the slim
contract expressible in one sentence and checkable mechanically, which
`tests/unit/model/test_p0_slim_extract.py` does by reflecting over
`dataclasses.fields`.

### What is skipped

| skipped | model.py line | work avoided |
|---|---|---|
| `flow_dual`, `gen_reduced_cost` | `:1255` | the whole-`col_dual` conversion — `layout.total_columns` entries through highspy's boxed-list accessor (21,759,840 on an ERCOT keeper year, 29,643,840 on MISO), plus the retained `(n_gen, T)` float32 block |
| `balance_activity` → `reserve_shortfall_by_family`, `reserve_held_by_family` | `:1273` | the `solution.row_value` conversion (one boxed list over all rows) |
| `gen_mc` float32 copy | `:1184-1188` | an `(n_gen, T)` half-width copy; the float64 `mc` is released at the same `del` as before |
| `rps_shadow_price`, `rps_region_duals`, `clean_region_duals`, `co2_cap_price` | `:1319,1337,1350` | small `row_dual` slices and their copies |
| `reserve_dispatch`, `reserve_price`, `reserve_price_by_family`, `reserve_supply_cap_dual`, `storage_reserve_dispatch` | `:1367,1459` | the per-family membership matmul and the ORDC partition |
| `posture_*`, `lcr_dual`, `interface_dual`, `hydro_cascade_*`, `flow_cap_*`, `interface_cap_*` | `:1470,1487,1512,1524,1597-1614` | block slices and their `.copy()` |

Everything on that list is read **out of** an already-solved model, and none of
it calls back into HiGHS. No LP row, coefficient, bound or objective entry is
touched, and the `changeColsCost` → `run()` sequence is byte-for-byte what it
was — which is why the P0 (cold) solves reproduce to the iteration (§5).

**Test.** `tests/unit/model/test_p0_slim_extract.py`, 3 tests. The trivial LP
(1 gen / 1 zone / 24 h) plus a second system carrying links, storage and reserve
co-optimization, so the skipped blocks are *populated* on the full result and
their absence on the slim one is a real skip rather than an empty LP. Every
required field asserted equal (`np.array_equal`, no tolerance); every optional
field asserted `None` except the documented `marginal_emission_rate` exception,
which is asserted **equal**.

## 2. Change 2 — `_marginal_emission_rate` on P0: REFUSED, warm-start-class

**The trim looked free and is not.** Every consumer of the rate reads the **P1**
result (`src/market_sim/results/export.py`, `src/market_sim/results/outputs.py`,
`scripts/run_full_horizon.py`); nothing reads it off `r0`, and §1's enumeration
is exhaustive. The computation is expensive for a diagnostic: a `getBasis`, 18
chunked `changeColsCost` over the whole objective, a `setBasis`, a
zero-iteration `h.run()`, a `row_dual` read and a second `setBasis`.

**Why it still cannot be skipped.** On the route where P1 re-solves the *same
live model*, the routine's closing `setBasis` leaves HiGHS entering P1's warm
`run()` from a re-installed basis rather than from a live post-solve
factorization. Removing it changes P1's simplex **path**. That was flagged as a
caveat before the gate, and the gate confirmed it.

**Measured, NEISO keeper `2026-09-19-neiso112-mer-year-isolated`, six years.**
NEISO is on the warm route — its 2020 log reads `Solve: 91.953s (cold …)` then
`Solve: 41.549s (warm …)` against one matrix build — so the gate exercised
exactly the risky path.

| year | P0 cold iters (base → arm) | P1 warm iters (base → arm) | P1 objective |
|---|---|---|---|
| 2020 | 181,129 → 181,129 | 63,420 → **63,655** | 1089646965.7871 → identical |
| 2021 | 186,283 → 186,283 | 62,390 → **62,525** | 2245931340.4588 → identical |
| 2022 | 185,720 → 185,720 | 58,941 → **59,087** | 4110199256.3035 → identical |
| 2023 | 187,362 → 187,362 | 61,167 → **61,063** | 1683031832.1118 → identical |
| 2024 | 187,155 → 187,155 | 58,346 → **58,235** | 2088096478.3843 → identical |
| 2025 | 188,783 → 188,783 | 58,923 → **58,923** | 3635776821.9178 → identical |

Same optimum, different vertex. The resulting byte-gate failure:

```
FAIL  NEISO/dispatch/{2020..2025}_P1.parquet:mw  max_dev 4.03e+02 .. 5.88e+02 (abs)
FAIL  NEISO/flows.parquet:mw                     max_dev 3.058e+03 (abs)
FAIL  NEISO/storage.parquet:{charge,discharge,soc}  max_dev 7.6e+02 .. 1.56e+03 (abs)
FAIL  NEISO/system.parquet:dump                  max_dev 1.381e+03 (abs)
FAIL  NEISO/system.parquet:price                  max_dev 6.375e-16 (rel)
FAIL  NEISO/system.parquet:reserve_price          max_dev 1.000e+00 (rel)
FAIL  NEISO/system.parquet:marginal_emission_rate max_dev 2.220e-16 (abs)
reshuffle: Σ|hourly Δ| 78.9 - 130.5 GWh = 0.081 % - 0.132 % of annual gen, Δ net +0.0000 GWh
```

That is the textbook marginal-tie reshuffle — total generation identical to four
decimals, `system.price` moving only at float epsilon, but per-unit dispatch,
flows and storage rearranged across ties, and one hour's `reserve_price` moving
by its whole value.

**Disposition.** The call stays **unconditional** (`model.py:1551-1571`), with
the measurement recorded at the call site so a later reader cannot mistake it
for an oversight; `tests/unit/model/test_p0_slim_extract.py` pins
`marginal_emission_rate` as an explicit exception to the skip set, so a
"tidy-up" that folds it in re-breaks this gate loudly instead of silently.

**For a successor.** This trim is available to a lane holding a
warm-start-class mandate and validating with
`scripts/diagnostics/diff_warmstart_bundles.py` rather than `--mode byte` — the
same standing the `MARKET_SIM_P1_FLOOR_INPLACE` path has
(`src/market_sim/pipeline/solve.py:583-597`). It is **not** available under a
byte-identity mandate, and rule 36 `[R-YEAR-ISOLATION]` (e) is the cautionary
precedent: two solve-path knobs were carried for a year on a documented
basis-neutrality claim that measurement later falsified. This one was measured
before landing, not after.

An alternative that would be byte-neutral and was **not** attempted here
(no timing work, and it is a design change rather than a trim): compute the rate
**once**, on P1 only, by gating it on something the pass knows about itself
rather than on `full_extract`. That still leaves the skip's effect on the P0→P1
warm state, so it needs the same warm-start mandate. There is no version of this
trim that is free on the warm route.

## 3. Change 3 — collapse the bound-vector concatenate chain (LANDED)

**What.** `src/market_sim/model/lp/rows.py:1596-1627` introduces `lower_parts` /
`upper_parts` / `n_rows_built` and a nested `_add_bounds(lo, hi)`. The 19
`row_lower = np.concatenate([row_lower, X])` / `row_upper = …` pairs between
`:1723` and `:2218` each become one `_add_bounds(X, Y)`; the two seeds (`:1631`
no-storage, `:1706-1708` with-storage) become `_add_bounds` calls; the three
mid-assembly `row_lower.size` reads become `n_rows_built` (`:1786` interface
offset, `:1825` LCR offset, `:1939` the hydro-cascade `row_offsets` entry); and
both return sites (`:2184-2185`, `:2222-2223`) join each list once with
`np.concatenate`.

**Why it is byte-identical.** A pure re-association: the same pieces, in the
same order, into one `np.concatenate`. `_add_bounds` applies
`np.asarray(..., dtype=float)` to each piece, reproducing the promotion the
pairwise chain performed against its float64 accumulator and a no-op (no copy)
for the float64 arrays every block builder returns. The one non-array piece —
the single ISO-wide RPS row's `[rhs]` / `[np.inf]` at `:2088` — goes through the
same `asarray`. Both returned vectors are freshly allocated by the final
`concatenate`, so they stay distinct objects aliasing neither each other nor
`eb_rhs`, exactly as the old `eb_rhs.copy()` / `row_lower.copy()` guaranteed.

What it avoids: the chain re-copied the whole accumulated vector once per row
family — ~20 copies of a vector reaching 1,026,876 entries on a plant-level MISO
year; quadratic work for a linear result. It is matrix-build-side, so on the
PRECOMMIT's own phase table it lives inside the 10-15 % Python share and is
small in absolute terms. The strongest evidence it is exact is §5's cold-solve
column: a bound vector off by one entry would change the LP, and all six cold
P0 solves reproduce to the iteration.

**Test.** `tests/unit/model/test_row_bounds_assembly.py`, 4 tests: the trivial
system's bounds are the energy-balance RHS with no aliasing; a
storage + interface system's three families land at their own rows with the
reported `iface_row_offset` indexing the band rows (this is what catches the
counter drifting from the parts list); the row count tracks the matrix as
families are added; the matrix is still one CSR of the right shape.

## 4. Change 4 — memoize `_fleet_group_by_code` (LANDED, and worth nothing here)

**What.** `scripts/run_calibration_full.py:2168-2175` adds
`_FLEET_GROUP_BY_CODE_MEMO`, keyed `(iso, id(iso_config), year)` — the full
argument tuple — with the `iso_config` held by a strong reference in the value
so its `id()` cannot be recycled onto a different object. `:2187-2210` serves a
hit and records a miss. A **fresh dict** is returned on every call, hit or miss,
so a caller mutating the result reaches neither the memo nor a later year.

`memoized_mapping` was considered and rejected: it is content-addressed on an
explicit `sources` list, and enumerating everything `load_fleet_from_csv` reads
for a given vintage is a larger and more fragile surface than this derivation
warrants.

**Its measured worth on the solve path is ZERO, and that is worth saying
plainly.** `_fleet_group_by_code` has exactly two call sites —
`scripts/run_calibration_full.py:6333` in the year loop, and `:9658` inside
`rebuild_benchmark`, which is a separate `--rebuild-benchmark` CLI mode. In a
normal solve each is reached **once per year**, with a distinct `year`, so every
call is a miss and no fleet load is saved. The change is correct and
behaviour-preserving, and it makes a repeat call free if one ever arrives — but
it is not a wall-clock win as the code is wired today. **The parent should feel
free to drop it** rather than carry a memo that never hits (rule 26
`[R-DELETE]`'s spirit); it is reported here as a no-op, not as a saving.

**Test.** `tests/unit/scripts/test_fleet_group_by_code_memo.py`, 5 tests with
`load_fleet_from_csv` stubbed so the load count is observable: `dict == dict` on
one ISO-year with a single load; a hit returns a fresh dict that survives caller
mutation; and the key discriminates on each of ISO, config identity and year.

## 5. Byte gate

```
python scripts/capture_keeper_goldens.py --iso NEISO --stage-tag perfc-s2-before  # pristine HEAD, before any edit
python scripts/capture_keeper_goldens.py --iso NEISO --stage-tag perfc-s2-after   # changes 1/3/4
python scripts/regression_gate.py --before results/regression-goldens/perfc-s2-before \
                                  --after  results/regression-goldens/perfc-s2-after --mode byte
```

Keeper `2026-09-19-neiso112-mer-year-isolated`, **all six years 2020-2025**,
8760 h, 300 recorded flags. Both captures reported `fidelity OK: 308 recorded
flags replayed identically … scenario_config 856 matched, 0 drifted`. (Both
manifests stamp `git_dirty: true`; the before capture was launched as this
shard's first action after the HEAD check and before any `Edit`, and its
dirtiness is the untracked golden output tree itself.)

**`[1] golden-diff: PASS` — 15 files, 53 numeric columns, `atol = rtol = 0`.**
`[2]` reports `Σ|hourly Δ| = 0.0 GWh = 0.000 %` and `Δ net +0.0000 GWh` in every
one of the six years. Independently, comparing the two manifests' content
hashes: **16 files compared, 16 identical, 0 differing** — a stronger statement
than the gate's column-wise numeric check.

`[3] smoke: PASS` (36 tests).

`[4]` reports two FAILs — `legitimacy(--keepers)` and `audit_keepers` — and
**both reproduce at clean HEAD**, verified by stashing this shard's five source
edits and re-running: `legitimacy rc=1`, `audit_keepers rc=1`. They are not this
shard's to fix (rule 32 `[R-SHARD]`: "a shard that repairs infrastructure is a
FAILURE"):

- `legitimacy(--keepers)`: `ValueError: nyiso_li_lcr_tsl=True but no published
  Long Island transfer_security_limit for delivery year 2022/2023 …
  available areas: []` — a NYISO capacity-deliverability table gap, raised on a
  data read before any LP. **Owed to the NYISO lane.**
- `audit_keepers`: `E13: 2026-09-20-soco53g-prb-own-iso is registered for SOCO
  but not the keeper and stamped to no keeper — a superseded run left behind a
  promotion` (plus warnings: SOCO E11, MISO E3). **Owed to the SOCO lane** under
  rule 35 `[R-PROMOTE]` (a).

### Coverage gap — state this before relying on the result

NEISO is on the **warm** P1 route, which is why it was the right ISO for change
2's caveat and why the gate caught it. What it does **not** cover is the **cold**
P1 route, where a second `DispatchModel` is built on a floored fleet and solved
cold (`src/market_sim/pipeline/solve.py:781`). **ERCOT, NYISO and CAISO take
that route** via their `p1_fleet_prep` bridges. For the three landed changes
that is a formality — change 1 only chooses which blocks are marshalled out of
an already-solved model and never calls into HiGHS, change 3 assembles the same
bound vectors matrix-build-side, and change 4 is off the solve path entirely —
but "formality" is an argument, not a measurement, and **no ERCOT / NYISO /
CAISO / MISO / PJM golden was captured here.** Changes 1 and 3 have their
largest effect precisely on the per-plant multi-zone ISOs, and nothing there was
measured. A lane touching one of those ISOs should run its own before/after byte
gate rather than inherit this PASS.

Container: `cgroup_peak_rss_gib=8.92`, `process_vmhwm_gib=4.94`, no swap used.
Preflight warned `ceiling+swap 19.4 GiB is below the 24 GiB target` — fine for
NEISO, noted because a per-plant ISO would care.

## 6. Tests run

| suite | result |
|---|---|
| `tests/unit/model/test_p0_slim_extract.py` | 3 passed |
| `tests/unit/model/test_row_bounds_assembly.py` | 4 passed |
| `tests/unit/scripts/test_fleet_group_by_code_memo.py` | 5 passed |
| `tests/unit/model/test_marginal_emission_rate.py` | passed (14 + 2 subtests) |
| `tests/unit/model` (whole dir) | passed |
| `tests/unit/pipeline` (whole dir) | 284 passed, 61 subtests, **2 failed — pre-existing** |
| `tests/regression/test_regression_smoke.py` | 36 passed |

The two `tests/unit/pipeline` failures —
`test_xyear_warmstart_default.py::TestResolveDefault::test_default_on_when_unset`
and `::TestResolveP1BasisSeedDefault::test_default_on_when_unset` — assert that
`resolve_xyear_warmstart_default` / `resolve_p1_basis_seed_default`
(`scripts/run_calibration.py:7684` and sibling) return `True` when the env var
is unset. CLAUDE.md rule 36 `[R-YEAR-ISOLATION]` (d), landed 2026-09-19 (the day
before this pin), flipped **both** defaults OFF, and the resolvers' own
docstrings say so; the tests were not updated with them. **Verified to fail at
clean HEAD** by the same stash check as §5, and neither
`scripts/run_calibration.py` nor that test file is in this shard's diff. Owed to
whichever lane owns rule 36's execution, not to PERF-C.

## 7. Files changed

| file | what |
|---|---|
| `src/market_sim/model/lp/model.py` | `full_extract` param + docstring (`:1054`, `:1070-1093`); `gen_mc` gate (`:1184-1188`); extraction gates (`:1255`, `:1273`, `:1319`, `:1337`, `:1350`, `:1367`, `:1459`, `:1470`, `:1487`, `:1512`, `:1524`, `:1597-1614`); MER refusal note (`:1551-1571`) |
| `src/market_sim/model/lp/__init__.py` | `solve_dispatch` forwards `full_extract` (`:474`, `:598-604`, `:730`) |
| `src/market_sim/pipeline/solve.py` | the P0 call site passes `full_extract=False`, both branches (`:512-526`) |
| `src/market_sim/model/lp/rows.py` | bound-vector collect-once (`:1596-1627` helper; 19 pair rewrites `:1723-2218`; seeds `:1631`, `:1706-1708`; offsets `:1786`, `:1825`, `:1939`; returns `:2184-2185`, `:2222-2223`) |
| `scripts/run_calibration_full.py` | `_fleet_group_by_code` memo (`:2168-2210`) |
| `tests/unit/model/test_p0_slim_extract.py` | NEW, 3 tests |
| `tests/unit/model/test_row_bounds_assembly.py` | NEW, 4 tests |
| `tests/unit/scripts/test_fleet_group_by_code_memo.py` | NEW, 5 tests |
| `results/regression-goldens/perfc-s2-{before,after}/manifest.json` | the hashes-only gate record (repo convention; the bundles are gitignored) |

## 8. Retrievability (rule 34 `[R-SHARD-PROMOTABLE]` (e))

Nothing here is a registrable run: this shard produced **no calibration bundle
for promotion**, only golden captures whose sole purpose is §5's equality and
whose every cited number is in this document. The deliverable is the code, the
tests and this doc, all committed on `claude/perfc-s2-p0-slim` and nothing else
to strand.

One housekeeping note for the record: the first `perfc-s2-after` capture — the
one that FAILED with change 2 armed — was removed to make room for the re-run
(the container had 5.8 GiB free and each capture is 223 MB). Its every cited
number is in §2, and it reproduces exactly by re-arming the gate at
`model.py:1571`. It was a throwaway bench artifact, never a promotable result.
