# PRECOMMIT — capx D79 phase 1: the solve-surface fingerprint lands frozen-hash

**Lane:** capx D79 phase 1 · **Branch:** `claude/capx-d79-p1-solve-surface-61m1oo` (fresh off
`origin/main` `e6a0402f`) · **Date:** 2026-09-06 · **DATA PROFILE:** code · **LP: ZERO.**
**Charter:** owner ruling **Q54** (capx ledger §3, r#50 amendment 1 — *"ADOPT, frozen-hash now"*),
executing `docs/handoffs/DESIGN-capx-d79-2026-09-06.md` §6 (the build spec) and §7 rows 1–5.

---

## 0. What this session ships, in one paragraph

`ScenarioConfig.cache_key()` gains a **solve-surface fingerprint**: a per-name, per-ISO-projected
value hash of the seven `SURFACE_MODULES`, each name dropped at its **frozen registration-time
hash**, plus a mechanical **scoped epoch** ledger that starts empty. A registry table that is
re-derived now re-keys the ISOs whose rows moved — the SCN-LOAD class, which until today changed
every T1-F peak while moving zero keys. Because every name is declared at its **live** hash, the
landing itself moves **nothing**: `moved_rows(iso) == {}` for all six ISOs, `SOLVE_EPOCHS == ()`,
and **0 of 148** committed run configs change key.

## 1. THE DECLARED NO-OP PREDICTION, and why its ordering carries no selection risk

**Prediction, made from the construction and not from a measurement:** `cache_key()` differs from
its pre-D79 form by exactly two *conditional* insertions —

```python
moved = moved_rows(self.iso)            # {} when every row is at its declaration
if moved: payload_dict["__solve_surface__"] = moved
ep = applicable_epochs(self)            # [] when SOLVE_EPOCHS is empty
if ep:    payload_dict["__solve_epochs__"] = ep
```

— so if `moved_rows` is empty **for every ISO string a config can carry** and `SOLVE_EPOCHS` is
empty, the payload is byte-identical for **every** config in existence, not merely for the ones
anyone thought to check. Both antecedents are properties of the two committed ledgers, not of any
run. So the prediction is **universal and falsifiable in advance**, key by key, and the measurement
below can only confirm or refute it.

**This lane has nothing to select against.** Rule 29 `[R-SCREEN]`'s ordering discipline exists so a
mechanism cannot be chosen by whether it moved a residual. D79 phase 1 solves nothing, scores
nothing, and touches no gate; the only number it can produce is "how many keys moved", whose target
(zero) was fixed by the owner's ruling before any code existed. The PRECOMMIT is therefore written
with the implementation rather than before it, and says so here rather than implying otherwise.

**Key by key, the prediction:**

| config | pre-D79 key | predicted post-D79 key |
|---|---|---|
| `ScenarioConfig()` (bare forecast) | `547053bdfccd4264` | `547053bdfccd4264` — unmoved |
| `ScenarioConfig(mode="backcast")` | `f61891696e671969` | `f61891696e671969` — unmoved |
| every committed `run_config.json` (148) | as recorded | unmoved, all 148 |
| the 14 bare keys D65-B-R Addendum C re-pinned | as pinned | unmoved |
| any config with an ISO outside the six | — | unmoved (`moved_rows(None)`, `moved_rows("SPP")`, `moved_rows("ercot")` all `{}`) |

**MEASURED (`scripts/probes/capxd79_solve_surface_no_op_check.py`, record committed at
`docs/handoffs/capxd79-solve-surface-no-op-record.json`):** 296 surface names, 296 declared, 0
undeclared, 0 solve epochs; `moved_rows` empty at all six ISOs; **148 configs checked (130 forecast,
18 backcast), 0 moved**; both bare keys reproduce exactly. **The merge gate PASSES.**

## 2. THE COLLISION CHECK — D65-B-R's in-flight batch

D65-B-R pre-declared seven solve keys and treats a realized key ≠ its pre-declaration as a **STOP**.
The charter asks this be settled by resolving those keys at HEAD before and after.

Measured this session on all six T1-F legs, resolving each leg's config through
`run_full_horizon.reference_config(...)` at HEAD and hashing it twice — once with the surface
neutralized (the pre-D79 algorithm) and once live:

| leg | pre-D79 | post-D79 | verdict |
|---|---|---|---|
| ERCOT | `fc8b3f1422c24c4d` | `fc8b3f1422c24c4d` | unmoved |
| NEISO | `af1be457c4690d49` | `af1be457c4690d49` | unmoved |
| NYISO | `06b8d7a36934dc67` | `06b8d7a36934dc67` | unmoved |
| CAISO | `d02bc50862eb7c53` | `d02bc50862eb7c53` | unmoved |
| PJM | `e814fad90184c835` | `e814fad90184c835` | unmoved |
| MISO | `d2465227d46357f6` | `d2465227d46357f6` | unmoved |

**Stated plainly so it cannot be misread later:** these six keys are **not** D65-B-R's seven
pre-declared values, and they are not supposed to be. The reconstruction above passes only
`(iso, 2026, 2050, cmc=False, golden_posture=True)` and therefore omits the batch's other recipe
flags, and **D67-ARM (owner ruling Q52) landed after the D65-B PRECOMMIT and moved PJM's forecast
recipe by itself**. What the table establishes is the only thing D79 could affect and the only
thing the collision question asks: **for every leg, post == pre.** D79 moves no key of D65-B-R's,
so the batch's STOP cannot fire on account of this PR, and its pre-declared keys hold exactly as
long as no registry row of the leg's ISO moves before it solves — which is the condition under
which those keys *should* hold, and which today nothing but this fingerprint can detect.

**Other in-flight lanes:** D78-R2 / D76-P2 / D75-R touch no cache plumbing. **`cache.py` is this
session's this window** — the module docstring and `save_result` are edited here; a concurrent
editor of that file should rebase rather than merge-resolve by hand.

## 3. WHAT IS BUILT (design §6.1, item by item)

| file | change |
|---|---|
| **NEW** `src/market_sim/config/solve_surface.py` | `SURFACE_MODULES`, `SURFACE_ISOS`, `canonical`, `row_hash`, `surface_fingerprint`, `surface_rows(iso)` (ISO-projected, `lru_cache`), `moved_rows(iso)`, `SolveEpoch` + `SOLVE_EPOCHS` (append-only, **empty**), `applicable_epochs(config)`, `surface_stamp(iso, config)`, `reset_caches` |
| **NEW** `src/market_sim/config/solve_surface_declared.py` | `DECLARED`, 296 names, generated, append-only, never hand-edited |
| `config/scenarios.py::cache_key` | +11 lines after the retired-field re-insertion, before path folding; dunder keys |
| `results/cache.py` | `save_result` writes `solve_surface.json`; module docstring gains the paragraph saying the key now sees the surface |
| `pipeline/persist.py`, `run_full_horizon.py`, `run_capacity_hindcast.py`, `results/export.py` | every site that writes `"cache_key"` also writes `"solve_surface"` |
| `scripts/lib/forecast_provenance.py` | `PROVENANCE_FIELDS += ("solve_surface",)` + `solve_surface_from`, READ from the artifact, never recomputed |
| `scripts/check_cache_key_registration.py` | checks **5** (undeclared surface name — FAILS), **6** (append-only — FAILS), **7** (a new `**Epoch` heading with no `SolveEpoch` and no KEY ADVANCE — WARNS) |
| **NEW** `scripts/solve_surface_register.py` | `--declare` / `--declare-missing`; `--diff <sha> [<sha>]`, the mechanised G-DRIFT "`constants.py` FIRST" step |
| `tests/regression/test_persisted_identity.py` | `config_identity_only` fixture on the two config pins; `PINNED_SURFACE_ROWS_BY_ISO` + its dated cause block; surface path-invariance |
| **NEW** `tests/unit/config/test_solve_surface.py`, `tests/unit/results/test_cache_solve_surface.py` | design §6.3 |
| `CLAUDE.md` | one sentence, naming the fingerprint and Q54 |

**Deliberately NOT built** (design §6.4, card rows 5–6): the WARN-level attestation guard for
forecast-evolution-path AST changes; `reserves/spec.py` / `interchange/spec.py` and the
floor-coefficient CSVs.

## 4. DISCIPLINE

* **Rule 24 `[R-REGISTRY]`** — derived, never settable. No `ScenarioConfig` field, no env var, no
  CLI flag; `--declare` writes a *declaration*, which can only ever remove a name from the key.
* **Rule 26 `[R-DELETE]`** — both ledgers append-only; a retired surface name keeps its last hash,
  and dropping its line is a check-6 breach whether or not the name still exists.
* **Rule 28 `[R-MECH-MATRIX]`** — **not triggered.** No `ScenarioConfig` field, no mechanism, no
  cell: the D24-R precedent exactly (cache plumbing).
* **Rule 27 `[R-PUSH]`** — `scenarios.py` (19,021), `cache.py` (1,367), `check_cache_key_registration.py`
  (713), `test_persisted_identity.py` (1,116) are ≥300-line files edited with the Edit tool on
  exact on-disk bytes; every push carrying one is blob-verified (§5 of the FINDING).
* **Rule 22 `[R-HOLDOUT]`** — nothing solved, scored or registered; no year touched.

**One declared deviation from the build spec.** Design §6.1 sizes `solve_surface.py` at "< 300
lines"; it lands at **406** (139 code, 183 docstring, 65 blank, 19 comment). The excess is rule-11
docstrings plus the rule-24/26 governance record, which are load-bearing here — the file is the
only place a reader learns why re-declaring a repaired table is the one wrong remedy. The
consequence is stated rather than avoided: it is a rule-27 ≥300-line file from its first commit and
gets that discipline, which this session applies to it anyway.

## 5. MERGE GATE

| gate | reading |
|---|---|
| no-op record reads 0 moved | **PASS** — 0 / 148, both bare keys reproduce |
| `tests/regression/test_persisted_identity.py` + the six surface pins | **PASS** — 23 collected, 23 passed (15 before this PR, +8: six ISO pins, the moved-rows gate, surface path-invariance) |
| `check_cache_key_registration.py --base origin/main` | **PASS** — checks 1–7 green, no check-7 WARN |
| `ruff check` / `ruff format --check` | **PASS** |
| G-DRIFT (`solve_surface_register.py --diff origin/main`) | **0 values moved, 0 added, 0 removed** — this branch changes no registry value |
