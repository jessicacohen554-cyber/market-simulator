# FINDING — Y-16: the rule-22 tier marker is re-checked at REGISTRATION (owner ruling R-AZ)

**Date:** 2026-09-06 · **Lane:** Model Audit & Release-Finalization Program, Y-16 ·
**Branch:** `claude/y16-registration-tier-marker-recheck-797rze` · **Pin:** `76886c2e` (origin/main)
**Status:** CLOSED — implemented, tested, no registered run affected.

> **Scope in one line.** A fourth rule-22 gate, at the seam where a run's solve years become a
> committed sidecar. The launch-time gate's semantics are unchanged; no marker, freeze, keeper
> shard, matrix shard, bench part, board or plan was touched; nothing was solved, scored or
> registered.

---

## 1. The ruling and the hole it closes

**R-AZ** (owner, audit-program director sitting 2026-09-06 ~00:15Z, card "Marker gate"; option
taken verbatim: *"Re-check at registration (Recommended)"*).

Rule 22 `[R-HOLDOUT]` gates the **spend** of an out-of-training year — solving it, scoring it,
registering it. Before this change, three gates enforced that, and each read the marker at a
moment that was not the moment of the spend it protects:

| gate | reads the marker | protects |
|---|---|---|
| `run_calibration_full.enforce_holdout_year_gate` | at **solve launch** | the solve |
| `legitimacy_diagnostics.run_d6_quarantine` (CI `quarantine-gates`) | at **PR time** | the merged tree |
| `audit_keepers` H1 | at **audit time** | the keeper record |

Nothing read it at the moment a run's years were written into
`frontend/data/backcast/registry/<id>.json`. An LP is hours long, so a run can outlive the
authorization it launched under.

**The case is Z-6** (`docs/handoffs/holdout-2022-completeness-ercot-nyiso-2026-09-05.md` §1a,
read and verified): the nyiso-189 recipe was replayed on 2022 with `--holdout-authorized`, legally,
under NYISO's D56-R `complete` marker. **While the LP ran**, `main` withdrew that marker
(nyiso-193 — keeper moved to `2026-09-05-nyiso-192-astoria-panel`, NOT-YET under the Q5 uniform
rule). The lane reverted its own registration commit at merge. That was correct, and it was
*discipline*: at the moment the sidecar would have been written, no tool would have objected. CI's
D-6 sweep would have caught it on the PR — after the artifact existed and after the number had been
read. R-AZ moves the refusal to the write.

## 2. The seam

`scripts/dashboard_add_run.py::main` is the single writer of a backcast registry sidecar. Verified
by sweeping every `scripts/**.py` reference to the registry directory: every other hit is a
**read** (`audit_keepers`, `build_manifest`, `build_status`, `calibration_verdict`,
`check_*`, `legitimacy_diagnostics`, `regen_dashboard`, `prune_iso_runs`, `bundle_io`) or an
**update in place** of an existing sidecar (`stamp_touchpoint_holdout.py`). `regen_dashboard.py`
re-renders payloads from sidecars that already exist and creates none. The forecast namespace
(`register_forecast_run.py`) is a separate registry and out of scope by rule 15.

Within `main`, the ordered facts are: `entry = rb.manifest_entry(label, bundle)` yields the run's
`iso` and its `years` (straight from the bundle's `meta.json`), and only afterwards is anything
written — the sidecar (`dashboard_add_run.py:333`), the `runs/<id>.js` payload and the bench parts
(`rb.generate`, `:339`). The gate goes between them, at `:322`.

## 3. What was implemented

**`scripts/lib/holdout_policy.py::registration_refusals(years, iso, marker_doc, freeze_doc)`**
(`:281`) — the policy. It composes the module's existing primitives and adds **no second tier
map**: `frozen_tiers` first and fail-closed (an ACTIVE freeze with no parseable scope covers every
tier), then `split_breach_by_tier` + `authorized` per tier. Same precedence as the launch gate, so
the two can never disagree about which year needs which block. Returns one refusal string per unmet
tier, each naming the ISO, the years, the tier, and the marker/freeze state.

**`scripts/dashboard_add_run.py::enforce_registration_marker_gate(iso, years, repo=None)`**
(`:163`) — the gate. Reads both documents off disk **on every call** (that freshness is the whole
ruling), delegates the decision, and `sys.exit`s with the refusals plus the ruling citation and the
remedy. Called at `:322`, before any write, so a refused run leaves no sidecar, no payload, no
bench part.

**No bypass flag.** There is deliberately no `--holdout-authorized` counterpart at registration:
a registration that fails this check is not a registration. The remedy named in the refusal is an
explicit owner act restoring the marker and a re-registration, or the run stays unregistered and
git history is the record (rule 15).

Refusal text as it actually prints (the Z-6 shape, reproduced in test):

```
error: REGISTRATION REFUSED (CLAUDE.md rule 22 [R-HOLDOUT]; owner ruling R-AZ, 2026-09-06 —
the tier marker is re-checked at registration, not only at solve launch).
  NYISO year(s) [2022] are validation-tier, and NYISO does not carry the 'complete' marker in
  frontend/data/backcast/calibration-complete.json AT REGISTRATION TIME (a marker present when
  the solve LAUNCHED does not authorize a registration after it was withdrawn)
There is no bypass flag. Either the ISO's marker is restored by an explicit owner act and the
run is re-registered, or the run is not registered — git history is the record (rule 15).
```

## 4. Tests — `tests/scoring/test_registration_marker_gate.py` (17, all passing)

Hermetic: every marker/freeze document is written into `tmp_path`; the committed documents are
only ever **read**, in the last class.

- **Policy layer (8).** In-sample 2023–2025 never refuses, marker file or not. A `complete` ISO
  passes on 2022. The **Z-6 shape** — marker withdrawn — refuses, and the message carries ISO,
  year, tier and block. A **locked-test** year (2019 and 2026) refuses for **every** ISO while the
  freeze names `locked_test`, including an ISO that holds `final`. An unenumerated year (2018,
  2027) fails closed to locked-test. An ACTIVE freeze with no parseable scope freezes the
  validation tier too. A mixed span names both unmet tiers and leaves the in-sample year out.
- **Gate layer (6).** The same 2022 run passes with the marker and is refused without it — the
  ruling's exact before/after. Locked-test refused for all six ISOs. In-sample untouched with no
  marker file present at all. A missing marker file fails closed. `repo=None` reads the module
  root at call time (so the existing monkeypatch pattern keeps working).
- **`main()` end-to-end (2).** A refused registration writes **no** sidecar, creates **no**
  `runs/` directory, and never reaches the payload renderer; the identical run with the marker
  present registers normally.
- **Committed record replay (1).** Every registry sidecar at HEAD whose `years` leave 2023–2025 is
  replayed through the new check against the **committed** marker and freeze documents and must
  return zero refusals — plus the invariants that they all belong to `complete` ISOs and that no
  locked-test year has ever been registered.

## 5. Confirmation that nothing already-registered breaks

| check | result |
|---|---|
| `scripts/audit_keepers.py --check` | **PASS: 0 failures, 0 warnings** (holdout / marker / status rows all clean) |
| `scripts/check_registry_payload_parity.py` | **OK** — 14 runs checked, 47 bundle dirs swept, 0 known-unsynced tolerated |
| `tests/scoring/test_holdout_year_gate.py` + `test_dashboard_add_run_sidecar.py` + `tests/regression/test_recipe_replay_gates.py` + `tests/scoring/test_full_forward_hindcast.py` + `test_rubric_consts.py` | 99 passed, 17 subtests passed |
| `ruff check` + `ruff format --check` on all three touched files | clean |

The five holdout-year sidecars on `main`, replayed through the new check against the committed
marker (`complete` = ERCOT, NEISO, PJM) and freeze (`scope.tiers = ["locked_test"]`):

| sidecar | ISO | years | tier | verdict |
|---|---|---|---|---|
| `2026-09-05-neiso-2020-2021-touchpoints` | NEISO | 2020, 2021 | validation | **valid** |
| `2026-09-05-neiso-2022-touchpoint-k99` | NEISO | 2022 | validation | **valid** |
| `2026-09-05-pjm-2022-2021-touchpoints` | PJM | 2021, 2022 | validation | **valid** |
| `2026-09-05-run249-2022-touchpoint-forward` | ERCOT | 2022 | validation | **valid** |
| `2026-09-05-run250-2022-touchpoint-carveout` | ERCOT | 2022 | validation | **valid** |

No locked-test year is registered anywhere, so the freeze leg is inert against the current record —
as it should be.

## 6. Deliberately not changed

- **The launch-time gate.** `enforce_holdout_year_gate` keeps its flag, its warnings and its
  semantics exactly. The registration check is additional, never a replacement: a solve still
  needs `--holdout-authorized` **and** the marker to start.
- **D-6 and `audit_keepers`.** Untouched. One asymmetry is recorded rather than repaired: the
  registration gate consults the **freeze** as well as the marker (fail-closed), while
  `run_d6_quarantine` reads the marker alone. It is inert today — the freeze covers the locked
  test and no locked-test year is registered — and closing it was outside this dispatch.
- **A pre-existing observation, not a change.** `main`'s post-registration scorer call is wrapped
  in `except Exception`, which does not catch the `SystemExit` `calibration_verdict.load_artifacts`
  raises for a missing sidecar. Only reachable when the sidecar write is bypassed (i.e. in tests),
  so it is noted, not touched.
- Markers, the freeze file, keeper shards, matrix shards, bench parts, the board and the plan.
  Nothing was solved, scored or registered by this session.

## 7. Files

| file | change |
|---|---|
| `scripts/lib/holdout_policy.py` | `+registration_refusals` (the policy; +73 lines) |
| `scripts/dashboard_add_run.py` | `+_load_json_doc`, `+enforce_registration_marker_gate`, call site at `:322`, module-docstring note |
| `tests/scoring/test_registration_marker_gate.py` | new, 17 tests |
| `CLAUDE.md` | rule 22 Enforcement clause — the registration-time paragraph, cited to R-AZ |
| `docs/governance/rule-history.md` | §4 dated entry + changelog row |
