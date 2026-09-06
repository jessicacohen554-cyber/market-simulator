# FINDING — Y-23: the D24 §4.5 invariant is moved off `results/` and onto a committed fixture

**Lane:** Y-23, Model Audit & Release-Finalization Program. **Date:** 2026-09-06.
**Director pin:** `b618ed4b`. **Base:** `8e3393b1` (`origin/main` at lane start; the pin is its
ancestor, four merges back — every reading below was re-taken at both, and they agree except where
the census is explicitly given per-revision).
**Branch:** `claude/y23-cache-agreement-fixture-daemvd`.
**Scope:** one test file, one new fixture, this doc. No solve, no bundle, no registration, no keeper
shard, no marker, no matrix shard, no `CLAUDE.md` (rules 15 `[R-DASHBOARD]` / 29(c) `[R-SCREEN]`).

## 0. Result in one paragraph

`tests/unit/results/test_cache_config_agreement.py::CommittedSharedKeyGroupsTest` failed on `main`
because rule 15's keeper-only retention **deleted the corpus the test measured**. The class built its
population live from `git ls-files '*run_config.json'`; PR #4808 pruned that population from 193
tracked files to 72 and from 20 shared-key groups to 7, and one of the two true positives lost its
partner — so both a `>= 14` census floor and an exact refused-key set went red. The D24 §4.5
invariant now lives in a **committed fixture** (`tests/fixtures/cache_shared_key_groups/`, three real
pairs recovered verbatim from the pre-prune tree), and the live-corpus replay is kept as a second,
skip-when-sparse pass whose every assertion is prune-monotone. The floor was **not** lowered and the
assertion was **not** deleted: the fixture asserts the refused set exactly, and adds two checks the
live census never made. 15 tests pass (was 8 passed / 2 failed).

## 1. Cause, by sha

The two failures reproduce at the pin and at `8e3393b1`:

```
test_fourteen_groups_split_two_and_twelve            AssertionError: 7 not greater than or equal to 14   (6 at b618ed4b)
test_both_true_positives_are_refused_on_the_R_A_pair KeyError: 'f061b2646bfaac8b'
```

Both are the same event. **PR #4808** (merge `95739d608d086d4eec1a8282a824e8b0b47b0d00`, 2026-09-05
13:59 -0700) executed rule 15 `[R-DASHBOARD]` as amended 2026-09-05 (keeper-only retention) in two
commits on separate branch lines:

| commit | subject | `run_config.json` deleted | files deleted |
| --- | --- | ---: | ---: |
| `e090fc1f26338c9afad700152b4849c6722a4d61` | Prune `results/calibration` to keeper bundles: 18 unmapped solve-output bundles, empty the keep-required allowlist | 17 | 278 |
| `9fd5e5b3eaf371542b546c9cf0ec98981e8b4049` | Prune stale forecast runs: 36 superseded hindcast sidecars, 109 unregistered `results/hindcast` dirs, unreferenced `ffr*` lane outputs | 101 | 1130 |

*(Correction to the dispatch, which cited PR #4816: the two commits merged to `main` as **#4808**.
The commits, their counts and the diagnosis are otherwise exactly as dispatched.)*

`9fd5e5b3` is the one that broke the invariant. It deleted
`results/hindcast/ercot-2021-2025-realized-t1h-d12c-armed/run_config.json` — the **stored** side of
true positive `f061b2646bfaac8b` — leaving only `-d4m`. A key with one member is not a group, so
`self.groups['f061b2646bfaac8b']` raised `KeyError`, and `refused_keys` lost that entry.

## 2. Corpus census, before → after

Measured by replaying the class's own grouping over `git ls-tree -r <rev>` at four revisions
(`scripts` in `/tmp`, not committed; every number reproducible from the tree shas above):

| revision | tracked `run_config.json` | keyed | distinct keys | groups (>1 member) | refused keys | `07e416…` / `f061b2…` members |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `95739d60^` = `d6891edd` (pre-prune) | **193** | 154 | 119 | **20** | `07e416f3f8072e7c`, `f061b2646bfaac8b` | 2 / 2 |
| `95739d60` (post-prune) | **72** | 54 | 50 | **4** | `07e416f3f8072e7c` | 2 / **1** |
| `b618ed4b` (director pin) | 120 | 96 | 89 | **6** | `07e416f3f8072e7c` | 2 / **1** |
| `8e3393b1` (`main`, lane start) | 125 | 100 | 92 | **7** | `07e416f3f8072e7c` | 2 / **1** |

Two things this table shows beyond the immediate cause:

1. **The pre-prune corpus still replays perfectly.** At the HEAD schema, `d6891edd`'s 20 groups
   refuse exactly the two true positives, each on
   `['storage_entry_availability_gate', 'storage_entry_cost_normalized_rank']`, and permit the other
   18 — the D24 §4.5 result, unchanged. Nothing about the *rule* regressed; only its object was
   deleted.
2. **The census drifts in both directions and is already moving again** — 4 → 6 → 7 groups across
   three days of ordinary registrations, and 6 → 7 between the director's pin and lane start. The
   dispatch's own numbers (6 groups) and the test's (14) differ from each other and from today's for
   the same reason: the quantity is not an invariant.

## 3. What the fixture pins

`tests/fixtures/cache_shared_key_groups/` — three real pairs, recovered **verbatim** from
`d6891edd600611d04679c12fee732a02fd60cc16` (= `95739d60^`), source blob shas in the fixture README:

| group | form | absent-from-stored | differing-common | strict (c) | (c′) | fate on `main` |
| --- | --- | ---: | ---: | --- | --- | --- |
| `07e416f3f8072e7c` NEISO `capxd14` → `rcrepair` | **D24 §4.2** — absent vs armed default | 5 | 0 | refuse | **REFUSE** | both alive |
| `f061b2646bfaac8b` ERCOT `d12c-armed` → `d4m` | **D24 §4.1** — differing common field | 0 | 2 | refuse | **REFUSE** | stored side deleted by `9fd5e5b3` |
| `5925e67c572a910f` NEISO `d37-control` → `d45r-datesoff` | designed — ordinary schema growth | 15 | 0 | refuse | **permit** | both deleted by `9fd5e5b3` |

The five assertions, of which three are new:

* the fixture carries exactly those three groups, as pairs — an exact check is safe *here*, because
  nothing prunes `tests/`, and it stops the rest passing vacuously if the fixture is ever emptied;
* the refused set is **exactly** the two true positives (kept exact, per the brief's (b));
* each refuses on **exactly** `['storage_entry_availability_gate', 'storage_entry_cost_normalized_rank']`;
* **new** — the two true positives are the two *distinct D24 forms*. The same field list is reached
  by two different branches of `config_disagreements`, and matching refusals alone would not notice
  one form regressing onto the other's code path: §4.2 requires both fields **absent** from stored
  and `True` in wanted (760 fields vs 765), §4.1 requires both **present** at `False` vs `True`;
* **new** — the designed group is permitted where strict equality refuses: 15 fields the stored
  config predates (769 → 784), every one at the value its absence is equivalent to. This is the
  clause that decides (c′) over strict (c) on real data, which the synthetic
  `StoredConfigAgreementTest` cases can only illustrate one field at a time.

The payloads are kept **whole** (~31 KB each, 190 KB total). The invariant is "refuses on exactly two
fields out of ~765"; trimming to the fields that differ would assert the answer the trimming chose.
The per-side field counts — 760 / 765 / 765 / 765 / 769 / 784 — are themselves the schema growth the
(c′) rule exists to tolerate.

**Two verifications that the repair is not merely green:**

* *Mutation.* Replacing `cache.config_disagreements` with strict (c) fails **3** of the fixture's
  assertions (`test_the_refused_set_is_exactly_the_two_true_positives`,
  `test_both_true_positives_are_refused_on_the_R_A_pair`,
  `test_the_designed_group_is_permitted_where_strict_equality_refuses`). The fixture discriminates
  the rule, not just its inputs.
* *Prune-monotonicity.* Replaying the live class's surviving assertions over the current 100-file
  corpus under all 100 single-file deletions and 400 random subsets (sizes 0–100): **0 failures**.
  A prune can now only skip or narrow the live pass, never redden it.

## 4. The live pass, and what was dropped from it

`CommittedSharedKeyGroupsTest` still replays `git ls-files '*run_config.json'` — that is the only
surface that can catch the hazard *in the wild*, a new registration landing two materially different
configs at one bundle key, which a frozen fixture cannot. It now skips when there is nothing to
replay (no keyed file, or no key with two members) instead of when a file count falls under 90, and
asserts:

* no committed group refuses **outside** the two known true positives (`⊆`, not `==`) — pruning only
  removes candidates, so this cannot go red on a prune, and a *new* refusing group still fails it;
* a true positive that **survives** in the corpus still refuses on the same field pair — guarded on
  presence, so it goes vacuous rather than red when retention takes a member. At `8e3393b1` this is
  non-vacuous: `07e416f3f8072e7c` still has both members.

Dropped, both retention hazards rather than invariants: the `>= 14` census floor, and
`assertIn("706e7ba8e6582d42", self.groups)` (a specific T3-GOLDEN-2 bundle staying on disk). The
floor's stated purpose — "a collapse of the grouping still fails" — is now served deterministically
by the fixture, which fails if the grouping or the rule breaks regardless of what `results/` holds.

## 5. Rule-15 interaction: a census over `results/` is a retention hazard

This is the general lesson, and it is structural rather than incidental. Rule 15 `[R-DASHBOARD]` as
amended 2026-09-05 makes the committed `results/` corpus **shrink by design** — keeper-only
retention, "git history is the record" — and rule 29(c) `[R-SCREEN]` adds that screen and control
bundles are deleted before merge. Any test that reads a *quantity* out of that corpus, or that
requires a *specific* run to still be on disk, is therefore asserting something the governance rules
promise to violate. It can only ever survive by accident, and the accident had already run out three
times in two days before this one: the same class's count was repaired in place 14 → 15 → 16, then
de-brittled to a floor by caiso-239 on 2026-09-02. The floor was the same mistake one step weaker —
retention removed not just the count but the invariant's object.

The rule of thumb: **an invariant's evidence belongs under `tests/`; `results/` may be read only for
signals that are monotone under deletion** (a `⊆` check, a presence-guarded check, a skip).

**Sweep for other tests of the same shape** (`grep -rn "ls-files" tests/ scripts/`, plus a sweep for
tests naming committed `results/` paths):

| site | shape | status |
| --- | --- | --- |
| `tests/unit/results/test_cache_config_agreement.py` | `git ls-files '*run_config.json'` census + exact refused set | **the failure — repaired here** |
| `tests/regression/test_reuse_solved.py:47` | `ls-files` appears only inside a **mocked** `subprocess` stub | not a hazard — reads no corpus |
| `tests/unit/model/test_capacity.py:6425` | globs `results/hindcast/pjm-2021-2025-realized-t1h-d45r/PJM/*/evolution_2022.json` | **same dependency, already safe** — `self.skipTest("committed D45-R / D48 / D54 artifacts absent")`. It goes vacuous, not red, when that bundle is pruned. Worth knowing it *will* go vacuous: the D45-R bundle is unregistered `results/hindcast`, exactly the class `9fd5e5b3` swept. |
| `tests/regression/test_forecast_invariants.py:991` | `results/ff-t3-neiso-golden/bau/fc6/arms/*/full_horizon_summary.json` | **same dependency, already safe** — `@pytest.mark.skipif(not …exists())`. Same vacuity note. |
| `tests/regression/test_persisted_identity.py:199` | names `results/hindcast/…-d55-keyfix` in a **comment** only | not a hazard |
| `tests/unit/results/test_sensitivity_tornado.py:41` | `assertGreaterEqual(len(reg), 14)` | not a hazard — `build_registry()` is code, not the results corpus |
| `scripts/probes/capxd24r_cache_key_no_op_check.py:106` | same `git ls-files '*run_config.json'` corpus | **not a test** (a manually-run merge gate, in no workflow) and it asserts no floor — it reports over whatever is present. Its *coverage* is now 100 configs instead of 154, which weakens the probe as evidence without breaking it. Named here so a future D24-class re-measurement uses the fixture or the pre-prune tree, not today's corpus. |
| `scripts/ci_refactor_guards.py:215` | bare `git ls-files` over tracked source | not a hazard — resolves references, counts nothing |

No repair is owed to the two skip-guarded sites: they already fail safe. The one recommendation this
lane makes and does not execute (out of scope) is that a future session giving either of them teeth
should take the fixture route rather than re-arming a `results/` dependency.

## 6. Verification run

```
uv run --frozen python -m pytest -q tests/unit/results/test_cache_config_agreement.py
    15 passed                              (before: 8 passed, 2 failed)
uv run --frozen python -m pytest -q -m "not slow and not integration and not fulldata" \
    tests/unit/results/ tests/regression/test_persisted_identity.py
    273 passed, 4 deselected, 1 xfailed, 28 subtests passed
uv run --frozen ruff check tests/unit/results/test_cache_config_agreement.py   -> All checks passed
uv run --frozen ruff format tests/unit/results/test_cache_config_agreement.py  -> applied
```

## 7. What this lane did not touch

No keeper shard, marker, holdout freeze, matrix shard or `CLAUDE.md`. No run registered, no bundle
committed, no bundle restored to `results/` — the deleted configs are recovered into `tests/` as
fixture data, which is not a bundle and carries no parquet, no sidecar and no dashboard presence.
Nothing on the solve path changed, so no cache key moves and every keeper re-scores byte-identically.
