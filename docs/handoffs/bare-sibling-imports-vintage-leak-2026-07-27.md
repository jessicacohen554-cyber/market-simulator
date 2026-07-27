# Bare sibling-import closure + the vintage-leak bisect (2026-07-27)

> Status: RECORD (frozen) — session record of the refactor-consolidation lane
> executing the bare-sibling-imports + test-pollution-bisect charter seeded by
> `docs/handoffs/path-registry-routing-2026-07.md` §4. Branch
> `claude/market-sim-refactor-consolidation-b8f9xc` off main @ `874ff27`.

## 1. Re-census (measured this session, not inherited)

AST walk of every live script (`scripts/` top level + `data/` + `lib/` +
`diagnostics/`; frozen `archive/`/`probes/` excluded), flagging any
`import X` / `from X import …` whose top-level name matches a live sibling
module and is not spelled through the `scripts.` package:

* **The recorded "~10" was an undercount: 126 bare sites across 104 files.**
* The charter's family — files bare-importing `run_calibration` /
  `run_calibration_full` / `replay_keeper` / `derive_pjm_ordc_overlay` — was
  **13 files**, not 9: the recorded nine plus `knob_jacobian.py`,
  `negative_control.py`, `lib/bundle_fleet.py`, and
  `run_calibration_full.py`'s own two deferred `import replay_keeper` sites.
  The extra four were compelled into the same change: converting only their
  callers would have *created* mixed bare+canonical copies of one module in
  one process (e.g. knob_jacobian canonical `scripts.replay_keeper` + rcf's
  deferred bare `replay_keeper`).
* The three miso probe drivers were **actively diseased already**: bare
  `import run_calibration_full as rcf` three lines above canonical
  `from scripts.run_calibration_full import report_run` — two live copies of
  the 10,273-line module in the same process, `solve_and_persist` called on
  one and `report_run` on the other.

## 2. Conversion (both-paths harness first, PR #2969 pattern)

Before switching, one process loaded each target via BOTH the bare name
(`scripts/`+`scripts/data` on `sys.path`) and the canonical `scripts.*` name
and compared every consumed attribute: `solve_and_persist`,
`_environment_block`, `_load_reference`, `_parse_offer_curve_json`,
`_classify_f923`, `_iso_plant_ids`, `_henry_hub_actual`, `report_run`
(run_calibration_full); `run_year`, `_HENRY_HUB_FALLBACK` (run_calibration);
`build_kwargs` (replay_keeper); `_run_year_kwargs` (derive_pjm_ordc_overlay).
**All identical objects or byte-identical source+bytecode** (`_load_reference`
and `_henry_hub_actual` are literally the same object on both paths — they
re-export from shared `market_sim.pipeline` code). The harness also
demonstrated the disease live: all four modules loaded as DISTINCT module
objects under the two names.

Import-form changes only; the in-function
`sys.path.insert(0, REPO / "scripts")` shims that existed solely to feed the
bare form went with their imports (knob_jacobian, negative_control).
`audit_eia923_completeness.py` moved to the canonical `REPO_ROOT` bootstrap.
No `__init__.py` anywhere under `scripts/` (PEP-420 stays load-bearing).
Post-state verified: single canonical copy per module in a converted process,
every deferred site resolves, all 13 standing tools' `--help` smoke-pass.

Recorded side effect: the frozen probe `probes/pjm123_composite_precheck.py`
bare-imports `run_calibration` itself while also calling the now-canonical
`lib/bundle_fleet.py`, so a re-run of that frozen probe would hold both names
(code verified identical; frozen record, left as-is). pjm124/125 come out
strictly cleaner (fully canonical processes).

**Conversion follow-on (found by the after-side fast-tier run):**
`tests/regression/test_reuse_unresolvable_sha.py` stubbed the recipe channel
at `sys.modules["replay_keeper"]` — a test double keyed to the retired bare
import — so on the converted tree the real `build_kwargs` ran and the kwargs
gate refused before the SHA gate (2 new reds). Re-keyed to the canonical
`sys.modules["scripts.replay_keeper"]` **plus** the `scripts` package
attribute (a from-import binds the parent-package attribute when present and
only falls back to `sys.modules` otherwise); verified green both with and
without the real module pre-imported. The other `sys.modules` site,
`tests/unit/data/test_offer_peak_ladder.py`'s
`setdefault("run_calibration_full", rcf)`, is an alias (not a stub) of the
canonical module under the bare name — harmless post-conversion, left as-is.

Residue (README updated): **105 bare sites across 91 live files** — the
intra-`scripts/data/` derive/build/fetch web plus the named top-level
clusters (`score_crossover`, the stdlib deploy trio, `dashboard_add_run`,
`pb5_assemble`, `generate_parameter_registry`, the zonal-sufficiency pair,
`validate_ercot_online_capacity`, `scratchpad_diag_evening`). Open work,
per-file, same harness discipline; the deploy trio must keep its stdlib
bootstrap self-sufficient (bare `python3`, sparse checkout).

## 3. Discovered en route: main's BLOCKING gate was red (cache_key pin)

`tests/regression/test_persisted_identity.py::test_default_scenario_config_cache_key_is_pinned`
failed on **unmodified main @ 874ff27**: `ScenarioConfig().cache_key()` =
`30065460cdc3042c` vs pin `edbc1b103207170a`. Bisected to `fa9fc78`
(nyiso-83): two new flags (`nyiso_li_locational_reserve`,
`nyiso_incity_commitment_obligation`) declared "Default off (byte-identical)"
but never registered in `_CACHE_KEY_OPTIONAL_FIELDS` — the same class of miss
the tuple already records for `nyiso_scr_edrp` and
`gas_offer_net_revenue_margin`. Fixed in-session via the sanctioned optional-field route
(pin restored, armed runs still key distinctly, and the baseline's second
symptom — `test_forecast_xyear_warmstart_flag::test_default_cache_key_unmoved`
— clears with it). **Main then fixed the same miss concurrently** (the
874ff27→3e7372f window registers both nyiso-83 fields alongside its own new
mechanisms' fields), so this branch's pin commit was dropped on the rebase
onto `3e7372f`; the incident record stands here. The same window also fixed
the standing `write_derived_solve_inputs` F821 (ruff 23 → 22).

## 4. The pollution bisect: one mechanism, one polluter

Deterministic reproduction (single process, no xdist, no randomness):

* Every recorded victim passes alone.
* Behind ONE test —
  `tests/scoring/test_crossover_harness.py::TestCrossoverRunnerPath::test_forward_year_demand_not_from_realized_loader`
  — they fail: the test drives a real-data fake-solve
  `runner.run_scenario_iso` on a hindcast config with
  `eia860_vintage_year=2023`, and `run_scenario_iso` calls
  `config.paths.set_eia860_vintage(2023)`, mutating the process-global
  `_ACTIVE_EIA_860_DIR` and deliberately leaving it active. Every later
  implicit-path eia860 read on that worker then resolves to
  `data/raw/eia-860/vintage_2023/` instead of the canonical 2025ER snapshot.
* Confirmed members (alone-green / paired-red, all measured this session):
  the `test_storage` EIA-860 family (10 red in the pair), `test_fleet`
  planned-additions + retired-within-window, `test_outages`
  `NEISOFloorOutageExemptTest`, `test_coal_sync_tranche` scope-set freeze,
  `test_derive_coal_sigmoid` MISO provenance freeze.
* The flap topology is fully explained: xdist workers are separate
  processes, so a victim fails iff it lands after the polluter on the same
  worker with no intervening `run_scenario_iso` carrying
  `eia860_vintage_year=None` (which resets the global). The Wave-5A
  migration-day failure-set swap (same totals, four rows exchanged) is the
  `curation/ < scoring/ < unit/` collection-order flip: curation victims
  moved ahead of the polluter (recovered), unit victims moved behind it
  (newly red).
* **Non-members, recorded:** `test_cache_control::
  test_largest_retained_frames_is_sorted_and_limited` did NOT reproduce with
  this polluter (GC-graph ambient state; separate open observation), and
  `test_consume_phase3d::EgridZoneAssignmentParity::test_zone_lookup_matches_raw`
  is the *inverse* dependence — it fails ALONE on a fresh checkout
  (`FileNotFoundError: data/clean/reference/bin-assignments/`) and passes
  in-suite because an earlier heavy fleet load curates that partition as a
  side effect: the triage's D7 missing-clean-partition class, not this leak.

Fix at the leak, not the schedule (commit `30298c8`; no xfail, no reorder,
no isolation):

1. `tests/conftest.py::_restore_eia860_vintage` — autouse snapshot/restore of
   the vintage global around every test (closes the class for any future
   polluter; snapshot semantics, not forced `None`).
2. The polluting test resets via `addCleanup` (hermetic under bare
   `unittest` too).
3. `scripts/diagnostics/repro_eia860_vintage_leak.py` — the bisect record +
   standing regression detector (exit 1 if the leak returns). Post-fix: fast
   pair 2 passed; `--full` 34 passed where the identical pairing failed 10+
   pre-fix.

## 5. Verification record (before → after, both measured this session)

| Gate | Before (main @ 874ff27) | After (branch head) |
|---|---|---|
| ruff check . | 23 errors / 5 files (was 22/4 at PR #2969; the +1 landed upstream) | identical 23 / 5 (none touched here) |
| ruff format --check . | clean | clean |
| ci_refactor_guards.py | import-walk OK; script-refs OK (8 tolerated) | identical |
| 9-file blocking facade + persisted-identity set | **1 FAILED** (cache_key pin, upstream `fa9fc78`) + 72 passed | 73 passed, 5 subtests — pin restored `edbc1b103207170a` |
| Fast tier (`-n 2`, CI expression), two runs per side | 26 failed + 1 error, sets byte-identical across both runs | **23 failed + 1 error, sets byte-identical across both runs** |

### 5.1 Fast-tier failure sets (all four runs measured this session)

Before (two runs, detached origin/main, clean tree): 27 sorted FAILED/ERROR
lines, **byte-identical run-to-run** — the triage's stable 26+1 backlog, with
exactly one pollution-family member (`test_coal_sync_tranche` scope freeze)
firing in both schedules. After (two runs, final tree): 24 lines,
**byte-identical run-to-run**, and the before → after diff is **purely
subtractive** — three rows green, zero rows red:

1. `test_persisted_identity::test_default_scenario_config_cache_key_is_pinned` (§3 pin fix)
2. `test_forecast_xyear_warmstart_flag::TestFieldRegistration::test_default_cache_key_unmoved` (§3 pin fix)
3. `test_coal_sync_tranche::TestCommittedTakeorpayRegulated::test_scope_set_membership_freeze` (§4 vintage-leak fix)

An intermediate after-run on the pre-§2-follow-on tree additionally showed the
two `test_reuse_unresolvable_sha` reds; the stub re-key cleared them and the
final sets carry no addition of any kind. 26+1 → 23+1, with a set that is now
stable across schedules on both sides.

### 5.2 Post-rebase re-verification (main moved to `3e7372f` mid-session)

Main advanced 874ff27 → `3e7372f` (74 files, incl. its own cache_key pin fix
and the F821 fix) while this session ran, so the branch was rebased onto
`3e7372f` (pin commit dropped as redundant; only `run_calibration_full.py`
overlapped, in disjoint regions) and the full two-runs-per-side protocol was
repeated:

* bare `3e7372f`: **25 failed + 1 error**, sets byte-identical across runs
  (main's pin fix already absorbs the two §3 rows; the pollution member
  `test_coal_sync_tranche` still fires on main).
* rebased tree: **24 failed + 1 error**, sets byte-identical across runs.
* newmain → rebased diff: **purely subtractive, exactly one row** —
  `test_coal_sync_tranche::test_scope_set_membership_freeze` green (the
  vintage-leak fix) — zero additions. Ruff 22 errors on both sides; pin
  `edbc1b103207170a` green on both sides.

## 6. Deliberately NOT done

* **`bench_warmstart_xyear.capture()` spy re-point (charter item 2,
  optional):** left as recorded rot. The charter's own gate — verify against
  the committed capture pickle *without re-running a solve* — is
  unsatisfiable: the only way to validate a re-pointed spy end-to-end is to
  run `capture()`, which solves real LPs. The docstring note from the
  2026-07-26 session stands.
* The 105-site bare-import residue (§2) — open work, recorded in
  `scripts/README.md`.
* `test_cache_control` GC-flap and the `phase3d` missing-clean-partition
  inversion (§4) — separate classes, recorded, unowned here.
