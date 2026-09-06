# FINDING — capx D79 phase 1: the solve-surface fingerprint, landed at zero key moves

**Lane:** capx D79 phase 1 · **Branch:** `claude/capx-d79-p1-solve-surface-61m1oo` (fresh off
`origin/main` `e6a0402f`) · **Date:** 2026-09-06 · **DATA PROFILE:** code · **LP: ZERO** — nothing
solved, scored or registered.
**Charter:** owner ruling **Q54** (capx ledger §3, r#50 amendment 1 — *"ADOPT, frozen-hash now"*)
over `DESIGN-capx-d79-2026-09-06.md` §6 (build spec) and §7 rows 1–5.
**PRECOMMIT:** `PRECOMMIT-capx-d79p1-2026-09-06.md`.

---

## 0. Result

**The fingerprint is in the key, and landing moved nothing.** `cache_key()` now carries a
per-name, per-ISO-projected value hash of the seven registry modules, dropped at each name's frozen
declaration, plus a scoped `SolveEpoch` ledger that starts empty. **296 surface names, 296 declared,
0 undeclared, 0 epochs; `moved_rows(iso) == {}` at all six ISOs; 0 of 148 committed run configs
change key; both bare keys reproduce to the digit.** From today a re-derived `DEMAND_GROWTH_RATES`
re-keys the ISOs whose rows moved instead of silently re-serving the pre-change bundle.

## 1. THE MERGE GATE

| gate | reading |
|---|---|
| no-op probe over every committed run config | **PASS — 0 of 148 moved** (130 forecast, 18 backcast) |
| bare forecast key | `547053bdfccd4264` → `547053bdfccd4264` |
| bare backcast key | `f61891696e671969` → `f61891696e671969` |
| `moved_rows` at each ISO | `{}` × 6; also `{}` for `None`, `"SPP"`, `"ercot"` |
| `tests/regression/test_persisted_identity.py` incl. the six surface pins | **PASS — 23/23** (15 before this PR) |
| `check_cache_key_registration.py --base origin/main` (checks 1–7) | **PASS**, no check-7 WARN |
| `check_mechanism_matrix.py --base origin/main` | **rc 0** (no `ScenarioConfig` field added) |
| `ruff check .` / `ruff format --check .` | **PASS** (1,376 files) |

Record: `docs/handoffs/capxd79-solve-surface-no-op-record.json`
(`scripts/probes/capxd79_solve_surface_no_op_check.py`).

**Why zero was predictable rather than lucky.** `cache_key()` differs from its pre-D79 form by two
*conditional* insertions, each guarded on emptiness. With every name declared at its live hash and
`SOLVE_EPOCHS` empty, neither antecedent can hold for **any** config — so the no-op is a property of
the two ledgers, not a sample over 148 files. The 148 are corroboration, not the argument.

## 2. THE CONSTRUCTION REPRODUCES THE INCIDENT IT WAS DESIGNED AGAINST

`scripts/solve_surface_register.py --diff` over the SCN-LOAD merge, run this session:

```
solve surface ad45b0e4^1 -> ad45b0e4
  286 -> 286 names; 3 value(s) moved, 0 added, 0 removed
  MOVED — each row below re-keys the ISOs named:
    DATACENTER_ADDITIONS_MW: CAISO, ERCOT, MISO, NYISO, PJM
    DEMAND_GROWTH_RATES:     CAISO, ERCOT, MISO, NEISO, NYISO, PJM
    ELECTRIFICATION_LAYERS:  ERCOT, NEISO, NYISO
  per-ISO totals: ERCOT 3, CAISO 2, MISO 2, PJM 2, NYISO 3, NEISO 2
```

Design §3 predicted *"catch — 3 names, all 6 ISOs (`DEMAND_GROWTH_RATES` every row;
`DATACENTER_ADDITIONS_MW` 5 rows; `ELECTRIFICATION_LAYERS` 3 rows)"*. **Row for row, that is what the
built code says.** The memo's arithmetic and the implementation are independent, so this is a real
check on both.

And the half that makes it affordable, on three recent registry merges:

| merge | names | value moved | added | keys moved |
|---|---|---|---|---|
| D75-R `4b4df964` (PJM VRE ELCC) | 294 → 296 | 0 | 2 | **0** |
| SCN-WS3b `29e039a3` (voluntary demand) | 287 → 294 | 0 | 7 | **0** |
| SCN-FIX2 `b57ab797` (carbon relabel) | 294 → 294 | 0 | 0 | **0** |

Nine table additions across three merges, zero key moves — the failure mode a naive whole-surface
hash has (§4.1's 25-of-51 addition-only merges re-keying the program) does not occur here.

**G-DRIFT for this branch:** `--diff origin/main` reads *0 values moved, 0 added, 0 removed*. This
PR changes no registry value.

## 3. THE COLLISION CHECK — D65-B-R

For all six T1-F legs, resolved at HEAD through `run_full_horizon.reference_config` and hashed twice
(surface neutralized = the pre-D79 algorithm, then live):

| leg | pre-D79 | post-D79 |
|---|---|---|
| ERCOT | `fc8b3f1422c24c4d` | `fc8b3f1422c24c4d` |
| NEISO | `af1be457c4690d49` | `af1be457c4690d49` |
| NYISO | `06b8d7a36934dc67` | `06b8d7a36934dc67` |
| CAISO | `d02bc50862eb7c53` | `d02bc50862eb7c53` |
| PJM | `e814fad90184c835` | `e814fad90184c835` |
| MISO | `d2465227d46357f6` | `d2465227d46357f6` |

**post == pre, 6/6.** Said plainly so it is not misread: these are **not** D65-B-R's seven
pre-declared values, and are not meant to be — the reconstruction passes only
`(iso, 2026, 2050, cmc=False, golden_posture=True)`, omitting the batch's other recipe flags, and
D67-ARM (Q52) landed after that PRECOMMIT and moved PJM's forecast recipe on its own. The table
answers the only question D79 can affect: **this PR moves no key of that batch's**, so its STOP
cannot fire on account of it. Its pre-declared keys hold exactly as long as no registry row of the
leg's ISO moves before it solves — the condition under which they *should* hold, and which nothing
before this PR could detect. D78-R2 / D76-P2 / D75-R touch no cache plumbing.

## 4. WHAT IS NOW TRUE THAT WAS NOT

1. **A registry value change re-keys, scoped.** Per name, per ISO row, per ISO token; a shared table
   reaches all six. `results/<ISO>/<key>/` bundles solved on the old value stay addressed by their
   own key and are simply not served to the new one.
2. **An addition costs nothing.** A new table is declared at its live hash in the PR that adds it
   (guard check 5 makes that mandatory and one command), so it moves no key.
3. **A revert restores the old key**, because it is the same model.
4. **Every bundle says what it solved on** — `solve_surface.json` beside `config.yaml`, and a
   `solve_surface` block beside every recorded `"cache_key"` in `run_config.json`, `meta.json`,
   the full-horizon summary, the export payload and the forecast provenance stamp (read from the
   artifact, never recomputed, so a run scored before today keeps its historical stamp).
5. **A code-level invalidation can be declared mechanically and in scope** — a `SolveEpoch` with
   `modes` / `isos` / `reaches_year`, so a forecast-only entry never touches a backcast keeper's
   key. The ledger starts empty by ruling Q54 row 4: D77's 2026-09-06b entry stays prose because the
   D65-B-R batch is its re-solve.
6. **The G-DRIFT "`constants.py` FIRST" step is mechanised** — `--diff <sha>` names the moved rows
   and the ISOs each reaches, in seconds and with no LP.

**What is still NOT true, stated at the gate.** The D55 class — a behaviour change with no value and
no field behind it — remains invisible; nothing short of a source-tree hash sees it, and that hash
fires on 207 of 225 merges (design §4.2). The §6.4 attestation guard that would make the *existence*
of a G-DRIFT audit mechanical is **not built** (card row 5, priced by the owner later), and
`reserves/spec.py` / `interchange/spec.py` / the floor-coefficient CSVs are out of scope (row 6).

## 5. RULE 27 `[R-PUSH]` — blob verification

Four ≥300-line files were edited with the Edit tool on exact on-disk bytes; none was rewritten from
regenerated content. Line counts and SHA-256 of the pushed blob vs local, fetched back after the
push:

| file | lines | local sha256[:16] | remote sha256[:16] | |
|---|---|---|---|---|
| `src/market_sim/config/scenarios.py` | 19,021 | `65aa887fdae3c9a3` | `65aa887fdae3c9a3` | ✓ |
| `src/market_sim/results/cache.py` | 1,367 | `005d519f0c5ed617` | `005d519f0c5ed617` | ✓ |
| `scripts/check_cache_key_registration.py` | 713 | `31784a9a0830782f` | `31784a9a0830782f` | ✓ |
| `tests/regression/test_persisted_identity.py` | 1,116 | `60bf321b3fe12ebd` | `60bf321b3fe12ebd` | ✓ |
| `src/market_sim/config/solve_surface.py` (new) | 406 | `7b382371ca38a5d3` | `7b382371ca38a5d3` | ✓ |
| `src/market_sim/config/solve_surface_declared.py` (new) | 577 | `938118be9fcd190f` | `938118be9fcd190f` | ✓ |
| `scripts/solve_surface_register.py` (new) | 269 | `8e977494f68b8b55` | `8e977494f68b8b55` | ✓ |

Every blob byte-identical to local. The remote side is read back with
`git fetch origin <branch>` + `git cat-file -p` on the tree the remote ref points at, so the
comparison is against what the server stores, not against the local push buffer.

## 6. TEST SWEEP, and the 12 failures that are NOT this PR's

`tests/unit/config` + `tests/unit/results` + `tests/regression`: **1,527 passed, 27 skipped, 12
failed** (251 s). The same 12 fail on the unmodified tree — measured this session by stashing every
tracked edit and re-running them (`12 failed, 34 passed`), an identical set:

* **11** are the `DATA PROFILE: code` environment: `data/clean/confirmed-retirements/...` is derived
  and gitignored, so `confirmed_exits_enabled` refuses to degrade silently
  (`tests/unit/results/test_export.py` ×4, `tests/regression/test_soundness.py` ×7).
* **1** is pre-existing on `main`: `test_constants_facade.py::test_moved_surface_is_complete` — D75-R
  added `PJM_SOLAR_CLASS_MIX_FIXED_TILT_SHARE` and `RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO` to
  `capacity_market.py` without the facade re-export. **Reported, not fixed here** (out of scope, and
  it belongs to the lane that added the names). It is worth noting that the surface fingerprint sees
  both names regardless of the facade, so this gap does not affect anything above.

## 7. DECLARED DEVIATION FROM THE BUILD SPEC

Design §6.1 sizes `config/solve_surface.py` at "< 300 lines". It lands at **406** — 139 code, 183
docstring, 65 blank, 19 comment. The excess is rule-11 docstrings plus the rule-24/26 governance
record, and the file is the only place a reader learns why re-declaring a repaired table is the one
wrong remedy. The consequence is taken rather than dodged: it is a rule-27 ≥300-line file from its
first commit and carries that discipline (edit-only, blob-verified), which this session applied to
it anyway. No other item of §6.1–§6.3 is reduced, and nothing in §6.4 was built.

## 8. GOVERNANCE ATTESTATION

| gate | reading |
|---|---|
| LP | **zero** — no solve, no bundle, no `--out-dir`, no `--year` |
| rule 22 `[R-HOLDOUT]` | nothing year-scoped solved, scored or registered |
| rule 24 `[R-REGISTRY]` | the fingerprint is DERIVED — no `ScenarioConfig` field, no env var, no CLI flag; `--declare` writes a declaration, which can only ever take a name OUT of the key |
| rule 25 `[R-ISO-SCOPE]` | the projection keeps each ISO's key sensitive to its own rows; nothing transferred (pinned by `test_another_isos_key_is_untouched_by_a_MISO_row`) |
| rule 26 `[R-DELETE]` | both ledgers append-only; a retired surface name keeps its last hash, and dropping its line is a check-6 breach whether or not the name still exists |
| rule 27 `[R-PUSH]` | §5 — four ≥300-line files edited, never rewritten; blobs verified after push |
| rule 28 `[R-MECH-MATRIX]` | **not triggered** — cache plumbing, no mechanism, no cell (the D24-R precedent); `check_mechanism_matrix --base` rc 0 |
| rule 29 `[R-SCREEN]` | no arm, no screen, no gate to select against; G-DRIFT for this branch reads 0 rows moved |
| CI | checks 5–7 ride the existing `check_cache_key_registration` step — **no new workflow** (CLAUDE.md "never offload work to CI") |
