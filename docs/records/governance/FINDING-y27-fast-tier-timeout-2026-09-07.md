# FINDING — Y-27: the `Fast test tier` timeout is `census()` on a foreign checkout

**Lane:** Y-27, Model Audit & Release-Finalization Program (CI plumbing).
**Pin:** `origin/main` @ `60f244e3` (2026-09-07 ~18:10Z); CI-shaped repro clone at
`ad78cc3`. Every number below was re-derived in this session; nothing is
transcribed from the handoff.
**Verdict:** shape **(a)** — the suite genuinely got ~570 s slower, deterministically,
on any checkout that is not the one the committed runs were solved in. It is **not**
a hang and it is not an infrastructure regression.
**Headline:** PR #5556 is exonerated. The cause is **PR #5557** (capx D85-R), and inside
it the single object is `scripts/lib/key_provenance.py::classify` reached through the
module-scoped `census()` fixture of `tests/regression/test_key_provenance_exceptions.py`.

---

## §1 The timeout reading, per job

`Fast test tier` (`ci.yml`, `timeout-minutes: 20`) no longer concludes: the
`Fast pytest tier` step is cancelled and the job reports `cancelled`.

| run | head | ancestor of `origin/main` | job | `Fast pytest tier` | job total | conclusion |
|---|---|---|---|---|---|---|
| 34144853473 | `44ac71ba` | YES | 101814540659 | 16:49:11 → 16:58:57 = **9m46s** | 11m35s | `failure` (6 real test failures) |
| 34144876665 | `7b7b758c` | YES | 101814613960 | 16:49:41 → 17:07:59 = **18m18s** | 20m19s | **`cancelled`** |
| 34148206271 | `63acb08d` | YES | 101824690811 | 17:36:49 → 17:55:18 = **18m29s** | 20m14s | **`cancelled`** |

Ancestry checked with `git merge-base --is-ancestor <sha> origin/main` for all three
(plus `5be38f3d`, `64680615`) — all YES.

Across the 20 completed `ci.yml` runs created at/after 2026-09-07T16:47:43Z, total run
duration is **20.30–20.37 min** on 12 distinct lane branches. Every other required check
on those runs is `success`; the only `failure` is FR-22 (NON-SET, not this lane's).

The other jobs in the same runs are **unchanged**, which rules out a runner-hardware or
runner-image regression: `audit_keepers --check` 28 s (baseline) vs 29 s (long run);
`check_registry_payload_parity` 9 s vs 10 s; `actions/checkout` 94 s vs 94 s; runner
image `ubuntu-24.04 / 20260831.293.1`, agent `20260828.587` in both.

## §2 The boundary, re-derived — and why it is **#5557**, not #5556

Last short run created **2026-09-07T16:47:23Z** (`44ac71ba`, 11.62 min).
First long run created **2026-09-07T16:47:43Z** (`7b7b758c`, 20.35 min). Runs from
2026-09-07T05:13Z through 16:47:23Z are 7.9–12.5 min with zero long runs.

`git log origin/main --first-parent` in the 20-second window gives exactly one merge:
`248f087d` (**PR #5556**, miso-241) at 16:47:29Z. **That is a red herring**, and the
`checkout` lines in the two job logs say why:

* the last SHORT run checked out `refs/remotes/pull/5556/merge`, i.e. `44ac71ba` merged
  into its base — so **#5556's four files were already in the 9m46s tree**;
* the first LONG run checked out `refs/remotes/pull/5557/merge` =
  `59a9941 "Merge 7b7b758c into 248f087d"`.

So the two trees are a clean one-variable A/B: **baseline tree == `248f087d`**, and
**first-long tree == `248f087d` + PR #5557**. #5557 (`capx D85-R record repairs`) merged
to `main` at 16:47:48Z, five seconds after that run was created, which is why every
branch's merge-ref carries it from then on.

The true delta (`git diff $(git merge-base 7b7b758c 44ac71ba) 7b7b758c`) is 11 files /
+1585 −73: `docs/governance/key-provenance-exceptions.json` (new, 320 lines),
`scripts/lib/key_provenance.py` (+404 −73), `scripts/check_key_provenance.py` (new),
`scripts/golden_forecast_bands.py`, `src/market_sim/pipeline/persist.py` (+34),
`tests/regression/test_key_provenance_exceptions.py` (**new, 9 tests**), and docs.

Collection count corroborates: baseline **9118 items**, both long runs **9127 items** —
exactly **+9**, the nine tests of the new file.

## §3 The duration evidence, and where the time goes

### 3.1 The regression is entirely in the last fifth of the run

Progress-line timestamps, parsed from the two job logs (`[N%]` first-reached, seconds
after the pytest banner):

| pct | baseline 34144853473 | first long 34144876665 | delta |
|---:|---:|---:|---:|
| 20 % | 108.4 s | 83.7 s | −24.7 |
| 25 % | 134.6 s | 163.7 s | +29.1 |
| 40 % | 204.2 s | 213.6 s | +9.4 |
| 60 % | 310.2 s | 335.6 s | +25.4 |
| **80 %** | **351.8 s** | **354.7 s** | **+2.9** |
| 83 % | 353.4 s | 568.4 s | **+215.0** |
| 89 % | 374.6 s | 626.0 s | **+251.4** |
| 100 % | **558.4 s** | never reached (cancelled at 1078.7 s, still 89 %) | **≥ +520** |

Gaps > 40 s: baseline **one** (52.3 s). First long run: 57.0 / 31.8 / 90.7 / 78.1 / 39.3 /
38.1 s plus a terminal **≥452 s** with no output. Second long run stalls at the **same
progress positions** (96.2 / 41.5 / 59.6 / 103.5 / 102.4 / 52.2 / 63.4 s, terminal ≥149 s)
on a different tree — deterministic, therefore content, not scheduling noise.

### 3.2 The workload itself barely moved (local A/B, this session)

Full fast tier, `-n 2`, this machine, identical command:

| tree | result | wall |
|---|---|---|
| `248f087d` (pre-boundary) | 6 failed, **9058** passed, 53 skipped, 1 xfailed | **546.04 s** |
| `60f244e3` (current main) | 6 failed, 9087 passed, 53 skipped, 1 xfailed | **620.91 s** |

+74.9 s for the whole span of main since the boundary — nowhere near the ≥520 s CI excess.
The tail region alone (`tests/unit/{model,pipeline,policy,results}`, the 80–100 % band)
is **210.68 s** pre-boundary and **215.97 s** at HEAD: **+5.3 s**. So `persist.py`'s
`environment_block()` addition, the only `src/` change in #5557, costs nothing.

Slowest calls at HEAD (`--durations`, whole tier, top 8): 46.82 s
`test_capacity_screen_peak_measured_hindcast.py::…::test_crossover_forward_year_keeps_the_growth_path`,
34.38 s `…::test_arming_adds_no_demand_read`, 32.68 s
`…::test_forecast_run_is_byte_identical_armed_and_unarmed`, 30.80 s
`test_runner.py::TestRunScenarioIso::test_rerun_skips_all_cached_years`, 30.11 s
`test_eia_loader.py::…::test_pjm_2019_2020_demand_resolves_from_hourly_extract`, 29.26 s
`test_crossover_harness.py::…::test_forward_year_demand_not_from_realized_loader`,
25.53 s `…::test_armed_hindcast_screens_see_the_measured_peak`, 23.87 s
`test_dam_outage_wiring.py::…::test_caiso_per_plant_precedence_and_fallback`. All of these
predate the boundary and are present in the 9m46s baseline run.
`tests/regression/test_key_provenance_exceptions.py` appears once, at **8.67 s setup** —
which is exactly the trap: **on this checkout it is cheap.**

### 3.3 The reproduction: a CI-shaped clone

Built locally to the letter of the `fast-tests` job:
`git clone --filter=blob:none --depth=1 --no-checkout`, the 82 `sparse-checkout`
patterns lifted verbatim from `ci.yml`, `git checkout --force main` (3.6 GB, 10.5 k files),
`uv sync`. Same Python, same lock, same machine.

```
tests/regression/test_key_provenance_exceptions.py
  author checkout  (/home/user/market-simulator) : ~15 s, 9 passed
  CI-shaped clone  (/home/user/ci-repro/repo)    : 1 passed in 273 s, then still
                                                   building the `record` fixture at
                                                   8.5 min, 99.9 % CPU, RSS 48 MB
```

Not network, not memory, not the promisor clone: `git rev-parse`/`git show` of the one
full-length vintage sha cost 1.97 s + 0.63 s once, and `git status --porcelain` /
`git diff --stat HEAD` (the per-bundle `persist.git_state()` calls) measured **0.032 s /
0.010 s both before and after** that lazy fetch. Pure CPU.

### 3.4 The mechanism, measured

`K.census(fetch_vintages=False)` per mismatch row:

| checkout | classify #1…#15 | census total |
|---|---|---|
| author's (`/home/user/market-simulator`) | 0.017–0.34 s, classes `pre-ledger-flip`, `pre-ledger-flip+split-root`, `lag` | **5.33 s** |
| CI-shaped (`/home/user/ci-repro/repo`) | **33.4 / 34.6 / 39.0 / 39.6 / 41.4 / 43.4 s …**, class `unclassified-unreachable-commit` for every row | **≈ 570 s** |

Both report `instrument_mismatch = 15` over the same 227 committed `run_config.json`.
`head_key` itself is identical in both (1.4–1.9 ms per key; 3.0 s projected for all 227).
The cost is entirely inside `classify`.

**Why.** `ScenarioConfig.cache_key()` rewrites checkout-absolute path values to
`<repo>` / `<data_root>` sentinels through `_cache_key_path_roots()`, which reads the
**current** checkout's `REPO_ROOT`. A committed payload carries the absolute paths of the
machine that solved it (`/home/user/market-simulator/data/raw/…`). Under that same prefix
the fold matches and the ladder's first rung reproduces the recorded literal in ~0.3 s.
Under **any other** prefix — a GitHub runner at
`/home/runner/work/market-simulator/market-simulator`, or simply a second clone — nothing
folds, no rung ever reproduces, and `classify` exhausts its entire recipe search before
falling through: 33–43 s per row × 15 rows.

**Arithmetic that closes the gap.** ~570 s per `census()`; the `record` fixture is
module-scoped, so under `-n 2 --dist load` **both** workers build it, in parallel →
**≈ +570 s of wall time**. Measured CI excess, first long run: 558.4 s → ≥1078.7 s =
**+520 s**. The residual is the second long run's smaller terminal stall and ordinary
scheduling jitter. Nothing else needs to be invoked.

**A second defect this exposes, for the routing.** On a non-solving checkout every one of
the 15 rows classifies `unclassified-unreachable-commit` instead of by its named recipe.
`test_census_has_zero_unknown_mismatches` only asserts `record["unclassified"] == 0`, and
`unclassified-unreachable-commit` is counted apart — so the gate **passes in CI while
measuring a degenerate case of itself**. The check that actually discriminates has only
ever run on the author's machine.

## §4 What I fixed, and what I routed

### Fixed (mine — markers on tests this diagnosis shows were mismarked)

`tests/regression/test_key_provenance_exceptions.py`: the **seven** tests that take the
`record` (census) fixture now carry `@pytest.mark.slow`, with the reasoning written into
the module docstring. The two that do not touch `census()`
(`test_exception_record_is_well_formed`, `test_exception_record_json_is_committed_and_parses`)
stay in the fast tier.

This is the repo's own marker definition applied honestly — *"slow: test is slow"* — to a
test measured at **~570 s of CPU on every checkout that is not its author's**, i.e. on
every CI run. It is a **quarantine, not a verdict**: the gate still runs in the full
serial lane (`pytest` with no `-m`) and through `scripts/check_key_provenance.py`, and it
returns to the fast tier the moment `classify` is bounded. `continue-on-error` was not
re-added, `timeout-minutes` was not raised, and nothing reports green having tested
nothing — 9,118 tests still run on every PR.

Verified in the environment that reproduces the fault: in the CI-shaped clone the file
now runs **`2 passed, 7 deselected in 0.04 s`** (was: not finished after 8.5 min).

### Routed — capx D85-R lane (`scripts/lib/key_provenance.py`)

Two items, neither of which this lane owns:

1. **`classify()` is unbounded on a foreign checkout.** 33–43 s per row is the ladder
   exhausting its recipe search because the path fold can never match. Either bound the
   search, or make the fold checkout-independent — the payload's `<repo>`-relative form
   is derivable from the recorded `environment.cache_key_path_roots` block that #5557's
   own `persist.py` repair (v-a) just started writing, which is precisely the information
   needed to re-fold a foreign payload correctly. Fixing it restores the tests to the
   fast tier and is the real repair.
2. **The gate is degenerate off the author's machine** (§3.4). `unclassified-unreachable-commit`
   for all 15 rows is not "this clone lacks a vintage blob" — it is "the checkout path
   differs", which is the normal case everywhere except one laptop. The class name and
   the assertion should distinguish them.

Not touched: any ISO shard, keeper, registry, matrix cell, marker file, or dashboard.
No solve, no registration. FR-22's three MISO failures are unrelated and were left alone.

## §5 Billed-minute delta

`ci.yml` is one workflow of ten jobs; only `Fast test tier` moves.

| | `Fast test tier` job | whole `ci.yml` run |
|---|---|---|
| before the boundary (measured, 34144853473) | 11.6 min | 11.6 min |
| after the boundary (measured, 20 runs) | **20.3 min** (cap, cancelled) | **20.3 min** |
| after this change (projected) | **≈ 11.6 min** | ≈ 11.6 min |

**Saving ≈ 8.7 billed runner-minutes per `ci.yml` run**, and the check concludes instead
of being cancelled. The projection is not an estimate from the delta alone: the full fast
tier was re-run **in the CI-shaped clone with this change applied** and finished in
**569.55 s (9m29s)** — `16 failed, 9070 passed, 53 skipped, 1 xfailed` — against the
558.4 s the baseline job spent from banner to 100 %. (None of the 16 is
`test_key_provenance_exceptions.py`; six are the failures the baseline CI run already
had, and ten more arrived on `main` between `248f087d` and the clone's `ad78cc3` from
other lanes — golden-manifest provenance, gate-A, backcast artifacts, the registration
marker gate. They are not this lane's and are not touched here.) Adding the job's fixed
~110 s of checkout + `uv sync` gives ≈ 11.4 min, i.e. the pre-boundary figure.
No `timeout-minutes` change is requested and none is needed — the tier's honest runtime
is ~10 min, well inside the existing 20-minute cap.

## §6 What this means for the branch-protection flip

Whether to flip is the owner's call and has already been ruled; this paragraph only
states the fact the flip depends on. For the ~68 minutes from 2026-09-07T16:47:43Z until
this change lands, `Fast test tier` — one of the seven R-AE required checks — could not
report a verdict at all: it was cancelled at the job cap on every PR, on every branch,
with roughly the last fifth of the suite never executed. A required check in that state
does not block merges on a real signal, it blocks them on a stopwatch, and it also
conceals whatever the unexecuted 11 % of the suite would have said. After this change the
tier concludes again in ~11.6 min with 9,118 tests run, and the one gate removed from it
is named, quarantined rather than deleted, and routed with a repair that returns it. The
seven-check set is therefore meaningful again as of this PR; the residual is that the
key-provenance record gate is, until the capx D85-R repair lands, enforced only in the
full serial lane.
