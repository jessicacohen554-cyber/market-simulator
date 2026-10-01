# FINDING — CI-RED REPAIR: the three `ci.yml` jobs failing on `main`'s own content

**Date:** 2026-09-02 · **Lane:** `claude/ci-red-repair-hn56lh` · **PR:** #4564
**Executes:** owner ruling **R-P** (2026-09-01 third sitting), blockers 1 and 2 as
recorded at director board **v19b H-1**
**Evidence base:** `docs/handoffs/audit-program-director-board-2026-08.md` v19b top
block + H-1, measured there against **run 2278** (the most recent *completed*
`ci.yml` run at pin `f45766e4`)
**Scope discipline:** no solve · no matrix edit · no keeper shard, marker, freeze
file or `program-status.json` touched · no guard silenced, skipped or loosened ·
workflow edits confined to the shrink-guard reporting scope (job 5)

---

## 0. Result

| R-P proposed required check | run 2278 (`main`) | this branch |
|---|---|---|
| `Rule-22 quarantine gates` | 🟢 success | 🟢 unaffected |
| `Rule-28 mechanism-matrix guard` | 🟢 success | 🟢 unaffected |
| `Cache-key registration guard` | 🟢 success | 🟢 unaffected |
| `FR-21 forecast-board staleness (WARN only)` | 🟢 success | 🟢 unaffected |
| **`Pinned default cache key`** | 🔴 **failure** | 🟢 **repaired** |
| **`Ruff lint + format`** | 🔴 **failure** | 🟢 **repaired** |
| **`Structural refactor guards`** | 🔴 **failure** | 🟢 **repaired** |

**All seven of R-P's proposed required checks are green on this branch.**

Two `ci.yml` jobs remain red on `main` content and are **untouched**: `FR-22
backcast->forecast parity` and `Forecast-invariant artifact audit`. Both are
**outside this lane's scope and outside R-P's required set** — H-1 names both
DO-NOT-REQUIRE. `Fast test tier` is deferred by memo §3. Re-measured at this pin:
`check_forecast_parity.py` exit 1, `check_forecast_invariants.py --sidecar-dir`
exit 1; every other gate script exits 0.

**Green run id: see §6.**

---

## 1. Reproduction (job 1)

Every red was reproduced locally from base-branch content, under CI's own
environment (`uv sync`) and each job's exact commands from `ci.yml`, with exit
codes captured **unpiped** (a piped `$?` reads the tail of the pipeline, not the
command — the first capture attempt made exactly that error and reported
`RUFF_CHECK_EXIT=0` on a failing run).

| job | step | exit |
|---|---|---|
| `Ruff lint + format` | `ruff check .` | **1** (5 errors) |
| `Ruff lint + format` | `ruff format --check .` | **1** (48 files) |
| `Pinned default cache key` | the two pin/guard pytest files | **1** (3 failed / 20 passed) |
| `Structural refactor guards` | `compileall -q src scripts` | 0 |
| `Structural refactor guards` | `ci_refactor_guards.py` | 0 (11 known-dangling tolerated) |
| `Structural refactor guards` | facade + persisted-identity tests | **1** (4 failed / 86 passed) |

All three reds reproduce from base-branch content, confirming the board's
measurement. Note that `refactor-guards` shares three of its four failures with
`cache-key-pin` (both run `test_persisted_identity.py`) — one root cause, two red
jobs — which is precisely the signal-isolation property the `cache-key-pin` job's
own header comment was created to provide.

---

## 2. `Pinned default cache key` — root cause (job 3)

### 2.1 What moved

| pin | pinned literal | measured at HEAD |
|---|---|---|
| `PINNED_DEFAULT_CACHE_KEY` | `603c2498bf71d21d` | `7a57fadff595ca83` |
| `PINNED_BACKCAST_CACHE_KEY` | `e027bc248c93c835` | `1d82ebcc9666278d` |

The test's own single-field diagnostic (`_fields_explaining_the_key_move`)
returned **"No SINGLE field explains the move"**, which is the branch that asks
for the manual bisect. That bisect was run: `scenarios.py` — which holds the
field set, `_CACHE_KEY_OPTIONAL_FIELDS`, the declared-defaults ledger *and*
`cache_key()` itself, so swapping it swaps the whole hashing surface — was
checked out at each candidate commit into the HEAD tree and both keys re-hashed.

| commit | subject | default key | backcast key |
|---|---|---|---|
| `ac14ddbd` | #4479 capx-D18 | `603c2498bf71d21d` ✅ | `e027bc248c93c835` ✅ |
| **`aebeb60e`** | **caiso-231 un-grounded-class offer re-grounding** | **`7a57fadff595ca83`** 🔴 | **`1d82ebcc9666278d`** 🔴 |
| `0ee0542a` | capx D24-R cache-key repair | `7a57fadff595ca83` | `1d82ebcc9666278d` |
| `e93ead0f` | add `carbon_price_delta` | `7a57fadff595ca83` | `1d82ebcc9666278d` |
| `0931d7e6` | delete `renewable_buildout_pace` | `7a57fadff595ca83` | `1d82ebcc9666278d` |
| `525496de` | capx-D34 carbon-price guard | `7a57fadff595ca83` | `1d82ebcc9666278d` |
| `eda30219` | miso-198 | `7a57fadff595ca83` | `1d82ebcc9666278d` |
| `HEAD` | — | `7a57fadff595ca83` | `1d82ebcc9666278d` |

**The move is a single step, at `aebeb60e`, and the payload key-set diff across
that step is one name: `caiso_offer_surface_measured_ungrounded`** — a new
`ScenarioConfig` field added *without* an entry in `_CACHE_KEY_OPTIONAL_FIELDS`,
so it enters the digest at its own default and orphans every on-disk cache.

This is the **rule 24 `[R-REGISTRY]`** recurrence that
`scripts/check_cache_key_registration.py` exists for — its docstring lists five
prior instances. Run against caiso-231's own merge base the guard reproduces the
miss exactly and prints this repair as the remedy:

```
[1] 1 new ScenarioConfig field(s) added in this PR are NOT in
    _CACHE_KEY_OPTIONAL_FIELDS ...: caiso_offer_surface_measured_ungrounded
  REMEDY (one line, do NOT re-pin the cache-key literal): ...
```

**Why the guard is green on `main` today:** check 1 is a `--base` diff check. On
any PR *after* caiso-231 merged, the field exists on both sides of the base, so
no new field is seen. The guard did not fail to detect this; it detected it on
the PR that introduced it, and the merge did not wait for it (the board's
documented 16-second merge pattern, H-1 "EXECUTION STATE").

### 2.2 The two neighbouring commits are innocent — measured, not assumed

- **`0931d7e6`, `renewable_buildout_pace` deletion.** Deleting a hashed field
  would normally move the key; this one does not, because the commit parks the
  field in `_CACHE_KEY_RETIRED_FIELDS` at `"mid"`, which re-injects it into the
  hashed payload at its retired value. Key-neutral by construction, and its own
  commit message records the control: *"default cache key 7a57fadff595ca83
  UNMOVED"* — i.e. the key was **already** on the moved value when it landed.
- **`0ee0542a`, capx D24-R.** Changes the drop rule from the **live** default to
  the **declared** default. Guard check 3 already forces declared == live for
  every registered field, so the re-baseline is a no-op — as its own commit
  message states and as the bisect independently confirms.

### 2.3 🔴 A dated correction: two committed artifacts carry the wrong attribution

Both of the following are **incorrect** and neither is edited by this PR (records
files are outside this lane's scope — routed in §7):

- `frontend/data/forecast/program-status.json`: *"23 of main's 33 test failures
  are one stale-pin defect — `ScenarioConfig().cache_key()` is
  `7a57fadff595ca83` but every pin still reads `603c2498bf71d21d`, **the intended
  consequence of D24-R (`0ee0542a`) meeting R-A's default flips (`ecf9972f`)**,
  not re-pinned in that PR. **A re-pin sweep clears all 23.**"*
- `results/calibration/miso198_oom_B/calibration_attestation.json` §(10):
  *"the capx-d24 repair **deliberately moved** the default key
  `603c2498bf71d21d -> 7a57fadff595ca83` (owner ruling Q20 b′) without updating
  its literal pins"*.

**Why both are wrong.** R-A's default flips were already in the tree at
`ac14ddbd`, where **both** keys still read their pinned values — including the
backcast pin `e027bc248c93c835`, which *is* R-A's own advance. D24-R landed
after the move and did not move either key. (The cited sha `ecf9972f` does not
resolve in the current history at all.)

**Why the difference matters.** The prescribed remedy differs: the recorded
attribution ("intended consequence", "a re-pin sweep clears all 23") licenses
**re-pinning 23 literals** and permanently accepting an orphaned cache. The
measured attribution requires **registering one field**, which restores every
orphaned key and edits no pin. The two diverge on exactly the decision the guard
docstring calls *"tempting and WRONG"*.

### 2.4 The repair — and why it is not a re-pin

Per the lane charter, an **undeclared** part of a key move forbids re-pinning.
Nothing here is re-pinned: `_CACHE_KEY_OPTIONAL_FIELDS` gains the field, and
**both pinned literals are restored untouched**, measured:

```
forecast 603c2498bf71d21d   backcast e027bc248c93c835
```

Preconditions verified before registering (registration is only sound if the
field is genuinely cache-neutral at its default):

1. **Single gated consumer.** `pipeline/backcast_config.py:2176` —
   `if caiso_offer_surface_measured_ungrounded and iso.upper() == "CAISO":`. No
   other read exists in `src/`. Off, the tree is byte-identical to the pre-field
   tree; armed, the config is re-overridden to `True` and still hashes distinctly.
2. **No coercion hazard.** The field is a `_BACKCAST_ONLY_OVERLAY_FIELDS` member,
   and that family's forecast-mode handling is a **refusal** (`ValueError`), not
   a coercion — so it cannot land off its declared default the way the D-3a
   near-miss and the R-A pair did, and it needs no
   `_DECLARED_BACKCAST_COERCION_REKEYS` entry.
3. **Ledger discipline.** Positioned at the end of the CAISO cluster per HOUSE-3,
   with the paired `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` line **appended** in the
   same commit (guard check 4 is append-only; no existing line is edited).
4. **No committed artifact is re-keyed.** No bundle, sidecar or `run_config.json`
   records a key in the moved family; the only occurrences of `7a57fadff595ca83`
   in the tree are the prose claims quoted in §2.3.

Cost: a one-time cache miss for any *unarmed* default-config solve run between
`aebeb60e` (2026-09-01) and this PR. caiso-231's own **armed** arms are
unaffected — an armed run's key never depended on the registration.

**Verification:** `Pinned default cache key` job **23 passed**;
`check_cache_key_registration.py` exit 0 both with and without `--base`
(221 registered fields, all resolve, all declared defaults match HEAD).

---

## 3. `Ruff lint + format` — root cause (job 2)

### 3.1 `ruff check` — 5 errors, of which **two are real latent defects**

| finding | file | class | disposition |
|---|---|---|---|
| F821 `build_nyiso_link_loss` | `runner.py:2779` | **real bug** | fixed |
| F821 `entry_walks` | `runner.py:1736` | **real, latent** | fixed |
| F821 `entry_reserve_adders` | `runner.py:1745` | **real, latent** | fixed |
| F841 unused `prov` | `gen_caiso197_attestation.py:357` | dead code | fixed |
| F541 f-string, no placeholders | `gen_caiso197_attestation.py:358` | dead code | fixed |

**`build_nyiso_link_loss` — a genuine `NameError`.** It is called at the NYISO
limb of the `link_loss` ladder but never imported, while its three siblings
(`build_caiso_link_loss`, `build_miso_link_loss`, `build_pjm_link_loss`) are
imported from `market_sim.model.transmission` twelve lines apart. Arming
`nyiso_zonal_loss_surface` raises `NameError` at that call. The name is
re-exported by `model.transmission` as the same object as
`model.interchange.build_nyiso_link_loss` (verified), so the fix is one import
line beside its siblings. Latent only because the flag is default-off.

**`entry_walks` / `entry_reserve_adders` — real, latent, and a broken mirror.**
Both are read near the top of the year loop in `run_scenario_iso` (the D11-R and
D12 entering-year rebinds) but bound only further down, at the solved-year seam.
Their own comments say they *"mirror `unified_signals`"* — and `unified_signals`
carries a **pre-loop binding** for exactly this reason. These two did not. Today
no live path reaches them unbound, because all three reads are gated on
`prior_results is not None`, which is `False` before the first seam; the defect
is one early `continue` away from a real `UnboundLocalError`. Fixed by binding
both before the loop, mirroring `unified_signals` exactly.

**Byte-identical, by construction:** each name is re-assigned to a fresh `{}` at
the seam on every iteration, so the pre-loop bindings are only ever read before
the first seam, where the gates are `False`. No solve path changes.

The two `gen_caiso197_attestation.py` lints are dead code; the call whose result
was discarded is retained (its assertions are the point) and the attestation's
printed output is unchanged.

### 3.2 `ruff format` — 48 files, ~180 lines of churn

`uv run ruff format .` output verbatim: no hand edits, no refactors,
AST-preserving. Total across all 48 files is under 200 lines — the churn is
accumulated drift, not a reflow. Two files (`runner.py`'s neighbour
`gen_caiso197_attestation.py`, and the file itself) carry their format
normalization in the lint commit so each file lands once.

**Charter exclusions honoured, not worked around.**
`src/market_sim/config/constants.py` is in `pyproject`'s `extend-exclude` (HOUSE-1
charter 2026-08-08 — *"ruff format must never reflow this hand-formatted core
file"*) and is **verifiably absent from the diff**; `scripts/archive`,
`scripts/probes` and `results/` likewise. Every existing per-file ignore is
untouched.

### 3.3 It re-reddened within minutes of the merge — which is R-P's own argument

This PR's parent was merged at **03:28:43Z**. Re-checked against `main` at
**03:45Z**, ~16 minutes and six merges later, `ruff format --check` was **red
again** on exactly one newly landed file:
`docs/handoffs/d33/position-decomposition-2026-09-02.py` (#4569, capx D33). It
is repaired here — a **one-line** reformat, the trivial case.

Recorded because the *shape* is the finding, not the file. With no required
status check, a mechanically-enforceable gate cannot stay green for a quarter of
an hour at this repo's merge cadence, and every later lane inherits the red — the
exact dynamic that let the caiso-231 registration miss reach `main` in §2.1 and
that left the `STORAGE_TECH_AVAILABLE_YEAR` inventory line unfixed through two
lanes in §4. Repairing a red without the flip buys minutes; the flip is what
makes the repair hold.

**And again, twice more, while this follow-up was being written.** Re-checked at
~03:55Z: red on `docs/handoffs/d33/…` (#4569). Re-checked at ~04:20Z, after that
repair merged: red again on **`src/market_sim/data/outages.py` and
`tests/unit/data/test_unit_outage_mixed_gas_routing.py`** (#4575, miso-200) —
this time **core `src/` code**, not a record-class file, so no exclusion would
have covered it. Both repaired here. **Three independent re-reddenings inside
one hour**, each from a different lane, each landing green-in-its-own-eyes
because nothing made the check block a merge. This lane stops chasing the file
here: at this cadence a repair without the flip has a half-life measured in
minutes, and the durable fix is R-P itself.

**Routed, not acted on (§7 item 5):** the *first* of the three is a **per-run analysis driver
committed as a record** — its own docstring says "zero solves" — living under
`docs/handoffs/`, which is *not* in `pyproject`'s `extend-exclude`. That exclude
list already carves out exactly this class for the same stated reason
(`scripts/probes`, `scripts/archive`, and `results/`, added after per-run scratch
drivers inside bundles *"went red on main for every PR that touches src/"*).
`docs/handoffs/**/*.py` is the same class and the same recurrence, one directory
short of the carve-out. **This lane did not add it**: widening a lint exclusion is
loosening a guard to get green, which the charter forbids, and it is a charter
question for the owner rather than a repair.

---

## 4. `Structural refactor guards` — root cause (job 4)

Two of its three steps already passed on `main`: `compileall` exit 0, and
`ci_refactor_guards.py` exit 0 (*"script-refs: OK (11 known-dangling
tolerated)"*) — **the `gen_caisoNNN` dangling-reference class the charter
anticipated is already inside the guard's own tolerance list and is not this
job's red.**

The job's red is its third step, and it has two components:

1. **Three `test_persisted_identity.py` failures** — the *same* root cause as
   §2, not a separate defect. Cleared by the same registration.
2. **`test_constants_facade.py::test_moved_surface_is_complete`** on
   `STORAGE_TECH_AVAILABLE_YEAR`.

**The facade contract was never broken.** Verified directly:
`constants.STORAGE_TECH_AVAILABLE_YEAR` resolves **and is the same object** as
`capacity_market.STORAGE_TECH_AVAILABLE_YEAR`, so
`test_every_moved_name_resolves_from_constants_facade` passes. What was missing
is the paired line in the test's frozen `MOVED_SURFACE` inventory — the name was
added to the split module *and* re-exported, but the inventory did not follow.
This is the identical gap `PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE` carries an
in-file comment for a few lines above, and it is an **allowlist-maintenance
item**, not a structural break — so it is fixed mechanically, with the guard's
own convention (a dated comment naming the cause), and nothing is suppressed.

Reported as a pre-existing `main` red by **two** prior lanes and fixed by
neither: `FINDING-capx-d16-seam-guard-2026-08-30` §3 and
`FINDING-capx-d4m-ercot-t1h-2026-08-31` §9 (*"Reported, not fixed — outside lane
scope"*).

**Verification:** all three steps exit 0; the pytest step reads
**90 passed, 5 subtests passed**.

---

## 5. `shrink-guard` — the R-P blocker-2 evaluation (job 5)

**The board's finding is confirmed.** `file-integrity-guard.yml`'s
`pull_request` trigger was path-filtered to `src/**`, `scripts/**`, `CLAUDE.md`,
`model-methodology-spec.md`, `.github/workflows/**`. A docs-only PR — **every
records-lane PR** — never triggers the workflow, so the check never reports, and
GitHub treats a never-reporting required check as **pending, not passed**.
Requiring it as written strands those PRs indefinitely.

**Verdict: make it report.** The `paths:` filter is removed from the
`pull_request` trigger only. The `push` trigger keeps its filter — a push to
`main` needs no always-report property, and unfiltered runs there would be billed
minutes for nothing (repo CI cost policy).

**This is a reporting-surface change, not a semantics change.** The scan is
already scoped by the step's own `is_core()` case, so on an out-of-scope PR
`expected = scanned = 0`, the step prints `Scanned 0/0 core paths` and exits 0 —
a clean no-op success. Untouched: the >30 % shrink rule, the deletion rule, the
≥300-line base threshold, the fail-closed incomplete-scan check (the PR #2866
lesson), and the `intentional-shrink` escape hatch. The stale *"and
path-filtered"* clause in the file header is corrected in the same commit.

A `do-not-require` write-up was the alternative; it is rejected because the guard
enforces **rule 27 `[R-PUSH]`**, whose incident is the reason the required set is
being flipped at all — leaving it unrequirable would carve the rule-27 guard out
of the very mechanism meant to enforce it.

---

## 5b. An induced regression, caught by the PR's own run and repaired

The branch's **first** push (run **2297**) turned `Rule-28 mechanism-matrix
guard` — green on `main` — **red**. Cause: registering the cache-key field added
**19 lines** near the top of `scenarios.py`, and the matrix carries
`scenarios.py:NNNN` **line anchors** for every row whose field is defined below
that point. 236 anchors went stale at once.

Repaired with the guard's own remedy, `check_mechanism_matrix.py --fix-anchors`
(*"repairs the digits only; the field NAME is the durable identifier"*), which is
routine maintenance for any PR that inserts lines into `scenarios.py` — the board
records the same command reading *"repairs 0"* at the v19b pin.

**This is an anchor repair, not a matrix edit** (the lane charter forbids the
latter), and that is *proved*, not asserted: normalizing every digit run in both
the pre- and post-images leaves the two files **byte-identical — not one
non-digit character changed anywhere** — and the only numeric delta applied
across all 120 changed lines is **+19**, exactly the line count this branch added
to `scenarios.py`. No verdict, cell, `fc` posture, evidence citation or keeper
stamp moved, and **all six per-ISO shards are unmodified**.

Worth recording as its own item: the ordinary consequence of this coupling is
that **any** PR adding lines high in `scenarios.py` inherits a red matrix guard
until it runs `--fix-anchors`. It is caught reliably (the guard is a hard gate
and names the remedy), but it is a standing tax on a heavily-crossed file.

---

## 6. Evidence — the green run (job 6)

**Run `2298`, id `33587007663`, head `0b4bdb39` — COMPLETED.**
<https://github.com/jessicacohen554-cyber/market-simulator/actions/runs/33587007663>

| job | conclusion | in R-P's required set |
|---|---|---|
| `Rule-22 quarantine gates` | 🟢 success | ✅ |
| `Rule-28 mechanism-matrix guard` | 🟢 success | ✅ |
| `Cache-key registration guard` | 🟢 success | ✅ |
| `FR-21 forecast-board staleness (WARN only)` | 🟢 success | ✅ |
| `Pinned default cache key` | 🟢 success | ✅ |
| `Ruff lint + format` | 🟢 success | ✅ |
| `Structural refactor guards` | 🟢 success | ✅ |
| `FR-22 backcast->forecast parity` | 🔴 failure | ❌ DO-NOT-REQUIRE (H-1) |
| `Forecast-invariant artifact audit` | 🔴 failure | ❌ DO-NOT-REQUIRE (H-1) |
| `Fast test tier` | 🔴 failure | ❌ deferred (memo §3) |

**7 of 7 required checks green.** The run is **not** "fully green" and this
finding does not claim it is: the three jobs still red are the three R-P
deliberately leaves out, each red on `main` content for reasons this lane did
not touch. Run **2297** (the branch's first push) is retained as the record of
the induced matrix regression and its repair (§5b).

`file-integrity-guard` run **2736** also passed on this PR's diff — 28 changed
core files ≥300 lines, none shrunk.

### The no-regression proof, and what the repair actually cleared

The full fast tier was run **twice locally under identical conditions** — once
on this branch, once with `src/ scripts/ tests/ conftest.py pyproject.toml`
checked out from `origin/main` — and the failure sets diffed name-for-name:

| | `origin/main` | this branch |
|---|---|---|
| fast-tier failures | **56** | **33** |
| failures **only on this branch** (regressions) | — | **0 — the set is EMPTY** |
| failures **only on main** (cleared here) | **23** | — |

**Zero regressions across 51 changed files.** Of the 23 cleared, **22 are
cache-key pin tests** spread across `tests/unit/config/`, `tests/unit/data/`,
`tests/unit/model/`, `tests/unit/pipeline/` and `tests/regression/`, and one is
the facade inventory. That number is the diagnosis confirming itself: the
`program-status.json` note quoted in §2.3 counted the same population
(*"23 of main's 33 test failures are one stale-pin defect"*) and prescribed
**a re-pin sweep of 23 literals**. All of them fall out of **registering one
field**, and **not one pin literal was edited.**

`Fast test tier` therefore goes **56 → 33 failures** on this branch. It stays
red and stays out of the required set; the improvement is a by-product of the
root-cause repair, not a goal of this lane, and the remaining 33 are
pre-existing and untouched.


No `workflow_dispatch` was issued: the PR's own run is the evidence, per the lane
charter and the repo CI cost policy.

**Rule 27 blob verification.** 28 of the pushed files are ≥300 lines. Every one
was fetched back from the remote after push and compared to local on **both**
line count and blob sha: **28 OK, 0 mismatches.** No file was rewritten from
regenerated response content — `ruff format`'s on-disk output was pushed as
exact bytes.

---

## 7. Routed, not fixed

Each item below is outside this lane's scope. None is edited here.

1. **🔴 → calibration desk (offer-path field).** `caiso_offer_surface_measured_ungrounded`
   landed in `aebeb60e` without its cache-key registration — a **rule 24
   `[R-REGISTRY]`** miss, the sixth documented instance. The field is repaired
   here; what is routed is the *process* finding, because the guard that catches
   this class **did** fire on that PR and the merge did not wait for it.
2. **🔴 → records lane.** The two committed artifacts in §2.3 carry a wrong
   attribution for the key move and, in `program-status.json`, a prescription
   (*"a re-pin sweep clears all 23"*) that is the remedy the guard docstring
   names as wrong. Both need a dated correction; neither is a records file this
   lane may touch.
3. **🟠 → capx desk (forecast-entry).** The two `runner.py` latent-`NameError`
   defects (§3.1) are repaired mechanically here, but they indicate that
   `nyiso_zonal_loss_surface`, `entry_margin_exhaustion` and
   `entry_forward_reserve_leg` have **never been exercised end-to-end** — an
   armed `nyiso_zonal_loss_surface` run would have crashed at the ladder. Each is
   a default-off mechanism whose arming path is untested; that is a coverage
   question for its owning desk.
5. **🟠 → owner (lint charter).** `docs/handoffs/**/*.py` holds per-run analysis
   drivers committed as records, and is **not** in `pyproject`'s
   `extend-exclude` although `scripts/probes`, `scripts/archive` and `results/`
   are, for precisely this class and after precisely this symptom. It re-reddened
   `Ruff lint + format` 16 minutes after this lane's parent merged (§3.3). Adding
   the directory is a one-line charter change and a plausible fix; it is also a
   lint-scope *widening*, so this lane repaired the file and left the charter
   alone.
6. **⚪ out of scope, unchanged.** `FR-22 backcast->forecast parity` (exit 1) and
   `Forecast-invariant artifact audit` (exit 1) remain red on `main` content.
   H-1 names both DO-NOT-REQUIRE; `Fast test tier` is deferred by memo §3.

---

## 8. R-P readiness statement

**The refreshed memo's required set stands as written.** Both blockers H-1
attached to it are removed by this PR:

- **Blocker 1** (three of the seven proposed required checks red on `main`):
  **cleared** — all seven are green on this branch, each by a root-cause repair,
  none by re-pinning, suppressing, skipping or loosening a guard.
- **Blocker 2** (the shrink guard never reports on a docs-only PR): **cleared** —
  the guard now reports on every PR, as a no-op success where it has nothing to
  scan.

The memo appendix's *"require the four green checks now, add the other three when
their lanes go green"* sequencing is therefore **no longer needed**: the other
three are green now, and the seven may be required together.

**The flip itself is the owner's Settings action.** A session cannot read or write
repository settings; this lane performed none, and no ruleset is in force at this
pin (H-1's 16-second merge record). The one caveat H-1 records still applies to
the *naming*, not the set: `FR-21 forecast-board staleness (WARN only)` carries
the **hard** `check_gate_a_provenance` step despite its display name, and
`check_golden_manifest` runs inside `Rule-22 quarantine gates`, so the seven
required checks already cover the board's seven gate scripts.
