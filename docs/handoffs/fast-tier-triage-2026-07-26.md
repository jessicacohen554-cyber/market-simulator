# Fast-tier pytest backlog triage — 2026-07-26

Classification-before-fixes record for the advisory fast tier
(`.github/workflows/ci.yml` `continue-on-error: true` job). This document is
committed BEFORE any fix so the reasoning is reviewable separately from the
diffs. Branch: `claude/fast-tier-pytest-triage-5e5sok`, baselined at main
`b054dfe93d170e9cc7dfb8e13999b5fce60cfb30` (the task charter's verified SHA
`10c239bf` plus three merges, none of which touch a failing area — verified by
diff).

## 0. Baseline (measured in this session's container, full tier, exact CI
   expression, single process)

```
.venv/bin/pytest -m "not slow and not integration and not fulldata" -q \
  -p no:cacheprovider --continue-on-collection-errors
141 failed, 5014 passed, 16 skipped, 40 deselected, 7 xfailed, 60 xpassed,
5 warnings, 2 errors (collection), 152 subtests passed, 12m42s
```

(136 distinct `FAILED` node lines; the summary's 141 includes the
`TestCampdBinningGate::test_artifact_isos_take_campd_path` parametrized
subtest failures counted per-param. The task charter's reference run measured
140/2/60/5003 one tree-day earlier — same backlog, main moved slightly.)

**Environment split.** 57 of the 136 failures are artifacts of THIS container
class, not of main: every one is `ModuleNotFoundError: No module named
'tzdata'`, and all 57 pass after `pip install tzdata` with no repo change
(re-verified file-by-file). Root cause is a genuine repo defect, but in the
pip fallback, not the code: `pyproject.toml` pins `tzdata>=2024.1`
**unconditionally** (its own comment: "tzdata supplies the IANA zone database
on minimal containers") and `uv.lock` carries it, so CI (`uv sync`) always has
it — but `requirements.txt:59` exports it with the *transitive* marker
`; sys_platform == 'emscripten' or sys_platform == 'win32'`, so a
`pip install -r requirements.txt` venv on Linux silently skips it. Bucket A,
one line. The CI-comparable backlog is therefore **79 test failures + 2
collection errors + 60 xpasses**.

## 1. Bucket summary

| Bucket | Count | Content |
|---|---|---|
| A — FIX | 1 env defect + 49 tests (incl. the 30-test confirmed-retirements cluster and 1 collection error) + the governance-file restore | §2, §4 D6/D7 |
| B — XFAIL-WITH-CITATION | **0** | every candidate resolved to A, C or D |
| C — DELETE-AS-OBSOLETE | 10 | storage C5b/C5c scorer tests (§3) |
| D — ESCALATE (write-up only, NO xfail) | 5 clusters: 20 tests + 1 collection error | §4 D1-D5 |
| E — STALE-XFAIL (xpassing) | 1 mark = all 60 xpasses | §5 |
| Open observations (not fixable in-session, not xfailable honestly) | 5 tests | §6 |

## 2. Bucket A — genuine small defects (fix in this PR)

| Test / file | Defect | Evidence / citation |
|---|---|---|
| `requirements.txt:59` | tzdata exported with emscripten/win32 marker; pyproject pins it unconditionally | §0; fixes the 57 container failures |
| `tests/test_structural_prior.py` (collection error) | Wave-4D item 8 landed at half: `write_prior_artifact` + the committed artifact (`results/ensemble/structural-prior/pb3-statmode-d7-2026-07.json`) shipped, `load_prior_artifact` + the `default_prior` inversion did not. The read half's exact logic already exists in-repo as `scripts/pb5_assemble.py::prior_from_artifact` ("Inverse of … write_prior_artifact"), and `pb5_assemble.py:17-18` + the test file's `ArtifactCanonicalTests` + prompt-pack item 8 all specify the same inversion. The committed artifact satisfies every assertion in the test file (verified: per-ISO biases, stale flags, emissions-basis block). | prompt pack `docs/refactor-consolidation-prompt-pack-2026-07.md:704-709`; `scripts/pb5_assemble.py:54`; implement `load_prior_artifact` + invert `default_prior` (old fit body kept as the private W3-P1 re-fit entry) |
| `tests/test_pipeline_api.py::TestReExports::test_runner_reexports` | `runner` never re-exported `run_scenario`/`run_pair`; `pipeline.api` documents itself as their home with call-time runner imports (cycle-safe) | additive re-export in `runner.py` |
| `tests/test_constants_facade.py::test_moved_surface_is_complete` | `4732235` (miso-91, 2026-07-26) re-homed `SUMMER_WEFOR_SHARE`/`SUMMER_CLASS_DERATE` into `config/fuel_trajectories.py` + re-exported them from `constants.py` (:148-149) but did not extend the test's frozen `MOVED_SURFACE` inventory | add the two names; the companion identity test then covers them |
| `tests/test_data_dictionary_sync.py::test_every_schema_has_a_section` | six landed intakes (`pjm-outages`, `lmp-components`, `transmission-expansion`, `dam-public-bids`, `wecc-west-supply`, `nuclear-license-status`) shipped schemas without registering in `scripts/render_data_dictionary.py::DATATYPE_ORDER` or re-rendering the committed dictionary | add the six + regenerate `data/dictionary/data-dictionary.md` |
| `tests/test_clean_io.py::TestRegenerateEntrypoint::test_datatype_list_matches_schemas` | the test's own frozen `ALL_DATATYPES` snapshot (test file line 28) lags `scripts/regenerate_clean.DATATYPES` by 16 landed intakes | re-freeze the snapshot to the current 46 |
| `tests/test_soundness.py::TestSpecCompliance::test_topology_matches_spec` | asserts the pre-split 4-zone CAISO; the SP15→LA_BASIN/SDGE/SP15_rest split is the operative default since `c28d57b1` (2026-07-09) and underlies every CAISO keeper since | update 4→6 |
| `tests/test_hydro.py::TestCAISOHydroBudget::test_zones_resolve_to_caiso_topology` | same: asserts `{"NP15","ZP26","SP15"}`; `SP15` deleted by the split (`0f14b757` re-pointed literals) | update zone set |
| `tests/test_cap_and_trade.py::TestMembership` + `TestCapPath` (2) | same: membership vector asserted at 4 zones, config now 6 (5 in-state + WECC_import external) | update expected vectors |
| `tests/test_capacity_deliverability_caiso.py` (2) | `e017d877` (caiso-79 STEP-0, 2026-07-12) added the Greater-Bay/NP26 peak_load intake rows to `data/raw/capacity-deliverability/caiso/caiso.csv`; the curate test's frozen row-count (147) and zone-area set ({SP26}) predate it | update literals 147→153, +NP26 |
| `tests/test_outages.py::NEISOUnitOutageSmokeTest::test_coal_target_is_merrimack_only_all_years` | `59f8bc30` (2026-07-24, owner-authorized 2018-2026 backfill) added Bridgeport Harbor 3 (ORIS 568, coal, retired 2021-06) rows for 2018-2021; the whole-CSV Merrimack-exclusivity assertion predates the span extension. All 568 COAL rows verified 2018-01→2021-02; Merrimack-only still holds for 2022+ | scope the assertion to the 2023-2025 backcast window it was written about |

## 3. Bucket C — deliberately removed mechanism, stale follower tests

`tests/test_storage_metric_payload.py`: `StorageVerdictWiringTests` (5),
`StorageShapeVerdictTests` (4), `ActualMonthlyTests::test_null_month_year_skips_c5c`
(1) — all call `scripts.calibration_verdict.score_storage` /
`score_storage_shape`. Those scorers were **removed outright** by the rubric
v2.7 owner amendment, commit `410811a2` (2026-07-16, "C5b/C5c removed from the
rubric"; CHANGELOG 2026-07-16 entry; `docs/calibration-determination-rubric.md`
§C5 "REMOVED"). `410811a2` updated the sibling `tests/test_calibration_verdict.py`
(tombstones at its lines 758/1590) but missed this file. `calibration_verdict.py`
lines 1609-1613 carry the removal tombstone. No renamed equivalent exists;
re-adding a stub would violate rule 26 `[R-DELETE]`. Fix: delete the ten tests
mirroring what `410811a2` did in the sibling file (tombstone comments in the
same style, module docstring updated); the 12 passing payload-helper tests in
the file — the run-page diagnostics v2.7 explicitly kept — stay.

## 4. Bucket D — source half missing. Write-ups only; per the charter these are
   NOT xfailed, NOT deleted, NOT "fixed" by inventing the mechanism.

### D1 — `tests/test_caiso_belly_import_cap.py` (collection error): caiso-117
mechanism NEVER LANDED; the calibration log wrongly records it as built-on-tree

The test imports `CAISO_BELLY_EXPORT_PERCENTILE`, `CAISO_BELLY_HOURS`
(interchange config), `build_caiso_belly_import_cap_group` (transmission),
`measured_west_belly_export_cap` (eia_loader) — none exist anywhere in `src/`.
History (all refs + GitHub API):

- The ONLY commits ever to touch the mechanism's surface on any surviving ref
  are LEG-1 commits: `07c2085a`/`36aef6a5` (2026-07-24, "caiso-117 LEG 1:
  belly-cap derive probe + unit tests", tests + probe only) and `a0bebf56`
  (the FINDING doc), merged via PRs #2828/#2835 from branch
  `claude/caiso-117-import-scarcity-cudor6` — **which is deleted**.
- `FINDING-caiso117-belly-cap-c3a-coupling-2026-07-24.md` and the
  `docs/calibration-log/caiso.md` caiso-117 entry (line 951) say "mechanism
  stays built default-OFF" / "built + unit-tested + default-OFF". The
  mechanism source (ScenarioConfig flag `caiso_belly_import_cap`, the
  constants, both builders) was built only in that session's working tree and
  never pushed; with the branch deleted it is unrecoverable from git.
- The FINDING's DO-NOT-REDO explicitly forbids re-deriving it standalone, and
  the caiso-118+ redirect makes it re-armable only jointly with the belly
  price-formation fix — so re-implementing it is a CAISO-lane decision, not a
  triage fix.

**Escalation:** CAISO lane must either (i) rebuild the mechanism from the
FINDING's Inv-2 spec (design + derive gates are fully recorded) when the joint
belly delta goes live, or (ii) explicitly decide the tests are rejected-probe
residue (which would then make a C-delete legitimate). The caiso.md entry's
"stays built" wording needs a correction note either way.

### D2 — `tests/test_transmission_expansion.py::TestScenarioGate` (4): the
`transmission_expansion_enabled` gate ships in an UNAPPLIED patch

FF-G1 (2026-07-19, commits `65ca0a89`…`221c5e10`) deliberately landed the data
half (schema, per-ISO lib, curation, fetch, loader `src/market_sim/data/
transmission_expansion.py` — its ~15 sibling tests in the same file pass) and
shipped the engine wiring as `docs/handoffs/patches/ff-g1-core-wiring.patch`:
scenarios.py gate field + backcast/hindcast coercion + `_CACHE_KEY_OPTIONAL_FIELDS`
entry (the patch itself uses the sanctioned optional-field route — pin
`edbc1b103207170a` unmoved), runner pre-loop load + per-year seam. `221c5e10`:
"everything here is inert until that patch is applied". The patch was never
applied; the FF plan §1.2-11 records FF-G1 as "LANDED" including the gate —
overstated by the patch half.

**Charter note:** the charter explicitly forbids "fixing" this by adding the
field or touching `_CACHE_KEY_OPTIONAL_FIELDS` in this lane — adding the field
outside the patch's APPLY-SPEC would still be wrong-by-process even though the
patch's own route is pin-safe. **Escalation:** owner decision to apply
`ff-g1-core-wiring.patch` per its APPLY-SPEC (handoff §8: `git apply --3way` +
blob-hash verification + dictionary regeneration) — same decision class as the
plan §9 D-5 patch register.

### D3 — `tests/test_ercot_offer_surface_cleared_share_steam_rt.py` (8):
ERCOT-93 machinery never merged; its delivery patch has ROTTED

- Test file added by `d21fe712` (2026-07-21, "ERCOT-93: tests for the ST_GAS
  steam RT/SCED basis + online span"). The 197-line engine wiring
  (`ScenarioConfig.ercot_offer_surface_cleared_share_rt_steam_path`,
  `ercot_shoulder_online_span_steam{,_path}` + fleet offer-surface blocks) was
  delivered as `docs/handoffs/ercot93-core-mechanism.patch` by `bb1c27a1`
  ("transport workaround — git push HTTP-413'd; push_files cannot carry
  fleet.py/scenarios.py"), and **never applied on main** (verified: no apply
  commit in the scenarios.py history; pickaxe zero hits; fields absent).
- `docs/calibration-log/ercot.md:336` records "Machinery MERGED default-OFF
  (git apply …)" — **false for main**; `docs/handoffs/ercot94-…md:98-100`
  admits it was "Left as a patch". The patch NO LONGER APPLIES: its
  `src/market_sim/data/fleet.py` target became the `data/fleet/` package
  (wave 3H) and the scenarios.py hunk context drifted.
- The mechanism is a REJECTED probe (default-off) per the ERCOT-93 finding,
  but ERCOT-94/95 still cite it as the recorded machinery for the
  season-conditioned-wall follow-up.

**Escalation:** owner decision between (i) hand-porting the patch into
`data/fleet/offer_surfaces.py` (+ regenerating the missing
`ercot_shoulder_online_span_steam_condbinned.json` artifact via the landed
derive script) — the `43d6d37` server-side patch-apply precedent is the
sanctioned transport — or (ii) recording the drop, which would reclassify the
8 tests C. The ercot.md "MERGED" line needs a correction note either way.

### D4 — orchestrator-extraction conversion half unlanded:
`tests/test_pipeline_facade_shims.py` (7) + `tests/test_flag_registry.py::
TestMainParserIntegration` (1)

The canonical pipeline modules (`market_sim/pipeline/{ttc,reference,persist,
report,flags}.py`) all landed; the scripts were never converted to alias them.
`scripts/run_calibration.py` still owns local `_apply_ttc_overrides`/
`_apply_iso_year_ttc`/`_apply_iso_monthly_ttc`/`_TTC_LINK_ZONES`/
`_load_reference`/`_henry_hub_actual`; `scripts/run_calibration_full.py` still
owns the persist/report privates and never imports
`pipeline.flags.add_flag_arguments`/`solve_kwargs_from_args`. Session-verified
equivalence: every drifted pair differs ONLY by the public/private name, the
constant names it references, and one docstring line (`inspect.getsource`
diff); every module-level constant compares equal.

Why not an in-session A-fix: the alias conversion edits the two solve-path
scripts, which the lane's binding constraints gate behind the §8 byte-identity
protocol (capture_keeper_goldens before / regression_gate --mode byte after) —
full keeper re-solves, out of scope for a no-solve triage session. Satisfying
`test_full_parser_accepts_family_flags` by a bare import without converting
`main()`'s parser would be letter-not-substance and is refused.
**Escalation:** the wave-3J/orchestrator-unification lane lands the alias
conversion under goldens; the equivalence table above is its starting
evidence. `ci.yml` already anticipates this file joining the blocking list
after triage.

### D5 — NEISO committed fleet-artifact drift:
`tests/test_neiso_bins.py::test_committed_artifact_is_deterministic`

`build_bin_assignments("NEISO")` no longer reproduces the committed
`data/raw/_processed-legacy/bin_assignments_NEISO.csv`: row 19 (plant 55042,
Bridgeport Energy Project) regenerates Nameplate 538.0 vs committed 520.0
(0.85 % of rows differ), with the regeneration log showing the cross-ISO CC
measured-capability stack firing (`4fb54b53`, 2026-07-14: "Unify CC capacity
into one measured-capability stack" — measured > schema > net-summer, guard
clips to max(nameplate, demonstrated_peak)). The committed artifact predates
that basis change. `thermal_tranches_NEISO.csv` is a live NEISO fleet input,
so regenerating + committing the artifacts changes the NEISO solve basis —
that requires the NEISO lane to re-gate its keeper (rules 14/23), not a triage
edit. **Escalation:** NEISO lane regenerates both `_processed-legacy` NEISO
artifacts under `4fb54b53`'s basis, cites the code change per rule 23, and
re-gates the keeper; or records why the committed artifact stays frozen.

### D6 — governance-file clobber: `frontend/data/backcast/calibration-complete.json`
(the two ff-battery marker tests are RIGHT and stay red until the restore lands)

`tests/test_ff_readiness_battery.py::test_marker_state_reflects_committed_markers`
(asserts NYISO `withdrawn`) and `…::test_build_registration_scorecard_no_iso_gate_open`
fail because the committed marker file regressed, not because the tests drifted:

- `a0476efe` (2026-07-19, phantom-outage re-audit): NYISO's calibration-complete
  marker moved from `complete` into a new `withdrawn` block ("WITHDRAWN, NEVER
  RUN … the CI quarantine gate re-blocks every NYISO out-of-training
  solve/score/registration"), and NEISO's `complete` entry gained the
  `phantom_reaudit_2026_07_19` note.
- `3a76fde` (2026-07-22, "Log owner re-authorization of PJM/MISO…") appended
  its intake_log entry onto a stale pre-07-19 copy of the file, silently
  reverting the withdrawal — NYISO back in `complete`, `withdrawn` block gone,
  NEISO's re-audit note gone — despite claiming "Existing entries and markers
  byte-preserved". Verified by fetching the file at `6340864` (withdrawn
  present) vs HEAD (absent); all later commits inherit the clobbered base.
- **Live governance side-effect:** since 07-22 the rule-22 CI quarantine gate
  and `run_calibration_full.py`'s marker check see NYISO as
  calibration-complete, un-blocking the out-of-training solves the withdrawal
  re-blocked. (No NYISO out-of-training run was registered in the window —
  verified against the registry; the only out-of-training registrations are
  the NEISO 2022 holdout runs, which NEISO's legitimate marker covers.)

**Action in this PR** (flagged for owner review in the PR body): restore the
`6340864` state of the file (withdrawn block + NEISO note) merged with the
three legitimate post-clobber intake_log entries (07-22, 07-24 ×2). This
re-arms the owner's own recorded 2026-07-19 decision; editing the tests to
expect `complete` instead would launder the clobber. The two tests then pass.

### D7 — confirmed-retirements missing-clean-partition cluster: RESOLVED A
(hermetic-fixture fix), recorded here because it looked like a D

30 failures (all of test_runner's 26 data-missing failures incl. the
parametrized campd-gate subtests, test_matrix ×3,
`test_pipeline_api::TestCacheLayoutContract::test_layout_via_facade`, and 3
ff-battery resolution tests) share one root: `8aa7e14` + `652c2a8`
(2026-07-17, W2-E) made `load_confirmed_exits(iso, required=True)` fail-loud
on a never-curated checkout and wired it into `run_scenario_iso`'s default
forecast path (`confirmed_exits_enabled` default-on since `4f845ee`,
2026-07-05). `data/clean` is gitignored, CI runs no curation → these tests
have never been green in CI since 2026-07-17 (the reorg commit `e460fcd`
already records the "70 failures … pre-existing missing-derived-data set").
The raw registry is committed and `scripts/data/curate_confirmed_retirements.py`
is pure-local (~10 s, verified: builds 5 partitions, all 30 clear).

Fix per the repo's own convention (tests/conftest.py `tmp_clean_dir`,
tests/helpers/base.py `CleanDirTestCase`, the loader's own tests at
test_confirmed_retirements.py:52-66): point the affected fixtures at a tmp
CLEAN_DIR carrying a curated-root so the loader's documented
curated-root/missing-ISO degrade path (`652c2a8`) fires. No assertion
touched. Two adjacent singles in the same files, also A:

- `test_runner.py::TestPriceSignalByteIdentity` — stale premise: the FF-2A
  flip (`entry_lookahead_reprice` default OFF→ON, 2026-07-18, scenarios.py
  :1498) means the forecast default now re-prices, so `price_signal` is no
  longer the `econ_prices` object. Pin `entry_lookahead_reprice=False` in the
  test config — the exact precedent is `e0a2e20` pinning
  `datacenter_load_path="off"` in the same file for the FF-1F flip, which
  missed this twin. Assertion unchanged.
- ff-battery resolution trio (`test_walk_inputs_trivial_single_year`,
  `test_resolve_report_no_hard_fail_full_horizon`,
  `test_ercot_confirmed_horizon_is_reported_not_failed`) — these exercise the
  real input-resolution walker against the real tree, i.e. the definition of
  the `integration` marker ("exercises real data inputs", pyproject:41; the
  test_consume_* precedent). Mark `integration`; they run in the full
  pre-push lane where curation exists.

## 5. Bucket E — the 60 xpasses are ONE stale mark

All 60 xpassed entries are per-subtest XPASS reports of a single
`strict=False` xfail on `tests/test_data_dictionary_sync.py::
DataDictionarySyncTest::test_per_column_tables_match_schemas` (reason:
"capacity-deliverability datatype dictionary/schema drift", 2026-07-05). The
drift has since been fixed; every subtest passes. This is the exact failure
mode the charter names: under strict xfail these would all be red. Fix: remove
the mark (with the dictionary regeneration from §2 keeping the file green).

## 6. Open observations (neither fixed nor masked here)

1. `tests/test_integration.py::TestFullYearPerformance::test_full_year` —
   perf budget 30 s; measured 31.5 s and 30.7 s in two runs of this container.
   Loosening the bound is forbidden (charter step 5 / rule 14 applied to
   tests); whether it is a real regression or slow-host noise needs a
   reference-hardware measurement. Left failing, tracked here.
2. Order-dependent pollution: `tests/test_fleet.py::TestLoadPlannedAdditions::
   test_ercot_planned_units`, `…::TestLoadRetiredWithinWindow::
   test_neiso_includes_mystic_cc`, `…::test_retiree_absent_from_operable_snapshot`,
   and `tests/test_derive_coal_sigmoid.py::TestProvenanceFreeze::
   test_miso_defaults_match_derive` fail in the full tier but pass in
   isolation AND in a 21-file subset run — an earlier test file leaks state
   (the fleet loaders are heavily `lru_cache`d; a monkeypatched-path fit is
   the likely mechanism). Needs a dedicated pollution bisect; not fixable
   blind, not honestly xfailable (they are not deterministic failures).
3. The 7 remaining `xfailed` marks (all "pre-existing failure … tracked for
   follow-up", 2026-07-05) are still genuinely failing, so they are outside
   this triage's failure/xpass mandate — but none carries a real citation and
   each hides a real defect (e.g. the P2-storage leak into the P1 throughput
   metric, the NEISO scarcity-overlay default contradiction, the CAISO
   CC_REGULAR committed-band drift 0.90→1.0). They are the next tranche of
   this backlog.
4. `CLAUDE.md`'s architecture line still describes CAISO as "3 zones + WECC
   import node" — stale since the SP15 split (`c28d57b1`). Doc fix belongs to
   a `/sync-docs` pass, noted here.
5. `docs/calibration-log/{caiso,ercot}.md` carry the two false "built/MERGED"
   claims flagged in D1/D3.

## 7. Fix plan for this PR (in order)

1. This document (classification-before-fixes).
2. A-fixes: requirements.txt tzdata marker; structural_prior read-half +
   inversion; runner re-exports; the stale-follower test updates;
   DATATYPE_ORDER + dictionary regeneration; clean_io snapshot refresh; the
   confirmed-retirements hermetic fixtures + lookahead pin + integration
   marks (D7); the calibration-complete.json restore (D6, owner-flagged).
3. C-deletes: the ten storage scorer tests (tombstoned).
4. E: remove the one stale xfail mark.
5. Re-run the full tier; record final numbers below; correct the stale "~72"
   ci.yml comment to measured reality. The flag STAYS (D1-D5 open by
   design); flipping to blocking with open escalations would break every
   lane's PRs.

## 8. Final numbers (filled after the fix commits)

<<FILLED-AFTER-RERUN>>
