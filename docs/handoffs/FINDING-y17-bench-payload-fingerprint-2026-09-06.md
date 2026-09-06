# FINDING — Y-17: a payload-only fingerprint for the bench stamp

**Lane:** Y-17 (Model Audit & Release-Finalization Program)
**Date:** 2026-09-06
**Pin:** `5fdd4374` (== `origin/main` at fetch, re-verified unchanged mid-session)
**Charter:** Director's call on the recommendation Y-15 §3.5 handed up, taking **option (a)** —
give `bench_stamp` a PAYLOAD-ONLY fingerprint and decide re-stampability on that, keeping the
aggregate hash as the staleness stamp.
**Branch:** `claude/y17-bench-payload-fingerprint-cm8gfn`

---

## 0. HEADLINE — the ninth gate is GREEN, and ERCOT/2022 went green on the payload measure without being re-stamped

`scripts/check_bench_freshness.py` reads **EXIT=0** at this pin: **24 parts checked, 0 STALE.**
It was **EXIT=1, 1 STALE** before this change and had been red on `main` continuously since
`f1561c2d` (2026-09-05 23:24:54Z).

`frontend/data/backcast/bench/ERCOT/2022.json.gz` is green **on the merits, not by fiat**: the
three sources that produce a bench payload are **byte-identical** — same git blob shas — between
the builder state that wrote the part and HEAD. No part was re-stamped, regenerated, hand-edited
or allowlisted. §2 is the decomposition that proves it.

**No determination moves.** All six ISO keepers read `CALIBRATED` before and after (§6). The only
behavioural delta anywhere in the scorer is that ERCOT's false stale-bench alarm stops firing.

---

## 1. The defect, verified rather than re-derived

Y-15 §3.5 established it; this lane re-measured it independently from the artifacts before
building on it.

`scripts/lib/bench_stamp.py` is a member of its own `BUILDER_SOURCES`. Y-12's edit to it
(`3d0fd19d`, 2026-09-05 22:34:10Z, owner ruling R-AS) therefore moved the aggregate fingerprint
for **every bench part in existence**. Two consequences, both confirmed here:

1. **The aggregate test can never return "equal" for any pre-Y-12 part**, so under a literal
   re-stamp rule no such part is ever re-stampable — every one would need a full re-solve.
2. **That contradicts the program's own practice.** `404f1908` ("Y-12: re-stamp all 20 bench
   parts at builder 4254168edcfe", committed 22:34:10Z — the sibling of `3d0fd19d`) re-stamped
   20 parts across exactly that boundary by the Y-8 method.

The self-inclusion is **not itself wrong** and is **not removed** by this change: a change to
stamping logic *should* invalidate the provenance stamp every part carries. What is wrong is
using the aggregate as the **payload-reproducibility** test, which is the question a re-stamp
actually turns on.

---

## 2. Per-source decomposition — the evidence ERCOT/2022's payload is HEAD's

Computed by reading each builder source **out of git at each revision** (never the worktree) and
hashing it two ways: `ast.dump(ast.parse(src))` (HEAD's instrument) and raw bytes.

### 2.1 Aggregate vs payload, across the Y-12 boundary

| revision | AST (all 4) | BYTE (all 4) | **AST (payload 3)** | BYTE (payload 3) |
|---|---|---|---|---|
| `HEAD` = `5fdd4374` | `4254168edcfe` | `abdc9f0d03d3` | **`643eac24b565`** | `547e05f990d1` |
| `3d0fd19d` (Y-12) | `4254168edcfe` | `abdc9f0d03d3` | **`643eac24b565`** | `547e05f990d1` |
| `dc0f7c14` (== `3d0fd19d^`) | `96e5860ce4ec` | **`b2f21b9a00d3`** | **`643eac24b565`** | `547e05f990d1` |
| `404f1908` (the re-stamp commit) | `4254168edcfe` | `abdc9f0d03d3` | **`643eac24b565`** | `547e05f990d1` |

The part carries **`b2f21b9a00d3`**, which is the **byte** aggregate at `dc0f7c14` — so the part
was written by a **pre-Y-12 checkout** while the byte-era stamp was still in force, then
committed (`f1561c2d`, ercot-249/250) onto a post-Y-12 `main` without re-rendering. A merge race,
not a builder defect (Y-15 §3.3, reconfirmed).

**The payload column does not move anywhere in that table.**

### 2.2 Per source — this is stronger than Y-15 stated

Y-15 §3.5 reported the three payload sources as "SAME AST / byte-identical". They are in fact the
**same git blobs**, which settles it without any hashing argument at all:

| builder source | blob at `dc0f7c14` | blob at `3d0fd19d` | blob at `HEAD` | verdict |
|---|---|---|---|---|
| `scripts/render_calibration_html.py` | `d382d9b` | `d382d9b` | `d382d9b` | **identical object** |
| `scripts/render_backcast.py` | `ccf8b1c` | `ccf8b1c` | `ccf8b1c` | **identical object** |
| `scripts/lib/backcast_artifacts.py` | `c75d828` | `c75d828` | `c75d828` | **identical object** |
| `scripts/lib/bench_stamp.py` | `e379717` | `edb7d50` | `edb7d50` | **MOVED (this module only)** |

The entire divergence is the module that **computes the stamp** and contributes not one number to
a `bench` block. By the guarantee `bench_stamp.py`'s own docstring states, ERCOT/2022's payload
**is** what the builder at HEAD would produce. Before this change the instrument could not say so.

### 2.3 The claim checked against the artifacts, not just the sources

Independently of any fingerprint: re-writing **all 24** committed parts through
`backcast_artifacts.write_bench_part` at HEAD and diffing the decoded objects —

> **24 of 24:** the only differing `meta` key is `builderFingerprint`, and the `bench` block is
> **identical**. Zero exceptions.

ERCOT/2022 included. This is now pinned as a test (§4).

---

## 3. What changed

### 3.1 `scripts/lib/bench_stamp.py` (151 → 321 lines)

* **`PAYLOAD_SOURCES`** — the three payload-producing sources, `bench_stamp.py` **excluded by
  construction**, with the exclusion justified in a comment naming this finding.
* **`BUILDER_SOURCES = PAYLOAD_SOURCES + (_STAMP_SOURCE,)`** — composed, never re-spelled, so the
  "payload sources plus this module" relation cannot drift. The tuple's value and order are
  unchanged, so the aggregate construction is untouched.
* **`_fingerprint(sources)`** — the existing hash body, extracted so both measures are computed by
  the *same* code and cannot diverge. `builder_fingerprint()` and the new `payload_fingerprint()`
  are one-line callers.
* **`part_payload_fingerprint()` / `payload_origin()`** — resolve a part's payload state from the
  aggregate it records (§3.2).
* **`is_stale()`** now decides on the **payload** measure.

**The aggregate is NOT deleted** and rule 26 `[R-DELETE]` does not bite: nothing is deprecated or
zeroed. `builder_fingerprint()` keeps every job it had — the value written to and read from
`meta.builderFingerprint`, the provenance record, the key the payload state is resolved from, and
the identity the SOFT engine-drift tier measures against.

### 3.2 How an existing part gets a payload fingerprint — and why it is not an escape hatch

A committed part records only the aggregate, and the aggregate is not invertible. **A part also
cannot be taught to carry a payload fingerprint**: the writer,
`backcast_artifacts.write_bench_part`, is itself a payload source, so adding a second stamped
field would move the payload fingerprint and mark **all 24** parts stale — the exact opposite of
the repair. That rules out the obvious design, and it is why **no payload source was edited in
this session**.

So the mapping is recorded in code, as `PAYLOAD_FINGERPRINT_BY_BUILDER`, and resolution is:

| the part's aggregate | resolves to | origin |
|---|---|---|
| == HEAD's aggregate | HEAD's payload fingerprint (an equal aggregate pins every source) | `current` |
| a known historical value | that builder state's payload fingerprint | `historical` |
| anything else, or no stamp | `None` ⇒ **STALE** | `unknown` |

Four properties keep it honest:

1. **It asserts nothing the aggregate did not already fix.** An entry is a claim about a builder
   *state*, not a file: equal aggregate ⇒ equal material for all four sources, barring collision.
2. **Fail-closed.** An unknown builder state is never forgiven — it reads STALE.
3. **It cannot forgive a moved payload.** Measured: pointing an entry at a different payload
   state leaves `is_stale` **True** (§4, `test_c_*`).
4. **Every entry is recomputed from git by a test**, not trusted as a literal (§4, `test_d_*`).

This is materially different from the hand re-stamp the charter forbids, and no part was
re-stamped: a hand re-stamp writes an unverifiable claim into one data artifact, whereas an entry
is a code-level, git-verifiable, test-pinned statement about a historical builder state that
applies to every part carrying it.

**Two entries, both derived in §2:**

| aggregate | payload fingerprint | provenance |
|---|---|---|
| `4254168edcfe` | `643eac24b565` | Y-12's AST-era aggregate (`3d0fd19d`), carried by 23 of 24 parts, superseded by *this* module's edit |
| `b2f21b9a00d3` | `643eac24b565` | the byte-era aggregate at `dc0f7c14`, carried by `ERCOT/2022` |

Both map to the same value — which is the whole point: **the payload sources have not moved
across any of these states.**

**Maintenance is bounded and machine-guided.** An entry is owed *exactly* when an edit moves the
aggregate without moving the payload — i.e. an edit to `bench_stamp.py` alone. The guard test
fails with the literal line to add, and says explicitly not to add one if a payload source moved.

### 3.3 `scripts/check_bench_freshness.py` (236 → 287 lines)

Decides STALE on the payload measure; prints **both** fingerprints at HEAD; reports a part whose
aggregate is superseded but whose payload reproduces as a **`::notice`**, never gating. Those
notices are emitted **once per distinct superseded stamp** with the part list, not once per part:
an edit to `bench_stamp.py` puts every part in that state at once, and 24 identical annotations is
the kind of noise that trains a reader to skip the output — the nyiso-148 failure mode this gate
exists to prevent. The SOFT engine-drift tier is untouched.

### 3.4 `scripts/calibration_verdict.py` (one message, 3 lines)

Its stale-bench alarm quoted `builder_fingerprint()` for a decision that is now the payload
measure, so it would have misdescribed itself. Reworded to quote `payload_fingerprint()`.
**Scope note:** strictly outside the charter's four items, taken because leaving it would ship a
defect this change introduced. The alarm is a **stderr print** — no criterion, no caveat, no
determination effect (§6 measures this rather than asserting it).

**No bundle, registry sidecar, keeper shard, marker, freeze file or `program-status.json` was
touched. No bench part was re-stamped or regenerated. No solve was run.** No `ScenarioConfig`
field is added, so rule 31 `[R-MECH-MATRIX]` duty (c) is not engaged.

---

## 4. Tests

`tests/scoring/test_bench_stamp_ast.py` — **untouched, 11 passed.** Both git-derived
counterfactual cases ran (not skipped).

`tests/scoring/test_bench_stamp_payload.py` — **new, 12 passed**, hermetic except group (d):

| group | pins |
|---|---|
| (a) | `BUILDER_SOURCES == PAYLOAD_SOURCES + (bench_stamp.py,)` exactly; the three charter-named payload sources; both digests 12-hex, deterministic, and distinct |
| (b) | a stamp-only edit moves the aggregate and **not** the payload; **a payload-identical, stamp-moved part reads FRESH** (the ERCOT/2022 shape); a part on the current aggregate needs no table entry |
| (c) | **a payload-moved part reads STALE regardless of the stamp** — both with a resolvable stamp and with the stamp also moved; an unknown aggregate and a missing stamp both fail closed |
| (d) | each table entry **recomputed from git** at its cited commit (skips on a shallow checkout); every committed part's aggregate must resolve, with the exact line to add in the failure message |

Group (d) **ran, it did not skip** — both entries verified against real history.

`tests/scoring/test_backcast_artifacts.py` — the re-write test's predicate moved from `is_stale`
to the **aggregate**, and was **strengthened**. `is_stale` now answers the payload question, which
is deliberately blind to `bench_stamp.py`, so it no longer predicts a byte diff — the field the
writer restamps is the aggregate. Left as-was it read red for all 24 parts the moment the measures
split. The new invariant: a part on HEAD's aggregate must reproduce byte-identically, and a part
on a superseded aggregate may differ **only** in `meta.builderFingerprint` — its other meta keys
and its whole `bench` block must be untouched. The old test only asked *whether* a differing part
was flagged; this one asks *what* differs, so a payload change smuggled in beside a stamp move now
fails here. That is §2.3 turned into a standing check.

**Negative checks run directly** (neither is a shipped test; both confirm the guards bite):
emptying the table makes **24 of 24** parts read unknown/STALE; an entry pointing at a different
payload state leaves `is_stale` **True**.

---

## 5. Gate readings, `$?` read directly

### 5.1 The ninth gate, before and after

```
BEFORE  (main 5fdd4374, unmodified)
$ python3 scripts/check_bench_freshness.py
builder fingerprint at HEAD: 4254168edcfe
::error file=frontend/data/backcast/bench/ERCOT/2022.json.gz::bench part is STALE — carries
  builder fingerprint b2f21b9a00d3 but HEAD's is 4254168edcfe. ...
bench freshness: 24 part(s) checked, 1 STALE, 23 with engine drift
EXIT=1
```

```
AFTER   (this branch)
$ python3 scripts/check_bench_freshness.py
builder fingerprint at HEAD: bee29e135d42 (aggregate, recorded stamp)
payload fingerprint at HEAD: 643eac24b565 (decides STALE)
::notice::23 part(s) carry superseded aggregate stamp 4254168edcfe (HEAD's is bee29e135d42) but
  their builder's payload sources hash to 643eac24b565, identical to HEAD's — so their numbers
  ARE reproducible. Provenance note only; not gated. Parts: CAISO/2023 … PJM/2025
::notice::1 part(s) carry superseded aggregate stamp b2f21b9a00d3 (HEAD's is bee29e135d42) but
  their builder's payload sources hash to 643eac24b565, identical to HEAD's — so their numbers
  ARE reproducible. Provenance note only; not gated. Parts: ERCOT/2022
bench freshness: 24 part(s) checked, 0 STALE, 24 on a superseded stamp with a reproducing
  payload, 24 with engine drift
EXIT=0
```

The aggregate at HEAD moved `4254168edcfe` → `bee29e135d42` **because this session edited
`bench_stamp.py`** — the mechanism working exactly as designed, and the reason all 23
previously-green parts appear on a superseded stamp. The payload fingerprint `643eac24b565` did
**not** move, which is why none of them is stale.

The engine-drift count goes 23 → 24 because ERCOT/2022 no longer short-circuits on STALE and now
reaches the SOFT tier. That is more complete reporting, not new drift.

### 5.2 Exit-code table

| check | before (main `5fdd4374`) | after (this branch) |
|---|---|---|
| **`scripts/check_bench_freshness.py`** | **1** — 24 parts, **1 STALE** | **0** — 24 parts, **0 STALE** |
| `scripts/check_bench_freshness.py --iso ERCOT` | 1 | **0** — 4 parts, 0 STALE |
| `ruff format --check .` | 0 | **0** (1,341 files) |
| `ruff check .` | 0 | **0** — "All checks passed!" |
| `python -m compileall -q src scripts` | 0 | **0** |
| `scripts/ci_refactor_guards.py` | 0 | **0** — import-walk OK, script-refs OK (12 known-dangling) |
| `scripts/audit_keepers.py --check` | 0 | **0** |
| `scripts/check_registry_payload_parity.py` | 0 | **0** — 14 runs, 47 bundle dirs |
| `scripts/check_golden_manifest.py` | 0 | **0** |
| `scripts/check_gate_a_provenance.py` | 0 | **0** — 6 rows |
| `scripts/check_cache_key_registration.py` | 0 | **0** — 798 fields, 253 registered |
| `pytest tests/scoring/test_bench_stamp_ast.py` | 0 | **0** — 11 passed |
| `pytest tests/scoring/test_bench_stamp_payload.py` | n/a (new) | **0** — 12 passed |
| `pytest tests/scoring/test_backcast_artifacts.py` | 0 | **0** — 15 passed |
| `pytest tests/scoring/` (full tier) | 4 failed | **4 failed — the SAME 4** |

**`ci_refactor_guards.py` must be run under `uv run`.** Bare `python3` exits 1 with
`ModuleNotFoundError: No module named 'numpy'` on the import walk — an interpreter artifact, not a
guard failure.

### 5.3 The one red left, and it is not this lane's

`tests/scoring/test_ff_readiness_battery.py` — 4 failures
(`test_walk_inputs_trivial_single_year`, `test_resolve_report_no_hard_fail_full_horizon`,
`test_ercot_confirmed_horizon_is_reported_not_failed`,
`test_build_registration_scorecard_no_iso_gate_open`). **Verified pre-existing** by stashing this
branch's changes and re-running against unmodified `main` at `5fdd4374`: identical set, identical
count. Forecast-readiness scoring, no contact with `bench_stamp`. **Routed to the forecast desk;
recorded, not chased.**

A second scanner trap was found and avoided rather than tolerated: the new test's synthetic
fixture paths deliberately sit under `fixture/`, not `scripts/`. A `scripts/`-shaped literal is
picked up by `ci_refactor_guards.py --script-refs` as a dangling reference once the file is
tracked — the trap that cost `test_bench_stamp_ast.py` an entry in that guard's `KNOWN_DANGLING`
allowlist (Y-13). Any repo-relative path exercises `_fingerprint` identically, so **no allowlist
entry was added**. Note the guard passes on an *untracked* file regardless; that pass is a false
negative, which is why this was fixed by construction rather than by the green reading.

---

## 6. No determination moves — measured, not asserted

Every ISO's designated keeper, scored with `scripts/calibration_verdict.py` on committed
artifacts only (no solve), before and after:

| keeper | before | after | stale-bench alarm before → after |
|---|---|---|---|
| `2026-09-05-caiso-252-b1-notrim` | CALIBRATED | CALIBRATED | 0 → 0 |
| `2026-09-05-ercot248-two-config-keeper` | CALIBRATED | CALIBRATED | **1 → 0** |
| `2026-09-05-miso-220-nonsteam-lift` | CALIBRATED | CALIBRATED | 0 → 0 |
| `2026-08-17-neiso-99-joint-p1` | CALIBRATED | CALIBRATED | 0 → 0 |
| `2026-09-06-nyiso-196-extract-basis` | CALIBRATED | CALIBRATED | 0 → 0 |
| `2026-08-15-pjm-162-inputclock` | CALIBRATED | CALIBRATED | 0 → 0 |

Six of six unchanged. The single behavioural delta is ERCOT's alarm going quiet — correctly: its
part's payload **is** reproducible at HEAD.

---

## 7. The `404f1908` precedent, reconciled

Y-15 recorded the contradiction and left it open: `404f1908` re-stamped 20 parts across the
`3d0fd19d` boundary, which the dispatch's literal decision rule ("re-stamp only if the builder AST
at the part's build commit equals HEAD's") would have forbidden.

**Both are now consistent, and neither needed to be overruled.** The rule and the commit were
answering different questions with the same instrument:

* The **aggregate** answers *"was this part written by the exact builder at HEAD?"* — the question
  the recorded stamp exists to answer, and to which the honest answer for all 20 parts was **no**.
  That is why they were re-stamped rather than left alone.
* **Re-stampability** turns on *"would the builder at HEAD produce the same numbers?"* The Y-8
  method answered that by inspecting what actually changed and finding it payload-inert — the
  right question, answered by hand.

`404f1908` was therefore correct on the merits and unsupported by the instrument. This change
gives that question its own measure, so the judgment call is no longer made by hand each time:
`payload_fingerprint()` computes what the Y-8 method adjudicated. Under it, the 20 parts
`404f1908` re-stamped read FRESH without a re-stamp at all, and so does ERCOT/2022 — the part that
missed the re-stamp only because it was in flight during the merge race.

**A live consequence worth stating.** This session's own edit to `bench_stamp.py` moved the
aggregate for all 24 parts. Under the old instrument that would have demanded a 24-part re-stamp —
a repeat of `404f1908`, and of `677b605a` before it, where a single reworded comment cost a
dedicated lane 20 artifacts. Under the payload measure it costs **one table entry** and zero
artifact edits. That is the recurring cost the director's option (a) was chosen to end, and it is
already paid off once, in the change that introduces it.

---

## 8. What this does NOT do

* **It does not weaken the guarantee.** Identical payload-source ASTs still compile to identical
  behaviour, so a part written under either is byte-identical in its `bench` block by
  construction. The surface narrows from "the builder plus its stamper" to "the builder", and the
  dropped member is the one member that provably cannot change a number.
* **It does not touch the SOFT tier.** Engine drift under `src/market_sim/data|config` is still
  reported and still never gates. The exposure `bench_stamp.py`'s docstring names — the builder
  imports the engine for the plant→class map, the CHP shares and the EIA-923 reconciliation — is
  unchanged by this lane and unaddressed by it.
* **It does not certify any bench part's numbers against reality.** It certifies only that the
  committed numbers are what the builder at HEAD reproduces. A part can be perfectly reproducible
  and still built on engine inputs that have since moved; that is what the SOFT tier is for.
* **It does not regenerate anything.** No part currently needs regeneration on the payload
  measure, so nothing was routed to a calibration desk on this axis.

---

## 9. Ninth gate — plain statement

**GREEN.** `scripts/check_bench_freshness.py` exits **0**: 24 parts, **0 STALE**, 24 on a
superseded aggregate stamp with a reproducing payload, 24 with engine drift (SOFT, ungated).
ERCOT/2022 is green on the payload measure, on the evidence in §2, without being re-stamped.

The gate remains **desk-only** — it appears in no workflow under `.github/workflows/`, unchanged
by this lane and not this lane's to change.

### 9.1 Verified ON `main`, after the lane's work landed

This section post-dates the merge and is recorded separately from it (see the coda below).

**The work is on `main`.** PR **#4943** merged as **`16b9bf44`**. All five changed source files
are byte-identical between `main` and this lane's branch, compared by git object id:
`bench_stamp.py`, `check_bench_freshness.py`, `test_bench_stamp_payload.py`,
`test_backcast_artifacts.py`, `calibration_verdict.py` — **5 of 5 MATCH**.

**The ninth gate is green on `main`'s own bytes**, not merely on this branch. Run from a checkout
of `origin/main` at **`81022b2d`**:

```
builder fingerprint at HEAD: bee29e135d42 (aggregate, recorded stamp)
payload fingerprint at HEAD: 643eac24b565 (decides STALE)
bench freshness: 24 part(s) checked, 0 STALE, 24 on a superseded stamp with a
  reproducing payload, 24 with engine drift
EXIT=0
```

| measure | lane pin `5fdd4374` | merged state `5a0b4566` | **on `main` `81022b2d`** |
|---|---|---|---|
| aggregate at HEAD | `bee29e135d42` | `bee29e135d42` | **`bee29e135d42`** |
| payload at HEAD | `643eac24b565` | `643eac24b565` | **`643eac24b565`** |
| `check_bench_freshness.py` | EXIT **0**, 24 parts, 0 STALE | EXIT **0**, same | **EXIT 0, 24 parts, 0 STALE** |
| bench-stamp suites (3 files) | 38 passed | 38 passed | **38 passed** |
| `ruff format --check .` / `ruff check .` | 0 / 0 | 0 / 0 | **0 / 0** |

`main` advanced twice during and after this lane — `5fdd4374` → `5a0b4566` (21 commits, merged
into the branch with no conflicts) and on to `81022b2d`. **Neither range touches a payload
source, a bench part, or any file this lane owns**, and both fingerprints hold identical across
all three states — which independently confirms both advances were payload-inert for the bench
builder. The four `test_ff_readiness_battery` failures of §5.3 persist unchanged and remain the
forecast desk's.

**Coda — why this section landed after the code.** #4943 was merged from a snapshot taken before
this addendum's commit, so `main` carried the finding at 378 lines while the branch had 398. The
gap was found by comparing the doc's blob on `main` against the local copy during a post-merge
sweep; the five source files were unaffected. Per the merged-PR rule the follow-up is a **fresh
change off the latest `main`**, not a commit stacked on merged history. Worth recording as a
process note: a blob-level comparison of *every* deliverable against `main` after a merge catches
this, whereas checking only the code files would have reported a clean landing.
