# FINDING — FAST-TIER REPAIR: the `Fast test tier` failures on `main`'s own content

**Date:** 2026-09-02 · **Lane:** `claude/fast-tier-repair-33-gyw8r0` · **PRs:** #4611
(the repairs — MERGED to `main` at `6d52fdc5` before this finding could be
appended to it; the runs in §6 are its) and the follow-up PR carrying this
finding alone (docs-only, from the same branch restarted on `main`)
**Executes:** owner ruling **R-W** (2026-09-02) — the lane the dispatch names as
G2 leg 2's only route. R-W is not yet recorded on the director board at this
lane's pin (`dfc44d95`; `grep "R-W"` finds only the unrelated J-12 heading), so
this finding is its first written record.
**Evidence base:** `docs/FINDING-ci-red-repair-2026-09.md` (R-U: 56 → 33 local,
zero regressions, recipe and environment), director board v21's top block (the
leg-2 correction), `docs/testing.md`, and CI's own fast-tier logs at two pins
(runs 2298 and 2319).
**Scope discipline:** no solve beyond what the failing tests execute · no
workflow edit · no matrix edit · no keeper shard, marker, freeze file or
`program-status.json` touched · no test skipped, disabled, quarantined or
loosened · the parity job's red (`miso200_control_A`) reported, not fixed.

---

## 0. Result

**G2 leg 2 is NOT satisfied by this lane, and this finding does not claim it.**
The criterion, verbatim from board v21 (top block, and its own earlier words):

> *"one completed fast-tier-green `ci.yml` run"*

— a completed `ci.yml` run whose **`Fast test tier` job concludes success**.
Not "required checks green", not "7 of 7", not a local pass. The v21
correction exists because the previous dispatch compressed R-U's "7 of 7
required checks green" into a leg-2 claim R-U's own finding declined to make;
the next records lane must not repeat that in either direction.

| measurement | `Fast test tier` failures |
|---|---|
| CI, run 2298 (R-U's pin `0b4bdb39`) | **9** |
| CI, run 2319 (main content at this lane's start, `ebef98c3` = capx-D40 merge head) | **12** |
| this branch, CI-side (§6), and local serial (§5) | **1** — `test_forecast_parity.py::test_all_six_keepers_resolve`, **ROUTED** (§3.8, §7.1) |

Eleven of the twelve are repaired by root cause, and a thirteenth defect —
latent in CI, the cause of every inflated local count including the
dispatch's 33 — was root-caused and repaired on the way (§4b). The twelfth
is **substantive**:
the test is right and the code has a real backcast→forecast fork, which the
dispatch's own triage rule sends to the owning desk with a finding, never to a
patch on either side. **While it stands, no `ci.yml` run can be fast-tier-green,
so leg 2 stays BLOCKED on that one adjudication** — a two-line, owner-authorized
act, spelled out in §7.1. The dispatch's "33" is reconciled in §1.2: it was a
local count, and CI's own run at the same pin read 9.

---

## 1. Reproduction (job 1)

### 1.1 Environment and command

`uv sync` (uv 0.8.17, Python 3.11.15, highspy 1.14.0, numpy 2.4.6, scipy
1.17.1); the job's exact command from `ci.yml`:

```
uv run python -m pytest -n 2 -m "not slow and not integration and not fulldata"
```

Exit codes captured **unpiped** into a file (`echo "PYTEST_EXIT=$?" > exit.txt`
after the bare command — R-U §1's lesson). The session clone is a full
non-sparse checkout with `data/raw` present (5.8 GB, 156 entries), a superset
of the job's sparse list, so no hydration was needed; `data/clean` is absent,
as on a fresh runner.

### 1.2 The count, four ways — and the "33" reconciled

| run | conditions | failed | of which main-content |
|---|---|---|---|
| CI run 2298 | runner, `-n 2`, R-U's pin | 9 | 9 |
| CI run 2319 | runner, `-n 2`, capx-D40 head (== today's main content) | 12 | 12 |
| local #1 | this container, `-n 2`, main content | **91** | 12 |
| local #2 | this container, **serial**, the 79 non-content failures of local #1 re-run | 0 (79 passed) | — |
| local #3 | this container, **serial**, full tier, the 11 repairs in, §4b leak not yet fixed | **204** | **1** (the routed §3.8 item; the other 203 are the §4b poisoning) |
| local #4 | this container, **serial**, full tier, the 11 repairs + the §4b fix | **1** | **1** — `1 failed, 7717 passed, 34 skipped, 2 xfailed`, byte-for-byte CI's own numbers |
| CI run 2322 | runner, `-n 2`, this branch at the 11 repairs (§6) | **1** | 1 |

**79 of local #1's 91, and 203 of local #3's 204, are NOT main-content
failures of the tests that report them — they are one latent suite-hygiene
defect, root-caused and repaired in §4b.** All of them raise the same error
from `model/lp/model.py`:

```
RuntimeError: dispatch LP has no feasible primal solution (status: Not Set)
```

HiGHS model status `Not Set` means `run()` returned without solving. Every one
of them passes standalone and passes when the 79 are re-run together
(`79 passed in 15.03s`), and the same tests pass under `-n 2` on the GitHub
runner (7,704 passed in run 2319, 7,717 in run 2322). What fails is **every LP
solve after one particular test file has run in the same process**: 79 in the
xdist worker that drew that file in local #1, and 203 — everything from
`tests/test_o7_attribution_harness.py` onward in collection order — in the
serial local #3. The file is `tests/scoring/test_golden_manifest_provenance.py`
and the mechanism is a leaked environment pin (§4b); CI has passed it only by
scheduling luck. The consequence for this lane's counting is that **a local
count of this suite is not a measurement of `main` until that leak is
fixed**, and it is exactly why the dispatch counted 33: R-U's 56 → 33 was a
local `-n 2` count in its own container, while CI's run 2298 at the identical
pin read 9 — the other 24 were LP tests poisoned by the same leak in R-U's
worker. The finding therefore anchors every main-content claim on CI's own
fast-tier logs. (R-U's *zero-regression* diff stands: it compared two runs
under identical local conditions, which is valid regardless of the leak.)

The 12 main-content failures reproduce **name-for-name** in CI run 2319, in
local #1 (its 12 non-`Not Set` failures) and in local #3 (its one non-`Not
Set` failure is the routed item; the other 11 are repaired there), and every
one of them reproduces standalone. That is the population this lane triages.

---

## 2. Triage (job 1) — the twelve, classified

Classes per the dispatch: **mechanical** (stale fixtures/inventories, drifted
environment), **behavioral-drift** (a test asserting behaviour an armed change
legitimately moved — fix the test, cite the landing), **substantive** (the
test may be right and the code wrong — route, never patch).

| # | test | class | root cause (landing on `main`) | disposition |
|---|---|---|---|---|
| 1–4 | `curation/test_curate_reference.py` ×4 | mechanical | curator gained a 4th table (`caiso-hub-membership`, caiso-217) whose raw CSV the synthetic fixture never wrote → `FileNotFoundError` (#4516 merge `c2599168`, 2026-08-31) | **fixed** §3.1 |
| 5 | `curation/test_clean_io.py::test_datatype_list_matches_schemas` | mechanical | `capacity-market-auction-supply` registered in `regenerate_clean.DATATYPES` without refreshing the frozen snapshot (capx D31 `89415b60`, 2026-09-02) | **fixed** §3.2 |
| 6 | `curation/test_data_dictionary_sync.py::test_every_schema_has_a_section` | mechanical | same intake shipped the schema YAML but not the dictionary section (renderer `DATATYPE_ORDER`/`NARRATIVE` not extended) | **fixed** §3.2 |
| 7 | `regression/test_constants_facade.py::test_moved_surface_is_complete` | mechanical | `NET_ICR_REQUIREMENT_MW_BY_ISO`, `NET_ICR_HOLD_LAST_RATIO_BY_ISO` added to `capacity_market.py` + re-exported, inventory not extended (capx D40 `4d3263c6`, 2026-09-02) | **fixed** §3.3 |
| 8 | `iso/caiso/test_caiso_locational_as.py::test_families_zone_masks` | behavioral-drift | `REGION_ZONES["AS_NP26"]` gained `FSNO` (caiso-224 partition, #4516); the test compares a 6-zone mask to the full region list | **fixed** §3.4 |
| 9 | `scoring/test_ff_readiness_battery.py::test_marker_state_reflects_committed_markers` | behavioral-drift | NYISO `complete` marker WITHDRAWN 2026-08-30 (owner ruling, capx-director refresh #12); ERCOT DECLARED `complete` (#4516) | **fixed** §3.5 |
| 10 | `unit/results/test_cache_config_agreement.py::test_fourteen_groups_split_two_and_twelve` | behavioral-drift | T3-GOLDEN-2 (`a5523fac`/`bba296ca`, 2026-09-01) landed a 15th shared-key group; the refused set is unchanged | **fixed** §3.6 |
| 11 | `unit/model/test_entry_vre_zone_selection.py::test_default_cache_key_is_byte_stable` | mechanical | the owner-authorized capx-D41 key ADVANCE (`11af6f1c`, 2026-09-02) swept every pin but this one | **fixed** §3.7 |
| 12 | `scoring/test_forecast_parity.py::test_all_six_keepers_resolve` | **substantive** | two ERCOT keeper mechanisms (`ercot_storage_adaptive_expectation`, `ercot_adaptive_event_release`) are consumed ONLY by the backcast orchestrator — a real FR-22 fork | **ROUTED** §3.8, §7.1 |
| 13 (latent) | `scoring/test_golden_manifest_provenance.py` — passes itself, poisons every LP test that follows it in its process | mechanical (suite hygiene) | executes `scripts/capture_keeper_goldens.py` by path; the script's import-time determinism pin leaks `MARKET_SIM_HIGHS_THREADS=1` into `os.environ`, and HiGHS refuses every later solve whose `threads` differs from the already-initialized global scheduler | **fixed** §4b |

**Fixed 11 of the 12 CI-visible failures plus 1 latent / routed 1.** No test
was skipped, marked, deselected, xfailed, loosened or deleted; every repair is
either a fixture/inventory catching up with a landed change (with the landing
cited in the file), a re-pin to an already-owner-authorized value, or the
restoration of process state a test had been leaking. Coverage went **up**,
not down: two new tests (§3.1, §3.4), trivial cases first.

---

## 3. Root causes and repairs (job 2)

### 3.1 `test_curate_reference.py` ×4 — a fixture that never learned the fourth table

`scripts/data/curate_reference.py::TABLES` gained `caiso-hub-membership`
(`curate_caiso_hub_membership`, the caiso-217 measured plant→hub crosswalk)
and `curate()` iterates every table, so all four tests died in `setUp`'s
successor call on `raw/reference/caiso-plant-hub-membership.csv` — a file the
synthetic raw dir never wrote. The test's own design is "a tiny synthetic raw
fixture, one stand-in per table"; the fourth stand-in was simply missing.

**Repair:** a 2-row `_HUB_CSV` with the real file's exact column set
(`plant_code,plant_name,tech,capacity_mw,hub,pnode,eff_start,eff_end,join_method,n_evidence`),
written in `setUp`; the expected-tables set gains the name; and a **new**
`test_caiso_hub_membership_normalization` asserts the curator's own contract
(`plant_code→plant_id`, `pnode→node`, `iso` stamped `CAISO`, `key` =
`caiso-hub-membership:<plant_id>`). The curator is untouched.

### 3.2 The `capacity-market-auction-supply` intake — two snapshots, one miss

capx D31 registered the datatype in `regenerate_clean.DATATYPES` and shipped
its schema YAML, but (a) did not refresh `test_clean_io.ALL_DATATYPES` — the
frozen snapshot whose header tells every intake to do exactly that (and which
records the identical miss for `miso-m2m-flowgates` and the FFR-PB pair), and
(b) did not extend `scripts/render_data_dictionary.py`'s `DATATYPE_ORDER` +
`NARRATIVE`, so the data dictionary carried no section and
`test_every_schema_has_a_section` read one shipped schema with no render.

**Repair:** the snapshot gains the name (dated header note); the renderer gains
the datatype in order and a `NARRATIVE` entry written from the schema header's
own words (the supply half of the auction record; rule-13 accounting-basis
posture; MISO PRA source tables); then `python scripts/render_data_dictionary.py`
regenerated `data/dictionary/data-dictionary.md`. The regenerated doc differs
from the committed one by **exactly the new section + its coverage-matrix row
(+37 lines, 0 removed)** — verified by diffing a pre-edit `--stdout` render
against the committed file, which was byte-identical, so the re-render churns
nothing else (no `data/clean` is present, so the matrix spans are unchanged).

### 3.3 `test_constants_facade.py` — the STORAGE_TECH_AVAILABLE_YEAR gap, recurring

Identical shape to the gap R-U closed one day earlier (its §4): capx D40 added
two names to `config/capacity_market.py` **with** the paired `constants.py`
re-export but **without** the inventory line. Verified before touching it:
`constants.NET_ICR_REQUIREMENT_MW_BY_ISO is capacity_market.NET_ICR_REQUIREMENT_MW_BY_ISO`
→ `True`, likewise for `NET_ICR_HOLD_LAST_RATIO_BY_ISO`, so the facade contract
was never broken and `test_every_moved_name_resolves_from_constants_facade`
passes. The inventory catches up, with the guard's own dated-comment
convention. No value touched.

### 3.4 `test_families_zone_masks` — FSNO listed in a region, absent from the topology

caiso-224 added `FSNO` to `REGION_ZONES["AS_NP26"]` with an in-code note that
the entry is *inert whenever the zone is not in the active topology — zone-name
matching finds nothing*. The test builds masks over the default 6-zone
`CAISO_ZONES` (no `FSNO`) and asserted equality with the **full** region
tuple; the mask correctly holds `{NP15, ZP26}`. The code's behaviour is the
documented one; the assertion had encoded "the region list has no members
outside the topology", which stopped being true by design.

**Repair (test only):** the NP26 assertion becomes "the region's members that
are PRESENT" (`set(REGION_ZONES["AS_NP26"]) & set(CAISO_ZONES)`, and
explicitly `{"NP15", "ZP26"}`), landing cited. **Added coverage**, trivial
case first: `test_families_zone_masks_include_fsno_when_partition_is_active`
runs the 7-zone caiso-224 list and asserts the NP26 mask picks `FSNO` up and
the SP26 mask does not — the behaviour the region entry exists for, previously
untested.

### 3.5 `test_marker_state_reflects_committed_markers` — two marker moves, same desync class

The test is a read of the committed `calibration-complete.json` and its own
comment records two prior instances of lagging it (PJM, then CAISO). Two more
had accrued: **ERCOT** is in `complete` (keeper `2026-08-25-234-eastex-identity`)
and **NYISO** is in `withdrawn` (withdrawn 2026-08-30 by owner ruling at the
capx director's refresh-#12 card: *a `complete` marker cannot stand on a
NOT-YET keeper*; `keeper_at_withdrawal` = `2026-08-30-nyiso-157-par-attribution`).
`_marker_state` reads `complete` → `withdrawn` → `none` in that order and is
untouched.

**Repair (test only):** ERCOT joins the `complete` set, NYISO joins CAISO in
`withdrawn`, MISO stays `none`; the comment records both moves and their
authority, keeping the file's `withdrawn ≠ none` reasoning.

### 3.6 `test_fourteen_groups_split_two_and_twelve` — a designed 15th pair

The test replays every committed `run_config.json` sharing a cache key and
asserts the (c′) rule refuses exactly the two D24 true positives. Recomputed at
the test's landing commit (`c2599168`) there were 14 groups; at HEAD there are
15, and the set difference is one key, `706e7ba8e6582d42`:
`results/ff-t3-neiso-golden/bau/run_config.json` (overwritten by T3-GOLDEN-2's
armed-posture golden, `a5523fac`) now shares it with
`bau/fc6/arms/base/run_config.json` (`bba296ca`). The pair agrees on every
field the rule compares — a **designed** case — so the second, load-bearing
assertion (`refused_keys == ["07e416f3f8072e7c", "f061b2646bfaac8b"]`) still
holds; only the frozen count moved.

**Repair (test only):** count 14 → 15 with the new key asserted present and the
landing cited; the two docstrings' "FOURTEEN … twelve" wording corrected. The
refused-set assertion — the invariant — is byte-unchanged.

### 3.7 `test_default_cache_key_is_byte_stable` — one pin the D41 sweep missed

`ScenarioConfig().cache_key()` reads `cedadc285f8603b9` at HEAD. That is the
**owner-authorized capx-D41 key ADVANCE** (`11af6f1c`, 2026-09-02; cause block
beside `PINNED_DEFAULT_CACHE_KEY` in `test_persisted_identity.py`): two
CCS-retrofit fixed-cost defaults re-identified onto the ATB 2024 basis, both
hashed at every value, so registration is not a remedy and re-pinning is the
sanctioned route — the `Pinned default cache key` job is green on it. D41
swept every other pin in the tree (25 files carry the new literal); this file
still read `603c2498bf71d21d`. **Repair:** the same authorized value, with the
authorization cited in-file. This is the opposite of R-U §2.4's case (an
unregistered new field), and the finding says so in the comment so the next
reader does not confuse the two.

### 3.8 `test_all_six_keepers_resolve` — a real FR-22 fork, ROUTED

`scripts/check_forecast_parity.py` at HEAD, on the ERCOT keeper
`2026-08-25-234-eastex-identity` (107 armed fields):

```
UNACCOUNTED    ercot_adaptive_event_release = True
UNACCOUNTED    ercot_storage_adaptive_expectation = True
UNACCOUNTED    ercot_storage_as_soc_reserve = True
```

The third is already in the test's exact-set pin `_FR22_OPEN_UNACCOUNTED`
(house-2, 2026-08-09). The first two are **new since the pin**: armed by the
ercot-221 promotion (2026-08-19, adaptive-expectation storage offer floor) and
ercot-223 (event-realized release guard). Measured, not assumed: the only
consumer of either field outside `scenarios.py` is
`scripts/run_calibration.py:5489` / `:5570` — the **backcast** orchestrator.
`src/market_sim/runner.py` and `pipeline/` carry no reference. A forecast run
carrying the keeper's config silently drops both — the precise defect class
FR-22 was built to catch, and neither promotion record
(`FINDING-ercot221-…`, `FINDING-ercot223-…`, `PRECOMMIT-ercot223-…`) mentions
parity at all (`grep -c` = 0 in each).

**The test is right.** The three available remedies are all adjudications the
test's own comment reserves for the forecast program (*"a GAP filing vs
BACKCAST_ONLY vs wiring it forward is a forecast-program adjudication, NOT a
housekeeping call"*): (a) wire the mechanism into the forecast orchestrator
(a solve-affecting `src/` change, the ERCOT desk's); (b) declare it in
`scripts/lib/forecast_parity_registry.py` (GAP or BACKCAST_ONLY — a
disposition); (c) extend the test's exact-set pin (which is loosening a test
to get green, forbidden to this lane). **Routed** (§7.1). Until one of them
lands, `Fast test tier` has exactly this one red and leg 2 cannot close.

---

## 4. Verification of the repairs

- **Targeted, serial, CI's marker filter:** the eight repaired files run clean
  (the four `integration`-marked readiness tests are deselected by the filter,
  exactly as in CI — a first targeted run without the filter surfaced them and
  is recorded here so nobody mistakes them for tier failures).
- **Ruff:** `ruff check` and `ruff format --check` on every changed file →
  exit 0 / "already formatted". (Main content is itself red on
  `ruff format --check` — three files, §7.2 — untouched here.)
- **The parity checker** still exits 1 on the three ERCOT UNACCOUNTED fields
  and `test_all_six_keepers_resolve` still fails on the two new ones: the
  routed item is reported at full magnitude, not hidden.

### 4b. The poisoner — a leaked environment pin, root-caused and repaired

**Symptom.** After some point in a process's test order, every
`LPModel.solve` raises `dispatch LP has no feasible primal solution (status:
Not Set)`; the same tests pass alone. Not a fork effect (the serial run shows
it), not resource exhaustion (a probe after the poisoning sequence read 6 open
fds, 10 OS threads, 0.7 GB RSS), and not HiGHS globally (a fresh `highspy`
LP with default options solved `Optimal` in the same poisoned process).

**Bisection.** Directory-level: `tests/curation`, `tests/iso`,
`tests/regression` and the root `tests/test_*.py` files each run clean ahead
of an LP sentinel; `tests/scoring` poisons it. Per-file: **no single scoring
file** poisons the sentinel. Prefix search over the 63 scoring files in
collection order: the smallest failing prefix is 42 files, last file
`test_golden_manifest_provenance.py`; that file + **either** half of the 41
before it fails, that file + the first scoring file alone passes. So the file
is necessary, and what it needs from the others is only that *some* LP has
already been solved in the process.

**Mechanism, reproduced verbatim outside the suite.** The file executes
`scripts/capture_keeper_goldens.py` by path (`spec_from_file_location` +
`exec_module`, three times). That script pins, at import, *"set BEFORE any
solve so dispatch.py's os.environ reads see the pinned values"*:

```
DETERMINISM_ENV = {"MARKET_SIM_HIGHS_THREADS": "1", "MARKET_SIM_WARMSTART": "1",
                   "MARKET_SIM_WARMSTART_XYEAR": "0"}
for _k, _v in DETERMINISM_ENV.items():
    os.environ[_k] = _v
```

Correct for its own CLI process; executed inside pytest it leaks into the
whole process. `model/lp/model.py:612` then does
`h.setOptionValue("threads", int(os.environ["MARKET_SIM_HIGHS_THREADS"]))` on
every later LP, and HiGHS — whose scheduler is process-global and sized on the
**first** solve — refuses:

```
ERROR:   Option 'threads' is set to 1 but global scheduler has already been
initialized to use 2 threads. The previous scheduler instance can be destroyed
by calling Highs::resetGlobalScheduler().
→ run() = HighsStatus.kError, model status 'Not Set'
```

(four-step `highspy` probe, this container: default-threads solve `Optimal`;
`threads=1` solve `kError / Not Set`; again `kError`; default again
`Optimal`.) The `dispatch.py` comment on the option — *"the LP optimum is
identical either way"* — is true, and irrelevant here: the solve never runs.

**Why CI has been green on it.** Purely ordering: the worker that draws the
file poisons only LPs solved *after* it, and only if some LP was solved
*before* it (otherwise the scheduler initializes at 1 and stays consistent).
Runs 2319 and 2322 drew a benign order. This is a **latent, scheduling-
dependent CI red** on `main`, and the object behind every inflated local
count this program has recorded (R-U's 33, this lane's 91 and 204).

**Repair (test only, `tests/scoring/test_golden_manifest_provenance.py`).**
The three by-path loads go through one helper, `_load_script`, which
snapshots `os.environ` before `exec_module` and restores it after — added keys
included — so the script's own pin never outlives its import. The script is
untouched (its pin is right for its CLI). Verified: the 21-file half +
the file + sentinel now `445 passed`; all of `tests/scoring` + sentinel now
fails only on the routed parity test (`1 failed, 1231 passed`). The full
serial tier is re-run on the repaired tree in §5.

The same import-time pattern exists in `scripts/replay_keeper.py:50`
(`MARKET_SIM_WARMSTART_XYEAR=0`); no test loads it, and the value equals the
`pipeline/solve.py` default, so it is noted (§7.6), not touched.

---

## 5. No-regression proof (job 2)

Because a local count in this container is not a measurement of `main`
(§1.2), the before/after is taken where both sides run under identical,
artifact-free conditions: **the GitHub runner, CI's own command, two
consecutive `ci.yml` runs** — run 2319 on `main` content (the capx-D40 merge
head, whose content is now `main`) and run 2322 on this branch — with the
failure sets diffed name-for-name from the two jobs' `short test summary`
blocks:

| | `main` content (run 2319) | this branch (run 2322) |
|---|---|---|
| fast-tier failures | **12** | **1** |
| failures **only on this branch** (regressions) | — | **0 — the set is EMPTY** |
| failures **only on main** (cleared here) | **11** | — |
| passed | 7,704 | **7,717** (+11 cleared, +2 added) |
| skipped / xfailed | 34 / 2 | 34 / 2 (unchanged: nothing deselected) |

**Zero regressions across 10 changed files.** The one remaining failure is the
routed §3.8 item, present on both sides.

With the §4b leak closed, a local serial count is a valid measurement again,
and it agrees with the runner to the digit: the full tier, serial, on the
final tree (local #4) reads `1 failed, 7717 passed, 34 skipped, 2 xfailed`
in 13m56s — the same four numbers as CI run 2322 — and the one failure is the
same routed test. Before the leak fix the identical tree read `204 failed`
(local #3): the 203-test difference is entirely §4b, which confirms the
attribution from the other direction.

---

## 6. Evidence — the CI run (job 3)

Two runs, one per code commit on PR #4611. **The evidence run is the second,
on the final code head:**

**Run `2324`, id `33658069194`, head `2617db3e` — COMPLETED, conclusion
`failure`.**
<https://github.com/jessicacohen554-cyber/market-simulator/actions/runs/33658069194>

| job | conclusion | note |
|---|---|---|
| **`Fast test tier`** | 🔴 **failure** | **`1 failed, 7727 passed, 34 skipped, 2 xfailed` in 8m13s — the one failure is `test_forecast_parity.py::test_all_six_keepers_resolve` (§3.8, routed)** |
| `Rule-22 quarantine gates` | 🟢 success | green on this PR's merge head (§7.3 for the `main`-content history) |
| `Cache-key registration guard` | 🟢 success | |
| `Pinned default cache key` | 🟢 success | |
| `Structural refactor guards` | 🟢 success | |
| `FR-21 forecast-board staleness (WARN only)` | 🟢 success | |
| `Rule-28 mechanism-matrix guard` | 🔴 failure | **new between the two runs, not this branch's:** 25 stale `scenarios.py:NNNN` anchors (+12 / +38 lines) from a `main` commit that grew `scenarios.py` after run 2322 — this PR touches neither `scenarios.py` nor the matrix (§7.7) |
| `Ruff lint + format` | 🔴 failure | `ruff format --check` on three `main`-content files this PR does not touch (§7.2); `ruff check` green |
| `FR-22 backcast->forecast parity` | 🔴 failure | as on `main` (DO-NOT-REQUIRE, H-1); the same ERCOT fields as §3.8 |
| `Forecast-invariant artifact audit` | 🔴 failure | as on `main` (DO-NOT-REQUIRE, H-1) |

The first run, **`2322`, id `33653838904`, head `2ba28852`** (the 11 repairs
without the §4b leak fix), read `Fast test tier` **`1 failed, 7717 passed,
34 skipped, 2 xfailed`** with the identical single failure, and the
mechanism-matrix guard still green — the §5 before/after is taken against
it because it is the run immediately after 2319. The passed-count rise
7,717 → 7,727 between the two is `main` moving under the PR (ten new tests
merged upstream), not this branch. #4611 was merged to `main` (`6d52fdc5`,
16:58Z) within a minute of run 2324 starting — the board's documented merge
cadence — so this finding lands through a separate docs-only PR from the
same branch restarted on `main`; its run adds no content evidence beyond
2324's.

**G2 leg 2 status, stated against the criterion verbatim — *"one completed
fast-tier-green `ci.yml` run"*: NOT SATISFIED.** The run completed; its
`Fast test tier` job is red on exactly one test, the routed §3.8 item. The
next records lane should carry it as *"leg 2 BLOCKED on the ERCOT parity
adjudication (§7.1); 11 of 12 tier failures repaired by R-W"*, and must not
compress a 12 → 1 into a green.

The other jobs are reported as found in the table above; none is this lane's
criterion and none was touched.

No `workflow_dispatch` was issued; the PR's own run is the evidence.

**Rule 27 blob verification.** Every pushed file was fetched back from
`origin/claude/fast-tier-repair-33-gyw8r0` after the push and compared to
local on **both** line count and blob sha: **9 of 9 OK, 0 mismatches**
(`data-dictionary.md` 2,021 lines, `render_data_dictionary.py` 1,415,
`test_clean_io.py` 406, `test_ff_readiness_battery.py` 398 — the four at or
above the 300-line threshold — plus the five smaller test files). No file was
rewritten from regenerated response content; the re-rendered dictionary is the
renderer's on-disk output pushed as exact bytes. The same check is repeated for
the commit carrying this finding.

---

## 7. Routed, not fixed

1. **🔴 → ERCOT calibration desk + forecast program (FR-22 registry owner).**
   `ercot_storage_adaptive_expectation` and `ercot_adaptive_event_release` are
   armed in the ERCOT keeper with a backcast-orchestrator-only consumer (§3.8).
   This is the sole remaining `Fast test tier` red and the sole blocker of G2
   leg 2. The decision is one of: wire forward (`runner.py` /
   `pipeline/solve.py` seam, `p1_storage_discharge_cost`), file a `GAP`
   declaration in `forecast_parity_registry.py` (the FFR-1E route the two
   storage-envelope fields took), or declare `BACKCAST_ONLY` with the
   rule-13 argument. Whichever is chosen, the same session re-runs the tier;
   the `_FR22_OPEN_UNACCOUNTED` pin should then be reviewed rather than
   extended, since the FR-22 job (DO-NOT-REQUIRE per H-1) is where the
   signal lives. A process finding rides along: two ERCOT promotions armed
   keeper mechanisms without the parity check that the promotion duty
   implies, and the fast tier — the one gate that would have caught it on
   the PR — was already red at the time, so the new red was invisible.
2. **🟠 → owner / next CI lane.** `main` content is red on `ruff format
   --check` again (`scripts/data/derive_thermal_tranches.py`,
   `src/market_sim/model/capacity_evolution/new_entry.py`,
   `tests/scoring/test_build_dof_ledger_coal_sigmoids.py`) — R-U §3.3's
   "re-reddens within minutes" dynamic, still running one day later. Outside
   this lane's criterion; untouched; the `Ruff lint + format` job on this PR
   will be red on those three files and on nothing this lane changed.
3. **🟢 as found — RESOLVED UPSTREAM, not by this lane.** At this lane's pin
   (`dfc44d95`) `Rule-22 quarantine gates` was red on
   `check_registry_payload_parity` (measured locally: exit 1 on
   `results/calibration/miso200_control_A` **and** `miso200_unitroute_B`,
   both unregistered full bundles — *dead solve output* under Class-E
   retention point 4). The dispatch named it the calibration desk's and this
   lane did not touch it. The desk registered both legs in #4609
   (`b81e8b4a`, "miso-200: register both A/B legs on the dashboard"), which
   merged to `main` (`5f1e47a6`) before this PR's run, so **the gate is green
   on run 2322's merge head** (§6 table) — the transient-class resolution
   board v21 predicted ("resolves by registration").
4. **⚪ as found, unchanged.** `FR-22 backcast->forecast parity` (exit 1 —
   the same three ERCOT fields plus the filed GAPs) and `Forecast-invariant
   artifact audit` remain red on `main` content; H-1 names both
   DO-NOT-REQUIRE.
5. **🟠 → records lane.** The dispatch's and board's "33 remaining" is a
   local-`-n 2` count, not a CI measurement (§1.2): CI read 9 at R-U's pin
   and 12 at this lane's start; the other 24 were the §4b leak. The next
   board version should carry the CI-side numbers; with §4b landed, a local
   serial count becomes a valid measurement again (§5).
7. **🟠 → the lanes that grew `scenarios.py` between runs 2322 and 2324
   (main drift).** `Rule-28 mechanism-matrix guard` is red on run 2324 with
   25 stale line anchors (+12 and +38 lines), the `--fix-anchors` maintenance
   R-U §5b calls *"a standing tax on a heavily-crossed file"*. The lines came
   from `main` commits merged between the two runs (the nyiso-176
   per-unit-attribution wiring, `938cf780` / `773ec391`, #4612–#4613; capx
   D43 `9b0174b3`, #4616, followed within minutes). This branch touches
   neither `scenarios.py` nor any matrix file, and this lane's charter forbids
   matrix edits, so the routine digits-only repair is left to the next lane
   that touches the file; reported here so the guard's red on run 2324 is not
   misread as #4611's.
6. **🟠 → owner (script hygiene, optional).** Two loose `scripts/` modules
   mutate `os.environ` at import time (`capture_keeper_goldens.py`,
   `replay_keeper.py`). The leak is closed on the test side (§4b), where it
   did the damage; whether the scripts should move their pins under `main()`
   so that any future by-path load is safe by construction is a small charter
   question, not a repair this lane needed.

---

## 8. R-W status statement

R-W's deliverable is a completed fast-tier-green `ci.yml` run. **This lane
delivers 11 of the 12 main-content failures repaired by root cause, zero
regressions, and one substantive item routed with its remedy enumerated.** The
green run is one adjudication away, and that adjudication is not this lane's
to make. Leg 2 remains BLOCKED; leg 4 (the owner's Settings action) is
unaffected by this finding.
