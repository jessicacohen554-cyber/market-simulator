# FINDING — capx D24-R: the cache-key repair, LANDED

**Lane:** capx D24-R · **Model:** Opus · **Branch:** `claude/capx-d24r-cachekey-repair-hjz6un`
**Charter:** owner ruling **Q20 (r#25)** on
`docs/handoffs/FINDING-capx-d24-cache-key-defect-2026-09-01.md` §7 — land **(c′) + (b′-1)**,
the zero-cost pair, exactly as D24 specifies them. Nothing else.
**Graded object:** `src/market_sim/config/scenarios.py::ScenarioConfig.cache_key` /
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`, `src/market_sim/results/cache.py`,
`src/market_sim/runner.py`'s `is_cached` seam, `scripts/check_cache_key_registration.py`
**Date:** 2026-09-01 · **ZERO SOLVES.** No LP was built or run; the only "solves" anywhere near
this lane are the mocked-dispatch runner unit tests.

---

## 0. Headline

1. **Both licensed changes are in.** `cache_key()` drops a registered field at its **frozen
   declared** default rather than the live one ((b′-1)), and the runner refuses a cached bundle
   whose stored `config.yaml` disagrees with the requesting config ((c′)). (§1, §2)
2. **The no-op is verified, not asserted.** Every one of the **170** committed `run_config.json`
   in both namespaces hashes **identically** under the old and the new drop rule — **0 moved**,
   106 forecast and 64 backcast. Both bare configs are unmoved. The check is committed and
   re-runnable. (§3.1)
3. **(c′) splits the committed population exactly as D24 priced it: 2 refused, 12 permitted.**
   Replayed over all fourteen committed shared-key groups, the rule refuses `f061b264…` (ERCOT
   §4.1) and `07e416f3…` (NEISO §4.2) and permits the other twelve. Strict (c) refuses 14/14.
   (§3.2)
4. **The append-only guard is validated against real history.** Run against the R-A commit's own
   base, new check 4 catches that flip as a ledger EDIT — i.e. had it existed on 2026-08-31 it
   would have forced the flip to be *appended*, which is precisely what would have separated the
   NEISO pair. (§3.3)
5. **A live, unrelated defect of the same family was found in passing and is ROUTED, NOT FIXED.**
   `caiso_offer_surface_measured_ungrounded` landed at `aebeb60e` (caiso-231) **unregistered**, so
   the default cache key has already moved `603c2498bf71d21d` → `7a57fadff595ca83` on main and
   13 pinned-key tests are RED at HEAD. They are red identically with and without this lane's
   diff. (§5)
6. **What this deliberately does NOT do:** it does not separate the two existing collisions, does
   not re-key anything, and does not touch a bundle, sidecar, board, keeper, shard or marker.
   (§4)

---

## 1. (b′-1) as landed — the drop reads the DECLARED default

`ScenarioConfig.cache_key()` previously dropped a `_CACHE_KEY_OPTIONAL_FIELDS` member when it
equalled `getattr(ScenarioConfig(), name)` — **the live default, recomputed on every call**. It now
compares against `cache_key_drop_defaults()`, the `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` ledger
evaluated once per process.

**What that buys.** After a default flip, a config sitting at the NEW default no longer equals the
frozen declaration, so it enters the hash and takes its own key: the post-flip run can no longer be
served the pre-flip bundle. The useful inverse is untouched — an EXPLICIT old value still equals
the declaration, is still dropped, and still addresses the pre-flip bundle, which is correct (same
posture, same bundle).

**Append-only, and how a flip is declared now.** `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` is an
append-only record: a new field adds a line, an existing line is never edited while the field
lives, and a line disappears only with its field (rule 26 `[R-DELETE]`, which parks the value in
`_CACHE_KEY_RETIRED_FIELDS`). A flip is declared by appending to the new
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` — `(date, field, new default source text)`, empty at the
re-baseline. Guard check 3 compares the live default against the newest appended declaration, so a
flip still cannot land silently; the frozen drop value it must not disturb stays put. New **check
4** (`--base`, so it runs on every PR in CI) fails any EDIT or unjustified removal.

**Resolution mechanics.** The ledger stores source TEXT so the guard can compare it
`ast.unparse`-normalized. `_resolve_declared_default` evaluates it: `ast.literal_eval`, plus the one
non-literal form the ledger carries (`field(default_factory=lambda: <literal>)`,
`federal_ces_eligible_fuels`). All 218 entries resolve; an unresolvable one would fall back to the
live default, be recorded in `_CACHE_KEY_UNRESOLVED_DECLARED_DEFAULTS` and trip a test — the
fallback exists so a malformed ledger entry can never kill every solve in the program, not as an
accepted state.

**This is (b′-1), not (b′-2).** The comparison is re-baselined at **today's** declarations, never
at each field's registration-time default. That variant moves 98/99 forecast and 63/63 backcast
keys, and was not licensed.

## 2. (c′) as landed — the seam refuses a disagreeing bundle

`runner.py`'s year loop (the `is_cached(iso, cache_key, year)` call D24 §7 names) now asks
`cache.cache_config_disagreements(iso, cache_key, year, config)` before serving. A disagreement is
a **logged cache MISS naming the differing fields, then a re-solve** — never an exception, per the
`assert_cache_key_uncontaminated` precedent's placement (owner decision D-11) and deliberately
unlike its tone: a run must not die because a stale bundle exists.

The rule, verbatim from the ruling: refuse on any **differing COMMON field**, or on a field
**ABSENT from the stored config** whose requested value is not that field's **registration-time
default**.

That second clause needs the *registration-time* value, which for the seven flipped fields is no
longer their declaration: both R-A fields are declared `True` today, so comparing against the
declaration would let D24 §4.2 — the collision that actually motivated the ruling — walk straight
through. `_CACHE_KEY_REGISTRATION_TIME_DEFAULTS` records the original default for exactly those
seven fields (D24 §2's four flip events, the complete measured set for the window that strictly
contains every committed forecast run). It is read **only** by `registration_time_default`, i.e.
only by this check; it reaches no hash. It does not grow: a flip from here on appends to the flips
ledger and leaves the frozen declaration alone, so the declaration REMAINS the registration-time
value.

**Three cases are deliberately not disagreements**, each because refusing would cost re-solves
without protecting anything:

| case | why permitted |
|---|---|
| no stored `config.yaml` | nothing to compare; every bundle `save_result` writes has one |
| a field only the STORED config has | a knob deleted under rule 26; `_CACHE_KEY_RETIRED_FIELDS` already re-inserts its value into the key |
| checkout-absolute paths | folded to sentinels on both sides exactly as the key folds them |

## 3. Verification

### 3.1 The zero-key-move merge gate — 0 of 170

`scripts/probes/capxd24r_cache_key_no_op_check.py` applies **both** drop rules to the same
committed `scenario_config` payload (everything downstream — retired-field re-insertion, path
folding, `json.dumps(sort_keys=True)`, `sha256[:16]` — is shared), so the comparison isolates the
drop rule and nothing else. Record committed at
`docs/handoffs/capxd24r-cache-key-no-op-record.json`.

```
checked 170 committed run configs (backcast: 64, forecast: 106)
  bare forecast: 7a57fadff595ca83 -> 7a57fadff595ca83
  bare backcast: 1d82ebcc9666278d -> 1d82ebcc9666278d
ok: 0 of 170 keys moved — (b′-1) is a no-op on every committed run
```

The result is not luck, and the probe is belt to the braces: guard check 3 already forces
`declared == live` for all 218 registered fields, measured directly this session as
`live != declared: 0`. The two rules are therefore the same mapping today, for **every** config
and not only the committed ones. **Any** key move would have meant (b′-2) had been implemented,
and would have stopped the lane.

(The keys printed are not the runs' recorded keys and are not meant to be: `ScenarioConfig` has
grown since each was solved. D24 §1.1 already did the historical reproduction, 94/98.)

### 3.2 (c′) over the committed shared-key groups — 2 refused, 12 permitted

`tests/unit/results/test_cache_config_agreement.py::CommittedSharedKeyGroupsTest` groups all 99
keyed committed run records by recorded key (14 multi-member groups), compares oldest-as-stored,
and restricts the requesting side to fields this codebase still has (a run today cannot ask for a
field that no longer exists; three groups span a knob added and later deleted between their
solves).

| group | verdict | on |
|---|---|---|
| `f061b2646bfaac8b` (ERCOT `d12c-armed` / `d4m`) | **REFUSED** | `storage_entry_availability_gate`, `storage_entry_cost_normalized_rank` |
| `07e416f3f8072e7c` (NEISO `capxd14` / `rcrepair`) | **REFUSED** | the same pair, in the absent-vs-armed form |
| the other 12 groups | permitted | — |

This reproduces D24 §4.5 and §7's (c′) row independently, and is the measurement that says (c′)
rather than strict (c) is the right shape.

### 3.3 Check 4 against real history

Run against the R-A arming commit's own base, the new append-only check reports:

```
_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS entr(y/ies) changed in this PR; the ledger is APPEND-ONLY:
  storage_entry_availability_gate: False -> True (EDITED)
  storage_entry_cost_normalized_rank: False -> True (EDITED)
```

That commit is the one that created the §4.2 collision. Had check 4 existed, the flip would have
had to be appended, the frozen declarations would have stayed `False`, and `rcrepair` would have
taken its own key.

### 3.4 Test inventory and suite state

| test | covers |
|---|---|
| `tests/unit/config/test_cache_key_declared_default_drop.py` (20 tests) | the simulated flip colliding under the live-default rule and separating under the declared one; the explicit-old-value inverse; every declaration resolving; declared == live where no flip is declared; both bare keys unmoved; `registration_time_default`; the append-only rules (edit → breach, add → clean, remove-with-field → breach, remove-with-deletion → clean); check 3 reading an appended flip |
| `tests/unit/results/test_cache_config_agreement.py` (10 tests) | §4.1 refused, §4.2 refused, inert schema growth served, stored-only field ignored, no-sidecar served, yaml round-trip not a difference, the 14-group replay |
| `tests/unit/pipeline/test_runner.py::TestCachedBundleConfigCheck` | the seam end-to-end on the mocked runner: a doctored sidecar forces a re-solve and logs the field; an agreeing sidecar is still served; `save_result` restores servability |
| `scripts/check_cache_key_registration.py` | green at HEAD (checks 2+3) and with `--base origin/main` (checks 1+4) |

**Suite state.** `tests/unit/config`, `tests/unit/results`, `tests/unit/pipeline`,
`tests/regression/test_persisted_identity.py`: the failure set is **byte-identical with and
without this lane's diff** (8 in `tests/unit/config`, 5 across the other two files), all of them
§5's pre-existing breakage. This lane adds 32 passing tests and breaks nothing.

## 4. What deliberately remains OPEN

1. **The two historical collision pairs stay unseparated.** `f061b264…` and `07e416f3…` still
   carry two postures each. Separating them retroactively is (a) or (b′-2), whose measured price
   is every on-disk cache in both lanes, keepers included — the owner's call, not this lane's.
   Nothing was annotated, re-keyed or re-registered.
2. **The provenance question D24 §5 and §9.3 reported is untouched.** `cache_epoch` / `cache_key`
   remains non-identifying in **both** directions: two postures at one key (§4.1, §4.2, now
   *unservable* but still indistinguishable as a provenance stamp), and one posture at two keys
   (§4.4, the `ff-t3-neiso-golden` pair with byte-identical `scenario_config` and different keys,
   plus four fc6 arms whose keys are unreproducible from their own configs). (c′) closes the
   **serving** half of the hazard; it closes none of the **reading** half. D24 §9.3's guidance
   stands: do not quote `cache_epoch` as a config-identity field.
3. **D24 §6's NEISO verdict linkage is the NEISO crossover lane's**, per the charter. Not read,
   not annotated, not acted on here.
4. **Two accepted false-positive classes in (c′)**, both costing a re-solve and never a wrong
   answer, both documented at the function: a bundle whose `config.yaml` was written from a
   **differently-rooted checkout** (its raw absolute paths do not fold to this checkout's
   sentinels), and a field the requester carries that **this codebase cannot reason about**
   (unknown default ⇒ refuse). Neither is reachable on the shipped runtime path.
5. **One stated limit on `_CACHE_KEY_REGISTRATION_TIME_DEFAULTS`:** a field registered before
   2026-07-26 whose default moved before that date would be missing from it. D24's measurement
   did not reach behind that boundary, and this lane ran no new history sweep.
6. **No cache-epoch ledger entry is owed, and none was written.** The ledger records *same-key
   invalidations* — behaviour changes that leave keys unmoved. (b′-1) moves no key and changes no
   solve; (c′) can only convert a would-be hit into a re-solve, which yields the same dispatch or
   a more correct one. The `results/cache.py` module docstring gains one paragraph saying the key
   is no longer the only thing between a config and a bundle, and that the ledger stays
   load-bearing for everything a stored config cannot see.

## 5. ROUTED, not fixed — main's default cache key has already moved

Found while establishing this lane's baseline, unrelated to it, and left alone:

* **`caiso_offer_surface_measured_ungrounded` (commit `aebeb60e`, caiso-231) was added to
  `ScenarioConfig` without a `_CACHE_KEY_OPTIONAL_FIELDS` registration.** The shipped guard's
  check 1 reports it against that commit's own base. Consequence, exactly as the guard's docstring
  predicts: the default key moved **`603c2498bf71d21d` → `7a57fadff595ca83`** and the backcast key
  `e027bc248c93c835` → `1d82ebcc9666278d`, orphaning every on-disk cache in both lanes.
* **13 tests are RED at HEAD because of it** — three in `tests/regression/test_persisted_identity.py`
  (both pins plus the path-invariance check), eight in `tests/unit/config` (the per-ISO
  "arming moves the key and not the pin" tests), one in
  `tests/unit/pipeline/test_forecast_xyear_warmstart_flag.py`, and four in
  `tests/unit/results/test_export.py`. All 13 fail identically on a clean `origin/main` checkout.
* **Not repaired here.** The remedy is the guard's one-line one (register the field, declare its
  default) — but landing it moves the key *again*, which is a keyed-identity decision belonging to
  the caiso-231 lane and the director, and this lane is licensed for (c′) + (b′-1) and nothing
  else. Registering it would also collide with whatever lane is currently editing that ledger.
  **Routed as: caiso-231's registration debt, live on main, blocking 13 tests.**

## 6. Governance and scope

- **Rule 28 `[R-MECH-MATRIX]` NOT triggered.** Cache plumbing is not a mechanism: no
  `ScenarioConfig` field added, moved or re-defaulted, no CLI flag, no matrix row, no shard
  edited. (The CI matrix guard's `ScenarioConfig`-field check has nothing to see — the diff adds
  none.)
- **Zero solves.** No LP built or run; no `--out-dir`, no bundle, no registration.
- **No committed bundle, sidecar, registry, board, verdict, keeper, shard or marker touched.**
  `results/` was read only (170 `run_config.json`, as a measurement population). The backcast
  namespace is untouched; the forecast namespace is untouched.
- **Rule 22 `[R-HOLDOUT]`:** no holdout year solved, scored or registered; nothing read here is
  year-scoped.
- **Rule 25 `[R-ISO-SCOPE]`:** no ISO-scoped parameter, file or cell written. The defect and its
  repair span ISOs because the cache path does.
- **Rule 24 `[R-REGISTRY]`:** no tunable added; the two new module constants are hash-side ledgers
  and a serving check, neither settable nor solve-affecting.
- **Rule 27 `[R-PUSH]`:** `scenarios.py` (15,367 → 15,617 lines) and `runner.py` (4,538 → 4,566)
  are ≥300-line core files. Both were edited **locally** with the Edit tool and pushed as exact
  on-disk bytes over `git push` on a freshly-fetched base; blob verification against the pushed
  refs is recorded in §7.
- **No GitHub Actions workflow added.** CI picks up check 4 through the existing
  `check_cache_key_registration` step, which already passes `--base`.

## 7. Files changed

| file | change |
|---|---|
| `src/market_sim/config/scenarios.py` | drop against the declared default; the flips ledger; `_CACHE_KEY_REGISTRATION_TIME_DEFAULTS`; `_resolve_declared_default` / `cache_key_drop_defaults` / `registration_time_default` |
| `src/market_sim/results/cache.py` | `cache_config_disagreements` + the pure `config_disagreements`; `_comparable`; one docstring paragraph |
| `src/market_sim/runner.py` | the (c′) refusal at the `is_cached` seam |
| `scripts/check_cache_key_registration.py` | check 3 reads the appended flip; new check 4 (append-only); `_declared_flips`, `_retired`, `append_only_violations` |
| `scripts/probes/capxd24r_cache_key_no_op_check.py` | the merge gate (new) |
| `docs/handoffs/capxd24r-cache-key-no-op-record.json` | its committed record (new) |
| `tests/unit/config/test_cache_key_declared_default_drop.py` | (b′-1) + append-only (new) |
| `tests/unit/results/test_cache_config_agreement.py` | (c′) + the 14-group replay (new) |
| `tests/unit/pipeline/test_runner.py` | `TestCachedBundleConfigCheck` |

### 7.1 Rule-27 blob verification

One commit (`0ee0542a`) on a base freshly fetched from `origin/main` (`3c1f9642`), pushed over
`git push`; every edited file was written locally with the Edit tool, never regenerated from
response content. Each pushed blob fetched back and compared to the on-disk bytes — line count and
content hash, `sha256` truncated to 16 hex:

| file | local | remote | verdict |
|---|---|---|---|
| `src/market_sim/config/scenarios.py` | 15,617 L / `b86324bcedfebce2` | 15,617 L / `b86324bcedfebce2` | MATCH |
| `src/market_sim/runner.py` | 4,566 L / `828a50f07b7f7269` | 4,566 L / `828a50f07b7f7269` | MATCH |
| `src/market_sim/results/cache.py` | 917 L / `79cb10385ae21989` | 917 L / `79cb10385ae21989` | MATCH |
| `scripts/check_cache_key_registration.py` | 442 L / `86f756cff25380a8` | 442 L / `86f756cff25380a8` | MATCH |
| `tests/unit/pipeline/test_runner.py` | 1,099 L / `d9af6a6375edaa40` | 1,099 L / `d9af6a6375edaa40` | MATCH |

No file shrank; every change is additive apart from the nine-line `cache_key` drop loop and the
one-line `is_cached` conditional.
