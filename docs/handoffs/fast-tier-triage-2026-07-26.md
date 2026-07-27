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

**RESOLVED 2026-07-26 (owner): (ii) RECORD THE DROP.**
`tests/test_caiso_belly_import_cap.py` C-deleted (clears the collection error).
The FINDING's **§Inv-2 is now labelled the rebuild recipe** and carries the
"never pushed / unrecoverable" correction, its DO-NOT-REDO "stays built" clause
is superseded on the factual half only, and the caiso-118 redirect #2 now says
"re-arm" means re-implement (that lane owning the unit tests). Matching
resolution note in `docs/calibration-log/caiso.md`. The landed derive half
`scripts/probes/_caiso117_belly_cap_derive.py` stays on disk.

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

**RESOLVED 2026-07-26 (owner): APPLY IN FULL, doc hunks included.** The
APPLY-SPEC's `git apply --3way` no longer works — five of the patch's eight
files conflict — so each hunk was re-anchored by hand and applied verbatim
where the target was unchanged: the `scenarios.py` gate + coercion +
`_CACHE_KEY_OPTIONAL_FIELDS` entry, the `runner.py` pre-loop load and per-year
`year_ttc`/interface-group seam, `regenerate_clean.DATATYPES` (+ the frozen
`test_clean_io.ALL_DATATYPES` snapshot), `run_full_horizon.py`'s
`--transmission-expansion` flag (re-anchored onto the `golden_posture`
signature the patch predates), and the CHANGELOG / FF-plan §1.2-11 + WAVE FI /
gap-register §3.11 doc hunks. The `render_data_dictionary.py` hunk had already
landed via this document's own §2 A-fix; the dictionary re-renders with no
diff. **The pin did NOT move** — `cache_key(ScenarioConfig())` is still
`edbc1b103207170a` (both `test_persisted_identity` and
`test_forecast_xyear_warmstart_flag` green). The three "LANDED 2026-07-19"
claims are corrected in place to "data half 07-19, engine half 07-26"; the
gate stays default-off and T1-F A/B is still pending before any flip.

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

**RESOLVED 2026-07-26 (owner): (ii) RECORD THE DROP.** The mechanism is a
rejected, default-off probe, so porting ~197 lines of engine wiring plus
regenerating a missing artifact buys no live behaviour.
`tests/test_ercot_offer_surface_cleared_share_steam_rt.py` C-deleted;
correction/resolution notes added to `docs/calibration-log/ercot.md`,
`docs/handoffs/ercot93-session-handoff.md` (its `git apply` step marked dead)
and `docs/handoffs/ercot94-scarcity-tail-diagnosis-2026-07.md`. The patch bytes
and the landed derive script stay as the wiring's only surviving record.

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

**RESOLVED 2026-07-26: converted under goldens.** Two corrections to the
session-verified equivalence recorded above — the tree moved after it was
taken, and `pipeline/persist.py` had fallen BEHIND the script on two counts:
`basis_sha()` and its `"basis_sha"` key inside `git_state()` (the caiso-122/123
origin-durable anchor), and the two `nyiso_{hydro,scr_edrp}_reserve_eligible`
`calibration_flags` keys. Both were FORWARD-PORTED into `pipeline/persist.py`
before aliasing; without the port the conversion would have silently dropped
three recorded `run_config.json` keys from every bundle. Everything else was
name-only as recorded.

The flag-registry wiring surfaced a live defect: the parser surface was
captured mechanically before and after (option strings, dest, default, action,
type, help, choices, nargs for every action) and differs in **exactly one
field** — `--coal-econ-marginal-hr-bound` default `False` -> `None`. Commit
`2554517` (ERCOT-115 promotion, owner sign-off 2026-07-26) moved the REGISTRY
default to the tri-state `None` precisely because a `False` default makes every
CLI run pass an explicit `False` and scrub the per-ISO default — but it never
updated the hand-written parser, so **the promotion has been inert on the
calibration path since it landed**. Wiring the registry is what makes it take
effect; owner-confirmed as intended.

Goldens (plan §8): NEISO captured before (pre-D4/D2 `scripts/`+`src/`) and
after, `regression_gate.py --mode byte` -> **PASS**, 9 files / 44 numeric
columns at `atol=0 rtol=0` across 2023-2025, zero gross reshuffle. Fidelity
oracle clean both sides (215 recorded flags replayed identically, 597
scenario_config keys matched, 0 drifted). The gate's check [4]
(`legitimacy_diagnostics --keepers`, the FULL D-2 recompute) FAILs, but on
`2026-07-26-ercot115-coal-marginal-hr` and `2026-07-26-nyiso-81-floor-rederive`
— keepers registered earlier the same day and untouched by this branch, whose
committed and recomputed shares are identical (the C8 forced-share budget, not
a recompute drift). The CI-equivalent invocation (`--no-d2-recompute`, the only
one ci.yml runs) PASSes. `tests/test_pipeline_facade_shims.py` moved into
ci.yml's blocking facade job.

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

**RESOLVED 2026-07-26: regenerated, re-gated, committed.** Rule 14
`[R-ACCURATE]` decides it — the newer measured-capability basis is the accurate
one, so the stale artifact goes. `thermal_tranches_NEISO.csv` needed NO
regeneration (the exporter does not write it, and it re-derives identically);
only `bin_assignments_NEISO.csv` moved, on two axes:

* **One dispatch-relevant cell.** Plant 55042 (Bridgeport Energy Project,
  CC_REGULAR) `Nameplate_MW` 520.0 -> 538.0, i.e. +18 MW on a 14.6 GW binned
  fleet (+0.12 %). Rule-23 citation: `4fb54b53` (2026-07-14, "Unify CC capacity
  into one measured-capability stack" — measured > schema > net-summer, guard
  clipping to `max(nameplate, demonstrated_peak)`). Source-data/basis change,
  not a residual move.
* **46 provenance-label corrections, zero LP effect.** `Must_Run_Source`
  `chp_sector_default` -> `chp_campd_p2` (4 rows) / `chp_eia923_cf` (42 rows).
  The `Pct_*` share columns are byte-identical, so no floor moved: the committed
  artifact had been written while the thermal-tranche artifact was unresolvable,
  which is exactly the silent degrade `export_iso_bin_assignments._chp_floor_status`
  was later hardened against ("a missing artifact used to drop every CHP
  `Must_Run_Source` to `chp_sector_default` unnoticed"). The stale artifact was
  therefore MIS-ATTRIBUTING measured CHP floors as class defaults.

**Re-gate result: the NEISO keeper's dispatch is BIT-IDENTICAL.** A faithful
keeper re-solve (`capture_keeper_goldens --iso NEISO`, all three years,
fidelity oracle clean both sides: 215 recorded flags replayed identically, 597
scenario_config keys matched) on the regenerated artifact, diffed against the
same-code pre-regeneration capture:

| year | total gen | gross Σ\|Δ\| | plant 55042 own gen | mean LMP |
|---|---|---|---|---|
| 2023 | 96,992.1 GWh, Δ +0.000 | 0.000 GWh | 2,424.71 GWh, Δ +0.000 | $38.3040, Δ +0.00000 |
| 2024 | 103,928.4 GWh, Δ +0.000 | 0.000 GWh | 2,757.81 GWh, Δ +0.000 | $43.6204, Δ +0.00000 |
| 2025 | 107,326.1 GWh, Δ +0.000 | 0.000 GWh | 2,282.39 GWh, Δ +0.000 | $70.0462, Δ +0.00000 |

Zero delta even on the changed plant's own generation: the keeper's fleet build
resolves CC capacity through the same measured-capability stack that produced
the 538.0 MW figure, so the artifact's stale 520.0 was never the binding pmax on
this path — it was a stale MIRROR of a value the solve already computes. The
keeper verdict therefore cannot move, and no new bundle is registered (this is a
null-effect input correction verified by re-solve, not a new run — rule 14 has
nothing to report). `tests/test_neiso_bins.py` is fully green.

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

**VERIFIED LIVE ON MAIN 2026-07-26 (escalation follow-through), STILL AWAITING
EXPLICIT OWNER ACKNOWLEDGEMENT.** `frontend/data/backcast/calibration-complete.json`
at HEAD carries `complete: [NEISO]` and `withdrawn: [NYISO]`, so the rule-22 CI
quarantine gate and `run_calibration_full.py`'s marker check once again BLOCK
every NYISO out-of-training solve / score / registration, as the 2026-07-19
withdrawal intended. The 07-22 to 07-26 window in which they did not is closed.
This is a governance state change made by a triage session on the owner's behalf
— it stays flagged here until the owner confirms they saw it, because the
alternative reading (that NYISO really is calibration-complete) would re-open
the quarantine and is the owner's call, not a session's.

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
- ff-battery walker tests (`test_walk_inputs_trivial_single_year`,
  `test_resolve_report_no_hard_fail_full_horizon`,
  `test_ercot_confirmed_horizon_is_reported_not_failed`, and
  `test_build_registration_scorecard_no_iso_gate_open`, whose gate-c half
  walks the same input resolution) — these exercise the real
  input-resolution walker against the real tree, i.e. the definition of the
  `integration` marker ("exercises real data inputs", pyproject:41; the
  test_consume_* precedent). Mark `integration`; they run in the full
  pre-push lane where curation exists. (The scorecard test ALSO needed the
  D6 restore for its marker assertions — both causes were real.)

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

   **Membership shifted on 2026-07-26 with the Wave-5A `tests/` migration**,
   exactly as predicted for a pollution family: moving files between
   directories changes collection order, so which members lose the coin toss
   changes with no edit to any test's content. Measured across two full serial
   runs (`uv run python -m pytest --continue-on-collection-errors`, before =
   flat `tests/`, after = the migrated tree), the aggregate counts were
   **identical** — 39 failed, 5183 passed, 28 skipped, 8 xfailed, 234 subtests
   passed, 1 collection error — but four rows swapped:

   | Direction | Test |
   |---|---|
   | started failing | `tests/unit/data/test_cache_control.py::test_largest_retained_frames_is_sorted_and_limited` |
   | started failing | `tests/unit/data/test_coal_sync_tranche.py::TestCommittedTakeorpayRegulated::test_scope_set_membership_freeze` |
   | stopped failing | `tests/curation/test_consume_phase3d.py::EgridZoneAssignmentParity::test_zone_lookup_matches_raw` |
   | stopped failing | `tests/curation/test_derive_coal_sigmoid.py::TestProvenanceFreeze::test_miso_defaults_match_derive` |

   All four pass in isolation on the migrated tree, so all four are this
   family, not migration defects. They were left exactly as they are: editing
   an order-shift victim masks the shared-state leak rather than fixing it.
   The bisect this item asks for now has two more known members to work with.

   **RESOLVED 2026-07-26: bisected to one leaked process global.** The
   `lru_cache` hypothesis was wrong. `paths.set_eia860_vintage` flips a
   MODULE-LEVEL global re-pointing every EIA-860-derived loader at
   `data/raw/eia-860/vintage_<year>/`; `runner.run_scenario_iso` sets it once
   per solve from `ScenarioConfig.eia860_vintage_year` and NOTHING resets it on
   return. `tests/test_crossover_harness.py` drives a 2023-vintage ERCOT
   crossover through the real `run_scenario_iso`, so every later test reads the
   2023 snapshot for the rest of the session. The failures are therefore
   **deterministic given collection order**, not flaky — which is exactly why
   isolation "fixed" them and they read as noise.

   Bisect: 344 collected files, 1-141 -> 71-141 -> 71-105 -> 71-88 -> 80-88 ->
   `test_crossover_harness.py`, each step confirmed by running the candidate
   prefix plus the five victims; two-file repro at the end. Fixed at the
   polluter — an autouse teardown in `tests/conftest.py` restores the global
   after every test, generalizing the convention
   `test_cod_ramp.py::TestEia860VintageSelection` already carried by hand
   ("never leak a vintage into other tests"). No victim assertion, fixture or
   expected value was touched. The fifth victim
   (`test_outages::NEISOFloorOutageExemptTest`) shares the same cause.
3. The 7 remaining `xfailed` marks (all "pre-existing failure … tracked for
   follow-up", 2026-07-05) are still genuinely failing, so they are outside
   this triage's failure/xpass mandate — but none carries a real citation and
   each hides a real defect (e.g. the P2-storage leak into the P1 throughput
   metric, the NEISO scarcity-overlay default contradiction, the CAISO
   CC_REGULAR committed-band drift 0.90→1.0). They are the next tranche of
   this backlog.

   **RESOLVED 2026-07-26: all seven re-adjudicated, ALL SEVEN bucket A, every
   mark removed.** In each case the deliberate, cited change was correct and
   the TEST had drifted; the marks were hiding that rather than a defect in the
   code. Every assertion is re-cut against the mechanism it exists to guard,
   with the citation inline:

   | test | what the mark hid | resolution |
   |---|---|---|
   | `test_tranche_hr::test_emission_rate_ordering` | asserted a plant's CO2/MWh scales with its BID heat-rate multiplier — R2/EM-4 deliberately books CO2 at the PHYSICAL heat rate, since a block offered at a scarcity price does not emit more | **the xfail was preserving a physics error as expected behaviour.** Renamed + INVERTED to pin the correction |
   | `test_storage_metric_payload::test_uses_only_p1_pass` | "P2 leaks into the P1-only metric" — `_primary_pass` was added deliberately and documents the rule | renamed; pins the primary-pass rule both ways (incl. never summing passes) |
   | `test_offer_curve_deleakage::test_caiso_core_gas_bands_preserved` | CAISO LEVER A (FINDING-caiso-evening-merit): 0.90x priced min-stable-load below `econ_low`, an inverted merit order | literals re-frozen post-lever (CC_REGULAR 1.00, CC_CHP 1.00) |
   | `test_iso_config::test_other_isos_no_scarcity_overlay_default` | NEISO's fully-cited ISO-NE winter ORDC overlay | invariant re-cut: an ISO may default-enable only with its OWN grounded ORDC block |
   | `test_eia923_fuel::test_pjm_subbit_resolves_from_table_not_prb` | PJM subbit round-2 re-derive (floor 1.00 -> 1.22) | asserts the ROUTING, not a lane-owned level |
   | `test_caiso_per_hub_intertie::test_split_resolves_to_two_flow_columns` | `build_interface_groups`' tuple grew to carry `lower_cap_mw` + `signs` | unpack updated; both new fields asserted |
   | `test_caiso_bins::test_peaking_empty_for_artifacts_without_column` | PJM's artifact was regenerated WITH `peaking_pct` | degrade path now exercised hermetically + a no-artifact companion (ERCOT) |
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

## 8. Final numbers (after the fix commits, rebased onto main `64d06c4`)

```
26 failed, 5153 passed, 16 skipped, 44 deselected, 8 xfailed, 60 xpassed -> 0,
1 collection error, 228 subtests passed, 11m56s
```

Baseline → final: **141 + 2 + 60 → 26 + 1 + 0.** Every remaining red is an
open escalation from §4 or a §6 observation — nothing unclassified:

| Cluster | Count |
|---|---|
| D1 caiso-117 belly cap (collection error) | 1 error |
| D2 ff-g1 `transmission_expansion_enabled` (unapplied patch) | 4 |
| D3 ercot-93 steam-RT (rotted patch) | 8 |
| D4 orchestrator shim conversion (7 shims + flag-registry seam) | 8 |
| D5 NEISO bin-artifact drift (`4fb54b53` basis) | 1 |
| §6.2 order-dependent pollution family (test_fleet ×3, derive_coal_sigmoid, and — new on the rebased tree — `test_outages::NEISOFloorOutageExemptTest`, which also passes in isolation) | 5 |

Membership of that last row is order-dependent by construction and shifted
again when the Wave-5A `tests/` migration changed collection order; the swap
(same totals, four rows exchanged) is tabulated in §6.2.

The §6.1 perf test (`test_full_year`, 30 s budget) PASSED on the final run —
consistent with slow-host noise at the margin, kept as an observation. The 8
xfailed = the 7 legacy 2026-07-05 marks (§6.3) + this session's one cited B
(the W3-P1 basis-drift guard). The 44 deselected = the 40 baseline + the 4
`integration`-marked ff-battery walker tests.

**Flag decision: `continue-on-error` STAYS** — the tier is not green (27 red,
all owner-decision escalations). Flipping to blocking now would break every
lane's PRs on failures no lane session is allowed to fix unilaterally. The
ci.yml comment is corrected to these measured numbers.

## 9. Escalation follow-through — CLOSED 2026-07-26, tier flipped to BLOCKING

Every §4 escalation and §6 observation above now carries an inline resolution.
Summary of what closed them:

| Cluster | Resolution |
|---|---|
| D1 caiso-117 belly cap | Owner: record the drop. Test C-deleted; FINDING §Inv-2 relabelled the rebuild recipe. |
| D2 ff-g1 gate | Owner: apply in full. Patch had rotted; every hunk re-anchored by hand. Pin `edbc1b103207170a` unmoved. |
| D3 ercot-93 steam-RT | Owner: record the drop. 8 tests C-deleted; three false "MERGED on main" claims corrected. |
| D4 orchestrator shims | Converted under goldens (`--mode byte` PASS, 9 files / 44 columns, `atol=rtol=0`). Two persist drifts forward-ported first; surfaced a live ERCOT-115 defect (the promotion was inert on the CLI). |
| D5 NEISO artifact | Regenerated on the `4fb54b53` basis + keeper re-gated: bit-identical dispatch, all three years. |
| §6.1 perf test | Still an observation; passed again on the final run. |
| §6.2 pollution family | Bisected to a leaked `set_eia860_vintage` process global; fixed at the polluter. |
| §6.3 legacy xfails | All seven re-adjudicated bucket A; all marks removed. |
| §6.4 / §6.5 doc staleness | §6.5's two false claims corrected with D1/D3. §6.4 (CLAUDE.md's "CAISO 3 zones") remains for a `/sync-docs` pass. |

One defect was found that pre-dates none of the above and is not in this
document's original classification: `calibration_verdict.FORCED_EXEMPT_MECH_NAMES`
had not been extended when caiso-124 (`1e00d6b`, the same day) added
`MECH_HYDRO_MIN_FLOW` to `floor_mechanisms.NON_THERMAL_MECHS` — a 28th failure,
caught by the guard test written for exactly that drift, fixed here.

**Final measured tier state (same command as §0):**

```
5187 passed, 16 skipped, 44 deselected, 1 xfailed, 5 warnings,
228 subtests passed, 12m39s
0 failed, 0 collection errors, 0 xpassed
```

Baseline → here: **141 failed + 2 errors + 60 xpassed → 0 + 0 + 0.** The single
remaining xfail is this triage's own cited bucket-B mark (§8), which carries its
removal condition in the mark. `continue-on-error` is REMOVED from ci.yml's fast
tier and the step renamed; a red there is now a real regression.
