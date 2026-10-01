# FINDING — FR-22 GAP DECLARATIONS + THE FAST-TIER-GREEN EVIDENCE (G2 leg 2)

**Date:** 2026-09-03 · **Lane:** `claude/fr22-gap-fast-tier-green-n9n7by` ·
**PR:** see §7
**Executes:** owner ruling **R-X** (2026-09-02) — on the
`ercot_storage_adaptive_expectation` + `ercot_adaptive_event_release`
backcast→forecast fork routed by R-W (`docs/FINDING-fast-tier-repair-2026-09.md`
§3.8 + §7.1), the owner ruled **FILE GAP DECLARATIONS**, the FFR-1E precedent
route the two storage-envelope fields took.
**Evidence base:** R-W's finding (§3.8, §4, §6, §7), the FFR-1E filing record
(`docs/handoffs/ffr-1e-forecast-parity-check-2026-07-31.md` §4 and its
adjudication note), `scripts/lib/forecast_parity_registry.py`, director board
v21/v22's leg-2 corrections, and `scripts/check_forecast_parity.py` run on
the current keepers AND on the keepers `main` carried at R-W's pin.
**Scope discipline:** no solve · no workflow edit · no matrix edit (a GAP
declaration tests no mechanism) · no keeper shard, marker, freeze file or
`program-status.json` touched · no test loosened (the `_FR22_OPEN_UNACCOUNTED`
pin is REVIEWED, not extended; the strict xfail is untouched) · no
`BACKCAST_ONLY` claim and no forward wiring anywhere.

---

## 0. Result

**G2 leg 2's criterion, verbatim from board v21:** *"one completed
fast-tier-green `ci.yml` run"* — a completed `ci.yml` run whose **`Fast test
tier` job concludes success**. The claim against it is made in §7 from the
run's own API record and nowhere else; §0 states only what this lane did.

| item | outcome |
|---|---|
| R-X's two ERCOT fields | **declared GAP** in `forecast_parity_registry.py` (one row, this doc as `finding`) — §1 |
| the job as R-W scoped it | **larger than R-W saw**: seven unaccounted fields on `main`, not three; three of the extra four were already armed at R-W's pin and masked by the test's assertion order — §2 |
| the three non-ERCOT fields | two accounted as `PARAMETER_OF` already-declared rows (registry bookkeeping, no disposition made); one filed GAP under the R-X route as a same-class fork, **flagged as the one row beyond the ruling's letter** — §3 |
| `_FR22_OPEN_UNACCOUNTED` pin | reviewed: exact, both members still live, **unchanged** (no shrink available, no extension permitted) — §4 |
| fast tier, local, CI's exact command | `1 failed, 7807 passed, 34 skipped, 2 xfailed` — the parity test is green; the one red is a NEW `main`-content forecast-board re-key (three promotions after R-W's run) in a file this lane may not touch — §5.1 |
| rider: `ruff format` on R-W §7.2's three files | done, own commit; the job is still red on `main` content — two `E731`s fail the lint step, and **ten further files** would fail the format step — reported, not fixed — §6 |
| CI evidence and the leg-2 statement | run 2344: `Fast test tier` **failure**, same one test as local. **Leg 2 NOT SATISFIED; not claimed.** Now BLOCKED on the forecast-board re-key, not on parity — §7 |
| routed items + R-W's process finding carried forward verbatim | §8 |

---

## 1. The ruling and the two declarations (job 1)

R-W §3.8, measured and unchanged at this lane's start: the only consumer of
either field outside `scenarios.py` is `scripts/run_calibration.py` (the
two-pass ercot-221 block at ~5513, the ercot-223 release mask at ~5596 — line
numbers drift; the block is the one headed *"ercot-221 ADAPTIVE-EXPECTATION
storage offer"*). `src/market_sim/runner.py` and `pipeline/` carry no
reference. The ERCOT forward keeper `2026-08-25-234-eastex-identity` arms both
(`run_config.json`: `ercot_storage_adaptive_expectation = True`,
`ercot_adaptive_event_release = True`; `ercot_adaptive_fixed_point = False`,
`ercot_storage_reservation_offer = False`, so the rule-19 exclusivity check in
that block is not tripped).

**One registry row, disposition `GAP`, exactly per the FFR-1E pattern**
(`fields`, `disposition=GAP`, `why`, `finding` = this document,
`evidence=("scripts/run_calibration.py",)` — the checker verifies the evidence
path exists and names at least one of the fields, and that the `finding` path
exists). The `why` states the fork and names the forward question as the
forecast desk's, in the ruling's own terms: *the fork is declared KNOWN and
TRACKED, not silenced — the wire-forward question routes to the capx/forecast
desk deliberately and is NOT decided here.* No `BACKCAST_ONLY` claim, no
forward wiring, no edit to any consumer, no matrix edit.

What a GAP row does and does not do, so nobody reads it as a fix:
- `check_forecast_parity.py` reports the row as `GAP` on every run and counts
  it in the header (`8 filed gap(s)` → `12`, §5 — the header counts armed
  field verdicts across the six keepers, so the ERCOT pair adds two, §3.3
  adds one and §3.2 adds one through its parent); the fields are no longer
  `UNACCOUNTED`, so `test_all_six_keepers_resolve` stops reddening on them.
- The dedicated `FR-22 backcast->forecast parity` job (DO-NOT-REQUIRE, H-1)
  stays red — on the two pinned fields (§4), not on GAPs (the checker's default
  exit code counts only UNACCOUNTED; `--strict-gaps` would also fail on GAPs).
- Nothing about a solve changes (rule 24 `[R-REGISTRY]`: the registry is a
  governance artifact read by a no-LP checker and its tests).

---

## 2. The job was larger than R-W saw — seven, not three

`scripts/check_forecast_parity.py` at this lane's start (`main` = `c73f78f5`,
the caiso-239 promotion merge) reads **7 unaccounted**, not R-W's 3:

```
FAIL  ERCOT: ercot_adaptive_event_release          (R-X)
FAIL  ERCOT: ercot_storage_adaptive_expectation    (R-X)
FAIL  ERCOT: ercot_storage_as_soc_reserve          (pinned, house-2)
FAIL  CAISO: caiso_offer_surface_measured_ungrounded
FAIL  NYISO: nyiso_seam_deliverability_envelope    (pinned, house-2)
FAIL  NYISO: nyiso_seam_par_attribution
FAIL  MISO:  miso_seam_envelope_hour_ending_key
```

**These are not new since R-W.** The checker, the registry, the test and
`keeper_store` are byte-unchanged between R-W's pin `dfc44d95` and `c73f78f5`
(`git diff --stat` empty on all four). The keepers `main` carried AT `dfc44d95`
already armed the three: swept directly with `--keeper-config` on those
bundles' `run_config.json`:

| ISO | keeper at `dfc44d95` (promoted) | field | value |
|---|---|---|---|
| CAISO | `2026-09-01-caiso-231-b1-ungrounded` (2026-09-01) | `caiso_offer_surface_measured_ungrounded` | True |
| NYISO | `2026-08-30-nyiso-159-loss-surface` (2026-08-30) | `nyiso_seam_par_attribution` | True |
| MISO | `2026-09-01-miso-198-oomlevel` (2026-09-01) | `miso_seam_envelope_hour_ending_key` | True |

(`SUMMARY: 3 keeper posture(s); 4 unaccounted` — the fourth is the pinned
NYISO envelope.) The current keepers (`caiso-239`, `nyiso-177`, `miso-201`)
inherit the same values.

**Why R-W's §3.8 saw only ERCOT.** `test_all_six_keepers_resolve` iterates the
reports in sweep order and asserts per ISO; ERCOT is first, so the assertion
that fails names ERCOT's two fields and the test stops there. CI's `1 failed`
is one test function, whatever the number of ISOs behind it. R-W quoted the
checker for ERCOT and reported "exactly this one red" — correct as a test
count, incomplete as an adjudication scope. **Filing R-X's two rows alone
would have moved the red from ERCOT to CAISO and left leg 2 exactly where it
was.** That is the measurement that shaped §3.

---

## 3. The three non-ERCOT fields — what was filed, and what was not decided

Rule for this section: the registry's own disposition semantics decide what is
bookkeeping and what is an adjudication. Two of the three are parameters of
mechanisms the registry already carries; the third is a mechanism.

### 3.1 `miso_seam_envelope_hour_ending_key` → `PARAMETER_OF miso_seam_flow_limit` (bookkeeping)

miso-175's hour-ENDING stamp convention for the measured (month × hod)
seam-envelope cap key. Its only reads are the two `_seam_hek = getattr(config,
"miso_seam_envelope_hour_ending_key", False)` lines inside the
`miso_seam_flow_limit` and `miso_seam_export_limit` blocks of
`scripts/run_calibration.py`, passed as `hour_ending_key=` to
`inject_miso_seam_flow_limit`. That is precisely the registry's existing
treatment of its sibling `miso_seam_envelope_merit_cap` (`PARAMETER_OF
miso_seam_flow_limit`). The checker resolves it through the parent →
`BACKCAST_ONLY` (the seam-envelope family's declared disposition), reported
`INERT` in any keeper where the parent is off. **No disposition was made
here** — the row says "this is a parameter of X", which is a fact about the
code, and inherits X's standing declaration.

### 3.2 `caiso_offer_surface_measured_ungrounded` → `PARAMETER_OF caiso_offer_surface_measured` (bookkeeping)

caiso-231's scope extension of the measured CAISO offer surface to the
un-grounded CHP / ST_GAS classes. Its one consumer
(`src/market_sim/pipeline/backcast_config.py`, the `if
caiso_offer_surface_measured_ungrounded and iso.upper() == "CAISO"` block)
raises `ValueError` unless `caiso_offer_surface_measured` is armed and merges
the SAME measured artifact's CC/CT bands onto three more classes. The parent
is FFR-1E's filed GAP **F-5**; the child resolves to that GAP through the
parent. **No disposition was made here** — it inherits F-5's filing and its
open question (wire the measured surface forward, or not) unchanged.

### 3.3 `nyiso_seam_par_attribution` → `GAP` (filed under the R-X route — the one row beyond the ruling's letter)

nyiso-127's full-seam PAR attribution: all four `NYISO_external` border-link
caps rebuilt from the measured MIS P-32 per-neighbour schedules, the SCH-PJ-NY
row split hour by hour by NYISO's published PAR shares. It SUPERSEDES the
nyiso-125 two-link envelope (`nyiso_seam_deliverability_envelope`; exactly one
of the two applies, rule 19), is armed in the NYISO keeper since nyiso-159, and
is consumed only in the backcast orchestrator's TTC overlay block
(`scripts/run_calibration.py`, the `nyiso_seam_par_attribution … and iso ==
"NYISO"` branch). It is a mechanism, not a parameter, so §3.1/§3.2's treatment
does not apply.

**It is the same defect class R-X ruled on** — a keeper-armed mechanism whose
only consumer is the backcast orchestrator, surfaced by the same test on the
same run — and this lane filed it the same way: `GAP`, with this document as
`finding`. Why that is the honest disposition and not an adjudication:

- FFR-1E's own adjudication note (§4): *"these are forecast-reachability gaps,
  not claims that arming them forward is correct. A follow-up session may
  legitimately conclude that a mechanism belongs in (b) instead — in which
  case the deliverable is a declaration with its reason, not silence."* GAP is
  the disposition that decides nothing; that is exactly why the owner chose it
  for the ERCOT pair.
- The open question is real and is named in the row's `why`: the mechanism
  sits in the measured-TTC family (`ercot_gtc_limits_measured`,
  `pjm_measured_interface_limits` — declared `BACKCAST_ONLY` because the
  transmission-expansion registry owns forward TTC), yet its own sibling
  envelope was deliberately left pinned OPEN by house-2 rather than declared
  `BACKCAST_ONLY`. This lane makes **no** `BACKCAST_ONLY` claim, per the
  charter; the forecast desk decides, and either answer is a one-line edit to
  the row.
- The alternative was to leave it undeclared, which leaves
  `test_all_six_keepers_resolve` red on NYISO and leg 2 blocked for a fourth
  cycle on a field the owner has not been shown. Extending the
  `_FR22_OPEN_UNACCOUNTED` pin instead is loosening a test to get green,
  forbidden to this lane and explicitly refused by R-W §7.1.

**Flag for the owner:** this row is filed under R-X's route, not under R-X's
text, which named the two ERCOT fields. If the owner would rather it had come
back as a routed item, reverting is one row and the tier goes red on NYISO
again — nothing else moves.

### 3.4 What this lane did NOT file

`ercot_storage_as_soc_reserve` and `nyiso_seam_deliverability_envelope` — the
two house-2 pinned fields — stay UNACCOUNTED and pinned (§4). They were not
part of R-X, have been open since 2026-08-09 as a forecast-program
adjudication, and nothing in this lane's evidence changes their status. The
FR-22 job stays red on exactly these two, which is where that signal belongs.

---

## 4. The `_FR22_OPEN_UNACCOUNTED` pin — reviewed, not extended (job 2)

R-W §7.1: *"the `_FR22_OPEN_UNACCOUNTED` pin should then be reviewed rather
than extended, since the FR-22 job (DO-NOT-REQUIRE per H-1) is where the
signal lives."*

Review, against the sweep with §1 and §3 filed:

| pin member | still armed in its keeper | still UNACCOUNTED | verdict |
|---|---|---|---|
| `ercot_storage_as_soc_reserve` (ERCOT) | True in `2026-08-25-234-eastex-identity` | yes — sole consumer `scripts/run_calibration.py` (the ercot-167 measured AS SOC reservation block) | **live, keep** |
| `nyiso_seam_deliverability_envelope` (NYISO) | True in `2026-09-02-nyiso-177-vintage-matched` | yes — sole consumer the backcast TTC overlay's `elif` branch (superseded at runtime by `nyiso_seam_par_attribution`, but armed and undeclared) | **live, keep** |

- **The accounting does not close, so the pin does not shrink.** A shrink is
  available only when a member is no longer UNACCOUNTED (declared or wired);
  neither is. Removing a live member would red the fast tier on a field whose
  disposition nobody has made, which is not this lane's call.
- **The pin is exact:** the set of UNACCOUNTED fields across all six keepers
  after this PR is exactly `{ercot_storage_as_soc_reserve,
  nyiso_seam_deliverability_envelope}` — the pin's two members, no more, no
  less (§5). The test's subset assertion would tolerate a stale member
  silently; this review confirms there is none.
- **Not extended**, per §7.1 and the charter. The three non-pin fields were
  resolved in the registry (§3), never by pinning.
- The strict xfail `test_check_exits_zero_on_the_current_keepers` remains
  correct and untouched: the checker still exits 1 on those two, and its
  `reason` names exactly them.

Where the signal now lives: the `FR-22 backcast->forecast parity` CI job
(DO-NOT-REQUIRE, H-1) exits 1 naming the two pinned fields and reports
`12 filed gap(s)` in its header; the fast tier no longer carries any of it.

---

## 5. Verification

- **Registry integrity:** `check_forecast_parity.py` → `0 registry failure(s)`
  (every new row's evidence path exists and names its field; both GAP rows'
  `finding` resolves to this document; both `PARAMETER_OF` parents are real
  fields).
- **The sweep after filing:** `SUMMARY: 6 keeper posture(s); 2 unaccounted,
  12 filed gap(s), 0 registry failure(s), 0 error(s)`, exit 1 on the two pin
  members; ERCOT reads `GAP` on the R-X pair (`GAP 4  UNACCOUNTED 1`), NYISO
  `GAP` on `nyiso_seam_par_attribution` (`GAP 2  UNACCOUNTED 1`), MISO
  `BACKCAST_ONLY` on the hour-ending key via its parent (`UNACCOUNTED 0`),
  CAISO `GAP` on `…_ungrounded` via F-5 (`UNACCOUNTED 0`); PJM and NEISO
  unchanged.
- **`tests/scoring/test_forecast_parity.py`:** `21 passed, 1 xfailed` — the
  formerly failing `test_all_six_keepers_resolve` passes with no test edit;
  the strict xfail still xfails (checker exit 1 on the pinned two).
- **Ruff** on the changed registry: `ruff check` clean, `ruff format --check`
  already formatted.
- **The full fast tier, locally, CI's exact command** (`python -m pytest -n 2
  -m "not slow and not integration and not fulldata"`, exit code read
  unpiped; a valid measurement again since R-W §4b closed the environment
  leak): see §5.1.

### 5.1 Local fast tier — `1 failed, 7807 passed, 34 skipped, 2 xfailed`, and the one is a NEW `main`-content red

Environment as R-W §1.1 (this container's clone carries `data/raw`, 5.8 GB,
161 entries — a superset of the job's sparse list; `data/clean` absent).
Command, exit captured unpiped into a file after the bare command:

```
uv run python -m pytest -n 2 -m "not slow and not integration and not fulldata"
PYTEST_EXIT=1
= 1 failed, 7807 passed, 34 skipped, 2 xfailed, 23 warnings in 518.92s (0:08:38) =
FAILED tests/scoring/test_gate_a_provenance.py::test_live_board_passes
```

(01:29:34Z → 01:38:15Z on the final tree, both commits in.) The routed
parity test **passes**; the skip and xfail counts are CI's own baseline
(34 / 2, as in run 2324). **The single failure is not the parity test and
not this branch's**:

```
gate-(a) provenance FAILED:
  - CAISO: gate.a_keeper_marker cites SUPERSEDED keeper '2026-09-01-caiso-231-b1-ungrounded';
    the ISO's current designated keeper is '2026-09-02-caiso-239-b1-stgas'
  - MISO:  gate.a_keeper_marker cites SUPERSEDED keeper '2026-09-01-miso-198-oomlevel';
    the ISO's current designated keeper is '2026-09-02-miso-201-stbasis'
  - NYISO: gate.a_keeper_marker cites SUPERSEDED keeper '2026-08-30-nyiso-159-loss-surface';
    the ISO's current designated keeper is '2026-09-02-nyiso-177-vintage-matched'
```

`scripts/check_gate_a_provenance.py` (the audit board's F-5 guard; also the
`check_gate_a_provenance` step of the `FR-21 forecast-board staleness` job)
compares each `isos.<ISO>.gate.a_keeper_marker` row of
`frontend/data/forecast/program-status.json` against the ISO's live keeper
shard, identity only. The board was last written at `8c41c90f`
(2026-09-02 16:54Z, capx D37); the three promotions that moved the keepers
landed **after** it — nyiso-177 `bfa990ec` (20:38Z), miso-201 `30a6518a`
(21:00Z), caiso-239 `c0cf3790` (22:57Z) — and none re-keyed the board row.
R-W's run 2324 (16:58Z) pre-dates all three, which is why this red did not
exist in R-W's count. It is on `main` content at `c73f78f5` and reproduces on
this branch unchanged.

**This lane cannot repair it.** The repair is a re-key of three
`program-status.json` rows, and the charter forbids this lane to touch
`program-status.json` (alongside keeper shards, markers and the freeze file)
— rightly: the forecast board is the FR-21/FF-2D namespace's, and a re-key
there is the promoting lane's duty (the same duty rule 22 D-5(b) states for
the backcast `complete` entry). Routed, §8 item 3. Until it lands, **no
`ci.yml` run can be fast-tier-green**, and the `FR-21` job is red on the same
object.

---

## 6. Rider — `ruff format` on R-W §7.2's three files (job 3)

Own commit, mechanical only, `uv run ruff format` (the lockfile's ruff,
0.15.17 — the same binary CI's `Ruff lint + format` job runs) on exactly:

- `scripts/data/derive_thermal_tranches.py`
- `src/market_sim/model/capacity_evolution/new_entry.py`
- `tests/scoring/test_build_dof_ledger_coal_sigmoids.py`

Every charter exclusion honoured: `src/market_sim/config/constants.py` is
never formatted (it is `extend-exclude`d in `pyproject.toml` and was not
touched); `scripts/archive`, `scripts/probes`, `results/` likewise.

**Reported, not formatted — `main` has re-reddened past R-W's three.**
`uv run ruff format --check .` on `c73f78f5` lists **13** files, R-W's three
plus ten that landed after its pin:

```
docs/handoffs/d37/grade-2026-09-02.py
docs/handoffs/d37/predecl-screen-grain-2026-09-02.py
scripts/gen_nyiso177_attestation.py
src/market_sim/data/fleet/arrays.py
src/market_sim/data/fleet/assembly.py
src/market_sim/data/fleet/campd_bins.py
src/market_sim/data/offer_curves.py
src/market_sim/data/outages.py
tests/unit/data/test_campd_per_unit_attribution.py
tests/unit/data/test_unit_outage_st_capacity_basis.py
```

The rider's charter names three files; five of the ten are heavily-crossed
core `src/` files other lanes are editing this week, and reflowing them from
this branch would seed merge conflicts in those lanes for no gain this lane
was asked for. So the `Ruff lint + format` job on this PR is red on those
ten and on nothing this lane changed (§7) — the R-U §3.3 "re-reddens within
minutes" dynamic, still running.

**And the job never reaches the format step on this PR: `ruff check` itself
is red on `main` content.** `uv run ruff check .` → `Found 2 errors`, both
`E731` (lambda assignment): `docs/handoffs/d37/grade-2026-09-02.py:127` and
`docs/handoffs/d37/predecl-screen-grain-2026-09-02.py:113` — two D37 scratch
scripts committed under `docs/handoffs/` (`c87452f5`, 2026-09-02 16:08Z), a
directory `pyproject.toml` does not exclude, unlike `scripts/probes` /
`scripts/archive` / `results`. Run 2344's `Ruff lint` step fails on them and
the `Ruff format check` step is skipped. R-U had this job green in run 2307;
the files landed after. Reported, not fixed (a `def` rewrite or an
`extend-exclude` entry for `docs/handoffs/**/*.py` is a one-line owner/CI-lane
call, not this rider's).
The owner's flip therefore still waits on both: the two E731s and the
format pass over the ten files.

---

## 7. Evidence — the CI run (job 4)

**PR #4635. Run `2344`, id `33703895548`, head `b2ce045a` (both code commits)
— `Fast test tier` job id `100488803209`, step *Fast pytest tier*
01:31:40Z → 01:40:21Z (8m41s), conclusion `failure`.**
<https://github.com/jessicacohen554-cyber/market-simulator/actions/runs/33703895548>

The job's own log tail:

```
FAILED tests/scoring/test_gate_a_provenance.py::test_live_board_passes - assert 1 == 0
= 1 failed, 7807 passed, 34 skipped, 2 xfailed, 23 warnings in 516.42s (0:08:36) =
##[error]Process completed with exit code 1.
```

Byte-for-byte the local §5.1 numbers (`1 / 7807 / 34 / 2`), the same single
test, so the serial-vs-`-n 2` and container-vs-runner axes agree — R-W §4b's
leak repair holds. **The routed parity test is green on CI** (it is not in
the failure list; the 7,807 include `test_all_six_keepers_resolve`), which is
what this lane was chartered to deliver on the tier. The one red is the
`main`-content forecast-board re-key of §5.1 / §8 item 3, present on `main`
since 22:57Z on 2026-09-02 and outside this lane's permitted files.

Every job, as found:

| job | conclusion | note |
|---|---|---|
| **`Fast test tier`** | 🔴 **failure** | `1 failed, 7807 passed, 34 skipped, 2 xfailed` — `test_gate_a_provenance.py::test_live_board_passes`, `main` content (§5.1); the R-W §3.8 parity red is CLEARED |
| `Rule-22 quarantine gates` | 🟢 success | `audit_keepers`, `legitimacy_diagnostics --keepers`, `check_registry_payload_parity`, `check_golden_manifest` all green |
| `Cache-key registration guard` | 🟢 success | |
| `Pinned default cache key` | 🟢 success | |
| `Structural refactor guards` | 🟢 success | |
| `Rule-28 mechanism-matrix guard` | 🟢 success | the R-W §7.7 anchor drift was repaired upstream; not this lane's |
| `Ruff lint + format` | 🔴 failure | **`Ruff lint` step** — the two `E731`s in `docs/handoffs/d37/` (§6); the format step is skipped behind it, so the rider's three files are not even reached |
| `FR-21 forecast-board staleness (WARN only)` | 🔴 failure | `check_gate_a_provenance` step — the SAME object as the tier's one red (§5.1); `check_forecast_staleness` green |
| `FR-22 backcast->forecast parity` | 🔴 failure | as designed (DO-NOT-REQUIRE, H-1): exit 1 on the two pinned fields only (§4) — down from seven UNACCOUNTED on `main` |
| `Forecast-invariant artifact audit` | 🔴 failure | as on `main` (DO-NOT-REQUIRE, H-1); untouched |

**G2 leg 2 status, stated against the criterion verbatim — *"one completed
fast-tier-green `ci.yml` run"*: NOT SATISFIED, and this finding does not
claim it.** The run completed; its `Fast test tier` job is red on exactly one
test. That test is not the one R-X was ruled to clear — that one is green —
but the criterion is the job, not a test, and the v21 / R-W refusals are the
guardrails in both directions: 7 → 1 on the parity object is not a green,
and neither is "green except for someone else's file". What blocks the
criterion now is a three-row re-key of `program-status.json` (§8 item 3) that
this lane is forbidden to make; the next records lane should carry leg 2 as
*"BLOCKED on the caiso-239 / miso-201 / nyiso-177 forecast-board re-key
(FR-22 gap filings landed, parity red cleared — #4635)"*.

No `workflow_dispatch` was issued; the PR's own run is the evidence. A
second run on the docs-only commit carrying this section (§9) adds no content
evidence beyond 2344's and is expected to read identically.

---

## 8. Routed, not fixed — and R-W's process finding, carried forward verbatim

1. **→ capx/forecast desk (FR-22 registry owner).** The wire-forward question
   on the R-X pair: `runner.py` / `pipeline/solve.py` seam,
   `p1_storage_discharge_cost`. Filed, tracked, undecided, per the ruling.
2. **→ forecast desk.** The disposition of `nyiso_seam_par_attribution`
   (§3.3) and, with it, its pinned sibling `nyiso_seam_deliverability_envelope`
   and `ercot_storage_as_soc_reserve` (§3.4): measured-TTC / measured-AS
   `BACKCAST_ONLY` family, or a forward channel. Three fields, one question.
3. **🔴 → the caiso-239 / miso-201 / nyiso-177 promoting lanes (or the
   forecast-board owner) — THE sole `Fast test tier` red, and this lane is
   forbidden to touch it.** `frontend/data/forecast/program-status.json`
   `isos.{CAISO,MISO,NYISO}.gate.a_keeper_marker` cite the superseded
   keepers (§5.1); `test_gate_a_provenance.py::test_live_board_passes` and
   the `FR-21` job's `check_gate_a_provenance` step fail on it. Repair: re-key
   the three rows against the live keepers per the F-5 protocol
   (`read_live_at` to the promotion sha, status re-read), one commit, then
   any PR's run can be fast-tier-green. Leg 2 is BLOCKED on exactly this
   until it lands.
4. **→ owner / next CI lane.** `Ruff lint + format` is red on `main` content
   twice over (§6): two `E731`s in a `docs/handoffs/d37/` script fail the
   lint step outright, and ten files beyond R-W's three would fail the
   format step behind it. This rider was chartered for three files.
5. **⚪ as found.** `Rule-28 mechanism-matrix guard` is **green** on run 2344
   — the 25 stale anchors R-W §7.7 reported were repaired upstream before
   this PR's run; nothing to route. `FR-22 backcast->forecast parity` and
   `Forecast-invariant artifact audit` red as on `main` (DO-NOT-REQUIRE,
   H-1); the FR-22 job's red is now the two pinned fields only (§4).
6. **→ calibration desk — R-W's process finding, verbatim:** *"A process
   finding rides along: two ERCOT promotions armed keeper mechanisms without
   the parity check that the promotion duty implies, and the fast tier — the
   one gate that would have caught it on the PR — was already red at the
   time, so the new red was invisible."* This lane adds three more instances
   of the same finding, one per ISO: the caiso-231, nyiso-159 and miso-198
   promotions each armed a keeper field with no forecast-orchestrator consumer
   and no registry row (§2), under the same red fast tier. Five promotions,
   four ISOs, zero parity checks. The duty is one command
   (`python scripts/check_forecast_parity.py --iso <ISO>`) before the
   promotion commit; making it part of the `calibration-report` skill or the
   `calibration-keeper-auditor` agent's checklist is the desk's call.

---

## 9. Rule 27 blob verification

Both code commits (`72d64d0a` registry + finding, `b2ce045a` rider) were
pushed over `git push` (HTTP/1.1, `lowSpeedLimit`/`lowSpeedTime` set) and
every pushed file was fetched back from
`origin/claude/fr22-gap-fast-tier-green-n9n7by` under `GIT_NO_LAZY_FETCH=1`
and compared to local on line count AND sha256: **5 of 5 OK, 0 mismatches**
— `scripts/lib/forecast_parity_registry.py` 548 lines,
`scripts/data/derive_thermal_tranches.py` 1,203,
`src/market_sim/model/capacity_evolution/new_entry.py` 1,872 (the three at or
above the 300-line threshold), plus `test_build_dof_ledger_coal_sigmoids.py`
195 and this document. No file was rewritten from regenerated response
content: the registry rows were added with local edits and the three rider
files are `ruff format`'s own on-disk output pushed as exact bytes. The
docs-only commit carrying §5.1/§7/§9 is verified the same way before this
lane ends, with the result recorded in the PR.
