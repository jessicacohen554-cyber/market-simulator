# FINDING — audit records v33: three instrument readings that do not match the dispatch

**Lane:** audit records v33 (Model Audit & Release-Finalization Program), records only.
**Pin:** `144eabe3` (PR #4904). Director pin `a22afd02` (00:08Z); main read `eb8ae4db`
(#4876) at 00:12Z. Window `a22afd02..144eabe3` = 34 commits, 14 merges.
**Date:** 2026-09-06, ~00:20–00:35Z.
**Scope:** records only — no solve, no score, no registration, no keeper shard, no
marker, no freeze file, no matrix shard, no workflow, no `program-status.json`, no
`status/*.js`, no `results/calibration/`, no `CLAUDE.md`.

The v33 dispatch carries a STANDING TEST: *"for every claim this dispatch makes, open
the cited artifact and check it."* Almost every claim checked out and is recorded in the
board and plan entries. **Three did not**, and each is a reading about an *instrument*
rather than about the model. They are collected here so a later lane can find them
without reading the board block.

None of the three is a correction of the director. All three of the director's readings
were taken 23:55–00:12Z; these were taken 00:20–00:35Z, after 34 commits landed. The
value of stating them is that in two of the three cases the *right next action changes*.

---

## 1. The ERCOT/2022 bench part is not stale — it is stamped in a **retired scheme**

**The dispatch says:** Y-15's third item is an "ERCOT/2022 bench re-stamp conditional on
an AST-equality check."

**Measured at `144eabe3`:** the condition cannot be evaluated, because the two values
are not commensurable.

| reading | value |
|---|---|
| `frontend/data/backcast/bench/ERCOT/2022.json.gz` → `meta.builderFingerprint` | **`b2f21b9a00d3`** |
| `bench/ERCOT/{2023,2024,2025}.json.gz` | **`4254168edcfe`** (all three) |
| `scripts.lib.bench_stamp.builder_fingerprint()` at HEAD | **`4254168edcfe`** |
| R-AS landed (hash the **AST**, not the bytes) | `3d0fd19d` / `404f1908`, **2026-09-05 22:34:10Z** |
| ERCOT/2022 part **ADDED** (`git log --diff-filter=A`) | `f1561c2d`, **2026-09-05 23:24:54Z** |

`scripts/lib/bench_stamp.py`'s own module docstring computes the R-AS counterfactual and
names the value, verbatim:

> ``677b605a^``/``677b605a`` (the comment reword) hash **identically**
> (``96e5860ce4ec``) where the **byte hash** moved ``4e78c85427bb`` → ``b2f21b9a00d3``

So `b2f21b9a00d3` is the **retired byte-era hash**. It is not an AST fingerprint, cannot
be equal to one, and an "AST-equality check" against it is a category error rather than
a test that passes or fails.

### What it actually is

The ERCOT/2022 part was **added 50 minutes after R-AS landed** and was stamped with the
superseded scheme. That means the ercot-249/250 registration ran on a tree predating
`3d0fd19d`. Y-12's 20-part re-stamp (`404f1908`, *"re-stamp all 20 bench parts at
builder 4254168edcfe"*) **could not have covered it — the part did not yet exist.**

This is not the failure mode `bench_stamp.py` was written for. Its docstring describes a
part that "sits un-refreshed while the builder that produces it moves underneath." Here
the part is *newer* than the builder move; what moved underneath was the **stamping
scheme**, in the 50-minute gap between the scheme change and the registration.

### Consequence

- **The remedy is regeneration through HEAD's bench path, not a re-stamp.** Writing
  `4254168edcfe` onto the existing payload would assert a reproducibility the payload
  has not been shown to have.
- Until then, `check_bench_freshness.py` is correct on its own terms and every ERCOT C1
  verdict scored against 2022 is, in the gate's words, *"not reproducible from the
  builder at HEAD."*
- **Not chartered here** — this is a records lane. Y-15 item (3) is recorded as OPEN
  with its stated condition **voided** and its true remedy named.

### Generalisation worth one line

Any bundle registered from a branch whose base predates a `bench_stamp` scheme change
will carry the old scheme, invisibly, because bench parts are byte-deterministic and
show no diff. The exposure window is (scheme change → every in-flight branch rebases).
Whether that deserves a guard is the director's call, not this lane's.

---

## 2. The two remaining flip-set reds are **one object each**, and one of them is a records duty

**Measured on this lane's own newest completed `ci.yml` run whose head is in `main`:**
run **2545**, id `34000645268`, head `7f63a4b9` (PR #4894, the nyiso-196 promotion),
created 00:11:41Z, completed 00:20:12Z — newer than the director's run 2541.

| # | required job | run 2541 (director) | run 2545 (this lane) |
|---|---|---|---|
| 1 | Ruff lint + format | FAILURE | **FAILURE** (the *format* step; *lint* SUCCESS) |
| 2 | Pinned default cache key | SUCCESS | **SUCCESS** |
| 3 | Structural refactor guards | SUCCESS | **SUCCESS** |
| 4 | Cache-key registration guard | SUCCESS | **SUCCESS** |
| 5 | Fast test tier | FAILURE | **FAILURE** |
| 6 | Rule-22 quarantine gates | SUCCESS | **SUCCESS** (second consecutive green) |

**FLIP SET 4 OF 6 — unmoved.** Non-set: Rule-28 mechanism-matrix guard is **SUCCESS**
here, so the director's FAILURE at 2541 was PR-head-local (D65 fix-anchors) and the
merged tree's anchors were always right — `check_mechanism_matrix` exits 0 on `main` at
both pins.

### Red 1 — Ruff format: already fixed on `main`

The failing file is `tests/unit/model/test_ccs_retrofit.py`, fixed at **`a802936c`**
(*"Hygiene: ruff format … D65 Act A landed it unformatted; red on main"*), which is
**newer than run 2545's base**. `ruff format --check .` exits **0** at this pin across
1336 files. Run 2547 (head `8bada44b`, also in `main`) still reads FAILURE for the same
base reason. **Nothing is owed; it goes green on the first PR run based ≥ `a802936c`.**

### Red 2 — Fast test tier: one test, and it is the gate-(a) gate

Job log tail, read directly (job `101398775647`):

```
FAILED tests/scoring/test_gate_a_provenance.py::test_live_board_passes - assert 1 == 0
 +  where 1 = <function main at 0x7f5f829be340>([])
 +    where <function main at 0x7f5f829be340> = cgap.main
= 1 failed, 8305 passed, 45 skipped, 2 xfailed, 23 warnings in 430.94s (0:07:10) =
```

**One test.** It calls `check_gate_a_provenance.main` and asserts exit 0. So:

> **The Fast-tier red and the FR-21 job's red are the same object.** Both clear on one
> records act — the gate-(a) keeper re-key — and neither is a code defect.

At run 2545 that re-key is owed against **NYISO** (`2026-09-05-nyiso-192-astoria-panel`
cited; live keeper `2026-09-06-nyiso-196-extract-basis`). It is in flight in another
desk's PR **#4908**. The director's reading at 2541 saw the *same test* failing on the
**MISO** stamp, which the capx desk then re-keyed at `4d1ed3ad`.

### Consequence for R-AU, recorded and not adjudicated

R-AU's trigger is "the first 6-of-6 head." On this reading that is **one already-landed
code fix plus one records act** away. But the records act is a **per-promotion duty**,
not a backlog item: it re-opened against NYISO within 36 minutes of being closed against
MISO, and this cycle saw **four promotions in six hours** (ercot-248, miso-220,
caiso-252, nyiso-196).

**A 6-of-6 head is therefore a window between promotions, not a state the repo settles
into.** This lane proposes no mechanism and does not re-sequence R-AU; it records that
the trigger's difficulty is promotion-rate-driven and hands that to the director.

---

## 3. The session-roster instrument is incomplete — G-14 recurred

**The dispatch says:** all three sessions appear in the roster this cycle, *"the G-14
incompleteness did not recur; record the roster instrument as complete at this
reading."*

**This lane opened the instrument and could not reproduce that.**

**Step 1 — the ids, from the primary source.** `git log -1 --format=%b` on each landed
commit, reading the `Claude-Session` trailer:

```
89d2067c (v32)   → session_01GTENGKMBExeLcabVUFDhza
62144f2a (Y-13)  → session_01CdBoNqCi3x6wEkxNZCJoyL
18dadeb1 (Y-14)  → session_0136oMppo5pPih56h9qZrcZy
```

**The dispatch's three ids are exactly right**, and all three commits are in `main`.

**Step 2 — the roster.** `list_sessions(mine=true, limit=30)` returns 30 rows with
`has_more: true`; page 2 via `after_id` returns 30 more. **None of the three appears in
either page (60 rows).** Page 1 spans `created_at` 2026-09-04 23:57Z → 2026-09-06
00:23Z — **a window that contains all three** (23:20–23:40Z on 09-05).

**Step 3 — direct resolution.**

```
get_session(session_01CdBoNqCi3x6wEkxNZCJoyL) → "failed to get session: the requested resource was not found"
get_session(session_01GTENGKMBExeLcabVUFDhza) → "failed to get session: the requested resource was not found"
```

**Step 4 — the control.** This is what makes it a finding rather than a guess.
`session_013kYk23DzQwhi9SY4vv7sZJ` — status **ARCHIVED**, `created_at`
**2026-09-05T23:25:26Z**, the same minute as Y-13, same environment — **resolves
normally and in full.** So the not-found is **specific to these ids**: not pagination,
not a general property of archived sessions, not an auth boundary.

### What this does and does not say

- **It does not say the work is unevidenced.** All three landings are verified in `main`
  by sha, and every landing claim in the v33 board and plan entries stands on git alone.
- **It does not correct the director**, whose reading was taken 23:55–00:12Z and is
  recorded as theirs.
- **It does refuse** to write "the roster instrument is complete" into the record on a
  reading this lane could not reproduce. **Recorded as: G-14 recurred.**
- The standing discipline is unchanged and is the reason this costs nothing:
  **launch state is read from PRs and commits; no non-launch is classified from the
  roster alone.**

---

## Provenance of every reading above

| reading | how taken |
|---|---|
| gates | `uv run --frozen python scripts/<gate>.py`, `$?` read directly, at `144eabe3` |
| commits, dates, ancestry | `git log` / `git merge-base --is-ancestor` against `origin/main` at `144eabe3` |
| bench fingerprints | `json.load(gzip.open(...))['meta']['builderFingerprint']` on the committed parts |
| CI jobs | `mcp__github__actions_list` → `list_workflow_jobs`, run `34000645268` |
| CI log tail | `mcp__github__get_job_logs`, job `101398775647`, `return_content=true` |
| branch protection | `mcp__github__list_branches`, ~00:24Z — `main` → `protected: false`, **reading twelve** |
| roster | `mcp__Claude_Code_Remote__list_sessions` (2 pages) and `get_session` (3 ids incl. the control) |

Session ids appearing in this document are read from committed git trailers and are
recorded as identifiers, not as endorsements of any other session's conclusions.
