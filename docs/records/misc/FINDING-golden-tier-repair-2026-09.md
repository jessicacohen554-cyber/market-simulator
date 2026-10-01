# FINDING — golden-data-tier repair: three cron REDs, three causes (plus a fourth the dispatch surfaced), cron removed, one dispatch green

**Date:** 2026-09-03 · **Session:** GOLDEN-TIER-REPAIR (`claude/golden-tier-repair-dvb3qx`)
**Executes:** owner ruling **R-Y** (2026-09-02): `golden-data-tier.yml` was 3-for-3
red on its own schedule (runs #5 2026-08-17, #6 2026-08-24, #7 2026-08-31 — the
last post-dating the R-V un-park), so byte-green certification had no working
instrument and a failing cron was billing minutes unwatched.
**Precedent read first:** `docs/FINDING-golden-tier-cron-red-2026-08-17.md`
(run #5's same-day diagnosis, PR #4071, verified by a full local four-step
replay) and the workflow itself.

## 0. Verdict, one paragraph

The three scheduled failures are **three different defects, each merged to
`main` between one firing and the next** — not one cause and not the 2026-08-16
history rewrite, the corpus conversions, or the R-J/R-O manifest-schema changes
(§4 rules each out on evidence). Run #5 was the neiso-97 `curate_lmp` dtype
crash, already root-caused and fixed by #4071 the same day. Run #6 was the
loud-failure guard doing its job: ercot-231 (2026-08-23) added a new raw corpus
(`data/raw/eia-930-interchange/`) and a `fulldata` test that reads it, without
extending the workflow's sparse-checkout list, so the test skipped for missing
data and the guard turned that skip red. Run #7 was that same gap **plus** a
stale assertion in an `integration`-marked test that still expected NYISO's
`complete` marker after the owner withdrew it on 2026-08-30. Every provisioning
and verification half of the tier is intact — the ERCOT fleet-arrays golden
itself **passed in #6 and #7**. Repairs: the missing glob, the assertion
corrected to the committed marker state, and the cron removed (dispatch-only).
The full four-step job replays green locally (§6). The first authorized
dispatch, run #8, then went red on a **fourth, previously un-root-caused
defect**: `curate_confirmed_retirements.py` completed every write and
validation and aborted at interpreter finalization (`terminate called without
an active exception`, exit -6) — the intermittent teardown abort three earlier
sessions had logged on other curations and never attributed. §7 pins the
mechanism (pandas hands Arrow a Python file handle on the validate round-trip
read; an Arrow IO thread outlives finalization) and fixes it at the shared
`clean_io.validate_clean` seam. The green run is **`33704730253`** (§8).

## 1. The three scheduled runs, dated against what merged

| run | fired (UTC) | head | failing step | cause | merged (UTC) |
|---|---|---|---|---|---|
| #5 `31999181985` | 08-17 05:48 | `6cc332e` (#4065) | 5 provision data/clean → `[FAIL] lmp` | `curate_lmp._neiso_flat24_repair` assigned the **str** `"02"` into an int64 `Hr_End` (pandas 3.0.3 `LossySetitemError`) | neiso-97 `a2b5e3d` / #4043, 08-17 02:34 — three hours before the cron. **Fixed by #4071, merged 08-17 14:36** |
| #6 `32694913707` | 08-24 05:49 | `d84a95e` (#4242) | 8 loud-failure guard (steps 5–7 all green: 45 passed / 3 skipped) | `DATA-MISSING SKIP: tests.iso.ercot.test_ercot_tie_zonal_interchange::test_flag_moves_placement_never_the_system_total — raw data input absent: missing ['data/raw/eia-930-interchange/ERCO interchange hourly.parquet']` | ercot-231 `8506f29` (corpus + test), 08-23 17:38; leap-year follow-up `e8a3150` 08-24 03:09 — both on `main` before the cron. The sparse list was never extended |
| #7 `33361411396` | 08-31 05:41 | `d44446e` (#4464) | 7 pytest (1 failed / 49 passed / 3 skipped) **and** 8 guard (same DATA-MISSING SKIP) | (a) the #6 gap, unchanged; (b) `test_build_registration_scorecard_no_iso_gate_open` asserted `sc["NYISO"]["gate_a_backcast"]["marker"] == "complete"`, got `'withdrawn'` | (b): Q5-W `ecc2d60` "withdraw NYISO's `complete` marker (owner r#12 ruling)", 08-30 18:01 — the night before the cron |

The last green of any kind was run #4 (2026-08-15, `workflow_dispatch`, the
#3996 emissions-OOM fix branch). Everything in the table post-dates it.

## 2. Root causes

### 2.1 Run #5 — `curate_lmp` dtype crash (RESOLVED BEFORE THIS SESSION)

Fully recorded in `docs/FINDING-golden-tier-cron-red-2026-08-17.md` §2: the
neiso-97 flat-24 DST repair relabelled the true spring-forward HE02 row with a
string in an int64 column; pandas 3.0.x raises instead of upcasting; the unit
test modelled the wrong dtype. #4071 relabels with the integer `2` and pins the
dtype in the test. Confirmation that the fix held: step 5's `lmp` curation is
`[ ok ]` with 44 partitions written in both #6 and #7, and in this session's
replay (§5).

### 2.2 Runs #6 and #7 — an un-provisioned new raw corpus (the guard working as designed)

`tests/iso/ercot/test_ercot_tie_zonal_interchange.py:103` is decorated
`@requires_raw(_NB_PATH, "data/raw/eia-930-hourly/ERCO hourly.parquet")` with
`_NB_PATH = data/raw/eia-930-interchange/ERCO interchange hourly.parquet`.
`requires_raw` (`tests/helpers/base.py:66`) tags the test `fulldata` — so the
tier selects it — and skips it with the message `raw data input absent: missing
[...]` when the path is absent. `scripts/check_data_tier_report.py` matches that
message against `DATA_MISSING_MARKERS` and fails the job: exactly the card-F
contract ("provision the data the tier needs or skip-with-loud-failure").

The corpus is **tracked** at tip (six files, ~5.8 MB: CISO/ERCO/ISNE/MISO/PJM
`interchange hourly.parquet` + `README.md`; `git ls-tree -r HEAD` verified) and
is **not** a converted corpus — no README re-fetch route is involved, nothing
was untracked, nothing is unrecoverable. The workflow's non-cone sparse list
simply had no line for it: the list was audit-measured on 2026-08-12 and
ercot-231 added a new dependency eleven days later without touching the
workflow. The header's own instruction covers this case verbatim: "A gap here
surfaces as a data-missing skip, which the loud-failure guard turns into a red
run — extend this list, never let the skip stand."

### 2.3 Run #7 — a stale marker assertion in an integration-marked test

`tests/scoring/test_ff_readiness_battery.py::test_build_registration_scorecard_no_iso_gate_open`
(marked `integration` because gate-c input resolution walks the real data tree,
so it runs only in this tier) pinned NYISO's gate-A marker to `complete` from
the 2026-07-31 nyiso-104b re-declaration. The owner withdrew that marker on
2026-08-30 (Q5-W, `ecc2d60`: "a `complete` marker cannot stand on a NOT-YET
keeper", CAISO precedent applied uniformly); `calibration-complete.json` at HEAD
has `complete = {ERCOT, NEISO, PJM}` and `withdrawn = {NYISO, CAISO}`, and
`ff_readiness_battery._marker_state` reports `"withdrawn"` for an ISO in the
`withdrawn` block. The **fast**-tier copy of the same expectation
(`test_marker_state_reflects_committed_markers`) was corrected by the R-W
fast-tier repair on 2026-09-02 (`2ba2885`), whose comment records the move —
but that lane ran the fast lane (`-m "not slow and not integration and not
fulldata"`), which deselects this test, so the integration copy stayed stale.
The same desync class the R-W repair itself named.

## 3. Repairs (this branch)

1. **`.github/workflows/golden-data-tier.yml` sparse list** — adds
   `/data/raw/eia-930-interchange/` (with a dated comment). Verified two ways
   before dispatch: (a) the pattern matcher itself — the sparse list evaluated
   under gitignore semantics (`git check-ignore -v` with the list as the
   excludes file, non-cone sparse-checkout's own rule syntax) reports the ERCO
   parquet and README matched by the new line, `eia-930-hourly/ERCO hourly.parquet`
   by its existing line, and a decoy `data/raw/ercot/<sced>.parquet` unmatched;
   (b) the CI run in §6, where the test now runs instead of skipping.
2. **`tests/scoring/test_ff_readiness_battery.py:292-302`** — NYISO's gate-A
   marker asserted `"withdrawn"`, read from the committed marker file exactly
   as the fast-tier copy does; the invariant the test exists to pin is kept and
   sharpened (gate B reads HOLD for every ISO, so the gate opens for neither
   NEISO with its marker nor NYISO without one). No marker, keeper shard,
   freeze file or `program-status.json` is touched — the test now agrees with
   the record, not the other way round.
3. **Cron removed** — §4.
4. **`scripts/lib/clean_io.py::validate_clean`** (second commit, after run #8
   surfaced it) — the round-trip read goes through Arrow's `LocalFileSystem`
   with reader threads and prefetch off, so no Arrow worker holds a Python
   object at interpreter exit; frame identical, regression test added. §7.

Neither verification half is weakened: the loud-failure guard is unchanged,
`DATA_MISSING_MARKERS` is unchanged, the golden assertion is unchanged, the
pytest expression and the three performance deselects are unchanged, and no
test is skipped, quarantined or disabled.

## 4. Cron reconciliation (R-Y, ruled): `workflow_dispatch`-only

The `schedule:` trigger (`37 5 * * 1`, weekly, card F signature F1 2026-08-11)
is **removed**. The workflow header now carries a prominent TRIGGER block
recording why: three consecutive scheduled firings were red with nobody
watching, each on a defect that had merged since the previous firing, so the
schedule produced billed minutes and no certification. CLAUDE.md's
GitHub-Actions policy ("Scheduled (`cron`) workflows spend money with nobody
watching … prefer `workflow_dispatch`-only") now governs the tier. The tier
runs when a session dispatches it — after a provisioning-list change, a golden
regeneration, or when byte-green certification is needed — and that session
reads the result. Re-adding a schedule is an explicit owner act.

What this does *not* change: the F1 signature authorized the tier's existence
and cadence; R-Y supersedes the cadence half only. The workflow remains the
one place the data-provisioned tier is scheduled at all, and the card-F
"a golden nothing schedules is not a guard" concern is now met by the dispatch
duty stated in the header rather than by a cron.

## 5. What was ruled out (the prompt's named suspects)

- **The 2026-08-16 history rewrite.** Every run checked out its head cleanly
  (`actions/checkout@v4`, ~60 s), `uv sync` succeeded, and steps 5–6 completed
  in #6/#7 from the same sparse list #4071 replayed green after the rewrite.
  No cache key, pin or missing blob appears in any failure path.
- **The corpus conversions (BLOAT-B / BLOAT-S2).** #4071 §3 cleared them for
  #5 per-glob; #6/#7 confirm it positively — every sparse-listed path
  materialized (the eia-930-hourly load/generation curations, the
  campd-unit-level 2023 emissions curation and the fleet/reference/AS slices
  all ran green). The one missing corpus is a *new* tracked one, not a
  converted one.
- **The R-J/R-O manifest-schema changes.** They touch
  `results/regression-goldens/*/manifest.json`, `check_golden_manifest.py` and
  `capture_keeper_goldens.py` — none of which the tier runs (its 53 selected
  tests are the curation-parity, soundness, seam-envelope, readiness-battery,
  tranche-guard, export and fleet-arrays-golden tests; the manifest-provenance
  test is fast-tier). The fleet-arrays golden passed in #6 and #7.

## 6. Local four-step replay (this session, 15 GB / 4 CPU, pandas 3.0.3)

Same commands as the workflow, in order, on this branch:

| step | command | result | wall |
|---|---|---|---|
| 5 | `regenerate_clean.py` × 9 datatypes | **`[ ok ]` × 9**, exit 0 — `lmp` included (44 partitions; the #5 fix holds) | 7m02s |
| 6 | `curate_emissions.py --years 2023` | exit 0 — 27,064,529 rows (the post-#3996 streaming path) | 2m11s |
| 7 | pytest `-m "slow or integration or fulldata"`, three performance deselects, serial | **51 passed, 2 skipped, 0 failed**, exit 0 (53 selected of 7,900 collected, zero collection errors) | 2m45s |
| 8 | `check_data_tier_report.py` | **"data-tier report clean: no data-missing skips; golden ran and passed"**, exit 0 | — |

The three tests the failures hinged on, from the junit report:

- `test_ercot_tie_zonal_interchange::test_flag_moves_placement_never_the_system_total` — **passed** (1.6 s; it skipped in #6/#7).
- `test_ff_readiness_battery::test_build_registration_scorecard_no_iso_gate_open` — **passed** (0.5 s; it failed in #7).
- `test_fleet_arrays_golden::test_generators_to_fleet_arrays_ercot_2023_golden` — **passed** (19.6 s).

The two remaining skips are the env-gated forecast solves
(`RUN_SLOW_FORECAST`, `RUN_GOLDEN_FORECAST`), neither a data-missing skip.
Compared with #4071's replay (44 passed / 2 skipped of 49), the tier has grown
by four tests (`test_thermal_tranche_guard::TestCommittedArtifacts`) plus the
interchange test — all green.

This replay ran on the first commit (`03d562b`). After the §7 fix landed
(`0bafd74`), step 5 was replayed again on the fixed `validate_clean`:
**`[ ok ]` × 9, exit 0, 6m20s** — the round-trip validation of all nine
datatypes is unchanged by the handle-free read.

## 7. Run #8 (`33703650184`) — the fourth defect: a teardown abort after successful curation

**Failure profile.** Dispatched at `03d562b` (the three repairs above).
Checkout, uv, and eight of nine `regenerate_clean` datatypes green — including
`lmp` — but:

```
wrote .../data/clean/confirmed-retirements/PJM/confirmed-retirements.parquet  (14 rows, 8 live)

5 partition(s) written.
terminate called without an active exception
[FAIL] confirmed-retirements: exit -6
```

Every partition was written **and round-trip validated** (the script calls
`validate_clean` after each `write_clean`); the abort is at interpreter
finalization, nine seconds after the last line of output, with the SIGABRT
signature of a C++ `std::terminate` raised during a forced thread unwind. Steps
6–7 were skipped and the guard failed as designed ("pytest died before writing
it; the tier did not run").

**Not new, never attributed.** The identical signature is on record three
times, always on a *different* curation, always intermittent, always after a
complete and verified write: `ancillary-services` (2026-08-03,
`results/calibration/FINDING-caiso160-…` §5.1 — "a future session reading
the `[FAIL]` alone would re-run 45 minutes of curation or abandon a solve on a
false premise"), `ira-credit-parameters` (2026-08-04, `ffr-3p` reproduction
notes, "harmless"), and a 2026-08-03 PJM session recording it did *not* fire
on a 50/50 run, "so it is not deterministic". It was carried as a known false
alarm; now it has cost a billed CI run.

**Reproduction attempts.** 40 consecutive local runs of the exact script
(repo root on `PYTHONPATH`, as `regenerate_clean` does) — 40/40 green. Runs
#6 and #7 executed the same script green on the same runner class. It is a
timing race at process exit, not a code-path defect; the local box does not
lose it.

**Mechanism, pinned from the code path and the upstream record.**

1. The signature. `terminate called without an active exception` with no
   `what()` is what glibc prints when a thread is force-unwound through a
   `noexcept` frame — which is what CPython does to a *non-Python* thread
   that calls `PyGILState_Ensure()` after `Py_FinalizeEx` has begun
   (`pthread_exit` → `_Unwind_ForcedUnwind` → `std::terminate`). The abort
   therefore needs an Arrow worker thread that still touches a Python object
   when the main thread reaches finalization. apache/arrow **#34314** and
   **#36980** record exactly this: a parquet-reader IO thread releasing a
   `PyBuffer` (a buffer backed by a Python file object) at exit —
   `ReadRangeCache` / `ParquetFileReader` destructors in the backtrace, "1 in
   25–30 times", Linux only; **unfixed upstream**, `use_threads=False` the
   documented mitigation.
2. Where this repo hands Arrow a Python file object. `validate_clean` reads
   the just-written file with a bare `pd.read_parquet(path)`. In pandas 3.0.3
   `_get_path_or_handle` (`pandas/io/parquet.py:131-146`) opens a *local
   path* itself via `get_handle` and passes **the handle**, not the path, to
   `pyarrow.parquet.read_table` — so the reader's prefetch (`pre_buffer=True`
   by default) runs on Arrow's IO pool through a `PythonFile`, holding
   Python buffers that are released on the worker.
3. Why it is the trigger. `validate_clean` is the **last parquet read every
   curation script performs** — 58 of the 65 `curate_*.py` end `write_clean`
   → `validate_clean`; all three historical victims and confirmed-retirements
   do — and the victims are the *small* datatypes (5 partitions of ≤16 rows
   here; a single tiny IRA table; the AS slices), where the interpreter reaches
   `Py_FinalizeEx` within milliseconds of that read. The big curations
   (emissions, lmp) never abort because their tails give the pool time to
   drain. That is exactly the "intermittent, small-script, after-success"
   profile all four sightings share.

**Fix (this branch, `scripts/lib/clean_io.py::validate_clean`).** Read
through `filesystem=pyarrow.fs.LocalFileSystem()` — pandas then passes the
*path* string and Arrow opens the file natively, so no worker thread ever
holds a Python object — with `use_threads=False, pre_buffer=False`, upstream's
mitigation, so no IO-pool prefetch and no CPU-pool decode are in flight at
exit. The validation is unchanged: `pd.read_parquet` is still the reader
(pandas' own dtype mapping, including the 3.0 `str` dtype, is preserved), and
the frame is **identical, dtypes included**, asserted with
`assert_frame_equal(check_exact=True)` on confirmed-retirements (14 rows),
lmp (105,120 rows) and the 27,064,529-row 2023 emissions partition — cost
there 3.7 s → 4.5 s. `read_clean` (the model's hot consumption seam, never at
a process tail) is untouched. A regression test
(`test_validate_clean_reads_handle_free_without_arrow_threads`) pins the read
kwargs and the frame identity. `regenerate_clean` is **not** taught to
tolerate exit -6 — a real failure must stay red.

Verified locally: `test_clean_io.py` 27/27 (26 + the new pin), the three
victims' curation tests green, ruff clean; the CI step-5 command replayed
green post-fix (`[ ok ]` × 9). Confirmed on the runner by run #9 (§8), the
only place the race has ever fired.

## 8. The authorized dispatch, second attempt — run **`33704730253`**

**`workflow_dispatch` of `golden-data-tier.yml` on `claude/golden-tier-repair-dvb3qx`
at `0bafd74`, run #9, `33704730253`** —
https://github.com/jessicacohen554-cyber/market-simulator/actions/runs/33704730253
— started 2026-09-03 01:42:28 UTC, **`success`** at 01:55:25 UTC (12m57s).
This is the R-V un-park's first exercise, authorized by R-Y; two dispatches
were spent (run #8 red on §7's defect, run #9 green) — the second was
required because the first surfaced a real defect, not to re-roll a flake.

| step | conclusion | wall |
|---|---|---|
| 2 checkout (non-cone sparse, incl. the new interchange glob) | success | 62 s |
| 5 provision data/clean × 9 datatypes | **success** — `confirmed-retirements` `[ ok ]` on the fixed seam | 7m21s |
| 6 provision emissions 2023 | success | 1m39s |
| 7 pytest tier (serial) | **success: 51 passed, 2 skipped, 0 failed** (7,848 deselected, 156.7 s) | 2m40s |
| 8 loud-failure guard | **"data-tier report clean: no data-missing skips; golden ran and passed"** | <1 s |

The two skips are the env-gated forecast solves (`RUN_SLOW_FORECAST`,
`RUN_GOLDEN_FORECAST`); the interchange test and the readiness scorecard test
both ran and passed on the runner, and the fleet-arrays golden passed. It is
the first green run of the tier since run #4 (2026-08-15) and the first ever
green on a head that carries the ercot-231 corpus and the NYISO withdrawal.

**What this run certifies, exactly:**

- The tier's **provisioning path is whole again at HEAD**: the sparse list
  materializes every raw input the 53 selected tests open, the nine
  `regenerate_clean` slices and the 2023 emissions partition build on a
  standard runner, and the loud-failure guard passes with **zero data-missing
  skips** (the three remaining skips are the two env-gated forecast solves,
  `RUN_SLOW_FORECAST` / `RUN_GOLDEN_FORECAST`, out of card F's scope by
  design).
- **`test_fleet_arrays_golden` ran and passed** — the ERCOT-2023 fleet-arrays
  per-field hash golden is byte-identical at this head. That is the one golden
  the tier owns.

**What it does NOT certify:**

- It is not a byte-green certificate for the **stage-0 keeper LP goldens**
  under `results/regression-goldens/`. Those are gated by
  `regression_gate.py --mode byte` from a full-8760 solve, which this tier
  never runs (no solves in CI beyond what the tier is built to do). The tier
  makes that certification *possible* — the instrument PERF-B's byte-green
  claim must be exercised on is working again — it does not perform it.
- "7-of-7 current" was a manifest fact at the R-Y sitting; **at this head it
  is 4-of-7** (`check_golden_manifest.py`: 42 manifests, 75 entries, 11
  enforced; ERCOT, ERCOT__carveout-2023, NEISO, PJM CURRENT; **CAISO, MISO,
  NYISO STALE** against the keepers promoted 2026-09-02 — caiso-239, miso-201,
  nyiso-177). Manifest currency is a separate fact from tier green and this
  run does not move it.

## 9. What G2 leg 1 still needs after this

Leg 1 is *PERF-B merged byte-green* (release plan §8; director board L-15).
With the instrument repaired, what remains is the work, not the tooling:

1. **PERF-B's remaining charter adjudication** — per board L-7, the WS3-next
   charter's four items re-verify CLOSED at HEAD, leaving one citation re-pin
   (item 4, `forecast_xyear_warmstart`, `scenarios.py:13606 → :13825`) and the
   L-8 hand-back (`markup` at 471–601 s/yr, unattributed) as a **charter item,
   not a lane**. Adjudicating that hand-back — attribute or close it — is the
   substantive item leg 1 waits on.
2. **Stage-0 currency back to 7-of-7** — three goldens went stale on the
   2026-09-02 promotions (§7) and need re-capture under the R-O partition
   schema before "merged byte-green" can be claimed against the live keepers;
   the MISO golden's capture (board K-5) is now a re-capture.
3. **A byte-green run of the keeper LP gate** against those current goldens
   (`regression_gate.py --mode byte`, in-session, never in CI) — the
   certificate itself, which this tier now no longer blocks.

The tier's own standing duty: dispatch it after any sparse-list or
`regenerate_clean` change and after any golden regeneration, and read the
result in that session.
