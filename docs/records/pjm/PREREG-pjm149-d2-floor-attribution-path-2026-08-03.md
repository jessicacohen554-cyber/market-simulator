# PRE-REGISTRATION — pjm-149: D-2/D-4 floor attribution is PATH-DEPENDENT on the dispatch source. Census populations, the dispatch contract, acceptance gates and stop rules, committed BEFORE any number that decides them

**Session:** pjm-149 (cross-ISO scoring infrastructure). **Date:** 2026-08-03.
**Branch:** `claude/d2-floor-attribution-path-06l2it`.
**Lane:** the side finding filed by pjm-148 —
`results/calibration/FINDING-pjm148-chp-host-steam-refused-2026-08-03.md` §4,
successor item §6.3 ("the D-2 payload path-dependence deserves its own cross-ISO
charter"). Its §5 DO-NOT-REDO binds this session.

**This is an AUDIT / SCORER charter, not a mechanism lever** (rule 28a). It
re-tests NO adjudicated matrix cell, arms NO mechanism, adds NO `ScenarioConfig`
field, tunes NO parameter, and changes NO solve —
`scripts/legitimacy_diagnostics.py` is diagnostic metadata; nothing in the LP
build reads it. Its matrix vehicle, if any cell's evidence moves, is the
EXISTING cross-cutting audit row family (`diagnostics_plant_set_census`, the
caiso-155 vehicle), not any ISO's lever queue. **No keeper is promoted from this
session.**

**LP budget: ZERO.** No solve, no dashboard registration, no rule-22 marker.
Floors are reconstructed through the standing G-06 path
(`run_year(fleet_only=True)` from each bundle's own `meta.json`), which exits
before any LP is constructed. Holdout: **2023–2025 only**;
`holdout-freeze.json` is ACTIVE, untouched, and outranks everything. No GitHub
Actions workflow is added (private repo, billed minutes).

**Keepers at entry** (read from `frontend/data/backcast/keepers/*.json`, this
session, before any measurement):

| ISO | keeper | bundle |
|---|---|---|
| ERCOT | `2026-08-02-ercot150b-zonal-anchor` | `results/calibration/ercot150_zonalanchor_B` |
| PJM | `2026-08-03-pjm-147b-chp-heat` | `results/calibration/pjm147_chp_B` |
| CAISO | `2026-08-03-caiso156-meter-screen-b` | `results/calibration/caiso156_meter_screen_B` |
| NYISO | `2026-08-02-nyiso-113-li-locational` | `results/calibration/nyiso113_lilocational_B` |
| NEISO | `2026-08-03-neiso-caiso156-meter-screen` | `results/calibration/neiso_c156_meter_screen_B` |
| MISO | `2026-08-03-miso-117b-ct-heat` | `results/calibration/miso117_ctheatrate_B` |

Verified by `ls` before this file was committed: **none of the six bundles
commits `floors/` or `dispatch/`** — every one of them re-scores on the payload
path with a floors rebuild.

---

## 1. The defect, restated precisely from code at HEAD (before any measurement)

`scripts/legitimacy_diagnostics.py::diagnose_bundle` resolves the per-plant
model dispatch map `model_plants_plant` from ONE of two sources:

1. `dispatch/<year>_<pass>.parquet` — the solve's own unit-hour frame, **every**
   model unit (`run_calibration_full.py:4909` writes the unfiltered frame; only
   the `plant_code > 0` filter and, for endogenous-WECC CAISO, the external-zone
   exclusion remove rows). Gitignored, so **absent from every committed bundle**;
   present only while the producing session is still running.
2. the dashboard **run payload** (`load_payload_plants`) — keyed by the CAMPD
   bench plant ids, **311 plants for PJM 2023**.

D-2/D-4's row set is then built at `scripts/legitimacy_diagnostics.py:2325-2327`:

```python
all_pids = [p for p in model_plants_plant if p in klass_by_pid or p in pid_strs]
```

The comprehension iterates **the dispatch map**, so a plant that is FLOORED
(present in `pid_strs` / `klass_by_pid`, i.e. carrying a positive `min_gen`)
but ABSENT from the dispatch map is **silently dropped** — no row, no failure,
no note. On path 1 the dispatch map holds every model plant, so nothing is
dropped. On path 2 it holds only bench-keyed plants, so **every floored plant
with no CAMPD bench entry loses all D-2 and D-4 attribution.**

The caiso-155 fix (`pseudo_pids`, line ~2345) already re-admits ONE family of
the drop — `plant_code <= 0` interchange pseudo-units, keyed `u:<unit_id>` —
under the floor-energy convention. It re-admits **only** keys starting with
`PSEUDO_PLANT_KEY_PREFIX`; real plants absent from the payload stay dropped.
The membership filter itself **predates** caiso-155 (`git log -S "if p in
klass_by_pid or p in pid_strs"`), so this is **not** a caiso-155 regression and
that question is not re-litigated here.

**Reproduced by pjm-148, no LP:** `pjm144_control_A` — whose own committed
`legitimacy_diagnostics.json` records `CC_CHP chp_steam 0.9938 TWh` — recomputes
to **zero CC_CHP rows** at HEAD, with the log line `model dispatch from run
payload … (311 plants)`; none of PJM's 14 CC_CHP plant codes appears in the
payload. Same bundle, same dispatch, different path.

**Why the corpus is exposed rather than just one bundle:** the calibration
protocol mandates scoring on the committed slim file set, i.e. path 2. But
`legitimacy_diagnostics.json` is *written during the producing run*, while
`dispatch/` still exists — i.e. on path 1. So the committed corpus is a
**mixture** of the two paths, and which path a given keeper's artifact was born
on is not recorded anywhere. Census population C6 measures that mixture.

## 2. Pre-registered census populations (measured AFTER this file is pushed)

Per keeper bundle × year, all six ISOs × 2023/2024/2025, payload path + G-06
floors rebuild, **no LP**:

* **C1 — payload-absent floored REAL plants.** Keys from
  `aggregate_floors_by_plant` that are numeric (`plant_code > 0`, i.e. not the
  `u:` pseudo-unit family caiso-155 already handles), carry
  `max_t min_gen > D2_FLOOR_MIN_MW` (1.0 MW), and are **absent** from
  `model_plants_plant`. Reported per row: plant code, `plant_group` (class),
  mechanism ids present, hours floored, mean/max floored MW, annual floor
  energy (TWh).
* **C2 — the lost rows.** The (class, mechanism) D-2 rows and the D-4 rows that
  exist when C1 plants are admitted but not at HEAD, per ISO-year. This is the
  charter's scope item 1 deliverable.
* **C3 — NON-EXEMPT exposure (the escalation trigger).** The subset of C1 whose
  class is **not** in `D2_EXEMPT_CLASSES` (`CC_CHP`, `CT_CHP`, `ST_CHP`,
  `nuclear`) and **not** the unclassified `""` bucket — the two families
  `run_d2` already excludes from its gated summary. A non-empty C3 means a
  **gated** class's denominator (and possibly its numerator) is wrong at a
  committed keeper: a live scoring error, escalated per the charter, not a
  bounded curiosity. **The pjm-148 claim that the defect moves no determination
  is treated as a HYPOTHESIS to be tested per ISO here, never as a premise.**
* **C4 — control, must not move.** Every payload-PRESENT plant: its dispatch
  row, class, floors and mechanisms must be identical pre/post fix.
* **C5 — the complement, must stay out.** Model-fleet plants absent from the
  payload AND unfloored (≤ 1 MW in every hour). These must remain excluded —
  they carry no floor and must not perturb any class denominator. Counted only.
* **C6 — committed-corpus path census.** For each of the six keepers, whether
  the COMMITTED `legitimacy_diagnostics.json` was born on path 1 or path 2,
  inferred from artifact evidence (presence of D-2 rows for classes that carry
  no bench/payload entry — e.g. `""`-bucket `nuclear_mustrun`, CHP classes).
  This says which committed keepers' numbers the fix would move.
* **C7 — parquet-path no-op.** The claim "the fix is a no-op wherever
  `dispatch/` exists" requires every floored `plant_code > 0` key to be present
  in the parquet-derived dispatch map. No committed bundle carries `dispatch/`,
  so this is **not** measurable on the corpus; it is (a) argued from the writer
  (`run_calibration_full.py:4909` writes the unfiltered unit-hour frame) and
  (b) **tested** by a synthetic unit test (gate A4). The one structural
  exception found in the writer — CAISO's endogenous-WECC external-zone
  exclusion — is reported explicitly rather than assumed harmless.

## 3. The pre-registered CONTRACT (committed before the census numbers exist)

The charter requires this be justified or rejected explicitly, not assumed from
the caiso-155 precedent. Both halves below are ISO-generic; no per-ISO branch.

### 3.1 Row set — path-independent (unconditional)

Every floored plant enters the D-2/D-4 matrices on **every** path. `all_pids`
stops being a filtered view of the dispatch map and becomes
`(dispatch-map plants that carry a class) ∪ (all floored keys)`. A floor is an
attribution fact about the fleet build; which dispatch artifact happens to
exist cannot decide whether it is reported.

### 3.2 Dispatch for a floored plant with no series on the active path — `disp := its own floor`

This **extends** PREREG-caiso155 §3's floor-energy convention from pseudo-units
to real plants. It is adopted not merely because it is the only quantity
derivable from committed data, but because it carries a **provable one-sided
bound** — the justification the charter demands, and one caiso-155 did not need
to state:

* **Numerator.** Forced energy is `Σ dispatch` over at-floor row-hours. Hours
  not at the floor contribute nothing, and at-floor hours have
  `dispatch ≈ min_gen`. So true forced energy ≤ `Σ_t min_gen` = floor energy.
  **Substituting the floor gives an UPPER BOUND on the numerator.**
* **Denominator.** LP feasibility guarantees `P ≥ min_gen` in every hour the
  unit is available, so the plant's true dispatch ≥ its floor energy.
  **Substituting the floor UNDERSTATES the denominator.**
* **Therefore the reported `forced_share` is an UPPER BOUND on the true share.**
  A gate that fails HIGH (rule 18 `[R-FORCED-BUDGET]`: FAIL when share > cap) is
  consequently **sound on a pass** — an upper bound under the cap proves the
  class is under the cap — and **indeterminate on a fail**, never a valid FAIL
  on its own.

This is strictly better than the status quo, which reports the share over an
unstated subset of the class with no bound in either direction.

**Disclosure is part of the contract, not an extra.** Every affected year emits
a note naming each plant scored under the convention with its class and floor
energy; the machine artifact carries the same list in a structured field; and
every D-2 **summary** row for a class containing such a plant is stamped
`upper_bound: true` (the mirror of the existing `lower_bound` flag that marks a
bridge-less floors rebuild). A number that is a bound must say so where it is
read.

### 3.3 Alternatives considered and REJECTED (stated ex ante)

* **`disp := 0`.** Fails to fix anything: `run_d2` skips a row whose forced MWh
  is ≤ 0, so the row still vanishes — and it asserts a dispatch the LP forbids
  (`P ≥ min_gen`). Rejected on both counts.
* **Exclude-but-disclose** (keep today's arithmetic; only add a note naming the
  dropped plants). Preserves every committed number, but leaves the row set
  path-dependent and leaves rule 18's *own* artifact without the attribution it
  is scored from. **Rejected as the primary fix; adopted as the disclosure half
  of §3.2.**
* **Apply `disp := floor` on the parquet path too**, for full value-level path
  independence. Would discard real measured dispatch (rule 14 `[R-ACCURATE]`)
  and rewrite the meaning of every artifact ever produced on path 1.
  **Rejected.**
* **Widen the run payload to carry every model plant.** The true long-run fix —
  it removes the information loss rather than bounding it — but it changes the
  dashboard payload format and would need every registered run re-emitted, and
  the payload is already the ~400 KB–1 MB object the push rules are built
  around. **Out of scope here; recorded as the named successor.**

### 3.4 What the contract does NOT decide

Whether the C8 rubric (`scripts/calibration_verdict.py`) should treat an
`upper_bound: true` over-cap class as INDETERMINATE rather than FAIL. That is a
rubric change with owner-visible consequences. It is opened **only if C3 is
non-empty**, and then as an escalation with the measured evidence — never
silently, and never inside this session's scorer commit.

## 4. Acceptance gates (ex ante)

* **A1 — reproduction baseline.** Per keeper bundle, regenerate the artifact
  in-session at HEAD (pre-fix) and diff against the committed
  `legitimacy_diagnostics.json`. Drift beyond G-06's documented reconciliations
  (the P0-pattern bridge family absent from rebuilt floors; per-class share
  jitter ≤ `D2_VERIFY_SHARE_TOL` = 2.5 pp on material classes) is diagnosed
  BEFORE proceeding. Every post-fix diff is taken against this same-session
  pre-fix regen, never against stale committed bytes.
* **A2 — confined delta.** Post-fix vs pre-fix regen, same bundle, same
  environment. **Unlike caiso-155 this is NOT expected to be purely additive**:
  a class that already had rows AND contains a C1 plant will see its
  `class_total_twh` rise and its `share_of_class` / `forced_share` move. The
  gate is that every delta is confined to (i) rows for C1 plants and (ii) the
  totals/shares of classes containing them, with **C4 rows bit-identical**. Any
  movement outside that set is a defect in the fix: stop and fix.
* **A3 — determination invariance through the production rubric.** Re-score
  every keeper through `scripts/calibration_verdict.py` (and the xiso-3
  instrument) on the pre-fix and post-fix artifacts. Criterion profile and
  determination must be IDENTICAL at all six ISOs. Any flip → **S1**.
* **A4 — parquet-path no-op, tested not asserted.** A synthetic test in which
  the floored plant IS present in the dispatch source must produce output
  identical pre/post fix. This is the charter's "prefer a fix that is a no-op
  wherever `dispatch/` exists" made falsifiable.
* **A5 — new-test coverage (charter scope item 4).** A payload-path bundle
  fixture carrying a floored, payload-absent plant must FAIL on HEAD and PASS
  after the fix, asserting the plant's rows are present in D-2 and D-4, that the
  disclosure note names it, and that the summary carries `upper_bound`.
* **A6 — suite health.** `pytest tests/scoring/test_legitimacy_diagnostics.py`
  plus the new tests green; `ruff format --check` clean on touched files;
  `scripts/check_mechanism_matrix.py` green. The two PRE-EXISTING failures
  (`test_clean_io.py::TestRegenerateEntrypoint::test_datatype_list_matches_schemas`,
  `test_consume_phase3d.py::EgridZoneAssignmentParity::test_zone_lookup_matches_raw`)
  are known clean-origin and out of scope; their status is re-checked at HEAD
  before the fix so a NEW failure cannot hide behind them.

## 5. Stop rules (ex ante)

* **S1 — determination or criterion flip at ANY ISO (A3).** STOP. No keeper
  motion, no shard edit, no matrix keeper-header restamp. Surface to the owner
  with the full per-ISO diff. Any subsequent keeper motion is scored
  leave-one-year-out within 2023–2025 first (rules 20/22).
* **S2 — C3 non-empty (a gated class is affected).** The scorer fix still ships
  — it converts a silent error into a visible one — but the affected ISO's
  numbers are reported per ISO in the FINDING, the rubric question of §3.4 is
  opened as an owner escalation, and **no keeper is re-gated in this session**.
* **S3 — blocked floors rebuild at an ISO** (the documented `pjm-da-virtuals`
  class of gitignored-input hazard). That ISO is censused statically from
  `meta.json` + config provenance, marked **BLOCKED**, and its artifact is NOT
  regenerated this session.
* **S4 — C1 empty at an ISO.** The defect is vacuous there; recorded as such,
  no artifact regenerated for it. If C1 is empty at **every** ISO the premise is
  refuted and no scorer change ships — pjm-148 has already shown this is false
  for PJM, so S4 is expected to bind per-ISO at most.
* **S5 — concurrent-lane collision.** `scripts/legitimacy_diagnostics.py` is
  shared by six concurrently-promoting ISO lanes. If a committed keeper's
  artifact would change, that is reported **per ISO before anything is
  regenerated** (charter scope item 3), and artifact regeneration for an ISO
  whose keeper shard has moved since this file's commit is deferred rather than
  raced.

## 6. Deliverables (fixed regardless of outcome)

1. Census probe `scripts/probes/_pjm149_d2_path_census.py` + its committed JSON.
2. `results/calibration/FINDING-pjm149-d2-floor-attribution-path-2026-08-03.md`
   with its own DO-NOT-REDO and a per-ISO statement of whether any committed
   keeper's D-2 numbers move.
3. The scorer fix + tests (A4/A5), only if the census is non-vacuous.
4. Regenerated `legitimacy_diagnostics.json` for affected keepers **only** if
   A2/A3 pass and S5 permits; `calibration-keeper-auditor` run afterwards.
5. `docs/calibration-log/governance.md` entry (cross-ISO — **not** a per-ISO lane
   file).
6. Rule 28b matrix stamp **only if** a mechanism cell's evidence actually
   changes; a scorer-visibility fix that moves no cell gets no stamp.

## 7. Rule compliance declared ex ante

Rule 12 `[R-PARALLEL]` (no solve at all), rule 15 `[R-DASHBOARD]` (no solve ⇒ no
registration — the pjm-131 / neiso-71 / caiso-155 no-LP precedent), rule 16
`[R-ALLYEARS]` (every measured quantity spans 2023/2024/2025), rule 22
`[R-HOLDOUT]` (2023–2025 only; freeze untouched), rules 1/19/20/21/23/24/25
(nothing tuned, no mechanism armed, no parameter derived, no per-ISO branch in
shared scorer structure), rule 27 `[R-PUSH]` (`legitimacy_diagnostics.py` is
≥ 300 lines ⇒ **local `Edit` only, never a regenerated full-file push, and blob
verification immediately after any push touching it**; model assignment Opus per
the charter).
