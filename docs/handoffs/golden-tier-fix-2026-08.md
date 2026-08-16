# GOLDEN-TIER-FIX — land the low-memory curate_emissions path (2026-08-15)

**STATUS: EXECUTED — equivalence proven, branch pushed; dispatch record below.**
Charter: the owner's 2026-08-15 BLOAT-B-5 sitting decision
(`docs/model-audit-release-plan-2026-08.md` §8) transferred the deferred
B-1/B-2/B-5 (and B-3) post-merge golden-tier dispatch duty to this lane; plan
§6 decision 7's **single authorized dispatch** executes here. Gate G3 is
evidence-blocked until that run is green (plan §2 G3 warning).
**Branch:** `claude/golden-tier-fix-2e138a` off `origin/main` @ `870c4c8`.
Upstream record: `docs/handoffs/perf-recheck-2026-08.md` §1 (PERF-A measured
root cause + prototype); `docs/bloat-removal-report-2026-08.md` §4 (in-repo
diagnosis of the same OOM).

---

## 1. What changed

`scripts/data/curate_emissions.py` — `curate_year()` internals reworked to the
PERF-A low-memory assembly, so **every caller** (the golden tier's
`--years 2023` step, `regenerate_clean.py emissions`, full-span reruns) gets
the bounded-memory path. CLI, function signature (`unit_dir`/`fac_dir`
kwargs), output layout, and the `write_clean`/`write_clean_iter` contracts are
untouched; `clean_io` itself is untouched. Mechanics (all order-equivalent to
the previous concat + `drop_duplicates(keep="first")` + `sort_values`):

* column-wise stacking — per-state parts shed each column as the output
  gains it, so parts and result never coexist in full;
* factorized stable lexsort + neighbor first-of-run dedupe in place of the
  whole-frame `drop_duplicates` hashtable + `sort_values` copy;
* column-wise gather of kept rows;
* `clean_io.write_clean_iter` streaming write (documented data-byte-identical
  layout) in place of `write_clean`'s full second Arrow copy.

The PERF-A prototype's `copy=False` concat kwarg was dropped (pandas 4 on the
runner deprecation-warns it; Copy-on-Write is default there).

**Not touched, on purpose:** `ci.yml` (fast-tier sparse block is PERF-B's
lane), `golden-data-tier.yml` (no workflow change needed — it already calls
`curate_emissions.py`), `scripts/data/curate_emissions_lowmem.py` +
`.github/workflows/perf-a-ci-probe.yml` + `.github/probes/rss_wrap.py` (the
owner merged the PERF-A branch as PR #3964 at 2026-08-15 16:56 UTC, so the
NOT-FOR-MERGE probe rig is on main; the probe workflow invokes the prototype,
so retiring the rig is a one-sweep owner/PERF-B decision, not this lane's —
but note that after this adoption the prototype is redundant and its
"stock script peaks ~10 GiB" framing is stale).

## 2. Equivalence proof (this session — PERF-A protocol, identical inputs)

Host: 4 vCPU / 15 GB RAM container, full `data/raw` checkout at `870c4c8`,
`data/clean` absent before each run; both runs =
`uv run python .github/probes/rss_wrap.py scripts/data/curate_emissions.py
--years 2023` (stock arm run from the unmodified tree first, output stashed
aside). pandas 3.0.3 / numpy 2.4.6 / pyarrow 24.0.0 / python 3.11.15.

| Arm | wall | peak RSS (VmHWM) | rows | file bytes |
|---|---|---|---|---|
| stock (main @ 870c4c8) | 152.9 s | **10.04 GiB** | 26,534,489 | 174,703,675 |
| reworked (this branch) | 148.5 s | **6.48 GiB (−3.56)** | 26,534,489 | 174,703,675 |

Both arms log identical composition: 26,348,736 unit-grain + 185,753
facility-ALL rows pre-dedupe. Comparison of the two parquets:

* **byte-size equal** (174,703,675 B both); row groups 26 both;
* column order identical; **all 10 columns exact-equal over all 26,534,489
  rows** (`assert_series_equal(check_exact=True, check_dtype=True)` per
  column — column-wise ≡ `assert_frame_equal(check_exact=True)`, done
  per-column to bound comparison memory); dtypes equal;
* embedded provenance metadata differs **only** in `market_sim.created_utc`
  (the timestamp `write_clean_iter` documents); file sha256 differs only via
  that stamp, matching PERF-A's finding that no repo gate hashes bundle bytes.

Against the runner ceiling (7.8 GiB RAM + 3.0 GiB swap, measured by PERF-A):
6.48 GiB local ≈ the 6.39–6.45 GiB PERF-A measured for the same assembly —
~4.3 GiB of headroom where stock's 10.04 GiB was a page-cache coin flip
(2 of 3 golden-tier dispatches died exit-143 in this step).

## 3. Solve-neutrality + checks

* Diff surface: **one file**, `scripts/data/curate_emissions.py` — curation
  layer only. No `ScenarioConfig` / `cache_key` surface touched (verified:
  the diff contains neither; the only cross-module importer of
  `curate_emissions` is the lowmem prototype, and every name it imports —
  `_SCHEMA_COLUMNS`, `RAW_UNIT_DIR`, `RAW_FACILITY_DIR`, `_detect_years`,
  `clean_campd_frame` — is preserved).
* `pytest tests/curation/test_curate_emissions.py
  tests/curation/test_curate_emissions_unit_annual.py`: **10 passed**.
* Fast tier (`-n auto -m "not slow and not integration and not fulldata"`):
  see §5.
* `tests/curation/test_consume_emissions.py` (slow/integration, reads the
  clean 2023 partition written by the **reworked** path): see §5.
* `ruff check .` clean; `ruff format --check .` has two pre-existing failures
  on main (`scripts/data/fetch_neiso_smd_zonal_lmp.py` +
  `tests/test_fetch_neiso_smd_zonal_lmp.py`, from the NEISO H1-2026 intake
  merge) — present with this branch's change stashed, so not this lane's;
  flagged to the NEISO lane via this note.
* No LP solves run in CI by this change; no history operations; no bulk
  rewrite (edits in place).

## 4. Golden-tier dispatch (the single authorized dispatch)

**Pending merge.** To execute after this branch reaches main, per charter:
dispatch `golden-data-tier.yml` once from main; record run id, per-step
walls and outcome here, and append the result to the release-plan §8 ledger
+ the bloat plan close-out note in the same commit.

Reminder recorded per charter: a red caused by a **data-missing skip** means a
prune removed something load-bearing — the remedy is restoring that corpus
(report to the program director), never widening the workflow's sparse list.

## 5. Test results

* Fast tier (`-n auto -m "not slow and not integration and not fulldata"`,
  this branch): **6,843 passed / 31 skipped / 2 xfailed / 1 failed** in 356 s.
  The single failure —
  `tests/scoring/test_replay_keeper_strict.py::TestCurrentKeepersReplayCleanly::test_all_keeper_metas_build`,
  "meta.json keys not bound to solve_and_persist kwargs:
  ['nyiso_solar_registry_cod_dates']" — is **pre-existing on clean main @
  `870c4c8`** (reproduced in 1.2 s with this branch's change stashed) and is a
  keeper-replay surface, not curation: some lane added
  `nyiso_solar_registry_cod_dates` to a keeper meta without extending
  `replay_keeper._REMAP/_IGNORE`. Flagged to the program director; not this
  lane's to fix. Skip count 31 matches PERF-A's full-data local baseline.
* `tests/curation/test_curate_emissions.py` +
  `test_curate_emissions_unit_annual.py`: **10 passed** against the reworked
  code.
* `tests/curation/test_consume_emissions.py` (slow/integration parity, read
  serially against the clean 2023 partition written by the **reworked** path):
  **3 passed** in 43 s.

## 6. Weekly cron

`golden-data-tier.yml`'s schedule (`37 5 * * 1`) is untouched and armed; its
first-ever scheduled firing is **Monday 2026-08-17 05:37 UTC**. With this
change on main it fires on the low-memory path.
