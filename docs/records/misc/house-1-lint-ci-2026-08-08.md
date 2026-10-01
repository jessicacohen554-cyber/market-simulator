# HOUSE-1 — lint/CI infrastructure repairs (sitting Addenda T.1, X.2)

**Lane:** `claude/house-1-lint-ci-repairs-9a7n6d`, 2026-08-08, Fable (rule 27 model
assignment honored — the lane touches `.github/workflows/` and hooks).
**Charter:** the workstream manager's Y.2 unowned queue, two repairs. **No model
behavior changed**: every edit is hook/lint/CI config or a semantics-preserving
format repair. Files touched: `.claude/hooks/ruff-autofix.sh`, `pyproject.toml`,
`.github/workflows/ci.yml`, `tests/unit/data/test_outages.py` (format-only), this
doc. No `src/market_sim/` file was edited.

Charter HEAD was `a445fce`; `origin/main` moved to `7fd1c28` (PRs #3741–#3743)
mid-lane and the branch was rebased onto it. That mid-lane movement produced a
live recurrence of BOTH incident classes this charter repairs — recorded in §3.4
and §2.3, and the strongest evidence the diagnosis in §3 is right.

---

## 1 Summary of what changed

1. **`.claude/hooks/ruff-autofix.sh`** now formats **only the file the session
   actually wrote** (with `--force-exclude`), never the tree (T.1 fix a).
2. **`pyproject.toml`** adds `src/market_sim/config/constants.py` to
   `[tool.ruff] extend-exclude` (T.1 fix b). The chartered enumeration of "other
   core files failing `--check` at HEAD" came back **EMPTY** (§2.2).
3. **`.github/workflows/ci.yml`** adds the `cache-key-pin` job — the two
   pin/guard test files as an isolated, unambiguous named check (X.2 minimal
   fix, §3.3). No new workflow file, no scheduled triggers.
4. **`tests/unit/data/test_outages.py`** reformatted (8 insertions / 2
   deletions, import-statement reflow only) — repairs the format regression
   caiso-184 pushed on 2026-08-08, which had re-armed the T.1 whole-tree-reflow
   hazard the same day it was being fixed (§2.3).
5. The current fast-tier baseline failures on main are pinned in §4
   (report-only, nothing fixed there).

---

## 2 T.1 — the ruff-autofix whole-tree reflow hazard

### 2.1 Hook before/after

Before (the two operative lines):

```bash
# Whole-tree, matching CI's scope exactly: safe autofixes, then format.
uv run ruff check --fix . >/dev/null 2>&1 || true
uv run ruff format . >/dev/null 2>&1 || true
```

After:

```bash
# The edited file ONLY — never the tree: safe autofixes, then format.
uv run ruff check --fix --force-exclude -- "$f" >/dev/null 2>&1 || true
uv run ruff format --force-exclude -- "$f" >/dev/null 2>&1 || true
```

Everything else (PostToolUse rationale, `.py`-only gating, the
staged-file-only re-staging) is unchanged. Two deliberate details:

- **`--force-exclude` is load-bearing.** Ruff processes any path named
  explicitly on the command line even when config excludes it; without the
  flag, an Edit to `constants.py` itself would re-arm the exact reflow the
  exclusion exists to prevent.
- The old header claimed the whole-tree scope made "the tree physically
  unable to fail the CI lint job". That claim is retired honestly: the scoped
  hook guarantees the session's **own writes** are ruff-clean; the tree-wide
  guarantee was never real (main can arrive dirty from elsewhere — it did on
  2026-08-05 and again on 2026-08-08) and pretending otherwise is what turned
  the hook into a rule-27 [R-PUSH] footgun.

### 2.2 The exclusion list, and the `--check` evidence (an empty enumeration)

The charter ordered: add `constants.py` **and any other core file failing
`ruff format --check` at HEAD** to `extend-exclude`. Measured at charter HEAD
`a445fce` with the locked toolchain (`uv.lock` ruff **0.15.17**, the same
resolution CI's `uv sync` installs):

```
$ uv run ruff format --check .
1235 files already formatted
```

**The failing set at charter HEAD was EMPTY — `constants.py` included**
(4,169 lines, passes `--check`). The T.1 incident premise ("main's own bytes
fail `ruff format --check`", 3,960-line file) was true when recorded on
2026-08-05 but had been repaired by the time this lane ran; the repair landed
before the shallow-clone boundary (`ba80564`, where the file is already 4,102
lines and format-clean), so this lane cannot cite the repairing commit.

`constants.py` is excluded anyway, exactly as chartered — the entry is
**prophylactic**, and the hazard is version- and edit-dependent, not gone: a
future `uv.lock` ruff bump (spec is `ruff>=0.5`) or a hand edit in the file's
historical style can recreate the failing state at any time, and the file is
the rule-27 crown jewel (the 6,368 → 33-line truncation incident file). What
the exclusion costs: `extend-exclude` removes the file from `ruff check` scope
too. Accepted because its F401 surface was already per-file-ignored,
`compileall` (refactor-guards) still catches syntax breaks, and
`tests/regression/test_constants_facade.py` still asserts the full re-export
surface. (A narrower `[tool.ruff.format] exclude` would keep lint coverage; the
charter said `extend-exclude`, the cost is small, and the entry's comment
records the tradeoff — flag it to the owner if lint coverage on constants.py
ever matters.)

`tests/unit/data/test_outages.py` — the file failing `--check` at the REBASED
head (§2.3) — is deliberately **not** excluded: it is an ordinary test file
whose correct treatment is to be formatted, not fenced. The exclusion list is
for hand-formatted core files where reformatting is the forbidden act.

### 2.3 Live re-arming, and verification

While this lane ran, caiso-184 (`3d0c4cd`, PR #3742, merged 2026-08-08) pushed
`tests/unit/data/test_outages.py` with two over-long import lines, making main
fail `ruff format --check` again — so between 2026-08-08 and this PR, **any**
`.py` Write/Edit under the old hook silently rewrote a file the session never
touched. That live dirty state was used as the natural experiment for the
charter's verification, run with the NEW hook and the dirty file still on disk:

- A deliberately misformatted scratch `.py`, piped through the hook as a
  PostToolUse event → **the scratch file was formatted**; `git status --short`
  showed no repo `.py` modified; `test_outages.py` still failed `--check`
  (byte-identical). The old hook demonstrably rewrote it under the same input.
- The same simulation with `constants.py` as the edited path → no-op,
  `git status` clean.
- `uv run ruff format --check --force-exclude src/market_sim/config/constants.py`
  → `warning: No Python files found under the given path(s)` — **quiet by
  exclusion**, as chartered.
- After the `test_outages.py` repair: `ruff format --check .` → `1234 files
  already formatted` (tree fully clean; the count is one lower because
  `constants.py` is now excluded from the walk).

---

## 3 X.2 — the red-main CI gap: the actual mechanism

### 3.1 The charter's questions, answered

**Are `tests/regression/test_persisted_identity.py` + the default-key pin tests
in the ci.yml test jobs? Advisory or blocking?** Yes, and blocking — at the
**job** level, in three places, all before this lane touched anything:

- `refactor-guards` runs `test_persisted_identity.py` explicitly (blocking
  since the job existed; the comment block calls it "the only BLOCKING test
  gate" from the era when fast-tests was advisory);
- `fast-tests` collects both pin files and every per-feature
  `test_default_cache_key_is_unmoved`-style test (blocking since 2026-07-27);
- `cache-key-guard` runs `scripts/check_cache_key_registration.py`, the
  dedicated stdlib guard, plus its HEAD-only declared-defaults step.

**So why did nyiso-128's unregistered field merge?** Detection was never the
gap. On PR **#3624** (the field-adding PR, `nyiso_solar_market_generator_basis`),
every relevant check ran and **failed**, naming the field and the one-line
remedy:

| event | UTC 2026-08-06 |
|---|---|
| PR #3624 created | 03:32:55 |
| checks start | ~03:33:00 |
| **PR merged by the session** | **03:34:21 (+86 s)** |
| cache-key-guard **FAIL** — "1 new field NOT in `_CACHE_KEY_OPTIONAL_FIELDS`: `nyiso_solar_market_generator_basis`" + remedy | 03:35:57 |
| refactor-guards **FAIL** — 3 pin tests (`318c22035173707c != 603c2498bf71d21d`) | 03:36:37 |
| lint **FAIL** (pre-existing) | 03:40:03 |
| fast-tests **FAIL** — 16 failures, 9 of them pinned-key tests | 03:45:54 |

**The mechanism, in one sentence: the merge does not wait for the checks, and
nothing on the GitHub side makes it wait.** Two layers:

1. **No enforcement at the merge.** Main has no effective required status
   checks: the merge API accepted a merge with every check still pending. This
   is systemic session behavior, not a one-off — sampled merged PRs: #3652
   merged **8 s** after creation, #3715 **11 s**, #3712 **22 s**, #3624 **86 s**.
   No check of any speed can complete inside those windows. A "blocking" job in
   ci.yml only fails the *workflow run*; absent branch protection it blocks
   nothing.
2. **Ambient red destroys the signal for anyone who does look.** The jobs the
   pin tests ride were already red on clean main for unrelated pre-existing
   reasons (§4; on #3624's run, refactor-guards also carried a
   `test_constants_facade` failure and lint was red). Every recent ci.yml run
   at this writing concludes `failure`. When every PR is red, a new red carries
   no information without opening logs.

### 3.2 What that means for the chartered fix

The charter's menu ("add the test file(s) to the blocking job, or a dedicated
quick job") presumed the tests were missing from a blocking job. They were not,
so **no ci.yml edit can, by itself, make a moved pinned key block a PR** — a
workflow file cannot force a merge to wait. The honest decomposition:

- **In ci.yml's power (done, §3.3):** make the moved-key verdict *isolated,
  unambiguous, and fast* — a named check that is red iff the key contract broke,
  immune to the ambient-red problem, delivered minutes before the full tiers.
- **In the owner's power only (recommended, §3.5):** make that named check
  *required* on main. That single repo-settings act converts every job-level
  "blocking" in this file from advisory-in-effect to actually blocking.

### 3.3 The minimal change made

New ci.yml job **`cache-key-pin`** ("Pinned default cache key"): checkout +
`uv sync` + pytest over exactly
`tests/regression/test_persisted_identity.py` and
`tests/unit/config/test_cache_key_default_flip_guard.py` (~2 s of pytest; the
job's wall time is the uv sync). Same workflow file, no new workflow, no
schedule. Rationale in the job's own comment block: signal isolation here,
enforcement named as the owner act it is. `fast-tests` and `refactor-guards`
are untouched (the same tests still run there; removing them from broader jobs
was not chartered and would weaken those jobs' own contracts).

### 3.4 The live recurrence that proves the diagnosis (found, not fixed — out of lane)

While this lane was running, the identical incident class landed on main
**again**:

- **PR #3742 (caiso-184, merged 2026-08-08)** added ScenarioConfig field
  `unit_outage_lp_capacity_basis` without registering it in
  `_CACHE_KEY_OPTIONAL_FIELDS`. The pinned default key moved
  `603c2498bf71d21d → c6bcb4c8a1bdede4` (backcast pin
  `35b6dc12f97968f1 → c154148361a6aaf8`). At `origin/main` = `7fd1c28`, the
  three `test_persisted_identity` pin tests and seven per-feature key tests
  **fail on clean main right now**; `check_cache_key_registration.py --base`
  names the field and the one-line remedy. On #3742's own run, cache-key-guard,
  refactor-guards and fast-tests all failed — and the PR merged anyway, exactly
  per §3.1.
- The same merge window also put **two F821s on main** (`ruff check .`:
  `ercot_fleet_forced_outage_sigma_mw` undefined at
  `src/market_sim/runner.py:3175` and `:3346` — a latent runtime NameError on
  those diagnostic paths, most recently touched by FFR-8A `43d680a`), and the
  `test_outages.py` format regression of §2.3.

Both the unregistered field and the F821s are `src/market_sim/` repairs owned
by their (still-active) lanes and are **out of this charter's scope** ("no
model behavior may change") — reported here and in the PR, not fixed.
**Consequence the reviewer will see: this PR's own `cache-key-pin` check is
born red**, through no fault of this diff — that is the new gate correctly
reporting main's live state, and it goes green the moment the caiso-184 lane
applies the guard's one-line remedy (register the field with its
cache-neutrality comment; do NOT re-pin the literals).

**RESOLVED WHILE THIS PR'S FIRST CI RUN WAS IN FLIGHT.** Main commit `7c14d11`
(FFR-8A P3, merged in #3744–#3747) applied both out-of-lane remedies above —
`unit_outage_lp_capacity_basis` registered in `_CACHE_KEY_OPTIONAL_FIELDS`
with its declared default, and the missing `ercot_fleet_forced_outage_sigma_mw`
runner import added — about two hours after the incident landed. The PR's
checks ran against that repaired base, so "Pinned default cache key"'s first
PR verdict was **green** (as were lint and refactor-guards); after rebasing
this branch onto `0501f9b`, the job's command passes 22/22 locally and
`ruff check .` is clean. The §3.1 mechanism finding is unaffected: the
incident again merged red and was again repaired *after* landing on main,
which is exactly the pattern required-status-check enforcement (§3.5) exists
to end. (One rebase-mechanics note for the record: on the pre-rebase base,
`shrink-guard` failed reporting a deleted 392-line core file — that was
`scripts/probes/ercot180_topcurve_edge_id.py`, *added* on the moved main and
absent from the stale base, not a real deletion; rebasing cleared it.)

### 3.5 Owner acts recommended (not performable from a workflow file or this lane)

1. **Branch protection / ruleset on `main` with required status checks** —
   minimally "Pinned default cache key"; ideally also "Structural refactor
   guards", "Cache-key registration guard", "Rule-22 quarantine gates",
   "Ruff lint + format", "Fast test tier". With required checks, the
   seconds-after-creation self-merge (§3.1) becomes impossible instead of
   discouraged. (Owner-account bypass should be disabled, or the pattern
   simply continues under bypass.)
2. **Session discipline until then:** a session that opens a PR waits for the
   check verdicts (or at minimum for `cache-key-pin`, the fastest meaningful
   one) before merging. Worth a line in the prompt-pack boilerplate.
3. Have the caiso-184 lane clear §3.4's live red (field registration is its
   one-line remedy; the F821s belong to the runner.py-touching lane).

---

## 4 The pinned fast-tier baseline on main (report-only)

> **ADDENDUM 2026-08-09 (HOUSE-2) — THIS TABLE IS SUPERSEDED. The current
> baseline is rows 1 and 2 only.**
>
> HOUSE-2 (`docs/handoffs/house-2-baseline-wave-2026-08-09.md`) cleared the
> table. Measured on `origin/main` @ `b5b88de` + that branch, the fast tier
> went **7 failed → 2 failed** (6,534 → 6,541 passed). Per-row:
>
> | # | test | status |
> |---|---|---|
> | 1 | `test_ercot_thermal_as_endogenous.py::TestScreenMutualExclusion::test_derived_map_suppresses_exogenous_credit` | **STILL RED** — chartered exclusion, ercot-181 live on that surface |
> | 2 | `…::test_exogenous_credit_keeps_unit_profitable` | **STILL RED** — same |
> | 3 | `test_neiso_bins.py::…::test_committed_artifact_is_deterministic` | CLEARED — artifact regenerated (stale since the D-25 gas_st taxonomy fix, PR #3697) |
> | 4 | `test_forecast_parity.py::test_all_six_keepers_resolve` | CLEARED — the two open UNACCOUNTED fields pinned as an exact set; a *third* still reds the tier |
> | 5 | `test_forecast_parity.py::test_check_exits_zero_on_the_current_keepers` | CLEARED — `xfail(strict=True)` with the FR-22 citation |
> | 6 | `test_outages.py::…::test_unknown_iso_degrades_to_empty` | CLEARED — asserted a coverage accident (NEISO gained a nuclear extract), re-pinned to the contract |
> | 7–9 | `test_data_dictionary_sync.py` × 3 subtests | CLEARED **on main itself**, between this doc's head and `b5b88de` — no HOUSE-2 edit |
> | 10 | `test_integration.py::TestFullYearPerformance::test_full_year` | **NOT IN THE ORIGINAL TABLE.** Pre-existing; a full-8760 LP with wall-clock budget assertions that flakes under `-n 2` contention. CLEARED by adding it to the `tests/conftest.py` `slow` autotag list, where its two siblings already live |
>
> **The rule of the table is unchanged, the set is not: a fast-tier red on a PR
> whose failures are a subset of {1, 2} is baseline; anything else is the PR's
> own.**
>
> Still red on main outside the fast tier, untouched and re-verified by
> HOUSE-2: the `lint` job (3 items, all in other lanes' files — see that doc
> §3), `forecast-parity-guard` (red on the two §4-row-4/5 fields **by design**;
> that is where the signal lives), and `Forecast-invariant artifact audit`.

Chartered as: write down the pre-existing failures on main's fast tier
(`pytest -n 2 -m "not slow and not integration and not fulldata"`). FFR-5E
counted 13 "environmental" at its head; the current set is **9** (6 test
failures + 3 subtest failures of one test), and it is **identical in CI
(ubuntu-latest, hermetic checkout) and in this container** — measured twice:
locally at charter HEAD `a445fce` (9 failed / 6,500 passed, 465 s) and in CI at
`d417be7` (job 93158741229; 19 failed = these 9 + the 10 live-incident
pinned-key failures of §3.4, which are excluded from the baseline as a
regression-in-flight, not environment).

The baseline list:

| # | test | note |
|---|---|---|
| 1 | `tests/iso/ercot/test_ercot_thermal_as_endogenous.py::TestScreenMutualExclusion::test_derived_map_suppresses_exogenous_credit` | |
| 2 | `tests/iso/ercot/test_ercot_thermal_as_endogenous.py::TestScreenMutualExclusion::test_exogenous_credit_keeps_unit_profitable` | |
| 3 | `tests/iso/neiso/test_neiso_bins.py::TestNeisoBinAssignments::test_committed_artifact_is_deterministic` | |
| 4 | `tests/scoring/test_forecast_parity.py::test_all_six_keepers_resolve` | asserts on `ercot_storage_as_soc_reserve` (also a filed FR-22 gap) |
| 5 | `tests/scoring/test_forecast_parity.py::test_check_exits_zero_on_the_current_keepers` | same root as #4 |
| 6 | `tests/unit/data/test_outages.py::NuclearUnitAvailabilityTest::test_unknown_iso_degrades_to_empty` | present in the 2026-08-06 #3624 run too |
| 7 | `tests/curation/test_data_dictionary_sync.py::DataDictionarySyncTest::test_per_column_tables_match_schemas` — SUBFAILED `datatype='capacity-deliverability'` | one test, three failing subtests |
| 8 | — SUBFAILED `datatype='som-competitive-conduct'` | |
| 9 | — SUBFAILED `datatype='unit-outage-events'` | |

Also red on main at `7fd1c28`, outside the fast tier (same report-only status):
the `lint` job (§3.4's two F821s; the format half is repaired by this PR), and
the pre-existing `Forecast-invariant artifact audit` (undeclared invariant
FAILs across ~21 registered runs) and `FR-22 backcast→forecast parity`
(`ercot_storage_as_soc_reserve`, `nyiso_seam_deliverability_envelope`) reds
visible on every recent run.

FFR-5E's 13 → 9 delta: at least one of its members
(`test_constants_facade::test_moved_surface_is_complete`,
`STORAGE_MEASURED_BASE_FLEET_ISOS`) was repaired between 2026-08-06 and this
head; the FFR-5E-era list itself was never written down (that being this
section's purpose), so a member-by-member reconciliation is not reconstructible
from the shallow clone. From here on, this table is the reference: **a fast-tier
red on a PR whose failures are a subset of this table is baseline; any failure
outside it is the PR's own.**

---

## 5 Verification record

- Hook scoping: §2.3 (scratch-probe formatted; dirty tree untouched;
  constants.py no-op; force-exclude quiet).
- `ruff format --check .` after all edits: `1234 files already formatted`.
- `ruff check .` after all edits: unchanged from main tip (the two §3.4 F821s,
  pre-existing).
- ci.yml parses (`yaml.safe_load`), 10 jobs; the new job's pytest command run
  locally reproduces exactly the §3.4 live-incident failures (3 in
  `test_persisted_identity.py`) and nothing else — red for the documented
  reason.
- Rule-27 blob verification performed post-push on both ≥300-line touched
  files (`.github/workflows/ci.yml`, 344 lines; `tests/unit/data/test_outages.py`,
  1,894 lines): fetched blobs byte-identical to local (see PR).
