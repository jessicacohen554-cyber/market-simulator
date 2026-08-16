# GOLDEN-TIER-FIX — low-memory curate_emissions: independent verification + lane close-out (2026-08-15/16)

**STATUS: CLOSED — the fix is on main (via the twin lane), the single
authorized dispatch is spent and GREEN (run `31913648051`), and this document
is this lane's surviving deliverable: an independent, byte-level verification
of the implementation now on main, plus the collision post-mortem.**

Charter: the owner's 2026-08-15 BLOAT-B-5 sitting decision
(`docs/model-audit-release-plan-2026-08.md` §8) transferred the deferred
B-1/B-2/B-5 (and B-3) post-merge golden-tier dispatch duty to this lane; plan
§6 decision 7's single authorized dispatch was executed **once**, by the twin
lane (§4). Gate G3's evidence blocker is cleared by that green.
**Branch:** `claude/golden-tier-fix-2e138a`, rebased onto main `00abb60`
after the owner's history rewrite. Upstream record:
`docs/handoffs/perf-recheck-2026-08.md` §1 (PERF-A measured root cause +
prototype); `docs/bloat-removal-report-2026-08.md` §4 (in-repo diagnosis).

---

## 1. Outcome — what this lane contributes, and what it dropped

The GOLDEN-TIER-FIX charter was executed **twice in parallel** (§5). The twin
lane's Arrow-side rework merged to main and is what ships. This branch's own
`curate_year()` rework — an independently-derived pandas/numpy assembly, fully
proven equivalent (§3) — is **deliberately dropped**: main already carries a
different rework of the same function, and stacking a second one on top is a
conflict at best and a silent mixed-state at worst. That was this document's
standing recommendation before the merge, and the rebase honors it.

**What this branch therefore carries: this document only. No code.**

Its value is that the verification is *independent*: the implementation on
main was measured and byte-compared here, on a separate host, against a stock
baseline this session generated itself — a second source on merged code,
rather than the authoring lane's own testimony.

## 2. Independent verification of the implementation now on main

`scripts/data/curate_emissions.py` on main `00abb60` is **byte-identical** to
the twin lane's commit `86374f2` (`git diff 86374f2 origin/main --` on that
path is empty), so the numbers below certify exactly what is shipping.

Host: 4 vCPU / 15 GB RAM container, full `data/raw`, `data/clean` absent
before each run. Command both arms:
`uv run python .github/probes/rss_wrap.py scripts/data/curate_emissions.py
--years 2023`. pandas 3.0.3 / numpy 2.4.6 / pyarrow 24.0.0 / python 3.11.15.

| Arm | wall | peak RSS (VmHWM) | rows | file bytes |
|---|---|---|---|---|
| stock (pre-fix `curate_year`) | 152.9 s | **10.04 GiB** | 26,534,489 | 174,703,675 |
| **merged (main's Arrow-side)** | 193.1 s | **5.20 GiB (−4.84)** | 26,534,489 | 174,703,675 |
| this lane's dropped variant | 148.5 s | 6.48 GiB (−3.56) | 26,534,489 | 174,703,675 |

The stock arm independently reproduced PERF-A's headline exactly (10.04 GiB
VmHWM, 26,534,489 rows) — so the baseline these deltas are measured against
is confirmed, not assumed.

**Merged-vs-stock output comparison — PASS:**

* **byte-size equal** (174,703,675 B both); 26 row groups both;
* column order identical; **all 10 columns exact-equal over all 26,534,489
  rows, dtypes equal** (`assert_series_equal(check_exact=True,
  check_dtype=True)` per column — column-wise ≡
  `assert_frame_equal(check_exact=True)`, split per column only to bound
  comparison memory);
* embedded provenance differs only in `market_sim.created_utc` (the timestamp
  `write_clean_iter` documents) and `market_sim.git_commit` (this working tree
  sat on a different HEAD — run-environment, not code). No repo gate hashes
  bundle these bytes (PERF-A H4 finding).

Against the measured runner ceiling (7.8 GiB RAM + 3.0 GiB swap): **5.20 GiB
leaves ~5.6 GiB of headroom** where stock's 10.04 GiB was a page-cache coin
flip that killed 2 of 3 dispatches at exit 143.

## 3. The dropped variant (recorded for the measurement trail)

This lane's own rework used column-wise stacking (parts shed each column as
the output gains it), a factorized stable lexsort + first-of-run neighbor
dedupe, a column-wise gather, and `write_clean_iter`. It was proven under the
same protocol: 6.48 GiB peak / 148.5 s, byte-size-equal output, all 10 columns
exact-equal over all 26,534,489 rows, dtypes equal, provenance differing only
in `created_utc`. Curation tests (10) and `test_consume_emissions` (3) passed
against its output.

So **both independent implementations are equivalent to stock and to each
other** — three different assemblies, one byte-identical result. Comparative
profile: main's is the lower-peak arm (5.20 vs 6.48 GiB) and additionally
carries the real-runner green; this one was the faster-wall arm (148.5 vs
193.1 s). Nothing in the dropped variant is missing from main; it is
superseded, not sacrificed. Full implementation is recoverable from this
branch's pre-rebase history if ever wanted (commit `5a20607`, now unreferenced).

## 4. Golden-tier dispatch — spent once, GREEN

Run **`31913648051`**: SUCCESS in 11m33s — checkout 71 s, `regenerate_clean`
5m58s, **`curate_emissions --years 2023` 1m31s** (the step that OOM-killed 2
of 3 prior dispatches), tier 2m43s; loud-failure guard **PASS with zero
data-missing skips**, no corpus restored, sparse list untouched. Dispatched by
the twin lane from `claude/golden-tier-emissions-oom-03qlck` @ `ccca569`, off
post-prune main `870c4c8` (carrying every executed BLOAT-B prune), so the one
run discharges the B-1/B-2/B-5 + PR-3 dispatch duty together.

Zero data-missing skips is the load-bearing result for the prune program: the
B-1/B-2/B-5 conversions and the PR-3 hourly prune opened **no tier-read gap**.

**This lane deliberately did NOT dispatch a second run** — the charter
authorizes exactly one, and a duplicate would spend billed minutes to
re-prove a settled result. The ledger entries (release plan §8, bloat plan
close-out, CHANGELOG) are already on main from the twin's commit `8c27a2e`;
this branch does not duplicate them.

*Verification caveat, stated plainly:* this session could not read the run
independently — the session proxy returns 403 on all `/actions/*` and
`/check-runs` endpoints for this integration — so the run id, per-step walls
and guard result above are as recorded by the twin lane. What this session
*did* verify independently is the code that ran (§2).

Reminder, still binding for the weekly cron: a red caused by a **data-missing
skip** means a prune removed something load-bearing — the remedy is restoring
that corpus (report to the program director), never widening the workflow's
sparse list.

## 5. Collision post-mortem — one charter, two lanes

Two sessions executed this charter simultaneously: this one and
`session_01St4QNz9jTnw3W5oSav1Tzi`, which pushed the Arrow-side rework
(per-file `pa.Table` conversion, `pc.sort_indices` with an explicit row-order
tiebreaker + adjacent-key dedupe, `table.take` per row group into
`write_clean_iter`), dispatched the tier from its branch, and recorded the
ledger. Both lanes reached a correct, equivalent fix; roughly one lane's worth
of compute and one duplicate implementation were the cost, and the single
authorized dispatch was consumed by whichever lane reached it first rather
than by explicit choice.

Worth noting for future multi-lane dispatch charters: the duplication was not
detectable from the charter or the repo at pickup time — the twin branch did
not exist on origin when this lane started (it appeared mid-session), so
nothing short of a lane registry or a pre-flight `git ls-remote` convention
would have caught it. The cheap mitigation is a pre-flight remote-branch scan
for the charter's keywords before starting implementation.

## 6. Ambient findings on the new main (not this lane's to fix)

Re-verified against main `00abb60` after the history rewrite:

* The keeper-replay red this lane reported pre-rebase
  (`test_all_keeper_metas_build`, `nyiso_solar_registry_cod_dates` unbound in
  `replay_keeper._REMAP/_IGNORE`) is **fixed on the new main** — now passes in
  1.4 s. No action needed.
* `ruff format --check .` reports **12 files** would-reformat on main
  (`tests/unit/model/test_storage.py` among them) — formatting drift that grew
  across the recent merges; the `lint` CI job runs exactly this check, so it
  is red on main until swept. Flagged to the program director; not this lane's
  surface.
* `tests/curation/test_curate_emissions.py` +
  `test_curate_emissions_unit_annual.py`: **10 passed** on main's merged
  implementation.

## 7. Weekly cron

`golden-data-tier.yml`'s schedule (`37 5 * * 1`) is untouched and **armed**;
its first-ever scheduled firing is **Monday 2026-08-17 05:37 UTC**. It fires
on main's low-memory path, which §2 measures at 5.20 GiB against a 10.8 GiB
ceiling — so the first scheduled run is expected green on engineering rather
than on capacity luck.
