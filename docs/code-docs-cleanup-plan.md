# Code & Documentation Cleanup Plan — market-simulator

> Status: SUPERSEDED-BY docs/refactor-consolidation-plan-2026-07.md — executed; folded into the consolidation charter.

Sibling to [`data-reorg-plan.md`](data-reorg-plan.md). That plan owns the **data**
reorg (raw/clean split, schemas, curation); this one owns **code** and
**documentation** hygiene. They run in parallel sessions and touch mostly
disjoint trees — the one shared seam is `scripts/lib/` (see Coordination).

---

## Where we are (status)

The data reorg is partway through its own waves:

| Wave (data-reorg-plan) | Status |
|------------------------|--------|
| **W0** Central path registry (`config/paths.py`) | ✅ done |
| **W1** Physical relocation `inputs/` → `data/raw/` | ✅ done |
| **W2** Schema + dictionary + `scripts/lib/clean_io.py` | ⬜ separate session |
| **W3** Per-datatype curation → `data/clean/` | ⬜ separate session |
| **W4** Loader cutover → `data/clean` | ⬜ separate session |
| **W5** Dedup, prune, finalize dictionary | ⬜ separate session |

Code/doc quick wins already landed (commit `cleanup: prune orphan
data/eia_hourly + repoint stale inputs/ path refs`):

- **Pruned** the orphaned `data/eia_hourly/` duplicate (the loader reads
  `data/raw/eia-930-hourly/`; those 3 files were read by nothing).
- **Repointed** every stale `inputs/…` path reference across `src/`, `scripts/`,
  `tests/` to its `data/raw/…` home. In `src/` these were docstrings only
  (behaviour-preserving); in `scripts/` several were **live code-path literals
  broken since W1** (`derive_ercot_zonal_lmp`, `derive_interface_limits`,
  `derive_cc_capacity_reconcile`, `score_nyiso_ttc_run`, `process_f923_fuel_costs`,
  …) and now resolve to existing files.

What remains is everything below.

---

## Scope of this plan

**In scope:** `scripts/` organization, Python hygiene (lint/format/dead code,
routing remaining script paths through `config.paths`), and the documentation
debt (README, `claude.md`, `market-sim-build-plan.md`, `requirements.txt` vs
`pyproject.toml`, empty `context/`, root-level clutter, prose still describing
the old `inputs/` layout).

**Out of scope (owned by `data-reorg-plan.md`):** anything under `data/`, the
schema/dictionary scaffold, curation scripts, loader cutover.

**Known issues to leave alone:** 4 pre-existing `test_eia_loader` failures
(CAISO/NYISO zonal-share fallback) fail identically on a clean tree — a data
fixture quirk, not a code-cleanup target. Note them; do not "fix" by editing
the fallback logic.

---

## Coordination with the data reorg

The only collision risk is **`scripts/lib/`**: data-reorg **W2** creates
`scripts/lib/clean_io.py`, and this plan's **Track C1** creates
`scripts/lib/` for shared helper modules. Resolution:

- Whichever session creates `scripts/lib/__init__.py` first, the other rebases
  onto it. Treat `scripts/lib/` as an additive, shared namespace — no session
  deletes or renames another session's module there.
- Track C1 must **not** touch any `data/` path or loader (that's W4); it only
  relocates helper *modules* and fixes their import sites.

---

## The two tracks

```
Track C — Code           Track D — Documentation
  C1 scripts/ reorg        D1 entrypoint docs (README/quickstart, requirements)
  C2 python hygiene        D2 reconcile in-repo prose to current reality
  (C3 frontend/dashboard   (D3 methodology/spec sync via /sync-docs)
      investigation)
```

C1→C2 are mildly ordered (reorg before lint so lint sees final paths). D1, D2,
C1 are independent and can run in parallel. D3 (`/sync-docs`) runs **last**,
after the data cutover (W4) and C1/D2 have settled, so it documents the final
state once rather than twice.

| Step | Parallel with | Gate |
|------|---------------|------|
| **C1** scripts/ reorg | D1, D2 | — |
| **C2** python hygiene | D1, D2 | C1 merged |
| **C3** frontend/dashboard probe | anything | — (investigation only) |
| **D1** entrypoint docs | C1, C2 | — |
| **D2** prose reconciliation | C1 | — |
| **D3** `/sync-docs` final pass | — | data W4 + C1 + D2 done |

---

## Grounded findings (what each task is fixing)

### scripts/ (106 files, 24 `_`-prefixed)
`_`-prefix here means **private/helper**, *not* throwaway — several are imported
by other scripts and/or cited across docs, so they must be **moved, not
deleted**, with references updated:

- **Shared helper modules** (imported by other scripts, belong in `scripts/lib/`):
  `_bundle_io.py` (also imported by `tests/test_bundle_io.py`),
  `_zonal_sufficiency.py` (imported by `neiso_/nyiso_/caiso_zonal_sufficiency.py`),
  `_session_score.py` and `_reldeploy_zonal_report.py` (imported by
  `_reldeploy_compare.py`), `_pjm_aswh_merge.py` + `_pjm_interchange_ab.py`
  (imported by the `_pjm_*` run chain), and the large shared `_backcast_shell.py`
  (cited across `CHANGELOG.md`, `docs/`, and the `calibration-report` skill).
- **One-off investigation probes** (run manually, cited only by docs/results):
  the `_caiso_*` set (7), `_pjm_*_run/_probe/_score/_refprice/_refconvex/_coopt`,
  `_dam_offer_compare.py`, `_neiso_probe_compare.py`. Keep them (they're the
  reproducible record behind committed findings) but corral them out of the
  top-level namespace.
- **~80 pipeline scripts** (`build_/derive_/fetch_/process_/analyze_/render_`)
  stay where they are — they're the real data/result pipeline.

### Documentation / config debt (verified)
- `README.md` is **15 lines with zero install/run/usage** instructions.
- `requirements.txt` lists only `requests` + `openpyxl` — a **stale partial
  subset**; the real dependency set lives in `pyproject.toml` (`highspy`,
  `numpy`, `scipy`, `pandas`, `pyarrow`, `pydantic`, `pyyaml`). The repo builds
  with `uv` (`uv.lock`). `requirements.txt` is referenced only by the data plan.
- `context/` is **empty** (`.gitkeep` only) yet referenced as if populated.
- **Root clutter:** 7 `.md` + 3 `.html` at repo root. `offer-curve-grounding.html`
  is referenced by nothing (orphan candidate); `index.html` →
  `model-updates.html` form a small GitHub-Pages landing site.
- `market-sim-build-plan.md` and `claude.md` still describe the pre-W1 `inputs/`
  data layout; `CHANGELOG.md` and many `docs/*.md` reference old `inputs/…`
  paths in prose (in-code refs are already fixed).

### frontend/ vs dashboard/ (investigate, don't assume)
Two parallel web trees exist (`frontend/{js,css,data}`, `dashboard/{js,styles}`).
Whether they overlap, supersede each other, or serve different surfaces (the
calibration dashboard vs the learning-hub site) is **unverified** — C3 is a
scoping probe, not a refactor.

---

## Verification (every step)

- `uv run python -m pytest -q` — the suite must stay green **except** the 4
  known-pre-existing `test_eia_loader` fallback failures (assert the count
  doesn't grow).
- `uv run ruff check .` and `uv run ruff format --check .` — clean after C2.
- After C1: `uv run python -m pytest tests/test_bundle_io.py -q` and a grep that
  every moved helper's new import path resolves
  (`grep -rn "from scripts.lib" scripts/ tests/` returns only valid modules; no
  stale `import _bundle_io` / `import _zonal_sufficiency` remain).
- After D2: `grep -rn "inputs/raw-data\|inputs/processed\|inputs/calibration"
  *.md docs/ claude.md` returns only intentional historical references.

---

## Session prompts (copy-paste into fresh sessions)

> Each prompt is self-contained. C1, D1, D2 can run in parallel; C2 after C1;
> D3 last. Every prompt ends by committing + pushing to its own branch.

### TRACK C1 — scripts/ reorganization

```text
TASK: Reorganize scripts/ so shared helper modules live in scripts/lib/ and
one-off investigation probes are corralled out of the top-level namespace,
WITHOUT breaking any import or any doc/result reference. Pure move + reference
fix — no behavior change, no data-path changes (those belong to the data reorg).

Context: scripts/ has ~106 files. The 24 `_`-prefixed ones are a mix of shared
helpers (imported by other scripts and tests) and manual one-off probes (cited
by docs/results). They are NOT throwaway — move, never delete.

Do this:
1. Create scripts/lib/__init__.py. (If the data-reorg session already created
   scripts/lib/clean_io.py, rebase onto it and add alongside — never delete it.)
2. Move the SHARED HELPER modules into scripts/lib/ and update every import site:
   _bundle_io.py (imported by tests/test_bundle_io.py and _pjm_aswh_merge.py),
   _zonal_sufficiency.py (imported by neiso_/nyiso_/caiso_zonal_sufficiency.py),
   _session_score.py and _reldeploy_zonal_report.py (imported by
   _reldeploy_compare.py), _pjm_aswh_merge.py and _pjm_interchange_ab.py
   (imported by the _pjm_* run chain), _backcast_shell.py (large shared shell
   cited across docs + the calibration-report skill). Use `git mv`; fix imports
   to `from scripts.lib.<mod> import ...` (or a sys.path shim if scripts run as
   loose files without the package installed — match how the importing script
   already runs).
3. Move the one-off PROBE scripts into scripts/probes/ via git mv: the _caiso_*
   set, _pjm_*_run/_probe/_score/_refprice/_refconvex/_coopt, _dam_offer_compare,
   _neiso_probe_compare, _pjm_online_headroom_breakdown, _pjm_bit_floor_probe.
   Keep them runnable.
4. Update EVERY reference to a moved file in docs/, results/, CHANGELOG.md, and
   .claude/skills/ so no doc points at a dead path. grep each moved basename
   first; fix all hits.
5. Leave the ~80 build_/derive_/fetch_/process_/analyze_/render_ pipeline
   scripts where they are.
6. Verify: `uv run python -m pytest tests/test_bundle_io.py -q` green; grep shows
   no stale `import _bundle_io|_zonal_sufficiency|_session_score|_pjm_aswh_merge`
   anywhere; full suite green except the 4 known test_eia_loader failures.

Branch: claude/scripts-reorg. Constraint: moves + reference fixes only; zero
data-path edits; no script deleted. Commit + push.
```

### TRACK C2 — Python hygiene (after C1)

```text
TASK: Lint, format, and prune dead code across src/, scripts/, tests/. Depends
on branch claude/scripts-reorg (branch off it).

Do this:
1. `uv run ruff check . --fix` then `uv run ruff format .`. Review every
   autofix; revert any that changes behavior. Keep the diff to mechanical
   lint/format + obvious dead-code removal.
2. For the manual derive/probe scripts still hardcoding CWD-relative data paths
   as string literals, route them through src/market_sim/config/paths.py
   (clean_path / RAW_DATA_DIR / the named constants) IF the script already
   imports the package; if it deliberately runs without the package (no import),
   leave the now-correct data/raw/... literal and add a one-line comment noting
   why it doesn't use the registry. Do not introduce a package dependency into a
   script that intentionally avoids one.
3. Remove unused imports/variables ruff flags; delete any script confirmed dead
   (zero refs in repo AND not an entrypoint) — list each with proof before
   removing.
4. Verify: `uv run ruff check .` and `uv run ruff format --check .` clean; full
   pytest green except the 4 known failures.

Branch: claude/python-hygiene. Commit + push.
```

### TRACK C3 — frontend/ vs dashboard/ investigation (independent, no refactor)

```text
TASK: INVESTIGATE ONLY — do not refactor. Determine the relationship between the
two web trees frontend/{js,css,data} and dashboard/{js,styles}: what each
renders, whether one supersedes the other, what builds/deploys them (check
.github/workflows and scripts/regen_dashboard.py / build_manifest.py /
render_backcast.py), and which files are orphaned. Produce a short
docs/frontend-dashboard-audit.md with: a file-by-file purpose table, the
deploy/build path for each, an overlap/duplication finding, and a recommended
consolidation (keep / merge / retire) with risks. Recommend; do not execute.

Branch: claude/frontend-audit. Commit + push the audit doc only.
```

### TRACK D1 — Entry-point docs (README quickstart + dependency single-source)

```text
TASK: Give the repo a real front door and one dependency source of truth.

Do this:
1. Rewrite README.md to add: a one-paragraph what-it-is (keep the existing
   summary), a Quickstart (clone, `uv sync`, run a backcast e.g.
   `uv run market-sim --iso ERCOT --mode backcast --year 2024`, run tests
   `uv run python -m pytest -q`), a "repo layout" map (src/ data/ scripts/
   docs/ frontend/ dashboard/ learning-hub/), and pointers to
   model-methodology-spec.md, claude.md, and the two cleanup plans. Verify each
   command actually runs before documenting it.
2. Resolve the requirements.txt vs pyproject.toml ambiguity: pyproject.toml +
   uv.lock are the source of truth (highspy/numpy/scipy/pandas/pyarrow/pydantic/
   pyyaml + dev: pytest/ruff). Either delete requirements.txt or replace it with
   a generated, clearly-labelled "pip fallback, source of truth is pyproject"
   export. Update the one reference in docs/data-reorg-plan.md.
3. Decide context/: it is empty (.gitkeep only). Either remove it and drop the
   references, or document what it is meant to hold. Recommend in the commit.

Branch: claude/docs-entrypoint. Commit + push.
```

### TRACK D2 — Reconcile in-repo prose to current reality (after C1)

```text
TASK: Bring the prose docs in line with the post-W1 layout and the scripts
reorg. Depends on branch claude/scripts-reorg (for moved script names).

Do this:
1. Update every prose reference to the old inputs/ layout in market-sim-build-plan.md,
   claude.md (the architecture diagram + data section), CHANGELOG.md (only where
   it describes current layout, not historical entries), and docs/*.md to the
   data/raw/... reality. Leave genuinely historical changelog entries intact;
   fix only statements that claim to describe how things are NOW.
2. Update claude.md's "Reference Docs" + architecture map for the scripts/lib +
   scripts/probes structure from C1.
3. Root clutter: move or retire the loose root HTML — confirm whether
   offer-curve-grounding.html is a true orphan (no refs) and either delete or
   relocate under a site/docs dir; keep index.html + model-updates.html as the
   Pages landing site but document what they are.
4. Verify: grep for inputs/raw-data|inputs/processed|inputs/calibration in *.md
   docs/ claude.md returns only intentional historical references; every moved
   script name from C1 resolves.

Branch: claude/docs-reconcile. Commit + push.
```

### TRACK D3 — Final /sync-docs pass (LAST, after data W4 + C1 + D2)

```text
TASK: Run the repo's /sync-docs skill to reconcile the methodology spec and any
remaining prose with the final settled code + data state. This runs LAST, after
the data loader cutover (data-reorg W4) and after C1/D2, so docs are synced once
against the final reality rather than mid-flight. Follow the skill: diff what
changed since the last doc sync, map each change to the docs that describe it,
verify behaviour against source, propose reviewed edits + a CHANGELOG entry.

Branch: claude/sync-docs-final. Commit + push.
```

---

## Risks & mitigations

- **Moving a `_`-prefixed script breaks a doc/skill link.** Mitigation: C1
  greps every moved basename across docs/, results/, CHANGELOG, .claude/ and
  fixes all hits in the same commit; verification re-greps for dead links.
- **`scripts/lib/` collision with data-reorg W2.** Mitigation: additive shared
  namespace, first-writer-wins on `__init__.py`, neither session deletes the
  other's module (see Coordination).
- **Scripts that run without the package installed.** Some scripts intentionally
  avoid `import market_sim`. C2 must detect this and not force the registry on
  them; keep the corrected literal + a comment.
- **`/sync-docs` run too early documents a moving target.** Mitigation: D3 is
  explicitly gated on W4 + C1 + D2.
- **Ruff autofix changing behavior.** Mitigation: C2 reviews every autofix and
  reverts non-mechanical ones; full suite is the guard.
